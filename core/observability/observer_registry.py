"""
Phase 11.2-3B.1 — Runtime Observer Registry
============================================
Discovers the REAL topology — not AST structure, but runtime interaction.

Tracks:
    - Observer lifecycle (spawn, shutdown, state, entropy, repair)
    - Observer relationships (interactions, frequency, latency, sync)
    - Runtime context (task, continuity region, memory, field zone, routing)

Output: runtime_topology_registry.json
"""

from __future__ import annotations

import json
import time
import uuid
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]  # larger-lab/
EXPORTS_DIR = REPO_ROOT / "experiments" / "exports" / "topology"


class ObserverState(Enum):
    SPAWNING = "spawning"
    ACTIVE = "active"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    SHUTDOWN = "shutdown"


class InteractionType(Enum):
    MESSAGE = "message"
    SYNC = "sync"
    REPAIR = "repair"
    MEMORY = "memory"
    ROUTE = "route"
    CHAOS = "chaos"


@dataclass
class ObserverRecord:
    """Single observer's runtime state."""
    observer_id: str
    observer_type: str
    spawn_time: str
    shutdown_time: str | None
    runtime_state: str
    entropy_score: float  # 0.0-1.0
    repair_state: str
    tasks_completed: int = 0
    errors: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObserverRelationship:
    """Runtime interaction between two observers."""
    source_observer: str
    target_observer: str
    interaction_type: str
    frequency: int = 0
    latency_ms: float = 0.0
    synchronization_state: str = "unknown"
    last_interaction: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeContext:
    """Context for a runtime interaction event."""
    task_id: str
    continuity_region: str
    memory_context: str
    field_zone: str
    routing_path: list[str] = field(default_factory=list)
    timestamp: str = ""


