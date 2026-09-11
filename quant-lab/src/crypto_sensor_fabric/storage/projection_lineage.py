"""SENSOR-B4-I05C/I05R1C — projection lineage repository.

Persists ``ProjectionLineage`` rows immutably under
``<t0_root>/catalogs/manifests/projection_lineage/`` through the shared
``DurableJsonCatalog`` primitive (I05R1 §4-§6): hashed physical keys, staged
fsync'd writes, no-clobber publish, corruption fail-closed.

I05R1 §11: the lineage repository MUST ITSELF validate — BEFORE durable
publication — that:

- lineage is nonempty;
- all entries share one ``lineage_manifest_id`` and one ``projection_id``;
- the explicit ``commit(lineage_manifest_id, ...)`` argument matches every
  entry's own lineage_manifest_id (§19 — no silently ignored argument);
- row bounds are BOTH-None or BOTH-present, inclusive and ordered (§20);
- ``source_order`` is contiguous unique 0..N-1;
- the artifact source list exactly matches the ordered lineage;
- every source blob has durable EvidenceBlob metadata AND physically
  verifies through LocalBlobStore (§48 — no metadata-only proof);
- every source acquisition exists durably, references the exact lineage
  blob, and is USABLE provenance;
- provider/venue/sensor_family/native_instrument match the projection
  context; granularity matches where both are known (§13 — byte equality
  never transfers provider provenance: a KRAKEN projection may not use a
  GATE acquisition even for identical bytes).

Production commits read durable repositories only (§12); dictionary-based
helpers remain for unit tests.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .json_catalog import JsonCatalogCorrupt, DurableJsonCatalog
from .models import AcquisitionRecord, EvidenceBlob, ProjectionLineage


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LineageError(RuntimeError):
    """Base class for lineage validation failures."""


class NoLineageEntries(LineageError):
    """Projection has zero lineage entries — FORBIDDEN (I05 §22)."""


class ProjectionLineageConflict(LineageError):
    """Lineage references inconsistent source blob/acquisition pairs."""


class SourceOrderConflict(LineageError):
    """Source order has duplicates, gaps, or is not contiguous 0..N-1."""


class ArtifactLineageMismatch(LineageError):
    """Artifact source_blob_sha256 list does not match ordered lineage."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NoUsableProjectionSource(LineageError):
    """Selected lineage acquisition is not usable provenance."""


class LineageManifestBindingConflict(LineageError):
    """commit(lineage_manifest_id, entries) argument disagrees with entries."""


class ProjectionLineageCatalogCorrupt(LineageError):
    """A committed lineage manifest fragment is corrupt; fail closed."""


class LineageManifestNotFound(KeyError):
    """Requested lineage_manifest_id not found."""


# ---------------------------------------------------------------------------
# Lineage validation helpers
# ---------------------------------------------------------------------------


def validate_row_bounds(entries: list[ProjectionLineage]) -> None:
    """Row bounds are BOTH-None or BOTH-present, inclusive, ordered (§20)."""
    for entry in entries:
        start, end = entry.source_row_start, entry.source_row_end
        if (start is None) != (end is None):
            raise ProjectionLineageConflict(
                f"lineage entry order={entry.source_order} has one-sided row "
                "bounds; source_row_start/source_row_end must be both None "
                "or both present"
            )
        if start is not None and end is not None and end < start:
            raise ProjectionLineageConflict(
                f"lineage entry order={entry.source_order} has "
                f"source_row_end {end} < source_row_start {start}"
            )


def validate_source_order(lineage_entries: list[ProjectionLineage]) -> None:
    """Validate source_order is contiguous unique 0..N-1."""
    orders = sorted(e.source_order for e in lineage_entries)
    if orders != list(range(len(lineage_entries))):
        raise SourceOrderConflict(
            f"source_order must be contiguous 0..{len(lineage_entries) - 1}, "
            f"got {orders}"
        )


def validate_artifact_lineage_consistency(
    source_blob_sha256: list[str],
    lineage_entries: list[ProjectionLineage],
) -> None:
    """Validate artifact source list exactly matches ordered unique lineage."""
    ordered = sorted(lineage_entries, key=lambda e: e.source_order)
    lineage_sources = [e.source_blob_sha256 for e in ordered]
    if lineage_sources != source_blob_sha256:
        raise ArtifactLineageMismatch(
            f"artifact source_blob_sha256 {source_blob_sha256} does not "
            f"match ordered lineage sources {lineage_sources}"
        )


