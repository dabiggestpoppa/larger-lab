"""G6 — constitutional-attack governance regressions S20–S24 (G6-ER01..ER07).

Rewritten against the external-review-hardened engine: deep-frozen evaluation
contracts, future-rule changes as CANDIDATES ratified via the CANONICAL
authority engine, GOVERNOR != OPERATOR, actual-vs-granted action envelopes,
evidence-bound governance classification, and CON-02 allocator provenance
observability. Deterministic, local, model-free, wall-clock-free.
"""
from __future__ import annotations

import pytest

from engine.authority import AuthorityState, AuthorityViolation
from engine.evidence import EvidenceRecord
from engine.g6_governance import (
    ActionGrantEnvelope,
    ActionRequest,
    AllocatorProvenanceLedger,
    AllocatorProvenanceRecord,
    CapabilityGraphEntry,
    ConstitutionPermissionRecord,
    EmpiricalEvidenceGrade,
    EvalContractSnapshot,
    EvidenceGraph,
    GovernanceClassificationEvidence,
    GovernanceEvent,
    OperatorMandate,
    apply_capability_change,
    apply_operator_directive,
    attempt_capability_driven_grant,
    activate_future_version,
    classify_governance_event,
    evaluate_against_window,
    execute_under_operator_hold,
    propose_contract_criteria_change,
)
from engine.registry import EvidenceRegistry


# =========================================================================== #
# S20 / ER01 — deep freeze: nested mutation is structurally impossible
# =========================================================================== #
def _criteria():
    return {
        "threshold": 0.5,
        "routing": {
            "channels": ["A", "B"],
            "weights": {"A": 1},
        },
    }


def test_s20_er01_nested_mutation_is_structurally_impossible():
    snap = EvalContractSnapshot.freeze("EVAL_A", 1, _criteria())
    assert snap.is_deeply_frozen()
    # frozen sequences have no mutation methods at all (structural, not convention)
    with pytest.raises(AttributeError):
        snap.criteria["routing"]["channels"].append("C")
    with pytest.raises(TypeError):
        snap.criteria["routing"]["weights"]["A"] = 99             # frozen dict
    with pytest.raises(TypeError):
        snap.criteria["routing"]["weights"]["B"] = 2              # new nested key
    with pytest.raises(TypeError):
        del snap.criteria["routing"]                              # frozen mapping
    assert list(snap.criteria["routing"]["channels"]) == ["A", "B"]


def test_s20_er01_caller_alias_is_severed():
    raw = _criteria()
    snap = EvalContractSnapshot.freeze("EVAL_A", 1, raw)
    # mutate the caller-retained alias freely
    raw["threshold"] = 0.99
    raw["routing"]["channels"].append("C")
    raw["routing"]["weights"]["A"] = 999
    # the frozen contract is untouched
    assert snap.criteria["threshold"] == 0.5
    assert list(snap.criteria["routing"]["channels"]) == ["A", "B"]
    assert snap.criteria["routing"]["weights"]["A"] == 1
    assert snap.is_deeply_frozen()


def test_s20_er01_fingerprint_deterministic_and_order_stable():
    a = EvalContractSnapshot.freeze("EVAL_A", 1, _criteria())
    b = EvalContractSnapshot.freeze("EVAL_A", 1,
                                    {"routing": {"weights": {"A": 1},
                                                 "channels": ["A", "B"]},
                                     "threshold": 0.5})
    assert a.criteria_fingerprint == b.criteria_fingerprint
    same = EvalContractSnapshot.freeze("EVAL_A", 1, _criteria())
    assert a.criteria_fingerprint == same.criteria_fingerprint


def test_s20_same_object_mutation_refused():
    snap = EvalContractSnapshot.freeze("EVAL_A", 1, _criteria())
    with pytest.raises(ValueError):
        snap.mutate_criteria("threshold", 0.99)
    assert snap.criteria["threshold"] == 0.5


def test_s20_unfreezable_criteria_fail_closed():
    class Opaque:
        pass
    with pytest.raises(TypeError):
        EvalContractSnapshot.freeze("EVAL_A", 1, {"obj": Opaque()})


