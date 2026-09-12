"""P1-C11 — backup/restore exactness evidence (P1 spec §17, test 35)."""

from __future__ import annotations

import sqlite3

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.ports.lineage import LineageEdge, LineageEdgeType
from qcae.infrastructure.artifact_store import (
    ArtifactCorruptionError,
    ContentAddressedArtifactStore,
)
from qcae.infrastructure.persistence.backup_restore import BackupService, RestoreService
from qcae.infrastructure.persistence.sqlite_lineage_store import (
    SqliteLineageRepository,
    LINEAGE_DDL,
)
from qcae.infrastructure.persistence.sqlite_metadata_store import SqliteEvidenceRepository
from qcae.infrastructure.persistence.store_factory import open_metadata_db

from qcae.tests.unit.test_p1_sqlite_store import _artifact


def _build_state(tmp_path):
    """Full runtime state: metadata + lineage + raw artifacts."""
    root = tmp_path / "runtime"
    conn = open_metadata_db(root / "meta.db")
    conn.executescript(LINEAGE_DDL)
    store = ContentAddressedArtifactStore(root / "artifacts")
    evidence = SqliteEvidenceRepository(conn)
    lineage = SqliteLineageRepository(conn)

    raw = b"raw evidence bytes: benchmark log"
    digest = store.put_bytes(raw)
    evidence.add(_artifact("ev-1", artifact_digest=digest))
    evidence.add(_artifact("ev-2"))
    lineage.add(LineageEdge(
        src_id="ev-1", src_kind="evidence", edge_type=LineageEdgeType.SUPERSEDES,
        dst_id="ev-2", dst_kind="evidence", created_at="t0"))
    conn.commit()
    return conn, store, digest


class TestBackupRestore:
    def test_full_cycle_exactness(self, tmp_path) -> None:
        """create state -> backup -> destroy -> restore -> verify everything."""
        conn, store, digest = _build_state(tmp_path)

        backup_dir = tmp_path / "backup"
        BackupService(conn, store).backup(backup_dir)
        conn.close()

        # destroy runtime state entirely
        import shutil

        shutil.rmtree(tmp_path / "runtime")

        # restore into fresh locations
        new_conn = RestoreService().restore(
            backup_dir, tmp_path / "restored" / "meta.db",
            tmp_path / "restored" / "artifacts")

        rconn = open_metadata_db(tmp_path / "restored" / "meta.db")
        revidence = SqliteEvidenceRepository(rconn)
        rstore = ContentAddressedArtifactStore(tmp_path / "restored" / "artifacts")

        # IDs survive
        assert revidence.get("ev-1") is not None
        assert revidence.get("ev-2") is not None
        # digests survive and artifact bytes verify
        assert rstore.verify(digest)
        assert rstore.get_bytes(digest) == b"raw evidence bytes: benchmark log"
        # relationships survive
        rlineage = SqliteLineageRepository(rconn)
        supers = rlineage.supersession_chain("ev-1")
        assert len(supers) == 1 and supers[0].edge_type is LineageEdgeType.SUPERSEDES
        # schema version survives
        assert new_conn.schema_version == 1
        rconn.close()

    def test_restore_verifies_every_artifact_digest(self, tmp_path) -> None:
        conn, store, _ = _build_state(tmp_path)
        backup_dir = tmp_path / "backup"
        BackupService(conn, store).backup(backup_dir)
        conn.close()

        # corrupt one artifact inside the backup
        blobs = list((backup_dir / "artifacts").iterdir())
        blobs[0].write_bytes(b"corrupted in transit")

        with pytest.raises(QcaeValidationError, match="failed digest check"):
            RestoreService().restore(
                backup_dir, tmp_path / "r" / "meta.db", tmp_path / "r" / "artifacts")

    def test_restore_rejects_missing_manifest(self, tmp_path) -> None:
        conn, store, _ = _build_state(tmp_path)
        backup_dir = tmp_path / "backup-no-manifest"
        backup_dir.mkdir()
        BackupService(conn, store)  # noqa: we only need the dir to lack a manifest
        conn.close()
        with pytest.raises(QcaeValidationError, match="manifest"):
            RestoreService().restore(
                backup_dir, tmp_path / "r" / "meta.db", tmp_path / "r" / "artifacts")

    def test_backup_refuses_nonempty_destination(self, tmp_path) -> None:
        conn, store, _ = _build_state(tmp_path)
        dest = tmp_path / "backup"
        dest.mkdir()
        (dest / "stale-file").write_text("x")
        with pytest.raises(QcaeValidationError, match="empty or nonexistent"):
            BackupService(conn, store).backup(dest)
        conn.close()

    def test_restored_store_detects_future_corruption(self, tmp_path) -> None:
        """After restore, integrity checking still guards the store."""
        conn, store, digest = _build_state(tmp_path)
        backup_dir = tmp_path / "backup"
        BackupService(conn, store).backup(backup_dir)
        conn.close()
        import shutil

        shutil.rmtree(tmp_path / "runtime")
        RestoreService().restore(
            backup_dir, tmp_path / "restored" / "meta.db",
            tmp_path / "restored" / "artifacts")
        rstore = ContentAddressedArtifactStore(tmp_path / "restored" / "artifacts")
        blob = rstore._path_for(digest)
        blob.write_bytes(b"post-restore tampering")
        with pytest.raises(ArtifactCorruptionError):
            rstore.get_bytes(digest)
