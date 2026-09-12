# Crypto Resource Integration Roadmap

## Current Status

Generation-1 (ALPHA-1 through ALPHA-2R1.2) used only:
- Hyperliquid perp data
- Binance spot data
- Hyperliquid funding data

Zero survivors. All 13 strategies falsified.

## New Resources (Documented, Not Yet Integrated)

### Priority 1: DefiLlama
**Lane:** CRYPTO-CAPITAL-FLOW

Why first:
- Infrastructure-grade API (free tier available)
- Enriches existing perp/spot research with onchain context
- Enables: stablecoin liquidity state, chain capital routing, DEX-vs-CEX activity
- Does not require new venue connections

Suggested first checkpoint:
```
CRYPTO-FLOW-DATA-0
DEFI-CAPITAL-FLOW-AND-LIQUIDITY-REALITY-AUDIT
```

### Priority 2: Boros by Pendle
**Lane:** CRYPTO-RATES

Why second:
- Fundamentally new payoff object (Yield Units)
- Makes funding stream itself tradeable
- Enables: fixed-vs-floating, cross-venue rate dislocations
- Highest potential for non-correlated alpha

Suggested first checkpoint:
```
CRYPTO-RATES-DATA-0
BOROS-AND-CROSS-VENUE-FUNDING-MARKET-REALITY-AUDIT
```

### Priority 3: Native Options Venues
**Lane:** CRYPTO-OPTIONS

Why third:
- Deribit, Derive, OKX options APIs
- Enables: IV surfaces, term structure, skew, convexity
- Options are the natural payoff object for volatility information

Suggested first checkpoint:
```
CRYPTO-OPTIONS-DATA-0
CROSS-VENUE-VOLATILITY-AND-OPTIONS-MARKET-REALITY-AUDIT
```

### Priority 4: Derivatives Monkey
**Lane:** CRYPTO-OPTIONS (crosscheck)

Why fourth:
- Options analytics discovery and crosscheck
- Not canonical — requires Level 1 verification
- Useful for screening and hypothesis generation

### Priority 5: PERPDEXLIST
**Lane:** GENERAL (cross-venue discovery)

Why fifth:
- Venue discovery and cross-venue dislocation candidates
- Highest noise — every finding requires native verification
- Useful for expanding venue coverage

## Integration Sequence

```
Phase 1: Document (THIS CHECKPOINT)
  ✓ All four resources documented
  ✓ Authority hierarchy frozen
  ✓ Future lanes defined

Phase 2: Data Reality Audit (ALPHA-3 / future)
  Access each resource
  Verify data fields
  Assess historical depth
  Document limitations

Phase 3: Enrichment (future checkpoints)
  Add onchain context to existing strategies
  Test whether capital-flow information improves edge

Phase 4: New Payoff Objects (future checkpoints)
  Boros YU as payoff object
  Options as payoff object
  Cross-venue spreads as payoff object
```

## Do NOT Yet

- Trade Boros
- Connect wallet
- Build arbitrage execution
- Scrape every perp DEX
- Pay for DefiLlama Pro
- Build options strategy
- Optimize implied-vol strategy
