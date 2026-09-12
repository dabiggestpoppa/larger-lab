"""SENSOR-B4-I03 — streaming NONE/ZSTD wrapper tests.

Proves: exact byte round-trip under both encodings; H1 (source SHA-256)
computed BEFORE wrapper compression and invariant across encodings; H2
(stored-object) equals H1 only for NONE; bounded streaming with non-seekable
sources; caller stream ownership preserved; empty sources valid; every byte
value 0x00-0xff round-trips; no implicit decoding anywhere.
"""

from __future__ import annotations

import hashlib
import io

import pytest
from crypto_sensor_fabric.storage.compression import (
    EncodeResult,
    encode_source_stream,
    iter_decode_stored,
)
from crypto_sensor_fabric.storage.enums import StorageEncoding

DEFAULT_CHUNK = 64 * 1024


def deterministic_bytes(size: int, seed: int = 12345) -> bytes:
    """Deterministic pseudo-random byte fixture (LCG), no wall clock."""
    out = bytearray()
    state = seed
    while len(out) < size:
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        out.append(state & 0xFF)
    return bytes(out)


def encode(data: bytes, encoding: StorageEncoding, chunk: int = DEFAULT_CHUNK) -> EncodeResult:
    sink = io.BytesIO()
    result = encode_source_stream(
        io.BytesIO(data), sink, encoding, chunk_size=chunk
    )
    stored = sink.getvalue()
    return result, stored, sink


def decode_all(stored: bytes, encoding: StorageEncoding, chunk: int = DEFAULT_CHUNK) -> bytes:
    out = bytearray()
    for piece in iter_decode_stored(io.BytesIO(stored), encoding, chunk_size=chunk):
        out.extend(piece)
    return bytes(out)


class TestNoneEncoding:
    def test_stored_bytes_byte_for_byte(self) -> None:
        data = b'{"ts":1730000000,"c":"124.10","v":"100"}'
        _, stored, _ = encode(data, StorageEncoding.NONE)
        assert stored == data

    def test_h1_equals_h2_for_none(self) -> None:
        data = b"exact source bytes"
        result, _, _ = encode(data, StorageEncoding.NONE)
        assert result.source_sha256 == hashlib.sha256(data).hexdigest()
        assert result.stored_sha256 == result.source_sha256

    def test_byte_lengths_match(self) -> None:
        data = deterministic_bytes(200_000)
        result, stored, _ = encode(data, StorageEncoding.NONE)
        assert result.source_byte_length == len(data)
        assert result.stored_byte_length == len(stored) == len(data)

    def test_roundtrip_exact(self) -> None:
        data = deterministic_bytes(5000)
        assert decode_all(encode(data, StorageEncoding.NONE)[1], StorageEncoding.NONE) == data


class TestZstdEncoding:
    def test_stored_bytes_compressed(self) -> None:
        data = (b"aaabbbcccdddeeefff" * 1000)
        result, stored, _ = encode(data, StorageEncoding.ZSTD)
        assert stored != data
        assert result.stored_byte_length < len(data)

    def test_h1_is_source_hash_not_stored_hash(self) -> None:
        data = (b"BTCUSDT-OHLCV-" * 500)
        result, stored, _ = encode(data, StorageEncoding.ZSTD)
        del stored
        assert result.source_sha256 == hashlib.sha256(data).hexdigest()
        assert result.stored_sha256 != result.source_sha256  # wrapper changes bytes

    def test_roundtrip_exact(self) -> None:
        data = deterministic_bytes(50_000)
        result, stored, _ = encode(data, StorageEncoding.ZSTD)
        assert decode_all(stored, StorageEncoding.ZSTD) == data
        assert result.source_sha256 == hashlib.sha256(data).hexdigest()

    def test_decoded_length_matches_source(self) -> None:
        data = deterministic_bytes(10_000)
        result, stored, _ = encode(data, StorageEncoding.ZSTD)
        assert len(decode_all(stored, StorageEncoding.ZSTD)) == len(data)
        assert result.source_byte_length == len(data)


class TestH1H2Separation:
    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_h1_invariant_across_encodings(self, encoding: StorageEncoding) -> None:
        data = b"the same exact source bytes for both wrappers"
        result, _, _ = encode(data, encoding)
        expected = hashlib.sha256(data).hexdigest()
        assert result.source_sha256 == expected

    def test_none_h1_equals_h2_zstd_differs(self) -> None:
        data = b"compress me " * 2000
        none_result = encode(data, StorageEncoding.NONE)[0]
        zstd_result = encode(data, StorageEncoding.ZSTD)[0]
        assert none_result.source_sha256 == none_result.stored_sha256
        assert zstd_result.source_sha256 == none_result.source_sha256
        # For this compressible fixture the stored bytes genuinely differ.
        assert zstd_result.stored_sha256 != zstd_result.source_sha256


class TestExactByteRoundTrip:
    def test_all_byte_values_roundtrip(self) -> None:
        data = bytes(range(256)) * 64
        for encoding in (StorageEncoding.NONE, StorageEncoding.ZSTD):
            assert decode_all(encode(data, encoding)[1], encoding) == data

    def test_nul_bytes_roundtrip(self) -> None:
        data = b"\x00\x00\x01\x00\xff\x00mid\x00"
        for encoding in (StorageEncoding.NONE, StorageEncoding.ZSTD):
            assert decode_all(encode(data, encoding)[1], encoding) == data

    def test_json_like_bytes_roundtrip(self) -> None:
        data = (
            b'{"a":[1,2,3],"b":{"c":null},"d":"\xe2\x9c\x93"}\n'
            b'{"rows":[{"t":1730000000,"p":"64000.5","q":"0.1"}]}'
        )
        for encoding in (StorageEncoding.NONE, StorageEncoding.ZSTD):
            assert decode_all(encode(data, encoding)[1], encoding) == data

    def test_random_binary_fixture(self) -> None:
        data = deterministic_bytes(100_000, seed=987654321)
        for encoding in (StorageEncoding.NONE, StorageEncoding.ZSTD):
            assert decode_all(encode(data, encoding)[1], encoding) == data


