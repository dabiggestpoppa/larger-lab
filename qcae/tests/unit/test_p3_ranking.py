"""P3-C04 — canonical merge, families, ranking, prefilter, saturation.

Covers canon 2.1.12 (dedup without corroboration), 2.7.3 (hard prefilters),
2.7.5/2.7.6 (diversity and families), 2.7.8/2.7.9 (next-action ranking),
2.7.11 (popularity cap), 2.7.14 (waves), 2.1.10 (saturation) and 2.1.9 (stop
rules). The recurring assertion is that ranking allocates investigation budget
and never promotes a candidate (2.7.4, 2.7.16 invariant 1).
"""

from __future__ import annotations

import dataclasses

import pytest

from qcae.core.discovery import (
    AdapterStatus,
    CandidateKind,
    CandidateLead,
    CostTier,
    DiscoveryBudget,
    DiversityRequirement,
    HardPrefilter,
    QueryFamilyKind,
    QueryFamilyRecord,
    SaturationMetrics,
    SearchCompleteness,
    SearchHypothesis,
    SearchHypothesisKind,
    SourceAllocation,
    SourceClass,
    StopCondition,
    StopRule,
    make_candidate_lead,
    make_discovery_plan,
)
from qcae.core.discovery.lead import QueryLineage
from qcae.core.discovery.report import PrefilterDecision
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.discovery import AdapterOutcome
from qcae.core.vocabulary import EvidenceClass, VerificationLevel
from qcae.discovery.planning.ranking import (
    DIMENSIONS,
    POPULARITY_WEIGHT_CAP,
    RankingDimension,
    RankingPolicy,
    apply_hard_prefilter,
    build_families,
    canonical_key_for,
    merge_leads,
    rank_candidates,
    stop_recommendation,
    update_saturation,
)

ATOM_A = "atom-causal-ordering"
ATOM_B = "atom-duplicate-suppression"
CAP = "CAP-REPLAY-001"


# -- builders ---------------------------------------------------------------


def lineage(source_class, adapter_id, atom_id=ATOM_A) -> QueryLineage:
    return QueryLineage(
        atom_id=atom_id,
        semantic_concept="capability concept",
        family_id="fam-behavioral",
        concrete_query="some query",
        source_class=source_class,
        adapter_id=adapter_id,
    )


def lead(
    lead_id: str,
    locator: str,
    *,
    kind: CandidateKind = CandidateKind.REPOSITORY,
    source_class: SourceClass = SourceClass.GITHUB_REPOSITORY_CODE,
    adapter_id: str = "adapter-github",
    claims=(ATOM_A,),
    atoms=(ATOM_A,),
    revision: str = "abc123",
    completeness: SearchCompleteness = SearchCompleteness.COMPLETE,
    license_claim: str = "MIT",
    novelty_family: str = "",
    conflicts=(),
) -> CandidateLead:
    return make_candidate_lead(
        lead_id=lead_id,
        source_class=source_class,
        adapter_id=adapter_id,
        candidate_kind=kind,
        source_locator=locator,
        discovered_at="2026-09-21T12:00:00Z",
        query_lineage=lineage(source_class, adapter_id, atoms[0]),
        claimed_capabilities=tuple(claims),
        possible_atom_matches=tuple(atoms),
        retrieved_revision=revision,
        license_claim=license_claim,
        completeness=completeness,
        novelty_family=novelty_family,
        initial_constraint_conflicts=tuple(conflicts),
    )


