"""Assemble the Block 2 terminal artifact from the pieces a run produced — canon 2.7.15.

``DiscoveryReport`` is the phase's terminal artifact, and the ranking layer's
output is investigation order rather than a verdict (2.7.4, 2.7.16 invariant 1).
This module is what actually produces that artifact: it takes the pieces a caller
holds — the plan, the internal baseline record, the adapter outcomes that ran, and
the ranking pass — and returns the assembled report.

It is a pure function of records. It performs **no discovery and no egress**: no
adapter is touched, no transport is imported, and nothing here can start a search.
Evidence flows one way, from the pieces into the artifact.

Two rules govern what it does with each piece:

- **Derive only what the pieces make factual.** Counters, the budget verdict, the
  partial-search notes, the negative findings and the remaining uncertainties are
  read off the plan, the baseline, the outcomes and the metrics. Judgements that
  are not in the records — that the non-dominated set is sufficient, that a
  contract amendment is required — are *declared* by the caller and passed
  through, never inferred. A condition the plan never declared still cannot
  justify a stop, because ``stop_recommendation`` owns that law (2.1.9).
- **Fail closed instead of dropping a piece.** A discovered candidate the ranking
  never saw, a baseline belonging to another plan or atom scope, a search that
  reached a source the plan never allocated, an unlabelled partial search, and a
  sufficiency declaration with no candidate set to be sufficient are refused
  rather than assembled into a report that quietly omits them. A contradiction
  the artifact cannot refuse — search that ran for atoms the baseline had already
  satisfied internally — is *disclosed* in its notes instead.

Owned elsewhere, deliberately not reimplemented here: canonical identity and merge
(``planning.canonical``), family identity (``planning.families``), the counting
rule (``planning.saturation``) and the report's own laws (``core.discovery.report``).
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from qcae.core.discovery.candidate import CanonicalCandidate
from qcae.core.discovery.lead import FAILURE_STATUSES
from qcae.core.discovery.plan import (
    DiscoveryBudget,
    DiscoveryPlan,
    SaturationMetrics,
)
from qcae.core.discovery.vocabulary import SourceClass
from qcae.core.discovery.report import (
    DiscoveryReport,
    PrefilterDecision,
    make_discovery_report,
)
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.discovery import AdapterOutcome, AdapterStatus

from qcae.discovery.internal.baseline import InternalBaselineRecord
from qcae.discovery.planning.canonical import (
    merge_canonical_candidates,
    merge_leads,
)
from qcae.discovery.planning.families import family_identity_for
from qcae.discovery.planning.ranking import RankingResult
from qcae.discovery.planning.saturation import (
    stop_recommendation,
    update_saturation,
)

__all__ = ["assemble_discovery_report"]


def assemble_discovery_report(
    *,
    report_id: str,
    plan: DiscoveryPlan,
    baseline: InternalBaselineRecord,
    ranking: RankingResult,
    outcomes: Sequence[AdapterOutcome] = (),
    previous_report: Optional[DiscoveryReport] = None,
    previous_metrics: Optional[SaturationMetrics] = None,
    previously_known_candidates: Sequence[CanonicalCandidate] = (),
    saturated: bool = False,
    saturation_reason: str = "",
    enough_non_dominated: bool = False,
    hard_constraints_eliminated_class: bool = False,
    contract_amendment_required: bool = False,
    stop_rationale: str = "",
    created_at: str = "",
    created_by: str = "",
) -> DiscoveryReport:
    """Assemble one discovery pass into its terminal report (canon 2.7.15).

    ``outcomes`` are the adapter results that ran; ``ranking`` is the pass over
    the candidates those outcomes produced. The judgement flags are the caller's
    declarations and are never inferred from the other pieces.

    For a later pass, hand the previous artifact over as ``previous_report``: the
    report carries both the counters and the canonical candidates they measured,
    so novelty stays measured against what was known (2.1.10) with no bookkeeping
    in the caller — which is the only reliable way to do it, since a caller whose
    records are gone (a durable loop restarting from the artifact) cannot
    reconstruct them. ``previous_metrics`` and ``previously_known_candidates``
    remain available for a caller that holds the pieces itself; supplying them
    alongside ``previous_report`` is refused, because the history has one owner.
    A counters-only handoff is still *disclosed* in ``coverage_notes`` rather than
    left to inflate the novelty the stop law reads.

    The history is bound to the capability it measured: a report assembled for
    another contract or another revision of it (canon 2.1.10) is refused rather
    than accepted as this pass's past, since its known set would otherwise be
    counted as this capability's knowledge in the counters and the stop verdict.
    A re-cut plan for the *same* capability is accepted and disclosed.
    """
    _require_one_history_source(previous_report, previous_metrics,
                               previously_known_candidates)
    _require_history_is_for_this_capability(previous_report, plan)
    if previous_report is not None:
        previous_metrics = previous_report.saturation_metrics
        previously_known_candidates = previous_report.known_candidates

    _require_baseline_matches_plan(baseline, plan)

    ran = tuple(outcomes)
    for outcome in ran:
        outcome.validate()
    _require_sources_allocated(ran, plan)

    # The ranking piece is the authority on canonical identity; the outcomes are
    # checked against it so a discovered path cannot vanish between the two.
    canonical_ids = tuple(sorted({
        member for family in ranking.families for member in family.member_candidate_ids
    }))
    discovered = merge_leads([lead for outcome in ran for lead in outcome.leads])
    _require_discovered_accounted_for(discovered, canonical_ids)
    # What is known as of this pass: everything an earlier pass knew plus what this
    # one found, aggregated by the canonical owner so one identity stays one
    # record (2.1.12) — the set the next pass measures novelty against (2.1.10).
    known_candidates = merge_canonical_candidates(
        [*previously_known_candidates, *discovered])
    _require_sufficiency_claim_has_a_set(
        enough_non_dominated=enough_non_dominated,
        canonical_ids=canonical_ids,
        previously_known_candidates=previously_known_candidates,
    )

    metrics = update_saturation(
        previous_metrics if previous_metrics is not None else SaturationMetrics(),
        outcomes=ran,
        canonical_candidates=discovered,
        previous_candidate_ids=[c.canonical_id for c in previously_known_candidates],
        previous_family_ids=[
            family_identity_for(c) for c in previously_known_candidates
        ],
        previous_covered_atoms=[
            atom for c in previously_known_candidates for atom in c.claims_atoms
        ],
        saturated=saturated,
        saturation_reason=saturation_reason,
    )

    verdict = stop_recommendation(
        plan,
        metrics,
        budget_exhausted=_budget_exhausted(plan.budget, metrics),
        enough_non_dominated=enough_non_dominated,
        hard_constraints_eliminated_class=hard_constraints_eliminated_class,
        contract_amendment_required=contract_amendment_required,
        rationale=stop_rationale,
    )

    return make_discovery_report(
        report_id=report_id,
        discovery_plan_id=plan.discovery_plan_id,
        contract_id=plan.contract_id,
        contract_version=plan.contract_version,
        atom_ids=tuple(plan.atom_ids),
        internal_baseline_ref=baseline.baseline_id,
        sources_searched=_sources_searched(ran),
        query_families_executed=_query_families_executed(ran),
        canonical_candidate_ids=canonical_ids,
        candidate_families=tuple(ranking.families),
        escalation_queue=tuple(ranking.queue),
        saturation_metrics=metrics,
        stop_recommendation=verdict,
        known_candidates=known_candidates,
        coverage_notes=_coverage_notes(
            plan, baseline, ran,
            previous_metrics=previous_metrics,
            previously_known_candidates=previously_known_candidates,
            previous_report=previous_report,
        ),
        partial_search_notes=_partial_search_notes(ran),
        prefilter_decisions=tuple(ranking.prefilter_decisions),
        negative_findings=_negative_findings(ran, baseline),
        remaining_uncertainties=_remaining_uncertainties(baseline, ranking),
        amendment_proposals=tuple(plan.amendment_proposals),
        created_at=created_at,
        created_by=created_by,
        policy_version=ranking.policy_version,
    )


# -- fail-closed consistency laws -------------------------------------------


def _require_one_history_source(
    previous_report: Optional[DiscoveryReport],
    previous_metrics: Optional[SaturationMetrics],
    previously_known_candidates: Sequence[CanonicalCandidate],
) -> None:
    """One owner per piece of state: the artifact, or the records (canon 2.1.10).

    Combining them would let one pass's counters meet another pass's candidates —
    the arithmetic that inflated novelty in the first place — so it is refused
    rather than resolved by precedence.
    """
    if previous_report is None:
        return
    conflicting = [
        name
        for name, supplied in (
            ("previous_metrics", previous_metrics is not None),
            ("previously_known_candidates", bool(previously_known_candidates)),
        )
        if supplied
    ]
    if conflicting:
        raise QcaeValidationError(
            f"previous_report was given together with {conflicting}: the pass history has "
            "one owner (canon 2.1.10), so hand over either the previous artifact or the "
            "explicit counters and candidates it carries, never both"
        )


def _require_history_is_for_this_capability(
    previous_report: Optional[DiscoveryReport], plan: DiscoveryPlan
) -> None:
    """Canon 2.1.10: the history is this capability's past, or it is not a history.

    The artifact states the identity it measured (contract and revision), so the
    binding is checkable without carrying anything new: refusing an unverifiable
    handoff is right, accepting it silently would put another capability's known
    candidates into this pass's novelty accounting and its stop verdict.
    """
    if previous_report is None:
        return
    mismatches: List[str] = []
    if previous_report.contract_id != plan.contract_id:
        mismatches.append(
            f"it measured contract {previous_report.contract_id!r}, this pass searches "
            f"{plan.contract_id!r}"
        )
    if previous_report.contract_version != plan.contract_version:
        mismatches.append(
            f"it measured contract version {previous_report.contract_version!r}, this "
            f"pass searches the plan's {plan.contract_version!r}"
        )
    if mismatches:
        raise QcaeValidationError(
            "the handed-over pass history belongs to a different capability: "
            + "; ".join(mismatches)
            + " (canon 2.1.10: novelty is measured against what was already known for "
            "this capability, so another capability's or revision's known set would be "
            "counted as this pass's past in new_candidates/new_atoms_covered and in the "
            "stop verdict — hand over the report this capability's previous pass "
            "produced, or the counters and candidates that belong to it)"
        )


def _require_baseline_matches_plan(
    baseline: InternalBaselineRecord, plan: DiscoveryPlan
) -> None:
    """Canon 2.1.6: the baseline is this plan's internal comparison, or nothing."""
    mismatches: List[str] = []
    if baseline.contract_id != plan.contract_id:
        mismatches.append(
            f"contract {baseline.contract_id!r} is not the plan's {plan.contract_id!r}"
        )
    if baseline.contract_version != plan.contract_version:
        mismatches.append(
            f"contract version {baseline.contract_version!r} is not the plan's "
            f"{plan.contract_version!r}"
        )
    if tuple(baseline.requested_atoms) != tuple(plan.atom_ids):
        mismatches.append(
            f"atom scope {list(baseline.requested_atoms)} is not the plan's "
            f"{list(plan.atom_ids)}"
        )
    if mismatches:
        raise QcaeValidationError(
            "the internal baseline belongs to a different plan: "
            + "; ".join(mismatches)
            + " (canon 2.1.6: every external comparison has an explicit baseline "
            "for this plan; a mismatched baseline would compare against the wrong "
            "internal state)"
        )


