"""
O-1-B9: ObserverLifecycle
==========================
Heartbeat, healthcheck, recovery, state persistence, restart continuity.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable

from core.observer.observer_state import ObserverState, get_observer_state, HealthStatus
from core.observer.event_awareness import EventAwareness, EventType


class ObserverLifecycle:
    """
    Manages the observer lifecycle: heartbeat, health checks,
    recovery, and state persistence.
    """

    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        healthcheck_interval: float = 60.0,
    ):
        self.state = get_observer_state()
        self.event_bus = EventAwareness()
        self._heartbeat_interval = heartbeat_interval
        self._healthcheck_interval = healthcheck_interval
        self._running = False
        self._heartbeat_thread: threading.Thread | None = None
        self._healthcheck_thread: threading.Thread | None = None
        self._heartbeat_count = 0
        self._last_healthcheck: str | None = None
        self._recovery_callbacks: list[Callable] = []

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def heartbeat_count(self) -> int:
        return self._heartbeat_count

    def start(self) -> None:
        """Start the observer lifecycle."""
        if self._running:
            return
        self._running = True
        self.state.set_health(HealthStatus.HEALTHY)
        self.event_bus.emit(
            EventType.OBSERVER_SPAWNED,
            source="observer_lifecycle",
            data={"status": "started"},
        )

        # Start heartbeat
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

        # Start healthcheck
        self._healthcheck_thread = threading.Thread(
            target=self._healthcheck_loop, daemon=True
        )
        self._healthcheck_thread.start()

    def stop(self) -> None:
        """Stop the observer lifecycle."""
        self._running = False
        self.state.set_health(HealthStatus.HEALTHY)
        self.event_bus.emit(
            EventType.OBSERVER_SHUTDOWN,
            source="observer_lifecycle",
            data={"status": "stopped"},
        )

    def register_recovery(self, callback: Callable) -> None:
        """Register a recovery callback."""
        self._recovery_callbacks.append(callback)

    def get_status(self) -> dict[str, Any]:
        """Get lifecycle status."""
        return {
            "running": self._running,
            "heartbeat_count": self._heartbeat_count,
            "last_healthcheck": self._last_healthcheck,
            "health": self.state.get("observer_health"),
            "continuity_score": self.state.get("continuity_score"),
            "uptime_heartbeats": self._heartbeat_count,
        }

    def _heartbeat_loop(self) -> None:
        """Periodic heartbeat."""
        while self._running:
            try:
                self._heartbeat_count += 1
                self.state.set("last_heartbeat", datetime.now(timezone.utc).isoformat())
                time.sleep(self._heartbeat_interval)
            except Exception:
                time.sleep(1)

    def _healthcheck_loop(self) -> None:
        """Periodic health check."""
        while self._running:
            try:
                self._run_healthcheck()
                time.sleep(self._healthcheck_interval)
            except Exception:
                time.sleep(1)

    def _run_healthcheck(self) -> None:
        """Run a health check and update state."""
        self._last_healthcheck = datetime.now(timezone.utc).isoformat()

        health = self.state.get("observer_health")
        if health == HealthStatus.FAILED.value:
            self._attempt_recovery()
        elif health == HealthStatus.DEGRADED.value:
            self.event_bus.emit(
                EventType.OBSERVER_DEGRADED,
                source="observer_lifecycle",
                data={"health": health},
            )

    def _attempt_recovery(self) -> None:
        """Attempt to recover from failure."""
        self.state.set_health(HealthStatus.RECOVERING)
        self.event_bus.emit(
            EventType.OBSERVER_RECOVERED,
            source="observer_lifecycle",
            data={"action": "recovery_started"},
        )

        for cb in self._recovery_callbacks:
            try:
                cb()
            except Exception:
                pass

        self.state.set_health(HealthStatus.HEALTHY)
