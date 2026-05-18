"""Tests for Self-Reflection Loop."""

import pytest
from oce.backend.introspection.self_reflection import SelfReflectionLoop, RepairRecord


class TestRepairRecord:
    def test_improvement(self):
        r = RepairRecord(
            record_id="r1", repair_type="coherence", trigger="drift",
            action_taken="repair", success=True, coherence_before=0.3, coherence_after=0.8,
        )
        assert r.improvement == pytest.approx(0.5, abs=0.01)


class TestSelfReflectionLoop:
    def test_record_repair(self):
        loop = SelfReflectionLoop()
        record = loop.record_repair("coherence", "drift", "repair", True, 0.3, 0.8)
        assert record.success is True
        assert record.improvement > 0

    def test_analyze_patterns(self):
        loop = SelfReflectionLoop()
        for _ in range(5):
            loop.record_repair("coherence", "drift", "repair", True, 0.3, 0.8)
        patterns = loop.analyze_patterns()
        assert patterns["total_repairs"] == 5

    def test_recommendations(self):
        loop = SelfReflectionLoop()
        for _ in range(5):
            loop.record_repair("bad_type", "trigger", "action", False, 0.5, 0.3)
        recs = loop.get_recommendations()
        assert len(recs) > 0

    def test_stats(self):
        loop = SelfReflectionLoop()
        loop.record_repair("test", "trigger", "action", True, 0.5, 0.8)
        stats = loop.stats
        assert stats["total_repairs"] == 1
