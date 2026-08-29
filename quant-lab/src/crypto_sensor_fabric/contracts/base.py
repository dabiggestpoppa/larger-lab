"""Bloc 1 canonical observation base contract.

Implements the shared T1 observation fields and invariants from
`bloc_01/02_SCHEMA_AND_PROVIDER_REGISTRY.md` §2:

- every observation carries provider + venue identity (never erased)
- every observation traces to an immutable raw object pointer + checksum
- effective/observed/ingested timestamps are distinct and UTC-normalized
- unresolved canonical identity is legal only with INSTRUMENT_ID_UNRESOLVED
- canonical serialization is deterministic under the same schema version
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import (
    AccessClass,
    ContractType,
    EvidenceClass,
    MarketType,
    MissingReason,
    QualityFlag,
    RetrievalMode,
    SemanticEquivalence,
    SensorFamily,
)


def coerce_utc(value: datetime) -> datetime:
    """Require timezone-aware datetimes and normalize to UTC.

    Naive datetimes are rejected outright (Bloc 1 B1-T04): no silent local-time
    assumption is allowed.  If a provider needs naive-source handling, the
    adapter must apply an explicit source-timezone rule before building a
    canonical observation.
    """
    if value.tzinfo is None:
        raise ValueError(
            f"naive datetime {value.isoformat()!r} is not allowed; "
            "supply a timezone-aware timestamp or apply an explicit source-timezone rule"
        )
    return value.astimezone(UTC)


def normalize_utc_datetimes(model: BaseModel) -> BaseModel:
    """Normalize every top-level datetime field on the model to UTC."""
    for name in type(model).model_fields:
        value = getattr(model, name)
        if isinstance(value, datetime):
            setattr(model, name, coerce_utc(value))
    return model


class CanonicalObservationBase(BaseModel):
    """Logical base of every T1 canonical observation (02 §2).

    Invariants (enforced):

    - `instrument_native` is never null (B1-T02).
    - `provider`, `venue`, `raw_object_uri`, `raw_checksum`, `schema_version`,
      `adapter_version` are required (B1-T01, B1-T05).
    - all datetime fields are timezone-aware and UTC after validation (B1-T04).
    - `instrument_id_canonical = None` is legal only when
      `INSTRUMENT_ID_UNRESOLVED` is present in `quality_flags` (B1-T03).

    Documented invariants (not schema-enforced):

    - `effective_at <= observed_at` except for provider-published future-effective
      information (e.g. announced funding); exceptions require methodology notes.
    - historical backfills may legitimately have modern `ingested_at` far after
      `observed_at`.
    """

    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    provider: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    evidence_class: EvidenceClass
    retrieval_mode: RetrievalMode

    instrument_native: str = Field(min_length=1)
    instrument_id_canonical: str | None = None
    market_type: MarketType
    base_asset: str | None = None
    quote_asset: str | None = None
    settlement_asset: str | None = None
    contract_type: ContractType | None = None
    contract_multiplier: float | None = None
    is_inverse: bool | None = None

    effective_at: datetime
    observed_at: datetime
    ingested_at: datetime
    window_start: datetime | None = None
    window_end: datetime | None = None
    source_interval: str | None = None

    endpoint_id: str = Field(min_length=1)
    source_record_id: str | None = None
    raw_object_uri: str = Field(min_length=1)
    raw_checksum: str = Field(min_length=1)

    access_class: AccessClass
    semantic_equivalence: SemanticEquivalence
    quality_flags: list[QualityFlag] = Field(default_factory=list)

    adapter_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    identity_version: str | None = None
    normalization_version: str | None = None
    methodology_version: str | None = None

    @model_validator(mode="after")
    def _normalize_timestamps_utc(self) -> CanonicalObservationBase:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _unresolved_identity_requires_flag(self) -> CanonicalObservationBase:
        if (
            self.instrument_id_canonical is None
            and QualityFlag.INSTRUMENT_ID_UNRESOLVED not in self.quality_flags
        ):
            raise ValueError(
                "instrument_id_canonical is unresolved; quality_flags must include "
                "INSTRUMENT_ID_UNRESOLVED (B1-T03)"
            )
        return self


class MissingObservation(BaseModel):
    """Structured missingness object (Bloc 1 §11 / B1-T51).

    Missing is information.  A missing observation is never a numeric zero and
    never silently carries forward prior values.  `reason` is mandatory.
    """

    model_config = ConfigDict(extra="forbid")

    sensor_family: SensorFamily
    provider: str = Field(min_length=1)
    venue: str | None = None
    instrument_native: str | None = None
    reason: MissingReason
    affected_start: datetime | None = None
    affected_end: datetime | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    source_interval: str | None = None
    providers_attempted: list[str] = Field(default_factory=list)
    detail: str | None = None
    quality_flags: list[QualityFlag] = Field(default_factory=list)

    @model_validator(mode="after")
    def _normalize_timestamps_utc(self) -> MissingObservation:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


def missing_reason_as_zero(reason: MissingReason) -> float:
    """Interpret a missing reason as a numeric value.

    Raises for every member of the Bloc 1 vocabulary: no missing reason may be
    coerced into a numeric zero (B1-T52).  A provider-confirmed valid zero is a
    real observation carried by a canonical record, never a missing reason.
    """
    raise ValueError(
        f"Missing reason {reason.value!r} must not be interpreted as a numeric zero; "
        "a valid zero must come from the source itself"
    )


def is_numeric_zero_semantics(reason: MissingReason) -> bool:
    """True only when the source itself reported a valid zero for the interval.

    The Bloc 1 missing-reason vocabulary contains no member that represents a
    numeric zero, so this always returns False (B1-T52).
    """
    return False


def canonical_dump(model: BaseModel) -> dict[str, Any]:
    """JSON-mode dump of the model (deterministic field content)."""
    return model.model_dump(mode="json")


def canonical_bytes(model: BaseModel) -> bytes:
    """Deterministic canonical byte serialization (B1-T62).

    Stable under the same schema version: keys sorted, compact separators,
    Decimal and datetime emitted in their JSON representations.
    """
    payload = model.model_dump(mode="json")
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_hash(model: BaseModel, algorithm: str = "sha256") -> str:
    """Content hash of the canonical byte serialization."""
    return hashlib.new(algorithm, canonical_bytes(model)).hexdigest()
