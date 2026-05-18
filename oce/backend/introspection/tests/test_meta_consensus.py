"""Tests for Meta-Consensus."""

import pytest
from oce.backend.introspection.meta_consensus import MetaConsensus, ConsensusProcess


class TestMetaConsensus:
    def test_record_consensus(self):
        mc = MetaConsensus()
        process = mc.record_consensus(
            "test_topic", ["obs1", "obs2", "obs3"],
            "agreement", 0.8, 120.0,
        )
        assert process.agreement_level == 0.8

    def test_evaluate_process(self):
        mc = MetaConsensus()
        mc.record_consensus("topic", ["a", "b", "c"], "outcome", 0.9, 120.0)
        evaluation = mc.evaluate_process(mc._processes[0].process_id)
        assert evaluation["is_healthy"] is True

    def test_meta_analysis(self):
        mc = MetaConsensus()
        for _ in range(3):
            mc.record_consensus("topic", ["a", "b"], "outcome", 0.7, 60.0)
        analysis = mc.get_meta_analysis()
        assert analysis["total_processes"] == 3

    def test_stats(self):
        mc = MetaConsensus()
        mc.record_consensus("topic", ["a", "b"], "outcome", 0.8, 60.0)
        stats = mc.stats
        assert stats["total_processes"] == 1
