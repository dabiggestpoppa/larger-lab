"""Kraken error-envelope -> typed acquisition-failure mapping (SENSOR-B3-I05).

Kraken returns errors both as non-2xx HTTP and, for the Market Analytics
family, as an envelope with an `errors` list (each `{msg, error_class}`).  Map
both to the frozen typed taxonomy so a provider failure is NEVER reported as
`[]`/`0`/`None`/EMPTY_VALID.  No secret material is attached — only a redacted
message is placed into provider-native context.
"""

from __future__ import annotations

from typing import Any

from ...contracts.enums import SensorFamily
from ..base.errors import (
    AccessClassViolation,
    AcquisitionError,
    AuthenticationRequired,
    GeoRestricted,
    InvalidInstrument,
    ProviderSemanticError,
    ProviderUnavailable,
    RateLimited,
)


def is_kraken_error_body(body: Any) -> bool:
    """True when an `errors` list is present and non-empty (analytics family)."""
    return (
        isinstance(body, dict)
        and isinstance(body.get("errors"), list)
        and bool(body["errors"])
    )


def _redacted_message(body: Any) -> str:
    parts: list[str] = []
    if isinstance(body, dict) and isinstance(body.get("errors"), list):
        for err in body["errors"]:
            if isinstance(err, dict) and isinstance(err.get("msg"), str):
                parts.append(err["msg"][:200])
    if isinstance(body, dict) and isinstance(body.get("error"), str):
        parts.append(body["error"][:200])
    return " | ".join(parts) if parts else ""


def map_kraken_error(
    provider_id: str,
    sensor_family: SensorFamily,
    body: Any,
    http_status: int,
    *,
    request_fingerprint: str | None = None,
) -> AcquisitionError:
    """Return a typed `AcquisitionError` for a Kraken failure response.

    Classification is evidence-grounded: symbol/instrument errors are
    `InvalidInstrument`, rate limit -> `RateLimited`, geo/region -> `GeoRestricted`,
    auth/permission -> `AuthenticationRequired`, HTTP 429 -> `RateLimited`,
    HTTP 451/403 with region -> `GeoRestricted`, HTTP 5xx -> `ProviderUnavailable`;
    everything else stays `ProviderSemanticError`.
    """
    message = (_redacted_message(body) or str(http_status)).lower()

    def _build(cls: type[AcquisitionError]) -> AcquisitionError:
        return cls(
            provider_id=provider_id,
            sensor_family=sensor_family,
            request_fingerprint=request_fingerprint,
            provider_native_context_redacted={"http_status": http_status},
            detail=_redacted_message(body) or f"HTTP {http_status}",
        )

    if http_status == 429:
        return _build(RateLimited)

    if any(tok in message for tok in ("rate limit", "too many requests", "quota")) and (
        http_status in (429, 400)
    ):
        return _build(RateLimited)

    if any(tok in message for tok in ("symbol", "instrument")):
        return _build(InvalidInstrument)

    if any(tok in message for tok in ("geo", "region", "restricted location")):
        return _build(GeoRestricted)

    if http_status in (451, 403) and any(tok in message for tok in ("geo", "region")):
        return _build(GeoRestricted)

    if any(
        tok in message
        for tok in ("permission", "auth", "unauthorized", "forbidden", "credential")
    ):
        return _build(AuthenticationRequired)

    if http_status == 403:
        return _build(AccessClassViolation)

    if 400 <= http_status < 500:
        return _build(ProviderSemanticError)

    if http_status >= 500:
        return _build(ProviderUnavailable)

    return _build(ProviderSemanticError)