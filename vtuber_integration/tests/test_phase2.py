"""
Phase 2 Integration Tests — PO Cognitive Field Routing

Tests the full 5-stage cognitive pipeline:
- Workspace scanning
- Vault retrieval
- Agent coordination
- Model routing
- Streaming response generation
"""

import pytest
import sys
import os
import asyncio
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestWorkspaceScanner:
    """Tests for the workspace scanner component (P2.1)."""

    def test_scanner_instantiation(self):
        """WorkspaceScanner should instantiate without error."""
        from oce.backend.po_workspace import WorkspaceScanner
        scanner = WorkspaceScanner()
        assert scanner is not None
        assert scanner.repo_root is not None

    def test_scan_returns_result(self):
        """Scan should return a ScanResult with expected fields."""
        from oce.backend.po_workspace import WorkspaceScanner
        scanner = WorkspaceScanner()
        result = scanner.scan()
        assert result is not None
        assert hasattr(result, "files_scanned")
        assert hasattr(result, "files_fresh")
        assert hasattr(result, "python_files")
        assert hasattr(result, "summary")
        summary = result.summary()
        assert "files_scanned" in summary
        assert "fresh" in summary

    def test_scan_delta(self):
        """scan_delta should return change information."""
        from oce.backend.po_workspace import WorkspaceScanner
        scanner = WorkspaceScanner()
        delta = scanner.scan_delta(time.time() - 60)
        assert "files_fresh" in delta
        assert "changed_files" in delta
        assert "patterns_found" in delta

    def test_pattern_detection(self):
        """Scanner should detect TODO/FIXME patterns in Python files."""
        from oce.backend.po_workspace import WorkspaceScanner
        scanner = WorkspaceScanner()
        result = scanner.scan()
        # Patterns may or may not exist, but the mechanism should work
        assert isinstance(result.patterns_found, dict)


class TestVaultRetriever:
    """Tests for the vault retrieval component (P2.2)."""

    def test_retriever_instantiation(self):
        """VaultRetriever should instantiate without error."""
        from oce.backend.po_vault import VaultRetriever
        retriever = VaultRetriever()
        assert retriever is not None

    def test_retrieve_returns_result(self):
        """Retrieve should return a RetrievalResult."""
        from oce.backend.po_vault import VaultRetriever
        retriever = VaultRetriever()
        result = retriever.retrieve("test query")
        assert result is not None
        assert hasattr(result, "hits")
        assert hasattr(result, "summary")
        assert hasattr(result, "top_hits")
        assert hasattr(result, "as_context_string")

    def test_retrieval_summary(self):
        """Summary should contain expected keys."""
        from oce.backend.po_vault import VaultRetriever
        retriever = VaultRetriever()
        result = retriever.retrieve("test")
        summary = result.summary()
        assert "query" in summary
        assert "hits" in summary
        assert "sources" in summary

    def test_context_string_generation(self):
        """Should generate a context string for LLM consumption."""
        from oce.backend.po_vault import VaultRetriever
        retriever = VaultRetriever()
        result = retriever.retrieve("test")
        ctx = result.as_context_string(max_tokens=1000)
        assert isinstance(ctx, str)


class TestThoughtStreamer:
    """Tests for the cognitive streaming pipeline (P2.3)."""

    def test_streamer_instantiation(self):
        """ThoughtStreamer should instantiate without error."""
        from oce.backend.po_stream import ThoughtStreamer
        streamer = ThoughtStreamer()
        assert streamer is not None

    def test_pipeline_initialization(self):
        """ThoughtPipeline should initialize with 5 stages."""
        from oce.backend.po_stream import ThoughtPipeline
        pipeline = ThoughtPipeline()
        assert len(pipeline.stages) == 5
        assert pipeline.current_stage_idx == 0
        stage_names = [s.name for s in pipeline.stages]
        assert stage_names == ["processing", "scanning", "retrieving", "routing", "responding"]

    def test_pipeline_advance(self):
        """Pipeline should advance through stages."""
        from oce.backend.po_stream import ThoughtPipeline
        pipeline = ThoughtPipeline()
        assert pipeline.current_stage().name == "processing"
        next_stage = pipeline.advance()
        assert next_stage is not None
        assert next_stage.name == "scanning"
        assert pipeline.current_stage_idx == 1

    def test_pipeline_status_dict(self):
        """Pipeline should serialize to status dict."""
        from oce.backend.po_stream import ThoughtPipeline
        pipeline = ThoughtPipeline()
        pipeline.request_id = "test-123"
        pipeline.session_id = "session-abc"
        status = pipeline.to_status_dict()
        assert status["request_id"] == "test-123"
        assert status["session_id"] == "session-abc"
        assert len(status["stages"]) == 5


