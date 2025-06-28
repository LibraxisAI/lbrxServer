#!/bin/bash
# Fix for VLM conversion GPU timeout

echo "🔧 Fixing VLM conversion for large models..."

# 1. Increase GPU timeout
echo "Setting longer GPU timeout..."
sudo sysctl -w kern.gpu.timeout_ms=300000  # 5 minutes

# 2. Set memory limits
echo "Setting memory limits..."
export MLX_METAL_MEMORY_LIMIT=$((400 * 1024 * 1024 * 1024))  # 400GB
export MLX_METAL_CACHE_LIMIT=$((50 * 1024 * 1024 * 1024))    # 50GB

# 3. Alternative: Split conversion
echo "Option 1: Try with smaller group size (faster):"
echo "uv run mlx_vlm.convert --hf-path meta-llama/Llama-4-Maverick-17B-128E-Instruct --mlx-path /Users/polyversai/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-MLX-Q5 --dtype bfloat16 -q --q-bits 5 --q-group-size 32"

echo ""
echo "Option 2: Try without quantization first:"
echo "uv run mlx_vlm.convert --hf-path meta-llama/Llama-4-Maverick-17B-128E-Instruct --mlx-path /Users/polyversai/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-MLX --dtype bfloat16"

echo ""
echo "Option 3: Use standard mlx_lm converter (if VLM features not critical):"
echo "uv run mlx_lm.convert --hf-path meta-llama/Llama-4-Maverick-17B-128E-Instruct --mlx-path /Users/polyversai/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-MLX-Q5 --dtype bfloat16 -q --q-bits 5 --q-group-size 64"