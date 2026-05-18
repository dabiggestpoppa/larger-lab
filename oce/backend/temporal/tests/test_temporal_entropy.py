"""Tests for Temporal Entropy Governance."""

import pytest
from oce.backend.temporal.temporal_entropy import TemporalEntropyGovernance, EntropyAssessment


class TestEntropyAssessment:
    def test_critical(self):
        a = EntropyAssessment(timestamp=0, overall_entropy=0.8)
        assert a.is_critical is True

    def test_not_critical(self):
        a = EntropyAssessment(timestamp=0, overall_entropy=0.2)
        assert a.is_critical is False


class TestTemporalEntropyGovernance:
    def test_assess(self):
        gov = TemporalEntropyGovernance()
        result = gov.assess(drift_score=0.3, memory_size=100)
        assert isinstance(result, EntropyAssessment)
        assert 0.0 <= result.overall_entropy <= 1.0

    def test_assess_critical(self):
        gov = TemporalEntropyGovernance()
        result = gov.assess(drift_score=0.9, memory_size=5000, mission_count=8, glyph_count=60, topology_changes=15)
        assert result.is_critical

    def test_get_trend(self):
        gov = TemporalEntropyGovernance()
        gov.assess(drift_score=0.1)
        gov.assess(drift_score=0.5)
        trend = gov.get_trend()
        assert isinstance(trend, float)

    def test_recommendations(self):
        gov = TemporalEntropyGovernance()
        gov.assess(drift_score=0.9, memory_size=5000, mission_count=8)
        recs = gov.get_recommendations()
        assert len(recs) > 0

    def test_stats(self):
        gov = TemporalEntropyGovernance()
        gov.assess(drift_score=0.3)
        stats = gov.stats
        assert stats["total_assessments"] == 1
