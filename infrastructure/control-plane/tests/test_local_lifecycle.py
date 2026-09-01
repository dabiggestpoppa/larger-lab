"""OCE Book 2 — local lifecycle unit tests (B2-R7).

Pure unit tests (no Docker required): they exercise the deterministic
lifecycle contract — no predictable default secrets, runtime-owned PID
tracking instead of pkill, stale-PID safety, explicit destructive
authorization, loopback-only ports, and no cloud credential dependency.
"""
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from oce_control import local_lifecycle as ll
from oce_control import local_secrets as ls

MARKER = "oce_control.http_api"  # must remain the marker local_lifecycle owns


def _spawn_sleeper() -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(600)"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@pytest.fixture(autouse=True)
def _clean_runtime(monkeypatch, tmp_path):
    """Point every .runtime path at an isolated tmp dir per test."""
    (tmp_path / "runtime").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path / "runtime")
    monkeypatch.setattr(ls, "SECRETS_FILE", tmp_path / "runtime" / "secrets.json")
    monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", tmp_path / "runtime" / "compose.env")
    monkeypatch.setattr(ls, "LOGS_DIR", tmp_path / "runtime" / "logs")
    monkeypatch.setattr(ll, "pid_file", lambda name: tmp_path / "runtime" / f"{name}.pid")
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("POSTGRES_DSN", raising=False)


# --------------------------------------------------------------------------
# Secrets — no predictable defaults
# --------------------------------------------------------------------------

def test_secret_generated_ephemeral_no_predictable_default():
    pw = ls.ensure_runtime_secret()
    assert len(pw) >= 32
    assert pw != "test-secret-b2-pg-001"  # the retired predictable default
    assert ls.load_runtime_secret() == pw
    # idempotent across invocations
    assert ls.ensure_runtime_secret() == pw


def test_secret_honors_operator_env(monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "operator-supplied-strong-secret-1234567890")
    assert ls.ensure_runtime_secret() == "operator-supplied-strong-secret-1234567890"


def test_secret_file_restrictive_permissions():
    ls.ensure_runtime_secret()
    if os.name != "nt":  # POSIX can enforce modes; Windows maps chmod to read-only
        assert ls.RUNTIME_DIR.stat().st_mode & 0o777 == 0o700
        assert ls.SECRETS_FILE.stat().st_mode & 0o777 == 0o600
    # cross-platform guarantee: the runtime secret is never committable
    gitignore = (ls.BASE_DIR.parent.parent / ".gitignore").read_text(encoding="utf-8")
    assert "infrastructure/control-plane/.runtime/" in gitignore, \
        "repo .gitignore must cover the .runtime dir (never committed)"


def test_configure_writes_compose_env_with_secret():
    report = ll.configure()
    assert ls.COMPOSE_ENV_FILE.exists()
    assert f"POSTGRES_PASSWORD={ls.load_runtime_secret()}" in ls.COMPOSE_ENV_FILE.read_text()
    assert report["port_offenders"] == []  # real compose.yml is loopback-only
    # B4-CXR5R1: configure is the INIT phase — it also materializes the
    # worker token ONCE (read-only thereafter; never added by runtime start)
    data = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))
    assert data.get("worker_token")
    assert ls.read_worker_token() == data["worker_token"]
    assert ls.initialize_worker_token() == data["worker_token"]  # preserved


def test_require_runtime_dsn_fails_closed_without_secret():
    with pytest.raises(RuntimeError, match="configure"):
        ls.require_runtime_dsn()


def test_require_runtime_dsn_rejects_external_bypass(monkeypatch):
    # B4-R3R4: an ambient POSTGRES_DSN that diverges from the governed secret
    # store is rejected (external DSN bypass denies fail closed).
    ls.ensure_runtime_secret()
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://u:p@127.0.0.1:5433/db")
    with pytest.raises(RuntimeError, match="bypass"):
        ls.require_runtime_dsn()


def test_require_runtime_dsn_accepts_governed_propagation(monkeypatch):
    # The runtime's OWN internal propagation (exactly the governed DSN) is
    # accepted — this is how compose_environment passes it to subprocesses.
    ls.ensure_runtime_secret()
    monkeypatch.setenv("POSTGRES_DSN", ls.postgres_dsn())
    assert ls.require_runtime_dsn() == ls.postgres_dsn()


# --------------------------------------------------------------------------
# B4-CXR3R1 — init vs runtime authority: an ambient POSTGRES_PASSWORD must
# never mutate the approved store through a runtime read path.
# --------------------------------------------------------------------------

