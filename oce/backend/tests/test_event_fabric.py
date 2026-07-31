"""
Tests for OCE Event Fabric.
"""

import asyncio
import pytest
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from event_fabric import EventFabric, Event, Subscriber, classify_event, EVENT_TYPES


@pytest.fixture
def fabric():
    """Create a fresh EventFabric for each test."""
    return EventFabric(max_history=100, retention_per_type=50)


@pytest.fixture
def populated_fabric():
    """Create an EventFabric pre-populated with test events."""
    fabric = EventFabric(max_history=100, retention_per_type=50)
    return fabric


class TestEventModel:
    def test_event_creation(self):
        event = Event(
            event_type="observer.state_change",
            source="planner",
            payload={"state": "active"},
        )
        assert event.event_id is not None
        assert event.event_type == "observer.state_change"
        assert event.source == "planner"
        assert event.priority == 1  # auto-classified
        assert event.payload["state"] == "active"

    def test_event_default_timestamp(self):
        event = Event(event_type="test", source="test")
        assert event.timestamp is not None

    def test_event_custom_priority(self):
        event = Event(event_type="test", source="test", priority=3)
        assert event.priority == 3


class TestEventClassification:
    def test_known_event_type(self):
        result = classify_event("observer.state_change")
        assert result["priority"] == 1

    def test_critical_event_type(self):
        result = classify_event("entropy.budget_exhausted")
        assert result["priority"] == 3

    def test_unknown_event_type(self):
        result = classify_event("custom.unknown")
        assert result["priority"] == 1  # default

    def test_all_event_types_classified(self):
        for event_type in EVENT_TYPES:
            result = classify_event(event_type)
            assert "priority" in result
            assert "description" in result


class TestIngestion:
    @pytest.mark.asyncio
    async def test_ingest_basic(self, fabric):
        event = await fabric.ingest("observer.state_change", "planner", {"state": "active"})
        assert event.event_type == "observer.state_change"
        assert event.source == "planner"
        assert fabric._total_ingested == 1

    @pytest.mark.asyncio
    async def test_ingest_auto_priority(self, fabric):
        event = await fabric.ingest("entropy.budget_exhausted", "entropy_budget")
        assert event.priority == 3  # critical

    @pytest.mark.asyncio
    async def test_ingest_custom_priority(self, fabric):
        event = await fabric.ingest("test.event", "test", priority=2)
        assert event.priority == 2

    @pytest.mark.asyncio
    async def test_ingest_multiple(self, fabric):
        for i in range(10):
            await fabric.ingest("observer.state_change", f"observer_{i % 3}")
        assert fabric._total_ingested == 10

    @pytest.mark.asyncio
    async def test_ingest_stores_in_history(self, fabric):
        await fabric.ingest("test.event", "test")
        assert len(fabric._event_history) == 1

    @pytest.mark.asyncio
    async def test_ingest_stores_by_type(self, fabric):
        await fabric.ingest("observer.state_change", "planner")
        await fabric.ingest("observer.state_change", "execution")
        await fabric.ingest("attractor.update", "attractor")
        assert len(fabric._events_by_type["observer.state_change"]) == 2
        assert len(fabric._events_by_type["attractor.update"]) == 1

    @pytest.mark.asyncio
    async def test_ingest_stores_by_source(self, fabric):
        await fabric.ingest("test.event", "planner")
        await fabric.ingest("test.event", "planner")
        await fabric.ingest("test.event", "execution")
        assert len(fabric._events_by_source["planner"]) == 2
        assert len(fabric._events_by_source["execution"]) == 1


class TestRetention:
    @pytest.mark.asyncio
    async def test_per_type_retention(self):
        fabric = EventFabric(max_history=1000, retention_per_type=5)
        for i in range(10):
            await fabric.ingest("observer.state_change", "planner", {"i": i})
        assert len(fabric._events_by_type["observer.state_change"]) == 5

    @pytest.mark.asyncio
    async def test_global_history_retention(self):
        fabric = EventFabric(max_history=10, retention_per_type=100)
        for i in range(20):
            await fabric.ingest("test.event", "test", {"i": i})
        assert len(fabric._event_history) == 10


