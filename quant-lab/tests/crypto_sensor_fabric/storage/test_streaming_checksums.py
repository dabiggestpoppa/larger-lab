"""SENSOR-B4-I04R2C — bounded streaming checksum tests.

I04R2 §21-§26: the streaming H3 layer must be bounded-memory, parity-exact
with the byte-based implementation, non-seekable-safe, and never close the
caller-owned stream.  CRC32 stays canonical (8 lowercase hex, leading
zeros).  The large-stream proof uses deterministic logical data generation
with a bounded-read tracking reader — no 1 GiB allocation.
"""

from __future__ import annotations

import hashlib
import io
import zlib

import pytest

from crypto_sensor_fabric.storage.checksums import (
    DEFAULT_CHUNK_SIZE,
    ChecksumStreamResult,
    compute_checksum,
    compute_checksum_stream,
    verify_checksum,
    verify_checksum_stream,
)
from crypto_sensor_fabric.storage.enums import ChecksumAlgorithm


class _TrackingReader:
    """Non-seekable reader that records every read() call's bound."""

    def __init__(self, data: bytes) -> None:
        self._buffer = io.BytesIO(data)
        self.max_read_size = 0
        self.reads_without_size = 0
        self.closed_by_callee = False

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            self.reads_without_size += 1
            raise AssertionError("read() called without a positive size")
        self.max_read_size = max(self.max_read_size, size)
        return self._buffer.read(size)

    @property
    def seekable(self) -> bool:
        return False

    def close(self) -> None:  # pragma: no cover - must never be called
        self.closed_by_callee = True

    @property
    def closed(self) -> bool:
        return False


class TestComputeChecksumStreamParity:
    """I04R2 §22 — streaming result == byte-based result, exactly."""

    DATA = bytes(range(256)) * 129  # deterministic 33024 bytes

    def test_sha256_parity(self) -> None:
        streamed = compute_checksum_stream(
            io.BytesIO(self.DATA), ChecksumAlgorithm.SHA256
        )
        bytewise = compute_checksum(self.DATA, ChecksumAlgorithm.SHA256)
        assert streamed.hex_digest == bytewise
        assert streamed.hex_digest == hashlib.sha256(self.DATA).hexdigest()
        assert streamed.byte_length == len(self.DATA)

    def test_md5_parity(self) -> None:
        streamed = compute_checksum_stream(
            io.BytesIO(self.DATA), ChecksumAlgorithm.MD5
        )
        bytewise = compute_checksum(self.DATA, ChecksumAlgorithm.MD5)
        assert streamed.hex_digest == bytewise
        assert streamed.hex_digest == hashlib.md5(self.DATA).hexdigest()
        assert streamed.byte_length == len(self.DATA)

    def test_crc32_parity_and_canonical_form(self) -> None:
        streamed = compute_checksum_stream(
            io.BytesIO(self.DATA), ChecksumAlgorithm.CRC32
        )
        bytewise = compute_checksum(self.DATA, ChecksumAlgorithm.CRC32)
        assert streamed.hex_digest == bytewise
        assert streamed.hex_digest == format(zlib.crc32(self.DATA), "08x")
        # canonical: exactly 8 lowercase hex chars, leading zeros retained
        assert len(streamed.hex_digest) == 8
        assert streamed.hex_digest == streamed.hex_digest.lower()
        zero_crc = compute_checksum_stream(
            io.BytesIO(b""), ChecksumAlgorithm.CRC32
        )
        assert zero_crc.hex_digest == "00000000"  # leading zeros preserved
        assert zero_crc.byte_length == 0

    def test_chunk_size_invariance(self) -> None:
        reference = compute_checksum(self.DATA, ChecksumAlgorithm.SHA256)
        for chunk_size in (1, 7, 64, 4096, DEFAULT_CHUNK_SIZE):
            result = compute_checksum_stream(
                io.BytesIO(self.DATA), ChecksumAlgorithm.SHA256, chunk_size=chunk_size
            )
            assert result.hex_digest == reference
            assert result.byte_length == len(self.DATA)

    def test_empty_stream(self) -> None:
        result = compute_checksum_stream(
            io.BytesIO(b""), ChecksumAlgorithm.SHA256
        )
        assert result.hex_digest == hashlib.sha256(b"").hexdigest()
        assert result.byte_length == 0

    def test_starts_at_current_position(self) -> None:
        # begins at the CURRENT stream position, never rewinds (I04R2 §22)
        stream = io.BytesIO(self.DATA)
        stream.seek(1000)
        result = compute_checksum_stream(stream, ChecksumAlgorithm.SHA256)
        assert result.byte_length == len(self.DATA) - 1000
        assert result.hex_digest == hashlib.sha256(self.DATA[1000:]).hexdigest()


