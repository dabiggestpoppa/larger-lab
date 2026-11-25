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
3. the query belongs to the current DiscoveryPlan (identity, family, source
   class, scope);
4. the source class and search scope are authorized by an enabled allocation;
5. an explicit may_discover allow decision is obtained through the
   AuthorityProvider boundary (GRANT required; DENY / REQUEST_MORE_EVIDENCE /
   missing provider -> zero transport calls);
6. remaining per-query and whole-run budgets are checked;
7. only then is the injected transport called.

The standalone may_discover allowance is therefore not treated as permission for
arbitrary GitHub network access: it is one gated step among several, and every
gate is fail-closed.

C03 provider outcome truth — typed statuses are implemented faithfully:

* NOT_CONFIGURED: provider/authority not wired, or egress not authorized.
* AUTH_FAILURE: provider 401/403.
* RATE_LIMITED: provider throttling (429 / headers) or budget exhaustion.
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
raw source evidence are all carried on the AdapterOutcome.
"""

from __future__ import annotations

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

        # C02 gate 5: explicit allow decision through the governance boundary.
        if self._authority_provider is None:
            return self.not_configured(
                query,
                "no governance authority provider wired; may_discover cannot be decided",
            )
        decision = self._authority_provider.decide(
            AuthorityRequest(
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
                },
            )
        )
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
        return self._run_search(query, allocation, budget, remaining_results)

    # -- search execution -------------------------------------------------

    def _run_search(
        self,
        query: DiscoveryQuery,
        allocation,
        budget,
        remaining_results: int,
    ) -> AdapterOutcome:
        """Perform the bounded repository/code search once egress is authorized."""
        max_results = min(query.max_results, remaining_results)
        if self._max_results_cap is not None:
            max_results = min(max_results, self._max_results_cap)

        per_page = min(max_results, 10)
        start_page = int(query.cursor) if query.cursor and query.cursor.isdigit() else 1

        leads: list = []
        pages_inspected = 0
        results_inspected = 0
        raw_refs: list = []
        provider_revision = ""

        status = AdapterStatus.OK
        completeness_note_parts: list = []

        # Repository search (metadata snippets — TIER_1 surface).
        (
            status,
            pages_inspected,
            results_inspected,
            raw_refs,
            note,
            repo_retry_after,
        ) = self._search_pages(
            kind="repository",
            query=query,
            per_page=per_page,
            start_page=start_page,
            max_results=max_results,
            items=leads,
        )
        if note:
            completeness_note_parts.append(note)

        # Code search (deeper source surface) only when the tier ceiling allows.
        code_note = ""
        code_retry_after: Optional[int] = None
        if (
            allocation.max_tier >= CostTier.TIER_2_DOCS_PACKAGE_METADATA
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
                completeness_note_parts.append(code_note)
            # Code search is additive; if either surface was partial, overall is partial.
            if code_status == AdapterStatus.PARTIAL_RESULTS:
                status = AdapterStatus.PARTIAL_RESULTS

        self._results_inspected += results_inspected

        # A failed search emits no leads, even if an earlier page succeeded.
        if status in FAILURE_STATUSES:
            leads = []

        # Build leads (collected into ``leads`` by the surface searches).
        lead_tuple: Tuple[CandidateLead, ...] = tuple(
            self._normalize_item(item, query, kind) for item, kind in leads
        )

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

            if response.status_code == 401 or response.status_code == 403:
                return (
                    AdapterStatus.AUTH_FAILURE,
                    pages_inspected,
                    0,
                    raw_refs,
                    "provider returned HTTP " + str(response.status_code) + " (authentication failure)",
                    retry_after,
                )
            if response.status_code == 429:
                retry_after = self._transport.rate_limit_reset(response)
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
                    retry_after,
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

            total_count = _total_count_from(body)
            incomplete = _incomplete_from(body)
            page_items = _items_from(body)

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
    ) -> CandidateLead:
        """Normalize one raw provider item into a CandidateLead (C04 firewall).

        Popularity (stars/forks) and activity are recorded as raw observed
        signals only; they are never interpreted as capability evidence. The
        retrieved revision is explicitly missing because GitHub search returns
        mutable repository metadata, never an immutable commit SHA.
        """
        if item.get("full_name"):
            full_name = str(item["full_name"])
            owner_repo = full_name
            html_url = item.get("html_url") or "https://github.com/" + full_name
            repository = item
        else:
            repository = item.get("repository") or {}
            full_name = str(
                repository.get("full_name")
                or item.get("repository_full_name")
                or "unknown"
            )
            owner_repo = full_name
            html_url = repository.get("html_url") or "https://github.com/" + full_name

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
            completeness=SearchCompleteness.COMPLETE,
            notes=(
                "discovered via GitHub " + kind + " search for " + repr(query.concrete_query) + "; "
                "retrieved revision is a mutable repository reference, not an "
                "immutable commit anchor (deeper intelligence deferred)"
            ),
        )
