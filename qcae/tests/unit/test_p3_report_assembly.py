"""P3 — the assembled terminal artifact (canon 2.7.15, 2.1.6, 2.2.13).

These tests drive the assembler the way a caller drives it: a plan, an internal
baseline record, real adapter outcomes and a ranking pass, assembled into the
``DiscoveryReport`` Block 3 receives. They assert the report is *consistent with
the pieces it came from* rather than merely constructible.
"""

from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

import qcae.discovery.reporting as reporting
from qcae.core.discovery.lead import (
    FAILURE_STATUSES,
    CandidateKind,
    QueryLineage,
)
from qcae.core.discovery.plan import (
    ContractAmendmentProposal,
    HardPrefilter,
)
from qcae.core.discovery.report import PrefilterDecision
from qcae.core.discovery.vocabulary import SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.discovery import (
    AdapterOutcome,
    AdapterStatus,
    make_discovery_query,
)
from qcae.core.ports.discovery import (
    ExecutionStatus,
    execution_record_for,
)
from qcae.core.vocabulary import EvidenceClass
from qcae.discovery.planning.canonical import merge_leads
from qcae.discovery.planning.prefilter import apply_hard_prefilter
from qcae.discovery.planning.ranking import rank_candidates
from qcae.discovery.reporting import assemble_discovery_report
from qcae.tests.unit.test_p3_internal_baseline import (
    ATOM_A,
    ATOM_B,
    CAP,
    FakeRegistryQuery,
    baseline as build_baseline,
    plan as baseline_plan,
)
from qcae.tests.unit.test_p3_ranking import (
    lead,
    make_discovery_plan,
    plan_kwargs,
    policy,
)

CREATED_AT = "2026-09-21T13:00:00Z"
CREATED_BY = "qcae-discovery-run"

# Execution-ordinal ledger for the fixture runner: repeated executions of one
# planned query bind as -exec2, -exec3, ... The autouse fixture gives every
# test a fresh ledger so numbering stays deterministic per test.
_EXECUTION_ORDINALS: dict = {}


@pytest.fixture(autouse=True)
def _fresh_execution_ordinals():
    _EXECUTION_ORDINALS.clear()
    yield
    _EXECUTION_ORDINALS.clear()


def _baseline(**overrides):
    """A real baseline record from the baseline service, not a hand-built one."""
    atom_ids = overrides.pop("atom_ids", [ATOM_A, ATOM_B])
    evidence = overrides.pop(
        "evidence", {atom_id: ["cand-internal-1"] for atom_id in atom_ids})
    registry = FakeRegistryQuery(
        categories=overrides.pop("categories", ["CAPABILITY_ACTIVE"]),
        atom_ids=atom_ids,
        candidate_refs=overrides.pop("candidate_refs", ["cand-internal-1"]),
        detail=overrides.pop("detail", None),
        reuse=overrides.pop("reuse", None),
        evidence=evidence,
    )
    return build_baseline(registry, **overrides)


def _narrow_plan():
    """The same capability and contract version, searched over one atom instead of two.

    A plan re-cut for the same capability: the scope changed, the identity did not.
    The portfolio shrinks to the classes the remaining family queries, rebalanced.
    """
    wide = baseline_plan()
    queried = {SourceClass.INTERNAL_REGISTRY_CODE, SourceClass.GITHUB_REPOSITORY_CODE}
    return replace(
        wide,
        atom_ids=(ATOM_A,),
        search_hypotheses=(wide.search_hypotheses[0],),
        query_families=(wide.query_families[0],),
        source_allocations=tuple(
            replace(allocation, budget_share=0.5)
            for allocation in wide.source_allocations
            if allocation.source_class in queried),
    )


def _slug(term: str) -> str:
    """Query ids are stable identifiers; terms slugify into them."""
    return term.strip().replace(" ", "-")


def _planned_query_id(source_class, term="causal ordering", plan=None):
    """A real planned query identity: the plan derives them from its families."""
    plan = plan or baseline_plan()
    for family in plan.query_families:
        if source_class in family.source_classes:
            return f"{family.family_id}:{_slug(family.terms[0])}"
    return f"{plan.query_families[0].family_id}:{_slug(term)}"


