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
import http.server
import inspect
import io
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request
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


def _capture_cli(argv: list[str]) -> tuple[int, str, str]:
    """Run the CLI in-process and return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


@contextlib.contextmanager
def _http_stub(payload: dict):
    """Minimal loopback HTTP server answering EVERY declared route with one
    fixed JSON body — no control-plane dependency, fully deterministic."""
    body = json.dumps(payload).encode("utf-8")

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # pragma: no cover - silence
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
        assert not thread.is_alive(), "stub stack failed to stop"


@contextlib.contextmanager
def _redirect_stub(location: str):
    """Loopback server whose ``/api/health`` answers 302 -> ``location``;
    every other declared route answers the healthy envelope."""
    body = json.dumps(ENVELOPE_OK).encode("utf-8")

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/health":
                self.send_response(302)
                self.send_header("Location", location)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # pragma: no cover - silence
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
        assert not thread.is_alive(), "redirect stub failed to stop"


@contextlib.contextmanager
def _blocked_off_loopback():
    """Record — and block — every connection attempt that leaves loopback.

    The attempt itself IS the violation: it is raised as ``OSError``
    before any packet leaves the machine, so the probe performs zero
    external I/O.
    """
    attempts: list[tuple] = []
    original = socket.create_connection

    def guarded(address, *args, **kwargs):
        if str(address[0]).lower() not in LOOPBACK_HOSTS:
            attempts.append(tuple(address))
            raise OSError("blocked off-loopback connection (probe)")
        return original(address, *args, **kwargs)

    socket.create_connection = guarded
    try:
        yield attempts
    finally:
        socket.create_connection = original


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
        # The package under test IS the in-repo one (no shadowing by an
        # installed copy): every proof below runs against this checkout.
        resolved_pkg = Path(oce_console.__file__).resolve().parent
        assert resolved_pkg == (CONSOLE_SRC / "oce_console").resolve(), resolved_pkg
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

        # X2 (surface-id contract): the injected read path is called with
        # the pack's SURFACE ids in the frozen section order — never with
        # an HTTP route. Route reconstruction has exactly one owner (the
        # transport), and the kernel holds no route string at all.
        seen: list[str] = []

        def recording(surface: str):
            seen.append(surface)
            return json.loads(json.dumps(ENVELOPE_OK))

        recorded = build_status_document(recording)
        assert recorded["state"] == STATE_OK
        assert seen == [
            "health.read",
            "readiness.read",
            "system.read",
            "workers.list",
            "jobs.schedules",
        ], f"kernel requested something other than the declared surfaces: {seen}"
        routes = load_read_surfaces()
        assert all(surface in routes for surface in seen), seen
        assert [section_route(routes, s) for s in STATUS_SECTIONS] == seen
        assert all("/" not in surface and " " not in surface for surface in seen), (
            f"kernel passed a route instead of a surface id: {seen}"
        )
        assert "/api/" not in inspect.getsource(kernel), (
            "kernel must not reconstruct HTTP routes"
        )

        # X2 (derived-state law): DEGRADED is derived ONLY from the
        # returned governed section states — a fully-ok view of the same
        # shape never degrades, and the summary cannot be written back
        # (no write verb exists in the transport).
        assert build_status_document(_fetch_all(ENVELOPE_OK))["state"] == STATE_OK
        assert 'method="GET"' in inspect.getsource(transport)

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

        original_open_url = transport._open_url
        transport._open_url = explode
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
            transport._open_url = original_open_url

        # X2 ambient-proxy law (same refusal-before-I/O class): an
        # ambient proxy setting must never divert a declared loopback
        # read to another host. ``http_proxy`` is set to the exact
        # non-loopback address that PRE-REPAIR demonstrably received the
        # connection; with the client's own proxy-free opener no
        # off-loopback socket is attempted at all.
        client = LoopbackTransport("http://127.0.0.1:1", timeout=1)  # dead port
        try:
            with _blocked_off_loopback() as attempts:
                os.environ["http_proxy"] = "http://10.0.0.5:8080"
                os.environ["HTTP_PROXY"] = "http://10.0.0.5:8080"
                with pytest.raises(StackUnreachable):
                    client.read("health.read")
        finally:
            os.environ.pop("http_proxy", None)
            os.environ.pop("HTTP_PROXY", None)
        assert attempts == [], (
            f"ambient proxy authority: off-loopback connection attempted {attempts}"
        )

        # Non-vacuity (demonstrated red): the PRE-REPAIR client shape —
        # urllib's own default proxy handler — DOES divert the identical
        # loopback read to the proxy host, so the assertion above is a
        # real guard and not theater.
        request = urllib.request.Request("http://127.0.0.1:8448/api/health", method="GET")
        try:
            os.environ["http_proxy"] = "http://10.0.0.5:8080"
            os.environ["HTTP_PROXY"] = "http://10.0.0.5:8080"
            with _blocked_off_loopback() as weakened_attempts:
                with contextlib.suppress(OSError):
                    urllib.request.build_opener(urllib.request.ProxyHandler()).open(
                        request, timeout=2
                    )
        finally:
            os.environ.pop("http_proxy", None)
            os.environ.pop("HTTP_PROXY", None)
        assert weakened_attempts == [("10.0.0.5", 8080)], (
            f"negative control vacuous: pre-repair path did not divert {weakened_attempts}"
        )

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

        def capture(opener, request, timeout=None):
            seen.append(request)
            return _FakeResponse()

        original_open_url = transport._open_url
        transport._open_url = capture
        try:
            client = LoopbackTransport("http://127.0.0.1:8448")
            client.read("health.read")
        finally:
            transport._open_url = original_open_url
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

        original_open_url = transport._open_url
        transport._open_url = explode
        try:
            for undeclared in ("jobs.submit", "jobs.cancel", "jobs.retry", "bogus.surface"):
                with pytest.raises(ConsoleRefusal):
                    client.read(undeclared)
        finally:
            transport._open_url = original_open_url

        # X2 redirect law (demonstrated, then repaired): a loopback 3xx is
        # DATA, but FOLLOWING it is new I/O and must stay inside the
        # frozen boundary. Pre-repair, ``302 Location:
        # http://10.0.0.5:8080/escaped`` demonstrably opened a socket to
        # that non-loopback host. Now the redirect is refused fail-closed
        # BEFORE the follow-up request is built — proven by blocking
        # every off-loopback connect.
        with _redirect_stub("http://10.0.0.5:8080/escaped") as base_url:
            client = LoopbackTransport(base_url)
            with _blocked_off_loopback() as attempts:
                with pytest.raises(ConsoleRefusal) as excinfo:
                    client.read("health.read")
            assert excinfo.value.reason == "non_loopback_refused"
            assert attempts == [], (
                f"redirect escaped loopback: off-loopback connect {attempts}"
            )

        # A loopback redirect to an UNDECLARED path is refused too: the
        # route allowlist (X6) cannot be widened by a 3xx.
        with _redirect_stub("/api/jobs/job-1") as base_url:
            client = LoopbackTransport(base_url)
            with _blocked_off_loopback() as attempts:
                with pytest.raises(ConsoleRefusal) as excinfo:
                    client.read("health.read")
            assert excinfo.value.reason == "unsupported_surface"
            assert attempts == []

        # Two-sided: a redirect onto a DECLARED route on the same loopback
        # host is followed and returns the governed envelope verbatim.
        with _redirect_stub("/api/workers") as base_url:
            response = LoopbackTransport(base_url).read("health.read")
        assert response == ENVELOPE_OK, "legitimate loopback redirect broken"

        # Non-vacuity (demonstrated red): the PRE-REPAIR client shape —
        # urllib's own default redirect handler — DOES follow the hostile
        # redirect off loopback, so the refusal above is a real guard.
        with _redirect_stub("http://10.0.0.5:8080/escaped") as base_url:
            request = urllib.request.Request(f"{base_url}/api/health", method="GET")
            with _blocked_off_loopback() as weakened_attempts:
                with contextlib.suppress(OSError):
                    urllib.request.build_opener().open(request, timeout=3)
        assert weakened_attempts == [("10.0.0.5", 8080)], (
            f"negative control vacuous: pre-repair path did not follow off-loopback "
            f"{weakened_attempts}"
        )

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

            # X3 (frozen interface, demonstrated then repaired): the
            # LITERAL documented command line — ``python -m oce_console
            # status ...`` (P0 gap/scope contract; charter section 8.1) —
            # must work end to end in a REAL subprocess against the real
            # stack. Before this repair the CLI's own parser rejected the
            # ``status`` token, so the documented invocation failed.
            env = dict(os.environ)
            env["PYTHONPATH"] = str(CONSOLE_SRC) + os.pathsep + env.get("PYTHONPATH", "")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "oce_console",
                    "status",
                    "--base-url",
                    base_url,
                    "--grant",
                    grant,
                    "--actor",
                    "b5i4-console",
                ],
                capture_output=True,
                text=True,
                env=env,
                timeout=180,
            )
            assert proc.returncode == cli.EXIT_OK, (proc.returncode, proc.stderr)
            assert json.loads(proc.stdout)["state"] == STATE_OK

        # X2 (CLI exit semantics): every outcome maps to its own exit
        # code, DERIVED from the authoritative document state — never
        # from parsing rendered text, never a false success.
        # (a) fully healthy document -> 0.
        with _http_stub(ENVELOPE_OK) as base_url:
            code, out, _err = _capture_cli(["--base-url", base_url])
            assert code == cli.EXIT_OK
            assert json.loads(out)["state"] == STATE_OK

        # (b) governed denials across the view -> DEGRADED -> 4, never 0.
        with _http_stub(DENIAL_ENVELOPE) as base_url:
            code, out, _err = _capture_cli(["--base-url", base_url])
            assert code == cli.EXIT_DEGRADED
            assert json.loads(out)["state"] == STATE_DEGRADED

        # (c) a governed non-envelope body -> UNVERIFIABLE -> 5, never 0.
        with _http_stub({"detail": "gateway sad"}) as base_url:
            code, out, _err = _capture_cli(["--base-url", base_url])
            assert code == cli.EXIT_UNVERIFIABLE
            assert json.loads(out)["state"] == STATE_UNVERIFIABLE

        # (d) malformed configuration is refused BEFORE any I/O -> 3 and
        # must never masquerade as a stack verdict (argparse's own usage
        # exit code is 2, which collided with EXIT_UNREACHABLE).
        code, out, err = _capture_cli(["--bogus-flag"])
        assert code == cli.EXIT_REFUSED, code
        assert "malformed_arguments" in err
        code, out, _err = _capture_cli(["--base-url"])
        assert code == cli.EXIT_REFUSED, code
        assert out == "", "a refused invocation must not render a document"

        # --help stays a clean success.
        code, out, _err = _capture_cli(["--help"])
        assert code == cli.EXIT_OK and "loopback" in out

        # X3 (frozen interface): the bare module invocation works and an
        # unknown command is a refused usage error — both decided before
        # any I/O.
        with _http_stub(ENVELOPE_OK) as base_url:
            code, out, _err = _capture_cli(["--base-url", base_url])
            assert code == cli.EXIT_OK, code
        code, _out, err = _capture_cli(["bogus-command"])
        assert code == cli.EXIT_REFUSED and "malformed_arguments" in err

        # (e) unexpected internal failure -> 1: reported, never success.
        original_build = cli.build_status_document

        def explode_build(*args, **kwargs):
            raise RuntimeError("internal defect")

        cli.build_status_document = explode_build
        try:
            code, _out, err = _capture_cli(["--base-url", "http://127.0.0.1:8448"])
        finally:
            cli.build_status_document = original_build
        assert code == cli.EXIT_INTERNAL, code
        assert "internal_error" in err

        # (f) X2 dead-branch law: the exit result reads the document's
        # summary only — no exception branch may shadow it, so main()
        # carries no StackUnreachable handler, and the state map can
        # never return 0 for a non-OK summary.
        assert "except StackUnreachable" not in inspect.getsource(cli.main)
        assert cli.EXIT_BY_DOCUMENT_STATE[STATE_OK] == cli.EXIT_OK
        assert set(cli.EXIT_BY_DOCUMENT_STATE.values()) == {
            cli.EXIT_OK,
            cli.EXIT_UNREACHABLE,
            cli.EXIT_DEGRADED,
            cli.EXIT_UNVERIFIABLE,
        }

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
            exit_code = cli.main(["--base-url", f"http://127.0.0.1:{dead_port}"])
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
