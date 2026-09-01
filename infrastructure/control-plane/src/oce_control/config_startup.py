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
  * create_activation_context()     -> frozen ActivationContext (B4-CXR4R3)

Errors are operator-legible and secret-free: a violation names the offending
setting and the rule, but never prints a secret value.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass

from oce_control.config_spine import (
    CANONICAL_PASSWORD_REF,
    ConfigResolver,
    EffectiveConfig,
    SOURCE_ENV,
    SOURCE_DEFAULT,
    ValidationError,
    build_default_registry,
    security_state_fingerprint,
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
    # B4-CXR5R3: safe activation-lineage carrier for child processes (JSON
    # envelope of SAFE metadata only — no passwords, tokens, or DSNs)
    "OCE_ACTIVATION_ENVELOPE",
})

# Canonical reference name for the local runtime PostgreSQL secret. The
# reference is defaulted at the CONFIGURATION layer (source = default); a
# runtime START additionally requires the reference to RESOLVE to a real
# materialized secret in the approved local secret store (see B4-R3R3).
# B4-CXR4R2: this is the ONE legal reference — the spine locks any alternate
# reference out at config validation (future-locked).
DEFAULT_PASSWORD_REF = CANONICAL_PASSWORD_REF


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
                         eff: EffectiveConfig | None = None,
                         ctx: "ActivationContext | None" = None) -> str:
    """Build the ephemeral PostgreSQL DSN from the governed secret boundary.

    path: effective config -> postgres.password_ref -> approved store ->
          in-memory DSN (never logged, evidenced, or fingerprinted).

    When a pinned ActivationContext (B4-CXR4R3) is supplied, the DSN comes
    from the PINNED postgres parameters + reference, and the context is
    checked for staleness (a rotated/revoked secret mid-activation fails
    closed). Otherwise the DSN is derived from the effective config. An
    ambient POSTGRES_DSN/POSTGRES_PASSWORD bypass is impossible — the DSN is
    derived, never read.
    """
    if ctx is not None:
        return ctx.runtime_dsn(backend)
    # B4-CXR5R3: a durable consumer that reaches the fallback WITHOUT a pinned
    # context inside a lifecycle-launched process (envelope present) fails
    # closed — the envelope is the only activation authority for children.
    if _envelope_present(environ) and eff is None:
        raise SystemExit(
            "production activation requires a pinned ActivationContext — "
            "governed_runtime_dsn() without ctx is a test-only compatibility "
            "path and is unreachable in a lifecycle-launched process "
            "(B4-CXR5R3)")
    if eff is None:
        ctx = create_activation_context(environ)  # resolve ONCE, pin
        return ctx.runtime_dsn(backend)
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


def validate_configuration(environ: dict | None = None) -> dict:
    """CONFIGURATION gate — schema/posture only (B4-CXR3R7/CXR4R6).

    Never raises. Returns a report dict:
        {"ok": bool, "config_ok": bool, "config": <redacted>,
         "fingerprint": str, "error": str|None}

    This is the start contract for a component that does not itself hold the
    durable secret (e.g. the in-memory ControlPlane). It deliberately does
    NOT resolve the secret: a configuration may be valid while its required
    runtime dependency (the secret store) is not yet resolvable.

    B4-CXR4R6 (CXR4-07): a CONFIGURATION-VALID result is NEVER
    misrepresented as RUNTIME-READY — this report contains NO
    start/ready/startable keys. "configuration valid" and "runtime
    ready/startable" are distinct truths; the latter requires
    validate_runtime_readiness() / require_runtime_startable().
    """
    try:
        eff = effective_from_env(environ)
        validate_effective(eff)  # redundant but explicit & self-documenting
        return {
            "ok": True,
            "config_ok": True,
            "config": eff.redacted(),
            "fingerprint": eff.fingerprint,
            "error": None,
        }
    except (ValidationError, KeyError, ValueError) as exc:
        return {
            "ok": False,
            "config_ok": False,
            "config": None,
            "error": redact_message(str(exc)),
        }


