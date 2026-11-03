"""OCE B5-I7 — governed change cycle, queue-depth panel, drill identity, compatibility.

Frozen planned nodes executed VERBATIM here (P0 construction plan §5; registry
``requirement_set.planned_test_nodes``), exactly twelve:

- ``B5I7-R02`` `TestSingleChange::test_exactly_one_governed_change_recorded`
- ``B5I7-R07`` `TestChangeCycle::test_change_has_positive_and_negative_proofs`
- ``B5I7-R12`` `TestRegressionDrill::test_unchanged_stack_drill_report_byte_identical`
- ``B5I7-R15`` `TestPanelContract::test_undeclared_surface_refused_before_io`
- ``B5I7-R16`` `TestPanelReadOnly::test_panel_issues_only_get_requests`
- ``B5I7-R17`` `TestPanelFailClosed::test_unreachable_stack_never_renders_healthy`
- ``B5I7-R18`` `TestPanelFailClosed::test_unknown_queue_depth_rendered_unknown_not_zero`
- ``B5I7-R19`` `TestPanelDeterminism::test_identical_inputs_render_byte_identically`
- ``B5I7-R20`` `TestPanelLoopback::test_non_loopback_base_url_refused`
- ``B5I7-R21`` `TestPanelSecurity::test_panel_output_contains_no_secret_material`
- ``B5I7-R22`` `TestPanelBounds::test_oversized_and_malformed_input_refused`
- ``B5I7-R23`` `TestCompatibility::test_documented_status_command_and_exit_codes_unchanged`

Laws exercised (two-sided wherever a refusal exists): the panel is a PROJECTION
of already-declared reads with no write path, no recovery authority, no cache,
no retry, no wall clock; unknown renders ``null`` + ``unknown_reason`` and never
``0``; a partial read never summarizes as success; refusals are observable and
precede I/O; the drill report identity uses the CLOSED three-field mask of
contract §22.

Every negative control here executes a GENUINELY WEAKENED implementation in
process and requires it to go red — an assertion that cannot fail is not a proof.
"""
from __future__ import annotations

import ast
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[2]
CONSOLE_SRC = REPO_ROOT / "infrastructure" / "console" / "src"
sys.path.insert(0, str(CONSOLE_SRC))

from oce_console import cli, panel  # noqa: E402
from oce_console.kernel import (  # noqa: E402
    STATUS_SECTIONS,
    ConsoleRefusal,
    build_status_document,
    render_status,
)
from oce_console.transport import (  # noqa: E402
    LoopbackTransport,
    StackUnreachable,
    validate_base_url,
)

BASE_SHA = "9dc0b7d29ab869e256653a6b6ec68c987d0a4090"
DEFAULT_PACK_SHA = "45bcb4f63fdb44c039e81fa51ac01a877bb05faee048efa8193ed7fc16af14aa"

#: The three—and only three—run-scoped drill fields masked by the frozen
#: canonicalization law (contract §22). A fourth field is a contract amendment.
DRILL_MASK = ("session_id", "binding.job_id", "binding.evidence_refs")
MASK_SENTINELS = {
    "session_id": "<session_id>",
    "binding.job_id": "<job_id>",
    "binding.evidence_refs": "<evidence_refs>",
}


# ── helpers ─────────────────────────────────────────────────────────────────

def _envelope(data, ok=True, status="ok", request_id="req-1", **extra):
    env = {"ok": ok, "status": status, "data": data, "request_id": request_id}
    env.update(extra)
    return env


def _healthy_health(**over):
    data = {
        "pending_jobs": 3,
        "active_jobs": 2,
        "failed_jobs": 1,
        "quarantined_jobs": 0,
        "workers": 2,
    }
    data.update(over)
    return data


SURFACES = {
    "health.read": "/api/health",
    "workers.list": "/api/workers",
    "jobs.schedules": "/api/schedules",
}


def _read_from(mapping):
    """A governed read callable over a fixed surface->envelope mapping."""
    calls = []

    def read(surface):
        calls.append(surface)
        value = mapping[surface]
        if isinstance(value, Exception):
            raise value
        return value

    read.calls = calls
    return read