def _outcome(query_id, *, source_class=SourceClass.GITHUB_REPOSITORY_CODE,
             adapter_id="adapter-github", results=1, leads=(),
             status=AdapterStatus.OK, completeness_note="", message="",
             plan=None, ordinal=None):
    """An outcome as a caller would have it: the record an adapter returned,
    bound to the typed execution record of the planned query that produced it
    (P3-R4: every outcome binds to exactly one executed query).

    The execution record derives from the given plan the same way a real
    runner derives it: query identity/family/atom/semantics/concrete query
    from the plan's own hypothesis -> family -> query lineage. Repeated
    executions of one planned query carry an ordinal suffix (``-exec2``,
    ``-exec3``, ...); ``ordinal=False`` forces the bare base id (used by the
    single-use refusal tests, which bind one record twice on purpose).
    """
    if not message and status != AdapterStatus.OK:
        # The port requires a typed message whenever a search did not simply
        # succeed, so a caller's record always carries one.
        message = f"typed {status.value} from {adapter_id}"

    plan = plan or baseline_plan()
    family = next(
        (f for f in plan.query_families if source_class in f.source_classes), None)
    if family is None:
        # No planned family serves this source class: the record cannot be
        # built (a plan never authorized it). Return the unbound outcome —
        # the assembler's unallocated-source law is what refuses it.
        return AdapterOutcome(
            adapter_id=adapter_id,
            source_class=source_class,
            query_id=query_id,
            status=status,
            leads=tuple(leads),
            pages_inspected=1,
            results_inspected=results,
            completeness_note=completeness_note,
            message=message,
        )
    family_id = family.family_id
    term = family.terms[0]
    base_query_id = f"{family_id}:{_slug(term)}"
    if ordinal is None:
        key = (plan.discovery_plan_id, base_query_id)
        ordinal = _EXECUTION_ORDINALS.get(key, 0) + 1
        _EXECUTION_ORDINALS[key] = ordinal
    bound_query_id = (
        base_query_id if not ordinal else f"{base_query_id}-exec{ordinal}")
    hypothesis = next(
        h for h in plan.search_hypotheses if h.hypothesis_id == family.hypothesis_ids[0]
    )
    atom_id = (leads[0].query_lineage.atom_id if leads else hypothesis.atom_ids[0])
    allocation = next(
        a for a in plan.source_allocations if a.source_class == source_class
    )
    record = execution_record_for(
        make_discovery_query(
            query_id=bound_query_id,
            family_id=family_id,
            atom_id=atom_id,
            semantic_concept=family.terms[0] if family.terms else family.family_id,
            concrete_query=term,
            source_class=source_class,
            max_results=20,
            max_tier=allocation.max_tier,
        ),
        plan,
        adapter_id=adapter_id,
        status=(ExecutionStatus.FAILED if status in FAILURE_STATUSES
                else ExecutionStatus.EXECUTED),
        executed_at="2026-09-21T13:00:00Z",
    )
    outcome = AdapterOutcome(
        adapter_id=adapter_id,
        source_class=source_class,
        query_id=bound_query_id,
        status=status,
        leads=tuple(leads),
        pages_inspected=1,
        results_inspected=results,
        completeness_note=completeness_note,
        message=message,
    )
    return outcome.bind_execution_record(record)


def _run(*, leads=(), outcomes=(), plan=None, baseline=None, candidates=None,
         prefilter_decisions=(), **overrides):
    """The caller's flow: merge leads, rank them, assemble the report."""
    plan = baseline_plan() if plan is None else plan
    baseline = _baseline() if baseline is None else baseline
    candidates = merge_leads(leads) if candidates is None else candidates
    ranking = rank_candidates(
        candidates=candidates, plan=plan, policy=policy(),
        prefilter_decisions=tuple(prefilter_decisions),
    )
    kwargs = dict(
        report_id="report-001",
        plan=plan,
        baseline=baseline,
        ranking=ranking,
        outcomes=tuple(outcomes),
        created_at=CREATED_AT,
        created_by=CREATED_BY,
    )
    kwargs.update(overrides)
    return assemble_discovery_report(**kwargs), candidates, ranking


def _two_adapter_run(plan=None):
    """One project found by two adapters, plus a paper from a third.

    Each lead sits in the outcome its own adapter returned: an outcome's leads
    must come from the adapters that responded (port law), so a multi-source hit
    is two outcomes that merge, not one outcome carrying both. ``plan`` threads
    through so the same run can be executed under a re-cut or foreign plan.
    """
    github = lead("lead-gh-1", "github:owner/lib", claims=(ATOM_A,), atoms=(ATOM_A,))
    registry = lead("lead-reg-1", "github:owner/Lib.git",
                    source_class=SourceClass.INTERNAL_REGISTRY_CODE,
                    adapter_id="adapter-registry",
                    claims=(ATOM_A, ATOM_B), atoms=(ATOM_A, ATOM_B))
    paper = lead("lead-paper-1", "arxiv:2401.00001", kind=CandidateKind.PAPER,
                 source_class=SourceClass.RESEARCH_LITERATURE, adapter_id="adapter-arxiv",
                 claims=(ATOM_B,), atoms=(ATOM_B,), license_claim="",
                 query_lineage=QueryLineage(
                     atom_id=ATOM_B, semantic_concept="ordering specification",
                     family_id="fam-spec", concrete_query="ordering specification",
                     source_class=SourceClass.RESEARCH_LITERATURE,
                     adapter_id="adapter-arxiv"))
    outcomes = [
        _outcome(_planned_query_id(SourceClass.GITHUB_REPOSITORY_CODE, plan=plan),
                 leads=(github,), plan=plan),
        _outcome(_planned_query_id(SourceClass.INTERNAL_REGISTRY_CODE, plan=plan),
                 source_class=SourceClass.INTERNAL_REGISTRY_CODE,
                 adapter_id="adapter-registry", leads=(registry,), plan=plan),
        _outcome(_planned_query_id(SourceClass.RESEARCH_LITERATURE, plan=plan),
                 source_class=SourceClass.RESEARCH_LITERATURE,
                 adapter_id="adapter-arxiv", leads=(paper,), plan=plan),
    ]
    return [github, registry, paper], outcomes


