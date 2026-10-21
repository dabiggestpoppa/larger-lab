"""Discovery source-adapter port — Book V 15.3 (provider-neutral discovery).

Canon 15.3 requires every discovery surface (GitHub, curated sensors, package
ecosystems, research/specification sources, internal indexes) to normalize into
one lead contract behind a common provider interface, because "the Discovery
Planner is provider-neutral" and "provider ranking does not become QCAE ranking".
Adapters own their provider quirks; the planner sees only
:class:`DiscoveryQuery` in and :class:`AdapterOutcome` out.

Three failure laws make the boundary honest:

- **A failing adapter returns no leads.** ``RATE_LIMITED``, ``AUTH_FAILURE``,
  ``PROVIDER_FAILURE``, ``UNSUPPORTED_QUERY`` and ``NOT_CONFIGURED`` are refused
  if they carry a payload, so a provider outage can never masquerade as results.
- **Partial is stated, not implied.** ``PARTIAL_RESULTS`` requires an explicit
  completeness note (canon 2.2.13: "a partial search must be marked partial
  rather than represented as exhaustive").
- **Absence of evidence is not evidence of absence.** ``NO_RESULTS`` (a
  completed empty search) is a different record from every failure status, and
  canon 2.1.13/2.2.15 require that distinction to survive into negative
  knowledge: a failed search never justifies "the capability does not exist".

``NOT_CONFIGURED`` is the standalone-first status (Book I 0.1: standalone now,
OCE-compatible by contract, OCE-governed later): QCAE must remain usable with no
external provider wired, and must say so rather than return a silent empty plan.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.discovery.lead import (
    FAILURE_STATUSES,
    PAYLOAD_STATUSES,
    AdapterStatus,
    CandidateLead,
    QueryLineage,
)
from qcae.core.discovery.vocabulary import CostTier, SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import (
    SerializableRecord,
    coerce_enum,
    coerce_int_enum,
)
from qcae.core.validation import (
    require_enum,
    require_hex_hash,
    require_identifier,
    require_non_empty_str,
    require_str_list,
)

__all__ = [
    "AdapterOutcome",
    "DiscoveryQuery",
    "DiscoverySourceAdapter",
    "ExecutionStatus",
    "ExecutedDiscoveryQuery",
    "execution_record_for",
    "make_discovery_query",
    "make_executed_query",
]


@dataclass(frozen=True)
class DiscoveryQuery(SerializableRecord):
    """One normalized search operation issued by the planner (Book V 15.3).

    The query carries the semantic anchor (``atom_id``/``semantic_concept``) and
    the plan's family, so an adapter can stamp exact lineage on every lead it
    returns without knowing what a capability contract is.
    """

    SCHEMA_VERSION = 1

    query_id: str
    family_id: str
    atom_id: str
    semantic_concept: str
    concrete_query: str
    source_class: SourceClass
    max_results: int = 20
    cursor: str = ""
    max_tier: CostTier = CostTier.TIER_1_METADATA_SNIPPETS

    _COERCIONS = {
        "source_class": lambda v: coerce_enum(v, SourceClass),
        "max_tier": lambda v: coerce_int_enum(v, CostTier),
    }

    def validate(self) -> None:
        require_identifier(self.query_id, "query_id")
        require_identifier(self.family_id, "family_id")
        require_identifier(self.atom_id, "atom_id")
        require_non_empty_str(self.semantic_concept, "semantic_concept")
        require_non_empty_str(self.concrete_query, "concrete_query")
        require_enum(self.source_class, SourceClass, "source_class")
        require_enum(self.max_tier, CostTier, "max_tier")
        if not isinstance(self.max_results, int) or isinstance(self.max_results, bool):
            raise QcaeValidationError("max_results must be an integer")
        if self.max_results < 1:
            raise QcaeValidationError(
                f"max_results must be >= 1, got {self.max_results!r}"
            )

    def lineage_for(self, adapter_id: str) -> QueryLineage:
        """Build the canon 2.1.4 lineage step this query will stamp on its leads."""
        return QueryLineage(
            atom_id=self.atom_id,
            semantic_concept=self.semantic_concept,
            family_id=self.family_id,
            concrete_query=self.concrete_query,
            source_class=self.source_class,
            adapter_id=adapter_id,
        )


@dataclass(frozen=True)
class AdapterOutcome(SerializableRecord):
    """Normalized adapter response with typed completeness and failure state."""

    SCHEMA_VERSION = 1

    adapter_id: str
    source_class: SourceClass
    query_id: str
    status: AdapterStatus
    retrieved_at: str = ""
    leads: Tuple[CandidateLead, ...] = ()
    pages_inspected: int = 0
    results_inspected: int = 0
    duplicate_count: int = 0
    novelty_count: int = 0
    raw_artifact_refs: Tuple[str, ...] = ()
    completeness_note: str = ""
    retry_after_seconds: Optional[int] = None
    message: str = ""
    cached: bool = False
    provider_revision: str = ""

    _COERCIONS = {
        "source_class": lambda v: coerce_enum(v, SourceClass),
        "status": lambda v: coerce_enum(v, AdapterStatus),
        "leads": tuple,
        "raw_artifact_refs": tuple,
    }

    _NESTED_RECORDS = {"leads": CandidateLead}

    #: The one execution record this outcome belongs to. A typed immutable
    #: ``ExecutedDiscoveryQuery`` set at assembly time; ``None`` until a caller
    #: binds it. Reporting refuses an outcome without one — an unattributed
    #: outcome is not this plan's evidence, whatever it claims to have found.
    execution_record: Optional["ExecutedDiscoveryQuery"] = None

    def validate(self) -> None:
        require_non_empty_str(self.adapter_id, "adapter_id")
        require_enum(self.source_class, SourceClass, "source_class")
        require_enum(self.status, AdapterStatus, "status")
        require_identifier(self.query_id, "query_id")
        require_str_list(self.raw_artifact_refs, "raw_artifact_refs")
        for name in ("pages_inspected", "results_inspected", "duplicate_count", "novelty_count"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise QcaeValidationError(f"{name} must be a non-negative integer, got {value!r}")
        if self.duplicate_count > self.results_inspected:
            raise QcaeValidationError(
                "duplicate_count cannot exceed results_inspected (canon 2.2.12: "
                "duplicate rate is measured against results actually inspected)"
            )
        if self.novelty_count > self.results_inspected:
            raise QcaeValidationError(
                "novelty_count cannot exceed results_inspected (canon 2.2.12)"
            )
        if self.retry_after_seconds is not None and (
            not isinstance(self.retry_after_seconds, int)
            or isinstance(self.retry_after_seconds, bool)
            or self.retry_after_seconds < 0
        ):
            raise QcaeValidationError("retry_after_seconds must be a non-negative integer or None")
        if not isinstance(self.cached, bool):
            raise QcaeValidationError("cached must be a bool")

        # A failing adapter must not carry a payload: an outage is not a result.
        if self.status in FAILURE_STATUSES:
            if self.leads:
                raise QcaeValidationError(
                    f"adapter status {self.status.value} cannot carry leads; failures "
                    "must not be reported as results (canon 2.1.13)"
                )
            require_non_empty_str(self.message, "message")
        # NO_RESULTS is a completed empty search — mutually exclusive with OK.
        if self.status == AdapterStatus.NO_RESULTS and self.leads:
            raise QcaeValidationError(
                "NO_RESULTS cannot carry leads; use OK for a search that returned results"
            )
        if self.status == AdapterStatus.OK and not self.leads:
            raise QcaeValidationError(
                "OK requires at least one lead; an empty completed search is NO_RESULTS"
            )
        if self.status in PAYLOAD_STATUSES and self.pages_inspected < 1:
            raise QcaeValidationError(
                f"{self.status.value} requires pages_inspected >= 1; results cannot "
                "appear from an unperformed search"
            )
        # Canon 2.2.13: a partial search is labeled partial.
        if self.status == AdapterStatus.PARTIAL_RESULTS and not self.completeness_note.strip():
            raise QcaeValidationError(
                "PARTIAL_RESULTS requires a completeness note: a partial search must "
                "never be represented as exhaustive (canon 2.2.13)"
            )
        for lead in self.leads:
            lead.validate()
            if lead.adapter_id != self.adapter_id:
                raise QcaeValidationError(
                    f"lead {lead.lead_id!r} came from adapter {lead.adapter_id!r}, not "
                    f"the responding adapter {self.adapter_id!r}"
                )
            if lead.source_class != self.source_class:
                raise QcaeValidationError(
                    f"lead {lead.lead_id!r} claims source class "
                    f"{lead.source_class.value}, not the responding class "
                    f"{self.source_class.value}"
                )
            if lead.query_lineage.family_id != "" and lead.query_lineage.atom_id == "":
                raise QcaeValidationError(
                    f"lead {lead.lead_id!r} carries an incomplete query lineage"
                )

    # -- derived standing ---------------------------------------------------

    @property
    def exhaustive(self) -> bool:
        """True only for a completed, unqualified search (canon 2.2.13)."""
        return self.status == AdapterStatus.OK and not self.completeness_note.strip()

    @property
    def is_failure(self) -> bool:
        """True when no search conclusion may be drawn from this outcome."""
        return self.status in FAILURE_STATUSES

    def bind_execution_record(
        self, record: "ExecutedDiscoveryQuery"
    ) -> "AdapterOutcome":
        """Return this outcome bound to exactly one execution record.

        Dataclasses are frozen, so binding is a validated replacement: the
        record must be an ``ExecutedDiscoveryQuery`` whose query identity and
        envelope match the outcome's own claims, otherwise the binding itself
        is refused instead of legitimizing a forged pairing.
        """
        if not isinstance(record, ExecutedDiscoveryQuery):
            raise QcaeValidationError(
                f"an outcome binds to an ExecutedDiscoveryQuery, got {type(record).__name__}"
            )
        if record.source_class != self.source_class:
            raise QcaeValidationError(
                f"execution record for query {record.query_id!r} declares source class "
                f"{record.source_class.value}, the outcome claims {self.source_class.value}"
            )
        if record.adapter_id != self.adapter_id:
            raise QcaeValidationError(
                f"execution record for query {record.query_id!r} names adapter "
                f"{record.adapter_id!r}, the outcome came from {self.adapter_id!r}"
            )
        bound = replace(self, execution_record=record)
        return bound

    @property
    def counts_toward_saturation(self) -> bool:
        """Saturation counters only advance on searches that actually ran."""
        return self.status in PAYLOAD_STATUSES or self.status == AdapterStatus.NO_RESULTS


class ExecutionStatus(StrEnum):
    """Typed execution states for one planned query (canon 2.1.4/2.1.17)."""

    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


def _require_rfc3339_utc(value: str, what: str) -> None:
    """Authoritative timestamps are validated UTC RFC3339 (canon 0.4.6 class)."""
    import re

    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise QcaeValidationError(
            f"{what} must be an RFC3339 UTC timestamp (YYYY-MM-DDTHH:MM:SSZ), got {value!r}"
        )


@dataclass(frozen=True)
class ExecutedDiscoveryQuery(SerializableRecord):
    """The immutable record of one planned query that was actually run.

    Every ``AdapterOutcome`` must bind to exactly one of these (canon 2.1.4/2.1.17
    invariant 4: search provenance is retained end to end). The record binds the
    plan's authorization to the adapter's execution so a caller can never smuggle
    an outcome in without the query that produced it:

    - identity: which plan/contract authorized the query, which family and atom
      it served, its semantic concept and its concrete query (or a safe
      deterministic digest when the raw query is not carried);
    - envelope: which source class, adapter, result limit and cost tier the plan
      authorized;
    - execution: what happened, when, against which provider revision, with which
      evidence artifacts, and which outcome identity it produced.

    The query digest is ``sha256`` over the canonical encoding of the query that
    ran (``sha256_of``), so the same query always carries the same digest and a
    different query can never inherit one's lineage.
    """

    SCHEMA_VERSION = 1

    discovery_plan_id: str
    contract_id: str
    contract_version: int
    query_id: str
    family_id: str
    atom_id: str
    semantic_concept: str
    concrete_query: str
    source_class: SourceClass
    adapter_id: str
    result_limit: int
    max_tier: CostTier
    status: ExecutionStatus
    executed_at: str
    query_digest: str = ""
    completed_at: str = ""
    provider_revision: str = ""
    evidence_refs: Tuple[str, ...] = ()
    outcome_id: str = ""

    _COERCIONS = {
        "source_class": lambda v: coerce_enum(v, SourceClass),
        "max_tier": lambda v: coerce_int_enum(v, CostTier),
        "status": lambda v: coerce_enum(v, ExecutionStatus),
        "evidence_refs": tuple,
    }

    def validate(self) -> None:
        require_identifier(self.discovery_plan_id, "discovery_plan_id")
        require_identifier(self.contract_id, "contract_id")
        if not isinstance(self.contract_version, int) or isinstance(
            self.contract_version, bool
        ) or self.contract_version < 1:
            raise QcaeValidationError("contract_version must be an integer >= 1")
        # One planned query, one execution: a repeated execution of the same
        # planned query carries an ordinal suffix (#2, #3, ...) so two outcomes
        # can never bind one record. The base stays a stable identifier.
        base_query_id, _, ordinal = self.query_id.partition("#")
        require_identifier(base_query_id, "query_id")
        if ordinal and not (
            ordinal.isdigit() and len(ordinal) <= 4 and int(ordinal) >= 2
        ):
            raise QcaeValidationError(
                f"query_id {self.query_id!r} carries an invalid execution ordinal; "
                "repeated executions of one planned query are numbered from #2"
            )
        require_identifier(self.family_id, "family_id")
        require_identifier(self.atom_id, "atom_id")
        require_non_empty_str(self.semantic_concept, "semantic_concept")
        # The query is carried either verbatim or as a deterministic digest;
        # an execution record with neither has no lineage to check leads against.
        if not self.concrete_query.strip() and not self.query_digest.strip():
            raise QcaeValidationError(
                "an execution record must carry its concrete query or a deterministic "
                "query digest; lineage without a query is not verifiable (canon 2.1.4)"
            )
        if self.query_digest.strip():
            require_hex_hash(self.query_digest, "query_digest", min_length=16)
        require_enum(self.source_class, SourceClass, "source_class")
        require_non_empty_str(self.adapter_id, "adapter_id")
        if not isinstance(self.result_limit, int) or isinstance(
            self.result_limit, bool
        ) or self.result_limit < 1:
            raise QcaeValidationError(f"result_limit must be an integer >= 1, got {self.result_limit!r}")
        require_enum(self.max_tier, CostTier, "max_tier")
        if not isinstance(self.status, ExecutionStatus):
            raise QcaeValidationError(f"status must be an ExecutionStatus member, got {self.status!r}")
        _require_rfc3339_utc(self.executed_at, "executed_at")
        if self.completed_at:
            _require_rfc3339_utc(self.completed_at, "completed_at")
            if self.completed_at < self.executed_at:
                raise QcaeValidationError(
                    "completed_at cannot precede executed_at: the record would claim "
                    "the search finished before it started"
                )
        require_str_list(self.evidence_refs, "evidence_refs")
        if self.outcome_id:
            require_identifier(self.outcome_id, "outcome_id")

    @property
    def lineage(self) -> QueryLineage:
        """The canon 2.1.4 lineage step this execution stamps on its leads."""
        return QueryLineage(
            atom_id=self.atom_id,
            semantic_concept=self.semantic_concept,
            family_id=self.family_id,
            concrete_query=self.concrete_query,
            source_class=self.source_class,
            adapter_id=self.adapter_id,
        )


def make_executed_query(**kwargs) -> ExecutedDiscoveryQuery:
    """Build and validate an execution record in one call."""
    record = ExecutedDiscoveryQuery(**kwargs)
    record.validate()
    return record


def execution_record_for(
    query: DiscoveryQuery,
    plan,
    *,
    adapter_id: str,
    status: ExecutionStatus,
    executed_at: str,
    result_limit: Optional[int] = None,
    provider_revision: str = "",
    evidence_refs: Tuple[str, ...] = (),
    outcome_id: str = "",
    completed_at: str = "",
    query_digest: str = "",
) -> ExecutedDiscoveryQuery:
    """Bind one planned query to its plan's authorization and execution truth.

    The plan supplies the authorization (plan id, contract identity, tier
    ceiling); the query supplies the semantics (family, atom, concept, query,
    source class); the caller supplies what only it knows — the adapter that
    ran, when, with which status, provider revision and evidence references.
    The result limit is the query's own unless the adapter narrowed it, and it
    can never exceed what the plan authorized.
    """
    limit = query.max_results if result_limit is None else result_limit
    if limit > query.max_results:
        raise QcaeValidationError(
            f"execution result_limit {limit} exceeds the planned query's "
            f"max_results {query.max_results}; an adapter may narrow but never widen "
            "the plan's envelope"
        )
    record = ExecutedDiscoveryQuery(
        discovery_plan_id=plan.discovery_plan_id,
        contract_id=plan.contract_id,
        contract_version=plan.contract_version,
        query_id=query.query_id,
        family_id=query.family_id,
        atom_id=query.atom_id,
        semantic_concept=query.semantic_concept,
        concrete_query=query.concrete_query,
        source_class=query.source_class,
        adapter_id=adapter_id,
        result_limit=limit,
        max_tier=min(query.max_tier, plan.cost_tier_ceiling),
        status=ExecutionStatus(status),
        executed_at=executed_at,
        query_digest=query_digest,
        completed_at=completed_at,
        provider_revision=provider_revision,
        evidence_refs=tuple(evidence_refs),
        outcome_id=outcome_id,
    )
    record.validate()
    return record


class DiscoverySourceAdapter(ABC):
    """Provider-neutral discovery surface (Book V 15.3).

    Adapters own authentication, pagination, rate-limit semantics and provider
    ranking. They may not: emit a verification level, apply QCAE ranking, retry
    past their declared budget, or turn a failure into an empty success.
    """

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        """Stable adapter identity recorded in lead provenance."""

    @property
    @abstractmethod
    def source_class(self) -> SourceClass:
        """The one source class this adapter serves (canon 2.1.5)."""

    @abstractmethod
    def search(self, query: DiscoveryQuery) -> AdapterOutcome:
        """Run one bounded normalized search and return a typed outcome."""

    def close(self) -> None:
        """Release provider resources; the default holds none.

        Declared on the port so composition releases adapters through their own
        interface instead of probing their internals: a ``getattr`` probe
        silently skipped cleanup whenever an adapter's hook was named or shaped
        differently, and nothing recorded that it had been skipped. An adapter
        that does hold resources must override this and must not raise.
        """

    # -- shared helpers: uniform standalone/failure reporting ---------------

    def not_configured(
        self, query: DiscoveryQuery, message: str = "provider not configured"
    ) -> AdapterOutcome:
        """The standalone-first outcome: capability absent, search not performed."""
        outcome = AdapterOutcome(
            adapter_id=self.adapter_id,
            source_class=self.source_class,
            query_id=query.query_id,
            status=AdapterStatus.NOT_CONFIGURED,
            message=message,
        )
        outcome.validate()
        return outcome

    def unsupported(
        self, query: DiscoveryQuery, message: str = "query unsupported by this adapter"
    ) -> AdapterOutcome:
        """A query this surface cannot express (Book V 15.3 failure semantics)."""
        outcome = AdapterOutcome(
            adapter_id=self.adapter_id,
            source_class=self.source_class,
            query_id=query.query_id,
            status=AdapterStatus.UNSUPPORTED_QUERY,
            message=message,
        )
        outcome.validate()
        return outcome

    def rate_limited(
        self,
        query: DiscoveryQuery,
        message: str,
        retry_after_seconds: Optional[int] = None,
    ) -> AdapterOutcome:
        """Budget/rate exhaustion, reported instead of silently truncated."""
        outcome = AdapterOutcome(
            adapter_id=self.adapter_id,
            source_class=self.source_class,
            query_id=query.query_id,
            status=AdapterStatus.RATE_LIMITED,
            message=message,
            retry_after_seconds=retry_after_seconds,
        )
        outcome.validate()
        return outcome


def make_discovery_query(**kwargs) -> DiscoveryQuery:
    """Build and validate a discovery query in one call."""
    query = DiscoveryQuery(**kwargs)
    query.validate()
    return query
