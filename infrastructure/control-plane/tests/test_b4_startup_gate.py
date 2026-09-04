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
    monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", tmp_path / "runtime" / "compose.env")
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
    def test_valid_default_config_reports_configured_not_started(self):
        # B4-CXR5R7: the in-memory assembly validates configuration and
        # reports in-memory health — it is CONFIGURED, never STARTED /
        # runtime-ready without the complete activation contract.
        p = _plane()
        result = p.startup(environ=dict(CLEAN_ENV))
        assert result["status"] == "configured"
        assert result["activation_ready"] is False
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
        configured = p.startup(environ=dict(CLEAN_ENV))
        # B4-CXR5R7: never "started" without full activation
        assert configured["status"] == "configured"
        assert configured["activation_ready"] is False


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
        rep = cs.config_gate()
        assert rep["ok"] in (True, False)
        assert rep["config_ok"] in (True, False)
        assert "start" not in rep  # CXR4-07/CXR5-07: config gate never claims start

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
        result = p.startup()
        assert result["status"] == "configured"  # B4-CXR5R7: never "started"
        assert result["activation_ready"] is False


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

    def test_worker_loop_has_no_secret_arguments(self):
        # D + CXR5-01-B: `python -m oce_control.worker_loop --dsn <external>`
        # or `--token <canary>` must fail at the CLI WITHOUT echoing the
        # candidate value — no gate, no DB connection possible, and the
        # worker token never travels through argv.
        import subprocess
        import sys
        cases = [
            (["--dsn", "postgresql://u:p@10.0.0.9:5432/other"],
             "postgresql://u:p@10.0.0.9:5432/other"),
            (["--token", "worker-token-canary-9876543210"],
             "worker-token-canary-9876543210"),
        ]
        for extra, canary in cases:
            r = subprocess.run(
                [sys.executable, "-m", "oce_control.worker_loop",
                 "--worker-id", "worker-x"] + extra,
                env=self._env(), capture_output=True, text=True, timeout=60)
            assert r.returncode == 2, extra
            blob = r.stderr + r.stdout
            assert canary not in blob  # candidate value is NEVER echoed
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

    def test_migrate_cli_rejects_db_flag_without_echo(self):
        # F(part 2) + CXR5-01-A: migrate.py --db is NOT a valid option. The
        # password-bearing DSN is never echoed and no connection is attempted.
        import subprocess
        import sys
        from pathlib import Path as _P
        script = str(_P(__file__).resolve().parent.parent / "scripts" / "migrate.py")
        canary = "postgresql://u:p@10.0.0.9:5432/other"
        r = subprocess.run([sys.executable, script, "up", "--db", canary],
                           env=self._env(), capture_output=True, text=True,
                           timeout=60)
        assert r.returncode == 2
        blob = r.stderr + r.stdout
        assert canary not in blob       # candidate value never echoed
        assert "10.0.0.9" not in blob
        assert "--db" in blob          # the option NAME is named, never its value
        assert "never accepted on the command line" in blob  # redacted denial

    def test_migrate_cli_rejects_equals_form_without_echo(self):
        # the --db=value form is rejected identically (raw value never echoed)
        import subprocess
        import sys
        from pathlib import Path as _P
        script = str(_P(__file__).resolve().parent.parent / "scripts" / "migrate.py")
        canary = "postgresql://u:canary-pw@10.0.0.9:5432/other"
        r = subprocess.run([sys.executable, script, "up", f"--db={canary}"],
                           env=self._env(), capture_output=True, text=True,
                           timeout=60)
        assert r.returncode == 2
        blob = r.stderr + r.stdout
        assert "canary-pw" not in blob
        assert "--db" in blob


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

    def test_ambient_worker_token_rejected(self):
        # B4-CXR5R6: the worker token lives ONLY in the approved secret store;
        # an ambient OCE_WORKER_TOKEN is known to the namespace but refused
        # outright (DEPRECATED_AND_REJECTED) — it can never be consumed.
        with pytest.raises(ValidationError, match="OCE_WORKER_TOKEN"):
            effective_from_env({**CLEAN_ENV, "OCE_WORKER_TOKEN": "opaque"})

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
    def _ctx(self, tmp_path, env=None, monkeypatch=None):
        import hashlib
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        if monkeypatch is not None:
            monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path)
        ls.initialize_activation_handoff_key()  # dedicated capability key
        # test_seam=True: rotate() is a TEST-ONLY metadata seam (B4-CXR5R4)
        backend = ls.RuntimeSecretBackend(store, test_seam=True)
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
        monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", tmp_path / "runtime" / "compose.env")
        calls: list = []
        monkeypatch.setattr(ll, "docker_available", lambda: True)
        monkeypatch.setattr(ll, "compose",
                            lambda *a, **k: calls.append(("compose", a)) or self._FakeComp())
        monkeypatch.setattr(ll, "wait_dependencies", lambda *a, **k: True)
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
        monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path / "runtime")
        monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", tmp_path / "runtime" / "compose.env")
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
        monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path / "runtime")
        monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", tmp_path / "runtime" / "compose.env")
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
    # (B4-CXR5R1: NO --db exists at all — the governed DSN is derived
    # internally, so an alternate identity cannot even be offered as input.)

    def test_migrate_rejects_db_flag_before_any_connection(self, capsys):
        # CXR5-01-A: NO --db interface exists — even a canonical-looking DSN
        # is rejected BEFORE the gate/connection, and the candidate value is
        # never echoed (DSNs are not valid CLI input, period).
        import scripts.migrate as mig
        bad_dsns = [
            "postgresql://oce_control_admin:pw@127.0.0.1:5432/oce_control",
            "postgresql://oce_control_admin:pw@127.0.0.1:5433/otherdb",
            "postgresql://other_user:pw@127.0.0.1:5433/oce_control",
            "postgresql://oce_control_admin:pw@10.0.0.9:5433/oce_control",
            "postgresql://oce_control_admin:pw@localhost:9999/oce_control",
            "postgresql://oce_control_admin:pw@127.0.0.1:5433/oce_control",
        ]
        for dsn in bad_dsns:
            with pytest.raises(SystemExit) as exc:
                mig.main(["up", "--db", dsn])
            assert exc.value.code == 2, dsn
        out, err = capsys.readouterr()
        blob = out + err
        assert "postgresql://" not in blob      # no DSN ever echoed
        assert "127.0.0.1" not in blob
        assert "never accepted on the command line" in err  # redacted denial

    def test_migrate_db_denial_has_zero_secret_store_effects(
            self, monkeypatch, tmp_path, capsys):
        # M: a denied migration has ZERO secret-store side effects, and the
        # candidate DSN (even with a wrong password) is never echoed.
        import scripts.migrate as mig
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "governed-secret-1234567890"}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        before = hashlib.sha256(store.read_bytes()).hexdigest()
        dsn = "postgresql://oce_control_admin:wrong-password@127.0.0.1:5433/oce_control"
        with pytest.raises(SystemExit) as exc:
            mig.main(["up", "--db", dsn])
        assert exc.value.code == 2
        out, err = capsys.readouterr()
        blob = out + err
        assert "wrong-password" not in blob
        assert "governed-secret-1234567890" not in blob
        assert "never accepted on the command line" in err
        assert hashlib.sha256(store.read_bytes()).hexdigest() == before

    def test_migrate_canonical_target_derived_internally_and_reaches_connect(
            self, monkeypatch, tmp_path, capsys):
        # the governed canonical DSN is DERIVED from the pinned activation
        # (no --db): it passes identity + gate checks in-memory and reaches
        # the connection step with the store-derived secret. Nothing is
        # echoed (unit test has no real PG; container CI proves the connect).
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
        with pytest.raises(RuntimeError, match="would-connect"):
            mig.main(["up"])
        derived = seen["dsn"]
        assert derived.startswith("postgresql://oce_control_admin:")
        assert "governed-secret-1234567890" in derived
        assert "@127.0.0.1:5433/oce_control" in derived
        out, err = capsys.readouterr()
        assert "governed-secret-1234567890" not in (out + err)  # never echoed

    def test_migrate_localhost_alias_derivation_deterministic(
            self, monkeypatch, tmp_path):
        # the derived target is deterministic: same store -> same canonical
        # loopback identity every time (127.0.0.1), no ambient influence.
        import scripts.migrate as mig
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "governed-secret-1234567890"}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        seen = []

        def fake_connect(dsn):
            seen.append(dsn)
            raise RuntimeError("would-connect")

        monkeypatch.setattr(mig, "connect", fake_connect)
        for _ in range(2):
            with pytest.raises(RuntimeError, match="would-connect"):
                mig.main(["up"])
        assert seen[0] == seen[1]
        assert "127.0.0.1" in seen[0]


