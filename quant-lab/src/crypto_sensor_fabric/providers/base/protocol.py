"""Common provider adapter protocol (01 §3).

`MechanicalProviderAdapter` is the provider-independent acquisition boundary.
Every future provider adapter (Kraken/Gate/OKX/Deribit) implements it and must
pass the common conformance suite (SENSOR-B3-I04).

Contract:

- `provider_id` is immutable per instance.
- `capabilities()` returns sensor-specific capabilities (never a global flag).
- Unsupported sensors return a TYPED `CapabilityUnavailable`, never `[]` / `0`
  / `None` as an ambiguous substitute.
- No canonical identity/unit resolution happens here (Bloc 4/5).
- No research-layer imports, ever (01 §24).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...contracts.enums import SensorFamily
from .errors import CapabilityUnavailable
from .models import (
    FetchBatch,
    FetchRequest,
    InstrumentListRequest,
    InstrumentListResult,
    ProviderCapabilities,
)


@runtime_checkable
class MechanicalProviderAdapter(Protocol):
    """The frozen common adapter protocol (01 §3)."""

    provider_id: str

    def capabilities(self) -> ProviderCapabilities:
        """Sensor-specific capability declaration for this adapter."""
        ...

    def list_instruments(
        self, request: InstrumentListRequest
    ) -> InstrumentListResult:
        """Discover native instrument IDs offered by the provider."""
        ...

    def fetch_trades(self, request: FetchRequest) -> FetchBatch:
        """Acquire trade/order-flow evidence (raw, native)."""
        ...

    def fetch_liquidations(self, request: FetchRequest) -> FetchBatch:
        """Acquire liquidation evidence (native shape preserved)."""
        ...

    def fetch_open_interest(self, request: FetchRequest) -> FetchBatch:
        """Acquire open-interest evidence (native unit preserved)."""
        ...

    def fetch_funding(self, request: FetchRequest) -> FetchBatch:
        """Acquire funding evidence (native interval/rate preserved)."""
        ...

    def fetch_book(self, request: FetchRequest) -> FetchBatch:
        """Acquire order-book snapshot evidence."""
        ...

    def fetch_book_metrics(self, request: FetchRequest) -> FetchBatch:
        """Acquire provider-native book metrics (spread/depth/liquidity)."""
        ...

    def fetch_positioning(self, request: FetchRequest) -> FetchBatch:
        """Acquire positioning evidence (public market-wide where available)."""
        ...

    def fetch_basis(self, request: FetchRequest) -> FetchBatch:
        """Acquire basis evidence (provider-native representation)."""
        ...


def ensure_supported(adapter: MechanicalProviderAdapter, sensor: SensorFamily) -> None:
    """Gate a fetch call on the declared capability (typed failure otherwise)."""
    capabilities = adapter.capabilities()
    capability = capabilities.capability_for(sensor)
    if not capability.supported:
        raise CapabilityUnavailable(
            provider_id=adapter.provider_id,
            sensor_family=sensor,
            detail=f"{sensor.value} is not a supported capability of {adapter.provider_id}",
        )
