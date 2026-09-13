"""OKX v5 error-envelope -> typed acquisition-failure mapping (SENSOR-B3-I07).

OKX v5 responses are provider-native envelopes:

    {"code": "...", "msg": "...", "data": [...]}

Success is `code == "0"`.  A NONZERO provider code is a provider failure and is
NEVER treated as EMPTY_VALID — even when it rides an HTTP 200.  The whole raw
envelope is preserved upstream; only a redacted message is attached to the
typed acquisition-failure context.

Code -> class mapping is evidence-grounded from the committed Bloc 2 probe
characterization (probe.CODE_FAILURE) and is NOT blindly frozen:
committed live runtime evidence wins where it refines it.

Rate-limit family: 50011 / 50012 / 50110 / 50111
Invalid instrument: 51001 ("Instrument ID does not exist")
Auth family: 50113 ("Please login")
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
RATE_LIMIT_CODES: frozenset[str] = frozenset({"50011", "50012", "50110", "50111"})
INVALID_INSTRUMENT_CODES: frozenset[str] = frozenset({"51001"})
AUTH_CODES: frozenset[str] = frozenset({"50113"})


def okx_provider_code(body: Any) -> str | None:
    """Return the OKX provider `code` string when this is an OKX envelope.

    Returns None when the body is not an OKX `{code, msg, data}` object with a
    string code.  Success is `"0"`.
    """
    if isinstance(body, dict) and isinstance(body.get("code"), str):
        return body["code"].strip()
    return None


def is_okx_error_body(body: Any) -> bool:
    """True when the body is an OKX error envelope (nonzero code, not success)."""
    code = okx_provider_code(body)
    return code is not None and code != "0"


def is_okx_success(body: Any) -> bool:
    """True when the body is an OKX success envelope (`code == "0"`), with or
    without data.  A valid empty `data` list is distinct from provider error."""
    code = okx_provider_code(body)
    return code is not None and code == "0"


def map_okx_error(
    provider_id: str,
    sensor_family: SensorFamily,
    body: Any,
    http_status: int,
    *,
    request_fingerprint: str | None = None,
) -> AcquisitionError:
    """Return a typed `AcquisitionError` for an OKX failure.

    Classification order (evidence-grounded):
    provider code -> rate-limit / invalid-instrument / auth; HTTP band ->
    access(class/geo) / provider-unavailable / semantic.  Any nonzero OKX code
    or non-2xx status is a typed failure — it is never EMPTY_VALID/`[]`/`0`.
    """
    code = okx_provider_code(body)
    message = body.get("msg") if isinstance(body, dict) else None
    redacted = str(message)[:200] if isinstance(message, str) else None

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

    # provider-native codes take priority over HTTP band
    if code is not None and code != "0":
        if code in RATE_LIMIT_CODES:
            return _build(RateLimited)
        if code in INVALID_INSTRUMENT_CODES:
            return _build(InvalidInstrument)
        if code in AUTH_CODES:
            return _build(AuthenticationRequired)
        # any other nonzero provider code is a semantic/request error
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
    "RATE_LIMIT_CODES",
    "INVALID_INSTRUMENT_CODES",
    "is_okx_error_body",
    "is_okx_success",
    "map_okx_error",
    "okx_provider_code",
]