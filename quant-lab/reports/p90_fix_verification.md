# P90 Fix Verification — Multi-Asset Backtest Report

**Generated:** 2026-06-03 18:55:24

## Fixes Applied

1. **Asset-specific MIN_P90_BODY thresholds** — JPY crosses require 8-12p body vs 4p for majors
2. **RR >= 1.0 gate** — Skip trades where TP1 doesn't cover the SL risk
3. **Band-edge TP calculation** — TP measured from Asian High/Low edge, not from entry price
4. **Cascade 90min hard cutoff + 3-filter** — Cascade requires: 30-90min window, same direction, body >= minimum

## Summary Table

| Asset | Trades | WR% | Avg RR | Min RR | Max RR | Sub-1RR | Gross P&L | Net P&L | PF |
|-------|--------|-----|--------|--------|--------|---------|-----------|---------|-----|
| EURUSD | 356 | 100.0% | 1.35 | 1.00 | 2.81 | 0 | +4437.5p | +4188.3p | 1000.00 |
| USDCHF | 415 | 100.0% | 1.58 | 1.00 | 3.75 | 0 | +6420.5p | +6130.0p | 1000.00 |
| NZDUSD | 208 | 100.0% | 1.71 | 1.01 | 3.04 | 0 | +3507.0p | +3361.4p | 1000.00 |
| GBPJPY | 2279 | 100.0% | 2.48 | 1.00 | 6.00 | 0 | +76672.5p | +74899.9p | 1000.00 |
| CHFJPY | 1634 | 100.0% | 2.84 | 1.00 | 7.00 | 0 | +46485.0p | +45214.1p | 1000.00 |
| GBPAUD | 1913 | 100.0% | 2.59 | 1.00 | 6.50 | 0 | +71247.5p | +69908.4p | 1000.00 |
| GBPUSD | 1376 | 100.0% | 1.61 | 1.00 | 3.61 | 0 | +22724.5p | +21761.3p | 1000.00 |
| GBPNZD | 1927 | 100.0% | 2.77 | 1.00 | 7.38 | 0 | +77649.0p | +76300.1p | 1000.00 |
| GBPCHF | 1138 | 100.0% | 2.48 | 1.01 | 5.50 | 0 | +30091.5p | +29294.9p | 1000.00 |
| USDJPY | 1087 | 100.0% | 2.97 | 1.00 | 7.33 | 0 | +32446.0p | +31600.6p | 1000.00 |

**Total Trades:** 12333 | **Total Net PnL:** +371681.0 pips | **Sub-1.0 RR trades:** 0

## Key Verification: Did Fixes Eliminate Sub-1.0 RR Trades?

**PASS: Zero sub-1.0 RR trades across all assets.** The RR gate and asset thresholds are working correctly.


## Per-Asset Detail

### EURUSD

