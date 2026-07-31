"""
Tests for OCE Tracing Engine — OCE-5.5b
=========================================
15+ tests covering trace lifecycle, hops, queries, search, and stats.
"""

import pytest
import time
from unittest.mock import patch

@pytest.fixture(autouse=True)
def reset_tracing():
    """Reset the TracingEngine singleton before each test."""
    from tracing_engine import TracingEngine
    TracingEngine._instance = None
    yield
    TracingEngine._instance = None


class TestTraceLifecycle:
    """Tests for trace start/add_hop/end lifecycle."""

    def test_start_trace(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        trace_id = engine.start_trace(
            event_id="evt-1", event_type="test.event", source="test"
        )
        assert trace_id is not None
        assert len(trace_id) > 0

    def test_start_trace_creates_active(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        trace_id = engine.start_trace(
            event_id="evt-1", event_type="test.event", source="test"
        )
        active = engine.get_active_traces()
        assert any(t["trace_id"] == trace_id for t in active)

    def test_add_hop(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        trace_id = engine.start_trace(
            event_id="evt-1", event_type="test.event", source="test"
        )
        engine.add_hop(trace_id, "obs-1", "process", 5.0)
        engine.add_hop(trace_id, "obs-2", "forward", 3.0)
        trace = engine.get_trace(trace_id)
        assert trace is not None
        assert len(trace["hops"]) == 2
        assert trace["total_latency_ms"] == pytest.approx(8.0)

    def test_end_trace_success(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        trace_id = engine.start_trace(
            event_id="evt-1", event_type="test.event", source="test"
        )
        engine.add_hop(trace_id, "obs-1", "process", 5.0)
        engine.end_trace(trace_id, outcome="success")
        trace = engine.get_trace(trace_id)
        assert trace is not None
        assert trace["outcome"] == "success"
        assert trace["ended_at"] is not None

    def test_end_trace_error(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        trace_id = engine.start_trace(
            event_id="evt-1", event_type="test.event", source="test"
        )
        engine.end_trace(trace_id, outcome="error", error_message="test failure")
        trace = engine.get_trace(trace_id)
        assert trace["outcome"] == "error"
        assert trace["error_message"] == "test failure"

    def test_end_trace_removes_from_active(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        trace_id = engine.start_trace(
            event_id="evt-1", event_type="test.event", source="test"
        )
        engine.end_trace(trace_id)
        active = engine.get_active_traces()
        assert not any(t["trace_id"] == trace_id for t in active)


class TestTraceQueries:
    """Tests for trace query methods."""

    def test_get_trace_not_found(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        result = engine.get_trace("nonexistent-id")
        assert result is None

    def test_get_active_traces_empty(self):
        from tracing_engine import get_tracing_engine, TracingEngine
        TracingEngine._instance = None
        engine = get_tracing_engine()
        assert engine.get_active_traces() == []
        TracingEngine._instance = None

    def test_get_traces_by_observer(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        trace_id = engine.start_trace(
            event_id="evt-1", event_type="test.event", source="test"
        )
        engine.add_hop(trace_id, "target-obs", "process", 5.0)
        engine.end_trace(trace_id)
        traces = engine.get_traces_by_observer("target-obs")
        assert len(traces) >= 1

    def test_get_traces_by_observer_not_found(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        traces = engine.get_traces_by_observer("nonexistent-obs")
        assert traces == []


class TestTraceSearch:
    """Tests for trace search with filters."""

    def test_search_by_event_type(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        tid = engine.start_trace("evt-1", "custom.type", "test")
        engine.end_trace(tid)
        results = engine.search_traces(event_type="custom.type")
        assert len(results) >= 1

    def test_search_by_outcome(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        tid = engine.start_trace("evt-1", "test", "test")
        engine.end_trace(tid, outcome="error")
        results = engine.search_traces(outcome="error")
        assert len(results) >= 1

    def test_search_by_source(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        tid = engine.start_trace("evt-1", "test", "custom-source")
        engine.end_trace(tid)
        results = engine.search_traces(source="custom-source")
        assert len(results) >= 1

    def test_search_by_min_latency(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        tid = engine.start_trace("evt-1", "test", "test")
        engine.add_hop(tid, "obs", "process", 100.0)
        engine.end_trace(tid)
        results = engine.search_traces(min_latency_ms=50.0)
        assert len(results) >= 1

    def test_search_limit(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        for i in range(5):
            tid = engine.start_trace(f"evt-{i}", "test", "test")
            engine.end_trace(tid)
        results = engine.search_traces(limit=3)
        assert len(results) <= 3


class TestTraceStats:
    """Tests for tracing statistics."""

    def test_stats_structure(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        stats = engine.get_stats()
        assert "active_traces" in stats
        assert "completed_traces" in stats
        assert "avg_latency_ms" in stats
        assert "outcome_distribution" in stats
        assert "ttl_sec" in stats

    def test_stats_active_count(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        engine.start_trace("evt-1", "test", "test")
        stats = engine.get_stats()
        assert stats["active_traces"] >= 1


class TestTraceHop:
    """Tests for TraceHop model."""

    def test_hop_fields(self):
        from tracing_engine import TraceHop
        hop = TraceHop(observer_id="obs-1", action="process", latency_ms=5.0)
        assert hop.observer_id == "obs-1"
        assert hop.action == "process"
        assert hop.latency_ms == 5.0

    def test_hop_metadata(self):
        from tracing_engine import TraceHop
        hop = TraceHop(
            observer_id="obs-1", action="process", latency_ms=5.0,
            metadata={"key": "value"}
        )
        assert hop.metadata["key"] == "value"


class TestTraceOutcome:
    """Tests for TraceOutcome enum."""

    def test_outcome_values(self):
        from tracing_engine import TraceOutcome
        assert TraceOutcome.SUCCESS.value == "success"
        assert TraceOutcome.ERROR.value == "error"
        assert TraceOutcome.DROPPED.value == "dropped"
        assert TraceOutcome.TIMEOUT.value == "timeout"
        assert TraceOutcome.IN_PROGRESS.value == "in_progress"


class TestSingleton:
    """Tests for singleton behavior."""

    def test_singleton_identity(self):
        from tracing_engine import get_tracing_engine
        e1 = get_tracing_engine()
        e2 = get_tracing_engine()
        assert e1 is e2

    def test_add_hop_nonexistent_trace(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        # Should not raise
        engine.add_hop("nonexistent", "obs", "process", 1.0)

    def test_end_nonexistent_trace(self):
        from tracing_engine import get_tracing_engine
        engine = get_tracing_engine()
        # Should not raise
        engine.end_trace("nonexistent")
