"""P3-T02-C01/C02/C03 — GitHub discovery adapter, policy-gated egress, statuses.

Covers:
- C01: injectable transport, provider-specific adapter behind the DiscoverySourceAdapter
  port, no default live network.
- C02: the seven pre-flight egress gates (baseline, assert_external_execution_authorized,
  plan/query identity, source-class/scope allocation, AuthorityProvider may_discover
  decision, budgets), fail-closed with zero transport calls on any denial.
- C03: typed provider outcome truth (OK/NO_RESULTS/PARTIAL_RESULTS/RATE_LIMITED/
  AUTH_FAILURE/PROVIDER_FAILURE/UNSUPPORTED_QUERY/NOT_CONFIGURED), pagination and
  budget behaviour, and C04 provenance firewall (no verification, mutable anchor
  represented as missing, popularity as raw signal only).
"""

from __future__ import annotations

from qcae.core.decisions.authority import (
    AuthorityDecision,
    AuthorityOutcome,
    AuthorityProvider,
    PolicyAction,
    AuthorityRequest,
)
from qcae.core.discovery.lead import (
    AdapterStatus,
    CandidateKind,
    VerificationLevel,
)
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

from qcae.discovery.internal.baseline import (
    InternalBaselineClassification,
    InternalBaselineRecord,
)
from qcae.core.ports.discovery import DiscoveryQuery
from qcae.discovery.github.adapter import (
    GitHubDiscoveryAdapter,
    MISSING_REVISION,
    FakeGitHubTransport,
    GitHubResponse,
)

ATOM = "atom-causal-ordering"
CAP = "CAP-REPLAY-001"
QUERY_ID = "fam-behavioral:causal-ordering"
FAMILY = "fam-behavioral"
CONCRETE_QUERY = "causal ordering library"


# -- fakes -------------------------------------------------------------------


class FakeAuthorityProvider(AuthorityProvider):
    """Programmable authority decision for may_discover."""

    def __init__(self, outcome=AuthorityOutcome.GRANT, reason="granted") -> None:
        self.outcome = outcome
        self.reason = reason
        self.requests: list = []

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


