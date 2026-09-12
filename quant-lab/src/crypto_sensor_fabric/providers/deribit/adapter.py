"""Deribit v2 public production adapter (SENSOR-B3-I08).

Implements the common `MechanicalProviderAdapter` for DERIBIT using ONLY the
four paths promoted by I14 (`source_promotion_candidates.yaml`):

    MECHANICAL_BOOK_SNAPSHOT  (CURRENT_ONLY — current snapshot, no history)
    MECHANICAL_FUNDING        (SECONDARY — historical hourly funding records)
    MECHANICAL_LIQUIDATION    (MECHANISM_MICROSCOPE — trade-level liquidation
                               anatomy, NEVER interval totals)
    MECHANICAL_TRADE          (MECHANISM_MICROSCOPE — native trade events)

Everything else Deribit may offer is typed `CapabilityUnavailable` under the
CURRENT I14 freeze:

    MECHANICAL_BASIS, MECHANICAL_BOOK_METRIC, MECHANICAL_OPEN_INTEREST,
    MECHANICAL_POSITIONING

VIOLATIONS HERE ARE FORBIDDEN:

- BOOK_SNAPSHOT stays CURRENT_ONLY: `depth` snapshot only, no start/end/
  cursor/historical replay, no invented deep-book history.
- The liquidation sensor is a MECHANISM MICROSCOPE: it projects ONLY
  trade-level rows carrying the evidence-backed forced-liquidation flag; it is
  NEVER numerically merged with interval liquidation totals (T2-SEM-06), never
  bucketed/summed, and never reinterpreted via direction/size/price.  The same
  physical `get_last_trades_by_instrument` surface supports TRADE and
  LIQUIDATION as distinct logical sensors; the FULL raw payload is preserved
  before any sensor-specific projection.
- Funding `result` is a RAW LIST (observed LIVE) — the old `{data:[...]}`
  envelope assumption is never reintroduced.
- Verified-history bounds stay LITERAL: LIQUIDATION/TRADE verified coverage is
  a single recent timestamp per I14; historical request capability does NOT
  upgrade into verified deep history, and older evidence-basis probe ids do
  not move the verified bound.

This is an ACQUISITION BOUNDARY.  It preserves raw provider evidence (in a
`RawPayloadEnvelope` with a content hash), provider identity, native instrument
and native fields/units.  It never performs canonical unit conversion,
cross-venue synthesis, liquidation aggregation, or research compute.

Transport is injected (dependency injection) — standard tests use a FAKE
transport; NO network calls are made.  The free-only access gate runs BEFORE
any transport call.  Deribit event/history timestamps are provider-native
epoch MILLISECOND INTEGERS (strict `type(x) is int`, bool rejected), validated
before any convenience datetime is derived.

Completion truth (I08R1 seal): the Deribit history surfaces carry the
requested window directly (`start_timestamp`/`end_timestamp` in the request).
A single evidence-backed request window is certified complete ONLY when the
semantic output is non-empty, the FULL SOURCE-PAGE coverage (every
schema-validated source row, not the filtered projection) lies inside the
requested [start_time, end_time) window, and the provider-native terminal
condition is met.  Trade/liquidation terminal = `has_more=false` (current
request window); FUNDING terminal/exhaustive semantics are NOT established by
committed evidence, so funding is NEVER certified complete (completion_proof =
LIMITED).  COMPLETE never carries PARTIAL_INTERVAL (mutually exclusive; PARTIAL
means partial, COMPLETE means complete).  Continuation beyond the evidenced
single window (window shifting / deep traversal) is NOT proven by committed
I13 evidence, so no `next_resume_token` is ever invented (pagination/resume =
LIMITED) and incomplete windows are returned truthfully with
PARTIAL_INTERVAL / GAP_DETECTED quality flags.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Callable, NoReturn

from ...contracts.access import FreeOnlyPolicy
from ...contracts.enums import AccessClass, SensorFamily
from ..base.access import assert_free_only_access
from ..base.enums import AdapterAuthMode, QualityFlagAcquisition
from ..base.errors import (
    CapabilityUnavailable,
    InvalidInstrument,
    ProviderSemanticError,
    ProviderUnavailable,
    SchemaDrift,
)
from ..base.fingerprint import fingerprint_request, payload_hash
from ..base.models import (
    FetchBatch,
    FetchRequest,
    InstrumentListRequest,
    InstrumentListResult,
    ProviderCapabilities,
    RawPayloadEnvelope,
)
from .capabilities import (
    DERIBIT_PRODUCTION_INSTRUMENT_SCOPE,
    PROVIDER_ID,
    build_deribit_capabilities,
)
from .errors import is_deribit_error_body, map_deribit_error
from .parsers import (
    parse_deribit_book,
    parse_deribit_funding,
    parse_deribit_liquidations,
    parse_deribit_trades,
)
from .requests import DeribitRequestBuilder

# Default free-only registry policy for DERIBIT (Bloc 1 F9).
DEFAULT_FREE_ONLY_POLICY = FreeOnlyPolicy(
    access_class=AccessClass.FREE_AUTOMATED,
    cost_usd_required=0,
    payment_method_required=False,
    staking_required=False,
    transaction_required=False,
)

#: Neutral provider-level sensor placeholder for InstrumentListRequest identity
#: failures (same pattern sealed for Kraken/Gate/OKX in SENSOR-B3-I05R2).
#: Instrument discovery has no requested sensor; the frozen SensorFamily enum
#: defines no provider-level member, so this explicit placeholder is used ONLY
#: for InstrumentListRequest and NEVER claims a scientific sensor.
NEUTRAL_INSTRUMENT_LIST_SENSOR = SensorFamily.MECHANICAL_TRADE

#: Transport signature: (url, params) -> (http_status_or_None, parsed_body).
TransportFn = Callable[[str, dict[str, Any]], tuple[int | None, Any]]


def _ms_int_to_dt(value: Any) -> datetime | None:
    """Derive a UTC convenience datetime AFTER a validated ms-epoch INT.

    Evidence basis: Deribit event/history timestamps are epoch MILLISECOND
    integers (09 fingerprint `timestamp:int`).  Strict: only an exact int
    (bool rejected) is converted.
    """
    if type(value) is not int:
        return None
    try:
        return datetime.fromtimestamp(value / 1000, tz=UTC)
    except (OverflowError, ValueError, OSError):
        return None


class DeribitAdapter:
    """Production Deribit adapter (four promoted paths)."""

    provider_id = PROVIDER_ID

    def __init__(
        self,
        transport: TransportFn | None = None,
        *,
        free_only_policy: FreeOnlyPolicy | None = None,
        auth_mode: AdapterAuthMode = AdapterAuthMode.NO_AUTH,
        promotion_candidates: list[dict[str, object]] | None = None,
        adapter_version: str = "deribit-adapter-v1",
        now: Callable[[], datetime] | None = None,
    ) -> None:
        # No transport -> the adapter stays OFFLINE: a fetch with no injected
        # transport raises typed ProviderUnavailable naming the REQUESTED
        # sensor.
        self._transport = transport
        self._policy = free_only_policy or DEFAULT_FREE_ONLY_POLICY
        self._auth_mode = auth_mode
        self._caps = build_deribit_capabilities(promotion_candidates)
        self._builder = DeribitRequestBuilder()
        self.adapter_version = adapter_version
        self._now = now or (lambda: datetime.now(UTC))

    # ---- protocol ---------------------------------------------------------
    def capabilities(self) -> ProviderCapabilities:
        return self._caps

    def list_instruments(self, request: InstrumentListRequest) -> InstrumentListResult:
        # Provider identity is part of the request contract (I05R1 guard).
        if request.provider_id != PROVIDER_ID:
            self._raise_wrong_provider(
                request.provider_id, NEUTRAL_INSTRUMENT_LIST_SENSOR
            )
        # Configured PRODUCTION evidence scope (evidence-backed union), NOT
        # live provider discovery and NOT the probe universe: ETH / SOL stay
        # probe-only (see capabilities).
        return InstrumentListResult(
            provider_id=self.provider_id,
            native_instrument_ids=list(DERIBIT_PRODUCTION_INSTRUMENT_SCOPE),
            retrieved_at=self._now(),
        )

    def fetch_trades(self, request: FetchRequest) -> FetchBatch:
        # TRADE IS a promoted Deribit path: method identity first, then route
        # to the supported acquisition (SENSOR-B3-I05R2 Repair 2 / I08 §22).
        self._require_sensor(request.sensor_family, SensorFamily.MECHANICAL_TRADE)
        return self._fetch(request, SensorFamily.MECHANICAL_TRADE)

    def fetch_liquidations(self, request: FetchRequest) -> FetchBatch:
        # LIQUIDATION IS a promoted Deribit path: mechanism-microscope view of
        # the same physical trade surface.
        self._require_sensor(
            request.sensor_family, SensorFamily.MECHANICAL_LIQUIDATION
        )
        return self._fetch(request, SensorFamily.MECHANICAL_LIQUIDATION)

    def fetch_funding(self, request: FetchRequest) -> FetchBatch:
        return self._fetch(request, SensorFamily.MECHANICAL_FUNDING)

    def fetch_book(self, request: FetchRequest) -> FetchBatch:
        # BOOK_SNAPSHOT IS a promoted Deribit path: method identity first, then
        # the current-only snapshot acquisition.
        self._require_sensor(
            request.sensor_family, SensorFamily.MECHANICAL_BOOK_SNAPSHOT
        )
        return self._fetch(request, SensorFamily.MECHANICAL_BOOK_SNAPSHOT)

    # ---- unsupported surfaces (typed CapabilityUnavailable) ----------------
    def fetch_open_interest(self, request: FetchRequest) -> FetchBatch:
        self._require_sensor(
            request.sensor_family, SensorFamily.MECHANICAL_OPEN_INTEREST
        )
        self._raise_unsupported(request.sensor_family)

    def fetch_positioning(self, request: FetchRequest) -> FetchBatch:
        self._require_sensor(
            request.sensor_family, SensorFamily.MECHANICAL_POSITIONING
        )
        self._raise_unsupported(request.sensor_family)

    def fetch_basis(self, request: FetchRequest) -> FetchBatch:
        self._require_sensor(request.sensor_family, SensorFamily.MECHANICAL_BASIS)
        self._raise_unsupported(request.sensor_family)

    def fetch_book_metrics(self, request: FetchRequest) -> FetchBatch:
        self._require_sensor(
            request.sensor_family, SensorFamily.MECHANICAL_BOOK_METRIC
        )
        self._raise_unsupported(request.sensor_family)

    # ---- helpers ----------------------------------------------------------
    def _raise_unsupported(self, sensor: SensorFamily) -> NoReturn:
        raise CapabilityUnavailable(
            provider_id=self.provider_id,
            sensor_family=sensor,
            detail=(
                f"{sensor.value} is NOT a promoted Deribit production path under "
                "CURRENT I14 (source_promotion_candidates.yaml); typed "
                "unsupported — a queued Deribit capability must not broaden I08"
            ),
        )

    def _raise_wrong_provider(
        self, declared: str, sensor_family: SensorFamily
    ) -> NoReturn:
        """Foreign-provider rejection carrying the ACTUAL requested sensor."""
        raise ProviderSemanticError(
            provider_id=self.provider_id,
            sensor_family=sensor_family,
            detail=(
                f"request provider_id {declared!r} != adapter provider "
                f"{PROVIDER_ID!r} (provider identity is part of the request "
                "contract; rejected before any transport call)"
            ),
        )

    def _require_sensor(self, requested: SensorFamily, expected: SensorFamily) -> None:
        """Named protocol method / request sensor identity (I05R1 guard)."""
        if requested is not expected:
            raise ProviderSemanticError(
                provider_id=self.provider_id,
                sensor_family=requested,
                detail=(
                    f"method/sensor identity mismatch: {expected.value} fetch "
                    f"method called with a {requested.value} request (use "
                    "dispatch_fetch for generic routing)"
                ),
            )

    def _fetch(self, request: FetchRequest, expected_sensor: SensorFamily) -> FetchBatch:
        # 1. named-method / request sensor identity (before anything else).
        self._require_sensor(request.sensor_family, expected_sensor)
        sensor = request.sensor_family

        # 2. request provider identity MUST match the adapter.
        if request.provider_id != self.provider_id:
            self._raise_wrong_provider(request.provider_id, request.sensor_family)

        capability = self._caps.capability_for(sensor)
        if not capability.supported:
            self._raise_unsupported(sensor)

        # FREE-ONLY ACCESS GATE MUST RUN BEFORE ANY TRANSPORT CALL.
        assert_free_only_access(
            self.provider_id, self._policy, self._auth_mode, sensor_family=sensor
        )

        # 3. sensor-specific PRODUCTION symbol scope (I05R1 guard).  A foreign
        #    protocol method never reaches transport for an unproven symbol.
        if (
            capability.symbol_scope
            and request.native_instrument_id not in capability.symbol_scope
        ):
            raise InvalidInstrument(
                provider_id=self.provider_id,
                sensor_family=sensor,
                detail=(
                    f"native instrument {request.native_instrument_id!r} is not "
                    f"evidence-backed for {sensor.value} (symbol_scope="
                    f"{sorted(capability.symbol_scope)})"
                ),
            )

        # 4. request building (may raise UnsupportedGranularity) — still before
        #    any transport call.  Deribit history requests carry the requested
        #    window directly (start_timestamp/end_timestamp, epoch ms).
        url, params = self._builder.build(request)
        fp = fingerprint_request(request, self._builder.endpoint_family(sensor), params)

        # 5. no transport -> typed ProviderUnavailable naming THIS sensor.
        if self._transport is None:
            raise ProviderUnavailable(
                provider_id=self.provider_id,
                sensor_family=sensor,
                detail=(
                    "no transport injected; adapter is offline (never "
                    "fabricates a network path)"
                ),
            )
        status, body = self._transport(url, params)

        if status is not None and status not in (200, 201, 204):
            raise map_deribit_error(
                self.provider_id, sensor, body, status, request_fingerprint=fp
            )
        if is_deribit_error_body(body):
            # JSON-RPC errors ride HTTP 200 inside {"error": {...}}.
            raise map_deribit_error(
                self.provider_id, sensor, body,
                status if status is not None else 200,
                request_fingerprint=fp,
            )

        if sensor is SensorFamily.MECHANICAL_FUNDING:
            parsed = parse_deribit_funding(body)
        elif sensor is SensorFamily.MECHANICAL_LIQUIDATION:
            parsed = parse_deribit_liquidations(body)
        elif sensor is SensorFamily.MECHANICAL_TRADE:
            parsed = parse_deribit_trades(body)
        else:  # BOOK_SNAPSHOT
            parsed = parse_deribit_book(body)

        # MATERIALIZE the immutable raw acquisition artifact BEFORE the parse
        # decision (I05R1 pattern): the envelope exists even when the schema is
        # BREAKING/UNKNOWN, so the failure path carries the exact preserved raw
        # body, hash, provider, sensor, fingerprint and retrieval metadata.
        raw_text = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        raw_bytes = raw_text.encode("utf-8")
        content_hash = payload_hash(raw_bytes)
        envelope = RawPayloadEnvelope(
            provider_id=self.provider_id,
            sensor_family=sensor,
            request_fingerprint=fp,
            content_type="application/json",
            encoding="utf-8",
            raw_body=raw_bytes,
            content_hash=content_hash,
            schema_state=parsed.schema_state,
            retrieval_metadata={"http_status": status},
            evidence_ref=capability.probe_evidence_ref,
            adapter_version=self.adapter_version,
        )

        if not parsed.semantic_output_allowed:
            raise SchemaDrift(
                provider_id=self.provider_id,
                sensor_family=sensor,
                request_fingerprint=fp,
                evidence_ref=capability.probe_evidence_ref,
                raw_payload_envelope=envelope,
                detail=(
                    f"Deribit {sensor.value} schema state "
                    f"{parsed.schema_state.value} blocks parsed output; raw "
                    "payload preserved in the failure envelope"
                ),
            )

        rows = list(parsed.rows)
        quality_flags: list[QualityFlagAcquisition] = []
        if not rows:
            quality_flags.append(QualityFlagAcquisition.EMPTY_VALID)
        else:
            timestamps = [
                dt.timestamp()
                for r in rows
                if (dt := self._row_dt(r, sensor)) is not None
            ]
            if len(timestamps) != len({round(t, 6) for t in timestamps}):
                quality_flags.append(QualityFlagAcquisition.DUPLICATE_EDGE)

        actual_first = self._row_dt(rows[0], sensor) if rows else None
        actual_last = self._row_dt(rows[-1], sensor) if rows else None

        # ---- acquisition-completion truth (I07R1 doctrine + I08R1 seal) ----
        # BOOK_SNAPSHOT is CURRENT_ONLY: a single current-snapshot acquisition
        # unit is complete by definition — the request never promises a
        # historical window, so the snapshot page satisfies it.
        if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            is_complete = True
        else:
            # COVERAGE truth comes from the schema-validated SOURCE-page
            # timestamps (`parsed.coverage_timestamps`), NOT from the projected
            # semantic rows (I08R1 Defect C): for LIQUIDATION the semantic view
            # is a filtered subset (only forced-liquidation events), and a
            # filtered subset must never manufacture completeness from a
            # narrower projection than the acquisition surface used to prove
            # it.  Coverage timestamps are validated exact epoch-ms ints; a
            # member that still fails to convert is an internal invariant
            # violation and FAILS CLOSED.
            coverage_datetimes = [
                dt
                for ts in parsed.coverage_timestamps
                if (dt := _ms_int_to_dt(ts)) is not None
            ]
            if len(coverage_datetimes) != len(parsed.coverage_timestamps):
                raise ProviderSemanticError(
                    provider_id=self.provider_id,
                    sensor_family=sensor,
                    request_fingerprint=fp,
                    detail=(
                        "internal invariant violation: a schema-validated "
                        "source timestamp produced no convenience datetime; "
                        "refusing to classify window completion"
                    ),
                )
            has_in_window = any(
                request.start_time <= dt < request.end_time
                for dt in coverage_datetimes
            )
            all_in_window = all(
                request.start_time <= dt < request.end_time
                for dt in coverage_datetimes
            )

            if sensor is SensorFamily.MECHANICAL_FUNDING:
                # FUNDING terminal/exhaustive semantics are NOT established by
                # committed evidence (I08R1 Defect B): the "short page under
                # the count cap is exhaustive" rule exists only as a
                # characterization heuristic (probe._pagination_state) and no
                # committed artifact proves get_funding_rate_history returns
                # ALL window records whenever len(result) < count.  Fail
                # closed: completion_proof = LIMITED, funding is NEVER
                # certified complete here.
                is_complete = False
            else:
                # TRADE / LIQUIDATION: `has_more == false` is the provider-
                # native terminal flag for the CURRENT REQUEST WINDOW
                # (characterization pagination contract + committed result
                # envelope).  Completion additionally requires non-empty
                # semantic output, at least one coverage row in-window, and
                # FULL source coverage inside the requested window.
                terminal = parsed.has_more is False
                is_complete = bool(
                    rows
                    and has_in_window
                    and all_in_window
                    and terminal
                )

            # COMPLETE can never also be PARTIAL (I08R1 Defect A): quality
            # flags are assigned AFTER the completion decision.  PARTIAL and
            # GAP remain mutually exclusive; an empty page is EMPTY_VALID
            # (never GAP merely from an empty default response).
            if rows and not is_complete:
                if has_in_window:
                    quality_flags.append(QualityFlagAcquisition.PARTIAL_INTERVAL)
                else:
                    quality_flags.append(QualityFlagAcquisition.GAP_DETECTED)

        return FetchBatch(
            provider_id=self.provider_id,
            sensor_family=sensor,
            native_instrument_id=request.native_instrument_id,
            request_fingerprint=fp,
            requested_start=request.start_time,
            requested_end=request.end_time,
            actual_first_timestamp=actual_first,
            actual_last_timestamp=actual_last,
            raw_payloads=[envelope],
            row_count=len(rows),
            next_resume_token=None,  # continuation beyond one window: LIMITED
            is_complete=is_complete,
            http_status=status,
            retrieved_at=self._now(),
            quality_flags=quality_flags,
            adapter_version=self.adapter_version,
        )

    def _row_dt(self, row: dict[str, Any], sensor: SensorFamily) -> datetime | None:
        """FetchBatch convenience datetime from the native epoch-ms int."""
        if sensor is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            return _ms_int_to_dt(row.get("timestamp"))
        # funding + trade + liquidation rows all carry `timestamp` (epoch ms).
        return _ms_int_to_dt(row.get("timestamp"))
