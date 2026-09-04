"""SENSOR-B4-I03 — immutable local T0A blob store (atomic filesystem backend).

``LocalBlobStore`` implements the frozen commit sequence THROUGH step 6
(03 doc §1, I03 §6):

1. write to staging on the SAME filesystem
2. flush userspace buffers
3. fsync staged file
4. verify staged artifact (decoded H1 + source byte count + optional H3)
5. atomically publish staging -> final (NO-CLOBBER)
6. fsync final parent directory

Steps 7-8 (durable metadata transaction, resume advancement) belong to later
checkpoints (I04 / I07) and are NOT implemented here.  There is also NO
recovery scanning (I08), NO T0B projection persistence (I05), NO acquisition
or manifest repository (I04), and ZERO network calls.

Identity layers (I02 §4-§5, I03 §20):

- H1 = ``blob_sha256`` = SHA-256 of the EXACT provider-source bytes, computed
  BEFORE wrapper compression.  Invariant across ``NONE`` and ``ZSTD``.
- H2 = stored-object SHA-256 (wrapper included); equals H1 only for ``NONE``.
- H3 = optional provider checksum, explicit algorithm, verified against the
  exact decoded source bytes; never inferred, never promoted to identity.

Public API is narrow: ``put`` / ``put_bytes`` / ``blob_exists`` /
``open_blob`` / ``verify_blob`` plus result/error types.  There is NO public
overwrite operation — committed T0A blobs are immutable (I03 §26).  Fault
hooks and operation recorders are internal test seams provided by
``atomic.py``; they are NOT part of the public export surface.

``storage_uri`` on ``EvidenceBlob`` is the backend-neutral object key
(``blobs/sha256/...``), never an absolute workstation path (I03 §30).
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import secrets
import zlib
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import BinaryIO

from ..contracts.base import coerce_utc
from .atomic import (
    OP_FILE_FLUSH,
    OP_FILE_FSYNC,
    OP_STAGE_VERIFY,
    OP_STAGE_WRITE,
    OP_STAGING_CLEANUP,
    OP_SUCCESS_RETURN,
    AtomicPublishError,
    AtomicPublishTargetExists,
    FaultError,
    FaultHook,
    FaultPoint,
    OpRecorder,
    default_device_probe,
    default_name_max,
    publish_no_replace,
    validate_component_length,
)
from .checksums import (
    DEFAULT_CHUNK_SIZE,
    ChecksumAlgorithm,
    checksum_algorithm_from_name,
    sha256_stream,
    validate_sha256_hex,
)
from .compression import EncodeResult, encode_source_stream, iter_decode_stored
from .enums import IntegrityState, StorageEncoding, StorageObjectType
from .models import EvidenceBlob, IntegrityCheck
from .paths import blob_object_key, escape_path_segment, resolve_under_root

# ---------------------------------------------------------------------------
# Typed errors
# ---------------------------------------------------------------------------


class InvalidStorageRoot(ValueError):
    """The configured data root is unusable (e.g. exists as a file)."""


class UnsafeObjectKey(ValueError):
    """A backend-controlled object key / identifier failed path containment."""


class StagingWriteError(RuntimeError):
    """Writing the staged artifact failed (I/O only; not an integrity claim)."""


class StagedVerificationError(RuntimeError):
    """The staged artifact failed H1/H2/length verification before commit."""


class ProviderChecksumMismatch(StagedVerificationError):
    """The optional provider checksum (H3) does not match exact source bytes."""


class BlobIntegrityError(RuntimeError):
    """A committed blob's decoded bytes no longer match its content identity."""


class ExistingBlobIntegrityConflict(BlobIntegrityError):
    """The final object at the content-addressed key exists but is not valid.

    It is NEVER overwritten, deleted or repaired here; recovery/quarantine is
    a later checkpoint (I08).  The new staged evidence is preserved.
    """


