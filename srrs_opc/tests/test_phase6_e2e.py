import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

"""
Phase 6 End-to-End Integration Test
=====================================
Tests recursive topology introspection.

Success criteria:
1. Topology snapshots capture system state
2. Coherence report identifies helpful vs harmful regions
3. Optimization candidates are identified
4. Repair density tracking works
5. Entropy zone detection works
"""

import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.topology_introspector import TopologyIntrospector


def test_1_snapshot():
    """Test 1: Topology snapshots capture system state."""
    print("\n=== Test 1: Topology Snapshot ===")

    intro = TopologyIntrospector()

    # Record some activity
    for i in range(20):
        intro.record_patch_activity("planner", 0.8)
        intro.record_patch_activity("execution", 0.6)
        intro.record_edge_usage("planner-execution")

    snapshot = intro.take_snapshot()
    assert snapshot is not None, "Snapshot should be created"
    assert len(snapshot.patches) == 2, f"Expected 2 patches, got {len(snapshot.patches)}"
    print(f"  OK: Snapshot with {len(snapshot.patches)} patches")

    stats = intro.get_stats()
    assert stats["snapshots_taken"] == 1
    print(f"  OK: Stats tracking works")

    print("  PASS Test 1")


def test_2_coherence_report():
    """Test 2: Coherence report identifies helpful vs harmful regions."""
    print("\n=== Test 2: Coherence Report ===")

    intro = TopologyIntrospector()

    # High activity, low repairs = coherent
    for i in range(30):
        intro.record_patch_activity("coherent_patch", 0.9)
        intro.record_patch_activity("noisy_patch", 0.2)

    # Noisy patch has many repairs
    for i in range(10):
        intro.record_repair("noisy_patch", 0.7, resolved=False)

    intro.take_snapshot()
    report = intro.get_coherence_report()

    assert "top_coherent" in report, "Report should have top_coherent"
    assert len(report["top_coherent"]) > 0, "Should have at least one coherent patch"
    print(f"  OK: Top coherent: {report['top_coherent'][:2]}")

    # Noisy patch should be in bottom or entropy zones
    bottom_names = [p[0] for p in report.get("bottom_coherent", [])]
    entropy_names = [z["patch"] for z in report.get("entropy_zones", [])]
    assert "noisy_patch" in bottom_names or "noisy_patch" in entropy_names, \
        "Noisy patch should be flagged"
    print(f"  OK: Noisy patch correctly flagged")

    print("  PASS Test 2")


def test_3_optimization_candidates():
    """Test 3: Optimization candidates are identified."""
    print("\n=== Test 3: Optimization Candidates ===")

    intro = TopologyIntrospector()

    # Create a high-repair region
    for i in range(50):
        intro.record_patch_activity("hotspot", 0.5)
        intro.record_patch_activity("isolated", 0.05)
        if i % 2 == 0:
            intro.record_repair("hotspot", 0.6, resolved=True)

    intro.take_snapshot()
    candidates = intro.get_optimization_candidates()

    assert len(candidates) > 0, "Should have optimization candidates"
    print(f"  OK: {len(candidates)} optimization candidate(s)")

    types = [c["type"] for c in candidates]
    assert "high_repair_density" in types or "isolated_patch" in types, \
        f"Should identify repair density or isolation issues, got: {types}"
    print(f"  OK: Candidate types: {types}")

    print("  PASS Test 3")


def test_4_repair_tracking():
    """Test 4: Repair density tracking works."""
    print("\n=== Test 4: Repair Tracking ===")

    intro = TopologyIntrospector()

    for i in range(20):
        intro.record_repair("region_a", 0.5, resolved=True)
        if i % 2 == 0:
            intro.record_repair("region_b", 0.3, resolved=False)

    intro.take_snapshot()
    report = intro.get_coherence_report()

    assert report["total_repairs_last_50"] > 0, "Should track repairs"
    print(f"  OK: {report['total_repairs_last_50']} repairs tracked")

    print("  PASS Test 4")


def test_5_entropy_zones():
    """Test 5: Entropy zone detection works."""
    print("\n=== Test 5: Entropy Zone Detection ===")

    intro = TopologyIntrospector()

    # Create an entropy zone: low activity, high repairs
    for i in range(50):
        intro.record_patch_activity("entropy_zone", 0.05)  # Very low activity
        intro.record_patch_activity("healthy", 0.8)  # High activity
        intro.record_repair("entropy_zone", 0.7, resolved=False)  # Many repairs

    intro.take_snapshot()
    report = intro.get_coherence_report()

    entropy_patches = [z["patch"] for z in report.get("entropy_zones", [])]
    assert "entropy_zone" in entropy_patches, \
        f"Low-activity high-repair patch should be entropy zone, got: {entropy_patches}"
    print(f"  OK: Entropy zone correctly detected: {entropy_patches}")

    print("  PASS Test 5")


def run_all():
    print("=" * 60)
    print("SRRA-OPH Phase 6: End-to-End Integration Tests")
    print("=" * 60)

    tests = [
        test_1_snapshot,
        test_2_coherence_report,
        test_3_optimization_candidates,
        test_4_repair_tracking,
        test_5_entropy_zones,
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

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
