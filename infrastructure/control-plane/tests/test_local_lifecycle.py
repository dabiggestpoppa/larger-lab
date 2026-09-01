"""OCE Book 2 — local lifecycle unit tests (B2-R7).

Pure unit tests (no Docker required): they exercise the deterministic
lifecycle contract — no predictable default secrets, runtime-owned PID
tracking instead of pkill, stale-PID safety, explicit destructive
authorization, loopback-only ports, and no cloud credential dependency.
"""
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from oce_control import local_lifecycle as ll
from oce_control import local_secrets as ls

MARKER = "oce_control.http_api"  # must remain the marker local_lifecycle owns


def _spawn_sleeper() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(600)"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@pytest.fixture(autouse=True)
def _clean_runtime(monkeypatch, tmp_path):
    """Point every .runtime path at an isolated tmp dir per test."""
    (tmp_path / "runtime").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path / "runtime")
    monkeypatch.setattr(ls, "SECRETS_FILE", tmp_path / "runtime" / "secrets.json")
    monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", tmp_path / "runtime" / "compose.env")
    monkeypatch.setattr(ls, "LOGS_DIR", tmp_path / "runtime" / "logs")
    monkeypatch.setattr(ll, "pid_file", lambda name: tmp_path / "runtime" / f"{name}.pid")
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("POSTGRES_DSN", raising=False)


# --------------------------------------------------------------------------
# Secrets — no predictable defaults
# --------------------------------------------------------------------------

def test_secret_generated_ephemeral_no_predictable_default():
    pw = ls.ensure_runtime_secret()
    assert len(pw) >= 32
    assert pw != "test-secret-b2-pg-001"  # the retired predictable default
    assert ls.load_runtime_secret() == pw
    # idempotent across invocations
    assert ls.ensure_runtime_secret() == pw


def test_secret_honors_operator_env(monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "operator-supplied-strong-secret-1234567890")
    assert ls.ensure_runtime_secret() == "operator-supplied-strong-secret-1234567890"


def test_secret_file_restrictive_permissions():
    ls.ensure_runtime_secret()
    if os.name != "nt":  # POSIX can enforce modes; Windows maps chmod to read-only
        assert ls.RUNTIME_DIR.stat().st_mode & 0o777 == 0o700
        assert ls.SECRETS_FILE.stat().st_mode & 0o777 == 0o600
    # cross-platform guarantee: the runtime secret is never committable
    gitignore = (ls.BASE_DIR.parent.parent / ".gitignore").read_text(encoding="utf-8")
    assert "infrastructure/control-plane/.runtime/" in gitignore, \
        "repo .gitignore must cover the .runtime dir (never committed)"


def test_configure_writes_compose_env_with_secret():
    report = ll.configure()
    assert ls.COMPOSE_ENV_FILE.exists()
    assert f"POSTGRES_PASSWORD={ls.load_runtime_secret()}" in ls.COMPOSE_ENV_FILE.read_text()
    assert report["port_offenders"] == []  # real compose.yml is loopback-only


def test_require_runtime_dsn_fails_closed_without_secret():
    with pytest.raises(RuntimeError, match="configure"):
        ls.require_runtime_dsn()


def test_require_runtime_dsn_rejects_external_bypass(monkeypatch):
    # B4-R3R4: an ambient POSTGRES_DSN that diverges from the governed secret
    # store is rejected (external DSN bypass denies fail closed).
    ls.ensure_runtime_secret()
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://u:p@127.0.0.1:5433/db")
    with pytest.raises(RuntimeError, match="bypass"):
        ls.require_runtime_dsn()


def test_require_runtime_dsn_accepts_governed_propagation(monkeypatch):
    # The runtime's OWN internal propagation (exactly the governed DSN) is
    # accepted — this is how compose_environment passes it to subprocesses.
    ls.ensure_runtime_secret()
    monkeypatch.setenv("POSTGRES_DSN", ls.postgres_dsn())
    assert ls.require_runtime_dsn() == ls.postgres_dsn()


