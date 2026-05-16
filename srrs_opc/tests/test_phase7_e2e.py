import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

"""
Phase 7 End-to-End Integration Test
=====================================
Tests multi-scale overlap ecologies + attractor-coherence governance.
"""

import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.collar_topology_engine import CollarTopologyEngine
from srrs_opc.prediction_contracts import PredictionContractManager, ContractStatus
from srrs_opc.attractor_reasoning import AttractorReasoningEngine


def test_1_overlap_cognition():
    """Test 1: Overlap-native cognition — cognition emerges in overlap."""
    print("\n=== Test 1: Overlap-Native Cognition ===")

    engine = CollarTopologyEngine()

    # Record overlap events between observers
    for i in range(20):
        engine.record_overlap_event("planner", "execution",
                                     coherence_delta=0.1, entropy_delta=0.02)
        engine.record_overlap_event("execution", "memory",
                                     coherence_delta=0.05, entropy_delta=0.03)

    metrics = engine.get_system_metrics()
    assert metrics["total_collars"] == 2
    assert metrics["avg_overlap_density"] > 0
    print(f"  OK: {metrics['total_collars']} collars, density={metrics['avg_overlap_density']}")

    # Check individual collar metrics
    collar = engine.get_collar_metrics("planner", "execution")
    assert collar is not None
    assert collar["overlap_density"] > 0
    assert collar["reconstruction_viability"] > 0.5
    print(f"  OK: Collar metrics — density={collar['overlap_density']}, viability={collar['reconstruction_viability']}")

    print("  PASS Test 1")


def test_2_collar_entropy_tracking():
    """Test 2: Collar entropy tracks instability in overlap."""
    print("\n=== Test 2: Collar Entropy Tracking ===")

    engine = CollarTopologyEngine()

    # Stable overlap
    for i in range(10):
        engine.record_overlap_event("stable_a", "stable_b",
                                     coherence_delta=0.1, entropy_delta=0.01)

    # Unstable overlap
    for i in range(10):
        engine.record_overlap_event("unstable_a", "unstable_b",
                                     coherence_delta=-0.05, entropy_delta=0.15)

    stable = engine.get_collar_metrics("stable_a", "stable_b")
    unstable = engine.get_collar_metrics("unstable_a", "unstable_b")

    assert stable["collar_entropy"] < unstable["collar_entropy"], \
        "Stable collar should have lower entropy"
    print(f"  OK: Stable entropy={stable['collar_entropy']} < unstable={unstable['collar_entropy']}")

    # Weak collars should be identified
    weak = engine.identify_weak_collars(threshold=0.5)
    assert len(weak) > 0, "Should identify weak collars"
    print(f"  OK: {len(weak)} weak collar(s) identified")

    print("  PASS Test 2")


def test_3_prediction_contracts():
    """Test 3: Prediction contracts enforce falsifiable evolution."""
    print("\n=== Test 3: Prediction Contracts ===")

    manager = PredictionContractManager()

    # Create contract for topology mutation
    contract = manager.create_contract(
        mutation_type="weaken_edge",
        target="memory-repair",
        expected_coherence_gain=0.1,
        expected_entropy_cost=0.05,
        rollback_feasibility=0.9
    )
    assert contract.status == ContractStatus.PENDING
    print(f"  OK: Contract created — {contract.contract_id}")

    # Validate with good outcome
    result = manager.validate_contract(contract.contract_id, 0.08, 0.04)
    assert result == True, "Contract should be validated"
    assert contract.status == ContractStatus.VALIDATED
    print(f"  OK: Contract validated")

    # Create contract that will be violated
    contract2 = manager.create_contract(
        mutation_type="strengthen_edge",
        target="planner-execution",
        expected_coherence_gain=0.15,
        expected_entropy_cost=0.05,
        rollback_feasibility=0.6
    )
    result2 = manager.validate_contract(contract2.contract_id, -0.05, 0.3)
    assert result2 == False, "Contract should be violated"
    assert contract2.status == ContractStatus.VIOLATED
    print(f"  OK: Contract correctly violated")

    # Check rollbacks
    rollbacks = manager.get_rollbacks_needed()
    assert len(rollbacks) > 0, "Should have rollbacks needed"
    print(f"  OK: {len(rollbacks)} rollback(s) needed")

    print("  PASS Test 3")


