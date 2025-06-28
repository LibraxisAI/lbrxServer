# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Production-ready MLX LLM server implementing native Apple Silicon optimization for VISTA and LibraXis services. Runs on Dragon M3 Ultra (512GB RAM) with OpenAI-compatible API endpoints.

## Build and Development Commands

### Quick Start
```bash
# Initialize and install dependencies (using uv)
uv init
uv sync

# Start development server
./scripts/start_server.sh dev

# Start production server (daemonized)
./scripts/start_server.sh

# Check server status
./scripts/manage.sh status
```

### Model Operations
```bash
# Convert model to MLX format
./convert-to-mlx-enhanced.sh <model_path_or_hf_id>

# Test model with MLX CLI
uv run mlx_lm.chat --model mlx-community/DeepSeek-V3-0324-4bit
uv run mlx_lm.generate --model "nemotron-ultra" --prompt "Test" --max-tokens 50

# Quantization example
uv run mlx_lm.convert --hf-path "mistralai/Mistral-7B-Instruct-v0.3" \
               --mlx-path "./mistral-7b-v0.3-4bit" \
               --dtype float16 \
               --quantize --q-bits 4 --q-group-size 64
```

### Testing
```bash
# Run test suite
./test_server.py

# Health check
curl -k https://dragon.fold-antares.ts.net/api/v1/health

# Test API endpoint
curl -X POST https://libraxis.cloud/api/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "nemotron-ultra", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Architecture Overview

### Core Components

- **FastAPI Server** (`src/main.py`): Async web server with lifespan management
  - SSL/TLS support via Tailscale certificates
  - Multi-domain hosting (libraxis.cloud, dragon.fold-antares.ts.net)
  - OpenAI-compatible endpoints

- **Model Manager** (`src/model_manager.py`): Dynamic model lifecycle management
  - Memory-aware loading/unloading (400GB reserved for models)
  - Support for LLM, VLM, Reranker, and Embedding models
  - Lazy loading with caching

- **Authentication** (`src/auth.py`): Multi-layer security
  - API key authentication for services
  - JWT tokens for sessions
  - Per-service access control

- **Middleware** (`src/middleware.py`): Request processing pipeline
  - Rate limiting (configurable per service)
  - CORS configuration
  - Request/response logging

### Model Architecture Support

1. **Standard LLMs** (via mlx-lm)
   - DeciLMForCausalLM (Nemotron custom architecture)
   - Llama, Mistral, Qwen families
   - Command-R, Gemma architectures

2. **Vision-Language Models** (via mlx_vlm)
   - Requires separate mlx_vlm.server on port 8081
   - Llama-Scout, Pixtral, Qwen-VL support
   - Auto-launched when VLM models configured

3. **Specialized Models**
   - Rerankers for search optimization
   - Embedding models for RAG pipelines
   - Audio models (Whisper) - future support

### Infrastructure Split

**Dragon (M3 Ultra, 512GB RAM)**
- Primary LLM inference server
- Hosts all language and vision models
- SSL endpoints: libraxis.cloud, dragon.fold-antares.ts.net

**Studio (M2 Ultra, 128GB RAM)**
- Voice processing workloads
- Whisper transcription services
- Audio synthesis pipelines

## Key Implementation Details

### Memory Management
```python
# Total system: 512GB
# Reserved for models: 400GB
# Safety margin: 112GB

