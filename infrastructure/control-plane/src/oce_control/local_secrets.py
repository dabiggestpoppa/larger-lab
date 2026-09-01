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

# B4-CXR6R1: DEDICATED activation-handoff authority. The activation
# capability (OCE_ACTIVATION_ENVELOPE) is MACed with this key so an ambient
# environment can never forge or self-sign a child activation. The key is
# high-entropy (256-bit), DOMAIN-SEPARATED from the PostgreSQL password and
# the worker token (never derived from either), initialized ONCE by the
# explicit configure phase, and read-only at runtime. It never appears in
# environment, argv, process title, logs, evidence, diagnostics, or the
# repository — only in this 0600 file.
ACTIVATION_KEY_FILE_NAME = "activation_handoff_key"
# Consumed-capability nonce ledger (single-use replay protection). Written
# ONLY after a capability verifies successfully; never on a denied path.
CONSUMED_NONCES_FILE_NAME = "consumed_activation_nonces.json"
# Capability lifetime (seconds). The envelope is consumed at child startup;
# the window exists so a launched child can always verify before starting
# work, while a replayed/stale capability fails closed.
CAPABILITY_TTL_SECONDS = 900


def activation_key_file() -> Path:
    return RUNTIME_DIR / ACTIVATION_KEY_FILE_NAME


def consumed_nonces_file() -> Path:
    return RUNTIME_DIR / CONSUMED_NONCES_FILE_NAME


def initialize_activation_handoff_key() -> str:
    """INITIALIZATION path (B4-CXR6R1) — materialize the dedicated
    activation-handoff key ONCE.

    Called only by the explicit init phase (`oce_local configure`).
    Generates a strong 256-bit random key when absent and PRESERVES the
    existing key on later invocations — an ordinary start/restart/recover
    never creates or replaces it. Atomic write with restrictive permissions
    at creation. The key is domain-separated: it is generated independently
    and is never derived from the PostgreSQL password or worker token.
    """
    path = activation_key_file()
    if path.exists():
        key = read_activation_handoff_key()  # validates + preserves
        return key
    key = secrets.token_hex(32)  # 256-bit entropy
    _atomic_write_text(path, key + "\n", mode=0o600)
    return key


def read_activation_handoff_key() -> str:
    """RUNTIME read path (B4-CXR6R1) — read-only, fails closed when absent.

    The activation-handoff key lives ONLY in the approved 0600 runtime file;
    it is never read from the environment and never emitted. A missing or
    malformed key fails closed with a `configure` remediation hint — runtime
    paths never materialize one.
    """
    path = activation_key_file()
    if not path.exists():
        raise RuntimeError(
            "activation handoff key not configured — run `oce_local "
            "configure` to initialize it (runtime reads never materialize "
            "one; B4-CXR6R1)")
    try:
        key = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(
            f"activation handoff key unreadable: {exc} — manual remediation "
            "required; OCE never recreates it (B4-CXR6R1)") from exc
    if not key or len(key) < 64 or not all(c in "0123456789abcdef" for c in key):
        raise RuntimeError(
            "activation handoff key is malformed — manual remediation "
            "required; OCE never recreates it (B4-CXR6R1)")
    return key


def _load_consumed_nonces() -> set[str]:
    """Read the consumed-capability nonce ledger (read-only)."""
    path = consumed_nonces_file()
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    if not isinstance(data, dict):
        return set()
    return {k for k, v in data.items()
            if isinstance(k, str) and isinstance(v, (int, float))}


