"""
O-6: Process Observer — Real-time Process Awareness
===================================================

Real-time process awareness and monitoring.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("oce.substrate.process_observer")


@dataclass
class ProcessInfo:
    """Information about a process."""
    pid: int
    name: str
    status: str  # "running", "idle", "hung", "terminated"
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    runtime_seconds: int = 0
    command: str = ""


class ProcessObserver:
    """
    Real-time process awareness.
    
    Tracks:
    - Active processes
    - Spawned runtimes
    - CPU usage
    - Memory usage
    - Hung processes
    - Orphaned tasks
    """
    
    _instance: Optional["ProcessObserver"] = None
    
    def __init__(self):
        self._monitored_processes: Dict[int, ProcessInfo] = {}
    
    def scan_processes(self) -> List[ProcessInfo]:
        """Scan all running processes."""
        import psutil
        
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "cmdline"]):
            try:
                info = ProcessInfo(
                    pid=proc.info["pid"],
                    name=proc.info["name"],
                    status="running",
                    cpu_percent=proc.info["cpu_percent"] or 0.0,
                    memory_percent=proc.info["memory_percent"] or 0.0,
                    command=" ".join(proc.info["cmdline"] or []),
                )
                processes.append(info)
                self._monitored_processes[proc.info["pid"]] = info
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return processes
    
    def get_active_processes(self) -> List[Dict[str, Any]]:
        """Get active processes as dict list."""
        return [
            {
                "pid": p.pid,
                "name": p.name,
                "status": p.status,
                "cpu": p.cpu_percent,
                "memory": p.memory_percent,
                "command": p.command,
            }
            for p in self._monitored_processes.values()
            if p.status == "running"
        ]
    
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute process operation."""
        operation = payload.get("operation")
        
        if operation == "list":
            return {"processes": [p.__dict__ for p in self.scan_processes()]}
        elif operation == "terminate":
            return await self.terminate(payload.get("pid", 0))
        elif operation == "monitor":
            return {"monitored": len(self._monitored_processes)}
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    async def terminate(self, pid: int) -> Dict[str, Any]:
        """Terminate a process."""
        try:
            import psutil
            proc = psutil.Process(pid)
            proc.terminate()
            
            if pid in self._monitored_processes:
                self._monitored_processes[pid].status = "terminated"
            
            return {"status": "terminated", "pid": pid}
        except Exception as e:
            return {"error": str(e), "pid": pid}
    
    def detect_hung_processes(self, threshold_seconds: int = 300) -> List[int]:
        """Detect hung processes (running > threshold seconds)."""
        hung = []
        for pid, proc in self._monitored_processes.items():
            if proc.runtime_seconds > threshold_seconds and proc.status == "running":
                hung.append(pid)
        return hung


def get_process_observer() -> ProcessObserver:
    """Get singleton ProcessObserver instance."""
    if ProcessObserver._instance is None:
        ProcessObserver._instance = ProcessObserver()
    return ProcessObserver._instance