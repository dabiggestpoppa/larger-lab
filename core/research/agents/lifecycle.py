"""
L3.6 — Agent lifecycle manager.

Manages research agent lifecycle:
States: queued → running → completed | failed | abandoned
Bounds: max 3 concurrent, max 1hr per task, max 2 retries

Usage:
    lifecycle = AgentLifecycle()
    lifecycle.spawn(task)
    lifecycle.heartbeat(task_id)
    lifecycle.complete(task_id, result)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Lifecycle bounds
MAX_CONCURRENT_AGENTS = 3
MAX_TASK_DURATION_SECONDS = 3600  # 1 hour
MAX_RETRIES = 2
HEARTBEAT_TIMEOUT_SECONDS = 300  # 5 minutes without heartbeat = stale


class AgentState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


@dataclass
class AgentInstance:
    """Represents a running research agent."""
    agent_id: str = ""
    task_id: str = ""
    state: AgentState = AgentState.QUEUED
    spawned_at: str = ""
    last_heartbeat: str = ""
    retry_count: int = 0
    error_message: str = ""
    result: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.agent_id:
            self.agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        if not self.spawned_at:
            self.spawned_at = datetime.now(timezone.utc).isoformat()
        if not self.last_heartbeat:
            self.last_heartbeat = self.spawned_at


class AgentLifecycle:
    """
    Manages research agent lifecycle.
    
    Enforces:
    - Max 3 concurrent agents
    - Max 1 hour per task
    - Max 2 retries before abandoned
    - Heartbeat timeout detection
    """

    def __init__(
        self,
        max_concurrent: int = MAX_CONCURRENT_AGENTS,
        max_duration: int = MAX_TASK_DURATION_SECONDS,
        max_retries: int = MAX_RETRIES,
    ):
        self.max_concurrent = max_concurrent
        self.max_duration = max_duration
        self.max_retries = max_retries
        self._agents: Dict[str, AgentInstance] = {}

    def spawn(self, task_id: str) -> Optional[AgentInstance]:
        """
        Spawn a new research agent for a task.
        
        Returns None if max concurrent reached.
        """
        # Check concurrent limit
        running = self._count_by_state(AgentState.RUNNING)
        if running >= self.max_concurrent:
            logger.warning(f"Lifecycle: max concurrent reached ({running}/{self.max_concurrent})")
            return None

        agent = AgentInstance(
            task_id=task_id,
            state=AgentState.RUNNING,
        )
        self._agents[agent.agent_id] = agent
        
        logger.info(f"Lifecycle: spawned {agent.agent_id} for task {task_id}")
        return agent

    def heartbeat(self, agent_id: str) -> bool:
        """
        Update agent heartbeat.
        
        Returns False if agent not found or timed out.
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        # Check if task exceeded time limit
        if self._is_timed_out(agent):
            logger.warning(f"Lifecycle: {agent_id} timed out")
            self._transition(agent_id, AgentState.FAILED, "Task exceeded time limit")
            return False
        
        agent.last_heartbeat = datetime.now(timezone.utc).isoformat()
        return True

    def complete(self, agent_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """Mark agent as completed."""
        return self._transition(agent_id, AgentState.COMPLETED, result=result)

    def fail(self, agent_id: str, error: str) -> bool:
        """
        Mark agent as failed. Increments retry count.
        If max retries exceeded, marks as abandoned.
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        agent.retry_count += 1
        agent.error_message = error
        
        if agent.retry_count > self.max_retries:
            logger.warning(f"Lifecycle: {agent_id} abandoned after {agent.retry_count} retries")
            return self._transition(agent_id, AgentState.ABANDONED, error=error)
        else:
            logger.info(f"Lifecycle: {agent_id} failed (retry {agent.retry_count}/{self.max_retries})")
            return self._transition(agent_id, AgentState.FAILED, error=error)

    def get_agent(self, agent_id: str) -> Optional[AgentInstance]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_running(self) -> List[AgentInstance]:
        """Get all running agents."""
        return [a for a in self._agents.values() if a.state == AgentState.RUNNING]

    def get_stale_agents(self) -> List[AgentInstance]:
        """Get agents that haven't sent a heartbeat recently."""
        now = datetime.now(timezone.utc)
        stale = []
        for agent in self._agents.values():
            if agent.state != AgentState.RUNNING:
                continue
            try:
                last_hb = datetime.fromisoformat(agent.last_heartbeat)
                if (now - last_hb).total_seconds() > HEARTBEAT_TIMEOUT_SECONDS:
                    stale.append(agent)
            except (ValueError, TypeError):
                stale.append(agent)
        return stale

    def cleanup_stale(self) -> int:
        """Remove stale agents. Returns count cleaned."""
        stale = self.get_stale_agents()
        for agent in stale:
            self._transition(agent.agent_id, AgentState.FAILED, "Heartbeat timeout")
        return len(stale)

    def get_stats(self) -> Dict[str, Any]:
        """Get lifecycle statistics."""
        return {
            "total_agents": len(self._agents),
            "by_state": {
                state.value: self._count_by_state(state)
                for state in AgentState
            },
            "max_concurrent": self.max_concurrent,
            "max_duration": self.max_duration,
            "max_retries": self.max_retries,
            "stale_count": len(self.get_stale_agents()),
        }

    def _transition(self, agent_id: str, new_state: AgentState,
                    error: str = "", result: Optional[Dict[str, Any]] = None) -> bool:
        """Transition agent to new state."""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        old_state = agent.state
        agent.state = new_state
        
        if error:
            agent.error_message = error
        if result:
            agent.result = result
        
        logger.debug(f"Lifecycle: {agent_id} {old_state.value} → {new_state.value}")
        return True

    def _count_by_state(self, state: AgentState) -> int:
        """Count agents in a given state."""
        return sum(1 for a in self._agents.values() if a.state == state)

    def _is_timed_out(self, agent: AgentInstance) -> bool:
        """Check if agent has exceeded time limit."""
        try:
            spawned = datetime.fromisoformat(agent.spawned_at)
            now = datetime.now(timezone.utc)
            return (now - spawned).total_seconds() > self.max_duration
        except (ValueError, TypeError):
            return False