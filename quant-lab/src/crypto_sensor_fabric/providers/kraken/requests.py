"""Kraken Market Analytics request builders (SENSOR-B3-I05).

An explicit, per-sensor request builder.  URL/parameter logic is centralized
here (never scattered across parsers).  Kraken promoted sensors all acquire via
the Market Analytics family (see `capabilities.kraken_native_evidence`):

    https://futures.kraken.com/api/charts/v1/analytics/{symbol}/{analytics_type}

Query contract (observed Bloc 2 I13R1 evidence):

    since    = epoch SECONDS (required)
    to       = epoch SECONDS
    interval = one supported resolution in seconds
               {60,300,900,1800,3600,14400,43200,86400,604800}
"""
from __future__ import annotations

from ...contracts.enums import SensorFamily
from .capabilities import KRAKEN_ANALYTICS_TYPES, kraken_endpoint_family
from ..base.enums import Granularity
from ..base.errors import UnsupportedGranularity
from ..base.models import FetchRequest

DEFAULT_INTERVAL_SECONDS = 3600

#: Canonical granularity -> Market Analytics interval (seconds) mapping
#: (SENSOR-B3-I05R1: EXACT mapping only — an explicit unsupported granularity
#: never silently becomes the default).
GRANULARITY_SECONDS: dict[Granularity, int] = {
    Granularity.G1M: 60,
    Granularity.G5M: 300,
    Granularity.G15M: 900,
    Granularity.G1H: 3600,
    Granularity.G4H: 14400,
    Granularity.G1D: 86400,
}

#: Kraken Market Analytics documents resolutions the Fabric Granularity enum
#: cannot represent: 1800 (30m), 43200 (12h), 604800 (1w).  They are a recorded
#: LIMITATION, not silently mapped or added to the enum (SENSOR-B3-I05R1).
KRAKEN_INTERVALS_UNREPRESENTABLE: tuple[int, ...] = (1800, 43200, 604800)


class KrakenAnalyticsRequestBuilder:
    """Builds Kraken Market Analytics (promoted sensor) requests + fingerprints.

    Only promoted Kraken sensors have a builder.  Trade-level `/history` and
    `/orderbook` snapshot are NOT promoted paths (no builder here — the adapter
    returns typed `CapabilityUnavailable` for them).
    """

    analytics_base_url = "https://futures.kraken.com/api/charts/v1/analytics"

    def __init__(self, vertical_timezone: str = "UTC") -> None:
        # `vertical_timezone` is informational (UTC boundaries enforced on the
        # FetchRequest upstream).  Kept for provider-context documentation.
        self._vertical_timezone = vertical_timezone

    def analytics_type(self, sensor: SensorFamily) -> str:
        if sensor not in KRAKEN_ANALYTICS_TYPES:
            raise ValueError(
                f"{sensor.value} is not a promoted Kraken analytics sensor"
            )
        return KRAKEN_ANALYTICS_TYPES[sensor]

    def endpoint_family(self, sensor: SensorFamily) -> str:
        return kraken_endpoint_family(sensor)

    def interval_seconds(self, request: FetchRequest) -> int:
        """Resolve the analytics `interval` (seconds) for a request.

        Fail-closed granularity contract (SENSOR-B3-I05R1):

        - request.granularity is None -> DEFAULT_INTERVAL_SECONDS (1h) is the
          documented adapter default.
        - request.granularity is one of the supported analytics buckets -> the
          exact mapping.
        - request.granularity is explicitly UNSUPPORTED (e.g. RAW_EVENT or
          BOOK_SNAPSHOT) -> typed `UnsupportedGranularity`, raised BEFORE any
          transport call; it is never silently mutated to 1h.
        """
        if request.granularity is None:
            return DEFAULT_INTERVAL_SECONDS
        mapped = GRANULARITY_SECONDS.get(request.granularity)
        if mapped is None:
            raise UnsupportedGranularity(
                provider_id=request.provider_id,
                sensor_family=request.sensor_family,
                detail=(
                    f"Kraken Market Analytics does not support granularity "
                    f"{request.granularity.value!r} (supported="
                    + ",".join(sorted(g.value for g in GRANULARITY_SECONDS))
                    + ")"
                ),
            )
        return mapped

    def build_params(self, request: FetchRequest) -> dict[str, int]:
        """Build the Market Analytics query params (epoch-SECOND since/to).

        Native symbol preservation: the request already carries the provider
        native instrument (`PI_XBTUSD`), never a canonical asset id.

        Resume mechanic (evidence: `result.more` -> re-issue `since` at the
        oldest bucket): when the request carries a deterministic ResumeToken
        from a previous page, its provider-native `since` overrides the
        window start so continuation is exact and re-runnable.
        """
        if request.resume_token is not None:
            native_since = request.resume_token.provider_native_state.get("since")
            if native_since is not None:
                return {
                    "since": int(native_since),
                    "to": int(request.end_time.timestamp()),
                    "interval": self.interval_seconds(request),
                }
        return {
            "since": int(request.start_time.timestamp()),
            "to": int(request.end_time.timestamp()),
            "interval": self.interval_seconds(request),
        }

    def build_url(self, sensor: SensorFamily, symbol: str) -> str:
        return f"{self.analytics_base_url}/{symbol}/{self.analytics_type(sensor)}"

    def build(self, request: FetchRequest) -> tuple[str, dict[str, int]]:
        """Return (url, params) for one promoted Kraken analytics request."""
        url = self.build_url(request.sensor_family, request.native_instrument_id)
        return url, self.build_params(request)