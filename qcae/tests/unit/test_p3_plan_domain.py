"""P3-C01 — DiscoveryPlan domain: canon 2.1 laws (planner failure modes).

Each assertion names the canon invariant it protects. The point of this suite is
that canon 2.1.16's failure modes (one-query discovery, dominant-vocabulary
capture, external search before internal lookup, silent contract change) are
*unrepresentable*, not merely discouraged.
"""

from __future__ import annotations

import pytest

from qcae.core.discovery import (
    BLOCK_2_MAX_TIER,
    AmendmentProposalStatus,
    ContractAmendmentProposal,
    CostTier,
    DiscoveryBudget,
    DiscoveryPlan,
    DiversityRequirement,
    HardPrefilter,
    QueryFamilyKind,
    QueryFamilyRecord,
    SaturationMetrics,
    SearchHypothesis,
    SearchHypothesisKind,
    SourceAllocation,
    SourceClass,
    StopCondition,
    StopRule,
    make_discovery_plan,
)
from qcae.core.errors import QcaeSchemaVersionError, QcaeValidationError
from qcae.core.vocabulary import EvidenceClass

ATOM_A = "atom-causal-ordering"
ATOM_B = "atom-duplicate-suppression"


# -- fixtures / builders ----------------------------------------------------


def hypothesis(hypothesis_id: str, atoms, kind, sources) -> SearchHypothesis:
    return SearchHypothesis(
        hypothesis_id=hypothesis_id,
        atom_ids=tuple(atoms),
        kind=kind,
        statement=f"capability may exist as {hypothesis_id}",
        rationale="route derived from contract semantics",
        expected_source_classes=tuple(sources),
    )


def family(family_id: str, kind, hypothesis_ids, sources) -> QueryFamilyRecord:
    return QueryFamilyRecord(
        family_id=family_id,
        kind=kind,
        hypothesis_ids=tuple(hypothesis_ids),
        terms=("causal ordering",),
        source_classes=tuple(sources),
    )


def allocation(source_class, share, tier=CostTier.TIER_1_METADATA_SNIPPETS) -> SourceAllocation:
    return SourceAllocation(
        source_class=source_class,
        budget_share=share,
        max_tier=tier,
        rationale="portfolio balance for this capability family",
    )


def budget() -> DiscoveryBudget:
    return DiscoveryBudget(
        max_queries=40,
        max_results_inspected=200,
        max_source_calls=20,
        max_wall_clock_seconds=900,
        max_cost_usd=5.0,
    )


def stop_rules() -> tuple:
    return (
        StopRule(condition=StopCondition.BUDGET_CEILING_REACHED, detail="plan envelope"),
        StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),
        StopRule(condition=StopCondition.NEGLIGIBLE_NOVELTY, threshold=0.05),
    )


def hypotheses_multi() -> tuple:
    """Two atoms, three routes: enough to trip the diversity requirement."""
    return (
        hypothesis("hyp-focused-library", [ATOM_A], SearchHypothesisKind.FOCUSED_LIBRARY,
                   [SourceClass.GITHUB_REPOSITORY_CODE, SourceClass.PACKAGE_ECOSYSTEM]),
        hypothesis("hyp-paper-reference", [ATOM_A], SearchHypothesisKind.PAPER_REFERENCE_IMPLEMENTATION,
                   [SourceClass.RESEARCH_LITERATURE]),
        hypothesis("hyp-standard", [ATOM_B], SearchHypothesisKind.PROTOCOL_SPECIFICATION,
                   [SourceClass.STANDARDS_SPECIFICATIONS]),
        hypothesis("hyp-embedded", [ATOM_B], SearchHypothesisKind.EXTRACTABLE_SUBSYSTEM,
                   [SourceClass.GITHUB_REPOSITORY_CODE]),
    )


def families_multi() -> tuple:
    return (
        family("fam-behavioral", QueryFamilyKind.BEHAVIORAL, ["hyp-focused-library", "hyp-embedded"],
               [SourceClass.INTERNAL_REGISTRY_CODE, SourceClass.GITHUB_REPOSITORY_CODE]),
        family("fam-synonym", QueryFamilyKind.SYNONYM, ["hyp-focused-library", "hyp-paper-reference"],
               [SourceClass.PACKAGE_ECOSYSTEM, SourceClass.RESEARCH_LITERATURE]),
        family("fam-spec", QueryFamilyKind.SPECIFICATION_PAPER, ["hyp-standard"],
               [SourceClass.STANDARDS_SPECIFICATIONS]),
    )


