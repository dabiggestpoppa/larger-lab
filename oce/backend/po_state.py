"""
PO State Persistence — durable state for the PO cognitive field.

Provides read/write access to PO's operational state, allowing the
cognitive field to persist across restarts and maintain continuity
even when the OCE backend is recycled.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.po_state")


@dataclass
class POStateSnapshot:
    """Snapshot of PO's operational state."""

    timestamp: float
    active_sessions: int = 0
    total_messages: int = 0
    total_turns: int = 0
    last_activity: float = 0.0
    cognitive_load: float = 0.0  # 0-1 scale
    memory_usage_mb: float = 0.0
    queue_depth: int = 0
    last_checkpoint: str = ""
    custom_state: Dict[str, Any] = field(default_factory=dict)


class POStateStore:
    """Persistent state store for the PO cognitive field."""

    def __init__(self, state_dir: str | Path | None = None):
        self.state_dir = Path(state_dir) if state_dir else Path(__file__).parent / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self.state_dir / "po_state.json"
        self._session_dir = self.state_dir / "sessions"
        self._session_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, Any] = {}
        self._cache_ts: float = 0.0

    # ── Global State ────────────────────────────────────────────────────

    def load_state(self) -> POStateSnapshot:
        """Load the current global state from disk."""
        if not self._state_file.exists():
            return POStateSnapshot(timestamp=time.time())

        try:
            data = json.loads(self._state_file.read_text(encoding="utf-8"))
            return POStateSnapshot(**data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"State load error: {e}, returning fresh state")
            return POStateSnapshot(timestamp=time.time())

    def save_state(self, snapshot: POStateSnapshot):
        """Persist the global state to disk."""
        snapshot.timestamp = time.time()
        data = {
            "timestamp": snapshot.timestamp,
            "active_sessions": snapshot.active_sessions,
            "total_messages": snapshot.total_messages,
            "total_turns": snapshot.total_turns,
            "last_activity": snapshot.last_activity,
            "cognitive_load": snapshot.cognitive_load,
            "memory_usage_mb": snapshot.memory_usage_mb,
            "queue_depth": snapshot.queue_depth,
            "last_checkpoint": snapshot.last_checkpoint,
            "custom_state": snapshot.custom_state,
        }
        self._state_file.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )
        self._cache = data
        self._cache_ts = time.time()

    def update_partial(self, **kwargs):
        """Update specific fields in the global state."""
        snapshot = self.load_state()
        for key, value in kwargs.items():
            if hasattr(snapshot, key):
                setattr(snapshot, key, value)
        self.save_state(snapshot)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the cached state."""
        if time.time() - self._cache_ts > 5:
            self._cache = self._state_file.read_text(encoding="utf-8") if self._state_file.exists() else "{}"
            try:
                self._cache = json.loads(self._cache) if isinstance(self._cache, str) else self._cache
            except json.JSONDecodeError:
                self._cache = {}
            self._cache_ts = time.time()
        return self._cache.get(key, default) if isinstance(self._cache, dict) else default

    # ── Session State ───────────────────────────────────────────────────

    def save_session(self, session_id: str, data: Dict[str, Any]):
        """Persist a session's state."""
        session_file = self._session_dir / f"{session_id}.json"
        data["_updated"] = time.time()
        session_file.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    def load_session(self, session_id: str) -> Dict[str, Any]:
        """Load a session's persisted state."""
        session_file = self._session_dir / f"{session_id}.json"
        if not session_file.exists():
            return {"session_id": session_id, "created": time.time()}
        try:
            return json.loads(session_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"session_id": session_id, "error": "corrupt"}

    def delete_session(self, session_id: str):
        """Remove a session's persisted state."""
        session_file = self._session_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all persisted sessions."""
        sessions = []
        for f in sorted(self._session_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sessions.append({
                    "session_id": data.get("session_id", f.stem),
                    "updated": data.get("_updated", 0),
                    "turns": data.get("turn_count", 0),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return sorted(sessions, key=lambda s: s["updated"], reverse=True)

    # ── Checkpointing ───────────────────────────────────────────────────

    def checkpoint(self, label: str = "") -> str:
        """Create a named checkpoint of current state."""
        ts = time.strftime("%Y%m%d_%H%M%S")
        checkpoint_id = f"{ts}_{label}" if label else ts
        cp_dir = self.state_dir / "checkpoints"
        cp_dir.mkdir(exist_ok=True)
        snapshot = self.load_state()
        cp_file = cp_dir / f"{checkpoint_id}.json"
        cp_file.write_text(
            json.dumps(
                {
                    "checkpoint_id": checkpoint_id,
                    "label": label,
                    "timestamp": time.time(),
                    "state": {
                        "active_sessions": snapshot.active_sessions,
                        "total_messages": snapshot.total_messages,
                        "total_turns": snapshot.total_turns,
                        "cognitive_load": snapshot.cognitive_load,
                    },
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        snapshot.last_checkpoint = checkpoint_id
        self.save_state(snapshot)
        return checkpoint_id

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore state from a named checkpoint."""
        cp_file = self.state_dir / "checkpoints" / f"{checkpoint_id}.json"
        if not cp_file.exists():
            return False
        try:
            data = json.loads(cp_file.read_text(encoding="utf-8"))
            snapshot = POStateSnapshot(
                timestamp=time.time(),
                active_sessions=data["state"]["active_sessions"],
                total_messages=data["state"]["total_messages"],
                total_turns=data["state"]["total_turns"],
                cognitive_load=data["state"]["cognitive_load"],
                last_checkpoint=checkpoint_id,
            )
            self.save_state(snapshot)
            return True
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Checkpoint restore failed: {e}")
            return False