def _require_sources_allocated(
    outcomes: Sequence[AdapterOutcome], plan: DiscoveryPlan
) -> None:
    """The source portfolio is declared before the search (canon 2.1.5/2.1.7)."""
    allocated = {allocation.source_class for allocation in plan.source_allocations}
    unallocated = sorted(
        {o.source_class for o in outcomes if o.counts_toward_saturation} - allocated,
        key=lambda source: source.value,
    )
    if unallocated:
        raise QcaeValidationError(
            "search(es) reached source class(es) the plan never allocated: "
            f"{[source.value for source in unallocated]} (canon 2.1.5/2.1.7: the plan "
            "owns the source portfolio, so an unallocated search is not reportable "
            "as this plan's work)"
        )


def _require_sufficiency_claim_has_a_set(
    *,
    enough_non_dominated: bool,
    canonical_ids: Sequence[str],
    previously_known_candidates: Sequence[CanonicalCandidate],
) -> None:
    """A sufficiency declaration must be about a set the artifact contains (2.1.9).

    ``NON_DOMINATED_SET_SUFFICIENT`` is the caller's judgement, but a judgement
    needs a subject: with no candidate from this pass and none seen by an earlier
    one, the report would recommend stopping on the strength of a set it does not
    contain. That is the one stop claim the artifact's own contents refute; every
    other stop condition is read off the plan or the counters, which cannot
    disagree with themselves. Candidates an earlier pass already saw are a real
    set, so a later pass that adds nothing may still be the pass that judges the
    accumulated set sufficient (2.1.10).
    """
    if enough_non_dominated and not canonical_ids and not previously_known_candidates:
        raise QcaeValidationError(
            "the non-dominated set is declared sufficient, but the report contains no "
            "candidate set to be sufficient: this pass found no candidate and none was "
            "known from an earlier pass (canon 2.1.9/2.7.15: a sufficiency claim must be "
            "about a set the artifact actually contains)"
        )


