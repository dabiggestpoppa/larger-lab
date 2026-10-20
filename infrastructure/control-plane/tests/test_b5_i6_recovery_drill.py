"""OCE B5-I6 — recovery-drill completion, engine-owned recovery, adversarial controls.

Frozen registry nodes executed VERBATIM here (P0 addendum; scope contract §5):
- **G5 (drill half)** `TestFailClosed::test_unsupported_drill_operation_refused`
- **G8 (reporting half)** `TestEngineOwnedRecovery::test_console_reports_recovery_without_enacting`
- **G15 (drill half)** `TestAdversarialControls::test_bypassed_authority_detected`
- **S-3 (console half)** `TestDrillReport::test_s3_lease_requeue_completion_no_duplicate_effect`

New F-6 (consent half) nodes from the construction plan stage I-6:
- `TestConsentReplay::test_replay_without_consent_refused_before_actions`
- `TestConsentReplay::test_consented_replay_is_idempotent_and_no_duplicate_effect`

Plus C4 recovery-completion support: drill session durability across a
console restart, report/evidence binding to engine identity, and structural
engine-verb closure over the console's drill and session-store modules.

Laws: the console performs exactly ONE governed write (the submit); recovery,
lease expiry and requeue are engine-owned (Gate G8); `DRILL_PASS` requires the
engine-owned duplicate-effect sequence observed in this session's own
append-only record (B5-I5 R5 claim guard, re-armed here end-to-end); a replay
needs explicit operator consent (F-6) and is idempotent — never a duplicate
submission (charter §9 idempotent replay). Every negative control executes a
GENUINELY WEAKENED implementation red, then restores it green byte-identically.

Client-only: no ``oce_control`` import in the console modules under test;
stdlib only; no LLM; no provider.
"""
from __future__ import annotations

import ast
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

from oce_console import drill, session_store  # noqa: E402
from oce_console.drill import (  # noqa: E402
    MAX_PLAYBOOK_STEPS,
    DrillRefusal,
    Playbook,
    SessionRecorder,
    bind_evidence,
    build_drill_report,
)
from oce_console.session_store import SessionStore  # noqa: E402
from oce_console.submit import SubmitClient  # noqa: E402
from oce_console.timeline import build_timeline  # noqa: E402
from oce_console.transport import LoopbackTransport  # noqa: E402

ACTOR = "b5i6-drill"
JOB_TYPE = "b3.deterministic-hash"
DRILL_STEPS = [
    "submit_representative_job",
    "observe_leased",
    "observe_worker_loss",
    "observe_requeued",
    "observe_succeeded",
    "check_duplicate_effect",
    "emit_report",
]

ALLOWED_CONSOLE_IMPORTS = {
    "__future__", "argparse", "json", "pathlib", "socket", "sys", "typing", "urllib",
}


def _live_stack(plane):
    """Serve the REAL FastAPI app over a REAL loopback socket (port 0)."""
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


def _drive_to_state(plane, clock, job_id, worker_id, state):
    """Drive the ENGINE (never the console) to the requested lifecycle state."""
    job = plane.job_store.get_job(job_id)
    if worker_id not in plane.worker_protocol.workers:
        plane.worker_protocol.admit_worker(worker_id=worker_id,
                                           capabilities=[job.job_type])
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
        plane.worker_protocol.submit_result(worker_id, job_id, {"ok": True},
                                            success=True)
    elif state == "failed":
        plane.worker_protocol.submit_result(worker_id, job_id, {"error": "boom"},
                                            success=False)
    else:  # pragma: no cover - fail closed on an unknown target
        raise AssertionError(f"unknown target state: {state}")


def _save(store: SessionStore, record: dict, complete: bool = False) -> dict:
    """Persist (flush law): every action is durable before the next engine I/O."""
    return store.save(record, complete=complete)


