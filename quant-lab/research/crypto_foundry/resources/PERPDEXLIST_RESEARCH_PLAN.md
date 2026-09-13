# PERPDEXLIST Research Plan

## Resource
PERPDEXLIST

## Role
PERP VENUE DISCOVERY + CROSS-VENUE DISLOCATION DISCOVERY

## Authority
CROSSCHECK_DISCOVERY_SOURCE (Level 3)

**NOT canonical execution truth.** Every finding must be verified by Level 1 source.

## What It Provides

- Registry of active perpetual DEX venues
- Market overlap information (which venues list which assets)
- Fee structure comparison
- Funding rate comparison across venues
- Price spread candidates between venues
- OI/volume crosschecks

## Use Cases

### Venue Registry
- Which perp DEXes exist?
- What assets does each list?
- What are the contract specifications?

### Fee Discovery
- Trading fees per venue
- Comparison with CEX fees
- Impact on strategy feasibility

### Funding Opportunity Discovery
- Compare funding rates across venues
- Identify cross-venue funding arbitrage candidates
- Screen for extreme funding dislocations

### Price Spread Discovery
- Same asset, different venues → price discrepancies
- Candidates for cross-venue arbitrage
- Must verify: depth, fees, settlement, execution speed

## Hard Rules

1. A PERPDEXLIST opportunity is only a **candidate**
2. Native APIs must verify: price, funding, fees, depth, contract orientation, settlement timing, market availability, execution feasibility
3. Never execute based solely on PERPDEXLIST data

## Access
Web interface / API. Public data.

## Historical Depth
Limited. primarily current-state discovery.

## Limitations
- Data may be stale or incomplete
- Not all venues may be represented
- Contract specifications may differ from what's listed
- Liquidity data often unavailable or unreliable

## Future Lane
GENERAL (cross-venue discovery across all crypto research lanes)

## Suggested Checkpoint
After CRYPTO-RATES-DATA-0, use PERPDEXLIST to expand venue coverage for funding research

## Verification Required
- Every venue must be individually verified via native API
- Contract specifications must match actual on-chain contracts
- Fees must be verified against actual trading reports
