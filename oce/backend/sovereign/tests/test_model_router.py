"""Tests for Model Router."""

import pytest
from oce.backend.sovereign.model_router import ModelRouter, ModelRoute


class TestModelRoute:
    """Tests for ModelRoute dataclass."""

    def test_route_creation(self):
        """Test ModelRoute can be created."""
        route = ModelRoute(
            route_id="route-1",
            timestamp=12345.0,
            model_name="sonnet",
            provider="anthropic",
            cost=0.015,
            latency=0.3,
            capability_match=0.85,
        )
        assert route.route_id == "route-1"
        assert route.model_name == "sonnet"
        assert route.provider == "anthropic"

    def test_route_to_dict(self):
        """Test ModelRoute serialization."""
        route = ModelRoute(
            route_id="route-1",
            timestamp=12345.0,
            model_name="sonnet",
            provider="anthropic",
            cost=0.015,
            latency=0.3,
            capability_match=0.85,
        )
        d = route.to_dict()
        assert d["route_id"] == "route-1"
        assert d["model_name"] == "sonnet"


class TestModelRouter:
    """Tests for ModelRouter class."""

    def test_router_creation(self):
        """Test ModelRouter can be created."""
        router = ModelRouter()
        assert router is not None

    def test_route_basic(self):
        """Test basic routing."""
        router = ModelRouter()
        route = router.route(
            task_complexity=0.7,
            cost_budget=0.1,
            latency_requirement=1.0,
        )
        assert route.model_name in ["opus", "sonnet", "haiku", "gpt-4", "gpt-3.5"]
        assert route.provider in ["anthropic", "openai"]
        assert route.cost > 0

    def test_route_low_budget(self):
        """Test routing with low budget."""
        router = ModelRouter()
        route = router.route(
            task_complexity=0.5,
            cost_budget=0.001,
            latency_requirement=1.0,
        )
        assert route.model_name == "haiku"

    def test_route_high_complexity(self):
        """Test routing for high complexity."""
        router = ModelRouter()
        route = router.route(
            task_complexity=0.95,
            cost_budget=0.1,
            latency_requirement=1.0,
        )
        # High complexity with sufficient budget should select a capable model
        assert route.model_name in ["opus", "sonnet"]

    def test_route_low_latency(self):
        """Test routing with low latency requirement."""
        router = ModelRouter()
        route = router.route(
            task_complexity=0.5,
            cost_budget=0.1,
            latency_requirement=0.05,
        )
        # Low latency requirement should select haiku (fastest)
        assert route.model_name == "haiku"
        assert route.latency <= 0.1  # haiku has latency 0.1

    def test_calculate_capability_match(self):
        """Test capability match calculation."""
        router = ModelRouter()
        match = router._calculate_capability_match("opus", 0.9)
        assert 0 <= match <= 1

    def test_get_stats(self):
        """Test getting router statistics."""
        router = ModelRouter()
        stats = router.get_stats()
        assert "total_routes" in stats
        assert "available_models" in stats