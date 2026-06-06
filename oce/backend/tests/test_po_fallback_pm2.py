"""
PM2 Tests — PO Fallback Chain (P3.2)

Tests for FallbackChain: instantiation, provider management,
error accumulation, and status reporting.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestFallbackChainCore:
    """Core fallback chain tests."""

    def test_default_chain_has_providers(self):
        """Default chain should have OpenRouter and Ollama."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        assert len(chain.chain) >= 2
        providers = [p["provider"] for p in chain.chain]
        assert "openrouter" in providers
        assert "ollama" in providers

    def test_custom_chain(self):
        """Should accept custom provider chain."""
        from oce.backend.po_fallback import FallbackChain
        custom = [{"provider": "custom", "endpoint": "http://test", "model": "test"}]
        chain = FallbackChain(chain=custom)
        assert len(chain.chain) == 1
        assert chain.chain[0]["provider"] == "custom"

    def test_status_returns_dict(self):
        """Status should return expected structure."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        status = chain.status()
        assert "providers" in status
        assert "provider_count" in status
        assert "recent_errors" in status
        assert "error_count" in status
        assert status["provider_count"] >= 2


class TestFallbackChainProviderManagement:
    """Provider add/remove tests."""

    def test_add_provider(self):
        """Should add a provider to the chain."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        initial = len(chain.chain)
        chain.add_provider({
            "provider": "custom",
            "endpoint": "http://custom.api/v1/chat",
            "model": "custom-model",
            "timeout": 30,
        })
        assert len(chain.chain) == initial + 1
        assert chain.chain[-1]["provider"] == "custom"

    def test_add_provider_at_position(self):
        """Should insert provider at specific position."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        chain.add_provider({
            "provider": "priority",
            "endpoint": "http://priority.api",
            "model": "p1",
        }, position=0)
        assert chain.chain[0]["provider"] == "priority"

    def test_remove_provider(self):
        """Should remove provider by name."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        chain.remove_provider("ollama")
        providers = [p["provider"] for p in chain.chain]
        assert "ollama" not in providers


class TestFallbackChainErrors:
    """Error tracking tests."""

    def test_initial_errors_empty(self):
        """Should start with no errors."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        assert chain.get_errors() == []

    def test_clear_errors(self):
        """Should clear accumulated errors."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        chain._errors.append({"test": True})
        chain.clear_errors()
        assert chain.get_errors() == []

    def test_fallback_error_exception(self):
        """FallbackError should format all provider errors."""
        from oce.backend.po_fallback import FallbackError
        errors = [
            {"provider": "openrouter", "error": "timeout"},
            {"provider": "ollama", "error": "connection refused"},
        ]
        exc = FallbackError(errors)
        assert "openrouter" in str(exc)
        assert "ollama" in str(exc)
        assert exc.errors == errors


class TestFallbackChainStatus:
    """Status reporting tests."""

    def test_status_shows_providers(self):
        """Status should list all providers."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        status = chain.status()
        assert "openrouter" in status["providers"]
        assert "ollama" in status["providers"]

    def test_status_shows_errors(self):
        """Status should include recent errors."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        chain._errors.append({"provider": "test", "error": "fail"})
        status = chain.status()
        assert status["error_count"] == 1
        assert len(status["recent_errors"]) == 1
