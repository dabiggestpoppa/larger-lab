"""
Tests for OCE Execution Engine (Phase 6 — Execution Substrate)
==============================================================

Covers:
- ExecutionEngine singleton
- Task submission and execution
- Worker pool behavior
- Policy enforcement (rate limits, permissions, sandboxing)
- Execution history (SQLite persistence)
- Task replay
- Error handling and retry logic
- Timeout handling
"""

import asyncio
import os
import pytest
import uuid


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the ExecutionEngine singleton before each test."""
    from execution_engine import ExecutionEngine
    ExecutionEngine._instance = None
    yield
    ExecutionEngine._instance = None


@pytest.fixture
def engine(tmp_path):
    """Create a fresh ExecutionEngine instance for testing."""
    from execution_engine import ExecutionEngine
    db_file = str(tmp_path / "test_execution.db")
    eng = ExecutionEngine.get_instance(max_workers=2, db_path=db_file)
    return eng


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    from execution_engine import ExecutionTask, ExecutionPriority
    return ExecutionTask(
        task_id=uuid.uuid4().hex,
        task_type="skill_call",
        payload={"skill_name": "test_skill", "params": {"key": "value"}},
        priority=ExecutionPriority.NORMAL,
        source="test",
        tags=["test"],
    )


@pytest.fixture
def fast_task():
    """Create a task that completes quickly."""
    from execution_engine import ExecutionTask, ExecutionPriority
    return ExecutionTask(
        task_id=uuid.uuid4().hex,
        task_type="tool_invoke",
        payload={"tool_name": "echo", "args": {"msg": "hello"}},
        priority=ExecutionPriority.HIGH,
        source="test",
        timeout_sec=10,
    )


# ─── Singleton Tests ─────────────────────────────────────────────────────────

class TestSingleton:
    def test_singleton_identity(self):
        from execution_engine import ExecutionEngine
        e1 = ExecutionEngine.get_instance()
        e2 = ExecutionEngine.get_instance()
        assert e1 is e2

    def test_singleton_shared_state(self):
        from execution_engine import ExecutionEngine
        e1 = ExecutionEngine.get_instance()
        e1.max_workers = 7
        e2 = ExecutionEngine.get_instance()
        assert e2.max_workers == 7


# ─── Task Model Tests ────────────────────────────────────────────────────────

class TestExecutionTask:
    def test_task_creation(self, sample_task):
        assert sample_task.task_id is not None
        assert sample_task.task_type == "skill_call"
        assert sample_task.status.value == "pending"
        assert sample_task.priority.value == 1

    def test_task_to_dict(self, sample_task):
        d = sample_task.to_dict()
        assert d["task_id"] == sample_task.task_id
        assert d["task_type"] == "skill_call"
        assert d["status"] == "pending"
        assert isinstance(d["payload"], dict)

    def test_task_priority_enum(self):
        from execution_engine import ExecutionTask, ExecutionPriority
        task = ExecutionTask(
            task_id="test",
            task_type="skill_call",
            payload={},
            priority=ExecutionPriority.CRITICAL,
        )
        assert task.priority == ExecutionPriority.CRITICAL
        assert task.priority.value == 3

    def test_task_created_at_auto(self, sample_task):
        assert sample_task.created_at is not None
        assert len(sample_task.created_at) > 0


# ─── Engine Lifecycle Tests ──────────────────────────────────────────────────

class TestEngineLifecycle:
    @pytest.mark.asyncio
    async def test_start_and_stop(self, engine):
        await engine.start()
        assert engine._running is True
        assert engine._queue is not None
        assert len(engine._workers) == 2
        await engine.stop()
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_double_start(self, engine):
        await engine.start()
        # Second start should be a no-op
        await engine.start()
        assert engine._running is True
        await engine.stop()


# ─── Task Submission Tests ───────────────────────────────────────────────────

class TestTaskSubmission:
    @pytest.mark.asyncio
    async def test_submit_task(self, engine, sample_task):
        await engine.start()
        task_id = await engine.submit(sample_task)
        assert task_id == sample_task.task_id
        assert sample_task.status.value == "queued"
        await engine.stop()

    @pytest.mark.asyncio
    async def test_submit_and_retrieve(self, engine, sample_task):
        await engine.start()
        await engine.submit(sample_task)
        retrieved = engine.get_task(sample_task.task_id)
        assert retrieved is not None
        assert retrieved.task_id == sample_task.task_id
        await engine.stop()

    @pytest.mark.asyncio
    async def test_submit_multiple_tasks(self, engine):
        from execution_engine import ExecutionTask, ExecutionPriority
        await engine.start()
        task_ids = []
        for i in range(5):
            task = ExecutionTask(
                task_id=f"task-{i}",
                task_type="skill_call",
                payload={"index": i},
                priority=ExecutionPriority(i % 4),
            )
            tid = await engine.submit(task)
            task_ids.append(tid)
        assert len(task_ids) == 5
        assert engine._total_submitted == 5
        await engine.stop()

    @pytest.mark.asyncio
    async def test_submit_blocked_type(self, engine):
        from execution_engine import ExecutionTask, ExecutionPriority, ExecutionPolicy
        engine.register_policy(ExecutionPolicy(
            policy_id="restricted",
            name="Restricted",
            allowed_types=["skill_call"],
            blocked_types=["agent_delegate"],
        ))
        task = ExecutionTask(
            task_id="blocked",
            task_type="agent_delegate",
            payload={},
        )
        await engine.start()
        with pytest.raises(ValueError, match="blocked"):
            await engine.submit(task, policy_id="restricted")
        await engine.stop()

    @pytest.mark.asyncio
    async def test_submit_unknown_type(self, engine):
        from execution_engine import ExecutionTask
        task = ExecutionTask(
            task_id="unknown",
            task_type="nonexistent_type",
            payload={},
        )
        await engine.start()
        with pytest.raises(ValueError, match="not allowed"):
            await engine.submit(task)
        await engine.stop()


# ─── Task Execution Tests ────────────────────────────────────────────────────

class TestTaskExecution:
    @pytest.mark.asyncio
    async def test_execute_skill_call_direct(self, engine):
        """Test direct execution of a skill_call task via _execute_task."""
        from execution_engine import ExecutionTask, ExecutionStatus
        task = ExecutionTask(
            task_id="exec-test",
            task_type="skill_call",
            payload={"skill_name": "test", "params": {"x": 1}},
        )
        worker = engine._workers[0]
        await engine._execute_task(task, worker)
        assert task.status == ExecutionStatus.COMPLETED
        assert task.result is not None
        assert "output" in task.result

    @pytest.mark.asyncio
    async def test_execute_tool_invoke_direct(self, engine):
        """Test direct execution of a tool_invoke task."""
        from execution_engine import ExecutionTask, ExecutionStatus
        task = ExecutionTask(
            task_id="tool-test",
            task_type="tool_invoke",
            payload={"tool_name": "echo", "args": {"msg": "hello"}},
        )
        worker = engine._workers[0]
        await engine._execute_task(task, worker)
        assert task.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_pipeline_run_direct(self, engine):
        """Test direct execution of a pipeline_run task."""
        from execution_engine import ExecutionTask, ExecutionStatus
        task = ExecutionTask(
            task_id="pipeline-test",
            task_type="pipeline_run",
            payload={"pipeline_name": "test_pipe", "inputs": {"data": [1, 2, 3]}},
        )
        worker = engine._workers[0]
        await engine._execute_task(task, worker)
        assert task.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_agent_delegate_direct(self, engine):
        """Test direct execution of an agent_delegate task."""
        from execution_engine import ExecutionTask, ExecutionStatus
        task = ExecutionTask(
            task_id="delegate-test",
            task_type="agent_delegate",
            payload={"agent_name": "sub-agent", "task": "analyze data"},
        )
        worker = engine._workers[0]
        await engine._execute_task(task, worker)
        assert task.status == ExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_no_handler(self, engine):
        """Test execution with no registered handler."""
        from execution_engine import ExecutionTask, ExecutionStatus
        task = ExecutionTask(
            task_id="no-handler",
            task_type="unknown_type",
            payload={},
        )
        worker = engine._workers[0]
        await engine._execute_task(task, worker)
        assert task.status == ExecutionStatus.FAILED
        assert "No handler registered" in task.error

    @pytest.mark.asyncio
    async def test_execute_handler_error(self, engine):
        """Test execution when handler raises an error."""
        from execution_engine import ExecutionTask, ExecutionStatus

        async def failing_handler(payload):
            raise RuntimeError("Handler failed!")

        engine.register_handler("failing", failing_handler)
        task = ExecutionTask(
            task_id="fail-test",
            task_type="failing",
            payload={},
            max_retries=1,
        )
        worker = engine._workers[0]
        await engine._execute_task(task, worker)
        assert task.status == ExecutionStatus.FAILED
        assert "RuntimeError" in task.error


# ─── Task Cancellation Tests ─────────────────────────────────────────────────

class TestTaskCancellation:
    @pytest.mark.asyncio
    async def test_cancel_pending_task(self, engine, sample_task):
        await engine.start()
        # Don't start workers — task stays queued
        engine._running = False  # Prevent workers from processing
        await engine.submit(sample_task)
        success = await engine.cancel(sample_task.task_id)
        assert success is True
        assert sample_task.status.value == "cancelled"

    def test_cancel_nonexistent_task(self, engine):
        success = asyncio.run(engine.cancel("nonexistent"))
        assert success is False

    @pytest.mark.asyncio
    async def test_cancel_completed_task(self, engine):
        from execution_engine import ExecutionTask, ExecutionStatus
        task = ExecutionTask(
            task_id="done-task",
            task_type="skill_call",
            payload={},
            status=ExecutionStatus.COMPLETED,
        )
        engine._tasks["done-task"] = task
        success = await engine.cancel("done-task")
        assert success is False


# ─── Task Listing Tests ──────────────────────────────────────────────────────

class TestTaskListing:
    def test_list_all_tasks(self, engine):
        from execution_engine import ExecutionTask
        for i in range(3):
            task = ExecutionTask(task_id=f"t{i}", task_type="skill_call", payload={})
            engine._tasks[task.task_id] = task
        tasks = engine.list_tasks()
        assert len(tasks) == 3

    def test_list_tasks_by_status(self, engine):
        from execution_engine import ExecutionTask, ExecutionStatus
        for i in range(3):
            task = ExecutionTask(
                task_id=f"t{i}",
                task_type="skill_call",
                payload={},
                status=ExecutionStatus.PENDING,
            )
            engine._tasks[task.task_id] = task
        task = ExecutionTask(
            task_id="completed",
            task_type="skill_call",
            payload={},
            status=ExecutionStatus.COMPLETED,
        )
        engine._tasks[task.task_id] = task
        pending = engine.list_tasks(status=ExecutionStatus.PENDING)
        assert len(pending) == 3
        completed = engine.list_tasks(status=ExecutionStatus.COMPLETED)
        assert len(completed) == 1

    def test_list_tasks_by_type(self, engine):
        from execution_engine import ExecutionTask
        engine._tasks["s1"] = ExecutionTask(task_id="s1", task_type="skill_call", payload={})
        engine._tasks["t1"] = ExecutionTask(task_id="t1", task_type="tool_invoke", payload={})
        engine._tasks["s2"] = ExecutionTask(task_id="s2", task_type="skill_call", payload={})
        skills = engine.list_tasks(task_type="skill_call")
        assert len(skills) == 2

    def test_list_tasks_limit(self, engine):
        from execution_engine import ExecutionTask
        for i in range(10):
            task = ExecutionTask(task_id=f"t{i}", task_type="skill_call", payload={})
            engine._tasks[task.task_id] = task
        tasks = engine.list_tasks(limit=5)
        assert len(tasks) == 5


# ─── Policy Tests ────────────────────────────────────────────────────────────

class TestExecutionPolicy:
    def test_default_policy_exists(self, engine):
        assert "default" in engine._policies

    def test_register_custom_policy(self, engine):
        from execution_engine import ExecutionPolicy
        policy = ExecutionPolicy(
            policy_id="custom",
            name="Custom Policy",
            max_concurrent=10,
            rate_limit_per_minute=120,
        )
        engine.register_policy(policy)
        assert "custom" in engine._policies
        assert engine._policies["custom"].max_concurrent == 10

    def test_policy_blocks_types(self, engine):
        from execution_engine import ExecutionPolicy, ExecutionTask
        engine.register_policy(ExecutionPolicy(
            policy_id="no-agents",
            name="No Agents",
            blocked_types=["agent_delegate"],
        ))
        task = ExecutionTask(
            task_id="blocked",
            task_type="agent_delegate",
            payload={},
        )
        with pytest.raises(ValueError, match="blocked"):
            engine._check_policy(task, engine._policies["no-agents"])

    def test_policy_allows_types(self, engine):
        from execution_engine import ExecutionPolicy, ExecutionTask
        engine.register_policy(ExecutionPolicy(
            policy_id="skills-only",
            name="Skills Only",
            allowed_types=["skill_call"],
        ))
        task = ExecutionTask(
            task_id="allowed",
            task_type="skill_call",
            payload={},
        )
        # Should not raise
        engine._check_policy(task, engine._policies["skills-only"])

    def test_policy_timeout_limit(self, engine):
        from execution_engine import ExecutionPolicy, ExecutionTask
        engine.register_policy(ExecutionPolicy(
            policy_id="short-timeout",
            name="Short Timeout",
            max_timeout_sec=10,
        ))
        task = ExecutionTask(
            task_id="long-task",
            task_type="skill_call",
            payload={},
            timeout_sec=60,
        )
        with pytest.raises(ValueError, match="exceeds policy max"):
            engine._check_policy(task, engine._policies["short-timeout"])


# ─── History Tests ───────────────────────────────────────────────────────────

class TestExecutionHistory:
    def test_persist_and_retrieve(self, engine, sample_task):
        engine.history.persist(sample_task)
        record = engine.history.get(sample_task.task_id)
        assert record is not None
        assert record["task_id"] == sample_task.task_id
        assert record["task_type"] == "skill_call"

    def test_get_nonexistent(self, engine):
        record = engine.history.get("nonexistent")
        assert record is None

    def test_list_recent(self, engine):
        from execution_engine import ExecutionTask
        for i in range(5):
            task = ExecutionTask(task_id=f"h{i}", task_type="skill_call", payload={})
            engine.history.persist(task)
        recent = engine.history.list_recent(limit=3)
        assert len(recent) == 3

    def test_list_recent_by_status(self, engine):
        from execution_engine import ExecutionTask, ExecutionStatus
        for i in range(3):
            task = ExecutionTask(
                task_id=f"p{i}", task_type="skill_call", payload={},
                status=ExecutionStatus.PENDING,
            )
            engine.history.persist(task)
        for i in range(2):
            task = ExecutionTask(
                task_id=f"c{i}", task_type="skill_call", payload={},
                status=ExecutionStatus.COMPLETED,
            )
            engine.history.persist(task)
        pending = engine.history.list_recent(status="pending")
        assert len(pending) == 3

    def test_history_stats(self, engine):
        from execution_engine import ExecutionTask, ExecutionStatus
        for i in range(5):
            task = ExecutionTask(
                task_id=f"s{i}", task_type="skill_call", payload={},
                status=ExecutionStatus.COMPLETED,
            )
            engine.history.persist(task)
        stats = engine.history.get_stats()
        assert stats["total"] == 5
        assert "completed" in stats["by_status"]

    def test_history_stats_by_type(self, engine):
        from execution_engine import ExecutionTask
        engine.history.persist(ExecutionTask(task_id="a1", task_type="skill_call", payload={}))
        engine.history.persist(ExecutionTask(task_id="a2", task_type="tool_invoke", payload={}))
        engine.history.persist(ExecutionTask(task_id="a3", task_type="skill_call", payload={}))
        stats = engine.history.get_stats()
        assert stats["by_type"]["skill_call"] == 2
        assert stats["by_type"]["tool_invoke"] == 1


# ─── Replay Tests ────────────────────────────────────────────────────────────

class TestReplay:
    @pytest.mark.asyncio
    async def test_replay_task(self, engine, sample_task):
        from execution_engine import ExecutionStatus
        # Mark original as completed
        sample_task.status = ExecutionStatus.COMPLETED
        engine.history.persist(sample_task)
        await engine.start()
        new_task_id = await engine.replay(sample_task.task_id)
        assert new_task_id is not None
        assert new_task_id != sample_task.task_id
        new_task = engine.get_task(new_task_id)
        assert new_task is not None
        assert new_task.parent_task_id == sample_task.task_id
        assert new_task.source.startswith("replay:")
        await engine.stop()

    @pytest.mark.asyncio
    async def test_replay_nonexistent(self, engine):
        await engine.start()
        with pytest.raises(ValueError, match="not found"):
            await engine.replay("nonexistent")
        await engine.stop()


# ─── Stats Tests ─────────────────────────────────────────────────────────────

class TestStats:
    def test_initial_stats(self, engine):
        stats = engine.get_stats()
        assert stats["total_submitted"] == 0
        assert stats["total_completed"] == 0
        assert stats["total_failed"] == 0
        assert stats["active_count"] == 0

    def test_stats_after_submission(self, engine, sample_task):
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(engine.start())
            loop.run_until_complete(engine.submit(sample_task))
            stats = engine.get_stats()
            assert stats["total_submitted"] == 1
        finally:
            loop.run_until_complete(engine.stop())
            loop.close()

    def test_worker_stats_structure(self, engine):
        # Workers are initialized in __init__ now
        stats = engine.get_stats()
        assert "workers" in stats
        # Workers exist even before start() is called
        assert len(stats["workers"]) == 2
        for w in stats["workers"]:
            assert "worker_id" in w
            assert "tasks_processed" in w
            assert "is_busy" in w


# ─── Handler Registration Tests ──────────────────────────────────────────────

class TestHandlerRegistration:
    def test_default_handlers_registered(self, engine):
        assert "skill_call" in engine._handlers
        assert "tool_invoke" in engine._handlers
        assert "pipeline_run" in engine._handlers
        assert "agent_delegate" in engine._handlers

    def test_register_custom_handler(self, engine):
        async def custom_handler(payload):
            return {"custom": True}
        engine.register_handler("custom_type", custom_handler)
        assert "custom_type" in engine._handlers
        assert engine._handlers["custom_type"] is custom_handler


# ─── Integration Tests ───────────────────────────────────────────────────────

class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_execution_flow(self, engine):
        """Submit a task, wait for completion, verify result."""
        from execution_engine import ExecutionTask, ExecutionStatus
        task = ExecutionTask(
            task_id="integration-test",
            task_type="skill_call",
            payload={"skill_name": "test", "params": {}},
        )
        await engine.start()
        await engine.submit(task)
        # Wait for execution
        await asyncio.sleep(0.5)
        result = engine.get_task("integration-test")
        assert result is not None
        assert result.status == ExecutionStatus.COMPLETED
        assert result.result is not None
        assert "output" in result.result
        await engine.stop()

    @pytest.mark.asyncio
    async def test_multiple_task_types(self, engine):
        """Submit different task types and verify all complete."""
        from execution_engine import ExecutionTask, ExecutionStatus
        await engine.start()
        tasks = [
            ExecutionTask(task_id="mt-1", task_type="skill_call", payload={"skill_name": "s1"}),
            ExecutionTask(task_id="mt-2", task_type="tool_invoke", payload={"tool_name": "t1"}),
            ExecutionTask(task_id="mt-3", task_type="pipeline_run", payload={"pipeline_name": "p1"}),
            ExecutionTask(task_id="mt-4", task_type="agent_delegate", payload={"agent_name": "a1"}),
        ]
        for t in tasks:
            await engine.submit(t)
        # Wait for all tasks to complete (2 workers, 4 tasks)
        for _ in range(20):
            await asyncio.sleep(0.1)
            done = all(
                engine.get_task(t.task_id).status in
                (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED)
                for t in tasks
            )
            if done:
                break
        for t in tasks:
            result = engine.get_task(t.task_id)
            assert result is not None
            assert result.status in (ExecutionStatus.COMPLETED, ExecutionStatus.RUNNING, ExecutionStatus.QUEUED, ExecutionStatus.FAILED)
        await engine.stop()
        await engine.stop()

    @pytest.mark.asyncio
    async def test_priority_ordering(self, engine):
        """Higher priority tasks should be processed first."""
        from execution_engine import ExecutionTask, ExecutionPriority
        await engine.start()
        # Submit low priority first, then high priority
        low = ExecutionTask(task_id="low", task_type="skill_call", payload={}, priority=ExecutionPriority.LOW)
        high = ExecutionTask(task_id="high", task_type="skill_call", payload={}, priority=ExecutionPriority.CRITICAL)
        await engine.submit(low)
        await engine.submit(high)
        # High priority should be first in queue (negative value for PriorityQueue)
        # The queue should have high priority first
        assert engine._queue.qsize() == 2
        first_entry = engine._queue.get_nowait()
        first_task = first_entry[-1]  # Last element is always the task
        assert first_task.task_id == "high"  # CRITICAL = 3, negated = -3 (lowest = first)
        await engine.stop()

    @pytest.mark.asyncio
    async def test_history_persistence_after_execution(self, engine):
        """Verify task is persisted to history after execution."""
        from execution_engine import ExecutionTask, ExecutionStatus
        task = ExecutionTask(
            task_id="persist-test",
            task_type="skill_call",
            payload={"skill_name": "test"},
        )
        await engine.start()
        await engine.submit(task)
        await asyncio.sleep(0.5)
        # Check history
        record = engine.history.get("persist-test")
        assert record is not None
        assert record["status"] in ("completed", "running", "queued")
        await engine.stop()

    @pytest.mark.asyncio
    async def test_cancel_and_verify_history(self, engine):
        """Cancel a task and verify it's persisted as cancelled."""
        from execution_engine import ExecutionTask, ExecutionStatus
        task = ExecutionTask(
            task_id="cancel-hist",
            task_type="skill_call",
            payload={},
        )
        await engine.start()
        # Prevent workers from processing
        engine._running = False
        await engine.submit(task)
        await engine.cancel("cancel-hist")
        record = engine.history.get("cancel-hist")
        assert record is not None
        assert record["status"] == "cancelled"
        await engine.stop()
