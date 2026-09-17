"""Gate Futures capability probe (bloc_02/02 §6 / 04 §6, SENSOR-B2-I12R1).

Minimal characterization module — NOT a production adapter.  Gate is the
primary candidate for interval-level liquidation + OI + taker-flow statistics:

- `/contract_stats` carries long/short liquidation sizes AND OI (contracts +
  USD notional) AND market-wide positioning fields (lsr_taker, lsr_account,
  top_lsr_*, top_long_size, top_short_size, long_users, short_users) per
  interval,
- `/trades` rows carry `taker_side` — the aggressor side directly, so no
  isBuyerMaker inversion is needed for Gate,
- `/funding_rates` and `/trades` accept from/to (ms) windows; retention caps
  must be PROBED, not assumed (§6.6).

WARNING (operator repair SENSOR-B2-I12R1): market-wide positioning MUST come
from the PUBLIC `/contract_stats` surface.  User `/positions` is
account-authenticated PRIVATE_ACCOUNT_DATA and is OUT_OF_SCOPE for the
required Sensor Fabric runtime — the Sensor Fabric never requires exchange
account credentials for market positioning.

contract_stats query contract (from first-party docs, observed 2026-08-30):
    GET /api/v4/futures/{settle}/contract_stats
    contract  = futures contract (required)
    from      = Unix SECONDS (NOT milliseconds)
    interval  = seconds between interval points (e.g. 5m=300, 1h=3600, 1d=86400)
    limit     = max records per response
    `to` is NOT invented — historical traversal is characterized via the
    provider's actual from/interval/limit behavior.

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

#: Settlement suffix for the USD-settled futures family probed.
GATE_SETTLE = "usdt"

#: Default interval bucket used for /contract_stats probe windows.
#: OBSERVED LIVE (SENSOR-B2-I13): interval is a STRING bucket ("5m"/"1h"/
#: "1d", ...), NOT epoch seconds — passing seconds returns HTTP 400
#: INVALID_PARAM_VALUE.  `from` remains Unix SECONDS.
GATE_CONTRACT_STATS_INTERVAL = "1h"


class GateCapabilityProbe(RestCapabilityProbeBase):
    """Gate Futures v4 REST capability characterization (offline)."""

    provider_id = PROVIDER_ID
    venue_market = "GATE_FUTURES"
    access_mode = AccessMode.PUBLIC_REST
    base_url = "https://api.gateio.ws/api/v4/futures/usdt"
    probe_version = "gate-probe-v2"

    native_instruments = NATIVE_INSTRUMENTS

    #: sensors whose payload is a bare top-level list.
    top_level_list_sensors = frozenset(
        {
            SensorFamily.MECHANICAL_OPEN_INTEREST,  # /contract_stats
            SensorFamily.MECHANICAL_LIQUIDATION,  # /contract_stats
            SensorFamily.MECHANICAL_POSITIONING,  # /contract_stats (public)
            SensorFamily.MECHANICAL_FUNDING,  # /funding_rates
            SensorFamily.MECHANICAL_TRADE,  # /trades (aggressor flow surface)
        }
    )
    #: sensors whose payload is a top-level book dict
    top_level_book_sensors = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

    #: sensors on /contract_stats with epoch-SECOND `from` + `interval` + `limit`
    # (no invented `to`).  Positioning rides here via the PUBLIC statistics.
    contract_stats_sensors = frozenset(
        {
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            SensorFamily.MECHANICAL_LIQUIDATION,
            SensorFamily.MECHANICAL_POSITIONING,
        }
    )
    #: from/to (ms) window queries — retention depth must be probed per era.
    # I13R1: funding uses the SINGLE-contract GET /funding_rate?contract=...
    # (no auth) — NOT the plural batch POST /funding_rates, which was probed
    # under a GET-style model and returned INVALID_CREDENTIALS (that attempt
    # was a REQUEST_CONTRACT_INVALID, not a provider auth failure).  The
    # plural batch route is modeled separately (batch_funding_rates_url).
    window_query_sensors = frozenset(
        {
            SensorFamily.MECHANICAL_FUNDING,  # GET /funding_rate (single contract)
            SensorFamily.MECHANICAL_TRADE,  # /trades
        }
    )

    #: sensor -> native unit semantics (characterization knowledge)
    sensor_units: ClassVar[dict[SensorFamily, dict[str, str]]] = {
        SensorFamily.MECHANICAL_LIQUIDATION: {
            "source": "interval-long/short liquidation sizes + USD notional via /contract_stats",
            "long_liq_size": "contracts (long liquidations)",
            "short_liq_size": "contracts (short liquidations)",
            "long_liq_usd": "USD notional",
            "short_liq_usd": "USD notional",
            "time": "epoch seconds (interval; I05-era sample was a synthetic ms fixture — prior characterization error, see BLOC_03_I10R2)",
        },
        SensorFamily.MECHANICAL_OPEN_INTEREST: {
            "source": "interval OI (contracts + USD notional) via /contract_stats",
            "open_interest": "contracts",
            "open_interest_usd": "USD notional",
            "lsr_taker": "long/short ratio (taker)",
            "lsr_account": "long/short ratio (account)",
        },
        SensorFamily.MECHANICAL_POSITIONING: {
            "source": "PUBLIC market-wide /contract_stats (never user /positions)",
            "lsr_taker": "long/short ratio (taker)",
            "lsr_account": "long/short ratio (account)",
            "top_lsr_account": "top-account long/short ratio",
            "top_lsr_size": "top long/short size",
            "top_long_size": "top long size",
            "top_short_size": "top short size",
            "long_users": "long user count",
            "short_users": "short user count",
            "private_positions": (
                "OUT_OF_SCOPE — /positions is PRIVATE_ACCOUNT_DATA; credentials "
                "are never required for market positioning"
            ),
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
    }

    # ------------------------------------------------------------------
    # query construction — Gate uses `contract` (not `symbol`)
    # ------------------------------------------------------------------

    def contract_stats_url(self) -> str:
        return f"https://api.gateio.ws/api/v4/futures/{GATE_SETTLE}/contract_stats"

    def funding_rate_url(self) -> str:
        """Single-contract historical funding GET route (I13R1).

        OBSERVED LIVE (I13R1): /funding_rate?contract=...&from=&to= uses Unix
        SECONDS for from/to (like contract_stats, NOT ms) and rows are
        {"r": rate, "t": epoch seconds}.  Retention is bounded ("from time
        exceeds 180-day limit" for older eras) — same rolling boundary as
        contract_stats.
        """
        return f"https://api.gateio.ws/api/v4/futures/{GATE_SETTLE}/funding_rate"

    def batch_funding_rates_url(self) -> str:
        """Plural batch POST /funding_rates — modeled separately from the GET."""
        return f"https://api.gateio.ws/api/v4/futures/{GATE_SETTLE}/funding_rates"

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        sensor = request.sensor_family
        params: dict[str, Any] = {"contract": request.instrument_native}
        if sensor in self.contract_stats_sensors:
            # epoch SECONDS `from`, STRING interval bucket, limit; no `to`.
            params["from"] = int(request.requested_start.timestamp())
            params["interval"] = GATE_CONTRACT_STATS_INTERVAL
            params["limit"] = self.page_limit
        elif sensor in self.window_query_sensors:
            # I13R1 live-observed: BOTH funding_rate and /trades from/to are
            # Unix SECONDS (ms windows return empty — the old ms probe was a
            # REQUEST_CONTRACT_INVALID, not a valid empty).  First-party SDK
            # docs confirm "Specify starting time in Unix seconds".
            params["from"] = int(request.requested_start.timestamp())
            params["to"] = int(request.requested_end.timestamp())
        if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            params["limit"] = 100
        if sensor is SensorFamily.MECHANICAL_FUNDING:
            # single-contract GET /funding_rate?contract=...&from=&to= (seconds)
            return {"url": self.funding_rate_url(), "params": params}
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # error envelopes: {\"label\": \"...\", \"message\": \"...\"}
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
    # funding rows carry {"r": rate, "t": epoch seconds} — expose `t` as a
    # timestamp field so PIT/characterization see it (I13R1 live-observed).
    # ------------------------------------------------------------------

    def extract_timestamp_fields(self, body: Any) -> list[str]:
        fields = super().extract_timestamp_fields(body)
        if isinstance(body, list) and any(
            isinstance(row, dict) and "t" in row and "r" in row for row in body[:50]
        ):
            if "t" not in fields:
                fields.append("t")
        return fields

    # ------------------------------------------------------------------
    # pagination: window coverage (seconds on contract_stats, ms elsewhere)
    # ------------------------------------------------------------------

    def _pagination_state(
        self,
        request: CapabilityProbeRequest,
        rows: list[dict[str, Any]],
        sensor: SensorFamily,
        body: Any = None,
    ) -> tuple[bool, bool | None]:
        if sensor not in self.contract_stats_sensors and sensor not in self.window_query_sensors:
            return False, None
        if not rows:
            return True, None  # nothing returned; completeness unresolved
        # funding_rate rows carry {"t": epoch SECONDS} (I13R1 live-observed);
        # /trades rows carry create_time_ms; contract_stats rows carry epoch
        # SECONDS `time` (current contract — I10R1 live-verified; the I05-era
        # sample was a synthetic ms fixture — prior characterization error,
        # NOT provider drift and NOT magnitude-rescued).
        if sensor is SensorFamily.MECHANICAL_FUNDING:
            last = max(
                (row.get("t") for row in rows if isinstance(row.get("t"), (int, float))),
                default=None,
            )
            end = int(request.requested_end.timestamp())
            return True, (last is not None and int(last) >= end)
        if sensor in self.contract_stats_sensors:
            # Request `from` is seconds; rows carry `time` in epoch seconds
            # (I10R1 live adjudication).  There is no `to` param — completeness
            # is bounded by from+interval+limit coverage, so signal coverage
            # against the requested window end in seconds.
            end = int(request.requested_end.timestamp())
            key = "time"
        else:
            # /trades: request from/to are Unix SECONDS (I13R1 live-observed),
            # but ROW timestamps are create_time_ms (epoch ms).  Compare
            # like-for-like: ms rows against the requested end in ms.
            end = int(request.requested_end.timestamp() * 1000)
            key = "time"
        last = max(
            (
                row.get(key)
                or row.get("funding_time")
                or row.get("create_time_ms")
                for row in rows
                if isinstance(row, dict)
            ),
            default=None,
        )
        if isinstance(last, (int, float)):
            return True, int(last) >= end
        return True, None