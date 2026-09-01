"""OCE Book 2 — local lifecycle (B2-R7).

Deterministic operator commands: configure, doctor, start, migrate,
wait-dependencies, smoke, restart, recover, stop, destroy.

Design rules (each is enforced by tests in tests/test_local_lifecycle.py):

  * No predictable default secrets. The PostgreSQL password comes from the
    operator's environment or the generated .runtime store (0600).
  * Shutdown is runtime-owned PID tracking ONLY — never ``pkill -f``.
  * Stale PID files are detected safely: a PID file whose process is dead,
    or whose command line does not match the expected marker, is treated as
    stale and is never signalled (no unrelated process is ever terminated).
  * Ordinary stop / test cleanup preserves the durable PostgreSQL volume.
    Only the explicit ``destroy --yes`` command removes durable state.
  * Every published port must bind loopback (127.0.0.1) only.
  * No cloud account or credential is required for any command.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from oce_control import local_secrets as ls

BASE_DIR = ls.BASE_DIR
COMPOSE_FILE = BASE_DIR / "compose" / "compose.yml"
PYTHON = sys.executable or "python3"

API_MARKER = "oce_control.http_api"
WORKER_MARKER = "oce_control.worker_loop"


def effective_api_port(environ: dict | None = None) -> int:
    """Canonical runtime HTTP port from the gated effective config (B4-R3R2).

    The lifecycle smoke/console paths use the SAME validated config the API
    binds, so the reported console URL always matches the actual listener.
    There is deliberately no legacy ``OCE_API_PORT``/8080 default here.
    """
    from oce_control.config_startup import require_startable
    return int(require_startable(environ).get("control_plane.port"))

# name -> (pid file, cmdline marker expected in the process args)
PROCESSES = {
    "api": ("api.pid", API_MARKER),
    "worker": ("worker.pid", WORKER_MARKER),
}


# --------------------------------------------------------------------------
# PID tracking (runtime-owned; never pkill)
# --------------------------------------------------------------------------

def pid_file(name: str) -> Path:
    return ls.RUNTIME_DIR / f"{name}.pid"


def read_pid(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def process_cmdline(pid: int) -> str | None:
    """Return the command line of pid, or None if it is not running."""
    if pid <= 0:
        return None
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        if raw:
            return raw.replace(b"\0", b" ").decode("utf-8", "replace").strip()
    except OSError:
        pass
    try:
        r = subprocess.run(["ps", "-p", str(pid), "-o", "args="],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    # Windows fallback (no POSIX ps)
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\").CommandLine"],
            capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def pid_state(path: Path, marker: str) -> tuple[str, str]:
    """Return ('live'|'stale', detail) for a PID file.

    A PID file is LIVE only when the recorded PID exists AND its command
    line contains the expected marker. Anything else is stale and must
    never be signalled.
    """
    pid = read_pid(path)
    if pid is None:
        return "stale", f"{path.name}: no parseable PID"
    cmdline = process_cmdline(pid)
    if cmdline is None:
        return "stale", f"{path.name}: pid {pid} not running"
    if marker not in cmdline:
        return "stale", f"{path.name}: pid {pid} is an unrelated process ({cmdline!r})"
    return "live", f"{path.name}: pid {pid} matches {marker!r}"


def write_pid(path: Path, pid: int) -> None:
    ls.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{pid}\n", encoding="utf-8")


def clear_pid(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _pid_alive(pid: int) -> bool:
    """Liveness check without /proc/ps dependency for the wait loop."""
    if os.name == "nt":
        # os.kill(pid, 0) is a no-op on Windows (never raises), so use the
        # cmdline probe: PowerShell returns empty for a dead pid.
        return process_cmdline(pid) is not None
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(errors="replace")
        # state is the field after the parenthesized comm; 'Z' = zombie
        # (exited, awaiting reap) — treat as dead, since kill(pid, 0)
        # still succeeds on zombies and would spin the wait loop.
        after = stat.split(")", 1)[1].split() if ")" in stat else []
        if after and after[0] == "Z":
            return False
    except OSError:
        pass
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return process_cmdline(pid) is not None


def terminate_pid(pid: int, timeout_s: float = 8.0) -> bool:
    """Terminate exactly the given PID. Returns True if it exited."""
    if pid <= 0:
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        # Windows: os.kill(SIGTERM) is emulated; if it fails use taskkill.
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/T"],
                           capture_output=True, text=True, timeout=15)
        except OSError:
            return False
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.2)
    sigkill = getattr(signal, "SIGKILL", None)
    if sigkill is not None:
        try:
            os.kill(pid, sigkill)
        except OSError:
            pass
    return not _pid_alive(pid)


def stop_runtime_processes() -> list[str]:
    """Stop API + worker using ONLY runtime-owned PID files.

    Never pkill, never touches a process whose cmdline does not match the
    expected marker. Returns a list of human-readable actions taken.
    """
    actions: list[str] = []
    for name, (pidfile, marker) in PROCESSES.items():
        path = pid_file(name)
        state, detail = pid_state(path, marker)
        if state == "live":
            pid = read_pid(path)
            assert pid is not None
            if terminate_pid(pid):
                actions.append(f"terminated {name} (pid {pid})")
            else:
                actions.append(f"WARN: could not confirm exit of {name} (pid {pid})")
            clear_pid(path)
        else:
            if path.exists():
                clear_pid(path)
            actions.append(f"stale/absent {name}: {detail}")
    return actions


# --------------------------------------------------------------------------
# Docker / compose helpers
# --------------------------------------------------------------------------

def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        r = subprocess.run(["docker", "compose", "version"],
                           capture_output=True, text=True, timeout=30)
        return r.returncode == 0
    except OSError:
        return False


def compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = ls.compose_environment()
    r = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE)] + list(args),
        cwd=str(BASE_DIR), env=env, capture_output=True, text=True, timeout=600)
    if check and r.returncode != 0:
        raise RuntimeError(f"compose {' '.join(args)} rc={r.returncode}\n"
                           f"{r.stdout}\n{r.stderr}")
    return r


def published_ports_from_compose() -> list[str]:
    """Static loopback check: every published port must bind 127.0.0.1.

    Parses compose.yml port declarations (no YAML dependency). Returns a
    list of offending declarations; empty means all ports are loopback-only.
    """
    if not COMPOSE_FILE.exists():
        return [f"missing {COMPOSE_FILE}"]
    text = COMPOSE_FILE.read_text(encoding="utf-8")
    offenders: list[str] = []
    for line in text.splitlines():
        m = re.search(r'^\s*-\s*"?([^"#]*?)"?\s*$', line)
        if not m:
            continue
        decl = m.group(1).strip()
        if not decl or ":" not in decl or "/" in decl:
            continue  # empty, comment, or volume mount (contains /)
        # port declarations look like 127.0.0.1:5433:5432 (or bare HOST:CONTAINER)
        if re.fullmatch(r"\d+:\d+", decl):
            offenders.append(f"{decl} binds all interfaces (missing loopback bind)")
            continue
        if not re.fullmatch(r"[0-9a-zA-Z_.-]+:\d+:\d+", decl):
            continue  # not a port mapping (e.g. depends_on, env) — ignore
        parts = decl.split(":")
        if parts[0] != "127.0.0.1":
            offenders.append(f"{decl} does not bind 127.0.0.1")
    return offenders


def live_port_bindings() -> list[str]:
    """Runtime loopback check via `docker compose port` for running services."""
    problems: list[str] = []
    for service, container_port in (("postgresql", "5432"), ("redis", "6379")):
        r = compose("port", service, container_port, check=False)
        if r.returncode != 0:
            problems.append(f"{service}: container not running or port unknown")
            continue
        bind = r.stdout.strip()
        if bind and not bind.startswith("127.0.0.1:"):
            problems.append(f"{service} publishes {bind!r} (not loopback)")
    return problems


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def _require_runtime_init_material() -> None:
    """CXR6-04: ordinary start/restart/recover are READ-ONLY over secret
    authority. They REQUIRE the material `configure` materialized and never
    create it — missing material fails closed with a `configure` hint.
    """
    missing = []
    if not ls.load_runtime_secret():
        missing.append("postgres password")
    try:
        ls.read_worker_token()
    except RuntimeError:
        missing.append("worker token")
    try:
        ls.read_activation_handoff_key()
    except RuntimeError:
        missing.append("activation handoff key")
    if missing:
        raise SystemExit(
            "OCE start BLOCKED: required initialization material missing "
            "(" + ", ".join(missing) + ") — run `python scripts/oce_local.py "
            "configure` to initialize it; ordinary start is READ-ONLY over "
            "secret authority and never materializes missing material "
            "(B4-CXR6R4)")


def _preflight_configuration() -> None:
    """Configuration posture preflight (B4-CXR6R4 #7): the effective config
    must validate BEFORE any mutation; a forbidden/malformed posture never
    reaches an initialization or activation step."""
    from oce_control.config_spine import ValidationError as _VE
    from oce_control.config_startup import (
        effective_from_env, startup_report, validate_effective)
    try:
        eff = effective_from_env(dict(os.environ))
        validate_effective(eff)
    except _VE:
        raise SystemExit(startup_report(dict(os.environ)))


def configure() -> dict:
    """EXPLICIT INITIALIZATION command (B4-CXR6R4).

    Materializes the postgres password (one-time), the worker token
    (one-time), AND the dedicated activation-handoff key (one-time) in the
    approved store, then writes compose.env. `start`/`restart`/`recover`
    NEVER call this — ordinary activation is read-only over secret authority.
    Preflights (configuration posture, static compose boundary, store
    readability) BEFORE any mutation; a failed step never partially writes.
    """
    _preflight_configuration()
    offenders = published_ports_from_compose()
    if offenders:
        raise SystemExit(
            "configure BLOCKED: published ports are not loopback-only: "
            + "; ".join(offenders) + " (B4-CXR6R4 preflight)")
    ls.write_compose_env()
    ls.initialize_worker_token()  # one-time init; existing token preserved
    ls.initialize_activation_handoff_key()  # B4-CXR6R1 dedicated capability key
    source = "unset"
    if ls.SECRETS_FILE.exists():
        try:
            source = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8")).get("source", "persisted")
        except (json.JSONDecodeError, OSError):
            source = "persisted"
    report = {
        "runtime_dir": str(ls.RUNTIME_DIR),
        "secret_source": source,
        "port_offenders": offenders,
    }
    return report


def wait_dependencies(timeout_s: int = 120) -> bool:
    """Wait for DEPENDENCY health ONLY (postgres + redis containers).

    B4-CXR5R7: named truthfully — this reports dependency health and is
    NEVER activation/runtime readiness. Activation readiness is a strictly
    stronger contract (pinned ActivationContext + resolved governed secret +
    migration state + processes); callers must treat this as dependency
    health only.
    """
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        pg = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Health.Status}}", "b2-local-postgresql"],
            capture_output=True, text=True, timeout=30).stdout.strip()
        redis = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Health.Status}}", "b2-local-redis"],
            capture_output=True, text=True, timeout=30).stdout.strip()
        if pg == "healthy" and redis == "healthy":
            return True
        time.sleep(2)
    return False


def _migration_set_identity() -> dict:
    """Canonical migration-set identity for the activation envelope
    (B4-CXR5R3): ordered filenames, versions, file hashes — never SQL
    contents. Loaded from the canonical migration program module."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "oce_migrate_identity", BASE_DIR / "scripts" / "migrate.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.migration_set_identity()


def migrate(ctx=None, env=None) -> subprocess.CompletedProcess:
    """Apply migrations against the GOVERNED database (B4-CXR3R2).

    No public DSN parameter: the migration target is always derived from the
    governed secret boundary (ls.postgres_dsn() — read-only, fail closed).
    An arbitrary DSN can never redirect migrations to another database.

    B4-CXR4R3: a pinned ActivationContext supplies the target from its
    PINNED postgres parameters + reference (stale-checked), so migrations
    run against the exact database the activation validated.

    B4-CXR5R1: NO --db anywhere. The child migration process resolves the
    governed connection INTERNALLY from its own pinned activation; a
    password-bearing DSN never enters process argv, /proc/<pid>/cmdline,
    command capture, or diagnostics.

    B4-CXR5R3: the child runs under the PARENT's SANITIZED activation
    environment (envelope carrier) — no ambient secret or OCE_* authority
    survives into the child, and the migration-set identity must match the
    parent envelope.
    """
    if ctx is None:
        from oce_control.config_startup import create_activation_context
        ctx = create_activation_context()
    if env is None:
        # B4-CXR6R1: the migration child is role-bound to 'migration' — the
        # authenticated capability it consumes can never authorize an API or
        # worker.
        env = ctx.child_environment(
            child_role="migration",
            migration_set_identity=_migration_set_identity())
    cmd = [PYTHON, str(BASE_DIR / "scripts" / "migrate.py"), "up"]
    return subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True,
                          text=True, timeout=300)