# =========================================================================== #
# S20 / ER02 — future rule change is a CANDIDATE, never self-adoption
# =========================================================================== #
def test_s20_er02_future_version_is_a_candidate_not_adopted():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5})
    v = propose_contract_criteria_change(w1, {"threshold": 0.9},
                                         base_fingerprint=w1.criteria_fingerprint,
                                         seq=2, proposed_by="GOVERNOR")
    assert v.status == "FUTURE_VERSION_CANDIDATE"
    assert v.candidate is not None
    assert v.candidate.status == "PROPOSED"
    assert v.activated_snapshot is None          # nothing activated by proposing
    assert v.target_window_seq == 2 and v.retroactive is False


def test_s20_er02_proposal_does_not_change_current_window_replay():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5})
    propose_contract_criteria_change(w1, {"threshold": 0.9},
                                     base_fingerprint=w1.criteria_fingerprint, seq=2)
    ev1 = evaluate_against_window(w1, "R1", observed_metric=0.6)
    ev2 = evaluate_against_window(w1, "R2", observed_metric=0.6)
    assert ev1.passed and ev2.passed
    assert ev1.criteria_fingerprint_used == w1.criteria_fingerprint
    assert ev2.criteria_fingerprint_used == ev1.criteria_fingerprint_used


def test_s20_stale_fingerprint_and_retroactive_refused():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5})
    stale = propose_contract_criteria_change(w1, {"threshold": 0.9},
                                             base_fingerprint="stale", seq=2)
    assert stale.status == "STALE_FINGERPRINT_REFUSED"
    cur = propose_contract_criteria_change(w1, {"threshold": 0.9},
                                           base_fingerprint=w1.criteria_fingerprint,
                                           seq=1)
    assert cur.status == "RETROACTIVE_CHANGE_REFUSED" and cur.retroactive
    past = propose_contract_criteria_change(w1, {"threshold": 0.9},
                                            base_fingerprint=w1.criteria_fingerprint,
                                            seq=0)
    assert past.status == "RETROACTIVE_CHANGE_REFUSED"


def test_s20_er02_governor_cannot_self_ratify_future_version():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5})
    v = propose_contract_criteria_change(w1, {"threshold": 0.9},
                                         base_fingerprint=w1.criteria_fingerprint,
                                         seq=2, proposed_by="GOVERNOR")
    authority = AuthorityState()
    authority.seed_level("GOVERNOR", "GOVERNOR")
    authority.freeze_initialization()
    # GOVERNOR tries to activate its own proposal (proposer == ratifier target)
    with pytest.raises(AuthorityViolation):
        activate_future_version(v.candidate, authority, ratifier="GOVERNOR",
                                seq=3)
    assert v.candidate.status == "PROPOSED"      # candidate untouched


def test_s20_er02_governed_activation_by_operator_is_representable():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5})
    v = propose_contract_criteria_change(w1, {"threshold": 0.9},
                                         base_fingerprint=w1.criteria_fingerprint,
                                         seq=2, proposed_by="GOVERNOR")
    authority = AuthorityState()
    authority.seed_level("OPERATOR_1", "OPERATOR")
    authority.freeze_initialization()
    v2 = activate_future_version(v.candidate, authority, ratifier="OPERATOR_1",
                                 seq=3)
    assert v2.status == "FUTURE_VERSION_RATIFIED"
    assert v2.activated_snapshot is not None
    assert v2.activated_snapshot.window_seq == 2        # the FUTURE window only
    assert v2.activated_snapshot.criteria_fingerprint != w1.criteria_fingerprint
    assert v2.candidate.status == "RATIFIED_ACTIVATED"
    # the original candidate object is immutable and stays PROPOSED
    assert v.candidate.status == "PROPOSED"
    # the CURRENT window contract is unchanged
    assert w1.criteria["threshold"] == 0.5


def test_s20_er02_double_activation_refused():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5})
    v = propose_contract_criteria_change(w1, {"threshold": 0.9},
                                         base_fingerprint=w1.criteria_fingerprint,
                                         seq=2, proposed_by="GOVERNOR")
    authority = AuthorityState()
    authority.seed_level("OPERATOR_1", "OPERATOR")
    authority.freeze_initialization()
    v2 = activate_future_version(v.candidate, authority, ratifier="OPERATOR_1",
                                 seq=3)
    # activating the already-RATIFIED candidate is refused
    with pytest.raises(AuthorityViolation):
        activate_future_version(v2.candidate, authority, ratifier="OPERATOR_1",
                                seq=4)


