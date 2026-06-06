"""
PO Session — memory continuity across chat turns.

Maintains conversation context, session state, and cross-turn coherence
for the PO cognitive field. Bridges between individual chat requests
and the longer-lived OCE structural memory.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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

    def get_context(self, max_messages: int = 20, max_tokens: int = 4000) -> str:
        """Get recent conversation context as a formatted string."""
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


class SessionManager:
    """Manages multiple PO sessions."""

    def __init__(self, max_sessions: int = 100, default_ttl: int = 3600):
        self.max_sessions = max_sessions
        self.default_ttl = default_ttl
        self._sessions: Dict[str, POSession] = {}

    def create(self, session_id: str | None = None) -> POSession:
        """Create a new session."""
        if len(self._sessions) >= self.max_sessions:
            # Evict oldest
            oldest_id = min(self._sessions, key=lambda k: self._sessions[k].created_at)
            del self._sessions[oldest_id]
        session = POSession(session_id)
        self._sessions[session.session_id] = session
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

    def cleanup(self, ttl: int | None = None):
        """Remove sessions older than TTL."""
        ttl = ttl or self.default_ttl
        cutoff = time.time() - ttl
        expired = [sid for sid, s in self._sessions.items() if s.last_active < cutoff]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)