"""G6 — constitutional-attack governance regressions S20–S24.

Authorized only after PASS_G5RER_TRUTH_CLOSURE (STRESS-G5RERT1..X + R). Each
scenario asserts a forbidden transition stays forbidden and that authority
never forks from truth. Deterministic, local, model-free, wall-clock-free.
"""
from __future__ import annotations

import pytest

from engine.g6_governance import (
    AuthorityGraphEntry,
    CapabilityChangeOutcome,
    CapabilityGraphEntry,
    ContractChangeVerdict,
    EmpiricalEvidenceGrade,
    EvalContractSnapshot,
    EvidenceGraph,
    GovernanceEvent,
    GovernanceEventDisposition,
    OperatorDirectiveOutcome,
    OperatorHoldVerdict,
    PreAuthorizedGrant,
    WindowEvaluation,
    apply_capability_change,
    apply_operator_directive,
    classify_governance_event,
    evaluate_against_window,
    execute_under_operator_hold,
    governed_authority_grant,
    propose_contract_criteria_change,
)


# =========================================================================== #
# S20 — an active evaluation contract cannot change its own success criteria
# =========================================================================== #
def test_s20_same_object_mutation_is_refused():
    snap = EvalContractSnapshot.freeze("EVAL_A", 1, {"pass_threshold": 0.5,
                                                     "rule": "threshold"})
    with pytest.raises(ValueError):
        snap.mutate_criteria("pass_threshold", 0.99)
    # the frozen criteria really is immutable
    assert snap.criteria["pass_threshold"] == 0.5


def test_s20_future_version_is_legal_and_current_window_unchanged():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"pass_threshold": 0.5,
                                                   "rule": "threshold"})
    verdict = propose_contract_criteria_change(w1, {"pass_threshold": 0.9,
                                                    "rule": "threshold"},
                                               base_fingerprint=w1.criteria_fingerprint,
                                               seq=2)
    assert verdict.status == "FUTURE_VERSION_ADOPTED"
    assert verdict.retroactive is False
    assert verdict.adopted_snapshot is not None
    assert verdict.adopted_snapshot.window_seq == 2
    assert verdict.adopted_snapshot.criteria_fingerprint != w1.criteria_fingerprint


def test_s20_current_window_replay_uses_original_contract():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"pass_threshold": 0.5,
                                                   "rule": "threshold"})
    propose_contract_criteria_change(w1, {"pass_threshold": 0.9, "rule": "threshold"},
                                     base_fingerprint=w1.criteria_fingerprint, seq=2)
    # replaying a window-1 result AFTER the future version exists must still use
    # window 1's original criteria (0.5), not the new 0.9
    ev1 = evaluate_against_window(w1, "RESULT_W1", observed_metric=0.6)
    assert ev1.passed is True
    assert ev1.criteria_fingerprint_used == w1.criteria_fingerprint
    ev2 = evaluate_against_window(w1, "RESULT_W1_AGAIN", observed_metric=0.6)
    assert ev2.passed is True
    assert ev2.criteria_fingerprint_used == ev1.criteria_fingerprint_used  # deterministic replay


def test_s20_stale_fingerprint_proposal_refused():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"pass_threshold": 0.5,
                                                   "rule": "threshold"})
    verdict = propose_contract_criteria_change(w1, {"pass_threshold": 0.9,
                                                    "rule": "threshold"},
                                               base_fingerprint="stale-old-fp", seq=2)
    assert verdict.status == "STALE_FINGERPRINT_REFUSED"


def test_s20_no_retroactive_success_criteria():
    w1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"pass_threshold": 0.5,
                                                   "rule": "threshold"})
    # proposing criteria for the CURRENT window (seq 1) or a past window is retroactive
    cur = propose_contract_criteria_change(w1, {"pass_threshold": 0.9,
                                                "rule": "threshold"},
                                           base_fingerprint=w1.criteria_fingerprint, seq=1)
    assert cur.status == "RETROACTIVE_CHANGE_REFUSED"
    assert cur.retroactive is True
    past = propose_contract_criteria_change(w1, {"pass_threshold": 0.9,
                                                 "rule": "threshold"},
                                            base_fingerprint=w1.criteria_fingerprint, seq=0)
    assert past.status == "RETROACTIVE_CHANGE_REFUSED"


# =========================================================================== #
# S21 — capability != authority
# =========================================================================== #
def test_s21_reliability_improvement_never_grants_authority():
    cap = CapabilityGraphEntry(worker_id="WORKER_1", reliability_grade="DEGRADED")
    auth = AuthorityGraphEntry(actor_id="WORKER_1", authority_level="NONE")
    out = apply_capability_change(cap, auth, "HIGH_RELIABILITY",
                                  evidence_ref="EV_PERF")
    assert out.capability_entry_changed is True
    assert out.authority_entry_unchanged is True
    assert out.emitted == ("AUTHORITY_REVIEW_REQUEST",)
    assert "AUTHORITY_GRANTED" not in out.emitted


