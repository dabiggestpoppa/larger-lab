"""Tests for OverlapManifold."""

import pytest
from oce.backend.reconstruction.overlap_manifold import OverlapManifold, OverlapZone
from oce.backend.reconstruction.attractor_memory import AttractorMemory, Attractor


class TestOverlapZone:
    def test_basic_creation(self):
        z = OverlapZone(zone_id="z1", observer_ids=["obs1", "obs2"])
        assert z.observer_count == 2

    def test_is_strong(self):
        z = OverlapZone(zone_id="z1", observer_ids=["obs1", "obs2"], overlap_strength=0.8)
        assert z.is_strong is True

    def test_add_observer(self):
        z = OverlapZone(zone_id="z1", observer_ids=["obs1"])
        z.add_observer("obs2")
        assert z.observer_count == 2

    def test_remove_observer(self):
        z = OverlapZone(zone_id="z1", observer_ids=["obs1", "obs2"])
        z.remove_observer("obs1")
        assert z.observer_count == 1


class TestOverlapManifold:
    def test_create_zone(self):
        manifold = OverlapManifold()
        zone = manifold.create_zone(["obs1", "obs2"])
        assert zone.zone_id in manifold.zones

    def test_find_zone(self):
        manifold = OverlapManifold()
        manifold.create_zone(["obs1", "obs2"])
        found = manifold.find_zone(["obs1", "obs2"])
        assert found is not None

    def test_find_zone_not_found(self):
        manifold = OverlapManifold()
        found = manifold.find_zone(["obs1", "obs2"])
        assert found is None

    def test_get_zones_for_observer(self):
        manifold = OverlapManifold()
        manifold.create_zone(["obs1", "obs2"])
        zones = manifold.get_zones_for_observer("obs1")
        assert len(zones) == 1

    def test_get_shared_observers(self):
        manifold = OverlapManifold()
        manifold.create_zone(["obs1", "obs2", "obs3"])
        shared = manifold.get_shared_observers("obs1", "obs2")
        assert "obs3" in shared

    def test_calculate_overlap_strength(self):
        manifold = OverlapManifold()
        manifold.create_zone(["obs1", "obs2"])
        strength = manifold.calculate_overlap_strength("obs1", "obs2")
        assert strength > 0.0

    def test_calculate_overlap_strength_no_overlap(self):
        manifold = OverlapManifold()
        manifold.create_zone(["obs1", "obs2"])
        manifold.create_zone(["obs3", "obs4"])
        strength = manifold.calculate_overlap_strength("obs1", "obs3")
        assert strength == 0.0

    def test_synthesize_shared_state(self):
        manifold = OverlapManifold()
        mem = AttractorMemory()
        attractor = mem.create_attractor("shared", ["obs1", "obs2"], coherence=0.9)
        for _ in range(5):
            mem.recall(attractor.attractor_id)
        manifold.create_zone(["obs1", "obs2"], shared_attractors=[attractor.attractor_id])
        result = manifold.synthesize_shared_state(["obs1", "obs2"], mem)
        assert result["synthesized"]

    def test_synthesize_no_overlap(self):
        manifold = OverlapManifold()
        mem = AttractorMemory()
        result = manifold.synthesize_shared_state(["obs1", "obs2"], mem)
        assert result["synthesized"] is False

    def test_stats(self):
        manifold = OverlapManifold()
        manifold.create_zone(["obs1", "obs2"])
        stats = manifold.stats
        assert stats["total_zones"] == 1
