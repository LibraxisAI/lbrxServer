"""
Model configuration and registry
"""
from enum import Enum
from typing import Any


class ModelType(Enum):
    """Model type enumeration"""
    LLM = "llm"           # Standard language models
    VLM = "vlm"           # Vision-language models
    EMBEDDING = "embed"   # Embedding models
    RERANKER = "rerank"   # Reranking models
    AUDIO = "audio"       # Audio models (future)


class ModelConfig:
    """Configuration for available models"""

    # Base model configurations
    # Add your own models here following this structure
    MODELS = {
        # Small models (good for testing)
        "llama-3.2-1b": {
            "id": "mlx-community/Llama-3.2-1B-Instruct-4bit",
            "type": ModelType.LLM,
            "description": "Llama 3.2 1B - Ultra-fast, minimal resource usage",
            "memory_gb": 2,
            "context_length": 131072,
            "auto_load": False,
            "priority": 10
        },
        "llama-3.2-3b": {
            "id": "mlx-community/Llama-3.2-3B-Instruct-4bit",
            "type": ModelType.LLM,
            "description": "Llama 3.2 3B - Good balance of speed and quality",
            "memory_gb": 4,
            "context_length": 131072,
            "auto_load": False,
            "priority": 5
        },

        # LibraxisAI Premium Models
        "qwen3-14b": {
            "id": "LibraxisAI/Qwen3-14b-MLX-Q5",
            "type": ModelType.LLM,
            "description": "Qwen3 14B Q5 - Premium quality, excellent reasoning",
            "memory_gb": 12,  # +2GB for inference
            "context_length": 32768,
            "auto_load": True,
            "priority": 1
        },

        # Medium models
        "mistral-7b": {
            "id": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
            "type": ModelType.LLM,
            "description": "Mistral 7B - Efficient general-purpose model",
            "memory_gb": 8,
            "context_length": 32768,
            "auto_load": False,
            "priority": 6
        },
        "phi-3": {
            "id": "mlx-community/Phi-3.5-mini-instruct-4bit",
            "type": ModelType.LLM,
            "description": "Phi 3.5 Mini - Microsoft's efficient model",
            "memory_gb": 5,
            "context_length": 131072,
            "auto_load": False,
            "priority": 7
        },

        # Medical/Scientific models
        "c4ai-03-2025": {
            "id": "LibraxisAI/c4ai-command-a-03-2025-q5-mlx",
            "type": ModelType.LLM,
            "description": "C4AI 03-2025 111B Dense - Scientifical/Medical excellence with internal reasoning",
            "memory_gb": 87,  # +2GB for inference
            "context_length": 131072,
            "auto_load": False,
            "priority": 2
        },
        "nemotron-49b": {
            "id": "LibraxisAI/Llama-3_3-Nemotron-Super-49B-v1-MLX-Q5",
            "type": ModelType.LLM,
            "description": "Nemotron Super 49B - High quality reasoning",
            "memory_gb": 51,  # +2GB for inference
            "context_length": 131072,
            "auto_load": True,
            "priority": 1
        },
        "nemotron-253b": {
            "id": "LibraxisAI/Llama-3_1-Nemotron-Ultra-253B-v1-mlx-q5",
            "type": ModelType.LLM,
            "description": "Nemotron Ultra 253B - Ultimate quality",
            "memory_gb": 253,
            "context_length": 131072,
            "auto_load": False,
            "priority": 1
        },
        "qwq-32b": {
            "id": "LibraxisAI/QwQ-32B-MLX-Q5",
            "type": ModelType.LLM,
            "description": "QwQ 32B - Superior reasoning with thinking mode",
            "memory_gb": 34,  # +2GB for inference
            "context_length": 32768,
            "auto_load": True,
            "priority": 3
        },
        "qwen3-30b-moe": {
            "id": "Qwen/Qwen3-30B-A3B-MLX-Q5",
            "type": ModelType.LLM,
            "description": "Qwen3 30B MoE (3B active) - Efficient reasoning",
            "memory_gb": 20,
            "context_length": 32768,
            "auto_load": False,
            "priority": 4
        },

        # Vision models
        "llama-vision": {
            "id": "mlx-community/Llama-3.2-11B-Vision-Instruct-4bit",
            "type": ModelType.VLM,
            "description": "Llama 3.2 Vision - Multimodal understanding",
            "memory_gb": 12,
            "context_length": 131072,
            "auto_load": False,
            "priority": 8,
            "server": "mlx_vlm"  # Requires VLM server
        },
        "qwen-vl": {
            "id": "mlx-community/Qwen2-VL-2B-Instruct-4bit",
            "type": ModelType.VLM,
            "description": "Qwen2 VL - Efficient vision-language model",
            "memory_gb": 4,
            "context_length": 32768,
            "auto_load": False,
            "priority": 9,
            "server": "mlx_vlm"
        },

        # Add your custom models here
        # "custom-model": {
        #     "id": "/path/to/your/model",
        #     "type": ModelType.LLM,
        #     "description": "Your custom model description",
        #     "memory_gb": 10,
        #     "context_length": 8192,
        #     "auto_load": False,
        #     "priority": 20
        # },
    }

    @classmethod
    def get_model_config(cls, model_id: str) -> dict[str, Any] | None:
        """Get configuration for a specific model"""
        # Check direct match
        if model_id in cls.MODELS:
            return cls.MODELS[model_id]

        # Check if it's a full model ID that matches
        for config in cls.MODELS.values():
            if config["id"] == model_id:
                return config

        # Check aliases
        if model_id in MODEL_ALIASES:
            alias_target = MODEL_ALIASES[model_id]
            return cls.get_model_config(alias_target)

        return None

    @classmethod
    def get_auto_load_models(cls) -> list[str]:
        """Get list of models to auto-load on startup"""
        auto_load = []
        for model_id, config in cls.MODELS.items():
            if config.get("auto_load", False):
                auto_load.append((config["priority"], model_id))

        # Sort by priority (lower number = higher priority)
        auto_load.sort(key=lambda x: x[0])
        return [model_id for _, model_id in auto_load]

    @classmethod
    def estimate_memory_usage(cls, model_ids: list[str]) -> int:
        """Estimate total memory usage for a list of models"""
        total_gb = 0
        for model_id in model_ids:
            config = cls.get_model_config(model_id)
            if config:
                total_gb += config.get("memory_gb", 0)
        return total_gb


# Model aliases for user-friendly names
MODEL_ALIASES = {
    # Default aliases
    "default": "qwen3-14b",
    "fast": "llama-3.2-1b",
    "vision": "llama-vision",

    # LibraxisAI models
    "qwen": "qwen3-14b",
    "qwen3": "qwen3-14b",
    
    # Medical/Scientific
    "c4ai": "c4ai-03-2025",
    "medical": "c4ai-03-2025",
    "scientific": "c4ai-03-2025",
    "vista": "c4ai-03-2025",  # Override for Vista to use best medical model

    # Common model name shortcuts
    "llama": "llama-3.2-3b",
    "llama-small": "llama-3.2-1b",
    "mistral": "mistral-7b",
    "phi": "phi-3",

    # Add your custom aliases here
    # "gpt": "your-custom-gpt-model",
}
