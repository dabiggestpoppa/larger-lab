"""OCE B5-I8 — adversarial proofs (10 frozen planned nodes).

Each node provokes one hostile condition against the REAL client surfaces and
requires a specific refusal or containment observable. The weakened form of each
law is exercised too wherever a checker could otherwise be vacuous.
"""
from __future__ import annotations

import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import b5_i8_audit_support as S
from oce_console import kernel, panel, transport

CONSOLE_PKG = S.CONSOLE_SRC / "oce_console"

WRITE_VERBS = (
    'method="POST"',
    "method='POST'",
    'method="PUT"',
    "method='PUT'",
    'method="PATCH"',
    "method='PATCH'",
    'method="DELETE"',
    "method='DELETE'",
)


def _write_hits(text: str) -> list:
    return [verb for verb in WRITE_VERBS if verb in text]


def _engine_imports(text: str) -> list:
    return re.findall(r"^\s*(?:from|import)\s+oce_control\b", text, flags=re.M)


class TestAuthorityMinting:
    """B5I8-R12 / F13 — the client cannot mint identity, grant or truth."""

    def test_client_cannot_mint_identity_or_grant(self):
        document = S.panel_document()
        assert document["non_authoritative"] is True

        sources = {path.name: path.read_text(encoding="utf-8") for path in CONSOLE_PKG.glob("*.py")}
        assert sources
        for name, text in sources.items():
            assert _engine_imports(text) == [], f"{name} imports the engine"
        # The READ surfaces are GET-only. The console's separate governed submit
        # path (submit.py, frozen at B5-I3) is not part of this projection and is
        # never imported by it.
        for name in ("panel.py", "kernel.py", "transport.py"):
            text = (CONSOLE_PKG / name).read_text(encoding="utf-8")
            assert _write_hits(text) == [], f"{name} contains a write verb"
        assert "submit" not in (CONSOLE_PKG / "panel.py").read_text(encoding="utf-8")
        assert (CONSOLE_PKG / "submit.py").exists()
        # Discrimination: the scans actually detect a planted violation.
        assert _write_hits('urllib.request.Request(url, method="POST")')
        assert _engine_imports("from oce_control.plane import ControlPlane")

        # A supplied grant is passed through verbatim and never invented.
        bare = transport.LoopbackTransport("http://127.0.0.1:8000", surfaces=S.SURFACES)
        assert "X-OCE-Grant" not in bare._headers()
        assert "X-OCE-Actor" not in bare._headers()
        supplied = transport.LoopbackTransport(
            "http://127.0.0.1:8000",
            grant_id="grant-abc",
            actor_id="actor-1",
            surfaces=S.SURFACES,
        )
        headers = supplied._headers()
        assert headers["X-OCE-Grant"] == "grant-abc"
        assert headers["X-OCE-Actor"] == "actor-1"

        # The transport performs exactly one method: GET.
        assert 'method="GET"' in (
            CONSOLE_PKG / "transport.py"
        ).read_text(encoding="utf-8")


class TestForgedState:
    """B5I8-R13 / F03 / F15 — forged client state is refused before effect."""

    def test_forged_client_state_refused_before_effect(self):
        # A forged envelope claiming success but carrying no governed collection
        # is UNVERIFIABLE, never a success.
        forged = S.envelope(
            {"pending_jobs": 1, "active_jobs": 1, "failed_jobs": 0, "quarantined_jobs": 0},
            request_id="req-forged-1",
        )
        document = S.build(reads=S.frozen_reads(**{"workers.list": forged}))
        assert document["reads"]["workers.list"]["state"] == panel.STATE_OK
        assert document["workers"]["known"] is False
        assert document["reads"]["workers.list"]["partial"] is True
        assert document["state"] == panel.STATE_UNVERIFIABLE
        assert document["state"] != panel.STATE_OK

        # Client-supplied canonical state has no entry point at all.
        with pytest.raises(TypeError):
            panel.build_panel_document(  # type: ignore[call-arg]
                S.read_from(S.frozen_reads()), S.SURFACES, client_state={"state": "OK"}
            )

        # Refusal precedes any governed read (zero side effects).
        reads = S.frozen_reads()
        read = S.read_from(reads)
        with pytest.raises(kernel.ConsoleRefusal) as refused:
            panel.build_panel_document(
                read, S.SURFACES, surfaces_requested=["jobs.inspect"]
            )
        assert refused.value.reason == "unsupported_surface"
        assert read.calls == []

        # A malformed request is refused for its own reason, still before effect.
        with pytest.raises(kernel.ConsoleRefusal) as malformed:
            panel.build_panel_document(read, S.SURFACES, surfaces_requested="health.read")
        assert malformed.value.reason == "malformed_request"
        assert read.calls == []


