"""Tests for Topology Observer."""

import pytest
from oce.backend.introspection.topology_observer import TopologyObserver, TopologySnapshot
from topology.collar_field import CollarFieldEngine


class TestTopologySnapshot:
    def test_creation(self):
        s = TopologySnapshot(snapshot_id="s1", timestamp=0, observer_count=5)
        assert s.observer_count == 5
        assert s.health_score == 1.0


class TestTopologyObserver:
    def test_observe(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", 0.8)
        observer = TopologyObserver(collar_engine=engine)
        snap = observer.observe()
        assert snap.observer_count >= 2
        assert snap.connection_count >= 1

    def test_observe_empty(self):
        observer = TopologyObserver()
        snap = observer.observe()
        assert snap.observer_count == 0

    def test_topology_report(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", 0.8)
        observer = TopologyObserver(collar_engine=engine)
        observer.observe()
        report = observer.get_topology_report()
        assert "current" in report

    def test_stats(self):
        observer = TopologyObserver()
        stats = observer.stats
        assert "status" in stats  # No data yet