class ObserverRegistry:
    """
    Central registry for runtime observer topology.

    Thread-safe. Designed for minimal overhead on runtime.
    All writes are async-flush to disk.
    """

    def __init__(self, auto_flush_interval: float = 30.0):
        self._observers: dict[str, ObserverRecord] = {}
        self._relationships: dict[str, ObserverRelationship] = {}
        self._contexts: list[RuntimeContext] = []
        self._lock = threading.RLock()
        self._flush_interval = auto_flush_interval
        self._dirty = False
        self._callbacks: list[Callable] = []

        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ─── Observer Lifecycle ──────────────────────────────────────────────

    def register_observer(self, observer_type: str, observer_id: str | None = None,
                          metadata: dict | None = None) -> str:
        """Register a new observer entering the field."""
        oid = observer_id or f"{observer_type}_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._observers[oid] = ObserverRecord(
                observer_id=oid,
                observer_type=observer_type,
                spawn_time=now,
                shutdown_time=None,
                runtime_state=ObserverState.SPAWNING.value,
                entropy_score=0.0,
                repair_state="idle",
                metadata=metadata or {},
            )
            self._dirty = True

        self._notify("observer_spawn", {"observer_id": oid, "type": observer_type})
        return oid

    def set_observer_state(self, observer_id: str, state: ObserverState,
                           entropy_score: float | None = None):
        """Update an observer's runtime state."""
        with self._lock:
            if observer_id in self._observers:
                obs = self._observers[observer_id]
                obs.runtime_state = state.value
                if entropy_score is not None:
                    obs.entropy_score = max(0.0, min(1.0, entropy_score))
                self._dirty = True

    def record_observer_task(self, observer_id: str, success: bool = True):
        """Record a task completion for an observer."""
        with self._lock:
            if observer_id in self._observers:
                self._observers[observer_id].tasks_completed += 1
                if not success:
                    self._observers[observer_id].errors += 1
                self._dirty = True

    def shutdown_observer(self, observer_id: str):
        """Mark an observer as shutdown."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            if observer_id in self._observers:
                self._observers[observer_id].runtime_state = ObserverState.SHUTDOWN.value
                self._observers[observer_id].shutdown_time = now
                self._dirty = True
        self._notify("observer_shutdown", {"observer_id": observer_id})

    # ─── Relationship Tracking ───────────────────────────────────────────

    def record_interaction(self, source: str, target: str,
                           interaction_type: InteractionType,
                           latency_ms: float = 0.0,
                           sync_state: str = "unknown"):
        """Record a runtime interaction between two observers."""
        key = f"{source}::{target}::{interaction_type.value}"
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            if key in self._relationships:
                rel = self._relationships[key]
                rel.frequency += 1
                rel.latency_ms = latency_ms  # latest latency
                rel.synchronization_state = sync_state
                rel.last_interaction = now
            else:
                self._relationships[key] = ObserverRelationship(
                    source_observer=source,
                    target_observer=target,
                    interaction_type=interaction_type.value,
                    frequency=1,
                    latency_ms=latency_ms,
                    synchronization_state=sync_state,
                    last_interaction=now,
                )
            self._dirty = True

    # ─── Runtime Context ─────────────────────────────────────────────────

    def record_context(self, task_id: str, continuity_region: str,
                       memory_context: str, field_zone: str,
                       routing_path: list[str] | None = None):
        """Record runtime context for an event."""
        ctx = RuntimeContext(
            task_id=task_id,
            continuity_region=continuity_region,
            memory_context=memory_context,
            field_zone=field_zone,
            routing_path=routing_path or [],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._contexts.append(ctx)
            self._dirty = True

    # ─── Queries ─────────────────────────────────────────────────────────

    def get_observer_graph(self) -> dict:
        """Get the current observer interaction graph."""
        with self._lock:
            nodes = {}
            for oid, obs in self._observers.items():
                nodes[oid] = {
                    "type": obs.observer_type,
                    "state": obs.runtime_state,
                    "entropy": obs.entropy_score,
                    "tasks": obs.tasks_completed,
                    "errors": obs.errors,
                }

            edges = []
            for key, rel in self._relationships.items():
                edges.append({
                    "source": rel.source_observer,
                    "target": rel.target_observer,
                    "type": rel.interaction_type,
                    "frequency": rel.frequency,
                    "latency_ms": rel.latency_ms,
                    "sync": rel.synchronization_state,
                })

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_observers": len(nodes),
                "total_interactions": len(edges),
                "nodes": nodes,
                "edges": edges,
            }

    def get_hotspots(self, min_entropy: float = 0.5) -> list[dict]:
        """Identify high-entropy observers (potential instability zones)."""
        with self._lock:
            return [
                {"observer_id": oid, "entropy": obs.entropy_score, "type": obs.observer_type}
                for oid, obs in self._observers.items()
                if obs.entropy_score >= min_entropy
            ]

    def get_sync_health(self) -> dict:
        """Measure overall synchronization health."""
        with self._lock:
            if not self._relationships:
                return {"status": "no_data", "sync_rate": 0.0}

            synced = sum(1 for r in self._relationships.values()
                         if r.synchronization_state == "synced")
            total = len(self._relationships)
            return {
                "status": "healthy" if synced / total > 0.8 else "degraded",
                "sync_rate": round(synced / total, 4),
                "total_relationships": total,
                "synced": synced,
                "desynced": total - synced,
            }

    # ─── Persistence ─────────────────────────────────────────────────────

    def export(self, path: Path | None = None) -> Path:
        """Export the full registry to JSON."""
        import sys
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[{ts}] REGISTRY: Starting export...", flush=True, file=sys.stderr)
        path = path or EXPORTS_DIR / "runtime_topology_registry.json"

        with self._lock:
            print(f"[{ts}] REGISTRY: Lock acquired, building data...", flush=True, file=sys.stderr)
            data = {
                "version": "0.1.0",
                "phase": "11.2-3B.1",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "observers": {oid: asdict(obs) for oid, obs in self._observers.items()},
                "relationships": {k: asdict(v) for k, v in self._relationships.items()},
                "contexts": [asdict(ctx) for ctx in self._contexts[-1000:]],
                "graph": self.get_observer_graph(),
                "sync_health": self.get_sync_health(),
                "hotspots": self.get_hotspots(),
            }
            print(f"[{ts}] REGISTRY: Data built, writing file...", flush=True, file=sys.stderr)

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        self._dirty = False
        print(f"[{ts}] REGISTRY: Export complete ({path})", flush=True, file=sys.stderr)
        return path

    # ─── Callbacks ───────────────────────────────────────────────────────

    def on_event(self, callback: Callable):
        """Register a callback for registry events."""
        self._callbacks.append(callback)

    def _notify(self, event_type: str, data: dict):
        for cb in self._callbacks:
            try:
                cb(event_type, data)
            except Exception:
                pass


# ─── Global Singleton ────────────────────────────────────────────────────

_registry: ObserverRegistry | None = None


def get_registry() -> ObserverRegistry:
    """Get or create the global observer registry."""
    global _registry
    if _registry is None:
        _registry = ObserverRegistry()
    return _registry
