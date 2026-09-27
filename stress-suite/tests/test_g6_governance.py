"""G6 — constitutional-attack governance regressions S20–S24 (G6-ER01..ER07
+ G6-TC01..TC09 truth closure).

Rewritten against the external-review-hardened engine plus the truth-closure
repairs: deep-frozen evaluation contracts whose internal representation is not
exposed as mutable state (TC03), future-rule changes as CANDIDATES ratified via
the CANONICAL authority engine, GOVERNOR != OPERATOR with authority DERIVED
from canonical AuthorityState (TC04), governed operator mandates verified
against canonical grants (TC05), verified governed permissions (TC06),
subject-bound evidence grade changes (TC07), deterministically linked
governance classification (TC08), and honest authority-mutation accounting
(TC09). Deterministic, local, model-free, wall-clock-free.
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
    ConstitutionalRuleRegistry,
    ConstitutionRule,
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
    verify_operator_mandate,
)
from engine.registry import EvidenceRegistry


# =========================================================================== #
# S20 / ER01 + TC03 — deep freeze: nested mutation is structurally impossible
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


def test_s20_tc03_backing_store_is_not_exposed_as_mutable_state():
    """TC03: the reachable `_data` attribute must not be a mutable dict.
    Item assignment through the reachable backing store must raise."""
    snap = EvalContractSnapshot.freeze("EVAL_A", 1, _criteria())
    assert snap.is_deeply_frozen()
    with pytest.raises(TypeError):
        snap.criteria._data["threshold"] = 0.99
    with pytest.raises(TypeError):
        snap.criteria._data["routing"]["weights"]["A"] = 99
    with pytest.raises(TypeError):
        snap.criteria._data["new_key"] = 1
    # nothing moved
    assert snap.criteria["threshold"] == 0.5
    assert snap.criteria["routing"]["weights"]["A"] == 1
    assert snap.is_deeply_frozen()
    # honest claim: the frozen tree is immutable through every supported/public
    # access path and through reachable internal attributes (MappingProxyType).
    # (deliberate object.__setattr__ introspection is outside every supported
    # surface and is NOT claimed impossible.)


def test_s20_tc03_sets_rejected_json_like_contract():
    """TC03: sets are not JSON — they are rejected at freeze time instead of
    being smuggled in with an invented canonical ordering."""
    with pytest.raises(TypeError):
        EvalContractSnapshot.freeze("EVAL_A", 1, {"tags": {"x", "y"}})
    with pytest.raises(TypeError):
        EvalContractSnapshot.freeze("EVAL_A", 1, {"tags": frozenset({"x"})})


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
# S22 / ER04 + TC04/TC05/TC06/TC07 — operator authority != truth; authority is
# DERIVED from canonical AuthorityState; mandates and permissions are governed
# =========================================================================== #
def _rule_registry():
    return ConstitutionalRuleRegistry([
        ConstitutionRule(rule_ref="A-009", version="1.0",
                         permitted_action_classes=("RESEARCH", "EXPERIMENT"),
                         scope="local-test",
                         applicable_roles=("OPERATOR", "GOVERNOR"),
                         status="ACTIVE", seq=1),
        ConstitutionRule(rule_ref="A-010", version="1.0",
                         permitted_action_classes=("POLICY",),
                         scope="local-test",
                         applicable_roles=("OPERATOR",),
                         status="ACTIVE", seq=1),
    ])


def _verified_perm(action_class="RESEARCH", rule_ref="A-009"):
    return ConstitutionPermissionRecord.claim(
        rule_ref=rule_ref, permitted_action_class=action_class,
        basis="constitution permits bounded research experiments", seq=1
    ).verify(_rule_registry())


def _auth(**seed):
    a = AuthorityState()
    for actor, level in seed.items():
        a.seed_level(actor, level)
    a.freeze_initialization()
    return a


def _issue_grant(authority, grant_id, actor, issued_by, seq,
                 action="research_directives", target="research://bounded",
                 risk_class="local-write"):
    from engine.authority import CapabilityGrant
    grant = CapabilityGrant(grant_id=grant_id, actor=actor, action=action,
                            target=target, environment="local-test",
                            risk_class=risk_class, issued_by=issued_by,
                            issued_seq=seq)
    authority.propose_authority_change(grant.actor, grant.actor, grant)
    authority.ratify_authority_change(issued_by, grant.actor, grant.actor, grant)
    return grant


def _graph(eid="EV_1", grade="CONTESTED", ref="MEASURE_1", subject="EV_1"):
    return EvidenceGraph(grades=(
        EmpiricalEvidenceGrade(evidence_id=eid, empirical_grade=grade,
                               grade_evidence_refs=(ref,), subject=subject),))


def _mandate(actor="GOV", scope="RESEARCH", issued_by="OPERATOR_1",
             grant_ref="GR_M1", seq=2):
    return OperatorMandate(actor=actor, scope=scope, issued_by=issued_by,
                           grant_ref=grant_ref, seq=seq)


def test_s22_operator_may_authorize_where_constitution_permits():
    auth = _auth(OPERATOR_1="OPERATOR")
    out = apply_operator_directive("DIR_1", "OPERATOR_1", auth, _graph(),
                                   _verified_perm(), evidence_id="EV_1",
                                   operator_preference="wants transformation")
    assert out.operator_action_authorized is True
    assert out.evidence_grade_unchanged is True
    assert out.evidence_grade_before == out.evidence_grade_after == "CONTESTED"
    assert "canonical OPERATOR authority" in out.authorization_basis


def test_s22_governor_is_not_automatically_operator():
    auth = _auth(GOV="GOVERNOR")
    out = apply_operator_directive("DIR_2", "GOV", auth, _graph(),
                                   _verified_perm(), evidence_id="EV_1")
    assert out.operator_action_authorized is False
    assert "NOT operator authority" in out.authorization_basis


def test_s22_governor_with_verified_mandate_may_authorize():
    auth = _auth(GOV="GOVERNOR", OPERATOR_1="OPERATOR")
    _issue_grant(auth, "GR_M1", actor="GOV", issued_by="OPERATOR_1", seq=1)
    mandate = _mandate(seq=2)
    out = apply_operator_directive("DIR_3", "GOV", auth, _graph(),
                                   _verified_perm(), evidence_id="EV_1",
                                   mandate=mandate)
    assert out.operator_action_authorized is True
    assert mandate.mandate_id in out.authorization_basis
    assert "VERIFIED governed operator mandate" in out.authorization_basis


def test_s22_worker_cannot_authorize_operator_actions():
    auth = _auth(W1="WORKER")
    out = apply_operator_directive("DIR_4", "W1", auth, _graph(),
                                   _verified_perm())
    assert out.operator_action_authorized is False


def test_s22_tc04_claimed_operator_label_has_no_authority():
    """TC04: the stimulus claims OPERATOR but canonical state says WORKER —
    the claim is recorded with NO VOTE; the decision derives WORKER."""
    auth = _auth(W1="WORKER", OPERATOR_1="OPERATOR")
    out = apply_operator_directive("DIR_5", "W1", auth, _graph(),
                                   _verified_perm(), evidence_id="EV_1",
                                   claimed_level="OPERATOR")
    assert out.operator_action_authorized is False
    assert "WORKER" in out.authorization_basis
    assert "claimed_level" in out.rationale
    assert "NO VOTE" in out.rationale


def test_s22_tc04_unknown_actor_fails_closed():
    """TC04: an actor with no canonical entry resolves to OBSERVER and cannot
    authorize operator actions."""
    auth = _auth(OPERATOR_1="OPERATOR")
    out = apply_operator_directive("DIR_6", "STRANGER", auth, _graph(),
                                   _verified_perm())
    assert out.operator_action_authorized is False
    assert "OBSERVER" in out.authorization_basis


def test_s22_tc06_operator_requires_verified_governed_permission():
    """TC06: a permission CLAIM (non-empty rule_ref/basis but unverified) cannot
    authorize anything — the decision path fails closed."""
    auth = _auth(OPERATOR_1="OPERATOR")
    claim = ConstitutionPermissionRecord.claim(
        rule_ref="A-009", permitted_action_class="RESEARCH",
        basis="constitution permits bounded research experiments", seq=1)
    with pytest.raises(ValueError):
        apply_operator_directive("DIR_7", "OPERATOR_1", auth, _graph(),
                                 claim, evidence_id="EV_1")


def test_s22_bare_boolean_cannot_mint_permission():
    with pytest.raises(ValueError):
        ConstitutionPermissionRecord(rule_ref="", permitted_action_class="RESEARCH",
                                     basis="")


def test_s22_tc06_permission_rule_must_resolve():
    """TC06: an unknown rule_ref fails closed even when strings are populated."""
    claim = ConstitutionPermissionRecord.claim(
        rule_ref="B-999", permitted_action_class="RESEARCH",
        basis="invented rule", seq=1)
    with pytest.raises(ValueError):
        claim.verify(_rule_registry())


def test_s22_tc06_permission_action_class_must_be_permitted():
    claim = ConstitutionPermissionRecord.claim(
        rule_ref="A-009", permitted_action_class="POLICY",
        basis="policy under research rule", seq=1)
    with pytest.raises(ValueError):
        claim.verify(_rule_registry())


def test_s22_tc06_permission_requires_active_rule():
    reg = ConstitutionalRuleRegistry([
        ConstitutionRule(rule_ref="A-009", version="1.0",
                         permitted_action_classes=("RESEARCH",),
                         scope="local-test",
                         applicable_roles=("OPERATOR", "GOVERNOR"),
                         status="SUSPENDED", seq=1)])
    claim = ConstitutionPermissionRecord.claim(
        rule_ref="A-009", permitted_action_class="RESEARCH",
        basis="under suspended rule", seq=1)
    with pytest.raises(ValueError):
        claim.verify(reg)


def test_s22_tc06_verified_permission_binds_rule_identity():
    verified = _verified_perm()
    assert verified.verified is True
    assert verified.version == "1.0"
    assert verified.status == "ACTIVE"
    assert "VERIFIED GOVERNED PERMISSION" in verified.verification_note


def test_s22_tc05_mandate_strings_alone_are_not_authority():
    """TC05: a mandate with populated strings but no resolving grant has no
    authority — verification fails."""
    auth = _auth(GOV="GOVERNOR", OPERATOR_1="OPERATOR")
    mandate = _mandate(grant_ref="GHOST_GRANT")
    ok, reasons = verify_operator_mandate(mandate, auth, "RESEARCH")
    assert ok is False
    assert any("does not resolve" in r for r in reasons)


def test_s22_tc05_mandate_issuer_must_hold_operator_authority():
    # issuer is a WORKER — populated strings cannot mint the operator claim
    auth = _auth(GOV="GOVERNOR", W2="WORKER", OPERATOR_1="OPERATOR")
    _issue_grant(auth, "GR_M1", actor="GOV", issued_by="OPERATOR_1", seq=1)
    mandate = _mandate(issued_by="W2", seq=2)
    ok, reasons = verify_operator_mandate(mandate, auth, "RESEARCH")
    assert ok is False
    assert any("does not hold OPERATOR authority" in r for r in reasons)


def test_s22_tc05_mandate_grant_must_pre_exist():
    auth = _auth(GOV="GOVERNOR", OPERATOR_1="OPERATOR")
    _issue_grant(auth, "GR_M1", actor="GOV", issued_by="OPERATOR_1", seq=5)
    mandate = _mandate(seq=2)          # grant issued AFTER the mandate
    ok, reasons = verify_operator_mandate(mandate, auth, "RESEARCH")
    assert ok is False
    assert any("not pre-existing" in r for r in reasons)


def test_s22_tc05_mandate_grantee_must_match_actor():
    auth = _auth(GOV="GOVERNOR", W2="WORKER", OPERATOR_1="OPERATOR")
    _issue_grant(auth, "GR_M1", actor="W2", issued_by="OPERATOR_1", seq=1)
    mandate = _mandate(actor="GOV", seq=2)
    ok, reasons = verify_operator_mandate(mandate, auth, "RESEARCH")
    assert ok is False
    assert any("grantee mismatch" in r for r in reasons)


def test_s22_tc05_mandate_revoked_grant_fails():
    auth = _auth(GOV="GOVERNOR", OPERATOR_1="OPERATOR")
    _issue_grant(auth, "GR_M1", actor="GOV", issued_by="OPERATOR_1", seq=1)
    auth.registry.revoke("GR_M1", "OPERATOR_1")
    mandate = _mandate(seq=2)
    ok, reasons = verify_operator_mandate(mandate, auth, "RESEARCH")
    assert ok is False
    assert any("does not resolve to an ACTIVE grant" in r for r in reasons)


def test_s22_tc05_mandate_scope_must_cover_action_class():
    auth = _auth(GOV="GOVERNOR", OPERATOR_1="OPERATOR")
    _issue_grant(auth, "GR_M1", actor="GOV", issued_by="OPERATOR_1", seq=1)
    mandate = _mandate(scope="EXPERIMENT", seq=2)
    ok, reasons = verify_operator_mandate(mandate, auth, "RESEARCH")
    assert ok is False
    assert any("does not cover requested action class" in r for r in reasons)


def test_s22_tc05_mandate_authority_bearing_grant_cannot_back_mandate():
    auth = _auth(GOV="GOVERNOR", OPERATOR_1="OPERATOR")
    _issue_grant(auth, "GR_M1", actor="GOV", issued_by="OPERATOR_1", seq=1,
                 risk_class="capital")
    mandate = _mandate(seq=2)
    ok, reasons = verify_operator_mandate(mandate, auth, "RESEARCH")
    assert ok is False
    assert any("authority-bearing risk class" in r for r in reasons)


def test_s22_tc05_self_issuance_refused_at_construction():
    with pytest.raises(AuthorityViolation):
        _mandate(issued_by="GOV")


def test_s22_tc05_governor_with_unverifiable_mandate_refused_at_directive():
    auth = _auth(GOV="GOVERNOR", OPERATOR_1="OPERATOR")
    mandate = _mandate(grant_ref="GHOST_GRANT", seq=2)   # grant never issued
    out = apply_operator_directive("DIR_8", "GOV", auth, _graph(),
                                   _verified_perm(), evidence_id="EV_1",
                                   mandate=mandate)
    assert out.operator_action_authorized is False
    assert "FAILED verification" in out.authorization_basis


def test_s22_direction_a_desire_cannot_improve_weak_evidence():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="MEASURE_WEAK", kind="OBSERVATION",
                                claim="weak mixed measurement", subject="EV_1",
                                seq=1))
    g = _graph(grade="CONTESTED")
    auth = _auth(OPERATOR_1="OPERATOR")
    out = apply_operator_directive("DIR_9", "OPERATOR_1", auth, g,
                                   _verified_perm(), evidence_id="EV_1",
                                   operator_preference="wants transformation")
    # authorized on the authority axis; evidence axis untouched by desire
    assert out.operator_action_authorized is True
    assert out.evidence_grade_after == "CONTESTED"
    # the grade moves ONLY through a registered, RELEVANT evidence ref
    reg.register(EvidenceRecord(record_id="MEASURE_2", kind="OBSERVATION",
                                claim="new measurement", subject="EV_1", seq=2))
    g2 = g.with_grade("EV_1", "SUPPORTED", "MEASURE_2", reg)
    assert g2.grade_of("EV_1") == "SUPPORTED"


def test_s22_direction_b_desire_cannot_block_contradictory_evidence():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="MEASURE_STRONG", kind="OBSERVATION",
                                claim="strong contradictory measurement",
                                subject="EV_INC", seq=2))
    g = _graph(eid="EV_INC", grade="SUPPORTED", ref="MEASURE_1",
               subject="EV_INC")
    auth = _auth(OPERATOR_1="OPERATOR")
    apply_operator_directive("DIR_10", "OPERATOR_1", auth, g, _verified_perm(),
                             evidence_id="EV_INC",
                             operator_preference="wants incumbent preserved")
    # operator preference did not freeze the graph — evidence still moves
    g2 = g.with_grade("EV_INC", "REFUTED", "MEASURE_STRONG", reg)
    assert g2.grade_of("EV_INC") == "REFUTED"


def test_s22_tc07_grade_change_requires_registered_evidence_ref():
    g = _graph()
    reg = EvidenceRegistry()          # empty: MEASURE_9 is not registered
    with pytest.raises(ValueError):
        g.with_grade("EV_1", "SUPPORTED", "MEASURE_9", reg)
    with pytest.raises(ValueError):
        g.with_grade("EV_1", "SUPPORTED", "", reg)
    assert g.grade_of("EV_1") == "CONTESTED"


def test_s22_tc07_registered_but_unrelated_ref_cannot_regrade():
    """TC07: registered-but-unrelated evidence (BTC price) cannot regrade an
    unrelated authority-policy claim."""
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="EV_BTC_PRICE", kind="OBSERVATION",
                                claim="btc price observation", subject="btc-price",
                                seq=1))
    g = _graph(eid="EV_AUTHORITY_POLICY", grade="CONTESTED",
               ref="MEASURE_1", subject="authority-policy")
    with pytest.raises(ValueError):
        g.with_grade("EV_AUTHORITY_POLICY", "SUPPORTED", "EV_BTC_PRICE", reg)
    assert g.grade_of("EV_AUTHORITY_POLICY") == "CONTESTED"


def test_s22_tc07_unknown_relevance_fails_closed():
    """TC07: an evidence record without a subject has UNKNOWN relevance and can
    never move a grade."""
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="MEASURE_NOSUBJ", kind="OBSERVATION",
                                claim="no subject binding", seq=1))
    g = _graph(eid="EV_1", grade="CONTESTED", subject="EV_1")
    with pytest.raises(ValueError):
        g.with_grade("EV_1", "SUPPORTED", "MEASURE_NOSUBJ", reg)
    assert g.grade_of("EV_1") == "CONTESTED"


def test_s22_tc07_relevant_ref_moves_grade_and_records_provenance():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="MEASURE_2", kind="OBSERVATION",
                                claim="new measurement", subject="EV_1", seq=2))
    g = _graph(eid="EV_1", grade="CONTESTED", subject="EV_1")
    g2 = g.with_grade("EV_1", "SUPPORTED", "MEASURE_2", reg)
    assert g2.grade_of("EV_1") == "SUPPORTED"
    assert "MEASURE_2" in g2.grades[0].grade_evidence_refs


def test_s22_unknown_grade_fails_closed():
    g = _graph()
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="M1", kind="OBSERVATION", claim="x",
                                subject="EV_1"))
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
# S24 / ER06 + TC08 — raw keywords are not governance truth; classification
# evidence must be deterministically LINKED to the event
# =========================================================================== #
def _ev(raw="authority amendment evaluation", refs=(), binding="", **kw):
    base = dict(event_id="EVT_1", raw_event=raw, evidence_refs=refs, seq=1,
                binding=binding)
    base.update(kw)
    return GovernanceEvent(**base)


def _sensor_registry():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="R_SENSOR", kind="OBSERVATION",
                                claim="sensor drift outside nominal band",
                                subject="sensor-drift", seq=3))
    return reg


def test_s24_structured_channel_routes_correctly():
    reg = _sensor_registry()
    ev = _ev(raw="sensor recalibration event", refs=("R_SENSOR",),
             binding="sensor-drift")
    ce = GovernanceClassificationEvidence(
        proposed_channel="SENSOR", evidence_refs=("R_SENSOR",),
        status="SUPPORTED", binding="sensor-drift")
    d = classify_governance_event(ev, (ce,), registry=reg)
    assert d.channel == "SENSOR"
    assert d.classification_failure == ""


def test_s24_raw_keyword_without_evidence_is_unresolved():
    # raw text contains "authority" but NO classification evidence exists
    ev = _ev(raw="authority grant request observed in prose", binding="x")
    d = classify_governance_event(ev)
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"
    assert d.classification_failure == "NO_EVIDENCE_SUPPORTED_CHANNEL"
    # the token hit is recorded as observation only, never as decision input
    assert d.preserved["raw_text_token_hits"] == ["AUTHORITY"]


def test_s24_contested_or_refless_evidence_does_not_route():
    ev = _ev(refs=("R1",), binding="b1")
    contested = GovernanceClassificationEvidence(
        proposed_channel="EVIDENCE", evidence_refs=("R1",), status="CONTESTED",
        binding="b1")
    refless = GovernanceClassificationEvidence(
        proposed_channel="AMENDMENT", evidence_refs=(), status="SUPPORTED",
        binding="b1")
    d = classify_governance_event(ev, (contested, refless))
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"


def test_s24_tc08_unbound_classification_evidence_fails_closed():
    """TC08: classification evidence without a deterministic binding is UNKNOWN
    linkage and cannot route anything."""
    reg = _sensor_registry()
    ev = _ev(raw="sensor recalibration drift", refs=("R_SENSOR",),
             binding="sensor-drift")
    unbound = GovernanceClassificationEvidence(
        proposed_channel="SENSOR", evidence_refs=("R_SENSOR",),
        status="SUPPORTED")                     # no binding field
    d = classify_governance_event(ev, (unbound,), registry=reg)
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"


def test_s24_tc08_registered_but_unrelated_evidence_cannot_route():
    """TC08: EV_RANDOM_PRICE resolves but is unrelated to the event subject —
    it must NOT route an AUTHORITY event."""
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="EV_RANDOM_PRICE", kind="OBSERVATION",
                                claim="random price tick", subject="price-tick",
                                seq=1))
    ev = _ev(raw="authority policy drift", refs=("EV_RANDOM_PRICE",),
             binding="authority-event")
    ce = GovernanceClassificationEvidence(
        proposed_channel="AUTHORITY", evidence_refs=("EV_RANDOM_PRICE",),
        status="SUPPORTED", binding="authority-event")
    d = classify_governance_event(ev, (ce,), registry=reg)
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"
    assert d.classification_failure == "NO_EVIDENCE_SUPPORTED_CHANNEL"


def test_s24_tc08_scope_mismatch_blocks_linkage():
    reg = _sensor_registry()
    ev = _ev(raw="sensor recalibration drift", refs=("R_SENSOR",),
             binding="sensor-drift", scope="production")
    ce = GovernanceClassificationEvidence(
        proposed_channel="SENSOR", evidence_refs=("R_SENSOR",),
        status="SUPPORTED", binding="sensor-drift", scope="local-test")
    d = classify_governance_event(ev, (ce,), registry=reg)
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"


def test_s24_multiple_supported_channels_is_unresolved():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="R1", kind="OBSERVATION",
                                claim="evidence-channel signal",
                                subject="dual-domain", seq=1))
    reg.register(EvidenceRecord(record_id="R2", kind="OBSERVATION",
                                claim="authority-channel signal",
                                subject="dual-domain", seq=2))
    ev = _ev(refs=("R1", "R2"), binding="dual-domain")
    ce1 = GovernanceClassificationEvidence(
        proposed_channel="EVIDENCE", evidence_refs=("R1",), status="SUPPORTED",
        binding="dual-domain")
    ce2 = GovernanceClassificationEvidence(
        proposed_channel="AUTHORITY", evidence_refs=("R2",), status="SUPPORTED",
        binding="dual-domain")
    d = classify_governance_event(ev, (ce1, ce2), registry=reg)
    assert d.channel == "UNRESOLVED_GOVERNANCE_EVENT"
    assert d.classification_failure == "AMBIGUOUS_EVIDENCE_SUPPORTED_CHANNELS"
    assert sorted(d.preserved["matching_channels"]) == ["AUTHORITY", "EVIDENCE"]
    assert "not self-ratified" in d.amendment_candidate


def test_s24_classification_refs_must_resolve_in_registry():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="R1", kind="OBSERVATION",
                                claim="real evidence", subject="evaluation-1",
                                seq=1))
    ev = _ev(refs=("R1",), binding="evaluation-1")
    good = GovernanceClassificationEvidence(
        proposed_channel="EVALUATION", evidence_refs=("R1",),
        status="SUPPORTED", binding="evaluation-1")
    bad = GovernanceClassificationEvidence(
        proposed_channel="CAPABILITY", evidence_refs=("GHOST_REF",),
        status="SUPPORTED", binding="evaluation-1")
    d = classify_governance_event(ev, (good, bad), registry=reg)
    assert d.channel == "EVALUATION"       # only the resolving ref routes


def test_s24_unknown_event_fully_preserved_no_ontology_mutation():
    ev = _ev(raw="quantum-regime data drift with no precedent rule",
             refs=("E9",), consequence_class="UNKNOWN",
             containment_action="SAFE_HOLD", binding="novel-quantum")
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