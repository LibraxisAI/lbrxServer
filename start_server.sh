#!/bin/bash
# Startup script for MLX LLM Server with VLM support

# Colors
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
CYAN="\033[36m"
RESET="\033[0m"

echo -e "${CYAN}Starting MLX LLM Server...${RESET}"

# Check if Redis is running (needed for ChukSessions)
if ! pgrep -x "redis-server" > /dev/null; then
    echo -e "${YELLOW}Starting Redis server...${RESET}"
    redis-server --daemonize yes
fi

# Kill any existing mlx_lm server processes
echo -e "${YELLOW}Stopping any existing MLX servers...${RESET}"
pkill -f "mlx_lm.server"
pkill -f "mlx_vlm.server"
pkill -f "src.main"
sleep 2

# Start VLM server for vision models (if needed)
if grep -q "auto_load.*true.*mlx_vlm" src/model_config.py; then
    echo -e "${CYAN}Starting MLX-VLM server for vision models...${RESET}"
    nohup uv run mlx_vlm.server \
        --model /Users/polyversai/.lmstudio/models/mlx-community/Llama-4-Scout-17B-16E-Instruct-6bit \
        --port 8081 \
        > logs/vlm_server.log 2>&1 &
    echo -e "${GREEN}VLM server started on port 8081${RESET}"
fi

# Create logs directory
mkdir -p logs

# Start main LLM server
echo -e "${CYAN}Starting main LLM server...${RESET}"

# Export environment variables
export SERVER_PORT=443
export ENABLE_AUTH=true
export ENABLE_METRICS=true

# Start the server
if [ "$1" == "dev" ]; then
    echo -e "${YELLOW}Starting in development mode...${RESET}"
    uv run python -m src.main
else
    echo -e "${GREEN}Starting in production mode...${RESET}"
    nohup uv run python -m src.main > logs/server.log 2>&1 &
    SERVER_PID=$!
    
    echo -e "${GREEN}Server started with PID: $SERVER_PID${RESET}"
    echo $SERVER_PID > server.pid
    
    # Wait and check if server started successfully
    sleep 5
    if ps -p $SERVER_PID > /dev/null; then
        echo -e "${GREEN}✓ Server is running${RESET}"
        echo -e "${CYAN}API available at:${RESET}"
        echo -e "  - https://libraxis.cloud/api/v1"
        echo -e "  - https://dragon.fold-antares.ts.net/api/v1"
        echo -e "${CYAN}Logs: tail -f logs/server.log${RESET}"
    else
        echo -e "${RED}✗ Server failed to start${RESET}"
        echo -e "${RED}Check logs: cat logs/server.log${RESET}"
        exit 1
    fi
fi