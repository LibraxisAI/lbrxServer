# MLX LLM Server - Architecture Documentation

## Overview

The MLX LLM Server is a production-ready inference server designed specifically for Apple Silicon, leveraging the MLX framework for optimal performance. It provides OpenAI-compatible APIs while supporting advanced features like session management, multi-model serving, and native DeciLMForCausalLM architectures.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Applications                      │
│  (VISTA, whisplbrx, forkmeASAPp, AnyDataNext, lbrxvoice)       │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────┐
        │             Load Balancer / SSL              │
        │    (libraxis.cloud / dragon.fold-antares)    │
        └──────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                          FastAPI Server                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Middleware  │  │   Routers    │  │   Authentication   │    │
│  │  - CORS     │  │  - Chat      │  │   - API Keys       │    │
│  │  - Logging  │  │  - Models    │  │   - JWT Tokens     │    │
│  │  - Rate Lim │  │  - Sessions  │  │   - Service Auth   │    │
│  └─────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Core Components                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Model Manager   │  │  ChukSessions    │  │   Config     │ │
│  │  - Loading       │  │  - Persistence    │  │  - Env Vars  │ │
│  │  - Memory Mgmt   │  │  - History        │  │  - Defaults  │ │
│  │  - Generation    │  │  - TTL            │  │  - Validation│ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
        ┌───────────────────────┐     ┌───────────────────────┐
        │      MLX-LM Layer     │     │    MLX-VLM Server     │
        │  - LLM Models         │     │  - Vision Models      │
        │  - Tokenizers         │     │  - Port 8081         │
        │  - KV Cache           │     │  - Image Processing   │
        └───────────────────────┘     └───────────────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
        ┌─────────────────────────────────────────────────┐
        │              Storage & Persistence               │
        │  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
        │  │    Redis    │  │  File System │  │ Metrics │ │
        │  │  Sessions   │  │   Models     │  │Prometheus│ │
        │  └─────────────┘  └─────────────┘  └─────────┘ │
        └─────────────────────────────────────────────────┘
```

## Component Details

### 1. FastAPI Application Layer

The main application is built on FastAPI for high-performance async request handling.

**Key Features:**
- Async/await throughout
- Automatic OpenAPI documentation
- Request validation with Pydantic
- Lifespan management for startup/shutdown

**File:** `src/main.py`

### 2. Middleware Stack

Layered middleware provides cross-cutting concerns:

- **CORS**: Configured for multi-domain support
- **Rate Limiting**: Using SlowAPI with Redis backend
- **Logging**: Structured JSON logging
- **Security**: Trusted host validation

**File:** `src/middleware.py`

### 3. Authentication System

Multi-level authentication supporting different use cases:

- **API Keys**: Service-level authentication
- **JWT Tokens**: User session tokens
- **Optional Auth**: Public endpoints

**File:** `src/auth.py`

### 4. Model Manager

Central component managing model lifecycle:

```python
class ModelManager:
    - load_model(model_id) -> Model
    - unload_model(model_id) -> bool
    - generate_completion(model_id, messages, **kwargs) -> str
    - get_memory_usage() -> MemoryStats
```

**Features:**
- Lazy loading with caching
- Memory-aware loading/unloading
- Support for LLM and VLM models
- Automatic tokenizer selection

**File:** `src/model_manager.py`

### 5. ChukSessions Integration

Provides conversation persistence and context management:

```python
class SessionManager:
    - create_session(session_id, data) -> Session
    - get_session(session_id) -> Session
    - add_message(session_id, role, content)
    - get_messages(session_id) -> List[Message]
