"""SENSOR-B4-I04B — immutable EvidenceBlob metadata + AcquisitionRecord catalog.

I04 gives the durable I03 T0A bytes durable EVIDENCE CONTEXT.  This module
implements the metadata/catalog layer over the accepted atomic filesystem
backend:

- dataset-style IMMUTABLE Parquet fragments (PyArrow; already a project
  dependency) under ``<t0_root>/catalogs/manifests/`` — appending means
  publishing ANOTHER immutable fragment, never mutating an existing file;
- ``BlobMetadataRepository`` — one durable ``EvidenceBlob`` row per
  physical object key ``(blob_sha256, storage_encoding)`` (policy B, I04 §66);
- ``AcquisitionRepository`` — one durable row per acquisition event, with
  the reconciled I04A AcquisitionRecord preserved losslessly;
- a shared immutable-fragment publication pipeline reusing the accepted I03
  durability doctrine: stage -> flush -> file fsync -> staged verification
  (parse + schema + exact expected rows) -> no-clobber publish -> parent
  directory fsync -> fragment hash.

Catalog physical paths are storage implementation details, NOT economic
identity (I04 §21): a SHA-256 of the exact UTF-8 acquisition_id is used as a
physical locator while the logical id stays authoritative inside the row.

Never persisted: secrets, pickles, ``repr()`` strings, opaque Python
objects.  Enum values are stored as their exact frozen string values;
nested Bloc-3 objects (ResumeToken / AdapterEvidenceRef) as deterministic
canonical JSON.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import pyarrow as pa
import pyarrow.parquet as pq

from ..contracts.base import coerce_utc
from ..providers.base.enums import Granularity, QualityFlagAcquisition, SchemaState
from ..providers.base.models import AdapterEvidenceRef, ResumeToken
from .atomic import (
    AtomicPublishTargetExists,
    ensure_durable_directory,
    fsync_directory,
    fsync_file,
    publish_no_replace,
)
from .blob_store import BlobMissing, InvalidStorageRoot, LocalBlobStore
from .checksums import sha256_file, validate_sha256_hex
from .enums import IntegrityState, StorageEncoding
from .models import AcquisitionRecord, EvidenceBlob
from .paths import blob_object_key, resolve_under_root

# ---------------------------------------------------------------------------
# Typed catalog errors (I04 §76 — no generic RuntimeError for every case)
# ---------------------------------------------------------------------------


class CatalogError(RuntimeError):
    """Base class for the durable catalog repository."""


class CatalogNotFound(CatalogError):
    """A required catalog object does not exist (distinct from corruption)."""


class BlobMetadataNotFound(CatalogNotFound):
    """No durable EvidenceBlob metadata row exists for the requested key."""


class AcquisitionNotFound(CatalogNotFound):
    """No durable AcquisitionRecord exists for the requested id."""


class ManifestNotFound(CatalogNotFound):
    """No durable PartitionManifest exists for the requested id/partition."""


class CatalogIntegrityError(CatalogError):
    """A fragment is unreadable, schema-mismatched or row-mismatched.

    A corrupt/unreadable metadata fragment must NEVER become usable catalog
    truth (I04 §24).
    """


class DanglingBlobReference(CatalogIntegrityError):
    """A record references a blob that has no durable verified evidence."""


class BlobMetadataConflict(CatalogError):
    """Same BlobStorageKey with semantically different immutable metadata.

    Never overwritten and never silently chosen (I04 §27/§71).
    """


class AcquisitionIdentityConflict(CatalogError):
    """Same acquisition_id with a differing semantic record (I04 §28/§70).

    Immutable: first append wins; the conflicting record is refused typed.
    """


class CatalogDurabilityError(CatalogError):
    """A durability primitive failed in a way that is not a content claim."""


class ProjectionReferenceUnavailable(CatalogError):
    """A record carries projection refs that cannot exist yet (I04 §20).

    I05 owns T0B projections; I04 manifest writes must keep projection_refs
    EMPTY and fail closed on dangling projection refs.
    """


# ---------------------------------------------------------------------------
# Stable explicit Arrow schemas (I04 §17/§18 — no pandas inference)
# ---------------------------------------------------------------------------

_TIMESTAMP = pa.timestamp("us", tz="UTC")


def _field(name: str, type_: pa.DataType, nullable: bool) -> pa.Field:
    return pa.field(name, type_, nullable=nullable)


BLOB_SCHEMA = pa.schema(
    [
        _field("blob_sha256", pa.string(), False),
        _field("byte_length", pa.int64(), False),
        _field("stored_byte_length", pa.int64(), False),
        _field("source_media_type", pa.string(), False),
        _field("storage_encoding", pa.string(), False),
        _field("storage_uri", pa.string(), False),
        _field("integrity_state", pa.string(), False),
        _field("created_at", _TIMESTAMP, False),
    ]
)

ACQUISITION_SCHEMA = pa.schema(
    [
        _field("acquisition_id", pa.string(), False),
        _field("provider_id", pa.string(), False),
        _field("venue", pa.string(), False),
        _field("sensor_family", pa.string(), False),
        _field("request_fingerprint", pa.string(), False),
        _field("adapter_version", pa.string(), False),
        _field("adapter_capability_version", pa.string(), True),
        _field("requested_start", _TIMESTAMP, False),
        _field("requested_end", _TIMESTAMP, False),
        _field("actual_start", _TIMESTAMP, True),
        _field("actual_end", _TIMESTAMP, True),
        _field("native_instrument", pa.string(), False),
        _field("native_granularity", pa.string(), True),
        _field("request_started_at", _TIMESTAMP, False),
        _field("response_observed_at", _TIMESTAMP, False),
        _field("ingested_at", _TIMESTAMP, False),
        _field("http_status_or_source_status", pa.string(), True),
        _field("endpoint_host", pa.string(), True),
        _field("endpoint_path", pa.string(), True),
        _field("request_family", pa.string(), True),
        _field("source_locator", pa.string(), False),
        _field("blob_sha256", pa.string(), True),
        _field("schema_state", pa.string(), True),
        _field("evidence_ref", pa.string(), True),
        _field("provider_checksum_algorithm", pa.string(), True),
        _field("provider_checksum_value", pa.string(), True),
        _field("provider_checksum_verified", pa.bool_(), True),
        _field("resume_token_before", pa.string(), True),
        _field("resume_token_after", pa.string(), True),
        _field("quality_flags", pa.list_(pa.string()), False),
        _field("failure_ref", pa.string(), True),
    ]
)


# ---------------------------------------------------------------------------
# Deterministic value representations (no Python repr, no pickles)
# ---------------------------------------------------------------------------


def canonical_nested_json(value: Any) -> str:
    """Deterministic canonical JSON for nested Bloc-3 objects/values.

    Stable key order, UTF-8, compact separators.  Round-trips through
    ``json.loads`` without any Python-specific repr artifacts.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def model_canonical_json(model: Any) -> str:
    """Canonical JSON of a pydantic model (enums as string values, UTC ISO)."""
    return canonical_nested_json(json.loads(model.model_dump_json()))


