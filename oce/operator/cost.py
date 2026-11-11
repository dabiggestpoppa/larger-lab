"""C2.S5 cost/capacity ledger: attribute provider/model/worker/storage/CI cost to task and app.

Estimate and actual are kept strictly separate, and a budget or capacity ceiling is reported as an
alert before excess where a projection is available. Deterministic and offline; every value is an
explicit integer supplied by the caller.
"""
from __future__ import annotations

from .model import OperatorRefusal, object_digest

CATEGORIES = ("provider", "model", "worker", "storage", "ci")
ENTRY_FIELDS = ("id", "app", "task", "category", "estimate_usd", "actual_usd", "capacity")


def _non_negative(value, label):
    value = int(value)
    if value < 0:
        raise OperatorRefusal("REFUSED_INVALID_COST", label)
    return value


def cost_ledger(entries):
    """Attribute cost and capacity to app, then task, then category, separating estimate/actual."""
    apps: dict[str, dict] = {}
    for entry in entries:
        for key in ENTRY_FIELDS:
            if key not in entry:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", key)
        if entry["category"] not in CATEGORIES:
            raise OperatorRefusal("REFUSED_UNKNOWN_CATEGORY", entry["category"])
        estimate = _non_negative(entry["estimate_usd"], entry["id"])
        actual = _non_negative(entry["actual_usd"], entry["id"])
        capacity = _non_negative(entry["capacity"], entry["id"])
        app = apps.setdefault(entry["app"], {"estimate_usd": 0, "actual_usd": 0,
                                             "capacity": 0, "tasks": {}})
        task = app["tasks"].setdefault(entry["task"], {"estimate_usd": 0, "actual_usd": 0,
                                                       "capacity": 0, "categories": {}})
        for bucket in (app, task):
            bucket["estimate_usd"] += estimate
            bucket["actual_usd"] += actual
            bucket["capacity"] += capacity
        category = task["categories"].setdefault(entry["category"],
                                                 {"estimate_usd": 0, "actual_usd": 0,
                                                  "capacity": 0})
        category["estimate_usd"] += estimate
        category["actual_usd"] += actual
        category["capacity"] += capacity
    total_estimate = sum(app["estimate_usd"] for app in apps.values())
    total_actual = sum(app["actual_usd"] for app in apps.values())
    doc = {
        "schema": "oce.operator.cost_ledger.v1",
        "apps": apps,
        "totals": {"apps": len(apps), "estimate_usd": total_estimate,
                   "actual_usd": total_actual},
    }
    doc["digest"] = object_digest(doc)
    return doc


def budget_alerts(ledger, budgets, projections=None):
    """Report OK / ALERT / BREACHED per app and category, before excess where projected.

    ``budgets`` maps app to category to an integer ceiling. A category whose projected spend meets
    or exceeds the ceiling raises ``ALERT`` even when actual spend is still below it; an actual
    spend at or above the ceiling raises ``BREACHED``.
    """
    projections = projections or {}
    rows = []
    for app, app_budget in budgets.items():
        app_data = ledger["apps"].get(app)
        if app_data is None:
            raise OperatorRefusal("REFUSED_INVALID_RECORD", f"unknown app {app}")
        for category, ceiling in app_budget.items():
            if category not in CATEGORIES:
                raise OperatorRefusal("REFUSED_UNKNOWN_CATEGORY", category)
            actual = 0
            for task in app_data["tasks"].values():
                actual += task["categories"].get(category, {}).get("actual_usd", 0)
            projected = int(projections.get(app, {}).get(category, 0))
            ceiling = int(ceiling)
            if actual >= ceiling:
                state = "BREACHED"
            elif projected >= ceiling:
                state = "ALERT"
            else:
                state = "OK"
            rows.append({"app": app, "category": category, "ceiling": ceiling,
                         "actual_usd": actual, "projected_usd": projected, "state": state})
    rows.sort(key=lambda row: (row["app"], row["category"]))
    doc = {"schema": "oce.operator.budget_alerts.v1", "rows": rows,
           "totals": {"rows": len(rows),
                      "alert": sum(1 for row in rows if row["state"] == "ALERT"),
                      "breached": sum(1 for row in rows if row["state"] == "BREACHED")}}
    doc["digest"] = object_digest(doc)
    return doc