class TestNoClaimOutrunsItsEvidence:
    """A claim in the artifact must not survive beside evidence that refutes it.

    Each case here is a state the real pieces reach: the report's own contents
    contradict a note, a status, or a stop recommendation. The phase's rule is
    that such a claim is refused or recorded, never left standing silently.
    """

    def test_external_search_though_the_baseline_assigned_no_atom_is_disclosed(self) -> None:
        """Searches ran for atoms the baseline says are already held internally.

        ``external_target_atoms`` empty means every requested atom is internally
        satisfied, so canon 2.6.5/2.6.8 makes external search on them wasted work.
        The report carries both facts, and says so.
        """
        leads, outcomes = _two_adapter_run()
        report, _, _ = _run(
            leads=leads, outcomes=outcomes,
            baseline=_baseline(evidence={ATOM_A: ["c-a"], ATOM_B: ["c-b"]}),
        )
        assert report.candidate_families  # the searches did return candidates
        assert any("assigns no atom to external search" in note
                   for note in report.coverage_notes)

    def test_a_fully_satisfied_baseline_with_no_search_records_no_contradiction(self) -> None:
        """The disclosure above is about a contradiction, not noise."""
        report, _, _ = _run(
            leads=(), outcomes=(),
            baseline=_baseline(evidence={ATOM_A: ["c-a"], ATOM_B: ["c-b"]}),
        )
        assert not any("assigns no atom to external search" in note
                       for note in report.coverage_notes)

    def test_a_completed_search_that_is_not_exhaustive_is_recorded_partial(self) -> None:
        """Canon 2.2.13: a partial search is never represented as exhaustive.

        The port's own standing is what makes a search partial: ``exhaustive``
        holds only for a completed search carrying no qualification, so a search
        that returned results *and* qualified its completeness is partial even
        though its status reads OK.
        """
        leads, _ = _two_adapter_run()
        qualified = _outcome(
            _planned_query_id(SourceClass.GITHUB_REPOSITORY_CODE), leads=(leads[0],),
            completeness_note="stopped after page 3 of 10")
        assert qualified.status is AdapterStatus.OK
        assert qualified.exhaustive is False

        report, _, _ = _run(leads=(leads[0],), outcomes=(qualified,))
        assert any("stopped after page 3 of 10" in note
                   for note in report.partial_search_notes)

    def test_an_exhaustive_search_records_no_partial_note(self) -> None:
        leads, outcomes = _two_adapter_run()
        report, _, _ = _run(leads=leads, outcomes=outcomes)
        assert report.partial_search_notes == ()

    def test_a_stop_on_a_set_the_report_does_not_contain_is_refused(self) -> None:
        """A sufficiency declaration the artifact's own contents refute.

        With no candidate from this pass and none known from an earlier one,
        there is no non-dominated set to be sufficient: the report would
        recommend stopping on the strength of a set it does not contain.
        """
        with pytest.raises(QcaeValidationError, match="no candidate set"):
            _run(leads=(), outcomes=(), baseline=_baseline(),
                 enough_non_dominated=True)

    def test_a_counter_history_without_the_knowledge_it_measured_is_disclosed(self) -> None:
        """The natural multi-pass handoff, and the one that inflates novelty.

        A previous pass's counters are what the artifact carries
        (``report.saturation_metrics``), so feeding them into the next pass is
        the obvious handoff; the candidate records they were measured against are
        not in that artifact. Carrying the counters without the candidates makes
        the executed count cumulative while novelty is counted as if this were
        the first pass, so the report publishes an inflated marginal novelty rate
        — the very number the stop law reads (canon 2.1.10).
        """
        leads, outcomes = _two_adapter_run()
        first, candidates, _r = _run(leads=leads, outcomes=outcomes)

        honest, _c1, _r1 = _run(
            leads=leads, outcomes=outcomes,
            previous_metrics=first.saturation_metrics,
            previously_known_candidates=candidates)
        inflated, _c2, _r2 = _run(
            leads=leads, outcomes=outcomes,
            previous_metrics=first.saturation_metrics)

        # The same repeat pass: honest novelty is zero, the half-carried one
        # re-counts what the previous pass already covered.
        assert (inflated.saturation_metrics.new_atoms_covered
                > honest.saturation_metrics.new_atoms_covered)
        assert (inflated.saturation_metrics.marginal_novelty_rate
                > honest.saturation_metrics.marginal_novelty_rate)
        assert any("previously_known_candidates" in note
                   for note in inflated.coverage_notes)
        assert not any("previously_known_candidates" in note
                       for note in honest.coverage_notes)

    def test_a_family_deferral_the_report_does_not_contain_is_refused(self) -> None:
        """Already law-guarded by the artifact's own validation, not by this module.

        A ranking row naming a family outside ``candidate_families`` would leave
        the deferrals disagreeing with the reported families. No ranking pass
        produces that, and the artifact refuses it rather than carrying it, so
        this item was never an open contradiction.
        """
        leads, outcomes = _two_adapter_run()
        _, _, ranking = _run(leads=leads, outcomes=outcomes)
        assert ranking.queue  # the rows exist to be contradicted
        tampered = replace(ranking, queue=tuple(
            replace(entry, family_id="fam-not-in-families") for entry in ranking.queue
        ))
        with pytest.raises(QcaeValidationError, match="unknown family"):
            assemble_discovery_report(
                report_id="report-001", plan=baseline_plan(), baseline=_baseline(),
                ranking=tampered, outcomes=tuple(outcomes),
                created_at=CREATED_AT, created_by=CREATED_BY,
            )

    def test_a_stop_on_candidates_known_from_an_earlier_pass_is_allowed(self) -> None:
        """The guard covers the declaration, not the multi-pass flow.

        A later pass that adds nothing can still be the pass that judges the
        accumulated set sufficient, so previously known candidates count.
        """
        known = merge_leads(_two_adapter_run()[0])
        report, _, _ = _run(leads=(), outcomes=(), baseline=_baseline(),
                           enough_non_dominated=True,
                           previously_known_candidates=known)
        assert report.stop_recommendation.state.value == "STOP"


