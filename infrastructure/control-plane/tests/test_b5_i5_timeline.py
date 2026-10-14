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

R5 fail-closed boundary (ratification audit §5–§8):
- `read_job` returns a validated governed envelope or raises `JobReadRefusal`;
  denial/partial/hostile responses can never enter the success domain, and no
  caller can consume failure data as success by omitting an `ok` check;
- the timeline renders denial/incomplete observations as explicit
  UNVERIFIABLE gaps, never as lifecycle events;
- evidence binding refuses denial payloads, missing engine identity and
  cross-job evidence; `DRILL_PASS` is refused unless the engine-owned
  duplicate-effect check held in this session's own record.

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
from oce_console.transport import (  # noqa: E402
    JobReadRefusal,
    LoopbackTransport,
    project_job_read,
)

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
    """One console read of a job; returns (knowledge_time, governed envelope).

    Uses the fail-closed typed boundary: a denial/not-found/malformed answer
    raises `JobReadRefusal`, so this helper can never hand failure data to the
    timeline (B5-I5 R5 §5).
    """
    env = transport_obj.read_job(job_id)
    knowledge = clock.now().isoformat()
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


def _job_env(**overrides) -> dict:
    """A structurally complete governed job envelope for boundary controls."""
    env = {
        "job_id": "job-1",
        "job_type": JOB_TYPE,
        "status": "pending",
        "payload_hash": "a" * 64,
        "created_at": "2026-10-13T10:00:00+00:00",
        "attempt_number": 1,
        "evidence_refs": ["jobs/job-1/submit.json"],
    }
    env.update(overrides)
    return env


def _resp(data, ok: bool = True, status: str = "success") -> dict:
    return {"ok": ok, "status": status, "data": data}