def test_s21_capability_change_does_not_mutate_authority_entry():
    cap = CapabilityGraphEntry(worker_id="WORKER_1", reliability_grade="NOMINAL")
    auth = AuthorityGraphEntry(actor_id="WORKER_1", authority_level="WORKER",
                               grant_refs=("GR_1",))
    apply_capability_change(cap, auth, "HIGH_RELIABILITY", evidence_ref="EV")
    # the authority entry object is unchanged (no grant, no revoke)
    assert auth.authority_level == "WORKER"
    assert auth.grant_refs == ("GR_1",)


def test_s21_authority_grant_requires_governed_grantor():
    # a capability record alone (grantor with NONE) cannot grant
    worker_auth = AuthorityGraphEntry(actor_id="WORKER_1", authority_level="WORKER")
    ok, level, _ = governed_authority_grant("WORKER_2", "WORKER", worker_auth,
                                            "EV_GRANT", seq=1)
    assert ok is False and level == "NONE"
    # a grantor without grant refs cannot grant
    gov_no_refs = AuthorityGraphEntry(actor_id="GOV", authority_level="GOVERNOR")
    ok2, _, _ = governed_authority_grant("WORKER_2", "WORKER", gov_no_refs,
                                         "EV_GRANT", seq=2)
    assert ok2 is False
    # a governed grantor with refs + evidence can grant
    gov = AuthorityGraphEntry(actor_id="GOV", authority_level="GOVERNOR",
                              grant_refs=("GOV_GRANT",))
    ok3, level3, _ = governed_authority_grant("WORKER_2", "WORKER", gov,
                                              "EV_GRANT", seq=3)
    assert ok3 is True and level3 == "WORKER"
    # grant without evidence ref fails closed
    ok4, _, _ = governed_authority_grant("WORKER_2", "WORKER", gov, "", seq=4)
    assert ok4 is False


# =========================================================================== #
# S22 — operator authority != truth
# =========================================================================== #
def test_s22_operator_desire_never_changes_empirical_grade():
    graph = EvidenceGraph(grades=(
        EmpiricalEvidenceGrade(evidence_id="EV_1", empirical_grade="CONTESTED",
                               grade_evidence_refs=("MEASURE_1",)),))
    # operator wants the transformation AND holds weak evidence — but the grade
    # must not move on desire alone
    out = apply_operator_directive(
        "DIR_1", "OPERATOR", graph, constitution_allows_action=True,
        evidence_id="EV_1")
    assert out.operator_action_authorized is True
    assert out.evidence_grade_unchanged is True
    assert out.evidence_grade_before == "CONTESTED"
    assert out.evidence_grade_after == "CONTESTED"


def test_s22_operator_prefers_incumbent_but_evidence_contradicts():
    graph = EvidenceGraph(grades=(
        EmpiricalEvidenceGrade(evidence_id="EV_INC", empirical_grade="SUPPORTED",
                               grade_evidence_refs=("MEASURE_1",)),))
    out = apply_operator_directive(
        "DIR_2", "GOVERNOR", graph, constitution_allows_action=True,
        evidence_id="EV_INC")
    assert out.evidence_grade_unchanged is True
    assert out.evidence_grade_after == "SUPPORTED"


def test_s22_worker_is_not_operator_authority():
    graph = EvidenceGraph()
    out = apply_operator_directive("DIR_3", "WORKER", graph,
                                   constitution_allows_action=True)
    assert out.operator_action_authorized is False


def test_s22_evidence_grade_changes_only_with_evidence():
    graph = EvidenceGraph(grades=(
        EmpiricalEvidenceGrade(evidence_id="EV_1", empirical_grade="CONTESTED",
                               grade_evidence_refs=("M1",)),))
    g2 = graph.with_grade("EV_1", "SUPPORTED", ref="MEASURE_2")
    assert g2.grade_of("EV_1") == "SUPPORTED"      # moved only with new evidence
    assert graph.grade_of("EV_1") == "CONTESTED"   # original unchanged (immutable)


# =========================================================================== #
# S23 — operator unavailable
# =========================================================================== #
def _grant(gid="GR_1", action="sandbox_rebalance_reversible", status="ACTIVE",
           surface="REVERSIBLE_SANDBOX", reversible=True, actor="OP_AGENT",
           expiry=0):
    return PreAuthorizedGrant(grant_id=gid, grantee=actor, exact_action=action,
                              surface_class=surface, reversible=reversible,
                              issued_seq=1, expiry_seq=expiry, status=status,
                              authority_basis="pre-existing operator grant")