class TestAgentCoordinator:
    """Tests for agent coordination (P2.4)."""

    def test_coordinator_instantiation(self):
        """AgentCoordinator should instantiate with default agents."""
        from oce.backend.po_agents import AgentCoordinator
        coord = AgentCoordinator()
        assert coord is not None
        agents = coord.list_agents()
        assert len(agents) >= 3  # analyst, researcher, coder

    def test_agent_registration(self):
        """Should be able to register custom agents."""
        from oce.backend.po_agents import AgentCoordinator, AgentSpec
        coord = AgentCoordinator()
        coord.register_agent(AgentSpec(name="tester", role="Testing"))
        agents = coord.list_agents()
        assert any(a["name"] == "tester" for a in agents)

    def test_agent_selection(self):
        """Coordinator should select appropriate agent for task."""
        from oce.backend.po_agents import AgentCoordinator, AgentTask
        coord = AgentCoordinator()
        task = AgentTask(task_id="test-1", agent_name="", prompt="write some code to sort a list")
        selected = coord._select_agent(task)
        assert selected is not None
        assert selected.name == "coder"


class TestModelRouter:
    """Tests for multi-model routing (P2.5)."""

    def test_router_instantiation(self):
        """ModelRouter should instantiate with default models."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        assert router is not None
        models = router.list_models()
        assert len(models) >= 1

    def test_route_returns_decision(self):
        """Route should return a RouteDecision."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        decision = router.route("test query")
        assert decision is not None
        assert hasattr(decision, "model_id")
        assert hasattr(decision, "provider")
        assert hasattr(decision, "fallback_chain")

    def test_po_is_primary(self):
        """Default routing should select PO as primary."""
        from oce.backend.po_router import ModelRouter
        router = ModelRouter()
        decision = router.route("any query")
        assert decision.model_id == "po"
        assert decision.provider == "oce"

    def test_model_registration(self):
        """Should be able to register and deregister models."""
        from oce.backend.po_router import ModelRouter, ModelInfo
        router = ModelRouter()
        router.register_model(ModelInfo(id="test/model", name="Test", provider="test"))
        assert router.get_model("test/model") is not None
        router.deregister_model("test/model")
        assert router.get_model("test/model") is None


class TestPOEvents:
    """Tests for PO event schema (P2.11)."""

    def test_all_event_types(self):
        """All POEventType values should be defined."""
        from oce.backend.po_events import POEventType
        assert POEventType.STATUS.value == "status"
        assert POEventType.WORKSPACE_SCAN.value == "workspace_scan"
        assert POEventType.VAULT_RETRIEVAL.value == "vault_retrieval"
        assert POEventType.AGENT_SPAWN.value == "agent_spawn"
        assert POEventType.STREAM_CHUNK.value == "chunk"
        assert POEventType.STREAM_DONE.value == "done"
        assert POEventType.STREAM_ERROR.value == "error"
        assert POEventType.STREAM_CANCELLED.value == "cancelled"

    def test_status_event_serialization(self):
        """StatusEvent should serialize to dict."""
        from oce.backend.po_events import StatusEvent
        evt = StatusEvent(stage="test", message="test message")
        d = evt.to_dict()
        assert d["type"] == "status"
        assert d["stage"] == "test"

    def test_stream_chunk_openai_shape(self):
        """StreamChunkEvent should produce OpenAI-compatible format."""
        from oce.backend.po_events import StreamChunkEvent
        evt = StreamChunkEvent(content="hello world")
        d = evt.to_dict()
        assert d["type"] == "chunk"
        assert "choices" in d
        assert d["choices"][0]["delta"]["content"] == "hello world"


class TestPOStatePersistence:
    """Tests for PO state persistence (P2.10)."""

    def test_state_store_instantiation(self):
        """POStateStore should instantiate."""
        from oce.backend.po_state import POStateStore
        store = POStateStore(state_dir="/tmp/po_test_state")
        assert store is not None

    def test_state_crud(self):
        """Should be able to save and load state."""
        from oce.backend.po_state import POStateStore, POStateSnapshot
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            store = POStateStore(state_dir=tmpdir)
            snapshot = POStateSnapshot(
                timestamp=0,
                active_sessions=5,
                total_messages=100,
                total_turns=50,
                cognitive_load=0.5,
            )
            store.save_state(snapshot)
            loaded = store.load_state()
            assert loaded.active_sessions == 5
            assert loaded.total_messages == 100

    def test_session_crud(self):
        """Should be able to save and load session data."""
        from oce.backend.po_state import POStateStore
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            store = POStateStore(state_dir=tmpdir)
            store.save_session("test-session", {"turns": 5, "status": "active"})
            data = store.load_session("test-session")
            assert data["turns"] == 5


class TestPOInterrupt:
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


class TestPOSession:
    """Tests for session management (P2.6)."""

    def test_session_creation(self):
        """Should create sessions with unique IDs."""
        from oce.backend.po_session import POSession
        session = POSession()
        assert session.session_id is not None
        assert len(session.session_id) > 0

    def test_session_add_message(self):
        """Should add messages and track turns."""
        from oce.backend.po_session import POSession
        session = POSession()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there!")
        assert session.turn_count == 2
        assert len(session.messages) == 2

    def test_session_context(self):
        """Should return formatted context string."""
        from oce.backend.po_session import POSession
        session = POSession()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")
        ctx = session.get_context()
        assert "user" in ctx
        assert "Hello" in ctx

    def test_session_state(self):
        """Should return state snapshot."""
        from oce.backend.po_session import POSession
        session = POSession()
        session.add_message("user", "test")
        state = session.get_state()
        assert state.message_count == 1
        assert state.turn_count == 1


class TestPOFallback:
    """Tests for fallback chain (P3.2)."""

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])