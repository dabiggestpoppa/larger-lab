"""
V3 Phase 5 — Temporal Trajectory Engine
Tracks how the cognitive field evolves over time.

Instead of seeing history as individual moments, the trajectory engine
sees continuous trajectories — patterns of change that reveal the
field's developmental arc.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Trajectory:
    """A continuous trajectory of field evolution."""
    trajectory_id: str
    trajectory_type: str          # "project", "behavioral", "topology", "strategic"
    coherence_score: float = 0.5
    entropy_drift: float = 0.0
    historical_states: list[str] = field(default_factory=list)
    active_attractors: list[str] = field(default_factory=list)
    continuity_weight: float = 1.0
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

    @property
    def is_stable(self) -> bool:
        return self.coherence_score > 0.6 and self.entropy_drift < 0.3

    @property
    def age_hours(self) -> float:
        return (time.time() - self.created_at) / 3600

    def add_state(self, state_id: str) -> None:
        self.historical_states.append(state_id)
        self.last_updated = time.time()

    def to_dict(self) -> dict:
        return {
            "trajectory_id": self.trajectory_id,
            "type": self.trajectory_type,
            "coherence": round(self.coherence_score, 4),
            "entropy_drift": round(self.entropy_drift, 4),
            "state_count": len(self.historical_states),
            "is_stable": self.is_stable,
            "age_hours": round(self.age_hours, 2),
        }


class TemporalTrajectoryEngine:
    """
    Manages temporal trajectories for the cognitive field.
    
    Tracks:
    - Project evolution (how projects develop over time)
    - Behavioral drift (how agent behavior changes)
    - Topology evolution (how the field structure changes)
    - Strategic continuity (whether long-term goals are maintained)
    - Recurring attractors (patterns that repeat)
    - Failure loops (recurring failure patterns)
    - Successful structures (patterns that consistently work)
    """

    def __init__(self):
        self.trajectories: dict[str, Trajectory] = {}
        self._state_trajectories: dict[str, list[str]] = {}  # state_id -> [trajectory_ids]

    def create_trajectory(
        self, trajectory_type: str, initial_state: str = None,
    ) -> Trajectory:
        """Create a new trajectory."""
        traj_id = f"traj_{trajectory_type}_{int(time.time())}"
        traj = Trajectory(
            trajectory_id=traj_id,
            trajectory_type=trajectory_type,
        )
        if initial_state:
            traj.add_state(initial_state)
        self.trajectories[traj_id] = traj
        return traj

    def record_state(self, trajectory_id: str, state_id: str) -> None:
        """Record a state transition in a trajectory."""
        traj = self.trajectories.get(trajectory_id)
        if traj:
            traj.add_state(state_id)
            if state_id not in self._state_trajectories:
                self._state_trajectories[state_id] = []
            self._state_trajectories[state_id].append(trajectory_id)

    def update_coherence(self, trajectory_id: str, coherence: float) -> None:
        """Update a trajectory's coherence score."""
        traj = self.trajectories.get(trajectory_id)
        if traj:
            traj.coherence_score = max(0.0, min(1.0, coherence))

    def update_entropy_drift(self, trajectory_id: str, drift: float) -> None:
        """Update a trajectory's entropy drift."""
        traj = self.trajectories.get(trajectory_id)
        if traj:
            traj.entropy_drift = max(0.0, min(1.0, drift))

    def get_trajectory(self, trajectory_id: str) -> Optional[Trajectory]:
        return self.trajectories.get(trajectory_id)

    def get_trajectories_by_type(self, traj_type: str) -> list[Trajectory]:
        return [t for t in self.trajectories.values() if t.trajectory_type == traj_type]

    def get_stable_trajectories(self) -> list[Trajectory]:
        return sorted(
            [t for t in self.trajectories.values() if t.is_stable],
            key=lambda t: t.coherence_score,
            reverse=True,
        )

    def get_drifting_trajectories(self) -> list[Trajectory]:
        """Get trajectories with high entropy drift."""
        return sorted(
            [t for t in self.trajectories.values() if t.entropy_drift > 0.5],
            key=lambda t: t.entropy_drift,
            reverse=True,
        )

    @property
    def stats(self) -> dict:
        stable = sum(1 for t in self.trajectories.values() if t.is_stable)
        drifting = sum(1 for t in self.trajectories.values() if t.entropy_drift > 0.5)
        return {
            "total_trajectories": len(self.trajectories),
            "stable": stable,
            "drifting": drifting,
            "types": {
                ttype: sum(1 for t in self.trajectories.values() if t.trajectory_type == ttype)
                for ttype in set(t.trajectory_type for t in self.trajectories.values())
            },
        }
