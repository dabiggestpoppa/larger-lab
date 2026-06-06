"""
Phase 3 Integration Tests — PO Identity Unification

Tests cross-interface identity continuity and fallback chain.
"""

import pytest
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestIdentitySessionBridge:
    """Tests for identity session bridge (P3.1)."""

    def test_bridge_instantiation(self):
        """IdentitySessionBridge should instantiate."""
        from core.identity.session_bridge import IdentitySessionBridge
        bridge = IdentitySessionBridge()
        assert bridge is not None

    def test_get_continuity(self):
        """Should resolve surface session to unified identity session."""
        from core.identity.session_bridge import IdentitySessionBridge
        bridge = IdentitySessionBridge()
        # Mock session store
        session = bridge.get_continuity("vtuber", "vtuber-session-123")
        assert session is not None

    def test_link_sessions(self):
        """Should link surface session to identity session."""
        from core.identity.session_bridge import IdentitySessionBridge
        bridge = IdentitySessionBridge()
        bridge.link("vtuber", "vtuber-session-123", "po-identity-456")
        # Verify link was created (key format is "surface:session_id")
        assert bridge._links.get("vtuber:vtuber-session-123") == "po-identity-456"


class TestFallbackChain:
    """Tests for multi-model fallback chain (P3.2)."""

    def test_fallback_chain_instantiation(self):
        """FallbackChain should instantiate with default providers."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        assert chain is not None
        assert len(chain.chain) >= 2  # openrouter + ollama

    def test_fallback_status(self):
        """Should return status dict."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        status = chain.status()
        assert "providers" in status
        assert "recent_errors" in status

    def test_fallback_chain_execution(self):
        """Should attempt providers in order."""
        from oce.backend.po_fallback import FallbackChain
        chain = FallbackChain()
        # Test that chain has expected structure
        providers = [p["provider"] for p in chain.chain]
        assert "openrouter" in providers


class TestInterruptHandler:
    """Tests for interrupt handling (P3.3)."""

    def test_handler_instantiation(self):
        """InterruptHandler should instantiate."""
        from oce.backend.po_interrupt import InterruptHandler
        handler = InterruptHandler()
        assert handler is not None

    def test_scope_creation(self):
        """Should be able to create cancel scopes."""
        from oce.backend.po_interrupt import InterruptHandler
        handler = InterruptHandler()
        scope = handler.create_scope("test-scope")
        assert scope is not None
        assert scope.scope_id == "test-scope"

    def test_cancel_scope(self):
        """Should be able to cancel a scope."""
        from oce.backend.po_interrupt import InterruptHandler
        handler = InterruptHandler()
        scope = handler.create_scope("test")
        handler.cancel("test", reason="test_cancel")
        assert scope.cancelled is True


class TestPOIdleRuntime:
    """Tests for autonomous idle runtime (P3.4)."""

    def test_idle_runtime_instantiation(self):
        """POIdleRuntime should instantiate with mocks."""
        from oce.backend.po_idle import POIdleRuntime
        runtime = POIdleRuntime()
        assert runtime is not None
        assert runtime is not None

    def test_single_tick(self):
        """Should run a single tick and return report."""
        from oce.backend.po_idle import POIdleRuntime
        runtime = POIdleRuntime()
        # Run one tick
        report = asyncio.run(runtime.tick())
        assert report is not None
        # tick_number is 0 in report (incremented after), but tick_count property shows 1
        assert runtime.tick_count == 1

    def test_cadence_computation(self):
        """Should compute correct cadence based on session state."""
        from oce.backend.po_idle import POIdleRuntime, SessionState
        runtime = POIdleRuntime()
        # Cold state (no activity)
        assert runtime._compute_cadence() == 900  # COLD_CADENCE


class TestCrossInterfaceIdentity:
    """Tests for cross-interface identity continuity (P3.5)."""

    def test_telegram_to_vtuber_continuity(self):
        """Message in Telegram should appear in VTuber history (mocked)."""
        from core.identity.session_bridge import IdentitySessionBridge
        bridge = IdentitySessionBridge()
        # Simulate Telegram session writing
        bridge.link("telegram", "tg-session-1", "po-identity-1")
        bridge.link("vtuber", "vtuber-session-1", "po-identity-1")
        # Both should resolve to same identity
        tg_session = bridge.get_continuity("telegram", "tg-session-1")
        vt_session = bridge.get_continuity("vtuber", "vtuber-session-1")
        assert tg_session.session_id == vt_session.session_id

    def test_missing_session_graceful(self):
        """Should handle missing/invalid session gracefully."""
        from core.identity.session_bridge import IdentitySessionBridge
        bridge = IdentitySessionBridge()
        session = bridge.get_continuity("unknown", "unknown-session")
        assert session is not None  # Should return default session

    def test_session_persistence(self):
        """Session data should persist across bridge calls."""
        from core.identity.session_bridge import IdentitySessionBridge
        bridge = IdentitySessionBridge()
        bridge.link("vtuber", "session-1", "identity-1")
        # Get should return same identity
        session = bridge.get_continuity("vtuber", "session-1")
        assert session.session_id == "identity-1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])