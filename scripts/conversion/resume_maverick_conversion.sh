#!/bin/bash
# Resume Maverick model conversion

echo "🔧 Resuming Maverick-17B conversion..."

# Check what we have
echo "Current conversion status:"
# Use environment variable or default path
MODELS_DIR=${LMSTUDIO_MODELS_DIR:-~/.lmstudio/models}
CONVERTED=$(ls "$MODELS_DIR"/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-MLX-Q5/model-*.safetensors 2>/dev/null | wc -l)
echo "Converted: $CONVERTED/72 files"

# Option 1: Try to complete with mlx_lm (recommended)
echo ""
echo "Option 1: Complete conversion with mlx_lm (recommended):"
cat << 'EOF'
cd ~/.lmstudio/mlx_lm
uv run mlx_lm.convert \
  --hf-path meta-llama/Llama-4-Maverick-17B-128E-Instruct \
  --mlx-path ~/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-MLX-Q4 \
  --dtype float16 -q --q-bits 4 --q-group-size 64
EOF

# Option 2: Use the partial conversion
echo ""
echo "Option 2: Try to use partial conversion (risky):"
echo "- Model might work with only 33/72 files"
echo "- But likely will fail when accessing later layers"

# Option 3: Download pre-converted version
echo ""
echo "Option 3: Check if someone already converted it:"
echo "https://huggingface.co/models?search=Maverick%20MLX"

# Clean up advice
echo ""
echo "To free space, you can remove the failed conversion:"
echo "rm -rf ~/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-MLX-Q5"
echo ""
echo "And the huge HF cache after successful conversion:"
echo "rm -rf ~/.cache/huggingface/hub/models--meta-llama--Llama-4-Maverick-17B-128E-Instruct"