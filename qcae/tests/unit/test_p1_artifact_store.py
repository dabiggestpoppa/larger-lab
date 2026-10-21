"""P1-C02 — content-addressed artifact store evidence (P1 spec §6, tests 1–7)."""

from __future__ import annotations

import hashlib

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.artifact_store import (
    ArtifactCollisionError,
    ArtifactCorruptionError,
    ContentAddressedArtifactStore,
)


@pytest.fixture()
def store(tmp_path):
    return ContentAddressedArtifactStore(tmp_path / "artifacts")


class TestIdentity:
    def test_same_bytes_same_digest(self, store) -> None:
        d1 = store.put_bytes(b"evidence payload v1")
        d2 = store.put_bytes(b"evidence payload v1")
        assert d1 == d2 == hashlib.sha256(b"evidence payload v1").hexdigest()

    def test_changed_bytes_changed_digest(self, store) -> None:
        d1 = store.put_bytes(b"evidence payload v1")
        d2 = store.put_bytes(b"evidence payload v2")
        assert d1 != d2

    def test_digest_is_sha256_hex(self, store) -> None:
        d = store.put_bytes(b"x")
        assert len(d) == 64
        int(d, 16)  # hex-parseable


class TestIdempotenceAndCollision:
    def test_duplicate_put_idempotent(self, store) -> None:
        d = store.put_bytes(b"same content")
        assert store.put_bytes(b"same content") == d

    def test_no_silent_overwrite_on_collision(self, store, tmp_path) -> None:
        """A digest/file mismatch is corruption, never rewritten."""
        data = b"the real artifact"
        d = store.put_bytes(data)
        # Simulate on-disk divergence under the same digest path.
        target = store._path_for(d)
        target.write_bytes(b"tampered bytes")
        with pytest.raises(ArtifactCollisionError):
            store.put_bytes(data)


class TestRetrievalAndIntegrity:
    def test_retrieval_returns_original_bytes(self, store) -> None:
        data = b"binary \x00\x01 evidence"
        d = store.put_bytes(data)
        assert store.get_bytes(d) == data

    def test_corrupted_artifact_detected(self, store) -> None:
        d = store.put_bytes(b"intact")
        target = store._path_for(d)
        target.write_bytes(b"mutated")
        with pytest.raises(ArtifactCorruptionError):
            store.get_bytes(d)

    def test_verify_detects_corruption(self, store) -> None:
        d = store.put_bytes(b"intact")
        assert store.verify(d) is True
        store._path_for(d).write_bytes(b"rot")
        assert store.verify(d) is False

    def test_missing_artifact_raises_file_not_found(self, store) -> None:
        with pytest.raises(FileNotFoundError):
            store.get_bytes("f" * 64)


class TestPathSafety:
    @pytest.mark.parametrize("bad", [
        "../" + "a" * 60,
        "a" * 63 + "/../../etc/passwd".replace("/", "")[:1],
        "A" * 64,  # uppercase rejected
        "z" * 64,  # non-hex rejected
        "short",
    ])
    def test_traversal_and_malformed_digests_rejected(self, store, bad) -> None:
        with pytest.raises(QcaeValidationError):
            store.get_bytes(bad)

    def test_path_lies_under_store_root(self, store) -> None:
        d = store.put_bytes(b"where am I")
        p = store._path_for(d)
        assert store._algo_dir in p.parents or p.parent.parent.parent == store._algo_dir
        assert ".." not in p.parts

    def test_layout_is_sha256_sharded(self, store) -> None:
        d = store.put_bytes(b"layout check")
        p = store._path_for(d)
        rel = p.relative_to(store._root)
        assert rel.parts == ("sha256", d[:2], d[2:4], d)


class TestAtomicity:
    def test_atomic_write_leaves_no_temp_files(self, store) -> None:
        store.put_bytes(b"atomic check")
        leftovers = [p for p in store._root.rglob(".tmp-*")]
        assert leftovers == []

    def test_failed_write_cleans_temp(self, store, monkeypatch) -> None:
        import os

        real_replace = os.replace

        def boom(src, dst):
            raise OSError("injected rename failure")

        monkeypatch.setattr(os, "replace", boom)
        with pytest.raises(OSError, match="injected rename failure"):
            store.put_bytes(b"doomed")
        leftovers = [p for p in store._root.rglob(".tmp-*")]
        assert leftovers == []
        monkeypatch.setattr(os, "replace", real_replace)
