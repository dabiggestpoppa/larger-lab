"""OKX Swap — Bloc 2 capability probe + Bloc 3 production adapter (I07).

Split surfaces (SENSOR-B3-I07):

- `probe.py`        — Bloc 2 offline capability characterization probe.
- `adapter.py`      — Bloc 3 production `OkxAdapter` (the three I14-promoted
                      paths; typed `CapabilityUnavailable` otherwise).
- `capabilities.py` — I14-bounded capability + native acquisition-mode freeze.
- `requests.py` / `parsers.py` / `errors.py` — request builders, provider-native
                      parsers, and failure-envelope mapping.

I14 promotes EXACTLY THREE OKX_SWAP production paths:

    MECHANICAL_BOOK_SNAPSHOT  (CURRENT_ONLY)
    MECHANICAL_FUNDING        (PRIMARY, HISTORICAL)
    MECHANICAL_TRADE          (PRIMARY, HISTORICAL)

Production instrument scope is evidence-backed BTC-USDT-SWAP for all three;
ETH/SOL/DOGE stay Bloc 2 probe/control instruments.  Timestamps are
millisecond-epoch STRINGS (provider-native).  No normalization or research
compute occurs here.
"""

from __future__ import annotations

from .capabilities import (
    OKX_BOOK_SNAPSHOT_SZ,
    OKX_FUNDING_RATE_HISTORY_PATH,
    OKX_HISTORY_TRADES_PATH,
    OKX_MARKET_BOOKS_PATH,
    OKX_PAGE_LIMIT,
    OKX_PRODUCTION_INSTRUMENT_SCOPE,
    OKX_PROBE_INSTRUMENT_SCOPE,
    OKX_PROMOTED_SENSORS,
    OKX_SYMBOL_SCOPES,
    PROVIDER_ID,
    build_okx_capabilities,
    okx_endpoint_family,
    okx_native_evidence,
    okx_symbol_scopes_from_evidence,
)
from .probe import NATIVE_INSTRUMENTS, OkxCapabilityProbe

__all__ = [
    "NATIVE_INSTRUMENTS",
    "OKX_BOOK_SNAPSHOT_SZ",
    "OKX_FUNDING_RATE_HISTORY_PATH",
    "OKX_HISTORY_TRADES_PATH",
    "OKX_MARKET_BOOKS_PATH",
    "OKX_PAGE_LIMIT",
    "OKX_PRODUCTION_INSTRUMENT_SCOPE",
    "OKX_PROBE_INSTRUMENT_SCOPE",
    "OKX_PROMOTED_SENSORS",
    "OKX_SYMBOL_SCOPES",
    "PROVIDER_ID",
    "OkxCapabilityProbe",
    "build_okx_capabilities",
    "okx_endpoint_family",
    "okx_native_evidence",
    "okx_symbol_scopes_from_evidence",
]