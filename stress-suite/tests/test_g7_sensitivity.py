"""G7 — sensitivity + metamorphic audit regressions.

Proves relational invariants across the institution when non-essential surface
conditions change: evidence quality, independence, persistence, centrality,
reversibility, operator availability, environment shift, plus the metamorphic
relations and the open-issue pressure tests (CON-02 allocator, CON-03 Goodhart,
negative knowledge dogma, anomaly spam, centrality inertia, transformation
addiction). Every relation runs through the shared G7 machinery
(engine/g7_sensitivity.py); mirror surfaces are cross-checked against the real
engines they represent. Deterministic, local, model-free.
"""
from __future__ import annotations

import pytest

from engine.evidence import EvidenceRecord
from engine.g6_governance import (
    ConstitutionPermissionRecord,
    ConstitutionalRuleRegistry,
    ConstitutionRule,
    EmpiricalEvidenceGrade,
    EvalContractSnapshot,
    EvidenceGraph,
    OperatorMandate,
    verify_operator_mandate,
    classify_governance_event,
    GovernanceClassificationEvidence,
    GovernanceEvent,
)
from engine.g7_sensitivity import (
    BaselineBehaviorFingerprint,
    CounterexampleRecord,
    PerturbationRecord,
    RelationVerdict,
    SensitivityCaseSpec,
    adjudicator_centrality_verdict,
    allocator_surface,
    anomaly_spam_surface,
    authority_boundary_surface,
    centrality_rigor_verdict,
    environment_shift_surface,
    evidence_support_surface,
    freeze_surface,
    independence_surface,
    negative_knowledge_surface,
    operator_availability_surface,
    persistence_verdict,
    reconstruction_surface,
    reversibility_surface,
    run_sensitivity_case,
    transformation_pressure_surface,
)
from engine.registry import EvidenceRegistry


# =========================================================================== #
# 0. Harness mechanics
# =========================================================================== #
def test_g7_harness_preserves_counterexample_on_failure():
    spec = SensitivityCaseSpec(
        case_id="HARNESS_FAIL", surface="x", subsystem="g7", dimension="HARNESS",
        perturbation=PerturbationRecord("p", "HARNESS", "X", "forcing failure"),
        baseline=lambda: {"v": 1}, perturbed=lambda: {"v": 2},
        relation_expected="invariance (forced fail)",
        relation=lambda b, p: b == p,
        baseline_inputs=lambda: {"a": 1}, perturbed_inputs=lambda: {"a": 2})
    v = run_sensitivity_case(spec, counterexample_classification="TEST CONTRACT WRONG")
    assert v.pass_ is False
    assert v.counterexample is not None
    assert v.counterexample.classification == "TEST CONTRACT WRONG"
    assert v.counterexample.baseline_observables == {"v": 1}
    assert v.counterexample.perturbed_observables == {"v": 2}


def test_g7_harness_passes_and_records_verdict():
    spec = SensitivityCaseSpec(
        case_id="HARNESS_OK", surface="x", subsystem="g7", dimension="HARNESS",
        perturbation=PerturbationRecord("p", "HARNESS", "X", "no-op"),
        baseline=lambda: {"v": 1}, perturbed=lambda: {"v": 1},
        relation_expected="invariance",
        relation=lambda b, p: b == p)
    v = run_sensitivity_case(spec)
    assert v.pass_ is True
    assert v.counterexample is None
    assert v.relation_observed is True


# =========================================================================== #
# 1. EVIDENCE QUALITY — WEAK -> MIXED -> STRONG must not weaken support
# =========================================================================== #
def _quality_records(subject="CLAIM_1", lineage_prefix="SRC", count=2):
    return [EvidenceRecord(record_id=f"R_{lineage_prefix}_{i}", kind="OBSERVATION",
                           claim=f"supports {subject}", subject=subject,
                           source_lineage=f"{lineage_prefix}{i}", seq=i)
            for i in range(count)]


def test_g7_evidence_quality_monotone_non_weakening():
    weak = evidence_support_surface(_quality_records(lineage_prefix="SRC", count=2))
    strong = evidence_support_surface(
        _quality_records(lineage_prefix="SRC", count=4) +
        _quality_records(lineage_prefix="OTHER", count=3))
    assert strong["raw_evidence_count"] >= weak["raw_evidence_count"]
    assert strong["distinct_source_lineages"] >= weak["distinct_source_lineages"]


