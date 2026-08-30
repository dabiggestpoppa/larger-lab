"""Binance USD-M Futures capability probe (bloc_02/02 §7 / 04 §6).

Minimal characterization module — NOT a production adapter.  Two surfaces:

- PUBLIC REST (`fapi.binance.com/fapi/v1`): aggTrades (aggressor flow), funding
  rate history, openInterestHist, current /depth.
- PUBLIC ARCHIVE (`data.binance.vision`): deterministic daily files
  {SYMBOL}-{kind}-{YYYY-MM-DD}.zip with .CHECKSUM siblings for trades /
  aggTrades / bookDepth / metrics / fundingRate.

Frozen Binance aggressor contract (operator repair SENSOR-B1-R01, still
PROVISIONAL until provider fixture verification):

    isBuyerMaker = true  -> SELL aggressor (buyer is maker; seller is taker)
    isBuyerMaker = false -> BUY aggressor (buyer is taker)

Historical liquidation is NOT assumed: there is no public historical
liquidation endpoint, so it stays UNVERIFIED_OR_UNAVAILABLE (02 §7 probe
priority §8, bloc_01/02 §13).  Archive holes must be detected per symbol/kind,
never assumed continuous.  All characterization is offline; fetching belongs
to SENSOR-B2-I13.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ...contracts.enums import AggressorSide, SensorFamily
from ...probes.enums import AccessMode, ProbeFailureClass, ResponseStatusClass
from ...probes.models import CapabilityProbeAttempt, CapabilityProbeRequest
from ..base import load_endpoint_registry
from ..rest import RestCapabilityProbeBase

PROVIDER_ID = "BINANCE_USDM"

#: Playbook core basket -> native perpetual symbols (02 §4).
NATIVE_INSTRUMENTS: ClassVar[dict[str, str]] = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "MID_TAIL_CONTROL": "DOGEUSDT",
}

#: Public archive daily base (data.binance.vision).
ARCHIVE_BASE_URL = "https://data.binance.vision/data/futures/um/daily"

#: Daily archive file kinds characterized by the probe.
ARCHIVE_KINDS: tuple[str, ...] = (
    "trades",
    "aggTrades",
    "bookDepth",
    "metrics",
    "fundingRate",
)


def aggressor_side_from_is_buyer_maker(is_buyer_maker: bool) -> AggressorSide:
    """Frozen Binance aggressor contract (SENSOR-B1-R01).

    isBuyerMaker=true  -> buyer is maker -> seller is taker/aggressor -> SELL
    isBuyerMaker=false -> buyer is taker/aggressor                    -> BUY

    The transformation implementation belongs to Bloc 5 normalization; this
    function pins the PROVISIONAL direction so an inversion can never be
    re-introduced silently.  Provider fixture verification (Bloc 2 I13) must
    confirm before the mapping is trusted.
    """
    return AggressorSide.SELL if is_buyer_maker else AggressorSide.BUY


class BinanceCapabilityProbe(RestCapabilityProbeBase):
    """Binance USD-M Futures REST + archive characterization (offline)."""

    provider_id = PROVIDER_ID
    venue_market = "BINANCE_USDM"
    access_mode = AccessMode.PUBLIC_REST
    base_url = "https://fapi.binance.com/fapi/v1"
    probe_version = "binance-probe-v1"

    native_instruments = NATIVE_INSTRUMENTS

    #: REST sensors whose payload is a bare top-level list
    top_level_list_sensors = frozenset(
        {
            SensorFamily.MECHANICAL_TRADE,  # /aggTrades
            SensorFamily.MECHANICAL_FUNDING,  # /fundingRate
            SensorFamily.MECHANICAL_OPEN_INTEREST,  # /futures/data/openInterestHist
        }
    )
    #: REST sensors whose payload is a top-level book dict
    top_level_book_sensors = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

    #: REST sensors queried with startTime/endTime (ms) windows
    window_query_sensors = frozenset(
        {
            SensorFamily.MECHANICAL_TRADE,
            SensorFamily.MECHANICAL_FUNDING,
            SensorFamily.MECHANICAL_OPEN_INTEREST,
        }
    )

    #: sensor -> native unit semantics (characterization knowledge)
    sensor_units: ClassVar[dict[SensorFamily, dict[str, str]]] = {
        SensorFamily.MECHANICAL_TRADE: {
            "price": "USD",
            "qty": "base asset",
            "quoteQty": "USD",
            "isBuyerMaker": (
                "true -> SELL aggressor; false -> BUY aggressor "
                "(R01 PROVISIONAL contract)"
            ),
            "time": "ms epoch (event time)",
        },
        SensorFamily.MECHANICAL_FUNDING: {
            "fundingRate": "decimal fraction per 8h interval",
            "fundingTime": "ms epoch (effective at)",
            "markPrice": "USD",
        },
        SensorFamily.MECHANICAL_OPEN_INTEREST: {
            "sumOpenInterest": "contracts",
            "sumOpenInterestValue": "USD notional",
            "timestamp": "ms epoch (period start)",
            "period": "5m|15m|30m|1h|4h|1d",
        },
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT: {
            "bids/asks": "[[price USD, qty base asset]]",
            "lastUpdateId": "book epoch id",
        },
    }

    def __init__(self, endpoints: dict[str, Any] | None = None) -> None:
        super().__init__(endpoints)
        registry = endpoints if endpoints is not None else load_endpoint_registry()
        entry = registry.get(PROVIDER_ID, {})
        self.archive_base_url: str = entry.get("archive_base_url", ARCHIVE_BASE_URL)

    # ------------------------------------------------------------------
    # query construction — Binance uses uppercase `symbol` + startTime/endTime
    # ------------------------------------------------------------------

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        sensor = request.sensor_family
        params: dict[str, Any] = {"symbol": request.instrument_native.upper()}
        if sensor in self.window_query_sensors:
            params["startTime"] = int(request.requested_start.timestamp() * 1000)
            params["endTime"] = int(request.requested_end.timestamp() * 1000)
            params["limit"] = 1000
        elif sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            params["limit"] = 100
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # error envelopes: {"code": <int>, "msg": "..."}
    # ------------------------------------------------------------------

    def classify_failure(
        self, http_status: int | None, body: Any
    ) -> ProbeFailureClass:
        code = self._error_label_class(body)
        if code is not None:
            return code
        return super().classify_failure(http_status, body)

    def _error_label_class(self, body: Any) -> ProbeFailureClass | None:
        if not isinstance(body, dict) or not isinstance(body.get("code"), (int, float)):
            return None
        code = int(body["code"])
        if code == -1121:
            return ProbeFailureClass.F_SYMBOL_NOT_FOUND
        if code in (-1003, 418, 429):
            return ProbeFailureClass.F_ACCESS_RATE_LIMIT
        if code == 451:
            return ProbeFailureClass.F_ACCESS_GEO
        if code in (-2015, -1022):
            return ProbeFailureClass.F_ACCESS_AUTH
        if code == -1021:
            return ProbeFailureClass.F_CLIENT_4XX
        return None

    def _redacted_error(self, body: Any) -> str | None:
        if isinstance(body, dict) and isinstance(body.get("msg"), str):
            return body["msg"][:200]
        return None

    # ------------------------------------------------------------------
    # pagination: startTime/endTime window coverage
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
        end_ms = int(request.requested_end.timestamp() * 1000)
        last = max(
            (row.get("time") or row.get("fundingTime") or row.get("timestamp") for row in rows),
            default=None,
        )
        if isinstance(last, (int, float)):
            return True, int(last) >= end_ms
        return True, None

    # ------------------------------------------------------------------
    # public archive characterization (deterministic file naming + checksums)
    # ------------------------------------------------------------------

    def archive_file_url(self, symbol: str, date: str, kind: str) -> str:
        """Deterministic daily archive file URL (02 §7 probe priority §1)."""
        if kind not in ARCHIVE_KINDS:
            raise ValueError(f"unknown binance archive kind {kind!r}")
        return f"{self.archive_base_url}/{kind}/{symbol}/{symbol}-{kind}-{date}.zip"

    def archive_checksum_url(self, symbol: str, date: str, kind: str) -> str:
        return f"{self.archive_file_url(symbol, date, kind)}.CHECKSUM"

    def characterize_archive(
        self,
        request: CapabilityProbeRequest,
        *,
        kind: str,
        date: str,
        file_status: int,
        checksum_status: str,
        checksum_line: str | None = None,
    ) -> CapabilityProbeAttempt:
        """Characterize one deterministic archive file + its checksum.

        `checksum_status` is one of "present" | "missing" | "unverified".
        A 404 on the file is F_ARCHIVE_NOT_FOUND (a historical hole), never a
        zero or an assumption of continuity.
        """
        symbol = request.instrument_native.upper()
        file_url = self.archive_file_url(symbol, date, kind)
        common: dict[str, Any] = {
            "probe_id": (
                f"{PROVIDER_ID.lower()}_archive_{kind}_{symbol.lower()}_{date}"
            ),
            "probe_run_id": request.probe_run_id,
            "provider_id": PROVIDER_ID,
            "sensor_family": request.sensor_family,
            "venue_market": "BINANCE_USDM",
            "instrument_native": request.instrument_native,
            "canonical_asset_hint": request.canonical_asset_hint,
            "requested_start": request.requested_start,
            "requested_end": request.requested_end,
            "requested_granularity": request.requested_granularity,
            "access_mode": AccessMode.PUBLIC_ARCHIVE,
            "query_mode": request.query_mode,
            "http_status_or_file_status": file_status,
            "request_fingerprint": file_url,
            "native_units_summary": {
                "archive_kind": kind,
                "file": f"{symbol}-{kind}-{date}.zip",
                "checksum": checksum_status,
            },
            "payload_hash_sample": (checksum_line or "")[:100] or None,
            "era_hint": request.era_hint,
            "probe_version": "binance-archive-v1",
        }
        if file_status == 200:
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.VERIFIED_SAMPLE,
                    "rows_returned": 0,  # file bytes; rows characterized at download
                    "rate_limit_metadata": {
                        "archive_kind": kind,
                        "checksum_status": checksum_status,
                    },
                }
            )
        failure = super().classify_failure(file_status, {})
        if file_status == 404:
            failure = ProbeFailureClass.F_ARCHIVE_NOT_FOUND
        return CapabilityProbeAttempt.model_validate(
            {
                **common,
                "response_status_class": ResponseStatusClass.FAILED,
                "error_class": failure,
                "error_detail_redacted": (
                    f"archive file missing: {symbol}-{kind}-{date}.zip"
                    if file_status == 404
                    else None
                ),
                "geo_block_detected": file_status == 451,
            }
        )
