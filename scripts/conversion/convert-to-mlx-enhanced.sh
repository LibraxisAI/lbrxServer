#!/bin/bash
# Enhanced MLX Model Conversion Utility
# Supports LLM, VLM, Audio models and modern architectures
# Version 3.0 - June 2025

# Text formatting
BOLD="\033[1m"
BLUE="\033[34m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
CYAN="\033[36m"
MAGENTA="\033[35m"
RESET="\033[0m"

# Detect system specs
TOTAL_MEMORY=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
TOTAL_MEMORY_GB=$((TOTAL_MEMORY / 1073741824))
CPU_BRAND=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown")

# Check if running on M3 Ultra
if [[ "$CPU_BRAND" == *"M3 Ultra"* ]] || [[ "$TOTAL_MEMORY_GB" -ge 400 ]]; then
    IS_M3_ULTRA=true
    echo -e "${BOLD}${MAGENTA}M3 Ultra detected! (${TOTAL_MEMORY_GB}GB RAM)${RESET}"
else
    IS_M3_ULTRA=false
fi

echo -e "${BOLD}${BLUE}================================================${RESET}"
echo -e "${BOLD}${BLUE}   Enhanced MLX Model Conversion Utility v3.0   ${RESET}"
echo -e "${BOLD}${BLUE}================================================${RESET}"
echo -e "Supports: LLM, VLM, Audio models | MLX 0.26.1+\n"

# Function to detect model type
detect_model_type() {
    local model_path=$1
    local config_path=""
    
    # Check if it's a local path or HF repo
    if [[ -f "$model_path/config.json" ]]; then
        config_path="$model_path/config.json"
    else
        # For HF repos, we'll detect after download
        echo "auto"
        return
    fi
    
    # Check config.json for model type hints
    if [[ -f "$config_path" ]]; then
        # Check for vision models
        if grep -q -i "vision\|image\|pixel" "$config_path"; then
            echo "vlm"
            return
        fi
        
        # Check for audio models
        if grep -q -i "audio\|whisper\|speech" "$config_path"; then
            echo "audio"
            return
        fi
        
        # Check for embedding models
        if grep -q -i "embedding\|sentence" "$config_path"; then
            echo "embedding"
            return
        fi
        
        # Check for reranker models
        if grep -q -i "rerank\|cross-encoder" "$config_path"; then
            echo "reranker"
            return
        fi
    fi
    
    echo "llm"
}

# Function to get conversion command based on model type
get_conversion_command() {
    local model_type=$1
    local base_cmd=""
    
    case $model_type in
        "vlm")
            base_cmd="mlx_vlm.convert"
            echo -e "${CYAN}Using MLX-VLM converter for vision model${RESET}"
            ;;
        "audio")
            base_cmd="mlx_whisper.convert"
            echo -e "${CYAN}Using MLX-Whisper converter for audio model${RESET}"
            ;;
        "embedding"|"reranker")
            base_cmd="mlx_lm.convert"
            echo -e "${CYAN}Using standard MLX converter for ${model_type} model${RESET}"
            ;;
        *)
            base_cmd="mlx_lm.convert"
            ;;
    esac
    
    echo "$base_cmd"
}

# Default values
DEFAULT_HF_PATH=""
DEFAULT_OUTPUT_DIR=""
DEFAULT_QUANTIZE="y"
DEFAULT_BITS="5"
DEFAULT_GROUP_SIZE="64"
DEFAULT_DTYPE="bfloat16"
DEFAULT_USE_HFXET="y"

# Model type selection
echo -e "${BOLD}Select model type:${RESET}"
echo -e "  1) LLM - Language Model (default)"
echo -e "  2) VLM - Vision-Language Model"
echo -e "  3) Audio - Speech/Audio Model"
echo -e "  4) Embedding - Text Embedding Model"
echo -e "  5) Reranker - Cross-Encoder Model"
echo -e "  6) Auto-detect"
read -p "> " MODEL_TYPE_CHOICE
MODEL_TYPE_CHOICE=${MODEL_TYPE_CHOICE:-1}

case $MODEL_TYPE_CHOICE in
    1) MODEL_TYPE="llm" ;;
    2) MODEL_TYPE="vlm" ;;
    3) MODEL_TYPE="audio" ;;
    4) MODEL_TYPE="embedding" ;;
    5) MODEL_TYPE="reranker" ;;
    6) MODEL_TYPE="auto" ;;
    *) MODEL_TYPE="llm" ;;
esac

