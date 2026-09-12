"""SENSOR-B4-I05C/I05R1C/I05R2A — projection lineage repository.

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

I05R2 §9-§14: a commit-capable lineage repository has NO optional proof
dependencies.  ``blob_store``, ``blob_metadata_repository``,
``acquisition_repository``, ``artifact_repository`` and
``context_repository`` are MANDATORY constructor dependencies; there is no
conditional branch that skips artifact source-list agreement or projection
context identity matching.  The referenced projection MUST have a committed
``RawProjectionArtifact`` (§11) and a committed ``ProjectionCatalogRecord``
(§12) BEFORE any lineage publication.

Production commits read durable repositories only (§12); dictionary-based
helpers remain for unit tests.
"""

from __future__ import annotations

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


class ProjectionArtifactMissing(LineageError):
    """Lineage references a projection_id with no committed artifact (I05R2 §11)."""


class ProjectionContextMissing(LineageError):
    """Lineage references a projection_id with no committed context (I05R2 §12)."""


class LineageContextBindingConflict(LineageError):
    """commit lineage_manifest_id disagrees with the context's authoritative
    lineage_manifest_id for the same projection (I05R3 §3/§4).

    A projection has EXACTLY ONE authoritative lineage manifest; a second
    lineage identity must not poison an already-valid projection.
    """


class LineageProjectionIdentityConflict(LineageError):
    """Multiple committed lineage manifests claim one projection_id
    (I05R3 §6) — corrupt/tampered state; never silently pick one."""


class LineageConfigurationError(LineageError):
    """A commit-capable lineage repository was constructed incompletely."""


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
    is_usable_predicate: Any,
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
# Projection lineage repository — enforcing, durable, immutable, SEALED
# ---------------------------------------------------------------------------


