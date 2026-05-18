"""Tests for Resonance Mapper."""

import pytest
import math
from oce.backend.cognition.resonance_mapper import ResonanceMapper, ResonanceSnapshot


class TestResonanceSnapshot:
    def test_overall_resonance(self):
        s = ResonanceSnapshot(
            timestamp=0, coherence_score=0.8, entropy_gradient=0.1,
            observer_alignment=0.9, trajectory_stability=0.7, signal_density=0.2,
        )
        assert s.overall_resonance > 0.5


class TestResonanceMapper:
    def test_creation(self):
        mapper = ResonanceMapper()
        assert mapper is not None

    def test_update_observer(self):
        mapper = ResonanceMapper()
        mapper.update_observer("obs1", phase=0.0, coherence=0.9)
        assert "obs1" in mapper._observer_phases

    def test_measure(self):
        mapper = ResonanceMapper()
        mapper.update_observer("obs1", 0.0, 0.9)
        mapper.update_observer("obs2", 0.1, 0.85)
        snap = mapper.measure(field_coherence=0.8, entropy_delta=0.1)
        assert snap.coherence_score == 0.8
        assert 0.0 <= snap.overall_resonance <= 1.0

    def test_observer_alignment(self):
        mapper = ResonanceMapper()
        mapper.update_observer("obs1", 0.0, 0.9)
        mapper.update_observer("obs2", 0.1, 0.85)
        alignment = mapper._calc_observer_alignment()
        assert alignment > 0.9  # Very close phases = high alignment

    def test_trend(self):
        mapper = ResonanceMapper()
        for i in range(5):
            mapper.measure(field_coherence=0.5 + i * 0.1)
        trend = mapper.get_trend("coherence_score")
        assert isinstance(trend, float)

    def test_stats(self):
        mapper = ResonanceMapper()
        mapper.measure(field_coherence=0.8)
        stats = mapper.stats
        assert stats["total_measurements"] == 1
