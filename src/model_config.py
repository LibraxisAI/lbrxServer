"""
Model configuration for MLX LLM Server
"""
from typing import Dict, List, Any, Optional
from enum import Enum


class ModelType(Enum):
    """Model types supported by the server"""
    LLM = "llm"           # Standard language models
    VLM = "vlm"           # Vision-language models
    EMBEDDING = "embed"   # Embedding models
    RERANKER = "rerank"   # Reranking models
    AUDIO = "audio"       # Audio models (future)


class ModelConfig:
    """Configuration for available models"""
    
    # Base model configurations
    MODELS = {
        # Primary models
        "nemotron-ultra": {
            "id": "LibraxisAI/Llama-3_1-Nemotron-Ultra-253B-v1-mlx-q5",
            "type": ModelType.LLM,
            "description": "Nemotron Ultra 253B - Primary reasoning model",
            "memory_gb": 170,
            "context_length": 131072,
            "auto_load": True,
            "priority": 1
        },
        "command-a": {
            "id": "LibraxisAI/c4ai-command-a-03-2025-q5-mlx",
            "type": ModelType.LLM,
            "description": "Command-A 03 2025 - Fast instruction following",
            "memory_gb": 80,
            "context_length": 256000,
            "auto_load": True,
            "priority": 2
        },
        "qwen3-14b": {
            "id": "LibraxisAI/Qwen3-14b-MLX-q5",  # Using the newer one
            "type": ModelType.LLM,
            "description": "Qwen3 14B - Efficient general purpose",
            "memory_gb": 10,
            "context_length": 40960,
            "auto_load": True,
            "priority": 3
        },
        "qwen3-8b": {
            "id": "lmstudio-community/Qwen3-8B-MLX-8bit",
            "type": ModelType.LLM,
            "description": "Qwen3 8B - Fast lightweight model",
            "memory_gb": 8,
            "context_length": 40960,
            "auto_load": False,
            "priority": 4
        },
        
        # Vision-Language Models (VLM)
        "llama-scout": {
            "id": "mlx-community/Llama-4-Scout-17B-16E-Instruct-6bit",
            "type": ModelType.VLM,
            "description": "Llama Scout - Vision-language model",
            "memory_gb": 15,
            "context_length": 8192,
            "auto_load": False,
            "priority": 5,
            "server": "mlx_vlm"  # Requires mlx_vlm.server
        },
        "nanonets-ocr": {
            "id": "LibraxisAI/nanonets/Nanonets-OCR-s-MLX-Q8",
            "type": ModelType.VLM,
            "description": "Nanonets OCR - Document extraction",
            "memory_gb": 5,
            "context_length": 4096,
            "auto_load": False,
            "priority": 6,
            "server": "mlx_vlm"
        },
        
        # Specialized models
        "qwen3-reranker": {
            "id": "LibraxisAI/Qwen3-Reranker-4B-MLX-Q5",
            "type": ModelType.RERANKER,
            "description": "Qwen3 Reranker - Search result reranking",
            "memory_gb": 4,
            "context_length": 8192,
            "auto_load": False,
            "priority": 7
        }
    }
    
    @classmethod
    def get_model_config(cls, model_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific model"""
        # Check by alias first
        if model_id in cls.MODELS:
            return cls.MODELS[model_id]
        
        # Check by full ID
        for config in cls.MODELS.values():
            if config["id"] == model_id:
                return config
        
        return None
    
    @classmethod
    def get_models_by_type(cls, model_type: ModelType) -> List[Dict[str, Any]]:
        """Get all models of a specific type"""
        return [
            config for config in cls.MODELS.values()
            if config["type"] == model_type
        ]
    
    @classmethod
    def get_auto_load_models(cls) -> List[Dict[str, Any]]:
        """Get models that should be loaded on startup"""
        return [
            config for config in cls.MODELS.values()
            if config.get("auto_load", False)
        ]
    
    @classmethod
    def estimate_total_memory(cls, model_ids: List[str]) -> float:
        """Estimate total memory usage for a set of models"""
        total_gb = 0
        for model_id in model_ids:
            config = cls.get_model_config(model_id)
            if config:
                total_gb += config.get("memory_gb", 0)
        return total_gb
    
    @classmethod
    def get_vlm_models(cls) -> List[Dict[str, Any]]:
        """Get models that require mlx_vlm server"""
        return [
            config for config in cls.MODELS.values()
            if config.get("server") == "mlx_vlm"
        ]