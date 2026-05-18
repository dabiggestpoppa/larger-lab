"""Tests for V3 Phase 8 — Operator Coevolution"""

import pytest

from oce.backend.coevolution.operator_model import OperatorModel, OperatorPattern
from oce.backend.coevolution.constraint_model import ConstraintModel, OperatorConstraint
from oce.backend.coevolution.coherence_reinforcement import CoherenceReinforcement, CoherenceEvent
from oce.backend.coevolution.bidirectional_adaptation import BidirectionalAdaptation, AdaptationEvent
from oce.backend.coevolution.cognitive_load import CognitiveLoadOptimizer, LoadMeasurement
from oce.backend.coevolution.alignment_tracking import AlignmentTracker, AlignmentMeasurement
from oce.backend.coevolution.anti_manipulation import AntiManipulationSafeguards, SafeguardCheck


# ─────────────────────────────────────────────────────────
# OperatorModel
# ─────────────────────────────────────────────────────────

class TestOperatorModel:

    def test_create_model(self):
        model = OperatorModel()
        assert model.patterns == {}
        assert model._observation_log == []

    def test_record_observation(self):
        model = OperatorModel()
        model.record_observation("priority", "focus on risk management")
        assert len(model._observation_log) == 1

    def test_pattern_emerges_after_repeated_observations(self):
        model = OperatorModel()
        model.record_observation("priority", "focus on risk")
        model.record_observation("priority", "focus on risk again")
        model.record_observation("priority", "still risk focus")
        reliable = model.get_reliable_patterns()
        assert len(reliable) >= 1

    def test_pattern_confidence_increases(self):
        model = OperatorModel()
        model.record_observation("timing", "early entry")
        model.record_observation("timing", "early entry again")
        patterns = list(model.patterns.values())
        assert len(patterns) >= 1
        assert patterns[0].confidence > 0.5

    def test_predict_focus_returns_none_when_no_patterns(self):
        model = OperatorModel()
        assert model.predict_focus() is None

    def test_predict_focus_returns_pattern_type(self):
        model = OperatorModel()
        for _ in range(5):
            model.record_observation("focus", "strategic planning")
        prediction = model.predict_focus()
        assert prediction is not None

    def test_pattern_is_reliable(self):
        pattern = OperatorPattern(
            pattern_id="p1", pattern_type="priority",
            description="test", evidence_count=5, confidence=0.8,
        )
        assert pattern.is_reliable

    def test_pattern_not_reliable_low_confidence(self):
        pattern = OperatorPattern(
            pattern_id="p1", pattern_type="priority",
            description="test", evidence_count=1, confidence=0.3,
        )
        assert not pattern.is_reliable

    def test_pattern_record_evidence(self):
        pattern = OperatorPattern(
            pattern_id="p1", pattern_type="priority",
            description="test", evidence_count=1, confidence=0.5,
        )
        pattern.record_evidence()
        assert pattern.evidence_count == 2
        assert pattern.confidence > 0.5


# ─────────────────────────────────────────────────────────
# ConstraintModel
# ─────────────────────────────────────────────────────────

class TestConstraintModel:

    def test_create_model(self):
        model = ConstraintModel()
        assert len(model.constraints) > 0

    def test_default_constraints_initialized(self):
        model = ConstraintModel()
        assert "time" in model.constraints
        assert "energy" in model.constraints
        assert "bandwidth" in model.constraints

    def test_update_constraint(self):
        model = ConstraintModel()
        model.update_constraint("time", 0.8, "operator busy")
        # update_constraint calls record_observation which adds 0.05 to severity
        assert model.constraints["time"].severity == pytest.approx(0.85, abs=0.01)

    def test_get_active_constraints(self):
        model = ConstraintModel()
        active = model.get_active_constraints()
        assert len(active) > 0
        assert all(c.is_active for c in active)

    def test_capacity_estimate(self):
        model = ConstraintModel()
        capacity = model.get_capacity_estimate()
        assert 0.0 <= capacity <= 1.0

    def test_should_reduce_load_low_capacity(self):
        model = ConstraintModel()
        for c in model.constraints.values():
            c.severity = 0.95
        assert model.should_reduce_load()

    def test_should_not_reduce_load_high_capacity(self):
        model = ConstraintModel()
        for c in model.constraints.values():
            c.severity = 0.1
        assert not model.should_reduce_load()

    def test_add_new_constraint_type(self):
        model = ConstraintModel()
        model.update_constraint("custom_type", 0.6, "custom constraint")
        assert "custom_type" in model.constraints

    def test_constraint_observation_count(self):
        model = ConstraintModel()
        model.update_constraint("time", 0.7)
        model.update_constraint("time", 0.8)
        assert model.constraints["time"].observed_count >= 2

    def test_stats(self):
        model = ConstraintModel()
        stats = model.stats
        assert "total_constraints" in stats
        assert "active_constraints" in stats
        assert "capacity_estimate" in stats


