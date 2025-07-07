# LibraxisAI LLM Server Test Report

## Test Date: 2025-07-07

## Objective
Test each available model on the remote LLM server (https://llm.libraxis.cloud) with the philosophical veterinary question: "Czy AI odbierze lekarzom weterynarii stetoskopy?" (Will AI take stethoscopes away from veterinarians?)

## Test Configuration
- Server URL: https://llm.libraxis.cloud
- API Endpoint: /api/v1/chat/completions
- API Key Provided: sk-libraxis-vista-v1
- Models to Test:
  1. LibraxisAI/Llama-3_3-Nemotron-Super-49B-v1-MLX-Q5
  2. LibraxisAI/Qwen3-14b-MLX-Q5
  3. LibraxisAI/c4ai-command-a-03-2025-q5-mlx
  4. qwen/Qwen3-8B-MLX-8bit
  5. LibraxisAI/QwQ-32B-MLX-Q5

## Server Discovery
1. Initial attempts with `/v1/` prefix failed with "Not Found" errors
2. Base URL query revealed correct API structure:
   ```json
   {
     "service": "MLX LLM Server",
     "version": "1.0.0",
     "status": "operational",
     "endpoints": {
       "chat": "/api/v1/chat/completions",
       "completions": "/api/v1/completions",
       "models": "/api/v1/models",
       "sessions": "/api/v1/sessions",
       "docs": "/api/v1/docs"
     }
   }
   ```

## Available Models
Successfully retrieved model list from `/api/v1/models`:
- All requested models are available on the server
- Additional models also present including larger variants

## Test Results

### Authentication Issues
1. **With API Key**: Returns `{"detail":"Could not validate credentials"}`
   - The provided API key appears to be invalid or incorrectly formatted
   
2. **Without API Key**: Returns `{"error":{"message":"Internal server error","type":"server_error","code":"internal_error"}}`
   - Server responds with HTTP 500 Internal Server Error
   - Suggests the server may require authentication but encounters errors when none is provided

### Model Responses
Unfortunately, I was unable to obtain responses from any of the models due to authentication/server issues:

| Model | Status | Error |
|-------|--------|-------|
| LibraxisAI/Llama-3_3-Nemotron-Super-49B-v1-MLX-Q5 | Failed | Authentication/Server Error |
| LibraxisAI/Qwen3-14b-MLX-Q5 | Failed | Authentication/Server Error |
| LibraxisAI/c4ai-command-a-03-2025-q5-mlx | Failed | Authentication/Server Error |
| qwen/Qwen3-8B-MLX-8bit | Failed | Authentication/Server Error |
| LibraxisAI/QwQ-32B-MLX-Q5 | Failed | Authentication/Server Error |

## Technical Details
- Server is hosted on Cloudflare (CF-Ray headers present)
- SSL certificate is valid (issued by Google Trust Services)
- Server supports HTTP/2
- Models are confirmed to exist on the server

## Conclusions
1. The LLM server is operational and the models are available
2. The provided API key "sk-libraxis-vista-v1" appears to be invalid
3. The server requires proper authentication to function
4. Without valid credentials, no model testing could be completed

## Recommendations
1. Verify the correct API key with the LibraxisAI team
2. Check if there's a different authentication method (Bearer token, API key header name, etc.)
3. Consult the API documentation at `/api/v1/docs` for proper authentication format
4. Consider if the API key needs to be passed in a different header or format

## Note on the Philosophical Question
The question "Czy AI odbierze lekarzom weterynarii stetoskopy?" is particularly interesting as it touches on:
- The role of AI in veterinary medicine
- The symbolic importance of the stethoscope as a medical tool
- The balance between AI assistance and human expertise in animal care

Unfortunately, without successful API access, we couldn't gather the models' perspectives on this thought-provoking question.