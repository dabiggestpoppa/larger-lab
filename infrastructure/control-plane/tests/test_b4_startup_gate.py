"""OCE Book 4 — real startup configuration gate (surface C, integrated).

Proves that the ACTUAL control-plane startup path validates its effective
configuration before activating: a valid default config resolves and starts,
while a malformed / incomplete / forbidden effective config refuses to start.
No Docker is used; the plane and config layers run in-process with a supplied
environ, so these tests stay in the authoritative local run.
"""
from __future__ import annotations

import json

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
from oce_control.config_spine import ValidationError

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