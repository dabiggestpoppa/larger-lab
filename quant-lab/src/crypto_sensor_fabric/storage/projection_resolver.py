"""SENSOR-B4-I05R1C — production ProjectionLineageResolver.

The REAL end-to-end projection reference validator consumed by
``PartitionManifestRepository`` (the I05D stub is NOT acceptance proof —
I05R1 §15/§17).

``ProjectionLineageResolver.validate_projection_ref(projection_id, manifest)``
loads, from DURABLE repositories only:

- the ``RawProjectionArtifact`` metadata,
- the ``ProjectionCatalogRecord`` context,
- the physical Parquet projection (bytes + schema + row count),
- the registered schema definition,
- the complete ``ProjectionLineage`` entries,
- every source acquisition (durable, usable, identity-matched),
- every source blob (durable metadata + physically verified T0A bytes),

and verifies the complete chain:

- artifact + context + lineage agree on SHA, URI, row count, schema key,
  fingerprint, parser, lineage manifest id;
- physical Parquet opens, its SHA matches the committed one, its row count
  matches, and required T0 metadata columns are present;
- every lineage entry is complete and consistent (order, bounds, blob/
  acquisition binding);
- lineage source pairs resolve to usable provenance matching the
  projection context (provider/venue/sensor/instrument/granularity);
- partition match (I05 §50 / I05R1 §50): partition_key, provider, venue,
  sensor_family, native_instrument, source granularity where known, and
  logical date/range context recorded by the projection;
- manifest source visibility (I05 §51 / I05R1 §49): every projection
  source blob appears in the manifest's ``blob_refs``.

No stub may certify the acceptance path; this object IS the production path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .checksums import sha256_file
from .paths import resolve_under_root
from .projection_lineage import (
    ArtifactLineageMismatch,
    NoUsableProjectionSource,
    ProjectionLineageConflict,
    SourceOrderConflict,
)
from .projection_schema import ProjectionSchemaDefinition, T0_METADATA_SCHEMA
from .projections import ProjectionCatalogRecord, ProjectionCorruption


class ProjectionResolverError(RuntimeError):
    """Base class for production resolver failures."""


class ProjectionChainBroken(ProjectionResolverError):
    """Artifact/context/lineage/physical disagree; the chain is not usable."""


class ProjectionPartitionMismatch(ProjectionResolverError):
    """The projection does not belong to the referencing manifest partition."""


class ProjectionSourceHidden(ProjectionResolverError):
    """A projection source blob is not visible in the manifest blob_refs."""


class ProjectionLineageResolver:
    """Production resolver: proves the complete T0A -> T0B chain on demand.

    Constructed with explicit durable dependencies (no hidden globals, no
    caller dictionaries on the production path):

    - root: the T0 data root (projection physical bytes resolve beneath it);
    - artifacts: ProjectionArtifactRepository;
    - contexts: ProjectionContextRepository;
    - lineage: ProjectionLineageRepository (durable-wired);
    - schemas: ProjectionSchemaRegistry.
    """

    def __init__(
        self,
        *,
        root: Path,
        artifacts: Any,
        contexts: Any,
        lineage: Any,
        schemas: Any,
    ) -> None:
        self._root = Path(root)
        self._artifacts = artifacts
        self._contexts = contexts
        self._lineage = lineage
        self._schemas = schemas

    # ------------------------------------------------------------------
    # Internal chain validation
    # ------------------------------------------------------------------

    def _load_artifact(self, projection_id: str) -> Any:
        artifact = self._artifacts.get(projection_id)
        if artifact is None:
            raise ProjectionChainBroken(
                f"projection_id={projection_id!r} has no committed "
                "RawProjectionArtifact metadata"
            )
        return artifact

    def _load_context(self, projection_id: str) -> ProjectionCatalogRecord:
        context = self._contexts.get(projection_id)
        if context is None:
            raise ProjectionChainBroken(
                f"projection_id={projection_id!r} has no committed "
                "ProjectionCatalogRecord context"
            )
        return context

    def _load_lineage(
        self, projection_id: str, context: ProjectionCatalogRecord
    ) -> list[Any]:
        """Resolve lineage through the context's authoritative manifest id.

        I05R3 §8: the binding is EXPLICIT — the resolver reads
        ``lineage.get(context.lineage_manifest_id)`` rather than scanning
        all fragments for the projection.  Every returned entry must still
        name the projection; a competing manifest identity for the same
        projection cannot be discovered here by design.
        """
        entries = self._lineage.get(context.lineage_manifest_id)
        if not entries:
            raise ProjectionChainBroken(
                f"projection_id={projection_id!r} has no committed lineage "
                f"manifest {context.lineage_manifest_id!r} "
                "(a VALID projection always has >= 1 entry)"
            )
        # Every entry must belong to the context's lineage manifest id AND
        # to the projection being resolved.
        for entry in entries:
            if entry.lineage_manifest_id != context.lineage_manifest_id:
                raise ProjectionChainBroken(
                    f"lineage entry manifest {entry.lineage_manifest_id!r} "
                    f"!= context lineage_manifest_id "
                    f"{context.lineage_manifest_id!r}"
                )
            if entry.projection_id != projection_id:
                raise ProjectionChainBroken(
                    f"authoritative lineage manifest "
                    f"{context.lineage_manifest_id!r} contains an entry for "
                    f"projection_id={entry.projection_id!r}, expected "
                    f"{projection_id!r}"
                )
        return entries

    def _verify_lineage_shape(
        self, projection_id: str, artifact: Any, entries: list[Any]
    ) -> None:
        # Contiguous unique order.
        orders = sorted(e.source_order for e in entries)
        if orders != list(range(len(entries))):
            raise SourceOrderConflict(
                f"projection {projection_id!r} lineage source_order {orders} "
                "is not contiguous 0..N-1"
            )
        # Row bounds both-or-none, inclusive ordered.
        for entry in entries:
            start, end = entry.source_row_start, entry.source_row_end
            if (start is None) != (end is None):
                raise ProjectionLineageConflict(
                    f"lineage order={entry.source_order} has one-sided row "
                    "bounds"
                )
            if start is not None and end is not None and end < start:
                raise ProjectionLineageConflict(
                    f"lineage order={entry.source_order} row bounds inverted"
                )
        # Artifact source list EXACTLY matches ordered lineage (no extra,
        # no missing, no duplicate identity).
        ordered_sources = [e.source_blob_sha256 for e in
                           sorted(entries, key=lambda e: e.source_order)]
        if artifact.source_blob_sha256 != ordered_sources:
            raise ArtifactLineageMismatch(
                f"artifact sources {artifact.source_blob_sha256} != ordered "
                f"lineage sources {ordered_sources}"
            )

    def _verify_source_pairs(self, entries: list[Any], context: ProjectionCatalogRecord) -> None:
        from .catalog import is_usable_manifest_provenance

        for entry in sorted(entries, key=lambda e: e.source_order):
            blob_sha = entry.source_blob_sha256
            acq_id = entry.source_acquisition_id

            metas = self._lineage._blob_metadata_repository.get_blob_metadata(blob_sha)
            if not metas:
                raise ProjectionChainBroken(
                    f"lineage source blob {blob_sha} has no durable metadata"
                )
            verified = False
            for meta in metas:
                check = self._lineage._blob_store.verify_blob(
                    meta.blob_sha256,
                    meta.storage_encoding,
                    expected_byte_length=meta.byte_length,
                )
                if check.integrity_state.name == "LOCAL_HASH_VERIFIED":
                    verified = True
                    break
            if not verified:
                raise ProjectionChainBroken(
                    f"lineage source blob {blob_sha} is not physically "
                    "verified"
                )

            try:
                acq = self._lineage._acquisitions.get_acquisition(acq_id)
            except Exception as exc:
                raise ProjectionChainBroken(
                    f"lineage acquisition {acq_id!r} does not exist durably"
                ) from exc
            if acq.blob_sha256 != blob_sha:
                raise ProjectionLineageConflict(
                    f"acquisition {acq_id!r} references blob "
                    f"{acq.blob_sha256!r}, lineage declares {blob_sha!r}"
                )
            if not is_usable_manifest_provenance(acq):
                raise NoUsableProjectionSource(
                    f"lineage acquisition {acq_id!r} is not usable provenance"
                )
            for name, expected, actual in (
                ("provider", context.provider, acq.provider_id),
                ("venue", context.venue, acq.venue),
                ("sensor_family", context.sensor_family, acq.sensor_family),
                ("native_instrument", context.native_instrument, acq.native_instrument),
            ):
                if str(actual) != expected:
                    raise ProjectionLineageConflict(
                        f"lineage acquisition {acq_id!r} {name}={actual!r} "
                        f"does not match projection {expected!r}"
                    )
            if (
                context.source_granularity is not None
                and acq.native_granularity is not None
                and str(acq.native_granularity) != context.source_granularity
            ):
                raise ProjectionLineageConflict(
                    f"lineage acquisition {acq_id!r} granularity mismatch"
                )

    def _verify_physical(
        self,
        projection_id: str,
        artifact: Any,
        context: ProjectionCatalogRecord,
        registered: ProjectionSchemaDefinition,
    ) -> None:
        """Prove the stored physical T0B file NOW (I05R2 §18-§22).

        "The writer validated it once" is not sufficient (§22): the
        read-time chain re-proves exact schema, T0 constant VALUES, row
        ordinals and physical row lineage from the bytes that exist now.
        """
        path = resolve_under_root(self._root, artifact.projection_uri)
        if not path.is_file():
            raise ProjectionCorruption(
                f"physical projection missing at {path!s}"
            )
        actual_sha = sha256_file(str(path)).hex_digest
        if actual_sha != artifact.projection_sha256:
            raise ProjectionCorruption(
                f"physical projection SHA {actual_sha} != committed "
                f"{artifact.projection_sha256}"
            )
        # Read the FILE's own schema via ParquetFile: pq.read_table()
        # performs dataset discovery and would append Hive partition
        # columns inferred from the directory layout, which are NOT part
        # of the stored schema contract.
        table = pq.ParquetFile(str(path)).read()
        if table.num_rows != artifact.row_count:
            raise ProjectionCorruption(
                f"physical row count {table.num_rows} != committed "
                f"{artifact.row_count}"
            )
        # EXACT full-schema equality (I05R2 §16/§18): registered native
        # schema + T0_METADATA_SCHEMA, checked with exact structural
        # equality (field order, names, types, nullability, nested
        # children, decimal precision/scale, timestamp units/timezones).
        # A name-only proof is not a schema proof.
        expected_full_schema = pa.schema(
            list(registered.provider_native_schema) + list(T0_METADATA_SCHEMA)
        )
        if not table.schema.equals(expected_full_schema, check_metadata=False):
            raise ProjectionCorruption(
                "physical projection schema does not EXACTLY equal the "
                f"registered schema {registered.projection_schema_id!r} @ "
                f"{registered.projection_schema_version!r}"
            )

        # T0 VALUE revalidation (§19): constants on EVERY row.
        expected_constants = {
            "_t0_projection_id": projection_id,
            "_t0_provider": context.provider,
            "_t0_venue": context.venue,
            "_t0_sensor_family": context.sensor_family,
            "_t0_native_instrument": context.native_instrument,
            "_t0_parser_version": context.parser_version,
            "_t0_schema_version": context.projection_schema_version,
        }
        for column, expected in expected_constants.items():
            values = set(table.column(column).to_pylist())
            if values != {expected}:
                raise ProjectionCorruption(
                    f"physical T0 column {column!r} is not constant "
                    f"{expected!r}: {values!r}"
                )

        # Row ordinal revalidation (§20): exactly 0..row_count-1,
        # contiguous, no duplicates, no gaps, no reordered identity.
        ordinals = table.column("_t0_row_ordinal").to_pylist()
        if ordinals != list(range(table.num_rows)):
            raise ProjectionCorruption(
                "physical _t0_row_ordinal is not exactly contiguous "
                f"0..{table.num_rows - 1}"
            )

        # Physical row lineage revalidation (§21): resolve lineage through
        # the context's authoritative manifest id (I05R3 §8).
        entries = sorted(
            self._lineage.get(context.lineage_manifest_id) or [],
            key=lambda e: e.source_order,
        )
        row_blobs = table.column("_t0_source_blob_sha256").to_pylist()
        row_acqs = table.column("_t0_acquisition_id").to_pylist()
        if len(entries) == 1:
            exact_blob = entries[0].source_blob_sha256
            exact_acq = entries[0].source_acquisition_id
            for i, (b, a) in enumerate(zip(row_blobs, row_acqs)):
                if b != exact_blob or a != exact_acq:
                    raise ProjectionCorruption(
                        f"row {i} single-source lineage ({b!r}, {a!r}) != "
                        f"committed ({exact_blob!r}, {exact_acq!r})"
                    )
        else:
            declared = {
                (e.source_blob_sha256, e.source_acquisition_id) for e in entries
            }
            for i, (b, a) in enumerate(zip(row_blobs, row_acqs)):
                if b is None and a is None:
                    continue  # unattributed row is allowed for multi-source
                if (b is None) != (a is None):
                    raise ProjectionCorruption(
                        f"row {i} has one-sided lineage (blob={b!r}, "
                        f"acquisition={a!r}); both or neither"
                    )
                if (b, a) not in declared:
                    raise ProjectionCorruption(
                        f"row {i} lineage pair ({b!r}, {a!r}) is not a "
                        "committed lineage pair"
                    )

        # Artifact/context agreement on identity + schema + lineage binding.
        if context.projection_sha256 != artifact.projection_sha256:
            raise ProjectionChainBroken(
                "context projection_sha256 != artifact projection_sha256"
            )
        if context.projection_uri != artifact.projection_uri:
            raise ProjectionChainBroken(
                "context projection_uri != artifact projection_uri"
            )
        if context.row_count != artifact.row_count:
            raise ProjectionChainBroken("context row_count != artifact row_count")
        if (
            context.projection_schema_id != artifact.projection_schema_id
            or context.projection_schema_version
            != artifact.projection_schema_version
            or context.parser_version != artifact.parser_version
        ):
            raise ProjectionChainBroken(
                "context schema/parser identity disagrees with the artifact"
            )

    # ------------------------------------------------------------------
    # Protocol implementation
    # ------------------------------------------------------------------

    def validate_projection_ref(
        self,
        projection_id: str,
        manifest: Any,
    ) -> None:
        """Prove one manifest projection_ref end to end (I05R1 §16)."""
        artifact = self._load_artifact(projection_id)
        context = self._load_context(projection_id)
        entries = self._load_lineage(projection_id, context)
        self._verify_lineage_shape(projection_id, artifact, entries)
        self._verify_source_pairs(entries, context)

        # Registered schema still resolves and matches the recorded
        # fingerprint (schema drift = broken chain).
        try:
            registered = self._schemas.resolve(context.schema_key)
        except Exception as exc:
            raise ProjectionChainBroken(
                f"projection schema key {context.schema_key!r} is not "
                "registered"
            ) from exc
        if registered.schema_fingerprint != context.schema_fingerprint:
            raise ProjectionChainBroken(
                "registered schema fingerprint != recorded schema fingerprint"
            )

        # I05R2 §18: physical verification is the authoritative read-time
        # proof — exact schema + T0 values + ordinals + row lineage.
        self._verify_physical(projection_id, artifact, context, registered)

        # Partition match (§50): same projection bytes never transfer
        # partition identity.
        if context.partition_key != manifest.partition_key:
            raise ProjectionPartitionMismatch(
                f"projection {projection_id!r} partition_key "
                f"{context.partition_key!r} != manifest "
                f"{manifest.partition_key!r}"
            )
        for name, expected, actual in (
            ("provider", manifest.provider, context.provider),
            ("venue", manifest.venue, context.venue),
            ("sensor_family", str(manifest.sensor_family), context.sensor_family),
            ("native_instrument", manifest.native_instrument, context.native_instrument),
        ):
            if str(actual) != str(expected):
                raise ProjectionPartitionMismatch(
                    f"projection {projection_id!r} {name}={actual!r} does "
                    f"not match manifest {expected!r}"
                )
        if (
            getattr(manifest, "source_granularity", None) is not None
            and context.source_granularity is not None
            and str(manifest.source_granularity) != context.source_granularity
        ):
            raise ProjectionPartitionMismatch(
                f"projection {projection_id!r} granularity "
                f"{context.source_granularity!r} != manifest "
                f"{str(manifest.source_granularity)!r}"
            )
        # Logical range compatibility: the projection's logical window must
        # intersect the manifest's logical window (both explicit records).
        if (
            context.logical_date_end < manifest.logical_date_start
            or context.logical_date_start > manifest.logical_date_end
        ):
            raise ProjectionPartitionMismatch(
                f"projection {projection_id!r} logical window "
                f"[{context.logical_date_start}, {context.logical_date_end}] "
                "does not intersect the manifest logical window"
            )

        # Source visibility (§49): every projection source blob appears in
        # the manifest blob_refs — no hidden T0A dependency.
        manifest_blobs = set(getattr(manifest, "blob_refs", []) or [])
        missing = set(artifact.source_blob_sha256) - manifest_blobs
        if missing:
            raise ProjectionSourceHidden(
                f"projection {projection_id!r} source blobs {sorted(missing)} "
                "are not visible in manifest blob_refs"
            )

        # Duplicate projection refs are the manifest repository's model-level
        # concern; when reached via that path they are rejected earlier.


__all__ = [
    "ProjectionChainBroken",
    "ProjectionLineageResolver",
    "ProjectionPartitionMismatch",
    "ProjectionResolverError",
    "ProjectionSourceHidden",
]
