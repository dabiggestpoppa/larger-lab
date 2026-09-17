"""G7 — sensitivity + metamorphic audit machinery (STRESS-G7C0).

G7 asks whether the institution keeps the SAME constitutional / epistemic
relationships when NON-ESSENTIAL surface conditions change. It is not
"more scenarios until green": every case below perturbs ONE non-essential
surface at a time and asserts the relational invariant, using minimum
discriminating perturbations (never a blind Cartesian product).

Shared objects (no scenario-id / expected-outcome / fixture-name predicates):

    SensitivityCaseSpec       baseline + perturbed pure surfaces + expected relation
    PerturbationRecord        one non-essential surface change
    BaselineBehaviorFingerprint / PerturbedBehaviorFingerprint
    RelationVerdict           preserves baseline inputs+result, perturbation,
                              perturbed result, relation expected/observed, verdict
    CounterexampleRecord      preserved failing case (never silently patched)

FAILURE CLASSIFICATION (G7-XX): when a relation fails the caller must classify
the cause — TEST CONTRACT WRONG / IMPLEMENTATION BUG / POLICY AMBIGUITY /
ARCHITECTURE CONTRADICTION / EXPECTED NON-INVARIANCE / UNKNOWN — and preserve
the counterexample. If two validated scenarios require incompatible
institutional semantics, that is G8-relevant evidence and blocks G7 PASS.

The surfaces in this module are PURE decision functions. Where they mirror an
engine (EvidenceAdjudicator, EvidenceRegistry lineage, g6 freeze/authority/
hold/classification, allocator ledger, canonical reconstruction), the mirror
semantics are cross-checked against the engine in tests/test_g7_sensitivity.py,
so the audit never asserts a reimplementation that the engine would contradict.
Everything is deterministic, local, model-free, wall-clock-free.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .adjudicate import (
    AdjudicatorPolicy,
    EvidenceAdjudicator,
    EvidenceObservation,
)
from .authority import AuthorityState, AuthorityViolation, CapabilityGrant
from .evidence import EvidenceRecord
from .evalcontract import PhaseEvaluationContract
from .g6_governance import (
    ActionGrantEnvelope,
    ActionRequest,
    AllocatorProvenanceLedger,
    AllocatorProvenanceRecord,
    ConstitutionPermissionRecord,
    ConstitutionalRuleRegistry,
    ConstitutionRule,
    EmpiricalEvidenceGrade,
    EvalContractSnapshot,
    EvidenceGraph,
    GovernanceClassificationEvidence,
    GovernanceEvent,
    apply_operator_directive,
    classify_governance_event,
    execute_under_operator_hold,
)
from .reconstruction import CanonicalArtifact, CanonicalArtifactRegistry
from .registry import EvidenceRegistry

# --------------------------------------------------------------------------- #
# Generic machinery
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PerturbationRecord:
    name: str
    dimension: str
    level: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "dimension": self.dimension,
                "level": self.level, "description": self.description}


@dataclass(frozen=True)
class BaselineBehaviorFingerprint:
    surface: str
    subsystem: str
    description: str
    observables: Dict[str, Any]
    digest: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "digest", deterministic_hex(
            "g7_baseline", self.surface,
            json.dumps(self.observables, sort_keys=True, default=str), length=24))

    def to_dict(self) -> Dict[str, Any]:
        return {"surface": self.surface, "subsystem": self.subsystem,
                "description": self.description, "observables": self.observables,
                "digest": self.digest}


@dataclass(frozen=True)
class CounterexampleRecord:
    counterexample_id: str
    case_id: str
    classification: str            # TEST CONTRACT WRONG / IMPLEMENTATION BUG / POLICY
                                   # AMBIGUITY / ARCHITECTURE CONTRADICTION /
                                   # EXPECTED NON-INVARIANCE / UNKNOWN
    baseline_observables: Dict[str, Any]
    perturbed_observables: Dict[str, Any]
    expected_relation: str
    observed_relation: str
    preserved_evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"counterexample_id": self.counterexample_id, "case_id": self.case_id,
                "classification": self.classification,
                "baseline_observables": self.baseline_observables,
                "perturbed_observables": self.perturbed_observables,
                "expected_relation": self.expected_relation,
                "observed_relation": self.observed_relation,
                "preserved_evidence": self.preserved_evidence}


@dataclass(frozen=True)
class RelationVerdict:
    case_id: str
    surface: str
    subsystem: str
    dimension: str
    perturbation: PerturbationRecord
    baseline_inputs: Dict[str, Any]
    baseline_result: Dict[str, Any]
    perturbed_inputs: Dict[str, Any]
    perturbed_result: Dict[str, Any]
    relation_expected: str
    relation_observed: bool
    pass_: bool
    counterexample: Optional[CounterexampleRecord] = None
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"case_id": self.case_id, "surface": self.surface,
                "subsystem": self.subsystem, "dimension": self.dimension,
                "perturbation": self.perturbation.to_dict(),
                "baseline_inputs": self.baseline_inputs,
                "baseline_result": self.baseline_result,
                "perturbed_inputs": self.perturbed_inputs,
                "perturbed_result": self.perturbed_result,
                "relation_expected": self.relation_expected,
                "relation_observed": self.relation_observed,
                "pass": self.pass_,
                "counterexample": self.counterexample.to_dict()
                if self.counterexample else None,
                "note": self.note}


@dataclass(frozen=True)
class SensitivityCaseSpec:
    case_id: str
    surface: str
    subsystem: str
    dimension: str
    perturbation: PerturbationRecord
    baseline: Callable[[], Dict[str, Any]]
    perturbed: Callable[[], Dict[str, Any]]
    relation_expected: str
    relation: Callable[[Dict[str, Any], Dict[str, Any]], bool]
    baseline_inputs: Callable[[], Dict[str, Any]] = lambda: {}
    perturbed_inputs: Callable[[], Dict[str, Any]] = lambda: {}


def run_sensitivity_case(spec: SensitivityCaseSpec,
                         counterexample_classification: str = "UNKNOWN") -> RelationVerdict:
    """Run one sensitivity case. On FAIL the counterexample is PRESERVED with
    the caller's classification — never silently patched."""
    base_in = spec.baseline_inputs()
    pert_in = spec.perturbed_inputs()
    base_res = spec.baseline()
    pert_res = spec.perturbed()
    ok = spec.relation(base_res, pert_res)
    counter = None
    if not ok:
        counter = CounterexampleRecord(
            counterexample_id=deterministic_hex(
                "g7_counter", spec.case_id,
                json.dumps(base_res, sort_keys=True, default=str),
                json.dumps(pert_res, sort_keys=True, default=str), length=20),
            case_id=spec.case_id, classification=counterexample_classification,
            baseline_observables=base_res, perturbed_observables=pert_res,
            expected_relation=spec.relation_expected,
            observed_relation="FAIL", preserved_evidence={"baseline_inputs": base_in,
                                                          "perturbed_inputs": pert_in})
    return RelationVerdict(
        case_id=spec.case_id, surface=spec.surface, subsystem=spec.subsystem,
        dimension=spec.dimension, perturbation=spec.perturbation,
        baseline_inputs=base_in, baseline_result=base_res,
        perturbed_inputs=pert_in, perturbed_result=pert_res,
        relation_expected=spec.relation_expected, relation_observed=ok,
        pass_=ok, counterexample=counter)


