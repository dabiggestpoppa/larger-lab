# BLOC 1 — PROVIDER REGISTRY SNAPSHOT

Source of truth: `quant-lab/config/crypto_sensor_fabric/provider_registry.yaml` (committed, schema_version 1.0).
All access classes are `UNVERIFIED` and all capability `verified` flags are `false` by Bloc 1 contract:
**Bloc 2 capability probes** are the only mechanism that may upgrade them.

Legend: C = capability claimed (planning), V = verified by probe (must stay false until Bloc 2).
`equiv` = default semantic equivalence for the mapping (where declared).

| Provider | Evidence class | Status | Access | Liq | OI | Funding | Order flow | Book/depth | Notes |
|---|---|---|---|---|---|---|---|---|---|
| KRAKEN_FUTURES | FIRST_PARTY_EXCHANGE | CANDIDATE | UNVERIFIED, $0 | C (NORMALIZABLE_COMPARABLE) | C | C | C | C | planned: liquidations, OI, funding, aggressor/CVD, book analytics, spreads, liquidity, slippage, basis |
| GATE_FUTURES | FIRST_PARTY_EXCHANGE | CANDIDATE | UNVERIFIED, $0 | C (NORMALIZABLE_COMPARABLE) | C | C | C | — | long/short liquidation aggregates, taker flow, funding/positioning |
| BINANCE_USDM | FIRST_PARTY_EXCHANGE | CANDIDATE | UNVERIFIED, $0 | claimed=false (UNVERIFIED_OR_UNAVAILABLE) | C | C | C | C | trades/aggTrades, OI, funding, taker-flow reconstruction, book archives |
| BYBIT_LINEAR | FIRST_PARTY_EXCHANGE | CANDIDATE | UNVERIFIED, $0 | — | C | C | C | C | OI, funding, historical trades, live book |
| OKX_SWAP | FIRST_PARTY_EXCHANGE | CANDIDATE | UNVERIFIED, $0 | — | — | C | C | C | historical trades, funding, historical book modules |
| DERIBIT | FIRST_PARTY_EXCHANGE | CANDIDATE | UNVERIFIED, $0 | C (CORROBORATION_ONLY) | — | C | C | C | liquidation-tagged trade anatomy, funding, microstructure |
| COINALYZE | THIRD_PARTY_AGGREGATOR | CANDIDATE | UNVERIFIED, $0 | C | C | C | — | — | aggregate OI/funding/liquidation corroboration; never canonical sole provider while first-party alternatives exist |
| BITFINEX_COMMUNITY_ARCHIVE | COMMUNITY_ARCHIVE | CANDIDATE | UNVERIFIED, $0 | C (CORROBORATION_ONLY) | — | — | — | — | historical liquidation replication; never promoted to first-party truth |

Free-only gate: with the default registry, `eligible_required_providers(...)` returns `[]` — **no provider may be a required automated dependency until Bloc 2 verifies it** (asserted by tests).

Fallback candidates per capability follow the frozen sensor-priority ordering (see `BLOC_01_EQUIVALENCE_MATRIX.md` for cross-references).