class TestSubscription:
    @pytest.mark.asyncio
    async def test_subscribe_all_events(self, fabric):
        received = []
        def callback(event):
            received.append(event)

        fabric.subscribe(callback)
        await fabric.ingest("test.event", "test")
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_subscribe_filtered(self, fabric):
        received = []
        def callback(event):
            received.append(event)

        fabric.subscribe(callback, event_types={"observer.state_change"})
        await fabric.ingest("observer.state_change", "planner")
        await fabric.ingest("attractor.update", "attractor")
        assert len(received) == 1
        assert received[0].event_type == "observer.state_change"

    @pytest.mark.asyncio
    async def test_subscribe_source_filter(self, fabric):
        received = []
        def callback(event):
            received.append(event)

        fabric.subscribe(callback, source_filter="planner")
        await fabric.ingest("test.event", "planner")
        await fabric.ingest("test.event", "execution")
        assert len(received) == 1
        assert received[0].source == "planner"

    @pytest.mark.asyncio
    async def test_unsubscribe(self, fabric):
        received = []
        def callback(event):
            received.append(event)

        sub = fabric.subscribe(callback)
        await fabric.ingest("test.event", "test")
        assert len(received) == 1

        fabric.unsubscribe(sub)
        await fabric.ingest("test.event", "test")
        assert len(received) == 1  # no new events

    @pytest.mark.asyncio
    async def test_async_callback(self, fabric):
        received = []
        async def callback(event):
            received.append(event)

        fabric.subscribe(callback)
        await fabric.ingest("test.event", "test")
        assert len(received) == 1


class TestHistory:
    @pytest.mark.asyncio
    async def test_get_history_all(self, fabric):
        for i in range(5):
            await fabric.ingest("test.event", "test", {"i": i})
        history = fabric.get_history(limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_get_history_by_type(self, fabric):
        await fabric.ingest("observer.state_change", "planner")
        await fabric.ingest("observer.state_change", "execution")
        await fabric.ingest("attractor.update", "attractor")
        history = fabric.get_history(event_type="observer.state_change")
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_get_history_by_source(self, fabric):
        await fabric.ingest("test.event", "planner")
        await fabric.ingest("test.event", "planner")
        await fabric.ingest("test.event", "execution")
        history = fabric.get_history(source="planner")
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_get_history_by_priority(self, fabric):
        await fabric.ingest("test.low", "test", priority=0)
        await fabric.ingest("test.normal", "test", priority=1)
        await fabric.ingest("test.high", "test", priority=2)
        history = fabric.get_history(min_priority=1)
        assert len(history) == 2

    def test_get_history_empty(self, fabric):
        history = fabric.get_history()
        assert len(history) == 0


class TestStreaming:
    @pytest.mark.asyncio
    async def test_create_stream(self, fabric):
        queue = fabric.create_stream()
        assert queue in fabric._stream_queues

    @pytest.mark.asyncio
    async def test_close_stream(self, fabric):
        queue = fabric.create_stream()
        fabric.close_stream(queue)
        assert queue not in fabric._stream_queues

    @pytest.mark.asyncio
    async def test_stream_receives_events(self, fabric):
        queue = fabric.create_stream()
        await fabric.ingest("test.event", "test", {"data": "hello"})

        # Check the queue has the event
        assert not queue.empty()
        event = queue.get_nowait()
        assert event.event_type == "test.event"
        assert event.payload["data"] == "hello"

        fabric.close_stream(queue)


class TestStatistics:
    @pytest.mark.asyncio
    async def test_get_stats(self, fabric):
        await fabric.ingest("observer.state_change", "planner")
        await fabric.ingest("attractor.update", "attractor")
        stats = fabric.get_stats()
        assert stats["total_ingested"] == 2
        assert "observer.state_change" in stats["events_by_type"]
        assert "attractor.update" in stats["events_by_type"]

    def test_get_event_types(self, fabric):
        types = fabric.get_event_types()
        assert len(types) == len(EVENT_TYPES)
        assert all("type" in t and "priority" in t and "description" in t for t in types)


class TestSingleton:
    def test_get_fabric_returns_same_instance(self):
        from event_fabric import get_fabric
        f1 = get_fabric()
        f2 = get_fabric()
        assert f1 is f2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
