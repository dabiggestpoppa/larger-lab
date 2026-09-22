"""Saturation accounting and stop recommendations — canon 2.1.9/2.1.10/2.2.12.

Counters advance only on searches that actually ran: a rate-limited or
unauthenticated adapter contributes failure information, not coverage. Novelty is
measured against what was already known, so a repeat pass over an
already-discovered paper is not a newly discovered specification — counting it
would inflate the marginal-novelty rate until the declared NEGLIGIBLE_NOVELTY
stop rule could never fire and a saturated search would run to budget instead of
stopping (2.1.9).

A STOP recommendation is only representable when a stop condition the plan
itself declared is satisfied: stop rules exist before the search, not after.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence

from qcae.core.discovery.candidate import CanonicalCandidate
from qcae.core.discovery.lead import (
    FAILURE_STATUSES,
    AdapterStatus,
    CandidateKind,
)
from qcae.core.discovery.plan import (
    DiscoveryPlan,
    SaturationMetrics,
    StopCondition,
)
from qcae.core.discovery.report import (
    StopRecommendation,
    StopRecommendationState,
)
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.discovery import AdapterOutcome

from qcae.discovery.planning.families import family_identity_for

__all__ = ["stop_recommendation", "update_saturation"]


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
