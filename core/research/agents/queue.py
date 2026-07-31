"""
L3.7 — SQLite-backed research task queue.

Manages research tasks with states: queued → running → completed | failed | abandoned.
Bounded by max concurrent tasks and retry limits.

Usage:
    queue = TaskQueue()
    task_id = queue.enqueue(task)
    task = queue.dequeue()
    queue.mark_complete(task_id, result)
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

AGENTS_DB = Path(__file__).resolve().parents[3] / "data" / "research" / "agents.db"


@dataclass
class ResearchTask:
    """A research task to be executed by a research agent."""
    id: str = ""
    gap_id: str = ""
    query: str = ""
    domains: List[str] = field(default_factory=list)
    status: str = "pending"
    priority: int = 3
    assigned_to: str = ""
    result_json: str = ""
    confidence: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    retry_count: int = 0
    error_message: str = ""
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"task_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class TaskQueue:
    """SQLite-backed task queue with bounded concurrency."""

    MAX_CONCURRENT = 3
    MAX_RETRIES = 2

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or AGENTS_DB
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(_TASK_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def enqueue(self, task: ResearchTask) -> str:
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO research_tasks 
                   (id, gap_id, query, domains, status, priority, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (task.id, task.gap_id, task.query,
                 json.dumps(task.domains), task.status, task.priority, task.created_at),
            )
            conn.commit()
            return task.id
        finally:
            conn.close()

    def dequeue(self) -> Optional[ResearchTask]:
        conn = self._get_connection()
        try:
            running = conn.execute(
                "SELECT COUNT(*) FROM research_tasks WHERE status = 'running'"
            ).fetchone()[0]
            if running >= self.MAX_CONCURRENT:
                return None
            row = conn.execute(
                """SELECT * FROM research_tasks 
                   WHERE status = 'pending' 
                   ORDER BY priority DESC, created_at ASC LIMIT 1"""
            ).fetchone()
            if not row:
                return None
            task_id = row[0]
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "UPDATE research_tasks SET status = 'running', started_at = ? WHERE id = ?",
                (now, task_id),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT * FROM research_tasks WHERE id = ?", (task_id,)
            ).fetchone()
            return self._row_to_task(updated)
        finally:
            conn.close()

    def mark_complete(self, task_id: str, result: Optional[Dict[str, Any]] = None,
                      confidence: float = 0.0, tokens: int = 0, cost: float = 0.0) -> bool:
        conn = self._get_connection()
        try:
            conn.execute(
                """UPDATE research_tasks 
                   SET status = 'completed', completed_at = ?, result_json = ?, 
                       confidence = ?, tokens_used = ?, cost_usd = ?
                   WHERE id = ?""",
                (datetime.now(timezone.utc).isoformat(),
                 json.dumps(result) if result else None,
                 confidence, tokens, cost, task_id),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def mark_failed(self, task_id: str, error: str) -> bool:
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT retry_count FROM research_tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if not row:
                return False
            retry_count = row[0] + 1
            # If max retries exceeded, abandon; otherwise mark as failed
            if retry_count > self.MAX_RETRIES:
                conn.execute(
                    """UPDATE research_tasks 
                       SET status = 'abandoned', error_message = ?, retry_count = ?
                       WHERE id = ?""",
                    (error, retry_count, task_id),
                )
            else:
                conn.execute(
                    """UPDATE research_tasks 
                       SET status = 'failed', error_message = ?, retry_count = ?
                       WHERE id = ?""",
                    (error, retry_count, task_id),
                )
            conn.commit()
            return True
        finally:
            conn.close()

    def mark_abandoned(self, task_id: str, error: str = "") -> bool:
        """Mark a task as abandoned (exceeded max retries)."""
        conn = self._get_connection()
        try:
            conn.execute(
                """UPDATE research_tasks 
                   SET status = 'abandoned', error_message = ?
                   WHERE id = ?""",
                (error, task_id),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def retry(self, task_id: str) -> bool:
        """Retry a failed task: transition from 'failed' back to 'pending'."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT status, retry_count FROM research_tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if not row:
                return False
            status, retry_count = row
            if status != 'failed':
                return False
            if retry_count > self.MAX_RETRIES:
                # Transition to abandoned instead
                conn.execute(
                    "UPDATE research_tasks SET status = 'abandoned' WHERE id = ?",
                    (task_id,),
                )
            else:
                conn.execute(
                    "UPDATE research_tasks SET status = 'pending' WHERE id = ?",
                    (task_id,),
                )
            conn.commit()
            return True
        finally:
            conn.close()

    def get_task(self, task_id: str) -> Optional[ResearchTask]:
        """Get a task by ID."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM research_tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_task(row)
        finally:
            conn.close()

    def mark_running(self, task_id: str) -> bool:
        """Mark a task as running."""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE research_tasks SET status = 'running', started_at = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), task_id),
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def get_running_count(self) -> int:
        conn = self._get_connection()
        try:
            return conn.execute(
                "SELECT COUNT(*) FROM research_tasks WHERE status = 'running'"
            ).fetchone()[0]
        finally:
            conn.close()

    def get_pending_count(self) -> int:
        conn = self._get_connection()
        try:
            return conn.execute(
                "SELECT COUNT(*) FROM research_tasks WHERE status = 'pending'"
            ).fetchone()[0]
        finally:
            conn.close()

    def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> List[ResearchTask]:
        conn = self._get_connection()
        try:
            query = "SELECT * FROM research_tasks"
            params = []
            if status:
                query += " WHERE status = ?"
                params.append(status)
            query += f" ORDER BY priority DESC, created_at DESC LIMIT {limit}"
            cursor = conn.execute(query, params)
            return [self._row_to_task(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _row_to_task(self, row) -> ResearchTask:
        return ResearchTask(
            id=row[0], gap_id=row[1], query=row[2],
            domains=json.loads(row[3]) if row[3] else [],
            status=row[4], priority=row[5], assigned_to=row[6],
            result_json=row[7], confidence=row[8], tokens_used=row[9],
            cost_usd=row[10], retry_count=row[11], error_message=row[12],
            created_at=row[13], started_at=row[14], completed_at=row[15],
        )


_TASK_SCHEMA = """
CREATE TABLE IF NOT EXISTS research_tasks (
    id TEXT PRIMARY KEY,
    gap_id TEXT,
    query TEXT NOT NULL,
    domains JSON,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 3,
    assigned_to TEXT,
    result_json TEXT,
    confidence REAL DEFAULT 0.0,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON research_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON research_tasks(priority);
"""