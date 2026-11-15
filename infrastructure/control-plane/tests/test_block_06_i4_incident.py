"""B6-I4 C2.S4 incident view and drill legibility."""
from __future__ import annotations

import pytest

from oce.operator.incident import assess_drill, incident_view
from oce.operator.model import OperatorRefusal

VIEWER = {"subject": "operator:mad"}


def incident(**overrides):
    row = {
        "id": "INC-1",
        "severity": "SEV2",
        "impact": {"scope": "app", "systems": ["kernel"]},
        "containment": [{"action": "rollback", "owner": "id:oncall", "at": 20}],
        "owners": ["id:oncall"],
        "timeline": [{"at": 10, "event": "detected"}, {"at": 20, "event": "contained"}],
        "recovery": "RECOVERED",
        "unresolved_risk": [],
    }
    row.update(overrides)
    return row


def test_incident_view_projects_fields():
    doc = incident_view([incident()], VIEWER)
    row = doc["rows"][0]
    assert row["severity"] == "SEV2" and row["recovery"] == "RECOVERED"
    assert row["containment"][0]["owner"] == "id:oncall"
    assert row["resolved"] is True and doc["digest"]
    assert "resolved" in row and "unresolved_risk" in row


def test_unknown_subject_refused():
    with pytest.raises(OperatorRefusal) as exc:
        incident_view([incident()], {})
    assert exc.value.code == "REFUSED_UNKNOWN_SUBJECT"


def test_invalid_severity_refused():
    with pytest.raises(OperatorRefusal) as exc:
        incident_view([incident(severity="SEV9")], VIEWER)
    assert exc.value.code == "REFUSED_INVALID_SEVERITY"


def test_timeline_must_be_monotonic():
    with pytest.raises(OperatorRefusal) as exc:
        incident_view([incident(timeline=[{"at": 20, "event": "a"}, {"at": 10, "event": "b"}])],
                      VIEWER)
    assert exc.value.code == "REFUSED_BROKEN_TIMELINE"


def test_unresolved_risk_requires_containment():
    with pytest.raises(OperatorRefusal) as exc:
        incident_view([incident(containment=[], unresolved_risk=["risk-1"])], VIEWER)
    assert exc.value.code == "REFUSED_UNRESOLVED_RISK"
    doc = incident_view([incident(unresolved_risk=["risk-1"])], VIEWER)
    assert doc["rows"][0]["resolved"] is False


def test_drill_legibility_latency():
    assert assess_drill({"id": "D1", "detected_at": 10, "visible_at": 16}, 6)["status"] == "LEGIBLE"
    assert assess_drill({"id": "D1", "detected_at": 10, "visible_at": 17}, 6)["status"] == "BREACHED"
    with pytest.raises(OperatorRefusal) as exc:
        assess_drill({"id": "D1", "detected_at": 10, "visible_at": 9}, 6)
    assert exc.value.code == "REFUSED_BROKEN_TIMELINE"
