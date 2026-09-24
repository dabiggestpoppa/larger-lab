"""CSIA Book 3 — append-only architecture change history."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .architecture import Book2ArchitectureProvenance
from .temporal import Timestamp, UnknownBound, normalize_utc


class ArchitectureChangeType(str, Enum):
    CONSENSUS_CHANGE = "CONSENSUS_CHANGE"
    FINALITY_CHANGE = "FINALITY_CHANGE"
    VM_CHANGE = "VM_CHANGE"
    EXECUTION_MODEL_CHANGE = "EXECUTION_MODEL_CHANGE"
    DA_MIGRATION = "DA_MIGRATION"
    SETTLEMENT_MIGRATION = "SETTLEMENT_MIGRATION"
    SECURITY_PROVIDER_CHANGE = "SECURITY_PROVIDER_CHANGE"
    SEQUENCER_CHANGE = "SEQUENCER_CHANGE"
    RUNTIME_UPGRADE = "RUNTIME_UPGRADE"
    GOVERNANCE_CHANGE = "GOVERNANCE_CHANGE"
    NETWORK_RESTART = "NETWORK_RESTART"
    SHUTDOWN = "SHUTDOWN"
    FORK = "FORK"
    STATE_MIGRATION = "STATE_MIGRATION"


class ArchitectureChangeRecord(BaseModel):
    """Immutable event; prior architecture remains queryable in the store."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    change_type: ArchitectureChangeType
    before_refs: tuple[str, ...] = ()
    after_refs: tuple[str, ...] = ()
    claim_refs: tuple[str, ...] = Field(min_length=1)
    valid_time: Timestamp | UnknownBound
    observed_time: datetime
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def _shape(self) -> "ArchitectureChangeRecord":
        normalize_utc(self.observed_time)
        if not isinstance(self.valid_time, UnknownBound):
            normalize_utc(self.valid_time)
        if self.change_type not in (
            ArchitectureChangeType.NETWORK_RESTART,
            ArchitectureChangeType.SHUTDOWN,
            ArchitectureChangeType.FORK,
        ) and self.before_refs == self.after_refs:
            raise ValueError("architecture change requires distinct before and after refs")
        return self


class ArchitectureHistory:
    """In-memory append-only event history; no update or delete path."""

    def __init__(self, provenance: Book2ArchitectureProvenance) -> None:
        self.provenance = provenance
        self._records: dict[str, ArchitectureChangeRecord] = {}

    def append(self, record: ArchitectureChangeRecord) -> ArchitectureChangeRecord:
        if record.record_id in self._records:
            raise ValueError("architecture history record IDs are immutable and unique")
        for claim_ref in record.claim_refs:
            self.provenance.resolve_claim(claim_ref)
        self._records[record.record_id] = record
        return record

    def require(self, record_id: str) -> ArchitectureChangeRecord:
        try:
            return self._records[record_id]
        except KeyError as exc:
            raise KeyError(f"unknown architecture history record {record_id}") from exc

    def for_object(self, object_id: str) -> tuple[ArchitectureChangeRecord, ...]:
        return tuple(
            sorted(
                (record for record in self._records.values() if record.object_id == object_id),
                key=lambda record: (record.valid_time if isinstance(record.valid_time, datetime) else datetime.min.replace(tzinfo=record.observed_time.tzinfo), record.record_id),
            )
        )

    def all_records(self) -> tuple[ArchitectureChangeRecord, ...]:
        return tuple(self._records.values())


__all__ = [
    "ArchitectureChangeRecord",
    "ArchitectureChangeType",
    "ArchitectureHistory",
]
