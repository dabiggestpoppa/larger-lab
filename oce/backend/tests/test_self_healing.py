"""
Tests for OCE Self-Healing Engine — OCE-7.4b
==============================================
15+ tests covering failure analysis, recommendations, healing actions,
and healing history.
"""

import os
import sys
import pytest
import time

# Ensure we import from the OCE backend, not SRRA-OPH
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)


@pytest.fixture(autouse=True)
def reset_healing():
    """Reset the SelfHealingEngine singleton before each test."""
    from self_healing_engine import SelfHealingEngine
    SelfHealingEngine._instance = None
    yield
    SelfHealingEngine._instance = None


class TestHealingEngineInit:
    """Tests for SelfHealingEngine initialization."""

    def test_singleton_identity(self):
        from self_healing_engine import get_self_healing_engine
        h1 = get_self_healing_engine()
        h2 = get_self_healing_engine()
        assert h1 is h2

    def test_builtin_handlers_registered(self):
        from self_healing_engine import get_self_healing_engine, HealingActionType
        h = get_self_healing_engine()
        assert HealingActionType.SCALE_WORKERS_UP in h._action_handlers
        assert HealingActionType.INCREASE_TIMEOUT in h._action_handlers
        assert HealingActionType.INCREASE_RETRIES in h._action_handlers


class TestFailureAnalysis:
    """Tests for failure pattern analysis."""

    def test_no_data(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        patterns = h.analyze_failures()
        assert patterns == []

    def test_returns_list(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        result = h.analyze_failures(time_range_hours=1)
        assert isinstance(result, list)


class TestRecommendations:
    """Tests for healing recommendation generation."""

    def test_no_patterns(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        recs = h.generate_recommendations([])
        assert recs == []

    def test_critical_pattern_generates_recommendations(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        patterns = [{"task_type": "skill_call", "fail_count": 25, "severity": "critical"}]
        recs = h.generate_recommendations(patterns)
        assert len(recs) > 0

    def test_low_severity_no_recommendations(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        patterns = [{"task_type": "skill_call", "fail_count": 1, "severity": "low"}]
        recs = h.generate_recommendations(patterns)
        assert len(recs) == 0

    def test_recommendation_has_action_type(self):
        from self_healing_engine import get_self_healing_engine, HealingActionType
        h = get_self_healing_engine()
        patterns = [{"task_type": "skill_call", "fail_count": 15, "severity": "high"}]
        recs = h.generate_recommendations(patterns)
        for r in recs:
            assert isinstance(r.action_type, HealingActionType)


class TestHealingActions:
    """Tests for applying healing actions."""

    def test_apply_scale_up(self):
        from self_healing_engine import get_self_healing_engine, HealingAction, HealingActionType
        h = get_self_healing_engine()
        action = HealingAction(
            action_type=HealingActionType.SCALE_WORKERS_UP,
            target="worker_pool",
            reason="Test",
            params={"delta": 2},
        )
        result = h.apply_healing_action(action)
        assert result is True
        assert action.applied is True

    def test_apply_increase_timeout(self):
        from self_healing_engine import get_self_healing_engine, HealingAction, HealingActionType
        h = get_self_healing_engine()
        action = HealingAction(
            action_type=HealingActionType.INCREASE_TIMEOUT,
            target="skill_call",
            reason="Test",
            params={"task_type": "skill_call", "timeout_multiplier": 2.0},
        )
        result = h.apply_healing_action(action)
        assert result is True

    def test_apply_increase_retries(self):
        from self_healing_engine import get_self_healing_engine, HealingAction, HealingActionType
        h = get_self_healing_engine()
        action = HealingAction(
            action_type=HealingActionType.INCREASE_RETRIES,
            target="skill_call",
            reason="Test",
            params={"task_type": "skill_call", "new_max_retries": 5},
        )
        result = h.apply_healing_action(action)
        assert result is True

    def test_apply_no_handler(self):
        from self_healing_engine import get_self_healing_engine, HealingAction, HealingActionType
        h = get_self_healing_engine()
        action = HealingAction(
            action_type=HealingActionType.RESET_HANDLER,
            target="unknown",
            reason="Test",
        )
        result = h.apply_healing_action(action)
        assert result is False  # No handler registered

    def test_action_recorded_in_history(self):
        from self_healing_engine import get_self_healing_engine, HealingAction, HealingActionType
        h = get_self_healing_engine()
        action = HealingAction(
            action_type=HealingActionType.SCALE_WORKERS_UP,
            target="worker_pool",
            reason="Test",
        )
        h.apply_healing_action(action)
        history = h.get_healing_history()
        assert len(history) >= 1


class TestHealingStats:
    """Tests for healing statistics."""

    def test_initial_stats(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        stats = h.get_stats()
        assert stats["total_actions"] == 0
        assert stats["applied"] == 0

    def test_stats_after_action(self):
        from self_healing_engine import get_self_healing_engine, HealingAction, HealingActionType
        h = get_self_healing_engine()
        action = HealingAction(
            action_type=HealingActionType.SCALE_WORKERS_UP,
            target="worker_pool",
            reason="Test",
        )
        h.apply_healing_action(action)
        stats = h.get_stats()
        assert stats["total_actions"] >= 1
        assert stats["applied"] >= 1

    def test_stats_structure(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        stats = h.get_stats()
        assert "total_actions" in stats
        assert "applied" in stats
        assert "failed" in stats
        assert "by_type" in stats
        assert "cooldown_sec" in stats


class TestAutoHeal:
    """Tests for auto-heal functionality."""

    def test_auto_heal_no_drift(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        actions = h.auto_heal()
        assert isinstance(actions, list)

    def test_auto_heal_with_drift_report(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        drift_report = {
            "healthy": False,
            "overall_level": "high",
            "drifts": [
                {
                    "metric": "queue_depth",
                    "task_type": "all",
                    "current_value": 100,
                    "baseline_value": 50,
                    "change_pct": 100.0,
                }
            ],
        }
        actions = h.auto_heal(drift_report)
        assert isinstance(actions, list)

    def test_auto_heal_healthy_report(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        drift_report = {"healthy": True, "overall_level": "none", "drifts": []}
        actions = h.auto_heal(drift_report)
        assert isinstance(actions, list)


class TestCooldown:
    """Tests for healing cooldown."""

    def test_cooldown_prevents_duplicate(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        assert h._check_cooldown("test_issue") is True
        h._last_healed["test_issue"] = time.time()
        assert h._check_cooldown("test_issue") is False

    def test_cooldown_expires(self):
        from self_healing_engine import get_self_healing_engine
        h = get_self_healing_engine()
        h._last_healed["test_issue"] = time.time() - 400  # Beyond cooldown
        assert h._check_cooldown("test_issue") is True


class TestCustomHandler:
    """Tests for custom action handler registration."""

    def test_register_custom_handler(self):
        from self_healing_engine import get_self_healing_engine, HealingActionType, HealingAction
        h = get_self_healing_engine()
        custom_called = []

        def custom_handler(params):
            custom_called.append(params)
            return "custom result"

        h.register_action_handler(HealingActionType.RESET_HANDLER, custom_handler)
        action = HealingAction(
            action_type=HealingActionType.RESET_HANDLER,
            target="test",
            reason="Test",
        )
        result = h.apply_healing_action(action)
        assert result is True
        assert len(custom_called) == 1
