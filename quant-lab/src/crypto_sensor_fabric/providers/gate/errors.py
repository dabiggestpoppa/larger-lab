"""Gate error-envelope -> typed acquisition-failure mapping (SENSOR-B3-I06).

Gate returns errors both as non-2xx HTTP and as a `{"label": "...", "message":
"..."}` body.  Map both to the frozen typed taxonomy so a provider failure is
NEVER reported as `[]`/`0`/`None`/EMPTY_VALID.  The verified rolling ~180-day
retention boundary ("from time exceeds 180-day limit") is typed
`HistoricalRangeUnavailable` (never EMPTY_VALID / auth / unsupported).  Only a
redacted message is attached to provider-native context.
"""

from __future__ import annotations

from typing import Any

from ...contracts.enums import SensorFamily
from ..base.errors import (
    AccessClassViolation,
    AcquisitionError,
    AuthenticationRequired,
    GeoRestricted,
    HistoricalRangeUnavailable,
    InvalidInstrument,
    ProviderSemanticError,
    ProviderUnavailable,
    RateLimited,
)


def is_gate_error_body(body: Any) -> bool:
    """True when the body is a Gate error envelope `{label: str, message: str}`."""
    return (
        isinstance(body, dict)
        and isinstance(body.get("label"), str)
        and (body.get("message") is None or isinstance(body.get("message"), str))
    )


def _redacted_text(body: Any) -> str:
    if is_gate_error_body(body):
        label = body["label"].lower()
        message = str(body.get("message") or "").lower()
        return f"{label} {message}".strip()
    return ""


def map_gate_error(
    provider_id: str,
    sensor_family: SensorFamily,
    body: Any,
    http_status: int,
    *,
    request_fingerprint: str | None = None,
) -> AcquisitionError:
    """Return a typed `AcquisitionError` for a Gate failure response.

    Evidence-grounded classification: 180-day retention boundary ->
    `HistoricalRangeUnavailable`; rate limit / 429 -> `RateLimited`; contract /
    symbol / instrument errors -> `InvalidInstrument`; unauthorized/invalid key
    -> `AuthenticationRequired`; forbidden -> `GeoRestricted` (US region);
    HTTP 403 -> `AccessClassViolation`; HTTP 5xx -> `ProviderUnavailable`;
    any other 4xx -> `ProviderSemanticError`.
    """
    text = _redacted_text(body)

    def _build(cls: type[AcquisitionError]) -> AcquisitionError:
        return cls(
            provider_id=provider_id,
            sensor_family=sensor_family,
            request_fingerprint=request_fingerprint,
            provider_native_context_redacted={
                "http_status": http_status,
                "label": _redacted_text(body) or None,
            },
            detail=_redacted_text(body) or f"HTTP {http_status}",
        )

    # rolling retention boundary (verified live at older eras): NOT an empty
    # window, not auth, not unsupported — typed HistoricalRangeUnavailable.
    if "180-day" in text or "from time exceeds" in text or "180 day" in text:
        return _build(HistoricalRangeUnavailable)

    if http_status == 429 or "rate limit" in text or "too many" in text:
        return _build(RateLimited)

    if any(tok in text for tok in ("contract", "instrument", "symbol", "not found")):
        return _build(InvalidInstrument)

    if "unauthorized" in text or "invalid key" in text or "permission" in text:
        return _build(AuthenticationRequired)

    if "forbidden" in text:
        return _build(GeoRestricted)

    if http_status == 403:
        return _build(AccessClassViolation)

    if http_status >= 500:
        return _build(ProviderUnavailable)

    if 400 <= http_status < 500:
        return _build(ProviderSemanticError)

    return _build(ProviderSemanticError)