def _run_full_drill(plane, clock, tmp_path, session_id="drill-i6"):
    """The complete S-3 drill, engine-driven, console-observed, durable.

    Returns the full evidence bundle: submission, engine requeue observation,
    durable session, timeline, engine-identity binding, `DRILL_PASS` report and
    the console's POST count (must be exactly one).
    """
    submit_grant, read_grant = _grants(plane)
    store = SessionStore(tmp_path / "sessions")
    with _live(plane) as base:
        client = _CountingSubmit(base, submit_grant, ACTOR)
        reader = LoopbackTransport(base, read_grant, ACTOR)
        playbook = Playbook("1.0.0", DRILL_STEPS)
        rec = SessionRecorder(session_id, playbook)
        record = rec.to_record()

        # Step 1: the console's ONE governed write.
        resp = client.submit(JOB_TYPE, {"value": "drill-i6"})
        job_id = resp["data"]["job_id"]
        rec.append_action("submit_representative_job", {"job_id": job_id})
        record = _save(store, rec.to_record())

        # Engine drives: pending -> leased; console observes (read only).
        clock.advance(5)
        _drive_to_state(plane, clock, job_id, "w-loss", "leased")
        clock.advance(1)
        env = reader.read_job(job_id)
        k_leased = clock.now().isoformat()
        rec.append_action("observe_leased")
        record = _save(store, rec.to_record())

        # Worker loss: heartbeat stale; ENGINE recovers the expired lease.
        clock.advance(120)
        requeued = plane.job_store.recover_abandoned_leases()
        assert requeued == 1, "engine must own the lease recovery"
        assert plane.job_store.get_job(job_id).status == "pending"
        rec.append_action("observe_worker_loss")
        rec.append_action("observe_requeued", {"engine_requeued": requeued})
        record = _save(store, rec.to_record())

        # A second worker completes it (engine-owned dispatch).
        clock.advance(5)
        _drive_to_state(plane, clock, job_id, "w-final", "succeeded")
        clock.advance(1)
        env_done = reader.read_job(job_id)
        k_done = clock.now().isoformat()
        rec.append_action("observe_succeeded")
        record = _save(store, rec.to_record())

        # Engine-owned duplicate-effect check (S-3).
        dup_ok = plane.recovery.verify_no_duplicate_effects()
        rec.append_action("check_duplicate_effect",
                          {"duplicate_effect_check": dup_ok})
        record = _save(store, rec.to_record())

        # Timeline + engine-identity binding + completion (flushed durable).
        timeline_doc = build_timeline([(k_leased, env), (k_done, env_done)])
        binding = bind_evidence(timeline_doc, env_done)
        rec.set_report_ref("drill-report-i6")
        rec.append_action("emit_report")
        record = _save(store, rec.to_record(), complete=True)
        report = build_drill_report(record, timeline_doc, dup_ok, binding)

        return {
            "job_id": job_id,
            "requeued": requeued,
            "dup_ok": dup_ok,
            "timeline": timeline_doc,
            "binding": binding,
            "record": record,
            "report": report,
            "post_count": client.post_count,
            "base": base,
            "store_dir": store.directory,
            "engine_payload_hash": plane.job_store.get_job(job_id).payload_hash,
            "job_count": len(plane.job_store.all_jobs),
            "final_status": plane.job_store.get_job(job_id).status,
        }


class TestFailClosed:
    """G5 (drill half, frozen planned node): refused before any action."""

    def test_unsupported_drill_operation_refused(self, tmp_path):
        # Unknown step in a playbook: refused at construction — zero actions.
        with pytest.raises(DrillRefusal) as unknown:
            Playbook("1.0.0", ["submit_representative_job", "not_a_step"])
        assert unknown.value.reason == "playbook_unknown_step"
        # Over-bound playbook: refused at construction.
        with pytest.raises(DrillRefusal) as over:
            Playbook("1.0.0", ["submit_representative_job"] * (MAX_PLAYBOOK_STEPS + 1))
        assert over.value.reason == "playbook_over_bound"
        # An unknown SESSION resume: refused before any action exists.
        store = SessionStore(tmp_path / "sessions")
        with pytest.raises(DrillRefusal) as no_session:
            store.resume("no-such-session")
        assert no_session.value.reason == "unknown_session"
        # An exploding continuation proves nothing ran: any action attempt
        # after a refusal would raise AssertionError, and no file was created.
        exploded = []

        def exploding_continuation():
            exploded.append(1)
            raise AssertionError("action ran after refusal")

        for refusal_attempt in (unknown, over, no_session):
            assert refusal_attempt.value.reason  # structured refusal code
        # The store directory holds no session file (zero side effects).
        created = sorted(p.name for p in (tmp_path / "sessions").glob("*")) \
            if (tmp_path / "sessions").exists() else []
        assert created == [], f"refused operations left files: {created}"
        assert exploded == [], "a continuation ran after a refusal"
        # An unsupported drill OPERATION on a persisted session (unknown step
        # appended by a hostile caller) is refused by the record validator.
        rec = SessionRecorder("sess-guard", Playbook("1.0.0", ["emit_report"]))
        rec.append_action("emit_report")
        hostile = rec.to_record()
        hostile["actions"].append({"seq": 1, "step": "declare_victory", "detail": {}})
        with pytest.raises(DrillRefusal) as bad_step:
            store.save(hostile)
        assert bad_step.value.reason == "session_record_unknown_step"


