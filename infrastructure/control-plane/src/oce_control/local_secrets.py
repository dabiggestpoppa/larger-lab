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


def require_runtime_dsn() -> str:
    """Fail-closed DSN for API/worker entrypoints.

    Prefers POSTGRES_DSN, then the runtime secret store. Raises with a
    clear remediation hint when neither exists — there is deliberately no
    predictable fallback.
    """
    env_dsn = os.environ.get("POSTGRES_DSN")
    if env_dsn:
        return env_dsn
    if SECRETS_FILE.exists() or os.environ.get("POSTGRES_PASSWORD"):
        return postgres_dsn()
    raise RuntimeError(
        "no PostgreSQL DSN configured: set POSTGRES_DSN or run "
        "`python scripts/oce_local.py configure` to generate a local secret"
    )
