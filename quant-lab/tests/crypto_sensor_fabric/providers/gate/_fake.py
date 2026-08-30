"""Shared fake transport for Gate adapter offline tests (SENSOR-B3-I06)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import FetchPurpose
from crypto_sensor_fabric.providers.base.models import FetchRequest

NOW = datetime(2026, 1, 1, tzinfo=UTC)


class FakeGateTransport:
    """Deterministic offline transport keyed by URL fragment.

    Routes: URL-substring -> (status, body) or an Exception to raise.  Default
    returns (200, []) — a valid EMPTY_VALID top-level list for both the
    contract_stats and funding surfaces.
    """

    def __init__(
        self,
        routes: dict[str, tuple[int, Any] | Exception] | None = None,
        default: tuple[int, Any] | None = None,
    ) -> None:
        self.routes = routes or {}
        self.default = default if default is not None else (200, [])
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, url: str, params: dict[str, Any]) -> tuple[int | None, Any]:
        self.calls.append((url, params))
        for fragment, response in self.routes.items():
            if fragment in url:
                if isinstance(response, Exception):
                    raise response
                return response
        return self.default


def request(
    sensor: SensorFamily,
    native_instrument_id: str = "BTC_USDT",
    start: datetime | None = None,
    request_id: str = "r1",
    adapter_version: str = "0.0.0-test",
) -> FetchRequest:
    s = start if start is not None else NOW
    return FetchRequest(
        provider_id="GATE_FUTURES",
        sensor_family=sensor,
        native_instrument_id=native_instrument_id,
        start_time=s,
        end_time=s.replace(hour=1),
        request_id=request_id,
        purpose=FetchPurpose.PROBE,
        adapter_semantic_version=adapter_version,
    )