def validate_startup(environ: dict | None = None) -> dict:
    """Compatibility alias of validate_configuration (B4-CXR4R6).

    Returns the IDENTICAL config-only report — config_ok, and NO
    start/ready/startable keys. A configuration-valid result is never
    misrepresented as runtime-ready.
    """
    return validate_configuration(environ)


def validate_runtime_readiness(
        environ: dict | None = None,
        backend: "ls.RuntimeSecretBackend | None" = None) -> dict:
    """COMPLETE runtime-start contract: configuration + secret resolution.

    Never raises. Returns:
        {"ok": bool, "ready": bool, "secret_ok": bool,
         "config": <redacted>, "fingerprint": str, "error": str|None}

    ``ready`` is True ONLY when the configuration is valid AND the
    configured secret reference resolves against the approved store. No
    contradictory state is possible: ``ready`` implies ``secret_ok`` implies
    ``ok`` (invariant asserted by tests, B4-CXR3R7).
    """
    try:
        eff = effective_from_env(environ)
        validate_effective(eff)
        try:
            resolve_startup_secret(eff, backend)
            secret_ok = True
        except (KeyError, PermissionError, ValidationError, ValueError):
            secret_ok = False
        return {
            "ok": True,
            "ready": secret_ok,
            "secret_ok": secret_ok,
            "config": eff.redacted(),
            "fingerprint": eff.fingerprint,
            "error": (None if secret_ok else
                       "configured secret reference does not resolve — run "
                       "`python scripts/oce_local.py configure` to materialize "
                       "the local runtime secret (fail closed)"),
        }
    except (ValidationError, KeyError, ValueError) as exc:
        return {
            "ok": False,
            "ready": False,
            "secret_ok": False,
            "config": None,
            "error": redact_message(str(exc)),
        }


def require_runtime_startable(
        environ: dict | None = None,
        backend: "ls.RuntimeSecretBackend | None" = None) -> EffectiveConfig:
    """Fail-closed runtime-start gate: configuration + secret resolution.

    Raises SystemExit on ANY readiness failure (malformed / incomplete /
    forbidden config, or a configured reference that does not resolve).
    Returns the validated effective config on success. Every durable
    DB-facing activation entrypoint must use this — nothing may report
    "started"/"ready" unless the full runtime-start contract holds.

    B4-CXR4R3: activation entrypoints that need a PINNED authority should
    use create_activation_context() instead — the context freezes the
    effective config and the resolved secret metadata so later environment
    mutation cannot alter the activation.
    """
    # B4-CXR5R3: resolve the environment EXACTLY ONCE — the returned
    # effective config is the one that passed both gates (no second
    # resolution that could observe a different environment).
    try:
        eff = effective_from_env(environ)
        validate_effective(eff)
        resolve_startup_secret(eff, backend)
    except ValidationError as exc:
        raise SystemExit(startup_report(environ)) from exc
    except PermissionError as exc:
        raise SystemExit(
            f"OCE startup BLOCKED: {redact_message(str(exc))} — run "
            "`python scripts/oce_local.py configure` to materialize the local "
            "runtime secret (or set OCE_POSTGRES_PASSWORD_REF to an existing "
            "reference)") from exc
    except KeyError as exc:
        raise SystemExit(
            f"OCE startup BLOCKED: {redact_message(str(exc))} — run "
            "`python scripts/oce_local.py configure` to materialize the local "
            "runtime secret (or set OCE_POSTGRES_PASSWORD_REF to an existing "
            "reference)") from exc
    return eff