def _blob_row(blob: EvidenceBlob) -> dict[str, Any]:
    return {
        "blob_sha256": blob.blob_sha256,
        "byte_length": blob.byte_length,
        "stored_byte_length": blob.stored_byte_length,
        "source_media_type": blob.source_media_type,
        "storage_encoding": blob.storage_encoding.value,
        "storage_uri": blob.storage_uri,
        "integrity_state": blob.integrity_state.value,
        "created_at": blob.created_at,
    }


def _acquisition_row(record: AcquisitionRecord) -> dict[str, Any]:
    return {
        "acquisition_id": record.acquisition_id,
        "provider_id": record.provider_id,
        "venue": record.venue,
        "sensor_family": record.sensor_family.value,
        "request_fingerprint": record.request_fingerprint,
        "adapter_version": record.adapter_version,
        "adapter_capability_version": record.adapter_capability_version,
        "requested_start": record.requested_start,
        "requested_end": record.requested_end,
        "actual_start": record.actual_start,
        "actual_end": record.actual_end,
        "native_instrument": record.native_instrument,
        "native_granularity": (
            record.native_granularity.value if record.native_granularity is not None else None
        ),
        "request_started_at": record.request_started_at,
        "response_observed_at": record.response_observed_at,
        "ingested_at": record.ingested_at,
        "http_status_or_source_status": record.http_status_or_source_status,
        "endpoint_host": record.endpoint_host,
        "endpoint_path": record.endpoint_path,
        "request_family": record.request_family,
        "source_locator": record.source_locator,
        "blob_sha256": record.blob_sha256,
        "schema_state": record.schema_state.value if record.schema_state is not None else None,
        "evidence_ref": (
            model_canonical_json(record.evidence_ref)
            if record.evidence_ref is not None
            else None
        ),
        "provider_checksum_algorithm": record.provider_checksum_algorithm,
        "provider_checksum_value": record.provider_checksum_value,
        "provider_checksum_verified": record.provider_checksum_verified,
        "resume_token_before": (
            model_canonical_json(record.resume_token_before)
            if record.resume_token_before is not None
            else None
        ),
        "resume_token_after": (
            model_canonical_json(record.resume_token_after)
            if record.resume_token_after is not None
            else None
        ),
        "quality_flags": [flag.value for flag in record.quality_flags],
        "failure_ref": record.failure_ref,
    }


