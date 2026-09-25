"""SENSOR-B4-I11 PostgreSQL operational metadata repository.

PostgreSQL is an operational mirror only.  It never stores T0A bytes, T0B
Parquet contents, source response bodies, or a second copy of accepted durable
authority.  The module deliberately imports ``psycopg`` lazily so importing
the storage package remains offline-safe when the optional runtime is absent.
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
_REFRESH_LOCK_KEY = 0x53454E534F5242  # fixed, not caller-controlled

TABLE_NAMES: tuple[str, ...] = (
    "provider_registry",
    "adapter_readiness",
    "storage_jobs",
    "storage_job_transitions",
    "blobs_current_metadata",
    "acquisitions",
    "partition_manifest_current",
    "source_revisions",
    "integrity_checks",
    "quota_state",
    "backup_state",
    "recovery_runs",
)
RECONSTRUCTIBLE_TABLES: tuple[str, ...] = (
    "provider_registry",
    "adapter_readiness",
    "storage_jobs",
    "storage_job_transitions",
    "blobs_current_metadata",
    "acquisitions",
    "partition_manifest_current",
    "source_revisions",
    "recovery_runs",
)
OPERATIONAL_ONLY_TABLES: tuple[str, ...] = (
    "integrity_checks",
    "quota_state",
    "backup_state",
)
TABLE_AUTHORITY: dict[str, str] = {
    "provider_registry": "CONFIG_MIRROR",
    "adapter_readiness": "CONFIG_MIRROR",
    "storage_jobs": "RECONSTRUCTIBLE",
    "storage_job_transitions": "RECONSTRUCTIBLE",
    "blobs_current_metadata": "RECONSTRUCTIBLE",
    "acquisitions": "RECONSTRUCTIBLE",
    "partition_manifest_current": "RECONSTRUCTIBLE",
    "source_revisions": "RECONSTRUCTIBLE",
    "recovery_runs": "RECONSTRUCTIBLE",
    "integrity_checks": "OPERATIONAL_ONLY",
    "quota_state": "OPERATIONAL_ONLY",
    "backup_state": "OPERATIONAL_ONLY",
}

# This is intentionally a closed schema.  There is no BYTEA/JSONB escape
# hatch and no generic payload/content/body/data column.
_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "schema_metadata": (
        "singleton", "schema_version", "repository_role", "installed_at",
    ),
    "provider_registry": (
        "provider_id", "status", "evidence_class", "access_class",
        "capability_count", "fallback_count", "notes",
    ),
    "adapter_readiness": (
        "provider_id", "sensor_family", "adapter_id", "adapter_version",
        "promoted", "implemented", "offline_conformance_pass", "schema_pass",
        "network_smoke_status", "evidence_ref", "pit_readiness", "limitations",
    ),
    "storage_jobs": (
        "job_id", "provider_id", "sensor_family", "request_fingerprint",
        "status", "updated_at", "last_committed_acquisition_id",
        "last_committed_blob_sha256", "last_manifest_id",
    ),
    "storage_job_transitions": (
        "transition_id", "job_id", "from_status", "to_status",
        "transitioned_at", "reason", "evidence_ref",
    ),
    "blobs_current_metadata": (
        "blob_sha256", "storage_encoding", "byte_length", "stored_byte_length",
        "source_media_type", "storage_uri", "integrity_state", "created_at",
    ),
    "acquisitions": (
        "acquisition_id", "provider_id", "venue", "sensor_family",
        "request_fingerprint", "adapter_version", "adapter_capability_version",
        "requested_start", "requested_end", "actual_start", "actual_end",
        "native_instrument", "native_granularity", "request_started_at",
        "response_observed_at", "ingested_at", "http_status_or_source_status",
        "endpoint_host", "endpoint_path", "request_family", "source_locator",
        "blob_sha256", "schema_state", "evidence_ref",
        "provider_checksum_algorithm", "provider_checksum_value",
        "provider_checksum_verified", "resume_token_before", "resume_token_after",
        "quality_flags", "failure_ref",
    ),
    "partition_manifest_current": (
        "partition_key", "partition_manifest_id", "manifest_version", "provider",
        "venue", "sensor_family", "native_instrument", "source_granularity",
        "date_basis", "logical_date_start", "logical_date_end", "coverage_state",
        "integrity_state", "row_count", "min_time", "max_time", "gap_count",
        "revision_count", "created_at", "supersedes_manifest_id", "pointer_updated_at",
    ),
    "source_revisions": (
        "source_revision_key", "revision_number", "blob_sha256", "first_seen_at",
        "last_seen_at", "revision_reason", "revision_state",
    ),
    "integrity_checks": (
        "check_id", "object_type", "object_id", "integrity_state", "checked_at",
        "expected_hash", "observed_hash", "provider_checksum_algorithm",
        "provider_checksum_value", "detail",
    ),
    "quota_state": (
        "singleton", "pressure_state", "priority_class", "used_bytes",
        "capacity_bytes", "free_bytes", "utilization_ratio",
        "absolute_free_floor_bytes", "observed_at",
    ),
    "backup_state": (
        "singleton", "state", "observed_at", "verified_object_count",
        "verified_bytes", "manifest_ref", "destination_ref", "verification_ref",
    ),
    "recovery_runs": (
        "recovery_run_id", "action_count", "object_count", "problem_count",
        "unresolved_count", "first_registered_at", "last_registered_at",
    ),
}
_CANONICAL_EXCLUDE = frozenset({"schema_metadata", "integrity_checks", "quota_state", "backup_state"})
_FORBIDDEN_COLUMN_PARTS = (
    "payload", "body", "content", "raw", "secret", "password", "token",
    "cookie", "authorization", "apikey", "api_key", "trade", "book",
    "market_row", "event_array",
)
_TEXT_LIMIT = 4096
_MEDIUM_TEXT_LIMIT = 16384


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
        if not self.application_name or len(self.application_name) > 128:
            raise ValueError("application_name must be 1..128 characters")


@dataclass(frozen=True)
class MetadataSnapshot:
    """Validated, bounded metadata rows grouped by fixed table name."""

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
    """Accepted public readers and explicit materialized views for I11.

    IDs/keys are supplied by the caller because the historical repositories
    intentionally expose point reads rather than a catalog-wide private scan.
    Every item below is read through a public method; no DuckDB helper or
    filesystem payload reader is used.
    """

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


def redact_dsn(dsn: str) -> str:
    """Return a safe DSN rendering; passwords and token query values vanish."""
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
    lowered = value.casefold()
    if any(part in lowered for part in ("password", "api_key", "apikey", "authorization", "cookie")):
        raise PostgresImportError(f"secret-shaped value refused in {field_name}")
    return value


def _enum(value: Any, field_name: str) -> str | None:
    return _text(value, field_name, limit=256)


def _bool(value: Any, field_name: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise PostgresImportError(f"{field_name} must be boolean metadata")
    return value


def _int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PostgresImportError(f"{field_name} must be a nonnegative integer")
    return value


def validate_row(table: str, row: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one row against the closed, metadata-only column contract."""
    if table not in TABLE_NAMES:
        raise PostgresImportError(f"unknown table {table!r}")
    if not isinstance(row, Mapping):
        raise PostgresImportError(f"{table} rows must be mappings")
    expected = set(_TABLE_COLUMNS[table])
    unknown = set(row) - expected
    missing = expected - set(row)
    if unknown or missing:
        raise PostgresImportError(f"{table} columns mismatch: unknown={sorted(unknown)}, missing={sorted(missing)}")
    for name in expected:
        if any(part in name.casefold() for part in _FORBIDDEN_COLUMN_PARTS):
            raise PostgresImportError(f"forbidden metadata column {table}.{name}")
    out: dict[str, Any] = {}
    for name, value in row.items():
        if isinstance(value, (bytes, bytearray, memoryview)):
            raise PostgresImportError(f"binary/raw content refused in {table}.{name}")
        if name.endswith("_at") or name in {"requested_start", "requested_end", "actual_start", "actual_end", "min_time", "max_time", "logical_date_start", "logical_date_end", "checked_at", "observed_at", "first_seen_at", "last_seen_at", "transitioned_at", "updated_at", "request_started_at", "response_observed_at", "ingested_at", "created_at", "pointer_updated_at", "first_registered_at", "last_registered_at"}:
            if value is not None and not isinstance(value, datetime):
                raise PostgresImportError(f"{table}.{name} must be an aware datetime")
            if value is not None and value.tzinfo is None:
                raise PostgresImportError(f"{table}.{name} must be UTC-aware")
            out[name] = value.astimezone(UTC) if value is not None else None
        elif name in {"promoted", "implemented", "offline_conformance_pass", "schema_pass", "provider_checksum_verified", "singleton"}:
            out[name] = _bool(value, f"{table}.{name}")
        elif name in {"capability_count", "fallback_count", "byte_length", "stored_byte_length", "manifest_version", "row_count", "gap_count", "revision_count", "revision_number", "used_bytes", "capacity_bytes", "free_bytes", "absolute_free_floor_bytes", "verified_object_count", "verified_bytes", "action_count", "object_count", "problem_count", "unresolved_count"}:
            out[name] = _int(value, f"{table}.{name}")
        elif name == "utilization_ratio":
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1):
                raise PostgresImportError(f"{table}.{name} must be between 0 and 1")
            out[name] = float(value) if value is not None else None
        elif name in {"quality_flags", "resume_token_before", "resume_token_after", "evidence_ref"}:
            if isinstance(value, (list, tuple, set)):
                value = ",".join(_text(item, name, limit=512) or "" for item in sorted(value, key=str))
            out[name] = _text(value, f"{table}.{name}", limit=_MEDIUM_TEXT_LIMIT)
        else:
            out[name] = _text(value, f"{table}.{name}")
    return out