# --------------------------------------------------------------------------- #
# B4-CXR4R3 — ONE IMMUTABLE ACTIVATION CONTEXT
# --------------------------------------------------------------------------- #
# The invariant: NO INPUT MAY MODIFY THE AUTHORITY THAT VALIDATES THAT INPUT,
# and the exact configuration that passes the activation gate is the exact
# configuration every component uses. create_activation_context() snapshots
# the environment ONCE, resolves and validates the effective config ONCE,
# resolves the required secret metadata ONCE, and freezes an immutable
# ActivationContext. Every runtime consumer (HTTP bind, scheduler, durable DB
# connection, worker, migrations, outbound worker URL, lifecycle) consumes the
# SAME pinned object instead of re-reading os.environ. If the secret is
# rotated/revoked after context creation, the context is STALE and every
# consumer fails closed — a rotated authority is never silently adopted.


@dataclass(frozen=True)
class ActivationEnvelope:
    """SAFE, secret-free activation-lineage proof for child processes
    (B4-CXR5R3).

    Contains ONLY safe metadata: context identity, fingerprints, secret
    reference identity, backend identity, generation, revocation state,
    pinned bind parameters, and the migration-set identity. NEVER contains
    a password, a worker token, or a password-bearing DSN. Child processes
    consume the envelope to prove the SAME pinned activation lineage; a
    stale generation/revocation state or a forged identity fails closed
    before any socket/database/workspace/process activity.
    """
    schema_version: int
    context_id: str
    config_fingerprint: str
    security_state_fingerprint: str
    secret_reference: str
    secret_backend_identity: str
    secret_generation: int
    secret_revocation_state: bool
    control_plane_host: str
    control_plane_port: int
    scheduler_interval: int
    postgres_host: str
    postgres_port: int
    postgres_database: str
    postgres_user: str
    canonical_control_plane_url: str
    migration_set_identity: dict
    parent_activation_id: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "context_id": self.context_id,
            "config_fingerprint": self.config_fingerprint,
            "security_state_fingerprint": self.security_state_fingerprint,
            "secret_reference": self.secret_reference,
            "secret_backend_identity": self.secret_backend_identity,
            "secret_generation": self.secret_generation,
            "secret_revocation_state": self.secret_revocation_state,
            "control_plane_host": self.control_plane_host,
            "control_plane_port": self.control_plane_port,
            "scheduler_interval": self.scheduler_interval,
            "postgres_host": self.postgres_host,
            "postgres_port": self.postgres_port,
            "postgres_database": self.postgres_database,
            "postgres_user": self.postgres_user,
            "canonical_control_plane_url": self.canonical_control_plane_url,
            "migration_set_identity": self.migration_set_identity,
            "parent_activation_id": self.parent_activation_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActivationEnvelope":
        if not isinstance(data, dict):
            raise ValueError("envelope must be a JSON object")
        required = ("schema_version", "context_id", "config_fingerprint",
                    "security_state_fingerprint", "secret_reference",
                    "secret_backend_identity", "secret_generation",
                    "secret_revocation_state", "control_plane_host",
                    "control_plane_port", "scheduler_interval",
                    "postgres_host", "postgres_port", "postgres_database",
                    "postgres_user", "canonical_control_plane_url",
                    "migration_set_identity")
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"envelope missing fields: {', '.join(missing)}")
        if not isinstance(data["schema_version"], int):
            raise ValueError("envelope schema_version must be an int")
        if not isinstance(data["context_id"], str) or not re.fullmatch(
                r"[0-9a-f]{64}", data["context_id"]):
            raise ValueError("envelope context_id must be a 64-hex string")
        if not isinstance(data["secret_generation"], int):
            raise ValueError("envelope secret_generation must be an int")
        if not isinstance(data["secret_revocation_state"], bool):
            raise ValueError("envelope secret_revocation_state must be a bool")
        if not isinstance(data["control_plane_port"], int):
            raise ValueError("envelope control_plane_port must be an int")
        if not isinstance(data["scheduler_interval"], int):
            raise ValueError("envelope scheduler_interval must be an int")
        if not isinstance(data["postgres_port"], int):
            raise ValueError("envelope postgres_port must be an int")
        if not isinstance(data["migration_set_identity"], dict):
            raise ValueError("envelope migration_set_identity must be a dict")
        return cls(
            schema_version=data["schema_version"],
            context_id=data["context_id"],
            config_fingerprint=data["config_fingerprint"],
            security_state_fingerprint=data["security_state_fingerprint"],
            secret_reference=data["secret_reference"],
            secret_backend_identity=data["secret_backend_identity"],
            secret_generation=data["secret_generation"],
            secret_revocation_state=data["secret_revocation_state"],
            control_plane_host=data["control_plane_host"],
            control_plane_port=data["control_plane_port"],
            scheduler_interval=data["scheduler_interval"],
            postgres_host=data["postgres_host"],
            postgres_port=data["postgres_port"],
            postgres_database=data["postgres_database"],
            postgres_user=data["postgres_user"],
            canonical_control_plane_url=data["canonical_control_plane_url"],
            migration_set_identity=data["migration_set_identity"],
            parent_activation_id=str(data.get("parent_activation_id", "")),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, raw: str) -> "ActivationEnvelope":
        try:
            return cls.from_dict(json.loads(raw))
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed activation envelope JSON: {exc}")


