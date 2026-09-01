"""SENSOR-B4-I02 — SHA-256 identity primitives and provider checksum comparison.

Non-negotiable hash doctrine (I02 §4–§5):

- ``blob_sha256`` is SHA-256 of the EXACT provider-source bytes, computed
  BEFORE any local wrapper compression, pretty printing, JSON reserialization,
  newline normalization, character decoding or projection parsing.
- Three distinct checksum layers are preserved:
  - H1 SOURCE SHA256 — mandatory; defines ``EvidenceBlob`` identity.
  - H2 STORED OBJECT CHECKSUM — optional; validates storage-object bytes
    (wrapper included) later, never compared directly to H1 when a wrapper
    changes stored bytes.
  - H3 PROVIDER CHECKSUM — optional; MD5/SHA256/CRC32 published by the
    provider, explicit-algorithm, integrity evidence only.
- ``sha256_bytes``/``sha256_stream``/``sha256_chunks``/``sha256_file`` consume
  and hash BYTES only — never implicit Python-string decoding.  Empty source
  payloads are valid evidence (an empty provider body may still be evidence).
- This module performs NO filesystem mutation, NO compression, NO network and
  NO content-address derivation (that is ``paths.py``).

Dependency direction: stdlib + storage enums only.  Provider adapters never
import storage.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import zlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import BinaryIO

from .enums import ChecksumAlgorithm

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_MD5_HEX_RE = re.compile(r"^[0-9a-f]{32}$")
_CRC32_HEX_RE = re.compile(r"^[0-9a-f]{8}$")

# Infrastructure default read size — NOT scientific truth; tests prove custom
# small chunk sizes and the stream contract keeps reads bounded by it.
DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MiB

# Canonical hex form per algorithm (lowercase; used to validate provider
# checksum expected values so the algorithm is never guessed from length).
_ALGORITHM_HEX_RE: dict[ChecksumAlgorithm, re.Pattern[str]] = {
    ChecksumAlgorithm.SHA256: _SHA256_HEX_RE,
    ChecksumAlgorithm.MD5: _MD5_HEX_RE,
    ChecksumAlgorithm.CRC32: _CRC32_HEX_RE,
}


def validate_sha256_hex(value: str) -> str:
    """Validate SHA-256 FORMAT only: 64 lowercase hex chars.  No hashing.

    This is THE single SHA-256 syntax rule for the whole storage package
    (I02 §19): ``paths.py`` and ``models.py`` reuse it — one validation rule,
    not two.  Returns the validated value for validator convenience.
    """
    if not isinstance(value, str) or not _SHA256_HEX_RE.fullmatch(value):
        raise ValueError(
            f"must be 64 lowercase hex characters, got {value!r}"
        )
    return value


@dataclass(frozen=True)
class Sha256Result:
    """Immutable SHA-256 identity of EXACT source bytes (H1 layer).

    Contains only the digest and the exact byte count of the hashed source —
    no timestamp, no path, no provider, no sensor.  Content identity is
    independent of acquisition semantics.
    """

    hex_digest: str
    byte_length: int

    def __post_init__(self) -> None:
        validate_sha256_hex(self.hex_digest)
        if not isinstance(self.byte_length, int) or self.byte_length < 0:
            raise ValueError(f"byte_length must be >= 0, got {self.byte_length!r}")


def sha256_bytes(data: bytes) -> Sha256Result:
    """Hash exact bytes (one-shot).  Rejects non-bytes (no implicit decoding)."""
    if not isinstance(data, bytes):
        raise TypeError(
            f"sha256_bytes requires bytes, got {type(data).__name__}"
        )
    return Sha256Result(
        hex_digest=hashlib.sha256(data).hexdigest(),
        byte_length=len(data),
    )


def sha256_stream(
    stream: BinaryIO,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Sha256Result:
    """Incremental SHA-256 over a binary stream (bounded memory).

    Contract (I02 §9–§10):
    - reads incrementally with ``read(size)`` — NEVER ``read()`` without size;
    - identical digest to ``hashlib.sha256(full_bytes)``;
    - works with non-seekable readers; starts at the current stream position
      and never rewinds;
    - does NOT close the caller-owned stream;
    - does not decode bytes; ``chunk_size`` must be a positive int.
    """
    if (
        not isinstance(chunk_size, int)
        or isinstance(chunk_size, bool)
        or chunk_size <= 0
    ):
        raise ValueError(f"chunk_size must be a positive int, got {chunk_size!r}")
    hasher = hashlib.sha256()
    total = 0
    while True:
        chunk = stream.read(chunk_size)
        if not isinstance(chunk, bytes):
            raise TypeError(
                f"stream.read({chunk_size}) must return bytes, got {type(chunk).__name__}"
            )
        if not chunk:
            break
        hasher.update(chunk)
        total += len(chunk)
    return Sha256Result(hex_digest=hasher.hexdigest(), byte_length=total)


def sha256_chunks(chunks: Iterable[bytes]) -> Sha256Result:
    """Hash an iterable of bytes chunks (concatenation identity).

    ``hash([b"ab", b"cd"]) == hash(b"abcd")``; zero-length chunks are allowed
    and never filtered (filtering would change byte identity); non-bytes chunks
    are rejected.
    """
    hasher = hashlib.sha256()
    total = 0
    for chunk in chunks:
        if not isinstance(chunk, bytes):
            raise TypeError(
                f"sha256_chunks yields non-bytes chunk of type {type(chunk).__name__}"
            )
        hasher.update(chunk)
        total += len(chunk)
    return Sha256Result(hex_digest=hasher.hexdigest(), byte_length=total)


def sha256_file(path: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Sha256Result:
    """Read-only streaming SHA-256 of a file (binary mode, no mmap, no writes).

    Generic read-only helper: actual backend path-security enforcement belongs
    to the local storage backend / hardening checkpoints.
    """
    with open(path, "rb") as fh:
        return sha256_stream(fh, chunk_size=chunk_size)


# ---------------------------------------------------------------------------
# Provider checksums (H3 layer) — explicit algorithm only
# ---------------------------------------------------------------------------


def checksum_algorithm_from_name(name: str) -> ChecksumAlgorithm:
    """Parse an explicit provider checksum algorithm name.

    Unknown algorithms fail closed — the algorithm is NEVER guessed from digest
    length, header-name substrings or provider identity.
    """
    if not isinstance(name, str):
        raise TypeError(f"checksum algorithm name must be str, got {type(name).__name__}")
    try:
        return ChecksumAlgorithm(name.upper())
    except ValueError:
        raise ValueError(
            f"unsupported provider checksum algorithm {name!r}; "
            "explicit selection required (SHA256|MD5|CRC32)"
        ) from None


def compute_checksum(data: bytes, algorithm: ChecksumAlgorithm) -> str:
    """Compute the canonical hex checksum of bytes for ONE explicit algorithm.

    SHA-256 → 64 lowercase hex; MD5 → 32 lowercase hex; CRC32 → 8 lowercase
    hex with leading zeros retained (no decimal/hex ambiguity).
    """
    if not isinstance(data, bytes):
        raise TypeError(f"compute_checksum requires bytes, got {type(data).__name__}")
    if not isinstance(algorithm, ChecksumAlgorithm):
        raise TypeError(
            f"algorithm must be a ChecksumAlgorithm, got {type(algorithm).__name__}"
        )
    if algorithm is ChecksumAlgorithm.SHA256:
        return hashlib.sha256(data).hexdigest()
    if algorithm is ChecksumAlgorithm.MD5:
        return hashlib.md5(data).hexdigest()
    if algorithm is ChecksumAlgorithm.CRC32:
        return format(zlib.crc32(data), "08x")
    raise ValueError(f"unsupported checksum algorithm {algorithm!r}")  # unreachable


def verify_checksum(
    data: bytes,
    algorithm: ChecksumAlgorithm,
    expected_hex: str,
) -> bool:
    """Compare a provider-published checksum against local bytes.

    - the algorithm is explicit and determines the canonical representation;
      the expected value NEVER determines the algorithm by length;
    - expected value must match the algorithm's canonical hex form (case is
      normalized per algorithm for comparison only);
    - equality is constant-time (``hmac.compare_digest``);
    - proves checksum AGREEMENT only — not cryptographic authenticity;
    - never promotes a provider checksum to T0 content identity (callers must
      use ``sha256_bytes``/``sha256_stream`` for ``blob_sha256``).
    """
    if not isinstance(data, bytes):
        raise TypeError(f"verify_checksum requires bytes, got {type(data).__name__}")
    if not isinstance(algorithm, ChecksumAlgorithm):
        raise TypeError(
            f"algorithm must be a ChecksumAlgorithm, got {type(algorithm).__name__}"
        )
    if not isinstance(expected_hex, str):
        raise TypeError(f"expected_hex must be str, got {type(expected_hex).__name__}")
    pattern = _ALGORITHM_HEX_RE[algorithm]
    normalized = expected_hex.lower()
    if not pattern.fullmatch(normalized):
        raise ValueError(
            f"expected {algorithm.value} checksum must match {pattern.pattern}, "
            f"got {expected_hex!r}"
        )
    actual = compute_checksum(data, algorithm)
    return hmac.compare_digest(actual, normalized)


__all__ = [
    "DEFAULT_CHUNK_SIZE",
    "Sha256Result",
    "checksum_algorithm_from_name",
    "compute_checksum",
    "sha256_bytes",
    "sha256_chunks",
    "sha256_file",
    "sha256_stream",
    "validate_sha256_hex",
    "verify_checksum",
]
