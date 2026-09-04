"""OCE Book 4 — B4-CXR7U4 atomic, fail-closed handoff consumption.

The split is_capability_consumed() / mark_capability_consumed() pair let the
check and the consume run under different locks and silently treated corrupt
persisted state as an empty ledger. consume_handoff_once(nonce, metadata) is
ONE exclusive-locked operation:

  authenticate/verify (caller) -> ONE exclusive lock -> load + validate UNDER
  the lock -> reject existing nonce -> append + atomic commit -> runtime
  activity only after successful commit.

Exactly one concurrent consumer may succeed. Corrupt / unreadable /
wrong-schema / symlinked / weak-permission ledger state fails closed with
the previous ledger preserved byte-for-byte — never rewritten, never reset,
never treated as empty.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

import pytest

from oce_control import local_secrets as ls


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path)
    # consumed_nonces_file() derives from RUNTIME_DIR
    yield


def _ledger_path() -> Path:
    return ls.consumed_nonces_file()


def _write_ledger(data) -> None:
    p = _ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, (str, bytes)):
        p.write_text(data, encoding="utf-8")
    else:
        p.write_text(json.dumps(data), encoding="utf-8")


class TestConsumeHandoffOnce:
    def test_first_consumer_succeeds(self):
        assert ls.consume_handoff_once("n" * 32) is True
        assert ls.is_capability_consumed("n" * 32)

    def test_sequential_replay_denied(self):
        assert ls.consume_handoff_once("r" * 32) is True
        assert ls.consume_handoff_once("r" * 32) is False

    def test_two_simultaneous_consumers_exactly_one_succeeds(self):
        barrier = threading.Barrier(8)
        results: list[bool] = []
        lock = threading.Lock()

        def worker():
            barrier.wait()
            ok = ls.consume_handoff_once("c" * 32, metadata={"role": "api"})
            with lock:
                results.append(ok)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(30)
        assert sum(1 for r in results if r is True) == 1
        assert sum(1 for r in results if r is False) == 7

    def test_metadata_recorded_non_secret(self):
        ls.consume_handoff_once("m" * 32, metadata={"role": "worker"})
        raw = json.loads(_ledger_path().read_text(encoding="utf-8"))
        assert raw["m" * 32]["m"] == "worker"
        assert raw["m" * 32]["t"] <= time.time()

    def test_ledger_has_canonical_schema_after_consume(self):
        ls.consume_handoff_once("s" * 32)
        data = json.loads(_ledger_path().read_text(encoding="utf-8"))
        assert isinstance(data["s" * 32], dict)
        assert isinstance(data["s" * 32]["t"], (int, float))


class TestFailClosedLedger:
    def test_corrupt_json_denied_without_rewrite(self):
        _write_ledger("{corrupt json not valid")
        before = _ledger_path().read_bytes()
        with pytest.raises(ls.LedgerCorrupt, match="corrupt JSON"):
            ls.consume_handoff_once("x" * 32)
        assert _ledger_path().read_bytes() == before  # no rewrite

    def test_wrong_schema_denied(self):
        _write_ledger({"nonce": ["not", "a", "number", "or", "dict"]})
        before = _ledger_path().read_bytes()
        with pytest.raises(ls.LedgerCorrupt, match="schema invalid"):
            ls.consume_handoff_once("y" * 32)
        assert _ledger_path().read_bytes() == before

    def test_top_level_list_denied(self):
        _write_ledger(["not", "an", "object"])
        with pytest.raises(ls.LedgerCorrupt, match="JSON object"):
            ls.consume_handoff_once("z" * 32)

    def test_entry_missing_timestamp_denied(self):
        _write_ledger({"a" * 32: {"no_timestamp": True}})
        with pytest.raises(ls.LedgerCorrupt, match="'t' must"):
            ls.consume_handoff_once("b" * 32)

    def test_unreadable_ledger_denied(self, monkeypatch):
        p = _ledger_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}", encoding="utf-8")
        # simulate unreadable state (permissions/IO) via read_text failure
        import unittest.mock as mock
        with mock.patch.object(Path, "read_text",
                               side_effect=OSError("permission denied")):
            with pytest.raises(ls.LedgerCorrupt, match="unreadable"):
                ls.consume_handoff_once("u" * 32)

    def test_legacy_epoch_entries_honored_not_erased(self):
        # pre-U4 schema entries are canonical re-derivations: honored as
        # their consumption timestamp and never erased while inside the
        # retention window (a STALE legacy entry legitimately prunes —
        # its handoff long expired)
        recent_legacy = time.time() - 60
        _write_ledger({"legacy" + "e" * 25: recent_legacy})
        assert ls.is_capability_consumed("legacy" + "e" * 25) is True
        # a fresh consume preserves the in-window legacy entry
        assert ls.consume_handoff_once("new" + "n" * 29) is True
        data = json.loads(_ledger_path().read_text(encoding="utf-8"))
        assert "legacy" + "e" * 25 in data

    def test_failed_replacement_preserves_complete_previous_ledger(
            self, monkeypatch):
        _write_ledger({"keep" + "k" * 28: {"t": time.time()}})
        before = _ledger_path().read_bytes()
        import unittest.mock as mock
        real_replace = os.replace

        def failing_replace(src, dst, *a, **kw):
            if str(dst) == str(_ledger_path()):
                raise OSError("simulated commit failure")
            return real_replace(src, dst, *a, **kw)

        with mock.patch.object(os, "replace", side_effect=failing_replace):
            with pytest.raises(ls.LedgerUnwritable, match="preserved"):
                ls.consume_handoff_once("f" * 32)
        assert _ledger_path().read_bytes() == before
        # and the nonce was NOT recorded
        assert ls.is_capability_consumed("f" * 32) is False

    def test_symlink_substitution_denied(self, tmp_path):
        # symlink refused only when the ledger already exists as a symlink
        target = tmp_path / "elsewhere.json"
        target.write_text("{}", encoding="utf-8")
        p = _ledger_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            p.symlink_to(target)
        except OSError:
            pytest.skip("symlinks unavailable on this platform")
        before = p.read_bytes() if not p.is_symlink() else b""
        with pytest.raises((ls.LedgerCorrupt, OSError)):
            ls.consume_handoff_once("l" * 32)
        # target untouched
        assert target.read_text(encoding="utf-8") == "{}"

    @pytest.mark.skipif(os.name == "nt", reason="POSIX permission enforcement")
    def test_weak_permissions_denied_where_enforceable(self):
        p = _ledger_path()
        _write_ledger({})
        p.chmod(0o666)  # group/world writable
        before = p.read_bytes()
        with pytest.raises(ls.LedgerCorrupt, match="weak permissions"):
            ls.consume_handoff_once("w" * 32)
        assert p.read_bytes() == before

    def test_pruning_cannot_reopen_a_valid_replay_window(self):
        # entries within the 24h retention floor are never pruned; the
        # capability TTL (900s) is far inside that floor
        recent = time.time() - (ls.CAPABILITY_TTL_SECONDS + 5)
        _write_ledger({"recent" + "r" * 26: {"t": recent}})
        assert ls.consume_handoff_once("fresh" + "f" * 27) is True
        data = json.loads(_ledger_path().read_text(encoding="utf-8"))
        assert "recent" + "r" * 26 in data  # still guarded
        assert ls.is_capability_consumed("recent" + "r" * 26) is True

    def test_malformed_nonce_refused(self):
        for bad in ("", None, 42):
            with pytest.raises(RuntimeError, match="malformed"):
                ls.consume_handoff_once(bad)  # type: ignore[arg-type]


class TestVerificationIntegration:
    """The verification path consumes atomically after full verification."""

    def _setup_ctx(self, tmp_path, monkeypatch):
        from oce_control import config_startup as cs
        store = tmp_path / "secrets.json"
        store.write_text(json.dumps({"postgres_password": "k" * 40}),
                         encoding="utf-8")
        monkeypatch.setattr(ls, "SECRETS_FILE", store)
        monkeypatch.setattr(ls, "RUNTIME_DIR", tmp_path)
        ls.initialize_activation_handoff_key()
        backend = ls.RuntimeSecretBackend(store, test_seam=True)
        ctx = cs.create_activation_context(environ={"PATH": "/usr/bin:/bin"},
                                           backend=backend)
        return ctx, backend

    def test_verified_child_consumes_once_and_replay_denied(
            self, tmp_path, monkeypatch):
        from oce_control import config_startup as cs
        ctx, backend = self._setup_ctx(tmp_path, monkeypatch)
        env = ctx.child_environment(child_role="api")
        child = cs.create_activation_context(
            environ=env, backend=backend, role="api")
        assert type(child).__name__ == "VerifiedChildContext"
        with pytest.raises(SystemExit, match="already consumed"):
            cs.create_activation_context(environ=env, backend=backend,
                                         role="api")

    def test_forged_handoff_leaves_ledger_unchanged(
            self, tmp_path, monkeypatch):
        from oce_control import config_startup as cs
        ctx, backend = self._setup_ctx(tmp_path, monkeypatch)
        env = ctx.child_environment(child_role="api")
        env["OCE_ACTIVATION_ENVELOPE"] = "{not json"
        before = _ledger_snapshot()
        with pytest.raises(SystemExit, match="malformed"):
            cs.create_activation_context(environ=env, backend=backend,
                                         role="api")
        assert _ledger_snapshot() == before

    def test_wrong_audience_leaves_ledger_unchanged(
            self, tmp_path, monkeypatch):
        from oce_control import config_startup as cs
        ctx, backend = self._setup_ctx(tmp_path, monkeypatch)
        env = ctx.child_environment(child_role="api")
        before = _ledger_snapshot()
        with pytest.raises(SystemExit, match="role-bound"):
            cs.create_activation_context(environ=env, backend=backend,
                                         role="worker")
        assert _ledger_snapshot() == before

    def test_corrupt_ledger_denies_activation_without_rewrite(
            self, tmp_path, monkeypatch):
        from oce_control import config_startup as cs
        ctx, backend = self._setup_ctx(tmp_path, monkeypatch)
        env = ctx.child_environment(child_role="api")
        _write_ledger("{broken ledger")
        before = _ledger_path().read_bytes()
        with pytest.raises(SystemExit, match="B4-CXR7U4"):
            cs.create_activation_context(environ=env, backend=backend,
                                         role="api")
        assert _ledger_path().read_bytes() == before


def _ledger_snapshot() -> bytes | None:
    p = _ledger_path()
    return p.read_bytes() if p.exists() else None