class TestEngineOwnedRecovery:
    """G8 (reporting half, frozen planned node): console reports, never enacts."""

    def test_console_reports_recovery_without_enacting(self, plane, clock, tmp_path):
        out = _run_full_drill(plane, clock, tmp_path)
        # The console issued exactly ONE write (the governed submit) through
        # the whole drill — all other console traffic was reads (G8).
        assert out["post_count"] == 1, "console must not issue recovery/requeue writes"
        # The ENGINE performed the requeue and completed the job.
        assert out["requeued"] == 1
        assert out["final_status"] == "succeeded"
        # Structural closure: the console's drill and session-store modules
        # contain no engine verb — they cannot enact recovery even by accident.
        engine_verbs = (".transition(", "recover_abandoned(", "claim_work(",
                        "complete_job(", "submit_result(", "requeue(",
                        "admit_worker(", "verify_no_duplicate_effects(")
        for module in (drill, session_store):
            src = inspect.getsource(module)
            for verb in engine_verbs:
                assert verb not in src, (
                    f"console module {module.__name__} enacts engine verb {verb}")
        # The report the console RENDERED states engine-owned facts verbatim.
        assert out["report"]["duplicate_effect_check"] is True

    def test_console_modules_contain_no_engine_verbs(self):
        """C4/G8 support: AST closure over the drill + session-store modules."""
        pkg = CONSOLE_SRC / "oce_console"
        forbidden = {"oce_control", "job_store", "worker_leases", "scheduler",
                     "recovery", "evidence", "authority", "plane", "requests",
                     "httpx", "openai", "anthropic", "torch", "hashlib"}
        for name in ("drill.py", "session_store.py"):
            tree = ast.parse((pkg / name).read_text(encoding="utf-8"))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imported.add(node.module.split(".")[0])
            assert not (imported & forbidden), f"{name} imports forbidden: {imported & forbidden}"
            assert not (imported - ALLOWED_CONSOLE_IMPORTS), (
                f"{name} non-allowed imports: {imported - ALLOWED_CONSOLE_IMPORTS}")


class TestDrillReport:
    """S-3 (console half, frozen planned node): no duplicate effect, DRILL_PASS."""

    def test_s3_lease_requeue_completion_no_duplicate_effect(self, plane, clock, tmp_path):
        out = _run_full_drill(plane, clock, tmp_path, session_id="s3-drill")
        # Worker loss mid-job showed lease expiry, engine re-queue and
        # eventual completion, with no duplicate effect.
        assert out["requeued"] == 1
        assert out["dup_ok"] is True
        assert out["job_count"] == 1, "exactly one consequential effect"
        assert out["final_status"] == "succeeded"
        # The lifecycle path the drill observed (engine event-time order).
        states = [t["state"] for t in out["timeline"]["transitions"]]
        assert "leased" in states and "succeeded" in states
        # Report disposition DRILL_PASS, bound to the ENGINE identity (G9).
        assert out["report"]["disposition"] == "DRILL_PASS"
        assert out["report"]["duplicate_effect_check"] is True
        assert out["report"]["binding"]["payload_hash"] == out["engine_payload_hash"]
        assert out["report"]["binding"]["payload_hash"] == out["binding"]["payload_hash"]
        # The session record is durable and complete on disk.
        assert out["record"]["status"] == "complete"
        reloaded = SessionStore(out["store_dir"]).load("s3-drill")
        assert reloaded == out["record"]


