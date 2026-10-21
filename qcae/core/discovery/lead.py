"""Normalized candidate leads + query lineage — canon 2.1.11, 2.1.4, Book V 15.3.

A **lead** is what a discovery adapter may emit: a normalized observation of
something that might implement a capability. Book V 15.3 lists the common
adapter output and states it "should not emit ``VERIFIED_CAPABILITY``"
(canon 2.3.12 says the same for sensors). The enforcement here is structural:

- :class:`CandidateLead` has **no verification field at all**, so no adapter can
  express confidence as a verification level even by accident. The read-only
  ``claim_verification`` property always answers ``DISCOVERED``, which is where
  canon 2.7.4 puts a ranked candidate ("the state transition is from
  ``DISCOVERED`` toward ``UNDER_REPOSITORY_INTELLIGENCE``, not toward
  ``ACCEPTED``").
- Popularity and activity arrive as raw recorded signals
  (``popularity_signals``/``activity_signals``); canon 2.2.9/2.2.8 make them
  weak, context-dependent operational signals, never capability evidence, so
  they are carried as observed numbers and interpreted nowhere in core.
- ``retrieved_revision`` is carried but never assumed: canon 2.2.5 requires an
  immutable commit anchor when a candidate enters deeper intelligence, which
  :attr:`CandidateLead.deeper_intelligence_ready` makes mechanical.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Dict, Tuple

from qcae.core.discovery.vocabulary import SourceClass
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_enum,
    require_identifier,
    require_non_empty_str,
    require_str_list,
)
from qcae.core.vocabulary import VerificationLevel

__all__ = [
    "AdapterStatus",
    "CandidateKind",
    "CandidateLead",
    "QueryLineage",
    "SearchCompleteness",
    "make_candidate_lead",
]


class AdapterStatus(StrEnum):
    """Typed discovery-adapter outcomes (Book V 15.3 failure semantics).

    ``NOT_CONFIGURED`` is the standalone-first status: canonical QCAE must remain
    usable with no external provider wired (Book I 0.1, A-001 §5), and an absent
    provider must be *reported*, never represented as an empty-but-successful
    search.
    """

    OK = "OK"
    NO_RESULTS = "NO_RESULTS"
    PARTIAL_RESULTS = "PARTIAL_RESULTS"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_FAILURE = "AUTH_FAILURE"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    UNSUPPORTED_QUERY = "UNSUPPORTED_QUERY"
    NOT_CONFIGURED = "NOT_CONFIGURED"


#: Statuses that mean the adapter produced no usable leads. A failing adapter
#: must not be read as "the capability does not exist" (canon 2.1.13: absence is
#: not proof of nonexistence) — only ``NO_RESULTS`` is a completed empty search.
FAILURE_STATUSES: frozenset = frozenset(
    {
        AdapterStatus.RATE_LIMITED,
        AdapterStatus.AUTH_FAILURE,
        AdapterStatus.PROVIDER_FAILURE,
        AdapterStatus.UNSUPPORTED_QUERY,
        AdapterStatus.NOT_CONFIGURED,
    }
)

#: Statuses that carry a usable (possibly incomplete) lead payload.
PAYLOAD_STATUSES: frozenset = frozenset({AdapterStatus.OK, AdapterStatus.PARTIAL_RESULTS})


class CandidateKind(StrEnum):
    """The shape of thing a lead points at (canon 2.1.11 ``candidate_kind``)."""

    REPOSITORY = "REPOSITORY"
    PACKAGE = "PACKAGE"
    SERVICE = "SERVICE"
    SPECIFICATION = "SPECIFICATION"
    PAPER = "PAPER"
    CURATED_ENTRY = "CURATED_ENTRY"
    INTERNAL_CODE = "INTERNAL_CODE"
    DATASET = "DATASET"
    REFERENCE_IMPLEMENTATION = "REFERENCE_IMPLEMENTATION"


class SearchCompleteness(StrEnum):
    """Whether the query that produced this lead was exhaustive (2.2.12/2.2.13)."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class QueryLineage(SerializableRecord):
    """One lineage step: atom -> concept -> family -> query -> source (canon 2.1.4).

    Canon 2.1.4 requires the planner to preserve this chain, and 2.1.17
    invariant 4 requires search provenance to be retained. Every lead carries
    the step that found it, so a ranked candidate can always be traced back to
    the capability semantics that justified searching for it.
    """

    SCHEMA_VERSION = 1

    atom_id: str
    semantic_concept: str
    family_id: str
    concrete_query: str
    source_class: SourceClass
    adapter_id: str

    _COERCIONS = {"source_class": lambda v: coerce_enum(v, SourceClass)}

    def validate(self) -> None:
        require_identifier(self.atom_id, "atom_id")
        require_non_empty_str(self.semantic_concept, "semantic_concept")
        require_identifier(self.family_id, "family_id")
        require_non_empty_str(self.concrete_query, "concrete_query")
        require_enum(self.source_class, SourceClass, "source_class")
        require_non_empty_str(self.adapter_id, "adapter_id")


def _require_signal_map(value: object, what: str) -> None:
    """Signals are flat observed facts, never nested interpretation.

    Records freeze mappings on construction (P3-R4C5), so a frozen mapping is
    the expected shape here; ``dict(...)`` reads either a dict or a proxy.
    """
    if not isinstance(value, (dict, MappingProxyType)):
        raise QcaeValidationError(f"{what} must be a flat mapping, got {type(value).__name__}")
    for key, item in dict(value).items():
        if not isinstance(key, str) or not key.strip():
            raise QcaeValidationError(f"{what} keys must be non-empty strings, got {key!r}")
        if isinstance(item, bool) or isinstance(item, (str, int, float)):
            continue
        raise QcaeValidationError(
            f"{what}[{key!r}] must be a scalar observed value, got {type(item).__name__}"
        )