# --------------------------------------------------------------------------
# B4-CXR3R1 — init vs runtime authority: an ambient POSTGRES_PASSWORD must
# never mutate the approved store through a runtime read path.
# --------------------------------------------------------------------------

def _store_snapshot() -> dict:
    """Hash/snapshot of the approved secret store (for denial side-effect
    proofs: DENIAL MUST HAVE ZERO AUTHORITY-SIDE EFFECTS)."""
    import hashlib
    if not ls.SECRETS_FILE.exists():
        return {"exists": False}
    return {
        "exists": True,
        "sha256": hashlib.sha256(ls.SECRETS_FILE.read_bytes()).hexdigest(),
        "content": ls.SECRETS_FILE.read_text(encoding="utf-8"),
    }


def test_runtime_password_cannot_materialize_missing_store(monkeypatch):
    # ambient POSTGRES_PASSWORD must NEVER create a store through a runtime
    # read path (CXR3-01-C: runtime password tries to materialize absent store)
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-password-123")
    before = _store_snapshot()
    with pytest.raises(RuntimeError, match="configure"):
        ls.require_runtime_dsn()
    with pytest.raises(RuntimeError, match="configure"):
        ls.derive_runtime_dsn()
    assert _store_snapshot() == before  # zero authority-side effects
    assert not ls.SECRETS_FILE.exists()


def test_runtime_password_cannot_rewrite_existing_store(monkeypatch):
    # CXR3-01-B: a runtime password must not overwrite an existing approved store
    ls.initialize_runtime_secret()
    governed = ls.read_runtime_secret()
    before = _store_snapshot()
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-overwrite-attempt-123456")
    dsn = ls.require_runtime_dsn()
    assert governed in dsn
    assert "ambient-overwrite-attempt-123456" not in dsn
    assert ls.read_runtime_secret() == governed  # store value unchanged
    assert _store_snapshot() == before  # zero authority-side effects


def test_matching_ambient_password_and_dsn_cannot_self_legitimate(monkeypatch):
    # CXR3-01-A: supply password X + a DSN containing X with NO store. The
    # runtime must fail closed and must NOT persist X (self-legitimation).
    monkeypatch.setenv("POSTGRES_PASSWORD", "selflegit-X-9876543210")
    dsn_attack = ("postgresql://oce_control_admin:selflegit-X-9876543210"
                  "@127.0.0.1:5433/oce_control")
    monkeypatch.setenv("POSTGRES_DSN", dsn_attack)
    before = _store_snapshot()
    with pytest.raises(RuntimeError, match="configure"):
        ls.require_runtime_dsn()
    assert _store_snapshot() == before  # DENIAL HAS ZERO AUTHORITY-SIDE EFFECTS
    assert not ls.SECRETS_FILE.exists()


def test_compose_environment_reads_without_materializing(monkeypatch):
    # compose env is a RUNTIME read: no store -> no secret vars, no store
    # created (ambient values never flow to a subprocess); after governed
    # init, the vars come from the STORE, never a stale ambient value
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-compose-1234567890")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://u:p@127.0.0.1:5432/x")
    env = ls.compose_environment()
    assert "POSTGRES_PASSWORD" not in env
    assert "POSTGRES_DSN" not in env
    assert not ls.SECRETS_FILE.exists()
    # governed init: the INIT path explicitly honors the operator password
    monkeypatch.setenv("POSTGRES_PASSWORD", "governed-operator-pw-123456789")
    ls.initialize_runtime_secret()
    governed = ls.read_runtime_secret()
    assert governed == "governed-operator-pw-123456789"
    env2 = ls.compose_environment()
    assert env2["POSTGRES_PASSWORD"] == governed
    assert "ambient-compose-1234567890" not in env2["POSTGRES_PASSWORD"]


def test_restart_uses_same_governed_secret():
    # CXR3-01-Q: restart after clean initialization uses the SAME secret
    ls.initialize_runtime_secret()
    first = ls.read_runtime_secret()
    assert ls.initialize_runtime_secret() == first  # init keeps existing
    assert ls.read_runtime_secret() == first
    assert ls.require_runtime_dsn() == ls.postgres_dsn() == ls.derive_runtime_dsn()


