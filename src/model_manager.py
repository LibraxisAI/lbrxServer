"""
Model management for MLX LLM Server
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
import mlx.core as mx
from mlx_lm import load, generate
from .config import config
from .model_config import ModelConfig


logger = logging.getLogger(__name__)


class ModelManager:
    """Manages MLX model loading, caching, and generation"""
    
    def __init__(self):
        self.models: Dict[str, Tuple[Any, Any]] = {}  # model_id -> (model, tokenizer)
        self.model_info: Dict[str, Dict[str, Any]] = {}
        self.current_model: Optional[str] = None
        self._lock = asyncio.Lock()
        self.vlm_models: Dict[str, Any] = {}  # For VLM models
        
        # Set MLX memory limits
        if config.max_model_memory_gb > 0:
            mx.metal.set_memory_limit(config.max_model_memory_gb * 1024**3)
            mx.metal.set_cache_limit(min(100, config.max_model_memory_gb // 4) * 1024**3)
    
    async def initialize(self):
        """Initialize with auto-load models"""
        # Load default model first
        if config.default_model:
            await self.load_model(config.default_model)
        
        # Load other auto-load models
        auto_load_models = ModelConfig.get_auto_load_models()
        for model_config in auto_load_models:
            if model_config["id"] != config.default_model:
                try:
                    await self.load_model(model_config["id"])
                except Exception as e:
                    logger.error(f"Failed to auto-load {model_config['id']}: {e}")
    
    async def load_model(self, model_id: str) -> Tuple[Any, Any]:
        """Load a model if not already loaded"""
        async with self._lock:
            # Check if it's an alias
            model_config = ModelConfig.get_model_config(model_id)
            if model_config:
                actual_model_id = model_config["id"]
            else:
                actual_model_id = model_id
            
            if actual_model_id in self.models:
                logger.info(f"Model {actual_model_id} already loaded")
                self.current_model = actual_model_id
                return self.models[actual_model_id]
            
            logger.info(f"Loading model {actual_model_id}...")
            
            # Determine model path
            model_path = self._resolve_model_path(actual_model_id)
            if not model_path.exists():
                raise ValueError(f"Model not found: {model_path}")
            
            # Load model and tokenizer in thread pool
            loop = asyncio.get_event_loop()
            model, tokenizer = await loop.run_in_executor(
                None, self._load_model_sync, str(model_path)
            )
            
            # Cache model with actual ID
            self.models[actual_model_id] = (model, tokenizer)
            self.model_info[actual_model_id] = {
                "id": actual_model_id,
                "alias": model_id if model_config else None,
                "path": str(model_path),
                "loaded_at": datetime.utcnow().isoformat(),
                "memory_usage": mx.metal.get_active_memory() / 1e9,  # GB
                "type": model_config["type"].value if model_config else "llm",
                "context_length": model_config.get("context_length", 4096) if model_config else 4096,
            }
            self.current_model = actual_model_id
            
            logger.info(f"Model {model_id} loaded successfully")
            logger.info(f"Active memory: {mx.metal.get_active_memory() / 1e9:.2f} GB")
            
            return model, tokenizer
    
    def _load_model_sync(self, model_path: str) -> Tuple[Any, Any]:
        """Synchronous model loading"""
        # Check if it's a VLM model
        model_config = None
        for model_cfg in ModelConfig.MODELS.values():
            if model_path.endswith(model_cfg["id"]) or model_cfg["id"] in model_path:
                model_config = model_cfg
                break
        
        if model_config and model_config.get("server") == "mlx_vlm":
            # VLM models need special handling
            try:
                import mlx_vlm
                return mlx_vlm.load(model_path)
            except ImportError:
                logger.warning("mlx_vlm not installed, falling back to standard loading")
        
        return load(model_path)
    
    async def unload_model(self, model_id: str):
        """Unload a model to free memory"""
        async with self._lock:
            if model_id in self.models:
                del self.models[model_id]
                del self.model_info[model_id]
                
                # Force garbage collection
                import gc
                gc.collect()
                
                # Clear MLX cache
                mx.metal.clear_cache()
                
                if self.current_model == model_id:
                    self.current_model = None
                
                logger.info(f"Model {model_id} unloaded")
    
    async def generate_completion(
        self,
        model_id: str,
        messages: list,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: Optional[int] = None,
        stop: Optional[list] = None,
        stream: bool = False,
        **kwargs
    ):
        """Generate completion for messages"""
        model, tokenizer = await self.get_or_load_model(model_id)
        
        # Apply chat template
        if hasattr(tokenizer, 'chat_template') and tokenizer.chat_template:
            prompt = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=False
            )
        else:
            # Fallback to simple concatenation
            prompt = self._format_messages(messages)
        
        # Generation parameters
        gen_kwargs = {
            "temp": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens or config.max_tokens_default,
        }
        
        if stop:
            # Convert stop strings to token IDs
            stop_ids = []
            for stop_str in stop:
                if stop_str:
                    tokens = tokenizer.encode(stop_str, add_special_tokens=False)
                    if tokens:
                        stop_ids.extend(tokens)
            if stop_ids:
                gen_kwargs["stop_tokens"] = stop_ids
        
        # Generate
        if stream:
            return self._stream_generate(model, tokenizer, prompt, **gen_kwargs)
        else:
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None, generate, model, tokenizer, prompt, **gen_kwargs
            )
            return output
    
    async def _stream_generate(self, model, tokenizer, prompt, **kwargs):
        """Stream generation (yields tokens)"""
        # This would use mlx_lm's streaming capabilities
        # For now, return a simple implementation
        output = generate(model, tokenizer, prompt, **kwargs)
        yield output
    
    async def get_or_load_model(self, model_id: str) -> Tuple[Any, Any]:
        """Get model, loading if necessary"""
        if model_id not in self.models:
            return await self.load_model(model_id)
        return self.models[model_id]
    
    def _resolve_model_path(self, model_id: str) -> Path:
        """Resolve model ID to path"""
        # Check if it's a full path
        if "/" in model_id and (config.models_dir / model_id).exists():
            return config.models_dir / model_id
        
        # Search in models directory
        for org_dir in config.models_dir.iterdir():
            if org_dir.is_dir():
                for model_dir in org_dir.iterdir():
                    if model_dir.is_dir() and model_dir.name == model_id:
                        return model_dir
        
        # Default to direct path
        return config.models_dir / model_id
    
    def _format_messages(self, messages: list) -> str:
        """Simple message formatting fallback"""
        formatted = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                formatted += f"System: {content}\n\n"
            elif role == "user":
                formatted += f"User: {content}\n\n"
            elif role == "assistant":
                formatted += f"Assistant: {content}\n\n"
        formatted += "Assistant: "
        return formatted
    
    def list_available_models(self) -> list:
        """List all available models"""
        models = []
        
        # Scan models directory
        for org_dir in config.models_dir.iterdir():
            if org_dir.is_dir():
                for model_dir in org_dir.iterdir():
                    if model_dir.is_dir() and (model_dir / "config.json").exists():
                        model_id = f"{org_dir.name}/{model_dir.name}"
                        models.append({
                            "id": model_id,
                            "path": str(model_dir),
                            "loaded": model_id in self.models,
                        })
        
        return models
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model"""
        return self.model_info.get(model_id)
    
    @property
    def memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        return {
            "active_gb": mx.metal.get_active_memory() / 1e9,
            "peak_gb": mx.metal.get_peak_memory() / 1e9,
            "cache_gb": mx.metal.get_cache_memory() / 1e9,
        }


# Global model manager instance
model_manager = ModelManager()