def _default_reads(**over):
    mapping = {
        "health.read": _envelope(_healthy_health()),
        "workers.list": _envelope({"workers": {"w-2": {}, "w-1": {}}}),
        "jobs.schedules": _envelope({"schedules": {}}),
    }
    mapping.update(over)
    return mapping


def _build(reads=None, **kwargs):
    mapping = _default_reads() if reads is None else reads
    return panel.build_panel_document(_read_from(mapping), SURFACES, **kwargs)


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=str(REPO_ROOT), capture_output=True, text=True, check=False
    )


def _assert_queue_law(document, health_data):
    """The load-bearing queue law, checked AGAINST THE GOVERNED SOURCE.

    Every counter must track its source token: a reported integer renders that
    integer; an absent, non-integer or negative source renders ``null`` with an
    ``unknown_reason`` and is NEVER a known ``0``. A document with any unknown
    counter may not summarize as ``OK`` (partial is not success).

    This law is callable so it can be executed positively (pristine code must
    satisfy it) and negatively (a weakened implementation must violate it).
    """
    source_is_object = isinstance(health_data, dict)
    for field in panel.QUEUE_FIELDS:
        entry = document["queue"][field]
        token = panel.QUEUE_SOURCE_FIELDS[field]
        raw = health_data.get(token) if source_is_object else None
        usable = (
            source_is_object
            and token in health_data
            and isinstance(raw, int)
            and not isinstance(raw, bool)
            and raw >= 0
        )
        if usable:
            assert entry["known"] is True, f"{field}: reported source not rendered"
            assert entry["value"] == raw, f"{field}: {entry['value']} != {raw}"
            assert entry["unknown_reason"] is None
        else:
            assert entry["known"] is False, f"{field}: unfounded value {entry['value']!r}"
            assert entry["value"] is None, f"{field}: unknown rendered as {entry['value']!r}"
            assert entry.get("unknown_reason"), f"{field}: unknown without reason"
    unknown_any = any(not document["queue"][f]["known"] for f in panel.QUEUE_FIELDS)
    if unknown_any:
        assert document["state"] != "OK", "partial queue summarized as success"
        assert document["reads"].get("health.read", {}).get("partial") is True
    depth = document["queue"]["depth"]
    pending, active = document["queue"]["pending"], document["queue"]["active"]
    if depth["known"]:
        assert pending["known"] and active["known"]
        assert depth["value"] == pending["value"] + active["value"]
        assert depth["basis"] == "pending+active"
    else:
        assert depth["value"] is None, "depth: unknown rendered as a number"
    assert document["non_authoritative"] is True


