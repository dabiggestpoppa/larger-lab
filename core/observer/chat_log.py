"""
O-1-B10: ChatLog
==================
Persistent conversation log for the Primary Observer.

Stores: user messages, observer responses, session context,
task metadata, and conversation history for field analysis.

Storage: JSON with session-based organization.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from collections import deque

CHAT_LOG_DIR = Path("C:/Users/wifik/Desktop/projects/larger-lab/data/observer/chat")
CHAT_LOG_FILE = CHAT_LOG_DIR / "chat_log.json"
MAX_HISTORY = 1000  # Maximum messages per session


@dataclass
class ChatMessage:
    """Single chat message."""
    message_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    session_id: str
    task_domain: Optional[str] = None
    complexity: Optional[str] = None
    observer_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatSession:
    """Chat session with message history."""
    session_id: str
    start_time: str
    last_active: str
    messages: list[dict] = field(default_factory=list)
    message_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0


class ChatLog:
    """
    Persistent conversation log for the Primary Observer.
    
    Stores all user-observer conversations with metadata for:
    - Continuity analysis
    - Field learning from dialogue patterns
    - Session reconstruction
    - Context inheritance across conversations
    """

    _instance: ChatLog | None = None

    def __init__(self):
        self._lock = threading.RLock()
        CHAT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, ChatSession] = {}
        self._current_session_id: str = ""
        self._load()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        try:
            if CHAT_LOG_FILE.exists():
                CHAT_LOG_FILE.unlink()
        except Exception:
            pass
        cls._instance = None

    def _get_or_create_session(self, session_id: Optional[str] = None) -> ChatSession:
        """Get existing session or create new one."""
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id]
            
            # Create new session
            new_session_id = session_id or f"chat_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            session = ChatSession(
                session_id=new_session_id,
                start_time=datetime.now(timezone.utc).isoformat(),
                last_active=datetime.now(timezone.utc).isoformat(),
            )
            self._sessions[new_session_id] = session
            self._current_session_id = new_session_id
            return session

    def add_message(
        self,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        task_domain: Optional[str] = None,
        complexity: Optional[str] = None,
        observer_metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Add a message to the chat log."""
        with self._lock:
            session = self._get_or_create_session(session_id)
            message_id = f"msg_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            
            message = {
                "message_id": message_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session.session_id,
                "task_domain": task_domain,
                "complexity": complexity,
                "observer_metadata": observer_metadata or {},
            }
            
            session.messages.append(message)
            session.message_count += 1
            session.last_active = datetime.now(timezone.utc).isoformat()
            
            if role == "user":
                session.user_message_count += 1
            elif role == "assistant":
                session.assistant_message_count += 1
            
            # Trim if too long
            if len(session.messages) > MAX_HISTORY:
                session.messages = session.messages[-MAX_HISTORY:]
            
            self._persist()
            return message_id

    def get_session_messages(self, session_id: str) -> list[dict]:
        """Get all messages for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            return list(session.messages) if session else []

    def get_recent_messages(self, limit: int = 50) -> list[dict]:
        """Get recent messages across all sessions."""
        with self._lock:
            all_messages = []
            for session in self._sessions.values():
                all_messages.extend(session.messages)
            
            # Sort by timestamp and return most recent
            all_messages.sort(key=lambda m: m["timestamp"], reverse=True)
            return all_messages[:limit]

    def get_current_session(self) -> str:
        """Get current session ID."""
        return self._current_session_id

    def search_messages(self, query: str) -> list[dict]:
        """Search messages by content."""
        with self._lock:
            results = []
            query_lower = query.lower()
            for session in self._sessions.values():
                for msg in session.messages:
                    if query_lower in msg["content"].lower():
                        results.append(msg)
            return results

    def get_session_summary(self, session_id: Optional[str] = None) -> dict[str, Any]:
        """Get summary for a session."""
        with self._lock:
            session = self._sessions.get(session_id or self._current_session_id)
            if not session:
                return {}
            
            return {
                "session_id": session.session_id,
                "start_time": session.start_time,
                "last_active": session.last_active,
                "message_count": session.message_count,
                "user_message_count": session.user_message_count,
                "assistant_message_count": session.assistant_message_count,
                "recent_messages": session.messages[-20:] if session.messages else [],
            }

    def to_dict(self) -> dict[str, Any]:
        """Export all chat log data."""
        with self._lock:
            return {
                "current_session_id": self._current_session_id,
                "sessions": {
                    sid: {
                        "session_id": s.session_id,
                        "start_time": s.start_time,
                        "last_active": s.last_active,
                        "message_count": s.message_count,
                        "user_message_count": s.user_message_count,
                        "assistant_message_count": s.assistant_message_count,
                        "messages": s.messages[-50:],  # Last 50 per session
                    }
                    for sid, s in self._sessions.items()
                },
            }

    def _persist(self) -> None:
        """Persist chat log to disk."""
        try:
            data = {
                "current_session_id": self._current_session_id,
                "sessions": {
                    sid: {
                        "session_id": s.session_id,
                        "start_time": s.start_time,
                        "last_active": s.last_active,
                        "message_count": s.message_count,
                        "user_message_count": s.user_message_count,
                        "assistant_message_count": s.assistant_message_count,
                        "messages": s.messages[-100:],  # Persist last 100 per session
                    }
                    for sid, s in self._sessions.items()
                },
            }
            CHAT_LOG_DIR.mkdir(parents=True, exist_ok=True)
            CHAT_LOG_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load(self) -> None:
        """Load chat log from disk."""
        if CHAT_LOG_FILE.exists():
            try:
                data = json.loads(CHAT_LOG_FILE.read_text())
                self._current_session_id = data.get("current_session_id", "")
                
                for sid, sdata in data.get("sessions", {}).items():
                    session = ChatSession(
                        session_id=sdata["session_id"],
                        start_time=sdata["start_time"],
                        last_active=sdata["last_active"],
                        messages=sdata.get("messages", []),
                        message_count=sdata.get("message_count", 0),
                        user_message_count=sdata.get("user_message_count", 0),
                        assistant_message_count=sdata.get("assistant_message_count", 0),
                    )
                    self._sessions[sid] = session
            except Exception:
                pass

    def reload(self) -> None:
        """Force reload from disk. Clears current state and re-reads the file."""
        self._sessions.clear()
        self._current_session_id = ""
        self._load()


# Global accessor
_chat_log_instance: ChatLog | None = None


def get_chat_log() -> ChatLog:
    """Get the global ChatLog instance."""
    global _chat_log_instance
    if _chat_log_instance is None:
        _chat_log_instance = ChatLog()
    return _chat_log_instance