def _store_snapshot() -> dict:
    """Hash/snapshot of the approved secret store (for denial side-effect
    proofs: DENIAL MUST HAVE ZERO AUTHORITY-SIDE EFFECTS)."""
    import hashlib
    if not ls.SECRETS_FILE.exists():
        return {"exists": False}
    return {
        "exists": True,
        "sha256": hashlib.sha256(ls.SECRETS_FILE.read_bytes()).hexdigest(),
        "content": ls.SECRETS_FILE.read_text(encoding="utf-8"),
    }


def test_runtime_password_cannot_materialize_missing_store(monkeypatch):
    # ambient POSTGRES_PASSWORD must NEVER create a store through a runtime
    # read path (CXR3-01-C: runtime password tries to materialize absent store)
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-password-123")
    before = _store_snapshot()
    with pytest.raises(RuntimeError, match="configure"):
        ls.require_runtime_dsn()
    with pytest.raises(RuntimeError, match="configure"):
        ls.derive_runtime_dsn()
    assert _store_snapshot() == before  # zero authority-side effects
    assert not ls.SECRETS_FILE.exists()


def test_runtime_password_cannot_rewrite_existing_store(monkeypatch):
    # CXR3-01-B: a runtime password must not overwrite an existing approved store
    ls.initialize_runtime_secret()
    governed = ls.read_runtime_secret()
    before = _store_snapshot()
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-overwrite-attempt-123456")
    dsn = ls.require_runtime_dsn()
    assert governed in dsn
    assert "ambient-overwrite-attempt-123456" not in dsn
    assert ls.read_runtime_secret() == governed  # store value unchanged
    assert _store_snapshot() == before  # zero authority-side effects


def test_matching_ambient_password_and_dsn_cannot_self_legitimate(monkeypatch):
    # CXR3-01-A: supply password X + a DSN containing X with NO store. The
    # runtime must fail closed and must NOT persist X (self-legitimation).
    monkeypatch.setenv("POSTGRES_PASSWORD", "selflegit-X-9876543210")
    dsn_attack = ("postgresql://oce_control_admin:selflegit-X-9876543210"
                  "@127.0.0.1:5433/oce_control")
    monkeypatch.setenv("POSTGRES_DSN", dsn_attack)
    before = _store_snapshot()
    with pytest.raises(RuntimeError, match="configure"):
        ls.require_runtime_dsn()
    assert _store_snapshot() == before  # DENIAL HAS ZERO AUTHORITY-SIDE EFFECTS
    assert not ls.SECRETS_FILE.exists()


def test_compose_environment_reads_without_materializing(monkeypatch):
    # compose env is a RUNTIME read: no store -> no secret vars, no store
    # created (ambient values never flow to a subprocess); after governed
    # init, the vars come from the STORE, never a stale ambient value
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-compose-1234567890")
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://u:p@127.0.0.1:5432/x")
    env = ls.compose_environment()
    assert "POSTGRES_PASSWORD" not in env
    assert "POSTGRES_DSN" not in env
    assert not ls.SECRETS_FILE.exists()
    # governed init: the INIT path explicitly honors the operator password
    monkeypatch.setenv("POSTGRES_PASSWORD", "governed-operator-pw-123456789012")
    ls.initialize_runtime_secret()
    governed = ls.read_runtime_secret()
    assert governed == "governed-operator-pw-123456789012"
    env2 = ls.compose_environment()
    assert env2["POSTGRES_PASSWORD"] == governed
    assert "ambient-compose-1234567890" not in env2["POSTGRES_PASSWORD"]


def test_restart_uses_same_governed_secret():
    # CXR3-01-Q: restart after clean initialization uses the SAME secret
    ls.initialize_runtime_secret()
    first = ls.read_runtime_secret()
    assert ls.initialize_runtime_secret() == first  # init keeps existing
    assert ls.read_runtime_secret() == first
    assert ls.require_runtime_dsn() == ls.postgres_dsn() == ls.derive_runtime_dsn()


# --------------------------------------------------------------------------
# B4-CXR4R1 — ONE-TIME secret initialization (CXR4-01): ordinary
# start/restart/recover/configure are READ-ONLY over an existing approved
# store. Ambient POSTGRES_PASSWORD may materialize a MISSING store only
# through the explicit INIT path, may never rewrite an existing store, and
# may never rotate/erase metadata. Denials have zero authority-side effects.
# --------------------------------------------------------------------------

