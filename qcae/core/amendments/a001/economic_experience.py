"""EconomicExperienceRecord — evidence about real external execution (A-001 §10–§11).

P0 scope: the minimum domain/reference contract needed for later P1 provenance
and registry work. No marketplace execution, no revenue automation, and no
economic-experience mutation authority lives here (reconciliation prompt §6).

Firewalls encoded:

- An EconomicExperienceRecord is evidence, not an instruction to self-modify,
  not institutional truth, not capability proof, and not trading proof.
- Client-specific/protected material fails closed against direct PROMOTED
  state (interface schema allOf condition; A-001 §11).
- PROMOTED state must cite the governed promotion path (promotion_refs);
  customer payment/acceptance can never constitute that citation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.amendments.a001.shared import A001_SCHEMA_VERSION, DataRights
from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_identifier,
    require_no_duplicates,
    require_non_empty_str,
    require_str_list,
)


class QaResult(StrEnum):
    PASS = "PASS"
    PASS_WITH_CAVEATS = "PASS_WITH_CAVEATS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"
    UNKNOWN = "UNKNOWN"


class CustomerAcceptance(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REVISED = "REVISED"
    TIMED_OUT = "TIMED_OUT"
    DISPUTED = "DISPUTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class EconomicOutcome(StrEnum):
    DELIVERED_PAID = "DELIVERED_PAID"
    DELIVERED_UNPAID = "DELIVERED_UNPAID"
    REJECTED = "REJECTED"
    ABANDONED = "ABANDONED"
    FAILED = "FAILED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class PromotionState(StrEnum):
    """Governed abstraction/promotion pipeline states (A-001 §11 canonical path)."""

    RAW = "RAW"
    RIGHTS_FILTERED = "RIGHTS_FILTERED"
    DEIDENTIFIED = "DEIDENTIFIED"
    ABSTRACTED = "ABSTRACTED"
    CLASSIFIED = "CLASSIFIED"
    REPRODUCED = "REPRODUCED"
    VALIDATED = "VALIDATED"
    SUBMITTED_FOR_INSTITUTIONAL_REVIEW = "SUBMITTED_FOR_INSTITUTIONAL_REVIEW"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True)
class EconomicsBlock(SerializableRecord):
    """Economic measurements (interface schema: economics object)."""

    SCHEMA_VERSION = 1

    gross_payout: float
    direct_cost: float
    compute_cost: float
    tool_cost: float
    currency: str = ""
    estimated_human_cost: Optional[float] = None
    net_contribution: Optional[float] = None

    def validate(self) -> None:
        for name in ("direct_cost", "compute_cost", "tool_cost"):
            value = getattr(self, name)
            if value < 0:
                raise QcaeValidationError(f"{name} must be >= 0, got {value!r}")
        if self.estimated_human_cost is not None and self.estimated_human_cost < 0:
            raise QcaeValidationError(
                f"estimated_human_cost must be >= 0, got {self.estimated_human_cost!r}"
            )


@dataclass(frozen=True)
class EconomicExperienceRecord(SerializableRecord):
    SCHEMA_VERSION = 1

    # A-001 interface schema version this contract mirrors (drift-guarded).
    interface_version: str = A001_SCHEMA_VERSION

    # -- identity -----------------------------------------------------------
    experience_id: str = ""
    source: str = ""
    opportunity_id: str = ""
    objective_type: str = ""

    # -- economics ------------------------------------------------------------
    economics: Optional[EconomicsBlock] = None

    # -- execution facts ------------------------------------------------------
    human_intervention_minutes: float = 0.0
    execution_time_seconds: float = 0.0
    capabilities_used: Tuple[str, ...] = ()
    research_used: Tuple[str, ...] = ()
    knowledge_gaps_found: Tuple[str, ...] = ()
    capability_gaps_found: Tuple[str, ...] = ()
    errors_encountered: Tuple[str, ...] = ()
    client_revisions: int = 0

    # -- acceptance/quality (never institutional truth) ------------------------
    qa_result: QaResult = QaResult.NOT_RUN
    customer_acceptance: CustomerAcceptance = CustomerAcceptance.UNKNOWN
    outcome: EconomicOutcome = EconomicOutcome.UNKNOWN

    # -- reuse potential -------------------------------------------------------
    reusability_score: Optional[float] = None
    transferability_score: Optional[float] = None
    lesson_candidates: Tuple[str, ...] = ()

    # -- rights and promotion firewall ------------------------------------------
    data_rights: DataRights = DataRights.UNKNOWN
    contains_client_specific_material: bool = False
    promotion_state: PromotionState = PromotionState.RAW
    promotion_refs: Tuple[str, ...] = ()

    recorded_at: str = ""

    _NESTED_RECORDS = {"economics": EconomicsBlock}
    _COERCIONS = {
        "qa_result": lambda v: coerce_enum(v, QaResult),
        "customer_acceptance": lambda v: coerce_enum(v, CustomerAcceptance),
        "outcome": lambda v: coerce_enum(v, EconomicOutcome),
        "promotion_state": lambda v: coerce_enum(v, PromotionState),
        "data_rights": lambda v: coerce_enum(v, DataRights),
    }

    def validate(self) -> None:
        if self.interface_version != A001_SCHEMA_VERSION:
            raise QcaeValidationError(
                f"interface_version {self.interface_version!r} does not match the "
                f"active A-001 interface schema ({A001_SCHEMA_VERSION})"
            )
        require_identifier(self.experience_id, "experience_id")
        require_non_empty_str(self.source, "source")
        if self.opportunity_id:
            require_identifier(self.opportunity_id, "opportunity_id")
        require_non_empty_str(self.objective_type, "objective_type")

        # Interface schema requires the economics block.
        if self.economics is None:
            raise QcaeValidationError("economics block is required")
        self.economics.validate()

        if self.human_intervention_minutes < 0 or self.execution_time_seconds < 0:
            raise QcaeValidationError(
                "human_intervention_minutes and execution_time_seconds must be >= 0"
            )
        if self.client_revisions < 0:
            raise QcaeValidationError("client_revisions must be >= 0")
        require_no_duplicates(self.capabilities_used, "capabilities_used")
        require_no_duplicates(self.research_used, "research_used")
        require_str_list(self.knowledge_gaps_found, "knowledge_gaps_found")
        require_str_list(self.capability_gaps_found, "capability_gaps_found")
        require_str_list(self.errors_encountered, "errors_encountered")
        require_str_list(self.lesson_candidates, "lesson_candidates")

        for name in ("reusability_score", "transferability_score"):
            value = getattr(self, name)
            if value is not None and not (0.0 <= value <= 1.0):
                raise QcaeValidationError(f"{name} must be within [0, 1], got {value!r}")

        for enum_field, enum_cls in (
            ("qa_result", QaResult),
            ("customer_acceptance", CustomerAcceptance),
            ("outcome", EconomicOutcome),
            ("promotion_state", PromotionState),
            ("data_rights", DataRights),
        ):
            if not isinstance(getattr(self, enum_field), enum_cls):
                raise QcaeValidationError(
                    f"{enum_field} must be a {enum_cls.__name__} member, "
                    f"got {getattr(self, enum_field)!r}"
                )

        require_non_empty_str(self.recorded_at, "recorded_at")

        # ---- promotion firewall (A-001 §10–§11) --------------------------------
        if self.contains_client_specific_material and (
            self.promotion_state == PromotionState.PROMOTED
        ):
            raise QcaeValidationError(
                "client-specific/protected material cannot reach PROMOTED state "
                "directly; rights review, de-identification, abstraction and the "
                "governed promotion path are required first (A-001 §11)"
            )
        if self.promotion_state == PromotionState.PROMOTED and not self.promotion_refs:
            raise QcaeValidationError(
                "PROMOTED requires promotion_refs citing the governed "
                "institutional review that admitted it; customer acceptance or "
                "payment is not such a citation"
            )
        # Customer acceptance alone must not imply the pipeline advanced:
        # a record still in RAW with accepted/paid outcome is legal only as
        # evidence, and every pipeline state beyond RAW must be justified by
        # the record's own rights state.
        if self.promotion_state != PromotionState.RAW and (
            self.contains_client_specific_material
            and self.data_rights in (DataRights.CLIENT_CONFIDENTIAL, DataRights.RESTRICTED)
            and self.promotion_state
            not in (PromotionState.RIGHTS_FILTERED, PromotionState.REJECTED, PromotionState.ARCHIVED)
        ):
            raise QcaeValidationError(
                f"protected client material ({self.data_rights}) cannot advance "
                f"to {self.promotion_state} before RIGHTS_FILTERED (A-001 §11)"
            )


def make_economic_experience(**kwargs) -> EconomicExperienceRecord:
    """Build and validate an economic experience record in one call."""
    record = EconomicExperienceRecord(**kwargs)
    record.validate()
    return record
