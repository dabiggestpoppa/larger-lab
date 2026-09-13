"""SENSOR-B4-I03 — immutable local T0A blob store tests (core backend).

Covers (I03 §47-§72): exact byte round-trip (empty, JSON-like, NUL, all byte
values, deterministic binary, large streamed fixture); H1/H2/H3 separation;
idempotent duplicate behavior; immutability (no public overwrite); missing vs
empty distinction; corruption detection; clock determinism; neutral
storage_uri; backend layout limited to blobs/ + staging/; staging-identity
safety; conservative permissions; provider independence; network 0.

Adversarial crash/race/order coverage (staging isolation, crash matrix,
operation-order contract, concurrent writers, cross-filesystem denial,
long-component denial) lives in `test_blob_store_adversarial.py`
(commit-sequence I03C).
"""

from __future__ import annotations

import hashlib
import inspect
import io
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest
from crypto_sensor_fabric.storage import (
    BlobMissing,
    ExistingBlobIntegrityConflict,
    IntegrityState,
    LocalBlobStore,
    ProviderChecksumMismatch,
    PutDisposition,
    StorageEncoding,
    UnsafeObjectKey,
)

FIXED = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)

MEDIA = "application/octet-stream"


def deterministic_bytes(size: int, seed: int = 12345) -> bytes:
    out = bytearray()
    state = seed
    while len(out) < size:
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        out.append(state & 0xFF)
    return bytes(out)


def make_store(tmp_path: Path, **kwargs: object) -> LocalBlobStore:
    return LocalBlobStore(tmp_path, clock=lambda: FIXED, **kwargs)


def final_path_for(tmp_path: Path, sha: str, encoding: StorageEncoding) -> Path:
    suffix = ".blob" if encoding is StorageEncoding.NONE else ".blob.zst"
    return (
        tmp_path / "blobs" / "sha256" / sha[:2] / sha[2:4] / f"{sha}{suffix}"
    )


class _BoundedOnlyReader(io.RawIOBase):
    """A source stream that hard-fails on unbounded read()."""

    def __init__(self, data: bytes) -> None:
        self._buf = io.BytesIO(data)

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            raise AssertionError("unbounded read() is forbidden")
        return self._buf.read(size)