def http_ok(path: str, port: int | None = None) -> bool:
    port = port if port is not None else effective_api_port()
    url = f"http://127.0.0.1:{port}{path}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status in (200, 307)
    except OSError:
        return False


def smoke(*, port: int) -> list[str]:
    """Smoke test: health endpoint + operator console served.

    B4-CXR5R7: the probe target MUST come from the pinned activation
    destination — callers pass ``port=ctx.control_plane_port``. There is NO
    port-less default that silently re-reads the environment; a fresh
    environment read can never select a different listener than the one the
    activation validated.
    """
    if not isinstance(port, int) or isinstance(port, bool):
        raise TypeError("smoke requires the pinned activation port "
                        "(B4-CXR5R7)")
    results = []
    results.append(("health", http_ok("/health", port)))
    results.append(("console", http_ok("/console", port)))
    return results


def start_process(name: str, argv: list[str], env: dict) -> Path:
    """Launch a runtime process with PID-file ownership and a log file.

    B4-CXR6R4: *env* is REQUIRED — an explicit verified child environment
    (the sanitized, role-bound activation capability environment from a
    pinned ActivationContext). The compose_environment() compatibility
    default is REMOVED: a runtime API/worker process can never acquire the
    Docker-Compose-only secret carrier (POSTGRES_PASSWORD/POSTGRES_DSN)
    through a default, and a process launch without verified lineage is
    rejected.
    """
    if env is None:
        raise RuntimeError(
            "start_process requires an explicit verified child environment — "
            "no compose_environment default; a process launch without "
            "verified activation lineage is refused (B4-CXR6R4)")
    log = ls.LOGS_DIR / f"{name}.log"
    ls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    env = dict(env)
    env["PYTHONPATH"] = str(BASE_DIR / "src") + os.pathsep + env.get("PYTHONPATH", "")
    fd = open(log, "ab")
    proc = subprocess.Popen(argv, cwd=str(BASE_DIR), env=env,
                            stdout=fd, stderr=subprocess.STDOUT, start_new_session=True)
    fd.close()
    path = pid_file(name)
    write_pid(path, proc.pid)
    return path


