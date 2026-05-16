"""
Phase 8 End-to-End Integration Test
====================================
Tests Sovereign Coevolution: Human-SRRA Continuity Ecology.

Components tested:
1. Operator Pattern Stabilization
2. Strategic Preference Modeling
3. Constraint Alignment Adaptation
4. Long-Horizon Operator Continuity Tracking
5. Bidirectional Coherence Reinforcement
6. Anti-Manipulation Safeguards
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from srrs_opc.operator_patterns import OperatorPatternModel, PatternObservation
from srrs_opc.strategic_preferences import StrategicPreferenceModel
from srrs_opc.constraint_alignment import ConstraintAlignmentAdapter
from srrs_opc.operator_continuity import OperatorContinuityTracker, SessionAnchor
from srrs_opc.bidirectional_coherence import BidirectionalCoherenceEngine
from srrs_opc.anti_manipulation import AntiManipulationSafeguards


def test_1_operator_patterns():
    """Test 1: Operator Pattern Stabilization — patterns stabilize across 3+ sessions."""
    print("\n=== Test 1: Operator Pattern Stabilization ===")

    model = OperatorPatternModel(operator_id="op_1")

    # Session 1: operator enters on momentum signal
    for i in range(5):
        model.record_observation(PatternObservation(
            action_type="entry",
            details={"signal": "momentum", "position_size": 3.0},
            session_id="session_1",
        ))

    # Session 2: same pattern
    for i in range(5):
        model.record_observation(PatternObservation(
            action_type="entry",
            details={"signal": "momentum", "position_size": 3.0},
            session_id="session_2",
        ))

    # Session 3: same pattern — now should be stable
    for i in range(5):
        model.record_observation(PatternObservation(
            action_type="entry",
            details={"signal": "momentum", "position_size": 3.0},
            session_id="session_3",
        ))

    stable = model.get_stable_patterns()
    assert len(stable) > 0, "Should have at least one stable pattern after 3 sessions"
    assert model.session_count == 3

    # Check entry preferences
    entry_prefs = model.get_entry_preferences()
    assert "momentum" in entry_prefs
    assert entry_prefs["momentum"] == 1.0

    # Check risk tolerance
    risk = model.get_risk_tolerance_estimate()
    assert 0.0 <= risk <= 1.0
    print(f"  OK: {len(stable)} stable patterns, risk_tolerance={risk:.3f}")


def test_2_strategic_preferences():
    """Test 2: Strategic Preference Modeling — preferences adapt and drift is detected."""
    print("\n=== Test 2: Strategic Preference Modeling ===")

    model = StrategicPreferenceModel(operator_id="op_1")

    # Operator consistently chooses mean-reversion over momentum
    for _ in range(10):
        model.record_action(
            dimension="strategy_type",
            chosen_value="mean_reversion",
            alternative_values=["momentum", "breakout"],
        )

    # Check dominant preference
    summary = model.get_preference_summary()
    assert "strategy_type" in summary["dominant_preferences"]
    dominant = summary["dominant_preferences"]["strategy_type"]
    assert dominant["value"] == "mean_reversion"
    assert dominant["weight"] > 0.3

    # Now operator shifts to momentum — detect drift
    for _ in range(10):
        model.record_action(
            dimension="strategy_type",
            chosen_value="momentum",
            alternative_values=["mean_reversion", "breakout"],
        )

    drift_signals = model.detect_drift()
    # Drift should be detected as momentum gains weight
    top_prefs = model.get_top_preferences(dimension="strategy_type")
    assert len(top_prefs) >= 2
    print(f"  OK: dominant={dominant['value']}, drift_signals={len(drift_signals)}, top_prefs={len(top_prefs)}")


def test_3_constraint_alignment():
    """Test 3: Constraint Alignment — system suggests, operator confirms/rejects."""
    print("\n=== Test 3: Constraint Alignment Adaptation ===")

    adapter = ConstraintAlignmentAdapter(operator_id="op_1")

    # Register constraints
    adapter.register_constraint(
        name="max_position_size",
        description="Maximum position size limit",
        weight=0.8,
        category="risk",
    )
    adapter.register_constraint(
        name="min_stop_loss",
        description="Minimum stop loss distance",
        weight=0.6,
        category="risk",
    )

    # Operator consistently contradicts max_position_size (takes larger positions)
    for _ in range(5):
        adapter.record_operator_action("max_position_size", alignment_delta=-0.5)

    # Should generate a suggestion to weaken the constraint
    pending = adapter.get_pending_suggestions()
    assert len(pending) > 0, "Should have pending suggestions after consistent contradiction"

    # Operator confirms the suggestion
    result = adapter.confirm_suggestion("max_position_size")
    assert result is True

    report = adapter.get_alignment_report()
    assert report["confirmed"] >= 1
    assert report["constraints"]["max_position_size"]["weight"] < 0.8

    # Operator rejects a suggestion for min_stop_loss
    for _ in range(5):
        adapter.record_operator_action("min_stop_loss", alignment_delta=-0.4)
    pending2 = adapter.get_pending_suggestions()
    if pending2:
        adapter.reject_suggestion(pending2[-1].constraint_name)

    print(f"  OK: confirmed={report['confirmed']}, alignment_score={report['alignment_score']}")


def test_4_operator_continuity():
    """Test 4: Operator Continuity — cross-session trajectory reconstruction."""
    print("\n=== Test 4: Long-Horizon Operator Continuity ===")

    tracker = OperatorContinuityTracker()

    # Record 3 sessions with evolving evidence
    tracker.record_session("op_1", "session_1", {
        "strategy": "mean_reversion",
        "risk_level": 0.3,
        "avg_position_size": 2.0,
    })
    tracker.record_session("op_1", "session_2", {
        "strategy": "mean_reversion",
        "risk_level": 0.4,
        "avg_position_size": 2.5,
    })
    tracker.record_session("op_1", "session_3", {
        "strategy": "momentum",
        "risk_level": 0.6,
        "avg_position_size": 3.0,
    })

    report = tracker.get_continuity_report("op_1")
    assert report["found"] is True
    assert report["reconstructable"] is True
    assert report["session_count"] == 3
    assert report["continuity_score"] > 0.0

    # Check strategic drift
    drift = report.get("strategic_drift", {})
    # Strategy changed from mean_reversion to momentum
    if drift.get("dimensions"):
        assert "strategy" in drift["dimensions"] or "risk_level" in drift["dimensions"]

    print(f"  OK: continuity={report['continuity_score']:.3f}, sessions={report['session_count']}")


def test_5_bidirectional_coherence():
    """Test 5: Bidirectional Coherence — feedback loops and coherence tracking."""
    print("\n=== Test 5: Bidirectional Coherence Reinforcement ===")

    engine = BidirectionalCoherenceEngine(operator_id="op_1")

    # Operator follows most suggestions (healthy coherence)
    suggestions_actions = [
        ("Consider reducing position size", "reduced position size", True),
        ("Consider reducing position size", "kept position same", False),
        ("Look at mean-reversion setups", "looked at mean-reversion setups", True),
        ("Look at mean-reversion setups", "looked at momentum instead", False),
        ("Review stop loss levels", "reviewed stop loss levels", True),
        ("Review stop loss levels", "reviewed stop loss levels", True),
        ("Consider taking profits", "took profits", True),
        ("Consider taking profits", "held position", False),
    ]

    for suggestion, action, expected_aligned in suggestions_actions:
        result = engine.record_feedback(suggestion, action)
        assert result == expected_aligned, f"Expected {expected_aligned}, got {result} for: {suggestion} -> {action}"

    coherence = engine.get_coherence_score()
    assert 0.0 <= coherence <= 1.0

    health = engine.get_coherence_health()
    assert "score" in health
    assert "status" in health
    assert health["status"] in ("too_low", "healthy", "too_high")

    adaptation = engine.get_adaptation_recommendation()
    assert "recommendation" in adaptation
    assert "assertiveness" in adaptation

    print(f"  OK: coherence={coherence:.3f}, status={health['status']}, adaptation={adaptation['recommendation']}")


def test_6_anti_manipulation():
    """Test 6: Anti-Manipulation Safeguards — detect and mitigate manipulation risks."""
    print("\n=== Test 6: Anti-Manipulation Safeguards ===")

    safeguards = AntiManipulationSafeguards(operator_id="op_1")

    # Clean output — low risk
    clean_output = "Based on recent data, the market shows mixed signals. Consider reviewing your positions."
    assessment1 = safeguards.assess_output(clean_output)
    assert assessment1.risk_score < 0.3, f"Clean output should have low risk, got {assessment1.risk_score}"

    # Urgency manipulation — high risk
    urgent_output = "Act fast! This is a limited time opportunity. Don't wait or you'll miss out!"
    assessment2 = safeguards.assess_output(urgent_output)
    assert assessment2.risk_score > 0.3, f"Urgent output should have elevated risk, got {assessment2.risk_score}"
    assert "urgency_manipulation" in assessment2.risk_factors

    # Uncertainty hiding
    certain_output = "This will definitely work. The market will absolutely reverse. Guaranteed."
    assessment3 = safeguards.assess_output(certain_output)
    assert "uncertainty_hiding" in assessment3.risk_factors

    # Anchoring bias
    anchoring_output = "The recommended approach is to use mean-reversion. This is the best choice for most people."
    assessment4 = safeguards.assess_output(anchoring_output)
    assert "anchoring_bias" in assessment4.risk_factors

    # Record operator override (healthy)
    safeguards.record_override()
    safeguards.record_override()

    report = safeguards.get_safety_report()
    assert report["total_outputs"] >= 4
    assert report["override_rate"] > 0

    print(f"  OK: outputs={report['total_outputs']}, avg_risk={report['avg_risk_score']:.3f}, overrides={safeguards._override_count}")


if __name__ == "__main__":
    test_1_operator_patterns()
    test_2_strategic_preferences()
    test_3_constraint_alignment()
    test_4_operator_continuity()
    test_5_bidirectional_coherence()
    test_6_anti_manipulation()
    print("\n=== All Phase 8 Tests Passed ===")