def _require_discovered_accounted_for(
    discovered: Sequence[CanonicalCandidate], canonical_ids: Sequence[str]
) -> None:
    """A discovered candidate the ranking never saw is a dropped piece (2.1.12)."""
    known = set(canonical_ids)
    missing = [
        f"{candidate.canonical_locator} ({candidate.canonical_id})"
        for candidate in discovered
        if candidate.canonical_id not in known
    ]
    if missing:
        raise QcaeValidationError(
            f"{len(missing)} discovered candidate(s) are absent from the ranking pass "
            f"and would be dropped from the report: {missing} (canon 2.1.12/2.7.15: "
            "every path that found a candidate survives into the artifact)"
        )


# -- derivations -------------------------------------------------------------


def _budget_exhausted(budget: DiscoveryBudget, metrics: SaturationMetrics) -> bool:
    """Only the ceilings the metrics can evidence are compared here.

    ``max_source_calls``, ``max_wall_clock_seconds`` and ``max_cost_usd`` have no
    counterpart in the counters, so exhaustion of those is never inferred: a
    caller that reached them declares the stop. Claiming a ceiling we cannot
    evidence would be worse than not claiming it (canon 2.1.9).
    """
    return (
        metrics.queries_executed >= budget.max_queries
        or metrics.results_inspected >= budget.max_results_inspected
    )


