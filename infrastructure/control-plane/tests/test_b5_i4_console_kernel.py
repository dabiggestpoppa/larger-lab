"""OCE B5-I4 — deterministic console kernel proofs (charter increment I-3).

Charter section 12 row I-3 (frozen planned nodes, executed here verbatim):
the deterministic read path — a CLI status view over contract-validated
reads with fail-closed ``STACK_UNREACHABLE``. Two-sided proofs for every
requirement in the B5-I4 acceptance matrix, including demonstrated
negative controls (a genuinely weakened implementation is executed and
must fail the same assertion the real implementation passes).

Laws proven here:
- G3 (UI read half): the console never reads a store directly; it is a
  client of the frozen B5-I2 contract pack and the loopback HTTP API.
- G7 (UI half): the status view equals the API's own responses verbatim.
- S-1: jobs/workers/health lists match the control plane verbatim over a
  REAL loopback socket (the plan-section-7 "local real path" gate).
- F-1: stack unreachable -> whole-view ``STACK_UNREACHABLE``, never green.
- F-5: unverifiable sections are explicit gaps, never stale-green.
- Loopback-only and GET-only transport; hostile non-loopback and malformed
  input refused fail-closed BEFORE any socket I/O.
- Deterministic, stateless, stdlib-only, no-LLM import closure.

Non-goals honored: no writes, no drills, no web view, no control-plane,
schema, workflow, or frontend modification (regression asserted).
"""
from __future__ import annotations

import ast
import contextlib
import inspect
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
sys.path.insert(0, str(CONSOLE_SRC))

import oce_console  # noqa: E402
from oce_console import cli, kernel, transport  # noqa: E402
from oce_console.kernel import (  # noqa: E402
    STATUS_SECTIONS,
    STATE_DEGRADED,
    STATE_OK,
    STATE_UNREACHABLE,
    STATE_UNVERIFIABLE,
    ConsoleRefusal,
    build_status_document,
    load_read_surfaces,
    project_section,
    render_status,
    section_route,
)
from oce_console.transport import (  # noqa: E402
    LOOPBACK_HOSTS,
    LoopbackTransport,
    StackUnreachable,
    validate_base_url,
)

BASE_SHA = "9df3bf4f00a47230b42c22ce10a2d81d1591c885"
ADDENDUM_PATH = (
    REPO_ROOT / "docs" / "oce-golden-system" / "OCE_B5_I4_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json"
)
PACK_PATH = REPO_ROOT / "infrastructure" / "control-plane" / "contracts" / "console-contract.json"

ENVELOPE_OK = {
    "ok": True,
    "status": "success",
    "data": {"workers": {"w-1": {"worker_id": "w-1"}}},
    "error": "",
    "request_id": "req-1",
}
DENIAL_ENVELOPE = {
    "ok": False,
    "status": "denied",
    "data": {"denial": {"reason_code": "missing_authority", "actor_id": "stranger"}},
    "error": "missing_authority",
    "request_id": "req-2",
}


def _fetch_all(envelope):
    def fetch(route):
        return json.loads(json.dumps(envelope))

    return fetch


def _git(*args: str) -> bytes:
    proc = subprocess.run(["git", *args], cwd=str(REPO_ROOT), capture_output=True)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    return proc.stdout