def _seed_initialized_store() -> dict:
    """Write a fully-initialized approved store (password + worker token +
    b4_meta + an unrelated secret entry) — the state an already-initialized
    store has after configure + first start."""
    data = {
        "postgres_password": "s" * 40,
        "source": "generated",
        "worker_token": "w" * 40,
        "another_entry": "another-secret-value",
        "b4_meta": {"runtime-local": {"generation": 1, "revoked": False}},
    }
    ls.SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ls.SECRETS_FILE.write_text(json.dumps(data), encoding="utf-8")
    return data


def _mock_docker_runtime(monkeypatch) -> None:
    """Mock every docker/process surface so ll.start()/restart()/recover()
    run deterministically without a live stack."""
    monkeypatch.setattr(ll, "docker_available", lambda: True)
    monkeypatch.setattr(ll, "compose", lambda *a, **k: _FakeComp(0))
    monkeypatch.setattr(ll, "wait_dependencies", lambda *a, **k: True)
    monkeypatch.setattr(ll, "migrate", lambda *a, **k: _FakeComp(0))
    monkeypatch.setattr(ll, "wait_for_http", lambda *a, **k: True)
    monkeypatch.setattr(ll, "smoke",
                        lambda *a, **k: [("health", True), ("console", True)])
    monkeypatch.setattr(ll, "start_process",
                        lambda *a, **k: ls.RUNTIME_DIR / "mock.pid")


def test_cxr4r1_a_start_never_rewrites_existing_store(monkeypatch):
    # A. existing store + ambient POSTGRES_PASSWORD + start() -> store hash
    #    BEFORE == AFTER (ordinary start fails closed, never rotates)
    _seed_initialized_store()
    before = _store_snapshot()
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-differs-9876543210")
    with pytest.raises(RuntimeError, match="explicit rotation path"):
        ll.start()
    assert _store_snapshot() == before


def test_cxr4r1_b_restart_never_rewrites_existing_store(monkeypatch):
    # B. same attack through restart (CLI restart = stop -> start): the safe
    #    shutdown half is always allowed; the activation half fails closed.
    _seed_initialized_store()
    before = _store_snapshot()
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-differs-9876543210")
    _mock_docker_runtime(monkeypatch)
    monkeypatch.setattr(ll, "stop_runtime_processes", lambda: [])
    ll.stop()
    with pytest.raises(RuntimeError, match="explicit rotation path"):
        ll.start()
    assert _store_snapshot() == before


def test_cxr4r1_c_recover_never_rewrites_existing_store(monkeypatch):
    # C. same attack through recover(): the repair path never consults an
    #    ambient password and never rewrites the approved store.
    _seed_initialized_store()
    before = _store_snapshot()
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-differs-9876543210")
    _mock_docker_runtime(monkeypatch)
    ll.recover()
    assert _store_snapshot() == before


def test_cxr4r1_d_e_meta_and_token_survive_start_restart_configure(monkeypatch):
    # D+E. b4_meta and worker_token survive configure/start/restart exactly;
    #    unrelated entries are never lost.
    _seed_initialized_store()
    before = _store_snapshot()
    ll.configure()
    assert _store_snapshot() == before
    _mock_docker_runtime(monkeypatch)
    ll.start()
    assert _store_snapshot() == before
    monkeypatch.setattr(ll, "stop_runtime_processes", lambda: [])
    ll.stop()
    ll.start()  # CLI restart semantics: stop -> start
    assert _store_snapshot() == before
    data = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))
    assert data["worker_token"] == "w" * 40
    assert data["b4_meta"]["runtime-local"]["generation"] == 1
    assert data["another_entry"] == "another-secret-value"


def test_cxr4r1_f_first_clean_initialization_still_works(monkeypatch):
    # F. explicit operator password on the FIRST governed init is honored;
    #    a clean init with no ambient value generates a strong secret.
    monkeypatch.setenv("POSTGRES_PASSWORD", "explicit-init-password-1234567890")
    pw = ls.initialize_runtime_secret()
    assert pw == "explicit-init-password-1234567890"
    assert ls.load_runtime_secret() == pw


