# Derivatives Monkey Research Plan

## Resource
Derivatives Monkey

## Role
OPTIONS ANALYTICS DISCOVERY + CROSS-VENUE VOLATILITY CROSSCHECK

## Authority
OPTIONS_ANALYTICS_DISCOVERY_AND_CROSSCHECK_SOURCE (Level 3)

**NOT canonical.** Native exchange APIs remain canonical for options data.

## What It Provides

| Field | Description |
|-------|-------------|
| Options Chains | Full chain data across venues |
| ATM IV | At-the-money implied volatility |
| Term Structure | IV across expiries |
| IV Smile | IV across strikes |
| Skew | Put-call IV skew |
| GEX | Gamma exposure |
| DEX / Delta Exposure | Net delta positioning |
| Implied Move | Market-implied expected move |
| Max Pain | Max pain price level |
| Flow | Options flow analysis |
| Venue Comparisons | Cross-venue options data |

## Venues Potentially Represented

- Deribit (BTC/ETH options canonical)
- Derive
- Binance
- Bybit
- OKX
- Thalex

## Use Cases

### Options Analytics Discovery
- Screen for interesting IV levels
- Identify term structure inversions
- Detect unusual skew
- Find flow signals

### Cross-Venue Volatility Crosscheck
- Compare IV across venues
- Identify venue-specific dislocations
- Verify options data consistency

### Connection to Generation-1
- Volatility information (V_HIGH, V_EXTREME) was used in FAM_C strategies
- But was expressed as a perp directional filter
- Options are the NATURAL payoff object for volatility information
- ALPHA-3 may test: same vol information → options expression

## Access
Web interface / API. May require registration.

## Historical Depth
Varies. Options data availability depends on venue and asset.

## Limitations
- Aggregated data may lag native exchange data
- Not all venues may be fully represented
- Options market is less liquid than perp market
- Smart contract / exchange risk for execution

## Future Lane
CRYPTO-OPTIONS

## Suggested Checkpoint
CRYPTO-OPTIONS-DATA-0: CROSS-VENUE-VOLATILITY-AND-OPTIONS-MARKET-REALITY-AUDIT

## Verification Required
- Cross-check IV against native Deribit API
- Verify options chain data against exchange directly
- Confirm GEX calculations against raw positioning data
