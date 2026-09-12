"""ResearchCapabilityHandoff — typed QCAE ↔ Research Mesh boundary (A-001 §4–§5).

QCAE issues a handoff when capability acquisition depends on unresolved
knowledge. Research Mesh owns epistemic acquisition; QCAE owns executable
capability. This record is the *contract only*: it implements no research
institution, no literature ingestion, no consensus engine, and no doctrine
lifecycle (A-001 §7 no-duplication rules).

Semantics enforced here:

- A handoff is EVIDENCE INPUT. Its result can never directly mark executable
  capability as proven: this record has no lifecycle authority, carries no
  waiver, and QCAE proving obligations are unchanged (A-001 §4, invariant 4).
- Research Mesh absence must not make QCAE unusable; fallback results are
  marked ``LOCAL_FALLBACK_RESEARCH``, carry explicit uncertainty, and require
  Research Mesh revalidation before any high-dependency knowledge claim is
  treated as institutional knowledge (A-001 §5).
- Field names and vocabularies mirror the A-001 interface schema
  ``research-capability-handoff.schema.json`` v1.0. A drift guard test keeps
  them synchronized.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.amendments.a001.gaps import GapType
from qcae.core.amendments.a001.shared import A001_SCHEMA_VERSION, DataRights
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_hex_hash,
    require_identifier,
    require_no_duplicates,
    require_non_empty_str,
    require_str_list,
)


class HandoffDirection(StrEnum):
    QCAE_TO_RESEARCH_MESH = "QCAE_TO_RESEARCH_MESH"
    RESEARCH_MESH_TO_QCAE = "RESEARCH_MESH_TO_QCAE"


class HandoffMode(StrEnum):
    """Research Mesh operating modes (A-001 §9)."""

    INTERNAL_ACQUISITION = "INTERNAL_ACQUISITION"
    QCAE_CAPABILITY_RESEARCH = "QCAE_CAPABILITY_RESEARCH"
    CLIENT_RESEARCH_SERVICE = "CLIENT_RESEARCH_SERVICE"


class HandoffStatus(StrEnum):
    REQUESTED = "REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    REFUSED = "REFUSED"


class RequiredOutput(StrEnum):
    EVIDENCE_PACKAGE = "EVIDENCE_PACKAGE"
    SYNTHESIS = "SYNTHESIS"
    SPECIFICATION_INPUT = "SPECIFICATION_INPUT"
    ASSUMPTIONS = "ASSUMPTIONS"
    CONTRADICTIONS = "CONTRADICTIONS"
    TESTABLE_CLAIMS = "TESTABLE_CLAIMS"
    UNCERTAINTY = "UNCERTAINTY"
    PROVENANCE = "PROVENANCE"
    RECOMMENDED_NEXT_ACTION = "RECOMMENDED_NEXT_ACTION"


class FallbackClass(StrEnum):
    NONE = "NONE"
    LOCAL_FALLBACK_RESEARCH = "LOCAL_FALLBACK_RESEARCH"


#: Gap types a handoff can carry — the interface-schema subset of the full
#: core GapType taxonomy (research-capability-handoff.schema.json v1.0).
#: EXECUTION_FAILURE and INSTITUTIONAL_LEARNING_CANDIDATE route elsewhere and
#: cannot be requested through this boundary.
HANDOFF_GAP_TYPES: frozenset = frozenset(
    {GapType.KNOWLEDGE_GAP, GapType.CAPABILITY_GAP, GapType.MIXED_GAP}
)


#: Statuses that imply a usable result payload must exist.
RESULT_REQUIRED_STATUSES = frozenset({HandoffStatus.COMPLETED, HandoffStatus.PARTIAL})


@dataclass(frozen=True)
class HandoffConstraints(SerializableRecord):
    """Budget / data-rights / source-policy envelope (A-001 §4 request content)."""

    SCHEMA_VERSION = 1

    deadline: str = ""
    max_compute_cost_usd: Optional[float] = None
    max_tool_cost_usd: Optional[float] = None
    max_human_minutes: Optional[float] = None
    source_allowlist: Tuple[str, ...] = ()
    source_denylist: Tuple[str, ...] = ()
    data_rights: DataRights = DataRights.UNKNOWN

    _COERCIONS = {"data_rights": lambda v: coerce_enum(v, DataRights)}

    def validate(self) -> None:
        for name in ("max_compute_cost_usd", "max_tool_cost_usd", "max_human_minutes"):
            value = getattr(self, name)
            if value is not None and (value < 0):
                raise QcaeValidationError(f"{name} must be >= 0, got {value!r}")
        require_str_list(self.source_allowlist, "source_allowlist")
        require_str_list(self.source_denylist, "source_denylist")
        overlap = sorted(set(self.source_allowlist) & set(self.source_denylist))
        if overlap:
            raise QcaeValidationError(
                f"sources cannot be both allowed and denied: {overlap}"
            )
        if not isinstance(self.data_rights, DataRights):
            raise QcaeValidationError(
                f"data_rights must be a DataRights member, got {self.data_rights!r}"
            )


@dataclass(frozen=True)
class HandoffProvenance(SerializableRecord):
    """Required provenance block (interface schema: created_at + producer)."""

    SCHEMA_VERSION = 1

    created_at: str
    producer: str
    source_refs: Tuple[str, ...] = ()
    evidence_hashes: Tuple[str, ...] = ()
    parent_event_ids: Tuple[str, ...] = ()

    def validate(self) -> None:
        require_non_empty_str(self.created_at, "created_at")
        require_non_empty_str(self.producer, "producer")
        require_str_list(self.source_refs, "source_refs")
        for digest in self.evidence_hashes:
            require_hex_hash(digest, "evidence_hashes entry", min_length=8)
        require_str_list(self.parent_event_ids, "parent_event_ids")


@dataclass(frozen=True)
class HandoffResult(SerializableRecord):
    """Research Mesh response payload: evidence input, never proof."""

    SCHEMA_VERSION = 1

    finding: Optional[str] = None
    confidence: Optional[float] = None
    uncertainty: Optional[str] = None
    assumptions: Tuple[str, ...] = ()
    contradictions: Tuple[str, ...] = ()
    testable_claims: Tuple[str, ...] = ()
    specification_inputs: Tuple[dict, ...] = ()
    recommended_next_action: Optional[str] = None

    def validate(self) -> None:
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise QcaeValidationError(
                f"confidence must be within [0, 1], got {self.confidence!r}"
            )
        require_str_list(self.assumptions, "assumptions")
        require_str_list(self.contradictions, "contradictions")
        require_str_list(self.testable_claims, "testable_claims")
        for spec in self.specification_inputs:
            if not isinstance(spec, dict):
                raise QcaeValidationError(
                    f"specification_inputs entries must be objects, got {spec!r}"
                )


@dataclass(frozen=True)
class ResearchCapabilityHandoff(SerializableRecord):
    SCHEMA_VERSION = 1

    # A-001 interface schema version this contract mirrors (drift-guarded).
    interface_version: str = A001_SCHEMA_VERSION

    # -- required by the interface schema ----------------------------------
    direction: HandoffDirection = HandoffDirection.QCAE_TO_RESEARCH_MESH
    request_id: str = ""
    mode: HandoffMode = HandoffMode.QCAE_CAPABILITY_RESEARCH
    gap_type: GapType = GapType.KNOWLEDGE_GAP
    status: HandoffStatus = HandoffStatus.REQUESTED
    provenance: Optional[HandoffProvenance] = None

    # -- request content (A-001 §4) -----------------------------------------
    origin_objective_id: str = ""
    capability_gap_id: str = ""
    research_question: str = ""
    capability_context: dict = field(default_factory=dict)
    constraints: Optional[HandoffConstraints] = None
    required_outputs: Tuple[RequiredOutput, ...] = ()

    # -- response content (A-001 §4) -----------------------------------------
    result: Optional[HandoffResult] = None
    fallback_class: FallbackClass = FallbackClass.NONE

    _NESTED_RECORDS = {
        "provenance": HandoffProvenance,
        "constraints": HandoffConstraints,
        "result": HandoffResult,
    }
    _COERCIONS = {
        "direction": lambda v: coerce_enum(v, HandoffDirection),
        "mode": lambda v: coerce_enum(v, HandoffMode),
        "gap_type": lambda v: coerce_enum(v, GapType),
        "status": lambda v: coerce_enum(v, HandoffStatus),
        "fallback_class": lambda v: coerce_enum(v, FallbackClass),
    }

    def validate(self) -> None:
        if self.interface_version != A001_SCHEMA_VERSION:
            raise QcaeValidationError(
                f"interface_version {self.interface_version!r} does not match the "
                f"active A-001 interface schema ({A001_SCHEMA_VERSION})"
            )
        require_identifier(self.request_id, "request_id")
        for name in ("origin_objective_id", "capability_gap_id"):
            value = getattr(self, name)
            if value:
                require_identifier(value, name)
        if not isinstance(self.direction, HandoffDirection):
            raise QcaeValidationError(f"direction must be a HandoffDirection, got {self.direction!r}")
        if not isinstance(self.mode, HandoffMode):
            raise QcaeValidationError(f"mode must be a HandoffMode, got {self.mode!r}")
        if not isinstance(self.gap_type, GapType):
            raise QcaeValidationError(f"gap_type must be a GapType member, got {self.gap_type!r}")
        if self.gap_type not in HANDOFF_GAP_TYPES:
            raise QcaeValidationError(
                f"gap_type {self.gap_type} cannot be requested through the Research "
                "Mesh handoff boundary (interface schema allows only "
                "KNOWLEDGE_GAP/CAPABILITY_GAP/MIXED_GAP)"
            )
        if not isinstance(self.status, HandoffStatus):
            raise QcaeValidationError(f"status must be a HandoffStatus, got {self.status!r}")
        if not isinstance(self.fallback_class, FallbackClass):
            raise QcaeValidationError(
                f"fallback_class must be a FallbackClass member, got {self.fallback_class!r}"
            )

        # Provenance is required by the interface schema.
        if self.provenance is None:
            raise QcaeValidationError(
                "provenance is required (A-001: events and handoffs carry "
                "immutable provenance)"
            )
        self.provenance.validate()
        if self.constraints is not None:
            self.constraints.validate()

        # Request-side obligations (A-001 §4 minimum request content).
        if self.direction == HandoffDirection.QCAE_TO_RESEARCH_MESH:
            if not self.research_question.strip():
                raise QcaeValidationError(
                    "research_question is required on QCAE_TO_RESEARCH_MESH handoffs"
                )

        # Result payloads are Research Mesh responses, with exactly one
        # A-001 §5 exception: a local fallback result produced by QCAE when
        # Research Mesh is unavailable, recorded on the request direction and
        # marked LOCAL_FALLBACK_RESEARCH.
        if self.result is not None:
            self.result.validate()
            if (
                self.direction != HandoffDirection.RESEARCH_MESH_TO_QCAE
                and self.fallback_class != FallbackClass.LOCAL_FALLBACK_RESEARCH
            ):
                raise QcaeValidationError(
                    "a request-direction handoff cannot carry a result payload "
                    "unless it is a LOCAL_FALLBACK_RESEARCH result (A-001 §5)"
                )
        if self.status in RESULT_REQUIRED_STATUSES and self.result is None:
            raise QcaeValidationError(
                f"status {self.status} requires a result payload"
            )

        # A-001 §5: local fallback results carry explicit uncertainty and
        # cannot masquerade as institutional knowledge. A fallback declaration
        # without a result yet (REQUESTED/IN_PROGRESS) is legal.
        if self.fallback_class == FallbackClass.LOCAL_FALLBACK_RESEARCH and self.result is not None:
            if not (self.result.uncertainty or "").strip():
                raise QcaeValidationError(
                    "LOCAL_FALLBACK_RESEARCH results must carry an explicit "
                    "uncertainty statement (A-001 §5)"
                )

        require_no_duplicates(self.required_outputs, "required_outputs")
        for output in self.required_outputs:
            if not isinstance(output, RequiredOutput):
                raise QcaeValidationError(
                    f"required_outputs entries must be RequiredOutput members, "
                    f"got {output!r}"
                )
        if not isinstance(self.capability_context, dict):
            raise QcaeValidationError("capability_context must be an object")


def make_handoff(**kwargs) -> ResearchCapabilityHandoff:
    """Build and validate a handoff in one call."""
    handoff = ResearchCapabilityHandoff(**kwargs)
    handoff.validate()
    return handoff