def mark_capability_consumed(nonce: str) -> None:
    """Record *nonce* as consumed (B4-CXR6R1 single-use replay protection).

    Called ONLY after a capability verifies successfully. Locked atomic
    read-modify-write: concurrent consumers cannot lose entries. Old nonces
    are pruned so the ledger stays bounded (a replayed old capability is
    already rejected by its expiry + parent binding; the ledger guards the
    launch window).
    """
    if not isinstance(nonce, str) or not nonce:
        raise RuntimeError("refusing to consume a malformed capability nonce")
    path = consumed_nonces_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.parent / f".{path.name}.lock"
    import time
    now = time.time()
    with open(lock_path, "a+b") as lf:
        _exclusive_lock(lf)
        try:
            data = {}
            try:
                parsed = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    data = parsed
            except (json.JSONDecodeError, OSError):
                pass
            data[nonce] = now
            # bound the ledger: drop entries older than 24h (their expiry +
            # freshness checks already fail closed long before this window)
            cutoff = now - 24 * 3600
            pruned = {k: v for k, v in data.items()
                      if isinstance(v, (int, float)) and v >= cutoff}
            _atomic_write_json(path, pruned)
        finally:
            _unlock(lf)


def is_capability_consumed(nonce: str) -> bool:
    """True when *nonce* was already consumed (replay guard, read-only)."""
    return nonce in _load_consumed_nonces()

# Local-only defaults that are NOT secrets (the password is never defaulted).
PG_USER = "oce_control_admin"
PG_DB = "oce_control"
PG_HOST = "127.0.0.1"
PG_PORT = 5433

MIN_SECRET_BYTES = 24  # token_urlsafe(24) -> >= 32 chars
MIN_SECRET_CHARS = 32  # strength contract: generated AND operator secrets


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
        _atomic_write_text(tmp, json.dumps(data, indent=2))
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
    _chmod(path, 0o600)


def _atomic_write_text(path: Path, content: str, mode: int = 0o600) -> None:
    """Write *content* to *path* RESTRICTIVE at creation (B4-CXR5R4).

    The file is created with mode 0600 via os.open — never written with
    broad permissions and chmodded afterward (no permissive window). Same-
    directory tmp + os.replace keeps the write atomic.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
    _chmod(path, mode)


def _exclusive_lock(lock_file) -> None:
    """Take an exclusive advisory lock on *lock_file* (fcntl on POSIX,
    msvcrt on Windows). Serializes read-modify-write of the approved store so
    concurrent initialization/revocation can never lose metadata
    (B4-CXR5R4)."""
    if os.name == "nt":
        import msvcrt
        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)


def _unlock(lock_file) -> None:
    if os.name == "nt":
        import msvcrt
        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _load_full_store_at(path: Path) -> dict:
    """Load + schema-validate the store at *path* (missing/unparseable-JSON
    yields {}; valid JSON with an invalid schema raises)."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    _validate_store_schema(data)
    return data


def _mutate_store(update_fn, secrets_file: Path | None = None) -> None:
    """Read-modify-write of the approved store under an exclusive file lock
    (B4-CXR5R4 #12): concurrent initialization/revocation cannot erase
    unrelated entries (worker token, b4_meta, ...). The lock and atomic write
    target *secrets_file* (default: the module store) — a backend mutates
    ITS OWN file, never the global store."""
    target = secrets_file if secrets_file is not None else SECRETS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.parent / f".{target.name}.lock"
    with open(lock_path, "a+b") as lf:
        _exclusive_lock(lf)
        try:
            data = _load_full_store_at(target)
            update_fn(data)
            _atomic_write_json(target, data)
        finally:
            _unlock(lf)


def _validate_secret_value(value: str, label: str,
                           min_length: bool = True) -> None:
    """Validate an operator-supplied secret BEFORE persistence (B4-CXR5R4
    #6-7): reject empty, undersized (init strength contract), CR/LF,
    NUL/control characters, and values that cannot be represented safely by
    the approved carrier. *min_length=False* is used only by the TEST-ONLY
    rotate seam (representation safety still applies)."""
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label}: empty secret refused (B4-CXR5R4)")
    if min_length and len(value) < MIN_SECRET_CHARS:
        raise ValueError(
            f"{label}: secret below the {MIN_SECRET_CHARS}-character strength "
            "contract (B4-CXR5R4)")
    if "\r" in value or "\n" in value:
        raise ValueError(
            f"{label}: CR/LF characters refused — newline injection could "
            "corrupt compose.env/DSN carriers (B4-CXR5R4)")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError(
            f"{label}: control characters refused — not safely representable "
            "by the approved carrier (B4-CXR5R4)")


