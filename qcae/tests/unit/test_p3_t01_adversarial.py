"""P3-T02-T01 — adversarial qualification for the GitHub discovery adapter.

Deterministic attacks against a fake/injectable transport, exercising the real
adapter/transport boundaries (not private helpers). Each attack asserts that no
transport call leaks past a denied gate and that provider outcomes are typed
faithfully. Evidence is LOCAL TEST EVIDENCE (no live GitHub CI).
"""

from __future__ import annotations

from qcae.core.decisions.authority import (
    AuthorityDecision,
    AuthorityOutcome,
    AuthorityProvider,
    AuthorityRequest,
)
from qcae.discovery.internal.baseline import InternalBaselineClassification
from qcae.core.discovery.lead import VerificationLevel
from qcae.core.discovery.plan import (
    CostTier,
    DiscoveryBudget,
    DiversityRequirement,
    QueryFamilyKind,
    QueryFamilyRecord,
    SearchHypothesis,
    SearchHypothesisKind,
    SourceAllocation,
    SourceClass,
    StopCondition,
    StopRule,
    make_discovery_plan,
)
from qcae.discovery.internal.baseline import InternalBaselineRecord
from qcae.core.ports.discovery import AdapterStatus, DiscoveryQuery
from qcae.discovery.github.adapter import (
    GitHubDiscoveryAdapter,
    FakeGitHubTransport,
    GitHubResponse,
)

ATOM = "atom-causal-ordering"
ATOM_B = "atom-second"
CAP = "CAP-REPLAY-001"
FAMILY = "fam-behavioral"
CONCRETE_QUERY = "causal ordering library"


# -- reusable fixtures -------------------------------------------------------


class FakeAuthorityProvider(AuthorityProvider):
    def __init__(self, outcome=AuthorityOutcome.GRANT, reason="granted") -> None:
        self.outcome = outcome
        self.reason = reason
        self.requests = []

    def decide(self, request: AuthorityRequest) -> AuthorityDecision:
        self.requests.append(request)
        return AuthorityDecision(
            decision_id="dec-1",
            request_ref=request.request_id,
            action=request.action,
            outcome=self.outcome,
            decided_by="test-policy",
            decided_at="2026-09-21T12:00:00Z",
            reason=self.reason,
        )


def plan(*, atom_ids=(ATOM,), with_github=True) -> object:
    github_alloc = (
        SourceAllocation(
            source_class=SourceClass.GITHUB_REPOSITORY_CODE,
            budget_share=0.5,
            max_tier=CostTier.TIER_3_SOURCE_TREE,
        ),
    ) if with_github else ()
    internal_alloc = (
        SourceAllocation(
            source_class=SourceClass.INTERNAL_REGISTRY_CODE,
            budget_share=0.5,
            max_tier=CostTier.TIER_0_MEMORY_LOOKUP,
        ),
    )
    return make_discovery_plan(
        discovery_plan_id="plan-001",
        contract_id=CAP,
        contract_version=1,
        atom_ids=atom_ids,
        internal_baseline_queries=("internal:capability-registry:" + CAP,),
        search_hypotheses=(
            SearchHypothesis(
                hypothesis_id="hyp-focused",
                atom_ids=atom_ids,
                kind=SearchHypothesisKind.FOCUSED_LIBRARY,
                statement="may exist as a focused library",
                expected_source_classes=(
                    (SourceClass.GITHUB_REPOSITORY_CODE,) if with_github else ()
                ),
            ),
        ),
        query_families=(
            QueryFamilyRecord(
                family_id=FAMILY,
                kind=QueryFamilyKind.BEHAVIORAL,
                hypothesis_ids=("hyp-focused",),
                terms=(CONCRETE_QUERY,),
                source_classes=(
                    (SourceClass.INTERNAL_REGISTRY_CODE, SourceClass.GITHUB_REPOSITORY_CODE)
                    if with_github
                    else (SourceClass.INTERNAL_REGISTRY_CODE,)
                ),
            ),
        ),
        source_allocations=internal_alloc + github_alloc,
        budget=DiscoveryBudget(
            max_queries=10, max_results_inspected=50, max_source_calls=10,
            max_wall_clock_seconds=300,
        ),
        cost_tier_ceiling=CostTier.TIER_3_SOURCE_TREE,
        diversity_requirements=DiversityRequirement(),
        stop_rules=(
            StopRule(condition=StopCondition.BUDGET_CEILING_REACHED),
            StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),
        ),
        created_by="qcae-discovery-planner",
        policy_version="discovery-ranking-policy-1.0",
        single_route_justification="single route recorded for this fixture",
    )


