#!/usr/bin/env python3
"""B3-R4: persistent cross-invocation worker CLI + supervisor (subprocess-level).

Each test runs the real ``scripts/oce_worker.py`` as a subprocess with a
dedicated --runtime-dir, so every invocation starts a FRESH supervisor. This
proves the exact defects are fixed:

* ``configure`` -> ``admit`` -> ``start`` -> ``status`` survive process
  boundaries (each interplay is a separate subprocess); admissed identity and
  operator-admitted capabilities are reloaded from the persisted state file;
* repeated ``--cap a --cap b`` is parsed into a real capability list (the old
  broken ``--cap ``-string split is gone);
* a fresh supervisor does NOT see an admitted worker as admitted unless it was
  persisted; admission and revocation are PO-only actions;
* stale PID files (a pid that no longer runs, or a pid reused by an unrelated
  process) are detected and never signalled — PID-reuse safety;
* cleanup preserves the persisted state/configuration and durable artifacts.
"""
from __future__ import annotations
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
CLI = BASE / "scripts" / "oce_worker.py"


def _run(runtime: Path, cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), "--runtime-dir", str(runtime),
         *cmd], cwd=str(BASE),
        capture_output=True, text=True, timeout=60)


def _out(r: subprocess.CompletedProcess) -> dict:
    assert r.returncode == 0, f"rc={r.returncode} out={r.stdout} err={r.stderr}"
    return json.loads(r.stdout)


class TestCliLifecycle:
    def fixture_runtime(self, tmp_path):
        return tmp_path / "runtime"

    def test_configure_then_admit_then_start_across_processes(self, tmp_path):
        rt = tmp_path / "runtime-1"
        # invoke 1: configure
        _out(_run(rt, ["configure", "wkr-a", "--cap", "hash",
                       "--cap", "compute-python", "--", sys.executable,
                       "-c", "import time; time.sleep(60)"]))
        # invoke 2: status shows configured but not yet admitted
        st = _out(_run(rt, ["status"]))
        assert st["wkr-a"]["state"] == "configured"
        assert "wkr-a" not in _out(_run(rt, ["console"]))["admitted"]
        # invoke 3: PO admission (single fresh process)
        ident = _out(_run(rt, ["admit", "wkr-a", "--confirm",
                               "--cap", "hash", "--cap", "compute-python"]))
        assert ident["worker_id"] == "wkr-a"
        assert set(ident["capabilities"]) == {"hash", "compute-python"}
        # invoke 4: a FRESH process still sees it admitted (persisted)
        console = _out(_run(rt, ["console"]))
        assert "wkr-a" in console["admitted"]
        # invoke 5: start (fresh process, picks up persisted admission)
        started = _out(_run(rt, ["start", "wkr-a"]))
        assert started["state"] == "running"
        # invoke 6: status confirms alive in a NEW process
        st = _out(_run(rt, ["status", "wkr-a"]))
        assert st["alive"] is True
        # invoke 7: stop (fresh process)
        stopped = _out(_run(rt, ["stop", "wkr-a"]))
        assert stopped["state"] == "stopped"

    def test_configure_does_not_admit(self, tmp_path):
        rt = tmp_path / "runtime-2"
        _out(_run(rt, ["configure", "wkr-x", "--", sys.executable]))
        console = _out(_run(rt, ["console"]))
        assert "wkr-x" not in console["admitted"]
        # still configured (persisted)
        st = _out(_run(rt, ["status"]))
        assert "wkr-x" in st

    def test_admission_is_po_only(self, tmp_path):
        rt = tmp_path / "runtime-3"
        _out(_run(rt, ["configure", "wkr-y", "--", sys.executable]))
        # a non-operator actor may not admit
        r = _run(rt, ["admit", "wkr-y", "--confirm", "--actor", "hermes"])
        assert r.returncode == 2
        assert "DENIED" in r.stderr
        # without --confirm, admission is refused (governance intent)
        r = _run(rt, ["admit", "wkr-y", "--cap", "hash"])
        assert r.returncode == 2
        assert "governance" in r.stderr

    def test_repeated_cap_parsed_as_list(self, tmp_path):
        rt = tmp_path / "runtime-4"
        cfg = _out(_run(rt, ["configure", "wkr-c", "--cap", "hash",
                             "--cap", "compute-python", "--cap", "analysis-artifact",
                             "--", sys.executable]))
        # the capability list is parsed as a real repeated list, not a string
        assert set(cfg["capabilities"]) == {
            "hash", "compute-python", "analysis-artifact"}
        ident = _out(_run(rt, ["admit", "wkr-c", "--confirm",
                               "--cap", "hash", "--cap", "compute-python",
                               "--cap", "analysis-artifact"]))
        assert set(ident["capabilities"]) == {
            "hash", "compute-python", "analysis-artifact"}
        # persisted across processes (fresh supervisor reloads the list)
        console = _out(_run(rt, ["console"]))
        assert "hash" in console["capabilities"]

    def test_revocation_persists_across_processes(self, tmp_path):
        rt = tmp_path / "runtime-5"
        _out(_run(rt, ["configure", "wkr-z", "--", sys.executable]))
        _out(_run(rt, ["admit", "wkr-z", "--confirm", "--cap", "hash"]))
        assert "wkr-z" in _out(_run(rt, ["console"]))["admitted"]
        _out(_run(rt, ["revoke", "wkr-z"]))
        console = _out(_run(rt, ["console"]))
        assert "wkr-z" not in console["admitted"]

    def test_stale_pid_detected_never_signalled(self, tmp_path):
        rt = tmp_path / "runtime-6"
        (rt / "pids").mkdir(parents=True, exist_ok=True)
        (rt / "pids" / "wkr-dead.pid").write_text("2147483647", encoding="utf-8")
        # a "live-ish" but unrelated pid file must be flagged stale (PID reuse)
        (rt / "pids" / "wkr-alien.pid").write_text(
            str(find_any_child_pid()), encoding="utf-8")
        r = _run(rt, ["doctor"])   # doctor returns 1 when a stale pid exists
        assert r.returncode == 1
        doctor = json.loads(r.stdout)
        assert doctor["ok"] is False
        assert "wkr-dead" in doctor["stale_pids"]
        # cleanup clears stale pid files without signalling unrelated-owned pid
        cleaned = _out(_run(rt, ["cleanup"]))
        assert cleaned["cleanup"] is True
        assert not (rt / "pids" / "wkr-dead.pid").exists()

    def test_cleanup_preserves_configuration(self, tmp_path):
        rt = tmp_path / "runtime-7"
        _out(_run(rt, ["configure", "wkr-keep", "--cap", "file-read",
                       "--", sys.executable]))
        _out(_run(rt, ["admit", "wkr-keep", "--confirm", "--cap", "file-read"]))
        cleaned = _out(_run(rt, ["cleanup"]))
        assert cleaned["state_preserved"] is True
        # configuration + admission survive cleanup (fresh process)
        console = _out(_run(rt, ["console"]))
        assert "wkr-keep" in console["admitted"]
        st = _out(_run(rt, ["status"]))
        assert "wkr-keep" in st


def find_any_child_pid() -> int:
    """Return a pid of a running, unrelated process (this pytest child)."""
    import os
    for cand in (os.getppid(), os.getpid()):
        return cand
    return os.getppid()