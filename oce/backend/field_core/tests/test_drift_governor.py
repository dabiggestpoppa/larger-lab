"""
V3 Phase 9 — Sovereign Field Emergence
Tests for DriftGovernor module.
"""

import pytest
from oce.backend.field_core.drift_governor import (
    DriftGovernor,
    DriftMetrics,
)


class TestDriftMetrics:
    """Tests for DriftMetrics dataclass."""

    def test_metrics_creation(self):
        """Test creating drift metrics."""
        metrics = DriftMetrics(
            metrics_id="drift_1",
            element_id="elem_1",
            drift_score=0.3,
            divergence_rate=0.1,
        )
        assert metrics.metrics_id == "drift_1"
        assert metrics.element_id == "elem_1"
        assert metrics.drift_score == 0.3
        assert metrics.divergence_rate == 0.1

    def test_is_drifting_true(self):
        """Test is_drifting when score is high."""
        metrics = DriftMetrics(
            metrics_id="drift_1",
            element_id="elem_1",
            drift_score=0.6,
            divergence_rate=0.1,
        )
        assert metrics.is_drifting is True

    def test_is_drifting_false(self):
        """Test is_drifting when score is low."""
        metrics = DriftMetrics(
            metrics_id="drift_1",
            element_id="elem_1",
            drift_score=0.4,
            divergence_rate=0.1,
        )
        assert metrics.is_drifting is False

    def test_is_critical_true(self):
        """Test is_critical when score is very high."""
        metrics = DriftMetrics(
            metrics_id="drift_1",
            element_id="elem_1",
            drift_score=0.9,
            divergence_rate=0.1,
        )
        assert metrics.is_critical is True

    def test_is_critical_false(self):
        """Test is_critical when score is not high enough."""
        metrics = DriftMetrics(
            metrics_id="drift_1",
            element_id="elem_1",
            drift_score=0.7,
            divergence_rate=0.1,
        )
        assert metrics.is_critical is False


class TestDriftGovernor:
    """Tests for DriftGovernor."""

    def test_governor_empty(self):
        """Test empty governor."""
        governor = DriftGovernor()
        assert governor.stats["total_measurements"] == 0
        assert governor.get_drifting_elements() == []

    def test_set_threshold(self):
        """Test setting threshold."""
        governor = DriftGovernor()
        governor.set_threshold("elem_1", 0.3)
        assert governor._thresholds["elem_1"] == 0.3

    def test_measure_drift_no_drift(self):
        """Test measuring drift with no drift."""
        governor = DriftGovernor()
        metrics = governor.measure_drift(
            "elem_1",
            {"key": "value"},
            {"key": "value"},
        )
        assert metrics.drift_score == 0.0
        assert metrics.divergence_rate == 0.0

    def test_measure_drift_with_drift(self):
        """Test measuring drift with drift."""
        governor = DriftGovernor()
        metrics = governor.measure_drift(
            "elem_1",
            {"key": "value"},
            {"different": "state"},
        )
        assert metrics.drift_score == 1.0

    def test_measure_drift_partial(self):
        """Test measuring partial drift."""
        governor = DriftGovernor()
        metrics = governor.measure_drift(
            "elem_1",
            {"key1": "val1", "key2": "val2"},
            {"key1": "val1", "key2": "different"},
        )
        assert metrics.drift_score == 0.5

    def test_get_drifting_elements(self):
        """Test getting drifting elements."""
        governor = DriftGovernor()
        governor.measure_drift("elem_1", {"key": "value"}, {"key": "value"})
        governor.measure_drift("elem_2", {"key": "value"}, {"different": "state"})

        drifting = governor.get_drifting_elements()
        assert "elem_2" in drifting

    def test_get_critical_elements(self):
        """Test getting critical elements."""
        governor = DriftGovernor()
        governor.measure_drift("elem_1", {"key": "value"}, {"key": "value"})
        governor.measure_drift("elem_2", {"key": "value"}, {"diff": "state"})
        governor.measure_drift("elem_3", {"key": "value"}, {"another": "change"})

        critical = governor.get_critical_elements()
        assert "elem_3" in critical

    def test_reconstruction_trigger(self):
        """Test reconstruction is triggered when threshold exceeded."""
        governor = DriftGovernor()
        governor.set_threshold("elem_1", 0.5)
        governor.measure_drift("elem_1", {"key": "value"}, {"different": "state"})

        assert len(governor._reconstruction_triggers) == 1
        assert governor._reconstruction_triggers[0]["element_id"] == "elem_1"

    def test_get_drift_trend(self):
        """Test getting drift trend."""
        governor = DriftGovernor()
        governor.measure_drift("elem_1", {"key": "value"}, {"key": "value"})
        governor.measure_drift("elem_1", {"key": "value"}, {"key": "different"})

        trend = governor.get_drift_trend("elem_1")
        assert trend > 0  # Worsening drift

    def test_stats(self):
        """Test governor stats."""
        governor = DriftGovernor()
        governor.measure_drift("elem_1", {"key": "value"}, {"key": "value"})
        governor.measure_drift("elem_2", {"key": "value"}, {"different": "state"})

        stats = governor.stats
        assert stats["total_measurements"] == 2
        assert stats["drifting_elements"] == 1