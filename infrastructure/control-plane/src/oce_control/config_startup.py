"""OCE Book 4 — real startup configuration validation (surface C, integrated).

Unlike config_spine.py (pure resolution primitives), this module is the REAL
runtime hook: it loads the effective configuration from the operator's
environment (mapped to canonical settings), validates it fail-closed via
validate_effective, and refuses to activate when the effective config is
malformed, incomplete, or forbidden.

Provenance is honest: environment values are reported with source
``environment`` (never masqueraded as ``file``), and the resolver's
deterministic precedence (default < file < environment < cli) is preserved.

A governed OCE namespace policy applies: every ``OCE_*`` variable must be a
known canonical setting, an explicit compatibility alias, or a documented
operational (non-config) variable. Unknown / typoed security- or
runtime-significant ``OCE_*`` variables fail closed instead of being silently
ignored while still altering the real runtime.

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
    SOURCE_ENV,
    SOURCE_DEFAULT,
    ValidationError,
    build_default_registry,
    validate_effective,
)
from oce_control import local_secrets as ls

# Canonical env-var -> canonical setting name. Only settings that are safe to
# read from the environment are listed; every one of them is ALSO run through
# validate_effective, so an attempt to turn on a forbidden posture (public
# listen, live trading, cloud activation, ...) fails closed regardless of the
# source it came from.
ENV_MAP = {
    "control_plane.host": "OCE_CONTROL_PLANE_HOST",
    "control_plane.port": "OCE_CONTROL_PLANE_PORT",
    "control_plane.scheduler_interval": "OCE_SCHEDULER_INTERVAL",
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

# Explicit compatibility aliases: legacy env vars mapped into a canonical
# setting through a documented adapter with deterministic precedence. The
# canonical env var wins; the alias is only consulted when the canonical name
# is absent (never the reverse), and any alias value is still validated by the
# canonical setting's rules (e.g. OCE_API_PORT=8080 is rejected because the
# canonical registry treats 8080 as reserved).
COMPAT_ALIASES = {
    "OCE_API_PORT": "control_plane.port",
}

# Documented operational (non-config) OCE_* variables used by CI runners,
# workers, and evidence tooling. They are NOT spine settings; they are listed
# so the governed-namespace check can classify them instead of failing closed.
OPERATIONAL_OCE_VARS = frozenset({
    # CI / runner identity + evidence plumbing
    "OCE_RUN_ID", "OCE_STAGE_LABEL", "OCE_BLOCK_LABEL", "OCE_BOOK_LABEL",
    "OCE_EVIDENCE_DIR", "OCE_ARTIFACT_BASE", "OCE_CI_MODE",
    "OCE_EXPECTED_REPO", "OCE_EXPECTED_BRANCH", "OCE_EXPECTED_COMMIT",
    "OCE_EXPECTED_TREE",
    # worker CLI / outbound client plumbing
    "OCE_CP_URL", "OCE_WORKER_ID", "OCE_WORKER_TOKEN", "OCE_WORKER_SECRET",
    "OCE_JOB_FILE", "OCE_WS_BASE", "OCE_ATTEMPT_WS", "OCE_RUNTIME_DIR",
})

# Canonical reference name for the local runtime PostgreSQL secret. The
# reference is defaulted at the CONFIGURATION layer (source = default); a
# runtime START additionally requires the reference to RESOLVE to a real
# materialized secret in the approved local secret store (see B4-R3R3).
DEFAULT_PASSWORD_REF = "secret:runtime-local"


_KNOWN_OCE_VARS = None


def known_oce_vars() -> frozenset:
    global _KNOWN_OCE_VARS
    if _KNOWN_OCE_VARS is None:
        _KNOWN_OCE_VARS = frozenset(set(ENV_MAP.values()) | set(COMPAT_ALIASES)
                                    | set(OPERATIONAL_OCE_VARS))
    return _KNOWN_OCE_VARS


def check_governed_namespace(environ: dict) -> None:
    """Fail closed on unknown / typoed OCE_* runtime-significant variables.

    The governed namespace is the ``OCE_`` prefix. Every variable in the
    process environment that starts with ``OCE_`` must be a known canonical
    env var, a compatibility alias, or a documented operational variable.
    Anything else is rejected — it could otherwise silently alter the real
    runtime (e.g. ``OCE_EXECUTION_BROKER_ENABLD=true``).

    Unrelated variables that merely contain "OCE" as incidental text do not
    start with ``OCE_`` and are deliberately not rejected.
    """
    known = known_oce_vars()
    unknown = sorted(k for k in environ if k.startswith("OCE_") and k not in known)
    if unknown:
        raise ValidationError(
            "unknown OCE_* configuration-namespace variable(s) present and "
            f"refused: {', '.join(unknown)} — fail closed (governed namespace "
            "policy; see B4-CONFIG-INPUT-INVENTORY.md)")


def effective_from_env(environ: dict | None = None,
                       registry=None) -> EffectiveConfig:
    """Build the effective config from *environ* with honest provenance.

    * Env values are mapped into the ``environment`` source tier (never
      ``file``).
    * Compatibility aliases (e.g. ``OCE_API_PORT``) are applied only when the
      canonical env var is absent.
    * ``postgres.password_ref`` has no safe *value* default, but the canonical
      local runtime reference name is supplied at DEFAULT tier so configuration
      resolution stays deterministic. Runtime activation must additionally
      verify the reference resolves (B4-R3R3).
    * Raises ValidationError for unknown OCE_* vars and any unauthorized
      resulting posture. A caller-supplied canonical *registry* is honored so
      forbidden-source rules can be tested through the real startup path.
    """
    env = dict(environ if environ is not None else os.environ)
    check_governed_namespace(env)
    env_source: dict[str, str] = {}
    for setting_name, var in ENV_MAP.items():
        if var in env:
            env_source[setting_name] = env[var]
    for alias_var, setting_name in COMPAT_ALIASES.items():
        canonical_var = ENV_MAP.get(setting_name)
        if alias_var in env and canonical_var not in env:
            env_source[setting_name] = env[alias_var]
    default_source: dict[str, str] = {}
    if "postgres.password_ref" not in env_source:
        default_source["postgres.password_ref"] = DEFAULT_PASSWORD_REF
    resolver = ConfigResolver(registry if registry is not None
                              else build_default_registry())
    return resolver.resolve({
        SOURCE_ENV: env_source,
        SOURCE_DEFAULT: default_source,
    })


def governed_runtime_dsn(environ: dict | None = None,
                         backend: "ls.RuntimeSecretBackend | None" = None,
                         eff: EffectiveConfig | None = None) -> str:
    """Build the ephemeral PostgreSQL DSN from the governed secret boundary.

    path: effective config -> postgres.password_ref -> approved store ->
          in-memory DSN (never logged, evidenced, or fingerprinted).

    The host comes from the canonical postgres.host setting; user/db/port
    come from the documented local runtime constants. An ambient
    POSTGRES_DSN/POSTGRES_PASSWORD bypass is impossible here — the DSN is
    derived, not read.
    """
    if eff is None:
        eff = effective_from_env(environ)
    password = resolve_startup_secret(eff, backend)
    host = eff.get("postgres.host") or ls.PG_HOST
    # CXR3-04 defense in depth: the durable DB host may only be the local
    # loopback while the Book 4 local-first contract is in force.
    if host not in ("127.0.0.1", "localhost"):
        from oce_control.config_spine import ValidationError as _VE
        raise _VE(
            "postgres.host is not loopback — governed DSN derivation "
            "refuses non-local durable truth (B4-CXR3R3); value not echoed")
    return (f"postgresql://{ls.PG_USER}:{password}@{host}:"
            f"{ls.PG_PORT}/{ls.PG_DB}")


def secret_resolution_evidence(environ: dict | None = None,
                               backend: "ls.RuntimeSecretBackend | None" = None,
                               eff: EffectiveConfig | None = None) -> dict:
    """Safe, evidence-ready record of secret resolution.

    Records ONLY: reference identity, resolver/backend identity,
    generation/version, and resolution success/failure. NEVER the password,
    a password-bearing DSN, or any digest suitable for offline recovery.
    """
    if eff is None:
        eff = effective_from_env(environ)
    backend = backend or ls.RuntimeSecretBackend()
    ref = eff.get("postgres.password_ref")
    name = ref.split(":", 1)[1] if isinstance(ref, str) and ":" in ref else ref
    try:
        resolve_startup_secret(eff, backend)
        ok, error = True, None
    except (KeyError, PermissionError, ValidationError, ValueError) as exc:
        ok, error = False, redact_message(str(exc))
    return {
        "reference": ref,
        "backend": "local-runtime-store-v1",
        "generation": backend.generation(name) if isinstance(name, str) else None,
        "revoked": backend.is_revoked(name) if isinstance(name, str) else None,
        "resolved": ok,
        "error": error,
        # deliberately excludes: password value, DSN, secret digest
    }


def resolve_startup_secret(eff: EffectiveConfig,
                           backend: "ls.RuntimeSecretBackend | None" = None) -> str:
    """Resolve ``postgres.password_ref`` through the approved local store.

    Returns the materialized secret. Fails closed (raises KeyError /
    PermissionError / ValidationError) when the reference is malformed,
    missing from the store, or revoked. The value exists only in process
    memory — it is never logged, evidenced, or fingerprinted.
    """
    backend = backend or ls.RuntimeSecretBackend()
    ref = eff.get("postgres.password_ref")
    from oce_control.config_spine import SECRET_REF_RE
    if not isinstance(ref, str) or not SECRET_REF_RE.match(ref):
        raise ValidationError(
            "postgres.password_ref must be a secret:reference "
            "(never a plain password value)")
    return backend.resolve(ref)


def require_secret_resolvable(environ: dict | None = None,
                              backend: "ls.RuntimeSecretBackend | None" = None,
                              eff: EffectiveConfig | None = None) -> None:
    """Activation-time secret proof: the effective password reference must
    RESOLVE against the approved local secret store or startup is BLOCKED.

    A syntactically valid reference string is NOT sufficient (B4-R3R3): a
    runtime start never passes because the code invented an unbacked
    reference. Distinguish configuration/init (may materialize the secret
    via `configure`) from runtime/start (must resolve it).
    """
    try:
        target = eff if eff is not None else effective_from_env(environ)
        resolve_startup_secret(target, backend)
    except (KeyError, PermissionError) as exc:
        raise SystemExit(
            f"OCE startup BLOCKED: {redact_message(str(exc))} — run "
            "`python scripts/oce_local.py configure` to materialize the local "
            "runtime secret (or set OCE_POSTGRES_PASSWORD_REF to an existing "
            "reference)") from exc
    except ValidationError as exc:
        raise SystemExit(startup_report(environ)) from exc


def validate_startup(environ: dict | None = None,
                     backend: "ls.RuntimeSecretBackend | None" = None) -> dict:
    """Validate the startup effective config.

    Never raises. Returns a report dict:
        {"ok": bool, "start": bool, "config": <redacted>,
         "secret_ok": bool|None, "error": str|None}
    """
    try:
        eff = effective_from_env(environ)
        validate_effective(eff)  # redundant but explicit & self-documenting
        secret_ok: bool | None = None
        try:
            resolve_startup_secret(eff, backend)
            secret_ok = True
        except (KeyError, PermissionError):
            secret_ok = False
        return {
            "ok": True,
            "start": True,
            "config": eff.redacted(),
            "fingerprint": eff.fingerprint,
            "secret_ok": secret_ok,
            "error": None,
        }
    except (ValidationError, KeyError, ValueError) as exc:
        return {
            "ok": False,
            "start": False,
            "config": None,
            "secret_ok": False,
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

    Uses the canonical redact_string leakage primitive on top of single-line
    trimming — defense in depth, never trusting exception prose alone. If a
    raw candidate value ever slips into a message (e.g. a canary secret in a
    malformed field), the primitive scrubs ``key=value`` patterns for
    sensitive keys before anything reaches the operator.
    """
    from oce_control.config_spine import redact_string
    return redact_string(text.split("\n")[0].strip())


