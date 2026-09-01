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

from dataclasses import dataclass, field, replace
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
    independently_originated_design: bool = False   # provenance-based, never name-based (G3R-06)
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
            independently_originated_design=bool(reviewer.get("independent_design", False)),
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
            "independently_originated_design": self.independently_originated_design,
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
# G3R-08: per-axis overlap is TRI-STATE — SAME / DIFFERENT / UNKNOWN.
# UNKNOWN vs UNKNOWN must NOT read as "independent" (that would mint favorable
# independence from missing metadata), and must NOT read as "shared dependency"
# either. Only SAME counts as a dependency; only DIFFERENT counts as a
# separation; UNKNOWN preserves uncertainty.
SAME = "SAME"
DIFFERENT = "DIFFERENT"
OVERLAP_STATES = (SAME, DIFFERENT, UNKNOWN)


@dataclass(frozen=True)
class PairwiseOverlap:
    reviewer_a: str
    reviewer_b: str
    overlaps: Mapping[str, str]         # per PAIRWISE_AXES dimension: SAME/DIFFERENT/UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {"reviewer_a": self.reviewer_a, "reviewer_b": self.reviewer_b,
                "overlaps": dict(self.overlaps)}


def _tri(known_a: bool, value_a: Any, known_b: bool, value_b: Any) -> str:
    """Tri-state relation between two axis values."""
    if known_a and known_b:
        return SAME if value_a == value_b else DIFFERENT
    return UNKNOWN


def _source_relation(pa_src: Sequence[str], pb_src: Sequence[str]) -> str:
    """Source-lineage relation: any shared source is SAME lineage; disjoint
    known bundles are DIFFERENT; an empty/unknown bundle is UNKNOWN."""
    pa_s, pb_s = set(pa_src), set(pb_src)
    if not pa_s or not pb_s:
        return UNKNOWN
    return SAME if (pa_s & pb_s) else DIFFERENT


