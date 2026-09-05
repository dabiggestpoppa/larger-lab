"""OKX Swap — Bloc 2 capability probe + Bloc 3 production adapter (I07).

Split surfaces (SENSOR-B3-I07):

- `probe.py`        — Bloc 2 offline capability characterization probe.
- `adapter.py`      — Bloc 3 production `OkxAdapter` (three I14-promoted
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
compute occurs here.  Funding/trade after/before cursor continuation is
UNRESOLVED by committed I13 evidence, so production issues a single
evidence-backed request window (no invented continuation cursor).
"""

from __future__ import annotations

from .adapter import (
    DEFAULT_FREE_ONLY_POLICY,
    NEUTRAL_INSTRUMENT_LIST_SENSOR,
    OkxAdapter,
)
from .capabilities import (
    OKX_BOOK_SNAPSHOT_SZ,
    OKX_FUNDING_RATE_HISTORY_PATH,
    OKX_HISTORY_TRADES_PATH,
    OKX_MARKET_BOOKS_PATH,
    OKX_PAGE_LIMIT,
    OKX_PRODUCTION_INSTRUMENT_SCOPE,
    OKX_PROBE_INSTRUMENT_SCOPE,
    OKX_PROMOTED_SENSORS,
    OKX_REST_BASE,
    OKX_SYMBOL_SCOPES,
    PROVIDER_ID,
    build_okx_capabilities,
    okx_endpoint_family,
    okx_native_evidence,
    okx_symbol_scopes_from_evidence,
)
from .errors import (
    AUTH_CODES,
    RATE_LIMIT_CODES,
    INVALID_INSTRUMENT_CODES,
    is_okx_error_body,
    is_okx_success,
    map_okx_error,
    okx_provider_code,
)
from .probe import NATIVE_INSTRUMENTS, OkxCapabilityProbe
from .requests import OkxRequestBuilder

__all__ = [
    "AUTH_CODES",
    "DEFAULT_FREE_ONLY_POLICY",
    "INVALID_INSTRUMENT_CODES",
    "NATIVE_INSTRUMENTS",
    "NEUTRAL_INSTRUMENT_LIST_SENSOR",
    "OKX_BOOK_SNAPSHOT_SZ",
    "OKX_FUNDING_RATE_HISTORY_PATH",
    "OKX_HISTORY_TRADES_PATH",
    "OKX_MARKET_BOOKS_PATH",
    "OKX_PAGE_LIMIT",
    "OKX_PRODUCTION_INSTRUMENT_SCOPE",
    "OKX_PROBE_INSTRUMENT_SCOPE",
    "OKX_PROMOTED_SENSORS",
    "OKX_REST_BASE",
    "OKX_SYMBOL_SCOPES",
    "PROVIDER_ID",
    "RATE_LIMIT_CODES",
    "OkxAdapter",
    "OkxCapabilityProbe",
    "OkxRequestBuilder",
    "build_okx_capabilities",
    "is_okx_error_body",
    "is_okx_success",
    "map_okx_error",
    "okx_endpoint_family",
    "okx_native_evidence",
    "okx_provider_code",
    "okx_symbol_scopes_from_evidence",
]