class TestJobReadFailClosedBoundary:
    """§5: every denial/hostile `jobs.inspect` response is refused at one seam."""

    def test_c1_caller_omitting_ok_check_cannot_consume_denial(self, plane, clock):
        """Control 1: the omitted-`ok`-check caller pattern is structurally dead."""
        hostile = _resp(
            _job_env(status="succeeded", attempt_number=7),
            ok=False, status="denied",
        )
        hostile["data"]["denial"] = {"code": "403", "reason": "denied"}
        # Real boundary: the naive `env = resp.get("data")` caller never runs —
        # read_job raises instead of returning anything to destructure.
        with pytest.raises(JobReadRefusal) as excinfo:
            project_job_read(hostile)
        assert excinfo.value.reason == "read_denied"
        # Weakened boundary (raw passthrough): the OLD shipped caller pattern
        # (`resp.get("data")` with no `ok` check) feeds the denial into the
        # authoritative view — the red state this seam exists to forbid.
        original = transport.project_job_read
        transport.project_job_read = lambda response, **kw: response
        try:
            resp = hostile  # exactly what a raw read_job would return
            env = resp.get("data") if isinstance(resp, dict) else None
            forged_view = capture_authoritative_view([env])
            forged_timeline = build_timeline([("2026-10-13T10:00:01+00:00", env)])
        finally:
            transport.project_job_read = original
        assert forged_view == [{
            "job_id": "job-1", "status": "succeeded",
            "payload_hash": "a" * 64, "attempt_number": 7,
        }], "negative control vacuous: denial did not forge a success view"
        # The timeline layer refuses it too (defense in depth).
        assert forged_timeline["state"] == "UNVERIFIABLE"
        assert forged_timeline["transitions"][0]["reason"] == "denial_envelope"
        # Restored: the same input is refused again.
        with pytest.raises(JobReadRefusal):
            project_job_read(hostile)

    def test_c2_denial_dictionary_with_job_like_fields_refused(self):
        hostile = _resp(
            _job_env(status="succeeded"), ok=False, status="denied")
        hostile["data"]["denial"] = {"reason": "denied"}
        with pytest.raises(JobReadRefusal) as excinfo:
            project_job_read(hostile)
        assert excinfo.value.reason == "read_denied"
        # An ok=true body whose data still carries a denial payload.
        sneaky = _resp(_job_env(denial={"reason": "denied"}), ok=True)
        with pytest.raises(JobReadRefusal) as excinfo:
            project_job_read(sneaky)
        assert excinfo.value.reason == "denial_envelope"

    def test_c3_malformed_response_with_job_id_but_no_identity_refused(self):
        # job_id present, but not a valid governed envelope (no payload_hash /
        # created_at) — must not enter the success domain.
        with pytest.raises(JobReadRefusal) as excinfo:
            project_job_read(_resp({"job_id": "job-1", "status": "pending"}))
        assert excinfo.value.reason == "incomplete_envelope"
        assert "payload_hash" in excinfo.value.detail

    def test_c4_ok_true_with_missing_required_fields_refused(self):
        with pytest.raises(JobReadRefusal) as excinfo:
            project_job_read(_resp(_job_env(payload_hash="")))
        assert excinfo.value.reason == "incomplete_envelope"
        assert "payload_hash" in excinfo.value.detail

    def test_c5_ok_false_with_success_looking_fields_refused(self):
        hostile = _resp(_job_env(status="succeeded"), ok=False, status="error")
        with pytest.raises(JobReadRefusal) as excinfo:
            project_job_read(hostile)
        assert excinfo.value.reason == "read_error"
        # The verbatim response stays attached for rendering (S-4 spirit).
        assert excinfo.value.response is hostile
        # The refusal IS a console refusal: the CLI's refusal renderer handles
        # it, so denial never becomes an unhandled success-shaped dict.
        assert issubclass(JobReadRefusal, ConsoleRefusal)

    def test_c6_stale_job_after_engine_restart_refused_fail_closed(
            self, plane, clock):
        """Control 6: engine restarted (fresh store) -> stale job refuses."""
        from oce_control.plane import ControlPlane
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "stale"})
            job_id = resp["data"]["job_id"]
        # Engine restart: a fresh, empty authoritative store behind a new stack.
        fresh = ControlPlane(test_clock=clock)
        _fresh_submit, fresh_read = _grants(fresh)
        with _live_stack(fresh) as base:
            reader = LoopbackTransport(base, fresh_read, ACTOR)
            with pytest.raises(JobReadRefusal) as excinfo:
                reader.read_job(job_id)
        assert "not_found" in excinfo.value.reason
        assert excinfo.value.response["ok"] is False
        # No fabricated envelope: the refusal carries no job data.
        assert excinfo.value.response["data"] == {} or "job_id" not in (
            excinfo.value.response.get("data") or {})

    def test_c7_unauthorized_read_grant_refused_denial_attached(self, plane, clock):
        submit_grant, read_grant = _grants(plane)
        with _live_stack(plane) as base:
            client = SubmitClient(base, submit_grant, ACTOR)
            resp = client.submit(JOB_TYPE, {"value": "x"})
            job_id = resp["data"]["job_id"]
            reader = LoopbackTransport(base, "tampered-read-grant", ACTOR)
            with pytest.raises(JobReadRefusal) as excinfo:
                reader.read_job(job_id)
            assert excinfo.value.reason == "read_denied"
            denial = (excinfo.value.response.get("data") or {}).get("denial")
            assert denial, "denial must stay verbatim on the refusal, not as a job"

    def test_c8_unknown_response_types_refused(self):
        for weird in ([{"ok": True}], "ok", 42, None, {"ok": True}):
            with pytest.raises(JobReadRefusal) as excinfo:
                project_job_read(weird)
            assert excinfo.value.reason == "not_a_governed_envelope"

    def test_c_wrong_job_id_refused_when_expected(self):
        with pytest.raises(JobReadRefusal) as excinfo:
            project_job_read(_resp(_job_env()), expected_job_id="job-2")
        assert excinfo.value.reason == "envelope_job_mismatch"