# --------------------------------------------------------------------------
# B4-CXR4R1 — ONE-TIME secret initialization (CXR4-01): ordinary
# start/restart/recover/configure are READ-ONLY over an existing approved
# store. Ambient POSTGRES_PASSWORD may materialize a MISSING store only
# through the explicit INIT path, may never rewrite an existing store, and
# may never rotate/erase metadata. Denials have zero authority-side effects.
# --------------------------------------------------------------------------

def _seed_initialized_store() -> dict:
    """Write a fully-initialized approved store (password + worker token +
    b4_meta + an unrelated secret entry) — the state an already-initialized
    store has after configure + first start."""
    data = {
        "postgres_password": "s" * 40,
        "source": "generated",
        "worker_token": "w" * 40,
        "another_entry": "another-secret-value",
        "b4_meta": {"runtime-local": {"generation": 1, "revoked": False}},
    }
    ls.SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ls.SECRETS_FILE.write_text(json.dumps(data), encoding="utf-8")
    return data


def _mock_docker_runtime(monkeypatch) -> None:
    """Mock every docker/process surface so ll.start()/restart()/recover()
    run deterministically without a live stack."""
    monkeypatch.setattr(ll, "docker_available", lambda: True)
    monkeypatch.setattr(ll, "compose", lambda *a, **k: _FakeComp(0))
    monkeypatch.setattr(ll, "wait_ready", lambda *a, **k: True)
    monkeypatch.setattr(ll, "migrate", lambda: _FakeComp(0))
    monkeypatch.setattr(ll, "wait_for_http", lambda *a, **k: True)
    monkeypatch.setattr(ll, "smoke", lambda: [("health", True), ("console", True)])
    monkeypatch.setattr(ll, "start_process",
                        lambda *a, **k: ls.RUNTIME_DIR / "mock.pid")


def test_cxr4r1_a_start_never_rewrites_existing_store(monkeypatch):
    # A. existing store + ambient POSTGRES_PASSWORD + start() -> store hash
    #    BEFORE == AFTER (ordinary start fails closed, never rotates)
    _seed_initialized_store()
    before = _store_snapshot()
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-differs-9876543210")
    with pytest.raises(RuntimeError, match="explicit rotation path"):
        ll.start()
    assert _store_snapshot() == before


def test_cxr4r1_b_restart_never_rewrites_existing_store(monkeypatch):
    # B. same attack through restart (CLI restart = stop -> start): the safe
    #    shutdown half is always allowed; the activation half fails closed.
    _seed_initialized_store()
    before = _store_snapshot()
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-differs-9876543210")
    _mock_docker_runtime(monkeypatch)
    monkeypatch.setattr(ll, "stop_runtime_processes", lambda: [])
    ll.stop()
    with pytest.raises(RuntimeError, match="explicit rotation path"):
        ll.start()
    assert _store_snapshot() == before


def test_cxr4r1_c_recover_never_rewrites_existing_store(monkeypatch):
    # C. same attack through recover(): the repair path never consults an
    #    ambient password and never rewrites the approved store.
    _seed_initialized_store()
    before = _store_snapshot()
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-differs-9876543210")
    _mock_docker_runtime(monkeypatch)
    ll.recover()
    assert _store_snapshot() == before


def test_cxr4r1_d_e_meta_and_token_survive_start_restart_configure(monkeypatch):
    # D+E. b4_meta and worker_token survive configure/start/restart exactly;
    #    unrelated entries are never lost.
    _seed_initialized_store()
    before = _store_snapshot()
    ll.configure()
    assert _store_snapshot() == before
    _mock_docker_runtime(monkeypatch)
    ll.start()
    assert _store_snapshot() == before
    monkeypatch.setattr(ll, "stop_runtime_processes", lambda: [])
    ll.stop()
    ll.start()  # CLI restart semantics: stop -> start
    assert _store_snapshot() == before
    data = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))
    assert data["worker_token"] == "w" * 40
    assert data["b4_meta"]["runtime-local"]["generation"] == 1
    assert data["another_entry"] == "another-secret-value"


