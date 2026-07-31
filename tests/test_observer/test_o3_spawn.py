"""
O-3 Tests: Spawn Engine + Context Inheritance
===============================================
Tests for O3-B1 through O3-B10 components.

Run: python -m pytest tests/test_observer/test_o3_spawn.py -v
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import pytest
from datetime import datetime, timezone


# ─── O3-T1: Basic Spawn Test ────────────────────────────────────────────────

class TestAgentSpawner:
    """O3-T1: Spawn coding, research, orchestration agents."""

    def setup_method(self):
        from core.spawn.agent_spawner import AgentSpawner
        self.spawner = AgentSpawner()

    def test_spawn_coding_agent(self):
        result = self.spawner.spawn_agent("coding", "medium", {"task": "write tests"})
        assert result["status"] in ("spawned", "queued")
        assert "agent_id" in result

    def test_spawn_research_agent(self):
        result = self.spawner.spawn_agent("research", "low", {"task": "analyze data"})
        assert result["status"] in ("spawned", "queued")

    def test_spawn_orchestration_agent(self):
        result = self.spawner.spawn_agent("orchestration", "high", {"task": "coordinate"})
        assert result["status"] in ("spawned", "queued")


# ─── O3-T2: Context Inheritance Test ───────────────────────────────────────

class TestContextInjector:
    """O3-T2: Verify topology awareness, prior workflow awareness."""

    def setup_method(self):
        from core.spawn.context_injector import ContextInjector
        self.injector = ContextInjector()

    def test_topology_awareness(self):
        context = self.injector.inject({
            "task": "coding",
            "topology": {"nodes": 10, "edges": 15},
            "prior_workflows": []
        })
        assert "topology" in context
        assert context["topology"]["node_count"] == 10

    def test_prior_workflow_awareness(self):
        context = self.injector.inject({
            "task": "coding",
            "topology": {},
            "prior_workflows": [
                {"domain": "coding", "success": True, "routing": "direct"}
            ]
        })
        assert "prior_workflows" in context
        assert len(context["prior_workflows"]) == 1

    def test_context_compression(self):
        import json
        context = self.injector.inject({
            "task": "coding",
            "topology": {"nodes": 5, "edges": 8, "clusters": [{"id": "c1"}]},
            "prior_workflows": [],
            "entropy": {"level": 0.2},
            "runtime": {"active_agents": ["a1", "a2"]}
        })
        # Context should be compact
        assert len(json.dumps(context)) < 2000


# ─── O3-T3: Execution Boundary Test ────────────────────────────────────────

class TestExecutionBoundary:
    """O3-T3: Attempt out-of-scope file access, restricted terminal execution."""

    def setup_method(self):
        from core.spawn.execution_boundary import ExecutionBoundary
        self.boundary = ExecutionBoundary()

    def test_in_scope_access(self):
        result = self.boundary.check_access("read", "src/main.py", {"scope": "src/"})
        assert result["allowed"] is True

    def test_out_of_scope_access(self):
        result = self.boundary.check_access("write", "/etc/passwd", {"scope": "src/"})
        assert result["allowed"] is False

    def test_terminal_restriction(self):
        result = self.boundary.check_command("rm -rf /", {"allowed_commands": ["git", "python", "npm"]})
        assert result["allowed"] is False

    def test_allowed_command(self):
        result = self.boundary.check_command("git status", {"allowed_commands": ["git", "python", "npm"]})
        assert result["allowed"] is True


# ─── O3-T4: Multi-Agent Coordination Test ──────────────────────────────────

class TestMultiAgentCoordinator:
    """O3-T4: 3-agent cooperative workflow."""

    def setup_method(self):
        from core.spawn.multi_agent_coordinator import MultiAgentCoordinator
        self.coordinator = MultiAgentCoordinator()

    def test_three_agent_workflow(self):
        tasks = [
            {"id": "t1", "type": "coding", "depends_on": []},
            {"id": "t2", "type": "research", "depends_on": ["t1"]},
            {"id": "t3", "type": "testing", "depends_on": ["t1", "t2"]},
        ]
        plan = self.coordinator.plan_execution(tasks)
        assert len(plan["phases"]) >= 2  # At least 2 phases (t1 alone, t2+t3 or t1+t2, t3)

    def test_parallel_tasks(self):
        tasks = [
            {"id": "t1", "type": "coding", "depends_on": []},
            {"id": "t2", "type": "research", "depends_on": []},
        ]
        plan = self.coordinator.plan_execution(tasks)
        # Both should be in same phase (no dependencies)
        assert len(plan["phases"]) == 1


# ─── O3-T5: Lifecycle Stability Test ───────────────────────────────────────

class TestAgentLifecycle:
    """O3-T5: Agent lifecycle state transitions."""

    def setup_method(self):
        from core.spawn.agent_lifecycle import AgentLifecycle, AgentState
        self.lifecycle = AgentLifecycle()

    def test_lifecycle_transitions(self):
        agent_id = "test_agent_1"
        self.lifecycle.create_agent(agent_id, {"task": "coding"})
        assert self.lifecycle.get_state(agent_id) == AgentState.PENDING

        self.lifecycle.transition(agent_id, AgentState.RUNNING)
        assert self.lifecycle.get_state(agent_id) == AgentState.RUNNING

        self.lifecycle.transition(agent_id, AgentState.COMPLETE)
        assert self.lifecycle.get_state(agent_id) == AgentState.COMPLETE

    def test_invalid_transition(self):
        agent_id = "test_agent_2"
        self.lifecycle.create_agent(agent_id, {"task": "coding"})
        # Can't go from PENDING to COMPLETE
        with pytest.raises(ValueError):
            self.lifecycle.transition(agent_id, AgentState.COMPLETE)


# ─── O3-T6: Trace Feedback Test ────────────────────────────────────────────

class TestTraceFeedback:
    """O3-T6: Routing metrics update, orchestration memory updates."""

    def setup_method(self):
        from core.spawn.trace_feedback import TraceFeedback
        self.feedback = TraceFeedback()

    def test_trace_recording(self):
        self.feedback.record_trace("agent_1", "coding", True, 1500, "direct")
        metrics = self.feedback.get_metrics()
        assert metrics["total_traces"] == 1
        assert metrics["success_rate"] == 1.0

    def test_routing_metrics_update(self):
        self.feedback.record_trace("a1", "coding", True, 1000, "direct")
        self.feedback.record_trace("a2", "coding", False, 5000, "direct")
        self.feedback.record_trace("a3", "coding", True, 2000, "direct")
        metrics = self.feedback.get_metrics()
        assert metrics["total_traces"] == 3
        assert metrics["success_rate"] == 2 / 3


# ─── O3-T7: Failover Test ──────────────────────────────────────────────────

class TestOpenRouterGateway:
    """O3-T7: Model timeout, provider failure, execution crash."""

    def setup_method(self):
        from core.spawn.openrouter_gateway import OpenRouterGateway
        self.gateway = OpenRouterGateway()

    def test_provider_failover(self):
        result = self.gateway.route_with_fallback("coding", ["primary_model", "fallback_model"])
        assert "model" in result
        assert "provider" in result

    def test_all_providers_fail(self):
        result = self.gateway.route_with_fallback("coding", [])
        assert result["status"] == "failed"


# ─── O3-T8: Spawn Storm Test ───────────────────────────────────────────────

class TestSpawnStorm:
    """O3-T8: High-frequency task bursts."""

    def setup_method(self):
        from core.spawn.agent_spawner import AgentSpawner
        from core.spawn.spawn_registry import SpawnRegistry
        self.spawner = AgentSpawner()
        self.registry = SpawnRegistry()

    def test_burst_handling(self):
        results = []
        for i in range(10):
            result = self.spawner.spawn_agent("coding", "low", {"task": f"task_{i}"})
            results.append(result)
        # All should be handled (spawned or queued)
        assert all(r["status"] in ("spawned", "queued") for r in results)

    def test_registry_tracking(self):
        snapshot = self.registry.get_snapshot()
        assert "active_agents" in snapshot
        assert "total_spawned" in snapshot


# ─── Spawn Blueprint Test ──────────────────────────────────────────────────

class TestSpawnBlueprint:
    """Spawn blueprint generation and validation."""

    def setup_method(self):
        from core.spawn.spawn_blueprint import SpawnBlueprint
        self.blueprint = SpawnBlueprint()

    def test_blueprint_generation(self):
        bp = self.blueprint.create("coding", "medium", {"model": "qwen-coder"})
        assert bp["task_type"] == "coding"
        assert bp["complexity"] == "medium"
        assert "execution_boundary" in bp

    def test_blueprint_validation(self):
        bp = self.blueprint.create("coding", "high", {})
        assert self.blueprint.validate(bp) is True

    def test_invalid_blueprint(self):
        bp = {"task_type": "coding"}  # Missing required fields
        assert self.blueprint.validate(bp) is False


# ─── Spawn Replay Test ─────────────────────────────────────────────────────

class TestSpawnReplay:
    """Spawn decision replay."""

    def setup_method(self):
        from core.spawn.spawn_replay import SpawnReplay
        self.replay = SpawnReplay()

    def test_replay_recording(self):
        self.replay.record("spawn_1", {"task": "coding", "model": "qwen-coder"})
        history = self.replay.get_history()
        assert len(history) == 1

    def test_replay_reconstruction(self):
        for i in range(5):
            self.replay.record(f"spawn_{i}", {"task": "coding", "model": f"model_{i}"})
        history = self.replay.get_history()
        assert len(history) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
