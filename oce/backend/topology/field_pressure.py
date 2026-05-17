"""
V3 Phase 3 — Field Pressure System
The nervous system of the cognitive field.

Monitors: observer overload, synchronization instability, entropy spikes,
coherence drift, trajectory fragmentation.

Triggers: repair, compression, topology shift, load redistribution.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional, Callable

from resonance import FieldStateManager, PressureTracker, PressureAlert
from .collar_field import CollarFieldEngine
from .bsp_projection import BSPProjectionEngine, TrajectoryProjection


@dataclass
class PressureReading:
    """A field pressure measurement."""
    timestamp: float
    observer_load: dict[str, float]     # observer_id -> load (0-1)
    sync_instability: float              # 0-1
    entropy_spike: float                 # 0-1
    coherence_drift: float               # 0-1
    trajectory_fragmentation: float      # 0-1
    overall_pressure: float              # 0-1

    @property
    def is_critical(self) -> bool:
        return self.overall_pressure > 0.8

    @property
    def needs_attention(self) -> bool:
        return self.overall_pressure > 0.5


class FieldPressureSystem:
    """
    The nervous system of the cognitive field.
    
    Continuously monitors field health and triggers responses:
    - Repair trigger when coherence drops
    - Compression when entropy spikes
    - Topology shift when load imbalances
    - Load redistribution when observers overload
    """

    def __init__(self):
        self._readings: list[PressureReading] = []
        self._max_readings = 1000
        self._callbacks: list[Callable] = []

    def register_callback(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def scan(
        self, field_manager: FieldStateManager,
        collar_engine: CollarFieldEngine,
        bsp_engine: BSPProjectionEngine = None,
        observer_states: dict = None,
    ) -> PressureReading:
        """
        Take a comprehensive pressure reading of the field.
        """
        now = time.time()

        # Observer load: signals per observer
        observer_load = {}
        for obs_id in field_manager.coherence_engine._observer_phases:
            signals = field_manager.signal_field.get_signals_by_source(obs_id)
            observer_load[obs_id] = min(1.0, len(signals) / 100.0)

        # Sync instability: phase variance across observers
        phases = list(field_manager.coherence_engine._observer_phases.values())
        if len(phases) >= 2:
            mean_phase = sum(phases) / len(phases)
            variance = sum((p - mean_phase) ** 2 for p in phases) / len(phases)
            sync_instability = min(1.0, variance / (math.pi ** 2))
        else:
            sync_instability = 0.0

        # Entropy spike: rate of entropy increase
        entropy_spike = 1.0 - field_manager.current_state.entropy_budget

        # Coherence drift: deviation from baseline
        baseline = field_manager.coherence_engine._baseline_coherence or 0.5
        current = field_manager.current_state.resonance_level
        coherence_drift = abs(current - baseline)

        # Trajectory fragmentation: from BSP projection
        if bsp_engine and observer_states:
            projection = bsp_engine.project(
                resonance_engine=field_manager.coherence_engine._observer_phases,  # Simplified
                attractor_memory=None,
                observer_states=observer_states,
            )
            trajectory_fragmentation = projection.entropy_pressure if projection else 0.0
        else:
            trajectory_fragmentation = 0.0

        # Overall pressure
        loads = list(observer_load.values()) if observer_load else [0.0]
        overall = (
            sum(loads) / len(loads) * 0.2 +
            sync_instability * 0.2 +
            entropy_spike * 0.2 +
            coherence_drift * 0.2 +
            trajectory_fragmentation * 0.2
        )

        reading = PressureReading(
            timestamp=now,
            observer_load=observer_load,
            sync_instability=round(sync_instability, 4),
            entropy_spike=round(entropy_spike, 4),
            coherence_drift=round(coherence_drift, 4),
            trajectory_fragmentation=round(trajectory_fragmentation, 4),
            overall_pressure=round(min(1.0, overall), 4),
        )

        self._readings.append(reading)
        if len(self._readings) > self._max_readings:
            self._readings = self._readings[-self._max_readings:]

        # Fire callbacks if critical
        if reading.is_critical:
            for cb in self._callbacks:
                cb(reading)

        return reading

    def get_trend(self, window: int = 10) -> float:
        """Get pressure trend (positive = increasing pressure)."""
        if len(self._readings) < 2:
            return 0.0
        recent = self._readings[-window:]
        if len(recent) < 2:
            return 0.0
        values = [r.overall_pressure for r in recent]
        return (values[-1] - values[0]) / len(values)

    @property
    def latest(self) -> Optional[PressureReading]:
        return self._readings[-1] if self._readings else None

    @property
    def stats(self) -> dict:
        if not self._readings:
            return {"total_readings": 0, "avg_pressure": 0.0, "critical_count": 0}
        critical = sum(1 for r in self._readings if r.is_critical)
        return {
            "total_readings": len(self._readings),
            "avg_pressure": round(sum(r.overall_pressure for r in self._readings) / len(self._readings), 4),
            "critical_count": critical,
            "trend": round(self.get_trend(), 4),
        }


import math  # Needed for pi
