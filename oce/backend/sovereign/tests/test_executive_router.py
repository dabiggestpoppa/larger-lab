"""Tests for Executive Router."""

import pytest
from oce.backend.sovereign.executive_router import ExecutiveRouter, RoutingDecision


class TestRoutingDecision:
    """Tests for RoutingDecision dataclass."""

    def test_routing_decision_creation(self):
        """Test RoutingDecision can be created."""
        decision = RoutingDecision(
            decision_id="test-decision",
            timestamp=12345.0,
            selected_agent="claude",
            selected_model="sonnet",
            selected_tool="terminal",
            confidence=0.85,
            entropy_pressure=0.3,
            resonance_fit=0.9,
            cost_estimate=0.015,
            continuity_stability=0.95,
            task_topology="coding",
        )
        assert decision.decision_id == "test-decision"
        assert decision.selected_agent == "claude"
        assert decision.confidence == 0.85

    def test_routing_decision_to_dict(self):
        """Test RoutingDecision serialization."""
        decision = RoutingDecision(
            decision_id="test-decision",
            timestamp=12345.0,
            selected_agent="claude",
            selected_model="sonnet",
            selected_tool="terminal",
            confidence=0.85,
            entropy_pressure=0.3,
            resonance_fit=0.9,
            cost_estimate=0.015,
            continuity_stability=0.95,
            task_topology="coding",
        )
        d = decision.to_dict()
        assert d["decision_id"] == "test-decision"
        assert d["selected_agent"] == "claude"


class TestExecutiveRouter:
    """Tests for ExecutiveRouter class."""

    def test_router_creation(self):
        """Test ExecutiveRouter can be created."""
        router = ExecutiveRouter()
        assert router is not None

    def test_route_basic(self):
        """Test basic routing decision."""
        router = ExecutiveRouter()
        decision = router.route(
            entropy_pressure=0.5,
            resonance_fit=0.8,
            cost_budget=0.1,
            continuity_stability=0.9,
            task_topology="coding",
        )
        assert decision.selected_agent == "claude"
        assert decision.selected_model in ["opus", "sonnet", "haiku"]
        assert decision.selected_tool == "terminal"
        assert 0 <= decision.confidence <= 1

    def test_route_high_entropy(self):
        """Test routing with high entropy pressure."""
        router = ExecutiveRouter()
        decision = router.route(
            entropy_pressure=0.9,
            resonance_fit=0.5,
            cost_budget=0.1,
            continuity_stability=0.8,
            task_topology="coding",
        )
        assert decision.selected_agent == "claude"

    def test_route_research_task(self):
        """Test routing for research task."""
        router = ExecutiveRouter()
        decision = router.route(
            entropy_pressure=0.3,
            resonance_fit=0.7,
            cost_budget=0.1,
            continuity_stability=0.9,
            task_topology="research",
        )
        assert decision.selected_agent == "gemini"
        assert decision.selected_tool == "browser"

    def test_route_low_budget(self):
        """Test routing with low cost budget."""
        router = ExecutiveRouter()
        decision = router.route(
            entropy_pressure=0.5,
            resonance_fit=0.8,
            cost_budget=0.001,
            continuity_stability=0.9,
            task_topology="coding",
        )
        assert decision.selected_model == "haiku"

    def test_calculate_confidence(self):
        """Test confidence calculation."""
        router = ExecutiveRouter()
        confidence = router._calculate_confidence(0.5, 0.8, 0.9)
        assert 0 <= confidence <= 1

    def test_select_agent(self):
        """Test agent selection."""
        router = ExecutiveRouter()
        assert router._select_agent(0.9, "coding") == "claude"
        assert router._select_agent(0.3, "research") == "gemini"

    def test_select_model(self):
        """Test model selection."""
        router = ExecutiveRouter()
        assert router._select_model(0.9, 0.1) == "opus"
        assert router._select_model(0.6, 0.1) == "sonnet"
        assert router._select_model(0.3, 0.1) == "haiku"

    def test_select_tool(self):
        """Test tool selection."""
        router = ExecutiveRouter()
        assert router._select_tool("research") == "browser"
        assert router._select_tool("coding") == "terminal"
        assert router._select_tool("analysis") == "memory"

    def test_estimate_cost(self):
        """Test cost estimation."""
        router = ExecutiveRouter()
        cost = router._estimate_cost("opus", "terminal")
        assert cost > 0

    def test_get_stats(self):
        """Test getting router statistics."""
        router = ExecutiveRouter()
        stats = router.get_stats()
        assert "total_decisions" in stats
        assert "available_agents" in stats
        assert "available_models" in stats
        assert "available_tools" in stats