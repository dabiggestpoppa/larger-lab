"""Bloc 3 base adapter models (01 §4-§8, 03 §5-§7).

The adapter layer is an ACQUISITION BOUNDARY.  Every model below preserves
provider identity, native instrument identity, request determinism and raw
evidence; none of them perform canonical identity/unit resolution (that is
Bloc 4/5 work).  Models fail closed on missing semantic fields — the
`dict.get(field, 0)` pattern is forbidden here (01 §17).

Time rules (01 §5):

- all datetime fields are timezone-aware and normalized to UTC
- boundaries are explicit `[start, end)` unless the provider forces
  alternate semantics, which must be recorded on the FetchBatch
- `request_id` is stable and deterministic across reruns
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...contracts.base import normalize_utc_datetimes
from ...contracts.enums import SensorFamily
from ...probes.enums import PITReadiness, ProviderRole, RedundancyClass
from .enums import (
    AdapterAuthMode,
    DuplicateAnnotation,
    FetchPurpose,
    FreeOnlyStatus,
    Granularity,
    HistoricalMode,
    LiveMode,
    PaginationMode,
    QualityFlagAcquisition,
    Retryability,
    SchemaState,
)


class AdapterEvidenceRef(BaseModel):
    """Pointer to one immutable Bloc 2/3 evidence item (05 §3)."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    verification_head: str | None = None
    claim_version: int | None = None


class RateLimitSnapshot(BaseModel):
    """Normalized rate-limit telemetry (01 §12).  UNKNOWN is valid — never invent."""

    model_config = ConfigDict(extra="forbid")

    limit_known: bool = False
    limit_capacity: int | None = None
    limit_remaining: int | None = None
    reset_at: datetime | None = None
    provider_weight_cost: float | None = None
    retry_after_seconds: float | None = None
    provider_native_headers: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _known_requires_values(self) -> RateLimitSnapshot:
        if self.limit_known:
            if self.limit_capacity is None or self.limit_remaining is None:
                raise ValueError(
                    "limit_known=True requires limit_capacity and limit_remaining"
                )
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> RateLimitSnapshot:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class ResumeToken(BaseModel):
    """Provider-native resume state (01 §15 / 03 §5-§6).

    Serializable, deterministic, round-trip safe.  Never inferred completion
    from a short page; completion is decided by the adapter from provider
    semantics, not by token absence alone.
    """

    model_config = ConfigDict(extra="forbid")

    mode: PaginationMode
    provider_cursor: str | None = None
    page_number: int = 0
    last_timestamp: datetime | None = None
    last_native_id: str | None = None
    archive_object_key: str | None = None
    checksum: str | None = None
    provider_native_state: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> ResumeToken:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class SensorCapability(BaseModel):
    """Per-sensor capability declaration (01 §4).  Sensor-specific, never global."""

    model_config = ConfigDict(extra="forbid")

    sensor_family: SensorFamily
    supported: bool = False
    access_mode: str | None = None
    historical_mode: HistoricalMode | None = None
    live_mode: LiveMode = LiveMode.NONE
    min_granularity: Granularity | None = None
    max_granularity: Granularity | None = None
    max_rows_per_request: int | None = None
    pagination_mode: PaginationMode | None = None
    symbol_scope: list[str] = Field(default_factory=list)
    auth_requirement: AdapterAuthMode = AdapterAuthMode.UNVERIFIED
    free_access_status: FreeOnlyStatus = FreeOnlyStatus.UNVERIFIED
    expected_latency_ms: int | None = None
    archive_mode: bool = False
    request_cost_class: str | None = None
    known_geo_constraints: list[str] = Field(default_factory=list)
    known_history_start: datetime | None = None
    verified_history_start: datetime | None = None
    verified_history_end: datetime | None = None
    verified_at: datetime | None = None
    probe_evidence_ref: AdapterEvidenceRef | None = None
    #: I14 authoritative bounds (source_promotion_candidates.yaml).  A
    #: capability may NOT be upgraded beyond these during Bloc 3 (I14 §E).
    allowed_role: ProviderRole | None = None
    redundancy_class: RedundancyClass | None = None
    pit_requirement: PITReadiness | None = None
    methodology_pin: str | None = None
    known_hazards: list[str] = Field(default_factory=list)
    evidence_basis: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _verified_history_ordered(self) -> SensorCapability:
        if (
            self.verified_history_start is not None
            and self.verified_history_end is not None
            and self.verified_history_start > self.verified_history_end
        ):
            raise ValueError(
                "verified_history_start must not exceed verified_history_end"
            )
        return self

    @model_validator(mode="after")
    def _pit_requirement_bounds_observed_history(self) -> SensorCapability:
        # PIT_READY* with an UNRESOLVED/absent verified window is not allowed
        # to claim verified history it does not have (fail closed, I13R1 §6).
        if (
            self.supported
            and self.pit_requirement is not None
            and "PIT_READY" in self.pit_requirement.value
            and self.verified_history_start is None
        ):
            raise ValueError(
                "PIT_READY_* capability requires a verified_history_start bound"
            )
        return self

    @model_validator(mode="after")
    def _unsupported_cannot_declare_surface(self) -> SensorCapability:
        if not self.supported:
            if self.historical_mode is not None or self.live_mode is not LiveMode.NONE:
                raise ValueError(
                    "unsupported sensor must not declare historical/live surface"
                )
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> SensorCapability:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class ProviderCapabilities(BaseModel):
    """All capabilities of one adapter, keyed by sensor (01 §4)."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    sensors: dict[SensorFamily, SensorCapability] = Field(default_factory=dict)

    def capability_for(self, sensor: SensorFamily) -> SensorCapability:
        return self.sensors.get(
            sensor, SensorCapability(sensor_family=sensor, supported=False)
        )

    def supported_sensors(self) -> list[SensorFamily]:
        return [s for s, c in self.sensors.items() if c.supported]


class FetchRequest(BaseModel):
    """Deterministic acquisition request (01 §5)."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    native_instrument_id: str = Field(min_length=1)
    start_time: datetime
    end_time: datetime
    granularity: Granularity | None = None
    page_size_hint: int | None = None
    resume_token: ResumeToken | None = None
    request_id: str = Field(min_length=1)
    purpose: FetchPurpose = FetchPurpose.BACKFILL
    adapter_semantic_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> FetchRequest:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _valid_window(self) -> FetchRequest:
        if self.end_time < self.start_time:
            raise ValueError("end_time must be >= start_time")
        return self