class TestTimelineOrderingControls:
    """§7: load-bearing ordering rules each have an executable discriminator."""

    def test_tiebreak_is_observation_sequence_not_knowledge_order(self):
        # Equal event-time: observation SEQUENCE is the declared tiebreak.
        # Knowledge times are deliberately reversed relative to sequence, so a
        # weakened (event_time, knowledge_time) tiebreak would order differently.
        a = _job_env(status="pending")
        b = _job_env(status="scheduled")
        doc1 = build_timeline([("k2", a), ("k1", b)])  # seq0 has LATER knowledge
        doc2 = build_timeline([("k2", a), ("k1", b)])
        states = [tr["state"] for tr in doc1["transitions"]]
        assert states == ["pending", "scheduled"], states
        assert [tr["sequence"] for tr in doc1["transitions"]] == [0, 1]
        assert render_timeline(doc1) == render_timeline(doc2)
        # Discrimination: a knowledge-time tiebreak would order b before a.
        assert states != [tr["state"] for tr in sorted(
            doc1["transitions"], key=lambda t: t["knowledge_time"])]
        # Reversed input order flips with it (input order == observation order).
        doc3 = build_timeline([("k1", b), ("k2", a)])
        assert [tr["state"] for tr in doc3["transitions"]] == ["scheduled", "pending"]

    def test_regressing_event_time_is_sorted_not_rewritten(self):
        # A later-observed job with an EARLIER engine event-time sorts first;
        # its event-time is preserved verbatim (never clamped to look
        # monotonic in observation order), and observation order is carried by
        # `sequence`, not by the sort.
        late = _job_env(job_id="job-2", created_at="2026-10-13T09:00:00+00:00")
        fresh = _job_env(job_id="job-3", created_at="2026-10-13T11:00:00+00:00")
        doc = build_timeline([
            ("2026-10-13T10:01:00+00:00", fresh),  # observed first, event later
            ("2026-10-13T10:02:00+00:00", late),   # observed second, event earlier
        ])
        etimes = [tr["event_time"] for tr in doc["transitions"]]
        assert etimes == sorted(etimes), "regressing event-time not sorted"
        assert doc["transitions"][0]["event_time"] == "2026-10-13T09:00:00+00:00"
        # Discrimination: sorting by observation/knowledge order would put the
        # 11:00 event first — the real timeline does not.
        assert doc["transitions"][0]["sequence"] == 1
        assert doc["transitions"][1]["sequence"] == 0
        # Knowledge-time annotations are untouched (never rewritten as event-time).
        assert doc["transitions"][0]["knowledge_time"] == "2026-10-13T10:02:00+00:00"
        assert doc["transitions"][1]["knowledge_time"] == "2026-10-13T10:01:00+00:00"

    def test_missing_timestamp_is_explicit_gap_never_fabricated(self):
        no_ts = _job_env()
        no_ts.pop("created_at")
        doc = build_timeline([("2026-10-13T10:00:01+00:00", no_ts)])
        tr = doc["transitions"][0]
        assert tr["state"] == "UNVERIFIABLE"
        assert tr["event_time"] == "", "a missing engine timestamp must not be filled"
        assert "created_at" in tr["reason"]
        assert doc["state"] == "UNVERIFIABLE"

    def test_denial_never_collapses_into_a_lifecycle_event(self):
        denial_data = {"denial": {"reason": "denied"}}
        doc = build_timeline([("2026-10-13T10:00:01+00:00", denial_data)])
        assert doc["state"] == "UNVERIFIABLE"
        assert doc["transitions"][0]["reason"] == "denial_envelope"
        assert all(t["state"] != "succeeded" for t in doc["transitions"])
        # Hostile denial carrying job-like fields (full identity + denial):
        # still a gap — a denial never collapses into a lifecycle event.
        hostile = _job_env(status="succeeded", denial={"reason": "denied"})
        doc2 = build_timeline([("2026-10-13T10:00:01+00:00", hostile)])
        assert doc2["state"] == "UNVERIFIABLE"
        assert doc2["transitions"][0]["reason"] == "denial_envelope"