class BlobMissing(FileNotFoundError):
    """The committed blob does not exist — distinct from an empty blob."""


# ---------------------------------------------------------------------------
# Result contract
# ---------------------------------------------------------------------------


class PutDisposition(str, Enum):
    COMMITTED_NEW = "COMMITTED_NEW"
    REUSED_EXISTING = "REUSED_EXISTING"


@dataclass(frozen=True)
class BlobPutResult:
    """Narrow put() result (I03 §29).  Disposition != integrity state."""

    blob: EvidenceBlob
    disposition: PutDisposition
    source_sha256: str
    stored_sha256: str | None
    source_byte_length: int
    stored_byte_length: int
    object_key: str


# ---------------------------------------------------------------------------
# Streaming provider-checksum accumulator (H3), explicit algorithm only
# ---------------------------------------------------------------------------

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_MD5_HEX_RE = re.compile(r"^[0-9a-f]{32}$")
_CRC32_HEX_RE = re.compile(r"^[0-9a-f]{8}$")

_EXPECTED_PATTERN: dict[ChecksumAlgorithm, re.Pattern[str]] = {
    ChecksumAlgorithm.SHA256: _SHA256_HEX_RE,
    ChecksumAlgorithm.MD5: _MD5_HEX_RE,
    ChecksumAlgorithm.CRC32: _CRC32_HEX_RE,
}


class _ChecksumAccumulator:
    """Incremental provider-checksum accumulator (SHA256/MD5/CRC32)."""

    __slots__ = ("_algorithm", "_crc", "_hasher")

    def __init__(self, algorithm: ChecksumAlgorithm) -> None:
        if not isinstance(algorithm, ChecksumAlgorithm):
            raise TypeError(
                f"algorithm must be a ChecksumAlgorithm, got {type(algorithm).__name__}"
            )
        self._algorithm = algorithm
        if algorithm is ChecksumAlgorithm.SHA256:
            self._hasher: hashlib._Hash | None = hashlib.sha256()
        elif algorithm is ChecksumAlgorithm.MD5:
            self._hasher = hashlib.md5()
        else:
            self._hasher = None
        self._crc = 0

    def update(self, data: bytes) -> None:
        if self._hasher is not None:
            self._hasher.update(data)
        else:
            self._crc = zlib.crc32(data, self._crc)

    def hexdigest(self) -> str:
        if self._hasher is not None:
            return self._hasher.hexdigest()
        return format(self._crc, "08x")


def _canonical_expected_checksum(value: str, algorithm: ChecksumAlgorithm) -> str:
    """Validate + lowercase a provider-published checksum before comparison.

    The algorithm is explicit; the expected value never determines the
    algorithm (mirrors ``checksums.verify_checksum`` canonicalization, kept
    here as a streaming-friendly validator so no bytes need materializing).
    """
    if not isinstance(value, str):
        raise TypeError(f"provider checksum must be str, got {type(value).__name__}")
    lower = value.lower()
    pattern = _EXPECTED_PATTERN[algorithm]
    if not pattern.fullmatch(lower):
        raise ValueError(
            f"expected {algorithm.value} checksum must match {pattern.pattern}, "
            f"got {value!r}"
        )
    return lower


def _validate_encoding(encoding: object) -> StorageEncoding:
    if not isinstance(encoding, StorageEncoding):
        raise TypeError(
            f"storage_encoding must be a StorageEncoding, got {type(encoding).__name__}"
        )
    if encoding not in (StorageEncoding.NONE, StorageEncoding.ZSTD):
        raise ValueError(f"unsupported storage encoding {encoding!r}")
    return encoding


# ---------------------------------------------------------------------------
# Local blob store
# ---------------------------------------------------------------------------