def plan_kwargs(**overrides) -> dict:
    kwargs = dict(
        discovery_plan_id="plan-001",
        contract_id=CAP,
        contract_version=1,
        atom_ids=(ATOM_A, ATOM_B),
        internal_baseline_queries=("internal:capability-registry:CAP-REPLAY-001",),
        search_hypotheses=(
            SearchHypothesis(hypothesis_id="hyp-a", atom_ids=(ATOM_A,),
                             kind=SearchHypothesisKind.FOCUSED_LIBRARY,
                             statement="A may exist as a focused library"),
            SearchHypothesis(hypothesis_id="hyp-b", atom_ids=(ATOM_B,),
                             kind=SearchHypothesisKind.EXTRACTABLE_SUBSYSTEM,
                             statement="B may exist in a framework"),
        ),
        query_families=(
            QueryFamilyRecord(family_id="fam-behavioral", kind=QueryFamilyKind.BEHAVIORAL,
                              hypothesis_ids=("hyp-a",), terms=("causal ordering",),
                              source_classes=(SourceClass.INTERNAL_REGISTRY_CODE,
                                              SourceClass.GITHUB_REPOSITORY_CODE)),
            QueryFamilyRecord(family_id="fam-synonym", kind=QueryFamilyKind.SYNONYM,
                              hypothesis_ids=("hyp-b",), terms=("dedup",),
                              source_classes=(SourceClass.PACKAGE_ECOSYSTEM,)),
        ),
        source_allocations=(
            SourceAllocation(source_class=SourceClass.INTERNAL_REGISTRY_CODE, budget_share=0.3,
                             max_tier=CostTier.TIER_0_MEMORY_LOOKUP),
            SourceAllocation(source_class=SourceClass.GITHUB_REPOSITORY_CODE, budget_share=0.4,
                             max_tier=CostTier.TIER_3_SOURCE_TREE),
            SourceAllocation(source_class=SourceClass.PACKAGE_ECOSYSTEM, budget_share=0.3),
        ),
        budget=DiscoveryBudget(max_queries=10, max_results_inspected=50,
                               max_source_calls=10, max_wall_clock_seconds=600),
        cost_tier_ceiling=CostTier.TIER_3_SOURCE_TREE,
        diversity_requirements=DiversityRequirement(),
        stop_rules=(
            StopRule(condition=StopCondition.BUDGET_CEILING_REACHED),
            StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),
            StopRule(condition=StopCondition.NEGLIGIBLE_NOVELTY, threshold=0.05),
        ),
        created_by="qcae-discovery-planner",
        policy_version="discovery-ranking-policy-1.0",
        single_route_justification="narrow routes recorded for this fixture",
    )
    kwargs.update(overrides)
    return kwargs


def plan():
    return make_discovery_plan(**plan_kwargs())


def policy(**overrides) -> RankingPolicy:
    weights = {d.value: 0.0 for d in DIMENSIONS}
    weights[RankingDimension.SEMANTIC_FIT.value] = 1.0
    kwargs = dict(policy_version="rank-policy-1.0", weights=weights, popularity_weight=0.0)
    kwargs.update(overrides)
    return RankingPolicy(**kwargs)


def adapter_outcome(query_id: str, *, status=AdapterStatus.OK, results=10, leads=()) -> AdapterOutcome:
    payload = status in (
        AdapterStatus.OK,
        AdapterStatus.PARTIAL_RESULTS,
        AdapterStatus.NO_RESULTS,
    )
    return AdapterOutcome(
        adapter_id="adapter-github",
        source_class=SourceClass.GITHUB_REPOSITORY_CODE,
        query_id=query_id,
        status=status,
        leads=tuple(leads),
        pages_inspected=1 if payload else 0,
        results_inspected=results if payload else 0,
        message="typed failure" if not payload else "",
    )


# -- canonical merge (2.1.12) ----------------------------------------------