def test_cxr4r1_g_rotation_changes_only_authorized_secret_and_generation():
    # G. explicit rotation is attributable + atomic: only the authorized
    #    secret value and its generation metadata change.
    _seed_initialized_store()
    # test_seam=True: rotate() is a TEST-ONLY metadata seam (B4-CXR5R4)
    backend = ls.RuntimeSecretBackend(test_seam=True)
    assert backend.generation("runtime-local") == 1
    backend.rotate("runtime-local", "rotated-governed-secret-abcdef123456")
    data = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))
    assert data["postgres_password"] == "rotated-governed-secret-abcdef123456"
    assert data["worker_token"] == "w" * 40  # untouched
    assert data["another_entry"] == "another-secret-value"  # untouched
    assert data["b4_meta"]["runtime-local"]["generation"] == 2
    assert data["b4_meta"]["runtime-local"]["revoked"] is False


# --------------------------------------------------------------------------
# B4-CXR5R1 — NO secrets in process argv: the worker token is initialized
# once by configure() and read-only at runtime; worker/migrate child argv is
# secret-free; child environments are sanitized; ambient worker-secret values
# can never flow to a spawned process.
# --------------------------------------------------------------------------

def test_cxr5r1_worker_token_init_read_split():
    # 7-8 (CXR5-01): worker token initialized ONCE during the explicit init
    # phase; runtime reads never materialize/add one; a missing store fails
    # closed instead of creating a token on the fly.
    with pytest.raises(RuntimeError, match="worker token"):
        ls.read_worker_token()          # runtime read, no store -> fail closed
    tok = ls.initialize_worker_token()  # explicit init materializes it
    assert tok and ls.read_worker_token() == tok
    assert ls.initialize_worker_token() == tok  # init preserves existing
    before = _store_snapshot()
    assert ls.read_worker_token() == tok         # runtime read never mutates
    assert _store_snapshot() == before


def test_cxr5r1_worker_token_init_refuses_corrupt_store():
    # H (CXR4R1 contract): a corrupt store is REFUSED by the token init path
    # too — never rewritten with only a token, never partially mutated.
    ls.SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ls.SECRETS_FILE.write_text("{corrupt-not-json", encoding="utf-8")
    corrupt = ls.SECRETS_FILE.read_bytes()
    with pytest.raises(RuntimeError, match="unreadable/corrupt"):
        ls.initialize_worker_token()
    assert ls.SECRETS_FILE.read_bytes() == corrupt  # not overwritten
    # a non-object store is refused as well
    ls.SECRETS_FILE.write_text('["not", "a", "dict"]', encoding="utf-8")
    with pytest.raises(RuntimeError, match="not a JSON object"):
        ls.initialize_worker_token()
    assert ls.SECRETS_FILE.read_text(encoding="utf-8") == '["not", "a", "dict"]'


def test_cxr5r1_runtime_never_adds_worker_token_to_existing_store():
    # A store seeded WITHOUT a worker token must not gain one through any
    # runtime read path (start/restart/recover never silently add a token).
    ls.initialize_runtime_secret()
    data = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))
    assert "worker_token" not in data
    before = _store_snapshot()
    with pytest.raises(RuntimeError, match="worker token"):
        ls.read_worker_token()
    assert _store_snapshot() == before  # zero authority-side effects


def test_cxr5r1_worker_launch_argv_has_no_token(monkeypatch):
    # A + B (CXR5-01): the lifecycle worker launch argv contains NO token —
    # the worker reads it from the approved store. A canary token placed in
    # the store never appears in the captured subprocess command list.
    _seed_initialized_store()
    _mock_docker_runtime(monkeypatch)
    seen: dict = {}

    def _capture(name, argv, env=None):
        seen[name] = list(argv)
        seen[f"{name}_env"] = dict(env or {})
        return ls.RUNTIME_DIR / f"{name}.pid"

    monkeypatch.setattr(ll, "start_process", _capture)
    ll.start()
    argv = " ".join(seen["worker"])
    token = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))["worker_token"]
    assert "--token" not in argv
    assert "--dsn" not in argv
    assert token not in argv            # canary: token bytes never in argv
    assert "postgresql://" not in argv
    # B4-CXR5R3: the child env carries the activation envelope, NEVER the
    # token/password or any ambient OCE_* authority
    wenv = seen["worker_env"]
    assert token not in " ".join(wenv.values())
    assert "POSTGRES_PASSWORD" not in wenv and "POSTGRES_DSN" not in wenv
    assert "OCE_ACTIVATION_ENVELOPE" in wenv  # safe lineage carrier present
    assert "context_id" in wenv["OCE_ACTIVATION_ENVELOPE"]


