# Boros by Pendle Research Plan

## Resource
Boros by Pendle

## Role
FUNDING-RATE / FIXED-VS-FLOATING YIELD MARKET

## Authority
LEVEL_1 (native protocol for YU trading)

## What It Is

Boros allows trading the funding rate itself as a standalone object. Instead of expressing a funding view through perp positioning, you can buy/sell Yield Units (YU) that represent a fixed funding rate over a period.

## Key Concepts

### Yield Units (YU)
- Represent a claim on funding rate over a defined period
- Buying YU = receiving fixed funding rate
- Selling YU = paying fixed funding rate (receiving floating)
- Settled against actual perp funding

### Implied Funding APR
- Market-implied forward funding rate
- Derived from YU pricing
- Compare to actual/historical funding for relative value

### Fixed vs Floating
- Actual perp funding = floating rate (changes every period)
- YU = fixed rate (locked in at trade time)
- Spread between implied and actual = tradeable dislocation

## Future Research Objects

| Object | Description |
|--------|-------------|
| YU direct | Trade funding rate direction directly |
| Perp + YU hedge | Lock in funding via YU, hedge perp exposure |
| Cross-venue funding spread | Compare YU-implied funding vs native venue funding |
| Funding term structure | Near-term vs far-term implied funding |
| Fixed funding carry | Earn fixed funding via YU positioning |

## Why This Matters for ALPHA-3

Generation-1 found that funding information (negative funding = short crowding) did not produce edge as a directional perp expression.

But the SAME information might produce edge as:
- A YU trade (bet on funding normalization)
- A perp + YU hedge (lock in funding differential)
- A cross-venue rate arbitrage

This is the payoff router concept in action: same information, different carrier.

## Access
Pendle/Boros protocol. Requires wallet connection for trading. Read-only API for data.

## Historical Depth
Limited — Boros is relatively new. Historical data may be sparse.

## Limitations
- New protocol, limited track record
- Liquidity may be thin for large positions
- Smart contract risk
- Settlement mechanics differ from perp funding

## Future Lane
CRYPTO-RATES

## Suggested Checkpoint
CRYPTO-RATES-DATA-0: BOROS-AND-CROSS-VENUE-FUNDING-MARKET-REALITY-AUDIT

## Verification Required
- Verify YU settlement mechanics against actual funding
- Cross-check implied funding vs native venue funding
- Verify liquidity depth before any execution planning
