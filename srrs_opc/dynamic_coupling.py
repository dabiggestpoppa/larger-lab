"""
Dynamic Coupling Engine
========================
Phase 3: Adaptive edge weights between observer patches.

Patch relationships adapt based on:
- Interaction frequency (how often patches communicate)
- Repair density (how often repairs are needed between patches)
- Synchronization necessity (how critical the connection is)

Edge weights range from 0.0 (weak/disconnected) to 1.0 (strong/critical).
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict


class EdgeWeight:
    """Represents the coupling strength between two patches."""

    def __init__(self, patch_a: str, patch_b: str, initial_weight: float = 0.5):
        self.patch_a = patch_a
        self.patch_b = patch_b
        self.weight = initial_weight
        self.interaction_count = 0
        self.repair_count = 0
        self.last_interaction = None
        self.created_at = datetime.now(timezone.utc).isoformat()

    def record_interaction(self):
        """Record an interaction between these patches."""
        self.interaction_count += 1
        self.last_interaction = datetime.now(timezone.utc).isoformat()

    def record_repair(self):
        """Record a repair event between these patches."""
        self.repair_count += 1
        self.last_interaction = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_a": self.patch_a,
            "patch_b": self.patch_b,
            "weight": round(self.weight, 3),
            "interaction_count": self.interaction_count,
            "repair_count": self.repair_count,
            "last_interaction": self.last_interaction,
        }


class DynamicCouplingEngine:
    """
    Manages adaptive edge weights between patches.

    Weights adjust based on:
    - Interaction frequency → higher frequency = stronger coupling
    - Repair density → more repairs = weaker coupling (instability)
    - Time decay → unused edges weaken over time
    """

    def __init__(self, learning_rate: float = 0.1, decay_rate: float = 0.01,
                 min_weight: float = 0.1, max_weight: float = 1.0):
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.min_weight = min_weight
        self.max_weight = max_weight
        self._edges: Dict[Tuple[str, str], EdgeWeight] = {}
        self._patch_weights: Dict[str, float] = defaultdict(float)

    def _key(self, a: str, b: str) -> Tuple[str, str]:
        """Canonical edge key (alphabetical)."""
        return (min(a, b), max(a, b))

    def get_or_create_edge(self, patch_a: str, patch_b: str) -> EdgeWeight:
        """Get or create an edge between two patches."""
        key = self._key(patch_a, patch_b)
        if key not in self._edges:
            self._edges[key] = EdgeWeight(patch_a, patch_b)
        return self._edges[key]

    def record_interaction(self, patch_a: str, patch_b: str):
        """Record an interaction and update weight."""
        edge = self.get_or_create_edge(patch_a, patch_b)
        edge.record_interaction()

        # Strengthen coupling based on interaction frequency
        edge.weight = min(self.max_weight,
                          edge.weight + self.learning_rate * (1 - edge.weight))

    def record_repair(self, patch_a: str, patch_b: str):
        """Record a repair event and update weight."""
        edge = self.get_or_create_edge(patch_a, patch_b)
        edge.record_repair()

        # Weaken coupling — repairs indicate instability
        edge.weight = max(self.min_weight,
                          edge.weight - self.learning_rate * 0.5)

    def decay_unused(self, threshold_seconds: float = 300):
        """Decay edges that haven't been used recently."""
        now = time.time()
        for edge in self._edges.values():
            if edge.last_interaction:
                last = datetime.fromisoformat(edge.last_interaction)
                last_ts = last.timestamp()
                if now - last_ts > threshold_seconds:
                    edge.weight = max(self.min_weight,
                                      edge.weight - self.decay_rate)

    def get_edge_weight(self, patch_a: str, patch_b: str) -> float:
        """Get current edge weight between two patches."""
        key = self._key(patch_a, patch_b)
        if key in self._edges:
            return self._edges[key].weight
        return 0.0  # No edge = no coupling

    def get_strongest_edges(self, patch: str, limit: int = 5) -> list:
        """Get the strongest edges for a given patch."""
        edges = []
        for edge in self._edges.values():
            if edge.patch_a == patch or edge.patch_b == patch:
                edges.append(edge)
        edges.sort(key=lambda e: e.weight, reverse=True)
        return [e.to_dict() for e in edges[:limit]]

    def get_topology(self) -> Dict[str, Any]:
        """Get the full coupling topology."""
        return {
            "edges": {f"{e.patch_a}<->{e.patch_b}": e.to_dict()
                      for e in self._edges.values()},
            "total_edges": len(self._edges),
            "avg_weight": round(
                sum(e.weight for e in self._edges.values()) / max(len(self._edges), 1), 3
            ),
        }

    def get_clusters(self, threshold: float = 0.5) -> list:
        """
        Identify natural clusters based on edge weights.
        Patches with strong coupling form clusters.
        """
        # Simple clustering: group patches connected by strong edges
        clusters = []
        visited = set()

        for edge in sorted(self._edges.values(), key=lambda e: e.weight, reverse=True):
            if edge.weight < threshold:
                continue

            if edge.patch_a not in visited and edge.patch_b not in visited:
                clusters.append({
                    "patches": [edge.patch_a, edge.patch_b],
                    "coupling": edge.weight,
                })
                visited.add(edge.patch_a)
                visited.add(edge.patch_b)
            elif edge.patch_a in visited and edge.patch_b not in visited:
                for c in clusters:
                    if edge.patch_a in c["patches"]:
                        c["patches"].append(edge.patch_b)
                        c["coupling"] = min(c["coupling"], edge.weight)
                visited.add(edge.patch_b)
            elif edge.patch_b in visited and edge.patch_a not in visited:
                for c in clusters:
                    if edge.patch_b in c["patches"]:
                        c["patches"].append(edge.patch_a)
                        c["coupling"] = min(c["coupling"], edge.weight)
                visited.add(edge.patch_a)

        return clusters


if __name__ == "__main__":
    engine = DynamicCouplingEngine()

    # Simulate interactions
    engine.record_interaction("planner", "execution")
    engine.record_interaction("planner", "execution")
    engine.record_interaction("planner", "execution")
    engine.record_interaction("execution", "memory")
    engine.record_interaction("memory", "repair")
    engine.record_repair("planner", "execution")  # One repair

    print("Topology:", json.dumps(engine.get_topology(), indent=2))
    print("\nClusters:", json.dumps(engine.get_clusters(), indent=2))
    print("\nStrongest edges for 'planner':",
          json.dumps(engine.get_strongest_edges("planner"), indent=2))