def test_cxr5r1_migrate_argv_has_no_password(monkeypatch):
    # A (CXR5-01): the lifecycle migrate() subprocess argv contains NO
    # password-bearing DSN — migration resolves the governed connection
    # internally. A canary password in the store never enters the command.
    _seed_initialized_store()
    seen: dict = {}

    def _capture_run(cmd, **kw):
        seen["cmd"] = list(cmd)

        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()

    monkeypatch.setattr(ll.subprocess, "run", _capture_run)
    ll.migrate(ctx=None)
    argv = " ".join(seen["cmd"])
    pw = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))["postgres_password"]
    assert "--db" not in argv and "--dsn" not in argv
    assert "postgresql://" not in argv
    assert pw not in argv               # canary: password bytes never in argv


def test_cxr5r1_proc_cmdline_free_of_secrets():
    # C (CXR5-01): the argv the lifecycle constructs reaches the kernel
    # command line cleanly — /proc/<pid>/cmdline contains no token/password.
    # (Lifecycle argv construction is proven secret-free by the captured-argv
    # tests above; this proves the argv -> kernel cmdline mechanism.)
    if not Path("/proc").exists():
        pytest.skip("no /proc — cmdline inspection unsupported on this platform")
    canary = "cmdline-canary-token-9876543210"
    # Replay the EXACT lifecycle worker argv shape (constant list, no secret
    # slots) with a short-lived stand-in process so we can read /proc while
    # alive. The kernel cmdline is byte-identical to the argv list passed.
    argv = [sys.executable, "-c",
            "import time; time.sleep(10)", "--worker-id", "probe-x"]
    assert "--token" not in " ".join(argv)
    proc = subprocess.Popen(argv, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        deadline = time.time() + 5
        seen = None
        while time.time() < deadline:
            try:
                raw = Path(f"/proc/{proc.pid}/cmdline").read_bytes()
                if raw:
                    seen = raw.replace(b"\0", b" ").decode("utf-8", "replace")
                    break
            except OSError:
                pass
            time.sleep(0.002)
        assert seen is not None, "could not read /proc cmdline"
        assert "--token" not in seen
        assert "postgresql://" not in seen
        assert canary not in seen
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_cxr5r1_sanitized_environment_strips_secrets(monkeypatch):
    # 9 (CXR5-01): ambient POSTGRES_DSN / POSTGRES_PASSWORD / worker-token /
    # worker-secret values are stripped from child environments; the compose
    # env inherits ONLY the governed store values.
    monkeypatch.setenv("POSTGRES_DSN", "postgresql://u:p@1.2.3.4/db")
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-pw-1234567890")
    monkeypatch.setenv("OCE_WORKER_TOKEN", "ambient-token-1234567890")
    monkeypatch.setenv("OCE_WORKER_SECRET", "ambient-secret-1234567890")
    env = ls.sanitized_environment()
    for var in ("POSTGRES_DSN", "POSTGRES_PASSWORD",
                "OCE_WORKER_TOKEN", "OCE_WORKER_SECRET"):
        assert var not in env, var
    cenv = ls.compose_environment()  # no store -> no secret vars at all
    assert "POSTGRES_PASSWORD" not in cenv and "POSTGRES_DSN" not in cenv
    assert "OCE_WORKER_TOKEN" not in cenv and "OCE_WORKER_SECRET" not in cenv
    # explicit INIT may honor an operator password; afterwards an ambient
    # rewrite attempt must be ignored — the store (and compose env) is the
    # ONLY source of secret material.
    monkeypatch.delenv("POSTGRES_PASSWORD")
    monkeypatch.setenv("POSTGRES_PASSWORD", "explicit-init-operator-pw-1234567890")
    ls.initialize_runtime_secret()
    governed = ls.read_runtime_secret()
    assert governed == "explicit-init-operator-pw-1234567890"
    monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attack-late-1234567890")
    cenv2 = ls.compose_environment()
    assert cenv2["POSTGRES_PASSWORD"] == governed
    assert "ambient-attack-late-1234567890" not in cenv2["POSTGRES_PASSWORD"]
    assert "OCE_WORKER_TOKEN" not in cenv2


def test_cxr5r1_h_failed_initialization_never_partially_rewrites(monkeypatch):
    # H. corrupt existing store -> REFUSED (never destroyed); an atomic-write
    #    failure mid-init -> no partial secrets.json, no stray tmp file.
    ls.SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ls.SECRETS_FILE.write_text("{corrupt-not-json", encoding="utf-8")
    corrupt = ls.SECRETS_FILE.read_bytes()
    with pytest.raises(RuntimeError, match="unreadable/corrupt"):
        ls.initialize_runtime_secret()
    assert ls.SECRETS_FILE.read_bytes() == corrupt  # not overwritten
    ls.SECRETS_FILE.unlink()
    import os as _os

    def _boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(_os, "replace", _boom)
    with pytest.raises(OSError, match="disk full"):
        ls.initialize_runtime_secret()
    assert not ls.SECRETS_FILE.exists()  # no partial file
    assert not list(ls.RUNTIME_DIR.glob("*.tmp-*"))  # no stray tmp


# --------------------------------------------------------------------------
# B4-CXR5R4 — secret representation + production rotation truth (CXR5-04):
# production rotation is FUTURE-LOCKED (rotate is a TEST-ONLY metadata seam),
# explicit init passwords are validated before persistence, compose.env is
# written atomically restrictive at creation, malformed store schemas fail
# closed, DSNs use standards-compliant escaping, and concurrent mutations
# cannot lose metadata.
# --------------------------------------------------------------------------

def test_cxr5r4_production_rotation_future_locked():
    # W: a store-only rotate() is NOT an authorized operational rotation —
    # it fails closed unless the explicit TEST-ONLY seam is enabled
    _seed_initialized_store()
    backend = ls.RuntimeSecretBackend()  # production default: NO seam
    with pytest.raises(RuntimeError, match="FUTURE-LOCKED"):
        backend.rotate("runtime-local", "rotated-secret-9876543210abcdef")
    # the store is byte-identical after the denial
    data = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))
    assert data["postgres_password"] == "s" * 40
    assert data["worker_token"] == "w" * 40
    assert data["b4_meta"]["runtime-local"]["generation"] == 1