class TestPutOpenRoundTrip:
    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_exact_json_bytes_roundtrip(self, tmp_path, encoding: StorageEncoding) -> None:
        data = b'{"rows":[{"t":1730000000,"o":"123.45","c":"124.10"}]}\n'
        store = make_store(tmp_path)
        result = store.put_bytes(data, storage_encoding=encoding, source_media_type="application/json")
        assert result.disposition is PutDisposition.COMMITTED_NEW
        with store.open_blob(result.blob.blob_sha256, encoding) as fh:
            assert fh.read() == data

    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_all_byte_values_roundtrip(self, tmp_path, encoding: StorageEncoding) -> None:
        data = bytes(range(256)) * 64
        store = make_store(tmp_path)
        result = store.put_bytes(data, storage_encoding=encoding, source_media_type=MEDIA)
        with store.open_blob(result.blob.blob_sha256, encoding) as fh:
            assert fh.read() == data

    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_nul_bytes_roundtrip(self, tmp_path, encoding: StorageEncoding) -> None:
        data = b"\x00\x00\x01\x00\xff\x00mid\x00tail"
        store = make_store(tmp_path)
        result = store.put_bytes(data, storage_encoding=encoding, source_media_type=MEDIA)
        with store.open_blob(result.blob.blob_sha256, encoding) as fh:
            assert fh.read() == data

    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_random_binary_fixture(self, tmp_path, encoding: StorageEncoding) -> None:
        data = deterministic_bytes(120_000, seed=777)
        store = make_store(tmp_path)
        result = store.put_bytes(data, storage_encoding=encoding, source_media_type=MEDIA)
        with store.open_blob(result.blob.blob_sha256, encoding) as fh:
            assert fh.read() == data

    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_large_streamed_fixture(self, tmp_path, encoding: StorageEncoding) -> None:
        # ~3 MiB deterministic fixture through the STREAMING path only.
        data = deterministic_bytes(3 * 1024 * 1024, seed=31415)
        store = make_store(tmp_path, chunk_size=1 << 18)
        result = store.put(
            io.BytesIO(data), storage_encoding=encoding, source_media_type=MEDIA
        )
        assert result.blob.byte_length == len(data)
        with store.open_blob(result.blob.blob_sha256, encoding) as fh:
            assert fh.read() == data

    def test_stream_starts_at_current_position(self, tmp_path) -> None:
        payload = b"the part after the header"
        source = io.BytesIO(b"IMPORTANT-HEADER" + payload)
        source.seek(len(b"IMPORTANT-HEADER"))
        store = make_store(tmp_path)
        result = store.put(source, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert result.blob.blob_sha256 == hashlib.sha256(payload).hexdigest()
        with store.open_blob(result.blob.blob_sha256, StorageEncoding.NONE) as fh:
            assert fh.read() == payload

    def test_nonseekable_source_accepted(self, tmp_path) -> None:
        data = deterministic_bytes(40_000)

        class NonSeekable(io.RawIOBase):
            def __init__(self, payload: bytes) -> None:
                self._buf = io.BytesIO(payload)

            def read(self, size: int = -1) -> bytes:
                if size is None or size < 0:
                    size = 1 << 16
                return self._buf.read(size)

            def seekable(self) -> bool:
                return False

        store = make_store(tmp_path)
        result = store.put(NonSeekable(data), storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert result.blob.blob_sha256 == hashlib.sha256(data).hexdigest()

    def test_source_not_closed_by_store(self, tmp_path) -> None:
        source = io.BytesIO(b"caller owns me")
        store = make_store(tmp_path)
        store.put(source, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert not source.closed

    def test_bounded_only_source_accepted(self, tmp_path) -> None:
        data = deterministic_bytes(60_000)
        store = make_store(tmp_path)
        result = store.put(
            _BoundedOnlyReader(data),
            storage_encoding=StorageEncoding.ZSTD,
            source_media_type=MEDIA,
        )
        assert result.blob.byte_length == len(data)

    def test_clock_is_injected_deterministic(self, tmp_path) -> None:
        store = make_store(tmp_path)
        result = store.put_bytes(b"x", storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert result.blob.created_at == FIXED
        assert result.blob.created_at.tzinfo is not None

    def test_storage_uri_is_neutral_object_key(self, tmp_path) -> None:
        data = b"absolute roots must not leak into identity"
        store = make_store(tmp_path)
        result = store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert result.blob.storage_uri == result.object_key
        assert result.object_key.startswith("blobs/sha256/")
        assert "\\" not in result.object_key
        assert str(tmp_path) not in result.blob.storage_uri

    def test_integrity_state_local_hash_verified(self, tmp_path) -> None:
        store = make_store(tmp_path)
        result = store.put_bytes(b"x", storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert result.blob.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED

    def test_evidence_blob_counts_truthful(self, tmp_path) -> None:
        data = deterministic_bytes(3000)
        store = make_store(tmp_path)
        none_result = store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert none_result.blob.byte_length == len(data)
        assert none_result.blob.stored_byte_length == len(data)
        zstd_result = store.put_bytes(data, storage_encoding=StorageEncoding.ZSTD, source_media_type=MEDIA)
        assert zstd_result.blob.byte_length == len(data)
        assert zstd_result.blob.stored_byte_length < len(data)
        assert zstd_result.blob.blob_sha256 == none_result.blob.blob_sha256


class TestH1H2H3:
    def test_none_h1_equals_h2(self, tmp_path) -> None:
        data = b"stored == source for NONE"
        store = make_store(tmp_path)
        result = store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert result.stored_sha256 == result.source_sha256

    def test_zstd_h1_differs_from_h2(self, tmp_path) -> None:
        data = b"compressible-payload-" * 500
        store = make_store(tmp_path)
        result = store.put_bytes(data, storage_encoding=StorageEncoding.ZSTD, source_media_type=MEDIA)
        assert result.source_sha256 == hashlib.sha256(data).hexdigest()
        assert result.stored_sha256 != result.source_sha256

    def test_h1_never_replaced_by_h2(self, tmp_path) -> None:
        data = b"identity is source bytes, not stored bytes"
        store = make_store(tmp_path)
        zresult = store.put_bytes(data, storage_encoding=StorageEncoding.ZSTD, source_media_type=MEDIA)
        nresult = store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert zresult.blob.blob_sha256 == nresult.blob.blob_sha256 == hashlib.sha256(data).hexdigest()

    @pytest.mark.parametrize(
        "algorithm",
        ["SHA256", "MD5", "CRC32"],
    )
    def test_h3_provider_checksum_valid(self, tmp_path, algorithm: str) -> None:
        data = b"provider published a checksum for these exact bytes"
        store = make_store(tmp_path)
        expected = _h3_value(data, algorithm)
        result = store.put_bytes(
            data,
            storage_encoding=StorageEncoding.NONE,
            source_media_type=MEDIA,
            provider_checksum_algorithm=algorithm,
            provider_checksum_value=expected,
        )
        assert result.disposition is PutDisposition.COMMITTED_NEW

    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_h3_mismatch_fails_before_commit(self, tmp_path, encoding: StorageEncoding) -> None:
        data = b"exact source bytes"
        store = make_store(tmp_path)
        wrong = hashlib.sha256(b"different bytes").hexdigest()
        with pytest.raises(ProviderChecksumMismatch):
            store.put(
                io.BytesIO(data),
                storage_encoding=encoding,
                source_media_type=MEDIA,
                provider_checksum_algorithm="SHA256",
                provider_checksum_value=wrong,
            )
        sha = hashlib.sha256(data).hexdigest()
        assert not final_path_for(tmp_path, sha, encoding).exists()
        staging_files = list((tmp_path / "staging").glob("*.partial"))
        assert staging_files, "staging evidence must be preserved on H3 failure"

    def test_h3_lowercase_uppercase_accepted(self, tmp_path) -> None:
        data = b"case-insensitive canonical comparison"
        store = make_store(tmp_path)
        upper = hashlib.sha256(data).hexdigest().upper()
        result = store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA,
            provider_checksum_algorithm="SHA256", provider_checksum_value=upper,
        )
        assert result.disposition is PutDisposition.COMMITTED_NEW

    def test_h3_algorithm_without_value_rejected(self, tmp_path) -> None:
        store = make_store(tmp_path)
        with pytest.raises(ValueError):
            store.put_bytes(b"x", storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA,
                            provider_checksum_algorithm="SHA256")

    def test_h3_value_without_algorithm_rejected(self, tmp_path) -> None:
        store = make_store(tmp_path)
        with pytest.raises(ValueError):
            store.put_bytes(b"x", storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA,
                            provider_checksum_value="0" * 64)

    def test_h3_bad_algorithm_rejected(self, tmp_path) -> None:
        store = make_store(tmp_path)
        with pytest.raises(ValueError):
            store.put_bytes(b"x", storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA,
                            provider_checksum_algorithm="SHA1", provider_checksum_value="0" * 40)

    def test_h3_bad_format_rejected(self, tmp_path) -> None:
        store = make_store(tmp_path)
        with pytest.raises(ValueError):
            store.put_bytes(b"x", storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA,
                            provider_checksum_algorithm="SHA256", provider_checksum_value="not-hex")


def _h3_value(data: bytes, algorithm: str) -> str:
    import zlib

    if algorithm == "SHA256":
        return hashlib.sha256(data).hexdigest()
    if algorithm == "MD5":
        return hashlib.md5(data).hexdigest()
    return format(zlib.crc32(data), "08x")


class TestDedupAndReuse:
    def test_duplicate_put_reuses_one_final(self, tmp_path) -> None:
        data = b"same exact bytes twice"
        store = make_store(tmp_path)
        first = store.put_bytes(data, storage_encoding=StorageEncoding.ZSTD, source_media_type=MEDIA)
        sha = first.blob.blob_sha256
        final = final_path_for(tmp_path, sha, StorageEncoding.ZSTD)
        mtime = final.stat().st_mtime_ns
        second = store.put_bytes(data, storage_encoding=StorageEncoding.ZSTD, source_media_type=MEDIA)
        assert second.disposition is PutDisposition.REUSED_EXISTING
        assert second.blob.blob_sha256 == sha
        assert final.stat().st_mtime_ns == mtime, "reuse must not touch the final"
        assert [p.name for p in (tmp_path / "blobs" / "sha256" / sha[:2] / sha[2:4]).iterdir()] == [
            f"{sha}.blob.zst"
        ]

    def test_duplicate_put_cleans_its_staging(self, tmp_path) -> None:
        data = b"transient staging removed on reuse"
        store = make_store(tmp_path)
        store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert not list((tmp_path / "staging").rglob("*.partial"))

    def test_encodings_are_distinct_objects(self, tmp_path) -> None:
        data = b"distinct wrapper objects"
        store = make_store(tmp_path)
        n = store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        z = store.put_bytes(data, storage_encoding=StorageEncoding.ZSTD, source_media_type=MEDIA)
        assert n.object_key != z.object_key
        assert n.disposition is PutDisposition.COMMITTED_NEW
        assert z.disposition is PutDisposition.COMMITTED_NEW


class TestNoClobberImmutability:
    def test_no_public_overwrite_method(self, tmp_path) -> None:
        store = make_store(tmp_path)
        public = {name for name in dir(store) if not name.startswith("_")}
        assert "overwrite" not in public
        assert "replace" not in public
        assert "write" not in public

    def test_repeated_put_never_changes_final(self, tmp_path) -> None:
        data = deterministic_bytes(20_000)
        store = make_store(tmp_path)
        first = store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        final = final_path_for(tmp_path, first.blob.blob_sha256, StorageEncoding.NONE)
        before = final.read_bytes()
        for _ in range(3):
            store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert final.read_bytes() == before

    def test_existing_corrupt_collision_conflicts_not_overwrites(self, tmp_path) -> None:
        data = b"correct source bytes"
        store = make_store(tmp_path)
        first = store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        final = final_path_for(tmp_path, first.blob.blob_sha256, StorageEncoding.NONE)
        final.write_bytes(b"EVIL" * 20)  # bypasses the API deliberately
        with pytest.raises(ExistingBlobIntegrityConflict):
            store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert final.read_bytes() == b"EVIL" * 20  # NOT overwritten
        assert list((tmp_path / "staging").glob("*.partial")), "staging preserved on conflict"

    def test_corrupt_existing_not_reused_as_valid(self, tmp_path) -> None:
        data = b"identity payload"
        store = make_store(tmp_path)
        first = store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        final = final_path_for(tmp_path, first.blob.blob_sha256, StorageEncoding.NONE)
        final.write_bytes(b"X" * len(data))
        check = store.verify_blob(first.blob.blob_sha256, StorageEncoding.NONE)
        assert check.integrity_state is IntegrityState.QUARANTINED_INTEGRITY_FAILURE
        assert check.observed_hash != first.blob.blob_sha256

    def test_verify_blob_detects_stored_h2_mismatch(self, tmp_path) -> None:
        data = b"h2 verified when supplied"
        store = make_store(tmp_path)
        result = store.put_bytes(data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        check = store.verify_blob(
            result.blob.blob_sha256,
            StorageEncoding.NONE,
            expected_h2="0" * 64,
        )
        assert check.integrity_state is IntegrityState.QUARANTINED_INTEGRITY_FAILURE

    def test_verify_blob_missing_raises(self, tmp_path) -> None:
        store = make_store(tmp_path)
        empty_sha = hashlib.sha256(b"").hexdigest()
        with pytest.raises(BlobMissing):
            store.verify_blob(empty_sha, StorageEncoding.NONE)

    def test_open_blob_missing_raises_distinct_from_empty(self, tmp_path) -> None:
        store = make_store(tmp_path)
        empty_sha = hashlib.sha256(b"").hexdigest()
        assert store.blob_exists(empty_sha, StorageEncoding.NONE) is False
        with (
            pytest.raises(BlobMissing),
            store.open_blob(empty_sha, StorageEncoding.NONE),
        ):
            pass  # pragma: no cover


class TestEmptySource:
    @pytest.mark.parametrize(
        "encoding",
        [StorageEncoding.NONE, StorageEncoding.ZSTD],
    )
    def test_empty_is_valid_evidence(self, tmp_path, encoding: StorageEncoding) -> None:
        store = make_store(tmp_path)
        empty_sha = hashlib.sha256(b"").hexdigest()
        result = store.put_bytes(b"", storage_encoding=encoding, source_media_type=MEDIA)
        assert result.blob.blob_sha256 == empty_sha
        assert result.blob.byte_length == 0
        assert store.blob_exists(empty_sha, encoding)
        with store.open_blob(empty_sha, encoding) as fh:
            assert fh.read() == b""
        check = store.verify_blob(empty_sha, encoding)
        assert check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED


class TestLayoutAndStagingIdentity:
    def test_only_required_dirs_created(self, tmp_path) -> None:
        store = make_store(tmp_path)
        store.put_bytes(b"x", storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        names = {p.name for p in tmp_path.iterdir() if p.is_dir()}
        assert names == {"blobs", "staging"}
        forbidden = {"projections", "catalogs", "duckdb", "postgres", "exports", "quarantine"}
        assert names.isdisjoint(forbidden)

    def test_job_id_escaped_never_traverses(self, tmp_path) -> None:
        store = make_store(tmp_path)
        result = store.put_bytes(
            b"x",
            storage_encoding=StorageEncoding.NONE,
            source_media_type=MEDIA,
            job_id="../evil",
        )
        assert result.disposition is PutDisposition.COMMITTED_NEW
        staging = tmp_path / "staging"
        assert (staging / "%2E%2E%2Fevil").is_dir()
        assert not (tmp_path / "evil").exists()
        assert not (tmp_path.parent / "evil").exists()

    def test_job_id_nul_and_backslash_escaped(self, tmp_path) -> None:
        store = make_store(tmp_path)
        for i, nasty in enumerate(("a\x00b", "a\\b", "a/b")):
            payload = f"payload-{i}".encode()
            result = store.put_bytes(
                payload,
                storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA,
                job_id=nasty,
            )
            assert result.disposition is PutDisposition.COMMITTED_NEW
        staging_names = {p.name for p in (tmp_path / "staging").iterdir()}
        assert "a\\b" not in staging_names
        assert "a/b" not in staging_names
        assert "a\x00b" not in staging_names
        # the escaped canonical forms ARE the staging identities
        assert "a%5Cb" in staging_names
        assert "a%2Fb" in staging_names
        assert "a%00b" in staging_names

    def test_job_id_empty_rejected(self, tmp_path) -> None:
        store = make_store(tmp_path)
        with pytest.raises(UnsafeObjectKey):
            store.put_bytes(
                b"x",
                storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA,
                job_id="",
            )

    def test_staging_nonce_never_becomes_identity(self, tmp_path) -> None:
        store = make_store(tmp_path)
        result = store.put_bytes(b"identity is content, not naming", storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        assert result.blob.blob_sha256 == hashlib.sha256(b"identity is content, not naming").hexdigest()
        assert ".partial" not in result.object_key
        final = list((tmp_path / "blobs" / "sha256").rglob("*"))
        assert all(".partial" not in p.name for p in final)


class TestPermissions:
    @pytest.mark.skipif(os.name != "posix", reason="POSIX mode bits do not apply on Windows")
    def test_final_not_world_writable(self, tmp_path) -> None:
        store = make_store(tmp_path)
        result = store.put_bytes(b"x", storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA)
        final = final_path_for(tmp_path, result.blob.blob_sha256, StorageEncoding.NONE)
        mode = stat.S_IMODE(os.stat(final).st_mode)
        assert mode & 0o077 == 0


class TestProviderIndependence:
    def test_storage_modules_never_import_providers_or_network(self) -> None:
        import crypto_sensor_fabric.storage.atomic as atomic_mod
        import crypto_sensor_fabric.storage.blob_store as blob_mod
        import crypto_sensor_fabric.storage.compression as comp_mod

        for module in (atomic_mod, blob_mod, comp_mod):
            source = inspect.getsource(module)
            assert "crypto_sensor_fabric.providers" not in source
            assert "from ..providers" not in source
            assert "import requests" not in source
            assert "import httpx" not in source
            assert "import aiohttp" not in source
            assert "urllib" not in source

    def test_storage_import_pulls_no_provider_adapter_modules(self) -> None:
        # Storage legitimately imports the frozen provider/base shared
        # contracts (ResumeToken etc.), but MUST NOT import any provider
        # ADAPTER or probe/network module.
        import subprocess
        import sys as _sys

        forbidden_prefixes = (
            "crypto_sensor_fabric.providers.kraken",
            "crypto_sensor_fabric.providers.gate",
            "crypto_sensor_fabric.providers.okx",
            "crypto_sensor_fabric.providers.deribit",
            "crypto_sensor_fabric.providers.network_smoke",
        )
        code = (
            "import sys; "
            "import crypto_sensor_fabric.storage as s; "
            "mods = [m for m in sys.modules if m.startswith('crypto_sensor_fabric.providers')]; "
            "print(','.join(sorted(mods)))"
        )
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).parents[0] / ".." / ".." / ".." / "src"))
        out = subprocess.run(
            [_sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(Path(__file__).parents[0] / ".." / ".." / ".."),
            check=True,
        )
        loaded = [m for m in out.stdout.strip().split(",") if m]
        for prefix in forbidden_prefixes:
            assert not any(m == prefix or m.startswith(prefix + ".") for m in loaded), (
                f"storage import pulled provider adapter {prefix}: {loaded}"
            )
