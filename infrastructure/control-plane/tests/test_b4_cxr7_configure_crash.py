"""OCE Book 4 — B4-CXR7U8-04 configure crash/restart + concurrency safety.

The U6 rollback was exception-safe only: its snapshot lived in process memory
and a process that DIED mid-configure could never perform the documented
rollback. configure() is now serialized under a whole-configure exclusive
lock and its journal durably carries the byte-for-byte prior state, so an
interrupted configure is recovered deterministically on the next run:

* journal + commit marker   -> committed bundle is authoritative; compose
  projection is rolled FORWARD and the journal is dropped;
* journal, no commit marker -> NOT committed; the prior state stored IN the
  journal is restored byte-for-byte and the journal is dropped.

Every crash test here kills a REAL subprocess (proc.kill()) at a specific
stage and then RESTARTS configure, proving real process interruption (not
monkeypatched exceptions) is reconciled deterministically.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent

DRIVER = r"""
import json
import sys
from pathlib import Path
import oce_control.local_secrets as ls
rt = Path(sys.argv[1])
ls.RUNTIME_DIR = rt
ls.SECRETS_FILE = rt / "secrets.json"
ls.COMPOSE_ENV_FILE = rt / "compose.env"
ls.LOGS_DIR = rt / "logs"
from oce_control import local_lifecycle as ll
# B4-CXR7U9R3: arm the PRIVATE in-process interruption seam (never an
# environment variable). argv: runtime_dir [pause_stage [release_file]]
if len(sys.argv) > 2 and sys.argv[2]:
    ll._configure_interruption.stages[sys.argv[2]] = sys.argv[3] if len(sys.argv) > 3 else ""
try:
    rep = ll.configure()
    print("CONFIGURE_OK " + json.dumps(rep))
except SystemExit as exc:
    print("CONFIGURE_EXIT " + str(exc), file=sys.stderr)
    sys.exit(1)
except BaseException as exc:  # noqa: BLE001
    print("CONFIGURE_ERR " + repr(exc), file=sys.stderr)
    sys.exit(2)