def stop() -> list[str]:
    actions = stop_runtime_processes()
    r = compose("down", check=False)
    if r.returncode != 0:
        actions.append(f"WARN: compose down rc={r.returncode}")
    actions.append("compose down (durable postgres volume preserved)")
    return actions


def destroy(confirmed: bool) -> list[str]:
    """Destructive: removes the durable PostgreSQL volume. Requires --yes."""
    if not confirmed:
        raise SystemExit(
            "destroy is DESTRUCTIVE (removes the durable PostgreSQL volume). "
            "Re-run with --yes to authorize.")
    actions = stop_runtime_processes()
    r = compose("down", "-v", check=False)
    if r.returncode != 0:
        raise RuntimeError(f"compose down -v rc={r.returncode}\n{r.stdout}\n{r.stderr}")
    actions.append("compose down -v: durable postgres volume REMOVED (explicit authorization)")
    return actions


def doctor() -> dict:
    """Run every local-runtime check; all must pass for the runtime to be sound."""
    checks: list[dict] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    chk("docker available", docker_available())
    chk("compose file present", COMPOSE_FILE.exists(), str(COMPOSE_FILE))
    chk("runtime dir perms 0700",
        ls.RUNTIME_DIR.stat().st_mode & 0o777 == 0o700 if ls.RUNTIME_DIR.exists() else False)
    secret = ls.load_runtime_secret()
    chk("runtime secret configured (no predictable default)",
        bool(secret) and len(secret) >= 32,
        "generated" if secret else "missing — run `configure`")
    secret_file_mode = ls.SECRETS_FILE.stat().st_mode & 0o777 if ls.SECRETS_FILE.exists() else None
    chk("secrets.json 0600", secret_file_mode == 0o600, f"mode={oct(secret_file_mode) if secret_file_mode else 'n/a'}")
    try:
        ls.read_activation_handoff_key()
        key_ok = True
        key_detail = "configured"
    except RuntimeError as exc:
        key_ok = False
        key_detail = str(exc)
    chk("activation handoff key configured (0600, read-only)", key_ok, key_detail)
    offenders = published_ports_from_compose()
    chk("published ports loopback-only", not offenders, "; ".join(offenders) or "all ports bind 127.0.0.1")
    for name, (pidfile, marker) in PROCESSES.items():
        state, detail = pid_state(pid_file(name), marker)
        chk(f"{name} pid state", state == "live" or not pid_file(name).exists(), detail)
    # durable volume must exist when the stack has ever been started
    vol = subprocess.run(["docker", "volume", "inspect", "b2_local_postgres_data"],
                         capture_output=True, text=True, timeout=30)
    chk("durable postgres volume present", vol.returncode == 0)
    cloud_hint = cloud_credential_hint()
    chk("no cloud credentials required", not cloud_hint, "; ".join(cloud_hint) or "local-only")
    # Book 4 surface C + B4-CXR3R7: doctor must fail when the effective
    # configuration is invalid AND when the configured secret reference does
    # not resolve — configuration alone is not runtime readiness.
    from oce_control.config_startup import validate_runtime_readiness
    rdy = validate_runtime_readiness()
    chk("config spine effective config valid (fail-closed)",
        rdy["ok"], rdy["error"] or "valid")
    chk("configured secret reference resolves (runtime readiness)",
        rdy["ready"], rdy["error"] or "resolved")
    return {"checks": checks, "ok": all(c["ok"] for c in checks)}


