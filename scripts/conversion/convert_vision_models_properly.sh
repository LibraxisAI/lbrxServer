#!/bin/bash
# Proper VLM/Audio/Image model conversion guide

echo "🎓 MLX Model Conversion Masterclass"
echo "==================================="

# 1. FIX GPU TIMEOUT
echo -e "\n1️⃣ Fix GPU timeout for large models:"
cat << 'EOF'
# Increase Metal timeout (needs sudo)
sudo sysctl -w kern.gpu.timeout_ms=600000  # 10 minutes

# Set environment variables BEFORE conversion
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export METAL_DEVICE_WRAPPER_TYPE=1
export MLX_METAL_MEMORY_LIMIT=450000000000  # 450GB
export MLX_METAL_CACHE_LIMIT=50000000000    # 50GB
EOF

# 2. VISION MODELS (VLM)
echo -e "\n2️⃣ Vision-Language Models (like Maverick):"
cat << 'EOF'
# For pure VLM models, use mlx_vlm
uv run mlx_vlm.convert \
  --hf-path MODEL_NAME \
  --mlx-path OUTPUT_PATH \
  --dtype float16 \
  -q --q-bits 5 --q-group-size 32

# For mixed/problematic models, use mlx_lm (loses vision features but works)
uv run mlx_lm.convert \
  --hf-path MODEL_NAME \
  --mlx-path OUTPUT_PATH \
  --dtype float16 \
  -q --q-bits 5 --q-group-size 32 \
  --ignore-modules vision_model  # Skip vision parts
EOF

# 3. AUDIO MODELS (Whisper)
echo -e "\n3️⃣ Audio Models (Whisper):"
cat << 'EOF'
# Whisper uses different converter
uv add mlx-whisper
uv run mlx_whisper.convert \
  --hf-path openai/whisper-large-v3 \
  --mlx-path whisper-large-v3-mlx \
  --dtype float16 \
  -q --q-bits 8  # Whisper works better with Q8
EOF

# 4. IMAGE MODELS (SAM, Stable Diffusion)
echo -e "\n4️⃣ Image Generation/Segmentation:"
cat << 'EOF'
# Stable Diffusion
pip install mlx-stable-diffusion
python -m mlx_stable_diffusion.convert \
  --hf-path stabilityai/stable-diffusion-2-1 \
  --mlx-path sd-2-1-mlx \
  -q --q-bits 8

# Segment Anything (SAM)
pip install mlx-sam
python -m mlx_sam.convert \
  --hf-path facebook/sam-vit-huge \
  --mlx-path sam-huge-mlx
EOF

# 5. CHUNKED CONVERSION FOR HUGE MODELS
echo -e "\n5️⃣ For Maverick specifically (chunked approach):"
cat << 'EOF'
# Split conversion into chunks to avoid timeout
python3 << 'PYTHON'
import os
import sys
sys.path.append(os.path.expanduser('~/.lmstudio/mlx_lm'))

# Import AFTER setting memory limits
os.environ['MLX_METAL_MEMORY_LIMIT'] = '450000000000'
os.environ['MLX_METAL_CACHE_LIMIT'] = '50000000000'

from mlx_lm.convert import convert
from pathlib import Path

# Try conversion with checkpointing
try:
    convert(
        hf_path="meta-llama/Llama-4-Maverick-17B-128E-Instruct",
        mlx_path=Path(os.path.expanduser("~/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-MLX-Q5")),
        quantize=True,
        q_bits=5,
        q_group_size=32,
        dtype="float16",
        # Special flags for large models
        upload_repo=None,
        revision=None,
        dequantize=False
    )
except Exception as e:
    print(f"Error: {e}")
    print("Try with mlx_lm.convert CLI instead")
PYTHON
EOF

# 6. ACTUAL COMMAND FOR MAVERICK
echo -e "\n6️⃣ Run this for Maverick (most likely to work):"
echo -e "${GREEN}cd ~/.lmstudio/mlx_lm${RESET}"
echo -e "${GREEN}export METAL_DEVICE_WRAPPER_TYPE=1${RESET}"
echo -e "${GREEN}export MLX_METAL_MEMORY_LIMIT=450000000000${RESET}"
echo -e "${GREEN}uv run mlx_lm.convert \\
  --hf-path meta-llama/Llama-4-Maverick-17B-128E-Instruct \\
  --mlx-path ~/.lmstudio/models/LibraxisAI/Llama-4-Maverick-17B-128E-Instruct-MLX-Q5 \\
  --dtype float16 -q --q-bits 5 --q-group-size 32${RESET}"

echo -e "\n💡 Pro tips:"
echo "- Use float16 instead of bfloat16 for better compatibility"
echo "- Smaller group_size (32) = faster conversion, tiny quality loss"
echo "- If timeout persists, try Q4 instead of Q5"
echo "- Monitor GPU usage: sudo powermetrics --samplers gpu_power"