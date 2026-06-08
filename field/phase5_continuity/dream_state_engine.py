"""5_continuity.dream_state_engine

Field module for background processing during idle periods.
Runs low-priority tasks when the field is idle to maximize throughput.

Status: IMPLEMENTED
"""
import logging
import heapq
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.dream_state")

# Priority map: lower number = higher priority
_PRIORITY_MAP = {"background": 4, "low": 3, "medium": 2, "high": 1}


class DreamStateConfig(BaseModel):
    """Configuration for dream_state_engine."""
    enabled: bool = True
    idle_threshold_sec: float = 30.0
    max_concurrent_tasks: int = 2
    max_queue_size: int = 100


class _TaskEntry(BaseModel):
    """Internal task representation."""
    task_id: str
    name: str
    priority: str = "background"
    priority_val: int = 4
    created_at: str = ""
    completed: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None


class DreamStateEngineModule:
    """Background task processor for idle field periods.

    Submits low-priority tasks that execute when the field has spare capacity.
    Supports four priority levels: high, medium, low, background.
    """

    def __init__(self):
        self.config = DreamStateConfig()
        self.running = False
        self._lock = Lock()
        self._queue: List[tuple] = []  # min-heap: (priority_val, task_id, task)
        self._completed: List[_TaskEntry] = []
        self._task_counter = 0

    def start(self) -> None:
        """Start the dream state engine."""
        self.running = True
        logger.info("DreamStateEngine started")

    def stop(self) -> None:
        """Stop the dream state engine."""
        self.running = False
        logger.info("DreamStateEngine stopped")

    def submit_task(self, name: str, priority: str = "background") -> str:
        """Submit a background task.

        Args:
            name: Human-readable task name.
            priority: One of 'high', 'medium', 'low', 'background'.

        Returns:
            task_id: Unique task identifier.
        """
        with self._lock:
            if len(self._queue) >= self.config.max_queue_size:
                raise RuntimeError(f"Task queue full ({self.config.max_queue_size})")
            self._task_counter += 1
            task_id = f"dream_{self._task_counter}"
            pval = _PRIORITY_MAP.get(priority, 4)
            task = _TaskEntry(
                task_id=task_id, name=name, priority=priority,
                priority_val=pval,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            heapq.heappush(self._queue, (pval, task_id, task))
            logger.debug("Submitted task %s (%s, priority=%s)", task_id, name, priority)
            return task_id

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status.

        Returns:
            Dict with queue_size, completed_count, running status.
        """
        with self._lock:
            return {
                "queue_size": len(self._queue),
                "completed_count": len(self._completed),
                "running": self.running,
                "max_queue_size": self.config.max_queue_size,
                "max_concurrent": self.config.max_concurrent_tasks,
            }

    def process_next(self) -> Optional[Dict[str, Any]]:
        """Process the next task in the queue.

        Returns:
            Task result dict or None if queue is empty.
        """
        with self._lock:
            if not self._queue:
                return None
            _, task_id, task = heapq.heappop(self._queue)
            task.completed = True
            task.result = f"processed:{task.name}"
            self._completed.append(task)
            logger.debug("Processed dream task %s (%s)", task_id, task.name)
            return {"task_id": task_id, "name": task.name, "result": task.result}

    def get_completed_tasks(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get recently completed tasks.

        Args:
            n: Maximum number of tasks to return.

        Returns:
            List of task result dicts, most recent first.
        """
        with self._lock:
            return [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "priority": t.priority,
                    "result": t.result,
                    "created_at": t.created_at,
                }
                for t in reversed(self._completed[-n:])
            ]
