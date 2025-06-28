"""
Middleware for MLX LLM Server
"""
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_client import Counter, Gauge, Histogram
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import config

logger = logging.getLogger(__name__)


# Metrics
request_count = Counter(
    "llm_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "llm_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)

active_requests = Gauge(
    "llm_active_requests",
    "Number of active requests"
)

model_memory_usage = Gauge(
    "llm_model_memory_gb",
    "Model memory usage in GB",
    ["model"]
)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


def setup_middleware(app):
    """Configure all middleware for the FastAPI app"""

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # Trusted Host
    trusted_hosts = [
        config.primary_domain,
        config.tailscale_domain,
        "localhost",
        "127.0.0.1",
        "178.183.101.202",  # Dragon static IP
    ]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Request logging and metrics
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", f"{time.time()}")
        start_time = time.time()

        # Track active requests
        active_requests.inc()

        # Log request
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} "
            f"from {request.client.host}"
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()

            request_duration.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

            # Log response
            logger.info(
                f"Response {request_id}: {response.status_code} "
                f"in {duration:.3f}s"
            )

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}"

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request {request_id} failed after {duration:.3f}s: {e!s}"
            )
            raise
        finally:
            active_requests.dec()

    # Security headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response

    return app