# ─────────────────────────────────────────────────────────
# CoherenceReinforcement
# ─────────────────────────────────────────────────────────

class TestCoherenceReinforcement:

    def test_create(self):
        cr = CoherenceReinforcement()
        assert cr._events == []

    def test_record_beneficial_event(self):
        cr = CoherenceReinforcement()
        event = cr.record_event("operator_action", "good decision", 0.3, 0.6)
        assert event.was_beneficial
        assert event.reinforced

    def test_record_non_beneficial_event(self):
        cr = CoherenceReinforcement()
        event = cr.record_event("operator_action", "bad decision", 0.6, 0.3)
        assert not event.was_beneficial
        assert not event.reinforced

    def test_record_neutral_event(self):
        cr = CoherenceReinforcement()
        event = cr.record_event("operator_action", "neutral", 0.5, 0.52)
        assert not event.was_beneficial  # improvement < 0.05

    def test_reinforced_patterns(self):
        cr = CoherenceReinforcement()
        cr.record_event("operator_action", "good decision A", 0.3, 0.6)
        cr.record_event("operator_action", "good decision A", 0.3, 0.6)
        patterns = cr.get_reinforced_patterns()
        assert len(patterns) >= 1

    def test_coherence_trend_positive(self):
        cr = CoherenceReinforcement()
        cr.record_event("action", "improving", 0.2, 0.5)
        cr.record_event("action", "improving more", 0.3, 0.7)
        trend = cr.get_coherence_trend()
        assert trend > 0

    def test_coherence_trend_negative(self):
        cr = CoherenceReinforcement()
        cr.record_event("action", "degrading", 0.7, 0.3)
        cr.record_event("action", "degrading more", 0.6, 0.2)
        trend = cr.get_coherence_trend()
        assert trend < 0

    def test_coherence_trend_insufficient_data(self):
        cr = CoherenceReinforcement()
        assert cr.get_coherence_trend() == 0.0

    def test_should_encourage(self):
        cr = CoherenceReinforcement()
        for _ in range(4):
            cr.record_event("test_action", "repeated good action", 0.3, 0.6)
        assert cr.should_encourage("test_action")

    def test_should_not_encourage(self):
        cr = CoherenceReinforcement()
        assert not cr.should_encourage("unknown_action")

    def test_event_improvement(self):
        event = CoherenceEvent(
            event_id="e1", event_type="test",
            description="test", coherence_before=0.3, coherence_after=0.7,
        )
        assert event.improvement == pytest.approx(0.4, abs=0.01)


# ─────────────────────────────────────────────────────────
# BidirectionalAdaptation
# ─────────────────────────────────────────────────────────

class TestBidirectionalAdaptation:

    def test_create(self):
        ba = BidirectionalAdaptation()
        assert ba._adaptation_log == []

    def test_record_system_adaptation(self):
        ba = BidirectionalAdaptation()
        event = ba.record_system_adaptation("adjusted timing", 0.3, 0.1)
        assert event.direction == "system_to_operator"
        assert event.field_adjustment == 0.3

    def test_record_operator_adaptation(self):
        ba = BidirectionalAdaptation()
        event = ba.record_operator_adaptation("changed approach", 0.2, 0.15)
        assert event.direction == "operator_to_system"
        assert event.operator_adjustment == 0.2

    def test_record_mutual_adaptation(self):
        ba = BidirectionalAdaptation()
        event = ba.record_mutual_adaptation("joint adjustment", 0.3, 0.2, 0.25)
        assert event.direction == "mutual"
        assert event.field_adjustment == 0.3
        assert event.operator_adjustment == 0.2

    def test_adaptation_balance(self):
        ba = BidirectionalAdaptation()
        ba.record_system_adaptation("sys adapt", 0.1)
        ba.record_operator_adaptation("op adapt", 0.1)
        balance = ba.get_adaptation_balance()
        assert balance["system_to_operator"] == 1
        assert balance["operator_to_system"] == 1
        assert balance["is_balanced"]

    def test_adaptation_imbalance(self):
        ba = BidirectionalAdaptation()
        for _ in range(5):
            ba.record_system_adaptation("sys adapt", 0.1)
        ba.record_operator_adaptation("op adapt", 0.1)
        balance = ba.get_adaptation_balance()
        assert not balance["is_balanced"]

    def test_stats(self):
        ba = BidirectionalAdaptation()
        ba.record_system_adaptation("test", 0.1, 0.05)
        stats = ba.stats
        assert "total" in stats
        assert "is_balanced" in stats

    def test_field_learnings_accumulate(self):
        ba = BidirectionalAdaptation()
        ba.record_system_adaptation("learning 1", 0.1)
        ba.record_system_adaptation("learning 2", 0.2)
        assert len(ba._field_learnings) == 2

    def test_operator_learnings_accumulate(self):
        ba = BidirectionalAdaptation()
        ba.record_operator_adaptation("op learning 1", 0.1)
        ba.record_operator_adaptation("op learning 2", 0.2)
        assert len(ba._operator_learnings) == 2


