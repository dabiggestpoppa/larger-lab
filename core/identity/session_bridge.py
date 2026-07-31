"""
Identity Session Bridge — bridges session state between interfaces.

Provides unified identity continuity across:
- Telegram (OC2)
- VTuber (Open-LLM-VTuber)
- Future interfaces (browser, API, etc.)

All interfaces read/write to the same POSessionStore.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger("core.identity.session_bridge")


class POSession:
    """Minimal session for identity bridge."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = 0.0
        self.last_active = 0.0
        self.message_count = 0


class IdentitySessionBridge:
    """
    Bridges session state between different interfaces.

    Maps surface sessions (vtuber-session-123, telegram-chat-456) to
    unified identity sessions (po-identity-789).
    """

    def __init__(self):
        self._links: Dict[str, str] = {}  # surface_session_id -> identity_session_id
        self._sessions: Dict[str, POSession] = {}

    def get_continuity(self, surface: str, surface_session_id: str) -> POSession:
        """
        Resolve a surface session to the unified identity session.

        If no link exists, creates a new identity session.
        """
        key = f"{surface}:{surface_session_id}"
        identity_id = self._links.get(key)

        if identity_id and identity_id in self._sessions:
            return self._sessions[identity_id]

        # Create new identity session
        identity_id = f"po-identity-{uuid.uuid4().hex[:8]}"
        session = POSession(identity_id)
        self._sessions[identity_id] = session
        self._links[key] = identity_id
        logger.info(f"Created identity session {identity_id} for {surface}:{surface_session_id}")
        return session

    def link(self, surface: str, surface_session_id: str, identity_session_id: str) -> None:
        """Link a surface session to a unified identity session."""
        key = f"{surface}:{surface_session_id}"
        self._links[key] = identity_session_id
        if identity_session_id not in self._sessions:
            self._sessions[identity_session_id] = POSession(identity_session_id)
        logger.info(f"Linked {key} -> {identity_session_id}")

    def get_session(self, identity_session_id: str) -> Optional[POSession]:
        """Get session by identity ID."""
        return self._sessions.get(identity_session_id)

    def get_status(self) -> Dict[str, Any]:
        """Get bridge status."""
        return {
            "total_links": len(self._links),
            "total_sessions": len(self._sessions),
            "surfaces": list(set(k.split(":")[0] for k in self._links.keys())),
        }