def validate_lineage_completeness(
    lineage_entries: list[ProjectionLineage],
    source_blob_sha256: list[str],
    projection_id: str,
) -> None:
    """Validate file-level lineage is complete and consistent."""
    if not lineage_entries:
        raise NoLineageEntries(
            f"projection {projection_id!r} has zero lineage entries (I05 §22)"
        )
    for entry in lineage_entries:
        if entry.projection_id != projection_id:
            raise ProjectionLineageConflict(
                f"lineage entry references projection_id={entry.projection_id!r} "
                f"but expected {projection_id!r}"
            )
    validate_row_bounds(lineage_entries)
    validate_source_order(lineage_entries)
    validate_artifact_lineage_consistency(source_blob_sha256, lineage_entries)


def validate_lineage_source(
    lineage_entry: ProjectionLineage,
    evidence_blobs: dict[str, EvidenceBlob],
    acquisitions: dict[str, AcquisitionRecord],
    *,
    is_usable_predicate: Callable[[AcquisitionRecord], bool],
) -> None:
    """Validate a single lineage source entry against supplied dictionaries.

    UNIT-TEST HELPER ONLY: production commits route through
    ``ProjectionLineageRepository.commit`` which reads durable repositories
    (I05R1 §12).
    """
    blob_sha = lineage_entry.source_blob_sha256
    acq_id = lineage_entry.source_acquisition_id

    if blob_sha not in evidence_blobs:
        raise ProjectionLineageConflict(
            f"lineage source_blob_sha256={blob_sha!r} has no "
            "EvidenceBlob metadata"
        )
    if acq_id not in acquisitions:
        raise ProjectionLineageConflict(
            f"lineage source_acquisition_id={acq_id!r} not found"
        )
    acq = acquisitions[acq_id]
    if acq.blob_sha256 != blob_sha:
        raise ProjectionLineageConflict(
            f"acquisition {acq_id!r} references blob_sha256={acq.blob_sha256!r} "
            f"but lineage declares {blob_sha!r}"
        )
    if not is_usable_predicate(acq):
        raise NoUsableProjectionSource(
            f"acquisition {acq_id!r} is not usable provenance "
            "(failure_ref or H3=False or explicit HTTP failure)"
        )


# ---------------------------------------------------------------------------
# Projection lineage repository — enforcing, durable, immutable
# ---------------------------------------------------------------------------


