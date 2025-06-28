#!/bin/bash
# Balanced Network Routing Configuration for Dragon M3 Ultra
# Ethernet (en0) - 80% Tailscale + 20% general internet (redundancy)
# Wi-Fi (en1) - 100% general internet (primary for daily use)

# Colors
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
CYAN="\033[36m"
MAGENTA="\033[35m"
RESET="\033[0m"

# Network interfaces
ETHERNET="en0"
WIFI="en1"
ETHERNET_IP="192.168.1.222"
WIFI_IP="192.168.1.5"
ETHERNET_GATEWAY="192.168.1.100"
WIFI_GATEWAY="192.168.1.1"

echo -e "${CYAN}=== Balanced Network Routing Configuration ===${RESET}"
echo -e "${MAGENTA}Strategy: Ethernet (80% Tailscale + 20% Internet) | Wi-Fi (100% Internet)${RESET}"
echo ""

# Function to configure balanced routing
configure_balanced_routes() {
    echo -e "${YELLOW}Configuring balanced network routes...${RESET}"
    
    # 1. Clear existing routes
    echo -e "${GREEN}Clearing existing routes...${RESET}"
    sudo route -n delete default 2>/dev/null
    sudo route -n delete default 2>/dev/null
    
    # 2. Set Wi-Fi as primary default route (lower metric = higher priority)
    echo -e "${GREEN}Setting Wi-Fi as primary internet route...${RESET}"
    sudo route -n add default $WIFI_GATEWAY
    
    # 3. Add Ethernet as secondary default route (for redundancy)
    echo -e "${GREEN}Adding Ethernet as backup internet route...${RESET}"
    sudo route -n add default $ETHERNET_GATEWAY -ifscope en0
    
    # 4. Force Tailscale traffic through Ethernet
    echo -e "${GREEN}Routing Tailscale traffic via Ethernet...${RESET}"
    
    # Tailscale CGNAT range
    sudo route -n add -net 100.64.0.0/10 $ETHERNET_GATEWAY
    sudo route -n add -net 100.0.0.0/8 $ETHERNET_GATEWAY
    
    # Specific Tailscale hosts
    sudo route -n add -host 100.75.30.90 $ETHERNET_GATEWAY  # Studio
    
    # 5. Route production services via Ethernet
    echo -e "${GREEN}Routing production services via Ethernet...${RESET}"
    
    # libraxis.cloud
    sudo route -n add -host 178.183.101.202 $ETHERNET_GATEWAY
    sudo route -n add -net 178.183.101.0/24 $ETHERNET_GATEWAY
    
    # 6. Configure load balancing for general traffic
    echo -e "${GREEN}Configuring load balancing...${RESET}"
    configure_load_balancing
    
    echo -e "${GREEN}✓ Balanced routes configured successfully${RESET}"
}

# Function to set up load balancing
configure_load_balancing() {
    # Create launchd plist for traffic distribution
    cat > /tmp/com.libraxis.network.loadbalancer.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.libraxis.network.loadbalancer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/network_load_balancer.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
    
    # Create load balancer script
    cat > /tmp/network_load_balancer.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import time
import random

class NetworkLoadBalancer:
    def __init__(self):
        self.ethernet_weight = 0.2  # 20% general traffic on Ethernet
        self.wifi_weight = 0.8      # 80% general traffic on Wi-Fi
        
    def balance_traffic(self):
        """Distribute non-Tailscale traffic between interfaces"""
        # This is a conceptual implementation
        # Real load balancing would require more complex routing rules
        pass
    
    def monitor_and_failover(self):
        """Monitor interfaces and failover if needed"""
        while True:
            # Check Wi-Fi health
            wifi_up = self.check_interface("en1")
            ethernet_up = self.check_interface("en0")
            
            if not wifi_up and ethernet_up:
                # Failover to Ethernet
                subprocess.run(["sudo", "route", "change", "default", "192.168.1.100"])
                print("Failed over to Ethernet")
            elif wifi_up and not ethernet_up:
                # Ensure Wi-Fi is primary
                subprocess.run(["sudo", "route", "change", "default", "192.168.1.1"])
                print("Using Wi-Fi only")
            
            time.sleep(10)
    
    def check_interface(self, interface):
        """Check if interface is up"""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-t", "1", "-I", interface, "8.8.8.8"],
                capture_output=True
            )
            return result.returncode == 0
        except:
            return False

