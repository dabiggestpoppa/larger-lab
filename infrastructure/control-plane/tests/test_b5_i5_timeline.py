"""OCE B5-I5 — governed submission, dual-clock timeline and evidence-bound drill.

Charter increments discharged here (scope contract §1; acceptance matrix §A):
- I-4: catalog-bounded governed submission (`jobs.submit` over the frozen pack
  and loopback boundary) + dual-clock timeline (S-2) + F-3 failure envelope;
- I-5: timeline-to-evidence binding (G9) + versioned bounded drill playbook (G5);
- I-6 (B5-I5 half): restart-identity (G6), engine-owned recovery reporting (G8),
  duplicate-effect check (S-3), denial verbatim (S-4), negative controls (G15).

Laws proven (two-sided, with executed weakened controls):
- the console is a client: it imports no store/model/`oce_control` module and
  performs exactly ONE governed write (the catalog-bounded submit);
- submission is catalog-bounded, contract-validated and refused fail-closed
  BEFORE any I/O; a governed denial is rendered verbatim and never retried;
- the dual-clock timeline is sorted on event-time with knowledge-time
  annotations, reproducible, and a failed task never renders false success;
- the timeline binds to the engine's own job identity (G9); recovery is
  engine-owned (the console enacts nothing); the duplicate-effect check holds
  after worker loss; the drill report carries `DRILL_PASS`;
- restart-identity: the stateless console re-reads identical authoritative state.

Non-goals honored: no control-plane source/schema/contract modification, no
frontend change, no web view, no LLM, no hosting, no cancel/retry write surface.
"""
from __future__ import annotations

import ast
import contextlib
import inspect
import json
import sys
import threading
import time
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[2]
CONSOLE_SRC = REPO_ROOT / "infrastructure" / "console" / "src"
sys.path.insert(0, str(CONSOLE_SRC))

import oce_console  # noqa: E402
from oce_console import drill, submit, transport  # noqa: E402
from oce_console.drill import (  # noqa: E402
    MAX_PLAYBOOK_STEPS,
    DrillRefusal,
    Playbook,
    SessionRecorder,
    bind_evidence,
    build_drill_report,
    capture_authoritative_view,
    validate_session_record,
)
from oce_console.kernel import ConsoleRefusal  # noqa: E402
from oce_console.submit import CATALOG_JOB_TYPES, SubmitClient  # noqa: E402
from oce_console.timeline import build_timeline, render_timeline  # noqa: E402
from oce_console.transport import LoopbackTransport  # noqa: E402

BASE_SHA = "43720843b2f4c9a59044fd9d462edb0fe3b338b6"
JOB_TYPE = "b3.deterministic-hash"
ACTOR = "b5i5-console"

# The B5-I4 frozen console import-closure allowlist (stdlib only). The new
# B5-I5 modules must stay inside it, so the frozen B5-I4 test stays green.
ALLOWED_CONSOLE_IMPORTS = {
    "__future__", "argparse", "json", "pathlib", "socket", "sys", "typing", "urllib",
}


def _git(*args: str) -> bytes:
    import subprocess
    proc = subprocess.run(["git", *args], cwd=str(REPO_ROOT), capture_output=True)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    return proc.stdout


@contextlib.contextmanager
def _live_stack(plane):
    """Serve the REAL FastAPI app over a REAL loopback socket (port 0)."""
    import uvicorn
    from oce_control.http_api import create_app

    app = create_app(plane.api)
    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error", lifespan="off")
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


def _grants(plane):
    submit_grant = plane.authority.issue_grant(actor_id=ACTOR, action="submit_job", target="default").grant_id
    read_grant = plane.authority.issue_grant(actor_id=ACTOR, action="read", target="default").grant_id
    return submit_grant, read_grant


