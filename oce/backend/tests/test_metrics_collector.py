"""
Tests for OCE Metrics Collector — OCE-5.5a
===========================================
15+ tests covering event metrics, observer metrics, memory metrics,
entropy metrics, rolling counters, latency tracking, and history.
"""

import pytest
import time
import os
from pathlib import Path

# Reset singleton between tests
@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset the MetricsCollector singleton before each test."""
    from metrics_collector import MetricsCollector
    MetricsCollector._instance = None
    yield
    MetricsCollector._instance = None


class TestRollingCounter:
    """Tests for the RollingCounter helper class."""

    def test_add_and_count(self):
        from metrics_collector import RollingCounter
        counter = RollingCounter(window_seconds=60)
        counter.add(1)
        counter.add(1)
        counter.add(1)
        assert counter.count() == 3

    def test_rate_per_second(self):
        from metrics_collector import RollingCounter
        counter = RollingCounter(window_seconds=60)
        counter.add(1)
        time.sleep(0.1)
        counter.add(1)
        rate = counter.rate_per_second()
        assert rate > 0

    def test_prune_expired(self):
        from metrics_collector import RollingCounter
        counter = RollingCounter(window_seconds=1)
        counter.add(1)
        counter.add(1)
        assert counter.count() == 2
        time.sleep(1.1)
        assert counter.count() == 0

    def test_empty_counter(self):
        from metrics_collector import RollingCounter
        counter = RollingCounter(window_seconds=60)
        assert counter.count() == 0
        assert counter.rate_per_second() == 0.0


class TestLatencyTracker:
    """Tests for the LatencyTracker helper class."""

    def test_record_and_avg(self):
        from metrics_collector import LatencyTracker
        tracker = LatencyTracker(window_seconds=60)
        tracker.record(10.0)
        tracker.record(20.0)
        tracker.record(30.0)
        assert tracker.avg() == pytest.approx(20.0)

    def test_p95(self):
        from metrics_collector import LatencyTracker
        tracker = LatencyTracker(window_seconds=60)
        for i in range(100):
            tracker.record(float(i + 1))
        p95 = tracker.p95()
        assert p95 >= 95.0

    def test_p99(self):
        from metrics_collector import LatencyTracker
        tracker = LatencyTracker(window_seconds=60)
        for i in range(100):
            tracker.record(float(i + 1))
        p99 = tracker.p99()
        assert p99 >= 99.0

    def test_empty_tracker(self):
        from metrics_collector import LatencyTracker
        tracker = LatencyTracker(window_seconds=60)
        assert tracker.avg() == 0.0
        assert tracker.p95() == 0.0
        assert tracker.p99() == 0.0
        assert tracker.count() == 0


class TestEventMetrics:
    """Tests for event metrics recording and querying."""

    def test_record_event(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_event(event_type="test.event", source="test", latency_ms=5.0)
        summary = mc.get_metrics_summary()
        assert summary["events"]["total_count"] >= 1

    def test_event_count_by_type(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_event(event_type="custom.type", source="test")
        mc.record_event(event_type="custom.type", source="test")
        assert mc.get_event_type_count("custom.type") >= 2

    def test_event_latency_stats(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_event(event_type="test", source="test", latency_ms=10.0)
        mc.record_event(event_type="test", source="test", latency_ms=20.0)
        stats = mc.get_event_latency_stats()
        assert stats["count"] >= 2
        assert stats["avg_ms"] > 0

    def test_event_rate(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_event(event_type="rate_test", source="test")
        rate = mc.get_event_rate("total")
        assert rate >= 0.0


class TestObserverMetrics:
    """Tests for observer metrics recording and querying."""

    def test_record_observer_health(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_observer_health("obs-1", health_score=0.9, entropy=0.1)
        assert mc.get_observer_health("obs-1") == pytest.approx(0.9)

    def test_avg_health(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_observer_health("obs-1", health_score=0.8, entropy=0.1)
        mc.record_observer_health("obs-2", health_score=0.6, entropy=0.2)
        assert mc.get_avg_health() == pytest.approx(0.7)

    def test_observer_error_rate(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_observer_error("obs-err")
        mc.record_observer_error("obs-err")
        rate = mc.get_observer_error_rate("obs-err")
        assert rate >= 0.0

    def test_avg_health_empty(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        assert mc.get_avg_health() == 1.0


class TestMemoryMetrics:
    """Tests for memory metrics recording and querying."""

    def test_record_memory_usage(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_memory_usage("WORK", size_bytes=1024, entry_count=10)
        stats = mc.get_memory_stats()
        assert stats["total_size_bytes"] >= 1024
        assert stats["total_entries"] >= 10

    def test_compression_ratio(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_memory_usage("WORK", size_bytes=1000, entry_count=100)
        mc.record_compression_ratio("WORK", 0.5)
        stats = mc.get_memory_stats()
        assert "WORK" in stats["layers"]
        assert stats["layers"]["WORK"]["compression_ratio"] == 0.5

    def test_multiple_layers(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_memory_usage("WORK", size_bytes=500, entry_count=50)
        mc.record_memory_usage("LEARNED", size_bytes=300, entry_count=30)
        mc.record_memory_usage("KNOWLEDGE", size_bytes=200, entry_count=20)
        stats = mc.get_memory_stats()
        assert stats["total_entries"] >= 100


class TestEntropyMetrics:
    """Tests for entropy budget metrics."""

    def test_record_entropy_budget(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_entropy_budget(consumed=100.0, remaining=900.0, total=1000.0)
        stats = mc.get_entropy_stats()
        assert stats["total"] == 1000.0
        assert stats["remaining"] == 900.0

    def test_entropy_usage_pct(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_entropy_budget(consumed=500.0, remaining=500.0, total=1000.0)
        stats = mc.get_entropy_stats()
        assert 0 <= stats["usage_pct"] <= 100


class TestMetricsSummary:
    """Tests for the full metrics summary."""

    def test_summary_structure(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_event(event_type="test", source="test")
        mc.record_observer_health("obs-1", 0.9, 0.1)
        summary = mc.get_metrics_summary()
        assert "timestamp" in summary
        assert "events" in summary
        assert "observers" in summary
        assert "memory" in summary
        assert "entropy" in summary

    def test_save_snapshot(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_event(event_type="snap_test", source="test")
        mc.save_snapshot()
        history = mc.get_metrics_history("events.total_count", limit=10)
        assert len(history) >= 1

    def test_reset_counters(self):
        from metrics_collector import get_metrics_collector
        mc = get_metrics_collector()
        mc.record_event(event_type="reset_test", source="test")
        mc.reset_counters()
        summary = mc.get_metrics_summary()
        assert summary["events"]["total_count"] == 0


class TestSingleton:
    """Tests for singleton behavior."""

    def test_singleton_identity(self):
        from metrics_collector import get_metrics_collector
        mc1 = get_metrics_collector()
        mc2 = get_metrics_collector()
        assert mc1 is mc2

    def test_singleton_shared_state(self):
        from metrics_collector import get_metrics_collector, MetricsCollector
        # Reset for clean test
        MetricsCollector._instance = None
        mc1 = get_metrics_collector()
        mc1.record_event(event_type="singleton_test", source="test")
        mc2 = get_metrics_collector()
        assert mc2.get_event_type_count("singleton_test") >= 1
        MetricsCollector._instance = None
