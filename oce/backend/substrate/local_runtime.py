"""
O-6: Local Runtime — Central Execution Substrate
==============================================

Central local execution substrate for machine-aware operations.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("oce.substrate.local_runtime")


@dataclass
class RuntimeState:
    """Live machine state snapshot."""
    timestamp: str = ""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    active_processes: int = 0
    active_sandboxes: int = 0
    uptime_seconds: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class LocalRuntime:
    """
    Central local execution substrate.
    
    Provides:
    - execute_task() — bounded task execution
    - inspect_runtime() — live system state
    - track_environment() — workspace awareness
    - manage_execution() — execution lifecycle
    - sync_state() — state synchronization
    """
    
    _instance: Optional["LocalRuntime"] = None
    
    def __init__(self):
        self.state = RuntimeState()
        self._start_time = datetime.now(timezone.utc)
        self._initialized = False
    
    async def initialize(self):
        """Initialize the local runtime substrate."""
        if self._initialized:
            return
        
        logger.info("Initializing Local Runtime substrate...")
        self._initialized = True
        logger.info("Local Runtime substrate ready")
    
    async def execute_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        sandbox_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task within bounded substrate.
        
        Args:
            task_type: Type of task to execute
            payload: Task parameters
            sandbox_id: Optional sandbox for isolated execution
            
        Returns:
            Execution result
        """
        logger.info(f"Executing task: {task_type}")
        
        # Route to appropriate handler based on task_type
        if task_type == "terminal":
            return await self._execute_terminal(payload, sandbox_id)
        elif task_type == "filesystem":
            return await self._execute_filesystem(payload, sandbox_id)
        elif task_type == "process":
            return await self._execute_process(payload, sandbox_id)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _execute_terminal(self, payload: Dict[str, Any], sandbox_id: Optional[str]) -> Dict[str, Any]:
        """Execute terminal command."""
        from .terminal_orchestrator import get_terminal_orchestrator
        orchestrator = get_terminal_orchestrator()
        return await orchestrator.execute(payload.get("command", ""), sandbox_id)
    
    async def _execute_filesystem(self, payload: Dict[str, Any], sandbox_id: Optional[str]) -> Dict[str, Any]:
        """Execute filesystem operation."""
        from .filesystem_awareness import get_filesystem_awareness
        fs = get_filesystem_awareness()
        return await fs.execute(payload)
    
    async def _execute_process(self, payload: Dict[str, Any], sandbox_id: Optional[str]) -> Dict[str, Any]:
        """Execute process operation."""
        from .process_observer import get_process_observer
        po = get_process_observer()
        return await po.execute(payload)
    
    async def inspect_runtime(self) -> RuntimeState:
        """Get current live system state."""
        import psutil
        
        self.state.cpu_percent = psutil.cpu_percent(interval=0.1)
        self.state.memory_percent = psutil.virtual_memory().percent
        self.state.disk_percent = psutil.disk_usage("/").percent
        
        # Count active processes
        from .process_observer import get_process_observer
        po = get_process_observer()
        self.state.active_processes = len(po.get_active_processes())
        
        # Count active sandboxes
        from .execution_sandbox import get_execution_sandbox
        sb = get_execution_sandbox()
        self.state.active_sandboxes = len(sb.get_active_sandboxes())
        
        # Calculate uptime
        uptime = datetime.now(timezone.utc) - self._start_time
        self.state.uptime_seconds = int(uptime.total_seconds())
        
        return self.state
    
    async def track_environment(self) -> Dict[str, Any]:
        """Get workspace environment awareness."""
        from .environment_model import get_environment_model
        em = get_environment_model()
        return em.get_current_environment()
    
    async def manage_execution(self, action: str, target: str) -> Dict[str, Any]:
        """Manage execution lifecycle."""
        if action == "terminate":
            from .process_observer import get_process_observer
            po = get_process_observer()
            return await po.terminate(target)
        elif action == "pause":
            return {"status": "paused", "target": target}
        elif action == "resume":
            return {"status": "resumed", "target": target}
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def sync_state(self) -> Dict[str, Any]:
        """Synchronize substrate state."""
        state = await self.inspect_runtime()
        env = await self.track_environment()
        return {
            "runtime": state.__dict__,
            "environment": env,
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state as dict."""
        return {
            "runtime": self.state.__dict__,
            "initialized": self._initialized,
        }


def get_local_runtime() -> LocalRuntime:
    """Get singleton LocalRuntime instance."""
    if LocalRuntime._instance is None:
        LocalRuntime._instance = LocalRuntime()
    return LocalRuntime._instance