"""G5 — deterministic CLASS C domain runner (S14–S19).

Pipeline (G2–G4R discipline carried): scenario pack -> decision-grade projection
(expected outcomes + hidden ground truth REMOVED) -> deterministic domain
machinery (B7 gates, doctrine/reproduction, provider diagnosis, sensor
availability, transfer firewall) with the ONE shared
G5_DOMAIN_EPISTEMIC_POLICY deciding every terminal disposition -> result with
scenario-id-free behavior fingerprint -> expectations applied post-hoc only.

Reused governed machinery:
  * policy-as-executor (G5-P0-A: no rule match => POLICY_HOLD);
  * governed EvidenceRegistry + EvidenceApplicability (P0-B/C) where reopen
    evidence is required (S18 reactivation);
  * NegativeKnowledgeRecord with machine-readable reopen conditions (S14/S16);
  * fail-closed unknowns (UNKNOWN data availability is not AVAILABLE).

Sealing guarantees: decision components never receive expected_outcome or
hidden_ground_truth; behavior fingerprints exclude scenario_id and expected
outcomes; metamorphics (PnL x10, renames) leave behavior unchanged.

Deterministic, local, model-free, wall-clock-free. No broker/exchange/live
model/production/cloud/capital contact.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .authority import AuthorityState
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
from .negative import NegativeKnowledgeRecord
from .reopen import ReopenCondition, ReopenEvaluator, EvidenceApplicability
from .registry import EvidenceRegistry
from .evidence import EvidenceRecord


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
    provider_observations: List[Mapping[str, Any]] = field(default_factory=list) # S17
    provider_semantics: List[Mapping[str, Any]] = field(default_factory=list)
    sensor_requirements: List[Mapping[str, Any]] = field(default_factory=list)  # S18
    data_availability: List[Mapping[str, Any]] = field(default_factory=list)
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
    "amendment_proposal", "provider_observations", "provider_semantics",
    "sensor_requirements", "data_availability", "transfer_hypotheses", "claims",
    "current_facts", "evidence", "evidence_applicability", "reopen_conditions",
    "expected_outcome", "hidden_ground_truth",
}

REF_KEYS = {
    "strategies_ref": "strategies", "unresolved_patterns_ref": "unresolved_patterns",
    "mechanism_cards_ref": "mechanism_cards", "protocols_ref": "experiment_protocols",
    "doctrine_claims_ref": "doctrine_claims", "reproductions_ref": "reproductions",
    "amendment_ref": "amendment_proposal",
    "provider_observations_ref": "provider_observations",
    "provider_semantics_ref": "provider_semantics",
    "sensor_requirements_ref": "sensor_requirements",
    "data_availability_ref": "data_availability",
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
        reg.register(EvidenceRecord(record_id=rid, kind=kind,
                                    claim=str(rec.get("claim", "")),
                                    source_lineage=str(rec.get("lineage", "")),
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
    REJECTED; a moderate clean candidate progresses farther."""
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

        # PROMOTION — decided by the gates only (B7 authority)
        if result.terminal == "REJECTED":
            promotion = PromotionDecision(
                decision_id=f"PROMO-{cand.candidate_id}",
                claim_ref=cand.candidate_id, decision="REJECTED")
        else:
            promotion = PromotionDecision(
                decision_id=f"PROMO-{cand.candidate_id}",
                claim_ref=cand.candidate_id, decision="PROMOTED")

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
                          mechanism_status="PRESENT" if i == 0 else "PRESENT"),
            "claim_disposition", factual)

        items.append({
            "candidate_id": cand.candidate_id,
            "performance": scaled.to_dict(),
            "gate_vector": [g.to_dict() for g in result.gates],
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
    experiment protocol. NEVER a strategy: no execution artifact is created.
    CONTROLS: data-quality failure kills the false pattern; a single-evidence
    lineage stays UNRESOLVED; a sensor-dependent residual routes to
    DATA_BLOCKED instead of forced ontology."""
    patterns = [UnresolvedPatternRecord.from_fixture(p) for p in pack.unresolved_patterns]
    cards = [MechanismCard.from_fixture(c) for c in pack.mechanism_cards]
    protocols = [FrozenExperimentProtocol.from_fixture(p) for p in pack.experiment_protocols]

    # deterministic anomaly cluster: group on explicit similarity signature
    clusters: List[Dict[str, Any]] = []
    by_sig: Dict[str, List[UnresolvedPatternRecord]] = {}
    for p in patterns:
        by_sig.setdefault(deterministic_hex("cluster", p.residual_behavior), []).append(p)
    for sig, members in sorted(by_sig.items()):
        clusters.append({
            "cluster_id": deterministic_hex("cluster", sig, "g5"),
            "pattern_refs": [m.pattern_id for m in members],
            "similarity_signature": sig,
            "independent_observations": sum(max(m.evidence_lineages, 1)
                                            for m in members)})
    cluster = clusters[0] if clusters else {}

    # dispositions per pattern
    pattern_items = []
    for p in patterns:
        if not p.data_quality_passed:
            mstatus, dq, da, indep = "UNRESOLVED", "FAILED", "AVAILABLE", "UNRESOLVED"
        elif p.required_sensor:
            mstatus, dq, da, indep = "UNRESOLVED", "CLEAN", "UNAVAILABLE", "UNRESOLVED"
        elif p.evidence_lineages >= 2:
            mstatus, dq, da, indep = "UNKNOWN_FAMILY", "CLEAN", "AVAILABLE", "CONFIRMED"
        else:
            mstatus, dq, da, indep = "UNRESOLVED", "CLEAN", "AVAILABLE", "UNRESOLVED"
        facts = _policy_facts(
            pack,
            claim_type="MECHANISM_HYPOTHESIS",
            data_quality=dq,
            mechanism_status=mstatus,
            independence_status=indep,
            data_availability=da,
            validation_gate_terminal="VALIDATION_PASS",
        )
        disp = g5_policy_outcome(policy, facts, "claim_disposition",
                                 "UNRESOLVED_PATTERN")
        pattern_items.append({
            "pattern_id": p.pattern_id,
            "disposition": disp["disposition"],
            "policy_rule_id": disp["rule_id"],
            "family_label": p.family_label,
        })

    # mechanism cards precede strategy: card exists, NO strategy/execution object
    mechanism_item = {}
    if cards:
        card = cards[0]
        protocol = protocols[0] if protocols else None
        forbidden_transition_blocked = True   # UNRESOLVED_PATTERN -> strategy is impossible (no strategy surface exists)
        mechanism_item = {
            "mechanism_card": card.to_dict(),
            "frozen_protocol": protocol.to_dict() if protocol else None,
            "protocol_fingerprint": protocol.fingerprint if protocol else "",
            "forbidden_transition_blocked": forbidden_transition_blocked,
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
    """DOCTRINE CLAIM preserved; REPRODUCTION separate; contradiction opens an
    explicit record + amendment proposal requiring OPERATOR. A flawed
    reproduction => REPRODUCTION_REJECTED and the manual stays preserved."""
    claims = [DoctrineClaimRecord.from_fixture(c) for c in pack.doctrine_claims]
    repros = []
    for r in pack.reproductions:
        rec = ReproductionRecord.from_fixture(r)
        repros.append(rec)

    results = []
    contradictions = []
    for claim in claims:
        for repro in repros:
            if claim.claim_id != repro.claim_id:
                continue
            if repro.deviates_from(claim):
                disp = g5_policy_outcome(
                    policy, _policy_facts(pack, reproduction_quality="FLAWED",
                                          manual_authority="CEREBUS_MANUAL",
                                          contradiction_present=False),
                    "doctrine", "MANUAL_PRESERVED")
                results.append({
                    "claim_id": claim.claim_id,
                    "reproduction_id": repro.reproduction_id,
                    "status": "REPRODUCTION_REJECTED",
                    "disposition": disp["disposition"],
                    "policy_rule_id": disp["rule_id"],
                    "manual_preserved": True,
                    "amendment_required": False,
                })
            elif repro.contradicts(claim):
                disp = g5_policy_outcome(
                    policy, _policy_facts(pack, reproduction_quality="CLEAN",
                                          manual_authority="CEREBUS_MANUAL",
                                          contradiction_present=True),
                    "doctrine", "CONTRADICTION_OPEN")
                contradictions.append(DoctrineContradictionRecord(
                    contradiction_id=deterministic_hex("contradiction", claim.claim_id,
                                                       repro.reproduction_id),
                    claim_id=claim.claim_id, reproduction_id=repro.reproduction_id,
                    contradiction_summary=(f"reproduction {repro.reproduction_id} "
                                           f"contradicts {claim.claim_id} under exact "
                                           f"governed conditions ({repro.result})"),
                    reproduction_confidence=repro.uncertainty, scope=claim.section))
                results.append({
                    "claim_id": claim.claim_id,
                    "reproduction_id": repro.reproduction_id,
                    "status": "CONTRADICTION_OPEN",
                    "disposition": disp["disposition"],
                    "policy_rule_id": disp["rule_id"],
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
                    "reproduction_id": repro.reproduction_id,
                    "status": "CONSISTENT",
                    "disposition": disp["disposition"],
                    "policy_rule_id": disp["rule_id"],
                    "manual_preserved": True,
                    "amendment_required": False,
                })

    amendment = dict(pack.amendment_proposal or {})
    amendment_ratified = bool(amendment.get("ratified", False))
    amendment_operator_required = bool(amendment.get("operator_required", True))

    fp = deterministic_hex("s16_behavior", [r["status"] for r in results],
                           [c.to_dict() for c in contradictions],
                           [a.to_dict() for a in claims],
                           policy_fingerprint, length=32)
    return G5RunResult({
        "scenario_id": pack.scenario_id,
        "domain": pack.domain,
        "doctrine_claims": [c.to_dict() for c in claims],
        "reproduction_results": results,
        "contradictions": [c.to_dict() for c in contradictions],
        "amendment_proposal": amendment,
        "amendment_ratified": amendment_ratified,
        "amendment_operator_required": amendment_operator_required,
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
    """Provider disagreement is diagnosed strictly source-first (provider
    semantics -> instrument identity -> adapter -> normalization -> time
    semantics -> quality -> disagreement surface). Native values are never
    averaged away; genuine disagreement is preserved."""
    obs = {o["observation_id"]: ProviderObservation.from_fixture(o)
           for o in pack.provider_observations}
    sems = {s["provider"]: ProviderSemanticsRecord.from_fixture(s)
            for s in pack.provider_semantics}
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
            sem_a = sems.get(oa.provider)
            sem_b = sems.get(ob.provider)
            if sem_a is None or sem_b is None:
                continue
            diag: SourceDiagnosisResult = diagnose_provider_disagreement(oa, ob, sem_a, sem_b)
            disp = g5_policy_outcome(
                policy,
                _policy_facts(pack, source_disagreement="PRESENT",
                              diagnosis_complete=diag.steps[-1].layer == "disagreement_surface"),
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
    Later sensor availability => REOPEN_CANDIDATE via the governed
    ReopenEvaluator (evidence-backed, applicability-bound); never retroactive
    validation."""
    reqs = [SensorRequirement.from_fixture(r) for r in pack.sensor_requirements]
    avail = {a["observable"]: DataAvailabilityRecord.from_fixture(a)
             for a in pack.data_availability}
    # apply the later-availability stimulus
    if sensor_available_later:
        for name, rec in avail.items():
            if rec.status in ("UNAVAILABLE", "CURRENT_ONLY", "UNKNOWN"):
                avail[name] = DataAvailabilityRecord(
                    observable=rec.observable, status="AVAILABLE",
                    history_depth=rec.history_depth,
                    instrument_coverage=rec.instrument_coverage,
                    claimed=True, verified=True, source=rec.source)

    blocked = []
    demands = []
    for r in reqs:
        rec = avail.get(r.required_observable)
        status = rec.status if rec else "UNKNOWN"
        adequate = rec.adequate_history(r) if rec else False
        disp = g5_policy_outcome(
            policy, _policy_facts(pack, claim_type="MECHANISM_HYPOTHESIS",
                                  data_availability=("AVAILABLE" if adequate
                                                     else status),
                                  sensor_resolution=("SUFFICIENT" if adequate
                                                     else "INSUFFICIENT"),
                                  mechanism_status="PRESENT"),
            "availability", "DATA_BLOCKED")
        blocked.append({
            "requirement_id": r.requirement_id,
            "claim_ref": r.claim_ref,
            "required_observable": r.required_observable,
            "data_availability": status,
            "adequate_history": adequate,
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
                value_of_information_class="HIGH",
                acceptable_sources=r.instrument_coverage,
                history_requirement=r.history_depth,
                quality_requirement=r.quality_minimum,
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
        facts["evidence_refs"] = ["EV_S18_SENSOR"]
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
            protocol_frozen: bool = True,
            broken_mapping: bool = False) -> G5RunResult:
    """Crypto concept -> FX transfer is a HYPOTHESIS until target-domain
    validation. Name similarity alone is ANALOGY. CEREBUS doctrine is never
    overridden by a cross-domain analogy."""
    transfers = [DomainTransferHypothesis.from_fixture(t)
                 for t in pack.transfer_hypotheses]
    items = []
    for t in transfers:
        map_ok = t.transfer_map.structurally_sound() and not broken_mapping
        # determine hypothesis status: broken structural assumption vs mere
        # name-similarity (no invariants) are distinct dispositions
        if broken_mapping or t.transfer_map.known_broken_assumptions:
            hstatus = "BROKEN_MAPPING"
        elif not map_ok:
            hstatus = "ANALOGY"
        else:
            hstatus = "HYPOTHESIS"
        # target data: fixture availability if not overridden
        if target_data_available is None:
            avail = {a["observable"]: a["status"]
                     for a in pack.data_availability}
            statuses = [avail.get(s, "UNKNOWN")
                        for s in t.transfer_map.required_sensors]
            target_ok = statuses and all(s == "AVAILABLE" for s in statuses)
        else:
            target_ok = target_data_available

        disp = g5_policy_outcome(
            policy,
            _policy_facts(pack,
                          claim_type="TRANSFER_HYPOTHESIS",
                          domain_transfer_status=hstatus,
                          target_data_availability=("AVAILABLE" if target_ok
                                                    else "UNAVAILABLE"),
                          protocol_frozen=protocol_frozen),
            "transfer", "TRANSFER_HYPOTHESIS_ONLY")
        items.append({
            "hypothesis_id": t.hypothesis_id,
            "source_concept": t.source_concept,
            "source_domain": t.source_domain,
            "target_domain": t.target_domain,
            "transfer_map": t.transfer_map.to_dict(),
            "mapping_sound": map_ok,
            "target_data_available": target_ok,
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