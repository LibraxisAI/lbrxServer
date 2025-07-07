#!/usr/bin/env python3
"""
Autonomous Stress Testing Pipeline for LibraxisAI Services
Runs continuous tests with delays, monitoring, and reporting
"""

import asyncio
import aiohttp
import json
import time
import random
from datetime import datetime
from pathlib import Path
import os

# Test configuration
ENDPOINTS = {
    "llm": {
        "url": "https://localhost:8555/api/v1/chat/completions",
        "verify_ssl": False,
        "headers": {"Authorization": "Bearer vista_medical"},
        "models": ["qwen3-14b", "nemotron-49b", "qwq-32b", "c4ai-03-2025"]
    },
    "whisperx": {
        "url": "http://localhost:8443/transcribe",
        "verify_ssl": True,
        "test_files": ["/tmp/test_audio_{i}.wav"],
        "headers": {"Authorization": "Bearer whisp_transcribe"}
    },
    "stt_mlx": {
        "url": "http://localhost:8444/transcribe",
        "verify_ssl": True,
        "test_files": ["/tmp/test_audio_{i}.wav"]
    },
    "tts": {
        "url": "http://localhost:8666/synthesize",
        "verify_ssl": True,
        "voices": ["pl-PL-MarekNeural", "pl-PL-ZofiaNeural", "en-US-AriaNeural"]
    }
}

# Test scenarios
TEST_SCENARIOS = {
    "llm_light": {
        "concurrent": 2,
        "delay_between": 5,
        "prompts": [
            "Explain quantum computing in 100 words",
            "Write a haiku about AI",
            "List 5 benefits of meditation"
        ]
    },
    "llm_medium": {
        "concurrent": 4,
        "delay_between": 10,
        "prompts": [
            "Explain the transformer architecture in detail",
            "Write a 500 word essay on climate change",
            "Describe the process of photosynthesis step by step"
        ]
    },
    "llm_heavy": {
        "concurrent": 6,
        "delay_between": 30,
        "prompts": [
            "Write a comprehensive analysis of quantum field theory",
            "Create a detailed business plan for an AI startup",
            "Explain the complete history of computing from abacus to quantum computers"
        ]
    },
    "audio_stress": {
        "concurrent": 3,
        "delay_between": 15,
        "file_sizes": ["small", "medium", "large"]
    }
}

