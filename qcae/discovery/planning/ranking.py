"""Ordering canonical candidates into an escalation queue — canon 2.7.5/2.7.14/2.7.16.

This module owns one thing: producing the investigation order. It consumes what
its sibling modules decided — canonical identity, family membership, dimension
scores and prefilter decisions — and turns them into waves, next actions and
priorities.

Ranking is triage, not a verdict. Canon 2.7.4 is the governing sentence: a
top-ranked candidate means "inspect this first", and 2.7.16 invariant 1 repeats
that ranking "allocates investigation budget; it does not approve acquisition".
Nothing here returns a verification level or acquisition advice.

What this module implements:

- **Diversity-aware ordering and waves (2.7.5/2.7.14).** Wave 1 admits one
  representative per family and a bounded number per source class; candidates
  that are not their family's representative are explicitly deferred behind it
  (2.7.9's "Candidate C → defer pending A because same family" row).
- **Rejection is a recorded decision, never a silence (2.7.3).** A candidate the
  plan's prefilters rejected becomes an explicit wave-3
  ``REJECT_HARD_CONSTRAINT`` row carrying that decision's rationale.

Where the sibling concerns live, so this module never grows back into one file:

- ranking vocabulary + the versioned policy: ``ranking_policy``
- canonical identity, merge and tie-break: ``canonical``
- what a family is and who represents it: ``families``
- dimension scores and the popularity cap: ``scoring``
- the prefilter evidence floor: ``prefilter``
- pass-over-pass counters and stop rules: ``saturation``
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from qcae.core.discovery.candidate import CanonicalCandidate
from qcae.core.discovery.lead import CandidateKind
from qcae.core.discovery.plan import DiscoveryPlan, SaturationMetrics
from qcae.core.discovery.report import (
    CandidateFamily,
    EscalationEntry,
    NextAction,
    PrefilterDecision,
    PrefilterDecisionRecord,
    Priority,
)

from qcae.discovery.planning.canonical import (
    descending_id,
    merge_canonical_candidates,
)
from qcae.discovery.planning.families import build_families, family_identity_for
from qcae.discovery.planning.ranking_policy import (
    DERIVABLE_DIMENSIONS,
    DIMENSIONS,
    RankingDimension,
    RankingPolicy,
)
from qcae.discovery.planning.scoring import blend, derive_dimensions

__all__ = ["RankingResult", "rank_candidates"]


@dataclass(frozen=True)
class RankingResult:
    """In-process assembly of a ranking pass (not persisted itself)."""

    policy_version: str
    families: Tuple[CandidateFamily, ...]
    queue: Tuple[EscalationEntry, ...]
    prefilter_decisions: Tuple[PrefilterDecisionRecord, ...]
    saturation: SaturationMetrics

    @property
    def rejected_candidate_ids(self) -> Tuple[str, ...]:
        return tuple(
            entry.candidate_id
            for entry in self.queue
            if entry.prefilter_decision == PrefilterDecision.REJECT
        )

    def entry_for(self, candidate_id: str) -> Optional[EscalationEntry]:
        for entry in self.queue:
            if entry.candidate_id == candidate_id:
                return entry
        return None


def rank_candidates(
    *,
    candidates: Sequence[CanonicalCandidate],
    plan: DiscoveryPlan,
    policy: RankingPolicy,
    popularity: Optional[Mapping[str, float]] = None,
    prefilter_decisions: Sequence[PrefilterDecisionRecord] = (),
) -> RankingResult:
    """Rank canonical candidates into an escalation queue (canon 2.7)."""
    policy.validate()
    # Aggregate first: candidates that arrived through separate merge passes must
    # rank as the one candidate canon 2.1.12 defines them to be.
    candidates = merge_canonical_candidates(candidates)
    if not candidates:
        return RankingResult(
            policy_version=policy.policy_version,
            families=(),
            queue=(),
            prefilter_decisions=tuple(prefilter_decisions),
            saturation=SaturationMetrics(),
        )

    family_sizes: Dict[str, int] = {}
    for candidate in candidates:
        key = family_identity_for(candidate)
        family_sizes[key] = family_sizes.get(key, 0) + 1

    popularity_map = popularity or {}
    derived: Dict[str, Tuple[Dict[RankingDimension, float], float, float]] = {}
    scores: Dict[str, float] = {}
    for candidate in candidates:
        dimension_scores, popularity_input, cost_units = derive_dimensions(
            candidate, plan, policy, family_sizes
        )
        if candidate.canonical_id in popularity_map:
            popularity_input = max(0.0, min(1.0, float(popularity_map[candidate.canonical_id])))
        derived[candidate.canonical_id] = (dimension_scores, popularity_input, cost_units)
        scores[candidate.canonical_id] = blend(dimension_scores, popularity_input, policy)

    families = build_families(candidates, scores)
    family_of = {
        member: family.family_id
        for family in families
        for member in family.member_candidate_ids
    }
    representative_of = {
        family.family_id: family.representative_candidate_id for family in families
    }
    decisions = {d.candidate_id: d for d in prefilter_decisions}

    ordered = sorted(
        candidates,
        key=lambda c: (-scores[c.canonical_id], descending_id(c.canonical_id)),
    )

    entries: List[EscalationEntry] = []
    wave_one_families: Dict[str, int] = {}
    wave_one_source_classes: Dict[str, int] = {}
    for candidate in ordered:
        dimension_scores, popularity_input, cost_units = derived[candidate.canonical_id]
        family_id = family_of[candidate.canonical_id]
        representative = representative_of[family_id]
        decision = decisions.get(candidate.canonical_id)
        coverage = dimension_scores[RankingDimension.SEMANTIC_FIT]
        info_gain = dimension_scores[RankingDimension.EXPECTED_INFORMATION_GAIN]
        next_action = _next_action_for(candidate, coverage, plan)

        if decision is not None and decision.decision == PrefilterDecision.REJECT:
            entry = EscalationEntry(
                candidate_id=candidate.canonical_id,
                family_id=family_id,
                next_action=NextAction.REJECT_HARD_CONSTRAINT,
                priority=Priority.LOW,
                wave=3,
                rationale=decision.rationale,
                score=scores[candidate.canonical_id],
                expected_information_gain=info_gain,
                expected_cost_units=cost_units,
                prefilter_decision=PrefilterDecision.REJECT,
                dimension_scores={d.value: dimension_scores[d] for d in DIMENSIONS},
            )
            entries.append(entry)
            continue

        if candidate.canonical_id != representative:
            entry = EscalationEntry(
                candidate_id=candidate.canonical_id,
                family_id=family_id,
                next_action=NextAction.DEFER_PENDING_FAMILY,
                priority=Priority.LOW,
                wave=3,
                rationale=(
                    "same family as its representative: canon 2.7.6 inspects a "
                    "representative first and branches only when differences matter"
                ),
                score=scores[candidate.canonical_id],
                expected_information_gain=info_gain,
                expected_cost_units=cost_units,
                deferred_pending=representative,
                dimension_scores={d.value: dimension_scores[d] for d in DIMENSIONS},
            )
            entries.append(entry)
            continue

        base_wave = _base_wave(cost_units, info_gain)
        wave = base_wave
        if base_wave == 1:
            family_key = family_id
            source_key = candidate.source_classes[0].value
            if (
                wave_one_families.get(family_key, 0) >= policy.max_per_family_in_wave_one
                or wave_one_source_classes.get(source_key, 0)
                >= policy.max_per_source_class_in_wave_one
            ):
                wave = 2
            else:
                wave_one_families[family_key] = wave_one_families.get(family_key, 0) + 1
                wave_one_source_classes[source_key] = (
                    wave_one_source_classes.get(source_key, 0) + 1
                )

        entry = EscalationEntry(
            candidate_id=candidate.canonical_id,
            family_id=family_id,
            next_action=next_action,
            priority=_priority_for(scores[candidate.canonical_id]),
            wave=wave,
            rationale=_rationale_for(candidate, coverage, cost_units, info_gain, wave),
            score=scores[candidate.canonical_id],
            expected_information_gain=info_gain,
            expected_cost_units=cost_units,
            dimension_scores={d.value: dimension_scores[d] for d in DIMENSIONS},
        )
        entries.append(entry)

    entries.sort(key=lambda e: (e.wave, -e.score, descending_id(e.candidate_id)))
    for entry in entries:
        entry.validate()

    return RankingResult(
        policy_version=policy.policy_version,
        families=families,
        queue=tuple(entries),
        prefilter_decisions=tuple(prefilter_decisions),
        # Saturation is accounted by ``update_saturation`` from adapter
        # outcomes; a ranking pass alone observes no search work.
        saturation=SaturationMetrics(),
    )


def _next_action_for(
    candidate: CanonicalCandidate, coverage: float, plan: DiscoveryPlan
) -> NextAction:
    """The cheapest useful next step (canon 2.7.8, 2.7.9)."""
    if candidate.candidate_kind in (CandidateKind.SPECIFICATION, CandidateKind.PAPER):
        return NextAction.SPECIFICATION_LOOKUP
    if not candidate.license_claims:
        return NextAction.LICENSE_VERIFY
    if not candidate.deeper_intelligence_ready:
        return NextAction.REPOSITORY_METADATA
    if coverage >= 1.0:
        return NextAction.DEEP_INTELLIGENCE
    return NextAction.SOURCE_TREE_MAP


def _priority_for(score: float) -> Priority:
    if score >= 0.66:
        return Priority.HIGH
    if score >= 0.40:
        return Priority.MEDIUM
    return Priority.LOW


def _base_wave(cost_units: float, info_gain: float) -> int:
    """Wave 1 cheap/high-information, wave 2 promising, wave 3 expensive (2.7.14)."""
    if cost_units < 0.4 and info_gain >= 0.5:
        return 1
    if cost_units < 0.7:
        return 2
    return 3


def _rationale_for(
    candidate: CanonicalCandidate, coverage: float, cost_units: float,
    info_gain: float, wave: int,
) -> str:
    derived = sorted(d.value for d in DIMENSIONS if d in DERIVABLE_DIMENSIONS)
    neutral = sorted(
        d.value for d in DIMENSIONS if d not in DERIVABLE_DIMENSIONS
    )
    return (
        f"atom coverage {coverage:.2f} from declared claims (not proof); "
        f"expected cost prior {cost_units:.2f}, expected information gain "
        f"{info_gain:.2f}; wave {wave} by canon 2.7.14. Derived dimensions: "
        f"{', '.join(derived)}. Neutral priors (no discovery-level evidence yet): "
        f"{', '.join(neutral)}. Discovery paths: {candidate.independent_path_count} "
        f"source class(es), {candidate.duplicate_path_count} duplicate path(s) "
        "(duplicates are not corroboration, canon 2.1.12)"
    )
