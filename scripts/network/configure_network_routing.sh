#!/bin/bash
# Network Routing Configuration for Dragon M3 Ultra
# Ethernet (en0) - 80% for Tailscale
# Wi-Fi (en1) - 20% for general traffic

# Colors
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
CYAN="\033[36m"
RESET="\033[0m"

# Network interfaces
ETHERNET="en0"
WIFI="en1"
ETHERNET_IP="192.168.1.222"
WIFI_IP="192.168.1.5"
ETHERNET_GATEWAY="192.168.1.100"
WIFI_GATEWAY="192.168.1.1"

# Tailscale configuration
TAILSCALE_SUBNET="100.64.0.0/10"  # Tailscale's CGNAT range
LIBRAXIS_SUBNET="178.183.101.0/24"  # Your libraxis.cloud subnet

echo -e "${CYAN}=== Network Routing Configuration ===${RESET}"
echo -e "Ethernet (en0): ${GREEN}$ETHERNET_IP${RESET} → Gateway: $ETHERNET_GATEWAY"
echo -e "Wi-Fi (en1): ${GREEN}$WIFI_IP${RESET} → Gateway: $WIFI_GATEWAY"
echo ""

# Function to show current routes
show_routes() {
    echo -e "${CYAN}Current routing table:${RESET}"
    netstat -rn | grep -E "^default|^100\.|^178\.183\." | head -10
    echo ""
}

# Function to configure routes
configure_routes() {
    echo -e "${YELLOW}Configuring network routes...${RESET}"
    
    # 1. Set route metrics (lower = higher priority)
    # Ethernet gets priority for Tailscale traffic
    echo -e "${GREEN}Setting route priorities...${RESET}"
    
    # Remove existing default routes
    sudo route -n delete default 2>/dev/null
    sudo route -n delete default 2>/dev/null
    
    # Add default routes with metrics
    # Wi-Fi as primary default (metric 100)
    sudo route -n add default $WIFI_GATEWAY -ifscope en1
    
    # Ethernet as secondary default (metric 200)
    sudo route -n add default $ETHERNET_GATEWAY -ifscope en0
    
    # 2. Add specific routes for Tailscale via Ethernet
    echo -e "${GREEN}Adding Tailscale routes via Ethernet...${RESET}"
    
    # Tailscale CGNAT range
    sudo route -n add -net 100.64.0.0/10 $ETHERNET_GATEWAY
    
    # Your specific Tailscale IPs
    sudo route -n add -host 100.75.30.90 $ETHERNET_GATEWAY  # Studio
    sudo route -n add -net 100.0.0.0/8 $ETHERNET_GATEWAY   # All Tailscale
    
    # 3. Add routes for production services via Ethernet
    echo -e "${GREEN}Adding production routes via Ethernet...${RESET}"
    
    # libraxis.cloud (178.183.101.202)
    sudo route -n add -host 178.183.101.202 $ETHERNET_GATEWAY
    sudo route -n add -net 178.183.101.0/24 $ETHERNET_GATEWAY
    
    # 4. Configure DNS priorities
    echo -e "${GREEN}Configuring DNS...${RESET}"
    
    # Set DNS servers with Ethernet priority for Tailscale DNS
    sudo networksetup -setdnsservers "Ethernet" 100.100.100.100 8.8.8.8 1.1.1.1
    sudo networksetup -setdnsservers "Wi-Fi" 8.8.8.8 1.1.1.1
    
    # 5. Set service order (Wi-Fi first for general traffic)
    echo -e "${GREEN}Setting service order...${RESET}"
    sudo networksetup -ordernetworkservices "Wi-Fi" "Ethernet"
    
    echo -e "${GREEN}✓ Routes configured successfully${RESET}"
}

