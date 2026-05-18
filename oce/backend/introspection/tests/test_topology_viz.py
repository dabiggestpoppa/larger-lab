"""Tests for Topology Visualization."""

import pytest
from oce.backend.introspection.topology_viz import TopologyVisualization, TopologyMap
from topology.collar_field import CollarFieldEngine


class TestTopologyMap:
    def test_creation(self):
        m = TopologyMap(map_id="m1", timestamp=0)
        assert m.map_id == "m1"
        assert len(m.nodes) == 0


class TestTopologyVisualization:
    def test_generate_map(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", 0.8)
        viz = TopologyVisualization(collar_engine=engine)
        map_data = viz.generate_map()
        assert len(map_data.nodes) >= 2
        assert len(map_data.edges) >= 1

    def test_generate_map_empty(self):
        viz = TopologyVisualization()
        map_data = viz.generate_map()
        assert len(map_data.nodes) == 0

    def test_field_summary(self):
        engine = CollarFieldEngine()
        engine.connect("obs1", "obs2", 0.8)
        viz = TopologyVisualization(collar_engine=engine)
        summary = viz.get_field_summary()
        assert summary["observers"] >= 2

    def test_stats(self):
        viz = TopologyVisualization()
        stats = viz.stats
        assert "observers" in stats