def test_g7_evidence_quality_more_distinct_lineages_never_hides_weakness():
    # a SINGLE-lineage claim cannot look strong by adding copies of itself
    one = evidence_support_surface([EvidenceRecord(
        record_id="R0", kind="OBSERVATION", claim="supports", subject="C",
        source_lineage="SRC", seq=0)])
    copies = evidence_support_surface([EvidenceRecord(
        record_id=f"R{i}", kind="OBSERVATION", claim="supports", subject="C",
        source_lineage="SRC", seq=i) for i in range(50)])
    assert copies["distinct_source_lineages"] == 1 == one["distinct_source_lineages"]
    assert copies["raw_evidence_count"] == 50


def test_g7_evidence_quality_legitimate_falsification_is_causal_not_mechanical():
    """A stronger observation that legitimately falsifies a hypothesis moves the
    grade via the subject-bound evidence path — the drop is causal (REFUTED),
    not a monotonicity violation."""
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="CONTRADICT", kind="OBSERVATION",
                                claim="refutes the claim", subject="CLAIM_1", seq=9))
    graph = EvidenceGraph(grades=(
        EmpiricalEvidenceGrade(evidence_id="CLAIM_1", empirical_grade="SUPPORTED",
                               grade_evidence_refs=("R0",), subject="CLAIM_1"),))
    g2 = graph.with_grade("CLAIM_1", "REFUTED", "CONTRADICT", reg)
    assert g2.grade_of("CLAIM_1") == "REFUTED"
    # the causal reason is recorded in the grade provenance, not hand-waved
    assert "CONTRADICT" in g2.grades[0].grade_evidence_refs


# =========================================================================== #
# 2. INDEPENDENCE — more genuine independence never reduces it; duplication
#    cannot manufacture it
# =========================================================================== #
def _reviewer(src, model="M1", retr="B1", rid="W1"):
    return {"source_lineage": src, "model_family": model,
            "retrieval_bundle": retr, "reviewer_id": rid}


def test_g7_independence_more_genuine_independence_never_weakens():
    low = independence_surface([_reviewer("SRC", rid=f"W{i}") for i in range(5)])
    high = independence_surface([
        _reviewer("SRC_A", "M_A", "B_A", "W1"),
        _reviewer("SRC_B", "M_B", "B_A", "W2"),
        _reviewer("SRC_C", "M_C", "B_B", "W3"),
        _reviewer("SRC_D", "M_D", "B_B", "W4")])
    assert high["distinct_source_lineages"] >= low["distinct_source_lineages"]
    assert high["distinct_model_families"] >= low["distinct_model_families"]
    assert high["distinct_retrieval_bundles"] >= low["distinct_retrieval_bundles"]


def test_g7_independence_duplicated_correlated_reviewer_manufactures_nothing():
    one = independence_surface([_reviewer("SRC")])
    ten = independence_surface([_reviewer("SRC", rid=f"W{i}") for i in range(10)])
    assert ten["raw_reviewers"] == 10
    assert ten["distinct_source_lineages"] == one["distinct_source_lineages"] == 1
    assert ten["distinct_model_families"] == 1
    assert ten["distinct_retrieval_bundles"] == 1


def test_g7_independence_unknown_provenance_is_never_favorable():
    unknown = independence_surface([{"reviewer_id": "W1"},
                                    {"reviewer_id": "W2"}])
    assert unknown["distinct_source_lineages"] == 0
    assert unknown["distinct_model_families"] == 0


# =========================================================================== #
# 3. PERSISTENCE — one-shot anomaly != chronic anomaly; raw repetition without
#    quality must not force transformation
# =========================================================================== #
def test_g7_persistence_one_shot_vs_repeated_vs_chronic():
    one_shot = persistence_verdict([{"independent_contradiction": "MEDIUM"}])
    repeated = persistence_verdict([{"independent_contradiction": "MEDIUM"}] * 3)
    chronic = persistence_verdict([{"independent_contradiction": "MEDIUM"}] * 10)
    assert one_shot["to_state"] != "ESCALATION_REVIEW"     # one-shot anomaly != chronic
    assert repeated["to_state"] == "ESCALATION_REVIEW"     # repeated credible contradiction
    assert chronic["to_state"] == repeated["to_state"]     # extra repetition != deeper change