def test_s23_exact_covered_reversible_action_may_continue():
    v = execute_under_operator_hold("ACT_1", "OP_AGENT", "sandbox_rebalance_reversible",
                                    _grant(), current_seq=5)
    assert v.verdict == "MAY_CONTINUE"
    assert v.grant_used == "GR_1"


def test_s23_near_match_grant_does_not_count():
    v = execute_under_operator_hold("ACT_1", "OP_AGENT", "sandbox_rebalance_SLIGHTLY_DIFFERENT",
                                    _grant(), current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"
    assert "near-match" in v.rationale


def test_s23_expired_grant_does_not_count():
    v = execute_under_operator_hold("ACT_1", "OP_AGENT", "sandbox_rebalance_reversible",
                                    _grant(expiry=4), current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"
    assert "expired" in v.rationale


def test_s23_revoked_grant_does_not_count():
    v = execute_under_operator_hold("ACT_1", "OP_AGENT", "sandbox_rebalance_reversible",
                                    _grant(status="REVOKED"), current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"


def test_s23_high_surface_irreversible_or_constitutional_is_hold():
    for surface in ("CONSTITUTIONAL", "CAPITAL", "IRREVERSIBLE", "HIGH_AFFECTED_SURFACE"):
        v = execute_under_operator_hold("ACT_1", "OP_AGENT",
                                        "sandbox_rebalance_reversible",
                                        _grant(surface=surface), current_seq=5)
        assert v.verdict == "OPERATOR_HOLD", surface
    v2 = execute_under_operator_hold("ACT_1", "OP_AGENT", "sandbox_rebalance_reversible",
                                     _grant(reversible=False), current_seq=5)
    assert v2.verdict == "OPERATOR_HOLD"


def test_s23_wrong_grantee_or_missing_grant_is_hold():
    v = execute_under_operator_hold("ACT_1", "SOMEONE_ELSE",
                                    "sandbox_rebalance_reversible", _grant(),
                                    current_seq=5)
    assert v.verdict == "OPERATOR_HOLD"
    v2 = execute_under_operator_hold("ACT_1", "OP_AGENT",
                                     "sandbox_rebalance_reversible", None,
                                     current_seq=5)
    assert v2.verdict == "OPERATOR_HOLD"


# =========================================================================== #
# S24 — unknown governance event
# =========================================================================== #
def test_s24_novel_event_stays_unresolved_and_preserved():
    ev = GovernanceEvent(event_id="EVT_NOVEL", seq=9,
                         raw_event="quantum-regime data drift with no precedent rule",
                         evidence_refs=("E9",),
                         consequence_class="UNKNOWN",
                         authority_context="NO_CHANNEL",
                         containment_action="SAFE_HOLD")
    d = classify_governance_event(ev)
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"
    assert d.classification_failure == "NO_MATCHING_GOVERNOR_CHANNEL"
    assert d.preserved["raw_event"] == ev.raw_event
    assert d.preserved["evidence_refs"] == ["E9"]
    assert d.preserved["containment_action"] == "SAFE_HOLD"
    # amendment candidate exists but is NOT self-ratified
    assert "amendment" in d.amendment_candidate.lower()
    assert "self-ratified" in d.amendment_candidate


def test_s24_matching_channel_routes_event():
    ev = GovernanceEvent(event_id="EVT_AUTH", seq=2,
                         raw_event="authority grant request observed",
                         authority_context="AUTHORITY")
    d = classify_governance_event(ev)
    assert d.channel == "AUTHORITY"
    assert d.classification_failure == ""


def test_s24_ambiguous_match_is_not_forced():
    ev = GovernanceEvent(event_id="EVT_AMB", seq=3,
                         raw_event="evidence authority amendment overlap event",
                         authority_context="UNKNOWN")
    d = classify_governance_event(ev)
    # matches EVIDENCE + AUTHORITY + AMENDMENT — must NOT be forced into one bucket
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"
    assert d.classification_failure == "AMBIGUOUS_MULTI_CHANNEL_MATCH"
    assert "matching_channels" in d.preserved
    assert "EVIDENCE" in d.preserved["matching_channels"]
    assert "AUTHORITY" in d.preserved["matching_channels"]
    assert len(d.preserved["matching_channels"]) >= 2


def test_s24_no_nearest_category_coercion_no_ontology_change():
    ev = GovernanceEvent(event_id="EVT_1", seq=1,
                         raw_event="completely novel event type")
    d = classify_governance_event(ev)
    # the event is NOT relabeled to the alphabetically-first channel
    assert d.channel != "AMENDMENT"
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"
    assert d.preserved["raw_event"] == "completely novel event type"