# =========================================================================== #
# S21 / ER03 — capability != authority, canonical engine only
# =========================================================================== #
def test_s21_reliability_improvement_emits_review_request_only():
    cap = CapabilityGraphEntry(worker_id="W1", reliability_grade="NOMINAL")
    out = apply_capability_change(cap, "HIGH_RELIABILITY")
    assert out.capability_entry_changed is True
    assert out.emitted == ("AUTHORITY_REVIEW_REQUEST",)
    assert out.rationale and "propose+ratify" in out.rationale


def test_s21_capability_change_never_touches_authority_state():
    authority = AuthorityState()
    authority.seed_level("W1", "WORKER")
    authority.freeze_initialization()
    before = authority.level("W1")
    cap = CapabilityGraphEntry(worker_id="W1", reliability_grade="DEGRADED")
    apply_capability_change(cap, "HIGH_RELIABILITY")
    assert authority.level("W1") == before
    assert authority.registry.grants("W1") == []


def test_s21_unknown_reliability_grade_fails_closed():
    cap = CapabilityGraphEntry(worker_id="W1", reliability_grade="NOMINAL")
    with pytest.raises(ValueError):
        apply_capability_change(cap, "OMNISCIENT")


def test_s21_capability_driven_self_grant_refused_by_canonical_engine():
    authority = AuthorityState()
    authority.seed_level("W1", "WORKER")
    authority.seed_level("W2", "WORKER")
    authority.freeze_initialization()
    # worker tries to grant ITSELF a deployment grant via capability improvement
    with pytest.raises(AuthorityViolation):
        attempt_capability_driven_grant(authority, requester="W1",
                                        target_actor="W1",
                                        requested_risk_class="deployment", seq=1)
    assert authority.registry.grants("W1") == []


def test_s21_worker_cannot_ratify_authority_bearing_grant():
    authority = AuthorityState()
    authority.seed_level("W1", "WORKER")
    authority.seed_level("W2", "WORKER")
    authority.freeze_initialization()
    # W1 proposes a deployment grant for W2 and another WORKER cannot ratify it
    with pytest.raises(AuthorityViolation):
        attempt_capability_driven_grant(authority, requester="W1",
                                        target_actor="W2",
                                        requested_risk_class="deployment", seq=1)
    assert authority.registry.grants("W2") == []


def test_s21_governor_cannot_grant_itself_governor_authority():
    authority = AuthorityState()
    authority.seed_level("GOV", "GOVERNOR")
    authority.freeze_initialization()
    with pytest.raises(AuthorityViolation):
        attempt_capability_driven_grant(authority, requester="GOV",
                                        target_actor="GOV",
                                        requested_risk_class="deployment", seq=1)


# =========================================================================== #
# S22 / ER04 — operator authority != truth; GOVERNOR is not OPERATOR
# =========================================================================== #
def _perm():
    return ConstitutionPermissionRecord(
        rule_ref="A-009", permitted_action_class="RESEARCH",
        basis="constitution permits bounded research experiments", seq=1)


def _graph(eid="EV_1", grade="CONTESTED", ref="MEASURE_1"):
    return EvidenceGraph(grades=(
        EmpiricalEvidenceGrade(evidence_id=eid, empirical_grade=grade,
                               grade_evidence_refs=(ref,)),))


def test_s22_operator_may_authorize_where_constitution_permits():
    out = apply_operator_directive("DIR_1", "OPERATOR", _graph(), _perm(),
                                   evidence_id="EV_1",
                                   operator_preference="wants transformation")
    assert out.operator_action_authorized is True
    assert out.evidence_grade_unchanged is True
    assert out.evidence_grade_before == out.evidence_grade_after == "CONTESTED"


def test_s22_governor_is_not_automatically_operator():
    out = apply_operator_directive("DIR_2", "GOVERNOR", _graph(), _perm(),
                                   evidence_id="EV_1")
    assert out.operator_action_authorized is False
    assert "NOT operator authority" in out.authorization_basis


def test_s22_governor_with_specific_mandate_may_authorize():
    mandate = OperatorMandate(actor="GOV", scope="RESEARCH",
                              issued_by="OPERATOR_1", grant_ref="GR_M1", seq=1)
    out = apply_operator_directive("DIR_3", "GOVERNOR", _graph(), _perm(),
                                   evidence_id="EV_1", mandate=mandate)
    assert out.operator_action_authorized is True
    assert mandate.mandate_id in out.authorization_basis


