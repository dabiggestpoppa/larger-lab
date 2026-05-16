"""
Phase 3 (Book 2 Updated) Tests
================================
Tests for overlap-first architecture components:
- Active Collar Fields
- Local Consensus Engines
- Capability Fields (Phase 4)
- Trajectory Fields (Phase 5)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.active_collar_fields import ActiveCollarField, CollarFieldManager
from srrs_opc.local_consensus import LocalConsensusEngine
from srrs_opc.capability_fields import CapabilityField, CapabilityFieldRegistry
from srrs_opc.trajectory_fields import TrajectoryFragment, TrajectoryReconstructionField


def test_1_active_collar_reconciliation():
    """Test 1: Active collar fields reconcile observer state."""
    print("\n=== Test 1: Active Collar Reconciliation ===")

    collar = ActiveCollarField("test_collar", ["observer_a", "observer_b"])

    # First reconciliation
    result1 = collar.reconcile("observer_a", {"key1": "value1", "key2": "value2"})
    assert result1["conflicts"] == 0, f"Expected 0 conflicts, got {result1['conflicts']}"
    print(f"  ✓ First reconcile: {result1['conflicts']} conflicts")

    # Second reconciliation with overlap
    result2 = collar.reconcile("observer_b", {"key1": "value1", "key3": "value3"})
    assert result2["conflicts"] == 0, f"Expected 0 conflicts for matching key1, got {result2['conflicts']}"
    print(f"  ✓ Second reconcile (matching): {result2['conflicts']} conflicts")

    # Third reconciliation with conflict
    result3 = collar.reconcile("observer_b", {"key2": "different_value"})
    assert result3["conflicts"] == 1, f"Expected 1 conflict, got {result3['conflicts']}"
    print(f"  ✓ Third reconcile (conflict): {result3['conflicts']} conflicts")

    # Check entropy increased
    assert collar.entropy_score > 0, "Entropy should increase with conflicts"
    print(f"  ✓ Entropy increased: {collar.entropy_score:.3f}")

    # Check viability decreased
    assert collar.reconstruction_viability < 1.0, "Viability should decrease with conflicts"
    print(f"  ✓ Viability: {collar.reconstruction_viability:.3f}")

    print("  ✅ Test 1 PASSED")


def test_2_collar_repair_queue():
    """Test 2: Collar repair queue processes stabilization tasks."""
    print("\n=== Test 2: Collar Repair Queue ===")

    collar = ActiveCollarField("repair_test", ["obs1", "obs2"])

    # Add repair tasks
    collar.add_repair_task({"type": "constraint_reconciliation", "key": "key2"})
    collar.add_repair_task({"type": "drift_correction", "observer": "obs1"})
    assert len(collar.repair_queue) == 2
    print(f"  ✓ Added 2 repair tasks")

    # Process repairs
    completed = collar.process_repairs()
    assert len(completed) == 2, f"Expected 2 completed, got {len(completed)}"
    print(f"  ✓ Processed {len(completed)} repairs")

    # Queue should be empty
    assert len(collar.repair_queue) == 0
    print(f"  ✓ Repair queue empty after processing")

    print("  ✅ Test 2 PASSED")


def test_3_local_consensus():
    """Test 3: Local consensus engines produce stable overlap closure."""
    print("\n=== Test 3: Local Consensus ===")

    engine = LocalConsensusEngine("consensus_1", ["obs1", "obs2", "obs3"])

    # Propose values
    engine.propose("obs1", "strategy", "mean_reversion", 0.9)
    engine.propose("obs2", "strategy", "mean_reversion", 0.85)
    engine.propose("obs3", "strategy", "momentum", 0.4)

    # Evaluate consensus
    result = engine.evaluate_consensus("strategy")
    assert result["converged"], f"Expected convergence, got {result}"
    assert result["consensus_value"] == "mean_reversion"
    print(f"  ✓ Consensus converged: {result['consensus_value']} (conf={result['consensus_confidence']})")

    # Verify local closure
    closure = engine.get_local_closure("strategy")
    assert closure["converged"] == True
    print(f"  ✓ Local closure confirmed")

    print("  ✅ Test 3 PASSED")


def test_4_capability_fields():
    """Test 4: Capability fields evaluate execution viability."""
    print("\n=== Test 4: Capability Fields ===")

    field = CapabilityField("claude", "reasoning", "Claude reasoning capability")
    field.add_affordance("analyze", 0.2)
    field.add_affordance("code", 0.3)
    field.add_affordance("execute", 0.6)

    # Test viable operation
    result = field.evaluate_execution("analyze", {})
    assert result["viable"] == True
    print(f"  ✓ 'analyze' viable: entropy_cost={result['entropy_cost']}")

    # Test unsupported operation
    result = field.evaluate_execution("fly", {})
    assert result["viable"] == False
    print(f"  ✓ 'fly' correctly rejected: {result['reason']}")

    # Test registry
    registry = CapabilityFieldRegistry()
    registry.register(field)
    capable = registry.find_capable("analyze")
    assert len(capable) == 1
    print(f"  ✓ Registry found {len(capable)} field(s) capable of 'analyze'")

    print("  ✅ Test 4 PASSED")


def test_5_trajectory_reconstruction():
    """Test 5: Trajectory fields reconstruct directional continuity."""
    print("\n=== Test 5: Trajectory Reconstruction ===")

    field = TrajectoryReconstructionField("traj_1")

    # Add fragments
    field.add_fragment("obs1", "System favors sparse representations", "sparse")
    field.add_fragment("obs2", "Sparse systems reduce entropy", "sparse")
    field.add_fragment("obs3", "Compression is key for scaling", "sparse")
    field.add_fragment("obs4", "Some prefer dense representations", "dense")

    # Reinforce dominant direction
    for frag in field.fragments.values():
        if frag.direction == "sparse":
            frag.reinforce()
            frag.reinforce()

    # Reconstruct
    result = field.reconstruct(min_weight=0.3)
    assert result["viable"] == True, f"Expected viable reconstruction, got {result}"
    assert result["dominant_direction"] == "sparse"
    print(f"  ✓ Reconstructed: direction={result['dominant_direction']}, weight={result['avg_weight']}")

    # Test viability
    viability = field.get_viability()
    assert viability["viable"] == True
    print(f"  ✓ Viability: {viability}")

    print("  ✅ Test 5 PASSED")


def test_6_trajectory_decay_and_prune():
    """Test 6: Trajectory fragments decay and can be pruned."""
    print("\n=== Test 6: Trajectory Decay & Prune ===")

    field = TrajectoryReconstructionField("traj_2")

    # Add fragments
    for i in range(10):
        field.add_fragment(f"obs_{i}", f"Fragment {i}", "test")

    initial_count = len(field.fragments)
    assert initial_count == 10

    # Apply decay many times
    for _ in range(50):
        field.apply_decay()

    # Prune weak
    pruned = field.prune_weak(threshold=0.3)
    remaining = len(field.fragments)

    assert remaining < initial_count, f"Expected pruning to reduce count"
    print(f"  ✓ Pruned {pruned} fragments, {remaining} remaining from {initial_count}")

    print("  ✅ Test 6 PASSED")


if __name__ == "__main__":
    print("=" * 60)
    print("SRRA-OPH Phase 3-5 (Book 2 Updated) Tests")
    print("=" * 60)

    test_1_active_collar_reconciliation()
    test_2_collar_repair_queue()
    test_3_local_consensus()
    test_4_capability_fields()
    test_5_trajectory_reconstruction()
    test_6_trajectory_decay_and_prune()

    print("\n" + "=" * 60)
    print("Results: 6 passed, 0 failed out of 6 tests")
    print("=" * 60)
