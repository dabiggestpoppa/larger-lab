"""
V3 Phase 9 — Sovereign Field Emergence
Tests for ResonanceEngine module.
"""

import pytest
import math
from oce.backend.field_core.resonance_engine import (
    ResonanceEngine,
    ResonanceState,
)


class TestResonanceState:
    """Tests for ResonanceState dataclass."""

    def test_state_creation(self):
        """Test creating a resonance state."""
        state = ResonanceState(
            state_id="test_1",
            element_a="node_a",
            element_b="node_b",
            resonance_score=0.75,
            phase_alignment=0.8,
        )
        assert state.state_id == "test_1"
        assert state.element_a == "node_a"
        assert state.element_b == "node_b"
        assert state.resonance_score == 0.75
        assert state.phase_alignment == 0.8

    def test_is_resonant_true(self):
        """Test is_resonant when score > 0.6."""
        state = ResonanceState(
            state_id="test_1",
            element_a="a",
            element_b="b",
            resonance_score=0.7,
            phase_alignment=0.5,
        )
        assert state.is_resonant is True

    def test_is_resonant_false(self):
        """Test is_resonant when score <= 0.6."""
        state = ResonanceState(
            state_id="test_1",
            element_a="a",
            element_b="b",
            resonance_score=0.5,
            phase_alignment=0.5,
        )
        assert state.is_resonant is False

    def test_is_aligned_true(self):
        """Test is_aligned when phase > 0.5."""
        state = ResonanceState(
            state_id="test_1",
            element_a="a",
            element_b="b",
            resonance_score=0.5,
            phase_alignment=0.7,
        )
        assert state.is_aligned is True

    def test_is_aligned_false(self):
        """Test is_aligned when phase <= 0.5."""
        state = ResonanceState(
            state_id="test_1",
            element_a="a",
            element_b="b",
            resonance_score=0.5,
            phase_alignment=0.3,
        )
        assert state.is_aligned is False


class TestResonanceEngineInit:
    """Tests for ResonanceEngine initialization."""

    def test_init_empty(self):
        """Test engine initializes with empty state."""
        engine = ResonanceEngine()
        assert engine._states == []
        assert engine._coherence_history == []

    def test_stats_empty(self):
        """Test stats on empty engine."""
        engine = ResonanceEngine()
        stats = engine.stats
        assert stats["total_measurements"] == 0
        assert stats["field_coherence"] == 0.5  # default


class TestMeasureResonance:
    """Tests for measure_resonance method."""

    def test_measure_basic(self):
        """Test basic resonance measurement."""
        engine = ResonanceEngine()
        state = engine.measure_resonance("a", "b", 1.0, 1.0, 0.0, 0.0)

        assert state.element_a == "a"
        assert state.element_b == "b"
        assert state.resonance_score == 1.0  # 1.0 * 1.0 * 1.0
        assert state.phase_alignment == 1.0

    def test_measure_phase_mismatch(self):
        """Test resonance with phase mismatch."""
        engine = ResonanceEngine()
        state = engine.measure_resonance("a", "b", 1.0, 1.0, 0.0, math.pi)

        # Phase diff = pi, alignment = 1 - pi/pi = 0
        assert state.phase_alignment == 0.0
        assert state.resonance_score == 0.0

    def test_measure_half_phase(self):
        """Test resonance with half-phase difference."""
        engine = ResonanceEngine()
        state = engine.measure_resonance("a", "b", 1.0, 1.0, 0.0, math.pi / 2)

        # Phase diff = pi/2, alignment = 1 - (pi/2)/pi = 0.5
        assert state.phase_alignment == 0.5
        assert state.resonance_score == 0.5

    def test_measure_amplitude_scaling(self):
        """Test resonance scales with amplitude."""
        engine = ResonanceEngine()
        state = engine.measure_resonance("a", "b", 0.5, 0.5, 0.0, 0.0)

        assert state.resonance_score == 0.25  # 0.5 * 0.5 * 1.0