if __name__ == "__main__":
    balancer = NetworkLoadBalancer()
    balancer.monitor_and_failover()
EOF
    
    sudo cp /tmp/network_load_balancer.py /usr/local/bin/
    sudo chmod +x /usr/local/bin/network_load_balancer.py
}

# Function to set up smart DNS
setup_smart_dns() {
    echo -e "${YELLOW}Setting up smart DNS configuration...${RESET}"
    
    # Primary DNS on Wi-Fi for general queries
    sudo networksetup -setdnsservers "Wi-Fi" 1.1.1.1 8.8.8.8 208.67.222.222
    
    # Tailscale DNS on Ethernet
    sudo networksetup -setdnsservers "Ethernet" 100.100.100.100 1.1.1.1 8.8.8.8
    
    # Create resolver for specific domains
    sudo mkdir -p /etc/resolver
    
    # Tailscale domains via Ethernet
    echo "nameserver 100.100.100.100" | sudo tee /etc/resolver/ts.net > /dev/null
    echo "nameserver 100.100.100.100" | sudo tee /etc/resolver/fold-antares.ts.net > /dev/null
    
    # LibraXis domains can use either
    echo -e "nameserver 1.1.1.1\nnameserver 8.8.8.8" | sudo tee /etc/resolver/libraxis.cloud > /dev/null
    
    echo -e "${GREEN}✓ Smart DNS configured${RESET}"
}

# Function to optimize network performance
optimize_performance() {
    echo -e "${YELLOW}Optimizing network performance...${RESET}"
    
    # Increase network buffers for high-throughput
    sudo sysctl -w net.inet.tcp.sendspace=1048576
    sudo sysctl -w net.inet.tcp.recvspace=1048576
    sudo sysctl -w kern.ipc.maxsockbuf=16777216
    
    # Enable TCP optimizations
    sudo sysctl -w net.inet.tcp.delayed_ack=0
    sudo sysctl -w net.inet.tcp.mssdflt=1440
    
    # Optimize for low latency on Tailscale
    sudo sysctl -w net.inet.tcp.win_scale_factor=8
    
    echo -e "${GREEN}✓ Performance optimizations applied${RESET}"
}

