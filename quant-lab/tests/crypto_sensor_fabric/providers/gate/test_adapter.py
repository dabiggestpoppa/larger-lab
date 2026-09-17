"""SENSOR-B3-I06 — Gate adapter offline tests (FAKE TRANSPORT ONLY).

Covers the provider-specific minimum at the REAL `GateAdapter` boundary:

- free-only access gate runs BEFORE any transport call (no bypass)
- MECHANICAL_TRADE / MECHANICAL_BOOK_SNAPSHOT stay typed `CapabilityUnavailable`
- four promoted paths fetch happy fixtures end-to-end (all SECONDARY)
- request/response timestamp units stay distinct (contract_stats `time` epoch
  SECONDS current contract — I05-era ms sample was synthetic (prior
  characterization error, I10R2); funding `t` / from-to seconds)
- EMPTY_VALID distinct from unsupported / retention
- 180-day retention maps to `HistoricalRangeUnavailable` (never EMPTY_VALID)
- raw payload hash deterministic; SchemaDrift carries RawPayloadEnvelope
- provider errors stay typed; symbol scope + method/provider identity guards
- NO private `/positions` and NO plural `/funding_rates` can be produced
- full common conformance suite passes in PRODUCTION_CANDIDATE mode

NO network call is possible: the only transport ever constructed is the
offline `FakeGateTransport`, and a no-transport adapter raises
`ProviderUnavailable` instead of fabricating a network path.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base import (
    AdapterUnderTest,
    AdapterConformanceMode,
    capabilities_from_promotion,
    classify_retryability,
    dispatch_fetch,
    load_promotion_candidates,
    payload_hash,
    run_conformance_suite,
    summarize_conformance,
)
from crypto_sensor_fabric.providers.base.enums import (
    AdapterAuthMode,
    QualityFlagAcquisition,
    Retryability,
    SchemaState,
)
from crypto_sensor_fabric.providers.base.errors import (
    AccessClassViolation,
    CapabilityUnavailable,
    HistoricalRangeUnavailable,
    InvalidInstrument,
    ProviderSemanticError,
    ProviderUnavailable,
    RateLimited,
    SchemaDrift,
)
from crypto_sensor_fabric.providers.base.models import (
    FetchBatch,
    InstrumentListRequest,
)
from crypto_sensor_fabric.providers.base.protocol import MechanicalProviderAdapter
from crypto_sensor_fabric.providers.gate import (
    DEFAULT_FREE_ONLY_POLICY,
    GATE_PRODUCTION_INSTRUMENT_SCOPE,
    NEUTRAL_INSTRUMENT_LIST_SENSOR,
    PROVIDER_ID,
    GateAdapter,
    GateRequestBuilder,
    build_gate_capabilities,
    gate_native_evidence,
)

from ._fake import FakeGateTransport, request
from .fixtures import responses as FX

CONTRACT_STATS = SensorFamily.MECHANICAL_OPEN_INTEREST
HAPPY_ROUTES: dict[str, Any] = {
    "/contract_stats": FX.CONTRACT_STATS_SCENARIOS["open_interest"]["happy"],
    "/funding_rate": FX.FUNDING_SCENARIOS["happy"],
}
ALL_PROMOTED = (
    SensorFamily.MECHANICAL_FUNDING,
    SensorFamily.MECHANICAL_LIQUIDATION,
    SensorFamily.MECHANICAL_OPEN_INTEREST,
    SensorFamily.MECHANICAL_POSITIONING,
)


def _adapter(routes: dict[str, Any] | None = None, **kwargs: Any) -> GateAdapter:
    transport = FakeGateTransport(routes=routes) if routes is not None else FakeGateTransport()
    return GateAdapter(transport=transport, **kwargs)


class TestProviderIdentityAndProtocol:
    def test_provider_id_frozen(self) -> None:
        assert PROVIDER_ID == "GATE_FUTURES"
        assert _adapter().provider_id == "GATE_FUTURES"

    def test_adapter_implements_common_protocol(self) -> None:
        assert isinstance(_adapter(), MechanicalProviderAdapter)

    def test_exactly_four_promoted(self) -> None:
        caps = _adapter().capabilities()
        assert set(caps.supported_sensors()) == set(ALL_PROMOTED)
        assert len(caps.supported_sensors()) == 4

    def test_list_instruments_is_configured_production_scope(self) -> None:
        transport = FakeGateTransport()
        adapter = GateAdapter(transport=transport)
        result = adapter.list_instruments(
            InstrumentListRequest(provider_id=PROVIDER_ID, request_id="r")
        )
        assert result.provider_id == PROVIDER_ID
        assert result.native_instrument_ids == list(GATE_PRODUCTION_INSTRUMENT_SCOPE)
        assert "ETH_USDT" not in result.native_instrument_ids
        assert "SOL_USDT" not in result.native_instrument_ids
        assert transport.calls == []  # configured scope, not discovery

    def test_no_transport_is_offline(self) -> None:
        adapter = GateAdapter()  # no transport
        with pytest.raises(ProviderUnavailable) as excinfo:
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_FUNDING


class TestAccessGateBeforeTransport:
    def test_trading_auth_blocked_before_transport(self) -> None:
        transport = FakeGateTransport()
        adapter = GateAdapter(transport=transport, auth_mode=AdapterAuthMode.TRADING_KEY)
        with pytest.raises(AccessClassViolation):
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert transport.calls == []

    def test_free_only_default_passes_gate_and_calls_transport(self) -> None:
        transport = FakeGateTransport(routes=HAPPY_ROUTES)
        adapter = GateAdapter(transport=transport)
        batch = adapter.fetch_open_interest(request(CONTRACT_STATS))
        assert isinstance(batch, FetchBatch)
        assert len(transport.calls) == 1


class TestTypedUnsupported:
    def test_fetch_trades_typed_unsupported_with_correct_sensor(self) -> None:
        transport = FakeGateTransport(routes=HAPPY_ROUTES)
        adapter = GateAdapter(transport=transport)
        with pytest.raises(CapabilityUnavailable) as excinfo:
            adapter.fetch_trades(request(SensorFamily.MECHANICAL_TRADE))
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_TRADE
        assert transport.calls == []

    def test_fetch_trades_mismatch_is_semantic_error_not_unsupported(self) -> None:
        transport = FakeGateTransport(routes=HAPPY_ROUTES)
        adapter = GateAdapter(transport=transport)
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_trades(request(SensorFamily.MECHANICAL_FUNDING))
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_FUNDING
        assert transport.calls == []

    def test_fetch_book_book_snapshot_typed_unsupported(self) -> None:
        transport = FakeGateTransport(routes=HAPPY_ROUTES)
        adapter = GateAdapter(transport=transport)
        with pytest.raises(CapabilityUnavailable) as excinfo:
            adapter.fetch_book(request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT))
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT
        assert transport.calls == []

    def test_fetch_book_mismatch_is_semantic_error_not_unsupported(self) -> None:
        transport = FakeGateTransport(routes=HAPPY_ROUTES)
        adapter = GateAdapter(transport=transport)
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_book(request(SensorFamily.MECHANICAL_FUNDING))
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_FUNDING
        assert transport.calls == []

    def test_dispatch_trade_typed_unsupported(self) -> None:
        with pytest.raises(CapabilityUnavailable):
            dispatch_fetch(_adapter(), request(SensorFamily.MECHANICAL_TRADE))


class TestHappyFetchPerPromotedSensor:
    def test_each_promoted_sensor_returns_valid_batch(self) -> None:
        adapter = _adapter(routes=HAPPY_ROUTES)
        for sensor in ALL_PROMOTED:
            batch = dispatch_fetch(adapter, request(sensor))
            assert isinstance(batch, FetchBatch)
            assert batch.provider_id == PROVIDER_ID
            assert batch.sensor_family is sensor
            assert batch.native_instrument_id == "BTC_USDT"
            assert batch.row_count >= 1
            # Completion is LIMITED for every Gate path (frozen I09 matrix
            # authority): runtime never manufactures is_complete=True and never
            # invents a resume token (SENSOR-B3-I10R2).
            assert batch.is_complete is False
            assert batch.next_resume_token is None
            assert batch.http_status == 200
            assert batch.raw_payloads, f"{sensor.value} must preserve raw evidence"
            ref = batch.raw_payloads[0].evidence_ref
            assert ref is not None and ref.evidence_id

    def test_shared_contract_stats_stays_separate_sensors(self) -> None:
        # same physical /contract_stats payload projected per sensor
        adapter = _adapter(routes={"/contract_stats": HAPPY_ROUTES["/contract_stats"]})
        oi = adapter.fetch_open_interest(request(CONTRACT_STATS))
        liq = adapter.fetch_liquidations(request(SensorFamily.MECHANICAL_LIQUIDATION))
        pos = adapter.fetch_positioning(request(SensorFamily.MECHANICAL_POSITIONING))
        assert oi.sensor_family is SensorFamily.MECHANICAL_OPEN_INTEREST
        assert liq.sensor_family is SensorFamily.MECHANICAL_LIQUIDATION
        assert pos.sensor_family is SensorFamily.MECHANICAL_POSITIONING
        # raw envelope is the same physical payload for all three
        assert oi.raw_payloads[0].content_hash == liq.raw_payloads[0].content_hash
        assert oi.raw_payloads[0].content_hash == pos.raw_payloads[0].content_hash


class TestTimestampUnits:
    def test_contract_stats_time_is_epoch_seconds(self) -> None:
        adapter = _adapter(routes={"/contract_stats": HAPPY_ROUTES["/contract_stats"]})
        batch = adapter.fetch_open_interest(request(CONTRACT_STATS))
        # current contract: native `time` is epoch SECONDS (I10R1 adjudication
        # — exact hourly bucket alignment verified live; see
        # BLOC_03_I10R1_STRUCTURAL_ADJUDICATION.json).  Convenience datetime
        # derived directly from the seconds value, raw int preserved.
        assert batch.actual_first_timestamp == datetime.fromtimestamp(1755000000, tz=UTC)
        assert batch.actual_last_timestamp == datetime.fromtimestamp(1755003600, tz=UTC)

    def test_old_millisecond_form_value_is_not_rescued(self) -> None:
        # An epoch-MILLISECOND-form value (the I05-era unit) is OUT of validity
        # for the current seconds contract: the convenience datetime is
        # un-derivable (years beyond year-9999 -> None) and must NOT be
        # magnitude-rescued (no `if value > 1e12: /1000` heuristic).  The raw
        # native int stays preserved in the parsed view.
        from .fixtures import responses as FX

        stale_row = {**FX.contract_stats_row(), "time": 1755000000000}
        adapter = _adapter(routes={"/contract_stats": (200, [stale_row])})
        batch = adapter.fetch_open_interest(request(CONTRACT_STATS))
        assert batch.row_count == 1
        assert batch.actual_first_timestamp is None
        assert batch.actual_last_timestamp is None
        assert batch.raw_payloads  # raw preserved regardless
        # native value preserved verbatim in the parsed row view
        assert batch.raw_payloads[0].raw_body is not None

    def test_funding_t_is_epoch_seconds(self) -> None:
        adapter = _adapter(routes={"/funding_rate": HAPPY_ROUTES["/funding_rate"]})
        batch = adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert batch.actual_first_timestamp == datetime.fromtimestamp(1755000000, tz=UTC)


class TestEmptyValidDistinct:
    def test_funding_empty_is_explicit_empty_valid(self) -> None:
        adapter = _adapter()  # default (200, [])
        batch = adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags
        assert batch.raw_payloads  # raw preserved even when empty

    def test_contract_stats_empty_is_empty_valid(self) -> None:
        adapter = _adapter()
        batch = adapter.fetch_open_interest(request(CONTRACT_STATS))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags


class TestRetention:
    def test_180_day_rejection_is_historical_range_unavailable(self) -> None:
        adapter = _adapter(
            routes={"/contract_stats": FX.CONTRACT_STATS_SCENARIOS["open_interest"]["retention"]}
        )
        with pytest.raises(HistoricalRangeUnavailable) as excinfo:
            adapter.fetch_open_interest(request(CONTRACT_STATS))
        err = excinfo.value
        assert classify_retryability(err) is Retryability.TERMINAL

    def test_retention_is_not_empty_valid(self) -> None:
        # retention raises HistoricalRangeUnavailable, never an EMPTY_VALID batch
        adapter = _adapter(
            routes={"/funding_rate": FX.FUNDING_SCENARIOS["retention"]}
        )
        with pytest.raises(HistoricalRangeUnavailable):
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))

    def test_retention_is_not_unsupported_nor_auth(self) -> None:
        adapter = _adapter(
            routes={"/contract_stats": FX.CONTRACT_STATS_SCENARIOS["positioning"]["retention"]}
        )
        with pytest.raises(HistoricalRangeUnavailable):
            adapter.fetch_positioning(request(SensorFamily.MECHANICAL_POSITIONING))


class TestProviderErrorsStayTyped:
    def test_invalid_contract_is_invalid_instrument(self) -> None:
        adapter = _adapter(
            routes={"/contract_stats": FX.CONTRACT_STATS_SCENARIOS["open_interest"]["invalid_contract"]}
        )
        with pytest.raises(InvalidInstrument) as excinfo:
            adapter.fetch_open_interest(request(CONTRACT_STATS))
        assert excinfo.value.failure_type == "InvalidInstrument"

    def test_http_429_rate_limited(self) -> None:
        adapter = _adapter(routes={"/funding_rate": FX.FUNDING_SCENARIOS["rate_limit"]})
        with pytest.raises(RateLimited):
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))

    def test_http_500_provider_unavailable(self) -> None:
        adapter = _adapter(routes={"/contract_stats": FX.CONTRACT_STATS_SCENARIOS["open_interest"]["provider_error"]})
        with pytest.raises(ProviderUnavailable):
            adapter.fetch_open_interest(request(CONTRACT_STATS))


class TestRawHashDeterministic:
    def test_identical_payload_identical_hash(self) -> None:
        a = _adapter(routes={"/contract_stats": HAPPY_ROUTES["/contract_stats"]}).fetch_open_interest(request(CONTRACT_STATS))
        b = _adapter(routes={"/contract_stats": HAPPY_ROUTES["/contract_stats"]}).fetch_open_interest(request(CONTRACT_STATS))
        assert a.raw_payloads[0].content_hash == b.raw_payloads[0].content_hash


class TestSchemaDriftRawEnvelope:
    def _drift_routes(self) -> dict[str, Any]:
        return {
            "/contract_stats": FX.CONTRACT_STATS_SCENARIOS["open_interest"]["drift"],
            "/funding_rate": FX.FUNDING_SCENARIOS["bad_t"],
        }

    def test_each_promoted_sensor_drift_carries_raw_envelope(self) -> None:
        adapter = _adapter(routes=self._drift_routes())
        for sensor in ALL_PROMOTED:
            with pytest.raises(SchemaDrift) as excinfo:
                dispatch_fetch(adapter, request(sensor))
            err = excinfo.value
            envelope = err.raw_payload_envelope
            assert envelope is not None, f"{sensor.value} drift lost the raw envelope"
            assert envelope.provider_id == PROVIDER_ID
            assert envelope.sensor_family is sensor
            assert envelope.request_fingerprint
            assert envelope.schema_state in (
                SchemaState.BREAKING_SCHEMA_CHANGE,
                SchemaState.UNKNOWN_SCHEMA,
            )
            raw = envelope.raw_body
            raw_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8")
            assert envelope.content_hash == payload_hash(raw_bytes)
            caps = build_gate_capabilities()
            ref = caps.capability_for(sensor).probe_evidence_ref
            assert ref is not None
            assert envelope.evidence_ref == ref
            assert ref.evidence_id in caps.capability_for(sensor).evidence_basis

    def test_missing_required_field_breaks_with_envelope(self) -> None:
        adapter = _adapter(
            routes={"/contract_stats": FX.CONTRACT_STATS_SCENARIOS["open_interest"]["missing_field"]}
        )
        with pytest.raises(SchemaDrift) as excinfo:
            adapter.fetch_open_interest(request(CONTRACT_STATS))
        envelope = excinfo.value.raw_payload_envelope
        assert envelope is not None
        assert envelope.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE


class TestInstrumentScopeSeparation:
    def test_probe_only_symbols_fail_every_promoted_sensor(self) -> None:
        for sensor in ALL_PROMOTED:
            for symbol in ("ETH_USDT", "SOL_USDT", "DOGE_USDT"):
                transport = FakeGateTransport(routes=HAPPY_ROUTES)
                adapter = GateAdapter(transport=transport)
                with pytest.raises(InvalidInstrument):
                    dispatch_fetch(adapter, request(sensor, native_instrument_id=symbol))
                assert transport.calls == []

    def test_btc_usdt_passes(self) -> None:
        adapter = _adapter(routes={"/contract_stats": HAPPY_ROUTES["/contract_stats"]})
        batch = adapter.fetch_open_interest(request(CONTRACT_STATS))
        assert batch.native_instrument_id == "BTC_USDT"


class TestRequestProviderIdentity:
    def test_foreign_provider_reports_requested_sensor_all_four(self) -> None:
        for sensor in ALL_PROMOTED:
            transport = FakeGateTransport(routes=HAPPY_ROUTES)
            adapter = GateAdapter(transport=transport)
            req = request(sensor).model_copy(update={"provider_id": "OKX_SWAP"})
            with pytest.raises(ProviderSemanticError) as excinfo:
                dispatch_fetch(adapter, req)
            assert excinfo.value.sensor_family is sensor, sensor
            assert transport.calls == [], f"{sensor.value} reached transport"

    def test_instrument_list_wrong_provider_uses_neutral_placeholder(self) -> None:
        adapter = _adapter()
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.list_instruments(
                InstrumentListRequest(provider_id="OKX_SWAP", request_id="r")
            )
        assert excinfo.value.sensor_family is NEUTRAL_INSTRUMENT_LIST_SENSOR


class TestMethodSensorIdentity:
    METHODS = {
        "fetch_funding": SensorFamily.MECHANICAL_FUNDING,
        "fetch_liquidations": SensorFamily.MECHANICAL_LIQUIDATION,
        "fetch_open_interest": SensorFamily.MECHANICAL_OPEN_INTEREST,
        "fetch_positioning": SensorFamily.MECHANICAL_POSITIONING,
    }

    def test_mismatched_request_fails_before_transport(self) -> None:
        for method_name, expected in self.METHODS.items():
            wrong = next(s for s in ALL_PROMOTED if s is not expected)
            transport = FakeGateTransport(routes=HAPPY_ROUTES)
            adapter = GateAdapter(transport=transport)
            with pytest.raises(ProviderSemanticError) as excinfo:
                getattr(adapter, method_name)(request(wrong))
            assert excinfo.value.sensor_family is wrong
            assert transport.calls == [], f"{method_name} reached transport"


class TestNoTransportSensorIdentity:
    def test_all_four_sensors_report_correct_sensor(self) -> None:
        for sensor in ALL_PROMOTED:
            adapter = GateAdapter()  # no transport
            with pytest.raises(ProviderUnavailable) as excinfo:
                dispatch_fetch(adapter, request(sensor))
            assert excinfo.value.sensor_family is sensor, sensor


class TestNoForbiddenRawPaths:
    def test_no_private_positions_in_any_production_request(self) -> None:
        builder = GateRequestBuilder()
        for sensor in ALL_PROMOTED:
            url, _ = builder.build(request(sensor))
            assert "/positions" not in url, sensor
            assert "positions" not in url.lower(), sensor

    def test_no_plural_funding_rates_in_production(self) -> None:
        builder = GateRequestBuilder()
        url, _ = builder.build(request(SensorFamily.MECHANICAL_FUNDING))
        assert "funding_rates" not in url  # only single GET /funding_rate


class TestLimitedCompletion:
    """Gate completion truth (SENSOR-B3-I10R2): runtime matches the frozen
    I09 LIMITED/LIMITED authority.

    is_complete is ALWAYS False (never manufactured), next_resume_token is
    always None, and nonempty pages carry truthful overlap flags —
    PARTIAL_INTERVAL when rows intersect [start, end), GAP_DETECTED when
    entirely outside, EMPTY_VALID on empty (mirrors the OKX/Deribit pattern).
    """

    #: Fixture rows sit at 2025-08-12T12:00:00Z and 13:00:00Z (1755000000 /
    #: 1755003600 epoch seconds).
    _WINDOW_START = datetime(2025, 8, 12, 11, 0, tzinfo=UTC)
    _WINDOW_END = datetime(2025, 8, 12, 14, 0, tzinfo=UTC)

    def test_contract_stats_overlap_is_partial_interval(self) -> None:
        adapter = _adapter(routes={"/contract_stats": HAPPY_ROUTES["/contract_stats"]})
        batch = adapter.fetch_open_interest(
            request(
                SensorFamily.MECHANICAL_OPEN_INTEREST,
                start=self._WINDOW_START,
                end=self._WINDOW_END,
            )
        )
        assert batch.is_complete is False
        assert batch.next_resume_token is None
        assert batch.row_count == 2
        assert QualityFlagAcquisition.PARTIAL_INTERVAL in batch.quality_flags
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags

    def test_contract_stats_rows_outside_request_is_gap_detected(self) -> None:
        # Default request window 2026-01-01T00:00..01:00; fixture rows are
        # 2025-08-12 — entirely outside the requested window.
        adapter = _adapter(routes={"/contract_stats": HAPPY_ROUTES["/contract_stats"]})
        batch = adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert batch.is_complete is False
        assert batch.next_resume_token is None
        assert batch.row_count == 2
        assert QualityFlagAcquisition.GAP_DETECTED in batch.quality_flags
        assert QualityFlagAcquisition.PARTIAL_INTERVAL not in batch.quality_flags

    def test_contract_stats_empty_is_empty_valid_not_complete(self) -> None:
        adapter = _adapter(
            routes={"/contract_stats": FX.CONTRACT_STATS_SCENARIOS["open_interest"]["empty"]}
        )
        batch = adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert batch.is_complete is False
        assert batch.next_resume_token is None
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags
        assert QualityFlagAcquisition.PARTIAL_INTERVAL not in batch.quality_flags
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags

    def test_funding_overlap_is_partial_interval_not_complete(self) -> None:
        adapter = _adapter(routes={"/funding_rate": FX.FUNDING_SCENARIOS["happy"]})
        batch = adapter.fetch_funding(
            request(
                SensorFamily.MECHANICAL_FUNDING,
                start=self._WINDOW_START,
                end=self._WINDOW_END,
            )
        )
        assert batch.is_complete is False
        assert batch.next_resume_token is None
        assert batch.row_count == 1
        assert QualityFlagAcquisition.PARTIAL_INTERVAL in batch.quality_flags

    def test_funding_empty_is_empty_valid_not_complete(self) -> None:
        adapter = _adapter(routes={"/funding_rate": FX.FUNDING_SCENARIOS["empty"]})
        batch = adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert batch.is_complete is False
        assert batch.next_resume_token is None
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags


class TestProductionCandidateConformance:
    def test_full_conformance_passes_with_real_adapter(self) -> None:
        # empty-valid: funding (default empty list); fetch: open-interest happy.
        routes = {
            "/funding_rate": FX.FUNDING_SCENARIOS["empty"],
            "/contract_stats": HAPPY_ROUTES["/contract_stats"],
        }
        adapter = _adapter(routes=routes)
        promoted = capabilities_from_promotion(
            "GATE_FUTURES", load_promotion_candidates()
        )
        under_test = AdapterUnderTest(
            adapter=adapter,
            registry_policy=DEFAULT_FREE_ONLY_POLICY,
            auth_mode=AdapterAuthMode.NO_AUTH,
            promoted_capabilities=promoted,
            native_evidence=gate_native_evidence(),
            empty_valid_request=request(SensorFamily.MECHANICAL_FUNDING),
            unsupported_request=request(SensorFamily.MECHANICAL_TRADE),
            fetch_request=request(SensorFamily.MECHANICAL_OPEN_INTEREST),
            mode=AdapterConformanceMode.PRODUCTION_CANDIDATE,
        )
        results = run_conformance_suite(under_test)
        failed = [r for r in results if not r.passed]
        assert not failed, "\n".join(f"{r.check_id}: {r.detail}" for r in failed)
        summary = summarize_conformance(results)
        assert summary["failed"] == 0

    def test_exact_i14_set_via_capabilities(self) -> None:
        caps = build_gate_capabilities()
        assert set(caps.supported_sensors()) == set(ALL_PROMOTED)

    def test_all_roles_secondary_at_adapter_boundary(self) -> None:
        from crypto_sensor_fabric.probes.enums import ProviderRole

        caps = _adapter().capabilities()
        for sensor in caps.supported_sensors():
            assert caps.capability_for(sensor).allowed_role is ProviderRole.SECONDARY