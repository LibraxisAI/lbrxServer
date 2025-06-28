"""
Text completion endpoints
"""
import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, status

from ..models import CompletionRequest
from ..model_manager import model_manager
from ..auth import verify_auth
from ..config import config
from ..middleware import limiter


router = APIRouter()


@router.post("/completions")
@limiter.limit(f"{config.rate_limit_per_minute}/minute")
async def create_completion(
    request: CompletionRequest,
    auth: dict = Depends(verify_auth)
):
    """Create a text completion"""
    try:
        # Handle prompt as list or string
        prompts = request.prompt if isinstance(request.prompt, list) else [request.prompt]
        
        completions = []
        for i, prompt in enumerate(prompts[:request.n]):
            # Convert to chat format for consistency
            messages = [{"role": "user", "content": prompt}]
            
            output = await model_manager.generate_completion(
                model_id=request.model,
                messages=messages,
                temperature=request.temperature,
                top_p=request.top_p,
                max_tokens=request.max_tokens,
                stop=request.stop,
                stream=False
            )
            
            completions.append({
                "text": output,
                "index": i,
                "logprobs": None,
                "finish_reason": "stop"
            })
        
        # Calculate usage
        prompt_tokens = sum(len(p.split()) * 1.3 for p in prompts)
        completion_tokens = sum(len(c["text"].split()) * 1.3 for c in completions)
        
        response = {
            "id": f"cmpl-{uuid.uuid4()}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": completions,
            "usage": {
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(prompt_tokens + completion_tokens)
            }
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )