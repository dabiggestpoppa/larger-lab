"""QL-EXEC-R5 — injectable HTTP transport for the TradeLocker client.

The client talks to a transport protocol, NOT to ``requests`` directly:

- ``UrllibTransport`` — stdlib-only real transport (no third-party deps).
- ``FakeTradeLocker`` — deterministic in-memory provider (tests; zero network).

Failure semantics matter for order safety:

- ``TimeoutBeforeSendError`` — request never left the process. Safe to retry
  (nothing reached the provider).
- ``AmbiguousSendError`` — request MAY have reached the provider. NEVER retry
  an order POST blindly: reconcile provider truth first.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Optional, Protocol


class TransportError(Exception):
    """Base transport failure (network-level, not an HTTP status)."""


class TimeoutBeforeSendError(TransportError):
    """Connect timeout: the request was never transmitted."""


class AmbiguousSendError(TransportError):
    """Timeout after the request may have been sent. Fill truth unknown."""


@dataclass
class HttpRequest:
    """Normalized request envelope shared by transport and fake provider."""

    method: str
    url: str  # full URL (path only is accepted and resolved by transport)
    headers: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    json_body: Optional[dict] = None
    timeout: tuple = (10, 30)  # (connect, read)


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict = field(default_factory=dict)
    body: str = ""

    def json(self) -> dict:
        if not self.body:
            raise ValueError("empty response body")
        try:
            parsed = json.loads(self.body)
        except json.JSONDecodeError as err:
            raise ValueError(f"malformed JSON response: {err}") from err
        if not isinstance(parsed, dict):
            raise ValueError(f"expected JSON object, got {type(parsed).__name__}")
        return parsed


class HttpTransport(Protocol):
    """Minimal transport the TradeLocker client depends on."""

    def request(self, request: HttpRequest) -> HttpResponse: ...


class UrllibTransport:
    """Stdlib urllib transport. No third-party HTTP dependency."""

    def request(self, request: HttpRequest) -> HttpResponse:
        url = request.url
        if request.params:
            url = _join_query(url, request.params)
        req = urllib.request.Request(
            url,
            method=request.method,
            headers=request.headers,
        )
        if request.json_body is not None:
            req.add_header("Content-Type", "application/json")
            data = json.dumps(request.json_body).encode("utf-8")
        else:
            data = None
        try:
            with urllib.request.urlopen(
                req, data=data, timeout=request.timeout[1]
            ) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return HttpResponse(
                    status=resp.status,
                    headers=dict(resp.headers.items()),
                    body=body,
                )
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", errors="replace")
            return HttpResponse(status=err.code, headers=dict(err.headers.items()), body=body)
        except TimeoutError as err:
            # A read/connect timeout cannot distinguish before/after send from
            # here. Treat as AMBIGUOUS for write methods; callers that know the
            # request was a pure read may downgrade.
            raise AmbiguousSendError(f"transport timeout: {err}") from err
        except urllib.error.URLError as err:
            reason = getattr(err, "reason", err)
            raise TransportError(f"transport error: {reason}") from err


def _join_query(url: str, params: dict) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = dict(urllib.parse.parse_qsl(parsed.query))
    query.update({k: str(v) for k, v in params.items()})
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
    )