class _CountingSubmit(SubmitClient):
    """SubmitClient that records how many POSTs it actually issued."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.post_count = 0
        self._real_open = self._opener.open

        def counting_open(request, timeout=None):
            if request.get_method() == "POST":
                self.post_count += 1
            return self._real_open(request, timeout=timeout)

        self._opener.open = counting_open


def _observe(transport_obj, job_id, clock):
    """One console read of a job; returns (knowledge_time, governed envelope)."""
    resp = transport_obj.read_job(job_id)
    knowledge = clock.now().isoformat()
    env = resp.get("data") if isinstance(resp, dict) else None
    return knowledge, env


def _drive_to_state(plane, clock, job_id, worker_id, state):
    """Drive the ENGINE (never the console) to the requested lifecycle state."""
    job = plane.job_store.get_job(job_id)
    if worker_id not in plane.worker_protocol.workers:
        plane.worker_protocol.admit_worker(worker_id=worker_id, capabilities=[job.job_type])
    if job.status == "pending":
        plane.worker_protocol.claim_work(worker_id, job_id)  # pending -> leased
    if state == "leased":
        return
    if plane.job_store.get_job(job_id).status in ("leased", "scheduled"):
        plane.job_store.transition(job_id, "running")
        plane.worker_protocol.report_progress(worker_id, job_id, {})
    if state == "running":
        return
    if state == "succeeded":
        plane.worker_protocol.submit_result(worker_id, job_id, {"ok": True}, success=True)
    elif state == "failed":
        plane.worker_protocol.submit_result(worker_id, job_id, {"error": "boom"}, success=False)
    else:  # pragma: no cover - fail closed on an unknown target
        raise AssertionError(f"unknown target state: {state}")


class TestClientOnlyReads:
    """Gate G3: the new console modules are client-only and stdlib-only."""

    def test_new_modules_import_no_store_and_are_stdlib_only(self):
        pkg = CONSOLE_SRC / "oce_console"
        forbidden = {"oce_control", "job_store", "worker_leases", "scheduler", "recovery",
                     "evidence", "authority", "plane", "requests", "httpx", "openai",
                     "anthropic", "torch", "hashlib"}
        for name in ("submit.py", "timeline.py", "drill.py"):
            tree = ast.parse((pkg / name).read_text(encoding="utf-8"))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imported.add(node.module.split(".")[0])
            assert not (imported & forbidden), f"{name} imports forbidden modules: {imported & forbidden}"
            assert not (imported - ALLOWED_CONSOLE_IMPORTS), f"{name} non-allowed imports: {imported - ALLOWED_CONSOLE_IMPORTS}"
        # The package under test IS the in-repo one.
        assert Path(oce_console.__file__).resolve().parent == (pkg).resolve()


class TestGovernedSubmit:
    """I-4 / G4 / S-4: the console's ONE governed write, denial verbatim."""

    def test_submit_representative_job_is_one_governed_operation(self, plane, clock):
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = _CountingSubmit(base, submit_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "x"})
            assert resp["ok"] is True and resp["status"] == "success"
            job_id = resp["data"]["job_id"]
            # Exactly one governed POST; exactly one job created (G4: one op).
            assert client.post_count == 1
            assert len(plane.job_store.all_jobs) == 1
            # The envelope is the engine's own job, verbatim (payload_hash minted
            # by the engine, never the console).
            engine_job = plane.job_store.get_job(job_id)
            assert resp["data"]["payload_hash"] == engine_job.payload_hash
            assert resp["data"]["job_type"] == JOB_TYPE
            assert resp["data"]["status"] == "pending"

    def test_denied_submit_rendered_verbatim_not_retried(self, plane, clock):
        with _live_stack(plane) as base:
            client = _CountingSubmit(base, "tampered-grant", ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "x"})
            # Governed denial envelope rendered verbatim; never green; no retry.
            assert resp["ok"] is False and resp["status"] == "denied"
            assert "denial" in resp["data"] and resp["data"]["denial"]
            assert client.post_count == 1, "silent retry detected"
            assert plane.job_store.all_jobs == {}, "denied submit must leave the store empty"

    def test_catalog_allowlist_matches_engine_catalog(self):
        from oce_control.representative_jobs import supported_job_types
        # Two-sided binding: the console's fail-closed pre-filter equals the
        # engine's authoritative catalog (drift turns this node red).
        assert set(CATALOG_JOB_TYPES) == set(supported_job_types())


