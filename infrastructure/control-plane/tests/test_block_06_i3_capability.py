"""B6-I3 C2.S1 capability truth: evidence, ceilings and simulation refusals."""
from __future__ import annotations

import pytest

from oce.operator import OperatorRefusal, capability_view

VIEWER = {"subject": "operator:mad", "grants": {"cap.api.invoke": "admin", "cap.other": "read"}}
EVIDENCE = {"e1": {"sha256": "aa"}}


def record(**overrides):
    row = {
        "id": "cap.api.invoke",
        "subject": "agent:builder",
        "version": "1.0.0",
        "kind": "capability",
        "proven": True,
        "ceiling": "execute",
        "status": "ACTIVE",
        "evidence_sha256": "e1",
    }
    row.update(overrides)
    return row


def test_proven_requires_evidence():
    with pytest.raises(OperatorRefusal) as exc:
        capability_view([record(evidence_sha256="absent")], VIEWER, EVIDENCE)
    assert exc.value.code == "REFUSED_EVIDENCE_MISSING"


def test_simulated_proof_refused():
    with pytest.raises(OperatorRefusal) as exc:
        capability_view([record(kind="simulation")], VIEWER, EVIDENCE)
    assert exc.value.code == "REFUSED_SIMULATED_PROOF"


def test_unproven_active_refused():
    with pytest.raises(OperatorRefusal) as exc:
        capability_view([record(proven=False, status="ACTIVE")], VIEWER, EVIDENCE)
    assert exc.value.code == "REFUSED_UNPROVEN_ACTIVE"


def test_ceiling_intersection():
    view = capability_view([record(ceiling="execute")],
                           {"subject": "operator:mad", "grants": {"cap.api.invoke": "read"}},
                           EVIDENCE)
    assert view["rows"][0]["ceiling"] == "read"
    assert view["rows"][0]["operational_proof"] is True


def test_unknown_subject_refused():
    with pytest.raises(OperatorRefusal) as exc:
        capability_view([record()], {}, EVIDENCE)
    assert exc.value.code == "REFUSED_UNKNOWN_SUBJECT"


def test_deterministic_view():
    first = capability_view([record(), record(id="cap.other")], VIEWER, EVIDENCE)
    second = capability_view([record(id="cap.other"), record()], VIEWER, EVIDENCE)
    assert first["digest"] == second["digest"]
    assert [row["id"] for row in first["rows"]] == ["cap.api.invoke", "cap.other"]


def test_status_vocabulary():
    with pytest.raises(OperatorRefusal) as exc:
        capability_view([record(status="OPERATIONAL")], VIEWER, EVIDENCE)
    assert exc.value.code == "REFUSED_INVALID_STATUS"
    view = capability_view([record(status="SUSPENDED")], VIEWER, EVIDENCE)
    assert view["rows"][0]["status"] == "SUSPENDED"
