"""Kraken Futures — Bloc 2 capability probe + Bloc 3 production adapter.

Split surfaces (I12R1/I05):

- `probe.py`        — Bloc 2 offline capability characterization probe.
- `adapter.py`      — Bloc 3 production `KrakenAdapter` (six I14-promoted
                      Market Analytics paths; typed unsupported otherwise).
- `capabilities.py` — I14-bounded capability + native acquisition-mode freeze.
- `requests.py` / `parsers.py` / `errors.py` — request builders, provider-native
                      parsers, and failure-envelope mapping.

Kraken analytics are provider-computed mechanics; they are NOT automatically
EXACT_EQUIVALENT to Fabric-reconstructed metrics, and history is ragged by
sensor/instrument.  No normalization or research compute occurs here.
"""

from __future__ import annotations

from .adapter import DEFAULT_FREE_ONLY_POLICY, KrakenAdapter
from .capabilities import (
    KRAKEN_ANALYTICS_TYPES,
    KRAKEN_INSTRUMENT_SCOPE,
    KRAKEN_PROMOTED_SENSORS,
    PROVIDER_ID,
    build_kraken_capabilities,
    kraken_endpoint_family,
    kraken_native_evidence,
)
from .probe import NATIVE_INSTRUMENTS, KrakenCapabilityProbe
from .requests import KrakenAnalyticsRequestBuilder

__all__ = [
    "DEFAULT_FREE_ONLY_POLICY",
    "KRAKEN_ANALYTICS_TYPES",
    "KRAKEN_INSTRUMENT_SCOPE",
    "KRAKEN_PROMOTED_SENSORS",
    "NATIVE_INSTRUMENTS",
    "PROVIDER_ID",
    "KrakenAdapter",
    "KrakenAnalyticsRequestBuilder",
    "KrakenCapabilityProbe",
    "build_kraken_capabilities",
    "kraken_endpoint_family",
    "kraken_native_evidence",
]