"""G3 cognitive ecology — independence semantics, consensus, ecology facts.

G3-P0 normalizes independence semantics before any S06–S09 scenario:

* P0-A: model/runtime independence is NEVER inferred from source independence.
  Two agents can share sources yet differ in model family; two model families
  can consume the same evidence bundle. Each axis is represented explicitly;
  an unknown axis stays UNKNOWN and contributes nothing (unknown is never
  treated as independent).
* P0-B: no ambiguous `shared_*` booleans. Explicit quantities/relations:
  distinct_allocator_count, distinct_retrieval_bundle_count, and per-axis
  concentration fractions (fraction of reviewers sharing the modal value).
  The G2R-era `LineageSummary` is FROZEN for historical G2R receipts and is
  deliberately NOT extended here — G3 uses this versioned profile instead.
* No effective-sample-size scalar is minted (AMB-03 stays OPEN). Raw consensus
  is an observation, never multiplied epistemic confidence.

G3-A adds the pairwise dependency graph, ConsensusRecord, CorrelatedFailureRecord
and the CognitiveEcologyHealthRecord (an observational vector with NO authority).

Everything is deterministic, local, model-free, and wall-clock-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex

# --------------------------------------------------------------------------- #
# G3-P0 constants
# --------------------------------------------------------------------------- #

PROFILE_SCHEMA_VERSION = "2.0.0"          # G3 versioned profile (vs G2R LineageSummary)
UNKNOWN = "UNKNOWN"

# §8 information membranes — semi-permeable cognition, staged reveal.
EXPOSURE_MODES = (
    "BLIND",
    "EVIDENCE_ONLY",
    "PRIOR_HYPOTHESIS_VISIBLE",
    "PRIOR_CONCLUSION_VISIBLE",
    "FULL_SHARED_CONTEXT",
)

# §3 pairwise dependency axes — preserved separately, never collapsed.
PAIRWISE_AXES = (
    "model_family",
    "provider",
    "runtime_lineage",
    "source_lineage",
    "retrieval_bundle",
    "prompt_context",
    "prior_conclusion_exposure",
    "implementation_path",
    "experiment_design",
    "allocator",
)

# §2 reviewer profile axes (a subset used for concentration/unknown accounting).
PROFILE_AXES = (
    "model_family",
    "provider",
    "runtime_lineage",
    "retrieval_bundle",
    "prompt_context",
    "implementation_path",
    "experiment_design_origin",
    "allocator",
)


def _norm(value: Any) -> str:
    """Normalize an axis value; empty/None become UNKNOWN (never independent)."""
    if value is None:
        return UNKNOWN
    s = str(value).strip()
    return s if s else UNKNOWN


# --------------------------------------------------------------------------- #
# §2 ReviewerIndependenceProfile — one evidence-producing path (versioned V1)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ReviewerIndependenceProfile:
    """Per-reviewer independence axes. `prior_conclusion_exposure` is tri-state:
    True / False / None (UNKNOWN). A reviewer whose provenance says nothing about
    an axis gets UNKNOWN on that axis — never a favorable inference."""

    reviewer_id: str
    schema_version: str = PROFILE_SCHEMA_VERSION
    role: str = UNKNOWN
    model_family: str = UNKNOWN
    provider: str = UNKNOWN
    runtime_lineage: str = UNKNOWN
    source_lineages: Tuple[str, ...] = ()
    retrieval_bundle: str = UNKNOWN
    prompt_context: str = UNKNOWN
    prior_conclusion_exposure: Optional[bool] = None
    implementation_path: str = UNKNOWN
    experiment_design_origin: str = UNKNOWN
    allocator: str = UNKNOWN
    fresh_context: bool = False
    exposure_mode: str = "FULL_SHARED_CONTEXT"
    claim_id: str = ""
    conclusion: str = ""
    confidence_if_supplied: str = UNKNOWN      # NEVER evidence of independence
    evidence_refs: Tuple[str, ...] = ()

    @classmethod
    def from_reviewer_fixture(cls, reviewer: Mapping[str, Any]) -> "ReviewerIndependenceProfile":
        sources = tuple(str(s) for s in (reviewer.get("sources") or []))
        pce = reviewer.get("prior_conclusion_exposure")
        if isinstance(pce, str):
            pce = {"TRUE": True, "FALSE": False, "UNKNOWN": None}.get(pce.upper())
        return cls(
            reviewer_id=str(reviewer.get("reviewer_id", "")),
            role=_norm(reviewer.get("role")),
            model_family=_norm(reviewer.get("model_family")),
            provider=_norm(reviewer.get("provider")),
            runtime_lineage=_norm(reviewer.get("runtime_lineage")),
            source_lineages=sources,
            retrieval_bundle=_norm(reviewer.get("retrieval_bundle")),
            prompt_context=_norm(reviewer.get("prompt_context")),
            prior_conclusion_exposure=pce,
            implementation_path=_norm(reviewer.get("implementation_path")),
            experiment_design_origin=_norm(reviewer.get("experiment_design_origin")),
            allocator=_norm(reviewer.get("allocator")),
            fresh_context=bool(reviewer.get("fresh_context", False)),
            exposure_mode=str(reviewer.get("visible_information", "FULL_SHARED_CONTEXT")),
            claim_id=str(reviewer.get("claim_id", "")),
            conclusion=str(reviewer.get("conclusion", "")),
            confidence_if_supplied=_norm(reviewer.get("confidence")),
            evidence_refs=tuple(str(r) for r in (reviewer.get("evidence_refs") or [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reviewer_id": self.reviewer_id,
            "schema_version": self.schema_version,
            "role": self.role,
            "model_family": self.model_family,
            "provider": self.provider,
            "runtime_lineage": self.runtime_lineage,
            "source_lineages": list(self.source_lineages),
            "retrieval_bundle": self.retrieval_bundle,
            "prompt_context": self.prompt_context,
            "prior_conclusion_exposure": self.prior_conclusion_exposure,
            "implementation_path": self.implementation_path,
            "experiment_design_origin": self.experiment_design_origin,
            "allocator": self.allocator,
            "fresh_context": self.fresh_context,
            "exposure_mode": self.exposure_mode,
            "claim_id": self.claim_id,
            "conclusion": self.conclusion,
            "confidence_if_supplied": self.confidence_if_supplied,
            "evidence_refs": list(self.evidence_refs),
        }

    # ------------------------------------------------------------------ #
    # axis access with UNKNOWN semantics (P0-A)
    # ------------------------------------------------------------------ #
    def axis_value(self, axis: str) -> str:
        if axis == "source_lineage":
            return "|".join(sorted(self.source_lineages)) or UNKNOWN
        if axis == "prior_conclusion_exposure":
            if self.prior_conclusion_exposure is None:
                return UNKNOWN
            return "TRUE" if self.prior_conclusion_exposure else "FALSE"
        return _norm(getattr(self, axis, None))

    def known_axis(self, axis: str) -> bool:
        return self.axis_value(axis) != UNKNOWN and self.axis_value(axis) != ""


# --------------------------------------------------------------------------- #
# §3 pairwise dependency representation (matrix, never a scalar)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PairwiseOverlap:
    reviewer_a: str
    reviewer_b: str
    overlaps: Mapping[str, bool]        # per PAIRWISE_AXES dimension

    def to_dict(self) -> Dict[str, Any]:
        return {"reviewer_a": self.reviewer_a, "reviewer_b": self.reviewer_b,
                "overlaps": dict(self.overlaps)}


def _pairwise_overlap(pa: ReviewerIndependenceProfile, pb: ReviewerIndependenceProfile) -> Mapping[str, bool]:
    shared_sources = bool(set(pa.source_lineages) & set(pb.source_lineages))
    pce = (pa.prior_conclusion_exposure is not None and pa.prior_conclusion_exposure == pb.prior_conclusion_exposure)
    return {
        "model_family": pa.model_family != UNKNOWN and pa.model_family == pb.model_family,
        "provider": pa.provider != UNKNOWN and pa.provider == pb.provider,
        "runtime_lineage": pa.runtime_lineage != UNKNOWN and pa.runtime_lineage == pb.runtime_lineage,
        "source_lineage": shared_sources,
        "retrieval_bundle": pa.retrieval_bundle != UNKNOWN and pa.retrieval_bundle == pb.retrieval_bundle,
        "prompt_context": pa.prompt_context != UNKNOWN and pa.prompt_context == pb.prompt_context,
        "prior_conclusion_exposure": pce and pa.prior_conclusion_exposure is not None,
        "implementation_path": pa.implementation_path != UNKNOWN and pa.implementation_path == pb.implementation_path,
        "experiment_design": pa.experiment_design_origin != UNKNOWN and pa.experiment_design_origin == pb.experiment_design_origin,
        "allocator": pa.allocator != UNKNOWN and pa.allocator == pb.allocator,
    }


@dataclass(frozen=True)
class DependencyGraph:
    """Pairwise overlap graph. Kept as a graph; NO scalar independence score."""

    graph_id: str
    reviewers: Tuple[str, ...]
    pairs: Tuple[PairwiseOverlap, ...]

    @classmethod
    def build(cls, profiles: Sequence[ReviewerIndependenceProfile]) -> "DependencyGraph":
        pairs: List[PairwiseOverlap] = []
        ids = [p.reviewer_id for p in profiles]
        for i, pa in enumerate(profiles):
            for j in range(i + 1, len(profiles)):
                pb = profiles[j]
                pairs.append(PairwiseOverlap(pa.reviewer_id, pb.reviewer_id,
                                             _pairwise_overlap(pa, pb)))
        pairs.sort(key=lambda p: (p.reviewer_a, p.reviewer_b))
        gid = deterministic_hex("depgraph", [p.to_dict() for p in pairs], length=24)
        return cls(graph_id=gid, reviewers=tuple(ids), pairs=tuple(pairs))

    def fingerprint(self) -> str:
        return self.graph_id

    def pair_overlap_counts(self) -> Dict[str, int]:
        """How many reviewer PAIRS overlap on each axis (observable, not a score)."""
        out = {ax: 0 for ax in PAIRWISE_AXES}
        for p in self.pairs:
            for ax, ov in p.overlaps.items():
                if ov:
                    out[ax] += 1
        return out

    def fully_correlated_pairs(self) -> int:
        """Pairs overlapping on EVERY axis (a tight basin signal)."""
        n = 0
        for p in self.pairs:
            if all(p.overlaps.values()):
                n += 1
        return n

    def to_dict(self) -> Dict[str, Any]:
        return {"graph_id": self.graph_id, "reviewers": list(self.reviewers),
                "pairs": [p.to_dict() for p in self.pairs]}


# --------------------------------------------------------------------------- #
# §4 ConsensusRecord — raw consensus is an observation, not multiplied confidence
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ConsensusRecord:
    claim_id: str
    raw_reviewer_count: int
    raw_vote_distribution: Mapping[str, int]          # conclusion -> vote count
    conclusion_set: Tuple[str, ...]
    supporting_evidence_refs: Tuple[str, ...]
    reviewer_profiles: Tuple[ReviewerIndependenceProfile, ...]
    pairwise_dependency_refs: Tuple[str, ...]         # graph ids
    source_lineage_concentration: Optional[float]     # fraction sharing modal source lineage
    model_family_concentration: Optional[float]       # fraction sharing modal model family
    retrieval_bundle_concentration: Optional[float]   # fraction sharing modal retrieval bundle
    prior_conclusion_exposure_count: int
    unknown_independence_dimensions: Tuple[str, ...]  # axes unknown for SOME reviewer
    disagreement_retained: Tuple[str, ...]            # dissenting conclusions preserved
    disposition: str = ""                             # G3 test-only epistemic disposition
    seq: int = 0

    @classmethod
    def build(
        cls,
        claim_id: str,
        profiles: Sequence[ReviewerIndependenceProfile],
        graph: DependencyGraph,
        seq: int = 0,
    ) -> "ConsensusRecord":
        votes: Dict[str, int] = {}
        for p in profiles:
            conclusion = p.conclusion or "(no conclusion)"
            votes[conclusion] = votes.get(conclusion, 0) + 1
        unknown_axes = tuple(
            ax for ax in PROFILE_AXES if any(not p.known_axis(ax) for p in profiles)
        )
        disagreements = tuple(sorted({p.conclusion for p in profiles if p.conclusion}))
        refs = sorted({r for p in profiles for r in p.evidence_refs})
        return cls(
            claim_id=claim_id,
            raw_reviewer_count=len(profiles),
            raw_vote_distribution=dict(votes),
            conclusion_set=disagreements,
            supporting_evidence_refs=tuple(refs),
            reviewer_profiles=tuple(profiles),
            pairwise_dependency_refs=(graph.graph_id,),
            source_lineage_concentration=_modal_concentration(
                [p.axis_value("source_lineage") for p in profiles]),
            model_family_concentration=_modal_concentration(
                [p.axis_value("model_family") for p in profiles]),
            retrieval_bundle_concentration=_modal_concentration(
                [p.axis_value("retrieval_bundle") for p in profiles]),
            prior_conclusion_exposure_count=sum(
                1 for p in profiles if p.prior_conclusion_exposure is True),
            unknown_independence_dimensions=unknown_axes,
            disagreement_retained=disagreements,
            seq=seq,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "raw_reviewer_count": self.raw_reviewer_count,
            "raw_vote_distribution": dict(self.raw_vote_distribution),
            "conclusion_set": list(self.conclusion_set),
            "supporting_evidence_refs": list(self.supporting_evidence_refs),
            "reviewer_profiles": [p.to_dict() for p in self.reviewer_profiles],
            "pairwise_dependency_refs": list(self.pairwise_dependency_refs),
            "source_lineage_concentration": self.source_lineage_concentration,
            "model_family_concentration": self.model_family_concentration,
            "retrieval_bundle_concentration": self.retrieval_bundle_concentration,
            "prior_conclusion_exposure_count": self.prior_conclusion_exposure_count,
            "unknown_independence_dimensions": list(self.unknown_independence_dimensions),
            "disagreement_retained": list(self.disagreement_retained),
            "disposition": self.disposition,
        }


def _modal_concentration(values: Sequence[str]) -> Optional[float]:
    """Fraction of reviewers sharing the modal KNOWN value; UNKNOWN excluded.
    All-unknown returns None (concentration is not independently knowable)."""
    known = [v for v in values if v != UNKNOWN and v]
    if not known:
        return None
    counts: Dict[str, int] = {}
    for v in known:
        counts[v] = counts.get(v, 0) + 1
    return max(counts.values()) / len(known)


# --------------------------------------------------------------------------- #
# §5 sufficiency predicates — TEST-CONTRACT only, never constitutional truth
# --------------------------------------------------------------------------- #
def independent_confirmation_satisfied(
    facts: "EcologyFacts",
    *,
    min_source_lineages: int = 2,
    min_model_or_runtime_lineages: int = 2,
    max_prior_exposure_ratio: float = 0.0,
    min_fresh_or_independent_design: int = 1,
) -> bool:
    """PROVISIONAL test-contract sufficiency. Explicitly NOT universal truth.

    Independent confirmation requires BOTH source and model/runtime diversity —
    source diversity alone never implies model independence (P0-A)."""
    if facts.distinct_source_lineages < min_source_lineages:
        return False
    if facts.distinct_model_family_count < 1 and facts.distinct_runtime_lineage_count < 1:
        return False
    model_or_runtime = max(facts.distinct_model_family_count, facts.distinct_runtime_lineage_count)
    if model_or_runtime < min_model_or_runtime_lineages:
        return False
    if facts.prior_conclusion_exposure_ratio > max_prior_exposure_ratio:
        return False
    if facts.independent_replication_count + facts.fresh_context_count < min_fresh_or_independent_design:
        return False
    return True


# --------------------------------------------------------------------------- #
# EcologyFacts — generic decision-grade properties consumed by the shared policy
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EcologyFacts:
    """Observable, scenario-agnostic ecology properties. No scenario id, no
    reviewer literals, no expected outcomes live here."""

    consequence_class: str = "LOW"                    # HIGH / MEDIUM / LOW
    raw_reviewer_count: int = 0
    distinct_source_lineages: int = 0
    distinct_model_family_count: int = 0
    distinct_runtime_lineage_count: int = 0
    distinct_retrieval_bundle_count: int = 0
    distinct_allocator_count: int = 0
    distinct_experiment_design_count: int = 0
    source_concentration: Optional[float] = None
    model_family_concentration: Optional[float] = None
    retrieval_concentration: Optional[float] = None
    prior_conclusion_exposure_ratio: float = 0.0
    fresh_context_count: int = 0
    independent_replication_count: int = 0
    disagreement_count: int = 0
    discriminating_contradiction_found: bool = False
    challenge_budget_exhausted: bool = False
    counter_attractor_attempted: bool = False
    unknown_dimension_count: int = 0

    @classmethod
    def from_consensus(
        cls,
        consensus: ConsensusRecord,
        consequence_class: str = "LOW",
        independent_replication_count: int = 0,
        discriminating_contradiction_found: bool = False,
        challenge_budget_exhausted: bool = False,
        counter_attractor_attempted: bool = False,
    ) -> "EcologyFacts":
        profiles = consensus.reviewer_profiles
        axes = {
            "source_lineage": set(),
            "model_family": set(),
            "runtime_lineage": set(),
            "retrieval_bundle": set(),
            "allocator": set(),
            "experiment_design_origin": set(),
        }
        unknown_count = 0
        fresh = 0
        for p in profiles:
            for ax in ("model_family", "provider", "runtime_lineage", "retrieval_bundle",
                       "prompt_context", "implementation_path", "experiment_design_origin",
                       "allocator"):
                if not p.known_axis(ax):
                    unknown_count += 1
            axes["source_lineage"].update(p.source_lineages)
            for ax, val in (("model_family", p.model_family), ("runtime_lineage", p.runtime_lineage),
                            ("retrieval_bundle", p.retrieval_bundle), ("allocator", p.allocator),
                            ("experiment_design_origin", p.experiment_design_origin)):
                if val != UNKNOWN and val:
                    axes[ax].add(val)
            if p.fresh_context:
                fresh += 1
        pce_true = sum(1 for p in profiles if p.prior_conclusion_exposure is True)
        return cls(
            consequence_class=consequence_class,
            raw_reviewer_count=len(profiles),
            distinct_source_lineages=len(axes["source_lineage"]),
            distinct_model_family_count=len(axes["model_family"]),
            distinct_runtime_lineage_count=len(axes["runtime_lineage"]),
            distinct_retrieval_bundle_count=len(axes["retrieval_bundle"]),
            distinct_allocator_count=len(axes["allocator"]),
            distinct_experiment_design_count=len(axes["experiment_design_origin"]),
            source_concentration=consensus.source_lineage_concentration,
            model_family_concentration=consensus.model_family_concentration,
            retrieval_concentration=consensus.retrieval_bundle_concentration,
            prior_conclusion_exposure_ratio=(pce_true / len(profiles)) if profiles else 0.0,
            fresh_context_count=fresh,
            independent_replication_count=independent_replication_count,
            disagreement_count=len(consensus.disagreement_retained),
            discriminating_contradiction_found=discriminating_contradiction_found,
            challenge_budget_exhausted=challenge_budget_exhausted,
            counter_attractor_attempted=counter_attractor_attempted,
            unknown_dimension_count=unknown_count,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "consequence_class", "raw_reviewer_count", "distinct_source_lineages",
            "distinct_model_family_count", "distinct_runtime_lineage_count",
            "distinct_retrieval_bundle_count", "distinct_allocator_count",
            "distinct_experiment_design_count", "source_concentration",
            "model_family_concentration", "retrieval_concentration",
            "prior_conclusion_exposure_ratio", "fresh_context_count",
            "independent_replication_count", "disagreement_count",
            "discriminating_contradiction_found", "challenge_budget_exhausted",
            "counter_attractor_attempted", "unknown_dimension_count")}


# --------------------------------------------------------------------------- #
# §17 CognitiveEcologyHealthRecord — observational vector, NO authority, NO scalar
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CognitiveEcologyHealthRecord:
    """Provisional observational surface. Explicitly NOT authority; never
    collapses into a health score."""

    raw_consensus_concentration: Optional[float]
    source_concentration: Optional[float]
    model_family_concentration: Optional[float]
    retrieval_concentration: Optional[float]
    prior_conclusion_exposure_ratio: float
    independent_reconstruction_count: int
    disagreement_preservation: int
    fresh_context_count: int
    counter_attractor_frequency: int
    review_cost_units: int
    information_gain: bool
    correlated_failure_warning: bool

    @classmethod
    def observe(cls, consensus: ConsensusRecord, facts: EcologyFacts,
                counter_attractor_frequency: int = 0, review_cost_units: int = 0,
                information_gain: bool = False,
                correlated_failure_warning: bool = False) -> "CognitiveEcologyHealthRecord":
        return cls(
            raw_consensus_concentration=_modal_concentration(list(consensus.raw_vote_distribution.values())),
            source_concentration=consensus.source_lineage_concentration,
            model_family_concentration=consensus.model_family_concentration,
            retrieval_concentration=consensus.retrieval_bundle_concentration,
            prior_conclusion_exposure_ratio=facts.prior_conclusion_exposure_ratio,
            independent_reconstruction_count=facts.independent_replication_count,
            disagreement_preservation=len(consensus.disagreement_retained),
            fresh_context_count=facts.fresh_context_count,
            counter_attractor_frequency=counter_attractor_frequency,
            review_cost_units=review_cost_units,
            information_gain=information_gain,
            correlated_failure_warning=correlated_failure_warning,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "raw_consensus_concentration", "source_concentration",
            "model_family_concentration", "retrieval_concentration",
            "prior_conclusion_exposure_ratio", "independent_reconstruction_count",
            "disagreement_preservation", "fresh_context_count",
            "counter_attractor_frequency", "review_cost_units",
            "information_gain", "correlated_failure_warning")}


# --------------------------------------------------------------------------- #
# §18 CorrelatedFailureRecord — many failures, one shared upstream dependency
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CorrelatedFailureRecord:
    failure_id: str
    shared_failure_source: str                 # upstream epistemic dependency (fixture truth / observable provenance)
    failure_count: int
    affected_reviewers: Tuple[str, ...]
    dependency_ref: str                        # the one shared lineage/bundle/context
    attribution_basis: str                     # "KNOWN_DEPENDENCY_LINEAGE" — never output matching alone

    @classmethod
    def make(cls, shared_failure_source: str, affected_reviewers: Sequence[str],
             dependency_ref: str, attribution_basis: str = "KNOWN_DEPENDENCY_LINEAGE") -> "CorrelatedFailureRecord":
        return cls(
            failure_id=deterministic_hex("corr_failure", shared_failure_source, sorted(affected_reviewers)),
            shared_failure_source=shared_failure_source,
            failure_count=len(affected_reviewers),
            affected_reviewers=tuple(sorted(affected_reviewers)),
            dependency_ref=dependency_ref,
            attribution_basis=attribution_basis,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "failure_id", "shared_failure_source", "failure_count",
            "affected_reviewers", "dependency_ref", "attribution_basis")}


# --------------------------------------------------------------------------- #
# §31 AllocationProvenance — PO influence observable, never evidentiary
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AllocationProvenance:
    """Who selected reviewers / source bundles / fresh-context status / experiment
    design. Making allocation observable does NOT make it evidence: an allocator
    may influence WHAT evidence is collected, never its strength by declaration.
    CON-02 stays OPEN."""

    claim_id: str
    reviewer_selector: str = UNKNOWN
    source_bundle_selector: str = UNKNOWN
    fresh_context_decider: str = UNKNOWN
    experiment_design_selector: str = UNKNOWN
    per_reviewer: Tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "reviewer_selector": self.reviewer_selector,
            "source_bundle_selector": self.source_bundle_selector,
            "fresh_context_decider": self.fresh_context_decider,
            "experiment_design_selector": self.experiment_design_selector,
            "per_reviewer": [dict(r) for r in self.per_reviewer],
        }


# --------------------------------------------------------------------------- #
# G3-P0 / receipt-lineage semantics (P0-C) — a receipt cannot self-pin its SHA
# --------------------------------------------------------------------------- #
RECEIPT_LINEAGE_SEMANTICS = {
    "artifacts_head_sha": "the LAST CODE commit whose artifacts this package documents (the parent of the evidence commit); known at write time",
    "receipt_content_parent_sha": "the commit whose tree contains this receipt (the evidence commit's parent); known at write time",
    "externally_verified_branch_head": "the branch head AFTER push, verified by git ls-remote; NOT self-contained in the receipt — stated in the final human report",
}


def receipt_lineage(artifacts_head_sha: str, receipt_content_parent_sha: str) -> Dict[str, Any]:
    """Build the non-self-referential receipt SHA block (G3-P0-C)."""
    return {
        "artifacts_head_sha": artifacts_head_sha,
        "receipt_content_parent_sha": receipt_content_parent_sha,
        "externally_verified_branch_head": None,   # filled by the human report after push, never self-pinned
        "self_pin_attempted": False,
        "semantics": RECEIPT_LINEAGE_SEMANTICS,
    }
