"""
OCE Event Fabric
================
Real-time event streaming backbone connecting OCE Continuity Core to SRRA-OPH Observer Runtime.

Responsibilities:
- Event ingestion (validate, timestamp, classify)
- Event routing (topology-aware, broadcast + targeted)
- Event persistence (trajectory memory, configurable retention)
- Event streaming (async generator for WebSocket)

Architecture:
    SRRA-OPH Substrate → ingest() → route() → persist()
                                               → stream() → WebSocket → Frontend
"""

import asyncio
import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field


# ─── Event Model ──────────────────────────────────────────────────────────────

class Event(BaseModel):
    """Core event model for the OCE Event Fabric."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # observer.state_change, attractor.update, entropy.signal, repair.trigger, etc.
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str  # which observer/subsystem emitted it
    priority: int = Field(default=0)  # 0=low, 1=normal, 2=high, 3=critical
    payload: Dict[str, Any] = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def __init__(self, **data):
        # Auto-classify priority from event_type if not explicitly set
        super().__init__(**data)
        if self.priority == 0 and self.event_type:
            classification = classify_event(self.event_type)
            # Only override if the default (0) was used, not if explicitly set to 0
            # We check if 'priority' was in the original data
            if 'priority' not in data:
                self.priority = classification.get("priority", 1)


# ─── Event Type Registry ─────────────────────────────────────────────────────

# Canonical event types emitted by SRRA-OPH subsystems
EVENT_TYPES = {
    # Observer events
    "observer.state_change": {"priority": 1, "description": "Observer state changed (active/idle/repairing)"},
    "observer.created": {"priority": 2, "description": "New observer registered"},
    "observer.destroyed": {"priority": 2, "description": "Observer removed"},
    "observer.entropy_threshold": {"priority": 3, "description": "Observer entropy exceeded threshold"},

    # Attractor events
    "attractor.update": {"priority": 1, "description": "Attractor state updated"},
    "attractor.convergence": {"priority": 2, "description": "Attractor reached convergence"},
    "attractor.divergence": {"priority": 3, "description": "Attractor diverged"},

    # Entropy events
    "entropy.signal": {"priority": 1, "description": "Entropy level changed"},
    "entropy.budget_warning": {"priority": 2, "description": "Entropy budget running low"},
    "entropy.budget_exhausted": {"priority": 3, "description": "Entropy budget exhausted"},

    # Repair events
    "repair.triggered": {"priority": 2, "description": "Repair process initiated"},
    "repair.completed": {"priority": 1, "description": "Repair completed successfully"},
    "repair.failed": {"priority": 3, "description": "Repair failed"},

    # Chat events
    "chat.message.received": {"priority": 0, "description": "User message received"},
    "chat.message.responded": {"priority": 0, "description": "Assistant response generated"},

    # System events
    "system.startup": {"priority": 1, "description": "OCE system started"},
    "system.shutdown": {"priority": 1, "description": "OCE system shutting down"},
    "system.error": {"priority": 3, "description": "System error occurred"},

    # Operator events (from PM's Operator tools)
    "operator.command.executed": {"priority": 1, "description": "System command executed"},
    "operator.process.killed": {"priority": 2, "description": "Process terminated"},
    "operator.file.modified": {"priority": 0, "description": "File modified by operator"},
    "operator.vscode.event": {"priority": 0, "description": "VS Code action performed"},
}


def classify_event(event_type: str) -> dict:
    """Classify an event type, returning priority and description."""
    if event_type in EVENT_TYPES:
        return EVENT_TYPES[event_type]
    # Unknown events get normal priority
    return {"priority": 1, "description": f"Unknown event type: {event_type}"}


# ─── Subscriber ───────────────────────────────────────────────────────────────

class Subscriber:
    """An event subscriber with optional filtering."""
    def __init__(self, callback: Callable, event_types: Optional[Set[str]] = None, source_filter: Optional[str] = None):
        self.callback = callback
        self.event_types = event_types  # None = subscribe to all
        self.source_filter = source_filter  # None = all sources

    def matches(self, event: Event) -> bool:
        """Check if this subscriber wants this event."""
        if self.event_types and event.event_type not in self.event_types:
            return False
        if self.source_filter and event.source != self.source_filter:
            return False
        return True


# ─── Event Fabric ─────────────────────────────────────────────────────────────

class EventFabric:
    """
    Core Event Fabric engine.

    Ingests events from SRRA-OPH substrate, routes them to subscribers,
    persists them to memory, and streams them to WebSocket clients.
    """

    def __init__(self, max_history: int = 10000, retention_per_type: int = 1000):
        self._subscribers: List[Subscriber] = []
        self._event_history: List[Event] = []
        self._events_by_type: Dict[str, List[Event]] = defaultdict(list)
        self._events_by_source: Dict[str, List[Event]] = defaultdict(list)
        self._max_history = max_history
        self._retention_per_type = retention_per_type
        self._total_ingested = 0
        self._total_routed = 0
        self._total_persisted = 0
        self._stream_queues: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    # ── Ingestion ─────────────────────────────────────────────────────────

    async def ingest(self, event_type: str, source: str, payload: Dict[str, Any] = None, priority: int = None) -> Event:
        """
        Ingest a new event into the fabric.

        Args:
            event_type: Type of event (e.g., "observer.state_change")
            source: Source subsystem (e.g., "planner", "attractor")
            payload: Event data
            priority: Override auto-detected priority

        Returns:
            The created Event
        """
        # Auto-classify priority if not specified
        if priority is None:
            classification = classify_event(event_type)
            priority = classification["priority"]

        event = Event(
            event_type=event_type,
            source=source,
            priority=priority,
            payload=payload or {},
        )

        async with self._lock:
            # Store in history
            self._event_history.append(event)
            self._events_by_type[event_type].append(event)
            self._events_by_source[source].append(event)
            self._total_ingested += 1

            # Enforce retention limits
            self._enforce_retention(event_type)

        # Route to subscribers
        await self._route(event)

        # Broadcast to stream queues
        await self._broadcast_to_streams(event)

        return event

    def _enforce_retention(self, event_type: str):
        """Enforce per-type retention limits."""
        type_events = self._events_by_type[event_type]
        if len(type_events) > self._retention_per_type:
            # Remove oldest events of this type
            excess = len(type_events) - self._retention_per_type
            self._events_by_type[event_type] = type_events[excess:]

        # Enforce global history limit
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

    # ── Routing ───────────────────────────────────────────────────────────

    def subscribe(self, callback: Callable, event_types: List[str] = None, source_filter: str = None) -> Subscriber:
        """
        Subscribe to events.

        Args:
            callback: Async or sync callable that receives Event
            event_types: Optional list of event types to filter (None = all)
            source_filter: Optional source filter (None = all sources)

        Returns:
            Subscriber object (call .unsubscribe() to remove)
        """
        sub = Subscriber(
            callback=callback,
            event_types=set(event_types) if event_types else None,
            source_filter=source_filter,
        )
        self._subscribers.append(sub)
        return sub

    def unsubscribe(self, subscriber: Subscriber):
        """Remove a subscriber."""
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    async def _route(self, event: Event):
        """Route an event to all matching subscribers."""
        for sub in self._subscribers:
            if sub.matches(event):
                self._total_routed += 1
                try:
                    if asyncio.iscoroutinefunction(sub.callback):
                        await sub.callback(event)
                    else:
                        sub.callback(event)
                except Exception as e:
                    # Don't let subscriber errors break the fabric
                    pass

    # ── Persistence ───────────────────────────────────────────────────────

    async def persist(self, event: Event):
        """
        Persist an event to trajectory memory.
        Delegates to SRRA-OPH TrajectoryReconstructionField.
        """
        # Persistence is handled by storing in history (in-memory for now)
        # In Phase 2+, this will write to SQLite/trajectory store
        self._total_persisted += 1
        return event.event_id

    def get_history(self, event_type: str = None, source: str = None, limit: int = 50, min_priority: int = None) -> List[Event]:
        """
        Query event history with optional filters.

        Args:
            event_type: Filter by event type
            source: Filter by source
            limit: Max events to return (most recent first)
            min_priority: Minimum priority level

        Returns:
            List of matching events, most recent first
        """
        if event_type:
            events = list(self._events_by_type.get(event_type, []))
        elif source:
            events = list(self._events_by_source.get(source, []))
        else:
            events = list(self._event_history)

        if min_priority is not None:
            events = [e for e in events if e.priority >= min_priority]

        # Return most recent first
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    # ── Streaming ──────────────────────────────────────────────────────────

    def create_stream(self) -> asyncio.Queue:
        """
        Create a new event stream queue.
        Used by WebSocket handlers to receive real-time events.
        """
        queue = asyncio.Queue(maxsize=1000)
        self._stream_queues.append(queue)
        return queue

    def close_stream(self, queue: asyncio.Queue):
        """Close an event stream queue."""
        if queue in self._stream_queues:
            self._stream_queues.remove(queue)

    async def _broadcast_to_streams(self, event: Event):
        """Broadcast an event to all active stream queues."""
        dead_queues = []
        for queue in self._stream_queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest event and try again
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    dead_queues.append(queue)
            except Exception:
                dead_queues.append(queue)

        # Clean up dead queues
        for q in dead_queues:
            self.close_stream(q)

    async def stream_events(self, queue: asyncio.Queue) -> AsyncGenerator[Event, None]:
        """
        Async generator that yields events from a stream queue.
        Use this in WebSocket handlers.
        """
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield event
        except asyncio.TimeoutError:
            # Send heartbeat to keep connection alive
            yield None
        except Exception:
            pass

    # ── Statistics ─────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get Event Fabric statistics."""
        type_counts = {etype: len(events) for etype, events in self._events_by_type.items()}
        source_counts = {src: len(events) for src, events in self._events_by_source.items()}

        return {
            "total_ingested": self._total_ingested,
            "total_routed": self._total_routed,
            "total_persisted": self._total_persisted,
            "active_subscribers": len(self._subscribers),
            "active_streams": len(self._stream_queues),
            "history_size": len(self._event_history),
            "events_by_type": type_counts,
            "events_by_source": source_counts,
            "registered_event_types": list(EVENT_TYPES.keys()),
        }

    def get_event_types(self) -> List[Dict[str, Any]]:
        """Get all registered event types with metadata."""
        return [
            {"type": t, "priority": m["priority"], "description": m["description"]}
            for t, m in EVENT_TYPES.items()
        ]


# ─── Singleton ────────────────────────────────────────────────────────────────

_fabric: Optional[EventFabric] = None


def get_fabric() -> EventFabric:
    """Get or create the Event Fabric singleton."""
    global _fabric
    if _fabric is None:
        _fabric = EventFabric()
    return _fabric