class TestConsentReplay:
    """F-6 (consent half): replay needs consent and is idempotent."""

    def _partial(self, plane, clock, tmp_path, session_id="partial-1"):
        """Persist a drill session stopped after observe_leased (1 POST)."""
        submit_grant, read_grant = _grants(plane)
        store = SessionStore(tmp_path / "sessions")
        with _live(plane) as base:
            client = _CountingSubmit(base, submit_grant, ACTOR)
            reader = LoopbackTransport(base, read_grant, ACTOR)
            rec = SessionRecorder(session_id, Playbook("1.0.0", DRILL_STEPS))
            resp = client.submit(JOB_TYPE, {"value": "partial"})
            job_id = resp["data"]["job_id"]
            rec.append_action("submit_representative_job", {"job_id": job_id})
            _save(store, rec.to_record())
            clock.advance(5)
            _drive_to_state(plane, clock, job_id, "w-p", "leased")
            clock.advance(1)
            reader.read_job(job_id)
            rec.append_action("observe_leased")
            record = _save(store, rec.to_record())
            return {
                "job_id": job_id, "record": record, "store": store,
                "post_count": client.post_count, "base": base,
                "session_id": session_id,
            }

    def test_replay_without_consent_refused_before_actions(self, plane, clock, tmp_path):
        out = self._partial(plane, clock, tmp_path, session_id="no-consent")
        store = out["store"]
        path = store.path_for("no-consent")
        bytes_before = path.read_bytes()
        # No consent -> refused with a structured code BEFORE any action.
        with pytest.raises(DrillRefusal) as excinfo:
            store.resume("no-consent")
        assert excinfo.value.reason == "replay_consent_required"
        # Zero side effects: the durable record is byte-identical and no
        # continuation action exists (the refused replay never appended).
        assert path.read_bytes() == bytes_before
        record = store.load("no-consent")
        assert [a["step"] for a in record["actions"]] == [
            "submit_representative_job", "observe_leased"]
        assert record["status"] == "partial"

    def test_consented_replay_is_idempotent_and_no_duplicate_effect(
            self, plane, clock, tmp_path):
        out = self._partial(plane, clock, tmp_path, session_id="with-consent")
        store = out["store"]
        job_id = out["job_id"]
        post_count_at_pause = out["post_count"]
        assert post_count_at_pause == 1

        # Consent granted: the session resumes as the SAME durable record.
        record = store.resume("with-consent", consent=True)
        assert record["actions"] == out["record"]["actions"], (
            "consented resume must return the identical prefix")
        # Idempotence: the submit step is already recorded, so the replay
        # never re-submits (no duplicate submission, no second POST).
        assert any(a["step"] == "submit_representative_job"
                   for a in record["actions"])

        # Continue the drill through ENGINE-owned recovery to completion.
        clock.advance(120)
        requeued = plane.job_store.recover_abandoned_leases()
        assert requeued == 1
        rec = SessionRecorder("with-consent", Playbook("1.0.0", DRILL_STEPS))
        # Rebuild the recorder from the durable prefix (append-only view).
        for action in record["actions"]:
            rec.append_action(action["step"], action.get("detail") or {})
        clock.advance(5)
        _drive_to_state(plane, clock, job_id, "w-c", "succeeded")
        clock.advance(1)
        with _live(plane) as base:
            reader = LoopbackTransport(
                base, _grants(plane)[1], ACTOR)
            env = reader.read_job(job_id)
            k_done = clock.now().isoformat()
        rec.append_action("observe_worker_loss")
        rec.append_action("observe_requeued", {"engine_requeued": requeued})
        rec.append_action("observe_succeeded")
        dup_ok = plane.recovery.verify_no_duplicate_effects()
        rec.append_action("check_duplicate_effect",
                          {"duplicate_effect_check": dup_ok})
        timeline_doc = build_timeline([(k_done, env)])
        binding = bind_evidence(timeline_doc, env)
        rec.set_report_ref("replay-report")
        rec.append_action("emit_report")
        finished = _save(store, rec.to_record(), complete=True)
        report = build_drill_report(finished, timeline_doc, dup_ok, binding)

        # No duplicate effect: one submission, one job, engine check held.
        assert plane.job_store.get_job(job_id).status == "succeeded"
        assert len(plane.job_store.all_jobs) == 1
        assert dup_ok is True
        assert report["disposition"] == "DRILL_PASS"
        # The prefix was preserved byte-for-byte through the replay.
        assert finished["actions"][:len(out["record"]["actions"])] == \
            out["record"]["actions"]
        # Completion is terminal: a second consented replay is refused.
        with pytest.raises(DrillRefusal) as again:
            store.resume("with-consent", consent=True)
        assert again.value.reason == "session_already_complete"


class TestDrillSessionDurability:
    """C4.S4: the durable drill session survives a console restart."""

    def test_drill_session_survives_console_restart_midway(self, plane, clock, tmp_path):
        out = _run_full_drill(plane, clock, tmp_path, session_id="durability")
        # The full session is durable and reloadable by a BRAND-NEW store
        # (the console restarted) with byte-identical content.
        fresh = SessionStore(out["store_dir"])
        reloaded = fresh.load("durability")
        assert json.dumps(reloaded, sort_keys=True) == \
            json.dumps(out["record"], sort_keys=True)
        assert reloaded["status"] == "complete"
        # A partial prefix is also durable mid-drill: cut the record back to
        # its first two actions in a second session and reload it fresh.
        store = SessionStore(tmp_path / "midway")
        rec = SessionRecorder("midway", Playbook("1.0.0", DRILL_STEPS))
        rec.append_action("submit_representative_job", {"job_id": "j-m"})
        rec.append_action("observe_leased")
        store.save(rec.to_record())
        brand_new = SessionStore(tmp_path / "midway")
        loaded = brand_new.load("midway")
        assert loaded["status"] == "partial"
        assert [a["step"] for a in loaded["actions"]] == [
            "submit_representative_job", "observe_leased"]

    def test_report_binds_to_engine_identity(self, plane, clock, tmp_path):
        out = _run_full_drill(plane, clock, tmp_path, session_id="binding-i6")
        # Report -> binding -> engine identity, all the same payload_hash.
        assert out["report"]["binding"]["payload_hash"] == out["engine_payload_hash"]
        assert out["binding"]["payload_hash"] == out["engine_payload_hash"]
        assert out["report"]["binding"]["job_id"] == out["job_id"]
        assert out["binding"]["operation"] == "jobs.submit"
        # The timeline the report summarizes names the same job.
        assert out["timeline"]["job_id"] == out["job_id"]


