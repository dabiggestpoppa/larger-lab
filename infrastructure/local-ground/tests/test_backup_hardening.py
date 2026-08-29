#!/usr/bin/env python3
"""OCE Local Ground â€” backup/restore fail-closed hardening regressions
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


def _make_backup(tmp, payload='{"clean": "1"}', scope="state-only", include_artifacts=False, name="bk"):
    """Build a minimal valid backup dir: manifest + content + protected meta.
    Defaults to a valid `state-only` backup (disaster_recovery_capable=false).
    Set scope="full" and include_artifacts=True to build a full-replace target."""
    import hashlib
    bk = tmp / name
    content_dir = bk / ".backup-content"
    content_dir.mkdir(parents=True)
    (content_dir / "state.json").write_text(payload, encoding="utf-8")
    dcr = scope == "full"
    info = {"format": "oce-local-ground-backup-v1", "schema_version": "2",
            "scope": scope, "backup_id": "b" * 32,
            "disaster_recovery_capable": dcr, "includes": "state" + (" postgres artifacts" if dcr else ""),
            "database": "oce_local", "run_id": "r" * 12, "pg_dump_format": "custom" if dcr else None,
            "pg_dump_version": None, "hash_algorithm": "sha256",
            "source_commit": "c" * 40, "created_at": "2026-01-01T00:00:00Z"}
    (content_dir / "backup-info.json").write_text(json.dumps(info), encoding="utf-8")
    if dcr:
        pdir = content_dir / "postgres"
        pdir.mkdir(exist_ok=True)
        (pdir / "archive.dump").write_text("CUSTOM-ARCHIVE", encoding="utf-8")
        (pdir / "inventory.json").write_text(json.dumps({"format": "oce-pg-inventory-v1",
                                                          "database": "oce_local", "pg_version_num": "160003",
                                                          "captured_at": "2026-01-01T00:00:00Z", "table_count": 0, "tables": []}), encoding="utf-8")
        adir = content_dir / "artifacts"
        adir.mkdir(exist_ok=True)
        if include_artifacts:
            (adir / "artifacts.tar.gz").write_text("ARTIFACT-TAR", encoding="utf-8")
    lines = []
    for rel in sorted(p.relative_to(content_dir).as_posix()
                      for p in content_dir.rglob("*") if p.is_file()):
        f = content_dir / rel
        lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.stat().st_size}  {rel}")
    (bk / "BACKUP_MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return bk


def _run_restore(bk, mode="state-only", extra=None):
    cmd = [_BASH, str(SCRIPTS / "restore.sh"), "--mode", mode, "--from", str(bk)]
    if extra:
        cmd += extra
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


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
    # simulate a full backup whose artifact tar contains the unsafe member
    bk = _make_backup(tmp_path, scope="full", include_artifacts=True)
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
    r = _run_restore(bk, mode="full-replace", extra=["--confirm-local-target", "oce_local"])
    # The tar validator must reject the unsafe member even without a live
    # artifact container (validation precedes extraction and container checks).
    combo = (r.stdout + r.stderr).lower()
    assert r.returncode != 0
    assert "unsafe tar members" in combo or "corrupt tar" in combo or "failed safe validation" in combo


# â”€â”€ recovery-contract state machine (scope/mode) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_unknown_backup_scope_fails_closed(tmp_path):
    r = subprocess.run([_BASH, str(SCRIPTS / "backup.sh"), "--scope", "mystery",
                        "--out", str(tmp_path / "bk")], capture_output=True, text=True, timeout=60)
    assert r.returncode != 0 and "unknown --scope" in (r.stdout + r.stderr).lower()


def test_backup_requires_scope(tmp_path):
    r = subprocess.run([_BASH, str(SCRIPTS / "backup.sh"), "--out", str(tmp_path / "bk")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode != 0 and "--scope" in (r.stdout + r.stderr)


def test_unknown_restore_mode_fails_closed(tmp_path):
    bk = _make_backup(tmp_path)
    r = _run_restore(bk, mode="mystery")
    assert r.returncode != 0 and "unknown --mode" in (r.stdout + r.stderr).lower()


def test_full_backup_blocked_without_docker_or_services():
    """A 'full' backup must BLOCK (never silently degrade) when the runtime
    services are unavailable â€” it must not produce an incomplete backup."""
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run([_BASH, str(SCRIPTS / "backup.sh"), "--scope", "full", "--out", td],
                           capture_output=True, text=True, timeout=120, env=env)
        assert r.returncode != 0
        combo = (r.stdout + r.stderr).lower()
        assert "blocked" in combo and "full" in combo


def test_state_only_backup_never_claims_disaster_recovery(tmp_path):
    bk = _make_backup(tmp_path)
    info = json.loads((bk / ".backup-content" / "backup-info.json").read_text(encoding="utf-8"))
    assert info["disaster_recovery_capable"] is False


def test_full_backup_cannot_use_state_only_restore(tmp_path):
    bk = _make_backup(tmp_path, scope="full", include_artifacts=True)
    r = _run_restore(bk, mode="state-only")
    assert r.returncode != 0
    assert "state-only" in r.stdout + r.stderr


def test_state_only_backup_cannot_use_full_replace_restore(tmp_path):
    bk = _make_backup(tmp_path)
    r = _run_restore(bk, mode="full-replace", extra=["--confirm-local-target", "oce_local"])
    assert r.returncode != 0
    assert "full-replace" in r.stdout + r.stderr or "state-only" in r.stdout + r.stderr


def test_full_replace_requires_confirm_local_target(tmp_path):
    bk = _make_backup(tmp_path, scope="full", include_artifacts=True)
    r = _run_restore(bk, mode="full-replace")
    assert r.returncode != 0 and "confirm-local-target" in r.stdout + r.stderr


def test_full_replace_rejects_wrong_local_target(tmp_path):
    bk = _make_backup(tmp_path, scope="full", include_artifacts=True)
    r = _run_restore(bk, mode="full-replace", extra=["--confirm-local-target", "other_db"])
    assert r.returncode != 0 and "confirm-local-target" in r.stdout + r.stderr


def test_incomplete_full_backup_rejected():
    """A full backup missing the artifact archive must be rejected as incomplete
    rather than passed off as a full backup."""
    import os
    import tempfile
    from pathlib import Path as _P
    import hashlib as _h
    with tempfile.TemporaryDirectory() as td:
        # run a state-only backup then tamper metadata to claim full: must fail
        bk = _P(td) / "b"
        r = subprocess.run([_BASH, str(SCRIPTS / "backup.sh"), "--scope", "state-only", "--out", str(bk)],
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 0
        info = json.loads((bk / ".backup-content" / "backup-info.json").read_text(encoding="utf-8"))
        info["scope"] = "full"
        info["disaster_recovery_capable"] = True
        (bk / ".backup-content" / "backup-info.json").write_text(json.dumps(info), encoding="utf-8")
        # the tampered full claim lacks postgres+artifacts: full-replace must block
        r2 = _run_restore(bk, mode="full-replace", extra=["--confirm-local-target", "oce_local"])
        assert r2.returncode != 0
