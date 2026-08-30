"""Gate Futures request builders (SENSOR-B3-I06).

Centralized construction of the two Gate acquisition surfaces; URL/parameter
logic never leaks into parsers.

- `contract_stats` (OI / LIQUIDATION / POSITIONING):
  `GET /api/v4/futures/usdt/contract_stats?contract=&from=&interval=&limit=`
  `from` is Unix SECONDS (NOT ms), `interval` is a provider STRING bucket
  ("1h" — NOT seconds), and NO `to` is invented.
- `funding_rate`:
  `GET /api/v4/futures/usdt/funding_rate?contract=&from=&to=`
  `from`/`to` are Unix SECONDS; no interval parameter (funding rows are
  event/effective records, not resampled bars).

Granularity is fail-closed: an explicit unsupported Granularity raises typed
`UnsupportedGranularity` BEFORE transport (never silently defaulted).
"""

from __future__ import annotations

from ...contracts.enums import SensorFamily
from ..base.enums import Granularity
from ..base.errors import UnsupportedGranularity
from ..base.models import FetchRequest
from .capabilities import (
    GATE_CONTRACT_STATS_PATH,
    GATE_FUNDING_RATE_PATH,
    GATE_USDT_BASE,
)

#: Provider string bucket for the evidence-backed 1h window on contract_stats.
GATE_INTERVAL_1H = "1h"

#: Configured default page for contract_stats window requests (no committed
#: evidence pins the exact default; `request.page_size_hint` overrides).
GATE_CONTRACT_STATS_DEFAULT_LIMIT = 100

#: The ONLY contract_stats granularity with committed evidence is 1h.
_CONTRACT_STATS_INTERVAL_BY_GRANULARITY: dict[Granularity, str] = {
    Granularity.G1H: GATE_INTERVAL_1H,
}


def _resolve_contract_stats_interval(
    request: FetchRequest,
) -> str:
    """Map an explicit granularity to the provider interval STRING bucket.

    `None` uses the documented 1h default; a supported member maps exactly to
    its evidence-backed bucket; any other explicit member raises typed
    `UnsupportedGranularity` BEFORE transport.
    """
    if request.granularity is None:
        return GATE_INTERVAL_1H
    bucket = _CONTRACT_STATS_INTERVAL_BY_GRANULARITY.get(request.granularity)
    if bucket is None:
        raise UnsupportedGranularity(
            provider_id=request.provider_id,
            sensor_family=request.sensor_family,
            detail=(
                f"Gate contract_stats granularity "
                f"{request.granularity.value} is not evidence-backed "
                "(only 1h / granularity None is supported)"
            ),
        )
    return bucket


def _validate_funding_granularity(request: FetchRequest) -> None:
    """Funding is event/effective records from /funding_rate — no bar interval.

    `None` or the documented G1H observation target is accepted (no interval
    query parameter is emitted); any other explicit member is incompatible with
    the single-contract funding surface and fails typed before transport.
    """
    if request.granularity is not None and request.granularity is not Granularity.G1H:
        raise UnsupportedGranularity(
            provider_id=request.provider_id,
            sensor_family=request.sensor_family,
            detail=(
                f"Gate /funding_rate does not resample into "
                f"{request.granularity.value} bars (event/effective records "
                "only; no interval parameter is sent)"
            ),
        )


class GateRequestBuilder:
    """Build Gate-native request (url, params) tuples for promoted sensors."""

    def endpoint_family(self, sensor: SensorFamily) -> str:
        if sensor is SensorFamily.MECHANICAL_FUNDING:
            return "gate-futures-funding_rate"
        return "gate-futures-contract_stats"

    def build(self, request: FetchRequest) -> tuple[str, dict[str, int]]:
        sensor = request.sensor_family
        if sensor is SensorFamily.MECHANICAL_FUNDING:
            return self._build_funding(request)
        if sensor in {
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            SensorFamily.MECHANICAL_LIQUIDATION,
            SensorFamily.MECHANICAL_POSITIONING,
        }:
            return self._build_contract_stats(request)
        raise ValueError(f"no Gate request builder for sensor {sensor.value}")

    def _build_contract_stats(
        self, request: FetchRequest
    ) -> tuple[str, dict[str, int]]:
        interval = _resolve_contract_stats_interval(request)
        params: dict[str, int] = {
            "contract": request.native_instrument_id,
            "from": int(request.start_time.timestamp()),
            "interval": interval,
            "limit": request.page_size_hint or GATE_CONTRACT_STATS_DEFAULT_LIMIT,
        }
        # NO `to` is invented for contract_stats — traversal is the
        # from/interval/limit window (evidence honesty; never add `to`).
        url = f"https://{GATE_USDT_BASE}{GATE_CONTRACT_STATS_PATH}"
        return url, params

    def _build_funding(self, request: FetchRequest) -> tuple[str, dict[str, int]]:
        _validate_funding_granularity(request)
        params: dict[str, int] = {
            "contract": request.native_instrument_id,
            "from": int(request.start_time.timestamp()),
            "to": int(request.end_time.timestamp()),
        }
        url = f"https://{GATE_USDT_BASE}{GATE_FUNDING_RATE_PATH}"
        return url, params