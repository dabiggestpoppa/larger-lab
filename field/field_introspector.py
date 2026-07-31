"""
4.1 Field Introspector — Sovereign Instrumentation
====================================================
Real-time field state inspection — every module, every agent, every event.

Provides:
- Snapshot of all field module states
- Active agent registry and status
- Event flow statistics
- Module health and heartbeat data

Singleton pattern consistent with OCE backend modules.
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.introspector")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "introspector.db"


class ModuleState(BaseModel):
    name: str
    status: str  # "active", "idle", "error", "stopped"
    last_heartbeat: str
    event_count: int = 0
    error_count: int = 0
    config_version: str = "0.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    agent_id: str
    agent_type: str
    status: str  # "connected", "disconnected", "processing", "error"
    last_seen: str
    tasks_processed: int = 0
    tasks_failed: int = 0
    current_task: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FieldSnapshot(BaseModel):
    timestamp: str
    module_count: int
    active_modules: int
    error_modules: int
    agent_count: int
    active_agents: int
    total_events_processed: int
    events_per_second: float
    event_queue_depth: int
    field_health_score: float  # 0.0 to 1.0
    modules: List[ModuleState] = Field(default_factory=list)
    agents: List[AgentState] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FieldIntrospector:
    """Singleton field introspection engine."""

    _instance: Optional["FieldIntrospector"] = None
    _lock = Lock()

    def __new__(cls) -> "FieldIntrospector":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._module_registry: Dict[str, ModuleState] = {}
        self._agent_registry: Dict[str, AgentState] = {}
        self._event_stats: Dict[str, int] = {"total": 0, "errors": 0, "queue_depth": 0}
        self._last_snapshot_time = datetime.now(timezone.utc)
        logger.info("FieldIntrospector initialized")

    def _init_db(self):
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    health_score REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS module_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    module_name TEXT NOT NULL,
                    status TEXT,
                    event_count INTEGER,
                    error_count INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snap_ts ON snapshots(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mod_ts ON module_states(timestamp)
            """)

    def register_module(self, name: str, status: str = "active", config_version: str = "0.0.0"):
        self._module_registry[name] = ModuleState(
            name=name, status=status,
            last_heartbeat=datetime.now(timezone.utc).isoformat(),
            config_version=config_version
        )

    def register_agent(self, agent_id: str, agent_type: str, status: str = "connected"):
        self._agent_registry[agent_id] = AgentState(
            agent_id=agent_id, agent_type=agent_type, status=status,
            last_seen=datetime.now(timezone.utc).isoformat()
        )

    def record_event(self, success: bool = True):
        self._event_stats["total"] += 1
        if not success:
            self._event_stats["errors"] += 1

    def set_queue_depth(self, depth: int):
        self._event_stats["queue_depth"] = depth

    def module_heartbeat(self, name: str, event_count: int = 0, error_count: int = 0):
        if name in self._module_registry:
            ms = self._module_registry[name]
            ms.last_heartbeat = datetime.now(timezone.utc).isoformat()
            ms.event_count = event_count
            ms.error_count = error_count

    def agent_heartbeat(self, agent_id: str, tasks_processed: int = 0, current_task: Optional[str] = None):
        if agent_id in self._agent_registry:
            a = self._agent_registry[agent_id]
            a.last_seen = datetime.now(timezone.utc).isoformat()
            a.tasks_processed = tasks_processed
            a.current_task = current_task

    def take_snapshot(self) -> FieldSnapshot:
        now = datetime.now(timezone.utc)
        elapsed = (now - self._last_snapshot_time).total_seconds() or 1
        eps = self._event_stats["total"] / elapsed

        active_mods = sum(1 for m in self._module_registry.values() if m.status == "active")
        error_mods = sum(1 for m in self._module_registry.values() if m.status == "error")
        active_agents = sum(1 for a in self._agent_registry.values() if a.status in ("connected", "processing"))

        total_mods = len(self._module_registry)
        total_agents = len(self._agent_registry)

        # Health score: weighted combination of module health, agent health, error rate
        module_health = active_mods / total_mods if total_mods else 1.0
        agent_health = active_agents / total_agents if total_agents else 1.0
        error_rate = self._event_stats["errors"] / self._event_stats["total"] if self._event_stats["total"] else 0.0
        health = round(module_health * 0.4 + agent_health * 0.3 + (1 - error_rate) * 0.3, 4)

        snapshot = FieldSnapshot(
            timestamp=now.isoformat(),
            module_count=total_mods,
            active_modules=active_mods,
            error_modules=error_mods,
            agent_count=total_agents,
            active_agents=active_agents,
            total_events_processed=self._event_stats["total"],
            events_per_second=round(eps, 2),
            event_queue_depth=self._event_stats["queue_depth"],
            field_health_score=health,
            modules=list(self._module_registry.values()),
            agents=list(self._agent_registry.values()),
        )

        # Persist
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO snapshots (timestamp, data, health_score) VALUES (?, ?, ?)",
                (now.isoformat(), snapshot.model_dump_json(), health),
            )
            for mod in snapshot.modules:
                conn.execute(
                    "INSERT INTO module_states (timestamp, module_name, status, event_count, error_count) VALUES (?,?,?,?,?)",
                    (now.isoformat(), mod.name, mod.status, mod.event_count, mod.error_count),
                )

        self._last_snapshot_time = now
        return snapshot

    def get_snapshot(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_module_history(self, name: str, limit: int = 20) -> List[Dict[str, Any]]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM module_states WHERE module_name = ? ORDER BY id DESC LIMIT ?",
                (name, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def to_dict(self) -> Dict[str, Any]:
        snap = self.take_snapshot()
        return snap.model_dump()