class RawPayloadEnvelope(BaseModel):
    """One preserved raw payload with integrity hash (01 §7 / 05 §2)."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    request_fingerprint: str = Field(min_length=1)
    content_type: str | None = None
    encoding: str | None = None
    #: faithful textual/byte form of the raw response body
    raw_body: str | bytes
    content_hash: str = Field(min_length=1)
    schema_state: SchemaState = SchemaState.UNKNOWN_SCHEMA
    retrieval_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_ref: AdapterEvidenceRef | None = None
    adapter_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _schema_state_matches_content(self) -> RawPayloadEnvelope:
        # Fail closed: a KNOWN_SCHEMA envelope must carry evidence + adapter
        # version (provenance); an envelope never pretends to parse.
        if self.schema_state is SchemaState.KNOWN_SCHEMA and self.evidence_ref is None:
            raise ValueError(
                "KNOWN_SCHEMA payload requires an evidence_ref (provenance)"
            )
        return self


class FetchBatch(BaseModel):
    """One successful/partial acquisition unit (01 §6).

    Raw payload preservation is mandatory; parsed convenience objects are
    subordinate and may be absent.  Missingness is explicit (quality flags /
    completion status), never an ambiguous empty substitute.
    """

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    native_instrument_id: str = Field(min_length=1)
    request_fingerprint: str = Field(min_length=1)
    requested_start: datetime
    requested_end: datetime
    actual_first_timestamp: datetime | None = None
    actual_last_timestamp: datetime | None = None
    raw_payloads: list[RawPayloadEnvelope] = Field(default_factory=list)
    row_count: int = 0
    next_resume_token: ResumeToken | None = None
    is_complete: bool = False
    provider_cursor: str | None = None
    http_status: int | None = None
    transport_status: str | None = None
    retrieved_at: datetime
    rate_limit_snapshot: RateLimitSnapshot = Field(default_factory=RateLimitSnapshot)
    quality_flags: list[QualityFlagAcquisition] = Field(default_factory=list)
    duplicate_annotations: list[DuplicateAnnotation] = Field(default_factory=list)
    adapter_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _complete_requires_resume_closed(self) -> FetchBatch:
        # is_complete=True with a non-None next_resume_token is a contradiction:
        # a completed acquisition has no remaining cursor.
        if self.is_complete and self.next_resume_token is not None:
            raise ValueError(
                "is_complete=True cannot carry a next_resume_token (ambiguous completion)"
            )
        return self

    @model_validator(mode="after")
    def _empty_valid_is_explicit(self) -> FetchBatch:
        # EMPTY_VALID must be a declared quality flag, never a silent [].  An
        # empty batch without the flag is an ambiguous result (fail closed).
        if self.row_count == 0 and not self.raw_payloads:
            if QualityFlagAcquisition.EMPTY_VALID not in self.quality_flags:
                raise ValueError(
                    "empty batch requires EMPTY_VALID quality flag (never silent empty)"
                )
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> FetchBatch:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class ProviderHealthSignal(BaseModel):
    """Provider health telemetry for later orchestration (03 §11)."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    consecutive_failures: int = 0
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    failure_class: str | None = None
    rate_limited: bool = False
    access_review_required: bool = False
    schema_drift: bool = False

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> ProviderHealthSignal:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class AcquisitionFailure(BaseModel):
    """Structured, serializable acquisition failure (01 §21 / 03 §12)."""

    model_config = ConfigDict(extra="forbid")

    failure_type: str = Field(min_length=1)  # one of the typed error names
    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    request_fingerprint: str | None = None
    retryability: Retryability = Retryability.UNKNOWN
    provider_native_context_redacted: dict[str, Any] = Field(default_factory=dict)
    evidence_ref: AdapterEvidenceRef | None = None
    detail: str | None = None

    @model_validator(mode="after")
    def _normalize(self) -> AcquisitionFailure:
        return self


class InstrumentListRequest(BaseModel):
    """Instrument discovery request (01 §3)."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    purpose: FetchPurpose = FetchPurpose.PROBE
    request_id: str = Field(min_length=1)


class InstrumentListResult(BaseModel):
    """Instrument discovery result (01 §3)."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    native_instrument_ids: list[str] = Field(default_factory=list)
    retrieved_at: datetime

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> InstrumentListResult:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]
