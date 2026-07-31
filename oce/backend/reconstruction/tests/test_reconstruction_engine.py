"""Tests for ReconstructionEngine."""

import pytest
from oce.backend.reconstruction.reconstruction_engine import ReconstructionEngine
from oce.backend.reconstruction.attractor_memory import Attractor


class TestReconstructionEngine:
    def test_reconstruct_from_attractor(self):
        engine = ReconstructionEngine()
        a = engine.attractor_memory.create_attractor("stable_state", ["obs1", "obs2"], coherence=0.9)
        # Access multiple times to build stability
        for _ in range(5):
            engine.attractor_memory.recall(a.attractor_id)
        result = engine.reconstruct("target", known_observers=["obs1"], known_coherence=0.85)
        assert result.reconstructed
        assert result.method == "attractor"
        assert result.confidence > 0.5

    def test_reconstruct_from_lineage(self):
        engine = ReconstructionEngine()
        engine.record_state_transition("s1", "s2", influence_weight=0.9, continuity_strength=0.9)
        engine.record_state_transition("s2", "s3", influence_weight=0.9, continuity_strength=0.9)
        result = engine.reconstruct("s3")
        assert result.reconstructed
        assert result.method == "lineage"

    def test_reconstruct_failure(self):
        engine = ReconstructionEngine()
        result = engine.reconstruct("unknown_state")
        assert result.reconstructed is False

    def test_record_state_transition(self):
        engine = ReconstructionEngine()
        edge = engine.record_state_transition("s1", "s2", influence_weight=0.8, continuity_strength=0.9)
        assert edge.source_state == "s1"
        assert edge.target_state == "s2"

    def test_success_rate(self):
        engine = ReconstructionEngine()
        engine.attractor_memory.create_attractor("s1", ["obs1"], coherence=0.9)
        engine.reconstruct("t1", known_observers=["obs1"], known_coherence=0.85)
        engine.reconstruct("t2")
        assert 0.0 <= engine.success_rate <= 1.0

    def test_stats(self):
        engine = ReconstructionEngine()
        stats = engine.stats
        assert "reconstructions" in stats
        assert "success_rate" in stats

    def test_observer_death_recovery(self):
        engine = ReconstructionEngine()
        a = engine.attractor_memory.create_attractor("stable", ["obs1", "obs2"], coherence=0.9)
        for _ in range(5):
            engine.attractor_memory.recall(a.attractor_id)
        result = engine.reconstruct("recovered", known_coherence=0.85)
        assert result.reconstructed

    def test_sparse_reconstruction(self):
        engine = ReconstructionEngine()
        engine.attractor_memory.create_attractor("anchor", ["obs1"], coherence=0.7)
        result = engine.reconstruct("sparse_target", known_coherence=0.6)
        assert result.method in ["attractor", "inference", "failed"]
