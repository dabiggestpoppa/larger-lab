"""OCE Book 2 — local runtime secrets (B2-R7 / B4-CXR3R1).

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

INITIALIZATION vs RUNTIME (B4-CXR3R1 — no self-legitimation):

* INITIALIZATION path (``initialize_runtime_secret`` / ``ensure_runtime_secret``,
  called only by explicit `configure`/first governed start, the CI runner, and
  the test stack helper) MAY accept an operator POSTGRES_PASSWORD or generate
  a strong random secret, and persists it in the approved untracked store.
* RUNTIME path (``read_runtime_secret`` / ``derive_runtime_dsn`` /
  ``require_runtime_dsn`` / ``compose_environment``) NEVER materializes or
  overwrites a secret. An ambient POSTGRES_PASSWORD therefore cannot rewrite
  an existing store, cannot materialize a missing store, and cannot
  self-legitimate a matching ambient POSTGRES_DSN.
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


def _atomic_write_json(path: Path, data: dict) -> None:
    """Atomically persist *data* to *path* (same-directory tmp + os.replace).

    A crash mid-write can never leave a partially-written secrets.json: the
    approved store is either the complete previous state or the complete new
    state (B4-CXR4R1, test H).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
    _chmod(path, 0o600)


def initialize_runtime_secret(environ: dict | None = None) -> str:
    """INITIALIZATION path — ONE-TIME ONLY (B4-CXR4R1).

    FIRST INITIALIZATION (store absent):
      * may accept an explicitly authorized operator POSTGRES_PASSWORD from
        *environ*, or generate a strong ephemeral secret;
      * persists atomically to the approved untracked store
        (.runtime/secrets.json, 0600).

    ALREADY INITIALIZED (store exists):
      * ordinary start/restart/configure MUST NEVER overwrite it;
      * ambient POSTGRES_PASSWORD MUST NOT rotate it, erase metadata, or be
        silently adopted;
      * if the store exists but the ambient POSTGRES_PASSWORD differs, this
        FAILS CLOSED with a "use the explicit rotation path" message;
      * if the store exists but is unreadable/corrupt, this FAILS CLOSED
        instead of destroying it.

    Runtime read paths (read_runtime_secret / derive_runtime_dsn /
    require_runtime_dsn / compose_environment) never call this — an ambient
    POSTGRES_PASSWORD can therefore never mutate secret authority while the
    runtime is running.
    """
    env = environ if environ is not None else os.environ
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    _chmod(RUNTIME_DIR, 0o700)
    if SECRETS_FILE.exists():
        existing = load_runtime_secret()
        if existing is None:
            raise RuntimeError(
                "approved secret store exists but is unreadable/corrupt — "
                "manual remediation required; OCE never overwrites an "
                "existing store (B4-CXR4R1)")
        env_pw = env.get("POSTGRES_PASSWORD")
        if env_pw and env_pw != existing:
            raise RuntimeError(
                "secret already initialized and ambient POSTGRES_PASSWORD "
                "differs from the approved store — use the explicit rotation "
                "path; ordinary start/restart/configure never rotates secret "
                "authority (B4-CXR4R1)")
        return existing
    # FIRST INITIALIZATION: store absent
    env_pw = env.get("POSTGRES_PASSWORD")
    if env_pw:
        data = {"postgres_password": env_pw, "source": "environment"}
    else:
        data = {"postgres_password": secrets.token_urlsafe(MIN_SECRET_BYTES),
                "source": "generated"}
    _atomic_write_json(SECRETS_FILE, data)
    return data["postgres_password"]


def ensure_runtime_secret(environ: dict | None = None) -> str:
    """INITIALIZATION alias kept for lifecycle/test callers (B4-CXR3R1).

    Same contract as initialize_runtime_secret — INIT ONLY. Never call this
    from a runtime read path; use read_runtime_secret() / derive_runtime_dsn().
    """
    return initialize_runtime_secret(environ)


def load_runtime_secret() -> str | None:
    """Read the persisted runtime secret, or None if not configured yet."""
    if not SECRETS_FILE.exists():
        return None
    try:
        return json.loads(SECRETS_FILE.read_text(encoding="utf-8")).get("postgres_password")
    except (json.JSONDecodeError, OSError):
        return None


def read_runtime_secret() -> str | None:
    """RUNTIME read path — NEVER materializes or overwrites a secret.

    Returns the persisted postgres password or None when the store is
    absent. Safe to call from any runtime path (zero side effects).
    """
    return load_runtime_secret()


def _load_full_store() -> dict:
    """Load the full secrets.json dict; missing/corrupt yields {} (callers
    decide fail-closed semantics; never writes)."""
    if not SECRETS_FILE.exists():
        return {}
    try:
        data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def initialize_worker_token() -> str:
    """INITIALIZATION path (B4-CXR5R1) — materialize the worker token ONCE.

    Called only by the explicit init phase (`oce_local configure` / first
    governed start). Generates a strong token when absent and preserves the
    existing token on later invocations — a runtime start/restart/recover
    NEVER silently adds a token to an existing store. Atomic write.
    """
    if SECRETS_FILE.exists():
        # a corrupt/unparseable store is REFUSED, never rewritten with only
        # a token (mirrors initialize_runtime_secret's fail-closed contract)
        try:
            raw = SECRETS_FILE.read_text(encoding="utf-8")
            parsed = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            raise RuntimeError(
                "approved secret store exists but is unreadable/corrupt — "
                "manual remediation required; OCE never overwrites an "
                "existing store (B4-CXR4R1)")
        if not isinstance(parsed, dict):
            raise RuntimeError(
                "approved secret store is not a JSON object — manual "
                "remediation required; OCE never overwrites it (B4-CXR4R1)")
        if parsed.get("worker_token"):
            return parsed["worker_token"]
    data = _load_full_store()
    data["worker_token"] = secrets.token_urlsafe(24)
    _atomic_write_json(SECRETS_FILE, data)
    return data["worker_token"]


