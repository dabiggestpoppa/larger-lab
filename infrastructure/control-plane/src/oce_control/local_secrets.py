"""OCE Book 2 — local runtime secrets (B2-R7).

There is NO predictable default PostgreSQL password anywhere in the
runtime. The operator either supplies POSTGRES_PASSWORD explicitly or the
first `configure`/`start` generates an ephemeral secret with
``secrets.token_urlsafe(24)`` and persists it OUTSIDE version control:

    <control-plane>/.runtime/
        secrets.json     0600   {"postgres_password": "..."}
        compose.env      0600   POSTGRES_PASSWORD=...
        logs/            0700   api.log, worker.log
        api.pid, worker.pid     runtime-owned PID tracking (never pkill)

.runtime/ is gitignored (see repo .gitignore) and created with 0700;
generated secrets are 0600 and never committed.
"""
from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # infrastructure/control-plane
RUNTIME_DIR = BASE_DIR / ".runtime"
SECRETS_FILE = RUNTIME_DIR / "secrets.json"
COMPOSE_ENV_FILE = RUNTIME_DIR / "compose.env"
LOGS_DIR = RUNTIME_DIR / "logs"

# Local-only defaults that are NOT secrets (the password is never defaulted).
PG_USER = "oce_control_admin"
PG_DB = "oce_control"
PG_HOST = "127.0.0.1"
PG_PORT = 5433

MIN_SECRET_BYTES = 24  # token_urlsafe(24) -> >= 32 chars


def _chmod(path: Path, mode: int) -> None:
    try:
        path.chmod(mode)
    except OSError:
        # Best effort (some CI filesystems ignore modes); the important
        # guarantee is that the secret is never written to a tracked path.
        pass


def ensure_runtime_secret() -> str:
    """Return the operator's or generated POSTGRES_PASSWORD (fail closed).

    If POSTGRES_PASSWORD is set in the environment it wins and is
    persisted so later invocations agree. Otherwise an ephemeral secret is
    generated and stored under .runtime/secrets.json (0600).
    """
    env_pw = os.environ.get("POSTGRES_PASSWORD")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    _chmod(RUNTIME_DIR, 0o700)
    if env_pw:
        data = {"postgres_password": env_pw, "source": "environment"}
    else:
        existing = load_runtime_secret()
        if existing:
            return existing
        data = {"postgres_password": secrets.token_urlsafe(MIN_SECRET_BYTES),
                "source": "generated"}
    SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _chmod(SECRETS_FILE, 0o600)
    return data["postgres_password"]


def load_runtime_secret() -> str | None:
    """Read the persisted runtime secret, or None if not configured yet."""
    if not SECRETS_FILE.exists():
        return None
    try:
        return json.loads(SECRETS_FILE.read_text(encoding="utf-8")).get("postgres_password")
    except (json.JSONDecodeError, OSError):
        return None


def write_compose_env() -> Path:
    """Persist .runtime/compose.env (0600) for `docker compose` invocations."""
    pw = ensure_runtime_secret()
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    _chmod(RUNTIME_DIR, 0o700)
    COMPOSE_ENV_FILE.write_text(f"POSTGRES_PASSWORD={pw}\n", encoding="utf-8")
    _chmod(COMPOSE_ENV_FILE, 0o600)
    return COMPOSE_ENV_FILE


def compose_environment() -> dict[str, str]:
    """Env dict for docker compose / migrate / api / worker (never defaults pw)."""
    env = dict(os.environ)
    env["POSTGRES_PASSWORD"] = ensure_runtime_secret()
    env["POSTGRES_DSN"] = postgres_dsn()
    return env


def postgres_dsn() -> str:
    pw = ensure_runtime_secret()
    return f"postgresql://{PG_USER}:{pw}@{PG_HOST}:{PG_PORT}/{PG_DB}"


def require_runtime_dsn(environ: dict | None = None) -> str:
    """Fail-closed DSN for API/worker entrypoints (B4-R3R4).

    The DSN is DERIVED from the governed secret store boundary — never from
    an ambient POSTGRES_DSN that could bypass Book 4 secret validation.

    A caller-supplied POSTGRES_DSN is accepted ONLY when it equals the
    governed derivation (i.e. it is the runtime's own internal propagation,
    e.g. compose_environment()); a DSN that diverges from the governed
    secret reference is REJECTED as a bypass. Raises with a clear
    remediation hint when the store is absent — no predictable fallback.
    """
    env = environ if environ is not None else os.environ
    env_dsn = env.get("POSTGRES_DSN")
    if env_dsn:
        governed = postgres_dsn()
        if env_dsn == governed:
            return env_dsn  # internal runtime propagation, matches the store
        raise RuntimeError(
            "POSTGRES_DSN conflicts with the governed secret-derived DSN — "
            "set the secret reference (OCE_POSTGRES_PASSWORD_REF) and let OCE "
            "derive the DSN (B4-R3R4); external DSN bypasses are rejected")
    if SECRETS_FILE.exists() or os.environ.get("POSTGRES_PASSWORD"):
        return postgres_dsn()
    raise RuntimeError(
        "no PostgreSQL DSN configured: run "
        "`python scripts/oce_local.py configure` to materialize the local "
        "runtime secret"
    )