class LocalBlobStore:
    """Immutable, content-addressed, no-clobber local T0A blob backend.

    The data root is explicit runtime configuration (never hard-coded, never
    part of evidence identity).  Git never contains production T0 payloads.
    """

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        clock: Callable[[], datetime] | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        device_probe: Callable[[Path], int] = default_device_probe,
        name_max_probe: Callable[[Path], int] = default_name_max,
    ) -> None:
        if not isinstance(root, (str, os.PathLike)):
            raise TypeError(
                f"root must be str or PathLike, got {type(root).__name__}"
            )
        self.root = Path(root)
        if str(self.root) == "":
            raise InvalidStorageRoot("data root must be a nonempty path")
        if self.root.exists() and not self.root.is_dir():
            raise InvalidStorageRoot(
                f"data root {self.root!s} exists and is not a directory"
            )
        self._clock: Callable[[], datetime] = (
            clock if clock is not None else lambda: datetime.now(UTC)
        )
        if (
            not isinstance(chunk_size, int)
            or isinstance(chunk_size, bool)
            or chunk_size <= 0
        ):
            raise ValueError(f"chunk_size must be a positive int, got {chunk_size!r}")
        self._chunk_size = chunk_size
        self._device_probe = device_probe
        self._name_max_probe = name_max_probe

    # -- internal helpers ---------------------------------------------------

    def _now(self) -> datetime:
        # created_at is METADATA, not content identity: injected clock keeps
        # tests deterministic and never contaminates digest/key/dedupe.
        return coerce_utc(self._clock())

    def _resolve(self, object_key: str) -> Path:
        try:
            return resolve_under_root(self.root, object_key)
        except ValueError as exc:
            raise UnsafeObjectKey(f"object key containment failed: {exc}") from None

    def _staging_dir(self, job_id: str | None) -> Path:
        if job_id is None:
            rel = "staging"
        else:
            if not isinstance(job_id, str) or job_id == "":
                raise UnsafeObjectKey("job_id must be a nonempty string")
            # Encoded with the frozen canonical path-component rules so no raw
            # provider value can introduce '/', '\\', '..', NUL or abs paths.
            escaped = escape_path_segment(job_id)
            # LONG-COMPONENT GUARD before ANY artifact path is opened/written
            # (I03 §10): the encoded staging component is checked against the
            # filesystem's component limit — over-limit fails typed
            # ComponentTooLong BEFORE the staging directory or file exists,
            # never as a late raw ENAMETOOLONG.  No truncation/normalization.
            staging_root = self._resolve("staging")
            validate_component_length(escaped, self._name_max_probe(staging_root))
            rel = f"staging/{escaped}"
        return self._resolve(rel)

    def _check_key_components(self, object_key: str, directory: Path) -> None:
        """Fail closed BEFORE any final artifact write (I03 §10)."""
        limit = self._name_max_probe(directory)
        for segment in object_key.split("/"):
            validate_component_length(segment, limit)

    def _decode_stats(
        self,
        path: Path,
        encoding: StorageEncoding,
        h3_accumulator: _ChecksumAccumulator | None = None,
    ) -> tuple[str, int]:
        """Stream-decode a stored object; return (decoded H1, byte length)."""
        hasher = hashlib.sha256()
        length = 0
        with open(path, "rb") as raw:
            for chunk in iter_decode_stored(raw, encoding, chunk_size=self._chunk_size):
                hasher.update(chunk)
                length += len(chunk)
                if h3_accumulator is not None:
                    h3_accumulator.update(chunk)
        return hasher.hexdigest(), length

    def _verify_staged(
        self,
        staging_path: Path,
        enc: EncodeResult,
        encoding: StorageEncoding,
        expected_h3: str | None,
        provider_alg: ChecksumAlgorithm | None,
    ) -> None:
        """Re-open the staged artifact and prove it before publication."""
        with open(staging_path, "rb") as raw:
            stored_stats = sha256_stream(raw, chunk_size=self._chunk_size)
        if stored_stats.hex_digest != enc.stored_sha256:
            raise StagedVerificationError(
                "staged stored bytes H2 mismatch: "
                f"{stored_stats.hex_digest} != {enc.stored_sha256}"
            )
        h3_acc = _ChecksumAccumulator(provider_alg) if provider_alg is not None else None
        digest, length = self._decode_stats(staging_path, encoding, h3_acc)
        if digest != enc.source_sha256:
            raise StagedVerificationError(
                f"decoded staged H1 {digest} != source H1 {enc.source_sha256}"
            )
        if length != enc.source_byte_length:
            raise StagedVerificationError(
                f"decoded staged length {length} != source length "
                f"{enc.source_byte_length}"
            )
        if h3_acc is not None and h3_acc.hexdigest() != expected_h3:
            raise ProviderChecksumMismatch(
                f"provider checksum {expected_h3!r} does not match exact "
                f"source bytes (observed {h3_acc.hexdigest()!r}); final "
                "commit refused"
            )

    def _verify_existing(
        self,
        final_path: Path,
        expected_h1: str,
        expected_len: int,
        encoding: StorageEncoding,
    ) -> tuple[str, int, str, int] | None:
        """Verify an existing final object; None if it does not exist.

        Raises ``ExistingBlobIntegrityConflict`` when the existing object
        cannot decode or does not hash to the expected content identity (
        never overwrites).  Returns (decoded_h1, decoded_len, stored_h2,
        stored_len) on valid existing.
        """
        if not os.path.exists(final_path):
            return None
        if not os.path.isfile(final_path):
            raise ExistingBlobIntegrityConflict(
                f"object key {final_path!s} exists but is not a regular file; "
                "NOT overwritten"
            )
        try:
            with open(final_path, "rb") as raw:
                stored_stats = sha256_stream(raw, chunk_size=self._chunk_size)
            digest, length = self._decode_stats(final_path, encoding)
        except FileNotFoundError:
            return None
        except Exception as exc:  # undecodable wrapper / I/O = integrity failure
            raise ExistingBlobIntegrityConflict(
                f"existing final {final_path!s} unreadable or undecodable: {exc}"
            ) from exc
        if digest != expected_h1 or length != expected_len:
            raise ExistingBlobIntegrityConflict(
                f"existing final {final_path!s} decodes to H1 {digest} / "
                f"len {length}; expected H1 {expected_h1} / len {expected_len}; "
                "NOT overwritten; staging preserved"
            )
        return (digest, length, stored_stats.hex_digest, stored_stats.byte_length)

    @staticmethod
    def _cleanup_staging(staging_path: Path) -> None:
        """Remove the transient staging artifact after verified success.

        Only called on ordinary success or after an existing final verified;
        ambiguous integrity failures keep staging as evidence (I03 §43).
        """
        try:
            os.unlink(staging_path)
        except FileNotFoundError:
            pass
        except OSError:
            pass  # leftover transient staging is not integrity evidence

    def _build_evidence(
        self,
        source_sha256: str,
        source_len: int,
        stored_len: int,
        media_type: str,
        encoding: StorageEncoding,
        object_key: str,
    ) -> EvidenceBlob:
        return EvidenceBlob(
            blob_sha256=source_sha256,
            byte_length=source_len,
            stored_byte_length=stored_len,
            source_media_type=media_type,
            storage_encoding=encoding,
            created_at=self._now(),
            storage_uri=object_key,
            integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
        )

    def _reuse_result(
        self,
        existing: tuple[str, int, str, int],
        enc: EncodeResult,
        media_type: str,
        encoding: StorageEncoding,
        object_key: str,
        ops: OpRecorder | None,
        staging_path: Path,
    ) -> BlobPutResult:
        digest, length, stored_h2, stored_len = existing
        self._cleanup_staging(staging_path)
        if ops is not None:
            ops.record(OP_STAGING_CLEANUP)
            ops.record(OP_SUCCESS_RETURN)
        return BlobPutResult(
            blob=self._build_evidence(
                digest, length, stored_len, media_type, encoding, object_key
            ),
            disposition=PutDisposition.REUSED_EXISTING,
            source_sha256=digest,
            stored_sha256=stored_h2,
            source_byte_length=length,
            stored_byte_length=stored_len,
            object_key=object_key,
        )

    # -- public API ---------------------------------------------------------

    def put(
        self,
        source: BinaryIO,
        *,
        storage_encoding: StorageEncoding,
        source_media_type: str,
        job_id: str | None = None,
        provider_checksum_algorithm: str | None = None,
        provider_checksum_value: str | None = None,
        fault_hooks: FaultHook | None = None,
        ops: OpRecorder | None = None,
    ) -> BlobPutResult:
        """Stream exact source bytes into an immutable, embedded blob.

        ``source`` is read at its CURRENT position, never closed.  A random
        transient nonce names the staging artifact; it never becomes blob,
        acquisition, manifest or lineage identity (I03 §12-§13).

        Optional H3: provider checksum (explicit algorithm) verified against
        the exact decoded source bytes; a mismatch fails before any usable
        final commit and the staged bytes are preserved.
        """
        encoding = _validate_encoding(storage_encoding)
        if not isinstance(source_media_type, str) or source_media_type == "":
            raise ValueError("source_media_type must be a nonempty string")

        provider_alg: ChecksumAlgorithm | None = None
        expected_h3: str | None = None
        if provider_checksum_algorithm is not None:
            provider_alg = checksum_algorithm_from_name(provider_checksum_algorithm)
            if provider_checksum_value is None:
                raise ValueError(
                    "provider_checksum_value is required when "
                    "provider_checksum_algorithm is supplied"
                )
            expected_h3 = _canonical_expected_checksum(
                provider_checksum_value, provider_alg
            )
        elif provider_checksum_value is not None:
            raise ValueError(
                "provider_checksum_algorithm is required when "
                "provider_checksum_value is supplied"
            )

        staging_dir = self._staging_dir(job_id)
        os.makedirs(staging_dir, exist_ok=True)
        staging_path = staging_dir / f"{secrets.token_hex(16)}.partial"
        if ops is not None:
            ops.record(OP_STAGE_WRITE)
        try:
            # O_EXCL + conservative 0o600: evidence is never world-writable.
            fd = os.open(
                staging_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
        except OSError as exc:
            raise StagingWriteError(
                f"cannot create staging artifact {staging_path!s}: {exc}"
            ) from exc
        try:
            with os.fdopen(fd, "wb") as fh:
                # fault A — during staged write: the artifact exists with a
                # partial payload.  The fault is raised INSIDE the with-block
                # so fdopen's with-context closes the descriptor even when
                # the injected crash propagates (no fd leak on this path).
                if fault_hooks is not None:
                    fault_hooks.raise_if(FaultPoint.STAGE_WRITE)
                enc = encode_source_stream(
                    source, fh, encoding, chunk_size=self._chunk_size
                )
                fh.flush()
                if ops is not None:
                    ops.record(OP_FILE_FLUSH)
                if fault_hooks is not None:
                    fault_hooks.raise_if(FaultPoint.BEFORE_FILE_FSYNC)
                os.fsync(fh.fileno())
                if ops is not None:
                    ops.record(OP_FILE_FSYNC)
        except FaultError:
            raise
        except OSError as exc:
            raise StagingWriteError(
                f"staged write/flush/fsync failed: {exc}"
            ) from exc

        # fault C — after fsync before staged verification
        if fault_hooks is not None:
            fault_hooks.raise_if(FaultPoint.BEFORE_STAGE_VERIFY)
        try:
            self._verify_staged(
                staging_path, enc, encoding, expected_h3, provider_alg
            )
        except (ProviderChecksumMismatch, StagedVerificationError):
            raise
        except Exception as exc:
            raise StagedVerificationError(
                f"staged artifact {staging_path!s} failed verification: {exc}"
            ) from exc
        if ops is not None:
            ops.record(OP_STAGE_VERIFY)

        object_key = blob_object_key(enc.source_sha256, encoding)
        final_path = self._resolve(object_key)
        # long-component guard BEFORE any final artifact write (I03 §10/§45)
        self._check_key_components(object_key, final_path.parent)

        # fault D — after verification before final publication
        if fault_hooks is not None:
            fault_hooks.raise_if(FaultPoint.BEFORE_PUBLISH)

        existing = self._verify_existing(
            final_path, enc.source_sha256, enc.source_byte_length, encoding
        )
        if existing is not None:
            return self._reuse_result(
                existing,
                enc,
                source_media_type,
                encoding,
                object_key,
                ops,
                staging_path,
            )

        try:
            publish_no_replace(
                staging_path,
                final_path,
                device_probe=self._device_probe,
                fault_hooks=fault_hooks,
                ops=ops,
            )
        except AtomicPublishTargetExists:
            # Lost a same-hash publish race: the winner is already final.
            winner = self._verify_existing(
                final_path, enc.source_sha256, enc.source_byte_length, encoding
            )
            if winner is None:
                raise AtomicPublishError(
                    "final name appeared and disappeared during a publish race; "
                    "staging preserved"
                ) from None
            return self._reuse_result(
                winner,
                enc,
                source_media_type,
                encoding,
                object_key,
                ops,
                staging_path,
            )
        # FaultError / CrossFilesystemAtomicityError / DurabilityUnsupported /
        # ComponentTooLong / AtomicPublishError propagate: no success claimed,
        # crash state intentionally preserved.
        if ops is not None:
            ops.record(OP_SUCCESS_RETURN)
        return BlobPutResult(
            blob=self._build_evidence(
                enc.source_sha256,
                enc.source_byte_length,
                enc.stored_byte_length,
                source_media_type,
                encoding,
                object_key,
            ),
            disposition=PutDisposition.COMMITTED_NEW,
            source_sha256=enc.source_sha256,
            stored_sha256=enc.stored_sha256,
            source_byte_length=enc.source_byte_length,
            stored_byte_length=enc.stored_byte_length,
            object_key=object_key,
        )

    def put_bytes(
        self,
        data: bytes,
        *,
        storage_encoding: StorageEncoding,
        source_media_type: str,
        job_id: str | None = None,
        provider_checksum_algorithm: str | None = None,
        provider_checksum_value: str | None = None,
        fault_hooks: FaultHook | None = None,
        ops: OpRecorder | None = None,
    ) -> BlobPutResult:
        """One-shot bytes convenience; exact same canonical path as put()."""
        if not isinstance(data, bytes):
            raise TypeError(f"put_bytes requires bytes, got {type(data).__name__}")
        return self.put(
            io.BytesIO(data),
            storage_encoding=storage_encoding,
            source_media_type=source_media_type,
            job_id=job_id,
            provider_checksum_algorithm=provider_checksum_algorithm,
            provider_checksum_value=provider_checksum_value,
            fault_hooks=fault_hooks,
            ops=ops,
        )

    def blob_exists(
        self, blob_sha256: str, storage_encoding: StorageEncoding
    ) -> bool:
        """PRESENCE ONLY (I03 §32) — never implies verified integrity."""
        encoding = _validate_encoding(storage_encoding)
        validate_sha256_hex(blob_sha256)
        object_key = blob_object_key(blob_sha256, encoding)
        return os.path.isfile(self._resolve(object_key))

    @contextmanager
    def open_blob(
        self, blob_sha256: str, storage_encoding: StorageEncoding
    ) -> Iterator[BinaryIO]:
        """Read-only access to DECODED exact source bytes (streaming).

        NONE: raw file reader.  ZSTD: streaming decompressor over the file.
        The final object is never opened for writing through this API.
        """
        encoding = _validate_encoding(storage_encoding)
        validate_sha256_hex(blob_sha256)
        path = self._resolve(blob_object_key(blob_sha256, encoding))
        if not os.path.isfile(path):
            raise BlobMissing(
                f"blob {blob_sha256} ({encoding.value}) does not exist at "
                f"{path!s}"
            )
        with open(path, "rb") as raw:
            if encoding is StorageEncoding.NONE:
                yield raw
            else:
                import zstandard

                decompressor = zstandard.ZstdDecompressor()
                with decompressor.stream_reader(
                    raw, read_size=self._chunk_size, closefd=False
                ) as reader:
                    yield reader

    def verify_blob(
        self,
        blob_sha256: str,
        storage_encoding: StorageEncoding,
        *,
        expected_byte_length: int | None = None,
        expected_h2: str | None = None,
    ) -> IntegrityCheck:
        """Recompute H1 from a committed object and return a typed result.

        Missing object: raises ``BlobMissing`` (absence != corruption).
        Corrupted object: returns ``IntegrityCheck`` with
        ``QUARANTINED_INTEGRITY_FAILURE`` (detection only, no repair).
        """
        encoding = _validate_encoding(storage_encoding)
        validate_sha256_hex(blob_sha256)
        object_key = blob_object_key(blob_sha256, encoding)
        path = self._resolve(object_key)
        if not os.path.exists(path):
            raise BlobMissing(
                f"blob {blob_sha256} ({encoding.value}) missing at {path!s}"
            )
        if not os.path.isfile(path):
            raise BlobIntegrityError(
                f"object key {path!s} exists but is not a regular file"
            )
        check_id = f"verify:{object_key}"
        try:
            with open(path, "rb") as raw:
                stored_stats = sha256_stream(raw, chunk_size=self._chunk_size)
            digest, length = self._decode_stats(path, encoding)
        except Exception as exc:  # noqa: BLE001 - any decode failure of a
            # committed stored object IS an integrity failure; broad catch is
            # intentional and bounded to this read/verify block.
            return IntegrityCheck(
                check_id=check_id,
                object_type=StorageObjectType.EVIDENCE_BLOB,
                object_id=object_key,
                integrity_state=IntegrityState.QUARANTINED_INTEGRITY_FAILURE,
                checked_at=self._now(),
                expected_hash=blob_sha256,
                observed_hash=None,
                detail=f"stored object undecodable: {exc}",
            )
        ok = True
        detail: str | None = None
        if digest != blob_sha256:
            ok = False
            detail = (
                f"decoded source SHA {digest} != expected content identity "
                f"{blob_sha256}"
            )
        elif expected_byte_length is not None and length != expected_byte_length:
            ok = False
            detail = (
                f"decoded byte length {length} != expected "
                f"{expected_byte_length}"
            )
        elif expected_h2 is not None and stored_stats.hex_digest != expected_h2:
            ok = False
            detail = (
                f"stored-object hash {stored_stats.hex_digest} != expected "
                f"H2 {expected_h2}"
            )
        return IntegrityCheck(
            check_id=check_id,
            object_type=StorageObjectType.EVIDENCE_BLOB,
            object_id=object_key,
            integrity_state=(
                IntegrityState.LOCAL_HASH_VERIFIED
                if ok
                else IntegrityState.QUARANTINED_INTEGRITY_FAILURE
            ),
            checked_at=self._now(),
            expected_hash=blob_sha256,
            observed_hash=digest,
            detail=detail,
        )


__all__ = [
    "BlobIntegrityError",
    "BlobMissing",
    "BlobPutResult",
    "ExistingBlobIntegrityConflict",
    "InvalidStorageRoot",
    "LocalBlobStore",
    "ProviderChecksumMismatch",
    "PutDisposition",
    "StagedVerificationError",
    "StagingWriteError",
    "UnsafeObjectKey",
]