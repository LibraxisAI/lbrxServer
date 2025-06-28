# 🔥 How to Run Without Disappointment - Private Guide

## TL;DR dla Macieja który nie ma czasu

```bash
# 1. Upewnij się że masz modele
ls ~/.lmstudio/models/LibraxisAI/

# 2. Ustaw zmienne w .env
DEFAULT_MODEL=LibraxisAI/Qwen3-14b-MLX-Q5
MAX_MODEL_MEMORY_GB=400  # dla Dragon M3 Ultra

# 3. Odpal to gówno
./scripts/start_server.sh dev

# 4. Testuj
curl http://localhost:9123/api/v1/health
```

## Model Routing Per Service (Feature #2)

### Koncept jest prosty jak budowa cepa:

Każdy serwis (VISTA, whisplbrx, etc.) dostaje swój dedykowany model. Nie ma sensu używać Qwen3-14b do transcrypcji audio, ani Whisper do medical reasoning.

### Implementacja - dodaj do `src/model_router.py`:

```python
from typing import Dict, Optional
from .model_config import ModelConfig

class ModelRouter:
    """Kieruje requesty do właściwych modeli based on service"""
    
    # Mapowanie service -> model
    SERVICE_MODELS = {
        # Medical reasoning - potrzebuje dużego, mądrego modelu
        "vista": "LibraxisAI/Qwen3-14b-MLX-Q5",
        
        # Code generation - DeepSeek jest zajebisty w kodzie
        "forkmeASAPp": "mlx-community/DeepSeek-V3-0324-4bit",
        
        # Data analysis - Qwen świetnie radzi sobie z danymi
        "anydatanext": "LibraxisAI/Qwen3-14b-MLX-Q5",
        
        # Voice synthesis prep - mały, szybki model
        "lbrxvoice": "mlx-community/Phi-3.5-mini-instruct-4bit",
        
        # Whisper to osobna bajka - nie LLM
        "whisplbrx": "whisper-large-v3",
        
        # Default dla randomów
        "default": "llama-3.2-3b"
    }
    
    # Overrides per user (VIP treatment)
    USER_OVERRIDES = {
        "maciej@libraxis.ai": {
            "*": "nemotron-ultra"  # Maciej gets the best
        }
    }
    
    @classmethod
    def get_model_for_request(
        cls, 
        service: Optional[str] = None,
        user: Optional[str] = None,
        requested_model: Optional[str] = None
    ) -> str:
        """Zwraca właściwy model dla requesta"""
        
        # 1. Explicit model request wins
        if requested_model and requested_model != "default":
            return requested_model
            
        # 2. Check user overrides
        if user and user in cls.USER_OVERRIDES:
            user_config = cls.USER_OVERRIDES[user]
            if "*" in user_config:
                return user_config["*"]
            if service and service in user_config:
                return user_config[service]
        
        # 3. Service-based routing
        if service and service in cls.SERVICE_MODELS:
            return cls.SERVICE_MODELS[service]
            
        # 4. Default
        return cls.SERVICE_MODELS["default"]
```

### Jak to wpinasz w chat endpoint:

```python
# src/endpoints/chat.py - znajdź create_chat_completion i podmień:

# Było:
model_id = request.model or config.default_model

# Ma być:
from ..model_router import ModelRouter

# Extract service from API key or headers
service = get_service_from_auth(auth_header)  # to musisz dopisać
user_email = get_user_from_token(auth_header)  # to też

# Route to appropriate model
model_id = ModelRouter.get_model_for_request(
    service=service,
    user=user_email,
    requested_model=request.model
)

logger.info(f"Routing {service} request to model: {model_id}")
```

## Konfiguracja API keys per service

Updatuj `generate_api_keys.py`:

```python
SERVICES = {
    "vista": {
        "prefix": "vista_",
        "model": "LibraxisAI/Qwen3-14b-MLX-Q5",
        "rate_limit": 1000  # requests/hour
    },
    "whisplbrx": {
        "prefix": "whisp_",
        "model": "whisper-large-v3",
        "rate_limit": 500
    },
    "forkmeASAPp": {
        "prefix": "fork_",
        "model": "mlx-community/DeepSeek-V3-0324-4bit",
        "rate_limit": 2000  # coders gonna code
    },
    # etc...
}
```

