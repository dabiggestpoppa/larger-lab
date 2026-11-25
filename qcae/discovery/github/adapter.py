"""GitHub repository/code discovery adapter — P3-T02 C01/C02/C03/C04.

Implements the DiscoverySourceAdapter port behind an injectable GitHub transport.
The adapter is provider-specific: it owns GitHub authentication, pagination,
rate-limit semantics and payload normalization. The planner, ranking, candidate
ontology and report assembler remain provider-neutral.

No default live-network operation. The transport is injected; the fake
transport is the only implementation in this module. A live client is an
explicit, separate integration decision (P3-T03+).

C02 egress authority — before any transport call the adapter confirms:

1. the internal baseline is established;
2. assert_external_execution_authorized (the baseline forecloses external search
   for fully satisfied / internally covered atoms);
3. baseline contract/version match the plan; the queried atom belongs to both
   the plan scope and the baseline's external_target_atoms;
4. the query belongs to the current DiscoveryPlan (identity, family, source
   class, scope) and its family is served by a hypothesis covering that atom;
5. the source class and search scope are authorized by an enabled allocation;
6. an explicit may_discover allow decision is obtained through the
   AuthorityProvider boundary, with the decision bound to the exact request
   (request_ref, action, structural validity; DENY / REQUEST_MORE_EVIDENCE /
   missing provider / provider exception -> zero transport calls);
7. remaining per-query and whole-run budgets are checked;
8. only then is the injected transport called.

C02 audit (frozen authority model): the standalone LocalAuthorityProvider /
LocalPolicyEngine matches policy rules on action / principal / resource /
classification only. The PolicyRequest scope and budget_ref fields are carried
but never rule-matched, so a broad internal MAY_DISCOVER ALLOW for a contract
cannot distinguish internal discovery from external GitHub egress, nor bind the
intended provider/resource, query/atom scope, or cost envelope. The adapter
therefore records provider/query/atom/tier context in the AuthorityRequest for
auditability but does NOT pretend the authority layer enforces egress scope.
Expressing that safely requires a frozen-model amendment (rule matching on
scope and/or budget_ref, or a dedicated egress action) and is reported as a
blocker rather than worked around with a permissive default.

C03 provider outcome truth — typed statuses are implemented faithfully:

* NOT_CONFIGURED: provider/authority not wired, or egress not authorized.
* AUTH_FAILURE: provider 401, or 403 access denial without rate-limit evidence.
* RATE_LIMITED: provider throttling (429, or 403 with X-RateLimit-Remaining: 0).
* PROVIDER_FAILURE: provider error or malformed payload.
* UNSUPPORTED_QUERY: query not expressible within this plan/contract.
* NO_RESULTS: a completed search returned no matches.
* PARTIAL_RESULTS: results obtained but completeness not established (note
  required; never represented as exhaustive).
* OK: completed search with actual leads.

No provider failure becomes NO_RESULTS. No partial page sequence is described as
exhaustive. No retry exceeds the declared source-call / time / cost / result
budget.

C04 capability provenance firewall — the adapter emits CandidateLead records
only: never VERIFIED/IMPLEMENTED, never a Capability Receipt, never a positive
acquisition decision, never QCAE ranking, and never correctness assertions from
stars/forks/README. Popularity and activity are raw observed signals, never
interpreted here. GitHub search returns mutable repository metadata only, so the
immutable commit anchor is represented as explicitly missing and deeper
qualification is deferred.

Exact query identity and lineage are preserved via DiscoveryQuery.lineage_for;
provider identity and revision metadata, pagination cursor and pages inspected,
result limit and cost-tier ceiling, rate-limit / partial-search standing, and
raw source evidence are all carried on the AdapterOutcome. Raw SHA-based
artifact refs are classified as non-durable response fingerprints, not
retrievable evidence artifacts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Optional, Tuple

from qcae.core.decisions.authority import (
    AuthorityOutcome,
    AuthorityProvider,
    AuthorityRequest,
    PolicyAction,
)
from qcae.discovery.internal.baseline import InternalBaselineRecord
from qcae.core.discovery.lead import (
    AdapterStatus,
    CandidateKind,
    CandidateLead,
    FAILURE_STATUSES,
    QueryLineage,
    SearchCompleteness,
    make_candidate_lead,
)
from qcae.core.discovery.plan import DiscoveryPlan
from qcae.discovery.reporting import assert_external_execution_authorized
from qcae.core.discovery.vocabulary import CostTier, SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.discovery import (
    AdapterOutcome,
    DiscoveryQuery,
    DiscoverySourceAdapter,
)
from qcae.core.serialization import sha256_of

from .transport import FakeGitHubTransport, GitHubResponse, GitHubTransport

__all__ = [
    "GitHubDiscoveryAdapter",
    "GitHubTransport",
    "GitHubResponse",
    "FakeGitHubTransport",
]

#: A GitHub default branch is a mutable ref, never an immutable commit anchor.
#: search results carry no commit SHA, so the anchor is explicitly missing.
MISSING_REVISION = ""

#: Maximum pages inspected per query before declaring a partial search.
#: This is a safety cap in addition to the plan's source-call budget.
_MAX_PAGES_PER_QUERY = 10


def _utc_now() -> str:
    """RFC3339 UTC timestamp for discovered_at / retrieved_at."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _items_from(body: object) -> Tuple[dict, ...]:
    """Extract the result items from a GitHub search response body."""
    if not isinstance(body, dict):
        return ()
    items = body.get("items")
    if not isinstance(items, list):
        return ()
    return tuple(item for item in items if isinstance(item, dict))


