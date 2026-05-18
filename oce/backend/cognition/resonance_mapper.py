"""
V3 Phase 6 — Resonance Mapper
Measures observer synchronization, symbolic convergence, topology agreement, execution coherence.

Core metrics: coherence_score, entropy_gradient, observer_alignment,
trajectory_stability, signal_density.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResonanceSnapshot:
    """A point-in-time measurement of field resonance."""
    timestamp: float
    coherence_score: float = 0.5
    entropy_gradient: float = 0.0
    observer_alignment: float = 0.5
    trajectory_stability: float = 0.5
    signal_density: float = 0.0

    @property
    def overall_resonance(self) -> float:
        """Overall resonance = positive metrics minus negative."""
        positive = (self.coherence_score + self.observer_alignment + self.trajectory_stability) / 3
        negative = (self.entropy_gradient + self.signal_density) / 2
        return max(0.0, min(1.0, positive - negative))


class ResonanceMapper:
    """
    Maps the resonance health of the cognitive field.
    
    Measures:
    - coherence_score: How coherent the field is (0-1)
    - entropy_gradient: Rate of entropy increase (0-1)
    - observer_alignment: How synchronized observers are (0-1)
    - trajectory_stability: How stable trajectories are (0-1)
    - signal_density: Signal convergence density (0-1)
    """

    def __init__(self, history_size: int = 1000):
        self.history: list[ResonanceSnapshot] = []
        self._history_size = history_size
        self._observer_phases: dict[str, float] = {}
        self._observer_coherences: dict[str, float] = {}

    def update_observer(self, observer_id: str, phase: float, coherence: float) -> None:
        """Register or update an observer's state."""
        self._observer_phases[observer_id] = phase % (2 * math.pi)
        self._observer_coherences[observer_id] = max(0.0, min(1.0, coherence))

    def remove_observer(self, observer_id: str) -> None:
        self._observer_phases.pop(observer_id, None)
        self._observer_coherences.pop(observer_id, None)

    def measure(
        self, field_coherence: float = 0.5, entropy_delta: float = 0.0,
        signal_count: int = 0, max_signals: int = 1000,
    ) -> ResonanceSnapshot:
        """
        Take a resonance measurement of the current field state.
        """
        # Observer alignment: circular variance of phases
        alignment = self._calc_observer_alignment()

        # Entropy gradient
        entropy_grad = min(1.0, entropy_delta)

        # Trajectory stability: based on coherence variance
        stability = self._calc_trajectory_stability()

        # Signal density
        density = min(1.0, signal_count / max(max_signals, 1))

        snap = ResonanceSnapshot(
            timestamp=time.time(),
            coherence_score=field_coherence,
            entropy_gradient=entropy_grad,
            observer_alignment=alignment,
            trajectory_stability=stability,
            signal_density=round(density, 4),
        )

        self.history.append(snap)
        if len(self.history) > self._history_size:
            self.history = self.history[-self._history_size:]

        return snap

    def _calc_observer_alignment(self) -> float:
        """Calculate observer alignment using circular variance."""
        if len(self._observer_phases) < 2:
            return 1.0

        phases = list(self._observer_phases.values())
        sin_sum = sum(math.sin(p) for p in phases)
        cos_sum = sum(math.cos(p) for p in phases)
        n = len(phases)
        r = math.sqrt(sin_sum**2 + cos_sum**2) / n
        return r

    def _calc_trajectory_stability(self) -> float:
        """Calculate trajectory stability from coherence variance."""
        if len(self._observer_coherences) < 2:
            return 1.0

        coherences = list(self._observer_coherences.values())
        mean_c = sum(coherences) / len(coherences)
        variance = sum((c - mean_c)**2 for c in coherences) / len(coherences)
        return max(0.0, 1.0 - math.sqrt(variance))

    def get_trend(self, metric: str, window: int = 10) -> float:
        """Get trend for a specific metric."""
        if len(self.history) < 2:
            return 0.0
        recent = self.history[-window:]
        if len(recent) < 2:
            return 0.0
        values = [getattr(s, metric, 0.0) for s in recent]
        return (values[-1] - values[0]) / len(values)

    @property
    def latest(self) -> Optional[ResonanceSnapshot]:
        return self.history[-1] if self.history else None

    @property
    def stats(self) -> dict:
        if not self.history:
            return {"total_measurements": 0, "avg_resonance": 0.5}
        return {
            "total_measurements": len(self.history),
            "avg_resonance": round(
                sum(s.overall_resonance for s in self.history) / len(self.history), 4
            ),
            "observer_count": len(self._observer_phases),
        }
