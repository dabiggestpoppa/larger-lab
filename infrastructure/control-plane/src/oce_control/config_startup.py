"""OCE Book 4 — real startup configuration validation (surface C, integrated).

Unlike config_spine.py (pure resolution primitives), this module is the REAL
runtime hook: it loads the effective configuration from the operator's
environment (mapped to canonical settings), validates it fail-closed via
validate_effective, and refuses to activate when the effective config is
malformed, incomplete, or forbidden.

Entry points wired into startup / CLI:
  * load_effective_config(environ)  -> EffectiveConfig  (raises on violation)
  * validate_startup(environ)       -> dict report       (never raises)
  * startup_report(environ)         -> operator-legible dict

Errors are operator-legible and secret-free: a violation names the offending
setting and the rule, but never prints a secret value.
"""
from __future__ import annotations

import os
import sys

from oce_control.config_spine import (
    ConfigResolver,
    EffectiveConfig,
    ValidationError,
    build_default_registry,
    validate_effective,
)

# Env-var -> canonical setting name. Only settings that are safe to read from
# the environment are listed; every one of them is ALSO run through
# validate_effective, so an attempt to turn on a forbidden posture (public
# listen, live trading, cloud activation, ...) fails closed regardless of the
# source it came from.
ENV_MAP = {
    "control_plane.host": "OCE_CONTROL_PLANE_HOST",
    "control_plane.port": "OCE_CONTROL_PLANE_PORT",
    "control_plane.public_listen": "OCE_CONTROL_PLANE_PUBLIC_LISTEN",
    "postgres.host": "OCE_POSTGRES_HOST",
    "postgres.password_ref": "OCE_POSTGRES_PASSWORD_REF",
    "redis.mode": "OCE_REDIS_MODE",
    "workers.egress": "OCE_WORKERS_EGRESS",
    "sandbox.strict": "OCE_SANDBOX_STRICT",
    "sandbox.process_tree_termination": "OCE_SANDBOX_PROCESS_TREE_TERMINATION",
    "sessions.auth_required": "OCE_SESSIONS_AUTH_REQUIRED",
    "execution.broker_enabled": "OCE_EXECUTION_BROKER_ENABLED",
    "execution.paper_trading_enabled": "OCE_EXECUTION_PAPER_TRADING_ENABLED",
    "execution.live_order_mode": "OCE_EXECUTION_LIVE_ORDER_MODE",
    "capital.authority": "OCE_CAPITAL_AUTHORITY",
    "cloud.provisioning": "OCE_CLOUD_PROVISIONING",
    "cloud.gpu_burst": "OCE_CLOUD_GPU_BURST",
    "cloud.accounts": "OCE_CLOUD_ACCOUNTS",
    "cloud.cost_ceiling_usd_per_month": "OCE_CLOUD_COST_CEILING_USD",
    "logging.redact_secrets": "OCE_LOG_REDACT_SECRETS",
    "logging.redact_cli": "OCE_LOG_REDACT_CLI",
}


def effective_from_env(environ: dict | None = None) -> EffectiveConfig:
    """Build the effective config from *environ* and validate fail-closed.

    Any OCE_* variable mapped above becomes a candidate value. Values not
    present fall back to the canonical default (which is safe). Raises
    ValidationError when the resulting effective config is unauthorized.
    """
    env = dict(environ if environ is not None else os.environ)
    file_source: dict[str, str] = {}
    for setting_name, var in ENV_MAP.items():
        if var in env:
            file_source[setting_name] = env[var]
    # postgres.password_ref has no safe default and must be a reference.
    # If the operator did not provide one, default to the approved runtime
    # reference so a valid default config still resolves and starts.
    if "postgres.password_ref" not in file_source:
        file_source["postgres.password_ref"] = "secret:runtime-local"
    resolver = ConfigResolver(build_default_registry())
    return resolver.resolve({"file": file_source})


def validate_startup(environ: dict | None = None) -> dict:
    """Validate the startup effective config.

    Never raises. Returns a report dict:
        {"ok": bool, "start": bool, "config": <redacted>, "error": str|None}
    """
    try:
        eff = effective_from_env(environ)
        validate_effective(eff)  # redundant but explicit & self-documenting
        return {
            "ok": True,
            "start": True,
            "config": eff.redacted(),
            "fingerprint": eff.fingerprint,
            "error": None,
        }
    except (ValidationError, KeyError, ValueError) as exc:
        return {
            "ok": False,
            "start": False,
            "config": None,
            "error": redact_message(str(exc)),
        }


def startup_report(environ: dict | None = None, prefix: str = "OCE") -> str:
    """Operator-legible, secret-free startup gate message."""
    report = validate_startup(environ)
    if report["ok"]:
        return (f"{prefix} startup config validated: START ok "
                f"(fingerprint {report['fingerprint'][:12]}...)")
    # Point at the offending posture; names the setting, never the value.
    err = report["error"]
    hint = _offending_setting(err)
    if hint:
        return (f"{prefix} startup BLOCKED: {err} "
                f"[offending setting: {hint}]")
    return f"{prefix} startup BLOCKED: {err}"


def redact_message(text: str) -> str:
    """Pare a validation message down to a secret-free operator hint.

    Single-line and trimmed. Validation errors name the offending setting
    and the rule; they never embed secret values, so this is lossless.
    """
    return text.split("\n")[0].strip()


def _offending_setting(message: str) -> str | None:
    import re
    m = re.search(r"[A-Za-z][A-Za-z0-9_.]*", message)
    return m.group(0) if m else None


def require_startable(environ: dict | None = None) -> EffectiveConfig:
    """Fail-closed startup hook: returns the validated effective config or
    raises a human-readable SystemExit (secret-free) that stops activation.
    """
    try:
        eff = effective_from_env(environ)
        validate_effective(eff)
    except ValidationError as exc:
        raise SystemExit(startup_report(environ)) from exc
    return eff


def gate_start(args_start: object | None = None) -> dict:
    """CLI hook for 'start'/'restart': gate on config before compose up."""
    return validate_startup()


if __name__ == "__main__":  # pragma: no cover - manual diagnostic
    print(startup_report())
    sys.exit(0 if validate_startup()["ok"] else 1)