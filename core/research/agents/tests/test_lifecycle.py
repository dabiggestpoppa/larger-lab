"""
Tests for L3.6 — Agent lifecycle manager.

6 tests covering:
1. Spawn agent
2. Heartbeat updates
3. Complete agent
4. Fail with retry
5. Abandon after max retries
6. Stale agent detection
"""

import pytest

from core.research.agents.lifecycle import AgentLifecycle, AgentState


@pytest.fixture
def lifecycle():
    return AgentLifecycle(max_concurrent=3, max_retries=2)


class TestLifecycleSpawn:
    """Test 1: Spawn agent."""

    def test_spawn_returns_agent(self, lifecycle):
        agent = lifecycle.spawn("task_1")
        assert agent is not None
        assert agent.task_id == "task_1"
        assert agent.state == AgentState.RUNNING

    def test_spawn_respects_concurrent_limit(self, lifecycle):
        for i in range(3):
            lifecycle.spawn(f"task_{i}")
        
        # 4th spawn should fail
        agent = lifecycle.spawn("task_3")
        assert agent is None

    def test_get_running(self, lifecycle):
        lifecycle.spawn("task_1")
        lifecycle.spawn("task_2")
        running = lifecycle.get_running()
        assert len(running) == 2


class TestLifecycleHeartbeat:
    """Test 2: Heartbeat updates."""

    def test_heartbeat_updates_timestamp(self, lifecycle):
        agent = lifecycle.spawn("task_1")
        old_hb = agent.last_heartbeat
        import time
        time.sleep(0.01)
        assert lifecycle.heartbeat(agent.agent_id) is True
        updated = lifecycle.get_agent(agent.agent_id)
        assert updated.last_heartbeat != old_hb

    def test_heartbeat_unknown_agent(self, lifecycle):
        assert lifecycle.heartbeat("nonexistent") is False


class TestLifecycleComplete:
    """Test 3: Complete agent."""

    def test_complete_transitions_state(self, lifecycle):
        agent = lifecycle.spawn("task_1")
        assert lifecycle.complete(agent.agent_id, result={"data": "test"}) is True
        updated = lifecycle.get_agent(agent.agent_id)
        assert updated.state == AgentState.COMPLETED

    def test_complete_frees_slot(self, lifecycle):
        for i in range(3):
            lifecycle.spawn(f"task_{i}")
        
        running = lifecycle.get_running()
        lifecycle.complete(running[0].agent_id)
        
        # Should be able to spawn a new one
        agent = lifecycle.spawn("new_task")
        assert agent is not None


class TestLifecycleFail:
    """Test 4: Fail with retry."""

    def test_fail_increments_retry(self, lifecycle):
        agent = lifecycle.spawn("task_1")
        lifecycle.fail(agent.agent_id, "test error")
        updated = lifecycle.get_agent(agent.agent_id)
        assert updated.retry_count == 1
        assert updated.state == AgentState.FAILED

    def test_fail_transitions_to_abandoned(self, lifecycle):
        agent = lifecycle.spawn("task_1")
        # Fail 3 times (max_retries=2, 3rd = abandoned)
        for i in range(3):
            lifecycle.fail(agent.agent_id, f"error {i+1}")
        
        updated = lifecycle.get_agent(agent.agent_id)
        assert updated.state == AgentState.ABANDONED


class TestLifecycleStats:
    """Test 5: Stats reporting."""

    def test_stats_initially_empty(self, lifecycle):
        stats = lifecycle.get_stats()
        assert stats["total_agents"] == 0
        assert stats["by_state"]["running"] == 0

    def test_stats_after_operations(self, lifecycle):
        lifecycle.spawn("task_1")
        lifecycle.spawn("task_2")
        stats = lifecycle.get_stats()
        assert stats["total_agents"] == 2
        assert stats["by_state"]["running"] == 2


class TestLifecycleStale:
    """Test 6: Stale agent detection."""

    def test_no_stale_agents_initially(self, lifecycle):
        lifecycle.spawn("task_1")
        stale = lifecycle.get_stale_agents()
        assert len(stale) == 0

    def test_cleanup_stale(self, lifecycle):
        agent = lifecycle.spawn("task_1")
        # Manually set heartbeat to old time
        agent.last_heartbeat = "2020-01-01T00:00:00+00:00"
        stale = lifecycle.get_stale_agents()
        assert len(stale) == 1
        
        cleaned = lifecycle.cleanup_stale()
        assert cleaned == 1