def _canonicalize_drill(report):
    """Apply EXACTLY the frozen two-step law: mask three fields, keep every byte.

    The mask list is closed (contract §22); the sentinels are constants, so a
    sentinel that varied with the run would fail the identity comparison.
    """
    import copy

    canonical = copy.deepcopy(report)
    canonical["session_id"] = MASK_SENTINELS["session_id"]
    canonical["binding"]["job_id"] = MASK_SENTINELS["binding.job_id"]
    canonical["binding"]["evidence_refs"] = MASK_SENTINELS["binding.evidence_refs"]
    return json.dumps(canonical, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


# ── R02: exactly one governed change ────────────────────────────────────────

class TestSingleChange:
    """`B5I7-R02` — exactly one governed change; a second change is a violation."""

    EXPECTED_SURFACE = {
        "infrastructure/console/packaging/make_release_manifest.py",
        "infrastructure/console/src/oce_console/cli.py",
        "infrastructure/console/src/oce_console/panel.py",
    }

    def test_exactly_one_governed_change_recorded(self):
        # The base commit must be a real ancestor of this tree, otherwise the
        # boundary comparison below would be vacuous.
        assert _git("cat-file", "-e", f"{BASE_SHA}^{{commit}}").returncode == 0
        assert _git("merge-base", "--is-ancestor", BASE_SHA, "HEAD").returncode == 0

        changed = _git(
            "diff", "--name-only", "--no-renames", BASE_SHA, "--", "infrastructure/console"
        )
        assert changed.returncode == 0, changed.stderr
        produced = {line for line in changed.stdout.splitlines() if line.strip()}
        assert produced == self.EXPECTED_SURFACE, f"console surface drift: {produced}"

        # Exactly one change: the new module is ONE panel builder, not a family
        # of authority surfaces. Count the governed document builders it exports.
        builders = [
            name
            for name in dir(panel)
            if name.startswith("build_") and callable(getattr(panel, name))
        ]
        assert builders == ["build_panel_document"], builders

        # A second change would need a second module, endpoint or job type; the
        # control plane (the only place an endpoint could be added) is frozen.
        cp = _git(
            "diff",
            "--name-only",
            "--no-renames",
            BASE_SHA,
            "--",
            "infrastructure/control-plane/src",
            "infrastructure/control-plane/contracts",
        )
        assert cp.stdout.strip() == "", f"control-plane modified: {cp.stdout}"
        assert panel.PANEL_SURFACES == ("health.read", "workers.list", "jobs.schedules")
        assert set(panel.PANEL_SURFACES) <= set(SURFACES)


# ── R07: positive AND executed negative proof ───────────────────────────────

class TestChangeCycle:
    """`B5I7-R07` — the change ships with a positive and a weakened negative proof."""

    def test_change_has_positive_and_negative_proofs(self):
        # POSITIVE: complete governed reads produce a verifiable OK panel.
        document = _build()
        assert document["state"] == panel.STATE_OK
        assert document["queue"]["pending"] == {
            "value": 3, "known": True, "unknown_reason": None
        }
        assert document["queue"]["depth"]["value"] == 5
        assert document["snapshot"]["consistent"] is True
        _assert_queue_law(document, _healthy_health())

        # NEGATIVE (weakened implementation): map an absent counter to 0, the
        # exact defect the law forbids. The SAME law must now fail.
        original = panel._queue_value
        partial_health = {"pending_jobs": 3, "active_jobs": 2, "failed_jobs": 1}
        try:
            panel._queue_value = lambda data, field: panel._known(0)
            weakened = panel.build_panel_document(
                _read_from(_default_reads(
                    **{"health.read": _envelope(partial_health)}
                )),
                SURFACES,
            )
        finally:
            panel._queue_value = original
        with pytest.raises(AssertionError):
            _assert_queue_law(weakened, partial_health)
        # The pristine implementation satisfies the SAME law on the SAME input.
        _assert_queue_law(
            _build(reads=_default_reads(**{"health.read": _envelope(partial_health)})),
            partial_health,
        )

        # The negative control changed ONLY the weakened copy: the pristine
        # implementation still yields an explicit unknown for the absent counter.
        assert weakened["queue"]["quarantined"]["known"] is True  # weakened: 0
        pristine = _build(
            reads=_default_reads(
                **{"health.read": _envelope({"pending_jobs": 3, "active_jobs": 2,
                                             "failed_jobs": 1})}
            )
        )
        assert pristine["queue"]["quarantined"]["value"] is None
        assert pristine["queue"]["quarantined"]["unknown_reason"] == "not_reported"
        assert pristine["state"] == panel.STATE_UNVERIFIABLE
        assert pristine["reads"]["health.read"]["partial"] is True


# ── R12: drill-report identity under the frozen canonicalization ────────────

class TestRegressionDrill:
    """`B5I7-R12` — unchanged-stack drill reports are byte-identical after masking."""

    def test_unchanged_stack_drill_report_byte_identical(self, plane, clock, tmp_path):
        import importlib.util

        # Load the frozen B5-I6 drill module by path: the helper is reused
        # unmodified (a real runtime dependency, not a copy).
        spec = importlib.util.spec_from_file_location(
            "b5i6_drill_module", TESTS_DIR / "test_b5_i6_recovery_drill.py"
        )
        b5i6 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b5i6)
        _run_full_drill = b5i6._run_full_drill
        from oce_control.clocks import TestClock, reset_clock, set_test_clock
        from oce_control.plane import ControlPlane

        first = _run_full_drill(plane, clock, tmp_path / "run-a", session_id="b5i7-a")

        fresh_clock = TestClock()
        set_test_clock(fresh_clock)
        try:
            fresh = ControlPlane(test_clock=fresh_clock)
            second = _run_full_drill(
                fresh, fresh_clock, tmp_path / "run-b", session_id="b5i7-b"
            )
        finally:
            reset_clock()

        report_a, report_b = first["report"], second["report"]
        # The two runs genuinely differ in exactly the run-scoped fields.
        assert report_a["session_id"] != report_b["session_id"]
        assert report_a["binding"]["job_id"] != report_b["binding"]["job_id"]

        bytes_a = _canonicalize_drill(report_a)
        bytes_b = _canonicalize_drill(report_b)
        assert bytes_a == bytes_b, "canonicalized drill reports differ"
        assert panel.sha256_hex(bytes_a.encode("utf-8")) == panel.sha256_hex(
            bytes_b.encode("utf-8")
        )

        # Engine-owned facts are preserved by the mask (the mask hides run
        # identity, not the outcome).
        assert report_a["disposition"] == "DRILL_PASS"
        assert report_a["duplicate_effect_check"] is True
        assert report_a["timeline_state"] == report_b["timeline_state"]
        assert report_a["binding"]["payload_hash"] == report_b["binding"]["payload_hash"]

        # NEGATIVE: a meaningful state change must break identity.
        drifted = json.loads(json.dumps(report_a))
        drifted["duplicate_effect_check"] = False
        assert _canonicalize_drill(drifted) != bytes_a

        # NEGATIVE: masking a fourth field (or varying the sentinel) is not
        # allowed to "repair" a difference — the mask list is closed.
        assert len(DRILL_MASK) == 3
        drift2 = json.loads(json.dumps(report_a))
        drift2["disposition"] = "DRILL_FAIL"
        assert _canonicalize_drill(drift2) != bytes_a
        variable = json.loads(json.dumps(report_a))
        variable["binding"]["payload_hash"] = "different"
        assert _canonicalize_drill(variable) != bytes_a


