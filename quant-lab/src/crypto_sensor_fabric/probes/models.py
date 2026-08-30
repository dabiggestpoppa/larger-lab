"""Bloc 2 probe core models.

Frozen shapes from `bloc_02/01` §7-8 and `05_PROBE_OUTPUT_TEMPLATES.md`.
These models are capability-probe infrastructure (T-1 evidence), not T1
canonical observations and not T0 ingestion records.

Invariants:

- every attempt emits an evidence record, even failures (T2-MODEL-05)
- evidence never carries secrets (redaction enforced at build time)
- unattempted is never serialized as unsupported (T2-MODEL-06)
- deterministic serialization under the same probe version (T2-MODEL-03)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..contracts.base import normalize_utc_datetimes
from ..contracts.enums import (
    MissingReason,
    SemanticEquivalence,
    SensorFamily,
)
from .enums import (
    AccessMode,
    CapabilityMissingness,
    CapabilityStatus,
    ContradictionResolutionStatus,
    ContradictionSeverity,
    EvidenceLevel,
    FreeOnlyStatus,
    Granularity,
    HistoricalBoundaryConfidence,
    PITReadiness,
    ProbeFailureClass,
    ProbeRunStatus,
    ProviderRole,
    QueryMode,
    RedundancyClass,
    ResponseStatusClass,
)


class CapabilityProbeRequest(BaseModel):
    """One deterministic provider/sensor/instrument/date/granularity attempt."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    venue_market: str = Field(min_length=1)
    instrument_native: str = Field(min_length=1)
    canonical_asset_hint: str | None = None
    requested_start: datetime
    requested_end: datetime
    requested_granularity: Granularity
    access_mode: AccessMode
    query_mode: QueryMode
    probe_run_id: str = Field(min_length=1)
    provider_hints: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_window(self) -> CapabilityProbeRequest:
        if self.requested_end < self.requested_start:
            raise ValueError("requested_end must be >= requested_start")
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> CapabilityProbeRequest:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @property
    def era_hint(self) -> str | None:
        """Era label stamped by the planner (RECENT_CONTROL / 2021 / ...)."""
        value = self.provider_hints.get("era")
        return value if isinstance(value, str) else None


