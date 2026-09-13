"""SENSOR-B3-I06 — Gate request-builder contract tests.

Proves the exact contract_stats / funding_rate request shapes: paths, native
`contract`, from/to units, string `interval`, no invented `to`, no private
/positions, no plural /funding_rates, and fail-closed granularity.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.providers.base.errors import UnsupportedGranularity
from crypto_sensor_fabric.providers.gate import (
    GATE_CONTRACT_STATS_DEFAULT_LIMIT,
    GATE_INTERVAL_1H,
    GateRequestBuilder,
)

from ._fake import request

CONTRACT_STATS_URL = "https://api.gateio.ws/api/v4/futures/usdt/contract_stats"
FUNDING_RATE_URL = "https://api.gateio.ws/api/v4/futures/usdt/funding_rate"

CONTRACT_STATS_SENSORS = (
    SensorFamily.MECHANICAL_OPEN_INTEREST,
    SensorFamily.MECHANICAL_LIQUIDATION,
    SensorFamily.MECHANICAL_POSITIONING,
)


class TestContractStatsRequest:
    def test_path_and_native_contract(self) -> None:
        for sensor in CONTRACT_STATS_SENSORS:
            url, params = GateRequestBuilder().build(request(sensor))
            assert url == CONTRACT_STATS_URL
            assert params["contract"] == "BTC_USDT"

    def test_from_is_epoch_seconds(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        url, params = GateRequestBuilder().build(request(SensorFamily.MECHANICAL_OPEN_INTEREST, start=start))
        assert params["from"] == int(start.timestamp())
        # seconds, NOT milliseconds
        assert params["from"] == 1767225600

    def test_no_invented_to(self) -> None:
        for sensor in CONTRACT_STATS_SENSORS:
            url, params = GateRequestBuilder().build(request(sensor))
            assert "to" not in params, sensor

    def test_interval_is_provider_string_bucket(self) -> None:
        for sensor in CONTRACT_STATS_SENSORS:
            url, params = GateRequestBuilder().build(request(sensor))
            assert params["interval"] == "1h"  # STRING bucket, never 3600

    def test_limit_present_and_configurable(self) -> None:
        url, params = GateRequestBuilder().build(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert params["limit"] == GATE_CONTRACT_STATS_DEFAULT_LIMIT
        url, params = GateRequestBuilder().build(
            request(SensorFamily.MECHANICAL_OPEN_INTEREST).model_copy(
                update={"page_size_hint": 500}
            )
        )
        assert params["limit"] == 500

    def test_granularity_none_defaults_to_1h(self) -> None:
        url, params = GateRequestBuilder().build(request(SensorFamily.MECHANICAL_OPEN_INTEREST))
        assert params["interval"] == GATE_INTERVAL_1H

    def test_granularity_g1h_maps_to_string_bucket(self) -> None:
        url, params = GateRequestBuilder().build(
            request(SensorFamily.MECHANICAL_OPEN_INTEREST).model_copy(
                update={"granularity": Granularity.G1H}
            )
        )
        assert params["interval"] == "1h"

    @pytest.mark.parametrize(
        "granularity",
        [
            Granularity.G1M,
            Granularity.G5M,
            Granularity.G15M,
            Granularity.G4H,
            Granularity.G1D,
            Granularity.RAW_EVENT,
            Granularity.BOOK_SNAPSHOT,
        ],
    )
    def test_unsupported_granularity_fails_typed(self, granularity: Granularity) -> None:
        builder = GateRequestBuilder()
        for sensor in CONTRACT_STATS_SENSORS:
            with pytest.raises(UnsupportedGranularity) as excinfo:
                builder.build(
                    request(sensor).model_copy(update={"granularity": granularity})
                )
            assert excinfo.value.sensor_family is sensor

    def test_no_private_positions_path(self) -> None:
        # the only URL the builder can emit for contract_stats sensors
        url, _ = GateRequestBuilder().build(request(SensorFamily.MECHANICAL_POSITIONING))
        assert "/positions" not in url


class TestFundingRateRequest:
    def test_path_and_native_contract(self) -> None:
        url, params = GateRequestBuilder().build(request(SensorFamily.MECHANICAL_FUNDING))
        assert url == FUNDING_RATE_URL
        assert params["contract"] == "BTC_USDT"

    def test_from_to_epoch_seconds(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        req = request(SensorFamily.MECHANICAL_FUNDING, start=start)
        url, params = GateRequestBuilder().build(req)
        assert params["from"] == int(start.timestamp())
        assert params["to"] == int(req.end_time.timestamp())

    def test_no_invented_interval(self) -> None:
        url, params = GateRequestBuilder().build(request(SensorFamily.MECHANICAL_FUNDING))
        assert "interval" not in params

    def test_granularity_none_or_g1h_no_interval(self) -> None:
        for g in (None, Granularity.G1H):
            req = request(SensorFamily.MECHANICAL_FUNDING)
            if g is not None:
                req = req.model_copy(update={"granularity": g})
            url, params = GateRequestBuilder().build(req)
            assert "interval" not in params

    def test_unsupported_granularity_fails_typed(self) -> None:
        for granularity in (Granularity.G5M, Granularity.RAW_EVENT, Granularity.BOOK_SNAPSHOT):
            with pytest.raises(UnsupportedGranularity) as excinfo:
                GateRequestBuilder().build(
                    request(SensorFamily.MECHANICAL_FUNDING).model_copy(
                        update={"granularity": granularity}
                    )
                )
            assert excinfo.value.sensor_family is SensorFamily.MECHANICAL_FUNDING

    def test_no_plural_funding_rates_path(self) -> None:
        url, _ = GateRequestBuilder().build(request(SensorFamily.MECHANICAL_FUNDING))
        assert "funding_rates" not in url  # plural batch route never used
        assert "/funding_rate" in url


class TestRequestFingerprintAuthoritative:
    def test_builder_never_scatters_urls(self) -> None:
        # endpoints are centralized in the request builder alone
        b = GateRequestBuilder()
        assert b.endpoint_family(SensorFamily.MECHANICAL_FUNDING) == "gate-futures-funding_rate"
        for sensor in CONTRACT_STATS_SENSORS:
            assert b.endpoint_family(sensor) == "gate-futures-contract_stats"
        with pytest.raises(ValueError):
            b.build(request(SensorFamily.MECHANICAL_TRADE))