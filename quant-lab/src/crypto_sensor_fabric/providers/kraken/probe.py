"""Kraken Futures capability probe (bloc_02/02 §5 / 04 §6).

Minimal characterization module — NOT a production adapter.  It declares the
Kraken-specific facts (endpoints, result keys, native units, instrument map,
query shape, error envelopes, pagination) on top of the shared REST probe
base; all characterization logic is offline.  Fetching belongs to the
explicit live run (SENSOR-B2-I13).

Liquidations are not a dedicated endpoint: on /history they appear as trade
rows whose `type` field is "liquidation" (02 §5 probe priorities).
Open interest is current-only via /tickers — historical OI is NOT publicly
exposed and must be characterized as CURRENT_ONLY / HISTORY_BLOCKED, never
assumed.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ...contracts.enums import SensorFamily
from ...probes.enums import AccessMode, ProbeFailureClass
from ...probes.models import CapabilityProbeRequest
from ..rest import RestCapabilityProbeBase

PROVIDER_ID = "KRAKEN_FUTURES"

#: Playbook core basket -> native perpetual symbols (02 §4).
#: MID_TAIL_CONTROL = DOGE: non-core, adequate venue history, no delisting
#: ambiguity where avoidable.  Operator-adjustable at probe-target config time.
NATIVE_INSTRUMENTS: ClassVar[dict[str, str]] = {
    "BTC": "PI_XBTUSD",
    "ETH": "PI_ETHUSD",
    "SOL": "PI_SOLUSD",
    "MID_TAIL_CONTROL": "PI_DOGEUSD",
}


class KrakenCapabilityProbe(RestCapabilityProbeBase):
    """Kraken Futures v3 REST capability characterization (offline)."""

    provider_id = PROVIDER_ID
    venue_market = "KRAKEN_FUTURES"
    access_mode = AccessMode.PUBLIC_REST
    base_url = "https://futures.kraken.com/derivatives/api/v3"
    probe_version = "kraken-probe-v1"

    native_instruments = NATIVE_INSTRUMENTS

    #: sensor -> result-list key inside the v3 `result` envelope
    result_key_sensors: ClassVar[dict[SensorFamily, str]] = {
        SensorFamily.MECHANICAL_TRADE: "history",
        SensorFamily.MECHANICAL_LIQUIDATION: "history",
        SensorFamily.MECHANICAL_OPEN_INTEREST: "tickers",
        SensorFamily.MECHANICAL_FUNDING: "rates",
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT: "orderBook",
        SensorFamily.MECHANICAL_BASIS: "tickers",
    }

    cursor_paginated_sensors = frozenset(
        {SensorFamily.MECHANICAL_TRADE, SensorFamily.MECHANICAL_LIQUIDATION}
    )
    window_query_sensors = frozenset({SensorFamily.MECHANICAL_FUNDING})
    latest_only_sensors = frozenset(
        {SensorFamily.MECHANICAL_OPEN_INTEREST, SensorFamily.MECHANICAL_BASIS}
    )

    #: sensor -> native unit semantics (characterization knowledge)
    sensor_units: ClassVar[dict[SensorFamily, dict[str, str]]] = {
        SensorFamily.MECHANICAL_TRADE: {
            "price": "USD",
            "size": "contracts (base asset)",
            "side": "buy|sell",
            "type": "fill|liquidation|settlement|block_trade|trade",
            "time": "ms epoch (event time)",
        },
        SensorFamily.MECHANICAL_LIQUIDATION: {
            "type": "'liquidation' marks liquidation trades",
            "price": "USD",
            "size": "contracts (base asset)",
            "time": "ms epoch (event time)",
        },
        SensorFamily.MECHANICAL_OPEN_INTEREST: {
            "openInterest": "contracts",
            "volumeQuote24h": "USD",
            "markPrice": "USD",
        },
        SensorFamily.MECHANICAL_FUNDING: {
            "fundingRate": "decimal fraction per interval",
            "relativeFundingRate": "decimal fraction per interval",
            "time": "ms epoch (effective at)",
        },
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT: {
            "bids/asks": "[[price USD, size contracts, ts ms]]",
            "depth": "levels requested",
        },
        SensorFamily.MECHANICAL_BASIS: {
            "markPrice": "USD (mark)",
            "last": "USD (last trade)",
            "openInterest": "contracts",
        },
    }

    # ------------------------------------------------------------------
    # query construction (Kraken-specific parameter shapes)
    # ------------------------------------------------------------------

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        sensor = request.sensor_family
        params: dict[str, Any] = {"symbol": request.instrument_native}
        if sensor in self.cursor_paginated_sensors:
            params["type"] = "all"
            params["since"] = int(request.requested_start.timestamp() * 1000)
        elif sensor is SensorFamily.MECHANICAL_FUNDING:
            params["from"] = int(request.requested_start.timestamp() * 1000)
            params["to"] = int(request.requested_end.timestamp() * 1000)
        elif sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            params["depth"] = 25
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # error envelopes
    # ------------------------------------------------------------------

    def _error_label_class(self, body: Any) -> ProbeFailureClass | None:
        if not isinstance(body, dict) or not isinstance(body.get("error"), str):
            return None
        error = body["error"].lower()
        if "symbol" in error or "instrument" in error:
            return ProbeFailureClass.F_SYMBOL_NOT_FOUND
        if "rate" in error or "limit" in error:
            return ProbeFailureClass.F_ACCESS_RATE_LIMIT
        if "permission" in error or "auth" in error:
            return ProbeFailureClass.F_ACCESS_AUTH
        if "geo" in error or "region" in error:
            return ProbeFailureClass.F_ACCESS_GEO
        return None

    def _domain_error(self, body: Any) -> ProbeFailureClass | None:
        # v3 domain errors ride on HTTP 200 inside {"error": "..."}
        return self._error_label_class(body)

    def _redacted_error(self, body: Any) -> str | None:
        if isinstance(body, dict) and isinstance(body.get("error"), str):
            return body["error"][:200]
        return None

    # ------------------------------------------------------------------
    # pagination: /history pages back via `since` (ms timestamp)
    # ------------------------------------------------------------------

    def _pagination_state(
        self,
        request: CapabilityProbeRequest,
        rows: list[dict[str, Any]],
        sensor: SensorFamily,
    ) -> tuple[bool, bool | None]:
        if sensor not in self.cursor_paginated_sensors:
            return False, None
        if not rows:
            return True, None
        last_time = rows[-1].get("time")
        since = int(request.requested_start.timestamp() * 1000)
        if isinstance(last_time, (int, float)):
            return True, int(last_time) <= since
        return True, None
