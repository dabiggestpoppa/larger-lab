"""
O7-B12: OperationalDriftDetector
==================================
Detect slow degradation patterns.

Monitors routing accuracy, response quality, resource usage.
Alerts on slow degradation before critical failure.
Historical comparison (week-over-week).
"""

from __future__ import annotations

import logging
import statistics
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("persistent_field.drift_detector")


@dataclass
class DriftMetric:
    """A drift metric reading."""
    metric_name: str
    value: float
    baseline: float = 0.0
    deviation: float = 0.0
    status: str = "normal"  # normal, warning, critical
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class OperationalDriftDetector:
    """
    Detect slow degradation patterns.

    Monitors: routing accuracy, response quality, resource usage.
    Alerts on slow degradation before critical failure.
    """

    WARNING_THRESHOLD = 0.15  # 15% deviation
    CRITICAL_THRESHOLD = 0.30  # 30% deviation

    def __init__(self):
        self._lock = threading.Lock()
        self._metrics: dict[str, list[DriftMetric]] = {}
        self._baselines: dict[str, float] = {}

    def record_metric(self, metric_name: str, value: float) -> DriftMetric:
        """Record a metric reading."""
        with self._lock:
            if metric_name not in self._metrics:
                self._metrics[metric_name] = []
                self._baselines[metric_name] = value

            baseline = self._baselines.get(metric_name, value)
            deviation = abs(value - baseline) / max(baseline, 0.001)

            if deviation >= self.CRITICAL_THRESHOLD:
                status = "critical"
            elif deviation >= self.WARNING_THRESHOLD:
                status = "warning"
            else:
                status = "normal"

            metric = DriftMetric(
                metric_name=metric_name,
                value=value,
                baseline=baseline,
                deviation=round(deviation, 4),
                status=status,
            )
            self._metrics[metric_name].append(metric)

            # Keep last 100 readings per metric
            if len(self._metrics[metric_name]) > 100:
                self._metrics[metric_name] = self._metrics[metric_name][-100:]

            if status != "normal":
                logger.warning(f"Drift detected: {metric_name} = {value} (deviation: {deviation:.1%})")

            return metric

    def update_baseline(self, metric_name: str, baseline: float) -> None:
        """Update the baseline for a metric."""
        with self._lock:
            self._baselines[metric_name] = baseline

    def get_drift_report(self) -> dict[str, Any]:
        """Get a comprehensive drift report."""
        with self._lock:
            report: dict[str, Any] = {
                "metrics": {},
                "alerts": [],
                "overall_status": "normal",
            }

            for metric_name, readings in self._metrics.items():
                if not readings:
                    continue

                recent = readings[-20:]
                values = [r.value for r in recent]
                deviations = [r.deviation for r in recent]

                metric_report = {
                    "current_value": values[-1] if values else 0,
                    "baseline": self._baselines.get(metric_name, 0),
                    "avg_deviation": round(statistics.mean(deviations), 4) if deviations else 0,
                    "max_deviation": round(max(deviations), 4) if deviations else 0,
                    "status": recent[-1].status if recent else "normal",
                    "readings_count": len(readings),
                }
                report["metrics"][metric_name] = metric_report

                if metric_report["status"] != "normal":
                    report["alerts"].append({
                        "metric": metric_name,
                        "status": metric_report["status"],
                        "deviation": metric_report["max_deviation"],
                    })

            if any(a["status"] == "critical" for a in report["alerts"]):
                report["overall_status"] = "critical"
            elif report["alerts"]:
                report["overall_status"] = "warning"

            report["timestamp"] = datetime.now(timezone.utc).isoformat()
            return report

    def get_trend(self, metric_name: str, window: int = 20) -> dict[str, Any]:
        """Get trend for a specific metric."""
        with self._lock:
            readings = self._metrics.get(metric_name, [])[-window:]
            if len(readings) < 2:
                return {"status": "insufficient_data"}

            values = [r.value for r in readings]
            return {
                "metric": metric_name,
                "direction": "improving" if values[-1] < values[0] else "degrading",
                "change_rate": round((values[-1] - values[0]) / max(values[0], 0.001), 4),
                "volatility": round(statistics.stdev(values), 4) if len(values) > 1 else 0,
                "samples": len(values),
            }
