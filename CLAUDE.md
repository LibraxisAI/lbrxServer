# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Server
```bash
# Start development server (port 9123, no SSL)
./scripts/start_server.sh dev

# Start production server (port 443, SSL required)
./scripts/start_server.sh

# Check status
./scripts/manage.sh status

# Run all tests and checks
./test.sh
```

### Testing
```bash
# Full test suite with linting and formatting
./test.sh

# Individual test commands
uv run ruff check .              # Linting
uv run ruff format .             # Format code
uv run pytest tests/ -v          # Unit tests
uv run pytest tests/ --cov=src   # With coverage

# Quick API test
curl http://localhost:9123/api/v1/health
```

### Model Operations
```bash
# Convert model to MLX format
./scripts/conversion/convert-to-mlx-enhanced.sh <model_path_or_hf_id>

# Test model directly
uv run mlx_lm.generate --model "qwen3-14b" --prompt "Test" --max-tokens 50
```

## Architecture

### Core Services Integration
The server provides model inference for multiple services via API key routing:

- **vista_*** → Medical/veterinary reasoning (default: qwen3-14b)
- **fork_*** → Code generation (default: deepseek-coder)
- **whisp_*** → Audio transcription (default: whisper-large-v3)
- **anydatanext_*** → Data processing (default: qwen3-14b)
- **lbrxvoice_*** → Voice synthesis (default: phi-3)

Model routing logic is in `src/model_router.py` - the router automatically selects the appropriate model based on the API key prefix.

### Memory Architecture
On M3 Ultra (512GB):
- Total system: 512GB
- Models allocation: 400GB
- Safety margin: 112GB

Model loading/unloading is managed by `src/model_manager.py` with intelligent memory tracking.

### Session Management
ChukSessions is built-in (`src/chuk_sessions/`):
- Redis backend for production
- In-memory backend for development
- Automatic conversation history tracking
- Session endpoints at `/api/v1/sessions`

### Authentication Flow
1. API key extraction from Authorization header
2. Service identification from key prefix
3. Model routing based on service
4. Request processing with selected model

## Key Development Patterns

### Environment Management
This project uses **uv exclusively** - no pip, conda, or poetry:
```bash
uv sync          # Install dependencies
uv add <pkg>     # Add new package
uv run <cmd>     # Run any command
```

### Configuration
- Development: `.env` file (copy from `.env.example`)
- Production: Environment variables
- Default port: 9123 (dev), 443 (prod)
- Default model: LibraxisAI/Qwen3-14b-MLX-Q5

### Model Configuration
Models are defined in `src/model_config.py`:
- Each model has memory requirements
- Auto-load flag for startup loading
- Priority for memory management
- Aliases for user-friendly names

### API Endpoints Structure
All endpoints follow OpenAI compatibility:
- `/api/v1/chat/completions` - Main chat endpoint with session support
- `/api/v1/models` - Model management
- `/api/v1/sessions` - Session CRUD operations
- `/api/v1/health` - Health monitoring

## Important Implementation Notes

### Model Router
The `ModelRouter` class handles service-based routing:
- Extracts service from API key prefix
- Maps service to appropriate model
- Falls back to default model if needed
- Respects explicit model requests when allowed

### Error Handling
- All endpoints return proper HTTP status codes
- Validation errors return 422 with details
- Model loading errors return 503
- Authentication errors return 401/403

### Performance Considerations
- Models are lazy-loaded on first request
- KV cache is reused for efficiency
- Streaming responses for real-time output
- Connection pooling for Redis sessions

### Security
- API keys validated on every request
- SSL/TLS required for production
- Rate limiting per service
- No sensitive data in logs

## Common Development Tasks

### Adding a New Model
1. Add configuration to `src/model_config.py`
2. Convert model to MLX format if needed
3. Update model router mappings if service-specific
4. Test with: `uv run mlx_lm.generate --model <alias>`

### Modifying Endpoints
1. Update endpoint in `src/endpoints/`
2. Update OpenAPI schema if needed
3. Add/update tests in `tests/`
4. Run `./test.sh` to verify

### Debugging Issues
```bash
# Check logs
tail -f logs/server.log

# Monitor memory usage
curl http://localhost:9123/api/v1/models/memory/usage

# Test model directly
uv run python -c "from src.model_manager import ModelManager; mm = ModelManager(); mm.load_model('qwen3-14b')"
```

## Testing Strategy

### Unit Tests
- Configuration validation
- Model routing logic
- Authentication flows
- Data model validation

### Integration Tests
- End-to-end API calls
- Session persistence
- Model loading/unloading
- Memory management

### Manual Testing
Always test with the default model (qwen3-14b) first, then test service-specific models.