# Get HF Path
echo -e "\n${BOLD}Hugging Face model path or local directory:${RESET}"
echo -e "${CYAN}Examples:${RESET}"
echo -e "  LLM: meta-llama/Llama-3.1-405B"
echo -e "  VLM: OpenGVLab/InternVL2-26B"
echo -e "  Audio: openai/whisper-large-v3"
echo -e "  Local: /path/to/model"
read -p "> " HF_PATH

# Auto-detect if needed
if [[ "$MODEL_TYPE" == "auto" ]]; then
    MODEL_TYPE=$(detect_model_type "$HF_PATH")
    echo -e "${GREEN}Detected model type: ${MODEL_TYPE}${RESET}"
fi

# Get base conversion command
CONVERT_CMD=$(get_conversion_command "$MODEL_TYPE")

# Use hf-xet for downloads (not for audio models)
if [[ "$MODEL_TYPE" != "audio" ]]; then
    echo -e "\n${BOLD}Use hf-xet for faster download? [y/n]${RESET}"
    echo -e "(10x faster downloads with chunk deduplication)"
    echo -e "Default: ${DEFAULT_USE_HFXET}"
    read -p "> " USE_HFXET
    USE_HFXET=${USE_HFXET:-$DEFAULT_USE_HFXET}
    
    if [[ "$USE_HFXET" == "y" ]]; then
        echo -e "${GREEN}✓ hf-xet enabled for download${RESET}"
        export HF_HUB_ENABLE_HF_TRANSFER=1
    fi
fi

# Suggest output directory
MODEL_NAME=$(basename "$HF_PATH")
DEFAULT_OUTPUT_DIR="LibraxisAI/${MODEL_NAME}-MLX-Q5"

echo -e "\n${BOLD}Output MLX model directory:${RESET}"
echo -e "(Default: ${DEFAULT_OUTPUT_DIR})"
read -p "> " OUTPUT_DIR
OUTPUT_DIR=${OUTPUT_DIR:-$DEFAULT_OUTPUT_DIR}

# Data type selection
echo -e "\n${BOLD}Model data type:${RESET}"
echo -e "(Default: ${DEFAULT_DTYPE}, Options: float16, bfloat16, float32)"
if [[ "$IS_M3_ULTRA" == true ]]; then
    echo -e "${MAGENTA}💡 M3 Ultra tip: bfloat16 recommended for best performance${RESET}"
fi
read -p "> " DTYPE
DTYPE=${DTYPE:-$DEFAULT_DTYPE}

# Quantization options (not for audio models)
if [[ "$MODEL_TYPE" != "audio" ]]; then
    echo -e "\n${BOLD}Quantize the model? [y/n]${RESET}"
    echo -e "(Default: ${DEFAULT_QUANTIZE})"
    read -p "> " QUANTIZE
    QUANTIZE=${QUANTIZE:-$DEFAULT_QUANTIZE}
    
    if [[ "$QUANTIZE" == "y" ]]; then
        echo -e "\n${BOLD}Quantization bits:${RESET}"
        echo -e "Options:"
        echo -e "  2 - Extreme compression (lowest quality)"
        echo -e "  3 - High compression"
        echo -e "  4 - Standard compression (good balance)"
        echo -e "  ${GREEN}5 - Recommended (best quality/size ratio)${RESET}"
        echo -e "  6 - Low compression"
        echo -e "  8 - Minimal compression (highest quality)"
        echo -e "(Default: ${DEFAULT_BITS})"
        read -p "> " BITS
        BITS=${BITS:-$DEFAULT_BITS}
        
        echo -e "\n${BOLD}Group size:${RESET}"
        echo -e "(Default: ${DEFAULT_GROUP_SIZE}, Options: 32, 64, 128)"
        if [[ "$IS_M3_ULTRA" == true ]]; then
            echo -e "${MAGENTA}💡 M3 Ultra tip: Use 64 or 128 for better performance${RESET}"
        fi
        read -p "> " GROUP_SIZE
        GROUP_SIZE=${GROUP_SIZE:-$DEFAULT_GROUP_SIZE}
        
        # Advanced quantization strategies
        echo -e "\n${BOLD}Quantization strategy:${RESET}"
        echo -e "Options:"
        echo -e "  none - Uniform quantization (default)"
        echo -e "  mixed_2_6 - Mix of 2 and 6 bit"
        echo -e "  mixed_3_4 - Mix of 3 and 4 bit"
        echo -e "  mixed_3_6 - Mix of 3 and 6 bit"
        echo -e "  mixed_4_6 - Mix of 4 and 6 bit"
        echo -e "Leave empty for uniform quantization"
        read -p "> " QUANT_STRATEGY
    fi
