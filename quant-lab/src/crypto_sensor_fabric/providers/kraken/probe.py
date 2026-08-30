"""Kraken Futures capability probe (bloc_02/02 §5 / 04 §6).

Minimal characterization module — NOT a production adapter.  It knows how to:

- map the playbook core instrument basket to native symbols (02 §4),
- build deterministic query shapes for each candidate sensor,
- classify failures (404 / 429 / invalidSymbol / 5xx / auth),
- summarize payloads (structural fingerprint, rows, timestamps, units).

Liquidations are not a dedicated endpoint: on /history they appear as trade
rows whose `type` field is "liquidation" (02 §5, §10 probe priorities).
Open interest is current-only via /tickers — historical OI is NOT publicly
exposed and must be characterized as CURRENT_ONLY / HISTORY_BLOCKED, never
assumed (probe priorities §4).  All characterization logic is offline;
fetching belongs to the explicit live run (SENSOR-B2-I13).
"""

from __future__ import annotations

from typing import Any

from ...contracts.enums import SensorFamily
from ...probes.enums import (
    AccessMode,
    ProbeFailureClass,
    ResponseStatusClass,
)
from ...probes.models import CapabilityProbeAttempt, CapabilityProbeRequest
from ...probes.payload import (
    TIMESTAMP_KEYS,
    find_row_lists,
    fingerprint_payload,
    first_last_timestamps,
)
from ..base import load_endpoint_registry

PROVIDER_ID = "KRAKEN_FUTURES"

#: Playbook core basket -> native perpetual symbols (02 §4).
#: MID_TAIL_CONTROL = DOGE: non-core, adequate venue history, no delisting
#: ambiguity where avoidable.  Operator-adjustable at probe-target config time.
NATIVE_INSTRUMENTS: dict[str, str] = {
    "BTC": "PI_XBTUSD",
    "ETH": "PI_ETHUSD",
    "SOL": "PI_SOLUSD",
    "MID_TAIL_CONTROL": "PI_DOGEUSD",
}

#: Sensor -> result-list key inside the v3 `result` envelope.
SENSOR_RESULT_KEYS: dict[SensorFamily, str] = {
    SensorFamily.MECHANICAL_TRADE: "history",
    SensorFamily.MECHANICAL_LIQUIDATION: "history",
    SensorFamily.MECHANICAL_OPEN_INTEREST: "tickers",
    SensorFamily.MECHANICAL_FUNDING: "rates",
    SensorFamily.MECHANICAL_BOOK_SNAPSHOT: "orderBook",
    SensorFamily.MECHANICAL_BASIS: "tickers",
}

