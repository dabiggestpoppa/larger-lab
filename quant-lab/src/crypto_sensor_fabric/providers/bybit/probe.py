"""Bybit Linear capability probe (bloc_02/02 §8 / 04 §6).

Minimal characterization module — NOT a production adapter.  Bybit is the
independent historical OI + funding + trade backbone candidate:

- `/open-interest` and `/funding/history` use `nextPageCursor` cursor
  pagination; cursor traversal must PROVE symbol-launch-depth history —
  documentation claims alone do not (probe priorities §8.1-8.2),
- OI rows are numeric strings and OI units are contracts (linear); units must
  be verified per contract type (§8.3),
- historical trades live in the public.bybit.com daily csv.gz archive,
- there is NO public historical liquidation surface — do not infer one from
  current liquidation streams (§8.7).

All characterization is offline; fetching belongs to SENSOR-B2-I13.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ...contracts.enums import SensorFamily
from ...probes.enums import AccessMode, ProbeFailureClass, ResponseStatusClass
from ...probes.models import CapabilityProbeAttempt, CapabilityProbeRequest
from ..base import load_endpoint_registry
from ..rest import RestCapabilityProbeBase

PROVIDER_ID = "BYBIT_LINEAR"

#: Playbook core basket -> native linear perpetual symbols (02 §4).
NATIVE_INSTRUMENTS: ClassVar[dict[str, str]] = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "MID_TAIL_CONTROL": "DOGEUSDT",
}

#: Public trading archive (daily csv.gz, deterministic naming, no checksums).
ARCHIVE_BASE_URL = "https://public.bybit.com/trading"

#: OI history intervalTime used for windowed checkpoint probes.
OI_INTERVAL = "1h"

#: v5 public error retCodes mapped to failure classes (characterization-level;
#: live verification may refine the table).
RETCODE_FAILURE: dict[int, ProbeFailureClass] = {
    10001: ProbeFailureClass.F_ACCESS_AUTH,
    10002: ProbeFailureClass.F_ACCESS_AUTH,
    10003: ProbeFailureClass.F_ACCESS_AUTH,
    10004: ProbeFailureClass.F_ACCESS_RATE_LIMIT,
    10006: ProbeFailureClass.F_CLIENT_4XX,
    110001: ProbeFailureClass.F_SYMBOL_NOT_FOUND,
}


class BybitCapabilityProbe(RestCapabilityProbeBase):
    """Bybit v5 Linear market characterization (offline)."""

    provider_id = PROVIDER_ID
    venue_market = "BYBIT_LINEAR"
    access_mode = AccessMode.PUBLIC_REST
    base_url = "https://api.bybit.com/v5/market"
    probe_version = "bybit-probe-v1"

    native_instruments = NATIVE_INSTRUMENTS

    #: rows sit under result.list for every REST sensor except the book,
    #: whose bids/asks live directly under result (no sub-key)
    result_key_sensors: ClassVar[dict[SensorFamily, str]] = {
        SensorFamily.MECHANICAL_OPEN_INTEREST: "list",
        SensorFamily.MECHANICAL_FUNDING: "list",
        SensorFamily.MECHANICAL_TRADE: "list",
    }
    book_in_result_sensors = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

    #: nextPageCursor cursor pagination
    cursor_paginated_sensors = frozenset(
        {SensorFamily.MECHANICAL_OPEN_INTEREST, SensorFamily.MECHANICAL_FUNDING}
    )
    #: latest-only surfaces
    latest_only_sensors = frozenset(
        {SensorFamily.MECHANICAL_TRADE, SensorFamily.MECHANICAL_BOOK_SNAPSHOT}
    )
    #: windowed (startTime/endTime) surfaces
    window_query_sensors = frozenset(
        {SensorFamily.MECHANICAL_OPEN_INTEREST, SensorFamily.MECHANICAL_FUNDING}
    )

    #: sensor -> native unit semantics (characterization knowledge)
    sensor_units: ClassVar[dict[SensorFamily, dict[str, str]]] = {
        SensorFamily.MECHANICAL_OPEN_INTEREST: {
            "openInterest": "contracts (linear) — verify per contract type",
            "timestamp": "ms epoch (string) — period start",
            "intervalTime": "5min|15min|30min|1h|4h|1d",
        },
        SensorFamily.MECHANICAL_FUNDING: {
            "fundingRate": "decimal fraction per 8h interval",
            "fundingTime": "ms epoch (string) — effective at",
            "markPrice": "USD",
        },
        SensorFamily.MECHANICAL_TRADE: {
            "price": "USD",
            "qty": "base asset",
            "side": "Buy|Sell — aggressor side directly",
            "time": "ms epoch (string) — event time",
        },
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT: {
            "bids/asks": "[[price USD, size base asset]]",
            "ts": "ms epoch (snapshot)",
        },
    }

    def __init__(self, endpoints: dict[str, Any] | None = None) -> None:
        super().__init__(endpoints)
        registry = endpoints if endpoints is not None else load_endpoint_registry()
        entry = registry.get(PROVIDER_ID, {})
        self.archive_base_url: str = entry.get("archive_base_url", ARCHIVE_BASE_URL)

    # ------------------------------------------------------------------
    # query construction — v5 category=linear
    # ------------------------------------------------------------------

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        sensor = request.sensor_family
        params: dict[str, Any] = {
            "category": "linear",
            "symbol": request.instrument_native,
        }
        if sensor in self.window_query_sensors:
            params["startTime"] = int(request.requested_start.timestamp() * 1000)
            params["endTime"] = int(request.requested_end.timestamp() * 1000)
            params["limit"] = 200
            if sensor is SensorFamily.MECHANICAL_OPEN_INTEREST:
                params["intervalTime"] = OI_INTERVAL
        elif sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            params["limit"] = 25
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # error envelopes: {"retCode": <int>, "retMsg": "..."}
    # ------------------------------------------------------------------

    def classify_failure(
        self, http_status: int | None, body: Any
    ) -> ProbeFailureClass:
        ret = self._error_label_class(body)
        if ret is not None:
            return ret
        return super().classify_failure(http_status, body)

    def _error_label_class(self, body: Any) -> ProbeFailureClass | None:
        if not isinstance(body, dict) or not isinstance(body.get("retCode"), (int, float)):
            return None
        return RETCODE_FAILURE.get(int(body["retCode"]))

    def _redacted_error(self, body: Any) -> str | None:
        if isinstance(body, dict) and isinstance(body.get("retMsg"), str):
            return body["retMsg"][:200]
        return None

    # ------------------------------------------------------------------
    # pagination: nextPageCursor in the result envelope
    # ------------------------------------------------------------------

    def _pagination_state(
        self,
        request: CapabilityProbeRequest,
        rows: list[dict[str, Any]],
        sensor: SensorFamily,
        body: Any = None,
    ) -> tuple[bool, bool | None]:
        if sensor not in self.cursor_paginated_sensors:
            return False, None
        if not isinstance(body, dict) or not isinstance(body.get("result"), dict):
            return True, None
        cursor = body["result"].get("nextPageCursor")
        if not cursor:
            return True, True  # terminal page
        return True, False  # more pages exist

    # ------------------------------------------------------------------
    # public trading archive (deterministic daily csv.gz naming)
    # ------------------------------------------------------------------

    def archive_file_url(self, symbol: str, date: str) -> str:
        return f"{self.archive_base_url}/{symbol}/{symbol}{date}.csv.gz"

    def characterize_archive(
        self,
        request: CapabilityProbeRequest,
        *,
        date: str,
        file_status: int,
    ) -> CapabilityProbeAttempt:
        """Characterize one daily trade archive file (no published checksums)."""
        symbol = request.instrument_native
        file_url = self.archive_file_url(symbol, date)
        common: dict[str, Any] = {
            "probe_id": f"{PROVIDER_ID.lower()}_archive_trades_{symbol.lower()}_{date}",
            "probe_run_id": request.probe_run_id,
            "provider_id": PROVIDER_ID,
            "sensor_family": SensorFamily.MECHANICAL_TRADE,
            "venue_market": "BYBIT_LINEAR",
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
                "archive_kind": "trades",
                "file": f"{symbol}{date}.csv.gz",
                "checksum": "not_published",
            },
            "era_hint": request.era_hint,
            "probe_version": "bybit-archive-v1",
        }
        if file_status == 200:
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.VERIFIED_SAMPLE,
                    "rows_returned": 0,  # file bytes; rows characterized at download
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
                    f"archive file missing: {symbol}{date}.csv.gz"
                    if file_status == 404
                    else None
                ),
            }
        )