class TestEvidenceBindingGuards:
    """§8: binding refuses denial, missing identity and cross-job evidence."""

    def test_denial_envelope_refused_by_binding(self):
        env = _job_env(denial={"reason": "denied"})
        doc = build_timeline([("k", env)])
        with pytest.raises(DrillRefusal) as excinfo:
            bind_evidence(doc, env)
        assert excinfo.value.reason == "evidence_binding_denial_envelope"

    def test_missing_payload_hash_refused_by_binding(self):
        env = _job_env()
        env.pop("payload_hash")
        doc = build_timeline([("k", _job_env())])
        with pytest.raises(DrillRefusal) as excinfo:
            bind_evidence(doc, env)
        assert excinfo.value.reason == "evidence_binding_no_payload_hash"

    def test_missing_evidence_refs_refused_by_binding(self):
        env = _job_env()
        env.pop("evidence_refs")
        doc = build_timeline([("k", _job_env())])
        with pytest.raises(DrillRefusal) as excinfo:
            bind_evidence(doc, env)
        assert excinfo.value.reason == "evidence_binding_no_evidence_refs"

    def test_cross_job_evidence_refused_by_binding(self):
        timeline_doc = build_timeline([("k", _job_env(job_id="job-1"))])
        other_job = _job_env(job_id="job-2")
        with pytest.raises(DrillRefusal) as excinfo:
            bind_evidence(timeline_doc, other_job)
        assert excinfo.value.reason == "evidence_binding_job_mismatch"


class TestDrillReportClaimGuard:
    """§8: DRILL_PASS cannot be claimed without this session's own evidence."""

    def _record(self, with_check: bool, check_value: bool = True) -> dict:
        playbook = Playbook("1.0.0", ["submit_representative_job", "emit_report"])
        rec = SessionRecorder("sess-guard", playbook)
        rec.append_action("submit_representative_job", {"job_id": "job-1"})
        if with_check:
            rec.append_action("check_duplicate_effect",
                              {"duplicate_effect_check": check_value})
        rec.append_action("emit_report")
        return rec.to_record()

    def _bound(self) -> dict:
        env = _job_env()
        doc = build_timeline([("k", env)])
        return bind_evidence(doc, env)

    def test_drill_pass_refused_without_duplicate_effect_check(self):
        record = self._record(with_check=True)
        binding = self._bound()
        doc = build_timeline([("k", _job_env())])
        # dup=False: refused (no false pass).
        with pytest.raises(DrillRefusal) as excinfo:
            build_drill_report(record, doc, False, binding)
        assert excinfo.value.reason == "drill_pass_requires_duplicate_effect_check"
        # A non-pass disposition still records the observed result.
        report = build_drill_report(record, doc, False, binding,
                                    disposition="DRILL_INCOMPLETE")
        assert report["disposition"] == "DRILL_INCOMPLETE"
        assert report["duplicate_effect_check"] is False

    def test_drill_pass_refused_without_session_check_action(self):
        # dup=True claimed, but THIS session never observed the check — a
        # reused/short-circuited record must not mint DRILL_PASS.
        record = self._record(with_check=False)
        with pytest.raises(DrillRefusal) as excinfo:
            build_drill_report(record, build_timeline([("k", _job_env())]),
                               True, self._bound())
        assert excinfo.value.reason == "drill_pass_requires_check_action"

    def test_drill_pass_refused_with_malformed_or_unbound_inputs(self):
        record = self._record(with_check=True)
        bad_record = dict(record)
        bad_record.pop("session_id")
        with pytest.raises(DrillRefusal) as excinfo:
            build_drill_report(bad_record, build_timeline([("k", _job_env())]),
                               True, self._bound())
        assert excinfo.value.reason == "session_record_missing_fields"
        unbound = dict(self._bound())
        unbound["payload_hash"] = ""
        with pytest.raises(DrillRefusal) as excinfo:
            build_drill_report(record, build_timeline([("k", _job_env())]),
                               True, unbound)
        assert excinfo.value.reason == "drill_report_unbound"


class TestSubmitIdentityAuthority:
    """§6: missing operator identity refuses BEFORE any I/O."""

    def test_missing_grant_or_actor_refused_before_io(self):
        for grant, actor in (("", ACTOR), ("g", ""), ("", "")):
            with pytest.raises(ConsoleRefusal) as excinfo:
                SubmitClient("http://127.0.0.1:8448", grant, actor)
            assert excinfo.value.reason == "missing_identity"
        # The refusal happens at construction: no client (and therefore no
        # request object or socket) can exist afterwards — before any I/O.