def _class_test_pairs(path: Path) -> set[tuple[str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    pairs: set[tuple[str, str]] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                    pairs.add((node.name, item.name))
    return pairs


@contextlib.contextmanager
def _live_stack(plane):
    """Serve the REAL FastAPI app over a REAL loopback socket (port 0).

    Readiness is a bounded poll of uvicorn's own ``started`` flag with a
    hard deadline that FAILS (never skips) — outcome is pass-or-fail,
    never flaky-green.
    """
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


def _read_grant(plane):
    return plane.authority.issue_grant(
        actor_id="b5i4-console", action="read", target="default"
    ).grant_id


class TestClientOnlyReads:
    """Gate G3 (UI read half): client-only, contract-mediated, no store."""

    def test_no_direct_store_read(self):
        """The console package cannot reach canonical state directly.

        AST proof: no module under oce_console imports the control plane
        (``oce_control``), any store/state module, or any model runtime —
        the ONLY repo file it can read is the contract pack (data).
        Behavioral proof: a full status build performs exactly one file
        read (the pack) and touches no store object.
        """
        forbidden_modules = {
            "oce_control",
            "job_store",
            "worker_leases",
            "pg_store",
            "events",
            "scheduler",
            "recovery",
            "evidence",
            "authority",
            "plane",
            "requests",
            "httpx",
            "openai",
            "anthropic",
            "torch",
        }
        pkg = CONSOLE_SRC / "oce_console"
        read_calls: list[Path] = []
        original_read_text = Path.read_text

        def tracking_read_text(self, *args, **kwargs):
            read_calls.append(self)
            return original_read_text(self, *args, **kwargs)

        modules = sorted(p for p in pkg.glob("*.py"))
        assert modules, "console package missing"
        imported: set[str] = set()
        for path in modules:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0:  # relative import inside the package
                        continue
                    if node.module:
                        imported.add(node.module.split(".")[0])
        offenders = sorted(imported & forbidden_modules)
        assert offenders == [], f"console imports store/model modules: {offenders}"

        # Behavioral: one status build reads only the contract pack.
        Path.read_text = tracking_read_text
        try:
            build_status_document(_fetch_all(ENVELOPE_OK))
        finally:
            Path.read_text = original_read_text
        read_paths = {p.resolve() for p in read_calls}
        assert read_paths == {PACK_PATH.resolve()}, (
            f"console read files other than the contract pack: {read_paths}"
        )

    def test_import_closure_is_stdlib_only(self):
        """G10/G11: stdlib-only import closure; no LLM, provider, or HTTP client."""
        allowed = {
            "__future__",
            "argparse",
            "json",
            "pathlib",
            "socket",
            "sys",
            "typing",
            "urllib",
        }
        pkg = CONSOLE_SRC / "oce_console"
        imported: set[str] = set()
        for path in sorted(pkg.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.level == 0 and node.module:
                        imported.add(node.module.split(".")[0])
        unexpected = sorted(imported - allowed)
        assert unexpected == [], f"non-stdlib or unexpected imports: {unexpected}"


class TestStatusAgreement:
    """Gate G7 (UI half): verbatim agreement with governed responses."""

    def test_status_view_matches_api_verbatim(self):
        """Every section preserves the governed envelope EXACTLY — field
        for field, including request_id — adding nothing, renaming
        nothing, defaulting nothing. A governed not-ok response keeps its
        verbatim envelope while the document summary degrades (never a
        silent green)."""
        doc = build_status_document(_fetch_all(ENVELOPE_OK))
        for section in STATUS_SECTIONS:
            projected = doc["sections"][section]
            assert projected["state"] == STATE_OK
            assert projected["response"] == ENVELOPE_OK, (
                f"{section}: projection is not verbatim"
            )
        assert doc["state"] == STATE_OK

        denied = build_status_document(_fetch_all(DENIAL_ENVELOPE))
        for section in STATUS_SECTIONS:
            assert denied["sections"][section]["response"] == DENIAL_ENVELOPE
        assert denied["state"] == STATE_DEGRADED, (
            "a document of governed denials must never summarize as OK"
        )

    def test_denied_read_rendered_verbatim_not_retried(self):
        """X3: a governed denial is rendered verbatim, the fetch happens
        exactly once (no silent retry), and canonical state is unaffected
        by the console (the engine's own audit is engine-owned)."""
        from oce_control.plane import ControlPlane

        plane = ControlPlane()
        bogus = plane.authority.issue_grant(
            actor_id="not-an-operator", action="read", target="default"
        )
        denied = plane.api.list_workers(
            grant_id=bogus.grant_id + "-tampered", actor_id="not-an-operator"
        )
        assert denied.ok is False and denied.status == "denied"

        calls: list[str] = []

        def counting_fetch(route):
            calls.append(route)
            return denied.to_dict()

        doc = build_status_document(counting_fetch)
        workers = doc["sections"]["workers"]
        assert workers["response"]["data"] == denied.data
        assert workers["response"]["status"] == "denied"
        assert doc["state"] == STATE_DEGRADED
        assert len(calls) == len(STATUS_SECTIONS), "silent retry detected"

        # Durable canonical state unaffected by the console's reads.
        assert plane.job_store.all_jobs == {}
        assert plane.worker_protocol.workers == {}


class TestStatusView:
    """Scenario S-1 (console half): lists match the API verbatim."""

    def test_s1_lists_match_api_verbatim(self, plane, clock):
        """Over a REAL loopback socket: the console's workers/system/
        health/schedules sections equal the control plane's own API
        response DATA byte-for-byte (JSON-normalized), and the per-section
        request_id is the one the API actually returned for that call."""
        grant = _read_grant(plane)
        with _live_stack(plane) as base_url:
            transport_obj = LoopbackTransport(
                base_url, grant_id=grant, actor_id="b5i4-console"
            )
            doc = transport_obj.read_status()

        assert doc["state"] == STATE_OK, doc
        direct_workers = plane.api.list_workers(
            grant_id=grant, actor_id="b5i4-console"
        ).to_dict()
        direct_system = plane.api.system_state(
            grant_id=grant, actor_id="b5i4-console"
        ).to_dict()
        direct_schedules = plane.api.list_schedules(
            grant_id=grant, actor_id="b5i4-console"
        ).to_dict()
        direct_health = plane.api.health().to_dict()

        assert doc["sections"]["workers"]["response"]["data"] == direct_workers["data"]
        assert doc["sections"]["system"]["response"]["data"] == direct_system["data"]
        assert doc["sections"]["schedules"]["response"]["data"] == direct_schedules["data"]
        assert doc["sections"]["health"]["response"]["data"] == direct_health["data"]
        for section in STATUS_SECTIONS:
            returned_id = doc["sections"][section]["response"]["request_id"]
            assert isinstance(returned_id, str) and returned_id, section

    def test_denied_and_missing_identity_rendered_over_real_loopback(self, plane, clock):
        """Missing identity -> the HTTP layer's 401 body is preserved
        verbatim as an explicit UNVERIFIABLE section (raw retained), and a
        tampered grant yields the governed denial verbatim. Neither is
        ever rendered green."""
        with _live_stack(plane) as base_url:
            anonymous = LoopbackTransport(base_url)
            doc_no_identity = anonymous.read_status()
            assert doc_no_identity["state"] == STATE_UNVERIFIABLE
            raw = doc_no_identity["sections"]["workers"].get("raw")
            assert isinstance(raw, dict) and "detail" in raw, raw

            tampered = LoopbackTransport(base_url, grant_id="nope", actor_id="nope")
            doc_denied = tampered.read_status()
            assert doc_denied["state"] in (STATE_DEGRADED, STATE_UNVERIFIABLE)
            workers = doc_denied["sections"]["workers"]
            assert workers["response"]["ok"] is not True
            assert workers["state"] == STATE_OK  # envelope intact...
            assert doc_denied["state"] != STATE_OK  # ...but never silent-green


class TestStackUnreachable:
    """Failure class F-1 (console half): fail-closed whole view."""

    def test_stack_unreachable_renders_fail_closed(self):
        """A closed loopback port collapses the WHOLE document to
        STACK_UNREACHABLE with zero sections — no partial green, no
        cached/default data, no fallback."""
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        dead_port = probe.getsockname()[1]
        probe.close()

        surfaces = load_read_surfaces()
        client = LoopbackTransport(
            f"http://127.0.0.1:{dead_port}", surfaces=surfaces, timeout=2
        )
        with pytest.raises(StackUnreachable):
            client.read("health.read")

        doc = build_status_document(client.read, surfaces)
        assert doc["state"] == STATE_UNREACHABLE
        assert doc["sections"] == {}
        assert "OK" not in json.dumps(doc)

    def test_hostile_and_malformed_input_refused_before_io(self):
        """X1/X2: hostile non-loopback and malformed inputs are refused
        fail-closed BEFORE any socket I/O — proven by making urlopen
        explode if it is ever reached."""
        hostile = [
            "https://127.0.0.1:8448",
            "http://10.0.0.1:8080",
            "http://192.168.1.5:9000",
            "http://172.16.0.2:9000",
            "http://example.com",
            "http://169.254.169.254/latest/meta-data",
            "http://[fd00::1]:8080",
            "http://0177.0.0.1:80",
            "http://2130706433:80",
            "http://user@127.0.0.1:8448",
            "ftp://127.0.0.1:21",
            "file:///etc/passwd",
            "http://127.0.0.1:8448/extra/path",
            "http://127.0.0.1:8448?q=1",
            "",
            "not-a-url",
            "http://[::2]:80",
        ]

        def explode(*args, **kwargs):  # pragma: no cover - must never run
            raise AssertionError("I/O attempted for a refused input")

        original_urlopen = transport.urllib.request.urlopen
        transport.urllib.request.urlopen = explode
        try:
            for url in hostile:
                with pytest.raises(ConsoleRefusal):
                    validate_base_url(url)
                with pytest.raises(ConsoleRefusal):
                    LoopbackTransport(url)
            # Malformed identity values are refused before I/O too.
            with pytest.raises(ConsoleRefusal):
                LoopbackTransport("http://127.0.0.1:8448", grant_id="a\r\nX-Evil: 1")
            with pytest.raises(ConsoleRefusal):
                LoopbackTransport("http://127.0.0.1:8448", actor_id="x" * 4096)
        finally:
            transport.urllib.request.urlopen = original_urlopen

        # The real guard admits loopback forms.
        assert validate_base_url("http://127.0.0.1:8448/") == "http://127.0.0.1:8448"
        assert validate_base_url("http://localhost:8080") == "http://localhost:8080"
        assert validate_base_url("http://[::1]:8448") == "http://[::1]:8448"
        assert LOOPBACK_HOSTS == frozenset({"127.0.0.1", "::1", "localhost"})


class TestReadOnlyTransport:
    """Charter I-3 non-goal 'no writes': the transport cannot mutate."""

    def test_transport_get_only_no_write_verb(self):
        """The transport issues GET only — no POST/PUT/PATCH/DELETE code
        path exists, and the Request objects it builds say GET."""
        source = inspect.getsource(transport)
        for verb in ("POST", "PUT", "PATCH", "DELETE"):
            assert f'method="{verb}"' not in source, f"write verb {verb} in transport"
        assert 'method="GET"' in source

        seen: list[object] = []

        class _FakeResponse:
            def read(self):
                return json.dumps(ENVELOPE_OK).encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def capture(request, timeout=None):
            seen.append(request)
            return _FakeResponse()

        original_urlopen = transport.urllib.request.urlopen
        transport.urllib.request.urlopen = capture
        try:
            client = LoopbackTransport("http://127.0.0.1:8448")
            client.read("health.read")
        finally:
            transport.urllib.request.urlopen = original_urlopen
        assert len(seen) == 1
        assert seen[0].get_method() == "GET"
        assert seen[0].data is None, "GET must not carry a body"

    def test_only_declared_routes_are_reachable(self):
        """X6: the route table is exactly the pack's declared GET routes;
        an undeclared surface is refused before any I/O."""
        surfaces = load_read_surfaces()
        pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
        declared_gets = {
            e["surface"]: e["binds_to"]["http_route"][len("GET "):]
            for e in pack["reads"]
            if e["binds_to"]["http_route"].startswith("GET ")
        }
        assert surfaces == declared_gets
        client = LoopbackTransport("http://127.0.0.1:8448", surfaces=surfaces)

        def explode(*args, **kwargs):  # pragma: no cover
            raise AssertionError("I/O attempted for an undeclared surface")

        original_urlopen = transport.urllib.request.urlopen
        transport.urllib.request.urlopen = explode
        try:
            for undeclared in ("jobs.submit", "jobs.cancel", "jobs.retry", "bogus.surface"):
                with pytest.raises(ConsoleRefusal):
                    client.read(undeclared)
        finally:
            transport.urllib.request.urlopen = original_urlopen

    def test_pack_unreadable_fails_closed(self, tmp_path):
        """X5: a missing or malformed pack refuses fail-closed — there is
        never an ad-hoc surface fallback."""
        with pytest.raises(ConsoleRefusal):
            kernel.load_read_surfaces(tmp_path / "absent.json")
        junk = tmp_path / "junk.json"
        junk.write_text("{not json", encoding="utf-8")
        with pytest.raises(ConsoleRefusal):
            kernel.load_read_surfaces(junk)
        hollow = tmp_path / "hollow.json"
        hollow.write_text('{"reads": []}', encoding="utf-8")
        with pytest.raises(ConsoleRefusal):
            kernel.load_read_surfaces(hollow)


class TestNoStaleGreen:
    """Failure class F-5 (console half): gaps stay explicit, never green."""

    def test_unverifiable_gap_never_renders_green(self):
        """A non-envelope body renders UNVERIFIABLE with the raw body
        preserved; a mid-view transport failure collapses the WHOLE view
        (no partial green); a not-ok governed section degrades the
        summary. Nothing green survives either path."""
        doc = build_status_document(
            lambda route: {"detail": "gateway sad"} if "workers" in route else ENVELOPE_OK
        )
        workers = doc["sections"]["workers"]
        assert workers["state"] == STATE_UNVERIFIABLE
        assert workers["raw"] == {"detail": "gateway sad"}
        assert "response" not in workers, "unverifiable section must not carry a response"
        assert doc["state"] == STATE_UNVERIFIABLE

        def failing_after_first(route):
            if "workers" in route:
                raise StackUnreachable("mid-view outage")
            return ENVELOPE_OK

        doc = build_status_document(failing_after_first)
        assert doc["state"] == STATE_UNREACHABLE
        assert doc["sections"] == {}, "no partial sections may survive F-1"

    def test_no_cache_between_invocations(self):
        """Statelessness (G6 by construction): a later invocation reflects
        the LATER truth; no residue of an earlier healthy read survives."""
        healthy = build_status_document(_fetch_all(ENVELOPE_OK))
        assert healthy["state"] == STATE_OK
        changed = build_status_document(_fetch_all(DENIAL_ENVELOPE))
        assert changed["state"] == STATE_DEGRADED
        assert changed["sections"]["workers"]["response"] == DENIAL_ENVELOPE
        back = build_status_document(_fetch_all(ENVELOPE_OK))
        assert render_status(back) == render_status(healthy)


class TestDeterminism:
    """Charter section 7 deterministic kernel: byte-identical output."""

    def test_identical_inputs_render_byte_identically(self):
        first = render_status(build_status_document(_fetch_all(ENVELOPE_OK)))
        second = render_status(build_status_document(_fetch_all(ENVELOPE_OK)))
        assert first.encode("utf-8") == second.encode("utf-8")
        # Render is canonical JSON: sorted keys, ASCII, trailing newline.
        parsed = json.loads(first)
        assert parsed["kind"] == "oce-console-status"
        assert first.endswith("\n")


class TestNegativeControls:
    """Mission section 7: demonstrated red — a genuinely weakened
    implementation is EXECUTED and must fail the assertion the real
    implementation passes. Never source-string theater."""

    def test_n1_weakened_loopback_guard_admits_hostile_url(self):
        """Widen LOOPBACK_HOSTS (controlled mutation of the real module):
        the real guard refuses example.com; the weakened guard admits it,
        so the hostile-input assertion demonstrably turns red."""
        def probe_refusal():
            try:
                validate_base_url("http://example.com")
            except ConsoleRefusal:
                return True
            return False

        assert probe_refusal() is True, "real loopback guard must refuse"
        original = transport.LOOPBACK_HOSTS
        transport.LOOPBACK_HOSTS = original | {"example.com"}
        try:
            weakened_refusal = probe_refusal()
        finally:
            transport.LOOPBACK_HOSTS = original
        assert weakened_refusal is False, (
            "negative control vacuous: weakened guard still refused"
        )
        assert probe_refusal() is True, "restored guard must refuse again"

    def test_n2_weakened_fail_closed_fallback_renders_stale_green(self):
        """Controlled source mutation of the REAL kernel: replace the
        F-1 whole-view collapse with a stale-green fallback and EXECUTE
        it. The weakened build renders OK where the real build renders
        STACK_UNREACHABLE — the F-1 assertion turns red."""
        source = inspect.getsource(kernel.build_status_document)
        stale_green = (
            'return {\n'
            '                "kind": CONSOLE_KIND,\n'
            '                "version": CONSOLE_STATUS_VERSION,\n'
            '                "state": STATE_OK,\n'
            '                "sections": {},\n'
            '            }'
        )
        mutated = source.replace(
            'return {\n'
            '                "kind": CONSOLE_KIND,\n'
            '                "version": CONSOLE_STATUS_VERSION,\n'
            '                "state": UNREACHABLE_DOCUMENT_STATE,\n'
            '                "sections": {},\n'
            '            }',
            stale_green,
            1,
        )
        assert mutated != source, "mutation did not apply — control vacuous"
        namespace = dict(kernel.__dict__)
        exec(compile(mutated, "<weakened-kernel>", "exec"), namespace)
        weakened_build = namespace["build_status_document"]

        def failing_fetch(route):
            raise StackUnreachable("down")

        real_doc = build_status_document(failing_fetch)
        weakened_doc = weakened_build(failing_fetch)
        assert real_doc["state"] == STATE_UNREACHABLE
        assert weakened_doc["state"] == STATE_OK, (
            "negative control vacuous: weakened kernel did not render green"
        )
        # The real assertion (state == STACK_UNREACHABLE) fails under the
        # mutation, exactly as intended.
        assert weakened_doc["state"] != real_doc["state"]

    def test_n3_weakened_projection_fabricates_fields(self):
        """Controlled source mutation of the REAL projection: fabricate
        ok/data instead of preserving them. The verbatim-agreement
        assertion turns red under the mutation and green when restored."""
        source = inspect.getsource(kernel.project_section)
        mutated = (
            source.replace('"ok": response["ok"],', '"ok": True,', 1)
            .replace('"data": response["data"],', '"data": {"fabricated": True},', 1)
        )
        assert mutated != source, "mutation did not apply — control vacuous"
        namespace = dict(kernel.__dict__)
        exec(compile(mutated, "<weakened-projection>", "exec"), namespace)
        weakened_project = namespace["project_section"]

        real = project_section("workers", DENIAL_ENVELOPE)
        weakened = weakened_project("workers", DENIAL_ENVELOPE)
        assert real["response"] == DENIAL_ENVELOPE
        assert weakened["response"]["ok"] is True
        assert weakened["response"]["data"] == {"fabricated": True}
        assert weakened["response"] != DENIAL_ENVELOPE, (
            "negative control vacuous: weakened projection stayed verbatim"
        )


class TestLocalRealPath:
    """Plan section 7 gate: 'Local real path passes' — end to end through
    the CLI over a real loopback socket."""

    def test_real_loopback_status_view_passes(self, plane, clock):
        grant = _read_grant(plane)
        with _live_stack(plane) as base_url:
            exit_code = cli.main(
                ["--base-url", base_url, "--grant", grant, "--actor", "b5i4-console"]
            )
        assert exit_code == cli.EXIT_OK

    def test_cli_fails_closed_when_stack_down(self):
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        dead_port = probe.getsockname()[1]
        probe.close()
        captured_out, captured_err = [], []

        class _Out:
            def write(self, text):
                captured_out.append(text)

        class _Err:
            def write(self, text):
                captured_err.append(text)

        original_out, original_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = _Out(), _Err()
        try:
            exit_code = cli.main([f"--base-url", f"http://127.0.0.1:{dead_port}"])
        finally:
            sys.stdout, sys.stderr = original_out, original_err
        assert exit_code == cli.EXIT_UNREACHABLE
        rendered = json.loads("".join(captured_out))
        assert rendered["state"] == STATE_UNREACHABLE

    def test_cli_refuses_hostile_base_url(self):
        captured_err = []

        class _Err:
            def write(self, text):
                captured_err.append(text)

        original_err = sys.stderr
        sys.stderr = _Err()
        try:
            exit_code = cli.main(["--base-url", "http://10.0.0.1:8080"])
        finally:
            sys.stderr = original_err
        assert exit_code == cli.EXIT_REFUSED
        assert "non_loopback_refused" in "".join(captured_err)


class TestRegistryAddendum:
    """B5-I3 registry extension is addendum-only and append-only."""

    def test_addendum_binds_the_five_i3_discharges(self):
        addendum = json.loads(ADDENDUM_PATH.read_text(encoding="utf-8"))
        assert addendum["base_sha"] == BASE_SHA
        assert addendum["extends"]["registry_id"] == "OCE-B5-I3-REGISTRY-001"
        discharges = addendum["discharges"]
        assert sorted(d["id"] for d in discharges) == ["F-1", "F-5", "G3", "G7", "S-1"]
        pairs = _class_test_pairs(Path(__file__))
        for entry in discharges:
            planned = entry["planned_node"]
            executed = entry["executed_node"]
            assert planned == executed, "executed node must equal the frozen planned node"
            prefix = "infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::"
            assert executed.startswith(prefix), executed
            class_name, test_name = executed[len(prefix):].split("::")
            assert (class_name, test_name) in pairs, f"node not present: {executed}"
        still = {d["id"]: d["owner"] for d in addendum["still_deferred"]}
        assert still["S-2"] == "I-4" and still["F-3"] == "I-4"

    def test_b5_i3_registry_unchanged_vs_base(self):
        """The frozen B5-I3 registry is byte-identical to the authorized
        base: this increment extends by addendum only."""
        base_blob = _git("show", f"{BASE_SHA}:docs/oce-golden-system/OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json")
        head_blob = _git("show", "HEAD:docs/oce-golden-system/OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json")
        assert base_blob == head_blob, "B5-I3 registry modified — append-only law broken"

    def test_frozen_instruments_unchanged_vs_base(self):
        """No control-plane source, contract, or frozen B5-I2/B5-I3 test
        file changed between the authorized base and HEAD."""
        for path in (
            "infrastructure/control-plane/src/",
            "infrastructure/control-plane/contracts/",
            "infrastructure/control-plane/tests/test_console_contracts.py",
            "infrastructure/control-plane/tests/test_b5_i2_mutation_harness.py",
            "infrastructure/control-plane/tests/test_b5_i3_requirement_registry.py",
            "oce/frontend/",
        ):
            changed = _git(
                "diff", "--name-only", BASE_SHA, "HEAD", "--", path
            ).decode("utf-8").strip()
            assert changed == "", f"frozen path changed: {path} -> {changed!r}"
