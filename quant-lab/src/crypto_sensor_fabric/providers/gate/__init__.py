"""Gate Futures — Bloc 2 capability probe + Bloc 3 production adapter.

Split surfaces (I06):

- `probe.py`        — Bloc 2 offline capability characterization probe.
- `adapter.py`      — Bloc 3 production `GateAdapter` (four I14-promoted
                      paths; typed unsupported otherwise).
- `capabilities.py` — I14-bounded capability + native acquisition-mode freeze.
- `requests.py` / `parsers.py` / `errors.py` — request builders, provider-native
                      parsers, and failure-envelope mapping.

Gate's FOUR promoted paths are SECONDARY.  OI / LIQUIDATION / POSITIONING
share the PUBLIC `/contract_stats` surface (same physical payload, separate
logical sensor contracts — never a combined state); positioning NEVER uses the
private `/positions` endpoint.  Funding uses the single-contract public
`GET /funding_rate` (the plural `/funding_rates` batch route is not a
production path).  A rolling ~180-day retention boundary is mapped to typed
`HistoricalRangeUnavailable`.  Provider-native units are preserved; no
normalization or research compute occurs here.
"""

from __future__ import annotations

from .adapter import DEFAULT_FREE_ONLY_POLICY, NEUTRAL_INSTRUMENT_LIST_SENSOR, GateAdapter
from .capabilities import (
    GATE_CONTRACT_STATS_PATH,
    GATE_FUNDING_RATE_PATH,
    GATE_PRODUCTION_INSTRUMENT_SCOPE,
    GATE_PROBE_INSTRUMENT_SCOPE,
    GATE_PROMOTED_SENSORS,
    GATE_SYMBOL_SCOPES,
    GATE_USDT_BASE,
    PROVIDER_ID,
    build_gate_capabilities,
    gate_endpoint_family,
    gate_native_evidence,
    gate_symbol_scopes_from_evidence,
)
from .probe import NATIVE_INSTRUMENTS, GateCapabilityProbe
from .requests import (
    GATE_CONTRACT_STATS_DEFAULT_LIMIT,
    GATE_INTERVAL_1H,
    GateRequestBuilder,
)

__all__ = [
    "DEFAULT_FREE_ONLY_POLICY",
    "GATE_CONTRACT_STATS_DEFAULT_LIMIT",
    "GATE_CONTRACT_STATS_PATH",
    "GATE_FUNDING_RATE_PATH",
    "GATE_INTERVAL_1H",
    "GATE_PRODUCTION_INSTRUMENT_SCOPE",
    "GATE_PROBE_INSTRUMENT_SCOPE",
    "GATE_PROMOTED_SENSORS",
    "GATE_SYMBOL_SCOPES",
    "GATE_USDT_BASE",
    "NATIVE_INSTRUMENTS",
    "NEUTRAL_INSTRUMENT_LIST_SENSOR",
    "PROVIDER_ID",
    "GateAdapter",
    "GateCapabilityProbe",
    "GateRequestBuilder",
    "build_gate_capabilities",
    "gate_endpoint_family",
    "gate_native_evidence",
    "gate_symbol_scopes_from_evidence",
]