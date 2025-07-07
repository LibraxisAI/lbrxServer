#!/bin/bash
# Start the anti-crash supervisor for lbrxserver

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting LBRXServer Anti-Crash Supervisor${NC}"

# Create required directories
echo "Creating directories..."
mkdir -p /tmp/lbrx_queue/{completed,failed}
mkdir -p /var/log/lbrx-supervisor

# Check if supervisor is already running
if pgrep -f "src.supervisor.supervisor" > /dev/null; then
    echo -e "${YELLOW}⚠️  Supervisor is already running${NC}"
    echo "To restart, run: $0 restart"
    exit 1
fi

# Kill any existing lbrxserver processes
echo "Checking for existing lbrxserver processes..."
if pgrep -f "lbrxserver.*start" > /dev/null; then
    echo -e "${YELLOW}Stopping existing lbrxserver processes...${NC}"
    pkill -f "lbrxserver.*start" || true
    sleep 2
fi

# Start supervisor
cd "$PROJECT_ROOT"
echo -e "${GREEN}Starting supervisor...${NC}"

if [[ "$1" == "daemon" ]]; then
    # Run as daemon
    nohup uv run python -m src.supervisor > /var/log/lbrx-supervisor/startup.log 2>&1 &
    SUPERVISOR_PID=$!
    echo $SUPERVISOR_PID > /tmp/lbrx-supervisor.pid
    
    echo -e "${GREEN}✅ Supervisor started as daemon (PID: $SUPERVISOR_PID)${NC}"
    echo "Logs: /var/log/lbrx-supervisor/"
    echo "Queue: /tmp/lbrx_queue/"
else
    # Run in foreground
    echo "Running in foreground mode (Ctrl+C to stop)..."
    echo "Logs will be written to /var/log/lbrx-supervisor/"
    
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export MLX_MEMORY_LIMIT=0
    export MLX_CACHE_LIMIT=0
    
    uv run python -m src.supervisor
fi