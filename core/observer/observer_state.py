"""
O-1-B2: ObserverState
=====================
Persistent observer state management.

Tracks: active_task, session_context, runtime_state, observer_health,
continuity_score, active_agents, entropy_state, repair_state.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
STATE_DIR = REPO_ROOT / "data" / "observer"
STATE_FILE = STATE_DIR / "observer_state.json"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    FAILED = "failed"


@dataclass
class ObserverStateData:
    """Complete observer state snapshot."""
    observer_id: str = "primary"
    active_task: str | None = None
    session_context: dict[str, Any] = field(default_factory=dict)
    runtime_state: dict[str, Any] = field(default_factory=dict)
    observer_health: str = HealthStatus.HEALTHY.value
    continuity_score: float = 1.0
    active_agents: list[str] = field(default_factory=list)
    entropy_state: dict[str, Any] = field(default_factory=dict)
    repair_state: dict[str, Any] = field(default_factory=dict)
    last_updated: str = ""
    version: int = 0

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now(timezone.utc).isoformat()


class ObserverState:
    """Thread-safe observer state with disk persistence."""

    _instance: ObserverState | None = None
    _lock = threading.Lock()

    def __new__(cls) -> ObserverState:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._state = ObserverStateData()
        self._listeners: list[Callable] = []
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        self._load()

    @property
    def data(self) -> ObserverStateData:
        return self._state

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._state, key, default)

    def set(self, key: str, value: Any) -> None:
        setattr(self._state, key, value)
        self._state.last_updated = datetime.now(timezone.utc).isoformat()
        self._state.version += 1
        self._persist()
        self._notify(key, value)

    def update(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self._state, k, v)
        self._state.last_updated = datetime.now(timezone.utc).isoformat()
        self._state.version += 1
        self._persist()
        for k, v in kwargs.items():
            self._notify(k, v)

    def set_health(self, status: HealthStatus) -> None:
        self.set("observer_health", status.value)

    def set_continuity_score(self, score: float) -> None:
        self.set("continuity_score", max(0.0, min(1.0, score)))

    def add_active_agent(self, agent_id: str) -> None:
        if agent_id not in self._state.active_agents:
            self._state.active_agents.append(agent_id)
            self._persist()

    def remove_active_agent(self, agent_id: str) -> None:
        if agent_id in self._state.active_agents:
            self._state.active_agents.remove(agent_id)
            self._persist()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self._state)

    def subscribe(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def _notify(self, key: str, value: Any) -> None:
        for cb in self._listeners:
            try:
                cb(key, value)
            except Exception:
                pass

    def _persist(self) -> None:
        try:
            STATE_FILE.write_text(json.dumps(self.to_dict(), indent=2))
        except Exception:
            pass

    def _load(self) -> None:
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                self._state = ObserverStateData(**data)
            except Exception:
                pass

    def reset(self) -> None:
        self._state = ObserverStateData()
        self._persist()


def get_observer_state() -> ObserverState:
    return ObserverState()
