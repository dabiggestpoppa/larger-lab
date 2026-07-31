# Passive Awareness

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O7-B3: PassiveAwareness
========================
Low-power monitoring during idle periods.

Maintains background environmental awareness without constant
active orchestration. Tracks machine state, workflow evolution,
and topology drift at minimal resource cost.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("persistent_field.passive_awareness")


@dataclass
class AwarenessSignal:
    """A passive awareness signal."""
    signal_type: str
    source: str
    value: float
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class PassiveAwareness:
    """
    Low-power background environmental awareness.

    Tracks machine state, workflow evolution, active projects,
    topology drift, and entropy changes — all at minimal cost.
    """

    def __init__(self):
        self._signals: list[AwarenessSignal] = []
        self._last_scan: float = 0.0
        self._scan_interval: float = 60.0  # seconds between scans

    def scan(self) -> list[AwarenessSignal]:
        """Perform a passive awareness scan."""
        now = time.time()
        if now - self._last_scan < self._scan_interval:
            return []

        self._last_scan = now
        signals: list[AwarenessSignal] = []

        # Machine state signals
        signals.extend(self._scan_machine_state())

        # Workflow evolution signals
        signals.extend(self._scan_workflow_state())

        # Topology drift signals
        signals.extend(self._scan_topology_drift())

        self._signals.extend(signals)
        # Keep only last 1000 signals
        if len(self._signals) > 1000:
            self._signals = self._signals[-1000:]

        return signals

    def get_recent_signals(self, signal_type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent awareness signals."""
        signals = self._signals
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        return [s.__dict__ for s in signals[-limit:]]

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of current awareness state."""
        recent = self._signals[-100:] if self._signals else []
        by_type: dict[str, int] = {}
        avg_value = 0.0

        for s in recent:
            by_type[s.signal_type] = by_type.get(s.signal_type, 0) + 1
            avg_value += s.value

        if recent:
            avg_value /= len(recent)

        return {
            "total_signals": len(self._signals),
            "recent_signals": len(recent),
            "by_type": by_type,
            "avg_value": round(avg_value, 3),
            "last_scan": datetime.fromtimestamp(self._last_scan).isoformat() if self._last_scan else None,
        }

    def _scan_machine_state(self) -> list[AwarenessSignal]:
        """Scan machine state (CPU, memory, disk)."""
        signals = []
        try:
            import psutil
            signals.append(AwarenessSignal("cpu_usage", "system", psutil.cpu_percent() / 100.0))
            signals.append(AwarenessSignal("memory_usage", "system", psutil.virtual_memory().percent / 100.0))
            signals.append(AwarenessSignal("disk_usage", "system", psutil.disk_usage("/").percent / 100.0))
        except ImportError:
            signals.append(AwarenessSignal("cpu_usage", "system", 0.0, metadata={"note": "psutil not available"}))
        return signals

    def _scan_workflow_state(self) -> list[AwarenessSignal]:
        """Scan workflow evolution state."""
        return [
            AwarenessSignal("workflow_active", "system", 0.5, metadata={"note": "placeholder — integrate with O-4 workflow memory"}),
        ]

    def _scan_topology_drift(self) -> list[AwarenessSignal]:
        """Scan for topology drift."""
        return [
            AwarenessSignal("topology_stability", "system", 0.9, metadata={"note": "placeholder — integrate with O-1 observer runtime"}),
        ]

```

LINKS:
[[Ontology Core Summary]]
[[Citation Workflow]]
[[Minimal]]
[[Server]]
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
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
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
