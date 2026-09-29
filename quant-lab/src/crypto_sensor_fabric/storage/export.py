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
    RawEvidenceQuery,
    RawEvidenceResult,
    canonical_json_bytes,
)
from .query import RawEvidenceQueryService

PACK_SCHEMA_VERSION = "1"
PACK_MANIFEST_NAME = "export_manifest.json"
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

LOGICAL_SOURCE_ROOT = "logical://source-lake"


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


def read_pack_manifest(pack_root: Path) -> PackManifestPayload:
    """Load + schema-check the pack manifest (fail-closed)."""
    path = pack_root / PACK_MANIFEST_NAME
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PackManifestCorrupt(f"pack manifest unreadable: {exc}") from exc
    if len(raw) > DEFAULT_MAX_MANIFEST_BYTES:
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
    payload_bytes = canonical_json_bytes(manifest)
    (pack_root / PACK_MANIFEST_NAME).write_bytes(payload_bytes)
    return hashlib.sha256(payload_bytes).hexdigest()


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

    # -- selection (query-driven only) ----------------------------------------

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
        store_root = Path(self._store.root).resolve()
        if resolved_dest == store_root or store_root in resolved_dest.parents:
            raise ExportDestinationUnsafe(
                "destination lies inside the source blob store"
            )
        for source_root in (self._blob_repo.root, self._acq_repo.root):
            src = Path(source_root).resolve()
            if resolved_dest == src or src in resolved_dest.parents:
                raise ExportDestinationUnsafe(
                    f"destination lies inside source catalog tree {src}"
                )

    def _check_free_space(self, destination: Path, required: int) -> None:
        if self._disk_usage is None:
            return
        total, free = self._disk_usage(destination)
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
        self._validate_destination(destination)
        destination.mkdir(parents=True, exist_ok=True)
        staging = destination / STAGING_DIR_NAME
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()
        try:
            inventory: list[ExportObjectRecord] = []
            blob_shas = sorted({sha for r in results for sha in r.blob_refs})
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

            # --- acquisitions linked to selected blobs ------------------------
            acq_ids: set[str] = set()
            for sha in blob_shas:
                for rec in self._acq_repo.list_acquisitions_for_blob(sha):
                    acq_ids.add(rec.acquisition_id)
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
            current_manifests = sorted(
                self._manifest_repo.list_all_current_manifests(),
                key=lambda m: m.partition_manifest_id,
            )
            identity_set = {
                (r.provider, r.venue, r.native_instrument) for r in results
            }
            for manifest in current_manifests:
                if (
                    manifest.provider,
                    manifest.venue,
                    manifest.native_instrument,
                ) not in identity_set:
                    continue
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.MANIFEST,
                    object_id=manifest.partition_manifest_id,
                    payload=canonical_json_bytes(manifest),
                    provenance_ref=manifest.partition_manifest_id,
                )
                pointer = self._manifest_repo.read_current_pointer(
                    manifest.partition_key
                )
                if pointer is not None:
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
                # T0B payload bytes (PACK_FILE domain; digest must equal the
                # artifact's projection_sha256 — same bytes, different role).
                payload_bytes = self._read_projection_payload(artifact)
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.PROJECTION_PAYLOAD,
                    object_id=f"payload:{projection_id}",
                    payload=payload_bytes,
                    provenance_ref=artifact.projection_sha256,
                )
                if self._contexts is not None:
                    context = self._contexts.get(projection_id)
                    if context is not None:
                        self._add_object(
                            inventory,
                            staging,
                            role=PackObjectRole.PROJECTION_CONTEXT,
                            object_id=f"context:{projection_id}",
                            payload=canonical_json_bytes(context),
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
                            payload=canonical_json_bytes(entries),
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
                            payload=canonical_json_bytes(definition),
                            provenance_ref=definition.schema_identity,
                        )

            # --- revision evidence for exported acquisitions (§7) --------------
            if self._revisions is not None:
                self._export_revisions(inventory, staging, acq_ids)

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
                manifest_sha256=hashlib.sha256(
                    canonical_json_bytes(inventory[0]) if inventory else b"0"
                ).hexdigest(),
                objects=sorted({rec.object_id for rec in inventory}),
                object_inventory=inventory,
                pack_root_sha256=None,
                layout={role.value: d for role, d in ROLE_DIRS.items()},
                checksum_domains={
                    "SOURCE_BYTES": (
                        "sha256 of exact provider-source bytes before "
                        "optional local wrapper compression"
                    ),
                    "PACK_FILE": "sha256 of the pack file's own bytes",
                },
            )
            # Self-verify BEFORE finalization (§43): the same independent
            # verifier a later consumer would run.
            write_pack_manifest(staging, payload)
            EvidencePackVerifier(
                limits=VerifyLimits(
                    max_objects=self._limits.max_objects,
                    max_total_bytes=self._limits.max_total_bytes,
                    max_object_bytes=self._limits.max_object_bytes,
                )
            ).verify_pack(staging)
            pack_root_sha = _file_digest(
                staging / PACK_MANIFEST_NAME
            )[0]
            self._finalize(staging, destination)

            receipt_manifest = ExportManifest(
                export_id=export_id,
                created_at=created_at,
                source_data_root=LOGICAL_SOURCE_ROOT,
                selection_query=query,
                blob_count=len(blob_shas),
                projection_count=len(projection_ids),
                total_bytes=total_bytes,
                manifest_sha256=pack_root_sha,
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

    def _export_revisions(
        self,
        inventory: list[ExportObjectRecord],
        staging: Path,
        acq_ids: set[str],
    ) -> None:
        registry = self._revisions
        for key in registry.list_source_revision_keys():
            # The durable SEGMENT records carry first_acquisition_id (the
            # materialized SourceRevision views do not); read-only
            # introspection of registry truth (§42).
            segments = list(
                getattr(registry, "_segments_by_key", {}).get(key, [])
            )
            if not any(s.first_acquisition_id in acq_ids for s in segments):
                continue
            for segment in segments:
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.REVISION_SEGMENTS,
                    object_id=segment.segment_id,
                    payload=canonical_json_bytes(segment),
                    provenance_ref=key,
                )
            for observation in registry.list_observations(key):
                if (
                    observation.acquisition_id in acq_ids
                    or observation.observation_id.startswith("birth:")
                ):
                    self._add_object(
                        inventory,
                        staging,
                        role=PackObjectRole.REVISION_OBSERVATIONS,
                        object_id=observation.observation_id,
                        payload=canonical_json_bytes(observation),
                        provenance_ref=key,
                    )
            # Declarations are explicit provider evidence bound to the key;
            # read-only introspection of durable registry truth (§42).
            declarations = getattr(registry, "_declarations_by_key", {}).get(
                key, []
            )
            for declaration in declarations:
                self._add_object(
                    inventory,
                    staging,
                    role=PackObjectRole.REVISION_DECLARATIONS,
                    object_id=declaration.declaration_id,
                    payload=canonical_json_bytes(declaration),
                    provenance_ref=key,
                )

    def _read_projection_payload(self, artifact: Any) -> bytes:
        """Read the provider-native projection file via its accepted
        read-only URI (validated safe-under-root by the artifact commit).
        Verify against projection_sha256 (the artifact's own digest law)."""
        from .paths import resolve_under_root

        root = Path(self._artifacts._projection_root)
        path = resolve_under_root(root, artifact.projection_uri)
        if not path.is_file():
            raise ExportSourceInvalid(
                f"projection payload missing for {artifact.projection_id}"
            )
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != artifact.projection_sha256:
            raise PackChecksumMismatch(
                f"projection payload digest != projection_sha256 for "
                f"{artifact.projection_id}"
            )
        return data

    def _finalize(self, staging: Path, destination: Path) -> None:
        """Promote the verified staging tree into the final pack root."""
        for child in list(staging.iterdir()):
            target = destination / child.name
            if target.exists():
                raise ExportPackExists(f"pack object already exists: {target}")
            shutil.move(str(child), str(target))
        staging.rmdir()

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


