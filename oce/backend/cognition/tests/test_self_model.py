"""Tests for Self-Model Engine."""

import pytest
from oce.backend.cognition.self_model import SelfModelEngine, SelfObservation


class TestSelfObservation:
    def test_creation(self):
        o = SelfObservation(observation_id="o1", observation_type="failure", description="test")
        assert o.resolved is False


class TestSelfModelEngine:
    def test_creation(self):
        model = SelfModelEngine()
        assert model is not None

    def test_observe_failure(self):
        model = SelfModelEngine()
        obs = model.observe_failure("test_fail", "Something went wrong", severity=0.7)
        assert obs.observation_type == "failure"
        assert obs.severity == 0.7

    def test_observe_drift(self):
        model = SelfModelEngine()
        obs = model.observe_drift(0.5, "Field coherence dropping")
        assert obs.observation_type == "drift"

    def test_observe_inefficiency(self):
        model = SelfModelEngine()
        obs = model.observe_inefficiency("token_waste", 0.05, "Redundant API call")
        assert obs.observation_type == "inefficiency"

    def test_resolve_observation(self):
        model = SelfModelEngine()
        obs = model.observe_failure("test", "test")
        assert model.resolve_observation(obs.observation_id, "Fixed") is True
        assert obs.resolved is True

    def test_get_unresolved(self):
        model = SelfModelEngine()
        model.observe_failure("f1", "fail 1")
        model.observe_failure("f2", "fail 2")
        unresolved = model.get_unresolved()
        assert len(unresolved) == 2

    def test_get_recurring_failures(self):
        model = SelfModelEngine()
        for _ in range(3):
            model.observe_failure("recurring", "Same issue")
        recurring = model.get_recurring_failures(min_count=2)
        assert len(recurring) >= 1

    def test_self_assessment(self):
        model = SelfModelEngine()
        model.observe_failure("f1", "fail")
        assessment = model.get_self_assessment()
        assert "health" in assessment
        assert 0.0 <= assessment["health"] <= 1.0

    def test_stats(self):
        model = SelfModelEngine()
        model.observe_failure("f1", "fail")
        stats = model.stats
        assert stats["total_observations"] == 1
        assert stats["unresolved"] == 1
