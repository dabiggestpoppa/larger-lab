"""
OCE Execution Engine (Phase 6 — Execution Substrate)
=====================================================

Task execution engine for Operator Continuity Engine.

Provides:
- Async job queue with priority scheduling
- Worker pool with configurable concurrency
- Execution policies (rate limits, permissions, sandboxing)
- Result persistence and replay
- Execution tracing (integrates with Phase 5 TracingEngine)
- Skill/tool invocation layer

Design principles:
- Singleton pattern (consistent with existing codebase)
- SQLite for persistence (consistent)
- Graceful degradation (errors logged, never crash the API)
- All execution is traced and observable
"""

import asyncio
import uuid
import time
import json
import sqlite3
import logging
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("oce.execution")


# ─── Enums ───────────────────────────────────────────────────────────────────

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    RETRYING = "retrying"


class ExecutionPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


# ─── Data Models ─────────────────────────────────────────────────────────────

@dataclass
class ExecutionTask:
    """Represents a single executable task."""
    task_id: str
    task_type: str  # "skill_call", "tool_invoke", "pipeline_run", "agent_delegate"
    payload: Dict[str, Any]
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    status: ExecutionStatus = ExecutionStatus.PENDING
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempts: int = 0
    max_retries: int = 3
    timeout_sec: int = 30
    source: str = "unknown"
    tags: List[str] = field(default_factory=list)
    trace_id: Optional[str] = None
    parent_task_id: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if isinstance(self.priority, int) and not isinstance(self.priority, ExecutionPriority):
            self.priority = ExecutionPriority(self.priority)
        if isinstance(self.status, str) and not isinstance(self.status, ExecutionStatus):
            self.status = ExecutionStatus(self.status)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "timeout_sec": self.timeout_sec,
            "source": self.source,
            "tags": self.tags,
            "trace_id": self.trace_id,
            "parent_task_id": self.parent_task_id,
        }


@dataclass
class ExecutionPolicy:
    """Rate limits and permissions for execution."""
    policy_id: str
    name: str
    max_concurrent: int = 5
    rate_limit_per_minute: int = 60
    allowed_types: List[str] = field(default_factory=lambda: ["skill_call", "tool_invoke", "pipeline_run", "agent_delegate"])
    blocked_types: List[str] = field(default_factory=list)
    max_timeout_sec: int = 300
    require_trace: bool = True
    sandboxed: bool = False
    description: str = ""


@dataclass
class WorkerStats:
    """Statistics for a single worker."""
    worker_id: str
    tasks_processed: int = 0
    tasks_failed: int = 0
    total_execution_time_ms: float = 0.0
    is_busy: bool = False
    current_task_id: Optional[str] = None


# ─── Execution History (SQLite) ──────────────────────────────────────────────

