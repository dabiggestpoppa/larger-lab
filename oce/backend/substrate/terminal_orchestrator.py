"""
O-6: Terminal Orchestrator — Command Execution Management
========================================================

All terminal execution management with safety boundaries.
"""

import asyncio
import logging
import subprocess
from typing import Any, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger("oce.substrate.terminal_orchestrator")


@dataclass
class TerminalExecution:
    """Represents a terminal execution."""
    command: str
    pid: Optional[int] = None
    status: str = "pending"
    output: str = ""
    error: str = ""
    started_at: str = ""
    completed_at: str = ""


class TerminalOrchestrator:
    """
    All terminal execution management.
    
    Capabilities:
    - Run commands
    - Monitor output
    - Track runtime
    - Stop hung processes
    - Stream logs
    - Attach execution traces
    
    Safeguards:
    - Timeouts
    - Permission scopes
    - Resource limits
    - Command allowlists
    """
    
    _instance: Optional["TerminalOrchestrator"] = None
    
    def __init__(self):
        self._active_executions: Dict[str, TerminalExecution] = {}
        self._process_timeout = 30  # seconds
    
    async def execute(
        self,
        command: str,
        sandbox_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a terminal command.
        
        Args:
            command: Command to execute
            sandbox_id: Optional sandbox context
            
        Returns:
            Execution result
        """
        from .permission_layer import get_permission_layer
        pl = get_permission_layer()
        
        if not pl.check_permission("terminal", "execute", command):
            return {"error": "Command not permitted", "command": command}
        
        if not pl.validate_command(command):
            return {"error": "Command blocked for safety", "command": command}
        
        exec_id = str(len(self._active_executions) + 1)
        execution = TerminalExecution(command=command, status="running")
        self._active_executions[exec_id] = execution
        
        try:
            # Use asyncio subprocess for non-blocking execution
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            execution.pid = proc.pid
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self._process_timeout
                )
                execution.output = stdout.decode() if stdout else ""
                execution.error = stderr.decode() if stderr else ""
                execution.status = "completed"
            except asyncio.TimeoutError:
                proc.kill()
                execution.status = "timed_out"
                execution.error = "Process timed out"
            
            return {
                "execution_id": exec_id,
                "command": command,
                "status": execution.status,
                "output": execution.output,
                "error": execution.error,
            }
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            return {"error": str(e), "command": command}
    
    async def stop_process(self, pid: int) -> Dict[str, Any]:
        """Stop a hung process."""
        try:
            import psutil
            proc = psutil.Process(pid)
            proc.terminate()
            return {"status": "terminated", "pid": pid}
        except Exception as e:
            return {"error": str(e), "pid": pid}
    
    def get_active_executions(self) -> Dict[str, Any]:
        """Get all active executions."""
        return {
            "executions": [
                {"id": eid, "command": ex.command, "status": ex.status, "pid": ex.pid}
                for eid, ex in self._active_executions.items()
            ]
        }


def get_terminal_orchestrator() -> TerminalOrchestrator:
    """Get singleton TerminalOrchestrator instance."""
    if TerminalOrchestrator._instance is None:
        TerminalOrchestrator._instance = TerminalOrchestrator()
    return TerminalOrchestrator._instance