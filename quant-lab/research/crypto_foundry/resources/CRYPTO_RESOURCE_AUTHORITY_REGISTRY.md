# Crypto Resource Authority Registry

## Frozen Authority Hierarchy

### LEVEL 1 — NATIVE VENUE / PROTOCOL API
**Authority:** CANONICAL_VENUE_TRUTH

Sources:
- Hyperliquid API (perp prices, funding, OI)
- Binance API (spot, perp, options)
- Bybit API
- OKX API
- Deribit API (options canonical)
- Derive API
- Onchain protocols (native RPC/indexer)

Rules:
- Always overrides aggregated sources for venue-specific data
- Required for: execution price, funding rates, orderbook depth, contract metadata, settlement timing
- No lower-level source may contradict Level 1

### LEVEL 2 — HIGH-QUALITY AGGREGATED FUNDAMENTAL / ONCHAIN
**Authority:** PRIMARY_ONCHAIN_AGGREGATION

Sources:
- DefiLlama API

Rules:
- Primary source for cross-chain onchain data
- TVL, stablecoin supply, DEX volume, yield pools, fees, revenue
- Must be verified at field level before use in strategies
- Native venue APIs outrank for execution-relevant data

### LEVEL 3 — SPECIALIZED ANALYTICS / MARKET DISCOVERY
**Authority:** CROSSCHECK_DISCOVERY

Sources:
- Derivatives Monkey (options analytics, cross-venue vol)
- PERPDEXLIST (venue discovery, cross-venue dislocation)

Rules:
- Discovery/candidate identification, NOT canonical truth
- Any opportunity found here must be verified by Level 1 source
- Useful for: screening, hypothesis generation, crosschecks

### LEVEL 4 — PRIOR ART / IDEAS / SOCIAL / RESEARCH
**Authority:** INSPIRATION_ONLY

Sources:
- Research papers
- Social media / Twitter
- Conference talks
- Blog posts

Rules:
- Idea generation only
- Never used as data source
- Must be independently verified

## Integration Rules

1. **No silent override:** Lower-level source never contradicts higher-level
2. **Field-level verification:** Aggregated data verified against native when stakes are high
3. **Discovery vs truth:** Level 3 sources identify candidates; Level 1 confirms
4. **Documentation required:** Every data source used in a strategy must be recorded with authority level
