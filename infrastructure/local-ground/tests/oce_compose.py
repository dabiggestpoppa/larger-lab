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


def verify_backup_manifest(backup_dir=None):
    """Independently verify a BACKUP_MANIFEST.sha256 over the .backup-content
    that was just produced (before any mutation). Returns the parsed manifest
    and raises on any hash/size mismatch."""
    assert backup_dir is not None, "verify_backup_manifest requires an explicit backup dir"
    d = Path(backup_dir)
    man = d / "BACKUP_MANIFEST.sha256"
    content = d / ".backup-content"
    assert man.is_file(), f"missing manifest: {man}"
    assert content.is_dir(), f"missing content dir: {content}"
    entries = {}
    for line in man.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) != 3:
            raise AssertionError(f"malformed manifest line: {line!r}")
        sha, size, rel = parts
        entries[rel] = (sha, int(size))
    assert entries, "empty backup manifest"
    for rel, (sha, size) in entries.items():
        f = content / rel
        assert f.is_file(), f"manifest entry missing file: {rel}"
        actual = hashlib.sha256(f.read_bytes()).hexdigest()
        abytes = f.stat().st_size
        assert actual == sha, f"hash mismatch: {rel}"
        assert abytes == size, f"size mismatch: {rel}"
    return entries


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


def health_snapshot():
    """One simultaneous Docker health snapshot of every mandatory service."""
    return {s: health(s) for s in ALL_SERVICES}


def converge_snapshot(timeout_s=180, stable=2, interval=3):
    """Require ALL mandatory services to be healthy in the SAME snapshot, for
    `stable` consecutive snapshots (a short stability window). Prevents a
    service briefly `starting` after a transition from being misread as
    healthy. Returns (ok, last_snapshot)."""
    deadline = time.time() + timeout_s
    streak = 0
    last = {}
    while time.time() < deadline:
        last = health_snapshot()
        if all(v == "healthy" for v in last.values()):
            streak += 1
            if streak >= stable:
                return True, last
        else:
            streak = 0
        time.sleep(interval)
    return False, last


def wait_all_healthy(timeout_s=180, stable=2, interval=3):
    """Return True only when the whole stack is simultaneously healthy and has
    held stable for `stable` consecutive snapshots."""
    ok, _ = converge_snapshot(timeout_s, stable, interval)
    return ok


def write_health_diagnostics(dir_path):
    """Record a deterministic health snapshot and per-container details into
    dir_path. Returns the snapshot dict. Never raises."""
    snap = {}
    d = Path(dir_path)
    try:
        d.mkdir(parents=True, exist_ok=True)
        snap = health_snapshot()
        (d / "health-snapshot.json").write_text(
            json.dumps({"services": snap, "all_healthy": all(v == "healthy" for v in snap.values())},
                       indent=2), encoding="utf-8")
        for c in ALL_SERVICES:
            insp = subprocess.run(["docker", "inspect", c], capture_output=True, text=True)
            (d / f"{c}.inspect.json").write_text(insp.stdout, encoding="utf-8")
            st = subprocess.run(["docker", "inspect", "--format", "{{.State.Status}}", c],
                                capture_output=True, text=True)
            hs = health(c)
            (d / f"{c}.state.txt").write_text(f"state={st.stdout.strip()} health={hs}\n", encoding="utf-8")
            logs = subprocess.run(["docker", "logs", "--tail", "80", c], capture_output=True, text=True)
            (d / f"{c}.logs.txt").write_text(logs.stdout + logs.stderr, encoding="utf-8")
    except Exception as e:  # diagnostics must never break the test
        try:
            (d / "diagnostics-error.txt").write_text(repr(e), encoding="utf-8")
        except Exception:
            pass
    return snap


def assert_stack_converged(timeout_s=180, stable=2, interval=3, evidence_subdir="health-convergence"):
    """Assert the entire stack becomes simultaneously healthy and stable.
    On timeout, write health diagnostics and fail with a full snapshot.
    Used after every full start/restart/down-up transition."""
    ok, snap = converge_snapshot(timeout_s, stable, interval)
    if not ok:
        diag = Path(os.environ["OCE_EVIDENCE_DIR"]) / evidence_subdir\
            if os.environ.get("OCE_EVIDENCE_DIR") else Path(".") / evidence_subdir
        write_health_diagnostics(diag)
        raise AssertionError(f"stack did not reach simultaneous stable health: {snap}")
    return snap


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
    """Bring the stack up (idempotent) and wait for truthful simultaneous,
    stable readiness of ALL mandatory services (not just postgres)."""
    ctl("local", "up", check=True)
    assert_stack_converged()
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
