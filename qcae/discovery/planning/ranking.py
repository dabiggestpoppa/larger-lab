"""Dedup, family clustering and diversity-aware ranking — canon 2.1.12, 2.7.

Ranking is triage, not a verdict. Canon 2.7.4 is the governing sentence: a
top-ranked candidate means "inspect this first", and 2.7.16 invariant 1 repeats
that ranking "allocates investigation budget; it does not approve acquisition".
Everything here therefore produces *investigation order*, never acquisition
advice, and never a verification level.

What this module implements:

- **Canonical merge (2.1.12).** Leads that point at the same normalized locator
  become one canonical candidate with every path preserved. Identity is
  content-addressed, so merging is deterministic and duplicate paths are counted
  as duplication rather than as corroboration.
- **Family clustering (2.7.6).** Candidates that declare the same lineage family
  are clustered around a representative, so investigating one representative can
  stand in for its family. The only lineage signal available at discovery is the
  adapter-declared ``novelty_family``; richer lineage detection belongs to
  repository intelligence (Block 3) and is deliberately *not* inferred here.
- **Honest score derivation (2.7.2/2.7.10).** Dimensions that follow from lead
  observations are derived and labelled; dimensions that need evidence this layer
  does not have (maintenance, dependency burden, license *verification*) stay at
  the policy's neutral prior and are labelled as neutral. No dimension is
  silently invented from popularity.
- **Popularity firewall (2.7.11/2.7.16 invariant 2).** Popularity enters through
  a bounded blend whose weight is capped, so popularity can break a tie but can
  never outrank semantic fit.
- **Diversity-aware ordering and waves (2.7.5/2.7.14).** Wave 1 admits one
  representative per family and a bounded number per source class; family
  duplicates are explicitly deferred behind their representative (2.7.9's
  "Candidate C → defer pending A because same family" row).
- **Saturation and stop rules (2.1.10/2.1.9).** Counters advance only on
  searches that actually ran, and a STOP recommendation is only representable
  when a stop condition the plan itself declared is satisfied.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from qcae.core.discovery.candidate import CanonicalCandidate
from qcae.core.discovery.lead import (
    FAILURE_STATUSES,
    AdapterStatus,
    CandidateKind,
    CandidateLead,
)
from qcae.core.discovery.plan import (
    DiscoveryPlan,
    HardPrefilter,
    SaturationMetrics,
    StopCondition,
)
from qcae.core.discovery.report import (
    CandidateFamily,
    EscalationEntry,
    NextAction,
    PrefilterDecision,
    PrefilterDecisionRecord,
    Priority,
    StopRecommendation,
    StopRecommendationState,
)
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.discovery import AdapterOutcome
from qcae.core.serialization import SerializableRecord
from qcae.core.validation import require_non_empty_str
from qcae.core.vocabulary import EVIDENCE_STRENGTH_ORDER, EvidenceClass

__all__ = [
    "DIMENSIONS",
    "POPULARITY_WEIGHT_CAP",
    "RankingDimension",
    "RankingPolicy",
    "RankingResult",
    "apply_hard_prefilter",
    "build_families",
    "canonical_key_for",
    "merge_canonical_candidates",
    "merge_leads",
    "rank_candidates",
    "update_saturation",
]


class RankingDimension(StrEnum):
    """Preliminary ranking dimensions (canon 2.7.10, verbatim order)."""

    SEMANTIC_FIT = "semantic_fit"
    COVERAGE_POTENTIAL = "coverage_potential"
    CONSTRAINT_FIT = "constraint_fit"
    FOCUS_EXTRACTABILITY_PRIOR = "focus_extractability_prior"
    EVIDENCE_AVAILABILITY = "evidence_availability"
    MAINTENANCE_PRIOR = "maintenance_prior"
    DEPENDENCY_PRIOR = "dependency_prior"
    LICENSE_PRIOR = "license_prior"
    NOVELTY = "novelty"
    EXPECTED_INVESTIGATION_COST = "expected_investigation_cost"
    EXPECTED_INFORMATION_GAIN = "expected_information_gain"


#: Every dimension must be scored, even when the value is a neutral prior.
DIMENSIONS: Tuple[RankingDimension, ...] = tuple(RankingDimension)

#: Canon 2.7.11: popularity may influence only a *bounded* portion of preliminary
#: ranking and must not overwhelm semantic fit, constraints or evidence
#: availability. 0.10 is the policy ceiling for that portion.
POPULARITY_WEIGHT_CAP = 0.10

#: Dimensions that are derivable from discovery observations alone.
DERIVABLE_DIMENSIONS: frozenset = frozenset(
    {
        RankingDimension.SEMANTIC_FIT,
        RankingDimension.COVERAGE_POTENTIAL,
        RankingDimension.CONSTRAINT_FIT,
        RankingDimension.FOCUS_EXTRACTABILITY_PRIOR,
        RankingDimension.EVIDENCE_AVAILABILITY,
        RankingDimension.NOVELTY,
        RankingDimension.EXPECTED_INVESTIGATION_COST,
        RankingDimension.EXPECTED_INFORMATION_GAIN,
    }
)

#: Candidate-kind extractability priors (2.7.2 "focused-component likelihood").
#: A prior, not a measurement: Block 3/4 replace it with structural evidence.
_EXTRACTABILITY_PRIOR: Mapping[CandidateKind, float] = {
    CandidateKind.INTERNAL_CODE: 0.8,
    CandidateKind.PACKAGE: 0.7,
    CandidateKind.REPOSITORY: 0.6,
    CandidateKind.REFERENCE_IMPLEMENTATION: 0.6,
    CandidateKind.SPECIFICATION: 0.5,
    CandidateKind.PAPER: 0.5,
    CandidateKind.SERVICE: 0.4,
    CandidateKind.CURATED_ENTRY: 0.4,
    CandidateKind.DATASET: 0.3,
}

#: Expected investigation-cost priors by kind (higher = more expensive).
_COST_PRIOR: Mapping[CandidateKind, float] = {
    CandidateKind.INTERNAL_CODE: 0.2,
    CandidateKind.SPECIFICATION: 0.4,
    CandidateKind.PACKAGE: 0.5,
    CandidateKind.REPOSITORY: 0.6,
    CandidateKind.REFERENCE_IMPLEMENTATION: 0.6,
    CandidateKind.PAPER: 0.7,
    CandidateKind.SERVICE: 0.8,
    CandidateKind.CURATED_ENTRY: 0.9,
    CandidateKind.DATASET: 0.9,
}

_KIND_NORMALIZATION = {
    CandidateKind.REPOSITORY: "case-insensitive",
    CandidateKind.PACKAGE: "case-insensitive",
}


@dataclass(frozen=True)
class RankingPolicy(SerializableRecord):
    """Versioned, auditable ranking policy (canon 2.7.11, 2.7.16 invariant 7)."""

    SCHEMA_VERSION = 1

    policy_version: str
    weights: Dict[str, float]
    popularity_weight: float = 0.0
    neutral_prior: float = 0.5
    max_per_family_in_wave_one: int = 1
    max_per_source_class_in_wave_one: int = 2

    def validate(self) -> None:
        require_non_empty_str(self.policy_version, "policy_version")
        if not isinstance(self.weights, dict):
            raise QcaeValidationError("weights must be a mapping of dimension to weight")
        missing = sorted(d.value for d in DIMENSIONS if d.value not in self.weights)
        if missing:
            raise QcaeValidationError(
                f"ranking policy must weight every dimension; missing {missing} "
                "(canon 2.7.10)"
            )
        unknown = sorted(set(self.weights) - {d.value for d in DIMENSIONS})
        if unknown:
            raise QcaeValidationError(f"unknown ranking dimensions: {unknown}")
        total = 0.0
        for name, weight in self.weights.items():
            if not isinstance(weight, (int, float)) or isinstance(weight, bool):
                raise QcaeValidationError(f"weight {name!r} must be a number")
            if weight < 0:
                raise QcaeValidationError(f"weight {name!r} must be >= 0, got {weight!r}")
            total += float(weight)
        if abs(total - 1.0) > 1e-6:
            raise QcaeValidationError(
                f"semantic dimension weights must sum to 1.0, got {total!r}"
            )
        if not (0.0 <= float(self.popularity_weight) <= POPULARITY_WEIGHT_CAP + 1e-9):
            raise QcaeValidationError(
                f"popularity_weight must be within [0, {POPULARITY_WEIGHT_CAP}]: "
                "popularity is a weak signal that must never overwhelm semantic fit "
                "(canon 2.7.11, 2.7.16 invariant 2)"
            )
        if not (0.0 <= float(self.neutral_prior) <= 1.0):
            raise QcaeValidationError("neutral_prior must be within [0, 1]")
        for name in ("max_per_family_in_wave_one", "max_per_source_class_in_wave_one"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise QcaeValidationError(f"{name} must be an integer >= 1")


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


# -- canonical merge (2.1.12) -----------------------------------------------


def canonical_key_for(candidate_kind: CandidateKind, source_locator: str) -> str:
    """Normalize a locator into a merge key (deliberately conservative).

    Over-normalizing would merge genuinely distinct candidates, so only
    well-defined equivalences are applied: surrounding whitespace, a trailing
    slash, a ``.git`` suffix, and — for repository/package identity, where the
    provider itself defines case-insensitive identity — letter case. Anything
    more provider-specific belongs in the adapter that owns that provider's
    quirks (Book V 15.3 adapter isolation).
    """
    locator = (source_locator or "").strip()
    while locator.endswith("/"):
        locator = locator[:-1]
    if locator.endswith(".git"):
        locator = locator[:-4]
    if candidate_kind in _KIND_NORMALIZATION:
        locator = locator.lower()
    return f"{candidate_kind.value}:{locator}"


def _canonical_id_for(key: str) -> str:
    """Content-addressed candidate identity (deterministic across runs)."""
    return "cand-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def merge_canonical_candidates(
    candidates: Sequence[CanonicalCandidate],
) -> Tuple[CanonicalCandidate, ...]:
    """Aggregate candidate records that share one canonical identity (2.1.12).

    Real runs merge leads per adapter outcome and then aggregate the passes, so
    the same project can arrive as two records carrying the same
    content-addressed ``canonical_id``. Aggregating unions the fields that
    preserve discovery paths — lead ids, locators, source classes, claims,
    revisions, readiness and conflicts — rather than dropping a record, because
    canon 2.1.12 requires every path that found the candidate to survive. The
    first record for an identity supplies its kind and canonical locator (both
    are functions of that identity). Every unioned field is order-insensitive and
    record order follows first appearance, so aggregating is idempotent and
    independent of the order in which adapter passes happen to complete.
    """
    aggregated: Dict[str, CanonicalCandidate] = {}
    for candidate in candidates:
        previous = aggregated.get(candidate.canonical_id)
        if previous is None:
            aggregated[candidate.canonical_id] = candidate
            continue
        aggregated[candidate.canonical_id] = CanonicalCandidate(
            canonical_id=previous.canonical_id,
            canonical_key=previous.canonical_key,
            candidate_kind=previous.candidate_kind,
            canonical_locator=previous.canonical_locator,
            merged_locators=tuple(sorted(set(previous.merged_locators)
                                         | set(candidate.merged_locators))),
            lead_ids=tuple(sorted(set(previous.lead_ids) | set(candidate.lead_ids))),
            ready_lead_ids=tuple(sorted(
                set(previous.ready_lead_ids) | set(candidate.ready_lead_ids))),
            source_classes=tuple(sorted(
                set(previous.source_classes) | set(candidate.source_classes),
                key=lambda sc: sc.value,
            )),
            claims_atoms=tuple(sorted(set(previous.claims_atoms)
                                     | set(candidate.claims_atoms))),
            retrieved_revisions=tuple(sorted(set(previous.retrieved_revisions)
                                             | set(candidate.retrieved_revisions))),
            license_claims=tuple(sorted(set(previous.license_claims)
                                       | set(candidate.license_claims))),
            constraint_conflicts=tuple(sorted(set(previous.constraint_conflicts)
                                             | set(candidate.constraint_conflicts))),
            languages=tuple(sorted(set(previous.languages) | set(candidate.languages))),
            novelty_family=previous.novelty_family or candidate.novelty_family,
            notes=previous.notes or candidate.notes,
        )
    for candidate in aggregated.values():
        candidate.validate()
    return tuple(aggregated.values())


def merge_leads(leads: Sequence[CandidateLead]) -> Tuple[CanonicalCandidate, ...]:
    """Merge discovery paths into canonical candidates (canon 2.1.12)."""
    groups: Dict[str, List[CandidateLead]] = {}
    for lead in leads:
        lead.validate()
        key = canonical_key_for(lead.candidate_kind, lead.source_locator)
        groups.setdefault(key, []).append(lead)

    merged: List[CanonicalCandidate] = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda item: item.lead_id)
        kind = members[0].candidate_kind
        locators = sorted({m.source_locator.strip() for m in members})
        canonical_locator = min(
            locators, key=lambda value: (canonical_key_for(kind, value), value)
        )
        claims: List[str] = []
        conflicts: List[str] = []
        licenses: List[str] = []
        languages: List[str] = []
        families: List[str] = []
        revisions: List[str] = []
        for member in members:
            for claim in member.claimed_capabilities + member.possible_atom_matches:
                if claim not in claims:
                    claims.append(claim)
            for conflict in member.initial_constraint_conflicts:
                if conflict not in conflicts:
                    conflicts.append(conflict)
            if member.license_claim and member.license_claim not in licenses:
                licenses.append(member.license_claim)
            if member.language_runtime and member.language_runtime not in languages:
                languages.append(member.language_runtime)
            if member.novelty_family and member.novelty_family not in families:
                families.append(member.novelty_family)
            if member.retrieved_revision and member.retrieved_revision not in revisions:
                revisions.append(member.retrieved_revision)

        candidate = CanonicalCandidate(
            canonical_id=_canonical_id_for(key),
            canonical_key=key,
            candidate_kind=kind,
            canonical_locator=canonical_locator,
            merged_locators=tuple(locators),
            lead_ids=tuple(m.lead_id for m in members),
            source_classes=tuple(
                sorted({m.source_class for m in members}, key=lambda sc: sc.value)
            ),
            claims_atoms=tuple(sorted(claims)),
            ready_lead_ids=tuple(m.lead_id for m in members if m.deeper_intelligence_ready),
            retrieved_revisions=tuple(sorted(revisions)),
            license_claims=tuple(licenses),
            constraint_conflicts=tuple(conflicts),
            languages=tuple(sorted(languages)),
            novelty_family=min(families) if families else "",
        )
        candidate.validate()
        merged.append(candidate)
    return tuple(merged)


# -- families (2.7.6) -------------------------------------------------------


def family_identity_for(candidate: CanonicalCandidate) -> str:
    """The one family identity this module publishes and compares (canon 2.7.6).

    Clustering, novelty sizing and saturation accounting must agree on what
    "the same family" means, or a caller using the ids ranking actually emitted
    can never match them and repeat families stay invisible to saturation.
    """
    label = candidate.novelty_family or f"singleton:{candidate.canonical_id}"
    return "fam-" + hashlib.sha256(label.encode("utf-8")).hexdigest()[:16]


def build_families(
    candidates: Sequence[CanonicalCandidate],
    scores: Mapping[str, float],
    policy: RankingPolicy,
) -> Tuple[CandidateFamily, ...]:
    """Cluster candidates around representatives (canon 2.7.6)."""
    candidates = merge_canonical_candidates(candidates)
    groups: Dict[str, List[CanonicalCandidate]] = {}
    for candidate in candidates:
        groups.setdefault(family_identity_for(candidate), []).append(candidate)

    families: List[CandidateFamily] = []
    for group_id in sorted(groups):
        members = sorted(groups[group_id], key=lambda c: c.canonical_id)
        representative = max(
            members,
            key=lambda c: (float(scores.get(c.canonical_id, 0.0)), _descending_id(c.canonical_id)),
        )
        singleton = len(members) == 1
        family = CandidateFamily(
            family_id=group_id,
            representative_candidate_id=representative.canonical_id,
            member_candidate_ids=tuple(m.canonical_id for m in members),
            shared_lineage=(
                f"adapter-declared novelty family {representative.novelty_family!r}"
                if not singleton
                else "singleton candidate (no shared lineage declared)"
            ),
            independent_family=singleton,
        )
        family.validate()
        families.append(family)
    return tuple(families)


def _descending_id(canonical_id: str) -> str:
    """Tie-break: prefer the lexicographically smallest ID deterministically."""
    return "".join(chr(0x10FFFF - ord(ch)) if ord(ch) < 0x10FFFF else ch for ch in canonical_id)


# -- scoring (2.7.2, 2.7.8, 2.7.10, 2.7.11) --------------------------------


def _derive_dimensions(
    candidate: CanonicalCandidate,
    plan: DiscoveryPlan,
    policy: RankingPolicy,
    family_sizes: Mapping[str, int],
) -> Tuple[Dict[RankingDimension, float], float, float]:
    """Return (dimension scores, popularity blend input, cost units)."""
    requested = set(plan.atom_ids)
    claimed = set(candidate.claims_atoms)
    coverage = len(requested & claimed) / len(requested) if requested else 0.0

    conflict_penalty = min(1.0, 0.25 * len(candidate.constraint_conflicts))
    constraint_fit = max(0.0, 1.0 - conflict_penalty)

    evidence_availability = 1.0 if candidate.deeper_intelligence_ready else 0.4

    family_size = max(1, int(family_sizes.get(family_identity_for(candidate), 1)))
    novelty = 1.0 / family_size

    extractability = _EXTRACTABILITY_PRIOR.get(
        candidate.candidate_kind, policy.neutral_prior
    )
    cost_units = _COST_PRIOR.get(candidate.candidate_kind, policy.neutral_prior)

    # 2.7.8: a candidate can be valuable because evaluating it resolves
    # uncertainty. Unknown license and partial capability coverage are the two
    # uncertainties discovery can actually see.
    information_gain = 0.5
    if not candidate.license_claims:
        information_gain += 0.25
    if 0.0 < coverage < 1.0:
        information_gain += 0.25
    information_gain = min(1.0, information_gain)

    scores: Dict[RankingDimension, float] = {
        RankingDimension.SEMANTIC_FIT: coverage,
        RankingDimension.COVERAGE_POTENTIAL: coverage,
        RankingDimension.CONSTRAINT_FIT: constraint_fit,
        RankingDimension.FOCUS_EXTRACTABILITY_PRIOR: extractability,
        RankingDimension.EVIDENCE_AVAILABILITY: evidence_availability,
        RankingDimension.MAINTENANCE_PRIOR: policy.neutral_prior,
        RankingDimension.DEPENDENCY_PRIOR: policy.neutral_prior,
        RankingDimension.LICENSE_PRIOR: policy.neutral_prior,
        RankingDimension.NOVELTY: novelty,
        RankingDimension.EXPECTED_INVESTIGATION_COST: 1.0 - cost_units,
        RankingDimension.EXPECTED_INFORMATION_GAIN: information_gain,
    }
    popularity_input = min(1.0, candidate.duplicate_path_count / 4.0)
    return scores, popularity_input, cost_units


def _blend(
    dimension_scores: Mapping[RankingDimension, float],
    popularity_input: float,
    policy: RankingPolicy,
) -> float:
    semantic = sum(
        float(policy.weights[dimension.value]) * float(dimension_scores[dimension])
        for dimension in DIMENSIONS
    )
    weight = float(policy.popularity_weight)
    return (1.0 - weight) * semantic + weight * popularity_input


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


# -- prefilter (2.7.3, plan hard prefilters) --------------------------------


def apply_hard_prefilter(
    prefilter: HardPrefilter,
    candidate: CanonicalCandidate,
    decision: PrefilterDecision,
    evidence_class: EvidenceClass,
    rationale: str,
) -> PrefilterDecisionRecord:
    """Record a prefilter judgement, enforcing its evidence floor (2.7.3).

    The caller states what evidence actually exists. A decision taken on
    evidence weaker than the prefilter's own floor is refused, so "reject because
    a README did not mention a license" is not expressible.
    """
    if EVIDENCE_STRENGTH_ORDER.index(evidence_class) < EVIDENCE_STRENGTH_ORDER.index(
        prefilter.min_evidence_class
    ):
        raise QcaeValidationError(
            f"prefilter {prefilter.prefilter_id!r} requires at least "
            f"{prefilter.min_evidence_class.value} evidence; {evidence_class.value} was "
            "supplied (canon 2.7.3: weak metadata cannot justify a decision)"
        )
    record = PrefilterDecisionRecord(
        candidate_id=candidate.canonical_id,
        prefilter_id=prefilter.prefilter_id,
        decision=decision,
        evidence_class=evidence_class,
        rationale=rationale,
    )
    record.validate()
    return record


# -- ranking pass -----------------------------------------------------------


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
    outcomes: Dict[str, float] = {}
    for candidate in candidates:
        dimension_scores, popularity_input, cost_units = _derive_dimensions(
            candidate, plan, policy, family_sizes
        )
        if candidate.canonical_id in popularity_map:
            popularity_input = max(0.0, min(1.0, float(popularity_map[candidate.canonical_id])))
        derived[candidate.canonical_id] = (dimension_scores, popularity_input, cost_units)
        blended = _blend(dimension_scores, popularity_input, policy)
        scores[candidate.canonical_id] = blended
        outcomes[candidate.canonical_id] = blended

    families = build_families(candidates, scores, policy)
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
        key=lambda c: (-scores[c.canonical_id], _descending_id(c.canonical_id)),
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

    entries.sort(key=lambda e: (e.wave, -e.score, _descending_id(e.candidate_id)))
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


# -- saturation + stop (2.1.9, 2.1.10, 2.7.14) ------------------------------


def update_saturation(
    previous: SaturationMetrics,
    *,
    outcomes: Sequence[AdapterOutcome] = (),
    canonical_candidates: Sequence[CanonicalCandidate] = (),
    previous_candidate_ids: Iterable[str] = (),
    previous_family_ids: Iterable[str] = (),
    previous_covered_atoms: Iterable[str] = (),
    saturated: bool = False,
    saturation_reason: str = "",
) -> SaturationMetrics:
    """Advance the marginal-novelty counters (canon 2.1.10, 2.2.12).

    Only searches that actually ran advance the counters (a rate-limited or
    unauthenticated adapter contributes failure information, not coverage), and
    novelty is measured against what was already known.
    """
    known_candidates = set(previous_candidate_ids)
    known_families = set(previous_family_ids)
    known_atoms = set(previous_covered_atoms)

    new_candidates = 0
    new_families: set = set()
    new_specifications = 0
    new_atoms: set = set()
    for candidate in canonical_candidates:
        is_new = candidate.canonical_id not in known_candidates
        if is_new:
            new_candidates += 1
        family = family_identity_for(candidate)
        if family not in known_families:
            new_families.add(family)
        # Canon 2.1.10 measures novelty against what was already known: a repeat
        # pass over an already-discovered paper is not a newly discovered
        # specification. Counting it inflates marginal_novelty_rate until the
        # declared NEGLIGIBLE_NOVELTY stop rule can never fire and a saturated
        # search runs to budget instead of stopping (canon 2.1.9).
        if is_new and candidate.candidate_kind in (
            CandidateKind.SPECIFICATION,
            CandidateKind.PAPER,
        ):
            new_specifications += 1
        new_atoms.update(set(candidate.claims_atoms) - known_atoms)

    inspected = 0
    failure_information = 0
    for outcome in outcomes:
        outcome.validate()
        if outcome.counts_toward_saturation:
            inspected += outcome.results_inspected
        if outcome.status == AdapterStatus.NO_RESULTS or outcome.status in FAILURE_STATUSES:
            failure_information += 1

    metrics = SaturationMetrics(
        queries_executed=previous.queries_executed + len(outcomes),
        results_inspected=previous.results_inspected + inspected,
        new_candidates=previous.new_candidates + new_candidates,
        new_implementation_families=previous.new_implementation_families + len(new_families),
        new_specifications=previous.new_specifications + new_specifications,
        new_atoms_covered=previous.new_atoms_covered + len(new_atoms),
        # Discovery assigns no acquisition forms yet (2.5.12 outcomes are
        # post-forensics), so this counter is not incremented here.
        new_acquisition_forms=previous.new_acquisition_forms,
        new_failure_information=previous.new_failure_information + failure_information,
        saturated=saturated,
        saturation_reason=saturation_reason,
    )
    metrics.validate()
    return metrics


def stop_recommendation(
    plan: DiscoveryPlan,
    metrics: SaturationMetrics,
    *,
    budget_exhausted: bool = False,
    enough_non_dominated: bool = False,
    hard_constraints_eliminated_class: bool = False,
    contract_amendment_required: bool = False,
    rationale: str = "",
) -> StopRecommendation:
    """Recommend stop/continue using only the plan's declared stop rules (2.1.9)."""
    metrics.validate()
    declared = {rule.condition for rule in plan.stop_rules}
    satisfied: List[StopCondition] = []

    if budget_exhausted:
        satisfied.append(StopCondition.BUDGET_CEILING_REACHED)
    if enough_non_dominated:
        satisfied.append(StopCondition.NON_DOMINATED_SET_SUFFICIENT)
    if hard_constraints_eliminated_class:
        satisfied.append(StopCondition.HARD_CONSTRAINTS_ELIMINATE_CLASS)
    if contract_amendment_required:
        satisfied.append(StopCondition.CONTRACT_AMBIGUITY_REQUIRES_AMENDMENT)
    if metrics.saturated:
        negligible_rule = next(
            (r for r in plan.stop_rules if r.condition == StopCondition.NEGLIGIBLE_NOVELTY),
            None,
        )
        if negligible_rule is None or negligible_rule.threshold is None:
            raise QcaeValidationError(
                "saturation was declared but the plan declares no NEGLIGIBLE_NOVELTY "
                "rule with a threshold; a stop cannot be justified by an undeclared "
                "condition (canon 2.1.9)"
            )
        if metrics.marginal_novelty_rate < float(negligible_rule.threshold):
            satisfied.append(StopCondition.NEGLIGIBLE_NOVELTY)

    undeclared = sorted(c.value for c in satisfied if c not in declared)
    if undeclared:
        raise QcaeValidationError(
            f"stop conditions satisfied but not declared by the plan: {undeclared} "
            "(canon 2.1.9: stop rules exist before the search, not after)"
        )

    if satisfied:
        state = StopRecommendationState.STOP
        detail = rationale or (
            "declared stop conditions satisfied: "
            + ", ".join(c.value for c in satisfied)
        )
    else:
        state = StopRecommendationState.CONTINUE
        detail = rationale or (
            "no declared stop condition is satisfied; continuing within the plan's "
            f"budget (queries executed: {metrics.queries_executed}, marginal novelty "
            f"{metrics.marginal_novelty_rate:.3f})"
        )
    recommendation = StopRecommendation(
        state=state, satisfied_conditions=tuple(satisfied), rationale=detail
    )
    recommendation.validate()
    return recommendation