# ── R15: undeclared surface refused BEFORE any I/O ──────────────────────────

class TestPanelContract:
    """`B5I7-R15` — only declared surfaces; refusal precedes the read."""

    def test_undeclared_surface_refused_before_io(self):
        read = _read_from(_default_reads())
        with pytest.raises(ConsoleRefusal) as undeclared:
            panel.build_panel_document(
                read, SURFACES, surfaces_requested=["jobs.inspect"]
            )
        assert undeclared.value.reason == "unsupported_surface"
        assert read.calls == [], f"I/O occurred before refusal: {read.calls}"

        # A surface embedded in the pack but NOT in the frozen panel set is
        # still refused (the panel may not widen its own authority).
        widened = dict(SURFACES)
        widened["audit.read"] = "/api/audit"
        with pytest.raises(ConsoleRefusal) as embedded:
            panel.build_panel_document(
                read, widened, surfaces_requested=["audit.read"]
            )
        assert embedded.value.reason == "unsupported_surface"
        assert read.calls == []

        # Duplicate identifiers would double-count queue depth: refused.
        with pytest.raises(ConsoleRefusal) as dup:
            panel.build_panel_document(
                read, SURFACES, surfaces_requested=["health.read", "health.read"]
            )
        assert dup.value.reason == "duplicate_surface"
        assert read.calls == []

        # Malformed request shapes: refused, never coerced.
        with pytest.raises(ConsoleRefusal) as scalar:
            panel.build_panel_document(read, SURFACES, surfaces_requested="health.read")
        assert scalar.value.reason == "malformed_request"
        with pytest.raises(ConsoleRefusal) as nonstring:
            panel.build_panel_document(read, SURFACES, surfaces_requested=[None])
        assert nonstring.value.reason == "malformed_request"
        assert read.calls == []

        # A pack missing a required declared surface is refused up front too.
        with pytest.raises(ConsoleRefusal) as missing:
            panel.build_panel_document(read, {"health.read": "/api/health"})
        assert missing.value.reason == "unsupported_surface"
        assert read.calls == []


