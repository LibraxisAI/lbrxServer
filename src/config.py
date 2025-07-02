"""
Configuration for MLX LLM Server
"""
from pathlib import Path
from typing import Any

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class ServerConfig(BaseSettings):
    """Main server configuration"""

    # Server settings
    host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    # Default HTTPS port for LLM server
    port: int = Field(default=8555, env="SERVER_PORT")
    workers: int = Field(default=1, env="SERVER_WORKERS")  # MLX works best with single worker

    # SSL/TLS settings (optional)
    ssl_certfile: Path | None = Field(default=None, env="SSL_CERT")
    ssl_keyfile: Path | None = Field(default=None, env="SSL_KEY")

    # Environment (dev/prod)
    environment: str = Field(default="prod", env="ENV")

    # Domain configuration
    primary_domain: str = Field(default="localhost", env="PRIMARY_DOMAIN")
    tailscale_domain: str = Field(default="", env="TAILSCALE_DOMAIN")
    # Comma-separated list of origins. When empty -> handled in middleware.
    allowed_origins: str = Field(default="", env="ALLOWED_ORIGINS")

    # Model settings
    models_dir: Path = Field(
        default=Path("./models"),
        env="MODELS_DIR"
    )
    default_model: str = Field(
        default="qwen3-14b",  # LibraxisAI Qwen3 14B - superior quality
        env="DEFAULT_MODEL"
    )
    max_model_memory_gb: int = Field(default=24, env="MAX_MODEL_MEMORY_GB")

    # API settings
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    max_tokens_default: int = Field(default=2048, env="MAX_TOKENS_DEFAULT")
    max_tokens_limit: int = Field(default=32768, env="MAX_TOKENS_LIMIT")

    # Redis settings for ChukSessions
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    session_ttl_hours: int = Field(default=24, env="SESSION_TTL_HOURS")

    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")

    # Authentication
    enable_auth: bool = Field(default=True, env="ENABLE_AUTH")
    api_keys: list[str] = Field(default=[], env="API_KEYS")
    jwt_secret: str = Field(default="", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")

    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    # Voice API routing (for future split)
    voice_api_host: str = Field(default="", env="VOICE_API_HOST")
    voice_services: list[str] = Field(
        default=[],
        env="VOICE_SERVICES"
    )

    @validator("ssl_certfile", "ssl_keyfile")
    def validate_ssl_paths(cls, v: Path | None) -> Path | None:
        """Ensure SSL paths exist if provided"""
        if v and not v.exists():
            raise ValueError(f"SSL path {v} does not exist")
        return v

    # Utility helpers

    @property
    def is_dev(self) -> bool:
        """Return True if running in development environment."""
        return self.environment.lower() in {"dev", "development", "local"}

    @property
    def cors_allowed_origins(self) -> list[str]:
        """Return parsed list of allowed CORS origins.

        If ALLOWED_ORIGINS is empty and we are in dev mode → ["*"].
        Otherwise split by comma, strip whitespace, discard empties.
        """
        if not self.allowed_origins:
            return ["*"] if self.is_dev else []

        # Provided list - support JSON list or comma separated string
        raw = self.allowed_origins.strip()
        if raw.startswith("["):
            import json
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(o) for o in parsed]
            except json.JSONDecodeError:
                pass  # fallback to comma parsing

        return [o.strip() for o in raw.split(",") if o.strip()]

    @validator("models_dir")
    def validate_models_dir(cls, v: Path) -> Path:
        """Create models directory if it doesn't exist"""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @validator("jwt_secret")
    def validate_jwt_secret(cls, v: str, values: dict[str, Any]) -> str:
        """Generate JWT secret if not provided"""
        if not v and values.get("enable_auth"):
            import secrets
            return secrets.token_urlsafe(32)
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
config = ServerConfig()
