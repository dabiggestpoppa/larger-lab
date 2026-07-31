"""Tests for CollarFieldEngine."""

import pytest
from oce.backend.topology.collar_field import CollarFieldEngine, CollarField


class TestCollarField:
    def test_basic_creation(self):
        c = CollarField(observer_id="obs1")
        assert c.observer_id == "obs1"
        assert c.active is True

    def test_is_strong(self):
        c = CollarField(observer_id="obs1", resonance_map={"obs2": 0.8, "obs3": 0.7})
        assert c.is_strong is True

    def test_is_weakening(self):
        c = CollarField(observer_id="obs1", resonance_map={"obs2": 0.1})
        assert c.is_weakening is True

    def test_decay(self):
        c = CollarField(observer_id="obs1", resonance_map={"obs2": 0.8}, glyph_affinity=0.8)
        c.decay(factor=0.5)
        assert c.resonance_map["obs2"] == pytest.approx(0.4, abs=0.01)
        assert c.glyph_affinity == pytest.approx(0.4, abs=0.01)


class TestCollarFieldEngine:
    def test_create_collar(self):
        engine = CollarFieldEngine()
        collar = engine.get_or_create_collar("obs1")
        assert collar.observer_id == "obs1"

    def test_connect(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", initial_resonance=0.8)
        assert "obs2" in engine.collars["obs1"].resonance_map
        assert "obs1" in engine.collars["obs2"].resonance_map

    def test_disconnect(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", initial_resonance=0.8)
        engine.disconnect("obs1", "obs2")
        assert engine.collars["obs1"].resonance_map["obs2"] == 0.0

    def test_resonance_matrix(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", initial_resonance=0.7)
        matrix = engine.get_resonance_matrix()
        assert "obs1" in matrix
        assert "obs2" in matrix["obs1"]

    def test_strongest_connections(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", initial_resonance=0.9)
        engine.connect("obs1", "obs3", initial_resonance=0.5)
        strongest = engine.get_strongest_connections("obs1")
        assert len(strongest) == 2
        assert strongest[0][0] == "obs2"  # Highest resonance first

    def test_field_coherence(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", initial_resonance=0.9)
        coherence = engine.get_field_coherence()
        assert 0.0 <= coherence <= 1.0

    def test_stats(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", initial_resonance=0.8)
        stats = engine.stats
        assert stats["total_collars"] >= 2