#: Sensor -> native unit semantics (characterization knowledge, not inference).
SENSOR_UNITS: dict[SensorFamily, dict[str, str]] = {
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


class KrakenCapabilityProbe:
    """Kraken Futures v3 REST capability characterization (offline)."""

    provider_id = PROVIDER_ID
    access_mode = AccessMode.PUBLIC_REST

    def __init__(self, endpoints: dict[str, Any] | None = None) -> None:
        registry = endpoints if endpoints is not None else load_endpoint_registry()
        entry = registry.get(PROVIDER_ID, {})
        self.base_url: str = entry.get(
            "base_url", "https://futures.kraken.com/derivatives/api/v3"
        )
        self.endpoints: dict[str, str] = entry.get("endpoints", {})

    # ------------------------------------------------------------------
    # instrument mapping
    # ------------------------------------------------------------------

    def native_instrument(self, canonical_asset: str | None) -> str:
        """Map a playbook asset hint to the native perpetual symbol."""
        if canonical_asset is None:
            raise ValueError("kraken probe requires a canonical_asset_hint")
        native = NATIVE_INSTRUMENTS.get(canonical_asset.upper())
        if native is None:
            raise ValueError(f"kraken probe has no native mapping for {canonical_asset!r}")
        return native

    # ------------------------------------------------------------------
    # query construction
    # ------------------------------------------------------------------

    def _endpoint_for(self, sensor: SensorFamily) -> str:
        path = self.endpoints.get(sensor.value)
        if path is None:
            raise ValueError(f"kraken probe has no endpoint for sensor {sensor.value}")
        return f"{self.base_url}{path}"

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        """Deterministic query shape for one probe request.

        Returns {"url", "params"}.  `since`/`to` semantics: Kraken uses
        inclusive ms epochs (probe priority §5.4); `/history` supports a
        `since` cursor for bounded pagination.
        """
        sensor = request.sensor_family
        params: dict[str, Any] = {"symbol": request.instrument_native}
        if sensor is SensorFamily.MECHANICAL_TRADE or sensor is SensorFamily.MECHANICAL_LIQUIDATION:
            params["type"] = "all"
            params["since"] = int(request.requested_start.timestamp() * 1000)
        elif sensor is SensorFamily.MECHANICAL_FUNDING:
            params["from"] = int(request.requested_start.timestamp() * 1000)
            params["to"] = int(request.requested_end.timestamp() * 1000)
        elif sensor is SensorFamily.MECHANICAL_OPEN_INTEREST or sensor is SensorFamily.MECHANICAL_BASIS:
            pass  # tickers: latest snapshot only
        elif sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            params["depth"] = 25
        return {"url": self._endpoint_for(sensor), "params": params}

    # ------------------------------------------------------------------
    # failure classification
    # ------------------------------------------------------------------

    def classify_failure(
        self, http_status: int | None, body: Any
    ) -> ProbeFailureClass:
        if http_status is not None:
            if http_status == 401 or http_status == 403:
                return ProbeFailureClass.F_ACCESS_AUTH
            if http_status == 404:
                return ProbeFailureClass.F_ENDPOINT_REMOVED
            if http_status == 429:
                return ProbeFailureClass.F_ACCESS_RATE_LIMIT
            if http_status == 451:
                return ProbeFailureClass.F_ACCESS_GEO
            if http_status >= 500:
                return ProbeFailureClass.F_SERVER_5XX
            if http_status >= 400:
                return ProbeFailureClass.F_CLIENT_4XX
        # v3 error envelopes: {"error": "..."}
        if isinstance(body, dict) and isinstance(body.get("error"), str):
            error = body["error"].lower()
            if "symbol" in error or "instrument" in error:
                return ProbeFailureClass.F_SYMBOL_NOT_FOUND
            if "rate" in error or "limit" in error:
                return ProbeFailureClass.F_ACCESS_RATE_LIMIT
            if "permission" in error or "auth" in error:
                return ProbeFailureClass.F_ACCESS_AUTH
            if "geo" in error or "region" in error:
                return ProbeFailureClass.F_ACCESS_GEO
        return ProbeFailureClass.F_UNKNOWN

    # ------------------------------------------------------------------
    # payload characterization
    # ------------------------------------------------------------------

    def _result_rows(self, body: Any, sensor: SensorFamily) -> list[dict[str, Any]]:
        """Extract the sensor's row list from a v3 result envelope."""
        if not isinstance(body, dict) or "result" not in body:
            raise ValueError("kraken payload missing 'result' envelope")
        result = body["result"]
        key = SENSOR_RESULT_KEYS[sensor]
        if key not in result:
            raise ValueError(f"kraken result missing '{key}' for {sensor.value}")
        value = result[key]
        if isinstance(value, dict):  # orderBook: {"bids": [[p, s, ts]], "asks": ...}
            if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
                merged: list[dict[str, Any]] = []
                for side in ("bids", "asks"):
                    for level in value.get(side, []):
                        if isinstance(level, list) and len(level) >= 2:
                            row: dict[str, Any] = {
                                "side": side,
                                "price": level[0],
                                "size": level[1],
                            }
                            if len(level) >= 3:
                                row["ts"] = level[2]
                            merged.append(row)
                return merged
            return value
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        raise ValueError(f"kraken result key '{key}' has unexpected shape")

    def extract_timestamp_fields(self, body: Any) -> list[str]:
        """Timestamp field candidates observed in the payload (probe P6)."""
        observed: list[str] = []
        for row_list in find_row_lists(body):
            for row in row_list[:200]:
                if not isinstance(row, dict):
                    continue
                for key in TIMESTAMP_KEYS:
                    if key in row and key not in observed:
                        observed.append(key)
        return observed

    def summarize_native_schema(self, body: Any) -> dict[str, Any]:
        return {
            "fingerprint": fingerprint_payload(body),
            "row_lists": [len(rows) for rows in find_row_lists(body)],
            "timestamp_fields": self.extract_timestamp_fields(body),
        }

    def characterize(
        self,
        request: CapabilityProbeRequest,
        http_status: int | None,
        body: Any,
    ) -> CapabilityProbeAttempt:
        """Map one fetched response into an immutable probe attempt."""
        sensor = request.sensor_family
        common: dict[str, Any] = {
            "probe_id": _probe_id(request),
            "probe_run_id": request.probe_run_id,
            "provider_id": PROVIDER_ID,
            "sensor_family": sensor,
            "venue_market": "KRAKEN_FUTURES",
            "instrument_native": request.instrument_native,
            "canonical_asset_hint": request.canonical_asset_hint,
            "requested_start": request.requested_start,
            "requested_end": request.requested_end,
            "requested_granularity": request.requested_granularity,
            "access_mode": request.access_mode,
            "query_mode": request.query_mode,
            "http_status_or_file_status": http_status,
            "payload_schema_fingerprint": fingerprint_payload(body),
            "native_timestamp_fields": self.extract_timestamp_fields(body),
            "native_units_summary": dict(SENSOR_UNITS.get(sensor, {})),
            "era_hint": request.era_hint,
            "probe_version": "kraken-probe-v1",
        }

        # failures
        if http_status is not None and http_status >= 400:
            failure = self.classify_failure(http_status, body)
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": failure,
                    "error_detail_redacted": _redacted_error(body),
                    "requires_auth": failure is ProbeFailureClass.F_ACCESS_AUTH,
                    "requires_payment": failure is ProbeFailureClass.F_ACCESS_PAYMENT,
                    "geo_block_detected": failure is ProbeFailureClass.F_ACCESS_GEO,
                }
            )
        # error envelope with HTTP 200 (Kraken returns 200 for domain errors)
        if isinstance(body, dict) and isinstance(body.get("error"), str):
            failure = self.classify_failure(http_status, body)
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": failure,
                    "error_detail_redacted": _redacted_error(body),
                }
            )

        # success: valid rows or valid empty
        try:
            rows = self._result_rows(body, sensor)
        except ValueError:
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": ProbeFailureClass.F_SCHEMA_CHANGED,
                    "error_detail_redacted": "result envelope missing expected sensor key",
                }
            )

        row_dicts = [r for r in rows if isinstance(r, dict)]
        first_ts, last_ts = first_last_timestamps(row_dicts)
        rows_returned = len(row_dicts)

        # pagination: /history pages back via `since` (ms timestamp).  The
        # page is complete when the oldest returned row reaches the requested
        # window start; a newer last row means older trades still exist.
        pagination_detected = sensor in {
            SensorFamily.MECHANICAL_TRADE,
            SensorFamily.MECHANICAL_LIQUIDATION,
        }
        pagination_complete = None
        if pagination_detected and row_dicts:
            last_time = row_dicts[-1].get("time")
            params = self.build_probe_request(request).get("params", {})
            since = params.get("since") if isinstance(params, dict) else None
            if since is not None and isinstance(last_time, (int, float)):
                pagination_complete = int(last_time) <= int(since)

        status = (
            ResponseStatusClass.VERIFIED_SAMPLE
            if rows_returned > 0
            else ResponseStatusClass.EMPTY_VALID
        )
        return CapabilityProbeAttempt.model_validate(
            {
                **common,
                "response_status_class": status,
                "rows_returned": rows_returned,
                "first_timestamp_returned": first_ts,
                "last_timestamp_returned": last_ts,
                "pagination_detected": pagination_detected,
                "pagination_complete": pagination_complete,
                # request_fingerprint is stamped by the live executor with the
                # normalized query shape (reproducibility gate, 03 §19)
            }
        )


def _probe_id(request: CapabilityProbeRequest) -> str:
    parts = [
        PROVIDER_ID.lower(),
        request.sensor_family.value.lower().replace("mechanical_", ""),
        request.instrument_native.lower(),
        request.era_hint or "unera",
        request.requested_granularity.value.lower(),
    ]
    return "_".join(parts)


def _redacted_error(body: Any) -> str | None:
    if isinstance(body, dict) and isinstance(body.get("error"), str):
        # v3 errors are short codes; never echo user-supplied parameters
        return body["error"][:200]
    return None
