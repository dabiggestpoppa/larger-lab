"""P3 — the assembled terminal artifact (canon 2.7.15, 2.1.6, 2.2.13).

These tests drive the assembler the way a caller drives it: a plan, an internal
baseline record, real adapter outcomes and a ranking pass, assembled into the
``DiscoveryReport`` Block 3 receives. They assert the report is *consistent with
the pieces it came from* rather than merely constructible.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

import qcae.discovery.reporting as reporting
from qcae.core.discovery.lead import CandidateKind
from qcae.core.discovery.plan import (
    ContractAmendmentProposal,
    HardPrefilter,
)
from qcae.core.discovery.report import PrefilterDecision
from qcae.core.discovery.vocabulary import SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.discovery import AdapterOutcome, AdapterStatus
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


def _outcome(query_id, *, source_class=SourceClass.GITHUB_REPOSITORY_CODE,
             adapter_id="adapter-github", results=1, leads=(),
             status=AdapterStatus.OK, completeness_note="", message=""):
    """An outcome as a caller would have it: the record an adapter returned."""
    if not message and status != AdapterStatus.OK:
        # The port requires a typed message whenever a search did not simply
        # succeed, so a caller's record always carries one.
        message = f"typed {status.value} from {adapter_id}"
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


def _two_adapter_run():
    """One project found by two adapters, plus a paper from a third.

    Each lead sits in the outcome its own adapter returned: an outcome's leads
    must come from the adapters that responded (port law), so a multi-source hit
    is two outcomes that merge, not one outcome carrying both.
    """
    github = lead("lead-gh-1", "github:owner/lib", claims=(ATOM_A,), atoms=(ATOM_A,))
    registry = lead("lead-reg-1", "github:owner/Lib.git",
                    source_class=SourceClass.INTERNAL_REGISTRY_CODE,
                    adapter_id="adapter-registry",
                    claims=(ATOM_A, ATOM_B), atoms=(ATOM_A, ATOM_B))
    paper = lead("lead-paper-1", "arxiv:2401.00001", kind=CandidateKind.PAPER,
                 source_class=SourceClass.RESEARCH_LITERATURE, adapter_id="adapter-arxiv",
                 claims=(ATOM_B,), atoms=(ATOM_B,), license_claim="")
    outcomes = [
        _outcome("q-gh", leads=(github,)),
        _outcome("q-reg", source_class=SourceClass.INTERNAL_REGISTRY_CODE,
                 adapter_id="adapter-registry", leads=(registry,)),
        _outcome("q-arxiv", source_class=SourceClass.RESEARCH_LITERATURE,
                 adapter_id="adapter-arxiv", leads=(paper,)),
    ]
    return [github, registry, paper], outcomes


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
                 novelty_family="family-ordering"),
        ]
        outcomes = [_outcome("q-1", results=len(leads), leads=leads)]
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
        assert "q-empty" in joined and "NO_RESULTS" in joined
        assert "q-limited" in joined and "RATE_LIMITED" in joined

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
        report, _candidates, _ranking = _run(leads=leads, outcomes=outcomes)
        assert report.stop_recommendation.state.value == "CONTINUE"
        assert report.stop_recommendation.satisfied_conditions == ()

        # max_queries is 10 in the plan; 11 executed searches exhaust it.
        spent = [_outcome(f"q-{i}", status=AdapterStatus.NO_RESULTS, results=0)
                 for i in range(11)]
        report_spent, _c2, _r2 = _run(leads=leads, outcomes=spent)
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
