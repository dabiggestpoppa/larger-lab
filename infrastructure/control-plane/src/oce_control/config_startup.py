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

TRUST BOUNDARY (B4-CXR7U1): see ``B4-THREAT-MODEL.md``. This module's
activation handoff is an AUTHENTICATED PARENT-LAUNCH HANDOFF WITH
ROLE/AUDIENCE CONSISTENCY CHECKING inside ONE trusted local OCE computing
base — NOT a hostile-child isolation boundary. Same-principal child
processes share the parent's trusted-computing-base authority (including
the handoff key); API-level parent/child separation (B4-CXR7U2) is
least-privilege defense in depth, never OS isolation.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
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

# Documented operational (non-config) OCE_* variables used by CI runners and
# evidence tooling. They carry run/evidence IDENTITY ONLY — never credential,
# job, execution, storage, durable-state, or destination authority — so they
# are listed for the governed-namespace check and classified
# OPERATIONAL_IDENTITY_ONLY (B4-CXR6R2): changing them has ZERO effect on
# credentials, job source, execution content, workspace, artifact
# destination, database, network, process launch, or secret authority.
OPERATIONAL_OCE_VARS = frozenset({
    # CI / runner identity + evidence plumbing (identity only)
    "OCE_RUN_ID", "OCE_STAGE_LABEL", "OCE_BLOCK_LABEL", "OCE_BOOK_LABEL",
    "OCE_EVIDENCE_DIR", "OCE_CI_MODE",
    "OCE_EXPECTED_REPO", "OCE_EXPECTED_BRANCH", "OCE_EXPECTED_COMMIT",
    "OCE_EXPECTED_TREE",
})

# B4-CXR6R1: the activation-lineage carrier is a VERIFIED INTERNAL
# CAPABILITY — NEVER OPERATIONAL. It has authority ONLY after cryptographic
# verification (HMAC-SHA-256 with the dedicated 0600 handoff key): a plain
# JSON blob in an ambient environment variable is never authoritative, and
# direct ambient injection without a valid protected proof fails closed
# before any socket/database/migration/workspace/process activity.
VERIFIED_INTERNAL_CAPABILITY_OCE_VARS = frozenset({"OCE_ACTIVATION_ENVELOPE"})

# Role vocabulary for the authenticated activation capability (B4-CXR6R1).
# Capabilities are role-bound: an API capability can never launch a worker, a
# worker capability can never authorize a migration, and a migration
# capability can never authorize an API.
CAPABILITY_ROLES = ("api", "worker", "migration", "outbound_worker")

# B4-CXR5R6: AUTHORITY-BEARING inputs — each changes identity, credential,
# job source, execution content, workspace/artifact destination, or persistent
# state location. NONE of these is merely OPERATIONAL; each is enforced at its
# consumer (oce_b3_worker / oce_worker / config gate):
#   OCE_CP_URL        -> VERIFIED_COMPATIBILITY_ASSERTION (must equal the
#                        canonical loopback endpoint; divergence fails closed)
#   OCE_WORKER_ID     -> VERIFIED against the admitted identity at handshake
#   OCE_WORKER_SECRET -> TEST seam only (approved store is the production
#                        authority; ambient value cannot self-authorize)
#   OCE_JOB_FILE      -> TEST_ONLY — rejected in production runtime
#   OCE_WS_BASE / OCE_ATTEMPT_WS / OCE_ARTIFACT_BASE -> path-containment
#                        enforced (working-root containment, no traversal /
#                        symlink escape / repo overwrite / secret-store overlap)
#   OCE_RUNTIME_DIR   -> contained worker-CLI state dir (same enforcement)
AUTHORITY_OCE_VARS = frozenset({
    "OCE_CP_URL", "OCE_WORKER_ID", "OCE_WORKER_SECRET", "OCE_JOB_FILE",
    "OCE_WS_BASE", "OCE_ATTEMPT_WS", "OCE_ARTIFACT_BASE", "OCE_RUNTIME_DIR",
})

