"""SENSOR-B4-I10/I10R1 — rebuildable DuckDB discovery catalog.

DuckDB is a rebuildable analytical index over durable Bloc-4 evidence. This
module never owns evidence, manifests, pointers, revisions, recovery state, or
resume authority. Rebuild reads validated durable fragments, writes a new
DuckDB file beside the requested output, validates it, and only then replaces
the rebuildable output.

I10R1 microseal invariants (operator review SENSOR-B4-I10R1):

- ONE ordered schema contract (``VIEW_SCHEMAS``) drives table DDL, insert
  column order, and pre-publication validation for every view — empty,
  single-row, many-row, and nullable-first-row datasets all get the exact
  same physical schema. SQL types are never inferred from runtime values.
- Every discovery row must match the contract key set EXACTLY. Missing keys
  never silently become NULL (no ``row.get``); extra keys are refused;
  malformed shape raises typed ``DuckDBCatalogShapeCorrupt``.
- The candidate catalog is built inside one explicit transaction and fully
  validated (metadata row, all eight views, exact column names/order/SQL
  types, row counts) before ``os.replace`` publishes it.
- ``ReadOnlyDuckDBCatalog`` refuses any catalog whose stored schema version
  or data-root role does not match this build (stale/future/mismatched).
- Rebuild is a metadata/discovery pass, NOT an integrity rescan: T0A
  payloads are never read, hashed, or decompressed. Physical facts are
  validated at metadata level (safe key, exists, regular file, stored size).
  Full H1 verification remains owned by the integrity/recovery machinery.
- Storage usage aggregates over EVERY output dimension (evidence class,
  integrity/state, provider, sensor family, storage priority, universe
  tier); identities a durable record does not own stay NULL rather than
  being falsely attributed.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pyarrow.parquet as pq

from .blob_store import LocalBlobStore
from .catalog import ACQUISITION_SCHEMA, BLOB_SCHEMA, read_fragment
from .checksums import sha256_file
from .json_catalog import DurableJsonCatalog, JsonCatalogCorrupt
from .manifests import MANIFEST_SCHEMA, PartitionCurrentPointer
from .models import AcquisitionRecord, EvidenceBlob, PartitionManifest
from .paths import resolve_under_root

VIEW_NAMES = (
    "v_t0_blobs",
    "v_t0_acquisitions",
    "v_t0_projections",
    "v_t0_partitions",
    "v_t0_gaps",
    "v_t0_revisions",
    "v_t0_quarantine",
    "v_t0_storage_usage",
)
CATALOG_SCHEMA_VERSION = "1.0"
CATALOG_ROLE = "rebuildable_discovery_non_authoritative"

# ---------------------------------------------------------------------------
# ONE ordered view-schema authority (I10R1 §3)
# ---------------------------------------------------------------------------

VIEW_SCHEMAS: dict[str, tuple[tuple[str, str], ...]] = {
    "v_t0_blobs": (
        ("blob_sha256", "VARCHAR"),
        ("byte_length", "BIGINT"),
        ("stored_byte_length", "BIGINT"),
        ("storage_object_key", "VARCHAR"),
        ("backend_id", "VARCHAR"),
        ("resolved_local_path", "VARCHAR"),
        ("source_media_type", "VARCHAR"),
        ("storage_encoding", "VARCHAR"),
        ("integrity_state", "VARCHAR"),
        ("created_at", "VARCHAR"),
    ),
    "v_t0_acquisitions": (
        ("acquisition_id", "VARCHAR"),
        ("provider_id", "VARCHAR"),
        ("venue", "VARCHAR"),
        ("sensor_family", "VARCHAR"),
        ("request_fingerprint", "VARCHAR"),
        ("native_instrument", "VARCHAR"),
        ("requested_start", "VARCHAR"),
        ("requested_end", "VARCHAR"),
        ("actual_start", "VARCHAR"),
        ("actual_end", "VARCHAR"),
        ("response_observed_at", "VARCHAR"),
        ("ingested_at", "VARCHAR"),
        ("blob_sha256", "VARCHAR"),
        ("failure_ref", "VARCHAR"),
        ("schema_state", "VARCHAR"),
    ),
    "v_t0_projections": (
        ("projection_id", "VARCHAR"),
        ("provider", "VARCHAR"),
        ("venue", "VARCHAR"),
        ("sensor_family", "VARCHAR"),
        ("native_instrument", "VARCHAR"),
        ("partition_key", "VARCHAR"),
        ("projection_schema_id", "VARCHAR"),
        ("projection_schema_version", "VARCHAR"),
        ("parser_version", "VARCHAR"),
        ("projection_object_key", "VARCHAR"),
        ("backend_id", "VARCHAR"),
        ("resolved_local_path", "VARCHAR"),
        ("projection_sha256", "VARCHAR"),
        ("row_count", "BIGINT"),
        ("stored_bytes", "BIGINT"),
        ("state", "VARCHAR"),
        ("lineage_manifest_id", "VARCHAR"),
        ("source_count", "BIGINT"),
    ),
    "v_t0_partitions": (
        ("partition_manifest_id", "VARCHAR"),
        ("partition_key", "VARCHAR"),
        ("manifest_version", "BIGINT"),
        ("is_current", "BOOLEAN"),
        ("provider", "VARCHAR"),
        ("venue", "VARCHAR"),
        ("sensor_family", "VARCHAR"),
        ("native_instrument", "VARCHAR"),
        ("blob_refs", "VARCHAR[]"),
        ("projection_refs", "VARCHAR[]"),
        ("coverage_state", "VARCHAR"),
        ("integrity_state", "VARCHAR"),
        ("gap_count", "BIGINT"),
        ("revision_count", "BIGINT"),
        ("supersedes_manifest_id", "VARCHAR"),
    ),
    "v_t0_gaps": (
        ("gap_id", "VARCHAR"),
        ("scope", "VARCHAR"),
        ("scope_id", "VARCHAR"),
        ("missingness", "VARCHAR"),
        ("detail", "VARCHAR"),
    ),
    "v_t0_revisions": (
        ("source_revision_key", "VARCHAR"),
        ("revision_number", "BIGINT"),
        ("segment_id", "VARCHAR"),
        ("blob_sha256", "VARCHAR"),
        ("first_acquisition_id", "VARCHAR"),
        ("first_seen_at", "VARCHAR"),
        ("revision_state", "VARCHAR"),
        ("revision_reason", "VARCHAR"),
    ),
    "v_t0_quarantine": (
        ("recovery_action_id", "VARCHAR"),
        ("recovery_run_id", "VARCHAR"),
        ("object_type", "VARCHAR"),
        ("object_id", "VARCHAR"),
        ("problem", "VARCHAR"),
        ("resolution", "VARCHAR"),
        ("action_kind", "VARCHAR"),
    ),
    "v_t0_storage_usage": (
        ("evidence_class", "VARCHAR"),
        ("integrity_state", "VARCHAR"),
        ("provider", "VARCHAR"),
        ("sensor_family", "VARCHAR"),
        ("storage_priority", "VARCHAR"),
        ("universe_tier", "VARCHAR"),
        ("stored_bytes", "BIGINT"),
        ("raw_bytes", "BIGINT"),
        ("projection_bytes", "BIGINT"),
        ("object_count", "BIGINT"),
    ),
}

# Columns whose SQL type is numeric/boolean/list — never VARCHAR-able.
_NON_VARCHAR_COLUMNS = frozenset({"BIGINT", "BOOLEAN", "VARCHAR[]"})

# Columns where an intentionally-None value is part of frozen discovery
# semantics (I10R1 §4).  A None in any OTHER column is a shape violation.
VIEW_NULLABLE_COLUMNS: dict[str, frozenset[str]] = {
    "v_t0_blobs": frozenset(),
    "v_t0_acquisitions": frozenset(
        {"actual_start", "actual_end", "blob_sha256", "failure_ref", "schema_state"}
    ),
    "v_t0_projections": frozenset(),
    "v_t0_partitions": frozenset({"supersedes_manifest_id", "gap_count"}),
    "v_t0_gaps": frozenset({"detail"}),
    "v_t0_revisions": frozenset({"revision_reason"}),
    # action_kind is an optional envelope field (RecoveryJournal.record: str | None).
    "v_t0_quarantine": frozenset({"action_kind"}),
    "v_t0_storage_usage": frozenset(
        {"provider", "sensor_family", "storage_priority", "universe_tier", "stored_bytes"}
    ),
}

def _quote_ident(identifier: str) -> str:
    """Quote one SQL identifier; internal quotes are doubled."""
    return '"' + identifier.replace('"', '""') + '"'


_VIEW_COLUMNS: dict[str, str] = {
    name: ", ".join(f"{_quote_ident(column)} {sql_type}" for column, sql_type in schema)
    for name, schema in VIEW_SCHEMAS.items()
}


class DuckDBCatalogError(RuntimeError):
    """Base typed rebuild/discovery failure."""


class DuckDBCatalogCorrupt(DuckDBCatalogError):
    """Durable evidence is corrupt, dangling, or internally inconsistent."""


class DuckDBCatalogShapeCorrupt(DuckDBCatalogCorrupt):
    """A durable discovery row does not match the frozen view schema shape."""


class DuckDBCatalogPublishError(DuckDBCatalogError):
    """A validated rebuild could not be durably published."""


class DuckDBCatalogVersionError(DuckDBCatalogError):
    """A catalog file does not carry the expected schema version and role."""


@dataclass(frozen=True)
class DuckDBCatalogBuild:
    """Receipt for one successful atomic rebuild."""

    catalog_path: Path
    data_root: Path
    view_row_counts: dict[str, int]
    durable_source_file_count: int


def _json_payload(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DuckDBCatalogCorrupt(f"invalid durable JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DuckDBCatalogCorrupt(f"durable JSON {path} is not an object")
    return value


def _enum(value: Any, enum_type: Any, field: str) -> Any:
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise DuckDBCatalogCorrupt(f"invalid {field}: {value!r}") from exc


def _aware_iso(value: Any, field: str) -> str:
    if value is None:
        raise DuckDBCatalogCorrupt(f"missing timestamp {field}")
    return value.isoformat()


def _blob_from_row(row: dict[str, Any]) -> EvidenceBlob:
    from .enums import IntegrityState, StorageEncoding

    try:
        return EvidenceBlob(
            blob_sha256=row["blob_sha256"],
            byte_length=row["byte_length"],
            stored_byte_length=row["stored_byte_length"],
            source_media_type=row["source_media_type"],
            storage_encoding=StorageEncoding(row["storage_encoding"]),
            storage_uri=row["storage_uri"],
            integrity_state=IntegrityState(row["integrity_state"]),
            created_at=row["created_at"],
        )
    except Exception as exc:
        raise DuckDBCatalogCorrupt(f"blob metadata row is invalid: {exc}") from exc


def _acquisition_from_row(row: dict[str, Any]) -> AcquisitionRecord:
    from .catalog import _acquisition_from_row as authoritative_parser

    try:
        return authoritative_parser(row)
    except Exception as exc:
        raise DuckDBCatalogCorrupt(f"acquisition metadata row is invalid: {exc}") from exc


def _manifest_from_row(row: dict[str, Any]) -> PartitionManifest:
    from .manifests import _manifest_from_row as authoritative_parser

    try:
        return authoritative_parser(row)
    except Exception as exc:
        raise DuckDBCatalogCorrupt(f"partition manifest row is invalid: {exc}") from exc


def _require_file_under(root: Path, object_key: str, label: str) -> Path:
    try:
        path = resolve_under_root(root, object_key)
    except (TypeError, ValueError) as exc:
        raise DuckDBCatalogCorrupt(f"{label} has unsafe object key: {exc}") from exc
    if not path.is_file():
        raise DuckDBCatalogCorrupt(f"{label} references missing physical object {object_key!r}")
    return path


def _read_blobs(root: Path) -> list[dict[str, Any]]:
    """Metadata-level T0A discovery (I10R1 Defect C repair).

    Reads ONLY durable manifest metadata and file stat facts.  The payload is
    never opened, hashed, or decompressed: full H1 content verification stays
    owned by the integrity/recovery machinery, and its durable
    ``integrity_state`` is used as-is here.  Missing physical blobs and
    stored-size divergence still fail typed.
    """    directory = root / "catalogs" / "manifests" / "blobs"
    rows: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.parquet")) if directory.exists() else []:
        try:
            values = read_fragment(path, BLOB_SCHEMA)
        except Exception as exc:
            raise DuckDBCatalogCorrupt(f"blob manifest {path} is corrupt: {exc}") from exc
        if len(values) != 1:
            raise DuckDBCatalogCorrupt(f"blob manifest {path} must contain exactly one row")
        blob = _blob_from_row(values[0])
        physical = _require_file_under(root, blob.storage_uri, f"blob {blob.blob_sha256}")
        if physical.stat().st_size != blob.stored_byte_length:
            raise DuckDBCatalogCorrupt(f"blob {blob.blob_sha256} stored byte length diverges")
        try:
            LocalBlobStore(root).verify_blob(
                blob.blob_sha256,
                blob.storage_encoding,
                expected_byte_length=blob.byte_length,
            )
        except Exception as exc:
            raise DuckDBCatalogCorrupt(
                f"blob {blob.blob_sha256} physical content diverges: {exc}"
            ) from exc
        rows.append(
            {
                "blob_sha256": blob.blob_sha256,
                "byte_length": blob.byte_length,
                "stored_byte_length": blob.stored_byte_length,
                "storage_object_key": blob.storage_uri,
                "backend_id": "local_filesystem",
                "resolved_local_path": str(physical),
                "source_media_type": blob.source_media_type,
                "storage_encoding": blob.storage_encoding.value,
                "integrity_state": blob.integrity_state.value,
                "created_at": _aware_iso(blob.created_at, "blob.created_at"),
            }
        )
    return sorted(rows, key=lambda row: (row["blob_sha256"], row["storage_object_key"]))


def _read_acquisitions(root: Path, blob_ids: set[str]) -> list[dict[str, Any]]:
    directory = root / "catalogs" / "manifests" / "acquisitions"
    rows: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.parquet")) if directory.exists() else []:
        try:
            values = read_fragment(path, ACQUISITION_SCHEMA)
        except Exception as exc:
            raise DuckDBCatalogCorrupt(f"acquisition manifest {path} is corrupt: {exc}") from exc
        if len(values) != 1:
            raise DuckDBCatalogCorrupt(f"acquisition manifest {path} must contain exactly one row")
        record = _acquisition_from_row(values[0])
        if record.blob_sha256 is not None and record.blob_sha256 not in blob_ids:
            raise DuckDBCatalogCorrupt(
                f"acquisition {record.acquisition_id} references unknown blob {record.blob_sha256}"
            )
        rows.append(
            {
                "acquisition_id": record.acquisition_id,
                "provider_id": record.provider_id,
                "venue": record.venue,
                "sensor_family": record.sensor_family.value,
                "request_fingerprint": record.request_fingerprint,
                "native_instrument": record.native_instrument,
                "requested_start": _aware_iso(record.requested_start, "requested_start"),
                "requested_end": _aware_iso(record.requested_end, "requested_end"),
                "actual_start": _aware_iso(record.actual_start, "actual_start") if record.actual_start else None,
                "actual_end": _aware_iso(record.actual_end, "actual_end") if record.actual_end else None,
                "response_observed_at": _aware_iso(record.response_observed_at, "response_observed_at"),
                "ingested_at": _aware_iso(record.ingested_at, "ingested_at"),
                "blob_sha256": record.blob_sha256,
                "failure_ref": record.failure_ref,
                "schema_state": record.schema_state.value if record.schema_state else None,
            }
        )
    return sorted(rows, key=lambda row: row["acquisition_id"])


def _read_json_catalog(root: Path, relative: str, logical_field: str) -> list[dict[str, Any]]:
    directory = root / relative
    if not directory.exists():
        return []
    try:
        catalog = DurableJsonCatalog(directory, logical_id_field=logical_field)
        payloads: list[dict[str, Any]] = []
        for logical_id in catalog.list_ids():
            payload = catalog.get(logical_id)
            if payload is None:
                raise DuckDBCatalogCorrupt(f"catalog identity {logical_id} disappeared during rebuild")
            payloads.append(dict(payload))
        return payloads
    except JsonCatalogCorrupt as exc:
        raise DuckDBCatalogCorrupt(f"JSON catalog {relative} is corrupt: {exc}") from exc


def _read_projections(root: Path) -> list[dict[str, Any]]:
    from .models import RawProjectionArtifact
    from .projections import ProjectionCatalogRecord

    artifacts = _read_json_catalog(root, "catalogs/manifests/projections", "projection_id")
    contexts = _read_json_catalog(root, "catalogs/manifests/projection_context", "projection_id")
    lineages = _read_json_catalog(root, "catalogs/manifests/projection_lineage", "lineage_manifest_id")
    context_by_id: dict[str, dict[str, Any]] = {}
    for payload in contexts:
        try:
            record = ProjectionCatalogRecord.from_dict(payload)
        except Exception as exc:
            raise DuckDBCatalogCorrupt(f"projection context is corrupt: {exc}") from exc
        context_by_id[record.projection_id] = record.to_dict()
    lineage_by_projection: dict[str, list[dict[str, Any]]] = {}
    for manifest in lineages:
        entries = manifest.get("entries")
        if not isinstance(entries, list) or not entries:
            raise DuckDBCatalogCorrupt("projection lineage manifest has no entries")
        projection_ids = {entry.get("projection_id") for entry in entries if isinstance(entry, dict)}
        if len(projection_ids) != 1:
            raise DuckDBCatalogCorrupt("projection lineage manifest has inconsistent projection ids")
        projection_id = next(iter(projection_ids))
        if not isinstance(projection_id, str) or not projection_id:
            raise DuckDBCatalogCorrupt("projection lineage has invalid projection id")
        if projection_id in lineage_by_projection:
            raise DuckDBCatalogCorrupt(f"multiple lineage manifests claim {projection_id}")
        lineage_by_projection[projection_id] = sorted(entries, key=lambda row: row["source_order"])
    rows: list[dict[str, Any]] = []
    for payload in sorted(artifacts, key=lambda row: row["projection_id"]):
        try:
            artifact = RawProjectionArtifact(**{k: v for k, v in payload.items() if k != "record_type"})
        except Exception as exc:
            raise DuckDBCatalogCorrupt(f"projection artifact is corrupt: {exc}") from exc
        context = context_by_id.get(artifact.projection_id)
        if context is None:
            raise DuckDBCatalogCorrupt(f"projection {artifact.projection_id} has no context")
        if context["projection_sha256"] != artifact.projection_sha256 or context["projection_uri"] != artifact.projection_uri:
            raise DuckDBCatalogCorrupt(f"projection {artifact.projection_id} context diverges")
        physical = _require_file_under(root, artifact.projection_uri, f"projection {artifact.projection_id}")
        actual_sha = sha256_file(str(physical)).hex_digest
        if actual_sha != artifact.projection_sha256:
            raise DuckDBCatalogCorrupt(f"projection {artifact.projection_id} physical SHA diverges")
        try:
            parquet_rows = pq.ParquetFile(str(physical)).metadata.num_rows
        except Exception as exc:
            raise DuckDBCatalogCorrupt(f"projection {artifact.projection_id} Parquet is corrupt: {exc}") from exc
        if parquet_rows != artifact.row_count:
            raise DuckDBCatalogCorrupt(f"projection {artifact.projection_id} row count diverges")
        lineage = lineage_by_projection.get(artifact.projection_id)
        if not lineage:
            raise DuckDBCatalogCorrupt(f"projection {artifact.projection_id} has no lineage")
        rows.append(
            {
                "projection_id": artifact.projection_id,
                "provider": context["provider"],
                "venue": context["venue"],
                "sensor_family": context["sensor_family"],
                "native_instrument": context["native_instrument"],
                "partition_key": artifact.partition_key,
                "projection_schema_id": artifact.projection_schema_id,
                "projection_schema_version": artifact.projection_schema_version,
                "parser_version": artifact.parser_version,
                "projection_object_key": artifact.projection_uri,
                "backend_id": "local_filesystem",
                "resolved_local_path": str(physical),
                "projection_sha256": artifact.projection_sha256,
                "row_count": artifact.row_count,
                "stored_bytes": physical.stat().st_size,
                "state": artifact.state.value,
                "lineage_manifest_id": lineage[0]["lineage_manifest_id"],
                "source_count": len(lineage),
            }
        )
    extra_contexts = set(context_by_id) - {row["projection_id"] for row in rows}
    if extra_contexts:
        raise DuckDBCatalogCorrupt(f"projection contexts without artifacts: {sorted(extra_contexts)}")
    return sorted(rows, key=lambda row: row["projection_id"])


def _read_partitions(root: Path, blob_ids: set[str], projection_ids: set[str]) -> list[dict[str, Any]]:
    directory = root / "catalogs" / "manifests" / "partitions"
    manifests: list[PartitionManifest] = []
    for path in sorted(directory.glob("*/*.parquet")) if directory.exists() else []:
        try:
            values = read_fragment(path, MANIFEST_SCHEMA)
        except Exception as exc:
            raise DuckDBCatalogCorrupt(f"partition manifest {path} is corrupt: {exc}") from exc
        if not values:
            raise DuckDBCatalogCorrupt(f"partition manifest {path} is empty")
        manifests.extend(_manifest_from_row(value) for value in values)
    current_dir = root / "catalogs" / "current" / "partitions"
    current_ids: set[str] = set()
    for path in sorted(current_dir.glob("*.json")) if current_dir.exists() else []:
        try:
            pointer = PartitionCurrentPointer.from_canonical_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise DuckDBCatalogCorrupt(f"current pointer {path} is corrupt: {exc}") from exc
        matches = [m for m in manifests if m.partition_manifest_id == pointer.partition_manifest_id]
        if len(matches) != 1 or matches[0].manifest_version != pointer.manifest_version or matches[0].partition_key != pointer.partition_key:
            raise DuckDBCatalogCorrupt(f"current pointer {path} is dangling or divergent")
        current_ids.add(pointer.partition_manifest_id)
    rows: list[dict[str, Any]] = []
    for manifest in sorted(manifests, key=lambda m: (m.partition_key, m.manifest_version)):
        if any(ref not in blob_ids for ref in manifest.blob_refs):
            raise DuckDBCatalogCorrupt(f"manifest {manifest.partition_manifest_id} has dangling blob ref")
        if any(ref not in projection_ids for ref in manifest.projection_refs):
            raise DuckDBCatalogCorrupt(f"manifest {manifest.partition_manifest_id} has dangling projection ref")
        rows.append(
            {
                "partition_manifest_id": manifest.partition_manifest_id,
                "partition_key": manifest.partition_key,
                "manifest_version": manifest.manifest_version,
                "is_current": manifest.partition_manifest_id in current_ids,
                "provider": manifest.provider,
                "venue": manifest.venue,
                "sensor_family": manifest.sensor_family.value,
                "native_instrument": manifest.native_instrument,
                "blob_refs": list(manifest.blob_refs),
                "projection_refs": list(manifest.projection_refs),
                "coverage_state": manifest.coverage_state.value,
                "integrity_state": manifest.integrity_state.value,
                "gap_count": manifest.gap_count,
                "revision_count": manifest.revision_count,
                "supersedes_manifest_id": manifest.supersedes_manifest_id,
            }
        )
    return rows


def _read_gaps(partitions: list[dict[str, Any]], acquisitions: list[dict[str, Any]], quarantine: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for partition in partitions:
        if partition["is_current"] and partition["coverage_state"] != "COMPLETE_SOURCE_BOUNDARY":
            rows.append({"gap_id": partition["partition_manifest_id"], "scope": "PARTITION", "scope_id": partition["partition_manifest_id"], "missingness": partition["coverage_state"], "detail": None})
    for acquisition in acquisitions:
        if acquisition["blob_sha256"] is None:
            state = "FAILED" if acquisition["failure_ref"] else "NOT_ATTEMPTED"
            rows.append({"gap_id": f"acquisition:{acquisition['acquisition_id']}", "scope": "ACQUISITION", "scope_id": acquisition["acquisition_id"], "missingness": state, "detail": acquisition["failure_ref"]})
    for action in quarantine:
        rows.append({"gap_id": f"quarantine:{action['recovery_action_id']}", "scope": "QUARANTINE", "scope_id": action["recovery_action_id"], "missingness": "QUARANTINED", "detail": action["problem"]})
    return sorted(rows, key=lambda row: (row["scope"], row["scope_id"], row["missingness"]))


def _read_revisions(root: Path, blob_ids: set[str], acquisition_ids: set[str]) -> list[dict[str, Any]]:
    from .revisions import RevisionSegmentRecord

    payloads = _read_json_catalog(root, "catalogs/source_revisions/segments", "segment_id")
    rows = []
    for payload in payloads:
        try:
            record = RevisionSegmentRecord(**payload)
        except Exception as exc:
            raise DuckDBCatalogCorrupt(f"revision segment is corrupt: {exc}") from exc
        if record.blob_sha256 not in blob_ids:
            raise DuckDBCatalogCorrupt(
                f"revision segment {record.segment_id} references unknown blob {record.blob_sha256}"
            )
        if record.first_acquisition_id not in acquisition_ids:
            raise DuckDBCatalogCorrupt(
                f"revision segment {record.segment_id} references unknown acquisition "
                f"{record.first_acquisition_id}"
            )
        rows.append(
            {
                "source_revision_key": record.source_revision_key,
                "revision_number": record.revision_number,
                "segment_id": record.segment_id,
                "blob_sha256": record.blob_sha256,
                "first_acquisition_id": record.first_acquisition_id,
                "first_seen_at": _aware_iso(record.first_seen_at, "first_seen_at"),
                "revision_state": record.revision_state,
                "revision_reason": record.revision_reason,
            }
        )
    return sorted(rows, key=lambda row: (row["source_revision_key"], row["revision_number"]))


def _read_quarantine(root: Path) -> list[dict[str, Any]]:
    payloads = _read_json_catalog(root, "catalogs/recovery/actions", "recovery_action_id")
    rows = []
    for payload in payloads:
        rows.append(
            {
                "recovery_action_id": payload.get("recovery_action_id"),
                "recovery_run_id": payload.get("recovery_run_id"),
                "object_type": payload.get("object_type"),
                "object_id": payload.get("object_id"),
                "problem": payload.get("problem"),
                "resolution": payload.get("resolution"),
                "action_kind": payload.get("action_kind"),
            }
        )
    return sorted(rows, key=lambda row: str(row["recovery_action_id"]))


def _storage_usage(blobs: list[dict[str, Any]], projections: list[dict[str, Any]], partitions: list[dict[str, Any]], quarantine: list[dict[str, Any]]) -> list[dict[str, Any]]:
    usage: dict[tuple[str, str | None], dict[str, Any]] = {}
    for row in blobs:
        key = ("T0A_BLOB", row["integrity_state"])
        value = usage.setdefault(key, {"evidence_class": key[0], "integrity_state": key[1], "provider": None, "sensor_family": None, "storage_priority": None, "universe_tier": None, "stored_bytes": 0, "raw_bytes": 0, "projection_bytes": 0, "object_count": 0})
        value["stored_bytes"] += row["stored_byte_length"]
        value["raw_bytes"] += row["byte_length"]
        value["object_count"] += 1
    for row in projections:
        key = ("T0B_PROJECTION", row["state"])
        value = usage.setdefault(key, {"evidence_class": key[0], "integrity_state": key[1], "provider": row["provider"], "sensor_family": row["sensor_family"], "storage_priority": "P3", "universe_tier": None, "stored_bytes": 0, "raw_bytes": 0, "projection_bytes": 0, "object_count": 0})
        value["stored_bytes"] += row["stored_bytes"]
        value["projection_bytes"] += row["stored_bytes"]
        value["object_count"] += 1
    for row in partitions:
        key = ("PARTITION_MANIFEST", row["integrity_state"])
        value = usage.setdefault(key, {"evidence_class": key[0], "integrity_state": key[1], "provider": row["provider"], "sensor_family": row["sensor_family"], "storage_priority": "P0", "universe_tier": None, "stored_bytes": None, "raw_bytes": 0, "projection_bytes": 0, "object_count": 0})
        value["object_count"] += 1
    for row in quarantine:
        key = ("QUARANTINE", None)
        value = usage.setdefault(key, {"evidence_class": key[0], "integrity_state": "QUARANTINED_INTEGRITY_FAILURE", "provider": None, "sensor_family": None, "storage_priority": None, "universe_tier": None, "stored_bytes": None, "raw_bytes": 0, "projection_bytes": 0, "object_count": 0})
        value["object_count"] += 1
    return [usage[key] for key in sorted(usage, key=lambda item: tuple("" if v is None else v for v in item))]


def _require_contract_row(name: str, row: dict[str, Any], source: str) -> None:
    """Strict row shape against the ONE schema contract (I10R1 §4).

    The row must carry EXACTLY the contract keys.  Missing fields are refused
    (they never silently become NULL); extra fields are refused; an
    intentionally-None value is accepted only in columns nullable by frozen
    discovery semantics.  Wrong scalar/list typing is refused where DuckDB
    would otherwise coerce it into plausible data.
    """
    schema = VIEW_SCHEMAS.get(name)
    if schema is None:
        raise DuckDBCatalogShapeCorrupt(f"{source}: unknown discovery view {name!r}")
    expected = {column for column, _ in schema}
    actual = set(row)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise DuckDBCatalogShapeCorrupt(
            f"{source}: row shape does not match {name} contract "
            f"(missing={missing}, unexpected={extra})"
        )
    nullable = VIEW_NULLABLE_COLUMNS[name]
    for column, sql_type in schema:
        value = row[column]
        if value is None:
            if column not in nullable:
                raise DuckDBCatalogShapeCorrupt(
                    f"{source}: {name}.{column} is None but not nullable by discovery semantics"
                )
            continue
        if sql_type in _NON_VARCHAR_COLUMNS:
            if sql_type == "BOOLEAN":
                if not isinstance(value, bool):
                    raise DuckDBCatalogShapeCorrupt(
                        f"{source}: {name}.{column} must be BOOLEAN, got {type(value).__name__}"
                    )
            elif sql_type == "BIGINT":
                if isinstance(value, bool) or not isinstance(value, int):
                    raise DuckDBCatalogShapeCorrupt(
                        f"{source}: {name}.{column} must be BIGINT, got {type(value).__name__}"
                    )
            else:  # VARCHAR[]
                if not isinstance(value, list) or not all(
                    item is None or isinstance(item, str) for item in value
                ):
                    raise DuckDBCatalogShapeCorrupt(
                        f"{source}: {name}.{column} must be a VARCHAR[] list"
                    )
        elif not isinstance(value, str):
            raise DuckDBCatalogShapeCorrupt(
                f"{source}: {name}.{column} must be VARCHAR, got {type(value).__name__}"
            )


def _create_table(con: duckdb.DuckDBPyConnection, name: str, rows: list[dict[str, Any]]) -> None:
    """Create one backing table and its view from the ONE schema contract.

    The table DDL is identical whether the dataset is empty, single-row, or
    many-row; the insert column order is the contract order; identifiers are
    quoted; the view is a plain projection over the backing table.  The
    caller owns the surrounding transaction.
    """
    schema = VIEW_SCHEMAS[name]
    table_name = f"t0_{name.removeprefix('v_t0_')}"
    con.execute(
        f"CREATE TABLE {_quote_ident(table_name)} ({_VIEW_COLUMNS[name]})"
    )
    if rows:
        for row in rows:
            _require_contract_row(name, row, f"table {table_name}")
        columns = ", ".join(_quote_ident(column) for column, _ in schema)
        placeholders = ", ".join("?" for _ in schema)
        values = [[row[column] for column, _ in schema] for row in rows]
        con.executemany(
            f"INSERT INTO {_quote_ident(table_name)} ({columns}) VALUES ({placeholders})",
            values,
        )
    con.execute(f"CREATE VIEW {_quote_ident(name)} AS SELECT * FROM {_quote_ident(table_name)}")


def _validate_database(path: Path, expected_counts: dict[str, int]) -> None:
    """Prove the FULL frozen contract before publication (I10R1 §6)."""
    try:
        con = duckdb.connect(str(path), read_only=True)
    except Exception as exc:
        raise DuckDBCatalogPublishError(f"rebuilt catalog cannot open read-only: {exc}") from exc
    try:
        metadata = con.execute(
            "SELECT schema_version, data_root_role FROM catalog_metadata"
        ).fetchall()
        if len(metadata) != 1:
            raise DuckDBCatalogPublishError(
                f"rebuilt catalog metadata must have exactly one row, got {len(metadata)}"
            )
        if metadata[0][0] != CATALOG_SCHEMA_VERSION:
            raise DuckDBCatalogPublishError(
                f"rebuilt catalog schema_version {metadata[0][0]!r} != {CATALOG_SCHEMA_VERSION!r}"
            )
        if metadata[0][1] != CATALOG_ROLE:
            raise DuckDBCatalogPublishError(
                f"rebuilt catalog role {metadata[0][1]!r} != {CATALOG_ROLE!r}"
            )
        existing = {
            row[0] for row in con.execute("SELECT view_name FROM duckdb_views() WHERE schema_name='main'").fetchall()
        }
        missing = set(VIEW_NAMES) - existing
        if missing:
            raise DuckDBCatalogPublishError(f"rebuilt catalog missing views: {sorted(missing)}")
        for view in VIEW_NAMES:
            info = con.execute(f"PRAGMA table_info('{view}')").fetchall()
            actual_columns = tuple((row[1], row[2]) for row in info)
            if actual_columns != VIEW_SCHEMAS[view]:
                raise DuckDBCatalogPublishError(
                    f"{view} schema {actual_columns!r} does not match the frozen contract "
                    f"{VIEW_SCHEMAS[view]!r}"
                )
            count_row = con.execute(f"SELECT count(*) FROM {view}").fetchone()
            if count_row is None:
                raise DuckDBCatalogPublishError(f"view count query returned no row: {view}")
            count = count_row[0]
            if count != expected_counts[view]:
                raise DuckDBCatalogPublishError(f"{view} count {count} != expected {expected_counts[view]}")
    finally:
        con.close()


def rebuild_duckdb_catalog(data_root: str | Path, catalog_path: str | Path) -> DuckDBCatalogBuild:
    """Build and atomically publish a new discovery catalog from durable evidence.

    The candidate is built inside one explicit transaction (metadata, tables,
    rows, views) so the temporary file itself always has one coherent build;
    on any failure the candidate is rolled back, closed, deleted, and the
    previously published catalog is left byte-identical.
    """
    root = Path(data_root)
    if not root.is_dir():
        raise DuckDBCatalogCorrupt(f"data root is not a directory: {root}")
    output = Path(catalog_path)
    if output.exists() and not output.is_file():
        raise DuckDBCatalogPublishError(f"catalog output is not a file: {output}")
    blobs = _read_blobs(root)
    acquisitions = _read_acquisitions(root, {row["blob_sha256"] for row in blobs})
    projections = _read_projections(root)
    partitions = _read_partitions(root, {row["blob_sha256"] for row in blobs}, {row["projection_id"] for row in projections})
    quarantine = _read_quarantine(root)
    revisions = _read_revisions(
        root,
        {row["blob_sha256"] for row in blobs},
        {row["acquisition_id"] for row in acquisitions},
    )
    gaps = _read_gaps(partitions, acquisitions, quarantine)
    usage = _storage_usage(blobs, projections, partitions, quarantine)
    datasets = {
        "v_t0_blobs": blobs,
        "v_t0_acquisitions": acquisitions,
        "v_t0_projections": projections,
        "v_t0_partitions": partitions,
        "v_t0_gaps": gaps,
        "v_t0_revisions": revisions,
        "v_t0_quarantine": quarantine,
        "v_t0_storage_usage": usage,
    }
    counts = {name: len(rows) for name, rows in datasets.items()}
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    os.close(handle)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        con = duckdb.connect(str(temporary))
        try:
            con.execute("SET threads TO 2")
            con.execute("SET preserve_insertion_order = true")
            con.execute("SET enable_external_access = false")
            con.execute("BEGIN TRANSACTION")
            try:
                con.execute(
                    f"CREATE TABLE {_quote_ident('catalog_metadata')}"
                    " (schema_version VARCHAR, data_root_role VARCHAR)"
                )
                con.execute(
                    "INSERT INTO catalog_metadata VALUES (?, ?)",
                    [CATALOG_SCHEMA_VERSION, CATALOG_ROLE],
                )
                for name in VIEW_NAMES:
                    _create_table(con, name, datasets[name])
            except Exception:
                con.execute("ROLLBACK")
                raise
            con.execute("COMMIT")
        finally:
            con.close()
        _validate_database(temporary, counts)
        descriptor = os.open(temporary, os.O_RDWR)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, output)
        try:
            fd = os.open(output.parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError:
            pass
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    durable_files = sum(
        1
        for path in root.rglob("*")
        if path.is_file() and path.resolve() != output.resolve()
    )
    return DuckDBCatalogBuild(output, root, counts, durable_files)


def _validate_catalog_identity(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    """Refuse stale/mismatched catalogs at open time (I10R1 §7)."""
    try:
        metadata = con.execute(
            "SELECT schema_version, data_root_role FROM catalog_metadata"
        ).fetchall()
    except duckdb.Error as exc:
        raise DuckDBCatalogVersionError(
            f"discovery catalog {path} has no readable catalog_metadata: {exc}"
        ) from exc
    if len(metadata) != 1:
        raise DuckDBCatalogVersionError(
            f"discovery catalog {path} must carry exactly one metadata row, got {len(metadata)}"
        )
    schema_version, role = metadata[0]
    if schema_version != CATALOG_SCHEMA_VERSION:
        raise DuckDBCatalogVersionError(
            f"discovery catalog {path} schema_version {schema_version!r} != "
            f"expected {CATALOG_SCHEMA_VERSION!r} (no silent migration)"
        )
    if role != CATALOG_ROLE:
        raise DuckDBCatalogVersionError(
            f"discovery catalog {path} data_root_role {role!r} != expected {CATALOG_ROLE!r}"
        )


class ReadOnlyDuckDBCatalog:
    """Normal consumer query boundary; no mutable connection is exposed."""

    def __init__(self, catalog_path: str | Path) -> None:
        self.catalog_path = Path(catalog_path)
        if not self.catalog_path.is_file():
            raise DuckDBCatalogCorrupt(f"discovery catalog is missing: {self.catalog_path}")
        self._connection = duckdb.connect(str(self.catalog_path), read_only=True)
        try:
            _validate_catalog_identity(self._connection, self.catalog_path)
        except Exception:
            self._connection.close()
            raise

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> ReadOnlyDuckDBCatalog:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def query_view(self, view_name: str, sql: str | None = None) -> list[tuple[Any, ...]]:
        if sql is None:
            if view_name not in VIEW_NAMES:
                raise DuckDBCatalogError(f"unknown discovery view: {view_name}")
            sql = f"SELECT * FROM {view_name}"
        lowered = sql.lstrip().lower()
        if not lowered.startswith("select") or ";" in sql.rstrip(";"):
            raise DuckDBCatalogError("query API accepts one read-only SELECT statement")
        return self._connection.execute(sql).fetchall()

    def canonical_view_rows(self, view_name: str) -> list[list[Any]]:
        if view_name not in VIEW_NAMES:
            raise DuckDBCatalogError(f"unknown discovery view: {view_name}")
        columns = [row[1] for row in self._connection.execute(f"PRAGMA table_info('{view_name}')").fetchall()]
        order = ", ".join(f'"{column}"' for column in columns)
        return [list(row) for row in self._connection.execute(f"SELECT * FROM {view_name} ORDER BY {order}").fetchall()]


__all__ = [
    "CATALOG_ROLE",
    "CATALOG_SCHEMA_VERSION",
    "DuckDBCatalogBuild",
    "DuckDBCatalogCorrupt",
    "DuckDBCatalogError",
    "DuckDBCatalogPublishError",
    "DuckDBCatalogShapeCorrupt",
    "DuckDBCatalogVersionError",
    "ReadOnlyDuckDBCatalog",
    "VIEW_NAMES",
    "VIEW_NULLABLE_COLUMNS",
    "VIEW_SCHEMAS",
    "rebuild_duckdb_catalog",
]
