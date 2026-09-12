# ALT-DATA-0 — Future Topology Data Readiness (Task 20)

No TDA implemented in this checkpoint. This document verifies whether the
future canonical PIT panel can provide the node attributes required for
graph research.

## Required node attributes → data availability

| attribute | can the DATA-0 foundation provide it? | source / class |
|---|---|---|
| rank | **YES** — `cmcRank` per dated snapshot (500-deep, any date) | CMC data-api, PRIMARY_VERIFIED |
| sector | **YES (approximated)** — CMC dated tags | HISTORICAL_APPROXIMATION |
| market cap | **YES** — snapshot `quotes.marketCap` | CMC PRIMARY_VERIFIED |
| volume | **YES** — snapshot `quotes.volume24h` | CMC PRIMARY_VERIFIED |
| price returns | **YES** — snapshot `quotes.price` across dates (1D–90D via repeated snapshots) | CMC PRIMARY_VERIFIED |
| BTC/ETH beta | **YES** — same price panel; needs per-asset × BTC/ETH series (feasible from snapshots) | CMC |
| liquidity | **PARTIAL** — perp venue current liquidity (HL dayNtlVlm/OI, DexPaprika pool liquidity) is CURRENT_ONLY; historical liquidity NOT available free | HL/DexPaprika CURRENT_ONLY |
| perp availability | **YES** — per-venue list/delist intervals (HL funding first/last ts, OKX listTime, Binance archive 2020+) | venue audits |

## Verdict

**TOPOLOGY_DATA_READY** for rank/sector(approx)/mcap/volume/returns/beta/perp
availability. **GAP:** historical liquidity (perp + DEX) is current-only in
the free stack; graph research that needs *historical* liquidity edges must
either (a) use listing-survivorship + volume as proxies, (b) collect
liquidity snapshots going forward, or (c) acquire paid liquidity history.
The gap is documented, not silently papered over.