def start(timeout_s: int = 120, migrate_now: bool = True) -> list[str]:
    # B4-CXR5R3: snapshot the activation inputs ONCE and resolve/validate the
    # effective configuration ONCE (fail closed on malformed / incomplete /
    # forbidden config BEFORE any init/mutation).
    from oce_control.config_spine import ValidationError as _VE
    from oce_control.config_startup import (
        create_activation_context, effective_from_env, startup_report,
        validate_effective)
    snapshot = dict(os.environ)
    try:
        eff = effective_from_env(snapshot)
        validate_effective(eff)
    except _VE:
        raise SystemExit(startup_report(snapshot))
    actions: list[str] = []
    # B4-CXR6R4: `start` is READ-ONLY over secret authority. It NEVER calls
    # configure() and NEVER materializes missing material — required
    # initialization material (postgres password, worker token, activation
    # handoff key) must already exist or start fails closed with a
    # `configure` remediation hint.
    _require_runtime_init_material()
    actions.append("initialization material present (start is read-only over secret authority)")
    # B4-CXR5R3: create EXACTLY ONE authoritative parent ActivationContext
    # (reusing the pre-resolved effective config — no second resolution);
    # every downstream step consumes the PINNED authority.
    ctx = create_activation_context(environ=snapshot, eff=eff)
    actions.append("activation context pinned (one resolution; immutable effective config + secret identity)")
    # B4-CXR5R3/CXR6R1: each SANITIZED child environment carries an
    # AUTHENTICATED, role-bound activation capability — the worker child is
    # bound to 'worker' and the API child to 'api'; a child proves the same
    # lineage instead of re-reading ambient authority.
    worker_env = ctx.child_environment(
        child_role="worker",
        migration_set_identity=_migration_set_identity())
    api_env = ctx.child_environment(
        child_role="api",
        migration_set_identity=_migration_set_identity())
    if not docker_available():
        raise RuntimeError("Docker is unavailable — the local runtime requires Docker "
                           "(PostgreSQL + Redis run as local containers on loopback)")
    offenders = published_ports_from_compose()
    if offenders:
        raise RuntimeError("published ports are not loopback-only: "
                           + "; ".join(offenders))
    compose("up", "-d")
    actions.append("compose up -d")
    if not wait_dependencies(timeout_s):
        raise RuntimeError("postgres/redis did not become healthy")
    actions.append("postgres + redis healthy")
    if migrate_now:
        # B4-CXR6R1: the migration child consumes a role-bound 'migration'
        # capability under the parent's pinned lineage.
        migration_env = ctx.child_environment(
            child_role="migration",
            migration_set_identity=_migration_set_identity())
        r = migrate(ctx, env=migration_env)
        if r.returncode != 0:
            raise RuntimeError(f"migrations failed:\n{r.stdout}\n{r.stderr}")
        actions.append("migrations applied")
    # B4-CXR5R1: worker authentication material is NEVER passed through
    # argv — the worker reads its token from the approved store (initialized
    # once in configure(); read-only during start/restart/recover).
    start_process("worker", [PYTHON, "-m", "oce_control.worker_loop",
                             "--worker-id", "worker-local01"], env=worker_env)
    actions.append("worker started (pid-file owned, token from approved store)")
    start_process("api", [PYTHON, "-m", "oce_control.http_api"], env=api_env)
    actions.append("api started (pid-file owned, pinned activation lineage)")
    if not wait_for_http(timeout_s, port=ctx.control_plane_port):
        raise RuntimeError("API did not answer on 127.0.0.1")
    results = smoke(port=ctx.control_plane_port)
    if not all(ok for _, ok in results):
        raise RuntimeError("smoke failed: " + ", ".join(f"{n}={ok}" for n, ok in results))
    actions.append("smoke: " + ", ".join(f"{n}={ok}" for n, ok in results))
    return actions


