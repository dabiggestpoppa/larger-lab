"""
PO × VTuber Integration — Smoke Tests

Phase 1.6: Verify PO Provider can be loaded and produces valid responses
through the OCE /api/po/chat endpoint.
"""

import pytest
import sys
import os

# Ensure repo root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestPOProviderLoading:
    """Test that the PO provider module can be imported and instantiated."""

    def test_import_po_provider(self):
        """PO Provider module should import without errors."""
        from vtuber_integration.po_provider.po_provider import POProvider
        assert POProvider is not None

    def test_po_provider_instantiation(self):
        """PO Provider should instantiate with default config."""
        from vtuber_integration.po_provider.po_provider import POProvider
        provider = POProvider()
        assert provider.config.model == "po"
        assert provider.config.oce_url == "http://localhost:8000"

    def test_po_provider_custom_config(self):
        """PO Provider should accept custom config."""
        from vtuber_integration.po_provider.po_provider import POProvider
        provider = POProvider(
            model="po",
            base_url="http://localhost:8000",
            temperature=0.5,
        )
        assert provider.config.model == "po"
        assert provider.config.temperature == 0.5


class TestPOProviderInterface:
    """Test that PO Provider implements the StatelessLLMInterface contract."""

    def test_has_chat_completion_method(self):
        """PO Provider must have chat_completion method."""
        from vtuber_integration.po_provider.po_provider import POProvider
        provider = POProvider()
        assert hasattr(provider, "chat_completion")
        assert callable(provider.chat_completion)

    def test_has_close_method(self):
        """PO Provider should have close() for cleanup."""
        from vtuber_integration.po_provider.po_provider import POProvider
        provider = POProvider()
        assert hasattr(provider, "close")
        assert callable(provider.close)

    def test_provider_repr(self):
        """PO Provider should have a useful repr."""
        from vtuber_integration.po_provider.po_provider import POProvider
        provider = POProvider(model="po", base_url="http://localhost:8000")
        r = repr(provider)
        assert "POProvider" in r
        assert "po" in r


class TestPOAPIEndpoints:
    """Test that OCE PO API endpoints are registered and respond."""

    def test_po_api_module_exists(self):
        """po_api module should exist in oce/backend."""
        from oce.backend import po_api
        assert po_api is not None
        assert hasattr(po_api, "router")

    def test_po_api_router_has_routes(self):
        """PO API router should have routes registered."""
        from oce.backend.po_api import router
        routes = [r.path for r in router.routes]
        assert "/chat" in routes or any("chat" in r for r in routes)
        assert "/status" in routes or any("status" in r for r in routes)

    def test_po_api_registered_in_main(self):
        """PO API router should be included in OCE main app."""
        from oce.backend.main import app
        # Check that PO routes are accessible
        route_paths = [r.path for r in app.routes]
        # The router may be mounted at root or with prefix
        has_po_routes = any("po" in str(p) or "chat" in str(p) for p in route_paths)
        assert has_po_routes, f"No PO routes found in app routes: {route_paths}"


class TestPOEvents:
    """Test that PO event schema is properly defined."""

    def test_event_types_enum(self):
        """POEventType should have expected values."""
        from oce.backend.po_events import POEventType
        assert POEventType.STATUS.value == "status"
        assert POEventType.WORKSPACE_SCAN.value == "workspace_scan"
        assert POEventType.VAULT_RETRIEVAL.value == "vault_retrieval"
        assert POEventType.AGENT_SPAWN.value == "agent_spawn"
        assert POEventType.STREAM_CHUNK.value == "chunk"
        assert POEventType.STREAM_DONE.value == "done"

    def test_status_event(self):
        """StatusEvent should serialize correctly."""
        from oce.backend.po_events import StatusEvent
        evt = StatusEvent(stage="processing", message="🧠 Thinking...")
        d = evt.to_dict()
        assert d["type"] == "status"
        assert d["stage"] == "processing"

    def test_stream_chunk_event(self):
        """StreamChunkEvent should produce OpenAI-shape output."""
        from oce.backend.po_events import StreamChunkEvent
        evt = StreamChunkEvent(content="hello")
        d = evt.to_dict()
        assert d["type"] == "chunk"
        assert "choices" in d
        assert d["choices"][0]["delta"]["content"] == "hello"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])