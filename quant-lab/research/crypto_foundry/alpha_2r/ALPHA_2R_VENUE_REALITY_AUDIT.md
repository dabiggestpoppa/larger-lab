# ALPHA-2R Venue Reality Audit

## Funding Sign Convention

### OLD (ALPHA-1.1 Sealed Contract)
```
"sign": "LONG receives when funding>0"
```

### VERIFIED HYPERLIQUID CONVENTION
**Source:** https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding

**Retrieved:** 2026-08-24

**Official Rule:**
- Positive funding rate → LONG PAYS SHORT
- Negative funding rate → SHORT PAYS LONG

**Additional Sources Confirmed:**
- Dwellir Guides: "a long with positive funding pays out, so its funding PnL is negative"
- OneKey: "Positive funding: longs pay shorts (being long has carry cost)"
- Chainstack docs: "Positive rates indicate longs pay shorts"
- Reddit/r/hyperliquid1: "If the perp price is above spot, funding rates is positive and the longs pay the shorts"

### FUNDING PNL RULE (CORRECTED)
```
LONG:  funding_pnl = -funding_rate * notional_per_hour
SHORT: funding_pnl = +funding_rate * notional_per_hour
```

### OLD vs CORRECTED SIGN
```
OLD:     LONG + positive funding → POSITIVE funding_pnl (RECEIVES)
CORRECT: LONG + positive funding → NEGATIVE funding_pnl (PAYS)
```

The old contract had the sign inverted. This is an OBJECTIVE_VENUE_REALITY_ERROR.

## Funding Frequency

### OLD (ALPHA-1.1 Sealed Contract)
```
"settlements": "00,08,16 UTC (8h)"
```

### VERIFIED HYPERLIQUID FREQUENCY
**Source:** Multiple official sources confirm Hyperliquid uses HOURLY funding.

- Pendle docs: "funding rates are settled every hour"
- Hyperliquid gitbook: hourly funding observations
- API docs: fundingHistory endpoint returns hourly timestamps

### FUNDING PROCESSING (CORRECTED)
Use ACTUAL persisted Hyperliquid hourly funding observations.
Each observation represents one settlement event.
No synthetic 8-hour grouping.

### OLD vs CORRECTED FREQUENCY
```
OLD:     3 settlements/day (00, 08, 16 UTC)
CORRECT: 24 settlements/day (every hour, using actual observations)
```

## Impact Assessment

The sign inversion means:
1. Long positions that were credited funding should have been debited
2. Net PnL for all long strategies will decrease
3. Short positions would be affected oppositely (but all strategies are LONG or LONG_HEDGE)
4. The magnitude depends on how many funding observations crossed during each trade

The frequency change means:
1. More funding observations processed per trade
2. Shorter trades that previously missed 8h settlements may now capture hourly ones
3. Net funding PnL may increase or decrease depending on sign corrections