fi

# Model-specific options
if [[ "$MODEL_TYPE" == "vlm" ]]; then
    echo -e "\n${BOLD}VLM-specific options:${RESET}"
    echo -e "Image resolution (default: auto-detect):"
    read -p "> " IMAGE_RES
fi

# Upload options
echo -e "\n${BOLD}Upload to Hugging Face Hub? (optional):${RESET}"
echo -e "(Leave empty to skip upload)"
read -p "> " UPLOAD_REPO

# Build command
CMD="uv run $CONVERT_CMD"
CMD="$CMD --hf-path $HF_PATH"
CMD="$CMD --mlx-path $OUTPUT_DIR"
CMD="$CMD --dtype $DTYPE"

if [[ "$QUANTIZE" == "y" ]] && [[ "$MODEL_TYPE" != "audio" ]]; then
    CMD="$CMD -q"
    CMD="$CMD --q-bits $BITS"
    CMD="$CMD --q-group-size $GROUP_SIZE"
    
    if [[ ! -z "$QUANT_STRATEGY" ]] && [[ "$QUANT_STRATEGY" != "none" ]]; then
        CMD="$CMD --q-strategy $QUANT_STRATEGY"
    fi
fi

if [[ ! -z "$UPLOAD_REPO" ]]; then
    CMD="$CMD --upload-repo $UPLOAD_REPO"
fi

# Model-specific flags
if [[ "$MODEL_TYPE" == "vlm" ]] && [[ ! -z "$IMAGE_RES" ]]; then
    CMD="$CMD --image-res $IMAGE_RES"
fi

# Memory estimates
echo -e "\n${BOLD}${CYAN}Command Preview:${RESET}"
echo -e "$CMD"

echo -e "\n${BOLD}Expected outcomes:${RESET}"
case $BITS in
    2) echo -e "- Q2: ~87.5% reduction (12.5% of original size)" ;;
    3) echo -e "- Q3: ~81.25% reduction (18.75% of original size)" ;;
    4) echo -e "- Q4: ~75% reduction (25% of original size)" ;;
    5) echo -e "- Q5: ~68.75% reduction (31.25% of original size)" ;;
    6) echo -e "- Q6: ~62.5% reduction (37.5% of original size)" ;;
    8) echo -e "- Q8: ~50% reduction (50% of original size)" ;;
esac

if [[ "$IS_M3_ULTRA" == true ]]; then
    echo -e "${MAGENTA}M3 Ultra: Can handle models up to 400GB comfortably${RESET}"
fi

# Confirm and run
echo -e "\n${BOLD}${YELLOW}Proceed with conversion? [y/n]${RESET}"
read -p "> " CONFIRM

if [[ "$CONFIRM" == "y" ]]; then
    echo -e "\n${GREEN}Starting conversion...${RESET}"
    
    # Set memory limits for M3 Ultra
    if [[ "$IS_M3_ULTRA" == true ]]; then
        export MLX_METAL_MEMORY_LIMIT=$((400 * 1024 * 1024 * 1024))  # 400GB
        export MLX_METAL_CACHE_LIMIT=$((100 * 1024 * 1024 * 1024))   # 100GB
    fi
    
    # Run conversion with timing
    START_TIME=$(date +%s)
    
    eval $CMD
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo -e "\n${GREEN}✓ Conversion completed in $((DURATION / 60)) minutes $((DURATION % 60)) seconds${RESET}"
    
    # Test the converted model
    echo -e "\n${BOLD}Test the converted model? [y/n]${RESET}"
    read -p "> " TEST_MODEL
    
    if [[ "$TEST_MODEL" == "y" ]]; then
        case $MODEL_TYPE in
            "vlm")
                TEST_CMD="uv run mlx_vlm.generate --model $OUTPUT_DIR --image test.jpg --prompt 'Describe this image' --max-tokens 100"
                ;;
            "audio")
                TEST_CMD="uv run mlx_whisper.transcribe --model $OUTPUT_DIR test.wav"
                ;;
            *)
                TEST_CMD="uv run mlx_lm.generate --model $OUTPUT_DIR --prompt 'Hello, world!' --max-tokens 50"
                ;;
        esac
        
        echo -e "\n${CYAN}Test command: $TEST_CMD${RESET}"
        echo -e "${YELLOW}Make sure you have a test file (image/audio) if needed${RESET}"
    fi
else
    echo -e "${RED}Conversion cancelled${RESET}"
fi