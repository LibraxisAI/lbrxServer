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
    # Get first VLM model from config
    VLM_MODEL=$(grep -A5 '"server": "mlx_vlm"' src/model_config.py | grep '"id":' | head -1 | cut -d'"' -f4)
    if [ -n "$VLM_MODEL" ]; then
        nohup uv run mlx_vlm.server \
            --model "$VLM_MODEL" \
            --port 8081 \
            > logs/vlm_server.log 2>&1 &
    fi
    echo -e "${GREEN}VLM server started on port 8081${RESET}"
fi

# Create logs directory
mkdir -p logs

# Start main LLM server
echo -e "${CYAN}Starting main LLM server...${RESET}"

# Start the server
if [ "$1" == "dev" ]; then
    echo -e "${YELLOW}Starting in development mode (HTTP on port 9123)...${RESET}"
    export SERVER_PORT=9123
    export ENABLE_AUTH=true
    export ENABLE_METRICS=true
    uv run -m src.main
else
    echo -e "${GREEN}Starting in production mode (HTTPS on port 443)...${RESET}"
    
    # Check SSL certificates
    if [ -z "$SSL_CERT" ] || [ -z "$SSL_KEY" ]; then
        echo -e "${RED}Error: SSL certificates required for production mode${RESET}"
        echo -e "${YELLOW}Set SSL_CERT and SSL_KEY in .env or environment${RESET}"
        echo -e "${YELLOW}For development, use: ./start_server.sh dev${RESET}"
        exit 1
    fi
    
    if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
        echo -e "${RED}Error: SSL certificate files not found${RESET}"
        echo -e "${YELLOW}SSL_CERT: $SSL_CERT${RESET}"
        echo -e "${YELLOW}SSL_KEY: $SSL_KEY${RESET}"
        exit 1
    fi
    
    export SERVER_PORT=443
    export ENABLE_AUTH=true
    export ENABLE_METRICS=true
    nohup uv run -m src.main > logs/server.log 2>&1 &
    SERVER_PID=$!
    
    echo -e "${GREEN}Server started with PID: $SERVER_PID${RESET}"
    echo $SERVER_PID > server.pid
    
    # Wait and check if server started successfully
    sleep 5
    if ps -p $SERVER_PID > /dev/null; then
        echo -e "${GREEN}✓ Server is running${RESET}"
        echo -e "${CYAN}API available at:${RESET}"
        echo -e "  - https://localhost/api/v1"
        echo -e "  - https://$PRIMARY_DOMAIN/api/v1 (if configured)"
        echo -e "${CYAN}Logs: tail -f logs/server.log${RESET}"
    else
        echo -e "${RED}✗ Server failed to start${RESET}"
        echo -e "${RED}Check logs: cat logs/server.log${RESET}"
        exit 1
    fi
fi