@dataclass(frozen=True)
class ActivationContext:
    """Immutable, pinned activation authority (B4-CXR4R3).

    Carries the validated effective config, the resolved secret METADATA
    (reference identity, backend identity, generation, revocation state —
    NEVER the password value or a password-bearing DSN), the pinned bind
    parameters, and a deterministic context identity. Frozen: once created,
    os.environ changes cannot alter the activation.
    """
    effective_config: EffectiveConfig
    config_fingerprint: str
    secret_reference: str
    secret_backend_identity: str
    secret_generation: int
    secret_revocation_state: bool
    security_state_fingerprint: str
    control_plane_host: str
    control_plane_port: int
    scheduler_interval: int
    postgres_host: str
    postgres_port: int
    postgres_database: str
    postgres_user: str
    canonical_control_plane_url: str
    context_id: str

    def assert_fresh(self,
                     backend: "ls.RuntimeSecretBackend | None" = None) -> None:
        """Fail closed when the secret authority changed after activation.

        A rotated or revoked secret invalidates the pinned context; callers
        MUST NOT silently adopt the new authority — re-activation is
        required. Zero side effects.
        """
        backend = backend if backend is not None else ls.RuntimeSecretBackend()
        name = self.secret_reference.split(":", 1)[1]
        if backend.generation(name) != self.secret_generation:
            raise RuntimeError(
                "activation context is STALE: secret generation changed after "
                "activation — rotated authority is never adopted silently; "
                "re-activation required (B4-CXR4R3)")
        if backend.is_revoked(name) != self.secret_revocation_state:
            raise RuntimeError(
                "activation context is STALE: secret revocation state changed "
                "after activation — re-activation required (B4-CXR4R3)")

    def runtime_dsn(self,
                    backend: "ls.RuntimeSecretBackend | None" = None) -> str:
        """Ephemeral DSN from the PINNED authority (never stored/evidenced).

        Resolves the pinned reference through the approved store and derives
        the DSN from the PINNED postgres parameters. Fails closed on a stale
        context. The password exists only in process memory.
        """
        backend = backend if backend is not None else ls.RuntimeSecretBackend()
        self.assert_fresh(backend)
        password = backend.resolve(self.secret_reference)
        return (f"postgresql://{self.postgres_user}:{password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}")

    def safe_summary(self) -> dict:
        """Evidence-ready, secret-free summary — reference identity and pinned
        bind parameters only. NEVER the password or a password-bearing DSN."""
        return {
            "context_id": self.context_id,
            "config_fingerprint": self.config_fingerprint,
            "secret_reference": self.secret_reference,
            "secret_backend": self.secret_backend_identity,
            "secret_generation": self.secret_generation,
            "secret_revocation_state": self.secret_revocation_state,
            "security_state_fingerprint": self.security_state_fingerprint,
            "control_plane_host": self.control_plane_host,
            "control_plane_port": self.control_plane_port,
            "scheduler_interval": self.scheduler_interval,
            "postgres_host": self.postgres_host,
            "postgres_port": self.postgres_port,
            "postgres_database": self.postgres_database,
            "postgres_user": self.postgres_user,
            "canonical_control_plane_url": self.canonical_control_plane_url,
        }

    # -- B4-CXR5R3: activation lineage -------------------------------------
    def build_envelope(self, migration_set_identity: dict | None = None
                       ) -> "ActivationEnvelope":
        """Serialize this PINNED context into a safe, secret-free envelope for
        child processes. NEVER includes passwords, tokens, or DSNs."""
        return ActivationEnvelope(
            schema_version=1,
            context_id=self.context_id,
            config_fingerprint=self.config_fingerprint,
            security_state_fingerprint=self.security_state_fingerprint,
            secret_reference=self.secret_reference,
            secret_backend_identity=self.secret_backend_identity,
            secret_generation=self.secret_generation,
            secret_revocation_state=self.secret_revocation_state,
            control_plane_host=self.control_plane_host,
            control_plane_port=self.control_plane_port,
            scheduler_interval=self.scheduler_interval,
            postgres_host=self.postgres_host,
            postgres_port=self.postgres_port,
            postgres_database=self.postgres_database,
            postgres_user=self.postgres_user,
            canonical_control_plane_url=self.canonical_control_plane_url,
            migration_set_identity=dict(migration_set_identity or {}),
        )

    def child_environment(self, migration_set_identity: dict | None = None
                          ) -> dict:
        """SANITIZED child environment for API/worker/migration subprocesses
        (B4-CXR5R3).

        Starts from sanitized_environment() (strips ambient POSTGRES_* /
        worker-secret values), removes EVERY ambient OCE_* variable (the
        envelope is now the only activation authority — a child cannot be
        redirected by a mutated parent environment), and injects the safe
        activation envelope. Children prove current secret generation/
        revocation freshness against the approved store or fail closed.
        """
        env = ls.sanitized_environment()
        for key in [k for k in env if k.startswith("OCE_")]:
            env.pop(key, None)
        env["OCE_ACTIVATION_ENVELOPE"] = self.build_envelope(
            migration_set_identity).to_json()
        return env


