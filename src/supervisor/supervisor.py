"""
Anti-crash supervisor pipeline with auto-recovery for LLM service.
Implements process monitoring, automatic restart, and request recovery.
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import psutil
import aiofiles
from loguru import logger

@dataclass
class ProcessInfo:
    """Information about a supervised process."""
    name: str
    command: List[str]
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    restart_count: int = 0
    last_restart: Optional[datetime] = None
    crashes: List[datetime] = field(default_factory=list)
    
@dataclass
class RequestInfo:
    """Information about an in-flight request."""
    request_id: str
    endpoint: str
    method: str
    headers: Dict[str, str]
    body: Any
    timestamp: datetime
    model: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed
    retry_count: int = 0
    
class RequestQueue:
    """Persistent request queue for crash recovery."""
    
    def __init__(self, queue_dir: Path):
        self.queue_dir = queue_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.active_requests: Dict[str, RequestInfo] = {}
        self.completed_dir = self.queue_dir / "completed"
        self.completed_dir.mkdir(exist_ok=True)
        self.failed_dir = self.queue_dir / "failed"
        self.failed_dir.mkdir(exist_ok=True)
        
    async def add_request(self, request: RequestInfo) -> None:
        """Add a request to the queue and persist it."""
        self.active_requests[request.request_id] = request
        request_file = self.queue_dir / f"{request.request_id}.json"
        
        request_data = {
            "request_id": request.request_id,
            "endpoint": request.endpoint,
            "method": request.method,
            "headers": request.headers,
            "body": request.body,
            "timestamp": request.timestamp.isoformat(),
            "model": request.model,
            "status": request.status,
            "retry_count": request.retry_count
        }
        
        async with aiofiles.open(request_file, 'w') as f:
            await f.write(json.dumps(request_data, indent=2))
            
    async def mark_processing(self, request_id: str) -> None:
        """Mark a request as being processed."""
        if request_id in self.active_requests:
            self.active_requests[request_id].status = "processing"
            await self.add_request(self.active_requests[request_id])
            
    async def mark_completed(self, request_id: str) -> None:
        """Mark a request as completed and move to completed directory."""
        if request_id in self.active_requests:
            request = self.active_requests.pop(request_id)
            request.status = "completed"
            
            # Move to completed directory
            old_path = self.queue_dir / f"{request_id}.json"
            new_path = self.completed_dir / f"{request_id}.json"
            
            if old_path.exists():
                old_path.rename(new_path)
                
    async def mark_failed(self, request_id: str, error: str) -> None:
        """Mark a request as failed and move to failed directory."""
        if request_id in self.active_requests:
            request = self.active_requests.pop(request_id)
            request.status = f"failed: {error}"
            
            # Move to failed directory
            old_path = self.queue_dir / f"{request_id}.json"
            new_path = self.failed_dir / f"{request_id}-{int(time.time())}.json"
            
            if old_path.exists():
                old_path.rename(new_path)
                
    async def load_pending_requests(self) -> List[RequestInfo]:
        """Load all pending requests from disk after a crash."""
        pending_requests = []
        
        for request_file in self.queue_dir.glob("*.json"):
            if request_file.is_file():
                try:
                    async with aiofiles.open(request_file, 'r') as f:
                        data = json.loads(await f.read())
                        
                    request = RequestInfo(
                        request_id=data["request_id"],
                        endpoint=data["endpoint"],
                        method=data["method"],
                        headers=data["headers"],
                        body=data["body"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        model=data.get("model"),
                        status=data.get("status", "pending"),
                        retry_count=data.get("retry_count", 0)
                    )
                    
                    # Only reload requests that were pending or processing
                    if request.status in ["pending", "processing"]:
                        request.retry_count += 1
                        pending_requests.append(request)
                        self.active_requests[request.request_id] = request
                        
                except Exception as e:
                    logger.error(f"Failed to load request from {request_file}: {e}")
                    
        return pending_requests

class LLMSupervisor:
    """Supervisor for LLM service with crash recovery."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.processes: Dict[str, ProcessInfo] = {}
        self.request_queue = RequestQueue(Path(self.config.get("queue_dir", "/tmp/lbrx_queue")))
        self.health_check_interval = self.config.get("health_check_interval", 30)
        self.restart_delay = self.config.get("restart_delay", 5)
        self.max_restart_attempts = self.config.get("max_restart_attempts", 10)
        self.restart_window = timedelta(minutes=self.config.get("restart_window_minutes", 10))
        self.running = False
        self._tasks: Set[asyncio.Task] = set()
        
    def _load_config(self, config_path: Optional[Path]) -> Dict[str, Any]:
        """Load supervisor configuration."""
        default_config = {
            "services": {
                "llm_server": {
                    "command": ["python", "-m", "start"],
                    "working_dir": "/Users/polyversai/hosted_dev/lbrxserver",
                    "env": {
                        "PYTHONPATH": "/Users/polyversai/hosted_dev/lbrxserver",
                        "MLX_MEMORY_LIMIT": "0",  # No memory limit as requested
                        "MLX_CACHE_LIMIT": "0"
                    },
                    "health_endpoint": "http://localhost:8555/api/v1/health",
                    "startup_delay": 60,  # Wait for models to load
                    "memory_threshold_gb": 280,  # Alert if memory usage exceeds this
                }
            },
            "queue_dir": "/tmp/lbrx_queue",
            "health_check_interval": 30,
            "restart_delay": 5,
            "max_restart_attempts": 10,
            "restart_window_minutes": 10,
            "log_dir": "/var/log/lbrx_supervisor"
        }
        
        if config_path and config_path.exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
        
    async def start(self):
        """Start the supervisor."""
        logger.info("Starting LLM Supervisor...")
        self.running = True
        
        # Create log directory
        log_dir = Path(self.config.get("log_dir", "/var/log/lbrx_supervisor"))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Load any pending requests from previous crash
        pending_requests = await self.request_queue.load_pending_requests()
        if pending_requests:
            logger.info(f"Loaded {len(pending_requests)} pending requests from previous session")
            
        # Start all configured services
        for service_name, service_config in self.config["services"].items():
            await self._start_service(service_name, service_config)
            
        # Start monitoring tasks
        self._tasks.add(asyncio.create_task(self._monitor_loop()))
        self._tasks.add(asyncio.create_task(self._health_check_loop()))
        
        # If we have pending requests, wait for services to be healthy then replay them
        if pending_requests:
            self._tasks.add(asyncio.create_task(self._replay_requests(pending_requests)))
            
        # Wait for shutdown signal
        await self._wait_for_shutdown()
        
    async def _start_service(self, name: str, config: Dict[str, Any]) -> bool:
        """Start a supervised service."""
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(config.get("env", {}))
            
            # Start the process using uv run
            command = ["uv", "run"] + config["command"]
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=config.get("working_dir"),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Create process info
            process_info = ProcessInfo(
                name=name,
                command=config["command"],
                pid=process.pid,
                start_time=datetime.now(),
                last_restart=datetime.now()
            )
            
            self.processes[name] = process_info
            logger.info(f"Started {name} with PID {process.pid}")
            
            # Monitor process output
            self._tasks.add(asyncio.create_task(
                self._monitor_process_output(name, process)
            ))
            
            # Wait for startup delay
            startup_delay = config.get("startup_delay", 10)
            await asyncio.sleep(startup_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            return False
            
    async def _monitor_process_output(self, name: str, process: asyncio.subprocess.Process):
        """Monitor process stdout/stderr for errors and crashes."""
        crash_indicators = [
            "failed assertion",
            "Segmentation fault",
            "Killed",
            "out of memory",
            "SIGKILL",
            "SIGTERM",
            "addCompletedHandler"  # MLX Metal crash
        ]
        
        async def read_stream(stream, stream_name):
            while True:
                try:
                    line = await stream.readline()
                    if not line:
                        break
                        
                    line_str = line.decode('utf-8', errors='replace').strip()
                    if line_str:
                        # Log to file
                        log_file = Path(self.config["log_dir"]) / f"{name}_{stream_name}.log"
                        async with aiofiles.open(log_file, 'a') as f:
                            await f.write(f"{datetime.now().isoformat()} {line_str}\n")
                            
                        # Check for crash indicators
                        for indicator in crash_indicators:
                            if indicator in line_str:
                                logger.error(f"Crash indicator detected in {name}: {indicator}")
                                logger.error(f"Full line: {line_str}")
                                
                except Exception as e:
                    logger.error(f"Error reading {stream_name} for {name}: {e}")
                    break
                    
        # Monitor both stdout and stderr
        await asyncio.gather(
            read_stream(process.stdout, "stdout"),
            read_stream(process.stderr, "stderr")
        )
        
        # Process has exited
        return_code = await process.wait()
        logger.error(f"{name} exited with code {return_code}")
        
        # Mark process as crashed
        if name in self.processes:
            self.processes[name].pid = None
            self.processes[name].crashes.append(datetime.now())
            
    async def _monitor_loop(self):
        """Monitor processes and restart if needed."""
        while self.running:
            try:
                for name, process_info in list(self.processes.items()):
                    if process_info.pid:
                        # Check if process is still running
                        try:
                            proc = psutil.Process(process_info.pid)
                            if not proc.is_running():
                                raise psutil.NoSuchProcess(process_info.pid)
                                
                            # Check memory usage
                            memory_gb = proc.memory_info().rss / (1024 ** 3)
                            threshold = self.config["services"][name].get("memory_threshold_gb", 280)
                            
                            if memory_gb > threshold:
                                logger.warning(f"{name} memory usage: {memory_gb:.2f}GB (threshold: {threshold}GB)")
                                
                        except psutil.NoSuchProcess:
                            logger.error(f"{name} (PID {process_info.pid}) is no longer running")
                            process_info.pid = None
                            
                    # Restart if needed
                    if not process_info.pid and self._should_restart(process_info):
                        logger.info(f"Attempting to restart {name}...")
                        await asyncio.sleep(self.restart_delay)
                        
                        if await self._start_service(name, self.config["services"][name]):
                            process_info.restart_count += 1
                        else:
                            logger.error(f"Failed to restart {name}")
                            
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                
            await asyncio.sleep(5)  # Check every 5 seconds
            
    def _should_restart(self, process_info: ProcessInfo) -> bool:
        """Determine if a process should be restarted."""
        # Check restart attempts within window
        recent_crashes = [
            crash for crash in process_info.crashes 
            if crash > datetime.now() - self.restart_window
        ]
        
        if len(recent_crashes) >= self.max_restart_attempts:
            logger.error(f"{process_info.name} crashed {len(recent_crashes)} times in {self.restart_window}. Not restarting.")
            return False
            
        return True
        
    async def _health_check_loop(self):
        """Perform health checks on services."""
        while self.running:
            try:
                for name, config in self.config["services"].items():
                    if "health_endpoint" in config and name in self.processes:
                        process_info = self.processes[name]
                        if process_info.pid:
                            is_healthy = await self._check_health(config["health_endpoint"])
                            if not is_healthy:
                                logger.warning(f"{name} health check failed")
                                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                
            await asyncio.sleep(self.health_check_interval)
            
    async def _check_health(self, endpoint: str) -> bool:
        """Check if a service is healthy."""
        try:
            # Simple HTTP health check
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=10) as response:
                    return response.status == 200
        except Exception:
            return False
            
    async def _replay_requests(self, requests: List[RequestInfo]):
        """Replay pending requests after recovery."""
        # Wait for services to be healthy
        logger.info("Waiting for services to be healthy before replaying requests...")
        
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            all_healthy = True
            for name, config in self.config["services"].items():
                if "health_endpoint" in config:
                    if not await self._check_health(config["health_endpoint"]):
                        all_healthy = False
                        break
                        
            if all_healthy:
                break
                
            await asyncio.sleep(10)
            
        if not all_healthy:
            logger.error("Services did not become healthy in time. Skipping request replay.")
            return
            
        # Replay requests
        logger.info(f"Replaying {len(requests)} pending requests...")
        
        for request in requests:
            try:
                # TODO: Implement actual request replay logic
                # This would need to integrate with the FastAPI app
                logger.info(f"Would replay request {request.request_id} to {request.endpoint}")
                
            except Exception as e:
                logger.error(f"Failed to replay request {request.request_id}: {e}")
                await self.request_queue.mark_failed(request.request_id, str(e))
                
    async def _wait_for_shutdown(self):
        """Wait for shutdown signal."""
        shutdown_event = asyncio.Event()
        
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}. Shutting down...")
            shutdown_event.set()
            
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        await shutdown_event.wait()
        
        # Graceful shutdown
        logger.info("Performing graceful shutdown...")
        self.running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # Terminate processes
        for name, process_info in self.processes.items():
            if process_info.pid:
                try:
                    proc = psutil.Process(process_info.pid)
                    proc.terminate()
                    logger.info(f"Terminated {name} (PID {process_info.pid})")
                except Exception as e:
                    logger.error(f"Failed to terminate {name}: {e}")

async def main():
    """Main entry point for the supervisor."""
    import argparse
    parser = argparse.ArgumentParser(description="LLM Service Supervisor")
    parser.add_argument("--config", type=Path, help="Configuration file path")
    args = parser.parse_args()
    
    supervisor = LLMSupervisor(args.config)
    await supervisor.start()

if __name__ == "__main__":
    asyncio.run(main())