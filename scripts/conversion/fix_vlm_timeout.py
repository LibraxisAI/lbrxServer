#!/usr/bin/env python3
"""
Fix VLM conversion timeout by patching the converter
"""
import os
import sys

# CRITICAL: Set limits BEFORE any MLX imports
os.environ['METAL_DEVICE_WRAPPER_TYPE'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
os.environ['MLX_METAL_MEMORY_LIMIT'] = str(450 * 1024**3)
os.environ['MLX_METAL_CACHE_LIMIT'] = str(50 * 1024**3)

# Add mlx_vlm to path
sys.path.insert(0, '/Users/polyversai/.lmstudio/mlx_lm/.venv/lib/python3.12/site-packages')

import gc

import mlx.core as mx
import mlx.nn as nn


def convert_with_aggressive_gc():
    """Convert VLM with aggressive garbage collection"""

    print("🔧 Patched VLM converter starting...")

    # Monkey patch the quantization to run in smaller chunks
    original_quantize = nn.quantize

    def chunked_quantize(model, config, q_group_size=32, q_bits=5):
        """Quantize model layer by layer to avoid GPU timeout"""
        print("Using chunked quantization...")

        # Process vision model separately
        if hasattr(model, 'vision_model'):
            print("Quantizing vision model...")
            model.vision_model = original_quantize(
                model.vision_model,
                group_size=q_group_size,
                bits=q_bits
            )
            gc.collect()
            mx.metal.clear_cache()

        # Process language model layers one by one
        if hasattr(model, 'language_model'):
            print("Quantizing language model layers...")
            for i, layer in enumerate(model.language_model.layers):
                print(f"  Layer {i+1}/{len(model.language_model.layers)}")
                layer = original_quantize(layer, group_size=q_group_size, bits=q_bits)
                gc.collect()
                mx.metal.clear_cache()

        return model

    nn.quantize = chunked_quantize

    try:
        # Run the actual conversion
        from mlx_vlm.convert import convert

        convert(
            hf_path="meta-llama/Llama-4-Maverick-17B-128E-Instruct",
            mlx_path="/Users/polyversai/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-VLM-MLX-Q5",
            quantize=True,
            q_group_size=32,
            q_bits=5,
            dtype="float16",
            low_memory=True  # If this option exists
        )

    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying alternative approach...")

        # Alternative: Use subprocess with timeout handling
        import subprocess
        cmd = [
            sys.executable, "-m", "mlx_vlm.convert",
            "--hf-path", "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
            "--mlx-path", "/Users/polyversai/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-VLM-MLX-Q5",
            "--dtype", "float16",
            "-q", "--q-bits", "5", "--q-group-size", "32"
        ]

        # Run with increased ulimits
        subprocess.run(["ulimit", "-n", "65536"])  # Increase file descriptors
        subprocess.run(cmd)

if __name__ == "__main__":
    print("Make sure you ran: sudo sysctl -w kern.gpu.timeout_ms=600000")
    input("Press Enter when ready...")
    convert_with_aggressive_gc()
