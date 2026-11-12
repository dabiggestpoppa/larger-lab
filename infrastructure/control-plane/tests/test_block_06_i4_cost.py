"""B6-I4 C2.S5 cost/capacity ledger and budget alerts."""
from __future__ import annotations

import pytest

from oce.operator.cost import budget_alerts, cost_ledger
from oce.operator.model import OperatorRefusal


def entry(**overrides):
    row = {"id": "C1", "app": "app-a", "task": "task-1", "category": "ci",
           "estimate_usd": 10, "actual_usd": 8, "capacity": 20}
    row.update(overrides)
    return row


def test_cost_ledger_separates_estimate_and_actual():
    doc = cost_ledger([entry()])
    task = doc["apps"]["app-a"]["tasks"]["task-1"]
    assert task["estimate_usd"] == 10 and task["actual_usd"] == 8
    assert doc["totals"] == {"apps": 1, "estimate_usd": 10, "actual_usd": 8}
    assert doc["digest"]


def test_unknown_category_refused():
    with pytest.raises(OperatorRefusal) as exc:
        cost_ledger([entry(category="electricity")])
    assert exc.value.code == "REFUSED_UNKNOWN_CATEGORY"


def test_negative_cost_refused():
    with pytest.raises(OperatorRefusal) as exc:
        cost_ledger([entry(estimate_usd=-1)])
    assert exc.value.code == "REFUSED_INVALID_COST"


def test_budget_alert_before_excess():
    ledger = cost_ledger([entry(estimate_usd=10, actual_usd=8)])
    doc = budget_alerts(ledger, {"app-a": {"ci": 12}}, {"app-a": {"ci": 13}})
    row = doc["rows"][0]
    assert row["actual_usd"] == 8 and row["state"] == "ALERT"
    assert doc["totals"]["alert"] == 1


def test_budget_breach_reported():
    ledger = cost_ledger([entry(actual_usd=12)])
    doc = budget_alerts(ledger, {"app-a": {"ci": 12}})
    assert doc["rows"][0]["state"] == "BREACHED"
    assert doc["totals"]["breached"] == 1


def test_cost_attributed_to_app_and_task():
    ledger = cost_ledger([entry(), entry(id="C2", task="task-2", category="model", actual_usd=5)])
    app = ledger["apps"]["app-a"]
    assert app["actual_usd"] == 13
    assert app["tasks"]["task-1"]["actual_usd"] == 8
    assert app["tasks"]["task-2"]["categories"]["model"]["actual_usd"] == 5


def test_fractional_cost_refused():
    for value in (0.9, 0.0, 1.0):
        with pytest.raises(OperatorRefusal) as exc:
            cost_ledger([entry(estimate_usd=value)])
        assert exc.value.code == "REFUSED_INVALID_COST"
        with pytest.raises(OperatorRefusal) as exc:
            cost_ledger([entry(actual_usd=value)])
        assert exc.value.code == "REFUSED_INVALID_COST"


def test_non_integer_cost_refused():
    for value in (True, "5", float("inf"), float("nan"), None):
        with pytest.raises(OperatorRefusal) as exc:
            cost_ledger([entry(capacity=value)])
        assert exc.value.code == "REFUSED_INVALID_COST"
    ledger = cost_ledger([entry()])
    with pytest.raises(OperatorRefusal) as exc:
        budget_alerts(ledger, {"app-a": {"ci": "12"}})
    assert exc.value.code == "REFUSED_INVALID_COST"
    with pytest.raises(OperatorRefusal) as exc:
        budget_alerts(ledger, {"app-a": {"ci": 12}}, {"app-a": {"ci": 0.5}})
    assert exc.value.code == "REFUSED_INVALID_COST"
