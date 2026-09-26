"""G3 deterministic scenario runner (S06–S09).

Pipeline (mirrors G2 §2 discipline):

    scenario pack
        -> decision-grade projection (expected disposition + hidden ground truth REMOVED)
        -> ReviewerIndependenceProfiles (sealed fixture provenance; registry truth wins)
        -> DependencyGraph -> ConsensusRecord -> EcologyFacts
        -> shared G3_COGNITIVE_ECOLOGY_POLICY (disposition / friction / counter-attractor)
        -> optional topology routing (S07), friction (S08), counter-attractor (S09)
        -> result with behavior_fingerprint (scenario-id-free, reviewer-id-NORMALIZED)
        -> expectations applied post-hoc only

Sealing guarantees:
  * expected_disposition and hidden_ground_truth never reach the decision path;
  * behavior_fingerprint excludes scenario_id, expected outcomes, hidden truth
    and reviewer_id literals — a scenario rename or reviewer rename that
    preserves relations does not change institutional behavior;
  * provenance fields are sealed BEFORE routing/adjudication: if a reviewer
    lies about lineage, the fixture truth in the registry wins (CON-03
    observation); unknown stays UNKNOWN.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .cognitive_ecology import (
    DEFAULT_PROVENANCE_MODE,
    PROVENANCE_MODES,
    AllocationProvenance,
    CognitiveEcologyHealthRecord,
    ConsensusRecord,
    DependencyGraph,
    EcologyFacts,
    ProvenanceConflict,
    ProvenanceConflictLedger,
    ReplicationPathRecord,
    ReviewerIndependenceProfile,
    ReviewerProvenanceRegistry,
    SyntheticFixtureAuthority,
    UNKNOWN,
    independent_confirmation_satisfied,
)
from .ecology_policy import EcologyPolicy, EcologyRule
from .friction import (
    CounterAttractorReview,
    CounterAttractorSpec,
    FrictionContract,
    FrictionResult,
    counter_attractor_trigger,
    friction_trigger,
    run_counter_attractor,
    run_friction,
)
from .review_topology import (
    ReviewTopology,
    ReviewTopologyDecision,
    TopologyConstraintContract,
    route_review_topology,
)


@dataclass
class G3ScenarioPack:
    """One G3 scenario's decision-grade data + sealed expectations."""

    scenario_id: str
    scenario_version: str = "1.0.0"
    claim_id: str = ""
    claim: str = ""
    consequence_class: str = "LOW"
    policy_ref: str = ""
    reviewers: List[Mapping[str, Any]] = field(default_factory=list)
    topology_options: List[Mapping[str, Any]] = field(default_factory=list)
    topology_contract: Optional[Mapping[str, Any]] = None
    friction_contract: Optional[Mapping[str, Any]] = None
    friction_reviewers: Optional[List[Mapping[str, Any]]] = None
    conclusions_by_exposure: Optional[Mapping[str, Mapping[str, str]]] = None
    counter_attractor_spec: Optional[Mapping[str, Any]] = None
    counter_attractor_findings: List[Mapping[str, Any]] = field(default_factory=list)
    independent_replication_count: int = 0
    replication_paths: Optional[List[Mapping[str, Any]]] = None   # G4-P0-A explicit identities
    allocation_provenance: Mapping[str, Any] = field(default_factory=dict)
    registered_provenance: Optional[List[Mapping[str, Any]]] = None   # G3R-07 governed registry
    provenance_mode: str = DEFAULT_PROVENANCE_MODE   # G3R2-02: GOVERNED_REGISTRY | AUTHORITATIVE_SYNTHETIC_FIXTURE
    expected_disposition: str = ""            # SEALED — stripped before run
    hidden_ground_truth: Optional[dict] = None  # SEALED

    def decision_grade(self) -> "G3ScenarioPack":
        out = {
            k: v for k, v in self.__dict__.items()
            if k not in ("expected_disposition", "hidden_ground_truth")
        }
        return G3ScenarioPack(**out)


@dataclass
class G3RunResult:
    artifacts: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.artifacts)


