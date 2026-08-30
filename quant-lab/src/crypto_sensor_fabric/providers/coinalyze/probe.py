"""Coinalyze capability probe (bloc_02/02 §11 / 04 §6).

Minimal characterization module — NOT a production adapter.  Coinalyze is a
THIRD_PARTY_AGGREGATOR (registry evidence_class): it never counts as
independent venue truth alongside the venues it aggregates (T2-COV-05, master
§14).  Characterization records:

- free API key requirement and rate-limit evidence (probe priorities §11.1),
- daily history depth and intraday retention at several intervals (§11.2-11.4),
- venue aggregation semantics: symbols carry venue suffixes
  (BTCUSDT_PERP.BINANCE) so attribution is preserved at symbol level (§11.6),
- per-field equivalence: aggregated methodology is opaque; fields are
  corroboration-classified pending live evidence (§11.7).

The free tier's limited quota may make full historical backfill infeasible —
that is a measured limitation, not a silent workaround.  The live executor
(SENSOR-B2-I13) injects the free key from the environment; it is never part
of a probe request or evidence.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ...contracts.enums import SensorFamily
from ...probes.enums import AccessMode, ProbeFailureClass
from ...probes.models import CapabilityProbeRequest
from ..rest import RestCapabilityProbeBase

PROVIDER_ID = "COINALYZE"

#: Playbook core basket -> aggregated series ids (venue-attributed).
#: Default series reference the BINANCE venue; probe-target config may choose
#: other venue series (attribution preserved per symbol).
NATIVE_INSTRUMENTS: ClassVar[dict[str, str]] = {
    "BTC": "BTCUSDT_PERP.BINANCE",
    "ETH": "ETHUSDT_PERP.BINANCE",
    "SOL": "SOLUSDT_PERP.BINANCE",
    "MID_TAIL_CONTROL": "DOGEUSDT_PERP.BINANCE",
}

#: History intervals; intraday retention is documented as shallow and must be
#: probed per interval (free tier).
HISTORY_INTERVALS: tuple[str, ...] = ("1h", "1d")


class CoinalyzeCapabilityProbe(RestCapabilityProbeBase):
    """Coinalyze v1 free-key aggregator characterization (offline)."""

    provider_id = PROVIDER_ID
    venue_market = "COINALYZE"
    access_mode = AccessMode.FREE_API_KEY
    base_url = "https://api.coinalyze.net/v1"
    probe_version = "coinalyze-probe-v1"

    native_instruments = NATIVE_INSTRUMENTS

    #: sensors characterized through the venue-attributed history endpoints
    window_query_sensors = frozenset(
        {
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            SensorFamily.MECHANICAL_LIQUIDATION,
            SensorFamily.MECHANICAL_FUNDING,
            SensorFamily.MECHANICAL_POSITIONING,
        }
    )

    #: sensor -> native unit semantics (characterization knowledge)
    sensor_units: ClassVar[dict[SensorFamily, dict[str, str]]] = {
        SensorFamily.MECHANICAL_OPEN_INTEREST: {
            "value": "aggregated USD open interest",
            "time": "ms epoch (interval)",
            "symbols": "venue-attributed (e.g. BTCUSDT_PERP.BINANCE)",
            "methodology": "vendor-aggregated, opaque — corroboration pending live evidence",
        },
        SensorFamily.MECHANICAL_LIQUIDATION: {
            "value": "aggregated USD liquidations",
            "time": "ms epoch (interval)",
            "symbols": "venue-attributed",
            "methodology": "vendor-aggregated, opaque — corroboration pending live evidence",
        },
        SensorFamily.MECHANICAL_FUNDING: {
            "value": "funding rate (decimal fraction)",
            "time": "ms epoch (interval)",
            "symbols": "venue-attributed",
            "methodology": "vendor-aggregated, opaque",
        },
        SensorFamily.MECHANICAL_POSITIONING: {
            "value": "long/short ratio",
            "time": "ms epoch (interval)",
            "symbols": "venue-attributed",
            "methodology": "vendor-aggregated, opaque",
        },
    }

    # ------------------------------------------------------------------
    # query construction — symbols + interval + from/to (seconds)
    # ------------------------------------------------------------------

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        sensor = request.sensor_family
        interval = "1h" if sensor not in self.latest_only_sensors else "1d"
        params: dict[str, Any] = {
            "symbols": request.instrument_native,
            "interval": interval,
            "from": int(request.requested_start.timestamp()),
            "to": int(request.requested_end.timestamp()),
        }
        # NOTE: the free `apikey` is injected by the live executor from the
        # environment; it is never embedded here and never enters evidence.
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # payload rows: [{symbol, data: [{time, value}]}]
    # ------------------------------------------------------------------

    def _extract_rows(self, body: Any, sensor: SensorFamily) -> list[dict[str, Any]]:
        if isinstance(body, list) and body and isinstance(body[0], dict):
            data = body[0].get("data")
            if isinstance(data, list):
                return [row for row in data if isinstance(row, dict)]
        raise ValueError("coinalyze payload is not a [{symbol, data:[...]}] envelope")

    # ------------------------------------------------------------------
    # error envelopes: {"detail": "..."} with HTTP 401/429/403
    # ------------------------------------------------------------------

    def classify_failure(
        self, http_status: int | None, body: Any
    ) -> ProbeFailureClass:
        detail = self._error_label_class(body)
        if detail is not None:
            return detail
        return super().classify_failure(http_status, body)

    def _error_label_class(self, body: Any) -> ProbeFailureClass | None:
        if not isinstance(body, dict) or not isinstance(body.get("detail"), str):
            return None
        detail = body["detail"].lower()
        if "key" in detail or "auth" in detail or "permission" in detail:
            return ProbeFailureClass.F_ACCESS_AUTH
        if "limit" in detail or "quota" in detail or "frequent" in detail:
            return ProbeFailureClass.F_ACCESS_RATE_LIMIT
        if "symbol" in detail or "instrument" in detail:
            return ProbeFailureClass.F_SYMBOL_NOT_FOUND
        return None

    def _redacted_error(self, body: Any) -> str | None:
        if isinstance(body, dict) and isinstance(body.get("detail"), str):
            return body["detail"][:200]
        return None

    # ------------------------------------------------------------------
    # pagination: window coverage by first/last row time
    # ------------------------------------------------------------------

    def _pagination_state(
        self,
        request: CapabilityProbeRequest,
        rows: list[dict[str, Any]],
        sensor: SensorFamily,
        body: Any = None,
    ) -> tuple[bool, bool | None]:
        if sensor not in self.window_query_sensors:
            return False, None
        if not rows:
            return True, None
        to_sec = int(request.requested_end.timestamp())
        last = max((row.get("time") for row in rows), default=None)
        if isinstance(last, (int, float)):
            # coinalyze `time` is ms in responses but from/to are seconds
            last_sec = last / 1000.0 if last > 10_000_000_000 else last
            return True, int(last_sec) >= to_sec
        return True, None
