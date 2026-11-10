"""B6-I3 C2.S2 approval authority: self, replay, stale, target, scope and cost refusals."""
from __future__ import annotations

import pytest

from oce.operator import OperatorRefusal, canonical, decide, digest

APPROVER = {"subject": "operator:mad", "grants": {"deploy.app": "execute"}, "cost_ceiling_usd": 100}
EVIDENCE = {"e1": {"sha256": "aa"}}


def request(**overrides):
    row = {
        "request_id": "req-1",
        "requester": "agent:builder",
        "action": "deploy.app",
        "target": "app",
        "target_sha256": "t1",
        "effect": {"replicas": 2},
        "cost_usd": 10,
        "reversibility": "reversible",
        "expires_at": 100,
        "evidence_sha256": "e1",
        "nonce": "n1",
        "required_ceiling": "execute",
    }
    row.update(overrides)
    return row


def test_self_approval_refused():
    with pytest.raises(OperatorRefusal) as exc:
        decide(request(), dict(APPROVER, subject="agent:builder"), "APPROVE", 50, set(), EVIDENCE,
               "t1")
    assert exc.value.code == "REFUSED_SELF_APPROVAL"


def test_replay_refused():
    with pytest.raises(OperatorRefusal) as exc:
        decide(request(), APPROVER, "APPROVE", 50, {"n1"}, EVIDENCE, "t1")
    assert exc.value.code == "REFUSED_REPLAY"


def test_stale_refused():
    with pytest.raises(OperatorRefusal) as exc:
        decide(request(), APPROVER, "APPROVE", 100, set(), EVIDENCE, "t1")
    assert exc.value.code == "REFUSED_STALE"


def test_wrong_target_refused():
    with pytest.raises(OperatorRefusal) as exc:
        decide(request(), APPROVER, "APPROVE", 50, set(), EVIDENCE, "t2")
    assert exc.value.code == "REFUSED_WRONG_TARGET"


def test_out_of_scope_refused():
    with pytest.raises(OperatorRefusal) as exc:
        decide(request(), dict(APPROVER, grants={}), "APPROVE", 50, set(), EVIDENCE, "t1")
    assert exc.value.code == "REFUSED_OUT_OF_SCOPE"


def test_cost_ceiling_refused():
    with pytest.raises(OperatorRefusal) as exc:
        decide(request(cost_usd=101), APPROVER, "APPROVE", 50, set(), EVIDENCE, "t1")
    assert exc.value.code == "REFUSED_COST_CEILING"


def test_deny_recorded():
    consumed = set()
    record = decide(request(), APPROVER, "DENY", 50, consumed, EVIDENCE, "t1")
    assert record["decision"] == "DENIED"
    assert consumed == {"n1"}
    assert record["decision_id"]


def test_approval_binds_effect_and_evidence():
    record = decide(request(), APPROVER, "APPROVE", 50, set(), EVIDENCE, "t1")
    assert record["effect_sha256"] == digest(canonical({"replicas": 2}))
    assert record["target_sha256"] == "t1"
    assert record["evidence_sha256"] == "e1"
    assert record["cost_usd"] == 10 and record["reversibility"] == "reversible"
    assert record["decision"] == "APPROVED"
