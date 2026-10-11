"""Deterministic console kernel (B5-I4, charter increment I-3).

A pure, stateless projection layer over contract-validated reads: it
enumerates the read surfaces declared in the frozen B5-I2 contract pack
(data only — never imported code), maps each requestable surface to its
declared GET route, and projects the governed API's own responses
VERBATIM into a fixed-order status document. Refusal and failure law
(charter sections 5/6/9; B5-I4 failure matrix):

- the pack is loaded fail-closed: missing or malformed pack -> refusal,
  never an ad-hoc surface fallback (matrix row X5);
- only surfaces with a declared ``GET`` route are requestable; embedded
  (denial/evidence) and invoke surfaces are refused (matrix row X6);
- any transport-level failure collapses the whole view to
  ``STACK_UNREACHABLE`` — never stale-green, never cached (F-1);
- a surface whose response cannot be parsed into the governed envelope
  shape renders as ``UNVERIFIABLE`` — an explicit gap, never green (F-5);
- the kernel holds NO state: two invocations with identical responses
  produce byte-identical documents (restart = fresh re-read, Gate G6).

Stdlib only; no LLM; no provider; the console is a client with zero
authority (charter section 5 rules 1-9).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Mapping, Optional

CONSOLE_KIND = "oce-console-status"
CONSOLE_STATUS_VERSION = "1.0.0"

# Fixed section order: identical inputs render byte-identically.
STATUS_SECTIONS = ("health", "readiness", "system", "workers", "schedules")

STATE_OK = "OK"
STATE_UNREACHABLE = "STACK_UNREACHABLE"
STATE_UNVERIFIABLE = "UNVERIFIABLE"

# Fail-closed whole-view marker: rendered when ANY transport call fails.
# There is no cached/green fallback path in this module by construction.
UNREACHABLE_DOCUMENT_STATE = STATE_UNREACHABLE

DEFAULT_PACK_PATH = (
    Path(__file__).resolve().parents[3] / "control-plane" / "contracts" / "console-contract.json"
)


class ConsoleRefusal(Exception):
    """Fail-closed refusal raised BEFORE any request is issued."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail

    def to_dict(self) -> dict:
        return {"refusal": self.reason, "detail": self.detail}


def load_read_surfaces(pack_path: Optional[Path] = None) -> dict:
    """Load the frozen contract pack, fail-closed (matrix X5).

    Returns a mapping ``surface_id -> declared GET route`` for exactly the
    declared read surfaces that carry a route. Embedded or malformed
    entries are refused rather than guessed around.
    """
    path = Path(pack_path) if pack_path is not None else DEFAULT_PACK_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConsoleRefusal("pack_unreadable", str(exc)) from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("reads"), list):
        raise ConsoleRefusal("pack_malformed", "reads section missing")
    surfaces: dict[str, str] = {}
    for entry in raw["reads"]:
        if not isinstance(entry, dict) or entry.get("kind") != "read":
            raise ConsoleRefusal("pack_malformed", f"non-read entry: {entry!r}")
        surface = entry.get("surface")
        route = entry.get("binds_to", {}).get("http_route", "")
        if not isinstance(surface, str) or not surface:
            raise ConsoleRefusal("pack_malformed", "read entry without surface id")
        if not route.startswith("GET "):
            # denial.read / evidence.read are embedded bindings, not routes.
            continue
        surfaces[surface] = route[len("GET "):]
    if not surfaces:
        raise ConsoleRefusal("pack_malformed", "no requestable read surfaces")
    return surfaces


def section_route(surfaces: Mapping[str, str], section: str) -> str:
    """Map a status section to its declared GET route, fail-closed.

    The five status sections bind to the pack's declared read surfaces by
    their frozen names; an unknown or non-requestable surface is refused
    (matrix X6) rather than resolved by any fallback.
    """
    binding = {
        "health": "health.read",
        "readiness": "readiness.read",
        "system": "system.read",
        "workers": "workers.list",
        "schedules": "jobs.schedules",
    }.get(section)
    if binding is None or binding not in surfaces:
        raise ConsoleRefusal("unsupported_surface", section)
    return surfaces[binding]


def project_section(section: str, response: object) -> dict:
    """Project one governed APIResponse dict VERBATIM into its section.

    The governed envelope shape is ``{ok, status, data, error,
    request_id}``; anything else renders ``UNVERIFIABLE`` — the kernel
    never fabricates, renames, defaults, or reinterprets a field (G7
    verbatim law; matrix F-5).
    """
    if not isinstance(response, dict):
        return {
            "state": STATE_UNVERIFIABLE,
            "reason": "response_not_an_envelope",
            "raw": response,
        }
    if not all(k in response for k in ("ok", "status", "data")):
        # A governed non-envelope body (e.g. the HTTP layer's 401 detail)
        # is still DATA: preserved verbatim, never fabricated into a
        # success or silently dropped (X3/X4; matrix F-5).
        return {
            "state": STATE_UNVERIFIABLE,
            "reason": "envelope_fields_missing",
            "raw": response,
        }
    return {
        "state": STATE_OK,
        "response": {
            "ok": response["ok"],
            "status": response["status"],
            "data": response["data"],
            "error": response.get("error", ""),
            "request_id": response.get("request_id", ""),
        },
    }


def build_status_document(
    fetch: Callable[[str], object],
    surfaces: Optional[Mapping[str, str]] = None,
) -> dict:
    """Build the full status document through ONE injected read path.

    ``fetch(route)`` performs the contract-validated GET and returns the
    parsed governed envelope, or raises on any transport failure. A
    transport failure collapses the ENTIRE document to
    ``STACK_UNREACHABLE`` (F-1): no partial green, no cached section, no
    fallback. Sections are fetched and rendered in the fixed
    ``STATUS_SECTIONS`` order for byte-identical determinism.
    """
    if surfaces is None:
        surfaces = load_read_surfaces()
    sections: dict[str, dict] = {}
    for section in STATUS_SECTIONS:
        route = section_route(surfaces, section)
        try:
            response = fetch(route)
        except Exception:
            # Fail closed, whole view: F-1. No section survives a
            # transport failure as green, and nothing is cached.
            return {
                "kind": CONSOLE_KIND,
                "version": CONSOLE_STATUS_VERSION,
                "state": UNREACHABLE_DOCUMENT_STATE,
                "sections": {},
            }
        sections[section] = project_section(section, response)
    state = STATE_OK
    for section in sections.values():
        if section["state"] != STATE_OK:
            state = STATE_UNVERIFIABLE
            break
    return {
        "kind": CONSOLE_KIND,
        "version": CONSOLE_STATUS_VERSION,
        "state": state,
        "sections": sections,
    }


def render_status(document: Mapping[str, object]) -> str:
    """Deterministic render: identical documents -> byte-identical text."""
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