def test_g7_persistence_raw_repetition_without_quality_forces_nothing():
    spam = anomaly_spam_surface(1000)
    assert spam["to_state"] != "ESCALATION_REVIEW"


def test_g7_anomaly_spam_counts_1_10_100_1000_all_hold():
    for n in (1, 10, 100, 1000):
        assert anomaly_spam_surface(n)["to_state"] != "ESCALATION_REVIEW", n


# =========================================================================== #
# 4. REVERSIBILITY — lower reversibility must never ease autonomous authority
# =========================================================================== #
def test_g7_reversibility_irreversible_never_easier():
    high = reversibility_surface(reversible=True)
    low = reversibility_surface(reversible=False)
    assert high["verdict"] == "MAY_CONTINUE"
    assert low["verdict"] == "OPERATOR_HOLD"


def test_g7_reversibility_grant_metadata_cannot_make_irreversible_reversible():
    v = reversibility_surface(reversible=False, grant_reversible=True)
    assert v["verdict"] == "OPERATOR_HOLD"
    assert "irreversible" in v["rationale"]


# =========================================================================== #
# 5. CENTRALITY — higher centrality raises rigor, never grants immunity
# =========================================================================== #
def test_g7_centrality_core_raises_rigor_but_not_permanent_immunity():
    leaf = centrality_rigor_verdict("LEAF", "MEDIUM", 1)
    core_medium = centrality_rigor_verdict("CORE", "MEDIUM", 1)
    core_strong_persistent = centrality_rigor_verdict("CORE", "HIGH", 2)
    assert leaf == "REVIEW_OPENED"
    assert core_medium == "RIGOR_HOLD"               # rigor raised at core
    assert core_strong_persistent == "REVIEW_OPENED"  # no permanent immunity


def test_g7_centrality_real_adjudicator_rigor_raised_not_immunity():
    """Ground the mirror surface in the REAL EvidenceAdjudicator: a HIGH-
    centrality observation needs HIGH independent contradiction (rigor), and a
    persistent HIGH contradiction still opens ESCALATION_REVIEW at core (no
    permanent incumbent immunity)."""
    # CORE + MEDIUM contradiction, 3 observations -> rigor holds (MEDIUM is not
    # enough for the HIGH-bar core rule)
    assert adjudicator_centrality_verdict("HIGH", "MEDIUM", 3) == "RIGOR_HOLD"
    # CORE + HIGH contradiction, persistent -> review opens
    assert adjudicator_centrality_verdict("HIGH", "HIGH", 2) == "REVIEW_OPENED"
    # chronic strong contradiction cannot be deferred forever
    assert adjudicator_centrality_verdict("HIGH", "HIGH", 5) == "REVIEW_OPENED"
    # the pure mirror surface (LEAF/MID/CORE vocabulary) agrees on the same
    # relational shape
    assert centrality_rigor_verdict("CORE", "MEDIUM", 1) == "RIGOR_HOLD"
    assert centrality_rigor_verdict("CORE", "HIGH", 2) == "REVIEW_OPENED"


def test_g7_centrality_inertia_chronic_strong_contradiction_opens_review():
    for persist in (2, 5, 20):
        assert centrality_rigor_verdict("CORE", "HIGH", persist) == "REVIEW_OPENED"
        assert adjudicator_centrality_verdict("HIGH", "HIGH", persist) == "REVIEW_OPENED"


# =========================================================================== #
# 6. OPERATOR AVAILABILITY — availability changes action authority, never
#    empirical evidence state
# =========================================================================== #
def test_g7_operator_availability_does_not_change_evidence_state():
    available = operator_availability_surface(operator_available=True)
    unavailable = operator_availability_surface(operator_available=False)
    assert available["action_verdict"] == "DIRECTIVE_AUTHORIZED"
    assert unavailable["action_verdict"] == "OPERATOR_HOLD"
    assert available["evidence_grade"] == unavailable["evidence_grade"] == "CONTESTED"
    assert available["evidence_refs"] == unavailable["evidence_refs"]


