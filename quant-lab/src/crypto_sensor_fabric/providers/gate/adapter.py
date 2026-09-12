"""Gate Futures production adapter (SENSOR-B3-I06).

Implements the common `MechanicalProviderAdapter` for GATE_FUTURES using ONLY
the four MECHANICAL paths promoted by I14 (`source_promotion_candidates.yaml`):
MECHANICAL_FUNDING, MECHANICAL_LIQUIDATION, MECHANICAL_OPEN_INTEREST,
MECHANICAL_POSITIONING — all SECONDARY.  MECHANICAL_TRADE and
MECHANICAL_BOOK_SNAPSHOT are NOT promoted: they remain typed
`CapabilityUnavailable`.

VIOLATIONS HERE ARE FORBIDDEN:

- market-wide positioning NEVER uses the private `/positions` endpoint (the
  public `/contract_stats` surface is the only positioning source);
- the plural batch `POST /funding_rates` route is never used in production
  (promoted funding uses the single-contract public `GET /funding_rate`);
- no `to` parameter is invented for `/contract_stats`;
- OI / LIQUIDATION / POSITIONING share the physical `/contract_stats` payload
  but remain SEPARATE sensor contracts — no combined state is ever created.

This is an ACQUISITION BOUNDARY.  It preserves raw provider evidence (in a
`RawPayloadEnvelope` with a content hash), provider identity, native instrument
and native analytic fields/units.  It never performs canonical unit conversion,
cross-venue CVD, liquidation/funding/positioning state or any research compute.

Transport is injected (dependency injection) — standard tests use a FAKE
transport; NO network calls are made.  The free-only access gate runs BEFORE
any transport call.  A rolling ~180-day retention rejection is typed
`HistoricalRangeUnavailable` (never EMPTY_VALID / auth / unsupported).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Callable, NoReturn

from ...contracts.access import FreeOnlyPolicy
from ...contracts.enums import AccessClass, SensorFamily
from ..base.access import assert_free_only_access
from ..base.enums import AdapterAuthMode, QualityFlagAcquisition, SchemaState
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
    GATE_PRODUCTION_INSTRUMENT_SCOPE,
    PROVIDER_ID,
    build_gate_capabilities,
)
from .errors import is_gate_error_body, map_gate_error
from .parsers import parse_gate_contract_stats, parse_gate_funding
from .requests import GateRequestBuilder

# Default free-only registry policy for GATE_FUTURES (Bloc 1 F9).
DEFAULT_FREE_ONLY_POLICY = FreeOnlyPolicy(
    access_class=AccessClass.FREE_AUTOMATED,
    cost_usd_required=0,
    payment_method_required=False,
    staking_required=False,
    transaction_required=False,
)

#: Neutral provider-level sensor placeholder for InstrumentListRequest identity
#: failures (same pattern sealed for Kraken in SENSOR-B3-I05R2).  Instrument
#: discovery has no requested sensor; the frozen SensorFamily enum defines no
#: provider-level member, so this explicit placeholder is used ONLY for
#: InstrumentListRequest and NEVER claims a scientific sensor.
NEUTRAL_INSTRUMENT_LIST_SENSOR = SensorFamily.MECHANICAL_FUNDING

#: Transport signature: (url, params) -> (http_status_or_None, parsed_body).
#: Gate params mix native strings (contract, interval STRING bucket) and ints
#: (from/to/limit), so they are typed `dict[str, Any]`.
TransportFn = Callable[[str, dict[str, Any]], tuple[int | None, Any]]


def _dt_seconds(epoch_seconds: int | float) -> datetime | None:
    try:
        return datetime.fromtimestamp(float(epoch_seconds), tz=UTC)
    except (OverflowError, ValueError, OSError):
        return None


class GateAdapter:
    """Production Gate Futures adapter (four promoted paths, all SECONDARY)."""

    provider_id = PROVIDER_ID

    def __init__(
        self,
        transport: TransportFn | None = None,
        *,
        free_only_policy: FreeOnlyPolicy | None = None,
        auth_mode: AdapterAuthMode = AdapterAuthMode.NO_AUTH,
        promotion_candidates: list[dict[str, object]] | None = None,
        adapter_version: str = "gate-adapter-v2",
        now: Callable[[], datetime] | None = None,
    ) -> None:
        # No transport -> the adapter stays OFFLINE: a fetch with no injected
        # transport raises typed ProviderUnavailable naming the REQUESTED
        # sensor.
        self._transport = transport
        self._policy = free_only_policy or DEFAULT_FREE_ONLY_POLICY
        self._auth_mode = auth_mode
        self._caps = build_gate_capabilities(promotion_candidates)
        self._builder = GateRequestBuilder()
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
        # live provider discovery and NOT the probe universe: ETH/SOL/DOGE stay
        # probe-only (see capabilities).
        return InstrumentListResult(
            provider_id=self.provider_id,
            native_instrument_ids=list(GATE_PRODUCTION_INSTRUMENT_SCOPE),
            retrieved_at=self._now(),
        )

    def fetch_trades(self, request: FetchRequest) -> FetchBatch:
        # Method identity FIRST (SENSOR-B3-I05R2): a non-TRADE request is a
        # typed method/sensor mismatch, never a false "unsupported surface".
        self._require_sensor(request.sensor_family, SensorFamily.MECHANICAL_TRADE)
        self._raise_unsupported(request.sensor_family)

    def fetch_book(self, request: FetchRequest) -> FetchBatch:
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

    def fetch_positioning(self, request: FetchRequest) -> FetchBatch:
        return self._fetch(request, SensorFamily.MECHANICAL_POSITIONING)

    def fetch_basis(self, request: FetchRequest) -> FetchBatch:
        # BASIS is not a promoted Gate path; method identity is checked first so
        # a mismatched request is a typed error, never a false unsupported claim.
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
                f"{sensor.value} is NOT a promoted Gate production path "
                "(I14 source_promotion_candidates.yaml); typed unsupported"
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

        # 3. sensor-specific PRODUCTION symbol scope (I05R1 guard).
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
        #    any transport call.  No private /positions or plural funding_rates
        #    can ever be produced by the builder.
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
            raise map_gate_error(
                self.provider_id, sensor, body, status, request_fingerprint=fp
            )
        if is_gate_error_body(body):
            raise map_gate_error(
                self.provider_id,
                sensor,
                body,
                status if status is not None else 200,
                request_fingerprint=fp,
            )

        if sensor is SensorFamily.MECHANICAL_FUNDING:
            parsed = parse_gate_funding(body)
        else:
            parsed = parse_gate_contract_stats(body, sensor)

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
                    f"Gate {sensor.value} analytics schema state "
                    f"{parsed.schema_state.value} blocks parsed output; raw "
                    "payload preserved in the failure envelope"
                ),
            )

        rows = list(parsed.rows)
        quality_flags: list[QualityFlagAcquisition] = []
        if not rows:
            quality_flags.append(QualityFlagAcquisition.EMPTY_VALID)
        if (
            parsed.assessment is not None
            and parsed.assessment.state is SchemaState.ADDITIVE_SCHEMA_CHANGE
        ):
            quality_flags.append(QualityFlagAcquisition.SCHEMA_ADDITIVE)

        actual_first = self._row_dt(rows[0], sensor) if rows else None
        actual_last = self._row_dt(rows[-1], sensor) if rows else None

        # Completion is LIMITED for ALL four Gate paths (frozen I09 matrix:
        # resume=LIMITED, completion=LIMITED).  contract_stats has
        # from/interval/limit and NO `to` — deep traversal is UNRESOLVED;
        # funding_rate from/to has NO committed evidence of exhaustive
        # requested-window coverage.  Runtime must NOT manufacture stronger
        # completion than the frozen readiness authority, so is_complete is
        # always False with no invented resume token.  A truthful partial page
        # remains valid evidence: rows intersecting [start, end) carry
        # PARTIAL_INTERVAL, rows entirely outside it carry GAP_DETECTED, an
        # empty page is EMPTY_VALID (mirrors the OKX/Deribit LIMITED pattern).
        is_complete = False
        if rows:
            # Overlap truth comes from ACTUAL VALIDATED ROW TIMESTAMPS, never
            # from first/last ordering assumptions.  If ANY row yields no
            # convenience datetime (e.g. an out-of-validity unit like a
            # 13-digit ms value under the seconds contract), overlap cannot be
            # truthfully classified: no PARTIAL/GAP flag is added (the batch
            # keeps its raw native values and None conveniences, and the SMOKE
            # temporal-plausibility guard flags it — the adapter never invents
            # a unit or rescues a value).
            row_datetimes = [self._row_dt(r, sensor) for r in rows]
            if all(dt is not None for dt in row_datetimes):
                has_in_window = any(
                    request.start_time <= dt < request.end_time
                    for dt in row_datetimes
                    if dt is not None
                )
                quality_flags.append(
                    QualityFlagAcquisition.PARTIAL_INTERVAL
                    if has_in_window
                    else QualityFlagAcquisition.GAP_DETECTED
                )

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
            next_resume_token=None,
            is_complete=is_complete,
            http_status=status,
            retrieved_at=self._now(),
            quality_flags=quality_flags,
            adapter_version=self.adapter_version,
        )

    def _row_dt(self, row: dict[str, Any], sensor: SensorFamily) -> datetime | None:
        """FetchBatch convenience datetime from the native bucket timestamp.

        Units are endpoint-specific (request/response units are DIFFERENT):
        `contract_stats` rows carry `time` in native epoch SECONDS (current
        contract, live-verified I10/I10R1; the I05-era ms sample was a SYNTHETIC
        fixture — final adjudication A_PRIOR_CHARACTERIZATION_ERROR, historical
        real unit UNIDENTIFIED, see BLOC_03_I10R2_SEMANTIC_RECONCILIATION.json);
        `funding_rate` rows carry `t` in native epoch SECONDS.  The parsed
        native field is never replaced and NO magnitude heuristic rescues an
        out-of-validity value.
        """
        if sensor is SensorFamily.MECHANICAL_FUNDING:
            ts = row.get("t")
            if type(ts) is int:
                return _dt_seconds(ts)
            return None
        ts = row.get("time")
        if type(ts) is int:
            return _dt_seconds(ts)
        return None