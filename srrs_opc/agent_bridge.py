"""
Agent Bridge — connects PO to OCE agent infrastructure.

Provides a unified interface for agent coordination, tool calling,
and multi-agent workflows. Used by PO to spawn and coordinate
specialized agents for complex tasks.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("srrs_opc.agent_bridge")


@dataclass
class AgentTask:
    """A task to be executed by an agent."""

    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_name: str = ""
    prompt: str = ""
    status: str = "pending"  # pending, running, complete, error, cancelled
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=lambda: asyncio.get_event_loop().time if asyncio.get_event_loop() else 0)


@dataclass
class AgentSpec:
    """Specification for an agent type."""

    name: str
    role: str
    capabilities: List[str] = field(default_factory=list)
    model: str = "po"
    config: Dict[str, Any] = field(default_factory=dict)


class AgentBridge:
    """
    Bridge between PO and OCE agent infrastructure.

    Manages agent registration, task dispatch, and result collection.
    """

    def __init__(self):
        self._agents: Dict[str, AgentSpec] = {}
        self._tasks: Dict[str, AgentTask] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default agent types."""
        self.register_agent(AgentSpec(
            name="analyst",
            role="Analysis and reasoning",
            capabilities=["reasoning", "analysis", "summarization"],
        ))
        self.register_agent(AgentSpec(
            name="researcher",
            role="Research and information retrieval",
            capabilities=["search", "retrieval", "synthesis"],
        ))
        self.register_agent(AgentSpec(
            name="coder",
            role="Code generation and execution",
            capabilities=["code_generation", "code_review", "execution"],
        ))

    def register_agent(self, spec: AgentSpec) -> None:
        """Register a new agent type."""
        self._agents[spec.name] = spec
        logger.info(f"Registered agent: {spec.name}")

    def deregister_agent(self, name: str) -> None:
        """Remove an agent type."""
        self._agents.pop(name, None)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            {"name": a.name, "role": a.role, "capabilities": a.capabilities}
            for a in self._agents.values()
        ]

    def get_agent(self, name: str) -> Optional[AgentSpec]:
        """Get an agent by name."""
        return self._agents.get(name)

    def submit_task(self, task: AgentTask) -> str:
        """Submit a task for execution."""
        self._tasks[task.task_id] = task
        return task.task_id

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_status(self) -> Dict[str, Any]:
        """Get bridge status."""
        return {
            "agents": len(self._agents),
            "tasks_pending": sum(1 for t in self._tasks.values() if t.status == "pending"),
            "tasks_running": sum(1 for t in self._tasks.values() if t.status == "running"),
            "tasks_complete": sum(1 for t in self._tasks.values() if t.status == "complete"),
        }