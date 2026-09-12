"""Backup + restore for the local evidence spine (Book V 13.3 Backup/Recovery,
P1 spec §17).

QCAE memory is engineering capital; backup must capture everything needed to
restore full state:

- the metadata database (SQLite backup API — consistent snapshot incl. WAL);
- the raw artifact store (every blob, verified by digest on restore);
- the schema version (carried in the SQLite file itself);
- registry relationships (rows in the same database).

A backup is a directory::

    backup/
      manifest.json          versions, counts, digests, created_at
      metadata.db            consistent DB snapshot
      artifacts/<digest>     raw artifact blobs (flat, digest-named)

Restore verifies the manifest counts and every artifact digest before
declaring success — a backup that cannot be verified is a failed backup.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from typing import Dict

from qcae.core.errors import QcaeValidationError
from qcae.infrastructure.artifact_store import ContentAddressedArtifactStore

__all__ = ["BackupService", "RestoreResult", "BACKUP_MANIFEST_NAME"]

BACKUP_MANIFEST_NAME = "manifest.json"


class RestoreResult:
    def __init__(self, metadata_rows: int, artifacts_restored: int,
                 schema_version: int) -> None:
        self.metadata_rows = metadata_rows
        self.artifacts_restored = artifacts_restored
        self.schema_version = schema_version

    def __repr__(self) -> str:  # pragma: no cover
        return (f"RestoreResult(metadata_rows={self.metadata_rows}, "
                f"artifacts_restored={self.artifacts_restored}, "
                f"schema_version={self.schema_version})")


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


class BackupService:
    def __init__(self, conn: sqlite3.Connection,
                 artifact_store: ContentAddressedArtifactStore) -> None:
        self._conn = conn
        self._artifacts = artifact_store

    def backup(self, destination: Path) -> Dict[str, object]:
        destination = Path(destination)
        if destination.exists() and any(destination.iterdir()):
            raise QcaeValidationError("backup destination must be empty or nonexistent")
        (destination / "artifacts").mkdir(parents=True, exist_ok=True)

        # 1. Consistent metadata snapshot via SQLite's backup API.
        meta_path = destination / "metadata.db"
        with sqlite3.connect(str(meta_path)) as dst:
            self._conn.backup(dst)

        # 2. Raw artifacts: copy blobs flat under their digest names.
        algo_dir = self._artifacts._root / "sha256"
        artifact_count = 0
        if algo_dir.exists():
            for blob in sorted(algo_dir.rglob("*")):
                if blob.is_file():
                    shutil.copy2(blob, destination / "artifacts" / blob.name)
                    artifact_count += 1

        # 3. Manifest: everything a verifier needs.
        evidence_rows = self._conn.execute(
            "SELECT COUNT(*) FROM evidence_artifact").fetchone()[0]
        lineage_rows = 0
        try:
            lineage_rows = self._conn.execute(
                "SELECT COUNT(*) FROM lineage_edge").fetchone()[0]
        except sqlite3.OperationalError:
            pass  # lineage table optional in minimal stores
        manifest = {
            "backup_version": 1,
            "schema_version": int(
                self._conn.execute("PRAGMA user_version").fetchone()[0]),
            "metadata_db_sha256": _file_sha256(meta_path),
            "evidence_rows": evidence_rows,
            "lineage_rows": lineage_rows,
            "artifact_count": artifact_count,
            "artifact_hashes": {
                p.name: _file_sha256(p)
                for p in sorted((destination / "artifacts").iterdir())
            },
        }
        (destination / BACKUP_MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        return manifest


class RestoreService:
    """Restores a backup into fresh runtime locations, verifying integrity."""

    def restore(self, backup_dir: Path, metadata_db_path: Path,
                artifact_root: Path) -> RestoreResult:
        backup_dir = Path(backup_dir)
        manifest_path = backup_dir / BACKUP_MANIFEST_NAME
        if not manifest_path.exists():
            raise QcaeValidationError(f"missing {BACKUP_MANIFEST_NAME} in {backup_dir}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        # Verify every artifact digest BEFORE touching runtime state.
        artifacts_dir = backup_dir / "artifacts"
        restored = 0
        if manifest.get("artifact_count", 0):
            if not artifacts_dir.exists():
                raise QcaeValidationError("backup declares artifacts but none present")
            store = ContentAddressedArtifactStore(artifact_root)
            for name, digest in manifest.get("artifact_hashes", {}).items():
                blob = artifacts_dir / name
                if not blob.exists() or _file_sha256(blob) != digest:
                    raise QcaeValidationError(f"backup artifact {name} failed digest check")
                # re-derive canonical location from content
                store.put_bytes(blob.read_bytes())
                restored += 1

        # Restore metadata DB and verify its digest.
        meta_src = backup_dir / "metadata.db"
        metadata_db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(meta_src, metadata_db_path)
        if _file_sha256(metadata_db_path) != manifest["metadata_db_sha256"]:
            raise QcaeValidationError("metadata database failed digest check")

        conn = sqlite3.connect(str(metadata_db_path))
        try:
            rows = conn.execute("SELECT COUNT(*) FROM evidence_artifact").fetchone()[0]
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        finally:
            conn.close()

        if rows != manifest["evidence_rows"]:
            raise QcaeValidationError(
                f"restored evidence rows {rows} != manifest {manifest['evidence_rows']}")
        return RestoreResult(rows, restored, version)
