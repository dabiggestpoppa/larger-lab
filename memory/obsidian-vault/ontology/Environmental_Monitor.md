# Environmental Monitor

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O7-B4: EnvironmentalMonitor
============================
Track system resources, network, disk.

Observes the machine + workflow ecosystem for situational awareness.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("persistent_field.environmental_monitor")


@dataclass
class EnvironmentReading:
    """A single environment reading."""
    metric: str
    value: float
    unit: str
    status: str = "normal"  # normal, warning, critical
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class EnvironmentalMonitor:
    """
    Monitor machine and workflow ecosystem.

    Tracks: repository changes, runtime health, resource pressure,
    process instability, orchestration saturation.
    """

    WARNING_THRESHOLD = 0.75
    CRITICAL_THRESHOLD = 0.90

    def __init__(self):
        self._readings: list[EnvironmentReading] = []
        self._last_check: float = 0.0

    def check_environment(self) -> dict[str, Any]:
        """Perform a full environment check."""
        now = time.time()
        self._last_check = now

        readings = []
        readings.extend(self._check_resources())
        readings.extend(self._check_disk())
        readings.extend(self._check_processes())

        self._readings.extend(readings)
        # Keep last 500 readings
        if len(self._readings) > 500:
            self._readings = self._readings[-500:]

        return self._build_report(readings)

    def get_current_state(self) -> dict[str, Any]:
        """Get current environment state."""
        if not self._readings:
            return self.check_environment()
        return self._build_report(self._readings[-20:])

    def _check_resources(self) -> list[EnvironmentReading]:
        """Check system resources."""
        readings = []
        try:
            import psutil
            cpu = psutil.cpu_percent() / 100.0
            mem = psutil.virtual_memory().percent / 100.0
            readings.append(self._make_reading("cpu_percent", cpu, "%"))
            readings.append(self._make_reading("memory_percent", mem, "%"))
        except ImportError:
            readings.append(EnvironmentReading("cpu_percent", 0.0, "%", "warning", datetime.now(timezone.utc).isoformat()))
        return readings

    def _check_disk(self) -> list[EnvironmentReading]:
        """Check disk usage."""
        readings = []
        try:
            import psutil
            disk = psutil.disk_usage("/").percent / 100.0
            readings.append(self._make_reading("disk_percent", disk, "%"))
        except ImportError:
            readings.append(EnvironmentReading("disk_percent", 0.0, "%", "warning", datetime.now(timezone.utc).isoformat()))
        return readings

    def _check_processes(self) -> list[EnvironmentReading]:
        """Check process health."""
        readings = []
        try:
            import psutil
            process_count = len(psutil.pids())
            readings.append(self._make_reading("process_count", min(process_count / 500.0, 1.0), "count", metadata={"raw_count": process_count}))
        except ImportError:
            readings.append(EnvironmentReading("process_count", 0.0, "count", "warning", datetime.now(timezone.utc).isoformat()))
        return readings

    def _make_reading(self, metric: str, value: float, unit: str, status: str = "", metadata: dict | None = None) -> EnvironmentReading:
        """Create a reading with automatic status."""
        if not status:
            if value >= self.CRITICAL_THRESHOLD:
                status = "critical"
            elif value >= self.WARNING_THRESHOLD:
                status = "warning"
            else:
                status = "normal"
        reading = EnvironmentReading(metric, value, unit, status)
        if metadata:
            reading.metadata = metadata  # type: ignore
        return reading

    def _build_report(self, readings: list[EnvironmentReading]) -> dict[str, Any]:
        """Build an environment report."""
        metrics: dict[str, float] = {}
        alerts: list[dict[str, Any]] = []

        for r in readings:
            metrics[r.metric] = r.value
            if r.status in ("warning", "critical"):
                alerts.append({"metric": r.metric, "value": r.value, "status": r.status})

        overall = "normal"
        if any(a["status"] == "critical" for a in alerts):
            overall = "critical"
        elif alerts:
            overall = "warning"

        return {
            "overall_status": overall,
            "metrics": metrics,
            "alerts": alerts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

```

LINKS:
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
[[Sources]]
[[System]]
[[Usage]]
[[Workflow]]
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
[[Memory]]
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
[[Operational Drift Detect]]
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
