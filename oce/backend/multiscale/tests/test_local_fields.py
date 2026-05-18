"""Tests for Local Observer Fields."""

import pytest
from oce.backend.multiscale.local_fields import LocalObserverField, LocalFieldRegistry


class TestLocalObserverField:
    def test_creation(self):
        f = LocalObserverField(observer_id="obs1")
        assert f.observer_id == "obs1"
        assert f.coherence_level == 1.0

    def test_update_state(self):
        f = LocalObserverField(observer_id="obs1")
        f.update_state("key1", "value1")
        assert f.get_state("key1") == "value1"

    def test_needs_sync(self):
        f = LocalObserverField(observer_id="obs1", sync_bound=2)
        assert not f.needs_sync()
        f.update_state("k", "v")
        f.update_state("k", "v")
        assert f.needs_sync()

    def test_calculate_coherence(self):
        f = LocalObserverField(observer_id="obs1")
        coherence = f.calculate_coherence()
        assert 0.0 <= coherence <= 1.0


class TestLocalFieldRegistry:
    def test_register_and_get(self):
        registry = LocalFieldRegistry()
        f = registry.register("obs1")
        assert f.observer_id == "obs1"
        assert registry.get("obs1") == f

    def test_get_needing_sync(self):
        registry = LocalFieldRegistry()
        registry.register("obs1", sync_bound=2)
        registry.register("obs2", sync_bound=10)
        registry.get("obs1").update_state("k", "v")
        registry.get("obs1").update_state("k", "v")
        needing = registry.get_needing_sync()
        assert len(needing) == 1
        assert needing[0].observer_id == "obs1"

    def test_all_fields(self):
        registry = LocalFieldRegistry()
        registry.register("obs1")
        registry.register("obs2")
        assert len(registry.all_fields()) == 2

    def test_remove(self):
        registry = LocalFieldRegistry()
        registry.register("obs1")
        assert registry.remove("obs1")
        assert registry.get("obs1") is None
