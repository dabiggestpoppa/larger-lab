"""
V3 Phase 4 — OCE Shell Runtime

Persistent executive cognition. Not chatbot, not dashboard — persistent executive 
cognition. Maintains identity, continuity, orchestration, memory alignment, active 
trajectories, field state, system priorities.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ShellState:
    """Current state of the OCE shell."""
    shell_id: str
    timestamp: float
    identity_hash: str
    continuity_score: float
    active_trajectories: list[str]
    field_state: dict
    system_priorities: list[str]
    memory_alignment: float
    is_stable: bool = True

    def to_dict(self) -> dict:
        return {
            "shell_id": self.shell_id,
            "timestamp": self.timestamp,
            "identity_hash": self.identity_hash,
            "continuity_score": self.continuity_score,
            "active_trajectories": self.active_trajectories,
            "field_state": self.field_state,
            "system_priorities": self.system_priorities,
            "memory_alignment": self.memory_alignment,
            "is_stable": self.is_stable,
        }


class OCEShell:
    """
    OCE Shell — Central Continuity Organism.
    
    Persistent executive cognition that maintains identity and continuity
    across sessions, crashes, and model changes.
    """

    def __init__(self, identity_hash: Optional[str] = None):
        self.shell_id = f"shell-{uuid.uuid4().hex[:8]}"
        self.identity_hash = identity_hash or self._generate_identity()
        self._state = ShellState(
            shell_id=self.shell_id,
            timestamp=time.time(),
            identity_hash=self.identity_hash,
            continuity_score=1.0,
            active_trajectories=[],
            field_state={},
            system_priorities=["coherence", "continuity", "efficiency"],
            memory_alignment=1.0,
        )
        self._state_history: list[ShellState] = []

    def _generate_identity(self) -> str:
        """Generate a unique identity hash for this shell instance."""
        return f"id-{uuid.uuid4().hex[:16]}"

    @property
    def state(self) -> ShellState:
        return self._state

    def update_field_state(self, field_state: dict) -> None:
        """Update the field state in the shell."""
        self._state.field_state = field_state
        self._state.timestamp = time.time()

    def add_trajectory(self, trajectory_id: str) -> None:
        """Add an active trajectory to the shell."""
        if trajectory_id not in self._state.active_trajectories:
            self._state.active_trajectories.append(trajectory_id)

    def remove_trajectory(self, trajectory_id: str) -> None:
        """Remove a trajectory from active list."""
        if trajectory_id in self._state.active_trajectories:
            self._state.active_trajectories.remove(trajectory_id)

    def set_priorities(self, priorities: list[str]) -> None:
        """Set system priorities."""
        self._state.system_priorities = priorities

    def measure_continuity(self) -> float:
        """Measure current continuity score."""
        return self._state.continuity_score

    def snapshot(self) -> ShellState:
        """Save current state to history and return a copy."""
        self._state_history.append(self._state)
        if len(self._state_history) > 100:
            self._state_history = self._state_history[-100:]
        # Return a copy to avoid mutation issues
        return ShellState(
            shell_id=self._state.shell_id,
            timestamp=self._state.timestamp,
            identity_hash=self._state.identity_hash,
            continuity_score=self._state.continuity_score,
            active_trajectories=list(self._state.active_trajectories),
            field_state=dict(self._state.field_state),
            system_priorities=list(self._state.system_priorities),
            memory_alignment=self._state.memory_alignment,
            is_stable=self._state.is_stable,
        )

    def restore(self, state: ShellState) -> None:
        """Restore shell state from a snapshot."""
        self._state = ShellState(
            shell_id=state.shell_id,
            timestamp=time.time(),
            identity_hash=state.identity_hash,
            continuity_score=state.continuity_score,
            active_trajectories=list(state.active_trajectories),
            field_state=dict(state.field_state),
            system_priorities=list(state.system_priorities),
            memory_alignment=state.memory_alignment,
            is_stable=state.is_stable,
        )

    def get_stats(self) -> dict:
        """Get shell statistics."""
        return {
            "shell_id": self.shell_id,
            "identity_hash": self.identity_hash,
            "continuity_score": self._state.continuity_score,
            "active_trajectories": len(self._state.active_trajectories),
            "memory_alignment": self._state.memory_alignment,
            "state_history_size": len(self._state_history),
        }