def _envelope_present(environ: dict | None = None) -> bool:
    """True when the (child) environment carries an activation envelope."""
    env = environ if environ is not None else os.environ
    return bool(env.get("OCE_ACTIVATION_ENVELOPE"))


def _context_from_envelope(raw: str, env: dict,
                           backend: "ls.RuntimeSecretBackend"
                           ) -> "ActivationContext":
    """Reconstruct the PINNED ActivationContext from a child envelope
    (B4-CXR5R3).

    The child consumes the parent's safe envelope instead of re-resolving
    ambient authority: it proves current secret generation/revocation
    freshness against the approved store (stale -> fail closed BEFORE any
    socket/database/workspace/process activity), verifies the envelope's
    context identity is self-consistent, and re-validates posture from the
    (sanitized) child environment. The envelope itself contains no secrets.
    """
    try:
        envelope = ActivationEnvelope.from_json(raw)
    except ValueError as exc:
        raise SystemExit(
            f"OCE activation lineage BLOCKED: {redact_message(str(exc))} — "
            "malformed activation envelope (B4-CXR5R3)") from exc
    if envelope.schema_version != 1:
        raise SystemExit(
            "OCE activation lineage BLOCKED: unsupported envelope schema "
            f"version {envelope.schema_version} (B4-CXR5R3)")
    name = envelope.secret_reference.split(":", 1)[1]
    if backend.generation(name) != envelope.secret_generation or \
            backend.is_revoked(name) != envelope.secret_revocation_state:
        raise SystemExit(
            "OCE activation lineage STALE: secret authority changed after "
            "parent activation — rotated/revoked authority is never adopted "
            "silently; re-activation required (B4-CXR5R3)")
    # identity self-consistency: the context id must match the envelope's
    # pinned metadata (a forged/inconsistent envelope fails closed)
    expected_id = hashlib.sha256(
        (f"{envelope.config_fingerprint}|{envelope.secret_reference}|"
         f"{envelope.secret_generation}|{envelope.secret_revocation_state}|"
         f"{envelope.secret_backend_identity}").encode("utf-8")).hexdigest()
    if envelope.context_id != expected_id:
        raise SystemExit(
            "OCE activation lineage BLOCKED: envelope context identity is "
            "inconsistent — forged activation lineage refused (B4-CXR5R3)")
    # posture re-validated from the sanitized child environment
    synth = dict(env)
    synth["OCE_CONTROL_PLANE_HOST"] = envelope.control_plane_host
    synth["OCE_CONTROL_PLANE_PORT"] = str(envelope.control_plane_port)
    synth["OCE_SCHEDULER_INTERVAL"] = str(envelope.scheduler_interval)
    synth["OCE_POSTGRES_HOST"] = envelope.postgres_host
    try:
        eff = effective_from_env(synth)
        validate_effective(eff)
    except ValidationError:
        raise SystemExit(startup_report(synth))
    return ActivationContext(
        effective_config=eff,
        config_fingerprint=envelope.config_fingerprint,
        secret_reference=envelope.secret_reference,
        secret_backend_identity=envelope.secret_backend_identity,
        secret_generation=envelope.secret_generation,
        secret_revocation_state=envelope.secret_revocation_state,
        security_state_fingerprint=envelope.security_state_fingerprint,
        control_plane_host=envelope.control_plane_host,
        control_plane_port=envelope.control_plane_port,
        scheduler_interval=envelope.scheduler_interval,
        postgres_host=envelope.postgres_host,
        postgres_port=envelope.postgres_port,
        postgres_database=envelope.postgres_database,
        postgres_user=envelope.postgres_user,
        canonical_control_plane_url=envelope.canonical_control_plane_url,
        context_id=envelope.context_id,
    )