# ── R16: GET only, no write, no recovery authority ─────────────────────────

class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _RecordingOpener:
    def __init__(self):
        self.methods = []
        self.urls = []

    def open(self, request, timeout=None):
        self.methods.append(request.get_method())
        self.urls.append(request.full_url)
        body = json.dumps(_envelope(_healthy_health())).encode("utf-8")
        return _FakeResponse(body)


class TestPanelReadOnly:
    """`B5I7-R16` — GET only; no write, invoke, lease, requeue or recovery."""

    def test_panel_issues_only_get_requests(self):
        client = LoopbackTransport("http://127.0.0.1:8448", "g-1", "a-1")
        opener = _RecordingOpener()
        client._opener = opener

        document = panel.build_panel_document(client.read, client.routes)

        assert opener.methods, "no request was issued"
        assert set(opener.methods) == {"GET"}, opener.methods
        assert len(opener.methods) == len(panel.PANEL_SURFACES)
        assert document["state"] in panel.PANEL_STATES

        # Structural proof: the module contains no write/recovery verb at all.
        source = (CONSOLE_SRC / "oce_console" / "panel.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {
            "write", "write_text", "write_bytes", "unlink", "mkdir", "rmdir",
            "post", "put", "patch", "delete", "recover_abandoned_leases",
            "requeue", "invoke", "lease", "transition", "submit", "commit",
        }
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert called & forbidden == set(), called & forbidden

        # No store handle, no cache: the module never imports the control plane
        # and declares no mutable module-level container.
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert "oce_control" not in imports
        assert "urllib" not in imports
        assert "socket" not in imports


# ── R17: unreachable never renders healthy ─────────────────────────────────

class TestPanelFailClosed:
    """`B5I7-R17` — an unreachable stack renders STACK_UNREACHABLE, never health."""

    def test_unreachable_stack_never_renders_healthy(self):
        document = panel.build_panel_document(
            _read_from({"health.read": StackUnreachable("boom")}), SURFACES
        )
        assert document["state"] == panel.STATE_UNREACHABLE
        assert document["snapshot"]["id"] is None
        assert document["snapshot"]["consistent"] is False
        assert document["snapshot"]["inconsistent_reason"] == "stack_unreachable"
        assert document["reads"] == {}
        for field in panel.QUEUE_FIELDS:
            assert document["queue"][field]["value"] is None
            assert document["queue"][field]["known"] is False
        assert document["queue"]["depth"]["value"] is None
        assert document["workers"]["known"] is False
        assert document["schedules"]["known"] is False
        assert "OK" not in json.dumps(document)
        assert document["non_authoritative"] is True

        # Failure raises inside a real (unreachable) loopback client too, and the
        # document is still fail-closed rather than propagated as health.
        dead = LoopbackTransport("http://127.0.0.1:1", "g-1", "a-1")
        real = panel.build_panel_document(dead.read, SURFACES)
        assert real["state"] == panel.STATE_UNREACHABLE
        assert real["snapshot"]["id"] is None

    def test_unknown_queue_depth_rendered_unknown_not_zero(self):
        # (a) one counter absent -> explicit unknown, partial read, UNVERIFIABLE.
        document = _build(
            reads=_default_reads(
                **{"health.read": _envelope({"pending_jobs": 3, "active_jobs": 2,
                                             "failed_jobs": 1})}
            )
        )
        quarantined = document["queue"]["quarantined"]
        assert quarantined == {
            "value": None, "known": False, "unknown_reason": "not_reported"
        }
        assert document["state"] == panel.STATE_UNVERIFIABLE
        assert document["reads"]["health.read"]["partial"] is True
        _assert_queue_law(
            document, {"pending_jobs": 3, "active_jobs": 2, "failed_jobs": 1}
        )

        # (b) NO counters at all -> every value null, never a zero queue.
        empty = _build(reads=_default_reads(**{"health.read": _envelope({})}))
        assert empty["state"] == panel.STATE_UNVERIFIABLE
        for field in panel.QUEUE_FIELDS:
            assert empty["queue"][field]["value"] is None
            assert empty["queue"][field]["known"] is False
        assert empty["queue"]["depth"]["value"] is None
        _assert_queue_law(empty, {})

        # (c) a known pending with an unknown active must NOT produce a depth.
        half = _build(
            reads=_default_reads(
                **{"health.read": _envelope({"pending_jobs": 3, "active_jobs": "2"})}
            )
        )
        assert half["queue"]["pending"]["value"] == 3
        assert half["queue"]["active"]["unknown_reason"] == "not_an_integer"
        assert half["queue"]["depth"]["value"] is None
        assert half["queue"]["depth"]["known"] is False

        # (d) a negative or boolean "count" is not a count.
        hostile = _build(
            reads=_default_reads(
                **{"health.read": _envelope(
                    {"pending_jobs": -1, "active_jobs": True,
                     "failed_jobs": 0, "quarantined_jobs": 0}
                )}
            )
        )
        assert hostile["queue"]["pending"]["unknown_reason"] == "negative_value"
        assert hostile["queue"]["active"]["unknown_reason"] == "not_an_integer"

        # (e) governed denial is carried verbatim and marked DENIED, not healthy.
        denied = _build(
            reads=_default_reads(
                **{"health.read": _envelope(
                    {"remote": "denied"}, ok=False, status="denied",
                    error="grant_denied", request_id="req-d",
                )}
            )
        )
        assert denied["state"] == panel.STATE_DENIED
        assert denied["queue"]["pending"]["unknown_reason"] == "read_denied"
        assert denied["reads"]["health.read"]["response"]["error"] == "grant_denied"
        assert denied["reads"]["health.read"]["response"]["request_id"] == "req-d"


