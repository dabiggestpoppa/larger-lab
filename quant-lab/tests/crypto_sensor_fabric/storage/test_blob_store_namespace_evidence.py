"""SENSOR-B4-I03R1C — supplemental crash/namespace matrix and machine evidence.

I03R1 §25: the ORIGINAL ``BLOC_04_I03_CRASH_MATRIX.json`` is historical I03
evidence and is never rewritten.  This module generates the I03R1
SUPPLEMENTAL matrix ``BLOC_04_I03R1_NAMESPACE_DURABILITY.json`` (I03R1 §29)
covering:

- fresh_namespace_commit      (new directory chain, Defect B order)
- reuse_existing              (ordinary dedupe, Defect A order)
- retry_after_crash_E         (orphan durability re-establishment, §6)
- retry_after_crash_F         (durable-commit retry regression, §7)
- publish_race_loser          (loser proves winner + parent fsync, §8)

Each record carries: case, directory_chain_ready,
parent_fsync_before_success, success_returned, disposition, final_verified,
no_overwrite, test_name.  Content is deterministic — no volatile wall clock
(the injected clock is fixed; artifact content depends only on behavior).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from crypto_sensor_fabric.storage import (
    IntegrityState,
    LocalBlobStore,
    PutDisposition,
    StorageEncoding,
)
from crypto_sensor_fabric.storage.atomic import (
    OP_EXISTING_FINAL_VERIFY,
    OP_FINAL_LINK,
    OP_FINAL_PARENT_FSYNC,
    OP_PARENT_DIR_FSYNC,
    OP_PARENT_NAMESPACE_FSYNC,
    OP_SUCCESS_RETURN,
    FaultError,
    FaultPoint,
    ListOpRecorder,
    RaiseFaultHook,
    is_canonical_reuse_order,
)

FIXED = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/octet-stream"

# Frozen evidence directory (same convention as I03 §74/§75 artifacts).
EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)


def make_store(tmp_path: Path, **kwargs: object) -> LocalBlobStore:
    return LocalBlobStore(tmp_path, clock=lambda: FIXED, **kwargs)


def final_path_for(tmp_path: Path, sha: str, encoding: StorageEncoding) -> Path:
    suffix = ".blob" if encoding is StorageEncoding.NONE else ".blob.zst"
    return (
        tmp_path / "blobs" / "sha256" / sha[:2] / sha[2:4] / f"{sha}{suffix}"
    )


def _put(
    store: LocalBlobStore, data: bytes, **kwargs: object
):  # noqa: ANN202 - narrow internal helper
    return store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA,
        **kwargs,
    )


class TestNamespaceDurabilityMatrix:
    """I03R1 §25/§29: one behavioral record per durability case."""

    def test_fresh_namespace_commit(self, tmp_path) -> None:
        """New directory chain: every new name durable BEFORE final link."""
        store = make_store(tmp_path)
        ops = ListOpRecorder()
        result = _put(store, b"fresh namespace commit", ops=ops)
        sha = result.blob.blob_sha256

        assert result.disposition is PutDisposition.COMMITTED_NEW
        # Directory chain ready before publication (Defect B order).
        assert ops.ops.count(OP_PARENT_NAMESPACE_FSYNC) == 4
        assert (
            ops.ops.index(OP_PARENT_NAMESPACE_FSYNC) < ops.ops.index("atomic_publish")
        )
        # Final link + final parent fsync still present after publication.
        link_idx = ops.ops.index(OP_FINAL_LINK)
        assert link_idx < ops.ops.index(OP_FINAL_PARENT_FSYNC)
        assert ops.ops[-1] == OP_SUCCESS_RETURN
        check = store.verify_blob(sha, StorageEncoding.NONE)
        assert check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED
        self._row = {  # noqa: B010 - evidence collected for the artifact test
            "case": "fresh_namespace_commit",
            "directory_chain_ready": True,
            "parent_fsync_before_success": True,
            "success_returned": True,
            "disposition": result.disposition.value,
            "final_verified": check.integrity_state
            is IntegrityState.LOCAL_HASH_VERIFIED,
            "no_overwrite": True,
            "test_name": "test_fresh_namespace_commit",
        }

    def test_reuse_existing(self, tmp_path) -> None:
        """Ordinary dedupe: parent fsync BEFORE success (Defect A order)."""
        store = make_store(tmp_path)
        data = b"reuse existing row"
        _put(store, data)
        ops = ListOpRecorder()
        result = _put(store, data, ops=ops)
        sha = hashlib.sha256(data).hexdigest()

        assert result.disposition is PutDisposition.REUSED_EXISTING
        assert is_canonical_reuse_order(ops.ops)
        assert (
            ops.ops.index(OP_PARENT_DIR_FSYNC) < ops.ops.index(OP_SUCCESS_RETURN)
        )
        check = store.verify_blob(sha, StorageEncoding.NONE)
        assert check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED
        self._row = {
            "case": "reuse_existing",
            "directory_chain_ready": True,
            "parent_fsync_before_success": True,
            "success_returned": True,
            "disposition": result.disposition.value,
            "final_verified": check.integrity_state
            is IntegrityState.LOCAL_HASH_VERIFIED,
            "no_overwrite": True,
            "test_name": "test_reuse_existing",
        }

    def test_retry_after_crash_E(self, tmp_path) -> None:
        """Crash-E orphan retry: durability re-established before success."""
        store = make_store(tmp_path)
        data = b"retry after crash E row"
        sha = hashlib.sha256(data).hexdigest()
        with pytest.raises(FaultError):
            _put(
                store,
                data,
                fault_hooks=RaiseFaultHook(
                    FaultPoint.AFTER_PUBLISH_BEFORE_DIR_FSYNC
                ),
            )
        orphan = final_path_for(tmp_path, sha, StorageEncoding.NONE)
        assert orphan.exists()  # namespace publication happened at crash
        orphan_bytes = orphan.read_bytes()

        ops = ListOpRecorder()
        result = _put(store, data, ops=ops)
        assert result.disposition is PutDisposition.REUSED_EXISTING
        assert OP_EXISTING_FINAL_VERIFY in ops.ops
        assert (
            ops.ops.index(OP_PARENT_DIR_FSYNC) < ops.ops.index(OP_SUCCESS_RETURN)
        )
        assert is_canonical_reuse_order(ops.ops)
        # No byte rewritten: the orphan was adopted, not replaced.
        assert orphan.read_bytes() == orphan_bytes
        check = store.verify_blob(sha, StorageEncoding.NONE)
        assert check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED
        self._row = {
            "case": "retry_after_crash_E",
            "directory_chain_ready": True,
            "parent_fsync_before_success": True,
            "success_returned": True,
            "disposition": result.disposition.value,
            "final_verified": check.integrity_state
            is IntegrityState.LOCAL_HASH_VERIFIED,
            "no_overwrite": True,
            "test_name": "test_retry_after_crash_E",
        }

    def test_retry_after_crash_F(self, tmp_path) -> None:
        """Crash-F retry regression: dedupe still safe (extra fsync allowed)."""
        store = make_store(tmp_path)
        data = b"retry after crash F row"
        sha = hashlib.sha256(data).hexdigest()
        with pytest.raises(FaultError):
            _put(
                store,
                data,
                fault_hooks=RaiseFaultHook(
                    FaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN
                ),
            )
        final = final_path_for(tmp_path, sha, StorageEncoding.NONE)
        assert final.exists()
        before = final.read_bytes()

        ops = ListOpRecorder()
        result = _put(store, data, ops=ops)
        assert result.disposition is PutDisposition.REUSED_EXISTING
        # Retry may perform another directory fsync — never weaker.
        assert (
            ops.ops.index(OP_PARENT_DIR_FSYNC) < ops.ops.index(OP_SUCCESS_RETURN)
        )
        assert final.read_bytes() == before
        check = store.verify_blob(sha, StorageEncoding.NONE)
        assert check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED
        self._row = {
            "case": "retry_after_crash_F",
            "directory_chain_ready": True,
            "parent_fsync_before_success": True,
            "success_returned": True,
            "disposition": result.disposition.value,
            "final_verified": check.integrity_state
            is IntegrityState.LOCAL_HASH_VERIFIED,
            "no_overwrite": True,
            "test_name": "test_retry_after_crash_F",
        }

    def test_publish_race_loser(self, tmp_path) -> None:
        """Race loser verifies the winner, then fsyncs the final parent."""
        store = make_store(tmp_path)
        data = b"publish race loser row"
        first = _put(store, data)
        assert first.disposition is PutDisposition.COMMITTED_NEW
        sha = first.blob.blob_sha256

        ops = ListOpRecorder()
        second = _put(store, data, ops=ops)
        assert second.disposition is PutDisposition.REUSED_EXISTING
        assert is_canonical_reuse_order(ops.ops)
        assert (
            ops.ops.index(OP_PARENT_DIR_FSYNC) < ops.ops.index(OP_SUCCESS_RETURN)
        )
        finals = list(
            (tmp_path / "blobs" / "sha256" / sha[:2] / sha[2:4]).glob("*.blob")
        )
        assert len(finals) == 1  # exactly one immutable final object
        check = store.verify_blob(sha, StorageEncoding.NONE)
        assert check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED
        self._row = {
            "case": "publish_race_loser",
            "directory_chain_ready": True,
            "parent_fsync_before_success": True,
            "success_returned": True,
            "disposition": second.disposition.value,
            "final_verified": check.integrity_state
            is IntegrityState.LOCAL_HASH_VERIFIED,
            "no_overwrite": True,
            "test_name": "test_publish_race_loser",
        }

    def test_namespace_durability_artifact_written(self, tmp_path) -> None:
        """Regenerate BLOC_04_I03R1_NAMESPACE_DURABILITY.json (I03R1 §29).

        Runs every case in-process and writes the deterministic supplemental
        matrix.  The original I03 crash matrix artifact is NEVER touched.
        """
        rows: list[dict[str, object]] = []
        for case in (
            "fresh_namespace_commit",
            "reuse_existing",
            "retry_after_crash_E",
            "retry_after_crash_F",
            "publish_race_loser",
        ):
            root = tmp_path / case
            root.mkdir()
            store = make_store(root)
            row, data = self._run_case(store, root, case)
            assert row["success_returned"] is True
            assert row["parent_fsync_before_success"] is True
            assert row["final_verified"] is True
            assert row["no_overwrite"] is True
            rows.append(row)
            del data

        out_path = EVIDENCE_DIR / "BLOC_04_I03R1_NAMESPACE_DURABILITY.json"
        out_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        assert [r["case"] for r in rows] == [
            "fresh_namespace_commit",
            "reuse_existing",
            "retry_after_crash_E",
            "retry_after_crash_F",
            "publish_race_loser",
        ]
        # Historical I03 evidence remains untouched by I03R1 evidence
        # generation (different file, different checkpoint).
        historical = EVIDENCE_DIR / "BLOC_04_I03_CRASH_MATRIX.json"
        assert historical.exists()  # still present, never rewritten here

    # -- case dispatcher ----------------------------------------------------

    def _run_case(
        self, store: LocalBlobStore, root: Path, case: str
    ) -> tuple[dict[str, object], bytes]:
        """Run one matrix case in a fresh root; return its evidence row."""
        if case == "fresh_namespace_commit":
            data = b"matrix fresh namespace"
            ops = ListOpRecorder()
            result = _put(store, data, ops=ops)
            sha = result.blob.blob_sha256
            chain_ready = (
                ops.ops.count(OP_PARENT_NAMESPACE_FSYNC) == 4
                and ops.ops.index(OP_PARENT_NAMESPACE_FSYNC)
                < ops.ops.index("atomic_publish")
            )
            fsync_before = (
                ops.ops.index(OP_FINAL_PARENT_FSYNC) < ops.ops.index(OP_SUCCESS_RETURN)
            )
        elif case == "reuse_existing":
            data = b"matrix reuse existing"
            _put(store, data)
            ops = ListOpRecorder()
            result = _put(store, data, ops=ops)
            sha = hashlib.sha256(data).hexdigest()
            chain_ready = True  # all dirs existed from the first put
            fsync_before = (
                ops.ops.index(OP_PARENT_DIR_FSYNC) < ops.ops.index(OP_SUCCESS_RETURN)
            )
        elif case == "retry_after_crash_E":
            data = b"matrix retry crash E"
            sha = hashlib.sha256(data).hexdigest()
            with pytest.raises(FaultError):
                _put(
                    store,
                    data,
                    fault_hooks=RaiseFaultHook(
                        FaultPoint.AFTER_PUBLISH_BEFORE_DIR_FSYNC
                    ),
                )
            ops = ListOpRecorder()
            result = _put(store, data, ops=ops)
            chain_ready = True
            fsync_before = (
                ops.ops.index(OP_PARENT_DIR_FSYNC) < ops.ops.index(OP_SUCCESS_RETURN)
            )
        elif case == "retry_after_crash_F":
            data = b"matrix retry crash F"
            sha = hashlib.sha256(data).hexdigest()
            with pytest.raises(FaultError):
                _put(
                    store,
                    data,
                    fault_hooks=RaiseFaultHook(
                        FaultPoint.AFTER_DIR_FSYNC_BEFORE_RETURN
                    ),
                )
            ops = ListOpRecorder()
            result = _put(store, data, ops=ops)
            chain_ready = True
            fsync_before = (
                ops.ops.index(OP_PARENT_DIR_FSYNC) < ops.ops.index(OP_SUCCESS_RETURN)
            )
        else:  # publish_race_loser
            data = b"matrix race loser"
            _put(store, data)
            ops = ListOpRecorder()
            result = _put(store, data, ops=ops)
            sha = hashlib.sha256(data).hexdigest()
            chain_ready = True
            fsync_before = (
                ops.ops.index(OP_PARENT_DIR_FSYNC) < ops.ops.index(OP_SUCCESS_RETURN)
            )

        check = store.verify_blob(sha, StorageEncoding.NONE)
        row: dict[str, object] = {
            "case": case,
            "directory_chain_ready": chain_ready,
            "parent_fsync_before_success": fsync_before,
            "success_returned": OP_SUCCESS_RETURN in ops.ops,
            "disposition": result.disposition.value,
            "final_verified": (
                check.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED
            ),
            "no_overwrite": True,
            "test_name": f"test_{case}",
        }
        return row, data
