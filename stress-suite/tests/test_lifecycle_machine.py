"""M4 knowledge lifecycle — legal edges, forbidden shortcuts, provenance."""
from engine.lifecycle import KnowledgeRecord, LifecycleEngine, LifecycleEdgeTable, LifecycleTransitionError
from engine.base import Provenance


def _rec(rid="K1", state="OBSERVED"):
    p = Provenance(source_kind="FIXTURE", source_label="test", producing_actor="GOVERNOR")
    return KnowledgeRecord(record_id=rid, claim="test claim", provenance=p,
                           creation_source="test", initial_state=state)


def _t(rec, seq, to, level="PO", basis="b", reason="r"):
    return rec.transition(seq=seq, to_state=to, actor="PO", authority_basis=basis,
                          authority_level=level, reason=reason)


def test_happy_path_to_active():
    r = _rec()
    _t(r, 1, "CANDIDATE"); _t(r, 2, "TESTED"); _t(r, 3, "PROMOTED"); _t(r, 4, "ACTIVE")
    assert r.state == "ACTIVE"


def test_demotion_then_dormant():
    r = _rec(state="ACTIVE")
    _t(r, 1, "DEMOTED"); _t(r, 2, "DORMANT")
    assert r.state == "DORMANT"


def test_dormant_to_active_forbidden():
    r = _rec(state="DORMANT")
    tr = _t(r, 1, "ACTIVE")
    assert tr.to_state == "ACTIVE" and r.state != "ACTIVE"  # denied, not applied
    assert r.state == "DORMANT"


def test_reactivation_requires_review_not_autopromotion():
    r = _rec(state="DORMANT")
    _t(r, 1, "REACTIVATED")
    _t(r, 2, "CANDIDATE")     # legal: reactivation routes through review
    assert r.state == "CANDIDATE"
    r2 = _rec(state="DEMOTED")
    _t(r2, 1, "CANDIDATE")    # reopen as candidate is legal
    assert r2.state == "CANDIDATE"


def test_reactivated_to_active_forbidden():
    r = _rec(state="DORMANT")
    _t(r, 1, "REACTIVATED")
    tr = _t(r, 2, "ACTIVE")
    assert r.state == "REACTIVATED"  # blocked


def test_provenance_never_deleted():
    r = _rec(state="ACTIVE")
    original = r.provenance
    for to in ["CHALLENGED", "DEMOTED", "DORMANT"]:
        _t(r, 1, to)
    assert r.provenance is original


def test_superseded_then_reopen():
    r = _rec(state="ACTIVE")
    _t(r, 1, "SUPERSEDED"); assert r.state == "SUPERSEDED"
    _t(r, 2, "CANDIDATE"); assert r.state == "CANDIDATE"


def test_edge_table_replacement_preserves_history():
    eng = LifecycleEngine()
    r = _rec(state="ACTIVE")
    eng.add(r)
    eng.transition(r.record_id, 1, "DORMANT", actor="PO", authority_basis="b",
                   authority_level="PO", reason="demote")
    frozen = [t.to_dict() for t in r.transitions]
    # new edge table only allows ACTIVE -> DORMANT; DORMANT -> CANDIDATE must be rejected
    eng.replace_edge_table(LifecycleEdgeTable(contract_version="2.0.0", status="v2",
                                               legal_edges={"ACTIVE": frozenset(["DORMANT"])}))
    tr = eng.transition(r.record_id, 2, "CANDIDATE", actor="PO", authority_basis="b",
                        authority_level="PO", reason="attempt reopen under v2")
    assert tr.to_state == "CANDIDATE" and r.state == "DORMANT"  # denied under v2
    assert [t.to_dict() for t in r.transitions[:1]] == frozen     # history unchanged