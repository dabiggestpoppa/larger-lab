"""G5 — deterministic CLASS C domain runner (S14–S19) + G5R hardening.

G5R closes fixture-declared truth paths across the six scenarios:

  * S14: gate materiality from the versioned B7GateContract (OCE-B7-PLAN-001);
    promotion vocabulary is layer-separated (validation != promotion decision
    != execution authority).
  * S15: independence is DERIVED from registered evidence paths (never from a
    declared integer); cluster observation counts are evidence-bound; a
    MechanismCard is admitted for experiment only when the pattern crossed the
    governed epistemic disposition.
  * S16: doctrine claims carry recomputed source bindings + exact bounded claim
    atoms; reproduction quality is DERIVED from the frozen protocol; the
    contradiction is DERIVED from the measured result; amendment ratification
    is governed by AuthorityState (OPERATOR only). The manual is never rewritten.
  * S17: provider semantic contracts resolve by (provider, metric); adapter
    versions must match; missing normalized values stay MISSING; no-disagreement
    never terminates as genuine; materiality uses the tolerance contract.
  * S18: sensor adequacy checks the FULL requirement vector with provenance;
    sensor arrival is an evidenced capability-state change; SearchDemand
    separates required instruments from acceptable source classes.
  * S19: transfer maps validate ALL invariant axes; the target protocol must be
    a real registered frozen object; target data uses governed sensor adequacy;
    source evidence refs resolve but never count as target validation.

All decisions are deterministic, local, model-free and wall-clock-free. The
shared G5 domain epistemic policy decides every terminal disposition; expected
outcomes and hidden ground truth are sealed away from the decision components.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .authority import AuthorityState
from .base import deterministic_hex
from .domain import (
    B7ValidationGate, B7ValidationResult, DataAvailabilityRecord,
    DomainClaimRecord, DomainTransferHypothesis, DoctrineClaimRecord,
    DoctrineContradictionRecord, FailureAtom, FrozenExperimentProtocol,
    MechanismCard, PerformanceReport, PromotionDecision, ProviderObservation,
    ProviderSemanticsRecord, ReproductionRecord, ResearchPriorityRecord,
    SearchDemand, SensorRequirement, SourceDiagnosisResult,
    SourceDisagreementRecord, StrategyCandidate, UnresolvedPatternRecord,
    diagnose_provider_disagreement,
)
from .domain_policy import G5DomainPolicy, g5_policy_outcome
from .evidence import EvidenceRecord
from .g5r import (
    DoctrineAmendmentProposal,
    DoctrineClaimAtom,
    ObservedResult,
    ReproductionProtocol,
    SensorCapabilityChangeRecord,
    assess_sensor_adequacy,
    cluster_verified_observation_paths,
    compare_measured_result,
    decide_mechanism_admission,
    derive_independence,
    derive_reproduction_quality,
    govern_amendment_ratification,
    recompute_source_binding,
    resolve_frozen_target_protocol,
    resolve_source_evidence_refs,
    validate_sha256_digest,
    validate_transfer_map,
)
from .negative import NegativeKnowledgeRecord
from .registry import EvidenceRegistry
from .reopen import ReopenCondition, ReopenEvaluator, EvidenceApplicability

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def data_availability_from_fixture(data: Mapping[str, Any]) -> DataAvailabilityRecord:
    return DataAvailabilityRecord.from_fixture(data)


def domain_claim_from_fixture(data: Mapping[str, Any]) -> DomainClaimRecord:
    return DomainClaimRecord.from_fixture(data)


@dataclass
class G5ScenarioPack:
    scenario_id: str
    scenario_version: str = "1.0.0"
    domain: str = "GENERIC"
    strategies: List[Mapping[str, Any]] = field(default_factory=list)          # S14
    unresolved_patterns: List[Mapping[str, Any]] = field(default_factory=list) # S15
    mechanism_cards: List[Mapping[str, Any]] = field(default_factory=list)
    experiment_protocols: List[Mapping[str, Any]] = field(default_factory=list)
    doctrine_claims: List[Mapping[str, Any]] = field(default_factory=list)     # S16
    reproductions: List[Mapping[str, Any]] = field(default_factory=list)
    amendment_proposal: Optional[Mapping[str, Any]] = None
    amendment_ratifications: List[Mapping[str, Any]] = field(default_factory=list)
    provider_observations: List[Mapping[str, Any]] = field(default_factory=list) # S17
    provider_semantics: List[Mapping[str, Any]] = field(default_factory=list)
    disagreement_tolerances: List[Mapping[str, Any]] = field(default_factory=list)
    sensor_requirements: List[Mapping[str, Any]] = field(default_factory=list)  # S18
    data_availability: List[Mapping[str, Any]] = field(default_factory=list)
    sensor_capability_changes: List[Mapping[str, Any]] = field(default_factory=list)
    transfer_hypotheses: List[Mapping[str, Any]] = field(default_factory=list)  # S19
    claims: List[Mapping[str, Any]] = field(default_factory=list)
    current_facts: Mapping[str, Any] = field(default_factory=dict)
    evidence: List[Mapping[str, Any]] = field(default_factory=list)
    evidence_applicability: List[Mapping[str, Any]] = field(default_factory=list)
    reopen_conditions: List[Mapping[str, Any]] = field(default_factory=list)
    expected_outcome: str = ""            # SEALED — stripped before run
    hidden_ground_truth: Optional[dict] = None  # SEALED

    def decision_grade(self) -> "G5ScenarioPack":
        out = {k: v for k, v in self.__dict__.items()
               if k not in ("expected_outcome", "hidden_ground_truth")}
        return G5ScenarioPack(**out)


@dataclass
class G5RunResult:
    artifacts: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.artifacts)


PACK_FIELDS = {
    "scenario_id", "scenario_version", "domain", "strategies", "unresolved_patterns",
    "mechanism_cards", "experiment_protocols", "doctrine_claims", "reproductions",
    "amendment_proposal", "amendment_ratifications", "provider_observations",
    "provider_semantics", "disagreement_tolerances", "sensor_requirements",
    "data_availability", "sensor_capability_changes", "transfer_hypotheses", "claims",
    "current_facts", "evidence", "evidence_applicability", "reopen_conditions",
    "expected_outcome", "hidden_ground_truth",
}

REF_KEYS = {
    "strategies_ref": "strategies", "unresolved_patterns_ref": "unresolved_patterns",
    "mechanism_cards_ref": "mechanism_cards", "protocols_ref": "experiment_protocols",
    "doctrine_claims_ref": "doctrine_claims", "reproductions_ref": "reproductions",
    "amendment_ref": "amendment_proposal",
    "amendment_ratifications_ref": "amendment_ratifications",
    "provider_observations_ref": "provider_observations",
    "provider_semantics_ref": "provider_semantics",
    "disagreement_tolerances_ref": "disagreement_tolerances",
    "sensor_requirements_ref": "sensor_requirements",
    "data_availability_ref": "data_availability",
    "sensor_capability_changes_ref": "sensor_capability_changes",
    "transfer_hypotheses_ref": "transfer_hypotheses",
    "claims_ref": "claims", "evidence_ref": "evidence",
    "evidence_applicability_ref": "evidence_applicability",
    "reopen_conditions_ref": "reopen_conditions",
}


def load_g5_pack(pack_dir: Path) -> G5ScenarioPack:
    root = Path(pack_dir)
    spec = json.loads((root / "scenario.json").read_text(encoding="utf-8"))
    kw: Dict[str, Any] = {}
    for key, value in spec.items():
        if key in REF_KEYS:
            kw[REF_KEYS[key]] = json.loads((root / value).read_text(encoding="utf-8"))
        elif key in PACK_FIELDS:
            kw[key] = value
    return G5ScenarioPack(**kw)


def _policy_facts(pack: G5ScenarioPack, **extra) -> Dict[str, Any]:
    facts = dict(pack.current_facts)
    facts.update(extra)
    return facts


def _evidence_registry(pack: G5ScenarioPack) -> EvidenceRegistry:
    reg = EvidenceRegistry()
    for i, rec in enumerate(pack.evidence or []):
        rec = dict(rec)
        rid = str(rec.get("record_id") or deterministic_hex("g5_ev", i))
        kind = str(rec.get("kind", "OBSERVATION")).upper()
        actual = ("INDEPENDENT_CONFIRMATION" if kind == "INDEPENDENT_CONFIRMATION"
                  else "AGENT_CLAIM" if kind == "AGENT_CLAIM"
                  else "DETERMINISTIC" if kind == "DETERMINISTIC" else "OBSERVATION")
        reg.register(EvidenceRecord(record_id=rid, kind=actual,
                                    claim=str(rec.get("claim", "")),
                                    source_lineage=str(rec.get("lineage", "")),
                                    source_label=str(rec.get("source_label", "")),
                                    retrieval_lineage=str(rec.get("retrieval_lineage", "")),
                                    seq=int(rec.get("seq", 0))))
    return reg


def _applicability(pack: G5ScenarioPack) -> Dict[str, EvidenceApplicability]:
    return {str(l["evidence_id"]): EvidenceApplicability.from_fixture(l)
            for l in (pack.evidence_applicability or [])}


def _nk(seq: int, claim: str, scope: str, reason: str,
        reopen_condition_ids: Sequence[str]) -> NegativeKnowledgeRecord:
    nk = NegativeKnowledgeRecord.make(seq, claim, scope, reason,
                                      reopen_conditions=list(reopen_condition_ids))
    nk.author_actor = "B7_VALIDATION"
    nk.authority_basis = "B7 material hard failure"
    return nk


def _tolerance_map(pack: G5ScenarioPack) -> Dict[Tuple[str, str], Any]:
    from .domain import DisagreementToleranceContract
    out: Dict[Tuple[str, str], Any] = {}
    for i, t in enumerate(pack.disagreement_tolerances or []):
        tol = DisagreementToleranceContract(
            contract_id=str(t.get("contract_id") or deterministic_hex("tol", i)),
            metric=str(t.get("metric", "*")), units=str(t.get("units", "*")),
            absolute_tolerance=float(t.get("absolute_tolerance", 0.0)),
            relative_tolerance=float(t.get("relative_tolerance", 0.0)),
            basis_points_tolerance=float(t.get("basis_points_tolerance", 0.0)))
        out[(tol.metric, tol.units)] = tol
    return out


# --------------------------------------------------------------------------- #
# S14 — huge fake alpha
# --------------------------------------------------------------------------- #
def run_s14(pack: G5ScenarioPack, policy: G5DomainPolicy,
            policy_fingerprint: str = "",
            pnl_multiplier: float = 1.0,
            fix_lookahead: bool = False,
            fix_fills: bool = False) -> G5RunResult:
    """Reject huge fake alpha: PIT/execution hard failures block promotion no
    matter the PnL; PnL only raises research priority. CONTROLS: fixing only
    lookahead (fills still impossible) or only fills (lookahead remains) keeps
    REJECTED; a moderate clean candidate progresses farther — but only to
    PROMOTION_CANDIDATE (validated gates), never to execution authority
    (G5R-24 separates validation result / promotion decision / execution)."""
    gate = B7ValidationGate()
    items = []
    for i, raw in enumerate(pack.strategies):
        cand = StrategyCandidate.from_fixture(raw, seq=i)
        features = tuple(f for f in cand.features
                         if not (fix_lookahead and f.leaks()))
        fills = tuple(f for f in cand.fills
                      if not (fix_fills and f.impossible()))
        perf = cand.performance
        scaled = PerformanceReport(
            sharpe=perf.sharpe, cumulative_return=perf.cumulative_return * pnl_multiplier,
            max_drawdown=perf.max_drawdown, win_rate=perf.win_rate,
            sample_years=perf.sample_years)
        fixed = StrategyCandidate(
            candidate_id=cand.candidate_id, family=cand.family,
            specification_ref=cand.specification_ref, performance=scaled,
            features=features, fills=fills, data_lineage=cand.data_lineage,
            dataset_ref=cand.dataset_ref, parameter_count=cand.parameter_count,
            sample_count=cand.sample_count, holdout_ref=cand.holdout_ref,
            walk_forward_ref=cand.walk_forward_ref, cost_model_ref=cand.cost_model_ref)
        # noqa
        result: B7ValidationResult = gate.run(fixed)

        # RESEARCH PRIORITY — PnL may raise priority ONLY
        priority = g5_policy_outcome(
            policy, _policy_facts(pack, economic_value_class=scaled.economic_value_class),
            "research_priority", "PRIORITY_NORMAL")
        priority_record = ResearchPriorityRecord(
            priority_id=f"PRI-{cand.candidate_id}",
            claim_ref=cand.candidate_id,
            priority=priority["disposition"],
            rationale=priority["rationale"],
            pnl_class_used=scaled.economic_value_class)

        # PROMOTION — decided by the gates only (B7 authority). G5R-24: the
        # decision vocabulary is PROMOTION_CANDIDATE / REJECTED / HOLD at the
        # research layer; execution_authority is ALWAYS NONE here.
        if result.terminal == "REJECTED":
            promotion = PromotionDecision(
                decision_id=f"PROMO-{cand.candidate_id}",
                claim_ref=cand.candidate_id, decision="REJECTED",
                validation_terminal="REJECTED", execution_authority="NONE",
                rationale="material BLOCKING gate failure")
        else:
            promotion = PromotionDecision(
                decision_id=f"PROMO-{cand.candidate_id}",
                claim_ref=cand.candidate_id, decision="PROMOTION_CANDIDATE",
                validation_terminal="VALIDATION_PASS", execution_authority="NONE",
                rationale="clean B7 gate vector; promotion to VALIDATION, never execution")

        # NEGATIVE KNOWLEDGE for material rejection — with machine-readable
        # reopen conditions (PIT-correct reconstruction + realistic execution +
        # frozen validation).
        nk = None
        if result.terminal == "REJECTED":
            nk = _nk(i, f"candidate {cand.candidate_id} rejected",
                     f"family:{cand.family}",
                     "material B7 hard failures",
                     [c["condition_id"] for c in pack.reopen_conditions])

        factual = result.terminal
        if result.terminal == "REJECTED":
            factual = "REJECTED_NEGATIVE_KNOWLEDGE"
        elif result.terminal == "VALIDATION_PASS":
            factual = "VALIDATION_REQUIRED"
        disposition = g5_policy_outcome(
            policy,
            _policy_facts(pack,
                          claim_type="ALPHA_CANDIDATE",
                          validation_gate_terminal=result.terminal,
                          pit_integrity=("BAD" if any(
                              a.failure_id == "LOOKAHEAD_LEAKAGE"
                              for a in result.failure_atoms) else "GOOD"),
                          execution_realism=("BAD" if any(
                              a.failure_id == "UNREALISTIC_FILL_MODEL"
                              for a in result.failure_atoms) else "GOOD"),
                          data_availability="AVAILABLE",
                          mechanism_status=("PRESENT" if result.terminal == "VALIDATION_PASS"
                                            else "UNRESOLVED")),
            "claim_disposition", factual)

        items.append({
            "candidate_id": cand.candidate_id,
            "performance": scaled.to_dict(),
            "gate_vector": [g.to_dict() for g in result.gates],
            "gate_contract_id": result.gate_contract_id,
            "not_executed_gates": list(result.not_executed_gates),
            "material_failures": list(result.material_failures),
            "failure_atoms": [a.to_dict() for a in result.failure_atoms],
            "research_priority": priority_record.to_dict(),
            "promotion_decision": promotion.to_dict(),
            "disposition": disposition["disposition"],
            "policy_rule_id": disposition["rule_id"],
            "negative_knowledge": nk.to_dict() if nk else None,
            "reopen_conditions": [dict(c) for c in pack.reopen_conditions],
        })
    fp = deterministic_hex("s14_behavior", [x["disposition"] for x in items],
                           [x["material_failures"] for x in items],
                           [x["promotion_decision"] for x in items],
                           policy_fingerprint, pnl_multiplier,
                           fix_lookahead, fix_fills, length=32)
    return G5RunResult({
        "scenario_id": pack.scenario_id,
        "domain": pack.domain,
        "items": items,
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g5_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S15 — new alpha family from unresolved pattern
# --------------------------------------------------------------------------- #
def run_s15(pack: G5ScenarioPack, policy: G5DomainPolicy,
            policy_fingerprint: str = "") -> G5RunResult:
    """UNRESOLVED_PATTERN -> anomaly cluster -> mechanism card -> frozen
    experiment protocol. NEVER a strategy. G5R-01/02: independence is DERIVED
    from registered evidence paths; cluster observation counts are
    evidence-bound (a repeated pattern on the same observation cannot inflate).
    G5R-03: a MechanismCard is admitted for experiment ONLY when its pattern
    crossed ONTOLOGY_EXPLORATION_CANDIDATE — fixture presence of the card file
    is never admission."""
    patterns = [UnresolvedPatternRecord.from_fixture(p) for p in pack.unresolved_patterns]
    cards = [MechanismCard.from_fixture(c) for c in pack.mechanism_cards]
    protocols = [FrozenExperimentProtocol.from_fixture(p) for p in pack.experiment_protocols]
    registry = _evidence_registry(pack)

    # per-pattern independence (evidence-path derived)
    pattern_assessments = {p.pattern_id: derive_independence(p, registry) for p in patterns}

    # deterministic anomaly cluster: group on explicit similarity signature
    clusters: List[Dict[str, Any]] = []
    by_sig: Dict[str, List[UnresolvedPatternRecord]] = {}
    for p in patterns:
        by_sig.setdefault(deterministic_hex("cluster", p.residual_behavior), []).append(p)
    for sig, members in sorted(by_sig.items()):
        unique_paths = cluster_verified_observation_paths(members, registry)
        clusters.append({
            "cluster_id": deterministic_hex("cluster", sig, "g5"),
            "pattern_refs": [m.pattern_id for m in members],
            "similarity_signature": sig,
            "independent_observations": len(unique_paths),
            "verified_evidence_paths": list(unique_paths),
        })
    cluster = clusters[0] if clusters else {}

    # dispositions per pattern
    pattern_items = []
    pattern_dispositions: Dict[str, str] = {}
    for p in patterns:
        assessment = pattern_assessments[p.pattern_id]
        if not p.data_quality_passed:
            dq, da, indep = "FAILED", "AVAILABLE", "UNRESOLVED"
        elif p.required_sensor:
            dq, da, indep = "CLEAN", "UNAVAILABLE", "UNRESOLVED"
        else:
            dq, da = "CLEAN", "AVAILABLE"
            indep = assessment.independence_status
        explored = (p.data_quality_passed and not p.required_sensor
                    and indep in ("CONFIRMED", "SUPPORTED"))
        facts = _policy_facts(
            pack,
            claim_type="MECHANISM_HYPOTHESIS",
            data_quality=dq,
            mechanism_status="UNKNOWN_FAMILY" if explored else "UNRESOLVED",
            data_availability=da,
            independence_status=indep,
            validation_gate_terminal="VALIDATION_PASS",
        )
        disp = g5_policy_outcome(policy, facts, "claim_disposition",
                                 "UNRESOLVED_PATTERN")
        pattern_dispositions[p.pattern_id] = disp["disposition"]
        pattern_items.append({
            "pattern_id": p.pattern_id,
            "disposition": disp["disposition"],
            "policy_rule_id": disp["rule_id"],
            "family_label": p.family_label,
            "independence": assessment.to_dict(),
            "data_quality_passed": p.data_quality_passed,
        })

    # mechanism cards precede strategy: admission is governed by the pattern
    # disposition (G5R-03); a card on a failed/blocked/unresolved pattern stays
    # PROPOSED_MECHANISM. No strategy/execution object is ever created.
    pattern_by_refs = {frozenset(p.independence_evidence_refs): p.pattern_id
                       for p in patterns}
    mechanism_item = {}
    if cards:
        card = cards[0]
        host = pattern_by_refs.get(frozenset(card.evidence_refs))
        card_disp = pattern_dispositions.get(host, "UNRESOLVED_PATTERN")
        # G5R-03: the card is admitted for experiment only when its host pattern
        # crossed the governed epistemic disposition. Fixture presence of the
        # card file is NOT admission.
        admission = decide_mechanism_admission(card, {card.mechanism_id: card_disp})
        admitted = admission.admission == "ADMITTED_MECHANISM_FOR_EXPERIMENT"
        protocol = protocols[0] if (protocols and admitted) else None
        mechanism_item = {
            "mechanism_card": card.to_dict(),
            "host_pattern_id": host,
            "host_disposition": card_disp,
            "mechanism_admission": admission.admission,
            "mechanism_admission_rationale": admission.rationale,
            "frozen_protocol": protocol.to_dict() if protocol else None,
            "protocol_fingerprint": protocol.fingerprint if protocol else "",
            "forbidden_transition_blocked": True,
            "strategy_created": False,
            "execution_artifact_created": False,
        }

    fp = deterministic_hex("s15_behavior", [x["disposition"] for x in pattern_items],
                           cluster, policy_fingerprint, length=32)
    return G5RunResult({
        "scenario_id": pack.scenario_id,
        "domain": pack.domain,
        "patterns": pattern_items,
        "cluster": cluster,
        "mechanism": mechanism_item,
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g5_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S16 — CEREBUS manual contradiction
# --------------------------------------------------------------------------- #
def run_s16(pack: G5ScenarioPack, policy: G5DomainPolicy,
            policy_fingerprint: str = "") -> G5RunResult:
    """DOCTRINE CLAIM preserved; REPRODUCTION separate; the contradiction is
    DERIVED from the measured result; amendment ratification is governed by
    AuthorityState. A flawed reproduction => REPRODUCTION_REJECTED and the
    manual stays preserved. The manual file is never rewritten."""
    claims = [DoctrineClaimRecord.from_fixture(c) for c in pack.doctrine_claims]
    repros = [dict(r) for r in pack.reproductions]

    claim_outputs = []
    for claim in claims:
        binding = None
        binding_status = "BOUND"
        try:
            binding = recompute_source_binding(
                str(REPO_ROOT / claim.source_path), claim.manual_version,
                f"{claim.section} / {claim.page}", claim.exact_claim_representation)
            # fail closed: a stored digest labeled SHA-256 must be a 64-hex
            # SHA-256 and must equal the recomputed file digest
            if claim.source_fingerprint:
                validate_sha256_digest(claim.source_fingerprint)
                if claim.source_fingerprint != binding.content_digest:
                    binding_status = "STALE_DIGEST"
        except Exception as exc:  # pragma: no cover - defensive
            binding_status = f"UNBOUND:{type(exc).__name__}"
        claim_output = claim.to_dict()
        claim_output["source_binding"] = binding.to_dict() if binding else None
        claim_output["source_binding_status"] = binding_status
        claim_atoms = []
        claim_atoms.append(DoctrineClaimAtom.make(
            atom_id=f"{claim.claim_id}:TARGET_METRIC",
            claim_id=claim.claim_id, source_path=claim.source_path,
            locator="Target Metric table (PAGE 4-5)",
            claim_kind="TARGET_METRIC_ROW",
            exact_fragment=json.dumps(dict(claim.numeric_parameters), sort_keys=True),
            manual_version=claim.manual_version))
        for i, cond in enumerate(claim.structural_conditions):
            claim_atoms.append(DoctrineClaimAtom.make(
                atom_id=f"{claim.claim_id}:APPLICABILITY:{i}",
                claim_id=claim.claim_id, source_path=claim.source_path,
                locator=f"{claim.section} / applicability fragment {i + 1}",
                claim_kind="APPLICABILITY_CONDITION", exact_fragment=cond,
                manual_version=claim.manual_version))
        claim_output["claim_atoms"] = [a.to_dict() for a in claim_atoms]
        claim_outputs.append(claim_output)

    results = []
    contradictions = []
    comparisons = []
    quality_assessments = []
    protocols = []
    observed_results = []
    for claim in claims:
        for raw in repros:
            if claim.claim_id != raw.get("claim_id"):
                continue
            protocol = ReproductionProtocol.from_fixture(raw.get("protocol", {}))
            observed = ObservedResult.from_fixture(raw.get("observed_result", {}) or {})
            claimed_fp = str(raw.get("protocol_fingerprint", ""))
            declared_deviations = tuple(raw.get("known_deviations", []))
            qa = derive_reproduction_quality(protocol, claim, declared_deviations,
                                             claim_fingerprint=claimed_fp if claimed_fp else "")
            protocols.append(protocol.to_dict())
            observed_results.append(observed.to_dict())
            quality_assessments.append(qa.to_dict())

            if qa.quality == "FLAWED":
                disp = g5_policy_outcome(
                    policy, _policy_facts(pack, reproduction_quality="FLAWED",
                                          manual_authority="CEREBUS_MANUAL",
                                          contradiction_present=False),
                    "doctrine", "MANUAL_PRESERVED")
                results.append({
                    "claim_id": claim.claim_id,
                    "reproduction_id": protocol.protocol_id,
                    "status": "REPRODUCTION_REJECTED",
                    "disposition": disp["disposition"],
                    "policy_rule_id": disp["rule_id"],
                    "quality": qa.to_dict(),
                    "observed_result": observed.to_dict(),
                    "manual_preserved": True,
                    "amendment_required": False,
                })
                continue

            # measured contradiction — the fixture's result STRING is never the
            # authority (G5R-07)
            win_band = list(claim.numeric_parameters.get("win_rate_band", []))
            comparison = None
            if observed.metric and win_band and len(win_band) == 2:
                comparison = compare_measured_result(observed, win_band)
                comparison = DoctrineComparison(
                    comparison_id=comparison.comparison_id,
                    claim_id=claim.claim_id, reproduction_id=protocol.protocol_id,
                    metric=comparison.metric, observed_estimate=comparison.observed_estimate,
                    observed_interval=comparison.observed_interval,
                    claim_interval=comparison.claim_interval,
                    verdict=comparison.verdict, rationale=comparison.rationale)
                comparisons.append(comparison.to_dict())

            if comparison and comparison.verdict == "CONTRADICTS_CLAIM":
                disp = g5_policy_outcome(
                    policy, _policy_facts(pack, reproduction_quality="CLEAN",
                                          manual_authority="CEREBUS_MANUAL",
                                          contradiction_present=True),
                    "doctrine", "CONTRADICTION_OPEN")
                contradictions.append(DoctrineContradictionRecord(
                    contradiction_id=deterministic_hex("contradiction", claim.claim_id,
                                                       protocol.protocol_id),
                    claim_id=claim.claim_id, reproduction_id=protocol.protocol_id,
                    contradiction_summary=(f"measured {observed.metric}={observed.estimate} "
                                           f"({observed.uncertainty_interval}) lies outside the "
                                           f"doctrine band {win_band} under exact governed "
                                           f"conditions"),
                    reproduction_confidence=str(raw.get("uncertainty", "HIGH_CONFIDENCE")),
                    scope=claim.section))
                results.append({
                    "claim_id": claim.claim_id,
                    "reproduction_id": protocol.protocol_id,
                    "status": "CONTRADICTION_OPEN",
                    "disposition": disp["disposition"],
                    "policy_rule_id": disp["rule_id"],
                    "quality": qa.to_dict(),
                    "observed_result": observed.to_dict(),
                    "comparison": comparison.to_dict(),
                    "manual_preserved": True,
                    "amendment_required": bool(pack.amendment_proposal),
                })
            else:
                disp = g5_policy_outcome(
                    policy, _policy_facts(pack, reproduction_quality="CLEAN",
                                          manual_authority="CEREBUS_MANUAL",
                                          contradiction_present=False),
                    "doctrine", "MANUAL_PRESERVED")
                results.append({
                    "claim_id": claim.claim_id,
                    "reproduction_id": protocol.protocol_id,
                    "status": "CONSISTENT",
                    "disposition": disp["disposition"],
                    "policy_rule_id": disp["rule_id"],
                    "quality": qa.to_dict(),
                    "observed_result": observed.to_dict(),
                    "comparison": comparison.to_dict() if comparison else None,
                    "manual_preserved": True,
                    "amendment_required": False,
                })

    # G5R-09 — governed ratification via AuthorityState (OPERATOR only); a
    # fixture-supplied `ratified=true` boolean is never consulted (CASE D).
    proposal = None
    if pack.amendment_proposal:
        proposal = DoctrineAmendmentProposal.from_fixture(pack.amendment_proposal)
    ratifications = []
    amendment_ratified = False
    if proposal:
        authority = AuthorityState()
        authority.seed_level("OPERATOR_ACTOR", "OPERATOR")
        for i, rat in enumerate(pack.amendment_ratifications or []):
            try:
                rec = govern_amendment_ratification(
                    authority, proposal, ratifier=str(rat.get("ratifier", "OPERATOR_ACTOR")),
                    authority_basis=str(rat.get("authority_basis", "provisional test contract")),
                    scope=str(rat.get("scope", proposal.scope)),
                    manual_claim_id=proposal.claim_id, seq=i)
                ratifications.append(rec.to_dict())
                amendment_ratified = True
            except Exception:
                # an invalid ratification attempt is recorded as rejected,
                # never applied — the manual remains canonical
                ratifications.append({"proposal_id": proposal.proposal_id,
                                      "ratifier": str(rat.get("ratifier", "")),
                                      "status": "REJECTED",
                                      "reason": "not governed OPERATOR ratification"})

    fp = deterministic_hex("s16_behavior", [r["status"] for r in results],
                           [c.to_dict() for c in contradictions],
                           [c for c in claim_outputs],
                           policy_fingerprint, length=32)
    return G5RunResult({
        "scenario_id": pack.scenario_id,
        "domain": pack.domain,
        "doctrine_claims": claim_outputs,
        "reproduction_protocols": protocols,
        "observed_results": observed_results,
        "quality_assessments": quality_assessments,
        "reproduction_results": results,
        "comparisons": comparisons,
        "contradictions": [c.to_dict() for c in contradictions],
        "amendment_proposal": proposal.to_dict() if proposal else None,
        "amendment_ratified": amendment_ratified,
        "amendment_ratifications": ratifications,
        "amendment_operator_required": bool(proposal) and not amendment_ratified,
        "manual_modified": False,                 # CONTRADICTION != SILENT REWRITE
        "manual_claim_rewritten": False,
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g5_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S17 — crypto provider disagreement
# --------------------------------------------------------------------------- #
def run_s17(pack: G5ScenarioPack, policy: G5DomainPolicy,
            policy_fingerprint: str = "") -> G5RunResult:
    """Provider disagreement is diagnosed strictly source-first. Semantic
    contracts resolve by (provider, metric) — a provider may publish several
    metrics with different semantics; a MISSING contract fails closed. Adapter
    versions must match; absent normalized values stay MISSING; equal clean
    values terminate NO_DISAGREEMENT; materiality uses the tolerance contract."""
    obs = {o["observation_id"]: ProviderObservation.from_fixture(o)
           for o in pack.provider_observations}
    sems = {(s["provider"], s["metric"]): ProviderSemanticsRecord.from_fixture(s)
            for s in pack.provider_semantics}
    tolerances = _tolerance_map(pack)
    diagnoses = []
    seen = set()
    oids = list(obs)
    for i in range(len(oids)):
        for j in range(i + 1, len(oids)):
            a, b = oids[i], oids[j]
            key = frozenset((a, b))
            if key in seen:
                continue
            seen.add(key)
            oa, ob = obs[a], obs[b]
            if oa.metric != ob.metric:
                continue
            sem_a = sems.get((oa.provider, oa.metric))
            sem_b = sems.get((ob.provider, ob.metric))
            tol = tolerances.get((oa.metric, oa.units))
            diag: SourceDiagnosisResult = diagnose_provider_disagreement(oa, ob, sem_a, sem_b,
                                                                         tolerance=tol)
            disp = g5_policy_outcome(
                policy,
                _policy_facts(pack, source_disagreement="PRESENT",
                              diagnosis_complete=diag.steps[-1].layer == "disagreement_surface"
                              if diag.steps else False),
                "source_disagreement", "SOURCE_DIAGNOSTIC_REQUIRED")
            record = SourceDisagreementRecord(
                disagreement_id=diag.disagreement_id, provider_a=oa.provider,
                provider_b=ob.provider, metric=oa.metric,
                value_a=oa.normalized_value, value_b=ob.normalized_value,
                diagnosis=diag)
            diagnoses.append({
                "disagreement_id": diag.disagreement_id,
                "steps": [s.to_dict() for s in diag.steps],
                "cause": diag.cause,
                "terminal": diag.terminal,
                "disposition": disp["disposition"],
                "policy_rule_id": disp["rule_id"],
                "source_disagreement_record": record.to_dict(),
                "averaged_to_consensus": False,
                "field_ontology_rewritten": False,
            })

    fp = deterministic_hex("s17_behavior",
                           [(d["cause"], d["terminal"]) for d in diagnoses],
                           policy_fingerprint, length=32)
    return G5RunResult({
        "scenario_id": pack.scenario_id,
        "domain": pack.domain,
        "diagnoses": diagnoses,
        "provider_native_values_preserved": True,
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g5_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S18 — sensor gap / SearchDemand / reactivation
# --------------------------------------------------------------------------- #
def run_s18(pack: G5ScenarioPack, policy: G5DomainPolicy,
            policy_fingerprint: str = "",
            sensor_available_later: bool = False) -> G5RunResult:
    """A mechanism requiring an absent observable => DATA_BLOCKED + SearchDemand.
    G5R-16/17: adequacy checks the FULL requirement vector with provenance.
    G5R-18: sensor arrival is an EVIDENCED capability-state change — the legacy
    boolean may flip a status for test plumbing but can never verify/certify.
    G5R-19: SearchDemand separates required instruments from acceptable source
    classes."""
    reqs = [SensorRequirement.from_fixture(r) for r in pack.sensor_requirements]
    avail = {a["observable"]: DataAvailabilityRecord.from_fixture(a)
             for a in pack.data_availability}

    # apply the later-availability stimulus: a registered capability change is
    # decision-grade; the plain boolean is NOT (verified/certified stay off).
    change_records: List[SensorCapabilityChangeRecord] = []
    if sensor_available_later:
        for r in reqs:
            rec = avail.get(r.required_observable)
            if rec and rec.status in ("UNAVAILABLE", "CURRENT_ONLY", "UNKNOWN"):
                new_rec = DataAvailabilityRecord(
                    observable=rec.observable, status="AVAILABLE",
                    history_depth=rec.history_depth or r.history_depth,
                    instrument_coverage=rec.instrument_coverage or r.instrument_coverage,
                    claimed=True, verified=False, source=rec.source,
                    resolution=rec.resolution or r.resolution,
                    time_semantics=rec.time_semantics or r.time_semantics,
                    quality_state=rec.quality_state or r.quality_minimum,
                    certification="")   # boolean override cannot certify
                change_records.append(SensorCapabilityChangeRecord(
                    change_id=deterministic_hex("sensor_change", r.required_observable, "bool"),
                    observable=r.required_observable, old_state=rec.status,
                    new_state="AVAILABLE", source="CRYPTO_SENSOR_FABRIC",
                    evidence_refs=[], certification="",
                    effective_epoch="E18_LATER", history_coverage=new_rec.history_depth))
                avail[r.required_observable] = new_rec

    # registered decision-grade capability changes (can verify/certify)
    for i, ch in enumerate(pack.sensor_capability_changes or []):
        c = SensorCapabilityChangeRecord.from_fixture(ch, seq=i)
        change_records.append(c)
        rec = avail.get(c.observable)
        if rec:
            avail[c.observable] = DataAvailabilityRecord(
                observable=rec.observable, status=c.new_state,
                history_depth=c.history_coverage or rec.history_depth,
                instrument_coverage=rec.instrument_coverage,
                claimed=True, verified=bool(c.certification),
                source=c.source, resolution=rec.resolution,
                time_semantics=rec.time_semantics, quality_state=rec.quality_state,
                certification=c.certification)

    blocked = []
    demands = []
    adequacy_results = []
    for r in reqs:
        rec = avail.get(r.required_observable)
        status = rec.status if rec else "UNKNOWN"
        adequate = rec.adequate_history(r) if rec else False
        full_vector = assess_sensor_adequacy(r, rec) if rec else None
        adequacy_results.append(full_vector)
        disp = g5_policy_outcome(
            policy, _policy_facts(pack, claim_type="MECHANISM_HYPOTHESIS",
                                  data_availability=("AVAILABLE" if adequate
                                                     else status),
                                  sensor_resolution=("SUFFICIENT" if adequate
                                                     else "INSUFFICIENT"),
                                  sensor_verified=("VERIFIED" if adequate
                                                   else bool(rec and rec.verified)),
                                  mechanism_status="PRESENT"),
            "availability", "DATA_BLOCKED")
        blocked.append({
            "requirement_id": r.requirement_id,
            "claim_ref": r.claim_ref,
            "required_observable": r.required_observable,
            "data_availability": status,
            "adequate_history": adequate,
            "adequacy": full_vector.to_dict() if full_vector else None,
            "disposition": disp["disposition"],
            "policy_rule_id": disp["rule_id"],
        })
        if not adequate:
            demands.append(SearchDemand(
                demand_id=deterministic_hex("search", r.claim_ref, r.required_observable),
                blocked_claim=r.claim_ref,
                required_sensor=r.required_observable,
                reason=(f"{r.why_required}; alternative ({r.alternative_insufficient}) "
                        f"is insufficient"),
                required_instruments=r.instrument_coverage,
                acceptable_source_classes=("CRYPTO_SENSOR_FABRIC",),
                history_requirement=r.history_depth,
                quality_requirement=r.quality_minimum,
                value_of_information_class="HIGH",
                status="OPEN",
                reopen_condition=f"sensor {r.required_observable} becomes AVAILABLE"))

    # reactivation when the sensor arrives (governed reopen, evidence-backed)
    reopen_items = []
    if sensor_available_later:
        registry = _evidence_registry(pack)
        conditions = tuple(ReopenCondition.make(i, **c)
                           for i, c in enumerate(pack.reopen_conditions))
        evaluator = ReopenEvaluator(conditions=conditions,
                                    evidence_registry=registry,
                                    applicability=_applicability(pack))
        facts = dict(pack.current_facts)
        facts["sensor_available"] = True
        facts["evidence_refs"] = [c.evidence_refs[0] for c in change_records
                                  if c.evidence_refs] or ["EV_S18_SENSOR"]
        for r in reqs:
            ev = evaluator.evaluate(r.claim_ref, facts)
            reopen_items.append({
                "claim_ref": r.claim_ref,
                "reopen_outcome": ev.outcome,
                "rationale": ev.rationale,
                "retroactively_validated": False,     # can now be TESTED, not believed
            })

    fp = deterministic_hex("s18_behavior",
                           [b["disposition"] for b in blocked],
                           [d.to_dict() for d in demands],
                           sensor_available_later,
                           policy_fingerprint, length=32)
    return G5RunResult({
        "scenario_id": pack.scenario_id,
        "domain": pack.domain,
        "blocked_claims": blocked,
        "search_demands": [d.to_dict() for d in demands],
        "sensor_adequacy_results": [a.to_dict() if a else None for a in adequacy_results],
        "sensor_capability_changes": [c.to_dict() for c in change_records],
        "boolean_override_non_authoritative": bool(
            [c for c in change_records if not c.certification]),
        "synthetic_backfill_used": False,
        "blocked_claim_demoted_as_false": False,
        "activation": reopen_items,
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g5_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S19 — crypto -> FX transfer firewall
# --------------------------------------------------------------------------- #
def run_s19(pack: G5ScenarioPack, policy: G5DomainPolicy,
            policy_fingerprint: str = "",
            target_data_available: Optional[bool] = None,
            protocol_frozen: Optional[bool] = None,
            broken_mapping: bool = False) -> G5RunResult:
    """Crypto concept -> FX transfer is a HYPOTHESIS until target-domain
    validation. G5R-20: the invariant map validates ALL axes. G5R-21: the
    target protocol must be a real registered frozen object. G5R-22: target
    data uses governed sensor adequacy — the boolean override is
    NON-AUTHORITATIVE test plumbing and never changes the governed result.
    G5R-23: source evidence refs resolve but never count as target validation."""
    transfers = [DomainTransferHypothesis.from_fixture(t)
                 for t in pack.transfer_hypotheses]
    protocols = [FrozenExperimentProtocol.from_fixture(p)
                 for p in pack.experiment_protocols]
    reqs = [SensorRequirement.from_fixture(r) for r in pack.sensor_requirements]
    avail = {a["observable"]: DataAvailabilityRecord.from_fixture(a)
             for a in pack.data_availability}
    registry = _evidence_registry(pack)

    items = []
    for t in transfers:
        # source evidence refs must resolve (G5R-23)
        unknown_source_refs = resolve_source_evidence_refs(t, registry)

        # transfer map: every invariant axis must be populated (G5R-20)
        validation = validate_transfer_map(t.transfer_map)
        map_ok = validation.map_sound and not broken_mapping

        if broken_mapping or t.transfer_map.known_broken_assumptions:
            hstatus = "BROKEN_MAPPING"
        elif not map_ok:
            hstatus = "ANALOGY"
        else:
            hstatus = "HYPOTHESIS"

        # target data: FULL governed sensor adequacy (G5R-22)
        target_adequacy: Dict[str, bool] = {}
        for r in reqs:
            rec = avail.get(r.required_observable)
            target_adequacy[r.required_observable] = \
                bool(rec and rec.adequate_history(r))
        governed_target_ok = bool(target_adequacy) and all(target_adequacy.values())

        # the boolean override is NON-AUTHORITATIVE plumbing: it is recorded
        # but can never change the primary governed result
        override_flag = None
        if target_data_available is True and not governed_target_ok:
            override_flag = "NON_AUTHORITATIVE_TEST_CONVENIENCE"
        elif target_data_available is not None:
            override_flag = "NON_AUTHORITATIVE_TEST_CONVENIENCE"
        target_ok = governed_target_ok

        # protocol must be a real frozen registered object (G5R-21)
        resolution = resolve_frozen_target_protocol(t, protocols)
        protocol_ok = (resolution.resolved and resolution.target_domain_ok
                       and resolution.fingerprint_valid
                       and resolution.frozen_before_result)
        if protocol_frozen is False:
            protocol_ok = False            # explicit deny (legacy test contract)
        elif protocol_frozen is True and not resolution.resolved:
            protocol_ok = False            # boolean alone cannot authorize

        # fail closed on unknown source evidence refs
        hstatus_effective = hstatus
        if unknown_source_refs:
            hstatus_effective = "HYPOTHESIS"

        disp = g5_policy_outcome(
            policy,
            _policy_facts(pack,
                          claim_type="TRANSFER_HYPOTHESIS",
                          domain_transfer_status=hstatus,
                          target_data_availability=("AVAILABLE" if target_ok
                                                    else "UNAVAILABLE"),
                          protocol_frozen=protocol_ok),
            "transfer", "TRANSFER_HYPOTHESIS_ONLY")
        if unknown_source_refs and disp["disposition"] in ("DOMAIN_VALIDATION_REQUIRED",):
            disp = {"disposition": "TRANSFER_HYPOTHESIS_ONLY",
                    "rule_id": "g5r.source_evidence_refs_fail_closed",
                    "governed": False,
                    "rationale": "unknown source evidence refs fail closed; "
                                 "hypothesis cannot proceed", "factual": "TRANSFER_HYPOTHESIS_ONLY"}
        items.append({
            "hypothesis_id": t.hypothesis_id,
            "source_concept": t.source_concept,
            "source_domain": t.source_domain,
            "target_domain": t.target_domain,
            "transfer_map": t.transfer_map.to_dict(),
            "transfer_map_validation": validation.to_dict(),
            "mapping_sound": map_ok,
            "source_evidence_refs_resolved": not bool(unknown_source_refs),
            "source_evidence_refs_unknown": list(unknown_source_refs),
            "target_data_available": target_ok,
            "target_data_override": override_flag,
            "target_adequacy": target_adequacy,
            "protocol_resolution": resolution.to_dict(),
            "protocol_frozen_governed": protocol_ok,
            "disposition": disp["disposition"],
            "policy_rule_id": disp["rule_id"],
            "cerebus_doctrine_overridden": False,
            "fx_strategy_generated": False,
            "source_validation_as_target_validation": False,
        })

    fp = deterministic_hex("s19_behavior",
                           [(i["disposition"], i["mapping_sound"]) for i in items],
                           protocol_frozen, policy_fingerprint, length=32)
    return G5RunResult({
        "scenario_id": pack.scenario_id,
        "domain": pack.domain,
        "transfers": items,
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g5_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# dispatch + post-hoc expectation
# --------------------------------------------------------------------------- #
def run_g5_scenario(pack: G5ScenarioPack, policy: G5DomainPolicy,
                    policy_fingerprint: str = "", **runner_kw) -> G5RunResult:
    if pack.expected_outcome or pack.hidden_ground_truth is not None:
        raise ValueError("run_g5_scenario refuses sealed fields: pass pack.decision_grade()")
    sid = pack.scenario_id
    if sid == "S14":
        return run_s14(pack, policy, policy_fingerprint, **runner_kw)
    if sid == "S15":
        return run_s15(pack, policy, policy_fingerprint)
    if sid == "S16":
        return run_s16(pack, policy, policy_fingerprint)
    if sid == "S17":
        return run_s17(pack, policy, policy_fingerprint)
    if sid == "S18":
        return run_s18(pack, policy, policy_fingerprint, **runner_kw)
    if sid == "S19":
        return run_s19(pack, policy, policy_fingerprint, **runner_kw)
    raise ValueError(f"unknown G5 scenario id {sid!r}")


def evaluate_g5_expectation(result: G5RunResult, pack: G5ScenarioPack) -> Dict[str, Any]:
    """Post-hoc comparator — expectations applied strictly AFTER execution."""
    expected = pack.expected_outcome
    failures = []
    artifacts = result.artifacts
    sid = pack.scenario_id
    if sid == "S14":
        actual = artifacts["items"][0]["disposition"] if artifacts.get("items") else ""
    elif sid == "S15":
        actual = artifacts["patterns"][0]["disposition"] if artifacts.get("patterns") else ""
    elif sid == "S16":
        first = artifacts["reproduction_results"][0] if artifacts.get("reproduction_results") else {}
        actual = first.get("status", "")
    elif sid == "S17":
        first = artifacts["diagnoses"][0] if artifacts.get("diagnoses") else {}
        actual = first.get("cause", "")
    elif sid == "S18":
        first = artifacts["blocked_claims"][0] if artifacts.get("blocked_claims") else {}
        actual = first.get("disposition", "")
    elif sid == "S19":
        first = artifacts["transfers"][0] if artifacts.get("transfers") else {}
        actual = first.get("disposition", "")
    else:
        actual = ""
    if expected and actual != expected:
        failures.append(f"outcome {actual!r} != expected {expected!r}")
    return {"pass": not failures, "expected_outcome": expected,
            "actual_outcome": actual, "failures": failures}


# re-export for convenience
from .g5r import ReproductionQualityAssessment  # noqa: E402
from .g5r import DoctrineComparison  # noqa: E402