#!/bin/bash
# Management script for MLX LLM Server

GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
CYAN="\033[36m"
RESET="\033[0m"

show_help() {
    echo -e "${CYAN}MLX LLM Server Management${RESET}"
    echo "Usage: ./manage.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start the server in production mode"
    echo "  stop        - Stop the server"
    echo "  restart     - Restart the server"
    echo "  status      - Check server status"
    echo "  logs        - Show server logs"
    echo "  test        - Run test suite"
    echo "  keys        - Generate new API keys"
    echo "  models      - List available models"
    echo "  memory      - Show memory usage"
    echo "  install     - Install/update dependencies"
    echo "  systemd     - Install systemd service"
}

start_server() {
    echo -e "${CYAN}Starting MLX LLM Server...${RESET}"
    ./start_server.sh
}

stop_server() {
    echo -e "${YELLOW}Stopping MLX LLM Server...${RESET}"
    
    if [ -f server.pid ]; then
        PID=$(cat server.pid)
        if ps -p $PID > /dev/null; then
            kill $PID
            echo -e "${GREEN}Server stopped (PID: $PID)${RESET}"
            rm server.pid
        else
            echo -e "${YELLOW}Server not running${RESET}"
            rm server.pid
        fi
    else
        # Try to find and kill by process name
        pkill -f "src.main"
        pkill -f "mlx_lm.server"
        echo -e "${GREEN}All MLX processes stopped${RESET}"
    fi
}

restart_server() {
    stop_server
    sleep 2
    start_server
}

check_status() {
    echo -e "${CYAN}Server Status${RESET}"
    echo "============="
    
    # Check main server
    if [ -f server.pid ] && ps -p $(cat server.pid) > /dev/null 2>&1; then
        PID=$(cat server.pid)
        echo -e "Main Server: ${GREEN}Running${RESET} (PID: $PID)"
        
        # Get memory usage
        MEM=$(ps -o rss= -p $PID | awk '{print $1/1024/1024}')
        echo -e "Memory Usage: ${YELLOW}${MEM:.2f} GB${RESET}"
    else
        echo -e "Main Server: ${RED}Not Running${RESET}"
    fi
    
    # Check if API is responding
    echo -e "\nAPI Health Check:"
    if curl -k -s https://localhost/api/v1/health > /dev/null 2>&1; then
        echo -e "API Status: ${GREEN}Healthy${RESET}"
        curl -k -s https://localhost/api/v1/health | jq -r '.memory_usage'
    else
        echo -e "API Status: ${RED}Not Responding${RESET}"
    fi
    
    # Check Redis
    if pgrep -x "redis-server" > /dev/null; then
        echo -e "\nRedis: ${GREEN}Running${RESET}"
    else
        echo -e "\nRedis: ${RED}Not Running${RESET}"
    fi
}

show_logs() {
    if [ -f logs/server.log ]; then
        echo -e "${CYAN}Server Logs (last 50 lines)${RESET}"
        echo "=========================="
        tail -n 50 logs/server.log
        echo ""
        echo -e "${YELLOW}For live logs: tail -f logs/server.log${RESET}"
    else
        echo -e "${RED}No log file found${RESET}"
    fi
}

run_tests() {
    echo -e "${CYAN}Running Test Suite${RESET}"
    ./test_server.py
}

generate_keys() {
    echo -e "${CYAN}Generating API Keys${RESET}"
    python3 generate_api_keys.py
}

list_models() {
    echo -e "${CYAN}Available Models${RESET}"
    echo "==============="
    
    # Use the API if server is running
    if curl -k -s https://localhost/api/v1/models > /dev/null 2>&1; then
        curl -k -s https://localhost/api/v1/models | jq -r '.data[] | "\(.id)"'
    else
        # List from filesystem
        echo -e "${YELLOW}Server not running, listing from filesystem:${RESET}"
        find /Users/polyversai/.lmstudio/models -maxdepth 2 -name "config.json" | \
            sed 's|/Users/polyversai/.lmstudio/models/||' | \
            sed 's|/config.json||'
    fi
}

show_memory() {
    echo -e "${CYAN}Memory Usage${RESET}"
    echo "============"
    
    if curl -k -s https://localhost/api/v1/models/memory/usage > /dev/null 2>&1; then
        curl -k -s https://localhost/api/v1/models/memory/usage | jq
    else
        echo -e "${RED}Server not running${RESET}"
        # Show system memory
        echo -e "\nSystem Memory:"
        vm_stat | grep -E "Pages (free|active|inactive|speculative|wired down)"
    fi
}

install_deps() {
    echo -e "${CYAN}Installing/Updating Dependencies${RESET}"
    uv sync
    echo -e "${GREEN}Dependencies updated${RESET}"
}

install_systemd() {
    echo -e "${CYAN}Installing systemd service${RESET}"
    
    # For macOS, we use launchd instead
    cat > ~/Library/LaunchAgents/ai.libraxis.mlx-llm-server.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.libraxis.mlx-llm-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/polyversai/.local/bin/uv</string>
        <string>run</string>
        <string>python</string>
        <string>-m</string>
        <string>src.main</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/polyversai/hosted_dev/mlx_lm_servers</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/polyversai/hosted_dev/mlx_lm_servers/logs/server.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/polyversai/hosted_dev/mlx_lm_servers/logs/error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/polyversai/.local/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>HOME</key>
        <string>/Users/polyversai</string>
    </dict>
</dict>
</plist>
EOF
    
    launchctl load ~/Library/LaunchAgents/ai.libraxis.mlx-llm-server.plist
    echo -e "${GREEN}Service installed and started${RESET}"
    echo -e "${YELLOW}To manage: launchctl [start|stop] ai.libraxis.mlx-llm-server${RESET}"
}

# Main command handling
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    test)
        run_tests
        ;;
    keys)
        generate_keys
        ;;
    models)
        list_models
        ;;
    memory)
        show_memory
        ;;
    install)
        install_deps
        ;;
    systemd)
        install_systemd
        ;;
    *)
        show_help
        ;;
esac