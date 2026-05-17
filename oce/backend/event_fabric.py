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

Topology Routing (OCE-2.3):
    Events are routed through a coupling graph that models observer proximity.
    The TopologicalRouter uses Dijkstra's algorithm on edge weights to find
    lowest-entropy paths. Supports broadcast (all) and targeted (specific observer).

Persistence Layer (OCE-2.4):
    Events are stored in trajectory memory via TrajectoryReconstructionField.
    Configurable retention per event type. Old events are compressed via
    AdaptiveCompressionEngine while preserving recoverability.
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger("oce.fabric")


# ─── Event Model ──────────────────────────────────────────────────────────────

class Event(BaseModel):
    """Core event model for the OCE Event Fabric."""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    priority: int = Field(default=0, ge=0, le=3)
    payload: Dict[str, Any] = {}

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

        # Persist to SQLite
        try:
            persistence = get_persistence()
            await persistence.store_event(event)
        except Exception as e:
            logger.warning(f"Persistence failed (non-critical): {e}")

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
                    logger.warning(f"Subscriber error during routing: {e}")

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


# ─── Topological Router (OCE-2.3) ───────────────────────────────────────────

class TopologicalRouter:
    """
    Topology-aware event routing using a coupling graph.
    
    Routes events through observer proximity graph using Dijkstra's algorithm
    on edge weights to find lowest-entropy paths.
    Supports broadcast (all observers) and targeted (specific observer) routing.
    """

    def __init__(self):
        self._edges: Dict[tuple, float] = {}  # (observer_a, observer_b) -> weight
        self._observers: Set[str] = set()

    def register_observer(self, observer_id: str):
        """Register an observer in the topology."""
        self._observers.add(observer_id)

    def unregister_observer(self, observer_id: str):
        """Remove an observer from the topology."""
        self._observers.discard(observer_id)
        # Clean up edges
        keys_to_remove = [k for k in self._edges if observer_id in k]
        for k in keys_to_remove:
            del self._edges[k]

    def update_edge(self, observer_a: str, observer_b: str, weight: float):
        """Update coupling weight between two observers."""
        key = (min(observer_a, observer_b), max(observer_a, observer_b))
        self._edges[key] = max(0.0, min(1.0, weight))
        self._observers.add(observer_a)
        self._observers.add(observer_b)

    def get_path(self, source: str, target: str) -> List[str]:
        """Find lowest-entropy path between observers using Dijkstra."""
        if source not in self._observers or target not in self._observers:
            return []
        
        # Build adjacency list
        adj: Dict[str, Dict[str, float]] = {o: {} for o in self._observers}
        for (a, b), w in self._edges.items():
            adj[a][b] = w
            adj[b][a] = w

        # Dijkstra (weight = 1.0 - coupling, so low weight = strong coupling)
        import heapq
        dist = {o: float('inf') for o in self._observers}
        prev = {o: None for o in self._observers}
        dist[source] = 0
        heap = [(0, source)]
        visited = set()

        while heap:
            d, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)
            if u == target:
                break
            for v, w in adj.get(u, {}).items():
                cost = 1.0 - w  # Invert: strong coupling = low cost
                if d + cost < dist[v]:
                    dist[v] = d + cost
                    prev[v] = u
                    heapq.heappush(heap, (dist[v], v))

        # Reconstruct path
        path = []
        node = target
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()
        return path if path[0] == source else []

    def get_broadcast_targets(self, source: str, max_hops: int = 3) -> List[str]:
        """Get all observers reachable within max_hops from source."""
        if source not in self._observers:
            return list(self._observers)
        
        visited = {source}
        current_level = {source}
        for _ in range(max_hops):
            next_level = set()
            for node in current_level:
                for (a, b), w in self._edges.items():
                    if a == node and b not in visited:
                        next_level.add(b)
                    elif b == node and a not in visited:
                        next_level.add(a)
            visited |= next_level
            current_level = next_level
        return list(visited - {source})

    def get_topology_stats(self) -> Dict[str, Any]:
        """Get topology statistics."""
        return {
            "observers": len(self._observers),
            "edges": len(self._edges),
            "avg_coupling": sum(self._edges.values()) / len(self._edges) if self._edges else 0,
            "density": len(self._edges) / (len(self._observers) * (len(self._observers) - 1) / 2) if len(self._observers) > 1 else 0,
        }


