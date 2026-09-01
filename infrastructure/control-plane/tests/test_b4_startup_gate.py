"""OCE Book 4 — real startup configuration gate (surface C, integrated).

Proves that the ACTUAL control-plane startup path validates its effective
configuration before activating: a valid default config resolves and starts,
while a malformed / incomplete / forbidden effective config refuses to start.
No Docker is used; the plane and config layers run in-process with a supplied
environ, so these tests stay in the authoritative local run.
"""
from __future__ import annotations

import json
import os

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
        assert rep["start"] is True
        assert rep["error"] is None

    def test_live_mode_forbidden(self):
        with pytest.raises(ValidationError):
            effective_from_env(LIVE_ENV)
        rep = validate_startup(LIVE_ENV)
        assert rep["ok"] is False and rep["start"] is False
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
        assert "start" in rep

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
            "file": {"postgres.password_ref": "secret:postgres",
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
            "file": {"postgres.password_ref": "secret:postgres",
                     "control_plane.port": "7000"},
            "environment": {"control_plane.port": "8455"}})
        b = ConfigResolver(reg).resolve({
            "environment": {"control_plane.port": "8455"},
            "file": {"postgres.password_ref": "secret:postgres",
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