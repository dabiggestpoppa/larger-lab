"""
O7-B8: RuntimeHeartbeat
========================
Periodic health signals.

Maintains field continuity pulse — tracks observer health, topology
stability, entropy pressure, runtime load, and orchestration activity.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("persistent_field.heartbeat")


@dataclass
class HeartbeatSignal:
    """A single heartbeat signal."""
    field_state: str = "stable"
    entropy_level: float = 0.0
    observer_health: float = 1.0
    runtime_load: float = 0.0
    active_agents: int = 0
    continuity_score: float = 1.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class RuntimeHeartbeat:
    """
    Field continuity pulse.

    Tracks: observer health, topology stability, entropy pressure,
    runtime load, orchestration activity.
    """

    def __init__(self):
        self._history: list[HeartbeatSignal] = []
        self._last_heartbeat: float = 0.0
        self._interval: float = 30.0  # seconds

    def pulse(self, **kwargs: Any) -> dict[str, Any]:
        """Generate a heartbeat pulse."""
        now = time.time()
        self._last_heartbeat = now

        signal = HeartbeatSignal(**kwargs)
        self._history.append(signal)

        # Keep last 200 heartbeats (~10 minutes at 30s interval)
        if len(self._history) > 200:
            self._history = self._history[-200:]

        return {
            "field_state": signal.field_state,
            "entropy_level": signal.entropy_level,
            "observer_health": signal.observer_health,
            "runtime_load": signal.runtime_load,
            "active_agents": signal.active_agents,
            "continuity_score": signal.continuity_score,
            "timestamp": signal.timestamp,
        }

    def get_current(self) -> dict[str, Any]:
        """Get current heartbeat state."""
        if self._history:
            latest = self._history[-1]
            return {
                "field_state": latest.field_state,
                "entropy_level": latest.entropy_level,
                "observer_health": latest.observer_health,
                "runtime_load": latest.runtime_load,
                "active_agents": latest.active_agents,
                "continuity_score": latest.continuity_score,
                "timestamp": latest.timestamp,
            }
        return self.pulse()

    def get_trend(self, window: int = 10) -> dict[str, Any]:
        """Get heartbeat trend over recent window."""
        recent = self._history[-window:] if len(self._history) >= window else self._history
        if not recent:
            return {"status": "no_data"}

        entropy_trend = [s.entropy_level for s in recent]
        health_trend = [s.observer_health for s in recent]

        return {
            "entropy_avg": round(sum(entropy_trend) / len(entropy_trend), 3),
            "entropy_trend": "rising" if entropy_trend[-1] > entropy_trend[0] else "stable",
            "health_avg": round(sum(health_trend) / len(health_trend), 3),
            "health_trend": "declining" if health_trend[-1] < health_trend[0] else "stable",
            "samples": len(recent),
        }

    def is_healthy(self) -> bool:
        """Check if the field is healthy."""
        current = self.get_current()
        return (
            current["entropy_level"] < 0.7
            and current["observer_health"] > 0.5
            and current["continuity_score"] > 0.5
        )