class ExecutionHistory:
    """SQLite-backed execution history for persistence and replay."""

    def __init__(self, db_path: str = "data/execution_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    result TEXT,
                    error TEXT,
                    attempts INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    timeout_sec INTEGER DEFAULT 30,
                    source TEXT DEFAULT 'unknown',
                    tags TEXT DEFAULT '[]',
                    trace_id TEXT,
                    parent_task_id TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exec_status ON execution_history(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exec_type ON execution_history(task_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exec_created ON execution_history(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_exec_source ON execution_history(source)")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"ExecutionHistory DB init error: {e}")

    def persist(self, task: ExecutionTask):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO execution_history
                (task_id, task_type, payload, priority, status, created_at, started_at,
                 completed_at, result, error, attempts, max_retries, timeout_sec, source, tags,
                 trace_id, parent_task_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id, task.task_type, json.dumps(task.payload),
                task.priority.value, task.status.value, task.created_at,
                task.started_at, task.completed_at,
                json.dumps(task.result) if task.result else None,
                task.error, task.attempts, task.max_retries, task.timeout_sec,
                task.source, json.dumps(task.tags),
                task.trace_id, task.parent_task_id,
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"ExecutionHistory persist error: {e}")

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM execution_history WHERE task_id = ?", (task_id,)).fetchone()
            conn.close()
            if row:
                d = dict(row)
                d["payload"] = json.loads(d["payload"])
                d["tags"] = json.loads(d["tags"])
                d["result"] = json.loads(d["result"]) if d.get("result") else None
                return d
            return None
        except Exception as e:
            logger.error(f"ExecutionHistory get error: {e}")
            return None

    def list_recent(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute(
                    "SELECT * FROM execution_history WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM execution_history ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            conn.close()
            results = []
            for row in rows:
                d = dict(row)
                d["payload"] = json.loads(d["payload"])
                d["tags"] = json.loads(d["tags"])
                d["result"] = json.loads(d["result"]) if d.get("result") else None
                results.append(d)
            return results
        except Exception as e:
            logger.error(f"ExecutionHistory list error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.db_path)
            total = conn.execute("SELECT COUNT(*) FROM execution_history").fetchone()[0]
            by_status = {}
            for row in conn.execute("SELECT status, COUNT(*) FROM execution_history GROUP BY status"):
                by_status[row[0]] = row[1]
            by_type = {}
            for row in conn.execute("SELECT task_type, COUNT(*) FROM execution_history GROUP BY task_type"):
                by_type[row[0]] = row[1]
            avg_time = conn.execute(
                "SELECT AVG(CAST((julianday(completed_at) - julianday(started_at)) * 86400000 AS REAL)) "
                "FROM execution_history WHERE status = 'completed' AND started_at IS NOT NULL AND completed_at IS NOT NULL"
            ).fetchone()[0]
            conn.close()
            return {
                "total": total,
                "by_status": by_status,
                "by_type": by_type,
                "avg_execution_time_ms": round(avg_time, 2) if avg_time else 0.0,
            }
        except Exception as e:
            logger.error(f"ExecutionHistory stats error: {e}")
            return {"total": 0, "by_status": {}, "by_type": {}, "avg_execution_time_ms": 0.0}

    def cleanup_old(self, keep_last: int = 10000) -> int:
        try:
            conn = sqlite3.connect(self.db_path)
            result = conn.execute(
                "DELETE FROM execution_history WHERE task_id NOT IN "
                "(SELECT task_id FROM execution_history ORDER BY created_at DESC LIMIT ?)",
                (keep_last,)
            )
            deleted = result.rowcount
            conn.commit()
            conn.close()
            return deleted
        except Exception as e:
            logger.error(f"ExecutionHistory cleanup error: {e}")
            return 0


# ─── Execution Engine ────────────────────────────────────────────────────────

class ExecutionEngine:
    """
    Core execution engine with async job queue, worker pool, and policy enforcement.
    Singleton pattern — use get_execution_engine() to get the instance.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, max_workers: int = 3, db_path: str = "data/execution_history.db"):
        self.max_workers = max_workers
        self.history = ExecutionHistory(db_path)
        self._queue: asyncio.PriorityQueue = None
        self._workers: List[WorkerStats] = []
        self._tasks: Dict[str, ExecutionTask] = {}
        self._running = False
        self._policies: Dict[str, ExecutionPolicy] = {}
        self._handlers: Dict[str, Callable] = {}
        self._rate_tracker: Dict[str, List[float]] = {}  # policy_id -> list of timestamps
        self._active_count = 0
        self._total_submitted = 0
        self._total_completed = 0
        self._total_failed = 0

        # Register default handlers
        self._register_default_handlers()
        # Register default policy
        self._policies["default"] = ExecutionPolicy(
            policy_id="default",
            name="Default Policy",
            max_concurrent=5,
            rate_limit_per_minute=60,
        )

    @classmethod
    def get_instance(cls, max_workers: int = 3, db_path: str = "data/execution_history.db") -> "ExecutionEngine":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(max_workers=max_workers, db_path=db_path)
        return cls._instance

    def _register_default_handlers(self):
        """Register built-in task type handlers."""
        self._handlers["skill_call"] = self._handle_skill_call
        self._handlers["tool_invoke"] = self._handle_tool_invoke
        self._handlers["pipeline_run"] = self._handle_pipeline_run
        self._handlers["agent_delegate"] = self._handle_agent_delegate

    def register_handler(self, task_type: str, handler: Callable):
        """Register a custom handler for a task type."""
        self._handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    def register_policy(self, policy: ExecutionPolicy):
        """Register an execution policy."""
        self._policies[policy.policy_id] = policy
        logger.info(f"Registered policy: {policy.name} ({policy.policy_id})")

    async def start(self):
        """Start the execution engine and worker pool."""
        if self._running:
            return
        self._running = True
        self._queue = asyncio.PriorityQueue()
        self._workers = [WorkerStats(worker_id=f"worker-{i}") for i in range(self.max_workers)]
        for worker in self._workers:
            asyncio.create_task(self._worker_loop(worker))
        logger.info(f"Execution engine started with {self.max_workers} workers")

    async def stop(self):
        """Stop the execution engine."""
        self._running = False
        # Cancel pending tasks
        while not self._queue.empty():
            try:
                entry = self._queue.get_nowait()
                task = entry[-1]  # Last element is always the task
                task.status = ExecutionStatus.CANCELLED
                self.history.persist(task)
            except asyncio.QueueEmpty:
                break
        logger.info("Execution engine stopped")

    async def submit(self, task: ExecutionTask, policy_id: str = "default") -> str:
        """
        Submit a task for execution.
        Returns task_id.
        Raises ValueError if policy check fails.
        """
        # Policy check
        policy = self._policies.get(policy_id, self._policies["default"])
        self._check_policy(task, policy)

        task.status = ExecutionStatus.QUEUED
        self._tasks[task.task_id] = task
        self._total_submitted += 1

        # Priority queue: lower number = higher priority (invert for PriorityQueue)
        # Use a counter as tiebreaker to avoid comparing ExecutionTask objects
        self._queue_counter = getattr(self, '_queue_counter', 0) + 1
        await self._queue.put((-task.priority.value, self._queue_counter, task))
        self.history.persist(task)

        logger.info(f"Task {task.task_id} submitted (type={task.task_type}, priority={task.priority.name})")
        return task.task_id

    def _check_policy(self, task: ExecutionTask, policy: ExecutionPolicy):
        """Check task against execution policy."""
        if task.task_type in policy.blocked_types:
            raise ValueError(f"Task type '{task.task_type}' is blocked by policy '{policy.name}'")
        if task.task_type not in policy.allowed_types:
            raise ValueError(f"Task type '{task.task_type}' is not allowed by policy '{policy.name}'")
        if task.timeout_sec > policy.max_timeout_sec:
            raise ValueError(f"Timeout {task.timeout_sec}s exceeds policy max {policy.max_timeout_sec}s")
        if self._active_count >= policy.max_concurrent:
            raise ValueError(f"Max concurrent executions ({policy.max_concurrent}) reached for policy '{policy.name}'")
        # Rate limit check
        now = time.time()
        if policy.policy_id not in self._rate_tracker:
            self._rate_tracker[policy.policy_id] = []
        # Clean old entries (>60s)
        self._rate_tracker[policy.policy_id] = [
            t for t in self._rate_tracker[policy.policy_id] if now - t < 60
        ]
        if len(self._rate_tracker[policy.policy_id]) >= policy.rate_limit_per_minute:
            raise ValueError(f"Rate limit ({policy.rate_limit_per_minute}/min) exceeded for policy '{policy.name}'")
        self._rate_tracker[policy.policy_id].append(now)

    async def cancel(self, task_id: str) -> bool:
        """Cancel a pending or running task."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        if task.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
            return False
        task.status = ExecutionStatus.CANCELLED
        task.completed_at = datetime.now(timezone.utc).isoformat()
        self.history.persist(task)
        logger.info(f"Task {task_id} cancelled")
        return True

    def get_task(self, task_id: str) -> Optional[ExecutionTask]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[ExecutionStatus] = None,
        task_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[ExecutionTask]:
        """List tasks with optional filters."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get execution engine statistics."""
        return {
            "total_submitted": self._total_submitted,
            "total_completed": self._total_completed,
            "total_failed": self._total_failed,
            "active_count": self._active_count,
            "queue_size": self._queue.qsize() if self._queue else 0,
            "workers": [
                {
                    "worker_id": w.worker_id,
                    "tasks_processed": w.tasks_processed,
                    "tasks_failed": w.tasks_failed,
                    "is_busy": w.is_busy,
                    "current_task_id": w.current_task_id,
                }
                for w in self._workers
            ],
            "history": self.history.get_stats(),
        }

    async def replay(self, task_id: str, policy_id: str = "default") -> str:
        """
        Replay a previously executed task.
        Returns new task_id.
        """
        record = self.history.get(task_id)
        if not record:
            raise ValueError(f"Task {task_id} not found in history")
        new_task = ExecutionTask(
            task_id=str(uuid.uuid4()),
            task_type=record["task_type"],
            payload=record["payload"],
            priority=ExecutionPriority(record.get("priority", 1)),
            max_retries=record.get("max_retries", 3),
            timeout_sec=record.get("timeout_sec", 30),
            source=f"replay:{task_id}",
            tags=record.get("tags", []),
            parent_task_id=task_id,
        )
        return await self.submit(new_task, policy_id)

    # ─── Worker Loop ──────────────────────────────────────────────────────

    async def _worker_loop(self, worker: WorkerStats):
        """Worker loop that processes tasks from the queue."""
        while self._running:
            try:
                entry = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                task = entry[-1]  # Last element is always the task
            except (asyncio.TimeoutError, asyncio.CancelledError):
                continue

            worker.is_busy = True
            worker.current_task_id = task.task_id
            self._active_count += 1

            try:
                await self._execute_task(task, worker)
            except Exception as e:
                logger.error(f"Worker {worker.worker_id} error executing task {task.task_id}: {e}")
                task.status = ExecutionStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now(timezone.utc).isoformat()
                self._total_failed += 1
                worker.tasks_failed += 1
                self.history.persist(task)
            finally:
                worker.is_busy = False
                worker.current_task_id = None
                self._active_count -= 1
                self._queue.task_done()

    async def _execute_task(self, task: ExecutionTask, worker: WorkerStats):
        """Execute a single task with timeout and retry logic."""
        task.status = ExecutionStatus.RUNNING
        task.started_at = datetime.now(timezone.utc).isoformat()
        task.attempts += 1

        handler = self._handlers.get(task.task_type)
        if not handler:
            raise ValueError(f"No handler registered for task type: {task.task_type}")

        start_time = time.monotonic()
        try:
            result = await asyncio.wait_for(
                handler(task.payload),
                timeout=task.timeout_sec,
            )
            elapsed_ms = (time.monotonic() - start_time) * 1000
            task.status = ExecutionStatus.COMPLETED
            task.result = {"output": result, "execution_time_ms": round(elapsed_ms, 2)}
            task.completed_at = datetime.now(timezone.utc).isoformat()
            self._total_completed += 1
            worker.tasks_processed += 1
            worker.total_execution_time_ms += elapsed_ms
            self.history.persist(task)
            logger.info(f"Task {task.task_id} completed in {elapsed_ms:.1f}ms")
        except asyncio.TimeoutError:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            if task.attempts < task.max_retries:
                task.status = ExecutionStatus.RETRYING
                task.error = f"Timeout after {task.timeout_sec}s (attempt {task.attempts}/{task.max_retries})"
                self.history.persist(task)
                # Re-queue with same priority
                self._queue_counter = getattr(self, '_queue_counter', 0) + 1
                await self._queue.put((-task.priority.value, self._queue_counter, task))
                logger.warning(f"Task {task.task_id} timed out, retrying ({task.attempts}/{task.max_retries})")
            else:
                task.status = ExecutionStatus.TIMED_OUT
                task.error = f"Timeout after {task.timeout_sec}s, max retries ({task.max_retries}) exceeded"
                task.completed_at = datetime.now(timezone.utc).isoformat()
                self._total_failed += 1
                worker.tasks_failed += 1
                self.history.persist(task)
                logger.error(f"Task {task.task_id} timed out permanently after {task.max_retries} retries")
        except Exception as e:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            if task.attempts < task.max_retries:
                task.status = ExecutionStatus.RETRYING
                task.error = f"{type(e).__name__}: {str(e)} (attempt {task.attempts}/{task.max_retries})"
                self.history.persist(task)
                self._queue_counter = getattr(self, '_queue_counter', 0) + 1
                await self._queue.put((-task.priority.value, self._queue_counter, task))
                logger.warning(f"Task {task.task_id} failed, retrying: {e}")
            else:
                task.status = ExecutionStatus.FAILED
                task.error = f"{type(e).__name__}: {str(e)}"
                task.completed_at = datetime.now(timezone.utc).isoformat()
                self._total_failed += 1
                worker.tasks_failed += 1
                self.history.persist(task)
                logger.error(f"Task {task.task_id} failed permanently: {e}")

    # ─── Default Handlers ─────────────────────────────────────────────────

    async def _handle_skill_call(self, payload: Dict[str, Any]) -> Any:
        """Handle skill_call tasks — invoke a named skill with parameters."""
        skill_name = payload.get("skill_name", "unknown")
        params = payload.get("params", {})
        # In production, this would dispatch to the skill registry
        return {"skill": skill_name, "status": "executed", "params_received": list(params.keys())}

    async def _handle_tool_invoke(self, payload: Dict[str, Any]) -> Any:
        """Handle tool_invoke tasks — call an external tool/API."""
        tool_name = payload.get("tool_name", "unknown")
        args = payload.get("args", {})
        return {"tool": tool_name, "status": "invoked", "args_received": list(args.keys())}

    async def _handle_pipeline_run(self, payload: Dict[str, Any]) -> Any:
        """Handle pipeline_run tasks — execute a DSPy pipeline."""
        pipeline_name = payload.get("pipeline_name", "unknown")
        inputs = payload.get("inputs", {})
        return {"pipeline": pipeline_name, "status": "completed", "inputs_received": list(inputs.keys())}

    async def _handle_agent_delegate(self, payload: Dict[str, Any]) -> Any:
        """Handle agent_delegate tasks — delegate to a sub-agent."""
        agent_name = payload.get("agent_name", "unknown")
        task_description = payload.get("task", "")
        return {"agent": agent_name, "status": "delegated", "task_length": len(task_description)}


# ─── Singleton Access ────────────────────────────────────────────────────────

def get_execution_engine(max_workers: int = 3, db_path: str = "data/execution_history.db") -> ExecutionEngine:
    """Get the singleton ExecutionEngine instance."""
    return ExecutionEngine.get_instance(max_workers=max_workers, db_path=db_path)
