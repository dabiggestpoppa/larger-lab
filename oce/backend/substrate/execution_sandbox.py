"""
O-6: Execution Sandbox — Safe Operational Zones
===============================================

Safe operational execution zones for bounded task execution.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("oce.substrate.execution_sandbox")


class SandboxType(str, Enum):
    DEV = "dev"
    ORCHESTRATION = "orchestration"
    TESTING = "testing"
    REPLAY = "replay"


@dataclass
class Sandbox:
    """Represents an execution sandbox."""
    id: str
    name: str
    type: SandboxType
    active_tasks: int = 0
    max_tasks: int = 5
    resource_usage: Dict[str, float] = None
    created_at: str = ""
    
    def __post_init__(self):
        if self.resource_usage is None:
            self.resource_usage = {"cpu": 0.0, "memory": 0.0}


class ExecutionSandbox:
    """
    Safe operational execution zones.
    
    Types:
    - dev sandbox: Development workflows
    - orchestration sandbox: Task orchestration
    - testing sandbox: Test execution
    - replay sandbox: Historical replay
    """
    
    _instance: Optional["ExecutionSandbox"] = None
    
    def __init__(self):
        self.sandboxes: Dict[str, Sandbox] = {}
        self._initialize_default_sandboxes()
    
    def _initialize_default_sandboxes(self):
        """Create default sandboxes."""
        self.sandboxes["dev"] = Sandbox(
            id="dev",
            name="Development Sandbox",
            type=SandboxType.DEV,
            max_tasks=10,
        )
        self.sandboxes["orchestration"] = Sandbox(
            id="orchestration",
            name="Orchestration Sandbox",
            type=SandboxType.ORCHESTRATION,
            max_tasks=5,
        )
        self.sandboxes["testing"] = Sandbox(
            id="testing",
            name="Testing Sandbox",
            type=SandboxType.TESTING,
            max_tasks=3,
        )
        self.sandboxes["replay"] = Sandbox(
            id="replay",
            name="Replay Sandbox",
            type=SandboxType.REPLAY,
            max_tasks=2,
        )
        logger.info(f"Initialized {len(self.sandboxes)} sandboxes")
    
    def get_sandbox(self, sandbox_id: str) -> Optional[Sandbox]:
        """Get a specific sandbox."""
        return self.sandboxes.get(sandbox_id)
    
    def get_active_sandboxes(self) -> List[Sandbox]:
        """Get all active sandboxes."""
        return [s for s in self.sandboxes.values() if s.active_tasks > 0]
    
    def create_sandbox(
        self,
        name: str,
        sandbox_type: SandboxType,
        max_tasks: int = 5,
    ) -> Sandbox:
        """Create a new sandbox."""
        sandbox = Sandbox(
            id=str(uuid.uuid4())[:8],
            name=name,
            type=sandbox_type,
            max_tasks=max_tasks,
        )
        self.sandboxes[sandbox.id] = sandbox
        logger.info(f"Created sandbox: {sandbox.name} ({sandbox.id})")
        return sandbox
    
    def enter(self, sandbox_id: str) -> bool:
        """Enter a sandbox for execution."""
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return False
        
        if sandbox.active_tasks >= sandbox.max_tasks:
            logger.warning(f"Sandbox {sandbox_id} at capacity")
            return False
        
        sandbox.active_tasks += 1
        return True
    
    def exit(self, sandbox_id: str):
        """Exit a sandbox after execution."""
        sandbox = self.sandboxes.get(sandbox_id)
        if sandbox and sandbox.active_tasks > 0:
            sandbox.active_tasks -= 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get sandbox status."""
        return {
            "sandboxes": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type.value,
                    "active_tasks": s.active_tasks,
                    "max_tasks": s.max_tasks,
                    "resource_usage": s.resource_usage,
                }
                for s in self.sandboxes.values()
            ],
            "total_active_tasks": sum(s.active_tasks for s in self.sandboxes.values()),
        }


def get_execution_sandbox() -> ExecutionSandbox:
    """Get singleton ExecutionSandbox instance."""
    if ExecutionSandbox._instance is None:
        ExecutionSandbox._instance = ExecutionSandbox()
    return ExecutionSandbox._instance