```

**Features:**
- Redis or in-memory backend
- Automatic TTL management
- Message history tracking
- Session metadata storage

**Directory:** `src/chuk_sessions/`

### 6. Model Configuration

Centralized model registry with metadata:

```python
MODEL_CONFIG = {
    "model_id": {
        "id": "path/to/model",
        "type": ModelType.LLM,
        "memory_gb": 160,
        "context_length": 128000,
        "auto_load": True
    }
}
```

**File:** `src/model_config.py`

## API Design

### OpenAI Compatibility

The server implements OpenAI's API specification for drop-in compatibility:

```http
POST /api/v1/chat/completions
{
    "model": "nemotron-ultra",
    "messages": [...],
    "session_id": "optional-session-id",
    "stream": false
}
```

### Extended Features

Additional endpoints for advanced functionality:

- Model management (load/unload)
- Session management (CRUD operations)
- Memory monitoring
- Health checks

## Data Flow

### Request Processing Pipeline

1. **Client Request** → SSL termination
2. **Middleware** → Auth, rate limit, logging
3. **Router** → Endpoint handler
4. **Session Manager** → Load/update context
5. **Model Manager** → Select and load model
6. **MLX Generation** → Process with model
7. **Response** → Format and return

### Session Flow

```
Client Request with session_id
       ↓
Check Session Exists
       ↓
Load Historical Messages
       ↓
Append New Messages
       ↓
Generate with Full Context
       ↓
Save Assistant Response
       ↓
Return to Client
```

## Memory Management

### Model Memory Allocation

- **Total System**: 512GB (M3 Ultra)
- **Reserved for Models**: 400GB
- **Safety Margin**: 112GB

### Loading Strategy

1. Check available memory
2. Unload least recently used models if needed
3. Load requested model
4. Cache for future requests

### Memory Tracking

```python
{
    "total_gb": 512,
    "available_gb": 350,
    "models_loaded": {
        "nemotron-ultra": 160,
        "command-a": 52
    }
}
```

## Security Architecture

### Network Security

- **SSL/TLS**: Tailscale certificates
- **Domain Validation**: Trusted hosts only
- **CORS**: Strict origin control

### Application Security

- **API Keys**: Per-service unique keys
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Pydantic models
- **No Data Persistence**: Except sessions

## Deployment Architecture

### Single Node (Current)

```
Dragon M3 Ultra (512GB)
├── MLX LLM Server (Port 443)
├── MLX VLM Server (Port 8081)
├── Redis (Port 6379)
└── Prometheus (Port 9090)
```

### Multi-Node (Future)

```
Load Balancer
├── Dragon M3 Ultra (Primary)
├── Studio M2 Ultra (Voice)
└── Additional M3 Max Nodes
```

## Performance Considerations

### Optimization Strategies

1. **Model Quantization**: 4-bit/8-bit for memory efficiency
2. **KV Cache**: Reuse across requests
3. **Batch Processing**: Group similar requests
4. **Connection Pooling**: Redis connections

### Benchmarks

- **Nemotron 253B**: ~50 tokens/s
- **Command-A 90B**: ~120 tokens/s
- **Qwen3 14B**: ~250 tokens/s

## Error Handling

### Error Categories

1. **Client Errors** (4xx)
   - Invalid model ID
   - Malformed requests
   - Authentication failures

2. **Server Errors** (5xx)
   - Model loading failures
   - Out of memory
   - Generation errors

### Recovery Strategies

- Automatic model unloading on OOM
- Request retry with backoff
- Graceful degradation
- Circuit breaker pattern

## Monitoring & Observability

### Metrics Collection

- **Prometheus**: System and application metrics
- **Custom Metrics**: Token usage, latency, errors
- **Health Endpoints**: Liveness and readiness

### Logging

- **Structured Logging**: JSON format
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Correlation IDs**: Request tracking

## Development Workflow

### Local Development

```bash
# Setup
uv sync
cp .env.example .env

# Run
./start_server.sh dev

# Test
./test_server.py
```

### Testing Strategy

- **Unit Tests**: Component isolation
- **Integration Tests**: API endpoints
- **Load Tests**: Performance validation
- **Model Tests**: Output quality

## Future Considerations

### Scalability

- Horizontal scaling with model sharding
- Distributed session storage
- Queue-based request handling

### Extensibility

- Plugin architecture for models
- Custom middleware support
- Webhook integrations

### Maintainability

- Automated dependency updates
- Performance regression testing
- API versioning strategy