# --------------------------------------------------------------------------- #
# B4-R3R3 — approved secret-resolution boundary (Book 4 reference model)
# --------------------------------------------------------------------------- #
# The canonical local runtime PostgreSQL secret lives ONLY in the untracked
# .runtime/secrets.json store (0600), written there by Book 2 `configure`
# materialization. Book 4 holds a REFERENCE (secret:runtime-local) which this
# backend resolves; startup passes only when the reference actually resolves.
CANONICAL_REF_NAME = "runtime-local"
B4_META_KEY = "b4_meta"


class RuntimeSecretBackend:
    """Approved local secret store adapter for the Book 4 reference model.

    Resolves ``secret:runtime-local`` to the materialized postgres password
    persisted by ``configure``/``ensure_runtime_secret``. Tracks a small
    non-secret metadata record (generation, revoked) so rotation / revocation
    are observable without ever exposing the value. Missing, unresolvable,
    or revoked references fail closed (KeyError / PermissionError).
    """

    def __init__(self, secrets_file: Path | None = None):
        # Resolve the default lazily so tests that monkeypatch SECRETS_FILE
        # (module global) observe the patched path.
        self._file = secrets_file

    @property
    def file(self) -> Path:
        return self._file if self._file is not None else SECRETS_FILE

    def _load(self) -> dict:
        f = self.file
        if not f.exists():
            return {}
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save(self, data: dict) -> None:
        f = self.file
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _chmod(f, 0o600)

    # -- reference semantics ------------------------------------------------
    # (the persistence helpers _load/_save above are lazy-bound to SECRETS_FILE)
    def _meta(self, data: dict, name: str) -> dict:
        meta = data.get(B4_META_KEY) or {}
        return (meta.get(name) or {}) if isinstance(meta, dict) else {}

    # -- reference semantics ------------------------------------------------
    def _entry_key(self, name: str) -> str:
        # the canonical local ref maps to Book 2's durable store key
        return "postgres_password" if name == CANONICAL_REF_NAME else name

    def resolve(self, ref: str) -> str:
        import re as _re
        if not isinstance(ref, str) or not _re.match(r"^secret:[A-Za-z0-9_.-]+$", ref):
            raise ValueError(f"not a secret reference: {ref!r}")
        name = ref.split(":", 1)[1]
        data = self._load()
        if self._meta(data, name).get("revoked"):
            raise PermissionError(
                f"secret '{name}' is revoked — REFUSED to resolve")
        value = data.get(self._entry_key(name))
        if not value:
            raise KeyError(
                f"secret '{name}' not provisioned — run `oce_local configure` "
                f"to materialize the local runtime secret")
        return value

    def has(self, name: str) -> bool:
        data = self._load()
        return bool(data.get(self._entry_key(name)))

    def generation(self, name: str) -> int:
        return int(self._meta(self._load(), name).get("generation", 1))

    def is_revoked(self, name: str) -> bool:
        return bool(self._meta(self._load(), name).get("revoked"))

    # -- lifecycle (rotate / revoke are PO-audited, never silent) ----------
    def rotate(self, name: str, new_value: str) -> None:
        if not new_value:
            raise ValueError("refused to rotate to an empty secret")
        data = self._load()
        data[self._entry_key(name)] = new_value
        meta = dict(data.get(B4_META_KEY) or {})
        rec = dict(self._meta(data, name))
        rec["generation"] = int(rec.get("generation", 1)) + 1
        rec["revoked"] = False
        meta[name] = rec
        data[B4_META_KEY] = meta
        self._save(data)

    def revoke(self, name: str) -> None:
        data = self._load()
        meta = dict(data.get(B4_META_KEY) or {})
        rec = dict(self._meta(data, name))
        rec["revoked"] = True
        rec["generation"] = int(rec.get("generation", 1)) + 1
        meta[name] = rec
        data[B4_META_KEY] = meta
        data.pop(self._entry_key(name), None)
        self._save(data)

    def security_metadata(self) -> dict:
        """Non-secret metadata only (reference identity, generation, revoked).

        Never includes the password value or its digest.
        """
        data = self._load()
        meta = data.get(B4_META_KEY) or {}
        out = {}
        for name, rec in (meta.items() if isinstance(meta, dict) else []):
            out[name] = {"generation": int(rec.get("generation", 1)),
                         "revoked": bool(rec.get("revoked")),
                         "backend": "local-runtime-store-v1"}
        return out