class ProjectionLineageRepository:
    """Immutable durable repository for ProjectionLineage records.

    Persists lineage manifests under
    ``<t0_root>/catalogs/manifests/projection_lineage/`` — one hashed
    fragment per ``lineage_manifest_id``, multiple rows per manifest.  All
    rows in one manifest MUST share lineage_manifest_id + projection_id.

    ``commit`` ENFORCES the full source-constraint set (I05R1 §11) before
    any durable publication: T0A physical verification, usable-provenance
    acquisition selection, identity matching against the projection
    context, contiguous source order, and exact artifact/lineage agreement.
    """

    def __init__(
        self,
        catalog_root: Path,
        *,
        blob_store: Any = None,
        blob_metadata_repository: Any = None,
        acquisition_repository: Any = None,
        artifact_repository: Any = None,
        context_repository: Any = None,
        projection_root: Path | None = None,
    ) -> None:
        self._root = Path(catalog_root)
        self._blob_store = blob_store
        self._blob_metadata_repository = blob_metadata_repository
        self._acquisitions = acquisition_repository
        self._artifact_repository = artifact_repository
        self._context_repository = context_repository
        self._projection_root = projection_root
        try:
            self._catalog = DurableJsonCatalog(
                self._root, logical_id_field="lineage_manifest_id"
            )
        except JsonCatalogCorrupt as exc:
            raise ProjectionLineageCatalogCorrupt(str(exc)) from exc
        self._cache: dict[str, list[ProjectionLineage]] = {}
        self._load_all()

    # -- loading -------------------------------------------------------------

    def _parse_fragment(self, payload: dict[str, Any]) -> list[ProjectionLineage]:
        if payload.get("record_type") != "projection_lineage_manifest":
            raise ProjectionLineageCatalogCorrupt(
                "lineage fragment has wrong record_type"
            )
        try:
            entries = [ProjectionLineage(**row) for row in payload["entries"]]
        except Exception as exc:
            raise ProjectionLineageCatalogCorrupt(
                f"lineage fragment entries are corrupt: {exc}"
            ) from exc
        if not entries:
            raise ProjectionLineageCatalogCorrupt(
                "committed lineage manifest has zero entries"
            )
        if any(
            e.lineage_manifest_id != payload.get("lineage_manifest_id")
            for e in entries
        ):
            raise ProjectionLineageCatalogCorrupt(
                "lineage fragment entries disagree with the manifest id"
            )
        return entries

    def _load_all(self) -> None:
        for logical_id in self._catalog.list_ids():
            payload = self._catalog.get(logical_id)
            assert payload is not None
            self._cache[logical_id] = self._parse_fragment(payload)

    # -- durable source verification (I05R1 §11/§13/§48) ---------------------

    def _verify_source_pair(
        self,
        entry: ProjectionLineage,
        context: Any | None,
    ) -> None:
        blob_sha = entry.source_blob_sha256
        acq_id = entry.source_acquisition_id

        # Durable blob metadata + PHYSICAL verification (no metadata-only proof).
        if self._blob_metadata_repository is None:
            raise LineageError(
                "ProjectionLineageRepository requires a "
                "blob_metadata_repository to prove source blob truth"
            )
        metas = self._blob_metadata_repository.get_blob_metadata(blob_sha)
        if not metas:
            raise ProjectionLineageConflict(
                f"lineage source_blob_sha256={blob_sha!r} has no durable "
                "EvidenceBlob metadata"
            )
        if self._blob_store is None:
            raise LineageError(
                "ProjectionLineageRepository requires a blob_store to "
                "physically verify source blobs"
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
            raise ProjectionLineageConflict(
                f"lineage source blob {blob_sha!r} has no physically "
                "verified representation"
            )

        # Durable acquisition truth.
        if self._acquisitions is None:
            raise LineageError(
                "ProjectionLineageRepository requires an "
                "acquisition_repository to prove source acquisition truth"
            )
        try:
            acq = self._acquisitions.get_acquisition(acq_id)
        except Exception as exc:
            raise ProjectionLineageConflict(
                f"lineage source_acquisition_id={acq_id!r} does not exist "
                "durably"
            ) from exc
        if acq.blob_sha256 != blob_sha:
            raise ProjectionLineageConflict(
                f"acquisition {acq_id!r} references blob "
                f"{acq.blob_sha256!r} but lineage declares {blob_sha!r}"
            )

        # USABLE provenance (forensic failure never becomes T0B lineage).
        from .catalog import is_usable_manifest_provenance

        if not is_usable_manifest_provenance(acq):
            raise NoUsableProjectionSource(
                f"acquisition {acq_id!r} is not usable provenance "
                "(forensic failure evidence may not become T0B lineage)"
            )

        # Identity matching against the projection context (§13).
        if context is not None:
            for name, expected, actual in (
                ("provider", context.provider, acq.provider_id),
                ("venue", context.venue, acq.venue),
                ("sensor_family", context.sensor_family, acq.sensor_family),
                (
                    "native_instrument",
                    context.native_instrument,
                    acq.native_instrument,
                ),
            ):
                if str(actual) != expected:
                    raise ProjectionLineageConflict(
                        f"acquisition {acq_id!r} {name}={actual!r} does not "
                        f"match projection context {expected!r}; byte "
                        "equality never transfers provider provenance"
                    )
            if (
                context.source_granularity is not None
                and acq.native_granularity is not None
                and str(acq.native_granularity) != context.source_granularity
            ):
                raise ProjectionLineageConflict(
                    f"acquisition {acq_id!r} granularity "
                    f"{str(acq.native_granularity)!r} does not match "
                    f"projection {context.source_granularity!r}"
                )

    def _resolve_context(self, projection_id: str) -> Any | None:
        if self._context_repository is None:
            return None
        return self._context_repository.get(projection_id)

    def _resolve_artifact_sources(self, projection_id: str) -> list[str] | None:
        if self._artifact_repository is None:
            return None
        artifact = self._artifact_repository.get(projection_id)
        if artifact is None:
            return None
        return list(artifact.source_blob_sha256)

    # -- commit ----------------------------------------------------------------

    def commit(
        self,
        lineage_manifest_id: str,
        entries: list[ProjectionLineage],
    ) -> list[ProjectionLineage]:
        """Validate and durably commit a lineage manifest (idempotent).

        Every §11 constraint is proven BEFORE publication.  Idempotent ONLY
        when ALL lineage fields match exactly, including row bounds (§18).
        """
        if not entries:
            raise NoLineageEntries("lineage manifest must contain entries")

        # All entries share manifest + projection identity.
        lmid = entries[0].lineage_manifest_id
        pid = entries[0].projection_id
        for entry in entries:
            if entry.lineage_manifest_id != lmid:
                raise ProjectionLineageConflict(
                    "all lineage entries must share lineage_manifest_id"
                )
            if entry.projection_id != pid:
                raise ProjectionLineageConflict(
                    "all lineage entries must share projection_id"
                )

        # §19: the explicit argument BINDS to the entries.
        if lineage_manifest_id != lmid:
            raise LineageManifestBindingConflict(
                f"commit argument lineage_manifest_id={lineage_manifest_id!r} "
                f"does not match entry lineage_manifest_id={lmid!r}"
            )

        # Row bounds + source order (§20 + §56).
        validate_row_bounds(entries)
        validate_source_order(entries)

        # Idempotence/conflict: ALL fields compared exactly, including row
        # bounds (§18).
        if lmid in self._cache:
            existing = self._cache[lmid]
            if len(existing) != len(entries):
                raise ProjectionLineageConflict(
                    f"lineage_manifest_id={lmid!r} already committed with "
                    f"{len(existing)} entries, got {len(entries)}"
                )
            for e, n in zip(
                sorted(existing, key=lambda x: x.source_order),
                sorted(entries, key=lambda x: x.source_order),
            ):
                if e.model_dump() != n.model_dump():
                    raise ProjectionLineageConflict(
                        f"lineage_manifest_id={lmid!r} already committed "
                        "with different content"
                    )
            return existing

        # Artifact source-list agreement (when an artifact repository is
        # wired — production always wires it; I05C-era callers may not).
        artifact_sources = self._resolve_artifact_sources(pid)
        if artifact_sources is not None:
            validate_artifact_lineage_consistency(artifact_sources, entries)

        # T0A source truth + identity matching, per entry, BEFORE publication.
        context = self._resolve_context(pid)
        for entry in sorted(entries, key=lambda e: e.source_order):
            self._verify_source_pair(entry, context)

        # Durable publication through the shared catalog primitive.
        payload = {
            "record_type": "projection_lineage_manifest",
            "lineage_manifest_id": lmid,
            "projection_id": pid,
            "entries": [json_entry(e) for e in entries],
        }
        try:
            self._catalog.commit(lmid, payload)
        except JsonCatalogCorrupt as exc:
            raise ProjectionLineageCatalogCorrupt(str(exc)) from exc
        self._cache[lmid] = entries
        return entries

    # -- reads ---------------------------------------------------------------

    def get(self, lineage_manifest_id: str) -> list[ProjectionLineage] | None:
        """Retrieve lineage entries by manifest ID."""
        return self._cache.get(lineage_manifest_id)

    def get_by_projection(self, projection_id: str) -> list[ProjectionLineage]:
        """Retrieve all lineage entries for a projection_id (ordered)."""
        result = []
        for entries in self._cache.values():
            for entry in entries:
                if entry.projection_id == projection_id:
                    result.append(entry)
        return sorted(result, key=lambda e: e.source_order)

    def has(self, lineage_manifest_id: str) -> bool:
        return lineage_manifest_id in self._cache

    def list_manifest_ids(self) -> list[str]:
        return sorted(self._cache.keys())


def json_entry(entry: ProjectionLineage) -> dict[str, Any]:
    """Canonical JSON-able row for a lineage entry."""
    import json as _json

    return _json.loads(entry.model_dump_json())


__all__ = [
    "ArtifactLineageMismatch",
    "LineageError",
    "LineageManifestBindingConflict",
    "LineageManifestNotFound",
    "NoLineageEntries",
    "NoUsableProjectionSource",
    "ProjectionLineageCatalogCorrupt",
    "ProjectionLineageConflict",
    "ProjectionLineageRepository",
    "SourceOrderConflict",
    "validate_artifact_lineage_consistency",
    "validate_lineage_completeness",
    "validate_lineage_source",
    "validate_row_bounds",
    "validate_source_order",
]
