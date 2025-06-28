"""
Configuration for MLX LLM Server
"""
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseSettings, Field, validator


class ServerConfig(BaseSettings):
    """Main server configuration"""
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    port: int = Field(default=443, env="SERVER_PORT")
    workers: int = Field(default=1, env="SERVER_WORKERS")  # MLX works best with single worker
    
    # SSL/TLS settings
    ssl_certfile: Path = Field(default=Path.home() / ".ssl" / "dragon.crt", env="SSL_CERT")
    ssl_keyfile: Path = Field(default=Path.home() / ".ssl" / "dragon.key", env="SSL_KEY")
    
    # Domain configuration
    primary_domain: str = Field(default="libraxis.cloud", env="PRIMARY_DOMAIN")
    tailscale_domain: str = Field(default="dragon.fold-antares.ts.net", env="TAILSCALE_DOMAIN")
    allowed_origins: List[str] = Field(
        default=[
            "https://libraxis.cloud",
            "https://dragon.fold-antares.ts.net",
            "https://whisplbrx.libraxis.cloud",
            "https://forkmeASAPp.libraxis.cloud",
            "https://anydatanext.libraxis.cloud",
            "https://lbrxvoice.libraxis.cloud",
            "https://vista.libraxis.cloud",
        ],
        env="ALLOWED_ORIGINS"
    )
    
    # Model settings
    models_dir: Path = Field(
        default=Path.home() / ".lmstudio" / "models",
        env="MODELS_DIR"
    )
    default_model: str = Field(
        default="nemotron-ultra",  # Use alias from model_config
        env="DEFAULT_MODEL"
    )
    max_model_memory_gb: int = Field(default=400, env="MAX_MODEL_MEMORY_GB")
    
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
    api_keys: List[str] = Field(default=[], env="API_KEYS")
    jwt_secret: str = Field(default="", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Voice API routing (for future split)
    voice_api_host: str = Field(default="100.75.30.90", env="VOICE_API_HOST")
    voice_services: List[str] = Field(
        default=["whisplbrx", "lbrxvoice", "lbrxvoicepro"],
        env="VOICE_SERVICES"
    )
    
    @validator("ssl_certfile", "ssl_keyfile", "models_dir")
    def validate_paths(cls, v: Path) -> Path:
        """Ensure paths exist"""
        if not v.exists():
            raise ValueError(f"Path {v} does not exist")
        return v
    
    @validator("jwt_secret")
    def validate_jwt_secret(cls, v: str, values: Dict[str, Any]) -> str:
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