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
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from qcae.core.discovery.lead import (
    FAILURE_STATUSES,
    PAYLOAD_STATUSES,
    AdapterStatus,
    CandidateLead,
    QueryLineage,
)
from qcae.core.discovery.plan import CostTier, SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_enum,
    require_identifier,
    require_non_empty_str,
    require_str_list,
)

__all__ = [
    "AdapterOutcome",
    "DiscoveryAdapterRegistry",
    "DiscoveryQuery",
    "DiscoverySourceAdapter",
    "make_discovery_query",
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
        "max_tier": lambda v: _coerce_tier(v),
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


def _coerce_tier(value: object) -> object:
    """Restore a CostTier from its serialized int/name form (see plan.py)."""
    if isinstance(value, CostTier):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        try:
            return CostTier(value)
        except ValueError:
            return value
    if isinstance(value, str):
        try:
            return CostTier[value]
        except KeyError:
            return value
    return value


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

    @property
    def counts_toward_saturation(self) -> bool:
        """Saturation counters only advance on searches that actually ran."""
        return self.status in PAYLOAD_STATUSES or self.status == AdapterStatus.NO_RESULTS


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


class DiscoveryAdapterRegistry:
    """Composition-wired map from source class to configured adapter (15.3).

    A single adapter serves exactly one source class, and an unregistered class
    is representable as missing rather than as an empty search: the planner must
    be able to report a gap in coverage instead of reporting a finished search
    (canon 2.2.15 "GitHub is not the universe", 2.1.13).
    """

    def __init__(self) -> None:
        self._adapters: Dict[SourceClass, DiscoverySourceAdapter] = {}

    def register(self, adapter: DiscoverySourceAdapter) -> None:
        """Register an adapter, refusing silent replacement of an existing one."""
        if not isinstance(adapter, DiscoverySourceAdapter):  # pragma: no cover - misuse guard
            raise QcaeValidationError("only DiscoverySourceAdapter instances may be registered")
        if adapter.source_class in self._adapters:
            raise QcaeValidationError(
                f"source class {adapter.source_class.value} already has adapter "
                f"{self._adapters[adapter.source_class].adapter_id!r}; "
                "replacing it must be an explicit composition decision"
            )
        if not adapter.adapter_id.strip():  # pragma: no cover - adapter contract
            raise QcaeValidationError("adapter_id must be non-empty")
        self._adapters[adapter.source_class] = adapter

    def adapter_for(self, source_class: SourceClass) -> Optional[DiscoverySourceAdapter]:
        """The adapter for a source class, or None when none is configured."""
        return self._adapters.get(source_class)

    def configured_source_classes(self) -> Tuple[SourceClass, ...]:
        """Every source class with a configured adapter, in registration order."""
        return tuple(self._adapters)

    def missing_source_classes(self, plan) -> Tuple[SourceClass, ...]:
        """Enabled plan source classes with no adapter — reported, never faked.

        The planner uses this to emit coverage gaps (``NOT_CONFIGURED``) so that
        an unconfigured surface is never mistaken for a capability absence.
        """
        return tuple(
            source_class
            for source_class in plan.enabled_source_classes()
            if source_class not in self._adapters
        )

    def close_all(self) -> List[str]:
        """Release every adapter that holds resources, returning their ids.

        Adapters may implement ``close()``; anything else is a no-op. Kept here
        so composition code never reaches into adapter internals.
        """
        closed: List[str] = []
        for adapter in self._adapters.values():
            close = getattr(adapter, "close", None)
            if callable(close):
                close()
                closed.append(adapter.adapter_id)
        return closed


def make_discovery_query(**kwargs) -> DiscoveryQuery:
    """Build and validate a discovery query in one call."""
    query = DiscoveryQuery(**kwargs)
    query.validate()
    return query
