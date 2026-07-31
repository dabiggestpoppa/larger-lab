# Phase 0 — Batch 1 Results (FX Majors)

**Date:** 2026-06-01 | **Strategies:** Symmetry Trap + P90 | **Assets:** 5 FX Majors

## Summary Table

| Asset   | Strategy      | Trades | WR    | Pnl (pips) |
|---------|--------------|--------|-------|------------|
| EURUSD  | Symmetry Trap| 2,186  | 82.1% | 8,584.7    |
| EURUSD  | P90          | 1,048  | 60.4% | 792.8      |
| GBPUSD  | Symmetry Trap| 2,234  | 83.5% | 11,750.6   |
| GBPUSD  | P90          | 1,297  | 53.1% | 396.9      |
| USDCHF  | Symmetry Trap| 2,050  | 81.6% | 7,756.4    |
| USDCHF  | P90          | 841    | 57.4% | 258.6      |
| USDJPY  | Symmetry Trap| 0      | 0.0%  | 0.0        |
| USDJPY  | P90          | 0      | 0.0%  | 0.0        |
| AUDUSD  | Symmetry Trap| 1,249  | 87.8% | 5,328.6    |
| AUDUSD  | P90          | 527    | 49.1% | -35.8      |

## Key Observations

### Symmetry Trap — Dominant Across All Tradeable Assets
- **Best performer:** GBPUSD (83.5% WR, 11,750.6 pips)
- **Highest WR:** AUDUSD (87.8% WR)
- **Consistent:** All 4 tradeable assets show 81-88% WR
- **USDJPY:** Zero trades generated — requires investigation (possible config/data issue)

### P90 — Mixed Results
- **Best performer:** EURUSD (60.4% WR, 792.8 pips)
- **Profitable on 3 of 4:** EURUSD, GBPUSD, USDCHF positive; AUDUSD slightly negative
- **AUDUSD:** 49.1% WR, -35.8 pips (loss-making)
- **USDJPY:** Zero trades — same issue as Symmetry Trap

### Symmetry Trap vs P90 Comparison
- Symmetry Trap outperforms P90 on every asset (where trades exist)
- Symmetry Trap WR range: 81-88% vs P90 WR range: 49-60%
- Symmetry Trap PnL significantly higher across all pairs

## Issues
- **USDJPY:** Both strategies generated 0 trades. Likely a data availability or asset config issue. Needs investigation before inclusion in any portfolio.
- **AUDUSD P90:** Loss-making at 49.1% WR. Below breakeven threshold.

## Totals (Symmetry Trap)
- **Total trades:** 7,719
- **Average WR:** 83.7% (across 4 tradeable assets)
- **Total PnL:** 33,420.3 pips

## Totals (P90)
- **Total trades:** 3,713
- **Average WR:** 55.0% (across 4 tradeable assets)
- **Total PnL:** 1,412.5 pips
