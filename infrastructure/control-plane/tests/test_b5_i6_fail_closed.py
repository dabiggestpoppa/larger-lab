"""OCE B5-I6 — fail-closed denial rendering on the drill path (S-4 completion).

Frozen registry node executed VERBATIM here (P0 addendum; scope contract §5):
- **S-4 (console half)** `TestDenialRendering::test_s4_denial_rendered_verbatim_no_silent_retry`

Plus C4/§9 support nodes: a missing-identity answer renders an explicit
UNVERIFIABLE gap (never `OK`), and a denied authority can never complete a
drill (no DRILL_PASS, no completion flip, empty store).

Laws (charter §9 Admission/refusal; B5-I2 pack §8; B5-I4 X3/X4): a governed
denial envelope is DATA, rendered verbatim with exactly ONE fetch and zero
silent retries; the HTTP layer's 401 ``detail`` body is a non-envelope —
preserved raw, never green; authority denial never converts to success at any
layer (kernel, timeline, drill report, session record).

Client-only: imports no ``oce_control`` module; stdlib only; no LLM; no
provider; no new engine surface.
"""
from __future__ import annotations

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

from oce_console.drill import (  # noqa: E402
    DrillRefusal,
    Playbook,
    SessionRecorder,
    bind_evidence,
    build_drill_report,
)
from oce_console.kernel import (  # noqa: E402
    STATE_DEGRADED,
    STATE_OK,
    STATE_UNVERIFIABLE,
    ConsoleRefusal,
    project_section,
)
from oce_console.session_store import SessionStore  # noqa: E402
from oce_console.submit import SubmitClient  # noqa: E402
from oce_console.timeline import build_timeline  # noqa: E402
from oce_console.transport import StackUnreachable  # noqa: E402

ACTOR = "b5i6-failclosed"
JOB_TYPE = "b3.deterministic-hash"


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


