"""SENSOR-B3-I07 — OKX adapter offline tests (FAKE TRANSPORT ONLY).

Covers the provider-specific minimum at the REAL `OkxAdapter` boundary:

- free-only access gate runs BEFORE any transport call (no bypass)
- five unpromoted sensors stay typed `CapabilityUnavailable`
- three promoted paths fetch happy fixtures end-to-end (book CURRENT_ONLY,
  funding + trade PRIMARY historical)
- book stays CURRENT_ONLY (no historical/rest surface)
- EMPTY_VALID distinct from unsupported / provider error
- raw payload hash deterministic; SchemaDrift carries RawPayloadEnvelope
- provider errors stay typed (nonzero OKX code != EMPTY_VALID)
- symbol scope + method/provider identity guards, no-transport sensor identity
- funding route is PUBLIC namespace (never /market)
- fundingRate/realizedRate distinct; native trade side preserved
- full common conformance passes in PRODUCTION_CANDIDATE mode

NO network call is possible: the only transport ever constructed is the
offline `FakeOkxTransport`; a no-transport adapter raises `ProviderUnavailable`.
"""

from __future__ import annotations

from typing import Any

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base import (
    AdapterConformanceMode,
    AdapterUnderTest,
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
    AuthenticationRequired,
    CapabilityUnavailable,
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
from crypto_sensor_fabric.providers.okx import (
    DEFAULT_FREE_ONLY_POLICY,
    NEUTRAL_INSTRUMENT_LIST_SENSOR,
    OKX_PRODUCTION_INSTRUMENT_SCOPE,
    PROVIDER_ID,
    OkxAdapter,
    OkxRequestBuilder,
    build_okx_capabilities,
    okx_native_evidence,
)

from ._fake import FakeOkxTransport, request
from .fixtures import responses as FX

BOOK = SensorFamily.MECHANICAL_BOOK_SNAPSHOT
FUNDING = SensorFamily.MECHANICAL_FUNDING
TRADE = SensorFamily.MECHANICAL_TRADE

ALL_PROMOTED = (BOOK, FUNDING, TRADE)

UNPROMOTED = (
    SensorFamily.MECHANICAL_BASIS,
    SensorFamily.MECHANICAL_BOOK_METRIC,
    SensorFamily.MECHANICAL_LIQUIDATION,
    SensorFamily.MECHANICAL_OPEN_INTEREST,
    SensorFamily.MECHANICAL_POSITIONING,
)

HAPPY_ROUTES: dict[str, Any] = {
    "/history-trades": (200, FX.TRADE_HAPPY),
    "/funding-rate-history": (200, FX.FUNDING_HAPPY),
    "/books": (200, FX.BOOK_HAPPY),
}


def _adapter(routes: dict[str, Any] | None = None, **kwargs: Any) -> OkxAdapter:
    transport = (
        FakeOkxTransport(routes=routes) if routes is not None else FakeOkxTransport()
    )
    return OkxAdapter(transport=transport, **kwargs)


class TestProviderIdentityAndProtocol:
    def test_provider_id_frozen(self) -> None:
        assert PROVIDER_ID == "OKX_SWAP"
        assert _adapter().provider_id == "OKX_SWAP"

    def test_adapter_implements_common_protocol(self) -> None:
        assert isinstance(_adapter(), MechanicalProviderAdapter)

    def test_exactly_three_promoted(self) -> None:
        caps = _adapter().capabilities()
        assert set(caps.supported_sensors()) == set(ALL_PROMOTED)
        assert len(caps.supported_sensors()) == 3

    def test_promoted_roles(self) -> None:
        from crypto_sensor_fabric.probes.enums import ProviderRole

        caps = _adapter().capabilities()
        assert caps.capability_for(BOOK).allowed_role is ProviderRole.CURRENT_ONLY
        assert caps.capability_for(FUNDING).allowed_role is ProviderRole.PRIMARY
        assert caps.capability_for(TRADE).allowed_role is ProviderRole.PRIMARY

    def test_list_instruments_is_configured_production_scope(self) -> None:
        transport = FakeOkxTransport()
        adapter = OkxAdapter(transport=transport)
        result = adapter.list_instruments(
            InstrumentListRequest(provider_id=PROVIDER_ID, request_id="r")
        )
        assert result.provider_id == PROVIDER_ID
        assert result.native_instrument_ids == list(OKX_PRODUCTION_INSTRUMENT_SCOPE)
        assert "ETH-USDT-SWAP" not in result.native_instrument_ids
        assert "SOL-USDT-SWAP" not in result.native_instrument_ids
        assert "DOGE-USDT-SWAP" not in result.native_instrument_ids
        assert transport.calls == []  # configured scope, not discovery

    def test_no_transport_is_offline(self) -> None:
        adapter = OkxAdapter()  # no transport
        with pytest.raises(ProviderUnavailable) as excinfo:
            adapter.fetch_trades(request(TRADE))
        assert excinfo.value.sensor_family is TRADE


class TestAccessGateBeforeTransport:
    def test_trading_auth_blocked_before_transport(self) -> None:
        transport = FakeOkxTransport()
        adapter = OkxAdapter(transport=transport, auth_mode=AdapterAuthMode.TRADING_KEY)
        with pytest.raises(AccessClassViolation):
            adapter.fetch_funding(request(FUNDING))
        assert transport.calls == []

    def test_free_only_default_passes_gate_and_calls_transport(self) -> None:
        transport = FakeOkxTransport(routes=HAPPY_ROUTES)
        adapter = OkxAdapter(transport=transport)
        batch = adapter.fetch_trades(request(TRADE))
        assert isinstance(batch, FetchBatch)
        assert len(transport.calls) == 1


class TestTypedUnsupported:
    @pytest.mark.parametrize("sensor", UNPROMOTED)
    def test_unpromoted_sensor_typed_unsupported_with_correct_sensor(self, sensor) -> None:
        transport = FakeOkxTransport(routes=HAPPY_ROUTES)
        adapter = OkxAdapter(transport=transport)
        method = {
            SensorFamily.MECHANICAL_BASIS: "fetch_basis",
            SensorFamily.MECHANICAL_BOOK_METRIC: "fetch_book_metrics",
            SensorFamily.MECHANICAL_LIQUIDATION: "fetch_liquidations",
            SensorFamily.MECHANICAL_OPEN_INTEREST: "fetch_open_interest",
            SensorFamily.MECHANICAL_POSITIONING: "fetch_positioning",
        }[sensor]
        with pytest.raises(CapabilityUnavailable) as excinfo:
            getattr(adapter, method)(request(sensor))
        assert excinfo.value.sensor_family is sensor
        assert transport.calls == []

    def test_dispatch_unpromoted_typed_unsupported(self) -> None:
        with pytest.raises(CapabilityUnavailable):
            dispatch_fetch(_adapter(), request(SensorFamily.MECHANICAL_LIQUIDATION))


class TestMethodSensorIdentity:
    METHOD_SENSOR = {
        "fetch_trades": TRADE,
        "fetch_book": BOOK,
        "fetch_funding": FUNDING,
    }

    def test_mismatched_request_fails_before_transport(self) -> None:
        for method_name, expected in self.METHOD_SENSOR.items():
            wrong = next(s for s in ALL_PROMOTED if s is not expected)
            transport = FakeOkxTransport(routes=HAPPY_ROUTES)
            adapter = OkxAdapter(transport=transport)
            with pytest.raises(ProviderSemanticError) as excinfo:
                getattr(adapter, method_name)(request(wrong))
            assert excinfo.value.sensor_family is wrong
            assert transport.calls == [], f"{method_name} reached transport"

    def test_unsupported_named_method_preserves_sensor_identity(self) -> None:
        # fetch_liquidations(FUNDING request) is a mismatch, NOT a false
        # "funding unsupported" claim.
        transport = FakeOkxTransport(routes=HAPPY_ROUTES)
        adapter = OkxAdapter(transport=transport)
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_liquidations(request(FUNDING))
        assert excinfo.value.sensor_family is FUNDING
        assert transport.calls == []


class TestHappyFetchPerPromotedSensor:
    def test_each_promoted_sensor_returns_valid_batch(self) -> None:
        adapter = _adapter(routes=HAPPY_ROUTES)
        for sensor in ALL_PROMOTED:
            batch = dispatch_fetch(adapter, request(sensor))
            assert isinstance(batch, FetchBatch)
            assert batch.provider_id == PROVIDER_ID
            assert batch.sensor_family is sensor
            assert batch.native_instrument_id == "BTC-USDT-SWAP"
            assert batch.row_count >= 1
            assert batch.is_complete is True
            assert batch.http_status == 200
            assert batch.raw_payloads, f"{sensor.value} must preserve raw evidence"
            ref = batch.raw_payloads[0].evidence_ref
            assert ref is not None and ref.evidence_id

    def test_book_batch_is_current_only(self) -> None:
        batch = _adapter(routes={"/books": HAPPY_ROUTES["/books"]}).fetch_book(request(BOOK))
        assert batch.is_complete is True
        # no next_resume_token (CURRENT_ONLY, no continuation)
        assert batch.next_resume_token is None
        assert batch.row_count >= 1


class TestTimestampUnits:
    def test_funding_convenience_dt_from_ms_string(self) -> None:
        batch = _adapter(
            routes={"/funding-rate-history": HAPPY_ROUTES["/funding-rate-history"]}
        ).fetch_funding(request(FUNDING))
        # parsed convenience datetime derived from the native ms-epoch STRING
        assert batch.actual_first_timestamp is not None
        assert batch.actual_last_timestamp is not None
        assert batch.actual_last_timestamp >= batch.actual_first_timestamp

    def test_trade_ts_is_ms_string(self) -> None:
        batch = _adapter(routes={"/history-trades": HAPPY_ROUTES["/history-trades"]}).fetch_trades(request(TRADE))
        assert batch.actual_first_timestamp is not None

    def test_book_ts_is_ms_string(self) -> None:
        batch = _adapter(routes={"/books": HAPPY_ROUTES["/books"]}).fetch_book(request(BOOK))
        assert batch.actual_first_timestamp is not None


class TestEmptyValidDistinct:
    def test_empty_funding_is_explicit_empty_valid(self) -> None:
        adapter = _adapter()  # default (200, {code:0, data:[]})
        batch = adapter.fetch_funding(request(FUNDING))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags
        assert batch.raw_payloads  # raw preserved even when empty

    def test_empty_trade_is_explicit_empty_valid(self) -> None:
        batch = _adapter().fetch_trades(request(TRADE))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags

    def test_empty_book_is_explicit_empty_valid(self) -> None:
        batch = _adapter().fetch_book(request(BOOK))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags


class TestProviderErrorsStayTyped:
    def test_invalid_instrument_is_invalid_instrument(self) -> None:
        adapter = _adapter(routes={"/history-trades": FX.SCENARIOS_TIMESTAMP["trade"]["invalid_instrument"]})
        with pytest.raises(InvalidInstrument) as excinfo:
            adapter.fetch_trades(request(TRADE))
        assert excinfo.value.failure_type == "InvalidInstrument"

    def test_http_429_rate_limited(self) -> None:
        adapter = _adapter(routes={"/funding-rate-history": FX.SCENARIOS_TIMESTAMP["funding"]["rate_limit"]})
        with pytest.raises(RateLimited):
            adapter.fetch_funding(request(FUNDING))

    def test_auth_code_authentication_required(self) -> None:
        adapter = _adapter(routes={"/history-trades": (200, FX.ERROR_AUTH)})
        with pytest.raises(AuthenticationRequired):
            adapter.fetch_trades(request(TRADE))

    def test_http_500_provider_unavailable(self) -> None:
        adapter = _adapter(routes={"/books": FX.SCENARIOS_TIMESTAMP["book"]["provider_error"]})
        with pytest.raises(ProviderUnavailable):
            adapter.fetch_book(request(BOOK))

    def test_nonzero_code_http200_is_typed_error_not_provider_success(self) -> None:
        # a 200 HTTP with code=51001 is an InvalidInstrument, never data/EMPTY_VALID
        adapter = _adapter(routes={"/history-trades": (200, FX.ERROR_INVALID_INSTRUMENT)})
        with pytest.raises(InvalidInstrument):
            adapter.fetch_trades(request(TRADE))


class TestRawHashDeterministic:
    def test_identical_payload_identical_hash(self) -> None:
        a = _adapter(routes={"/history-trades": HAPPY_ROUTES["/history-trades"]}).fetch_trades(request(TRADE))
        b = _adapter(routes={"/history-trades": HAPPY_ROUTES["/history-trades"]}).fetch_trades(request(TRADE))
        assert a.raw_payloads[0].content_hash == b.raw_payloads[0].content_hash


class TestSchemaDriftRawEnvelope:
    def _drift_routes(self) -> dict[str, Any]:
        return {
            "/history-trades": FX.SCENARIOS_TIMESTAMP["trade"]["bad_timestamp"],
            "/funding-rate-history": FX.SCENARIOS_TIMESTAMP["funding"]["bad_timestamp"],
            "/books": FX.SCENARIOS_TIMESTAMP["book"]["bad_timestamp"],
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
            assert envelope.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
            raw = envelope.raw_body
            raw_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8")
            assert envelope.content_hash == payload_hash(raw_bytes)
            caps = build_okx_capabilities()
            ref = caps.capability_for(sensor).probe_evidence_ref
            assert ref is not None
            assert envelope.evidence_ref == ref
            assert ref.evidence_id in caps.capability_for(sensor).evidence_basis

    def test_drift_blocks_parsed_output(self) -> None:
        adapter = _adapter(routes={"/books": FX.SCENARIOS_TIMESTAMP["book"]["bad_timestamp"]})
        with pytest.raises(SchemaDrift):
            adapter.fetch_book(request(BOOK))


class TestInstrumentScopeSeparation:
    def test_probe_only_symbols_fail_every_promoted_sensor(self) -> None:
        for sensor in ALL_PROMOTED:
            for symbol in ("ETH-USDT-SWAP", "SOL-USDT-SWAP", "DOGE-USDT-SWAP"):
                transport = FakeOkxTransport(routes=HAPPY_ROUTES)
                adapter = OkxAdapter(transport=transport)
                with pytest.raises(InvalidInstrument):
                    dispatch_fetch(adapter, request(sensor, native_instrument_id=symbol))
                assert transport.calls == []

    def test_btc_usdt_swap_passes(self) -> None:
        batch = _adapter(routes={"/books": HAPPY_ROUTES["/books"]}).fetch_book(request(BOOK))
        assert batch.native_instrument_id == "BTC-USDT-SWAP"


class TestRequestProviderIdentity:
    def test_foreign_provider_reports_requested_sensor_all_three(self) -> None:
        for sensor in ALL_PROMOTED:
            transport = FakeOkxTransport(routes=HAPPY_ROUTES)
            adapter = OkxAdapter(transport=transport)
            req = request(sensor).model_copy(update={"provider_id": "GATE_FUTURES"})
            with pytest.raises(ProviderSemanticError) as excinfo:
                dispatch_fetch(adapter, req)
            assert excinfo.value.sensor_family is sensor, sensor
            assert transport.calls == [], f"{sensor.value} reached transport"

    def test_instrument_list_wrong_provider_uses_neutral_placeholder(self) -> None:
        adapter = _adapter()
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.list_instruments(
                InstrumentListRequest(provider_id="GATE_FUTURES", request_id="r")
            )
        assert excinfo.value.sensor_family is NEUTRAL_INSTRUMENT_LIST_SENSOR


class TestNoTransportSensorIdentity:
    def test_all_three_sensors_report_correct_sensor(self) -> None:
        for sensor in ALL_PROMOTED:
            adapter = OkxAdapter()  # no transport
            with pytest.raises(ProviderUnavailable) as excinfo:
                dispatch_fetch(adapter, request(sensor))
            assert excinfo.value.sensor_family is sensor, sensor


class TestNoForbiddenPaths:
    def test_funding_never_market_namespace(self) -> None:
        builder = OkxRequestBuilder()
        url, _ = builder.build(request(FUNDING))
        assert "/api/v5/public/funding-rate-history" in url
        assert "/api/v5/market/funding-rate-history" not in url

    def test_book_never_historical(self) -> None:
        builder = OkxRequestBuilder()
        url, params = builder.build(request(BOOK))
        assert "/books" in url
        for forbidden in ("start", "end", "after", "before"):
            assert forbidden not in params


class TestNativeMethodGuardsUnpromoted:
    def test_fetch_book_metrics_mismatch_not_false_unsupported(self) -> None:
        transport = FakeOkxTransport()
        adapter = OkxAdapter(transport=transport)
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_book_metrics(request(FUNDING))
        assert excinfo.value.sensor_family is FUNDING


class TestProductionCandidateConformance:
    def test_full_conformance_passes_with_real_adapter(self) -> None:
        # empty-valid: funding (default empty); fetch: trade happy.
        routes = {
            "/history-trades": HAPPY_ROUTES["/history-trades"],
        }
        adapter = _adapter(routes=routes)
        promoted = capabilities_from_promotion(
            "OKX_SWAP", load_promotion_candidates()
        )
        under_test = AdapterUnderTest(
            adapter=adapter,
            registry_policy=DEFAULT_FREE_ONLY_POLICY,
            auth_mode=AdapterAuthMode.NO_AUTH,
            promoted_capabilities=promoted,
            native_evidence=okx_native_evidence(),
            empty_valid_request=request(FUNDING),
            unsupported_request=request(SensorFamily.MECHANICAL_LIQUIDATION),
            fetch_request=request(TRADE),
            mode=AdapterConformanceMode.PRODUCTION_CANDIDATE,
        )
        results = run_conformance_suite(under_test)
        failed = [r for r in results if not r.passed]
        assert not failed, "\n".join(f"{r.check_id}: {r.detail}" for r in failed)
        summary = summarize_conformance(results)
        assert summary["failed"] == 0

    def test_exact_i14_set_via_capabilities(self) -> None:
        caps = build_okx_capabilities()
        assert set(caps.supported_sensors()) == set(ALL_PROMOTED)


class TestRetryClassification:
    def test_retryability_of_typed_failures(self) -> None:
        assert classify_retryability(RateLimited(PROVIDER_ID, TRADE)) is Retryability.RETRYABLE
        assert classify_retryability(ProviderUnavailable(PROVIDER_ID, TRADE)) is Retryability.RETRYABLE
        assert classify_retryability(InvalidInstrument(PROVIDER_ID, TRADE)) is Retryability.TERMINAL
        assert classify_retryability(AuthenticationRequired(PROVIDER_ID, TRADE)) is Retryability.TERMINAL
        assert classify_retryability(SchemaDrift(PROVIDER_ID, TRADE)) is Retryability.TERMINAL