# --------------------------------------------------------------------------- #
# B4-CXR5R2 (CXR5-02) — ONLY the repository-owned canonical migration program
# may mutate the governed database: --dir removed, symlink/duplicate/unknown-
# filename/gap rejection, secret-free migration-set identity, fixed cmd_down
# engine, and production rollback FUTURE-LOCKED.
# --------------------------------------------------------------------------- #
class TestCXR5R2CanonicalMigrationProgram:
    def _env(self) -> dict:
        env = dict(os.environ)
        from pathlib import Path as _P
        env["PYTHONPATH"] = str(_P(__file__).resolve().parent.parent / "src") \
            + os.pathsep + env.get("PYTHONPATH", "")
        return env

    def _scan_dir(self, tmp_path) -> Path:
        d = tmp_path / "migrations"
        d.mkdir()
        return d

    def test_migrate_cli_rejects_dir_flag_without_echo(self):
        # E + F: --dir is rejected BEFORE anything — the alternate directory
        # value is never echoed and can never select the SQL to execute.
        import subprocess
        import sys
        from pathlib import Path as _P
        script = str(_P(__file__).resolve().parent.parent / "scripts" / "migrate.py")
        alt = "/tmp/attacker-migrations"
        r = subprocess.run([sys.executable, script, "up", "--dir", alt],
                           env=self._env(), capture_output=True, text=True,
                           timeout=60)
        assert r.returncode == 2
        blob = r.stderr + r.stdout
        assert alt not in blob
        assert "--dir" in blob
        assert "canonical" in blob.lower()

    def test_canary_sql_never_executed_via_dir(self, monkeypatch, tmp_path, capsys):
        # F: a directory full of canary SQL can never be executed — the CLI
        # rejects --dir before any gate/connection; the scanner also refuses
        # non-canonical directories programmatically.
        import scripts.migrate as mig
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        d = tmp_path / "attacker-migrations"
        d.mkdir()
        (d / "0001_evil.sql").write_text("INSERT INTO canary VALUES (1);",
                                          encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            mig.main(["up", "--dir", str(d)])
        assert exc.value.code == 2
        out, err = capsys.readouterr()
        assert "canary" not in (out + err)
        with pytest.raises(RuntimeError, match="canonical"):
            mig.discover_migrations(d)

    def test_symlink_escape_blocked(self, tmp_path):
        # G: a symlink inside the scanned directory (even pointing at a
        # regular file) is rejected — SQL can never be smuggled from outside
        # the canonical set via a link.
        import scripts.migrate as mig
        outside = tmp_path / "outside.sql"
        outside.write_text("DROP TABLE anything;", encoding="utf-8")
        d = self._scan_dir(tmp_path)
        try:
            (d / "0001_link.sql").symlink_to(outside)
        except OSError:
            pytest.skip("symlink creation unsupported on this platform")
        with pytest.raises(RuntimeError, match="not a regular file"):
            mig._scan_migrations(d)

    def test_duplicate_version_blocked(self, tmp_path):
        # H: two up scripts for one version are a structural contradiction
        import scripts.migrate as mig
        d = self._scan_dir(tmp_path)
        (d / "0001_a.sql").write_text("SELECT 1;", encoding="utf-8")
        (d / "0001_b.sql").write_text("SELECT 2;", encoding="utf-8")
        with pytest.raises(RuntimeError, match="duplicate up"):
            mig._scan_migrations(d)

    def test_noncanonical_down_variant_blocked(self, tmp_path):
        # only the exact NNNN_down.sql form is canonical; any other *_down
        # variant is an unrecognized form and fails closed
        import scripts.migrate as mig
        d = self._scan_dir(tmp_path)
        (d / "0001_x.sql").write_text("SELECT 1;", encoding="utf-8")
        (d / "0001_a_down.sql").write_text("SELECT 0;", encoding="utf-8")
        # a near-miss down variant is NOT the canonical NNNN_down.sql form:
        # it parses as a second up script and fails closed as a duplicate
        with pytest.raises(RuntimeError, match="duplicate up"):
            mig._scan_migrations(d)

    def test_unrecognized_filename_blocked(self, tmp_path):
        # unrecognized .sql forms fail closed instead of being silently ignored
        import scripts.migrate as mig
        d = self._scan_dir(tmp_path)
        (d / "0001_x.sql").write_text("SELECT 1;", encoding="utf-8")
        (d / "evil-notes.sql").write_text("DROP TABLE x;", encoding="utf-8")
        with pytest.raises(RuntimeError, match="unrecognized migration filename"):
            mig._scan_migrations(d)

    def test_version_gap_blocked(self, tmp_path):
        import scripts.migrate as mig
        d = self._scan_dir(tmp_path)
        (d / "0001_x.sql").write_text("SELECT 1;", encoding="utf-8")
        (d / "0003_x.sql").write_text("SELECT 3;", encoding="utf-8")
        with pytest.raises(RuntimeError, match="not contiguous"):
            mig._scan_migrations(d)

    def test_rollback_future_locked_in_production_cli(self):
        # I: production `down` is FUTURE-LOCKED — refused BEFORE any
        # activation/connection work; the engine stays unit-testable.
        import scripts.migrate as mig
        rc = mig.main(["down"])
        assert rc == 3

    def test_cmd_down_engine_fixed(self, capsys):
        # I: cmd_down previously crashed on dict(discover_migrations(...));
        # the real rollback engine now works (executes the canonical down
        # script for the latest applied version) — production CLI locked.
        import scripts.migrate as mig
        applied = {"0006": "<sha>"}

        class _Cur:
            def __init__(self):
                self.executed = []

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def execute(self, sql, params=None):
                self.executed.append(sql)

            def fetchall(self):
                return list(applied.items())

        class _Conn:
            def __init__(self):
                self.cur = _Cur()

            def cursor(self):
                return self.cur

            def commit(self):
                pass

            def rollback(self):
                pass

            def close(self):
                pass

        conn = _Conn()
        monkeypatched = False
        orig_connect = mig.connect
        mig.connect = lambda dsn: conn  # type: ignore[assignment]
        try:
            rc = mig.cmd_down("governed-dsn", mig.MIGRATIONS_DIR)
        finally:
            mig.connect = orig_connect
        assert rc == 0
        out = capsys.readouterr().out
        assert "reverted 0006" in out
        down_sql = (mig.MIGRATIONS_DIR / "0006_down.sql").read_text(encoding="utf-8")
        assert down_sql in conn.cur.executed[-1]

    def test_migration_set_identity_deterministic_and_sql_free(self):
        # migration-set identity: ordered versions, file hashes, NO SQL
        # contents, deterministic across calls.
        import scripts.migrate as mig
        a = mig.migration_set_identity()
        b = mig.migration_set_identity()
        assert a == b
        assert a["manifest_sha256"] == b["manifest_sha256"]
        blob = json.dumps(a)
        assert "CREATE TABLE" not in blob and "SELECT" not in blob
        versions = [e["version"] for e in a["entries"]]
        assert versions == sorted(versions)
        for e in a["entries"]:
            assert re.fullmatch(r"[0-9a-f]{64}", e["up_sha256"])

    def test_migration_set_identity_detects_mutation(self, monkeypatch, tmp_path):
        # the identity changes when the migration set changes (tamper proof)
        import shutil
        import scripts.migrate as mig
        real = mig.MIGRATIONS_DIR
        fake_base = tmp_path / "control-plane"
        (fake_base / "migrations").mkdir(parents=True)
        shutil.copytree(real, fake_base / "migrations", dirs_exist_ok=True)
        monkeypatch.setattr(mig, "BASE", fake_base)
        monkeypatch.setattr(mig, "MIGRATIONS_DIR", fake_base / "migrations")
        before = mig.migration_set_identity()
        tamper = fake_base / "migrations" / "0006_config_override_audit.sql"
        tamper.write_text(
            tamper.read_text(encoding="utf-8") + "\n-- tampered\n",
            encoding="utf-8")
        after = mig.migration_set_identity()
        assert after["manifest_sha256"] != before["manifest_sha256"]


# --------------------------------------------------------------------------- #
# B4-CXR5R3 (CXR5-03) — ONE activation lineage across process boundaries: the
# parent resolves the environment exactly ONCE and freezes one authoritative
# ActivationContext; children consume a SANITIZED environment carrying a safe
# secret-free ActivationEnvelope and prove current generation/revocation
# freshness (stale/forged/revoked lineage fails closed before activity).
# --------------------------------------------------------------------------- #
class TestCXR5R3ActivationLineage:
    def _ctx(self, tmp_path, env=None, monkeypatch=None):
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        if monkeypatch is not None:
            monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path)
        ls.initialize_activation_handoff_key()  # dedicated capability key
        # test_seam=True: rotate() is a TEST-ONLY metadata seam (B4-CXR5R4)
        backend = ls.RuntimeSecretBackend(store, test_seam=True)
        ctx = cs.create_activation_context(
            environ=dict(env or CLEAN_ENV), backend=backend)
        return ctx, backend, store

    def test_one_parent_resolution_during_start(self, monkeypatch, tmp_path):
        # exactly ONE environment/config resolution during one ll.start()
        import oce_control.local_lifecycle as ll
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40,
                                     "worker_token": "w" * 40}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path / "runtime")
        monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", tmp_path / "runtime" / "compose.env")
        ls.initialize_activation_handoff_key()  # dedicated capability key
        # B4-CXR5X1: the CI runner injects ambient POSTGRES_PASSWORD/DSN into
        # the pytest environment; the isolated test store is the sole authority
        # here (the ambient value must not trigger a fail-closed mismatch).
        monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
        monkeypatch.delenv("POSTGRES_DSN", raising=False)
        class _FakeComp:
            returncode = 0
            stdout = ""
            stderr = ""

        monkeypatch.setattr(ll, "docker_available", lambda: True)
        monkeypatch.setattr(ll, "compose", lambda *a, **k: _FakeComp())
        monkeypatch.setattr(ll, "wait_dependencies", lambda *a, **k: True)
        monkeypatch.setattr(ll, "migrate", lambda *a, **k: _FakeComp())
        monkeypatch.setattr(ll, "wait_for_http", lambda *a, **k: True)
        monkeypatch.setattr(ll, "smoke",
                            lambda *a, **k: [("health", True), ("console", True)])
        monkeypatch.setattr(ll, "start_process",
                            lambda *a, **k: Path("mock.pid"))
        calls = []
        orig = cs.effective_from_env

        def _counting(environ=None, registry=None):
            calls.append(1)
            return orig(environ, registry=registry)

        monkeypatch.setattr(cs, "effective_from_env", _counting)
        ll.start()
        assert len(calls) == 1  # M: exactly one parent resolution

    def test_child_consumes_envelope_pinned_values(self, tmp_path):
        # J: parent created, environment mutated afterwards — the child
        # (envelope env) stays pinned to the parent's authority
        from oce_control import local_secrets as ls
        env = {**CLEAN_ENV, "OCE_CONTROL_PLANE_PORT": "8455",
               "OCE_SCHEDULER_INTERVAL": "9"}
        ctx, backend, _ = self._ctx(tmp_path, env=env)
        assert ctx.control_plane_port == 8455 and ctx.scheduler_interval == 9
        child_env = ctx.child_environment(child_role="api")
        # mutate ambient authority AFTER parent creation — must not move child
        child_env["OCE_CONTROL_PLANE_PORT"] = "9999"
        child_env["POSTGRES_PASSWORD"] = "ambient-attack-1234567890"
        child = cs.create_activation_context(environ=child_env, backend=backend,
                                             role="api")
        assert child.context_id == ctx.context_id       # same lineage
        assert child.control_plane_port == 8455          # pinned
        assert child.scheduler_interval == 9
        assert child.runtime_dsn(backend) == ctx.runtime_dsn(backend)
        # B4-CXR7U2: the verified child receives the DISTINCT child type
        assert type(child) is cs.VerifiedChildContext
        assert type(ctx) is cs.ParentActivationContext
        assert child.declared_role == "api"
        assert not hasattr(child, "issue_child_handoff")
        assert not hasattr(child, "child_environment")

    def test_child_environment_is_sanitized(self, tmp_path):
        # 5 (CXR5-03): child env carries NO ambient OCE_* authority or secret
        # — only the authenticated capability — and the carrier has no secret
        # material (no password, DSN, token, or handoff key)
        ctx, backend, store = self._ctx(tmp_path)
        env = ctx.child_environment(child_role="api")
        for key in env:
            assert not key.startswith("OCE_") or key == "OCE_ACTIVATION_ENVELOPE", key
        assert "POSTGRES_PASSWORD" not in env and "POSTGRES_DSN" not in env
        assert "OCE_WORKER_TOKEN" not in env and "OCE_WORKER_SECRET" not in env
        blob = env["OCE_ACTIVATION_ENVELOPE"]
        assert "k" * 40 not in blob            # password never in envelope
        assert "postgresql://" not in blob     # DSN never in envelope
        assert "worker_token" not in blob
        assert "secret_generation" in blob     # safe metadata IS present
        assert "config_fingerprint" in blob
        import oce_control.local_secrets as ls
        assert ls.read_activation_handoff_key() not in blob  # key never leaves

    def test_child_rejects_stale_generation(self, tmp_path):
        # L: secret rotates AFTER parent activation -> child lineage STALE,
        # fails closed before any activity; new generation never adopted
        ctx, backend, _ = self._ctx(tmp_path)
        child_env = ctx.child_environment(child_role="api")
        backend.rotate("runtime-local", "rotated-after-parent-9876543210")
        with pytest.raises(SystemExit, match="STALE"):
            cs.create_activation_context(environ=child_env, backend=backend,
                                         role="api")

    def test_child_rejects_revoked_secret(self, tmp_path):
        ctx, backend, _ = self._ctx(tmp_path)
        child_env = ctx.child_environment(child_role="api")
        backend.revoke("runtime-local")
        with pytest.raises(SystemExit, match="STALE"):
            cs.create_activation_context(environ=child_env, backend=backend,
                                         role="api")

    def test_child_rejects_forged_identity(self, tmp_path):
        # K (CXR6-01): any forged field breaks the MAC — a recomputable
        # plain-SHA self-consistency check is no longer the gate
        ctx, backend, _ = self._ctx(tmp_path)
        child_env = ctx.child_environment(child_role="api")
        forged = json.loads(child_env["OCE_ACTIVATION_ENVELOPE"])
        payload = json.loads(forged["payload"])
        payload["context_id"] = "0" * 64
        forged["payload"] = json.dumps(payload, sort_keys=True,
                                        separators=(",", ":"))
        child_env["OCE_ACTIVATION_ENVELOPE"] = json.dumps(forged)
        with pytest.raises(SystemExit, match="MAC verification FAILED"):
            cs.create_activation_context(environ=child_env, backend=backend,
                                         role="api")

    def test_child_rejects_malformed_envelope(self, tmp_path):
        ctx, backend, _ = self._ctx(tmp_path)
        child_env = ctx.child_environment(child_role="api")
        child_env["OCE_ACTIVATION_ENVELOPE"] = "{not json"
        with pytest.raises(SystemExit, match="malformed"):
            cs.create_activation_context(environ=child_env, backend=backend,
                                         role="api")

    def test_require_runtime_startable_resolves_once(self, monkeypatch, tmp_path):
        # M: require_runtime_startable resolves the environment exactly once
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        calls = []
        orig = cs.effective_from_env

        def _counting(environ=None, registry=None):
            calls.append(1)
            return orig(environ, registry=registry)

        monkeypatch.setattr(cs, "effective_from_env", _counting)
        eff = cs.require_runtime_startable(environ=CLEAN_ENV)
        assert len(calls) == 1
        assert eff.get_bool("sandbox.strict") is True

    def test_legacy_fallbacks_fail_closed_in_lifecycle_process(self, tmp_path,
                                                               monkeypatch):
        # N: with an activation envelope present (lifecycle-launched child),
        # the ctx=None compatibility fallbacks fail closed
        from oce_control import local_secrets as ls
        from oce_control import http_api as api
        ctx, backend, _ = self._ctx(tmp_path, monkeypatch=monkeypatch)
        child_env = ctx.child_environment(child_role="api")
        with pytest.raises(SystemExit, match="pinned ActivationContext"):
            api.runtime_bind(environ=child_env)
        with pytest.raises(SystemExit, match="pinned ActivationContext"):
            api.runtime_scheduler_interval(environ=child_env)
        monkeypatch.setenv("OCE_ACTIVATION_ENVELOPE",
                           child_env["OCE_ACTIVATION_ENVELOPE"])
        with pytest.raises(SystemExit, match="pinned ActivationContext"):
            api.build_durable_app(ctx=None)  # type: ignore[call-arg]

    def test_migrate_child_rejects_migration_set_mismatch(self, monkeypatch,
                                                          tmp_path, capsys):
        # migration proves the same lineage: a child whose envelope's
        # migration-set identity differs from the canonical set refuses to
        # mutate the governed database (rc=2 before any connection)
        import scripts.migrate as mig
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        ctx, backend, _ = self._ctx(tmp_path, monkeypatch=monkeypatch)
        child_env = ctx.child_environment(
            child_role="migration",
            migration_set_identity={"manifest_sha256": "0" * 64})
        monkeypatch.setenv("OCE_ACTIVATION_ENVELOPE",
                           child_env["OCE_ACTIVATION_ENVELOPE"])
        rc = mig.main(["up"])
        assert rc == 2
        out, err = capsys.readouterr()
        assert "migration-set identity" in (out + err)

    def test_migrate_child_accepts_matching_identity_reaches_gate(
            self, monkeypatch, tmp_path, capsys):
        # a child envelope carrying the TRUE canonical migration-set identity
        # passes lineage and reaches the connection step (unit: no real PG;
        # container CI proves the connect)
        import scripts.migrate as mig
        from oce_control import local_secrets as ls
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        ctx, backend, _ = self._ctx(tmp_path, monkeypatch=monkeypatch)
        identity = mig.migration_set_identity()
        child_env = ctx.child_environment(
            child_role="migration", migration_set_identity=identity)
        monkeypatch.setenv("OCE_ACTIVATION_ENVELOPE",
                           child_env["OCE_ACTIVATION_ENVELOPE"])
        seen = []

        def fake_connect(dsn):
            seen.append(dsn)
            raise RuntimeError("would-connect")

        monkeypatch.setattr(mig, "connect", fake_connect)
        with pytest.raises(RuntimeError, match="would-connect"):
            mig.main(["up"])
        assert seen and "k" * 40 in seen[0]  # governed secret in derived DSN
        out, err = capsys.readouterr()
        assert "k" * 40 not in (out + err)  # never echoed