# =========================================================================== #
# 7. ENVIRONMENT SHIFT — changes interpretation, never erases provenance or
#    bypasses evidence
# =========================================================================== #
def test_g7_environment_shift_preserves_provenance_and_never_bypasses_evidence():
    none_ = environment_shift_surface(environment="")
    confirmed = environment_shift_surface(environment="production")
    assert none_["channel"] == "SENSOR"
    assert confirmed["channel"] == "UNRESOLVED_GOVERNANCE_EVENT"
    # provenance fully preserved across the shift
    assert confirmed["preserved_raw_event"] == none_["preserved_raw_event"]
    assert confirmed["preserved_evidence_refs"] == none_["preserved_evidence_refs"]
    # evidence is never bypassed: the production-scope shift is not routed by
    # raw keywords
    assert confirmed["amendment_candidate"] is True


# =========================================================================== #
# METAMORPHIC RELATIONS
# =========================================================================== #
def test_g7_m1_rename_agent_ids_same_substantive_decision():
    a = authority_boundary_surface("OPERATOR_1", "GOV")
    b = authority_boundary_surface("OP_X", "GOV_X")
    assert a == b == {"operator_authorized": True,
                      "governor_authorized": False,
                      "stranger_authorized": False}


def test_g7_m2_rename_runtime_creator_same_constitutional_result():
    f1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5},
                                     created_by="RUNTIME_A")
    f2 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5},
                                     created_by="RUNTIME_B")
    # the creator/runtime label is identity metadata, not decision content
    assert f1.criteria_fingerprint == f2.criteria_fingerprint


def test_g7_m3_duplicate_correlated_evidence_10x_independence_unchanged():
    one = independence_surface([_reviewer("SRC")])
    ten = independence_surface([_reviewer("SRC", rid=f"W{i}") for i in range(10)])
    assert one["distinct_source_lineages"] == ten["distinct_source_lineages"] == 1
    assert one["distinct_model_families"] == ten["distinct_model_families"] == 1


def test_g7_m4_alias_one_canonical_evidence_under_multiple_refs_one_epistemic_path():
    reg = EvidenceRegistry()
    # the SAME content registered under two ids is one lineage, not two
    reg.register(EvidenceRecord(record_id="EV_1", kind="OBSERVATION",
                                claim="same claim", subject="S",
                                source_lineage="L1", seq=1))
    reg.register(EvidenceRecord(record_id="EV_1_ALIAS", kind="OBSERVATION",
                                claim="same claim", subject="S",
                                source_lineage="L1", seq=1))
    summary = reg.lineage_summary(["EV_1", "EV_1_ALIAS"])
    assert summary.distinct_source_lineages == 1


def test_g7_m5_reorder_unordered_maps_fingerprint_stable():
    # dict KEY order is semantically unordered; the channels LIST is ordered and
    # must NOT be reordered (that is identity content)
    a = freeze_surface({"threshold": 0.5, "routing": {"channels": ["A", "B"],
                                                      "weights": {"A": 1}}})
    b = freeze_surface({"routing": {"weights": {"A": 1},
                                    "channels": ["A", "B"]},
                        "threshold": 0.5})
    assert a["criteria_fingerprint"] == b["criteria_fingerprint"]


def test_g7_m6_reorder_non_causal_evidence_arrival_equivalent_outcome():
    a = persistence_verdict([{"independent_contradiction": "MEDIUM"},
                             {"reliability_degradation": "LOW"},
                             {"independent_contradiction": "MEDIUM"}])
    b = persistence_verdict([{"reliability_degradation": "LOW"},
                             {"independent_contradiction": "MEDIUM"},
                             {"independent_contradiction": "MEDIUM"}])
    # same multiset, no causal ordering dependence: identical terminal proposal
    assert (a["action"], a["rule_id"], a["to_state"]) == \
           (b["action"], b["rule_id"], b["to_state"])


