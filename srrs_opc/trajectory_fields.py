"""
Trajectory Reconstruction Fields
==================================
Phase 5 (Updated): Continuity through reconstructable directional trajectories.

Continuity is NOT stored state.
Continuity is the ability to reconstruct coherent directional trajectories
from sparse overlap evidence.

Identity exists only to the degree that trajectory reconstruction remains viable.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict


class TrajectoryFragment:
    """A partial trajectory fragment maintained by an observer."""

    def __init__(self, observer_id: str, content: str, direction: str = ""):
        self.fragment_id = hashlib.sha256(
            f"{observer_id}:{content}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]
        self.observer_id = observer_id
        self.content = content
        self.direction = direction
        self.weight: float = 0.5
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_reinforced = self.created_at
        self.decay_rate: float = 0.01

    def reinforce(self):
        """Increase weight when fragment is confirmed by overlap."""
        self.weight = min(1.0, self.weight + 0.1)
        self.last_reinforced = datetime.now(timezone.utc).isoformat()

    def decay(self):
        """Natural decay of unused fragments."""
        self.weight = max(0.0, self.weight - self.decay_rate)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fragment_id": self.fragment_id,
            "observer_id": self.observer_id,
            "content": self.content,
            "direction": self.direction,
            "weight": round(self.weight, 3),
            "created_at": self.created_at,
            "last_reinforced": self.last_reinforced,
        }


class TrajectoryReconstructionField:
    """
    Reconstructs coherent directional trajectories from sparse overlap evidence.

    Key insight: Identity is reconstructable directional coherence, not persistent state.
    """

    def __init__(self, field_id: str):
        self.field_id = field_id
        self.fragments: Dict[str, TrajectoryFragment] = {}
        self.reconstruction_log: List[dict] = []

    def add_fragment(self, observer_id: str, content: str, direction: str = "") -> TrajectoryFragment:
        """Add a trajectory fragment from an observer."""
        fragment = TrajectoryFragment(observer_id, content, direction)
        self.fragments[fragment.fragment_id] = fragment
        return fragment

    def reconstruct(self, min_weight: float = 0.3) -> dict:
        """
        Reconstruct coherent trajectory from fragments.

        Returns directional continuity assessment.
        """
        active_fragments = [f for f in self.fragments.values() if f.weight >= min_weight]

        if not active_fragments:
            return {
                "viable": False,
                "reason": "no_active_fragments",
                "fragment_count": 0,
            }

        # Group by direction
        direction_groups: Dict[str, List[TrajectoryFragment]] = defaultdict(list)
        for f in active_fragments:
            direction_groups[f.direction].append(f)

        # Find dominant direction
        dominant_direction = max(direction_groups.keys(), key=lambda d: len(direction_groups[d]))
        dominant_fragments = direction_groups[dominant_direction]

        avg_weight = sum(f.weight for f in dominant_fragments) / len(dominant_fragments)

        result = {
            "viable": avg_weight > 0.5,
            "dominant_direction": dominant_direction,
            "fragment_count": len(active_fragments),
            "dominant_count": len(dominant_fragments),
            "avg_weight": round(avg_weight, 3),
            "directions": {d: len(fs) for d, fs in direction_groups.items()},
            "reconstructed_at": datetime.now(timezone.utc).isoformat(),
        }

        self.reconstruction_log.append(result)
        return result

    def apply_decay(self):
        """Apply natural decay to all fragments."""
        for fragment in self.fragments.values():
            fragment.decay()

    def prune_weak(self, threshold: float = 0.1) -> int:
        """Remove fragments below weight threshold. Returns count removed."""
        to_remove = [fid for fid, f in self.fragments.items() if f.weight < threshold]
        for fid in to_remove:
            del self.fragments[fid]
        return len(to_remove)

    def get_viability(self) -> Dict[str, Any]:
        """Get reconstruction viability assessment."""
        if not self.fragments:
            return {"viable": False, "fragment_count": 0}

        weights = [f.weight for f in self.fragments.values()]
        return {
            "viable": max(weights) > 0.5,
            "fragment_count": len(weights),
            "avg_weight": round(sum(weights) / len(weights), 3),
            "max_weight": round(max(weights), 3),
            "min_weight": round(min(weights), 3),
        }
