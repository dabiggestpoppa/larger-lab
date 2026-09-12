#!/usr/bin/env python3
"""OCE Local Ground — backup/restore fail-closed hardening regressions
(B1-LOCAL, A-003; R18/R19).

Rejects missing / absolute / parent-traversal / malformed / duplicate manifest
paths; requires the backup metadata to be hash-protected inside the manifest;
rejects unsafe artefact tar members. These run anywhere (no Docker): restore.sh
must fail fast on integrity problems before touching any data.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

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


# ── recovery-contract state machine (scope/mode) ──────────────────────────
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


def _fake_docker(tmp_path, mode):
    """Build a controlled fake `docker` command environment so the
    unavailable-service path is tested DETERMINISTICALLY without stopping or
    damaging any live Local Ground stack.

    mode: no-docker    — docker CLI present but non-functional (exit 127)
          no-postgres  — compose works, postgres inspect/exec fail
          no-artifact  — compose+postgres work, artifact inspect fails
    Returns the fake bin dir to prepend to PATH."""
    d = tmp_path / "fakebin"
    d.mkdir(exist_ok=True)
    lines = ["#!/usr/bin/env bash"]
    if mode == "no-docker":
        lines.append("exit 127")
    else:
        lines.append('if [ "$1" = "compose" ] && [ "$2" = "version" ]; then exit 0; fi')
        lines.append('if [ "$1" = "inspect" ] && [ "$2" = "oce-local-postgresql" ]; then exit 0; fi')
        if mode == "no-artifact":
            lines.append('if [ "$1" = "exec" ] && [ "$2" = "oce-local-postgresql" ]; then exit 0; fi')
        lines.append("exit 1")
    (d / "docker").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (d / "docker").chmod(0o755)
    return d


def _run_full_backup_with_fake_docker(tmp_path, mode):
    fake = _fake_docker(tmp_path, mode)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               PATH=str(fake) + os.pathsep + os.environ.get("PATH", ""))
    out = tmp_path / "out"
    r = subprocess.run([_BASH, str(SCRIPTS / "backup.sh"), "--scope", "full", "--out", str(out)],
                       capture_output=True, text=True, timeout=120, env=env)
    return r


def test_full_backup_blocked_without_docker_or_services(tmp_path):
    """A 'full' backup must BLOCK (never silently degrade) when the runtime is
    unavailable, even in an environment where a real live stack exists. The
    unavailable-service path is executed in an isolated fake command
    environment (dependency injection) — the shared CI stack is never
    stopped or damaged, and this regression NEVER skips."""
    r = _run_full_backup_with_fake_docker(tmp_path, "no-docker")
    assert r.returncode != 0, "full backup must block when the docker runtime is unavailable"
    combo = (r.stdout + r.stderr).lower()
    assert "blocked" in combo and "full" in combo
    assert "docker" in combo


def test_full_backup_blocked_when_postgres_unavailable(tmp_path):
    """A 'full' backup must BLOCK when PostgreSQL is unavailable even though
    the docker runtime is present (no silent degradation to an incomplete
    backup). Executed against a fake command environment."""
    r = _run_full_backup_with_fake_docker(tmp_path, "no-postgres")
    assert r.returncode != 0
    combo = (r.stdout + r.stderr).lower()
    assert "blocked" in combo
    assert "postgresql" in combo, combo


def test_full_backup_blocked_when_artifact_store_unavailable(tmp_path):
    """A 'full' backup must BLOCK when the artifact store is unavailable even
    though docker and PostgreSQL are present. Executed against a fake command
    environment."""
    r = _run_full_backup_with_fake_docker(tmp_path, "no-artifact")
    assert r.returncode != 0
    combo = (r.stdout + r.stderr).lower()
    assert "blocked" in combo
    assert "artifact" in combo, combo


def test_state_only_backup_still_works_without_docker(tmp_path):
    """state-only backups must remain deterministic when the runtime is
    unavailable (they never require docker) — R7 keeps local capability."""
    fake = _fake_docker(tmp_path, "no-docker")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               PATH=str(fake) + os.pathsep + os.environ.get("PATH", ""))
    out = tmp_path / "out"
    r = subprocess.run([_BASH, str(SCRIPTS / "backup.sh"), "--scope", "state-only", "--out", str(out)],
                       capture_output=True, text=True, timeout=120, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    info = json.loads((out / ".backup-content" / "backup-info.json").read_text(encoding="utf-8"))
    assert info["scope"] == "state-only"
    assert info["disaster_recovery_capable"] is False


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


def _load_pr():
    import importlib.util
    spec = importlib.util.spec_from_file_location("pg_recovery", str(SCRIPTS / "pg-recovery.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_inventory_verification_pure():
    """Unit test of pg-recovery verify_inventory pure helper (no Docker)."""
    pr = _load_pr()
    inv = pr.parse_inventory(json.dumps({
        "format": "oce-pg-inventory-v1", "database": "oce_local",
        "table_count": 2, "tables": [
            {"name": "public.state_probe", "row_count": 3},
            {"name": "public.backup_probe", "row_count": 2}]}))
    ok, probs = pr.verify_inventory(inv, {"public.state_probe": 3, "public.backup_probe": 2},
                                    pr.parse_probe_spec("public.backup_probe=2"))
    assert ok and not probs
    ok2, probs2 = pr.verify_inventory(inv, {"public.state_probe": 3, "public.backup_probe": 9})
    assert not ok2


def test_sha256_file_is_deterministic():
    """sha256_file returns a 64-char hex digest deterministically."""
    pr = _load_pr()
    p = str(BASE_DIR / "requirements-ci.txt")
    assert len(pr.sha256_file(p)) == 64
    assert pr.sha256_file(p) == pr.sha256_file(p)


# ── R25: phase-safe recovery state machine (pure) ─────────────────────────
def test_pg_recovery_source_has_no_invalid_database_syntax():
    """PostgreSQL does not support `ALTER DATABASE IF EXISTS`; existence must
    be proven via the pg_database catalog before ALTER/DROP DATABASE. The
    recovery engine must never contain the invalid forms."""
    src = (SCRIPTS / "pg-recovery.py").read_text(encoding="utf-8")
    assert "ALTER DATABASE IF EXISTS" not in src
    assert "DROP DATABASE IF EXISTS" not in src
    assert "pg_database" in src, "catalog-based existence checks must be used"


def test_promote_phase_prefix_is_valid():
    pr = _load_pr()
    good = ["inventory_validated", "archive_validated", "staging_created",
            "staging_restored", "staging_verified", "canonical_quarantined",
            "promoted", "canonical_verified"]
    assert pr.valid_phase_prefix(good, pr.PHASES_PROMOTE) is True
    # a prefix (recovery still in progress) is valid
    assert pr.valid_phase_prefix(good[:4], pr.PHASES_PROMOTE) is True
    # out-of-order / invented / empty phase lists must be rejected
    assert pr.valid_phase_prefix(list(reversed(good)), pr.PHASES_PROMOTE) is False
    assert pr.valid_phase_prefix(["invented_phase"], pr.PHASES_PROMOTE) is False
    assert pr.valid_phase_prefix([], pr.PHASES_PROMOTE) is False


def test_finalize_phase_prefix_is_valid():
    pr = _load_pr()
    good = ["final_canonical_verified", "quarantine_dropped",
            "quarantine_removal_verified"]
    assert pr.valid_phase_prefix(good, pr.PHASES_FINALIZE) is True
    assert pr.valid_phase_prefix(good[:1], pr.PHASES_FINALIZE) is True
    assert pr.valid_phase_prefix(["quarantine_dropped", "final_canonical_verified"],
                                 pr.PHASES_FINALIZE) is False


def test_rollback_receipt_truthfulness_contract():
    """rollback_truthful: a rollback that was never attempted, or that claims
    success without restoring the original, is rejected; a truthfully failed
    rollback (quarantine missing) is reported as rollback_failed."""
    pr = _load_pr()
    # never attempted -> not truthful
    assert pr.rollback_truthful({"rollback_required": True}) is False
    # attempted + succeeded with original restored + verified -> truthful
    good = {"rollback_required": True, "rollback_attempted": True,
            "rollback_succeeded": True, "rollback_failed": False,
            "original_canonical_restored": True,
            "rollback_verification": {"result": "ok"}}
    assert pr.rollback_truthful(good) is True
    # claims success but original NOT restored -> a lie
    lie = dict(good, original_canonical_restored=False)
    assert pr.rollback_truthful(lie) is False
    # claims success but verification failed -> a lie
    lie2 = dict(good, rollback_verification={"result": "failed"})
    assert pr.rollback_truthful(lie2) is False
    # attempted + truthfully failed (quarantine missing) -> reported as failure
    failed = {"rollback_required": True, "rollback_attempted": True,
              "rollback_succeeded": False, "rollback_failed": True,
              "original_canonical_restored": False}
    assert pr.rollback_truthful(failed) is True  # truthful ABOUT the failure


def test_recovery_succeeded_never_overrides_failed_invariant():
    """recovery_succeeded: a green exit cannot override a failed rollback or
    an outstanding rollback — the recovery gate fails closed."""
    pr = _load_pr()
    assert pr.recovery_succeeded({"exit_status": 0}) is True
    # exit 0 but rollback required and never succeeded -> NOT success
    assert pr.recovery_succeeded({"exit_status": 0, "rollback_required": True,
                                  "rollback_succeeded": False}) is False
    assert pr.recovery_succeeded({"exit_status": 0, "rollback_failed": True}) is False
    # exit 1 can never be success
    assert pr.recovery_succeeded({"exit_status": 1}) is False
    # exit 0 + fully successful rollback -> success
    assert pr.recovery_succeeded({"exit_status": 0, "rollback_required": True,
                                  "rollback_succeeded": True}) is True


# ── R26: protected recovery values and fingerprints (pure) ────────────────
def _fingerprinted_inventory(rows):
    return json.dumps({
        "format": "oce-pg-inventory-v1", "database": "oce_local", "table_count": len(rows),
        "fingerprint_algorithm": "md5-of-sorted-row-json",
        "fingerprinted_tables": list(rows),
        "tables": [{"name": n, "row_count": r, "fingerprint": f"fp-{n}"}
                   for n, r in rows.items()]})


def test_fingerprint_mismatch_rejected_despite_matching_counts():
    """Row counts are NOT content proof: identical counts with different
    values must fail closed via the protected value fingerprints."""
    pr = _load_pr()
    inv = pr.parse_inventory(_fingerprinted_inventory({"public.backup_probe": 2}))
    # counts match, fingerprints differ -> verification must fail
    ok, probs = pr.verify_inventory(inv, {"public.backup_probe": 2}, None,
                                    {"public.backup_probe": "different-fingerprint"})
    assert not ok
    assert any("fingerprint" in p for p in probs)


def test_value_altered_after_staging_verification_is_caught():
    """A value altered AFTER staging verification (e.g. in the promoted
    canonical) changes the fingerprint even when the row count is identical.
    Re-verification must fail closed."""
    pr = _load_pr()
    inv = pr.parse_inventory(_fingerprinted_inventory({"public.backup_probe": 2}))
    # staging verified clean
    ok1, _ = pr.verify_inventory(inv, {"public.backup_probe": 2}, None,
                                 {"public.backup_probe": "fp-public.backup_probe"})
    assert ok1
    # one value altered after staging verification: count unchanged, fp changed
    ok2, probs2 = pr.verify_inventory(inv, {"public.backup_probe": 2}, None,
                                      {"public.backup_probe": "tampered-fingerprint"})
    assert not ok2
    assert any("fingerprint mismatch" in p for p in probs2)


def test_row_count_only_receipt_is_rejected():
    """A receipt that proves only row counts (no fingerprint evidence) cannot
    prove values and must be rejected — a false row-count-only receipt fails
    closed."""
    pr = _load_pr()
    inv = pr.parse_inventory(_fingerprinted_inventory({"public.backup_probe": 2}))
    ok, probs = pr.verify_inventory(inv, {"public.backup_probe": 2}, None, None)
    assert not ok
    assert any("missing fingerprint evidence" in p for p in probs)


def test_inventory_fingerprint_tamper_rejected():
    """Tampering with the protected inventory (e.g. replacing a fingerprint)
    breaks the inventory SHA and must be rejected before any recovery."""
    pr = _load_pr()
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        invp = os.path.join(td, "inventory.json")
        shap = os.path.join(td, "inventory.json.sha256")
        doc = _fingerprinted_inventory({"public.backup_probe": 2})
        with open(invp, "w", encoding="utf-8") as f:
            f.write(doc)
        with open(shap, "w", encoding="utf-8") as f:
            f.write(hashlib.sha256(doc.encode()).hexdigest() + "\n")
        # load is fine before tampering
        inv = pr._load_protected_inventory(invp, shap)
        assert "public.backup_probe" in inv["tables"]
        # tamper one fingerprint value -> SHA mismatch -> RuntimeError
        tampered = doc.replace("fp-public.backup_probe", "fp-evil")
        with open(invp, "w", encoding="utf-8") as f:
            f.write(tampered)
        import pytest as _pytest
        with _pytest.raises(RuntimeError, match="tampered"):
            pr._load_protected_inventory(invp, shap)


# ── R8: immutable indexed recovery receipts (pure) ─────────────────────────
def _ops_add(root, opid, op_type="restore", final="success", rollback="none",
             receipt=None, extra=None):
    if receipt is None:
        receipt = tmpfile_ops_receipt(root)
    cmd = [sys.executable, str(SCRIPTS / "recovery-ops.py"), "add",
           "--ops-root", str(root), "--operation-id", opid,
           "--operation-type", op_type, "--run-id", "aabbccddeeff",
           "--commit", "c" * 40, "--tree", "t" * 40,
           "--started-at", "2026-01-01T00:00:00Z", "--finished-at", "2026-01-01T00:00:01Z",
           "--backup-id", opid, "--backup-scope", "full", "--restore-mode", "full-replace",
           "--source-database", "oce_local", "--target-database", "oce_local",
           "--final-result", final, "--rollback-result", rollback,
           "--cloud-mutations", "0", "--cloud-cost-state", "ZERO",
           "--receipt", str(receipt)] + list(extra or [])
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


def tmpfile_ops_receipt(root):
    root.mkdir(parents=True, exist_ok=True)
    p = root / "receipt-src.json"
    p.write_text(json.dumps({"receipt": True, "phase": "staging"}), encoding="utf-8")
    return p


def test_two_restores_preserve_two_receipt_sets(tmp_path):
    """Two restore operations produce two preserved, independently indexed
    receipt sets; neither clobbers the other."""
    root = tmp_path / "ops"
    r1 = _ops_add(root, "a" * 16, receipt=tmpfile_ops_receipt(root / "r1"))
    r2 = _ops_add(root, "b" * 16, receipt=tmpfile_ops_receipt(root / "r2"))
    assert r1.returncode == 0, r1.stdout + r1.stderr
    assert r2.returncode == 0, r2.stdout + r2.stderr
    idx = json.loads((root / "index.json").read_text(encoding="utf-8"))
    assert len(idx["operations"]) == 2
    assert (root / "operations" / ("a" * 16) / "receipt-src.json").is_file()
    assert (root / "operations" / ("b" * 16) / "receipt-src.json").is_file()
    v = subprocess.run([sys.executable, str(SCRIPTS / "recovery-ops.py"), "verify",
                        "--ops-root", str(root)], capture_output=True, text=True, timeout=60)
    assert v.returncode == 0, v.stdout + v.stderr


def test_later_operation_cannot_overwrite_earlier_evidence(tmp_path):
    """Registering a later operation never modifies the earlier operation's
    receipt set or its indexed hashes."""
    root = tmp_path / "ops"
    rec_a = tmpfile_ops_receipt(root / "r1")
    r1 = _ops_add(root, "a" * 16, receipt=rec_a)
    assert r1.returncode == 0
    before = (root / "operations" / ("a" * 16) / "receipt-src.json").read_bytes()
    # a later (successful) restore registers a second operation
    r2 = _ops_add(root, "b" * 16, receipt=tmpfile_ops_receipt(root / "r2"))
    assert r2.returncode == 0
    after = (root / "operations" / ("a" * 16) / "receipt-src.json").read_bytes()
    assert before == after, "later operation modified earlier evidence"
    idx = json.loads((root / "index.json").read_text(encoding="utf-8"))
    e_a = [op for op in idx["operations"] if op["operation_id"] == "a" * 16][0]
    # the earlier entry still references its ORIGINAL hash
    assert e_a["receipts"][0]["sha256"] == hashlib.sha256(before).hexdigest()


def test_duplicate_operation_id_fails(tmp_path):
    """A duplicate operation ID must be rejected — immutable receipts cannot
    be overwritten or re-indexed."""
    root = tmp_path / "ops"
    rec = tmpfile_ops_receipt(root)
    r1 = _ops_add(root, "a" * 16, receipt=rec)
    assert r1.returncode == 0
    r2 = _ops_add(root, "a" * 16, receipt=tmpfile_ops_receipt(root / "dup"))
    assert r2.returncode != 0
    assert "DUPLICATE_OPERATION_ID" in r2.stdout + r2.stderr
    idx = json.loads((root / "index.json").read_text(encoding="utf-8"))
    assert len(idx["operations"]) == 1, "duplicate op must not be indexed"


def test_verify_detects_missing_indexed_receipt(tmp_path):
    """Deleting an indexed receipt file fails verification (missing indexed
    receipts must fail the gate)."""
    root = tmp_path / "ops"
    assert _ops_add(root, "a" * 16, receipt=tmpfile_ops_receipt(root / "r")).returncode == 0
    (root / "operations" / ("a" * 16) / "receipt-src.json").unlink()
    v = subprocess.run([sys.executable, str(SCRIPTS / "recovery-ops.py"), "verify",
                        "--ops-root", str(root)], capture_output=True, text=True, timeout=60)
    assert v.returncode != 0
    assert "missing" in (v.stdout + v.stderr).lower()


def test_verify_detects_receipt_hash_mismatch(tmp_path):
    """Tampering with an indexed receipt file fails verification (receipt
    hash mismatch must fail the gate)."""
    root = tmp_path / "ops"
    assert _ops_add(root, "a" * 16, receipt=tmpfile_ops_receipt(root / "r")).returncode == 0
    p = root / "operations" / ("a" * 16) / "receipt-src.json"
    p.write_text('{"tampered": true}', encoding="utf-8")
    v = subprocess.run([sys.executable, str(SCRIPTS / "recovery-ops.py"), "verify",
                        "--ops-root", str(root)], capture_output=True, text=True, timeout=60)
    assert v.returncode != 0
    assert "mismatch" in (v.stdout + v.stderr).lower()


def test_collect_observed_fingerprints_decodes_bytes_stdout():
    """psql returns BYTES stdout (docker exec without text=True); the
    observed fingerprints must be decoded strings so they are JSON-
    serializable in the receipt and comparable to the inventory. This is the
    regression for the authoritative CI bytes-in-receipt failure."""
    pr = _load_pr()
    import types

    class FakeR:
        returncode = 0
        stdout = b"fp-public.backup_probe"
        stderr = b""

    def fake_psql(container, db, user, sql, stdin_bytes=None):
        return FakeR()

    pr.psql = fake_psql
    fps = pr.collect_observed_fingerprints("c", "d", "u", ["public.backup_probe"])
    assert fps == {"public.backup_probe": "fp-public.backup_probe"}
    assert isinstance(fps["public.backup_probe"], str)
    json.dumps({"fingerprints": fps})  # must be JSON-serializable (no bytes)
    # and comparable to a str inventory fingerprint (no false mismatch)
    inv = pr.parse_inventory(_fingerprinted_inventory({"public.backup_probe": 2}))
    ok, probs = pr.verify_inventory(inv, {"public.backup_probe": 2}, None, fps)
    assert ok, probs


def test_collect_observed_rows_decodes_bytes_stdout():
    pr = _load_pr()

    class FakeR:
        returncode = 0
        stdout = b"2"
        stderr = b""

    pr.psql = lambda container, db, user, sql, stdin_bytes=None: FakeR()
    rows = pr.collect_observed_rows("c", "d", "u", ["public.backup_probe"])
    assert rows == {"public.backup_probe": 2}
    assert isinstance(rows["public.backup_probe"], int)


def test_latest_pointer_is_not_authoritative(tmp_path):
    """A convenience latest.json cannot substitute for the authoritative
    indexed receipt sets: without an index (or with an empty index) verify
    must fail."""
    root = tmp_path / "ops"
    root.mkdir(parents=True, exist_ok=True)
    (root / "latest.json").write_text('{"operation_id": "a" * 16}', encoding="utf-8")
    v = subprocess.run([sys.executable, str(SCRIPTS / "recovery-ops.py"), "verify",
                        "--ops-root", str(root)], capture_output=True, text=True, timeout=60)
    assert v.returncode != 0
    assert "index missing" in (v.stdout + v.stderr).lower()