def test_cxr4r1_f_first_clean_initialization_still_works(monkeypatch):
    # F. explicit operator password on the FIRST governed init is honored;
    #    a clean init with no ambient value generates a strong secret.
    monkeypatch.setenv("POSTGRES_PASSWORD", "explicit-init-pw-1234567890")
    pw = ls.initialize_runtime_secret()
    assert pw == "explicit-init-pw-1234567890"
    assert ls.load_runtime_secret() == pw


def test_cxr4r1_g_rotation_changes_only_authorized_secret_and_generation():
    # G. explicit rotation is attributable + atomic: only the authorized
    #    secret value and its generation metadata change.
    _seed_initialized_store()
    backend = ls.RuntimeSecretBackend()
    assert backend.generation("runtime-local") == 1
    backend.rotate("runtime-local", "rotated-governed-secret-abcdef123456")
    data = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))
    assert data["postgres_password"] == "rotated-governed-secret-abcdef123456"
    assert data["worker_token"] == "w" * 40  # untouched
    assert data["another_entry"] == "another-secret-value"  # untouched
    assert data["b4_meta"]["runtime-local"]["generation"] == 2
    assert data["b4_meta"]["runtime-local"]["revoked"] is False


def test_cxr4r1_h_failed_initialization_never_partially_rewrites(monkeypatch):
    # H. corrupt existing store -> REFUSED (never destroyed); an atomic-write
    #    failure mid-init -> no partial secrets.json, no stray tmp file.
    ls.SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ls.SECRETS_FILE.write_text("{corrupt-not-json", encoding="utf-8")
    corrupt = ls.SECRETS_FILE.read_bytes()
    with pytest.raises(RuntimeError, match="unreadable/corrupt"):
        ls.initialize_runtime_secret()
    assert ls.SECRETS_FILE.read_bytes() == corrupt  # not overwritten
    ls.SECRETS_FILE.unlink()
    import os as _os

    def _boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(_os, "replace", _boom)
    with pytest.raises(OSError, match="disk full"):
        ls.initialize_runtime_secret()
    assert not ls.SECRETS_FILE.exists()  # no partial file
    assert not list(ls.RUNTIME_DIR.glob("*.tmp-*"))  # no stray tmp


# --------------------------------------------------------------------------
# Ports — loopback only
# --------------------------------------------------------------------------

def test_real_compose_ports_are_loopback_only():
    assert ll.published_ports_from_compose() == []


def test_bare_port_binding_rejected(monkeypatch, tmp_path):
    fake = tmp_path / "compose.yml"
    fake.write_text('services:\n  pg:\n    ports:\n      - "5433:5432"\n')
    monkeypatch.setattr(ll, "COMPOSE_FILE", fake)
    offenders = ll.published_ports_from_compose()
    assert any("binds all interfaces" in o for o in offenders)


def test_public_bind_rejected(monkeypatch, tmp_path):
    fake = tmp_path / "compose.yml"
    fake.write_text('services:\n  pg:\n    ports:\n      - "0.0.0.0:5433:5432"\n')
    monkeypatch.setattr(ll, "COMPOSE_FILE", fake)
    assert any("does not bind 127.0.0.1" in o for o in ll.published_ports_from_compose())


# --------------------------------------------------------------------------
# PID ownership — never pkill
# --------------------------------------------------------------------------

def test_lifecycle_module_never_uses_pkill():
    src = Path(ll.__file__).read_text(encoding="utf-8")
    # B2-R7 forbids broad pkill shutdown: pkill must never appear as a
    # quoted command literal (docstring prose may explain the prohibition).
    assert not re.search(r"['\"]pkill['\"]", src), "B2-R7 forbids pkill shutdown"


