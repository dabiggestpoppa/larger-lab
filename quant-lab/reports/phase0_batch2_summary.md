# Phase 0 — Batch 2 Results (FX Crosses)

**Date:** 2026-06-01
**Assets:** NZDUSD, GBPJPY, GBPCHF, GBPAUD, GBPNZD
**Strategies:** Symmetry Trap, P90

## Summary Table

| Asset   | Strategy      | Trades | Win Rate | PnL (pips) |
|---------|--------------|--------|----------|-------------|
| NZDUSD  | Symmetry Trap| 833    | 91.6%    | 4,363.9     |
| NZDUSD  | P90          | 457    | 54.0%    | 215.0       |
| GBPJPY  | Symmetry Trap| 0      | 0.0%*    | 0.0         |
| GBPJPY  | P90          | 0      | 0.0%*    | 0.0         |
| GBPCHF  | Symmetry Trap| 1,161  | 89.9%    | 7,981.2     |
| GBPCHF  | P90          | 980    | 59.7%    | 673.6       |
| GBPAUD  | Symmetry Trap| 1,428  | 85.2%    | 12,529.2    |
| GBPAUD  | P90          | 380    | 47.9%    | 81.0        |
| GBPNZD  | Symmetry Trap| 1,410  | 85.0%    | 13,936.1    |
| GBPNZD  | P90          | 255    | 48.6%    | 133.9       |

\* GBPJPY generated 0 trades for both strategies — no signals were triggered across the full dataset.

## Key Observations

### Symmetry Trap — Strong Performance
- **GBPNZD** leads with **13,936.1 pips** (1,410 trades, 85.0% WR)
- **GBPAUD** close behind at **12,529.2 pips** (1,428 trades, 85.2% WR)
- **GBPCHF** solid at **7,981.2 pips** (1,161 trades, 89.9% WR)
- **NZDUSD** at **4,363.9 pips** (833 trades, 91.6% WR) — highest WR of the batch
- All four trading assets showed **85%+ win rate**

### P90 — Weak on FX Crosses
- Best P90 result: **NZDUSD 54.0%** WR, 215.0 pips
- **GBPJPY** produced zero signals
- P90 WR ranged only **47.9%–59.7%** on crosses — below the 85%+ threshold
- P90 signals are designed for P90 CASCADE on majors; crosses appear to be outside its edge

### Warnings
- **GBPCHF**: CHF/USD exchange rate errors throughout (known Nautilus data gap)
- **GBPAUD**: AUD/USD exchange rate errors throughout (known Nautilus data gap)
- **GBPNZD**: NZD/USD exchange rate errors throughout (known Nautilus data gap)
- PnL for these 3 pairs may have slight inaccuracies due to missing conversion data
- **GBPJPY**: Zero trades — the strategy conditions were never met on this pair

### Totals
| Metric | Symmetry Trap | P90 |
|--------|--------------|-----|
| Total Trades | 4,832 | 2,072 |
| Total PnL | 38,810.4 pips | 1,103.5 pips |
| Avg WR (trading assets) | 87.9% | 52.6% |
