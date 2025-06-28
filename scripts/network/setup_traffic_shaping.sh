#!/bin/bash
# Advanced Traffic Shaping for macOS
# Uses both route-based and application-based routing

GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${CYAN}=== Advanced Network Traffic Shaping ===${RESET}"

# Function to set up application-specific routing
setup_app_routing() {
    echo -e "${YELLOW}Setting up application-specific routing...${RESET}"
    
    # Create network locations
    echo -e "${GREEN}Creating network locations...${RESET}"
    
    # Create Tailscale location (Ethernet priority)
    sudo networksetup -createlocation "Tailscale" populate
    sudo networksetup -switchtolocation "Tailscale"
    sudo networksetup -ordernetworkservices "Ethernet" "Wi-Fi"
    
    # Create General location (Wi-Fi priority)  
    sudo networksetup -createlocation "General" populate
    sudo networksetup -switchtolocation "General"
    sudo networksetup -ordernetworkservices "Wi-Fi" "Ethernet"
    
    # Switch based on need
    sudo networksetup -switchtolocation "Tailscale"
}

# Function to create routing rules using pf
setup_pf_rules() {
    echo -e "${YELLOW}Setting up packet filter rules...${RESET}"
    
    # Backup current pf configuration
    sudo cp /etc/pf.conf /etc/pf.conf.backup
    
    # Create custom pf rules
    cat > /tmp/pf-tailscale.conf << 'EOF'
# Custom PF rules for traffic routing
# Redirect Tailscale traffic to Ethernet

# Define interfaces
ethernet = "en0"
wifi = "en1"

# Define networks
tailscale = "{ 100.64.0.0/10, 100.0.0.0/8 }"
production = "{ 178.183.101.202/32 }"

# Create routing rules
# Force Tailscale through Ethernet
pass out route-to ($ethernet) from any to $tailscale
pass out route-to ($ethernet) from any to $production

# Default route through Wi-Fi for everything else
pass out route-to ($wifi) from any to !$tailscale
EOF
    
    # Load the rules
    sudo pfctl -f /tmp/pf-tailscale.conf
    sudo pfctl -e
    
    echo -e "${GREEN}✓ Packet filter rules loaded${RESET}"
}

# Function to set up split DNS
setup_split_dns() {
    echo -e "${YELLOW}Setting up split DNS...${RESET}"
    
    # Create resolver configuration for Tailscale domains
    sudo mkdir -p /etc/resolver
    
    # Tailscale DNS
    cat > /tmp/tailscale.resolver << EOF
nameserver 100.100.100.100
search fold-antares.ts.net
EOF
    sudo cp /tmp/tailscale.resolver /etc/resolver/ts.net
    
    # LibraXis DNS
    cat > /tmp/libraxis.resolver << EOF
nameserver 8.8.8.8
nameserver 1.1.1.1
EOF
    sudo cp /tmp/libraxis.resolver /etc/resolver/libraxis.cloud
    
    echo -e "${GREEN}✓ Split DNS configured${RESET}"
}