def allocations() -> tuple:
    return (
        allocation(SourceClass.INTERNAL_REGISTRY_CODE, 0.1, CostTier.TIER_0_MEMORY_LOOKUP),
        allocation(SourceClass.GITHUB_REPOSITORY_CODE, 0.4, CostTier.TIER_3_SOURCE_TREE),
        allocation(SourceClass.PACKAGE_ECOSYSTEM, 0.2),
        allocation(SourceClass.RESEARCH_LITERATURE, 0.2),
        allocation(SourceClass.STANDARDS_SPECIFICATIONS, 0.1),
    )


def plan_kwargs(**overrides) -> dict:
    kwargs = dict(
        discovery_plan_id="plan-replay-001",
        contract_id="CAP-REPLAY-001",
        contract_version=1,
        atom_ids=(ATOM_A, ATOM_B),
        internal_baseline_queries=(
            "internal:capability-registry:CAP-REPLAY-001",
            "internal:negative-knowledge:causal-ordering",
        ),
        search_hypotheses=hypotheses_multi(),
        query_families=families_multi(),
        source_allocations=allocations(),
        budget=budget(),
        cost_tier_ceiling=CostTier.TIER_3_SOURCE_TREE,
        diversity_requirements=DiversityRequirement(),
        hard_prefilters=(
            HardPrefilter(
                prefilter_id="pf-archived",
                rule="archived repository incompatible with the required maintenance profile",
                min_evidence_class=EvidenceClass.E2_SOURCE,
                rationale="repository metadata is source-grade evidence",
            ),
        ),
        stop_rules=stop_rules(),
        created_by="qcae-discovery-planner",
        policy_version="discovery-ranking-policy-1.0",
        operating_context="standalone",
        security_data_constraints=("no-external-egress-without-policy",),
        accepted_acquisition_forms=("EXTRACT_COMPONENT", "REIMPLEMENT_FROM_SPEC"),
    )
    kwargs.update(overrides)
    return kwargs


# -- happy path -------------------------------------------------------------


class TestValidPlan:
    def test_valid_plan_builds_and_digests(self) -> None:
        plan = make_discovery_plan(**plan_kwargs())
        assert plan.enabled_source_classes()[0] == SourceClass.INTERNAL_REGISTRY_CODE
        assert len(plan.digest()) == 64

    def test_round_trip_preserves_equality_including_int_enum_tier(self) -> None:
        plan = make_discovery_plan(**plan_kwargs())
        restored = DiscoveryPlan.from_dict(plan.to_dict())
        assert restored == plan
        assert restored.cost_tier_ceiling is CostTier.TIER_3_SOURCE_TREE
        assert restored.digest() == plan.digest()

    def test_hypotheses_for_atom(self) -> None:
        plan = make_discovery_plan(**plan_kwargs())
        assert {h.hypothesis_id for h in plan.hypotheses_for_atom(ATOM_A)} == {
            "hyp-focused-library",
            "hyp-paper-reference",
        }

    def test_schema_version_and_unknown_field_fail_closed(self) -> None:
        plan = make_discovery_plan(**plan_kwargs())
        payload = plan.to_dict()
        payload["schema_version"] = 99
        with pytest.raises(QcaeSchemaVersionError):
            DiscoveryPlan.from_dict(payload)
        payload = plan.to_dict()
        payload["smuggled_field"] = "retroactive"
        with pytest.raises(Exception):
            DiscoveryPlan.from_dict(payload)


# -- canon 2.1.16: one-query discovery, unrouted atoms ----------------------


