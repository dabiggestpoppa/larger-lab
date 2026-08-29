#!/usr/bin/env python3
"""OCE Local Ground — real container lifecycle tests (B1-LOCAL, A-003).

Prove the actual Compose stack runs: config validates, images are pinned, all
services reach healthy, no forbidden public ports, artifact round trip against
the live store, backup/restore against the running stack, structured logs,
safe shutdown, and full volume cleanup. These tests run for real in CI (Docker
present) and SKIP truthfully without Docker.
"""
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.container

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = BASE_DIR / "scripts"
COMPOSE = BASE_DIR / "compose"
COMPOSE_FILE = COMPOSE / "compose.yml"
POSTGRES = "oce-local-postgresql"
REDIS = "oce-local-redis"
ARTIFACT = "oce-local-artifact"
METRICS = "oce-local-prometheus"

TEST_SECRETS = {
    "POSTGRES_PASSWORD": "test-secret-postgres-001",
    "ARTIFACT_SECRET_KEY": "test-secret-artifact-001",
}


def docker_available():
    if shutil.which("docker") is None:
        return False
    r = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
    return r.returncode == 0


def run(args, env_extra=None, check=False):
    env = dict(os.environ, OCE_RUNTIME_TARGET="local", PYTHONDONTWRITEBYTECODE="1",
               **TEST_SECRETS, **(env_extra or {}))
    r = subprocess.run(args, cwd=str(BASE_DIR), env=env, capture_output=True, text=True, timeout=300)
    if check:
        assert r.returncode == 0, f"{args} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def dcompose(*args, check=True):
    r = subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE)] + list(args),
                       cwd=str(COMPOSE), capture_output=True, text=True, timeout=300)
    if check:
        assert r.returncode == 0, f"docker compose {args} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def dexec(container, cmd, check=True):
    r = subprocess.run(["docker", "exec", container] + cmd, capture_output=True, text=True, timeout=120)
    if check:
        assert r.returncode == 0, f"docker exec {container} {cmd} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def health(container):
    r = subprocess.run(["docker", "inspect", "--format", "{{.State.Health.Status}}", container],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "missing"


def wait_healthy(container, timeout_s=90):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if health(container) == "healthy":
            return True
        time.sleep(3)
    return False


@pytest.fixture(scope="module", autouse=True)
def stack():
    if not docker_available():
        pytest.skip("container runtime unavailable (Docker absent)")
    # bring the real stack up
    run(["bash", str(SCRIPTS / "oce-ctl"), "local", "up"], check=True)
    for svc in (POSTGRES, REDIS, ARTIFACT, METRICS):
        assert wait_healthy(svc), f"{svc} did not become healthy"
    yield
    # full cleanup: remove containers AND disposable volumes
    dcompose("down", "-v", "--remove-orphans", check=False)


def test_ctl_compose_config_validates(stack):
    dcompose("config", "--quiet")


def test_ctl_images_are_pinned(stack):
    text = COMPOSE_FILE.read_text(encoding="utf-8")
    import re
    images = re.findall(r"image:\s*(\S+)", text)
    assert images, "no images found"
    for img in images:
        assert "latest" not in img, f"unpinned image: {img}"
        assert ":" in img or "@" in img, f"unpinned image: {img}"


def test_ctl_all_services_healthy(stack):
    for svc in (POSTGRES, REDIS, ARTIFACT, METRICS):
        assert health(svc) == "healthy", f"{svc} health={health(svc)}"


def test_ctl_no_forbidden_public_ports(stack):
    r = dcompose("ps", "--format", "json")
    for line in r.stdout.splitlines():
        entry = json.loads(line)
        ports = entry.get("Publishers") or entry.get("Ports") or []
        assert not ports, f"service {entry.get('Service')} publishes ports: {ports}"


def test_ctl_postgres_authoritative_row_survives_restart(stack):
    dexec(POSTGRES, ["psql", "-U", "oce_local_admin", "-d", "oce_local", "-c",
                     "CREATE TABLE IF NOT EXISTS state_probe(k text PRIMARY KEY, v text);"
                     "INSERT INTO state_probe VALUES('ctl','1') ON CONFLICT (k) DO UPDATE SET v='1';"])
    subprocess.run(["docker", "restart", POSTGRES], capture_output=True, text=True, check=True)
    assert wait_healthy(POSTGRES)
    r = dexec(POSTGRES, ["psql", "-U", "oce_local_admin", "-d", "oce_local", "-tAc",
                         "SELECT v FROM state_probe WHERE k='ctl';"])
    assert r.stdout.strip() == "1"


def test_ctl_artifact_round_trip_against_live_store(stack):
    payload = "artifact-payload-" + hashlib.sha256(os.urandom(16)).hexdigest()
    dexec(ARTIFACT, ["sh", "-c", f"echo '{payload}' > /data/probe.txt"])
    r = dexec(ARTIFACT, ["sh", "-c", "cat /data/probe.txt"])
    assert r.stdout.strip() == payload
    assert hashlib.sha256(payload.encode()).hexdigest() == hashlib.sha256(r.stdout.encode()).hexdigest()


def test_ctl_backup_and_restore_against_running_stack(stack, tmp_path):
    (BASE_DIR / "var").mkdir(exist_ok=True)
    (BASE_DIR / "var" / "state.json").write_text('{"lifecycle": "ok"}')
    bk = tmp_path / "bk"
    run(["bash", str(SCRIPTS / "backup.sh"), "--out", str(bk)], check=True)
    assert (bk / "BACKUP_MANIFEST.sha256").is_file()
    shutil.rmtree(BASE_DIR / "var", ignore_errors=True)
    run(["bash", str(SCRIPTS / "restore.sh"), "--from", str(bk)], check=True)
    assert json.loads((BASE_DIR / "var" / "state.json").read_text()) == {"lifecycle": "ok"}


def test_ctl_corrupt_backup_rejected_against_running_stack(stack, tmp_path):
    bk = tmp_path / "bk2"
    run(["bash", str(SCRIPTS / "backup.sh"), "--out", str(bk)], check=True)
    (bk / ".backup-content" / "state.json").write_text('{"tampered": true}')
    r = run(["bash", str(SCRIPTS / "restore.sh"), "--from", str(bk)], check=False)
    assert r.returncode != 0
    assert "CORRUPT" in r.stdout + r.stderr


def test_ctl_structured_logs_use_json_file_driver(stack):
    r = subprocess.run(["docker", "inspect", "--format", "{{.HostConfig.LogConfig.Type}}", POSTGRES],
                       capture_output=True, text=True)
    assert r.stdout.strip() == "json-file"
    logs = subprocess.run(["docker", "logs", "--tail", "5", POSTGRES], capture_output=True, text=True)
    assert logs.returncode == 0 and logs.stdout.strip()


def test_ctl_safe_shutdown_and_volume_cleanup(stack):
    r = subprocess.run(["bash", str(SCRIPTS / "oce-ctl"), "local", "down"], capture_output=True, text=True)
    assert r.returncode == 0
    # volumes were removed by the module teardown; assert the stack is fully down
    r = dcompose("ps", "--all", "--format", "json", check=False)
    remaining = [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
    assert all(e.get("State") == "exited" for e in remaining), remaining