def wait_for_http(timeout_s: int = 60, port: int | None = None) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if http_ok("/health", port):
            return True
        time.sleep(1)
    return False


def cloud_credential_hint(environ: dict | None = None) -> list[str]:
    """Names of cloud-provider credential variables in the environment.

    The local runtime must never require (or silently use) cloud
    credentials. Returns the offending variable names; empty means
    local-only.
    """
    env = environ if environ is not None else os.environ
    # Only CREDENTIAL variables count — benign runner noise like
    # AZURE_EXTENSION_DIR or AZURE_HTTP_USER_AGENT must not trip this.
    provider = re.compile(r"(aws|azure|gcp|google)", re.I)
    secret = re.compile(r"(secret|token|password|credential|access_key|key_id|"
                        r"client_id|client_secret|session_token|tenant_id|"
                        r"service_account|connection_string)", re.I)
    return sorted(k for k in env if provider.search(k) and secret.search(k))


def recover() -> list[str]:
    """Bring the runtime back to a known-good state without destroying data.

    B4-CXR4R3/R4: the activation gate runs FIRST (pinned ActivationContext
    with config posture + secret resolution); compose up / migration / process
    launch happen only AFTER the gate — a forbidden effective config can
    never mutate infrastructure or the database before rejection.
    """
    actions: list[str] = []
    # B4-CXR6R4: recover is READ-ONLY over secret authority — required
    # initialization material must exist (never materialized here).
    _require_runtime_init_material()
    from oce_control.config_startup import create_activation_context
    ctx = create_activation_context()  # gate first — fail closed before any mutation
    actions.append("activation gate passed (pinned context)")
    # Clear stale PID files first (never signal anything unexpected).
    for name, (pidfile, marker) in PROCESSES.items():
        path = pid_file(name)
        state, detail = pid_state(path, marker)
        if state == "stale" and path.exists():
            clear_pid(path)
            actions.append(f"cleared stale {name} pid: {detail}")
    if not docker_available():
        raise RuntimeError("Docker unavailable")
    if not wait_dependencies(60):
        compose("up", "-d")
        if not wait_dependencies(120):
            raise RuntimeError("stack did not recover to healthy")
        actions.append("stack re-upped and healthy")
    r = migrate(ctx)
    if r.returncode != 0:
        raise RuntimeError(f"migrations failed:\n{r.stdout}\n{r.stderr}")
    actions.append("migrations up-to-date")
    for name, (pidfile, marker) in PROCESSES.items():
        if pid_state(pid_file(name), marker)[0] != "live":
            # B4-CXR6R1: each restarted child consumes a role-bound capability
            child_role = "worker" if name == "worker" else "api"
            child_env = ctx.child_environment(
                child_role=child_role,
                migration_set_identity=_migration_set_identity())
            if name == "worker":
                start_process("worker", [PYTHON, "-m", "oce_control.worker_loop",
                                         "--worker-id", "worker-local01"],
                              env=child_env)
            else:
                start_process("api", [PYTHON, "-m", "oce_control.http_api"],
                              env=child_env)
            actions.append(f"{name} restarted (pinned activation lineage)")
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="oce_local",
                                     description="OCE Book 2 local runtime lifecycle (B2-R7)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("configure", help="generate/verify local secret, write compose.env")
    sub.add_parser("doctor", help="run every local-runtime check")
    sp = sub.add_parser("start", help="configure -> compose up -> migrate -> worker+api -> smoke")
    sp.add_argument("--no-migrate", action="store_true")
    sp.add_argument("--timeout", type=int, default=120)
    sub.add_parser("migrate", help="apply numbered migrations")
    sp = sub.add_parser("wait-dependencies",
                        help="wait until postgres+redis are healthy (dependency health ONLY — never activation readiness)")
    sp.add_argument("--timeout", type=int, default=120)
    sub.add_parser("smoke", help="health + console smoke test against the running API")
    sub.add_parser("restart", help="stop then start (durable volume preserved)")
    sub.add_parser("recover", help="clear stale pids, restore stack + processes")
    sub.add_parser("stop", help="stop api/worker (PID files) + compose down, volume preserved")
    sp = sub.add_parser("destroy", help="DESTRUCTIVE: also remove durable postgres volume")
    sp.add_argument("--yes", action="store_true", help="explicit authorization")
    args = parser.parse_args(argv)

    try:
        if args.command == "configure":
            report = configure()
            print(json.dumps(report, indent=2))
            return 0 if not report["port_offenders"] else 1
        if args.command == "doctor":
            result = doctor()
            for c in result["checks"]:
                print(f"[{'OK' if c['ok'] else 'FAIL'}] {c['check']}  {c['detail']}")
            return 0 if result["ok"] else 1
        if args.command == "start":
            for a in start(timeout_s=args.timeout, migrate_now=not args.no_migrate):
                print(f"==> {a}")
            print(f"==> console at http://127.0.0.1:{effective_api_port()}/console")
            return 0
        if args.command == "migrate":
            # B4-CXR4R4: activation authority FIRST — no migration without a
            # validated effective config + resolved governed secret.
            from oce_control.config_startup import create_activation_context
            ctx = create_activation_context()
            r = migrate(ctx)
            print(r.stdout, end="")
            print(r.stderr, file=sys.stderr, end="")
            return r.returncode
        if args.command == "wait-dependencies":
            return 0 if wait_dependencies(args.timeout) else 1
        if args.command == "smoke":
            # B4-CXR5R7: smoke is pinned to the activation destination — the
            # probe port comes from the pinned context, never a fresh env read.
            from oce_control.config_startup import create_activation_context
            ctx = create_activation_context()
            results = smoke(port=ctx.control_plane_port)
            for n, ok in results:
                print(f"smoke {n}: {'OK' if ok else 'FAIL'}")
            return 0 if all(ok for _, ok in results) else 1
        if args.command == "restart":
            for a in stop():
                print(f"==> {a}")
            for a in start():
                print(f"==> {a}")
            return 0
        if args.command == "recover":
            for a in recover():
                print(f"==> {a}")
            return 0
        if args.command == "stop":
            for a in stop():
                print(f"==> {a}")
            print("==> stopped (durable postgres volume preserved)")
            return 0
        if args.command == "destroy":
            for a in destroy(args.yes):
                print(f"==> {a}")
            return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:  # fail closed with a plain message
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
