"""
Tests for OCE Alerting Engine — OCE-5.5c
==========================================
15+ tests covering rules, evaluation, alert lifecycle, and stats.
"""

import pytest
import time

@pytest.fixture(autouse=True)
def reset_alerting():
    """Reset the AlertingEngine singleton before each test."""
    from alerting_engine import AlertingEngine
    AlertingEngine._instance = None
    yield
    AlertingEngine._instance = None


class TestBuiltinRules:
    """Tests for built-in alert rules."""

    def test_builtin_rules_loaded(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        rules = engine.get_rules()
        assert len(rules) >= 5  # 5 built-in rules

    def test_builtin_rule_names(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        rules = engine.get_rules()
        names = [r["name"] for r in rules]
        assert "observer_health_critical" in names
        assert "event_queue_overflow" in names
        assert "memory_usage_critical" in names
        assert "entropy_budget_low" in names
        assert "observer_error_rate_high" in names


class TestRuleManagement:
    """Tests for adding and removing rules."""

    def test_add_rule(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        rule_id = engine.add_rule(
            name="test_rule",
            metric="test.metric",
            threshold=50.0,
            comparison="gt",
            severity="warning",
        )
        assert rule_id is not None
        rules = engine.get_rules()
        assert any(r["rule_id"] == rule_id for r in rules)

    def test_add_rule_with_defaults(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        rule_id = engine.add_rule(
            name="simple_rule",
            metric="x.y",
            threshold=1.0,
        )
        rules = engine.get_rules()
        rule = next(r for r in rules if r["rule_id"] == rule_id)
        assert rule["comparison"] == "lt"
        assert rule["severity"] == "warning"
        assert rule["cooldown_sec"] == 300

    def test_remove_rule(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        rule_id = engine.add_rule(
            name="removable", metric="x", threshold=1.0
        )
        assert engine.remove_rule(rule_id) is True
        rules = engine.get_rules()
        assert not any(r["rule_id"] == rule_id for r in rules)

    def test_remove_nonexistent_rule(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        assert engine.remove_rule("nonexistent") is False


class TestEvaluation:
    """Tests for rule evaluation against metrics snapshots."""

    def test_evaluate_triggers_alert(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        # Add a rule that will fire
        engine.add_rule(
            name="test_trigger",
            metric="test.value",
            threshold=10.0,
            comparison="gt",
        )
        metrics = {"test": {"value": 15.0}}
        alerts = engine.evaluate(metrics)
        assert len(alerts) >= 1
        assert any(a.rule_name == "test_trigger" for a in alerts)

    def test_evaluate_no_trigger(self):
        from alerting_engine import get_alerting_engine, AlertingEngine
        AlertingEngine._instance = None
        engine = get_alerting_engine()
        engine.add_rule(
            name="no_trigger",
            metric="test.value",
            threshold=100.0,
            comparison="gt",
        )
        metrics = {"test": {"value": 5.0}}
        alerts = engine.evaluate(metrics)
        assert len(alerts) == 0
        AlertingEngine._instance = None

    def test_evaluate_lt_comparison(self):
        from alerting_engine import get_alerting_engine, AlertingEngine
        AlertingEngine._instance = None
        engine = get_alerting_engine()
        engine.add_rule(
            name="lt_test",
            metric="health.score",
            threshold=0.5,
            comparison="lt",
        )
        metrics = {"health": {"score": 0.3}}
        alerts = engine.evaluate(metrics)
        assert len(alerts) >= 1
        AlertingEngine._instance = None

    def test_evaluate_missing_metric(self):
        from alerting_engine import get_alerting_engine, AlertingEngine
        AlertingEngine._instance = None
        engine = get_alerting_engine()
        engine.add_rule(
            name="missing_metric",
            metric="nonexistent.path",
            threshold=1.0,
        )
        metrics = {"other": "data"}
        alerts = engine.evaluate(metrics)
        assert len(alerts) == 0
        AlertingEngine._instance = None

    def test_evaluate_nested_metric(self):
        from alerting_engine import get_alerting_engine, AlertingEngine
        AlertingEngine._instance = None
        engine = get_alerting_engine()
        engine.add_rule(
            name="nested_test",
            metric="observers.avg_health",
            threshold=0.5,
            comparison="lt",
        )
        metrics = {"observers": {"avg_health": 0.3}}
        alerts = engine.evaluate(metrics)
        assert len(alerts) >= 1
        AlertingEngine._instance = None


class TestAlertLifecycle:
    """Tests for alert acknowledge and clear."""

    def test_acknowledge_alert(self):
        from alerting_engine import get_alerting_engine, AlertingEngine
        AlertingEngine._instance = None
        engine = get_alerting_engine()
        engine.add_rule(
            name="ack_test",
            metric="x",
            threshold=1.0,
            comparison="gt",
            cooldown_sec=0,
        )
        metrics = {"x": 5.0}
        alerts = engine.evaluate(metrics)
        assert len(alerts) >= 1
        alert_id = alerts[0].alert_id
        assert engine.acknowledge_alert(alert_id) is True
        active = engine.get_active_alerts()
        acked = next(a for a in active if a["alert_id"] == alert_id)
        assert acked["state"] == "acknowledged"
        AlertingEngine._instance = None

    def test_clear_alert(self):
        from alerting_engine import get_alerting_engine, AlertingEngine
        AlertingEngine._instance = None
        engine = get_alerting_engine()
        engine.add_rule(
            name="clear_test",
            metric="x",
            threshold=1.0,
            comparison="gt",
            cooldown_sec=0,
        )
        metrics = {"x": 5.0}
        alerts = engine.evaluate(metrics)
        alert_id = alerts[0].alert_id
        assert engine.clear_alert(alert_id) is True
        active = engine.get_active_alerts()
        assert not any(a["alert_id"] == alert_id for a in active)
        history = engine.get_alert_history()
        assert any(a["alert_id"] == alert_id for a in history)
        AlertingEngine._instance = None

    def test_acknowledge_nonexistent(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        assert engine.acknowledge_alert("nonexistent") is False

    def test_clear_nonexistent(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        assert engine.clear_alert("nonexistent") is False


class TestAlertStats:
    """Tests for alerting statistics."""

    def test_stats_structure(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        stats = engine.get_stats()
        assert "active_firing" in stats
        assert "active_acknowledged" in stats
        assert "total_active" in stats
        assert "total_history" in stats
        assert "rules_count" in stats
        assert "by_severity" in stats

    def test_stats_counts(self):
        from alerting_engine import get_alerting_engine
        engine = get_alerting_engine()
        stats = engine.get_stats()
        assert stats["rules_count"] >= 5  # built-in rules


class TestCooldown:
    """Tests for alert cooldown behavior."""

    def test_cooldown_prevents_refire(self):
        from alerting_engine import get_alerting_engine, AlertingEngine
        AlertingEngine._instance = None
        engine = get_alerting_engine()
        engine.add_rule(
            name="cooldown_test",
            metric="x",
            threshold=1.0,
            comparison="gt",
            cooldown_sec=60,
        )
        metrics = {"x": 5.0}
        alerts1 = engine.evaluate(metrics)
        alerts2 = engine.evaluate(metrics)
        # Second evaluation should not fire due to cooldown
        new_in_second = [a for a in alerts2 if a.rule_name == "cooldown_test"]
        assert len(new_in_second) == 0
        AlertingEngine._instance = None


class TestComparisonHelper:
    """Tests for the _compare helper function."""

    def test_lt(self):
        from alerting_engine import _compare
        assert _compare(3.0, 5.0, "lt") is True
        assert _compare(5.0, 3.0, "lt") is False

    def test_gt(self):
        from alerting_engine import _compare
        assert _compare(5.0, 3.0, "gt") is True
        assert _compare(3.0, 5.0, "gt") is False

    def test_lte(self):
        from alerting_engine import _compare
        assert _compare(3.0, 5.0, "lte") is True
        assert _compare(5.0, 5.0, "lte") is True
        assert _compare(6.0, 5.0, "lte") is False

    def test_gte(self):
        from alerting_engine import _compare
        assert _compare(5.0, 3.0, "gte") is True
        assert _compare(5.0, 5.0, "gte") is True
        assert _compare(3.0, 5.0, "gte") is False

    def test_eq(self):
        from alerting_engine import _compare
        assert _compare(5.0, 5.0, "eq") is True
        assert _compare(3.0, 5.0, "eq") is False


class TestGetNested:
    """Tests for the _get_nested helper function."""

    def test_simple_path(self):
        from alerting_engine import _get_nested
        data = {"a": {"b": 42}}
        assert _get_nested(data, "a.b") == 42

    def test_missing_path(self):
        from alerting_engine import _get_nested
        data = {"a": {"b": 42}}
        assert _get_nested(data, "a.c") is None

    def test_deep_path(self):
        from alerting_engine import _get_nested
        data = {"a": {"b": {"c": {"d": 99}}}}
        assert _get_nested(data, "a.b.c.d") == 99

    def test_non_dict_intermediate(self):
        from alerting_engine import _get_nested
        data = {"a": "string"}
        assert _get_nested(data, "a.b") is None


class TestSingleton:
    """Tests for singleton behavior."""

    def test_singleton_identity(self):
        from alerting_engine import get_alerting_engine
        e1 = get_alerting_engine()
        e2 = get_alerting_engine()
        assert e1 is e2