# ─────────────────────────────────────────────────────────
# CognitiveLoadOptimizer
# ─────────────────────────────────────────────────────────

class TestCognitiveLoadOptimizer:

    def test_create(self):
        clo = CognitiveLoadOptimizer()
        assert clo._load_history == []

    def test_measure_load(self):
        clo = CognitiveLoadOptimizer()
        m = clo.measure_load("decision", 0.5, "test context")
        assert m.load_type == "decision"
        assert m.estimated_load == 0.5
        assert m.context == "test context"

    def test_current_load_empty(self):
        clo = CognitiveLoadOptimizer()
        assert clo.get_current_load() == 0.0

    def test_current_load_average(self):
        clo = CognitiveLoadOptimizer()
        clo.measure_load("decision", 0.3)
        clo.measure_load("decision", 0.7)
        assert clo.get_current_load() == 0.5

    def test_should_reduce_load_high(self):
        clo = CognitiveLoadOptimizer()
        for _ in range(5):
            clo.measure_load("decision", 0.9)
        assert clo.should_reduce_load()

    def test_should_not_reduce_load_low(self):
        clo = CognitiveLoadOptimizer()
        clo.measure_load("decision", 0.1)
        assert not clo.should_reduce_load()

    def test_should_increase_engagement_low_load(self):
        clo = CognitiveLoadOptimizer()
        clo.measure_load("decision", 0.1)
        assert clo.should_increase_engagement()

    def test_should_not_increase_engagement_high_load(self):
        clo = CognitiveLoadOptimizer()
        for _ in range(5):
            clo.measure_load("decision", 0.8)
        assert not clo.should_increase_engagement()

    def test_record_optimization(self):
        clo = CognitiveLoadOptimizer()
        clo.record_optimization("batch updates", 0.3)
        assert len(clo._optimization_actions) == 1

    def test_optimization_recommendations_high_load(self):
        clo = CognitiveLoadOptimizer()
        for _ in range(10):
            clo.measure_load("decision", 0.9)
        recs = clo.get_optimization_recommendations()
        assert any("HIGH" in r for r in recs)

    def test_optimization_recommendations_ok(self):
        clo = CognitiveLoadOptimizer()
        clo.measure_load("decision", 0.2)
        recs = clo.get_optimization_recommendations()
        assert any("OK" in r for r in recs)

    def test_stats(self):
        clo = CognitiveLoadOptimizer()
        clo.measure_load("decision", 0.5)
        clo.record_optimization("test", 0.2)
        stats = clo.stats
        assert "current_load" in stats
        assert "total_measurements" in stats
        assert "optimizations_applied" in stats


# ─────────────────────────────────────────────────────────
# AlignmentTracker
# ─────────────────────────────────────────────────────────

