"""SENSOR-B4-I02 — SHA-256 primitives and provider-checksum tests.

Proves the I02 hash doctrine: hash BYTES not meaning; exact-byte identity;
streaming == one-shot; bounded reads; nonseekable + ownership contracts;
explicit-algorithm provider checksums (never inferred from length); H1/H2/H3
separation; MD5/CRC32 never promoted to T0 content identity.
"""

from __future__ import annotations

import hashlib
import io
import zlib

import pytest

from crypto_sensor_fabric.storage.checksums import (
    DEFAULT_CHUNK_SIZE,
    Sha256Result,
    checksum_algorithm_from_name,
    compute_checksum,
    sha256_bytes,
    sha256_chunks,
    sha256_file,
    sha256_stream,
    verify_checksum,
)
from crypto_sensor_fabric.storage.enums import ChecksumAlgorithm


class TestSha256KnownVectors:
    def test_empty_bytes(self) -> None:
        result = sha256_bytes(b"")
        assert result.hex_digest == hashlib.sha256(b"").hexdigest()
        assert result.byte_length == 0

    def test_abc(self) -> None:
        assert sha256_bytes(b"abc").hex_digest == hashlib.sha256(b"abc").hexdigest()
        assert sha256_bytes(b"abc").byte_length == 3

    def test_binary_bytes(self) -> None:
        data = b"\x00\xff\x10\x00\xfe\x00\x00\xff"
        assert sha256_bytes(data).hex_digest == hashlib.sha256(data).hexdigest()

    def test_utf8_explicit_bytes(self) -> None:
        data = "héllo-世界".encode()
        assert sha256_bytes(data).hex_digest == hashlib.sha256(data).hexdigest()

    def test_rejects_str(self) -> None:
        with pytest.raises(TypeError):
            sha256_bytes("abc")  # type: ignore[arg-type]


class TestTransformationSensitivity:
    def test_exact_bytes_not_semantic_json(self) -> None:
        # Whitespace and trailing-newline variants are DIFFERENT source bytes
        # and therefore different source SHA values — identity is byte-exact.
        variants = (b'{"a":1}', b'{"a": 1}', b'{"a":1}\n')
        assert len({sha256_bytes(v).hex_digest for v in variants}) == len(variants)


class TestSha256Stream:
    def test_equals_one_shot(self) -> None:
        data = bytes(range(256)) * 32  # deterministic 8192 bytes
        result = sha256_stream(io.BytesIO(data))
        assert result.hex_digest == hashlib.sha256(data).hexdigest()
        assert result.byte_length == len(data)

    def test_chunk_size_invariance(self) -> None:
        data = b"0123456789abcdef" * 4096  # 64 KiB
        reference = hashlib.sha256(data).hexdigest()
        for chunk_size in (1, 7, 4096, DEFAULT_CHUNK_SIZE):
            result = sha256_stream(io.BytesIO(data), chunk_size=chunk_size)
            assert result.hex_digest == reference
            assert result.byte_length == len(data)

    def test_empty_stream(self) -> None:
        result = sha256_stream(io.BytesIO(b""))
        assert result.hex_digest == hashlib.sha256(b"").hexdigest()
        assert result.byte_length == 0

    def test_bounded_reads(self) -> None:
        class TrackingReader:
            def __init__(self, data: bytes) -> None:
                self._buffer = io.BytesIO(data)
                self.max_read_size = 0
                self.reads_without_size = 0

            def read(self, size: int = -1) -> bytes:
                if size is None or size < 0:
                    self.reads_without_size += 1
                    raise AssertionError("read() called without a positive size")
                self.max_read_size = max(self.max_read_size, size)
                return self._buffer.read(size)

        data = b"z" * 1_000_000
        reader = TrackingReader(data)
        result = sha256_stream(reader, chunk_size=4096)  # type: ignore[arg-type]
        assert result.byte_length == len(data)
        assert result.hex_digest == hashlib.sha256(data).hexdigest()
        assert reader.max_read_size <= 4096
        assert reader.reads_without_size == 0

    def test_nonseekable_stream(self) -> None:
        class ReadOnlyStream:
            """Supports read(size) only — deliberately no seek/tell/close."""

            def __init__(self, data: bytes) -> None:
                self._buffer = io.BytesIO(data)

            def read(self, size: int = -1) -> bytes:
                if size is None or size < 0:
                    raise AssertionError("read() called without a positive size")
                return self._buffer.read(size)

        data = b"x" * 100_000
        result = sha256_stream(ReadOnlyStream(data), chunk_size=7)  # type: ignore[arg-type]
        assert result.hex_digest == hashlib.sha256(data).hexdigest()
        assert result.byte_length == len(data)

    def test_caller_stream_not_closed(self) -> None:
        stream = io.BytesIO(b"payload")
        sha256_stream(stream)
        assert not stream.closed

    def test_starts_at_current_position_no_rewind(self) -> None:
        stream = io.BytesIO(b"payload")
        stream.seek(3)
        result = sha256_stream(stream)
        assert result.hex_digest == hashlib.sha256(b"load").hexdigest()
        assert stream.tell() == 7  # consumed from current position only, never rewound

    def test_invalid_chunk_size(self) -> None:
        for bad in (0, -1, True, 1.5, "1"):
            with pytest.raises((ValueError, TypeError)):
                sha256_stream(io.BytesIO(b"x"), chunk_size=bad)  # type: ignore[arg-type]


