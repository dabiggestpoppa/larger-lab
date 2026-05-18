"""
V3 Phase 9 — Monitoring Dashboard
Real-time system health metrics for the V3 cognitive field system.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HealthMetric:
    """A single health metric reading."""
    metric_id: str
    name: str
    value: float
    unit: str = ""
    threshold_warning: float = 0.7
    threshold_critical: float = 0.9
    timestamp: float = field(default_factory=time.time)

    @property
    def status(self) -> str:
        if self.value >= self.threshold_critical:
            return "critical"
        if self.value >= self.threshold_warning:
            return "warning"
        return "healthy"

    @property
    def is_healthy(self) -> bool:
        return self.value < self.threshold_warning


@dataclass
class SystemHealth:
    """Aggregated system health snapshot."""
    overall_score: float  # 0-1
    field_coherence: float
    observer_health: float
    entropy_budget: float
    topology_stability: float
    timestamp: float = field(default_factory=time.time)

    @property
    def status(self) -> str:
        if self.overall_score >= 0.8:
            return "healthy"
        if self.overall_score >= 0.5:
            return "degraded"
        return "critical"

    @property
    def needs_attention(self) -> bool:
        return self.overall_score < 0.5


class MonitoringDashboard:
    """
    Real-time system health monitoring.
    
    Tracks:
    - Field coherence (signal alignment across observers)
    - Observer health (are all observers functioning?)
    - Entropy budget (how much entropy headroom remains)
    - Topology stability (is the network structure stable?)
    """

    def __init__(self):
        self._metrics: list[HealthMetric] = []
        self._health_snapshots: list[SystemHealth] = []

    def record_metric(self, name: str, value: float, unit: str = "",
                      warning: float = 0.7, critical: float = 0.9) -> HealthMetric:
        """Record a health metric."""
        metric = HealthMetric(
            metric_id=f"metric_{int(time.time() * 1000)}",
            name=name, value=value, unit=unit,
            threshold_warning=warning, threshold_critical=critical,
        )
        self._metrics.append(metric)
        return metric

    def get_latest_metric(self, name: str) -> Optional[HealthMetric]:
        """Get the most recent reading for a metric."""
        for m in reversed(self._metrics):
            if m.name == name:
                return m
        return None

    def get_metrics_by_status(self, status: str) -> list[HealthMetric]:
        """Get all metrics matching a status (healthy/warning/critical)."""
        return [m for m in self._metrics if m.status == status]

    def record_health_snapshot(self, field_coherence: float, observer_health: float,
                                entropy_budget: float, topology_stability: float) -> SystemHealth:
        """Record a full system health snapshot."""
        overall = (field_coherence + observer_health + entropy_budget + topology_stability) / 4
        snapshot = SystemHealth(
            overall_score=round(overall, 4),
            field_coherence=field_coherence,
            observer_health=observer_health,
            entropy_budget=entropy_budget,
            topology_stability=topology_stability,
        )
        self._health_snapshots.append(snapshot)
        return snapshot

    def get_current_health(self) -> Optional[SystemHealth]:
        """Get the most recent health snapshot."""
        if not self._health_snapshots:
            return None
        return self._health_snapshots[-1]

    def get_health_trend(self, window: int = 10) -> float:
        """Get health trend (positive = improving)."""
        if len(self._health_snapshots) < 2:
            return 0.0
        recent = self._health_snapshots[-window:]
        if len(recent) < 2:
            return 0.0
        return (recent[-1].overall_score - recent[0].overall_score) / len(recent)

    @property
    def stats(self) -> dict:
        current = self.get_current_health()
        return {
            "total_metrics_recorded": len(self._metrics),
            "total_snapshots": len(self._health_snapshots),
            "current_health": current.overall_score if current else None,
            "current_status": current.status if current else "unknown",
            "trend": round(self.get_health_trend(), 4),
        }
