"""
Phase 10: Recursive Field Computation Tests

Tests for RCG, PRS, RPE, DCT, and ACE modules.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from phase10.rcg import RecursiveComputeGraph, ComputeNode, ComputeState
from phase10.prs import PositionalReferenceSystem, ReferenceFrame, Position
from phase10.rpe import ResonancePropagationEngine, PropagationMode
from phase10.dct import DynamicConstraintTopology, ConstraintEdge
from phase10.ace import AttractorComputeEngine, AttractorType


class TestRecursiveComputeGraph:
    """Tests for RCG module."""
    
    def test_create_graph(self):
        """Test graph creation."""
        graph = RecursiveComputeGraph("test_graph")
        assert graph.name == "test_graph"
        assert len(graph.nodes) == 0
    
    def test_add_node(self):
        """Test adding nodes to graph."""
        graph = RecursiveComputeGraph()
        node = ComputeNode(node_id="n1", initial_state={"value": 1.0})
        graph.add_node(node)
        assert "n1" in graph.nodes
    
    def test_connect_nodes(self):
        """Test connecting nodes."""
        graph = RecursiveComputeGraph()
        n1 = ComputeNode(node_id="n1", initial_state={"value": 1.0})
        n2 = ComputeNode(node_id="n2", initial_state={"value": 2.0})
        graph.add_node(n1)
        graph.add_node(n2)
        graph.connect("n1", "n2")
        assert "n2" in graph.edges["n1"]
        assert "n1" in graph.edges["n2"]
    
    def test_compute_coherence(self):
        """Test coherence computation."""
        graph = RecursiveComputeGraph()
        n1 = ComputeNode(node_id="n1", initial_state={"value": 1.0})
        n2 = ComputeNode(node_id="n2", initial_state={"value": 1.0})
        graph.add_node(n1)
        graph.add_node(n2)
        graph.connect("n1", "n2")
        coherence = graph.compute_coherence("n1")
        assert 0.0 <= coherence <= 1.0
    
    def test_stabilize_node(self):
        """Test node stabilization."""
        graph = RecursiveComputeGraph()
        n1 = ComputeNode(node_id="n1", initial_state={"value": 1.0})
        n2 = ComputeNode(node_id="n2", initial_state={"value": 1.0})
        graph.add_node(n1)
        graph.add_node(n2)
        graph.connect("n1", "n2")
        result = graph.stabilize_node("n1")
        assert result.node_id == "n1"
        assert result.iterations >= 0
    
    def test_compute_cycle(self):
        """Test full compute cycle."""
        graph = RecursiveComputeGraph()
        for i in range(3):
            node = ComputeNode(node_id=f"n{i}", initial_state={"value": float(i)})
            graph.add_node(node)
        graph.connect("n0", "n1")
        graph.connect("n1", "n2")
        results = graph.compute()
        assert len(results) == 3


class TestPositionalReferenceSystem:
    """Tests for PRS module."""
    
    def test_create_system(self):
        """Test PRS creation."""
        prs = PositionalReferenceSystem("test_prs")
        assert prs.name == "test_prs"
    
    def test_create_frame(self):
        """Test frame creation."""
        prs = PositionalReferenceSystem()
        frame = prs.create_frame("frame1")
        assert frame.frame_id == "frame1"
    
    def test_add_position(self):
        """Test adding positions."""
        prs = PositionalReferenceSystem()
        frame = prs.create_frame("f1")
        pos = Position(position_id="p1", coordinates={"x": 0.0, "y": 0.0})
        frame.add_position(pos)
        assert "p1" in frame.positions
    
    def test_transition(self):
        """Test state transition."""
        prs = PositionalReferenceSystem()
        frame = prs.create_frame("f1")
        p1 = Position(position_id="p1", coordinates={"x": 0.0, "y": 0.0})
        p2 = Position(position_id="p2", coordinates={"x": 1.0, "y": 1.0})
        frame.add_position(p1)
        frame.add_position(p2)
        result = frame.transition("p1", "p2")
        assert result["valid"] is True
        assert result["delta"]["x"] == 1.0
    
    def test_compute_transition_path(self):
        """Test transition path computation."""
        prs = PositionalReferenceSystem()
        frame = prs.create_frame("f1")
        for i in range(3):
            pos = Position(position_id=f"p{i}", coordinates={"x": float(i)})
            frame.add_position(pos)
        path = prs.compute_transition_path("p0", "p2")
        assert len(path) >= 1


class TestResonancePropagationEngine:
    """Tests for RPE module."""
    
    def test_create_engine(self):
        """Test RPE creation."""
        rpe = ResonancePropagationEngine("test_rpe")
        assert rpe.name == "test_rpe"
    
    def test_register_node(self):
        """Test node registration."""
        rpe = ResonancePropagationEngine()
        rpe.register_node("n1", {"value": 1.0})
        assert "n1" in rpe.nodes
    
    def test_connect_and_propagate(self):
        """Test propagation."""
        rpe = ResonancePropagationEngine()
        rpe.register_node("n1", {"value": 1.0})
        rpe.register_node("n2", {"value": 1.0})
        rpe.connect("n1", "n2")
        rpe.set_constraint("n1", "value", 1.0)
        result = rpe.propagate("n1")
        assert result.source_id == "n1"
    
    def test_get_field_coherence(self):
        """Test field coherence."""
        rpe = ResonancePropagationEngine()
        rpe.register_node("n1", {"value": 1.0})
        rpe.set_constraint("n1", "value", 1.0)
        coherence = rpe.compute_coherence("n1")
        assert coherence == 1.0


class TestDynamicConstraintTopology:
    """Tests for DCT module."""
    
    def test_create_topology(self):
        """Test DCT creation."""
        dct = DynamicConstraintTopology("test_dct")
        assert dct.name == "test_dct"
    
    def test_add_node_and_edge(self):
        """Test adding nodes and edges."""
        dct = DynamicConstraintTopology()
        dct.add_node("n1")
        dct.add_node("n2")
        dct.add_edge("n1", "n2")
        assert "n1" in dct.nodes
        assert ("n1", "n2") in dct.edges
    
    def test_rewire(self):
        """Test topology rewiring."""
        dct = DynamicConstraintTopology()
        dct.add_node("n1")
        dct.add_node("n2")
        dct.add_node("n3")
        dct.add_edge("n1", "n2")
        dct.set_coherence("n1", 0.9)
        dct.set_coherence("n2", 0.9)
        dct.set_coherence("n3", 0.9)
        changes = dct.rewire()
        assert len(changes) >= 0
    
    def test_get_metrics(self):
        """Test topology metrics."""
        dct = DynamicConstraintTopology()
        dct.add_node("n1")
        dct.add_node("n2")
        dct.add_edge("n1", "n2")
        metrics = dct.get_topology_metrics()
        assert metrics["num_nodes"] == 2
        assert metrics["num_edges"] == 1


class TestAttractorComputeEngine:
    """Tests for ACE module."""
    
    def test_create_engine(self):
        """Test ACE creation."""
        ace = AttractorComputeEngine("test_ace")
        assert ace.name == "test_ace"
    
    def test_set_field_state(self):
        """Test setting field state."""
        ace = AttractorComputeEngine()
        ace.set_field_state({"x": 1.0, "y": 2.0})
        assert ace.field_state["x"] == 1.0
    
    def test_compute_energy(self):
        """Test energy computation."""
        ace = AttractorComputeEngine()
        ace.set_field_state({"x": 1.0})
        ace.add_attractor({"center": {"x": 1.0}, "weight": 1.0})
        energy = ace.compute_energy()
        assert energy == 0.0
    
    def test_compute(self):
        """Test solution computation."""
        ace = AttractorComputeEngine()
        ace.set_field_state({"x": 0.0, "y": 0.0})
        ace.add_attractor({"center": {"x": 1.0, "y": 1.0}, "weight": 1.0})
        solution = ace.compute(max_steps=10)
        assert solution.stability_score >= 0.0
        assert solution.energy >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])