"""OCE B5-I6 — console restart identity, crash-partial sessions, session durability.

Registry discharges executed here (P0 addendum; scope contract §5):
- **G6 (console half)** — `TestRestartIdentity::test_restart_preserves_session_record`
  (frozen planned node, verbatim): a durable session record survives a console
  restart byte-identically while engine/governed state stays unaltered.
- **F-4 (console half)** — `TestConsoleCrash::test_session_record_marked_partial_on_crash`
  (adopted under the disclosed file-prefix supersession: the frozen planned file
  `test_b5_i5_drills.py` was never created; class/function names identical): a
  real console subprocess killed mid-drill leaves a durable PARTIAL record with
  every pre-crash action present, and control-plane state untouched.
- C4.S4 support — an engine restart can never resurrect console state and stale
  job reads fail closed (`JobReadRefusal`), never false success.

Laws: charter §5 rule 6 (frontend loss cannot lose or rewrite governed state),
charter §9 Interruption/Restart, plan §5 C4.S4 (restore; RPO 0 for console
records). Client-only closure: `session_store.py` imports stay inside the
frozen B5-I4 allowlist and touch no store/model/engine module.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[2]
CONSOLE_SRC = REPO_ROOT / "infrastructure" / "console" / "src"
sys.path.insert(0, str(CONSOLE_SRC))

import oce_console  # noqa: E402
from oce_console.drill import DrillRefusal, Playbook, SessionRecorder  # noqa: E402
from oce_console.session_store import SessionStore  # noqa: E402
from oce_console.transport import JobReadRefusal, LoopbackTransport  # noqa: E402

ACTOR = "b5i6-console"
JOB_TYPE = "b3.deterministic-hash"
PLAYBOOK = ["submit_representative_job", "observe_leased", "emit_report"]

# The frozen B5-I4 import allowlist (test_b5_i4_console_kernel.py, frozen green).
ALLOWED_CONSOLE_IMPORTS = {
    "__future__", "argparse", "json", "pathlib", "socket", "sys", "typing", "urllib",
}


def _playbook() -> Playbook:
    return Playbook("1.0.0", PLAYBOOK)


def _partial_record(session_id: str, steps: int) -> dict:
    rec = SessionRecorder(session_id, _playbook())
    for step in PLAYBOOK[:steps]:
        rec.append_action(step, {"job_id": "job-x"})
    return rec.to_record()


class TestRestartIdentity:
    """G6 (console half): restart preserves the durable session record."""

    def test_restart_preserves_session_record(self, plane, clock, tmp_path):
        """FROZEN PLANNED NODE (registry G6, verbatim id).

        A completed record and a partial record are each written by one
        console process; a BRAND-NEW store (the console restarted) loads
        byte-identical, schema-valid, append-only records. The engine's
        governed state is unchanged by the console restart in both
        directions (console restart alters nothing engine-side; engine
        reads stay identical).
        """
        store_dir = tmp_path / "sessions"
        # Seed one governed job so engine state exists and must survive.
        grant = plane.authority.issue_grant(actor_id=ACTOR, action="submit_job", target="default")
        resp = plane.api.submit_job(grant_id=grant.grant_id, actor_id=ACTOR,
                                    job_type=JOB_TYPE, payload={"value": "restart"})
        assert resp.ok, resp
        job_id = resp.data["job_id"]
        engine_before = {
            jid: plane.job_store.get_job(jid).status
            for jid in plane.job_store.all_jobs
        }

        # Console process 1: persist a partial record and a completed one.
        store1 = SessionStore(store_dir)
        partial = store1.save(_partial_record("sess-partial", 2))
        rec = SessionRecorder("sess-done", _playbook())
        rec.append_action("submit_representative_job", {"job_id": job_id})
        rec.append_action("observe_leased")
        rec.append_action("emit_report")
        rec.set_report_ref("report-1")
        done = store1.save(rec.to_record(), complete=True)

        # Console restart: a brand-new store object (no memory carried over).
        store2 = SessionStore(store_dir)
        reloaded_partial = store2.load("sess-partial")
        reloaded_done = store2.load("sess-done")
        assert json.dumps(reloaded_partial, sort_keys=True) == json.dumps(partial, sort_keys=True)
        assert json.dumps(reloaded_done, sort_keys=True) == json.dumps(done, sort_keys=True)
        assert reloaded_partial["status"] == "partial"
        assert reloaded_done["status"] == "complete"
        # Append-only across the restart: the loaded record can only grow.
        grown = json.loads(json.dumps(reloaded_partial))
        grown["actions"].append({"seq": 2, "step": "emit_report", "detail": {}})
        persisted = store2.save(grown)
        assert len(persisted["actions"]) == 3
        # Engine governed state is byte-identical after console restart (G6).
        engine_after = {
            jid: plane.job_store.get_job(jid).status
            for jid in plane.job_store.all_jobs
        }
        assert engine_after == engine_before
        assert plane.job_store.get_job(job_id).status == "pending"

    def test_engine_restart_leaves_console_state_untouched_and_reads_fail_closed(
            self, plane, clock, tmp_path):
        """Engine restart cannot resurrect console state; stale reads refuse.

        The console's durable record is untouched by an engine restart, and
        a read of the pre-restart job against the fresh engine raises
        `JobReadRefusal` — never a fabricated or cached success (F-5/§9).
        """
        from oce_control.plane import ControlPlane

        store_dir = tmp_path / "sessions"
        store1 = SessionStore(store_dir)
        record = store1.save(_partial_record("sess-engine-restart", 2))

        # Pre-restart: one governed job exists (the record references it).
        grant1 = plane.authority.issue_grant(actor_id=ACTOR, action="submit_job", target="default")
        read1 = plane.authority.issue_grant(actor_id=ACTOR, action="read", target="default")
        resp = plane.api.submit_job(grant_id=grant1.grant_id, actor_id=ACTOR,
                                    job_type=JOB_TYPE, payload={"value": "pre-restart"})
        assert resp.ok, resp
        old_job_id = resp.data["job_id"]

        # ENGINE restart: a fresh in-memory ControlPlane (B4/Postgres owns
        # durable engine restart — carried limitation, disclosed).
        plane2 = ControlPlane(test_clock=clock)
        # Console durable state is untouched by the engine restart.
        assert json.dumps(SessionStore(store_dir).load("sess-engine-restart"),
                          sort_keys=True) == json.dumps(record, sort_keys=True)
        # The stale job read fails closed against the fresh engine.
        read2 = plane2.authority.issue_grant(actor_id=ACTOR, action="read", target="default")
        import contextlib
        import threading
        import uvicorn
        from oce_control.http_api import create_app

        app = create_app(plane2.api)
        config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error",
                                lifespan="off")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        deadline = time.monotonic() + 20
        while not server.started:
            if time.monotonic() > deadline:
                raise AssertionError("loopback stack did not start within 20s")
            time.sleep(0.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        try:
            reader = LoopbackTransport(f"http://127.0.0.1:{port}", read2.grant_id, ACTOR)
            with pytest.raises(JobReadRefusal) as excinfo:
                reader.read_job(old_job_id)
            # Every non-success path refuses typed, with the verbatim
            # response attached — no dict ever leaks out as a "job".
            assert excinfo.value.response is None or isinstance(excinfo.value.response, dict)
            assert excinfo.value.reason
        finally:
            server.should_exit = True
            thread.join(timeout=20)
            assert not thread.is_alive(), "loopback stack failed to stop"


class TestConsoleCrash:
    """F-4 (console half): crash mid-drill leaves a durable partial record."""

    def test_session_record_marked_partial_on_crash(self, plane, tmp_path):
        """FROZEN PLANNED NODE (registry F-4; disclosed file-prefix supersession).

        A REAL console subprocess persists two drill actions, signals
        readiness, and is killed with no chance to run cleanup (SIGTERM /
        TerminateProcess). The durable record on disk still carries every
        pre-crash action and `status: partial` — a crash can never mint a
        completion — and the control-plane state is untouched.
        """
        store_dir = tmp_path / "crash-sessions"
        store_dir.mkdir()
        engine_before = {
            jid: plane.job_store.get_job(jid).status
            for jid in plane.job_store.all_jobs
        }
        child_src = (
            "import sys, time\n"
            "from pathlib import Path\n"
            "from oce_console.drill import Playbook, SessionRecorder\n"
            "from oce_console.session_store import SessionStore\n"
            "store_dir, session_id = sys.argv[1], sys.argv[2]\n"
            "pb = Playbook('1.0.0', ['submit_representative_job', "
            "'observe_leased', 'emit_report'])\n"
            "rec = SessionRecorder(session_id, pb)\n"
            "store = SessionStore(store_dir)\n"
            "rec.append_action('submit_representative_job', {'job_id': 'job-crash'})\n"
            "store.save(rec.to_record())\n"
            "rec.append_action('observe_leased')\n"
            "store.save(rec.to_record())\n"
            "print('READY', flush=True)\n"
            "while True:\n"
            "    time.sleep(1)\n"
        )
        env = dict(**{k: v for k, v in __import__("os").environ.items()},
                   PYTHONPATH=str(CONSOLE_SRC))
        proc = subprocess.Popen(
            [sys.executable, "-c", child_src, str(store_dir), "sess-crash"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", env=env)
        try:
            line = proc.stdout.readline().strip()
            assert line == "READY", f"child failed to reach mid-drill: {line!r}"
            proc.terminate()  # hard stop: no cleanup, no completion flip
            proc.wait(timeout=15)
        finally:
            if proc.poll() is None:  # pragma: no cover - safety net
                proc.kill()
                proc.wait(timeout=15)

        # The durable record survived the crash with every pre-crash action
        # and is still PARTIAL — never a false completion (charter §9).
        record = SessionStore(store_dir).load("sess-crash")
        assert record["status"] == "partial"
        assert [a["step"] for a in record["actions"]] == [
            "submit_representative_job", "observe_leased"]
        assert [a["seq"] for a in record["actions"]] == [0, 1]
        assert record["drill_report_ref"] == ""
        # Control-plane state untouched by the console crash (charter §5 rule 6).
        engine_after = {
            jid: plane.job_store.get_job(jid).status
            for jid in plane.job_store.all_jobs
        }
        assert engine_after == engine_before

        # The partial record resumes only WITH consent (F-6) and completes
        # only via a bound report reference — the crash path cannot finish it.
        store = SessionStore(store_dir)
        with pytest.raises(DrillRefusal) as no_consent:
            store.resume("sess-crash")
        assert no_consent.value.reason == "replay_consent_required"
        resumed = store.resume("sess-crash", consent=True)
        assert resumed["status"] == "partial"
        with pytest.raises(DrillRefusal) as no_ref:
            store.save(resumed, complete=True)
        assert no_ref.value.reason == "completion_requires_report_ref"


class TestClientOnlyClosure:
    """Gate G3/G10 extension: the new module stays client-only and stdlib-only."""

    def test_session_store_imports_no_store_and_is_stdlib_only(self):
        pkg = CONSOLE_SRC / "oce_console"
        forbidden = {"oce_control", "job_store", "worker_leases", "scheduler", "recovery",
                     "evidence", "authority", "plane", "requests", "httpx", "openai",
                     "anthropic", "torch", "hashlib"}
        tree = ast.parse((pkg / "session_store.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module.split(".")[0])
        assert not (imported & forbidden), f"session_store imports forbidden: {imported & forbidden}"
        assert not (imported - ALLOWED_CONSOLE_IMPORTS), (
            f"session_store non-allowed imports: {imported - ALLOWED_CONSOLE_IMPORTS}")
        # The package under test IS the in-repo one (no installed shadowing).
        assert Path(oce_console.__file__).resolve().parent == pkg.resolve()
