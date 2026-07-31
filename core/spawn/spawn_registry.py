"""
O3-B10: SpawnRegistry
======================
Maintain active-agent awareness.

Central registry of all spawned agents, their states, and metadata.
Provides real-time visibility into the agent field.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("spawn.registry")


@dataclass
class RegisteredAgent:
    """Agent entry in the registry."""
    agent_id: str
    plan_id: str
    task_type: str
    model: str
    state: str = "pending"
    group_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_heartbeat: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpawnRecord:
    """Record of a spawn decision for replay."""
    spawn_id: str = ""
    agent_id: str = ""
    plan_id: str = ""
    task_type: str = ""
    model: str = ""
    status: str = "pending"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str = ""
    ended_at: str = ""
    duration_seconds: float = 0.0
    tokens_used: int = 0
    error: str | None = None
    complexity: str = ""
    confidence: float = 0.0


class SpawnRegistry:
    """
    Central registry for all spawned agents.
    
    Provides real-time awareness of the agent field:
    - Which agents are active
    - What they're working on
    - Their current state
    - Resource usage
    """

    def __init__(self):
        self._agents: dict[str, RegisteredAgent] = {}

    def register(self, agent: RegisteredAgent) -> None:
        """Register a new agent."""
        self._agents[agent.agent_id] = agent
        logger.info(f"Agent registered: {agent.agent_id} ({agent.task_type})")

    def unregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def update_state(self, agent_id: str, state: str) -> bool:
        """Update an agent's state."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        agent.state = state
        agent.last_heartbeat = datetime.now(timezone.utc).isoformat()
        return True

    def heartbeat(self, agent_id: str) -> bool:
        """Update an agent's heartbeat."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        agent.last_heartbeat = datetime.now(timezone.utc).isoformat()
        return True

    def update_status(self, agent_id: str, status: str) -> bool:
        """Legacy-compatible update_status method."""
        return self.update_state(agent_id, status)

    def get(self, agent_id: str) -> RegisteredAgent | None:
        return self._agents.get(agent_id)

    def get_all(self) -> list[RegisteredAgent]:
        return list(self._agents.values())

    def get_active(self) -> list[RegisteredAgent]:
        """Get all active (non-terminal) agents."""
        return [
            a for a in self._agents.values()
            if a.state in ("pending", "running")
        ]

    def get_by_state(self, state: str) -> list[RegisteredAgent]:
        return [a for a in self._agents.values() if a.state == state]

    def get_by_task_type(self, task_type: str) -> list[RegisteredAgent]:
        return [a for a in self._agents.values() if a.task_type == task_type]

    def get_by_group(self, group_id: str) -> list[RegisteredAgent]:
        return [a for a in self._agents.values() if a.group_id == group_id]

    def get_field_snapshot(self) -> dict[str, Any]:
        """Get a snapshot of the current agent field."""
        active = self.get_active()
        return {
            "total_agents": len(self._agents),
            "active_agents": len(active),
            "by_state": self._count_by_state(),
            "by_task_type": self._count_by_type(),
            "active_details": [
                {
                    "agent_id": a.agent_id,
                    "task_type": a.task_type,
                    "model": a.model,
                    "state": a.state,
                    "created_at": a.created_at,
                }
                for a in active
            ],
        }

    def _count_by_state(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for a in self._agents.values():
            counts[a.state] = counts.get(a.state, 0) + 1
        return counts

    def _count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for a in self._agents.values():
            counts[a.task_type] = counts.get(a.task_type, 0) + 1
        return counts