class TestAntiOneQueryLaws:
    def test_plan_without_hypotheses_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="search hypothesis"):
            make_discovery_plan(**plan_kwargs(search_hypotheses=()))

    def test_plan_without_query_families_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="query families"):
            make_discovery_plan(**plan_kwargs(query_families=()))

    def test_unrouted_atom_refused(self) -> None:
        hypotheses = tuple(
            h for h in hypotheses_multi() if ATOM_B not in h.atom_ids
        )
        with pytest.raises(QcaeValidationError, match="without any search hypothesis"):
            make_discovery_plan(**plan_kwargs(search_hypotheses=hypotheses))

    def test_single_route_atom_requires_recorded_justification(self) -> None:
        hypotheses = (
            hypothesis("hyp-focused-library", [ATOM_A, ATOM_B],
                       SearchHypothesisKind.EXTRACTABLE_SUBSYSTEM,
                       [SourceClass.GITHUB_REPOSITORY_CODE]),
            hypothesis("hyp-embedded", [ATOM_B], SearchHypothesisKind.EXTRACTABLE_SUBSYSTEM,
                       [SourceClass.GITHUB_REPOSITORY_CODE]),
        )
        families = (
            family("fam-behavioral", QueryFamilyKind.BEHAVIORAL, ["hyp-focused-library", "hyp-embedded"],
                   [SourceClass.INTERNAL_REGISTRY_CODE, SourceClass.GITHUB_REPOSITORY_CODE]),
            family("fam-synonym", QueryFamilyKind.SYNONYM, ["hyp-focused-library"],
                   [SourceClass.PACKAGE_ECOSYSTEM]),
        )
        portfolio = (
            allocation(SourceClass.INTERNAL_REGISTRY_CODE, 0.2, CostTier.TIER_0_MEMORY_LOOKUP),
            allocation(SourceClass.GITHUB_REPOSITORY_CODE, 0.4, CostTier.TIER_3_SOURCE_TREE),
            allocation(SourceClass.PACKAGE_ECOSYSTEM, 0.4),
        )
        with pytest.raises(QcaeValidationError, match="single search route"):
            make_discovery_plan(
                **plan_kwargs(
                    search_hypotheses=hypotheses,
                    query_families=families,
                    source_allocations=portfolio,
                    single_route_justification="",
                )
            )
        plan = make_discovery_plan(
            **plan_kwargs(
                search_hypotheses=hypotheses,
                query_families=families,
                source_allocations=portfolio,
                single_route_justification="capability is single-vendor by construction",
            )
        )
        assert plan.single_route_justification

    def test_hypothesis_outside_plan_scope_refused(self) -> None:
        hypotheses = hypotheses_multi() + (
            hypothesis("hyp-foreign", ["atom-not-in-scope"], SearchHypothesisKind.SERVICE_API,
                       [SourceClass.WEB_DISCOVERY]),
        )
        with pytest.raises(QcaeValidationError, match="outside the plan scope"):
            make_discovery_plan(**plan_kwargs(search_hypotheses=hypotheses))

    def test_hypothesis_without_query_family_refused(self) -> None:
        hypotheses = hypotheses_multi() + (
            hypothesis("hyp-orphan", [ATOM_A], SearchHypothesisKind.ADJACENT_DOMAIN,
                       [SourceClass.GITHUB_REPOSITORY_CODE]),
        )
        with pytest.raises(QcaeValidationError, match="no query family"):
            make_discovery_plan(**plan_kwargs(search_hypotheses=hypotheses))

    def test_family_referencing_unknown_hypothesis_refused(self) -> None:
        families = families_multi() + (
            family("fam-phantom", QueryFamilyKind.SYNONYM, ["hyp-not-declared"],
                   [SourceClass.GITHUB_REPOSITORY_CODE]),
        )
        with pytest.raises(QcaeValidationError, match="unknown hypotheses"):
            make_discovery_plan(**plan_kwargs(query_families=families))


# -- canon 2.1.6: internal-first -------------------------------------------


class TestInternalFirstLaw:
    def test_plan_without_internal_baseline_queries_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="internal_baseline_queries"):
            make_discovery_plan(**plan_kwargs(internal_baseline_queries=()))


# -- canon 2.1.7 / 2.1.16: diversity and dominant-vocabulary capture -------


