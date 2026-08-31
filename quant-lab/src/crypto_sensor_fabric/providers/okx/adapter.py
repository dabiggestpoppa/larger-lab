"""OKX Swap production adapter (SENSOR-B3-I07).

Implements the common `MechanicalProviderAdapter` for OKX_SWAP using ONLY the
three paths promoted by I14 (`source_promotion_candidates.yaml`):

    MECHANICAL_BOOK_SNAPSHOT  (CURRENT_ONLY — current-only surface, no history)
    MECHANICAL_FUNDING        (PRIMARY — historical funding records)
    MECHANICAL_TRADE          (PRIMARY — historical raw trade events)

Everything else OKX might offer is typed `CapabilityUnavailable` under the
CURRENT I14 freeze:

    MECHANICAL_BASIS, MECHANICAL_BOOK_METRIC, MECHANICAL_LIQUIDATION,
    MECHANICAL_OPEN_INTEREST, MECHANICAL_POSITIONING

VIOLATIONS HERE ARE FORBIDDEN:

- BOOK_SNAPSHOT stays CURRENT_ONLY: no `start`/`end`/`after`/`before`, no
  historical cursor, no replay, no REST_RANGE — even though newer OKX docs may
  advertise historical book products (that is queued future research, not I07).
- Funding uses only the PUBLIC `/api/v5/public/funding-rate-history` namespace
  (NEVER `/api/v5/market/funding-rate-history`); the funding interval is NOT
  frozen to "8h"; fundingRate vs realizedRate stay distinct; no annualization.
- Trade uses `/api/v5/market/history-trades` with provider-native after/before
  cursor semantics kept SEPARATE from funding; `side` is preserved verbatim
  (never reinterpreted into strategy direction); no CVD / order-flow state.
- The public traderecords daily-zip archive is Bloc 2 characterization ONLY —
  it is never substituted as a production REST path, and it never extends the
  frozen I14 verified-history boundary.

This is an ACQUISITION BOUNDARY.  It preserves raw provider evidence (in a
`RawPayloadEnvelope` with a content hash), provider identity, native instrument
and native fields/units.  It never performs canonical unit conversion,
cross-venue synthesis, or research compute.

Transport is injected (dependency injection) — standard tests use a FAKE
transport; NO network calls are made.  The free-only access gate runs BEFORE
any transport call.  OKX v5 timestamps are millisecond-epoch STRINGS; they are
validated strictly (no silent coercion) and preserved natively.
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
    OKX_PRODUCTION_INSTRUMENT_SCOPE,
    PROVIDER_ID,
    build_okx_capabilities,
)
from .errors import is_okx_error_body, map_okx_error
from .parsers import parse_okx_book, parse_okx_funding, parse_okx_trades
from .requests import OkxRequestBuilder

# Default free-only registry policy for OKX_SWAP (Bloc 1 F9).
DEFAULT_FREE_ONLY_POLICY = FreeOnlyPolicy(
    access_class=AccessClass.FREE_AUTOMATED,
    cost_usd_required=0,
    payment_method_required=False,
    staking_required=False,
    transaction_required=False,
)

#: Neutral provider-level sensor placeholder for InstrumentListRequest identity
#: failures (same pattern sealed for Kraken/Gate in SENSOR-B3-I05R2).  Instrument
#: discovery has no requested sensor; the frozen SensorFamily enum defines no
#: provider-level member, so this explicit placeholder is used ONLY for
#: InstrumentListRequest and NEVER claims a scientific sensor.
NEUTRAL_INSTRUMENT_LIST_SENSOR = SensorFamily.MECHANICAL_TRADE

#: Transport signature: (url, params) -> (http_status_or_None, parsed_body).
TransportFn = Callable[[str, dict[str, Any]], tuple[int | None, Any]]


def _ms_str_to_dt(value: Any) -> datetime | None:
    """Derive a UTC convenience datetime AFTER a validated ms-epoch STRING.

    Evidence basis: OKX timestamps are millisecond-epoch strings (probe
    `sensor_units` + 09 schema fingerprint: `ts`/`fundingTime` as `str`).
    No precision is invented: only a numeric-string ms epoch is converted.
    """
    if not isinstance(value, str) or not value.isdigit():
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (OverflowError, ValueError, OSError):
        return None


class OkxAdapter:
    """Production OKX Swap adapter (three promoted paths)."""

    provider_id = PROVIDER_ID

    def __init__(
        self,
        transport: TransportFn | None = None,
        *,
        free_only_policy: FreeOnlyPolicy | None = None,
        auth_mode: AdapterAuthMode = AdapterAuthMode.NO_AUTH,
        promotion_candidates: list[dict[str, object]] | None = None,
        adapter_version: str = "okx-adapter-v1",
        now: Callable[[], datetime] | None = None,
    ) -> None:
        # No transport -> the adapter stays OFFLINE: a fetch with no injected
        # transport raises typed ProviderUnavailable naming the REQUESTED
        # sensor.
        self._transport = transport
        self._policy = free_only_policy or DEFAULT_FREE_ONLY_POLICY
        self._auth_mode = auth_mode
        self._caps = build_okx_capabilities(promotion_candidates)
        self._builder = OkxRequestBuilder()
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
        # live provider discovery and NOT the probe universe: ETH / SOL / DOGE
        # stay probe-only (see capabilities).
        return InstrumentListResult(
            provider_id=self.provider_id,
            native_instrument_ids=list(OKX_PRODUCTION_INSTRUMENT_SCOPE),
            retrieved_at=self._now(),
        )

    def fetch_trades(self, request: FetchRequest) -> FetchBatch:
        # TRADE IS a promoted OKX path: method identity first, then route to
        # the supported acquisition (SENSOR-B3-I05R2 Repair 2 / I07 §18).
        self._require_sensor(request.sensor_family, SensorFamily.MECHANICAL_TRADE)
        return self._fetch(request, SensorFamily.MECHANICAL_TRADE)

    def fetch_book(self, request: FetchRequest) -> FetchBatch:
        # BOOK_SNAPSHOT IS a promoted OKX path: method identity first, then the
        # current-only snapshot acquisition.
        self._require_sensor(
            request.sensor_family, SensorFamily.MECHANICAL_BOOK_SNAPSHOT
        )
        return self._fetch(request, SensorFamily.MECHANICAL_BOOK_SNAPSHOT)

    def fetch_funding(self, request: FetchRequest) -> FetchBatch:
        return self._fetch(request, SensorFamily.MECHANICAL_FUNDING)

    # ---- unsupported surfaces (typed CapabilityUnavailable) ----------------
    def fetch_liquidations(self, request: FetchRequest) -> FetchBatch:
        self._require_sensor(
            request.sensor_family, SensorFamily.MECHANICAL_LIQUIDATION
        )
        self._raise_unsupported(request.sensor_family)

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
                f"{sensor.value} is NOT a promoted OKX production path under "
                "CURRENT I14 (source_promotion_candidates.yaml); typed "
                "unsupported — a queued OKX capability must not broaden I07"
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
        #    any transport call.
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
            raise map_okx_error(
                self.provider_id, sensor, body, status, request_fingerprint=fp
            )
        if is_okx_error_body(body):
            raise map_okx_error(
                self.provider_id, sensor, body, status if status is not None else 200,
                request_fingerprint=fp,
            )

        if sensor is SensorFamily.MECHANICAL_FUNDING:
            parsed = parse_okx_funding(body, symbol=request.native_instrument_id)
        elif sensor is SensorFamily.MECHANICAL_TRADE:
            parsed = parse_okx_trades(body)
        else:  # BOOK_SNAPSHOT
            parsed = parse_okx_book(body)

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
                    f"OKX {sensor.value} schema state "
                    f"{parsed.schema_state.value} blocks parsed output; raw "
                    "payload preserved in the failure envelope"
                ),
            )

        rows = list(parsed.rows)
        quality_flags: list[QualityFlagAcquisition] = []
        if not rows:
            quality_flags.append(QualityFlagAcquisition.EMPTY_VALID)
        else:
            # Annotate, never destructively remove, a repeated native cursor/
            # timestamp edge or exact duplicate within one page (raw preserved).
            timestamps = [self._row_dt(r, sensor).timestamp() for r in rows]
            timestamps = [t for t in timestamps if t is not None]
            if len(timestamps) != len({round(t, 6) for t in timestamps}):
                quality_flags.append(QualityFlagAcquisition.DUPLICATE_EDGE)

        actual_first = self._row_dt(rows[0], sensor) if rows else None
        actual_last = self._row_dt(rows[-1], sensor) if rows else None

        # Single evidence-backed production request window (instId+limit /
        # instId+sz).  Deeper after/before cursor traversal is UNRESOLVED by
        # committed I13 evidence (direction not proven), so no invented
        # continuation cursor is emitted — completion semantics are honest.
        is_complete = True

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
        """FetchBatch convenience datetime from the native ms-epoch string."""
        if sensor is SensorFamily.MECHANICAL_TRADE:
            return _ms_str_to_dt(row.get("ts"))
        if sensor is SensorFamily.MECHANICAL_FUNDING:
            return _ms_str_to_dt(row.get("fundingTime"))
        return _ms_str_to_dt(row.get("ts"))  # BOOK_SNAPSHOT