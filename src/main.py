"""
Main FastAPI application for MLX LLM Server
"""
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_client import start_http_server

from .config import config
from .endpoints import chat, completions, models, sessions, vista
from .middleware import setup_middleware
from .model_manager import model_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MLX LLM Server...")

    # Initialize model manager
    await model_manager.initialize()
    logger.info(f"Default model loaded: {config.default_model}")

    # Start metrics server
    if config.enable_metrics:
        start_http_server(config.metrics_port)
        logger.info(f"Metrics server started on port {config.metrics_port}")

    yield

    # Shutdown
    logger.info("Shutting down MLX LLM Server...")


# Create FastAPI app
app = FastAPI(
    title="MLX LLM Server",
    description="Production LLM server for VISTA and LibraXis services",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=f"{config.api_prefix}/docs",
    redoc_url=f"{config.api_prefix}/redoc",
    openapi_url=f"{config.api_prefix}/openapi.json"
)

# Setup middleware
app = setup_middleware(app)

# Include routers
app.include_router(chat.router, prefix=f"{config.api_prefix}", tags=["Chat"])
app.include_router(completions.router, prefix=f"{config.api_prefix}", tags=["Completions"])
app.include_router(models.router, prefix=f"{config.api_prefix}", tags=["Models"])
app.include_router(sessions.router, prefix=f"{config.api_prefix}", tags=["Sessions"])
app.include_router(vista.router, prefix=f"{config.api_prefix}", tags=["VISTA"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MLX LLM Server",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "chat": f"{config.api_prefix}/chat/completions",
            "completions": f"{config.api_prefix}/completions",
            "models": f"{config.api_prefix}/models",
            "sessions": f"{config.api_prefix}/sessions",
            "docs": f"{config.api_prefix}/docs"
        }
    }


@app.get(f"{config.api_prefix}/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "memory_usage": (
            model_manager.memory_usage
            if isinstance(model_manager.memory_usage, dict)
            else {"used_gb": model_manager.memory_usage, "total_gb": None}
        ),
        "loaded_models": list(model_manager.models.keys())
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "server_error",
                "code": "internal_error"
            }
        }
    )


def run_server():
    """Run the server with SSL"""
    logger.info(f"Starting server on https://{config.host}:{config.port}")
    logger.info(f"API available at https://{config.primary_domain}{config.api_prefix}")
    logger.info(f"Also available at https://{config.tailscale_domain}{config.api_prefix}")

    cert_file = config.ssl_certfile
    key_file = config.ssl_keyfile

    # Fallback to ~/.ssl/dragon.* or origin.* if not provided
    if cert_file is None or key_file is None:
        from pathlib import Path

        home_ssl = Path.home() / ".ssl"
        dragon_crt = home_ssl / "dragon.crt"
        dragon_key = home_ssl / "dragon.key"
        origin_crt = home_ssl / "origin.crt"
        origin_key = home_ssl / "origin.key"

        if dragon_crt.exists() and dragon_key.exists():
            cert_file, key_file = dragon_crt, dragon_key
        elif origin_crt.exists() and origin_key.exists():
            cert_file, key_file = origin_crt, origin_key

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        ssl_certfile=str(cert_file) if cert_file else None,
        ssl_keyfile=str(key_file) if key_file else None,
        workers=config.workers,
        log_level="info",
        access_log=True,
        reload=False,  # Set to True for development
    )


if __name__ == "__main__":
    run_server()
