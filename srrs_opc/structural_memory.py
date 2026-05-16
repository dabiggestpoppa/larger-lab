"""
Structural Memory Fields
==========================
Phase 7: Memory hierarchy — deepest memory exists in topology, not logs.

Memory priority:
1. Attractor memory (highest)
2. Topology memory (highest)
3. Repair memory (highest)
4. Trajectory memory (medium)
5. Event replay (medium)
6. Prompt/context (lowest)
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum


class MemoryLayer(str, Enum):
    ATTRACTOR = "attractor"
    TOPOLOGY = "topology"
    REPAIR = "repair"
    TRAJECTORY = "trajectory"
    EVENT = "event"
    CONTEXT = "context"


class StructuralMemoryEntry:
    def __init__(self, layer: MemoryLayer, key: str, data: Any,
                 weight: float = 1.0, source: str = "system"):
        self.layer = layer
        self.key = key
        self.data = data
        self.weight = weight
        self.source = source
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.access_count = 0

    def to_dict(self) -> dict:
        return {
            "layer": self.layer.value,
            "key": self.key,
            "data": self.data,
            "weight": round(self.weight, 3),
            "access_count": self.access_count,
            "created_at": self.created_at,
        }


class StructuralMemoryFields:
    """
    Structural memory that persists through topology, not event replay.
    Continuity survives even if event history is deleted.
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, StructuralMemoryEntry]] = {
            layer.value: {} for layer in MemoryLayer
        }

    def store(self, layer: MemoryLayer, key: str, data: Any,
              weight: float = 1.0, source: str = "system"):
        entry = StructuralMemoryEntry(layer, key, data, weight, source)
        self._store[layer.value][key] = entry

    def retrieve(self, layer: MemoryLayer, key: str) -> Optional[dict]:
        entry = self._store[layer.value].get(key)
        if entry:
            entry.access_count += 1
            return entry.to_dict()
        return None

    def get_layer(self, layer: MemoryLayer) -> List[dict]:
        return [e.to_dict() for e in self._store[layer.value].values()]

    def compress(self, layer: MemoryLayer, max_entries: int = 50):
        entries = list(self._store[layer.value].values())
        if len(entries) <= max_entries:
            return
        entries.sort(key=lambda e: e.weight * (1 + e.access_count * 0.1), reverse=True)
        self._store[layer.value] = {e.key: e for e in entries[:max_entries]}

    def get_stats(self) -> dict:
        stats = {}
        for layer in MemoryLayer:
            entries = list(self._store[layer.value].values())
            if entries:
                weights = [e.weight for e in entries]
                stats[layer.value] = {
                    "entries": len(entries),
                    "avg_weight": round(sum(weights) / len(weights), 3),
                    "total_accesses": sum(e.access_count for e in entries),
                }
            else:
                stats[layer.value] = {"entries": 0}
        return stats

    def persist_without_events(self) -> dict:
        """Verify continuity persists without event replay."""
        return {
            "attractors": self.get_layer(MemoryLayer.ATTRACTOR),
            "topology": self.get_layer(MemoryLayer.TOPOLOGY),
            "repair_policies": self.get_layer(MemoryLayer.REPAIR),
            "trajectories": self.get_layer(MemoryLayer.TRAJECTORY),
        }


if __name__ == "__main__":
    mem = StructuralMemoryFields()
    mem.store(MemoryLayer.ATTRACTOR, "convergence_alpha",
              {"position": [0.7, 0.3, 0.5], "stability": 0.85}, weight=0.9)
    mem.store(MemoryLayer.TOPOLOGY, "coupling_graph",
              {"edges": {"planner-execution": 0.8}}, weight=0.85)
    mem.store(MemoryLayer.REPAIR, "local_first_policy",
              {"strategy": "local_before_global", "success_rate": 0.92}, weight=0.8)

    print("Stats:", json.dumps(mem.get_stats(), indent=2))
    persisted = mem.persist_without_events()
    print(f"Persisted without events: {len(persisted)} layers")