def _blob_from_row(row: dict[str, Any]) -> EvidenceBlob:
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


def _acquisition_from_row(row: dict[str, Any]) -> AcquisitionRecord:
    kwargs: dict[str, Any] = {
        "acquisition_id": row["acquisition_id"],
        "provider_id": row["provider_id"],
        "venue": row["venue"],
        "sensor_family": row["sensor_family"],
        "request_fingerprint": row["request_fingerprint"],
        "adapter_version": row["adapter_version"],
        "adapter_capability_version": row["adapter_capability_version"],
        "requested_start": row["requested_start"],
        "requested_end": row["requested_end"],
        "actual_start": row["actual_start"],
        "actual_end": row["actual_end"],
        "native_instrument": row["native_instrument"],
        "native_granularity": (
            Granularity(row["native_granularity"])
            if row["native_granularity"] is not None
            else None
        ),
        "request_started_at": row["request_started_at"],
        "response_observed_at": row["response_observed_at"],
        "ingested_at": row["ingested_at"],
        "http_status_or_source_status": row["http_status_or_source_status"],
        "endpoint_host": row["endpoint_host"],
        "endpoint_path": row["endpoint_path"],
        "request_family": row["request_family"],
        "source_locator": row["source_locator"],
        "blob_sha256": row["blob_sha256"],
        "schema_state": (
            SchemaState(row["schema_state"]) if row["schema_state"] is not None else None
        ),
        "evidence_ref": (
            AdapterEvidenceRef.model_validate(json.loads(row["evidence_ref"]))
            if row["evidence_ref"] is not None
            else None
        ),
        "provider_checksum_algorithm": row["provider_checksum_algorithm"],
        "provider_checksum_value": row["provider_checksum_value"],
        "provider_checksum_verified": row["provider_checksum_verified"],
        "resume_token_before": (
            ResumeToken.model_validate(json.loads(row["resume_token_before"]))
            if row["resume_token_before"] is not None
            else None
        ),
        "resume_token_after": (
            ResumeToken.model_validate(json.loads(row["resume_token_after"]))
            if row["resume_token_after"] is not None
            else None
        ),
        "quality_flags": [QualityFlagAcquisition(v) for v in row["quality_flags"]],
        "failure_ref": row["failure_ref"],
    }
    return AcquisitionRecord(**kwargs)


