"""P3-C02 — discovery adapter contract: leads, typed outcomes, registry.

Covers canon 2.1.11/2.1.4 (intake + lineage), 2.2.12/2.2.13 (pagination and
partial search honesty), 2.3.12 ("should not emit VERIFIED_CAPABILITY"), Book V
15.3 (adapter isolation, failure semantics) and the standalone-first rule that an
absent provider is reported rather than imitated.
"""

from __future__ import annotations

import pytest

from qcae.core.discovery import (
    AdapterStatus,
    CandidateKind,
    CandidateLead,
    CostTier,
    DiscoveryBudget,
    DiversityRequirement,
    QueryFamilyKind,
    QueryFamilyRecord,
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
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.discovery import (
    AdapterOutcome,
    DiscoveryAdapterRegistry,
    DiscoveryQuery,
    DiscoverySourceAdapter,
    make_discovery_query,
)

ATOM = "atom-causal-ordering"


# -- builders ---------------------------------------------------------------


def query(**overrides) -> DiscoveryQuery:
    kwargs = dict(
        query_id="qry-001",
        family_id="fam-behavioral",
        atom_id=ATOM,
        semantic_concept="causal event ordering",
        concrete_query="causal ordering library",
        source_class=SourceClass.GITHUB_REPOSITORY_CODE,
        max_results=10,
        max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
    )
    kwargs.update(overrides)
    return make_discovery_query(**kwargs)


def lead(adapter_id: str = "adapter-github", **overrides) -> CandidateLead:
    kwargs = dict(
        lead_id="lead-001",
        source_class=SourceClass.GITHUB_REPOSITORY_CODE,
        adapter_id=adapter_id,
        candidate_kind=CandidateKind.REPOSITORY,
        source_locator="github:owner/repo",
        discovered_at="2026-09-21T12:00:00Z",
        query_lineage=query().lineage_for(adapter_id),
        claimed_capabilities=("atom-causal-ordering",),
        possible_atom_matches=(ATOM,),
        retrieved_revision="9f2c1ab",
        language_runtime="python",
        license_claim="MIT (claimed in README)",
        activity_signals={"last_commit_days": 12},
        popularity_signals={"stars": 4100},
    )
    kwargs.update(overrides)
    return make_candidate_lead(**kwargs)


def outcome(**overrides) -> AdapterOutcome:
    kwargs = dict(
        adapter_id="adapter-github",
        source_class=SourceClass.GITHUB_REPOSITORY_CODE,
        query_id="qry-001",
        status=AdapterStatus.OK,
        retrieved_at="2026-09-21T12:00:05Z",
        leads=(lead(),),
        pages_inspected=2,
        results_inspected=20,
        duplicate_count=3,
        novelty_count=12,
        raw_artifact_refs=("sha256:deadbeefcafe",),
    )
    kwargs.update(overrides)
    return AdapterOutcome(**kwargs)


class FakeGitHubAdapter(DiscoverySourceAdapter):
    """Minimal adapter used to exercise the port laws without a provider."""

    def __init__(self, result=None) -> None:
        self._result = result
        self.closed = False

    @property
    def adapter_id(self) -> str:
        return "adapter-github"

    @property
    def source_class(self) -> SourceClass:
        return SourceClass.GITHUB_REPOSITORY_CODE

    def search(self, query: DiscoveryQuery) -> AdapterOutcome:
        if self._result is not None:
            return self._result
        return outcome(query_id=query.query_id)

    def close(self) -> None:
        self.closed = True


def minimal_plan():
    return make_discovery_plan(
        discovery_plan_id="plan-001",
        contract_id="CAP-001",
        contract_version=1,
        atom_ids=(ATOM,),
        internal_baseline_queries=("internal:capability-registry:CAP-001",),
        search_hypotheses=(
            SearchHypothesis(
                hypothesis_id="hyp-focused",
                atom_ids=(ATOM,),
                kind=SearchHypothesisKind.FOCUSED_LIBRARY,
                statement="may exist as a focused library",
                expected_source_classes=(SourceClass.GITHUB_REPOSITORY_CODE,),
            ),
        ),
        query_families=(
            QueryFamilyRecord(
                family_id="fam-behavioral",
                kind=QueryFamilyKind.BEHAVIORAL,
                hypothesis_ids=("hyp-focused",),
                terms=("causal ordering",),
                source_classes=(
                    SourceClass.INTERNAL_REGISTRY_CODE,
                    SourceClass.GITHUB_REPOSITORY_CODE,
                ),
            ),
        ),
        source_allocations=(
            SourceAllocation(
                source_class=SourceClass.INTERNAL_REGISTRY_CODE,
                budget_share=0.5,
                max_tier=CostTier.TIER_0_MEMORY_LOOKUP,
            ),
            SourceAllocation(
                source_class=SourceClass.GITHUB_REPOSITORY_CODE,
                budget_share=0.5,
                max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
            ),
        ),
        budget=DiscoveryBudget(
            max_queries=5,
            max_results_inspected=50,
            max_source_calls=5,
            max_wall_clock_seconds=300,
        ),
        cost_tier_ceiling=CostTier.TIER_1_METADATA_SNIPPETS,
        diversity_requirements=DiversityRequirement(),
        stop_rules=(
            StopRule(condition=StopCondition.BUDGET_CEILING_REACHED),
            StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),
        ),
        created_by="qcae-discovery-planner",
        policy_version="discovery-ranking-policy-1.0",
        single_route_justification="narrow route recorded for this fixture",
    )