def _pairwise_overlap(pa: ReviewerIndependenceProfile, pb: ReviewerIndependenceProfile) -> Mapping[str, str]:
    pa_pce = pa.prior_conclusion_exposure is not None
    pb_pce = pb.prior_conclusion_exposure is not None
    return {
        "model_family": _tri(pa.known_axis("model_family"), pa.model_family,
                              pb.known_axis("model_family"), pb.model_family),
        "provider": _tri(pa.known_axis("provider"), pa.provider,
                          pb.known_axis("provider"), pb.provider),
        "runtime_lineage": _tri(pa.known_axis("runtime_lineage"), pa.runtime_lineage,
                                 pb.known_axis("runtime_lineage"), pb.runtime_lineage),
        "source_lineage": _source_relation(pa.source_lineages, pb.source_lineages),
        "retrieval_bundle": _tri(pa.known_axis("retrieval_bundle"), pa.retrieval_bundle,
                                  pb.known_axis("retrieval_bundle"), pb.retrieval_bundle),
        "prompt_context": _tri(pa.known_axis("prompt_context"), pa.prompt_context,
                                pb.known_axis("prompt_context"), pb.prompt_context),
        "prior_conclusion_exposure": _tri(pa_pce, pa.prior_conclusion_exposure,
                                           pb_pce, pb.prior_conclusion_exposure),
        "implementation_path": _tri(pa.known_axis("implementation_path"), pa.implementation_path,
                                     pb.known_axis("implementation_path"), pb.implementation_path),
        "experiment_design": _tri(pa.known_axis("experiment_design_origin"), pa.experiment_design_origin,
                                   pb.known_axis("experiment_design_origin"), pb.experiment_design_origin),
        "allocator": _tri(pa.known_axis("allocator"), pa.allocator,
                           pb.known_axis("allocator"), pb.allocator),
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
        """How many reviewer PAIRS are SAME on each axis (observable, not a
        score). UNKNOWN never counts as either a dependency or a separation."""
        out = {ax: 0 for ax in PAIRWISE_AXES}
        for p in self.pairs:
            for ax, ov in p.overlaps.items():
                if ov == SAME:
                    out[ax] += 1
        return out

    def fully_correlated_pairs(self) -> int:
        """Pairs SAME on EVERY axis with no UNKNOWN dimension (a tight basin
        signal). Pairs with any UNKNOWN are not claimed as fully correlated."""
        n = 0
        for p in self.pairs:
            if all(ov == SAME for ov in p.overlaps.values()):
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
    require_known_exposure_coverage: Optional[bool] = None,
    min_source_known_coverage: Optional[float] = None,
) -> bool:
    """PROVISIONAL test-contract sufficiency. Explicitly NOT universal truth.

    Independent confirmation requires BOTH source and model/runtime diversity —
    source diversity alone never implies model independence (P0-A).

    G3R2-05: UNKNOWN prior-conclusion exposure is neither TRUE nor FALSE. For
    HIGH/MEDIUM consequence the contract requires KNOWN exposure coverage
    (`require_known_exposure_coverage` defaults to that): a reviewer whose
    exposure is UNKNOWN can never satisfy an "unexposed" requirement.

    G3R2-09: the fresh/design/replication requirement counts UNIQUE qualifying
    epistemic paths (one path with several properties is one path)."""
    if facts.distinct_source_lineages < min_source_lineages:
        return False
    model_or_runtime = max(facts.distinct_model_family_count, facts.distinct_runtime_lineage_count)
    if model_or_runtime < min_model_or_runtime_lineages:
        return False
    if require_known_exposure_coverage is None:
        require_known_exposure_coverage = facts.consequence_class in ("HIGH", "MEDIUM")
    if require_known_exposure_coverage and facts.prior_exposure_known_ratio < 1.0:
        return False                       # UNKNOWN exposure cannot satisfy "unexposed"
    if facts.prior_exposure_true_ratio_among_known > max_prior_exposure_ratio:
        return False
    if min_source_known_coverage is not None and \
            facts.known_coverage_by_axis.get("source_lineage", 0.0) < min_source_known_coverage:
        return False                       # G3R2-06: unknown-heavy sets cannot look diverse
    if facts.unique_epistemic_path_count < min_fresh_or_independent_design:
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
    dominant_vote_count: int = 0          # G3R-03: consensus-strength topology facts
    dominant_vote_ratio: float = 0.0      # G3R-03: NOT evidence strength — vote topology only
    distinct_conclusion_count: int = 0    # G3R-03
    distinct_source_lineages: int = 0
    distinct_model_family_count: int = 0
    distinct_runtime_lineage_count: int = 0
    distinct_retrieval_bundle_count: int = 0
    distinct_allocator_count: int = 0
    distinct_experiment_design_count: int = 0
    independently_originated_design_count: int = 0   # G3R-06: provenance-based
    source_concentration: Optional[float] = None
    max_single_source_lineage_prevalence: Optional[float] = None   # G3R2-04
    model_family_concentration: Optional[float] = None
    retrieval_concentration: Optional[float] = None
    prior_conclusion_exposure_ratio: float = 0.0
    prior_exposure_true_count: int = 0              # G3R2-05
    prior_exposure_false_count: int = 0             # G3R2-05
    prior_exposure_unknown_count: int = 0           # G3R2-05
    prior_exposure_known_ratio: float = 0.0         # G3R2-05 known / all
    prior_exposure_true_ratio_among_known: float = 0.0  # G3R2-05
    fresh_context_count: int = 0
    independent_replication_count: int = 0
    unique_epistemic_path_count: int = 0            # G3R2-09: distinct qualifying paths
    known_coverage_by_axis: Dict[str, float] = field(default_factory=dict)   # G3R2-06
    unknown_count_by_axis: Dict[str, int] = field(default_factory=dict)      # G3R2-06
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
        replication_paths: Optional[Sequence[ReplicationPathRecord]] = None,
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
        pce_false = sum(1 for p in profiles if p.prior_conclusion_exposure is False)
        pce_unknown = len(profiles) - pce_true - pce_false
        votes = consensus.raw_vote_distribution or {}
        dominant_count = max(votes.values()) if votes else 0
        # G3R2-04: max single-source prevalence — the most common single source
        # across reviewers with KNOWN source provenance (partial-bundle overlap
        # is a shared dependency even when whole bundles differ).
        known_sources = [p for p in profiles if p.source_lineages]
        prevalence: Optional[float] = None
        if known_sources:
            source_counts: Dict[str, int] = {}
            for p in known_sources:
                for s in set(p.source_lineages):
                    source_counts[s] = source_counts.get(s, 0) + 1
            prevalence = max(source_counts.values()) / len(known_sources)
        # G3R2-06: per-axis known coverage / unknown counts survive into facts
        cov_axes: Dict[str, float] = {}
        unc_axes: Dict[str, int] = {}
        for ax in ("model_family", "provider", "runtime_lineage", "retrieval_bundle",
                   "prompt_context", "implementation_path", "experiment_design_origin",
                   "allocator", "source_lineage"):
            known = sum(1 for p in profiles if p.known_axis(ax))
            cov_axes[ax] = (known / len(profiles)) if profiles else 0.0
            unc_axes[ax] = len(profiles) - known
        paths = collect_epistemic_paths(profiles, replication_paths,
                                        independent_replication_count)
        return cls(
            consequence_class=consequence_class,
            raw_reviewer_count=len(profiles),
            dominant_vote_count=dominant_count,
            dominant_vote_ratio=(dominant_count / len(profiles)) if profiles else 0.0,
            distinct_conclusion_count=len(votes),
            distinct_source_lineages=len(axes["source_lineage"]),
            distinct_model_family_count=len(axes["model_family"]),
            distinct_runtime_lineage_count=len(axes["runtime_lineage"]),
            distinct_retrieval_bundle_count=len(axes["retrieval_bundle"]),
            distinct_allocator_count=len(axes["allocator"]),
            distinct_experiment_design_count=len(axes["experiment_design_origin"]),
            independently_originated_design_count=sum(1 for p in profiles if p.independently_originated_design),
            source_concentration=consensus.source_lineage_concentration,
            max_single_source_lineage_prevalence=prevalence,
            model_family_concentration=consensus.model_family_concentration,
            retrieval_concentration=consensus.retrieval_bundle_concentration,
            prior_conclusion_exposure_ratio=(pce_true / len(profiles)) if profiles else 0.0,
            prior_exposure_true_count=pce_true,
            prior_exposure_false_count=pce_false,
            prior_exposure_unknown_count=pce_unknown,
            prior_exposure_known_ratio=((pce_true + pce_false) / len(profiles)) if profiles else 0.0,
            prior_exposure_true_ratio_among_known=(
                (pce_true / (pce_true + pce_false)) if (pce_true + pce_false) else 0.0),
            fresh_context_count=fresh,
            independent_replication_count=independent_replication_count,
            unique_epistemic_path_count=len(paths),
            known_coverage_by_axis=cov_axes,
            unknown_count_by_axis=unc_axes,
            disagreement_count=len(consensus.disagreement_retained),
            discriminating_contradiction_found=discriminating_contradiction_found,
            challenge_budget_exhausted=challenge_budget_exhausted,
            counter_attractor_attempted=counter_attractor_attempted,
            unknown_dimension_count=unknown_count,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in (
            "consequence_class", "raw_reviewer_count", "dominant_vote_count",
            "dominant_vote_ratio", "distinct_conclusion_count",
            "distinct_source_lineages", "distinct_model_family_count",
            "distinct_runtime_lineage_count", "distinct_retrieval_bundle_count",
            "distinct_allocator_count", "distinct_experiment_design_count",
            "independently_originated_design_count", "source_concentration",
            "max_single_source_lineage_prevalence",
            "model_family_concentration", "retrieval_concentration",
            "prior_conclusion_exposure_ratio",
            "prior_exposure_true_count", "prior_exposure_false_count",
            "prior_exposure_unknown_count", "prior_exposure_known_ratio",
            "prior_exposure_true_ratio_among_known",
            "fresh_context_count", "independent_replication_count",
            "unique_epistemic_path_count", "known_coverage_by_axis",
            "unknown_count_by_axis", "disagreement_count",
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
# G3R2-02 / §13 — explicit provenance authority semantics.
#
# A reviewer's CLAIMED provenance is never its own authority. Two explicit modes:
#
#   GOVERNED_REGISTRY             — decision-grade axes come ONLY from the governed
#                                   registered_provenance table; a missing entry
#                                   fails closed (all independence axes UNKNOWN).
#   AUTHORITATIVE_SYNTHETIC_FIXTURE — the harness itself owns the synthetic ground
#                                   truth for a deterministic test pack; fixture
#                                   fields ARE authoritative observable data.
#                                   Explicit in the scenario contract, never
#                                   inferred. This does NOT make agent claims
#                                   trusted — it makes the harness the authority.
#
# The default (GOVERNED_REGISTRY) fails closed: no registry file => no verified
# provenance => claims are never promoted.
# --------------------------------------------------------------------------- #
PROVENANCE_MODES = ("GOVERNED_REGISTRY", "AUTHORITATIVE_SYNTHETIC_FIXTURE")
DEFAULT_PROVENANCE_MODE = "GOVERNED_REGISTRY"

# Capability provenance (G3R2-10): capability_tiers are evidence only when the
# provenance of the capability fact is explicit. UNVERIFIED never satisfies a
# positive minimum-capability requirement.
CAPABILITY_SOURCES = (
    "AUTHORITATIVE_SYNTHETIC_CAPABILITY",
    "REGISTERED_CAPABILITY",
    "UNVERIFIED_CAPABILITY",
)


@dataclass(frozen=True)
class SyntheticFixtureAuthority:
    """Explicit mode marker (G3R2-02/§13): "for this deterministic test pack,
    these provenance/capability facts are supplied by the harness as
    authoritative observable fixture data." It is NOT a trust grant for agent
    self-claims; receipts must record when synthetic authority was used."""

    mode: str = "AUTHORITATIVE_SYNTHETIC_FIXTURE"
    scope: str = "provenance_and_capability_facts_for_this_pack"
    agent_claims_trusted: bool = False
    wall_clock_free: bool = True
    model_calls: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"mode": self.mode, "scope": self.scope,
                "agent_claims_trusted": self.agent_claims_trusted,
                "wall_clock_free": self.wall_clock_free, "model_calls": self.model_calls}


# --------------------------------------------------------------------------- #
# G3R2-09 — unique epistemic paths, not summed labels
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EpistemicPathRecord:
    """One distinct qualifying epistemic path. A single path may carry several
    attributes (fresh_context AND independent_design AND replication) but is
    still ONE path — a path with two properties must never be counted twice.
    Identity is `path_id`; duplicated ids count once. A path whose provenance is
    entirely UNKNOWN does not qualify as an independent epistemic path."""

    path_id: str
    fresh_context: bool = False
    independent_design: bool = False
    independent_replication: bool = False
    reviewer_id: str = UNKNOWN
    runtime_lineage: str = UNKNOWN
    evidence_refs: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {"path_id": self.path_id, "fresh_context": self.fresh_context,
                "independent_design": self.independent_design,
                "independent_replication": self.independent_replication,
                "reviewer_id": self.reviewer_id, "runtime_lineage": self.runtime_lineage,
                "evidence_refs": list(self.evidence_refs)}


_PATH_KNOWN_AXES = ("model_family", "runtime_lineage", "source_lineage",
                    "retrieval_bundle", "experiment_design_origin")


# --------------------------------------------------------------------------- #
# G4-P0-A — replication must have identity / provenance
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ReplicationPathRecord:
    """An explicit, attributable replication path (G4-P0-A). A replication
    counts as an independent epistemic path only when it has a distinct,
    verified/synthetic-authoritative path identity. A raw integer count is a
    derived DISPLAY field — it must never mint path identities by declaration.

    `qualifies()` fails closed: an empty/unknown identity, an unknown
    provenance mode, or entirely-UNKNOWN provenance never qualifies.
    """

    replication_id: str
    claim_id: str = ""
    method: str = UNKNOWN
    runtime_or_deterministic_path: str = UNKNOWN
    source_lineages: Tuple[str, ...] = ()
    experiment_design_origin: str = UNKNOWN
    evidence_refs: Tuple[str, ...] = ()
    provenance_mode: str = DEFAULT_PROVENANCE_MODE
    registered_or_synthetic_authority: str = ""
    prior_conclusion_exposure: Optional[bool] = None
    result: str = ""

    @classmethod
    def from_fixture(cls, data: Mapping[str, Any]) -> "ReplicationPathRecord":
        pce = data.get("prior_conclusion_exposure")
        if isinstance(pce, str):
            pce = {"TRUE": True, "FALSE": False, "UNKNOWN": None}.get(pce.upper())
        return cls(
            replication_id=_norm(data.get("replication_id")),
            claim_id=str(data.get("claim_id", "")),
            method=_norm(data.get("method")),
            runtime_or_deterministic_path=_norm(data.get("runtime_or_deterministic_path")),
            source_lineages=tuple(str(s) for s in (data.get("source_lineages") or [])),
            experiment_design_origin=_norm(data.get("experiment_design_origin")),
            evidence_refs=tuple(str(r) for r in (data.get("evidence_refs") or [])),
            provenance_mode=str(data.get("provenance_mode", DEFAULT_PROVENANCE_MODE)),
            registered_or_synthetic_authority=str(data.get("registered_or_synthetic_authority", "")),
            prior_conclusion_exposure=pce,
            result=str(data.get("result", "")),
        )

    def qualifies(self) -> bool:
        """A replication path qualifies only with a distinct identity AND known
        provenance under an explicit provenance mode."""
        if not self.replication_id or self.replication_id == UNKNOWN:
            return False
        if self.provenance_mode not in PROVENANCE_MODES:
            return False
        if not self.registered_or_synthetic_authority:
            return False
        return bool(
            (self.method not in (UNKNOWN, ""))
            or (self.runtime_or_deterministic_path not in (UNKNOWN, ""))
            or bool(self.source_lineages)
            or (self.experiment_design_origin not in (UNKNOWN, "")))

    def to_dict(self) -> Dict[str, Any]:
        return {"replication_id": self.replication_id, "claim_id": self.claim_id,
                "method": self.method,
                "runtime_or_deterministic_path": self.runtime_or_deterministic_path,
                "source_lineages": list(self.source_lineages),
                "experiment_design_origin": self.experiment_design_origin,
                "evidence_refs": list(self.evidence_refs),
                "provenance_mode": self.provenance_mode,
                "registered_or_synthetic_authority": self.registered_or_synthetic_authority,
                "prior_conclusion_exposure": self.prior_conclusion_exposure,
                "result": self.result}


# `replication_paths=None` means: use the LEGACY synthetic-fixture display
# semantics (a harness-declared count synthesizes REPL:N identities). A SUPPLIED
# sequence — even an empty one — is the explicit institutional contract: only
# those path identities count, deduplicated, provenance-checked.
def collect_epistemic_paths(
    profiles: Sequence[ReviewerIndependenceProfile],
    replication_paths: Optional[Sequence[ReplicationPathRecord]] = None,
    independent_replication_count: int = 0,
) -> Tuple[EpistemicPathRecord, ...]:
    """Unique qualifying epistemic paths (G3R2-09 / G4-P0-A).

    * A reviewer path qualifies when it is fresh-context and/or
      independently-originated-design AND its provenance is not entirely
      UNKNOWN (unknown path provenance does not qualify).
    * Reviewer paths are keyed by reviewer identity; a duplicated reviewer id
      counts once.
    * Replication paths come from EXPLICIT ReplicationPathRecord identities
      (deduplicated by replication_id; only qualifying records count). A raw
      integer count is display-only when explicit identities are supplied.
      When NO explicit identities are supplied (legacy synthetic fixtures), a
      harness-declared count may synthesize REPL:N identities.
    """
    paths: Dict[str, EpistemicPathRecord] = {}
    for p in profiles:
        if not (p.fresh_context or p.independently_originated_design):
            continue
        if not any(p.known_axis(ax) for ax in _PATH_KNOWN_AXES):
            continue                       # unknown path provenance does not qualify
        paths[p.reviewer_id] = EpistemicPathRecord(
            path_id=f"REVIEWER:{p.reviewer_id}",
            fresh_context=p.fresh_context,
            independent_design=p.independently_originated_design,
            reviewer_id=p.reviewer_id,
            runtime_lineage=p.runtime_lineage,
            evidence_refs=p.evidence_refs,
        )
    if replication_paths is None:
        # LEGACY synthetic-fixture display semantics (historical G3 receipts).
        for i in range(max(0, int(independent_replication_count))):
            paths[f"REPL:{i}"] = EpistemicPathRecord(
                path_id=f"REPL:{i}", independent_replication=True,
                evidence_refs=(f"REPLICATION:{i}",))
    else:
        for rp in replication_paths:
            if not rp.qualifies():
                continue                   # unknown replication provenance: no path
            if rp.replication_id in paths:
                continue                   # duplicated identity counts once
            paths[rp.replication_id] = EpistemicPathRecord(
                path_id=rp.replication_id, independent_replication=True,
                reviewer_id=rp.replication_id,
                runtime_lineage=rp.runtime_or_deterministic_path,
                evidence_refs=rp.evidence_refs,
            )
    return tuple(sorted(paths.values(), key=lambda r: r.path_id))


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


# --------------------------------------------------------------------------- #
# G3R-07 — governed reviewer provenance registry (CLAIMED vs VERIFIED)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class RegisteredReviewerProvenance:
    """VERIFIED/REGISTERED provenance for one reviewer, bound from governed
    evidence/identity records. UNKNOWN means the system has no verified value:
    a self-claim is NEVER promoted to verified independence (fail-closed)."""

    reviewer_id: str
    model_family: str = UNKNOWN
    provider: str = UNKNOWN
    runtime_lineage: str = UNKNOWN
    source_lineages: Tuple[str, ...] = ()
    retrieval_bundle: str = UNKNOWN
    prompt_context: str = UNKNOWN
    experiment_design_origin: str = UNKNOWN
    allocator: str = UNKNOWN
    prior_conclusion_exposure: Optional[bool] = None
    fresh_context: bool = False
    exposure_mode: str = UNKNOWN
    independently_originated_design: bool = False
    capability_tier: str = UNKNOWN      # G3R2-10: registered capability fact (if known)

    @classmethod
    def from_fixture(cls, entry: Mapping[str, Any]) -> "RegisteredReviewerProvenance":
        pce = entry.get("prior_conclusion_exposure")
        if isinstance(pce, str):
            pce = {"TRUE": True, "FALSE": False, "UNKNOWN": None}.get(pce.upper())
        return cls(
            reviewer_id=str(entry.get("reviewer_id", "")),
            model_family=_norm(entry.get("model_family")),
            provider=_norm(entry.get("provider")),
            runtime_lineage=_norm(entry.get("runtime_lineage")),
            source_lineages=tuple(str(s) for s in (entry.get("sources") or [])),
            retrieval_bundle=_norm(entry.get("retrieval_bundle")),
            prompt_context=_norm(entry.get("prompt_context")),
            experiment_design_origin=_norm(entry.get("experiment_design_origin")),
            allocator=_norm(entry.get("allocator")),
            prior_conclusion_exposure=pce,
            fresh_context=bool(entry.get("fresh_context", False)),
            exposure_mode=_norm(entry.get("visible_information", UNKNOWN)),
            independently_originated_design=bool(entry.get("independent_design", False)),
            capability_tier=_norm(entry.get("capability_tier", UNKNOWN)),
        )

    def axis_value(self, axis: str) -> str:
        if axis == "source_lineage":
            return "|".join(sorted(self.source_lineages)) or UNKNOWN
        if axis == "prior_conclusion_exposure":
            if self.prior_conclusion_exposure is None:
                return UNKNOWN
            return "TRUE" if self.prior_conclusion_exposure else "FALSE"
        return _norm(getattr(self, axis, None))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reviewer_id": self.reviewer_id,
            "model_family": self.model_family,
            "provider": self.provider,
            "runtime_lineage": self.runtime_lineage,
            "source_lineages": list(self.source_lineages),
            "retrieval_bundle": self.retrieval_bundle,
            "prompt_context": self.prompt_context,
            "experiment_design_origin": self.experiment_design_origin,
            "allocator": self.allocator,
            "prior_conclusion_exposure": self.prior_conclusion_exposure,
            "fresh_context": self.fresh_context,
            "exposure_mode": self.exposure_mode,
            "independently_originated_design": self.independently_originated_design,
            "capability_tier": self.capability_tier,
        }


