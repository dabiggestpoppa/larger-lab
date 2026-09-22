#!/usr/bin/env python3
"""B4-CXR7U9R39-R1 — a failed full replace must not leave the two durable
stores from different snapshots. CONTAINER-BACKED (mandatory in CI).

restore.sh used to replace the live artifact volume BEFORE PostgreSQL
recovery, so an artifact replacement that succeeded followed by a PostgreSQL
failure left the artifact truth from the backup and the database truth from
before it. Full replace is now a staged two-resource recovery: both stores are
staged with a held rollback source (the PostgreSQL quarantine, and a
byte-for-byte copy of the live artifact volume taken before it is touched),
both are verified against the selected backup, and only then is the
transaction committed by finalizing PostgreSQL and releasing the artifact
rollback source. Any failure before commitment restores BOTH stores.

Fault injection is a TEST-SIDE `docker` shim placed first on PATH: it delegates
to the real runtime except for one named injection, so the engine's own
production path is what runs, unmodified and without a production test seam.
"""
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

import oce_compose as oc

pytestmark = pytest.mark.container

VAR = oc.SCRIPTS.parent / "var"
ARTIFACT_VOLUME = "oce_local_artifact_data"


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _pg_truth():
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT k || '=' || v FROM backup_probe ORDER BY k;"])
    return [line.strip() for line in r.stdout.splitlines() if line.strip()]


def _artifact_volume_sha():
    r = oc.run(["docker", "run", "--rm", "-v", f"{ARTIFACT_VOLUME}:/data",
                "postgres:16.2-alpine", "sh", "-c",
                "cd /data 2>/dev/null || exit 0; "
                "find . -type f -exec sha256sum {} + 2>/dev/null"])
    lines = sorted(line for line in r.stdout.splitlines() if line.strip())
    return _sha("\n".join(lines))


def _redis_value(key):
    r = oc.dexec(oc.REDIS, ["redis-cli", "GET", key])
    return r.stdout.strip()


def _env(tmp_path, evidence=None):
    return {"OCE_BACKUP_ROOTS": str(tmp_path),
            "OCE_EVIDENCE_DIR": str(evidence or (tmp_path / "evidence")),
            "OCE_COMMIT": "a" * 40, "OCE_TREE": "b" * 40,
            "OCE_RUN_ID": "0123456789abcdef"}


def _seed_and_backup(tmp_path):
    """Protected database truth, a marked artifact file and a transient cache
    key, then ONE full backup of exactly that state."""
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS backup_probe"
                           "(k text PRIMARY KEY, v text);"
                           "INSERT INTO backup_probe VALUES('b1','alpha'),('b2','beta') "
                           "ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v;"])
    marker = tmp_path / "artifact-marker.txt"
    marker.write_text("backup-A\n", encoding="utf-8")
    oc.cp_into(oc.ARTIFACT, str(marker), "/data/artifact-marker.txt")
    oc.dexec(oc.REDIS, ["redis-cli", "SET", "txn:cache", "untouched"])
    bk = tmp_path / "bk"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--scope", "full",
            "--out", str(bk)], check=True)
    return bk


def _restore_argv(bk):
    return ["bash", str(oc.SCRIPTS / "restore.sh"), "--mode", "full-replace",
            "--from", str(bk), "--confirm-local-target", oc.PG_DB]


def _evidence(tmp_path, name):
    p = Path(tmp_path) / "evidence" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def _docker_shim(tmp_path, injection):
    """A PATH-first `docker` that delegates to the real one, except for the
    single injected fault this test is about."""
    real = shutil.which("docker")
    assert real, "the container marker should have skipped without Docker"
    shim = tmp_path / "shim"
    shim.mkdir(exist_ok=True)
    script = shim / "docker"
    script.write_text(
        "#!/usr/bin/env bash\n"
        "set -uo pipefail\n"
        f"REAL='{real}'\n"
        "if [[ \"${1:-}\" == \"cp\" && \"${3:-}\" == *\"oce-local-artifact:/data/\"* ]]; then\n"
        "  case \"" + injection + "\" in\n"
        "    artifact-copy-fail)\n"
        "      # the wipe has already run: the live volume is empty and the\n"
        "      # snapshot is the only way back\n"
        "      echo 'shim: injected artifact copy failure' >&2; exit 1 ;;\n"
        "    artifact-extra-file)\n"
        "      \"$REAL\" \"$@\" || exit $?\n"
        "      \"$REAL\" run --rm -v oce_local_artifact_data:/data \\\n"
        "        postgres:16.2-alpine sh -c 'echo injected > /data/injected.txt'\n"
        "      exit 0 ;;\n"
        "  esac\n"
        "fi\n"
        "exec \"$REAL\" \"$@\"\n", encoding="utf-8")
    script.chmod(0o755)
    return str(shim)


