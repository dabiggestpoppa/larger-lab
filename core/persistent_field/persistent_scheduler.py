"""
O7-B9: PersistentScheduler
===========================
Schedule long-running tasks.

Manages background operational tasks: health checks, topology snapshots,
memory persistence, replay compression, entropy scans.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger("persistent_field.scheduler")


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ScheduledTask:
    """A scheduled background task."""
    task_id: str
    task_type: str  # health_check, topology_snapshot, memory_persist, replay_compress, entropy_scan
    priority: str = TaskPriority.NORMAL
    interval_seconds: float = 300.0
    status: str = TaskStatus.PENDING
    last_run: str = ""
    next_run: str = ""
    run_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.next_run:
            self.next_run = datetime.now(timezone.utc).isoformat()


class PersistentScheduler:
    """
    Manage background operational tasks.

    Tasks: health checks, topology snapshots, memory persistence,
    replay compression, entropy scans.
    """

    DEFAULT_TASKS = [
        {"task_type": "health_check", "priority": TaskPriority.HIGH, "interval_seconds": 60},
        {"task_type": "topology_snapshot", "priority": TaskPriority.NORMAL, "interval_seconds": 300},
        {"task_type": "memory_persist", "priority": TaskPriority.HIGH, "interval_seconds": 120},
        {"task_type": "entropy_scan", "priority": TaskPriority.NORMAL, "interval_seconds": 180},
        {"task_type": "replay_compress", "priority": TaskPriority.LOW, "interval_seconds": 600},
    ]

    def __init__(self):
        self._lock = threading.RLock()
        self._tasks: dict[str, ScheduledTask] = {}
        self._init_default_tasks()

    def _init_default_tasks(self) -> None:
        """Initialize default scheduled tasks."""
        for task_def in self.DEFAULT_TASKS:
            task_id = f"task_{task_def['task_type']}"
            self._tasks[task_id] = ScheduledTask(
                task_id=task_id,
                task_type=task_def["task_type"],
                priority=task_def["priority"],
                interval_seconds=task_def["interval_seconds"],
            )

    def get_due_tasks(self) -> list[dict[str, Any]]:
        """Get tasks that are due for execution."""
        now = datetime.now(timezone.utc)
        due = []

        with self._lock:
            for task in self._tasks.values():
                if task.status == TaskStatus.RUNNING:
                    continue
                try:
                    next_run = datetime.fromisoformat(task.next_run)
                    if now >= next_run:
                        due.append({
                            "task_id": task.task_id,
                            "task_type": task.task_type,
                            "priority": task.priority,
                            "run_count": task.run_count,
                        })
                except (ValueError, TypeError):
                    due.append({
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "priority": task.priority,
                        "run_count": task.run_count,
                    })

        # Sort by priority
        priority_order = {TaskPriority.CRITICAL: 0, TaskPriority.HIGH: 1, TaskPriority.NORMAL: 2, TaskPriority.LOW: 3}
        due.sort(key=lambda t: priority_order.get(t["priority"], 99))
        return due

    def complete_task(self, task_id: str, success: bool = True) -> None:
        """Mark a task as complete."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.COMPLETE if success else TaskStatus.FAILED
                task.last_run = datetime.now(timezone.utc).isoformat()
                task.run_count += 1
                # Schedule next run
                next_time = datetime.now(timezone.utc).timestamp() + task.interval_seconds
                task.next_run = datetime.fromtimestamp(next_time, tz=timezone.utc).isoformat()
                task.status = TaskStatus.PENDING

    def get_status(self) -> dict[str, Any]:
        """Get scheduler status."""
        with self._lock:
            tasks = list(self._tasks.values())
            return {
                "total_tasks": len(tasks),
                "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
                "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
                "due_now": len(self.get_due_tasks()),
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "task_type": t.task_type,
                        "priority": t.priority,
                        "status": t.status,
                        "run_count": t.run_count,
                        "interval_seconds": t.interval_seconds,
                    }
                    for t in tasks
                ],
            }
