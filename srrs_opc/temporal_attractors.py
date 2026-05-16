"""
Temporal Attractor Stabilization
==================================
Phase 5: Attractors constrain viable reconstruction paths.

Soft constraints, not deterministic state locks.
Maintain: directional continuity, reconstruction constraints,
repair preference fields, entropy boundaries.

Key insight: Stable continuity requires attractor structures,
not perfect memory. Attractors pull the system back toward
coherent trajectories.
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class TemporalAttractor:
    """
    An attractor that stabilizes a particular direction of continuity.
    
    Soft constraint: pulls nearby states toward the attractor basin.
    Not a hard lock: states can escape if evidence is strong enough.
    """

    def __init__(self, attractor_id: str, direction: str, strength: float = 0.5):
        self.attractor_id = attractor_id
        self.direction = direction
        self.strength = max(0.0, min(1.0, strength))
        self.basin_width: float = 0.3  # How wide the attractor basin is
        self.creation_time = datetime.now(timezone.utc).isoformat()
        self.last_activation = None
        self.activation_count = 0
        self.state_history: List[Dict[str, Any]] = []

    def compute_pull(self, state: dict) -> dict:
        """
        Compute the pull vector toward this attractor.
        
        Returns a dict with pull direction and magnitude.
        States within the basin get pulled toward the attractor.
        States outside the basin are unaffected.
        """
        if not self.state_history:
            return {"pull_magnitude": 0.0, "direction": self.direction}

        # Compute distance to attractor center
        recent = self.state_history[-10:]
        if not recent:
            return {"pull_magnitude": 0.0, "direction": self.direction}

        # Simple distance: fraction of matching keys
        center = recent[-1]
        all_keys = set(state.keys()) | set(center.keys())
        if not all_keys:
            return {"pull_magnitude": 0.0, "direction": self.direction}

        matches = sum(1 for k in all_keys if state.get(k) == center.get(k))
        distance = 1.0 - (matches / len(all_keys))

        # Pull is stronger when closer to the basin
        if distance < self.basin_width:
            pull = self.strength * (1.0 - distance / self.basin_width)
        else:
            pull = 0.0

        if pull > 0:
            self.last_activation = datetime.now(timezone.utc).isoformat()
            self.activation_count += 1

        return {
            "pull_magnitude": round(pull, 3),
            "direction": self.direction,
            "distance": round(distance, 3),
        }

    def apply_stabilization(self, state: dict, learning_rate: float = 0.1) -> dict:
        """
        Apply attractor stabilization to a state.
        
        Moves the state slightly toward the attractor basin.
        The learning_rate controls how strong the pull is.
        """
        pull = self.compute_pull(state)
        magnitude = pull["pull_magnitude"]

        if magnitude == 0:
            return state

        # Record state
        self.state_history.append({
            "state": state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pull_applied": magnitude,
        })

        # Keep history bounded
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]

        # Return stabilized state (simplified — real implementation would
        # use gradient descent on the attractor energy landscape)
        stabilized = dict(state)
        stabilized["_attractor_pull"] = magnitude
        stabilized["_attractor_direction"] = pull["direction"]

        return stabilized

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attractor_id": self.attractor_id,
            "direction": self.direction,
            "strength": self.strength,
            "basin_width": self.basin_width,
            "activation_count": self.activation_count,
            "last_activation": self.last_activation,
        }


class AttractorField:
    """
    A collection of temporal attractors that together stabilize
    the system's continuity.
    """

    def __init__(self):
        self.attractors: Dict[str, TemporalAttractor] = {}
        self.global_entropy_boundary: float = 0.8

    def add_attractor(self, attractor: TemporalAttractor):
        self.attractors[attractor.attractor_id] = attractor

    def stabilize(self, state: dict, learning_rate: float = 0.1) -> dict:
        """Apply all attractor stabilizations to a state."""
        stabilized = dict(state)
        total_pull = 0.0

        for attractor in self.attractors.values():
            pull = attractor.compute_pull(stabilized)
            if pull["pull_magnitude"] > 0:
                stabilized = attractor.apply_stabilization(stabilized, learning_rate)
                total_pull += pull["magnitude"]

        # Check entropy boundary
        if total_pull > self.global_entropy_boundary:
            # Too much pull — system is over-constrained
            stabilized["_over_constrained"] = True
            stabilized["_total_pull"] = round(total_pull, 3)

        return stabilized

    def get_field_report(self) -> Dict[str, Any]:
        """Get status of the attractor field."""
        if not self.attractors:
            return {"attractor_count": 0, "total_activations": 0}

        total_activations = sum(a.activation_count for a in self.attractors.values())
        avg_strength = sum(a.strength for a in self.attractors.values()) / len(self.attractors)

        return {
            "attractor_count": len(self.attractors),
            "total_activations": total_activations,
            "avg_strength": round(avg_strength, 3),
            "entropy_boundary": self.global_entropy_boundary,
            "attractors": {aid: a.to_dict() for aid, a in self.attractors.items()},
        }
