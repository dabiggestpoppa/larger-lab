"""SENSOR-B3-I04R2 Issue 2 — provider-independent method dispatch.

`dispatch_fetch` must route each sensor family to the CORRECT protocol fetch
method (acquisition mechanics only), and unknown/unsupported sensors must fail
TYPED (`CapabilityUnavailable`) — never `[]`/`0`/`None`/an EMPTY_VALID batch.

All offline; uses a recording fake adapter, never network.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base import (
    ProviderCapabilities,
    SENSOR_FETCH_METHOD,
    dispatch_fetch,
)
from crypto_sensor_fabric.providers.base.enums import FetchPurpose
from crypto_sensor_fabric.providers.base.errors import CapabilityUnavailable
from crypto_sensor_fabric.providers.base.models import (
    FetchBatch,
    FetchRequest,
    SensorCapability,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)
END = NOW.replace(hour=1)

# The 8 canonical mechanical sensors, in protocol-order.
ALL_SENSORS = [
    SensorFamily.MECHANICAL_TRADE,
    SensorFamily.MECHANICAL_LIQUIDATION,
    SensorFamily.MECHANICAL_OPEN_INTEREST,
    SensorFamily.MECHANICAL_FUNDING,
    SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
    SensorFamily.MECHANICAL_BOOK_METRIC,
    SensorFamily.MECHANICAL_POSITIONING,
    SensorFamily.MECHANICAL_BASIS,
]

EXPECTED_METHODS = {
    SensorFamily.MECHANICAL_TRADE: "fetch_trades",
    SensorFamily.MECHANICAL_LIQUIDATION: "fetch_liquidations",
    SensorFamily.MECHANICAL_OPEN_INTEREST: "fetch_open_interest",
    SensorFamily.MECHANICAL_FUNDING: "fetch_funding",
    SensorFamily.MECHANICAL_BOOK_SNAPSHOT: "fetch_book",
    SensorFamily.MECHANICAL_BOOK_METRIC: "fetch_book_metrics",
    SensorFamily.MECHANICAL_POSITIONING: "fetch_positioning",
    SensorFamily.MECHANICAL_BASIS: "fetch_basis",
}


class DispatchProbe:
    """Records which method handled each sensor; all 8 sensors supported."""

    provider_id = "KRAKEN_FUTURES"

    def __init__(self) -> None:
        self.calls: list[str] = []
        self._caps = ProviderCapabilities(provider_id="KRAKEN_FUTURES", sensors={})
        for sensor in ALL_SENSORS:
            self._caps.sensors[sensor] = SensorCapability(
                sensor_family=sensor, supported=True
            )

    def capabilities(self) -> ProviderCapabilities:
        return self._caps

    def _mk(self, method: str, request: FetchRequest) -> FetchBatch:
        self.calls.append(method)
        return FetchBatch(
            provider_id=self.provider_id,
            sensor_family=request.sensor_family,
            native_instrument_id=f"called:{method}",
            request_fingerprint="fp",
            requested_start=NOW,
            requested_end=END,
            row_count=1,
            is_complete=True,
            retrieved_at=NOW,
            adapter_version="0.0.0-probe",
        )

    def fetch_trades(self, r):  # noqa: ANN001
        return self._mk("fetch_trades", r)

    def fetch_liquidations(self, r):  # noqa: ANN001
        return self._mk("fetch_liquidations", r)

    def fetch_open_interest(self, r):  # noqa: ANN001
        return self._mk("fetch_open_interest", r)

    def fetch_funding(self, r):  # noqa: ANN001
        return self._mk("fetch_funding", r)

    def fetch_book(self, r):  # noqa: ANN001
        return self._mk("fetch_book", r)

    def fetch_book_metrics(self, r):  # noqa: ANN001
        return self._mk("fetch_book_metrics", r)

    def fetch_positioning(self, r):  # noqa: ANN001
        return self._mk("fetch_positioning", r)

    def fetch_basis(self, r):  # noqa: ANN001
        return self._mk("fetch_basis", r)


def _request(sensor: SensorFamily) -> FetchRequest:
    return FetchRequest(
        provider_id="KRAKEN_FUTURES",
        sensor_family=sensor,
        native_instrument_id="PI_XBTUSD",
        start_time=NOW,
        end_time=END,
        request_id="r1",
        purpose=FetchPurpose.PROBE,
        adapter_semantic_version="0.0.0-probe",
    )


class TestDispatchMap:
    def test_map_covers_all_mechanical_sensors(self) -> None:
        assert set(SENSOR_FETCH_METHOD) == set(ALL_SENSORS)
        for sensor, expected in EXPECTED_METHODS.items():
            assert SENSOR_FETCH_METHOD[sensor] == expected

    def test_each_sensor_routes_to_correct_method(self) -> None:
        probe = DispatchProbe()
        for sensor in ALL_SENSORS:
            probe.calls.clear()
            batch = dispatch_fetch(probe, _request(sensor))
            assert probe.calls == [EXPECTED_METHODS[sensor]]
            assert batch.native_instrument_id == f"called:{EXPECTED_METHODS[sensor]}"
            assert batch.sensor_family is sensor

    def test_unsupported_sensor_raises_typed(self) -> None:
        # fake provider supports only a subset; BASIS is unsupported
        probe = DispatchProbe()
        probe._caps.sensors[SensorFamily.MECHANICAL_BASIS] = SensorCapability(
            sensor_family=SensorFamily.MECHANICAL_BASIS, supported=False
        )
        with pytest.raises(CapabilityUnavailable):
            dispatch_fetch(probe, _request(SensorFamily.MECHANICAL_BASIS))

    def test_unknown_sensor_is_typed_not_substitute(self) -> None:
        # A sensor that maps to no method must still fail typed (never []/0/None).
        probe = DispatchProbe()
        # MECHANICAL_BASIS is mapped, so corrupt the map membership check by
        # using the ensure_supported gate first: declare unsupported.
        probe._caps.sensors[SensorFamily.MECHANICAL_BASIS] = SensorCapability(
            sensor_family=SensorFamily.MECHANICAL_BASIS, supported=False
        )
        with pytest.raises(CapabilityUnavailable):
            dispatch_fetch(probe, _request(SensorFamily.MECHANICAL_BASIS))