def test_cxr5r4_rotate_seam_requires_explicit_enable():
    _seed_initialized_store()
    with pytest.raises(RuntimeError, match="FUTURE-LOCKED"):
        ls.RuntimeSecretBackend().rotate("runtime-local", "x" * 40)
    # the seam works ONLY when explicitly enabled (test-only metadata mutation)
    ls.RuntimeSecretBackend(test_seam=True).rotate(
        "runtime-local", "seam-rotated-secret-9876543210")
    data = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))
    assert data["postgres_password"] == "seam-rotated-secret-9876543210"
    assert data["worker_token"] == "w" * 40  # unrelated entries survive


def test_cxr5r4_init_password_validation(monkeypatch):
    # 6-7 (CXR5-04): explicit init passwords validated BEFORE persistence
    # (environ dicts are passed directly — a NUL byte cannot even enter the
    # process environment on some platforms, which is itself the point)
    bad = ["", "short", "has-newline\ninjection", "has\rreturn",
           "has-nul-\x00-char-1234567890", "has-\x1b-escape-1234567890"]
    for value in bad:
        with pytest.raises((ValueError, RuntimeError)):
            ls.initialize_runtime_secret(environ={"POSTGRES_PASSWORD": value})
        assert not ls.SECRETS_FILE.exists(), value  # never persisted
    # a strength-contract password persists (via env, like the real init)
    monkeypatch.setenv("POSTGRES_PASSWORD", "valid-strong-password-1234567890")
    pw = ls.initialize_runtime_secret()
    assert pw == "valid-strong-password-1234567890"


def test_cxr5r4_special_chars_cannot_corrupt_dsn_or_compose_env(monkeypatch):
    # X: a stored password with reserved URI characters is percent-encoded in
    # the DSN (can never redirect/parse-corrupt it); compose projection
    # refuses a newline-carrying value outright.
    monkeypatch.setenv("POSTGRES_PASSWORD", "pw-with-@-slash-/-#-question-?-1234567890")
    ls.initialize_runtime_secret()
    dsn = ls.derive_runtime_dsn()
    assert "@" not in dsn.split("@", 1)[0].split(":", 2)[2]  # encoded userinfo
    assert "%40" in dsn and "%2F" in dsn  # quote_plus encoding applied
    assert dsn.startswith("postgresql://oce_control_admin:")
    # direct-crafted store with a newline -> projection fails closed (no
    # ambient value may paper over the malformed store)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    ls.SECRETS_FILE.write_text(json.dumps(
        {"postgres_password": "line1\nPOSTGRES_PASSWORD=injected"}),
        encoding="utf-8")
    with pytest.raises(ValueError, match="CR/LF"):
        ls.write_compose_env()


