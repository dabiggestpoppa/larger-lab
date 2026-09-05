"""Deribit — Bloc 2 capability probe + Bloc 3 production adapter (I08).

Split surfaces (SENSOR-B3-I08):

- `probe.py`        — Bloc 2 offline capability characterization probe.
- `adapter.py`      — Bloc 3 production `DeribitAdapter` (four I14-promoted
                      paths; typed `CapabilityUnavailable` otherwise).
- `capabilities.py` — I14-bounded capability + native acquisition-mode freeze.
- `requests.py` / `parsers.py` / `errors.py` — request builders, provider-native
                      parsers, and JSON-RPC failure-envelope mapping.

I14 promotes EXACTLY FOUR DERIBIT production paths:

    MECHANICAL_BOOK_SNAPSHOT  (CURRENT_ONLY)
    MECHANICAL_FUNDING        (SECONDARY, HISTORICAL)
    MECHANICAL_LIQUIDATION    (MECHANISM_MICROSCOPE, HISTORICAL)
    MECHANICAL_TRADE          (MECHANISM_MICROSCOPE, HISTORICAL)

Production instrument scope is evidence-backed BTC-PERPETUAL for all four;
ETH/SOL stay Bloc 2 probe/control instruments.  Timestamps are
millisecond-epoch INTEGERS (provider-native; strict type check, bool rejected).
Deribit is the mechanism microscope: trade/liquidation is TRADE-LEVEL anatomy
and is NEVER numerically merged with interval liquidation totals.  The same
physical `get_last_trades_by_instrument` endpoint supports two logical sensor
views; the raw payload is preserved before any sensor-specific projection.
Funding `result` is a raw LIST (observed LIVE).  Continuation beyond the
evidenced single request window is NOT proven by committed I13 evidence, so
production issues a single evidence-backed request window with truthful
completion semantics and no invented resume token.
"""

from __future__ import annotations

from .adapter import (
    DEFAULT_FREE_ONLY_POLICY,
    NEUTRAL_INSTRUMENT_LIST_SENSOR,
    DeribitAdapter,
)
from .capabilities import (
    DERIBIT_BOOK_DEPTH,
    DERIBIT_FUNDING_RATE_HISTORY_PATH,
    DERIBIT_LAST_TRADES_PATH,
    DERIBIT_ORDER_BOOK_PATH,
    DERIBIT_PAGE_LIMIT,
    DERIBIT_PRODUCTION_INSTRUMENT_SCOPE,
    DERIBIT_PROBE_INSTRUMENT_SCOPE,
    DERIBIT_PROMOTED_SENSORS,
    DERIBIT_REST_BASE,
    DERIBIT_SYMBOL_SCOPES,
    PROVIDER_ID,
    build_deribit_capabilities,
    deribit_endpoint_family,
    deribit_native_evidence,
    deribit_symbol_scopes_from_evidence,
)
from .errors import (
    AUTH_CODES,
    ENDPOINT_REMOVED_CODES,
    INVALID_INSTRUMENT_CODES,
    RATE_LIMIT_CODES,
    deribit_error_code,
    is_deribit_error_body,
    map_deribit_error,
)
from .probe import NATIVE_INSTRUMENTS, DeribitCapabilityProbe
from .requests import DeribitRequestBuilder

__all__ = [
    "AUTH_CODES",
    "DEFAULT_FREE_ONLY_POLICY",
    "DERIBIT_BOOK_DEPTH",
    "DERIBIT_FUNDING_RATE_HISTORY_PATH",
    "DERIBIT_LAST_TRADES_PATH",
    "DERIBIT_ORDER_BOOK_PATH",
    "DERIBIT_PAGE_LIMIT",
    "DERIBIT_PRODUCTION_INSTRUMENT_SCOPE",
    "DERIBIT_PROBE_INSTRUMENT_SCOPE",
    "DERIBIT_PROMOTED_SENSORS",
    "DERIBIT_REST_BASE",
    "DERIBIT_SYMBOL_SCOPES",
    "ENDPOINT_REMOVED_CODES",
    "INVALID_INSTRUMENT_CODES",
    "NATIVE_INSTRUMENTS",
    "NEUTRAL_INSTRUMENT_LIST_SENSOR",
    "PROVIDER_ID",
    "RATE_LIMIT_CODES",
    "DeribitAdapter",
    "DeribitCapabilityProbe",
    "DeribitRequestBuilder",
    "build_deribit_capabilities",
    "deribit_endpoint_family",
    "deribit_error_code",
    "deribit_native_evidence",
    "deribit_symbol_scopes_from_evidence",
    "is_deribit_error_body",
    "map_deribit_error",
]
