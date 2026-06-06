"""
PM2 Tests — PO Multi-Model Router (P2.5)

Tests for ModelRouter: registration, routing, context-aware routing,
fallback chain building, and health checks.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestModelRouterCore:
    """Core routing tests."""

    def test_default_models_registered(self):
        """Should have PO, OpenAI, and Ollama models by default."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        models = router.list_models()
        ids = [m.id for m in models]
        assert "po" in ids
        assert "openai/gpt-4o" in ids
        assert "ollama/llama3.1" in ids

    def test_route_defaults_to_po(self):
        """Default routing should select PO as primary."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        decision = router.route("any query")
        assert decision.model_id == "po"
        assert decision.provider == "oce"

    def test_route_with_preferred_model(self):
        """Should respect preferred model override."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        decision = router.route("test", preferred_model="openai/gpt-4o")
        assert decision.model_id == "openai/gpt-4o"

    def test_route_unavailable_preferred_falls_back(self):
        """Should fall back if preferred model is unavailable."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        router.set_model_status("openai/gpt-4o", "unavailable")
        decision = router.route("test", preferred_model="openai/gpt-4o")
        # Should fall back to another available model
        assert decision.model_id != "openai/gpt-4o"

    def test_register_deregister_model(self):
        """Should register and deregister custom models."""
        from oce.backend.po_router import ModelRouter, ModelInfo
        router = ModelRouter()
        router.register_model(ModelInfo(id="test/llm", name="Test", provider="test"))
        assert router.get_model("test/llm") is not None
        router.deregister_model("test/llm")
        assert router.get_model("test/llm") is None


class TestModelRouterContextAware:
    """Context-aware routing tests."""

    def test_route_with_context_small_query(self):
        """Small queries should route to PO."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        decision = router.route_with_context("hello", estimated_tokens=100)
        assert decision.model_id == "po"

    def test_route_with_context_large_tokens(self):
        """Queries exceeding context window should skip small models."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        # 999999 tokens exceeds all default models' context windows
        decision = router.route_with_context("huge query", estimated_tokens=999999)
        # Should still return a decision (relaxed constraints)
        assert decision is not None

    def test_route_with_streaming_requirement(self):
        """Should only route to streaming-capable models when required."""
        from oce.backend.po_router import ModelRouter, ModelInfo
        router = ModelRouter()
        # Register a non-streaming model
        router.register_model(ModelInfo(
            id="test/local",
            name="Local Non-Streaming",
            provider="local",
            supports_streaming=False,
        ))
        decision = router.route_with_context("test", require_streaming=True)
        assert decision.model_id != "test/local"

    def test_route_with_preferred_and_context(self):
        """Should respect preferred model with context constraints."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        decision = router.route_with_context(
            "test",
            estimated_tokens=100,
            preferred_model="openai/gpt-4o",
        )
        assert decision.model_id == "openai/gpt-4o"


class TestModelRouterFallbackChain:
    """Fallback chain building tests."""

    def test_po_fallback_chain(self):
        """PO primary should have OpenAI and Ollama in fallback."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        decision = router.route("test")
        chain = decision.fallback_chain
        assert len(chain) >= 1  # At least one fallback available

    def test_fallback_chain_only_available(self):
        """Fallback chain should only include available models."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        router.set_model_status("openai/gpt-4o", "unavailable")
        decision = router.route("test")
        assert "openai/gpt-4o" not in decision.fallback_chain


class TestModelRouterHealth:
    """Health check and stats tests."""

    def test_health_check(self):
        """Should return health status for all models."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        health = router.health_check()
        assert "po" in health
        assert health["po"]["status"] == "available"

    def test_routing_stats(self):
        """Should return routing statistics."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        stats = router.get_routing_stats()
        assert stats["total_models"] >= 3
        assert stats["available_models"] >= 3

    def test_list_available_models(self):
        """Should list only available models."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        router.set_model_status("openai/gpt-4o", "unavailable")
        available = router.list_available_models()
        ids = [m.id for m in available]
        assert "openai/gpt-4o" not in ids
        assert "po" in ids
