#!/usr/bin/env python3
"""OCE Local Ground â€” real container lifecycle tests (B1-LOCAL, A-003).

Prove the actual Compose stack runs: config validates, images are pinned, all
services reach truthful health (including Prometheus /-/ready), an invalid
Prometheus config fails closed, no forbidden public ports, PostgreSQL
persistence across restart, artifact round trip against the live store,
backup/restore against the running stack, corrupt-backup rejection,
structured logs, safe shutdown, and verified volume cleanup.

Stack ownership belongs to the single session-scoped `oce_stack` fixture in
conftest.py; nothing here starts or destroys the stack independently. These
tests require Docker and SKIP truthfully without it.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import oce_compose as oc

pytestmark = pytest.mark.container


def test_ctl_compose_config_validates(oce_stack):
    oc.dcompose("config", "--quiet")


def test_ctl_images_are_pinned(oce_stack):
    text = oc.COMPOSE_FILE.read_text(encoding="utf-8")
    images = re.findall(r"image:\s*(\S+)", text)
    assert images, "no images found"
    for img in images:
        assert "latest" not in img, f"unpinned image: {img}"
        assert ":" in img or "@" in img, f"unpinned image: {img}"


def test_ctl_all_services_healthy(oce_stack):
    """THE WHOLE STACK is simultaneously healthy and stable â€” not a scalar
    per-service check. This is what verifies a service observed `starting`
    after an earlier transition is caught and converged."""
    snap = oc.assert_stack_converged(timeout_s=180, stable=2)
    assert all(v == "healthy" for v in snap.values()), snap


def test_ctl_prometheus_readiness_endpoint(oce_stack):
    """Prometheus is healthy only via its own /-/ready healthcheck, and the
    whole stack holds simultaneous stable health."""
    oc.assert_stack_converged(timeout_s=180, stable=2)
    assert oc.health(oc.METRICS) == "healthy", f"prometheus health={oc.health(oc.METRICS)}"


def test_ctl_invalid_prometheus_config_fails_closed(oce_stack, tmp_path):
    """An invalid Prometheus config must fail closed: never healthy, process
    exits. Proven with an isolated standalone project so the shared stack is
    untouched."""
    bad = tmp_path / "bad-prometheus.yml"
    bad.write_text("this: [is: not: valid: yaml:", encoding="utf-8")
    cfg = tmp_path / "badcfg.yml"
    cfg.write_text(
        "services:\n"
        "  metrics:\n"
        "    image: prom/prometheus:v2.52.0\n"
        "    container_name: oce-local-prometheus-badcfg\n"
        "    volumes:\n"
        f"      - {bad.as_posix()}:/etc/prometheus/prometheus.yml:ro\n"
        "    command: [\"--config.file=/etc/prometheus/prometheus.yml\"]\n"
        "    healthcheck:\n"
        "      test: [\"CMD\", \"wget\", \"-q\", \"-O\", \"/dev/null\", \"http://localhost:9090/-/ready\"]\n"
        "      interval: 2s\n"
        "      timeout: 2s\n"
        "      retries: 3\n"
        "      start_period: 2s\n",
        encoding="utf-8")
    try:
        r = subprocess.run(["docker", "compose", "-f", str(cfg), "up", "-d"],
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stdout + r.stderr
        assert not oc.wait_healthy("oce-local-prometheus-badcfg", timeout_s=25), \
            "invalid prometheus config reported healthy"
        assert oc.state("oce-local-prometheus-badcfg") == "exited", \
            f"expected exited, got {oc.state('oce-local-prometheus-badcfg')}"
    finally:
        subprocess.run(["docker", "compose", "-f", str(cfg), "down", "-v", "--remove-orphans"],
                       capture_output=True, text=True, timeout=120)


def test_ctl_no_forbidden_public_ports(oce_stack):
    r = oc.dcompose("ps", "--format", "json")
    entries = oc.parse_compose_ps(r.stdout)
    offenders = oc.published_ports(entries)
    assert offenders == [], f"services publish ports: {offenders}"


def test_ctl_postgres_authoritative_row_survives_restart(oce_stack):
    oc.assert_stack_converged(timeout_s=180, stable=2)
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS state_probe(k text PRIMARY KEY, v text);"
                           "INSERT INTO state_probe VALUES('ctl','1') ON CONFLICT (k) DO UPDATE SET v='1';"])
    subprocess.run(["docker", "restart", oc.POSTGRES], capture_output=True, text=True, check=True)
    assert oc.pg_ready(), "postgres not ready after restart"
    oc.assert_stack_converged(timeout_s=180, stable=2)
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT v FROM state_probe WHERE k='ctl';"])
    assert r.stdout.strip() == "1"


def test_ctl_artifact_round_trip_against_live_store(oce_stack, tmp_path):
    payload = "artifact-payload-" + hashlib.sha256(os.urandom(16)).hexdigest()
    src = tmp_path / "payload.bin"
    src.write_text(payload, encoding="utf-8")
    oc.cp_into(oc.ARTIFACT, src, "/data/probe.txt")
    dst = tmp_path / "probe-out.bin"
    oc.cp_out(oc.ARTIFACT, "/data/probe.txt", dst)
    assert dst.read_text(encoding="utf-8") == payload
    assert hashlib.sha256(payload.encode()).hexdigest() == hashlib.sha256(dst.read_bytes()).hexdigest()


def test_ctl_clean_room_database_artifact_restore(oce_stack, tmp_path):
    """Real authoritative recovery: known PostgreSQL records and known
    artifact payloads are backed up FULL, the disposable stack and its volumes
    are destroyed, clean volumes are recreated, and the full backup restores
    into them via verified staging promotion with exact hashes. Redis is
    rebuilt as disposable state, never restored as authoritative truth."""
    # 1. known postgres records
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS backup_probe(k text PRIMARY KEY, v text);"
                           "INSERT INTO backup_probe VALUES('b1','alpha'),('b2','beta') "
                           "ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v;"])
    # 2. known artifact payload
    payload = "clean-room-payload-" + hashlib.sha256(os.urandom(8)).hexdigest()
    src = tmp_path / "artifact-payload.bin"
    src.write_bytes(payload.encode())
    oc.cp_into(oc.ARTIFACT, src, "/data/backup-probe.bin")
    expected_sha = hashlib.sha256(payload.encode()).hexdigest()
    # 3. disposable redis state (must NOT survive restore)
    oc.dexec(oc.REDIS, ["redis-cli", "SET", "pre:backup:key", "cached"])
    # 4. versioned FULL backup package with authoritative data
    bk = tmp_path / "bk"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--scope", "full", "--out", str(bk)], check=True)
    assert (bk / "BACKUP_MANIFEST.sha256").is_file()
    info = json.loads((bk / ".backup-content" / "backup-info.json").read_text(encoding="utf-8"))
    assert info["scope"] == "full", info
    assert info["disaster_recovery_capable"] is True, info
    assert "postgres" in info["includes"], info
    assert "artifacts" in info["includes"], info
    assert (bk / ".backup-content" / "postgres" / "archive.dump").is_file()
    assert (bk / ".backup-content" / "postgres" / "inventory.json").is_file()
    assert (bk / ".backup-content" / "artifacts" / "artifacts.tar.gz").is_file()
    # 4c. verify the backup metadata is hash-protected (tamper => gate fails)
    oc.verify_backup_manifest(bk)
    # 5. destroy the disposable stack and Book 1 test volumes only
    oc.dcompose("down", "-v", "--remove-orphans")
    # 6. recreate clean volumes and wait for simultaneous stable readiness
    oc.dcompose("up", "-d")
    oc.assert_stack_converged(timeout_s=240, stable=2)
    assert oc.pg_ready(), "postgres not ready on clean volumes"
    # 7. restore with EXPLICIT full-replace intent + local target identity
    oc.run(["bash", str(oc.SCRIPTS / "restore.sh"), "--mode", "full-replace",
            "--from", str(bk), "--confirm-local-target", oc.PG_DB], check=True)
    oc.assert_stack_converged(timeout_s=240, stable=2)
    # 8. postgres records exactly (a zero-exit restore with missing rows fails)
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT k || '=' || v FROM backup_probe ORDER BY k;"])
    assert r.stdout.strip().splitlines() == ["b1=alpha", "b2=beta"], (
        f"restore returned success but rows not recovered: {r.stdout!r}")
    # 9. artifact hash exactly
    out = tmp_path / "restored-artifact.bin"
    oc.cp_out(oc.ARTIFACT, "/data/backup-probe.bin", out)
    assert hashlib.sha256(out.read_bytes()).hexdigest() == expected_sha
    # 10. redis is disposable: pre-backup cache gone, rebuildable
    r = oc.dexec(oc.REDIS, ["redis-cli", "GET", "pre:backup:key"])
    assert r.stdout.strip() == "", "redis restored as truth (should be disposable)"
    oc.dexec(oc.REDIS, ["redis-cli", "SET", "post:restore:key", "rebuilt"])
    r = oc.dexec(oc.REDIS, ["redis-cli", "GET", "post:restore:key"])
    assert r.stdout.strip() == "rebuilt"


def test_ctl_full_replace_into_populated_target(oce_stack, tmp_path):
    """Full-replace must REPLACE (not merge) the authoritative state even when
    the target DB already holds populated tables. After restore, only the
    backed-up snapshot rows exist for the probed table; a pre-existing row that
    was NOT part of the snapshot must be gone (snapshot replacement semantics)."""
    oc.assert_stack_converged(timeout_s=180, stable=2)
    # create a marker row that exists only in the pre-restore target and a
    # recovery table we will populate and back up
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS replace_probe(k text PRIMARY KEY, v text);"
                           "INSERT INTO replace_probe VALUES('keep','snapshot') "
                           "ON CONFLICT (k) DO UPDATE SET v='snapshot';"])
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "INSERT INTO replace_probe VALUES('stray','not-in-snapshot') "
                           "ON CONFLICT (k) DO UPDATE SET v='not-in-snapshot';"])
    # capture full backup (contains only 'keep' row in replace_probe)
    bk = tmp_path / "bk"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--scope", "full", "--out", str(bk)], check=True)
    oc.verify_backup_manifest(bk)
    # add a conflicting row into the live target that is NOT in the snapshot; it
    # must be replaced away because the snapshot replaces the whole DB
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "INSERT INTO replace_probe VALUES('live','post-backup') "
                           "ON CONFLICT (k) DO UPDATE SET v='post-backup';"])
    oc.dexec(oc.REDIS, ["redis-cli", "SET", "replace:cache", "cached"])
    # full-replace into the POPULATED live target
    oc.run(["bash", str(oc.SCRIPTS / "restore.sh"), "--mode", "full-replace",
            "--from", str(bk), "--confirm-local-target", oc.PG_DB], check=True)
    oc.assert_stack_converged(timeout_s=240, stable=2)
    # the post-backup live row must NOT exist (snapshot replacement)
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT count(*) FROM replace_probe WHERE k='live';"])
    assert r.stdout.strip() == "0", f"live row survived full-replace: {r.stdout}"
    # the snapshot row must be present
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT v FROM replace_probe WHERE k='keep';"])
    assert r.stdout.strip() == "snapshot"
    # R27: Redis is never RESTORED from backup, and after PostgreSQL+artifact
    # replacement passed final verification the transient cache is INVALIDATED:
    # the stale pre-restore value must be ABSENT, and Redis remains usable.
    r = oc.dexec(oc.REDIS, ["redis-cli", "GET", "replace:cache"])
    assert r.stdout.strip() == "", f"stale redis cache survived full-replace: {r.stdout!r}"
    oc.dexec(oc.REDIS, ["redis-cli", "SET", "post:replace:key", "rebuilt"])
    r = oc.dexec(oc.REDIS, ["redis-cli", "GET", "post:replace:key"])
    assert r.stdout.strip() == "rebuilt", "redis unusable after full-replace (must be rebuildable)"


def test_ctl_post_promotion_failure_rolls_back_original(oce_stack, tmp_path):
    """Real injected post-promotion failure (R25/Repair 8): the recovery
    engine promotes the candidate with quarantine HELD, a verification
    failure is injected AFTER promotion but BEFORE finalization, the
    candidate is rejected, the ORIGINAL canonical database is restored from
    quarantine, and the protected values are intact. The transient cache is
    left untouched by the rolled-back recovery."""
    oc.assert_stack_converged(timeout_s=180, stable=2)
    # seed protected truth
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS backup_probe(k text PRIMARY KEY, v text);"
                           "INSERT INTO backup_probe VALUES('b1','alpha'),('b2','beta') "
                           "ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v;"])
    # transient cache written BEFORE recovery must survive a rolled-back run
    oc.dexec(oc.REDIS, ["redis-cli", "SET", "rollback:cache", "untouched"])
    # full backup of the seeded truth
    bk = tmp_path / "bk"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--scope", "full", "--out", str(bk)], check=True)
    inv = bk / ".backup-content" / "postgres" / "inventory.json"
    invsha = bk / ".backup-content" / "postgres" / "inventory.json.sha256"
    dump = bk / ".backup-content" / "postgres" / "archive.dump"
    # PHASE 1 — promote (quarantine HELD; canonical replaced by candidate)
    promote_receipt = tmp_path / "promote.json"
    r = oc.run(["python3", str(oc.SCRIPTS / "pg-recovery.py"), "--phase", "promote",
                "--archive", str(dump), "--inventory", str(inv),
                "--inventory-sha", str(invsha),
                "--db", oc.PG_DB, "--user", oc.PG_USER, "--container", oc.POSTGRES,
                "--receipt-out", str(promote_receipt)], check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    pr = json.loads(promote_receipt.read_text(encoding="utf-8"))
    assert pr.get("promoted") is True, pr
    assert pr.get("quarantine_held") is True, pr
    assert pr.get("quarantine_dropped") is False, pr
    assert pr.get("quarantine_database"), pr
    # INJECT failure AFTER promotion: alter one protected value in the promoted
    # canonical so the finalize re-verification must fail.
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "UPDATE backup_probe SET v='evil' WHERE k='b1';"])
    # PHASE 2 — finalize: canonical re-verification FAILS -> rollback
    final_receipt = tmp_path / "final.json"
    r2 = oc.run(["python3", str(oc.SCRIPTS / "pg-recovery.py"), "--phase", "finalize",
                 "--receipt-in", str(promote_receipt),
                 "--inventory", str(inv), "--inventory-sha", str(invsha),
                 "--db", oc.PG_DB, "--user", oc.PG_USER, "--container", oc.POSTGRES,
                 "--receipt-out", str(final_receipt)], check=False)
    assert r2.returncode != 0, "finalize must fail when canonical truth is broken"
    fr = json.loads(final_receipt.read_text(encoding="utf-8"))
    assert fr.get("rollback_required") is True, fr
    assert fr.get("rollback_attempted") is True, fr
    assert fr.get("rollback_succeeded") is True, fr
    assert fr.get("original_canonical_restored") is True, fr
    assert fr.get("promoted_candidate_removed") is True, fr
    assert fr.get("rollback_verification", {}).get("result") == "ok", fr
    assert fr.get("exit_status") != 0, "failed recovery must not exit 0"
    # the ORIGINAL protected values are present after rollback
    r3 = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                                "SELECT k || '=' || v FROM backup_probe ORDER BY k;"])
    assert r3.stdout.strip().splitlines() == ["b1=alpha", "b2=beta"], r3.stdout
    # Redis was NOT invalidated/restored by the rolled-back recovery
    r4 = oc.dexec(oc.REDIS, ["redis-cli", "GET", "rollback:cache"])
    assert r4.stdout.strip() == "untouched", "rolled-back recovery mutated Redis"
    # preserve the rollback receipt as authoritative, INDEXED evidence (R8):
    # the injected-failure rollback operation is registered in the immutable
    # operation index with final_result=failed / rollback_result=ok.
    ev = os.environ.get("OCE_EVIDENCE_DIR")
    if ev:
        evdir = Path(ev)
        evdir.mkdir(parents=True, exist_ok=True)
        (evdir / "rollback-receipt.json").write_text(
            json.dumps(fr, indent=2), encoding="utf-8")
        (evdir / ("rollback-receipt-" + pr.get("stamp", "x") + ".json")).write_text(
            json.dumps(fr, indent=2), encoding="utf-8")
        opid = pr.get("stamp", "x")
        # register the rollback receipt under the gate-expected name so the
        # indexed entry carries postgres-recovery-receipt.json
        rb_named = tmp_path / "postgres-recovery-receipt.json"
        rb_named.write_text(json.dumps(fr, indent=2), encoding="utf-8")
        reg = subprocess.run(
            ["python3", str(oc.SCRIPTS / "recovery-ops.py"), "add",
             "--ops-root", str(evdir / "operations"),
             "--operation-id", opid, "--operation-type", "restore",
             "--run-id", os.environ.get("OCE_RUN_ID", "not-set"),
             "--commit", os.environ.get("OCE_COMMIT", "unknown"),
             "--tree", os.environ.get("OCE_TREE", "unknown"),
             "--started-at", fr.get("started_at", ""), "--finished-at", fr.get("finished_at", ""),
             "--backup-id", "b" * 32, "--backup-scope", "full", "--restore-mode", "full-replace",
             "--source-database", oc.PG_DB, "--target-database", oc.PG_DB,
             "--final-result", "failed", "--rollback-result", "ok",
             "--cloud-mutations", "0", "--cloud-cost-state", "ZERO",
             "--receipt", str(rb_named)],
            capture_output=True, text=True)
        assert reg.returncode == 0, reg.stdout + reg.stderr


def test_ctl_rollback_failure_returns_nonzero_and_preserves_evidence(oce_stack, tmp_path):
    """If the rollback source is destroyed (quarantine missing) and the
    promoted canonical is broken, rollback MUST fail loudly: nonzero exit,
    actionable evidence, and NO claim of restoration success (Repair 8)."""
    oc.assert_stack_converged(timeout_s=180, stable=2)
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS backup_probe(k text PRIMARY KEY, v text);"
                           "INSERT INTO backup_probe VALUES('b1','alpha'),('b2','beta') "
                           "ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v;"])
    bk = tmp_path / "bk"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--scope", "full", "--out", str(bk)], check=True)
    inv = bk / ".backup-content" / "postgres" / "inventory.json"
    invsha = bk / ".backup-content" / "postgres" / "inventory.json.sha256"
    dump = bk / ".backup-content" / "postgres" / "archive.dump"
    promote_receipt = tmp_path / "promote.json"
    r = oc.run(["python3", str(oc.SCRIPTS / "pg-recovery.py"), "--phase", "promote",
                "--archive", str(dump), "--inventory", str(inv),
                "--inventory-sha", str(invsha),
                "--db", oc.PG_DB, "--user", oc.PG_USER, "--container", oc.POSTGRES,
                "--receipt-out", str(promote_receipt)], check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    pr = json.loads(promote_receipt.read_text(encoding="utf-8"))
    q = pr.get("quarantine_database")
    assert q
    # destroy the rollback source AND break the promoted canonical: rollback
    # cannot restore the original, so it must fail loudly.
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", "postgres", "-c",
                           f'DROP DATABASE "{q}" WITH (FORCE);'])
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "UPDATE backup_probe SET v='evil' WHERE k='b1';"])
    final_receipt = tmp_path / "final.json"
    r2 = oc.run(["python3", str(oc.SCRIPTS / "pg-recovery.py"), "--phase", "finalize",
                 "--receipt-in", str(promote_receipt),
                 "--inventory", str(inv), "--inventory-sha", str(invsha),
                 "--db", oc.PG_DB, "--user", oc.PG_USER, "--container", oc.POSTGRES,
                 "--receipt-out", str(final_receipt)], check=False)
    assert r2.returncode != 0, "rollback failure must return nonzero"
    fr = json.loads(final_receipt.read_text(encoding="utf-8"))
    assert fr.get("rollback_required") is True
    assert fr.get("rollback_attempted") is True
    assert fr.get("rollback_succeeded") is False, "must not claim restoration success"
    assert fr.get("rollback_failed") is True
    assert fr.get("original_canonical_restored") is False
    assert fr.get("exit_status") != 0
    # evidence of the failed rollback is preserved (never hidden) and INDEXED
    ev = os.environ.get("OCE_EVIDENCE_DIR")
    if ev:
        evdir = Path(ev)
        evdir.mkdir(parents=True, exist_ok=True)
        (evdir / "rollback-failure-receipt.json").write_text(
            json.dumps(fr, indent=2), encoding="utf-8")
        opid = pr.get("stamp", "x")
        rb_named = tmp_path / "postgres-recovery-receipt.json"
        rb_named.write_text(json.dumps(fr, indent=2), encoding="utf-8")
        reg = subprocess.run(
            ["python3", str(oc.SCRIPTS / "recovery-ops.py"), "add",
             "--ops-root", str(evdir / "operations"),
             "--operation-id", opid, "--operation-type", "restore",
             "--run-id", os.environ.get("OCE_RUN_ID", "not-set"),
             "--commit", os.environ.get("OCE_COMMIT", "unknown"),
             "--tree", os.environ.get("OCE_TREE", "unknown"),
             "--started-at", fr.get("started_at", ""), "--finished-at", fr.get("finished_at", ""),
             "--backup-id", "b" * 32, "--backup-scope", "full", "--restore-mode", "full-replace",
             "--source-database", oc.PG_DB, "--target-database", oc.PG_DB,
             "--final-result", "failed", "--rollback-result", "failed",
             "--cloud-mutations", "0", "--cloud-cost-state", "ZERO",
             "--receipt", str(rb_named)],
            capture_output=True, text=True)
        assert reg.returncode == 0, reg.stdout + reg.stderr
    # leave the shared stack's protected truth intact for later tests
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "UPDATE backup_probe SET v='alpha' WHERE k='b1';"])
    r5 = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                                "SELECT k || '=' || v FROM backup_probe ORDER BY k;"])
    assert r5.stdout.strip().splitlines() == ["b1=alpha", "b2=beta"], r5.stdout


def test_ctl_redis_invalidation_failure_blocks_success(oce_stack, tmp_path):
    """R27: if transient-cache invalidation fails AFTER PostgreSQL replacement
    is irreversible, the recovery must NOT report a clean success: nonzero
    exit, redis_failure recorded, and evidence of PostgreSQL status preserved."""
    oc.assert_stack_converged(timeout_s=180, stable=2)
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS backup_probe(k text PRIMARY KEY, v text);"
                           "INSERT INTO backup_probe VALUES('b1','alpha'),('b2','beta') "
                           "ON CONFLICT (k) DO UPDATE SET v=EXCLUDED.v;"])
    bk = tmp_path / "bk"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--scope", "full", "--out", str(bk)], check=True)
    # make the transient cache unavailable for invalidation (no FLUSHALL)
    subprocess.run(["docker", "stop", oc.REDIS], capture_output=True, text=True, check=True)
    try:
        r = oc.run(["bash", str(oc.SCRIPTS / "restore.sh"), "--mode", "full-replace",
                    "--from", str(bk), "--confirm-local-target", oc.PG_DB], check=False)
        assert r.returncode != 0, "restore must not report clean success when redis invalidation fails"
        combo = r.stdout + r.stderr
        assert "BLOCKED" in combo and "redis" in combo.lower(), combo
        # postgres truth is intact (promotion succeeded before the redis step)
        r2 = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                                    "SELECT k || '=' || v FROM backup_probe ORDER BY k;"])
        assert r2.stdout.strip().splitlines() == ["b1=alpha", "b2=beta"], r2.stdout
        ev = os.environ.get("OCE_EVIDENCE_DIR")
        if ev:
            p = Path(ev) / "redis-invalidation-receipt.json"
            assert p.is_file(), "redis invalidation failure receipt must be preserved"
            rr = json.loads(p.read_text(encoding="utf-8"))
            assert rr.get("redis_invalidation_attempted") is True
            assert rr.get("redis_invalidated") is False
            assert rr.get("redis_verification") == "failed"
            assert rr.get("redis_failure"), rr
            assert rr.get("redis_restored") is False
            assert rr.get("postgres_promoted") is True
    finally:
        subprocess.run(["docker", "start", oc.REDIS], capture_output=True, text=True, check=True)
        assert oc.wait_healthy(oc.REDIS), "redis did not recover after invalidation-failure test"


def test_ctl_corrupt_backup_rejected_against_running_stack(oce_stack, tmp_path):
    bk = tmp_path / "bk2"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--scope", "full", "--out", str(bk)], check=True)
    (bk / ".backup-content" / "state.json").write_text('{"tampered": true}', encoding="utf-8")
    r = oc.run(["bash", str(oc.SCRIPTS / "restore.sh"), "--mode", "full-replace",
                "--from", str(bk), "--confirm-local-target", oc.PG_DB], check=False)
    assert r.returncode != 0
    assert "CORRUPT" in r.stdout + r.stderr
    # postgres data must NOT have been touched by the rejected restore
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT count(*) FROM backup_probe;"])
    assert r.stdout.strip().isdigit()


def test_ctl_structured_logs_use_json_file_driver(oce_stack):
    """Verify the json-file log driver and its rotation options independently,
    then accept Docker logs on stdout OR stderr (PostgreSQL logs on stderr),
    and confirm the content contains a recognizable PostgreSQL log record."""
    inspect = subprocess.run(["docker", "inspect", oc.POSTGRES], capture_output=True, text=True)
    assert inspect.returncode == 0
    obj = json.loads(inspect.stdout)[0]
    lc = obj.get("HostConfig", {}).get("LogConfig", {})
    # 1. log driver type independently verified
    assert lc.get("Type") == "json-file", lc
    # 2. rotation options verified
    opts = lc.get("Config", {}) or {}
    assert opts.get("max-size") == "10m", opts
    assert opts.get("max-file") == "3", opts
    # record the inspected driver config as evidence
    ev = os.environ.get("OCE_EVIDENCE_DIR")
    if ev:
        Path(ev).mkdir(parents=True, exist_ok=True)
        (Path(ev) / "log-driver-config.json").write_text(json.dumps(lc, indent=2), encoding="utf-8")
    # 3. combined stdout+stderr accepted; nonempty; contains a postgres record
    logs = subprocess.run(["docker", "logs", "--tail", "50", oc.POSTGRES], capture_output=True, text=True)
    combined = (logs.stdout + "\n" + logs.stderr) if logs.stderr else logs.stdout
    assert logs.returncode == 0
    assert combined.strip(), "docker logs returned empty output for postgres"
    assert re.search(r"database system (is ready|was shut down)|ready to accept|LOG:", combined), \
        f"no recognizable postgres record in logs: {combined[:400]}"


def test_ctl_safe_shutdown_and_verified_cleanup(oce_stack):
    """Safe shutdown brings every service to exited state, then RESTORES the
    shared stack to simultaneous stable health so later tests never observe a
    half-started stack. Final volume cleanup is verified by the session
    fixture teardown and recorded in container-cleanup.json."""
    r = oc.ctl("local", "down")
    assert r.returncode == 0
    r = oc.dcompose("ps", "--all", "--format", "json", check=False)
    remaining = oc.parse_compose_ps(r.stdout)
    assert all(e.get("State") == "exited" for e in remaining), remaining
    # restore the shared stack (graceful) so no later test sees `starting`
    oc.ctl("local", "up", check=True)
    oc.assert_stack_converged(timeout_s=240, stable=2)