@dataclass(frozen=True)
class MetamorphicRelation:
    relation_id: str
    kind: str
    subsystem: str
    source_inputs: Dict[str, Any]
    source_result: Dict[str, Any]
    transformed_inputs: Dict[str, Any]
    transformed_result: Dict[str, Any]
    invariant: str
    pass_: bool
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"relation_id": self.relation_id, "kind": self.kind,
                "subsystem": self.subsystem,
                "source_inputs": self.source_inputs,
                "source_result": self.source_result,
                "transformed_inputs": self.transformed_inputs,
                "transformed_result": self.transformed_result,
                "invariant": self.invariant, "pass": self.pass_, "note": self.note}


def run_metamorphic(relation_id: str, kind: str, subsystem: str,
                    source_inputs: Dict[str, Any], source_result: Dict[str, Any],
                    transformed_inputs: Dict[str, Any], transformed_result: Dict[str, Any],
                    invariant: str, pass_: bool, note: str = "") -> MetamorphicRelation:
    return MetamorphicRelation(relation_id=relation_id, kind=kind, subsystem=subsystem,
                              source_inputs=source_inputs, source_result=source_result,
                              transformed_inputs=transformed_inputs,
                              transformed_result=transformed_result,
                              invariant=invariant, pass_=pass_, note=note)


