"""
Persistent model preloading for production stability
"""
import asyncio
import logging
from typing import Dict, List

from .config import config
from .model_manager import model_manager

logger = logging.getLogger(__name__)


class ModelPreloader:
    """Manages persistent model loading with fixed allocation"""
    
    # Production model configuration
    PERSISTENT_MODELS: Dict[str, int] = {
        # Primary models
        "nemotron-49b": 2,        # 2x ~49GB = ~98GB (medical/general)
        "qwen3-14b": 2,           # 2x ~14GB = ~28GB (general purpose)
        
        # Specialized models  
        "c4ai-03-2025": 1,        # 1x ~85GB = ~85GB (medical)
        "qwq-32b": 1,             # 1x ~32GB = ~32GB (reasoning)
        
        # Total: ~243GB of 300GB budget (leaving 57GB for operations)
    }
    
    # Load balancing for multi-instance models
    instance_counters: Dict[str, int] = {}
    instance_mapping: Dict[str, List[str]] = {}
    
    @classmethod
    async def load_all_persistent_models(cls) -> None:
        """Load all persistent models at startup"""
        logger.info("Starting persistent model loading...")
        
        total_memory = 0
        for model_id, num_instances in cls.PERSISTENT_MODELS.items():
            logger.info(f"Loading {num_instances}x {model_id}...")
            
            # For single instance, just load normally
            if num_instances == 1:
                try:
                    await model_manager.load_model(model_id)
                    model_info = model_manager.get_model_info(model_id)
                    if model_info:
                        total_memory += model_info.get("memory_usage", 0)
                except Exception as e:
                    logger.error(f"Failed to load {model_id}: {e}")
            else:
                # For multiple instances, we need a different approach
                # For now, just load one instance (MLX doesn't support true multi-instance)
                # but track that we want multiple for load balancing
                try:
                    await model_manager.load_model(model_id)
                    model_info = model_manager.get_model_info(model_id)
                    if model_info:
                        total_memory += model_info.get("memory_usage", 0)
                    
                    cls.instance_mapping[model_id] = [model_id]  # Track instances
                    cls.instance_counters[model_id] = 0
                except Exception as e:
                    logger.error(f"Failed to load {model_id}: {e}")
        
        logger.info(f"Persistent model loading complete. Total memory: {total_memory:.2f}GB")
        
        # Verify we're within budget
        if total_memory > 300:
            logger.warning(f"Memory usage ({total_memory:.2f}GB) exceeds 300GB budget!")
    
    @classmethod
    def get_instance_for_request(cls, model_id: str) -> str:
        """Get the least loaded instance for a model (round-robin)"""
        if model_id not in cls.instance_mapping:
            return model_id
        
        # Simple round-robin for now
        instances = cls.instance_mapping[model_id]
        if not instances:
            return model_id
        
        counter = cls.instance_counters.get(model_id, 0)
        instance = instances[counter % len(instances)]
        cls.instance_counters[model_id] = counter + 1
        
        return instance
    
    @classmethod
    async def ensure_model_loaded(cls, model_id: str) -> bool:
        """Ensure a model is loaded, return False if not allowed"""
        # Check whitelist
        from .model_router import ModelRouter
        if model_id not in ModelRouter.ALLOWED_MODELS:
            logger.error(f"Model {model_id} not in whitelist! Rejecting request.")
            return False
        
        # Check if already loaded
        if model_id in model_manager.models:
            return True
        
        # Check if it's a persistent model we should have loaded
        if model_id in cls.PERSISTENT_MODELS:
            logger.warning(f"Persistent model {model_id} not loaded! Attempting to load...")
            try:
                await model_manager.load_model(model_id)
                return True
            except Exception as e:
                logger.error(f"Failed to load persistent model {model_id}: {e}")
                return False
        
        # Non-persistent model - reject (no JIT loading!)
        logger.error(f"Model {model_id} not pre-loaded and JIT loading is disabled!")
        return False


# Initialize on import
preloader = ModelPreloader()