class TestTheArtifactIsItsOwnHandoff:
    """A pass assembled from the previous report must count as honestly as a caller
    who hand-supplies the previous counters *and* the records they measured.

    Canon 2.7.15 lists the canonical candidate set among the artifact's contents and
    canon 2.1.10 measures novelty against what was already known, so the artifact is
    where the next pass's history has to come from — otherwise the natural durable
    handoff publishes an inflated novelty rate to the stop law.
    """

    def test_handing_off_from_the_artifact_matches_hand_supplied_history(self) -> None:
        leads, outcomes = _two_adapter_run()
        first, candidates, _r = _run(leads=leads, outcomes=outcomes)

        control, _c1, _r1 = _run(
            leads=leads, outcomes=outcomes,
            previous_metrics=first.saturation_metrics,
            previously_known_candidates=candidates)
        handed_off, _c2, _r2 = _run(leads=leads, outcomes=outcomes,
                                    previous_report=first)

        assert handed_off.saturation_metrics == control.saturation_metrics
        assert (handed_off.stop_recommendation.state
                == control.stop_recommendation.state)
        assert (handed_off.stop_recommendation.satisfied_conditions
                == control.stop_recommendation.satisfied_conditions)
        # The honest number, not the inflated one: a repeat pass discovers nothing.
        assert (handed_off.saturation_metrics.new_candidates
                == first.saturation_metrics.new_candidates)
        assert (handed_off.saturation_metrics.new_atoms_covered
                == first.saturation_metrics.new_atoms_covered)
        assert (handed_off.saturation_metrics.marginal_novelty_rate
                < first.saturation_metrics.marginal_novelty_rate)

    def test_the_loop_stays_honest_when_only_the_artifact_travels(self) -> None:
        """Three passes, each handed over as the artifact alone.

        Accumulating the history in the caller is the bookkeeping a durable loop
        cannot do (the artifact carries ids, not records), so the artifact itself
        has to know what was already known — otherwise pass three re-counts what
        pass one found.
        """
        leads, outcomes = _two_adapter_run()
        first, _c, _r = _run(leads=leads, outcomes=outcomes)
        second, _c2, _r2 = _run(leads=leads, outcomes=outcomes, previous_report=first)
        third, _c3, _r3 = _run(leads=leads, outcomes=outcomes, previous_report=second)

        assert (second.saturation_metrics.new_candidates
                == first.saturation_metrics.new_candidates)
        assert (third.saturation_metrics.new_candidates
                == second.saturation_metrics.new_candidates)
        assert (third.saturation_metrics.new_atoms_covered
                == first.saturation_metrics.new_atoms_covered)
        assert (third.saturation_metrics.marginal_novelty_rate
                < second.saturation_metrics.marginal_novelty_rate)
        # The known set accumulates identities, not duplicates of them.
        assert (second.known_candidates_ids == third.known_candidates_ids
                == first.known_candidates_ids)

    def test_the_artifact_carries_the_known_set_it_counted(self) -> None:
        leads, outcomes = _two_adapter_run()
        report, candidates, _r = _run(leads=leads, outcomes=outcomes)
        assert report.known_candidates == tuple(candidates)
        assert set(report.canonical_candidate_ids) <= {
            c.canonical_id for c in report.known_candidates}

    def test_the_artifact_carries_what_an_earlier_pass_already_knew(self) -> None:
        """A later pass's report knows both its own discoveries and the earlier ones."""
        leads, outcomes = _two_adapter_run()
        first, candidates, _r = _run(leads=leads, outcomes=outcomes)
        later, _c, _r2 = _run(leads=leads, outcomes=outcomes, previous_report=first)
        assert set(later.known_candidates_ids) == set(first.known_candidates_ids)
        assert later.known_candidates == first.known_candidates
        assert set(first.known_candidates_ids) == {c.canonical_id for c in candidates}

    def test_history_from_another_capability_is_refused(self) -> None:
        """A handed-over report belongs to the capability it measured (2.1.10).

        Nothing bound the history to its identity, so a report assembled for
        another contract could be handed in as this pass's past: its known
        candidates entered this pass's novelty accounting, and a search for one
        capability would be judged against knowledge about a different one —
        including at the stop verdict. Fail closed instead.
        """
        leads, outcomes = _two_adapter_run()
        elsewhere = replace(baseline_plan(), contract_id="CAP-OTHER-001")
        foreign_leads, foreign_outcomes = _two_adapter_run(plan=elsewhere)
        foreign, _c, _r = _run(
            leads=foreign_leads, outcomes=foreign_outcomes, plan=elsewhere,
            baseline=_baseline(plan=elsewhere, atom_ids=[ATOM_A, ATOM_B]))

        with pytest.raises(QcaeValidationError, match="CAP-OTHER-001"):
            _run(leads=leads, outcomes=outcomes, previous_report=foreign)

    def test_history_from_another_contract_revision_is_refused(self) -> None:
        """A different contract version is a different comparison, as for the baseline."""
        leads, outcomes = _two_adapter_run()
        first, _c, _r = _run(leads=leads, outcomes=outcomes)
        older = replace(first, contract_version=first.contract_version + 1)
        with pytest.raises(QcaeValidationError, match="contract version"):
            _run(leads=leads, outcomes=outcomes, previous_report=older)

    def test_history_survives_the_json_round_trip_the_durable_loop_uses(self) -> None:
        """The binding reads the artifact's stated identity, so it must survive it."""
        leads, outcomes = _two_adapter_run()
        first, _c, _r = _run(leads=leads, outcomes=outcomes)
        reloaded = type(first).from_dict(json.loads(json.dumps(first.to_dict())))
        handed_off, _c2, _r2 = _run(leads=leads, outcomes=outcomes,
                                    previous_report=reloaded)
        assert reloaded.contract_id == first.contract_id
        assert (handed_off.saturation_metrics.new_candidates
                == first.saturation_metrics.new_candidates)

    def test_history_from_another_plan_for_the_same_capability_is_accepted(self) -> None:
        """A plan re-cut between passes is still this capability's history.

        The accounting reads candidate identity, family and claimed atoms — all
        the capability's — so a plan id the counters never touch is not an
        identity to bind on; refusing it would refuse a verifiable history.
        """
        leads, outcomes = _two_adapter_run()
        first, _c, _r = _run(leads=leads, outcomes=outcomes)
        recut = replace(baseline_plan(), discovery_plan_id="plan-002")
        recut_leads, recut_outcomes = _two_adapter_run(plan=recut)
        handed_off, _c2, _r2 = _run(
            leads=recut_leads, outcomes=recut_outcomes, plan=recut,
            baseline=_baseline(plan=recut, atom_ids=[ATOM_A, ATOM_B]),
            previous_report=first)
        assert handed_off.discovery_plan_id == "plan-002"
        assert (handed_off.saturation_metrics.new_candidates
                == first.saturation_metrics.new_candidates)
        # Accepted, and said out loud: the plan id changed, the capability did not.
        assert any("re-cut plan scope" in note and "plan-001" in note
                   for note in handed_off.coverage_notes)

    def test_history_from_a_narrower_scope_is_accepted_and_stays_honest(self) -> None:
        """The same capability searched over fewer atoms keeps honest counters.

        A narrower plan is a re-cut search, not another capability: the atoms the
        previous pass already covered stay known, so a repeat hit still earns no
        new atom, and the counters match what a caller who supplied the previous
        metrics and candidates by hand would get.
        """
        leads, outcomes = _two_adapter_run()
        first, _c, _r = _run(leads=leads, outcomes=outcomes)
        narrow = _narrow_plan()
        narrow_baseline = _baseline(plan=narrow, atom_ids=[ATOM_A],
                                    evidence={ATOM_A: ["cand-internal-1"]})
        # The narrowed portfolio no longer searches the literature class, so the
        # re-cut pass's own outcomes are the two the remaining family queries.
        narrow_leads, narrow_outcomes = leads[:2], outcomes[:2]

        handed_off, _c2, _r2 = _run(
            leads=narrow_leads, outcomes=narrow_outcomes, plan=narrow,
            baseline=narrow_baseline, previous_report=first)
        control, _c3, _r3 = _run(
            leads=narrow_leads, outcomes=narrow_outcomes, plan=narrow,
            baseline=narrow_baseline,
            previous_metrics=first.saturation_metrics,
            previously_known_candidates=first.known_candidates)

        assert handed_off.atom_ids == (ATOM_A,)  # the report states its own scope
        assert handed_off.saturation_metrics == control.saturation_metrics
        # Nothing is re-discovered: the atoms the wider pass already covered stay
        # known, and the counter is the capability's, not the narrower plan's.
        assert (handed_off.saturation_metrics.new_atoms_covered
                == first.saturation_metrics.new_atoms_covered)
        # A narrower scope is disclosed as such, both sides of the change named.
        assert any("re-cut plan scope" in note and ATOM_B in note
                   for note in handed_off.coverage_notes)

    def test_history_from_a_wider_scope_is_accepted_and_stays_honest(self) -> None:
        """The other direction: a history searched fewer atoms than this pass.

        The atom the history never saw is genuinely new and must be counted as
        such, while the atom it did cover stays known — a wider scope is a re-cut
        search, not a reason to re-count what was already held.
        """
        leads, outcomes = _two_adapter_run()
        narrow = _narrow_plan()
        narrow_baseline = _baseline(plan=narrow, atom_ids=[ATOM_A],
                                    evidence={ATOM_A: ["cand-internal-1"]})
        first, _c, _r = _run(leads=leads[:1], outcomes=outcomes[:1],
                             plan=narrow, baseline=narrow_baseline)
        assert first.saturation_metrics.new_atoms_covered == 1  # atom A only

        wider, _c2, _r2 = _run(leads=leads, outcomes=outcomes,
                               previous_report=first)
        # B is covered for the first time here; A is not re-credited.
        assert wider.saturation_metrics.new_atoms_covered == 2
        assert any("re-cut plan scope" in note and ATOM_B in note
                   for note in wider.coverage_notes)

    def test_mixing_the_artifact_with_explicit_history_is_refused(self) -> None:
        """One owner for the pass history, so the two cannot be combined. """
        leads, outcomes = _two_adapter_run()
        first, candidates, _r = _run(leads=leads, outcomes=outcomes)
        with pytest.raises(QcaeValidationError, match="previous_report"):
            _run(leads=leads, outcomes=outcomes, previous_report=first,
                 previous_metrics=first.saturation_metrics)
        with pytest.raises(QcaeValidationError, match="previous_report"):
            _run(leads=leads, outcomes=outcomes, previous_report=first,
                 previously_known_candidates=candidates)

    def test_a_report_whose_known_set_omits_a_reported_candidate_is_refused(self) -> None:
        """The artifact's own validation owns that law, not only the assembler."""
        leads, outcomes = _two_adapter_run()
        report, _c, _r = _run(leads=leads, outcomes=outcomes)
        assert report.known_candidates
        with pytest.raises(QcaeValidationError, match="known_candidates"):
            replace(report, known_candidates=()).validate()

    def test_the_disclosure_still_fires_when_only_the_counters_are_carried(self) -> None:
        """The note stays as a belt-and-braces signal beside the working handoff."""
        leads, outcomes = _two_adapter_run()
        first, _c, _r = _run(leads=leads, outcomes=outcomes)
        partial_handoff, _c2, _r2 = _run(
            leads=leads, outcomes=outcomes, previous_metrics=first.saturation_metrics)
        assert any("previously_known_candidates" in note
                   for note in partial_handoff.coverage_notes)
        handed_off, _c3, _r3 = _run(leads=leads, outcomes=outcomes,
                                    previous_report=first)
        assert not any("previously_known_candidates" in note
                       for note in handed_off.coverage_notes)


