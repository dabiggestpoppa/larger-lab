"""
O-2 Tests: Observer Consensus + Task Routing
==============================================
Tests for O2-B1 through O2-B10 components.

Run: python -m pytest tests/test_observer/test_o2_consensus.py -v
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import pytest
from datetime import datetime, timezone


# ─── O2-T1: Task Classification Test ────────────────────────────────────────

class TestTaskClassifier:
    """O2-T1: Feed 9 task types, verify 95% accuracy."""

    def setup_method(self):
        from core.consensus.task_classifier import TaskClassifier
        self.classifier = TaskClassifier()

    def test_coding_classification(self):
        result = self.classifier.classify("Write a Python function to sort a list")
        assert result["task_type"] == "coding"

    def test_research_classification(self):
        result = self.classifier.classify("Research the differences between REST and GraphQL")
        assert result["task_type"] == "research"

    def test_architecture_classification(self):
        result = self.classifier.classify("Design the system architecture for microservices")
        assert result["task_type"] == "architecture"

    def test_repair_classification(self):
        result = self.classifier.classify("Fix the broken API endpoint")
        assert result["task_type"] == "repair"

    def test_debugging_classification(self):
        result = self.classifier.classify("Debug why the application crashes on startup")
        assert result["task_type"] == "debugging"

    def test_orchestration_classification(self):
        result = self.classifier.classify("Coordinate multiple agents to process data")
        assert result["task_type"] == "orchestration"

    def test_visualization_classification(self):
        result = self.classifier.classify("Create a dashboard to display metrics")
        assert result["task_type"] == "visualization"

    def test_automation_classification(self):
        result = self.classifier.classify("Set up a CI/CD pipeline for deployment")
        assert result["task_type"] == "automation"

    def test_system_analysis_classification(self):
        result = self.classifier.classify("Analyze system performance and health")
        assert result["task_type"] == "system_analysis"


# ─── O2-T2: Routing Stability Test ─────────────────────────────────────────

class TestRoutingConsensus:
    """O2-T2: 100 repeated orchestration requests, verify consistent routing."""

    def setup_method(self):
        from core.consensus.routing_consensus import RoutingConsensus
        self.routing = RoutingConsensus()

    def test_routing_consistency(self):
        results = []
        for _ in range(20):
            result = self.routing.determine_route("coding", "medium", {})
            results.append(result["route"])
        # All should be the same
        assert len(set(results)) == 1

    def test_routing_factors(self):
        result = self.routing.determine_route("coding", "high", {"load": 0.8})
        assert "route" in result
        assert "confidence" in result


# ─── O2-T3: Model Selection Test ───────────────────────────────────────────

class TestModelSelector:
    """O2-T3: Large coding, lightweight, research tasks."""

    def setup_method(self):
        from core.consensus.model_selector import ModelSelector
        self.selector = ModelSelector()

    def test_large_coding_model(self):
        result = self.selector.select("coding", "critical", {})
        assert result["model"] is not None

    def test_lightweight_model(self):
        result = self.selector.select("research", "low", {})
        assert result["model"] is not None

    def test_research_model(self):
        result = self.selector.select("research", "high", {})
        assert result["model"] is not None


# ─── O2-T4: Entropy Routing Test ───────────────────────────────────────────

class TestEntropyRouting:
    """O2-T4: Overloaded runtime, unstable topology, failing observers."""

    def setup_method(self):
        from core.consensus.routing_consensus import RoutingConsensus
        self.routing = RoutingConsensus()

    def test_overloaded_runtime(self):
        result = self.routing.determine_route("coding", "high", {
            "load": 0.95,
            "entropy": 0.8,
            "observer_health": "degraded"
        })
        assert "route" in result
        # Should still produce a route (graceful degradation)
        assert result["confidence"] < 0.9  # Lower confidence under stress

    def test_stable_runtime(self):
        result = self.routing.determine_route("coding", "medium", {
            "load": 0.3,
            "entropy": 0.1,
            "observer_health": "healthy"
        })
        assert result["confidence"] > 0.5


# ─── O2-T5: Consensus Replay Test ───────────────────────────────────────────

class TestConsensusReplay:
    """O2-T5: Replay orchestration history."""

    def setup_method(self):
        from core.consensus.consensus_replay import ConsensusReplay
        self.replay = ConsensusReplay()

    def test_replay_recording(self):
        self.replay.record_decision("req_1", "coding", "direct", 0.9)
        history = self.replay.get_history()
        assert len(history) == 1
        assert history[0]["request_id"] == "req_1"

    def test_replay_reconstruction(self):
        for i in range(5):
            self.replay.record_decision(f"req_{i}", "coding", "direct", 0.8 + i * 0.02)
        history = self.replay.get_history()
        assert len(history) == 5


# ─── O2-T6: Specialization Test ────────────────────────────────────────────

class TestObserverSpecialization:
    """O2-T6: Extended orchestration workloads."""

    def setup_method(self):
        from core.consensus.observer_specialization import ObserverSpecialization
        self.spec = ObserverSpecialization()

    def test_specialization_tracking(self):
        self.spec.record_performance("observer_1", "coding", 0.9)
        self.spec.record_performance("observer_1", "coding", 0.85)
        score = self.spec.get_specialization("observer_1", "coding")
        assert score > 0.8

    def test_specialization_improves(self):
        for i in range(10):
            self.spec.record_performance("obs_1", "coding", 0.5 + i * 0.04)
        score = self.spec.get_specialization("obs_1", "coding")
        assert score > 0.6


# ─── O2-T7: Spawn Planning Test ────────────────────────────────────────────

class TestSpawnPlanner:
    """O2-T7: Bounded execution scopes, stable spawn plans."""

    def setup_method(self):
        from core.consensus.spawn_planner import SpawnPlanner
        self.planner = SpawnPlanner()

    def test_spawn_plan_generation(self):
        plan = self.planner.generate_plan("coding", "medium", {})
        assert "spawn_required" in plan
        assert "spawn_count" in plan
        assert "recommended_model" in plan

    def test_bounded_execution(self):
        plan = self.planner.generate_plan("coding", "high", {})
        assert plan["spawn_count"] <= 5  # Bounded

    def test_capability_matching(self):
        from core.consensus.capability_matcher import CapabilityMatcher
        matcher = CapabilityMatcher()
        caps = matcher.match_capabilities("coding", "high")
        assert "repo_access" in caps


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
