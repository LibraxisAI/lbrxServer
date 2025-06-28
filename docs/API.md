# MLX LLM Server - API Documentation

## Base URL

Production: `https://libraxis.cloud/api/v1`  
Tailscale: `https://dragon.fold-antares.ts.net/api/v1`

## Authentication

All endpoints require authentication via Bearer token in the Authorization header:

```http
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Chat Completions

Create a chat completion with optional session management.

**Endpoint:** `POST /chat/completions`

**Request Body:**

```json
{
  "model": "nemotron-ultra",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ],
  "temperature": 0.7,
  "top_p": 1.0,
  "max_tokens": 2048,
  "stream": false,
  "session_id": "optional-session-identifier",
  "stop": ["END", "STOP"],
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "seed": 42,
  "user": "user-identifier"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| model | string | Yes | - | Model ID or alias |
| messages | array | Yes | - | Array of message objects |
| temperature | float | No | 0.7 | Sampling temperature (0.0-2.0) |
| top_p | float | No | 1.0 | Nucleus sampling parameter |
| max_tokens | integer | No | 2048 | Maximum tokens to generate |
| stream | boolean | No | false | Enable streaming response |
| session_id | string | No | null | Session identifier for context |
| stop | string/array | No | null | Stop sequences |
| presence_penalty | float | No | 0.0 | Penalize new tokens (-2.0-2.0) |
| frequency_penalty | float | No | 0.0 | Penalize frequent tokens (-2.0-2.0) |
| seed | integer | No | null | Random seed for reproducibility |
| user | string | No | null | End-user identifier |

**Response (Non-streaming):**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1719565427,
  "model": "nemotron-ultra",
  "system_fingerprint": "mlx-libraxis.cloud",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 8,
    "total_tokens": 33
  }
}
```

**Response (Streaming):**

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1719565427,"model":"nemotron-ultra","system_fingerprint":"mlx-libraxis.cloud","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1719565427,"model":"nemotron-ultra","system_fingerprint":"mlx-libraxis.cloud","choices":[{"index":0,"delta":{"content":"The"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1719565427,"model":"nemotron-ultra","system_fingerprint":"mlx-libraxis.cloud","choices":[{"index":0,"delta":{"content":" capital"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1719565427,"model":"nemotron-ultra","system_fingerprint":"mlx-libraxis.cloud","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

### Model Routing

The server automatically routes requests to appropriate models based on the service identified by your API key:

**Service-specific routing:**
- `vista_*` API keys → `qwen3-14b` (medical reasoning)
- `fork_*` API keys → `deepseek-coder` (code generation)
- `data_*` API keys → `qwen3-14b` (data analysis)
- `voice_*` API keys → `phi-3` (fast responses for voice)
- `whisp_*` API keys → `whisper-large-v3` (transcription)

**Example with VISTA API key:**
```bash
curl -X POST http://localhost:9123/api/v1/chat/completions \
  -H "Authorization: Bearer vista_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Diagnose symptoms: fever, cough, fatigue"}]
  }'
# Automatically uses qwen3-14b model
```

**Override with explicit model:**
```bash
curl -X POST http://localhost:9123/api/v1/chat/completions \
  -H "Authorization: Bearer vista_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b",  # Overrides default routing
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Completions

Create a text completion (legacy format).

**Endpoint:** `POST /completions`

**Request Body:**

```json
{
  "model": "nemotron-ultra",
  "prompt": "The meaning of life is",
  "max_tokens": 100,
  "temperature": 0.8,
  "top_p": 0.95,
  "stream": false,
  "stop": ["\n", "END"]
}
```

**Response:**

```json
{
  "id": "cmpl-abc123",
  "object": "text_completion",
  "created": 1719565427,
  "model": "nemotron-ultra",
  "system_fingerprint": "mlx-libraxis.cloud",
  "choices": [
    {
      "text": " a profound philosophical question that has been contemplated throughout human history...",
      "index": 0,
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 6,
    "completion_tokens": 94,
    "total_tokens": 100
  }
}
```

### List Models

Get a list of available models.