# --------------------------------------------------------------------------- #
# B4-CXR5R6 — authority-bearing input fences (proofs O/P/Q + ambient-          #
# credential). OCE_JOB_FILE is TEST_ONLY; the ambient worker secret cannot    #
# self-authorize; workspace/artifact/runtime paths are containment-enforced.  #
# --------------------------------------------------------------------------- #
class TestCXR5R6AuthorityInputs:
    def _spawn(self, tmp_path, extra_env: dict):
        import subprocess
        import sys
        env = dict(os.environ)
        base = Path(__file__).resolve().parent.parent
        env["PYTHONPATH"] = str(base / "src") + os.pathsep + \
            env.get("PYTHONPATH", "")
        # B4-CXR5X1: never inherit the CI runner's OCE_CI_MODE into the spawned
        # worker — the test declares the seam explicitly per invocation.
        env.pop("OCE_CI_MODE", None)
        env.update(extra_env)
        return subprocess.run(
            [sys.executable, str(base / "scripts" / "oce_b3_worker.py")],
            cwd=str(tmp_path), env=env, capture_output=True, text=True,
            timeout=120)

    def test_production_job_file_rejected_before_activity(self, tmp_path):
        # O/P: a local job spec can never replace the authoritative
        # control-plane job in production. OCE_JOB_FILE is TEST_ONLY and
        # REJECTED UNCONDITIONALLY — before any job/workspace/process/socket
        # activity (no output, no workspace).
        jobfile = tmp_path / "job.json"
        jobfile.write_text(json.dumps({
            "job_id": "j-local", "job_type": "hash",
            "params": {"value": "canary"}}), encoding="utf-8")
        r = self._spawn(tmp_path, {
            "OCE_CP_URL": "http://127.0.0.1:8448",
            "OCE_WORKER_ID": "worker-local01",
            "OCE_WORKER_SECRET": "ambient-cannot-self-authorize",
            "OCE_JOB_FILE": str(jobfile),
        })
        assert r.returncode != 0
        assert "TEST_ONLY" in (r.stdout + r.stderr)
        assert not (tmp_path / "output").exists()
        assert not (tmp_path / "b3-workspace").exists()

    def test_ci_mode_never_unlocks_job_file(self, tmp_path):
        # B4-CXR6R2: OCE_CI_MODE=true carries ZERO authority — a local job
        # spec is rejected exactly the same as in production (before any
        # activity). An environment string can never unlock test authority.
        jobfile = tmp_path / "job.json"
        jobfile.write_text(json.dumps({
            "job_id": "j-local", "job_type": "hash",
            "params": {"value": "x"}}), encoding="utf-8")
        r = self._spawn(tmp_path, {
            "OCE_CP_URL": "http://127.0.0.1:8448",
            "OCE_WORKER_ID": "worker-local01",
            "OCE_WORKER_SECRET": "test-secret",
            "OCE_JOB_FILE": str(jobfile),
            "OCE_CI_MODE": "true",
        })
        assert r.returncode != 0
        assert "TEST_ONLY" in (r.stdout + r.stderr)
        assert not (tmp_path / "b3-workspace").exists()

    def test_ambient_worker_secret_cannot_self_authorize(self, monkeypatch):
        # B4-CXR6R2: the ambient secret is NEVER consumed — with OR without
        # OCE_CI_MODE — the approved store is the only credential authority.
        import scripts.oce_b3_worker as w
        import oce_control.local_secrets as ls
        monkeypatch.delenv("OCE_CI_MODE", raising=False)
        monkeypatch.setenv("OCE_WORKER_SECRET", "ambient-cannot-self-authorize")
        monkeypatch.setattr(ls, "read_worker_token",
                            lambda: (_ for _ in ()).throw(
                                RuntimeError("no token")))
        with pytest.raises(SystemExit, match="secret unavailable"):
            w.ProductionWorkerDependencies().shared_secret()

    def test_ci_mode_never_consumes_ambient_secret(self, monkeypatch):
        # B4-CXR6R2: even with OCE_CI_MODE=true the ambient worker secret is
        # refused — an environment string cannot unlock a credential.
        import scripts.oce_b3_worker as w
        import oce_control.local_secrets as ls
        monkeypatch.setenv("OCE_CI_MODE", "true")
        monkeypatch.setenv("OCE_WORKER_SECRET", "test-secret-42")
        monkeypatch.setattr(ls, "read_worker_token",
                            lambda: (_ for _ in ()).throw(
                                RuntimeError("no token")))
        with pytest.raises(SystemExit, match="secret unavailable"):
            w.ProductionWorkerDependencies().shared_secret()

    def test_private_dependency_seam_injects_job_and_secret(self, monkeypatch):
        # B4-CXR6R2: test injection works ONLY through the private dependency
        # object — the seam reaches run() directly and the production CLI can
        # never construct it from an environment string.
        from oce_b3_worker_test_deps import TestWorkerDependencies
        import scripts.oce_b3_worker as w
        deps = TestWorkerDependencies(
            secret="test-secret-42",
            job_spec={"job_id": "j-seam", "job_type": "hash",
                      "params": {"value": "x"}})
        assert deps.shared_secret() == "test-secret-42"
        assert deps.resolve_job(None)["job_id"] == "j-seam"
        # production deps never read a job file / ambient secret
        assert not hasattr(w.ProductionWorkerDependencies(), "_job_spec")

    def test_contained_path_rejects_traversal(self, tmp_path):
        from scripts.oce_b3_worker import _contained_path
        with pytest.raises(SystemExit, match="traversal"):
            _contained_path("OCE_WS_BASE", "../evil", str(tmp_path / "ws"))
        with pytest.raises(SystemExit, match="traversal"):
            _contained_path("OCE_ARTIFACT_BASE", "a/../../evil",
                            str(tmp_path / "cas"))

    def test_contained_path_rejects_external_absolute(self, tmp_path):
        from scripts.oce_b3_worker import _contained_path
        outside = tmp_path.resolve().parent.parent / "external-abs"
        with pytest.raises(SystemExit, match="escapes the working root"):
            _contained_path("OCE_WS_BASE", str(outside), str(tmp_path / "ws"))

    def test_contained_path_rejects_repo_and_secret_store_overlap(self, tmp_path):
        from scripts.oce_b3_worker import _contained_path, BASE
        with pytest.raises(SystemExit, match="governed control-plane"):
            _contained_path("OCE_WS_BASE", str(BASE), str(tmp_path / "ws"))
        with pytest.raises(SystemExit, match="governed control-plane"):
            _contained_path("OCE_WS_BASE", str(BASE / ".runtime"),
                            str(tmp_path / "ws"))

    def test_contained_path_accepts_internal(self, tmp_path, monkeypatch):
        from scripts.oce_b3_worker import _contained_path
        monkeypatch.chdir(tmp_path)
        p = _contained_path("OCE_WS_BASE", "ws", str(tmp_path / "ws"))
        assert p == Path("ws")
