"""Event envelope and causality for OCE control plane.

B3.C3 / B2-C3 — event ID, type, schema, actor, authority, causality,
target, hashes, environment, result, evidence. Parent/root correlation,
ordering facts, monotonic sequence, clock uncertainty.
"""
from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
import json

from .clocks import get_clock
from .hashes import generate_id, payload_hash


@dataclass
class EventEnvelope:
    event_id: str
    event_type: str
    schema_version: str
    actor_id: str
    authority_grant_id: str
    causality: dict
    target: str
    payload_hash: str
    environment: str
    timestamp: str
    result: dict = field(default_factory=dict)
    evidence_refs: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class EventStore:
    """Append-only event store with causality tracking."""

    def __init__(self):
        self._events: list[EventEnvelope] = []
        self._by_id: dict[str, EventEnvelope] = {}
        self._by_root: dict[str, list[str]] = {}  # root_id -> [event_ids]
        self._sequence: int = 0

    def emit(self, *, event_type: str, actor_id: str, authority_grant_id: str,
             target: str, payload: dict, environment: str = "local",
             root_id: Optional[str] = None, parent_id: Optional[str] = None,
             result: dict = None) -> EventEnvelope:
        """Emit an event with causality tracking."""
        clock = get_clock()
        now = clock.now()

        self._sequence += 1

        if root_id is None:
            root_id = generate_id()

        event = EventEnvelope(
            event_id=generate_id(),
            event_type=event_type,
            schema_version="2.0.0",
            actor_id=actor_id,
            authority_grant_id=authority_grant_id,
            causality={
                "root_id": root_id,
                "parent_id": parent_id or "",
                "sequence": self._sequence,
            },
            target=target,
            payload_hash=payload_hash(payload),
            environment=environment,
            timestamp=now.isoformat(),
            result=result or {},
        )

        self._events.append(event)
        self._by_id[event.event_id] = event
        if root_id not in self._by_root:
            self._by_root[root_id] = []
        self._by_root[root_id].append(event.event_id)

        return event

    def get_event(self, event_id: str) -> Optional[EventEnvelope]:
        return self._by_id.get(event_id)

    def get_causal_chain(self, root_id: str) -> list[EventEnvelope]:
        """Get all events in a causal chain."""
        event_ids = self._by_root.get(root_id, [])
        return [self._by_id[eid] for eid in event_ids if eid in self._by_id]

    def detect_orphans(self) -> list[str]:
        """Detect events with parent_id pointing to non-existent events."""
        orphans = []
        for event in self._events:
            parent = event.causality.get("parent_id", "")
            if parent and parent not in self._by_id:
                orphans.append(event.event_id)
        return orphans

    def detect_cycles(self) -> list[str]:
        """Detect causal cycles."""
        # Simple cycle detection: if A's parent is B and B's parent is A
        cycles = []
        for event in self._events:
            parent_id = event.causality.get("parent_id", "")
            if parent_id:
                parent = self._by_id.get(parent_id)
                if parent:
                    grandparent = parent.causality.get("parent_id", "")
                    if grandparent == event.event_id:
                        cycles.append(event.event_id)
        return cycles

    @property
    def events(self) -> list:
        return list(self._events)

    @property
    def event_count(self) -> int:
        return len(self._events)
