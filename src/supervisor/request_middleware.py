"""
Request capture middleware for crash recovery.
Integrates with FastAPI to persist all incoming requests.
"""

import json
import time
import uuid
from datetime import datetime
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from .supervisor import RequestQueue, RequestInfo


class RequestPersistenceMiddleware(BaseHTTPMiddleware):
    """Middleware to persist requests for crash recovery."""
    
    def __init__(self, app: ASGIApp, queue_dir: str = "/tmp/lbrx_queue"):
        super().__init__(app)
        self.request_queue = RequestQueue(queue_dir)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Capture and persist request before processing."""
        # Skip health checks and non-API endpoints
        if request.url.path in ["/health", "/api/v1/health", "/metrics"]:
            return await call_next(request)
            
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Capture request body
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                body = json.loads(body_bytes) if body_bytes else {}
                
                # Reconstruct request for downstream processing
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except Exception as e:
                logger.error(f"Failed to capture request body: {e}")
                
        # Extract model from body if present
        model = None
        if isinstance(body, dict):
            model = body.get("model")
            
        # Create request info
        request_info = RequestInfo(
            request_id=request_id,
            endpoint=str(request.url.path),
            method=request.method,
            headers=dict(request.headers),
            body=body,
            timestamp=datetime.now(),
            model=model,
            status="pending"
        )
        
        # Persist request
        try:
            await self.request_queue.add_request(request_info)
            logger.debug(f"Persisted request {request_id} to queue")
        except Exception as e:
            logger.error(f"Failed to persist request {request_id}: {e}")
            
        # Mark as processing
        try:
            await self.request_queue.mark_processing(request_id)
            
            # Process request
            response = await call_next(request)
            
            # Mark as completed on success
            if response.status_code < 400:
                await self.request_queue.mark_completed(request_id)
            else:
                await self.request_queue.mark_failed(
                    request_id, 
                    f"HTTP {response.status_code}"
                )
                
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Mark as failed on exception
            logger.error(f"Request {request_id} failed with exception: {e}")
            await self.request_queue.mark_failed(request_id, str(e))
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "message": str(e) if logger.level <= 10 else "An error occurred"
                },
                headers={"X-Request-ID": request_id}
            )