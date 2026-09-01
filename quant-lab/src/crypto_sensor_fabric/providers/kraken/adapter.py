"""Kraken Futures production adapter (SENSOR-B3-I05).

Implements the common `MechanicalProviderAdapter` for KRAKEN_FUTURES using ONLY
the six MECHANICAL Market Analytics paths promoted by I14
(`source_promotion_candidates.yaml`).  MECHANICAL_TRADE and MECHANICAL_BOOK_SNAPSHOT
are NOT promoted: they remain typed `CapabilityUnavailable`.

This is an ACQUISITION BOUNDARY.  It preserves raw provider evidence (in a
`RawPayloadEnvelope` with a content hash), provider identity, native instrument
and native analytic fields/units.  It never performs canonical unit conversion,
cross-venue CVD, liquidation/funding/positioning state or any research compute.

Transport is injected (dependency injection) — standard tests use a FAKE
transport; NO network calls are made by this adapter's default path.  The
free-only access gate runs BEFORE any transport call.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Callable, NoReturn

from ...contracts.access import FreeOnlyPolicy
from ...contracts.enums import AccessClass, SensorFamily
from ..base.access import assert_free_only_access
from ..base.enums import (
    AdapterAuthMode,
    PaginationMode,
    QualityFlagAcquisition,
    SchemaState,
)
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
    ResumeToken,
)
from ..base.schema import SchemaAssessment
from .capabilities import (
    KRAKEN_PRODUCTION_INSTRUMENT_SCOPE,
    PROVIDER_ID,
    build_kraken_capabilities,
)
from .errors import is_kraken_error_body, map_kraken_error
from .parsers import parse_kraken_analytics
from .requests import KrakenAnalyticsRequestBuilder

#: Neutral provider-level sensor placeholder for InstrumentListRequest identity
#: failures ONLY (SENSOR-B3-I05R2 Repair 1).
#:
#: Instrument discovery is a provider-level scope, not a SensorFamily, so a
#: foreign InstrumentListRequest has no requested sensor to report.  The fabric
#: error model forces a SensorFamily placeholder on every AcquisitionError and
#: the frozen Bloc 1 schema (contracts/enums.py) defines no provider-level
#: member (adding one is a schema-breaking change out of scope here).  Per the
#: operator instruction we therefore RETAIN an explicit neutral placeholder for
#: this single provider-level case and document that it implies NO scientific
#: sensor meaning.  A foreign *FetchRequest* NEVER uses this placeholder — it
#: always reports the REQUESTED sensor.
NEUTRAL_INSTRUMENT_LIST_SENSOR = SensorFamily.MECHANICAL_OPEN_INTEREST


# Default free-only registry policy for KRAKEN_FUTURES (Bloc 1 F9).
DEFAULT_FREE_ONLY_POLICY = FreeOnlyPolicy(
    access_class=AccessClass.FREE_AUTOMATED,
    cost_usd_required=0,
    payment_method_required=False,
    staking_required=False,
    transaction_required=False,
)

#: Transport signature: (url, params) -> (http_status_or_None, parsed_body).
TransportFn = Callable[[str, dict[str, int]], tuple[int | None, Any]]


def _epoch_to_dt(value: Any, *, milliseconds: bool = False) -> datetime | None:
    """Coerce a native analytics bucket timestamp to UTC (convenience only).

    Units are SENSOR-SPECIFIC on the live Market Analytics family (I10R1
    adjudication, BLOC_03_I10R1_STRUCTURAL_ADJUDICATION.json): most analytics
    types emit epoch SECONDS, but MECHANICAL_FUNDING emits epoch MILLISECONDS
    (13-digit; I10 proved seconds-class values would NOT overflow the converter
    while funding returned NULL convenience timestamps).  The raw native int is
    never replaced; this only affects the FetchBatch convenience datetime.  No
    magnitude heuristic rescues an out-of-validity value (a wrong-unit value
    yields None).
    """
    if not isinstance(value, (int, float)):
        return None
    seconds = (float(value) / 1000.0) if milliseconds else float(value)
    try:
        return datetime.fromtimestamp(seconds, tz=UTC)
    except (OverflowError, ValueError, OSError):
        return None


def _funding_is_milliseconds(sensor: SensorFamily) -> bool:
    """True for the only analytics sensor whose live timestamps are epoch ms."""
    return sensor is SensorFamily.MECHANICAL_FUNDING


class KrakenAdapter:
    """Production Kraken Futures adapter (six promoted Market Analytics paths)."""

    provider_id = PROVIDER_ID

    def __init__(
        self,
        transport: TransportFn | None = None,
        *,
        free_only_policy: FreeOnlyPolicy | None = None,
        auth_mode: AdapterAuthMode = AdapterAuthMode.NO_AUTH,
        promotion_candidates: list[dict[str, object]] | None = None,
        adapter_version: str = "kraken-adapter-v2",
        now: Callable[[], datetime] | None = None,
    ) -> None:
        # No transport -> the adapter stays OFFLINE: a fetch with no injected
        # transport raises typed ProviderUnavailable naming the REQUESTED
        # sensor (never a hard-coded placeholder sensor).
        self._transport = transport
        self._policy = free_only_policy or DEFAULT_FREE_ONLY_POLICY
        self._auth_mode = auth_mode
        self._caps = build_kraken_capabilities(promotion_candidates)
        self._builder = KrakenAnalyticsRequestBuilder()
        self.adapter_version = adapter_version
        self._now = now or (lambda: datetime.now(UTC))

    # ---- protocol ---------------------------------------------------------
    def capabilities(self) -> ProviderCapabilities:
        return self._caps

    def list_instruments(self, request: InstrumentListRequest) -> InstrumentListResult:
        # Provider identity is part of the request contract (SENSOR-B3-I05R1).
        # A foreign InstrumentListRequest has NO requested sensor; it fails with
        # the neutral provider-level placeholder (never a real sensor).
        if request.provider_id != PROVIDER_ID:
            self._raise_wrong_provider(
                request.provider_id, NEUTRAL_INSTRUMENT_LIST_SENSOR
            )
        # Configured PRODUCTION evidence scope (evidence-backed union), NOT
        # live provider discovery and NOT the probe universe: PI_SOLUSD /
        # PI_DOGEUSD stay probe-only (see capabilities).
        return InstrumentListResult(
            provider_id=self.provider_id,
            native_instrument_ids=list(KRAKEN_PRODUCTION_INSTRUMENT_SCOPE),
            retrieved_at=self._now(),
        )

    def fetch_trades(self, request: FetchRequest) -> FetchBatch:
        # Method identity is checked FIRST (SENSOR-B3-I05R2 Repair 2): a
        # non-TRADE request must NOT be reported as an unsupported surface.
        # fetch_trades(FUNDING) is a method/sensor mismatch (ProviderSemanticError),
        # NOT a claim that FUNDING is unsupported.  Only once the request is a
        # genuine MECHANICAL_TRADE request does the typed CapabilityUnavailable
        # (TRADE is not promoted) surface.
        self._require_sensor(request.sensor_family, SensorFamily.MECHANICAL_TRADE)
        self._raise_unsupported(request.sensor_family)

    def fetch_book(self, request: FetchRequest) -> FetchBatch:
        # Same fail-closed method/sensor identity as fetch_trades, for the
        # BOOK_SNAPSHOT surface.
        self._require_sensor(
            request.sensor_family, SensorFamily.MECHANICAL_BOOK_SNAPSHOT
        )
        self._raise_unsupported(request.sensor_family)

    def fetch_liquidations(self, request: FetchRequest) -> FetchBatch:
        return self._fetch(request, SensorFamily.MECHANICAL_LIQUIDATION)

    def fetch_open_interest(self, request: FetchRequest) -> FetchBatch:
        return self._fetch(request, SensorFamily.MECHANICAL_OPEN_INTEREST)

    def fetch_funding(self, request: FetchRequest) -> FetchBatch:
        return self._fetch(request, SensorFamily.MECHANICAL_FUNDING)

    def fetch_basis(self, request: FetchRequest) -> FetchBatch:
        return self._fetch(request, SensorFamily.MECHANICAL_BASIS)

    def fetch_positioning(self, request: FetchRequest) -> FetchBatch:
        return self._fetch(request, SensorFamily.MECHANICAL_POSITIONING)

    def fetch_book_metrics(self, request: FetchRequest) -> FetchBatch:
        return self._fetch(request, SensorFamily.MECHANICAL_BOOK_METRIC)

    # ---- helpers ----------------------------------------------------------
    def _raise_unsupported(self, sensor: SensorFamily) -> NoReturn:
        raise CapabilityUnavailable(
            provider_id=self.provider_id,
            sensor_family=sensor,
            detail=(
                f"{sensor.value} is NOT a promoted Kraken production path "
                "(I14 source_promotion_candidates.yaml); typed unsupported"
            ),
        )

    def _raise_wrong_provider(
        self, declared: str, sensor_family: SensorFamily
    ) -> NoReturn:
        """Foreign-provider rejection carrying the ACTUAL requested sensor.

        A rejected `FetchRequest.provider_id != KRAKEN_FUTURES` reports its own
        `request.sensor_family` so the diagnostic never mis-attributes which
        surface was requested (SENSOR-B3-I05R2 Repair 1).  Instrument-list
        discovery passes the documented neutral provider-level placeholder.
        """
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
        """Named protocol method / request sensor identity (SENSOR-B3-I05R1).

        `fetch_funding` requires a MECHANICAL_FUNDING request, etc.  A mismatch
        fails typed BEFORE transport — the named method is itself a contract.
        """
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

        # 2. request provider identity MUST match the adapter (R2): a
        #    KRAKEN_FUTURES adapter never executes a foreign-provider request.
        if request.provider_id != self.provider_id:
            self._raise_wrong_provider(request.provider_id, request.sensor_family)

        capability = self._caps.capability_for(sensor)
        if not capability.supported:
            self._raise_unsupported(sensor)

        # FREE-ONLY ACCESS GATE MUST RUN BEFORE ANY TRANSPORT CALL.
        assert_free_only_access(
            self.provider_id, self._policy, self._auth_mode, sensor_family=sensor
        )

        # 3. sensor-specific PRODUCTION symbol scope (R1): the sensor is
        #    supported but this native instrument must be proven for IT.
        if capability.symbol_scope and request.native_instrument_id not in capability.symbol_scope:
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
        #    any transport call.
        url, params = self._builder.build(request)
        fp = fingerprint_request(
            request, self._builder.endpoint_family(sensor), params
        )

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
            raise map_kraken_error(
                self.provider_id, sensor, body, status, request_fingerprint=fp
            )
        if is_kraken_error_body(body):
            raise map_kraken_error(
                self.provider_id, sensor, body, status if status is not None else 200,
                request_fingerprint=fp,
            )

        parsed = parse_kraken_analytics(body, sensor)
        assessment: SchemaAssessment | None = parsed.assessment
        semantic_ok = parsed.semantic_output_allowed

        # MATERIALIZE the immutable raw acquisition artifact BEFORE the parse
        # decision (SENSOR-B3-I05R1): the envelope exists even when the schema
        # is BREAKING/UNKNOWN, so the failure path carries the exact preserved
        # raw body, hash, provider, sensor, fingerprint and retrieval metadata.
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

        if not semantic_ok:
            # BREAKING / UNKNOWN: raw evidence is PRESERVED (typed envelope
            # attachment on the failure); parsed semantic output BLOCKED.
            raise SchemaDrift(
                provider_id=self.provider_id,
                sensor_family=sensor,
                request_fingerprint=fp,
                evidence_ref=capability.probe_evidence_ref,
                raw_payload_envelope=envelope,
                detail=(
                    f"Kraken {sensor.value} analytics schema state "
                    f"{parsed.schema_state.value} blocks parsed output; raw "
                    "payload preserved in the failure envelope"
                ),
            )

        rows = list(parsed.rows)
        quality_flags: list[QualityFlagAcquisition] = []
        if not rows:
            quality_flags.append(QualityFlagAcquisition.EMPTY_VALID)
        if assessment is not None and assessment.state is SchemaState.ADDITIVE_SCHEMA_CHANGE:
            quality_flags.append(QualityFlagAcquisition.SCHEMA_ADDITIVE)

        # Row timestamps are already schema-validated to EXACT int epoch
        # seconds (SENSOR-B3-I05R2).  No silent `int()` rescue / isinstance
        # filter is needed: every row here is a strict int, so resume/non-
        # monotonic derive only from already-validated native timestamps.
        numeric_ts = [r["timestamp"] for r in rows]
        if _is_non_monotonic(numeric_ts):
            quality_flags.append(QualityFlagAcquisition.NON_MONOTONIC_TIMESTAMPS)

        # Convenience datetimes are sensor-unit-aware (funding = epoch ms,
        # siblings = epoch seconds); the raw native ints stay preserved.
        actual_first = (
            _epoch_to_dt(rows[0]["timestamp"], milliseconds=_funding_is_milliseconds(sensor))
            if rows
            else None
        )
        actual_last = (
            _epoch_to_dt(rows[-1]["timestamp"], milliseconds=_funding_is_milliseconds(sensor))
            if rows
            else None
        )

        next_resume: ResumeToken | None = None
        if parsed.more and rows:
            oldest = min(r["timestamp"] for r in rows)
            prior_page = request.resume_token.page_number if request.resume_token else 0
            next_resume = ResumeToken(
                mode=PaginationMode.TIME_RANGE,
                page_number=prior_page + 1,
                provider_native_state={
                    "since": oldest,
                    "symbol": request.native_instrument_id,
                },
            )
        is_complete = not parsed.more

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
            next_resume_token=next_resume,
            is_complete=is_complete,
            http_status=status,
            retrieved_at=self._now(),
            quality_flags=quality_flags,
            adapter_version=self.adapter_version,
        )


def _is_non_monotonic(values: list[Any]) -> bool:
    """True when numeric timestamps decrease anywhere (acquisition quality flag)."""
    previous: int | float | None = None
    for value in values:
        if previous is not None and value < previous:
            return True
        previous = value
    return False