"""
O-1-B4: ContinuityMemory
=========================
Operational continuity memory (NOT chat memory).

Tracks: workflow evolution, prior orchestration, successful/failed routing,
active operational goals, user/system continuity.

Storage: JSON + lightweight vector.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = REPO_ROOT / "data" / "observer" / "memory"
MEMORY_FILE = MEMORY_DIR / "continuity_memory.json"


@dataclass
class WorkflowRecord:
    """Single workflow execution record."""
    workflow_id: str
    task_domain: str
    complexity: str
    timestamp: str
    success: bool = True
    routing_path: str = ""
    model_used: str = ""
    duration_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContinuityRecord:
    """Long-horizon continuity tracking."""
    session_id: str
    start_time: str
    last_active: str
    workflow_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    active_goals: list[str] = field(default_factory=list)
    workflow_history: list[dict] = field(default_factory=list)
    routing_patterns: dict[str, int] = field(default_factory=dict)


class ContinuityMemory:
    """
    Persistent operational continuity memory.
    
    Stores workflow outcomes, routing patterns, and operational goals
    to enable continuity across sessions and restarts.
    """

    _instance: ContinuityMemory | None = None

    def __init__(self):
        self._lock = threading.RLock()
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._record = self._load()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        # Delete persistence file
        try:
            if MEMORY_FILE.exists():
                MEMORY_FILE.unlink()
        except Exception:
            pass
        cls._instance = None


    @property
    def record(self) -> ContinuityRecord:
        return self._record

    def record_workflow(self, workflow: WorkflowRecord) -> None:
        """Record a completed workflow."""
        with self._lock:
            self._record.workflow_count += 1
            if workflow.success:
                self._record.success_count += 1
            else:
                self._record.failure_count += 1

            self._record.last_active = datetime.now(timezone.utc).isoformat()
            self._record.workflow_history.append({
                "workflow_id": workflow.workflow_id,
                "domain": workflow.task_domain,
                "complexity": workflow.complexity,
                "timestamp": workflow.timestamp,
                "success": workflow.success,
                "routing_path": workflow.routing_path,
                "model_used": workflow.model_used,
                "duration_ms": workflow.duration_ms,
                "error": workflow.error,
            })

            # Track routing patterns
            key = f"{workflow.task_domain}:{workflow.routing_path}"
            self._record.routing_patterns[key] = \
                self._record.routing_patterns.get(key, 0) + 1

            # Trim history
            if len(self._record.workflow_history) > 200:
                self._record.workflow_history = self._record.workflow_history[-200:]

            self._persist()

    def add_goal(self, goal: str) -> None:
        with self._lock:
            if goal not in self._record.active_goals:
                self._record.active_goals.append(goal)
                self._persist()

    def complete_goal(self, goal: str) -> None:
        with self._lock:
            if goal in self._record.active_goals:
                self._record.active_goals.remove(goal)
                self._persist()

    def get_routing_history(self, domain: str | None = None) -> list[dict]:
        """Get routing history, optionally filtered by domain."""
        with self._lock:
            if domain:
                return [w for w in self._record.workflow_history if w["domain"] == domain]
            return list(self._record.workflow_history)

    def get_success_rate(self, domain: str | None = None) -> float:
        """Get success rate for a domain or overall."""
        with self._lock:
            history = self.get_routing_history(domain)
            if not history:
                return 0.0
            successes = sum(1 for w in history if w["success"])
            return successes / len(history)

    def get_top_routing_patterns(self, n: int = 5) -> list[tuple[str, int]]:
        """Get most common routing patterns."""
        with self._lock:
            sorted_patterns = sorted(
                self._record.routing_patterns.items(),
                key=lambda x: x[1],
                reverse=True,
            )
            return sorted_patterns[:n]

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "session_id": self._record.session_id,
                "start_time": self._record.start_time,
                "last_active": self._record.last_active,
                "workflow_count": self._record.workflow_count,
                "success_count": self._record.success_count,
                "failure_count": self._record.failure_count,
                "active_goals": self._record.active_goals,
                "workflow_history": self._record.workflow_history[-50:],
                "routing_patterns": self._record.routing_patterns,
            }

    def _persist(self) -> None:
        try:
            data = {
                "session_id": self._record.session_id,
                "start_time": self._record.start_time,
                "last_active": self._record.last_active,
                "workflow_count": self._record.workflow_count,
                "success_count": self._record.success_count,
                "failure_count": self._record.failure_count,
                "active_goals": list(self._record.active_goals),
                "workflow_history": list(self._record.workflow_history[-50:]),
                "routing_patterns": dict(self._record.routing_patterns),
            }
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            MEMORY_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load(self) -> ContinuityRecord:
        if MEMORY_FILE.exists():
            try:
                data = json.loads(MEMORY_FILE.read_text())
                return ContinuityRecord(**data)
            except Exception:
                pass
        return ContinuityRecord(
            session_id=f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            start_time=datetime.now(timezone.utc).isoformat(),
            last_active=datetime.now(timezone.utc).isoformat(),
        )
