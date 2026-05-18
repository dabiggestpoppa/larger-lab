"""Tests for CausalGeometryEngine."""

import pytest
from oce.backend.reconstruction.causal_geometry import CausalGeometryEngine, CausalEdge, ContinuityLineage


class TestCausalEdge:
    def test_basic_creation(self):
        e = CausalEdge(source_state="s1", target_state="s2")
        assert e.source_state == "s1"
        assert e.target_state == "s2"
        assert e.influence_weight == 0.5

    def test_is_strong(self):
        e = CausalEdge(source_state="s1", target_state="s2", influence_weight=0.9, continuity_strength=0.9)
        assert e.is_strong is True

    def test_is_entropic(self):
        e = CausalEdge(source_state="s1", target_state="s2", entropy_delta=0.8)
        assert e.is_entropic is True

    def test_to_dict(self):
        e = CausalEdge(source_state="s1", target_state="s2")
        d = e.to_dict()
        assert "edge_id" in d
        assert "is_strong" in d


class TestCausalGeometryEngine:
    def test_add_edge(self):
        engine = CausalGeometryEngine()
        edge = engine.create_edge("s1", "s2", influence_weight=0.8, continuity_strength=0.9)
        assert edge.edge_id in engine.edges

    def test_get_lineage(self):
        engine = CausalGeometryEngine()
        engine.create_edge("s1", "s2", continuity_strength=0.9)
        lineage = engine.get_lineage("s2")
        assert lineage is not None
        assert lineage.state_id == "s2"

    def test_lineage_intact(self):
        engine = CausalGeometryEngine()
        engine.create_edge("s1", "s2", continuity_strength=0.9)
        engine.create_edge("s2", "s3", continuity_strength=0.9)
        lineage = engine.get_lineage("s3")
        assert lineage.is_intact is True

    def test_lineage_broken(self):
        engine = CausalGeometryEngine()
        engine.create_edge("s1", "s2", continuity_strength=0.1)
        engine.create_edge("s2", "s3", continuity_strength=0.1)
        lineage = engine.get_lineage("s3")
        assert lineage.is_intact is False

    def test_get_ancestor_chain(self):
        engine = CausalGeometryEngine()
        engine.create_edge("s1", "s2")
        engine.create_edge("s2", "s3")
        chain = engine.get_ancestor_chain("s3")
        assert "s1" in chain
        assert "s2" in chain

    def test_get_influence_score(self):
        engine = CausalGeometryEngine()
        engine.create_edge("s1", "s2", influence_weight=0.8)
        engine.create_edge("s1", "s3", influence_weight=0.6)
        score = engine.get_influence_score("s1")
        assert score > 0.5

    def test_strongest_path(self):
        engine = CausalGeometryEngine()
        engine.create_edge("s1", "s2", influence_weight=0.9)
        engine.create_edge("s2", "s3", influence_weight=0.9)
        path = engine.get_strongest_path("s1", "s3")
        assert len(path) == 2

    def test_no_path(self):
        engine = CausalGeometryEngine()
        engine.create_edge("s1", "s2")
        engine.create_edge("s3", "s4")
        path = engine.get_strongest_path("s1", "s4")
        assert len(path) == 0

    def test_stats(self):
        engine = CausalGeometryEngine()
        engine.create_edge("s1", "s2")
        stats = engine.stats
        assert stats["total_edges"] == 1
        assert stats["total_lineages"] == 1