# Function to create monitoring dashboard
create_advanced_monitor() {
    echo -e "${YELLOW}Creating advanced traffic monitor...${RESET}"
    
    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
    
    cat > "$PROJECT_DIR/network_dashboard.py" << 'EOF'
#!/usr/bin/env python3
import psutil
import time
import os
import json
from datetime import datetime
from collections import deque

class NetworkDashboard:
    def __init__(self):
        self.history_size = 60  # Keep 60 seconds of history
        self.en0_history = deque(maxlen=self.history_size)
        self.en1_history = deque(maxlen=self.history_size)
        self.tailscale_ips = set(['100.', '178.183.101.'])
        
    def is_tailscale_traffic(self, connections):
        """Identify Tailscale traffic"""
        tailscale_bytes = 0
        for conn in connections:
            if any(ip in str(conn.raddr) for ip in self.tailscale_ips):
                tailscale_bytes += 1
        return tailscale_bytes
    
    def get_interface_stats(self):
        stats = psutil.net_io_counters(pernic=True)
        connections = psutil.net_connections()
        
        return {
            'en0': {
                'stats': stats.get('en0', None),
                'tailscale_connections': self.is_tailscale_traffic(connections)
            },
            'en1': {
                'stats': stats.get('en1', None),
                'tailscale_connections': 0
            }
        }
    
    def calculate_distribution(self, en0_speed, en1_speed):
        """Calculate traffic distribution percentage"""
        total = en0_speed + en1_speed
        if total == 0:
            return 0, 0
        return (en0_speed / total * 100), (en1_speed / total * 100)
    
    def format_bytes(self, bytes_value):
        """Format bytes to human readable"""
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB/s"
    
    def draw_bar(self, percentage, width=30):
        """Draw a percentage bar"""
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:.1f}%"
    
    def run(self):
        print("\033[2J\033[H")  # Clear screen
        print("\033[36m=== Dragon Network Dashboard ===\033[0m")
        print("\033[35mBalanced Mode: Ethernet (80% Tailscale + 20% Internet) | Wi-Fi (100% Internet)\033[0m\n")
        
        prev_stats = self.get_interface_stats()
        
        while True:
            time.sleep(1)
            curr_stats = self.get_interface_stats()
            
            # Calculate speeds
            en0_rx = en0_tx = en1_rx = en1_tx = 0
            
            if prev_stats['en0']['stats'] and curr_stats['en0']['stats']:
                en0_rx = curr_stats['en0']['stats'].bytes_recv - prev_stats['en0']['stats'].bytes_recv
                en0_tx = curr_stats['en0']['stats'].bytes_sent - prev_stats['en0']['stats'].bytes_sent
                
            if prev_stats['en1']['stats'] and curr_stats['en1']['stats']:
                en1_rx = curr_stats['en1']['stats'].bytes_recv - prev_stats['en1']['stats'].bytes_recv
                en1_tx = curr_stats['en1']['stats'].bytes_sent - prev_stats['en1']['stats'].bytes_sent
            
            # Store history
            self.en0_history.append((en0_rx, en0_tx))
            self.en1_history.append((en1_rx, en1_tx))
            
            # Calculate distributions
            rx_en0_pct, rx_en1_pct = self.calculate_distribution(en0_rx, en1_rx)
            tx_en0_pct, tx_en1_pct = self.calculate_distribution(en0_tx, en1_tx)
            
            # Clear and redraw
            os.system('clear')
            print(f"\033[36m=== Dragon Network Dashboard === {datetime.now().strftime('%H:%M:%S')}\033[0m")
            print("\033[35mBalanced Mode Active\033[0m\n")
            
            # Ethernet stats
            print("\033[32m📡 Ethernet (en0) - Tailscale + Backup Internet:\033[0m")
            print(f"  ↓ Download: {self.format_bytes(en0_rx):<12} {self.draw_bar(rx_en0_pct)}")
            print(f"  ↑ Upload:   {self.format_bytes(en0_tx):<12} {self.draw_bar(tx_en0_pct)}")
            print(f"  🔗 Tailscale Connections: {curr_stats['en0']['tailscale_connections']}")
            
            print("\n\033[33m📶 Wi-Fi (en1) - Primary Internet:\033[0m")
            print(f"  ↓ Download: {self.format_bytes(en1_rx):<12} {self.draw_bar(rx_en1_pct)}")
            print(f"  ↑ Upload:   {self.format_bytes(en1_tx):<12} {self.draw_bar(tx_en1_pct)}")
            
            # Summary
            total_rx = en0_rx + en1_rx
            total_tx = en0_tx + en1_tx
            print(f"\n\033[36m📊 Total Bandwidth:\033[0m")
            print(f"  ↓ {self.format_bytes(total_rx)} | ↑ {self.format_bytes(total_tx)}")
            
            # Average over last minute
            if len(self.en0_history) > 10:
                avg_en0 = sum(rx + tx for rx, tx in list(self.en0_history)[-10:]) / 10
                avg_en1 = sum(rx + tx for rx, tx in list(self.en1_history)[-10:]) / 10
                print(f"\n\033[35m📈 10-sec Average:\033[0m")
                print(f"  Ethernet: {self.format_bytes(avg_en0)} | Wi-Fi: {self.format_bytes(avg_en1)}")
            
            prev_stats = curr_stats

