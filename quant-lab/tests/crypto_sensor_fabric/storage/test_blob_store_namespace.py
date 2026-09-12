"""SENSOR-B4-I03R1 — namespace durability tests (directory chain + probe).

Covers (I03R1 §9-§25): durable directory-chain creation (every new name is
fsynced into its parent BEFORE the final object is published); concurrent
creation races tolerated; conflicting non-directory components fail closed;
actual NAME_MAX probed from an EXISTING ancestor with fail-closed probe
policy; staging-nonce component validation; machine-readable namespace
durability order (DIR_CREATE < DIR_FSYNC < PARENT_NAMESPACE_FSYNC ...).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from crypto_sensor_fabric.storage import (
    ComponentTooLong,
    LocalBlobStore,
    PutDisposition,
    StorageEncoding,
)
from crypto_sensor_fabric.storage.atomic import (
    OP_DIR_CREATE,
    OP_DIR_FSYNC,
    OP_FINAL_LINK,
    OP_FINAL_PARENT_FSYNC,
    OP_PARENT_NAMESPACE_FSYNC,
    AtomicPublishError,
    DurabilityUnsupported,
    ListOpRecorder,
    default_name_max,
    ensure_durable_directory,
    ensure_durable_directory_chain,
    fsync_directory,
    is_canonical_durable_order,
    publish_no_replace,
    validate_component_length,
)

FIXED = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/octet-stream"


def make_store(tmp_path: Path, **kwargs: object) -> LocalBlobStore:
    return LocalBlobStore(tmp_path, clock=lambda: FIXED, **kwargs)


def _staged_file(tmp_path: Path, name: str = "obj.partial") -> Path:
    p = tmp_path / "staging" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(b"durable chain fixture bytes")
        fh.flush()
        os.fsync(fh.fileno())
    return p


class _FsyncRecorder:
    """I03R1 §22: injectable directory-fsync recorder (test double)."""

    def __init__(self) -> None:
        self.fsynced: list[Path] = []

    def __call__(self, path: Path) -> None:
        fsync_directory(path)
        self.fsynced.append(path)


class TestDurableDirectoryChain:
    def test_every_new_name_fsynced_into_parent(self, tmp_path) -> None:
        base = tmp_path / "base"
        base.mkdir()
        rec = _FsyncRecorder()
        ops = ListOpRecorder()
        leaf = ensure_durable_directory_chain(
            base, ["a", "b", "c"], dir_fsync=rec, ops=ops
        )
        assert leaf == base / "a" / "b" / "c"
        assert leaf.is_dir()
        # Per level: the fresh child dir is flushed, then the parent namespace
        # is flushed so the child's NAME is durable (I03R1 §10 steps 3-4).
        assert rec.fsynced == [
            base / "a",
            base,
            base / "a" / "b",
            base / "a",
            base / "a" / "b" / "c",
            base / "a" / "b",
        ]
        # Each creation emits DIR_CREATE + DIR_FSYNC + PARENT_NAMESPACE_FSYNC
        # in that order (I03R1 §22 machine-readable distinction).
        assert ops.ops.count(OP_DIR_CREATE) == 3
        for i, tag in enumerate(ops.ops):
            if tag == OP_DIR_CREATE:
                assert ops.ops[i + 1] == OP_DIR_FSYNC
                assert ops.ops[i + 2] == OP_PARENT_NAMESPACE_FSYNC

    def test_existing_chain_skips_creation(self, tmp_path) -> None:
        base = tmp_path / "base"
        (base / "x" / "y").mkdir(parents=True)
        rec = _FsyncRecorder()
        ops = ListOpRecorder()
        leaf = ensure_durable_directory_chain(
            base, ["x", "y"], dir_fsync=rec, ops=ops
        )
        assert leaf == base / "x" / "y"
        assert ops.ops == []  # nothing created, nothing fsynced
        assert rec.fsynced == []

    def test_missing_trusted_ancestor_fails_closed(self, tmp_path) -> None:
        with pytest.raises(DurabilityUnsupported):
            ensure_durable_directory_chain(tmp_path / "nope", ["a"])

    def test_nonexistent_component_ok_but_base_must_exist(self, tmp_path) -> None:
        base = tmp_path / "anchor"
        base.mkdir()
        leaf = ensure_durable_directory_chain(base, ["solo"])
        assert leaf == base / "solo"
        assert leaf.is_dir()

    def test_existing_non_directory_component_fails_closed(self, tmp_path) -> None:
        base = tmp_path / "base"
        base.mkdir()
        (base / "blocker").write_bytes(b"a file, not a directory")
        with pytest.raises(AtomicPublishError):
            ensure_durable_directory_chain(base, ["blocker", "deeper"])
        # Fail closed: the blocker is NOT deleted or replaced.
        assert (base / "blocker").is_file()
        assert not (base / "blocker" / "deeper").exists()

    def test_creation_race_tolerated(self, tmp_path) -> None:
        """A concurrent creator winning the mkdir race is tolerated (I03R1 §11)."""
        base = tmp_path / "base"
        base.mkdir()
        # Simulate the race: pre-create the child JUST before the helper's
        # exists() check window by racing against a probe that creates it.
        original_exists = Path.exists

        def racing_exists(self: Path) -> bool:
            result = original_exists(self)
            if self == base / "raced":
                (base / "raced").mkdir()  # concurrent creator wins the race
            return result

        import unittest.mock

        with unittest.mock.patch.object(Path, "exists", racing_exists):
            leaf = ensure_durable_directory_chain(base, ["raced"])
        assert leaf == base / "raced"
        assert leaf.is_dir()

    def test_component_validated_against_existing_parent_limit(
        self, tmp_path
    ) -> None:
        base = tmp_path / "base"
        base.mkdir()

        def tiny_probe(path: Path) -> int:
            assert path == base, "probe must target the EXISTING parent"
            return 8

        with pytest.raises(ComponentTooLong):
            ensure_durable_directory_chain(
                base, ["way-too-long-component"], name_max_probe=tiny_probe
            )
        assert not (base / "way-too-long-component").exists()

    def test_invalid_components_rejected(self, tmp_path) -> None:
        base = tmp_path / "base"
        base.mkdir()
        with pytest.raises(ValueError):
            ensure_durable_directory_chain(base, [])
        with pytest.raises(ValueError):
            ensure_durable_directory_chain(base, [".."])
        with pytest.raises(ValueError):
            ensure_durable_directory_chain(base, ["a/b"])


class TestEnsureDurableDirectory:
    def test_creates_missing_ancestors_from_deepest_existing(
        self, tmp_path
    ) -> None:
        target = tmp_path / "l1" / "l2" / "leaf"
        leaf = ensure_durable_directory(target)
        assert leaf == target
        assert leaf.is_dir()

    def test_existing_directory_returned_unchanged(self, tmp_path) -> None:
        target = tmp_path / "already"
        target.mkdir()
        assert ensure_durable_directory(target) == target

    def test_existing_file_component_fails_closed(self, tmp_path) -> None:
        target = tmp_path / "blocker"
        target.write_bytes(b"not a dir")
        with pytest.raises(AtomicPublishError):
            ensure_durable_directory(target)
        assert target.is_file()

    def test_publish_creates_fanout_durably(self, tmp_path) -> None:
        """Full fresh fanout via publish_no_replace — chain before link (§23)."""
        sp = _staged_file(tmp_path)
        fp = tmp_path / "blobs" / "sha256" / "ab" / "cd" / "obj.blob"
        ops = ListOpRecorder()
        publish_no_replace(sp, fp, ops=ops)
        assert fp.is_file()
        # Directory-chain milestones appear BEFORE the final link.
        assert ops.ops.index(OP_DIR_CREATE) < ops.ops.index(OP_FINAL_LINK)
        assert ops.ops.count(OP_DIR_CREATE) == 4  # blobs, sha256, ab, cd
        assert ops.ops.count(OP_PARENT_NAMESPACE_FSYNC) == 4
        link_idx = ops.ops.index(OP_FINAL_LINK)
        pfs_idx = ops.ops.index(OP_FINAL_PARENT_FSYNC)
        assert link_idx < pfs_idx  # link happens after chain ready


class TestNameMaxProbe:
    def test_probes_real_limit_on_existing_dir(self, tmp_path) -> None:
        limit = default_name_max(tmp_path)
        assert isinstance(limit, int) and limit >= 1

    def test_nonexistent_dir_fails_closed_not_255(self) -> None:
        """A probe of a nonexistent directory can NEVER yield a silent 255."""
        with pytest.raises(DurabilityUnsupported):
            default_name_max(Path("Z:/definitely/not/here/nope"))

    def test_posix_probe_failure_fails_closed(self, tmp_path, monkeypatch) -> None:
        """A failing PC_NAME_MAX query fails closed — never silent 255 (§17)."""
        if not hasattr(os, "pathconf"):
            pytest.skip("platform has no os.pathconf")

        def broken_pathconf(path: object, name: object) -> int:
            raise OSError("injected probe failure")

        monkeypatch.setattr(os, "pathconf", broken_pathconf)
        with pytest.raises(DurabilityUnsupported):
            default_name_max(tmp_path)

    def test_store_component_check_uses_existing_ancestor(self, tmp_path) -> None:
        """The store probes the limit from an existing ancestor, not the
        not-yet-created fanout leaf (I03R1 §16/§18)."""
        probed: list[Path] = []

        def recording_probe(path: Path) -> int:
            probed.append(path)
            assert path.exists(), f"probed nonexistent {path}"
            return 255

        store = make_store(tmp_path, name_max_probe=recording_probe)
        store.put_bytes(
            b"probe ancestor", storage_encoding=StorageEncoding.NONE,
            source_media_type=MEDIA,
        )
        assert probed, "component-limit probe must have run"
        assert all(p.exists() for p in probed)


class TestStagingNonceComponent:
    def test_nonce_component_validated_before_open(self, tmp_path) -> None:
        """A nonce that exceeds the limit fails typed BEFORE open (I03R1 §19)."""
        calls: list[tuple[str, int]] = []
        real_validate = validate_component_length

        def spy(component: str, limit: int) -> str:
            calls.append((component, limit))
            return real_validate(component, limit)

        store = make_store(tmp_path)
        import unittest.mock

        with unittest.mock.patch(
            "crypto_sensor_fabric.storage.blob_store.validate_component_length",
            spy,
        ):
            store.put_bytes(
                b"nonce check", storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA,
            )
        # '<32 hex>.partial' = 40 bytes was validated against a real limit.
        nonce_calls = [c for c in calls if c[0].endswith(".partial")]
        assert nonce_calls, "generated staging nonce must be validated"
        component, limit = nonce_calls[0]
        assert component.endswith(".partial") and len(component) == 40
        assert limit == default_name_max(tmp_path)

    def test_over_limit_staging_filename_fails_typed_before_open(
        self, tmp_path
    ) -> None:
        """An over-limit transient staging filename fails typed pre-open."""

        def tiny_nonce_limit(path: Path) -> int:
            # The staging dir exists at nonce-validation time; the fanout
            # parents do not — report a real limit for existing ancestors.
            return 255 if path.exists() else 255

        store = make_store(
            tmp_path,
            name_max_probe=lambda p: 20 if "staging" in str(p) else 255,
        )
        with pytest.raises(ComponentTooLong):
            store.put_bytes(
                b"x", storage_encoding=StorageEncoding.NONE,
                source_media_type=MEDIA,
            )
        # Nothing was written anywhere: no staging artifact, no blob.
        assert not list((tmp_path / "staging").rglob("*.partial"))
        assert not (tmp_path / "blobs").exists()


class TestNamespaceDurabilityOrder:
    def test_first_write_new_namespace_order(self, tmp_path) -> None:
        """Fresh namespace: durable chain ready < publish < parent fsync < OK."""
        store = make_store(tmp_path)
        ops = ListOpRecorder()
        store.put_bytes(
            b"fresh namespace order", storage_encoding=StorageEncoding.NONE,
            source_media_type=MEDIA, ops=ops,
        )
        assert ops.ops.count(OP_DIR_CREATE) == 4
        assert ops.ops.count(OP_PARENT_NAMESPACE_FSYNC) == 4
        # DURABLE_DIRECTORY_CHAIN_READY < ATOMIC_PUBLISH (I03R1 §23)
        assert ops.ops.index(OP_PARENT_NAMESPACE_FSYNC) < ops.ops.index(
            "atomic_publish"
        )
        # FINAL_LINK < FINAL_PARENT_FSYNC < SUCCESS (§15/§23)
        assert ops.ops.index(OP_FINAL_LINK) < ops.ops.index(
            OP_FINAL_PARENT_FSYNC
        )
        assert ops.ops[-1] == "success_return"
        # The canonical I03 durable order is still intact.
        assert is_canonical_durable_order(ops.ops)

    def test_existing_namespace_no_dir_creation(self, tmp_path) -> None:
        """All required dirs pre-exist: no dir creation, parent fsync remains."""
        import hashlib

        store = make_store(tmp_path)
        first = store.put_bytes(
            b"warm the namespace", storage_encoding=StorageEncoding.NONE,
            source_media_type=MEDIA,
        )
        assert first.disposition is PutDisposition.COMMITTED_NEW
        # Pre-create the FULL fanout for a second known blob: the §24
        # existing-namespace case.
        data2 = b"second distinct blob"
        sha2 = hashlib.sha256(data2).hexdigest()
        (tmp_path / "blobs" / "sha256" / sha2[:2] / sha2[2:4]).mkdir(
            parents=True
        )
        ops = ListOpRecorder()
        result = store.put_bytes(
            data2, storage_encoding=StorageEncoding.NONE,
            source_media_type=MEDIA, ops=ops,
        )
        assert result.disposition is PutDisposition.COMMITTED_NEW
        assert ops.ops.count(OP_DIR_CREATE) == 0
        assert ops.ops.count(OP_DIR_FSYNC) == 0
        assert "final_parent_fsync" in ops.ops
        assert ops.ops[-1] == "success_return"

    def test_second_blob_same_fanout_no_creation(self, tmp_path) -> None:
        store = make_store(tmp_path)
        data = b"same fanout twice"
        store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        ops = ListOpRecorder()
        result = store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE,
            source_media_type=MEDIA, ops=ops,
        )
        assert result.disposition is PutDisposition.REUSED_EXISTING
        assert ops.ops.count(OP_DIR_CREATE) == 0