def test_cxr5r4_malformed_store_schema_fails_closed():
    # 13 (CXR5-04): dict/list/null values are NEVER coerced into credentials
    ls.SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    for payload in ({"postgres_password": ["not", "a", "string"]},
                    {"postgres_password": {"nested": True}},
                    {"postgres_password": None},
                    {"postgres_password": "x" * 40,
                     "b4_meta": {"runtime-local": {"generation": "one"}}},
                    {"postgres_password": "x" * 40,
                     "b4_meta": ["not", "a", "dict"]}):
        ls.SECRETS_FILE.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(RuntimeError, match="B4-CXR5R4"):
            ls.RuntimeSecretBackend().resolve("secret:runtime-local")
        with pytest.raises(RuntimeError, match="B4-CXR5R4"):
            ls._load_full_store()


def test_cxr5r4_compose_env_atomic_and_failed_projection_keeps_store(
        monkeypatch, tmp_path):
    # 10-11 (CXR5-04): compose.env is restrictive AT CREATION (no broad-write
    # + chmod window); a failed projection leaves the approved store intact.
    monkeypatch.setenv("POSTGRES_PASSWORD", "valid-strong-password-1234567890")
    ls.initialize_runtime_secret()
    before = _store_snapshot()
    ls.write_compose_env()
    if os.name != "nt":
        assert ls.COMPOSE_ENV_FILE.stat().st_mode & 0o777 == 0o600
    import os as _os

    def _boom(src, dst):
        raise OSError("projection-disk-full")

    monkeypatch.setattr(_os, "replace", _boom)
    with pytest.raises(OSError, match="projection-disk-full"):
        ls.write_compose_env()
    assert _store_snapshot() == before  # store unchanged by failed projection


def test_cxr5r4_concurrent_mutations_preserve_all_entries():
    # 12 (CXR5-04): concurrent read-modify-writes cannot erase the worker
    # token / b4_meta / unrelated entries (locked RMW)
    _seed_initialized_store()
    import threading
    backend = ls.RuntimeSecretBackend(test_seam=True)
    errors: list = []

    def _worker():
        try:
            ls.initialize_worker_token()
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def _rotator():
        try:
            backend.rotate("runtime-local", "concurrent-rotated-9876543210")
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(4)] + \
        [threading.Thread(target=_rotator) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    data = json.loads(ls.SECRETS_FILE.read_text(encoding="utf-8"))
    assert data["postgres_password"] == "concurrent-rotated-9876543210"
    assert data["worker_token"] == "w" * 40
    assert data["another_entry"] == "another-secret-value"
    assert data["b4_meta"]["runtime-local"]["generation"] >= 2


def test_cxr5r4_structured_connection_params():
    # 8 (CXR5-04): structured psycopg2 parameters — no DSN string to parse
    ls.initialize_runtime_secret()
    params = ls.runtime_connection_params()
    assert params == {"host": ls.PG_HOST, "port": ls.PG_PORT,
                      "dbname": ls.PG_DB, "user": ls.PG_USER,
                      "password": ls.read_runtime_secret()}


# --------------------------------------------------------------------------
# Ports — loopback only
# --------------------------------------------------------------------------

def test_real_compose_ports_are_loopback_only():
    assert ll.published_ports_from_compose() == []


def test_bare_port_binding_rejected(monkeypatch, tmp_path):
    fake = tmp_path / "compose.yml"
    fake.write_text('services:\n  pg:\n    ports:\n      - "5433:5432"\n')
    monkeypatch.setattr(ll, "COMPOSE_FILE", fake)
    offenders = ll.published_ports_from_compose()
    assert any("binds all interfaces" in o for o in offenders)


def test_public_bind_rejected(monkeypatch, tmp_path):
    fake = tmp_path / "compose.yml"
    fake.write_text('services:\n  pg:\n    ports:\n      - "0.0.0.0:5433:5432"\n')
    monkeypatch.setattr(ll, "COMPOSE_FILE", fake)
    assert any("does not bind 127.0.0.1" in o for o in ll.published_ports_from_compose())


# --------------------------------------------------------------------------
# PID ownership — never pkill
# --------------------------------------------------------------------------

def test_lifecycle_module_never_uses_pkill():
    src = Path(ll.__file__).read_text(encoding="utf-8")
    # B2-R7 forbids broad pkill shutdown: pkill must never appear as a
    # quoted command literal (docstring prose may explain the prohibition).
    assert not re.search(r"['\"]pkill['\"]", src), "B2-R7 forbids pkill shutdown"


def test_stop_terminates_only_pid_file_process(monkeypatch):
    proc = _spawn_sleeper()
    try:
        pid = proc.pid
        path = ll.pid_file("worker")
        path.write_text(f"{pid}\n")
        monkeypatch.setattr(ll, "PROCESSES", {"worker": ("worker.pid", "time.sleep(600)")})
        actions = ll.stop_runtime_processes()
        deadline = time.time() + 15
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.1)
        assert proc.poll() is not None, f"recorded process was not terminated; actions={actions}"
        assert not path.exists(), "pid file should be cleared"
        assert any("terminated worker" in a for a in actions), f"actions={actions}"
    finally:
        if proc.poll() is None:
            proc.kill()


