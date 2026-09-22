"""Honest dimension derivation and the popularity-bounded blend — canon 2.7.2/2.7.8/2.7.10/2.7.11.

Dimensions that follow from lead observations are derived here. Dimensions that
need evidence this layer does not have (maintenance, dependency burden, license
*verification*) are reported at the policy's neutral prior and labelled as
neutral in the rationale ``ranking`` writes. No dimension is silently invented
from popularity.

Popularity enters only through ``blend``, whose weight the policy caps
(2.7.11/2.7.16 invariant 2), so popularity can break a tie but can never
outrank semantic fit, constraints or evidence availability.
"""

from __future__ import annotations

from typing import Dict, Mapping, Tuple

from qcae.core.discovery.candidate import CanonicalCandidate
from qcae.core.discovery.lead import CandidateKind
from qcae.core.discovery.plan import DiscoveryPlan

from qcae.discovery.planning.families import family_identity_for
from qcae.discovery.planning.ranking_policy import (
    DIMENSIONS,
    RankingDimension,
    RankingPolicy,
)

__all__ = ["blend", "derive_dimensions"]

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


def derive_dimensions(
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


def blend(
    dimension_scores: Mapping[RankingDimension, float],
    popularity_input: float,
    policy: RankingPolicy,
) -> float:
    """Weighted semantic score with popularity bounded by the policy cap (2.7.11)."""
    semantic = sum(
        float(policy.weights[dimension.value]) * float(dimension_scores[dimension])
        for dimension in DIMENSIONS
    )
    weight = float(policy.popularity_weight)
    return (1.0 - weight) * semantic + weight * popularity_input
