"""C2.S4 incident view: severity, impact, containment, owners, timeline, recovery, risk.

Read-only projection over caller-supplied governed records. Deterministic, no wall clock, no
network. A recovered incident that still carries unresolved risk without recorded containment is
refused rather than shown as resolved.
"""
from __future__ import annotations

from .model import OperatorRefusal, object_digest

SEVERITIES = ("SEV1", "SEV2", "SEV3", "SEV4")
RANK = {name: index for index, name in enumerate(SEVERITIES)}
RECOVERIES = ("ACTIVE", "CONTAINED", "RECOVERED")
FIELDS = ("id", "severity", "impact", "containment", "owners", "timeline", "recovery",
          "unresolved_risk")


def _validate_timeline(timeline, incident_id) -> list:
    if not isinstance(timeline, list) or not timeline:
        raise OperatorRefusal("REFUSED_BROKEN_TIMELINE", incident_id)
    rows = []
    previous = None
    for entry in timeline:
        if "at" not in entry or "event" not in entry:
            raise OperatorRefusal("REFUSED_INVALID_RECORD", "timeline entry")
        at = int(entry["at"])
        if previous is not None and at < previous:
            raise OperatorRefusal("REFUSED_BROKEN_TIMELINE", incident_id)
        previous = at
        rows.append({"at": at, "event": entry["event"]})
    return rows


def incident_view(incidents, viewer):
    """Project incident records for one viewer, sorted by severity then id."""
    subject = (viewer or {}).get("subject")
    if not subject:
        raise OperatorRefusal("REFUSED_UNKNOWN_SUBJECT", "viewer subject missing")
    rows = []
    for incident in incidents:
        for key in FIELDS:
            if key not in incident:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", key)
        if incident["severity"] not in RANK:
            raise OperatorRefusal("REFUSED_INVALID_SEVERITY", incident["severity"])
        if incident["recovery"] not in RECOVERIES:
            raise OperatorRefusal("REFUSED_INVALID_RECORD", incident["recovery"])
        owners = list(incident["owners"])
        if not owners:
            raise OperatorRefusal("REFUSED_INVALID_RECORD", "owners")
        containment = []
        for action in incident["containment"]:
            if "action" not in action or "owner" not in action or "at" not in action:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", "containment entry")
            containment.append({"action": action["action"], "owner": action["owner"],
                                "at": int(action["at"])})
        timeline = _validate_timeline(incident["timeline"], incident["id"])
        unresolved = list(incident["unresolved_risk"])
        if incident["recovery"] == "RECOVERED" and unresolved and not containment:
            raise OperatorRefusal("REFUSED_UNRESOLVED_RISK", incident["id"])
        rows.append({
            "id": incident["id"],
            "severity": incident["severity"],
            "impact": incident["impact"],
            "containment": containment,
            "owners": owners,
            "timeline": timeline,
            "recovery": incident["recovery"],
            "unresolved_risk": unresolved,
            "resolved": incident["recovery"] == "RECOVERED" and not unresolved,
        })
    rows.sort(key=lambda row: (RANK[row["severity"]], row["id"]))
    doc = {
        "schema": "oce.operator.incident_view.v1",
        "viewer": subject,
        "rows": rows,
        "totals": {
            "rows": len(rows),
            "active": sum(1 for row in rows if row["recovery"] == "ACTIVE"),
            "unresolved": sum(1 for row in rows if row["unresolved_risk"]),
        },
    }
    doc["digest"] = object_digest(doc)
    return doc


def assess_drill(drill, latency_limit):
    """Judge whether a failure drill became legible within a defined detection latency."""
    for key in ("id", "detected_at", "visible_at"):
        if key not in drill:
            raise OperatorRefusal("REFUSED_INVALID_RECORD", key)
    detected = int(drill["detected_at"])
    visible = int(drill["visible_at"])
    if visible < detected:
        raise OperatorRefusal("REFUSED_BROKEN_TIMELINE", drill["id"])
    latency = visible - detected
    doc = {
        "schema": "oce.operator.drill_assessment.v1",
        "id": drill["id"],
        "latency": latency,
        "limit": int(latency_limit),
        "status": "LEGIBLE" if latency <= int(latency_limit) else "BREACHED",
    }
    doc["digest"] = object_digest(doc)
    return doc
