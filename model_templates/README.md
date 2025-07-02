# Model Chat Templates

This directory contains custom chat templates for models that require special formatting.

## Structure

Each model has its own directory containing:
- `chat_template.jinja` - The Jinja2 template file
- `tokenizer_config_patch.json` - JSON patch for tokenizer_config.json with escaped template

## Usage

### For Hugging Face Model Cards

1. Copy the `tokenizer_config_patch.json` content
2. In your model's `tokenizer_config.json`, add or update the `chat_template` field
3. Commit and push to Hugging Face

### For Local Testing

```python
from transformers import AutoTokenizer

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("model-id")

# Read and apply custom template
with open("model_templates/model-name/chat_template.jinja", "r") as f:
    tokenizer.chat_template = f.read()

# Use the tokenizer with custom template
messages = [{"role": "user", "content": "Hello!"}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False)
```

## Models

### qwen3-235-a22
- Supports tool calling with `<tool_call>` tags
- Reasoning with `<think>` tags
- Uses `<|im_start|>` and `<|im_end|>` tokens

### nemotron
- Uses `<|start_header_id|>` and `<|end_header_id|>` tokens
- Supports `<think>` tag extraction
- Default system message: "detailed thinking on"