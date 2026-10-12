"""Loopback-only transport for the OCE console (B5-I4, charter increment I-3).

The ONLY egress this package is capable of: GET requests to declared
contract-pack routes on a loopback base URL. Laws enforced here, before
any socket I/O (charter sections 5/6; B5-I4 failure matrix X1/X2/X3):

- base URL must be ``http://`` with a literal loopback host
  (``127.0.0.1``, ``::1``, ``localhost``) — anything else (RFC1918,
  public, link-local, IPv6 non-loopback, hostname, userinfo, https,
  other schemes) is refused fail-closed BEFORE request construction;
- GET only: no POST/PUT/PATCH/DELETE code path exists in this module;
- only routes declared in the frozen contract pack are requestable —
  the route set is fixed at construction from the pack, never caller-
  widened, and a redirect cannot widen it either;
- grant/actor identity values are operator inputs passed through verbatim
  in headers; the transport mints nothing and never retries silently;
- connection-level failure raises ``StackUnreachable`` so the kernel can
  collapse the whole view to ``STACK_UNREACHABLE`` (F-1 fail-closed).

B5-I4-X2 (demonstrated defects repaired here, both closed BEFORE any
socket I/O):

- **Ambient proxy authority removed.** The client owns ONE opener built
  with an EMPTY proxy map, so ``http_proxy``/``https_proxy``/``no_proxy``
  environment variables or the Windows proxy registry can never divert a
  declared loopback read to a third-party host. Before this repair a
  read of ``http://127.0.0.1:8448/api/health`` with ``http_proxy`` set
  demonstrably opened a connection to the proxy host instead.
- **Redirects cannot escape the frozen boundary.** A 3xx answer is DATA
  from the loopback stack, but FOLLOWING it is new I/O: the target must
  be a declared route on a loopback host or the redirect is refused
  fail-closed before the follow-up request is constructed. Before this
  repair a loopback ``302 Location: http://10.0.0.5:8080/escaped``
  demonstrably opened a connection to that non-loopback host.

Stdlib only (urllib, socket); no LLM; no provider; no telemetry.
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Mapping, Optional

from .kernel import ConsoleRefusal, load_read_surfaces

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
ALLOWED_SCHEME = "http"
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_IDENTITY_CHARS = 256


class StackUnreachable(Exception):
    """Transport-level failure: the local stack could not answer a read."""


class _LoopbackRouteRedirect(urllib.request.HTTPRedirectHandler):
    """Redirect policy closed over the frozen route table (B5-I4-X2).

    ``redirect_request`` runs before urllib builds the follow-up
    ``Request``, so a refused target performs no socket I/O at all.
    """

    def __init__(self, routes: Mapping[str, str]):
        super().__init__()
        self._allowed_paths = frozenset(routes.values())

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urljoin(req.full_url, newurl)
        parsed = urllib.parse.urlsplit(target)
        if parsed.scheme != ALLOWED_SCHEME or (parsed.hostname or "").lower() not in LOOPBACK_HOSTS:
            raise ConsoleRefusal("non_loopback_refused", f"redirect target {newurl!r}")
        if parsed.path not in self._allowed_paths:
            raise ConsoleRefusal("unsupported_surface", f"redirect target {newurl!r}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_url(opener, request, timeout):
    """The single socket-I/O seam of this package (tests may substitute it).

    Everything reachable from the console happens through this one
    function; nothing else in the package opens a connection.
    """
    return opener.open(request, timeout=timeout)


def _validate_identity(kind: str, value: str) -> str:
    """Refuse malformed identity header values fail-closed, before any I/O.

    Operator-supplied grant/actor ids are passed through verbatim — the
    transport mints nothing — but a value carrying header separators or
    exceeding the bound is refused at construction (matrix X2) rather
    than handed to the HTTP layer.
    """
    text = str(value)
    if any(ch in text for ch in ("\r", "\n", "\t")):
        raise ConsoleRefusal("malformed_identity", f"{kind} contains control characters")
    if len(text) > MAX_IDENTITY_CHARS:
        raise ConsoleRefusal("malformed_identity", f"{kind} exceeds {MAX_IDENTITY_CHARS} chars")
    return text


def validate_base_url(base_url: str) -> str:
    """Refuse any non-loopback base URL fail-closed, before any I/O.

    This runs BEFORE a Request object or socket exists: no resolution,
    no connection, no header construction happens for a refused URL
    (matrix X1/X2).
    """
    if not isinstance(base_url, str) or not base_url:
        raise ConsoleRefusal("malformed_base_url", "empty or non-string base URL")
    for ch in ("@", " ", "\t", "\r", "\n", "#", "?"):
        if ch in base_url:
            raise ConsoleRefusal("malformed_base_url", "forbidden character in base URL")
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme != ALLOWED_SCHEME:
        raise ConsoleRefusal("non_loopback_refused", f"scheme {parsed.scheme!r}")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ConsoleRefusal("malformed_base_url", "base URL must be scheme+host[:port] only")
    host = parsed.hostname
    if host is None or host.lower() not in LOOPBACK_HOSTS:
        raise ConsoleRefusal("non_loopback_refused", f"host {host!r}")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ConsoleRefusal("malformed_base_url", f"invalid port: {exc}") from exc
    if port is not None and not (0 < port < 65536):
        raise ConsoleRefusal("malformed_base_url", "port out of range")
    return base_url.rstrip("/")


class LoopbackTransport:
    """GET-only client over declared contract-pack routes, loopback only."""

    def __init__(
        self,
        base_url: str,
        grant_id: str = "",
        actor_id: str = "",
        surfaces: Optional[Mapping[str, str]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        # Order matters: validate the base URL BEFORE the route table is
        # even loaded, so a hostile URL performs zero work.
        self._base = validate_base_url(base_url)
        self._surfaces = dict(surfaces) if surfaces is not None else load_read_surfaces()
        if not self._surfaces:
            raise ConsoleRefusal("pack_malformed", "no requestable read surfaces")
        self._grant = _validate_identity("grant", grant_id)
        self._actor = _validate_identity("actor", actor_id)
        self._timeout = float(timeout)
        # One opener, owned by this client: no ambient proxy authority
        # (empty proxy map) and a redirect policy closed over the same
        # frozen route table (B5-I4-X2).
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            _LoopbackRouteRedirect(self._surfaces),
        )

    @property
    def routes(self) -> dict:
        """The fixed route table (surface id -> GET route). Caller-widening
        is impossible: this is the complete requestable set."""
        return dict(self._surfaces)

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self._grant or self._actor:
            # Operator-supplied identity, passed through verbatim. The
            # transport never mints, pads, or reinterprets it (charter
            # section 5 rule 3); a missing/invalid grant produces the
            # governed denial, rendered verbatim upstream (X3).
            headers["X-OCE-Grant"] = self._grant
            headers["X-OCE-Actor"] = self._actor
        return headers

    def read(self, surface: str) -> object:
        """Perform one declared GET; return the parsed governed envelope.

        Raises ``ConsoleRefusal`` for an undeclared surface (refused
        before any I/O) and ``StackUnreachable`` for any transport-level
        failure — never a fabricated or cached answer.
        """
        route = self._surfaces.get(surface)
        if route is None:
            raise ConsoleRefusal("unsupported_surface", surface)
        url = f"{self._base}{route}"
        request = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with _open_url(self._opener, request, self._timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            # A governed HTTP answer (401/403 denial, 5xx) is DATA, not a
            # transport failure: surface the body verbatim for the kernel
            # to project; the denial path is never reinterpreted (X3/X4).
            body = exc.read()
        except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as exc:
            raise StackUnreachable(f"{surface}: {exc}") from exc
        try:
            return json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise StackUnreachable(f"{surface}: unparseable body") from exc

    def read_status(self) -> dict:
        """Convenience: build the kernel status document over this client."""
        from .kernel import build_status_document

        return build_status_document(self.read, self._surfaces)