@dataclass(frozen=True)
class CandidateLead(SerializableRecord):
    """Discovery intake record (canon 2.1.11) normalized for adapter output (15.3)."""

    SCHEMA_VERSION = 1

    lead_id: str
    source_class: SourceClass
    adapter_id: str
    candidate_kind: CandidateKind
    source_locator: str
    discovered_at: str
    query_lineage: QueryLineage
    claimed_capabilities: Tuple[str, ...] = ()
    possible_atom_matches: Tuple[str, ...] = ()
    retrieved_revision: str = ""
    language_runtime: str = ""
    license_claim: str = ""
    activity_signals: Dict[str, object] = field(default_factory=dict)
    popularity_signals: Dict[str, object] = field(default_factory=dict)
    initial_constraint_conflicts: Tuple[str, ...] = ()
    novelty_family: str = ""
    prior_evaluation_id: str = ""
    raw_source_artifact_ref: str = ""
    completeness: SearchCompleteness = SearchCompleteness.COMPLETE
    notes: str = ""

    _COERCIONS = {
        "source_class": lambda v: coerce_enum(v, SourceClass),
        "candidate_kind": lambda v: coerce_enum(v, CandidateKind),
        "completeness": lambda v: coerce_enum(v, SearchCompleteness),
        "claimed_capabilities": tuple,
        "possible_atom_matches": tuple,
        "initial_constraint_conflicts": tuple,
    }

    _NESTED_RECORDS = {"query_lineage": QueryLineage}

    # -- validation ---------------------------------------------------------

    def validate(self) -> None:
        require_identifier(self.lead_id, "lead_id")
        require_enum(self.source_class, SourceClass, "source_class")
        require_enum(self.candidate_kind, CandidateKind, "candidate_kind")
        require_enum(self.completeness, SearchCompleteness, "completeness")
        require_non_empty_str(self.adapter_id, "adapter_id")
        require_non_empty_str(self.source_locator, "source_locator")
        require_non_empty_str(self.discovered_at, "discovered_at")
        self.query_lineage.validate()
        if self.query_lineage.source_class != self.source_class:
            raise QcaeValidationError(
                f"lead source_class {self.source_class.value} disagrees with its query "
                f"lineage {self.query_lineage.source_class.value}"
            )
        if self.query_lineage.adapter_id != self.adapter_id:
            raise QcaeValidationError(
                "lead adapter_id disagrees with its query lineage adapter_id; "
                "provenance must name the adapter that actually returned the lead"
            )
        require_str_list(self.claimed_capabilities, "claimed_capabilities")
        require_str_list(self.possible_atom_matches, "possible_atom_matches")
        if not self.claimed_capabilities and not self.possible_atom_matches:
            raise QcaeValidationError(
                "a lead must attach to at least one claimed capability or possible "
                "atom match; capability is the acquisition object (canon 0.2.1)"
            )
        require_str_list(self.initial_constraint_conflicts, "initial_constraint_conflicts")
        _require_signal_map(self.activity_signals, "activity_signals")
        _require_signal_map(self.popularity_signals, "popularity_signals")
        if self.prior_evaluation_id:
            require_identifier(self.prior_evaluation_id, "prior_evaluation_id")
        if self.candidate_kind == CandidateKind.INTERNAL_CODE:
            if self.source_class != SourceClass.INTERNAL_REGISTRY_CODE:
                raise QcaeValidationError(
                    "internal code leads must come from the internal registry/code "
                    "source class (canon 2.6.2)"
                )
        if self.candidate_kind == CandidateKind.SPECIFICATION and self.license_claim:
            raise QcaeValidationError(
                "specifications do not carry a software license claim; record "
                "access/normative notes instead (canon 2.5.11)"
            )

    # -- derived standing ---------------------------------------------------

    @property
    def claim_verification(self) -> VerificationLevel:
        """Always ``DISCOVERED``: a lead is an observation, not a verified claim.

        Canon 2.1.11 ("these are discovery observations, not verified facts unless
        the evidence warrants that state") and 2.7.4 (ranking is triage) make any
        stronger value unrepresentable rather than merely discouraged.
        """
        return VerificationLevel.DISCOVERED

    @property
    def deeper_intelligence_ready(self) -> bool:
        """Whether this lead may be escalated to Block 3 repository intelligence.

        Canon 2.2.5: deeper analysis is anchored to an immutable revision. A
        moving branch or an incomplete search is not an acceptable sole identity
        for evidence, so both an immutable revision and a completed query are
        required.
        """
        return bool(self.retrieved_revision.strip()) and (
            self.completeness == SearchCompleteness.COMPLETE
        )

    @property
    def independent_source_classes(self) -> Tuple[SourceClass, ...]:
        """Source classes that surfaced this lead (one lead = one observation).

        Multi-source corroboration is counted by the ranking layer over merged
        candidates, never here: canon 2.1.12 forbids counting repeated discovery
        as independent evidence of capability quality.
        """
        return (self.source_class,)


def make_candidate_lead(**kwargs) -> CandidateLead:
    """Build and validate a candidate lead in one call."""
    lead = CandidateLead(**kwargs)
    lead.validate()
    return lead
