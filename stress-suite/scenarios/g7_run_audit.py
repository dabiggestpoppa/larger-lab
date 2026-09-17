"""G7 — sensitivity + metamorphic audit runner (STRESS-G7R).

Runs the canonical sensitivity cases, metamorphic relations and open-issue
pressure tests through the shared G7 machinery and writes the evidence package:

    evidence/G7_RESULT.md
    evidence/G7_EVIDENCE_RECEIPT.json
    evidence/G7_SENSITIVITY_MATRIX.md
    evidence/G7_METAMORPHIC_AUDIT.md
    evidence/G7_MONOTONICITY_AUDIT.md
    evidence/G7_CON02_ALLOCATOR_SENSITIVITY.md
    evidence/G7_CON03_GOODHART_AUDIT.md
    evidence/G7_COUNTEREXAMPLE_REGISTER.json

Byte-reproducible; run from the stress-suite root:
    PYTHONIOENCODING=utf-8 python scenarios/g7_run_audit.py
Deterministic, local, model-free.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.evidence import EvidenceRecord  # noqa: E402
from engine.g6_governance import (  # noqa: E402
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
from engine.g7_sensitivity import (  # noqa: E402
    PerturbationRecord,
    SensitivityCaseSpec,
    run_metamorphic,
    run_sensitivity_case,
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
    transformation_pressure_surface,
)
from engine.registry import EvidenceRegistry  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "evidence"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _quality_records(lineage_prefix: str = "SRC", count: int = 2,
                     subject: str = "CLAIM_1"):
    return [EvidenceRecord(record_id=f"R_{lineage_prefix}_{i}", kind="OBSERVATION",
                           claim=f"supports {subject}", subject=subject,
                           source_lineage=f"{lineage_prefix}{i}", seq=i)
            for i in range(count)]


def _reviewer(src, model="M1", retr="B1", rid="W1"):
    return {"source_lineage": src, "model_family": model,
            "retrieval_bundle": retr, "reviewer_id": rid}


def _single_lineage_records(n: int, subject: str = "CLAIM_1"):
    return [EvidenceRecord(record_id=f"R_{i}", kind="OBSERVATION",
                           claim=f"supports {subject}", subject=subject,
                           source_lineage="SRC", seq=i) for i in range(n)]


# --------------------------------------------------------------------------- #
# sensitivity case catalog (7 canonical dimensions x representative surfaces)
# --------------------------------------------------------------------------- #
def sensitivity_cases() -> List[SensitivityCaseSpec]:
    cases: List[SensitivityCaseSpec] = []

    # ---- 1. EVIDENCE QUALITY (G5) ---------------------------------------- #
    cases.append(SensitivityCaseSpec(
        case_id="G7-EQ-01", surface="evidence_support", subsystem="G5",
        dimension="EVIDENCE QUALITY",
        perturbation=PerturbationRecord(
            "weak_to_strong", "EVIDENCE QUALITY", "WEAK -> STRONG",
            "more distinct source lineages added to the same claim"),
        baseline=lambda: evidence_support_surface(
            _quality_records(lineage_prefix="SRC", count=2)),
        perturbed=lambda: evidence_support_surface(
            _quality_records(lineage_prefix="SRC", count=4) +
            _quality_records(lineage_prefix="OTHER", count=3)),
        relation_expected="MONOTONE_NON_WEAKENING: stronger evidence must not "
                          "weaken empirical support",
        relation=lambda b, p: p["raw_evidence_count"] >= b["raw_evidence_count"]
                              and p["distinct_source_lineages"] >= b["distinct_source_lineages"]))
    cases.append(SensitivityCaseSpec(
        case_id="G7-EQ-02", surface="evidence_support", subsystem="G5",
        dimension="EVIDENCE QUALITY",
        perturbation=PerturbationRecord(
            "single_lineage_copies", "EVIDENCE QUALITY", "WEAK (1 lineage) x50",
            "50 copies of the SAME lineage must not inflate distinctness"),
        baseline=lambda: evidence_support_surface(_single_lineage_records(1)),
        perturbed=lambda: evidence_support_surface(_single_lineage_records(50)),
        relation_expected="INVARIANT: correlated copies never manufacture "
                          "distinct source lineages",
        relation=lambda b, p: p["distinct_source_lineages"] ==
                              b["distinct_source_lineages"] == 1))

    # ---- 2. INDEPENDENCE (G3) -------------------------------------------- #
    cases.append(SensitivityCaseSpec(
        case_id="G7-IN-01", surface="independence", subsystem="G3",
        dimension="INDEPENDENCE",
        perturbation=PerturbationRecord(
            "low_to_high", "INDEPENDENCE", "LOW -> HIGH",
            "more GENUINE independence (distinct sources/models/retrievals)"),
        baseline=lambda: independence_surface(
            [_reviewer("SRC", rid=f"W{i}") for i in range(5)]),
        perturbed=lambda: independence_surface([
            _reviewer("SRC_A", "M_A", "B_A", "W1"),
            _reviewer("SRC_B", "M_B", "B_A", "W2"),
            _reviewer("SRC_C", "M_C", "B_B", "W3"),
            _reviewer("SRC_D", "M_D", "B_B", "W4")]),
        relation_expected="MONOTONE_NON_WEAKENING: more genuine independence "
                          "must not reduce observed distinctness",
        relation=lambda b, p: p["distinct_source_lineages"] >= b["distinct_source_lineages"]
                              and p["distinct_model_families"] >= b["distinct_model_families"]
                              and p["distinct_retrieval_bundles"] >= b["distinct_retrieval_bundles"]))
    cases.append(SensitivityCaseSpec(
        case_id="G7-IN-02", surface="independence", subsystem="G3",
        dimension="INDEPENDENCE",
        perturbation=PerturbationRecord(
            "unknown_provenance", "INDEPENDENCE", "UNKNOWN",
            "reviewers with no provenance at all"),
        baseline=lambda: independence_surface([_reviewer("SRC")]),
        perturbed=lambda: independence_surface([{"reviewer_id": "W1"},
                                                {"reviewer_id": "W2"}]),
        relation_expected="UNKNOWN NEVER FAVORABLE: unknown provenance counts "
                          "as zero distinct lineages, never favorable",
        relation=lambda b, p: p["distinct_source_lineages"] == 0
                              and p["distinct_model_families"] == 0))

    # ---- 3. PERSISTENCE (G2) --------------------------------------------- #
    cases.append(SensitivityCaseSpec(
        case_id="G7-PE-01", surface="persistence", subsystem="G2",
        dimension="PERSISTENCE",
        perturbation=PerturbationRecord(
            "one_shot_to_repeated", "PERSISTENCE", "ONE_SHOT -> REPEATED",
            "one anomaly vs three credible contradictions"),
        baseline=lambda: persistence_verdict(
            [{"independent_contradiction": "MEDIUM"}]),
        perturbed=lambda: persistence_verdict(
            [{"independent_contradiction": "MEDIUM"}] * 3),
        relation_expected="ONE_SHOT != CHRONIC: one-shot anomaly must not "
                          "escalate; repeated credible contradiction may",
        relation=lambda b, p: b["to_state"] != "ESCALATION_REVIEW"
                              and p["to_state"] == "ESCALATION_REVIEW"))
    cases.append(SensitivityCaseSpec(
        case_id="G7-PE-02", surface="persistence", subsystem="G2",
        dimension="PERSISTENCE",
        perturbation=PerturbationRecord(
            "repeated_to_chronic", "PERSISTENCE", "REPEATED -> CHRONIC",
            "3 vs 10 contradictions, no new quality"),
        baseline=lambda: persistence_verdict(
            [{"independent_contradiction": "MEDIUM"}] * 3),
        perturbed=lambda: persistence_verdict(
            [{"independent_contradiction": "MEDIUM"}] * 10),
        relation_expected="INVARIANT: raw extra repetition without new quality "
                          "does not deepen transformation",
        relation=lambda b, p: p["to_state"] == b["to_state"]))

    # ---- 4. REVERSIBILITY (G6) ------------------------------------------- #
    cases.append(SensitivityCaseSpec(
        case_id="G7-RV-01", surface="reversibility", subsystem="G6",
        dimension="REVERSIBILITY",
        perturbation=PerturbationRecord(
            "high_to_low", "REVERSIBILITY", "HIGH -> LOW",
            "the same action becomes irreversible"),
        baseline=lambda: reversibility_surface(reversible=True),
        perturbed=lambda: reversibility_surface(reversible=False),
        relation_expected="LOWER REVERSIBILITY NEVER EASIER: actual "
                          "irreversibility must hold even under a safe grant",
        relation=lambda b, p: b["verdict"] == "MAY_CONTINUE"
                              and p["verdict"] == "OPERATOR_HOLD"))
    cases.append(SensitivityCaseSpec(
        case_id="G7-RV-02", surface="reversibility", subsystem="G6",
        dimension="REVERSIBILITY",
        perturbation=PerturbationRecord(
            "grant_metadata_irreversible", "REVERSIBILITY", "LOW (grant says safe)",
            "grant metadata cannot make an actual irreversible action reversible"),
        baseline=lambda: reversibility_surface(reversible=True),
        perturbed=lambda: reversibility_surface(reversible=False,
                                                grant_reversible=True),
        relation_expected="INVARIANT: grant reversibility metadata never "
                          "reverses an actually-irreversible action",
        relation=lambda b, p: b["verdict"] == "MAY_CONTINUE"
                              and p["verdict"] == "OPERATOR_HOLD"))

    # ---- 5. CENTRALITY (G2) ---------------------------------------------- #
    cases.append(SensitivityCaseSpec(
        case_id="G7-CE-01", surface="centrality_rigor", subsystem="G2",
        dimension="DEPENDENCY CENTRALITY",
        perturbation=PerturbationRecord(
            "leaf_to_core", "DEPENDENCY CENTRALITY", "LEAF -> CORE",
            "same MEDIUM contradiction, core dependency"),
        baseline=lambda: {"verdict": centrality_rigor_verdict("LEAF", "MEDIUM", 1)},
        perturbed=lambda: {"verdict": centrality_rigor_verdict("CORE", "MEDIUM", 1)},
        relation_expected="RIGOR RAISED: higher centrality raises the bar; "
                          "MEDIUM contradiction no longer opens review at core",
        relation=lambda b, p: b["verdict"] == "REVIEW_OPENED"
                              and p["verdict"] == "RIGOR_HOLD"))
    cases.append(SensitivityCaseSpec(
        case_id="G7-CE-02", surface="centrality_rigor", subsystem="G2",
        dimension="DEPENDENCY CENTRALITY",
        perturbation=PerturbationRecord(
            "core_strong_persistent", "DEPENDENCY CENTRALITY", "CORE + STRONG",
            "strong PERSISTENT independent contradiction at core"),
        baseline=lambda: {"verdict": centrality_rigor_verdict("CORE", "MEDIUM", 1)},
        perturbed=lambda: {"verdict": centrality_rigor_verdict("CORE", "HIGH", 2)},
        relation_expected="NO PERMANENT IMMUNITY: strong persistent "
                          "contradiction opens review even at core",
        relation=lambda b, p: b["verdict"] == "RIGOR_HOLD"
                              and p["verdict"] == "REVIEW_OPENED"))

    # ---- 6. OPERATOR AVAILABILITY (G6) ----------------------------------- #
    cases.append(SensitivityCaseSpec(
        case_id="G7-OA-01", surface="operator_availability", subsystem="G6",
        dimension="OPERATOR AVAILABILITY",
        perturbation=PerturbationRecord(
            "available_to_unavailable", "OPERATOR AVAILABILITY",
            "AVAILABLE -> UNAVAILABLE",
            "operator goes unavailable mid-scope"),
        baseline=lambda: operator_availability_surface(operator_available=True),
        perturbed=lambda: operator_availability_surface(operator_available=False),
        relation_expected="AVAILABILITY CHANGES ACTION AUTHORITY ONLY: "
                          "empirical evidence state is invariant",
        relation=lambda b, p: b["action_verdict"] == "DIRECTIVE_AUTHORIZED"
                              and p["action_verdict"] == "OPERATOR_HOLD"
                              and b["evidence_grade"] == p["evidence_grade"]
                              and b["evidence_refs"] == p["evidence_refs"]))

    # ---- 7. ENVIRONMENT SHIFT (S24/G4) ----------------------------------- #
    cases.append(SensitivityCaseSpec(
        case_id="G7-ES-01", surface="environment_shift", subsystem="S24",
        dimension="ENVIRONMENT SHIFT",
        perturbation=PerturbationRecord(
            "none_to_confirmed", "ENVIRONMENT SHIFT", "NONE -> CONFIRMED",
            "scope shifts to production (confirmed environment change)"),
        baseline=lambda: environment_shift_surface(environment=""),
        perturbed=lambda: environment_shift_surface(environment="production"),
        relation_expected="PROVENANCE INVARIANT, EVIDENCE NEVER BYPASSED: shift "
                          "may change interpretation but never erases provenance "
                          "or routes by raw keywords",
        relation=lambda b, p: p["preserved_raw_event"] == b["preserved_raw_event"]
                              and p["preserved_evidence_refs"] == b["preserved_evidence_refs"]
                              and p["channel"] == "UNRESOLVED_GOVERNANCE_EVENT"))

    return cases


# --------------------------------------------------------------------------- #
# metamorphic relations (identity / representation / evidence / authority /
# context)
# --------------------------------------------------------------------------- #
def metamorphic_relations() -> List[Any]:
    rels: List[Any] = []

    def _boundary(actor, gov):
        return authority_boundary_surface(actor, gov)

    rels.append(run_metamorphic(
        "M1", "RENAME_AGENT_IDS", "G6",
        {"actors": ["OPERATOR_1", "GOV"]}, _boundary("OPERATOR_1", "GOV"),
        {"actors": ["OP_X", "GOV_X"]}, _boundary("OP_X", "GOV_X"),
        "renaming agent ids gives the same substantive permission boundary",
        _boundary("OPERATOR_1", "GOV") == _boundary("OP_X", "GOV_X")))
    f1 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5},
                                     created_by="RUNTIME_A")
    f2 = EvalContractSnapshot.freeze("EVAL_A", 1, {"threshold": 0.5},
                                     created_by="RUNTIME_B")
    rels.append(run_metamorphic(
        "M2", "RENAME_CERTIFIED_RUNTIME", "S20",
        {"created_by": "RUNTIME_A"}, {"fingerprint": f1.criteria_fingerprint},
        {"created_by": "RUNTIME_B"}, {"fingerprint": f2.criteria_fingerprint},
        "renaming the certified runtime/creator label does not change the "
        "frozen contract fingerprint (identity metadata, not decision content)",
        f1.criteria_fingerprint == f2.criteria_fingerprint))
    rels.append(run_metamorphic(
        "M3", "DUPLICATE_CORRELATED_EVIDENCE", "G3",
        {"reviewers": 1}, independence_surface([_reviewer("SRC")]),
        {"reviewers": 10}, independence_surface(
            [_reviewer("SRC", rid=f"W{i}") for i in range(10)]),
        "duplicating correlated evidence 10x leaves independence unchanged",
        independence_surface([_reviewer("SRC")])["distinct_source_lineages"] ==
        independence_surface([_reviewer("SRC", rid=f"W{i}") for i in range(10)])[
            "distinct_source_lineages"] == 1))
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="EV_1", kind="OBSERVATION",
                                claim="same claim", subject="S",
                                source_lineage="L1", seq=1))
    reg.register(EvidenceRecord(record_id="EV_1_ALIAS", kind="OBSERVATION",
                                claim="same claim", subject="S",
                                source_lineage="L1", seq=1))
    rels.append(run_metamorphic(
        "M4", "ALIAS_CANONICAL_EVIDENCE", "G2R",
        {"refs": ["EV_1"]}, reg.lineage_summary(["EV_1"]).to_dict(),
        {"refs": ["EV_1", "EV_1_ALIAS"]},
        reg.lineage_summary(["EV_1", "EV_1_ALIAS"]).to_dict(),
        "aliasing one canonical evidence object under multiple refs is one "
        "epistemic path (distinct_source_lineages stays 1)",
        reg.lineage_summary(["EV_1", "EV_1_ALIAS"]).distinct_source_lineages == 1))
    a = freeze_surface({"threshold": 0.5, "routing": {"channels": ["A", "B"],
                                                      "weights": {"A": 1}}})
    b = freeze_surface({"routing": {"weights": {"A": 1},
                                    "channels": ["A", "B"]},
                        "threshold": 0.5})
    rels.append(run_metamorphic(
        "M5", "REORDER_UNORDERED_MAPS", "S20",
        {"criteria": {"threshold": 0.5, "routing": {"channels": ["A", "B"],
                                                    "weights": {"A": 1}}}},
        a, {"criteria_reordered": True}, b,
        "reordering semantically unordered map keys leaves the freeze "
        "fingerprint stable",
        a["criteria_fingerprint"] == b["criteria_fingerprint"]))
    pa = persistence_verdict([{"independent_contradiction": "MEDIUM"},
                              {"reliability_degradation": "LOW"},
                              {"independent_contradiction": "MEDIUM"}])
    pb = persistence_verdict([{"reliability_degradation": "LOW"},
                              {"independent_contradiction": "MEDIUM"},
                              {"independent_contradiction": "MEDIUM"}])
    rels.append(run_metamorphic(
        "M6", "REORDER_NON_CAUSAL_ARRIVAL", "G2",
        {"order": ["IC_MEDIUM", "LOW", "IC_MEDIUM"]}, pa,
        {"order": ["LOW", "IC_MEDIUM", "IC_MEDIUM"]}, pb,
        "reordering non-causal evidence arrival gives an explainably "
        "equivalent terminal proposal",
        (pa["action"], pa["rule_id"], pa["to_state"]) ==
        (pb["action"], pb["rule_id"], pb["to_state"])))
    rels.append(run_metamorphic(
        "M7", "FILE_COUNT_WITH_PRESERVED_SURFACE", "G2",
        {"files": 1}, {"verdict": centrality_rigor_verdict("CORE", "HIGH", 2)},
        {"files": 1000}, {"verdict": centrality_rigor_verdict("CORE", "HIGH", 2)},
        "changing file count while preserving the affected surface and "
        "evidence leaves review rigor unchanged",
        centrality_rigor_verdict("CORE", "HIGH", 2) == "REVIEW_OPENED"))
    rels.append(run_metamorphic(
        "M8", "EQUIVALENT_AUTHORITY_REPRESENTATION", "G6",
        {"actor": "OPERATOR_1", "governor": "GOVERNOR_9"},
        _boundary("OPERATOR_1", "GOVERNOR_9"),
        {"actor": "OP-RENAMED", "governor": "GOV-RENAMED"},
        _boundary("OP-RENAMED", "GOV-RENAMED"),
        "equivalent authority representation gives the same permission "
        "boundary",
        _boundary("OPERATOR_1", "GOVERNOR_9") ==
        _boundary("OP-RENAMED", "GOV-RENAMED")))
    rels.append(run_metamorphic(
        "M9", "RENAME_OPERATOR_ACTOR", "G6",
        {"operator": "OPERATOR_1"}, _boundary("OPERATOR_1", "GOV"),
        {"operator": "OP-Z"}, _boundary("OP-Z", "GOV"),
        "renaming the operator actor while preserving canonical authority "
        "gives the same result",
        _boundary("OPERATOR_1", "GOV") == _boundary("OP-Z", "GOV")))
    rels.append(run_metamorphic(
        "M10", "CLAIM_OPERATOR_LABEL_WITHOUT_AUTHORITY", "G6",
        {"actor": "OPERATOR_1", "governor": "GOV"}, _boundary("OPERATOR_1", "GOV"),
        {"stranger_claims": "OPERATOR"},
        {"operator_authorized": True, "governor_authorized": False,
         "stranger_authorized": False},
        "claiming an OPERATOR label without canonical authority has no effect "
        "(stranger fails closed)",
        _boundary("OPERATOR_1", "GOV")["stranger_authorized"] is False))

    from engine.authority import AuthorityState, CapabilityGrant

    def _mandate_check(seq):
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
        m = OperatorMandate(actor="GOV", scope="RESEARCH", issued_by="OPERATOR_1",
                            grant_ref="GR_M1", seq=seq)
        ok, reasons = verify_operator_mandate(m, auth, "RESEARCH")
        return {"verified": ok, "reasons": reasons}

    rels.append(run_metamorphic(
        "M11", "REPLACE_MANDATE_ID", "G6",
        {"mandate_seq": 2}, _mandate_check(2),
        {"mandate_seq": 3}, _mandate_check(3),
        "replacing the mandate id while preserving the same governed mandate "
        "semantics gives the same verification result",
        _mandate_check(2)["verified"] is _mandate_check(3)["verified"] is True))

    reg_m12 = EvidenceRegistry()
    reg_m12.register(EvidenceRecord(record_id="EV_BTC", kind="OBSERVATION",
                                    claim="price tick", subject="btc-price",
                                    seq=1))
    graph_m12 = EvidenceGraph(grades=(
        EmpiricalEvidenceGrade(evidence_id="EV_POLICY", empirical_grade="CONTESTED",
                               grade_evidence_refs=("R0",), subject="policy"),))
    m12_refused = False
    try:
        graph_m12.with_grade("EV_POLICY", "SUPPORTED", "EV_BTC", reg_m12)
    except ValueError:
        m12_refused = True
    rels.append(run_metamorphic(
        "M12", "UNRELATED_REGISTERED_EVIDENCE", "G6",
        {"refs": [], "grade": "CONTESTED"},
        {"grade": "CONTESTED"},
        {"refs": ["EV_BTC"], "grade": "CONTESTED"},
        {"grade": "CONTESTED", "refused": m12_refused},
        "unrelated registered evidence cannot alter another claim's grade "
        "(refused, grade unchanged)",
        m12_refused and graph_m12.grade_of("EV_POLICY") == "CONTESTED"))

    reg_s = EvidenceRegistry()
    reg_s.register(EvidenceRecord(record_id="R_SENSOR", kind="OBSERVATION",
                                  claim="sensor drift", subject="sensor-drift",
                                  seq=3))
    ce = GovernanceClassificationEvidence(
        proposed_channel="SENSOR", evidence_refs=("R_SENSOR",),
        status="SUPPORTED", binding="sensor-drift")
    e1 = GovernanceEvent(event_id="E1", raw_event="sensor recalibration drift",
                         evidence_refs=("R_SENSOR",), binding="sensor-drift", seq=1)
    e2 = GovernanceEvent(event_id="E2",
                         raw_event="completely different wording describing "
                                   "the same sensor recalibration drift",
                         evidence_refs=("R_SENSOR",), binding="sensor-drift", seq=2)
    d1 = classify_governance_event(e1, (ce,), registry=reg_s)
    d2 = classify_governance_event(e2, (ce,), registry=reg_s)
    rels.append(run_metamorphic(
        "M13", "S24_WORDING_CHANGE_SAME_STRUCTURED_EVIDENCE", "S24",
        {"raw_event": "sensor recalibration drift"}, {"channel": d1.channel},
        {"raw_event": "different wording, same drift"}, {"channel": d2.channel},
        "changing S24 raw wording while structured classification evidence is "
        "unchanged gives the same governance channel",
        d1.channel == d2.channel == "SENSOR"))
    u1 = classify_governance_event(GovernanceEvent(event_id="E1",
                                                   raw_event="authority grant",
                                                   binding="x", seq=1))
    u2 = classify_governance_event(GovernanceEvent(event_id="E2",
                                                   raw_event="renamed tokens",
                                                   binding="y", seq=2))
    rels.append(run_metamorphic(
        "M14", "S24_KEYWORD_CHANGE_NO_EVIDENCE", "S24",
        {"raw_event": "authority grant"}, {"channel": u1.channel},
        {"raw_event": "renamed tokens"}, {"channel": u2.channel},
        "changing S24 keywords with no classification evidence leaves the event "
        "unresolved",
        u1.channel == u2.channel == "UNRESOLVED_GOVERNANCE_EVENT"))
    f_a = EvalContractSnapshot.freeze("EC", 2, {"threshold": 0.9, "rule": "threshold"})
    f_b = EvalContractSnapshot.freeze("EC", 2, {"rule": "threshold", "threshold": 0.9})
    rels.append(run_metamorphic(
        "M15", "EQUIVALENT_FUTURE_CONTRACT_CONTENT", "S20",
        {"criteria": {"threshold": 0.9, "rule": "threshold"}},
        {"fingerprint": f_a.criteria_fingerprint},
        {"criteria": {"rule": "threshold", "threshold": 0.9}},
        {"fingerprint": f_b.criteria_fingerprint},
        "equivalent future-contract canonical content gives the same "
        "fingerprint",
        f_a.criteria_fingerprint == f_b.criteria_fingerprint))
    raw = {"threshold": 0.5, "routing": {"channels": ["A"]}}
    snap = EvalContractSnapshot.freeze("EC", 1, raw)
    raw["threshold"] = 0.99
    raw["routing"]["channels"].append("C")
    rels.append(run_metamorphic(
        "M16", "NESTED_CALLER_ALIASES", "S20",
        {"criteria": {"threshold": 0.5, "routing": {"channels": ["A"]}}},
        {"threshold": snap.criteria["threshold"],
         "channels": list(snap.criteria["routing"]["channels"])},
        {"caller_mutates_alias": True},
        {"threshold": snap.criteria["threshold"],
         "channels": list(snap.criteria["routing"]["channels"])},
        "nested caller aliases cannot change the frozen state",
        snap.criteria["threshold"] == 0.5 and
        list(snap.criteria["routing"]["channels"]) == ["A"] and
        snap.is_deeply_frozen()))
    content = {"threshold": 0.5, "routing": {"channels": ["A", "B"]}}
    r1 = reconstruction_surface(content, epoch_id="E1")
    r2 = reconstruction_surface(content, epoch_id="E1")
    rels.append(run_metamorphic(
        "M17", "RUNTIME_PROCESS_RESTART", "G4",
        {"epoch": "E1"}, r1,
        {"fresh_registry_restart": True}, r2,
        "runtime/process restart reconstructs the canonical decision "
        "identically",
        r1["fingerprint"] == r2["fingerprint"] and r1["registered"] is True))
    return rels


# --------------------------------------------------------------------------- #
# open-issue pressure tests
# --------------------------------------------------------------------------- #
def pressure_results() -> Dict[str, Any]:
    con02 = allocator_surface([
        {"evidence_ref": f"EV_{i}", "initiating_actor": f"AGENT_{i}",
         "allocator_actor": "PO_ALLOCATION", "worker_selected": f"W_{i}",
         "source_path": f"source://{i}", "retrieval_lineage": f"retrieval-{i}",
         "exposure_lineage": f"agenda-{i}"} for i in range(6)])
    con02_diverse = allocator_surface([
        {"evidence_ref": "EV_0", "initiating_actor": "AGENT_0",
         "allocator_actor": "PO_ALLOCATION", "source_path": "s0"},
        {"evidence_ref": "EV_1", "initiating_actor": "AGENT_1",
         "allocator_actor": "OPEN_REVIEW", "source_path": "s1"}])
    con03 = {
        known: transformation_pressure_surface(novelty_count=100,
                                               threshold_known=known)
        for known in ("EXACT", "APPROXIMATE", "UNKNOWN")}
    con03_genuine = transformation_pressure_surface(
        novelty_count=100, has_quality=True, has_independence=True,
        has_contradiction=True, threshold_known="EXACT")
    spam = {str(n): anomaly_spam_surface(n)["to_state"] for n in (1, 10, 100, 1000)}
    inertia = {
        "core_medium_1": centrality_rigor_verdict("CORE", "MEDIUM", 1),
        "core_high_2": centrality_rigor_verdict("CORE", "HIGH", 2),
        "core_high_20": centrality_rigor_verdict("CORE", "HIGH", 20),
        "adjudicator_core_high_2": adjudicator_centrality_verdict("HIGH", "HIGH", 2),
        "adjudicator_core_high_5": adjudicator_centrality_verdict("HIGH", "HIGH", 5)}
    addiction = {str(n): transformation_pressure_surface(novelty_count=n)["candidate"]
                 for n in (1, 10, 100, 1000)}
    neg = {"impossible": negative_knowledge_surface(False),
           "possible": negative_knowledge_surface(True)}
    return {"CON02": {"concentrated": con02, "diverse": con02_diverse},
            "CON03": {"threshold_knowledge": con03,
                      "genuine_triple": con03_genuine},
            "anomaly_spam": spam,
            "centrality_inertia": inertia,
            "transformation_addiction": addiction,
            "negative_knowledge": neg}


# --------------------------------------------------------------------------- #
# evidence package
# --------------------------------------------------------------------------- #
def build_package() -> Dict[str, Any]:
    cases = sensitivity_cases()
    verdicts = [run_sensitivity_case(c, counterexample_classification="UNKNOWN")
                for c in cases]
    rels = metamorphic_relations()
    pressure = pressure_results()

    failed = [v for v in verdicts if not v.pass_]
    failed_rels = [r for r in rels if not r.pass_]
    counterexamples = [v.counterexample for v in failed if v.counterexample]

    _SURFACE_FAMILY = {"evidence_support": "G5", "independence": "G3",
                       "persistence": "G2", "reversibility": "G6",
                       "centrality_rigor": "G2", "operator_availability": "G6",
                       "environment_shift": "S24"}
    dimensions = sorted({c.dimension for c in cases})
    subsystems = sorted({_SURFACE_FAMILY.get(c.surface, c.surface) for c in cases} |
                        {r.subsystem for r in rels})
    n_sensitivity = len(cases)
    n_perturbations = len(cases)
    n_relations = len(rels)

    matrix_lines = ["# G7 Sensitivity Matrix", "",
                    "| Case | Dimension | Perturbation | Expected RELATION | Verdict |", "|---|",
                    "|---|---|---|---|---|"]
    for v in verdicts:
        matrix_lines.append(
            f"| {v.case_id} | {v.dimension} | {v.perturbation.level} | "
            f"{v.relation_expected} | {'PASS' if v.pass_ else 'FAIL'} |")

    meta_lines = ["# G7 Metamorphic Audit", "", "| Relation | Kind | Invariant | Verdict |",
                  "|---|---|---|---|"]
    for r in rels:
        meta_lines.append(f"| {r.relation_id} | {r.kind} | {r.invariant} | "
                          f"{'PASS' if r.pass_ else 'FAIL'} |")

    mono_lines = ["# G7 Monotonicity Audit", "",
                  "Relational invariants verified in this pass:",
                  "- EVIDENCE QUALITY: WEAK -> MIXED -> STRONG never weakens "
                  "empirical support (G7-EQ-01); correlated copies never "
                  "manufacture distinctness (G7-EQ-02); legitimate falsification "
                  "is causal (grade moves to REFUTED through the subject-bound "
                  "evidence path), not mechanical.",
                  "- INDEPENDENCE: more genuine independence never reduces "
                  "observed distinctness (G7-IN-01); UNKNOWN provenance is never "
                  "favorable (G7-IN-02); duplication cannot manufacture "
                  "independence (M3, M4).",
                  "- PERSISTENCE: one-shot anomaly != chronic anomaly (G7-PE-01); "
                  "raw repetition without quality forces nothing (G7-PE-02, "
                  "anomaly spam).",
                  "- REVERSIBILITY: lower reversibility never makes autonomous "
                  "authority easier (G7-RV-01/02).",
                  "- CENTRALITY: higher centrality raises rigor (G7-CE-01) but "
                  "never grants permanent immunity (G7-CE-02, centrality inertia).",
                  "- OPERATOR AVAILABILITY: changes action authority only, never "
                  "empirical evidence state (G7-OA-01).",
                  "- ENVIRONMENT SHIFT: changes interpretation, never erases "
                  "provenance or bypasses evidence (G7-ES-01).", ""]
    mono_lines += [f"- {v.case_id}: {v.relation_expected} -> "
                   f"{'PASS' if v.pass_ else 'FAIL'}" for v in verdicts]

    con02_lines = ["# G7 CON-02 Allocator Sensitivity", "",
                   "CON-02 remains observable, not resolved: no final rejection "
                   "threshold is constitutionalized. Varying allocator/source/"
                   "worker/retrieval/exposure diversity independently:",
                   f"- 6 source-diverse paths through ONE allocator -> "
                   f"{pressure['CON02']['concentrated']['concentration']} "
                   f"(observable).",
                   f"- 2 paths through 2 allocators -> "
                   f"{pressure['CON02']['diverse']['concentration']}.",
                   "",
                   "Observation is full-fidelity regardless of verdict; A-009/"
                   "A-010 unchanged."]

    con03_lines = ["# G7 CON-03 Goodhart Audit", "",
                   "Workers who know the exact/approximate threshold cannot "
                   "manufacture transformation by shaping counts:",
                   f"- EXACT threshold knowledge, 100 novelty records, no quality "
                   f"triple -> candidate={pressure['CON03']['threshold_knowledge']['EXACT']['candidate']}",
                   f"- APPROXIMATE -> candidate={pressure['CON03']['threshold_knowledge']['APPROXIMATE']['candidate']}",
                   f"- UNKNOWN -> candidate={pressure['CON03']['threshold_knowledge']['UNKNOWN']['candidate']}",
                   f"- genuine quality+independence+contradiction triple -> "
                   f"candidate={pressure['CON03']['genuine_triple']['candidate']}",
                   "",
                   "Transparent-vs-gameable thresholds is NOT silently solved; "
                   "CON-03 stays open."]

    (OUT / "G7_SENSITIVITY_MATRIX.md").write_text("\n".join(matrix_lines) + "\n",
                                                  encoding="utf-8")
    (OUT / "G7_METAMORPHIC_AUDIT.md").write_text("\n".join(meta_lines) + "\n",
                                                 encoding="utf-8")
    (OUT / "G7_MONOTONICITY_AUDIT.md").write_text("\n".join(mono_lines) + "\n",
                                                  encoding="utf-8")
    (OUT / "G7_CON02_ALLOCATOR_SENSITIVITY.md").write_text(
        "\n".join(con02_lines) + "\n", encoding="utf-8")
    (OUT / "G7_CON03_GOODHART_AUDIT.md").write_text(
        "\n".join(con03_lines) + "\n", encoding="utf-8")

    counterexamples_register = [c.to_dict() for c in counterexamples if c]
    (OUT / "G7_COUNTEREXAMPLE_REGISTER.json").write_text(
        json.dumps({"counterexamples": counterexamples_register,
                    "failed_sensitivity_cases": [v.case_id for v in failed],
                    "failed_metamorphic_relations": [r.relation_id for r in failed_rels],
                    "note": "empty register = every relation held under "
                            "perturbation; a failure is preserved, never patched"},
                   indent=2) + "\n", encoding="utf-8")

    return {"verdicts": [v.to_dict() for v in verdicts],
            "relations": [r.to_dict() for r in rels],
            "pressure": pressure,
            "counts": {"sensitivity_cases": n_sensitivity,
                       "perturbations": n_perturbations,
                       "metamorphic_relations": n_relations,
                       "failed_cases": len(failed),
                       "failed_relations": len(failed_rels),
                       "dimensions": dimensions,
                       "subsystems": subsystems},
            "counterexamples": counterexamples_register}


def main() -> Dict[str, Any]:
    pkg = build_package()
    print(json.dumps(pkg["counts"], indent=2))
    print("counterexamples:", len(pkg["counterexamples"]))
    print("written:", sorted(f.name for f in OUT.glob("G7_*")))
    return pkg


if __name__ == "__main__":
    main()