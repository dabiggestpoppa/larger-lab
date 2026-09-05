"""SENSOR-B4-I04C — append-only PartitionManifest repository + current pointer.

The logical manifest layer of the durable acquisition catalog:

- every ``PartitionManifest`` version is persisted as an IMMUTABLE, COMPLETE
  logical snapshot fragment (never an in-place delta) under
  ``<t0_root>/catalogs/manifests/partitions/<partition-key-hash>/``;
- a small MUTABLE operational ``PartitionCurrentPointer`` under
  ``<t0_root>/catalogs/current/partitions/`` is the ONLY overwrite-allowed
  state (I04 §34-§36): readers observe either the OLD valid pointer or the
  NEW valid pointer, never partial JSON;
- partition-scoped writer coordination via an atomic ``mkdir`` no-replace
  lock (I04 §37/§38) + expected-current CAS (I04 §40): a stale writer gets
  ``ManifestCASConflict`` and must recompute explicitly — it may not
  silently rewrite the chain;
- the pointer crash matrix P1-P5 is injectable (I04 §42/§43): a visible
  pointer is never treated as a proven durable pointer.

LOCAL truth only (I04 §39): this is filesystem CAS for local multi-process
writers, NOT distributed consensus; I11 owns database-backed coordination.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Protocol

import pyarrow as pa

from ..contracts.base import coerce_utc
from ..providers.base.enums import Granularity
from .atomic import (
    AtomicPublishTargetExists,
    ensure_durable_directory,
    fsync_directory,
    fsync_file,
)
from .blob_store import LocalBlobStore
from .catalog import (
    BlobMetadataNotFound,
    BlobMetadataRepository,
    CatalogError,
    CatalogFragmentReceipt,
    CatalogIntegrityError,
    CatalogNotFound,
    ManifestNotFound,
    ProjectionReferenceUnavailable,
    _rows_equal,
    publish_immutable_fragment,
    read_fragment,
    resolve_catalog_root,
)
from .checksums import sha256_file, validate_sha256_hex
from .enums import CoverageState, DateBasis, IntegrityState
from .models import PartitionManifest

# ---------------------------------------------------------------------------
# Typed manifest errors (I04 §76)
# ---------------------------------------------------------------------------


class ManifestIdentityConflict(CatalogError):
    """Same manifest_id with different immutable content, or partition
    identity coordinates drifting across versions (I04 §32/§33)."""


class ManifestVersionConflict(CatalogError):
    """Version rules violated: gaps, non-sequential bump, supersedes != current."""


class ManifestCASConflict(CatalogError):
    """expected_current does not match the actual current pointer (I04 §40).

    A stale writer fails; it is NEVER auto-promoted to a newer version and
    never silently rebased onto a newer base.
    """


class ManifestLockHeld(CatalogError):
    """The partition lock directory already exists (I04 §37/§38).

    A crash may leave the lock: I04 NEVER auto-deletes stale locks and
    reports ManifestLockHeld / RecoveryRequired; I08 owns reconciliation.
    """


class CurrentPointerCorrupt(CatalogError):
    """The current pointer file exists but is not valid operational state."""


class CurrentPointerDangling(CatalogError):
    """The current pointer references a missing/corrupt manifest fragment."""


# ---------------------------------------------------------------------------
# Pointer fault injection (I04 §42 — P1..P5 deterministic crash matrix)
# ---------------------------------------------------------------------------


class PointerFaultPoint(str, Enum):
    P1 = "P1"  # before manifest publication
    P2 = "P2"  # after manifest publication / before pointer stage
    P3 = "P3"  # after pointer stage+fsync / before pointer replace
    P4 = "P4"  # after pointer replace / before parent fsync
    P5 = "P5"  # after parent fsync / before return


class PointerFaultHook(Protocol):
    def raise_if(self, point: PointerFaultPoint) -> None: ...  # pragma: no cover


class RaisePointerFaultHook:
    """Raise a deterministic RuntimeError at each configured point."""

    def __init__(self, *points: PointerFaultPoint) -> None:
        self._points = frozenset(points)

    def raise_if(self, point: PointerFaultPoint) -> None:
        if point in self._points:
            raise RuntimeError(f"injected pointer fault at {point.value}")

    def points(self) -> frozenset[PointerFaultPoint]:
        return self._points


class ManifestDisposition(str, Enum):
    COMMITTED_NEW = "COMMITTED_NEW"
    IDEMPOTENT_COMPLETION = "IDEMPOTENT_COMPLETION"


@dataclass(frozen=True)
class ManifestAppendResult:
    manifest: PartitionManifest
    current_pointer: PartitionCurrentPointer
    disposition: ManifestDisposition
    fragment_receipt: CatalogFragmentReceipt


# ---------------------------------------------------------------------------
# Current pointer (operational state, I04 §34/§35)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PartitionCurrentPointer:
    """Small operational pointer — NOT historical raw evidence."""

    partition_key: str
    partition_manifest_id: str
    manifest_version: int
    previous_manifest_id: str | None
    updated_at: datetime

    def to_canonical_json(self) -> str:
        payload = {
            "partition_key": self.partition_key,
            "partition_manifest_id": self.partition_manifest_id,
            "manifest_version": self.manifest_version,
            "previous_manifest_id": self.previous_manifest_id,
            "updated_at": self.updated_at.isoformat(),
        }
        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    @classmethod
    def from_canonical_json(cls, text: str) -> PartitionCurrentPointer:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CurrentPointerCorrupt(
                f"current pointer is not valid JSON: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise CurrentPointerCorrupt("current pointer must be a JSON object")
        try:
            partition_key = str(payload["partition_key"])
            manifest_id = str(payload["partition_manifest_id"])
            version = int(payload["manifest_version"])
            previous = payload.get("previous_manifest_id")
            previous_id: str | None = (
                None if previous is None else str(previous)
            )
            updated_at = datetime.fromisoformat(str(payload["updated_at"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise CurrentPointerCorrupt(
                f"current pointer missing/invalid fields: {exc}"
            ) from exc
        if not partition_key or not manifest_id or version < 1:
            raise CurrentPointerCorrupt(
                "current pointer carries invalid identity fields"
            )
        if updated_at.tzinfo is None:
            raise CurrentPointerCorrupt(
                "current pointer updated_at must be timezone-aware"
            )
        return cls(
            partition_key=partition_key,
            partition_manifest_id=manifest_id,
            manifest_version=version,
            previous_manifest_id=previous_id,
            updated_at=coerce_utc(updated_at),
        )


# ---------------------------------------------------------------------------
# Stable Arrow schema for partition manifest fragments (I04 §19)
# ---------------------------------------------------------------------------

_TIMESTAMP = pa.timestamp("us", tz="UTC")


def _field(name: str, type_: pa.DataType, nullable: bool) -> pa.Field:
    return pa.field(name, type_, nullable=nullable)


MANIFEST_SCHEMA = pa.schema(
    [
        _field("partition_manifest_id", pa.string(), False),
        _field("partition_key", pa.string(), False),
        _field("manifest_version", pa.int64(), False),
        _field("provider", pa.string(), False),
        _field("venue", pa.string(), False),
        _field("sensor_family", pa.string(), False),
        _field("native_instrument", pa.string(), False),
        _field("source_granularity", pa.string(), True),
        _field("date_basis", pa.string(), False),
        _field("logical_date_start", _TIMESTAMP, False),
        _field("logical_date_end", _TIMESTAMP, False),
        _field("blob_refs", pa.list_(pa.string()), False),
        _field("projection_refs", pa.list_(pa.string()), False),
        _field("coverage_state", pa.string(), False),
        _field("integrity_state", pa.string(), False),
        _field("row_count", pa.int64(), True),
        _field("min_time", _TIMESTAMP, True),
        _field("max_time", _TIMESTAMP, True),
        _field("gap_count", pa.int64(), True),
        _field("revision_count", pa.int64(), False),
        _field("created_at", _TIMESTAMP, False),
        _field("supersedes_manifest_id", pa.string(), True),
    ]
)


def _manifest_row(manifest: PartitionManifest) -> dict[str, Any]:
    return {
        "partition_manifest_id": manifest.partition_manifest_id,
        "partition_key": manifest.partition_key,
        "manifest_version": manifest.manifest_version,
        "provider": manifest.provider,
        "venue": manifest.venue,
        "sensor_family": manifest.sensor_family.value,
        "native_instrument": manifest.native_instrument,
        "source_granularity": (
            manifest.source_granularity.value
            if manifest.source_granularity is not None
            else None
        ),
        "date_basis": manifest.date_basis.value,
        "logical_date_start": manifest.logical_date_start,
        "logical_date_end": manifest.logical_date_end,
        "blob_refs": list(manifest.blob_refs),
        "projection_refs": list(manifest.projection_refs),
        "coverage_state": manifest.coverage_state.value,
        "integrity_state": manifest.integrity_state.value,
        "row_count": manifest.row_count,
        "min_time": manifest.min_time,
        "max_time": manifest.max_time,
        "gap_count": manifest.gap_count,
        "revision_count": manifest.revision_count,
        "created_at": manifest.created_at,
        "supersedes_manifest_id": manifest.supersedes_manifest_id,
    }


def _manifest_from_row(row: dict[str, Any]) -> PartitionManifest:
    return PartitionManifest(
        partition_manifest_id=row["partition_manifest_id"],
        partition_key=row["partition_key"],
        manifest_version=row["manifest_version"],
        provider=row["provider"],
        venue=row["venue"],
        sensor_family=row["sensor_family"],
        native_instrument=row["native_instrument"],
        source_granularity=(
            Granularity(row["source_granularity"])
            if row["source_granularity"] is not None
            else None
        ),
        date_basis=DateBasis(row["date_basis"]),
        logical_date_start=row["logical_date_start"],
        logical_date_end=row["logical_date_end"],
        blob_refs=list(row["blob_refs"]),
        projection_refs=list(row["projection_refs"]),
        coverage_state=CoverageState(row["coverage_state"]),
        integrity_state=IntegrityState(row["integrity_state"]),
        row_count=row["row_count"],
        min_time=row["min_time"],
        max_time=row["max_time"],
        gap_count=row["gap_count"],
        revision_count=row["revision_count"],
        created_at=row["created_at"],
        supersedes_manifest_id=row["supersedes_manifest_id"],
    )


def _partition_hash(partition_key: str) -> str:
    """32-hex physical locator for a partition (I04 §21).

    The hash is ONLY a physical catalog key — the EXACT original
    partition_key is stored inside every fragment and current pointer, so
    truncation never loses identity and keeps deep catalog paths well under
    Windows' MAX_PATH limit.
    """
    return hashlib.sha256(partition_key.encode("utf-8")).hexdigest()[:32]


_POINTER_REPLACE_RETRIES = 25
_POINTER_REPLACE_RETRY_SLEEP_S = 0.005


def _atomic_replace_pointer(staged: Path, final: Path) -> None:
    """Atomic pointer replacement tolerating transient reader file locks.

    The pointer is MUTABLE operational state (I04 §36): readers may briefly
    hold the pointer file open while reading it.  On Windows an open file
    handle blocks os.replace with PermissionError; a bounded retry absorbs
    that transient contention while preserving old-or-new visibility.  The
    replace itself is still atomic when it succeeds — a reader can never
    observe partial pointer content.
    """
    import time

    for attempt in range(_POINTER_REPLACE_RETRIES):
        try:
            os.replace(staged, final)
            return
        except PermissionError:
            if attempt == _POINTER_REPLACE_RETRIES - 1:
                raise
            time.sleep(_POINTER_REPLACE_RETRY_SLEEP_S)


def _manifest_fragment_name(manifest: PartitionManifest) -> str:
    # version-prefixed + content-id-hashed physical locator (I04 §21):
    # <version> is logical truth; the hash is only a physical key.
    id_hash = hashlib.sha256(manifest.partition_manifest_id.encode("utf-8")).hexdigest()[:32]
    return f"v{manifest.manifest_version:08d}-{id_hash}.parquet"


def _integrity_strength(state: IntegrityState) -> int:
    """Strength order for claim checks (I04 §46): UNVERIFIED < LOCAL < PROVIDER.

    Quarantined/missing are NOT a strength: they fail referential checks.
    """
    return {
        IntegrityState.UNVERIFIED: 0,
        IntegrityState.LOCAL_HASH_VERIFIED: 1,
        IntegrityState.PROVIDER_HASH_VERIFIED: 2,
    }.get(state, -1)


class PartitionManifestRepository:
    """Append-only manifest versions + transactional current pointer.

    Write protocol (I04 §41), all inside the partition lock:

      A. validate physical blob refs
      B. validate blob metadata refs
      C. validate expected current
      D. write/verify/publish immutable manifest fragment
      E. stage new current pointer
      F. fsync pointer file
      G. atomic replace current pointer
      H. fsync pointer parent directory
      I. success

    Failure before D: nothing new.  Failure after D before pointer update:
    an immutable ORPHAN manifest fragment may exist; current stays old; it is
    never deleted automatically (I04 §44).
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

    def _now(self) -> datetime:
        return coerce_utc(self._clock())

    # -- paths ---------------------------------------------------------------

    def _partitions_dir(self, partition_hash: str) -> Path:
        return self.root / "catalogs" / "manifests" / "partitions" / partition_hash

    def _pointer_dir(self) -> Path:
        return self.root / "catalogs" / "current" / "partitions"

    def _pointer_path(self, partition_hash: str) -> Path:
        return self._pointer_dir() / f"{partition_hash}.json"

    def _lock_dir(self, partition_hash: str) -> Path:
        return self.root / "catalogs" / "locks" / "partitions" / f"{partition_hash}.lock"

    # -- partition lock (I04 §37/§38) ----------------------------------------

    def _acquire_lock(self, partition_hash: str) -> Path:
        lock_dir = self._lock_dir(partition_hash)
        ensure_durable_directory(lock_dir.parent)
        try:
            os.mkdir(lock_dir)
        except FileExistsError as exc:
            raise ManifestLockHeld(
                f"partition lock held at {lock_dir!s}; RecoveryRequired — "
                "I04 never auto-deletes stale locks (I08 owns reconciliation)"
            ) from exc
        return lock_dir

    def _release_lock(self, lock_dir: Path) -> None:
        try:
            lock_dir.rmdir()
        except OSError as exc:  # pragma: no cover - defensive
            raise CatalogError(
                f"could not release partition lock {lock_dir!s}: {exc}"
            ) from exc

    # -- pointer read/validate (I04 §62) -------------------------------------

    def read_current_pointer(self, partition_key: str) -> PartitionCurrentPointer | None:
        """Raw operational pointer state (None when no pointer exists yet)."""
        path = self._pointer_path(_partition_hash(partition_key))
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CurrentPointerCorrupt(
                f"current pointer {path!s} unreadable: {exc}"
            ) from exc
        return PartitionCurrentPointer.from_canonical_json(text)

    def _load_manifest_fragment(
        self, pointer: PartitionCurrentPointer
    ) -> PartitionManifest:
        partition_hash = _partition_hash(pointer.partition_key)
        name = (
            f"v{pointer.manifest_version:08d}-"
            f"{hashlib.sha256(pointer.partition_manifest_id.encode('utf-8')).hexdigest()[:32]}"
            ".parquet"
        )
        path = self._partitions_dir(partition_hash) / name
        if not path.exists():
            raise CurrentPointerDangling(
                f"current pointer references missing manifest fragment "
                f"{path!s} ({pointer.partition_manifest_id})"
            )
        rows = read_fragment(path, MANIFEST_SCHEMA)
        if len(rows) != 1:
            raise CurrentPointerDangling(
                f"manifest fragment {path!s} holds {len(rows)} rows"
            )
        manifest = _manifest_from_row(rows[0])
        if manifest.partition_manifest_id != pointer.partition_manifest_id:
            raise CurrentPointerDangling(
                "current pointer manifest_id does not match the referenced "
                "fragment content"
            )
        if manifest.manifest_version != pointer.manifest_version:
            raise CurrentPointerDangling(
                "current pointer version does not match the referenced "
                "fragment version"
            )
        if manifest.partition_key != pointer.partition_key:
            raise CurrentPointerDangling(
                "current pointer partition_key does not match the referenced "
                "fragment"
            )
        return manifest

    def _read_validated_pointer(self, partition_key: str) -> PartitionCurrentPointer | None:
        """Read + validate the pointer against its referenced fragment."""
        pointer = self.read_current_pointer(partition_key)
        if pointer is not None:
            self._load_manifest_fragment(pointer)
        return pointer

    # -- manifest reads (I04 §49/§50) ----------------------------------------

    def get_manifest(self, manifest_id: str) -> PartitionManifest:
        """Typed NotFound for a missing manifest id."""
        fragments_dir = self.root / "catalogs" / "manifests" / "partitions"
        if not fragments_dir.exists():
            raise ManifestNotFound(f"no PartitionManifest for id {manifest_id}")
        for partition_dir in sorted(fragments_dir.iterdir()):
            if not partition_dir.is_dir():
                continue
            for path in sorted(partition_dir.glob("v*.parquet")):
                rows = read_fragment(path, MANIFEST_SCHEMA)
                if len(rows) != 1:
                    raise CatalogIntegrityError(
                        f"manifest fragment {path!s} holds {len(rows)} rows"
                    )
                manifest = _manifest_from_row(rows[0])
                if manifest.partition_manifest_id == manifest_id:
                    return manifest
        raise ManifestNotFound(f"no PartitionManifest for id {manifest_id}")

    def get_current_manifest(self, partition_key: str) -> PartitionManifest:
        pointer = self._read_validated_pointer(partition_key)
        if pointer is None:
            raise ManifestNotFound(
                f"no current PartitionManifest for partition_key {partition_key}"
            )
        return self._load_manifest_fragment(pointer)

    def list_manifest_versions(self, partition_key: str) -> list[PartitionManifest]:
        """Committed manifest chain v1..vN (current follows the pointer)."""
        pointer = self._read_validated_pointer(partition_key)
        if pointer is None:
            return []
        chain: list[PartitionManifest] = []
        seen: set[str] = set()
        current: PartitionManifest | None = self._load_manifest_fragment(pointer)
        while current is not None:
            if current.partition_manifest_id in seen:
                raise CatalogIntegrityError(
                    "manifest chain contains a cycle (supersedes loop)"
                )
            seen.add(current.partition_manifest_id)
            chain.append(current)
            if current.supersedes_manifest_id is None:
                break
            current = self.get_manifest(current.supersedes_manifest_id)
        chain.sort(key=lambda m: m.manifest_version)
        if [m.manifest_version for m in chain] != list(
            range(1, len(chain) + 1)
        ):
            raise CatalogIntegrityError(
                "committed manifest chain has version gaps — history must "
                "never be rewritten, this is corruption"
            )
        return chain

    def list_orphan_manifest_fragments(
        self, partition_key: str
    ) -> list[PartitionManifest]:
        """Forensic view: published fragments NOT in the committed chain."""
        chain_ids = {m.partition_manifest_id for m in self.list_manifest_versions(partition_key)}
        partition_hash = _partition_hash(partition_key)
        fragments_dir = self._partitions_dir(partition_hash)
        orphans: list[PartitionManifest] = []
        if fragments_dir.exists():
            for path in sorted(fragments_dir.glob("v*.parquet")):
                rows = read_fragment(path, MANIFEST_SCHEMA)
                if len(rows) != 1:
                    raise CatalogIntegrityError(
                        f"manifest fragment {path!s} holds {len(rows)} rows"
                    )
                manifest = _manifest_from_row(rows[0])
                if manifest.partition_manifest_id not in chain_ids:
                    orphans.append(manifest)
        orphans.sort(key=lambda m: (m.manifest_version, m.partition_manifest_id))
        return orphans

    # -- referential integrity (I04 §45/§46/§47/§68) --------------------------

    def _verify_blob_ref(self, blob_sha256: str) -> None:
        validate_sha256_hex(blob_sha256)
        try:
            metas = self._blob_metadata_repository.get_blob_metadata(blob_sha256)
        except BlobMetadataNotFound as exc:
            raise CatalogIntegrityError(
                f"manifest blob_ref {blob_sha256} has no durable blob "
                "metadata (I04 §45)"
            ) from exc
        best_strength = -1
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
            except Exception:  # noqa: BLE001 - absence/corruption is a ref failure
                continue
            if check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED:
                best_strength = max(best_strength, _integrity_strength(meta.integrity_state))
        if best_strength < 0:
            raise CatalogIntegrityError(
                f"manifest blob_ref {blob_sha256} has no physically verified "
                "representation (I04 §45/§68)"
            )

    def _validate_referential_integrity(self, manifest: PartitionManifest) -> None:
        if manifest.projection_refs:
            raise ProjectionReferenceUnavailable(
                "PartitionManifest carries projection_refs but I05 owns T0B "
                "projections — I04 manifest writes keep projection_refs "
                "EMPTY and fail closed on dangling projection refs (I04 §20)"
            )
        if not manifest.blob_refs:
            if _integrity_strength(manifest.integrity_state) > 0:
                raise CatalogIntegrityError(
                    "manifest with no blob_refs may only claim "
                    "integrity_state UNVERIFIED — a stronger claim would be "
                    "vacuous (I04 §46)"
                )
            return
        claim = _integrity_strength(manifest.integrity_state)
        for ref in manifest.blob_refs:
            # full metadata + physical verification for every ref
            self._verify_blob_ref(ref)
        # strength ceiling: never claim stronger than the weakest ref
        if claim > 0:
            ref_strengths: list[int] = []
            for ref in manifest.blob_refs:
                metas = self._blob_metadata_repository.get_blob_metadata(ref)
                ref_strengths.append(
                    max(_integrity_strength(m.integrity_state) for m in metas)
                )
            if claim > min(ref_strengths):
                raise CatalogIntegrityError(
                    "manifest integrity claim stronger than referenced "
                    "evidence supports (I04 §46)"
                )

    # -- partition identity (I04 §30/§32) ------------------------------------

    @staticmethod
    def _identity_coordinates(manifest: PartitionManifest) -> tuple[Any, ...]:
        return (
            manifest.provider,
            manifest.venue,
            manifest.sensor_family,
            manifest.native_instrument,
            manifest.source_granularity,
            manifest.date_basis,
            manifest.logical_date_start,
            manifest.logical_date_end,
        )

    def _validate_partition_identity(
        self, manifest: PartitionManifest, current: PartitionManifest
    ) -> None:
        if self._identity_coordinates(manifest) != self._identity_coordinates(current):
            raise ManifestIdentityConflict(
                "manifest partition identity coordinates (provider/venue/"
                "sensor_family/native_instrument/source_granularity/date_basis/"
                "logical range) drift across versions (I04 §32)"
            )

    # -- pointer durability re-establishment (I04 §43) -----------------------

    def _reestablish_pointer_durability(
        self, manifest: PartitionManifest, pointer: PartitionCurrentPointer
    ) -> None:
        """Retry after P4/P5 (visible != proven durable).

        Validates pointer content, the referenced manifest fragment, and the
        referenced blobs, then fsyncs the pointer parent directory before
        returning success.
        """
        fragment = self._load_manifest_fragment(pointer)
        if fragment.model_dump() != manifest.model_dump():
            raise CurrentPointerDangling(
                "current pointer references a manifest whose content differs "
                "from the retried manifest"
            )
        if pointer.previous_manifest_id != manifest.supersedes_manifest_id:
            raise CurrentPointerDangling(
                "current pointer previous_manifest_id does not match the "
                "referenced manifest"
            )
        self._validate_referential_integrity(manifest)
        fsync_directory(self._pointer_dir())

    # -- main append ---------------------------------------------------------

    def append_partition_manifest(
        self,
        manifest: PartitionManifest,
        expected_current: tuple[str, int] | None,
        *,
        fault_hooks: PointerFaultHook | None = None,
    ) -> ManifestAppendResult:
        """Commit ONE immutable manifest version + advance the current pointer.

        ``expected_current`` is the (manifest_id, version) the caller
        believes is current: None for v1, the current pair for vN.  Any
        divergence raises ``ManifestCASConflict`` (I04 §40) — no silent
        retry onto a newer base.
        """
        hook = fault_hooks if fault_hooks is not None else RaisePointerFaultHook()
        partition_hash = _partition_hash(manifest.partition_key)
        lock_dir = self._acquire_lock(partition_hash)
        try:
            current = self._read_validated_pointer(manifest.partition_key)

            # Idempotent completion (I04 §43/§44): the pointer ALREADY
            # references this exact manifest (duplicate append or retry after
            # P4/P5).  Visible pointer != proven durable pointer — re-prove
            # durability, then succeed.
            if current is not None and (
                current.partition_manifest_id == manifest.partition_manifest_id
            ):
                self._reestablish_pointer_durability(manifest, current)
                receipt = self._receipt_for_manifest(manifest, partition_hash)
                return ManifestAppendResult(
                    manifest=manifest,
                    current_pointer=current,
                    disposition=ManifestDisposition.IDEMPOTENT_COMPLETION,
                    fragment_receipt=receipt,
                )

            # CAS + version rules (I04 §31/§32/§33/§40)
            if current is None:
                if expected_current is not None:
                    raise ManifestCASConflict(
                        "expected_current supplied but no current manifest "
                        "exists for the partition (I04 §31)"
                    )
                if manifest.manifest_version != 1:
                    raise ManifestVersionConflict(
                        "first manifest must be version 1 "
                        f"(got {manifest.manifest_version})"
                    )
                if manifest.supersedes_manifest_id is not None:
                    raise ManifestVersionConflict(
                        "first manifest (v1) must have "
                        "supersedes_manifest_id=None"
                    )
            else:
                if expected_current != (
                    current.partition_manifest_id,
                    current.manifest_version,
                ):
                    raise ManifestCASConflict(
                        f"expected_current {expected_current!r} != actual "
                        f"current ({(current.partition_manifest_id, current.manifest_version)!r}); "
                        "stale writer — recompute explicitly, no auto-rebase "
                        "(I04 §40/§73)"
                    )
                if manifest.manifest_version != current.manifest_version + 1:
                    raise ManifestVersionConflict(
                        "manifest version must be current + 1 "
                        f"(current {current.manifest_version}, got "
                        f"{manifest.manifest_version}); no version gaps "
                        "(I04 §33)"
                    )
                if manifest.supersedes_manifest_id != current.partition_manifest_id:
                    raise ManifestVersionConflict(
                        "supersedes_manifest_id must equal the CURRENT "
                        "manifest id (I04 §33)"
                    )
                current_manifest = self._load_manifest_fragment(current)
                self._validate_partition_identity(manifest, current_manifest)

            # referential integrity BEFORE any publication (I04 §41 A/B)
            self._validate_referential_integrity(manifest)

            hook.raise_if(PointerFaultPoint.P1)  # before manifest publication

            # D: publish the immutable manifest fragment
            final = self._partitions_dir(partition_hash) / _manifest_fragment_name(manifest)
            fragment_rows = [_manifest_row(manifest)]
            try:
                receipt = publish_immutable_fragment(
                    self.root,
                    ["catalogs", "manifests", "partitions", partition_hash],
                    _manifest_fragment_name(manifest),
                    MANIFEST_SCHEMA,
                    fragment_rows,
                    clock=self._clock,
                )
            except AtomicPublishTargetExists:
                existing = read_fragment(final, MANIFEST_SCHEMA)
                if len(existing) != 1:
                    raise CatalogIntegrityError(
                        f"manifest fragment {final!s} holds {len(existing)} rows"
                    ) from None
                if not _rows_equal(existing[0], fragment_rows[0]):
                    raise ManifestIdentityConflict(
                        "same manifest_id already committed with DIFFERENT "
                        "immutable content (I04 §33/§44)"
                    )
                # orphan retry / exact duplicate: fragment matches; proceed
                # to the intended pointer transition (base still permits it)
                receipt = self._receipt_for_manifest(manifest, partition_hash)

            hook.raise_if(PointerFaultPoint.P2)  # after publish, before stage

            # E/F: stage + fsync the new pointer
            pointer = PartitionCurrentPointer(
                partition_key=manifest.partition_key,
                partition_manifest_id=manifest.partition_manifest_id,
                manifest_version=manifest.manifest_version,
                previous_manifest_id=manifest.supersedes_manifest_id,
                updated_at=self._now(),
            )
            pointer_dir = self._pointer_dir()
            ensure_durable_directory(pointer_dir)
            pointer_final = self._pointer_path(partition_hash)
            pointer_staged = pointer_dir / f".{partition_hash}.pointer.tmp"
            pointer_staged.write_text(
                pointer.to_canonical_json() + "\n", encoding="utf-8"
            )
            fsync_file(pointer_staged)

            hook.raise_if(PointerFaultPoint.P3)  # after stage, before replace

            # G: atomic replace (pointer is MUTABLE operational state)
            _atomic_replace_pointer(pointer_staged, pointer_final)

            hook.raise_if(PointerFaultPoint.P4)  # after replace, before fsync

            # H: pointer parent durability
            fsync_directory(pointer_dir)

            hook.raise_if(PointerFaultPoint.P5)  # after fsync, before return

            return ManifestAppendResult(
                manifest=manifest,
                current_pointer=pointer,
                disposition=ManifestDisposition.COMMITTED_NEW,
                fragment_receipt=receipt,
            )
        finally:
            self._release_lock(lock_dir)

    def _receipt_for_manifest(
        self, manifest: PartitionManifest, partition_hash: str
    ) -> CatalogFragmentReceipt:
        final = self._partitions_dir(partition_hash) / _manifest_fragment_name(manifest)
        return CatalogFragmentReceipt(
            family="catalogs/manifests/partitions",
            fragment_key=_manifest_fragment_name(manifest),
            fragment_path=str(final),
            fragment_sha256=sha256_file(str(final)).hex_digest,
            row_count=1,
            created_at=self._now(),
        )


__all__ = [
    "CatalogError",
    "CatalogNotFound",
    "CurrentPointerCorrupt",
    "CurrentPointerDangling",
    "MANIFEST_SCHEMA",
    "ManifestAppendResult",
    "ManifestCASConflict",
    "ManifestDisposition",
    "ManifestIdentityConflict",
    "ManifestLockHeld",
    "ManifestNotFound",
    "ManifestVersionConflict",
    "PartitionCurrentPointer",
    "PartitionManifestRepository",
    "PointerFaultPoint",
    "PointerFaultHook",
    "RaisePointerFaultHook",
]