class TestSha256Chunks:
    def test_concatenation_identity(self) -> None:
        assert sha256_chunks([b"ab", b"cd"]).hex_digest == sha256_bytes(b"abcd").hex_digest

    def test_zero_length_chunks_allowed(self) -> None:
        data = b"payload"
        assert (
            sha256_chunks([b"", b"payload", b""]).hex_digest
            == hashlib.sha256(data).hexdigest()
        )

    def test_empty_iterable(self) -> None:
        assert sha256_chunks([]).hex_digest == hashlib.sha256(b"").hexdigest()
        assert sha256_chunks([]).byte_length == 0

    def test_rejects_non_bytes_chunk(self) -> None:
        with pytest.raises(TypeError):
            sha256_chunks([b"ok", "no"])  # type: ignore[list-item]


class TestSha256File:
    def test_digest_matches_contents_and_read_only(self, tmp_path) -> None:
        path = tmp_path / "sample.bin"
        data = bytes(range(256)) * 100
        path.write_bytes(data)
        result = sha256_file(str(path))
        assert result.hex_digest == hashlib.sha256(data).hexdigest()
        assert result.byte_length == len(data)
        assert path.read_bytes() == data  # unchanged (read-only helper)


class TestSha256Result:
    def test_rejects_bad_digest(self) -> None:
        with pytest.raises(ValueError):
            Sha256Result(hex_digest="abc", byte_length=0)

    def test_rejects_negative_length(self) -> None:
        with pytest.raises(ValueError):
            Sha256Result(hex_digest=hashlib.sha256(b"").hexdigest(), byte_length=-1)


class TestProviderChecksums:
    def test_sha256_known(self) -> None:
        assert compute_checksum(b"abc", ChecksumAlgorithm.SHA256) == hashlib.sha256(b"abc").hexdigest()

    def test_md5_known(self) -> None:
        assert compute_checksum(b"abc", ChecksumAlgorithm.MD5) == hashlib.md5(b"abc").hexdigest()

    def test_crc32_canonical_8_lowercase_hex(self) -> None:
        assert compute_checksum(b"abc", ChecksumAlgorithm.CRC32) == format(zlib.crc32(b"abc"), "08x")
        assert compute_checksum(b"", ChecksumAlgorithm.CRC32) == "00000000"  # leading zeros retained

    def test_algorithm_from_name(self) -> None:
        assert checksum_algorithm_from_name("sha256") is ChecksumAlgorithm.SHA256
        assert checksum_algorithm_from_name("MD5") is ChecksumAlgorithm.MD5
        assert checksum_algorithm_from_name("crc32") is ChecksumAlgorithm.CRC32

    def test_unknown_algorithm_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            checksum_algorithm_from_name("blake3")

    def test_verify_correct_and_wrong(self) -> None:
        data = b"payload"
        expected = compute_checksum(data, ChecksumAlgorithm.SHA256)
        assert verify_checksum(data, ChecksumAlgorithm.SHA256, expected) is True
        assert verify_checksum(data, ChecksumAlgorithm.SHA256, "0" * 64) is False

    def test_uppercase_expected_normalized_per_algorithm(self) -> None:
        data = b"payload"
        expected = compute_checksum(data, ChecksumAlgorithm.SHA256).upper()
        assert verify_checksum(data, ChecksumAlgorithm.SHA256, expected) is True

    def test_algorithm_never_inferred_from_length(self) -> None:
        # A 64-char value supplied as a CRC32 expected checksum is REJECTED —
        # never auto-detected as SHA-256 by length.
        with pytest.raises(ValueError):
            verify_checksum(b"payload", ChecksumAlgorithm.CRC32, "ab" * 32)

    def test_malformed_expected_rejected(self) -> None:
        with pytest.raises(ValueError):
            verify_checksum(b"payload", ChecksumAlgorithm.SHA256, "nothex")
        with pytest.raises(ValueError):
            verify_checksum(b"", ChecksumAlgorithm.CRC32, "0")  # per-algorithm length, no padding guess

    def test_crc32_wellformed_mismatch_is_false(self) -> None:
        assert verify_checksum(b"", ChecksumAlgorithm.CRC32, "00000001") is False

    def test_md5_provider_checksum_never_promoted_to_content_identity(self) -> None:
        # H3 provider MD5 is 32 hex chars and can never become a Sha256Result
        # (blob_sha256 identity) — MD5 is integrity evidence only.
        md5_hex = compute_checksum(b"abc", ChecksumAlgorithm.MD5)
        assert len(md5_hex) == 32
        assert md5_hex != hashlib.sha256(b"abc").hexdigest()
        with pytest.raises(ValueError):
            Sha256Result(hex_digest=md5_hex, byte_length=3)


