"""G3-B review topology and constraint routing (S07).

A ReviewTopology describes one admissible arrangement of reviewers for a claim.
Cognitive routing is CONSTRAINED SATISFACTION, not a scalar ranking:

    goal:        obtain sufficient evidence for the consequence class
    constraints: minimum capability, required independence dimensions,
                 budget (cost/latency), context restrictions

The router picks the CHEAPEST admissible topology (deterministic tie-break).
Capability and epistemic independence are SEPARATE axes: a diverse set of
insufficient-capability reviewers cannot pass merely because it is diverse, and
a monoculture of high-capability reviewers cannot satisfy independence
constraints. No `quality * independence` scalar is ever formed.

Constraints come from a PROVISIONAL test contract (per consequence class), not
from constitutional truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .cognitive_ecology import (
    PROFILE_SCHEMA_VERSION,
    UNKNOWN,
    ReviewerIndependenceProfile,
)

CONSEQUENCE_CLASSES = ("HIGH", "MEDIUM", "LOW")


@dataclass(frozen=True)
class TopologyConstraintContract:
    """PROVISIONAL per-consequence constraints for G3 routing tests."""

    contract_id: str
    version_tag: str = "V1"
    status: str = "PROVISIONAL_SCENARIO_TEST_POLICY"
    constraints: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    # e.g. {
    #   "HIGH": {"min_capability": "ADEQUATE", "min_source_lineages": 2,
    #            "min_model_or_runtime_lineages": 2, "max_prior_exposure_ratio": 0.0,
    #            "max_cost_units": 100, "max_latency_units": 50,
    #            "min_fresh_or_independent_design": 1},
    #   "LOW":  {"min_capability": "ADEQUATE", "max_cost_units": 30, ...}
    # }

    def for_consequence(self, consequence_class: str) -> Mapping[str, Any]:
        if consequence_class not in CONSEQUENCE_CLASSES:
            raise ValueError(f"unknown consequence class {consequence_class!r}")
        return dict(self.constraints.get(consequence_class, {}))

    def fingerprint(self) -> str:
        return deterministic_hex("topology_contract", self.contract_id, self.version_tag,
                                 self.constraints, length=24)


@dataclass(frozen=True)
class ReviewTopology:
    """One candidate arrangement of reviewers for a claim."""

    topology_id: str
    purpose: str
    consequence_class: str
    profiles: Tuple[ReviewerIndependenceProfile, ...]
    capability_tiers: Tuple[str, ...]               # per profile; synthetic metadata only
    cost_units: int = 0
    latency_units: int = 0
    fresh_context_count: int = 0
    counter_attractor_budget: int = 0
    stop_conditions: Tuple[str, ...] = ()
    independently_originated_design_count: int = 0   # G3R-06: provenance-based, not name-based

    def reviewer_count(self) -> int:
        return len(self.profiles)

    def fresh_or_independent_design_count(self) -> int:
        """G3R-06: fresh-context paths OR provenance-verified independent design
        origins both qualify for a fresh-or-design requirement."""
        return self.fresh_context_count + self.independently_originated_design_count

    def independence_counts(self) -> Dict[str, int]:
        axes = {
            "model_family": set(),
            "runtime_lineage": set(),
            "source_lineage": set(),
            "retrieval_bundle": set(),
            "experiment_design_origin": set(),
            "allocator": set(),
        }
        for p in self.profiles:
            for ax, val in (("model_family", p.model_family), ("runtime_lineage", p.runtime_lineage),
                            ("retrieval_bundle", p.retrieval_bundle),
                            ("experiment_design_origin", p.experiment_design_origin),
                            ("allocator", p.allocator)):
                if val != UNKNOWN and val:
                    axes[ax].add(val)
            axes["source_lineage"].update(p.source_lineages)
        return {ax: len(v) for ax, v in axes.items()}

    def prior_exposure_ratio(self) -> float:
        if not self.profiles:
            return 0.0
        exposed = sum(1 for p in self.profiles if p.prior_conclusion_exposure is True)
        return exposed / len(self.profiles)

    def max_capability(self) -> str:
        rank = {"BASIC": 1, "ADEQUATE": 2, "HIGH": 3}
        best = "BASIC"
        for t in self.capability_tiers:
            if rank.get(t, 0) > rank[best]:
                best = t
        return best

    def fingerprint(self) -> str:
        return deterministic_hex(
            "review_topology", self.topology_id, self.consequence_class,
            [p.to_dict() for p in self.profiles], self.cost_units, self.latency_units,
            length=24,
        )


@dataclass(frozen=True)
class ReviewTopologyDecision:
    decision_id: str
    purpose: str
    consequence_class: str
    chosen_topology_id: str
    reason: str
    constraints_satisfied: bool
    cost_units: int
    latency_units: int
    independence_dimensions_achieved: Mapping[str, int]
    individual_quality_metadata: Mapping[str, str]   # reviewer -> capability tier
    remaining_gaps: Tuple[str, ...]
    admissible_alternatives: Tuple[str, ...]          # other admissible topology ids
    contract_id: str = ""
    contract_fingerprint: str = ""
    # G3R-10: choosing a better topology is NOT the same as having obtained
    # evidence from it. The G3 router only RECOMMENDS; evidence is obtained
    # only when the executed topology actually produces decision-grade results.
    execution_status: str = "REVIEW_TOPOLOGY_RECOMMENDED"   # RECOMMENDED | EXECUTED
    evidence_obtained: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "decision_id", "purpose", "consequence_class", "chosen_topology_id",
            "reason", "constraints_satisfied", "cost_units", "latency_units",
            "independence_dimensions_achieved", "individual_quality_metadata",
            "remaining_gaps", "admissible_alternatives", "contract_id",
            "contract_fingerprint", "execution_status", "evidence_obtained")}


def _capability_ok(tier: str, required: str) -> bool:
    rank = {"BASIC": 1, "ADEQUATE": 2, "HIGH": 3}
    return rank.get(tier, 0) >= rank.get(required, 0)


def _topology_admissible(topo: ReviewTopology, constraints: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    gaps: List[str] = []
    # G3R-09 capability semantics are EXPLICIT — the contract states what it
    # means. `min_capability` is the conservative alias for "every required
    # reviewer must meet the tier" (fail-closed: one HIGH + several BASIC must
    # not pass a contract intended to require ADEQUATE review paths).
    # `minimum_all_required_roles_capability` is the same semantic spelled out;
    # `minimum_any_reviewer_capability` is the explicit at-least-one semantic.
    required_all = str(constraints.get("minimum_all_required_roles_capability")
                       or constraints.get("min_capability") or "")
    required_any = str(constraints.get("minimum_any_reviewer_capability") or "")
    if required_all and (not topo.capability_tiers
                         or any(not _capability_ok(t, required_all) for t in topo.capability_tiers)):
        gaps.append(f"capability below {required_all} for all required reviewers")
    if required_any and not any(_capability_ok(t, required_any) for t in topo.capability_tiers):
        gaps.append(f"no reviewer at {required_any}+ capability")
    counts = topo.independence_counts()
    if counts["source_lineage"] < int(constraints.get("min_source_lineages", 0)):
        gaps.append("insufficient distinct source lineages")
    model_or_runtime = max(counts["model_family"], counts["runtime_lineage"])
    if model_or_runtime < int(constraints.get("min_model_or_runtime_lineages", 0)):
        gaps.append("insufficient model/runtime lineage diversity")
    if topo.prior_exposure_ratio() > float(constraints.get("max_prior_exposure_ratio", 1.0)):
        gaps.append("prior-conclusion exposure above allowed ratio")
    # G3R-06: fresh-context OR provenance-verified independent design qualify
    if int(constraints.get("min_fresh_context", 0)) and \
            topo.fresh_context_count < int(constraints.get("min_fresh_context", 0)):
        gaps.append("insufficient fresh-context paths")
    if int(constraints.get("min_independent_design", 0)) and \
            topo.independently_originated_design_count < int(constraints.get("min_independent_design", 0)):
        gaps.append("insufficient independently-originated design paths")
    if int(constraints.get("min_fresh_or_independent_design", 0)) and \
            topo.fresh_or_independent_design_count() < int(constraints.get("min_fresh_or_independent_design", 0)):
        gaps.append("insufficient fresh-context / independent-design paths")
    if topo.cost_units > int(constraints.get("max_cost_units", 10 ** 9)):
        gaps.append("cost above budget")
    if topo.latency_units > int(constraints.get("max_latency_units", 10 ** 9)):
        gaps.append("latency above budget")
    return (not gaps, gaps)


def route_review_topology(
    purpose: str,
    consequence_class: str,
    candidate_topologies: Sequence[ReviewTopology],
    contract: TopologyConstraintContract,
) -> ReviewTopologyDecision:
    """Cheapest admissible topology satisfying the consequence-class constraints.
    Deterministic tie-break: (cost_units, reviewer_count, topology_id)."""
    if consequence_class not in CONSEQUENCE_CLASSES:
        raise ValueError(f"unknown consequence class {consequence_class!r}")
    constraints = contract.for_consequence(consequence_class)
    admissible: List[ReviewTopology] = []
    gaps_by_id: Dict[str, List[str]] = {}
    for topo in candidate_topologies:
        ok, gaps = _topology_admissible(topo, constraints)
        gaps_by_id[topo.topology_id] = gaps
        if ok:
            admissible.append(topo)
    admissible.sort(key=lambda t: (t.cost_units, t.reviewer_count(), t.topology_id))

    chosen = admissible[0] if admissible else None
    chosen_id = chosen.topology_id if chosen else ""
    reason = (
        f"cheapest admissible topology for {consequence_class} consequence "
        f"(cost={chosen.cost_units if chosen else '-'}, reviewers={chosen.reviewer_count() if chosen else 0})"
        if chosen else "NO admissible topology; constraints unmet (see remaining_gaps)"
    )
    quality = {}
    if chosen:
        quality = dict(zip([p.reviewer_id for p in chosen.profiles], chosen.capability_tiers))
    decision = ReviewTopologyDecision(
        decision_id=deterministic_hex("topology_decision", purpose, consequence_class, chosen_id, reason),
        purpose=purpose,
        consequence_class=consequence_class,
        chosen_topology_id=chosen_id,
        reason=reason,
        constraints_satisfied=chosen is not None,
        cost_units=chosen.cost_units if chosen else 0,
        latency_units=chosen.latency_units if chosen else 0,
        independence_dimensions_achieved=chosen.independence_counts() if chosen else {},
        individual_quality_metadata=quality,
        remaining_gaps=tuple(gaps_by_id.get(chosen_id, []) if chosen else
                             sorted({g for gs in gaps_by_id.values() for g in gs})),
        admissible_alternatives=tuple(t.topology_id for t in admissible[1:]),
        contract_id=contract.contract_id,
        contract_fingerprint=contract.fingerprint(),
    )
    return decision