# Sentinel for omitted mandatory dependencies: lets the constructor raise
# the TYPED configuration error (I05R2 §10) instead of a bare TypeError,
# while remaining a mandatory keyword in every realistic call.
_MISSING = object()


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

    I05R2 §9-§14: ALL proof dependencies are MANDATORY constructor
    arguments.  There is no metadata-only or dependency-starved commit
    path: artifact existence (§11), context existence (§12), artifact
    source-list agreement (§13) and provider/venue/sensor/instrument
    identity (§14) are ALWAYS enforced before durable publication.
    """

    def __init__(
        self,
        catalog_root: Path,
        *,
        blob_store: Any = _MISSING,
        blob_metadata_repository: Any = _MISSING,
        acquisition_repository: Any = _MISSING,
        artifact_repository: Any = _MISSING,
        context_repository: Any = _MISSING,
    ) -> None:
        # I05R2 §10: no optional enforcement.  A commit-capable lineage
        # repository is born with its complete proof-dependency set; a
        # missing dependency is a construction-time typed failure, never a
        # silent skip at commit time.
        if blob_store is _MISSING or blob_store is None:
            raise LineageConfigurationError(
                "ProjectionLineageRepository requires blob_store"
            )
        if (
            blob_metadata_repository is _MISSING
            or blob_metadata_repository is None
        ):
            raise LineageConfigurationError(
                "ProjectionLineageRepository requires "
                "blob_metadata_repository"
            )
        if (
            acquisition_repository is _MISSING
            or acquisition_repository is None
        ):
            raise LineageConfigurationError(
                "ProjectionLineageRepository requires "
                "acquisition_repository"
            )
        if (
            artifact_repository is _MISSING
            or artifact_repository is None
        ):
            raise LineageConfigurationError(
                "ProjectionLineageRepository requires "
                "artifact_repository (lineage may not publish without "
                "artifact agreement — I05R2 §11)"
            )
        if (
            context_repository is _MISSING
            or context_repository is None
        ):
            raise LineageConfigurationError(
                "ProjectionLineageRepository requires "
                "context_repository (lineage may not publish without "
                "context identity — I05R2 §12)"
            )
        self._root = Path(catalog_root)
        self._blob_store = blob_store
        self._blob_metadata_repository = blob_metadata_repository
        self._acquisitions = acquisition_repository
        self._artifact_repository = artifact_repository
        self._context_repository = context_repository
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
        owners: dict[str, str] = {}
        for logical_id in self._catalog.list_ids():
            payload = self._catalog.get(logical_id)
            assert payload is not None
            self._cache[logical_id] = self._parse_fragment(payload)
        # I05R3 §6 load invariant: at most ONE committed lineage manifest
        # may claim a given projection_id.  This should be impossible after
        # I05R3, but protects against legacy/tampered disk — fail closed,
        # never silently pick one.
        for lmid, entries in self._cache.items():
            pid = entries[0].projection_id
            previous = owners.get(pid)
            if previous is not None:
                raise LineageProjectionIdentityConflict(
                    f"lineage manifests {previous!r} and {lmid!r} both claim "
                    f"projection_id={pid!r}; a projection has exactly one "
                    "authoritative lineage manifest"
                )
            owners[pid] = lmid

    # -- durable source verification (I05R1 §11/§13/§48 + I05R2 §14) ---------

    def _verify_source_pair(
        self,
        entry: ProjectionLineage,
        context: Any,
    ) -> None:
        """Prove one lineage source against durable T0A truth + context.

        ``context`` is MANDATORY (I05R2 §12): provider/venue/sensor/
        instrument identity matching is unconditional (§14 — it lives in
        the real commit path, not only the later resolver).
        """
        blob_sha = entry.source_blob_sha256
        acq_id = entry.source_acquisition_id

        # Durable blob metadata + PHYSICAL verification (no metadata-only proof).
        metas = self._blob_metadata_repository.get_blob_metadata(blob_sha)
        if not metas:
            raise ProjectionLineageConflict(
                f"lineage source_blob_sha256={blob_sha!r} has no durable "
                "EvidenceBlob metadata"
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

        # Identity matching against the projection context (I05R2 §14 —
        # ALWAYS, never conditional on an optional dependency).
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
        # bounds (§18).  Content conflict fails fast; identical content
        # falls through to FULL re-validation below — idempotence is NOT
        # permission to trust stale evidence (I05R3 §9/§10).
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

        # I05R2 §11: the projection MUST have a committed artifact BEFORE
        # lineage publication.  Missing artifact = typed failure, never
        # "no artifact consistency rule applicable".  Re-proven on EVERY
        # commit, idempotent or not (I05R3 §10).
        artifact = self._artifact_repository.get(pid)
        if artifact is None:
            raise ProjectionArtifactMissing(
                f"projection_id={pid!r} has no committed "
                "RawProjectionArtifact; lineage may not publish without "
                "artifact agreement (I05R2 §11)"
            )

        # I05R2 §13: artifact source-list agreement is UNCONDITIONAL.
        validate_artifact_lineage_consistency(
            list(artifact.source_blob_sha256), entries
        )

        # I05R2 §12: the projection MUST have a committed context BEFORE
        # lineage publication.  No context = no scientific lineage commit.
        context = self._context_repository.get(pid)
        if context is None:
            raise ProjectionContextMissing(
                f"projection_id={pid!r} has no committed "
                "ProjectionCatalogRecord; provider/venue/sensor/instrument "
                "identity checks are mandatory (I05R2 §12)"
            )

        # I05R3 §3/§4: the THREE-WAY binding must hold — commit argument ==
        # every entry's lineage_manifest_id == context.lineage_manifest_id.
        # A projection has exactly ONE authoritative lineage manifest; a
        # second lineage identity may not poison an already-valid projection.
        if context.lineage_manifest_id != lmid:
            raise LineageContextBindingConflict(
                f"lineage_manifest_id={lmid!r} does not match the context's "
                f"authoritative lineage_manifest_id="
                f"{context.lineage_manifest_id!r} for projection "
                f"{pid!r}; one projection has exactly one authoritative "
                "lineage manifest (I05R3 §4)"
            )

        # T0A source truth + identity matching, per entry, BEFORE publication
        # and before ANY idempotent success (I05R3 §10).
        for entry in sorted(entries, key=lambda e: e.source_order):
            self._verify_source_pair(entry, context)

        # Fully re-validated — only NOW may the idempotent existing manifest
        # be returned as current truth (I05R3 §10).
        if lmid in self._cache:
            return self._cache[lmid]

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
        """Retrieve lineage entries for a projection_id (ordered).

        I05R3 §7: a projection resolves to EXACTLY ONE lineage manifest.
        Zero manifests -> empty list.  More than one manifest claiming the
        projection -> typed corruption (never concatenate competing
        manifests into one truth).
        """
        owners: list[str] = []
        result: list[ProjectionLineage] = []
        for lmid, entries in self._cache.items():
            if entries and entries[0].projection_id == projection_id:
                owners.append(lmid)
                result.extend(entries)
        if len(owners) > 1:
            raise LineageProjectionIdentityConflict(
                f"lineage manifests {sorted(owners)!r} all claim "
                f"projection_id={projection_id!r}; a projection has exactly "
                "one authoritative lineage manifest"
            )
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
    "LineageConfigurationError",
    "LineageContextBindingConflict",
    "LineageError",
    "LineageManifestBindingConflict",
    "LineageManifestNotFound",
    "LineageProjectionIdentityConflict",
    "NoLineageEntries",
    "NoUsableProjectionSource",
    "ProjectionArtifactMissing",
    "ProjectionContextMissing",
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
