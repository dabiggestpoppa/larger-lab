"""
Semantic Logger
================
Structured logging for all contradiction events.
Every contradiction event produces a structured log entry with:
- event_id, contradiction_type, observers_affected
- semantic_divergence, resolution_method, reconstruction_time
- anchor_integrity, continuity_status
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path


class SemanticLogger:
    """
    Structured logging for semantic contradiction events.
    Writes to both file and in-memory log.
    """

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = Path(log_file) if log_file else None
        self.events: List[Dict[str, Any]] = []

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_contradiction_event(self, event_id: str, contradiction_type: str,
                                 observers_affected: List[str],
                                 semantic_divergence: float,
                                 resolution_method: str,
                                 reconstruction_time: float,
                                 anchor_integrity: bool,
                                 continuity_status: str,
                                 extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log a contradiction event with all required fields.
        """
        event = {
            "event_id": event_id,
            "contradiction_type": contradiction_type,
            "observers_affected": observers_affected,
            "semantic_divergence": semantic_divergence,
            "resolution_method": resolution_method,
            "reconstruction_time": reconstruction_time,
            "anchor_integrity": anchor_integrity,
            "continuity_status": continuity_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            event["extra"] = extra

        self.events.append(event)
        self._write_to_file(event)
        return event

    def log_verification_event(self, signal_id: str, reported_state: str,
                                validated_state: str, verification_method: str,
                                observer_consensus: float, anchor_integrity: bool,
                                accepted: bool,
                                extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log a verification event (Phase 11.4.2).
        """
        event = {
            "signal_id": signal_id,
            "reported_state": reported_state,
            "validated_state": validated_state,
            "verification_method": verification_method,
            "observer_consensus": observer_consensus,
            "anchor_integrity": anchor_integrity,
            "accepted": accepted,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            event["extra"] = extra

        self.events.append(event)
        self._write_to_file(event)
        return event

    def _write_to_file(self, event: Dict[str, Any]):
        """Write event to log file."""
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event) + "\n")

    def get_events(self) -> List[Dict[str, Any]]:
        """Return all logged events."""
        return list(self.events)

    def get_events_by_type(self, contradiction_type: str) -> List[Dict[str, Any]]:
        """Return events filtered by contradiction type."""
        return [e for e in self.events if e.get("contradiction_type") == contradiction_type]

    def get_events_by_continuity_status(self, status: str) -> List[Dict[str, Any]]:
        """Return events filtered by continuity status."""
        return [e for e in self.events if e.get("continuity_status") == status]

    def clear(self):
        """Clear in-memory events (not file)."""
        self.events.clear()
