"""Tests for Attractor Engine."""

import pytest
from oce.backend.cognition.attractor_engine import AttractorEngine, CognitiveAttractor


class TestCognitiveAttractor:
    def test_creation(self):
        a = CognitiveAttractor(attractor_id="a1", attractor_type="execution", stability=0.8)
        assert a.attractor_id == "a1"
        assert a.is_stable is False  # Need 3+ convergences

    def test_stable(self):
        a = CognitiveAttractor(attractor_id="a1", attractor_type="execution", stability=0.8, convergence_count=5)
        assert a.is_stable is True

    def test_converge(self):
        a = CognitiveAttractor(attractor_id="a1", attractor_type="execution", stability=0.5)
        a.converge()
        assert a.convergence_count == 1
        assert a.stability > 0.5


class TestAttractorEngine:
    def test_creation(self):
        engine = AttractorEngine()
        assert engine is not None

    def test_find_attractor(self):
        engine = AttractorEngine()
        states = [f"s{i}" for i in range(10)]
        coherence = [0.9 - i * 0.05 for i in range(10)]
        attractor = engine.find_attractor(states, coherence)
        assert attractor is not None

    def test_find_no_attractor(self):
        engine = AttractorEngine()
        states = ["s1", "s2"]
        coherence = [0.1, 0.2]  # Too low
        attractor = engine.find_attractor(states, coherence)
        assert attractor is None

    def test_get_stable(self):
        engine = AttractorEngine()
        states = [f"s{i}" for i in range(10)]
        coherence = [0.9 - i * 0.02 for i in range(10)]
        engine.find_attractor(states, coherence)
        # Reinforce to make stable
        for attr in engine.cognitive_attractors.values():
            for _ in range(3):
                attr.converge()
        stable = engine.get_stable_attractors()
        assert isinstance(stable, list)

    def test_dissolve_weak(self):
        engine = AttractorEngine()
        states = [f"s{i}" for i in range(5)]
        coherence = [0.9 - i * 0.02 for i in range(5)]
        engine.find_attractor(states, coherence)
        removed = engine.dissolve_weak()
        assert isinstance(removed, int)

    def test_stats(self):
        engine = AttractorEngine()
        engine.find_attractor(["s1", "s2"], [0.8, 0.9])
        stats = engine.stats
        assert stats["total_attractors"] >= 0