def baseline(*, covered_atoms, external_target_atoms, verdict) -> InternalBaselineRecord:
    requested = tuple(covered_atoms) + tuple(external_target_atoms)
    return InternalBaselineRecord(
        baseline_id="baseline-001",
        capability_id=CAP,
        contract_id=CAP,
        contract_version=1,
        requested_atoms=requested,
        covered_atoms=tuple(covered_atoms),
        missing_atoms=tuple(external_target_atoms),
        external_target_atoms=tuple(external_target_atoms),
        classifications=(verdict,),
        sufficiency_verdict=verdict,
        query_provenance=("internal:capability-registry:" + CAP,),
        created_at="2026-09-21T12:00:00Z",
        created_by="qcae-internal-discovery",
    )


def fully_satisfied():
    return baseline(
        covered_atoms=(ATOM,), external_target_atoms=(),
        verdict=InternalBaselineClassification.FULLY_SATISFIED_INTERNAL,
    )


def partially_satisfied():
    return baseline(
        covered_atoms=(), external_target_atoms=(ATOM,),
        verdict=InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL,
    )


def partially_satisfied_two_atoms():
    # ATOM covered, ATOM_B external -> only ATOM_B may be searched externally.
    return baseline(
        covered_atoms=(ATOM,), external_target_atoms=(ATOM_B,),
        verdict=InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL,
    )


def make_adapter(*, transport, authority, baseline_record, plan_obj, max_results_cap=None):
    return GitHubDiscoveryAdapter(
        transport=transport,
        authority_provider=authority,
        baseline=baseline_record,
        plan=plan_obj,
        clock=lambda: "2026-09-21T12:00:05Z",
        max_results_cap=max_results_cap,
    )


def query(*, atom_id=ATOM, family_id=FAMILY, concrete_query=CONCRETE_QUERY,
          source_class=SourceClass.GITHUB_REPOSITORY_CODE, query_id=None):
    if query_id is None:
        query_id = family_id + ":" + concrete_query.strip().replace(" ", "-")
    return DiscoveryQuery(
        query_id=query_id,
        family_id=family_id,
        atom_id=atom_id,
        semantic_concept="causal event ordering",
        concrete_query=concrete_query,
        source_class=source_class,
        max_results=20,
        max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
        cursor="",
    )


def item(full_name="owner/repo", stars=42):
    return {
        "full_name": full_name,
        "html_url": "https://github.com/" + full_name,
        "stargazers_count": stars,
        "forks_count": 7,
        "language": "Python",
        "license": {"spdx_id": "MIT"},
        "updated_at": "2026-01-01T00:00:00Z",
    }


# -- adversarial attacks -----------------------------------------------------


