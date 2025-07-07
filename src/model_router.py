"""
Model routing based on service and user preferences
"""
import logging

logger = logging.getLogger(__name__)


class ModelRouter:
    """Routes requests to appropriate models based on service type"""

    # WHITELIST ONLY - NO JIT LOADING!
    ALLOWED_MODELS: set[str] = {
        "nemotron-49b",
        "LibraxisAI/Llama-3_3-Nemotron-Super-49B-v1-MLX-Q5",
        "nemotron-253b",  # Ultra!
        "qwen3-14b",
        "LibraxisAI/Qwen3-14b-MLX-Q5",
        "qwq-32b",  # Reasoning
        "LibraxisAI/QwQ-32B-MLX-Q5",
        "c4ai-03-2025",  # medical
        "LibraxisAI/c4ai-command-a-03-2025-q5-mlx",
        "whisper-large-v3",
        "nanonets-ocr",  # OCR
    }

    # Service to model mapping
    SERVICE_MODELS: dict[str, str] = {
        # Medical reasoning - c4ai is working!
        "vista": "c4ai-03-2025",  # Medical model loaded at 88GB

        # Code generation - DeepSeek excels at code
        "forkmeASAPp": "deepseek-coder-v2",

        # Data analysis - Qwen handles data well
        "anydatanext": "qwen3-14b",

        # Voice synthesis prep - use fast model
        "lbrxvoice": "qwen3-14b",  # Better quality than 1.7b

        # Whisper is separate - not an LLM
        "whisplbrx": "whisper-large-v3",

        # Default for unknown services
        "default": "qwen3-14b"  # Our workhorse
    }

    # User-specific overrides (VIP treatment)
    USER_OVERRIDES: dict[str, dict[str, str]] = {
        # Example: "user@example.com": {"*": "premium-model"}
    }

    # Model fallback chain for reliability
    FALLBACK_CHAIN: dict[str, str | None] = {
        "qwen3-14b": "mistral-7b",
        "mistral-7b": "llama-3.2-3b",
        "deepseek-coder": "qwen3-14b",
        "phi-3": "llama-3.2-1b",
    }

    @classmethod
    def get_model_for_request(
        cls,
        service: str | None = None,
        user: str | None = None,
        requested_model: str | None = None,
        check_availability: bool = True
    ) -> str:
        """
        Determine which model to use for a request
        
        Priority:
        1. Explicitly requested model (IF WHITELISTED)
        2. User override
        3. Service-based routing
        4. Default model
        
        Args:
            service: Service name (vista, whisplbrx, etc.)
            user: User identifier for overrides
            requested_model: Explicitly requested model
            check_availability: Whether to check if model exists
            
        Returns:
            Model ID to use
        """
        # 1. Explicit model request takes precedence (BUT MUST BE WHITELISTED!)
        if requested_model and requested_model != "default":
            if requested_model not in cls.ALLOWED_MODELS:
                logger.warning(f"Requested model {requested_model} not in whitelist! Available: {cls.ALLOWED_MODELS}")
                # Fall through to service routing
            else:
                logger.info(f"Using explicitly requested model: {requested_model}")
                return requested_model

        # 2. Check user overrides
        if user and user in cls.USER_OVERRIDES:
            user_config = cls.USER_OVERRIDES[user]
            if "*" in user_config:
                logger.info(f"Using user override model for {user}: {user_config['*']}")
                return user_config["*"]
            if service and service in user_config:
                logger.info(f"Using user override model for {user}/{service}: {user_config[service]}")
                return user_config[service]

        # 3. Service-based routing
        if service and service in cls.SERVICE_MODELS:
            model_id = cls.SERVICE_MODELS[service]
            logger.info(f"Routing {service} request to model: {model_id}")
            return model_id

        # 4. Default fallback
        default_model = cls.SERVICE_MODELS.get("default", "default")
        logger.info(f"Using default model: {default_model}")
        return default_model

    @classmethod
    def get_fallback_model(cls, model_id: str) -> str | None:
        """Get fallback model if primary fails"""
        return cls.FALLBACK_CHAIN.get(model_id)

    @classmethod
    def extract_service_from_api_key(cls, api_key: str) -> str | None:
        """
        Extract service name from API key prefix
        
        Expected format: service_xxxxx or svc_xxxxx
        """
        if not api_key:
            return None

        # Handle Bearer token format
        if api_key.startswith("Bearer "):
            api_key = api_key[7:]

        # Extract prefix
        parts = api_key.split("_", 1)
        if len(parts) >= 2:
            prefix = parts[0].lower()

            # Map prefixes to services
            prefix_mapping = {
                "vista": "vista",
                "vis": "vista",
                "whisp": "whisplbrx",
                "whi": "whisplbrx",
                "fork": "forkmeASAPp",
                "for": "forkmeASAPp",
                "data": "anydatanext",
                "any": "anydatanext",
                "voice": "lbrxvoice",
                "lbrx": "lbrxvoice",
            }

            return prefix_mapping.get(prefix)

        return None
