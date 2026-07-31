# Phase 0 — Batch 3 Results (Metals + Crypto)

**Date:** 2026-06-01
**Assets:** CHFJPY, XAUUSD, XAGUSD, BTCUSD, ETHUSD
**Strategies:** symmetry_trap, p90

## Summary Table

| Asset   | Strategy      | Trades | WR    | Pnl (pips) |
|---------|--------------|--------|-------|------------|
| CHFJPY  | symmetry_trap | 0      | 0.0%  | 0.0        |
| CHFJPY  | p90          | 0      | 0.0%  | 0.0        |
| XAUUSD  | symmetry_trap | 1,718  | 81.8% | 21,118.2   |
| XAUUSD  | p90          | 202    | 54.5% | 309.2      |
| XAGUSD  | symmetry_trap | 2      | 100.0%| 50.0       |
| XAGUSD  | p90          | 0      | 0.0%  | 0.0        |
| BTCUSD  | symmetry_trap | 2,014  | 86.9% | 219,718.6  |
| BTCUSD  | p90          | 2      | 100.0%| 17.0       |
| ETHUSD  | symmetry_trap | 777    | 94.7% | 11,901.9   |
| ETHUSD  | p90          | 99     | 83.8% | 391.0      |

## Key Findings

### Winners (by PnL — symmetry_trap dominates)
1. **BTCUSD** — symmetry_trap: 2,014 trades, 86.9% WR, **219,718.6 pips** ⭐ Best overall
2. **XAUUSD** — symmetry_trap: 1,718 trades, 81.8% WR, **21,118.2 pips**
3. **ETHUSD** — symmetry_trap: 777 trades, 94.7% WR, **11,901.9 pips**
4. **ETHUSD** — p90: 99 trades, 83.8% WR, **391.0 pips** (only viable P90)
5. **XAUUSD** — p90: 202 trades, 54.5% WR, **309.2 pips** (below 60% threshold)

### Flat / No Trades
- **CHFJPY** — 0 trades both strategies. Low volatility cross, tier thresholds not triggering.
- **XAGUSD** — only 2 symmetry_trap trades (100% but tiny sample), 0 p90 trades. Wide tiers (T1 ar_max=50) filter most action.

### Strategy Comparison
- **symmetry_trap** is the clear dominant strategy across metals and crypto: 4,511 total trades vs p90's 303
- **p90** only shows viability on ETHUSD (83.8% WR, 99 trades). XAUUSD p90 at 54.5% WR is below threshold.
- **BTCUSD + ETHUSD** are the strongest assets overall (both 86%+ WR on symmetry_trap)
- **CHFJPY** needs tier recalibration or exclusion from the active asset list
- **XAGUSD** needs tighter tier config to generate meaningful trade volume

## Errors
None — all 10 backtests completed successfully.