# B4-CXR5R6: DEPRECATED AND REJECTED. The worker token lives ONLY in the
# approved secret store (initialize_worker_token / read_worker_token); an
# ambient OCE_WORKER_TOKEN can never be consumed and is refused outright.
DEPRECATED_AND_REJECTED_OCE_VARS = frozenset({"OCE_WORKER_TOKEN"})

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
        _KNOWN_OCE_VARS = frozenset(
            set(ENV_MAP.values()) | set(COMPAT_ALIASES)
            | set(OPERATIONAL_OCE_VARS) | set(AUTHORITY_OCE_VARS)
            | set(VERIFIED_INTERNAL_CAPABILITY_OCE_VARS)
            | set(DEPRECATED_AND_REJECTED_OCE_VARS))
    return _KNOWN_OCE_VARS


def check_governed_namespace(environ: dict) -> None:
    """Fail closed on unknown / typoed / rejected OCE_* variables.

    The governed namespace is the ``OCE_`` prefix. Every variable in the
    process environment that starts with ``OCE_`` must be a known canonical
    env var, a compatibility alias, an authority-bearing consumer-enforced
    variable, or a documented operational variable. Anything else is rejected
    — it could otherwise silently alter the real runtime (e.g.
    ``OCE_EXECUTION_BROKER_ENABLD=true``).

    B4-CXR5R6: DEPRECATED_AND_REJECTED variables (OCE_WORKER_TOKEN) are KNOWN
    but refused explicitly — their authority moved into the approved secret
    store and no ambient value is legal.

    Unrelated variables that merely contain "OCE" as incidental text do not
    start with ``OCE_`` and are deliberately not rejected.
    """
    known = known_oce_vars()
    rejected = sorted(k for k in environ if k in DEPRECATED_AND_REJECTED_OCE_VARS)
    if rejected:
        raise ValidationError(
            "deprecated OCE_* credential/authority variable(s) present and "
            "refused: " + ", ".join(rejected) + " — the worker token lives "
            "ONLY in the approved secret store; no ambient value is accepted "
            "(B4-CXR5R6; see B4-CONFIG-INPUT-INVENTORY.md)")
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
    """AUTHENTICATED, role-bound activation capability for child processes
    (B4-CXR6R1).

    Carries ONLY safe metadata (no passwords, tokens, or DSNs), and the
    payload is MACed with the dedicated activation-handoff key
    (HMAC-SHA-256, constant-time verification). SAFE METADATA IS NOT
    AUTHORITY MERELY BECAUSE IT IS WELL-FORMED: a plain JSON blob in an
    ambient environment variable is never authoritative — the MAC is
    required, and every security-relevant field is re-derived and compared
    against canonical authority after verification.
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
    parent_activation_id: str
    # B4-CXR6R1: role-bound capability fields
    child_role: str
    capability_nonce: str
    issued_at: int
    expires_at: int

    def to_payload(self) -> dict:
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
            "child_role": self.child_role,
            "capability_nonce": self.capability_nonce,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }

    def _canonical_json(self) -> str:
        """Deterministic canonical serialization of the payload (sorted keys,
        compact separators) — the exact byte string the MAC covers."""
        return json.dumps(self.to_payload(), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=True)

    def to_json(self, key: str | None = None) -> str:
        """Serialize as {"payload": <canonical json>, "mac": <hex>}.

        The MAC is HMAC-SHA-256 over the canonical payload with the
        dedicated activation-handoff key (read-only from the approved 0600
        store when *key* is None). The key is never embedded in the
        carrier."""
        payload_json = self._canonical_json()
        key = key if key is not None else ls.read_activation_handoff_key()
        mac = hmac.new(key.encode("utf-8"), payload_json.encode("utf-8"),
                       hashlib.sha256).hexdigest()
        return json.dumps({"payload": payload_json, "mac": mac},
                          sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, payload: dict) -> "ActivationEnvelope":
        """Validate the typed payload (unknown fields, types, ranges)."""
        if not isinstance(payload, dict):
            raise ValueError("capability payload must be a JSON object")
        allowed = {"schema_version", "context_id", "config_fingerprint",
                   "security_state_fingerprint", "secret_reference",
                   "secret_backend_identity", "secret_generation",
                   "secret_revocation_state", "control_plane_host",
                   "control_plane_port", "scheduler_interval",
                   "postgres_host", "postgres_port", "postgres_database",
                   "postgres_user", "canonical_control_plane_url",
                   "migration_set_identity", "parent_activation_id",
                   "child_role", "capability_nonce", "issued_at",
                   "expires_at"}
        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise ValueError(
                "capability payload carries unknown field(s): "
                + ", ".join(unknown) + " (B4-CXR6R1)")
        missing = [k for k in allowed if k not in payload]
        if missing:
            raise ValueError(
                f"capability payload missing fields: {', '.join(missing)}")
        if payload["schema_version"] != 1:
            raise ValueError("unsupported capability schema version")
        if not isinstance(payload["context_id"], str) or not re.fullmatch(
                r"[0-9a-f]{64}", payload["context_id"]):
            raise ValueError("capability context_id must be a 64-hex string")
        for fp_field in ("config_fingerprint", "security_state_fingerprint"):
            if not isinstance(payload[fp_field], str) or not payload[fp_field]:
                raise ValueError(f"capability {fp_field} must be a string")
        for str_field in ("secret_reference", "secret_backend_identity",
                          "control_plane_host", "postgres_host",
                          "postgres_database", "postgres_user",
                          "canonical_control_plane_url",
                          "parent_activation_id"):
            if not isinstance(payload[str_field], str):
                raise ValueError(f"capability {str_field} must be a string")
        for int_field in ("control_plane_port", "scheduler_interval",
                          "postgres_port", "secret_generation",
                          "issued_at", "expires_at"):
            if not isinstance(payload[int_field], int) or \
                    isinstance(payload[int_field], bool):
                raise ValueError(
                    f"capability {int_field} must be an int (bool-as-int "
                    "confusion rejected)")
        if not isinstance(payload["secret_revocation_state"], bool):
            raise ValueError(
                "capability secret_revocation_state must be a bool "
                "(bool-as-int confusion rejected)")
        if not (1 <= payload["control_plane_port"] <= 65535) or \
                not (1 <= payload["postgres_port"] <= 65535):
            raise ValueError("capability port out of range")
        if payload["scheduler_interval"] <= 0:
            raise ValueError("capability scheduler_interval must be positive")
        if payload["secret_generation"] <= 0:
            raise ValueError("capability secret_generation must be positive")
        if not isinstance(payload["migration_set_identity"], dict):
            raise ValueError("capability migration_set_identity must be a dict")
        if payload["child_role"] not in CAPABILITY_ROLES:
            raise ValueError(
                "capability child_role must be one of: "
                + ", ".join(CAPABILITY_ROLES))
        if not isinstance(payload["capability_nonce"], str) or not re.fullmatch(
                r"[0-9a-f]{16,64}", payload["capability_nonce"]):
            raise ValueError("capability nonce must be a hex string")
        if payload["expires_at"] <= payload["issued_at"]:
            raise ValueError("capability expires_at must follow issued_at")
        return cls(
            schema_version=1,
            context_id=payload["context_id"],
            config_fingerprint=payload["config_fingerprint"],
            security_state_fingerprint=payload["security_state_fingerprint"],
            secret_reference=payload["secret_reference"],
            secret_backend_identity=payload["secret_backend_identity"],
            secret_generation=payload["secret_generation"],
            secret_revocation_state=payload["secret_revocation_state"],
            control_plane_host=payload["control_plane_host"],
            control_plane_port=payload["control_plane_port"],
            scheduler_interval=payload["scheduler_interval"],
            postgres_host=payload["postgres_host"],
            postgres_port=payload["postgres_port"],
            postgres_database=payload["postgres_database"],
            postgres_user=payload["postgres_user"],
            canonical_control_plane_url=payload["canonical_control_plane_url"],
            migration_set_identity=payload["migration_set_identity"],
            parent_activation_id=payload["parent_activation_id"],
            child_role=payload["child_role"],
            capability_nonce=payload["capability_nonce"],
            issued_at=payload["issued_at"],
            expires_at=payload["expires_at"],
        )

    @classmethod
    def from_json(cls, raw: str, key: str | None = None) -> "ActivationEnvelope":
        """Parse, MAC-verify (constant-time), and type-validate the carrier.

        Fails closed on: malformed JSON, duplicate JSON keys, unknown
        top-level fields, an oversized carrier, a missing/mismatched MAC,
        unknown payload fields, or malformed types. The key is read from the
        approved 0600 store when *key* is None; it never comes from the
        carrier."""
        if not isinstance(raw, str) or len(raw) > 16384:
            raise ValueError("oversized activation capability carrier")
        try:
            parsed = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
        except json.JSONDecodeError as exc:
            raise ValueError(f"malformed activation capability JSON: {exc}")
        except ValueError as exc:
            raise ValueError(f"activation capability JSON refused: {exc}")
        if not isinstance(parsed, dict):
            raise ValueError("activation capability must be a JSON object")
        unknown = sorted(set(parsed) - {"payload", "mac"})
        if unknown:
            raise ValueError(
                "activation capability carrier carries unknown field(s): "
                + ", ".join(unknown) + " (B4-CXR6R1)")
        payload_json = parsed.get("payload")
        mac = parsed.get("mac")
        if not isinstance(payload_json, str) or not isinstance(mac, str) \
                or not re.fullmatch(r"[0-9a-f]{64}", mac):
            raise ValueError(
                "activation capability missing payload/mac (B4-CXR6R1)")
        key = key if key is not None else ls.read_activation_handoff_key()
        expected = hmac.new(key.encode("utf-8"),
                            payload_json.encode("utf-8"),
                            hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, mac):
            raise ValueError(
                "activation capability MAC verification FAILED — no valid "
                "authenticated capability exists; ambient JSON is never "
                "authoritative (B4-CXR6R1)")
        try:
            payload = json.loads(payload_json,
                                 object_pairs_hook=_reject_duplicate_keys)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(
                f"activation capability payload refused: {exc}")
        now = int(time.time())
        if payload.get("expires_at", 0) < now:
            raise ValueError(
                "activation capability EXPIRED — replayed/stale capability "
                "refused (B4-CXR6R1)")
        return cls.from_dict(payload)


def _reject_duplicate_keys(pairs) -> dict:
    """Reject duplicate/ambiguous JSON object keys (B4-CXR6R1): a duplicate
    key is a representation ambiguity that must never silently win."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key: {k}")
        out[k] = v
    return out


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
        # B4-CXR5R4: standards-compliant percent-encoding — reserved URI
        # characters can never redirect or corrupt the DSN
        from urllib.parse import quote_plus
        return (f"postgresql://{self.postgres_user}:{quote_plus(password)}"
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

    # -- B4-CXR6R1: authenticated role-bound activation lineage -------------
    def build_envelope(self, child_role: str,
                       migration_set_identity: dict | None = None,
                       ttl_seconds: int = ls.CAPABILITY_TTL_SECONDS
                       ) -> "ActivationEnvelope":
        """Serialize this PINNED context into an AUTHENTICATED, role-bound
        activation capability for ONE child process (B4-CXR6R1).

        NEVER includes passwords, tokens, or DSNs. The payload is MACed with
        the dedicated activation-handoff key (read-only from the approved
        0600 store — missing key fails closed with a `configure` hint). A
        fresh nonce + issuance/expiry are minted per launch so a capability
        cannot be replayed from an earlier launch or another parent.
        """
        if child_role not in CAPABILITY_ROLES:
            raise ValueError(
                "child_role must be one of: " + ", ".join(CAPABILITY_ROLES))
        now = int(time.time())
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
            parent_activation_id=self.context_id,
            child_role=child_role,
            capability_nonce=secrets.token_hex(16),
            issued_at=now,
            expires_at=now + ttl_seconds,
        )

    def child_environment(self, child_role: str,
                          migration_set_identity: dict | None = None) -> dict:
        """SANITIZED child environment for API/worker/migration subprocesses
        (B4-CXR6R1).

        Starts from sanitized_environment() (strips ambient POSTGRES_* /
        worker-secret values), removes EVERY ambient OCE_* variable (the
        capability is now the only activation authority — a child cannot be
        redirected by a mutated parent environment), and injects the
        MAC-authenticated activation capability for *child_role*. The child
        verifies the MAC with the approved handoff key, proves current
        secret generation/revocation freshness, re-derives canonical values,
        and enforces its declared role — or fails closed before any
        socket/database/migration/workspace/process activity.
        """
        env = ls.sanitized_environment()
        for key in [k for k in env if k.startswith("OCE_")]:
            env.pop(key, None)
        env["OCE_ACTIVATION_ENVELOPE"] = self.build_envelope(
            child_role, migration_set_identity).to_json()
        return env


