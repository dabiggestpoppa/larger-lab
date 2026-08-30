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


def test_require_runtime_dsn_prefers_environment(monkeypatch):
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://u:p@127.0.0.1:5433/db")
    assert ls.require_runtime_dsn() == "postgresql://u:p@127.0.0.1:5433/db"


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
        deadline = time.time() + 10
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.1)
        assert proc.poll() is not None, "recorded process was not terminated"
        assert not path.exists(), "pid file should be cleared"
        assert any("terminated worker" in a for a in actions)
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