class CapabilityProbeAttempt(BaseModel):
    """Immutable evidence record for one probe attempt (01 §8 / 05 §1).

    Created for every attempt — success or failure.  `error_class` set and
    `response_status_class=FAILED` is a valid, complete record.
    """

    model_config = ConfigDict(extra="forbid")

    probe_id: str = Field(min_length=1)
    probe_run_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    venue_market: str = Field(min_length=1)
    instrument_native: str = Field(min_length=1)
    canonical_asset_hint: str | None = None
    requested_start: datetime
    requested_end: datetime
    requested_granularity: Granularity
    access_mode: AccessMode
    query_mode: QueryMode
    request_method: str | None = None
    request_fingerprint: str | None = None
    response_status_class: ResponseStatusClass = ResponseStatusClass.NOT_ATTEMPTED
    http_status_or_file_status: int | str | None = None
    rows_returned: int | None = None
    first_timestamp_returned: datetime | None = None
    last_timestamp_returned: datetime | None = None
    native_timestamp_fields: list[str] = Field(default_factory=list)
    native_units_summary: dict[str, str] = Field(default_factory=dict)
    pagination_detected: bool = False
    pagination_complete: bool | None = None
    rate_limit_metadata: dict[str, Any] = Field(default_factory=dict)
    requires_auth: bool = False
    requires_payment: bool = False
    geo_block_detected: bool = False
    payload_schema_fingerprint: str | None = None
    payload_hash_sample: str | None = None
    error_class: ProbeFailureClass | None = None
    error_detail_redacted: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    probe_version: str = Field(min_length=1)
    #: Checkpoint era label (RECENT_CONTROL / 2021 / ...), stamped by the
    #: runner from the request so evidence synthesis stays checkpoint-traceable.
    era_hint: str | None = None

    @model_validator(mode="after")
    def _failed_attempt_carries_error_class(self) -> CapabilityProbeAttempt:
        if (
            self.response_status_class is ResponseStatusClass.FAILED
            and self.error_class is None
        ):
            raise ValueError(
                "failed attempts must carry an error_class (T2-MODEL-05)"
            )
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> CapabilityProbeAttempt:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class CapabilityClaim(BaseModel):
    """Versioned, normalized capability statement (05 §2 / 03 §3)."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    venue_market: str = Field(min_length=1)
    instrument_scope: list[str] = Field(default_factory=list)
    granularity_scope: list[Granularity] = Field(default_factory=list)
    access_mode: AccessMode
    capability_status: CapabilityStatus = CapabilityStatus.UNVERIFIED
    evidence_level: EvidenceLevel = EvidenceLevel.E0_CLAIM_ONLY
    earliest_claimed_history: datetime | None = None
    earliest_verified_history: datetime | None = None
    history_boundary_confidence: HistoricalBoundaryConfidence = (
        HistoricalBoundaryConfidence.UNKNOWN
    )
    latest_verified_history: datetime | None = None
    PIT_readiness: PITReadiness = PITReadiness.NOT_PIT_READY
    semantic_equivalence_class: SemanticEquivalence | None = None
    free_only_status: FreeOnlyStatus = FreeOnlyStatus.UNVERIFIED
    known_gaps: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    claim_version: int = 1
    valid_from: datetime | None = None
    supersedes_claim_id: str | None = None

    #: I13R1 — PIT semantics facts.  Fail closed: a PIT_READY_* state is
    # forbidden unless the facts that justify it are understood.  `None`
    # means UNKNOWN and never supports readiness.
    pit_effective_ts_understood: bool | None = None
    pit_observation_ts_understood: bool | None = None
    pit_publication_delay_understood: bool | None = None
    pit_forward_info_required: bool = False
    pit_forward_availability_resolved: bool | None = None
    pit_publication_affects_reconstruction: bool | None = None
    pit_blocking_reason: str | None = None

    #: I13R1 — a claim counts toward VERIFIED redundancy only when the data
    # semantics themselves were verified (not just source availability).
    data_semantics_verified: bool = False

    @model_validator(mode="after")
    def _verified_boundaries_ordered(self) -> CapabilityClaim:
        if (
            self.earliest_verified_history is not None
            and self.latest_verified_history is not None
            and self.earliest_verified_history > self.latest_verified_history
        ):
            raise ValueError(
                "earliest_verified_history must not exceed latest_verified_history"
            )
        return self

    @model_validator(mode="after")
    def _verified_requires_runtime_evidence(self) -> CapabilityClaim:
        if self.capability_status not in {
            CapabilityStatus.UNVERIFIED,
            CapabilityStatus.TRANSIENT_FAILURE,
            CapabilityStatus.ACCESS_BLOCKED,
            CapabilityStatus.GEO_BLOCKED,
            CapabilityStatus.AUTH_BLOCKED,
            CapabilityStatus.PAYMENT_BLOCKED,
            CapabilityStatus.HISTORY_BLOCKED,
            CapabilityStatus.UNSUPPORTED,
            CapabilityStatus.SEMANTICALLY_UNUSABLE,  # runtime-derived (failed sample)
        } and self.evidence_level == EvidenceLevel.E0_CLAIM_ONLY:
            raise ValueError(
                "capability_status requires runtime evidence; "
                "E0_CLAIM_ONLY cannot support a verified/limited status"
            )
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> CapabilityClaim:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class DocumentationRuntimeContradiction(BaseModel):
    """Preserved docs-vs-runtime mismatch (05 §8 / 03 §15)."""

    model_config = ConfigDict(extra="forbid")

    contradiction_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    documentation_claim: str = Field(min_length=1)
    documentation_source_ref: str | None = None
    runtime_observation: str = Field(min_length=1)
    runtime_evidence_ids: list[str] = Field(default_factory=list)
    severity: ContradictionSeverity = ContradictionSeverity.INFO
    resolution_status: ContradictionResolutionStatus = (
        ContradictionResolutionStatus.OPEN
    )
    notes: str | None = None


class FailureRecord(BaseModel):
    """One machine-readable failure (05 §7)."""

    model_config = ConfigDict(extra="forbid")

    failure_id: str = Field(min_length=1)
    probe_id: str | None = None
    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    failure_class: ProbeFailureClass = ProbeFailureClass.F_UNKNOWN
    provider_native_code: str | None = None
    provider_native_message_redacted: str | None = None
    retryable: bool = False
    hard_block: bool = False
    missingness_mapping: CapabilityMissingness | None = None
    evidence_ref: str | None = None


class ProviderSensorCoverage(BaseModel):
    """Coverage row per provider/sensor scope (05 §3)."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    venue_market: str = Field(min_length=1)
    instrument_scope: list[str] = Field(default_factory=list)
    access_mode: AccessMode
    era_status: dict[str, CapabilityStatus] = Field(default_factory=dict)
    earliest_verified_history: datetime | None = None
    latest_verified_history: datetime | None = None
    granularity_scope: list[Granularity] = Field(default_factory=list)
    PIT_readiness: PITReadiness = PITReadiness.NOT_PIT_READY
    unit_clarity: float | None = None
    pagination_quality: float | None = None
    schema_stability: float | None = None
    semantic_equivalence_class: SemanticEquivalence | None = None
    evidence_level: EvidenceLevel = EvidenceLevel.E0_CLAIM_ONLY
    provider_role: ProviderRole = ProviderRole.REFERENCE_ONLY
    capability_score: float | None = None
    promotion_eligible: bool = False
    blocking_reason: str | None = None

    #: I13R1 — PIT semantics facts mirroring the claim (fail closed).
    pit_effective_ts_understood: bool | None = None
    pit_observation_ts_understood: bool | None = None
    pit_publication_delay_understood: bool | None = None
    pit_forward_info_required: bool = False
    pit_forward_availability_resolved: bool | None = None
    pit_publication_affects_reconstruction: bool | None = None
    pit_blocking_reason: str | None = None
    data_semantics_verified: bool = False

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> ProviderSensorCoverage:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class ProviderProbeSummary(BaseModel):
    """Per-provider summary for the human report (02 §16)."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    access_free_only_status: FreeOnlyStatus = FreeOnlyStatus.UNVERIFIED
    auth_mode: str | None = None
    sensors_tested: list[SensorFamily] = Field(default_factory=list)
    instruments_tested: list[str] = Field(default_factory=list)
    historical_checkpoints_tested: list[str] = Field(default_factory=list)
    earliest_verified_history: datetime | None = None
    timestamp_semantics: str | None = None
    unit_semantics: str | None = None
    pagination_archive_behavior: str | None = None
    known_limitations: list[str] = Field(default_factory=list)
    semantic_equivalence_notes: list[str] = Field(default_factory=list)
    reproducibility_evidence: list[str] = Field(default_factory=list)
    recommended_role_summary: str | None = None


class SensorRedundancySummary(BaseModel):
    """Independence-aware redundancy per sensor (05 §5 / 03 §17)."""

    model_config = ConfigDict(extra="forbid")

    sensor_family: SensorFamily
    verified_provider_count: int = 0
    verified_venues: list[str] = Field(default_factory=list)
    redundancy_class: RedundancyClass = RedundancyClass.R0_NONE
    first_party_count: int = 0
    aggregator_count: int = 0
    community_count: int = 0
    PIT_ready_provider_count: int = 0
    gap_status: str = "UNVERIFIED"
    notes: str | None = None


class ProbeRunResult(BaseModel):
    """Outcome of one planned run (03 §22)."""

    model_config = ConfigDict(extra="forbid")

    probe_run_id: str = Field(min_length=1)
    run_status: ProbeRunStatus = ProbeRunStatus.PARTIAL
    attempts: list[CapabilityProbeAttempt] = Field(default_factory=list)
    planned_but_skipped: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    probe_version: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)


# Missing-reason mapping contract used by later blocs (03 §6).
# `missing_reason` is None when the Bloc 1 vocabulary has no faithful member;
# the probe-layer CapabilityMissingness must then be preserved and flagged
# BLOC5_SCHEMA_REFINEMENT_PENDING rather than forcing a frozen-schema change.
MISSING_REASON_MAP: dict[CapabilityMissingness, MissingReason | None] = {
    CapabilityMissingness.PRE_LISTING: None,  # no faithful Bloc 1 member
    CapabilityMissingness.UNSUPPORTED_INSTRUMENT: MissingReason.NOT_LISTED,
    CapabilityMissingness.UNKNOWN_SYMBOL: MissingReason.NOT_LISTED,
    CapabilityMissingness.OUTSIDE_PROVIDER_RETENTION: (
        MissingReason.OUTSIDE_PROVIDER_HISTORY
    ),
    CapabilityMissingness.SENSOR_NOT_SUPPORTED: MissingReason.NOT_SUPPORTED,
    CapabilityMissingness.PROVIDER_SCHEMA_BREAK: MissingReason.PARSE_FAILED,
    CapabilityMissingness.ENDPOINT_UNAVAILABLE: MissingReason.ENDPOINT_UNAVAILABLE,
    CapabilityMissingness.RATE_LIMITED: MissingReason.RATE_LIMITED,
    CapabilityMissingness.AUTH_BLOCKED: MissingReason.AUTH_BLOCKED,
    CapabilityMissingness.GEO_BLOCKED: MissingReason.GEO_BLOCKED,
    CapabilityMissingness.PAYMENT_BLOCKED: None,  # no faithful Bloc 1 member
    CapabilityMissingness.PROVIDER_GAP: MissingReason.PROVIDER_GAP,
    CapabilityMissingness.DATA_BLOCKED: MissingReason.DATA_BLOCKED,
}


def missingness_to_bloc1_reason(
    missingness: CapabilityMissingness,
) -> tuple[MissingReason | None, str | None]:
    """Map probe-layer missingness to Bloc 1 MissingReason.

    Returns (reason, note).  When reason is None the distinction has no
    faithful Bloc 1 member (e.g. PRE_LISTING, PAYMENT_BLOCKED) and the
    probe-layer value must be carried forward; the note flags
    BLOC5_SCHEMA_REFINEMENT_PENDING so the gap is visible, not silent.
    """
    reason = MISSING_REASON_MAP[missingness]
    if reason is None:
        return None, (
            f"probe missingness {missingness.value!r} has no faithful Bloc 1 "
            "MissingReason member; preserve at probe layer — "
            "BLOC5_SCHEMA_REFINEMENT_PENDING"
        )
    return reason, None
