"""
PO Session — memory continuity across chat turns.

Maintains conversation context, session state, and cross-turn coherence
for the PO cognitive field. Bridges between individual chat requests
and the longer-lived OCE structural memory.

Persistence:
- Sessions are saved to disk (JSON) and survive server restarts.
- Sessions are NOT time-expired — they persist until explicitly reset
  or a new session is created. This is critical for the VTuber agent
  (Poala) which is used for quick chats across long idle periods.
- Session summaries are stored in StructuralMemory (SQLite) for
  long-term recall across sessions.
"""

from __future__ import annotations

import json
import time
import uuid
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.po_session")

# ─── Persistence Paths ───────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
SESSIONS_FILE = DATA_DIR / "po_sessions.json"


@dataclass
class SessionState:
    """Snapshot of PO session state."""

    session_id: str
    created_at: float
    last_active: float
    message_count: int = 0
    turn_count: int = 0
    total_tokens: int = 0
    last_topic: str = ""
    context_summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryEntry:
    """A single memory entry within a session."""

    entry_id: str
    session_id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float
    embeddings: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class POSession:
    """Manages a single PO session with memory continuity."""

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())[:12]
        self.created_at = time.time()
        self.last_active = self.created_at
        self.messages: List[MemoryEntry] = []
        self.turn_count = 0
        self.total_tokens = 0
        self._state = "active"

    def add_message(self, role: str, content: str, tags: List[str] | None = None) -> MemoryEntry:
        """Add a message to the session."""
        entry = MemoryEntry(
            entry_id=str(uuid.uuid4())[:8],
            session_id=self.session_id,
            role=role,
            content=content,
            timestamp=time.time(),
            tags=tags or [],
        )
        self.messages.append(entry)
        self.last_active = time.time()
        self.total_tokens += len(content.split())
        if role in ("user", "assistant"):
            self.turn_count += 1
        return entry

    def get_context(self, max_messages: int = 50, max_tokens: int = 8000) -> str:
        """Get recent conversation context as a formatted string.
        
        Default 50 messages / 8000 tokens — matches PO agent _max_history=50
        and provides enough context for coherent long conversations.
        """
        recent = self.messages[-max_messages:]
        chunks = []
        token_count = 0
        for msg in reversed(recent):
            tokens = len(msg.content.split())
            if token_count + tokens > max_tokens and chunks:
                break
            chunks.insert(0, f"{msg.role}: {msg.content}")
            token_count += tokens
        return "\n".join(chunks)

    def get_state(self) -> SessionState:
        """Get current session state snapshot."""
        topics = [m.content for m in self.messages[-10:] if m.role == "user"]
        return SessionState(
            session_id=self.session_id,
            created_at=self.created_at,
            last_active=self.last_active,
            message_count=len(self.messages),
            turn_count=self.turn_count,
            total_tokens=self.total_tokens,
            last_topic=topics[-1] if topics else "",
            context_summary=self.messages[-1].content if self.messages else "",
            metadata={"duration_seconds": round(time.time() - self.created_at, 1)},
        )

    def summarize(self) -> str:
        """Generate a brief summary of the session."""
        if not self.messages:
            return "(empty session)"
        user_msgs = [m for m in self.messages if m.role == "user"]
        last_user = user_msgs[-1].content if user_msgs else "no user messages"
        return f"Session {self.session_id}: {self.turn_count} turns, last: {last_user[:80]}"

    def clear(self):
        """Clear session messages (keep metadata)."""
        self.messages.clear()
        self.turn_count = 0
        self.total_tokens = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dict for disk persistence."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "turn_count": self.turn_count,
            "total_tokens": self.total_tokens,
            "state": self._state,
            "messages": [
                {
                    "entry_id": m.entry_id,
                    "session_id": m.session_id,
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "tags": m.tags,
                    "metadata": m.metadata,
                }
                for m in self.messages
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POSession":
        """Deserialize session from dict."""
        session = cls(session_id=data["session_id"])
        session.created_at = data["created_at"]
        session.last_active = data.get("last_active", session.created_at)
        session.turn_count = data.get("turn_count", 0)
        session.total_tokens = data.get("total_tokens", 0)
        session._state = data.get("state", "active")
        session.messages = [
            MemoryEntry(
                entry_id=m["entry_id"],
                session_id=m["session_id"],
                role=m["role"],
                content=m["content"],
                timestamp=m["timestamp"],
                tags=m.get("tags", []),
                metadata=m.get("metadata", {}),
            )
            for m in data.get("messages", [])
        ]
        return session


class SessionManager:
    """Manages multiple PO sessions with disk persistence.
    
    Sessions persist across server restarts — no TTL-based expiration.
    Sessions are only cleared on explicit reset or new session creation.
    """

    def __init__(self, max_sessions: int = 500):
        self.max_sessions = max_sessions
        self._sessions: Dict[str, POSession] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """Load sessions from disk on startup."""
        if SESSIONS_FILE.exists():
            try:
                data = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
                for sid, sdata in data.items():
                    try:
                        self._sessions[sid] = POSession.from_dict(sdata)
                    except Exception as e:
                        logger.warning(f"Failed to load session {sid}: {e}")
                logger.info(f"Loaded {len(self._sessions)} sessions from disk")
            except Exception as e:
                logger.warning(f"Failed to load sessions from disk: {e}")

    def _save_to_disk(self):
        """Persist all sessions to disk."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            data = {sid: s.to_dict() for sid, s in self._sessions.items()}
            SESSIONS_FILE.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Failed to save sessions to disk: {e}")

    def create(self, session_id: str | None = None) -> POSession:
        """Create a new session."""
        if len(self._sessions) >= self.max_sessions:
            # Evict oldest by last_active
            oldest_id = min(self._sessions, key=lambda k: self._sessions[k].last_active)
            del self._sessions[oldest_id]
            logger.info(f"Evicted oldest session {oldest_id} (max_sessions={self.max_sessions})")
        session = POSession(session_id)
        self._sessions[session.session_id] = session
        self._save_to_disk()
        logger.info(f"Created session {session.session_id}")
        return session

    def get(self, session_id: str) -> POSession | None:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None = None) -> POSession:
        """Get existing session or create new one."""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return [
            {
                "session_id": s.session_id,
                "created_at": s.created_at,
                "last_active": s.last_active,
                "turns": s.turn_count,
                "messages": len(s.messages),
            }
            for s in self._sessions.values()
        ]

    def add_message(self, session_id: str, role: str, content: str, tags: List[str] | None = None) -> Optional[MemoryEntry]:
        """Add a message to a session and persist."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        entry = session.add_message(role, content, tags)
        self._save_to_disk()
        return entry

    def clear_session(self, session_id: str) -> bool:
        """Clear a session's messages (keep the session alive)."""
        session = self._sessions.get(session_id)
        if not session:
            return False
        session.clear()
        self._save_to_disk()
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session entirely."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save_to_disk()
            return True
        return False

    def save(self):
        """Explicitly save all sessions to disk."""
        self._save_to_disk()
