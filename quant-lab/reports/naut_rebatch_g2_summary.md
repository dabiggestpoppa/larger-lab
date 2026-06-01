# Nautilus Rebatch — Group 2 Summary

**Date:** 2026-06-01  
**Assets:** NZDUSD, GBPJPY, GBPCHF, GBPAUD, GBPNZD  
**Data:** M5 CSV, ~277K bars per asset  
**Engine:** CEREBUS FX v4.0 Nautilus Backtest

---

## Results Overview

| Asset | Strategy | Trades | Win Rate | PnL (pips) |
|-------|----------|--------|----------|------------|
| NZDUSD | Symmetry Trap | 833 | **91.6%** | 4,363.9 |
| NZDUSD | P90 | 236 | 60.2% | 142.7 |
| GBPJPY | Symmetry Trap | 1,948 | 81.8% | 17,037.6 |
| GBPJPY | P90 | 278 | 67.6% | 724.8 |
| GBPCHF | Symmetry Trap | 1,161 | **89.9%** | 7,981.2 |
| GBPCHF | P90 | 343 | 67.9% | 246.7 |
| GBPAUD | Symmetry Trap | 1,428 | 85.2% | 12,529.2 |
| GBPAUD | P90 | 195 | 64.6% | 300.5 |
| GBPNZD | Symmetry Trap | 1,410 | 85.0% | 13,936.1 |
| GBPNZD | P90 | 130 | 69.2% | 307.3 |

---

## Key Findings

### Symmetry Trap — Dominant Across All 5 Assets
- **Average WR: 86.7%** (range: 81.8% – 91.6%)
- **Total PnL: 55,848 pips** across 6,780 trades
- **Best:** NZDUSD at 91.6% WR
- **Lowest:** GBPJPY at 81.8% WR (still strong)
- Consistent high-WR performance across all GBP and NZD crosses

### P90 — Moderate, Consistent
- **Average WR: 65.9%** (range: 60.2% – 69.2%)
- **Total PnL: 1,722 pips** across 1,182 trades
- **Best:** GBPNZD at 69.2% WR
- **Weakest:** NZDUSD at 60.2% WR
- Lower trade count but positive across all assets

### Symmetry Trap vs P90 Advantage
| Metric | Symmetry Trap | P90 | Ratio |
|--------|--------------|-----|-------|
| Avg WR | 86.7% | 65.9% | +20.8pp |
| Total Trades | 6,780 | 1,182 | 5.7x |
| Total PnL | 55,848 | 1,722 | 32.4x |

**Symmetry Trap dominates on every metric** — higher WR, more trades, and 32x the PnL.

---

## Per-Asset Notes

- **NZDUSD:** ST exceptional at 91.6% WR. P90 weakest link at 60.2%.
- **GBPJPY:** Highest trade count (1,948 ST). ST WR dips to 81.8% but PnL is highest at 17K pips.
- **GBPCHF:** ST near-excellent at 89.9%. P90 solid at 67.9%.
- **GBPAUD:** ST strong at 85.2%. P90 lowest WR at 64.6%.
- **GBPNZD:** ST strong at 85.0%. P90 best relative showing at 69.2%.

---

## Conclusion

Group 2 confirms Symmetry Trap as the dominant engine across GBP and NZD crosses. All 5 assets show ST WR above 81%, with 3 of 5 above 85%. P90 is consistently profitable but at significantly lower WR and PnL. No asset in this group shows P90 outperforming Symmetry Trap.

**Recommendation:** Symmetry Trap is the primary engine for GBP/NZD crosses. P90 can serve as a secondary/convergence signal but should not be the sole strategy on these pairs.