def _validate_store_schema(data: dict) -> None:
    """Fail closed on malformed secret-store types (B4-CXR5R4 #13): the store
    must be a JSON object; every entry (except b4_meta) must be a string;
    metadata records must be objects with integer generations. A dict/list/
    null value is NEVER silently coerced into a credential."""
    if not isinstance(data, dict):
        raise RuntimeError(
            "approved secret store must be a JSON object (B4-CXR5R4)")
    for key, value in data.items():
        if key == B4_META_KEY:
            if not isinstance(value, dict):
                raise RuntimeError(
                    "approved secret store b4_meta must be an object "
                    "(B4-CXR5R4)")
            for name, rec in value.items():
                if not isinstance(rec, dict) or \
                        not isinstance(rec.get("generation"), int):
                    raise RuntimeError(
                        f"approved secret store b4_meta record '{name}' is "
                        "malformed (generation must be an int) (B4-CXR5R4)")
            continue
        if not isinstance(value, str):
            raise RuntimeError(
                f"approved secret store entry '{key}' must be a string — "
                "dict/list/null values are never coerced into credentials "
                "(B4-CXR5R4)")


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
    if "POSTGRES_PASSWORD" in env and env["POSTGRES_PASSWORD"] is not None:
        env_pw = env["POSTGRES_PASSWORD"]
        # B4-CXR5R4: explicit init passwords are VALIDATED before persistence
        # (empty, undersized, CR/LF, NUL/control all refused)
        _validate_secret_value(env_pw, "POSTGRES_PASSWORD")
        data = {"postgres_password": env_pw, "source": "environment"}
    else:
        data = {"postgres_password": secrets.token_urlsafe(MIN_SECRET_BYTES),
                "source": "generated"}
    # B4-CXR5R4: locked read-modify-write — concurrent init cannot lose
    # metadata (worker token / b4_meta / unrelated entries)
    _mutate_store(lambda d: d.update(data))
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
    """Load the module-level store; see _load_full_store_at."""
    return _load_full_store_at(SECRETS_FILE)


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
        _validate_store_schema(parsed)
        if parsed.get("worker_token"):
            return parsed["worker_token"]
    def _set_token(data: dict) -> None:
        if not data.get("worker_token"):
            data["worker_token"] = secrets.token_urlsafe(24)
    _mutate_store(_set_token)  # B4-CXR5R4: locked RMW preserves other entries
    return _load_full_store()["worker_token"]


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
    """Persist .runtime/compose.env (0600, restrictive AT CREATION) for
    `docker compose` invocations (B4-CXR5R4 #10).

    A projection of the governed store for the compose stack (the governed
    carrier). Never passes a raw ambient secret: the value comes from
    initialize_runtime_secret() (one-time init, existing store read-only).
    The stored secret is re-validated before projection so a directly-crafted
    store can never inject extra compose.env entries; a failed projection
    leaves the approved store untouched (the store write and the projection
    are independent atomic steps).
    """
    pw = initialize_runtime_secret()
    _validate_secret_value(pw, "stored postgres_password")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    _chmod(RUNTIME_DIR, 0o700)
    _atomic_write_text(COMPOSE_ENV_FILE, f"POSTGRES_PASSWORD={pw}\n")
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

    B4-CXR5R4 #8: the DSN is NOT built through unsafe raw concatenation —
    the password is percent-encoded (urllib.parse.quote_plus) so reserved
    URI characters (/, :, @, #, ?) can never redirect or corrupt the DSN.
    """
    pw = read_runtime_secret()
    if not pw:
        raise RuntimeError(
            "no governed PostgreSQL secret configured — run "
            "`python scripts/oce_local.py configure` to materialize the local "
            "runtime secret (runtime reads never materialize one)")
    from urllib.parse import quote_plus
    return (f"postgresql://{PG_USER}:{quote_plus(pw)}"
            f"@{PG_HOST}:{PG_PORT}/{PG_DB}")


def runtime_connection_params() -> dict:
    """Structured psycopg2 connection parameters from the governed store
    (B4-CXR5R4 #8): host/port/dbname/user/password — no DSN string to
    concatenate, parse, or leak. Fails closed when the store is absent."""
    pw = read_runtime_secret()
    if not pw:
        raise RuntimeError(
            "no governed PostgreSQL secret configured — run "
            "`python scripts/oce_local.py configure` to materialize the local "
            "runtime secret (runtime reads never materialize one)")
    return {"host": PG_HOST, "port": PG_PORT, "dbname": PG_DB,
            "user": PG_USER, "password": pw}


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

    def __init__(self, secrets_file: Path | None = None, *, test_seam: bool = False):
        # Resolve the default lazily so tests that monkeypatch SECRETS_FILE
        # (module global) observe the patched path.
        #
        # B4-CXR5R4: *test_seam* gates the TEST-ONLY store-metadata mutation
        # (rotate). Production code never constructs a seam backend; a
        # store-only write is NOT an authorized operational rotation.
        self._file = secrets_file
        self._test_seam = test_seam

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
        if not isinstance(data, dict):
            return {}
        _validate_store_schema(data)  # never coerce dict/list/null -> secret
        return data

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

    # -- lifecycle ---------------------------------------------------------
    # B4-CXR5R4 (CXR5-04): PRODUCTION ROTATION IS FUTURE-LOCKED. A store-only
    # write is NOT a coherent database credential rotation (it never moves
    # the PostgreSQL role password, compose.env, live API/worker connections,
    # recovery state, generation transition, or the durable audit record).
    # rotate() is therefore a TEST-ONLY metadata seam: it raises unless the
    # backend is constructed with test_seam=True, and no production path may
    # present a store-only write as an authorized rotation.
    def rotate(self, name: str, new_value: str) -> None:
        if not self._test_seam:
            raise RuntimeError(
                "production secret rotation is FUTURE-LOCKED in Book 4: a "
                "store-only write is not a coherent database rotation (role "
                "password, compose.env, live connections, recovery, "
                "generation transition, and durable audit must move "
                "together). This method is a TEST-ONLY metadata seam — "
                "construct RuntimeSecretBackend(test_seam=True) to exercise "
                "the store mechanics (B4-CXR5R4)")
        # representation safety only — the strength contract belongs to the
        # real INIT path (this seam is not an operational rotation)
        _validate_secret_value(new_value, f"rotation value for '{name}'",
                               min_length=False)
        if self._load().get(self._entry_key(name)) is None:
            raise KeyError(f"secret '{name}' not provisioned — cannot rotate "
                           "an absent secret")

        def _update(data: dict) -> None:
            data[self._entry_key(name)] = new_value
            meta = dict(data.get(B4_META_KEY) or {})
            rec = dict(self._meta(data, name))
            rec["generation"] = int(rec.get("generation", 1)) + 1
            rec["revoked"] = False
            meta[name] = rec
            data[B4_META_KEY] = meta
        _mutate_store(_update, self.file)  # locked RMW on THIS backend's file

    def revoke(self, name: str) -> None:
        # Revocation is a fail-closed security primitive (the reference stops
        # resolving) and remains operational. It is metadata-state mutation,
        # not a DB rotation; like every mutation it is a locked RMW.
        def _update(data: dict) -> None:
            meta = dict(data.get(B4_META_KEY) or {})
            rec = dict(self._meta(data, name))
            rec["revoked"] = True
            rec["generation"] = int(rec.get("generation", 1)) + 1
            meta[name] = rec
            data[B4_META_KEY] = meta
            data.pop(self._entry_key(name), None)
        _mutate_store(_update, self.file)  # locked RMW on THIS backend's file

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