def _env_with_shim(tmp_path, shim):
    env = _env(tmp_path)
    env["PATH"] = shim + os.pathsep + os.environ.get("PATH", "")
    return env


# --------------------------------------------------------------------- #
# a committed full replace
# --------------------------------------------------------------------- #

def test_successful_full_replace_sources_both_stores_from_one_backup(oce_stack, tmp_path):
    oc.assert_stack_converged(timeout_s=180, stable=2)
    bk = _seed_and_backup(tmp_path)
    backup_truth = _pg_truth()
    assert backup_truth == ["b1=alpha", "b2=beta"], backup_truth
    # destroy the live truth in BOTH stores so the restore has real work to do
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "UPDATE backup_probe SET v='destroyed' WHERE k='b1';"])
    later = tmp_path / "later.txt"
    later.write_text("not-in-the-backup\n", encoding="utf-8")
    oc.cp_into(oc.ARTIFACT, str(later), "/data/later.txt")

    r = oc.run(_restore_argv(bk), env_extra=_env(tmp_path), check=False, timeout=900)
    assert r.returncode == 0, r.stdout + r.stderr

    # PostgreSQL truth is the backup's
    assert _pg_truth() == backup_truth
    # artifact truth is the backup's - the later file is gone, the marker is back
    assert oc.dexec(oc.ARTIFACT, ["cat", "/data/artifact-marker.txt"]).stdout.strip() \
        == "backup-A"
    assert oc.run(["docker", "exec", oc.ARTIFACT, "test", "!", "-e",
                   "/data/later.txt"], check=False).returncode == 0

    # and the artifact receipt proves which volume identity was committed
    art = _evidence(tmp_path, "artifact-recovery-receipt.json")
    assert art["artifact_replaced"] is True, art
    assert art["artifact_verify"] == "ok", art
    assert art["artifact_volume_sha256_after"] == art["artifact_staged_sha256"], art
    assert art["artifact_volume_sha256_after"] == _artifact_volume_sha()
    assert art["artifact_volume_sha256_before"] != art["artifact_volume_sha256_after"]
    # a committed transaction writes no rollback receipt
    assert _evidence(tmp_path, "transaction-rollback-receipt.json") is None
    # Redis is transient: invalidated, never restored
    assert _redis_value("txn:cache") == ""


# --------------------------------------------------------------------- #
# preflight / promotion failure: the artifact store is never touched
# --------------------------------------------------------------------- #

def _tamper_inventory_row_count(bk):
    """Make the backup restore successfully but FAIL verification, keeping the
    manifest and the inventory SHA internally consistent."""
    content = bk / ".backup-content"
    inv = content / "postgres" / "inventory.json"
    doc = json.loads(inv.read_text(encoding="utf-8"))
    doc["tables"][0]["row_count"] = 999
    inv.write_text(json.dumps(doc), encoding="utf-8")
    sha = hashlib.sha256(inv.read_bytes()).hexdigest()
    (content / "postgres" / "inventory.json.sha256").write_text(sha, encoding="utf-8")
    manifest = bk / "BACKUP_MANIFEST.sha256"
    lines = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.split(" ")
        if len(parts) == 3 and parts[2] in ("postgres/inventory.json",
                                            "postgres/inventory.json.sha256"):
            target = content / parts[2]
            parts[0] = hashlib.sha256(target.read_bytes()).hexdigest()
            parts[1] = str(target.stat().st_size)
            line = " ".join(parts)
        lines.append(line)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_postgres_promotion_failure_leaves_database_and_artifacts_unchanged(
        oce_stack, tmp_path):
    oc.assert_stack_converged(timeout_s=180, stable=2)
    bk = _seed_and_backup(tmp_path)
    _tamper_inventory_row_count(bk)
    art_before = _artifact_volume_sha()
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "UPDATE backup_probe SET v='current' WHERE k='b1';"])
    pg_live = _pg_truth()

    r = oc.run(_restore_argv(bk), env_extra=_env(tmp_path), check=False, timeout=900)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "BLOCKED" in r.stderr
    # the DATABASE is exactly where it was (the candidate never became canonical)
    assert _pg_truth() == pg_live, _pg_truth()
    # and the artifact volume was never switched: still byte-identical
    assert _artifact_volume_sha() == art_before
    assert _redis_value("txn:cache") == "untouched", "a failed restore touched the cache"


