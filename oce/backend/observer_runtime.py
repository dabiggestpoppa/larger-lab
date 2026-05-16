"""
OCE Observer Runtime
====================
Execution layer that brings SRRA-OPH observers to life within OCE.

Responsibilities:
- Observer lifecycle management (create, activate, suspend, destroy)
- Event routing from Event Fabric to subscribed observers
- Health monitoring (entropy, drift, budget)
- State persistence (reconstruction from sparse anchors)
- Observer API (REST + WebSocket)

Architecture:
    Event Fabric → Observer Runtime → SRRA-OPH Substrate
                                         ↓
                                    Observer State
                                         ↓
                                    Persistence
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from event_fabric import EventFabric, Event, get_fabric

logger = logging.getLogger("oce.runtime")


# ─── Observer State Machine ──────────────────────────────────────────────────

class ObserverState(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DESTROYED = "destroyed"


# ─── Observer Model ──────────────────────────────────────────────────────────

class ObserverConfig(BaseModel):
    """Configuration for creating a new observer."""
    observer_type: str  # planner, execution, memory, repair, trading, entropy, content, system
    name: str
    description: str = ""
    capabilities: List[str] = []
    event_subscriptions: List[str] = []  # event types to subscribe to
    config: Dict[str, Any] = {}  # type-specific config


class Observer(BaseModel):
    """An active observer instance."""
    observer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: ObserverConfig
    state: ObserverState = ObserverState.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    destroyed_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None
    event_count: int = 0
    error_count: int = 0
    health_score: float = 1.0  # 0.0 = unhealthy, 1.0 = healthy
    entropy: float = 0.0
    metadata: Dict[str, Any] = {}


class ObserverHealth(BaseModel):
    """Health metrics for an observer."""
    observer_id: str
    state: ObserverState
    health_score: float
    entropy: float
    event_count: int
    error_count: int
    uptime_seconds: float = 0.0
    last_event_at: Optional[str] = None
    drift_signals: int = 0
    budget_remaining: float = 500.0


# ─── Observer Runtime ────────────────────────────────────────────────────────

class ObserverRuntime:
    """
    Core Observer Runtime engine.

    Manages observer lifecycle, routes events from the Event Fabric,
    monitors health, and persists state.
    """

    def __init__(self, fabric: Optional[EventFabric] = None):
        self._fabric = fabric or get_fabric()
        self._observers: Dict[str, Observer] = {}
        self._lock = asyncio.Lock()

    # ── Lifecycle ─────────────────────────────────────────────────────────

    async def create_observer(self, config: ObserverConfig) -> Observer:
        """Create and register a new observer."""
        async with self._lock:
            observer = Observer(config=config)
            self._observers[observer.observer_id] = observer

            # Subscribe to events
            if config.event_subscriptions:
                self._fabric.subscribe(
                    callback=lambda e, oid=observer.observer_id: self._handle_event(oid, e),
                    event_types=config.event_subscriptions,
                )

            # Emit creation event
            await self._fabric.ingest(
                event_type="observer.created",
                source="observer_runtime",
                payload={
                    "observer_id": observer.observer_id,
                    "observer_type": config.observer_type,
                    "name": config.name,
                },
                priority=2,
            )

            logger.info(f"Observer created: {observer.observer_id} ({config.name})")
            return observer

    async def activate_observer(self, observer_id: str) -> Optional[Observer]:
        """Activate an observer to start processing events."""
        async with self._lock:
            observer = self._observers.get(observer_id)
            if not observer or observer.state == ObserverState.DESTROYED:
                return None

            observer.state = ObserverState.ACTIVE
            observer.activated_at = datetime.now(timezone.utc)

            await self._fabric.ingest(
                event_type="observer.state_change",
                source="observer_runtime",
                payload={
                    "observer_id": observer_id,
                    "state": "active",
                    "previous_state": observer.state.value,
                },
            )

            logger.info(f"Observer activated: {observer_id}")
            return observer

    async def suspend_observer(self, observer_id: str) -> Optional[Observer]:
        """Suspend an observer (pause event processing)."""
        async with self._lock:
            observer = self._observers.get(observer_id)
            if not observer or observer.state == ObserverState.DESTROYED:
                return None

            previous_state = observer.state
            observer.state = ObserverState.SUSPENDED
            observer.suspended_at = datetime.now(timezone.utc)

            await self._fabric.ingest(
                event_type="observer.state_change",
                source="observer_runtime",
                payload={
                    "observer_id": observer_id,
                    "state": "suspended",
                    "previous_state": previous_state.value,
                },
            )

            logger.info(f"Observer suspended: {observer_id}")
            return observer

    async def destroy_observer(self, observer_id: str) -> bool:
        """Destroy an observer (permanent removal)."""
        async with self._lock:
            observer = self._observers.get(observer_id)
            if not observer:
                return False

            observer.state = ObserverState.DESTROYED
            observer.destroyed_at = datetime.now(timezone.utc)

            await self._fabric.ingest(
                event_type="observer.destroyed",
                source="observer_runtime",
                payload={
                    "observer_id": observer_id,
                    "observer_type": config.observer_type if (config := observer.config) else "unknown",
                    "total_events": observer.event_count,
                    "total_errors": observer.error_count,
                },
                priority=2,
            )

            # Remove from active observers
            del self._observers[observer_id]

            logger.info(f"Observer destroyed: {observer_id}")
            return True

    # ── Query ──────────────────────────────────────────────────────────────

    def get_observer(self, observer_id: str) -> Optional[Observer]:
        """Get a single observer by ID."""
        return self._observers.get(observer_id)

    def list_observers(
        self,
        state: Optional[ObserverState] = None,
        observer_type: Optional[str] = None,
    ) -> List[Observer]:
        """List all observers with optional filters."""
        results = list(self._observers.values())

        if state:
            results = [o for o in results if o.state == state]
        if observer_type:
            results = [o for o in results if o.config.observer_type == observer_type]

        return results

    def get_observer_health(self, observer_id: str) -> Optional[ObserverHealth]:
        """Get health metrics for an observer."""
        observer = self._observers.get(observer_id)
        if not observer:
            return None

        uptime = 0.0
        if observer.activated_at:
            uptime = (datetime.now(timezone.utc) - observer.activated_at).total_seconds()

        return ObserverHealth(
            observer_id=observer.observer_id,
            state=observer.state,
            health_score=observer.health_score,
            entropy=observer.entropy,
            event_count=observer.event_count,
            error_count=observer.error_count,
            uptime_seconds=uptime,
            last_event_at=observer.last_event_at.isoformat() if observer.last_event_at else None,
        )

    def get_all_health(self) -> List[ObserverHealth]:
        """Get health metrics for all observers."""
        return [
            self.get_observer_health(oid)
            for oid in self._observers
            if self.get_observer_health(oid) is not None
        ]

    # ── Event Handling ─────────────────────────────────────────────────────

    async def _handle_event(self, observer_id: str, event: Event):
        """Route an event to a specific observer."""
        observer = self._observers.get(observer_id)
        if not observer or observer.state != ObserverState.ACTIVE:
            return

        observer.event_count += 1
        observer.last_event_at = datetime.now(timezone.utc)

        # Update health based on event priority
        if event.priority >= 3:  # critical
            observer.health_score = max(0.0, observer.health_score - 0.1)
        elif event.priority == 0:  # low
            observer.health_score = min(1.0, observer.health_score + 0.01)

        logger.debug(f"Event {event.event_id[:8]} → observer {observer_id[:8]}")

    # ── Persistence ────────────────────────────────────────────────────────

    async def snapshot_observer(self, observer_id: str) -> Optional[Dict[str, Any]]:
        """Create a state snapshot of an observer for persistence."""
        observer = self._observers.get(observer_id)
        if not observer:
            return None

        return {
            "observer_id": observer.observer_id,
            "config": observer.config.model_dump(),
            "state": observer.state.value,
            "created_at": observer.created_at.isoformat(),
            "event_count": observer.event_count,
            "error_count": observer.error_count,
            "health_score": observer.health_score,
            "entropy": observer.entropy,
            "metadata": observer.metadata,
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
        }

    async def restore_observer(self, snapshot: Dict[str, Any]) -> Optional[Observer]:
        """Restore an observer from a state snapshot."""
        try:
            config = ObserverConfig(**snapshot["config"])
            observer = Observer(
                observer_id=snapshot["observer_id"],
                config=config,
                state=ObserverState(snapshot["state"]),
                created_at=datetime.fromisoformat(snapshot["created_at"]),
                event_count=snapshot.get("event_count", 0),
                error_count=snapshot.get("error_count", 0),
                health_score=snapshot.get("health_score", 1.0),
                entropy=snapshot.get("entropy", 0.0),
                metadata=snapshot.get("metadata", {}),
            )
            self._observers[observer.observer_id] = observer
            return observer
        except Exception as e:
            logger.error(f"Failed to restore observer: {e}")
            return None

    # ── Statistics ─────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get Observer Runtime statistics."""
        states = {}
        types = {}
        for o in self._observers.values():
            states[o.state.value] = states.get(o.state.value, 0) + 1
            t = o.config.observer_type
            types[t] = types.get(t, 0) + 1

        return {
            "total_observers": len(self._observers),
            "by_state": states,
            "by_type": types,
            "total_events_processed": sum(o.event_count for o in self._observers.values()),
            "total_errors": sum(o.error_count for o in self._observers.values()),
            "avg_health": (
                sum(o.health_score for o in self._observers.values()) / len(self._observers)
                if self._observers else 0.0
            ),
        }


# ─── Singleton ────────────────────────────────────────────────────────────────

_runtime: Optional[ObserverRuntime] = None


def get_runtime() -> ObserverRuntime:
    """Get or create the Observer Runtime singleton."""
    global _runtime
    if _runtime is None:
        _runtime = ObserverRuntime()
    return _runtime
