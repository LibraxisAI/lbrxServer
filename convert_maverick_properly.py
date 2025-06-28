#!/usr/bin/env python3
"""
Custom conversion script for Llama-4-Maverick with better error handling
"""
import os
import sys
sys.path.append('/Users/polyversai/.lmstudio/mlx_lm')

import mlx.core as mx

# Set memory limits BEFORE import
mx.metal.set_memory_limit(400 * 1024**3)  # 400GB limit
mx.metal.set_cache_limit(50 * 1024**3)    # 50GB cache


def convert_with_checkpointing():
    """Convert model with better memory management"""
    
    source = "meta-llama/Llama-4-Maverick-17B-128E-Instruct"
    target = "/Users/polyversai/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-MLX-Q5-fixed"
    
    print(f"Converting {source} to {target}")
    print("This will take time but should work...")
    
    # Use the command line interface directly
    import subprocess
    
    # First, try with smaller batch size
    cmd = [
        sys.executable, "-m", "mlx_lm.convert",
        "--hf-path", source,
        "--mlx-path", target,
        "--dtype", "float16",  # Use float16 instead of bfloat16
        "-q",
        "--q-bits", "5",
        "--q-group-size", "32",  # Smaller group size = less memory
        "--q-bits-vision", "5",  # Also quantize vision components
        "--no-quantize-gate",    # Skip gate quantization to save memory
    ]
    
    # Set environment for better performance
    env = os.environ.copy()
    env["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
    env["METAL_DEVICE_WRAPPER_TYPE"] = "1"
    env["METAL_DEBUG_ERROR_MODE"] = "0"
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            
            # If it fails, try without vision quantization
            print("\nTrying without vision quantization...")
            cmd.remove("--q-bits-vision")
            cmd.remove("5")
            result = subprocess.run(cmd, env=env)
            
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    convert_with_checkpointing()