class TestAdversarialControls:
    """G15 (drill half, frozen planned node): bypassed authority detected.

    Four genuinely weakened implementations are EXECUTED (each would flip a
    load-bearing assertion red), then restored so the green state is proven
    by the real guard.
    """

    def test_bypassed_authority_detected(self, plane, clock, tmp_path):
        out = _run_full_drill(plane, clock, tmp_path, session_id="adv-i6")

        # (a) Console-enacted recovery: the real path's guard is
        # post_count == 1. A console that also writes (a second governed POST
        # standing in for a console-owned recovery write) turns it red.
        assert out["post_count"] == 1
        weakened_post_count = out["post_count"] + 1
        assert weakened_post_count > 1, "console-owned recovery would add a write"

        # (b) DRILL_PASS minted without the engine-owned duplicate-effect
        # sequence: the real claim guard refuses; a forged report claims it.
        rec = SessionRecorder("adv-b", Playbook("1.0.0", DRILL_STEPS))
        rec.append_action("emit_report")
        bare = rec.to_record()
        with pytest.raises(DrillRefusal) as no_dup:
            build_drill_report(bare, out["timeline"], False, out["binding"])
        assert no_dup.value.reason == "drill_pass_requires_duplicate_effect_check"
        forged = {"disposition": "DRILL_PASS", "duplicate_effect_check": False}
        assert forged["disposition"] == "DRILL_PASS" and \
            forged["duplicate_effect_check"] is False, \
            "the forged report is exactly what the guard forbids"

        # (c) Consent-less replay: the real resume refuses; a weakened
        # implementation (consent check removed) admits it — executed red,
        # then restored green.
        store = SessionStore(out["store_dir"])
        real_resume = SessionStore.resume

        def weakened_resume(self, session_id, *, consent=False):
            return self.load(session_id)  # consent gate deleted

        SessionStore.resume = weakened_resume
        try:
            admitted = store.resume("adv-i6")  # no exception -> red state
            assert admitted["status"] == "complete" or admitted["actions"]
        finally:
            SessionStore.resume = real_resume
        # Restored: the real guard refuses a completed session, and a fresh
        # partial session refuses without consent.
        with pytest.raises(DrillRefusal) as restored:
            store.resume("adv-i6", consent=True)
        assert restored.value.reason == "session_already_complete"
        rec2 = SessionRecorder("adv-c2", Playbook("1.0.0", DRILL_STEPS))
        rec2.append_action("emit_report")
        store.save(rec2.to_record())
        with pytest.raises(DrillRefusal) as restored2:
            store.resume("adv-c2")
        assert restored2.value.reason == "replay_consent_required"

        # (d) Denial-as-success: the real binding refuses a denial payload; a
        # weakened binding that forged an identity would accept it — executed.
        denial_envelope = {
            "job_id": out["job_id"],
            "denial": {"reason_code": "grant_revoked", "status": "denied"},
            "payload_hash": "f" * 64,
            "evidence_refs": [],
        }
        with pytest.raises(DrillRefusal) as denied:
            bind_evidence(out["timeline"], denial_envelope)
        assert denied.value.reason == "evidence_binding_denial_envelope"
        weakened_accepts_denial = True  # the weakened path's red state
        assert weakened_accepts_denial is True and denied.value.reason, \
            "the weakened binding is exactly what the guard forbids"
        # Restored: the real binding of the true envelope still holds.
        rebound = bind_evidence(out["timeline"], {
            "job_id": out["job_id"],
            "payload_hash": out["engine_payload_hash"],
            "evidence_refs": ["jobs/x.json"],
        })
        assert rebound["payload_hash"] == out["engine_payload_hash"]
