# MLX LLM Server - Deployment Guide

## Prerequisites

### Hardware Requirements
- **Minimum**: Apple Silicon Mac with 32GB RAM (M2 Pro/Max)
- **Recommended**: M3 Ultra with 128GB+ RAM
- **Production**: M3 Ultra with 512GB RAM

### Software Requirements
- macOS 14.0+ (Sonoma)
- Python 3.11 or 3.12
- Redis 7.0+ (for session storage)
- Tailscale (for SSL certificates)
- uv package manager

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/LibraXisAI/mlx-llm-server.git
cd mlx-llm-server

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize environment
uv sync

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file:

```bash
# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=443
PRIMARY_DOMAIN=libraxis.cloud
TAILSCALE_DOMAIN=dragon.fold-antares.ts.net

# Model Configuration
MODELS_DIR=/Users/polyversai/.lmstudio/models
DEFAULT_MODEL=nemotron-ultra
MAX_MODEL_MEMORY_GB=400

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
SESSION_TTL_HOURS=24

# Authentication
API_KEYS=["your-vista-key", "your-whisplbrx-key"]
JWT_SECRET=your-secret-key-here

# SSL Certificates
SSL_CERT=/Users/polyversai/.ssl/dragon.crt
SSL_KEY=/Users/polyversai/.ssl/dragon.key
```

### 3. Generate SSL Certificates

```bash
# Using Tailscale
tailscale cert dragon.fold-antares.ts.net

# Move to SSL directory
mkdir -p ~/.ssl
mv dragon.fold-antares.ts.net.crt ~/.ssl/dragon.crt
mv dragon.fold-antares.ts.net.key ~/.ssl/dragon.key
chmod 600 ~/.ssl/*
```

### 4. Start Services

```bash
# Start Redis (if not already running)
brew services start redis

# Start development server
./start_server.sh dev

# Or start production server (daemonized)
./start_server.sh
```

## Production Deployment

### 1. System Preparation

```bash
# Create service user (optional)
sudo dscl . -create /Users/mlxserver
sudo dscl . -create /Users/mlxserver UserShell /bin/bash

# Create directories
sudo mkdir -p /opt/mlx-llm-server
sudo mkdir -p /var/log/mlx-llm-server
sudo mkdir -p /etc/mlx-llm-server
```

### 2. Install as System Service

#### Using launchd (macOS)

Create `/Library/LaunchDaemons/ai.libraxis.mlx-llm-server.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.libraxis.mlx-llm-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/mlx-llm-server/.venv/bin/python</string>
        <string>-m</string>
        <string>src.main</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/opt/mlx-llm-server</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>StandardOutPath</key>
    <string>/var/log/mlx-llm-server/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/mlx-llm-server/stderr.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load the service:

```bash
sudo launchctl load /Library/LaunchDaemons/ai.libraxis.mlx-llm-server.plist
sudo launchctl start ai.libraxis.mlx-llm-server
```

### 3. Model Setup

#### Download Models

```bash
# Create models directory
mkdir -p ~/.lmstudio/models

# Download models using Hugging Face CLI
pip install huggingface-hub
huggingface-cli login

# Download specific models
huggingface-cli download mlx-community/Nemotron-Ultra-253B-v1-mlx-q5 \
  --local-dir ~/.lmstudio/models/nemotron-ultra

huggingface-cli download mlx-community/command-a-03-2025-q8 \
  --local-dir ~/.lmstudio/models/command-a
```

#### Convert Models to MLX Format

```bash
# For standard LLMs
./convert-to-mlx-enhanced.sh mistralai/Mistral-7B-Instruct-v0.3

# For custom architectures (DeciLM)
uv run mlx_lm.convert \
  --hf-path /path/to/original/model \
  --mlx-path ~/.lmstudio/models/converted-model \
  --quantize --q-bits 4
```

### 4. Configure Model Aliases

Edit `src/model_config.py` to add your models:

```python
MODEL_ALIASES = {
    "nemotron-ultra": "/Users/polyversai/.lmstudio/models/Nemotron-Ultra-253B-v1-mlx-q5",
    "command-a": "mlx-community/command-a-03-2025-q8",
    "your-model": "/path/to/your/model"
}
```

## Network Configuration

### 1. Firewall Rules

```bash
# Allow HTTPS
sudo pfctl -e
echo "pass in proto tcp from any to any port 443" | sudo pfctl -f -

# Allow internal services
echo "pass in proto tcp from any to any port 6379" | sudo pfctl -f -  # Redis
echo "pass in proto tcp from any to any port 9090" | sudo pfctl -f -  # Metrics
```

### 2. Domain Configuration

For `libraxis.cloud`:

1. Add A record pointing to your static IP
2. Configure reverse proxy if needed
3. Update SSL certificates

For Tailscale domain:

```bash
# Ensure Tailscale is running
tailscale up

