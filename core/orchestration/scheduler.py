"""
Phase 1.6.7 — Recursive Scheduler

Autonomous recurring cognition. Tasks that run on schedules
and can spawn new tasks recursively.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("oce.scheduler")


class ScheduleFrequency(str, Enum):
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ScheduledTask:
    """A task that runs on a schedule."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    title: str = ""
    description: str = ""
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    cron_expression: str = ""  # Optional cron expression
    is_enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    max_runs: int = 0  # 0 = unlimited
    callback: str = ""  # Name of function/handler to call
    callback_args: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SchedulerEngine:
    """
    Manages scheduled and recursive task execution.
    
    Examples:
        OpenAlex ingestion → daily
        Repo scanning → hourly
        Topology repair → nightly
        Research expansion → weekly
    """

    def __init__(self):
        self._scheduled_tasks: Dict[str, ScheduledTask] = {}
        self._running: List[str] = []

    def schedule(
        self,
        title: str,
        frequency: ScheduleFrequency,
        callback: str,
        description: str = "",
        callback_args: Optional[Dict[str, Any]] = None,
        max_runs: int = 0,
    ) -> ScheduledTask:
        """Schedule a recurring task."""
        task = ScheduledTask(
            title=title,
            description=description,
            frequency=frequency,
            callback=callback,
            callback_args=callback_args or {},
            max_runs=max_runs,
        )
        self._scheduled_tasks[task.task_id] = task
        logger.info(f"Scheduled: {title} ({frequency.value})")
        return task

    def unschedule(self, task_id: str) -> bool:
        """Remove a scheduled task."""
        if task_id in self._scheduled_tasks:
            del self._scheduled_tasks[task_id]
            return True
        return False

    def list_scheduled(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks."""
        return [
            {
                "id": t.task_id,
                "title": t.title,
                "frequency": t.frequency.value,
                "enabled": t.is_enabled,
                "run_count": t.run_count,
                "last_run": t.last_run,
            }
            for t in self._scheduled_tasks.values()
        ]

    def get_due_tasks(self) -> List[ScheduledTask]:
        """Get tasks that are due for execution."""
        now = datetime.now(timezone.utc)
        due = []
        for task in self._scheduled_tasks.values():
            if not task.is_enabled:
                continue
            if task.max_runs > 0 and task.run_count >= task.max_runs:
                continue
            # Simple frequency check
            if task.last_run:
                last = datetime.fromisoformat(task.last_run)
                elapsed = (now - last).total_seconds()
                intervals = {
                    ScheduleFrequency.MINUTELY: 60,
                    ScheduleFrequency.HOURLY: 3600,
                    ScheduleFrequency.DAILY: 86400,
                    ScheduleFrequency.WEEKLY: 604800,
                    ScheduleFrequency.MONTHLY: 2592000,
                }
                if elapsed < intervals.get(task.frequency, 86400):
                    continue
            due.append(task)
        return due

    def mark_executed(self, task_id: str):
        """Mark a task as executed."""
        task = self._scheduled_tasks.get(task_id)
        if task:
            task.last_run = datetime.now(timezone.utc).isoformat()
            task.run_count += 1

    def enable(self, task_id: str) -> bool:
        task = self._scheduled_tasks.get(task_id)
        if task:
            task.is_enabled = True
            return True
        return False

    def disable(self, task_id: str) -> bool:
        task = self._scheduled_tasks.get(task_id)
        if task:
            task.is_enabled = False
            return True
        return False