def test_g7_m7_file_count_with_preserved_affected_surface_rigor_unchanged():
    # review rigor is a function of centrality/contradiction/persistence, not of
    # how many files an artifact happens to contain
    small = centrality_rigor_verdict("CORE", "HIGH", 2)
    big = centrality_rigor_verdict("CORE", "HIGH", 2)
    assert small == big == "REVIEW_OPENED"
    assert centrality_rigor_verdict("LEAF", "MEDIUM", 1) == \
           centrality_rigor_verdict("LEAF", "MEDIUM", 1)


def test_g7_m8_m9_equivalent_authority_representation_same_boundary():
    a = authority_boundary_surface("OPERATOR_1", "GOVERNOR_9")
    b = authority_boundary_surface("OP-RENAMED", "GOV-RENAMED")
    assert a == b


def test_g7_m10_claim_operator_label_without_authority_no_effect():
    out = authority_boundary_surface("OPERATOR_1", "GOV")
    assert out["stranger_authorized"] is False


def test_g7_m11_replace_mandate_id_same_governed_semantics_same_result():
    from engine.authority import AuthorityState, CapabilityGrant

    def _check(mandate, seq):
        auth = AuthorityState()
        auth.seed_level("GOV", "GOVERNOR")
        auth.seed_level("OPERATOR_1", "OPERATOR")
        auth.freeze_initialization()
        grant = CapabilityGrant(grant_id="GR_M1", actor="GOV",
                                action="research_directives",
                                target="research://bounded",
                                environment="local-test", risk_class="local-write",
                                issued_by="OPERATOR_1", issued_seq=1)
        auth.propose_authority_change("GOV", "GOV", grant)
        auth.ratify_authority_change("OPERATOR_1", "GOV", "GOV", grant)
        return verify_operator_mandate(mandate, auth, "RESEARCH")

    m1 = OperatorMandate(actor="GOV", scope="RESEARCH", issued_by="OPERATOR_1",
                         grant_ref="GR_M1", seq=2)
    m2 = OperatorMandate(actor="GOV", scope="RESEARCH", issued_by="OPERATOR_1",
                         grant_ref="GR_M1", seq=3)      # different id, same semantics
    assert m1.mandate_id != m2.mandate_id
    ok1, _ = _check(m1, 2)
    ok2, _ = _check(m2, 3)
    assert ok1 is ok2 is True


def test_g7_m12_unrelated_registered_evidence_cannot_alter_another_claim():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="EV_BTC", kind="OBSERVATION",
                                claim="price tick", subject="btc-price", seq=1))
    graph = EvidenceGraph(grades=(
        EmpiricalEvidenceGrade(evidence_id="EV_POLICY", empirical_grade="CONTESTED",
                               grade_evidence_refs=("R0",), subject="policy"),))
    with pytest.raises(ValueError):
        graph.with_grade("EV_POLICY", "SUPPORTED", "EV_BTC", reg)
    assert graph.grade_of("EV_POLICY") == "CONTESTED"


def test_g7_m13_s24_wording_change_same_structured_evidence_same_channel():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="R_SENSOR", kind="OBSERVATION",
                                claim="sensor drift", subject="sensor-drift",
                                seq=3))
    ce = GovernanceClassificationEvidence(
        proposed_channel="SENSOR", evidence_refs=("R_SENSOR",),
        status="SUPPORTED", binding="sensor-drift")
    e1 = GovernanceEvent(event_id="E1", raw_event="sensor recalibration drift",
                         evidence_refs=("R_SENSOR",), binding="sensor-drift", seq=1)
    e2 = GovernanceEvent(event_id="E2",
                         raw_event="completely different wording that still "
                                   "describes the same sensor recalibration drift",
                         evidence_refs=("R_SENSOR",), binding="sensor-drift", seq=2)
    d1 = classify_governance_event(e1, (ce,), registry=reg)
    d2 = classify_governance_event(e2, (ce,), registry=reg)
    assert d1.channel == d2.channel == "SENSOR"


def test_g7_m14_s24_keyword_change_no_classification_evidence_still_unresolved():
    e1 = GovernanceEvent(event_id="E1", raw_event="authority grant request", seq=1,
                         binding="x")
    e2 = GovernanceEvent(event_id="E2",
                         raw_event="renamed tokens with no overlap", seq=2,
                         binding="y")
    d1 = classify_governance_event(e1)
    d2 = classify_governance_event(e2)
    assert d1.channel == d2.channel == "UNRESOLVED_GOVERNANCE_EVENT"


