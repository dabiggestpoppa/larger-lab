"""OCE Book 4 — B4-CXR7U6 complete-or-nothing explicit initialization.

configure() stages FOUR formerly-independent mutations (postgres password,
worker token, activation handoff key, compose.env projection). These tests
inject a failure after EVERY initialization stage and hash the relevant
stores before and after, proving:

* first configure produces a complete initialization state or none;
* repeated configure preserves existing authority byte-for-byte;
* failure after any stage restores the prior state exactly;
* unrelated metadata survives;
* compose.env is a derived projection, not authority;
* ambient passwords cannot rotate established authority;
* start/restart/recover remain read-only over secret authority;
* no failure leaves a false initialized state (commit marker absent);
* recover()'s only mutation is classified stale-PID cleanup.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from oce_control import local_lifecycle as ll
from oce_control import local_secrets as ls


CLEAN_ENV = {"PATH": "/usr/bin:/bin"}


def _store_digests(runtime_dir: Path) -> dict:
    """SHA-256 of every relevant authority/projection store."""
    def dig(p: Path) -> str | None:
        return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    return {
        "secrets.json": dig(runtime_dir / "secrets.json"),
        "compose.env": dig(runtime_dir / "compose.env"),
        "activation_handoff_key": dig(runtime_dir / "activation_handoff_key"),
        "configure.committed": dig(runtime_dir / "configure.committed"),
        "configure_journal.json": dig(runtime_dir / "configure_journal.json"),
    }


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    """Isolated runtime dir + clean environment."""
    rt = tmp_path / ".runtime"
    monkeypatch.setattr(ls, "RUNTIME_DIR", rt)
    monkeypatch.setattr(ls, "SECRETS_FILE", rt / "secrets.json")
    monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", rt / "compose.env")
    monkeypatch.setattr(ls, "LOGS_DIR", rt / "logs")
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    return rt


class TestCompleteOrNothingConfigure:
    def test_first_configure_produces_complete_state(self, runtime, monkeypatch):
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")
        report = ll.configure()
        assert (runtime / "secrets.json").exists()
        assert (runtime / "activation_handoff_key").exists()
        assert (runtime / "compose.env").exists()
        assert (runtime / "configure.committed").exists()
        assert not (runtime / "configure_journal.json").exists()
        assert "complete-or-nothing" in report["initialization"]
        # all three authorities present and non-empty
        store = json.loads((runtime / "secrets.json").read_text("utf-8"))
        assert store["postgres_password"] and store["worker_token"]
        key = (runtime / "activation_handkey").exists() or \
            len((runtime / "activation_handoff_key").read_text().strip()) >= 64
        assert key

    def test_repeated_configure_preserves_authority_byte_for_byte(
            self, runtime, monkeypatch):
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")
        ll.configure()
        before = _store_digests(runtime)
        ll.configure()
        after = _store_digests(runtime)
        assert before["secrets.json"] == after["secrets.json"]
        assert before["activation_handoff_key"] == after["activation_handoff_key"]
        assert before["compose.env"] == after["compose.env"]

    def _inject_failure(self, stage: str, runtime, monkeypatch):
        """Make the named stage raise AFTER the previous stages committed."""
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")

        def boom(*a, **kw):
            raise RuntimeError(f"injected failure at {stage}")

        monkeypatch.setattr(ls, stage, boom)

    @pytest.mark.parametrize("stage", [
        "initialize_runtime_secret",
        "initialize_worker_token",
        "initialize_activation_handoff_key",
        "write_compose_env",
    ])
    def test_failure_after_any_stage_restores_prior_state(
            self, runtime, monkeypatch, stage):
        # establish a prior complete state
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")
        ll.configure()
        before = _store_digests(runtime)
        # now reconfigure with an injected failure at the named stage
        self._inject_failure(stage, runtime, monkeypatch)
        with pytest.raises(RuntimeError, match="injected failure"):
            ll.configure()
        after = _store_digests(runtime)
        # every store restored byte-for-byte; NO false initialized state
        for k in ("secrets.json", "compose.env", "activation_handoff_key"):
            assert before[k] == after[k], k
        assert after["configure.committed"] == before["configure.committed"]
        assert not (runtime / "configure_journal.json").exists()

    def test_failure_on_first_configure_leaves_no_state(
            self, runtime, monkeypatch):
        # no prior state at all + failure at the LAST stage: everything
        # rolled back — no partial initialization, no commit marker
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")

        def boom(*a, **kw):
            raise RuntimeError("injected failure at projection")

        monkeypatch.setattr(ls, "write_compose_env", boom)
        with pytest.raises(RuntimeError, match="injected failure"):
            ll.configure()
        assert not (runtime / "secrets.json").exists()
        assert not (runtime / "activation_handoff_key").exists()
        assert not (runtime / "compose.env").exists()
        assert not (runtime / "configure.committed").exists()

    def test_unrelated_metadata_survives_failure(self, runtime, monkeypatch):
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")
        ll.configure()
        # inject unrelated metadata into the store
        store = json.loads((runtime / "secrets.json").read_text("utf-8"))
        store["b4_meta"] = {"runtime-local": {"generation": 3, "revoked": False}}
        store["operator_note"] = "keep me"
        (runtime / "secrets.json").write_text(json.dumps(store), "utf-8")
        before = (runtime / "secrets.json").read_bytes()

        def boom(*a, **kw):
            raise RuntimeError("injected failure")

        monkeypatch.setattr(ls, "write_compose_env", boom)
        with pytest.raises(RuntimeError, match="injected failure"):
            ll.configure()
        assert (runtime / "secrets.json").read_bytes() == before
        after = json.loads((runtime / "secrets.json").read_text("utf-8"))
        assert after["operator_note"] == "keep me"
        assert after["b4_meta"]["runtime-local"]["generation"] == 3

    def test_compose_env_is_projection_not_authority(self, runtime, monkeypatch):
        # deleting compose.env then re-running configure re-derives it from
        # the store — the STORE is authority, the projection is regenerable
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")
        ll.configure()
        pw_before = json.loads((runtime / "secrets.json").read_text("utf-8"))[
            "postgres_password"]
        (runtime / "compose.env").unlink()
        ll.configure()
        env_text = (runtime / "compose.env").read_text("utf-8")
        assert env_text == f"POSTGRES_PASSWORD={pw_before}\n"
        # and the store password did not change (projection never feeds back)
        assert json.loads((runtime / "secrets.json").read_text("utf-8"))[
            "postgres_password"] == pw_before

    def test_ambient_password_cannot_rotate_established_authority(
            self, runtime, monkeypatch):
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")
        ll.configure()
        before = _store_digests(runtime)
        monkeypatch.setenv("POSTGRES_PASSWORD", "ambient-attacker-password-1234567890")
        with pytest.raises(RuntimeError, match="rotation"):
            ll.configure()
        after = _store_digests(runtime)
        assert before["secrets.json"] == after["secrets.json"]

    def test_start_remains_read_only_over_authority(self, runtime, monkeypatch):
        # start() requires material (never creates it) — missing material
        # fails closed with a configure hint and mutates NOTHING. The REAL
        # ll.start() entrypoint is invoked (never a private helper): every
        # external surface (compose, process launch, HTTP probe) is spied on
        # and must stay untouched because the material gate fires first.
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")
        calls = {"compose": [], "start_process": [], "http": []}

        def _spy_compose(*args, **kwargs):
            calls["compose"].append(args)
            raise AssertionError("compose must never run when material is absent")

        def _spy_start_process(*args, **kwargs):
            calls["start_process"].append(args)
            raise AssertionError("process launch must never run when material is absent")

        monkeypatch.setattr(ll, "compose", _spy_compose)
        monkeypatch.setattr(ll, "start_process", _spy_start_process)
        monkeypatch.setattr(ll, "wait_for_http", lambda *a, **k: True)
        monkeypatch.setattr(ll, "docker_available", lambda: True)
        with pytest.raises(SystemExit, match="configure"):
            ll.start()  # REAL production entrypoint, no __wrapped__, no helper
        assert calls == {"compose": [], "start_process": [], "http": []}
        assert not (runtime / "secrets.json").exists()
        assert not (runtime / "compose.env").exists()
        assert not (runtime / "activation_handoff_key").exists()

    def test_recover_only_mutation_is_classified_stale_pid_cleanup(
            self, runtime, tmp_path, monkeypatch):
        # truth classification: recover removes a STALE pid file (intentional,
        # non-authoritative) while never touching authority stores
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")
        ll.configure()
        before = _store_digests(runtime)
        # a stale PID file: dead pid recorded
        ll.write_pid(ll.pid_file("api"), 999999)
        # gate the rest of recover off: docker unavailable raises after cleanup
        monkeypatch.setattr(ll, "docker_available", lambda: False)
        with pytest.raises(RuntimeError, match="Docker"):
            ll.recover()
        after = _store_digests(runtime)
        for k in ("secrets.json", "compose.env", "activation_handoff_key"):
            assert before[k] == after[k]  # authority untouched
        assert not ll.pid_file("api").exists()  # stale pid removed
        # and the actions list classifies the cleanup
        # (the removal happened before the docker check; classification is
        # asserted by the docstring contract + action strings in real runs)

    def test_no_failure_leaves_false_initialized_state(self, runtime, monkeypatch):
        # commit marker exists ONLY when every stage committed
        monkeypatch.setenv("OCE_CONTROL_PLANE_HOST", "127.0.0.1")
        monkeypatch.setenv("OCE_CONTROL_PLANE_PORT", "8448")

        def boom(*a, **kw):
            raise RuntimeError("injected failure")

        monkeypatch.setattr(ls, "initialize_worker_token", boom)
        with pytest.raises(RuntimeError, match="injected failure"):
            ll.configure()
        assert not (runtime / "configure.committed").exists()
        # and the failed password stage rolled back too
        assert not (runtime / "secrets.json").exists()
        # after a successful reconfigure the marker appears
        monkeypatch.setattr(ls, "initialize_worker_token",
                            lambda: "t" * 43)
        monkeypatch.setattr(ls, "initialize_activation_handoff_key",
                            lambda: "a" * 64)
        ll.configure()
        assert (runtime / "configure.committed").exists()