def _row(table: str, **values: Any) -> dict[str, Any]:
    return validate_row(table, {column: values.get(column) for column in _TABLE_COLUMNS[table]})


def _model_row(table: str, model: Any) -> dict[str, Any]:
    data = model.model_dump(mode="python") if hasattr(model, "model_dump") else dict(model)
    return _row(table, **data)


def _safe_provider_rows(registry: Any) -> list[dict[str, Any]]:
    providers = getattr(registry, "providers", None)
    if providers is None and isinstance(registry, Mapping):
        providers = registry.get("providers", {})
    rows: list[dict[str, Any]] = []
    for provider_id, entry in sorted((providers or {}).items()):
        dumped = entry.model_dump(mode="python") if hasattr(entry, "model_dump") else dict(entry)
        access = dumped.get("access", {})
        access_class = access.get("mode") if isinstance(access, Mapping) else getattr(access, "mode", None)
        notes = dumped.get("notes")
        if isinstance(notes, str) and any(part in notes.casefold() for part in ("password", "api_key", "apikey", "authorization", "cookie", "secret")):
            notes = None
        rows.append(_row("provider_registry", provider_id=provider_id, status=dumped.get("status"), evidence_class=dumped.get("evidence_class"), access_class=access_class, capability_count=len(dumped.get("capabilities", {})), fallback_count=len(dumped.get("fallback_candidates", {})), notes=notes))
    return rows