class TestAssembledReportMatchesItsPieces:
    def test_report_is_consistent_with_the_inputs_it_came_from(self) -> None:
        leads, outcomes = _two_adapter_run()
        report, candidates, ranking = _run(leads=leads, outcomes=outcomes)

        # plan / baseline identity
        assert report.discovery_plan_id == baseline_plan().discovery_plan_id
        assert report.contract_id == CAP
        assert report.atom_ids == baseline_plan().atom_ids
        assert report.internal_baseline_ref == _baseline().baseline_id

        # the ranking piece is carried through, not re-derived
        assert report.candidate_families == ranking.families
        assert report.escalation_queue == ranking.queue
        assert report.prefilter_decisions == ranking.prefilter_decisions
        assert report.policy_version == ranking.policy_version

        # the canonical set is exactly what the families cover
        assert set(report.canonical_candidate_ids) == {
            member for family in ranking.families for member in family.member_candidate_ids
        }
        assert set(report.canonical_candidate_ids) == {
            candidate.canonical_id for candidate in candidates
        }
        for entry in report.escalation_queue:
            assert entry.candidate_id in set(report.canonical_candidate_ids)

        # and the report satisfies its own laws
        report.validate()

    def test_queue_keeps_waves_next_actions_and_family_deferrals(self) -> None:
        leads = [
            lead("lead-rep", "github:owner/lib", claims=(ATOM_A, ATOM_B),
                 atoms=(ATOM_A, ATOM_B), novelty_family="family-ordering"),
            lead("lead-fam", "github:owner/other", claims=(ATOM_B,), atoms=(ATOM_B,),
                 novelty_family="family-ordering",
                 query_lineage=QueryLineage(
                     atom_id=ATOM_A, semantic_concept="causal ordering",
                     family_id="fam-behavioral", concrete_query="causal ordering",
                     source_class=SourceClass.GITHUB_REPOSITORY_CODE,
                     adapter_id="adapter-github")),
        ]
        outcomes = [
            _outcome(_planned_query_id(SourceClass.GITHUB_REPOSITORY_CODE),
                     results=len(leads), leads=leads),
        ]
        report, _candidates, _ranking = _run(leads=leads, outcomes=outcomes)

        deferred = [e for e in report.escalation_queue
                    if e.next_action.value == "DEFER_PENDING_FAMILY"]
        assert len(deferred) == 1
        assert deferred[0].deferred_pending
        assert deferred[0].wave == 3
        assert {e.wave for e in report.escalation_queue} <= {1, 2, 3}

    def test_rejected_candidate_is_parked_and_carries_its_decision(self) -> None:
        leads = [lead("lead-gh-1", "github:owner/copyleft")]
        candidates = merge_leads(leads)
        strict = HardPrefilter(
            prefilter_id="pf-license",
            rule="explicit incompatible license",
            min_evidence_class=EvidenceClass.E2_SOURCE,
        )
        decision = apply_hard_prefilter(
            strict, candidates[0], PrefilterDecision.REJECT, EvidenceClass.E2_SOURCE,
            "LICENSE file is GPL-3.0 and the contract forbids copyleft",
        )
        report, _candidates, _ranking = _run(
            leads=leads, outcomes=[_outcome("q-1", results=1, leads=leads)],
            prefilter_decisions=(decision,),
        )
        assert report.rejected_candidate_ids == (candidates[0].canonical_id,)
        entry = report.escalation_queue[0]
        assert entry.next_action.value == "REJECT_HARD_CONSTRAINT"
        assert entry.prefilter_decision == PrefilterDecision.REJECT
        assert entry.rationale == decision.rationale
        assert decision in report.prefilter_decisions

    def test_every_discovered_candidate_survives_into_the_report(self) -> None:
        leads, outcomes = _two_adapter_run()
        report, candidates, _ranking = _run(leads=leads, outcomes=outcomes)
        for candidate in candidates:
            assert candidate.canonical_id in report.canonical_candidate_ids