class TestH1H2H3Layers:
    def test_layers_stay_separate(self) -> None:
        source = b'{"a":1}'
        h1 = sha256_bytes(source)  # H1 = exact source bytes
        # H3 provider checksum (MD5) is not H1 and cannot equal it.
        assert compute_checksum(source, ChecksumAlgorithm.MD5) != h1.hex_digest
        # A hypothetical local wrapper (extra newline) changes stored bytes (H2)
        # but the H1 source identity is unaffected.
        assert sha256_bytes(b'{"a":1}\n').hex_digest != h1.hex_digest
        assert sha256_bytes(source).hex_digest == h1.hex_digest
        # Provider checksum agreement is a separate verification primitive.
        assert verify_checksum(source, ChecksumAlgorithm.SHA256, h1.hex_digest) is True


class TestLargeStreamBoundedReads:
    """Proves bounded incremental hashing of a 1 GiB-equivalent logical input
    WITHOUT materializing 1 GiB in memory (I02 §11).

    The deterministic reader exposes a large logical length, tracks the maximum
    requested read size, fails if ``read()`` is ever called without a size, and
    produces deterministic repeated bytes one bounded chunk at a time.
    """

    _PATTERN = b"0123456789abcdef"  # 16-byte deterministic pattern
    _LOGICAL_BYTES = 2**30  # 1 GiB-equivalent logical input

    class _GiantReader:
        def __init__(self, pattern: bytes, total: int) -> None:
            self._pattern = pattern
            self._remaining = total
            self.max_read_size = 0
            self.reads_without_size = 0

        def read(self, size: int = -1) -> bytes:
            if size is None or size < 0:
                self.reads_without_size += 1
                raise AssertionError("read() called without a positive size")
            self.max_read_size = max(self.max_read_size, size)
            if self._remaining == 0:
                return b""
            take = min(size, self._remaining)
            self._remaining -= take
            full, rem = divmod(take, len(self._pattern))
            return self._pattern * full + self._pattern[:rem]

    def _giant(self) -> _GiantReader:
        return self._GiantReader(self._PATTERN, self._LOGICAL_BYTES)

    def test_bounded_reads_and_exact_byte_count(self) -> None:
        reader = self._giant()
        result = sha256_stream(reader, chunk_size=DEFAULT_CHUNK_SIZE)  # type: ignore[arg-type]
        assert result.byte_length == self._LOGICAL_BYTES  # full logical volume consumed
        assert reader.reads_without_size == 0
        assert reader.max_read_size <= DEFAULT_CHUNK_SIZE  # bounded reads honored
        assert len(result.hex_digest) == 64

    def test_digest_deterministic_across_runs(self) -> None:
        first = sha256_stream(self._giant(), chunk_size=DEFAULT_CHUNK_SIZE).hex_digest  # type: ignore[arg-type]
        second = sha256_stream(self._giant(), chunk_size=DEFAULT_CHUNK_SIZE).hex_digest  # type: ignore[arg-type]
        assert first == second
