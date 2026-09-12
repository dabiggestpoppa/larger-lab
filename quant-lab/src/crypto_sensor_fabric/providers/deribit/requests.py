"""Deribit v2 public request builders (SENSOR-B3-I08).

Centralized construction of the four Deribit acquisition surfaces; URL /
parameter logic never leaks into parsers.

- `MECHANICAL_TRADE` + `MECHANICAL_LIQUIDATION`:
  `GET /api/v2/public/get_last_trades_by_instrument` with
  `instrument_name`, `start_timestamp`, `end_timestamp` (epoch MILLISECONDS),
  `count` (<= 1000) and `include_old=true` (REQUIRED for historical depth).
  The result envelope carries `has_more`; rows live under `result.trades`.
  Both sensors share the physical surface but remain distinct logical
  observations (never a combined state).
- `MECHANICAL_FUNDING`:
  `GET /api/v2/public/get_funding_rate_history` with `instrument_name`,
  `start_timestamp`, `end_timestamp` (epoch MILLISECONDS), `count` (<= 1000).
  Observed LIVE: `result` is a RAW LIST (NOT `{data:[...]}`).
- `MECHANICAL_BOOK_SNAPSHOT`:
  `GET /api/v2/public/get_order_book` with `instrument_name`, `depth=25`.
  CURRENT snapshot only — NO `start`/`end`/cursor/historical replay.

Granularity is fail-closed per sensor: an explicitly unsupported Granularity
raises typed `UnsupportedGranularity` BEFORE transport.  Trade/liquidation are
raw event surfaces (RAW_EVENT); funding is an hourly record surface (1h); the
book is a snapshot surface (BOOK_SNAPSHOT).  The `1h` label in some Bloc 2
evidence ids is the probe's sampling interval, NOT a bar-resampling contract.
"""

from __future__ import annotations

from typing import Any

from ...contracts.enums import SensorFamily
from ..base.enums import Granularity
from ..base.errors import UnsupportedGranularity
from ..base.models import FetchRequest
from .capabilities import (
    DERIBIT_BOOK_DEPTH,
    DERIBIT_FUNDING_RATE_HISTORY_PATH,
    DERIBIT_LAST_TRADES_PATH,
    DERIBIT_ORDER_BOOK_PATH,
    DERIBIT_PAGE_LIMIT,
    DERIBIT_REST_BASE,
    deribit_endpoint_family,
)

#: Granularity acceptance by sensor.  `None` (default) is always accepted.
_TRADE_ACCEPTED: frozenset[Granularity] = frozenset({Granularity.RAW_EVENT})
_LIQUIDATION_ACCEPTED: frozenset[Granularity] = frozenset({Granularity.RAW_EVENT})
_FUNDING_ACCEPTED: frozenset[Granularity] = frozenset({Granularity.G1H})
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
                f"Deribit {request.sensor_family.value} does not support "
                f"granularity {request.granularity.value!r} (accepted="
                + ",".join(sorted(g.value for g in accepted))
                + " or None)"
            ),
        )


def _ms_epoch(dt: Any) -> int:
    """Request timestamp in provider-native epoch MILLISECONDS.

    Deribit's public history surfaces accept `start_timestamp` /
    `end_timestamp` in epoch milliseconds (live_probe_contracts.yaml
    start_unit=end_unit=epoch_milliseconds).
    """
    return int(dt.timestamp() * 1000)


class DeribitRequestBuilder:
    """Build Deribit-native request (url, params) tuples for promoted sensors."""

    def endpoint_family(self, sensor: SensorFamily) -> str:
        return deribit_endpoint_family(sensor)

    def build(self, request: FetchRequest) -> tuple[str, dict[str, Any]]:
        sensor = request.sensor_family
        if sensor is SensorFamily.MECHANICAL_TRADE:
            return self._build_trades(request)
        if sensor is SensorFamily.MECHANICAL_LIQUIDATION:
            return self._build_liquidations(request)
        if sensor is SensorFamily.MECHANICAL_FUNDING:
            return self._build_funding(request)
        if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            return self._build_book(request)
        raise ValueError(f"no Deribit request builder for sensor {sensor.value}")

    def _build_trades(self, request: FetchRequest) -> tuple[str, dict[str, Any]]:
        _validate_granularity(request, _TRADE_ACCEPTED)
        params: dict[str, Any] = {
            "instrument_name": request.native_instrument_id,
            "start_timestamp": _ms_epoch(request.start_time),
            "end_timestamp": _ms_epoch(request.end_time),
            "count": request.page_size_hint or DERIBIT_PAGE_LIMIT,
            "include_old": True,  # REQUIRED for historical depth (probe §10.1)
        }
        url = f"https://{DERIBIT_REST_BASE}{DERIBIT_LAST_TRADES_PATH}"
        return url, params

    def _build_liquidations(self, request: FetchRequest) -> tuple[str, dict[str, Any]]:
        _validate_granularity(request, _LIQUIDATION_ACCEPTED)
        # SAME physical surface as trade; distinct logical sensor view.
        params: dict[str, Any] = {
            "instrument_name": request.native_instrument_id,
            "start_timestamp": _ms_epoch(request.start_time),
            "end_timestamp": _ms_epoch(request.end_time),
            "count": request.page_size_hint or DERIBIT_PAGE_LIMIT,
            "include_old": True,
        }
        url = f"https://{DERIBIT_REST_BASE}{DERIBIT_LAST_TRADES_PATH}"
        return url, params

    def _build_funding(self, request: FetchRequest) -> tuple[str, dict[str, Any]]:
        _validate_granularity(request, _FUNDING_ACCEPTED)
        params: dict[str, Any] = {
            "instrument_name": request.native_instrument_id,
            "start_timestamp": _ms_epoch(request.start_time),
            "end_timestamp": _ms_epoch(request.end_time),
            "count": request.page_size_hint or DERIBIT_PAGE_LIMIT,
        }
        url = f"https://{DERIBIT_REST_BASE}{DERIBIT_FUNDING_RATE_HISTORY_PATH}"
        return url, params

    def _build_book(self, request: FetchRequest) -> tuple[str, dict[str, Any]]:
        _validate_granularity(request, _BOOK_ACCEPTED)
        params: dict[str, Any] = {
            "instrument_name": request.native_instrument_id,
            "depth": DERIBIT_BOOK_DEPTH,
        }
        # Current-only snapshot: no start/end/cursor/historical replay.
        url = f"https://{DERIBIT_REST_BASE}{DERIBIT_ORDER_BOOK_PATH}"
        return url, params