def test_s22_worker_cannot_authorize_operator_actions():
    out = apply_operator_directive("DIR_4", "WORKER", _graph(), _perm())
    assert out.operator_action_authorized is False


def test_s22_bare_boolean_cannot_mint_permission():
    with pytest.raises(ValueError):
        ConstitutionPermissionRecord(rule_ref="", permitted_action_class="RESEARCH",
                                     basis="")


def test_s22_direction_a_desire_cannot_improve_weak_evidence():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="MEASURE_WEAK", kind="OBSERVATION",
                                claim="weak mixed measurement", seq=1))
    g = _graph(grade="CONTESTED")
    out = apply_operator_directive("DIR_5", "OPERATOR", g, _perm(),
                                   evidence_id="EV_1",
                                   operator_preference="wants transformation")
    # authorized on the authority axis; evidence axis untouched by desire
    assert out.operator_action_authorized is True
    assert out.evidence_grade_after == "CONTESTED"
    # the grade moves ONLY through a registered evidence ref, not through desire
    reg.register(EvidenceRecord(record_id="MEASURE_2", kind="OBSERVATION",
                                claim="new measurement", seq=2))
    g2 = g.with_grade("EV_1", "SUPPORTED", "MEASURE_2", reg)
    assert g2.grade_of("EV_1") == "SUPPORTED"


def test_s22_direction_b_desire_cannot_block_contradictory_evidence():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="MEASURE_STRONG", kind="OBSERVATION",
                                claim="strong contradictory measurement", seq=2))
    g = _graph(eid="EV_INC", grade="SUPPORTED", ref="MEASURE_1")
    apply_operator_directive("DIR_6", "OPERATOR", g, _perm(),
                             evidence_id="EV_INC",
                             operator_preference="wants incumbent preserved")
    # operator preference did not freeze the graph — evidence still moves
    g2 = g.with_grade("EV_INC", "REFUTED", "MEASURE_STRONG", reg)
    assert g2.grade_of("EV_INC") == "REFUTED"


def test_s22_grade_change_requires_registered_evidence_ref():
    g = _graph()
    reg = EvidenceRegistry()          # empty: MEASURE_9 is not registered
    with pytest.raises(ValueError):
        g.with_grade("EV_1", "SUPPORTED", "MEASURE_9", reg)
    with pytest.raises(ValueError):
        g.with_grade("EV_1", "SUPPORTED", "", reg)
    assert g.grade_of("EV_1") == "CONTESTED"


def test_s22_unknown_grade_fails_closed():
    g = _graph()
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="M1", kind="OBSERVATION", claim="x"))
    with pytest.raises(ValueError):
        g.with_grade("EV_1", "OBVIOUSLY_TRUE", "M1", reg)


# =========================================================================== #
# S23 / ER05 — actual action envelope vs granted envelope
# =========================================================================== #
def _request(**kw):
    base = dict(action="sandbox_rebalance_reversible",
                target_scope="sandbox://portfolio_minor",
                affected_surface="REVERSIBLE_SANDBOX", reversible=True,
                risk_class="local-write", environment="local-test")
    base.update(kw)
    return ActionRequest(**base)


def _grant(**kw):
    base = dict(grant_id="GR_1", grantee="OP_AGENT",
                action="sandbox_rebalance_reversible",
                target_scope="sandbox://portfolio_minor",
                affected_surface="REVERSIBLE_SANDBOX", reversible=True,
                risk_class="local-write", environment="local-test",
                issued_seq=1, expiry_seq=0, status="ACTIVE")
    base.update(kw)
    return ActionGrantEnvelope(**base)


def test_s23_exact_covered_reversible_action_may_continue():
    v = execute_under_operator_hold("ACT_1", "OP_AGENT", _request(), _grant(),
                                    current_seq=5)
    assert v.verdict == "MAY_CONTINUE"
    assert v.grant_used == "GR_1"