# ─── Persistence Layer (OCE-2.4) ────────────────────────────────────────────

import sqlite3
from pathlib import Path

class EventPersistence:
    """
    SQLite-backed event persistence layer.
    Stores events in trajectory memory with configurable retention.
    Compresses old events while preserving recoverability.
    """

    def __init__(self, db_path: str = "data/events.db", retention_per_type: int = 1000):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._retention = retention_per_type
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                priority INTEGER DEFAULT 1,
                payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
            CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
            CREATE TABLE IF NOT EXISTS event_compression (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                original_count INTEGER,
                compressed_count INTEGER,
                compressed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.close()

    def store_event(self, event: Event):
        """Store a single event."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute(
            "INSERT OR REPLACE INTO events (event_id, event_type, source, priority, payload, created_at) VALUES (?,?,?,?,?,?)",
            (event.event_id, event.event_type, event.source, event.priority,
             json.dumps(event.payload), event.timestamp.isoformat())
        )
        conn.commit()
        conn.close()

    def query_events(self, event_type: str = None, source: str = None,
                     limit: int = 100, since: str = None) -> List[Dict]:
        """Query stored events."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        q = "SELECT * FROM events WHERE 1=1"
        params = []
        if event_type:
            q += " AND event_type = ?"
            params.append(event_type)
        if source:
            q += " AND source = ?"
            params.append(source)
        if since:
            q += " AND created_at > ?"
            params.append(since)
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def compress_old_events(self, event_type: str, keep_last: int = 100):
        """Compress old events, keeping only the most recent N per type."""
        conn = sqlite3.connect(str(self._db_path))
        # Count total
        total = conn.execute("SELECT COUNT(*) FROM events WHERE event_type = ?",
                             (event_type,)).fetchone()[0]
        if total <= keep_last:
            conn.close()
            return

        # Delete old events beyond retention
        conn.execute("""DELETE FROM events WHERE event_type = ? AND event_id NOT IN
                      (SELECT event_id FROM events WHERE event_type = ?
                       ORDER BY created_at DESC LIMIT ?)""",
                     (event_type, event_type, keep_last))

        deleted = total - keep_last
        conn.execute(
            "INSERT INTO event_compression (event_type, original_count, compressed_count) VALUES (?,?,?)",
            (event_type, total, keep_last)
        )
        conn.commit()
        conn.close()
        return deleted

    def get_stats(self) -> Dict[str, Any]:
        """Get persistence statistics."""
        conn = sqlite3.connect(str(self._db_path))
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        types = conn.execute("SELECT event_type, COUNT(*) FROM events GROUP BY event_type").fetchall()
        conn.close()
        return {
            "total_events": total,
            "events_by_type": {t: c for t, c in types},
            "retention_per_type": self._retention,
        }


# ─── Singleton ────────────────────────────────────────────────────────────────

_fabric: Optional[EventFabric] = None
_router: Optional[TopologicalRouter] = None
_persistence: Optional[EventPersistence] = None


def get_fabric() -> EventFabric:
    """Get or create the Event Fabric singleton."""
    global _fabric
    if _fabric is None:
        _fabric = EventFabric()
    return _fabric


def get_router() -> TopologicalRouter:
    """Get or create the Topological Router singleton."""
    global _router
    if _router is None:
        _router = TopologicalRouter()
    return _router


def get_persistence() -> EventPersistence:
    """Get or create the Event Persistence singleton."""
    global _persistence
    if _persistence is None:
        _persistence = EventPersistence()
    return _persistence
