#!/usr/bin/env python3
"""OCE Local Ground — backup/restore fail-closed hardening regressions
(B1-LOCAL, A-003; R18/R19).

Rejects missing / absolute / parent-traversal / malformed / duplicate manifest
paths; requires the backup metadata to be hash-protected inside the manifest;
rejects unsafe artefact tar members. These run anywhere (no Docker): restore.sh
must fail fast on integrity problems before touching any data.
"""
import json
import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = BASE_DIR / "scripts"
_BASH = shutil.which("bash") or "bash"


def _make_backup(tmp, payload='{"clean": "1"}'):
    """Build a minimal valid backup dir: manifest + content + protected meta."""
    bk = tmp / "bk"
    content_dir = bk / ".backup-content"
    content_dir.mkdir(parents=True)
    (content_dir / "state.json").write_text(payload, encoding="utf-8")
    info = {"format": "oce-local-ground-backup-v1", "schema_version": "1",
            "includes": ["var"], "run_id": "r" * 12, "pg_dump_format": "plain",
            "pg_dump_version": None, "hash_algorithm": "sha256",
            "source_commit": "c" * 40, "created_at": "2026-01-01T00:00:00Z"}
    (content_dir / "backup-info.json").write_text(json.dumps(info), encoding="utf-8")
    lines = []
    for rel in sorted(p.relative_to(content_dir).as_posix()
                      for p in content_dir.rglob("*") if p.is_file()):
        f = content_dir / rel
        import hashlib
        lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.stat().st_size}  {rel}")
    (bk / "BACKUP_MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return bk


def _run_restore(bk):
    return subprocess.run([_BASH, str(SCRIPTS / "restore.sh"), "--from", str(bk)],
                          capture_output=True, text=True, timeout=120)


def _write_manifest(bk, lines):
    (bk / "BACKUP_MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _valid_line(bk, rel):
    f = bk / ".backup-content" / rel
    import hashlib
    return f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.stat().st_size}  {rel}"


def test_restore_accepts_pristine_backup(tmp_path):
    bk = _make_backup(tmp_path)
    r = _run_restore(bk)
    assert r.returncode == 0, r.stdout + r.stderr


def test_restore_rejects_missing_manifest_file(tmp_path):
    bk = _make_backup(tmp_path)
    (bk / "BACKUP_MANIFEST.sha256").unlink()
    r = _run_restore(bk)
    assert r.returncode != 0 and "CORRUPT" in r.stdout + r.stderr


def test_restore_rejects_absolute_manifest_path(tmp_path):
    bk = _make_backup(tmp_path)
    _write_manifest(bk, [f"{'0' * 64}  1024  /etc/evil"])
    r = _run_restore(bk)
    assert r.returncode != 0 and ("unsafe" in r.stdout + r.stderr.lower() or "CORRUPT" in r.stdout + r.stderr)


def test_restore_rejects_parent_traversal_manifest_path(tmp_path):
    bk = _make_backup(tmp_path)
    _write_manifest(bk, [f"{'0' * 64}  1024  ../outside"])
    r = _run_restore(bk)
    assert r.returncode != 0 and ("unsafe" in r.stdout + r.stderr.lower() or "CORRUPT" in r.stdout + r.stderr)


def test_restore_rejects_duplicate_manifest_path(tmp_path):
    bk = _make_backup(tmp_path)
    line = _valid_line(bk, "state.json")
    _write_manifest(bk, [line, line])
    r = _run_restore(bk)
    assert r.returncode != 0 and "duplicate" in r.stdout + r.stderr.lower()


def test_restore_rejects_malformed_manifest_line(tmp_path):
    bk = _make_backup(tmp_path)
    _write_manifest(bk, ["not-a-valid-line"])
    r = _run_restore(bk)
    assert r.returncode != 0


def test_restore_rejects_backup_without_protected_metadata(tmp_path):
    bk = _make_backup(tmp_path)
    (bk / ".backup-content" / "backup-info.json").unlink()
    # keep manifest referencing state.json only (metadata no longer hash-protected)
    r = _run_restore(bk)
    assert r.returncode != 0 and "backup-info" in (r.stdout + r.stderr).lower()


def test_restore_rejects_tampered_metadata_hash(tmp_path):
    bk = _make_backup(tmp_path)
    (bk / ".backup-content" / "backup-info.json").write_text('{"tampered": true}', encoding="utf-8")
    r = _run_restore(bk)
    assert r.returncode != 0 and "CORRUPT" in r.stdout + r.stderr


def test_restore_rejects_unsafe_artifact_member(tmp_path):
    """R19: a tar with an absolute or '..' member must be rejected rather than
    extracted. Uses the same python tar-validation logic restore.sh relies on."""
    import io
    import socket  # noqa: F401 (portability sanity)
    import tarfile
    tar_path = tmp_path / "unsafe.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        import tarfile as _tf
        info = _tf.TarInfo("/abs/path")
        info.size = 0
        tf.addfile(info)
    # simulate a backup whose artifact tar contains the unsafe member
    bk = _make_backup(tmp_path)
    art_dir = bk / ".backup-content" / "artifacts"
    art_dir.mkdir(exist_ok=True)
    shutil.copy2(tar_path, art_dir / "artifacts.tar.gz")
    # rebuild manifest to include the tar entry with correct hash
    import hashlib
    lines = []
    for rel in sorted(p.relative_to(bk / ".backup-content").as_posix()
                      for p in (bk / ".backup-content").rglob("*") if p.is_file()):
        f = bk / ".backup-content" / rel
        lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.stat().st_size}  {rel}")
    _write_manifest(bk, lines)
    r = _run_restore(bk)
    # The tar validator must reject the unsafe member even without a live
    # artifact container (validation precedes extraction and container checks).
    combo = (r.stdout + r.stderr).lower()
    assert r.returncode != 0
    assert "unsafe tar members" in combo or "corrupt tar" in combo or "failed safe validation" in combo