def test_stale_dead_pid_cleared_not_signalled():
    # a PID that cannot be running: reuse a finished process's pid
    probe = _spawn_sleeper()
    pid = probe.pid
    probe.terminate()
    probe.wait(timeout=10)
    path = ll.pid_file("api")
    path.write_text(f"{pid}\n")
    actions = ll.stop_runtime_processes()
    assert not path.exists(), "stale pid file must be cleared"
    assert any("stale" in a for a in actions)


def test_unrelated_process_never_signalled(monkeypatch):
    proc = _spawn_sleeper()  # cmdline does NOT contain the api marker
    try:
        pid = proc.pid
        path = ll.pid_file("api")
        path.write_text(f"{pid}\n")
        actions = ll.stop_runtime_processes()
        assert proc.poll() is None, "unrelated process must never be terminated"
        assert not path.exists(), "pid file cleared as stale"
        assert any("unrelated process" in a for a in actions)
    finally:
        proc.kill()
        proc.wait(timeout=10)


def test_pid_file_with_garbage_ignored():
    path = ll.pid_file("api")
    path.write_text("not-a-pid\n")
    state, detail = ll.pid_state(path, MARKER)
    assert state == "stale"
    assert "no parseable PID" in detail


# --------------------------------------------------------------------------
# Destructive authorization
# --------------------------------------------------------------------------

def test_destroy_requires_confirmation(monkeypatch):
    monkeypatch.setattr(ll, "compose", lambda *a, **k: None)
    with pytest.raises(SystemExit, match="DESTRUCTIVE"):
        ll.destroy(confirmed=False)


def test_destroy_removes_volume_only_with_yes(monkeypatch):
    calls = []
    monkeypatch.setattr(ll, "stop_runtime_processes", lambda: [])
    monkeypatch.setattr(ll, "compose", lambda *a, **k: calls.append(a) or _FakeComp(0))
    ll.destroy(confirmed=True)
    assert ("down", "-v") in calls, "durable volume removal must use compose down -v"


class _FakeComp:
    def __init__(self, rc):
        self.returncode = rc


# --------------------------------------------------------------------------
# Start / doctor / cloud-free posture
# --------------------------------------------------------------------------

def test_start_fails_closed_without_docker(monkeypatch):
    monkeypatch.setattr(ll, "docker_available", lambda: False)
    with pytest.raises(RuntimeError, match="Docker is unavailable"):
        ll.start()


def test_cloud_credential_hint_detects_cloud_env(monkeypatch):
    assert ll.cloud_credential_hint({"PATH": "/usr/bin", "HOME": "/root"}) == []
    hint = ll.cloud_credential_hint({"AWS_ACCESS_KEY_ID": "x", "PATH": "/usr/bin"})
    assert hint == ["AWS_ACCESS_KEY_ID"]


def test_doctor_reports_cloud_free_when_clean(monkeypatch, tmp_path):
    monkeypatch.setattr(ll, "docker_available", lambda: True)
    monkeypatch.setattr(ll, "published_ports_from_compose", lambda: [])
    monkeypatch.setattr(ll, "process_cmdline", lambda pid: None)
    monkeypatch.setattr(ls, "load_runtime_secret", lambda: "x" * 40)
    monkeypatch.setattr(ls, "SECRETS_FILE", tmp_path / "secrets.json")
    ls.SECRETS_FILE.write_text(json.dumps({"postgres_password": "x" * 40}))
    import subprocess as _sp
    monkeypatch.setattr(_sp, "run", lambda *a, **k: _FakeComp(0))
    result = ll.doctor()
    cloud = [c for c in result["checks"] if c["check"] == "no cloud credentials required"]
    assert cloud and cloud[0]["ok"] is True
