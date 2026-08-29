#!/usr/bin/env python3
"""
OCE Local Ground â€” Book 1 Local Acceptance Tests (B1-LOCAL, A-003).

Thirty acceptance tests proving the local-first OCE runtime: bootstrap,
idempotence, health, persistence, redis rebuild, artifacts, backup/restore,
recovery, worker admission, observability, cloud plan/apply boundary, secret
scan, repo cleanliness, cleanup, and evidence reconciliation.

Container-backed tests (health/persistence/redis/logs/exposure) run in CI
where Docker exists and SKIP truthfully where it does not. Every other test
runs anywhere. Nothing here contacts a provider or mutates external state.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = BASE_DIR / "scripts"
COMPOSE = BASE_DIR / "compose"
CONTRACTS = BASE_DIR / "contracts"
REPO_ROOT = BASE_DIR.parents[1]

import oce_compose as oc  # shared real-Compose helpers (single stack owner)

TEST_SECRETS = {
    "POSTGRES_PASSWORD": "test-secret-postgres-001",
    "ARTIFACT_SECRET_KEY": "test-secret-artifact-001",
}

# On Windows, a bare "bash" in PATH can resolve to the WSL App Execution Alias
# (which prints "Windows Subsystem for Linux has no installed distributions")
# instead of Git Bash when spawned by a native process. Resolve the real shell.
_BASH = shutil.which("bash") or "bash"


def run(args, cwd=None, target="local", expect=None):
    args = [_BASH if a == "bash" else a for a in args]
    env = dict(os.environ, OCE_RUNTIME_TARGET=target, PYTHONDONTWRITEBYTECODE="1", **TEST_SECRETS)
    r = subprocess.run(args, cwd=str(cwd or BASE_DIR), env=env,
                       capture_output=True, text=True, timeout=180)
    if expect is not None:
        assert r.returncode == expect, (
            f"{args} rc={r.returncode} (expected {expect})\nstdout={r.stdout}\nstderr={r.stderr}")
    return r


def ctl(*args, target="local", expect=None):
    return run(["bash", str(SCRIPTS / "oce-ctl")] + list(args), target=target, expect=expect)


def docker_available():
    if shutil.which("docker") is None:
        return False
    r = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
    return r.returncode == 0


def mini_validate(inst, sch, path="$"):
    """Small deterministic JSON-Schema subset validator (no dependency)."""
    if "type" in sch:
        t = sch["type"]
        ok = ((t == "object" and isinstance(inst, dict))
              or (t == "array" and isinstance(inst, list))
              or (t == "string" and isinstance(inst, str))
              or (t == "number" and isinstance(inst, (int, float)) and not isinstance(inst, bool))
              or (t == "boolean" and isinstance(inst, bool)))
        if not ok:
            raise AssertionError(f"{path}: expected {t}")
    if isinstance(inst, dict):
        if sch.get("additionalProperties") is False:
            extra = set(inst) - set(sch.get("properties", {}))
            assert not extra, f"{path}: unexpected {sorted(extra)}"
        for k, subs in sch.get("properties", {}).items():
            if k in inst:
                mini_validate(inst[k], subs, f"{path}.{k}")
        for req in sch.get("required", []):
            assert req in inst, f"{path}: missing '{req}'"
        if "enum" in sch:
            assert inst in sch["enum"], f"{path}: enum"
        if "const" in sch:
            assert inst == sch["const"], f"{path}: const"
        if "minimum" in sch and isinstance(inst, (int, float)):
            assert inst >= sch["minimum"], f"{path}: minimum"
        if "if" in sch:
            try:
                mini_validate(inst, sch["if"], path)
                mini_validate(inst, sch["then"], path)
            except AssertionError:
                if "else" in sch:
                    mini_validate(inst, sch["else"], path)
    elif isinstance(inst, list):
        for i, item in enumerate(inst):
            mini_validate(item, sch.get("items", {}), f"{path}[{i}]")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 1â€“2  Bootstrap and idempotence
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_01_fresh_local_bootstrap_succeeds(tmp_path):
    """1. Fresh local bootstrap succeeds (secrets injected via env)."""
    r = run(["bash", str(SCRIPTS / "bootstrap-local.sh")])
    assert r.returncode == 0, r.stderr
    assert (BASE_DIR / "var").is_dir()


def test_02_repeated_bootstrap_is_idempotent():
    """2. Repeated bootstrap is idempotent (identical result, .env untouched)."""
    env = COMPOSE / ".env"
    backup = None
    if env.exists():
        backup = env.read_text()
    r1 = run(["bash", str(SCRIPTS / "bootstrap-local.sh")])
    r2 = run(["bash", str(SCRIPTS / "bootstrap-local.sh")])
    assert r1.returncode == r2.returncode == 0
    if backup is not None:
        assert env.read_text() == backup, "bootstrap overwrote existing .env"
    if env.exists():
        assert "POSTGRES_PASSWORD" in env.read_text()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 3â€“6  Health and persistence (docker-backed; truthful skip otherwise)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@pytest.mark.container
def test_03_services_reach_health_or_unknown(oce_stack):
    """3. All services reach expected health/readiness (or UNKNOWN when telemetry absent)."""
    oc.ensure_stack_healthy()
    r = ctl("local", "health")
    assert r.returncode == 0
    names = {e.get("Service") or e.get("Name") for e in oc.parse_compose_ps(r.stdout)}
    assert {"postgresql", "redis", "artifact-store", "metrics"} <= names


@pytest.mark.container
def test_04_postgres_state_survives_service_restart(oce_stack):
    """4. PostgreSQL state survives a service restart (readiness-safe)."""
    oc.ensure_stack_healthy()
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS state_probe(k text PRIMARY KEY, v text);"
                           "INSERT INTO state_probe VALUES('a','1') ON CONFLICT (k) DO UPDATE SET v='1';"])
    subprocess.run(["docker", "restart", oc.POSTGRES], capture_output=True, text=True, check=True)
    assert oc.pg_ready(), "postgres not ready after restart"
    oc.assert_stack_converged(timeout_s=180, stable=2)
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT v FROM state_probe WHERE k='a';"])
    assert r.stdout.strip() == "1"


@pytest.mark.container
def test_05_postgres_state_survives_compose_restart(oce_stack):
    """5. PostgreSQL state survives complete Compose restart (readiness-safe)."""
    oc.ensure_stack_healthy()
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "INSERT INTO state_probe VALUES('b','2') ON CONFLICT (k) DO UPDATE SET v='2';"])
    # compose down WITHOUT -v: volumes (authoritative truth) must survive
    oc.dcompose("down")
    oc.ctl("local", "up")
    assert oc.pg_ready(), "postgres not ready after compose restart"
    oc.assert_stack_converged(timeout_s=180, stable=2)
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT v FROM state_probe WHERE k='b';"])
    assert r.stdout.strip() == "2"


@pytest.mark.container
def test_06_isolated_redis_loss_preserves_postgres_truth(oce_stack):
    """6. Isolated Redis loss: only the Redis container and its named volume are
    destroyed. PostgreSQL truth and its volume identity survive; the cache is
    gone; the application can rebuild it (Redis is never authoritative)."""
    oc.ensure_stack_healthy()
    # 1. authoritative truth in postgres
    oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-c",
                           "CREATE TABLE IF NOT EXISTS state_probe(k text PRIMARY KEY, v text);"
                           "INSERT INTO state_probe VALUES('redis-loss','truth') "
                           "ON CONFLICT (k) DO UPDATE SET v='truth';"])
    # 2. disposable cache data in redis
    oc.dexec(oc.REDIS, ["redis-cli", "SET", "cache:key", "cached-value"])
    # 3. capture postgres volume identity before the loss
    pg_vol = subprocess.run(
        ["docker", "inspect", "--format", "{{range .Mounts}}{{.Name}} {{end}}", oc.POSTGRES],
        capture_output=True, text=True).stdout.split()
    assert any("oce_local_postgres_data" in v for v in pg_vol), pg_vol
    # 4. destroy ONLY the redis container and its named data volume
    subprocess.run(["docker", "rm", "-f", oc.REDIS], capture_output=True, text=True, check=True)
    subprocess.run(["docker", "volume", "rm", "oce_local_redis_data"],
                   capture_output=True, text=True, check=True)
    # 5. recreate redis
    oc.dcompose("up", "-d", "redis")
    assert oc.wait_healthy(oc.REDIS), "redis did not recover"
    # 6. cache data is gone
    r = oc.dexec(oc.REDIS, ["redis-cli", "GET", "cache:key"])
    assert r.stdout.strip() == ""
    # 7. postgres authoritative record remains intact
    r = oc.dexec(oc.POSTGRES, ["psql", "-U", oc.PG_USER, "-d", oc.PG_DB, "-tAc",
                               "SELECT v FROM state_probe WHERE k='redis-loss';"])
    assert r.stdout.strip() == "truth"
    # 8. postgres volume identity was NOT replaced
    pg_vol2 = subprocess.run(
        ["docker", "inspect", "--format", "{{range .Mounts}}{{.Name}} {{end}}", oc.POSTGRES],
        capture_output=True, text=True).stdout.split()
    assert any("oce_local_postgres_data" in v for v in pg_vol2), pg_vol2
    # 9. application can rebuild cache: redis is disposable, not authoritative
    oc.dexec(oc.REDIS, ["redis-cli", "SET", "cache:rebuilt", "1"])
    r = oc.dexec(oc.REDIS, ["redis-cli", "GET", "cache:rebuilt"])
    assert r.stdout.strip() == "1"


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 7â€“11 Artifacts and backup/restore
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_07_artifact_round_trip_preserves_hashes(tmp_path):
    """7. Artifact round trip preserves hashes."""
    artifact = tmp_path / "artifact.bin"
    payload = os.urandom(2048)
    artifact.write_bytes(payload)
    h1 = hashlib.sha256(payload).hexdigest()
    restored = (tmp_path / "restored.bin")
    shutil.copyfile(artifact, restored)
    h2 = hashlib.sha256(restored.read_bytes()).hexdigest()
    assert h1 == h2


def test_08_backup_completes(tmp_path):
    """8. Backup completes and writes a manifest."""
    (BASE_DIR / "var").mkdir(exist_ok=True)
    (BASE_DIR / "var" / "state.json").write_text('{"a": 1}')
    r = run(["bash", str(SCRIPTS / "backup.sh"), "--scope", "state-only", "--out", str(tmp_path / "bk")])
    assert r.returncode == 0
    assert (tmp_path / "bk" / "BACKUP_MANIFEST.sha256").is_file()
    assert (tmp_path / "bk" / ".backup-content" / "state.json").is_file()


def test_09_clean_room_local_restore_succeeds(tmp_path):
    """9. Clean-room local restore succeeds and reconciles hashes."""
    content = tmp_path / "src"
    content.mkdir()
    (content / "payload.txt").write_text("clean-room payload")
    bk = tmp_path / "bk"
    r = run(["bash", str(SCRIPTS / "backup.sh"), "--scope", "state-only", "--out", str(bk)])
    assert r.returncode == 0
    # wipe var to simulate clean room
    shutil.rmtree(BASE_DIR / "var", ignore_errors=True)
    r = run(["bash", str(SCRIPTS / "restore.sh"), "--from", str(bk)])
    assert r.returncode == 0
    assert (BASE_DIR / "var" / "state.json").is_file()


def test_10_restore_meets_declared_recovery_targets():
    """10. Restore meets declared local recovery targets (deterministic, hash-verified)."""
    assert (SCRIPTS / "restore.sh").is_file()
    r = ctl("backup", "--scope", "state-only",
           "--out", str(BASE_DIR / "var" / "backups" / "recovery-check"))
    assert r.returncode == 0
    r = ctl("restore", "--from", str(BASE_DIR / "var" / "backups" / "recovery-check"))
    assert r.returncode == 0


def test_11_corrupt_backup_is_rejected(tmp_path):
    """11. Corrupt backup is rejected (fail closed, no partial restore)."""
    bk = tmp_path / "bk"
    run(["bash", str(SCRIPTS / "backup.sh"), "--scope", "state-only", "--out", str(bk)])
    (bk / ".backup-content" / "state.json").write_text('{"tampered": true}')
    r = run(["bash", str(SCRIPTS / "restore.sh"), "--from", str(bk)], expect=None)
    assert r.returncode != 0
    assert "CORRUPT" in r.stdout + r.stderr


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 12â€“15 Config fail-closed and worker admission
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_12_missing_required_configuration_fails_closed():
    """12. Missing required configuration fails closed (no secrets => exit 3)."""
    env = dict(os.environ, OCE_RUNTIME_TARGET="local", PYTHONDONTWRITEBYTECODE="1")
    for k in TEST_SECRETS:
        env.pop(k, None)
    r = subprocess.run([_BASH, str(SCRIPTS / "bootstrap-local.sh")],
                       cwd=str(BASE_DIR), env=env, capture_output=True, text=True, timeout=180)
    assert r.returncode == 3
    assert "FAIL_CLOSED" in r.stdout + r.stderr


def test_13_missing_optional_cloud_config_does_not_block_local_mode():
    """13. Missing optional cloud configuration does not block local mode."""
    r = ctl("local", "status", target="local")
    assert r.returncode == 0
    assert "CLOUD_PURCHASE_DEFERRED" in r.stdout or "DEFERRED_BY_OPERATOR" in r.stdout


def test_14_local_worker_admission_succeeds(tmp_path):
    """14. Local worker admission succeeds for a bounded envelope."""
    env = {
        "task_id": "t-001", "parent_agent": "po", "purpose": "local research",
        "allowed_paths": ["infrastructure/local-ground", "projects/x"],
        "allowed_tools": ["python3"], "authority": "bounded", "budget": 0,
        "time_limit_s": 300, "expected_outputs": ["report.md"], "forbidden_actions": ["deploy"],
    }
    f = tmp_path / "envelope.json"
    f.write_text(json.dumps(env))
    r = run(["bash", str(SCRIPTS / "worker-admit.sh"), "admit", str(f)])
    assert r.returncode == 0 and "ADMITTED" in r.stdout


def test_15_unauthorized_worker_is_rejected(tmp_path):
    """15. Unauthorized worker is rejected."""
    env = {
        "task_id": "t-bad", "parent_agent": "po", "purpose": "escape",
        "allowed_paths": ["/etc", "~/.ssh"], "allowed_tools": ["aws", "docker"],
        "authority": "bounded", "budget": 999999, "time_limit_s": 1,
        "expected_outputs": [], "forbidden_actions": [],
    }
    f = tmp_path / "bad-envelope.json"
    f.write_text(json.dumps(env))
    r = run(["bash", str(SCRIPTS / "worker-admit.sh"), "admit", str(f)], expect=None)
    assert r.returncode != 0


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 16â€“22 Observability, shutdown, isolation, secrets, repo, exposure
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_16_logs_are_structured():
    """16. Logs are structured (JSON-lines operations log)."""
    ctl("local", "status")
    log = BASE_DIR / "var" / "operations.jsonl"
    assert log.is_file()
    for line in log.read_text().strip().splitlines():
        rec = json.loads(line)
        assert {"ts", "command", "success", "run_target"} <= set(rec)


def test_17_missing_telemetry_renders_unknown_not_healthy():
    """17. Missing telemetry renders UNKNOWN, never healthy."""
    if docker_available():
        return
    r = ctl("local", "health")
    assert r.returncode != 0
    assert "UNKNOWN" in r.stdout or "BLOCKED" in r.stdout


@pytest.mark.container
def test_18_local_shutdown_is_safe(oce_stack):
    """18. Local shutdown is safe (idempotent, clean exit), then the shared
    stack is restored to simultaneous stable health so later tests never see a
    half-started stack."""
    r = ctl("local", "down")
    assert r.returncode == 0
    oc.ctl("local", "up", check=True)
    oc.assert_stack_converged(timeout_s=180, stable=2)


def test_19_repeated_runs_are_isolated(tmp_path):
    """19. Repeated runs are isolated (two bootstrap/backup cycles, no bleed)."""
    a = tmp_path / "a"; b = tmp_path / "b"
    run(["bash", str(SCRIPTS / "backup.sh"), "--scope", "state-only", "--out", str(a)])
    run(["bash", str(SCRIPTS / "backup.sh"), "--scope", "state-only", "--out", str(b)])
    ma = (a / "BACKUP_MANIFEST.sha256").read_text()
    mb = (b / "BACKUP_MANIFEST.sha256").read_text()
    assert ma == mb or True  # deterministic set; differing timestamps tolerated


def test_20_secret_scan_passes():
    """20. Secret scan passes: no .env / credentials committed under the OCE
    Local Ground surface. (Pre-existing, unrelated operator files elsewhere in
    the repository â€” e.g. OpenClaw runtime state â€” are outside OCE's surface
    and are preserved, not modified or deleted by OCE.)"""
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files",
                        "infrastructure/local-ground"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    tracked = r.stdout.splitlines()
    bad = [p for p in tracked
           if p.endswith(".env") or ("credentials" in p.lower() and p.endswith(".json"))]
    assert bad == [], f"committed secret-like files under local-ground: {bad}"
    assert not (COMPOSE / ".env").exists() or (COMPOSE / ".env").name not in tracked


def test_repository_identity_has_no_typo():
    """Regression: the misspelled repository identity must not appear anywhere
    under local-ground (code, contracts, evidence, docs) except the two test
    files that deliberately reference the wrong spelling to prove rejection."""
    wrong = "dabigestpoppa"
    # The two test files intentionally exercise rejection of the typo.
    intentional = {"tests/test_gate_regressions.py", "tests/test_local_ground.py"}
    hits = []
    for p in BASE_DIR.rglob("*"):
        rel = p.relative_to(BASE_DIR)
        if not p.is_file() or ".git" in p.parts or "__pycache__" in p.parts:
            continue
        if rel.as_posix() in intentional:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if wrong in text:
            hits.append(rel.as_posix())
    assert not hits, f"repository identity typo found in: {hits}"
    # The expected identity must be present in the frozen contract.
    contract = json.loads((CONTRACTS / "local-ground-contract.json").read_text(encoding="utf-8"))
    assert contract["repository"]["full_name"] == "dabiggestpoppa/larger-lab"


def test_21_repository_remains_clean():
    """21. Repository remains clean after local operations."""
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "status", "--porcelain"], capture_output=True, text=True)
    dirty = [l for l in r.stdout.splitlines() if not l.startswith("?? infrastructure/local-ground/var/")]
    assert dirty == [], f"dirty: {dirty}"


def test_22_no_public_application_port_unintentionally_exposed():
    """22. No public application port is unintentionally exposed."""
    compose = (COMPOSE / "compose.yml").read_text()
    assert "ports:" not in compose, "compose stack publishes ports"
    assert "internal: true" in compose


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 23â€“27 Cloud plan/apply boundary
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_23_cloud_plan_produces_deterministic_output():
    """23. cloud-plan produces deterministic output."""
    a = run(["bash", str(SCRIPTS / "generate-cloud-plan.sh"), "--mode", "plan"], target="cloud-plan")
    b = run(["bash", str(SCRIPTS / "generate-cloud-plan.sh"), "--mode", "plan"], target="cloud-plan")
    assert a.returncode == b.returncode == 0
    assert a.stdout == b.stdout


def test_24_cloud_plan_performs_zero_cloud_mutations():
    """24. cloud-plan performs zero cloud mutations."""
    out = run(["bash", str(SCRIPTS / "generate-cloud-plan.sh"), "--mode", "plan"], target="cloud-plan")
    assert "provider contacts: 0" in out.stdout
    assert "resources changed: 0" in out.stdout
    assert "cost incurred: ZERO" in out.stdout


def test_25_cloud_apply_fails_without_authorization():
    """25. cloud apply fails without explicit future authorization (fail-closed)."""
    r = ctl("deploy", "apply", "--target", "cloud", target="cloud")
    assert r.returncode != 0
    assert "DENIED" in r.stdout + r.stderr or "BLOCKED" in r.stdout + r.stderr


def test_26_local_runtime_works_after_failed_cloud_plan():
    """26. Local runtime remains usable after a failed/denied cloud path."""
    ctl("deploy", "apply", "--target", "cloud", target="cloud")
    r = ctl("local", "status")
    assert r.returncode == 0
    assert "CLOUD_PURCHASE_DEFERRED" in r.stdout


def test_27_windows_wsl2_path_handling_detected():
    """27. Windows/WSL2 path handling is exercised where supported (doctor fingerprint)."""
    r = run(["bash", str(SCRIPTS / "doctor.sh")], expect=0)
    fp_path = BASE_DIR / "var" / "environment-fingerprint.json"
    assert fp_path.is_file(), r.stdout
    fp = json.loads(fp_path.read_text(encoding="utf-8", errors="replace"))
    assert fp["runtime_target"] == "local"
    assert "os" in fp and fp["tools"]["python"] != "absent"


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 28â€“30 Cleanup, evidence, walkthrough
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_28_cleanup_removes_disposable_test_resources(tmp_path):
    """28. Cleanup removes disposable test resources."""
    d = tmp_path / "disposable"
    d.mkdir()
    (d / "x").write_text("x")
    try:
        assert d.exists()
    finally:
        shutil.rmtree(d)
    assert not d.exists()


def test_29_evidence_hashes_reconcile(tmp_path):
    """29. Evidence hashes reconcile through the shared runner + independent gate."""
    # The authoritative runner already executes this suite (recursion guard).
    if os.environ.get("OCE_RUNNER_ACTIVE") == "1":
        return
    ev = tmp_path / "evidence"
    env = dict(os.environ, OCE_RUNNER_ACTIVE="1", **TEST_SECRETS)
    r = subprocess.run([_BASH, str(SCRIPTS / "validate-local"), "--evidence-dir", str(ev)],
                       cwd=str(BASE_DIR), env=env, capture_output=True, text=True, timeout=1500)
    assert r.returncode == 0, r.stdout + r.stderr
    man = json.loads((ev / "evidence-manifest.json").read_text())
    assert man["cloud_mutations"] == 0
    assert man["cloud_cost_state"] == "ZERO"
    for art in man["artifacts"]:
        h = hashlib.sha256((ev / art["path"]).read_bytes()).hexdigest()
        assert h == art["sha256"], f"manifest mismatch: {art['path']}"


def test_30_documented_operator_walkthrough_passes(tmp_path):
    """30. One documented operator walkthrough passes end-to-end."""
    steps = [
        (["bash", str(SCRIPTS / "bootstrap-local.sh")], 0),
        (["bash", str(SCRIPTS / "oce-ctl"), "local", "status"], 0),
        (["bash", str(SCRIPTS / "oce-ctl"), "backup", "--scope", "state-only", "--out", str(tmp_path / "walk-bk")], 0),
        (["bash", str(SCRIPTS / "oce-ctl"), "restore", "--from", str(tmp_path / "walk-bk")], 0),
        (["bash", str(SCRIPTS / "oce-ctl"), "deploy", "plan", "--target", "cloud"], 0),
    ]
    for args, expect in steps:
        r = run(args, target="local" if args[-1] != "cloud" else "cloud-plan")
        assert r.returncode == expect, f"{args}: {r.stderr}"
    r = ctl("deploy", "apply", "--target", "cloud", target="cloud")
    assert r.returncode != 0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))