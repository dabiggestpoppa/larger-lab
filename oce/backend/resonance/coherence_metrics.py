"""
V3 Phase 1 — Coherence Metrics Engine
Measures resonance health of the cognitive field.

Six metrics tracked:
1. phase_alignment    — Observer synchronization
2. entropy_gradient   — Instability pressure
3. resonance_density  — Signal convergence
4. field_tension      — Constraint conflict
5. manifold_drift     — Projection divergence
6. attractor_stability — Continuity integrity
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Optional

from .signal_packet import SignalPacket, SignalField


@dataclass
class CoherenceSnapshot:
    """A point-in-time measurement of field coherence."""
    timestamp: float
    phase_alignment: float       # 0.0-1.0, higher = more synchronized
    entropy_gradient: float      # 0.0-1.0, higher = more instability
    resonance_density: float     # 0.0-1.0, higher = more convergence
    field_tension: float         # 0.0-1.0, higher = more conflict
    manifold_drift: float        # 0.0-1.0, higher = more divergence
    attractor_stability: float   # 0.0-1.0, higher = more stable

    @property
    def overall_coherence(self) -> float:
        """
        Overall coherence score.
        = (phase_alignment + resonance_density + attractor_stability) / 3
          - (entropy_gradient + field_tension + manifold_drift) / 3
        Clamped to 0.0-1.0
        """
        positive = (self.phase_alignment + self.resonance_density + self.attractor_stability) / 3
        negative = (self.entropy_gradient + self.field_tension + self.manifold_drift) / 3
        return max(0.0, min(1.0, positive - negative))

    @property
    def is_stable(self) -> bool:
        """Field is stable if overall coherence > 0.5."""
        return self.overall_coherence > 0.5

    @property
    def is_critical(self) -> bool:
        """Field is critical if overall coherence < 0.2."""
        return self.overall_coherence < 0.2

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "phase_alignment": round(self.phase_alignment, 4),
            "entropy_gradient": round(self.entropy_gradient, 4),
            "resonance_density": round(self.resonance_density, 4),
            "field_tension": round(self.field_tension, 4),
            "manifold_drift": round(self.manifold_drift, 4),
            "attractor_stability": round(self.attractor_stability, 4),
            "overall_coherence": round(self.overall_coherence, 4),
            "is_stable": self.is_stable,
            "is_critical": self.is_critical,
        }


class CoherenceEngine:
    """
    Core coherence measurement engine.
    Continuously monitors the cognitive field's resonance health.
    """

    def __init__(self, history_size: int = 1000):
        self.history: list[CoherenceSnapshot] = []
        self.history_size = history_size
        self._observer_phases: dict[str, float] = {}
        self._observer_coherences: dict[str, float] = {}
        self._baseline_coherence: Optional[float] = None

    def update_observer(self, observer_id: str, phase: float, coherence: float) -> None:
        """Register or update an observer's state."""
        self._observer_phases[observer_id] = phase % (2 * math.pi)
        self._observer_coherences[observer_id] = max(0.0, min(1.0, coherence))

    def remove_observer(self, observer_id: str) -> None:
        """Remove an observer from tracking."""
        self._observer_phases.pop(observer_id, None)
        self._observer_coherences.pop(observer_id, None)

    def measure(self, field: SignalField) -> CoherenceSnapshot:
        """
        Take a coherence snapshot of the current field state.
        
        Computes all 6 metrics from the signal field and observer states.
        """
        signals = field.signals
        now = time.time()

        # 1. Phase Alignment — how synchronized are observers?
        phase_alignment = self._calc_phase_alignment()

        # 2. Entropy Gradient — how much instability pressure?
        entropy_gradient = self._calc_entropy_gradient(signals)

        # 3. Resonance Density — how convergent are signals?
        resonance_density = self._calc_resonance_density(signals)

        # 4. Field Tension — how much constraint conflict?
        field_tension = self._calc_field_tension(signals)

        # 5. Manifold Drift — how much projection divergence?
        manifold_drift = self._calc_manifold_drift()

        # 6. Attractor Stability — how stable is continuity?
        attractor_stability = self._calc_attractor_stability(field)

        snapshot = CoherenceSnapshot(
            timestamp=now,
            phase_alignment=phase_alignment,
            entropy_gradient=entropy_gradient,
            resonance_density=resonance_density,
            field_tension=field_tension,
            manifold_drift=manifold_drift,
            attractor_stability=attractor_stability,
        )

        self.history.append(snapshot)
        if len(self.history) > self.history_size:
            self.history = self.history[-self.history_size:]

        if self._baseline_coherence is None:
            self._baseline_coherence = snapshot.overall_coherence

        return snapshot

    def _calc_phase_alignment(self) -> float:
        """
        Phase alignment = how close observer phases are to each other.
        Uses circular variance: 1.0 = all aligned, 0.0 = completely scattered.
        """
        if len(self._observer_phases) < 2:
            return 1.0
        
        phases = list(self._observer_phases.values())
        # Circular mean resultant length
        sin_sum = sum(math.sin(p) for p in phases)
        cos_sum = sum(math.cos(p) for p in phases)
        n = len(phases)
        r = math.sqrt(sin_sum**2 + cos_sum**2) / n
        return r

    def _calc_entropy_gradient(self, signals: list[SignalPacket]) -> float:
        """
        Entropy gradient = rate of entropy increase.
        High = field is becoming more disordered.
        """
        if not signals:
            return 0.0
        total_entropy = sum(s.entropy_delta for s in signals)
        # Normalize: >1.0 entropy per signal = high gradient
        return min(1.0, total_entropy / max(len(signals), 1))

    def _calc_resonance_density(self, signals: list[SignalPacket]) -> float:
        """
        Resonance density = proportion of signals that are resonant.
        High = signals are converging, field is coherent.
        """
        if not signals:
            return 1.0
        resonant = sum(1 for s in signals if s.is_resonant)
        return resonant / len(signals)

    def _calc_field_tension(self, signals: list[SignalPacket]) -> float:
        """
        Field tension = conflict between signals targeting same boundaries.
        High = multiple signals pushing boundaries in different directions.
        """
        if not signals:
            return 0.0
        
        boundary_pressures: dict[str, list[float]] = {}
        for s in signals:
            for tag in s.boundary_tags:
                if tag not in boundary_pressures:
                    boundary_pressures[tag] = []
                boundary_pressures[tag].append(s.signal_pressure)
        
        if not boundary_pressures:
            return 0.0
        
        # Tension = variance of pressures per boundary
        tensions = []
        for pressures in boundary_pressures.values():
            if len(pressures) > 1:
                mean_p = sum(pressures) / len(pressures)
                variance = sum((p - mean_p)**2 for p in pressures) / len(pressures)
                tensions.append(min(1.0, variance))
        
        return sum(tensions) / max(len(tensions), 1)

    def _calc_manifold_drift(self) -> float:
        """
        Manifold drift = how much observer coherences diverge from baseline.
        High = observers are losing shared understanding.
        """
        if not self._observer_coherences:
            return 0.0
        
        coherences = list(self._observer_coherences.values())
        if len(coherences) < 2:
            return 0.0
        
        mean_c = sum(coherences) / len(coherences)
        variance = sum((c - mean_c)**2 for c in coherences) / len(coherences)
        return min(1.0, math.sqrt(variance))

    def _calc_attractor_stability(self, field: SignalField) -> float:
        """
        Attractor stability = how stable the field's coherence is over time.
        Compares current coherence to baseline.
        """
        if self._baseline_coherence is None or not field.signals:
            return 1.0
        
        current = field.field_coherence
        drift = abs(current - self._baseline_coherence)
        return max(0.0, 1.0 - drift)

    def get_trend(self, metric: str, window: int = 10) -> float:
        """
        Get trend for a specific metric over recent history.
        Returns positive (improving) or negative (degrading) value.
        """
        if len(self.history) < 2:
            return 0.0
        
        recent = self.history[-window:]
        if len(recent) < 2:
            return 0.0
        
        values = [getattr(s, metric, 0.0) for s in recent]
        # Simple linear trend: (last - first) / count
        return (values[-1] - values[0]) / len(values)

    def get_drift_alerts(self, threshold: float = 0.3) -> list[dict]:
        """
        Check for metrics that have drifted beyond threshold.
        Returns list of alerts for metrics needing attention.
        """
        if not self.history:
            return []
        
        latest = self.history[-1]
        alerts = []
        
        checks = [
            ("phase_alignment", latest.phase_alignment, False),  # False = alert if LOW
            ("entropy_gradient", latest.entropy_gradient, True),  # True = alert if HIGH
            ("resonance_density", latest.resonance_density, False),
            ("field_tension", latest.field_tension, True),
            ("manifold_drift", latest.manifold_drift, True),
            ("attractor_stability", latest.attractor_stability, False),
        ]
        
        for name, value, alert_if_high in checks:
            if alert_if_high and value > threshold:
                alerts.append({
                    "metric": name,
                    "value": round(value, 4),
                    "severity": "critical" if value > 0.7 else "warning",
                    "direction": "high",
                })
            elif not alert_if_high and value < (1.0 - threshold):
                alerts.append({
                    "metric": name,
                    "value": round(value, 4),
                    "severity": "critical" if value < 0.3 else "warning",
                    "direction": "low",
                })
        
        return alerts

    @property
    def latest(self) -> Optional[CoherenceSnapshot]:
        """Get the most recent coherence snapshot."""
        return self.history[-1] if self.history else None

    @property
    def observer_count(self) -> int:
        return len(self._observer_phases)

    def __repr__(self) -> str:
        if self.latest:
            return f"CoherenceEngine(coherence={self.latest.overall_coherence:.2f}, observers={self.observer_count})"
        return "CoherenceEngine(empty)"