class TestTruthCollapse:
    """B5I8-R14..R16 / F04 / F06 / F07 — unknown, partial and stale never collapse."""

    def test_unknown_never_renders_zero(self):
        data = {"active_jobs": 2, "failed_jobs": 0, "quarantined_jobs": 0}
        document = S.build(reads=S.frozen_reads(**{"health.read": S.envelope(data)}))
        pending = document["queue"]["pending"]
        assert pending["known"] is False
        assert pending["value"] is None
        assert pending["unknown_reason"] == "not_reported"
        assert document["queue"]["depth"]["known"] is False
        assert document["queue"]["depth"]["value"] is None
        assert document["state"] == panel.STATE_UNVERIFIABLE

        # A KNOWN zero stays a known zero: unknown is not a synonym for empty.
        zero_doc = S.build(
            reads=S.frozen_reads(
                **{
                    "health.read": S.envelope(
                        {"pending_jobs": 0, "active_jobs": 0, "failed_jobs": 0,
                         "quarantined_jobs": 0}
                    )
                }
            )
        )
        assert zero_doc["queue"]["pending"]["known"] is True
        assert zero_doc["queue"]["pending"]["value"] == 0
        assert zero_doc["queue"]["depth"]["value"] == 0
        assert zero_doc["state"] == panel.STATE_OK

    def test_partial_never_renders_success(self):
        data = {"pending_jobs": 4, "active_jobs": 1}
        document = S.build(reads=S.frozen_reads(**{"health.read": S.envelope(data)}))
        assert document["reads"]["health.read"]["partial"] is True
        assert document["queue"]["failed"]["known"] is False
        assert document["queue"]["depth"]["known"] is True  # pending+active known
        assert document["queue"]["depth"]["value"] == 5
        assert document["state"] == panel.STATE_UNVERIFIABLE
        assert document["state"] != panel.STATE_OK

    def test_stale_state_never_renders_green(self):
        stale = S.build(reads=S.frozen_reads())
        assert stale["state"] == panel.STATE_OK  # reads are intact...
        assert stale["snapshot"]["currency"] == "UNKNOWN"  # ...but not current
        assert stale["snapshot"]["currency_reason"] == "no_governed_observation_time"
        assert stale["snapshot"]["observed_at"] is None

        current = S.panel_document()
        assert current["snapshot"]["currency"] == "CURRENT"
        assert current["snapshot"]["observed_at"] == S.FIXED_OBSERVED_AT
        assert current["snapshot"]["currency_reason"] is None


class TestTransport:
    """B5I8-R17 / R18 / F12 / F14 — loopback-only, unsupported refused pre-I/O."""

    def test_non_loopback_request_fail_closed(self, monkeypatch):
        import socket

        def _boom(*args, **kwargs):  # pragma: no cover - must never run
            raise AssertionError("socket constructed for a refused URL")

        monkeypatch.setattr(socket, "socket", _boom)

        for hostile in (
            "http://0.0.0.0:8000",
            "http://192.168.1.10:8000",
            "http://localhost:8000",
            "https://127.0.0.1:8000",
            "http://[::2]:8000",
        ):
            with pytest.raises(kernel.ConsoleRefusal) as refused:
                transport.LoopbackTransport(hostile, surfaces=S.SURFACES)
            assert refused.value.reason == "non_loopback_refused", hostile

        assert transport.validate_base_url("http://127.0.0.1:8000") == "http://127.0.0.1:8000"
        assert transport.validate_base_url("http://[::1]:8000").startswith("http://[::1]")
        transport.LoopbackTransport("http://127.0.0.1:8000", surfaces=S.SURFACES)

    def test_unsupported_route_refused_before_side_effect(self, monkeypatch):
        client = transport.LoopbackTransport("http://127.0.0.1:8000", surfaces=S.SURFACES)

        def _boom(*args, **kwargs):  # pragma: no cover - must never run
            raise AssertionError("I/O attempted for an unsupported route")

        monkeypatch.setattr(transport, "_open_url", _boom)
        with pytest.raises(kernel.ConsoleRefusal) as refused:
            client.read("jobs.inspect")
        assert refused.value.reason == "unsupported_surface"
        assert "jobs.inspect" not in client.routes

        # The panel refuses the same undeclared surface before reading.
        read = S.read_from(S.frozen_reads())
        with pytest.raises(kernel.ConsoleRefusal):
            panel.build_panel_document(read, S.SURFACES, surfaces_requested=["health.write"])
        assert read.calls == []


