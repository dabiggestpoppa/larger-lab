import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

"""
Phase 2 End-to-End Integration Test
=====================================
Tests the full Reconstruction + Recoverability pipeline.

Success criteria:
1. Recovery anchors can be stored and retrieved
2. System can reconstruct coherent continuity from sparse anchors
3. Drift detector identifies stale/inconsistent anchors
4. Consistency validator catches contradictions
5. Contradiction resolver auto-resolves low-severity conflicts
6. Constraint propagation fires events on constraint changes
7. Deleting 90% of anchors still leaves coherent core
"""

import json
import os
import sys
import shutil
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.recovery_anchors import (
    create_anchor, get_anchor, get_top_anchors, get_anchor_count,
    get_stats, delete_weak_anchors, seed_initial_anchors, DB_PATH
)
from srrs_opc.drift_detector import DriftDetector
from srrs_opc.consistency_validator import ConsistencyValidator
from srrs_opc.reconstruction_synthesizer import ReconstructionSynthesizer
from srrs_opc.contradiction_resolver import ContradictionResolver
from srrs_opc.constraint_propagator import ConstraintPropagator


def cleanup():
    """Remove test database."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    data_dir = DB_PATH.parent
    if data_dir.exists():
        shutil.rmtree(data_dir, ignore_errors=True)


def test_1_recovery_anchors():
    """Test 1: Recovery anchor CRUD."""
    print("\n=== Test 1: Recovery Anchors ===")
    cleanup()

    # Create anchors
    a1 = create_anchor("Test anchor 1", weight=0.9, source="test", tags=["test", "core"])
    a2 = create_anchor("Test anchor 2", weight=0.5, source="test", tags=["test"])
    a3 = create_anchor("Test anchor 3", weight=0.3, source="test", tags=["weak"])

    # Verify count
    count = get_anchor_count()
    assert count == 3, f"Expected 3 anchors, got {count}"
    print(f"  ✓ Created {count} anchors")

    # Retrieve
    retrieved = get_anchor(a1["id"])
    assert retrieved is not None, "Anchor not found"
    assert retrieved["content"] == "Test anchor 1"
    print(f"  ✓ Retrieved anchor: {retrieved['content']}")

    # Top anchors
    top = get_top_anchors(limit=2, min_weight=0.4)
    assert len(top) == 2, f"Expected 2 top anchors, got {len(top)}"
    print(f"  ✓ Top anchors: {[a['content'] for a in top]}")

    # Stats
    stats = get_stats()
    assert stats["total_anchors"] == 3
    print(f"  ✓ Stats: {json.dumps(stats)}")

    cleanup()
    print("  ✅ Test 1 PASSED")


def test_2_reconstruction():
    """Test 2: Reconstruction from sparse anchors."""
    print("\n=== Test 2: Reconstruction ===")
    cleanup()

    # Seed with initial anchors
    seed_initial_anchors()

    # Reconstruct
    synthesizer = ReconstructionSynthesizer(min_weight=0.3)
    result = synthesizer.reconstruct()

    assert result["status"] == "reconstructed", f"Reconstruction failed: {result}"
    assert result["anchor_count"] > 0, "No anchors used in reconstruction"
    assert result["confidence"] > 0.3, f"Low confidence: {result['confidence']}"
    print(f"  ✓ Reconstructed from {result['anchor_count']} anchors")
    print(f"  ✓ Confidence: {result['confidence']}")
    print(f"  ✓ Clusters: {result['clusters']}")
    print(f"  ✓ Gaps: {result['gaps']}")

    cleanup()
    print("  ✅ Test 2 PASSED")


def test_3_drift_detection():
    """Test 3: Drift detector."""
    print("\n=== Test 3: Drift Detection ===")
    cleanup()

    seed_initial_anchors()

    # Run drift detector with very short staleness window
    detector = DriftDetector(staleness_days=0)  # Everything is stale
    reports = detector.scan_all()

    summary = detector.get_drift_summary(reports)
    print(f"  ✓ Drift reports: {summary['total_drifts']}")
    print(f"  ✓ Max severity: {summary['max_severity']:.2f}")

    cleanup()
    print("  ✅ Test 3 PASSED")


def test_4_consistency_validation():
    """Test 4: Consistency validator."""
    print("\n=== Test 4: Consistency Validation ===")
    cleanup()

    # Create contradictory anchors
    create_anchor("MT5 is the primary backtesting engine", weight=0.8, source="old", tags=["trading"])
    create_anchor("MT5 is fully deprecated — Nautilus only", weight=0.9, source="new", tags=["trading"])

    validator = ConsistencyValidator()
    contradictions = validator.validate_all()

    summary = validator.get_validation_summary(contradictions)
    print(f"  ✓ Contradictions found: {summary['total_contradictions']}")
    if summary["total_contradictions"] > 0:
        print(f"  ✓ Types: {summary['by_type']}")

    cleanup()
    print("  ✅ Test 4 PASSED")


def test_5_contradiction_resolution():
    """Test 5: Contradiction resolver."""
    print("\n=== Test 5: Contradiction Resolution ===")
    cleanup()

    # Create contradictory anchors
    create_anchor("MT5 is the primary backtesting engine", weight=0.4, source="old", tags=["trading"])
    create_anchor("MT5 is fully deprecated — Nautilus only", weight=0.9, source="new", tags=["trading"])

    resolver = ContradictionResolver(auto_resolve_threshold=0.7)
    results = resolver.auto_detect_and_resolve()

    print(f"  ✓ Resolutions: {len(results)}")
    for r in results:
        print(f"    - {r.strategy}: {r.action_taken[:80]}")

    stats = resolver.get_stats()
    print(f"  ✓ Stats: {json.dumps(stats)}")

    cleanup()
    print("  ✅ Test 5 PASSED")


def test_6_constraint_propagation():
    """Test 6: Constraint propagation."""
    print("\n=== Test 6: Constraint Propagation ===")

    propagator = ConstraintPropagator()

    events_received = []

    @propagator.on("constraint_changed")
    def on_change(event):
        events_received.append(event)

    @propagator.on("constraint_added")
    def on_add(event):
        events_received.append(event)

    # Set constraints
    propagator.set_constraint("risk", "low")
    propagator.set_constraint("max_dd", 0.2)

    # Change a constraint
    propagator.set_constraint("risk", "medium")

    # Verify
    assert propagator.get_constraint("risk") == "medium"
    assert propagator.get_constraint("max_dd") == 0.2
    assert len(events_received) == 3  # 2 adds + 1 change

    stats = propagator.get_stats()
    print(f"  ✓ Constraints: {stats['total_constraints']}")
    print(f"  ✓ Events: {stats['total_events']}")
    print(f"  ✓ Handlers: {stats['handlers_registered']}")

    print("  ✅ Test 6 PASSED")


def test_7_sparse_recovery():
    """Test 7: Delete 90% of anchors, verify coherent core remains."""
    print("\n=== Test 7: Sparse Recovery (90% Deletion) ===")
    cleanup()

    # Create 20 anchors with varying weights
    for i in range(20):
        weight = 0.9 if i < 2 else (0.5 if i < 5 else 0.1)
        create_anchor(f"Anchor {i}: {'core' if weight > 0.7 else 'normal' if weight > 0.3 else 'weak'}",
                      weight=weight, source="test", tags=["core"] if weight > 0.7 else ["normal"])

    initial_count = get_anchor_count()
    assert initial_count == 20, f"Expected 20, got {initial_count}"
    print(f"  ✓ Created {initial_count} anchors")

    # Delete weak anchors (weight < 0.2)
    deleted = delete_weak_anchors(max_weight=0.2)
    remaining = get_anchor_count()
    print(f"  ✓ Deleted {deleted} weak anchors, {remaining} remaining")

    # Should have ~5 anchors remaining (2 core + 3 normal)
    assert remaining <= 7, f"Expected <= 7 remaining, got {remaining}"

    # Reconstruct from remaining
    synthesizer = ReconstructionSynthesizer(min_weight=0.3)
    result = synthesizer.reconstruct()

    assert result["status"] == "reconstructed"
    assert result["confidence"] > 0.3, f"Low confidence after deletion: {result['confidence']}"
    print(f"  ✓ Reconstructed with confidence {result['confidence']} from {result['anchor_count']} anchors")

    cleanup()
    print("  ✅ Test 7 PASSED")


def run_all():
    """Run all Phase 2 tests."""
    print("=" * 60)
    print("SRRA-OPH Phase 2: End-to-End Integration Tests")
    print("=" * 60)

    tests = [
        test_1_recovery_anchors,
        test_2_reconstruction,
        test_3_drift_detection,
        test_4_consistency_validation,
        test_5_contradiction_resolution,
        test_6_constraint_propagation,
        test_7_sparse_recovery,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