class AutonomousStressTester:
    def __init__(self):
        self.results = []
        self.running = True
        self.report_dir = Path("/tmp/stress_test_reports")
        self.report_dir.mkdir(exist_ok=True)
        
    async def create_test_audio_files(self):
        """Create dummy audio files for testing"""
        sizes = {
            "small": 1024 * 1024,      # 1MB
            "medium": 50 * 1024 * 1024, # 50MB
            "large": 200 * 1024 * 1024  # 200MB
        }
        
        for i, (size_name, size_bytes) in enumerate(sizes.items()):
            filepath = f"/tmp/test_audio_{i}.wav"
            if not os.path.exists(filepath):
                # Create WAV header + dummy data
                with open(filepath, 'wb') as f:
                    # Simplified WAV header
                    f.write(b'RIFF')
                    f.write((size_bytes + 36).to_bytes(4, 'little'))
                    f.write(b'WAVEfmt ')
                    f.write((16).to_bytes(4, 'little'))
                    f.write((1).to_bytes(2, 'little'))  # PCM
                    f.write((1).to_bytes(2, 'little'))  # Mono
                    f.write((16000).to_bytes(4, 'little'))  # Sample rate
                    f.write((32000).to_bytes(4, 'little'))  # Byte rate
                    f.write((2).to_bytes(2, 'little'))  # Block align
                    f.write((16).to_bytes(2, 'little'))  # Bits per sample
                    f.write(b'data')
                    f.write(size_bytes.to_bytes(4, 'little'))
                    # Fill with zeros
                    f.write(b'\x00' * (size_bytes - 44))
                    
    async def test_llm_endpoint(self, session, scenario_name):
        """Test LLM endpoint with various loads"""
        scenario = TEST_SCENARIOS[scenario_name]
        endpoint = ENDPOINTS["llm"]
        
        print(f"\n🔥 Starting LLM test: {scenario_name}")
        
        async def make_request(model, prompt):
            start_time = time.time()
            try:
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2048,
                    "temperature": 0.7
                }
                
                async with session.post(
                    endpoint["url"],
                    json=data,
                    headers=endpoint["headers"],
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    duration = time.time() - start_time
                    result = {
                        "timestamp": datetime.now().isoformat(),
                        "endpoint": "llm",
                        "model": model,
                        "scenario": scenario_name,
                        "status": response.status,
                        "duration": duration,
                        "success": response.status == 200
                    }
                    
                    if response.status == 200:
                        data = await response.json()
                        result["tokens"] = len(data.get("choices", [{}])[0].get("message", {}).get("content", "").split())
                    
                    return result
                    
            except asyncio.TimeoutError:
                return {
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": "llm",
                    "model": model,
                    "scenario": scenario_name,
                    "status": "timeout",
                    "duration": time.time() - start_time,
                    "success": False
                }
            except Exception as e:
                return {
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": "llm",
                    "model": model,
                    "scenario": scenario_name,
                    "status": "error",
                    "error": str(e),
                    "duration": time.time() - start_time,
                    "success": False
                }
        
        # Run concurrent requests
        tasks = []
        for i in range(scenario["concurrent"]):
            model = random.choice(endpoint["models"])
            prompt = random.choice(scenario["prompts"])
            tasks.append(make_request(model, prompt))
            
        results = await asyncio.gather(*tasks)
        self.results.extend(results)
        
        # Report results
        successful = sum(1 for r in results if r["success"])
        print(f"✅ LLM {scenario_name}: {successful}/{len(results)} successful")
        
        return results
        
    async def test_audio_endpoints(self, session):
        """Test audio endpoints"""
        print(f"\n🎵 Starting audio endpoint tests")
        
        # Test WhisperX
        async def test_whisperx():
            try:
                files = {
                    'audio': open('/tmp/test_audio_0.wav', 'rb')
                }
                async with session.post(
                    ENDPOINTS["whisperx"]["url"],
                    data=files,
                    headers=ENDPOINTS["whisperx"]["headers"],
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    return {
                        "endpoint": "whisperx",
                        "status": response.status,
                        "success": response.status == 200
                    }
            except Exception as e:
                return {
                    "endpoint": "whisperx",
                    "status": "error",
                    "error": str(e),
                    "success": False
                }
                
        # Test TTS
        async def test_tts():
            try:
                data = {
                    "text": "Testing LibraxisAI TTS service with Polish voice",
                    "voice": "pl-PL-MarekNeural",
                    "speed": 1.0
                }
                async with session.post(
                    ENDPOINTS["tts"]["url"],
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    return {
                        "endpoint": "tts",
                        "status": response.status,
                        "success": response.status == 200
                    }
            except Exception as e:
                return {
                    "endpoint": "tts", 
                    "status": "error",
                    "error": str(e),
                    "success": False
                }
        
        results = await asyncio.gather(
            test_whisperx(),
            test_tts(),
            return_exceptions=True
        )
        
        self.results.extend([r for r in results if isinstance(r, dict)])
        
    async def run_test_cycle(self):
        """Run one complete test cycle"""
        print(f"\n{'='*60}")
        print(f"🚀 Starting test cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        async with aiohttp.ClientSession() as session:
            # Phase 1: Light load
            await self.test_llm_endpoint(session, "llm_light")
            await asyncio.sleep(10)
            
            # Phase 2: Audio tests
            await self.test_audio_endpoints(session)
            await asyncio.sleep(15)
            
            # Phase 3: Medium load
            await self.test_llm_endpoint(session, "llm_medium")
            await asyncio.sleep(20)
            
            # Phase 4: Heavy load (danger zone!)
            await self.test_llm_endpoint(session, "llm_heavy")
            await asyncio.sleep(30)
            
        # Generate report
        self.generate_report()
        
    def generate_report(self):
        """Generate test report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.report_dir / f"stress_test_{timestamp}.json"
        
        # Calculate statistics
        stats = {
            "total_requests": len(self.results),
            "successful": sum(1 for r in self.results if r.get("success", False)),
            "failed": sum(1 for r in self.results if not r.get("success", False)),
            "by_endpoint": {},
            "by_scenario": {}
        }
        
        for result in self.results:
            endpoint = result.get("endpoint", "unknown")
            scenario = result.get("scenario", "unknown")
            
            if endpoint not in stats["by_endpoint"]:
                stats["by_endpoint"][endpoint] = {"success": 0, "fail": 0}
            if scenario not in stats["by_scenario"]:
                stats["by_scenario"][scenario] = {"success": 0, "fail": 0}
                
            if result.get("success"):
                stats["by_endpoint"][endpoint]["success"] += 1
                stats["by_scenario"][scenario]["success"] += 1
            else:
                stats["by_endpoint"][endpoint]["fail"] += 1
                stats["by_scenario"][scenario]["fail"] += 1
        
        report = {
            "timestamp": timestamp,
            "statistics": stats,
            "recent_results": self.results[-50:]  # Last 50 results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📊 Report saved to: {report_file}")
        print(f"   Total: {stats['total_requests']} | Success: {stats['successful']} | Failed: {stats['failed']}")
        
    async def monitor_health(self):
        """Monitor service health in background"""
        while self.running:
            try:
                async with aiohttp.ClientSession() as session:
                    # Check LLM health
                    async with session.get(
                        "https://localhost:8555/api/v1/health",
                        ssl=False,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status != 200:
                            print(f"⚠️  LLM health check failed: {response.status}")
                            
            except Exception as e:
                print(f"⚠️  Health check error: {e}")
                
            await asyncio.sleep(60)  # Check every minute
            
    async def run(self):
        """Main autonomous testing loop"""
        print("🤖 Autonomous Stress Testing Pipeline Started!")
        print("   Press Ctrl+C to stop gracefully")
        
        # Create test files
        await self.create_test_audio_files()
        
        # Start health monitoring
        health_task = asyncio.create_task(self.monitor_health())
        
        try:
            while self.running:
                await self.run_test_cycle()
                
                # Wait between cycles
                wait_time = random.randint(300, 600)  # 5-10 minutes
                print(f"\n💤 Sleeping for {wait_time}s before next cycle...")
                await asyncio.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\n🛑 Gracefully shutting down...")
            self.running = False
            health_task.cancel()
            
        # Final report
        self.generate_report()
        print("\n✅ Testing pipeline completed!")

if __name__ == "__main__":
    tester = AutonomousStressTester()
    asyncio.run(tester.run())