# axes bound by the registry (CLAIMED value replaced when registered is known)
REGISTRY_AXES = (
    "model_family", "provider", "runtime_lineage", "source_lineage",
    "retrieval_bundle", "prompt_context", "experiment_design_origin",
    "allocator", "prior_conclusion_exposure", "fresh_context", "exposure_mode",
    "independently_originated_design",
)


@dataclass(frozen=True)
class ProvenanceConflict:
    """A recorded mismatch between a reviewer's CLAIMED provenance and the
    VERIFIED registry value (or an unverified claim against an UNKNOWN registry
    axis). Registered truth wins; the conflict is preserved, never erased."""

    reviewer_id: str
    axis: str
    claimed: Any
    registered: Any
    disposition: str = "REGISTERED_WINS"     # or "UNVERIFIED_CLAIM" when registered is UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {"reviewer_id": self.reviewer_id, "axis": self.axis,
                "claimed": self.claimed, "registered": self.registered,
                "disposition": self.disposition}


class ReviewerProvenanceRegistry:
    """Governed identity/provenance source. `bind()` returns the bound profile
    (registered truth) plus every conflict against the claim."""

    def __init__(self, entries: Sequence[RegisteredReviewerProvenance] = ()):
        self._by_id: Dict[str, RegisteredReviewerProvenance] = {}
        for e in entries:
            if not e.reviewer_id:
                continue
            if e.reviewer_id in self._by_id:
                raise ValueError(f"duplicate registered provenance for reviewer {e.reviewer_id!r}")
            self._by_id[e.reviewer_id] = e

    @classmethod
    def from_fixtures(cls, entries: Sequence[Mapping[str, Any]]) -> "ReviewerProvenanceRegistry":
        return cls([RegisteredReviewerProvenance.from_fixture(e) for e in entries])

    def registered(self, reviewer_id: str) -> Optional[RegisteredReviewerProvenance]:
        return self._by_id.get(reviewer_id)

    def bind(self, claimed: ReviewerIndependenceProfile) -> Tuple[ReviewerIndependenceProfile, Tuple[ProvenanceConflict, ...]]:
        """Bind a CLAIMED profile to registry truth. Registered UNKNOWN does NOT
        promote the claim (G3R-07 fail-closed); conflicts are returned.

        G3R2-01: when NO registry record exists at all, every decision-grade
        independence axis of the bound profile becomes UNKNOWN / non-qualifying
        (fail-closed). Identity, conclusion and evidence refs remain as claims
        but acquire NO verified independence semantics."""
        reg = self._by_id.get(claimed.reviewer_id)
        if reg is None:
            # no registry record: nothing is verified — force every
            # independence-bearing axis to UNKNOWN / non-qualifying
            claimed_conflicts: List[ProvenanceConflict] = []
            for ax in ("model_family", "provider", "runtime_lineage", "source_lineage",
                       "retrieval_bundle", "prompt_context", "experiment_design_origin",
                       "allocator", "prior_conclusion_exposure"):
                if claimed.known_axis(ax):
                    claimed_conflicts.append(ProvenanceConflict(
                        claimed.reviewer_id, ax, claimed.axis_value(ax), UNKNOWN,
                        "UNVERIFIED_CLAIM"))
            if claimed.fresh_context:
                claimed_conflicts.append(ProvenanceConflict(
                    claimed.reviewer_id, "fresh_context", True, False, "UNVERIFIED_CLAIM"))
            if claimed.exposure_mode not in (UNKNOWN, "FULL_SHARED_CONTEXT"):
                claimed_conflicts.append(ProvenanceConflict(
                    claimed.reviewer_id, "exposure_mode", claimed.exposure_mode, UNKNOWN,
                    "UNVERIFIED_CLAIM"))
            if claimed.independently_originated_design:
                claimed_conflicts.append(ProvenanceConflict(
                    claimed.reviewer_id, "independently_originated_design", True, False,
                    "UNVERIFIED_CLAIM"))
            conflicts = tuple(claimed_conflicts)
            bound = replace(
                claimed,
                model_family=UNKNOWN,
                provider=UNKNOWN,
                runtime_lineage=UNKNOWN,
                source_lineages=(),
                retrieval_bundle=UNKNOWN,
                prompt_context=UNKNOWN,
                experiment_design_origin=UNKNOWN,
                allocator=UNKNOWN,
                prior_conclusion_exposure=None,
                fresh_context=False,
                exposure_mode=UNKNOWN,
                independently_originated_design=False,
            )
            return bound, conflicts
        conflicts: List[ProvenanceConflict] = []
        kw: Dict[str, Any] = {}

        def bind_axis(axis: str, reg_value: Any, claim_value: Any,
                      *, unknown_is_unverified: bool = False) -> Any:
            nonlocal conflicts
            rv = reg_value if reg_value != UNKNOWN else None
            if reg_value == UNKNOWN:
                if claim_value is not None and claim_value != UNKNOWN and unknown_is_unverified:
                    conflicts.append(ProvenanceConflict(claimed.reviewer_id, axis,
                                                        claim_value, UNKNOWN, "UNVERIFIED_CLAIM"))
                return UNKNOWN
            if claim_value != rv:
                conflicts.append(ProvenanceConflict(claimed.reviewer_id, axis,
                                                    claim_value, rv, "REGISTERED_WINS"))
            return rv

        kw["model_family"] = bind_axis("model_family", reg.model_family, claimed.model_family, unknown_is_unverified=True)
        kw["provider"] = bind_axis("provider", reg.provider, claimed.provider, unknown_is_unverified=True)
        kw["runtime_lineage"] = bind_axis("runtime_lineage", reg.runtime_lineage, claimed.runtime_lineage, unknown_is_unverified=True)
        kw["retrieval_bundle"] = bind_axis("retrieval_bundle", reg.retrieval_bundle, claimed.retrieval_bundle, unknown_is_unverified=True)
        kw["prompt_context"] = bind_axis("prompt_context", reg.prompt_context, claimed.prompt_context, unknown_is_unverified=True)
        kw["experiment_design_origin"] = bind_axis("experiment_design_origin", reg.experiment_design_origin, claimed.experiment_design_origin, unknown_is_unverified=True)
        kw["allocator"] = bind_axis("allocator", reg.allocator, claimed.allocator, unknown_is_unverified=True)
        # source lineage: registry list wins wholesale when non-empty
        if reg.source_lineages:
            if tuple(claimed.source_lineages) != reg.source_lineages:
                conflicts.append(ProvenanceConflict(claimed.reviewer_id, "source_lineage",
                                                    list(claimed.source_lineages), list(reg.source_lineages)))
            kw["source_lineages"] = reg.source_lineages
        else:
            if claimed.source_lineages:
                conflicts.append(ProvenanceConflict(claimed.reviewer_id, "source_lineage",
                                                    list(claimed.source_lineages), [], "UNVERIFIED_CLAIM"))
            kw["source_lineages"] = ()
        # prior-conclusion exposure: system-observable; registered (non-None) wins
        if reg.prior_conclusion_exposure is not None:
            if claimed.prior_conclusion_exposure != reg.prior_conclusion_exposure:
                conflicts.append(ProvenanceConflict(claimed.reviewer_id, "prior_conclusion_exposure",
                                                    claimed.prior_conclusion_exposure,
                                                    reg.prior_conclusion_exposure))
            kw["prior_conclusion_exposure"] = reg.prior_conclusion_exposure
        elif claimed.prior_conclusion_exposure is not None:
            conflicts.append(ProvenanceConflict(claimed.reviewer_id, "prior_conclusion_exposure",
                                                claimed.prior_conclusion_exposure, None, "UNVERIFIED_CLAIM"))
            kw["prior_conclusion_exposure"] = None
        else:
            kw["prior_conclusion_exposure"] = None
        # fresh context / exposure mode / independent design: system-observable
        if reg.fresh_context != claimed.fresh_context:
            conflicts.append(ProvenanceConflict(claimed.reviewer_id, "fresh_context",
                                                claimed.fresh_context, reg.fresh_context))
        kw["fresh_context"] = reg.fresh_context
        if reg.exposure_mode != UNKNOWN and reg.exposure_mode != claimed.exposure_mode:
            conflicts.append(ProvenanceConflict(claimed.reviewer_id, "exposure_mode",
                                                claimed.exposure_mode, reg.exposure_mode))
        kw["exposure_mode"] = reg.exposure_mode if reg.exposure_mode != UNKNOWN else claimed.exposure_mode
        if reg.independently_originated_design != claimed.independently_originated_design:
            conflicts.append(ProvenanceConflict(claimed.reviewer_id, "independently_originated_design",
                                                claimed.independently_originated_design,
                                                reg.independently_originated_design))
        kw["independently_originated_design"] = reg.independently_originated_design

        bound = replace(claimed, **kw)
        return bound, tuple(conflicts)

    def bind_all(
        self,
        claimed: Sequence[ReviewerIndependenceProfile],
    ) -> Tuple[Tuple[ReviewerIndependenceProfile, ...], Tuple[ProvenanceConflict, ...]]:
        out: List[ReviewerIndependenceProfile] = []
        conflicts: List[ProvenanceConflict] = []
        for p in claimed:
            b, cs = self.bind(p)
            out.append(b)
            conflicts.extend(cs)
        return tuple(out), tuple(conflicts)