# --------------------------------------------------------------------------- #
# Surface: G2 centrality rigor (mirrors EvidenceAdjudicator G2R-01 semantics)
# --------------------------------------------------------------------------- #
_CENTRALITY_BAR = {"LEAF": "MEDIUM", "MID": "MEDIUM", "CORE": "HIGH"}
_GRADE_ORDER = ("LOW", "MEDIUM", "HIGH")


def _meets(observed: str, required: str) -> bool:
    return _GRADE_ORDER.index(observed) >= _GRADE_ORDER.index(required)


def centrality_rigor_verdict(centrality: str, contradiction_grade: str,
                             persistence: int) -> str:
    """G2R-01 semantics: dependency centrality raises the independent-
    contradiction bar (rigor), NEVER grants permanent immunity. A strong
    PERSISTENT independent contradiction must still open review at any
    centrality. Returns REVIEW_OPENED | RIGOR_HOLD."""
    if centrality not in _CENTRALITY_BAR:
        raise ValueError(f"unknown centrality {centrality!r}")
    if contradiction_grade not in _GRADE_ORDER:
        raise ValueError(f"unknown contradiction grade {contradiction_grade!r}")
    bar = _CENTRALITY_BAR[centrality]
    if not _meets(contradiction_grade, bar):
        return "RIGOR_HOLD"
    # core requires the contradiction to be PERSISTENT before review opens
    required_persistence = 2 if centrality == "CORE" else 1
    if persistence >= required_persistence:
        return "REVIEW_OPENED"
    return "RIGOR_HOLD"


def _adjudicator_policy_for_centrality() -> AdjudicatorPolicy:
    return AdjudicatorPolicy.from_data({
        "policy_id": "g7-centrality",
        "version_tag": "G7V1",
        "rules": [
            {"rule_id": "escalate.core", "to_state": "ESCALATION_REVIEW",
             "all_of": [{"independent_contradiction": "HIGH"}],
             "persistence": {"channel": "independent_contradiction",
                             "grade": "HIGH", "minimum_observations": 2},
             "dependency": {"min_centrality": "HIGH",
                            "requires_stronger_review": True}},
            {"rule_id": "watch.any", "to_state": "WATCH",
             "any_of": [{"independent_contradiction": "MEDIUM"}]},
        ],
    })


def adjudicator_centrality_verdict(centrality: str, contradiction_grade: str,
                                   persistence: int) -> str:
    """Ground-truth cross-check surface using the REAL EvidenceAdjudicator.
    `dependency_centrality` uses the engine's canonical grade vocabulary
    (LOW/MEDIUM/HIGH maps to LEAF/MID/CORE). The policy declares ONE
    dependency-bearing escalation rule (min_centrality HIGH +
    requires_stronger_review): a HIGH-centrality observation needs HIGH
    independent contradiction (rigor), and once it has it persistently the
    transition opens (no permanent immunity). Returns ESCALATION_REVIEW-based
    REVIEW_OPENED / RIGOR_HOLD."""
    a = EvidenceAdjudicator(_adjudicator_policy_for_centrality(),
                            _frozen_contract("G7V1"))
    for i in range(persistence):
        a.observe(EvidenceObservation(
            seq=i + 1,
            vector={"independent_contradiction": contradiction_grade,
                    "dependency_centrality": centrality}))
    prop = a.propose(current_phase="STABLE")
    if prop.action == "TRANSITION" and prop.to_state == "ESCALATION_REVIEW":
        return "REVIEW_OPENED"
    return "RIGOR_HOLD"


def _frozen_contract(tag: str = "G7V1") -> PhaseEvaluationContract:
    c = PhaseEvaluationContract.make(1, version_tag=tag)
    c.freeze()
    return c


# --------------------------------------------------------------------------- #
# Surface: evidence quality (G5 family — lineage support must not weaken)
# --------------------------------------------------------------------------- #
def evidence_support_surface(refs: Sequence[str]) -> Dict[str, Any]:
    """Non-scalar lineage support of a claim from registered evidence refs
    (EvidenceRegistry.lineage_summary). Adding QUALITY (more distinct source
    lineages) must not reduce support unless the new evidence legitimately
    contradicts (recorded causally, not mechanically)."""
    reg = EvidenceRegistry()
    for r in refs:
        reg.register(r)
    summary = reg.lineage_summary([r.record_id for r in refs])
    return {"raw_evidence_count": summary.raw_evidence_count,
            "distinct_source_lineages": summary.distinct_source_lineages,
            "distinct_model_lineages": summary.distinct_model_lineages,
            "shared_allocator": summary.shared_allocator,
            "shared_retrieval": summary.shared_retrieval}