def test_4_attractor_reasoning():
    """Test 4: Reasoning converges toward stable cyclic attractors."""
    print("\n=== Test 4: Attractor Reasoning ===")

    engine = AttractorReasoningEngine(dimension=3)

    # Run reasoning that should converge
    result = engine.reason(
        problem_state=[0.8, 0.2, 0.5],
        attractor_id="test_problem",
        max_iterations=20
    )
    assert result["status"] == "converged", f"Should converge, got {result['status']}"
    assert result["stability"] > 0.5
    print(f"  OK: Converged in {result['iterations']} iterations, stability={result['stability']}")

    # Compressed insight should exist
    assert "compressed_insight" in result
    assert len(result["compressed_insight"]) == 3
    print(f"  OK: Compressed insight = {result['compressed_insight']}")

    # Second reasoning on same attractor should converge faster
    result2 = engine.reason(
        problem_state=[0.7, 0.3, 0.4],
        attractor_id="test_problem",
        max_iterations=20
    )
    assert result2["iterations"] <= result["iterations"], \
        "Second reasoning should converge faster"
    print(f"  OK: Second reasoning converged in {result2['iterations']} iterations")

    print("  PASS Test 4")


def test_5_multi_scale_metrics():
    """Test 5: Multi-scale metrics track system-wide coherence."""
    print("\n=== Test 5: Multi-Scale Metrics ===")

    engine = CollarTopologyEngine()

    # Simulate multi-scale activity
    for i in range(30):
        engine.record_overlap_event("planner", "execution", 0.1, 0.02)
        engine.record_overlap_event("execution", "memory", 0.05, 0.03)
        engine.record_overlap_event("memory", "repair", 0.03, 0.05)
        engine.record_overlap_event("repair", "planner", 0.08, 0.02)

    metrics = engine.get_system_metrics()
    assert metrics["total_collars"] == 4
    assert metrics["total_events"] == 120
    print(f"  OK: {metrics['total_collars']} collars, {metrics['total_events']} events")

    # System should have measurable coherence
    assert metrics["avg_overlap_density"] > 0
    assert metrics["avg_reconstruction_viability"] > 0.3
    print(f"  OK: Density={metrics['avg_overlap_density']}, viability={metrics['avg_reconstruction_viability']}")

    # Optimization suggestions should work
    suggestions = engine.suggest_overlap_optimizations()
    print(f"  OK: {len(suggestions)} optimization suggestion(s)")

    print("  PASS Test 5")


def test_6_structural_memory():
    """Test 6: Structural memory persists without event replay."""
    print("\n=== Test 6: Structural Memory ===")

    from srrs_opc.structural_memory import StructuralMemoryFields, MemoryLayer

    mem = StructuralMemoryFields()

    # Store structural memories
    mem.store(MemoryLayer.ATTRACTOR, "convergence_alpha",
              {"position": [0.7, 0.3, 0.5], "stability": 0.85}, weight=0.9)
    mem.store(MemoryLayer.TOPOLOGY, "coupling_graph",
              {"edges": {"planner-execution": 0.8}}, weight=0.85)
    mem.store(MemoryLayer.REPAIR, "local_first_policy",
              {"strategy": "local_before_global"}, weight=0.8)
    mem.store(MemoryLayer.TRAJECTORY, "operator_pattern",
              {"direction": "low_redundancy"}, weight=0.7)

    stats = mem.get_stats()
    assert stats["attractor"]["entries"] == 1
    assert stats["topology"]["entries"] == 1
    assert stats["repair"]["entries"] == 1
    assert stats["trajectory"]["entries"] == 1
    print(f"  OK: {len(stats)} memory layers populated")

    # Verify persistence without events
    persisted = mem.persist_without_events()
    assert len(persisted["attractors"]) == 1
    assert len(persisted["topology"]) == 1
    print(f"  OK: Continuity persists without event replay")

    # Compression should work
    for i in range(60):
        mem.store(MemoryLayer.EVENT, f"event_{i}", {"data": i}, weight=0.1)
    mem.compress(MemoryLayer.EVENT, max_entries=30)
    event_stats = mem.get_stats()["event"]
    assert event_stats["entries"] <= 30
    print(f"  OK: Compression works ({event_stats['entries']} entries after compression)")

    print("  PASS Test 6")


def run_all():
    print("=" * 60)
    print("SRRA-OPH Phase 7: End-to-End Integration Tests")
    print("=" * 60)

    tests = [
        test_1_overlap_cognition,
        test_2_collar_entropy_tracking,
        test_3_prediction_contracts,
        test_4_attractor_reasoning,
        test_5_multi_scale_metrics,
        test_6_structural_memory,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {len(tests)} tests")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
