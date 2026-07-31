"""Tests for AttractorMemory."""

import pytest
from oce.backend.reconstruction.attractor_memory import AttractorMemory, Attractor


class TestAttractor:
    def test_basic_creation(self):
        a = Attractor(state_id="test_state", coherence=0.8)
        assert a.state_id == "test_state"
        assert a.coherence == 0.8

    def test_access(self):
        a = Attractor(state_id="test")
        a.access()
        assert a.access_count == 1

    def test_stability_increases_with_access(self):
        a = Attractor(state_id="test", coherence=0.8)
        initial = a.stability
        for _ in range(10):
            a.access()
        assert a.stability >= initial


class TestAttractorMemory:
    def test_store(self):
        mem = AttractorMemory()
        a = Attractor(state_id="s1", coherence=0.8)
        aid = mem.store(a)
        assert aid in mem.attractors

    def test_recall(self):
        mem = AttractorMemory()
        a = Attractor(state_id="s1", coherence=0.8)
        aid = mem.store(a)
        recalled = mem.recall(aid)
        assert recalled is not None
        assert recalled.state_id == "s1"

    def test_find_nearest(self):
        mem = AttractorMemory()
        mem.create_attractor("s1", ["obs1"], coherence=0.8)
        mem.create_attractor("s2", ["obs2"], coherence=0.3)
        nearest = mem.find_nearest(coherence=0.75, observers=["obs1"])
        assert nearest is not None
        assert nearest.state_id == "s1"

    def test_find_by_observer(self):
        mem = AttractorMemory()
        mem.create_attractor("s1", ["obs1", "obs2"], coherence=0.8)
        results = mem.find_by_observer("obs1")
        assert len(results) == 1

    def test_merge_similar(self):
        mem = AttractorMemory()
        mem.create_attractor("s1", ["obs1"], coherence=0.7)
        mem.create_attractor("s1", ["obs1"], coherence=0.9)  # Same state_id
        # Should merge, not create duplicate
        assert len(mem.attractors) == 1
        # Coherence should be max of both
        values = list(mem.attractors.values())
        assert values[0].coherence == 0.9

    def test_stable_attractors(self):
        mem = AttractorMemory()
        a = mem.create_attractor("s1", ["obs1"], coherence=0.9)
        for _ in range(20):
            mem.recall(a.attractor_id)
        stable = mem.get_stable_attractors()
        assert len(stable) >= 1

    def test_stats(self):
        mem = AttractorMemory()
        mem.create_attractor("s1", ["obs1"], coherence=0.8)
        stats = mem.stats
        assert stats["total_attractors"] == 1