class TestAssemblyFailsClosed:
    def test_a_candidate_the_ranking_never_saw_fails_closed(self) -> None:
        ranked = [lead("lead-gh-1", "github:owner/lib")]
        unranked = lead("lead-lost", "github:owner/never-ranked")
        outcomes = [_outcome("q-1", results=2, leads=ranked + [unranked])]
        with pytest.raises(QcaeValidationError) as excinfo:
            _run(leads=ranked, outcomes=outcomes)
        assert "never-ranked" in str(excinfo.value) or "not accounted" in str(excinfo.value)

    def test_baseline_from_another_plan_fails_closed(self) -> None:
        baseline = _baseline()
        leads = [lead("lead-gh-1", "github:owner/lib")]
        outcomes = [_outcome("q-1", results=1, leads=leads)]

        with pytest.raises(QcaeValidationError, match="baseline"):
            _run(leads=leads, outcomes=outcomes,
                 baseline=replace(baseline, contract_id="CAP-OTHER-001"))
        with pytest.raises(QcaeValidationError, match="baseline"):
            _run(leads=leads, outcomes=outcomes,
                 baseline=replace(baseline, requested_atoms=("atom-elsewhere",)))

    def test_source_outside_the_plan_allocation_fails_closed(self) -> None:
        leads = [lead("lead-gh-1", "github:owner/lib")]
        outcomes = [
            _outcome("q-1", leads=leads),
            # A completed empty search still counts as the class having been
            # searched, so an unallocated class cannot hide behind no results.
            _outcome("q-2", source_class=SourceClass.CURATED_SENSOR,
                     adapter_id="adapter-curated", results=0,
                     status=AdapterStatus.NO_RESULTS),
        ]
        with pytest.raises(QcaeValidationError, match="CURATED_SENSOR"):
            _run(leads=leads, outcomes=outcomes)

    def test_no_stop_can_rest_on_a_condition_the_plan_never_declared(self) -> None:
        leads = [lead("lead-gh-1", "github:owner/lib")]
        outcomes = [_outcome("q-1", results=1, leads=leads)]
        # The baseline plan declares BUDGET_CEILING_REACHED and
        # NON_DOMINATED_SET_SUFFICIENT, but no NEGLIGIBLE_NOVELTY rule.
        with pytest.raises(QcaeValidationError, match="NEGLIGIBLE_NOVELTY"):
            _run(leads=leads, outcomes=outcomes, saturated=True,
                 saturation_reason="nothing new is appearing")