def create_activation_context(
        environ: dict | None = None,
        backend: "ls.RuntimeSecretBackend | None" = None,
        eff: EffectiveConfig | None = None) -> ActivationContext:
    """Build ONE immutable activation context (B4-CXR4R3 / B4-CXR5R3).

    PARENT path (no envelope in the environment):

      snapshot env ONCE
        -> validate governed OCE namespace
        -> resolve EffectiveConfig ONCE (default < file < environment < cli)
        -> validate posture (validate_effective)
        -> resolve required secret metadata (reference MUST resolve)
        -> freeze ActivationContext

    A caller may pass a PRE-RESOLVED validated *eff* (from the same
    snapshot) so a full start resolves the environment exactly once; the
    context then freezes that same effective config.

    CHILD path (OCE_ACTIVATION_ENVELOPE present in the environment): the
    context is reconstructed from the parent's safe envelope — proving
    secret generation/revocation freshness against the approved store and
    rejecting forged/inconsistent identities — instead of re-resolving
    ambient authority (B4-CXR5R3).

    Raises SystemExit (fail closed) on any violation. The SAME frozen object
    is then passed to every runtime consumer, so the configuration that
    passes the gate is the configuration the runtime actually uses, and a
    later os.environ mutation cannot change the activation.
    """
    env = dict(environ if environ is not None else os.environ)
    raw_envelope = env.get("OCE_ACTIVATION_ENVELOPE")
    if raw_envelope:
        backend = backend if backend is not None else ls.RuntimeSecretBackend()
        return _context_from_envelope(raw_envelope, env, backend)
    if eff is None:
        try:
            eff = effective_from_env(env)  # namespace + posture validated
            validate_effective(eff)  # explicit, self-documenting
        except ValidationError:
            # operator-legible, secret-free denial — same contract as the
            # other activation gates (no raw exception prose reaches operator)
            raise SystemExit(startup_report(env))
    backend = backend if backend is not None else ls.RuntimeSecretBackend()
    ref = eff.get("postgres.password_ref")
    name = ref.split(":", 1)[1]
    try:
        resolve_startup_secret(eff, backend)  # reference must actually resolve
    except (KeyError, PermissionError) as exc:
        raise SystemExit(
            redact_message(str(exc)) + " — run `python scripts/oce_local.py "
            "configure` to materialize the local runtime secret (fail closed, "
            "B4-CXR4R3)") from exc
    except ValidationError as exc:
        raise SystemExit(startup_report(env)) from exc
    generation = backend.generation(name)
    revoked = backend.is_revoked(name)
    cfg_fp = eff.fingerprint
    sec_meta = {name: {"generation": generation, "revoked": revoked,
                        "backend": "local-runtime-store-v1"}}
    sec_fp = security_state_fingerprint(sec_meta)
    host = str(eff.get("control_plane.host"))
    port = int(eff.get("control_plane.port"))
    interval = int(eff.get("control_plane.scheduler_interval"))
    pg_host = str(eff.get("postgres.host"))
    context_id = hashlib.sha256(
        f"{cfg_fp}|{ref}|{generation}|{revoked}|local-runtime-store-v1".encode(
            "utf-8")).hexdigest()
    return ActivationContext(
        effective_config=eff,
        config_fingerprint=cfg_fp,
        secret_reference=ref,
        secret_backend_identity="local-runtime-store-v1",
        secret_generation=generation,
        secret_revocation_state=revoked,
        security_state_fingerprint=sec_fp,
        control_plane_host=host,
        control_plane_port=port,
        scheduler_interval=interval,
        postgres_host=pg_host,
        postgres_port=ls.PG_PORT,
        postgres_database=ls.PG_DB,
        postgres_user=ls.PG_USER,
        canonical_control_plane_url=f"http://{host}:{port}",
        context_id=context_id,
    )