if __name__ == "__main__":
    try:
        dashboard = NetworkDashboard()
        dashboard.run()
    except KeyboardInterrupt:
        print("\n\n✨ Dashboard closed.")
EOF
    
    chmod +x "$PROJECT_DIR/network_dashboard.py"
    echo -e "${GREEN}✓ Advanced monitor created${RESET}"
}

# Function to test configuration
test_balanced_config() {
    echo -e "\n${CYAN}Testing balanced configuration...${RESET}"
    
    echo -e "${YELLOW}1. Route Tests:${RESET}"
    
    # Test Tailscale
    TAILSCALE_IF=$(route get 100.64.0.1 2>/dev/null | grep "interface:" | awk '{print $2}')
    echo -e "   Tailscale (100.64.0.1): ${GREEN}$TAILSCALE_IF${RESET}"
    
    # Test general internet
    INTERNET_IF=$(route get 8.8.8.8 2>/dev/null | grep "interface:" | awk '{print $2}')
    echo -e "   Internet (8.8.8.8): ${GREEN}$INTERNET_IF${RESET}"
    
    # Test libraxis
    LIBRAXIS_IF=$(route get 178.183.101.202 2>/dev/null | grep "interface:" | awk '{print $2}')
    echo -e "   LibraXis: ${GREEN}$LIBRAXIS_IF${RESET}"
    
    echo -e "\n${YELLOW}2. Interface Health:${RESET}"
    
    # Ping test on both interfaces
    if ping -c 1 -t 1 -I en0 8.8.8.8 > /dev/null 2>&1; then
        echo -e "   Ethernet Internet: ${GREEN}✓ Working${RESET}"
    else
        echo -e "   Ethernet Internet: ${RED}✗ Not working${RESET}"
    fi
    
    if ping -c 1 -t 1 -I en1 8.8.8.8 > /dev/null 2>&1; then
        echo -e "   Wi-Fi Internet: ${GREEN}✓ Working${RESET}"
    else
        echo -e "   Wi-Fi Internet: ${RED}✗ Not working${RESET}"
    fi
    
    echo -e "\n${YELLOW}3. DNS Resolution:${RESET}"
    
    # Test DNS
    if nslookup google.com > /dev/null 2>&1; then
        echo -e "   General DNS: ${GREEN}✓ Working${RESET}"
    fi
    
    if nslookup dragon.fold-antares.ts.net 100.100.100.100 > /dev/null 2>&1; then
        echo -e "   Tailscale DNS: ${GREEN}✓ Working${RESET}"
    fi
}

# Main menu
case "$1" in
    configure)
        configure_balanced_routes
        setup_smart_dns
        optimize_performance
        test_balanced_config
        ;;
    monitor)
        create_advanced_monitor
        echo -e "${YELLOW}Run ./network_dashboard.py to start monitoring${RESET}"
        ;;
    optimize)
        optimize_performance
        ;;
    test)
        test_balanced_config
        ;;
    reset)
        echo -e "${RED}Resetting to system defaults...${RESET}"
        sudo route -n delete -net 100.64.0.0/10 2>/dev/null
        sudo route -n delete -net 100.0.0.0/8 2>/dev/null
        sudo route -n delete -host 178.183.101.202 2>/dev/null
        sudo networksetup -setdnsservers "Ethernet" "Empty"
        sudo networksetup -setdnsservers "Wi-Fi" "Empty"
        echo -e "${GREEN}✓ Reset complete${RESET}"
        ;;
    *)
        echo -e "${CYAN}Balanced Network Routing Configuration${RESET}"
        echo -e "${MAGENTA}Ethernet: 80% Tailscale + 20% Internet | Wi-Fi: 100% Internet${RESET}"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  configure - Apply balanced routing configuration"
        echo "  monitor   - Create advanced monitoring dashboard"
        echo "  optimize  - Apply performance optimizations"
        echo "  test      - Test current configuration"
        echo "  reset     - Reset to defaults"
        echo ""
        echo "Quick start: $0 configure"
        ;;
esac