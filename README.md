# MLX LLM Server

Production-ready LLM server for VISTA and LibraXis services, powered by MLX on Apple Silicon. Built specifically for M3 Ultra (512GB) with native DeciLMForCausalLM support and integrated ChukSessions for conversation management.

## Features

- **Native MLX Support**: Direct integration with MLX for optimal performance on Apple Silicon
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API endpoints
- **Multi-Domain Support**: Serves on both `libraxis.cloud` and `dragon.fold-antares.ts.net`
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

## Installation

```bash
# Clone the repository
cd ~/hosted_dev/mlx_lm_servers

# Initialize with uv
uv init
uv sync

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

## Configuration

Key settings in `.env`:
- `DEFAULT_MODEL`: Set to your Nemotron model path
- `API_KEYS`: Generate secure API keys for services
- `SSL_CERT/SSL_KEY`: Path to Tailscale certificates

## Running the Server

```bash
# Development
uv run python -m src.main

# Production (with systemd)
sudo cp mlx-llm-server.service /etc/systemd/system/
sudo systemctl enable mlx-llm-server
sudo systemctl start mlx-llm-server
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

## Future Enhancements

1. **ChukSessions Integration**: Full conversation persistence
2. **Model Routing**: Different models for different services
3. **WebSocket Support**: Real-time streaming
4. **Multi-Model Serving**: Concurrent model serving
5. **A/B Testing**: Model comparison capabilities