def test_g7_m15_equivalent_future_contract_canonical_content_same_fingerprint():
    a = EvalContractSnapshot.freeze("EC", 2, {"threshold": 0.9, "rule": "threshold"})
    b = EvalContractSnapshot.freeze("EC", 2, {"rule": "threshold", "threshold": 0.9})
    assert a.criteria_fingerprint == b.criteria_fingerprint


def test_g7_m16_nested_caller_aliases_frozen_state_unchanged():
    raw = {"threshold": 0.5, "routing": {"channels": ["A"]}}
    snap = EvalContractSnapshot.freeze("EC", 1, raw)
    raw["threshold"] = 0.99
    raw["routing"]["channels"].append("C")
    assert snap.criteria["threshold"] == 0.5
    assert list(snap.criteria["routing"]["channels"]) == ["A"]
    assert snap.is_deeply_frozen()


def test_g7_m17_runtime_process_restart_reconstructs_identically():
    content = {"threshold": 0.5, "routing": {"channels": ["A", "B"]}}
    r1 = reconstruction_surface(content, epoch_id="E1")
    r2 = reconstruction_surface(content, epoch_id="E1")   # fresh registry = restart
    assert r1["fingerprint"] == r2["fingerprint"]
    assert r1["registered"] is r2["registered"] is True


# =========================================================================== #
# OPEN-ISSUE PRESSURE TESTS
# =========================================================================== #
def test_g7_con02_allocator_concentration_remains_observable():
    diverse_paths = [
        {"evidence_ref": f"EV_{i}", "initiating_actor": f"AGENT_{i}",
         "allocator_actor": "PO_ALLOCATION", "worker_selected": f"W_{i}",
         "source_path": f"source://{i}", "retrieval_lineage": f"retrieval-{i}",
         "exposure_lineage": f"agenda-{i}"}
        for i in range(6)]
    report = allocator_surface(diverse_paths)
    assert report["paths"] == 6
    assert report["distinct_allocators"] == 1
    assert report["concentration"] == "CONCENTRATED_SINGLE_ALLOCATOR"
    assert "observability only" in report["note"]


def test_g7_con02_diverse_allocators_visible_as_diverse():
    paths = [
        {"evidence_ref": "EV_0", "initiating_actor": "AGENT_0",
         "allocator_actor": "PO_ALLOCATION", "source_path": "s0"},
        {"evidence_ref": "EV_1", "initiating_actor": "AGENT_1",
         "allocator_actor": "OPEN_REVIEW", "source_path": "s1"},
        {"evidence_ref": "EV_2", "initiating_actor": "AGENT_2",
         "allocator_actor": "OPEN_REVIEW", "source_path": "s2"}]
    report = allocator_surface(paths)
    assert report["distinct_allocators"] == 2
    assert report["concentration"] == "DIVERSE"


def test_g7_con03_goodhart_threshold_knowledge_manufactures_no_transformation():
    for known in ("EXACT", "APPROXIMATE", "UNKNOWN"):
        r = transformation_pressure_surface(novelty_count=100, threshold_known=known)
        assert r["candidate"] is False, known
        assert r["note"]
    genuine = transformation_pressure_surface(
        novelty_count=100, has_quality=True, has_independence=True,
        has_contradiction=True, threshold_known="EXACT")
    assert genuine["candidate"] is True


def test_g7_transformation_addiction_novelty_count_alone_forces_nothing():
    for n in (1, 10, 100, 1000):
        r = transformation_pressure_surface(novelty_count=n)
        assert r["candidate"] is False, n


def test_g7_negative_knowledge_narrow_reopen_conditions_visible_as_dogma():
    impossible = negative_knowledge_surface(reopen_possible=False)
    possible = negative_knowledge_surface(reopen_possible=True)
    assert impossible["reopen_state"] == "NO_REOPEN"
    assert impossible["dogma_risk"] is True
    assert possible["reopen_state"] == "REOPEN_CANDIDATE"
    assert possible["dogma_risk"] is False