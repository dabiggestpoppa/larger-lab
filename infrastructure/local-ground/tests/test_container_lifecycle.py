#!/usr/bin/env python3
"""OCE Local Ground — real container lifecycle tests (B1-LOCAL, A-003).

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
    for svc in oc.ALL_SERVICES:
        assert oc.health(svc) == "healthy", f"{svc} health={oc.health(svc)}"


def test_ctl_prometheus_readiness_endpoint(oce_stack):
    """Prometheus is healthy only via its own /-/ready healthcheck."""
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
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS state_probe(k text PRIMARY KEY, v text);"
                           "INSERT INTO state_probe VALUES('ctl','1') ON CONFLICT (k) DO UPDATE SET v='1';"])
    subprocess.run(["docker", "restart", oc.POSTGRES], capture_output=True, text=True, check=True)
    assert oc.pg_ready(), "postgres not ready after restart"
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
    """Real authoritative recovery (R13): known PostgreSQL records and known
    artifact payloads are backed up, the disposable stack and its volumes are
    destroyed, clean volumes are recreated, and the backup restores into them
    with exact hashes. Redis is rebuilt as disposable state, never restored
    as authoritative truth."""
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
    # 4. versioned backup package with authoritative data
    bk = tmp_path / "bk"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--out", str(bk)], check=True)
    assert (bk / "BACKUP_MANIFEST.sha256").is_file()
    info = json.loads((bk / "backup-info.json").read_text(encoding="utf-8"))
    assert "postgres" in info["includes"], info
    assert "artifacts" in info["includes"], info
    assert (bk / ".backup-content" / "postgres" / "dump.sql").is_file()
    assert (bk / ".backup-content" / "artifacts" / "artifacts.tar.gz").is_file()
    # 5. destroy the disposable stack and Book 1 test volumes only
    oc.dcompose("down", "-v", "--remove-orphans")
    # 6. recreate clean volumes and wait for truthful readiness
    oc.dcompose("up", "-d")
    assert oc.wait_all_healthy(), "stack not healthy on clean volumes"
    assert oc.pg_ready(), "postgres not ready on clean volumes"
    # 7. restore
    oc.run(["bash", str(oc.SCRIPTS / "restore.sh"), "--from", str(bk)], check=True)
    # 8. postgres records exactly
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tA",
                               "SELECT k || '=' || v FROM backup_probe ORDER BY k;"])
    assert r.stdout.strip().splitlines() == ["b1=alpha", "b2=beta"], r.stdout
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


def test_ctl_corrupt_backup_rejected_against_running_stack(oce_stack, tmp_path):
    bk = tmp_path / "bk2"
    oc.run(["bash", str(oc.SCRIPTS / "backup.sh"), "--out", str(bk)], check=True)
    (bk / ".backup-content" / "state.json").write_text('{"tampered": true}', encoding="utf-8")
    r = oc.run(["bash", str(oc.SCRIPTS / "restore.sh"), "--from", str(bk)], check=False)
    assert r.returncode != 0
    assert "CORRUPT" in r.stdout + r.stderr


def test_ctl_structured_logs_use_json_file_driver(oce_stack):
    r = subprocess.run(["docker", "inspect", "--format", "{{.HostConfig.LogConfig.Type}}", oc.POSTGRES],
                       capture_output=True, text=True)
    assert r.stdout.strip() == "json-file"
    logs = subprocess.run(["docker", "logs", "--tail", "5", oc.POSTGRES], capture_output=True, text=True)
    assert logs.returncode == 0 and logs.stdout.strip()


def test_ctl_safe_shutdown_and_verified_cleanup(oce_stack):
    """Safe shutdown; final volume cleanup is verified by the session
    fixture teardown and recorded in container-cleanup.json."""
    r = oc.ctl("local", "down")
    assert r.returncode == 0
    r = oc.dcompose("ps", "--all", "--format", "json", check=False)
    remaining = oc.parse_compose_ps(r.stdout)
    assert all(e.get("State") == "exited" for e in remaining), remaining
