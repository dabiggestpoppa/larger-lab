"""
O-1-B8: ObserverSession
========================
Session continuity management.

Tracks observer sessions across time, handles session creation,
resumption, and archival.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SESSION_DIR = REPO_ROOT / "data" / "observer" / "sessions"
SESSION_FILE = SESSION_DIR / "active_sessions.json"


@dataclass
class SessionData:
    """Single observer session."""
    session_id: str
    observer_id: str
    created_at: str
    last_active: str
    status: str = "active"  # "active", "paused", "closed"
    context: dict[str, Any] = field(default_factory=dict)
    task_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ObserverSession:
    """
    Manages observer session lifecycle.
    
    Sessions track continuity across interactions and enable
    resumption after restarts.
    """

    def __init__(self):
        self._lock = threading.RLock()
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, SessionData] = {}
        self._active_session_id: str | None = None
        self._load()

    @property
    def active_session(self) -> SessionData | None:
        if self._active_session_id:
            return self._sessions.get(self._active_session_id)
        return None

    def create_session(
        self,
        observer_id: str = "primary",
        context: dict[str, Any] | None = None,
    ) -> SessionData:
        """Create a new session."""
        with self._lock:
            session = SessionData(
                session_id=f"session_{uuid.uuid4().hex[:8]}",
                observer_id=observer_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                last_active=datetime.now(timezone.utc).isoformat(),
                context=context or {},
            )
            self._sessions[session.session_id] = session
            self._active_session_id = session.session_id
            self._persist()
            return session

    def resume_session(self, session_id: str) -> SessionData | None:
        """Resume an existing session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.status != "closed":
                session.status = "active"
                session.last_active = datetime.now(timezone.utc).isoformat()
                self._active_session_id = session_id
                self._persist()
                return session
            return None

    def close_session(self, session_id: str | None = None) -> None:
        """Close a session."""
        with self._lock:
            sid = session_id or self._active_session_id
            if sid and sid in self._sessions:
                self._sessions[sid].status = "closed"
                self._sessions[sid].last_active = datetime.now(timezone.utc).isoformat()
                if self._active_session_id == sid:
                    self._active_session_id = None
                self._persist()

    def touch_session(self, task_increment: int = 1) -> None:
        """Update active session's last active time."""
        with self._lock:
            session = self.active_session
            if session:
                session.last_active = datetime.now(timezone.utc).isoformat()
                session.task_count += task_increment
                self._persist()

    def get_all_sessions(self) -> list[dict[str, Any]]:
        """Get all sessions as dicts."""
        with self._lock:
            return [
                {
                    "session_id": s.session_id,
                    "observer_id": s.observer_id,
                    "created_at": s.created_at,
                    "last_active": s.last_active,
                    "status": s.status,
                    "task_count": s.task_count,
                    "context": s.context,
                }
                for s in self._sessions.values()
            ]

    def _persist(self) -> None:
        try:
            data = {
                sid: {
                    "session_id": s.session_id,
                    "observer_id": s.observer_id,
                    "created_at": s.created_at,
                    "last_active": s.last_active,
                    "status": s.status,
                    "context": s.context,
                    "task_count": s.task_count,
                    "metadata": s.metadata,
                }
                for sid, s in self._sessions.items()
            }
            data["_active_session_id"] = self._active_session_id
            SESSION_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load(self) -> None:
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text())
                self._active_session_id = data.pop("_active_session_id", None)
                for sid, sdata in data.items():
                    self._sessions[sid] = SessionData(**sdata)
            except Exception:
                pass