def _rows_equal(got: dict[str, Any], expected: dict[str, Any]) -> bool:
    """Semantic row equality (None == null; scalars compare directly)."""
    if got.keys() != expected.keys():
        return False
    for key in got:
        if got[key] != expected[key]:
            return False
    return True


# ---------------------------------------------------------------------------
# Shared root + immutable fragment publication pipeline
# ---------------------------------------------------------------------------


def resolve_catalog_root(root: str | Path) -> Path:
    """ACTUAL ROOT POLICY (I04 §3 reconciliation).

    Existing root directory -> use it; existing non-directory -> fail closed;
    missing root -> MAY be created durably by the fragment pipeline through
    ``ensure_durable_directory`` (never blind recursive mkdir).
    """
    path = Path(root)
    if str(path) == "":
        raise InvalidStorageRoot("data root must be a nonempty path")
    if path.exists() and not path.is_dir():
        raise InvalidStorageRoot(f"data root {path!s} exists and is not a directory")
    return path


@dataclass(frozen=True)
class CatalogFragmentReceipt:
    """Publication receipt for one immutable catalog fragment."""

    family: str
    fragment_key: str
    fragment_path: str
    fragment_sha256: str
    row_count: int
    created_at: datetime


def _receipt_for_existing(
    family: str, fragment_key: str, final: Path, row_count: int
) -> CatalogFragmentReceipt:
    return CatalogFragmentReceipt(
        family=family,
        fragment_key=fragment_key,
        fragment_path=str(final),
        fragment_sha256=sha256_file(str(final)).hex_digest,
        row_count=row_count,
        created_at=datetime.now(UTC),
    )


def publish_immutable_fragment(
    root: Path,
    family_components: list[str],
    filename: str,
    schema: pa.Schema,
    rows: list[dict[str, Any]],
    *,
    clock: Callable[[], datetime],
    ops: Any = None,
) -> CatalogFragmentReceipt:
    """Durably publish ONE immutable fragment; never overwrites anything.

    Pipeline (I04 §23/§24): durable directory chain -> stage -> flush ->
    file fsync -> staged verification (parse + schema + exactly the expected
    rows) -> no-clobber publish -> parent-directory fsync -> fragment hash.

    Raises ``AtomicPublishTargetExists`` when the final already exists — the
    caller reconciles idempotence/conflict from the existing fragment.
    """
    if not rows:
        raise ValueError("an immutable catalog fragment must contain rows")
    family_dir = root.joinpath(*family_components)
    ensure_durable_directory(family_dir)
    # Staging lives at a SHALLOW root-level directory (same filesystem, same
    # device as the final family) so deep family paths can never push a
    # Windows MAX_PATH (260) limit.  It is shared catalog operational space;
    # only the staged FILE is removed after publication.
    staging_dir = root / "catalogs" / "staging"
    ensure_durable_directory(staging_dir)
    nonce = uuid.uuid4().hex
    staged = staging_dir / f"{nonce}.partial"
    final = family_dir / filename
    try:
        table = pa.Table.from_pylist(rows, schema=schema)
        pq.write_table(table, str(staged))
        fsync_file(staged)
        # staged verification: a corrupt/unreadable fragment must never
        # become catalog truth (I04 §24)
        reread = pq.read_table(str(staged))
        if reread.schema != schema:
            raise CatalogIntegrityError(
                f"staged fragment {staged!s} schema mismatch (expected "
                f"{schema}, got {reread.schema})"
            )
        got = reread.to_pylist()
        if len(got) != len(rows):
            raise CatalogIntegrityError(
                f"staged fragment {staged!s} row count {len(got)} != expected "
                f"{len(rows)}"
            )
        for index, (g, e) in enumerate(zip(got, rows)):
            if not _rows_equal(g, e):
                raise CatalogIntegrityError(
                    f"staged fragment {staged!s} row {index} does not match "
                    "the expected record"
                )
        publish_no_replace(staged, final, ops=ops)
        fsync_directory(final.parent)
        digest = sha256_file(str(final))
        return CatalogFragmentReceipt(
            family="/".join(family_components),
            fragment_key=filename,
            fragment_path=str(final),
            fragment_sha256=digest.hex_digest,
            row_count=len(rows),
            created_at=coerce_utc(clock()),
        )
    finally:
        try:
            if staged.exists():
                staged.unlink()
        except OSError:  # pragma: no cover - best-effort cleanup
            pass


