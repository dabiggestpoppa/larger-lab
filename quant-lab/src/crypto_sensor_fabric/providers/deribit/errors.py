"""Deribit JSON-RPC error-envelope -> typed acquisition-failure mapping.

Deribit uses JSON-RPC v2 style responses.  A provider error may ride on HTTP
200:

    {"jsonrpc": "2.0", "error": {"code": <int>, "message": "..."}}

HTTP 200 does NOT imply success.  A provider error is NEVER treated as
EMPTY_VALID / [] / 0 / None.

Code -> class mapping is grounded in the committed Bloc 2 probe
characterization (probe.CODE_FAILURE):

    40400  -> invalid instrument
    10001  -> rate limit
    10000 / 10002 -> authentication/access family
    -32601 -> endpoint removed / unsupported
    -32602 -> invalid request / client semantics

Committed live runtime evidence wins where it refines the table (none does
today).  Unknown JSON-RPC errors map to typed `ProviderSemanticError`.
"""

from __future__ import annotations

from typing import Any

from ...contracts.enums import SensorFamily
from ..base.errors import (
    AccessClassViolation,
    AcquisitionError,
    AuthenticationRequired,
    InvalidInstrument,
    ProviderSemanticError,
    ProviderUnavailable,
    RateLimited,
)

#: Committed provider-code classification (Bloc 2 probe.CODE_FAILURE).
INVALID_INSTRUMENT_CODES: frozenset[int] = frozenset({40400})
RATE_LIMIT_CODES: frozenset[int] = frozenset({10001})
AUTH_CODES: frozenset[int] = frozenset({10000, 10002})
ENDPOINT_REMOVED_CODES: frozenset[int] = frozenset({-32601})


def deribit_error_code(body: Any) -> int | None:
    """Return the JSON-RPC `error.code` int when this is a Deribit error body.

    Returns None when the body is not a `{error: {code: <int>, ...}}` object.
    """
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        code = body["error"].get("code")
        if isinstance(code, int) and not isinstance(code, bool):
            return code
    return None


def is_deribit_error_body(body: Any) -> bool:
    """True when the body is a Deribit JSON-RPC error envelope (HTTP 200 ok)."""
    return deribit_error_code(body) is not None


def map_deribit_error(
    provider_id: str,
    sensor_family: SensorFamily,
    body: Any,
    http_status: int,
    *,
    request_fingerprint: str | None = None,
) -> AcquisitionError:
    """Return a typed `AcquisitionError` for a Deribit failure.

    Classification order (evidence-grounded): JSON-RPC error code -> rate-limit
    / invalid-instrument / auth / endpoint-removed / semantic; HTTP band ->
    access(class/geo) / provider-unavailable / semantic.  Any JSON-RPC error or
    non-2xx status is a typed failure — never EMPTY_VALID/`[]`/`0`.
    """
    code = deribit_error_code(body)
    message = None
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        msg = body["error"].get("message")
        if isinstance(msg, str):
            message = msg
    redacted = message[:200] if isinstance(message, str) else None

    def _build(cls: type[AcquisitionError]) -> AcquisitionError:
        return cls(
            provider_id=provider_id,
            sensor_family=sensor_family,
            request_fingerprint=request_fingerprint,
            provider_native_context_redacted={
                "http_status": http_status,
                "code": code,
                "msg_redacted": redacted,
            },
            detail=redacted or f"HTTP {http_status}",
        )

    # JSON-RPC provider codes take priority over the HTTP band.
    if code is not None:
        if code in RATE_LIMIT_CODES:
            return _build(RateLimited)
        if code in INVALID_INSTRUMENT_CODES:
            return _build(InvalidInstrument)
        if code in AUTH_CODES:
            return _build(AuthenticationRequired)
        if code in ENDPOINT_REMOVED_CODES:
            return _build(ProviderSemanticError)
        # any other JSON-RPC error is a semantic/request error
        return _build(ProviderSemanticError)

    if http_status == 429:
        return _build(RateLimited)
    if http_status == 403:
        return _build(AccessClassViolation)
    if http_status >= 500:
        return _build(ProviderUnavailable)
    if 400 <= http_status < 500:
        return _build(ProviderSemanticError)
    return _build(ProviderSemanticError)


__all__ = [
    "AUTH_CODES",
    "ENDPOINT_REMOVED_CODES",
    "INVALID_INSTRUMENT_CODES",
    "RATE_LIMIT_CODES",
    "deribit_error_code",
    "is_deribit_error_body",
    "map_deribit_error",
]
