"""Tests for Strategic Memory Engine."""

import pytest
from oce.backend.temporal.strategic_memory import StrategicMemoryEngine, StrategicInsight


class TestStrategicInsight:
    def test_reliable(self):
        i = StrategicInsight(
            insight_id="i1", insight_type="success_pattern",
            description="test", confidence=0.8, evidence_count=5,
        )
        assert i.is_reliable is True

    def test_not_reliable(self):
        i = StrategicInsight(
            insight_id="i1", insight_type="success_pattern",
            description="test", confidence=0.3, evidence_count=1,
        )
        assert i.is_reliable is False


class TestStrategicMemoryEngine:
    def test_record_outcome(self):
        engine = StrategicMemoryEngine()
        engine.record_outcome("pattern_a", success=True, context="test")
        assert "pattern_a" in engine._pattern_evidence

    def test_success_pattern(self):
        engine = StrategicMemoryEngine()
        for _ in range(5):
            engine.record_outcome("good_pattern", success=True, context="test")
        insights = engine.get_success_patterns()
        assert len(insights) >= 1

    def test_failure_pattern(self):
        engine = StrategicMemoryEngine()
        for _ in range(5):
            engine.record_outcome("bad_pattern", success=False, context="test")
        insights = engine.get_failure_patterns()
        assert len(insights) >= 1

    def test_predict_outcome(self):
        engine = StrategicMemoryEngine()
        for _ in range(5):
            engine.record_outcome("test_pattern", success=True, context="test")
        prediction = engine.predict_outcome("test_pattern")
        assert prediction is not None
        assert prediction > 0.5

    def test_stats(self):
        engine = StrategicMemoryEngine()
        engine.record_outcome("p1", success=True, context="test")
        stats = engine.stats
        assert stats["patterns_tracked"] == 1
