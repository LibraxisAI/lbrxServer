"""
Emergency Metal concurrency fix
Wraps model generation with semaphore to prevent concurrent Metal encoding
"""

import asyncio
from functools import wraps

# Global semaphore - only ONE model call at a time!
metal_semaphore = asyncio.Semaphore(1)

def serialize_metal_calls(func):
    """Decorator to serialize all Metal/MLX calls"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with metal_semaphore:
            return await func(*args, **kwargs)
    return wrapper

# Monkey patch for model_manager.py
def apply_emergency_fix():
    import sys
    sys.path.insert(0, '/Users/polyversai/hosted_dev/lbrxserver')
    
    from src import model_manager
    
    # Wrap the generate method
    original_generate = model_manager.ModelManager.generate
    
    @serialize_metal_calls
    async def patched_generate(self, *args, **kwargs):
        return await original_generate(self, *args, **kwargs)
    
    model_manager.ModelManager.generate = patched_generate
    
    # Also wrap stream_generate
    if hasattr(model_manager.ModelManager, 'stream_generate'):
        original_stream = model_manager.ModelManager.stream_generate
        
        @serialize_metal_calls
        async def patched_stream(self, *args, **kwargs):
            async for chunk in original_stream(self, *args, **kwargs):
                yield chunk
        
        model_manager.ModelManager.stream_generate = patched_stream
    
    print("🔧 EMERGENCY METAL FIX APPLIED!")
    print("   - Concurrent requests now serialized")
    print("   - Only ONE model call at a time")
    
if __name__ == "__main__":
    apply_emergency_fix()