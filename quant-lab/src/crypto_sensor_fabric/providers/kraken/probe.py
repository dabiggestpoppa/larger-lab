"""Kraken Futures capability probe (bloc_02/02 §5 / 04 §6, SENSOR-B2-I12R1).

Minimal characterization module — NOT a production adapter.  It declares the
Kraken-specific facts (endpoints, result keys, native units, instrument map,
query shape, error envelopes, pagination) on top of the shared REST probe
base; all characterization logic is offline.  Fetching belongs to the
explicit live run (SENSOR-B2-I13).

Kraken exposes TWO distinct mechanical surfaces that must be kept separate
(operator repair SENSOR-B2-I12R1):

1. Derivatives v3 trade-level REST (`/derivatives/api/v3`):
   - `/history` — raw trades; liquidations appear as trade rows whose `type`
     field is "liquidation" (trade-level execution/liquidation anatomy).
   - `/orderbook` — L2 book snapshot.
   These carry `since` (ms) cursors / current snapshots only.

2. Market Analytics (`/api/charts/v1/analytics/{symbol}/{analytics_type}`):
   precomputed, time-bucketed historical metrics.  This is the selected
   HISTORICAL mechanical source for bucketed OI / funding / basis /
   positioning / book metrics.  Query contract (from first-party docs):
       since   = epoch seconds (required)
       to      = epoch seconds (default now)
       interval= one supported resolution in seconds
                 (60, 300, 900, 1800, 3600, 14400, 43200, 86400, 604800)
       envelope: {"result": {"timestamp": [...], "data": [...], "more": bool},
                   "errors": [...]}

Historical OI therefore targets `.../analytics/{symbol}/open-interest`,
NEVER the current-only /tickers surface.  Precomputed Kraken analytics are
NEVER assumed EXACT_EQUIVALENT to Fabric-reconstructed metrics unless later
live evidence earns that distinction.
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

#: Market Analytics base (source: docs.kraken.com/api-reference/analytics/market-analytics,
#: observed 2026-08-30).
ANALYTICS_BASE_URL = "https://futures.kraken.com/api/charts/v1/analytics"

#: Default bucketing resolution used for historical probe windows (seconds).
#: One of the supported analytics interval values.
ANALYTICS_INTERVAL_SECONDS = 3600

#: Sensor -> analytics_type for sensors probed via the bucketed Market
#: Analytics surface.  These are the primary HISTORICAL probe routes for the
#: bucketed mechanical sensors.
ANALYTICS_SENSORS: dict[SensorFamily, str] = {
    SensorFamily.MECHANICAL_OPEN_INTEREST: "open-interest",
    SensorFamily.MECHANICAL_FUNDING: "funding",
    SensorFamily.MECHANICAL_BASIS: "future-basis",
    SensorFamily.MECHANICAL_POSITIONING: "long-short-ratio",
    SensorFamily.MECHANICAL_BOOK_METRIC: "orderbook",
}

#: Candidate analytics types per sensor that are NOT the default probe route
#: but map to the same sensor family when characterized (provider-native
#: methodology preserved).  Aggressor/trade-flow analytics map to the TRADE
#: sensor with semantic-equivalence retained (never assumed EXACT_EQUIVALENT).
ANALYTICS_CANDIDATES: dict[SensorFamily, tuple[str, ...]] = {
    SensorFamily.MECHANICAL_LIQUIDATION: ("liquidation-volume",),
    SensorFamily.MECHANICAL_POSITIONING: ("top-traders", "long-short-info"),
    SensorFamily.MECHANICAL_BOOK_METRIC: ("spreads", "liquidity", "slippage"),
    SensorFamily.MECHANICAL_TRADE: (
        "aggressor-differential",
        "cvd",
        "trade-volume",
        "trade-count",
    ),
    SensorFamily.MECHANICAL_OPEN_INTEREST: (),
    SensorFamily.MECHANICAL_FUNDING: (),
    SensorFamily.MECHANICAL_BASIS: (),
}

#: Reverse mapping: analytics_type -> sensor family (documentation/verification).
ALL_ANALYTICS_TYPES: tuple[str, ...] = (
    "open-interest",
    "aggressor-differential",
    "trade-volume",
    "trade-count",
    "liquidation-volume",
    "rolling-volatility",
    "long-short-ratio",
    "long-short-info",
    "cvd",
    "top-traders",
    "orderbook",
    "spreads",
    "liquidity",
    "slippage",
    "future-basis",
    "funding",
)

#: Default analytics_type mapped per supported analytics member (which member a
#: given analytics_type belongs to).  Used to route characterization.
ANALYTICS_TYPE_TO_SENSOR: dict[str, SensorFamily] = {
    "open-interest": SensorFamily.MECHANICAL_OPEN_INTEREST,
    "funding": SensorFamily.MECHANICAL_FUNDING,
    "future-basis": SensorFamily.MECHANICAL_BASIS,
    "long-short-ratio": SensorFamily.MECHANICAL_POSITIONING,
    "top-traders": SensorFamily.MECHANICAL_POSITIONING,
    "long-short-info": SensorFamily.MECHANICAL_POSITIONING,
    "liquidation-volume": SensorFamily.MECHANICAL_LIQUIDATION,
    "orderbook": SensorFamily.MECHANICAL_BOOK_METRIC,
    "spreads": SensorFamily.MECHANICAL_BOOK_METRIC,
    "liquidity": SensorFamily.MECHANICAL_BOOK_METRIC,
    "slippage": SensorFamily.MECHANICAL_BOOK_METRIC,
}


#: bucket period (per window) the probe asks analytics to segment into.
def analytics_type_for_sensor(sensor: SensorFamily) -> str:
    """Return the primary Market Analytics type mapped to a sensor family."""
    if sensor in ANALYTICS_SENSORS:
        return ANALYTICS_SENSORS[sensor]
    raise ValueError(f"{sensor.value} has no primary Market Analytics type")


def supported_analytics_types() -> tuple[str, ...]:
    return ALL_ANALYTICS_TYPES


class KrakenCapabilityProbe(RestCapabilityProbeBase):
    """Kraken Futures REST + Market Analytics characterization (offline)."""

    provider_id = PROVIDER_ID
    venue_market = "KRAKEN_FUTURES"
    access_mode = AccessMode.PUBLIC_REST
    base_url = "https://futures.kraken.com/derivatives/api/v3"
    probe_version = "kraken-probe-v2"

    native_instruments = NATIVE_INSTRUMENTS

    #: sensor -> result-list key inside the v3 `result` envelope
    # (trade-level surfaces only; analytics sensors are routed separately)
    result_key_sensors: ClassVar[dict[SensorFamily, str]] = {
        SensorFamily.MECHANICAL_TRADE: "history",
        SensorFamily.MECHANICAL_LIQUIDATION: "history",
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT: "orderBook",
    }

    cursor_paginated_sensors = frozenset(
        {SensorFamily.MECHANICAL_TRADE, SensorFamily.MECHANICAL_LIQUIDATION}
    )
    window_query_sensors = frozenset()  # analytics sensors handle their own window
    latest_only_sensors = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

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
            "source": (
                "TRADE_LEVEL anatomy via /history `type=liquidation` OR "
                "bucketed analytics `liquidation-volume` — never numerically "
                "merged across shapes (T2-SEM-06)"
            ),
            "type": "'liquidation' marks liquidation trades on /history",
            "price": "USD",
            "size": "contracts (base asset)",
            "time": "ms epoch (event time)",
        },
        SensorFamily.MECHANICAL_OPEN_INTEREST: {
            "source": "precomputed Market Analytics `open-interest` (bucketed)",
            "openInterest": "provider-precomputed open interest (bucketed)",
            "since": "epoch seconds",
            "to": "epoch seconds",
            "interval": "one supported resolution in seconds",
            "exact_equivalent": (
                "not assumed — precomputed vs Fabric-derived OI requires later "
                "evidence"
            ),
        },
        SensorFamily.MECHANICAL_FUNDING: {
            "source": "precomputed Market Analytics `funding` (bucketed)",
            "fundingRate": "provider-precomputed funding rate (bucketed)",
            "since": "epoch seconds",
            "to": "epoch seconds",
            "interval": "one supported resolution in seconds",
        },
        SensorFamily.MECHANICAL_BASIS: {
            "source": "precomputed Market Analytics `future-basis` (bucketed)",
            "since/to": "epoch seconds",
        },
        SensorFamily.MECHANICAL_POSITIONING: {
            "source": (
                "precomputed Market Analytics `long-short-ratio` / `top-traders` / "
                "`long-short-info` (bucketed)"
            ),
            "population": "TOP_TRADER_ACCOUNT_RATIO / GLOBAL_LONG_SHORT_RATIO — "
            "population-neutral, never equated across endpoints",
        },
        SensorFamily.MECHANICAL_BOOK_METRIC: {
            "source": (
                "precomputed Market Analytics `orderbook` / `spreads` / "
                "`liquidity` / `slippage` (bucketed) — precomputed, not a raw L2"
            ),
        },
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT: {
            "bids/asks": "[[price USD, size contracts, ts ms]]",
            "depth": "levels requested",
        },
    }

    # ------------------------------------------------------------------
    # query construction
    #
    # Trade-level sensors use v3 `/derivatives`; bucketed mechanical sensors
    # use Market Analytics with epoch-SECONDS since/to and an explicit interval.
    # ------------------------------------------------------------------

    def _analytics_url(self, sensor: SensorFamily, symbol: str) -> str:
        analytics_type = ANALYTICS_SENSORS[sensor]
        return f"{ANALYTICS_BASE_URL}/{symbol}/{analytics_type}"

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        sensor = request.sensor_family
        if sensor in ANALYTICS_SENSORS:
            # Market Analytics contract: since/to in SECONDS, interval explicit.
            return {
                "url": self._analytics_url(sensor, request.instrument_native),
                "params": {
                    "since": int(request.requested_start.timestamp()),
                    "to": int(request.requested_end.timestamp()),
                    "interval": ANALYTICS_INTERVAL_SECONDS,
                },
            }
        params: dict[str, Any] = {"symbol": request.instrument_native}
        if sensor in self.cursor_paginated_sensors:
            params["type"] = "all"
            params["since"] = int(request.requested_start.timestamp() * 1000)
        elif sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            params["depth"] = 25
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # payload extraction — analytics envelope {} vs v3 result envelope
    # ------------------------------------------------------------------

    def _extract_rows(self, body: Any, sensor: SensorFamily) -> list[dict[str, Any]]:
        if sensor in ANALYTICS_SENSORS:
            return self._extract_analytics_rows(body, sensor)
        return super()._extract_rows(body, sensor)

    def _extract_analytics_rows(
        self, body: Any, sensor: SensorFamily
    ) -> list[dict[str, Any]]:
        # {"result": {"timestamp": [...], "data": [...], "more": bool}, "errors": [...]}
        #
        # OBSERVED (SENSOR-B2-I13): `data` is a per-type list for some analytics
        # (e.g. open-interest) but a DICT of per-metric lists parallel to
        # `timestamp` for others (e.g. funding -> {"rate": [...],
        # "relativeRate": [...]}).  Both shapes are flattened here.  `timestamp`
        # is epoch seconds for most analytics types and epoch ms for funding.
        if not isinstance(body, dict) or not isinstance(body.get("result"), dict):
            raise ValueError(  # noqa: TRY004 — type guard feeds F_SCHEMA_CHANGED
                f"{self.provider_id} analytics payload missing 'result'"
            )
        result = body["result"]
        data = result.get("data")
        timestamps = result.get("timestamp") or []
        rows: list[dict[str, Any]] = []
        if isinstance(data, list):
            for i, datum in enumerate(data):
                row: dict[str, Any] = (
                    dict(datum) if isinstance(datum, dict) else {"value": datum}
                )
                if i < len(timestamps):
                    row["timestamp"] = timestamps[i]
                rows.append(row)
            return rows
        if isinstance(data, dict):
            # metric -> list of values parallel to `timestamp`
            metrics = list(data)
            for i in range(len(timestamps)):
                row = {"timestamp": timestamps[i]}
                for metric in metrics:
                    values = data[metric]
                    if isinstance(values, list) and i < len(values):
                        row[metric] = values[i]
                rows.append(row)
            return rows
        raise ValueError(  # noqa: TRY004 — type guard feeds F_SCHEMA_CHANGED
            f"{self.provider_id} analytics result 'data' has unexpected shape"
        )

    # ------------------------------------------------------------------
    # error envelopes
    # ------------------------------------------------------------------

    def _error_label_class(self, body: Any) -> ProbeFailureClass | None:
        if isinstance(body, dict) and isinstance(body.get("errors"), list):
            for err in body["errors"]:
                if isinstance(err, dict):
                    msg = str(err.get("msg", ""))
                    cls = str(err.get("error_class", ""))
                    combined = f"{msg} {cls}".lower()
                    if "symbol" in combined or "instrument" in combined:
                        return ProbeFailureClass.F_SYMBOL_NOT_FOUND
                    if "rate" in combined or "limit" in combined:
                        return ProbeFailureClass.F_ACCESS_RATE_LIMIT
                    if (
                        "permission" in combined
                        or "auth" in combined
                        or "unauthorized" in combined
                    ):
                        return ProbeFailureClass.F_ACCESS_AUTH
                    if "geo" in combined or "region" in combined:
                        return ProbeFailureClass.F_ACCESS_GEO
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

    def _redacted_error(self, body: Any) -> str | None:
        if isinstance(body, dict) and isinstance(body.get("errors"), list):
            parts = []
            for err in body["errors"]:
                if isinstance(err, dict) and isinstance(err.get("msg"), str):
                    parts.append(err["msg"][:200])
            if parts:
                return " | ".join(parts)
        if isinstance(body, dict) and isinstance(body.get("error"), str):
            return body["error"][:200]
        return None

    # ------------------------------------------------------------------
    # pagination: /history pages back via `since` (ms); analytics uses `more`
    # ------------------------------------------------------------------

    def _pagination_state(
        self,
        request: CapabilityProbeRequest,
        rows: list[dict[str, Any]],
        sensor: SensorFamily,
        body: Any = None,
    ) -> tuple[bool, bool | None]:
        if sensor in ANALYTICS_SENSORS:
            more = False
            if isinstance(body, dict) and isinstance(body.get("result"), dict):
                more = bool(body["result"].get("more"))
            return True, not more
        if sensor not in self.cursor_paginated_sensors:
            return False, None
        if not rows:
            return True, None
        last_time = rows[-1].get("time")
        since = int(request.requested_start.timestamp() * 1000)
        if isinstance(last_time, (int, float)):
            return True, int(last_time) <= since
        return True, None