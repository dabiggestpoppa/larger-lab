"""
4_instrumentation.instrumentation_bus
======================================
Central event bus for all field instrumentation — pub/sub system
for metric updates, alerts, heartbeats, state changes, and errors.

Thread-safe ring buffer with configurable retention.
"""

import logging
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.instrumentation_bus")

# ── Data Models ──────────────────────────────────────────────────

class BusEvent(BaseModel):
    """A single instrumentation bus event."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    event_type: str  # metric_update, alert, heartbeat, state_change, error
    source: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Dict[str, Any] = Field(default_factory=dict)


class EventTypeStats(BaseModel):
    """Statistics for a single event type."""
    event_type: str
    count: int = 0
    last_event_time: str = ""
    first_event_time: str = ""


class InstrumentationBusConfig(BaseModel):
    """Configuration for instrumentation_bus."""
    enabled: bool = True
    max_events: int = 10000
    flush_interval_sec: float = 5.0
    event_retention_hours: float = 24.0


# ── Instrumentation Bus ──────────────────────────────────────────

class InstrumentationBusModule:
    """
    Central pub/sub event bus for field instrumentation.

    Supports event types: metric_update, alert, heartbeat, state_change, error.
    Thread-safe ring buffer with configurable max size and retention.
    """

    def __init__(self):
        self.config = InstrumentationBusConfig()
        self.running = False
        self._events: deque[BusEvent] = deque(maxlen=self.config.max_events)
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._global_handlers: List[Callable] = []
        self._stats: Dict[str, EventTypeStats] = {}
        self._lock = Lock()
        self._total_published = 0
        self._total_delivered = 0

    def start(self) -> None:
        """Start the instrumentation bus."""
        self._events = deque(maxlen=self.config.max_events)
        self._handlers = defaultdict(list)
        self._global_handlers = []
        self._stats = {}
        self._total_published = 0
        self._total_delivered = 0
        self.running = True
        logger.info("InstrumentationBus started (max_events=%d)", self.config.max_events)

    def stop(self) -> None:
        """Stop the instrumentation bus."""
        self.running = False
        logger.info("InstrumentationBus stopped (total_published=%d)", self._total_published)

    def publish(self, event_type: str, source: str, data: Optional[Dict[str, Any]] = None) -> BusEvent:
        """
        Publish an event to the bus.

        Args:
            event_type: Type of event (metric_update, alert, heartbeat, state_change, error)
            source: Source module/agent name
            data: Optional event data dict

        Returns:
            The published BusEvent
        """
        event = BusEvent(event_type=event_type, source=source, data=data or {})

        with self._lock:
            self._events.append(event)
            self._total_published += 1

            # Update stats
            if event_type not in self._stats:
                self._stats[event_type] = EventTypeStats(
                    event_type=event_type,
                    first_event_time=event.timestamp,
                )
            stats = self._stats[event_type]
            stats.count += 1
            stats.last_event_time = event.timestamp

        # Dispatch to handlers (outside lock)
        delivered = 0
        for handler in self._global_handlers:
            try:
                handler(event)
                delivered += 1
            except Exception as e:
                logger.warning("Global handler error: %s", e)

        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
                delivered += 1
            except Exception as e:
                logger.warning("Handler error for %s: %s", event_type, e)

        with self._lock:
            self._total_delivered += delivered

        return event

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        Subscribe a handler to a specific event type.

        Args:
            event_type: Event type to subscribe to, or '*' for all events
            handler: Callable that receives BusEvent
        """
        if event_type == '*':
            self._global_handlers.append(handler)
        else:
            self._handlers[event_type].append(handler)
        logger.debug("Subscribed handler for event_type=%s", event_type)

    def unsubscribe(self, handler: Callable) -> int:
        """
        Unsubscribe a handler from all event types.

        Returns:
            Number of subscriptions removed
        """
        removed = 0
        if handler in self._global_handlers:
            self._global_handlers.remove(handler)
            removed += 1
        for event_type, handlers in list(self._handlers.items()):
            if handler in handlers:
                handlers.remove(handler)
                removed += 1
        return removed

    def get_recent_events(self, n: int = 50, event_type: Optional[str] = None) -> List[BusEvent]:
        """
        Get the N most recent events, optionally filtered by type.

        Args:
            n: Maximum number of events to return
            event_type: Optional filter by event type

        Returns:
            List of BusEvent, most recent first
        """
        with self._lock:
            events = list(self._events)

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events[-n:][::-1]

    def get_event_stats(self) -> Dict[str, EventTypeStats]:
        """
        Get statistics for all event types.

        Returns:
            Dict mapping event_type -> EventTypeStats
        """
        with self._lock:
            return dict(self._stats)

    def get_bus_stats(self) -> Dict[str, Any]:
        """
        Get overall bus statistics.

        Returns:
            Dict with total_published, total_delivered, event_count, handler_count, type_count
        """
        with self._lock:
            return {
                "total_published": self._total_published,
                "total_delivered": self._total_delivered,
                "event_buffer_size": len(self._events),
                "event_buffer_max": self.config.max_events,
                "handler_count": sum(len(h) for h in self._handlers.values()) + len(self._global_handlers),
                "event_type_count": len(self._stats),
                "event_types": {k: v.count for k, v in self._stats.items()},
            }

    def clear(self) -> int:
        """
        Clear all events from the buffer.

        Returns:
            Number of events cleared
        """
        with self._lock:
            count = len(self._events)
            self._events.clear()
            return count
