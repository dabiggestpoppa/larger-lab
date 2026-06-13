"""
Phase 1.6.1 — Orchestration Controller

Central execution authority. The brainstem of OCE.
Receives all requests, decides execution path, routes to subsystems.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.orchestration")


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class TaskState(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETE = "complete"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A unit of cognitive work."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    title: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    state: TaskState = TaskState.PENDING
    parent_id: Optional[str] = None  # For recursive/sub tasks
    subtask_ids: List[str] = field(default_factory=list)
    assigned_agent: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    recursion_depth: int = 0
    max_recursion: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds()
        return None

    @property
    def is_terminal(self) -> bool:
        return self.state in (TaskState.COMPLETE, TaskState.FAILED, TaskState.CANCELLED)


@dataclass
class OrchestrationController:
    """
    Central execution authority for OCE.
    
    Receives tasks from users or internal sources, routes them to the
    appropriate subsystem (synthesis, retrieval, ingestion, etc.),
    and tracks execution state.
    """

    max_concurrent_tasks: int = 5
    max_recursion_depth: int = 5
    _tasks: Dict[str, Task] = field(default_factory=dict)
    _running: List[str] = field(default_factory=list)

    def submit_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        input_data: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> Task:
        """Submit a new task for execution."""
        task = Task(
            title=title,
            description=description,
            priority=priority,
            input_data=input_data or {},
            parent_id=parent_id,
            max_recursion=self.max_recursion_depth,
        )
        self._tasks[task.task_id] = task
        logger.info(f"Task submitted: [{priority.value}] {title}")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_tasks_by_state(self, state: TaskState) -> List[Task]:
        return [t for t in self._tasks.values() if t.state == state]

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        return [t for t in self._tasks.values() if t.priority == priority]

    def update_state(self, task_id: str, state: TaskState, **kwargs) -> Optional[Task]:
        """Update task state and optional fields."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        task.state = state
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        if state == TaskState.RUNNING and not task.started_at:
            task.started_at = datetime.now(timezone.utc).isoformat()
        if state in (TaskState.COMPLETE, TaskState.FAILED):
            task.completed_at = datetime.now(timezone.utc).isoformat()

        return task

    def create_subtask(
        self,
        parent_id: str,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Optional[Task]:
        """Create a subtask under a parent task."""
        parent = self._tasks.get(parent_id)
        if not parent:
            logger.warning(f"Parent task {parent_id} not found")
            return None

        if parent.recursion_depth >= parent.max_recursion:
            logger.warning(f"Max recursion depth reached for {parent_id}")
            return None

        subtask = Task(
            title=title,
            description=description,
            priority=priority,
            parent_id=parent_id,
            recursion_depth=parent.recursion_depth + 1,
            max_recursion=parent.max_recursion,
        )
        self._tasks[subtask.task_id] = subtask
        parent.subtask_ids.append(subtask.task_id)
        return subtask

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all task states."""
        states = {}
        for task in self._tasks.values():
            state_name = task.state.value
            states[state_name] = states.get(state_name, 0) + 1

        return {
            "total_tasks": len(self._tasks),
            "states": states,
            "pending": len(self.get_tasks_by_state(TaskState.PENDING)),
            "running": len(self.get_tasks_by_state(TaskState.RUNNING)),
            "complete": len(self.get_tasks_by_state(TaskState.COMPLETE)),
            "failed": len(self.get_tasks_by_state(TaskState.FAILED)),
        }

    def route_task(self, task: Task) -> str:
        """
        Route a task to the appropriate subsystem.
        
        Returns the target subsystem name.
        """
        title_lower = task.title.lower()
        desc_lower = task.description.lower()

        # Route based on task content
        if any(w in title_lower for w in ["research", "synthesize", "report", "analysis"]):
            return "synthesis"
        elif any(w in title_lower for w in ["ingest", "fetch", "retrieve", "openalex"]):
            return "ingestion"
        elif any(w in title_lower for w in ["search", "recall", "find", "query"]):
            return "retrieval"
        elif any(w in title_lower for w in ["plan", "decompose", "schedule"]):
            return "planning"
        elif any(w in title_lower for w in ["verify", "validate", "check", "reflect"]):
            return "reflection"
        elif any(w in title_lower for w in ["govern", "limit", "permission", "safety"]):
            return "governance"
        else:
            return "general"