class TestCanonicalMerge:
    def test_same_project_from_two_sources_is_one_candidate_with_both_paths(self) -> None:
        leads = [
            lead("lead-1", "github:owner/repo"),
            lead("lead-2", "github:owner/repo", source_class=SourceClass.PACKAGE_ECOSYSTEM,
                 adapter_id="adapter-pypi"),
        ]
        merged = merge_leads(leads)
        assert len(merged) == 1
        candidate = merged[0]
        assert candidate.lead_ids == ("lead-1", "lead-2")
        assert candidate.duplicate_path_count == 1
        assert candidate.distinct_locator_count == 1
        assert candidate.independent_path_count == 2
        assert candidate.claim_verification is VerificationLevel.DISCOVERED

    def test_locator_normalization_is_conservative(self) -> None:
        assert len(merge_leads([
            lead("lead-1", "github:Owner/Repo.git"),
            lead("lead-2", "github:owner/repo/"),
        ])) == 1
        assert canonical_key_for(CandidateKind.REPOSITORY, "github:A/B") == \
            canonical_key_for(CandidateKind.REPOSITORY, "github:a/b")
        # Case is identity for non-repository locators (papers, specs, datasets).
        assert canonical_key_for(CandidateKind.PAPER, "arxiv:1234/AbC") != \
            canonical_key_for(CandidateKind.PAPER, "arxiv:1234/abc")

    def test_distinct_projects_stay_distinct(self) -> None:
        merged = merge_leads([lead("lead-1", "github:owner/one"),
                              lead("lead-2", "github:owner/two")])
        assert len(merged) == 2

    def test_same_location_different_kind_is_not_merged(self) -> None:
        merged = merge_leads([
            lead("lead-1", "owner/thing", kind=CandidateKind.REPOSITORY),
            lead("lead-2", "owner/thing", kind=CandidateKind.SPECIFICATION, license_claim=""),
        ])
        assert len(merged) == 2

    def test_claims_are_unioned_and_readiness_requires_an_anchor(self) -> None:
        merged = merge_leads([
            lead("lead-1", "github:owner/repo", claims=(ATOM_A,), atoms=(ATOM_A,)),
            lead("lead-2", "github:owner/repo", claims=(ATOM_B,), atoms=(ATOM_B,),
                 revision="", completeness=SearchCompleteness.PARTIAL),
        ])
        candidate = merged[0]
        assert candidate.claims_atoms == (ATOM_A, ATOM_B)
        assert candidate.deeper_intelligence_ready is True
        assert candidate.ready_lead_ids == ("lead-1",)

    def test_identity_is_deterministic_and_content_addressed(self) -> None:
        first = merge_leads([lead("lead-1", "github:owner/repo")])[0]
        second = merge_leads([lead("lead-9", "github:owner/repo")])[0]
        assert first.canonical_id == second.canonical_id

    def test_constraint_conflicts_survive_the_merge(self) -> None:
        candidate = merge_leads([
            lead("lead-1", "github:owner/repo", conflicts=("windows-only platform",))
        ])[0]
        assert candidate.has_constraint_conflicts is True


# -- families (2.7.6) -------------------------------------------------------


class TestFamilies:
    def test_declared_lineage_clusters_around_the_better_score(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/original", novelty_family="family-x",
                 claims=(ATOM_A, ATOM_B), atoms=(ATOM_A, ATOM_B)),
            lead("lead-2", "github:owner/fork", novelty_family="family-x", claims=(ATOM_A,)),
        ])
        by_locator = {c.canonical_locator: c for c in candidates}
        scores = {c.canonical_id: 0.1 for c in candidates}
        scores[by_locator["github:owner/original"].canonical_id] = 0.9
        families = build_families(candidates, scores, policy())
        assert len(families) == 1
        assert families[0].representative_candidate_id == \
            by_locator["github:owner/original"].canonical_id
        assert families[0].independent_family is False
        assert len(families[0].member_candidate_ids) == 2

    def test_singleton_is_its_own_independent_family(self) -> None:
        candidates = merge_leads([lead("lead-1", "github:owner/repo")])
        families = build_families(candidates, {candidates[0].canonical_id: 0.5}, policy())
        assert families[0].independent_family is True
        assert families[0].representative_candidate_id == candidates[0].canonical_id

    def test_family_duplicates_are_deferred_behind_the_representative(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/original", novelty_family="family-x"),
            lead("lead-2", "github:owner/fork", novelty_family="family-x"),
        ])
        result = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        deferred = [e for e in result.queue if e.next_action.value == "DEFER_PENDING_FAMILY"]
        assert len(deferred) == 1
        assert deferred[0].wave == 3
        assert deferred[0].deferred_pending in {e.candidate_id for e in result.queue}


# -- ranking policy laws (2.7.10/2.7.11) -----------------------------------