def _safe_readiness_rows(records: Sequence[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        data = record if isinstance(record, Mapping) else record.__dict__
        refs = data.get("evidence_refs", data.get("evidence_ref", []))
        if isinstance(refs, (list, tuple, set)):
            refs = ",".join(sorted(str(ref) for ref in refs))
        limitations = data.get("limitations")
        if isinstance(limitations, str) and any(part in limitations.casefold() for part in ("password", "api_key", "apikey", "authorization", "cookie", "secret")):
            limitations = ""
        rows.append(_row("adapter_readiness", provider_id=data.get("provider_id"), sensor_family=data.get("sensor_family"), adapter_id=data.get("adapter_id"), adapter_version=data.get("adapter_version"), promoted=data.get("promoted"), implemented=data.get("implemented"), offline_conformance_pass=data.get("offline_conformance_pass"), schema_pass=data.get("schema_pass"), network_smoke_status=data.get("network_smoke_status"), evidence_ref=refs, pit_readiness=data.get("pit_readiness"), limitations=limitations))
    return rows


def _blob_row(blob: EvidenceBlob) -> dict[str, Any]:
    return _model_row("blobs_current_metadata", blob)


def _acquisition_row(record: AcquisitionRecord) -> dict[str, Any]:
    data = record.model_dump(mode="python")
    for key in ("evidence_ref", "resume_token_before", "resume_token_after"):
        value = data.get(key)
        if value is not None and not isinstance(value, str):
            data[key] = ",".join(sorted(str(part) for part in value)) if isinstance(value, (list, tuple, set, dict)) else str(value)
    data["quality_flags"] = sorted(str(flag) for flag in data.get("quality_flags", []))
    return _model_row("acquisitions", data)


def _manifest_row(manifest: PartitionManifest, pointer_updated_at: datetime | None = None) -> dict[str, Any]:
    data = manifest.model_dump(mode="python")
    data["provider"] = data.pop("provider", None) or ""
    data["pointer_updated_at"] = pointer_updated_at or data["created_at"]
    return _model_row("partition_manifest_current", data)


def _job_row(job: StorageJobState) -> dict[str, Any]:
    return _model_row("storage_jobs", job)


def _transition_row(transition: StorageJobTransition) -> dict[str, Any]:
    data = transition.model_dump(mode="python")
    evidence = data.get("evidence_ref")
    if evidence is not None and not isinstance(evidence, str):
        data["evidence_ref"] = str(evidence)
    return _model_row("storage_job_transitions", data)


def _revision_row(revision: SourceRevision) -> dict[str, Any]:
    return _model_row("source_revisions", revision)


def reconstruct_snapshot(
    *,
    data_root: str | Path | None = None,
    provider_registry_path: str | Path | None = None,
    readiness_path: str | Path | None = None,
    sources: MetadataSources | None = None,
) -> MetadataSnapshot:
    """Build metadata through accepted public repository methods only.

    ``data_root`` is retained as an explicit context/location check.  Catalog
    enumeration is never performed by scanning private implementation files;
    callers provide the public IDs/keys their accepted readers expose.
    """
    if data_root is not None and not Path(data_root).exists():
        raise PostgresImportError(f"data_root does not exist: {data_root}")
    if sources is None:
        raise PostgresImportError("public MetadataSources are required for reconstruction")
    rows: dict[str, list[dict[str, Any]]] = {name: [] for name in TABLE_NAMES}
    if sources.provider_registry is not None:
        rows["provider_registry"] = _safe_provider_rows(sources.provider_registry)
    if provider_registry_path is not None and sources.provider_registry is None:
        from ..registry.provider_registry import load_provider_registry
        rows["provider_registry"] = _safe_provider_rows(load_provider_registry(Path(provider_registry_path)))
    if sources.readiness_records:
        rows["adapter_readiness"] = _safe_readiness_rows(sources.readiness_records)
    elif readiness_path is not None:
        import json
        payload = json.loads(Path(readiness_path).read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise PostgresImportError("readiness_path must contain a list of readiness records")
        rows["adapter_readiness"] = _safe_readiness_rows(payload)
    blob_repo = sources.blob_metadata_repository
    for blob_hash in sources.blob_sha256s:
        if blob_repo is None:
            raise PostgresImportError("blob_sha256s requires BlobMetadataRepository")
        for blob in blob_repo.get_blob_metadata(blob_hash):
            rows["blobs_current_metadata"].append(_blob_row(blob))
    acq_repo = sources.acquisition_repository
    for acquisition_id in sources.acquisition_ids:
        if acq_repo is None:
            raise PostgresImportError("acquisition_ids requires AcquisitionRepository")
        rows["acquisitions"].append(_acquisition_row(acq_repo.get_acquisition(acquisition_id)))
    manifest_repo = sources.manifest_repository
    for partition_key in sources.partition_keys:
        if manifest_repo is None:
            raise PostgresImportError("partition_keys requires PartitionManifestRepository")
        manifest = manifest_repo.get_current_manifest(partition_key)
        pointer = manifest_repo.read_current_pointer(partition_key)
        rows["partition_manifest_current"].append(_manifest_row(manifest, pointer.updated_at if pointer else None))
    jobs = sources.job_repository
    if jobs is not None:
        for job_id in sorted(jobs.list_job_ids()):
            rows["storage_jobs"].append(_job_row(jobs.get_job(job_id)))
            rows["storage_job_transitions"].extend(_transition_row(t) for t in jobs.list_transitions(job_id))
    revisions = sources.revision_registry
    for source_key in sources.source_revision_keys:
        if revisions is None:
            raise PostgresImportError("source_revision_keys requires SourceRevisionRegistry")
        rows["source_revisions"].extend(_revision_row(rev) for rev in revisions.list_revisions(source_key))
    journal = sources.recovery_journal
    for run_id in sources.recovery_run_ids:
        if journal is None:
            raise PostgresImportError("recovery_run_ids requires RecoveryJournal")
        actions = journal.list_for_run(run_id)
        registered = []
        for action in actions:
            value = action.get("registered_at")
            if isinstance(value, str):
                value = datetime.fromisoformat(value)
            if isinstance(value, datetime):
                registered.append(value.astimezone(UTC))
        rows["recovery_runs"].append(_row("recovery_runs", recovery_run_id=run_id, action_count=len(actions), object_count=len({a.get("object_id") for a in actions}), problem_count=len({a.get("problem") for a in actions}), unresolved_count=sum(1 for a in actions if a.get("action_kind") in {"UNRESOLVED", "UNKNOWN"}), first_registered_at=min(registered, default=None), last_registered_at=max(registered, default=None)))
    return MetadataSnapshot({table: sorted(values, key=lambda row: tuple(str(row.get(c)) for c in _TABLE_COLUMNS[table])) for table, values in rows.items()})


class PostgresMetadataRepository:
    """Direct psycopg3 repository with explicit connection/transaction laws."""

    def __init__(self, config: PostgresMetadataConfig, *, connection_factory: Any = None, refresh_hook: Any = None) -> None:
        self.config = config
        self._connection_factory = connection_factory
        self._refresh_hook = refresh_hook

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        try:
            import psycopg  # type: ignore[import-not-found]  # noqa: PLC0415
        except ImportError as exc:
            raise PostgresImportError("psycopg[binary]>=3.2,<4 is required for PostgreSQL I11") from exc
        try:
            connection = self._connection_factory() if self._connection_factory else psycopg.connect(self.config.dsn)
            connection.execute("SET application_name = 'crypto_sensor_fabric_i11'")
            yield connection
        except PostgresMetadataError:
            raise
        except Exception as exc:
            raise PostgresMetadataError(f"PostgreSQL operation failed for {redact_dsn(self.config.dsn)} ({type(exc).__name__})") from None
        finally:
            if "connection" in locals():
                connection.close()

    @contextmanager
    def _transaction(self, connection: Any) -> Iterator[Any]:
        connection.execute("BEGIN")
        try:
            yield
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    @staticmethod
    def _sql_identifier(name: str) -> str:
        if name not in _TABLE_COLUMNS:
            raise PostgresSchemaError(f"unknown fixed table {name!r}")
        return '"' + name + '"'

    def _create_table_sql(self, table: str) -> str:
        schema = SCHEMA_NAME
        t = self._sql_identifier(table)
        if table == "schema_metadata":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (singleton boolean PRIMARY KEY CHECK (singleton), schema_version text NOT NULL CHECK (schema_version = '{SCHEMA_VERSION}'), repository_role text NOT NULL CHECK (repository_role = '{REPOSITORY_ROLE}'), installed_at timestamptz NOT NULL)'''
        if table == "provider_registry":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (provider_id text PRIMARY KEY, status text NOT NULL, evidence_class text NOT NULL, access_class text, capability_count integer NOT NULL CHECK (capability_count >= 0), fallback_count integer NOT NULL CHECK (fallback_count >= 0), notes text)'''
        if table == "adapter_readiness":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (provider_id text NOT NULL, sensor_family text NOT NULL, adapter_id text NOT NULL, adapter_version text NOT NULL, promoted boolean NOT NULL, implemented boolean NOT NULL, offline_conformance_pass boolean NOT NULL, schema_pass boolean NOT NULL, network_smoke_status text NOT NULL, evidence_ref text, pit_readiness text NOT NULL, limitations text NOT NULL, PRIMARY KEY (provider_id, sensor_family))'''
        if table == "storage_jobs":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (job_id text PRIMARY KEY, provider_id text NOT NULL, sensor_family text NOT NULL, request_fingerprint text NOT NULL, status text NOT NULL, updated_at timestamptz NOT NULL, last_committed_acquisition_id text, last_committed_blob_sha256 text, last_manifest_id text)'''
        if table == "storage_job_transitions":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (transition_id text PRIMARY KEY, job_id text NOT NULL REFERENCES "{schema}"."storage_jobs"(job_id), from_status text NOT NULL, to_status text NOT NULL, transitioned_at timestamptz NOT NULL, reason text, evidence_ref text)'''
        if table == "blobs_current_metadata":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (blob_sha256 text NOT NULL, storage_encoding text NOT NULL, byte_length bigint NOT NULL CHECK (byte_length >= 0), stored_byte_length bigint NOT NULL CHECK (stored_byte_length >= 0), source_media_type text NOT NULL, storage_uri text NOT NULL, integrity_state text NOT NULL, created_at timestamptz NOT NULL, PRIMARY KEY (blob_sha256, storage_encoding))'''
        if table == "acquisitions":
            cols = ", ".join(f"{self._sql_identifier(c)} {'timestamptz' if c.endswith('_at') or c in {'requested_start','requested_end','actual_start','actual_end'} else 'text'}" for c in _TABLE_COLUMNS[table])
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} ({cols}, PRIMARY KEY (acquisition_id))'''
        if table == "partition_manifest_current":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (partition_key text PRIMARY KEY, partition_manifest_id text NOT NULL UNIQUE, manifest_version integer NOT NULL CHECK (manifest_version >= 1), provider text NOT NULL, venue text NOT NULL, sensor_family text NOT NULL, native_instrument text NOT NULL, source_granularity text, date_basis text NOT NULL, logical_date_start timestamptz NOT NULL, logical_date_end timestamptz NOT NULL, coverage_state text NOT NULL, integrity_state text NOT NULL, row_count bigint, min_time timestamptz, max_time timestamptz, gap_count bigint, revision_count integer NOT NULL CHECK (revision_count >= 0), created_at timestamptz NOT NULL, supersedes_manifest_id text, pointer_updated_at timestamptz NOT NULL)'''
        if table == "source_revisions":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (source_revision_key text NOT NULL, revision_number integer NOT NULL CHECK (revision_number >= 1), blob_sha256 text NOT NULL, first_seen_at timestamptz NOT NULL, last_seen_at timestamptz NOT NULL, revision_reason text, revision_state text NOT NULL, PRIMARY KEY (source_revision_key, revision_number))'''
        if table == "integrity_checks":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (check_id text PRIMARY KEY, object_type text NOT NULL, object_id text NOT NULL, integrity_state text NOT NULL, checked_at timestamptz NOT NULL, expected_hash text, observed_hash text, provider_checksum_algorithm text, provider_checksum_value text, detail text)'''
        if table == "quota_state":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (singleton boolean PRIMARY KEY CHECK (singleton), pressure_state text NOT NULL, priority_class text, used_bytes bigint NOT NULL CHECK (used_bytes >= 0), capacity_bytes bigint NOT NULL CHECK (capacity_bytes >= 0), free_bytes bigint NOT NULL CHECK (free_bytes >= 0), utilization_ratio double precision NOT NULL CHECK (utilization_ratio BETWEEN 0 AND 1), absolute_free_floor_bytes bigint, observed_at timestamptz NOT NULL)'''
        if table == "backup_state":
            return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (singleton boolean PRIMARY KEY CHECK (singleton), state text NOT NULL, observed_at timestamptz NOT NULL, verified_object_count bigint NOT NULL CHECK (verified_object_count >= 0), verified_bytes bigint NOT NULL CHECK (verified_bytes >= 0), manifest_ref text, destination_ref text, verification_ref text)'''
        return f'''CREATE TABLE IF NOT EXISTS "{schema}".{t} (recovery_run_id text PRIMARY KEY, action_count integer NOT NULL CHECK (action_count >= 0), object_count integer NOT NULL CHECK (object_count >= 0), problem_count integer NOT NULL CHECK (problem_count >= 0), unresolved_count integer NOT NULL CHECK (unresolved_count >= 0), first_registered_at timestamptz, last_registered_at timestamptz)'''

    def install_schema(self) -> None:
        """Install the closed schema; unknown/future versions fail closed."""
        with self._connection() as connection:
            with self._transaction(connection):
                existing = connection.execute("SELECT to_regclass(%s)", (f"{SCHEMA_NAME}.schema_metadata",)).fetchone()
                if existing and existing[0] is not None:
                    row = connection.execute(f'SELECT schema_version, repository_role FROM "{SCHEMA_NAME}"."schema_metadata"').fetchone()
                    if row is None or row[0] != SCHEMA_VERSION or row[1] != REPOSITORY_ROLE:
                        raise PostgresSchemaError(f"unsupported or future schema metadata in {SCHEMA_NAME}")
                connection.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA_NAME}"')
                for table in ("schema_metadata",) + TABLE_NAMES:
                    connection.execute(self._create_table_sql(table))
                if not existing or existing[0] is None:
                    connection.execute(f'INSERT INTO "{SCHEMA_NAME}"."schema_metadata" (singleton, schema_version, repository_role, installed_at) VALUES (TRUE, %s, %s, CURRENT_TIMESTAMP)', (SCHEMA_VERSION, REPOSITORY_ROLE))

    def drop_schema(self) -> None:
        """Explicit test/rebuild operation; never called by refresh."""
        with self._connection() as connection:
            with self._transaction(connection):
                connection.execute(f'DROP SCHEMA IF EXISTS "{SCHEMA_NAME}" CASCADE')

    def introspect_schema(self) -> dict[str, Any]:
        with self._connection() as connection:
            tables = connection.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name", (SCHEMA_NAME,)).fetchall()
            names = [row[0] for row in tables if not row[0].startswith("_")]
            columns = connection.execute("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = %s ORDER BY table_name, ordinal_position", (SCHEMA_NAME,)).fetchall()
            return {"schema": SCHEMA_NAME, "schema_version": SCHEMA_VERSION, "tables": names, "columns": {table: [(name, typ) for t, name, typ in columns if t == table] for table in names}, "raw_table_absent": not any(any(part in name.casefold() for part in ("raw", "payload", "trade", "book", "market", "event")) for name in names), "generic_raw_column_absent": not any(any(part in name.casefold() for part in _FORBIDDEN_COLUMN_PARTS) for _, name, _ in columns), "bytea_absent": not any(typ.casefold() == "bytea" for _, _, typ in columns)}

    def _insert_row(self, connection: Any, table: str, row: Mapping[str, Any]) -> None:
        row = validate_row(table, row)
        columns = _TABLE_COLUMNS[table]
        names = ", ".join(self._sql_identifier(c) for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f'INSERT INTO "{SCHEMA_NAME}"."{table}" ({names}) VALUES ({placeholders})'
        try:
            connection.execute(sql, tuple(row[c] for c in columns))
        except Exception as exc:
            raise PostgresConflict(f"metadata identity conflict in {table}") from exc

    def _validate_db_invariants(self, connection: Any) -> None:
        version = connection.execute(f'SELECT schema_version, repository_role FROM "{SCHEMA_NAME}"."schema_metadata"').fetchone()
        if version is None or tuple(version) != (SCHEMA_VERSION, REPOSITORY_ROLE):
            raise PostgresSchemaError("database schema metadata invariant failed")
        orphan = connection.execute(f'SELECT COUNT(*) FROM "{SCHEMA_NAME}"."storage_job_transitions" t LEFT JOIN "{SCHEMA_NAME}"."storage_jobs" j USING (job_id) WHERE j.job_id IS NULL').fetchone()[0]
        if orphan:
            raise PostgresSchemaError("storage transition foreign-key invariant failed")

    def refresh_reconstructible_metadata(self, *, data_root: str | Path | None = None, provider_registry_path: str | Path | None = None, readiness_path: str | Path | None = None, sources: MetadataSources | None = None, snapshot: MetadataSnapshot | Mapping[str, Sequence[Mapping[str, Any]]] | None = None) -> dict[str, int]:
        """Atomically replace only reconstructible rows; operational state remains."""
        candidate = snapshot if isinstance(snapshot, MetadataSnapshot) else (MetadataSnapshot(snapshot) if snapshot is not None else reconstruct_snapshot(data_root=data_root, provider_registry_path=provider_registry_path, readiness_path=readiness_path, sources=sources))
        # Validate all rows before BEGIN, as required by the checkpoint law.
        for table in RECONSTRUCTIBLE_TABLES:
            for row in candidate.rows.get(table, ()):
                validate_row(table, row)
        with self._connection() as connection:
            with self._transaction(connection):
                connection.execute("SELECT pg_advisory_xact_lock(%s)", (_REFRESH_LOCK_KEY,))
                connection.execute("TRUNCATE TABLE " + ", ".join(f'"{SCHEMA_NAME}"."{table}"' for table in ("storage_job_transitions", "storage_jobs", "provider_registry", "adapter_readiness", "blobs_current_metadata", "acquisitions", "partition_manifest_current", "source_revisions", "recovery_runs")))
                counts: dict[str, int] = {}
                for table in RECONSTRUCTIBLE_TABLES:
                    records = candidate.rows.get(table, ())
                    for row in records:
                        self._insert_row(connection, table, row)
                    counts[table] = len(records)
                    if self._refresh_hook is not None:
                        self._refresh_hook(table, connection)
                self._validate_db_invariants(connection)
                return counts

    def upsert_operational_state(self, table: str, row: Mapping[str, Any]) -> None:
        if table not in OPERATIONAL_ONLY_TABLES:
            raise PostgresImportError(f"{table} is not operational-only state")
        row = validate_row(table, row)
        columns = _TABLE_COLUMNS[table]
        names = ", ".join(self._sql_identifier(c) for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        updates = ", ".join(f"{self._sql_identifier(c)}=EXCLUDED.{self._sql_identifier(c)}" for c in columns if c != "singleton")
        sql = f'INSERT INTO "{SCHEMA_NAME}"."{table}" ({names}) VALUES ({placeholders}) ON CONFLICT (singleton) DO UPDATE SET {updates}'
        with self._connection() as connection:
            with self._transaction(connection):
                connection.execute(sql, tuple(row[c] for c in columns))

    def canonical_rows(self) -> dict[str, list[tuple[Any, ...]]]:
        """Return deterministic scientific rows, excluding operational tables."""
        with self._connection() as connection:
            result: dict[str, list[tuple[Any, ...]]] = {}
            for table in RECONSTRUCTIBLE_TABLES:
                columns = _TABLE_COLUMNS[table]
                order = ", ".join(self._sql_identifier(columns[0]) if len(columns) == 1 else ", ".join(self._sql_identifier(c) for c in columns[:2]))
                select = ", ".join(self._sql_identifier(c) for c in columns)
                rows = connection.execute(f'SELECT {select} FROM "{SCHEMA_NAME}"."{table}" ORDER BY {order}').fetchall()
                result[table] = [tuple(row) for row in rows]
            return result


__all__ = [
    "MetadataSnapshot", "MetadataSources", "PostgresConflict", "PostgresImportError",
    "PostgresMetadataConfig", "PostgresMetadataError", "PostgresMetadataRepository",
    "PostgresSchemaError", "RECONSTRUCTIBLE_TABLES", "REPOSITORY_ROLE", "SCHEMA_NAME",
    "SCHEMA_VERSION", "TABLE_AUTHORITY", "TABLE_NAMES", "redact_dsn", "reconstruct_snapshot",
    "validate_row",
]