# --------------------------------------------------------------------- #
# failure AFTER promotion: BOTH stores come back
# --------------------------------------------------------------------- #

def _assert_both_restored(tmp_path, pg_before, art_before, expect_reason):
    assert _pg_truth() == pg_before, _pg_truth()
    assert _artifact_volume_sha() == art_before, "the artifact volume is not the original"
    assert _redis_value("txn:cache") == "untouched", "the rolled-back run touched the cache"
    tx = _evidence(tmp_path, "transaction-rollback-receipt.json")
    assert tx is not None, "a pre-commit failure must leave a truthful rollback receipt"
    assert tx["committed"] is False, tx
    assert tx["postgres_rolled_back"] is True, tx
    assert tx["artifact_restored"] is True, tx
    assert tx["redis_untouched"] is True, tx
    assert tx["artifact_sha256_before"] == tx["artifact_sha256_after"], tx
    assert expect_reason in (tx["reason"] or ""), tx


def test_artifact_switch_failure_restores_both_stores(oce_stack, tmp_path):
    """The injected fault lands AFTER PostgreSQL promotion (quarantine held) and
    INSIDE the artifact switch, after the wipe: without the artifact rollback
    source the database would be restored while the artifact volume stayed
    empty - the exact cross-store divergence this gate exists to prevent."""
    oc.assert_stack_converged(timeout_s=180, stable=2)
    bk = _seed_and_backup(tmp_path)
    pg_before, art_before = _pg_truth(), _artifact_volume_sha()
    shim = _docker_shim(tmp_path, "artifact-copy-fail")
    try:
        r = oc.run(_restore_argv(bk), env_extra=_env_with_shim(tmp_path, shim),
                   check=False, timeout=900)
    finally:
        shutil.rmtree(shim, ignore_errors=True)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "artifact restore into the container failed" in r.stderr, r.stderr
    _assert_both_restored(tmp_path, pg_before, art_before, "artifact restore")


def test_artifact_verification_failure_restores_both_stores(oce_stack, tmp_path):
    """The copy lands, but the restored volume is NOT the staged snapshot: the
    verification must refuse the switch and restore BOTH stores."""
    oc.assert_stack_converged(timeout_s=180, stable=2)
    bk = _seed_and_backup(tmp_path)
    pg_before, art_before = _pg_truth(), _artifact_volume_sha()
    shim = _docker_shim(tmp_path, "artifact-extra-file")
    try:
        r = oc.run(_restore_argv(bk), env_extra=_env_with_shim(tmp_path, shim),
                   check=False, timeout=900)
    finally:
        shutil.rmtree(shim, ignore_errors=True)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "not the staged snapshot" in r.stderr, r.stderr
    _assert_both_restored(tmp_path, pg_before, art_before, "artifact volume")
    # the injected file is gone: the volume really is the pre-replace truth
    assert oc.run(["docker", "exec", oc.ARTIFACT, "test", "!", "-e",
                   "/data/injected.txt"], check=False).returncode == 0


def test_interrupted_full_replace_commits_nothing(oce_stack, tmp_path):
    """Process interruption between staging and commit (the operator's Ctrl-C):
    the transaction must not commit and BOTH stores must be left original."""
    oc.assert_stack_converged(timeout_s=180, stable=2)
    bk = _seed_and_backup(tmp_path)
    pg_before, art_before = _pg_truth(), _artifact_volume_sha()
    proc = subprocess.Popen(
        ["bash", str(oc.SCRIPTS / "restore.sh"), "--mode", "full-replace",
         "--from", str(bk), "--confirm-local-target", oc.PG_DB],
        env=dict(os.environ, **oc.TEST_SECRETS, **{
            "OCE_RUNTIME_TARGET": "local",
            "OCE_EVIDENCE_DIR": str(tmp_path / "evidence")}),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # interrupt only once the promotion is durable (the quarantine is held)
    deadline = time.time() + 240
    promoted = False
    while time.time() < deadline and proc.poll() is None:
        if list((VAR / "recovery" / "ops").glob("*/promote-receipt.json")):
            promoted = True
            break
        time.sleep(1)
    if proc.poll() is None:
        proc.terminate()
    out, err = proc.communicate(timeout=600)
    assert promoted, f"the promotion never became durable: {out}\n{err}"
    assert proc.returncode != 0, out + err
    assert _pg_truth() == pg_before, _pg_truth()
    assert _artifact_volume_sha() == art_before
    assert _redis_value("txn:cache") == "untouched"
    tx = _evidence(tmp_path, "transaction-rollback-receipt.json")
    assert tx is not None and tx["committed"] is False, tx
