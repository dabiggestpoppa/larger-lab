"""
5_continuity.session_bridger
=============================
Bridges context between sessions to maintain continuity across time.

Tracks active sessions, persists context, and enables smooth handoffs
between sessions so the field never loses its thread.
"""

import json
import logging
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.session_bridger")


class SessionBridgeConfig(BaseModel):
    """Configuration for session_bridger."""
    enabled: bool = True
    max_sessions: int = 100
    session_timeout_sec: int = 3600
    context_persistence_path: str = "data/sessions.json"


class SessionInfo(BaseModel):
    session_id: str
    context: Dict[str, Any] = Field(default_factory=dict)
    started_at: str = ""
    last_active: str = ""
    status: str = "active"  # active, bridged, expired, ended
    handoff_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BridgeRecord(BaseModel):
    bridge_id: str
    session_a: str
    session_b: str
    bridged_at: str = ""
    context_transferred: List[str] = Field(default_factory=list)
    success: bool = True


class SessionBridgerModule:
    """session_bridger field module — bridges sessions across time."""

    def __init__(self):
        self.config = SessionBridgeConfig()
        self.running = False
        self._sessions: OrderedDict[str, SessionInfo] = OrderedDict()
        self._bridge_history: List[BridgeRecord] = []
        self._lock = Lock()
        self._data_dir = Path("field/data")
        self._persist_path = self._data_dir / "sessions.json"

    def start(self) -> None:
        self.running = True
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._load_sessions()
        logger.info("SessionBridgeModule started — %d sessions loaded", len(self._sessions))

    def stop(self) -> None:
        self._persist_sessions()
        self.running = False
        logger.info("SessionBridgeModule stopped")

    # ── Session Management ──────────────────────────────────────

    def start_session(self, session_id: str, context: Optional[Dict[str, Any]] = None) -> SessionInfo:
        """Start a new session with initial context."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            # Evict expired sessions if at capacity
            self._evict_expired()
            if len(self._sessions) >= self.config.max_sessions and session_id not in self._sessions:
                oldest = next(iter(self._sessions))
                self._sessions.pop(oldest)
                logger.debug("Evicted oldest session: %s", oldest)

            session = SessionInfo(
                session_id=session_id,
                context=context or {},
                started_at=now,
                last_active=now,
                status="active",
            )
            self._sessions[session_id] = session
            logger.info("Session started: %s", session_id)
            return session

    def end_session(self, session_id: str) -> bool:
        """End a session and persist its final context."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].status = "ended"
                self._sessions[session_id].last_active = datetime.now(timezone.utc).isoformat()
                self._persist_sessions()
                logger.info("Session ended: %s", session_id)
                return True
            logger.warning("Session not found: %s", session_id)
            return False

    def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the context for a specific session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.last_active = datetime.now(timezone.utc).isoformat()
                return dict(session.context)
            return None

    def update_session_context(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update context for an active session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.status == "active":
                session.context.update(updates)
                session.last_active = datetime.now(timezone.utc).isoformat()
                return True
            return False

    def get_active_sessions(self) -> List[SessionInfo]:
        """Get all currently active sessions."""
        with self._lock:
            return [s for s in self._sessions.values() if s.status == "active"]

    # ── Session Bridging ────────────────────────────────────────

    def bridge_sessions(self, session_a: str, session_b: str) -> Optional[BridgeRecord]:
        """Bridge two sessions — transfer context from A to B."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            sa = self._sessions.get(session_a)
            sb = self._sessions.get(session_b)
            if not sa or not sb:
                logger.warning("Cannot bridge — session not found: %s / %s", session_a, session_b)
                return None

            transferred = []
            for key, value in sa.context.items():
                if key not in sb.context:
                    sb.context[key] = value
                    transferred.append(key)

            sb.handoff_count += 1
            sa.status = "bridged"
            sb.last_active = now

            bridge = BridgeRecord(
                bridge_id=f"bridge_{session_a}_{session_b}_{int(datetime.now(timezone.utc).timestamp())}",
                session_a=session_a,
                session_b=session_b,
                bridged_at=now,
                context_transferred=transferred,
                success=True,
            )
            self._bridge_history.append(bridge)
            logger.info("Bridged %s -> %s (%d keys)", session_a, session_b, len(transferred))
            return bridge

    def get_bridge_history(self, n: int = 20) -> List[BridgeRecord]:
        """Get recent bridge records."""
        with self._lock:
            return list(self._bridge_history[-n:])

    # ── Persistence ─────────────────────────────────────────────

    def _persist_sessions(self):
        """Persist sessions to disk."""
        try:
            data = {
                sid: s.model_dump() for sid, s in self._sessions.items()
                if s.status == "active"
            }
            self._persist_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error("Failed to persist sessions: %s", e)

    def _load_sessions(self):
        """Load sessions from disk."""
        try:
            if self._persist_path.exists():
                data = json.loads(self._persist_path.read_text())
                for sid, sdata in data.items():
                    self._sessions[sid] = SessionInfo(**sdata)
                logger.info("Loaded %d sessions from disk", len(data))
        except Exception as e:
            logger.error("Failed to load sessions: %s", e)

    def _evict_expired(self):
        """Evict sessions that have exceeded timeout."""
        timeout = timedelta(seconds=self.config.session_timeout_sec)
        now = datetime.now(timezone.utc)
        expired = []
        for sid, s in self._sessions.items():
            try:
                last = datetime.fromisoformat(s.last_active)
                if now - last > timeout:
                    expired.append(sid)
            except (ValueError, TypeError):
                expired.append(sid)
        for sid in expired:
            self._sessions[sid].status = "expired"
            self._sessions.move_to_end(sid)
            logger.debug("Session expired: %s", sid)
