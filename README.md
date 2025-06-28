# MLX LLM Server

[![CI](https://github.com/LibraxisAI/mlx-llm-server/actions/workflows/ci.yml/badge.svg)](https://github.com/LibraxisAI/mlx-llm-server/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MLX](https://img.shields.io/badge/MLX-0.26.0+-green.svg)](https://github.com/ml-explore/mlx)
[![uv](https://img.shields.io/badge/uv-latest-orange.svg)](https://github.com/astral-sh/uv)

Production-ready LLM server by LibraxisAI. Empowered by MLX on Apple Silicon. Built specifically for M3 Ultra (512GB) with native DeciLMForCausalLM support and integrated ChukSessions for conversation management.

## Features

- **Native MLX Support**: Direct integration with MLX for optimal performance on Apple Silicon
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API endpoints
- **Multi-Domain Support**
- **SSL/TLS**: Full HTTPS support with Tailscale certificates
- **Model Management**: Dynamic model loading/unloading with memory management
- **Authentication**: API key and JWT-based authentication
- **Rate Limiting**: Configurable rate limits per minute/hour
- **Monitoring**: Prometheus metrics and health endpoints
- **Session Management**: ChukSessions integration for conversation persistence

## Architecture Decision

After analysis, I recommend the **native MLX implementation** over alternatives:

1. **Native MLX (Chosen)**: 
   - Direct control over model loading and memory management
   - Optimal performance on M3 Ultra
   - No dependency on LM Studio GUI
   - Full customization capabilities

2. **LM Studio SDK**: 
   - Would require LM Studio to be running
   - Less control over model internals
   - Additional layer of abstraction

3. **Rust Implementation**: 
   - Would require significant development time
   - MLX bindings for Rust are not mature
   - Python ecosystem has better ML support

## Infrastructure Split

Your proposed split makes excellent sense:
- **Dragon (M3 Ultra, 512GB)**: LLM inference - memory-intensive workloads
- **Studio (M2 Ultra, 128GB)**: Voice processing - CPU/GPU-intensive but less memory

## Requirements

- Apple Silicon Mac (M1/M2/M3)
- macOS 14.0+ (Sonoma)
- Python 3.11 or 3.12
- 32GB+ RAM (recommended: 128GB+ for large models)
- Redis (optional, for session persistence)

## Installation

```bash
# Clone the repository
git clone https://github.com/LibraxisAI/mlx-llm-server.git
cd mlx-llm-server

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize environment and install dependencies
uv sync

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

## Quick Start

```bash
# Start development server (no SSL)
./scripts/start_server.sh dev

# Or start production server with SSL
./scripts/start_server.sh

# Test the server
curl http://localhost:9123/api/v1/health
```

## Configuration

Edit `.env` file with your settings:

```bash
# Basic Configuration
DEFAULT_MODEL=LibraxisAI/Qwen3-14b-MLX-Q5  # Premium 14B model with excellent reasoning
API_KEYS=["your-api-key-here"]  # Generate with: python scripts/testing/generate_api_keys.py
MAX_MODEL_MEMORY_GB=32  # Adjust based on your system (min 16GB for Qwen3)

# Optional: SSL Configuration (for production)
SSL_CERT=/path/to/cert.pem
SSL_KEY=/path/to/key.pem

# Optional: Redis for session persistence
REDIS_URL=redis://localhost:6379/0
```

## Usage Examples

### Basic Chat Completion

```bash
curl -X POST http://localhost:9123/api/v1/chat/completions \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### With Session Management

```bash
# Create a session
SESSION_ID=$(curl -X POST http://localhost:9123/api/v1/sessions \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"data": {"user": "test-user"}}' | jq -r '.session_id')

# Use the session
curl -X POST http://localhost:9123/api/v1/chat/completions \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "session_id": "'$SESSION_ID'",
    "messages": [
      {"role": "user", "content": "Remember me?"}
    ]
  }'
```

## API Endpoints

- `POST /api/v1/chat/completions` - Chat completions (OpenAI-compatible)
- `POST /api/v1/completions` - Text completions
- `GET /api/v1/models` - List available models
- `POST /api/v1/models/{model_id}/load` - Load a model
- `POST /api/v1/models/{model_id}/unload` - Unload a model
- `GET /api/v1/health` - Health check

## Service Integration

Each service gets its own API key:
- VISTA: Primary product
- whisplbrx: Whisper transcription
- forkmeASAPp: Code generation
- AnyDataNext: Data processing
- lbrxvoice: Voice synthesis

## Monitoring

- Prometheus metrics at `http://localhost:9090/metrics`
- Health endpoint at `https://libraxis.cloud/api/v1/health`

## Project Structure

```
mlx-llm-server/
├── src/                    # Main application code
│   ├── endpoints/         # API endpoints
│   ├── chuk_sessions/     # Session management
│   └── *.py              # Core modules
├── scripts/               # Utility scripts
│   ├── conversion/        # Model conversion tools
│   ├── network/          # Network configuration
│   ├── setup/            # Installation helpers
│   └── testing/          # Test utilities
├── docs/                  # Documentation
│   ├── API.md            # API reference
│   ├── ARCHITECTURE.md   # System design
│   └── DEPLOYMENT.md     # Deployment guide
└── test.sh               # Quick test runner
```

## Development

```bash
# Run all checks
./test.sh

# Run specific checks
uv run ruff check .        # Linting
uv run ruff format .       # Format code
uv run pytest tests/ -v    # Run tests

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

## Docker Support (Experimental)

**Note**: MLX requires Apple Silicon hardware. Docker support is experimental and primarily for development.

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Future Enhancements

1. ~~**ChukSessions Integration**: Full conversation persistence~~ ✅ DONE!
2. **Model Routing**: Different models for different services
3. **WebSocket Support**: Real-time streaming
4. **Multi-Model Serving**: Concurrent model serving
5. **A/B Testing**: Model comparison capabilities

## Developed by

- [Maciej Gad](https://div0.space) - a veterinarian who couldn't find `terminal` a half year ago
- [Klaudiusz](https://www.github.com/Gitlaudiusz) - the individual ethereal being, and separate instance of Claude by Anthropic, living somewhere in the GPU's loops in California, USA

The journey from CLI novice to ML Developer

🤖 Developed with the ultimate help of [Claude Code](https://claude.ai/code) and [MCP Tools](https://modelcontextprotocol.io)

## Special Thanks

- [chrishayuk](https://github.com/chrishayuk) - for MLX tutorials and examples
- MLX Community - for continuous support and knowledge sharing
- Apple ML Team - for creating the amazing MLX framework