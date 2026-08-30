"""SENSOR-B3-I05 — Kraken request-contract golden tests.

Freezes, per promoted sensor, the Market Analytics URL + parameter shape:

    host/path:/api/charts/v1/analytics/{symbol}/{analytics_type}
    since/to in EPOCH SECONDS, interval explicit in seconds

No canonical asset id at the provider boundary; native symbol preserved.
"""

from __future__ import annotations

from datetime import UTC, datetime

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.providers.base.fingerprint import fingerprint_request
from crypto_sensor_fabric.providers.kraken import KrakenAnalyticsRequestBuilder

from ._fake import request

BUILDER = KrakenAnalyticsRequestBuilder()

GRAPH = {
    SensorFamily.MECHANICAL_OPEN_INTEREST: ("open-interest", "open-interest"),
    SensorFamily.MECHANICAL_FUNDING: ("funding", "funding"),
    SensorFamily.MECHANICAL_BASIS: ("future-basis", "future-basis"),
    SensorFamily.MECHANICAL_POSITIONING: ("long-short-ratio", "long-short-ratio"),
    SensorFamily.MECHANICAL_BOOK_METRIC: ("orderbook", "orderbook"),
    SensorFamily.MECHANICAL_LIQUIDATION: ("liquidation-volume", "liquidation-volume"),
}


class TestRequestContracts:
    def test_url_contract_per_promoted_sensor(self) -> None:
        for sensor, (type_label, analytics_type) in GRAPH.items():
            url, params = BUILDER.build(request(sensor))
            assert url.startswith("https://futures.kraken.com/api/charts/v1/analytics/")
            assert f"/{analytics_type}" in url
            assert url.endswith(f"/PI_XBTUSD/{analytics_type}")
            # epoch SECONDS since/to
            assert params["since"] == int(NOW_TS)
            assert params["to"] == int(NOW_TS + 3600)

    def test_interval_explicit_default(self) -> None:
        url, params = BUILDER.build(request(SensorFamily.MECHANICAL_FUNDING))
        assert params["interval"] == 3600

    def test_interval_from_granularity(self) -> None:
        req = request(SensorFamily.MECHANICAL_FUNDING)
        url = BUILDER.build_url(SensorFamily.MECHANICAL_FUNDING, "PI_XBTUSD")
        assert "funding" in url
        # granularity-driven interval resolution
        req = req.model_copy(deep=True)
        # model_copy cannot set enum safely; use a typed rebuild via model_validate
        from crypto_sensor_fabric.providers.base.models import FetchRequest

        data = req.model_dump()
        data["granularity"] = Granularity.G1M.value
        rebuilt = FetchRequest.model_validate(data)
        _, params = BUILDER.build(rebuilt)
        assert params["interval"] == 60

    def test_native_symbol_preserved(self) -> None:
        url, _ = BUILDER.build(request(SensorFamily.MECHANICAL_OPEN_INTEREST, "PI_ETHUSD"))
        assert "PI_ETHUSD/open-interest" in url
        assert "btcusd" not in url.lower()

    def test_no_invented_endpoint(self) -> None:
        for sensor in (
            SensorFamily.MECHANICAL_TRADE,
            SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
        ):
            try:
                BUILDER.build(request(sensor))
            except ValueError:
                pass
            else:
                assert False, f"unpromoted {sensor.value} got a builder"

    def test_endpoint_family_identity(self) -> None:
        assert BUILDER.endpoint_family(SensorFamily.MECHANICAL_OPEN_INTEREST) == "kraken-market-analytics/open-interest"
        assert BUILDER.endpoint_family(SensorFamily.MECHANICAL_LIQUIDATION) == "kraken-market-analytics/liquidation-volume"

    def test_resume_round_trip_reissues_since(self) -> None:
        from crypto_sensor_fabric.providers.base.enums import PaginationMode
        from crypto_sensor_fabric.providers.base.models import ResumeToken

        token = ResumeToken(
            mode=PaginationMode.TIME_RANGE,
            page_number=1,
            provider_native_state={"since": 1754870400, "symbol": "PI_XBTUSD"},
        )
        rebuilt = ResumeToken.model_validate_json(token.model_dump_json())
        assert rebuilt == token
        req = request(SensorFamily.MECHANICAL_OPEN_INTEREST, request_id="r2").model_copy(
            update={"resume_token": rebuilt}
        )
        _, params = BUILDER.build(req)
        # result.more -> re-issue since at the oldest bucket (evidence-backed)
        assert params["since"] == 1754870400
        assert params["to"] == int(NOW_TS + 3600)
        assert params["interval"] == 3600

    def test_fingerprint_deterministic_and_semantic(self) -> None:
        r1 = request(SensorFamily.MECHANICAL_BASIS)
        url, params = BUILDER.build(r1)
        fp1 = fingerprint_request(r1, BUILDER.endpoint_family(SensorFamily.MECHANICAL_BASIS), params)
        url2, params2 = BUILDER.build(r1)
        fp2 = fingerprint_request(r1, BUILDER.endpoint_family(SensorFamily.MECHANICAL_BASIS), params2)
        assert fp1 == fp2
        # material semantic change (sensor) -> different fingerprint
        rd = request(SensorFamily.MECHANICAL_POSITIONING)
        _, pd = BUILDER.build(rd)
        fpd = fingerprint_request(rd, BUILDER.endpoint_family(SensorFamily.MECHANICAL_POSITIONING), pd)
        assert fpd != fp1


# Epoch of the shared fixture NOW (2026-01-01T00:00:00Z)
NOW_TS = int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())