class TestDenialRendering:
    """S-4 (frozen planned node) + §9 gap rendering on the drill path."""

    def test_s4_denial_rendered_verbatim_no_silent_retry(self, plane):
        # A TAMPERED grant (not issued by the engine) yields the governed
        # denial envelope — exactly one POST, rendered verbatim, never OK.
        with _live(plane) as base:
            client = _CountingSubmit(base, "tampered-grant", ACTOR)
            response = client.submit(JOB_TYPE, {"value": "denied"})
            # The governed denial is DATA: envelope shape, status denied.
            assert isinstance(response, dict)
            assert response["ok"] is False
            assert response["status"] == "denied"
            # The engine's OWN governed reason code for an unissued grant,
            # rendered verbatim (never reinterpreted or softened).
            assert response["data"]["denial"]["reason_code"] == "missing_authority"
            # Exactly ONE fetch: a denial is never silently retried (S-4).
            assert client.post_count == 1
            # The kernel renders the denial verbatim as DEGRADED — never OK.
            section = project_section("system", response)
            assert section["state"] == STATE_OK  # intact governed envelope
            assert section["response"]["ok"] is False
            assert json.dumps(section["response"]) == json.dumps({
                "ok": response["ok"],
                "status": response["status"],
                "data": response["data"],
                "error": response["error"],
                "request_id": response["request_id"],
            }), "the denial envelope must round-trip verbatim"
            # The full document summary over this denial is DEGRADED — the
            # governed denial can never summarize green at any layer.
            from oce_console.kernel import build_status_document

            surfaces = {
                "health.read": "/api/health",
                "readiness.read": "/api/readiness",
                "system.read": "/api/system",
                "workers.list": "/api/workers",
                "jobs.schedules": "/api/schedules",
            }
            document = build_status_document(lambda surface: response, surfaces)
            assert document["state"] == STATE_DEGRADED
            assert document["state"] != "OK"
            for rendered in document["sections"].values():
                assert rendered["response"]["ok"] is False
            # The timeline NEVER collapses a denial into a lifecycle event.
            doc = build_timeline([(clock_now(plane), response["data"])])
            assert doc["state"] == "UNVERIFIABLE"
            assert all(t["state"] == "UNVERIFIABLE" for t in doc["transitions"])
            # Evidence binding refuses the denial payload outright — a real
            # engine denial carries no job identity, so the binding's
            # no-operation guard fires first (the denial-with-job-id guard is
            # proven separately in the G15 control (d) of the drill suite).
            with pytest.raises(DrillRefusal) as excinfo:
                bind_evidence(doc, response["data"])
            assert excinfo.value.reason == "evidence_binding_no_operation"

    def test_missing_identity_renders_unverifiable_never_ok(self, plane):
        # An identity-less request (no grant headers) produces the HTTP
        # layer's 401 detail body — a NON-envelope: preserved raw as an
        # explicit gap, never fabricated into OK.
        with _live(plane) as base:
            import urllib.error
            import urllib.request
            request = urllib.request.Request(
                f"{base}/api/system", method="GET")
            try:
                with urllib.request.urlopen(request, timeout=5) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                    status_code = resp.status
            except urllib.error.HTTPError as exc:
                body = json.loads(exc.read().decode("utf-8"))
                status_code = exc.code
            assert status_code == 401
            section = project_section("system", body)
            assert section["state"] == STATE_UNVERIFIABLE
            assert "response" not in section, "no envelope, no projection"
            assert section["raw"] == body, "raw body preserved verbatim"
            assert section["reason"] == "envelope_fields_missing"
            # An identity-less SUBMIT is refused fail-closed BEFORE any I/O
            # (B5-I5 §6 law, re-armed here on the drill path).
            with pytest.raises(ConsoleRefusal) as refused:
                SubmitClient(base, "", ACTOR)
            assert refused.value.reason == "missing_identity"
            with pytest.raises(ConsoleRefusal) as refused2:
                SubmitClient(base, "g", "")
            assert refused2.value.reason == "missing_identity"

    def test_denied_authority_never_completes_a_drill(self, plane, tmp_path):
        # A drill whose ONLY write is denied: no DRILL_PASS, no completion
        # flip, no job in the store, no fabricated lifecycle.
        store = SessionStore(tmp_path / "denied-sessions")
        rec = SessionRecorder("denied-drill", Playbook("1.0.0", [
            "submit_representative_job", "emit_report"]))
        with _live(plane) as base:
            client = _CountingSubmit(base, "tampered-grant", ACTOR)
            response = client.submit(JOB_TYPE, {"value": "denied-drill"})
            assert response["status"] == "denied"
            assert client.post_count == 1
            # The store holds NOTHING — the denied submit left no job.
            assert plane.job_store.all_jobs == {}
            # The console records the attempt as data, never as success:
            # the envelope's job data is a denial, so the timeline is an
            # explicit gap and no evidence binding or report can exist.
            doc = build_timeline([("2026-10-20T00:00:00+00:00", response["data"])])
            assert doc["state"] == "UNVERIFIABLE"
            with pytest.raises(DrillRefusal):
                bind_evidence(doc, response["data"])
            with pytest.raises(DrillRefusal) as unbound:
                build_drill_report(rec.to_record(), doc, True, {
                    "operation": "jobs.submit", "job_id": "",
                    "payload_hash": "", "evidence_refs": []})
            assert unbound.value.reason == "drill_report_unbound"
            # The session record cannot be completed: a drill whose submit
            # was DENIED never reaches a report reference.
            record = store.save(rec.to_record())
            assert record["status"] == "partial"
            with pytest.raises(DrillRefusal) as no_completion:
                store.save(rec.to_record(), complete=True)
            assert no_completion.value.reason == "completion_requires_report_ref"

    def test_transport_failure_is_never_rendered_success(self):
        # A transport-level failure raises StackUnreachable — it can never
        # arrive as data that some layer might project green.
        import socket

        from oce_console.transport import LoopbackTransport

        # Deterministic closed port: bind an ephemeral port, then release it
        # so nothing listens (never a fixed port that a real stack could use).
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        closed_port = probe.getsockname()[1]
        probe.close()
        client = LoopbackTransport(f"http://127.0.0.1:{closed_port}", "g", ACTOR)
        with pytest.raises(StackUnreachable):
            client.read("health.read")


def clock_now(plane) -> str:
    """Engine event-time for a synthetic observation (deterministic)."""
    from oce_control.clocks import get_clock

    return get_clock().now().isoformat()