# -- lead laws (canon 2.1.11, 2.3.12, 2.2.5) --------------------------------


class TestCandidateLeadLaws:
    def test_lead_never_carries_a_verification_level(self) -> None:
        from qcae.core.vocabulary import VerificationLevel

        candidate_lead = lead()
        assert candidate_lead.claim_verification is VerificationLevel.DISCOVERED
        assert "claim_verification" not in candidate_lead.to_dict()

    def test_lead_must_attach_to_a_capability(self) -> None:
        with pytest.raises(QcaeValidationError, match="at least one claimed capability"):
            lead(claimed_capabilities=(), possible_atom_matches=())

    def test_internal_code_lead_requires_internal_source_class(self) -> None:
        with pytest.raises(QcaeValidationError, match="internal registry"):
            lead(
                candidate_kind=CandidateKind.INTERNAL_CODE,
                query_lineage=query().lineage_for("adapter-github"),
            )

    def test_specification_lead_cannot_carry_a_license_claim(self) -> None:
        with pytest.raises(QcaeValidationError, match="license claim"):
            lead(
                candidate_kind=CandidateKind.SPECIFICATION,
                license_claim="MIT",
                source_locator="standards:RFC-0001",
            )

    def test_lead_lineage_must_match_source_and_adapter(self) -> None:
        with pytest.raises(QcaeValidationError, match="disagrees with its query lineage"):
            lead(source_class=SourceClass.PACKAGE_ECOSYSTEM)
        with pytest.raises(QcaeValidationError, match="adapter_id disagrees"):
            lead(query_lineage=query().lineage_for("adapter-other"))

    def test_deeper_intelligence_requires_immutable_revision_and_complete_search(self) -> None:
        assert lead().deeper_intelligence_ready is True
        assert lead(retrieved_revision="").deeper_intelligence_ready is False
        assert (
            lead(completeness=SearchCompleteness.PARTIAL).deeper_intelligence_ready is False
        )

    def test_signals_must_be_flat_observed_scalars(self) -> None:
        with pytest.raises(QcaeValidationError, match="scalar observed value"):
            lead(activity_signals={"commits": {"2026": 12}})

    def test_lead_round_trip(self) -> None:
        candidate_lead = lead()
        restored = CandidateLead.from_dict(candidate_lead.to_dict())
        assert restored == candidate_lead
        assert restored.query_lineage == candidate_lead.query_lineage


# -- adapter outcome laws (Book V 15.3, canon 2.2.13, 2.1.13) ---------------


