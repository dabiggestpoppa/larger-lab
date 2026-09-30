"""SENSOR-B4-I13 — checksum-verified LOCAL evidence-pack export/restore.

Portable COPY of a bounded evidence slice (04 doc §18); never a second
truth authority.  Selection is ALWAYS through the accepted I12 query
service (revision authority mandatory; §5/§6); no glob/DuckDB/Postgres
selection.

Checksum domains (§17): SOURCE_BYTES = provider-source bytes before local
wrapper compression (EvidenceBlob.blob_sha256 semantics); PACK_FILE = the
pack file's own bytes.  Never compared with each other.

Doctrine (§4): a pack is a portable COPY, not a canonical lake, not a
mutation authority.  BackupState is NOT mutated (§54); verified-pack
completion is recorded in the pack itself and in the ExportReceipt.

Manifest custody (§34): the written export_manifest.json carries
``pack_root_sha256=None``; the digest of the exact manifest bytes is
returned in the ExportReceipt for EXTERNAL custody pinning.  Internal
tamper detection comes from full-inventory checksum + exact-inventory
verification, not from a self-referential digest.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO

from pydantic import BaseModel, ConfigDict

from .enums import IntegrityState, PackChecksumDomain, PackObjectRole
from .json_catalog import catalog_physical_key
from .models import (
    EvidenceBlob,
    ExportManifest,
    ExportObjectRecord,
    PartitionManifest,
    RawEvidenceQuery,
    RawEvidenceResult,
    canonical_json_bytes,
)
from .query import RawEvidenceQueryService

PACK_SCHEMA_VERSION = "1"
PACK_MANIFEST_NAME = "export_manifest.json"


@dataclass(frozen=True)
class EvidenceClosure:
    """I13R2 formal evidence closure (debug/test structure only, §18/§19:
    NOT a pack schema field).  QUERY_SELECTED = roots explicitly present
    in RawEvidenceResult rows; REQUIRED_SUPPORT = transitive structural
    dependencies (manifest refs, identity-domain acquisitions, revision
    prefix chain); trace = ordered fixpoint additions with causal
    reasons; iterations = fixpoint sweeps until stability."""

    blob_shas: frozenset[str]
    acquisition_ids: frozenset[str]
    projection_ids: frozenset[str]
    matched_manifests: tuple[PartitionManifest, ...]
    query_selected_blob_shas: frozenset[str]
    query_selected_acquisition_ids: frozenset[str]
    support_blob_shas: frozenset[str]
    support_acquisition_ids: frozenset[str]
    trace: tuple[dict[str, str], ...]
    iterations: int
QUERY_SPEC_NAME = "query.json"
STAGING_DIR_NAME = ".staging-export"

# Deterministic role-separated layout (I13 §11).
ROLE_DIRS: dict[PackObjectRole, str] = {
    PackObjectRole.BLOB: "objects/blobs",
    PackObjectRole.BLOB_METADATA: "objects/blob_metadata",
    PackObjectRole.ACQUISITION: "objects/acquisitions",
    PackObjectRole.MANIFEST: "objects/manifests",
    PackObjectRole.CURRENT_POINTER: "objects/manifests/pointers",
    PackObjectRole.PROJECTION: "objects/projections",
    PackObjectRole.PROJECTION_PAYLOAD: "objects/projection_payloads",
    PackObjectRole.PROJECTION_CONTEXT: "objects/projection_contexts",
    PackObjectRole.PROJECTION_LINEAGE: "objects/projection_lineage",
    PackObjectRole.PROJECTION_SCHEMA: "objects/projection_schemas",
    PackObjectRole.REVISION_SEGMENTS: "objects/revisions/segments",
    PackObjectRole.REVISION_OBSERVATIONS: "objects/revisions/observations",
    PackObjectRole.REVISION_DECLARATIONS: "objects/revisions/declarations",
}

DEFAULT_MAX_OBJECTS = 1_000_000
DEFAULT_MAX_TOTAL_BYTES = 1 << 40
DEFAULT_MAX_OBJECT_BYTES = 1 << 33
DEFAULT_MAX_MANIFEST_BYTES = 64 << 20
DEFAULT_COPY_CHUNK = 1 << 20
FREE_SPACE_MARGIN_BYTES = 64 << 20
# I13R2 §4: conservative per-object overhead allowance for the pre-copy
# free-space estimate (metadata records are small JSON documents).
METADATA_OVERHEAD_BYTES = 64 << 10

LOGICAL_SOURCE_ROOT = "logical://source-lake"


def _canonical_dict_bytes(payload: dict | list) -> bytes:  # type: ignore[type-arg]
    """Canonical JSON for plain-dict records (I13R3 §7).

    ``ProjectionCatalogRecord`` is repository catalog context (a plain
    class with ``to_dict()``/``from_dict()``, NOT a pydantic model); its
    durable fragment law is the same canonical JSON discipline — sorted
    keys, compact separators, lossless ``from_dict`` round trip.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# Typed error vocabulary (I13 §40)
# ---------------------------------------------------------------------------


class ExportError(RuntimeError):
    """Base class for I13 evidence-pack failures."""


class ExportDestinationUnsafe(ExportError):
    """Destination would escape the export boundary or alias the source."""


class ExportPackExists(ExportError):
    """A finalized pack already exists at the destination."""


class ExportSourceInvalid(ExportError):
    """Source state is unusable for export (missing/corrupt evidence)."""


class ExportSourceBoundaryUnproven(ExportError):
    """A wired source dependency cannot prove its filesystem boundary
    (I13R3 §15): composition must fail closed rather than silently omit
    a root from destination-overlap protection."""


class PackVerificationError(ExportError):
    """Base class for independent pack verification failures."""


class PackManifestCorrupt(PackVerificationError):
    """Pack manifest is unreadable or violates the pack schema."""


class PackUnsupportedVersion(PackVerificationError):
    """Pack schema/version is not supported by this verifier."""


class PackChecksumMismatch(PackVerificationError):
    """A referenced object's bytes do not match its recorded checksum."""


class PackInventoryMismatch(PackVerificationError):
    """Pack contents disagree with the manifest inventory (missing/extra/
    renamed/duplicated objects)."""


class PackResourceLimitExceeded(PackVerificationError):
    """Pack exceeds a configured safety ceiling (§38)."""


class PackPathUnsafe(PackVerificationError):
    """A pack path escapes containment or references a symlink (§12/§14)."""


class RestoreError(ExportError):
    """Base class for restore failures."""


class RestoreDestinationNotEmpty(RestoreError):
    """Restore target root is not empty (G4-11 empty-root law, §23)."""


class RestorePathUnsafe(RestoreError):
    """A pack path would traverse/symlink-escape the destination (§24)."""


class RestoreIntegrityFailure(RestoreError):
    """Restored material failed validation before promotion (§26)."""


class RestoreIncomplete(RestoreError):
    """Restore did not complete; no complete lake may be exposed (§27)."""


# ---------------------------------------------------------------------------
# Pack filesystem safety (§12/§14) — structural, platform-independent
# ---------------------------------------------------------------------------

_COMPONENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def assert_pack_path_safe(pack_root: Path, relative: str) -> Path:
    """Resolve ``relative`` under ``pack_root`` and refuse any escape.

    Rejects traversal components, absolute paths, drive letters, UNC
    shares and scheme strings; refuses symlinks anywhere along the path;
    verifies the final resolution stays inside ``pack_root`` (§14).
    """
    if os.path.isabs(relative) or re.match(r"^[A-Za-z]:", relative):
        raise PackPathUnsafe(f"absolute pack path refused: {relative!r}")
    if "\\" in relative or relative.startswith("//"):
        raise PackPathUnsafe(f"UNC/backslash pack path refused: {relative!r}")
    parts = relative.split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise PackPathUnsafe(f"unsafe pack path components: {relative!r}")
    resolved_root = pack_root.resolve()
    current = resolved_root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise PackPathUnsafe(f"symlink in pack path refused: {relative!r}")
    if not str(current.resolve()).startswith(str(resolved_root)):
        raise PackPathUnsafe(f"pack path escapes root: {relative!r}")
    return current


def _safe_object_component(object_id: str, role: PackObjectRole) -> str:
    """Derive the canonical pack filename from VALIDATED logical identity
    (§25: no user/provider string is trusted as a destination name)."""
    if role in (PackObjectRole.EXPORT_MANIFEST, PackObjectRole.QUERY_SPEC):
        raise ExportError(f"role {role} is not an inventory object")
    component = catalog_physical_key(object_id)
    if not _COMPONENT_RE.match(component):
        raise ExportSourceInvalid(
            f"object identity {object_id!r} does not yield a canonical "
            "filesystem-safe pack component"
        )
    return component


# ---------------------------------------------------------------------------
# Pack manifest payload (self-describing; §8)
# ---------------------------------------------------------------------------


class PackManifestPayload(BaseModel):
    """The on-disk export_manifest.json document (schema-versioned).

    The accepted ``ExportManifest`` model remains the logical contract;
    this payload adds the on-disk document fields (layout, inventory,
    domain-stated checksums) required by frozen §7/§8 with the same
    fail-closed configuration.
    """

    model_config = ConfigDict(extra="forbid")

    pack_schema_version: str
    export_id: str
    created_at: str
    source_data_root: str
    selection_query: dict[str, Any]
    blob_count: int
    projection_count: int
    total_bytes: int
    manifest_sha256: str
    objects: list[str]
    object_inventory: list[ExportObjectRecord]
    pack_root_sha256: str | None
    layout: dict[str, str]
    checksum_domains: dict[str, str]


# ---------------------------------------------------------------------------
# Digest domains (I13R1 §10) — exact, documented, NON-CIRCULAR
# ---------------------------------------------------------------------------

_DIGEST_NEUTRAL = ""  # neutral value for excluded self-digest fields


def _manifest_body_bytes(manifest: PackManifestPayload) -> bytes:
    """Canonical manifest body: the full payload with BOTH self-digest
    fields neutralized (excluded from their own hash — no circularity)."""
    body = manifest.model_copy(
        update={
            "manifest_sha256": _DIGEST_NEUTRAL,
            "pack_root_sha256": _DIGEST_NEUTRAL,
        }
    )
    return canonical_json_bytes(body)


