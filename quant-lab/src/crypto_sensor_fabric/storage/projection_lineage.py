"""SENSOR-B4-I05C — projection lineage repository.

Persists ``ProjectionLineage`` rows immutably under
``<t0_root>/catalogs/manifests/projection_lineage/``.

Lineage answers: WHICH exact T0A bytes, WHICH acquisition, WHICH provider,
WHICH native instrument, WHICH parser, WHICH schema version fed this
projection.

Key doctrines:
- Every VALID projection has >= 1 lineage entry.
- Every lineage source blob must be physically verified.
- Every lineage acquisition must exist durably and reference the exact source
  blob.
- Every lineage acquisition must be USABLE provenance (not forensic failure).
- Source order must be contiguous and unique (0..N-1).
- Artifact source list must exactly match ordered unique lineage sources.
- Failed forensic acquisitions may NOT become T0B scientific lineage.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

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


class LineageManifestNotFound(KeyError):
    """Requested lineage_manifest_id not found."""


# ---------------------------------------------------------------------------
# Lineage validation helpers
# ---------------------------------------------------------------------------


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
    # Unique lineage sources in source_order
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

    # Check all entries belong to the same projection
    for entry in lineage_entries:
        if entry.projection_id != projection_id:
            raise ProjectionLineageConflict(
                f"lineage entry references projection_id={entry.projection_id!r} "
                f"but expected {projection_id!r}"
            )

    # Validate source order
    validate_source_order(lineage_entries)

    # Validate artifact/lineage consistency
    validate_artifact_lineage_consistency(source_blob_sha256, lineage_entries)


def validate_lineage_source(
    lineage_entry: ProjectionLineage,
    evidence_blobs: dict[str, EvidenceBlob],
    acquisitions: dict[str, AcquisitionRecord],
    *,
    is_usable_predicate: Callable[[AcquisitionRecord], bool],
) -> None:
    """Validate a single lineage source entry.

    Checks:
    - Source blob has EvidenceBlob metadata
    - Acquisition exists and references exact source blob
    - Acquisition is usable provenance (not forensic failure)
    """
    blob_sha = lineage_entry.source_blob_sha256
    acq_id = lineage_entry.source_acquisition_id

    # Blob must have metadata
    if blob_sha not in evidence_blobs:
        raise ProjectionLineageConflict(
            f"lineage source_blob_sha256={blob_sha!r} has no "
            "EvidenceBlob metadata"
        )

    # Acquisition must exist
    if acq_id not in acquisitions:
        raise ProjectionLineageConflict(
            f"lineage source_acquisition_id={acq_id!r} not found"
        )

    acq = acquisitions[acq_id]

    # Acquisition must reference exact source blob
    if acq.blob_sha256 != blob_sha:
        raise ProjectionLineageConflict(
            f"acquisition {acq_id!r} references blob_sha256={acq.blob_sha256!r} "
            f"but lineage declares {blob_sha!r}"
        )

    # Acquisition must be usable provenance
    if not is_usable_predicate(acq):
        raise NoUsableProjectionSource(
            f"acquisition {acq_id!r} is not usable provenance "
            "(failure_ref or H3=False or explicit HTTP failure)"
        )


# ---------------------------------------------------------------------------
# Projection lineage repository
# ---------------------------------------------------------------------------


class ProjectionLineageRepository:
    """Immutable repository for ProjectionLineage records.

    Persists lineage manifests under
    ``<t0_root>/catalogs/manifests/projection_lineage/``.

    One file per ``lineage_manifest_id``.  Multiple rows per manifest allowed.
    All rows in one manifest MUST share lineage_manifest_id + projection_id.
    """

    def __init__(self, catalog_root: Path) -> None:
        self._root = catalog_root
        self._root.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, list[ProjectionLineage]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all persisted lineage manifests."""
        for path in self._root.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                entries = [ProjectionLineage(**row) for row in data["entries"]]
                if entries:
                    lmid = entries[0].lineage_manifest_id
                    self._cache[lmid] = entries
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    def commit(
        self,
        lineage_manifest_id: str,
        entries: list[ProjectionLineage],
    ) -> list[ProjectionLineage]:
        """Commit a lineage manifest.  Idempotent for exact duplicates.

        Raises ``LineageError`` for validation failures.
        """
        if not entries:
            raise NoLineageEntries("lineage manifest must contain entries")

        # Validate all entries share the same manifest_id and projection_id
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

        if lmid in self._cache:
            existing = self._cache[lmid]
            # Idempotent check
            if len(existing) != len(entries):
                raise ProjectionLineageConflict(
                    f"lineage_manifest_id={lmid!r} already committed with "
                    f"{len(existing)} entries, got {len(entries)}"
                )
            for e, n in zip(existing, entries):
                if (
                    e.source_blob_sha256 != n.source_blob_sha256
                    or e.source_acquisition_id != n.source_acquisition_id
                    or e.source_order != n.source_order
                ):
                    raise ProjectionLineageConflict(
                        f"lineage_manifest_id={lmid!r} already committed "
                        "with different content"
                    )
            return existing

        # Persist
        path = self._root / f"{lmid}.json"
        rows = [json.loads(e.model_dump_json()) for e in entries]
        path.write_text(
            json.dumps(
                {"lineage_manifest_id": lmid, "projection_id": pid, "entries": rows},
                sort_keys=True,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self._cache[lmid] = entries
        return entries

    def get(self, lineage_manifest_id: str) -> list[ProjectionLineage] | None:
        """Retrieve lineage entries by manifest ID."""
        return self._cache.get(lineage_manifest_id)

    def get_by_projection(self, projection_id: str) -> list[ProjectionLineage]:
        """Retrieve all lineage entries for a projection_id."""
        result = []
        for entries in self._cache.values():
            for entry in entries:
                if entry.projection_id == projection_id:
                    result.append(entry)
        return sorted(result, key=lambda e: e.source_order)

    def has(self, lineage_manifest_id: str) -> bool:
        """Check if a lineage manifest exists."""
        return lineage_manifest_id in self._cache

    def list_manifest_ids(self) -> list[str]:
        """Return all committed lineage manifest IDs (sorted)."""
        return sorted(self._cache.keys())


__all__ = [
    "ArtifactLineageMismatch",
    "LineageError",
    "LineageManifestNotFound",
    "NoLineageEntries",
    "NoUsableProjectionSource",
    "ProjectionLineageConflict",
    "ProjectionLineageRepository",
    "SourceOrderConflict",
    "validate_artifact_lineage_consistency",
    "validate_lineage_completeness",
    "validate_lineage_source",
    "validate_source_order",
]
