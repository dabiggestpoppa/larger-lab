"""
O-1 Tests: Primary Observer Core
=================================
Tests for O1-B1 through O1-B9 components.

Run: python -m pytest tests/test_observer/test_o1_primary_observer.py -v
"""

import sys
import os
from pathlib import Path

# Ensure repo root is on path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import pytest
import json
import time
import tempfile
import shutil
from datetime import datetime, timezone


# ─── O1-T3: Task Analysis Test ─────────────────────────────────────────────

class TestTaskIntentAnalyzer:
    """O1-T3: Feed coding, research, orchestration, repair tasks."""

    def setup_method(self):
        from core.observer.task_intent_analyzer import TaskIntentAnalyzer
        self.analyzer = TaskIntentAnalyzer()

    def test_coding_task(self):
        result = self.analyzer.analyze("Write a Python function to sort a list")
        assert result["domain"] == "coding"
        assert result["requires_repo_access"] is True

    def test_research_task(self):
        result = self.analyzer.analyze("Research the differences between REST and GraphQL")
        assert result["domain"] == "research"

    def test_orchestration_task(self):
        result = self.analyzer.analyze("Coordinate multiple agents to process data in parallel")
        assert result["domain"] == "orchestration"
        assert result["requires_spawn"] is True

    def test_repair_task(self):
        result = self.analyzer.analyze("Fix the broken API endpoint that returns 500 errors")
        assert result["domain"] == "repair"
        assert result["requires_repo_access"] is True

    def test_debugging_task(self):
        result = self.analyzer.analyze("Debug why the application crashes on startup")
        assert result["domain"] == "debugging"

    def test_architecture_task(self):
        result = self.analyzer.analyze("Design the system architecture for the new microservice")
        assert result["domain"] == "architecture"

    def test_visualization_task(self):
        result = self.analyzer.analyze("Create a dashboard to display the topology graph")
        assert result["domain"] == "visualization"

    def test_automation_task(self):
        result = self.analyzer.analyze("Set up a CI/CD pipeline for automated deployment")
        assert result["domain"] == "automation"

    def test_system_analysis_task(self):
        result = self.analyzer.analyze("Analyze the system performance and health metrics")
        assert result["domain"] == "system_analysis"
        assert result["requires_runtime_context"] is True

    def test_complexity_estimation(self):
        result = self.analyzer.analyze("Refactor the entire codebase architecture")
        assert result["complexity"] in ("high", "critical")

    def test_routing_hints_present(self):
        result = self.analyzer.analyze("Write a simple hello world function")
        assert "routing_hints" in result
        assert "priority" in result["routing_hints"]
        assert "estimated_duration" in result["routing_hints"]
        assert "suggested_model" in result["routing_hints"]


# ─── O1-T2: Runtime Awareness Test ────────────────────────────────────────

class TestRuntimeAwareness:
    """O1-T2: Inject topology mutation, entropy spike, observer failure."""

    def setup_method(self):
        from core.observer.runtime_awareness import RuntimeAwareness
        self.awareness = RuntimeAwareness()

    def test_topology_mutation(self):
        self.awareness.update_topology(node_count=10, edge_count=15)
        snapshot = self.awareness.get_snapshot_dict()
        assert snapshot["topology"]["nodes"] == 10
        assert snapshot["topology"]["edges"] == 15

    def test_entropy_spike(self):
        self.awareness.update_entropy(0.3)
        self.awareness.update_entropy(0.85)  # spike
        snapshot = self.awareness.get_snapshot_dict()
        assert snapshot["entropy"]["level"] == 0.85
        assert any(a["type"] == "entropy_spike" for a in snapshot["alerts"])

    def test_observer_tracking(self):
        self.awareness.update_observers(["obs_1", "obs_2", "obs_3"])
        snapshot = self.awareness.get_snapshot_dict()
        assert len(snapshot["active_observers"]) == 3

    def test_repair_state(self):
        self.awareness.update_repair(True, targets=["node_a", "node_b"])
        snapshot = self.awareness.get_snapshot_dict()
        assert snapshot["repair"]["active"] is True
        assert "node_a" in snapshot["repair"]["targets"]

    def test_spawned_agents(self):
        self.awareness.update_spawned_agents(5)
        snapshot = self.awareness.get_snapshot_dict()
        assert snapshot["spawned_agents"] == 5

    def test_snapshot_history(self):
        self.awareness.update_entropy(0.1)
        self.awareness.take_snapshot()
        self.awareness.update_entropy(0.5)
        self.awareness.take_snapshot()
        assert len(self.awareness._history) == 2


# ─── O1-T4: Context Distillation Test ─────────────────────────────────────

