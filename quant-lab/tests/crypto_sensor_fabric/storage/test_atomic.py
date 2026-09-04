"""SENSOR-B4-I03 — generic no-clobber atomic durability primitive tests.

Proves: component-length fail-closed behavior (255-byte limit respected,
over-limit rejected BEFORE artifact write); same-filesystem enforcement via
injectable device probe (cross-device commit DENIED, no copy fallback);
no-clobber hard-link publication (never overwrites, reader never sees a
partial final); parent-directory fsync presence; canonical durable-operation
order contract; fault points E/F leave truthful crash state.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from crypto_sensor_fabric.storage.atomic import (
    OP_ATOMIC_PUBLISH,
    OP_DEVICE_CHECK,
    OP_EXISTING_FINAL_VERIFY,
    OP_FINAL_LINK,
    OP_FINAL_PARENT_FSYNC,
    OP_FILE_FLUSH,
    OP_FILE_FSYNC,
    OP_PARENT_DIR_FSYNC,
    OP_STAGE_VERIFY,
    OP_STAGE_WRITE,
    OP_STAGING_CLEANUP,
    OP_SUCCESS_RETURN,
    AtomicPublishError,
    AtomicPublishTargetExists,
    ComponentTooLong,
    CrossFilesystemAtomicityError,
    DurabilityUnsupported,
    FaultError,
    FaultPoint,
    ListOpRecorder,
    RaiseFaultHook,
    default_name_max,
    ensure_same_device,
    fsync_directory,
    fsync_file,
    is_canonical_durable_order,
    is_canonical_reuse_order,
    publish_no_replace,
    validate_component_length,
)


def _staged_final_fixture(tmp_path: Path) -> tuple[Path, Path]:
    staging_dir = tmp_path / "staging"
    final_dir = tmp_path / "blobs" / "sha256" / "ab" / "cd"
    staging_dir.mkdir(parents=True)
    final_dir.mkdir(parents=True)
    sp = staging_dir / "obj.partial"
    fp = final_dir / "obj.blob"
    with open(sp, "wb") as fh:
        fh.write(b"fully written staged bytes")
        fh.flush()
        os.fsync(fh.fileno())
    return sp, fp


class TestComponentLength:
    def test_safe_ordinary_component_accepted(self) -> None:
        assert validate_component_length("blobs", 255) == "blobs"
        assert validate_component_length("sha256", 255) == "sha256"
        assert validate_component_length("ab", 255) == "ab"

    def test_max_component_accepted_per_filesystem_limit(self, tmp_path) -> None:
        limit = default_name_max(tmp_path)
        name = "a" * limit
        assert validate_component_length(name, limit) == name

    def test_over_limit_rejected(self) -> None:
        with pytest.raises(ComponentTooLong):
            validate_component_length("a" * 256, 255)

    def test_over_limit_rejected_before_any_write(self, tmp_path) -> None:
        target = tmp_path
        limit = default_name_max(target)
        with pytest.raises(ComponentTooLong):
            validate_component_length("a" * (limit + 1), limit)
        assert not any(target.iterdir())

    def test_bad_arguments_rejected(self) -> None:
        with pytest.raises(TypeError):
            validate_component_length(b"blobs", 255)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            validate_component_length("blobs", 0)
        with pytest.raises(ValueError):
            validate_component_length("blobs", -1)

    def test_default_name_max_is_positive(self, tmp_path) -> None:
        assert isinstance(default_name_max(tmp_path), int)
        assert default_name_max(tmp_path) >= 255


class TestSameFilesystem:
    def test_same_device_accepted(self, tmp_path) -> None:
        ensure_same_device(tmp_path, tmp_path)

    def test_cross_device_denied(self, tmp_path) -> None:
        def probe(path: Path) -> int:
            return 1 if path == tmp_path / "other" else 2

        with pytest.raises(CrossFilesystemAtomicityError):
            ensure_same_device(tmp_path, tmp_path / "other", device_probe=probe)

    def test_publish_rejects_cross_device_before_link(self, tmp_path) -> None:
        sp, fp = _staged_final_fixture(tmp_path)
        staging_dir = sp.parent

        def probe(path: Path) -> int:
            return 1 if path == staging_dir else 2

        with pytest.raises(CrossFilesystemAtomicityError):
            publish_no_replace(sp, fp, device_probe=probe)
        # No copy+delete fallback: final must NOT exist.
        assert not fp.exists()
        assert sp.exists()  # staging preserved


class TestPublishNoReplace:
    def test_success_publishes_and_cleans_staging(self, tmp_path) -> None:
        sp, fp = _staged_final_fixture(tmp_path)
        publish_no_replace(sp, fp)
        assert fp.exists()
        assert fp.read_bytes() == b"fully written staged bytes"
        assert not sp.exists()

    def test_never_overwrites_existing(self, tmp_path) -> None:
        sp, fp = _staged_final_fixture(tmp_path)
        fp.write_bytes(b"ORIGINAL COMMITTED CONTENT")
        before = fp.read_bytes()
        with pytest.raises(AtomicPublishTargetExists):
            publish_no_replace(sp, fp)
        assert fp.read_bytes() == before
        assert sp.exists()  # staging not consumed

    def test_missing_staging_rejected(self, tmp_path) -> None:
        sp, fp = _staged_final_fixture(tmp_path)
        sp.unlink()
        with pytest.raises(AtomicPublishError):
            publish_no_replace(sp, fp)

    def test_fault_e_leaves_final_and_staging(self, tmp_path) -> None:
        sp, fp = _staged_final_fixture(tmp_path)
        hooks = RaiseFaultHook(FaultPoint.AFTER_PUBLISH_BEFORE_DIR_FSYNC)
        with pytest.raises(FaultError):
            publish_no_replace(sp, fp, fault_hooks=hooks)
        # Namespace publication happened; parent fsync did NOT.
        assert fp.exists()
        assert sp.exists()

    def test_fault_f_leaves_durable_final_and_staging(self, tmp_path) -> None:
        sp, fp = _staged_final_fixture(tmp_path)
        hooks = RaiseFaultHook(FaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN)
        with pytest.raises(FaultError):
            publish_no_replace(sp, fp, fault_hooks=hooks)
        assert fp.exists()
        assert sp.exists()

    def test_multiple_publications_never_clobber(self, tmp_path) -> None:
        sp, fp = _staged_final_fixture(tmp_path)
        publish_no_replace(sp, fp)
        sp2 = tmp_path / "staging" / "second.partial"
        with open(sp2, "wb") as fh:
            fh.write(b"second")
            fh.flush()
            os.fsync(fh.fileno())
        with pytest.raises(AtomicPublishTargetExists):
            publish_no_replace(sp2, fp)


class TestFsyncHelpers:
    def test_fsync_directory_works_on_platform(self, tmp_path) -> None:
        dir_path = tmp_path / "blobs" / "sha256" / "ab"
        dir_path.mkdir(parents=True)
        # Either the platform proves directory fsync, or it reports a
        # truthful unsupported condition — a claim is never fabricated.
        try:
            fsync_directory(dir_path)
        except DurabilityUnsupported:
            pytest.skip("platform cannot fsync directories")

    def test_fsync_file_works(self, tmp_path) -> None:
        p = tmp_path / "x"
        with open(p, "wb") as fh:
            fh.write(b"x")
        fsync_file(p)
        assert p.read_bytes() == b"x"


class TestOperationOrder:
    def test_canonical_order_accepted(self) -> None:
        ops = [
            OP_STAGE_WRITE,
            OP_DEVICE_CHECK,
            OP_FILE_FLUSH,
            OP_FILE_FSYNC,
            OP_STAGE_VERIFY,
            OP_ATOMIC_PUBLISH,
            OP_PARENT_DIR_FSYNC,
            OP_SUCCESS_RETURN,
        ]
        assert is_canonical_durable_order(ops)

    def test_missing_element_rejected(self) -> None:
        assert not is_canonical_durable_order([OP_STAGE_WRITE, OP_FILE_FLUSH])

    def test_reordered_rejected(self) -> None:
        ops = [
            OP_STAGE_WRITE,
            OP_FILE_FSYNC,
            OP_FILE_FLUSH,
            OP_STAGE_VERIFY,
            OP_ATOMIC_PUBLISH,
            OP_PARENT_DIR_FSYNC,
            OP_SUCCESS_RETURN,
        ]
        assert not is_canonical_durable_order(ops)

    def test_success_before_parent_fsync_rejected(self) -> None:
        ops = [
            OP_STAGE_WRITE,
            OP_FILE_FLUSH,
            OP_FILE_FSYNC,
            OP_STAGE_VERIFY,
            OP_ATOMIC_PUBLISH,
            OP_SUCCESS_RETURN,
            OP_PARENT_DIR_FSYNC,
        ]
        assert not is_canonical_durable_order(ops)

    def test_recorder_keeps_strict_order(self, tmp_path) -> None:
        record = ListOpRecorder()
        sp, fp = _staged_final_fixture(tmp_path)
        publish_no_replace(sp, fp, ops=record)
        # I03R1: the final parent already exists here, so no directory-chain
        # milestones appear; publication still emits the explicit link and
        # final-parent-fsync milestones (I03R1 §22).
        assert record.ops == [
            OP_DEVICE_CHECK,
            OP_ATOMIC_PUBLISH,
            OP_FINAL_LINK,
            OP_PARENT_DIR_FSYNC,
            OP_FINAL_PARENT_FSYNC,
            OP_STAGING_CLEANUP,
        ]


class TestReuseOrder:
    """SENSOR-B4-I03R1 §5: frozen REUSED_EXISTING durability order contract."""

    def test_full_reuse_order_accepted(self) -> None:
        ops = [
            OP_STAGE_WRITE,
            OP_FILE_FLUSH,
            OP_FILE_FSYNC,
            OP_STAGE_VERIFY,
            OP_EXISTING_FINAL_VERIFY,
            OP_PARENT_DIR_FSYNC,
            OP_STAGING_CLEANUP,
            OP_SUCCESS_RETURN,
        ]
        assert is_canonical_reuse_order(ops)

    def test_reuse_without_parent_fsync_rejected(self) -> None:
        """A reuse result without parent-directory fsync is a FAIL (I03R1 §5)."""
        ops = [
            OP_STAGE_WRITE,
            OP_FILE_FLUSH,
            OP_FILE_FSYNC,
            OP_STAGE_VERIFY,
            OP_EXISTING_FINAL_VERIFY,
            OP_STAGING_CLEANUP,
            OP_SUCCESS_RETURN,
        ]
        assert not is_canonical_reuse_order(ops)

    def test_reuse_success_before_fsync_rejected(self) -> None:
        ops = [
            OP_STAGE_WRITE,
            OP_FILE_FLUSH,
            OP_FILE_FSYNC,
            OP_STAGE_VERIFY,
            OP_EXISTING_FINAL_VERIFY,
            OP_SUCCESS_RETURN,
            OP_PARENT_DIR_FSYNC,
            OP_STAGING_CLEANUP,
        ]
        assert not is_canonical_reuse_order(ops)

    def test_reuse_missing_existing_verify_rejected(self) -> None:
        ops = [
            OP_STAGE_WRITE,
            OP_FILE_FLUSH,
            OP_FILE_FSYNC,
            OP_STAGE_VERIFY,
            OP_PARENT_DIR_FSYNC,
            OP_STAGING_CLEANUP,
            OP_SUCCESS_RETURN,
        ]
        assert not is_canonical_reuse_order(ops)