def load_g3_pack(pack_dir: Path) -> G3ScenarioPack:
    root = Path(pack_dir)
    spec = json.loads((root / "scenario.json").read_text(encoding="utf-8"))
    reviewers = json.loads((root / spec.get("reviewers_ref", "reviewers.json")).read_text(encoding="utf-8"))
    topo = None
    if spec.get("topology_options_ref"):
        topo = json.loads((root / spec["topology_options_ref"]).read_text(encoding="utf-8"))
    friction = None
    if spec.get("friction_ref"):
        friction = json.loads((root / spec["friction_ref"]).read_text(encoding="utf-8"))
    counter = None
    if spec.get("counter_attractor_ref"):
        counter = json.loads((root / spec["counter_attractor_ref"]).read_text(encoding="utf-8"))
    registered = None
    if spec.get("registered_provenance_ref"):
        registered = json.loads((root / spec["registered_provenance_ref"]).read_text(encoding="utf-8"))
    return G3ScenarioPack(
        scenario_id=str(spec["scenario_id"]),
        scenario_version=str(spec.get("scenario_version", "1.0.0")),
        claim_id=str(spec.get("claim_id", "")),
        claim=str(spec.get("claim", "")),
        consequence_class=str(spec.get("consequence_class", "LOW")),
        policy_ref=str(spec.get("policy_ref", "")),
        reviewers=list(reviewers),
        topology_options=list((topo or {}).get("topology_options", [])),
        topology_contract=(topo or {}).get("contract"),
        friction_contract=(friction or {}).get("contract"),
        friction_reviewers=(friction or {}).get("reviewers"),
        conclusions_by_exposure=(friction or {}).get("conclusions_by_exposure"),
        counter_attractor_spec=(counter or {}).get("spec"),
        counter_attractor_findings=list((counter or {}).get("findings", [])),
        independent_replication_count=int(spec.get("independent_replication_count", 0)),
        replication_paths=spec.get("replication_paths"),
        allocation_provenance=dict(spec.get("allocation_provenance", {})),
        registered_provenance=list(registered) if registered is not None else None,
        provenance_mode=str(spec.get("provenance_mode", DEFAULT_PROVENANCE_MODE)),
        expected_disposition=str(spec.get("expected_disposition", "")),
        hidden_ground_truth=spec.get("hidden_ground_truth"),
    )


def _relations_fingerprint(profiles: Sequence[ReviewerIndependenceProfile]) -> str:
    """Reviewer-id-free relational fingerprint: exposure modes, axes and
    conclusions. Rows are sorted by their RELATIONS (never by reviewer id), so
    renaming reviewers cannot change behavior identity."""
    rows = []
    for p in profiles:
        rows.append((p.exposure_mode, p.model_family, p.provider, p.runtime_lineage,
                     tuple(sorted(p.source_lineages)), p.retrieval_bundle, p.prompt_context,
                     p.prior_conclusion_exposure, p.implementation_path,
                     p.experiment_design_origin, p.allocator, p.fresh_context, p.conclusion))
    return deterministic_hex("relations", sorted(rows), length=24)


def _friction_relations(fr: Optional[FrictionResult]) -> Tuple[Any, ...]:
    if fr is None:
        return ()
    # actions are included reviewer-id-free (method + result only) so method
    # governance is part of behavior identity while reviewer renames stay inert
    actions = tuple(sorted((a.method, a.result) for a in fr.actions))
    return (fr.triggered, fr.budget_used, tuple(sorted(fr.surfaced_alternatives)),
            fr.information_gain, fr.evidence_gap, fr.cost_units, actions)


def _counter_relations(cr: Optional[CounterAttractorReview]) -> Tuple[Any, ...]:
    if cr is None:
        return ()
    non_admissible = tuple(sorted(
        f.get("method", "") for f in cr.non_admissible_findings))
    return (cr.terminal_result, cr.discriminating_contradiction_found, cr.budget_used,
            cr.review_budget, tuple(cr.allowed_methods), tuple(sorted(cr.evidence_produced)),
            non_admissible)


def _topology_relations(td: Optional[ReviewTopologyDecision]) -> Tuple[Any, ...]:
    if td is None:
        return ()
    return (td.chosen_topology_id, td.constraints_satisfied, td.cost_units, td.latency_units,
            tuple(sorted(td.independence_dimensions_achieved.items())),
            tuple(sorted(td.individual_quality_metadata.values())),
            tuple(td.remaining_gaps), tuple(td.admissible_alternatives))