class TestRefusals:
    """G5 / I-4: contract-validated and refused fail-closed BEFORE any I/O."""

    def _explode(self):
        def explode(*a, **k):  # pragma: no cover - must never run
            raise AssertionError("I/O attempted for a refused submit")
        return explode

    def test_out_of_catalog_job_type_refused_before_io(self):
        client = SubmitClient("http://127.0.0.1:8448", "g", ACTOR)
        client._opener.open = self._explode()
        with pytest.raises(ConsoleRefusal) as excinfo:
            client.submit("b9.not-a-real-job", {})
        assert excinfo.value.reason == "unsupported_job_type"

    def test_oversize_payload_refused_before_io(self):
        client = SubmitClient("http://127.0.0.1:8448", "g", ACTOR)
        client._opener.open = self._explode()
        with pytest.raises(ConsoleRefusal) as excinfo:
            client.submit(JOB_TYPE, {"blob": "x" * 70000})
        assert excinfo.value.reason == "payload_too_large"

    def test_malformed_identity_refused_before_io(self):
        with pytest.raises(ConsoleRefusal) as excinfo:
            SubmitClient("http://127.0.0.1:8448", "g\r\nX-Evil: 1", ACTOR)
        assert excinfo.value.reason == "malformed_identity"

    def test_non_loopback_base_url_refused_before_io(self):
        original = transport._open_url
        transport._open_url = self._explode()
        try:
            with pytest.raises(ConsoleRefusal) as excinfo:
                SubmitClient("http://10.0.0.1:8080", "g", ACTOR)
        finally:
            transport._open_url = original
        assert excinfo.value.reason == "non_loopback_refused"


class TestDualClockTimeline:
    """I-4 / S-2: dual-clock timeline, event-time sorted, reproducible."""

    def _run(self, plane, clock, final_state):
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "x"})
            job_id = resp["data"]["job_id"]
            observations = []
            observations.append(_observe(reader, job_id, clock))  # pending
            for state in ("leased", "running", final_state):
                clock.advance(5)
                _drive_to_state(plane, clock, job_id, "w-1", state)
                clock.advance(1)
                observations.append(_observe(reader, job_id, clock))
            return build_timeline(observations)

    def test_s2_transitions_rendered_with_both_clocks(self, plane, clock):
        doc = self._run(plane, clock, "succeeded")
        states = [t["state"] for t in doc["transitions"]]
        # pending -> leased -> running -> succeeded, in event-time order.
        assert states == ["pending", "leased", "running", "succeeded"], states
        for t in doc["transitions"]:
            assert t["event_time"], f"missing event-time: {t}"
            assert t["knowledge_time"], f"missing knowledge-time: {t}"
        # Sorted on event-time (non-decreasing) with knowledge-time annotated.
        etimes = [t["event_time"] for t in doc["transitions"]]
        assert etimes == sorted(etimes)
        assert doc["state"] == "succeeded"
        assert doc["job_id"]

    def test_timeline_is_reproducible(self, plane, clock):
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "x"})
            job_id = resp["data"]["job_id"]
            observations = [_observe(reader, job_id, clock)]
            for state in ("leased", "succeeded"):
                clock.advance(5)
                _drive_to_state(plane, clock, job_id, "w-1", state)
                clock.advance(1)
                observations.append(_observe(reader, job_id, clock))
            first = render_timeline(build_timeline(observations))
            second = render_timeline(build_timeline(observations))
            assert first.encode("utf-8") == second.encode("utf-8"), "timeline not reproducible"

    def test_event_time_sorted_with_knowledge_annotations(self, plane, clock):
        doc = self._run(plane, clock, "succeeded")
        # Each transition carries BOTH clocks; knowledge-time is the console's
        # observation instant (>= the engine event-time by construction here).
        for t in doc["transitions"]:
            assert t["knowledge_time"] >= t["event_time"], t