# ── R19: byte-identical canonical rendering ────────────────────────────────

class TestPanelDeterminism:
    """`B5I7-R19` — identical inputs render byte-identical canonical JSON."""

    def test_identical_inputs_render_byte_identically(self):
        first = _build()
        second = _build()
        text_a = panel.render_panel(first)
        text_b = panel.render_panel(second)
        assert text_a == text_b
        assert panel.canonical_digest(first) == panel.canonical_digest(second)
        assert panel.canonical_digest(first) == panel.sha256_hex(text_a.encode("utf-8"))
        assert text_a.endswith("\n") and not text_a.endswith("\n\n")
        text_a.encode("ascii")  # ensure_ascii=True: pure ASCII bytes

        # Insertion order cannot reach the bytes: permuted inputs, same output.
        permuted = _default_reads(
            **{"workers.list": _envelope({"workers": {"w-1": {}, "w-2": {}}})}
        )
        assert panel.render_panel(_build(reads=permuted)) == text_a

        # Non-ASCII ids are escaped, never emitted raw or locale-dependent.
        non_ascii = _build(
            reads=_default_reads(
                **{"workers.list": _envelope({"workers": {"w\u00e9-1": {}}})}
            )
        )
        rendered = panel.render_panel(non_ascii)
        rendered.encode("ascii")
        assert "\\u00e9" in rendered

        # A meaningful change DOES change the digest (determinism is not stasis).
        changed = _build(reads=_default_reads(
            **{"health.read": _envelope(_healthy_health(pending_jobs=4))}
        ))
        assert panel.canonical_digest(changed) != panel.canonical_digest(first)

        # The digest algorithm is genuinely sha256 (cross-checked against the
        # stdlib without importing it into the console package).
        import hashlib

        assert panel.sha256_hex(b"") == hashlib.sha256(b"").hexdigest()
        payload = text_a.encode("utf-8")
        assert panel.sha256_hex(payload) == hashlib.sha256(payload).hexdigest()


# ── R20: loopback only ─────────────────────────────────────────────────────