def read_worker_token() -> str:
    """RUNTIME read path (B4-CXR5R1) — read-only, fails closed when absent.

    The worker token lives ONLY in the approved store; it is never passed
    through process argv or ambient environment. Zero side effects.
    """
    data = _load_full_store()
    token = data.get("worker_token")
    if not token or not isinstance(token, str):
        raise RuntimeError(
            "worker token not configured — run `oce_local configure` to "
            "initialize it (runtime reads never materialize one)")
    return token


def sanitized_environment(environ: dict | None = None) -> dict:
    """Child-process environment WITHOUT ambient secret authority (B4-CXR5R1).

    Strips ambient POSTGRES_DSN / POSTGRES_PASSWORD / OCE_WORKER_TOKEN /
    OCE_WORKER_SECRET so a spawned process can never inherit a secret that
    was not deliberately supplied through a governed carrier. The governed
    store remains the ONLY source of secret material; children read it
    directly. Docker-compose subprocesses use compose_environment() instead
    (the compose stack is the specifically governed carrier for the
    container's POSTGRES_PASSWORD).
    """
    env = dict(environ if environ is not None else os.environ)
    for var in ("POSTGRES_DSN", "POSTGRES_PASSWORD",
                "OCE_WORKER_TOKEN", "OCE_WORKER_SECRET"):
        env.pop(var, None)
    return env


def write_compose_env() -> Path:
    """Persist .runtime/compose.env (0600) for `docker compose` invocations.

    A projection of the governed store for the compose stack (the governed
    carrier). Never passes a raw ambient secret: the value comes from
    initialize_runtime_secret() (one-time init, existing store read-only).
    """
    pw = initialize_runtime_secret()
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    _chmod(RUNTIME_DIR, 0o700)
    COMPOSE_ENV_FILE.write_text(f"POSTGRES_PASSWORD={pw}\n", encoding="utf-8")
    _chmod(COMPOSE_ENV_FILE, 0o600)
    return COMPOSE_ENV_FILE


def compose_environment() -> dict[str, str]:
    """Env dict for docker compose / migrate / api / worker (RUNTIME, read-only).

    B4-CXR5R1: starts from sanitized_environment() so ambient secret
    authority (POSTGRES_DSN / POSTGRES_PASSWORD / OCE_WORKER_TOKEN /
    OCE_WORKER_SECRET) is NEVER inherited by a child. POSTGRES_PASSWORD and
    POSTGRES_DSN are set ONLY from the governed store when a secret already
    exists (the compose stack is the specifically governed carrier for the
    container's POSTGRES_PASSWORD). When the store is absent, teardown
    commands still run (empty substitution) while any activation that needs
    the secret fails closed at its own gate — an ambient runtime value can
    never create secret authority (B4-CXR3R1).
    """
    env = sanitized_environment()
    pw = read_runtime_secret()
    if pw:
        env["POSTGRES_PASSWORD"] = pw
        env["POSTGRES_DSN"] = derive_runtime_dsn()
    return env


def derive_runtime_dsn() -> str:
    """RUNTIME DSN derivation — read-only, fails closed when the store is absent.

    Never materializes from ambient POSTGRES_PASSWORD and never consults an
    ambient POSTGRES_DSN: the DSN is derived from the approved store. An
    absent store raises with a remediation hint (B4-CXR3R1).
    """
    pw = read_runtime_secret()
    if not pw:
        raise RuntimeError(
            "no governed PostgreSQL secret configured — run "
            "`python scripts/oce_local.py configure` to materialize the local "
            "runtime secret (runtime reads never materialize one)")
    return f"postgresql://{PG_USER}:{pw}@{PG_HOST}:{PG_PORT}/{PG_DB}"


def postgres_dsn() -> str:
    """Alias of derive_runtime_dsn() (read-only, fail closed)."""
    return derive_runtime_dsn()


def require_runtime_dsn(environ: dict | None = None) -> str:
    """Fail-closed DSN for API/worker entrypoints (B4-R3R4 / B4-CXR3R1).

    The DSN is DERIVED from the governed secret store boundary — never from
    an ambient POSTGRES_DSN that could bypass Book 4 secret validation, and
    never materialized from ambient POSTGRES_PASSWORD.

    A caller-supplied POSTGRES_DSN is accepted ONLY when it equals the
    governed derivation (internal runtime propagation, e.g.
    compose_environment()); a DSN that diverges from the governed secret
    reference is REJECTED as a bypass. An ambient POSTGRES_PASSWORD is never
    consulted: it cannot rewrite an existing store, cannot materialize a
    missing store, and cannot self-legitimate a matching DSN. Raises with a
    clear remediation hint when the store is absent — no predictable fallback.
    """
    env = environ if environ is not None else os.environ
    governed = derive_runtime_dsn()  # read-only; raises "configure" when absent
    env_dsn = env.get("POSTGRES_DSN")
    if env_dsn:
        if env_dsn == governed:
            return env_dsn  # internal runtime propagation, matches the store
        raise RuntimeError(
            "POSTGRES_DSN conflicts with the governed secret-derived DSN — "
            "set the secret reference (OCE_POSTGRES_PASSWORD_REF) and let OCE "
            "derive the DSN (B4-R3R4); external DSN bypasses are rejected")
    return governed


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
        # Atomic (same-dir tmp + os.replace): a failed rotation/revocation can
        # never leave a partially rewritten secrets.json (B4-CXR4R1, test H).
        _atomic_write_json(self.file, data)

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