class TestFieldCoherence:
    """Tests for field coherence methods."""

    def test_get_field_coherence_empty(self):
        """Test coherence on empty engine."""
        engine = ResonanceEngine()
        assert engine.get_field_coherence() == 0.5

    def test_get_field_coherence_single(self):
        """Test coherence with single measurement."""
        engine = ResonanceEngine()
        engine.measure_resonance("a", "b", 1.0, 1.0, 0.0, 0.0)
        assert engine.get_field_coherence() == 1.0

    def test_get_field_coherence_multiple(self):
        """Test coherence with multiple measurements."""
        engine = ResonanceEngine()
        engine.measure_resonance("a", "b", 1.0, 1.0, 0.0, 0.0)  # 1.0
        engine.measure_resonance("c", "d", 0.5, 0.5, 0.0, 0.0)  # 0.25
        # Average of last 20 (both) = 0.625
        assert engine.get_field_coherence() == pytest.approx(0.625, rel=0.01)


class TestAlignmentPattern:
    """Tests for alignment pattern detection."""

    def test_empty_pattern(self):
        """Test pattern on empty engine."""
        engine = ResonanceEngine()
        pattern = engine.get_alignment_pattern()
        assert pattern["aligned"] == 0
        assert pattern["misaligned"] == 0
        assert pattern["total"] == 0

    def test_aligned_pattern(self):
        """Test pattern with aligned measurements."""
        engine = ResonanceEngine()
        engine.measure_resonance("a", "b", 1.0, 1.0, 0.0, 0.0)  # aligned
        engine.measure_resonance("c", "d", 1.0, 1.0, 0.0, 0.1)  # aligned
        pattern = engine.get_alignment_pattern()
        assert pattern["aligned"] == 2
        assert pattern["alignment_rate"] == 1.0

    def test_mixed_pattern(self):
        """Test pattern with mixed alignment."""
        engine = ResonanceEngine()
        engine.measure_resonance("a", "b", 1.0, 1.0, 0.0, 0.0)  # aligned (phase diff = 0)
        engine.measure_resonance("c", "d", 1.0, 1.0, 0.0, 0.6)  # phase diff = 0.6, alignment = 1 - 0.6/pi ≈ 0.53
        pattern = engine.get_alignment_pattern()
        # Both are aligned since 0.53 > 0.5
        assert pattern["aligned"] == 2
        assert pattern["misaligned"] == 0


class TestResonantPairs:
    """Tests for finding resonant pairs."""

    def test_find_resonant_pairs_empty(self):
        """Test finding pairs on empty engine."""
        engine = ResonanceEngine()
        assert engine.find_resonant_pairs() == []

    def test_find_resonant_pairs_threshold(self):
        """Test threshold filtering."""
        engine = ResonanceEngine()
        engine.measure_resonance("a", "b", 1.0, 1.0, 0.0, 0.0)  # 1.0
        engine.measure_resonance("c", "d", 0.5, 0.5, 0.0, 0.0)  # 0.25
        pairs = engine.find_resonant_pairs(threshold=0.5)
        assert len(pairs) == 1
        assert pairs[0].element_a == "a"


class TestCoherenceTrend:
    """Tests for coherence trend calculation."""

    def test_trend_empty(self):
        """Test trend on empty history."""
        engine = ResonanceEngine()
        assert engine.get_coherence_trend() == 0.0

    def test_trend_single(self):
        """Test trend with single measurement."""
        engine = ResonanceEngine()
        engine.record_coherence(0.5)
        assert engine.get_coherence_trend() == 0.0

    def test_trend_improving(self):
        """Test improving trend."""
        engine = ResonanceEngine()
        for i in range(10):
            engine.record_coherence(0.3 + i * 0.1)  # 0.3 to 1.2
        trend = engine.get_coherence_trend()
        assert trend > 0  # positive trend

    def test_trend_declining(self):
        """Test declining trend."""
        engine = ResonanceEngine()
        for i in range(10):
            engine.record_coherence(1.0 - i * 0.1)  # 1.0 to 0.1
        trend = engine.get_coherence_trend()
        assert trend < 0  # negative trend


class TestStats:
    """Tests for stats property."""

    def test_stats_with_data(self):
        """Test stats with measurements."""
        engine = ResonanceEngine()
        engine.measure_resonance("a", "b", 1.0, 1.0, 0.0, 0.0)
        engine.measure_resonance("c", "d", 1.0, 1.0, 0.0, 0.0)
        engine.record_coherence(0.8)

        stats = engine.stats
        assert stats["total_measurements"] == 2
        assert stats["field_coherence"] == 1.0
        assert stats["resonant_pairs"] == 2
        assert "coherence_trend" in stats