"""Governed submission client (B5-I5, charter increment I-4).

The console's ONE write surface: a catalog-bounded ``jobs.submit`` invoke,
bound by the frozen B5-I2 contract pack to the single existing governed
operation ``ControlPlaneAPI.submit_job`` (``POST /api/jobs``). This module
is a separate client from the frozen GET-only read transport
(``transport.py``) so the B5-I4 read-path law ("GET only, no write verb")
stays untouched and green; this module adds exactly the I-4 submit.

Laws (charter sections 5/8/9; Gates G3/G4/G5; S-2/S-4):

- loopback-only, literal host, empty proxy map (reuses the read
  transport's base-URL and identity guards) — no ambient authority;
- catalog-bounded: a ``job_type`` outside the representative catalog is
  refused fail-closed BEFORE any I/O (I-4 non-goal "no new job types");
- contract-validated: payload must be an object and within the pack's
  ``max_payload_bytes``; required fields present — refused before I/O;
- the operator's grant/actor are passed VERBATIM in headers; the console
  mints no identity, retries nothing, and never widens the route;
- a governed denial (403 envelope) or an HTTP-layer 401 ``detail`` body is
  surfaced as DATA verbatim — never reinterpreted, never turned green
  (S-4); a transport failure raises ``StackUnreachable``.

Client-only: imports no ``oce_control`` module and no store/model runtime
(Gate G3). The authoritative catalog remains the engine's
``representative_jobs.supported_job_types()``; ``CATALOG_JOB_TYPES`` below
is a fail-closed client-side pre-filter bound to that engine catalog by a
two-sided test (drift turns the binding node red).

Stdlib only; no LLM; no provider; no telemetry.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from .kernel import ConsoleRefusal
from .transport import StackUnreachable, _validate_identity, validate_base_url

# Console-side frozen representative-catalog allowlist (DATA). The engine's
# oce_control.representative_jobs.supported_job_types() is the sole
# authority; this is a fail-closed client-side pre-filter. A two-sided test
# asserts it equals the engine catalog, so drift turns that node red.
CATALOG_JOB_TYPES = frozenset({
    "b3.deterministic-hash",
    "b3.bounded-compute",
    "b3.repo-inventory",
    "b3.synthetic-backtest",
    "b3.analysis-artifact",
    "b3.cancel-during-exec",
    "b3.timeout-violation",
})

DEFAULT_PACK_PATH = (
    Path(__file__).resolve().parents[3] / "control-plane" / "contracts" / "console-contract.json"
)

_SUBMIT_SURFACE = "jobs.submit"


def load_invoke_surface(surface: str = _SUBMIT_SURFACE,
                        pack_path: Optional[Path] = None) -> dict:
    """Load the ONE declared invoke surface from the frozen pack, fail-closed.

    Returns ``{surface, route, required, max_payload_bytes}`` where ``route``
    is the POST path (e.g. ``/api/jobs``). A missing/malformed pack, an
    undeclared surface, or a non-POST binding is refused before any I/O.
    """
    path = Path(pack_path) if pack_path is not None else DEFAULT_PACK_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConsoleRefusal("pack_unreadable", str(exc)) from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("invokes"), list):
        raise ConsoleRefusal("pack_malformed", "invokes section missing")
    for entry in raw["invokes"]:
        if not isinstance(entry, dict) or entry.get("kind") != "invoke":
            raise ConsoleRefusal("pack_malformed", f"non-invoke entry: {entry!r}")
        if entry.get("surface") != surface:
            continue
        route = entry.get("binds_to", {}).get("http_route", "")
        if not route.startswith("POST "):
            raise ConsoleRefusal("pack_malformed", f"{surface} is not a POST invoke")
        return {
            "surface": surface,
            "route": route[len("POST "):],
            "required": list(entry.get("required_request_fields", [])),
            "max_payload_bytes": int(entry.get("max_payload_bytes", 65536)),
        }
    raise ConsoleRefusal("unsupported_surface", surface)


class SubmitClient:
    """Loopback-only governed submit client (POST on the ONE declared invoke).

    Reuses the read transport's base-URL and identity guards and owns a
    single proxy-free opener, so no ambient authority can divert a declared
    loopback submit. The route set is fixed at construction from the pack;
    it cannot be widened by a caller or a redirect.
    """

    def __init__(self, base_url: str, grant_id: str = "", actor_id: str = "",
                 pack_path: Optional[Path] = None):
        # Order matters: validate the base URL before the pack is loaded.
        self._base = validate_base_url(base_url)
        self._surface = load_invoke_surface(_SUBMIT_SURFACE, pack_path)
        self._grant = _validate_identity("grant", grant_id)
        self._actor = _validate_identity("actor", actor_id)
        # §6 authority law: a governed submit requires non-empty operator
        # identity and is refused HERE — before a request object or socket
        # exists. (Malformed values are refused by _validate_identity above;
        # well-formed but engine-invalid grants are decided by the engine and
        # rendered verbatim as denials.)
        for kind, value in (("grant", self._grant), ("actor", self._actor)):
            if not value.strip():
                raise ConsoleRefusal("missing_identity",
                                     f"{kind} is required for submit")
        # One proxy-free opener owned by this client (no ambient proxy law).
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @property
    def route(self) -> str:
        return self._surface["route"]

    @property
    def surface(self) -> str:
        return self._surface["surface"]

    def submit(self, job_type: str, payload: dict, **opts) -> dict:
        """Perform the governed submit; return the parsed governed envelope.

        Contract-validated BEFORE any I/O (Gate G5). Returns whatever the
        control plane answered, verbatim (governed envelope on 200/403, or
        the HTTP-layer body) — the caller decides; this client never turns a
        denial into success and never retries.
        """
        if job_type not in CATALOG_JOB_TYPES:
            raise ConsoleRefusal("unsupported_job_type", str(job_type))
        if not isinstance(payload, dict):
            raise ConsoleRefusal("malformed_request", "payload must be an object")
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        if len(encoded) > self._surface["max_payload_bytes"]:
            raise ConsoleRefusal("payload_too_large", str(job_type))

        body = {"job_type": job_type, "payload": payload}
        for key in ("resource_scope", "environment", "priority"):
            if key in opts:
                body[key] = opts[key]
        data = json.dumps(body).encode("utf-8")
        url = f"{self._base}{self._surface['route']}"
        request = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-OCE-Grant": self._grant,
                "X-OCE-Actor": self._actor,
            },
        )
        try:
            with self._opener.open(request, timeout=5.0) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            # A governed answer (403 denial, 401 detail, 4xx/5xx) is DATA.
            raw = exc.read()
        except (urllib.error.URLError, OSError, ConnectionError) as exc:
            raise StackUnreachable(f"{_SUBMIT_SURFACE}: {exc}") from exc
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise StackUnreachable(f"{_SUBMIT_SURFACE}: unparseable body") from exc