class TestContextDistiller:
    """O1-T4: Spawn multiple tasks, verify low-noise context."""

    def setup_method(self):
        from core.observer.context_distiller import ContextDistiller
        self.distiller = ContextDistiller()

    def test_coding_context(self):
        context = self.distiller.distill(
            task_domain="coding",
            complexity="medium",
            runtime_state={"active_agents": ["agent_1"]},
            topology_state={"nodes": 10, "edges": 15},
        )
        assert context["task"]["domain"] == "coding"
        assert "_meta" in context

    def test_context_under_500_tokens(self):
        """Context should be compact (< 500 tokens estimated)."""
        context = self.distiller.distill(
            task_domain="coding",
            complexity="low",
            runtime_state={"active_agents": ["a1"]},
            topology_state={"nodes": 5, "edges": 8},
            entropy_state={"level": 0.2, "trend": "stable"},
        )
        estimated = context["_meta"]["estimated_tokens"]
        assert estimated < 500, f"Context too large: {estimated} tokens"

    def test_orchestration_gets_more_context(self):
        """Orchestration tasks should get topology and runtime context."""
        ctx_orch = self.distiller.distill(
            task_domain="orchestration",
            complexity="high",
            runtime_state={"active_agents": ["a1"], "system_load": 0.5},
            topology_state={"nodes": 10, "edges": 15, "clusters": [{"id": "c1"}], "alerts": []},
        )
        assert "node_count" in ctx_orch["topology"]
        assert "cluster_count" in ctx_orch["topology"]

    def test_continuity_included(self):
        context = self.distiller.distill(
            task_domain="coding",
            complexity="low",
            session_context={"last_domain": "research", "last_complexity": "medium"},
            prior_workflows=[
                {"domain": "coding", "success": True, "routing_path": "direct"},
            ],
        )
        assert context["continuity"]["previous_domain"] == "research"
        assert len(context["continuity"]["recent_workflows"]) == 1


# ─── O1-T1: Continuity Test ───────────────────────────────────────────────

class TestContinuityMemory:
    """O1-T1: Persistent observer session continuity."""

    def setup_method(self):
        from core.observer.continuity_memory import ContinuityMemory, WorkflowRecord
        # Reset singleton state for clean tests (deletes persistence file)
        ContinuityMemory.reset_instance()
        self.memory = ContinuityMemory()
        self.WorkflowRecord = WorkflowRecord

    def test_workflow_recording(self):
        wf = self.WorkflowRecord(
            workflow_id="wf_1",
            task_domain="coding",
            complexity="medium",
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True,
            routing_path="direct",
        )
        self.memory.record_workflow(wf)
        assert self.memory.record.workflow_count == 1
        assert self.memory.record.success_count == 1

    def test_success_rate(self):
        for i in range(5):
            wf = self.WorkflowRecord(
                workflow_id=f"wf_{i}",
                task_domain="coding",
                complexity="low",
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=i < 4,  # 4/5 success
                routing_path="direct",
            )
            self.memory.record_workflow(wf)
        rate = self.memory.get_success_rate("coding")
        assert rate == 0.8

    def test_routing_patterns(self):
        for i in range(3):
            wf = self.WorkflowRecord(
                workflow_id=f"wf_{i}",
                task_domain="coding",
                complexity="low",
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=True,
                routing_path="direct",
            )
            self.memory.record_workflow(wf)
        patterns = self.memory.get_top_routing_patterns()
        assert len(patterns) > 0
        assert patterns[0][0] == "coding:direct"

    def test_goal_tracking(self):
        self.memory.add_goal("Complete Phase O-1")
        assert "Complete Phase O-1" in self.memory.record.active_goals
        self.memory.complete_goal("Complete Phase O-1")
        assert "Complete Phase O-1" not in self.memory.record.active_goals


# ─── O1-T5: Restart Recovery Test ─────────────────────────────────────────

class TestObserverState:
    """O1-T5: Crash observer, verify continuity restored."""

    def setup_method(self):
        # Reset singleton for clean tests
        from core.observer import observer_state
        observer_state.ObserverState._instance = None
        from core.observer.observer_state import get_observer_state
        self.state = get_observer_state()
        self.state.reset()

    def test_state_persistence(self):
        self.state.set("observer_health", "healthy")
        self.state.set("continuity_score", 0.95)
        # Re-read from disk
        data = self.state.to_dict()
        assert data["observer_health"] == "healthy"
        assert data["continuity_score"] == 0.95

    def test_version_increments(self):
        v1 = self.state.get("version")
        self.state.set("continuity_score", 0.8)
        v2 = self.state.get("version")
        assert v2 > v1

    def test_agent_tracking(self):
        self.state.add_active_agent("agent_1")
        self.state.add_active_agent("agent_2")
        assert len(self.state.get("active_agents")) == 2
        self.state.remove_active_agent("agent_1")
        assert len(self.state.get("active_agents")) == 1


# ─── O1-T6: Event Awareness Test ──────────────────────────────────────────

