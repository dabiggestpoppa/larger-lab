""" O-4-B2: OperationalReplay ========================= Replays full orchestration history: task evolution, observer decisions, routing chains, spawned agents, topology changes, entropy spikes, repair events. """

from __future__ import annotations
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.learning.operational_replay")

@dataclass
class ReplayEvent:
    """A single event in the operational replay."""
    event_id: str
    timestamp: str
    event_type: str  # "task_start", "task_complete", "routing_change", "topology_change", "entropy_spike", "repair"
    payload: Dict[str, Any]

class OperationalReplay:
    """Records and replays operational history for debugging and learning."""
    
    def __init__(self, storage_path: str | None = None):
        self._events: List[ReplayEvent] = []
        self._storage_path = Path(storage_path) if storage_path else None
    
    def record_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Record a new operational event."""
        event = ReplayEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            payload=payload,
        )
        self._events.append(event)
        logger.info(f"Replay event recorded: {event_type} - {payload.get('trace_id', 'unknown')}")
    
    def get_events(self, event_type: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None) -> List[ReplayEvent]:
        """Filter events by type and time range."""
        filtered = self._events
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if start_time:
            filtered = [e for e in filtered if e.timestamp >= start_time]
        if end_time:
            filtered = [e for e in filtered if e.timestamp <= end_time]
        return filtered
    
    def get_timeline(self, trace_id: str) -> List[ReplayEvent]:
        """Get all events for a specific trace."""
        return [e for e in self._events if e.payload.get("trace_id") == trace_id]
    
    def save(self) -> None:
        """Persist replay history to disk."""
        if not self._storage_path:
            return
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "events": [
                {
                    "event_id": e.event_id,
                    "timestamp": e.timestamp,
                    "event_type": e.event_type,
                    "payload": e.payload,
                }
                for e in self._events
            ],
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._storage_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Operational replay saved to {self._storage_path}")
    
    def load(self) -> bool:
        """Load replay history from disk."""
        if not self._storage_path or not self._storage_path.exists():
            return False
        try:
            data = json.loads(self._storage_path.read_text())
            self._events = [
                ReplayEvent(
                    event_id=e["event_id"],
                    timestamp=e["timestamp"],
                    event_type=e["event_type"],
                    payload=e["payload"],
                )
                for e in data.get("events", [])
            ]
            logger.info(f"Operational replay loaded from {self._storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load operational replay: {e}")
            return False