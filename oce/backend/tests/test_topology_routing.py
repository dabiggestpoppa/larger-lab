"""
Tests for OCE-2.3: Topological Router
"""
import pytest
from event_fabric import TopologicalRouter, EventPersistence, Event, get_router, get_persistence


class TestTopologicalRouter:
    def setup_method(self):
        self.router = TopologicalRouter()

    def test_register_observer(self):
        self.router.register_observer("obs-1")
        assert "obs-1" in self.router._observers

    def test_unregister_observer(self):
        self.router.register_observer("obs-1")
        self.router.register_observer("obs-2")
        self.router.update_edge("obs-1", "obs-2", 0.8)
        self.router.unregister_observer("obs-1")
        assert "obs-1" not in self.router._observers
        assert ("obs-1", "obs-2") not in self.router._edges

    def test_update_edge(self):
        self.router.update_edge("obs-1", "obs-2", 0.8)
        assert self.router._edges[("obs-1", "obs-2")] == 0.8

    def test_update_edge_clamps_weight(self):
        self.router.update_edge("obs-1", "obs-2", 1.5)
        assert self.router._edges[("obs-1", "obs-2")] == 1.0
        self.router.update_edge("obs-1", "obs-2", -0.5)
        assert self.router._edges[("obs-1", "obs-2")] == 0.0

    def test_get_path_direct(self):
        self.router.update_edge("obs-1", "obs-2", 0.8)
        path = self.router.get_path("obs-1", "obs-2")
        assert path == ["obs-1", "obs-2"]

    def test_get_path_multi_hop(self):
        # obs-1 --0.8-- obs-2 --0.6-- obs-3
        self.router.update_edge("obs-1", "obs-2", 0.8)
        self.router.update_edge("obs-2", "obs-3", 0.6)
        path = self.router.get_path("obs-1", "obs-3")
        assert path == ["obs-1", "obs-2", "obs-3"]

    def test_get_path_no_path(self):
        self.router.register_observer("obs-1")
        self.router.register_observer("obs-2")
        # No edge between them
        path = self.router.get_path("obs-1", "obs-2")
        assert path == []

    def test_get_path_nonexistent_observer(self):
        self.router.register_observer("obs-1")
        path = self.router.get_path("obs-1", "nonexistent")
        assert path == []

    def test_get_broadcast_targets(self):
        # obs-1 -- obs-2 -- obs-3 -- obs-4
        self.router.update_edge("obs-1", "obs-2", 0.8)
        self.router.update_edge("obs-2", "obs-3", 0.6)
        self.router.update_edge("obs-3", "obs-4", 0.7)

        targets = self.router.get_broadcast_targets("obs-1", max_hops=1)
        assert "obs-2" in targets
        assert "obs-3" not in targets

        targets = self.router.get_broadcast_targets("obs-1", max_hops=2)
        assert "obs-2" in targets
        assert "obs-3" in targets
        assert "obs-4" not in targets

        targets = self.router.get_broadcast_targets("obs-1", max_hops=3)
        assert "obs-4" in targets

    def test_get_broadcast_targets_nonexistent(self):
        targets = self.router.get_broadcast_targets("nonexistent")
        assert targets == []

    def test_topology_stats(self):
        self.router.update_edge("obs-1", "obs-2", 0.8)
        self.router.update_edge("obs-2", "obs-3", 0.6)
        stats = self.router.get_topology_stats()
        assert stats["observers"] == 3
        assert stats["edges"] == 2
        assert stats["avg_coupling"] == 0.7

    def test_singleton(self):
        r1 = get_router()
        r2 = get_router()
        assert r1 is r2


class TestEventPersistence:
    def setup_method(self):
        self.persistence = EventPersistence(db_path="data/test_events.db")

    def teardown_method(self):
        import os
        if os.path.exists("data/test_events.db"):
            os.remove("data/test_events.db")

    def test_store_and_query(self):
        event = Event(event_type="test.event", source="test", priority=1, payload={"key": "value"})
        # Need to set event_id explicitly for in-memory test
        event.event_id = "test-001"
        self.persistence.store_event(event)

        results = self.persistence.query_events(limit=10)
        assert len(results) == 1
        assert results[0]["event_id"] == "test-001"
        assert results[0]["event_type"] == "test.event"

    def test_query_by_type(self):
        for i in range(5):
            e = Event(event_type="type-a", source="test", priority=1)
            e.event_id = f"a-{i}"
            self.persistence.store_event(e)
        for i in range(3):
            e = Event(event_type="type-b", source="test", priority=1)
            e.event_id = f"b-{i}"
            self.persistence.store_event(e)

        results = self.persistence.query_events(event_type="type-a")
        assert len(results) == 5

    def test_query_by_source(self):
        e1 = Event(event_type="test", source="src-a", priority=1)
        e1.event_id = "s1"
        e2 = Event(event_type="test", source="src-b", priority=1)
        e2.event_id = "s2"
        self.persistence.store_event(e1)
        self.persistence.store_event(e2)

        results = self.persistence.query_events(source="src-a")
        assert len(results) == 1
        assert results[0]["source"] == "src-a"

    def test_compress_old_events(self):
        # Store 150 events of same type
        for i in range(150):
            e = Event(event_type="compressible", source="test", priority=1)
            e.event_id = f"comp-{i}"
            self.persistence.store_event(e)

        # Compress to keep only last 100
        deleted = self.persistence.compress_old_events("compressible", keep_last=100)
        assert deleted == 50

        remaining = self.persistence.query_events(event_type="compressible", limit=200)
        assert len(remaining) == 100

    def test_compress_no_op_when_under_limit(self):
        for i in range(10):
            e = Event(event_type="sparse", source="test", priority=1)
            e.event_id = f"sparse-{i}"
            self.persistence.store_event(e)

        deleted = self.persistence.compress_old_events("sparse", keep_last=100)
        assert deleted is None  # No compression needed

    def test_get_stats(self):
        for i in range(3):
            e = Event(event_type="type-a", source="test", priority=1)
            e.event_id = f"stat-a-{i}"
            self.persistence.store_event(e)
        for i in range(2):
            e = Event(event_type="type-b", source="test", priority=1)
            e.event_id = f"stat-b-{i}"
            self.persistence.store_event(e)

        stats = self.persistence.get_stats()
        assert stats["total_events"] == 5
        assert stats["events_by_type"]["type-a"] == 3
        assert stats["events_by_type"]["type-b"] == 2

    def test_singleton(self):
        p1 = get_persistence()
        p2 = get_persistence()
        assert p1 is p2
