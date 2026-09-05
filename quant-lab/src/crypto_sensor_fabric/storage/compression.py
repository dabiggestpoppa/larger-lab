"""SENSOR-B4-I03 — streaming NONE/ZSTD source-byte wrapper.

This module owns ONLY the narrow streaming wrapper behavior:

- ``encode_source_stream(source, sink, encoding, chunk_size)`` reads EXACT
  source bytes from ``source`` at its current position (bounded reads,
  non-seekable friendly), writes STORED bytes to ``sink``, and returns an
  ``EncodeResult`` carrying H1 (source SHA-256) and H2 (stored-object
  SHA-256) plus both byte counts.  Neither stream is closed by this module.
- ``iter_decode_stored(stored, encoding, chunk_size)`` yields DECODED exact
  source bytes from a stored object (NONE: byte-for-byte passthrough; ZSTD:
  streaming decompression).  Exact source bytes are preserved on decode.

Hash doctrine (I02 §4-§5, I03 §15/§18/§20):

- ``blob_sha256`` (H1) is ALWAYS SHA-256 of the EXACT provider-source bytes
  BEFORE wrapper compression.  ZSTD changes the STORED bytes, never H1 and
  never the source ``byte_length``.
- H2 validates the storage object (wrapper included) and is never compared
  against H1 when a wrapper changes stored bytes.  For NONE, H1 == H2
  because stored bytes == source bytes.

H3 (provider checksum) is deliberately NOT computed here — it is a
provider-integrity layer handled by the blob store against decoded source
bytes.

No provider logic, no filesystem mutation, no network, no full-object
materialization, no JSON/text decoding anywhere.
"""

from __future__ import annotations

import hashlib
import io
from collections.abc import Iterator
from dataclasses import dataclass
from typing import BinaryIO, cast

from .checksums import DEFAULT_CHUNK_SIZE, validate_sha256_hex
from .enums import StorageEncoding


@dataclass(frozen=True)
class EncodeResult:
    """Immutable result of one bounded streaming encode pass.

    ``source_sha256`` is H1 (exact source bytes, BEFORE wrapper compression);
    ``stored_sha256`` is H2 (the stored object bytes, wrapper included).
    ``stored_byte_length`` is the size of the stored object as written.
    """

    source_sha256: str
    source_byte_length: int
    stored_sha256: str
    stored_byte_length: int

    def __post_init__(self) -> None:
        validate_sha256_hex(self.source_sha256)
        validate_sha256_hex(self.stored_sha256)
        if (
            not isinstance(self.source_byte_length, int)
            or isinstance(self.source_byte_length, bool)
            or self.source_byte_length < 0
        ):
            raise ValueError(
                f"source_byte_length must be >= 0, got {self.source_byte_length!r}"
            )
        if (
            not isinstance(self.stored_byte_length, int)
            or isinstance(self.stored_byte_length, bool)
            or self.stored_byte_length < 0
        ):
            raise ValueError(
                f"stored_byte_length must be >= 0, got {self.stored_byte_length!r}"
            )


class _HashCountingWriter(io.RawIOBase):
    """Write-through sink adapter that feeds a hasher and counts bytes.

    Used ONLY to derive H2 from the exact stored bytes a ZSTD compressor
    writes, without materializing them.
    """

    def __init__(self, sink: BinaryIO, hasher: hashlib._Hash) -> None:
        super().__init__()
        self._sink = sink
        self._hasher = hasher
        self.count = 0

    def write(self, data: bytes) -> int:  # type: ignore[override]
        self._hasher.update(data)
        written = self._sink.write(data)
        self.count += written
        return written

    def flush(self) -> None:
        self._sink.flush()

    def close(self) -> None:
        # Never close the caller-owned sink; just satisfy the compressor.
        self.flush()


def _validate_encoding(encoding: object) -> StorageEncoding:
    if not isinstance(encoding, StorageEncoding):
        raise TypeError(
            f"storage_encoding must be a StorageEncoding, got {type(encoding).__name__}"
        )
    if encoding not in (StorageEncoding.NONE, StorageEncoding.ZSTD):
        raise ValueError(f"unsupported storage encoding {encoding!r}")
    return encoding