def test_stop_terminates_only_pid_file_process(monkeypatch):
    proc = _spawn_sleeper()
    try:
        pid = proc.pid
        path = ll.pid_file("worker")
        path.write_text(f"{pid}\n")
        monkeypatch.setattr(ll, "PROCESSES", {"worker": ("worker.pid", "time.sleep(600)")})
        actions = ll.stop_runtime_processes()
        deadline = time.time() + 15
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.1)
        assert proc.poll() is not None, f"recorded process was not terminated; actions={actions}"
        assert not path.exists(), "pid file should be cleared"
        assert any("terminated worker" in a for a in actions), f"actions={actions}"
    finally:
        if proc.poll() is None:
            proc.kill()


def test_stale_dead_pid_cleared_not_signalled():
    # a PID that cannot be running: reuse a finished process's pid
    probe = _spawn_sleeper()
    pid = probe.pid
    probe.terminate()
    probe.wait(timeout=10)
    path = ll.pid_file("api")
    path.write_text(f"{pid}\n")
    actions = ll.stop_runtime_processes()
    assert not path.exists(), "stale pid file must be cleared"
    assert any("stale" in a for a in actions)


def test_unrelated_process_never_signalled(monkeypatch):
    proc = _spawn_sleeper()  # cmdline does NOT contain the api marker
    try:
        pid = proc.pid
        path = ll.pid_file("api")
        path.write_text(f"{pid}\n")
        actions = ll.stop_runtime_processes()
        assert proc.poll() is None, "unrelated process must never be terminated"
        assert not path.exists(), "pid file cleared as stale"
        assert any("unrelated process" in a for a in actions)
    finally:
        proc.kill()
        proc.wait(timeout=10)


def test_pid_file_with_garbage_ignored():
    path = ll.pid_file("api")
    path.write_text("not-a-pid\n")
    state, detail = ll.pid_state(path, MARKER)
    assert state == "stale"
    assert "no parseable PID" in detail


# --------------------------------------------------------------------------
# Destructive authorization
# --------------------------------------------------------------------------

def test_destroy_requires_confirmation(monkeypatch):
    monkeypatch.setattr(ll, "compose", lambda *a, **k: None)
    with pytest.raises(SystemExit, match="DESTRUCTIVE"):
        ll.destroy(confirmed=False)


def test_destroy_removes_volume_only_with_yes(monkeypatch):
    calls = []
    monkeypatch.setattr(ll, "stop_runtime_processes", lambda: [])
    monkeypatch.setattr(ll, "compose", lambda *a, **k: calls.append(a) or _FakeComp(0))
    ll.destroy(confirmed=True)
    assert ("down", "-v") in calls, "durable volume removal must use compose down -v"


class _FakeComp:
    def __init__(self, rc):
        self.returncode = rc


# --------------------------------------------------------------------------
# Start / doctor / cloud-free posture
# --------------------------------------------------------------------------

def test_start_fails_closed_without_docker(monkeypatch):
    monkeypatch.setattr(ll, "docker_available", lambda: False)
    with pytest.raises(RuntimeError, match="Docker is unavailable"):
        ll.start()


def test_cloud_credential_hint_detects_cloud_env(monkeypatch):
    assert ll.cloud_credential_hint({"PATH": "/usr/bin", "HOME": "/root"}) == []
    hint = ll.cloud_credential_hint({"AWS_ACCESS_KEY_ID": "x", "PATH": "/usr/bin"})
    assert hint == ["AWS_ACCESS_KEY_ID"]


def test_doctor_reports_cloud_free_when_clean(monkeypatch, tmp_path):
    monkeypatch.setattr(ll, "docker_available", lambda: True)
    monkeypatch.setattr(ll, "published_ports_from_compose", lambda: [])
    monkeypatch.setattr(ll, "process_cmdline", lambda pid: None)
    monkeypatch.setattr(ls, "load_runtime_secret", lambda: "x" * 40)
    monkeypatch.setattr(ls, "SECRETS_FILE", tmp_path / "secrets.json")
    ls.SECRETS_FILE.write_text(json.dumps({"postgres_password": "x" * 40}))
    import subprocess as _sp
    monkeypatch.setattr(_sp, "run", lambda *a, **k: _FakeComp(0))
    result = ll.doctor()
    cloud = [c for c in result["checks"] if c["check"] == "no cloud credentials required"]
    assert cloud and cloud[0]["ok"] is True
