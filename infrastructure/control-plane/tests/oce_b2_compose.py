"""B2 control-plane stack helpers (B2-R2).

Owns the B2 compose stack lifecycle for tests: starts PostgreSQL + Redis
on loopback ports (5433/6380), waits for truthful readiness, and tears
down WITHOUT removing the durable postgres volume (cleanup removes only
disposable resources; durable state removal requires explicit operator
authorization — see B2-R7).
"""
import os
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
COMPOSE = BASE_DIR / "compose"
COMPOSE_FILE = COMPOSE / "compose.yml"

POSTGRES = "b2-local-postgresql"
REDIS = "b2-local-redis"
ALL_SERVICES = [POSTGRES, REDIS]

PG_HOST = "127.0.0.1"
PG_PORT = 5433
PG_USER = "oce_control_admin"
PG_DB = "oce_control"
REDIS_PORT = 6380

_DSN = "postgresql://{user}:{pw}@{host}:{port}/{db}"


def runtime_password() -> str:
    """POSTGRES_PASSWORD for the compose stack (B2-R7).

    Never a predictable default: either the operator's POSTGRES_PASSWORD
    env or the generated .runtime secret (0600, gitignored).
    """
    from oce_control.local_secrets import ensure_runtime_secret
    return ensure_runtime_secret()


def TEST_SECRETS() -> dict:
    return {"POSTGRES_PASSWORD": runtime_password()}


def docker_available():
    import shutil
    if shutil.which("docker") is None:
        return False
    r = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
    return r.returncode == 0


def dsn():
    return _DSN.format(user=PG_USER, pw=runtime_password(),
                       host=PG_HOST, port=PG_PORT, db=PG_DB)


def redis_url():
    return f"redis://127.0.0.1:{REDIS_PORT}/0"


def _env():
    env = dict(os.environ)
    env["POSTGRES_PASSWORD"] = runtime_password()
    return env


def _run_docker(args, timeout=300):
    return subprocess.run(["docker"] + args, capture_output=True, text=True,
                          timeout=timeout, env=_env())


def compose(*args, check=True, timeout=300):
    r = subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE)] + list(args),
                       cwd=str(COMPOSE), env=_env(), capture_output=True, text=True,
                       timeout=timeout)
    if check:
        assert r.returncode == 0, f"compose {' '.join(args)} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    return r


def health(container):
    r = _run_docker(["inspect", "-f", "{{.State.Health.Status}}", container])
    return r.stdout.strip() if r.returncode == 0 else "missing"


def pg_ready(timeout_s=120):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if health(POSTGRES) == "healthy":
            return True
        time.sleep(2)
    return False


def redis_ready(timeout_s=90):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if health(REDIS) == "healthy":
            return True
        time.sleep(2)
    return False


def stack_up():
    """Idempotently start the B2 stack and wait for readiness."""
    if not docker_available():
        raise RuntimeError("Docker unavailable")
    compose("up", "-d")
    assert pg_ready(), "postgres not ready"
    assert redis_ready(), "redis not ready"


def stack_down_disposable():
    """Tear down containers/network; PRESERVE the durable postgres volume."""
    compose("down", check=False)  # no -v: durable volume survives