class TestRankingPolicyLaws:
    def test_every_dimension_must_be_weighted(self) -> None:
        weights = {d.value: 0.0 for d in DIMENSIONS}
        weights[RankingDimension.SEMANTIC_FIT.value] = 1.0
        del weights[RankingDimension.NOVELTY.value]
        with pytest.raises(QcaeValidationError, match="missing"):
            RankingPolicy(policy_version="p", weights=weights).validate()

    def test_unknown_dimension_refused(self) -> None:
        weights = {d.value: 0.0 for d in DIMENSIONS}
        weights[RankingDimension.SEMANTIC_FIT.value] = 1.0
        weights["star_count"] = 0.0
        with pytest.raises(QcaeValidationError, match="unknown ranking dimensions"):
            RankingPolicy(policy_version="p", weights=weights).validate()

    def test_weights_must_sum_to_one(self) -> None:
        weights = {d.value: 0.1 for d in DIMENSIONS}
        with pytest.raises(QcaeValidationError, match="sum to 1.0"):
            RankingPolicy(policy_version="p", weights=weights).validate()

    def test_negative_weight_refused(self) -> None:
        weights = {d.value: 0.0 for d in DIMENSIONS}
        weights[RankingDimension.SEMANTIC_FIT.value] = 0.5
        weights[RankingDimension.MAINTENANCE_PRIOR.value] = -0.5
        with pytest.raises(QcaeValidationError, match="must be >= 0"):
            RankingPolicy(policy_version="p", weights=weights).validate()

    def test_popularity_weight_is_capped(self) -> None:
        weights = {d.value: 0.0 for d in DIMENSIONS}
        weights[RankingDimension.SEMANTIC_FIT.value] = 1.0
        with pytest.raises(QcaeValidationError, match="popularity_weight"):
            RankingPolicy(policy_version="p", weights=weights,
                          popularity_weight=POPULARITY_WEIGHT_CAP + 0.01).validate()
        RankingPolicy(policy_version="p", weights=weights,
                      popularity_weight=POPULARITY_WEIGHT_CAP).validate()

    def test_popularity_cannot_outrank_semantic_fit(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/full", claims=(ATOM_A, ATOM_B),
                 atoms=(ATOM_A, ATOM_B), license_claim=""),
            lead("lead-2", "github:owner/none", claims=("atom-unrelated",),
                 atoms=("atom-unrelated",)),
        ])
        by_locator = {c.canonical_locator: c for c in candidates}
        popularity = {
            by_locator["github:owner/full"].canonical_id: 0.0,
            by_locator["github:owner/none"].canonical_id: 1.0,
        }
        ranking_policy = policy(popularity_weight=POPULARITY_WEIGHT_CAP)
        result = rank_candidates(candidates=candidates, plan=plan(),
                                 policy=ranking_policy, popularity=popularity)
        assert result.entry_for(by_locator["github:owner/full"].canonical_id).score > \
            result.entry_for(by_locator["github:owner/none"].canonical_id).score


# -- score derivation honesty ----------------------------------------------


class TestScoreDerivation:
    def test_semantic_fit_is_declared_atom_coverage(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/full", claims=(ATOM_A, ATOM_B),
                 atoms=(ATOM_A, ATOM_B)),
            lead("lead-2", "github:owner/half", claims=(ATOM_A,), atoms=(ATOM_A,)),
        ])
        by_locator = {c.canonical_locator: c for c in candidates}
        result = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        assert result.entry_for(by_locator["github:owner/full"].canonical_id) \
            .dimension_scores["semantic_fit"] == 1.0
        assert result.entry_for(by_locator["github:owner/half"].canonical_id) \
            .dimension_scores["semantic_fit"] == 0.5

    def test_underivable_dimensions_are_labelled_neutral_priors(self) -> None:
        candidates = merge_leads([lead("lead-1", "github:owner/repo")])
        result = rank_candidates(candidates=candidates, plan=plan(),
                                 policy=policy(neutral_prior=0.5))
        entry = result.queue[0]
        for name in ("maintenance_prior", "dependency_prior", "license_prior"):
            assert entry.dimension_scores[name] == 0.5
        assert "Neutral priors" in entry.rationale
        assert "duplicates are not corroboration" in entry.rationale

    def test_constraint_conflicts_lower_constraint_fit(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/clean"),
            lead("lead-2", "github:owner/conflict",
                 conflicts=("windows-only platform", "requires SaaS egress")),
        ])
        result = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        penalised = [e for e in result.queue if e.dimension_scores["constraint_fit"] < 1.0]
        assert len(penalised) == 1
        assert penalised[0].dimension_scores["constraint_fit"] == 0.5

    def test_evidence_availability_reflects_the_immutable_anchor(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/pinned"),
            lead("lead-2", "github:owner/unpinned", revision="",
                 completeness=SearchCompleteness.PARTIAL),
        ])
        result = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        assert sorted(e.dimension_scores["evidence_availability"] for e in result.queue) == \
            [0.4, 1.0]

    def test_novelty_bonus_favours_a_singleton_family(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/original", novelty_family="family-x"),
            lead("lead-2", "github:owner/fork", novelty_family="family-x"),
            lead("lead-3", "github:owner/other"),
        ])
        result = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        novelty = [e.dimension_scores["novelty"] for e in result.queue]
        assert 1.0 in novelty and 0.5 in novelty


# -- next actions and waves (2.7.9/2.7.14) ---------------------------------


