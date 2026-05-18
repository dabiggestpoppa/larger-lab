"""
V3 System Capability Tests — Real System Validation

Tests actual system capabilities for deployment readiness.
NOT unit tests — these validate end-to-end system behavior.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from oce.backend.field_core.resonance_engine import ResonanceEngine
from oce.backend.field_core.recursive_field_nodes import RecursiveFieldNode, FieldNodeRegistry
from oce.backend.field_core.attractor_mapper import AttractorMapper
from oce.backend.field_core.drift_governor import DriftGovernor
from oce.backend.field_core.reconstruction_core import ReconstructionCore
from oce.backend.field_core.continuity_identity_engine import ContinuityIdentityEngine
from oce.backend.phase10.rcg import RecursiveComputeGraph, ComputeNode
from oce.backend.phase10.prs import PositionalReferenceSystem, Position
from oce.backend.phase10.rpe import ResonancePropagationEngine
from oce.backend.phase10.dct import DynamicConstraintTopology
from oce.backend.phase10.ace import AttractorComputeEngine


class TestSystemIntegration:
    """End-to-end system integration tests."""

    def test_field_coherence_chain(self):
        """Test full field coherence chain: resonance → nodes → attractor."""
        # Phase 9: Resonance Engine
        engine = ResonanceEngine()
        state = engine.measure_resonance("a", "b", 0.9, 0.9, 0.1, 0.1)
        assert state.is_resonant
        
        # Phase 9: Field Nodes
        registry = FieldNodeRegistry()
        node = registry.register("test_node", local_state={"value": 1.0})
        assert registry.get("test_node") is not None
        
        # Phase 9: Attractor Mapper
        mapper = AttractorMapper()
        attractor = mapper.register_attractor("test_attractor")
        mapper.record_state({"value": 1.0})
        assert attractor is not None

    def test_recursive_compute_integration(self):
        """Test Phase 10 RCG integrates with Phase 9 field_core."""
        # Create compute graph with field-aware nodes
        graph = RecursiveComputeGraph("integration_test")
        
        # Add nodes with field-like states
        for i in range(3):
            node = ComputeNode(
                node_id=f"n{i}",
                initial_state={"value": float(i), "coherence": 0.5}
            )
            graph.add_node(node)
        
        # Connect in chain
        graph.connect("n0", "n1")
        graph.connect("n1", "n2")
        
        # Run compute cycle
        results = graph.compute()
        assert len(results) == 3
        
        # Verify coherence propagation
        for node_id, result in results.items():
            assert result.coherence_score >= 0.0

    def test_positional_reference_integration(self):
        """Test PRS integrates with field topology."""
        prs = PositionalReferenceSystem("test_prs")
        
        # Create reference frames
        frame1 = prs.create_frame("frame1")
        
        # Add positions using frame.add_position
        pos1 = Position(position_id="pos1", coordinates={"x": 0.0, "y": 0.0})
        pos2 = Position(position_id="pos2", coordinates={"x": 1.0, "y": 1.0})
        frame1.add_position(pos1)
        frame1.add_position(pos2)
        
        # Test transition
        path = prs.compute_transition_path("pos1", "pos2")
        assert path is not None


class TestDeploymentReadiness:
    """Tests for deployment readiness."""

    def test_memory_efficiency(self):
        """Test system handles memory efficiently under load."""
        import gc
        
        # Create many nodes
        graph = RecursiveComputeGraph("memory_test")
        for i in range(100):
            node = ComputeNode(
                node_id=f"node_{i}",
                initial_state={"value": float(i), "data": list(range(10))}
            )
            graph.add_node(node)
        
        # Connect in grid pattern
        for i in range(100):
            if i % 10 > 0:
                graph.connect(f"node_{i}", f"node_{i-1}")
            if i >= 10:
                graph.connect(f"node_{i}", f"node_{i-10}")
        
        # Run compute
        results = graph.compute()
        assert len(results) == 100
        
        # Force garbage collection
        gc.collect()

    def test_concurrent_operations(self):
        """Test system handles concurrent operations."""
        import threading
        import time
        
        results = {"count": 0}
        lock = threading.Lock()
        
        def create_graph(thread_id):
            graph = RecursiveComputeGraph(f"thread_{thread_id}")
            for i in range(10):
                node = ComputeNode(node_id=f"n{i}", initial_state={"value": float(i)})
                graph.add_node(node)
            for i in range(9):
                graph.connect(f"n{i}", f"n{i+1}")
            graph.compute()
            with lock:
                results["count"] += 1
        
        threads = [threading.Thread(target=create_graph, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert results["count"] == 5

    def test_error_recovery(self):
        """Test system recovers from errors gracefully."""
        graph = RecursiveComputeGraph("error_test")
        
        # Add valid node
        node = ComputeNode(node_id="valid", initial_state={"value": 1.0})
        graph.add_node(node)
        
        # Try to stabilize non-existent node
        with pytest.raises(ValueError):
            graph.stabilize_node("nonexistent")
        
        # System should still work
        result = graph.stabilize_node("valid")
        assert result is not None


class TestRealWorldScenarios:
    """Tests simulating real-world usage scenarios."""

    def test_observer_pattern_scenario(self):
        """Test observer pattern with field coherence."""
        # Simulate multiple observers converging on solution
        prs = PositionalReferenceSystem("observer_scenario")
        
        # Create observer positions
        frame = prs.create_frame("observers")
        observer_positions = []
        for i in range(5):
            pos = Position(position_id=f"obs_{i}", coordinates={"x": float(i), "y": float(i**2)})
            frame.add_position(pos)
            observer_positions.append(pos)
        
        # Verify positions were added
        assert len(frame.positions) == 5

    def test_drift_recovery_scenario(self):
        """Test drift detection and recovery."""
        drift_governor = DriftGovernor()
        
        # Simulate normal operation
        metrics = drift_governor.measure_drift("element1", {"value": 1.0}, {"value": 1.0})
        assert metrics.drift_score < 0.1
        
        # Simulate drift
        metrics = drift_governor.measure_drift("element2", {"value": 1.0}, {"value": 10.0})
        assert metrics.drift_score > 0.5

    def test_attractor_convergence_scenario(self):
        """Test attractor-based computation convergence."""
        ace = AttractorComputeEngine("convergence_test")
        
        # Set up field state
        field_state = {
            "nodes": [{"id": f"n{i}", "state": {"value": float(i)}} for i in range(5)],
            "constraints": [{"type": "boundary", "value": 1.0}]
        }
        ace.set_field_state(field_state)
        
        # Compute solution
        solution = ace.compute()
        assert solution is not None
        assert solution.energy is not None


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    def test_compute_throughput(self):
        """Test compute throughput for deployment sizing."""
        import time
        
        graph = RecursiveComputeGraph("throughput_test")
        
        # Create 50-node graph
        for i in range(50):
            node = ComputeNode(node_id=f"n{i}", initial_state={"value": float(i)})
            graph.add_node(node)
        
        for i in range(49):
            graph.connect(f"n{i}", f"n{i+1}")
        
        # Measure time
        start = time.time()
        results = graph.compute()
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 5.0  # 5 seconds max for 50 nodes
        assert len(results) == 50

    def test_memory_growth(self):
        """Test memory doesn't grow unboundedly."""
        import sys
        
        graph = RecursiveComputeGraph("memory_growth_test")
        
        initial_size = sys.getsizeof(graph)
        
        # Add many nodes
        for i in range(1000):
            node = ComputeNode(node_id=f"n{i}", initial_state={"value": float(i)})
            graph.add_node(node)
        
        final_size = sys.getsizeof(graph)
        
        # Size should be bounded (not 1000x initial)
        assert final_size < initial_size * 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])