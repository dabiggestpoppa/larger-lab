"""Gate Futures capability probe (bloc_02/02 §6 / 04 §6).

Minimal characterization module — NOT a production adapter.  Gate is the
primary candidate for interval-level liquidation + OI + taker-flow statistics:

- `/contract_stats` carries long/short liquidation sizes AND OI (contracts +
  USD notional) per interval (probe priorities §6.2-6.4),
- `/trades` rows carry `taker_side` — the aggressor side directly, so no
  isBuyerMaker inversion is needed for Gate,
- `/funding_rates` and `/trades` accept from/to (ms) windows; retention caps
  must be PROBED, not assumed (§6.6),
- `/liquidation_orders` is recent-only,
- `/positions` is auth-gated (characterized as requires_auth; free accounts
  may still qualify under free-only rules if a free key is acceptable).

All characterization logic is offline; fetching belongs to SENSOR-B2-I13.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ...contracts.enums import SensorFamily
from ...probes.enums import AccessMode, ProbeFailureClass
from ...probes.models import CapabilityProbeRequest
from ..rest import RestCapabilityProbeBase

PROVIDER_ID = "GATE_FUTURES"

#: Playbook core basket -> native perpetual contracts (02 §4).
NATIVE_INSTRUMENTS: ClassVar[dict[str, str]] = {
    "BTC": "BTC_USDT",
    "ETH": "ETH_USDT",
    "SOL": "SOL_USDT",
    "MID_TAIL_CONTROL": "DOGE_USDT",
}


class GateCapabilityProbe(RestCapabilityProbeBase):
    """Gate Futures v4 REST capability characterization (offline)."""

    provider_id = PROVIDER_ID
    venue_market = "GATE_FUTURES"
    access_mode = AccessMode.PUBLIC_REST
    base_url = "https://api.gateio.ws/api/v4/futures/usdt"
    probe_version = "gate-probe-v1"

    native_instruments = NATIVE_INSTRUMENTS

    #: sensors whose payload is a bare top-level list.
    #: Aggressor/order-flow probing rides on MECHANICAL_TRADE: the frozen
    #: Bloc 1 SensorFamily has no ORDER_FLOW member — order flow is a T2
    #: derived state family (master §20), so /trades is probed as the raw
    #: trade surface and taker_side aggressor semantics are characterized here
    #: for later T2 derivation (BLOC5_SCHEMA_REFINEMENT_PENDING note).
    top_level_list_sensors = frozenset(
        {
            SensorFamily.MECHANICAL_OPEN_INTEREST,  # /contract_stats
            SensorFamily.MECHANICAL_FUNDING,  # /funding_rates
            SensorFamily.MECHANICAL_TRADE,  # /trades (aggressor flow surface)
            SensorFamily.MECHANICAL_LIQUIDATION,  # /liquidation_orders (recent)
            SensorFamily.MECHANICAL_POSITIONING,  # /positions (auth-gated)
        }
    )
    #: sensors whose payload is a top-level book dict
    top_level_book_sensors = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

    #: from/to (ms) window queries — retention depth must be probed per era.
    #: Liquidations probe /contract_stats interval totals (long/short), the
    #: historical route; the /liquidation_orders stream is recent-only and is
    #: not the research target for interval liquidation totals.
    window_query_sensors = frozenset(
        {
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            SensorFamily.MECHANICAL_FUNDING,
            SensorFamily.MECHANICAL_TRADE,
            SensorFamily.MECHANICAL_LIQUIDATION,
        }
    )
    #: recent/latest-only surfaces (no historical window)
    latest_only_sensors = frozenset({SensorFamily.MECHANICAL_POSITIONING})

    #: sensor -> native unit semantics (characterization knowledge)
    sensor_units: ClassVar[dict[SensorFamily, dict[str, str]]] = {
        SensorFamily.MECHANICAL_LIQUIDATION: {
            "long_liq_size": "contracts (long liquidations)",
            "short_liq_size": "contracts (short liquidations)",
            "long_liq_usd": "USD notional",
            "short_liq_usd": "USD notional",
            "time": "ms epoch (interval)",
        },
        SensorFamily.MECHANICAL_OPEN_INTEREST: {
            "open_interest": "contracts",
            "open_interest_usd": "USD notional",
            "lsr_taker": "long/short ratio (taker)",
            "lsr_account": "long/short ratio (account)",
        },
        SensorFamily.MECHANICAL_FUNDING: {
            "funding_rate": "decimal fraction per interval",
            "funding_time": "ms epoch (effective at)",
            "interval": "seconds between payments",
        },
        SensorFamily.MECHANICAL_TRADE: {
            "taker_side": "buy|sell — aggressor side directly (no maker inversion)",
            "size": "contracts (base asset)",
            "price": "USD",
            "create_time_ms": "ms epoch (event time)",
        },
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT: {
            "bids/asks": "[[price USD, size contracts]]",
        },
        SensorFamily.MECHANICAL_POSITIONING: {
            "size": "contracts",
            "leverage": "multiplier",
            "value": "USD notional",
        },
    }

    # ------------------------------------------------------------------
    # query construction — Gate uses `contract`, not `symbol`
    # ------------------------------------------------------------------

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        sensor = request.sensor_family
        params: dict[str, Any] = {"contract": request.instrument_native}
        if sensor in self.window_query_sensors:
            params["from"] = int(request.requested_start.timestamp() * 1000)
            params["to"] = int(request.requested_end.timestamp() * 1000)
        if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            params["limit"] = 100
        elif sensor not in self.latest_only_sensors:
            params["limit"] = self.page_limit
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # error envelopes: {"label": "...", "message": "..."}
    # ------------------------------------------------------------------

    def classify_failure(
        self, http_status: int | None, body: Any
    ) -> ProbeFailureClass:
        label = self._error_label_class(body)
        if label is not None:
            return label
        return super().classify_failure(http_status, body)

    def _error_label_class(self, body: Any) -> ProbeFailureClass | None:
        if not isinstance(body, dict) or not isinstance(body.get("label"), str):
            return None
        label = body["label"].upper()
        if "RATE_LIMIT" in label or "RATE LIMIT" in label:
            return ProbeFailureClass.F_ACCESS_RATE_LIMIT
        if "UNAUTHORIZED" in label or "INVALID_KEY" in label:
            return ProbeFailureClass.F_ACCESS_AUTH
        if "NOT_FOUND" in label:
            return ProbeFailureClass.F_ENDPOINT_REMOVED
        if "FORBIDDEN" in label:
            # Gate is region-restricted for US users; a forbidden response is
            # geo evidence, never bypassed.
            return ProbeFailureClass.F_ACCESS_GEO
        if "INVALID_PARAM_VALUE" in label:
            message = (body.get("message") or "").lower()
            if "contract" in message or "symbol" in message:
                return ProbeFailureClass.F_SYMBOL_NOT_FOUND
            return ProbeFailureClass.F_CLIENT_4XX
        return None

    def _redacted_error(self, body: Any) -> str | None:
        if isinstance(body, dict):
            label = body.get("label")
            message = body.get("message")
            if isinstance(label, str):
                detail = label
                if isinstance(message, str):
                    detail = f"{label}: {message[:180]}"
                return detail
        return None

    # ------------------------------------------------------------------
    # pagination: from/to window coverage
    # ------------------------------------------------------------------

    def _pagination_state(
        self,
        request: CapabilityProbeRequest,
        rows: list[dict[str, Any]],
        sensor: SensorFamily,
    ) -> tuple[bool, bool | None]:
        if sensor not in self.window_query_sensors:
            return False, None
        if not rows:
            return True, None  # nothing returned; completeness unresolved
        to_ms = int(request.requested_end.timestamp() * 1000)
        last = max(
            (
                row.get("time")
                or row.get("funding_time")
                or row.get("create_time_ms")
                for row in rows
            ),
            default=None,
        )
        if isinstance(last, (int, float)):
            return True, int(last) >= to_ms
        return True, None