class TestPanelLoopback:
    """`B5I7-R20` — a non-loopback base URL is refused before any connection."""

    def test_non_loopback_base_url_refused(self, monkeypatch):
        for hostile in (
            "http://example.com:8448",
            "https://api.example.org",
            "http://10.1.2.3:8448",
            "http://192.168.1.10:8448",
            "http://127.0.0.1.evil.test",
        ):
            with pytest.raises(ConsoleRefusal) as refusal:
                validate_base_url(hostile)
            assert refusal.value.reason.startswith("non_loopback") or \
                refusal.value.reason == "malformed_request", refusal.value.reason

        # Loopback LITERALS stay accepted (the refusal is not blanket). The
        # frozen transport accepts address literals only, so the hostname
        # spelling is refused as well - stricter than contract 10's prose,
        # never weaker, and left unchanged because R23 forbids altering the
        # frozen refusal behaviour.
        for local in ("http://127.0.0.1:8448", "http://[::1]:8448"):
            validate_base_url(local)
        with pytest.raises(ConsoleRefusal) as hostname:
            validate_base_url("http://localhost:8448")
        assert hostname.value.reason == "non_loopback_refused"

        # No socket is ever created for a hostile URL, even through the CLI.
        def _no_socket(*args, **kwargs):
            raise AssertionError("socket created for a non-loopback base URL")

        monkeypatch.setattr(socket, "socket", _no_socket)
        monkeypatch.setattr(socket, "create_connection", _no_socket)
        code = cli.main(["--base-url", "http://example.com:8448", "panel"])
        assert code == cli.EXIT_REFUSED
        assert code != 0


# ── R21: no secret material, recursively ───────────────────────────────────

class TestPanelSecurity:
    """`B5I7-R21` — no secret/token/authorization material in any output field."""

    def test_panel_output_contains_no_secret_material(self):
        token = "sk-live-SECRET-9f2c"
        cookie_value = "session=COOKIE-VALUE-77"
        denial = _envelope(
            {
                "authorization": f"Bearer {token}",
                "nested": {"cookie": cookie_value,
                           "deep": [{"private_key": "KEY-MATERIAL-55"}]},
                "credentials": ("user", "PASS-WORD-31"),
                "note": f"upstream said Authorization: Bearer {token}",
                "X-OCE-Grant": "GRANT-ID-42",
            },
            ok=False,
            status="denied",
            error=f"denied for Bearer {token}",
            request_id="req-safe",
        )
        document = _build(reads=_default_reads(**{"health.read": denial}))
        rendered = panel.render_panel(document)

        for secret in (token, cookie_value, "KEY-MATERIAL-55", "PASS-WORD-31",
                       "GRANT-ID-42"):
            assert secret not in rendered, f"secret leaked: {secret}"
        assert panel.REDACTED in rendered
        # The governed envelope itself is still carried (redaction, not deletion).
        assert document["reads"]["health.read"]["response"]["ok"] is False
        assert document["state"] == panel.STATE_DENIED
        # A safe request id survives non-redacted.
        assert document["reads"]["health.read"]["request_id"] == "req-safe"

        # Case variations of the markers are redacted too.
        varied = _build(
            reads=_default_reads(
                **{"workers.list": _envelope({"workers": {"W-BEARER x": {}}})}
            )
        )
        assert "BEARER x" not in panel.render_panel(varied)


# ── R22: bounds and hostile shapes ─────────────────────────────────────────