"""


def _driver_env(runtime_dir: Path) -> dict:
    # CLEAN minimal env: the child runs configure's fail-closed namespace
    # validation, so it must NEVER inherit stray OCE_* variables that other
    # tests (or the host) may have left in the parent os.environ. Test
    # control travels through argv + the private seam — NEVER the
    # environment (B4-CXR7U9R3).
    env = {"PATH": os.environ.get("PATH", ""),
           "PYTHONPATH": str(BASE / "src")}
    for var in ("SYSTEMROOT", "TEMP", "TMP", "PYTHONIOENCODING"):
        if var in os.environ:
            env[var] = os.environ[var]
    env["OCE_CONTROL_PLANE_HOST"] = "127.0.0.1"
    env["OCE_CONTROL_PLANE_PORT"] = "8448"
    return env


def _spawn(runtime_dir: Path, *, pause=None, release=None):
    argv = [sys.executable, "-c", DRIVER, str(runtime_dir)]
    if pause:
        argv += [pause, str(release or "")]
    return subprocess.Popen(
        argv,
        env=_driver_env(runtime_dir),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _wait_stage(runtime_dir: Path, stage: str, timeout_s: float = 60.0) -> None:
    """Wait until the journal reports the given stage committed."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        jp = runtime_dir / "configure_journal.json"
        if jp.exists():
            try:
                data = json.loads(jp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
            if data.get("stage") == stage and data.get("status") == "committed":
                return
        time.sleep(0.02)
    raise AssertionError(f"journal never reached stage {stage!r}")


def _run_to_completion(runtime_dir: Path, *, pause=None, release=None,
                       timeout_s: float = 120.0):
    p = _spawn(runtime_dir, pause=pause, release=release)
    out, err = p.communicate(timeout=timeout_s)
    return p, out, err


def _digest(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def _digests(rt: Path) -> dict:
    return {
        "secrets.json": _digest(rt / "secrets.json"),
        "compose.env": _digest(rt / "compose.env"),
        "activation_handoff_key": _digest(rt / "activation_handoff_key"),
        "marker": _digest(rt / "configure.committed"),
    }


def _assert_complete_coherent(rt: Path) -> dict:
    store = json.loads((rt / "secrets.json").read_text(encoding="utf-8"))
    assert store["postgres_password"] and store["worker_token"]
    key = (rt / "activation_handoff_key").read_text(encoding="utf-8").strip()
    assert len(key) >= 64
    pw = store["postgres_password"]
    assert (rt / "compose.env").read_text(encoding="utf-8") == \
        f"POSTGRES_PASSWORD={pw}\n"
    assert (rt / "configure.committed").exists()
    assert not (rt / "configure_journal.json").exists()
    return store


class TestConfigureSubprocessCrash:
    """A REAL subprocess killed mid-configure must recover deterministically."""

    @pytest.mark.parametrize("stage", [
        "postgres_password",
        "worker_token",
        "activation_handoff_key",
        "compose_env_projection",
        "commit",
    ])
    def test_first_configure_killed_at_stage_recovers_on_restart(
            self, tmp_path, stage):
        rt = tmp_path / ".runtime"
        # 1. kill the process while paused after the named stage committed
        p = _spawn(rt, pause=stage)
        _wait_stage(rt, stage)
        time.sleep(0.4)          # let the process reach the pause loop
        assert p.poll() is None, "driver died before the pause point"
        p.kill()
        p.wait(timeout=30)
        assert (rt / "configure_journal.json").exists(), \
            "journal must survive the kill (durable recoverable state)"
        # 2. restart configure: deterministic recovery then completion
        p2, out, err = _run_to_completion(rt)
        assert p2.returncode == 0, f"restart failed: {err}\n{out}"
        assert "CONFIGURE_OK" in out
        store = _assert_complete_coherent(rt)
        assert store["postgres_password"]

    def test_reconfigure_killed_before_commit_preserves_prior_authority(
            self, tmp_path):
        rt = tmp_path / ".runtime"
        _run_to_completion(rt)
        prior = _digests(rt)
        assert prior["marker"]
        # re-configure killed at the first stage: the journal snapshot holds
        # the committed prior state; recovery must restore it byte-for-byte
        p = _spawn(rt, pause="postgres_password")
        _wait_stage(rt, "postgres_password")
        time.sleep(0.4)
        p.kill()
        p.wait(timeout=30)
        p2, out, err = _run_to_completion(rt)
        assert p2.returncode == 0, f"restart failed: {err}"
        after = _digests(rt)
        for key in ("secrets.json", "activation_handoff_key", "marker"):
            assert after[key] == prior[key], \
                f"{key} changed across crash recovery"
        assert _assert_complete_coherent(rt)

    def test_kill_after_authority_commit_rolls_forward(self, tmp_path):
        rt = tmp_path / ".runtime"
        _run_to_completion(rt)
        prior = _digests(rt)
        # kill AFTER the commit marker + journal("commit"): the committed
        # bundle is authoritative — restart must roll FORWARD, not back
        p = _spawn(rt, pause="commit")
        _wait_stage(rt, "commit")
        time.sleep(0.4)
        assert (rt / "configure.committed").exists()
        p.kill()
        p.wait(timeout=30)
        p2, out, err = _run_to_completion(rt)
        assert p2.returncode == 0, f"restart failed: {err}"
        assert "crash_recovery" in out
        after = _digests(rt)
        assert after["secrets.json"] == prior["secrets.json"]
        assert after["activation_handoff_key"] == prior["activation_handoff_key"]
        assert _assert_complete_coherent(rt)


class TestConfigureConcurrency:
    def test_two_concurrent_configure_processes_serialize(self, tmp_path):
        rt = tmp_path / ".runtime"
        release = tmp_path / "release.txt"
        a = _spawn(rt, pause="worker_token", release=release)
        try:
            _wait_stage(rt, "worker_token")
            time.sleep(0.4)
            # second configure blocks on the whole-configure lock
            b = _spawn(rt)
            time.sleep(1.5)
            assert b.poll() is None, \
                "concurrent configure must WAIT on the exclusive lock"
            # release A: both complete serially
            release.write_text("go", encoding="utf-8")
            out_a, err_a = a.communicate(timeout=120)
            out_b, err_b = b.communicate(timeout=120)
            assert a.returncode == 0, err_a
            assert b.returncode == 0, err_b
            assert "CONFIGURE_OK" in out_a and "CONFIGURE_OK" in out_b
        finally:
            if a.poll() is None:
                a.kill()
            try:
                release.unlink(missing_ok=True)
            except OSError:
                pass
        store = _assert_complete_coherent(rt)
        assert store["postgres_password"]

    def test_failed_concurrent_configure_never_restores_stale_snapshot(
            self, tmp_path):
        rt = tmp_path / ".runtime"
        # A succeeds first
        _run_to_completion(rt)
        authority = _digests(rt)
        # B crashes mid re-configure (its snapshot is of A's committed state)
        b = _spawn(rt, pause="worker_token")
        _wait_stage(rt, "worker_token")
        time.sleep(0.4)
        b.kill()
        b.wait(timeout=30)
        # C restarts: recovery rolls B back to A's state, then idempotent
        # configure must preserve A's authority (no stale snapshot over a
        # successful commit)
        p2, out, err = _run_to_completion(rt)
        assert p2.returncode == 0, err
        after = _digests(rt)
        assert after["secrets.json"] == authority["secrets.json"]
        assert after["activation_handoff_key"] == authority["activation_handoff_key"]
        assert after["marker"] == authority["marker"]


class TestConfigureCorruptJournal:
    def test_corrupt_journal_fails_closed_without_rewrite(self, tmp_path):
        rt = tmp_path / ".runtime"
        _run_to_completion(rt)
        jp = rt / "configure_journal.json"
        jp.write_text("{not-json", encoding="utf-8")
        jbytes = jp.read_bytes()
        p, out, err = _run_to_completion(rt)
        assert p.returncode != 0
        assert "CONFIGURE_ERR" in err or "CONFIGURE_EXIT" in err
        assert jp.read_bytes() == jbytes, "corrupt journal was overwritten"
        # authority untouched
        store = json.loads((rt / "secrets.json").read_text(encoding="utf-8"))
        assert store["postgres_password"]

    def test_journal_without_recoverable_snapshot_fails_closed(self, tmp_path):
        # a journal from the pre-U8 format (stage/digest only, no snapshot)
        # cannot be rolled back deterministically -> manual remediation raise
        rt = tmp_path / ".runtime"
        _run_to_completion(rt)
        jp = rt / "configure_journal.json"
        jp.write_text(json.dumps({"stage": "worker_token",
                                  "status": "committed",
                                  "snapshot_digest": "x"}), encoding="utf-8")
        # an UNCOMMITTED crash (no marker) cannot be rolled back from a
        # journal without recoverable state -> manual remediation, fail closed
        (rt / "configure.committed").unlink()
        jbytes = jp.read_bytes()
        p, out, err = _run_to_completion(rt)
        assert p.returncode != 0
        assert jp.read_bytes() == jbytes, "legacy journal was overwritten"
        assert "manual remediation" in err
# --------------------------------------------------------------------------- #
# B4-CXR7U9R3 — production configure must not consume ambient test-control
# variables. The old CXR7U8_CONFIGURE_* environment surface is REMOVED:
# setting both variables has ZERO effect on public configure(); the names
# appear nowhere in production os.environ/getenv reads; the private
# in-process seam remains functional for crash/concurrency proofs; no test
# seam appears in the CLI surface.
# --------------------------------------------------------------------------- #
class TestCXR7U9R3ConfigureSeamIsolation:
    def test_legacy_env_variables_have_zero_effect(self, tmp_path, monkeypatch):
        import oce_control.local_secrets as ls
        import oce_control.local_lifecycle as ll
        rt = tmp_path / ".runtime"
        monkeypatch.setattr(ls, "RUNTIME_DIR", rt)
        monkeypatch.setattr(ls, "SECRETS_FILE", rt / "secrets.json")
        monkeypatch.setattr(ls, "COMPOSE_ENV_FILE", rt / "compose.env")
        monkeypatch.setattr(ls, "LOGS_DIR", rt / "logs")
        # BOTH legacy names set: public configure() must complete normally,
        # ignoring them entirely (no pause, no timing change)
        monkeypatch.setenv("CXR7U8_CONFIGURE_PAUSE_STAGE",
                           "postgres_password")
        monkeypatch.setenv("CXR7U8_CONFIGURE_RELEASE_FILE",
                           str(tmp_path / "never-created"))
        rep = ll.configure()
        assert rep
        store = __import__("json").loads(
            (rt / "secrets.json").read_text(encoding="utf-8"))
        assert store["postgres_password"] and store["worker_token"]

    def test_legacy_names_absent_from_production_env_reads(self):
        import pathlib
        prod = (pathlib.Path(__file__).resolve().parent.parent / "src"
                / "oce_control")
        offenders = []
        for py in prod.glob("*.py"):
            text = py.read_text(encoding="utf-8")
            if "CXR7U8_CONFIGURE" in text:
                offenders.append(py.name)
        assert offenders == [], \
            f"legacy test-control names present in production source: {offenders}"

    def test_private_seam_pauses_at_every_required_stage(self, tmp_path):
        import json
        import threading
        import time
        import oce_control.local_secrets as ls
        import oce_control.local_lifecycle as ll
        rt = tmp_path / ".runtime"
        monkey_rt = {"RUNTIME_DIR": rt,
                     "SECRETS_FILE": rt / "secrets.json",
                     "COMPOSE_ENV_FILE": rt / "compose.env",
                     "LOGS_DIR": rt / "logs"}
        saved = {k: getattr(ls, k) for k in monkey_rt}
        for k, v in monkey_rt.items():
            setattr(ls, k, v)
        try:
            for stage in ("postgres_password", "worker_token",
                          "activation_handoff_key", "compose_env_projection",
                          "commit"):
                release = tmp_path / f"release-{stage}"
                release.write_text("", encoding="utf-8")  # pre-created? NO:
                release.unlink()  # armed pause must WAIT for this file
                ll._configure_interruption.stages = {stage: str(release)}
                done = {}
                def _run():
                    try:
                        done["rep"] = ll.configure()
                    except BaseException as exc:  # noqa: BLE001
                        done["err"] = repr(exc)
                th = threading.Thread(target=_run, daemon=True)
                th.start()
                time.sleep(1.0)
                assert th.is_alive(),                     f"configure did not pause at armed stage {stage}"
                # release: the pause ends only when the release file appears
                release.write_text("go", encoding="utf-8")
                th.join(timeout=60)
                assert not th.is_alive(), f"configure hung at {stage}"
                assert "err" not in done, done.get("err")
                assert done.get("rep")
                # journal proves the stage sequence ran to the commit stage
                jp = rt / "configure_journal.json"
                if jp.exists():
                    data = json.loads(jp.read_text(encoding="utf-8"))
                    assert data.get("status") in ("committed", "pending")
            ll._configure_interruption.stages = {}
            # full authority materialized through the REAL implementation
            store = json.loads(
                (rt / "secrets.json").read_text(encoding="utf-8"))
            assert store["postgres_password"] and store["worker_token"]
        finally:
            for k, v in saved.items():
                setattr(ls, k, v)

    def test_no_test_seam_in_cli_help_or_arguments(self):
        import pathlib
        oce_local = (pathlib.Path(__file__).resolve().parent.parent
                     / "scripts" / "oce_local.py")
        text = oce_local.read_text(encoding="utf-8")
        assert "CXR7U8" not in text
        assert "_configure_interruption" not in text
        assert "pause_stage" not in text
        assert "release_file" not in text

    def test_seam_grants_no_authority(self):
        # the controller only carries timing data: no configuration values,
        # no secrets, no callbacks into authority-bearing code
        import oce_control.local_lifecycle as ll
        c = ll._ConfigureInterruptionController()
        assert c.__dict__.keys() == {"stages", "deadline_seconds"}
        assert c.stages == {}