def _sources_searched(outcomes: Sequence[AdapterOutcome]) -> Tuple[SourceClass, ...]:
    """The classes actually searched, by the adapter's own definition of 'ran'."""
    return tuple(sorted(
        {o.source_class for o in outcomes if o.counts_toward_saturation},
        key=lambda source: source.value,
    ))


def _query_families_executed(outcomes: Sequence[AdapterOutcome]) -> Tuple[str, ...]:
    """Families attributable from lead lineage (canon 2.1.4/2.1.17 invariant 4)."""
    return tuple(sorted({
        lead.query_lineage.family_id
        for outcome in outcomes
        for lead in outcome.leads
        if lead.query_lineage.family_id
    }))


def _coverage_notes(
    plan: DiscoveryPlan,
    baseline: InternalBaselineRecord,
    outcomes: Sequence[AdapterOutcome],
    *,
    previous_metrics: Optional[SaturationMetrics] = None,
    previously_known_candidates: Sequence[CanonicalCandidate] = (),
    previous_report: Optional[DiscoveryReport] = None,
) -> Tuple[str, ...]:
    notes: List[str] = [
        f"internal baseline {baseline.baseline_id}: coverage basis "
        f"{baseline.coverage_basis}; classifications "
        f"{[c.value for c in baseline.classifications] or 'none'}",
    ]
    requested = tuple(plan.atom_ids)
    targets = tuple(baseline.external_target_atoms)
    searched = tuple(o for o in outcomes if o.counts_toward_saturation)
    if not targets and searched:
        notes.append(
            f"{len(searched)} external search(es) ran while the internal baseline assigns "
            "no atom to external search (canon 2.6.5/2.6.8): every requested atom is "
            "internally satisfied, so the searches were not required by the baseline. "
            "The report records both facts rather than implying the effort was needed"
        )
    if targets and len(targets) < len(requested):
        notes.append(
            f"external search narrowed to {len(targets)} of {len(requested)} requested "
            f"atom(s) by internal partial reuse (canon 2.6.8): {list(targets)}"
        )
    unattributed = [
        o.query_id for o in outcomes if o.counts_toward_saturation and not o.leads
    ]
    if unattributed:
        notes.append(
            f"{len(unattributed)} executed search(es) carried no lead lineage, so their "
            "query families are absent from query_families_executed: "
            f"{unattributed} (the executed count is disclosed rather than implied)"
        )
    if baseline.sufficient_without_discovery and any(
        o.counts_toward_saturation for o in outcomes
    ):
        notes.append(
            "the internal baseline reports sufficient_without_discovery, yet external "
            "search ran (canon 2.6.7): the report records both rather than choosing"
        )
    if _previous_knowledge_is_missing(previous_metrics, previously_known_candidates):
        notes.append(
            "counters carried forward from a previous pass without the candidates they "
            "measured, so this pass's novelty is counted as if nothing were known before "
            "and new_candidates/new_specifications/new_atoms_covered overstate it (canon "
            "2.1.10: the terminal artifact carries the metrics, not the candidate "
            "records, so pass the previously_known_candidates alongside them)"
        )
    if _history_is_a_recut_search(previous_report, plan):
        notes.append(
            f"pass history {previous_report.report_id} was measured for a re-cut plan "
            f"scope: plan {previous_report.discovery_plan_id!r} over "
            f"{list(previous_report.atom_ids)} vs this pass's "
            f"{plan.discovery_plan_id!r} over {list(plan.atom_ids)} — the carrier is "
            "this capability's accumulated knowledge, so novelty stays measured "
            "against it (canon 2.1.10) and the scope change is recorded rather than "
            "left to be inferred from two reports"
        )
    return tuple(notes)