def plan(**overrides) -> object:
    """A valid DiscoveryPlan allocating GITHUB_REPOSITORY_CODE for ATOM."""
    kwargs = dict(
        discovery_plan_id="plan-001",
        contract_id=CAP,
        contract_version=1,
        atom_ids=(ATOM,),
        internal_baseline_queries=("internal:capability-registry:" + CAP,),
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
                family_id=FAMILY,
                kind=QueryFamilyKind.BEHAVIORAL,
                hypothesis_ids=("hyp-focused",),
                terms=(CONCRETE_QUERY,),
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
                max_tier=CostTier.TIER_3_SOURCE_TREE,
            ),
        ),
        budget=DiscoveryBudget(
            max_queries=10,
            max_results_inspected=50,
            max_source_calls=10,
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
    kwargs.update(overrides)
    return make_discovery_plan(**kwargs)


def query(**overrides) -> DiscoveryQuery:
    kwargs = dict(
        family_id=FAMILY,
        atom_id=ATOM,
        semantic_concept="causal event ordering",
        concrete_query=CONCRETE_QUERY,
        source_class=SourceClass.GITHUB_REPOSITORY_CODE,
        max_results=20,
        max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
        cursor="",
    )
    kwargs.update(overrides)
    kwargs.setdefault(
        "query_id",
        kwargs["family_id"] + ":" + kwargs["concrete_query"].strip().replace(" ", "-"),
    )
    return DiscoveryQuery(**kwargs)


# Baseline records: coverage must be internally consistent (validate checks it).


def baseline_record(*, covered_atoms, external_target_atoms, verdict) -> InternalBaselineRecord:
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
    return baseline_record(
        covered_atoms=(ATOM,), external_target_atoms=(),
        verdict=InternalBaselineClassification.FULLY_SATISFIED_INTERNAL,
    )


def partially_satisfied():
    return baseline_record(
        covered_atoms=(), external_target_atoms=(ATOM,),
        verdict=InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL,
    )


def no_internal():
    return baseline_record(
        covered_atoms=(), external_target_atoms=(ATOM,),
        verdict=InternalBaselineClassification.NO_INTERNAL_CAPABILITY_FOUND,
    )


def make_adapter(
    *,
    transport=None,
    authority=None,
    baseline=None,
    plan_obj=None,
    clock="2026-09-21T12:00:05Z",
    max_results_cap=None,
) -> GitHubDiscoveryAdapter:
    return GitHubDiscoveryAdapter(
        transport=transport or FakeGitHubTransport(),
        authority_provider=authority,
        baseline=baseline,
        plan=plan_obj or plan(),
        clock=lambda: clock,
        max_results_cap=max_results_cap,
    )


# -- C01: transport injection + port contract -------------------------------


class TestAdapterPortContract:
    def test_adapter_id_and_source_class(self) -> None:
        adapter = make_adapter(authority=FakeAuthorityProvider(), baseline=partially_satisfied())
        assert adapter.adapter_id == "github-discovery"
        assert adapter.source_class is SourceClass.GITHUB_REPOSITORY_CODE

    def test_transport_is_injected_and_used(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        response = adapter.search(query())
        # Gates pass; the injected transport was called exactly once.
        assert len(transport.repository_calls) == 1
        assert response.status is not AdapterStatus.NOT_CONFIGURED

    def test_only_github_source_class_is_served(self) -> None:
        adapter = make_adapter(authority=FakeAuthorityProvider(), baseline=partially_satisfied())
        q = query(source_class=SourceClass.PACKAGE_ECOSYSTEM)
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY


# -- C02: egress authority gates -------------------------------------------


class TestEgressGates:
    def _transport_calls(self, adapter) -> int:
        return len(adapter._transport.repository_calls) + len(adapter._transport.code_calls)

    def test_fully_satisfied_baseline_blocks_all_external_search(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(transport=transport, authority=FakeAuthorityProvider(), baseline=fully_satisfied())
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert self._transport_calls(adapter) == 0
        assert "baseline" in outcome.message.lower()

    def test_no_baseline_is_not_configured(self) -> None:
        adapter = make_adapter(authority=FakeAuthorityProvider(), baseline=None)
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert self._transport_calls(adapter) == 0

    def test_authority_absent_is_not_configured(self) -> None:
        adapter = make_adapter(authority=None, baseline=partially_satisfied())
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert self._transport_calls(adapter) == 0

    def test_authority_deny_causes_zero_transport_calls(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(outcome=AuthorityOutcome.DENY, reason="policy denies egress"),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert self._transport_calls(adapter) == 0
        assert "zero transport calls" in outcome.message

    def test_authority_require_more_evidence_causes_zero_transport_calls(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(outcome=AuthorityOutcome.REQUEST_MORE_EVIDENCE, reason="needs review"),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert self._transport_calls(adapter) == 0

    def test_wrong_query_identity_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        q = query(query_id="not-a-planned-query")
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert self._transport_calls(adapter) == 0

    def test_atom_outside_plan_scope_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        q = query(atom_id="atom-not-in-plan")
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert self._transport_calls(adapter) == 0

    def test_undeclared_concrete_query_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        q = query(concrete_query="something never planned")
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert self._transport_calls(adapter) == 0

    def test_unallocated_source_class_refused(self) -> None:
        transport = FakeGitHubTransport()
        # Family does not reference GITHUB and GITHUB has no enabled allocation.
        valid_without_github = plan(
            query_families=(
                QueryFamilyRecord(
                    family_id=FAMILY,
                    kind=QueryFamilyKind.BEHAVIORAL,
                    hypothesis_ids=("hyp-focused",),
                    terms=(CONCRETE_QUERY,),
                    source_classes=(SourceClass.INTERNAL_REGISTRY_CODE,
                                    SourceClass.PACKAGE_ECOSYSTEM),
                ),
            ),
            source_allocations=(
                SourceAllocation(
                    source_class=SourceClass.INTERNAL_REGISTRY_CODE,
                    budget_share=0.5,
                    max_tier=CostTier.TIER_0_MEMORY_LOOKUP,
                ),
                SourceAllocation(
                    source_class=SourceClass.PACKAGE_ECOSYSTEM,
                    budget_share=0.5,
                    max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
                ),
            ),
            diversity_requirements=DiversityRequirement(
                max_single_source_share=0.9, min_distinct_source_classes=2
            ),
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
            plan_obj=valid_without_github,
        )
        q = query()
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert self._transport_calls(adapter) == 0

    def test_all_gates_pass_calls_transport_once(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        # One repository page plus one code-search page (effective tier permits code search).
        assert self._transport_calls(adapter) == 2
        assert len(transport.repository_calls) == 1
        assert transport.repository_calls[0][0] == CONCRETE_QUERY

    def test_may_discover_request_names_the_plan_and_action(self) -> None:
        authority = FakeAuthorityProvider()
        adapter = make_adapter(
            authority=authority, baseline=partially_satisfied(),
        )
        adapter.search(query())
        assert len(authority.requests) == 1
        req = authority.requests[0]
        assert req.action is PolicyAction.MAY_DISCOVER
        assert req.subject_id == CAP
        assert req.context["budget_ref"] == "plan-001"

    def test_budget_exhaustion_blocks_transport(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
            plan_obj=plan(budget=DiscoveryBudget(max_queries=1, max_results_inspected=50,
                                                max_source_calls=10, max_wall_clock_seconds=300)),
        )
        # First search consumes the query budget.
        first = adapter.search(query())
        assert first.status is not AdapterStatus.RATE_LIMITED
        calls_before = self._transport_calls(adapter)
        # Second search is blocked by the exhausted query budget: zero new calls.
        second = adapter.search(query())
        assert second.status is AdapterStatus.RATE_LIMITED
        assert self._transport_calls(adapter) == calls_before


# -- C03: provider outcome truth ------------------------------------------


class TestProviderStatuses:
    def _item(self, full_name="owner/repo", stars=42):
        return {
            "full_name": full_name,
            "html_url": "https://github.com/" + full_name,
            "stargazers_count": stars,
            "forks_count": 7,
            "language": "Python",
            "license": {"spdx_id": "MIT"},
            "updated_at": "2026-01-01T00:00:00Z",
        }

    def _seeded(self, transport, items, status_code=200, headers=None, total_count=None):
        body = {"items": items, "total_count": len(items) if total_count is None else total_count}
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=status_code, headers=headers or {}, body=body
        )

    def test_ok_with_actual_leads(self) -> None:
        transport = FakeGitHubTransport()
        self._seeded(transport, [self._item(), self._item("other/tool")])
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert outcome.status is AdapterStatus.OK
        assert len(outcome.leads) == 2
        assert outcome.results_inspected == 2
        # One repository page plus one code-search page (effective tier permits code search).
        assert outcome.pages_inspected == 2
        assert len(transport.repository_calls) == 1
        assert outcome.exhaustive is True

    def test_empty_successful_response_is_no_results_not_ok(self) -> None:
        transport = FakeGitHubTransport()
        self._seeded(transport, [])
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert outcome.status is AdapterStatus.NO_RESULTS
        assert outcome.leads == ()
        # One repository page plus one code-search page (effective tier permits code search).
        assert outcome.pages_inspected == 2

    def test_401_is_auth_failure(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=401, headers={}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.AUTH_FAILURE
        assert outcome.leads == ()

    def test_403_is_auth_failure(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=403, headers={}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.AUTH_FAILURE

    def test_429_is_rate_limited(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=429, headers={"X-RateLimit-Reset": "1700000000"}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.RATE_LIMITED
        # C06: retry_after_seconds is a duration, never the raw X-RateLimit-Reset epoch.
        assert outcome.retry_after_seconds is not None
        assert outcome.retry_after_seconds != 1700000000

    def test_500_is_provider_failure(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=500, headers={}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PROVIDER_FAILURE

    def test_malformed_payload_is_provider_failure(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body="not a json object"
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PROVIDER_FAILURE

    def test_incomplete_results_is_partial_results_with_note(self) -> None:
        transport = FakeGitHubTransport()
        body = {"items": [self._item()], "total_count": 5, "incomplete_results": True}
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body=body
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert outcome.completeness_note.strip()
        assert outcome.exhaustive is False

    def test_result_limit_exhaustion_is_partial_results(self) -> None:
        transport = FakeGitHubTransport()
        body = {"items": [self._item(), self._item("b/repo")], "total_count": 100}
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body=body
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
            max_results_cap=1,
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert len(outcome.leads) == 1
        assert "result limit reached" in outcome.completeness_note

    def test_pagination_tracks_pages_inspected(self) -> None:
        transport = FakeGitHubTransport()
        # Page 1 has all results (total_count == 1) -> one page inspected.
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [self._item()], "total_count": 1}
        )
        transport._responses[("repository", CONCRETE_QUERY, 2)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [], "total_count": 1}
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.pages_inspected == 1
        assert outcome.results_inspected == 1


# -- C04: provenance firewall ----------------------------------------------


class TestProvenanceFirewall:
    def _item(self, full_name="owner/repo", stars=42):
        return {
            "full_name": full_name,
            "html_url": "https://github.com/" + full_name,
            "stargazers_count": stars,
            "forks_count": 7,
            "language": "Python",
            "license": {"spdx_id": "MIT"},
            "updated_at": "2026-01-01T00:00:00Z",
        }

    def _seeded(self, transport, items, status_code=200, headers=None):
        body = {"items": items, "total_count": len(items)}
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=status_code, headers=headers or {}, body=body
        )

    def test_lead_carries_exact_query_lineage(self) -> None:
        transport = FakeGitHubTransport()
        self._seeded(transport, [self._item()])
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        lead = outcome.leads[0]
        assert lead.query_lineage.atom_id == ATOM
        assert lead.query_lineage.family_id == FAMILY
        assert lead.query_lineage.concrete_query == CONCRETE_QUERY
        assert lead.query_lineage.adapter_id == "github-discovery"
        assert lead.query_lineage.source_class is SourceClass.GITHUB_REPOSITORY_CODE

    def test_retrieved_revision_explicitly_missing(self) -> None:
        transport = FakeGitHubTransport()
        self._seeded(transport, [self._item()])
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        lead = adapter.search(query()).leads[0]
        assert lead.retrieved_revision == MISSING_REVISION
        assert lead.retrieved_revision == ""
        assert lead.deeper_intelligence_ready is False

    def test_lead_never_carries_verification(self) -> None:
        transport = FakeGitHubTransport()
        self._seeded(transport, [self._item()])
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        lead = adapter.search(query()).leads[0]
        assert lead.claim_verification is VerificationLevel.DISCOVERED

    def test_popularity_is_raw_signal_never_interpreted(self) -> None:
        transport = FakeGitHubTransport()
        self._seeded(transport, [self._item(stars=100000)])
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        lead = adapter.search(query()).leads[0]
        assert lead.popularity_signals["stargazers_count"] == 100000
        # No verification or ranking field is derived from popularity.
        assert lead.claim_verification is VerificationLevel.DISCOVERED

    def test_lead_is_repository_kind_with_github_locator(self) -> None:
        transport = FakeGitHubTransport()
        self._seeded(transport, [self._item("acme/causal-engine")])
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        lead = adapter.search(query()).leads[0]
        assert lead.candidate_kind is CandidateKind.REPOSITORY
        assert lead.source_locator == "github:acme/causal-engine"
        assert lead.possible_atom_matches == (ATOM,)

    def test_duplicate_identities_are_emitted_as_duplicates_not_corroboration(self) -> None:
        transport = FakeGitHubTransport()
        item = self._item("dup/repo")
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={},
            body={"items": [item, item], "total_count": 2},
        )
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.OK
        assert len(outcome.leads) == 2
        assert outcome.leads[0].source_locator == outcome.leads[1].source_locator
        # Deduplication/corroboration belongs to the merge layer, not the adapter.

    def test_raw_artifact_ref_preserved_per_page(self) -> None:
        transport = FakeGitHubTransport()
        self._seeded(transport, [self._item()])
        adapter = make_adapter(
            transport=transport,
            authority=FakeAuthorityProvider(),
            baseline=partially_satisfied(),
        )
        outcome = adapter.search(query())
        assert outcome.raw_artifact_refs
        assert all(ref.startswith("sha256:") for ref in outcome.raw_artifact_refs)