def _envelope_present(environ: dict | None = None) -> bool:
    """True when the (child) environment carries an activation capability
    carrier. Presence alone is NOT authority — verification is required."""
    env = environ if environ is not None else os.environ
    return bool(env.get("OCE_ACTIVATION_ENVELOPE"))


def _verify_activation_capability(raw: str, env: dict, role: str | None,
                                  backend: "ls.RuntimeSecretBackend"
                                  ) -> "ActivationEnvelope":
    """AUTHENTICATE + re-derive a child activation capability (B4-CXR6R1).

    1. MAC-verify the carrier (constant-time) with the dedicated handoff key
       — plain JSON in an ambient env var is NEVER authoritative;
    2. reject expired capabilities;
    3. enforce the declared role (API/worker/migration/outbound_worker);
    4. prove secret generation/revocation freshness against the approved
       store (stale -> fail closed BEFORE any activity);
    5. re-derive canonical identities and compare with the authenticated
       payload: PostgreSQL port/database/user from canonical authority,
       canonical control-plane URL from the authenticated host+port, secret
       backend identity, security-state fingerprint from current backend
       metadata, effective-config fingerprint from the reconstructed config,
       and the context identity;
    6. enforce single use (consumed-nonce ledger) after verification.

    Returns the verified envelope. Any failure raises SystemExit (fail
    closed) — zero authority-side effects.
    """
    try:
        envelope = ActivationEnvelope.from_json(raw)
    except ValueError as exc:
        raise SystemExit(
            f"OCE activation lineage BLOCKED: {redact_message(str(exc))} "
            "— no valid authenticated activation capability exists; "
            "ambient JSON is never authoritative (B4-CXR6R1)") from exc
    # role binding: the child must declare the SAME role the parent minted
    if role is None:
        raise SystemExit(
            "OCE activation lineage BLOCKED: an activation capability is "
            "present but no child role was declared — role-bound activation "
            "required (B4-CXR6R1)")
    if role != envelope.child_role:
        raise SystemExit(
            f"OCE activation lineage BLOCKED: capability is role-bound to "
            f"'{envelope.child_role}' but the process declared '{role}' — "
            "role confusion refused before any activity (B4-CXR6R1)")
    # single-use replay protection (checked BEFORE consuming)
    if ls.is_capability_consumed(envelope.capability_nonce):
        raise SystemExit(
            "OCE activation lineage BLOCKED: capability nonce already "
            "consumed — replayed one-time capability refused (B4-CXR6R1)")
    name = envelope.secret_reference.split(":", 1)[1]
    if backend.generation(name) != envelope.secret_generation or \
            backend.is_revoked(name) != envelope.secret_revocation_state:
        raise SystemExit(
            "OCE activation lineage STALE: secret authority changed after "
            "parent activation — rotated/revoked authority is never adopted "
            "silently; re-activation required (B4-CXR6R1)")
    # -- re-derive canonical identities (never blindly trust the payload) --
    # PostgreSQL port/database/user come from canonical Book 4 authority
    for field, canonical in (("postgres_port", ls.PG_PORT),
                             ("postgres_database", ls.PG_DB),
                             ("postgres_user", ls.PG_USER)):
        if getattr(envelope, field) != canonical:
            raise SystemExit(
                f"OCE activation lineage BLOCKED: capability {field} does "
                "not match canonical authority — alternate database identity "
                "refused before any connection (B4-CXR6R1)")
    if envelope.secret_backend_identity != "local-runtime-store-v1":
        raise SystemExit(
            "OCE activation lineage BLOCKED: capability backend identity is "
            "not the canonical approved store (B4-CXR6R1)")
    # canonical control-plane URL is DERIVED from the authenticated host+port
    derived_url = (f"http://{envelope.control_plane_host}:"
                   f"{envelope.control_plane_port}")
    if envelope.canonical_control_plane_url != derived_url:
        raise SystemExit(
            "OCE activation lineage BLOCKED: capability control-plane URL is "
            "not derivable from the authenticated host/port — external URL "
            "forgery refused before any socket activity (B4-CXR6R1)")
    # security fingerprint recomputed from CURRENT approved backend metadata
    sec_meta = {name: {"generation": backend.generation(name),
                       "revoked": backend.is_revoked(name),
                       "backend": "local-runtime-store-v1"}}
    if security_state_fingerprint(sec_meta) != envelope.security_state_fingerprint:
        raise SystemExit(
            "OCE activation lineage BLOCKED: security-state fingerprint does "
            "not match the current approved backend metadata (B4-CXR6R1)")
    # effective config reconstructed from the sanitized child env + pinned
    # bind parameters; its fingerprint must equal the authenticated payload
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
    if eff.fingerprint != envelope.config_fingerprint:
        raise SystemExit(
            "OCE activation lineage BLOCKED: reconstructed effective-config "
            "fingerprint does not match the authenticated capability "
            "(B4-CXR6R1)")
    # context identity recomputed from the RE-DERIVED values
    expected_id = hashlib.sha256(
        (f"{eff.fingerprint}|{envelope.secret_reference}|"
         f"{envelope.secret_generation}|{envelope.secret_revocation_state}|"
         f"{envelope.secret_backend_identity}").encode("utf-8")).hexdigest()
    if envelope.context_id != expected_id:
        raise SystemExit(
            "OCE activation lineage BLOCKED: capability context identity is "
            "inconsistent with re-derived authority (B4-CXR6R1)")
    # consume the one-time capability (only after full verification)
    ls.mark_capability_consumed(envelope.capability_nonce)
    return envelope


