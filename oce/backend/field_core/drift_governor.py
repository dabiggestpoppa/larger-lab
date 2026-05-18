"""
V3 Phase 9 — Drift Governor
Measures divergence and triggers reconstruction.
Monitors field drift and initiates coherence restoration when needed.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DriftMetrics:
    """Drift measurement for a field element."""
    metrics_id: str
    element_id: str
    drift_score: float  # 0-1, how far from expected state
    divergence_rate: float  # rate of change
    timestamp: float = field(default_factory=time.time)

    @property
    def is_drifting(self) -> bool:
        return self.drift_score > 0.5

    @property
    def is_critical(self) -> bool:
        return self.drift_score > 0.8


class DriftGovernor:
    """
    Measures divergence and triggers reconstruction.
    
    Monitors field drift — the tendency of field elements to diverge
    from their expected states. When drift exceeds thresholds, triggers
    coherence restoration.
    """

    def __init__(self):
        self._metrics: list[DriftMetrics] = []
        self._thresholds: dict[str, float] = {}
        self._reconstruction_triggers: list[dict] = []

    def set_threshold(self, element_id: str, threshold: float) -> None:
        """Set drift threshold for an element."""
        self._thresholds[element_id] = threshold

    def measure_drift(self, element_id: str, expected_state: dict,
                       actual_state: dict) -> DriftMetrics:
        """Measure drift between expected and actual state."""
        # Compute drift as fraction of mismatched keys
        if not expected_state:
            drift_score = 0.0
        else:
            mismatches = sum(
                1 for k, v in expected_state.items()
                if k not in actual_state or actual_state[k] != v
            )
            drift_score = mismatches / len(expected_state)

        # Compute divergence rate from previous measurement
        prev = self._get_latest_metrics(element_id)
        divergence_rate = 0.0
        if prev:
            time_delta = time.time() - prev.timestamp
            if time_delta > 0:
                divergence_rate = abs(drift_score - prev.drift_score) / time_delta

        metrics = DriftMetrics(
            metrics_id=f"drift_{int(time.time() * 1000)}",
            element_id=element_id,
            drift_score=round(drift_score, 4),
            divergence_rate=round(divergence_rate, 4),
        )
        self._metrics.append(metrics)

        # Check if reconstruction should be triggered
        threshold = self._thresholds.get(element_id, 0.5)
        if metrics.drift_score > threshold:
            self._trigger_reconstruction(element_id, metrics)

        return metrics

    def _get_latest_metrics(self, element_id: str) -> Optional[DriftMetrics]:
        for m in reversed(self._metrics):
            if m.element_id == element_id:
                return m
        return None

    def _trigger_reconstruction(self, element_id: str, metrics: DriftMetrics) -> None:
        """Trigger reconstruction for a drifting element."""
        self._reconstruction_triggers.append({
            "element_id": element_id,
            "drift_score": metrics.drift_score,
            "timestamp": time.time(),
        })

    def get_drifting_elements(self) -> list[str]:
        """Get IDs of elements that are currently drifting."""
        latest: dict[str, DriftMetrics] = {}
        for m in self._metrics:
            latest[m.element_id] = m
        return [eid for eid, m in latest.items() if m.is_drifting]

    def get_critical_elements(self) -> list[str]:
        """Get IDs of elements with critical drift."""
        latest: dict[str, DriftMetrics] = {}
        for m in self._metrics:
            latest[m.element_id] = m
        return [eid for eid, m in latest.items() if m.is_critical]

    def get_drift_trend(self, element_id: str, window: int = 10) -> float:
        """Get drift trend for an element (positive = worsening)."""
        element_metrics = [m for m in self._metrics if m.element_id == element_id]
        if len(element_metrics) < 2:
            return 0.0
        recent = element_metrics[-window:]
        if len(recent) < 2:
            return 0.0
        return (recent[-1].drift_score - recent[0].drift_score) / len(recent)

    @property
    def stats(self) -> dict:
        drifting = len(self.get_drifting_elements())
        critical = len(self.get_critical_elements())
        return {
            "total_measurements": len(self._metrics),
            "drifting_elements": drifting,
            "critical_elements": critical,
            "reconstruction_triggers": len(self._reconstruction_triggers),
            "monitored_elements": len(self._thresholds),
        }