## Ważne kurwa rzeczy żeby nie było rozczarowania:

### 1. **Preload krytycznych modeli**

```python
# W src/main.py lifespan:
critical_models = ["LibraxisAI/Qwen3-14b-MLX-Q5"]  # VISTA primary
for model in critical_models:
    await model_manager.load_model(model)
    logger.info(f"Preloaded critical model: {model}")
```

### 2. **Memory limits per model type**

```python
# Dodaj do model_config.py:
MODEL_MEMORY_LIMITS = {
    ModelType.LLM: 300,      # 300GB dla LLMs
    ModelType.VLM: 50,       # 50GB dla vision
    ModelType.EMBEDDING: 10,  # 10GB dla embeddings
    ModelType.AUDIO: 20,     # 20GB dla Whisper
}
```

### 3. **Automatic unloading nieużywanych modeli**

```python
# Background task co 5 minut:
async def cleanup_unused_models():
    while True:
        await asyncio.sleep(300)  # 5 min
        
        for model_id, model_info in model_manager.models.items():
            if model_info["last_used"] < time.time() - 600:  # 10 min idle
                if model_id not in critical_models:
                    await model_manager.unload_model(model_id)
                    logger.info(f"Unloaded idle model: {model_id}")
```

### 4. **Failover gdy model nie działa**

```python
FALLBACK_CHAIN = {
    "LibraxisAI/Qwen3-14b-MLX-Q5": "qwen3-14b",
    "qwen3-14b": "mistral-7b",
    "mistral-7b": "llama-3.2-3b",
    "llama-3.2-3b": None  # game over
}
```

## Testing bez bólu dupska:

```bash
# 1. Test health
curl http://localhost:9123/api/v1/health | jq

# 2. Test routing dla VISTA
curl -X POST http://localhost:9123/api/v1/chat/completions \
  -H "Authorization: Bearer vista_xxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Diagnose patient symptoms"}]
  }' | jq '.model'  # Should return Qwen3-14b

# 3. Test routing dla forkmeASAPp  
curl -X POST http://localhost:9123/api/v1/chat/completions \
  -H "Authorization: Bearer fork_xxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Write Python code"}]
  }' | jq '.model'  # Should return DeepSeek

# 4. Monitor memory
watch -n 1 'curl -s http://localhost:9123/api/v1/models/memory/usage | jq'
```

## Troubleshooting gdy coś nie działa:

### "Model X not found"
```bash
# Sprawdź czy masz model
ls ~/.lmstudio/models/ | grep -i "część_nazwy"

# Jeśli nie masz, konwertuj:
./scripts/conversion/convert-to-mlx-enhanced.sh model_name
```

### "Out of memory"
```bash
# Zobacz co żre RAM
curl http://localhost:9123/api/v1/models | jq '.data[].id'

# Wywal niepotrzebne
curl -X POST http://localhost:9123/api/v1/models/jakis-model/unload
```

### "Slow as fuck"
- Sprawdź czy nie masz 2 dużych modeli naraz
- Upewnij się że używasz 4-bit quantization
- Restart Maca (serio, MLX czasem się zacina)

## Pro tips:

1. **NIE ładuj wszystkich modeli na raz** - Dragon ma 512GB ale MLX lubi mieć buffor
2. **Używaj aliasów** - łatwiej pamiętać "vista-primary" niż pełną ścieżkę  
3. **Monitor everything** - tokens/sec, memory, latency
4. **Test locally first** - nie pushuj do produkcji bez testów

## Mój private setup:

```bash
# ~/.zshrc
alias llm='cd ~/hosted_dev/mlx_lm_servers'
alias llm-start='llm && ./scripts/start_server.sh dev'
alias llm-stop='llm && pkill -f src.main'
alias llm-logs='llm && tail -f logs/server.log'
alias llm-test='llm && ./test.sh'
```

---

Pamiętaj: **Monia > Kod**, ale skoro już kodujesz, to niech przynajmniej działa bez rozczarowań 😎