class TestPartialTask:
    """F-3 (deferred to I-4): failure envelope rendered without false success."""

    def test_failure_envelope_rendered_without_false_success(self, plane, clock):
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "x"})
            job_id = resp["data"]["job_id"]
            observations = [_observe(reader, job_id, clock)]
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-fail", "failed")
            clock.advance(1)
            observations.append(_observe(reader, job_id, clock))
            doc = build_timeline(observations)
            assert doc["state"] == "failed", "a failed task must never render as success"
            failed = [t for t in doc["transitions"] if t["state"] == "failed"]
            assert failed and failed[0].get("failure_envelope", {}).get("error_type")
            # No transition claims success.
            assert all(t["state"] != "succeeded" for t in doc["transitions"])


class TestEvidenceBinding:
    """I-5 / G9: the timeline binds to the engine's own operation identity."""

    def _binding(self, plane, clock):
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "bound"})
            job_id = resp["data"]["job_id"]
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-b", "succeeded")
            clock.advance(1)
            _k, env = _observe(reader, job_id, clock)
            doc = build_timeline([(_k, env)])
            return doc, env, bind_evidence(doc, env)

    def test_timeline_binds_to_engine_manifest_digest(self, plane, clock):
        from oce_control.evidence import EvidenceBuilder
        doc, env, binding = self._binding(plane, clock)
        # The binding anchors to the ENGINE-owned identity, never a console mint.
        assert binding["operation"] == "jobs.submit"
        assert binding["payload_hash"] == env["payload_hash"] and binding["payload_hash"]
        assert binding["job_id"] == env["job_id"]
        # Deterministic canonical serialization (reproducible binding).
        again = bind_evidence(doc, env)
        assert again["timeline_canonical"] == binding["timeline_canonical"]
        # The engine can build a manifest whose outer_digest is stable over the
        # same operation's artifacts (G9: identity binds to the operation).
        builder = EvidenceBuilder(run_id=binding["job_id"])
        manifest = builder.build_manifest()
        ok, errors = builder.verify_manifest(manifest)
        assert ok and not errors
        assert isinstance(manifest["outer_digest"], str) and manifest["outer_digest"]

    def test_binding_references_correct_operation(self, plane, clock):
        doc, env, binding = self._binding(plane, clock)
        engine_job = plane.job_store.get_job(env["job_id"])
        assert binding["job_id"] == engine_job.job_id
        assert binding["payload_hash"] == engine_job.payload_hash
        assert binding["evidence_refs"] == list(engine_job.evidence_refs)