def read_fragment(path: Path, schema: pa.Schema) -> list[dict[str, Any]]:
    """Read an existing immutable fragment with schema enforcement.

    Unreadable or schema-mismatched fragments raise CatalogIntegrityError —
    they never become usable catalog truth.
    """
    try:
        table = pq.read_table(str(path))
    except Exception as exc:  # noqa: BLE001 - any read failure is integrity noise
        raise CatalogIntegrityError(
            f"catalog fragment {path!s} is unreadable: {exc}"
        ) from exc
    if table.schema != schema:
        raise CatalogIntegrityError(
            f"catalog fragment {path!s} schema mismatch (expected {schema}, "
            f"got {table.schema})"
        )
    return table.to_pylist()


# ---------------------------------------------------------------------------
# Blob metadata repository (I04 §15/§17/§26/§27/§64/§66-§67)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BlobStorageKey:
    """Physical-object repository key (policy B, I04 §66/§67).

    ``blob_sha256`` remains SOURCE CONTENT identity; ``storage_encoding``
    distinguishes the physical wrapper representations I03 already permits
    for the same H1.
    """

    blob_sha256: str
    storage_encoding: StorageEncoding

    def __post_init__(self) -> None:
        validate_sha256_hex(self.blob_sha256)
        if not isinstance(self.storage_encoding, StorageEncoding):
            raise TypeError("storage_encoding must be a StorageEncoding member")

    @property
    def fragment_name(self) -> str:
        return f"{self.blob_sha256}.{self.storage_encoding.value}.parquet"


