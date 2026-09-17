"""OKX Swap request builders (SENSOR-B3-I07).

Centralized construction of the three OKX acquisition surfaces; URL / parameter
logic never leaks into parsers.

- `MECHANICAL_TRADE`:
  `GET /api/v5/market/history-trades?instId=&limit=`
  Provider-native cursor params are `after`/`before` keyed around trade ids,
  but their direction is UNRESOLVED by committed I13 evidence, so production
  issues a single evidence-backed request window (`instId` + `limit`) and does
  NOT invent a `after`/`before` continuation value.
- `MECHANICAL_FUNDING`:
  `GET /api/v5/public/funding-rate-history?instId=&limit=`
  PUBLIC namespace (NOT `/market`).  Same single-window policy; no invented
  interval query parameter (funding is `fundingTime`-keyed records, and the
  interval is NOT frozen to "8h").
- `MECHANICAL_BOOK_SNAPSHOT`:
  `GET /api/v5/market/books?instId=&sz=400`
  CURRENT snapshot only — NO `start`/`end`/`after`/`before`/historical cursor,
  no historical depth (deep book history UNVERIFIED, never claimed).

Granularity is fail-closed per sensor: an explicitly unsupported Granularity
raises typed `UnsupportedGranularity` BEFORE transport.
"""

from __future__ import annotations

from typing import Any

from ...contracts.enums import SensorFamily
from ..base.enums import Granularity
from ..base.errors import UnsupportedGranularity
from ..base.models import FetchRequest
from .capabilities import (
    OKX_BOOK_SNAPSHOT_SZ,
    OKX_FUNDING_RATE_HISTORY_PATH,
    OKX_HISTORY_TRADES_PATH,
    OKX_MARKET_BOOKS_PATH,
    OKX_PAGE_LIMIT,
    OKX_REST_BASE,
    okx_endpoint_family,
)

#: Granularity acceptance by sensor.  `None` (default) is always accepted.
#: Funding and trade are record surfaces (not arbitrary resampled bars), so
#: only the event/record-native granularities are accepted.
_FUNDING_ACCEPTED: frozenset[Granularity] = frozenset({Granularity.G1H})
_TRADE_ACCEPTED: frozenset[Granularity] = frozenset({Granularity.RAW_EVENT})
_BOOK_ACCEPTED: frozenset[Granularity] = frozenset({Granularity.BOOK_SNAPSHOT})


def _validate_granularity(
    request: FetchRequest,
    accepted: frozenset[Granularity],
) -> None:
    """Fail closed on an explicit unsupported granularity (before transport)."""
    if request.granularity is not None and request.granularity not in accepted:
        raise UnsupportedGranularity(
            provider_id=request.provider_id,
            sensor_family=request.sensor_family,
            detail=(
                f"OKX {request.sensor_family.value} does not support "
                f"granularity {request.granularity.value!r} (accepted="
                + ",".join(sorted(g.value for g in accepted))
                + " or None)"
            ),
        )


class OkxRequestBuilder:
    """Build OKX-native request (url, params) tuples for promoted sensors."""

    def endpoint_family(self, sensor: SensorFamily) -> str:
        return okx_endpoint_family(sensor)

    def build(self, request: FetchRequest) -> tuple[str, dict[str, Any]]:
        sensor = request.sensor_family
        if sensor is SensorFamily.MECHANICAL_TRADE:
            return self._build_trades(request)
        if sensor is SensorFamily.MECHANICAL_FUNDING:
            return self._build_funding(request)
        if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            return self._build_book(request)
        raise ValueError(f"no OKX request builder for sensor {sensor.value}")

    def _build_trades(self, request: FetchRequest) -> tuple[str, dict[str, Any]]:
        _validate_granularity(request, _TRADE_ACCEPTED)
        params: dict[str, Any] = {
            "instId": request.native_instrument_id,
            "limit": request.page_size_hint or OKX_PAGE_LIMIT,
        }
        # after/before cursor direction is UNRESOLVED by evidence; do not
        # invent a continuation value for the single production window.
        url = f"https://{OKX_REST_BASE}{OKX_HISTORY_TRADES_PATH}"
        return url, params

    def _build_funding(self, request: FetchRequest) -> tuple[str, dict[str, Any]]:
        _validate_granularity(request, _FUNDING_ACCEPTED)
        params: dict[str, Any] = {
            "instId": request.native_instrument_id,
            "limit": request.page_size_hint or OKX_PAGE_LIMIT,
        }
        # PUBLIC namespace, never /api/v5/market/funding-rate-history.  No
        # interval query parameter (fundingTime-keyed records; interval not
        # frozen to "8h").
        url = f"https://{OKX_REST_BASE}{OKX_FUNDING_RATE_HISTORY_PATH}"
        return url, params

    def _build_book(self, request: FetchRequest) -> tuple[str, dict[str, Any]]:
        _validate_granularity(request, _BOOK_ACCEPTED)
        params: dict[str, Any] = {
            "instId": request.native_instrument_id,
            "sz": OKX_BOOK_SNAPSHOT_SZ,
        }
        # Current-only snapshot: no start/end/after/before/historical cursor.
        url = f"https://{OKX_REST_BASE}{OKX_MARKET_BOOKS_PATH}"
        return url, params