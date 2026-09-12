"""SENSOR-B4-I05B/I05R1C — immutable T0B projection writer, artifact catalog,
projection context catalog and the end-to-end publication service.

I05R1 repairs layered on the accepted I05 design:

- DURABLE CATALOGS: ``ProjectionArtifactRepository`` and the new
  ``ProjectionContextRepository`` persist through the shared
  ``DurableJsonCatalog`` primitive (I05R1 §4-§6) — staged write -> fsync ->
  reopen/verify -> no-clobber publish -> parent-dir fsync.  No direct
  ``write_text`` persistence of committed truth.  Corruption fails closed.
- SAFE PHYSICAL KEYS: hashed filenames; raw projection_id never touches the
  filesystem namespace; binding revalidated on reload.
- ARTIFACT PHYSICAL VERIFICATION (§22): ``commit`` may not accept arbitrary
  metadata.  Before first commit the physical projection_uri must resolve
  safely beneath root, the file must exist, its exact SHA-256 must equal
  ``projection_sha256``, the Parquet must open, row_count must agree, the
  registered schema must agree and the required T0 metadata columns must
  agree.  ``state=VALID`` is only accepted after that proof (§23).
- PROJECTION CONTEXT (§14): ``ProjectionCatalogRecord`` — an immutable
  repository-specific context record carrying the partition/provider/
  sensor/instrument/granularity/logical-date/schema/parser context that
  ``RawProjectionArtifact`` deliberately does not carry.  Storage catalog
  context, NOT T1 normalization.
- WRITER PRECONDITIONS (§28-§33): cheap deterministic inputs are validated
  BEFORE physical publication (projection id, source hashes, acquisition
  ids, identity strings, shard, quality flags, registered schema, exact
  native row-field contract, no caller-supplied ``_t0_*`` keys).
- T0BProjectionService (§42): earns the complete chain — verify T0A
  sources, verify usable acquisitions, resolve registered schema, write/
  verify/publish Parquet, commit artifact + context + lineage, validate
  with the production resolver.  STOP before manifests (I05 §46 step 10+
  is the manifest repository's job).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .atomic import (
    AtomicPublishTargetExists,
    ensure_durable_directory,
    fsync_directory,
    fsync_file,
    publish_no_replace,
)
from .checksums import sha256_file, validate_sha256_hex
from .json_catalog import (
    JsonCatalogCorrupt,
    DurableJsonCatalog,
)
from .models import RawProjectionArtifact
from .paths import projection_object_key, resolve_under_root
from .projection_schema import (
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
    T0_METADATA_SCHEMA,
)
from ..providers.base.enums import QualityFlagAcquisition

# ---------------------------------------------------------------------------
# T0B metadata columns injected by the projection layer (names only).
# The FULL canonical schema lives in projection_schema.T0_METADATA_SCHEMA.
# ---------------------------------------------------------------------------

T0_PROJECTION_METADATA_COLUMNS: list[str] = [
    field.name for field in T0_METADATA_SCHEMA
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ProjectionWriteError(RuntimeError):
    """Base class for projection write failures."""


class ProjectionSchemaMismatch(ProjectionWriteError):
    """Provided table does not match the registered provider-native schema."""


class ProjectionSchemaNotFound(ProjectionWriteError):
    """The schema is not registered in the ProjectionSchemaRegistry (§30)."""


class ProjectionIdentityConflict(ProjectionWriteError):
    """Same projection_id committed with different bytes/lineage/schema."""

    def __init__(self, projection_id: str) -> None:
        self.projection_id = projection_id
        super().__init__(
            f"projection_id={projection_id!r} already committed with "
            "different artifact content"
        )


class ProjectionIntegrityError(ProjectionWriteError):
    """Physical projection file fails integrity verification."""


class ProjectionCorruption(ProjectionIntegrityError):
    """Committed projection SHA or Parquet structure fails verification."""


class ProjectionArtifactCatalogCorrupt(ProjectionWriteError):
    """A committed artifact/context catalog fragment is corrupt (fail closed)."""


class ProjectionPreconditionError(ProjectionWriteError):
    """A cheap deterministic caller input failed pre-publication validation."""


class ProjectionSourceNotUsable(ProjectionWriteError):
    """A selected source acquisition is not usable manifest provenance."""


# ---------------------------------------------------------------------------
# ProjectionCatalogRecord (I05R1 §14) — immutable projection context
# ---------------------------------------------------------------------------


def _canonical_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


class ProjectionCatalogRecord:
    """Immutable storage-catalog context for one committed projection.

    This is repository catalog context (NOT a rename of, and NOT a
    replacement for, the frozen ``RawProjectionArtifact`` model and NOT T1
    normalization).  It carries the fields needed to validate a
    PartitionManifest projection_ref that the artifact model intentionally
    does not carry.
    """

    __slots__ = (
        "projection_id",
        "provider",
        "venue",
        "sensor_family",
        "native_instrument",
        "source_granularity",
        "partition_key",
        "logical_date_start",
        "logical_date_end",
        "projection_schema_id",
        "projection_schema_version",
        "schema_key",
        "schema_fingerprint",
        "parser_version",
        "projection_uri",
        "projection_sha256",
        "row_count",
        "min_provider_time",
        "max_provider_time",
        "lineage_manifest_id",
        "quality_flags",
        "created_at",
    )

    def __init__(
        self,
        *,
        projection_id: str,
        provider: str,
        venue: str,
        sensor_family: str,
        native_instrument: str,
        source_granularity: str | None,
        partition_key: str,
        logical_date_start: datetime,
        logical_date_end: datetime,
        projection_schema_id: str,
        projection_schema_version: str,
        schema_key: str,
        schema_fingerprint: str,
        parser_version: str,
        projection_uri: str,
        projection_sha256: str,
        row_count: int,
        min_provider_time: datetime | None,
        max_provider_time: datetime | None,
        lineage_manifest_id: str,
        quality_flags: list[str],
        created_at: datetime,
    ) -> None:
        if not isinstance(projection_id, str) or not projection_id:
            raise ProjectionPreconditionError("projection_id must be nonempty")
        for name, value in (
            ("provider", provider),
            ("venue", venue),
            ("sensor_family", sensor_family),
            ("native_instrument", native_instrument),
            ("partition_key", partition_key),
            ("projection_schema_id", projection_schema_id),
            ("parser_version", parser_version),
            ("projection_uri", projection_uri),
            ("lineage_manifest_id", lineage_manifest_id),
        ):
            if not isinstance(value, str) or not value:
                raise ProjectionPreconditionError(
                    f"{name} must be a nonempty string"
                )
        if logical_date_end < logical_date_start:
            raise ProjectionPreconditionError(
                "logical_date_end must be >= logical_date_start"
            )
        self.projection_id = projection_id
        self.provider = provider
        self.venue = venue
        self.sensor_family = sensor_family
        self.native_instrument = native_instrument
        self.source_granularity = source_granularity
        self.partition_key = partition_key
        self.logical_date_start = logical_date_start
        self.logical_date_end = logical_date_end
        self.projection_schema_id = projection_schema_id
        self.projection_schema_version = projection_schema_version
        self.schema_key = schema_key
        self.schema_fingerprint = schema_fingerprint
        self.parser_version = parser_version
        self.projection_uri = projection_uri
        self.projection_sha256 = projection_sha256
        self.row_count = row_count
        self.min_provider_time = min_provider_time
        self.max_provider_time = max_provider_time
        self.lineage_manifest_id = lineage_manifest_id
        self.quality_flags = list(quality_flags)
        self.created_at = created_at

    # -- serialization -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_type": "projection_context",
            "projection_id": self.projection_id,
            "provider": self.provider,
            "venue": self.venue,
            "sensor_family": self.sensor_family,
            "native_instrument": self.native_instrument,
            "source_granularity": self.source_granularity,
            "partition_key": self.partition_key,
            "logical_date_start": _canonical_utc(self.logical_date_start),
            "logical_date_end": _canonical_utc(self.logical_date_end),
            "projection_schema_id": self.projection_schema_id,
            "projection_schema_version": self.projection_schema_version,
            "schema_key": self.schema_key,
            "schema_fingerprint": self.schema_fingerprint,
            "parser_version": self.parser_version,
            "projection_uri": self.projection_uri,
            "projection_sha256": self.projection_sha256,
            "row_count": self.row_count,
            "min_provider_time": _canonical_utc(self.min_provider_time),
            "max_provider_time": _canonical_utc(self.max_provider_time),
            "lineage_manifest_id": self.lineage_manifest_id,
            "quality_flags": list(self.quality_flags),
            "created_at": _canonical_utc(self.created_at),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ProjectionCatalogRecord:
        if payload.get("record_type") != "projection_context":
            raise ProjectionArtifactCatalogCorrupt(
                "projection context fragment has wrong record_type"
            )

        def _dt(field: str) -> datetime:
            raw = payload.get(field)
            if raw is None:
                raise ProjectionArtifactCatalogCorrupt(
                    f"projection context missing {field}"
                )
            return datetime.fromisoformat(raw)

        return cls(
            projection_id=payload["projection_id"],
            provider=payload["provider"],
            venue=payload["venue"],
            sensor_family=payload["sensor_family"],
            native_instrument=payload["native_instrument"],
            source_granularity=payload.get("source_granularity"),
            partition_key=payload["partition_key"],
            logical_date_start=_dt("logical_date_start"),
            logical_date_end=_dt("logical_date_end"),
            projection_schema_id=payload["projection_schema_id"],
            projection_schema_version=payload["projection_schema_version"],
            schema_key=payload["schema_key"],
            schema_fingerprint=payload["schema_fingerprint"],
            parser_version=payload["parser_version"],
            projection_uri=payload["projection_uri"],
            projection_sha256=payload["projection_sha256"],
            row_count=payload["row_count"],
            min_provider_time=(
                datetime.fromisoformat(payload["min_provider_time"])
                if payload.get("min_provider_time")
                else None
            ),
            max_provider_time=(
                datetime.fromisoformat(payload["max_provider_time"])
                if payload.get("max_provider_time")
                else None
            ),
            lineage_manifest_id=payload["lineage_manifest_id"],
            quality_flags=list(payload.get("quality_flags", [])),
            created_at=_dt("created_at"),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProjectionCatalogRecord):
            return NotImplemented
        return self.to_dict() == other.to_dict()


# ---------------------------------------------------------------------------
# Internal: inject T0 metadata columns into rows (§24-§27)
# ---------------------------------------------------------------------------


class RowProjectionLineage:
    """Optional defensible row-level source attribution (I05R1 §27).

    Each pair is validated against the committed file-level lineage set; a
    row may never reference undeclared source evidence.  Row-lineage data
    may not travel inside provider-native row dicts.
    """

    __slots__ = ("row_ordinal", "source_blob_sha256", "source_acquisition_id")

    def __init__(
        self,
        row_ordinal: int,
        source_blob_sha256: str,
        source_acquisition_id: str,
    ) -> None:
        if not isinstance(row_ordinal, int) or isinstance(row_ordinal, bool):
            raise ProjectionPreconditionError(
                "RowProjectionLineage.row_ordinal must be an int"
            )
        if row_ordinal < 0:
            raise ProjectionPreconditionError(
                "RowProjectionLineage.row_ordinal must be >= 0"
            )
        validate_sha256_hex(source_blob_sha256)
        if not isinstance(source_acquisition_id, str) or not source_acquisition_id:
            raise ProjectionPreconditionError(
                "RowProjectionLineage.source_acquisition_id must be nonempty"
            )
        self.row_ordinal = row_ordinal
        self.source_blob_sha256 = source_blob_sha256
        self.source_acquisition_id = source_acquisition_id


def _validate_no_reserved_keys(rows: list[dict[str, Any]]) -> None:
    """Provider-native rows must never supply ``_t0_*`` keys (I05R1 §24)."""
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ProjectionPreconditionError(
                f"row {index} is not a mapping"
            )
        for key in row:
            if isinstance(key, str) and key.startswith("_t0_"):
                raise ProjectionPreconditionError(
                    f"row {index} supplies reserved T0 metadata key {key!r}; "
                    "T0 metadata belongs exclusively to the projection layer"
                )


def _inject_t0_metadata(
    rows: list[dict[str, Any]],
    *,
    projection_id: str,
    provider: str,
    venue: str,
    sensor_family: str,
    native_instrument: str,
    parser_version: str,
    schema_version: str,
    source_blob_sha256: list[str],
    acquisition_ids: list[str],
    row_lineage: list[RowProjectionLineage] | None,
) -> list[dict[str, Any]]:
    """Inject required _t0_* metadata into every row.

    Ownership (I05R1 §24-§26): callers may never supply _t0_* fields; the
    layer overwrites by construction.  Single source -> exact per-row
    attribution; multi-source -> NULL unless defensible row lineage is
    supplied through the separate typed argument.
    """
    single = len(source_blob_sha256) == 1 and len(acquisition_ids) == 1
    by_ordinal: dict[int, RowProjectionLineage] = {}
    if row_lineage:
        for rl in row_lineage:
            if rl.row_ordinal in by_ordinal:
                raise ProjectionPreconditionError(
                    f"duplicate RowProjectionLineage for row "
                    f"{rl.row_ordinal}"
                )
            by_ordinal[rl.row_ordinal] = rl

    enriched: list[dict[str, Any]] = []
    for ordinal, row in enumerate(rows):
        out = dict(row)
        out["_t0_projection_id"] = projection_id
        out["_t0_provider"] = provider
        out["_t0_venue"] = venue
        out["_t0_sensor_family"] = sensor_family
        out["_t0_native_instrument"] = native_instrument
        out["_t0_parser_version"] = parser_version
        out["_t0_schema_version"] = schema_version
        out["_t0_row_ordinal"] = ordinal
        if single:
            out["_t0_source_blob_sha256"] = source_blob_sha256[0]
            out["_t0_acquisition_id"] = acquisition_ids[0]
        elif ordinal in by_ordinal:
            rl = by_ordinal[ordinal]
            out["_t0_source_blob_sha256"] = rl.source_blob_sha256
            out["_t0_acquisition_id"] = rl.source_acquisition_id
        else:
            out["_t0_source_blob_sha256"] = None
            out["_t0_acquisition_id"] = None
        enriched.append(out)
    return enriched


# ---------------------------------------------------------------------------
# write_projection
# ---------------------------------------------------------------------------


def write_projection(
    *,
    root: Path,
    rows: list[dict[str, Any]],
    schema_definition: ProjectionSchemaDefinition,
    schema_registry: ProjectionSchemaRegistry | None = None,
    projection_id: str,
    source_blob_sha256: list[str],
    acquisition_ids: list[str],
    provider: str,
    venue: str,
    sensor_family: str,
    native_instrument: str,
    native_granularity: str,
    parser_version: str,
    partition_key: str,
    logical_year: int,
    logical_month: int,
    logical_day: int,
    shard_id: int = 0,
    min_provider_time: datetime | None = None,
    max_provider_time: datetime | None = None,
    quality_flags: list[str | QualityFlagAcquisition] | None = None,
    row_lineage: list[RowProjectionLineage] | None = None,
) -> tuple[RawProjectionArtifact, Path]:
    """Write a T0B Parquet projection with full staging/durability pipeline.

    Pipeline (I05 §37, preconditions hardened per I05R1 §28-§33):
    0. Validate ALL cheap deterministic inputs BEFORE physical publication
    1. Build explicit Arrow Table with injected _t0_* metadata columns
    2. Validate against the registered provider-native schema
    3. Write staged Parquet
    4. Flush + fsync staged
    5. Reopen staged Parquet, verify full schema + T0 constants + row count
       + row ordinals + row lineage
    6. Compute SHA-256 of exact stored Parquet bytes
    7. Derive final projection_object_key()
    8. No-clobber publish (idempotent reuse only on identical bytes)
    9. Parent-directory fsync
    """
    # ---- 0. Cheap deterministic precondition validation (§28) -------------
    if not isinstance(projection_id, str) or not projection_id:
        raise ProjectionPreconditionError("projection_id must be nonempty")
    if "\x00" in projection_id or "/" in projection_id or "\\" in projection_id:
        raise ProjectionPreconditionError(
            "projection_id must not contain path-structural characters"
        )
    if not rows:
        raise ProjectionWriteError("projection must contain at least one row")
    if not isinstance(source_blob_sha256, list) or not source_blob_sha256:
        raise ProjectionPreconditionError(
            "source_blob_sha256 must be a nonempty list"
        )
    seen: set[str] = set()
    for sha in source_blob_sha256:
        try:
            validate_sha256_hex(sha)
        except ValueError as exc:
            raise ProjectionPreconditionError(
                f"source_blob_sha256 malformed: {sha!r}"
            ) from exc
        if sha in seen:
            raise ProjectionPreconditionError(
                f"duplicate source_blob_sha256 {sha!r}"
            )
        seen.add(sha)
    if not isinstance(acquisition_ids, list) or len(acquisition_ids) != len(
        source_blob_sha256
    ):
        raise ProjectionPreconditionError(
            "acquisition_ids must be a list parallel to source_blob_sha256"
        )
    for acq_id in acquisition_ids:
        if not isinstance(acq_id, str) or not acq_id:
            raise ProjectionPreconditionError(
                "every acquisition_id must be a nonempty string"
            )
    for name, value in (
        ("provider", provider),
        ("venue", venue),
        ("sensor_family", sensor_family),
        ("native_instrument", native_instrument),
        ("native_granularity", native_granularity),
        ("parser_version", parser_version),
        ("partition_key", partition_key),
    ):
        if not isinstance(value, str) or not value:
            raise ProjectionPreconditionError(f"{name} must be nonempty")
    if not isinstance(shard_id, int) or isinstance(shard_id, bool) or shard_id < 0:
        raise ProjectionPreconditionError(
            "shard_id must be a nonnegative int"
        )
    declared_pairs = set(zip(source_blob_sha256, acquisition_ids))
    if row_lineage is not None:
        for rl in row_lineage:
            if (rl.source_blob_sha256, rl.source_acquisition_id) not in declared_pairs:
                raise ProjectionPreconditionError(
                    f"row lineage for row {rl.row_ordinal} references "
                    f"undeclared source pair ({rl.source_blob_sha256!r}, "
                    f"{rl.source_acquisition_id!r}); a row may never point "
                    "outside the committed file-level lineage set"
                )
            if len(source_blob_sha256) == 1 and rl.source_blob_sha256 != source_blob_sha256[0]:
                raise ProjectionPreconditionError(
                    "row lineage references a blob outside the single "
                    "declared source"
                )

    # Quality flags BEFORE physical publication (§29): accept the enum or
    # its exact string value; anything else fails closed here.
    normalized_flags: list[str] = []
    for flag in quality_flags or []:
        if isinstance(flag, QualityFlagAcquisition):
            normalized_flags.append(flag.value)
        elif isinstance(flag, str):
            try:
                normalized_flags.append(QualityFlagAcquisition(flag).value)
            except ValueError as exc:
                raise ProjectionPreconditionError(
                    f"invalid quality flag {flag!r}"
                ) from exc
        else:
            raise ProjectionPreconditionError(
                f"quality flag must be QualityFlagAcquisition or str, "
                f"got {type(flag).__name__}"
            )

    # Registered-schema gate (§30): an in-memory definition is not
    # sufficient authority; the registry must contain the exact fingerprint.
    if schema_registry is None:
        raise ProjectionPreconditionError(
            "schema_registry is required — schemas must be registered "
            "before physical publication"
        )
    try:
        registered = schema_registry.resolve(schema_definition.schema_key)
    except Exception as exc:  # ProjectionSchemaNotFound (KeyError subclass)
        raise ProjectionSchemaNotFound(
            f"projection schema {schema_definition.schema_identity!r} is not "
            "registered; physical publication refused"
        ) from exc
    if registered.schema_fingerprint != schema_definition.schema_fingerprint:
        raise ProjectionSchemaMismatch(
            "supplied schema definition does not match the registered "
            "structural fingerprint"
        )

    # No caller-supplied _t0_* keys (§24) — before any physical work.
    _validate_no_reserved_keys(rows)

    # Exact native row-field contract (§31): the row key set must be
    # EXACTLY the registered provider-native field set.
    native_names = {f.name for f in schema_definition.provider_native_schema}
    for index, row in enumerate(rows):
        keys = set(row.keys())
        unknown = keys - native_names
        if unknown:
            raise ProjectionSchemaMismatch(
                f"row {index} carries unknown provider-native field(s) "
                f"{sorted(unknown)}; silent Arrow inference is forbidden"
            )
        for field in schema_definition.provider_native_schema:
            if field.name not in keys:
                if field.nullable:
                    continue  # nullable missing field may become null
                raise ProjectionSchemaMismatch(
                    f"row {index} missing non-nullable field "
                    f"{field.name!r}"
                )

    # ---- 1. Inject T0 metadata --------------------------------------------
    enriched = _inject_t0_metadata(
        rows,
        projection_id=projection_id,
        provider=provider,
        venue=venue,
        sensor_family=sensor_family,
        native_instrument=native_instrument,
        parser_version=parser_version,
        schema_version=schema_definition.projection_schema_version,
        source_blob_sha256=source_blob_sha256,
        acquisition_ids=acquisition_ids,
        row_lineage=row_lineage,
    )

    # ---- 2. Build explicit Arrow Table ------------------------------------
    full_schema = pa.schema(
        list(schema_definition.provider_native_schema) + list(T0_METADATA_SCHEMA)
    )
    try:
        table = pa.Table.from_pylist(enriched, schema=full_schema)
    except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
        raise ProjectionSchemaMismatch(
            f"failed to build Arrow Table from rows (no lossy coercion): {exc}"
        ) from exc
    if not table.schema.equals(full_schema, check_metadata=False):
        raise ProjectionSchemaMismatch(
            f"table schema mismatch: expected {full_schema}, got {table.schema}"
        )

    # ---- 3. Staging + write ------------------------------------------------
    # Staging at root level (same filesystem) to stay within Windows MAX_PATH
    # when the final path includes deep provider/venue/schema directories.
    staging_dir = root / "_staging"
    ensure_durable_directory(staging_dir)
    staged = staging_dir / f"{uuid.uuid4().hex}.parquet"

    try:
        pq.write_table(table, str(staged))

        # ---- 4. Flush + fsync ---------------------------------------------
        fsync_file(staged)

        # ---- 5. Reopen and verify staged Parquet (§33) --------------------
        reread = pq.read_table(str(staged))
        if reread.num_rows != len(enriched):
            raise ProjectionIntegrityError(
                f"staged projection row count {reread.num_rows} != expected "
                f"{len(enriched)}"
            )
        if not reread.schema.equals(full_schema, check_metadata=False):
            raise ProjectionIntegrityError(
                "staged Parquet schema does not match the projected schema"
            )
        ordinals = reread.column("_t0_row_ordinal").to_pylist()
        if ordinals != list(range(len(enriched))):
            raise ProjectionIntegrityError(
                f"row ordinals not contiguous 0..{len(enriched)-1}"
            )
        # T0 constants (§33): projection/provider/venue/sensor/instrument/
        # parser/schema_version identical on EVERY row.
        for column, expected in (
            ("_t0_projection_id", projection_id),
            ("_t0_provider", provider),
            ("_t0_venue", venue),
            ("_t0_sensor_family", sensor_family),
            ("_t0_native_instrument", native_instrument),
            ("_t0_parser_version", parser_version),
            ("_t0_schema_version", schema_definition.projection_schema_version),
        ):
            values = set(reread.column(column).to_pylist())
            if values != {expected}:
                raise ProjectionIntegrityError(
                    f"staged T0 column {column} is not constant "
                    f"{expected!r}: {values!r}"
                )
        # Row lineage (§33): single-source exact; multi-source non-null
        # pairs must belong to the declared lineage set.
        declared_pairs = set(zip(source_blob_sha256, acquisition_ids))
        row_blobs = reread.column("_t0_source_blob_sha256").to_pylist()
        row_acqs = reread.column("_t0_acquisition_id").to_pylist()
        if len(source_blob_sha256) == 1:
            if set(row_blobs) != {source_blob_sha256[0]} or set(row_acqs) != {
                acquisition_ids[0]
            }:
                raise ProjectionIntegrityError(
                    "single-source row lineage is not exact on every row"
                )
        else:
            for i, (b, a) in enumerate(zip(row_blobs, row_acqs)):
                if b is None:
                    continue  # NULL is allowed when attribution is not defensible
                if (b, a) not in declared_pairs:
                    raise ProjectionIntegrityError(
                        f"row {i} references undeclared source pair "
                        f"({b!r}, {a!r})"
                    )

        # ---- 6. SHA of exact stored bytes ---------------------------------
        digest = sha256_file(str(staged))
        projection_sha256 = digest.hex_digest

        # ---- 7. Final projection key --------------------------------------
        key = projection_object_key(
            provider=provider,
            venue=venue,
            sensor_family=sensor_family,
            native_instrument=native_instrument,
            native_granularity=native_granularity,
            year=logical_year,
            month=logical_month,
            day=logical_day,
            schema_key=schema_definition.schema_key,
            shard_id=shard_id,
            projection_sha256=projection_sha256,
        )
        final = root / key
        ensure_durable_directory(final.parent)

        # ---- 8. No-clobber publish ----------------------------------------
        try:
            publish_no_replace(staged, final)
        except (FileExistsError, AtomicPublishTargetExists):
            # Idempotent: verify the existing object is byte-identical.
            existing_digest = sha256_file(str(final))
            if existing_digest.hex_digest != projection_sha256:
                raise ProjectionIdentityConflict(projection_id) from None

        # ---- 9. Parent-directory fsync ------------------------------------
        fsync_directory(final.parent)

        artifact = RawProjectionArtifact(
            projection_id=projection_id,
            source_blob_sha256=source_blob_sha256,
            projection_schema_id=schema_definition.projection_schema_id,
            projection_schema_version=schema_definition.projection_schema_version,
            parser_version=parser_version,
            row_count=reread.num_rows,
            min_provider_time=min_provider_time,
            max_provider_time=max_provider_time,
            partition_key=partition_key,
            projection_uri=key,
            projection_sha256=projection_sha256,
            quality_flags=[
                QualityFlagAcquisition(f) for f in normalized_flags
            ],
        )

        return artifact, final

    finally:
        try:
            if staged.exists():
                staged.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Projection artifact repository (durable, verifying, immutable)
# ---------------------------------------------------------------------------

# Fields compared for artifact idempotence (I05R1 §21) — ALL immutable
# semantic fields of RawProjectionArtifact.
_ARTIFACT_IDEMPOTENCE_FIELDS = (
    "projection_sha256",
    "source_blob_sha256",
    "projection_schema_id",
    "projection_schema_version",
    "parser_version",
    "row_count",
    "min_provider_time",
    "max_provider_time",
    "partition_key",
    "projection_uri",
    "quality_flags",
    "state",
)


def _artifact_payload(artifact: RawProjectionArtifact) -> dict[str, Any]:
    """Language-neutral canonical payload for one artifact fragment."""
    payload = json.loads(artifact.model_dump_json())
    payload["record_type"] = "projection_artifact"
    return payload


class ProjectionArtifactRepository:
    """Immutable, durable, physically-verifying RawProjectionArtifact catalog.

    Persisted under ``<t0_root>/catalogs/manifests/projections/`` through the
    shared ``DurableJsonCatalog`` primitive: hashed physical keys, staged
    fsync'd writes, no-clobber publish, corruption fail-closed.

    I05R2 §4-§7: a commit-capable repository has NO verification bypass.
    ``projection_root`` and ``schema_registry`` are MANDATORY constructor
    dependencies; the historical ``verify_physical=False`` metadata-only
    persistence path is removed.  Unit tests that only need artifact
    metadata use ``RawProjectionArtifact`` directly — never this writer as
    an unverified metadata sink.

    Commit gates (I05R1 §21-§23 + I05R2 §7):

    - the physical projection_uri must resolve safely beneath root;
    - the file must exist and its exact SHA-256 must equal
      ``projection_sha256``;
    - the Parquet must open; ``row_count`` must agree;
    - the physical schema must EXACTLY equal the registered
      ``provider_native_schema`` + ``T0_METADATA_SCHEMA`` (I05R2 §15-§17:
      field order, names, Arrow types, nullability, nested structure —
      a name-only proof is not a schema proof);
    - ``state=VALID`` is accepted only after that physical + schema proof;
    - idempotence compares ALL immutable semantic fields and RE-VERIFIES
      the physical truth for VALID artifacts on every idempotent commit
      (I05R2 §8 — no success claimed from stale cache).
    """

    def __init__(
        self,
        catalog_root: Path,
        *,
        projection_root: Path,
        schema_registry: ProjectionSchemaRegistry,
    ) -> None:
        self._root = Path(catalog_root)
        self._projection_root = Path(projection_root)
        self._schema_registry = schema_registry
        try:
            self._catalog = DurableJsonCatalog(
                self._root, logical_id_field="projection_id"
            )
        except JsonCatalogCorrupt as exc:
            raise ProjectionArtifactCatalogCorrupt(str(exc)) from exc
        self._cache: dict[str, RawProjectionArtifact] = {}
        self._load_all()

    # -- loading -------------------------------------------------------------

    def _parse_payload(self, payload: dict[str, Any]) -> RawProjectionArtifact:
        if payload.get("record_type") != "projection_artifact":
            raise ProjectionArtifactCatalogCorrupt(
                "projection artifact fragment has wrong record_type"
            )
        try:
            return RawProjectionArtifact(**{
                k: v for k, v in payload.items() if k != "record_type"
            })
        except Exception as exc:
            raise ProjectionArtifactCatalogCorrupt(
                f"projection artifact fragment is corrupt: {exc}"
            ) from exc

    def _load_all(self) -> None:
        for logical_id in self._catalog.list_ids():
            payload = self._catalog.get(logical_id)
            assert payload is not None  # catalog invariant
            self._cache[logical_id] = self._parse_payload(payload)

    # -- physical verification (§22) ------------------------------------------

    def _verify_physical_projection(self, artifact: RawProjectionArtifact) -> None:
        """Prove the stored physical T0B bytes (I05R1 §22 + I05R2 §15-§17).

        No bypass: the caller-supplied schema is not authority — the
        REGISTERED schema (by id/version) plus the canonical T0 metadata
        schema must EXACTLY equal the physical Parquet schema.
        """
        if artifact.state.name != "VALID":
            return  # only VALID claims require physical proof
        from .checksums import validate_sha256_hex

        try:
            validate_sha256_hex(artifact.projection_sha256)
        except ValueError as exc:
            raise ProjectionCorruption(
                f"artifact projection_sha256 malformed: {exc}"
            ) from exc
        try:
            path = resolve_under_root(
                self._projection_root, artifact.projection_uri
            )
        except ValueError as exc:
            raise ProjectionCorruption(
                f"projection_uri does not resolve safely beneath root: {exc}"
            ) from exc
        if not path.is_file():
            raise ProjectionCorruption(
                f"physical projection missing at {path!s}; metadata without "
                "physical evidence is not a committed projection artifact"
            )
        actual = sha256_file(str(path)).hex_digest
        if actual != artifact.projection_sha256:
            raise ProjectionCorruption(
                f"physical projection SHA {actual} != committed "
                f"{artifact.projection_sha256}"
            )
        # Read the FILE's own Arrow schema via ParquetFile: pq.read_table()
        # performs dataset discovery and would append Hive partition columns
        # (provider=/venue=/...) inferred from the physical directory layout,
        # which are NOT part of the stored schema contract.
        table = pq.ParquetFile(str(path)).read()
        if table.num_rows != artifact.row_count:
            raise ProjectionCorruption(
                f"physical row count {table.num_rows} != committed "
                f"{artifact.row_count}"
            )
        # Registered schema agreement — MANDATORY (I05R2 §15-§17): the
        # physical schema must EXACTLY equal registered provider-native
        # schema + T0_METADATA_SCHEMA.  Exact structural equality covers
        # field order, names, Arrow types (incl. nested children, decimal
        # precision/scale, timestamp units/timezones) and nullability —
        # it subsumes the per-column T0 type and native-name checks of
        # I05R1 with a single authoritative proof.
        try:
            registered = self._schema_registry.resolve_by_id(
                artifact.projection_schema_id,
                artifact.projection_schema_version,
            )
        except Exception as exc:
            raise ProjectionCorruption(
                "artifact references an unregistered projection schema: "
                f"{artifact.projection_schema_id!r} @ "
                f"{artifact.projection_schema_version!r}"
            ) from exc
        expected_full_schema = pa.schema(
            list(registered.provider_native_schema) + list(T0_METADATA_SCHEMA)
        )
        if not table.schema.equals(expected_full_schema, check_metadata=False):
            raise ProjectionCorruption(
                "physical projection schema does not EXACTLY equal the "
                f"registered schema {artifact.projection_schema_id!r} @ "
                f"{artifact.projection_schema_version!r}: expected "
                f"{expected_full_schema}, got {table.schema}"
            )

    # -- commit ---------------------------------------------------------------

    def commit(self, artifact: RawProjectionArtifact) -> RawProjectionArtifact:
        """Commit one immutable artifact record (idempotent or conflict).

        I05R2 §8: idempotent reuse is NEVER claimed from stale cache —
        after the immutable-field comparison, a VALID artifact re-runs the
        full physical verification so corruption since startup fails
        instead of silently succeeding.
        """
        pid = artifact.projection_id
        if pid in self._cache:
            existing = self._cache[pid]
            # Idempotence over ALL immutable semantic fields (§21).
            for field in _ARTIFACT_IDEMPOTENCE_FIELDS:
                if getattr(existing, field) != getattr(artifact, field):
                    raise ProjectionIdentityConflict(pid)
            # I05R2 §8: re-verify physical truth NOW (the writer validated
            # it once; that history is not a current integrity proof).
            self._verify_physical_projection(existing)
            return existing

        # Physical verification BEFORE first commit (§22) — VALID is earned.
        self._verify_physical_projection(artifact)

        try:
            self._catalog.commit(pid, _artifact_payload(artifact))
        except JsonCatalogCorrupt as exc:
            raise ProjectionArtifactCatalogCorrupt(str(exc)) from exc
        self._cache[pid] = artifact
        return artifact

    # -- reads ----------------------------------------------------------------

    def get(self, projection_id: str) -> RawProjectionArtifact | None:
        """Retrieve a projection artifact by ID, or None."""
        return self._cache.get(projection_id)

    def verify_physical(self, projection_id: str) -> None:
        """Re-prove the physical T0B bytes NOW (I05R3 §10/§13).

        The writer validated the file once at commit; that history is not
        a current integrity proof.  Raises ``ProjectionCorruption`` if the
        stored bytes no longer satisfy the committed artifact identity.
        """
        artifact = self._cache.get(projection_id)
        if artifact is None:
            raise ProjectionCorruption(
                f"projection_id={projection_id!r} has no committed "
                "RawProjectionArtifact to verify"
            )
        self._verify_physical_projection(artifact)

    def get_strict(self, projection_id: str) -> RawProjectionArtifact:
        """Typed NotFound variant of :meth:`get`."""
        artifact = self._cache.get(projection_id)
        if artifact is None:
            raise KeyError(
                f"no committed RawProjectionArtifact for projection_id "
                f"{projection_id!r}"
            )
        return artifact

    def has(self, projection_id: str) -> bool:
        return projection_id in self._cache

    def list_ids(self) -> list[str]:
        return sorted(self._cache.keys())


# ---------------------------------------------------------------------------
# Projection context repository (I05R1 §14)
# ---------------------------------------------------------------------------


class ProjectionContextRepository:
    """Immutable durable catalog of ProjectionCatalogRecord context records.

    Persisted under ``<t0_root>/catalogs/manifests/projection_context/`` via
    the shared durable primitive.  Logical ID = projection_id; the record
    binds to the artifact by construction (same SHA/URI/row_count).
    """

    def __init__(self, catalog_root: Path) -> None:
        self._root = Path(catalog_root)
        try:
            self._catalog = DurableJsonCatalog(
                self._root, logical_id_field="projection_id"
            )
        except JsonCatalogCorrupt as exc:
            raise ProjectionArtifactCatalogCorrupt(str(exc)) from exc
        self._cache: dict[str, ProjectionCatalogRecord] = {}
        self._load_all()

    def _load_all(self) -> None:
        for logical_id in self._catalog.list_ids():
            payload = self._catalog.get(logical_id)
            assert payload is not None
            try:
                self._cache[logical_id] = ProjectionCatalogRecord.from_dict(payload)
            except ProjectionArtifactCatalogCorrupt:
                raise
            except Exception as exc:
                raise ProjectionArtifactCatalogCorrupt(
                    f"projection context fragment corrupt: {exc}"
                ) from exc

    def commit(self, record: ProjectionCatalogRecord) -> ProjectionCatalogRecord:
        if record.projection_id in self._cache:
            if self._cache[record.projection_id] != record:
                raise ProjectionIdentityConflict(record.projection_id)
            return self._cache[record.projection_id]
        try:
            self._catalog.commit(record.projection_id, record.to_dict())
        except JsonCatalogCorrupt as exc:
            raise ProjectionArtifactCatalogCorrupt(str(exc)) from exc
        self._cache[record.projection_id] = record
        return record

    def get(self, projection_id: str) -> ProjectionCatalogRecord | None:
        return self._cache.get(projection_id)

    def get_strict(self, projection_id: str) -> ProjectionCatalogRecord:
        record = self._cache.get(projection_id)
        if record is None:
            raise KeyError(
                f"no committed ProjectionCatalogRecord for projection_id "
                f"{projection_id!r}"
            )
        return record

    def has(self, projection_id: str) -> bool:
        return projection_id in self._cache

    def list_ids(self) -> list[str]:
        return sorted(self._cache.keys())


# ---------------------------------------------------------------------------
# T0BProjectionService (I05R1 §42) — end-to-end orchestration
# ---------------------------------------------------------------------------


class T0BProjectionService:
    """Earns the complete T0A -> T0B transition, in the frozen order.

    1. resolve/verify selected T0A blobs (durable metadata + physical)
    2. resolve/verify selected usable acquisitions
    3. resolve registered projection schema
    4. validate provider/native context
    5. validate all caller inputs (inside write_projection)
    6. write/verify/publish physical Parquet
    7. commit RawProjectionArtifact metadata
    8. commit ProjectionCatalogRecord context
    9. commit complete ProjectionLineage
    10. STOP — manifest publication is a separate, later step (I05 §46).
    """

    def __init__(
        self,
        *,
        root: Path,
        blob_store: Any,
        blob_metadata_repository: Any,
        acquisition_repository: Any,
        schema_registry: ProjectionSchemaRegistry,
        artifact_repository: ProjectionArtifactRepository,
        context_repository: ProjectionContextRepository,
        lineage_repository: Any,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        # I05R2 §29: the service only accepts SEALED, commit-capable
        # repositories.  A non-verifying artifact writer or a lineage
        # repository without its mandatory proof dependencies cannot be
        # constructed since I05R2; assert the invariant explicitly so a
        # partial future regression fails immediately at construction.
        if getattr(artifact_repository, "_projection_root", None) is None:
            raise ProjectionPreconditionError(
                "T0BProjectionService requires a sealed "
                "ProjectionArtifactRepository with a mandatory "
                "projection_root"
            )
        if getattr(artifact_repository, "_schema_registry", None) is None:
            raise ProjectionPreconditionError(
                "T0BProjectionService requires a sealed "
                "ProjectionArtifactRepository with a mandatory "
                "schema_registry"
            )
        for dep in (
            "_blob_store",
            "_blob_metadata_repository",
            "_acquisitions",
            "_artifact_repository",
            "_context_repository",
        ):
            if getattr(lineage_repository, dep, None) is None:
                raise ProjectionPreconditionError(
                    "T0BProjectionService requires a sealed "
                    "ProjectionLineageRepository with ALL mandatory "
                    f"dependencies (missing: {dep})"
                )
        self._root = Path(root)
        self._blob_store = blob_store
        self._blob_metadata_repository = blob_metadata_repository
        self._acquisitions = acquisition_repository
        self._schemas = schema_registry
        self._artifacts = artifact_repository
        self._contexts = context_repository
        self._lineage = lineage_repository
        self._clock = clock or (lambda: datetime.now(UTC))

    def commit_projection(
        self,
        *,
        rows: list[dict[str, Any]],
        schema_definition: ProjectionSchemaDefinition,
        projection_id: str,
        source_blob_sha256: list[str],
        acquisition_ids: list[str],
        provider: str,
        venue: str,
        sensor_family: str,
        native_instrument: str,
        native_granularity: str | None,
        parser_version: str,
        partition_key: str,
        logical_year: int,
        logical_month: int,
        logical_day: int,
        lineage_manifest_id: str,
        shard_id: int = 0,
        min_provider_time: datetime | None = None,
        max_provider_time: datetime | None = None,
        quality_flags: list[str | QualityFlagAcquisition] | None = None,
        row_lineage: list[RowProjectionLineage] | None = None,
    ) -> tuple[RawProjectionArtifact, Path]:
        """Commit the full T0A-verified, lineage-complete projection."""
        from .models import ProjectionLineage
        from .catalog import is_usable_manifest_provenance

        # -- 1/2. T0A sources: durable metadata + physical verification +
        # usable acquisition identity (I05R1 §11-§13, §17) ----------------
        if len(source_blob_sha256) != len(acquisition_ids):
            raise ProjectionPreconditionError(
                "source_blob_sha256 and acquisition_ids must be parallel"
            )
        for blob_sha, acq_id in zip(source_blob_sha256, acquisition_ids):
            metas = self._blob_metadata_repository.get_blob_metadata(blob_sha)
            if not metas:
                raise ProjectionSourceNotUsable(
                    f"source blob {blob_sha} has no durable EvidenceBlob "
                    "metadata"
                )
            verified = False
            for meta in metas:
                check = self._blob_store.verify_blob(
                    meta.blob_sha256,
                    meta.storage_encoding,
                    expected_byte_length=meta.byte_length,
                )
                if check.integrity_state.name == "LOCAL_HASH_VERIFIED":
                    verified = True
                    break
            if not verified:
                raise ProjectionSourceNotUsable(
                    f"source blob {blob_sha} has no physically verified "
                    "representation"
                )
            try:
                acq = self._acquisitions.get_acquisition(acq_id)
            except Exception as exc:
                raise ProjectionSourceNotUsable(
                    f"source acquisition {acq_id!r} does not exist durably"
                ) from exc
            if acq.blob_sha256 != blob_sha:
                raise ProjectionSourceNotUsable(
                    f"acquisition {acq_id!r} references blob "
                    f"{acq.blob_sha256!r}, lineage declares {blob_sha!r}"
                )
            if not is_usable_manifest_provenance(acq):
                raise ProjectionSourceNotUsable(
                    f"acquisition {acq_id!r} is not usable provenance "
                    "(forensic failure evidence may not become T0B lineage)"
                )
            for name, expected, actual in (
                ("provider", provider, acq.provider_id),
                ("venue", venue, acq.venue),
                ("sensor_family", sensor_family, acq.sensor_family),
                ("native_instrument", native_instrument, acq.native_instrument),
            ):
                if str(actual) != expected:
                    raise ProjectionSourceNotUsable(
                        f"acquisition {acq_id!r} {name}={actual!r} does not "
                        f"match projection context {expected!r}; byte equality "
                        "never transfers provenance"
                    )
            if (
                native_granularity is not None
                and acq.native_granularity is not None
                and str(acq.native_granularity) != native_granularity
            ):
                raise ProjectionSourceNotUsable(
                    f"acquisition {acq_id!r} granularity "
                    f"{str(acq.native_granularity)!r} does not match "
                    f"projection {native_granularity!r}"
                )

        # -- 3. Registered schema ------------------------------------------
        try:
            self._schemas.resolve(schema_definition.schema_key)
        except Exception as exc:
            raise ProjectionSchemaNotFound(
                f"projection schema {schema_definition.schema_identity!r} is "
                "not registered"
            ) from exc

        # -- 4/5/6. Write, verify, publish the physical projection ---------
        artifact, final_path = write_projection(
            root=self._root,
            rows=rows,
            schema_definition=schema_definition,
            schema_registry=self._schemas,
            projection_id=projection_id,
            source_blob_sha256=source_blob_sha256,
            acquisition_ids=acquisition_ids,
            provider=provider,
            venue=venue,
            sensor_family=sensor_family,
            native_instrument=native_instrument,
            native_granularity=native_granularity or "unknown",
            parser_version=parser_version,
            partition_key=partition_key,
            logical_year=logical_year,
            logical_month=logical_month,
            logical_day=logical_day,
            shard_id=shard_id,
            min_provider_time=min_provider_time,
            max_provider_time=max_provider_time,
            quality_flags=quality_flags,
            row_lineage=row_lineage,
        )

        # -- 7. Commit artifact metadata (physically verified) -------------
        committed_artifact = self._artifacts.commit(artifact)

        # -- 8. Commit projection context ----------------------------------
        context = ProjectionCatalogRecord(
            projection_id=projection_id,
            provider=provider,
            venue=venue,
            sensor_family=sensor_family,
            native_instrument=native_instrument,
            source_granularity=native_granularity,
            partition_key=partition_key,
            logical_date_start=datetime(logical_year, logical_month, logical_day, tzinfo=UTC),
            logical_date_end=datetime(logical_year, logical_month, logical_day, 23, 59, 59, tzinfo=UTC),
            projection_schema_id=schema_definition.projection_schema_id,
            projection_schema_version=schema_definition.projection_schema_version,
            schema_key=schema_definition.schema_key,
            schema_fingerprint=schema_definition.schema_fingerprint,
            parser_version=parser_version,
            projection_uri=artifact.projection_uri,
            projection_sha256=artifact.projection_sha256,
            row_count=artifact.row_count,
            min_provider_time=min_provider_time,
            max_provider_time=max_provider_time,
            lineage_manifest_id=lineage_manifest_id,
            quality_flags=[str(f) for f in artifact.quality_flags],
            created_at=self._clock(),
        )
        self._contexts.commit(context)

        # -- 9. Commit complete lineage ------------------------------------
        entries = [
            ProjectionLineage(
                lineage_manifest_id=lineage_manifest_id,
                projection_id=projection_id,
                source_blob_sha256=blob_sha,
                source_acquisition_id=acq_id,
                source_order=order,
            )
            for order, (blob_sha, acq_id) in enumerate(
                zip(source_blob_sha256, acquisition_ids)
            )
        ]
        self._lineage.commit(lineage_manifest_id, entries)

        return committed_artifact, final_path


__all__ = [
    "ProjectionArtifactCatalogCorrupt",
    "ProjectionArtifactRepository",
    "ProjectionCatalogRecord",
    "ProjectionContextRepository",
    "ProjectionCorruption",
    "ProjectionIdentityConflict",
    "ProjectionIntegrityError",
    "ProjectionPreconditionError",
    "ProjectionSchemaMismatch",
    "ProjectionSchemaNotFound",
    "ProjectionSourceNotUsable",
    "ProjectionWriteError",
    "RowProjectionLineage",
    "T0BProjectionService",
    "T0_PROJECTION_METADATA_COLUMNS",
    "write_projection",
]