class TestNextActionsAndWaves:
    def test_specification_sources_get_a_spec_lookup(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "arxiv:2020.0001", kind=CandidateKind.PAPER, license_claim="",
                 source_class=SourceClass.RESEARCH_LITERATURE, adapter_id="adapter-arxiv")
        ])
        result = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        assert result.queue[0].next_action.value == "SPECIFICATION_LOOKUP"

    def test_unknown_license_is_resolved_by_a_cheap_license_check(self) -> None:
        candidates = merge_leads([lead("lead-1", "github:owner/repo", license_claim="")])
        result = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        assert result.queue[0].next_action.value == "LICENSE_VERIFY"

    def test_unpinned_revision_gets_a_metadata_step_first(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/repo", revision="",
                 completeness=SearchCompleteness.PARTIAL)
        ])
        result = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        assert result.queue[0].next_action.value == "REPOSITORY_METADATA"

    def test_full_coverage_with_anchor_escalates_to_repository_intelligence(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/repo", claims=(ATOM_A, ATOM_B),
                 atoms=(ATOM_A, ATOM_B))
        ])
        result = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        assert result.queue[0].next_action.value == "DEEP_INTELLIGENCE"

    def test_wave_one_is_bounded_per_source_class(self) -> None:
        candidates = merge_leads([
            lead(f"lead-{i}", f"internal:module{i}", kind=CandidateKind.INTERNAL_CODE,
                 source_class=SourceClass.INTERNAL_REGISTRY_CODE,
                 adapter_id="adapter-internal", license_claim="")
            for i in range(4)
        ])
        result = rank_candidates(candidates=candidates, plan=plan(),
                                 policy=policy(max_per_source_class_in_wave_one=2))
        assert len([e for e in result.queue if e.wave == 1]) == 2
        assert any(e.wave == 2 for e in result.queue)

    def test_queue_is_deterministic(self) -> None:
        candidates = merge_leads([
            lead("lead-1", "github:owner/a"),
            lead("lead-2", "github:owner/b", license_claim=""),
            lead("lead-3", "github:owner/c", revision="",
                 completeness=SearchCompleteness.PARTIAL),
        ])
        first = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        second = rank_candidates(candidates=candidates, plan=plan(), policy=policy())
        assert [e.candidate_id for e in first.queue] == [e.candidate_id for e in second.queue]
        assert [e.wave for e in first.queue] == [e.wave for e in second.queue]

    def test_empty_candidate_set_produces_an_empty_queue(self) -> None:
        result = rank_candidates(candidates=(), plan=plan(), policy=policy())
        assert result.queue == ()
        assert result.families == ()


# -- prefilter (2.7.3) ------------------------------------------------------


class TestPrefilterLaws:
    def test_decision_below_the_prefilter_evidence_floor_is_refused(self) -> None:
        candidate = merge_leads([lead("lead-1", "github:owner/repo")])[0]
        strict = HardPrefilter(
            prefilter_id="pf-archived",
            rule="archived repository incompatible with the maintenance profile",
            min_evidence_class=EvidenceClass.E2_SOURCE,
        )
        with pytest.raises(QcaeValidationError, match="requires at least"):
            apply_hard_prefilter(strict, candidate, PrefilterDecision.DEFER,
                                 EvidenceClass.E0_CLAIM, "looks unmaintained")

    def test_reject_requires_source_grade_evidence(self) -> None:
        candidate = merge_leads([lead("lead-1", "github:owner/repo")])[0]
        strict = HardPrefilter(
            prefilter_id="pf-license",
            rule="explicit incompatible license",
            min_evidence_class=EvidenceClass.E1_DOCUMENTATION,
        )
        with pytest.raises(QcaeValidationError, match="source-grade"):
            apply_hard_prefilter(strict, candidate, PrefilterDecision.REJECT,
                                 EvidenceClass.E1_DOCUMENTATION, "docs look restrictive")

    def test_rejected_candidate_is_parked_not_ranked(self) -> None:
        candidate = merge_leads([lead("lead-1", "github:owner/repo")])[0]
        strict = HardPrefilter(
            prefilter_id="pf-license",
            rule="explicit incompatible license",
            min_evidence_class=EvidenceClass.E2_SOURCE,
        )
        decision = apply_hard_prefilter(
            strict, candidate, PrefilterDecision.REJECT, EvidenceClass.E2_SOURCE,
            "LICENSE file is GPL-3.0 and the contract forbids copyleft",
        )
        result = rank_candidates(candidates=[candidate], plan=plan(), policy=policy(),
                                 prefilter_decisions=(decision,))
        entry = result.queue[0]
        assert entry.next_action.value == "REJECT_HARD_CONSTRAINT"
        assert entry.wave == 3
        assert result.rejected_candidate_ids == (candidate.canonical_id,)


