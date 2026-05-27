"""
O-1-B7: EventAwareness
=======================
Observes runtime events:
TASK_STARTED, TASK_FAILED, OBSERVER_SPAWNED, ENTROPY_SPIKE,
REPAIR_TRIGGERED, ROUTING_UPDATED.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class EventType(str, Enum):
    """All observable event types."""
    # Task events
    TASK_RECEIVED = "task_received"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Observer events
    OBSERVER_SPAWNED = "observer_spawned"
    OBSERVER_SHUTDOWN = "observer_shutdown"
    OBSERVER_DEGRADED = "observer_degraded"
    OBSERVER_RECOVERED = "observer_recovered"

    # System events
    ENTROPY_SPIKE = "entropy_spike"
    REPAIR_TRIGGERED = "repair_triggered"
    REPAIR_COMPLETED = "repair_completed"
    ROUTING_UPDATED = "routing_updated"
    TOPOLOGY_CHANGED = "topology_changed"
    CONTINUITY_LOST = "continuity_lost"
    CONTINUITY_RESTORED = "continuity_restored"

    # Spawn events
    AGENT_SPAWNED = "agent_spawned"
    AGENT_TERMINATED = "agent_terminated"
    SPAWN_FAILED = "spawn_failed"


@dataclass
class ObserverEvent:
    """Single observer event."""
    event_type: str
    source: str
    timestamp: str
    data: dict[str, Any] = field(default_factory=dict)


class EventAwareness:
    """
    Event bus for observer system.
    
    Emits and tracks all runtime events. Subscribers can listen
    for specific event types.
    """

    def __init__(self, max_events: int = 500):
        self._lock = threading.RLock()
        self._events: list[ObserverEvent] = []
        self._max_events = max_events
        self._subscribers: dict[str, list[Callable]] = {}
        self._global_subscribers: list[Callable] = []

    def emit(
        self,
        event_type: EventType | str,
        source: str,
        data: dict[str, Any] | None = None,
    ) -> ObserverEvent:
        """Emit an event."""
        event = ObserverEvent(
            event_type=event_type.value if isinstance(event_type, EventType) else str(event_type),
            source=source,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data or {},
        )

        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]

        # Notify subscribers
        self._notify(event)
        return event

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to a specific event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable) -> None:
        """Subscribe to all events."""
        self._global_subscribers.append(callback)

    def get_events(
        self,
        event_type: str | None = None,
        source: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get recent events with optional filtering."""
        with self._lock:
            events = list(self._events)

        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if source:
            events = [e for e in events if e.source == source]

        return [
            {
                "event_type": e.event_type,
                "source": e.source,
                "timestamp": e.timestamp,
                "data": e.data,
            }
            for e in events[-limit:]
        ]

    def get_event_counts(self) -> dict[str, int]:
        """Get count of each event type."""
        with self._lock:
            counts: dict[str, int] = {}
            for e in self._events:
                counts[e.event_type] = counts.get(e.event_type, 0) + 1
            return counts

    def _notify(self, event: ObserverEvent) -> None:
        """Notify all relevant subscribers."""
        # Type-specific subscribers
        for cb in self._subscribers.get(event.event_type, []):
            try:
                cb(event)
            except Exception:
                pass
        # Global subscribers
        for cb in self._global_subscribers:
            try:
                cb(event)
            except Exception:
                pass
