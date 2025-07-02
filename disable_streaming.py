#!/usr/bin/env python3
"""
Quick script to test non-streaming generation
"""
import asyncio
import httpx
import json

async def test_non_streaming():
    url = "http://localhost:9123/api/v1/chat/completions"
    
    payload = {
        "model": "nemotron",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "stream": False  # Explicitly disable streaming
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Authorization": "Bearer test-key"},
            timeout=30.0
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_non_streaming())