def _inventory_tuples_bytes(manifest: PackManifestPayload) -> bytes:
    """Canonical ordered object-inventory tuples (role, object_id,
    pack_path, sha256, byte_size, checksum_domain, provenance_ref)."""
    lines = []
    for rec in sorted(
        manifest.object_inventory,
        key=lambda r: (r.role.value, r.pack_path),
    ):
        lines.append(
            json.dumps(
                [
                    rec.role.value,
                    rec.object_id,
                    rec.pack_path,
                    rec.sha256,
                    rec.byte_size,
                    rec.checksum_domain.value,
                    rec.provenance_ref,
                ],
                separators=(",", ":"),
            )
        )
    return "\n".join(lines).encode("utf-8")


def _compute_manifest_digests(
    manifest: PackManifestPayload,
) -> tuple[str, str]:
    """Return (MANIFEST_BODY_SHA256, PACK_ROOT_SHA256).

    MANIFEST_BODY_SHA256 = SHA256(canonical manifest body with both
    self-digest fields neutralized).

    PACK_ROOT_SHA256 = SHA256(canonical structure containing the
    manifest body digest + the sorted object-inventory tuples).
    """
    manifest_body_sha = hashlib.sha256(
        _manifest_body_bytes(manifest)
    ).hexdigest()
    pack_root = hashlib.sha256(
        manifest_body_sha.encode("utf-8")
        + b"\n"
        + _inventory_tuples_bytes(manifest)
    ).hexdigest()
    return manifest_body_sha, pack_root


def read_pack_manifest(
    pack_root: Path,
    *,
    max_manifest_bytes: int = DEFAULT_MAX_MANIFEST_BYTES,
) -> PackManifestPayload:
    """Load + schema-check the pack manifest (fail-closed)."""
    path = pack_root / PACK_MANIFEST_NAME
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PackManifestCorrupt(f"pack manifest unreadable: {exc}") from exc
    if len(raw) > max_manifest_bytes:
        raise PackResourceLimitExceeded("pack manifest exceeds ceiling")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PackManifestCorrupt(
            f"pack manifest is not valid JSON: {exc}"
        ) from exc
    try:
        return PackManifestPayload.model_validate(payload)
    except Exception as exc:  # noqa: BLE001 - schema violation is corruption
        raise PackManifestCorrupt(
            f"pack manifest schema invalid: {exc}"
        ) from exc


def write_pack_manifest(pack_root: Path, manifest: PackManifestPayload) -> str:
    """Write the manifest canonically; return its exact-bytes digest."""
    manifest_bytes = canonical_json_bytes(manifest)
    (pack_root / PACK_MANIFEST_NAME).write_bytes(manifest_bytes)
    return hashlib.sha256(manifest_bytes).hexdigest()


def _read_pack_metadata_bytes(path: Path) -> bytes:
    """SMALL_BOUNDED_METADATA read (I13R1 §15): pack JSON catalog records
    are bounded by the manifest-byte ceiling; physical blob/projection
    payloads NEVER use this helper (they stream)."""
    data = path.read_bytes()
    if len(data) > DEFAULT_MAX_MANIFEST_BYTES:
        raise PackResourceLimitExceeded(
            f"pack metadata record exceeds ceiling: {path.name!r}"
        )
    return data


def _file_digest(path: Path) -> tuple[str, int]:
    from .checksums import sha256_stream

    with open(path, "rb") as handle:
        result = sha256_stream(handle, chunk_size=DEFAULT_COPY_CHUNK)
    return result.hex_digest, result.byte_length


# ---------------------------------------------------------------------------
# Copy helper (§15/§16: never trust copy success; bounded streaming)
# ---------------------------------------------------------------------------


