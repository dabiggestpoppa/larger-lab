"""SENSOR-B4-I11R1 PostgreSQL operational metadata repository.

PostgreSQL is a reconstructible operational mirror. It never owns T0A bytes,
T0B contents, manifests, resume state, recovery authority, or quota policy.
The module uses one closed schema authority for DDL, inserts, introspection,
and evidence. psycopg is imported lazily so offline storage imports stay safe.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence
import re

from .catalog import AcquisitionRepository, BlobMetadataRepository
from .jobs import DurableJobStateRepository
from .manifests import PartitionManifestRepository
from .models import (
    AcquisitionRecord,
    EvidenceBlob,
    PartitionManifest,
    SourceRevision,
    StorageJobState,
    StorageJobTransition,
)

SCHEMA_NAME = "crypto_sensor_fabric_ops"
SCHEMA_VERSION = "1"
REPOSITORY_ROLE = "operational_metadata_non_raw"
_REFRESH_LOCK_KEY = 0x53454E534F5242
_INSTALL_LOCK_KEY = 0x53454E534F494E

TABLE_NAMES: tuple[str, ...] = (
    "provider_registry", "adapter_readiness", "storage_jobs",
    "storage_job_transitions", "blobs_current_metadata", "acquisitions",
    "partition_manifest_current", "source_revisions", "integrity_checks",
    "quota_state", "backup_state", "recovery_runs",
)
RECONSTRUCTIBLE_TABLES: tuple[str, ...] = (
    "provider_registry", "adapter_readiness", "storage_jobs",
    "storage_job_transitions", "blobs_current_metadata", "acquisitions",
    "partition_manifest_current", "source_revisions", "recovery_runs",
)
OPERATIONAL_ONLY_TABLES: tuple[str, ...] = ("integrity_checks", "quota_state", "backup_state")
TABLE_AUTHORITY: dict[str, str] = {
    "provider_registry": "CONFIG_MIRROR", "adapter_readiness": "CONFIG_MIRROR",
    "storage_jobs": "RECONSTRUCTIBLE", "storage_job_transitions": "RECONSTRUCTIBLE",
    "blobs_current_metadata": "RECONSTRUCTIBLE", "acquisitions": "RECONSTRUCTIBLE",
    "partition_manifest_current": "RECONSTRUCTIBLE", "source_revisions": "RECONSTRUCTIBLE",
    "recovery_runs": "RECONSTRUCTIBLE", "integrity_checks": "OPERATIONAL_ONLY",
    "quota_state": "OPERATIONAL_ONLY", "backup_state": "OPERATIONAL_ONLY",
}
CANONICAL_ORDER: dict[str, tuple[str, ...]] = {
    "provider_registry": ("provider_id",),
    "adapter_readiness": ("provider_id", "sensor_family"),
    "storage_jobs": ("job_id",),
    "storage_job_transitions": ("job_id", "transitioned_at", "transition_id"),
    "blobs_current_metadata": ("blob_sha256", "storage_encoding"),
    "acquisitions": ("acquisition_id",),
    "partition_manifest_current": ("partition_key",),
    "source_revisions": ("source_revision_key", "revision_number"),
    "recovery_runs": ("recovery_run_id",),
}
CANONICAL_ORDER["integrity_checks"] = ("check_id",)
CANONICAL_ORDER["quota_state"] = ("singleton",)
CANONICAL_ORDER["backup_state"] = ("singleton",)

# Column vocabulary and secret-value detection are deliberately separate.
_FORBIDDEN_COLUMN_TERMS = (
    "payload", "body", "content", "raw", "trade_row", "book_level",
    "market_row", "event_array", "bytea",
)
_SECRET_COLUMN_TERMS = ("password", "cookie", "authorization", "api_key", "apikey", "secret")
_SECRET_VALUE_RE = re.compile(
    r"(?i)(?:password|passwd|api[_-]?key|apikey|authorization|cookie|bearer|secret)\s*[:=]"
)
_TEXT_LIMIT = 4096
_MEDIUM_TEXT_LIMIT = 16384


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    sql_type: str
    nullable: bool = True


@dataclass(frozen=True)
class TableSpec:
    columns: tuple[ColumnSpec, ...]
    primary_key: tuple[str, ...] = ()
    foreign_keys: tuple[tuple[str, str, str], ...] = ()
    checks: tuple[str, ...] = ()


def _c(name: str, sql_type: str, nullable: bool = True) -> ColumnSpec:
    return ColumnSpec(name, sql_type, nullable)


# This is the sole authority for table shape, SQL types, nullability, and keys.
TABLE_SCHEMAS: dict[str, TableSpec] = {
    "schema_metadata": TableSpec(
        (_c("singleton", "boolean", False), _c("schema_version", "text", False),
         _c("repository_role", "text", False), _c("installed_at", "timestamptz", False)),
        ("singleton",), checks=('"singleton"',),
    ),
    "provider_registry": TableSpec(
        (_c("provider_id", "text", False), _c("status", "text", False),
         _c("evidence_class", "text", False), _c("access_class", "text"),
         _c("capability_count", "integer", False), _c("fallback_count", "integer", False),
         _c("notes", "text")), ("provider_id",),
        checks=('"capability_count" >= 0', '"fallback_count" >= 0'),
    ),
    "adapter_readiness": TableSpec(
        (_c("provider_id", "text", False), _c("sensor_family", "text", False),
         _c("adapter_id", "text", False), _c("adapter_version", "text", False),
         _c("promoted", "boolean", False), _c("implemented", "boolean", False),
         _c("offline_conformance_pass", "boolean", False), _c("schema_pass", "boolean", False),
         _c("network_smoke_status", "text", False), _c("evidence_ref", "text"),
         _c("pit_readiness", "text", False), _c("limitations", "text", False)),
        ("provider_id", "sensor_family"),
    ),
    "storage_jobs": TableSpec(
        (_c("job_id", "text", False), _c("provider_id", "text", False),
         _c("sensor_family", "text", False), _c("request_fingerprint", "text", False),
         _c("status", "text", False), _c("updated_at", "timestamptz", False),
         _c("last_committed_acquisition_id", "text"), _c("last_committed_blob_sha256", "text"),
         _c("last_manifest_id", "text")), ("job_id",),
    ),
    "storage_job_transitions": TableSpec(
        (_c("transition_id", "text", False), _c("job_id", "text", False),
         _c("from_status", "text", False), _c("to_status", "text", False),
         _c("transitioned_at", "timestamptz", False), _c("reason", "text"),
         _c("evidence_ref", "text")), ("transition_id",),
         (("job_id", "storage_jobs", "job_id"),),
    ),
    "blobs_current_metadata": TableSpec(
        (_c("blob_sha256", "text", False), _c("storage_encoding", "text", False),
         _c("byte_length", "bigint", False), _c("stored_byte_length", "bigint", False),
         _c("source_media_type", "text", False), _c("storage_uri", "text", False),
         _c("integrity_state", "text", False), _c("created_at", "timestamptz", False)),
        ("blob_sha256", "storage_encoding"),
        checks=('"byte_length" >= 0', '"stored_byte_length" >= 0'),
    ),
    "acquisitions": TableSpec(
        (_c("acquisition_id", "text", False), _c("provider_id", "text", False),
         _c("venue", "text", False), _c("sensor_family", "text", False),
         _c("request_fingerprint", "text", False), _c("adapter_version", "text", False),
         _c("adapter_capability_version", "text"), _c("requested_start", "timestamptz", False),
         _c("requested_end", "timestamptz", False), _c("actual_start", "timestamptz"),
         _c("actual_end", "timestamptz"), _c("native_instrument", "text", False),
         _c("native_granularity", "text"), _c("request_started_at", "timestamptz", False),
         _c("response_observed_at", "timestamptz", False), _c("ingested_at", "timestamptz", False),
         _c("http_status_or_source_status", "text"), _c("endpoint_host", "text"),
         _c("endpoint_path", "text"), _c("request_family", "text"),
         _c("source_locator", "text", False), _c("blob_sha256", "text"),
         _c("schema_state", "text"), _c("evidence_ref", "text"),
         _c("provider_checksum_algorithm", "text"), _c("provider_checksum_value", "text"),
         _c("provider_checksum_verified", "boolean"), _c("quality_flags", "text"),
         _c("failure_ref", "text")), ("acquisition_id",),
    ),
    "partition_manifest_current": TableSpec(
        (_c("partition_key", "text", False), _c("partition_manifest_id", "text", False),
         _c("manifest_version", "integer", False), _c("provider", "text", False),
         _c("venue", "text", False), _c("sensor_family", "text", False),
         _c("native_instrument", "text", False), _c("source_granularity", "text"),
         _c("date_basis", "text", False), _c("logical_date_start", "timestamptz", False),
         _c("logical_date_end", "timestamptz", False), _c("coverage_state", "text", False),
         _c("integrity_state", "text", False), _c("row_count", "bigint"),
         _c("min_time", "timestamptz"), _c("max_time", "timestamptz"),
         _c("gap_count", "bigint"), _c("revision_count", "integer", False),
         _c("created_at", "timestamptz", False), _c("supersedes_manifest_id", "text"),
         _c("pointer_updated_at", "timestamptz", False)), ("partition_key",),
        checks=('"manifest_version" >= 1', '"row_count" IS NULL OR "row_count" >= 0',
                '"gap_count" IS NULL OR "gap_count" >= 0', '"revision_count" >= 0'),
    ),
    "source_revisions": TableSpec(
        (_c("source_revision_key", "text", False), _c("revision_number", "integer", False),
         _c("blob_sha256", "text", False), _c("first_seen_at", "timestamptz", False),
         _c("last_seen_at", "timestamptz", False), _c("revision_reason", "text"),
         _c("revision_state", "text", False)), ("source_revision_key", "revision_number"),
        checks=('"revision_number" >= 1',),
    ),
    "integrity_checks": TableSpec(
        (_c("check_id", "text", False), _c("object_type", "text", False),
         _c("object_id", "text", False), _c("integrity_state", "text", False),
         _c("checked_at", "timestamptz", False), _c("expected_hash", "text"),
         _c("observed_hash", "text"), _c("provider_checksum_algorithm", "text"),
         _c("provider_checksum_value", "text"), _c("detail", "text")), ("check_id",),
    ),
    "quota_state": TableSpec(
        (_c("singleton", "boolean", False), _c("pressure_state", "text", False),
         _c("priority_class", "text"), _c("used_bytes", "bigint", False),
         _c("capacity_bytes", "bigint", False), _c("free_bytes", "bigint", False),
         _c("utilization_ratio", "double precision", False),
         _c("absolute_free_floor_bytes", "bigint"), _c("observed_at", "timestamptz", False)),
        ("singleton",), checks=('"singleton"', '"used_bytes" >= 0', '"capacity_bytes" >= 0',
                                  '"free_bytes" >= 0', '"utilization_ratio" BETWEEN 0 AND 1'),
    ),
    "backup_state": TableSpec(
        (_c("singleton", "boolean", False), _c("state", "text", False),
         _c("observed_at", "timestamptz", False), _c("verified_object_count", "bigint", False),
         _c("verified_bytes", "bigint", False), _c("manifest_ref", "text"),
         _c("destination_ref", "text"), _c("verification_ref", "text")), ("singleton",),
        checks=('"singleton"', '"verified_object_count" >= 0', '"verified_bytes" >= 0'),
    ),
    "recovery_runs": TableSpec(
        (_c("recovery_run_id", "text", False), _c("action_count", "integer", False),
         _c("object_count", "integer", False), _c("problem_count", "integer", False),
         _c("unresolved_count", "integer", False), _c("first_registered_at", "timestamptz"),
         _c("last_registered_at", "timestamptz")), ("recovery_run_id",),
        checks=('"action_count" >= 0', '"object_count" >= 0', '"problem_count" >= 0',
                '"unresolved_count" >= 0'),
    ),
}
ALL_TABLE_NAMES: tuple[str, ...] = ("schema_metadata",) + TABLE_NAMES
_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    table: tuple(column.name for column in spec.columns) for table, spec in TABLE_SCHEMAS.items()
}


class PostgresMetadataError(RuntimeError):
    """Base error with no DSN or secret leakage."""


class PostgresSchemaError(PostgresMetadataError):
    """The installed schema is unknown, future, or structurally invalid."""


class PostgresImportError(PostgresMetadataError):
    """A source snapshot violates the metadata-only import boundary."""


class PostgresConflict(PostgresMetadataError):
    """An imported identity conflicts with an existing durable mirror row."""


@dataclass(frozen=True)
class PostgresMetadataConfig:
    dsn: str
    schema: str = SCHEMA_NAME
    application_name: str = "crypto_sensor_fabric_i11"

    def __post_init__(self) -> None:
        if not isinstance(self.dsn, str) or not self.dsn.strip():
            raise ValueError("PostgreSQL DSN must be a nonempty explicit string")
        if self.schema != SCHEMA_NAME:
            raise ValueError(f"PostgreSQL schema must be fixed to {SCHEMA_NAME!r}")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", self.application_name):
            raise ValueError("application_name must contain only safe connection-label characters")


@dataclass(frozen=True)
class MetadataInventory:
    """Caller-certified complete ID inventory for a bounded reconstruction."""
    blob_sha256s: tuple[str, ...]
    acquisition_ids: tuple[str, ...]
    partition_keys: tuple[str, ...]
    source_revision_keys: tuple[str, ...]
    recovery_run_ids: tuple[str, ...]
    complete: bool

    def __post_init__(self) -> None:
        if not self.complete:
            raise ValueError("a reconstruction inventory must be explicitly complete")


@dataclass(frozen=True)
class MetadataSnapshot:
    rows: Mapping[str, Sequence[Mapping[str, Any]]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = set(self.rows) - set(TABLE_NAMES)
        if unknown:
            raise PostgresImportError(f"unknown metadata tables: {sorted(unknown)}")
        for table, records in self.rows.items():
            for record in records:
                validate_row(table, record)


@dataclass(frozen=True)
class MetadataSources:
    provider_registry: Any | None = None
    readiness_records: Sequence[Any] = ()
    blob_metadata_repository: BlobMetadataRepository | None = None
    blob_sha256s: Sequence[str] = ()
    acquisition_repository: AcquisitionRepository | None = None
    acquisition_ids: Sequence[str] = ()
    manifest_repository: PartitionManifestRepository | None = None
    partition_keys: Sequence[str] = ()
    job_repository: DurableJobStateRepository | None = None
    revision_registry: Any | None = None
    source_revision_keys: Sequence[str] = ()
    recovery_journal: Any | None = None
    recovery_run_ids: Sequence[str] = ()
    inventory: MetadataInventory | None = None


def redact_dsn(dsn: str) -> str:
    value = str(dsn)
    value = re.sub(r"(://[^:/@]+:)[^@]*@", r"\1<redacted>@", value)
    value = re.sub(r"(?i)(password|passwd|secret|token)=([^&;\s]+)", r"\1=<redacted>", value)
    return value


def _value(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    return value


def _text(value: Any, field_name: str, *, limit: int = _TEXT_LIMIT) -> str | None:
    if value is None:
        return None
    value = _value(value)
    if not isinstance(value, str):
        raise PostgresImportError(f"{field_name} must be text metadata")
    if len(value) > limit:
        raise PostgresImportError(f"{field_name} exceeds bounded metadata limit")
    if _SECRET_VALUE_RE.search(value):
        raise PostgresImportError(f"secret-shaped value refused in {field_name}")
    return value


def _bool(value: Any, field_name: str) -> bool | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"yes", "true", "1"}:
            return True
        if normalized in {"no", "false", "0"}:
            return False
    if not isinstance(value, bool):
        raise PostgresImportError(f"{field_name} must be boolean metadata")
    return value


def _int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PostgresImportError(f"{field_name} must be a nonnegative integer")
    return value


def _all_column_names() -> set[str]:
    return {column.name for spec in TABLE_SCHEMAS.values() for column in spec.columns}


def _sql_identifier(name: str) -> str:
    if name not in _all_column_names():
        raise PostgresSchemaError(f"unknown fixed SQL identifier {name!r}")
    return '"' + name + '"'


def validate_row(table: str, row: Mapping[str, Any]) -> dict[str, Any]:
    if table not in TABLE_SCHEMAS or table == "schema_metadata":
        raise PostgresImportError(f"unknown metadata table {table!r}")
    if not isinstance(row, Mapping):
        raise PostgresImportError(f"{table} rows must be mappings")
    expected = set(_TABLE_COLUMNS[table])
    unknown = set(row) - expected
    missing = expected - set(row)
    if unknown or missing:
        raise PostgresImportError(f"{table} columns mismatch: unknown={sorted(unknown)}, missing={sorted(missing)}")
    for name in expected:
        lowered = name.casefold()
        if any(term in lowered for term in _FORBIDDEN_COLUMN_TERMS):
            raise PostgresImportError(f"forbidden raw-storage column {table}.{name}")
        if any(term in lowered for term in _SECRET_COLUMN_TERMS):
            raise PostgresImportError(f"forbidden secret-bearing column {table}.{name}")
    out: dict[str, Any] = {}
    for name, value in row.items():
        if isinstance(value, (bytes, bytearray, memoryview, dict)):
            raise PostgresImportError(f"raw or structured content refused in {table}.{name}")
        if name in {"quality_flags", "evidence_ref"}:
            if isinstance(value, (list, tuple, set)):
                value = ",".join(_text(item, name, limit=512) or "" for item in sorted(value, key=str))
            out[name] = _text(value, f"{table}.{name}", limit=_MEDIUM_TEXT_LIMIT)
        elif name.endswith("_at") or name in {
            "requested_start", "requested_end", "actual_start", "actual_end", "min_time",
            "max_time", "logical_date_start", "logical_date_end", "checked_at",
            "observed_at", "first_seen_at", "last_seen_at", "transitioned_at", "updated_at",
            "request_started_at", "response_observed_at", "ingested_at", "created_at",
            "pointer_updated_at", "first_registered_at", "last_registered_at",
        }:
            if value is not None and not isinstance(value, datetime):
                raise PostgresImportError(f"{table}.{name} must be an aware datetime")
            if value is not None and value.tzinfo is None:
                raise PostgresImportError(f"{table}.{name} must be UTC-aware")
            out[name] = value.astimezone(UTC) if value is not None else None
        elif name in {"promoted", "implemented", "offline_conformance_pass", "schema_pass", "provider_checksum_verified", "singleton"}:
            out[name] = _bool(value, f"{table}.{name}")
        elif name in {
            "capability_count", "fallback_count", "byte_length", "stored_byte_length", "manifest_version",
            "row_count", "gap_count", "revision_count", "revision_number", "used_bytes", "capacity_bytes",
            "free_bytes", "absolute_free_floor_bytes", "verified_object_count", "verified_bytes",
            "action_count", "object_count", "problem_count", "unresolved_count",
        }:
            out[name] = _int(value, f"{table}.{name}")
        elif name == "utilization_ratio":
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1):
                raise PostgresImportError(f"{table}.{name} must be between 0 and 1")
            out[name] = float(value) if value is not None else None
        else:
            out[name] = _text(value, f"{table}.{name}")
    return out


def _row(table: str, **values: Any) -> dict[str, Any]:
    return validate_row(table, {column: values.get(column) for column in _TABLE_COLUMNS[table]})


def _model_row(table: str, model: Any) -> dict[str, Any]:
    data = model.model_dump(mode="python") if hasattr(model, "model_dump") else dict(model)
    return _row(table, **{column: data.get(column) for column in _TABLE_COLUMNS[table]})


def _safe_provider_rows(registry: Any) -> list[dict[str, Any]]:
    providers = getattr(registry, "providers", None)
    if providers is None and isinstance(registry, Mapping):
        providers = registry.get("providers", {})
    rows = []
    for provider_id, entry in sorted((providers or {}).items()):
        dumped = entry.model_dump(mode="python") if hasattr(entry, "model_dump") else dict(entry)
        access = dumped.get("access", {})
        access_class = access.get("mode") if isinstance(access, Mapping) else getattr(access, "mode", None)
        notes = dumped.get("notes")
        if isinstance(notes, str) and _SECRET_VALUE_RE.search(notes):
            notes = None
        rows.append(_row("provider_registry", provider_id=provider_id, status=dumped.get("status"),
                         evidence_class=dumped.get("evidence_class"), access_class=access_class,
                         capability_count=len(dumped.get("capabilities", {})), fallback_count=len(dumped.get("fallback_candidates", {})), notes=notes))
    return rows


def _safe_readiness_rows(records: Sequence[Any]) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        data = dict(record) if isinstance(record, Mapping) else dict(record.__dict__)
        refs = data.get("evidence_refs", data.get("evidence_ref", []))
        if isinstance(refs, (list, tuple, set)):
            refs = ",".join(sorted(str(ref) for ref in refs))
        limitations = data.get("limitations")
        if isinstance(limitations, str) and _SECRET_VALUE_RE.search(limitations):
            limitations = ""
        rows.append(_row("adapter_readiness", provider_id=data.get("provider_id"), sensor_family=data.get("sensor_family"),
                         adapter_id=data.get("adapter_id"), adapter_version=data.get("adapter_version"),
                         promoted=data.get("promoted"), implemented=data.get("implemented"),
                         offline_conformance_pass=data.get("offline_conformance_pass"), schema_pass=data.get("schema_pass"),
                         network_smoke_status=data.get("network_smoke_status"), evidence_ref=refs,
                         pit_readiness=data.get("pit_readiness"), limitations=limitations))
    return rows


def _blob_row(blob: EvidenceBlob) -> dict[str, Any]:
    return _model_row("blobs_current_metadata", blob)


def _acquisition_row(record: AcquisitionRecord) -> dict[str, Any]:
    data = record.model_dump(mode="python")
    # Deliberately omit resume tokens: I11 is not I07 resume authority.
    for key in ("evidence_ref",):
        value = data.get(key)
        if value is not None and not isinstance(value, str):
            data[key] = ",".join(sorted(str(part) for part in value)) if isinstance(value, (list, tuple, set, dict)) else str(value)
    data["quality_flags"] = sorted(str(flag) for flag in (data.get("quality_flags") or []))
    return _model_row("acquisitions", data)


def _manifest_row(manifest: PartitionManifest, pointer_updated_at: datetime | None = None) -> dict[str, Any]:
    data = manifest.model_dump(mode="python")
    data["pointer_updated_at"] = pointer_updated_at or data["created_at"]
    return _model_row("partition_manifest_current", data)


def _job_row(job: StorageJobState) -> dict[str, Any]:
    return _model_row("storage_jobs", job)


def _transition_row(transition: StorageJobTransition) -> dict[str, Any]:
    data = transition.model_dump(mode="python")
    if data.get("evidence_ref") is not None and not isinstance(data["evidence_ref"], str):
        data["evidence_ref"] = str(data["evidence_ref"])
    return _model_row("storage_job_transitions", data)


def _revision_row(revision: SourceRevision) -> dict[str, Any]:
    return _model_row("source_revisions", revision)


def _inventory_values(sources: MetadataSources, name: str, legacy: Sequence[str]) -> Sequence[str]:
    if sources.inventory is not None:
        return tuple(getattr(sources.inventory, name))
    return tuple(legacy)


def reconstruct_snapshot(*, data_root: str | Path | None = None, provider_registry_path: str | Path | None = None,
                         readiness_path: str | Path | None = None, sources: MetadataSources | None = None) -> MetadataSnapshot:
    if data_root is not None and not Path(data_root).exists():
        raise PostgresImportError(f"data_root does not exist: {data_root}")
    if sources is None:
        raise PostgresImportError("public MetadataSources are required for reconstruction")
    rows: dict[str, list[dict[str, Any]]] = {name: [] for name in TABLE_NAMES}
    if sources.provider_registry is not None:
        rows["provider_registry"] = _safe_provider_rows(sources.provider_registry)
    elif provider_registry_path is not None:
        from ..registry.provider_registry import load_provider_registry
        rows["provider_registry"] = _safe_provider_rows(load_provider_registry(Path(provider_registry_path)))
    if sources.readiness_records:
        rows["adapter_readiness"] = _safe_readiness_rows(sources.readiness_records)
    elif readiness_path is not None:
        from ..providers.readiness import load_human_readiness_matrix
        matrix = load_human_readiness_matrix(Path(readiness_path))
        rows["adapter_readiness"] = _safe_readiness_rows([
            {**values, "provider_id": key[0], "sensor_family": key[1]} for key, values in matrix.items()
        ])
    for blob_hash in _inventory_values(sources, "blob_sha256s", sources.blob_sha256s):
        if sources.blob_metadata_repository is None:
            raise PostgresImportError("blob inventory requires BlobMetadataRepository")
        rows["blobs_current_metadata"].extend(_blob_row(blob) for blob in sources.blob_metadata_repository.get_blob_metadata(blob_hash))
    for acquisition_id in _inventory_values(sources, "acquisition_ids", sources.acquisition_ids):
        if sources.acquisition_repository is None:
            raise PostgresImportError("acquisition inventory requires AcquisitionRepository")
        rows["acquisitions"].append(_acquisition_row(sources.acquisition_repository.get_acquisition(acquisition_id)))
    for partition_key in _inventory_values(sources, "partition_keys", sources.partition_keys):
        if sources.manifest_repository is None:
            raise PostgresImportError("partition inventory requires PartitionManifestRepository")
        manifest = sources.manifest_repository.get_current_manifest(partition_key)
        pointer = sources.manifest_repository.read_current_pointer(partition_key)
        rows["partition_manifest_current"].append(_manifest_row(manifest, pointer.updated_at if pointer else None))
    if sources.job_repository is not None:
        for job_id in sorted(sources.job_repository.list_job_ids()):
            rows["storage_jobs"].append(_job_row(sources.job_repository.get_job(job_id)))
            rows["storage_job_transitions"].extend(_transition_row(t) for t in sources.job_repository.list_transitions(job_id))
    for source_key in _inventory_values(sources, "source_revision_keys", sources.source_revision_keys):
        if sources.revision_registry is None:
            raise PostgresImportError("revision inventory requires SourceRevisionRegistry")
        rows["source_revisions"].extend(_revision_row(rev) for rev in sources.revision_registry.list_revisions(source_key))
    for run_id in _inventory_values(sources, "recovery_run_ids", sources.recovery_run_ids):
        if sources.recovery_journal is None:
            raise PostgresImportError("recovery inventory requires RecoveryJournal")
        actions = sources.recovery_journal.list_for_run(run_id)
        timestamps = []
        for action in actions:
            value = action.get("registered_at")
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            if isinstance(value, datetime):
                timestamps.append(value.astimezone(UTC))
        rows["recovery_runs"].append(_row("recovery_runs", recovery_run_id=run_id, action_count=len(actions),
                                           object_count=len({a.get("object_id") for a in actions}),
                                           problem_count=len({a.get("problem") for a in actions}),
                                           unresolved_count=sum(1 for a in actions if a.get("action_kind") in {"UNRESOLVED", "UNKNOWN"}),
                                           first_registered_at=min(timestamps, default=None), last_registered_at=max(timestamps, default=None)))
    return MetadataSnapshot({table: sorted(values, key=lambda row: tuple(str(row.get(c)) for c in CANONICAL_ORDER[table])) for table, values in rows.items()})


class PostgresMetadataRepository:
    def __init__(self, config: PostgresMetadataConfig, *, connection_factory: Any = None, refresh_hook: Any = None) -> None:
        self.config = config
        self._connection_factory = connection_factory
        self._refresh_hook = refresh_hook

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        try:
            import psycopg  # type: ignore[import-not-found]
        except ImportError as exc:
            raise PostgresImportError("psycopg[binary]>=3.2,<4 is required for PostgreSQL I11") from exc
        connection = None
        try:
            if self._connection_factory is not None:
                connection = self._connection_factory()
            else:
                connection = psycopg.connect(self.config.dsn, autocommit=True, application_name=self.config.application_name)
            yield connection
        except PostgresMetadataError:
            raise
        except Exception as exc:
            raise PostgresMetadataError(f"PostgreSQL operation failed for {redact_dsn(self.config.dsn)} ({type(exc).__name__})") from None
        finally:
            if connection is not None:
                connection.close()

    @contextmanager
    def _transaction(self, connection: Any) -> Iterator[Any]:
        transaction_factory = getattr(connection, "transaction", None)
        if transaction_factory is not None:
            with transaction_factory():
                yield
            return
        connection.execute("BEGIN")
        try:
            yield
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    @staticmethod
    def _sql_identifier(name: str) -> str:
        return _sql_identifier(name)

    def _create_table_sql(self, table: str) -> str:
        spec = TABLE_SCHEMAS[table]
        definitions = []
        for column in spec.columns:
            nullability = "" if column.nullable else " NOT NULL"
            definitions.append(f"{_sql_identifier(column.name)} {column.sql_type.upper()}{nullability}")
        if spec.primary_key:
            definitions.append("PRIMARY KEY (" + ", ".join(_sql_identifier(c) for c in spec.primary_key) + ")")
        for fk_column, fk_table, fk_target_column in spec.foreign_keys:
            definitions.append(f"FOREIGN KEY ({_sql_identifier(fk_column)}) REFERENCES \"{SCHEMA_NAME}\".\"{fk_table}\" ({_sql_identifier(fk_target_column)})")
        for check in spec.checks:
            definitions.append(f"CHECK ({check})")
        return f'CREATE TABLE "{SCHEMA_NAME}"."{table}" (' + ", ".join(definitions) + ")"

    def _schema_snapshot(self, connection: Any) -> dict[str, Any]:
        tables = [row[0] for row in connection.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE' ORDER BY table_name", (SCHEMA_NAME,)).fetchall()]
        columns = connection.execute("SELECT table_name, column_name, data_type, is_nullable, ordinal_position FROM information_schema.columns WHERE table_schema = %s ORDER BY table_name, ordinal_position", (SCHEMA_NAME,)).fetchall()
        column_map: dict[str, list[tuple[str, str, str]]] = {}
        for table, name, data_type, nullable, _position in columns:
            column_map.setdefault(table, []).append((name, data_type, nullable))
        pk_rows = connection.execute("SELECT tc.table_name, kcu.column_name, kcu.ordinal_position FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu ON kcu.constraint_name = tc.constraint_name AND kcu.constraint_schema = tc.constraint_schema WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = %s ORDER BY tc.table_name, kcu.ordinal_position", (SCHEMA_NAME,)).fetchall()
        primary_keys: dict[str, list[str]] = {}
        for table, column, _position in pk_rows:
            primary_keys.setdefault(table, []).append(column)
        fk_rows = connection.execute("SELECT tc.table_name, kcu.column_name, ccu.table_name, ccu.column_name FROM information_schema.table_constraints tc JOIN information_schema.key_column_usage kcu ON kcu.constraint_name = tc.constraint_name AND kcu.constraint_schema = tc.constraint_schema JOIN information_schema.referential_constraints rc ON rc.constraint_name = tc.constraint_name AND rc.constraint_schema = tc.constraint_schema JOIN information_schema.key_column_usage ccu ON ccu.constraint_name = rc.unique_constraint_name AND ccu.constraint_schema = rc.unique_constraint_schema WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = %s ORDER BY tc.table_name, kcu.column_name", (SCHEMA_NAME,)).fetchall()
        foreign_keys = sorted(tuple(row) for row in fk_rows)
        metadata = connection.execute(f'SELECT schema_version, repository_role FROM "{SCHEMA_NAME}"."schema_metadata"').fetchall() if "schema_metadata" in tables else []
        return {"tables": tables, "columns": column_map, "primary_keys": primary_keys, "foreign_keys": foreign_keys, "metadata": [tuple(row) for row in metadata]}

    def validate_installed_schema(self) -> dict[str, Any]:
        with self._connection() as connection:
            return self._validate_installed_schema(connection)

    def _validate_installed_schema(self, connection: Any) -> dict[str, Any]:
        snapshot = self._schema_snapshot(connection)
        expected_tables = list(ALL_TABLE_NAMES)
        if snapshot["tables"] != sorted(expected_tables):
            raise PostgresSchemaError(f"exact table set mismatch: {snapshot['tables']}")
        for table in expected_tables:
            actual = snapshot["columns"].get(table, [])
            expected = [(c.name, "timestamp with time zone" if c.sql_type == "timestamptz" else c.sql_type, "YES" if c.nullable else "NO") for c in TABLE_SCHEMAS[table].columns]
            normalized = actual
            if normalized != expected:
                raise PostgresSchemaError(f"exact column/type/nullability mismatch in {table}")
            if tuple(snapshot["primary_keys"].get(table, [])) != TABLE_SCHEMAS[table].primary_key:
                raise PostgresSchemaError(f"primary-key mismatch in {table}")
        expected_fks = [("storage_job_transitions", "job_id", "storage_jobs", "job_id")]
        if snapshot["foreign_keys"] != expected_fks:
            raise PostgresSchemaError(f"foreign-key mismatch: {snapshot['foreign_keys']}")
        if snapshot["metadata"] != [(SCHEMA_VERSION, REPOSITORY_ROLE)]:
            raise PostgresSchemaError("schema_metadata must contain exactly one authorized row")
        return snapshot

    def install_schema(self) -> None:
        with self._connection() as connection:
            with self._transaction(connection):
                connection.execute("SELECT pg_advisory_xact_lock(%s)", (_INSTALL_LOCK_KEY,))
                exists = connection.execute("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = %s)", (SCHEMA_NAME,)).fetchone()[0]
                if exists:
                    tables = connection.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE'", (SCHEMA_NAME,)).fetchall()
                    if tables:
                        self._validate_installed_schema(connection)
                        return
                connection.execute(f'CREATE SCHEMA "{SCHEMA_NAME}"')
                for table in ALL_TABLE_NAMES:
                    connection.execute(self._create_table_sql(table))
                connection.execute(f'INSERT INTO "{SCHEMA_NAME}"."schema_metadata" (singleton, schema_version, repository_role, installed_at) VALUES (TRUE, %s, %s, CURRENT_TIMESTAMP)', (SCHEMA_VERSION, REPOSITORY_ROLE))
                self._validate_installed_schema(connection)

    def drop_schema(self) -> None:
        with self._connection() as connection:
            with self._transaction(connection):
                connection.execute(f'DROP SCHEMA IF EXISTS "{SCHEMA_NAME}" CASCADE')

    def introspect_schema(self) -> dict[str, Any]:
        with self._connection() as connection:
            snapshot = self._schema_snapshot(connection)
        all_columns = [name for values in snapshot["columns"].values() for name, _typ, _null in values]
        return {"schema": SCHEMA_NAME, "schema_version": SCHEMA_VERSION, **snapshot,
                "raw_table_absent": not any(any(term in name.casefold() for term in _FORBIDDEN_COLUMN_TERMS) for name in snapshot["tables"]),
                "generic_raw_column_absent": not any(any(term in name.casefold() for term in _FORBIDDEN_COLUMN_TERMS) for name in all_columns),
                "secret_column_absent": not any(any(term in name.casefold() for term in _SECRET_COLUMN_TERMS) for name in all_columns),
                "bytea_absent": not any(typ.casefold() == "bytea" for values in snapshot["columns"].values() for _name, typ, _null in values)}

    def _insert_row(self, connection: Any, table: str, row: Mapping[str, Any]) -> None:
        row = validate_row(table, row)
        columns = _TABLE_COLUMNS[table]
        names = ", ".join(_sql_identifier(c) for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        try:
            connection.execute(f'INSERT INTO "{SCHEMA_NAME}"."{table}" ({names}) VALUES ({placeholders})', tuple(row[c] for c in columns))
        except Exception as exc:
            raise PostgresConflict(f"metadata identity conflict in {table}") from exc

    def _validate_db_invariants(self, connection: Any) -> None:
        self._validate_installed_schema(connection)
        orphan = connection.execute(f'SELECT COUNT(*) FROM "{SCHEMA_NAME}"."storage_job_transitions" t LEFT JOIN "{SCHEMA_NAME}"."storage_jobs" j USING (job_id) WHERE j.job_id IS NULL').fetchone()[0]
        if orphan:
            raise PostgresSchemaError("storage transition foreign-key invariant failed")

    def refresh_reconstructible_metadata(self, *, data_root: str | Path | None = None, provider_registry_path: str | Path | None = None, readiness_path: str | Path | None = None, sources: MetadataSources | None = None, snapshot: MetadataSnapshot | Mapping[str, Sequence[Mapping[str, Any]]] | None = None) -> dict[str, int]:
        candidate = snapshot if isinstance(snapshot, MetadataSnapshot) else (MetadataSnapshot(snapshot) if snapshot is not None else reconstruct_snapshot(data_root=data_root, provider_registry_path=provider_registry_path, readiness_path=readiness_path, sources=sources))
        for table in RECONSTRUCTIBLE_TABLES:
            for row in candidate.rows.get(table, ()):
                validate_row(table, row)
        with self._connection() as connection:
            with self._transaction(connection):
                connection.execute("SELECT pg_advisory_xact_lock(%s)", (_REFRESH_LOCK_KEY,))
                tables = ", ".join(f'"{SCHEMA_NAME}"."{table}"' for table in RECONSTRUCTIBLE_TABLES)
                connection.execute(f"TRUNCATE TABLE {tables}")
                counts = {}
                for table in RECONSTRUCTIBLE_TABLES:
                    records = candidate.rows.get(table, ())
                    for row in records:
                        self._insert_row(connection, table, row)
                    counts[table] = len(records)
                    if self._refresh_hook is not None:
                        self._refresh_hook(table, connection)
                self._validate_db_invariants(connection)
                return counts

    def _singleton_upsert(self, table: str, row: Mapping[str, Any]) -> None:
        row = validate_row(table, row)
        columns = _TABLE_COLUMNS[table]
        names = ", ".join(_sql_identifier(c) for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        updates = ", ".join(f"{_sql_identifier(c)}=EXCLUDED.{_sql_identifier(c)}" for c in columns if c != "singleton")
        sql = f'INSERT INTO "{SCHEMA_NAME}"."{table}" ({names}) VALUES ({placeholders}) ON CONFLICT (singleton) DO UPDATE SET {updates}'
        with self._connection() as connection:
            with self._transaction(connection):
                connection.execute(sql, tuple(row[c] for c in columns))

    def record_integrity_check(self, check: Mapping[str, Any]) -> None:
        row = validate_row("integrity_checks", check)
        columns = _TABLE_COLUMNS["integrity_checks"]
        names = ", ".join(_sql_identifier(c) for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        with self._connection() as connection:
            with self._transaction(connection):
                connection.execute(f'INSERT INTO "{SCHEMA_NAME}"."integrity_checks" ({names}) VALUES ({placeholders}) ON CONFLICT (check_id) DO NOTHING', tuple(row[c] for c in columns))
                existing = connection.execute(f'SELECT {names} FROM "{SCHEMA_NAME}"."integrity_checks" WHERE "check_id" = %s', (row["check_id"],)).fetchone()
                if existing is None or tuple(existing) != tuple(row[c] for c in columns):
                    raise PostgresConflict(f"integrity check {row['check_id']!r} has divergent semantics")

    def set_quota_state(self, state: Mapping[str, Any]) -> None:
        self._singleton_upsert("quota_state", state)

    def set_backup_state(self, state: Mapping[str, Any]) -> None:
        self._singleton_upsert("backup_state", state)

    def upsert_operational_state(self, table: str, row: Mapping[str, Any]) -> None:
        if table == "integrity_checks":
            self.record_integrity_check(row)
        elif table == "quota_state":
            self.set_quota_state(row)
        elif table == "backup_state":
            self.set_backup_state(row)
        else:
            raise PostgresImportError(f"{table} is not operational-only state")

    def _canonical_select(self, table: str) -> str:
        columns = _TABLE_COLUMNS[table]
        order = CANONICAL_ORDER[table]
        if not set(order) <= set(columns):
            raise PostgresSchemaError(f"invalid canonical sort map for {table}")
        return ", ".join(_sql_identifier(c) for c in order)

    def canonical_rows(self, tables: Sequence[str] = RECONSTRUCTIBLE_TABLES) -> dict[str, list[tuple[Any, ...]]]:
        selected = tuple(tables)
        if any(table not in TABLE_SCHEMAS for table in selected):
            raise PostgresSchemaError("canonical_rows requested an unknown table")
        with self._connection() as connection:
            result = {}
            for table in selected:
                columns = _TABLE_COLUMNS[table]
                select = ", ".join(_sql_identifier(c) for c in columns)
                result[table] = [tuple(row) for row in connection.execute(f'SELECT {select} FROM "{SCHEMA_NAME}"."{table}" ORDER BY {self._canonical_select(table)}').fetchall()]
            return result


__all__ = [
    "ALL_TABLE_NAMES", "CANONICAL_ORDER", "ColumnSpec", "MetadataInventory", "MetadataSnapshot", "MetadataSources",
    "PostgresConflict", "PostgresImportError", "PostgresMetadataConfig", "PostgresMetadataError", "PostgresMetadataRepository",
    "PostgresSchemaError", "RECONSTRUCTIBLE_TABLES", "REPOSITORY_ROLE", "SCHEMA_NAME", "SCHEMA_VERSION",
    "TABLE_AUTHORITY", "TABLE_NAMES", "TABLE_SCHEMAS", "TableSpec", "redact_dsn", "reconstruct_snapshot", "validate_row",
]