def test_s23_actual_capital_hides_behind_safe_grant_metadata():
    # grant metadata says safe; the ACTUAL action is capital -> HOLD
    v = execute_under_operator_hold("ACT_2", "OP_AGENT",
                                    _request(risk_class="capital"), _grant(),
                                    current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"
    assert "authority-bearing" in v.rationale


def test_s23_actual_irreversible_hides_behind_reversible_grant():
    v = execute_under_operator_hold("ACT_3", "OP_AGENT",
                                    _request(reversible=False), _grant(),
                                    current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"
    assert "irreversible" in v.rationale


def test_s23_grant_issued_after_hold_does_not_count():
    v = execute_under_operator_hold("ACT_4", "OP_AGENT", _request(),
                                    _grant(issued_seq=5), current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"
    assert "post-hoc" in v.rationale or "not before" in v.rationale


def test_s23_near_match_target_does_not_count():
    v = execute_under_operator_hold("ACT_5", "OP_AGENT",
                                    _request(action="sandbox_rebalance_reversible_v2"),
                                    _grant(), current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"
    assert "near-match" in v.rationale
    v2 = execute_under_operator_hold(
        "ACT_5b", "OP_AGENT", _request(target_scope="sandbox://portfolio_major"),
        _grant(), current_seq=5)
    assert v2.verdict == "OPERATOR_HOLD"


def test_s23_exact_action_but_broader_surface_does_not_count():
    v = execute_under_operator_hold(
        "ACT_6", "OP_AGENT",
        _request(affected_surface="HIGH_AFFECTED_SURFACE"), _grant(),
        current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"
    v2 = execute_under_operator_hold(
        "ACT_6b", "OP_AGENT", _request(affected_surface="PRODUCTION"),
        _grant(), current_seq=5)
    assert v2.verdict == "OPERATOR_HOLD"


def test_s23_expired_or_revoked_or_wrong_grantee_hold():
    v = execute_under_operator_hold("ACT_7", "OP_AGENT", _request(),
                                    _grant(expiry_seq=4), current_seq=5)
    assert v.verdict == "OPERATOR_HOLD" and "expired" in v.rationale
    v2 = execute_under_operator_hold("ACT_7b", "OP_AGENT", _request(),
                                     _grant(status="REVOKED"), current_seq=5)
    assert v2.verdict == "OPERATOR_HOLD"
    v3 = execute_under_operator_hold("ACT_7c", "SOMEONE_ELSE", _request(),
                                     _grant(), current_seq=5)
    assert v3.verdict == "OPERATOR_HOLD"
    v4 = execute_under_operator_hold("ACT_7d", "OP_AGENT", _request(), None,
                                     current_seq=5)
    assert v4.verdict == "OPERATOR_HOLD"


def test_s23_non_reversible_grant_envelope_cannot_authorize():
    v = execute_under_operator_hold("ACT_8", "OP_AGENT", _request(),
                                    _grant(reversible=False), current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"
    v2 = execute_under_operator_hold(
        "ACT_8b", "OP_AGENT", _request(), _grant(risk_class="deployment"),
        current_seq=5)
    assert v2.verdict == "OPERATOR_HOLD"


def test_s23_environment_mismatch_holds():
    v = execute_under_operator_hold("ACT_9", "OP_AGENT",
                                    _request(environment="production"), _grant(),
                                    current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"


def test_s23_unknown_risk_class_fails_closed():
    with pytest.raises(AuthorityViolation):
        _request(risk_class="medium-reversible")   # AMB-08: no invented ontology


# =========================================================================== #
# S24 / ER06 — raw keywords are not governance truth
# =========================================================================== #
def _ev(raw="authority amendment evaluation", refs=(), **kw):
    base = dict(event_id="EVT_1", raw_event=raw, evidence_refs=refs, seq=1)
    base.update(kw)
    return GovernanceEvent(**base)


def test_s24_structured_channel_routes_correctly():
    ev = _ev(raw="sensor recalibration event", refs=("R1",))
    ce = GovernanceClassificationEvidence(
        proposed_channel="SENSOR", evidence_refs=("R1",), status="SUPPORTED")
    d = classify_governance_event(ev, (ce,))
    assert d.channel == "SENSOR"
    assert d.classification_failure == ""


def test_s24_raw_keyword_without_evidence_is_unresolved():
    # raw text contains "authority" but NO classification evidence exists
    ev = _ev(raw="authority grant request observed in prose")
    d = classify_governance_event(ev)
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"
    assert d.classification_failure == "NO_EVIDENCE_SUPPORTED_CHANNEL"
    # the token hit is recorded as observation only, never as decision input
    assert d.preserved["raw_text_token_hits"] == ["AUTHORITY"]


def test_s24_contested_or_refless_evidence_does_not_route():
    ev = _ev(refs=("R1",))
    contested = GovernanceClassificationEvidence(
        proposed_channel="EVIDENCE", evidence_refs=("R1",), status="CONTESTED")
    refless = GovernanceClassificationEvidence(
        proposed_channel="AMENDMENT", evidence_refs=(), status="SUPPORTED")
    d = classify_governance_event(ev, (contested, refless))
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"


def test_s24_multiple_supported_channels_is_unresolved():
    ev = _ev(refs=("R1", "R2"))
    ce1 = GovernanceClassificationEvidence(
        proposed_channel="EVIDENCE", evidence_refs=("R1",), status="SUPPORTED")
    ce2 = GovernanceClassificationEvidence(
        proposed_channel="AUTHORITY", evidence_refs=("R2",), status="SUPPORTED")
    d = classify_governance_event(ev, (ce1, ce2))
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"
    assert d.classification_failure == "AMBIGUOUS_EVIDENCE_SUPPORTED_CHANNELS"
    assert sorted(d.preserved["matching_channels"]) == ["AUTHORITY", "EVIDENCE"]
    assert "not self-ratified" in d.amendment_candidate


def test_s24_classification_refs_must_resolve_in_registry():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="R1", kind="OBSERVATION",
                                claim="real evidence", seq=1))
    ev = _ev(refs=("R1",))
    good = GovernanceClassificationEvidence(
        proposed_channel="EVALUATION", evidence_refs=("R1",), status="SUPPORTED")
    bad = GovernanceClassificationEvidence(
        proposed_channel="CAPABILITY", evidence_refs=("GHOST_REF",),
        status="SUPPORTED")
    d = classify_governance_event(ev, (good, bad), registry=reg)
    assert d.channel == "EVALUATION"       # only the resolving ref routes


def test_s24_unknown_event_fully_preserved_no_ontology_mutation():
    ev = _ev(raw="quantum-regime data drift with no precedent rule",
             refs=("E9",), consequence_class="UNKNOWN",
             containment_action="SAFE_HOLD")
    d = classify_governance_event(ev)
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"
    assert d.preserved["raw_event"] == ev.raw_event
    assert d.preserved["evidence_refs"] == ["E9"]
    assert d.preserved["consequence_class"] == "UNKNOWN"
    assert d.preserved["containment_action"] == "SAFE_HOLD"
    assert "not self-ratified" in d.amendment_candidate


# =========================================================================== #
# ER07 — CON-02 allocator provenance observability
# =========================================================================== #
def test_er07_allocator_concentration_is_detectable():
    ledger = AllocatorProvenanceLedger()
    for i in range(3):
        ledger.record(AllocatorProvenanceRecord(
            evidence_ref=f"EV_{i}", initiating_actor=f"AGENT_{i}",
            allocator_actor="PO_ALLOCATION", worker_selected=f"W_{i}",
            source_path=f"source://{i}", retrieval_lineage="retrieval-1",
            exposure_lineage="agenda-A", seq=i))
    report = ledger.allocator_concentration()
    assert report["paths"] == 3
    assert report["distinct_allocators"] == 1
    assert report["concentration"] == "CONCENTRATED_SINGLE_ALLOCATOR"
    assert "observability only" in report["note"]


def test_er07_diverse_allocators_not_flagged_and_observations_preserved():
    ledger = AllocatorProvenanceLedger()
    ledger.record(AllocatorProvenanceRecord(
        evidence_ref="EV_0", initiating_actor="AGENT_0",
        allocator_actor="PO_ALLOCATION", worker_selected="W_0", seq=0))
    ledger.record(AllocatorProvenanceRecord(
        evidence_ref="EV_1", initiating_actor="AGENT_1",
        allocator_actor="OPEN_REVIEW", worker_selected="W_1", seq=1))
    report = ledger.allocator_concentration()
    assert report["concentration"] == "DIVERSE"
    # observation is full-fidelity regardless of verdict
    assert ledger.records[0].allocator_actor == "PO_ALLOCATION"


def test_er07_provenance_requires_evidence_ref():
    ledger = AllocatorProvenanceLedger()
    with pytest.raises(ValueError):
        ledger.record(AllocatorProvenanceRecord(
            evidence_ref="", initiating_actor="A", allocator_actor="B"))
