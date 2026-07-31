"""
7.5 Session Engine — Session-Level Aggregation
================================================
Aggregates tick-level data into session-level summaries.

A session is a continuous period of activity (e.g. a trading session
or a work session). Computes session duration, activity density,
peak activity windows, and session quality score.

Session quality: 0.0 (dead/no activity) to 1.0 (peak performance).
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.multiscale.session_engine")


class SessionEngineConfig(BaseModel):
    """Configuration for session_engine."""
    enabled: bool = True
    max_sessions: int = 500
    session_timeout_sec: int = 1800  # 30 min gap = new session
    quality_window: int = 50


class ActivityEvent(BaseModel):
    """A single activity event within a session."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_id: str
    event_type: str
    intensity: float = 0.5  # 0.0 to 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionSummary(BaseModel):
    """Summary of a completed or active session."""
    session_id: str
    agent_id: str
    start_time: str
    end_time: str = ""
    duration_sec: float = 0.0
    event_count: int = 0
    avg_intensity: float = 0.0
    peak_intensity: float = 0.0
    peak_window_start: str = ""
    peak_window_end: str = ""
    quality_score: float = 0.0
    event_types: Dict[str, int] = Field(default_factory=dict)
    active: bool = True


class SessionEngineModule:
    """Session-level aggregation engine."""

    def __init__(self):
        self.config = SessionEngineConfig()
        self.running = False
        self._lock = Lock()
        self._sessions: Dict[str, List[ActivityEvent]] = {}  # session_id -> events
        self._session_meta: Dict[str, SessionSummary] = {}   # session_id -> summary
        self._active_sessions: Dict[str, str] = {}           # agent_id -> session_id
        self._completed: List[SessionSummary] = []

    def start(self) -> None:
        self.running = True
        logger.info("SessionEngine started")

    def stop(self) -> None:
        self.running = False
        # Close all active sessions
        with self._lock:
            for agent_id in list(self._active_sessions.keys()):
                self.end_session(agent_id)
        logger.info("SessionEngine stopped")

    def record_event(self, agent_id: str, event_type: str,
                     intensity: float = 0.5, **metadata) -> str:
        """
        Record an activity event. Auto-creates session if needed.

        Returns the event_id.
        """
        event = ActivityEvent(
            agent_id=agent_id,
            event_type=event_type,
            intensity=max(0.0, min(1.0, intensity)),
            metadata=metadata,
        )

        with self._lock:
            # Check if agent has an active session
            session_id = self._active_sessions.get(agent_id)

            if session_id:
                # Check timeout
                meta = self._session_meta.get(session_id)
                if meta:
                    last_time = datetime.fromisoformat(meta.end_time) if meta.end_time else (
                        datetime.fromisoformat(meta.start_time)
                    )
                    now = datetime.now(timezone.utc)
                    if (now - last_time).total_seconds() > self.config.session_timeout_sec:
                        # Timeout — close old, start new
                        self._close_session(session_id)
                        session_id = None

            if not session_id:
                session_id = str(uuid.uuid4())[:8]
                self._sessions[session_id] = []
                self._session_meta[session_id] = SessionSummary(
                    session_id=session_id,
                    agent_id=agent_id,
                    start_time=event.timestamp,
                )
                self._active_sessions[agent_id] = session_id
                logger.debug("New session %s for agent %s", session_id, agent_id)

            self._sessions[session_id].append(event)

            # Update meta
            meta = self._session_meta[session_id]
            meta.end_time = event.timestamp
            start = datetime.fromisoformat(meta.start_time)
            end = datetime.fromisoformat(meta.end_time)
            meta.duration_sec = (end - start).total_seconds()
            meta.event_count = len(self._sessions[session_id])
            meta.event_types[event_type] = meta.event_types.get(event_type, 0) + 1

            # Recompute intensity stats
            events = self._sessions[session_id]
            intensities = [e.intensity for e in events]
            meta.avg_intensity = round(sum(intensities) / len(intensities), 4)
            meta.peak_intensity = round(max(intensities), 4)

            # Find peak window
            if len(intensities) >= 3:
                window_size = min(5, len(intensities))
                best_avg = 0.0
                best_idx = 0
                for i in range(len(intensities) - window_size + 1):
                    w_avg = sum(intensities[i:i + window_size]) / window_size
                    if w_avg > best_avg:
                        best_avg = w_avg
                        best_idx = i
                meta.peak_window_start = events[best_idx].timestamp
                meta.peak_window_end = events[best_idx + window_size - 1].timestamp

            # Quality score: blend of intensity, density, and diversity
            density = min(meta.event_count / 100, 1.0)  # normalize to 100 events
            diversity = len(meta.event_types) / max(len(meta.event_types), 1)
            meta.quality_score = round(
                0.5 * meta.avg_intensity + 0.3 * density + 0.2 * diversity, 4
            )

            # Evict old completed sessions
            if len(self._completed) > self.config.max_sessions:
                self._completed = self._completed[-self.config.max_sessions:]

        return event.event_id

    def end_session(self, agent_id: str) -> Optional[SessionSummary]:
        """End an agent's active session."""
        with self._lock:
            session_id = self._active_sessions.pop(agent_id, None)
            if session_id:
                return self._close_session(session_id)
        return None

    def _close_session(self, session_id: str) -> Optional[SessionSummary]:
        """Close a session and produce final summary."""
        meta = self._session_meta.get(session_id)
        if meta and meta.active:
            meta.active = False
            self._completed.append(meta)
            logger.info("Session %s closed: %d events, quality=%.3f",
                        session_id, meta.event_count, meta.quality_score)
            return meta
        return None

    def get_active_session(self, agent_id: str) -> Optional[Dict]:
        """Get an agent's active session summary."""
        with self._lock:
            sid = self._active_sessions.get(agent_id)
            if sid:
                return self._session_meta[sid].model_dump()
        return None

    def get_session_history(self, limit: int = 50) -> List[Dict]:
        """Get completed session summaries."""
        with self._lock:
            return [s.model_dump() for s in self._completed[-limit:]]

    def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        with self._lock:
            active = len(self._active_sessions)
            completed = len(self._completed)
            total_events = sum(s.event_count for s in self._completed)
            avg_quality = (
                sum(s.quality_score for s in self._completed) / completed
                if completed > 0 else 0.0
            )
            return {
                "active_sessions": active,
                "completed_sessions": completed,
                "total_events_recorded": total_events,
                "avg_session_quality": round(avg_quality, 4),
                "max_sessions_stored": self.config.max_sessions,
            }
