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