class TestEventAwareness:
    """O1-T6: Live panels, event sync, runtime updates."""

    def setup_method(self):
        from core.observer.event_awareness import EventAwareness, EventType
        self.events = EventAwareness()
        self.EventType = EventType

    def test_emit_event(self):
        event = self.events.emit(
            self.EventType.TASK_RECEIVED,
            source="test",
            data={"task_id": "t1"},
        )
        assert event.event_type == "task_received"
        assert event.source == "test"

    def test_event_filtering(self):
        self.events.emit(self.EventType.TASK_RECEIVED, source="obs_1")
        self.events.emit(self.EventType.TASK_STARTED, source="obs_1")
        self.events.emit(self.EventType.TASK_RECEIVED, source="obs_2")

        received = self.events.get_events(event_type="task_received")
        assert len(received) == 2

        from_obs_1 = self.events.get_events(source="obs_1")
        assert len(from_obs_1) == 2

    def test_event_counts(self):
        self.events.emit(self.EventType.TASK_RECEIVED, source="test")
        self.events.emit(self.EventType.TASK_RECEIVED, source="test")
        self.events.emit(self.EventType.TASK_STARTED, source="test")

        counts = self.events.get_event_counts()
        assert counts["task_received"] == 2
        assert counts["task_started"] == 1

    def test_subscribe(self):
        received = []
        self.events.subscribe("task_received", lambda e: received.append(e))
        self.events.emit(self.EventType.TASK_RECEIVED, source="test")
        self.events.emit(self.EventType.TASK_STARTED, source="test")
        assert len(received) == 1


# ─── Observer Session Test ─────────────────────────────────────────────────

class TestObserverSession:
    """Session continuity management."""

    def setup_method(self):
        from core.observer.observer_session import ObserverSession
        self.sessions = ObserverSession()

    def test_create_session(self):
        session = self.sessions.create_session(observer_id="primary")
        assert session.session_id is not None
        assert session.status == "active"
        assert self.sessions.active_session is not None

    def test_close_and_resume(self):
        session = self.sessions.create_session(observer_id="primary")
        sid = session.session_id
        self.sessions.close_session(sid)
        assert self.sessions.active_session is None

        resumed = self.sessions.resume_session(sid)
        # Closed sessions can't be resumed
        assert resumed is None

    def test_touch_session(self):
        session = self.sessions.create_session(observer_id="primary")
        initial_count = session.task_count
        self.sessions.touch_session()
        assert self.sessions.active_session.task_count == initial_count + 1


# ─── Observer Lifecycle Test ───────────────────────────────────────────────

class TestObserverLifecycle:
    """Heartbeat, healthcheck, recovery."""

    def setup_method(self):
        from core.observer.observer_lifecycle import ObserverLifecycle
        self.lifecycle = ObserverLifecycle(
            heartbeat_interval=0.05,
            healthcheck_interval=0.1,
        )

    def teardown_method(self):
        if self.lifecycle.is_running:
            self.lifecycle.stop()

    def test_start_stop(self):
        self.lifecycle.start()
        assert self.lifecycle.is_running is True
        time.sleep(0.2)
        assert self.lifecycle.heartbeat_count >= 1
        self.lifecycle.stop()
        assert self.lifecycle.is_running is False

    def test_health_status(self):
        from core.observer.observer_state import HealthStatus
        status = self.lifecycle.get_status()
        assert status["running"] is False
        self.lifecycle.start()
        time.sleep(0.15)
        status = self.lifecycle.get_status()
        assert status["health"] == HealthStatus.HEALTHY.value
        self.lifecycle.stop()


# ─── Primary Observer Integration Test ─────────────────────────────────────

class TestPrimaryObserver:
    """Full integration: receive_input → analyze → respond."""

    def setup_method(self):
        from core.observer import observer_state
        observer_state.ObserverState._instance = None
        # Also reset the singleton module-level reference
        import core.observer.observer_state as os_mod
        os_mod.ObserverState._instance = None
        from core.observer.primary_observer import PrimaryObserver
        self.observer = PrimaryObserver()

    def test_receive_coding_task(self):
        response = self.observer.receive_input("Write a Python function to calculate fibonacci")
        assert response.status == "received"
        assert response.task_domain == "coding"
        assert response.request_id is not None

    def test_receive_research_task(self):
        response = self.observer.receive_input("Research the best practices for microservices")
        assert response.task_domain == "research"

    def test_receive_orchestration_task(self):
        response = self.observer.receive_input("Coordinate 3 agents to process data in parallel")
        assert response.task_domain == "orchestration"
        assert response.routing_hints.get("suggested_model") is not None

    def test_health_endpoint(self):
        health = self.observer.health
        assert "observer_id" in health
        assert "continuity_score" in health
        assert health["status"] == "healthy"

    def test_full_status(self):
        status = self.observer.get_status()
        assert "health" in status
        assert "runtime_state" in status
        assert "entropy_state" in status
        assert "repair_state" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