def _total_count_from(body: object) -> int:
    if not isinstance(body, dict):
        return 0
    value = body.get("total_count", 0)
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _incomplete_from(body: object) -> bool:
    if not isinstance(body, dict):
        return True  # unknown shape -> treat as incomplete, never exhaustive
    value = body.get("incomplete_results", False)
    return bool(value)


def _sha_of_body(body: object) -> str:
    """Stable raw-artifact reference for one response page."""
    return "sha256:" + sha256_of(body)[:24]


class GitHubDiscoveryAdapter(DiscoverySourceAdapter):
    """GitHub discovery adapter with policy-gated egress.

    Construction injects every external dependency so the adapter is fully
    deterministic under test: transport, authority provider, baseline, plan,
    clock and an optional results cap. Nothing here reaches the network unless
    an injected transport does, and no transport call happens until every C02
    egress gate passes.
    """

    def __init__(
        self,
        *,
        transport: GitHubTransport,
        authority_provider: Optional[AuthorityProvider] = None,
        baseline: Optional[InternalBaselineRecord] = None,
        plan: Optional[DiscoveryPlan] = None,
        clock=None,
        max_results_cap: Optional[int] = None,
    ) -> None:
        self._transport = transport
        self._authority_provider = authority_provider
        self._baseline = baseline
        self._plan = plan
        self._clock = clock or _utc_now
        self._max_results_cap = max_results_cap

        # Run budget accounting (c02 gate 6 / c03).
        self._source_calls = 0
        self._results_inspected = 0
        self._queries_executed = 0

    # -- DiscoverySourceAdapter port ---------------------------------------

    @property
    def adapter_id(self) -> str:
        return "github-discovery"

    @property
    def source_class(self) -> SourceClass:
        return SourceClass.GITHUB_REPOSITORY_CODE

    def search(self, query: DiscoveryQuery) -> AdapterOutcome:
        """Run one bounded, policy-gated GitHub search.

        Zero transport calls happen unless every egress gate passes. The typed
        outcome reports what actually occurred; a denial is never reported as a
        completed empty search.
        """
        # Gate 0: this adapter serves only the GitHub source class.
        if query.source_class != SourceClass.GITHUB_REPOSITORY_CODE:
            return self.unsupported(
                query,
                "this adapter serves "
                + SourceClass.GITHUB_REPOSITORY_CODE.value
                + ", not "
                + query.source_class.value,
            )

        # C02 gate 1: the internal baseline must be established.
        if self._baseline is None:
            return self.not_configured(
                query, "internal baseline not established; external search cannot run"
            )

        # C02 gate 2: the baseline must assign this atom to external search.
        try:
            assert_external_execution_authorized(self._baseline, (query.atom_id,))
        except QcaeValidationError as exc:
            return self.not_configured(
                query,
                "external search not authorized by internal baseline: " + str(exc),
            )

        # C02 gate 3: the query must belong to the current DiscoveryPlan.
        plan = self._plan
        if plan is None:
            return self.not_configured(
                query, "no DiscoveryPlan bound; query identity cannot be verified"
            )
        if query.query_id not in plan.query_ids:
            return self.unsupported(
                query, "query " + query.query_id + " is not declared by this plan"
            )
        if query.atom_id not in plan.atom_ids:
            return self.unsupported(
                query, "atom " + query.atom_id + " is outside this plan's atom scope"
            )
        family = next(
            (f for f in plan.query_families if f.family_id == query.family_id),
            None,
        )
        if family is None:
            return self.unsupported(
                query, "family " + query.family_id + " is not declared by this plan"
            )
        if query.concrete_query not in family.terms:
            return self.unsupported(
                query,
                "query "
                + query.query_id
                + " runs concrete query "
                + query.concrete_query
                + " which family "
                + query.family_id
                + " never declared",
            )
        if query.source_class not in family.source_classes:
            return self.unsupported(
                query,
                "family "
                + query.family_id
                + " does not declare source class "
                + query.source_class.value,
            )

        # C02 gate 4: source class and scope authorized by an enabled allocation.
        allocation = next(
            (
                a
                for a in plan.source_allocations
                if a.source_class == query.source_class and a.enabled
            ),
            None,
        )
        if allocation is None:
            return self.unsupported(
                query,
                "no enabled source allocation for "
                + query.source_class.value
                + " in this plan",
            )

        # C03: plan/baseline identity binding before any authority decision.
        # baseline.contract_id/version must match the plan.
        if self._baseline.contract_id != plan.contract_id:
            return self.not_configured(
                query,
                "baseline contract " + self._baseline.contract_id
                + " does not match plan contract " + plan.contract_id
                + "; zero transport calls",
            )
        if self._baseline.contract_version != plan.contract_version:
            return self.not_configured(
                query,
                "baseline contract version "
                + str(self._baseline.contract_version)
                + " does not match plan version "
                + str(plan.contract_version)
                + "; zero transport calls",
            )
        # The queried atom must be an authorized external target of the baseline.
        if query.atom_id not in self._baseline.external_target_atoms:
            return self.not_configured(
                query,
                "atom " + query.atom_id
                + " is not in the baseline's external_target_atoms; zero transport calls",
            )
        # The query's family must be served by a hypothesis that covers this atom.
        family_record = next(
            (f for f in plan.query_families if f.family_id == query.family_id),
            None,
        )
        hypothesis_covers_atom = False
        if family_record is not None:
            hypothesis_covers_atom = any(
                query.atom_id in h.atom_ids
                for h in plan.search_hypotheses
                if h.hypothesis_id in family_record.hypothesis_ids
            )
        if not hypothesis_covers_atom:
            return self.unsupported(
                query,
                "no search hypothesis in family "
                + query.family_id
                + " covers atom "
                + query.atom_id
                + "; zero transport calls",
            )

        # C02 gate 5: explicit allow decision through the governance boundary.
        if self._authority_provider is None:
            return self.not_configured(
                query,
                "no governance authority provider wired; may_discover cannot be decided",
            )
        # C01: construct and validate the exact AuthorityRequest.
        request = AuthorityRequest(
            request_id="auth-" + query.query_id,
            action=PolicyAction.MAY_DISCOVER,
            subject_id=plan.contract_id,
            justification=(
                "GitHub discovery for query "
                + query.query_id
                + " on behalf of plan "
                + plan.discovery_plan_id
            ),
            requested_by="qcae-github-discovery-adapter",
            context={
                "scope": "github-external-search",
                "budget_ref": plan.discovery_plan_id,
                "classification": "INTERNAL",
                "risk_class": "low",
                # C02: record the exact external egress intent for auditability.
                # The frozen policy engine does not match on scope/budget_ref;
                # these fields are recorded, not enforced, at this boundary.
                "provider": "github",
                "query_id": query.query_id,
                "atom_id": query.atom_id,
                "family_id": query.family_id,
                "cost_tier_ceiling": plan.cost_tier_ceiling.value,
            },
        )
        request.validate()
        # C01: obtain the decision, fail closed on any exception.
        try:
            decision = self._authority_provider.decide(request)
        except Exception as exc:  # fail closed: provider unreachable -> no egress
            return self.not_configured(
                query,
                "authority provider raised while deciding may_discover: "
                + type(exc).__name__
                + "; zero transport calls",
            )
        # C01: validate the decision's structural validity.
        try:
            decision.validate()
        except QcaeValidationError:
            return self.not_configured(
                query,
                "authority decision failed structural validation; zero transport calls",
            )
        # C01: require request_ref to equal the issued request ID.
        if decision.request_ref != request.request_id:
            return self.not_configured(
                query,
                "authority decision request_ref "
                + decision.request_ref
                + " does not match issued request "
                + request.request_id
                + "; zero transport calls",
            )
        # C01: require the action to equal MAY_DISCOVER.
        if decision.action is not PolicyAction.MAY_DISCOVER:
            return self.not_configured(
                query,
                "authority decision action "
                + decision.action.value
                + " is not MAY_DISCOVER; zero transport calls",
            )
        # C01: require a genuine GRANT.
        if decision.outcome is not AuthorityOutcome.GRANT:
            return self.not_configured(
                query,
                (
                    "governance authority did not grant may_discover "
                    "(outcome="
                    + decision.outcome.value
                    + ", reason="
                    + decision.reason
                    + "); zero transport calls"
                ),
            )

        # C02 gate 6: remaining per-query and whole-run budgets.
        budget = plan.budget
        if self._queries_executed >= budget.max_queries:
            return self.rate_limited(query, "plan query budget exhausted")
        if self._source_calls >= budget.max_source_calls:
            return self.rate_limited(query, "plan source-call budget exhausted")
        remaining_results = budget.max_results_inspected - self._results_inspected
        if remaining_results < 1:
            return self.rate_limited(query, "plan results-inspected budget exhausted")

        # All gates passed — execute the search.
        self._queries_executed += 1
        return self._run_search(query, plan, allocation, budget, remaining_results)

    # -- search execution -------------------------------------------------

    def _run_search(
        self,
        query: DiscoveryQuery,
        plan,
        allocation,
        budget,
        remaining_results: int,
    ) -> AdapterOutcome:
        """Perform the bounded repository/code search once egress is authorized."""
        # C06: refuse invalid pagination cursors instead of silently restarting
        # at page 1.
        start_page = self._parse_cursor(query.cursor)
        if start_page is None:
            return self.unsupported(
                query,
                "invalid pagination cursor " + repr(query.cursor)
                + "; zero transport calls",
            )

        max_results = min(query.max_results, remaining_results)
        if self._max_results_cap is not None:
            max_results = min(max_results, self._max_results_cap)

        per_page = min(max_results, 10)

        leads: list = []
        pages_inspected = 0
        results_inspected = 0
        raw_refs: list = []
        provider_revision = ""

        completeness_note_parts: list = []

        # C04: effective cost-tier ceiling — the most restrictive of query,
        # plan, and allocation. Repository search is TIER_1 and always allowed;
        # code search is TIER_2+ and gated on the effective ceiling.
        effective_tier = min(
            query.max_tier,
            plan.cost_tier_ceiling,
            allocation.max_tier,
        )

        # Repository search (TIER_1 metadata surface — always allowed).
        (
            repo_status,
            repo_pages,
            repo_results,
            repo_refs,
            repo_note,
            repo_retry_after,
        ) = self._search_pages(
            kind="repository",
            query=query,
            per_page=per_page,
            start_page=start_page,
            max_results=max_results,
            items=leads,
        )
        pages_inspected += repo_pages
        results_inspected += repo_results
        raw_refs.extend(repo_refs)
        if repo_note:
            completeness_note_parts.append("repository: " + repo_note)
        repo_surface_complete = repo_status == AdapterStatus.OK

        # C05 rule 2: a repository surface failure is terminal — no secondary
        # code-search request after a terminal provider/authority failure.
        if repo_status in FAILURE_STATUSES:
            self._results_inspected += results_inspected
            return self._failure_outcome(
                query,
                repo_status,
                pages_inspected,
                results_inspected,
                raw_refs,
                repo_note or "repository surface failed",
                repo_retry_after,
            )

        # Code search (deeper source surface) only when the effective tier
        # ceiling permits TIER_2+ work.
        code_status = AdapterStatus.OK
        code_note = ""
        code_retry_after: Optional[int] = None
        code_surface_complete = True
        if (
            effective_tier >= CostTier.TIER_2_DOCS_PACKAGE_METADATA
            and results_inspected < max_results
        ):
            (
                code_status,
                code_pages,
                code_results,
                code_refs,
                code_note,
                code_retry_after,
            ) = self._search_pages(
                kind="code",
                query=query,
                per_page=min(max_results - results_inspected, 10),
                start_page=start_page,
                max_results=max_results - results_inspected,
                items=leads,
            )
            pages_inspected += code_pages
            results_inspected += code_results
            raw_refs.extend(code_refs)
            if code_note:
                completeness_note_parts.append("code: " + code_note)
            code_surface_complete = code_status == AdapterStatus.OK

        self._results_inspected += results_inspected

        # C05: explicit two-surface outcome aggregation.
        status = self._aggregate_surface_status(repo_status, code_status)

        # Build leads with per-surface completeness (C07): a lead from a
        # partial surface cannot be recorded as exhaustive evidence. Items
        # without a usable repository identity are skipped (no github:unknown
        # fabrication) rather than emitted.
        normalized: list = []
        for item, kind in leads:
            lead = self._normalize_item(
                item,
                query,
                kind,
                completeness=SearchCompleteness.COMPLETE
                if (kind == "repository" and repo_surface_complete)
                or (kind == "code" and code_surface_complete)
                else SearchCompleteness.PARTIAL,
            )
            if lead is not None:
                normalized.append(lead)
        lead_tuple: Tuple[CandidateLead, ...] = tuple(normalized)

        completeness_note = "; ".join(part for part in completeness_note_parts if part)
        if status == AdapterStatus.OK and not lead_tuple:
            status = AdapterStatus.NO_RESULTS

        # Failure statuses require a non-empty message (port validation law);
        # the completeness note carries the reason the search did not complete.
        outcome_message = completeness_note if status in FAILURE_STATUSES else ""
        retry_after = repo_retry_after or code_retry_after

        outcome = AdapterOutcome(
            adapter_id=self.adapter_id,
            source_class=self.source_class,
            query_id=query.query_id,
            status=status,
            retrieved_at=self._clock(),
            leads=lead_tuple,
            pages_inspected=pages_inspected,
            results_inspected=results_inspected,
            duplicate_count=0,
            novelty_count=0,
            raw_artifact_refs=tuple(raw_refs),
            completeness_note=completeness_note,
            provider_revision=provider_revision,
            message=outcome_message,
            retry_after_seconds=retry_after,
        )
        outcome.validate()
        return outcome

    @staticmethod
    def _parse_cursor(cursor: str) -> Optional[int]:
        """Parse a pagination cursor; return None for invalid cursors (C06)."""
        if not cursor:
            return 1
        if not cursor.isdigit():
            return None
        value = int(cursor)
        return value if value >= 1 else None

    @staticmethod
    def _aggregate_surface_status(
        repo_status: AdapterStatus,
        code_status: AdapterStatus,
    ) -> AdapterStatus:
        """C05: explicit two-surface outcome aggregation.

        1. Repository failure is terminal (no secondary continuation).
        2. Code failure after repo success -> PARTIAL_RESULTS (never exhaustive OK).
        3. Either surface partial -> PARTIAL_RESULTS.
        4. Both OK -> OK.
        """
        if repo_status in FAILURE_STATUSES:
            return repo_status
        if code_status in FAILURE_STATUSES:
            return AdapterStatus.PARTIAL_RESULTS
        if repo_status == AdapterStatus.PARTIAL_RESULTS or code_status == AdapterStatus.PARTIAL_RESULTS:
            return AdapterStatus.PARTIAL_RESULTS
        return AdapterStatus.OK

    def _failure_outcome(
        self,
        query: DiscoveryQuery,
        status: AdapterStatus,
        pages_inspected: int,
        results_inspected: int,
        raw_refs: list,
        message: str,
        retry_after: Optional[int],
    ) -> AdapterOutcome:
        """Build a typed failure outcome with zero leads (C05 rule 1)."""
        outcome = AdapterOutcome(
            adapter_id=self.adapter_id,
            source_class=self.source_class,
            query_id=query.query_id,
            status=status,
            retrieved_at=self._clock(),
            leads=(),
            pages_inspected=pages_inspected,
            results_inspected=results_inspected,
            duplicate_count=0,
            novelty_count=0,
            raw_artifact_refs=tuple(raw_refs),
            completeness_note=message,
            provider_revision="",
            message=message,
            retry_after_seconds=retry_after,
        )
        outcome.validate()
        return outcome

    def _retry_after_seconds(self, response: GitHubResponse) -> Optional[int]:
        """C06: compute retry_after as a duration (seconds) from X-RateLimit-Reset.

        X-RateLimit-Reset is a UTC epoch timestamp; retry_after_seconds is a
        duration. Never copy the epoch directly into retry_after_seconds.
        Uses the injected clock for determinism; returns None when the reset
        timestamp is unavailable or unparseable.
        """
        reset = self._transport.rate_limit_reset(response)
        if reset is None:
            return None
        try:
            now_str = self._clock()
            now_dt = datetime.strptime(now_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            now_epoch = int(now_dt.timestamp())
            duration = reset - now_epoch
            return max(duration, 0)
        except (ValueError, TypeError, OSError):
            return None

    def _search_pages(
        self,
        *,
        kind: str,
        query: DiscoveryQuery,
        per_page: int,
        start_page: int,
        max_results: int,
        items: list,
    ) -> Tuple[AdapterStatus, int, int, list, str, Optional[int]]:
        """Fetch one surface page by page, bounded by result and call budgets.

        Appends normalized raw items to ``items`` (the caller's lead collector).

        Returns (status, pages_inspected, results_inspected, raw_refs, note,
        retry_after_seconds).
        """
        pages_inspected = 0
        results_inspected = 0
        raw_refs: list = []
        note = ""
        retry_after: Optional[int] = None

        page = start_page
        total_count = 0
        incomplete = False

        while page - start_page < _MAX_PAGES_PER_QUERY:
            # Call budget: refuse to exceed the declared source-call ceiling.
            budget = self._plan.budget if self._plan is not None else None
            if budget is not None and self._source_calls >= budget.max_source_calls:
                note = "source-call budget exhausted before search completed"
                return (
                    AdapterStatus.PARTIAL_RESULTS,
                    pages_inspected,
                    results_inspected,
                    raw_refs,
                    note,
                    retry_after,
                )

            response = self._page_request(kind, query=query, per_page=per_page, page=page)
            self._source_calls += 1
            pages_inspected += 1
            raw_refs.append(_sha_of_body(response.body))

            # C06: distinguish AUTH_FAILURE (access denial) from RATE_LIMITED
            # (exhausted provider allowance). 401 is always AUTH_FAILURE. 403 is
            # RATE_LIMITED only when X-RateLimit-Remaining signals exhaustion;
            # otherwise it is AUTH_FAILURE. 429 is always RATE_LIMITED.
            remaining = self._transport.rate_limit_remaining(response)
            if response.status_code == 401:
                return (
                    AdapterStatus.AUTH_FAILURE,
                    pages_inspected,
                    0,
                    raw_refs,
                    "provider returned HTTP 401 (authentication failure)",
                    None,
                )
            if response.status_code == 403:
                if remaining is not None and remaining <= 0:
                    retry_after = self._retry_after_seconds(response)
                    return (
                        AdapterStatus.RATE_LIMITED,
                        pages_inspected,
                        results_inspected,
                        raw_refs,
                        "provider rate-limit exhausted (HTTP 403, X-RateLimit-Remaining: 0)",
                        retry_after,
                    )
                return (
                    AdapterStatus.AUTH_FAILURE,
                    pages_inspected,
                    0,
                    raw_refs,
                    "provider returned HTTP 403 (access denial)",
                    None,
                )
            if response.status_code == 429:
                retry_after = self._retry_after_seconds(response)
                return (
                    AdapterStatus.RATE_LIMITED,
                    pages_inspected,
                    results_inspected,
                    raw_refs,
                    "provider rate-limit exhausted (HTTP 429)",
                    retry_after,
                )
            if response.status_code >= 400:
                return (
                    AdapterStatus.PROVIDER_FAILURE,
                    pages_inspected,
                    results_inspected,
                    raw_refs,
                    "provider returned HTTP " + str(response.status_code),
                    None,
                )

            body = response.body
            if not isinstance(body, dict):
                return (
                    AdapterStatus.PROVIDER_FAILURE,
                    pages_inspected,
                    results_inspected,
                    raw_refs,
                    "provider returned a malformed (non-object) payload",
                    retry_after,
                )

            # C06: required response structure — items must exist and be a list.
            # A 200 with missing/malformed required fields is not a completed
            # empty search.
            if "items" not in body or not isinstance(body.get("items"), list):
                return (
                    AdapterStatus.PROVIDER_FAILURE,
                    pages_inspected,
                    results_inspected,
                    raw_refs,
                    "provider returned a 200 response missing the required 'items' list",
                    retry_after,
                )

            total_count = _total_count_from(body)
            incomplete = _incomplete_from(body)
            page_items = _items_from(body)

            # C06: consume X-RateLimit-Remaining — if the provider signals
            # exhaustion after a successful page, report partial (results from
            # this page are valid, but no more calls should be issued).
            remaining = self._transport.rate_limit_remaining(response)
            if remaining is not None and remaining <= 0:
                note = "provider rate-limit remaining exhausted after this page"
                retry_after = self._retry_after_seconds(response)
                return (
                    AdapterStatus.PARTIAL_RESULTS,
                    pages_inspected,
                    results_inspected,
                    raw_refs,
                    note,
                    retry_after,
                )

            for item in page_items:
                if results_inspected >= max_results:
                    note = "result limit reached before the surface was exhausted"
                    return (
                        AdapterStatus.PARTIAL_RESULTS,
                        pages_inspected,
                        results_inspected,
                        raw_refs,
                        note,
                        retry_after,
                    )
                items.append((item, kind))
                results_inspected += 1

            # Pagination honesty: stop when the surface is exhausted.
            if not page_items:
                break
            if results_inspected >= total_count and total_count > 0:
                break
            if incomplete:
                note = "provider reported incomplete results; completeness not established"
                return (
                    AdapterStatus.PARTIAL_RESULTS,
                    pages_inspected,
                    results_inspected,
                    raw_refs,
                    note,
                    retry_after,
                )

            page += 1

        # Loop ended without exhausting: cap hit or empty tail -> partial if we
        # did not consume the whole reported universe.
        if not note:
            if incomplete or (total_count > 0 and results_inspected < total_count):
                note = "search stopped before the reported result universe was exhausted"
                status = AdapterStatus.PARTIAL_RESULTS
            else:
                status = AdapterStatus.OK
        else:
            status = AdapterStatus.PARTIAL_RESULTS

        return status, pages_inspected, results_inspected, raw_refs, note, retry_after

    def _page_request(
        self,
        kind: str,
        *,
        query: DiscoveryQuery,
        per_page: int,
        page: int,
    ) -> GitHubResponse:
        """Issue one page request through the injected transport."""
        if kind == "repository":
            return self._transport.repository_search(
                q=query.concrete_query, per_page=per_page, page=page
            )
        return self._transport.code_search(
            q=query.concrete_query, per_page=per_page, page=page
        )

    def _normalize_item(
        self,
        item: dict,
        query: DiscoveryQuery,
        kind: str,
        completeness: SearchCompleteness = SearchCompleteness.COMPLETE,
    ) -> CandidateLead:
        """Normalize one raw provider item into a CandidateLead (C04 firewall).

        Popularity (stars/forks) and activity are recorded as raw observed
        signals only; they are never interpreted as capability evidence. The
        retrieved revision is explicitly missing because GitHub search returns
        mutable repository metadata, never an immutable commit SHA.

        Completeness reflects whether the surface search that yielded this
        lead was exhaustive (C07): a lead from a partial surface is PARTIAL,
        never COMPLETE.
        """
        if item.get("full_name"):
            full_name = str(item["full_name"])
            owner_repo = full_name
            html_url = item.get("html_url") or "https://github.com/" + full_name
            repository = item
        else:
            repository = item.get("repository") or {}
            repo_full_name = (
                repository.get("full_name")
                or item.get("repository_full_name")
                or ""
            )
            # C07: never fabricate github:unknown when repository identity is missing.
            if not repo_full_name:
                html_url = item.get("html_url") or ""
                owner_repo = html_url.replace("https://github.com/", "").rstrip("/") if html_url else ""
                if not owner_repo:
                    # No usable identity — skip this item rather than fabricating.
                    return None  # type: ignore[return-value]
            else:
                owner_repo = repo_full_name
                html_url = repository.get("html_url") or "https://github.com/" + repo_full_name

        source_locator = "github:" + owner_repo

        popularity_signals = {}
        for key in ("stargazers_count", "forks_count", "watchers_count", "size"):
            value = item.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                popularity_signals[key] = value

        activity_signals = {}
        for key in ("updated_at", "pushed_at", "created_at", "default_branch"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                activity_signals[key] = value
        activity_signals["source_url"] = html_url
        # C07: code-search provenance retains file/path identity without
        # pretending a blob SHA is a repository commit anchor.
        if kind == "code":
            path = item.get("path")
            if isinstance(path, str) and path.strip():
                activity_signals["path"] = path
            blob_sha = item.get("sha")
            if isinstance(blob_sha, str) and blob_sha.strip():
                activity_signals["blob_sha"] = blob_sha

        license_claim = ""
        license_block = item.get("license")
        if isinstance(license_block, dict) and license_block.get("spdx_id"):
            license_claim = str(license_block["spdx_id"])

        language_runtime = str(item.get("language") or "")

        lineage: QueryLineage = query.lineage_for(self.adapter_id)

        return make_candidate_lead(
            lead_id="lead-" + sha256(source_locator.encode("utf-8")).hexdigest()[:12],
            source_class=self.source_class,
            adapter_id=self.adapter_id,
            candidate_kind=CandidateKind.REPOSITORY,
            source_locator=source_locator,
            discovered_at=self._clock(),
            query_lineage=lineage,
            claimed_capabilities=tuple(
                c for c in (query.semantic_concept, query.concrete_query) if c
            ),
            possible_atom_matches=(query.atom_id,),
            retrieved_revision=MISSING_REVISION,
            language_runtime=language_runtime,
            license_claim=license_claim,
            activity_signals=activity_signals,
            popularity_signals=popularity_signals,
            initial_constraint_conflicts=(),
            novelty_family="",
            prior_evaluation_id="",
            raw_source_artifact_ref=_sha_of_body(item),
            completeness=completeness,
            notes=(
                "discovered via GitHub " + kind + " search for " + repr(query.concrete_query) + "; "
                "retrieved revision is a mutable repository reference, not an "
                "immutable commit anchor (deeper intelligence deferred); "
                "raw_source_artifact_ref is a non-durable response fingerprint, "
                "not a retrievable evidence artifact"
            ),
        )