# Function to create a traffic monitoring dashboard
create_monitor() {
    echo -e "${YELLOW}Creating traffic monitor...${RESET}"
    
    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
    
    cat > "$PROJECT_DIR/monitor_traffic.py" << 'EOF'
#!/usr/bin/env python3
import psutil
import time
import os
from datetime import datetime

def get_network_stats():
    stats = psutil.net_io_counters(pernic=True)
    return {
        'en0': stats.get('en0', None),
        'en1': stats.get('en1', None)
    }

def format_bytes(bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def main():
    print("\033[36m=== Network Traffic Monitor ===\033[0m")
    print("Ethernet (en0) - Tailscale | Wi-Fi (en1) - General\n")
    
    prev_stats = get_network_stats()
    
    while True:
        time.sleep(1)
        curr_stats = get_network_stats()
        
        # Calculate speeds
        en0_rx_speed = 0
        en0_tx_speed = 0
        en1_rx_speed = 0
        en1_tx_speed = 0
        
        if prev_stats['en0'] and curr_stats['en0']:
            en0_rx_speed = curr_stats['en0'].bytes_recv - prev_stats['en0'].bytes_recv
            en0_tx_speed = curr_stats['en0'].bytes_sent - prev_stats['en0'].bytes_sent
            
        if prev_stats['en1'] and curr_stats['en1']:
            en1_rx_speed = curr_stats['en1'].bytes_recv - prev_stats['en1'].bytes_recv
            en1_tx_speed = curr_stats['en1'].bytes_sent - prev_stats['en1'].bytes_sent
        
        # Clear screen and print stats
        os.system('clear')
        print(f"\033[36m=== Network Traffic Monitor === {datetime.now().strftime('%H:%M:%S')}\033[0m")
        print("\033[32mEthernet (en0) - Tailscale Traffic:\033[0m")
        print(f"  ↓ Download: {format_bytes(en0_rx_speed)}/s")
        print(f"  ↑ Upload:   {format_bytes(en0_tx_speed)}/s")
        if curr_stats['en0']:
            print(f"  Total: ↓ {format_bytes(curr_stats['en0'].bytes_recv)} | ↑ {format_bytes(curr_stats['en0'].bytes_sent)}")
        
        print("\n\033[33mWi-Fi (en1) - General Traffic:\033[0m")
        print(f"  ↓ Download: {format_bytes(en1_rx_speed)}/s")
        print(f"  ↑ Upload:   {format_bytes(en1_tx_speed)}/s")
        if curr_stats['en1']:
            print(f"  Total: ↓ {format_bytes(curr_stats['en1'].bytes_recv)} | ↑ {format_bytes(curr_stats['en1'].bytes_sent)}")
        
        # Calculate percentage split
        total_rx = en0_rx_speed + en1_rx_speed
        total_tx = en0_tx_speed + en1_tx_speed
        
        if total_rx > 0:
            en0_rx_pct = (en0_rx_speed / total_rx) * 100
            en1_rx_pct = (en1_rx_speed / total_rx) * 100
            print(f"\n\033[36mTraffic Split (Download):\033[0m")
            print(f"  Ethernet: {en0_rx_pct:.1f}% | Wi-Fi: {en1_rx_pct:.1f}%")
        
        prev_stats = curr_stats

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
EOF
    
    chmod +x "$PROJECT_DIR/monitor_traffic.py"
    echo -e "${GREEN}✓ Traffic monitor created${RESET}"
}

# Function to test the configuration
test_config() {
    echo -e "\n${CYAN}Testing network configuration...${RESET}"
    
    # Test Tailscale routing
    echo -e "${YELLOW}1. Testing Tailscale routing:${RESET}"
    TAILSCALE_ROUTE=$(route get 100.64.0.1 2>/dev/null | grep "interface:" | awk '{print $2}')
    if [[ "$TAILSCALE_ROUTE" == "en0" ]]; then
        echo -e "   ${GREEN}✓ Tailscale routes through Ethernet (en0)${RESET}"
    else
        echo -e "   ${RED}✗ Tailscale routes through $TAILSCALE_ROUTE${RESET}"
    fi
    
    # Test general internet routing
    echo -e "${YELLOW}2. Testing general internet routing:${RESET}"
    INTERNET_ROUTE=$(route get 8.8.8.8 2>/dev/null | grep "interface:" | awk '{print $2}')
    if [[ "$INTERNET_ROUTE" == "en1" ]]; then
        echo -e "   ${GREEN}✓ Internet routes through Wi-Fi (en1)${RESET}"
    else
        echo -e "   ${YELLOW}! Internet routes through $INTERNET_ROUTE${RESET}"
    fi
    
    # Test DNS resolution
    echo -e "${YELLOW}3. Testing DNS resolution:${RESET}"
    if dig +short dragon.fold-antares.ts.net @100.100.100.100 > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Tailscale DNS working${RESET}"
    else
        echo -e "   ${RED}✗ Tailscale DNS not responding${RESET}"
    fi
}

# Main execution
case "$1" in
    full)
        echo -e "${CYAN}Full setup with all features...${RESET}"
        ./configure_network_routing.sh configure
        setup_split_dns
        create_monitor
        test_config
        echo -e "\n${GREEN}✓ Full configuration complete!${RESET}"
        echo -e "${YELLOW}Run './monitor_traffic.py' to see live traffic split${RESET}"
        ;;
    dns)
        setup_split_dns
        ;;
    monitor)
        create_monitor
        ;;
    test)
        test_config
        ;;
    *)
        echo -e "${CYAN}Advanced Traffic Shaping Setup${RESET}"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  full    - Complete setup with routing, DNS, and monitoring"
        echo "  dns     - Set up split DNS only"
        echo "  monitor - Create traffic monitor only"
        echo "  test    - Test current configuration"
        echo ""
        echo "After setup, use:"
        echo "  ./configure_network_routing.sh configure - Apply routing"
        echo "  ./monitor_traffic.py - Monitor traffic split"
        ;;
esac