def _offending_setting(message: str) -> str | None:
    import re
    m = re.search(r"setting '([A-Za-z0-9_.]+)'", message)
    if m:
        return m.group(1)
    m = re.search(r"refused: ([A-Z0-9_, ]+)", message)
    if m:
        return m.group(1).strip()
    return None


def require_startable(environ: dict | None = None) -> EffectiveConfig:
    """Fail-closed startup hook: returns the validated effective config or
    raises a human-readable SystemExit (secret-free) that stops activation.

    NOTE: secret-reference resolution (B4-R3R3) is layered on top of this
    function by the runtime secret backend; the configuration gate itself
    runs here so no activation can bypass posture validation.
    """
    try:
        eff = effective_from_env(environ)
        validate_effective(eff)
    except ValidationError as exc:
        raise SystemExit(startup_report(environ)) from exc
    return eff


def outbound_cp_url(environ: dict | None = None) -> str:
    """Canonical outbound control-plane target for workers (B4-CXR3R3).

    The Book 4 activation gate ALWAYS runs first regardless of whether
    OCE_CP_URL is set — a worker can never skip validation by supplying the
    URL. OCE_CP_URL is NOT an arbitrary operational string: when present it
    is treated as a VERIFIED COMPATIBILITY ASSERTION that must equal the
    canonical loopback endpoint derived from the validated effective config
    (control_plane.host + control_plane.port). Anything else — external
    host (10.x / 192.168.x / public hostname), noncanonical port, embedded
    credentials, path/query — fails closed before any socket activity.
    """
    env = environ if environ is not None else os.environ
    eff = require_startable(env)  # gate first: forbidden config still blocks
    canonical = (f"http://{eff.get('control_plane.host')}:"
                 f"{eff.get('control_plane.port')}")
    url = env.get("OCE_CP_URL")
    if not url:
        return canonical
    if url.rstrip("/") != canonical:
        raise SystemExit(
            "OCE startup BLOCKED: OCE_CP_URL is not the canonical loopback "
            f"control-plane endpoint (expected {canonical}) — workers derive "
            "their target from the validated effective config (B4-CXR3R3)")
    return url


def gate_start(args_start: object | None = None) -> dict:
    """CLI hook for 'start'/'restart': gate on config before compose up."""
    return validate_startup()


if __name__ == "__main__":  # pragma: no cover - manual diagnostic
    print(startup_report())
    sys.exit(0 if validate_startup()["ok"] else 1)