class TestAdapterOutcomeLaws:
    def test_ok_requires_leads_and_pages(self) -> None:
        with pytest.raises(QcaeValidationError, match="OK requires at least one lead"):
            outcome(leads=()).validate()
        with pytest.raises(QcaeValidationError, match="pages_inspected >= 1"):
            outcome(pages_inspected=0).validate()

    def test_no_results_cannot_carry_leads(self) -> None:
        with pytest.raises(QcaeValidationError, match="NO_RESULTS cannot carry leads"):
            outcome(status=AdapterStatus.NO_RESULTS, leads=(lead(),)).validate()
        ok = outcome(
            status=AdapterStatus.NO_RESULTS, leads=(), pages_inspected=1, results_inspected=0,
            duplicate_count=0, novelty_count=0,
        )
        ok.validate()
        assert ok.is_failure is False
        assert ok.exhaustive is False

    @pytest.mark.parametrize(
        "status",
        [
            AdapterStatus.RATE_LIMITED,
            AdapterStatus.AUTH_FAILURE,
            AdapterStatus.PROVIDER_FAILURE,
            AdapterStatus.UNSUPPORTED_QUERY,
            AdapterStatus.NOT_CONFIGURED,
        ],
    )
    def test_failure_statuses_cannot_carry_leads(self, status) -> None:
        with pytest.raises(QcaeValidationError, match="cannot carry leads"):
            outcome(status=status, message="boom").validate()
        good = outcome(status=status, leads=(), message="boom", pages_inspected=0,
                       results_inspected=0, duplicate_count=0, novelty_count=0)
        good.validate()
        assert good.is_failure is True
        assert good.counts_toward_saturation is False

    def test_failure_statuses_require_a_message(self) -> None:
        with pytest.raises(QcaeValidationError, match="message"):
            outcome(status=AdapterStatus.PROVIDER_FAILURE, leads=(), pages_inspected=0,
                    results_inspected=0, duplicate_count=0, novelty_count=0).validate()

    def test_partial_results_require_a_completeness_note(self) -> None:
        with pytest.raises(QcaeValidationError, match="completeness note"):
            outcome(status=AdapterStatus.PARTIAL_RESULTS, completeness_note="").validate()
        partial = outcome(
            status=AdapterStatus.PARTIAL_RESULTS,
            completeness_note="page 2 of 7 inspected; budget exhausted",
        )
        partial.validate()
        assert partial.exhaustive is False
        assert partial.counts_toward_saturation is True

    def test_counters_are_bounded_by_results_inspected(self) -> None:
        with pytest.raises(QcaeValidationError, match="duplicate_count cannot exceed"):
            outcome(duplicate_count=21).validate()
        with pytest.raises(QcaeValidationError, match="novelty_count cannot exceed"):
            outcome(novelty_count=21).validate()
        with pytest.raises(QcaeValidationError, match="non-negative integer"):
            outcome(pages_inspected=-1).validate()

    def test_leads_must_come_from_the_responding_adapter_and_class(self) -> None:
        with pytest.raises(QcaeValidationError, match="not the responding adapter"):
            outcome(leads=(lead(adapter_id="adapter-other"),)).validate()

    def test_exhaustive_only_for_unqualified_ok(self) -> None:
        assert outcome().exhaustive is True
        assert outcome(completeness_note="first page only").exhaustive is False

    def test_outcome_round_trip_preserves_nested_leads(self) -> None:
        original = outcome()
        restored = AdapterOutcome.from_dict(original.to_dict())
        assert restored == original
        assert restored.leads[0].query_lineage == original.leads[0].query_lineage


# -- query + lineage --------------------------------------------------------


class TestDiscoveryQuery:
    def test_query_requires_positive_result_bound(self) -> None:
        with pytest.raises(QcaeValidationError, match="max_results"):
            query(max_results=0)

    def test_lineage_is_stamped_from_the_query(self) -> None:
        lineage = query().lineage_for("adapter-github")
        assert lineage.atom_id == ATOM
        assert lineage.family_id == "fam-behavioral"
        assert lineage.source_class is SourceClass.GITHUB_REPOSITORY_CODE
        assert lineage.adapter_id == "adapter-github"

    def test_query_round_trip_restores_int_enum_tier(self) -> None:
        original = query(max_tier=CostTier.TIER_3_SOURCE_TREE)
        restored = DiscoveryQuery.from_dict(original.to_dict())
        assert restored.max_tier is CostTier.TIER_3_SOURCE_TREE


# -- port helpers + registry (Book V 15.3) ----------------------------------


class TestAdapterHelpersAndRegistry:
    def test_adapter_helpers_produce_valid_typed_outcomes(self) -> None:
        adapter = FakeGitHubAdapter()
        q = query()
        assert adapter.not_configured(q).status is AdapterStatus.NOT_CONFIGURED
        assert adapter.unsupported(q).status is AdapterStatus.UNSUPPORTED_QUERY
        limited = adapter.rate_limited(q, "rate limit", retry_after_seconds=60)
        assert limited.status is AdapterStatus.RATE_LIMITED
        assert limited.retry_after_seconds == 60

    def test_registry_rejects_silent_replacement(self) -> None:
        registry = DiscoveryAdapterRegistry()
        registry.register(FakeGitHubAdapter())
        with pytest.raises(QcaeValidationError, match="already has adapter"):
            registry.register(FakeGitHubAdapter())

    def test_registry_reports_missing_source_classes_instead_of_empty_searches(self) -> None:
        plan = minimal_plan()
        registry = DiscoveryAdapterRegistry()
        assert registry.missing_source_classes(plan) == (
            SourceClass.INTERNAL_REGISTRY_CODE,
            SourceClass.GITHUB_REPOSITORY_CODE,
        )
        registry.register(FakeGitHubAdapter())
        assert registry.missing_source_classes(plan) == (SourceClass.INTERNAL_REGISTRY_CODE,)
        assert registry.adapter_for(SourceClass.GITHUB_REPOSITORY_CODE) is not None
        assert registry.adapter_for(SourceClass.WEB_DISCOVERY) is None
        assert registry.configured_source_classes() == (SourceClass.GITHUB_REPOSITORY_CODE,)

    def test_registry_close_all_releases_adapters(self) -> None:
        registry = DiscoveryAdapterRegistry()
        adapter = FakeGitHubAdapter()
        registry.register(adapter)
        assert registry.close_all() == ["adapter-github"]
        assert adapter.closed is True
