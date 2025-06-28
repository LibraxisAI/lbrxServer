"""
Chat completion endpoints with ChukSessions integration
"""
import asyncio
import json
import time
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..auth import verify_auth
from ..chuk_sessions import SessionManager
from ..config import config
from ..middleware import limiter
from ..model_manager import model_manager
from ..model_router import ModelRouter
from ..models import ChatCompletionChunk, ChatCompletionRequest, ChatCompletionResponse, Choice, Message, Usage

router = APIRouter()

# Initialize session manager
session_manager = None

async def get_session_manager() -> SessionManager:
    """Get or create session manager instance"""
    global session_manager
    if session_manager is None:
        session_manager = SessionManager(
            storage_type="redis" if "redis://" in config.redis_url else "memory",
            redis_url=config.redis_url if "redis://" in config.redis_url else None,
            default_ttl=config.session_ttl_hours * 3600,  # Convert hours to seconds
        )
        await session_manager.initialize()
    return session_manager


@router.post("/chat/completions")
@limiter.limit(f"{config.rate_limit_per_minute}/minute")
async def create_chat_completion(
    request: ChatCompletionRequest,
    auth: dict = Depends(verify_auth)
) -> ChatCompletionResponse:
    """Create a chat completion"""
    try:
        # Validate request
        if request.max_tokens is None:
            request.max_tokens = config.max_tokens_default
        elif request.max_tokens > config.max_tokens_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"max_tokens cannot exceed {config.max_tokens_limit}"
            )

        # Extract service from API key
        service = None
        if auth.get("method") == "api_key":
            api_key = auth.get("key", "")
            service = ModelRouter.extract_service_from_api_key(api_key)

        # Route to appropriate model
        model_id = ModelRouter.get_model_for_request(
            service=service,
            user=request.user,
            requested_model=request.model
        )

        # Update request with routed model
        request.model = model_id

        # Get session manager
        sm = await get_session_manager()

        # Handle session if provided
        if request.session_id:
            # Try to get existing session
            session = await sm.get_session(request.session_id)
            if session:
                # Add messages to session history
                for msg in request.messages:
                    await sm.add_message(
                        session_id=request.session_id,
                        role=msg.role,
                        content=msg.content
                    )
                # Get full conversation history
                messages = await sm.get_messages(request.session_id)
            else:
                # Create new session if it doesn't exist
                await sm.create_session(
                    session_id=request.session_id,
                    data={"model": request.model, "user": request.user}
                )
                messages = [msg.dict() for msg in request.messages]
                # Add initial messages to session
                for msg in request.messages:
                    await sm.add_message(
                        session_id=request.session_id,
                        role=msg.role,
                        content=msg.content
                    )
        else:
            # No session management, just convert messages
            messages = [msg.dict() for msg in request.messages]

        # Generate completion
        if request.stream:
            return StreamingResponse(
                stream_chat_completion(request, messages),
                media_type="text/event-stream"
            )
        else:
            # Non-streaming response
            output = await model_manager.generate_completion(
                model_id=request.model,
                messages=messages,
                temperature=request.temperature,
                top_p=request.top_p,
                max_tokens=request.max_tokens,
                stop=request.stop,
                stream=False
            )

            # Save assistant response to session if using sessions
            if request.session_id:
                await sm.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=output
                )

            # Count tokens (approximate)
            prompt_tokens = sum(len(msg["content"].split()) * 1.3 for msg in messages)
            completion_tokens = len(output.split()) * 1.3

            response = ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4()}",
                object="chat.completion",
                created=int(time.time()),
                model=request.model,
                system_fingerprint=f"mlx-{config.primary_domain}",
                choices=[
                    Choice(
                        index=0,
                        message=Message(role="assistant", content=output),
                        finish_reason="stop"
                    )
                ],
                usage=Usage(
                    prompt_tokens=int(prompt_tokens),
                    completion_tokens=int(completion_tokens),
                    total_tokens=int(prompt_tokens + completion_tokens)
                )
            )

            return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def stream_chat_completion(
    request: ChatCompletionRequest,
    messages: list
) -> AsyncGenerator[str, None]:
    """Stream chat completion responses"""
    try:
        completion_id = f"chatcmpl-{uuid.uuid4()}"
        created = int(time.time())

        # Initial chunk
        chunk = ChatCompletionChunk(
            id=completion_id,
            object="chat.completion.chunk",
            created=created,
            model=request.model,
            system_fingerprint=f"mlx-{config.primary_domain}",
            choices=[{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
        )
        yield f"data: {chunk.json()}\n\n"

        # Generate content
        async for token in model_manager.generate_completion(
            model_id=request.model,
            messages=messages,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            stop=request.stop,
            stream=True
        ):
            chunk = ChatCompletionChunk(
                id=completion_id,
                object="chat.completion.chunk",
                created=created,
                model=request.model,
                system_fingerprint=f"mlx-{config.primary_domain}",
                choices=[{"index": 0, "delta": {"content": token}, "finish_reason": None}]
            )
            yield f"data: {chunk.json()}\n\n"
            await asyncio.sleep(0)  # Allow other tasks to run

        # Final chunk
        chunk = ChatCompletionChunk(
            id=completion_id,
            object="chat.completion.chunk",
            created=created,
            model=request.model,
            system_fingerprint=f"mlx-{config.primary_domain}",
            choices=[{"index": 0, "delta": {}, "finish_reason": "stop"}]
        )
        yield f"data: {chunk.json()}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