class BlobMetadataRepository:
    """Durable append-only EvidenceBlob metadata (one row per physical key).

    Ordering (I04 §26): physical blob durability (I03) comes FIRST; this
    repository verifies the physical object before committing metadata and
    NEVER auto-creates fake metadata from acquisition fields.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        blob_store: LocalBlobStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.root = resolve_catalog_root(root)
        if not isinstance(blob_store, LocalBlobStore):
            raise TypeError("blob_store must be a LocalBlobStore")
        self._blob_store = blob_store
        self._clock: Callable[[], datetime] = (
            clock if clock is not None else lambda: datetime.now(UTC)
        )

    def _now(self) -> datetime:
        return coerce_utc(self._clock())

    def _family_dir(self) -> Path:
        return self.root / "catalogs" / "manifests" / "blobs"

    def _fragment_path(self, key: BlobStorageKey) -> Path:
        return self._family_dir() / key.fragment_name

    def _require_physical_truth(self, blob: EvidenceBlob) -> None:
        """Physical gate (I04 §64): presence is NOT enough.

        The committed object must verify LOCAL_HASH_VERIFIED (or stronger)
        and the stored byte length in the metadata must match the physical
        object size — presence-only blob_exists is insufficient.
        """
        key = BlobStorageKey(blob.blob_sha256, blob.storage_encoding)
        try:
            check = self._blob_store.verify_blob(
                key.blob_sha256,
                key.storage_encoding,
                expected_byte_length=blob.byte_length,
            )
        except BlobMissing as exc:
            raise DanglingBlobReference(
                f"physical blob {key.blob_sha256} ({key.storage_encoding.value}) "
                "missing — metadata cannot be committed for absent bytes"
            ) from exc
        if check.integrity_state is not IntegrityState.LOCAL_HASH_VERIFIED:
            raise CatalogIntegrityError(
                f"physical blob {key.blob_sha256} ({key.storage_encoding.value}) "
                f"failed verification: {check.integrity_state.value} "
                f"({check.detail or 'no detail'})"
            )
        object_path = resolve_under_root(
            self.root, blob_object_key(key.blob_sha256, key.storage_encoding)
        )
        physical_size = os.path.getsize(object_path)
        if physical_size != blob.stored_byte_length:
            raise CatalogIntegrityError(
                f"metadata stored_byte_length {blob.stored_byte_length} != "
                f"physical object size {physical_size} at {object_path!s}"
            )

    def append_metadata(
        self, blob: EvidenceBlob
    ) -> tuple[EvidenceBlob, CatalogFragmentReceipt]:
        """Commit one durable EvidenceBlob metadata row (idempotent).

        Same BlobStorageKey + identical record -> idempotent reuse.
        Same BlobStorageKey + conflicting record -> BlobMetadataConflict
        (never overwrite, never silently choose one — I04 §27).
        """
        key = BlobStorageKey(blob.blob_sha256, blob.storage_encoding)
        self._require_physical_truth(blob)
        rows = [_blob_row(blob)]
        final = self._fragment_path(key)
        try:
            receipt = publish_immutable_fragment(
                self.root,
                ["catalogs", "manifests", "blobs"],
                key.fragment_name,
                BLOB_SCHEMA,
                rows,
                clock=self._clock,
            )
        except AtomicPublishTargetExists:
            existing = read_fragment(final, BLOB_SCHEMA)
            if len(existing) != 1:
                raise CatalogIntegrityError(
                    f"blob metadata fragment {final!s} holds "
                    f"{len(existing)} rows, expected exactly 1"
                ) from None
            if _blob_from_row(existing[0]).model_dump() != blob.model_dump():
                raise BlobMetadataConflict(
                    f"BlobStorageKey {key.blob_sha256}/"
                    f"{key.storage_encoding.value} already has CONFLICTING "
                    "immutable metadata; nothing overwritten (I04 §27)"
                )
            receipt = _receipt_for_existing("blobs", key.fragment_name, final, 1)
        return blob, receipt

    def get_blob_metadata(self, blob_sha256: str) -> list[EvidenceBlob]:
        """All durable metadata rows for one CONTENT hash (all encodings)."""
        validate_sha256_hex(blob_sha256)
        pattern = f"{blob_sha256}.*.parquet"
        matches = sorted(self._family_dir().glob(pattern))
        if not matches:
            raise BlobMetadataNotFound(
                f"no EvidenceBlob metadata for content hash {blob_sha256}"
            )
        blobs: list[EvidenceBlob] = []
        for path in matches:
            rows = read_fragment(path, BLOB_SCHEMA)
            if len(rows) != 1:
                raise CatalogIntegrityError(
                    f"blob metadata fragment {path!s} holds {len(rows)} rows"
                )
            blobs.append(_blob_from_row(rows[0]))
        blobs.sort(key=lambda b: b.storage_encoding.value)
        return blobs

    def get_blob_metadata_exact(
        self, blob_sha256: str, storage_encoding: StorageEncoding
    ) -> EvidenceBlob:
        """The durable metadata row for ONE physical key (typed NotFound)."""
        key = BlobStorageKey(blob_sha256, storage_encoding)
        path = self._fragment_path(key)
        if not path.exists():
            raise BlobMetadataNotFound(
                f"no EvidenceBlob metadata for {key.blob_sha256}/"
                f"{key.storage_encoding.value}"
            )
        rows = read_fragment(path, BLOB_SCHEMA)
        if len(rows) != 1:
            raise CatalogIntegrityError(
                f"blob metadata fragment {path!s} holds {len(rows)} rows"
            )
        return _blob_from_row(rows[0])

    def has_verified_physical(self, blob_sha256: str) -> bool:
        """True when >=1 durable, non-quarantined, physically verifying row exists.

        Used by manifest referential checks (I04 §68): the check passes if at
        least one non-quarantined verified physical representation exists;
        all physical metadata is recorded independently.
        """
        try:
            metas = self.get_blob_metadata(blob_sha256)
        except BlobMetadataNotFound:
            return False
        for meta in metas:
            if meta.integrity_state in (
                IntegrityState.QUARANTINED_INTEGRITY_FAILURE,
                IntegrityState.MISSING_BLOB,
                IntegrityState.PROJECTION_INVALID,
            ):
                continue
            try:
                check = self._blob_store.verify_blob(
                    meta.blob_sha256,
                    meta.storage_encoding,
                    expected_byte_length=meta.byte_length,
                )
            except BlobMissing:
                continue
            if check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED:
                return True
        return False


# ---------------------------------------------------------------------------
# Acquisition repository (I04 §15/§18/§26/§28/§29/§70)
# ---------------------------------------------------------------------------


class AcquisitionRepository:
    """Durable append-only AcquisitionRecord history (one row per event).

    Repeated fetches are expected: different acquisition_ids may reference
    the same blob hash — only physical bytes are deduped, acquisition
    history is not (I04 §29).  A successful acquisition requires its blob's
    durable metadata + verified physical bytes first (I04 §12/§26); a
    blob-less record must be explicitly explainable (I04 §13).
    """

    def __init__(
        self,
        root: str | Path,
        *,
        blob_store: LocalBlobStore,
        blob_metadata_repository: BlobMetadataRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.root = resolve_catalog_root(root)
        self._blob_store = blob_store
        self._blob_metadata_repository = blob_metadata_repository
        self._clock: Callable[[], datetime] = (
            clock if clock is not None else lambda: datetime.now(UTC)
        )

    def _family_dir(self) -> Path:
        return self.root / "catalogs" / "manifests" / "acquisitions"

    @staticmethod
    def _fragment_name(acquisition_id: str) -> str:
        # physical locator only (I04 §21): logical id stays authoritative.
        return f"{hashlib.sha256(acquisition_id.encode('utf-8')).hexdigest()}.parquet"

    def _fragment_path(self, acquisition_id: str) -> Path:
        return self._family_dir() / self._fragment_name(acquisition_id)

    def _validate_blob_linkage(self, record: AcquisitionRecord) -> None:
        """I04 §12/§13/§14: blob truth before acquisition fact."""
        if record.blob_sha256 is not None:
            try:
                metas = self._blob_metadata_repository.get_blob_metadata(
                    record.blob_sha256
                )
            except BlobMetadataNotFound as exc:
                raise DanglingBlobReference(
                    "acquisition references blob "
                    f"{record.blob_sha256} but no durable EvidenceBlob "
                    "metadata exists (I04 §12/§26)"
                ) from exc
            if not metas:
                raise DanglingBlobReference(
                    f"acquisition references blob {record.blob_sha256} with no "
                    "durable metadata rows"
                )
            verified = False
            for meta in metas:
                if meta.integrity_state in (
                    IntegrityState.QUARANTINED_INTEGRITY_FAILURE,
                    IntegrityState.MISSING_BLOB,
                    IntegrityState.PROJECTION_INVALID,
                ):
                    continue
                try:
                    check = self._blob_store.verify_blob(
                        meta.blob_sha256,
                        meta.storage_encoding,
                        expected_byte_length=meta.byte_length,
                    )
                except BlobMissing:
                    continue
                if check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED:
                    verified = True
                    break
            if not verified:
                raise DanglingBlobReference(
                    f"acquisition references blob {record.blob_sha256} but no "
                    "physically verified representation exists (I04 §12)"
                )
        else:
            # blob_sha256 absent ONLY when the record truthfully represents a
            # failure/non-payload outcome (I04 §13): explicit failure_ref OR
            # an explicit failed/unavailable source status is required.
            status = record.http_status_or_source_status
            explainable = record.failure_ref is not None or (
                status is not None and not status.startswith("2")
            )
            if not explainable:
                raise CatalogIntegrityError(
                    "successful acquisition without a blob and without "
                    "explicit failure/unavailable evidence cannot be "
                    "persisted (I04 §13)"
                )

    def append_acquisition(
        self, record: AcquisitionRecord
    ) -> tuple[AcquisitionRecord, CatalogFragmentReceipt]:
        """Commit one durable acquisition row (idempotent by acquisition_id).

        Same acquisition_id + exact same semantic record -> idempotent.
        Same acquisition_id + any differing field -> AcquisitionIdentityConflict
        (never mutate old acquisition facts — I04 §28/§70).
        """
        self._validate_blob_linkage(record)
        rows = [_acquisition_row(record)]
        final = self._fragment_path(record.acquisition_id)
        try:
            receipt = publish_immutable_fragment(
                self.root,
                ["catalogs", "manifests", "acquisitions"],
                self._fragment_name(record.acquisition_id),
                ACQUISITION_SCHEMA,
                rows,
                clock=self._clock,
            )
        except AtomicPublishTargetExists:
            existing = read_fragment(final, ACQUISITION_SCHEMA)
            if len(existing) != 1:
                raise CatalogIntegrityError(
                    f"acquisition fragment {final!s} holds {len(existing)} "
                    "rows, expected exactly 1"
                ) from None
            if _acquisition_from_row(existing[0]).model_dump() != record.model_dump():
                raise AcquisitionIdentityConflict(
                    f"acquisition_id {record.acquisition_id} already committed "
                    "with DIFFERENT immutable facts; first append wins, "
                    "nothing overwritten (I04 §28)"
                )
            receipt = _receipt_for_existing(
                "acquisitions", self._fragment_name(record.acquisition_id), final, 1
            )
        return record, receipt

    def get_acquisition(self, acquisition_id: str) -> AcquisitionRecord:
        """Typed NotFound for a missing id (I04 §50)."""
        path = self._fragment_path(acquisition_id)
        if not path.exists():
            raise AcquisitionNotFound(
                f"no AcquisitionRecord for acquisition_id {acquisition_id}"
            )
        rows = read_fragment(path, ACQUISITION_SCHEMA)
        if len(rows) != 1:
            raise CatalogIntegrityError(
                f"acquisition fragment {path!s} holds {len(rows)} rows"
            )
        return _acquisition_from_row(rows[0])


# ---------------------------------------------------------------------------
# Facade (I04 §15 — optional single entry point; NOT a god class)
# ---------------------------------------------------------------------------


class LocalEvidenceCatalog:
    """Convenience facade over the three I04 repositories.

    The repositories are independently usable; this facade wires them to one
    configured root + blob store + clock for evidence/tests.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        blob_store: LocalBlobStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        # imported lazily: manifests.py imports catalog.py at module level
        from .manifests import PartitionManifestRepository  # noqa: PLC0415

        self.root = resolve_catalog_root(root)
        self.blob_metadata = BlobMetadataRepository(
            root, blob_store=blob_store, clock=clock
        )
        self.acquisitions = AcquisitionRepository(
            root,
            blob_store=blob_store,
            blob_metadata_repository=self.blob_metadata,
            clock=clock,
        )
        self.manifests = PartitionManifestRepository(
            root,
            blob_store=blob_store,
            blob_metadata_repository=self.blob_metadata,
            clock=clock,
        )


__all__ = [
    "ACQUISITION_SCHEMA",
    "AcquisitionIdentityConflict",
    "AcquisitionNotFound",
    "AcquisitionRepository",
    "BLOB_SCHEMA",
    "BlobMetadataConflict",
    "BlobMetadataNotFound",
    "BlobMetadataRepository",
    "BlobStorageKey",
    "CatalogDurabilityError",
    "CatalogError",
    "CatalogFragmentReceipt",
    "CatalogIntegrityError",
    "CatalogNotFound",
    "DanglingBlobReference",
    "LocalEvidenceCatalog",
    "ProjectionReferenceUnavailable",
    "canonical_nested_json",
    "model_canonical_json",
    "publish_immutable_fragment",
    "read_fragment",
    "resolve_catalog_root",
]