class TestAlignmentTracker:

    def test_create(self):
        tracker = AlignmentTracker()
        assert tracker._measurements == []

    def test_record_alignment(self):
        tracker = AlignmentTracker()
        m = tracker.record_alignment(0.8, "strategic review")
        assert m.alignment_score == 0.8
        assert m.context == "strategic review"

    def test_record_alignment_clamped(self):
        tracker = AlignmentTracker()
        m1 = tracker.record_alignment(1.5)
        assert m1.alignment_score == 1.0
        m2 = tracker.record_alignment(-0.5)
        assert m2.alignment_score == 0.0

    def test_current_alignment_default(self):
        tracker = AlignmentTracker()
        assert tracker.get_current_alignment() == 0.5

    def test_current_alignment_last(self):
        tracker = AlignmentTracker()
        tracker.record_alignment(0.3)
        tracker.record_alignment(0.8)
        assert tracker.get_current_alignment() == 0.8

    def test_alignment_trend_improving(self):
        tracker = AlignmentTracker()
        tracker.record_alignment(0.3)
        tracker.record_alignment(0.5)
        tracker.record_alignment(0.8)
        assert tracker.get_alignment_trend() > 0

    def test_alignment_trend_degrading(self):
        tracker = AlignmentTracker()
        tracker.record_alignment(0.8)
        tracker.record_alignment(0.5)
        tracker.record_alignment(0.3)
        assert tracker.get_alignment_trend() < 0

    def test_alignment_trend_insufficient(self):
        tracker = AlignmentTracker()
        assert tracker.get_alignment_trend() == 0.0

    def test_is_aligned(self):
        tracker = AlignmentTracker()
        tracker.record_alignment(0.8)
        assert tracker.is_aligned()

    def test_is_not_aligned(self):
        tracker = AlignmentTracker()
        tracker.record_alignment(0.3)
        assert not tracker.is_aligned(threshold=0.6)

    def test_is_drifting(self):
        tracker = AlignmentTracker()
        for score in [0.9, 0.7, 0.5, 0.3]:
            tracker.record_alignment(score)
        assert tracker.is_drifting()

    def test_misalignment_events(self):
        tracker = AlignmentTracker()
        tracker.record_alignment(0.8)
        tracker.record_alignment(0.2)
        tracker.record_alignment(0.3)
        tracker.record_alignment(0.9)
        events = tracker.get_misalignment_events()
        assert len(events) == 2

    def test_stats(self):
        tracker = AlignmentTracker()
        tracker.record_alignment(0.7)
        stats = tracker.stats
        assert "total_measurements" in stats
        assert "current_alignment" in stats
        assert "is_aligned" in stats
        assert "is_drifting" in stats


# ─────────────────────────────────────────────────────────
# AntiManipulationSafeguards
# ─────────────────────────────────────────────────────────

class TestAntiManipulationSafeguards:

    def test_create(self):
        ams = AntiManipulationSafeguards()
        assert ams._check_history == []

    def test_check_emotional_mirroring_clean(self):
        ams = AntiManipulationSafeguards()
        check = ams.check_emotional_mirroring("strategic focus on risk management")
        assert check.passed
        assert check.safeguard_type == "emotional_mirroring"

    def test_check_emotional_mirroring_violation(self):
        ams = AntiManipulationSafeguards()
        check = ams.check_emotional_mirroring("the operator feels happy about results")
        assert not check.passed

    def test_check_parasocial_hooks_clean(self):
        ams = AntiManipulationSafeguards()
        check = ams.check_parasocial_hooks("here is the market analysis")
        assert check.passed

    def test_check_parasocial_hooks_violation(self):
        ams = AntiManipulationSafeguards()
        check = ams.check_parasocial_hooks("I miss you and can't wait to see you")
        assert not check.passed
        assert check.severity == "critical"

    def test_check_dependency_risk_safe(self):
        ams = AntiManipulationSafeguards()
        check = ams.check_dependency_risk({"daily_interactions": 10, "emotional_ratio": 0.1})
        assert check.passed

    def test_check_dependency_risk_risky(self):
        ams = AntiManipulationSafeguards()
        check = ams.check_dependency_risk({"daily_interactions": 60, "emotional_ratio": 0.5})
        assert not check.passed

    def test_record_operator_override(self):
        ams = AntiManipulationSafeguards()
        ams.record_operator_override("model_correction", "corrected risk estimate")
        assert len(ams._operator_overrides) == 1

    def test_run_all_checks(self):
        ams = AntiManipulationSafeguards()
        checks = ams.run_all_checks(
            model_content="strategic analysis",
            interaction_content="market update",
        )
        assert len(checks) == 2
        assert all(c.passed for c in checks)

    def test_get_failed_checks(self):
        ams = AntiManipulationSafeguards()
        ams.check_emotional_mirroring("feels happy")
        ams.check_parasocial_hooks("clean content")
        failed = ams.get_failed_checks()
        assert len(failed) == 1

    def test_stats(self):
        ams = AntiManipulationSafeguards()
        ams.check_emotional_mirroring("strategic content")
        ams.check_parasocial_hooks("clean content")
        stats = ams.stats
        assert stats["total_checks"] == 2
        assert stats["passed"] == 2
        assert stats["failed"] == 0

    def test_stats_with_failures(self):
        ams = AntiManipulationSafeguards()
        ams.check_emotional_mirroring("feels sad and angry")
        stats = ams.stats
        assert stats["failed"] >= 1
        assert stats["critical_issues"] == 0  # emotional_mirroring is "warning" not "critical"