# -- saturation (2.1.10) ----------------------------------------------------


class TestSaturation:
    def test_only_searches_that_ran_advance_counters(self) -> None:
        candidates = merge_leads([lead("lead-1", "github:owner/repo")])
        metrics = update_saturation(
            SaturationMetrics(),
            outcomes=(
                adapter_outcome("q1", results=2, leads=(lead("lead-1", "github:owner/repo"),)),
                adapter_outcome("q2", status=AdapterStatus.RATE_LIMITED, leads=()),
                adapter_outcome("q3", status=AdapterStatus.NO_RESULTS, results=0),
                adapter_outcome("q4", status=AdapterStatus.PROVIDER_FAILURE),
            ),
            canonical_candidates=candidates,
        )
        assert metrics.queries_executed == 4
        assert metrics.results_inspected == 2
        assert metrics.new_candidates == 1
        assert metrics.new_failure_information == 3

    def test_novelty_is_measured_against_what_was_known(self) -> None:
        candidates = merge_leads([lead("lead-1", "github:owner/repo")])
        known = candidates[0].canonical_id
        metrics = update_saturation(
            SaturationMetrics(),
            canonical_candidates=candidates,
            previous_candidate_ids=(known,),
            previous_covered_atoms=(ATOM_A,),
        )
        assert metrics.new_candidates == 0
        assert metrics.new_atoms_covered == 0
        assert metrics.marginal_novelty_rate == 0.0

    def test_saturation_requires_a_reason(self) -> None:
        with pytest.raises(QcaeValidationError, match="recorded reason"):
            update_saturation(SaturationMetrics(), saturated=True)


# -- stop recommendation (2.1.9) -------------------------------------------


class TestStopRecommendation:
    def test_continue_when_nothing_is_satisfied(self) -> None:
        recommendation = stop_recommendation(plan(), SaturationMetrics())
        assert recommendation.state.value == "CONTINUE"
        assert recommendation.satisfied_conditions == ()

    def test_budget_ceiling_stops_the_search(self) -> None:
        recommendation = stop_recommendation(plan(), SaturationMetrics(),
                                             budget_exhausted=True)
        assert recommendation.state.value == "STOP"
        assert StopCondition.BUDGET_CEILING_REACHED in recommendation.satisfied_conditions

    def test_saturation_without_a_declared_threshold_cannot_stop(self) -> None:
        no_novelty_rule = make_discovery_plan(**plan_kwargs(stop_rules=(
            StopRule(condition=StopCondition.BUDGET_CEILING_REACHED),
            StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),
        )))
        with pytest.raises(QcaeValidationError, match="NEGLIGIBLE_NOVELTY"):
            stop_recommendation(
                no_novelty_rule,
                SaturationMetrics(results_inspected=10, new_candidates=0, saturated=True,
                                  saturation_reason="three families returned known candidates"),
            )

    def test_saturated_search_with_a_declared_threshold_stops(self) -> None:
        recommendation = stop_recommendation(
            plan(),
            SaturationMetrics(results_inspected=40, new_candidates=1, saturated=True,
                              saturation_reason="ten queries produced one new candidate"),
        )
        assert recommendation.state.value == "STOP"
        assert StopCondition.NEGLIGIBLE_NOVELTY in recommendation.satisfied_conditions

    def test_undeclared_stop_condition_is_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="not declared by the plan"):
            stop_recommendation(plan(), SaturationMetrics(),
                                hard_constraints_eliminated_class=True)


# -- regressions from the tranche-1 audit -----------------------------------
#
# Both defects shipped because every other test in this file runs a single merged
# batch and a single saturation pass. Real runs merge per adapter outcome and
# repeat searches until a stop rule fires, so these two paths are exercised here.


