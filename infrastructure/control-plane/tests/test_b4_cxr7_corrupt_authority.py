"""OCE Book 4 — B4-CXR7U8-05 corrupt secret authority byte-invariance.

The canonical threat model states corrupt persisted security state must FAIL
CLOSED and never behave like empty state. These proofs drive every
initialization, runtime, and mutation path against each corrupt/wrong-schema
store shape and assert:

* a typed SecretStoreCorrupt / SecretStoreUnreadable failure (never {} /
  None / silent reset);
* store bytes BEFORE == AFTER for every entrypoint;
* no compose, no database mutation, no process launch, no projection
  rewrite, no new authority file.

Missing file MAY mean uninitialized; an EXISTING unreadable/invalid/non-
object/wrong-schema store is CORRUPTION and is never overwritten by a denied
or failed operation.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

import oce_control.local_secrets as ls
import oce_control.local_lifecycle as ll

CORRUPT_STORES = {
    "invalid-json": b"{corrupt-not-json",
    "non-object": b'["not", "a", "dict"]',
    "list-value": json.dumps({"postgres_password": ["x", "y"]}).encode(),
    "int-value": json.dumps({"postgres_password": 42}).encode(),
    "null-value": json.dumps({"postgres_password": None}).encode(),
    "empty-password": json.dumps({"postgres_password": ""}).encode(),
    "bad-meta": json.dumps({
        "postgres_password": "s" * 40,
        "b4_meta": {"runtime-local": {"generation": "one"}},
    }).encode(),
}
# NOTE: a type-valid store missing the postgres_password KEY is INCOMPLETE,
# not corrupt — the runtime treats it as missing material (load_runtime_secret
# -> None, start blocked with a `configure` hint, init refused). Its
# fail-closed behavior is covered by the existing "missing material" tests.


@pytest.fixture
def corrupt_runtime(monkeypatch, tmp_path):
    """Point the runtime at an isolated tmp store seeded with corrupt bytes."""
    rt = tmp_path / "runtime"
    rt.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ls, "RUNTIME_DIR", rt)
    monkeypatch.setattr(ls, "SECRETS_FILE", rt / "secrets.json")
    monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", rt / "compose.env")
    monkeypatch.setattr(ls, "LOGS_DIR", rt / "logs")

    calls = {"compose": [], "migrate": [], "start_process": []}

    def _spy_compose(*args, **kwargs):
        calls["compose"].append(args)
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    def _spy_migrate(*args, **kwargs):
        calls["migrate"].append(args)
        return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    def _spy_start_process(*args, **kwargs):
        calls["start_process"].append(args)

    # configure preflight parses the repo compose file statically; force the
    # loopback-only posture so the corrupt-store denial point is deterministic.
    monkeypatch.setattr(ll, "published_ports_from_compose", lambda: [])
    monkeypatch.setattr(ll, "docker_available", lambda: False)
    monkeypatch.setattr(ll, "compose", _spy_compose)
    monkeypatch.setattr(ll, "migrate", _spy_migrate)
    monkeypatch.setattr(ll, "start_process", _spy_start_process)
    # clean minimal env: a stray OCE_* in the test host env must never reach
    # the effective-config validation of the entrypoints under test.
    monkeypatch.setattr(os, "environ", {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    })
    return rt, calls


def _snapshot(rt: Path) -> dict:
    out = {}
    for p in sorted(rt.iterdir()):
        if p.is_file():
            out[p.name] = p.read_bytes()
    return out


def _authority_bytes(rt: Path) -> tuple:
    return (
        (rt / "secrets.json").read_bytes() if (rt / "secrets.json").exists() else None,
        (rt / "compose.env").read_bytes() if (rt / "compose.env").exists() else None,
        (rt / "activation_handoff_key").read_bytes()
        if (rt / "activation_handoff_key").exists() else None,
    )


def _seed(rt: Path, variant: str) -> bytes:
    payload = CORRUPT_STORES[variant]
    (rt / "secrets.json").write_bytes(payload)
    return payload


# --------------------------------------------------------------------------- #
# 1. loaders + initialization + backend mutations raise typed failures and
#    never touch the corrupt bytes
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("variant", sorted(CORRUPT_STORES))
def test_u8_loaders_and_mutations_fail_closed(corrupt_runtime, variant):
    rt, _calls = corrupt_runtime
    payload = _seed(rt, variant)
    before = _authority_bytes(rt)

    with pytest.raises(ls.SecretStoreCorrupt):
        ls._load_full_store()
    with pytest.raises(ls.SecretStoreCorrupt):
        ls.load_runtime_secret()
    with pytest.raises(ls.SecretStoreCorrupt):
        ls.read_runtime_secret()
    with pytest.raises(ls.SecretStoreCorrupt):
        ls.initialize_runtime_secret()

    backend = ls.RuntimeSecretBackend(rt / "secrets.json", test_seam=True)
    with pytest.raises(ls.SecretStoreCorrupt):
        backend.resolve("secret:runtime-local")
    with pytest.raises(ls.SecretStoreCorrupt):
        backend.generation("runtime-local")
    with pytest.raises(ls.SecretStoreCorrupt):
        backend.revoke("runtime-local")
    with pytest.raises(ls.SecretStoreCorrupt):
        backend.rotate("runtime-local", "gen-2-secret-value-1234567890")

    # every corrupt shape is refused by the token init too — an existing
    # corrupt store is never rewritten with only a token
    with pytest.raises(ls.SecretStoreCorrupt):
        ls.initialize_worker_token()

    assert _authority_bytes(rt) == before
    assert (rt / "secrets.json").read_bytes() == payload
    assert not (rt / "compose.env").exists()
    assert not (rt / "activation_handoff_key").exists()


@pytest.mark.parametrize("variant", sorted(CORRUPT_STORES))
def test_u8_configure_fails_closed_byte_invariant(corrupt_runtime, variant):
    rt, calls = corrupt_runtime
    payload = _seed(rt, variant)
    files_before = _snapshot(rt)
    with pytest.raises(ls.SecretStoreCorrupt):
        ll.configure()
    # corrupt authority never rewritten; no projection, no marker
    assert (rt / "secrets.json").read_bytes() == payload
    assert not (rt / "compose.env").exists()
    assert not (rt / "activation_handoff_key").exists()
    assert not (rt / "configure.committed").exists()
    assert not (rt / "configure_journal.json").exists()
    # no compose / migration / process launch occurred
    assert calls["compose"] == []
    assert calls["migrate"] == []
    assert calls["start_process"] == []
    # the only permitted new file is the whole-configure lock
    assert set(_snapshot(rt)) - set(files_before) <= {"configure.lock"}


@pytest.mark.parametrize("variant", sorted(CORRUPT_STORES))
def test_u8_start_restart_recover_fail_closed_byte_invariant(
        corrupt_runtime, variant):
    rt, calls = corrupt_runtime
    payload = _seed(rt, variant)
    before = _authority_bytes(rt)

    with pytest.raises(ls.SecretStoreCorrupt):
        ll.start()
    assert _authority_bytes(rt) == before

    # restart: the material gate runs BEFORE stop()/compose down
    rc = ll.main(["restart"])
    assert rc == 1
    assert calls["compose"] == []
    assert _authority_bytes(rt) == before

    with pytest.raises(ls.SecretStoreCorrupt):
        ll.recover()
    assert _authority_bytes(rt) == before

    assert calls["migrate"] == []
    assert calls["start_process"] == []
    assert (rt / "secrets.json").read_bytes() == payload


# --------------------------------------------------------------------------- #
# 2. existing-but-unreadable store -> SecretStoreUnreadable (POSIX only:
#    Windows ACLs do not map to chmod, so the read succeeds there)
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(sys.platform.startswith("win"),
                    reason="POSIX chmod-000 read denial not enforceable on Windows")
def test_u8_unreadable_store_fails_closed(corrupt_runtime):
    rt, calls = corrupt_runtime
    (rt / "secrets.json").write_bytes(json.dumps({
        "postgres_password": "s" * 40}).encode())
    before = _authority_bytes(rt)
    (rt / "secrets.json").chmod(0)

    with pytest.raises(ls.SecretStoreUnreadable):
        ls.load_runtime_secret()
    with pytest.raises(ls.SecretStoreUnreadable):
        ls.initialize_runtime_secret()
    with pytest.raises(ls.SecretStoreUnreadable):
        ls.initialize_worker_token()
    with pytest.raises(ls.SecretStoreUnreadable):
        ll.configure()

    (rt / "secrets.json").chmod(0o600)
    assert _authority_bytes(rt) == before
    assert calls["compose"] == []


# --------------------------------------------------------------------------- #
# 3. missing file is UNINITIALIZED (None / {}), never corruption — and the
#    runtime read paths stay read-only over an absent store
# --------------------------------------------------------------------------- #
def test_u8_missing_store_is_uninitialized_not_corrupt(corrupt_runtime):
    rt, calls = corrupt_runtime
    assert ls.load_runtime_secret() is None
    assert ls._load_full_store() == {}
    assert ls.RuntimeSecretBackend(rt / "secrets.json")._load() == {}
    # a first explicit init materializes the store normally
    pw = ls.initialize_runtime_secret()
    assert pw and len(pw) >= 32
    assert ls.load_runtime_secret() == pw
    assert calls["compose"] == []


# --------------------------------------------------------------------------- #
# 4. doctor() reports a corrupt store as a FAILING check (no crash, no lie)
# --------------------------------------------------------------------------- #
def test_u8_doctor_reports_corrupt_store(corrupt_runtime, monkeypatch, capsys):
    rt, _calls = corrupt_runtime
    _seed(rt, "invalid-json")

    class _R:
        returncode = 1
        stdout = ""
        stderr = ""

    # the durable-volume probe shells out to docker — stub the subprocess
    # surface so the corrupt-store report is the only outcome
    monkeypatch.setattr(ll.subprocess, "run", lambda *a, **k: _R())
    rc = ll.main(["doctor"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "CORRUPT store" in out
    assert (rt / "secrets.json").read_bytes() == CORRUPT_STORES["invalid-json"]
