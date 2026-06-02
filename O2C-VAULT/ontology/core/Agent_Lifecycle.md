# Agent Lifecycle

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O3-B5: AgentLifecycle
======================
Manage agent states.

Tracks the full lifecycle of spawned agents: pending → running →
[complete | failed | timeout | cancelled]. Handles state transitions,
health checks, and cleanup.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger("spawn.lifecycle")


class AgentState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# Valid state transitions
VALID_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.PENDING: {AgentState.RUNNING, AgentState.CANCELLED},
    AgentState.RUNNING: {AgentState.COMPLETE, AgentState.FAILED, AgentState.TIMEOUT, AgentState.CANCELLED},
    AgentState.COMPLETE: set(),
    AgentState.FAILED: set(),
    AgentState.TIMEOUT: set(),
    AgentState.CANCELLED: set(),
}


@dataclass
class AgentInstance:
    """Represents a single spawned agent."""
    agent_id: str
    plan_id: str
    task_type: str
    model: str
    state: AgentState = AgentState.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str | None = None
    ended_at: str | None = None
    turns_used: int = 0
    tokens_used: int = 0
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.ended_at:
            try:
                start = datetime.fromisoformat(self.started_at)
                end = datetime.fromisoformat(self.ended_at)
                return (end - start).total_seconds()
            except (ValueError, TypeError):
                return None
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "plan_id": self.plan_id,
            "task_type": self.task_type,
            "model": self.model,
            "state": self.state.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "turns_used": self.turns_used,
            "tokens_used": self.tokens_used,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
        }


class AgentLifecycle:
    """
    Manages the full lifecycle of spawned agents.
    
    Tracks state, enforces valid transitions, handles timeouts,
    and provides lifecycle statistics.
    """

    def __init__(self):
        self._agents: dict[str, AgentInstance] = {}

    def register(self, agent: AgentInstance) -> None:
        """Register a new agent instance."""
        self._agents[agent.agent_id] = agent
        logger.info(f"Agent registered: {agent.agent_id} ({agent.task_type})")

    def transition(self, agent_id: str, new_state: AgentState, **kwargs: Any) -> bool:
        """
        Transition an agent to a new state.
        
        Returns True if transition was valid and applied.
        """
        agent = self._agents.get(agent_id)
        if not agent:
            logger.warning(f"Unknown agent: {agent_id}")
            return False

        current = agent.state
        if new_state not in VALID_TRANSITIONS.get(current, set()):
            logger.warning(
                f"Invalid transition: {agent_id} {current.value} -> {new_state.value}"
            )
            return False

        agent.state = new_state
        now = datetime.now(timezone.utc).isoformat()

        if new_state == AgentState.RUNNING and not agent.started_at:
            agent.started_at = now
        elif new_state in (AgentState.COMPLETE, AgentState.FAILED, AgentState.TIMEOUT, AgentState.CANCELLED):
            agent.ended_at = now

        # Apply extra fields
        for key, value in kwargs.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        logger.info(f"Agent {agent_id}: {current.value} -> {new_state.value}")
        return True

    def start(self, agent_id: str) -> bool:
        """Legacy-compatible start method. Transitions pending -> running."""
        return self.transition(agent_id, AgentState.RUNNING)

    def complete(self, agent_id: str) -> bool:
        """Legacy-compatible complete method. Transitions running -> complete."""
        return self.transition(agent_id, AgentState.COMPLETE)

    def fail(self, agent_id: str, error: str = "") -> bool:
        """Legacy-compatible fail method. Transitions running -> failed."""
        return self.transition(agent_id, AgentState.FAILED, error=error)

    def get(self, agent_id: str) -> AgentInstance | None:
        return self._agents.get(agent_id)

    def get_active(self) -> list[AgentInstance]:
        """Get all active (pending or running) agents."""
        return [
            a for a in self._agents.values()
            if a.state in (AgentState.PENDING, AgentState.RUNNING)
        ]

    def get_by_state(self, state: AgentState) -> list[AgentInstance]:
        return [a for a in self._agents.values() if a.state == state]

    def get_by_plan(self, plan_id: str) -> list[AgentInstance]:
        return [a for a in self._agents.values() if a.plan_id == plan_id]

    def check_timeouts(self, max_age_seconds: float = 600) -> list[str]:
        """Check for timed-out agents. Returns list of timed-out agent IDs."""
        timed_out = []
        now = datetime.now(timezone.utc)
        for agent in self.get_active():
            if agent.started_at:
                try:
                    start = datetime.fromisoformat(agent.started_at)
                    age = (now - start).total_seconds()
                    if age > max_age_seconds:
                        self.transition(agent.agent_id, AgentState.TIMEOUT)
                        timed_out.append(agent.agent_id)
                except (ValueError, TypeError):
                    pass
        return timed_out

    def get_stats(self) -> dict[str, Any]:
        """Get lifecycle statistics."""
        total = len(self._agents)
        by_state = {s.value: 0 for s in AgentState}
        for agent in self._agents.values():
            by_state[agent.state.value] += 1

        total_tokens = sum(a.tokens_used for a in self._agents.values())
        durations = [a.duration_seconds for a in self._agents.values() if a.duration_seconds is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_agents": total,
            "by_state": by_state,
            "active_count": len(self.get_active()),
            "total_tokens": total_tokens,
            "avg_duration_seconds": round(avg_duration, 1),
        }

```

LINKS:
[[02 Agent Workflow]]
[[Agents]]
[[Sub Agent Rules]]
[[Agent Topology]]
[[Hermes Agent Activation Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Ontology Core Summary]]
[[Citation Workflow]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
