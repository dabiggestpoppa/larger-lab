"""Tests for ContinuityRepairLoop."""

import pytest
from oce.backend.reconstruction.continuity_repair import ContinuityRepairLoop


class TestContinuityRepairLoop:
    def test_detect_fractures_empty(self):
        repair = ContinuityRepairLoop()
        fractures = repair.detect_fractures()
        assert len(fractures) == 0

    def test_detect_lineage_fracture(self):
        repair = ContinuityRepairLoop()
        repair.reconstruction_engine.record_state_transition("s1", "s2", continuity_strength=0.1)
        repair.reconstruction_engine.record_state_transition("s2", "s3", continuity_strength=0.1)
        fractures = repair.detect_fractures()
        assert len(fractures) >= 1
        assert fractures[0]["type"] == "lineage_fracture"

    def test_repair_success(self):
        repair = ContinuityRepairLoop()
        repair.reconstruction_engine.attractor_memory.create_attractor(
            "stable", ["obs1"], coherence=0.9
        )
        result = repair.repair("broken_state", known_observers=["obs1"], known_coherence=0.85)
        assert result.success

    def test_repair_failure(self):
        repair = ContinuityRepairLoop()
        result = repair.repair("unknown_state")
        assert result.success is False

    def test_auto_repair(self):
        repair = ContinuityRepairLoop()
        repair.reconstruction_engine.record_state_transition("s1", "s2", continuity_strength=0.1)
        repair.reconstruction_engine.attractor_memory.create_attractor(
            "stable", ["obs1"], coherence=0.9
        )
        results = repair.auto_repair(observer_ids=["obs1"])
        assert isinstance(results, list)

    def test_repair_success_rate(self):
        repair = ContinuityRepairLoop()
        repair.reconstruction_engine.attractor_memory.create_attractor(
            "stable", ["obs1"], coherence=0.9
        )
        repair.repair("s1", known_observers=["obs1"], known_coherence=0.85)
        repair.repair("s2")  # Will fail
        assert 0.0 <= repair.repair_success_rate <= 1.0

    def test_stats(self):
        repair = ContinuityRepairLoop()
        stats = repair.stats
        assert "total_repairs" in stats
        assert "success_rate" in stats