def startup_report(environ: dict | None = None, prefix: str = "OCE") -> str:
    """Operator-legible, secret-free startup gate message.

    B4-CXR4R6: config-valid reports "configuration valid" — never "START
    ok"/"ready"/"startable", which are reserved for the complete
    runtime-start contract.
    """
    report = validate_configuration(environ)
    if report["ok"]:
        return (f"{prefix} configuration valid "
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


def outbound_cp_url(environ: dict | None = None,
                    ctx: "ActivationContext | None" = None) -> str:
    """Canonical outbound control-plane target for workers (B4-CXR3R3).

    The Book 4 activation gate ALWAYS runs first regardless of whether
    OCE_CP_URL is set — a worker can never skip validation by supplying the
    URL. OCE_CP_URL is NOT an arbitrary operational string: when present it
    is treated as a VERIFIED COMPATIBILITY ASSERTION that must equal the
    canonical loopback endpoint derived from the validated effective config
    (control_plane.host + control_plane.port). Anything else — external
    host (10.x / 192.168.x / public hostname), noncanonical port, embedded
    credentials, path/query — fails closed before any socket activity.

    When a pinned ActivationContext (B4-CXR4R3) is supplied, the canonical
    endpoint comes from the PINNED config — post-creation environment
    mutation cannot move a worker's target.
    """
    env = environ if environ is not None else os.environ
    if ctx is not None:
        canonical = ctx.canonical_control_plane_url
    else:
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
    return validate_configuration()


if __name__ == "__main__":  # pragma: no cover - manual diagnostic
    print(startup_report())
    sys.exit(0 if validate_configuration()["ok"] else 1)