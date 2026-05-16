import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

"""
Phase 6 End-to-End Integration Test
=====================================
Tests recursive topology introspection: self-modeling, efficiency analysis.
"""

import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.topology_observer import TopologyObserver


def test_1_topology_tracking():
    print("\n=== Test 1: Topology Tracking ===")
    observer = TopologyObserver()
    observer.record_edge("planner", "execution", 0.8)
    observer.record_edge("execution", "memory", 0.6)
    observer.record_edge("memory", "repair", 0.5)
    observer.record_edge("repair", "planner", 0.7)

    topology = observer.get_topology_map()
    assert len(topology["patches"]) == 4
    assert topology["edge_count"] == 4
    print(f"  OK: {len(topology['patches'])} patches, {topology['edge_count']} edges")
    print("  PASS Test 1")


def test_2_sync_cost_analysis():
    print("\n=== Test 2: Sync Cost Analysis ===")
    observer = TopologyObserver()
    observer.record_edge("planner", "execution", 0.8)
    observer.record_edge("memory", "repair", 0.3)

    for i in range(20):
        observer.record_sync("planner", "execution", 0.5)
    for i in range(5):
        observer.record_sync("memory", "repair", 2.0)

    efficiency = observer.analyze_efficiency()
    assert efficiency["total_sync_cost"] > 0
    print(f"  OK: Total sync cost = {efficiency['total_sync_cost']}")
    print("  PASS Test 2")


def test_3_repair_efficiency():
    print("\n=== Test 3: Repair Efficiency ===")
    observer = TopologyObserver()
    observer.record_edge("planner", "execution", 0.8)
    observer.record_edge("memory", "repair", 0.3)

    for i in range(10):
        observer.record_repair("planner", "execution")
    for i in range(3):
        observer.record_repair("memory", "repair")

    efficiency = observer.analyze_efficiency()
    total_repairs = sum(observer._repair_counts.values())
    assert total_repairs == 13
    print(f"  OK: Total repairs = {total_repairs}")
    print("  PASS Test 3")


def test_4_restructuring_suggestions():
    print("\n=== Test 4: Restructuring Suggestions ===")
    observer = TopologyObserver()

    observer.record_edge("expensive_patch", "weak_patch", 0.2)
    for i in range(20):
        observer.record_sync("expensive_patch", "weak_patch", 1.5)

    observer.record_edge("unstable_a", "unstable_b", 0.5)
    for i in range(8):
        observer.record_repair("unstable_a", "unstable_b")

    suggestions = observer.suggest_restructuring()
    assert len(suggestions) > 0
    print(f"  OK: {len(suggestions)} suggestion(s) generated")
    print("  PASS Test 4")


def test_5_snapshot_history():
    print("\n=== Test 5: Snapshot History ===")
    observer = TopologyObserver()
    observer.record_edge("a", "b", 0.5)

    for i in range(5):
        observer.record_sync("a", "b", 0.1 * i)
        observer.take_snapshot()

    assert len(observer._snapshots) == 5
    print(f"  OK: {len(observer._snapshots)} snapshots taken")
    print("  PASS Test 5")


def run_all():
    print("=" * 60)
    print("SRRA-OPH Phase 6: End-to-End Integration Tests")
    print("=" * 60)

    tests = [test_1_topology_tracking, test_2_sync_cost_analysis,
             test_3_repair_efficiency, test_4_restructuring_suggestions,
             test_5_snapshot_history]

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