def _history_is_a_recut_search(
    previous_report: Optional[DiscoveryReport], plan: DiscoveryPlan
) -> bool:
    """Is this history the same capability searched over a different plan?

    A plan is a search document, not the capability: it is re-cut between passes
    (amended contracts, refocused scope), and the counters read candidate
    identity, family and claimed atoms — all the capability's. So a differing
    plan id or atom scope is disclosed rather than refused; refusing it would
    refuse a verifiable history. A differing contract or revision is a different
    comparison and is refused by ``_require_history_is_for_this_capability``.
    """
    if previous_report is None:
        return False
    return (
        previous_report.discovery_plan_id != plan.discovery_plan_id
        or tuple(previous_report.atom_ids) != tuple(plan.atom_ids)
    )


def _previous_knowledge_is_missing(
    previous_metrics: Optional[SaturationMetrics],
    previously_known_candidates: Sequence[CanonicalCandidate],
) -> bool:
    """Was a previous pass carried by its counters alone?

    Only a real loss is disclosed: counters recording no candidate, atom or
    specification carry no knowledge to measure against, so a first pass with an
    empty history stays quiet. This is disclosed rather than refused because the
    report is what a caller has to hand over — its counters travel, its candidate
    records do not — so the metrics-only handoff is reachable by following the
    artifact rather than by being careless.
    """
    if previous_metrics is None or previously_known_candidates:
        return False
    return bool(
        previous_metrics.new_candidates
        or previous_metrics.new_atoms_covered
        or previous_metrics.new_specifications
    )


def _partial_search_notes(outcomes: Sequence[AdapterOutcome]) -> Tuple[str, ...]:
    """Partial searches stay labelled partial (canon 2.2.13).

    What counts as partial is the port's own finding (``exhaustive``), not the
    status label alone: a search that ran and qualified its completeness is
    partial whether its status reads PARTIAL_RESULTS or reads OK because it
    returned results from pages it did not finish. Its own completeness note is
    carried, never summarized. A failure is not a partial search — it is a
    negative finding.
    """
    return tuple(
        f"{o.source_class.value} {o.query_id}: {o.completeness_note}"
        for o in outcomes
        if o.counts_toward_saturation
        and not o.exhaustive
        and o.completeness_note.strip()
    )


def _negative_findings(
    outcomes: Sequence[AdapterOutcome], baseline: InternalBaselineRecord
) -> Tuple[str, ...]:
    """Completed-empty and failed searches, kept distinct (canon 2.1.13/2.2.15)."""
    findings: List[str] = []
    for outcome in outcomes:
        if outcome.status == AdapterStatus.NO_RESULTS:
            findings.append(
                f"{outcome.source_class.value} {outcome.query_id}: NO_RESULTS — a "
                "completed empty search, which is not a failure and not evidence of "
                "absence (canon 2.1.13/2.2.15)"
            )
        elif outcome.status in FAILURE_STATUSES:
            findings.append(
                f"{outcome.source_class.value} {outcome.query_id}: {outcome.status.value}"
                + (f" — {outcome.message}" if outcome.message else "")
            )
    findings.extend(
        f"prior external rejection on record: {ref}"
        for ref in baseline.prior_rejection_refs
    )
    return tuple(findings)


def _remaining_uncertainties(
    baseline: InternalBaselineRecord, ranking: RankingResult
) -> Tuple[str, ...]:
    """What the artifact does not settle, stated rather than implied."""
    uncertainties: List[str] = []
    if baseline.external_target_atoms:
        uncertainties.append(
            "atoms not resolved by internal knowledge and assigned to external search: "
            f"{list(baseline.external_target_atoms)}"
        )
    if baseline.missing_atoms:
        uncertainties.append(
            "atoms with no internal implementation found: "
            f"{list(baseline.missing_atoms)}"
        )
    if baseline.requires_revalidation:
        uncertainties.append(
            "evidence requires revalidation before reuse: "
            f"{list(baseline.stale_evidence_refs)}"
        )
    if baseline.revision_change_refs:
        uncertainties.append(
            "candidate revisions changed since retrieval (ADR-0007): "
            f"{list(baseline.revision_change_refs)}"
        )
    rejected = tuple(
        entry.candidate_id
        for entry in ranking.queue
        if entry.prefilter_decision == PrefilterDecision.REJECT
    )
    if rejected:
        uncertainties.append(
            f"candidate(s) parked by hard prefilter, still uninvestigated: {list(rejected)}"
        )
    return tuple(uncertainties)
