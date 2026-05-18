"""Tests for Continuity Collar."""

import pytest
from oce.backend.temporal.continuity_collar import ContinuityCollarManager, ContinuityCollar


class TestContinuityCollar:
    def test_creation(self):
        c = ContinuityCollar(collar_id="c1", observer_ids=["obs1", "obs2"])
        assert len(c.observer_ids) == 2

    def test_is_strong(self):
        c = ContinuityCollar(collar_id="c1", observer_ids=["obs1", "obs2"], continuity_strength=0.8)
        assert c.is_strong is True

    def test_sync(self):
        c = ContinuityCollar(collar_id="c1", observer_ids=["obs1"])
        c.sync()
        assert c.sync_count == 1


class TestContinuityCollarManager:
    def test_create_collar(self):
        mgr = ContinuityCollarManager()
        c = mgr.create_collar(["obs1", "obs2"], mission="V3 build")
        assert c.collar_id in mgr.collars

    def test_find_collar(self):
        mgr = ContinuityCollarManager()
        mgr.create_collar(["obs1", "obs2"])
        found = mgr.find_collar_for_observer("obs1")
        assert len(found) >= 1

    def test_sync(self):
        mgr = ContinuityCollarManager()
        c = mgr.create_collar(["obs1", "obs2"])
        mgr.sync_collar(c.collar_id)
        assert c.sync_count == 1

    def test_stats(self):
        mgr = ContinuityCollarManager()
        mgr.create_collar(["obs1", "obs2"])
        stats = mgr.stats
        assert stats["total_collars"] == 1
