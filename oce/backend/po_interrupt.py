"""
PO Interrupt Handler — cancels in-flight PO generations.

Provides the ability to interrupt ongoing streaming responses,
cancel long-running tool calls, and gracefully abort multi-step
agent operations.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, Set

logger = logging.getLogger("oce.po_interrupt")


class InterruptSignal(Exception):
    """Raised when an interrupt is requested for a session/request."""

    def __init__(self, session_id: str, reason: str = "user_interrupt"):
        self.session_id = session_id
        self.reason = reason
        super().__init__(f"Interrupt: {reason} for session {session_id}")


class CancelScope:
    """A cancellable scope wrapping an async operation."""

    def __init__(self, scope_id: str):
        self.scope_id = scope_id
        self._cancelled = False
        self._cancel_reason = ""
        self._event = asyncio.Event()

    def cancel(self, reason: str = "cancelled"):
        """Request cancellation."""
        self._cancelled = True
        self._cancel_reason = reason
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @property
    def cancel_reason(self) -> str:
        return self._cancel_reason

    async def wait_if_cancelled(self):
        """Raise InterruptSignal if cancellation was requested."""
        if self._cancelled:
            raise InterruptSignal(self.scope_id, self._cancel_reason)
        # Wait for cancellation signal (with timeout to allow checking)
        try:
            await asyncio.wait_for(self._event.wait(), timeout=0.1)
            if self._cancelled:
                raise InterruptSignal(self.scope_id, self._cancel_reason)
        except asyncio.TimeoutError:
            pass

    def reset(self):
        """Reset the scope for reuse."""
        self._cancelled = False
        self._cancel_reason = ""
        self._event.clear()


class InterruptHandler:
    """Manages interrupt signals for PO operations."""

    def __init__(self):
        self._scopes: Dict[str, CancelScope] = {}
        self._interrupt_history: list[Dict[str, Any]] = []

    def create_scope(self, scope_id: str | None = None) -> CancelScope:
        """Create a new cancellable scope."""
        scope_id = scope_id or str(uuid.uuid4())[:8]
        scope = CancelScope(scope_id)
        self._scopes[scope_id] = scope
        return scope

    def get_scope(self, scope_id: str) -> CancelScope | None:
        """Get an existing scope by ID."""
        return self._scopes.get(scope_id)

    def cancel(self, scope_id: str, reason: str = "user_interrupt"):
        """Cancel a scope by ID."""
        scope = self._scopes.get(scope_id)
        if scope:
            scope.cancel(reason)
            self._interrupt_history.append({
                "scope_id": scope_id,
                "reason": reason,
                "timestamp": self._now(),
            })
            logger.info(f"Cancelled scope {scope_id}: {reason}")

    def cancel_session(self, session_id: str, reason: str = "user_interrupt"):
        """Cancel all scopes associated with a session."""
        cancelled = []
        for scope_id, scope in list(self._scopes.items()):
            if scope_id.startswith(session_id[:8]):
                scope.cancel(reason)
                cancelled.append(scope_id)
                self._interrupt_history.append({
                    "scope_id": scope_id,
                    "reason": reason,
                    "timestamp": self._now(),
                })
        logger.info(f"Cancelled {len(cancelled)} scopes for session {session_id}")
        return cancelled

    def cancel_all(self, reason: str = "system_shutdown"):
        """Cancel all active scopes."""
        count = len(self._scopes)
        for scope in self._scopes.values():
            scope.cancel(reason)
        self._interrupt_history.append({
            "scope_id": "*",
            "reason": reason,
            "timestamp": self._now(),
        })
        logger.info(f"Cancelled all {count} scopes: {reason}")
        return count

    def cleanup(self, max_age_seconds: float = 300):
        """Remove completed/cancelled scopes older than max_age."""
        cutoff = self._now() - max_age_seconds
        expired = [
            sid for sid, scope in self._scopes.items()
            if scope.cancelled and self._now() - scope._event._loop_time > max_age_seconds
        ] if hasattr(asyncio, 'Event') else []
        for sid in expired:
            del self._scopes[sid]
        return len(expired)

    def get_status(self) -> Dict[str, Any]:
        """Get handler status."""
        return {
            "active_scopes": len(self._scopes),
            "cancelled_scopes": sum(1 for s in self._scopes.values() if s.cancelled),
            "recent_interrupts": self._interrupt_history[-10:],
        }

    @staticmethod
    def _now() -> float:
        import time
        return time.time()