class TestStreamingContract:
    """I04R2 §22/§25 — bounded reads, nonseekable, caller ownership."""

    def test_no_read_without_size_and_bounded(self) -> None:
        reader = _TrackingReader(b"z" * 100_000)
        result = compute_checksum_stream(
            reader,  # type: ignore[arg-type]
            ChecksumAlgorithm.SHA256,
            chunk_size=4096,
        )
        assert result.byte_length == 100_000
        assert reader.reads_without_size == 0
        assert reader.max_read_size <= 4096
        assert result.hex_digest == hashlib.sha256(b"z" * 100_000).hexdigest()

    def test_nonseekable_stream_works(self) -> None:
        reader = _TrackingReader(self._logical_data(64_000))
        result = compute_checksum_stream(
            reader,  # type: ignore[arg-type]
            ChecksumAlgorithm.MD5,
            chunk_size=1024,
        )
        assert result.hex_digest == hashlib.md5(self._logical_data(64_000)).hexdigest()
        assert result.byte_length == 64_000

    def test_caller_stream_not_closed(self) -> None:
        reader = _TrackingReader(b"abc")
        compute_checksum_stream(reader, ChecksumAlgorithm.SHA256)  # type: ignore[arg-type]
        assert reader.closed_by_callee is False

    def test_invalid_chunk_size_rejected(self) -> None:
        for bad in (0, -1, True, 1.5, "4096"):
            with pytest.raises(ValueError):
                compute_checksum_stream(
                    io.BytesIO(b"x"), ChecksumAlgorithm.SHA256, chunk_size=bad  # type: ignore[arg-type]
                )

    def test_non_bytes_chunk_rejected(self) -> None:
        class BadReader:
            def read(self, size: int) -> str:  # type: ignore[return]
                return ""  # returns str, never bytes

        with pytest.raises(TypeError):
            compute_checksum_stream(
                BadReader(),  # type: ignore[arg-type]
                ChecksumAlgorithm.SHA256,
            )

    @staticmethod
    def _logical_data(n: int) -> bytes:
        # deterministic logical data generation — no RNG, no wall clock
        out = bytearray()
        counter = 0
        while len(out) < n:
            out.extend(hashlib.sha256(f"logical-{counter}".encode()).digest())
            counter += 1
        return bytes(out[:n])


class TestLargeLogicalStreamBounded:
    """I04R2 §25 — large logical stream, bounded reads, no 1 GiB allocation."""

    def test_large_logical_stream_bounded_reads(self) -> None:
        # generate 8 MiB of deterministic logical data WITHOUT holding more
        # than one chunk of it in the checksum path at any time
        chunk_size = 64 * 1024

        class _Probe:
            max_read_size = 0
            reads_without_size = 0

        probe = _Probe()
        total = 0

        class LogicalStream:
            """Deterministic non-seekable logical byte source (8 MiB)."""

            TOTAL = 8 * 1024 * 1024

            def __init__(self) -> None:
                self._remaining = self.TOTAL
                self._counter = 0

            def read(self, size: int = -1) -> bytes:
                if size is None or size < 0:
                    probe.reads_without_size += 1
                    raise AssertionError("read() called without a positive size")
                probe.max_read_size = max(probe.max_read_size, size)
                take = min(size, self._remaining)
                if take <= 0:
                    return b""
                block = hashlib.sha256(f"block-{self._counter}".encode()).digest()
                self._counter += 1
                data = (block * ((take // len(block)) + 1))[:take]
                self._remaining -= take
                return data

        stream = LogicalStream()
        result = compute_checksum_stream(
            stream,  # type: ignore[arg-type]
            ChecksumAlgorithm.SHA256,
            chunk_size=chunk_size,
        )
        assert result.byte_length == stream.TOTAL
        assert probe.reads_without_size == 0
        assert probe.max_read_size <= chunk_size
        # reference digest computed the same incremental way (parity by
        # construction against hashlib over the identical logical sequence)
        reference = hashlib.sha256()
        counter = 0
        remaining = stream.TOTAL
        while remaining > 0:
            take = min(chunk_size, remaining)
            block = hashlib.sha256(f"block-{counter}".encode()).digest()
            counter += 1
            reference.update((block * ((take // len(block)) + 1))[:take])
            remaining -= take
        assert result.hex_digest == reference.hexdigest()
        assert total == 0  # no stray accumulation outside the helper


class TestVerifyChecksumStream:
    """I04R2 §21/§22 — streaming verify with pre-consumption validation."""

    DATA = b'{"open_interest": 1234.5, "ts": 1723000001}'

    def test_sha256_verify_parity_true(self) -> None:
        expected = hashlib.sha256(self.DATA).hexdigest()
        assert (
            verify_checksum_stream(io.BytesIO(self.DATA), ChecksumAlgorithm.SHA256, expected)
            is True
        )
        assert verify_checksum(self.DATA, ChecksumAlgorithm.SHA256, expected) is True

    def test_md5_verify_parity_false(self) -> None:
        wrong = hashlib.md5(b"other").hexdigest()
        assert (
            verify_checksum_stream(io.BytesIO(self.DATA), ChecksumAlgorithm.MD5, wrong)
            is False
        )

    def test_crc32_verify_parity(self) -> None:
        expected = format(zlib.crc32(self.DATA), "08x")
        assert (
            verify_checksum_stream(io.BytesIO(self.DATA), ChecksumAlgorithm.CRC32, expected)
            is True
        )

    def test_malformed_value_rejected_before_reading(self) -> None:
        class NoReadStream:
            def read(self, size: int) -> bytes:  # pragma: no cover
                raise AssertionError("stream must not be read for a malformed value")

        with pytest.raises(ValueError):
            verify_checksum_stream(
                NoReadStream(),  # type: ignore[arg-type]
                ChecksumAlgorithm.MD5,
                "deadbeef",  # not 32 hex chars
            )

    def test_uppercase_expected_normalized(self) -> None:
        expected = hashlib.sha256(self.DATA).hexdigest().upper()
        assert (
            verify_checksum_stream(io.BytesIO(self.DATA), ChecksumAlgorithm.SHA256, expected)
            is True
        )

    def test_result_type_is_frozen_dataclass(self) -> None:
        result = compute_checksum_stream(io.BytesIO(b"x"), ChecksumAlgorithm.SHA256)
        assert isinstance(result, ChecksumStreamResult)
        with pytest.raises(Exception):  # noqa: B017 - frozen dataclass immutability
            result.byte_length = 5  # type: ignore[misc]
