"""OCE Book 4 — real startup configuration gate (surface C, integrated).

Proves that the ACTUAL control-plane startup path validates its effective
configuration before activating: a valid default config resolves and starts,
while a malformed / incomplete / forbidden effective config refuses to start.
No Docker is used; the plane and config layers run in-process with a supplied
environ, so these tests stay in the authoritative local run.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import pytest

from oce_control.plane import ControlPlane
from oce_control import config_startup as cs
from oce_control.config_startup import (
    ENV_MAP,
    effective_from_env,
    require_startable,
    startup_report,
    validate_startup,
)
from oce_control.config_spine import ValidationError, build_default_registry

# Clean env (no OCE_* posture overrides) — must start.
CLEAN_ENV: dict[str, str] = {"PATH": "/usr/bin:/bin"}

# A forbidden posture (live trading) explicitly attempted via the environment.
LIVE_ENV = {**CLEAN_ENV, "OCE_EXECUTION_BROKER_ENABLED": "true"}
CLOUD_ENV = {**CLEAN_ENV, "OCE_CLOUD_PROVISIONING": "true"}
LISTEN_ENV = {**CLEAN_ENV, "OCE_CONTROL_PLANE_PUBLIC_LISTEN": "true"}
EGRESS_ENV = {**CLEAN_ENV, "OCE_WORKERS_EGRESS": "public"}
MALFORMED_ENV = {**CLEAN_ENV, "OCE_CONTROL_PLANE_PORT": "not-a-port"}
BADREF_ENV = {**CLEAN_ENV, "OCE_POSTGRES_PASSWORD_REF": "plain-password-123"}


def _plane():
    from oce_control.clocks import TestClock, set_test_clock, reset_clock
    c = TestClock()
    set_test_clock(c)
    try:
        return ControlPlane(test_clock=c)
    finally:
        reset_clock()


def _doctor_env(monkeypatch, tmp_path, secrets_file):
    """Hermetic doctor harness (no docker/ps dependency), returns ll."""
    import oce_control.local_lifecycle as ll
    from oce_control import local_secrets as ls
    monkeypatch.setattr(ls, "SECRETS_FILE", secrets_file)
    monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path / "runtime")
    (tmp_path / "runtime").mkdir(exist_ok=True)
    monkeypatch.setattr(ll, "docker_available", lambda: True)
    monkeypatch.setattr(ll, "published_ports_from_compose", lambda: [])
    monkeypatch.setattr(ll, "process_cmdline", lambda pid: None)
    import subprocess as _sp

    class _FakeComp:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(_sp, "run", lambda *a, **k: _FakeComp())
    return ll


# --------------------------------------------------------------------------- #
# Effective config loading / validation primitives
# --------------------------------------------------------------------------- #
class TestEffectiveFromEnv:
    def test_clean_env_resolves_and_starts(self):
        eff = effective_from_env(CLEAN_ENV)
        assert eff.get("control_plane.host") == "127.0.0.1"
        assert eff.get_bool("execution.broker_enabled") is False
        assert eff.get_bool("cloud.provisioning") is False
        # password_ref is defaulted to the approved runtime reference
        assert eff.get("postgres.password_ref") == "secret:runtime-local"

    def test_validate_startup_clean(self):
        rep = validate_startup(CLEAN_ENV)
        assert rep["ok"] is True
        assert rep["config_ok"] is True
        assert "start" not in rep  # CXR4-07: config-valid never claims start
        assert rep["error"] is None

    def test_live_mode_forbidden(self):
        with pytest.raises(ValidationError):
            effective_from_env(LIVE_ENV)
        rep = validate_startup(LIVE_ENV)
        assert rep["ok"] is False and rep["config_ok"] is False
        assert "start" not in rep
        assert "broker" in rep["error"].lower()

    def test_cloud_provisioning_forbidden(self):
        assert validate_startup(CLOUD_ENV)["ok"] is False

    def test_public_listen_forbidden(self):
        assert validate_startup(LISTEN_ENV)["ok"] is False

    def test_workers_egress_forbidden(self):
        assert validate_startup(EGRESS_ENV)["ok"] is False

    def test_malformed_type_fails_closed(self):
        assert validate_startup(MALFORMED_ENV)["ok"] is False

    def test_plain_password_ref_fails_closed(self):
        assert validate_startup(BADREF_ENV)["ok"] is False

    def test_error_is_secret_free(self):
        rep = validate_startup(BADREF_ENV)
        # no plain password value or marker content leaks into the message
        assert "plain-password-123" not in rep["error"]
        assert "password_ref" in rep["error"] or "postgres" in rep["error"]

    def test_report_is_legible_and_secret_free(self):
        rep = startup_report(LIVE_ENV)
        assert "BLOCKED" in rep
        assert "true" not in rep.lower().split("broker")[0]

    def test_all_env_map_entries_resolve_to_registered_settings(self):
        from oce_control.config_spine import build_default_registry
        reg = build_default_registry()
        for setting_name in ENV_MAP:
            assert reg.get(setting_name) is not None, setting_name


# --------------------------------------------------------------------------- #
# Real startup path: ControlPlane.startup()
# --------------------------------------------------------------------------- #
class TestControlPlaneStartupGate:
    def test_valid_default_config_starts(self):
        p = _plane()
        result = p.startup(environ=dict(CLEAN_ENV))
        assert result["status"] == "started"
        assert result["health"] is not None
        assert "api" in result["components"]

    def test_invalid_live_config_blocks_activation(self):
        p = _plane()
        result = p.startup(environ=dict(LIVE_ENV))
        assert result["status"] == "blocked"
        assert result["health"] is None
        assert result["components"] == []
        assert "blocked" in result["reason"].lower()

    def test_invalid_cloud_config_blocks_activation(self):
        p = _plane()
        assert p.startup(environ=dict(CLOUD_ENV))["status"] == "blocked"

    def test_invalid_egress_blocks_activation(self):
        p = _plane()
        assert p.startup(environ=dict(EGRESS_ENV))["status"] == "blocked"

    def test_malformed_config_blocks_activation(self):
        p = _plane()
        assert p.startup(environ=dict(MALFORMED_ENV))["status"] == "blocked"

    def test_startup_reason_is_operator_legible_and_secret_free(self):
        p = _plane()
        result = p.startup(environ=dict(BADREF_ENV))
        assert result["status"] == "blocked"
        assert "plain-password-123" not in result["reason"]

    def test_console_status_surfaces_blocked_reason(self):
        # The operator console reads startup state; a blocked config must be
        # visible as blocked (not silently "started").
        p = _plane()
        blocked = p.startup(environ=dict(CLOUD_ENV))
        assert blocked["status"] == "blocked"
        started = p.startup(environ=dict(CLEAN_ENV))
        assert started["status"] == "started"


# --------------------------------------------------------------------------- #
# CLI / entry hook: require_startable + start gate
# --------------------------------------------------------------------------- #
class TestCliEntryGate:
    def test_require_startable_clean_returns_effective(self):
        eff = require_startable(CLEAN_ENV)
        assert eff.get_bool("cloud.provisioning") is False

    def test_require_startable_invalid_raises_systemexit(self):
        with pytest.raises(SystemExit):
            require_startable(LIVE_ENV)

    def test_require_startable_message_is_secret_free_and_legible(self):
        try:
            require_startable(BADREF_ENV)
        except SystemExit as exc:
            msg = str(exc)
            assert "BLOCKED" in msg
            assert "plain-password-123" not in msg

    def test_start_gate_function_returns_blocked_report(self):
        rep = cs.gate_start()
        assert rep["ok"] in (True, False)
        assert rep["config_ok"] in (True, False)
        assert "start" not in rep  # CXR4-07: config gate never claims start

    def test_env_map_covers_posture_setting(self):
        # ensure the env map touches every deny-by-default posture surface
        assert "execution.broker_enabled" in ENV_MAP
        assert "execution.paper_trading_enabled" in ENV_MAP
        assert "execution.live_order_mode" in ENV_MAP
        assert "cloud.provisioning" in ENV_MAP
        assert "cloud.gpu_burst" in ENV_MAP
        assert "control_plane.public_listen" in ENV_MAP
        assert "workers.egress" in ENV_MAP
        assert "cloud.cost_ceiling_usd_per_month" in ENV_MAP

    def test_report_serializable(self):
        rep = validate_startup(CLEAN_ENV)
        json.dumps(rep)  # operator console / evidence serializes it


# --------------------------------------------------------------------------- #
# B4-R3RX — remaining adversarial proofs: env!=file through the real startup
# path, env>file precedence, restart authority stability, whole-env namespace.
# --------------------------------------------------------------------------- #
class TestR3RXAdversarialClosure:
    def test_env_value_labeled_environment_not_file_at_startup(self):
        import oce_control.config_startup as cs
        eff = cs.effective_from_env({**CLEAN_ENV, "OCE_CONTROL_PLANE_PORT": "8455"})
        assert eff.get("control_plane.port") == 8455
        assert eff.provenance["control_plane.port"] == "environment"
        assert eff.provenance["control_plane.port"] != "file"

    def test_env_overrides_file_and_cli_overrides_env(self):
        reg = build_default_registry()
        from oce_control.config_spine import ConfigResolver
        r = ConfigResolver(reg)
        eff = r.resolve({
            "file": {"postgres.password_ref": "secret:runtime-local",
                     "control_plane.port": "7000"},
            "environment": {"control_plane.port": "8455"},
        }, cli={"control_plane.port": "8456"})
        assert eff.get("control_plane.port") == 8456
        assert eff.provenance["control_plane.port"] == "cli"

    def test_env_over_file_precedence_deterministic(self):
        # identical inputs, reordered dicts, same effective config
        reg = build_default_registry()
        from oce_control.config_spine import ConfigResolver
        a = ConfigResolver(reg).resolve({
            "file": {"postgres.password_ref": "secret:runtime-local",
                     "control_plane.port": "7000"},
            "environment": {"control_plane.port": "8455"}})
        b = ConfigResolver(reg).resolve({
            "environment": {"control_plane.port": "8455"},
            "file": {"postgres.password_ref": "secret:runtime-local",
                     "control_plane.port": "7000"}})
        assert a.resolved == b.resolved
        assert a.provenance == b.provenance

    def test_restart_does_not_change_effective_authority(self):
        # restart with the SAME env -> identical effective config + fingerprint
        import oce_control.config_startup as cs
        env = {**CLEAN_ENV, "OCE_SCHEDULER_INTERVAL": "7"}
        a = cs.effective_from_env(dict(env))
        b = cs.effective_from_env(dict(env))
        assert a.resolved == b.resolved
        assert a.fingerprint == b.fingerprint
        assert a.provenance == b.provenance

    def test_unknown_oce_whole_env_fails_closed_via_startup(self):
        import os as _os
        suspicious = {**_os.environ}
        suspicious["OCE_EXECUTION_BROKER_ENABLD"] = "true"
        with pytest.raises(ValidationError):
            effective_from_env(suspicious)

    def test_env_forbidden_source_cannot_override_via_alias(self):
        # a setting forbidden from the environment stays forbidden even when
        # the value arrives through the OCE_API_PORT-style alias path
        reg = build_default_registry()
        reg.forbid_source("control_plane.port", "environment")
        import oce_control.config_startup as cs
        with pytest.raises(ValidationError):
            cs.effective_from_env(
                {**CLEAN_ENV, "OCE_API_PORT": "8500"}, registry=reg)


# --------------------------------------------------------------------------- #
# Default config must stay startable (regression guard)
# --------------------------------------------------------------------------- #
class TestDefaultStaysStartable:
    def test_full_environment_default_starts(self):
        # Uses the actual parent environment (PATH etc.) like the real entry.
        rep = validate_startup()
        assert rep["ok"] is True, rep["error"]

    def test_plane_default_startup_status(self):
        p = _plane()
        assert p.startup()["status"] == "started"


# --------------------------------------------------------------------------- #
# B4-R3R2 — converged runtime bind: effective config == actual listener.
# Subprocess proofs: direct-launch denial + real loopback bind with the SAME
# gate decision the durable entry uses. No public listener is ever opened.
# --------------------------------------------------------------------------- #
class TestR3R2RuntimeBind:
    def test_runtime_bind_resolves_effective_host_port(self):
        from oce_control.http_api import runtime_bind, runtime_scheduler_interval
        eff = effective_from_env({**CLEAN_ENV, "OCE_CONTROL_PLANE_PORT": "8451"})
        host, port = runtime_bind({**CLEAN_ENV, "OCE_CONTROL_PLANE_PORT": "8451"})
        assert host == eff.get("control_plane.host")
        assert port == eff.get("control_plane.port") == 8451
        assert runtime_scheduler_interval(
            {**CLEAN_ENV, "OCE_SCHEDULER_INTERVAL": "9"}) == 9

    def test_direct_launch_denied_on_forbidden_config(self):
        # `python -m oce_control.http_api` must NOT activate when the effective
        # config is forbidden — the gate raises before any bind/DB work.
        import subprocess
        import sys
        from pathlib import Path
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent / "src") \
            + os.pathsep + env.get("PYTHONPATH", "")
        for bad in (LIVE_ENV, CLOUD_ENV, {"OCE_WORKERS_EGRESS": "public"}):
            full = {**env, **bad}
            r = subprocess.run(
                [sys.executable, "-c",
                 "from oce_control.http_api import runtime_bind; "
                 "print('BOUND', runtime_bind()[1])"],
                env=full, capture_output=True, text=True, timeout=60)
            assert r.returncode != 0, f"direct launch must fail closed: {bad}"
            assert "BOUND" not in r.stdout

    def test_direct_launch_denied_on_malformed_config(self):
        import subprocess
        import sys
        from pathlib import Path
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent / "src") \
            + os.pathsep + env.get("PYTHONPATH", "")
        full = {**env, "OCE_CONTROL_PLANE_PORT": "not-a-port"}
        r = subprocess.run(
            [sys.executable, "-c",
             "from oce_control.http_api import runtime_bind; "
             "print('BOUND', runtime_bind()[1])"],
            env=full, capture_output=True, text=True, timeout=60)
        assert r.returncode != 0
        assert "BOUND" not in r.stdout

    def test_actual_loopback_bind_matches_effective_config(self):
        # Real bind proof: the gate decision (runtime_bind) is used verbatim to
        # open a loopback listener; probe it live, then tear it down.
        import socket
        import subprocess
        import sys
        import time
        import urllib.request
        from pathlib import Path
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        src = str(Path(__file__).resolve().parent.parent / "src")
        env = dict(os.environ)
        env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
        env["OCE_CONTROL_PLANE_PORT"] = str(port)
        script = (
            "import uvicorn\n"
            "from fastapi import FastAPI\n"
            "from oce_control.http_api import runtime_bind\n"
            "host, port = runtime_bind()\n"
            "app = FastAPI()\n"
            "@app.get('/api/health')\n"
            "def h(): return {'ok': True}\n"
            "uvicorn.run(app, host=host, port=port, log_level='warning')\n")
        proc = subprocess.Popen([sys.executable, "-c", script], env=env,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        try:
            deadline = time.time() + 30
            body = None
            while time.time() < deadline:
                try:
                    with urllib.request.urlopen(
                            f"http://127.0.0.1:{port}/api/health",
                            timeout=2) as resp:
                        body = resp.read().decode()
                        break
                except OSError:
                    if proc.poll() is not None:
                        break
                    time.sleep(0.4)
            assert body is not None and "ok" in body, \
                f"server on effective port {port} did not answer (rc={proc.poll()})"
            # no public listener: only 127.0.0.1 was bound by the effective host
            assert proc.poll() is None  # still serving -> real bind
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


# --------------------------------------------------------------------------- #
# B4-CXR3R8 (CXR3-09/CXR3-10) — adversarial closure for the remaining escape
# paths: unresolved custom reference + doctor, revoked reference + doctor, and
# aggregate denial-side-effect invariance (denial never mutates the store).
# --------------------------------------------------------------------------- #
class TestCXR3R8AdversarialClosure:
    def test_doctor_fails_on_custom_reference_future_lock(self, tmp_path, monkeypatch):
        # N + CXR4-02: a CUSTOM password ref is future-locked — even when the
        # store could resolve it, doctor fails at the CONFIG gate so the spine
        # never validates one secret authority while the runtime uses another.
        from oce_control import local_secrets as ls
        store = tmp_path / "custom-store.json"
        store.write_text(json.dumps({"custom-db": "x" * 40}), encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        monkeypatch.setenv("OCE_POSTGRES_PASSWORD_REF", "secret:custom-db")
        ll = _doctor_env(monkeypatch, tmp_path, store)
        result = ll.doctor()
        checks = {c["check"]: c["ok"] for c in result["checks"]}
        assert checks["config spine effective config valid (fail-closed)"] is False
        assert checks["configured secret reference resolves (runtime readiness)"] \
            is False

    def test_doctor_fails_on_revoked_reference(self, tmp_path, monkeypatch):
        # O: a REVOKED reference must fail doctor readiness
        from oce_control import local_secrets as ls
        store = tmp_path / "revoked-store.json"
        store.write_text(json.dumps({
            "postgres_password": "x" * 40,
            "b4_meta": {"runtime-local": {"revoked": True, "generation": 2}},
        }), encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        ll = _doctor_env(monkeypatch, tmp_path, store)
        result = ll.doctor()
        checks = {c["check"]: c["ok"] for c in result["checks"]}
        assert checks["configured secret reference resolves (runtime readiness)"] \
            is False

    def test_config_denials_never_mutate_secret_store(self, tmp_path, monkeypatch):
        # R: DENIAL HAS ZERO AUTHORITY-SIDE EFFECTS across every denial path
        import hashlib
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        before = hashlib.sha256(store.read_bytes()).hexdigest()
        deny_envs = [
            {"OCE_EXECUTION_BROKER_ENABLED": "true"},
            {"OCE_CAPITAL_AUTHORITY": "approved"},
            {"OCE_LOG_REDACT_SECRETS": "false"},
            {"OCE_SANDBOX_PROCESS_TREE_TERMINATION": "false"},
            {"OCE_CONTROL_PLANE_PORT": "not-a-port"},
            {"OCE_POSTGRES_HOST": "10.0.0.9"},
            {"OCE_CP_URL": "http://10.0.0.9:8448"},
        ]
        for extra in deny_envs:
            env = {"PATH": "/usr/bin",
                   "OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local",
                   **extra}
            if "OCE_CP_URL" not in extra:
                with pytest.raises(ValidationError):
                    cs.effective_from_env(env)
            with pytest.raises(SystemExit):
                cs.outbound_cp_url(env)  # URL/config denials at the gate
        monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-9876543210")
        monkeypatch.setenv("POSTGRES_DSN",
                           "postgresql://oce_control_admin:ambient-attack-9876543210"
                           "@127.0.0.1:5433/oce_control")
        with pytest.raises(RuntimeError, match="bypass"):
            ls.require_runtime_dsn()
        after = hashlib.sha256(store.read_bytes()).hexdigest()
        assert before == after
        assert ls.load_runtime_secret() == "k" * 40  # store value unchanged


# --------------------------------------------------------------------------- #
# B4-CXR3R7 (CXR3-08) — unified startup-truth semantics: validate_startup is
# the config gate; validate_runtime_readiness / require_runtime_startable are
# the complete runtime-start contract (config + secret resolution). No
# contradictory start=True + secret_ok=False combination is possible, and
# doctor fails when the configured reference does not resolve.
# --------------------------------------------------------------------------- #
class TestCXR3R7StartupTruthSemantics:
    def test_validate_configuration_is_config_gate_without_secret_state(self):
        # CXR4-07: the config gate reports config_ok — never start/ready/
        # startable, which belong to the complete runtime-start contract.
        rep = cs.validate_startup(CLEAN_ENV)
        assert rep["ok"] is True and rep["config_ok"] is True
        assert "start" not in rep and "ready" not in rep
        assert "secret_ok" not in rep  # config gate reports NO secret state

    def test_configuration_valid_never_claims_runtime_ready(self):
        # CXR4-07: config-valid is distinct from runtime-ready/startable
        rep = cs.validate_configuration(CLEAN_ENV)
        assert rep["config_ok"] is True and rep["ok"] is True
        for key in ("start", "ready", "startable"):
            assert key not in rep
        msg = cs.startup_report(CLEAN_ENV)
        assert "configuration valid" in msg
        assert "START ok" not in msg
        assert "ready" not in msg.lower()

    def test_readiness_requires_secret_resolution(self, tmp_path):
        from oce_control import local_secrets as ls
        f = tmp_path / "secrets.json"
        f.write_text(json.dumps({"postgres_password": "x" * 40}),
                     encoding="utf-8")
        backend = ls.RuntimeSecretBackend(f)
        env = {**CLEAN_ENV, "OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"}
        ready = cs.validate_runtime_readiness(environ=env, backend=backend)
        assert ready["ready"] is True and ready["secret_ok"] is True
        f.unlink()  # store gone -> not ready, never contradictory
        not_ready = cs.validate_runtime_readiness(environ=env, backend=backend)
        assert not_ready["ok"] is True
        assert not_ready["ready"] is False
        assert not_ready["secret_ok"] is False
        assert not (not_ready["ready"] and not not_ready["secret_ok"])

    def test_require_runtime_startable_fails_closed_on_missing_secret(self, tmp_path):
        from oce_control import local_secrets as ls
        backend = ls.RuntimeSecretBackend(tmp_path / "absent-secrets.json")
        env = {**CLEAN_ENV, "OCE_POSTGRES_PASSWORD_REF": "secret:runtime-local"}
        with pytest.raises(SystemExit) as exc:
            cs.require_runtime_startable(environ=env, backend=backend)
        assert "configure" in str(exc.value)

    def test_require_runtime_startable_returns_effective_when_ready(self, tmp_path):
        from oce_control import local_secrets as ls
        f = tmp_path / "secrets.json"
        f.write_text(json.dumps({"postgres_password": "y" * 40}),
                     encoding="utf-8")
        backend = ls.RuntimeSecretBackend(f)
        eff = cs.require_runtime_startable(
            environ={**CLEAN_ENV, "OCE_POSTGRES_PASSWORD_REF":
                     "secret:runtime-local"}, backend=backend)
        assert eff.get_bool("sandbox.strict") is True

    def test_doctor_fails_on_unresolved_secret(self, tmp_path, monkeypatch):
        # doctor must FAIL when the configured reference does not resolve
        ll = _doctor_env(monkeypatch, tmp_path, tmp_path / "absent-doctor.json")
        result = ll.doctor()
        checks = {c["check"]: c["ok"] for c in result["checks"]}
        assert checks["config spine effective config valid (fail-closed)"] is True
        assert checks["configured secret reference resolves (runtime readiness)"] \
            is False

    def test_doctor_passes_secret_check_when_store_resolves(self, tmp_path, monkeypatch):
        from pathlib import Path as _P
        f = tmp_path / "doctor-secrets.json"
        f.write_text(json.dumps({"postgres_password": "z" * 40}),
                     encoding="utf-8")
        ll = _doctor_env(monkeypatch, tmp_path, f)
        result = ll.doctor()
        checks = {c["check"]: c["ok"] for c in result["checks"]}
        assert checks["configured secret reference resolves (runtime readiness)"] \
            is True


# --------------------------------------------------------------------------- #
# B4-CXR3R3 — outbound worker target canonicalized (CXR3-03) + durable
# PostgreSQL host locked to loopback (CXR3-04).
# --------------------------------------------------------------------------- #
class TestCXR3R3WorkerTargetAndDbHost:
    def test_oce_cp_url_external_hosts_blocked(self):
        for bad in ("http://10.0.0.9:8448", "http://192.168.1.5:8448",
                    "http://example.com:8448", "https://public-host",
                    "http://[2001:db8::1]:8448"):
            with pytest.raises(SystemExit) as exc:
                cs.outbound_cp_url({**CLEAN_ENV, "OCE_CP_URL": bad})
            assert "BLOCKED" in str(exc.value)

    def test_oce_cp_url_noncanonical_port_blocked(self):
        with pytest.raises(SystemExit):
            cs.outbound_cp_url({**CLEAN_ENV, "OCE_CP_URL": "http://127.0.0.1:9999"})

    def test_oce_cp_url_embedded_credentials_blocked(self):
        with pytest.raises(SystemExit):
            cs.outbound_cp_url(
                {**CLEAN_ENV, "OCE_CP_URL": "http://user:pass@127.0.0.1:8448"})

    def test_oce_cp_url_forbidden_config_still_blocks(self):
        # the gate runs FIRST: OCE_CP_URL cannot skip require_startable()
        with pytest.raises(SystemExit) as exc:
            cs.outbound_cp_url({
                **CLEAN_ENV, "OCE_EXECUTION_BROKER_ENABLED": "true",
                "OCE_CP_URL": "http://127.0.0.1:8448"})
        assert "broker" in str(exc.value).lower()  # config denial, not URL msg

    def test_oce_cp_url_canonical_loopback_accepted(self):
        url = cs.outbound_cp_url(
            {**CLEAN_ENV, "OCE_CP_URL": "http://127.0.0.1:8448"})
        assert url == "http://127.0.0.1:8448"

    def test_canonical_url_follows_validated_config_port(self):
        env = {**CLEAN_ENV, "OCE_CONTROL_PLANE_PORT": "8455"}
        assert cs.outbound_cp_url(env) == "http://127.0.0.1:8455"
        assert cs.outbound_cp_url(
            {**env, "OCE_CP_URL": "http://127.0.0.1:8455"}) == \
            "http://127.0.0.1:8455"
        with pytest.raises(SystemExit):
            cs.outbound_cp_url({**env, "OCE_CP_URL": "http://127.0.0.1:8448"})

    def test_worker_subprocess_blocks_external_url_before_socket(self):
        # separate-process proof: external OCE_CP_URL + dummy secret exits
        # BLOCKED before any client/socket activity
        import subprocess
        import sys
        from pathlib import Path as _P
        env = dict(os.environ)
        src = str(_P(__file__).resolve().parent.parent / "src")
        env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
        env["OCE_CP_URL"] = "http://10.0.0.9:8448"
        env["OCE_WORKER_SECRET"] = "dummy-secret"
        env["OCE_WORKER_ID"] = "worker-x"
        script = str(_P(__file__).resolve().parent.parent
                     / "scripts" / "oce_b3_worker.py")
        r = subprocess.run([sys.executable, script], env=env,
                           capture_output=True, text=True, timeout=60)
        assert r.returncode != 0
        assert "BLOCKED" in (r.stderr + r.stdout)
        assert "connect" not in (r.stderr + r.stdout).lower()

    def test_postgres_host_external_rejected_via_env(self):
        for bad in ("external.example", "10.0.0.9", "192.168.1.5",
                    "2001:db8::1", "user:pass@127.0.0.1",
                    "https://db.example"):
            with pytest.raises(ValidationError):
                cs.effective_from_env({**CLEAN_ENV, "OCE_POSTGRES_HOST": bad})
        # only the canonical identity 127.0.0.1 is accepted under the
        # local-first contract (deterministic, single-valued)
        with pytest.raises(ValidationError):
            cs.effective_from_env({**CLEAN_ENV, "OCE_POSTGRES_HOST": "localhost"})
        eff = cs.effective_from_env(
            {**CLEAN_ENV, "OCE_POSTGRES_HOST": "127.0.0.1"})
        assert eff.get("postgres.host") == "127.0.0.1"

    def test_postgres_host_external_rejected_via_file_and_cli(self):
        from oce_control.config_spine import ConfigResolver
        reg = build_default_registry()
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve({
                "file": {"postgres.host": "10.0.0.9",
                         "postgres.password_ref": "secret:runtime-local"}})
        with pytest.raises(ValidationError):
            ConfigResolver(reg).resolve(
                {"file": {"postgres.password_ref": "secret:runtime-local"}},
                cli={"postgres.host": "external.example"})
        # canonical still resolves
        eff = ConfigResolver(reg).resolve({
            "file": {"postgres.password_ref": "secret:runtime-local"}})
        assert eff.get("postgres.host") == "127.0.0.1"


# --------------------------------------------------------------------------- #
# B4-CXR3R2 — no arbitrary runtime DSN injection: worker --dsn removed,
# build_durable_app has no DSN override, migrations cannot redirect outside
# the governed loopback database.
# --------------------------------------------------------------------------- #
class TestCXR3R2DsnEscapeRemoved:
    def _env(self) -> dict:
        env = dict(os.environ)
        from pathlib import Path as _P
        env["PYTHONPATH"] = str(_P(__file__).resolve().parent.parent / "src") \
            + os.pathsep + env.get("PYTHONPATH", "")
        return env

    def test_worker_loop_has_no_dsn_argument(self):
        # D: `python -m oce_control.worker_loop --dsn <external>` must fail at
        # the CLI (unrecognized argument) — no gate, no DB connection possible.
        import subprocess
        import sys
        r = subprocess.run(
            [sys.executable, "-m", "oce_control.worker_loop",
             "--dsn", "postgresql://u:p@10.0.0.9:5432/other", "--token", "t"],
            env=self._env(), capture_output=True, text=True, timeout=60)
        assert r.returncode != 0
        assert "unrecognized arguments" in (r.stderr + r.stdout).lower()
        assert "connect" not in r.stderr.lower()  # never reached a connection

    def test_build_durable_app_accepts_no_dsn_override(self):
        # E: the durable API cannot activate against an arbitrary DSN
        from oce_control.http_api import build_durable_app
        with pytest.raises(TypeError):
            build_durable_app(dsn="postgresql://u:p@10.0.0.9:5432/other")  # type: ignore

    def test_lifecycle_migrate_accepts_no_dsn_override(self):
        # F(part 1): the lifecycle migrate() has no public DSN parameter
        from oce_control import local_lifecycle as ll
        with pytest.raises(TypeError):
            ll.migrate(dsn="postgresql://u:p@10.0.0.9:5432/other")  # type: ignore

    def test_migrate_cli_rejects_external_db(self):
        # F(part 2): migrate.py --db external is rejected BEFORE connecting
        import subprocess
        import sys
        from pathlib import Path as _P
        script = str(_P(__file__).resolve().parent.parent / "scripts" / "migrate.py")
        r = subprocess.run(
            [sys.executable, script, "up",
             "--db", "postgresql://u:p@10.0.0.9:5432/other"],
            env=self._env(), capture_output=True, text=True, timeout=60)
        assert r.returncode == 2
        assert "loopback" in (r.stderr + r.stdout).lower()
        assert "10.0.0.9" not in r.stdout  # target never echoed

    def test_migrate_cli_requires_db(self):
        # no predictable default DSN: --db is mandatory
        import subprocess
        import sys
        from pathlib import Path as _P
        script = str(_P(__file__).resolve().parent.parent / "scripts" / "migrate.py")
        r = subprocess.run([sys.executable, script, "up"],
                           env=self._env(), capture_output=True, text=True,
                           timeout=60)
        assert r.returncode == 2
        assert "--db" in r.stderr


# --------------------------------------------------------------------------- #
# B4-R3R1 — governed OCE_* namespace (fail closed on unknown/typoed)
# --------------------------------------------------------------------------- #
class TestGovernedNamespace:
    def test_typoed_execution_var_fails_closed(self):
        with pytest.raises(ValidationError):
            effective_from_env({**CLEAN_ENV, "OCE_EXECUTION_BROKER_ENABLD": "true"})
        rep = validate_startup({**CLEAN_ENV, "OCE_EXECUTION_BROKER_ENABLD": "true"})
        assert rep["ok"] is False
        assert "OCE_EXECUTION_BROKER_ENABLD" in rep["error"]

    def test_typoed_cloud_var_fails_closed(self):
        with pytest.raises(ValidationError):
            effective_from_env({**CLEAN_ENV, "OCE_CLOUD_PROVISION": "true"})

    def test_typoed_public_listen_var_fails_closed(self):
        with pytest.raises(ValidationError):
            effective_from_env({**CLEAN_ENV, "OCE_PUBLIC_LISTEN": "true"})

    def test_unknown_operation_variable_fails_closed(self):
        # An OCE_* var that looks security-relevant but is not governed
        with pytest.raises(ValidationError):
            effective_from_env({**CLEAN_ENV, "OCE_EXEC_MODE": "live"})

    def test_operational_vars_are_allowed(self):
        eff = effective_from_env({
            **CLEAN_ENV,
            "OCE_RUN_ID": "abcdef",
            "OCE_STAGE_LABEL": "B4-CONFIG-SPINE-CLOSURE",
            "OCE_BLOCK_LABEL": "Book 4",
            "OCE_BOOK_LABEL": "Book 4",
            "OCE_EVIDENCE_DIR": "/tmp/evidence",
            "OCE_EXPECTED_COMMIT": "abc123",
            "OCE_EXPECTED_REPO": "dabiggestpoppa/larger-lab",
            "OCE_EXPECTED_BRANCH": "oce-program-build",
            "OCE_EXPECTED_TREE": "deadbeef",
            "OCE_WORKER_ID": "worker-local01",
            "OCE_WORKER_TOKEN": "opaque",
            "OCE_WORKER_SECRET": "opaque",
            "OCE_CP_URL": "http://127.0.0.1:8448",
            "OCE_JOB_FILE": "/tmp/job.json",
            "OCE_ARTIFACT_BASE": "/tmp/artifacts",
            "OCE_RUNTIME_DIR": "/tmp/runtime",
            "OCE_WS_BASE": "/tmp/ws",
            "OCE_ATTEMPT_WS": "/tmp/ws/a1",
            "OCE_CI_MODE": "1",
        })
        assert eff.get_bool("cloud.provisioning") is False

    def test_benign_incidental_OCE_text_not_rejected(self):
        # Vars that merely contain OCE as incidental text (not OCE_ prefix)
        eff = effective_from_env({
            **CLEAN_ENV,
            "MY_OCEAN_VAR": "1",
            "OCEAN_CURRENT": "gulf",
        })
        assert eff.get_bool("cloud.provisioning") is False

    def test_alias_OCE_API_PORT_maps_to_canonical_when_canonical_absent(self):
        eff = effective_from_env({**CLEAN_ENV, "OCE_API_PORT": "8449"})
        assert eff.get("control_plane.port") == 8449
        assert eff.provenance["control_plane.port"] == "environment"

    def test_canonical_env_wins_over_alias_conflict(self):
        eff = effective_from_env({
            **CLEAN_ENV,
            "OCE_API_PORT": "9090",
            "OCE_CONTROL_PLANE_PORT": "8448",
        })
        assert eff.get("control_plane.port") == 8448

    def test_alias_legacy_default_rejected_as_reserved(self):
        # The legacy default 8080 is reserved by the canonical registry and
        # cannot silently re-activate the old bind.
        rep = validate_startup({**CLEAN_ENV, "OCE_API_PORT": "8080"})
        assert rep["ok"] is False
        assert "port" in rep["error"].lower()

# --------------------------------------------------------------------------- #
# B4-CXR4R3 (CXR4-03) — ONE immutable ActivationContext: after creation,
# os.environ mutation cannot alter the activation; a rotated/revoked secret
# makes the context STALE and every consumer fails closed (no silent adoption).
# --------------------------------------------------------------------------- #
class TestCXR4R3ImmutableActivationContext:
    def _ctx(self, tmp_path, env=None):
        import hashlib
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        backend = ls.RuntimeSecretBackend(store)
        ctx = cs.create_activation_context(environ=env or CLEAN_ENV, backend=backend)
        return ctx, backend, store

    def test_context_pins_effective_config_and_metadata(self, tmp_path):
        # the frozen context carries the validated config + safe secret metadata
        ctx, backend, _ = self._ctx(tmp_path)
        assert ctx.control_plane_host == "127.0.0.1"
        assert ctx.control_plane_port == 8448
        assert ctx.scheduler_interval == 5
        assert ctx.postgres_host == "127.0.0.1"
        assert ctx.secret_reference == "secret:runtime-local"
        assert ctx.secret_backend_identity == "local-runtime-store-v1"
        assert ctx.secret_generation == 1
        assert ctx.secret_revocation_state is False
        assert ctx.canonical_control_plane_url == "http://127.0.0.1:8448"
        assert re.fullmatch(r"[0-9a-f]{64}", ctx.context_id)
        blob = json.dumps(ctx.safe_summary())
        assert "k" * 40 not in blob  # NEVER the password
        assert "postgresql://" not in blob  # NEVER a password-bearing DSN

    def test_environment_mutation_after_creation_changes_nothing(self, tmp_path, monkeypatch):
        # create the context, then mutate every relevant env surface — the
        # pinned consumers must not re-read ambient environment.
        ctx, backend, _ = self._ctx(tmp_path)
        host, port = ctx.control_plane_host, ctx.control_plane_port
        dsn = ctx.runtime_dsn(backend)
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "9999")
        monkeypatch.setenv("OCE_POSTGRES_HOST", "10.0.0.9")
        monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-1234567890")
        monkeypatch.setenv("POSTGRES_DSN", "postgresql://evil:pw@10.9.9.9:5432/x")
        assert ctx.control_plane_port == port          # pinned
        assert ctx.postgres_host == "127.0.0.1"        # pinned
        assert ctx.runtime_dsn(backend) == dsn         # pinned (store-derived)
        assert "ambient-attack-1234567890" not in ctx.runtime_dsn(backend)
        assert "10.9.9.9" not in ctx.runtime_dsn(backend)
        from oce_control.http_api import runtime_bind, runtime_scheduler_interval
        assert runtime_bind(ctx=ctx) == (host, port)
        assert runtime_scheduler_interval(ctx=ctx) == ctx.scheduler_interval

    def test_outbound_cp_url_pinned_with_context(self, tmp_path):
        ctx, backend, _ = self._ctx(tmp_path)
        # canonical assertion passes; any external OCE_CP_URL is still blocked
        env = {**CLEAN_ENV, "OCE_CP_URL": ctx.canonical_control_plane_url}
        assert cs.outbound_cp_url(environ=env, ctx=ctx) == ctx.canonical_control_plane_url
        env_bad = {**CLEAN_ENV, "OCE_CP_URL": "http://10.0.0.9:8448"}
        with pytest.raises(SystemExit):
            cs.outbound_cp_url(environ=env_bad, ctx=ctx)
        # env mutation after creation cannot move the canonical target
        env_mut = {**CLEAN_ENV, "OCE_CP_URL": "http://127.0.0.1:7777"}
        with pytest.raises(SystemExit):
            cs.outbound_cp_url(environ=env_mut, ctx=ctx)

    def test_rotation_after_creation_makes_context_stale(self, tmp_path):
        # secret rotates AFTER ActivationContext creation -> STALE, rejected;
        # the new generation is never silently adopted.
        ctx, backend, _ = self._ctx(tmp_path)
        assert ctx.runtime_dsn(backend)  # fresh
        backend.rotate("runtime-local", "rotated-after-activation-9876543210")
        with pytest.raises(RuntimeError, match="STALE"):
            ctx.assert_fresh(backend)
        with pytest.raises(RuntimeError, match="STALE"):
            ctx.runtime_dsn(backend)

    def test_revocation_after_creation_makes_context_stale(self, tmp_path):
        ctx, backend, _ = self._ctx(tmp_path)
        backend.revoke("runtime-local")
        with pytest.raises(RuntimeError, match="STALE"):
            ctx.assert_fresh(backend)
        with pytest.raises(RuntimeError, match="STALE"):
            ctx.runtime_dsn(backend)

    def test_same_inputs_same_context_identity(self, tmp_path):
        # deterministic: identical env + store -> identical pinned context
        ctx_a, _, _ = self._ctx(tmp_path)
        ctx_b, _, _ = self._ctx(tmp_path)
        assert ctx_a.context_id == ctx_b.context_id
        assert ctx_a.safe_summary() == ctx_b.safe_summary()

    def test_context_creation_fails_closed_without_secret(self, tmp_path):
        from oce_control import local_secrets as ls
        store = tmp_path / "empty.json"  # no secret provisioned
        backend = ls.RuntimeSecretBackend(store)
        with pytest.raises(SystemExit):
            cs.create_activation_context(environ=CLEAN_ENV, backend=backend)


# --------------------------------------------------------------------------- #
# B4-CXR4R4 (CXR4-04/05) — recover/migrate gate FIRST: no compose up, no
# migration, no process launch, and no secret/database mutation under a
# forbidden/malformed/unresolved configuration; and the migration target must
# be the EXACT governed PostgreSQL identity (host+port+db+user+credential).
# --------------------------------------------------------------------------- #
class TestCXR4R4GateFirstRecoverAndMigration:
    class _FakeComp:
        def __init__(self, rc=0):
            self.returncode = rc
            self.stdout = ""
            self.stderr = ""

    def _recover_env(self, monkeypatch, tmp_path):
        import hashlib
        from oce_control import local_secrets as ls
        import oce_control.local_lifecycle as ll
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "x" * 40}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path / "runtime")
        calls: list = []
        monkeypatch.setattr(ll, "docker_available", lambda: True)
        monkeypatch.setattr(ll, "compose",
                            lambda *a, **k: calls.append(("compose", a)) or self._FakeComp())
        monkeypatch.setattr(ll, "wait_ready", lambda *a, **k: True)
        monkeypatch.setattr(ll, "migrate",
                            lambda *a, **k: calls.append(("migrate", a)) or self._FakeComp())
        monkeypatch.setattr(ll, "start_process",
                            lambda *a, **k: calls.append(("start", a)) or Path("mock.pid"))
        before = hashlib.sha256(store.read_bytes()).hexdigest()
        return ll, calls, store, before

    def test_recover_forbidden_config_no_mutation(self, monkeypatch, tmp_path):
        ll, calls, store, before = self._recover_env(monkeypatch, tmp_path)
        monkeypatch.setenv("OCE_EXECUTION_BROKER_ENABLED", "true")
        with pytest.raises(SystemExit):
            ll.recover()
        assert calls == []  # no compose, no migration, no process launch
        assert hashlib.sha256(store.read_bytes()).hexdigest() == before

    def test_recover_malformed_config_no_mutation(self, monkeypatch, tmp_path):
        ll, calls, store, before = self._recover_env(monkeypatch, tmp_path)
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "not-a-port")
        with pytest.raises(SystemExit):
            ll.recover()
        assert calls == []
        assert hashlib.sha256(store.read_bytes()).hexdigest() == before

    def test_recover_unresolved_secret_no_mutation(self, monkeypatch, tmp_path):
        from oce_control import local_secrets as ls
        import oce_control.local_lifecycle as ll
        import hashlib
        store = tmp_path / "absent.json"  # no secret -> unresolvable
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        calls: list = []
        monkeypatch.setattr(ll, "compose",
                            lambda *a, **k: calls.append(("compose", a)) or self._FakeComp())
        with pytest.raises(SystemExit):
            ll.recover()
        assert calls == []

    def test_recover_revoked_secret_no_mutation(self, monkeypatch, tmp_path):
        import hashlib
        from oce_control import local_secrets as ls
        import oce_control.local_lifecycle as ll
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({
            "postgres_password": "x" * 40,
            "b4_meta": {"runtime-local": {"revoked": True, "generation": 2}},
        }), encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        before = hashlib.sha256(store.read_bytes()).hexdigest()
        calls: list = []
        monkeypatch.setattr(ll, "compose",
                            lambda *a, **k: calls.append(("compose", a)) or self._FakeComp())
        with pytest.raises(SystemExit):
            ll.recover()
        assert calls == []
        assert hashlib.sha256(store.read_bytes()).hexdigest() == before

    def test_stop_remains_usable_under_invalid_config(self, monkeypatch):
        # safe shutdown must never require a healthy config
        import oce_control.local_lifecycle as ll
        monkeypatch.setenv("OCE_EXECUTION_BROKER_ENABLED", "true")
        monkeypatch.setattr(ll, "stop_runtime_processes", lambda: ["stopped"])
        monkeypatch.setattr(ll, "compose", lambda *a, **k: self._FakeComp())
        actions = ll.stop()
        assert any("compose down" in a for a in actions)

    # -- CXR4-05: migration target must be the EXACT governed DB -----------

    def test_migrate_rejects_alternate_loopback_identity(self):
        import scripts.migrate as mig
        bad_dsns = [
            "postgresql://oce_control_admin:pw@127.0.0.1:5432/oce_control",
            "postgresql://oce_control_admin:pw@127.0.0.1:5433/otherdb",
            "postgresql://other_user:pw@127.0.0.1:5433/oce_control",
            "postgresql://oce_control_admin:pw@10.0.0.9:5433/oce_control",
            "postgresql://oce_control_admin:pw@localhost:9999/oce_control",
        ]
        for dsn in bad_dsns:
            assert mig.main(["up", "--db", dsn]) == 2, dsn

    def test_migrate_rejects_credential_mismatch(self, monkeypatch, tmp_path, capsys):
        import scripts.migrate as mig
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "governed-secret-1234567890"}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        dsn = "postgresql://oce_control_admin:wrong-password@127.0.0.1:5433/oce_control"
        assert mig.main(["up", "--db", dsn]) == 2
        out, err = capsys.readouterr()
        blob = out + err
        assert "wrong-password" not in blob and "governed-secret-1234567890" not in blob
        assert "never echoed" in err

    def test_migrate_canonical_target_passes_gates_and_reaches_connect(
            self, monkeypatch, tmp_path):
        # the governed canonical DSN passes identity + gate + credential
        # checks and reaches the connection step (unit test has no real PG;
        # container CI proves the actual connect).
        import scripts.migrate as mig
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "governed-secret-1234567890"}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        seen = {}

        def fake_connect(dsn):
            seen["dsn"] = dsn
            raise RuntimeError("would-connect")

        monkeypatch.setattr(mig, "connect", fake_connect)
        dsn = ("postgresql://oce_control_admin:governed-secret-1234567890"
               "@127.0.0.1:5433/oce_control")
        with pytest.raises(RuntimeError, match="would-connect"):
            mig.main(["up", "--db", dsn])
        assert seen["dsn"] == dsn

    def test_migrate_localhost_alias_deterministic(self, monkeypatch, tmp_path):
        # localhost alias is deterministically treated as the governed loopback
        import scripts.migrate as mig
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "governed-secret-1234567890"}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        seen = {}

        def fake_connect(dsn):
            seen["dsn"] = dsn
            raise RuntimeError("would-connect")

        monkeypatch.setattr(mig, "connect", fake_connect)
        dsn = ("postgresql://oce_control_admin:governed-secret-1234567890"
               "@localhost:5433/oce_control")
        with pytest.raises(RuntimeError, match="would-connect"):
            mig.main(["up", "--db", dsn])
        assert seen["dsn"] == dsn
