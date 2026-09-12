"""SENSOR-B3-I07B — OKX request builder tests.

Focus: native request contracts per promoted sensor — trade uses
`/api/v5/market/history-trades` (trade-id cursors, single window), funding uses
the PUBLIC `/api/v5/public/funding-rate-history` (never /market), book is the
current-only `/api/v5/market/books` snapshot with `sz` and no historical
cursor.  Granularity is fail-closed per sensor.
"""

from __future__ import annotations

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.providers.base.errors import UnsupportedGranularity
from crypto_sensor_fabric.providers.okx import (
    OkxRequestBuilder,
    okx_endpoint_family,
)

from ._fake import request

BOOK = SensorFamily.MECHANICAL_BOOK_SNAPSHOT
FUNDING = SensorFamily.MECHANICAL_FUNDING
TRADE = SensorFamily.MECHANICAL_TRADE

BUILDER = OkxRequestBuilder()


class TestTradeRequest:
    def test_path_and_params(self) -> None:
        url, params = BUILDER.build(request(TRADE))
        assert url == "https://www.okx.com/api/v5/market/history-trades"
        assert params["instId"] == "BTC-USDT-SWAP"
        assert params["limit"] == 100
        # single evidence-backed window — no invented after/before cursor
        assert "after" not in params
        assert "before" not in params

    def test_granularity_raw_event_accepted(self) -> None:
        req = request(TRADE).model_copy(update={"granularity": Granularity.RAW_EVENT})
        BUILDER.build(req)

    def test_bar_granularity_rejected(self) -> None:
        for g in (Granularity.G1H, Granularity.G1D):
            req = request(TRADE).model_copy(update={"granularity": g})
            with pytest.raises(UnsupportedGranularity):
                BUILDER.build(req)


class TestFundingRequest:
    def test_path_and_params_public_namespace(self) -> None:
        url, params = BUILDER.build(request(FUNDING))
        assert url == "https://www.okx.com/api/v5/public/funding-rate-history"
        assert "public/funding-rate-history" in url
        # NEVER composed as /api/v5/market/funding-rate-history
        assert "/api/v5/market/funding-rate-history" not in url
        assert params["instId"] == "BTC-USDT-SWAP"
        assert params["limit"] == 100
        # no invented interval query param
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
        assert url == "https://www.okx.com/api/v5/market/books"
        assert params["instId"] == "BTC-USDT-SWAP"
        assert params["sz"] == 400
        # current-only: NO historical/start/end/after/before cursor
        for forbidden in ("start", "end", "after", "before"):
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
        assert okx_endpoint_family(TRADE) == "okx-swap-history-trades"
        assert okx_endpoint_family(FUNDING) == "okx-swap-funding-rate-history"
        assert okx_endpoint_family(BOOK) == "okx-swap-market-books"

    def test_no_builder_for_unsupported_sensor(self) -> None:
        with pytest.raises(ValueError):
            BUILDER.build(request(SensorFamily.MECHANICAL_LIQUIDATION))