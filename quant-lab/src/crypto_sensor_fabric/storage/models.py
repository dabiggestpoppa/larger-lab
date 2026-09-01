"""SENSOR-B4-I01 — frozen storage contract models.

The immutable T0 raw-evidence lake now has a stable typed vocabulary, but NO
storage backend yet.  These models:

- preserve T0A (exact source artifact evidence) vs T0B (lossless/rebuildable
  provider-native projection) authority: T0A always wins if they disagree;
- keep acquisition identity != blob identity; logical partition != physical
  blob address; ingestion time != historical market availability time;
- keep integrity and coverage separate; missingness explicit (never numeric
  zero); LIMITED != complete;
- never imply canonical asset identity or canonical market units;
- carry NO secret-bearing fields (no API keys, tokens, cookies, credentials);
- fail closed on unknown fields (extra="forbid"), naive datetimes, negative
  counts, inverted windows and malformed SHA-256 syntax (syntax only — no
  hashing, no file access, no stream reads in I01);
- serialize deterministically (see serialization helper).

Dependency direction: storage -> frozen provider/base shared contracts only.
Provider adapters MUST NOT import storage.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..contracts.base import normalize_utc_datetimes
from ..contracts.enums import SensorFamily
from ..providers.base.enums import Granularity, QualityFlagAcquisition
from ..providers.base.models import AdapterEvidenceRef, ResumeToken
from .enums import (
    BackupClass,
    CoverageState,
    DateBasis,
    DiskPressure,
    IntegrityState,
    ProjectionState,
    RevisionPolicy,
    RevisionState,
    StorageEncoding,
    StorageJobStatus,
    StorageObjectType,
    StoragePriority,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _validate_sha256_syntax(value: str, field_name: str) -> None:
    """Validate SHA-256 FORMAT only (64 lowercase hex chars).  No hashing."""
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must be 64 lowercase hex characters, got {value!r}"
        )


def _validate_nonnegative_int(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be >= 0, got {value}")


def canonical_json_bytes(model: BaseModel) -> bytes:
    """Deterministic canonical serialization (I01 §37).

    UTF-8, stable key ordering (sort_keys), enum values serialized as their
    string values, UTC ISO-8601, no memory-address repr, no wall-clock
    auto-population.  This is a SERIALIZATION helper for IDs/evidence/export
    manifests — NOT content hashing (I02 owns hashing).
    """
    payload = json.loads(model.model_dump_json())
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


class StorageModelBase(BaseModel):
    """Common fail-closed configuration for every storage contract model."""

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# T0A evidence
# ---------------------------------------------------------------------------


class EvidenceBlob(StorageModelBase):
    """Immutable T0A source bytes (one physical blob artifact).

    `blob_sha256` is the SHA-256 of the EXACT provider-source bytes BEFORE any
    optional local wrapper compression.  I01 validates the hash FORMAT only;
    hashing is implemented in I02.

    No provider/sensor/instrument lives in the physical blob identity: the same
    exact blob may support multiple acquisitions.
    """

    blob_sha256: str = Field(min_length=64, max_length=64)
    byte_length: int = 0
    stored_byte_length: int = 0
    source_media_type: str = Field(min_length=1)
    storage_encoding: StorageEncoding = StorageEncoding.NONE
    created_at: datetime
    storage_uri: str = Field(min_length=1)
    integrity_state: IntegrityState = IntegrityState.UNVERIFIED

    @model_validator(mode="after")
    def _validate_hash(self) -> EvidenceBlob:
        _validate_sha256_syntax(self.blob_sha256, "blob_sha256")
        return self

    @model_validator(mode="after")
    def _validate_counts(self) -> EvidenceBlob:
        _validate_nonnegative_int(self.byte_length, "byte_length")
        _validate_nonnegative_int(self.stored_byte_length, "stored_byte_length")
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> EvidenceBlob:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class AcquisitionRecord(StorageModelBase):
    """ONE actual retrieval/acquisition event (F4: acquisitions != blobs).

    Preserves provider/native identity, request identity, time ranges, adapter
    provenance, blob linkage, resume linkage and failure/quality state.
    Nothing is canonicalized: no BTC/contract-type/unit/notional/side.
    """

    acquisition_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    sensor_family: SensorFamily
    request_fingerprint: str = Field(min_length=1)
    adapter_version: str = Field(min_length=1)
    requested_start: datetime
    requested_end: datetime
    native_instrument: str = Field(min_length=1)
    native_granularity: Granularity | None = None
    request_started_at: datetime
    response_observed_at: datetime
    ingested_at: datetime
    http_status_or_source_status: str | None = None
    source_locator: str = Field(min_length=1)
    blob_sha256: str | None = None
    provider_checksum: str | None = None
    resume_token_before: ResumeToken | None = None
    resume_token_after: ResumeToken | None = None
    quality_flags: list[QualityFlagAcquisition] = Field(default_factory=list)
    failure_ref: str | None = None

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> AcquisitionRecord:
        # MUST run before window comparisons: naive datetimes are rejected by
        # coerce_utc, so an offset-naive field can never reach a comparison.
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _validate_window(self) -> AcquisitionRecord:
        if self.requested_end < self.requested_start:
            raise ValueError(
                "requested_end must be >= requested_start "
                f"({self.requested_start.isoformat()} > {self.requested_end.isoformat()})"
            )
        return self

    @model_validator(mode="after")
    def _validate_hash_if_present(self) -> AcquisitionRecord:
        if self.blob_sha256 is not None:
            _validate_sha256_syntax(self.blob_sha256, "blob_sha256")
        return self


# ---------------------------------------------------------------------------
# T0B projection + lineage
# ---------------------------------------------------------------------------


class RawProjectionArtifact(StorageModelBase):
    """Optional T0B lossless/rebuildable provider-native projection (F6).

    T0B is subordinate to T0A and rebuildable from it.  No canonical
    asset/unit field may live here.
    """

    projection_id: str = Field(min_length=1)
    source_blob_sha256: list[str] = Field(default_factory=list)
    projection_schema_id: str = Field(min_length=1)
    projection_schema_version: int = 1
    parser_version: str = Field(min_length=1)
    row_count: int = 0
    min_provider_time: datetime | None = None
    max_provider_time: datetime | None = None
    partition_key: str = Field(min_length=1)
    projection_uri: str = Field(min_length=1)
    projection_sha256: str = Field(min_length=64, max_length=64)
    quality_flags: list[QualityFlagAcquisition] = Field(default_factory=list)
    state: ProjectionState = ProjectionState.VALID

    @model_validator(mode="after")
    def _validate_hash(self) -> RawProjectionArtifact:
        _validate_sha256_syntax(self.projection_sha256, "projection_sha256")
        for ref in self.source_blob_sha256:
            _validate_sha256_syntax(ref, "source_blob_sha256 member")
        return self

    @model_validator(mode="after")
    def _validate_counts(self) -> RawProjectionArtifact:
        _validate_nonnegative_int(self.row_count, "row_count")
        _validate_nonnegative_int(self.projection_schema_version, "projection_schema_version")
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> RawProjectionArtifact:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class ProjectionLineage(StorageModelBase):
    """File-level lineage record for a T0B projection (multiple allowed)."""

    lineage_manifest_id: str = Field(min_length=1)
    projection_id: str = Field(min_length=1)
    source_blob_sha256: str = Field(min_length=64, max_length=64)
    source_acquisition_id: str = Field(min_length=1)
    source_row_start: int | None = None
    source_row_end: int | None = None
    source_order: int = 0

    @model_validator(mode="after")
    def _validate_hash(self) -> ProjectionLineage:
        _validate_sha256_syntax(self.source_blob_sha256, "source_blob_sha256")
        return self

    @model_validator(mode="after")
    def _validate_counts(self) -> ProjectionLineage:
        if self.source_row_start is not None:
            _validate_nonnegative_int(self.source_row_start, "source_row_start")
        if self.source_row_end is not None:
            _validate_nonnegative_int(self.source_row_end, "source_row_end")
        _validate_nonnegative_int(self.source_order, "source_order")
        return self

    @model_validator(mode="after")
    def _validate_row_bounds(self) -> ProjectionLineage:
        if (
            self.source_row_start is not None
            and self.source_row_end is not None
            and self.source_row_end < self.source_row_start
        ):
            raise ValueError("source_row_end must be >= source_row_start")
        return self


# ---------------------------------------------------------------------------
# Logical manifests
# ---------------------------------------------------------------------------


class PartitionManifest(StorageModelBase):
    """Typed LOGICAL manifest/index state (F5: != physical blob location)."""

    partition_manifest_id: str = Field(min_length=1)
    partition_key: str = Field(min_length=1)
    manifest_version: int = 1
    provider: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    sensor_family: SensorFamily
    native_instrument: str = Field(min_length=1)
    source_granularity: Granularity | None = None
    date_basis: DateBasis = DateBasis.EVENT_TIME
    logical_date_start: datetime
    logical_date_end: datetime
    blob_refs: list[str] = Field(default_factory=list)
    projection_refs: list[str] = Field(default_factory=list)
    coverage_state: CoverageState = CoverageState.NOT_ATTEMPTED
    integrity_state: IntegrityState = IntegrityState.UNVERIFIED
    row_count: int | None = None
    min_time: datetime | None = None
    max_time: datetime | None = None
    gap_count: int | None = None
    revision_count: int = 0
    created_at: datetime
    supersedes_manifest_id: str | None = None

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> PartitionManifest:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _validate_window(self) -> PartitionManifest:
        if self.logical_date_end < self.logical_date_start:
            raise ValueError(
                "logical_date_end must be >= logical_date_start "
                f"({self.logical_date_start.isoformat()} > "
                f"{self.logical_date_end.isoformat()})"
            )
        return self

    @model_validator(mode="after")
    def _validate_counts(self) -> PartitionManifest:
        if self.manifest_version < 1:
            raise ValueError(f"manifest_version must be >= 1, got {self.manifest_version}")
        if self.row_count is not None:
            _validate_nonnegative_int(self.row_count, "row_count")
        if self.gap_count is not None:
            _validate_nonnegative_int(self.gap_count, "gap_count")
        _validate_nonnegative_int(self.revision_count, "revision_count")
        return self


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


class StorageJobState(StorageModelBase):
    """Durable job state vocabulary (I01 = vocabulary only; transitions in I07)."""

    job_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    request_fingerprint: str = Field(min_length=1)
    resume_token: ResumeToken | None = None
    last_committed_acquisition_id: str | None = None
    last_committed_blob_sha256: str | None = None
    last_manifest_id: str | None = None
    status: StorageJobStatus = StorageJobStatus.PLANNED
    updated_at: datetime

    @model_validator(mode="after")
    def _validate_hash_if_present(self) -> StorageJobState:
        if self.last_committed_blob_sha256 is not None:
            _validate_sha256_syntax(self.last_committed_blob_sha256, "last_committed_blob_sha256")
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> StorageJobState:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class StorageJobTransition(StorageModelBase):
    """Append-only job transition record (I01 = vocabulary; graph in I07)."""

    transition_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    from_status: StorageJobStatus
    to_status: StorageJobStatus
    transitioned_at: datetime
    reason: str | None = None
    evidence_ref: AdapterEvidenceRef | None = None

    @model_validator(mode="after")
    def _noop_transition(self) -> StorageJobTransition:
        if self.from_status is self.to_status:
            raise ValueError(
                f"noop transition {self.from_status} -> {self.to_status} is not recorded"
            )
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> StorageJobTransition:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Revision / integrity / quota / backup
# ---------------------------------------------------------------------------


class SourceRevision(StorageModelBase):
    """Frozen source-revision evidence (different bytes = distinct revisions)."""

    source_revision_key: str = Field(min_length=1)
    revision_number: int = 1
    blob_sha256: str = Field(min_length=64, max_length=64)
    first_seen_at: datetime
    last_seen_at: datetime
    revision_reason: str | None = None
    revision_state: RevisionState = RevisionState.STABLE

    @model_validator(mode="after")
    def _validate_hash(self) -> SourceRevision:
        _validate_sha256_syntax(self.blob_sha256, "blob_sha256")
        return self

    @model_validator(mode="after")
    def _validate_counts(self) -> SourceRevision:
        if self.revision_number < 1:
            raise ValueError(
                f"revision_number must be >= 1, got {self.revision_number}"
            )
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> SourceRevision:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _validate_seen_order(self) -> SourceRevision:
        if self.last_seen_at < self.first_seen_at:
            raise ValueError("last_seen_at must be >= first_seen_at")
        return self


class IntegrityCheck(StorageModelBase):
    """ONE integrity verification event.  No repair behavior yet."""

    check_id: str = Field(min_length=1)
    object_type: StorageObjectType
    object_id: str = Field(min_length=1)
    integrity_state: IntegrityState = IntegrityState.UNVERIFIED
    checked_at: datetime
    expected_hash: str | None = None
    observed_hash: str | None = None
    provider_checksum_algorithm: str | None = None
    provider_checksum_value: str | None = None
    detail: str | None = None

    @model_validator(mode="after")
    def _validate_hashes(self) -> IntegrityCheck:
        for field in ("expected_hash", "observed_hash"):
            value = getattr(self, field)
            if value is not None:
                _validate_sha256_syntax(value, field)
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> IntegrityCheck:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class StorageQuotaState(StorageModelBase):
    """Typed storage-pressure snapshot (I01 = model; enforcement in I09)."""

    pressure_state: DiskPressure = DiskPressure.NORMAL
    priority_class: StoragePriority | None = None
    used_bytes: int = 0
    capacity_bytes: int = 0
    free_bytes: int = 0
    utilization_ratio: float = 0.0
    absolute_free_floor_bytes: int | None = None
    observed_at: datetime

    @model_validator(mode="after")
    def _validate_bytes(self) -> StorageQuotaState:
        _validate_nonnegative_int(self.used_bytes, "used_bytes")
        _validate_nonnegative_int(self.capacity_bytes, "capacity_bytes")
        _validate_nonnegative_int(self.free_bytes, "free_bytes")
        if self.absolute_free_floor_bytes is not None:
            _validate_nonnegative_int(self.absolute_free_floor_bytes, "absolute_free_floor_bytes")
        if not (0.0 <= self.utilization_ratio <= 1.0):
            raise ValueError(
                f"utilization_ratio must be in [0.0, 1.0], got {self.utilization_ratio}"
            )
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> StorageQuotaState:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


class BackupState(StorageModelBase):
    """Current backup evidence state (F18).  No fake "backed up" boolean."""

    state: BackupClass = BackupClass.UNBACKED
    observed_at: datetime
    verified_object_count: int = 0
    verified_bytes: int = 0
    manifest_ref: str | None = None
    destination_ref: str | None = None
    verification_ref: str | None = None

    @model_validator(mode="after")
    def _validate_counts(self) -> BackupState:
        _validate_nonnegative_int(self.verified_object_count, "verified_object_count")
        _validate_nonnegative_int(self.verified_bytes, "verified_bytes")
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> BackupState:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Query / result / Bloc 5 handoff
# ---------------------------------------------------------------------------


class RawEvidenceQuery(StorageModelBase):
    """Provider-independent raw-evidence query (F19).  Fail-safe by default."""

    providers: list[str] = Field(default_factory=list)
    venues: list[str] = Field(default_factory=list)
    sensor_families: list[SensorFamily] = Field(default_factory=list)
    native_instruments: list[str] = Field(default_factory=list)
    source_granularities: list[Granularity] = Field(default_factory=list)
    logical_start: datetime | None = None
    logical_end: datetime | None = None
    acquired_before: datetime | None = None
    observed_before: datetime | None = None
    integrity_minimum: IntegrityState = IntegrityState.UNVERIFIED
    coverage_states: list[CoverageState] = Field(default_factory=list)
    revision_policy: RevisionPolicy = RevisionPolicy.ERROR_ON_AMBIGUITY
    include_t0a: bool = True
    include_t0b: bool = False
    projection_schema_ids: list[str] = Field(default_factory=list)
    limit: int | None = None

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> RawEvidenceQuery:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _validate_window(self) -> RawEvidenceQuery:
        if (
            self.logical_start is not None
            and self.logical_end is not None
            and self.logical_end < self.logical_start
        ):
            raise ValueError("logical_end must be >= logical_start")
        return self

    @model_validator(mode="after")
    def _validate_limit(self) -> RawEvidenceQuery:
        if self.limit is not None:
            _validate_nonnegative_int(self.limit, "limit")
        return self


class RawEvidenceResult(StorageModelBase):
    """One provider/sensor evidence group (source ambiguity stays visible)."""

    provider: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    sensor_family: SensorFamily
    native_instrument: str = Field(min_length=1)
    source_granularity: Granularity | None = None
    logical_time_start: datetime
    logical_time_end: datetime
    coverage_state: CoverageState = CoverageState.NOT_ATTEMPTED
    integrity_state: IntegrityState = IntegrityState.UNVERIFIED
    acquisition_ids: list[str] = Field(default_factory=list)
    blob_refs: list[str] = Field(default_factory=list)
    projection_refs: list[str] = Field(default_factory=list)
    revision_state: RevisionState = RevisionState.UNKNOWN_REVISION
    quality_flags: list[QualityFlagAcquisition] = Field(default_factory=list)
    lineage_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> RawEvidenceResult:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _validate_window(self) -> RawEvidenceResult:
        if self.logical_time_end < self.logical_time_start:
            raise ValueError("logical_time_end must be >= logical_time_start")
        return self


class RawNormalizationBatch(StorageModelBase):
    """Future Bloc 5 handoff object (F19/F21).  NO normalization here.

    No canonical_asset_id / canonical_notional / effective_at / normalized_*
    fields: those belong to Bloc 5.
    """

    batch_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    sensor_family: SensorFamily
    native_instrument: str = Field(min_length=1)
    projection_schema_id: str = Field(min_length=1)
    projection_schema_version: int = 1
    parser_version: str = Field(min_length=1)
    raw_rows_or_reader: str = Field(min_length=1)  # descriptor/reference only
    source_blob_refs: list[str] = Field(default_factory=list)
    acquisition_refs: list[str] = Field(default_factory=list)
    logical_time_range_start: datetime
    logical_time_range_end: datetime
    integrity_state: IntegrityState = IntegrityState.UNVERIFIED
    coverage_state: CoverageState = CoverageState.NOT_ATTEMPTED
    revision_state: RevisionState = RevisionState.UNKNOWN_REVISION
    quality_flags: list[QualityFlagAcquisition] = Field(default_factory=list)
    known_gap_intervals: list[str] = Field(default_factory=list)
    source_granularity: Granularity | None = None
    history_boundary: str | None = None

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> RawNormalizationBatch:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _validate_window(self) -> RawNormalizationBatch:
        if self.logical_time_range_end < self.logical_time_range_start:
            raise ValueError("logical_time_range_end must be >= logical_time_range_start")
        return self

    @model_validator(mode="after")
    def _validate_counts(self) -> RawNormalizationBatch:
        _validate_nonnegative_int(self.projection_schema_version, "projection_schema_version")
        return self


# ---------------------------------------------------------------------------
# Recovery / export
# ---------------------------------------------------------------------------


class RecoveryAction(StorageModelBase):
    """Recovery evidence record (03 doc §17).  No silent repair."""

    recovery_run_id: str = Field(min_length=1)
    object_type: StorageObjectType
    object_id: str = Field(min_length=1)
    problem: str = Field(min_length=1)
    resolution: str = Field(min_length=1)
    before_state: str | None = None
    after_state: str | None = None
    evidence_ref: AdapterEvidenceRef | None = None


class ExportManifest(StorageModelBase):
    """Future export contract (04 doc §15).  No copy/export behavior yet."""

    export_id: str = Field(min_length=1)
    created_at: datetime
    source_data_root: str = Field(min_length=1)
    selection_query: RawEvidenceQuery
    blob_count: int = 0
    projection_count: int = 0
    total_bytes: int = 0
    manifest_sha256: str = Field(min_length=64, max_length=64)
    objects: list[str] = Field(default_factory=list)
    verification_state: IntegrityState = IntegrityState.UNVERIFIED

    @model_validator(mode="after")
    def _validate_hash(self) -> ExportManifest:
        _validate_sha256_syntax(self.manifest_sha256, "manifest_sha256")
        return self

    @model_validator(mode="after")
    def _validate_counts(self) -> ExportManifest:
        _validate_nonnegative_int(self.blob_count, "blob_count")
        _validate_nonnegative_int(self.projection_count, "projection_count")
        _validate_nonnegative_int(self.total_bytes, "total_bytes")
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> ExportManifest:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


# Ensure the module imports cleanly and keeps the frozen public surface.
__all__ = [
    "AcquisitionRecord",
    "BackupState",
    "EvidenceBlob",
    "ExportManifest",
    "IntegrityCheck",
    "PartitionManifest",
    "ProjectionLineage",
    "RawEvidenceQuery",
    "RawEvidenceResult",
    "RawNormalizationBatch",
    "RawProjectionArtifact",
    "RecoveryAction",
    "SourceRevision",
    "StorageJobState",
    "StorageJobTransition",
    "StorageQuotaState",
    "canonical_json_bytes",
]
