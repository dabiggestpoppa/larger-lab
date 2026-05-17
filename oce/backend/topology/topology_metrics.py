"""
V3 Phase 3 — Topology Metrics
Measures the health and efficiency of the cognitive field topology.

Metrics: coupling efficiency, resonance stability, observer drift,
topology coherence, overlap bandwidth efficiency.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from .collar_field import CollarFieldEngine
from .field_pressure import FieldPressureSystem, PressureReading


@dataclass
class TopologyHealth:
    """Complete topology health assessment."""
    timestamp: float
    coupling_efficiency: float        # 0-1
    resonance_stability: float         # 0-1
    observer_drift: float             # 0-1, lower is better
    topology_coherence: float         # 0-1
    overlap_bandwidth_efficiency: float  # 0-1
    overall_health: float             # 0-1

    @property
    def is_healthy(self) -> bool:
        return self.overall_health > 0.6

    @property
    def needs_attention(self) -> bool:
        return self.overall_health < 0.4

    def to_dict(self) -> dict:
        return {
            "coupling_efficiency": round(self.coupling_efficiency, 4),
            "resonance_stability": round(self.resonance_stability, 4),
            "observer_drift": round(self.observer_drift, 4),
            "topology_coherence": round(self.topology_coherence, 4),
            "overlap_bandwidth_efficiency": round(self.overlap_bandwidth_efficiency, 4),
            "overall_health": round(self.overall_health, 4),
            "is_healthy": self.is_healthy,
        }


class TopologyMetrics:
    """
    Measures topology health across the cognitive field.
    
    These metrics determine whether the field is self-organizing
    effectively or needs intervention.
    """

    def __init__(self):
        self._health_history: list[TopologyHealth] = []

    def measure(
        self, collar_engine: CollarFieldEngine,
        pressure_system: FieldPressureSystem,
        observer_count: int = 0,
    ) -> TopologyHealth:
        """
        Take a complete topology health measurement.
        """
        now = time.time()

        # Coupling efficiency: how well observers are connected
        collar_stats = collar_engine.stats
        if collar_stats["total_collars"] > 0:
            coupling = collar_stats["strong_collars"] / collar_stats["total_collars"]
        else:
            coupling = 1.0

        # Resonance stability: from pressure system
        pressure = pressure_system.latest
        if pressure:
            resonance = 1.0 - pressure.sync_instability
        else:
            resonance = 1.0

        # Observer drift: variance in collar strengths
        collars = list(collar_engine.collars.values())
        if len(collars) >= 2:
            strengths = [c.avg_resonance for c in collars]
            mean_s = sum(strengths) / len(strengths)
            variance = sum((s - mean_s) ** 2 for s in strengths) / len(strengths)
            drift = min(1.0, math.sqrt(variance))
        else:
            drift = 0.0

        # Topology coherence: from collar field
        coherence = collar_engine.get_field_coherence()

        # Overlap bandwidth efficiency
        if observer_count > 1:
            possible_connections = observer_count * (observer_count - 1) / 2
            actual_connections = sum(c.connection_count for c in collars) / 2
            overlap_eff = min(1.0, actual_connections / max(possible_connections, 1))
        else:
            overlap_eff = 1.0

        # Overall health
        overall = (
            coupling * 0.25 +
            resonance * 0.25 +
            (1.0 - drift) * 0.2 +
            coherence * 0.15 +
            overlap_eff * 0.15
        )

        health = TopologyHealth(
            timestamp=now,
            coupling_efficiency=coupling,
            resonance_stability=resonance,
            observer_drift=drift,
            topology_coherence=coherence,
            overlap_bandwidth_efficiency=overlap_eff,
            overall_health=round(overall, 4),
        )

        self._health_history.append(health)
        return health

    def get_trend(self, window: int = 10) -> float:
        """Get health trend (positive = improving)."""
        if len(self._health_history) < 2:
            return 0.0
        recent = self._health_history[-window:]
        if len(recent) < 2:
            return 0.0
        values = [h.overall_health for h in recent]
        return (values[-1] - values[0]) / len(values)

    @property
    def latest(self) -> Optional[TopologyHealth]:
        return self._health_history[-1] if self._health_history else None

    @property
    def stats(self) -> dict:
        if not self._health_history:
            return {"total_measurements": 0, "avg_health": 1.0, "healthy_ratio": 1.0}
        healthy = sum(1 for h in self._health_history if h.is_healthy)
        return {
            "total_measurements": len(self._health_history),
            "avg_health": round(
                sum(h.overall_health for h in self._health_history) / len(self._health_history), 4
            ),
            "healthy_ratio": round(healthy / len(self._health_history), 4),
            "trend": round(self.get_trend(), 4),
        }
