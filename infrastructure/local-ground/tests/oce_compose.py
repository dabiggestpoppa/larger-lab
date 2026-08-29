"""OCE Local Ground — shared real-Compose helpers (B1-LOCAL, A-003).

Single owner of the Local Ground stack: the session-scoped `oce_stack`
fixture in conftest.py starts the stack once, waits for truthful readiness,
and tears it down (with volumes) in `finally`, recording cleanup evidence.
These helpers are executable only with Docker present; the pure parser
(parse_compose_ps) is unit-tested separately without Docker.
"""
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = BASE_DIR / "scripts"
COMPOSE = BASE_DIR / "compose"
COMPOSE_FILE = COMPOSE / "compose.yml"

POSTGRES = "oce-local-postgresql"
REDIS = "oce-local-redis"
ARTIFACT = "oce-local-artifact"
METRICS = "oce-local-prometheus"
ALL_SERVICES = [POSTGRES, REDIS, ARTIFACT, METRICS]

PG_USER = "oce_local_admin"
PG_DB = "oce_local"

TEST_SECRETS = {
    "POSTGRES_PASSWORD": "test-secret-postgres-001",
    "ARTIFACT_SECRET_KEY": "test-secret-artifact-001",
}

_BASH = shutil.which("bash") or "bash"


def docker_available():
    if shutil.which("docker") is None:
        return False
    r = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
    return r.returncode == 0


def run(args, env_extra=None, check=False, cwd=None, target="local", timeout=300):
    env = dict(os.environ, OCE_RUNTIME_TARGET=target, PYTHONDONTWRITEBYTECODE="1",
               **TEST_SECRETS, **(env_extra or {}))
    r = subprocess.run(args, cwd=str(cwd or BASE_DIR), env=env,
                       capture_output=True, text=True, timeout=timeout)
    if check:
        assert r.returncode == 0, f"{args} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def ctl(*args, check=True, target="local", env_extra=None):
    return run([_BASH, str(SCRIPTS / "oce-ctl")] + list(args), check=check,
               target=target, env_extra=env_extra)


def dcompose(*args, check=True, env_extra=None, timeout=300):
    env = dict(os.environ, **TEST_SECRETS, **(env_extra or {}))
    r = subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE)] + list(args),
                       cwd=str(COMPOSE), env=env, capture_output=True, text=True, timeout=timeout)
    if check:
        assert r.returncode == 0, f"docker compose {args} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def dexec(container, cmd, check=True, timeout=120):
    r = subprocess.run(["docker", "exec", container] + list(cmd),
                       capture_output=True, text=True, timeout=timeout)
    if check:
        assert r.returncode == 0, f"docker exec {container} {cmd} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def cp_into(container, host_src, container_dst):
    """Copy a host file into a container without needing a shell inside it."""
    r = subprocess.run(["docker", "cp", str(host_src), f"{container}:{container_dst}"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"docker cp -> {container}:{container_dst} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def cp_out(container, container_src, host_dst):
    """Copy a file out of a container without needing a shell inside it."""
    r = subprocess.run(["docker", "cp", f"{container}:{container_src}", str(host_dst)],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, f"docker cp <- {container}:{container_src} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def health(container):
    r = subprocess.run(["docker", "inspect", "--format", "{{.State.Health.Status}}", container],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "missing"


def state(container):
    r = subprocess.run(["docker", "inspect", "--format", "{{.State.Status}}", container],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "missing"


def wait_healthy(container, timeout_s=90):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if health(container) == "healthy":
            return True
        time.sleep(3)
    return False


def wait_all_healthy(timeout_s=120):
    return all(wait_healthy(s, timeout_s) for s in ALL_SERVICES)


def pg_ready(timeout_s=90, diagnostic_dir=None):
    """Bounded PostgreSQL readiness via Docker health state OR pg_isready.

    On timeout, preserves container state, health, recent logs, inspect
    output, and the exact last pg_isready command/exit status in
    `diagnostic_dir` (defaults to OCE_EVIDENCE_DIR when set).
    """
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        if health(POSTGRES) == "healthy":
            return True
        try:
            r = subprocess.run(["docker", "exec", POSTGRES, "pg_isready",
                                "-U", PG_USER, "-d", PG_DB, "-h", "localhost"],
                               capture_output=True, text=True, timeout=20)
        except subprocess.TimeoutExpired:
            last = None
            time.sleep(2)
            continue
        last = r
        if r.returncode == 0 and "accepting connections" in r.stdout:
            return True
        time.sleep(2)
    d = diagnostic_dir or os.environ.get("OCE_EVIDENCE_DIR")
    if d:
        dd = Path(d)
        dd.mkdir(parents=True, exist_ok=True)
        (dd / "postgres-timeout.log").write_text(
            "last pg_isready rc=" + str(last.returncode if last else "never") + "\n"
            + ("stdout=" + last.stdout + "\n" if last else "")
            + ("stderr=" + last.stderr + "\n" if last else ""), encoding="utf-8")
        (dd / "postgres-state.txt").write_text(
            f"state={state(POSTGRES)} health={health(POSTGRES)}\n", encoding="utf-8")
        insp = subprocess.run(["docker", "inspect", POSTGRES], capture_output=True, text=True)
        (dd / "postgres-inspect.json").write_text(insp.stdout, encoding="utf-8")
        logs = subprocess.run(["docker", "logs", "--tail", "100", POSTGRES], capture_output=True, text=True)
        (dd / "postgres-logs.txt").write_text(logs.stdout + logs.stderr, encoding="utf-8")
    return False


def ensure_stack_healthy():
    """Bring the stack up (idempotent) and wait for truthful readiness."""
    ctl("local", "up", check=True)
    assert wait_all_healthy(), f"stack not healthy: {[(s, health(s)) for s in ALL_SERVICES]}"
    assert pg_ready(), "postgres not ready"


def parse_compose_ps(text):
    """Parse `docker compose ps --format json` output portably.

    Supports the documented Compose output forms:
      * a single JSON array;
      * a single JSON object;
      * newline-delimited JSON objects (one per line).

    Raises ValueError on malformed or incomplete output.
    """
    text = text.strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"malformed compose ps JSON array: {e}") from e
        if not isinstance(data, list):
            raise ValueError("compose ps output: expected a JSON array")
        for entry in data:
            if not isinstance(entry, dict):
                raise ValueError("compose ps output: array entries must be JSON objects")
        return data
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict):
        return [data]
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"malformed compose ps line: {line!r} ({e})") from e
        if not isinstance(obj, dict):
            raise ValueError(f"compose ps line is not a JSON object: {line!r}")
        out.append(obj)
    return out


def published_ports(entries):
    """Return services whose entries publish any port (deny-by-default check).

    Handles both the modern `Publishers` list and the legacy `Ports` field.
    """
    bad = []
    for e in entries:
        pubs = e.get("Publishers") or []
        ports = e.get("Ports") or ""
        has = bool(pubs)
        if isinstance(ports, str):
            has = has or bool(ports.strip()) and ports.strip() != "-"
        elif isinstance(ports, list):
            has = has or bool(ports)
        if has:
            bad.append(e.get("Service") or e.get("Name") or str(e))
    return bad
