"""Shared REST capability-probe base (bloc_02/04 §5-6).

Most provider modules are free public REST surfaces with the same
characterization needs: deterministic query construction, failure
classification, payload fingerprinting, timestamp/unit extraction and
immutable attempt construction.  This base implements that machinery;
provider modules subclass it and declare only what is provider-specific:

- endpoint paths and base URL,
- how rows are extracted from the payload (`_extract_rows`),
- error-envelope label classification (`_error_label_class`),
- pagination semantics (`_pagination_state`),
- native units and instrument mapping,
- small query-shape overrides (build_probe_request).

Characterization stays pure and offline; fetching belongs to the explicit
live run (SENSOR-B2-I13).  Provider identity is never merged.
"""

from __future__ import annotations

from typing import Any, ClassVar

from ..contracts.enums import SensorFamily
from ..probes.enums import (
    AccessMode,
    ProbeFailureClass,
    ResponseStatusClass,
)
from ..probes.models import CapabilityProbeAttempt, CapabilityProbeRequest
from ..probes.payload import (
    TIMESTAMP_KEYS,
    find_row_lists,
    fingerprint_payload,
    first_last_timestamps,
)
from .base import load_endpoint_registry

#: Default page limit for bounded characterization (providers may override).
DEFAULT_PAGE_LIMIT = 1000


