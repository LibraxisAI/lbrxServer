#!/usr/bin/env python
"""
Test script for MLX LLM Server
"""
import asyncio
import httpx
import json


API_BASE = "https://dragon.fold-antares.ts.net/api/v1"
# API_BASE = "https://libraxis.cloud/api/v1"  # Alternative

# Test with your actual API key
API_KEY = "lbrx_test_key_here"


async def test_models(client: httpx.AsyncClient):
    """Test models endpoint"""
    print("\n=== Testing Models Endpoint ===")
    response = await client.get(f"{API_BASE}/models")
    print(f"Status: {response.status_code}")
    print(f"Models: {json.dumps(response.json(), indent=2)}")
    return response.json()


async def test_chat_completion(client: httpx.AsyncClient, model: str):
    """Test chat completion"""
    print(f"\n=== Testing Chat Completion with {model} ===")
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France? Answer in one word."}
        ],
        "temperature": 0.7,
        "max_tokens": 50
    }
    
    response = await client.post(
        f"{API_BASE}/chat/completions",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200:
        print(f"Response: {result['choices'][0]['message']['content']}")
        print(f"Usage: {result['usage']}")
    else:
        print(f"Error: {result}")
    
    return result


async def test_streaming(client: httpx.AsyncClient, model: str):
    """Test streaming chat completion"""
    print(f"\n=== Testing Streaming with {model} ===")
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Count from 1 to 5."}
        ],
        "stream": True,
        "max_tokens": 100
    }
    
    async with client.stream(
        "POST",
        f"{API_BASE}/chat/completions",
        json=payload
    ) as response:
        print(f"Status: {response.status_code}")
        
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    print("\nStream completed")
                    break
                
                try:
                    chunk = json.loads(data)
                    if "choices" in chunk and chunk["choices"]:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            print(delta["content"], end="", flush=True)
                except json.JSONDecodeError:
                    pass


async def test_health(client: httpx.AsyncClient):
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = await client.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Health: {json.dumps(response.json(), indent=2)}")


async def main():
    """Run all tests"""
    # Configure client with SSL verification disabled for Tailscale cert
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(
        headers=headers,
        verify=False,  # For self-signed Tailscale certs
        timeout=30.0
    ) as client:
        
        # Test health
        await test_health(client)
        
        # Test models
        models_response = await test_models(client)
        
        # Get first available model
        if models_response.get("data"):
            model_id = models_response["data"][0]["id"]
            
            # Test chat completion
            await test_chat_completion(client, model_id)
            
            # Test streaming
            await test_streaming(client, model_id)
        else:
            print("No models available!")


if __name__ == "__main__":
    print("MLX LLM Server Test Suite")
    print("=" * 50)
    asyncio.run(main())