# --------------------------------------------------------------------------- #
# G4-P0-B — ProvenanceConflictLedger: secondary-surface conflicts must survive
# --------------------------------------------------------------------------- #
SURFACE_TAGS = ("PRIMARY_REVIEW", "TOPOLOGY_CANDIDATE", "FRICTION_REVIEW",
                "REPLICATION_PATH")


@dataclass(frozen=True)
class LedgerConflict:
    surface: str
    reviewer_id: str
    axis: str
    claimed: Any
    registered: Any
    disposition: str

    @classmethod
    def from_conflict(cls, surface: str, c: ProvenanceConflict) -> "LedgerConflict":
        return cls(surface=surface, reviewer_id=c.reviewer_id, axis=c.axis,
                   claimed=c.claimed, registered=c.registered,
                   disposition=c.disposition)

    def to_dict(self) -> Dict[str, Any]:
        return {"surface": self.surface, "reviewer_id": self.reviewer_id,
                "axis": self.axis, "claimed": self.claimed,
                "registered": self.registered, "disposition": self.disposition}


class ProvenanceConflictLedger:
    """Run-level audit lineage of every provenance conflict across ALL cognitive
    surfaces (primary review, topology candidates, friction reviewers,
    replication paths). G4-P0-B: behavior already fails closed; this guarantees
    the conflicts are reconstructable in receipts."""

    def __init__(self) -> None:
        self._entries: List[LedgerConflict] = []

    def record(self, surface: str, conflicts: Sequence[ProvenanceConflict]) -> None:
        if surface not in SURFACE_TAGS:
            raise ValueError(f"unknown provenance surface tag {surface!r}")
        for c in conflicts:
            self._entries.append(LedgerConflict.from_conflict(surface, c))

    def entries(self) -> Tuple[LedgerConflict, ...]:
        return tuple(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def to_dict(self) -> Dict[str, Any]:
        return {"entries": [e.to_dict() for e in self._entries],
                "count": len(self._entries)}
