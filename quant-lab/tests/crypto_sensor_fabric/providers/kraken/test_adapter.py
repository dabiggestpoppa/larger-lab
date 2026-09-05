"""SENSOR-B3-I05 — Kraken adapter offline tests (FAKE TRANSPORT ONLY).

Covers the provider-specific minimum at the REAL `KrakenAdapter` boundary:

- free-only access gate runs BEFORE any transport call (no bypass)
- MECHANICAL_TRADE / MECHANICAL_BOOK_SNAPSHOT stay typed `CapabilityUnavailable`
- six promoted Market Analytics paths fetch happy fixtures end-to-end
- epoch-second bucket units from evidence (never invented precision)
- EMPTY_VALID stays distinct from unsupported; ragged history preserved
- schema drift / malformed bodies block parsed output (SchemaDrift)
- provider error envelopes stay typed (InvalidInstrument / RateLimited /
  ProviderUnavailable / AccessClassViolation)
- raw payload hash is deterministic
- resume token round-trip re-issues `since` at the oldest bucket
- full common conformance suite passes in PRODUCTION_CANDIDATE mode

NO network call is possible: the only transport ever constructed is the
offline `FakeKrakenTransport`, and a no-transport adapter raises
`ProviderUnavailable` instead of fabricating a network path.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from crypto_sensor_fabric.contracts.access import FreeOnlyPolicy
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
    Granularity,
    PaginationMode,
    QualityFlagAcquisition,
    Retryability,
    SchemaState,
)
from crypto_sensor_fabric.providers.base.errors import (
    AccessClassViolation,
    CapabilityUnavailable,
    InvalidInstrument,
    ProviderSemanticError,
    ProviderUnavailable,
    RateLimited,
    SchemaDrift,
    UnsupportedGranularity,
)
from crypto_sensor_fabric.providers.base.models import (
    FetchBatch,
    InstrumentListRequest,
    RawPayloadEnvelope,
    ResumeToken,
)
from crypto_sensor_fabric.providers.base.protocol import MechanicalProviderAdapter
from crypto_sensor_fabric.providers.kraken import (
    DEFAULT_FREE_ONLY_POLICY,
    KRAKEN_PRODUCTION_INSTRUMENT_SCOPE,
    KRAKEN_PROBE_INSTRUMENT_SCOPE,
    KRAKEN_SYMBOL_SCOPES,
    NEUTRAL_INSTRUMENT_LIST_SENSOR,
    PROVIDER_ID,
    KrakenAdapter,
    KrakenAnalyticsRequestBuilder,
    build_kraken_capabilities,
    kraken_native_evidence,
)

from ._fake import FakeKrakenTransport, request
from .fixtures import analytics as FX

#: analytics-type URL fragment -> (http_status, body) fixture per promoted
#: sensor.  `FX.HAPPY[k]` is the full (status, body) pair; the fake transport
#: returns route values verbatim, so the adapter receives a real status int.
HAPPY_ROUTES: dict[str, Any] = {
    "/open-interest": FX.HAPPY["open_interest"],
    "/funding": FX.HAPPY["funding"],
    "/future-basis": FX.HAPPY["basis"],
    "/long-short-ratio": FX.HAPPY["positioning"],
    "/liquidation-volume": FX.HAPPY["liquidation"],
    "/orderbook": FX.HAPPY["book_metric"],
}

ALL_PROMOTED = (
    SensorFamily.MECHANICAL_BASIS,
    SensorFamily.MECHANICAL_BOOK_METRIC,
    SensorFamily.MECHANICAL_FUNDING,
    SensorFamily.MECHANICAL_LIQUIDATION,
    SensorFamily.MECHANICAL_OPEN_INTEREST,
    SensorFamily.MECHANICAL_POSITIONING,
)


def _adapter(routes: dict[str, Any] | None = None, **kwargs: Any) -> KrakenAdapter:
    transport = FakeKrakenTransport(routes=routes) if routes is not None else FakeKrakenTransport()
    return KrakenAdapter(transport=transport, **kwargs)


class TestProviderIdentityAndProtocol:
    def test_provider_id_frozen(self) -> None:
        assert PROVIDER_ID == "KRAKEN_FUTURES"
        assert _adapter().provider_id == "KRAKEN_FUTURES"

    def test_adapter_implements_common_protocol(self) -> None:
        assert isinstance(_adapter(), MechanicalProviderAdapter)

    def test_capabilities_provider_matches(self) -> None:
        caps = _adapter().capabilities()
        assert caps.provider_id == "KRAKEN_FUTURES"

    def test_list_instruments_is_configured_production_scope_no_discovery(self) -> None:
        transport = FakeKrakenTransport()
        adapter = KrakenAdapter(transport=transport)
        result = adapter.list_instruments(
            InstrumentListRequest(provider_id=PROVIDER_ID, request_id="r")
        )
        assert result.provider_id == PROVIDER_ID
        # configured PRODUCTION evidence scope only (no discovery endpoint);
        # probe-only SOL/DOGE are NOT exposed as production support
        assert result.native_instrument_ids == list(KRAKEN_PRODUCTION_INSTRUMENT_SCOPE)
        assert "PI_SOLUSD" not in result.native_instrument_ids
        assert "PI_DOGEUSD" not in result.native_instrument_ids
        # a configured native scope, NOT an invented discovery endpoint: the
        # transport is never consulted.
        assert transport.calls == []

    def test_no_transport_is_offline(self) -> None:
        adapter = KrakenAdapter()  # no transport injected
        with pytest.raises(ProviderUnavailable) as excinfo:
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_FUNDING


class TestAccessGateBeforeTransport:
    def test_trading_auth_blocked_before_transport(self) -> None:
        transport = FakeKrakenTransport()
        adapter = KrakenAdapter(transport=transport, auth_mode=AdapterAuthMode.TRADING_KEY)
        with pytest.raises(AccessClassViolation):
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert transport.calls == []  # gate MUST run before any transport call

    def test_unverified_policy_blocked_before_transport(self) -> None:
        transport = FakeKrakenTransport()
        adapter = KrakenAdapter(transport=transport, free_only_policy=FreeOnlyPolicy())
        with pytest.raises(AccessClassViolation):
            adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert transport.calls == []

    def test_free_only_default_passes_gate_and_calls_transport(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        batch = adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert isinstance(batch, FetchBatch)
        assert len(transport.calls) == 1


class TestTypedUnsupported:
    def test_fetch_trades_typed_unsupported(self) -> None:
        adapter = _adapter()
        with pytest.raises(CapabilityUnavailable) as excinfo:
            adapter.fetch_trades(request(SensorFamily.MECHANICAL_TRADE))
        assert excinfo.value.failure_type == "CapabilityUnavailable"

    def test_fetch_book_typed_unsupported(self) -> None:
        adapter = _adapter()
        with pytest.raises(CapabilityUnavailable):
            adapter.fetch_book(request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT))

    def test_dispatch_trade_typed_unsupported(self) -> None:
        adapter = _adapter()
        with pytest.raises(CapabilityUnavailable):
            dispatch_fetch(adapter, request(SensorFamily.MECHANICAL_TRADE))

    def test_dispatch_book_snapshot_typed_unsupported(self) -> None:
        adapter = _adapter()
        with pytest.raises(CapabilityUnavailable):
            dispatch_fetch(adapter, request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT))

    def test_unsupported_capabilities_never_declare_surface(self) -> None:
        caps = _adapter().capabilities()
        for sensor in (SensorFamily.MECHANICAL_TRADE, SensorFamily.MECHANICAL_BOOK_SNAPSHOT):
            cap = caps.capability_for(sensor)
            assert cap.supported is False
            assert cap.historical_mode is None


class TestHappyFetchPerPromotedSensor:
    def test_each_promoted_sensor_returns_valid_batch(self) -> None:
        adapter = _adapter(routes=HAPPY_ROUTES)
        for sensor in ALL_PROMOTED:
            batch = dispatch_fetch(adapter, request(sensor))
            assert isinstance(batch, FetchBatch)
            assert batch.provider_id == PROVIDER_ID
            assert batch.sensor_family is sensor
            assert batch.native_instrument_id == "PI_XBTUSD"
            assert batch.row_count >= 1
            assert batch.is_complete is True
            assert batch.next_resume_token is None
            assert batch.http_status == 200
            assert batch.raw_payloads, f"{sensor.value} must preserve raw evidence"
            assert batch.raw_payloads[0].evidence_ref is not None

    def test_funding_native_shape_preserved(self) -> None:
        batch = _adapter(routes=HAPPY_ROUTES).fetch_funding(
            request(SensorFamily.MECHANICAL_FUNDING)
        )
        # native provider values survive verbatim (never normalized/coerced)
        assert batch.row_count == 1
        # raw body preserved: content hash matches the deterministic hash of
        # the faithful textual form
        raw = batch.raw_payloads[0].raw_body
        raw_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8")
        assert batch.raw_payloads[0].content_hash == payload_hash(raw_bytes)

    def test_native_symbol_preserved_at_boundary(self) -> None:
        batch = _adapter(routes=HAPPY_ROUTES).fetch_open_interest(
            request(SensorFamily.MECHANICAL_OPEN_INTEREST, native_instrument_id="PI_ETHUSD")
        )
        assert batch.native_instrument_id == "PI_ETHUSD"


class TestEpochUnitBehavior:
    def test_bucket_timestamps_are_epoch_seconds(self) -> None:
        # 1755000000 is epoch SECONDS (2025-08-12T20:00:00Z).  If a parser
        # treated it as milliseconds the batch boundary would be absurd.
        batch = _adapter(routes=HAPPY_ROUTES).fetch_open_interest(
            request(SensorFamily.MECHANICAL_OPEN_INTEREST)
        )
        assert batch.actual_first_timestamp == datetime.fromtimestamp(1755000000, tz=UTC)
        assert batch.actual_last_timestamp == datetime.fromtimestamp(1755003600, tz=UTC)

    def test_funding_timestamps_epoch_milliseconds(self) -> None:
        # Funding bucket timestamps are epoch MILLISECONDS on the live Market
        # Analytics funding surface (I10R1 adjudication: I10 NULL convenience
        # timestamps = 13-digit overflow; probe module observed ms for funding;
        # live characterization reproduced {rate, relativeRate} exactly).
        # Convenience datetime = ms/1000; raw native int preserved.
        batch = _adapter(routes=HAPPY_ROUTES).fetch_funding(
            request(SensorFamily.MECHANICAL_FUNDING)
        )
        assert batch.actual_first_timestamp == datetime.fromtimestamp(1755000000000 / 1000, tz=UTC)

    def test_interval_encoding_default_seconds(self) -> None:
        _, params = KrakenAnalyticsRequestBuilder().build(
            request(SensorFamily.MECHANICAL_FUNDING)
        )
        assert params["interval"] == 3600


class TestEmptyValidAndRaggedHistory:
    def test_empty_valid_is_explicit_quality_flag(self) -> None:
        adapter = _adapter()  # default route = empty-valid analytics body
        batch = adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert isinstance(batch, FetchBatch)
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags
        assert batch.is_complete is True

    def test_ragged_old_window_stays_empty_valid_not_unsupported(self) -> None:
        # OI 2021/2022 windows are EMPTY_VALID per committed evidence — an
        # empty response is an OBSERVATION, never rewritten as unsupported.
        adapter = _adapter()
        batch = adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags
        assert batch.raw_payloads  # raw evidence preserved even when empty

    def test_funding_old_window_empty_valid(self) -> None:
        # funding 2021/2022/2024 checkpoints were EMPTY_VALID; positive
        # coverage verified 2026+ (I13R1).  Empty stays a valid observation.
        adapter = _adapter()
        batch = adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags


class TestSchemaDriftFailClosed:
    def test_each_sensor_drift_body_blocks_parsed_output(self) -> None:
        routes = {
            "/open-interest": FX.DRIFT["open_interest"],
            "/funding": FX.DRIFT["funding"],
            "/future-basis": FX.DRIFT["basis"],
            "/long-short-ratio": FX.DRIFT["positioning"],
            "/liquidation-volume": FX.DRIFT["liquidation"],
            "/orderbook": FX.DRIFT["book_metric"],
        }
        adapter = _adapter(routes=routes)
        for sensor in ALL_PROMOTED:
            with pytest.raises(SchemaDrift) as excinfo:
                dispatch_fetch(adapter, request(sensor))
            assert excinfo.value.failure_type == "SchemaDrift"
            assert classify_retryability(excinfo.value) is Retryability.TERMINAL

    def test_unknown_envelope_blocks(self) -> None:
        adapter = _adapter(routes={"/funding": (200, {"unexpected": 1})})
        with pytest.raises(SchemaDrift):
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))

    def test_short_metric_column_blocks(self) -> None:
        # a metric column shorter than the timestamp column is a schema break
        body = {
            "errors": [],
            "result": {
                "timestamp": [1755000000, 1755003600],
                "data": {"basis": ["0.001"]},
                "more": False,
            },
        }
        adapter = _adapter(routes={"/future-basis": (200, body)})
        with pytest.raises(SchemaDrift):
            adapter.fetch_basis(request(SensorFamily.MECHANICAL_BASIS))


class TestProviderErrorsStayTyped:
    def test_symbol_error_envelope_is_invalid_instrument(self) -> None:
        adapter = _adapter(routes={"/open-interest": FX.ERROR["open_interest"]})
        with pytest.raises(InvalidInstrument) as excinfo:
            adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert excinfo.value.failure_type == "InvalidInstrument"
        assert classify_retryability(excinfo.value) is Retryability.TERMINAL

    def test_http_429_is_rate_limited(self) -> None:
        adapter = _adapter(routes={"/funding": (429, {"errors": []})})
        with pytest.raises(RateLimited) as excinfo:
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert classify_retryability(excinfo.value) is Retryability.RETRYABLE

    def test_http_500_is_provider_unavailable(self) -> None:
        adapter = _adapter(routes={"/orderbook": (500, {})})
        with pytest.raises(ProviderUnavailable):
            adapter.fetch_book_metrics(request(SensorFamily.MECHANICAL_BOOK_METRIC))

    def test_http_403_is_access_class_violation(self) -> None:
        adapter = _adapter(routes={"/orderbook": (403, {})})
        with pytest.raises(AccessClassViolation):
            adapter.fetch_book_metrics(request(SensorFamily.MECHANICAL_BOOK_METRIC))

    def test_transport_raise_stays_typed(self) -> None:
        from crypto_sensor_fabric.providers.base.errors import TransportFailure

        adapter = _adapter(
            routes={"/funding": TransportFailure(PROVIDER_ID, SensorFamily.MECHANICAL_FUNDING)}
        )
        with pytest.raises(TransportFailure):
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))


class TestRawHashDeterministic:
    def test_identical_payload_identical_hash(self) -> None:
        a = _adapter(routes=HAPPY_ROUTES).fetch_basis(request(SensorFamily.MECHANICAL_BASIS))
        b = _adapter(routes=HAPPY_ROUTES).fetch_basis(request(SensorFamily.MECHANICAL_BASIS))
        assert a.raw_payloads[0].content_hash == b.raw_payloads[0].content_hash
        assert a.raw_payloads[0].raw_body == b.raw_payloads[0].raw_body

    def test_different_payload_different_hash(self) -> None:
        a = _adapter(routes=HAPPY_ROUTES).fetch_basis(request(SensorFamily.MECHANICAL_BASIS))
        b = _adapter().fetch_basis(request(SensorFamily.MECHANICAL_BASIS))  # empty-valid
        assert a.raw_payloads[0].content_hash != b.raw_payloads[0].content_hash


class TestResumeDeterminism:
    def test_continuation_page_token_from_oldest_bucket(self) -> None:
        adapter = _adapter(routes={"/open-interest": FX.CONTINUE["open_interest"]})
        batch = adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert batch.is_complete is False
        assert batch.next_resume_token is not None
        token = batch.next_resume_token
        assert token.mode is PaginationMode.TIME_RANGE
        assert token.page_number == 1
        # result.more -> re-issue since at the OLDEST bucket (no cursor guessing)
        assert token.provider_native_state["since"] == 1754870400
        assert token.provider_native_state["symbol"] == "PI_XBTUSD"

    def test_resume_token_round_trip_deterministic(self) -> None:
        adapter = _adapter(routes={"/open-interest": FX.CONTINUE["open_interest"]})
        token = adapter.fetch_open_interest(
            request(SensorFamily.MECHANICAL_OPEN_INTEREST)
        ).next_resume_token
        assert token is not None
        rebuilt = ResumeToken.model_validate_json(token.model_dump_json())
        assert rebuilt == token

    def test_resumed_request_reissues_since_at_oldest_bucket(self) -> None:
        adapter = _adapter(routes={"/open-interest": FX.CONTINUE["open_interest"]})
        first = adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        token = first.next_resume_token
        assert token is not None
        continuation = request(
            SensorFamily.MECHANICAL_OPEN_INTEREST, request_id="r2"
        ).model_copy(update={"resume_token": token})
        url, params = KrakenAnalyticsRequestBuilder().build(continuation)
        assert params["since"] == 1754870400  # exact, re-runnable continuation

    def test_boundary_overlap_preserved_not_dropped(self) -> None:
        # the continuation since equals the OLDEST bucket of the previous page
        # (overlap is a provider semantic; duplicates are annotated upstream,
        # never destructively removed here)
        adapter = _adapter(routes={"/open-interest": FX.CONTINUE["open_interest"]})
        batch = adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert batch.next_resume_token is not None
        assert batch.next_resume_token.provider_native_state["since"] == min(
            1754870400, 1754874000
        )

    def test_terminal_page_has_no_resume_token(self) -> None:
        adapter = _adapter(routes=HAPPY_ROUTES)
        batch = adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert batch.is_complete is True
        assert batch.next_resume_token is None

    def test_repeated_resume_state_is_deterministic_no_loop(self) -> None:
        # the adapter returns ONE page per call; re-issuing the same token
        # yields the same `since` (deterministic, no infinite traversal here)
        token = ResumeToken(
            mode=PaginationMode.TIME_RANGE,
            page_number=1,
            provider_native_state={"since": 1754870400, "symbol": "PI_XBTUSD"},
        )
        p1 = KrakenAnalyticsRequestBuilder().build(
            request(SensorFamily.MECHANICAL_OPEN_INTEREST, request_id="r2").model_copy(
                update={"resume_token": token}
            )
        )
        p2 = KrakenAnalyticsRequestBuilder().build(
            request(SensorFamily.MECHANICAL_OPEN_INTEREST, request_id="r3").model_copy(
                update={"resume_token": token}
            )
        )
        assert p1 == p2


class TestNativeInstrumentRequired:
    def test_empty_native_instrument_rejected(self) -> None:
        from crypto_sensor_fabric.providers.base.models import FetchRequest

        with pytest.raises(Exception):
            FetchRequest(
                provider_id=PROVIDER_ID,
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
                native_instrument_id="",
                start_time=datetime(2026, 1, 1, tzinfo=UTC),
                end_time=datetime(2026, 1, 1, hour=1, tzinfo=UTC),
                request_id="r",
                purpose="PROBE",
                adapter_semantic_version="0.0.0",
            )


class TestInstrumentScopeSeparation:
    """SENSOR-B3-I05R1 — probe universe vs production instrument support."""

    def test_production_scope_derived_from_evidence(self) -> None:
        # evidence-backed union (08_HISTORY_BOUNDARIES.csv): PI_XBTUSD for all
        # six, PI_ETHUSD additionally for OI — never probe-only SOL/DOGE
        assert KRAKEN_PRODUCTION_INSTRUMENT_SCOPE == ["PI_XBTUSD", "PI_ETHUSD"]

    def test_probe_scope_keeps_probe_universe(self) -> None:
        assert KRAKEN_PROBE_INSTRUMENT_SCOPE == [
            "PI_XBTUSD",
            "PI_ETHUSD",
            "PI_SOLUSD",
            "PI_DOGEUSD",
        ]

    def test_sensor_specific_symbol_scopes_from_evidence(self) -> None:
        assert KRAKEN_SYMBOL_SCOPES[SensorFamily.MECHANICAL_OPEN_INTEREST] == (
            "PI_ETHUSD",
            "PI_XBTUSD",
        )
        for sensor in ALL_PROMOTED:
            if sensor is SensorFamily.MECHANICAL_OPEN_INTEREST:
                continue
            assert KRAKEN_SYMBOL_SCOPES[sensor] == ("PI_XBTUSD",)

    def test_capability_symbol_scope_per_sensor(self) -> None:
        caps = build_kraken_capabilities()
        oi = caps.capability_for(SensorFamily.MECHANICAL_OPEN_INTEREST)
        assert set(oi.symbol_scope) == {"PI_XBTUSD", "PI_ETHUSD"}
        basis = caps.capability_for(SensorFamily.MECHANICAL_BASIS)
        assert basis.symbol_scope == ["PI_XBTUSD"]

    def test_oi_eth_evidence_backed_passes(self) -> None:
        adapter = _adapter(routes=HAPPY_ROUTES)
        batch = adapter.fetch_open_interest(
            request(SensorFamily.MECHANICAL_OPEN_INTEREST, native_instrument_id="PI_ETHUSD")
        )
        assert batch.native_instrument_id == "PI_ETHUSD"

    def test_basis_eth_not_evidence_backed_fails_typed(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        with pytest.raises(InvalidInstrument) as excinfo:
            adapter.fetch_basis(
                request(SensorFamily.MECHANICAL_BASIS, native_instrument_id="PI_ETHUSD")
            )
        assert excinfo.value.failure_type == "InvalidInstrument"
        assert transport.calls == []  # fails BEFORE transport

    def test_probe_only_symbols_fail_every_promoted_sensor(self) -> None:
        for sensor in ALL_PROMOTED:
            for symbol in ("PI_SOLUSD", "PI_DOGEUSD"):
                transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
                adapter = KrakenAdapter(transport=transport)
                with pytest.raises(InvalidInstrument):
                    dispatch_fetch(adapter, request(sensor, native_instrument_id=symbol))
                assert transport.calls == []


class TestRequestProviderIdentity:
    """SENSOR-B3-I05R1 — a Kraken adapter never executes foreign requests."""

    def test_fetch_request_wrong_provider_fails_before_transport(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        req = request(SensorFamily.MECHANICAL_FUNDING).model_copy(
            update={"provider_id": "OKX_SWAP"}
        )
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_funding(req)
        assert excinfo.value.failure_type == "ProviderSemanticError"
        assert transport.calls == []

    def test_dispatch_wrong_provider_fails_before_transport(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        req = request(SensorFamily.MECHANICAL_BASIS).model_copy(
            update={"provider_id": "DERIBIT"}
        )
        with pytest.raises(ProviderSemanticError):
            dispatch_fetch(adapter, req)
        assert transport.calls == []

    def test_instrument_list_request_wrong_provider_fails(self) -> None:
        # instrument discovery carries no requested sensor; the failure uses
        # the documented neutral provider-level placeholder (never a real
        # scientific sensor), per SENSOR-B3-I05R2 Repair 1.
        adapter = _adapter()
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.list_instruments(
                InstrumentListRequest(provider_id="GATE_FUTURES", request_id="r")
            )
        assert excinfo.value.provider_id == PROVIDER_ID
        assert excinfo.value.sensor_family is NEUTRAL_INSTRUMENT_LIST_SENSOR


class TestGranularityFailClosed:
    """SENSOR-B3-I05R1 — explicit unsupported granularity never becomes 1h."""

    SUPPORTED = {
        Granularity.G1M: 60,
        Granularity.G5M: 300,
        Granularity.G15M: 900,
        Granularity.G1H: 3600,
        Granularity.G4H: 14400,
        Granularity.G1D: 86400,
    }
    UNSUPPORTED = (Granularity.RAW_EVENT, Granularity.BOOK_SNAPSHOT)

    def test_granularity_none_uses_documented_default(self) -> None:
        builder = KrakenAnalyticsRequestBuilder()
        _, params = builder.build(request(SensorFamily.MECHANICAL_FUNDING))
        assert params["interval"] == 3600  # explicit None -> default 1h

    def test_every_supported_granularity_maps_exactly(self) -> None:
        builder = KrakenAnalyticsRequestBuilder()
        for granularity, interval in self.SUPPORTED.items():
            req = request(SensorFamily.MECHANICAL_FUNDING).model_copy(
                update={"granularity": granularity}
            )
            _, params = builder.build(req)
            assert params["interval"] == interval, granularity

    def test_every_unsupported_granularity_fails_typed(self) -> None:
        builder = KrakenAnalyticsRequestBuilder()
        for granularity in self.UNSUPPORTED:
            req = request(SensorFamily.MECHANICAL_FUNDING).model_copy(
                update={"granularity": granularity}
            )
            with pytest.raises(UnsupportedGranularity) as excinfo:
                builder.build(req)
            assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_FUNDING

    def test_unsupported_granularity_fails_before_transport(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        req = request(SensorFamily.MECHANICAL_FUNDING).model_copy(
            update={"granularity": Granularity.RAW_EVENT}
        )
        with pytest.raises(UnsupportedGranularity):
            adapter.fetch_funding(req)
        assert transport.calls == []


class TestSchemaDriftRawEnvelope:
    """SENSOR-B3-I05R1 — SchemaDrift carries the exact preserved raw envelope."""

    def _drift_routes(self) -> dict[str, Any]:
        return {
            "/open-interest": FX.DRIFT["open_interest"],
            "/funding": FX.DRIFT["funding"],
            "/future-basis": FX.DRIFT["basis"],
            "/long-short-ratio": FX.DRIFT["positioning"],
            "/liquidation-volume": FX.DRIFT["liquidation"],
            "/orderbook": FX.DRIFT["book_metric"],
        }

    def test_each_promoted_sensor_drift_carries_raw_envelope(self) -> None:
        adapter = _adapter(routes=self._drift_routes())
        for sensor in ALL_PROMOTED:
            with pytest.raises(SchemaDrift) as excinfo:
                dispatch_fetch(adapter, request(sensor))
            err = excinfo.value
            assert err.failure_type == "SchemaDrift"
            envelope = err.raw_payload_envelope
            assert envelope is not None, f"{sensor.value} drift lost the raw envelope"
            assert envelope.provider_id == PROVIDER_ID
            assert envelope.sensor_family is sensor
            assert envelope.request_fingerprint
            assert envelope.schema_state in (
                SchemaState.BREAKING_SCHEMA_CHANGE,
                SchemaState.UNKNOWN_SCHEMA,
            )
            # hash matches the preserved raw body; evidence ref resolves to I14
            raw = envelope.raw_body
            raw_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8")
            assert envelope.content_hash == payload_hash(raw_bytes)
            caps = build_kraken_capabilities()
            ref = caps.capability_for(sensor).probe_evidence_ref
            assert ref is not None
            assert envelope.evidence_ref == ref
            assert ref.evidence_id in caps.capability_for(sensor).evidence_basis

    def test_drift_envelope_hash_deterministic(self) -> None:
        first = _adapter(routes=self._drift_routes())
        second = _adapter(routes=self._drift_routes())
        with pytest.raises(SchemaDrift) as a:
            first.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        with pytest.raises(SchemaDrift) as b:
            second.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))
        assert a.value.raw_payload_envelope is not None
        assert b.value.raw_payload_envelope is not None
        assert a.value.raw_payload_envelope.content_hash == b.value.raw_payload_envelope.content_hash
        assert a.value.raw_payload_envelope.raw_body == b.value.raw_payload_envelope.raw_body


class TestListCardinalityFailClosed:
    """SENSOR-B3-I05R1 — structural list/dict cardinality mismatch is BREAKING."""

    LIST_SENSORS = (
        SensorFamily.MECHANICAL_OPEN_INTEREST,
        SensorFamily.MECHANICAL_POSITIONING,
        SensorFamily.MECHANICAL_LIQUIDATION,
    )
    FRAGMENT = {
        SensorFamily.MECHANICAL_OPEN_INTEREST: "/open-interest",
        SensorFamily.MECHANICAL_POSITIONING: "/long-short-ratio",
        SensorFamily.MECHANICAL_LIQUIDATION: "/liquidation-volume",
    }

    def test_list_data_shorter_than_timestamps_breaks(self) -> None:
        for sensor in self.LIST_SENSORS:
            body = {
                "errors": [],
                "result": {
                    "timestamp": [1755000000, 1755003600, 1755007200],
                    "data": [["1"], ["2"]],
                    "more": False,
                },
            }
            adapter = _adapter(routes={self.FRAGMENT[sensor]: (200, body)})
            with pytest.raises(SchemaDrift):
                dispatch_fetch(adapter, request(sensor))

    def test_list_data_longer_than_timestamps_breaks(self) -> None:
        for sensor in self.LIST_SENSORS:
            body = {
                "errors": [],
                "result": {
                    "timestamp": [1755000000],
                    "data": [["1"], ["2"]],
                    "more": False,
                },
            }
            adapter = _adapter(routes={self.FRAGMENT[sensor]: (200, body)})
            with pytest.raises(SchemaDrift):
                dispatch_fetch(adapter, request(sensor))

    def test_dict_metric_column_longer_than_timestamps_breaks(self) -> None:
        body = {
            "errors": [],
            "result": {
                "timestamp": [1755000000],
                "data": {"basis": ["0.001", "0.002"]},
                "more": False,
            },
        }
        adapter = _adapter(routes={"/future-basis": (200, body)})
        with pytest.raises(SchemaDrift):
            adapter.fetch_basis(request(SensorFamily.MECHANICAL_BASIS))

    def test_legitimate_provider_null_still_preserved(self) -> None:
        # a correctly-sized column containing a provider-declared null is
        # native data, NOT a structural mismatch (book_metric slippage1m)
        batch = _adapter(routes=HAPPY_ROUTES).fetch_book_metrics(
            request(SensorFamily.MECHANICAL_BOOK_METRIC)
        )
        assert batch.row_count >= 1


class TestNoTransportSensorIdentity:
    """SENSOR-B3-I05R1 — no-transport failure names the REQUESTED sensor."""

    def test_all_six_sensors_report_correct_sensor(self) -> None:
        for sensor in ALL_PROMOTED:
            adapter = KrakenAdapter()  # no transport
            with pytest.raises(ProviderUnavailable) as excinfo:
                dispatch_fetch(adapter, request(sensor))
            assert excinfo.value.sensor_family is sensor, sensor


class TestMethodSensorIdentity:
    """SENSOR-B3-I05R1 — named fetch methods are themselves a contract."""

    METHODS = {
        "fetch_funding": SensorFamily.MECHANICAL_FUNDING,
        "fetch_basis": SensorFamily.MECHANICAL_BASIS,
        "fetch_liquidations": SensorFamily.MECHANICAL_LIQUIDATION,
        "fetch_open_interest": SensorFamily.MECHANICAL_OPEN_INTEREST,
        "fetch_positioning": SensorFamily.MECHANICAL_POSITIONING,
        "fetch_book_metrics": SensorFamily.MECHANICAL_BOOK_METRIC,
    }

    def test_mismatched_request_fails_before_transport(self) -> None:
        for method_name, expected in self.METHODS.items():
            wrong = next(s for s in ALL_PROMOTED if s is not expected)
            transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
            adapter = KrakenAdapter(transport=transport)
            method = getattr(adapter, method_name)
            with pytest.raises(ProviderSemanticError) as excinfo:
                method(request(wrong))
            assert excinfo.value.sensor_family is wrong
            assert transport.calls == [], f"{method_name} reached transport"

    def test_matching_request_passes(self) -> None:
        adapter = _adapter(routes=HAPPY_ROUTES)
        for method_name, expected in self.METHODS.items():
            batch = getattr(adapter, method_name)(request(expected))
            assert batch.sensor_family is expected


class TestForeignProviderErrorSensorIdentity:
    """SENSOR-B3-I05R2 Repair 1 — a foreign FetchRequest reports ITS OWN sensor."""

    def test_all_six_promoted_sensors_report_requested_sensor(self) -> None:
        for sensor in ALL_PROMOTED:
            transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
            adapter = KrakenAdapter(transport=transport)
            req = request(sensor).model_copy(update={"provider_id": "OKX_SWAP"})
            with pytest.raises(ProviderSemanticError) as excinfo:
                dispatch_fetch(adapter, req)
            err = excinfo.value
            assert err.failure_type == "ProviderSemanticError"
            assert err.provider_id == PROVIDER_ID
            assert err.sensor_family is sensor, f"wrong sensor {err.sensor_family} for {sensor.value}"
            assert transport.calls == [], f"{sensor.value} reached transport"

    def test_foreign_funding_request_reports_funding(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        req = request(SensorFamily.MECHANICAL_FUNDING).model_copy(
            update={"provider_id": "OKX_SWAP"}
        )
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_funding(req)
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_FUNDING
        assert transport.calls == []

    def test_foreign_basis_request_reports_basis(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        req = request(SensorFamily.MECHANICAL_BASIS).model_copy(
            update={"provider_id": "DERIBIT"}
        )
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_basis(req)
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_BASIS
        assert transport.calls == []


class TestUnsupportedMethodIdentity:
    """SENSOR-B3-I05R2 Repair 2 — unsupported named methods honor METHOD identity."""

    def test_fetch_trades_funding_request_is_mismatch_not_unsupported_funding(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_trades(request(SensorFamily.MECHANICAL_FUNDING))
        assert excinfo.value.failure_type == "ProviderSemanticError"
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_FUNDING
        assert transport.calls == []  # method/sensor mismatch: never claims funding unsupported

    def test_fetch_trades_trade_request_is_typed_unsupported(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        with pytest.raises(CapabilityUnavailable) as excinfo:
            adapter.fetch_trades(request(SensorFamily.MECHANICAL_TRADE))
        assert excinfo.value.failure_type == "CapabilityUnavailable"
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_TRADE
        assert transport.calls == []

    def test_fetch_book_funding_request_is_mismatch_not_unsupported_funding(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_book(request(SensorFamily.MECHANICAL_FUNDING))
        assert excinfo.value.failure_type == "ProviderSemanticError"
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_FUNDING
        assert transport.calls == []  # method/sensor mismatch: never claims funding unsupported

    def test_fetch_book_book_snapshot_request_is_typed_unsupported(self) -> None:
        transport = FakeKrakenTransport(routes=HAPPY_ROUTES)
        adapter = KrakenAdapter(transport=transport)
        with pytest.raises(CapabilityUnavailable) as excinfo:
            adapter.fetch_book(request(SensorFamily.MECHANICAL_BOOK_SNAPSHOT))
        assert excinfo.value.failure_type == "CapabilityUnavailable"
        assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT
        assert transport.calls == []


class TestTimestampSchemaThroughAdapter:
    """SENSOR-B3-I05R2 Repair 3/4 — invalid timestamps drift with raw envelope."""

    def test_string_timestamp_through_real_adapter_drift_carries_envelope(self) -> None:
        body = {"errors": [], "result": {"timestamp": ["1755000000"], "data": [["725.3"]], "more": False}}
        transport = FakeKrakenTransport(routes={"/open-interest": (200, body)})
        adapter = KrakenAdapter(transport=transport)
        with pytest.raises(SchemaDrift) as excinfo:
            adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        err = excinfo.value
        assert err.failure_type == "SchemaDrift"
        assert err.sensor_family is SensorFamily.MECHANICAL_OPEN_INTEREST
        envelope = err.raw_payload_envelope
        assert envelope is not None
        assert envelope.provider_id == PROVIDER_ID
        assert envelope.sensor_family is SensorFamily.MECHANICAL_OPEN_INTEREST
        assert envelope.schema_state is SchemaState.BREAKING_SCHEMA_CHANGE
        raw = envelope.raw_body
        raw_bytes = raw if isinstance(raw, bytes) else raw.encode("utf-8")
        assert envelope.content_hash == payload_hash(raw_bytes)
        # evidence ref resolves to the I14 basis for this sensor
        ref = build_kraken_capabilities().capability_for(
            SensorFamily.MECHANICAL_OPEN_INTEREST
        ).probe_evidence_ref
        assert ref is not None
        assert envelope.evidence_ref == ref

    def test_invalid_timestamp_reaches_transport_but_drifts_before_resume(self) -> None:
        # a continuation page whose timestamp list contains a float must drift
        # BEFORE a ResumeToken could be derived — no int-rescue path on resume.
        body = {
            "errors": [],
            "result": {
                "timestamp": [1755000000, 1755000000.0],
                "data": [["700.1"], ["701.0"]],
                "more": True,
            },
        }
        adapter = _adapter(routes={"/open-interest": (200, body)})
        with pytest.raises(SchemaDrift) as excinfo:
            adapter.fetch_open_interest(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert excinfo.value.raw_payload_envelope is not None
        assert isinstance(excinfo.value.raw_payload_envelope, RawPayloadEnvelope)


class TestProductionCandidateConformance:
    def test_full_conformance_passes_with_real_adapter(self) -> None:
        # `/funding` deliberately has NO happy route: the empty-valid request
        # for funding hits the fake transport's default empty-valid body, so
        # the conformance suite exercises the REAL supported-empty path.
        routes = {k: v for k, v in HAPPY_ROUTES.items() if k != "/funding"}
        adapter = _adapter(routes=routes)
        promoted = capabilities_from_promotion(
            "KRAKEN_FUTURES", load_promotion_candidates()
        )
        under_test = AdapterUnderTest(
            adapter=adapter,
            registry_policy=DEFAULT_FREE_ONLY_POLICY,
            auth_mode=AdapterAuthMode.NO_AUTH,
            promoted_capabilities=promoted,
            native_evidence=kraken_native_evidence(),
            empty_valid_request=request(SensorFamily.MECHANICAL_FUNDING),
            unsupported_request=request(SensorFamily.MECHANICAL_TRADE),
            fetch_request=request(SensorFamily.MECHANICAL_BOOK_METRIC),
            mode=AdapterConformanceMode.PRODUCTION_CANDIDATE,
        )
        results = run_conformance_suite(under_test)
        failed = [r for r in results if not r.passed]
        assert not failed, "\n".join(f"{r.check_id}: {r.detail}" for r in failed)
        summary = summarize_conformance(results)
        assert summary["failed"] == 0
        assert summary["passed"] == summary["checks"]

    def test_exact_i14_set_no_seventh_path(self) -> None:
        caps = build_kraken_capabilities()
        assert set(caps.supported_sensors()) == set(ALL_PROMOTED)
        assert len(caps.supported_sensors()) == 6