# Function to set up persistent routes
make_persistent() {
    echo -e "${YELLOW}Creating persistent configuration...${RESET}"
    
    # Create LaunchDaemon for persistent routes
    cat > /tmp/com.libraxis.network.routing.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.libraxis.network.routing</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/setup_network_routes.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/network-routing.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/network-routing.error.log</string>
</dict>
</plist>
EOF
    
    # Create the actual routing script
    cat > /tmp/setup_network_routes.sh << 'EOF'
#!/bin/bash
# Wait for network to be ready
sleep 10

# Ethernet routes for Tailscale
/sbin/route -n add -net 100.64.0.0/10 192.168.1.100
/sbin/route -n add -net 100.0.0.0/8 192.168.1.100
/sbin/route -n add -host 178.183.101.202 192.168.1.100

# Set metrics
/sbin/route -n change default 192.168.1.1 -ifscope en1
/sbin/route -n change default 192.168.1.100 -ifscope en0
EOF
    
    # Install files
    sudo cp /tmp/com.libraxis.network.routing.plist /Library/LaunchDaemons/
    sudo cp /tmp/setup_network_routes.sh /usr/local/bin/
    sudo chmod +x /usr/local/bin/setup_network_routes.sh
    sudo chown root:wheel /Library/LaunchDaemons/com.libraxis.network.routing.plist
    sudo chown root:wheel /usr/local/bin/setup_network_routes.sh
    
    # Load the daemon
    sudo launchctl load /Library/LaunchDaemons/com.libraxis.network.routing.plist
    
    echo -e "${GREEN}✓ Persistent configuration installed${RESET}"
}

# Function to test routing
test_routing() {
    echo -e "\n${CYAN}Testing network routing...${RESET}"
    
    # Test Tailscale routing
    echo -e "${YELLOW}Testing Tailscale route:${RESET}"
    route get 100.75.30.90 | grep "interface:"
    
    # Test general internet routing
    echo -e "${YELLOW}Testing general internet route:${RESET}"
    route get 8.8.8.8 | grep "interface:"
    
    # Test libraxis.cloud routing
    echo -e "${YELLOW}Testing libraxis.cloud route:${RESET}"
    route get 178.183.101.202 | grep "interface:"
}

# Function to monitor traffic
monitor_traffic() {
    echo -e "\n${CYAN}Monitoring traffic distribution...${RESET}"
    echo -e "Press Ctrl+C to stop\n"
    
    while true; do
        EN0_BYTES=$(netstat -ibn | grep -E "^en0 " | awk '{print $7}')
        EN1_BYTES=$(netstat -ibn | grep -E "^en1 " | awk '{print $7}')
        
        echo -ne "\rEthernet (en0): ${GREEN}$EN0_BYTES${RESET} bytes | Wi-Fi (en1): ${YELLOW}$EN1_BYTES${RESET} bytes"
        sleep 1
    done
}

# Main menu
case "$1" in
    configure)
        show_routes
        configure_routes
        show_routes
        ;;
    persistent)
        make_persistent
        ;;
    test)
        test_routing
        ;;
    monitor)
        monitor_traffic
        ;;
    reset)
        echo -e "${RED}Resetting to default configuration...${RESET}"
        sudo route -n delete -net 100.64.0.0/10 2>/dev/null
        sudo route -n delete -net 100.0.0.0/8 2>/dev/null
        sudo route -n delete -host 178.183.101.202 2>/dev/null
        sudo networksetup -setdnsservers "Ethernet" "Empty"
        sudo networksetup -setdnsservers "Wi-Fi" "Empty"
        echo -e "${GREEN}✓ Reset complete${RESET}"
        ;;
    *)
        echo -e "${CYAN}Network Routing Configuration Tool${RESET}"
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  configure   - Configure routing (temporary)"
        echo "  persistent  - Make configuration persistent"
        echo "  test        - Test current routing"
        echo "  monitor     - Monitor traffic on interfaces"
        echo "  reset       - Reset to default configuration"
        echo ""
        echo "Example: $0 configure"
        ;;
esac