class TestAssembledEvidence:
    def test_partial_search_note_is_carried_not_summarized(self) -> None:
        note = "pages 1-2 of 9; provider rate limit stopped pagination"
        first = lead("lead-gh-1", "github:owner/lib")
        # A second query on the same page boundary finds the same project again:
        # a distinct lead id, the same canonical identity.
        second = lead("lead-gh-2", "github:owner/lib")
        outcomes = [
            _outcome("q-1", leads=(first,)),
            _outcome("q-2", results=3, leads=(second,),
                     status=AdapterStatus.PARTIAL_RESULTS, completeness_note=note),
        ]
        report, _candidates, _ranking = _run(leads=[first], outcomes=outcomes)
        # The completeness note is carried verbatim (attributed to its query), not
        # paraphrased into a summary that could soften "partial".
        assert note in "\n".join(report.partial_search_notes)
        assert report.canonical_candidate_ids == (merge_leads([first])[0].canonical_id,)

    def test_completed_empty_and_failed_searches_stay_distinguishable(self) -> None:
        leads = [lead("lead-gh-1", "github:owner/lib")]
        outcomes = [
            _outcome("q-1", results=1, leads=leads),
            _outcome("q-empty", status=AdapterStatus.NO_RESULTS, results=0),
            _outcome("q-limited", status=AdapterStatus.RATE_LIMITED, results=0),
        ]
        report, _candidates, _ranking = _run(leads=leads, outcomes=outcomes)
        joined = "\n".join(report.negative_findings)
        # Notes carry the executed-query identity, not the caller's label.
        assert "NO_RESULTS" in joined and "RATE_LIMITED" in joined
        assert ("causal-ordering-exec2" in joined
                and "causal-ordering-exec3" in joined)

    def test_remaining_uncertainties_come_from_the_baseline(self) -> None:
        baseline = _baseline(categories=["EVIDENCE_STALE"],
                             detail={"EVIDENCE_STALE": ["ev-001"]},
                             atom_ids=[ATOM_A])
        leads = [lead("lead-gh-1", "github:owner/lib", claims=(ATOM_A,), atoms=(ATOM_A,))]
        outcomes = [_outcome("q-1", results=1, leads=leads)]
        report, _candidates, _ranking = _run(leads=leads, outcomes=outcomes,
                                             baseline=baseline)
        joined = "\n".join(report.remaining_uncertainties)
        assert ATOM_B in joined  # externally unresolved: not covered internally
        assert "ev-001" in joined  # stale evidence pending revalidation

    def test_amendment_proposals_are_carried_from_the_plan(self) -> None:
        proposal = ContractAmendmentProposal(
            proposal_id="prop-001",
            contract_id=CAP,
            contract_version=1,
            plan_id="plan-001",
            discovered_need="discovery needs a NEW_BEHAVIOR clause",
            proposed_change="add ordering constraint clause",
            evidence_ids=("ev-1",),
        )
        plan = make_discovery_plan(**plan_kwargs(amendment_proposals=(proposal,)))
        leads = [lead("lead-gh-1", "github:owner/lib")]
        outcomes = [_outcome("q-1", results=1, leads=leads)]
        report, _candidates, _ranking = _run(leads=leads, outcomes=outcomes, plan=plan)
        assert report.amendment_proposals == (proposal,)


