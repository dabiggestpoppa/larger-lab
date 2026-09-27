"""Independence model (A-010 §11; G1 §6). REPRESENT FIRST, SCORE LATER.

* No magic `independence_score` scalar is treated as authoritative (AMB-03 stays
  open). We record the raw overlap vector and separate *raw reviewer count* from
  *distinct lineages*.
* Allocation origin is observable (producing vs assigning actor, task, source and
  retrieval lineage, prior-conclusion exposure, experiment-design origin) so that
  G0 Q3 (PO biasing the Governor via work allocation) can be tested later.
* A derived summary, if ever needed, is explicitly EXPERIMENTAL / NON-AUTHORITATIVE
  and NEVER replaces the raw vector.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set

from .base import deterministic_hex

INDEPENDENCE_DIMENSIONS = (
    "model_family_overlap",
    "provider_overlap",
    "source_overlap",
    "retrieval_overlap",
    "prompt_context_overlap",
    "prior_conclusion_exposure",
    "implementation_path_overlap",
    "experiment_design_overlap",
    "runtime_lineage_overlap_if_known",
    "allocator_overlap",
)

# Every dimension takes one of these qualitative grades so G1 never pretends a
# precise effective sample size is known.
QUALITATIVE_GRADES = ("NONE", "LOW", "MEDIUM", "HIGH", "UNKNOWN")


@dataclass
class IndependenceRecord:
    record_id: str
    schema_version: str = "1.0.0"

    raw_reviewers: int = 0
    distinct_source_lineages: int = 0
    distinct_model_families: int = 0
    distinct_retrieval_bundles: int = 0

    # qualitative overlap vector (10 dimensions above)
    overlaps: Dict[str, str] = field(default_factory=dict)

    # per-reviewer evidence of provenance/allocation origin
    reviewers: List[dict] = field(default_factory=list)

    seq: int = 0

    @classmethod
    def make(cls, seq, raw_reviewers=0, overlaps=None, reviewers=None, **counts):
        clamped = {d: (overlaps or {}).get(d, "UNKNOWN") for d in INDEPENDENCE_DIMENSIONS}
        bad = {d: g for d, g in clamped.items() if g not in QUALITATIVE_GRADES}
        if bad:
            raise ValueError(f"invalid independence grade: {bad}")
        rec = cls(
            record_id=deterministic_hex("independence", seq, *counts.values()),
            raw_reviewers=raw_reviewers,
            distinct_source_lineages=counts.get("distinct_source_lineages", 0),
            distinct_model_families=counts.get("distinct_model_families", 0),
            distinct_retrieval_bundles=counts.get("distinct_retrieval_bundles", 0),
            overlaps=clamped,
            reviewers=list(reviewers or []),
            seq=seq,
        )
        return rec

    # ------------------------------------------------------------------ #
    # Readable view — deliberately does NOT invent effective sample size.
    # ------------------------------------------------------------------ #
    @property
    def summary(self) -> Dict[str, object]:
        return {
            "RAW_REVIEWERS": self.raw_reviewers,
            "DISTINCT_SOURCE_LINEAGES": self.distinct_source_lineages,
            "DISTINCT_MODEL_FAMILIES": self.distinct_model_families,
            "DISTINCT_RETRIEVAL_BUNDLES": self.distinct_retrieval_bundles,
            "effective_independence": "NOT_AUTHORITATIVE_UNKNOWN",
        }

    # ------------------------------------------------------------------ #
    # EXPERIMENTAL / NON-AUTHORITATIVE — never a transition authority.
    # ------------------------------------------------------------------ #
    def experimental_effective_lineages(self) -> float:
        """Heuristic only. Labeled NON-AUTHORITATIVE; raw vector is truth."""
        base = max(
            self.distinct_source_lineages,
            self.distinct_model_families,
            self.distinct_retrieval_bundles,
            1,
        )
        if self.overlaps.get("allocator_overlap", "UNKNOWN") == "HIGH":
            base = max(1.0, base - 0.5)
        return base

    # ------------------------------------------------------------------ #
    # Allocation-origin recording (G0 Q3).
    # ------------------------------------------------------------------ #
    def add_reviewer(
        self,
        reviewer_id: str,
        producing_actor: str,
        assigning_actor: str = "",
        task_ref: str = "",
        model_family: str = "",
        provider: str = "",
        source_lineage: str = "",
        retrieval_lineage: str = "",
        prior_conclusion_exposure: str = "",
        experiment_design: str = "",
    ) -> None:
        self.reviewers.append(
            {
                "reviewer_id": reviewer_id,
                "producing_actor": producing_actor,
                "assigning_actor": assigning_actor,
                "task_ref": task_ref,
                "model_family": model_family,
                "provider": provider,
                "source_lineage": source_lineage,
                "retrieval_lineage": retrieval_lineage,
                "prior_conclusion_exposure": prior_conclusion_exposure,
                "experiment_design": experiment_design,
            }
        )

    def allocator_concentration(self) -> str:
        """Observable signal for later S03/S06/S08/S20 — NOT a validity verdict."""
        assigns = {r.get("assigning_actor", "") for r in self.reviewers if r.get("assigning_actor")}
        if len(assigns) <= 1 and len(self.reviewers) > 1:
            return "SINGLE_ALLOCATOR"
        return "MULTI_ALLOCATOR"