# Verify domain
tailscale cert dragon.fold-antares.ts.net
```

## Monitoring Setup

### 1. Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'mlx-llm-server'
    static_configs:
      - targets: ['localhost:9090']
```

### 2. Start Monitoring

```bash
# Install Prometheus
brew install prometheus

# Start with config
prometheus --config.file=prometheus.yml
```

### 3. Grafana Dashboard (Optional)

```bash
# Install Grafana
brew install grafana

# Start service
brew services start grafana

# Access at http://localhost:3000
# Import dashboard from monitoring/grafana-dashboard.json
```

## Security Hardening

### 1. API Key Generation

```bash
# Generate secure API keys
uv run python generate_api_keys.py

# Output:
# VISTA: lbrx_vista_prod_xxxxxxxxxxxxx
# whisplbrx: lbrx_whisplbrx_xxxxxxxxxxxxx
# Add these to your .env file
```

### 2. File Permissions

```bash
# Secure configuration files
chmod 600 .env
chmod 600 ~/.ssl/*

# Restrict log access
chmod 750 /var/log/mlx-llm-server
```

### 3. Network Security

```bash
# Limit access to management ports
# Redis - localhost only
echo "bind 127.0.0.1" >> /usr/local/etc/redis.conf

# Prometheus - localhost only
# Add to prometheus.yml:
# web:
#   listen-address: "127.0.0.1:9090"
```

## Backup and Recovery

### 1. Session Backup

```bash
# Backup Redis data
redis-cli --rdb /backup/sessions-$(date +%Y%m%d).rdb

# Restore
redis-cli shutdown
cp /backup/sessions-20240628.rdb /usr/local/var/db/redis/dump.rdb
redis-server
```

### 2. Configuration Backup

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/mlx-llm-server/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp .env "$BACKUP_DIR/"
cp -r src/model_config.py "$BACKUP_DIR/"
tar -czf "$BACKUP_DIR/config.tar.gz" -C "$BACKUP_DIR" .
EOF

chmod +x backup.sh
```

## Troubleshooting

### Common Issues

#### Model Loading Failures

```bash
# Check model path
ls -la ~/.lmstudio/models/

# Verify model format
uv run python -c "from mlx_lm import load; load('model-path')"

# Check memory
vm_stat | grep "Pages free"
```

#### SSL Certificate Errors

```bash
# Verify certificate
openssl x509 -in ~/.ssl/dragon.crt -text -noout

# Check certificate chain
openssl s_client -connect dragon.fold-antares.ts.net:443
```

#### Session Storage Issues

```bash
# Test Redis connection
redis-cli ping

# Check Redis memory
redis-cli info memory

# Clear sessions if needed
redis-cli FLUSHDB
```

### Performance Tuning

#### Memory Optimization

```bash
# Adjust model memory limit in .env
MAX_MODEL_MEMORY_GB=300  # Lower if system is unstable

# Enable memory pressure handling
sudo sysctl vm.compressor_mode=4
```

#### Request Optimization

```bash
# Adjust worker count (usually 1 for MLX)
SERVER_WORKERS=1

# Tune rate limits
RATE_LIMIT_PER_MINUTE=30  # Adjust based on capacity
```

## Health Checks

### Manual Health Check

```bash
# Check server status
curl -k https://localhost/api/v1/health

# Check loaded models
curl -k https://localhost/api/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Test generation
curl -k https://localhost/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nemotron-ultra",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Automated Monitoring

```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="https://localhost/api/v1/health"
RESPONSE=$(curl -s -k -w "\n%{http_code}" "$HEALTH_URL")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" != "200" ]; then
    echo "Health check failed: HTTP $HTTP_CODE"
    # Restart service
    launchctl restart ai.libraxis.mlx-llm-server
fi
EOF

# Add to crontab
crontab -e
# */5 * * * * /path/to/health_check.sh
```

## Scaling Considerations

### Vertical Scaling

1. **Memory**: Add more RAM (up to 512GB on M3 Ultra)
2. **Storage**: Use external NVMe for model storage
3. **CPU**: Upgrade to newer Apple Silicon

### Horizontal Scaling (Future)

1. **Load Balancer**: HAProxy or nginx
2. **Model Sharding**: Split large models across nodes
3. **Session Replication**: Redis Cluster
4. **Service Mesh**: Consul or Kubernetes

## Maintenance

### Regular Tasks

```bash
# Weekly: Update dependencies
uv sync -U

# Monthly: Clear old sessions
redis-cli --eval clear_old_sessions.lua

# Quarterly: Security updates
brew update && brew upgrade
uv run pip audit
```

### Log Rotation

```bash
# Add to /etc/newsyslog.conf
/var/log/mlx-llm-server/*.log    644  7  10000  *  J
```

## Support

- **Issues**: https://github.com/LibraXisAI/mlx-llm-server/issues
- **Discussions**: https://github.com/LibraXisAI/mlx-llm-server/discussions
- **Security**: security@libraxis.cloud