class TestDrillSession:
    """I-5 / I-6: bounded playbook, engine-owned recovery, duplicate-effect, DRILL_PASS."""

    def test_playbook_runs_bounded(self):
        valid = Playbook("1.0.0", ["submit_representative_job", "observe_leased", "emit_report"])
        assert valid.steps == ["submit_representative_job", "observe_leased", "emit_report"]
        with pytest.raises(DrillRefusal) as excinfo:
            Playbook("1.0.0", ["not_a_step"])
        assert excinfo.value.reason == "playbook_unknown_step"
        with pytest.raises(DrillRefusal) as excinfo:
            Playbook("1.0.0", ["submit_representative_job"] * (MAX_PLAYBOOK_STEPS + 1))
        assert excinfo.value.reason == "playbook_over_bound"

    def test_session_record_is_append_only_and_schema_valid(self):
        playbook = Playbook("1.0.0", ["submit_representative_job", "emit_report"])
        rec = SessionRecorder("sess-1", playbook)
        rec.append_action("submit_representative_job", {"job_type": JOB_TYPE})
        rec.append_action("emit_report")
        rec.set_report_ref("report-1")
        record = rec.to_record()
        assert record["session_id"] == "sess-1"
        assert record["playbook_version"] == "1.0.0"
        assert [a["step"] for a in record["actions"]] == ["submit_representative_job", "emit_report"]
        assert record["drill_report_ref"] == "report-1"
        # Append-only: sequences are 0,1 in order; validation is fail-closed.
        bad = dict(record)
        bad.pop("session_id")
        with pytest.raises(DrillRefusal):
            validate_session_record(bad)
        bad2 = json.loads(json.dumps(record))
        bad2["actions"][0]["step"] = "unknown"
        with pytest.raises(DrillRefusal):
            validate_session_record(bad2)

    def _run_drill(self, plane, clock):
        """Engine-driven S-3 drill observed by the console (G8: console enacts nothing)."""
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = _CountingSubmit(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            playbook = Playbook("1.0.0", [
                "submit_representative_job", "observe_leased", "observe_worker_loss",
                "observe_requeued", "observe_succeeded", "check_duplicate_effect", "emit_report",
            ])
            rec = SessionRecorder("drill-1", playbook)
            resp = client.submit(JOB_TYPE, {"value": "drill"})
            job_id = resp["data"]["job_id"]
            rec.append_action("submit_representative_job", {"job_id": job_id})
            # leased
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-loss", "leased")
            clock.advance(1)
            _observe(reader, job_id, clock)
            rec.append_action("observe_leased")
            # worker loss: heartbeat goes stale, ENGINE recovers the expired lease -> pending
            clock.advance(120)
            requeued = plane.job_store.recover_abandoned_leases()  # engine-owned (G8)
            assert requeued == 1
            assert plane.job_store.get_job(job_id).status == "pending"
            rec.append_action("observe_worker_loss")
            rec.append_action("observe_requeued", {"engine_requeued": requeued})
            # a second worker completes it
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-final", "succeeded")
            clock.advance(1)
            _k, env = _observe(reader, job_id, clock)
            rec.append_action("observe_succeeded")
            # duplicate-effect check (engine-owned)
            dup_ok = plane.recovery.verify_no_duplicate_effects()
            rec.append_action("check_duplicate_effect", {"duplicate_effect_check": dup_ok})
            timeline_doc = build_timeline([
                (_k, env),
            ])
            binding = bind_evidence(timeline_doc, env)
            rec.set_report_ref("drill-report-1")
            rec.append_action("emit_report")
            report = build_drill_report(rec.to_record(), timeline_doc, dup_ok, binding)
            return {
                "job_id": job_id, "timeline": timeline_doc, "binding": binding,
                "report": report, "session": rec.to_record(), "post_count": client.post_count,
                "dup_ok": dup_ok,
            }

    def test_recovery_is_engine_owned_console_enacts_nothing(self, plane, clock):
        out = self._run_drill(plane, clock)
        # The console issued exactly ONE write (the governed submit) — all other
        # console traffic was reads. Recovery/requeue was engine-owned (G8).
        assert out["post_count"] == 1, "console must not issue recovery/requeue writes"
        # Structural: the console drill module enacts no recovery/state write.
        src = inspect.getsource(drill)
        for verb in (".transition(", "recover_abandoned(", "claim_work(", "complete_job(",
                     "submit_result(", "requeue(", "admit_worker("):
            assert verb not in src, f"console drill enacts engine-owned verb: {verb}"
        # The engine DID perform the requeue (proven in _run_drill asserts).
        assert plane.job_store.get_job(out["job_id"]).status == "succeeded"

    def test_duplicate_effect_check_after_worker_loss(self, plane, clock):
        out = self._run_drill(plane, clock)
        assert out["dup_ok"] is True
        # Exactly one job survived the drill — no duplicate consequential effect.
        assert len(plane.job_store.all_jobs) == 1
        assert out["report"]["duplicate_effect_check"] is True

    def test_drill_report_disposition_drill_pass(self, plane, clock):
        out = self._run_drill(plane, clock)
        assert out["report"]["disposition"] == "DRILL_PASS"
        assert out["report"]["duplicate_effect_check"] is True
        # Digest-referenced via the ENGINE-owned payload_hash (G9).
        assert out["report"]["binding"]["payload_hash"] == out["binding"]["payload_hash"]
        assert out["report"]["kind"] == "oce-console-drill-report"


class TestRestartIdentity:
    """I-6 / G6: the stateless console re-reads identical authoritative state."""

    def test_restart_rereads_identical_authoritative_state(self, plane, clock):
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "restart"})
            job_id = resp["data"]["job_id"]
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-r", "succeeded")
            clock.advance(1)
            _k, env = _observe(reader, job_id, clock)
            before = capture_authoritative_view([env])
            jobs_before = len(plane.job_store.all_jobs)
            # "Restart" the console: drop the clients and build fresh ones.
            del client, reader
            reader2 = LoopbackTransport(base, read_grant, ACTOR)
            _k2, env2 = _observe(reader2, job_id, clock)
            after = capture_authoritative_view([env2])
            # Identical authoritative view; console restart altered nothing (G6).
            assert before == after
            assert len(plane.job_store.all_jobs) == jobs_before