class TestStopVerdictIsDerived:
    def test_budget_exhaustion_is_derived_from_the_counters(self) -> None:
        leads = [lead("lead-gh-1", "github:owner/lib")]
        outcomes = [_outcome("q-1", results=1, leads=leads)]
        report, candidates, _ranking = _run(leads=leads, outcomes=outcomes)
        assert report.stop_recommendation.state.value == "CONTINUE"
        assert report.stop_recommendation.satisfied_conditions == ()

        # max_queries is 10 in the plan; 11 executed searches exhaust it. The
        # candidate is known from the earlier pass, so this pass discovers
        # nothing: the counters advance, the discovery set does not.
        spent = [_outcome(f"q-{i}", status=AdapterStatus.NO_RESULTS, results=0)
                 for i in range(11)]
        report_spent, _c2, _r2 = _run(leads=leads, outcomes=spent,
                                      previously_known_candidates=candidates)
        assert report_spent.saturation_metrics.queries_executed >= 10
        assert report_spent.stop_recommendation.state.value == "STOP"
        assert [c.value for c in report_spent.stop_recommendation.satisfied_conditions] == [
            "BUDGET_CEILING_REACHED"
        ]

    def test_repeat_pass_novelty_is_measured_against_the_previous_pass(self) -> None:
        leads, outcomes = _two_adapter_run()
        first, candidates, _ranking = _run(leads=leads, outcomes=outcomes)
        discovered = first.saturation_metrics.new_candidates
        assert discovered >= 1

        second, _c2, _r2 = _run(
            leads=leads, outcomes=outcomes,
            previous_metrics=first.saturation_metrics,
            previously_known_candidates=candidates,
        )
        # A repeat pass over the same candidates discovers nothing new; the
        # counters must not inflate (canon 2.1.10, and the stop law depends on it).
        assert second.saturation_metrics.new_candidates == discovered
        assert second.saturation_metrics.new_specifications == \
            first.saturation_metrics.new_specifications
        assert (second.saturation_metrics.marginal_novelty_rate
                < first.saturation_metrics.marginal_novelty_rate)


class TestClaimKindsReachTheArtifact:
    """What a caller sees when a hit claims a capability and matches an atom.

    Canon 2.1.11 separates the two claim kinds at intake, so a capability id
    must never be read as an atom downstream — not by the counters the stop law
    reads, and not by the candidates the artifact hands to the next pass.
    """

    def test_a_capability_claim_is_not_counted_as_an_atom(self) -> None:
        item = lead("lead-cap", "github:owner/lib", claims=(CAP,), atoms=(ATOM_A,))
        report, _c, _r = _run(
            leads=[item], outcomes=[_outcome("q-1", results=1, leads=[item])])
        assert report.saturation_metrics.new_atoms_covered == 1
        assert report.known_candidates[0].claims_atoms == (ATOM_A,)
        assert report.known_candidates[0].claimed_capabilities == (CAP,)

    def test_a_capability_only_claim_earns_no_atom_coverage(self) -> None:
        """Fail-closed: naming the capability is not evidence of covering it."""
        item = lead("lead-cap", "github:owner/lib", claims=(CAP,), atoms=())
        report, _c, _r = _run(
            leads=[item], outcomes=[_outcome("q-1", results=1, leads=[item])])
        assert report.saturation_metrics.new_atoms_covered == 0
        assert report.escalation_queue[0].dimension_scores["coverage_potential"] == 0.0

    def test_the_handoff_carries_atoms_and_capabilities_apart(self) -> None:
        """The carried candidate keeps the kinds apart through the artifact."""
        item = lead("lead-cap", "github:owner/lib", claims=(CAP,), atoms=(ATOM_A,))
        first, _c, _r = _run(
            leads=[item], outcomes=[_outcome("q-1", results=1, leads=[item])])
        handed = type(first).from_dict(first.to_dict())
        carried = handed.known_candidates[0]
        assert carried.claims_atoms == (ATOM_A,)
        assert carried.claimed_capabilities == (CAP,)
        second, _c2, _r2 = _run(
            leads=[item], outcomes=[_outcome("q-1", results=1, leads=[item])],
            previous_report=handed)
        assert second.saturation_metrics.new_atoms_covered \
            == first.saturation_metrics.new_atoms_covered


class TestNoEgress:
    def test_the_assembler_has_no_egress_path(self) -> None:
        """Assembly is a pure function of records: no adapter, no network."""
        source = Path(reporting.__file__).read_text(encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        forbidden = {"urllib", "http", "socket", "requests", "httpx", "aiohttp"}
        assert not {name for name in imported
                    if name.split(".")[0] in forbidden}, imported
        assert not [name for name in imported
                    if name.startswith("qcae.discovery.github")
                    or name.startswith("qcae.discovery.research")], imported