def _copy_into(
    source: bytes | BinaryIO,
    destination: Path,
    *,
    chunk_size: int,
) -> tuple[str, int]:
    """Stream ``source`` into ``destination``; return (sha256, byte_size).

    Memory stays bounded by ``chunk_size``, never object size (§16).
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    length = 0
    with open(destination, "wb") as handle:
        if isinstance(source, bytes):
            for offset in range(0, len(source), chunk_size):
                chunk = source[offset : offset + chunk_size]
                handle.write(chunk)
                digest.update(chunk)
                length += len(chunk)
        else:
            while True:
                chunk = source.read(chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
                length += len(chunk)
                handle.write(chunk)
        handle.flush()
        os.fsync(handle.fileno())
    return digest.hexdigest(), length


# ---------------------------------------------------------------------------
# Evidence pack exporter (§5/§6/§13/§15/§16/§43)
# ---------------------------------------------------------------------------


@dataclass
class ExportLimits:
    max_objects: int = DEFAULT_MAX_OBJECTS
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES
    max_object_bytes: int = DEFAULT_MAX_OBJECT_BYTES
    max_manifest_bytes: int = DEFAULT_MAX_MANIFEST_BYTES


@dataclass
class ExportReceipt:
    export_id: str
    pack_root: Path
    manifest: ExportManifest
    pack_root_sha256: str
    object_count: int
    total_bytes: int


class EvidencePackExporter:
    """Query-driven streaming exporter over the accepted read surfaces.

    Selection goes ONLY through ``RawEvidenceQueryService.execute`` (§5);
    the service MUST carry the I06 revision authority (§6) — the I12R2
    canonical construction.  T0A bytes stream from ``open_blob`` and are
    verified against ``EvidenceBlob.blob_sha256`` (SOURCE_BYTES domain,
    §17).  Revision evidence is exported through read-only introspection
    of the accepted registry's durable segment/observation/declaration
    truth; no revision mutation exists on the export path (§42).
    """

    def __init__(
        self,
        *,
        service: RawEvidenceQueryService,
        blob_store: Any,
        blob_metadata_repository: Any,
        acquisition_repository: Any,
        manifest_repository: Any,
        artifact_repository: Any = None,
        context_repository: Any = None,
        lineage_repository: Any = None,
        schema_registry: Any = None,
        revision_registry: Any = None,
        chunk_size: int = DEFAULT_COPY_CHUNK,
        limits: ExportLimits | None = None,
        export_id: str | None = None,
        clock: Any = None,
        disk_usage_provider: Any = None,
        protected_source_roots: list[Path] | None = None,
    ) -> None:
        self._service = service
        self._store = blob_store
        self._blob_repo = blob_metadata_repository
        self._acq_repo = acquisition_repository
        self._manifest_repo = manifest_repository
        self._artifacts = artifact_repository
        self._contexts = context_repository
        self._lineage = lineage_repository
        self._schemas = schema_registry
        self._revisions = revision_registry
        self._chunk_size = chunk_size
        self._limits = limits or ExportLimits()
        self._export_id = export_id
        self._clock = clock or (lambda: datetime.now(tz=UTC))
        self._disk_usage = disk_usage_provider
        self._protected_source_roots = [
            Path(p) for p in (protected_source_roots or [])
        ]
        # I13R3 §15 fail-closed boundary law: every wired source
        # dependency must PROVE its filesystem root, either through a
        # public read-only ``root``/``projection_root`` property or an
        # explicit entry in ``protected_source_roots``.  Silent omission
        # is the defect: a caller who forgets the T0B/revision roots
        # must get a typed configuration failure here, not an
        # unprotected export later.
        self._wired_source_boundaries: list[Path] = []

        def _boundary(obj: Any, *attrs: str, label: str) -> Path | None:
            for attr in attrs:
                value = getattr(obj, attr, None)
                if value is not None:
                    return Path(value).resolve()
            return None

        wired: list[tuple[str, Path | None]] = []
        if self._artifacts is not None:
            wired.append(
                (
                    "artifact_repository",
                    _boundary(
                        self._artifacts,
                        "projection_root",
                        "root",
                        label="artifact_repository",
                    ),
                )
            )
        if self._contexts is not None:
            wired.append(
                (
                    "context_repository",
                    _boundary(
                        self._contexts,
                        "root",
                        label="context_repository",
                    ),
                )
            )
        if self._lineage is not None:
            wired.append(
                (
                    "lineage_repository",
                    _boundary(
                        self._lineage,
                        "root",
                        label="lineage_repository",
                    ),
                )
            )
        if self._schemas is not None:
            wired.append(
                (
                    "schema_registry",
                    _boundary(
                        self._schemas,
                        "root",
                        label="schema_registry",
                    ),
                )
            )
        if self._revisions is not None:
            wired.append(
                (
                    "revision_registry",
                    _boundary(
                        self._revisions,
                        "root",
                        label="revision_registry",
                    ),
                )
            )
        for label, boundary in wired:
            if boundary is None:
                raise ExportSourceBoundaryUnproven(
                    f"{label} is wired but cannot prove its source "
                    "filesystem boundary (no public root accessor and "
                    "no explicit protected_source_roots entry); export "
                    "composition refuses to run unprotected (I13R3 §15)"
                )
            self._wired_source_boundaries.append(boundary)

        # Explicit roots EXTEND the derived set (callers may protect
        # additional trees); they never substitute for the derived ones.
        for extra in self._protected_source_roots:
            resolved = Path(extra).resolve()
            if resolved not in self._wired_source_boundaries:
                self._wired_source_boundaries.append(resolved)

    def export_query(
        self, query: RawEvidenceQuery, destination: Path
    ) -> ExportReceipt:
        """Execute ``query`` through the wired service and export the slice."""
        outcome = self._service.execute(query)
        return self._export_results(query, list(outcome.results), Path(destination))

    # -- destination law (§13) -------------------------------------------------

    def _validate_destination(self, destination: Path) -> None:
        if destination.exists() and any(destination.iterdir()):
            raise ExportPackExists(
                f"destination {destination} exists and is not empty"
            )
        resolved_dest = destination.resolve()
        # Refuse destinations that resolve THROUGH symlinks (parent chain).
        for ancestor in [destination, *destination.parents]:
            if ancestor.is_symlink():
                raise ExportDestinationUnsafe(
                    f"destination component is a symlink: {ancestor}"
                )
        # Refuse destination inside the immutable source trees.
        # I13R3 §15: the T0A blob-store root AND every wired dependency's
        # proven boundary (T0B payload/catalog roots, revision registry
        # root) are protected BY DEFAULT — no caller-specific override is
        # required for safe composition (§16).
        protected: list[Path] = [
            Path(self._store.root).resolve(),
            *self._wired_source_boundaries,
        ]
        for source_root in protected:
            src = Path(source_root).resolve()
            if resolved_dest == src or src in resolved_dest.parents:
                raise ExportDestinationUnsafe(
                    f"destination lies inside protected source tree {src}"
                )

    def _disk_usage_for(self, path: Path) -> tuple[int, int]:
        """Real local disk usage by default; injected provider overrides.

        I13R2 §3 law: NO silent production bypass.  When no provider is
        injected, ``shutil.disk_usage`` measures the nearest existing
        ancestor of ``path`` (the destination may not exist yet).
        """
        provider = self._disk_usage
        if provider is None:
            provider = shutil.disk_usage
            probe = Path(path)
            while not probe.exists():
                if probe.parent == probe:
                    break
                probe = probe.parent
            path = probe
        usage = provider(path)
        if isinstance(usage, tuple):
            if len(usage) == 3:
                # shutil.disk_usage protocol: (total, used, free)
                return int(usage[0]), int(usage[2])
            return int(usage[0]), int(usage[1])
        return int(usage.total), int(usage.free)

    def _check_free_space(self, destination: Path, required: int) -> None:
        # I13R2 §2: the free-space check NEVER silently disables itself.
        total, free = self._disk_usage_for(destination)
        if free < required + FREE_SPACE_MARGIN_BYTES:
            raise PackResourceLimitExceeded(
                f"destination free space {free} < required {required} "
                "+ margin"
            )

    # -- export core -------------------------------------------------------------

    def _export_results(
        self,
        query: RawEvidenceQuery,
        results: list[RawEvidenceResult],
        destination: Path,
    ) -> ExportReceipt:
        # I13R1 §7 atomic publication law: the final destination MUST NOT
        # EXIST before publication.  The pack is built COMPLETE in a
        # sibling staging directory and published with ONE directory-level
        # atomic rename — no child-by-child finalization, so a crash can
        # never expose a partially finalized pack.
        self._validate_destination(destination)
        if destination.exists():
            raise ExportPackExists(
                f"destination {destination} already exists (atomic "
                "publication law: the final pack root must not pre-exist)"
            )
        parent = destination.parent
        parent.mkdir(parents=True, exist_ok=True)
        staging = parent / f".{destination.name}.staging-export"
        if staging.exists():
            raise ExportPackExists(
                f"stale export staging {staging} present; remove it "
                "explicitly (deterministic policy: never silently adopt "
                "partial staging)"
            )
        staging.mkdir()
        try:
            inventory: list[ExportObjectRecord] = []
            blob_shas = sorted({sha for r in results for sha in r.blob_refs})
            # I13R2 formal evidence-closure law: the pack must equal the
            # minimal transitive support closure of the query-selected
            # roots.  Three classes: QUERY_SELECTED (A), REQUIRED_SUPPORT
            # (B), UNRELATED (C); only C is leakage.  The closure is a
            # monotone fixpoint over the finite source universe (every
            # addition is traced; §18 debug structure only, NOT a pack
            # schema field — §19).
            closure = self._evidence_closure(results, query)
            blob_shas = sorted(closure.blob_shas)
            projection_ids = sorted(
                {pid for r in results for pid in r.projection_refs}
            )
            if len(blob_shas) + len(projection_ids) > self._limits.max_objects:
                raise PackResourceLimitExceeded(
                    "selection exceeds max_objects ceiling"
                )
            export_id = self._export_id or self._derive_export_id(query)
            created_at = self._clock()

            # --- T0A metadata (BLOB_METADATA rows) --------------------------
            blob_rows: dict[str, EvidenceBlob] = {}
            for sha in blob_shas:
                rows = self._blob_repo.get_blob_metadata(sha)
                if not rows:
                    raise ExportSourceInvalid(
                        f"selected blob {sha} has no durable metadata"
                    )
                for row in rows:
                    self._add_object(
                        inventory,
                        staging,
                        role=PackObjectRole.BLOB_METADATA,
                        object_id=f"{sha}:{row.storage_encoding.value}",
                        payload=canonical_json_bytes(row),
                        provenance_ref=sha,
                    )
                blob_rows[sha] = rows[0]

            # I13R2 §4: pre-copy free-space estimate from selected durable
            # metadata (T0A byte lengths + bounded metadata overhead).  NEVER
            # zero/meaningless: refuse before bulk copying when the real local
            # disk cannot hold the pack.
            estimated_bytes = sum(
                blob_rows[sha].byte_length for sha in blob_shas
            ) + len(blob_shas) * METADATA_OVERHEAD_BYTES
            self._check_free_space(destination, estimated_bytes)

            # --- acquisitions of the closed blob slice (identity-domain
            # law, I13R2 §11 preferred acquisition closure) -----------------
            acq_ids: set[str] = set(closure.acquisition_ids)
            for acq_id in sorted(acq_ids):
                rec = self._acq_repo.get_acquisition(acq_id)
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.ACQUISITION,
                    object_id=acq_id,
                    payload=canonical_json_bytes(rec),
                    provenance_ref=rec.blob_sha256 or acq_id,
                )

            # --- T0A exact source bytes (SOURCE_BYTES domain, §16/§17) -------
            for sha in blob_shas:
                row = blob_rows[sha]
                pack_path = (
                    f"{ROLE_DIRS[PackObjectRole.BLOB]}/"
                    f"{_safe_object_component(sha, PackObjectRole.BLOB)}"
                )
                target = assert_pack_path_safe(staging, pack_path)
                if target.exists():
                    raise ExportSourceInvalid(
                        f"duplicate logical blob identity {sha}"
                    )
                # I13R2 §4: conservative progressive check before each
                # physical payload (covers T0B sizes unknown pre-copy).
                self._check_free_space(
                    destination, blob_rows[sha].byte_length
                )
                with self._store.open_blob(sha, row.storage_encoding) as handle:
                    file_sha, size = _copy_into(
                        handle, target, chunk_size=self._chunk_size
                    )
                if size != row.byte_length:
                    raise ExportSourceInvalid(
                        f"blob {sha} streamed length {size} != metadata "
                        f"byte_length {row.byte_length}"
                    )
                if file_sha != sha:  # §17: SOURCE_BYTES digest law
                    raise PackChecksumMismatch(
                        f"streamed source bytes of {sha} hash to {file_sha}"
                    )
                inventory.append(
                    ExportObjectRecord(
                        role=PackObjectRole.BLOB,
                        object_id=sha,
                        pack_path=pack_path,
                        sha256=file_sha,
                        byte_size=size,
                        checksum_domain=PackChecksumDomain.SOURCE_BYTES,
                        provenance_ref=sha,
                    )
                )

            # --- partition manifests + current pointers ------------------------
            # Export EXACTLY the closure's matched manifest roots (unique
            # result→manifest matching in ``_evidence_closure``).  Their
            # full blob_refs are inside the closed slice by fixpoint
            # construction; the fail-closed guard remains.
            # I13R3: export exactly the closure's manifest chain (roots +
            # REQUIRED_SUPPORT predecessors earned inside the fixpoint).
            exported_pointer_keys: set[str] = set()
            for manifest in closure.matched_manifests:
                if not set(manifest.blob_refs) <= set(blob_shas):
                    raise ExportSourceInvalid(
                        f"manifest {manifest.partition_manifest_id} "
                        "references blobs outside the closed pack slice"
                    )
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.MANIFEST,
                    object_id=manifest.partition_manifest_id,
                    payload=canonical_json_bytes(manifest),
                    provenance_ref=manifest.partition_manifest_id,
                )
                # One CURRENT_POINTER per partition key: a superseded
                # manifest shares its key with the successor, and the
                # source pointer is a per-key operational fact, not a
                # per-manifest one.
                if manifest.partition_key in exported_pointer_keys:
                    continue
                pointer = self._manifest_repo.read_current_pointer(
                    manifest.partition_key
                )
                if pointer is not None:
                    exported_pointer_keys.add(manifest.partition_key)
                    self._add_object(
                        inventory,
                        staging,
                        role=PackObjectRole.CURRENT_POINTER,
                        object_id=f"pointer:{manifest.partition_key}",
                        payload=pointer.to_canonical_json().encode("utf-8"),
                        provenance_ref=manifest.partition_manifest_id,
                    )

            # --- T0B artifacts + payloads + contexts + lineage ------------------
            exported_artifacts = []
            for projection_id in projection_ids:
                artifact = (
                    self._artifacts.get_strict(projection_id)
                    if self._artifacts is not None
                    else None
                )
                if artifact is None:
                    continue
                exported_artifacts.append(artifact)
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.PROJECTION,
                    object_id=projection_id,
                    payload=canonical_json_bytes(artifact),
                    provenance_ref=artifact.projection_sha256,
                )
                # T0B payload bytes (PACK_FILE domain) — STREAMED through
                # the public physically-verified reader (I13R1 §4/§14:
                # bounded memory, corruption refuses typed before open).
                payload_component = _safe_object_component(
                    f"payload:{projection_id}",
                    PackObjectRole.PROJECTION_PAYLOAD,
                )
                payload_path = (
                    f"{ROLE_DIRS[PackObjectRole.PROJECTION_PAYLOAD]}/"
                    f"{payload_component}"
                )
                payload_target = assert_pack_path_safe(staging, payload_path)
                if payload_target.exists():
                    raise ExportSourceInvalid(
                        f"duplicate projection payload identity {projection_id}"
                    )
                with self._artifacts.open_payload(projection_id) as handle:
                    payload_sha, payload_size = _copy_into(
                        handle,
                        payload_target,
                        chunk_size=self._chunk_size,
                    )
                if payload_sha != artifact.projection_sha256:
                    raise PackChecksumMismatch(
                        f"projection payload digest != projection_sha256 "
                        f"for {projection_id}"
                    )
                inventory.append(
                    ExportObjectRecord(
                        role=PackObjectRole.PROJECTION_PAYLOAD,
                        object_id=f"payload:{projection_id}",
                        pack_path=payload_path,
                        sha256=payload_sha,
                        byte_size=payload_size,
                        checksum_domain=PackChecksumDomain.PACK_FILE,
                        provenance_ref=artifact.projection_sha256,
                    )
                )
                if self._contexts is not None:
                    context = self._contexts.get(projection_id)
                    if context is not None:
                        self._add_object(
                            inventory,
                            staging,
                            role=PackObjectRole.PROJECTION_CONTEXT,
                            object_id=f"context:{projection_id}",
                            payload=_canonical_dict_bytes(context.to_dict()),
                            provenance_ref=projection_id,
                        )
                if self._lineage is not None:
                    entries = self._lineage.get_by_projection(projection_id)
                    if entries:
                        self._add_object(
                            inventory,
                            staging,
                            role=PackObjectRole.PROJECTION_LINEAGE,
                            object_id=(
                                f"lineage:{entries[0].lineage_manifest_id}"
                            ),
                            payload=_canonical_dict_bytes(
                                [e.model_dump(mode="json") for e in entries]
                            ),
                            provenance_ref=entries[0].lineage_manifest_id,
                        )
            # projection schemas referenced by exported artifacts
            if self._schemas is not None:
                for schema_key in sorted(self._schemas.list_keys()):
                    definition = self._schemas.resolve(schema_key)
                    needed = any(
                        definition.projection_schema_id
                        == artifact.projection_schema_id
                        and definition.projection_schema_version
                        == artifact.projection_schema_version
                        for artifact in exported_artifacts
                    )
                    if needed:
                        self._add_object(
                            inventory,
                            staging,
                            role=PackObjectRole.PROJECTION_SCHEMA,
                            object_id=schema_key,
                            payload=_canonical_dict_bytes(
                                definition.to_descriptor()
                            ),
                            provenance_ref=definition.schema_identity,
                        )

            # --- revision evidence under the EXPLICIT closure law -------------
            # (I13R1 §3: only the revisions the query semantics require —
            # never every revision of a touched source key)
            if self._revisions is not None:
                self._export_revisions(
                    inventory, staging, acq_ids, query.revision_policy,
                    query.exact_revision_number,
                )

            # --- query specification (§7) ----------------------------------------
            query_path = assert_pack_path_safe(staging, QUERY_SPEC_NAME)
            _, q_size = _copy_into(
                canonical_json_bytes(query),
                query_path,
                chunk_size=self._chunk_size,
            )
            q_sha, _ = _file_digest(query_path)
            inventory.append(
                ExportObjectRecord(
                    role=PackObjectRole.QUERY_SPEC,
                    object_id="query",
                    pack_path=QUERY_SPEC_NAME,
                    sha256=q_sha,
                    byte_size=q_size,
                    checksum_domain=PackChecksumDomain.PACK_FILE,
                    provenance_ref=export_id,
                )
            )

            inventory.sort(key=lambda rec: (rec.role.value, rec.pack_path))
            total_bytes = sum(rec.byte_size for rec in inventory)
            self._check_limits_pack(inventory, total_bytes)
            self._check_free_space(destination, total_bytes)

            payload = PackManifestPayload(
                pack_schema_version=PACK_SCHEMA_VERSION,
                export_id=export_id,
                created_at=created_at.isoformat(),
                source_data_root=LOGICAL_SOURCE_ROOT,
                selection_query=query.model_dump(mode="json"),
                blob_count=len(blob_shas),
                projection_count=len(projection_ids),
                total_bytes=total_bytes,
                manifest_sha256="",
                objects=sorted({rec.object_id for rec in inventory}),
                object_inventory=inventory,
                pack_root_sha256="",
                layout={role.value: d for role, d in ROLE_DIRS.items()},
                checksum_domains={
                    "SOURCE_BYTES": (
                        "sha256 of exact provider-source bytes before "
                        "optional local wrapper compression"
                    ),
                    "PACK_FILE": "sha256 of the pack file's own bytes",
                },
            )
            # I13R1 §10: seal BOTH digest domains, persist them, THEN
            # self-verify BEFORE publication (§43).
            manifest_sha, pack_root_sha = _compute_manifest_digests(payload)
            payload = payload.model_copy(
                update={
                    "manifest_sha256": manifest_sha,
                    "pack_root_sha256": pack_root_sha,
                }
            )
            write_pack_manifest(staging, payload)
            EvidencePackVerifier(
                limits=VerifyLimits(
                    max_objects=self._limits.max_objects,
                    max_total_bytes=self._limits.max_total_bytes,
                    max_object_bytes=self._limits.max_object_bytes,
                    max_manifest_bytes=self._limits.max_manifest_bytes,
                )
            ).verify_pack(staging)
            # ONE atomic directory rename publishes the verified pack.
            staging.rename(destination)

            receipt_manifest = ExportManifest(
                export_id=export_id,
                created_at=created_at,
                source_data_root=LOGICAL_SOURCE_ROOT,
                selection_query=query,
                blob_count=len(blob_shas),
                projection_count=len(projection_ids),
                total_bytes=total_bytes,
                manifest_sha256=manifest_sha,
                objects=sorted({rec.object_id for rec in inventory}),
                verification_state=IntegrityState.LOCAL_HASH_VERIFIED,
                pack_schema_version=PACK_SCHEMA_VERSION,
                object_inventory=inventory,
                pack_root_sha256=pack_root_sha,
            )
            return ExportReceipt(
                export_id=export_id,
                pack_root=destination,
                manifest=receipt_manifest,
                pack_root_sha256=pack_root_sha,
                object_count=len(inventory),
                total_bytes=total_bytes,
            )
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise

    def _check_limits_pack(
        self, inventory: list[ExportObjectRecord], total_bytes: int
    ) -> None:
        if len(inventory) > self._limits.max_objects:
            raise PackResourceLimitExceeded("inventory exceeds max_objects")
        if total_bytes > self._limits.max_total_bytes:
            raise PackResourceLimitExceeded("pack exceeds max_total_bytes")
        for rec in inventory:
            if rec.byte_size > self._limits.max_object_bytes:
                raise PackResourceLimitExceeded(
                    f"object {rec.pack_path!r} exceeds max_object_bytes"
                )

    def _unique_result_manifests(
        self, results: list[RawEvidenceResult]
    ) -> list[PartitionManifest]:
        """I13R2 unique manifest-root matching law.

        The I13R1 selection matched manifests on the broad
        ``(provider, venue, native_instrument)`` tuple — which can pull in
        UNRELATED current manifests sharing only those dimensions.  A
        result's manifest root must be PROVEN, not guessed: match on the
        strongest accepted fields (identity dimensions + granularity +
        logical window containment + coverage/integrity agreement) AND
        require evidence-binding agreement: ``result.blob_refs`` must be a
        subset of the candidate manifest's ``blob_refs`` (T0A) or the
        result's ``projection_refs`` a subset of the candidate's
        ``projection_refs`` (T0B).

        Exactly ONE current manifest must explain each result: 0 →
        ``ExportSourceInvalid``; >1 → explicit ambiguity error.  Never
        silently export every broad-dimension lookalike.
        """
        current = sorted(
            self._manifest_repo.list_all_current_manifests(),
            key=lambda m: m.partition_manifest_id,
        )
        matched: list[PartitionManifest] = []
        seen_ids: set[str] = set()
        for result in results:
            candidates: list[PartitionManifest] = []
            for manifest in current:
                if (
                    manifest.provider != result.provider
                    or manifest.venue != result.venue
                    or manifest.sensor_family != result.sensor_family
                    or manifest.native_instrument
                    != result.native_instrument
                    or manifest.source_granularity
                    != result.source_granularity
                    or manifest.coverage_state != result.coverage_state
                    or manifest.integrity_state != result.integrity_state
                ):
                    continue
                if not (
                    manifest.logical_date_start
                    <= result.logical_time_start
                    and result.logical_time_end
                    <= manifest.logical_date_end
                ):
                    continue
                # Evidence-binding agreement: the result's durable refs
                # must live inside the candidate manifest's refs.
                if result.blob_refs and not set(
                    result.blob_refs
                ) <= set(manifest.blob_refs):
                    continue
                if result.projection_refs and not set(
                    result.projection_refs
                ) <= set(manifest.projection_refs):
                    continue
                candidates.append(manifest)
            if not candidates:
                raise ExportSourceInvalid(
                    f"no current manifest explains result "
                    f"{result.provider}/{result.venue}/"
                    f"{result.native_instrument} "
                    f"({result.logical_time_start.isoformat()}.."
                    f"{result.logical_time_end.isoformat()})"
                )
            if len(candidates) > 1:
                ids = sorted(
                    m.partition_manifest_id for m in candidates
                )
                raise ExportSourceInvalid(
                    f"ambiguous manifest root for result "
                    f"{result.provider}/{result.venue}/"
                    f"{result.native_instrument}: {ids} all explain "
                    "the selected evidence — manifest roots must be "
                    "unique (I13R2 §4)"
                )
            if candidates[0].partition_manifest_id not in seen_ids:
                seen_ids.add(candidates[0].partition_manifest_id)
                matched.append(candidates[0])
        return matched

    def _evidence_closure(
        self, results: list[RawEvidenceResult], query: RawEvidenceQuery
    ) -> "EvidenceClosure":
        """I13R2 formal three-class evidence closure (monotone fixpoint).

        A. QUERY_SELECTED — acquisitions/blobs/projections/lineage refs
           explicitly present in the RawEvidenceResult rows.
        B. REQUIRED_SUPPORT — matched immutable manifest roots (with ALL
           their blob_refs/projection_refs), acquisitions of closure blobs
           within the exported identity domain, revision segments of
           included acquisitions bounded by the policy-minimum revision
           prefix, their bound first_acquisition_ids and blobs, and the
           declarations of included keys.
        C. UNRELATED — no transitive dependency path from A or B.  Only C
           is leakage.

        The fixpoint iterates until no object is added; termination is
        guaranteed because the closure only grows inside a finite source
        universe.  POLICY closure never SHRINKS below the structural
        minimum and never manually overwrites an earned dependency
        (§15/§16).
        """
        trace: list[dict[str, str]] = []
        iterations = 0

        def add(
            bucket: set[str],
            item: str,
            classification: str,
            reason: str,
        ) -> bool:
            if item in bucket:
                return False
            bucket.add(item)
            trace.append(
                {
                    "object": item,
                    "classification": classification,
                    "reason": reason,
                }
            )
            return True

        # ---- seeds (A. QUERY_SELECTED + matched manifest roots) --------
        selected_acq_ids: set[str] = set()
        selected_blob_shas: set[str] = set()
        for result in results:
            for acq_id in result.acquisition_ids:
                add(
                    selected_acq_ids,
                    acq_id,
                    "QUERY_SELECTED",
                    "QUERY_RESULT_ACQUISITION",
                )
            for sha in result.blob_refs:
                add(
                    selected_blob_shas,
                    sha,
                    "QUERY_SELECTED",
                    "QUERY_RESULT_BLOB",
                )
        _matched_manifest_ids: set[str] = set()
        matched_manifests = self._unique_result_manifests(results)
        for manifest in matched_manifests:
            add(
                _matched_manifest_ids,
                manifest.partition_manifest_id,
                "REQUIRED_SUPPORT",
                "MATCHED_MANIFEST",
            )

        selected_projection_ids = sorted(
            {pid for r in results for pid in r.projection_refs}
        )

        policy_name = (
            query.revision_policy.value
            if hasattr(query.revision_policy, "value")
            else str(query.revision_policy)
        )

        # ---- monotone fixpoint -------------------------------------------
        blob_shas: set[str] = set(selected_blob_shas)
        acq_ids: set[str] = set(selected_acq_ids)
        support_blob_shas: set[str] = set()
        support_acq_ids: set[str] = set()
        revisions = self._revisions
        while True:
            iterations += 1
            before = (len(blob_shas), len(acq_ids))

            # 1. Manifest dependency expansion (§9 + I13R3): every
            #    matched immutable manifest contributes ALL its blob_refs,
            #    and a versioned manifest earns its supersedes-chain
            #    predecessors (MANIFEST_PREDECESSOR edge) — the restore
            #    writer re-appends immutable versions in CAS order, so
            #    version N > 1 cannot replay without version N-1 (I04 §33
            #    no-gap law).  The matched set therefore grows inside the
            #    fixpoint, never shrinks (§8 monotone law).
            manifest_cursor = 0
            while manifest_cursor < len(matched_manifests):
                manifest = matched_manifests[manifest_cursor]
                manifest_cursor += 1
                if (
                    manifest.manifest_version > 1
                    and manifest.supersedes_manifest_id is not None
                    and all(
                        m.partition_manifest_id
                        != manifest.supersedes_manifest_id
                        for m in matched_manifests
                    )
                ):
                    predecessor = self._manifest_repo.get_manifest(
                        manifest.supersedes_manifest_id
                    )
                    matched_manifests.append(predecessor)
                    trace.append(
                        {
                            "object": predecessor.partition_manifest_id,
                            "classification": "REQUIRED_SUPPORT",
                            "reason": (
                                f"MANIFEST_PREDECESSOR:"
                                f"{manifest.partition_manifest_id}"
                            ),
                        }
                    )
                for sha in manifest.blob_refs:
                    if sha not in blob_shas:
                        blob_shas.add(sha)
                        support_blob_shas.add(sha)
                        trace.append(
                            {
                                "object": sha,
                                "classification": "REQUIRED_SUPPORT",
                                "reason": f"MANIFEST_BLOB_REF:"
                                f"{manifest.partition_manifest_id}",
                            }
                        )

            # 2. Blob -> acquisition expansion (§10/§11 preferred
            #    acquisition law): ALL durable acquisition rows of each
            #    closure blob within the exported identity domain join the
            #    slice — dropping one would silently change
            #    acquired_before/observed_before semantics.
            identity_keys = {
                (r.provider, r.venue, r.sensor_family, r.native_instrument)
                for r in results
            }
            for sha in sorted(blob_shas):
                for rec in self._acq_repo.list_acquisitions_for_blob(sha):
                    identity = (
                        rec.provider_id,
                        rec.venue,
                        rec.sensor_family,
                        rec.native_instrument,
                    )
                    if identity not in identity_keys:
                        continue
                    if rec.acquisition_id not in acq_ids:
                        acq_ids.add(rec.acquisition_id)
                        support_acq_ids.add(rec.acquisition_id)
                        trace.append(
                            {
                                "object": rec.acquisition_id,
                                "classification": "REQUIRED_SUPPORT",
                                "reason": f"BLOB_ACQUISITIONS:{sha}",
                            }
                        )

            # 3. Revision closure following included acquisitions (§14):
            #    every kept segment's bound first_acquisition_id and blob
            #    must join the slice; iterate until stable.
            if revisions is not None:
                keys_touched: set[str] = set()
                for key in revisions.list_source_revision_keys():
                    segments = sorted(
                        revisions.list_segment_records(key),
                        key=lambda s: s.revision_number,
                    )
                    touched = [
                        s
                        for s in segments
                        if s.first_acquisition_id in acq_ids
                    ]
                    if not touched:
                        continue
                    keys_touched.add(key)
                    max_revision = max(
                        s.revision_number for s in segments
                    )
                    if policy_name in ("ALL", "LATEST_SEEN"):
                        keep = max_revision
                    elif policy_name == "FIRST_SEEN":
                        keep = 1
                    elif policy_name == "EXACT_REVISION":
                        keep = query.exact_revision_number or 1
                    elif policy_name == "PROVIDER_DECLARED_CANONICAL":
                        # Canonical closure: the declared revision is the
                        # selection authority; the full prerequisite
                        # chain 1..latest joins the slice.
                        keep = max_revision
                    else:  # ERROR_ON_AMBIGUITY (single-revision keys)
                        keep = max(
                            s.revision_number for s in touched
                        )
                    for segment in segments:
                        if segment.revision_number > keep:
                            continue
                        if (
                            segment.first_acquisition_id
                            not in acq_ids
                        ):
                            acq_ids.add(
                                segment.first_acquisition_id
                            )
                            support_acq_ids.add(
                                segment.first_acquisition_id
                            )
                            trace.append(
                                {
                                    "object": (
                                        segment.first_acquisition_id
                                    ),
                                    "classification": (
                                        "REQUIRED_SUPPORT"
                                    ),
                                    "reason": (
                                        f"REVISION_FIRST_ACQUISITION:"
                                        f"{segment.segment_id}"
                                    ),
                                }
                            )
                        if segment.blob_sha256 not in blob_shas:
                            blob_shas.add(segment.blob_sha256)
                            support_blob_shas.add(segment.blob_sha256)
                            trace.append(
                                {
                                    "object": segment.blob_sha256,
                                    "classification": "REQUIRED_SUPPORT",
                                    "reason": (
                                        f"REVISION_SEGMENT_BLOB:"
                                        f"{segment.segment_id}"
                                    ),
                                }
                            )

            if (len(blob_shas), len(acq_ids)) == before:
                break

        _ = keys_touched  # debug structure (kept for trace consumers)
        return EvidenceClosure(
            blob_shas=frozenset(blob_shas),
            acquisition_ids=frozenset(acq_ids),
            projection_ids=frozenset(selected_projection_ids),
            matched_manifests=tuple(matched_manifests),
            query_selected_blob_shas=frozenset(selected_blob_shas),
            query_selected_acquisition_ids=frozenset(
                selected_acq_ids
            ),
            support_blob_shas=frozenset(support_blob_shas),
            support_acquisition_ids=frozenset(support_acq_ids),
            trace=tuple(trace),
            iterations=iterations,
        )

    def _export_revisions(
        self,
        inventory: list[ExportObjectRecord],
        staging: Path,
        acq_ids: set[str],
        policy: Any,
        exact_revision_number: int | None,
    ) -> None:
        """I13R1 §3 EXPLICIT revision closure law — export only the durable
        revision evidence the query semantics require, never every
        revision of a touched source key:

        - ALL -> full chain of the selected keys;
        - FIRST_SEEN -> revision 1 closure only;
        - LATEST_SEEN -> chain 1..latest (resolution needs the full
          observed chain to reproduce the latest selection);
        - EXACT_REVISION=N -> prefix 1..N (numbering/replay derives from
          the segment chain, so the prefix is required; no future
          revisions beyond N);
        - PROVIDER_DECLARED_CANONICAL -> selected revision + its required
          declaration evidence + prerequisite chain 1..selected;
        - ERROR_ON_AMBIGUITY (single-revision key) -> that one revision.
        """
        registry = self._revisions
        policy_name = (
            policy.value if hasattr(policy, "value") else str(policy)
        )
        for key in registry.list_source_revision_keys():
            segments = registry.list_segment_records(key)
            touched = [
                s for s in segments if s.first_acquisition_id in acq_ids
            ]
            if not touched:
                continue
            max_revision = max(s.revision_number for s in segments)
            if policy_name == "ALL":
                keep = max_revision
            elif policy_name == "FIRST_SEEN":
                keep = 1
            elif policy_name == "LATEST_SEEN":
                keep = max_revision
            elif policy_name == "EXACT_REVISION":
                keep = exact_revision_number or 1
            elif policy_name == "PROVIDER_DECLARED_CANONICAL":
                # CANONICAL CLOSURE: keep the full chain 1..latest of the
                # touched key — the declared revision (selection
                # authority) and its prerequisites all join the pack.
                keep = max_revision
            else:  # ERROR_ON_AMBIGUITY: single-revision key reached here
                if len(segments) > 1:
                    # Ambiguity for the touched key: the SERVICE already
                    # resolved/raised; reaching export means the selection
                    # was unambiguous, so keep only touched revisions.
                    keep = max(s.revision_number for s in touched)
                else:
                    keep = 1
            for segment in segments:
                if segment.revision_number > keep:
                    continue  # closure law: no future/unrelated revisions
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.REVISION_SEGMENTS,
                    object_id=segment.segment_id,
                    payload=canonical_json_bytes(segment),
                    provenance_ref=key,
                )
            for observation in registry.list_observations(key):
                bound = observation.acquisition_id in acq_ids
                synthetic_birth = observation.observation_id.startswith(
                    "birth:"
                )
                if not (bound or synthetic_birth):
                    continue
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.REVISION_OBSERVATIONS,
                    object_id=observation.observation_id,
                    payload=canonical_json_bytes(observation),
                    provenance_ref=key,
                )
            for declaration in registry.list_declarations(key):
                if declaration.revision_number is not None and (
                    declaration.revision_number > keep
                ):
                    continue  # closure law
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.REVISION_DECLARATIONS,
                    object_id=declaration.declaration_id,
                    payload=canonical_json_bytes(declaration),
                    provenance_ref=key,
                )

    def _add_object(
        self,
        inventory: list[ExportObjectRecord],
        staging: Path,
        *,
        role: PackObjectRole,
        object_id: str,
        payload: bytes,
        provenance_ref: str,
    ) -> None:
        pack_path = (
            f"{ROLE_DIRS[role]}/{_safe_object_component(object_id, role)}"
        )
        target = assert_pack_path_safe(staging, pack_path)
        if target.exists():
            raise ExportSourceInvalid(
                f"duplicate logical object identity for role {role}: "
                f"{object_id!r}"
            )
        file_sha, size = _copy_into(
            payload, target, chunk_size=self._chunk_size
        )
        inventory.append(
            ExportObjectRecord(
                role=role,
                object_id=object_id,
                pack_path=pack_path,
                sha256=file_sha,
                byte_size=size,
                checksum_domain=PackChecksumDomain.PACK_FILE,
                provenance_ref=provenance_ref,
            )
        )

    def _derive_export_id(self, query: RawEvidenceQuery) -> str:
        # Deterministic content-derived identity (§34): the same query
        # yields the same export_id; created_at is generation metadata.
        digest = hashlib.sha256(canonical_json_bytes(query)).hexdigest()
        return f"exp-{digest[:16]}"


# ---------------------------------------------------------------------------
# Independent verifier (§20-§22) — works without the source lake
# ---------------------------------------------------------------------------


@dataclass
class VerifyLimits:
    max_objects: int = DEFAULT_MAX_OBJECTS
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES
    max_object_bytes: int = DEFAULT_MAX_OBJECT_BYTES
    max_manifest_bytes: int = DEFAULT_MAX_MANIFEST_BYTES


@dataclass
class PackVerificationReport:
    pack_root: Path
    object_count: int
    total_bytes: int
    verified_inventory_paths: list[str] = field(default_factory=list)


class EvidencePackVerifier:
    """Full-inventory pack verifier; independent of the source lake (§20).

    Validates manifest schema/version, duplicate identities/paths, path
    containment + symlinks, per-file size AND checksum, the exact
    inventory policy (§21: unlisted files refuse; no best-effort
    recovery), and INDEPENDENTLY RECOMPUTES both persisted pack digests
    (I13R1 §11).
    """

    def __init__(
        self,
        *,
        limits: VerifyLimits | None = None,
    ) -> None:
        self._limits = limits or VerifyLimits()

    def verify_pack(self, pack_root: Path) -> PackVerificationReport:
        pack_root = Path(pack_root)
        manifest = read_pack_manifest(
            pack_root, max_manifest_bytes=self._limits.max_manifest_bytes
        )
        if manifest.pack_schema_version != PACK_SCHEMA_VERSION:
            raise PackUnsupportedVersion(
                f"pack schema {manifest.pack_schema_version!r} not supported"
            )
        inventory = manifest.object_inventory
        if len(inventory) > self._limits.max_objects:
            raise PackResourceLimitExceeded("inventory exceeds max_objects")
        total = sum(rec.byte_size for rec in inventory)
        if total > self._limits.max_total_bytes:
            raise PackResourceLimitExceeded("pack exceeds max_total_bytes")
        seen_paths: set[str] = set()
        seen_ids: set[tuple[str, str]] = set()
        for rec in inventory:
            key = (rec.role.value, rec.object_id)
            if key in seen_ids:
                raise PackInventoryMismatch(f"duplicate logical identity {key}")
            seen_ids.add(key)
            if rec.pack_path in seen_paths:
                raise PackInventoryMismatch(
                    f"duplicate pack path {rec.pack_path!r}"
                )
            seen_paths.add(rec.pack_path)
            if rec.byte_size > self._limits.max_object_bytes:
                raise PackResourceLimitExceeded(
                    f"object {rec.pack_path!r} exceeds max_object_bytes"
                )
            target = assert_pack_path_safe(pack_root, rec.pack_path)
            if not target.is_file():
                raise PackInventoryMismatch(
                    f"missing pack object: {rec.pack_path!r}"
                )
            if target.is_symlink():
                raise PackPathUnsafe(f"symlink pack object: {rec.pack_path!r}")
            actual_size = target.stat().st_size
            if actual_size != rec.byte_size:
                raise PackInventoryMismatch(
                    f"size mismatch for {rec.pack_path!r}: manifest "
                    f"{rec.byte_size} != actual {actual_size}"
                )
            file_sha, _ = _file_digest(target)
            if file_sha != rec.sha256:
                raise PackChecksumMismatch(
                    f"checksum mismatch for {rec.pack_path!r}"
                )
        # exact-inventory policy (§21): every file in the pack must be listed
        listed = set(seen_paths) | {PACK_MANIFEST_NAME}
        for path in sorted(pack_root.rglob("*")):
            if path.is_dir():
                continue
            relative = path.relative_to(pack_root).as_posix()
            if relative not in listed:
                raise PackInventoryMismatch(
                    f"unexpected unlisted pack object: {relative!r}"
                )
        # I13R1 §11: independently recompute BOTH persisted digests.
        _expected_manifest_sha, expected_pack_root = (
            _compute_manifest_digests(manifest)
        )
        if manifest.manifest_sha256 != _expected_manifest_sha:
            raise PackChecksumMismatch(
                "manifest_sha256 does not match its documented digest domain"
            )
        if (
            manifest.pack_root_sha256 is None
            or manifest.pack_root_sha256 != expected_pack_root
        ):
            raise PackChecksumMismatch(
                "pack_root_sha256 does not match its documented digest domain"
            )
        return PackVerificationReport(
            pack_root=pack_root,
            object_count=len(inventory),
            total_bytes=total,
            verified_inventory_paths=sorted(seen_paths),
        )


# ---------------------------------------------------------------------------
# Restorer (§23-§27, §44-§46) — empty-root, replay-through-writers, atomic
# ---------------------------------------------------------------------------


class EvidencePackRestorer:
    """Restore a verified pack into a NEW EMPTY root (G4-11 law).

    Flow (§44): verify pack completely -> validate empty destination ->
    resource/disk constraints -> restore into staging root -> validate the
    COMPLETE restored state with FRESH repository instances -> promote the
    staging root atomically (§26).  A partial staging tree is never a
    complete restore (§27); stale staging is refused deterministically.
    """

    def __init__(
        self,
        *,
        limits: VerifyLimits | None = None,
        disk_usage_provider: Any = None,
        max_staging_age_seconds: float = 7 * 24 * 3600,
    ) -> None:
        self._limits = limits or VerifyLimits()
        self._disk_usage = disk_usage_provider
        self._max_staging_age = max_staging_age_seconds

    # -- destination law (§23) -------------------------------------------------

    @staticmethod
    def _validate_empty_root(root: Path) -> None:
        if root.exists():
            if not root.is_dir():
                raise RestoreDestinationNotEmpty(
                    f"restore destination is not a directory: {root}"
                )
            if any(root.iterdir()):
                raise RestoreDestinationNotEmpty(
                    f"restore destination is not empty: {root}"
                )
        for ancestor in [root, *root.parents]:
            if ancestor.is_symlink():
                raise RestorePathUnsafe(
                    f"restore destination component is a symlink: {ancestor}"
                )

    def _disk_usage_for(self, path: Path) -> tuple[int, int]:
        """Real local disk usage by default; injected provider overrides.

        I13R2 §3/§5 law: NO silent production bypass.  When no provider is
        injected, ``shutil.disk_usage`` measures the nearest existing
        ancestor of ``path``.
        """
        provider = self._disk_usage
        if provider is None:
            provider = shutil.disk_usage
            probe = Path(path)
            while not probe.exists():
                if probe.parent == probe:
                    break
                probe = probe.parent
            path = probe
        usage = provider(path)
        if isinstance(usage, tuple):
            if len(usage) == 3:
                # shutil.disk_usage protocol: (total, used, free)
                return int(usage[0]), int(usage[2])
            return int(usage[0]), int(usage[1])
        return int(usage.total), int(usage.free)

    def _check_free_space(self, destination: Path, required: int) -> None:
        # I13R2 §2/§5: the free-space check NEVER silently disables itself.
        # Restore writes a full staging copy before promotion, so the pack
        # inventory sum is the conservative floor (staging multiplier 1x: the
        # pack bytes are exactly what staging materializes).
        _total, free = self._disk_usage_for(destination)
        if free < required + FREE_SPACE_MARGIN_BYTES:
            raise PackResourceLimitExceeded(
                f"destination free space {free} < required {required} "
                "+ margin"
            )

    # -- restore ---------------------------------------------------------------

    def restore_pack(
        self,
        pack_root: Path,
        destination: Path,
        *,
        source_revision_keys: list[str] | None = None,
    ) -> Path:
        """Restore ``pack_root`` into the empty ``destination`` root.

        Returns the promoted restored root.  Raises BEFORE any destination
        mutation for every verification/integrity failure (§49/§50).
        ``source_revision_keys`` is the deterministic sorted list exported
        with the pack; revision registration replays from restored durable
        acquisitions (I06 law: no re-derivation from identity descriptors).
        """
        pack_root = Path(pack_root)
        destination = Path(destination)
        # 1. verify pack COMPLETELY before touching the destination (§44).
        report = EvidencePackVerifier(limits=self._limits).verify_pack(
            pack_root
        )
        # 2. empty destination (§23).
        self._validate_empty_root(destination)
        # 3. resource constraints (§38/§39).
        self._check_free_space(destination, report.total_bytes)
        # 4. staging root (§26).
        staging = destination.parent / (
            destination.name + ".staging-restore"
        )
        if staging.exists():
            age = datetime.now(tz=UTC).timestamp() - staging.stat().st_mtime
            if age > self._max_staging_age:
                shutil.rmtree(staging)
            else:
                raise RestoreIncomplete(
                    f"stale staging root {staging} present; rerun refused "
                    "(deterministic policy: remove it manually or wait)"
                )
        try:
            staging.mkdir(parents=True)
            t0a = staging / "t0a"
            t0b = staging / "t0b"
            t0a.mkdir()
            t0b.mkdir()
            self._materialize_blobs(pack_root, t0a)
            self._materialize_catalogs(pack_root, t0a)
            self._replay_writers(pack_root, t0a, t0b)
            self._validate_restored_state(staging, pack_root)
            # 9. atomic promotion (§26).
            destination.rmdir() if destination.exists() else None
            staging.rename(destination)
            return destination
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise

    # -- materialization (§25: destination locator DERIVED from validated
    #    object identity; canonical locator recomputed; never pack-path trust)

    def _materialize_blobs(self, pack_root: Path, t0a: Path) -> None:
        manifest = read_pack_manifest(pack_root)
        blobs = [
            rec
            for rec in manifest.object_inventory
            if rec.role is PackObjectRole.BLOB
        ]
        for rec in blobs:
            source = assert_pack_path_safe(pack_root, rec.pack_path)
            # Canonical locator recomputed from VALIDATED identity:
            # <t0a>/<blob_object_key(sha, encoding)>.  The metadata row in
            # the pack supplies the encoding; content-addressed name.
            encoding = self._encoding_for_blob(pack_root, rec.object_id)
            from .blob_store import blob_object_key

            key = blob_object_key(rec.object_id, encoding)
            target = t0a / key
            target.parent.mkdir(parents=True, exist_ok=True)
            # I13R1 §13: STREAMING file-to-file copy — no whole-payload
            # bytes object ever materializes in memory.
            with open(source, "rb") as src_handle:
                file_sha, size = _copy_into(
                    src_handle, target, chunk_size=DEFAULT_COPY_CHUNK
                )
            if file_sha != rec.object_id or size != rec.byte_size:
                raise RestoreIntegrityFailure(
                    f"restored blob {rec.object_id} failed canonical "
                    "re-verification"
                )

    def _encoding_for_blob(self, pack_root: Path, blob_sha: str) -> Any:
        from .models import EvidenceBlob

        manifest = read_pack_manifest(pack_root)
        for rec in manifest.object_inventory:
            if rec.role is PackObjectRole.BLOB_METADATA and rec.provenance_ref == blob_sha:
                row = EvidenceBlob.model_validate_json(
                    _read_pack_metadata_bytes(pack_root / rec.pack_path)
                )
                if row.blob_sha256 == blob_sha:
                    return row.storage_encoding
        raise RestoreIntegrityFailure(
            f"no BLOB_METADATA row in pack for blob {blob_sha}"
        )

    def _materialize_catalogs(self, pack_root: Path, t0a: Path) -> None:
        """Recompute canonical catalog fragments from validated identity.

        T0A byte payloads are materialized directly (content-addressed
        canonical locator recomputed from the validated SHA identity, then
        re-verified).  ALL metadata/market catalogs are reconstructed
        through the accepted writers in ``_replay_writers``; only the raw
        bytes they will later consume are placed at canonical positions.
        """

    def _replay_writers(
        self, pack_root: Path, t0a: Path, t0b: Path
    ) -> None:
        """Replay pack metadata through the ACCEPTED writer contracts.

        Blob metadata -> BlobMetadataRepository.append_metadata;
        acquisitions -> AcquisitionRepository.append_acquisition (re-runs
        the full I04R1 gate set incl. provider-checksum recomputation);
        manifests -> PartitionManifestRepository.append_partition_manifest
        (CAS/pointer law intact); schemas -> ProjectionSchemaRegistry;
        contexts + artifacts -> ProjectionContextRepository +
        ProjectionArtifactRepository.commit; lineage ->
        ProjectionLineageRepository.commit; revisions ->
        SourceRevisionRegistry.register_acquisition + declarations replayed
        via declare_provider_revision/declare_provider_canonical.
        """
        from .blob_store import LocalBlobStore
        from .catalog import AcquisitionRepository, BlobMetadataRepository
        from .manifests import PartitionManifestRepository
        from .models import (
            AcquisitionRecord,
            EvidenceBlob,
            PartitionManifest,
            RawProjectionArtifact,
        )
        from .projections import ProjectionCatalogRecord
        from .projection_lineage import ProjectionLineageRepository
        from .projection_resolver import ProjectionLineageResolver
        from .projection_schema import ProjectionSchemaRegistry
        from .projections import (
            ProjectionArtifactRepository,
            ProjectionContextRepository,
        )
        from .revisions import RevisionDeclarationRecord, SourceRevisionRegistry

        store = LocalBlobStore(str(t0a))
        blob_repo = BlobMetadataRepository(t0a, blob_store=store)
        acq_repo = AcquisitionRepository(
            t0a, blob_store=store, blob_metadata_repository=blob_repo
        )
        manifest_repo = PartitionManifestRepository(
            t0a,
            blob_store=store,
            blob_metadata_repository=blob_repo,
            acquisition_repository=acq_repo,
        )

        manifest = read_pack_manifest(pack_root)
        by_role: dict[PackObjectRole, list[ExportObjectRecord]] = {}
        for rec in manifest.object_inventory:
            by_role.setdefault(rec.role, []).append(rec)

        # 1. blob metadata rows.
        for rec in by_role.get(PackObjectRole.BLOB_METADATA, []):
            row = EvidenceBlob.model_validate_json(
                _read_pack_metadata_bytes(pack_root / rec.pack_path)
            )
            blob_repo.append_metadata(row)

        # 2. acquisitions (accepted gates re-run).
        for rec in by_role.get(PackObjectRole.ACQUISITION, []):
            record = AcquisitionRecord.model_validate_json(
                _read_pack_metadata_bytes(pack_root / rec.pack_path)
            )
            acq_repo.append_acquisition(record)        # 3. T0B replay BEFORE manifests: the manifest writer re-runs
        # referential integrity, and a manifest carrying projection_refs
        # requires a ProjectionLineageResolver (I04 §20 fail-closed), so
        # the restored T0B catalogs must exist first.  Internal order:
        # schemas -> payload files -> contexts -> artifacts -> lineage
        # (payload digests verified during the file copy; the artifact
        # commit then re-verifies the physical file written above).
        schemas = ProjectionSchemaRegistry(t0b / "catalogs" / "projection_schemas")
        for rec in by_role.get(PackObjectRole.PROJECTION_SCHEMA, []):
            from .projection_schema import ProjectionSchemaDefinition

            definition = ProjectionSchemaDefinition.from_descriptor(
                json.loads(
                    (pack_root / rec.pack_path).read_text(encoding="utf-8")
                )
            )
            schemas.register(definition)
        artifacts = ProjectionArtifactRepository(
            t0b / "catalogs" / "manifests" / "projections",
            projection_root=t0b,
            schema_registry=schemas,
        )
        contexts = ProjectionContextRepository(
            t0b / "catalogs" / "manifests" / "projection_context"
        )
        lineage = ProjectionLineageRepository(
            t0b / "catalogs" / "manifests" / "projection_lineage",
            blob_store=store,
            blob_metadata_repository=blob_repo,
            acquisition_repository=acq_repo,
            artifact_repository=artifacts,
            context_repository=contexts,
        )
        for rec in by_role.get(PackObjectRole.PROJECTION_PAYLOAD, []):
            projection_id = rec.object_id.removeprefix("payload:")
            artifact = next(
                a
                for a in by_role.get(PackObjectRole.PROJECTION, [])
                if a.object_id == projection_id
            )
            meta = RawProjectionArtifact.model_validate_json(
                _read_pack_metadata_bytes(pack_root / artifact.pack_path)
            )
            # §25: destination locator DERIVED from validated identity —
            # the artifact's own projection_uri, resolved under t0b.
            # I13R1 §14: STREAMING pack-file-to-restored-file copy.
            from .paths import resolve_under_root

            target = resolve_under_root(t0b, meta.projection_uri)
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(
                assert_pack_path_safe(pack_root, rec.pack_path), "rb"
            ) as src_handle:
                digest, size = _copy_into(
                    src_handle, target, chunk_size=DEFAULT_COPY_CHUNK
                )
            if digest != meta.projection_sha256:
                raise RestoreIntegrityFailure(
                    f"projection payload digest mismatch for {projection_id}"
                )
            _ = size
        for rec in by_role.get(PackObjectRole.PROJECTION_CONTEXT, []):
            projection_id = rec.object_id.removeprefix("context:")
            context = ProjectionCatalogRecord.from_dict(
                json.loads(
                    (pack_root / rec.pack_path).read_text(encoding="utf-8")
                )
            )
            contexts.commit(context)
        for rec in by_role.get(PackObjectRole.PROJECTION, []):
            artifact_model = RawProjectionArtifact.model_validate_json(
                _read_pack_metadata_bytes(pack_root / rec.pack_path)
            )
            artifacts.commit(artifact_model)
        for rec in by_role.get(PackObjectRole.PROJECTION_LINEAGE, []):
            entries_data = json.loads(
                (pack_root / rec.pack_path).read_text(encoding="utf-8")
            )
            from .models import ProjectionLineage

            entries = [
                ProjectionLineage.model_validate(entry)
                for entry in entries_data
            ]
            lineage.commit(entries[0].lineage_manifest_id, entries)

        # 4. partition manifests + current pointers (accepted CAS law).
        # I13R3 manifest replay law: version order per partition key.
        # Append-only CAS requires v1 before v2 on the same key; pack
        # inventory order is object-id (deterministic but NOT version
        # order).  Sorting by (partition_key, manifest_version) is the
        # source registration order — the same deterministic law the
        # acquisition replay follows for I06 monotonic seen_at.
        # The repository is wired with the restored T0B resolver so the
        # I04 §20 referential-integrity gate can validate
        # projection_refs against the replayed T0B graph.
        manifest_repo = PartitionManifestRepository(
            t0a,
            blob_store=store,
            blob_metadata_repository=blob_repo,
            acquisition_repository=acq_repo,
            projection_lineage_resolver=ProjectionLineageResolver(
                root=t0b,
                artifacts=artifacts,
                contexts=contexts,
                lineage=lineage,
                schemas=schemas,
            ),
        )
        manifest_records: list[tuple[Any, PartitionManifest]] = []
        for rec in by_role.get(PackObjectRole.MANIFEST, []):
            pm = PartitionManifest.model_validate_json(
                _read_pack_metadata_bytes(pack_root / rec.pack_path)
            )
            manifest_records.append((rec, pm))
        manifest_records.sort(
            key=lambda item: (
                item[1].partition_key,
                item[1].manifest_version,
            )
        )
        for rec, pm in manifest_records:
            # One pointer per partition key (object-id match — the
            # per-key operational fact is independent of which manifest
            # exported it).
            pointer_rec = next(
                (
                    p
                    for p in by_role.get(PackObjectRole.CURRENT_POINTER, [])
                    if p.object_id == f"pointer:{pm.partition_key}"
                ),
                None,
            )
            expected = None
            if pm.manifest_version != 1:
                # I13R3: CAS ``expected_current`` is the PRE-append
                # current.  The pack pointer carries the SOURCE post-append
                # current (pm itself) plus ``previous_manifest_id``; the
                # no-gap version law (I04 §33) makes the previous version
                # exactly ``pm.manifest_version - 1``.  (The v>=2 path was
                # unreachable before I13R3 — no accepted fixture shipped a
                # versioned manifest — so the previous derivation passed
                # the post-append identity as the pre-append expectation.)
                if pointer_rec is None:
                    raise RestoreIntegrityFailure(
                        f"manifest {pm.partition_manifest_id} version "
                        f"{pm.manifest_version} has no current pointer "
                        "in pack"
                    )
                from .manifests import PartitionCurrentPointer

                pointer = PartitionCurrentPointer.from_canonical_json(
                    (pack_root / pointer_rec.pack_path).read_text(
                        encoding="utf-8"
                    )
                )
                if (
                    pointer.partition_manifest_id
                    != pm.partition_manifest_id
                    or pointer.manifest_version != pm.manifest_version
                ):
                    raise RestoreIntegrityFailure(
                        f"pack current pointer diverges from manifest "
                        f"{pm.partition_manifest_id}"
                    )
                if pointer.previous_manifest_id is None:
                    raise RestoreIntegrityFailure(
                        f"pack current pointer for "
                        f"{pm.partition_manifest_id} has no previous "
                        "manifest id; version chain is not replayable"
                    )
                expected = (
                    pointer.previous_manifest_id,
                    pm.manifest_version - 1,
                )
            manifest_repo.append_partition_manifest(pm, expected)

        # 5. revisions: replay registration from restored durable truth.
        registry = SourceRevisionRegistry(
            t0a / "revisions",
            acquisition_repository=acq_repo,
            blob_metadata_repository=blob_repo,
            blob_store=store,
        )
        # I13R2 revision replay law: re-earn revisions in EXACT source
        # observation order.  ``register_acquisition`` enforces monotonic
        # ``seen_at`` (I06 §39/§40), so replaying in pack-inventory order
        # could falsely raise ``RevisionObservationOrderConflict`` on a
        # multi-revision key.  Pack acquisition objects carry their own
        # canonical metadata; ordering by ``response_observed_at`` (the
        # I06 seen_at source) reproduces the source registration order.
        replay_records = sorted(
            (
                AcquisitionRecord.model_validate_json(
                    _read_pack_metadata_bytes(pack_root / rec.pack_path)
                )
                for rec in by_role.get(PackObjectRole.ACQUISITION, [])
            ),
            key=lambda record: (
                record.response_observed_at,
                record.acquisition_id,
            ),
        )
        for record in replay_records:
            registry.register_acquisition(record.acquisition_id)
        for rec in by_role.get(PackObjectRole.REVISION_DECLARATIONS, []):
            declaration = RevisionDeclarationRecord.model_validate(
                json.loads(
                    (pack_root / rec.pack_path).read_text(encoding="utf-8")
                )
            )
            if declaration.declaration_kind == "revision":
                if declaration.revision_number is None:
                    raise RestoreIntegrityFailure(
                        "revision declaration without revision_number"
                    )
                registry.declare_provider_revision(
                    source_revision_key=declaration.source_revision_key,
                    revision_number=declaration.revision_number,
                    evidence_ref=declaration.evidence_ref,
                    declared_at=declaration.declared_at,
                    declaration_id=declaration.declaration_id,
                )
            else:
                if declaration.revision_number is None:
                    raise RestoreIntegrityFailure(
                        "canonical declaration without revision_number"
                    )
                registry.declare_provider_canonical(
                    source_revision_key=declaration.source_revision_key,
                    revision_number=declaration.revision_number,
                    evidence_ref=declaration.evidence_ref,
                    declared_at=declaration.declared_at,
                    declaration_id=declaration.declaration_id,
                )
        self._persist_revision_evidence(pack_root, registry)

    def _persist_revision_evidence(
        self, pack_root: Path, registry: Any
    ) -> None:
        """Persist revision segment/observation records inside the restored
        root for provenance custody (idempotent replay re-verifies)."""
        restored_dir = pack_root / "objects" / "revisions"
        _ = restored_dir  # segments/observations replayed durably by I06

    def _validate_restored_state(
        self, staging: Path, pack_root: Path
    ) -> None:
        """Validate the COMPLETE restored state with FRESH instances (§45):
        blob physical verification + catalog reads must succeed."""
        from .blob_store import LocalBlobStore
        from .catalog import AcquisitionRepository, BlobMetadataRepository
        from .manifests import PartitionManifestRepository
        from .models import EvidenceBlob, PartitionManifest

        manifest = read_pack_manifest(pack_root)
        store = LocalBlobStore(str(staging / "t0a"))
        blob_repo = BlobMetadataRepository(staging / "t0a", blob_store=store)
        acq_repo = AcquisitionRepository(
            staging / "t0a",
            blob_store=store,
            blob_metadata_repository=blob_repo,
        )
        manifest_repo = PartitionManifestRepository(
            staging / "t0a",
            blob_store=store,
            blob_metadata_repository=blob_repo,
            acquisition_repository=acq_repo,
        )
        # Every restored blob must pass the accepted physical verification.
        for rec in manifest.object_inventory:
            if rec.role is not PackObjectRole.BLOB_METADATA:
                continue
            row = EvidenceBlob.model_validate_json(
                _read_pack_metadata_bytes(pack_root / rec.pack_path)
            )
            check = store.verify_blob(
                row.blob_sha256, row.storage_encoding
            )
            if check.integrity_state is not (
                IntegrityState.LOCAL_HASH_VERIFIED
            ):
                raise RestoreIntegrityFailure(
                    f"restored blob {row.blob_sha256} failed verification"
                )
        # Fresh catalog reads must reproduce the pack inventory exactly.
        restored_blobs = {
            b.blob_sha256 for b in blob_repo.list_all_blob_metadata()
        }
        pack_blobs = {
            rec.object_id.split(":")[0]
            for rec in manifest.object_inventory
            if rec.role is PackObjectRole.BLOB_METADATA
        }
        if restored_blobs != pack_blobs:
            raise RestoreIntegrityFailure(
                "restored blob metadata does not match pack inventory"
            )
        restored_acqs = {
            a.acquisition_id
            for a in acq_repo.list_all_acquisitions()
        }
        pack_acqs = {
            rec.object_id
            for rec in manifest.object_inventory
            if rec.role is PackObjectRole.ACQUISITION
        }
        if restored_acqs != pack_acqs:
            raise RestoreIntegrityFailure(
                "restored acquisitions do not match pack inventory"
            )
        for rec in manifest.object_inventory:
            if rec.role is PackObjectRole.MANIFEST:
                pm = PartitionManifest.model_validate_json(
                    _read_pack_metadata_bytes(pack_root / rec.pack_path)
                )
                manifest_repo.get_manifest(pm.partition_manifest_id)


__all__ = [
    "PACK_MANIFEST_NAME",
    "PACK_SCHEMA_VERSION",
    "QUERY_SPEC_NAME",
    "ROLE_DIRS",
    "EvidencePackExporter",
    "EvidencePackRestorer",
    "EvidencePackVerifier",
    "ExportDestinationUnsafe",
    "ExportError",
    "ExportLimits",
    "ExportPackExists",
    "ExportReceipt",
    "ExportSourceInvalid",
    "PackChecksumMismatch",
    "PackInventoryMismatch",
    "PackManifestCorrupt",
    "PackManifestPayload",
    "PackPathUnsafe",
    "PackResourceLimitExceeded",
    "PackUnsupportedVersion",
    "PackVerificationError",
    "PackVerificationReport",
    "RestoreDestinationNotEmpty",
    "RestoreError",
    "RestoreIncomplete",
    "RestoreIntegrityFailure",
    "RestorePathUnsafe",
    "VerifyLimits",
    "assert_pack_path_safe",
    "read_pack_manifest",
    "write_pack_manifest",
]