class TestEgressDenialAttacks:
    def test_baseline_fully_satisfied_zero_egress(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=fully_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport.repository_calls == []

    def test_partially_satisfied_only_uncovered_atom_searched(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={},
            body={"items": [item()], "total_count": 1},
        )
        # ATOM is covered (blocked), ATOM_B is external (allowed).
        plan_b = make_discovery_plan(
            discovery_plan_id="plan-001", contract_id=CAP, contract_version=1,
            atom_ids=(ATOM, ATOM_B),
            internal_baseline_queries=("internal:capability-registry:" + CAP,),
            search_hypotheses=(
                SearchHypothesis(
                    hypothesis_id="hyp-focused", atom_ids=(ATOM, ATOM_B),
                    kind=SearchHypothesisKind.FOCUSED_LIBRARY,
                    statement="focused library",
                    expected_source_classes=(SourceClass.GITHUB_REPOSITORY_CODE,),
                ),
            ),
            query_families=(
                QueryFamilyRecord(
                    family_id=FAMILY, kind=QueryFamilyKind.BEHAVIORAL,
                    hypothesis_ids=("hyp-focused",),
                    terms=(CONCRETE_QUERY, CONCRETE_QUERY + " b"),
                    source_classes=(SourceClass.INTERNAL_REGISTRY_CODE,
                                    SourceClass.GITHUB_REPOSITORY_CODE),
                ),
            ),
            source_allocations=(
                SourceAllocation(source_class=SourceClass.INTERNAL_REGISTRY_CODE,
                                 budget_share=0.5, max_tier=CostTier.TIER_0_MEMORY_LOOKUP),
                SourceAllocation(source_class=SourceClass.GITHUB_REPOSITORY_CODE,
                                 budget_share=0.5, max_tier=CostTier.TIER_3_SOURCE_TREE),
            ),
            budget=DiscoveryBudget(max_queries=10, max_results_inspected=50,
                                   max_source_calls=10, max_wall_clock_seconds=300),
            cost_tier_ceiling=CostTier.TIER_3_SOURCE_TREE,
            diversity_requirements=DiversityRequirement(),
            stop_rules=(
                StopRule(condition=StopCondition.BUDGET_CEILING_REACHED),
                StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),
            ),
            created_by="qcae-discovery-planner",
            policy_version="discovery-ranking-policy-1.0",
            single_route_justification="fixture",
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied_two_atoms(), plan_obj=plan_b,
        )
        # Covered atom: blocked, zero transport calls.
        covered = adapter.search(query(atom_id=ATOM))
        assert covered.status is AdapterStatus.NOT_CONFIGURED
        assert transport.repository_calls == []
        # Uncovered atom: allowed, transport called.
        qb = query(atom_id=ATOM_B, concrete_query=CONCRETE_QUERY + " b")
        uncovered = adapter.search(qb)
        assert uncovered.status is not AdapterStatus.NOT_CONFIGURED
        assert len(transport.repository_calls) == 1
        assert transport.repository_calls[0][0] == CONCRETE_QUERY + " b"

    def test_wrong_query_identity_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        q = query(query_id="not-a-planned-query")
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert transport.repository_calls == []

    def test_atom_outside_plan_scope_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        q = query(atom_id="atom-not-in-plan")
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert transport.repository_calls == []

    def test_undeclared_concrete_query_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        q = query(concrete_query="something never planned")
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert transport.repository_calls == []

    def test_wrong_source_class_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(with_github=True),
        )
        q = query(source_class=SourceClass.PACKAGE_ECOSYSTEM)
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert transport.repository_calls == []

    def test_unallocated_source_class_refused(self) -> None:
        transport = FakeGitHubTransport()
        valid_without_github = make_discovery_plan(
            discovery_plan_id="plan-001", contract_id=CAP, contract_version=1,
            atom_ids=(ATOM,),
            internal_baseline_queries=("internal:capability-registry:" + CAP,),
            search_hypotheses=(
                SearchHypothesis(
                    hypothesis_id="hyp-focused", atom_ids=(ATOM,),
                    kind=SearchHypothesisKind.FOCUSED_LIBRARY,
                    statement="focused library",
                    expected_source_classes=(),
                ),
            ),
            query_families=(
                QueryFamilyRecord(
                    family_id=FAMILY, kind=QueryFamilyKind.BEHAVIORAL,
                    hypothesis_ids=("hyp-focused",),
                    terms=(CONCRETE_QUERY,),
                    source_classes=(SourceClass.INTERNAL_REGISTRY_CODE,
                                    SourceClass.PACKAGE_ECOSYSTEM),
                ),
            ),
            source_allocations=(
                SourceAllocation(source_class=SourceClass.INTERNAL_REGISTRY_CODE,
                                 budget_share=0.5, max_tier=CostTier.TIER_0_MEMORY_LOOKUP),
                SourceAllocation(source_class=SourceClass.PACKAGE_ECOSYSTEM,
                                 budget_share=0.5, max_tier=CostTier.TIER_1_METADATA_SNIPPETS),
            ),
            budget=DiscoveryBudget(max_queries=10, max_results_inspected=50,
                                   max_source_calls=10, max_wall_clock_seconds=300),
            cost_tier_ceiling=CostTier.TIER_3_SOURCE_TREE,
            diversity_requirements=DiversityRequirement(
                max_single_source_share=0.9, min_distinct_source_classes=2),
            stop_rules=(
                StopRule(condition=StopCondition.BUDGET_CEILING_REACHED),
                StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),
            ),
            created_by="qcae-discovery-planner",
            policy_version="discovery-ranking-policy-1.0",
            single_route_justification="fixture",
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=valid_without_github,
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert transport.repository_calls == []

    def test_deny_decision_zero_transport_calls(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(outcome=AuthorityOutcome.DENY, reason="denied"),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport.repository_calls == []
        assert "zero transport calls" in outcome.message

    def test_request_more_evidence_zero_transport_calls(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(outcome=AuthorityOutcome.REQUEST_MORE_EVIDENCE, reason="review"),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport.repository_calls == []

    def test_missing_provider_not_configured(self) -> None:
        adapter = make_adapter(
            transport=FakeGitHubTransport(), authority=None,
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED

    def test_no_baseline_not_configured(self) -> None:
        adapter = make_adapter(
            transport=FakeGitHubTransport(), authority=FakeAuthorityProvider(),
            baseline_record=None, plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED


class TestProviderStatusMatrix:
    def test_empty_successful_response_is_no_results(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [], "total_count": 0},
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NO_RESULTS
        assert outcome.leads == ()

    def test_401_and_403_are_auth_failure_distinct_from_rate_limit(self) -> None:
        for code in (401, 403):
            transport = FakeGitHubTransport()
            transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
                status_code=code, headers={}, body={},
            )
            adapter = make_adapter(
                transport=transport, authority=FakeAuthorityProvider(),
                baseline_record=partially_satisfied(), plan_obj=plan(),
            )
            outcome = adapter.search(query())
            assert outcome.status is AdapterStatus.AUTH_FAILURE, code
            assert outcome.leads == ()

    def test_429_rate_limit_exhaustion(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=429, headers={"X-RateLimit-Reset": "1700000000"}, body={},
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.RATE_LIMITED
        assert outcome.retry_after_seconds == 1700000000

    def test_incomplete_pagination_partial_with_note(self) -> None:
        transport = FakeGitHubTransport()
        body = {"items": [item()], "total_count": 9, "incomplete_results": True}
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body=body,
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert outcome.completeness_note.strip()
        assert outcome.exhaustive is False

    def test_result_limit_exhaustion_is_partial_not_ok(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={},
            body={"items": [item(), item("b/repo")], "total_count": 2},
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
            max_results_cap=1,
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert len(outcome.leads) == 1
        assert "result limit reached" in outcome.completeness_note

    def test_malformed_payload_provider_failure_not_no_results(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body="not-an-object",
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PROVIDER_FAILURE
        assert outcome.leads == ()

    def test_no_provider_failure_becomes_no_results(self) -> None:
        for code in (401, 403, 429, 500):
            transport = FakeGitHubTransport()
            transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
                status_code=code, headers={}, body={},
            )
            adapter = make_adapter(
                transport=transport, authority=FakeAuthorityProvider(),
                baseline_record=partially_satisfied(), plan_obj=plan(),
            )
            outcome = adapter.search(query())
            assert outcome.status is not AdapterStatus.NO_RESULTS, code


class TestProvenanceAttacks:
    def test_duplicate_identities_emitted_not_corroborated(self) -> None:
        transport = FakeGitHubTransport()
        it = item("dup/repo")
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [it, it], "total_count": 2},
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert len(outcome.leads) == 2
        assert outcome.leads[0].source_locator == outcome.leads[1].source_locator

    def test_missing_mutable_revision_anchor_explicit(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1},
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        lead = adapter.search(query()).leads[0]
        assert lead.retrieved_revision == ""
        assert lead.deeper_intelligence_ready is False

    def test_lead_lineage_binds_to_exact_query_that_found_it(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1},
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        outcome = adapter.search(query())
        lineage = outcome.leads[0].query_lineage
        assert lineage.adapter_id == "github-discovery"
        assert lineage.concrete_query == CONCRETE_QUERY
        assert lineage.atom_id == ATOM
        assert lineage.family_id == FAMILY
        assert lineage.source_class is SourceClass.GITHUB_REPOSITORY_CODE
        # A different query produces a different lineage; identity is exact.
        other_lineage = query(concrete_query="totally different query").lineage_for(
            "github-discovery"
        )
        assert other_lineage.concrete_query != lineage.concrete_query

    def test_popularity_does_not_elevate_verification(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={},
            body={"items": [item(stars=999999)], "total_count": 1},
        )
        adapter = make_adapter(
            transport=transport, authority=FakeAuthorityProvider(),
            baseline_record=partially_satisfied(), plan_obj=plan(),
        )
        lead = adapter.search(query()).leads[0]
        assert lead.popularity_signals["stargazers_count"] == 999999
        assert lead.claim_verification is VerificationLevel.DISCOVERED
        assert "claim_verification" not in lead.to_dict()