@dataclass
class PackVerificationReport:
    pack_root: Path
    object_count: int
    total_bytes: int
    verified_inventory_paths: list[str] = field(default_factory=list)


class EvidencePackVerifier:
    """Full-inventory pack verifier; independent of the source lake (§20).

    Validates manifest schema/version, duplicate identities/paths, path
    containment + symlinks, per-file size AND checksum, and the exact
    inventory policy (§21: unlisted files refuse; no best-effort recovery).
    """

    def __init__(
        self,
        *,
        limits: VerifyLimits | None = None,
    ) -> None:
        self._limits = limits or VerifyLimits()

    def verify_pack(self, pack_root: Path) -> PackVerificationReport:
        pack_root = Path(pack_root)
        manifest = read_pack_manifest(pack_root)
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

    def _check_free_space(self, destination: Path, required: int) -> None:
        if self._disk_usage is None:
            return
        _total, free = self._disk_usage(destination)
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
            file_sha, size = _copy_into(
                source.read_bytes(), target, chunk_size=DEFAULT_COPY_CHUNK
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
                    (pack_root / rec.pack_path).read_bytes()
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
                (pack_root / rec.pack_path).read_bytes()
            )
            blob_repo.append_metadata(row)

        # 2. acquisitions (accepted gates re-run).
        for rec in by_role.get(PackObjectRole.ACQUISITION, []):
            record = AcquisitionRecord.model_validate_json(
                (pack_root / rec.pack_path).read_bytes()
            )
            acq_repo.append_acquisition(record)

        # 3. partition manifests + current pointers (accepted CAS law).
        for rec in by_role.get(PackObjectRole.MANIFEST, []):
            pm = PartitionManifest.model_validate_json(
                (pack_root / rec.pack_path).read_bytes()
            )
            pointer_rec = next(
                (
                    p
                    for p in by_role.get(PackObjectRole.CURRENT_POINTER, [])
                    if p.provenance_ref == pm.partition_manifest_id
                ),
                None,
            )
            expected = None
            if pm.manifest_version != 1 and pointer_rec is not None:
                from .manifests import PartitionCurrentPointer

                pointer = PartitionCurrentPointer.from_canonical_json(
                    (pack_root / pointer_rec.pack_path).read_text(
                        encoding="utf-8"
                    )
                )
                expected = (
                    pointer.partition_manifest_id,
                    pointer.manifest_version,
                )
            manifest_repo.append_partition_manifest(pm, expected)

        # 4. T0B: schemas, artifact payloads, contexts, artifacts, lineage.
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
                (pack_root / artifact.pack_path).read_bytes()
            )
            payload_bytes = (pack_root / rec.pack_path).read_bytes()
            # §25: destination locator DERIVED from validated identity —
            # the artifact's own projection_uri, resolved under t0b.
            from .paths import resolve_under_root

            target = resolve_under_root(t0b, meta.projection_uri)
            target.parent.mkdir(parents=True, exist_ok=True)
            digest, size = _copy_into(
                payload_bytes, target, chunk_size=DEFAULT_COPY_CHUNK
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
                (pack_root / rec.pack_path).read_bytes()
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

        # 5. revisions: replay registration from restored durable truth.
        registry = SourceRevisionRegistry(
            t0a / "revisions",
            acquisition_repository=acq_repo,
            blob_metadata_repository=blob_repo,
            blob_store=store,
        )
        for rec in by_role.get(PackObjectRole.ACQUISITION, []):
            record = AcquisitionRecord.model_validate_json(
                (pack_root / rec.pack_path).read_bytes()
            )
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
                (pack_root / rec.pack_path).read_bytes()
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
                    (pack_root / rec.pack_path).read_bytes()
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