def _context_from_envelope(raw: str, env: dict, role: str | None,
                           backend: "ls.RuntimeSecretBackend"
                           ) -> "ActivationContext":
    """Reconstruct the PINNED ActivationContext from a VERIFIED activation
    capability (B4-CXR6R1).

    The child proves the authenticated, role-bound, non-stale lineage and
    re-derives every canonical identity from approved authority instead of
    trusting redundant envelope fields."""
    envelope = _verify_activation_capability(raw, env, role, backend)
    name = envelope.secret_reference.split(":", 1)[1]
    synth = dict(env)
    synth["OCE_CONTROL_PLANE_HOST"] = envelope.control_plane_host
    synth["OCE_CONTROL_PLANE_PORT"] = str(envelope.control_plane_port)
    synth["OCE_SCHEDULER_INTERVAL"] = str(envelope.scheduler_interval)
    synth["OCE_POSTGRES_HOST"] = envelope.postgres_host
    eff = effective_from_env(synth)
    validate_effective(eff)
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
        eff: EffectiveConfig | None = None,
        role: str | None = None) -> ActivationContext:
    """Build ONE immutable activation context (B4-CXR4R3 / B4-CXR6R1).

    PARENT path (no activation capability in the environment):

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
    context is reconstructed ONLY from a verified authenticated activation
    capability — the child proves the MAC (dedicated handoff key),
    role-binding (the *role* the process declares must match the capability),
    freshness (secret generation/revocation), single-use, and re-derives
    every canonical identity from approved authority. An ambient JSON blob
    with no valid protected proof fails closed before any socket/database/
    migration/workspace/process activity (B4-CXR6R1).

    Raises SystemExit (fail closed) on any violation. The SAME frozen object
    is then passed to every runtime consumer, so the configuration that
    passes the gate is the configuration the runtime actually uses, and a
    later os.environ mutation cannot change the activation.
    """
    env = dict(environ if environ is not None else os.environ)
    raw_envelope = env.get("OCE_ACTIVATION_ENVELOPE")
    if raw_envelope:
        backend = backend if backend is not None else ls.RuntimeSecretBackend()
        return _context_from_envelope(raw_envelope, env, role, backend)
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


def config_gate() -> dict:
    """CLI hook for 'start'/'restart': gate on CONFIGURATION before compose up.

    B4-CXR5R7: named truthfully — this validates configuration ONLY and
    never claims the runtime start gate. Activation readiness is a separate,
    strictly stronger contract (pinned context + resolved governed secret +
    dependencies + processes); this function reports configuration validity.
    """
    return validate_configuration()


if __name__ == "__main__":  # pragma: no cover - manual diagnostic
    print(startup_report())
    sys.exit(0 if validate_configuration()["ok"] else 1)