def _validate_chunk_size(chunk_size: object) -> int:
    if (
        not isinstance(chunk_size, int)
        or isinstance(chunk_size, bool)
        or chunk_size <= 0
    ):
        raise ValueError(f"chunk_size must be a positive int, got {chunk_size!r}")
    return chunk_size


def encode_source_stream(
    source: BinaryIO,
    sink: BinaryIO,
    storage_encoding: StorageEncoding,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> EncodeResult:
    """Stream exact source bytes into stored bytes under ONE wrapper encoding.

    - starts at the caller stream's CURRENT position (no rewinding);
    - bounded ``read(chunk_size)`` — never an unbounded ``read()``;
    - accepts non-seekable sources and sinks;
    - does NOT close either stream (caller owns both);
    - computes H1 over the exact source bytes before/while wrapping;
    - computes H2 over the stored bytes it writes.
    """
    _validate_encoding(storage_encoding)
    _validate_chunk_size(chunk_size)

    if storage_encoding is StorageEncoding.NONE:
        source_hasher = hashlib.sha256()
        stored_hasher = hashlib.sha256()
        source_total = 0
        while True:
            chunk = source.read(chunk_size)
            if not isinstance(chunk, bytes):
                raise TypeError(
                    f"source.read({chunk_size}) must return bytes, got {type(chunk).__name__}"
                )
            if not chunk:
                break
            source_hasher.update(chunk)
            stored_hasher.update(chunk)
            sink.write(chunk)
            source_total += len(chunk)
        digest = source_hasher.hexdigest()
        return EncodeResult(
            source_sha256=digest,
            source_byte_length=source_total,
            stored_sha256=stored_hasher.hexdigest(),
            stored_byte_length=source_total,
        )

    # ZSTD: the exact source bytes are hashed as H1 BEFORE wrapper
    # compression; the stored (compressed) bytes are hashed as H2.
    import zstandard

    source_hasher = hashlib.sha256()
    stored_hasher = hashlib.sha256()
    source_total = 0
    writer = _HashCountingWriter(sink, stored_hasher)
    # stream_writer requires a BinaryIO; the adapter satisfies the write/flush
    # protocol and never closes the caller-owned sink.
    zwriter_target = cast(BinaryIO, writer)
    compressor = zstandard.ZstdCompressor()
    with compressor.stream_writer(zwriter_target) as zwriter:
        while True:
            chunk = source.read(chunk_size)
            if not isinstance(chunk, bytes):
                raise TypeError(
                    f"source.read({chunk_size}) must return bytes, got {type(chunk).__name__}"
                )
            if not chunk:
                break
            source_hasher.update(chunk)
            zwriter.write(chunk)
            source_total += len(chunk)
    return EncodeResult(
        source_sha256=source_hasher.hexdigest(),
        source_byte_length=source_total,
        stored_sha256=stored_hasher.hexdigest(),
        stored_byte_length=writer.count,
    )


def iter_decode_stored(
    stored: BinaryIO,
    storage_encoding: StorageEncoding,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Iterator[bytes]:
    """Yield EXACT source bytes decoded from a stored object (streaming).

    - NONE: raw byte-for-byte passthrough of the stored object;
    - ZSTD: streaming decompression frame-by-frame;
    - bounded reads; the caller-owned ``stored`` stream is NOT closed;
    - does not validate content identity — verification (H1/H2) is the blob
      store's responsibility.
    """
    _validate_encoding(storage_encoding)
    _validate_chunk_size(chunk_size)

    if storage_encoding is StorageEncoding.NONE:
        while True:
            chunk = stored.read(chunk_size)
            if not isinstance(chunk, bytes):
                raise TypeError(
                    f"stored.read({chunk_size}) must return bytes, got {type(chunk).__name__}"
                )
            if not chunk:
                break
            yield chunk
        return

    import zstandard

    decompressor = zstandard.ZstdDecompressor()
    with decompressor.stream_reader(stored, read_size=chunk_size, closefd=False) as reader:
        while True:
            chunk = reader.read(chunk_size)
            if not isinstance(chunk, bytes):
                raise TypeError(
                    f"zstd reader.read({chunk_size}) must return bytes, got {type(chunk).__name__}"
                )
            if not chunk:
                break
            yield chunk


__all__ = [
    "EncodeResult",
    "encode_source_stream",
    "iter_decode_stored",
]