class TestDiversityLaws:
    def test_multi_hypothesis_plan_needs_a_diversity_family(self) -> None:
        families = (
            family("fam-behavioral", QueryFamilyKind.BEHAVIORAL,
                   [h.hypothesis_id for h in hypotheses_multi()],
                   [SourceClass.INTERNAL_REGISTRY_CODE, SourceClass.GITHUB_REPOSITORY_CODE,
                    SourceClass.PACKAGE_ECOSYSTEM, SourceClass.RESEARCH_LITERATURE,
                    SourceClass.STANDARDS_SPECIFICATIONS]),
        )
        with pytest.raises(QcaeValidationError, match="diversity family"):
            make_discovery_plan(**plan_kwargs(query_families=families))

    def test_single_source_capture_refused(self) -> None:
        allocs = (
            allocation(SourceClass.INTERNAL_REGISTRY_CODE, 0.1, CostTier.TIER_0_MEMORY_LOOKUP),
            allocation(SourceClass.GITHUB_REPOSITORY_CODE, 0.9, CostTier.TIER_3_SOURCE_TREE),
        )
        with pytest.raises(QcaeValidationError, match="diversity cap"):
            make_discovery_plan(**plan_kwargs(source_allocations=allocs))

    def test_budget_shares_must_sum_to_one(self) -> None:
        allocs = allocations()[:-1]
        with pytest.raises(QcaeValidationError, match="sum to 1.0"):
            make_discovery_plan(**plan_kwargs(source_allocations=allocs))

    def test_enabled_budget_that_is_never_queried_refused(self) -> None:
        allocs = allocations() + (
            allocation(SourceClass.WEB_DISCOVERY, 0.0),
        )
        with pytest.raises(QcaeValidationError, match="funded but never queried"):
            make_discovery_plan(**plan_kwargs(source_allocations=allocs))

    def test_diversity_requirement_cannot_be_weakened_to_one_source(self) -> None:
        with pytest.raises(QcaeValidationError, match="at least 2"):
            DiversityRequirement(min_distinct_source_classes=1).validate()

    def test_diversity_cap_of_one_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="between 0 and 1"):
            DiversityRequirement(max_single_source_share=1.0).validate()

    def test_enabled_classes_below_requirement_refused(self) -> None:
        allocs = (
            allocation(SourceClass.GITHUB_REPOSITORY_CODE, 0.5, CostTier.TIER_3_SOURCE_TREE),
            allocation(SourceClass.PACKAGE_ECOSYSTEM, 0.5),
        )
        strict = DiversityRequirement(min_distinct_source_classes=3)
        with pytest.raises(QcaeValidationError, match="below the diversity requirement"):
            make_discovery_plan(
                **plan_kwargs(source_allocations=allocs, diversity_requirements=strict)
            )

    def test_family_targeting_unfunded_source_class_refused(self) -> None:
        families = families_multi()[:-1] + (
            family("fam-spec", QueryFamilyKind.SPECIFICATION_PAPER,
                   ["hyp-standard", "hyp-paper-reference"], [SourceClass.WEB_DISCOVERY]),
        )
        with pytest.raises(QcaeValidationError, match="no enabled allocation"):
            make_discovery_plan(**plan_kwargs(query_families=families))


# -- canon 2.1.8: cost tiers ------------------------------------------------


class TestCostTierLaws:
    def test_block_2_cannot_ceiling_above_tier_3(self) -> None:
        with pytest.raises(QcaeValidationError, match="Block 2"):
            make_discovery_plan(**plan_kwargs(cost_tier_ceiling=CostTier.TIER_4_REPOSITORY_INTELLIGENCE))

    def test_allocation_tier_above_ceiling_refused(self) -> None:
        allocs = (
            allocation(SourceClass.INTERNAL_REGISTRY_CODE, 0.1, CostTier.TIER_0_MEMORY_LOOKUP),
            allocation(SourceClass.GITHUB_REPOSITORY_CODE, 0.4, CostTier.TIER_3_SOURCE_TREE),
            allocation(SourceClass.PACKAGE_ECOSYSTEM, 0.2),
            allocation(SourceClass.RESEARCH_LITERATURE, 0.2),
            allocation(SourceClass.STANDARDS_SPECIFICATIONS, 0.1),
        )
        with pytest.raises(QcaeValidationError, match="above the plan ceiling"):
            make_discovery_plan(
                **plan_kwargs(source_allocations=allocs, cost_tier_ceiling=CostTier.TIER_2_DOCS_PACKAGE_METADATA)
            )

    def test_block_2_ceiling_constant_is_tier_3(self) -> None:
        assert BLOCK_2_MAX_TIER is CostTier.TIER_3_SOURCE_TREE


# -- canon 2.1.9: stop rules ------------------------------------------------


class TestStopRuleLaws:
    def test_plan_without_stop_rules_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="stop rules must exist"):
            make_discovery_plan(**plan_kwargs(stop_rules=()))

    def test_required_stop_conditions_must_be_present(self) -> None:
        rules = (StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),)
        with pytest.raises(QcaeValidationError, match="stop rule conditions missing"):
            make_discovery_plan(**plan_kwargs(stop_rules=rules))

    def test_duplicate_stop_conditions_refused(self) -> None:
        rules = stop_rules() + (StopRule(condition=StopCondition.BUDGET_CEILING_REACHED),)
        with pytest.raises(QcaeValidationError, match="duplicate"):
            make_discovery_plan(**plan_kwargs(stop_rules=rules))

    def test_negligible_novelty_requires_a_threshold(self) -> None:
        with pytest.raises(QcaeValidationError, match="explicit threshold"):
            StopRule(condition=StopCondition.NEGLIGIBLE_NOVELTY).validate()


# -- canon 2.7.3 / 2.2.14: hard prefilters ---------------------------------