**Endpoint:** `GET /models`

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "nemotron-ultra",
      "object": "model",
      "created": 1719565427,
      "owned_by": "libraxis",
      "permission": [],
      "root": "nemotron-ultra",
      "parent": null
    },
    {
      "id": "command-a",
      "object": "model",
      "created": 1719565427,
      "owned_by": "libraxis",
      "permission": [],
      "root": "command-a",
      "parent": null
    }
  ]
}
```

### Load Model

Load a specific model into memory.

**Endpoint:** `POST /models/{model_id}/load`

**Response:**

```json
{
  "status": "success",
  "model_id": "nemotron-ultra",
  "memory_used_gb": 160,
  "load_time_seconds": 28.5
}
```

### Unload Model

Unload a model from memory.

**Endpoint:** `POST /models/{model_id}/unload`

**Response:**

```json
{
  "status": "success",
  "model_id": "nemotron-ultra",
  "memory_freed_gb": 160
}
```

### Memory Usage

Get current memory usage statistics.

**Endpoint:** `GET /models/memory/usage`

**Response:**

```json
{
  "total_gb": 512,
  "available_gb": 312,
  "used_gb": 200,
  "models_loaded": {
    "nemotron-ultra": {
      "memory_gb": 160,
      "loaded_at": "2024-06-28T10:30:00Z"
    },
    "command-a": {
      "memory_gb": 40,
      "loaded_at": "2024-06-28T10:35:00Z"
    }
  },
  "system_reserved_gb": 112
}
```

## Session Management

### Create Session

Create a new conversation session.

**Endpoint:** `POST /sessions`

**Request Body:**

```json
{
  "session_id": "custom-session-id",
  "data": {
    "user": "user-123",
    "context": "medical consultation"
  },
  "ttl": 3600
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| session_id | string | No | auto-generated | Custom session identifier |
| data | object | No | {} | Session metadata |
| ttl | integer | No | 86400 | Time-to-live in seconds |

**Response:**

```json
{
  "session_id": "custom-session-id",
  "created_at": "2024-06-28T10:30:00Z",
  "updated_at": "2024-06-28T10:30:00Z",
  "expires_at": "2024-06-28T11:30:00Z",
  "data": {
    "user": "user-123",
    "context": "medical consultation"
  },
  "message_count": 0
}
```

### Get Session

Retrieve session information.

**Endpoint:** `GET /sessions/{session_id}`

**Response:**

```json
{
  "session_id": "custom-session-id",
  "created_at": "2024-06-28T10:30:00Z",
  "updated_at": "2024-06-28T10:45:00Z",
  "expires_at": "2024-06-29T10:30:00Z",
  "data": {
    "user": "user-123",
    "context": "medical consultation"
  },
  "message_count": 5
}
```

### Get Session Messages

Retrieve conversation history from a session.

**Endpoint:** `GET /sessions/{session_id}/messages`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 100 | Maximum messages to return |

**Response:**

```json
{
  "session_id": "custom-session-id",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful medical assistant."
    },
    {
      "role": "user",
      "content": "What are the symptoms of dehydration?"
    },
    {
      "role": "assistant",
      "content": "Common symptoms of dehydration include..."
    }
  ],
  "count": 3
}
```

### Delete Session

Delete a session and its history.

**Endpoint:** `DELETE /sessions/{session_id}`

**Response:**

```json
{
  "message": "Session deleted successfully"
}
```

### List Sessions

List all active sessions (admin only).

**Endpoint:** `GET /sessions`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 50 | Maximum sessions to return |
| offset | integer | 0 | Pagination offset |

**Response:**

```json
{
  "sessions": [],
  "total": 0
}
```

## System Endpoints

### Health Check

Check server health status.

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-06-28T10:30:00Z",
  "uptime_seconds": 3600,
  "models_loaded": 2,
  "active_requests": 5
}
```

### Metrics

Prometheus metrics endpoint.

**Endpoint:** `GET /metrics` (Port 9090)

**Response:** Prometheus text format

```
# HELP mlx_llm_requests_total Total number of requests
# TYPE mlx_llm_requests_total counter
mlx_llm_requests_total{method="POST",endpoint="/chat/completions"} 1234

# HELP mlx_llm_tokens_generated_total Total tokens generated
# TYPE mlx_llm_tokens_generated_total counter
mlx_llm_tokens_generated_total{model="nemotron-ultra"} 567890
```

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "message": "Model not found: gpt-4",
    "type": "model_not_found",
    "code": "MODEL_NOT_FOUND"
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | INVALID_REQUEST | Malformed request body |
| 401 | UNAUTHORIZED | Missing or invalid API key |
| 403 | FORBIDDEN | Access denied for resource |
| 404 | NOT_FOUND | Resource not found |
| 422 | VALIDATION_ERROR | Request validation failed |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |
| 503 | SERVICE_UNAVAILABLE | Model loading or system overload |

## Rate Limits

Default rate limits per API key:

- **Per Minute**: 60 requests
- **Per Hour**: 1000 requests

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1719565500
```

## Model Aliases

The following model aliases are available:

| Alias | Full Model Path |
|-------|-----------------|
| nemotron-ultra | LibraxisAI/Llama-3_1-Nemotron-Ultra-253B-v1-mlx-q5 |
| command-a | mlx-community/command-a-03-2025-q8 |
| qwen3-14b | mlx-community/qwen-3-14b-lbrx-2.0-q8 |
| llama-scout | mlx-community/llama-3.3-scout-8b |
| maverick | LibraxisAI/maverick-13b-mlx-8bit |

## WebSocket Support (Coming Soon)

Future support for WebSocket connections:

```javascript
const ws = new WebSocket('wss://libraxis.cloud/api/v1/ws');

ws.send(JSON.stringify({
  type: 'chat',
  model: 'nemotron-ultra',
  messages: [...],
  session_id: 'abc123'
}));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content);
};
```

## SDK Examples

### Python

```python
import httpx

async def chat_completion(messages, session_id=None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://libraxis.cloud/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "nemotron-ultra",
                "messages": messages,
                "session_id": session_id
            }
        )
        return response.json()
```

### JavaScript/TypeScript

```typescript
async function chatCompletion(
  messages: Message[],
  sessionId?: string
): Promise<ChatCompletionResponse> {
  const response = await fetch('https://libraxis.cloud/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'nemotron-ultra',
      messages,
      session_id: sessionId
    })
  });
  
  return response.json();
}
```

### cURL

```bash
curl -X POST https://libraxis.cloud/api/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nemotron-ultra",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'
```

## Best Practices

1. **Session Management**: Use sessions for conversations to maintain context
2. **Error Handling**: Implement exponential backoff for rate limits
3. **Streaming**: Use streaming for long responses to improve UX
4. **Model Selection**: Choose appropriate models based on task complexity
5. **Security**: Never expose API keys in client-side code