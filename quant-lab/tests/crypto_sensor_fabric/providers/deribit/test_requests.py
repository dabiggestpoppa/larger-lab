"""SENSOR-B3-I08B — Deribit request builder tests.

Focus: native request contracts per promoted sensor — trade/liquidation share
`get_last_trades_by_instrument` (instrument_name + start/end epoch-ms +
count<=1000 + include_old=true), funding uses `get_funding_rate_history`
(start/end epoch-ms + count), book is the current-only `get_order_book`
snapshot (depth=25, no historical cursor).  Granularity is fail-closed per
sensor.
"""

from __future__ import annotations

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.providers.base.errors import UnsupportedGranularity
from crypto_sensor_fabric.providers.deribit import (
    DeribitRequestBuilder,
    deribit_endpoint_family,
)

from ._fake import request

BOOK = SensorFamily.MECHANICAL_BOOK_SNAPSHOT
FUNDING = SensorFamily.MECHANICAL_FUNDING
LIQUIDATION = SensorFamily.MECHANICAL_LIQUIDATION
TRADE = SensorFamily.MECHANICAL_TRADE

BUILDER = DeribitRequestBuilder()


class TestTradeRequest:
    def test_path_and_params(self) -> None:
        url, params = BUILDER.build(request(TRADE))
        assert url == "https://www.deribit.com/api/v2/public/get_last_trades_by_instrument"
        assert params["instrument_name"] == "BTC-PERPETUAL"
        assert params["count"] == 1000
        assert params["include_old"] is True  # REQUIRED for historical depth
        # start/end are provider-native epoch MILLISECONDS
        assert params["start_timestamp"] == int(request(TRADE).start_time.timestamp() * 1000)
        assert params["end_timestamp"] == int(request(TRADE).end_time.timestamp() * 1000)

    def test_granularity_raw_event_accepted(self) -> None:
        req = request(TRADE).model_copy(update={"granularity": Granularity.RAW_EVENT})
        BUILDER.build(req)

    def test_bar_granularity_rejected(self) -> None:
        for g in (Granularity.G1H, Granularity.G1D):
            req = request(TRADE).model_copy(update={"granularity": g})
            with pytest.raises(UnsupportedGranularity):
                BUILDER.build(req)


class TestLiquidationRequest:
    def test_same_physical_surface_distinct_sensor(self) -> None:
        url, params = BUILDER.build(request(LIQUIDATION))
        assert url == "https://www.deribit.com/api/v2/public/get_last_trades_by_instrument"
        assert params["instrument_name"] == "BTC-PERPETUAL"
        assert params["include_old"] is True
        assert params["count"] == 1000

    def test_granularity_raw_event_accepted(self) -> None:
        req = request(LIQUIDATION).model_copy(update={"granularity": Granularity.RAW_EVENT})
        BUILDER.build(req)

    def test_bar_granularity_rejected(self) -> None:
        req = request(LIQUIDATION).model_copy(update={"granularity": Granularity.G1H})
        with pytest.raises(UnsupportedGranularity):
            BUILDER.build(req)


class TestFundingRequest:
    def test_path_and_params(self) -> None:
        url, params = BUILDER.build(request(FUNDING))
        assert url == "https://www.deribit.com/api/v2/public/get_funding_rate_history"
        assert params["instrument_name"] == "BTC-PERPETUAL"
        assert params["count"] == 1000
        # no invented interval query param (hourly records, no resampling)
        assert "interval" not in params

    def test_granularity_none_and_1h_accepted(self) -> None:
        BUILDER.build(request(FUNDING))
        req = request(FUNDING).model_copy(update={"granularity": Granularity.G1H})
        BUILDER.build(req)

    def test_unsupported_granularity_rejected(self) -> None:
        for g in (Granularity.G1D, Granularity.RAW_EVENT):
            req = request(FUNDING).model_copy(update={"granularity": g})
            with pytest.raises(UnsupportedGranularity):
                BUILDER.build(req)


class TestBookRequest:
    def test_path_and_params_current_only(self) -> None:
        url, params = BUILDER.build(request(BOOK))
        assert url == "https://www.deribit.com/api/v2/public/get_order_book"
        assert params["instrument_name"] == "BTC-PERPETUAL"
        assert params["depth"] == 25
        # current-only: NO historical/start/end/cursor params
        for forbidden in ("start", "end", "start_timestamp", "end_timestamp", "count"):
            assert forbidden not in params, forbidden

    def test_granularity_book_snapshot_accepted(self) -> None:
        req = request(BOOK).model_copy(update={"granularity": Granularity.BOOK_SNAPSHOT})
        BUILDER.build(req)

    def test_unsupported_granularity_rejected(self) -> None:
        for g in (Granularity.G1H, Granularity.RAW_EVENT):
            req = request(BOOK).model_copy(update={"granularity": g})
            with pytest.raises(UnsupportedGranularity):
                BUILDER.build(req)


class TestEndpointFamily:
    def test_endpoint_families(self) -> None:
        assert deribit_endpoint_family(TRADE) == "deribit-get-last-trades-by-instrument"
        assert deribit_endpoint_family(LIQUIDATION) == "deribit-get-last-trades-by-instrument"
        assert deribit_endpoint_family(FUNDING) == "deribit-get-funding-rate-history"
        assert deribit_endpoint_family(BOOK) == "deribit-get-order-book"

    def test_no_builder_for_unsupported_sensor(self) -> None:
        with pytest.raises(ValueError):
            BUILDER.build(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
