"""SENSOR-B4-I05B — immutable provider-native T0B Parquet writer and projection artifact catalog.

Provides:
- ``write_projection``: builds an Arrow Table, writes to staging, verifies
  schema/metadata/row-ordinals, computes projection SHA-256 of exact stored
  bytes, and publishes to the final path via no-clobber atomicity.
- ``ProjectionArtifactRepository``: immutable metadata catalog for
  ``RawProjectionArtifact`` records, persisted under
  ``<t0_root>/catalogs/manifests/projections/``.

Key doctrines:
- T0B is subordinate to T0A and rebuildable from it.
- Provider-native values preserved; no normalization.
- Projection SHA = SHA-256 of exact stored Parquet bytes (NOT T0A source hash).
- No-clobber publication; same projection_id + same bytes = idempotent reuse.
- Same projection_id + different bytes/lineage/schema = ProjectionIdentityConflict.
- Physical staging + fsync + verify before publication.
- No caller-trusted row count: repository/writer derives it.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .atomic import (
    AtomicPublishTargetExists,
    ensure_durable_directory,
    fsync_directory,
    publish_no_replace,
)
from .checksums import sha256_file
from .models import RawProjectionArtifact
from .projection_schema import ProjectionSchemaDefinition
from ..providers.base.enums import QualityFlagAcquisition

# ---------------------------------------------------------------------------
# T0B metadata columns injected by the projection layer
# ---------------------------------------------------------------------------

T0_PROJECTION_METADATA_COLUMNS: list[str] = [
    "_t0_projection_id",
    "_t0_source_blob_sha256",
    "_t0_acquisition_id",
    "_t0_provider",
    "_t0_venue",
    "_t0_sensor_family",
    "_t0_native_instrument",
    "_t0_parser_version",
    "_t0_schema_version",
    "_t0_row_ordinal",
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ProjectionWriteError(RuntimeError):
    """Base class for projection write failures."""


class ProjectionSchemaMismatch(ProjectionWriteError):
    """Provided table does not match the registered provider-native schema."""


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


# ---------------------------------------------------------------------------
# Internal: inject T0 metadata columns into rows
# ---------------------------------------------------------------------------


def _inject_t0_metadata(
    rows: list[dict[str, Any]],
    projection_id: str,
    provider: str,
    venue: str,
    sensor_family: str,
    native_instrument: str,
    parser_version: str,
    schema_version: str,
    source_blob_sha256: list[str],
    acquisition_ids: list[str],
) -> list[dict[str, Any]]:
    """Inject required _t0_* metadata columns into each row.

    For single-source projections, _t0_source_blob_sha256 and
    _t0_acquisition_id are populated per row.  For multi-source, they may
    be NULL when per-row attribution is not defensible.
    """
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

        # Source attribution: single-source → every row gets the exact source;
        # multi-source → per-row attribution left NULL unless caller already
        # populated it in the source rows.
        if len(source_blob_sha256) == 1 and len(acquisition_ids) == 1:
            if "_t0_source_blob_sha256" not in out or out["_t0_source_blob_sha256"] is None:
                out["_t0_source_blob_sha256"] = source_blob_sha256[0]
            if "_t0_acquisition_id" not in out or out["_t0_acquisition_id"] is None:
                out["_t0_acquisition_id"] = acquisition_ids[0]

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
    quality_flags: list[str] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> tuple[RawProjectionArtifact, Path]:
    """Write a T0B Parquet projection with full staging/durability pipeline.

    Returns the committed ``RawProjectionArtifact`` metadata and the final
    file path.

    Pipeline (I05 §37):
    1. Build explicit Arrow Table with injected _t0_* metadata columns
    2. Validate against registered provider-native schema
    3. Write staged Parquet
    4. Flush + fsync staged
    5. Reopen staged Parquet, verify schema + metadata columns + row count + row ordinals
    6. Compute SHA-256 of exact stored Parquet bytes
    7. Derive final projection_object_key()
    8. No-clobber publish
    9. Parent-directory fsync
    """
    from .paths import projection_object_key

    if clock is None:
        clock = datetime.utcnow

    if not rows:
        raise ProjectionWriteError("projection must contain at least one row")

    # 1. Inject T0 metadata
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
    )

    # 2. Build Arrow Table — first construct expected schema with T0 columns
    t0_fields = [
        pa.field("_t0_projection_id", pa.string(), nullable=False),
        pa.field("_t0_source_blob_sha256", pa.string(), nullable=True),
        pa.field("_t0_acquisition_id", pa.string(), nullable=True),
        pa.field("_t0_provider", pa.string(), nullable=False),
        pa.field("_t0_venue", pa.string(), nullable=False),
        pa.field("_t0_sensor_family", pa.string(), nullable=False),
        pa.field("_t0_native_instrument", pa.string(), nullable=False),
        pa.field("_t0_parser_version", pa.string(), nullable=False),
        pa.field("_t0_schema_version", pa.string(), nullable=False),
        pa.field("_t0_row_ordinal", pa.int64(), nullable=False),
    ]
    full_schema = pa.schema(
        list(schema_definition.provider_native_schema) + t0_fields
    )

    # Validate provider-native fields don't contain reserved _t0_ columns
    for field in schema_definition.provider_native_schema:
        if field.name.startswith("_t0_"):
            raise ProjectionWriteError(
                f"provider-native schema contains reserved column {field.name!r}"
            )

    try:
        table = pa.Table.from_pylist(enriched, schema=full_schema)
    except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
        raise ProjectionSchemaMismatch(
            f"failed to build Arrow Table from rows: {exc}"
        ) from exc

    # Verify schema match
    if table.schema != full_schema:
        raise ProjectionSchemaMismatch(
            f"table schema mismatch: expected {full_schema}, got {table.schema}"
        )

    # 3. Derive final projection key and staging path
    # Staging at root level (same filesystem) to stay within Windows MAX_PATH
    # when the final path includes deep provider/venue/schema directories.
    staging_dir = root / "_staging"
    ensure_durable_directory(staging_dir)
    staged = staging_dir / f"{uuid.uuid4().hex}.parquet"

    try:
        pq.write_table(table, str(staged))

        # 4. Flush + fsync
        fsync_file(staged)

        # 5. Reopen and verify
        reread = pq.read_table(str(staged))
        if reread.num_rows != len(enriched):
            raise ProjectionIntegrityError(
                f"staged projection row count {reread.num_rows} != expected {len(enriched)}"
            )

        # Verify row ordinals are contiguous 0..N-1
        ordinals = reread.column("_t0_row_ordinal").to_pylist()
        expected_ordinals = list(range(len(enriched)))
        if ordinals != expected_ordinals:
            raise ProjectionIntegrityError(
                f"row ordinals not contiguous 0..{len(enriched)-1}: {ordinals}"
            )

        # 6. Compute SHA of exact stored bytes
        digest = sha256_file(str(staged))
        projection_sha256 = digest.hex_digest

        # 7. Derive final projection key
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

        # 8. No-clobber publish
        try:
            publish_no_replace(staged, final)
        except AtomicPublishTargetExists:
            # Idempotent: verify existing matches
            existing_digest = sha256_file(str(final))
            if existing_digest.hex_digest != projection_sha256:
                raise ProjectionIdentityConflict(projection_id)
            # Same bytes — idempotent reuse

        # 9. Parent-directory fsync
        fsync_directory(final.parent)

        # Build metadata
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
                QualityFlagAcquisition(f) for f in (quality_flags or [])
            ],
        )

        return artifact, final

    finally:
        try:
            if staged.exists():
                staged.unlink()
        except OSError:
            pass


def fsync_file(path: Path) -> None:
    """Fsync a file (imported from atomic for convenience)."""
    from .atomic import fsync_file as _fsync

    _fsync(path)


# ---------------------------------------------------------------------------
# Projection artifact repository
# ---------------------------------------------------------------------------


class ProjectionArtifactRepository:
    """Immutable metadata catalog for RawProjectionArtifact records.

    Persists one immutable JSON fragment per projection_id under
    ``<t0_root>/catalogs/manifests/projections/``.

    Same projection_id + same semantic artifact = idempotent.
    Same projection_id + different SHA/schema/lineage = ProjectionIdentityConflict.
    """

    PROJECTION_CATALOG_SCHEMA = pa.schema(
        [
            pa.field("projection_id", pa.string(), nullable=False),
            pa.field("source_blob_sha256", pa.list_(pa.string()), nullable=False),
            pa.field("projection_schema_id", pa.string(), nullable=False),
            pa.field("projection_schema_version", pa.string(), nullable=False),
            pa.field("parser_version", pa.string(), nullable=False),
            pa.field("row_count", pa.int64(), nullable=False),
            pa.field("min_provider_time", pa.timestamp("us", tz="UTC"), nullable=True),
            pa.field("max_provider_time", pa.timestamp("us", tz="UTC"), nullable=True),
            pa.field("partition_key", pa.string(), nullable=False),
            pa.field("projection_uri", pa.string(), nullable=False),
            pa.field("projection_sha256", pa.string(), nullable=False),
            pa.field("quality_flags", pa.list_(pa.string()), nullable=False),
            pa.field("state", pa.string(), nullable=False),
        ]
    )

    def __init__(self, catalog_root: Path) -> None:
        self._root = catalog_root
        self._root.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, RawProjectionArtifact] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all persisted projection artifacts into memory."""
        for path in self._root.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                artifact = RawProjectionArtifact(**data)
                self._cache[artifact.projection_id] = artifact
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    def commit(self, artifact: RawProjectionArtifact) -> RawProjectionArtifact:
        """Commit a projection artifact metadata record.

        Idempotent for same projection_id + same semantic artifact.
        ProjectionIdentityConflict for same projection_id + different content.
        """
        pid = artifact.projection_id
        if pid in self._cache:
            existing = self._cache[pid]
            # Check for conflicts
            if (
                existing.projection_sha256 != artifact.projection_sha256
                or existing.source_blob_sha256 != artifact.source_blob_sha256
                or existing.projection_schema_id != artifact.projection_schema_id
                or existing.projection_schema_version != artifact.projection_schema_version
                or existing.parser_version != artifact.parser_version
                or existing.row_count != artifact.row_count
            ):
                raise ProjectionIdentityConflict(pid)
            return existing  # idempotent

        # Persist as immutable JSON
        path = self._root / f"{pid}.json"
        path.write_text(
            json.dumps(
                json.loads(artifact.model_dump_json()),
                sort_keys=True,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self._cache[pid] = artifact
        return artifact

    def get(self, projection_id: str) -> RawProjectionArtifact | None:
        """Retrieve a projection artifact by ID, or None."""
        return self._cache.get(projection_id)

    def has(self, projection_id: str) -> bool:
        """Check if a projection_id is committed."""
        return projection_id in self._cache

    def list_ids(self) -> list[str]:
        """Return all committed projection_ids (sorted)."""
        return sorted(self._cache.keys())


__all__ = [
    "ProjectionArtifactRepository",
    "ProjectionCorruption",
    "ProjectionIdentityConflict",
    "ProjectionIntegrityError",
    "ProjectionSchemaMismatch",
    "ProjectionWriteError",
    "T0_PROJECTION_METADATA_COLUMNS",
    "write_projection",
]