def run_g3_scenario(
    pack: G3ScenarioPack,
    policy: EcologyPolicy,
    policy_fingerprint: str = "",
) -> G3RunResult:
    """Execute one G3 scenario against the shared ecology policy. `pack` MUST be
    the decision-grade projection (no expected disposition, no hidden truth)."""
    if pack.expected_disposition or pack.hidden_ground_truth is not None:
        raise ValueError("run_g3_scenario refuses sealed fields: pass pack.decision_grade()")

    # ---- G3R2-02: EXPLICIT provenance authority. Default (GOVERNED_REGISTRY)
    # fails closed: no registry file => no verified provenance => claims are
    # never promoted. AUTHORITATIVE_SYNTHETIC_FIXTURE is explicit in the
    # scenario contract: the harness owns the synthetic ground truth for the
    # whole pack (primary + topology + friction reviewers), so fixture fields
    # ARE authoritative observable data. Never inferred from the absence of a
    # registry file.
    mode = pack.provenance_mode or DEFAULT_PROVENANCE_MODE
    if mode not in PROVENANCE_MODES:
        raise ValueError(f"unknown provenance mode {mode!r}; expected one of {PROVENANCE_MODES}")
    synthetic_authority = SyntheticFixtureAuthority() if mode == "AUTHORITATIVE_SYNTHETIC_FIXTURE" \
        else None
    registry: Optional[ReviewerProvenanceRegistry] = None

    def _bind(fixtures: Sequence[Mapping[str, Any]]
              ) -> Tuple[Tuple[ReviewerIndependenceProfile, ...], Tuple[ProvenanceConflict, ...]]:
        """Bind one cognitive surface (primary / topology / friction) under the
        scenario's provenance authority. G3R2-03: secondary surfaces use the
        SAME semantics as the primary surface — synthetic fixtures are identity
        (harness-authoritative); governed mode binds against the registry with
        fail-closed UNKNOWN for missing entries."""
        if not fixtures:
            return (), ()
        claimed = [ReviewerIndependenceProfile.from_reviewer_fixture(r) for r in fixtures]
        if mode == "AUTHORITATIVE_SYNTHETIC_FIXTURE":
            return tuple(claimed), ()
        assert registry is not None
        return registry.bind_all(claimed)

    if mode == "AUTHORITATIVE_SYNTHETIC_FIXTURE":
        profiles, provenance_conflicts = _bind(pack.reviewers)
    else:
        registry = ReviewerProvenanceRegistry.from_fixtures(pack.registered_provenance or [])
        profiles, provenance_conflicts = _bind(pack.reviewers)
    if not profiles:
        raise ValueError("G3 scenario requires at least one reviewer")

    # ---- G4-P0-B: every surface's provenance conflicts join the run ledger --- #
    ledger = ProvenanceConflictLedger()
    ledger.record("PRIMARY_REVIEW", provenance_conflicts)

    # ---- G4-P0-A: replication needs explicit path identities. A raw count is
    # display-only; in GOVERNED_REGISTRY mode it never mints paths. Synthetic
    # fixtures without explicit paths keep the legacy harness-declared count
    # semantics (historical G3 receipts preserved).
    rep_records = None
    if pack.replication_paths:
        rep_records = [ReplicationPathRecord.from_fixture(r) for r in pack.replication_paths]
    elif mode == "GOVERNED_REGISTRY":
        rep_records = []

    # ---- consensus + facts ------------------------------------------------- #
    graph = DependencyGraph.build(profiles)
    consensus = ConsensusRecord.build(pack.claim_id, profiles, graph)
    conflict_tuples: Tuple[ProvenanceConflict, ...] = provenance_conflicts
    facts = EcologyFacts.from_consensus(
        consensus,
        consequence_class=pack.consequence_class,
        independent_replication_count=pack.independent_replication_count,
        replication_paths=rep_records,
    )

    # ---- shared policy evaluation (generic predicates only) ---------------- #
    fact_flags = facts.to_dict()
    fact_flags["independent_confirmation_satisfied"] = independent_confirmation_satisfied(facts)

    disposition_rule: Optional[EcologyRule] = policy.evaluate(fact_flags, "disposition")
    disposition = (disposition_rule.then.get("disposition", "") if disposition_rule else "")
    if disposition:
        consensus = replace(consensus, disposition=disposition)

    friction_rule = policy.evaluate(fact_flags, "friction")
    counter_rule = policy.evaluate(fact_flags, "counter_attractor")

    # ---- optional machinery per scenario ----------------------------------- #
    topology_decision: Optional[ReviewTopologyDecision] = None
    friction_result: Optional[FrictionResult] = None
    counter_result: Optional[CounterAttractorReview] = None
    friction_reviewers: List[ReviewerIndependenceProfile] = []
    cost_units = 0
    latency_units = 0

    if pack.topology_options:
        contract = TopologyConstraintContract(**dict(pack.topology_contract or {}))
        candidates = []
        for spec in pack.topology_options:
            topo_reviewers = list(spec.get("reviewers", []))
            topo_profiles, topo_conflicts = _bind(topo_reviewers)
            ledger.record("TOPOLOGY_CANDIDATE", topo_conflicts)
            if mode == "AUTHORITATIVE_SYNTHETIC_FIXTURE":
                # G3R2-10: fixture capability tiers are harness-authoritative.
                capability_tiers = tuple(str(r.get("capability_tier", "BASIC"))
                                         for r in topo_reviewers)
                capability_source = "AUTHORITATIVE_SYNTHETIC_CAPABILITY"
            else:
                # governed: tiers only from REGISTERED capability facts;
                # missing/UNKNOWN registered capability => UNVERIFIED (fails
                # any positive minimum-capability requirement).
                tiers: List[str] = []
                all_registered = bool(topo_reviewers)
                for r in topo_reviewers:
                    reg = registry.registered(str(r.get("reviewer_id", "")))
                    if reg is None or reg.capability_tier == UNKNOWN:
                        tiers.append(UNKNOWN)
                        all_registered = False
                    else:
                        tiers.append(reg.capability_tier)
                capability_tiers = tuple(tiers)
                capability_source = ("REGISTERED_CAPABILITY" if all_registered
                                     else "UNVERIFIED_CAPABILITY")
            candidates.append(ReviewTopology(
                topology_id=str(spec.get("topology_id", "")),
                purpose=pack.claim,
                consequence_class=pack.consequence_class,
                profiles=tuple(topo_profiles),
                capability_tiers=capability_tiers,
                capability_source=capability_source,
                cost_units=int(spec.get("cost_units", 0)),
                latency_units=int(spec.get("latency_units", 0)),
                fresh_context_count=sum(1 for p in topo_profiles if p.fresh_context),
                independently_originated_design_count=sum(
                    1 for p in topo_profiles if p.independently_originated_design),
                counter_attractor_budget=int(spec.get("counter_attractor_budget", 0)),
                stop_conditions=tuple(spec.get("stop_conditions", [])),
            ))
        topology_decision = route_review_topology(pack.claim, pack.consequence_class,
                                                  candidates, contract)
        cost_units += topology_decision.cost_units
        latency_units += topology_decision.latency_units

    dominant = (max(consensus.raw_vote_distribution, key=lambda k: consensus.raw_vote_distribution[k])
                if consensus.raw_vote_distribution else "")

    if friction_rule is not None and friction_rule.then.get("trigger", False):
        fcontract = FrictionContract(**dict(pack.friction_contract or {
            "contract_id": "DEFAULT-FRICTION", "consequence_classes": {}}))
        trigger = friction_trigger(facts, fcontract)
        # G3R2-03: fresh-context/friction reviewers use the SAME provenance
        # authority — a reviewer cannot self-declare BLIND without
        # registered/synthetic-authoritative provenance.
        friction_reviewers, friction_conflicts = _bind(list(pack.friction_reviewers or []))
        ledger.record("FRICTION_REVIEW", friction_conflicts)
        friction_result = run_friction(
            trigger, friction_reviewers,
            pack.conclusions_by_exposure or {},
            incumbent_conclusion=dominant,
            budget=trigger.budget,
            cost_per_reconstruction=int((fcontract.for_consequence(pack.consequence_class)
                                         .get("cost_per_reconstruction", 5))),
        )
        cost_units += friction_result.cost_units

    if counter_rule is not None and counter_rule.then.get("trigger", False):
        spec = CounterAttractorSpec(**dict(pack.counter_attractor_spec or {"spec_id": "DEFAULT-COUNTER"}))
        if counter_attractor_trigger(facts, spec):
            counter_result = run_counter_attractor(spec, dominant or pack.claim,
                                                   pack.counter_attractor_findings)
            cost_units += counter_result.cost_units

    # ---- observational health record (vector, no scalar) ------------------- #
    health = CognitiveEcologyHealthRecord.observe(
        consensus, facts,
        counter_attractor_frequency=1 if counter_result else 0,
        review_cost_units=cost_units,
        information_gain=bool(friction_result and friction_result.information_gain),
        correlated_failure_warning=(
            (facts.max_single_source_lineage_prevalence is not None
             and facts.max_single_source_lineage_prevalence >= 0.8)
            or (facts.source_concentration is not None and facts.source_concentration >= 0.8
                and facts.distinct_source_lineages <= 1)),
    )

    # ---- fingerprints -------------------------------------------------------- #
    relations_fp = _relations_fingerprint(list(profiles) + list(friction_reviewers))
    behavior_fingerprint = deterministic_hex(
        "g3_behavior", pack.consequence_class, facts.to_dict(), disposition,
        relations_fp,
        _topology_relations(topology_decision),
        _friction_relations(friction_result),
        _counter_relations(counter_result),
        policy_fingerprint or policy.fingerprint(),
        length=32,
    )
    run_identity_fingerprint = deterministic_hex(
        "g3_run", pack.scenario_id, pack.claim_id, behavior_fingerprint, length=32,
    )

    return G3RunResult({
        "scenario_id": pack.scenario_id,
        "scenario_version": pack.scenario_version,
        "claim_id": pack.claim_id,
        "claim": pack.claim,
        "consequence_class": pack.consequence_class,
        "consensus": consensus.to_dict(),
        "dependency_graph_fingerprint": graph.fingerprint(),
        "pair_overlap_counts": graph.pair_overlap_counts(),
        "fully_correlated_pairs": graph.fully_correlated_pairs(),
        "facts": facts.to_dict(),
        "independent_confirmation_satisfied": fact_flags["independent_confirmation_satisfied"],
        "disposition_rule": disposition_rule.rule_id if disposition_rule else "",
        "disposition": disposition,
        "friction_rule": friction_rule.rule_id if friction_rule else "",
        "friction_triggered": bool(friction_result and friction_result.triggered),
        "counter_attractor_rule": counter_rule.rule_id if counter_rule else "",
        "topology_decision": topology_decision.to_dict() if topology_decision else None,
        "topology_execution_status": (topology_decision.execution_status
                                       if topology_decision else None),
        "evidence_obtained_from_executed_topology": bool(
            topology_decision and topology_decision.evidence_obtained),
        "provenance_conflicts": [c.to_dict() for c in conflict_tuples],
        "provenance_conflict_ledger": ledger.to_dict(),
        "friction_result": friction_result.to_dict() if friction_result else None,
        "counter_attractor_result": counter_result.to_dict() if counter_result else None,
        "health_record": health.to_dict(),
        "allocation_provenance": dict(pack.allocation_provenance),
        "raw_reviewer_count": facts.raw_reviewer_count,
        "raw_vote_distribution": consensus.raw_vote_distribution,
        "cost_units": cost_units,
        "latency_units": latency_units,
        "authority_before": "NONE",
        "authority_after": "NONE",
        "expected_disposition_accessed": False,
        "hidden_ground_truth_accessed": False,
        "provenance_mode": mode,
        "synthetic_fixture_authority_used": mode == "AUTHORITATIVE_SYNTHETIC_FIXTURE",
        "synthetic_fixture_authority": synthetic_authority.to_dict() if synthetic_authority else None,
        "policy_id": policy.policy_id,
        "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "behavior_fingerprint": behavior_fingerprint,
        "fingerprint": run_identity_fingerprint,
    })


def evaluate_g3_expectation(result: G3RunResult, pack: G3ScenarioPack) -> Dict[str, Any]:
    """Post-hoc comparator — expectations applied strictly AFTER execution."""
    expected = pack.expected_disposition
    actual = result.artifacts.get("disposition", "")
    failures = []
    if expected and actual != expected:
        failures.append(f"disposition {actual!r} != expected {expected!r}")
    return {
        "pass": not failures,
        "expected_disposition": expected,
        "actual_disposition": actual,
        "failures": failures,
    }
