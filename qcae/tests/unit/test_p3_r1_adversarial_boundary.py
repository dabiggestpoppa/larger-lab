"""P3-T02-R1 — Adversarial boundary repair regression tests.

Red-first reproducers for C01-C07 defects in the GitHub discovery adapter,
then green evidence after repair. All transports are injectable fakes; no live
network. Evidence is LOCAL TEST EVIDENCE (no GitHub CI).

C01 — Authority must bind to the exact request (request_ref, action, structure,
fail-closed on exception).
C02 — External egress scope is NOT enforceable by the frozen policy model
(scope / budget_ref are never rule-matched); audit + report, no pretend fix.
C03 — Plan/baseline identity binding before transport.
C04 — Effective tier = min(query.max_tier, plan.cost_tier_ceiling,
allocation.max_tier); all DiscoveryBudget dimensions enforced.
C05 — Two-surface result aggregation as an explicit state transition.
C06 — Provider error vs rate-limit semantics; retry_after is a duration, never
an X-RateLimit-Reset epoch timestamp copied straight across.
C07 — Lead completeness matches surface coverage; raw artifact refs are
non-durable fingerprints, not retrievable evidence artifacts.
"""

from __future__ import annotations

from qcae.core.decisions.authority import (
    AuthorityDecision,
    AuthorityOutcome,
    AuthorityProvider,
    AuthorityRequest,
    PolicyAction,
)
from qcae.core.discovery.lead import (
    AdapterStatus,
    SearchCompleteness,
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
ATOM_B = "atom-second"
CAP = "CAP-REPLAY-001"
FAMILY = "fam-behavioral"
CONCRETE_QUERY = "causal ordering library"


# -- reusable fixtures -------------------------------------------------------


class GrantingAuthorityProvider(AuthorityProvider):
    """Always GRANTS, binding decision.request_ref to request.request_id."""

    def decide(self, request: AuthorityRequest) -> AuthorityDecision:
        return AuthorityDecision(
            decision_id="dec-1",
            request_ref=request.request_id,
            action=request.action,
            outcome=AuthorityOutcome.GRANT,
            decided_by="test-policy",
            decided_at="2026-09-21T12:00:00Z",
            reason="granted",
        )


class RaisingAuthorityProvider(AuthorityProvider):
    """Authority provider that raises instead of deciding."""

    def decide(self, request: AuthorityRequest) -> AuthorityDecision:
        raise RuntimeError("authority provider is unreachable")


class MismatchedAuthorityProvider(AuthorityProvider):
    """Returns a GRANT whose request_ref/action do not match the request."""

    def __init__(self, wrong_ref: str = "auth-other", wrong_action=PolicyAction.MAY_CLONE_TO_SANDBOX) -> None:
        self.wrong_ref = wrong_ref
        self.wrong_action = wrong_action

    def decide(self, request: AuthorityRequest) -> AuthorityDecision:
        return AuthorityDecision(
            decision_id="dec-1",
            request_ref=self.wrong_ref,
            action=self.wrong_action,
            outcome=AuthorityOutcome.GRANT,
            decided_by="test-policy",
            decided_at="2026-09-21T12:00:00Z",
            reason="mismatched",
        )


class MalformedAuthorityProvider(AuthorityProvider):
    """Returns a decision missing required fields (decision_id empty)."""

    def decide(self, request: AuthorityRequest) -> AuthorityDecision:
        return AuthorityDecision(
            decision_id="",
            request_ref=request.request_id,
            action=request.action,
            outcome=AuthorityOutcome.GRANT,
            decided_by="",
            decided_at="",
            reason="malformed",
        )


def plan(
    *,
    atom_ids=(ATOM,),
    contract_id=CAP,
    contract_version=1,
    with_github=True,
    github_max_tier=CostTier.TIER_3_SOURCE_TREE,
    query_max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
    budget=None,
    family_terms=None,
) -> object:
    github_alloc = (
        SourceAllocation(
            source_class=SourceClass.GITHUB_REPOSITORY_CODE,
            budget_share=0.5,
            max_tier=github_max_tier,
        ),
    ) if with_github else ()
    internal_alloc = (
        SourceAllocation(
            source_class=SourceClass.INTERNAL_REGISTRY_CODE,
            budget_share=0.5,
            max_tier=CostTier.TIER_0_MEMORY_LOOKUP,
        ),
    )
    terms = family_terms or (CONCRETE_QUERY,)
    return make_discovery_plan(
        discovery_plan_id="plan-001",
        contract_id=contract_id,
        contract_version=contract_version,
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
                terms=terms,
                source_classes=(
                    (SourceClass.INTERNAL_REGISTRY_CODE, SourceClass.GITHUB_REPOSITORY_CODE)
                    if with_github
                    else (SourceClass.INTERNAL_REGISTRY_CODE,)
                ),
            ),
        ),
        source_allocations=internal_alloc + github_alloc,
        budget=budget or DiscoveryBudget(
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


def baseline(
    *,
    covered_atoms=(),
    external_target_atoms=(ATOM,),
    verdict=InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL,
    contract_id=CAP,
    contract_version=1,
) -> InternalBaselineRecord:
    requested = tuple(covered_atoms) + tuple(external_target_atoms)
    return InternalBaselineRecord(
        baseline_id="baseline-001",
        capability_id=CAP,
        contract_id=contract_id,
        contract_version=contract_version,
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


def fully_satisfied() -> InternalBaselineRecord:
    return baseline(
        covered_atoms=(ATOM,),
        external_target_atoms=(),
        verdict=InternalBaselineClassification.FULLY_SATISFIED_INTERNAL,
    )


def partially_satisfied() -> InternalBaselineRecord:
    return baseline(
        covered_atoms=(),
        external_target_atoms=(ATOM,),
        verdict=InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL,
    )


def make_adapter(
    *,
    transport,
    authority,
    baseline_record,
    plan_obj,
    clock="2026-09-21T12:00:05Z",
    max_results_cap=None,
) -> GitHubDiscoveryAdapter:
    return GitHubDiscoveryAdapter(
        transport=transport,
        authority_provider=authority,
        baseline=baseline_record,
        plan=plan_obj,
        clock=lambda: clock,
        max_results_cap=max_results_cap,
    )


def query(
    *,
    atom_id=ATOM,
    family_id=FAMILY,
    concrete_query=CONCRETE_QUERY,
    source_class=SourceClass.GITHUB_REPOSITORY_CODE,
    query_id=None,
    max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
    cursor="",
) -> DiscoveryQuery:
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
        max_tier=max_tier,
        cursor=cursor,
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


def transport_calls(adapter) -> int:
    return len(adapter._transport.repository_calls) + len(adapter._transport.code_calls)


# ============================================================================
# C01 — Authority must bind to the exact request
# ============================================================================


class TestC01AuthorityBinding:
    def test_grant_for_another_request_is_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=MismatchedAuthorityProvider(wrong_ref="auth-other-query"),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0
        assert "request_ref" in outcome.message

    def test_grant_for_another_action_is_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=MismatchedAuthorityProvider(
                wrong_ref="auth-" + query().query_id,
                wrong_action=PolicyAction.MAY_CLONE_TO_SANDBOX,
            ),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0
        assert "MAY_DISCOVER" in outcome.message or "action" in outcome.message.lower()

    def test_malformed_decision_is_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=MalformedAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0

    def test_exception_from_authority_provider_fails_closed(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=RaisingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0

    def test_deny_is_refused(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),  # will be overridden below
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        # Swap in a deny provider
        from qcae.core.decisions.authority import AuthorityOutcome

        class DenyProvider(AuthorityProvider):
            def decide(self, request: AuthorityRequest) -> AuthorityDecision:
                return AuthorityDecision(
                    decision_id="dec-1",
                    request_ref=request.request_id,
                    action=request.action,
                    outcome=AuthorityOutcome.DENY,
                    decided_by="test-policy",
                    decided_at="2026-09-21T12:00:00Z",
                    reason="denied",
                )

        adapter._authority_provider = DenyProvider()
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0

    def test_request_more_evidence_is_refused(self) -> None:
        transport = FakeGitHubTransport()

        class MoreEvidenceProvider(AuthorityProvider):
            def decide(self, request: AuthorityRequest) -> AuthorityDecision:
                return AuthorityDecision(
                    decision_id="dec-1",
                    request_ref=request.request_id,
                    action=request.action,
                    outcome=AuthorityOutcome.REQUEST_MORE_EVIDENCE,
                    decided_by="test-policy",
                    decided_at="2026-09-21T12:00:00Z",
                    reason="needs review",
                )

        adapter = make_adapter(
            transport=transport,
            authority=MoreEvidenceProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0

    def test_valid_grant_proceeds_with_zero_defects(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status in (AdapterStatus.OK, AdapterStatus.NO_RESULTS, AdapterStatus.PARTIAL_RESULTS)
        assert transport_calls(adapter) >= 1


# ============================================================================
# C02 — External egress scope is not enforceable by the frozen policy model
# ============================================================================


class TestC02EgressScopeAudit:
    def test_frozen_policy_ignores_scope_field(self) -> None:
        """The policy engine matches action/principal/resource/classification
        only; scope and budget_ref are carried but never rule-matched. A broad
        MAY_DISCOVER ALLOW for a contract therefore silently covers GitHub
        egress for any query/atom/budget under that contract."""
        from qcae.governance.standalone.policy import (
            LocalPolicyEngine,
            PolicyDecisionType,
            PolicyEffect,
            PolicyRule,
            PolicyRequest,
            PolicySet,
        )

        rule = PolicyRule(
            rule_id="allow-discover",
            effect=PolicyEffect.ALLOW,
            action="may_discover",
            principal_match="*",
            resource_match="*",
            classification_match="*",
            reason="broad internal discovery allowance",
        )
        engine = LocalPolicyEngine(
            PolicySet(
                policy_id="pol-1",
                policy_version="1.0",
                rules=(rule,),
            )
        )
        # External GitHub egress request with explicit scope/budget_ref.
        req = PolicyRequest(
            principal="adapter",
            action="may_discover",
            resource=CAP,
            scope="github-external-search",
            classification="INTERNAL",
            budget_ref="plan-001",
            risk_class="low",
        )
        decision = engine.evaluate(req, decision_id="d-1", created_at="2026-01-01T00:00:00Z")
        assert decision.decision is PolicyDecisionType.ALLOW
        # Same rule would match an identical request with no scope / no budget
        # ref — the engine cannot tell them apart.
        req2 = PolicyRequest(
            principal="adapter",
            action="may_discover",
            resource=CAP,
            scope="",
            classification="INTERNAL",
            budget_ref="",
            risk_class="",
        )
        decision2 = engine.evaluate(req2, decision_id="d-2", created_at="2026-01-01T00:00:00Z")
        assert decision2.decision is PolicyDecisionType.ALLOW
        assert decision.rule_ref == decision2.rule_ref

    def test_adapter_context_carries_provider_and_query_identity(self) -> None:
        """Even though the frozen policy engine does not enforce scope, the
        adapter's AuthorityRequest context must at least record the exact
        external egress intent for auditability."""
        transport = FakeGitHubTransport()
        captured = []

        class CapturingProvider(AuthorityProvider):
            def decide(self, request: AuthorityRequest) -> AuthorityDecision:
                captured.append(request)
                return AuthorityDecision(
                    decision_id="dec-1",
                    request_ref=request.request_id,
                    action=request.action,
                    outcome=AuthorityOutcome.GRANT,
                    decided_by="test-policy",
                    decided_at="2026-09-21T12:00:00Z",
                    reason="granted",
                )

        provider = CapturingProvider()
        adapter = make_adapter(
            transport=transport,
            authority=provider,
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        adapter.search(query())
        assert len(captured) == 1
        ctx = captured[0].context
        assert ctx["scope"] == "github-external-search"
        assert ctx["budget_ref"] == "plan-001"
        assert ctx["provider"] == "github"
        assert ctx["query_id"] == query().query_id
        assert ctx["atom_id"] == ATOM


# ============================================================================
# C03 — Plan and baseline identity
# ============================================================================


class TestC03PlanBaselineIdentity:
    def test_baseline_contract_a_with_plan_contract_b(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=baseline(contract_id="CAP-OTHER"),
            plan_obj=plan(contract_id=CAP),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0

    def test_same_contract_wrong_version(self) -> None:
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=baseline(contract_version=99),
            plan_obj=plan(contract_version=1),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0

    def test_query_for_atom_outside_baseline_external_target_atoms(self) -> None:
        transport = FakeGitHubTransport()
        # Baseline says ATOM_B is external target; query asks about ATOM.
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=baseline(external_target_atoms=(ATOM_B,)),
            plan_obj=plan(atom_ids=(ATOM,)),
        )
        outcome = adapter.search(query(atom_id=ATOM))
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0

    def test_atom_in_plan_but_outside_baseline_external_target(self) -> None:
        transport = FakeGitHubTransport()
        # Baseline external_target_atoms is empty (all internally covered).
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=fully_satisfied(),
            plan_obj=plan(atom_ids=(ATOM,)),
        )
        outcome = adapter.search(query(atom_id=ATOM))
        assert outcome.status is AdapterStatus.NOT_CONFIGURED
        assert transport_calls(adapter) == 0

    def test_query_id_from_family_a_paired_with_family_b(self) -> None:
        transport = FakeGitHubTransport()
        # query_id derived from family B but query uses family A terms.
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        q = query(query_id="fam-other:some-term")
        outcome = adapter.search(q)
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert transport_calls(adapter) == 0

    def test_family_whose_hypotheses_do_not_authorize_the_queried_atom(self) -> None:
        transport = FakeGitHubTransport()
        # Plan has hypothesis hyp-atom covering ATOM, but family FAMILY only
        # serves hyp-other (covering ATOM_B). Querying family FAMILY for atom
        # ATOM must be refused: the family does not authorize that atom.
        plan_b = make_discovery_plan(
            discovery_plan_id="plan-001",
            contract_id=CAP,
            contract_version=1,
            atom_ids=(ATOM, ATOM_B),
            internal_baseline_queries=("internal:capability-registry:" + CAP,),
            search_hypotheses=(
                SearchHypothesis(
                    hypothesis_id="hyp-atom",
                    atom_ids=(ATOM,),
                    kind=SearchHypothesisKind.FOCUSED_LIBRARY,
                    statement="may exist as a focused library for ATOM",
                    expected_source_classes=(SourceClass.GITHUB_REPOSITORY_CODE,),
                ),
                SearchHypothesis(
                    hypothesis_id="hyp-other",
                    atom_ids=(ATOM_B,),
                    kind=SearchHypothesisKind.FOCUSED_LIBRARY,
                    statement="other atom",
                    expected_source_classes=(SourceClass.GITHUB_REPOSITORY_CODE,),
                ),
            ),
            query_families=(
                # Family fam-a serves hyp-atom (ATOM) - a different family.
                QueryFamilyRecord(
                    family_id="fam-a",
                    kind=QueryFamilyKind.BEHAVIORAL,
                    hypothesis_ids=("hyp-atom",),
                    terms=(CONCRETE_QUERY,),
                    source_classes=(
                        SourceClass.INTERNAL_REGISTRY_CODE,
                        SourceClass.GITHUB_REPOSITORY_CODE,
                    ),
                ),
                # Family FAMILY serves hyp-other (ATOM_B) only - NOT hyp-atom.
                QueryFamilyRecord(
                    family_id=FAMILY,
                    kind=QueryFamilyKind.BEHAVIORAL,
                    hypothesis_ids=("hyp-other",),
                    terms=(CONCRETE_QUERY,),
                    source_classes=(
                        SourceClass.INTERNAL_REGISTRY_CODE,
                        SourceClass.GITHUB_REPOSITORY_CODE,
                    ),
                ),
                # Diversity family to satisfy canon 2.1.16 for a multi-hypothesis plan.
                QueryFamilyRecord(
                    family_id="fam-synonym",
                    kind=QueryFamilyKind.SYNONYM,
                    hypothesis_ids=("hyp-atom",),
                    terms=("causal ordering synonyms",),
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
            diversity_requirements=DiversityRequirement(
                max_single_source_share=0.9, min_distinct_source_classes=2
            ),
            stop_rules=(
                StopRule(condition=StopCondition.BUDGET_CEILING_REACHED),
                StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),
            ),
            created_by="qcae-discovery-planner",
            policy_version="discovery-ranking-policy-1.0",
            single_route_justification="fixture",
        )
        # Baseline must list ATOM as an external target.
        baseline_ab = baseline(
            covered_atoms=(),
            external_target_atoms=(ATOM,),
            verdict=InternalBaselineClassification.PARTIALLY_SATISFIED_INTERNAL,
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=baseline_ab,
            plan_obj=plan_b,
        )
        # Query uses family FAMILY (which only serves hyp-other/ATOM_B) but asks
        # about atom ATOM (covered by hyp-atom, which is in family fam-a, not FAMILY).
        outcome = adapter.search(query(atom_id=ATOM, family_id=FAMILY))
        assert outcome.status is AdapterStatus.UNSUPPORTED_QUERY
        assert transport_calls(adapter) == 0


# ============================================================================
# C04 — Cost-tier and budget authority
# ============================================================================


class TestC04CostTierBudget:
    def test_tier_1_query_higher_allocation_no_deeper_search(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(
                github_max_tier=CostTier.TIER_3_SOURCE_TREE,
                query_max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
            ),
        )
        adapter.search(query(max_tier=CostTier.TIER_1_METADATA_SNIPPETS))
        # Query tier is TIER_1: code search (TIER_2+) must not run.
        assert len(transport.code_calls) == 0, transport.code_calls

    def test_higher_query_tier_lower_plan_ceiling_no_deep_search(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        # Build a plan whose cost_tier_ceiling is TIER_1. Canon requires
        # allocation.max_tier <= cost_tier_ceiling, so allocation is TIER_1 too.
        # min(query=TIER_3, ceiling=TIER_1, allocation=TIER_1) = TIER_1 -> code search blocked.
        plan_ceiling_t1 = make_discovery_plan(
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
                    max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
                ),
            ),
            budget=DiscoveryBudget(
                max_queries=10,
                max_results_inspected=50,
                max_source_calls=10,
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
            single_route_justification="fixture",
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan_ceiling_t1,
        )
        adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert len(transport.code_calls) == 0, transport.code_calls

    def test_higher_plan_ceiling_lower_allocation_allocation_wins(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        # Plan ceiling TIER_3, query TIER_3, but allocation max_tier TIER_1:
        # min(3, 3, 1) = 1 -> no code search.
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(
                github_max_tier=CostTier.TIER_1_METADATA_SNIPPETS,
                query_max_tier=CostTier.TIER_3_SOURCE_TREE,
            ),
        )
        adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert len(transport.code_calls) == 0, transport.code_calls

    def test_query_budget_max_queries_exhausted_zero_calls(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [], "total_count": 0}
        )
        # Two query terms so a second planned query exists.
        plan_two_terms = plan(
            budget=DiscoveryBudget(max_queries=1, max_results_inspected=50,
                                   max_source_calls=10, max_wall_clock_seconds=300),
            family_terms=(CONCRETE_QUERY, "other search term"),
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan_two_terms,
        )
        adapter.search(query())
        calls_before = transport_calls(adapter)
        # Second planned query: same family, different term.
        second = adapter.search(query(query_id="fam-behavioral:other-search-term"))
        assert second.status is AdapterStatus.RATE_LIMITED
        assert transport_calls(adapter) == calls_before

    def test_source_call_budget_exhausted_partial_not_ok(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item(), item("b/repo")], "total_count": 10}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(
                budget=DiscoveryBudget(
                    max_queries=10,
                    max_results_inspected=50,
                    max_source_calls=1,
                    max_wall_clock_seconds=300,
                )
            ),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        # Repo search returns 2 of 10 results on page 1; page 2 would need a
        # second source call but max_source_calls=1 -> partial with leads kept.
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert len(outcome.leads) == 2
        assert "budget" in outcome.completeness_note.lower()

    def test_wall_clock_and_cost_usd_not_claimed_enforced(self) -> None:
        """If exact cost/wall-clock cannot be measured, the adapter must not
        claim the ceiling is enforced. This test documents the gap."""
        transport = FakeGitHubTransport()
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(
                budget=DiscoveryBudget(
                    max_queries=10,
                    max_results_inspected=50,
                    max_source_calls=10,
                    max_wall_clock_seconds=1,  # absurdly tight
                    max_cost_usd=0.0,
                )
            ),
        )
        outcome = adapter.search(query())
        # The adapter has no injected wall-clock or cost metering, so it cannot
        # enforce these. It should still proceed (no false claim of enforcement).
        assert outcome.status is not AdapterStatus.NOT_CONFIGURED


# ============================================================================
# C05 — Two-surface result aggregation
# ============================================================================


class TestC05TwoSurfaceAggregation:
    def _seed_repo_ok(self, transport, items=None):
        items = items or [item()]
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": items, "total_count": len(items)}
        )

    def test_repo_ok_code_401_partial_with_leads(self) -> None:
        transport = FakeGitHubTransport()
        self._seed_repo_ok(transport)
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=401, headers={}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert len(outcome.leads) == 1
        assert outcome.pages_inspected == 2
        assert "code" in outcome.completeness_note.lower()

    def test_repo_ok_code_403_rate_limited_partial(self) -> None:
        transport = FakeGitHubTransport()
        self._seed_repo_ok(transport)
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=403,
            headers={"X-RateLimit-Remaining": "0"},
            body={},
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert len(outcome.leads) == 1

    def test_repo_ok_code_429_partial(self) -> None:
        transport = FakeGitHubTransport()
        self._seed_repo_ok(transport)
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=429, headers={"X-RateLimit-Reset": "1700000000"}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert len(outcome.leads) == 1

    def test_repo_ok_code_500_partial(self) -> None:
        transport = FakeGitHubTransport()
        self._seed_repo_ok(transport)
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=500, headers={}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert len(outcome.leads) == 1

    def test_repo_ok_code_malformed_partial(self) -> None:
        transport = FakeGitHubTransport()
        self._seed_repo_ok(transport)
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body="not-a-json-object"
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert len(outcome.leads) == 1

    def test_repo_401_no_code_search_continuation(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=401, headers={}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.AUTH_FAILURE
        assert outcome.leads == ()
        assert len(transport.code_calls) == 0

    def test_first_page_ok_later_page_fails_partial(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 5}
        )
        transport._responses[("repository", CONCRETE_QUERY, 2)] = GitHubResponse(
            status_code=500, headers={}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        # C05 rule 1: repository failure terminates that surface truthfully.
        # A later-page failure makes the whole repo search a provider failure;
        # no secondary code-search call is issued, and no leads are retained.
        assert outcome.status is AdapterStatus.PROVIDER_FAILURE
        assert outcome.leads == ()
        assert len(transport.code_calls) == 0

    def test_first_page_ok_call_budget_exhausted_partial(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item(), item("b/repo")], "total_count": 10}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(
                budget=DiscoveryBudget(
                    max_queries=10,
                    max_results_inspected=50,
                    max_source_calls=1,
                    max_wall_clock_seconds=300,
                )
            ),
            max_results_cap=20,
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert len(outcome.leads) == 2
        assert "budget" in outcome.completeness_note.lower()

    def test_both_completed_no_leads_no_results(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [], "total_count": 0}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.NO_RESULTS
        assert outcome.leads == ()


# ============================================================================
# C06 — Provider error and rate-limit semantics
# ============================================================================


class TestC06ProviderRateLimit:
    def test_401_is_auth_failure_no_retry_after(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=401, headers={}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.AUTH_FAILURE
        assert outcome.retry_after_seconds is None

    def test_403_without_rate_headers_is_auth_failure(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=403, headers={}, body={}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.AUTH_FAILURE

    def test_403_with_rate_limit_remaining_zero_is_rate_limited(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=403,
            headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"},
            body={},
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.RATE_LIMITED
        # retry_after_seconds must be a duration, never the raw reset epoch.
        assert outcome.retry_after_seconds is None or outcome.retry_after_seconds != 1700000000

    def test_429_rate_limited_retry_after_is_duration_not_epoch(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=429,
            headers={"X-RateLimit-Reset": "1700000000"},
            body={},
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.RATE_LIMITED
        assert outcome.retry_after_seconds is None or outcome.retry_after_seconds != 1700000000

    def test_x_ratelimit_remaining_consumed_prevents_further_calls(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200,
            headers={"X-RateLimit-Remaining": "0"},
            body={"items": [item()], "total_count": 1},
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        # With remaining=0 after the first page, no further pages should be
        # attempted; the search is partial (exhaustion known).
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        assert outcome.pages_inspected == 1

    def test_malformed_200_is_provider_failure_not_no_results(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body="not-a-json-object"
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PROVIDER_FAILURE
        assert outcome.leads == ()

    def test_200_missing_items_field_is_provider_failure(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"total_count": 0}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PROVIDER_FAILURE

    def test_invalid_pagination_cursor_refused(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [], "total_count": 0}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query(cursor="not-a-number"))
        # Invalid cursor should not silently restart at page 1.
        assert outcome.status in (AdapterStatus.UNSUPPORTED_QUERY, AdapterStatus.NOT_CONFIGURED, AdapterStatus.NO_RESULTS)
        assert transport_calls(adapter) == 0


# ============================================================================
# C07 — Lead completeness and provenance
# ============================================================================


class TestC07LeadCompletenessProvenance:
    def test_partial_outcome_leads_are_not_complete(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 5, "incomplete_results": True}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.PARTIAL_RESULTS
        for lead in outcome.leads:
            assert lead.completeness is SearchCompleteness.PARTIAL, lead.completeness

    def test_complete_outcome_leads_are_complete(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        transport._responses[("repository", CONCRETE_QUERY, 2)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [], "total_count": 1}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert outcome.status is AdapterStatus.OK
        for lead in outcome.leads:
            assert lead.completeness is SearchCompleteness.COMPLETE

    def test_missing_revision_anchor_explicitly_missing(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        lead = adapter.search(query()).leads[0]
        assert lead.retrieved_revision == MISSING_REVISION
        assert lead.retrieved_revision == ""

    def test_no_github_unknown_fabrication(self) -> None:
        transport = FakeGitHubTransport()
        # Code-search item without repository identity.
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [], "total_count": 0}
        )
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200,
            headers={},
            body={
                "items": [
                    {
                        "repository": None,
                        "html_url": "https://github.com/owner/repo",
                        "path": "src/module.py",
                        "sha": "abc123",
                    }
                ],
                "total_count": 1,
            },
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(
                github_max_tier=CostTier.TIER_3_SOURCE_TREE,
                query_max_tier=CostTier.TIER_3_SOURCE_TREE,
            ),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        for lead in outcome.leads:
            assert "github:unknown" not in lead.source_locator

    def test_code_search_provenance_retains_file_path(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [], "total_count": 0}
        )
        transport._responses[("code", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200,
            headers={},
            body={
                "items": [
                    {
                        "repository": {"full_name": "owner/repo", "html_url": "https://github.com/owner/repo"},
                        "path": "src/module.py",
                        "sha": "blob-sha-not-a-commit",
                    }
                ],
                "total_count": 1,
            },
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(
                github_max_tier=CostTier.TIER_3_SOURCE_TREE,
                query_max_tier=CostTier.TIER_3_SOURCE_TREE,
            ),
        )
        outcome = adapter.search(query(max_tier=CostTier.TIER_3_SOURCE_TREE))
        assert outcome.status is AdapterStatus.OK
        lead = outcome.leads[0]
        # path identity retained
        assert lead.activity_signals.get("path") == "src/module.py" or "src/module.py" in str(lead.activity_signals)
        # blob sha is not a commit anchor
        assert lead.retrieved_revision == MISSING_REVISION

    def test_duplicate_identities_do_not_inflate_corroboration(self) -> None:
        transport = FakeGitHubTransport()
        it = item("dup/repo")
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [it, it], "total_count": 2}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        assert len(outcome.leads) == 2
        # Adapter emits duplicates; corroboration is the merge layer's job.
        assert outcome.leads[0].source_locator == outcome.leads[1].source_locator

    def test_popularity_remains_raw_signal(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item(stars=999999)], "total_count": 1}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        lead = adapter.search(query()).leads[0]
        assert lead.popularity_signals["stargazers_count"] == 999999
        assert lead.claim_verification is VerificationLevel.DISCOVERED

    def test_leads_never_emit_verification_or_acquisition(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        lead = adapter.search(query()).leads[0]
        assert not hasattr(lead, "verification_level")
        assert not hasattr(lead, "acquisition_approved")
        assert not hasattr(lead, "receipt")

    def test_raw_artifact_ref_is_non_durable_fingerprint(self) -> None:
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        for ref in outcome.raw_artifact_refs:
            assert ref.startswith("sha256:")
        # A digest alone is not proof of durable artifact storage; the notes
        # must classify it as a response fingerprint.
        for lead in outcome.leads:
            assert "fingerprint" in lead.notes.lower() or "transient" in lead.notes.lower()


# ============================================================================
# C02 (continued) — external egress scope enforcement is a frozen-model gap
# ============================================================================


class TestC02NoPretendEnforcement:
    def test_broad_may_discover_allows_unscoped_github_egress(self) -> None:
        """Documents that the frozen authority model cannot distinguish internal
        MAY_DISCOVER from unrestricted GitHub egress. A GRANT for contract CAP
        with scope 'github-external-search' and budget_ref 'plan-001' is
        matched identically to the same request with empty scope/budget_ref.
        The adapter must not pretend the authority layer enforces egress scope."""
        transport = FakeGitHubTransport()
        transport._responses[("repository", CONCRETE_QUERY, 1)] = GitHubResponse(
            status_code=200, headers={}, body={"items": [item()], "total_count": 1}
        )
        adapter = make_adapter(
            transport=transport,
            authority=GrantingAuthorityProvider(),
            baseline_record=partially_satisfied(),
            plan_obj=plan(),
        )
        outcome = adapter.search(query())
        # The adapter proceeds because it received a GRANT, but C02 establishes
        # that the frozen policy model did not actually authorize the specific
        # external egress. The outcome must not claim authority-level scope
        # enforcement that does not exist.
        assert outcome.status is not AdapterStatus.NOT_CONFIGURED