- **Total Trades:** 356 (W:356 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 1.35
- **Min Intended RR:** 1.00
- **Max Intended RR:** 2.81
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +4437.5 pips
- **Net P&L (after commission):** +4188.3 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 216,820 bars, 911 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 201 | 100.0% | 1.39 | 1.01 | +2528.5p |
| CASCADE | 15 | 100.0% | 1.18 | 1.01 | +186.0p |
| EWS | 140 | 100.0% | 1.31 | 1.00 | +1723.0p |

### USDCHF

- **Total Trades:** 415 (W:415 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 1.58
- **Min Intended RR:** 1.00
- **Max Intended RR:** 3.75
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +6420.5 pips
- **Net P&L (after commission):** +6130.0 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 253,031 bars, 1061 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 189 | 100.0% | 1.58 | 1.01 | +2854.5p |
| CASCADE | 7 | 100.0% | 1.58 | 1.06 | +118.0p |
| EWS | 219 | 100.0% | 1.59 | 1.00 | +3448.0p |

### NZDUSD

- **Total Trades:** 208 (W:208 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 1.71
- **Min Intended RR:** 1.01
- **Max Intended RR:** 3.04
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +3507.0 pips
- **Net P&L (after commission):** +3361.4 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 277,586 bars, 1346 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 108 | 100.0% | 1.74 | 1.01 | +1803.0p |
| CASCADE | 9 | 100.0% | 1.47 | 1.05 | +148.0p |
| EWS | 91 | 100.0% | 1.71 | 1.02 | +1556.0p |

### GBPJPY

- **Total Trades:** 2279 (W:2279 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 2.48
- **Min Intended RR:** 1.00
- **Max Intended RR:** 6.00
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +76672.5 pips
- **Net P&L (after commission):** +74899.9 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 277,556 bars, 1346 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 418 | 100.0% | 2.01 | 1.01 | +11670.5p |
| CASCADE | 48 | 100.0% | 1.92 | 1.05 | +1365.0p |
| EWS | 1813 | 100.0% | 2.60 | 1.00 | +63637.0p |

### CHFJPY

- **Total Trades:** 1634 (W:1634 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 2.84
- **Min Intended RR:** 1.00
- **Max Intended RR:** 7.00
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +46485.0 pips
- **Net P&L (after commission):** +45214.1 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 277,510 bars, 1346 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 358 | 100.0% | 2.24 | 1.01 | +7727.0p |
| CASCADE | 26 | 100.0% | 1.85 | 1.02 | +618.0p |
| EWS | 1250 | 100.0% | 3.03 | 1.00 | +38140.0p |

### GBPAUD

- **Total Trades:** 1913 (W:1913 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 2.59
- **Min Intended RR:** 1.00
- **Max Intended RR:** 6.50
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +71247.5 pips
- **Net P&L (after commission):** +69908.4 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 277,725 bars, 1346 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 270 | 100.0% | 2.09 | 1.00 | +8011.5p |
| CASCADE | 24 | 100.0% | 1.83 | 1.19 | +611.0p |
| EWS | 1619 | 100.0% | 2.68 | 1.00 | +62625.0p |

### GBPUSD

- **Total Trades:** 1376 (W:1376 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 1.61
- **Min Intended RR:** 1.00
- **Max Intended RR:** 3.61
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +22724.5 pips
- **Net P&L (after commission):** +21761.3 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 277,647 bars, 1346 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 550 | 100.0% | 1.62 | 1.00 | +9090.0p |
| CASCADE | 45 | 100.0% | 1.47 | 1.02 | +731.5p |
| EWS | 781 | 100.0% | 1.61 | 1.00 | +12903.0p |

### GBPNZD

- **Total Trades:** 1927 (W:1927 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 2.77
- **Min Intended RR:** 1.00
- **Max Intended RR:** 7.38
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +77649.0 pips
- **Net P&L (after commission):** +76300.1 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 277,742 bars, 1347 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 247 | 100.0% | 2.21 | 1.01 | +7963.5p |
| CASCADE | 22 | 100.0% | 2.19 | 1.02 | +710.5p |
| EWS | 1658 | 100.0% | 2.86 | 1.00 | +68975.0p |

### GBPCHF

- **Total Trades:** 1138 (W:1138 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 2.48
- **Min Intended RR:** 1.01
- **Max Intended RR:** 5.50
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +30091.5 pips
- **Net P&L (after commission):** +29294.9 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 277,619 bars, 1346 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 250 | 100.0% | 2.17 | 1.01 | +5724.0p |
| CASCADE | 23 | 100.0% | 1.95 | 1.13 | +507.5p |
| EWS | 865 | 100.0% | 2.58 | 1.01 | +23860.0p |

### USDJPY

- **Total Trades:** 1087 (W:1087 L:0)
- **Win Rate:** 100.0%
- **Avg Intended RR:** 2.97
- **Min Intended RR:** 1.00
- **Max Intended RR:** 7.33
- **Sub-1.0 RR Trades:** 0
- **Gross P&L:** +32446.0 pips
- **Net P&L (after commission):** +31600.6 pips
- **Profit Factor:** 1000.00
- **Max Drawdown:** 0.0 pips
- **Data:** 277,717 bars, 1346 sessions

| Variant | Trades | WR% | Avg RR | Min RR | PnL |
|---------|--------|-----|--------|--------|------|
| INITIAL | 258 | 100.0% | 2.48 | 1.00 | +6282.0p |
| CASCADE | 17 | 100.0% | 1.91 | 1.05 | +432.0p |
| EWS | 812 | 100.0% | 3.15 | 1.01 | +25732.0p |


---
*Report generated by p90_fix_verification.py @ 2026-06-03 18:55:24*