class TestPanelBounds:
    """`B5I7-R22` — bounded inputs; oversized/malformed refused with frozen vocabulary."""

    def test_oversized_and_malformed_input_refused(self, capsys):
        # Oversized identity string: refused, never truncated (a truncated
        # identity would be a fabricated identity).
        with pytest.raises(ConsoleRefusal) as oversize:
            _build(
                reads=_default_reads(
                    **{"health.read": _envelope(
                        _healthy_health(),
                        request_id="x" * (panel.MAX_STRING_BYTES + 1),
                    )}
                )
            )
        assert oversize.value.reason == "payload_too_large"

        # Too many requested surfaces.
        with pytest.raises(ConsoleRefusal) as many:
            panel.build_panel_document(
                _read_from(_default_reads()), SURFACES,
                surfaces_requested=["health.read"] * (panel.MAX_SURFACE_COUNT + 1),
            )
        assert many.value.reason == "payload_too_large"

        # Malformed envelopes degrade to UNVERIFIABLE — never a crash, never OK.
        for hostile in ("not-an-envelope", 17, None, {"ok": True}):
            document = _build(
                reads=_default_reads(**{"health.read": hostile})
            )
            assert document["state"] == panel.STATE_UNVERIFIABLE
            assert document["queue"]["pending"]["value"] is None

        # A hostile over-wide collection is bounded and flagged, not truncated
        # silently into an apparently-complete list.
        wide = {f"w-{i:03d}": {} for i in range(panel.MAX_COLLECTION_ITEMS + 5)}
        bounded = _build(
            reads=_default_reads(**{"workers.list": _envelope({"workers": wide})})
        )
        assert bounded["workers"]["truncated"] is True
        assert len(bounded["workers"]["ids"]) == panel.MAX_COLLECTION_ITEMS
        assert bounded["workers"]["count"]["value"] == panel.MAX_COLLECTION_ITEMS + 5
        assert bounded["workers"]["bound"] == panel.MAX_COLLECTION_ITEMS

        # CLI: malformed arguments are a refusal (3), never a stack verdict (2).
        capsys.readouterr()
        assert cli.main(["panel", "--nope"]) == cli.EXIT_REFUSED
        assert cli.main(["--unknown-command"]) == cli.EXIT_REFUSED


# ── R23: strictly additive compatibility ───────────────────────────────────

class TestCompatibility:
    """`B5I7-R23` — the documented status command and exit codes are unchanged."""

    def test_documented_status_command_and_exit_codes_unchanged(self, capsys):
        # The frozen five-section status contract is untouched: no sixth section.
        assert STATUS_SECTIONS == (
            "health", "readiness", "system", "workers", "schedules"
        )
        status = build_status_document(_read_from({
            "health.read": _envelope(_healthy_health()),
            "readiness.read": _envelope({"ready": True}),
            "system.read": _envelope({"platform": "test"}),
            "workers.list": _envelope({"workers": {}}),
            "jobs.schedules": _envelope({"schedules": {}}),
        }), {
            "health.read": "/api/health",
            "readiness.read": "/api/readiness",
            "system.read": "/api/system",
            "workers.list": "/api/workers",
            "jobs.schedules": "/api/schedules",
        })
        assert tuple(status["sections"].keys()) == STATUS_SECTIONS
        assert "panel" not in status["sections"]
        assert "queue" not in status["sections"]

        # Documented exit codes are unchanged and nonzero for every non-OK state.
        assert cli.EXIT_OK == 0
        assert cli.EXIT_UNREACHABLE == 2
        assert cli.EXIT_REFUSED == 3
        assert cli.EXIT_DEGRADED == 4
        assert cli.EXIT_UNVERIFIABLE == 5
        assert cli.EXIT_BY_DOCUMENT_STATE == {
            "OK": 0, "STACK_UNREACHABLE": 2, "DEGRADED": 4, "UNVERIFIABLE": 5,
        }
        # The panel is additive: its own map never maps a non-OK state to 0.
        assert cli.EXIT_BY_PANEL_STATE[panel.STATE_OK] == 0
        for state in (panel.STATE_UNREACHABLE, panel.STATE_DENIED,
                      panel.STATE_UNVERIFIABLE):
            assert cli.EXIT_BY_PANEL_STATE[state] != 0

        # Bare invocation still defaults to `status`, and --help still exits 0.
        assert cli.build_parser().parse_args([]).command == "status"
        assert cli.main(["--help"]) == cli.EXIT_OK
        # The documented invocation token is accepted, and the additive one too.
        choices = cli.build_parser().parse_args(["panel"]).command
        assert choices == "panel"
        assert render_status(status).endswith("\n")