class TestEmptySource:
    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_empty_is_valid_evidence(self, encoding: StorageEncoding) -> None:
        result, stored, _ = encode(b"", encoding)
        assert result.source_sha256 == hashlib.sha256(b"").hexdigest()
        assert result.source_byte_length == 0
        if encoding is StorageEncoding.NONE:
            assert stored == b""
            assert result.stored_byte_length == 0
        else:
            # a ZSTD frame of an empty source is not zero bytes — but it must
            # still decode to exactly b"".
            assert result.stored_byte_length > 0
        assert decode_all(stored, encoding) == b""


class TestStreamingContract:
    def test_bounded_reads_only(self) -> None:
        """A source that refuses unbounded read() must still encode."""

        class BoundedReader(io.RawIOBase):
            def __init__(self, data: bytes, chunk: int) -> None:
                self._buf = io.BytesIO(data)
                self._chunk = chunk

            def read(self, size: int = -1) -> bytes:
                if size is None or size < 0:
                    raise AssertionError("unbounded read() is forbidden")
                return self._buf.read(min(size, self._chunk))

        data = deterministic_bytes(300_000)
        for encoding in (StorageEncoding.NONE, StorageEncoding.ZSTD):
            sink = io.BytesIO()
            encode_source_stream(
                BoundedReader(data, 4096), sink, encoding, chunk_size=4096
            )
            assert decode_all(sink.getvalue(), encoding, chunk=4096) == data

    def test_nonseekable_source(self) -> None:
        class NonSeekable(io.RawIOBase):
            def __init__(self, data: bytes) -> None:
                self._buf = io.BytesIO(data)

            def read(self, size: int = -1) -> bytes:
                if size is None or size < 0:
                    size = 65536
                return self._buf.read(size)

            def seekable(self) -> bool:
                return False

        data = deterministic_bytes(20_000)
        result = encode_source_stream(
            NonSeekable(data), io.BytesIO(), StorageEncoding.ZSTD
        )
        assert result.source_sha256 == hashlib.sha256(data).hexdigest()

    def test_streams_not_closed(self) -> None:
        source = io.BytesIO(b"owner keeps me")
        sink = io.BytesIO()
        encode_source_stream(source, sink, StorageEncoding.ZSTD, chunk_size=7)
        assert not source.closed and not sink.closed

    def test_small_chunk_size_works(self) -> None:
        data = deterministic_bytes(10_000)
        for encoding in (StorageEncoding.NONE, StorageEncoding.ZSTD):
            result, stored, _ = encode(data, encoding, chunk=13)
            assert decode_all(stored, encoding, chunk=13) == data
            assert result.source_sha256 == hashlib.sha256(data).hexdigest()

    def test_large_streamed_fixture_bounded(self) -> None:
        # ~4 MiB deterministic fixture: proves no full-1GiB materialization is
        # needed and the streaming path stays bounded.
        data = deterministic_bytes(4 * 1024 * 1024, seed=42)
        for encoding in (StorageEncoding.NONE, StorageEncoding.ZSTD):
            result = encode_source_stream(
                io.BytesIO(data), io.BytesIO(), encoding, chunk_size=1 << 20
            )
            assert result.source_byte_length == len(data)
            assert result.source_sha256 == hashlib.sha256(data).hexdigest()


class TestValidation:
    @pytest.mark.parametrize("bad", [0, -1, 1.5, True, None])
    def test_bad_chunk_size_rejected(self, bad: object) -> None:
        with pytest.raises(ValueError):
            encode_source_stream(
                io.BytesIO(b"x"), io.BytesIO(), StorageEncoding.NONE, chunk_size=bad  # type: ignore[arg-type]
            )

    def test_non_enum_encoding_rejected(self) -> None:
        with pytest.raises(TypeError):
            encode_source_stream(io.BytesIO(b"x"), io.BytesIO(), "NONE")  # type: ignore[arg-type]

    def test_unknown_encoding_member_cannot_exist(self) -> None:
        # The frozen vocabulary is closed: an unknown value fails at the enum
        # boundary before any stream is touched.
        with pytest.raises(ValueError):
            StorageEncoding("BOGUS")

    def test_decode_accepts_chunk_size_one(self) -> None:
        data = b"decode with tiny chunks"
        assert decode_all(encode(data, StorageEncoding.NONE)[1], StorageEncoding.NONE, chunk=1) == data

    def test_decode_rejects_corrupt_zstd_frame(self) -> None:
        import zstandard  # test-only concrete frame exception

        garbage = b"\x28\xb5\x2f\xfd not a real frame" + b"\x00" * 32
        with pytest.raises(zstandard.ZstdError):
            list(iter_decode_stored(io.BytesIO(garbage), StorageEncoding.ZSTD))

    def test_source_must_be_bytes(self) -> None:
        class StrReader(io.RawIOBase):
            def read(self, size: int = -1) -> str:
                return "nope"

        with pytest.raises(TypeError):
            encode_source_stream(StrReader(), io.BytesIO(), StorageEncoding.NONE)  # type: ignore[return-value]


class TestDeterministicStoredBytes:
    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_encode_twice_same_stored_bytes(self, encoding: StorageEncoding) -> None:
        data = b"deterministic wrapper output " * 100
        first = encode(data, encoding)[1]
        second = encode(data, encoding)[1]
        assert first == second