"""SENSOR-B3-I08 — Deribit adapter offline tests (FAKE TRANSPORT ONLY).

Covers the provider-specific minimum at the REAL `DeribitAdapter` boundary:

- free-only access gate runs BEFORE any transport call (no bypass)
- four unpromoted sensors stay typed `CapabilityUnavailable`
- four promoted paths fetch happy fixtures end-to-end (book CURRENT_ONLY,
  funding SECONDARY historical, liquidation + trade MECHANISM_MICROSCOPE)
- completion truth: a single evidence-backed window is complete ONLY when the
  rows are non-empty, all in-window, and the provider-native terminal condition
  holds (funding under count cap; trade/liquidation has_more=false); no
  invented resume token (continuation beyond one window LIMITED)
- liquidation microscope: mixed page -> liquidation view projects ONLY the
  forced-liquidation row while the trade view keeps every row; zero events ->
  EMPTY_VALID with raw payload preserved
- book stays CURRENT_ONLY (no historical/rest surface)
- EMPTY_VALID distinct from unsupported / provider error
- raw payload hash deterministic; SchemaDrift carries RawPayloadEnvelope
- provider errors stay typed (JSON-RPC error on HTTP 200 != EMPTY_VALID)
- symbol scope + method/provider identity guards, no-transport sensor identity
- full common conformance passes in PRODUCTION_CANDIDATE mode

NO network call is possible: the only transport ever constructed is the
offline `FakeDeribitTransport`; a no-transport adapter raises
`ProviderUnavailable`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
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
from crypto_sensor_fabric.providers.deribit import (
    DEFAULT_FREE_ONLY_POLICY,
    NEUTRAL_INSTRUMENT_LIST_SENSOR,
    DERIBIT_PRODUCTION_INSTRUMENT_SCOPE,
    PROVIDER_ID,
    DeribitAdapter,
    DeribitRequestBuilder,
    build_deribit_capabilities,
    deribit_native_evidence,
)

from ._fake import FakeDeribitTransport, request
from .fixtures import responses as FX

BOOK = SensorFamily.MECHANICAL_BOOK_SNAPSHOT
FUNDING = SensorFamily.MECHANICAL_FUNDING
LIQUIDATION = SensorFamily.MECHANICAL_LIQUIDATION
TRADE = SensorFamily.MECHANICAL_TRADE

ALL_PROMOTED = (BOOK, FUNDING, LIQUIDATION, TRADE)

UNPROMOTED = (
    SensorFamily.MECHANICAL_BASIS,
    SensorFamily.MECHANICAL_BOOK_METRIC,
    SensorFamily.MECHANICAL_OPEN_INTEREST,
    SensorFamily.MECHANICAL_POSITIONING,
)

HAPPY_ROUTES: dict[str, Any] = {
    "/get_last_trades_by_instrument": (200, FX.TRADE_HAPPY),
    "/get_funding_rate_history": (200, FX.FUNDING_HAPPY),
    "/get_order_book": (200, FX.BOOK_HAPPY),
}


def _adapter(routes: dict[str, Any] | None = None, **kwargs: Any) -> DeribitAdapter:
    transport = (
        FakeDeribitTransport(routes=routes) if routes is not None else FakeDeribitTransport()
    )
    return DeribitAdapter(transport=transport, **kwargs)


class TestProviderIdentityAndProtocol:
    def test_provider_id_frozen(self) -> None:
        assert PROVIDER_ID == "DERIBIT"
        assert _adapter().provider_id == "DERIBIT"

    def test_adapter_implements_common_protocol(self) -> None:
        assert isinstance(_adapter(), MechanicalProviderAdapter)

    def test_exactly_four_promoted(self) -> None:
        caps = _adapter().capabilities()
        assert set(caps.supported_sensors()) == set(ALL_PROMOTED)
        assert len(caps.supported_sensors()) == 4

    def test_promoted_roles(self) -> None:
        from crypto_sensor_fabric.probes.enums import ProviderRole

        caps = _adapter().capabilities()
        assert caps.capability_for(BOOK).allowed_role is ProviderRole.CURRENT_ONLY
        assert caps.capability_for(FUNDING).allowed_role is ProviderRole.SECONDARY
        assert caps.capability_for(LIQUIDATION).allowed_role is ProviderRole.MECHANISM_MICROSCOPE
        assert caps.capability_for(TRADE).allowed_role is ProviderRole.MECHANISM_MICROSCOPE

    def test_list_instruments_is_configured_production_scope(self) -> None:
        transport = FakeDeribitTransport()
        adapter = DeribitAdapter(transport=transport)
        result = adapter.list_instruments(
            InstrumentListRequest(provider_id=PROVIDER_ID, request_id="r")
        )
        assert result.provider_id == PROVIDER_ID
        assert result.native_instrument_ids == list(DERIBIT_PRODUCTION_INSTRUMENT_SCOPE)
        assert "ETH-PERPETUAL" not in result.native_instrument_ids
        assert "SOL-PERPETUAL" not in result.native_instrument_ids
        assert transport.calls == []  # configured scope, not discovery

    def test_no_transport_is_offline(self) -> None:
        adapter = DeribitAdapter()  # no transport
        with pytest.raises(ProviderUnavailable) as excinfo:
            adapter.fetch_trades(request(TRADE))
        assert excinfo.value.sensor_family is TRADE


class TestAccessGateBeforeTransport:
    def test_trading_auth_blocked_before_transport(self) -> None:
        transport = FakeDeribitTransport()
        adapter = DeribitAdapter(transport=transport, auth_mode=AdapterAuthMode.TRADING_KEY)
        with pytest.raises(AccessClassViolation):
            adapter.fetch_funding(request(FUNDING))
        assert transport.calls == []

    def test_free_only_default_passes_gate_and_calls_transport(self) -> None:
        transport = FakeDeribitTransport(routes=HAPPY_ROUTES)
        adapter = DeribitAdapter(transport=transport)
        batch = adapter.fetch_trades(request(TRADE))
        assert isinstance(batch, FetchBatch)
        assert len(transport.calls) == 1


class TestTypedUnsupported:
    @pytest.mark.parametrize("sensor", UNPROMOTED)
    def test_unpromoted_sensor_typed_unsupported_with_correct_sensor(self, sensor) -> None:
        transport = FakeDeribitTransport(routes=HAPPY_ROUTES)
        adapter = DeribitAdapter(transport=transport)
        method = {
            SensorFamily.MECHANICAL_BASIS: "fetch_basis",
            SensorFamily.MECHANICAL_BOOK_METRIC: "fetch_book_metrics",
            SensorFamily.MECHANICAL_OPEN_INTEREST: "fetch_open_interest",
            SensorFamily.MECHANICAL_POSITIONING: "fetch_positioning",
        }[sensor]
        with pytest.raises(CapabilityUnavailable) as excinfo:
            getattr(adapter, method)(request(sensor))
        assert excinfo.value.sensor_family is sensor
        assert transport.calls == []

    def test_dispatch_unpromoted_typed_unsupported(self) -> None:
        with pytest.raises(CapabilityUnavailable):
            dispatch_fetch(_adapter(), request(SensorFamily.MECHANICAL_OPEN_INTEREST))


class TestMethodSensorIdentity:
    METHOD_SENSOR = {
        "fetch_trades": TRADE,
        "fetch_liquidations": LIQUIDATION,
        "fetch_book": BOOK,
        "fetch_funding": FUNDING,
    }

    def test_mismatched_request_fails_before_transport(self) -> None:
        for method_name, expected in self.METHOD_SENSOR.items():
            wrong = next(s for s in ALL_PROMOTED if s is not expected)
            transport = FakeDeribitTransport(routes=HAPPY_ROUTES)
            adapter = DeribitAdapter(transport=transport)
            with pytest.raises(ProviderSemanticError) as excinfo:
                getattr(adapter, method_name)(request(wrong))
            assert excinfo.value.sensor_family is wrong
            assert transport.calls == [], f"{method_name} reached transport"

    def test_unsupported_named_method_preserves_sensor_identity(self) -> None:
        # fetch_open_interest(FUNDING request) is a mismatch, NOT a false
        # "funding unsupported" claim.
        transport = FakeDeribitTransport(routes=HAPPY_ROUTES)
        adapter = DeribitAdapter(transport=transport)
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_open_interest(request(FUNDING))
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
            assert batch.native_instrument_id == "BTC-PERPETUAL"
            assert batch.http_status == 200
            assert batch.raw_payloads, f"{sensor.value} must preserve raw evidence"
            ref = batch.raw_payloads[0].evidence_ref
            assert ref is not None and ref.evidence_id
            assert batch.next_resume_token is None  # continuation LIMITED

    def test_book_batch_is_current_only_complete(self) -> None:
        batch = _adapter(routes={"/get_order_book": HAPPY_ROUTES["/get_order_book"]}).fetch_book(request(BOOK))
        assert batch.is_complete is True  # current snapshot acquisition unit
        assert batch.next_resume_token is None
        assert batch.row_count >= 1

    def test_funding_window_served_completion_limited(self) -> None:
        # I08R1 Defect B: the "short page under the count cap is exhaustive"
        # rule is a characterization heuristic, NOT a proven provider
        # contract — funding is NEVER certified complete (completion_proof =
        # LIMITED) even when every row lies inside the requested window.
        batch = _adapter(
            routes={"/get_funding_rate_history": HAPPY_ROUTES["/get_funding_rate_history"]}
        ).fetch_funding(request(FUNDING))
        assert batch.is_complete is False
        assert batch.next_resume_token is None
        assert QualityFlagAcquisition.PARTIAL_INTERVAL in batch.quality_flags
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags

    def test_trade_terminal_page_is_complete(self) -> None:
        # has_more=false + non-empty + all rows in-window -> window served.
        batch = _adapter(
            routes={"/get_last_trades_by_instrument": HAPPY_ROUTES["/get_last_trades_by_instrument"]}
        ).fetch_trades(request(TRADE))
        assert batch.is_complete is True

    def test_liquidation_happy_complete_when_terminal(self) -> None:
        batch = _adapter(
            routes={"/get_last_trades_by_instrument": (200, FX.LIQ_HAPPY)}
        ).fetch_liquidations(request(LIQUIDATION))
        assert batch.is_complete is True
        assert batch.row_count == 1  # ONLY the forced-liquidation row


class TestLiquidationMicroscope:
    def test_mixed_page_projects_only_forced_liquidation(self) -> None:
        routes = {"/get_last_trades_by_instrument": (200, FX.LIQ_HAPPY)}
        adapter = _adapter(routes=routes)
        liq = adapter.fetch_liquidations(request(LIQUIDATION))
        trade = adapter.fetch_trades(request(TRADE))
        assert liq.row_count == 1
        assert trade.row_count == 3
        # raw payload preserved for BOTH views (same physical payload)
        assert liq.raw_payloads[0].content_hash == trade.raw_payloads[0].content_hash
        # the raw envelope retains the FULL provider payload (all three rows),
        # including the native liquidation flag values, un-aggregated.
        raw = json.loads(liq.raw_payloads[0].raw_body.decode("utf-8"))
        flag_values = [r["liquidation"] for r in raw["result"]["trades"]]
        assert flag_values == ["liquidation", "taker", "maker"]
        assert not any(
            k.startswith(("liquidation_usd", "liquidation_volume", "long_liq", "short_liq"))
            for r in raw["result"]["trades"] for k in r
        )

    def test_no_events_is_empty_valid_raw_preserved(self) -> None:
        adapter = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.LIQ_NO_EVENTS)})
        batch = adapter.fetch_liquidations(request(LIQUIDATION))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags
        assert batch.raw_payloads  # nonempty raw payload still preserved

    def test_direction_never_transformed_to_long_short(self) -> None:
        adapter = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.LIQ_HAPPY)})
        batch = adapter.fetch_liquidations(request(LIQUIDATION))
        assert batch.row_count == 1
        raw = json.loads(batch.raw_payloads[0].raw_body.decode("utf-8"))
        flagged = [r for r in raw["result"]["trades"] if r["liquidation"] == "liquidation"]
        # native direction is preserved verbatim (never long/short liquidation)
        assert flagged[0]["direction"] == "sell"
        assert not any("long_liq" in k or "short_liq" in k for r in raw["result"]["trades"] for k in r)


class TestWindowTruth:
    """I07R1 doctrine applied to Deribit — completion is never invented.

    A historical funding/trade/liquidation request is certified complete ONLY
    when the returned rows are non-empty, every row timestamp lies inside the
    requested [start, end) window, and the provider-native terminal condition
    holds.  Requested and actual boundaries stay separate; no continuation
    token is invented.
    """

    @staticmethod
    def _dt(ts_ms: int) -> datetime:
        return datetime.fromtimestamp(ts_ms / 1000, tz=UTC)

    @staticmethod
    def _window(center_dt: datetime) -> tuple[datetime, datetime]:
        # tight 30s window so ONLY the centered row falls inside (fixture rows
        # are 65s / 130s apart)
        half = timedelta(seconds=30)
        return center_dt - half, center_dt + half

    def test_old_requested_window_with_recent_page_is_not_complete(self) -> None:
        # 2021 requested window + a page of 2022 rows: the page does NOT
        # satisfy the request -> GAP_DETECTED, is_complete False.
        old_start = datetime(2021, 1, 1, tzinfo=UTC)
        adapter = _adapter(routes=HAPPY_ROUTES)
        batch = adapter.fetch_trades(request(TRADE, start=old_start))
        assert batch.is_complete is False
        assert batch.next_resume_token is None
        assert batch.requested_start == old_start
        assert QualityFlagAcquisition.GAP_DETECTED in batch.quality_flags
        assert batch.actual_first_timestamp is not None
        assert batch.actual_first_timestamp.year == 2022

    def test_has_more_true_never_complete(self) -> None:
        adapter = _adapter(
            routes={"/get_last_trades_by_instrument": (200, FX.TRADE_HAS_MORE_TRUE)}
        )
        batch = adapter.fetch_trades(request(TRADE))
        assert batch.is_complete is False
        assert batch.next_resume_token is None
        assert QualityFlagAcquisition.PARTIAL_INTERVAL in batch.quality_flags

    def test_rows_outside_requested_window_never_complete(self) -> None:
        # rows at 2022-06-15, window around 2020: outside -> GAP, not complete.
        old = datetime(2020, 1, 1, tzinfo=UTC)
        batch = _adapter(routes=HAPPY_ROUTES).fetch_funding(
            request(FUNDING, start=old, end=old + timedelta(days=1))
        )
        assert batch.is_complete is False
        assert QualityFlagAcquisition.GAP_DETECTED in batch.quality_flags

    def test_requested_and_actual_boundaries_stay_separate(self) -> None:
        old_start = datetime(2021, 1, 1, tzinfo=UTC)
        batch = _adapter(routes=HAPPY_ROUTES).fetch_trades(request(TRADE, start=old_start))
        assert batch.requested_start == old_start
        assert batch.actual_first_timestamp != old_start  # actual = returned rows

    def test_empty_historical_page_is_not_complete(self) -> None:
        # a valid empty page does not prove the requested window is empty:
        # EMPTY_VALID, completeness UNKNOWN (conservative).
        batch = _adapter().fetch_trades(request(TRADE))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags
        assert batch.is_complete is False

    def test_book_snapshot_remains_complete_per_unit(self) -> None:
        batch = _adapter(routes={"/get_order_book": HAPPY_ROUTES["/get_order_book"]}).fetch_book(request(BOOK))
        assert batch.is_complete is True

    def test_no_invented_continuation_token(self) -> None:
        cases = (
            ("fetch_trades", TRADE, "/get_last_trades_by_instrument", (200, FX.TRADE_HAS_MORE_TRUE)),
            ("fetch_liquidations", LIQUIDATION, "/get_last_trades_by_instrument", (200, FX.TRADE_HAS_MORE_TRUE)),
            ("fetch_funding", FUNDING, "/get_funding_rate_history", (200, FX.FUNDING_HAPPY)),
        )
        for method, sensor, route, payload in cases:
            adapter = _adapter(routes={route: payload})
            batch = getattr(adapter, method)(request(sensor))
            assert batch.next_resume_token is None, method


class TestWindowOrderInvariant:
    """PARTIAL/GAP classification is ORDER INVARIANT (I07R2 doctrine).

    Returned row order is provider behavior, not chronological truth: overlap
    is classified from ANY validated row timestamp inside the requested window,
    never from a range test on actual_first/actual_last.
    """

    @staticmethod
    def _dt(ts_ms: int) -> datetime:
        return datetime.fromtimestamp(ts_ms / 1000, tz=UTC)

    @staticmethod
    def _window(center_dt: datetime) -> tuple[datetime, datetime]:
        # tight 30s window so ONLY the centered row falls inside (fixture rows
        # are 65s / 130s apart)
        half = timedelta(seconds=30)
        return center_dt - half, center_dt + half

    def _fetch_descending(self, start: datetime, end: datetime) -> FetchBatch:
        adapter = _adapter(
            routes={"/get_last_trades_by_instrument": (200, FX.TRADE_DESCENDING)}
        )
        return adapter.fetch_trades(request(TRADE, start=start, end=end))

    @staticmethod
    def _assert_partial(batch: FetchBatch) -> None:
        assert QualityFlagAcquisition.PARTIAL_INTERVAL in batch.quality_flags
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags

    @staticmethod
    def _assert_gap(batch: FetchBatch) -> None:
        assert QualityFlagAcquisition.GAP_DETECTED in batch.quality_flags
        assert QualityFlagAcquisition.PARTIAL_INTERVAL not in batch.quality_flags

    def test_descending_page_oldest_row_only_in_window(self) -> None:
        s, e = self._window(self._dt(FX.T1))
        batch = self._fetch_descending(s, e)
        self._assert_partial(batch)
        assert batch.is_complete is False

    def test_descending_page_newest_row_only_in_window(self) -> None:
        s, e = self._window(self._dt(FX.T3))
        batch = self._fetch_descending(s, e)
        self._assert_partial(batch)
        assert batch.is_complete is False

    def test_descending_page_middle_row_only_in_window(self) -> None:
        s, e = self._window(self._dt(FX.T2))
        batch = self._fetch_descending(s, e)
        self._assert_partial(batch)

    def test_descending_page_no_row_in_window_is_gap(self) -> None:
        t1 = self._dt(FX.T1)
        s, e = t1 - timedelta(hours=2), t1 - timedelta(hours=1)
        batch = self._fetch_descending(s, e)
        self._assert_gap(batch)
        assert batch.is_complete is False

    def test_descending_actual_boundaries_preserve_returned_order(self) -> None:
        s, e = self._window(self._dt(FX.T1))
        batch = self._fetch_descending(s, e)
        # actual_first/last = first/last RETURNED rows (not min/max)
        assert batch.actual_first_timestamp == self._dt(FX.T3)
        assert batch.actual_last_timestamp == self._dt(FX.T1)
        assert batch.actual_first_timestamp > batch.actual_last_timestamp

    def test_funding_ascending_exclusivity(self) -> None:
        s, e = self._window(self._dt(FX.T1))
        adapter = _adapter(routes={"/get_funding_rate_history": HAPPY_ROUTES["/get_funding_rate_history"]})
        partial = adapter.fetch_funding(request(FUNDING, start=s, end=e))
        self._assert_partial(partial)
        old = datetime(2020, 1, 1, tzinfo=UTC)
        gap = adapter.fetch_funding(request(FUNDING, start=old, end=old + timedelta(days=1)))
        self._assert_gap(gap)
        assert gap.is_complete is False


class TestQualityFlagMatrix:
    """I08R1 Defect A — COMPLETE can never carry PARTIAL_INTERVAL.

    Quality flags are assigned AFTER the completion decision: a proven-complete
    batch has NO PARTIAL/GAP flag; PARTIAL and GAP stay mutually exclusive;
    an empty page is EMPTY_VALID (never GAP merely from an empty response).
    """

    def test_a_complete_trade_has_no_partial_flag(self) -> None:
        # fully in-window + has_more=false -> COMPLETE, clean flags.
        batch = _adapter(routes={"/get_last_trades_by_instrument": HAPPY_ROUTES["/get_last_trades_by_instrument"]}).fetch_trades(request(TRADE))
        assert batch.is_complete is True
        assert QualityFlagAcquisition.PARTIAL_INTERVAL not in batch.quality_flags
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags

    def test_b_complete_liquidation_source_page_clean(self) -> None:
        # source page fully in-window + terminal + forced event present.
        batch = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.LIQ_HAPPY)}).fetch_liquidations(request(LIQUIDATION))
        assert batch.is_complete is True
        assert batch.row_count == 1
        assert QualityFlagAcquisition.PARTIAL_INTERVAL not in batch.quality_flags
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags

    def test_c_partial_trade_has_more(self) -> None:
        # some rows in-window, terminal NOT proven (has_more=true).
        batch = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.TRADE_HAS_MORE_TRUE)}).fetch_trades(request(TRADE))
        assert batch.is_complete is False
        assert QualityFlagAcquisition.PARTIAL_INTERVAL in batch.quality_flags
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags

    def test_d_gap_trade_no_row_in_window(self) -> None:
        old = datetime(2020, 1, 1, tzinfo=UTC)
        batch = _adapter(routes={"/get_last_trades_by_instrument": HAPPY_ROUTES["/get_last_trades_by_instrument"]}).fetch_trades(request(TRADE, start=old))
        assert batch.is_complete is False
        assert QualityFlagAcquisition.GAP_DETECTED in batch.quality_flags
        assert QualityFlagAcquisition.PARTIAL_INTERVAL not in batch.quality_flags

    def test_e_liquidation_filter_trap_source_leak_never_complete(self) -> None:
        # raw source: ordinary trade OUTSIDE window + liquidation INSIDE window
        # + has_more=false.  Semantic output = the liquidation row only, but
        # SOURCE-PAGE coverage leaks outside the requested window -> the
        # filtered projection must NOT manufacture completeness (I08R1 Defect
        # C: projection is not coverage).
        adapter = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.LIQ_TRAP)})
        batch = adapter.fetch_liquidations(request(LIQUIDATION))
        assert batch.row_count == 1  # forced-liquidation row only
        assert batch.is_complete is False  # source coverage not wholly in-window
        assert batch.next_resume_token is None
        assert QualityFlagAcquisition.PARTIAL_INTERVAL in batch.quality_flags
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags

    def test_f_liquidation_ordinary_rows_never_leak(self) -> None:
        batch = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.LIQ_TRAP)}).fetch_liquidations(request(LIQUIDATION))
        raw = json.loads(batch.raw_payloads[0].raw_body.decode("utf-8"))
        # semantic row_count is the forced-liquidation subset only
        flagged = [r for r in raw["result"]["trades"] if r["liquidation"] == "liquidation"]
        assert batch.row_count == len(flagged) == 1

    def test_g_empty_liquidation_conservative(self) -> None:
        # nonempty source page with zero forced-liquidation rows -> EMPTY_VALID,
        # raw preserved, completion conservative (UNKNOWN).
        batch = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.LIQ_NO_EVENTS)}).fetch_liquidations(request(LIQUIDATION))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags
        assert batch.raw_payloads  # nonempty raw payload preserved
        assert batch.is_complete is False
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags


class TestFundingCompletionLimited:
    """I08R1 Defect B — funding terminal/exhaustive proof is NOT established.

    The short-page-under-cap rule is only a characterization heuristic; no
    committed artifact proves get_funding_rate_history returns ALL window
    records whenever len(result) < count.  Funding is therefore NEVER
    certified complete (completion_proof = LIMITED) — a short page is not
    terminal merely because it is short.
    """

    def test_funding_never_complete_even_under_cap(self) -> None:
        adapter = _adapter(routes={"/get_funding_rate_history": HAPPY_ROUTES["/get_funding_rate_history"]})
        batch = adapter.fetch_funding(request(FUNDING))
        assert batch.row_count == 3  # well under the 1000 cap
        assert batch.is_complete is False
        assert batch.next_resume_token is None
        assert QualityFlagAcquisition.PARTIAL_INTERVAL in batch.quality_flags
        assert QualityFlagAcquisition.GAP_DETECTED not in batch.quality_flags

    def test_funding_count_cap_page_never_complete(self) -> None:
        # a page AT the count cap (1000 rows) is never complete — no terminal
        # proof exists for funding regardless of page size.
        rows = [FX.funding_row(FX.T1 + i * 3_600_000) for i in range(1000)]
        body = FX._ok_result(rows)
        adapter = _adapter(routes={"/get_funding_rate_history": (200, body)})
        batch = adapter.fetch_funding(request(FUNDING))
        assert batch.row_count == 1000
        assert batch.is_complete is False
        assert batch.next_resume_token is None

    def test_funding_outside_window_never_complete(self) -> None:
        old = datetime(2020, 1, 1, tzinfo=UTC)
        batch = _adapter(routes={"/get_funding_rate_history": HAPPY_ROUTES["/get_funding_rate_history"]}).fetch_funding(
            request(FUNDING, start=old, end=old + timedelta(days=1))
        )
        assert batch.is_complete is False
        assert QualityFlagAcquisition.GAP_DETECTED in batch.quality_flags
        assert QualityFlagAcquisition.PARTIAL_INTERVAL not in batch.quality_flags


class TestTimestampUnits:
    def test_funding_convenience_dt_from_ms_int(self) -> None:
        batch = _adapter(
            routes={"/get_funding_rate_history": HAPPY_ROUTES["/get_funding_rate_history"]}
        ).fetch_funding(request(FUNDING))
        assert batch.actual_first_timestamp is not None
        assert batch.actual_last_timestamp is not None
        # epoch-ms int -> UTC datetime; timestamps in request are ms too
        assert batch.actual_first_timestamp.year == 2022

    def test_trade_ts_is_ms_int(self) -> None:
        batch = _adapter(routes={"/get_last_trades_by_instrument": HAPPY_ROUTES["/get_last_trades_by_instrument"]}).fetch_trades(request(TRADE))
        assert batch.actual_first_timestamp is not None

    def test_book_ts_is_ms_int(self) -> None:
        batch = _adapter(routes={"/get_order_book": HAPPY_ROUTES["/get_order_book"]}).fetch_book(request(BOOK))
        assert batch.actual_first_timestamp is not None

    def test_request_timestamps_are_ms_in_params(self) -> None:
        transport = FakeDeribitTransport(routes=HAPPY_ROUTES)
        adapter = DeribitAdapter(transport=transport)
        req = request(TRADE)
        adapter.fetch_trades(req)
        _, params = transport.calls[0]
        # request units are epoch MILLISECONDS (not seconds)
        assert params["start_timestamp"] == int(req.start_time.timestamp() * 1000)
        assert abs(params["start_timestamp"] - req.start_time.timestamp()) > 1


class TestEmptyValidDistinct:
    def test_empty_trade_is_explicit_empty_valid(self) -> None:
        batch = _adapter().fetch_trades(request(TRADE))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags
        assert batch.raw_payloads  # raw preserved even when empty

    def test_empty_liquidation_is_explicit_empty_valid(self) -> None:
        batch = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.LIQ_EMPTY)}).fetch_liquidations(request(LIQUIDATION))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags

    def test_empty_funding_is_explicit_empty_valid(self) -> None:
        batch = _adapter(routes={"/get_funding_rate_history": (200, FX.FUNDING_EMPTY)}).fetch_funding(request(FUNDING))
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags


class TestProviderErrorsStayTyped:
    def test_invalid_instrument_http_200_error_body(self) -> None:
        # JSON-RPC error on HTTP 200 is InvalidInstrument, never data/EMPTY_VALID
        adapter = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.ERROR_INVALID_INSTRUMENT)})
        with pytest.raises(InvalidInstrument) as excinfo:
            adapter.fetch_trades(request(TRADE))
        assert excinfo.value.failure_type == "InvalidInstrument"

    def test_http_429_rate_limited(self) -> None:
        adapter = _adapter(routes={"/get_funding_rate_history": FX.SCENARIOS_FUNDING["rate_limit"]})
        with pytest.raises(RateLimited):
            adapter.fetch_funding(request(FUNDING))

    def test_auth_code_authentication_required(self) -> None:
        adapter = _adapter(routes={"/get_last_trades_by_instrument": (200, FX.ERROR_AUTH)})
        with pytest.raises(AuthenticationRequired):
            adapter.fetch_trades(request(TRADE))

    def test_http_500_provider_unavailable(self) -> None:
        adapter = _adapter(routes={"/get_order_book": FX.SCENARIOS_BOOK["provider_error"]})
        with pytest.raises(ProviderUnavailable):
            adapter.fetch_book(request(BOOK))

    def test_endpoint_removed_is_typed_error(self) -> None:
        adapter = _adapter(routes={"/get_funding_rate_history": (200, FX.ERROR_ENDPOINT_REMOVED)})
        with pytest.raises(ProviderSemanticError):
            adapter.fetch_funding(request(FUNDING))


class TestRawHashDeterministic:
    def test_identical_payload_identical_hash(self) -> None:
        a = _adapter(routes={"/get_last_trades_by_instrument": HAPPY_ROUTES["/get_last_trades_by_instrument"]}).fetch_trades(request(TRADE))
        b = _adapter(routes={"/get_last_trades_by_instrument": HAPPY_ROUTES["/get_last_trades_by_instrument"]}).fetch_trades(request(TRADE))
        assert a.raw_payloads[0].content_hash == b.raw_payloads[0].content_hash


class TestSchemaDriftRawEnvelope:
    def _drift_routes(self) -> dict[str, Any]:
        return {
            "/get_last_trades_by_instrument": FX.SCENARIOS_TRADE["bad_timestamp"],
            "/get_funding_rate_history": FX.SCENARIOS_FUNDING["bad_timestamp"],
            "/get_order_book": FX.SCENARIOS_BOOK["bad_timestamp"],
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
            caps = build_deribit_capabilities()
            ref = caps.capability_for(sensor).probe_evidence_ref
            assert ref is not None
            assert envelope.evidence_ref == ref
            assert ref.evidence_id in caps.capability_for(sensor).evidence_basis

    def test_drift_blocks_parsed_output(self) -> None:
        adapter = _adapter(routes={"/get_order_book": FX.SCENARIOS_BOOK["bad_timestamp"]})
        with pytest.raises(SchemaDrift):
            adapter.fetch_book(request(BOOK))


class TestInstrumentScopeSeparation:
    def test_probe_only_symbols_fail_every_promoted_sensor(self) -> None:
        for sensor in ALL_PROMOTED:
            for symbol in ("ETH-PERPETUAL", "SOL-PERPETUAL"):
                transport = FakeDeribitTransport(routes=HAPPY_ROUTES)
                adapter = DeribitAdapter(transport=transport)
                with pytest.raises(InvalidInstrument):
                    dispatch_fetch(adapter, request(sensor, native_instrument_id=symbol))
                assert transport.calls == []

    def test_btc_perpetual_passes(self) -> None:
        batch = _adapter(routes={"/get_order_book": HAPPY_ROUTES["/get_order_book"]}).fetch_book(request(BOOK))
        assert batch.native_instrument_id == "BTC-PERPETUAL"


class TestRequestProviderIdentity:
    def test_foreign_provider_reports_requested_sensor_all_four(self) -> None:
        for sensor in ALL_PROMOTED:
            transport = FakeDeribitTransport(routes=HAPPY_ROUTES)
            adapter = DeribitAdapter(transport=transport)
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


class TestNoTransportSensorIdentity:
    def test_all_four_sensors_report_correct_sensor(self) -> None:
        for sensor in ALL_PROMOTED:
            adapter = DeribitAdapter()  # no transport
            with pytest.raises(ProviderUnavailable) as excinfo:
                dispatch_fetch(adapter, request(sensor))
            assert excinfo.value.sensor_family is sensor, sensor


class TestNoForbiddenPaths:
    def test_book_never_historical(self) -> None:
        builder = DeribitRequestBuilder()
        url, params = builder.build(request(BOOK))
        assert "/get_order_book" in url
        for forbidden in ("start", "end", "start_timestamp", "end_timestamp", "count"):
            assert forbidden not in params

    def test_funding_uses_single_rate_history_route(self) -> None:
        builder = DeribitRequestBuilder()
        url, _ = builder.build(request(FUNDING))
        assert "/get_funding_rate_history" in url
        assert "/get_last_trades_by_instrument" not in url


class TestNativeMethodGuardsUnpromoted:
    def test_fetch_open_interest_mismatch_not_false_unsupported(self) -> None:
        transport = FakeDeribitTransport()
        adapter = DeribitAdapter(transport=transport)
        with pytest.raises(ProviderSemanticError) as excinfo:
            adapter.fetch_open_interest(request(FUNDING))
        assert excinfo.value.sensor_family is FUNDING


class TestProductionCandidateConformance:
    def test_full_conformance_passes_with_real_adapter(self) -> None:
        # empty-valid: liquidation via default empty trades envelope; fetch:
        # trade happy.
        routes = {
            "/get_last_trades_by_instrument": HAPPY_ROUTES["/get_last_trades_by_instrument"],
        }
        adapter = _adapter(routes=routes)
        promoted = capabilities_from_promotion(
            "DERIBIT", load_promotion_candidates()
        )
        under_test = AdapterUnderTest(
            adapter=adapter,
            registry_policy=DEFAULT_FREE_ONLY_POLICY,
            auth_mode=AdapterAuthMode.NO_AUTH,
            promoted_capabilities=promoted,
            native_evidence=deribit_native_evidence(),
            empty_valid_request=request(LIQUIDATION),
            unsupported_request=request(SensorFamily.MECHANICAL_OPEN_INTEREST),
            fetch_request=request(TRADE),
            mode=AdapterConformanceMode.PRODUCTION_CANDIDATE,
        )
        results = run_conformance_suite(under_test)
        failed = [r for r in results if not r.passed]
        assert not failed, "\n".join(f"{r.check_id}: {r.detail}" for r in failed)
        summary = summarize_conformance(results)
        assert summary["failed"] == 0

    def test_exact_i14_set_via_capabilities(self) -> None:
        caps = build_deribit_capabilities()
        assert set(caps.supported_sensors()) == set(ALL_PROMOTED)


class TestRetryClassification:
    def test_retryability_of_typed_failures(self) -> None:
        assert classify_retryability(RateLimited(PROVIDER_ID, TRADE)) is Retryability.RETRYABLE
        assert classify_retryability(ProviderUnavailable(PROVIDER_ID, TRADE)) is Retryability.RETRYABLE
        assert classify_retryability(InvalidInstrument(PROVIDER_ID, TRADE)) is Retryability.TERMINAL
        assert classify_retryability(AuthenticationRequired(PROVIDER_ID, TRADE)) is Retryability.TERMINAL
        assert classify_retryability(SchemaDrift(PROVIDER_ID, TRADE)) is Retryability.TERMINAL
