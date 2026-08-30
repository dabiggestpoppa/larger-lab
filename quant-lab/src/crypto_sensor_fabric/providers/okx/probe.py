"""OKX Swap capability probe (bloc_02/02 §9 / 04 §6).

Minimal characterization module — NOT a production adapter.  OKX is the
candidate for historical trades/funding plus the deepest possible historical
book source:

- `/history-trades` and `/funding-rate-history` page backward via `after`/
  `before` (trade ids, not timestamps); cursor traversal must prove depth,
- `/books` returns a CURRENT snapshot only (sz-level); DEEP BOOK HISTORY is
  UNVERIFIED pending the live probe — never claimed (probe priorities §9.3),
- the public traderecords daily zip archive `{instId}/{YYYYMMDD}.zip` is the
  historical trade download route; link expiry and async archive generation
  must be probed (§9.6),
- OI: no official free historical route is assumed; current OI is never
  substituted for history (§9.6).

OKX timestamps are ms-epoch strings.  All characterization is offline;
fetching belongs to SENSOR-B2-I13.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ...contracts.enums import SensorFamily
from ...probes.enums import AccessMode, ProbeFailureClass, ResponseStatusClass
from ...probes.models import CapabilityProbeAttempt, CapabilityProbeRequest
from ..base import load_endpoint_registry
from ..rest import RestCapabilityProbeBase

PROVIDER_ID = "OKX_SWAP"

#: Playbook core basket -> native swap instrument ids (02 §4).
NATIVE_INSTRUMENTS: ClassVar[dict[str, str]] = {
    "BTC": "BTC-USDT-SWAP",
    "ETH": "ETH-USDT-SWAP",
    "SOL": "SOL-USDT-SWAP",
    "MID_TAIL_CONTROL": "DOGE-USDT-SWAP",
}

#: Public daily trade-history archive (traderecords).
ARCHIVE_BASE_URL = "https://www.okx.com/cdn/okex/traderecords"

#: Cursor page limit for history endpoints.
PAGE_LIMIT = 100

#: v5 error code strings mapped to failure classes (characterization-level;
#: live verification may refine the table).
CODE_FAILURE: dict[str, ProbeFailureClass] = {
    "50011": ProbeFailureClass.F_ACCESS_RATE_LIMIT,
    "50012": ProbeFailureClass.F_ACCESS_RATE_LIMIT,
    "50110": ProbeFailureClass.F_ACCESS_RATE_LIMIT,
    "50111": ProbeFailureClass.F_ACCESS_RATE_LIMIT,
    "51001": ProbeFailureClass.F_SYMBOL_NOT_FOUND,
    "50113": ProbeFailureClass.F_ACCESS_AUTH,
}


class OkxCapabilityProbe(RestCapabilityProbeBase):
    """OKX v5 Swap market characterization (offline)."""

    provider_id = PROVIDER_ID
    venue_market = "OKX_SWAP"
    access_mode = AccessMode.PUBLIC_REST
    base_url = "https://www.okx.com/api/v5/market"
    probe_version = "okx-probe-v1"

    native_instruments = NATIVE_INSTRUMENTS
    envelope_key = "data"

    #: history rows ARE the data envelope content; the book's data is a list
    #: holding one book dict
    envelope_is_list_sensors = frozenset(
        {SensorFamily.MECHANICAL_TRADE, SensorFamily.MECHANICAL_FUNDING}
    )
    book_in_result_sensors = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

    #: after/before (trade id) cursor pagination
    cursor_paginated_sensors = frozenset(
        {SensorFamily.MECHANICAL_TRADE, SensorFamily.MECHANICAL_FUNDING}
    )
    #: current-only surface
    latest_only_sensors = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

    #: sensor -> native unit semantics (characterization knowledge)
    sensor_units: ClassVar[dict[SensorFamily, dict[str, str]]] = {
        SensorFamily.MECHANICAL_TRADE: {
            "px": "USD",
            "sz": "base asset",
            "side": "buy|sell — aggressor side directly",
            "ts": "ms epoch (string) — event time",
        },
        SensorFamily.MECHANICAL_FUNDING: {
            "fundingRate": "decimal fraction per 8h interval",
            "realizedRate": "decimal fraction (realized)",
            "fundingTime": "ms epoch (string) — effective at",
            "markPrice": "USD",
        },
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT: {
            "bids/asks": "[[px USD, sz base asset, ...]]",
            "sz": "levels requested (current snapshot only)",
            "deep_history": "UNVERIFIED — live probe required, not claimed",
        },
    }

    def __init__(self, endpoints: dict[str, Any] | None = None) -> None:
        super().__init__(endpoints)
        registry = endpoints if endpoints is not None else load_endpoint_registry()
        entry = registry.get(PROVIDER_ID, {})
        self.archive_base_url: str = entry.get("archive_base_url", ARCHIVE_BASE_URL)

    # ------------------------------------------------------------------
    # query construction — instId + after/before cursors
    # ------------------------------------------------------------------

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        sensor = request.sensor_family
        params: dict[str, Any] = {"instId": request.instrument_native}
        if sensor in self.cursor_paginated_sensors:
            params["limit"] = PAGE_LIMIT
        elif sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            params["sz"] = 400
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # error envelopes: {"code": "<str>", "msg": "..."}
    # ------------------------------------------------------------------

    def classify_failure(
        self, http_status: int | None, body: Any
    ) -> ProbeFailureClass:
        code = self._error_label_class(body)
        if code is not None:
            return code
        return super().classify_failure(http_status, body)

    def _error_label_class(self, body: Any) -> ProbeFailureClass | None:
        if not isinstance(body, dict) or not isinstance(body.get("code"), str):
            return None
        if body["code"] == "0":
            return None
        return CODE_FAILURE.get(body["code"])

    def _redacted_error(self, body: Any) -> str | None:
        if isinstance(body, dict) and isinstance(body.get("msg"), str):
            return body["msg"][:200]
        return None

    # ------------------------------------------------------------------
    # pagination: partial page means the history start was reached
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
        if not rows:
            return True, True  # empty page: nothing more to page
        return True, len(rows) < PAGE_LIMIT

    # ------------------------------------------------------------------
    # public trade-history archive (traderecords daily zips)
    # ------------------------------------------------------------------

    def archive_file_url(self, inst_id: str, date: str) -> str:
        """Daily trade-record archive URL (date as YYYYMMDD)."""
        compact = date.replace("-", "")
        return f"{self.archive_base_url}/{inst_id}/{compact}.zip"

    def characterize_archive(
        self,
        request: CapabilityProbeRequest,
        *,
        date: str,
        file_status: int,
    ) -> CapabilityProbeAttempt:
        """Characterize one daily traderecords zip (no published checksums)."""
        inst_id = request.instrument_native
        file_url = self.archive_file_url(inst_id, date)
        common: dict[str, Any] = {
            "probe_id": f"{PROVIDER_ID.lower()}_archive_trades_{inst_id.lower()}_{date}",
            "probe_run_id": request.probe_run_id,
            "provider_id": PROVIDER_ID,
            "sensor_family": SensorFamily.MECHANICAL_TRADE,
            "venue_market": "OKX_SWAP",
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
                "file": f"{inst_id}/{date.replace('-', '')}.zip",
                "checksum": "not_published",
            },
            "era_hint": request.era_hint,
            "probe_version": "okx-archive-v1",
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
                    f"archive file missing: {inst_id}/{date.replace('-', '')}.zip"
                    if file_status == 404
                    else None
                ),
            }
        )
