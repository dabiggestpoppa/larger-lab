"""Saturation accounting and stop recommendations — canon 2.1.9/2.1.10/2.2.12.

Counters advance only on searches that actually ran: a rate-limited or
unauthenticated adapter contributes failure information, not coverage. Novelty is
measured against what was already known, so a repeat pass over an
already-discovered paper is not a newly discovered specification — counting it
would inflate the marginal-novelty rate until the declared NEGLIGIBLE_NOVELTY
stop rule could never fire and a saturated search would run to budget instead of
stopping (2.1.9).

A STOP recommendation is only representable when a stop condition the plan
itself declared is satisfied: stop rules exist before the search, not after,
and no raw caller boolean may create one (P3-R4-R1) — saturation is derived
from the typed counters the accounting itself advances.
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
    StopConditionAssessment,
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
    plan: DiscoveryPlan,
    outcomes: Sequence[AdapterOutcome] = (),
    canonical_candidates: Sequence[CanonicalCandidate] = (),
    previous_candidate_ids: Iterable[str] = (),
    previous_family_ids: Iterable[str] = (),
    previous_covered_atoms: Iterable[str] = (),
    novel_atom_scope: Iterable[str] = (),
    negative_observation_ids: Iterable[str] = (),
    previous_negative_observation_ids: Iterable[str] = (),
) -> SaturationMetrics:
    """Advance the marginal-novelty counters (canon 2.1.10, 2.2.12).

    Only searches that actually ran advance the counters (a rate-limited or
    unauthenticated adapter contributes failure information, not coverage), and
    novelty is measured against what was already known. Saturation is derived
    here, never asserted (P3-R4-R1: no raw caller boolean may create a STOP) —
    a caller who judges the families exhausted files a
    NON_DOMINATED_SET_SUFFICIENT assessment instead.

    ``novel_atom_scope`` is this plan's authorized external scope (P3-R4C2): a
    candidate that claims an atom outside it is an observation about another
    plan's scope — a provider may mention it, but it cannot increase
    ``new_atoms_covered`` or satisfy this plan.
    """
    known_candidates = set(previous_candidate_ids)
    known_families = set(previous_family_ids)
    known_atoms = set(previous_covered_atoms)
    in_scope = set(novel_atom_scope)

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
        # P3-R4C2: only atoms inside the plan's authorized external scope can
        # become newly covered here — an out-of-scope mention is not this
        # plan's evidence. Callers that pass no scope keep the unscoped
        # accounting (the assembler always passes the baseline-authorized one).
        claimed = set(candidate.claims_atoms)
        if in_scope:
            claimed &= in_scope
        new_atoms.update(claimed - known_atoms)

    inspected = 0
    for outcome in outcomes:
        outcome.validate()
        if outcome.counts_toward_saturation:
            inspected += outcome.results_inspected
    # P3-R4C4: failure information is identity-deduplicated. The caller hands
    # over the deduplicated observation ids seen this pass and the ones already
    # known; only identities not known before are new negative knowledge, so a
    # repeated identical failure or empty search cannot inflate the
    # marginal-novelty numerator the negligible-novelty stop law reads. A
    # caller without typed observations still gets within-pass identity dedup
    # over (query, adapter, status) instead of a raw per-outcome count.
    if negative_observation_ids:
        failure_information = len(
            set(negative_observation_ids) - set(previous_negative_observation_ids))
    else:
        failure_information = len({
            (o.query_id, o.adapter_id, o.status.value)
            for o in outcomes
            if o.status == AdapterStatus.NO_RESULTS or o.status in FAILURE_STATUSES
        })

    # P3-R4-R1: derived, not asserted. This pass derived "saturated" when its
    # searches actually carried observations — at least one result inspected —
    # and found nothing new. The reason is the same derivation, so the record
    # always stands on the counters it was computed from. A pass with no
    # payload (only empty or failed searches) is never saturation: it produced
    # no observations for the rate to be a rate over.
    derived_saturated = (
        inspected > 0
        and not new_candidates
        and not new_specifications
        and not new_families
        and not new_atoms
    )
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
        saturated=derived_saturated,
        saturation_reason=(
            "derived: this pass inspected results and discovered nothing new "
            "(no new candidates, specifications, families or atoms)"
        ) if derived_saturated else "",
    )
    metrics.validate()
    return metrics


def stop_recommendation(
    plan: DiscoveryPlan,
    metrics: SaturationMetrics,
    *,
    assessments: Sequence[StopConditionAssessment] = (),
    assessed_at: str = "1970-01-01T00:00:00Z",
    rationale: str = "",
) -> StopRecommendation:
    """Recommend stop/continue from attributable assessments (canon 2.1.9).

    P3-R4C3: there is no boolean path to a STOP. Each satisfied condition must
    arrive as a typed ``StopConditionAssessment`` naming its evaluator, policy,
    subject set, derivation and evidence; the budget condition is additionally
    derived from the typed counters here, and NEGLIGIBLE_NOVELTY is derived
    from the metrics under the plan's declared threshold. The recommendation
    that results is advice only — it grants no acquisition authority.

    P3-R4-R1 (§5 law 8): ``SaturationMetrics.saturated`` is derived from the
    typed accounting, never caller-asserted. NEGLIGIBLE_NOVELTY additionally
    requires inspected results — an exhaustion rate is a rate over
    observations, and a pass where nothing carried a payload has none.
    """
    metrics.validate()
    declared = {rule.condition for rule in plan.stop_rules}
    satisfied: List[StopCondition] = []

    # Law 1: budget exhaustion is derived from typed accounting, not asserted.
    if (
        metrics.queries_executed >= plan.budget.max_queries
        or metrics.results_inspected >= plan.budget.max_results_inspected
        or metrics.new_failure_information >= plan.budget.max_source_calls
    ):
        satisfied.append(StopCondition.BUDGET_CEILING_REACHED)

    # Caller-supplied attributable assessments for the judgement conditions.
    supplied: dict = {}
    for assessment in assessments:
        if assessment.condition in supplied:
            raise QcaeValidationError(
                f"duplicate stop assessment for {assessment.condition.value}"
            )
        supplied[assessment.condition] = assessment

    if StopCondition.NON_DOMINATED_SET_SUFFICIENT in supplied:
        satisfied.append(StopCondition.NON_DOMINATED_SET_SUFFICIENT)
    if StopCondition.HARD_CONSTRAINTS_ELIMINATE_CLASS in supplied:
        satisfied.append(StopCondition.HARD_CONSTRAINTS_ELIMINATE_CLASS)
    if StopCondition.CONTRACT_AMBIGUITY_REQUIRES_AMENDMENT in supplied:
        satisfied.append(StopCondition.CONTRACT_AMBIGUITY_REQUIRES_AMENDMENT)

    # Law 6: negligible novelty is derived from the (in-scope) observations.
    # An exhaustion rate is a rate over observations: a pass where nothing
    # carried a payload (empty or failed searches only) has no observations to
    # derive a rate from, so it cannot satisfy any threshold (§5 law 7) — no
    # boolean may stand in for the missing evidence.
    if metrics.saturated and metrics.results_inspected > 0:
        # The undeclared-condition tripwire is for *asserted* saturation: the
        # accounting derives saturation with a ``derived: `` reason, so a
        # derived measurement never trips it — a plan that declares no
        # NEGLIGIBLE_NOVELTY rule simply continues (its own declared choice),
        # while an externally supplied saturated record still cannot invent
        # the condition.
        asserted = not metrics.saturation_reason.startswith("derived: ")
        negligible_rule = next(
            (r for r in plan.stop_rules if r.condition == StopCondition.NEGLIGIBLE_NOVELTY),
            None,
        )
        if asserted and (negligible_rule is None or negligible_rule.threshold is None):
            raise QcaeValidationError(
                "saturation was declared but the plan declares no NEGLIGIBLE_NOVELTY "
                "rule with a threshold; a stop cannot be justified by an undeclared "
                "condition (canon 2.1.9)"
            )
        if (negligible_rule is not None and negligible_rule.threshold is not None
                and metrics.marginal_novelty_rate < float(negligible_rule.threshold)):
            satisfied.append(StopCondition.NEGLIGIBLE_NOVELTY)

    # Every satisfied condition must carry its attributable assessment. The
    # two derived conditions are synthesized here from the typed accounting
    # they were derived from; the judgement conditions come from the caller.
    def _assessment_for(condition: StopCondition) -> StopConditionAssessment:
        if condition is StopCondition.BUDGET_CEILING_REACHED:
            return StopConditionAssessment(
                condition=condition,
                discovery_plan_id=plan.discovery_plan_id,
                contract_id=plan.contract_id,
                contract_version=plan.contract_version,
                evaluator_id="qcae-saturation-accounting",
                policy_version=plan.policy_version,
                assessed_at=assessed_at,
                subject_ids=(
                    f"queries_executed:{metrics.queries_executed}",
                    f"results_inspected:{metrics.results_inspected}",
                    f"max_queries:{plan.budget.max_queries}",
                    f"max_results_inspected:{plan.budget.max_results_inspected}",
                ),
                derivation_method=(
                    "derived from typed saturation counters against the plan's "
                    "declared budget envelope"
                ),
                rationale=(
                    f"executed {metrics.queries_executed}/{plan.budget.max_queries} "
                    f"queries, inspected {metrics.results_inspected}/"
                    f"{plan.budget.max_results_inspected} results"
                ),
            )
        if condition is StopCondition.NEGLIGIBLE_NOVELTY:
            threshold = next(
                float(r.threshold) for r in plan.stop_rules
                if r.condition is StopCondition.NEGLIGIBLE_NOVELTY
            )
            return StopConditionAssessment(
                condition=condition,
                discovery_plan_id=plan.discovery_plan_id,
                contract_id=plan.contract_id,
                contract_version=plan.contract_version,
                evaluator_id="qcae-saturation-accounting",
                policy_version=plan.policy_version,
                assessed_at=assessed_at,
                subject_ids=(
                    f"marginal_novelty_rate:{metrics.marginal_novelty_rate:.6f}",
                    f"results_inspected:{metrics.results_inspected}",
                    f"threshold:{threshold}",
                ),
                derivation_method=(
                    "derived saturation from the typed accounting (this pass "
                    "inspected results and discovered nothing new), derived "
                    "the marginal novelty rate from the in-scope observations "
                    "and compared it with the plan's declared NEGLIGIBLE_NOVELTY "
                    "threshold"
                ),
                rationale=(
                    "the pass inspected results with no new discoveries; "
                    f"marginal novelty {metrics.marginal_novelty_rate:.3f} is "
                    f"below the declared threshold {threshold}"
                ),
            )
        return supplied[condition]

    validated_assessments = tuple(_assessment_for(c) for c in satisfied)
    for assessment in validated_assessments:
        assessment.validate()

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
        state=state,
        satisfied_conditions=tuple(satisfied),
        assessments=validated_assessments,
        rationale=detail,
    )
    recommendation.validate()
    return recommendation
