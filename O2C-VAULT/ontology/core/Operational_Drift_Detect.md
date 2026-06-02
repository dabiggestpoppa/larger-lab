# Operational Drift Detect

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
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

```

LINKS:
[[Ontology Core Summary]]
[[Operational State 20260531]]
[[Cal]]
[[Citation Workflow]]
[[Patterns]]
[[Usage]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
