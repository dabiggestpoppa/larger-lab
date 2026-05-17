"""
Tests for OCE Drift Detector — OCE-7.4a
=========================================
15+ tests covering latency trends, error rate trends, throughput trends,
queue depth, and full drift reports.
"""

import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_drift():
    """Reset the DriftDetector singleton before each test."""
    from drift_detector import DriftDetector
    DriftDetector._instance = None
    yield
    DriftDetector._instance = None


class TestDriftDetectorInit:
    """Tests for DriftDetector initialization."""

    def test_singleton_identity(self):
        from drift_detector import get_drift_detector
        d1 = get_drift_detector()
        d2 = get_drift_detector()
        assert d1 is d2

    def test_default_thresholds(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        assert d._thresholds["latency_increase_pct"] == 20.0
        assert d._thresholds["error_rate_increase_pct"] == 10.0
        assert d._thresholds["throughput_decrease_pct"] == 25.0
        assert d._thresholds["queue_depth_threshold"] == 50

    def test_configure_thresholds(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        d.configure_thresholds(latency_increase_pct=50.0)
        assert d._thresholds["latency_increase_pct"] == 50.0


class TestLatencyTrend:
    """Tests for latency trend analysis."""

    def test_no_data(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        result = d.analyze_latency_trend("skill_call")
        assert result["drift"] is False
        assert result["reason"] == "no data"

    def test_with_task_type(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        result = d.analyze_latency_trend("nonexistent_type")
        assert result["drift"] is False


class TestErrorRateTrend:
    """Tests for error rate trend analysis."""

    def test_no_data(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        result = d.analyze_error_rate_trend("skill_call")
        assert result["drift"] is False
        assert result["reason"] == "no data"

    def test_no_drift_without_exec_db(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        result = d.analyze_error_rate_trend()
        assert result["drift"] is False


class TestThroughputTrend:
    """Tests for throughput trend analysis."""

    def test_no_data(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        result = d.analyze_throughput_trend()
        assert result["drift"] is False
        assert result["reason"] == "no data"


class TestQueueDepth:
    """Tests for queue depth analysis."""

    def test_no_bottleneck_without_data(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        result = d.analyze_queue_depth()
        assert result["bottleneck"] is False
        assert result["current_depth"] == 0

    def test_structure(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        result = d.analyze_queue_depth()
        assert "bottleneck" in result
        assert "current_depth" in result
        assert "threshold" in result
        assert "pending_count" in result
        assert "running_count" in result


class TestDriftReport:
    """Tests for full drift report generation."""

    def test_healthy_report(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        report = d.get_drift_report()
        assert report["healthy"] is True
        assert report["overall_level"] == "none"
        assert report["drift_count"] == 0
        assert "timestamp" in report

    def test_report_structure(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        report = d.get_drift_report()
        assert "drifts" in report
        assert "overall_level" in report
        assert "healthy" in report


class TestAlertCallbacks:
    """Tests for alert callback registration."""

    def test_register_callback(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        callback = lambda r: None
        d.register_alert_callback(callback)
        assert len(d._alert_callbacks) == 1

    def test_multiple_callbacks(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        d.register_alert_callback(lambda r: None)
        d.register_alert_callback(lambda r: None)
        assert len(d._alert_callbacks) == 2


class TestDriftHistory:
    """Tests for drift report persistence."""

    def test_get_drift_history_empty(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        history = d.get_drift_history()
        assert isinstance(history, list)

    def test_report_persisted(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        d.get_drift_report()  # Generates and persists a report
        history = d.get_drift_history(limit=10)
        assert len(history) >= 1


class TestCooldown:
    """Tests for alert cooldown."""

    def test_alert_callback_registration(self):
        from drift_detector import get_drift_detector
        d = get_drift_detector()
        fired = []
        d.register_alert_callback(lambda r: fired.append(r))
        # Manually trigger with a critical report
        from drift_detector import DriftReport, DriftLevel
        report = DriftReport()
        report.add_drift("latency", "test", DriftLevel.CRITICAL, 100.0, 50.0, 100.0, "test rec")
        d._trigger_alerts(report)
        assert len(fired) == 1
