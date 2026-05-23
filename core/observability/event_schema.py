"""
Phase 11.2-3B.3 — Continuity Event Schema
==========================================
Unified event language for continuity observation.

Every event carries:
    - continuity_score  (0.0-1.0, how intact is continuity)
    - entropy_delta     (change in entropy caused by this event)
    - observer_pressure (how many observers are affected)
    - field_zone        (which operational zone this belongs to)
    - attractor_region  (which attractor basin this maps to)

Output: normalized_continuity_events.parquet (or JSON for now)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]  # larger-lab/
EXPORTS_DIR = REPO_ROOT / "experiments" / "exports" / "timelines"


class EventType(Enum):
    """Core continuity event types."""
    OBSERVER_SPAWN = "observer_spawn"
    OBSERVER_SYNC = "observer_sync"
    OBSERVER_DEGRADE = "observer_degrade"
    OBSERVER_RECOVER = "observer_recover"
    OBSERVER_SHUTDOWN = "observer_shutdown"
    MEMORY_PULL = "memory_pull"
    MEMORY_PUSH = "memory_push"
    MEMORY_CORRUPT = "memory_corrupt"
    ROUTE_SHIFT = "route_shift"
    ROUTE_STABILIZE = "route_stabilize"
    REPAIR_TRIGGER = "repair_trigger"
    REPAIR_COMPLETE = "repair_complete"
    REPAIR_FAIL = "repair_fail"
    FIELD_PERTURBATION = "field_perturbation"
    FIELD_DISSIPATE = "field_dissipate"
    ATTRACTOR_LOCK = "attractor_lock"
    ATTRACTOR_ESCAPE = "attractor_escape"
    CONTINUITY_DROP = "continuity_drop"
    CONTINUITY_RESTORE = "continuity_restore"
    CHAOS_INJECT = "chaos_inject"
    SYNC_DRIFT = "sync_drift"
    SYNC_RESTORE = "sync_restore"


@dataclass
class ContinuityEvent:
    """A single continuity event with full context."""
    event_id: str
    timestamp: str
    event_type: str
    source: str

    # Continuity metrics
    continuity_score: float = 1.0   # 0.0-1.0
    entropy_delta: float = 0.0      # change in entropy
    observer_pressure: int = 0      # observers affected

    # Field context
    field_zone: str = "default"
    attractor_region: str = "unknown"

    # Event details
    target: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    success: bool = True

    # Chain tracking
    parent_event_id: str | None = None
    chain_id: str | None = None


class EventStore:
    """
    Append-only event store for continuity events.
    Supports chain tracking, filtering, and export.
    """

    def __init__(self):
        self._events: list[ContinuityEvent] = []
        self._chains: dict[str, list[str]] = {}  # chain_id -> [event_ids]
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def emit(self, event_type: EventType, source: str,
             continuity_score: float = 1.0,
             entropy_delta: float = 0.0,
             observer_pressure: int = 0,
             field_zone: str = "default",
             attractor_region: str = "unknown",
             target: str = "",
             details: dict | None = None,
             duration_ms: float = 0.0,
             success: bool = True,
             parent_event_id: str | None = None,
             chain_id: str | None = None) -> ContinuityEvent:
        """Emit a new continuity event."""

        # Auto-generate chain_id from parent if not provided
        if chain_id is None and parent_event_id is not None:
            for ev in self._events:
                if ev.event_id == parent_event_id:
                    chain_id = ev.chain_id
                    break

        if chain_id is None:
            chain_id = f"chain_{uuid.uuid4().hex[:8]}"

        event = ContinuityEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type.value,
            source=source,
            continuity_score=max(0.0, min(1.0, continuity_score)),
            entropy_delta=entropy_delta,
            observer_pressure=observer_pressure,
            field_zone=field_zone,
            attractor_region=attractor_region,
            target=target,
            details=details or {},
            duration_ms=duration_ms,
            success=success,
            parent_event_id=parent_event_id,
            chain_id=chain_id,
        )

        self._events.append(event)
        self._chains.setdefault(chain_id, []).append(event.event_id)

        return event

    def get_chain(self, chain_id: str) -> list[ContinuityEvent]:
        """Get all events in a chain, ordered by time."""
        event_ids = self._chains.get(chain_id, [])
        events = [e for e in self._events if e.event_id in event_ids]
        return sorted(events, key=lambda e: e.timestamp)

    def get_events_by_type(self, event_type: EventType) -> list[ContinuityEvent]:
        """Filter events by type."""
        return [e for e in self._events if e.event_type == event_type.value]

    def get_events_by_zone(self, field_zone: str) -> list[ContinuityEvent]:
        """Filter events by field zone."""
        return [e for e in self._events if e.field_zone == field_zone]

    def get_continuity_timeline(self) -> list[dict]:
        """Get continuity_score over time."""
        return [
            {"timestamp": e.timestamp, "continuity_score": e.continuity_score,
             "entropy_delta": e.entropy_delta, "event_type": e.event_type}
            for e in sorted(self._events, key=lambda e: e.timestamp)
        ]

    def get_entropy_profile(self) -> dict:
        """Aggregate entropy statistics."""
        if not self._events:
            return {"status": "no_data"}

        deltas = [e.entropy_delta for e in self._events]
        return {
            "total_events": len(self._events),
            "total_entropy_injected": sum(d for d in deltas if d > 0),
            "total_entropy_dissipated": abs(sum(d for d in deltas if d < 0)),
            "net_entropy": sum(deltas),
            "avg_entropy_per_event": round(sum(abs(d) for d in deltas) / len(deltas), 4),
            "max_single_entropy": max(deltas) if deltas else 0,
            "min_single_entropy": min(deltas) if deltas else 0,
        }

    def get_repair_chains(self) -> list[list[dict]]:
        """Extract all repair trigger → complete/fail chains."""
        repair_events = [e for e in self._events
                         if e.event_type in (EventType.REPAIR_TRIGGER.value,
                                             EventType.REPAIR_COMPLETE.value,
                                             EventType.REPAIR_FAIL.value)]
        chains: dict[str, list[dict]] = {}
        for e in repair_events:
            chains.setdefault(e.chain_id or "ungrouped", []).append(asdict(e))
        return list(chains.values())

    def export(self, path: Path | None = None) -> Path:
        """Export all events to JSON."""
        path = path or EXPORTS_DIR / "normalized_continuity_events.json"

        data = {
            "version": "0.1.0",
            "phase": "11.2-3B.3",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_events": len(self._events),
            "total_chains": len(self._chains),
            "entropy_profile": self.get_entropy_profile(),
            "events": [asdict(e) for e in self._events],
            "chains": {k: v for k, v in self._chains.items()},
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return path

    def summary(self) -> dict:
        """Quick summary of event store state."""
        type_counts: dict[str, int] = {}
        for e in self._events:
            type_counts[e.event_type] = type_counts.get(e.event_type, 0) + 1

        return {
            "total_events": len(self._events),
            "total_chains": len(self._chains),
            "event_types": type_counts,
            "entropy_profile": self.get_entropy_profile(),
            "latest_continuity": self._events[-1].continuity_score if self._events else None,
        }


# ─── Global Singleton ────────────────────────────────────────────────────

_store: EventStore | None = None


def get_event_store() -> EventStore:
    """Get or create the global event store."""
    global _store
    if _store is None:
        _store = EventStore()
    return _store