# --------------------------------------------------------------------------- #
# Surface: independence (G3 family — duplication cannot manufacture it)
# --------------------------------------------------------------------------- #
def independence_surface(reviewers: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Distinct-lineage accounting over reviewer provenance records:
    {source_lineage, model_family, retrieval_bundle}. More GENUINE
    independence must not reduce distinctness; duplicating a correlated
    reviewer must not increase it."""
    sources = {str(r.get("source_lineage", "")) for r in reviewers if r.get("source_lineage")}
    models = {str(r.get("model_family", "")) for r in reviewers if r.get("model_family")}
    retrievals = {str(r.get("retrieval_bundle", "")) for r in reviewers
                  if r.get("retrieval_bundle")}
    # a reviewer whose provenance is entirely UNKNOWN cannot count as diverse
    return {"raw_reviewers": len(reviewers),
            "distinct_source_lineages": len(sources),
            "distinct_model_families": len(models),
            "distinct_retrieval_bundles": len(retrievals)}


# --------------------------------------------------------------------------- #
# Surface: persistence / anomaly spam (G2 family — count is not transformation)
# --------------------------------------------------------------------------- #
_PERSISTENCE_RULES = [
    {"rule_id": "escalate.persist", "to_state": "ESCALATION_REVIEW",
     "all_of": [{"independent_contradiction": "MEDIUM"}],
     "persistence": {"channel": "independent_contradiction", "grade": "MEDIUM",
                     "minimum_observations": 3}},
    {"rule_id": "watch.any", "to_state": "WATCH",
     "any_of": [{"reliability_degradation": "MEDIUM"},
                {"independent_contradiction": "MEDIUM"}]},
]


def persistence_verdict(observations: Sequence[Mapping[str, str]]) -> Dict[str, Any]:
    """Feed observations (in order) into the REAL EvidenceAdjudicator and
    return the terminal proposal."""
    a = EvidenceAdjudicator(AdjudicatorPolicy.from_data({
        "policy_id": "g7-persistence", "version_tag": "G7V1",
        "rules": _PERSISTENCE_RULES}), _frozen_contract("G7V1"))
    for i, v in enumerate(observations):
        a.observe(EvidenceObservation(seq=i + 1, vector=v))
    prop = a.propose(current_phase="STABLE")
    return {"action": prop.action, "to_state": prop.to_state,
            "rule_id": prop.rule_id, "observation_count": len(observations)}


def anomaly_spam_surface(weak_records: int) -> Dict[str, Any]:
    """Raw count of WEAK records alone must not force transformation."""
    return persistence_verdict([{"reliability_degradation": "LOW"}] * weak_records)


# --------------------------------------------------------------------------- #
# Surface: reversibility (G6 family — lower reversibility never eases authority)
# --------------------------------------------------------------------------- #
def _safe_grant(seq: int = 1, grant_reversible: bool = True) -> ActionGrantEnvelope:
    return ActionGrantEnvelope(grant_id="GR_SAFE", grantee="OP_AGENT",
                               action="sandbox_rebalance_reversible",
                               target_scope="sandbox://portfolio_minor",
                               affected_surface="REVERSIBLE_SANDBOX",
                               reversible=grant_reversible, risk_class="local-write",
                               environment="local-test", issued_seq=seq)


def reversibility_surface(reversible: bool, request_risk: str = "local-write",
                          grant_reversible: bool = True) -> Dict[str, Any]:
    v = execute_under_operator_hold(
        "ACT_1", "OP_AGENT",
        ActionRequest(action="sandbox_rebalance_reversible",
                      target_scope="sandbox://portfolio_minor",
                      affected_surface="REVERSIBLE_SANDBOX",
                      reversible=reversible, risk_class=request_risk,
                      environment="local-test"),
        _safe_grant(grant_reversible=grant_reversible), current_seq=5)
    return {"verdict": v.verdict, "rationale": v.rationale}


# --------------------------------------------------------------------------- #
# Surface: operator availability (G6 family — availability changes action
# authority, NEVER empirical evidence state)
# --------------------------------------------------------------------------- #
def operator_availability_surface(operator_available: bool) -> Dict[str, Any]:
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="MEASURE_1", kind="OBSERVATION",
                                claim="measurement", subject="EV_1", seq=1))
    graph = EvidenceGraph(grades=(
        EmpiricalEvidenceGrade(evidence_id="EV_1", empirical_grade="CONTESTED",
                               grade_evidence_refs=("MEASURE_1",), subject="EV_1"),))
    if operator_available:
        auth = AuthorityState()
        auth.seed_level("OPERATOR_1", "OPERATOR")
        auth.freeze_initialization()
        rules = ConstitutionalRuleRegistry([ConstitutionRule(
            rule_ref="A-009", version="1.0",
            permitted_action_classes=("RESEARCH", "EXPERIMENT"),
            scope="local-test", applicable_roles=("OPERATOR", "GOVERNOR"),
            status="ACTIVE", seq=1)])
        perm = ConstitutionPermissionRecord.claim(
            rule_ref="A-009", permitted_action_class="RESEARCH",
            basis="bounded research", seq=1).verify(rules)
        out = apply_operator_directive("DIR_1", "OPERATOR_1", auth, graph,
                                       perm, evidence_id="EV_1")
        action = "DIRECTIVE_AUTHORIZED" if out.operator_action_authorized \
            else "DIRECTIVE_REFUSED"
    else:
        v = execute_under_operator_hold(
            "ACT_1", "OP_AGENT",
            ActionRequest(action="sandbox_rebalance_reversible",
                          target_scope="sandbox://portfolio_minor",
                          affected_surface="REVERSIBLE_SANDBOX",
                          reversible=False, risk_class="local-write",
                          environment="local-test"),
            _safe_grant(), current_seq=5)
        action = v.verdict
    return {"action_verdict": action,
            "evidence_grade": graph.grade_of("EV_1"),
            "evidence_refs": list(graph.grades[0].grade_evidence_refs)}


# --------------------------------------------------------------------------- #
# Surface: environment shift (S24 family — shift changes interpretation, never
# erases provenance or bypasses evidence)
# --------------------------------------------------------------------------- #
def _sensor_registry() -> EvidenceRegistry:
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="R_SENSOR", kind="OBSERVATION",
                                claim="sensor drift", subject="sensor-drift",
                                seq=3))
    return reg


def environment_shift_surface(environment: str = "") -> Dict[str, Any]:
    reg = _sensor_registry()
    event = GovernanceEvent(event_id="EVT_1", raw_event="sensor recalibration drift",
                            evidence_refs=("R_SENSOR",), seq=1,
                            binding="sensor-drift", scope=environment)
    ce = GovernanceClassificationEvidence(
        proposed_channel="SENSOR", evidence_refs=("R_SENSOR",),
        status="SUPPORTED", binding="sensor-drift",
        scope="local-test" if environment else "")
    d = classify_governance_event(event, (ce,), registry=reg)
    preserved = d.preserved
    return {"channel": d.channel,
            "preserved_raw_event": preserved.get("raw_event"),
            "preserved_evidence_refs": list(preserved.get("evidence_refs", ())),
            "preserved_consequence_class": preserved.get("consequence_class", ""),
            "preserved_containment": preserved.get("containment_action", ""),
            "amendment_candidate": bool(d.amendment_candidate)}


# --------------------------------------------------------------------------- #
# Surface: evaluation-contract freeze (S20 family — canonical content stability)
# --------------------------------------------------------------------------- #
def freeze_surface(criteria: Mapping[str, Any]) -> Dict[str, Any]:
    snap = EvalContractSnapshot.freeze("EVAL_A", 1, dict(criteria))
    return {"criteria_fingerprint": snap.criteria_fingerprint,
            "deeply_frozen": snap.is_deeply_frozen(),
            "threshold": snap.criteria.get("threshold"),
            "channels": list(snap.criteria.get("routing", {}).get("channels", []))}


# --------------------------------------------------------------------------- #
# Surface: allocator concentration (CON-02 observability)
# --------------------------------------------------------------------------- #
def allocator_surface(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    ledger = AllocatorProvenanceLedger()
    for i, r in enumerate(records):
        ledger.record(AllocatorProvenanceRecord(
            evidence_ref=r["evidence_ref"], initiating_actor=r["initiating_actor"],
            allocator_actor=r["allocator_actor"],
            worker_selected=r.get("worker_selected", ""),
            source_path=r.get("source_path", ""),
            retrieval_lineage=r.get("retrieval_lineage", ""),
            exposure_lineage=r.get("exposure_lineage", ""), seq=i))
    return ledger.allocator_concentration()


# --------------------------------------------------------------------------- #
# Surface: transformation pressure (CON-03 Goodhart / transformation addiction)
# --------------------------------------------------------------------------- #
def transformation_pressure_surface(
    novelty_count: int,
    has_quality: bool = False,
    has_independence: bool = False,
    has_contradiction: bool = False,
    threshold_known: str = "UNKNOWN",
) -> Dict[str, Any]:
    """A trigger-vector-looking configuration (lots of novelty / channel /
    anomaly / reviewer counts) must NOT equal genuine transformation evidence.
    Transformation candidacy requires REAL quality + independence +
    contradiction together. Threshold knowledge (exact/approximate/unknown)
    is recorded as an observation and never converts count into evidence."""
    genuine = has_quality and has_independence and has_contradiction
    return {"novelty_count": novelty_count,
            "candidate": bool(genuine),
            "genuine_evidence_triple": genuine,
            "threshold_known": threshold_known,
            "note": ("counts are observables; transformation candidacy requires "
                     "quality AND independence AND contradiction — raw count or "
                     "threshold knowledge alone manufactures nothing")}


# --------------------------------------------------------------------------- #
# Surface: negative knowledge dogma (G4 family — impossible reopen conditions
# must remain visible as dogma risk)
# --------------------------------------------------------------------------- #
def negative_knowledge_surface(reopen_possible: bool) -> Dict[str, Any]:
    """Narrowest scenario contract: a NegativeKnowledge-style blocker resolves
    only when a specific evidence ref arrives. `reopen_possible=False` models
    an impossible/narrow condition that can never be satisfied — visible as
    perpetual NO_REOPEN (dogma risk), never silently reopened."""
    if reopen_possible:
        return {"reopen_state": "REOPEN_CANDIDATE", "dogma_risk": False,
                "reason": "blocker resolution evidence present"}
    return {"reopen_state": "NO_REOPEN", "dogma_risk": True,
            "reason": "reopen condition cannot be satisfied by any admissible "
                      "evidence — narrow/impossible reopen condition remains "
                      "visible as dogma risk"}


# --------------------------------------------------------------------------- #
# Surface: runtime-neutral reconstruction (G4/G5 family — process restart)
# --------------------------------------------------------------------------- #
def reconstruction_surface(content: Mapping[str, Any], epoch_id: str = "E1") -> Dict[str, Any]:
    reg = CanonicalArtifactRegistry()
    art = CanonicalArtifact.make(kind="EVALUATION_CONTRACT", artifact_id="EC-1",
                                 content=dict(content), epoch_id=epoch_id)
    reg.register(art)
    return {"fingerprint": art.computed_fingerprint(), "epoch_id": epoch_id,
            "registered": True}


# --------------------------------------------------------------------------- #
# Authority representation surface (G6 family — equivalent representation =
# same permission boundary)
# --------------------------------------------------------------------------- #
def authority_boundary_surface(actor: str, other_actor: str) -> Dict[str, Any]:
    """Renaming actors while preserving the canonical authority map must give
    the same permission boundary: OPERATOR authorizes, GOVERNOR without a
    mandate does not, WORKER never does."""
    auth = AuthorityState()
    auth.seed_level(actor, "OPERATOR")
    auth.seed_level(other_actor, "GOVERNOR")
    auth.freeze_initialization()
    rules = ConstitutionalRuleRegistry([ConstitutionRule(
        rule_ref="A-009", version="1.0",
        permitted_action_classes=("RESEARCH", "EXPERIMENT"),
        scope="local-test", applicable_roles=("OPERATOR", "GOVERNOR"),
        status="ACTIVE", seq=1)])
    perm = ConstitutionPermissionRecord.claim(
        rule_ref="A-009", permitted_action_class="RESEARCH",
        basis="bounded research", seq=1).verify(rules)
    graph = EvidenceGraph()
    out_op = apply_operator_directive("DIR_OP", actor, auth, graph, perm)
    out_gov = apply_operator_directive("DIR_GOV", other_actor, auth, graph, perm)
    out_worker = apply_operator_directive(
        "DIR_W", "STRANGER", auth, graph, perm, claimed_level="OPERATOR")
    return {"operator_authorized": out_op.operator_action_authorized,
            "governor_authorized": out_gov.operator_action_authorized,
            "stranger_authorized": out_worker.operator_action_authorized}