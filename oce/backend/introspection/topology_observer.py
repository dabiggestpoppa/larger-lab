"""
V3 Phase 6 — Topology Observer
Monitors coupling graph structure in real-time.

The system can observe its own topology: which observers are connected,
how strong the connections are, and how the structure changes over time.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional

from topology.collar_field import CollarFieldEngine


@dataclass
class TopologySnapshot:
    """A snapshot of the field's topology at a point in time."""
    snapshot_id: str
    timestamp: float
    observer_count: int = 0
    connection_count: int = 0
    strong_connections: int = 0
    weak_connections: int = 0
    isolated_observers: int = 0
    topology_density: float = 0.0   # 0-1, how connected the field is
    health_score: float = 1.0

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "observers": self.observer_count,
            "connections": self.connection_count,
            "strong": self.strong_connections,
            "weak": self.weak_connections,
            "isolated": self.isolated_observers,
            "density": round(self.topology_density, 4),
            "health": round(self.health_score, 4),
        }


class TopologyObserver:
    """
    Observes the cognitive field's topology in real-time.
    
    Tracks:
    - Which observers are connected
    - Connection strengths
    - Topology density
    - Isolated observers
    - Topology health
    """

    def __init__(self, collar_engine: CollarFieldEngine = None):
        self.collar_engine = collar_engine or CollarFieldEngine()
        self._snapshots: list[TopologySnapshot] = []

    def observe(self) -> TopologySnapshot:
        """Take a topology snapshot of the current field."""
        collars = self.collar_engine.collars
        observers = set()
        connections = 0
        strong = 0
        weak = 0
        isolated = 0

        for obs_id, collar in collars.items():
            observers.add(obs_id)
            if collar.connection_count == 0:
                isolated += 1
            for target_id, resonance in collar.resonance_map.items():
                observers.add(target_id)
                connections += 1
                if resonance > 0.6:
                    strong += 1
                else:
                    weak += 1

        n = len(observers)
        max_connections = n * (n - 1) / 2 if n > 1 else 1
        density = connections / max_connections if max_connections > 0 else 0

        health = 1.0
        health -= isolated * 0.1
        health -= weak * 0.02
        health = max(0.0, min(1.0, health))

        snap = TopologySnapshot(
            snapshot_id=f"topo_{int(time.time())}",
            timestamp=time.time(),
            observer_count=n,
            connection_count=connections,
            strong_connections=strong,
            weak_connections=weak,
            isolated_observers=isolated,
            topology_density=round(density, 4),
            health_score=round(health, 4),
        )

        self._snapshots.append(snap)
        return snap

    def get_topology_report(self) -> dict:
        """Generate a comprehensive topology report."""
        if not self._snapshots:
            return {"status": "no_data"}

        latest = self._snapshots[-1]
        return {
            "current": latest.to_dict(),
            "history_size": len(self._snapshots),
            "avg_health": round(
                sum(s.health_score for s in self._snapshots) / len(self._snapshots), 4
            ),
        }

    @property
    def stats(self) -> dict:
        return self.get_topology_report()
