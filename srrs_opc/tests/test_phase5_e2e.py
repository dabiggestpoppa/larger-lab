import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

"""
Phase 5 End-to-End Integration Test
=====================================
Tests long-horizon adaptation: drift tracking, reinforcement weighting.

Success criteria:
1. Long-term drift tracker detects gradual divergence
2. Reinforcement engine increases weight with recurrence
3. Decay reduces weight of unused anchors
4. Operator trajectory modeling works
5. Memory grows sublinearly (compression)
"""

import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.drift_tracker import LongTermDriftTracker
from srrs_opc.reinforcement_engine import ReinforcementEngine


def test_1_drift_detection():
    """Test 1: Long-term drift tracker detects gradual divergence."""
    print("\n=== Test 1: Long-Term Drift Detection ===")

    tracker = LongTermDriftTracker(window_size=50, sensitivity=0.15)

    import random
    random.seed(42)

    # Stable metric — no drift
    for i in range(100):
        tracker.record("stable_metric", 0.7 + random.gauss(0, 0.05))

    # Drifting metric — gradually increasing
    for i in range(100):
        tracker.record("drifting_metric", 0.1 + i * 0.005 + random.gauss(0, 0.02))

    signals = tracker.check_all()
    assert len(signals) > 0, "Should detect drift in drifting_metric"
    print(f"  OK: {len(signals)} drift signal(s) detected")

    # Check that drifting metric has a signal
    drifting_signals = [s for s in signals if "drifting" in s.drift_type]
    assert len(drifting_signals) > 0, "Should have drift signal for drifting_metric"
    print(f"  OK: Drift detected in drifting_metric (severity={drifting_signals[0].severity:.3f})")

    # Stable metric should NOT have a drift signal
    stable_signals = [s for s in signals if "stable" in s.drift_type]
    assert len(stable_signals) == 0, "Stable metric should not have drift signal"
    print(f"  OK: No false positive for stable metric")

    # Trend analysis
    trend = tracker.get_trend("drifting_metric")
    assert trend is not None
    assert trend["direction"] == "increasing", f"Expected increasing, got {trend['direction']}"
    print(f"  OK: Trend direction={trend['direction']}, slope={trend['slope']}")

    print("  PASS Test 1")


def test_2_reinforcement_weighting():
    """Test 2: Reinforcement increases weight with recurrence."""
    print("\n=== Test 2: Reinforcement Weighting ===")

    engine = ReinforcementEngine()

    # Reinforce anchor_1 frequently
    for i in range(20):
        engine.reinforce("anchor_frequent", is_strategic=True)

    # Reinforce anchor_2 rarely
    engine.reinforce("anchor_rare")

    # Check weights
    stats = engine.get_stats()
    assert stats["total_anchors"] == 2, f"Expected 2 anchors, got {stats['total_anchors']}"
    print(f"  OK: {stats['total_anchors']} anchors registered")

    strongest = engine.get_strongest(2)
    assert strongest[0]["anchor_id"] == "anchor_frequent", "Frequent anchor should be strongest"
    assert strongest[0]["weight"] > strongest[1]["weight"], "Frequent anchor should have higher weight"
    print(f"  OK: Frequent anchor weight={strongest[0]['weight']:.3f} > rare={strongest[1]['weight']:.3f}")

    print("  PASS Test 2")


def test_3_decay():
    """Test 3: Decay reduces weight of unused anchors."""
    print("\n=== Test 3: Decay ===")

    engine = ReinforcementEngine(decay_rate=0.05)

    # Create an anchor and reinforce it once
    engine.register("decay_test", initial_weight=0.8)
    engine.reinforce("decay_test")

    initial_weight = engine._records["decay_test"].weight
    print(f"  OK: Initial weight after reinforce: {initial_weight:.3f}")

    # Apply decay many times
    for i in range(50):
        engine.decay_all()

    final_weight = engine._records["decay_test"].weight
    assert final_weight < initial_weight, f"Decay should reduce weight: {final_weight} vs {initial_weight}"
    print(f"  OK: Weight decayed from {initial_weight:.3f} to {final_weight:.3f}")

    print("  PASS Test 3")


def test_4_operator_trajectory():
    """Test 4: Operator trajectory modeling works."""
    print("\n=== Test 4: Operator Trajectory ===")

    engine = ReinforcementEngine()

    # Record operator patterns
    patterns = ["low_redundancy", "deterministic_execution", "mean_reversion",
                "low_redundancy", "low_redundancy", "deterministic_execution"]
    for p in patterns:
        engine.record_operator_pattern(p)

    trajectory = engine.get_operator_trajectory()
    assert trajectory["total_observations"] == 6
    assert trajectory["unique_patterns"] == 3
    print(f"  OK: {trajectory['unique_patterns']} unique patterns from {trajectory['total_observations']} observations")

    # Most frequent should be low_redundancy
    assert trajectory["dominant_patterns"][0]["pattern"] == "low_redundancy"
    print(f"  OK: Dominant pattern = '{trajectory['dominant_patterns'][0]['pattern']}'")

    print("  PASS Test 4")


def test_5_sublinear_growth():
    """Test 5: Memory grows sublinearly (compression principle)."""
    print("\n=== Test 5: Sublinear Growth (Compression) ===")

    engine = ReinforcementEngine()

    # Simulate 100 anchor creations with reinforcement
    for i in range(100):
        anchor_id = f"anchor_{i % 20}"  # Only 20 unique anchors, repeated
        engine.reinforce(anchor_id)

    stats = engine.get_stats()
    # Should have 20 unique anchors, not 100
    assert stats["total_anchors"] == 20, f"Expected 20 unique anchors, got {stats['total_anchors']}"
    print(f"  OK: {stats['total_anchors']} unique anchors from 100 operations (compression working)")

    # Average weight should be high (frequent reinforcement)
    assert stats["avg_weight"] > 0.5, f"Average weight should be > 0.5, got {stats['avg_weight']}"
    print(f"  OK: Average weight = {stats['avg_weight']:.3f}")

    print("  PASS Test 5")


def run_all():
    print("=" * 60)
    print("SRRA-OPH Phase 5: End-to-End Integration Tests")
    print("=" * 60)

    tests = [
        test_1_drift_detection,
        test_2_reinforcement_weighting,
        test_3_decay,
        test_4_operator_trajectory,
        test_5_sublinear_growth,
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
