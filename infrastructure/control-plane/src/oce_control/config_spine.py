"""OCE Book 4 — Configuration & Security Control Spine.

ONE canonical configuration + security control spindle: explicit ownership,
deterministic resolution, fail-closed validation, a secret-reference model,
redaction / leakage defense, least-privilege authorization boundaries,
private-first network posture, live-order denial, billable-cloud gates, and a
deterministic drift fingerprint.

Design rules (fail closed):

* Unknown settings never silently activate functionality.
* A lower-authority source never silently overrides a higher-authority policy.
* Invalid / unauthorized configuration -> NO START / SAFE DEGRADED STATE.
* Real secrets never live in source, fixtures, evidence, logs, artifacts, CLI
  history, committed config, or test snapshots. Runtime refers to secrets via
  an approved secret reference; un-resolvable secrets fail closed.
* Configuration never grants arbitrary authority; every operator override is
  attributable.
* Network expansion, live-order / execution modes, and billable cloud
  activation are denied unless explicitly authorized through the approved
  control path.
Each book must not weaken the frozen Book 2/3 guarantees (sandbox, fence
generation, authenticated outbound sessions, one-effect idempotency).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone


# --------------------------------------------------------------------------- #
# Sensitive value semantics
# --------------------------------------------------------------------------- #
SECRET_REF_PREFIX = "secret:"          # e.g. secret:postgres_password
SECRET_REF_RE = re.compile(r"^secret:[A-Za-z0-9_.-]+$")

# Values that must never appear unredacted in any output path.
SENSITIVE_SUFFIXES = (
    "password", "secret", "token", "apikey", "api_key", "key", "credential",
    "dsn", "private_key", "bearer",
)
REDACTED = "<REDACTED>"


def is_sensitive(name: str) -> bool:
    low = name.lower()
    return any(s in low for s in SENSITIVE_SUFFIXES)


def redact_value(name: str, value: object) -> object:
    """Return a safe representation of *value* for external display.

    Sensitive names redact to REDACTED. Secret references are kept as
    references (never resolved values). Non-sensitive values pass through.
    """
    if isinstance(value, str) and SECRET_REF_RE.match(value):
        return value  # a reference, not a secret value — safe to show
    if is_sensitive(name):
        return REDACTED
    return value


def redact_mapping(mapping: dict) -> dict:
    """Recursively redact a nested config/mapping by key name."""
    out = {}
    for k, v in mapping.items():
        if isinstance(v, dict):
            out[k] = redact_mapping(v)
        elif isinstance(v, list):
            out[k] = [redact_mapping(i) if isinstance(i, dict) else
                      redact_value(str(k), i) for i in v]
        else:
            out[k] = redact_value(str(k), v)
    return out


def redact_string(text: str, secrets_pool: list[str] | None = None) -> str:
    """Redact known secret values and secret references out of a free string
    (log line, exception message, CLI output) — the leakage-defense primitive.
    """
    out = text
    if secrets_pool:
        for s in secrets_pool:
            if not s:
                continue
            out = out.replace(s, REDACTED)
    # Redact any "key=secretvalue" that follows a sensitive key.
    out = re.sub(
        r"(?i)(" + "|".join(SENSITIVE_SUFFIXES) + r")[\"']?=([^\\s,;}\"']+)",
        r"\1=" + REDACTED,
        out,
    )
    return out


# --------------------------------------------------------------------------- #
# Setting ownership registry (surface A)
# --------------------------------------------------------------------------- #
SOURCE_ENV = "environment"
SOURCE_FILE = "file"
SOURCE_CLI = "cli"
SOURCE_DEFAULT = "default"
_PRECEDENCE = [SOURCE_DEFAULT, SOURCE_FILE, SOURCE_ENV, SOURCE_CLI]


class ValidationError(ValueError):
    """Effective configuration is invalid / unauthorized. Fail closed."""


@dataclass(frozen=True)
class Setting:
    # canonical name
    name: str
    # python type family: str, int, float, bool, enum, list, json
    value_type: str
    # owner (who owns the decision): operator, operator(po), policy, system
    owner: str = "policy"
    # allowed sources, ordered low->high; only these are consulted
    allowed_sources: tuple[str, ...] = (SOURCE_DEFAULT, SOURCE_FILE,
                                        SOURCE_ENV, SOURCE_CLI)
    # safe default; None means "no default" (must be declared)
    default: object = None
    has_default: bool = True
    # allowed enum values (for value_type == enum)
    enum: tuple[str, ...] = ()
    # validation function, optional
    validate: callable | None = None
    validation_rule: str = ""
    # mutability: immutable at runtime vs reloadable vs restart-required
    mutability: str = "immutable"
    # internal sensitivity flag
    sensitive: bool = False
    # policy tags used by gates (e.g. network, cloud, live, sandbox)
    tags: tuple[str, ...] = ()
    # configured value blinding for drift fingerprints (never leak secrets)
    drift_blind: bool = False

    def validate_value(self, value: object) -> None:
        if self.validate is not None:
            self.validate(value)
        if self.value_type == "enum" and self.enum:
            if value not in self.enum:
                raise ValidationError(
                    f"setting '{self.name}' value {value!r} not in allowed "
                    f"enum {list(self.enum)}")


_NO_DEFAULT = object()


class SettingsRegistry:
    """Canonical registry of all security/runtime-significant settings.

    Unknown settings, conflicting registrations, unsafe no-default settings,
    and forbidden sources all fail closed at registration/validation time.
    """

    def __init__(self):
        self._settings: dict[str, Setting] = {}
        self._aliases: dict[str, str] = {}  # canonical name -> canonical name
        self._forbidden_sources: set[tuple[str, str]] = set()

    def register(self, setting: Setting) -> "SettingsRegistry":
        if setting.name in self._settings:
            raise ValueError(f"duplicate setting registration: {setting.name}")
        if not setting.has_default and setting.default is not None:
            raise ValueError(f"setting '{setting.name}' declares both no-default "
                             f"and a default value")
        if setting.value_type == "enum" and not setting.enum:
            raise ValueError(f"enum setting '{setting.name}' has no allowed values")
        self._settings[setting.name] = setting
        return self

    def alias(self, source: str, canonical: str) -> "SettingsRegistry":
        # A lower-authority duplicate that collides with a canonical name is a
        # fail-closed condition, not silently resolved.
        if source in self._settings:
            raise ValueError(f"alias '{source}' collides with a canonical setting")
        self._aliases[source] = canonical
        return self

    def forbid_source(self, name: str, source: str) -> "SettingsRegistry":
        self._forbidden_sources.add((name, source))
        return self

    def get(self, name: str) -> Setting | None:
        return self._settings.get(self._aliases.get(name, name))

    @property
    def settings(self) -> dict[str, Setting]:
        return dict(self._settings)

    @property
    def aliases(self) -> dict[str, str]:
        return dict(self._aliases)

    @property
    def forbidden_sources(self) -> set[tuple[str, str]]:
        return set(self._forbidden_sources)

    def freeze(self) -> "SettingsRegistry":
        """Return a validated copy; rejects unknown/underspecified settings."""
        self.validate_registry()
        return self

    def validate_registry(self) -> None:
        for name, setting in self._settings.items():
            if not self.value_type_ok(setting):
                raise ValueError(f"setting '{name}': unsupported type "
                                 f"'{setting.value_type}'")

    def value_type_ok(self, s: Setting) -> bool:
        return s.value_type in ("str", "int", "float", "bool", "enum", "list", "json")

    def _register_standard(self, setting: Setting):
        return self.register(setting)


def _bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        low = v.strip().lower()
        if low in ("1", "true", "yes", "on"):
            return True
        if low in ("0", "false", "no", "off", ""):
            return False
    raise ValidationError(f"not a boolean: {v!r}")


def build_default_registry() -> SettingsRegistry:
    """The canonical OCE Book 4 settings registry (used by the spine and tests).

    Each entry documents owner, sources, default/no-default, validation,
    mutability, sensitivity, tags.
    """
    r = SettingsRegistry()

    def reg(s: Setting) -> None:
        r._register_standard(s)

    # ---- local runtime (operator-owned, restart-required, secret-backed) ----
    reg(Setting(name="control_plane.host", value_type="enum",
                owner="operator", enum=("127.0.0.1", "localhost"),
                default="127.0.0.1", has_default=True,
                validation_rule="loopback-only bind", mutability="restart",
                tags=("network",)))
    def _valid_port(v) -> None:
        if not 1 <= int(v) <= 65535 or int(v) in (8080, 5000, 5432):
            raise ValidationError("invalid/reserved port")

    def _valid_scheduler_interval(v) -> None:
        if not 1 <= int(v) <= 3600:
            raise ValidationError("scheduler interval must be 1..3600 seconds")

    reg(Setting(name="control_plane.port", value_type="int",
                owner="operator", default=8448, has_default=True,
                validate=_valid_port,
                validation_rule="1..65535, excludes public defaults",
                mutability="restart", tags=("network",)))
    reg(Setting(name="control_plane.scheduler_interval", value_type="int",
                owner="operator", default=5, has_default=True,
                validate=_valid_scheduler_interval,
                validation_rule="1..3600 seconds", mutability="restart",
                tags=("runtime",)))

    reg(Setting(name="control_plane.public_listen", value_type="bool",
                owner="policy", default=False, has_default=True,
                validation_rule="denied by default; cannot be activated",
                mutability="restart", tags=("network", "deny-by-default")))
    reg(Setting(name="postgres.host", value_type="str", owner="operator",
                default="127.0.0.1", mutability="restart",
                validation_rule="local database bind", tags=("database",)))
    def _valid_secret_ref(v) -> None:
        if not isinstance(v, str) or not SECRET_REF_RE.match(v):
            raise ValidationError(
                "postgres.password_ref must be a secret:reference "
                "(never a plain value)")

    reg(Setting(name="postgres.password_ref", value_type="str",
                owner="operator", has_default=False,
                validate=_valid_secret_ref,
                validation_rule="secret:reference (no plain value)",
                mutability="restart", sensitive=True, tags=("secret",)))

    # ---- transports & isolation (policy-owned, immutable) ----
    reg(Setting(name="redis.mode", value_type="enum", owner="policy",
                enum=("transport", "cache"), default="transport",
                validation_rule="redis is disposable transport only",
                mutability="immutable", tags=("durability",)))
    reg(Setting(name="workers.egress", value_type="enum", owner="policy",
                enum=("deny", "loopback"), default="deny",
                validation_rule="network disabled by default",
                mutability="immutable", tags=("network", "sandbox")))
    reg(Setting(name="sandbox.strict", value_type="bool", owner="policy",
                default=True,
                validation_rule="missing mandatory isolation blocks execution",
                mutability="immutable", tags=("sandbox",)))
    reg(Setting(name="sandbox.process_tree_termination", value_type="bool",
                owner="policy", default=True, mutability="immutable",
                validation_rule="complete process-tree termination",
                tags=("sandbox",)))
    reg(Setting(name="sessions.auth_required", value_type="bool",
                owner="policy", default=True, mutability="immutable",
                validation_rule="authenticated outbound sessions mandatory",
                tags=("session", "authorization")))

    # ---- execution / capital denial (policy-owned, immutable) ----
    reg(Setting(name="execution.broker_enabled", value_type="bool",
                owner="policy", default=False,
                validation_rule="broker execution disabled", mutability="immutable",
                tags=("live", "deny-by-default")))
    reg(Setting(name="execution.paper_trading_enabled", value_type="bool",
                owner="policy", default=False,
                validation_rule="paper trading disabled by default",
                mutability="immutable", tags=("live",)))
    reg(Setting(name="execution.live_order_mode", value_type="enum",
                owner="policy", enum=("disabled",), default="disabled",
                validation_rule="only 'disabled' is a legal mode",
                mutability="immutable", tags=("live", "deny-by-default")))
    reg(Setting(name="capital.authority", value_type="enum", owner="operator(po)",
                enum=("none", "approved"), default="none",
                validation_rule="denies live-capital by default",
                mutability="immutable", tags=("capital",)))

    # ---- billable cloud gates (policy-owned, immutable, deny-by-default) ----
    reg(Setting(name="cloud.provisioning", value_type="bool",
                owner="policy", default=False,
                validation_rule="no cloud provisioning", mutability="immutable",
                tags=("cloud", "billable", "deny-by-default")))
    reg(Setting(name="cloud.gpu_burst", value_type="bool", owner="policy",
                default=False, validation_rule="no GPU burst spend",
                mutability="immutable", tags=("cloud", "billable",
                                              "deny-by-default")))
    reg(Setting(name="cloud.accounts", value_type="list", owner="policy",
                default=[], validation_rule="empty when dormant",
                mutability="immutable", tags=("cloud",)))
    reg(Setting(name="cloud.cost_ceiling_usd_per_month", value_type="float",
                owner="operator(po)", default=0.0,
                validation_rule="0 means no authorized spend",
                mutability="immutable", tags=("cloud", "billable")))


    # ---- observability / redaction (policy-owned) ----
    reg(Setting(name="logging.redact_secrets", value_type="bool",
                owner="policy", default=True, mutability="reload",
                validation_rule="redact secrets from structured logs",
                tags=("observability", "security")))
    reg(Setting(name="logging.redact_cli", value_type="bool",
                owner="policy", default=True, mutability="reload",
                validation_rule="redact secrets from CLI output",
                tags=("observability", "security")))
    return r


def validate_setting_value(setting: Setting, value: object) -> object:
    """Coerce + validate a raw value into the setting's canonical type.

    Raises ValidationError on failure. Returns the coerced value.
    """
    try:
        if setting.value_type == "bool":
            value = _bool(value)
        elif setting.value_type == "int":
            value = int(value)
        elif setting.value_type == "float":
            value = float(value)
        elif setting.value_type == "list":
            if isinstance(value, str):
                value = json.loads(value)
            if not isinstance(value, list):
                raise ValidationError("expected a list")
        elif setting.value_type == "json":
            if isinstance(value, str):
                value = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValidationError(
            f"setting '{setting.name}' invalid {setting.value_type}: {exc}")
    setting.validate_value(value)
    return value


# --------------------------------------------------------------------------- #
# Deterministic resolution / precedence (surface B)
# --------------------------------------------------------------------------- #
class Source:
    def __init__(self, priority, payload: dict, provenance="", source_level=""):
        self.priority = priority
        self.payload = payload
        self.provenance = provenance
        self.source_level = source_level


class EffectiveConfig:
    """Resolved, validated effective configuration for one scope.

    Resolution is deterministic: give the same sources and the same
    canonical registry, and you always resolve the same effective config.
    """

    def __init__(self, registry: SettingsRegistry, resolved: dict,
                 provenance: dict, fingerprint: str):
        self._registry = registry
        self._resolved = resolved
        self._provenance = provenance
        self._fingerprint = fingerprint
        self._secret_resolver = None

    def bind_secret_resolver(self, resolver) -> "EffectiveConfig":
        self._secret_resolver = resolver
        return self

    def get(self, name: str, default=_NO_DEFAULT):
        if name not in self._resolved:
            if default is not _NO_DEFAULT:
                return default
            raise KeyError(name)
        return self._resolved[name]

    def get_bool(self, name: str) -> bool:
        return bool(self.get(name))

    def __contains__(self, name: str) -> bool:
        return name in self._resolved

    @property
    def resolved(self) -> dict:
        return dict(self._resolved)

    @property
    def provenance(self) -> dict:
        return dict(self._provenance)

    @property
    def fingerprint(self) -> str:
        return self._fingerprint

    def redacted(self) -> dict:
        """Non-secret, display-safe view of the effective config."""
        return redact_mapping(self._resolved)

    def redeclare(self, other: "EffectiveConfig") -> None:
        # Not used in v1; kept for symmetry with reload semantics doc.
        raise NotImplementedError

    def to_dict(self) -> dict:
        return {
            "resolved": redact_mapping(self._resolved),
            "provenance": self._provenance,
            "fingerprint": self._fingerprint,
        }


class ConfigResolver:
    """Deterministic layered resolver with explicit precedence.

    Precedence (low -> high): default < file < environment < cli.
    A lower-priority source never overrides a higher-priority source. Loops
    and duplicate conflicting sources are resolved deterministically.
    """

    def __init__(self, registry: SettingsRegistry,
                 source_order: tuple[str, ...] = _PRECEDENCE):
        self._registry = registry
        self._order = source_order

    @property
    def registry(self) -> SettingsRegistry:
        return self._registry

    def resolve(self, sources: dict[str, dict], cli: dict | None = None) -> EffectiveConfig:
        """*sources* maps source_level -> {name: raw_value}.

        *cli* is merged into the ``cli`` source tier (the highest priority).
        Sources are only consulted if the setting allows them (allowed_sources)
        and the source is not forbidden for that setting. Unknown settings and
        disallowed-source overrides fail closed.
        """
        if cli is not None:
            merged = dict(sources or {})
            merged[SOURCE_CLI] = {**merged.get(SOURCE_CLI, {}), **cli}
            sources = merged
        # 1) gather candidate values per canonical setting per allowed source
        candidates: dict[str, dict[str, object]] = {}
        for level, source_level in enumerate(self._order):
            raw = sources.get(source_level, {})
            if not isinstance(raw, dict):
                raise ValidationError(
                    f"source '{source_level}' must be a mapping")
            for key, value in raw.items():
                setting = self._registry.get(key)
                if setting is None:
                    raise ValidationError(
                        f"unknown setting '{key}' injected from "
                        f"{source_level} — fail closed")
                if (key, source_level) in self._registry.forbidden_sources:
                    raise ValidationError(
                        f"setting '{key}' forbids source '{source_level}'")
                if source_level not in setting.allowed_sources:
                    raise ValidationError(
                        f"setting '{key}' does not allow source "
                        f"'{source_level}' (allowed={setting.allowed_sources})")
                value = validate_setting_value(setting, value)
                candidates.setdefault(key, {})[source_level] = value
                candidates[key]["__owner__"] = setting.name  # for provenance

        # 2) pick highest-priority allowed value per setting (or default)
        resolved: dict[str, object] = {}
        provenance: dict[str, str] = {}
        for key, setting in self._registry.settings.items():
            present: dict[str, object] = {}
            for level in self._order:
                if level in candidates.get(key, {}):
                    present[level] = candidates[key][level]
            if present:
                chosen_level = max(present, key=self._order.index)
                resolved[key] = present[chosen_level]
                provenance[key] = chosen_level
            elif setting.has_default:
                resolved[key] = setting.default
                provenance[key] = "default"
            else:
                raise ValidationError(
                    f"setting '{key}' has no default and was not supplied "
                    f"by any allowed source — NO START")

        # 3) aliases reflected into resolution for lookup stability
        for alias, canonical in self._registry.aliases.items():
            if canonical in resolved and alias not in resolved:
                resolved[alias] = resolved[canonical]
                provenance[alias] = provenance[canonical]

        effective = EffectiveConfig(self._registry, resolved, provenance,
                                    fingerprint_config(self._registry, resolved))
        return self._post_validate(effective)

    def _post_validate(self, effective: EffectiveConfig) -> EffectiveConfig:
        """Cross-setting runtime gates: network, live, cloud, sandbox."""
        validate_effective(effective)
        return effective


def fingerprint_config(registry: SettingsRegistry, resolved: dict) -> str:
    """Deterministic drift fingerprint over NON-SECRET effective settings.

    Sensitive keys are blinded so no secret value leaks into the fingerprint
    while still detecting *change* in sensitive settings (the presence of a
    change alters the fingerprint without revealing the value).
    """
    h = hashlib.sha256()
    for name in sorted(resolved):
        setting = registry.get(name)
        sensitive = setting.sensitive if setting else is_sensitive(name)
        if sensitive:
            h.update(f"{name}=<secret>".encode("utf-8"))
        else:
            h.update(f"{name}={resolved[name]}".encode("utf-8"))
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Startup validation — fail closed (surface C)
# --------------------------------------------------------------------------- #
def validate_effective(effective: EffectiveConfig) -> None:
    """Fail-closed cross-surface checks applied before runtime activation.

    Raises ValidationError for any unauthorized posture (no 'start and hope').
    """
    # private-first network: public listen is denied by default
    if effective.get_bool("control_plane.public_listen") is True:
        raise ValidationError(
            "control_plane.public_listen=True is forbidden — OCE must stay "
            "private-first (loopback only)")

    # redis must remain disposable transport, never sole durable truth
    if effective.get("redis.mode") != "transport":
        raise ValidationError("redis.mode must be 'transport' (disposable)")

    # workers: network disabled by default
    if effective.get("workers.egress") != "deny" and \
       effective.get("workers.egress") != "loopback":
        raise ValidationError("workers.egress must be 'deny' or 'loopback'")

    # sandbox: strict isolation is mandatory
    if effective.get_bool("sandbox.strict") is False:
        raise ValidationError("sandbox.strict=False weakens mandatory isolation")

    # live-order / execution denial
    if effective.get_bool("execution.broker_enabled") is True:
        raise ValidationError("execution.broker_enabled=True is forbidden")
    if effective.get_bool("execution.paper_trading_enabled") is True:
        raise ValidationError("execution.paper_trading_enabled=True is forbidden")
    if effective.get("execution.live_order_mode") != "disabled":
        raise ValidationError("execution.live_order_mode must be 'disabled'")

    # billable cloud gates
    if effective.get_bool("cloud.provisioning") is True:
        raise ValidationError("cloud.provisioning=True is forbidden")
    if effective.get_bool("cloud.gpu_burst") is True:
        raise ValidationError("cloud.gpu_burst=True is forbidden")
    if effective.get("cloud.accounts"):
        raise ValidationError("cloud.accounts must be empty while dormant")
    if (effective.get("cloud.cost_ceiling_usd_per_month") or 0) > 0:
        raise ValidationError("cloud cost ceiling must be $0 (no authorized spend)")

    # sessions: mandatory auth
    if effective.get_bool("sessions.auth_required") is False:
        raise ValidationError("sessions.auth_required=False weakens outbound auth")


# --------------------------------------------------------------------------- #
# Secret reference model (surface D)
# --------------------------------------------------------------------------- #
class SecretStore:
    """Approved, local secret store. Never writes a real secret to a tracked
    path or any evidence/log/CLI surface unless explicitly sized for it.

    Values are stored (ephemeral or filesystem) and exposed by reference only;
    references look like 'secret:name'. Rotation replaces the value with a new
    generation; revocation removes it (fails closure on next resolution).
    """

    def __init__(self, persist: bool = False, dir: str | None = None):
        self._values: dict[str, str] = {}
        self._generations: dict[str, int] = {}
        self._revoked: set[str] = set()
        self._persist = persist
        self._dir = dir

    def store(self, name: str, value: str) -> str:
        if not value:
            raise ValidationError(f"refused to store empty secret '{name}'")
        if not re.match(r"^[A-Za-z0-9_.-]+$", name):
            raise ValidationError(f"invalid secret reference name: {name!r}")
        self._values[name] = value
        self._generations[name] = self._generations.get(name, 0) + 1
        if name in self._revoked:
            self._revoked.discard(name)
        return self.reference(name)

    def reference(self, name: str) -> str:
        return f"secret:{name}"

    def resolve(self, ref: str) -> str:
        if not SECRET_REF_RE.match(ref or ""):
            raise ValidationError(f"not a secret reference: {ref!r}")
        name = ref.split(":", 1)[1]
        if name in self._revoked:
            raise PermissionError(
                f"secret '{name}' is revoked — REFUSED to resolve")
        if name not in self._values:
            raise KeyError(f"secret '{name}' not provisioned — fail closed")
        return self._values[name]

    def rotate(self, name: str, new_value: str) -> str:
        """Rotate: store a new generation for *name*; returns new reference."""
        return self.store(name, new_value)

    def revoke(self, name: str) -> None:
        self._revoked.add(name)
        self._values.pop(name, None)
        self._generations[name] = self._generations.get(name, 0) + 1

    def generation(self, name: str) -> int:
        return self._generations.get(name, 0)

    def has(self, name: str) -> bool:
        return name in self._values

    def is_revoked(self, name: str) -> bool:
        return name in self._revoked

    def snapshot(self, redact: bool = True) -> dict:
        out = {}
        for name in self._values:
            out[name] = {"generation": self._generations.get(name, 0),
                         "revoked": name in self._revoked,
                         "value": REDACTED if redact else self._values[name]}
        for name in self._revoked:
            out.setdefault(name, {"generation": self._generations.get(name, 0),
                                  "revoked": True,
                                  "value": REDACTED if redact else ""})
        return out


def resolve_postgres_password(effective: EffectiveConfig,
                              store: SecretStore) -> str:
    """Resolve the postgres password through the canonical secret store.

    'postgres.password_ref' must be a secret:reference; if it is missing,
    revoked, or an un-resolvable store entry, this fails closed.
    """
    ref = effective.get("postgres.password_ref")
    if not isinstance(ref, str) or not SECRET_REF_RE.match(ref):
        raise ValidationError(
            "postgres.password_ref must be a secret:reference (never a plain "
            "password value)")
    return store.resolve(ref)


# --------------------------------------------------------------------------- #
# Authorization boundaries & operator-override audit (surface F)
# --------------------------------------------------------------------------- #
@dataclass
class OverrideAudit:
    actor: str                 # explicit actor (e.g. operator:po)
    requested_change: str      # human/CSV description of the change
    reason: str                # justification captured at override time
    target: str                # setting name changed
    previous: object           # effective value before (non-secret display)
    new: object                # effective value after (non-secret display)
    timestamp: str = field(default_factory=lambda:
                           datetime.now(timezone.utc).isoformat())
    authorized: bool = False


class ConfigAuthorization:
    """Least-privilege boundaries over configuration mutation.

    Operators may change operator-owned settings; policy-owned settings are
    immutable by configuration at runtime and require an authorized override
    that writes a durable audit record. No invisible override is possible.
    """

    POLICY_OWNER = "policy"

    def __init__(self, registry: SettingsRegistry):
        self._registry = registry
        self._audit: list[OverrideAudit] = []

    def can_mutate(self, actor: str, setting: Setting) -> bool:
        # policy-owned settings are not mutated by operators; only operator /
        # operator(po) owned settings are mutable by those actors.
        if setting.owner == self.POLICY_OWNER:
            return False
        if setting.owner == "operator(po)":
            return actor == "operator:po"
        # operator-owned
        return actor in ("operator", "operator:po")

    def operator_override(self, effective: EffectiveConfig, *, actor: str,
                          setting_name: str, requested_change: str,
                          reason: str, new_value: object) -> object:
        """Authorized override with durable, attributable audit trail.

        Returns the *new effective value* for a mutable, non-sensitive setting
        and records the change. Policy-owned or sensitive settings reject the
        override regardless of actor.
        """
        setting = self._registry.get(setting_name)
        if setting is None:
            raise ValidationError(f"unknown setting override: {setting_name}")
        if not self.can_mutate(actor, setting):
            raise PermissionError(
                f"actor '{actor}' cannot override policy-owned setting "
                f"'{setting_name}'")
        if setting.sensitive:
            raise PermissionError(
                f"override of sensitive setting '{setting_name}' is not "
                f"permitted through this path")
        new_value = validate_setting_value(setting, new_value)
        self._audit.append(OverrideAudit(
            actor=actor, requested_change=requested_change, reason=reason,
            target=setting_name,
            previous=effective.get(setting_name, None), new=new_value,
            authorized=True))
        return new_value

    @property
    def audit(self) -> list[OverrideAudit]:
        return list(self._audit)