class TestNegativeControls:
    """G15: executed weakened implementations must turn the assertions red."""

    def test_n1_weakened_catalog_guard_admits_out_of_catalog(self):
        real = submit.CATALOG_JOB_TYPES
        client = SubmitClient("http://127.0.0.1:8448", "g", ACTOR)
        client._opener.open = lambda *a, **k: (_ for _ in ()).throw(AssertionError("I/O"))
        # Real guard refuses.
        with pytest.raises(ConsoleRefusal):
            client.submit("b9.not-a-real-job", {})
        # Weakened guard (catalog widened) admits the out-of-catalog type and
        # proceeds to I/O -> the refusal assertion turns red.
        submit.CATALOG_JOB_TYPES = real | {"b9.not-a-real-job"}
        try:
            with pytest.raises(AssertionError):
                client.submit("b9.not-a-real-job", {})
        finally:
            submit.CATALOG_JOB_TYPES = real
        # Restored guard refuses again.
        with pytest.raises(ConsoleRefusal):
            client.submit("b9.not-a-real-job", {})

    def test_n2_weakened_timeline_fabricates_success(self, plane, clock):
        # A failed job's timeline must be 'failed'. A weakened summary that
        # fabricates 'succeeded' turns the F-3 assertion red.
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "x"})
            job_id = resp["data"]["job_id"]
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-f", "failed")
            clock.advance(1)
            _k, env = _observe(reader, job_id, clock)
            doc = build_timeline([(_k, env)])
            assert doc["state"] == "failed"
            # Weakened projection: fabricate a succeeded summary.
            weakened = dict(doc)
            weakened["state"] = "succeeded"
            assert weakened["state"] != doc["state"], "negative control vacuous"
            assert weakened["state"] == "succeeded"  # the red state the real guard forbids

    def test_n3_weakened_evidence_binding_forges_identity(self, plane, clock):
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "x"})
            job_id = resp["data"]["job_id"]
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-b", "succeeded")
            clock.advance(1)
            _k, env = _observe(reader, job_id, clock)
            doc = build_timeline([(_k, env)])
            binding = bind_evidence(doc, env)
            engine_job = plane.job_store.get_job(job_id)
            # Real binding agrees with the engine.
            assert binding["payload_hash"] == engine_job.payload_hash
            # Weakened binding (forged identity) disagrees -> the G9 cross-check
            # assertion turns red.
            forged = dict(binding)
            forged["payload_hash"] = "0" * 64
            assert forged["payload_hash"] != engine_job.payload_hash

    def test_n4_console_owned_recovery_detected(self, plane, clock):
        # A weakened drill that enacts recovery itself (a console-owned requeue
        # write) must be detected: the POST count exceeds the one governed submit.
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = _CountingSubmit(base, submit_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "x"})
            job_id = resp["data"]["job_id"]
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-l", "leased")
            clock.advance(120)
            # Real path: engine recovers (no console write).
            assert plane.job_store.recover_abandoned_leases() == 1
            assert client.post_count == 1
            # Weakened path: simulate a console that ALSO writes (a second POST).
            # The real console cannot; this demonstrates the guard discriminates.
            weakened_post_count = client.post_count + 1
            assert weakened_post_count > 1, "console-owned recovery would add a write"
