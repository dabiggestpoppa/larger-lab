"""
Tests for OCE Observer Runtime.
"""

import asyncio
import pytest
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from observer_runtime import (
    ObserverRuntime, Observer, ObserverConfig, ObserverState, ObserverHealth, get_runtime
)
from event_fabric import EventFabric, get_fabric


@pytest.fixture
def fabric():
    """Create a fresh EventFabric for each test."""
    return EventFabric(max_history=100, retention_per_type=50)


@pytest.fixture
def runtime(fabric):
    """Create a fresh ObserverRuntime for each test."""
    return ObserverRuntime(fabric=fabric)


class TestObserverConfig:
    def test_create_config(self):
        config = ObserverConfig(
            observer_type="planner",
            name="Test Planner",
            event_subscriptions=["observer.state_change"],
        )
        assert config.observer_type == "planner"
        assert config.name == "Test Planner"
        assert "observer.state_change" in config.event_subscriptions


class TestObserverLifecycle:
    @pytest.mark.asyncio
    async def test_create_observer(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        observer = await runtime.create_observer(config)
        assert observer.observer_id is not None
        assert observer.state == ObserverState.CREATED
        assert observer.config.name == "Test"

    @pytest.mark.asyncio
    async def test_activate_observer(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        observer = await runtime.create_observer(config)
        activated = await runtime.activate_observer(observer.observer_id)
        assert activated is not None
        assert activated.state == ObserverState.ACTIVE
        assert activated.activated_at is not None

    @pytest.mark.asyncio
    async def test_suspend_observer(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        observer = await runtime.create_observer(config)
        await runtime.activate_observer(observer.observer_id)
        suspended = await runtime.suspend_observer(observer.observer_id)
        assert suspended is not None
        assert suspended.state == ObserverState.SUSPENDED

    @pytest.mark.asyncio
    async def test_destroy_observer(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        observer = await runtime.create_observer(config)
        result = await runtime.destroy_observer(observer.observer_id)
        assert result is True
        assert runtime.get_observer(observer.observer_id) is None

    @pytest.mark.asyncio
    async def test_destroy_nonexistent(self, runtime):
        result = await runtime.destroy_observer("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_activate_destroyed_observer(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        observer = await runtime.create_observer(config)
        await runtime.destroy_observer(observer.observer_id)
        result = await runtime.activate_observer(observer.observer_id)
        assert result is None


class TestObserverQuery:
    @pytest.mark.asyncio
    async def test_get_observer(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        observer = await runtime.create_observer(config)
        fetched = runtime.get_observer(observer.observer_id)
        assert fetched is not None
        assert fetched.observer_id == observer.observer_id

    @pytest.mark.asyncio
    async def test_list_all_observers(self, runtime):
        for i in range(3):
            config = ObserverConfig(observer_type="planner", name=f"Test-{i}")
            await runtime.create_observer(config)
        observers = runtime.list_observers()
        assert len(observers) == 3

    @pytest.mark.asyncio
    async def test_list_by_state(self, runtime):
        config1 = ObserverConfig(observer_type="planner", name="Active")
        obs1 = await runtime.create_observer(config1)
        await runtime.activate_observer(obs1.observer_id)

        config2 = ObserverConfig(observer_type="planner", name="Created")
        await runtime.create_observer(config2)

        active = runtime.list_observers(state=ObserverState.ACTIVE)
        assert len(active) == 1
        assert active[0].observer_id == obs1.observer_id

    @pytest.mark.asyncio
    async def test_list_by_type(self, runtime):
        await runtime.create_observer(ObserverConfig(observer_type="planner", name="P"))
        await runtime.create_observer(ObserverConfig(observer_type="execution", name="E"))
        planners = runtime.list_observers(observer_type="planner")
        assert len(planners) == 1


class TestObserverHealth:
    @pytest.mark.asyncio
    async def test_get_health(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        observer = await runtime.create_observer(config)
        health = runtime.get_observer_health(observer.observer_id)
        assert health is not None
        assert health.observer_id == observer.observer_id
        assert health.state == ObserverState.CREATED
        assert health.health_score == 1.0

    @pytest.mark.asyncio
    async def test_health_after_events(self, runtime):
        config = ObserverConfig(
            observer_type="planner",
            name="Test",
            event_subscriptions=["test.event"],
        )
        observer = await runtime.create_observer(config)
        await runtime.activate_observer(observer.observer_id)

        class FakeEvent:
            event_id = "test"
            event_type = "test.event"
            timestamp = datetime.now(timezone.utc)
            source = "test"
            priority = 0
            payload = {}

        await runtime._handle_event(observer.observer_id, FakeEvent())

        health = runtime.get_observer_health(observer.observer_id)
        assert health.event_count == 1

    def test_get_health_nonexistent(self, runtime):
        health = runtime.get_observer_health("nonexistent")
        assert health is None


class TestObserverPersistence:
    @pytest.mark.asyncio
    async def test_snapshot(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        observer = await runtime.create_observer(config)
        snapshot = await runtime.snapshot_observer(observer.observer_id)
        assert snapshot is not None
        assert snapshot["observer_id"] == observer.observer_id
        assert snapshot["state"] == "created"

    @pytest.mark.asyncio
    async def test_restore(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        observer = await runtime.create_observer(config)
        snapshot = await runtime.snapshot_observer(observer.observer_id)

        restored = await runtime.restore_observer(snapshot)
        assert restored is not None
        assert restored.observer_id == observer.observer_id
        assert restored.config.name == "Test"

    @pytest.mark.asyncio
    async def test_snapshot_nonexistent(self, runtime):
        snapshot = await runtime.snapshot_observer("nonexistent")
        assert snapshot is None


class TestObserverStats:
    @pytest.mark.asyncio
    async def test_get_stats(self, runtime):
        config = ObserverConfig(observer_type="planner", name="Test")
        await runtime.create_observer(config)
        stats = runtime.get_stats()
        assert stats["total_observers"] == 1
        assert "created" in stats["by_state"]

    def test_get_stats_empty(self, runtime):
        stats = runtime.get_stats()
        assert stats["total_observers"] == 0
        assert stats["avg_health"] == 0.0


class TestSingleton:
    def test_get_runtime_returns_same_instance(self):
        r1 = get_runtime()
        r2 = get_runtime()
        assert r1 is r2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