class TestRedaction:
    """B5I8-R19 / F11 / F18 — no credential material reaches audit output."""

    def test_secret_material_absent_from_audit_output(self):
        document = S.build(reads=S.frozen_reads(**{"health.read": S.secret_envelope()}))
        text = panel.render_panel(document)

        for planted in ("PLANTED", "hunter2", "tok-PLANTED-abc123", "Bearer PLANTED"):
            assert planted not in text, f"secret survived: {planted}"
        assert panel.REDACTED in text
        assert document["reads"]["health.read"]["response"]["error"] == ""

class TestBounds:
    """B5I8-R20 / F08 / F09 — bounded input and bounded collection width."""

    def test_oversized_input_refused_within_bounds(self):
        # Excessive collection width is truncated WITH an explicit marker.
        ids = [f"w-{index:03d}" for index in range(100)]
        document = S.build(
            reads=S.frozen_reads(
                **{"workers.list": S.envelope({"workers": {key: {} for key in ids}})}
            )
        )
        workers = document["workers"]
        assert workers["known"] is True
        assert workers["count"]["value"] == 100
        assert workers["truncated"] is True
        assert len(workers["ids"]) == panel.MAX_COLLECTION_ITEMS == 64
        assert workers["bound"] == 64
        assert workers["ids"] == sorted(workers["ids"])[:64]

        # An over-wide request is refused before any read.
        read = S.read_from(S.frozen_reads())
        with pytest.raises(kernel.ConsoleRefusal) as too_many:
            panel.build_panel_document(
                read,
                S.SURFACES,
                surfaces_requested=list(S.SURFACES) * 3,
            )
        assert too_many.value.reason in {"payload_too_large", "duplicate_surface"}
        assert read.calls == []

        # An over-bound string identity is refused, never truncated silently.
        huge = "r" * (panel.MAX_STRING_BYTES + 1)
        with pytest.raises(kernel.ConsoleRefusal) as over_bound:
            S.build(reads=S.frozen_reads(**{"health.read": S.envelope(S.healthy_data(), request_id=huge)}))
        assert over_bound.value.reason == "payload_too_large"


class TestDeterminism:
    """B5I8-R21 / F10 — permuted equivalent input yields identical bytes."""

    def test_adversarial_case_ordering_deterministic(self):
        baseline = S.panel_text()

        permuted_reads = dict(reversed(list(S.frozen_reads().items())))
        permuted = panel.render_panel(
            panel.build_panel_document(
                S.read_from(permuted_reads), S.SURFACES, observed_at=S.FIXED_OBSERVED_AT
            )
        )
        assert permuted == baseline

        ids_a = [f"w-{index}" for index in range(12)]
        ids_b = list(reversed(ids_a))
        doc_a = S.build(
            reads=S.frozen_reads(
                **{"workers.list": S.envelope({"workers": {key: {} for key in ids_a}})}
            )
        )
        doc_b = S.build(
            reads=S.frozen_reads(
                **{"workers.list": S.envelope({"workers": {key: {} for key in ids_b}})}
            )
        )
        assert panel.render_panel(doc_a) == panel.render_panel(doc_b)
        assert doc_a["workers"]["ids"] == doc_b["workers"]["ids"] == sorted(ids_a)

        # Ordering does not erase distinct content: a different case set differs.
        changed = S.build(
            reads=S.frozen_reads(
                **{"workers.list": S.envelope({"workers": {"w-999": {}}})}
            )
        )
        assert panel.render_panel(changed) != baseline
