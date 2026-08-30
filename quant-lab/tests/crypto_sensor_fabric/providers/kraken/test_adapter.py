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
    PaginationMode,
    QualityFlagAcquisition,
    Retryability,
)
from crypto_sensor_fabric.providers.base.errors import (
    AccessClassViolation,
    CapabilityUnavailable,
    InvalidInstrument,
    ProviderUnavailable,
    RateLimited,
    SchemaDrift,
)
from crypto_sensor_fabric.providers.base.models import (
    FetchBatch,
    InstrumentListRequest,
    ResumeToken,
)
from crypto_sensor_fabric.providers.base.protocol import MechanicalProviderAdapter
from crypto_sensor_fabric.providers.kraken import (
    DEFAULT_FREE_ONLY_POLICY,
    KRAKEN_INSTRUMENT_SCOPE,
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

    def test_list_instruments_is_configured_scope_no_discovery(self) -> None:
        transport = FakeKrakenTransport()
        adapter = KrakenAdapter(transport=transport)
        result = adapter.list_instruments(
            InstrumentListRequest(provider_id=PROVIDER_ID, request_id="r")
        )
        assert result.provider_id == PROVIDER_ID
        assert result.native_instrument_ids == list(KRAKEN_INSTRUMENT_SCOPE)
        # a configured native scope, NOT an invented discovery endpoint: the
        # transport is never consulted.
        assert transport.calls == []

    def test_no_transport_is_offline(self) -> None:
        adapter = KrakenAdapter()  # no transport injected
        with pytest.raises(ProviderUnavailable):
            adapter.fetch_funding(request(SensorFamily.MECHANICAL_FUNDING))


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

    def test_funding_timestamps_epoch_seconds_from_evidence(self) -> None:
        # funding happy fixture uses the same epoch-second unit as the committed
        # probe fixture + live probe contract (I13R1 fingerprint pins int only).
        batch = _adapter(routes=HAPPY_ROUTES).fetch_funding(
            request(SensorFamily.MECHANICAL_FUNDING)
        )
        assert batch.actual_first_timestamp == datetime.fromtimestamp(1755000000, tz=UTC)

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