class TestMultiSourceAggregationRegression:
    """Audit finding 1 — aggregation of separate merge passes crashed.

    ``merge_leads(outcome_a) + merge_leads(outcome_b)`` is how multi-source runs
    combine results, and canon 2.1.12 exists precisely so that the same project
    found twice stays one candidate.
    """

    def _two_passes(self):
        github_pass = merge_leads([lead("lead-gh", "github:owner/repo")])
        registry_pass = merge_leads([
            lead("lead-pypi", "github:owner/repo",
                 source_class=SourceClass.PACKAGE_ECOSYSTEM, adapter_id="adapter-pypi")
        ])
        return github_pass, registry_pass

    def test_separate_passes_for_one_project_rank_as_a_single_candidate(self) -> None:
        github_pass, registry_pass = self._two_passes()
        assert github_pass[0].canonical_id == registry_pass[0].canonical_id
        combined = list(github_pass) + list(registry_pass)
        result = rank_candidates(candidates=combined, plan=plan(), policy=policy())
        assert [entry.candidate_id for entry in result.queue] == [github_pass[0].canonical_id]
        assert [family.member_candidate_ids for family in result.families] == [
            (github_pass[0].canonical_id,)
        ]

    def test_aggregation_preserves_every_discovery_path(self) -> None:
        from qcae.discovery.planning.ranking import merge_canonical_candidates

        github_pass, registry_pass = self._two_passes()
        aggregated = merge_canonical_candidates(list(github_pass) + list(registry_pass))
        assert len(aggregated) == 1
        assert aggregated[0].lead_ids == ("lead-gh", "lead-pypi")
        assert aggregated[0].independent_path_count == 2
        assert aggregated[0].duplicate_path_count == 1

    def test_aggregation_is_deterministic_and_idempotent(self) -> None:
        from qcae.discovery.planning.ranking import merge_canonical_candidates

        github_pass, registry_pass = self._two_passes()
        combined = list(github_pass) + list(registry_pass)
        once = merge_canonical_candidates(combined)
        twice = merge_canonical_candidates(list(once))
        assert once == twice
        assert merge_canonical_candidates(list(reversed(combined))) == once


class TestRepeatedPassSaturationRegression:
    """Audit finding 2 — repeated passes inflated novelty so STOP never fired.

    ``marginal_novelty_rate`` is cumulative (novel items / results inspected), so
    a counter that increments for *known* candidates keeps the rate above the
    declared ``NEGLIGIBLE_NOVELTY`` threshold no matter how exhausted the search
    becomes, and the saturated search runs to budget instead of stopping
    (canon 2.1.9/2.1.10).
    """

    PAPER_LEAD = lead("lead-1", "arxiv:2020.1", kind=CandidateKind.PAPER,
                      license_claim="", source_class=SourceClass.RESEARCH_LITERATURE,
                      adapter_id="adapter-arxiv", novelty_family="family-spec")

    def _search_outcome(self):
        """A search that keeps returning the one paper already discovered."""
        return AdapterOutcome(
            adapter_id="adapter-arxiv",
            source_class=SourceClass.RESEARCH_LITERATURE,
            query_id="qry-paper",
            status=AdapterStatus.OK,
            leads=(self.PAPER_LEAD,),
            pages_inspected=1,
            results_inspected=10,
        )

    def _twenty_passes(self) -> SaturationMetrics:
        specs = merge_leads([self.PAPER_LEAD])
        candidate_id = specs[0].canonical_id
        metrics = update_saturation(
            SaturationMetrics(),
            outcomes=(self._search_outcome(),),
            canonical_candidates=specs,
        )
        for _ in range(19):
            metrics = update_saturation(
                metrics,
                outcomes=(self._search_outcome(),),
                canonical_candidates=specs,
                previous_candidate_ids=(candidate_id,),
                previous_family_ids=("family-spec",),
                previous_covered_atoms=(ATOM_A,),
            )
        return metrics

    def test_repeat_passes_over_known_candidates_do_not_inflate_novelty(self) -> None:
        metrics = self._twenty_passes()
        assert metrics.new_candidates == 1
        assert metrics.new_specifications == 1
        assert metrics.new_implementation_families == 1

    def test_saturated_search_can_satisfy_the_declared_stop_rule(self) -> None:
        metrics = self._twenty_passes()
        saturated = dataclasses.replace(
            metrics,
            saturated=True,
            saturation_reason="twenty passes returned only the already-known candidate",
        )
        recommendation = stop_recommendation(plan(), saturated)
        assert recommendation.state.value == "STOP"
        assert StopCondition.NEGLIGIBLE_NOVELTY in recommendation.satisfied_conditions