class TestHardPrefilterLaws:
    def test_prefilter_cannot_act_on_claim_evidence(self) -> None:
        with pytest.raises(QcaeValidationError, match="E0_CLAIM"):
            HardPrefilter(
                prefilter_id="pf-stars",
                rule="reject repositories below 1000 stars",
                min_evidence_class=EvidenceClass.E0_CLAIM,
            ).validate()

    def test_prefilter_with_evidence_floor_is_accepted(self) -> None:
        plan = make_discovery_plan(**plan_kwargs())
        assert plan.hard_prefilters[0].min_evidence_class is EvidenceClass.E2_SOURCE


# -- canon 2.1.14: contract amendment proposals -----------------------------


class TestAmendmentProposalLaws:
    def test_proposal_requires_evidence(self) -> None:
        with pytest.raises(QcaeValidationError, match="cite evidence"):
            ContractAmendmentProposal(
                proposal_id="prop-001",
                contract_id="CAP-REPLAY-001",
                contract_version=1,
                plan_id="plan-replay-001",
                discovered_need="every implementation requires an ordering key",
                proposed_change="add required input 'ordering_key'",
                evidence_ids=(),
            ).validate()

    def test_proposal_from_another_contract_refused_on_plan(self) -> None:
        proposal = ContractAmendmentProposal(
            proposal_id="prop-001",
            contract_id="CAP-OTHER-002",
            contract_version=1,
            plan_id="plan-replay-001",
            discovered_need="every implementation requires an ordering key",
            proposed_change="add required input 'ordering_key'",
            evidence_ids=("ev-001",),
        )
        with pytest.raises(QcaeValidationError, match="not the plan's"):
            make_discovery_plan(**plan_kwargs(amendment_proposals=(proposal,)))

    def test_proposal_attached_to_plan_is_proposal_only(self) -> None:
        proposal = ContractAmendmentProposal(
            proposal_id="prop-001",
            contract_id="CAP-REPLAY-001",
            contract_version=1,
            plan_id="plan-replay-001",
            discovered_need="every implementation requires an ordering key",
            proposed_change="add required input 'ordering_key'",
            evidence_ids=("ev-001",),
        )
        plan = make_discovery_plan(**plan_kwargs(amendment_proposals=(proposal,)))
        assert plan.amendment_proposals[0].status is AmendmentProposalStatus.PROPOSED
        # No enacted state is reachable from the discovery layer (canon 2.1.14).
        assert {state.name for state in AmendmentProposalStatus} == {"PROPOSED", "WITHDRAWN"}


# -- canon 2.1.10: saturation metrics ---------------------------------------


class TestSaturationLaws:
    def test_negative_counter_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="non-negative integer"):
            SaturationMetrics(results_inspected=-1).validate()

    def test_saturation_requires_reason(self) -> None:
        with pytest.raises(QcaeValidationError, match="recorded reason"):
            SaturationMetrics(saturated=True).validate()

    def test_marginal_novelty_rate_is_derived(self) -> None:
        metrics = SaturationMetrics(
            queries_executed=6,
            results_inspected=40,
            new_candidates=2,
            new_implementation_families=1,
            new_specifications=1,
            saturated=True,
            saturation_reason="three consecutive families returned only known candidates",
        )
        assert metrics.marginal_novelty_rate == pytest.approx(0.1)
        assert SaturationMetrics().marginal_novelty_rate == 0.0


# -- budget envelope --------------------------------------------------------


class TestBudgetLaws:
    def test_zero_spend_envelope_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="integer >= 1"):
            DiscoveryBudget(
                max_queries=0,
                max_results_inspected=10,
                max_source_calls=2,
                max_wall_clock_seconds=60,
            ).validate()

    def test_negative_cost_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="max_cost_usd"):
            DiscoveryBudget(
                max_queries=1,
                max_results_inspected=1,
                max_source_calls=1,
                max_wall_clock_seconds=1,
                max_cost_usd=-0.01,
            ).validate()

    def test_identity_and_policy_version_are_required(self) -> None:
        with pytest.raises(QcaeValidationError, match="created_by"):
            make_discovery_plan(**plan_kwargs(created_by=""))
        with pytest.raises(QcaeValidationError, match="policy_version"):
            make_discovery_plan(**plan_kwargs(policy_version=""))

    def test_plan_requires_atom_scope(self) -> None:
        with pytest.raises(QcaeValidationError, match="at least one atom"):
            make_discovery_plan(**plan_kwargs(atom_ids=()))