# Model memory estimates (from model_config.py):
- Nemotron 253B Q5: 160GB
- Command-A 03 Q8: 52GB
- Qwen3 14B Q8: 15GB
- Llama Scout VLM: 13GB
```

### Model Aliases System
```python
# User-friendly aliases map to full model paths
"nemotron-ultra" → "/path/to/Nemotron-Ultra-253B-v1-mlx-q5"
"command-a" → "mlx-community/command-a-03-2025-q8"
"qwen3-14b" → "mlx-community/qwen-3-14b-lbrx-2.0-q8"
```

### VLM Integration
Vision models require special handling:
1. Separate mlx_vlm.server process on port 8081
2. Automatic launch via start_server.sh
3. Model loading via mlx_vlm instead of mlx_lm

### ChukSessions Integration (Built-in)
- Integrated as core component (src/chuk_sessions)
- Redis or in-memory storage backends
- Session IDs map to conversation history
- Automatic context management with TTL
- Full conversation history tracking
- API endpoints for session management

## API Endpoints

### OpenAI-Compatible
- `POST /api/v1/chat/completions` - Chat completions (with session support)
- `POST /api/v1/completions` - Text completions
- `GET /api/v1/models` - List available models

### Model Management
- `POST /api/v1/models/{model_id}/load` - Load specific model
- `POST /api/v1/models/{model_id}/unload` - Unload model
- `GET /api/v1/models/memory/usage` - Memory statistics

### Session Management (ChukSessions)
- `POST /api/v1/sessions` - Create new session
- `GET /api/v1/sessions/{session_id}` - Get session details
- `GET /api/v1/sessions/{session_id}/messages` - Get conversation history
- `DELETE /api/v1/sessions/{session_id}` - Delete session
- `GET /api/v1/sessions` - List active sessions

### System Monitoring
- `GET /api/v1/health` - Health check
- `GET /metrics` - Prometheus metrics (port 9090)

## Service Integration

Each service has dedicated API key:
- **VISTA**: Primary veterinary PIMS
- **whisplbrx**: Whisper transcription
- **forkmeASAPp**: Code generation
- **AnyDataNext**: Data processing
- **lbrxvoice**: Voice synthesis

## MLX Framework Context

### MLX Advantages on Apple Silicon
- Unified memory architecture (no GPU transfers)
- Hardware acceleration via Metal/ANE
- 4-bit/8-bit quantization with minimal quality loss
- ~250 tokens/s on M3 Max for 1B models

### Model Conversion Best Practices
```bash
# Always prefer safetensors format
# Use latest mlx-lm version (check with: pip show mlx-lm)
# For VLMs, ensure mlx_vlm is updated

# Conversion with optimal settings for M3 Ultra
uv run mlx_lm.convert \
  --hf-path <model> \
  --mlx-path <output> \
  --quantize \
  --q-bits 4 \
  --q-group-size 128
```

### Common MLX Operations
```python
# Load model with KV cache (recommended)
from mlx_lm import load, generate
from mlx_lm.models.cache import make_prompt_cache

model, tokenizer = load("model-path")
cache = make_prompt_cache(model)
text = generate(model, tokenizer, prompt=prompt, prompt_cache=cache)

# Fine-tuning with LoRA
# Use QLoRA (4-bit) for memory efficiency on large models
```

## Development Workflow

### Environment Management
**ALWAYS use uv** - no pip, no conda, no poetry:
```bash
uv sync          # Install/update dependencies
uv add package   # Add new package
uv run command   # Run any command (auto-syncs!)
```

### Testing Checklist
1. Test with primary model (Nemotron)
2. Verify memory management under load
3. Check SSL certificates validity
4. Validate API key authentication
5. Monitor VLM server for vision models

### Debugging
```bash
# Check logs
tail -f logs/server.log

# Monitor memory
watch -n 1 'ps aux | grep mlx'

# Test model directly
uv run python -m mlx_lm.generate --model <path> --prompt "test"
```

## Common Issues and Solutions

### DeciLMForCausalLM Architecture
- Custom architecture not supported by LM Studio
- Use native mlx_lm server instead
- Ensure model has proper config.json with architecture type

### Memory Exhaustion
- Monitor via `/api/v1/models/memory/usage`
- Set MAX_MEMORY_GB in config
- Enable auto-unload for unused models

### SSL Certificate Errors
```bash
# For local testing
curl -k https://localhost:8443/health

# Regenerate Tailscale certs
tailscale cert dragon.fold-antares.ts.net
```

### VLM Server Issues
- Check if mlx_vlm.server is running (port 8081)
- Verify VLM model paths in config
- Ensure sufficient memory for both LLM and VLM servers

## Production Deployment

### Systemd Service
```bash
# Install service
sudo cp mlx-llm-server.service /etc/systemd/system/
sudo systemctl enable mlx-llm-server
sudo systemctl start mlx-llm-server

# View logs
journalctl -u mlx-llm-server -f
```

### Monitoring
- Prometheus metrics: http://localhost:9090
- Health endpoint: https://libraxis.cloud/api/v1/health
- Memory tracking: Built-in memory usage API

### Security Considerations
- API keys stored in environment variables
- SSL/TLS for all production endpoints
- Rate limiting per service
- No external data transmission

## Future Enhancements

1. ~~**Full ChukSessions Implementation**: Complete conversation persistence~~ ✅ DONE
2. **Model Routing**: Service-specific model selection
3. **WebSocket Support**: Real-time streaming
4. **Audio Model Integration**: Whisper support
5. **Multi-Model Serving**: Concurrent model execution
6. **A/B Testing**: Model comparison framework
7. **Session Analytics**: Usage patterns and metrics
8. **Session Sharing**: Multi-user conversation support

## Important Notes

- This server replaces LM Studio for production use
- Designed specifically for M3 Ultra optimization
- All models must be in MLX format (use conversion script)
- VLM models require additional server process
- Memory management is critical with large models