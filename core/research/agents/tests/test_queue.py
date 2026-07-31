"""
Tests for L3.7 — SQLite-backed research task queue.

8 tests covering:
1. Enqueue task
2. Dequeue task (respects concurrency limit)
3. Mark complete
4. Mark failed with retry
5. Abandon after max retries
6. Get running/pending counts
7. List tasks by status
8. Max concurrent enforcement
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from core.research.agents.queue import ResearchTask, TaskQueue


@pytest.fixture
def temp_queue():
    """Create a task queue with a temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_queue.db"
        queue = TaskQueue(db_path)
        yield queue


@pytest.fixture
def sample_task():
    return ResearchTask(
        query="test query for agent orchestration",
        domains=["agent_orchestration"],
        priority=3,
    )


class TestQueueEnqueue:
    """Test 1: Enqueue task."""

    def test_enqueue_returns_id(self, temp_queue, sample_task):
        task_id = temp_queue.enqueue(sample_task)
        assert task_id is not None
        assert len(task_id) > 0

    def test_enqueue_sets_pending_status(self, temp_queue, sample_task):
        task_id = temp_queue.enqueue(sample_task)
        assert temp_queue.get_pending_count() == 1


class TestQueueDequeue:
    """Test 2: Dequeue task."""

    def test_dequeue_returns_task(self, temp_queue, sample_task):
        temp_queue.enqueue(sample_task)
        task = temp_queue.dequeue()
        assert task is not None
        assert task.query == "test query for agent orchestration"

    def test_dequeue_marks_running(self, temp_queue, sample_task):
        temp_queue.enqueue(sample_task)
        temp_queue.dequeue()
        assert temp_queue.get_running_count() == 1
        assert temp_queue.get_pending_count() == 0

    def test_dequeue_empty_returns_none(self, temp_queue):
        assert temp_queue.dequeue() is None


class TestQueueComplete:
    """Test 3: Mark complete."""

    def test_mark_complete(self, temp_queue, sample_task):
        task_id = temp_queue.enqueue(sample_task)
        temp_queue.dequeue()
        assert temp_queue.mark_complete(task_id, result={"finding": "test"}) is True

    def test_complete_frees_slot(self, temp_queue, sample_task):
        task_id = temp_queue.enqueue(sample_task)
        temp_queue.dequeue()
        temp_queue.mark_complete(task_id)
        assert temp_queue.get_running_count() == 0


class TestQueueFail:
    """Test 4: Mark failed with retry."""

    def test_mark_failed_increments_retry(self, temp_queue, sample_task):
        task_id = temp_queue.enqueue(sample_task)
        temp_queue.dequeue()
        assert temp_queue.mark_failed(task_id, "test error") is True
        # mark_failed sets status to 'failed'; retry() re-queues
        assert temp_queue.retry(task_id) is True
        assert temp_queue.get_pending_count() == 1

    def test_failed_task_re_queued(self, temp_queue, sample_task):
        task_id = temp_queue.enqueue(sample_task)
        temp_queue.dequeue()
        temp_queue.mark_failed(task_id, "error 1")
        # Retry to re-queue
        temp_queue.retry(task_id)
        # Should be able to dequeue again
        task = temp_queue.dequeue()
        assert task is not None


class TestQueueAbandon:
    """Test 5: Abandon after max retries."""

    def test_abandon_after_max_retries(self, temp_queue, sample_task):
        task_id = temp_queue.enqueue(sample_task)
        
        # Fail 3 times (max_retries = 2, so 3rd fail = auto-abandoned)
        for i in range(3):
            temp_queue.dequeue()
            temp_queue.mark_failed(task_id, f"error {i+1}")
        
        # After 3 fails, should be abandoned (mark_failed auto-abandons when retries exceeded)
        tasks = temp_queue.list_tasks(status="abandoned")
        assert len(tasks) == 1
        assert tasks[0].retry_count >= 2


class TestQueueCounts:
    """Test 6: Get running/pending counts."""

    def test_counts_initially_zero(self, temp_queue):
        assert temp_queue.get_running_count() == 0
        assert temp_queue.get_pending_count() == 0

    def test_counts_after_operations(self, temp_queue, sample_task):
        temp_queue.enqueue(sample_task)
        assert temp_queue.get_pending_count() == 1
        
        temp_queue.dequeue()
        assert temp_queue.get_running_count() == 1
        assert temp_queue.get_pending_count() == 0


class TestQueueList:
    """Test 7: List tasks by status."""

    def test_list_all_tasks(self, temp_queue, sample_task):
        temp_queue.enqueue(sample_task)
        tasks = temp_queue.list_tasks()
        assert len(tasks) == 1

    def test_list_by_status(self, temp_queue, sample_task):
        temp_queue.enqueue(sample_task)
        
        pending = temp_queue.list_tasks(status="pending")
        assert len(pending) == 1
        
        running = temp_queue.list_tasks(status="running")
        assert len(running) == 0


class TestQueueConcurrency:
    """Test 8: Max concurrent enforcement."""

    def test_max_concurrent_limit(self, temp_queue):
        # Enqueue 5 tasks
        for i in range(5):
            task = ResearchTask(query=f"task {i}", priority=3)
            temp_queue.enqueue(task)
        
        # Dequeue up to max (3)
        dequeued = []
        for _ in range(5):
            task = temp_queue.dequeue()
            if task:
                dequeued.append(task)
        
        # Should only get 3 (MAX_CONCURRENT)
        assert len(dequeued) == 3
        assert temp_queue.get_running_count() == 3

    def test_dequeue_blocked_at_max(self, temp_queue):
        for i in range(3):
            task = ResearchTask(query=f"task {i}", priority=3)
            temp_queue.enqueue(task)
            temp_queue.dequeue()
        
        # All 3 slots full, next dequeue should return None
        extra_task = ResearchTask(query="extra", priority=5)
        temp_queue.enqueue(extra_task)
        assert temp_queue.dequeue() is None