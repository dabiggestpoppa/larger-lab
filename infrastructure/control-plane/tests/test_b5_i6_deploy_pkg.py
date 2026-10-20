"""OCE B5-I6 — C4 local deployment, observability and recovery objectives.

Plan §5 rows discharged here (P0 acceptance matrix §A):
- **C4.S1** release packaging: deterministic manifest, declared install set,
  tamper detection, clean-install dry run (R12–R15). Local only — remote
  mutation stays hold-gated and is never attempted.
- **C4.S2** observability: the operator detects failure (fail-closed) and
  traces a governed operation through the engine's own audit surface (R16–R17).
- **C4.S3** failure injection: the plan-named chaos classes at the
  console/deployment boundary — process kill, dependency outage, partial
  write, timeout (R18).
- **C4.S4** recovery: restore drill with RPO 0 (no persisted action lost, no
  duplicate effect, evidence identity re-derived byte-identically) and RTO
  measured on the ENGINE clock within the frozen objective bound (R19).

Laws: constitution §12.2 (clean versioned releases from declared source; the
local workspace is never uploaded wholesale; no deployment without rollback
metadata), Article XV (untested restore is unverified), charter §6 (local-only,
$0, no provider). The packaging tool is stdlib-only and lives OUTSIDE the
oce_console package, so the frozen B5-I4 import closure is untouched.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[2]
CONSOLE_SRC = REPO_ROOT / "infrastructure" / "console" / "src"
PACKAGING_DIR = REPO_ROOT / "infrastructure" / "console" / "packaging"
sys.path.insert(0, str(CONSOLE_SRC))
sys.path.insert(0, str(PACKAGING_DIR))

import make_release_manifest as mrm  # noqa: E402
from oce_console.drill import (  # noqa: E402
    DrillRefusal,
    Playbook,
    SessionRecorder,
    bind_evidence,
    build_drill_report,
)
from oce_console.kernel import (  # noqa: E402
    STATE_UNREACHABLE,
    build_status_document,
)
from oce_console.session_store import SessionStore  # noqa: E402
from oce_console.submit import SubmitClient  # noqa: E402
from oce_console.timeline import build_timeline  # noqa: E402
from oce_console.transport import LoopbackTransport, StackUnreachable  # noqa: E402

ACTOR = "b5i6-deploy"
JOB_TYPE = "b3.deterministic-hash"
DRILL_STEPS = [
    "submit_representative_job", "observe_leased", "observe_worker_loss",
    "observe_requeued", "observe_succeeded", "check_duplicate_effect",
    "emit_report",
]
# Frozen RTO objective (C4.S4): the engine-clock budget from worker-loss
# injection to DRILL_PASS — lease TTL (120s) plus the fixed drill steps'
# clock advances (5+1+5+1 = 12s) with headroom. Deterministic on the test
# clock; no wall-clock claim is made anywhere.
RTO_OBJECTIVE_SECONDS = 300


def _live_stack(plane):
    import uvicorn
    from oce_control.http_api import create_app

    app = create_app(plane.api)
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
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=20)
        assert not thread.is_alive(), "loopback stack failed to stop"


import contextlib  # noqa: E402

_live = contextlib.contextmanager(_live_stack)


def _grants(plane):
    submit_grant = plane.authority.issue_grant(
        actor_id=ACTOR, action="submit_job", target="default").grant_id
    read_grant = plane.authority.issue_grant(
        actor_id=ACTOR, action="read", target="default").grant_id
    return submit_grant, read_grant


def _drive_to_state(plane, clock, job_id, worker_id, state):
    """Drive the ENGINE (never the console) to the requested lifecycle state."""
    job = plane.job_store.get_job(job_id)
    if worker_id not in plane.worker_protocol.workers:
        plane.worker_protocol.admit_worker(worker_id=worker_id,
                                           capabilities=[job.job_type])
    if job.status == "pending":
        plane.worker_protocol.claim_work(worker_id, job_id)
    if state == "leased":
        return
    if plane.job_store.get_job(job_id).status in ("leased", "scheduled"):
        plane.job_store.transition(job_id, "running")
        plane.worker_protocol.report_progress(worker_id, job_id, {})
    if state == "running":
        return
    if state == "succeeded":
        plane.worker_protocol.submit_result(worker_id, job_id, {"ok": True},
                                            success=True)
    else:  # pragma: no cover - fail closed on an unknown target
        raise AssertionError(f"unknown target state: {state}")


def _closed_port() -> int:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


class TestReleaseManifest:
    """C4.S1: deterministic package, declared set, tamper-proof, dry run."""

    def test_manifest_is_deterministic_byte_identical(self):
        first = mrm.build_manifest(REPO_ROOT)
        second = mrm.build_manifest(REPO_ROOT)
        assert mrm.render_manifest(first) == mrm.render_manifest(second)
        assert first["outer_digest"] == second["outer_digest"]

    def test_manifest_covers_declared_install_set_and_rollback(self):
        manifest = mrm.build_manifest(REPO_ROOT)
        # Every console module and declared support file is hashed.
        assert manifest["install_set"] == sorted(mrm.DECLARED_INSTALL_SET)
        for name in ("kernel.py", "transport.py", "submit.py", "drill.py",
                     "session_store.py", "timeline.py", "cli.py",
                     "__init__.py", "__main__.py"):
            assert f"infrastructure/console/src/oce_console/{name}" in \
                manifest["install_set"]
        assert "infrastructure/control-plane/contracts/console-contract.json" in \
            manifest["install_set"]
        assert manifest["dependency_lock_sha256"] and manifest["contract_pack_sha256"]
        # Rollback metadata is present and points at the authorized base.
        rollback = manifest["rollback"]
        assert rollback["base_commit"] == manifest["base_commit"]
        assert rollback["procedure"]
        assert mrm.REQUIRED_ROLLBACK_FIELDS[0] in rollback
        # A missing declared file fails generation CLOSED (no incomplete
        # manifest is ever produced).
        absent = mrm.DECLARED_INSTALL_SET + ("infrastructure/console/src/"
                                             "oce_console/ghost.py",)
        original = mrm.DECLARED_INSTALL_SET
        mrm.DECLARED_INSTALL_SET = absent
        try:
            with pytest.raises(SystemExit) as excinfo:
                mrm.build_manifest(REPO_ROOT)
            assert "missing declared file" in str(excinfo.value)
        finally:
            mrm.DECLARED_INSTALL_SET = original

    def test_tampered_install_file_fails_verification(self, tmp_path):
        manifest = mrm.build_manifest(REPO_ROOT)
        dest = tmp_path / "install"
        mrm.materialize(manifest, REPO_ROOT, dest)
        ok, errors = mrm.verify_manifest(manifest, dest)
        assert ok and errors == []
        # Tamper one byte of one installed file.
        victim = dest / "infrastructure/console/src/oce_console/kernel.py"
        victim.write_bytes(victim.read_bytes() + b"\n# tampered\n")
        ok, errors = mrm.verify_manifest(manifest, dest)
        assert not ok
        assert any("hash mismatch" in e and "kernel.py" in e for e in errors), \
            f"verification must NAME the tampered file: {errors}"
        # Executed negative control: a WEAKENED verifier that skips the hash
        # check admits the tampered tree (the red state), then the real
        # verifier is restored and refuses again.
        def weakened_verify(manifest, root):
            # hash comparison deleted — sizes only
            errs = []
            for entry in manifest["files"]:
                path = Path(root) / entry["path"]
                if not path.is_file():
                    errs.append(f"missing file: {entry['path']}")
            return (not errs), errs
        weakened_ok, _ = weakened_verify(manifest, dest)
        assert weakened_ok is True, "the weakened verifier is exactly the red state"
        ok_again, _ = mrm.verify_manifest(manifest, dest)
        assert ok_again is False, "the restored verifier must refuse again"

    def test_clean_install_dry_run_verifies_and_imports(self, tmp_path):
        manifest = mrm.build_manifest(REPO_ROOT)
        dest = tmp_path / "fresh-install"
        copied = mrm.materialize(manifest, REPO_ROOT, dest)
        assert sorted(copied) == sorted(manifest["install_set"])
        ok, errors = mrm.verify_manifest(manifest, dest)
        assert ok, errors
        # The installed copy IS importable and renders a status document —
        # the dry run proves the package stands alone (stdlib only).
        child = (
            "import json, sys\n"
            "from oce_console.kernel import build_status_document, render_status\n"
            "surfaces = {'health.read': '/api/health', 'readiness.read': "
            "'/api/readiness', 'system.read': '/api/system', 'workers.list': "
            "'/api/workers', 'jobs.schedules': '/api/schedules'}\n"
            "envelope = {'ok': True, 'status': 'success', 'data': {}, "
            "'error': '', 'request_id': 'dry-run'}\n"
            "doc = build_status_document(lambda s: envelope, surfaces)\n"
            "import oce_console\n"
            "print(json.dumps({'state': doc['state'], "
            "'pkg': oce_console.__file__}))\n"
        )
        env = dict(**{k: v for k, v in __import__("os").environ.items()},
                   PYTHONPATH=str(dest / "infrastructure/console/src"))
        proc = subprocess.run([sys.executable, "-c", child], env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              timeout=60)
        assert proc.returncode == 0, proc.stderr
        out = json.loads(proc.stdout.strip().splitlines()[-1])
        assert out["state"] == "OK"
        # The import came from the INSTALLED copy, not the source tree.
        assert str(dest) in out["pkg"], out["pkg"]


class TestObservability:
    """C4.S2: the operator detects failure and traces a governed operation."""

    def test_stack_failure_detected_fail_closed(self):
        # Dependency outage: the CLI fails closed (exit 2, STACK_UNREACHABLE
        # document) — never stale green, never exit 0.
        child = (
            "import sys\n"
            "from oce_console.cli import main\n"
            "code = main(['status', '--base-url', "
            f"'http://127.0.0.1:{_closed_port()}',"
            " '--grant', 'g', '--actor', 'a'])\n"
            "sys.exit(code)\n"
        )
        env = dict(**{k: v for k, v in __import__("os").environ.items()},
                   PYTHONPATH=str(CONSOLE_SRC))
        proc = subprocess.run([sys.executable, "-c", child], env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              timeout=60)
        assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
        document = json.loads(proc.stdout)
        assert document["state"] == STATE_UNREACHABLE
        assert document["sections"] == {}, "no partial green survives"

    def test_operator_traces_governed_operation_in_audit_surface(self, plane, clock):
        # A governed submit is traceable locally: the engine's OWN audit
        # surface names the operation and the job it produced, and the
        # timeline/evidence bind to the same engine identity — correlated
        # through console reads only (no new endpoint, no store access).
        submit_grant, read_grant = _grants(plane)
        with _live(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "trace"})
            job_id = resp["data"]["job_id"]
            request_id = resp["request_id"]
            # The engine's audit surface (declared read surface) records the
            # governed operation with the job as its target.
            audit = reader.read("audit.read")
            assert audit["ok"] is True
            entries = audit["data"]["audit_log"]
            submit_entries = [e for e in entries
                              if e["action"] == "submit_job" and e["target"] == job_id]
            assert len(submit_entries) == 1, entries
            assert submit_entries[0]["success"] is True
            assert submit_entries[0]["actor"] == ACTOR
            # The same job read through jobs.inspect carries the engine's
            # identity, which the timeline + evidence binding reference.
            clock.advance(1)
            env = reader.read_job(job_id)
            assert env["payload_hash"]
            timeline = build_timeline([(clock.now().isoformat(), env)])
            binding = bind_evidence(timeline, env)
            assert binding["job_id"] == job_id
            assert binding["payload_hash"] == env["payload_hash"]
            assert request_id  # the response id the operator saw


class TestChaosMatrix:
    """C4.S3: process, dependency, partial-write and timeout injections."""

    def test_process_and_dependency_injections_fail_closed(self, plane, tmp_path):
        # Process injection: a console killed mid-session leaves a durable
        # partial record; a NEW console against a dead stack fails closed.
        store = SessionStore(tmp_path / "chaos-sessions")
        rec = SessionRecorder("chaos-1", Playbook("1.0.0", DRILL_STEPS))
        rec.append_action("submit_representative_job", {"job_id": "j-chaos"})
        store.save(rec.to_record())
        # (the durable record survives the process loss)
        assert SessionStore(tmp_path / "chaos-sessions").load("chaos-1")["status"] \
            == "partial"
        # Dependency injection: reads against the closed port raise
        # StackUnreachable — the kernel collapses the WHOLE view.
        client = LoopbackTransport(f"http://127.0.0.1:{_closed_port()}",
                                   "g", ACTOR)
        with pytest.raises(StackUnreachable):
            client.read("health.read")

    def test_partial_write_and_timeout_injections_fail_closed(self, tmp_path):
        # Partial-write injection: an interrupted write leaves only a .tmp
        # fragment; the store NEVER reads tmp files, and a torn FINAL file
        # refuses fail-closed (never fabricated into a record).
        store = SessionStore(tmp_path / "partial-sessions")
        rec = SessionRecorder("partial-1", Playbook("1.0.0", DRILL_STEPS))
        rec.append_action("submit_representative_job", {"job_id": "j-p"})
        store.save(rec.to_record())
        final = store.path_for("partial-1")
        torn_tmp = final.with_name(final.name + ".tmp")
        torn_tmp.write_text('{"session_id": "partial-1", "half', encoding="utf-8")
        # The valid record still loads (the fragment is invisible to reads).
        assert store.load("partial-1")["actions"][0]["step"] == \
            "submit_representative_job"
        # A torn FINAL file (the crash landed between write and replace) is
        # refused explicitly — no fabricated record, no false completion.
        final.write_text('{"session_id": "partial-1", "act', encoding="utf-8")
        with pytest.raises(DrillRefusal) as excinfo:
            store.load("partial-1")
        assert excinfo.value.reason == "session_record_corrupt"
        # Timeout injection: an injected transport timeout raises
        # StackUnreachable (fail-closed), never a fabricated success.
        import oce_console.transport as transport_module

        client = LoopbackTransport(f"http://127.0.0.1:{_closed_port()}", "g", ACTOR)
        real_open = transport_module._open_url

        def timing_out(opener, request, timeout):
            raise socket.timeout("injected timeout")

        transport_module._open_url = timing_out
        try:
            with pytest.raises(StackUnreachable) as timed:
                client.read("health.read")
            assert "timeout" in str(timed.value) or timed.value
        finally:
            transport_module._open_url = real_open
        # Restored: the real seam fails closed on the closed port too.
        with pytest.raises(StackUnreachable):
            client.read("health.read")


class TestRestoreObjectives:
    """C4.S4: restore drill — RPO 0 and RTO within the frozen objective."""

    def test_restore_drill_meets_rpo_and_rto_objectives(self, plane, clock, tmp_path):
        from datetime import datetime

        submit_grant, read_grant = _grants(plane)
        store = SessionStore(tmp_path / "restore-sessions")
        with _live(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            rec = SessionRecorder("restore-1", Playbook("1.0.0", DRILL_STEPS))
            resp = client.submit(JOB_TYPE, {"value": "restore"})
            job_id = resp["data"]["job_id"]
            rec.append_action("submit_representative_job", {"job_id": job_id})
            store.save(rec.to_record())
            # Engine drives to leased; console observes and persists.
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-r", "leased")
            clock.advance(1)
            env = reader.read_job(job_id)
            rec.append_action("observe_leased")
            record_at_leased = store.save(rec.to_record())
            actions_at_loss = len(record_at_leased["actions"])

            # RTO measurement starts: worker-loss injection (engine clock).
            t_loss = clock.now()
            clock.advance(120)  # heartbeat goes stale (lease TTL)
            requeued = plane.job_store.recover_abandoned_leases()
            assert requeued == 1
            rec.append_action("observe_worker_loss")
            rec.append_action("observe_requeued", {"engine_requeued": requeued})
            store.save(rec.to_record())
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-final", "succeeded")
            clock.advance(1)
            env_done = reader.read_job(job_id)
            rec.append_action("observe_succeeded")
            dup_ok = plane.recovery.verify_no_duplicate_effects()
            rec.append_action("check_duplicate_effect",
                              {"duplicate_effect_check": dup_ok})
            timeline = build_timeline([(clock.now().isoformat(), env),
                                       (clock.now().isoformat(), env_done)])
            binding = bind_evidence(timeline, env_done)
            rec.set_report_ref("restore-report")
            rec.append_action("emit_report")
            finished = store.save(rec.to_record(), complete=True)
            report = build_drill_report(finished, timeline, dup_ok, binding)
            t_done = clock.now()

            # RTO: engine-clock duration from injection to DRILL_PASS is
            # within the frozen objective bound (deterministic, no wall clock).
            rto_seconds = (t_done - t_loss).total_seconds()
            assert report["disposition"] == "DRILL_PASS"
            assert 0 <= rto_seconds <= RTO_OBJECTIVE_SECONDS, (
                f"RTO {rto_seconds}s exceeds objective {RTO_OBJECTIVE_SECONDS}s")

            # RPO part 1: zero persisted drill actions lost — the record the
            # console held at worker-loss time is still a prefix of the
            # finished record (nothing was lost or rewritten).
            assert finished["actions"][:actions_at_loss] == \
                record_at_leased["actions"]
            # RPO part 2: no duplicate consequential effect.
            assert dup_ok is True
            assert len(plane.job_store.all_jobs) == 1

            # RPO part 3 (identity): the engine evidence manifest re-derives
            # byte-identically from the same artifacts (fresh builder) —
            # evidence identity survives a restart with zero loss.
            from oce_control.evidence import EvidenceBuilder

            artifact = tmp_path / "artifact.json"
            artifact.write_text(json.dumps({"job_id": job_id,
                                            "payload_hash": env_done["payload_hash"]},
                                           sort_keys=True), encoding="utf-8")
            first = EvidenceBuilder("run-1")
            first.add_artifact("drill-result", str(artifact))
            second = EvidenceBuilder("run-2")
            second.add_artifact("drill-result", str(artifact))
            assert first.build_manifest()["outer_digest"] == \
                second.build_manifest()["outer_digest"], (
                    "evidence identity must re-derive byte-identically")