class RestCapabilityProbeBase:
    """Deterministic, offline characterization of one free REST surface."""

    provider_id: ClassVar[str] = ""
    venue_market: ClassVar[str] = ""
    access_mode: ClassVar[AccessMode] = AccessMode.PUBLIC_REST
    base_url: ClassVar[str] = ""
    probe_version: ClassVar[str] = "rest-probe-v1"

    #: sensor -> endpoint path (relative to base_url)
    endpoint_paths: ClassVar[dict[SensorFamily, str]] = {}
    #: sensor -> native unit semantics (characterization knowledge)
    sensor_units: ClassVar[dict[SensorFamily, dict[str, str]]] = {}
    #: playbook asset hint -> native instrument
    native_instruments: ClassVar[dict[str, str]] = {}
    #: sensors whose payload row list sits at the top level of the body
    top_level_list_sensors: ClassVar[frozenset[SensorFamily]] = frozenset()
    #: sensors whose payload is a top-level book dict {"bids": [...], "asks": [...]}
    top_level_book_sensors: ClassVar[frozenset[SensorFamily]] = frozenset()
    #: sensors reached via body["result"][key]
    result_key_sensors: ClassVar[dict[SensorFamily, str]] = {}
    #: sensors queried with a `since` (ms) cursor
    cursor_paginated_sensors: ClassVar[frozenset[SensorFamily]] = frozenset()
    #: sensors that return only the latest snapshot (no historical window)
    latest_only_sensors: ClassVar[frozenset[SensorFamily]] = frozenset()
    #: sensors queried with from/to (ms) windows
    window_query_sensors: ClassVar[frozenset[SensorFamily]] = frozenset()
    #: default characterization limit
    page_limit: ClassVar[int] = DEFAULT_PAGE_LIMIT

    def __init__(self, endpoints: dict[str, Any] | None = None) -> None:
        registry = endpoints if endpoints is not None else load_endpoint_registry()
        entry = registry.get(self.provider_id, {})
        if self.base_url:
            # subclass default stands; registry may override it
            self.base_url = entry.get("base_url", self.base_url)
        else:
            self.base_url = entry.get("base_url", "")
        registered = entry.get("endpoints", {})
        if registered:
            self.endpoint_paths = {
                SensorFamily(key): str(path) for key, path in registered.items()
            }

    # ------------------------------------------------------------------
    # instrument mapping
    # ------------------------------------------------------------------

    def native_instrument(self, canonical_asset: str | None) -> str:
        if canonical_asset is None:
            raise ValueError(f"{self.provider_id} probe requires a canonical_asset_hint")
        native = self.native_instruments.get(canonical_asset.upper())
        if native is None:
            raise ValueError(
                f"{self.provider_id} probe has no native mapping for {canonical_asset!r}"
            )
        return native

    # ------------------------------------------------------------------
    # query construction
    # ------------------------------------------------------------------

    def _endpoint_for(self, sensor: SensorFamily) -> str:
        path = self.endpoint_paths.get(sensor)
        if path is None:
            raise ValueError(f"{self.provider_id} probe has no endpoint for {sensor.value}")
        return f"{self.base_url}{path}"

    def build_probe_request(self, request: CapabilityProbeRequest) -> dict[str, Any]:
        """Deterministic query shape: {"url", "params"}.

        Default parameterization: `symbol` always; `since` (ms) for cursor
        sensors; `from`/`to` (ms) for window sensors; none for latest-only.
        Providers override for provider-specific details.
        """
        sensor = request.sensor_family
        params: dict[str, Any] = {"symbol": request.instrument_native}
        if sensor in self.cursor_paginated_sensors:
            params["since"] = int(request.requested_start.timestamp() * 1000)
        elif sensor in self.window_query_sensors:
            params["from"] = int(request.requested_start.timestamp() * 1000)
            params["to"] = int(request.requested_end.timestamp() * 1000)
        params["limit"] = self.page_limit
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
        label = self._error_label_class(body)
        return label if label is not None else ProbeFailureClass.F_UNKNOWN

    def _error_label_class(self, body: Any) -> ProbeFailureClass | None:
        """Provider-specific error envelope -> failure class (override)."""
        return None

    # ------------------------------------------------------------------
    # payload extraction
    # ------------------------------------------------------------------

    def _extract_rows(self, body: Any, sensor: SensorFamily) -> list[dict[str, Any]]:
        """Extract the sensor's row list from the payload (override as needed)."""
        if sensor in self.top_level_list_sensors:
            if not isinstance(body, list):
                raise ValueError(f"{self.provider_id} payload is not a row list")
            return [row for row in body if isinstance(row, dict)]
        if sensor in self.top_level_book_sensors:
            if not isinstance(body, dict) or "bids" not in body or "asks" not in body:
                raise ValueError(f"{self.provider_id} payload is not a top-level book")
            return self._flatten_book(body)
        if not isinstance(body, dict) or "result" not in body:
            raise ValueError(f"{self.provider_id} payload missing 'result' envelope")
        result = body["result"]
        key = self.result_key_sensors[sensor]
        if key not in result:
            raise ValueError(f"{self.provider_id} result missing '{key}' for {sensor.value}")
        value = result[key]
        if isinstance(value, dict):  # book: {"bids": [[p, s, ts]], "asks": [...]}
            return self._flatten_book(value)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        raise ValueError(f"{self.provider_id} result key '{key}' has unexpected shape")

    def _flatten_book(self, value: dict[str, Any]) -> list[dict[str, Any]]:
        """Flatten a book dict into per-level rows with side/price/size/ts."""
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

    # ------------------------------------------------------------------
    # pagination semantics
    # ------------------------------------------------------------------

    def _pagination_state(
        self,
        request: CapabilityProbeRequest,
        rows: list[dict[str, Any]],
        sensor: SensorFamily,
    ) -> tuple[bool, bool | None]:
        """(pagination_detected, pagination_complete).  Override per provider."""
        return False, None

    # ------------------------------------------------------------------
    # payload characterization
    # ------------------------------------------------------------------

    def extract_timestamp_fields(self, body: Any) -> list[str]:
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
            "probe_id": self._probe_id(request),
            "probe_run_id": request.probe_run_id,
            "provider_id": self.provider_id,
            "sensor_family": sensor,
            "venue_market": self.venue_market,
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
            "native_units_summary": dict(self.sensor_units.get(sensor, {})),
            "era_hint": request.era_hint,
            "probe_version": self.probe_version,
        }

        if http_status is not None and http_status >= 400:
            failure = self.classify_failure(http_status, body)
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": failure,
                    "error_detail_redacted": self._redacted_error(body),
                    "requires_auth": failure is ProbeFailureClass.F_ACCESS_AUTH,
                    "requires_payment": failure is ProbeFailureClass.F_ACCESS_PAYMENT,
                    "geo_block_detected": failure is ProbeFailureClass.F_ACCESS_GEO,
                }
            )

        domain_failure = self._domain_error(body)
        if domain_failure is not None:
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": domain_failure,
                    "error_detail_redacted": self._redacted_error(body),
                }
            )

        try:
            rows = self._extract_rows(body, sensor)
        except ValueError:
            return CapabilityProbeAttempt.model_validate(
                {
                    **common,
                    "response_status_class": ResponseStatusClass.FAILED,
                    "error_class": ProbeFailureClass.F_SCHEMA_CHANGED,
                    "error_detail_redacted": "payload shape does not match sensor contract",
                }
            )

        first_ts, last_ts = first_last_timestamps(rows)
        pagination_detected, pagination_complete = self._pagination_state(
            request, rows, sensor
        )
        status = (
            ResponseStatusClass.VERIFIED_SAMPLE
            if rows
            else ResponseStatusClass.EMPTY_VALID
        )
        return CapabilityProbeAttempt.model_validate(
            {
                **common,
                "response_status_class": status,
                "rows_returned": len(rows),
                "first_timestamp_returned": first_ts,
                "last_timestamp_returned": last_ts,
                "pagination_detected": pagination_detected,
                "pagination_complete": pagination_complete,
            }
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _domain_error(self, body: Any) -> ProbeFailureClass | None:
        """A domain error carried in a 200 response (provider override)."""
        return self._error_label_class(body)

    def _redacted_error(self, body: Any) -> str | None:
        """Short redacted provider-native error text (override)."""
        return None

    def _probe_id(self, request: CapabilityProbeRequest) -> str:
        parts = [
            self.provider_id.lower(),
            request.sensor_family.value.lower().replace("mechanical_", ""),
            request.instrument_native.lower(),
            request.era_hint or "unera",
            request.requested_granularity.value.lower(),
        ]
        return "_".join(parts)
