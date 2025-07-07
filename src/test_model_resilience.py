#!/usr/bin/env python3
"""
Test resilience of all models on https://llm.libraxis.cloud
Goal: Verify if models achieve 100% response rate (even partial responses)
"""

import requests
import json
import time
from datetime import datetime

# API configuration
API_URL = "https://llm.libraxis.cloud/api/v1/chat/completions"
API_KEY = ""  # No API key needed for public endpoint

# Models to test
MODELS = [
    "LibraxisAI/Llama-3_3-Nemotron-Super-49B-v1-MLX-Q5",
    "LibraxisAI/Qwen3-14b-MLX-Q5",
    "LibraxisAI/c4ai-command-a-03-2025-q5-mlx",
    "LibraxisAI/QwQ-32B-MLX-Q5",
    "qwen/Qwen3-8B-MLX-8bit"
]

# Test question
QUESTION = "Czy AI odbierze lekarzom weterynarii stetoskopy?"

def test_model(model_name):
    """Test a single model for resilience"""
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Try without authorization first
    headers = {
        "Content-Type": "application/json"
    }
    
    # If API_KEY is set, add authorization
    if API_KEY and API_KEY != "":
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": QUESTION
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500,
        "stream": False
    }
    
    start_time = time.time()
    
    try:
        # Send request with 60 second timeout
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response_time = time.time() - start_time
        
        # Check HTTP status
        print(f"HTTP Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.2f} seconds")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    print(f"Response received: YES ✓")
                    print(f"Response length: {len(content)} characters")
                    print(f"First 200 chars: {content[:200]}...")
                else:
                    print(f"Response received: YES (but empty choices)")
                    print(f"Raw response: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                print(f"Response received: YES (but invalid JSON)")
                print(f"Raw text: {response.text[:500]}...")
        else:
            print(f"Response received: YES (with error)")
            print(f"Error response: {response.text[:500]}...")
            
        return {
            "model": model_name,
            "responded": True,
            "status_code": response.status_code,
            "response_time": response_time,
            "success": response.status_code == 200
        }
        
    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        print(f"Response: TIMEOUT after {response_time:.2f} seconds")
        return {
            "model": model_name,
            "responded": False,
            "status_code": None,
            "response_time": response_time,
            "success": False,
            "error": "Timeout"
        }
        
    except requests.exceptions.ConnectionError as e:
        response_time = time.time() - start_time
        print(f"Response: CONNECTION ERROR after {response_time:.2f} seconds")
        print(f"Error: {str(e)}")
        return {
            "model": model_name,
            "responded": False,
            "status_code": None,
            "response_time": response_time,
            "success": False,
            "error": f"Connection Error: {str(e)}"
        }
        
    except Exception as e:
        response_time = time.time() - start_time
        print(f"Response: EXCEPTION after {response_time:.2f} seconds")
        print(f"Error: {type(e).__name__}: {str(e)}")
        return {
            "model": model_name,
            "responded": False,
            "status_code": None,
            "response_time": response_time,
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }

def main():
    """Run resilience tests on all models"""
    print("LLM API Resilience Test")
    print(f"API URL: {API_URL}")
    print(f"Question: {QUESTION}")
    print(f"Testing {len(MODELS)} models")
    
    results = []
    
    for model in MODELS:
        result = test_model(model)
        results.append(result)
        # Small delay between tests to avoid overwhelming the server
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY REPORT")
    print(f"{'='*60}")
    
    total_models = len(results)
    responded_count = sum(1 for r in results if r["responded"])
    success_count = sum(1 for r in results if r["success"])
    
    print(f"\nTotal models tested: {total_models}")
    print(f"Models that responded (any response): {responded_count}/{total_models} ({responded_count/total_models*100:.1f}%)")
    print(f"Models with successful responses: {success_count}/{total_models} ({success_count/total_models*100:.1f}%)")
    
    print("\nDetailed Results:")
    print(f"{'Model':<50} {'Responded':<10} {'Status':<8} {'Time (s)':<10}")
    print("-" * 80)
    
    for result in results:
        model_short = result["model"].split("/")[-1][:45]
        responded = "YES" if result["responded"] else "NO"
        status = str(result["status_code"]) if result["status_code"] else "N/A"
        time_str = f"{result['response_time']:.2f}"
        
        print(f"{model_short:<50} {responded:<10} {status:<8} {time_str:<10}")
    
    # Check if we achieved 100% response rate milestone
    print(f"\n{'='*60}")
    if responded_count == total_models:
        print("✓ MILESTONE ACHIEVED: 100% response rate!")
        print("All models returned responses (even if errors)")
    else:
        print(f"✗ Milestone not yet achieved: {responded_count}/{total_models} models responded")
        print("Failed models:")
        for result in results:
            if not result["responded"]:
                print(f"  - {result['model']}: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()