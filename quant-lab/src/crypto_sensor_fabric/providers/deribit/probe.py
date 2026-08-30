"""Deribit capability probe (bloc_02/02 §10 / 04 §6).

Minimal characterization module — NOT a production adapter.  Deribit is the
mechanism microscope, especially BTC/ETH trade-level liquidation anatomy:

- historical trades traverse by timestamp window + count with `has_more`
  (`include_old=true` is REQUIRED for historical depth — probe priorities
  §10.1),
- liquidations appear as trade rows carrying a `liquidation` flag
  ("liquidation" | "taker" | "maker"); this is TRADE_LEVEL anatomy and is
  NEVER numerically merged with interval liquidation totals (02 §10, master
  §13 / T2-SEM-06),
- the asset universe is deliberately narrower (BTC/ETH-heavy); MID_TAIL_CONTROL
  is NOT mapped and that limitation is recorded explicitly (§10.7),
- funding history is hourly with 8h/1h values (§10.5).

All characterization is offline; fetching belongs to SENSOR-B2-I13.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ...contracts.enums import SensorFamily
from ...probes.enums import AccessMode, ProbeFailureClass
from ...probes.models import CapabilityProbeRequest
from ..rest import RestCapabilityProbeBase

PROVIDER_ID = "DERIBIT"

#: Playbook core basket -> native instruments.  Deribit is BTC/ETH-heavy;
#: MID_TAIL_CONTROL is deliberately NOT mapped (02 §10.7 narrower universe).
NATIVE_INSTRUMENTS: ClassVar[dict[str, str]] = {
    "BTC": "BTC-PERPETUAL",
    "ETH": "ETH-PERPETUAL",
    "SOL": "SOL-PERPETUAL",
}

#: v2 JSON-RPC error codes mapped to failure classes (characterization-level;
#: live verification may refine the table).
CODE_FAILURE: dict[int, ProbeFailureClass] = {
    40400: ProbeFailureClass.F_SYMBOL_NOT_FOUND,
    10001: ProbeFailureClass.F_ACCESS_RATE_LIMIT,
    10000: ProbeFailureClass.F_ACCESS_AUTH,
    10002: ProbeFailureClass.F_ACCESS_AUTH,
    -32601: ProbeFailureClass.F_ENDPOINT_REMOVED,
    -32602: ProbeFailureClass.F_CLIENT_4XX,
}


class DeribitCapabilityProbe(RestCapabilityProbeBase):
    """Deribit v2 public JSON-RPC characterization (offline)."""

    provider_id = PROVIDER_ID
    venue_market = "DERIBIT"
    access_mode = AccessMode.PUBLIC_REST
    base_url = "https://www.deribit.com/api/v2/public"
    probe_version = "deribit-probe-v1"

    native_instruments = NATIVE_INSTRUMENTS

    #: rows sit under result.trades / result.data; the book is the result dict
    result_key_sensors: ClassVar[dict[SensorFamily, str]] = {
        SensorFamily.MECHANICAL_TRADE: "trades",
        SensorFamily.MECHANICAL_LIQUIDATION: "trades",
        SensorFamily.MECHANICAL_FUNDING: "data",
    }
    book_in_result_sensors = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

    #: timestamp-window + has_more pagination
    cursor_paginated_sensors = frozenset(
        {SensorFamily.MECHANICAL_TRADE, SensorFamily.MECHANICAL_LIQUIDATION}
    )
    window_query_sensors = frozenset({SensorFamily.MECHANICAL_FUNDING})
    latest_only_sensors = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

    #: page size cap for history traversal
    page_limit = 1000

    #: sensor -> native unit semantics (characterization knowledge)
    sensor_units: ClassVar[dict[SensorFamily, dict[str, str]]] = {
        SensorFamily.MECHANICAL_TRADE: {
            "price": "USD (index/mark referenced)",
            "amount": "base asset",
            "direction": "buy|sell — taker/aggressor side",
            "liquidation": "taker|maker|liquidation flag",
            "timestamp": "ms epoch (event time)",
        },
        SensorFamily.MECHANICAL_LIQUIDATION: {
            "shape": "TRADE_LEVEL anatomy — never numerically merged with interval totals (T2-SEM-06)",
            "liquidation": "'liquidation' marks forced-liquidation trades",
            "direction": "liquidation aggressor side",
            "timestamp": "ms epoch (event time)",
        },
        SensorFamily.MECHANICAL_FUNDING: {
            "funding_rate": "decimal fraction per interval",
            "funding_8h": "decimal fraction (8h series)",
            "funding_1h": "decimal fraction (1h series)",
            "timestamp": "ms epoch (effective at)",
        },
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT: {
            "bids/asks": "[[price USD, amount base, iv]]",
            "depth": "levels requested",
            "timestamp": "ms epoch (snapshot)",
        },
    }

    # ------------------------------------------------------------------
    # query construction — instrument_name + timestamp windows
    # ------------------------------------------------------------------

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        sensor = request.sensor_family
        params: dict[str, Any] = {"instrument_name": request.instrument_native}
        if sensor in self.cursor_paginated_sensors:
            params["start_timestamp"] = int(request.requested_start.timestamp() * 1000)
            params["end_timestamp"] = int(request.requested_end.timestamp() * 1000)
            params["count"] = self.page_limit
            params["include_old"] = True  # required for historical depth
        elif sensor is SensorFamily.MECHANICAL_FUNDING:
            params["start_timestamp"] = int(request.requested_start.timestamp() * 1000)
            params["end_timestamp"] = int(request.requested_end.timestamp() * 1000)
            params["count"] = self.page_limit
        elif sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            params["depth"] = 25
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # error envelopes: JSON-RPC {"error": {"code": <int>, "message": ...}}
    # ------------------------------------------------------------------

    def classify_failure(
        self, http_status: int | None, body: Any
    ) -> ProbeFailureClass:
        code = self._error_label_class(body)
        if code is not None:
            return code
        return super().classify_failure(http_status, body)

    def _error_label_class(self, body: Any) -> ProbeFailureClass | None:
        if not isinstance(body, dict) or not isinstance(body.get("error"), dict):
            return None
        error = body["error"]
        if not isinstance(error.get("code"), int):
            return None
        return CODE_FAILURE.get(error["code"])

    def _domain_error(self, body: Any) -> ProbeFailureClass | None:
        # JSON-RPC errors ride on HTTP 200 inside {"error": {...}}
        return self._error_label_class(body)

    def _redacted_error(self, body: Any) -> str | None:
        if isinstance(body, dict) and isinstance(body.get("error"), dict):
            message = body["error"].get("message")
            if isinstance(message, str):
                return message[:200]
        return None

    # ------------------------------------------------------------------
    # pagination: has_more flag in the result envelope
    # ------------------------------------------------------------------

    def _pagination_state(
        self,
        request: CapabilityProbeRequest,
        rows: list[dict[str, Any]],
        sensor: SensorFamily,
        body: Any = None,
    ) -> tuple[bool, bool | None]:
        if sensor in self.cursor_paginated_sensors:
            has_more = False
            if isinstance(body, dict) and isinstance(body.get("result"), dict):
                has_more = bool(body["result"].get("has_more"))
            return True, not has_more
        if sensor in self.window_query_sensors:
            if not rows:
                return True, True
            return True, len(rows) < self.page_limit
        return False, None
