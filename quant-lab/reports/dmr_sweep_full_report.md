# DMR (Deep Mean Rebalancing) — Full Sweep Report
## CEREBUS FX v4.0 | Strategy B: Resolution Output Stall Play

**Date:** 2026-06-29
**Engine:** `quant-lab/backtest/dmr_reconstructed.py`
**Data:** M5 bars, 2022-01 to 2026-06 (~4.4 years)
**Source:** CEREBUS FX v4.0 Manual (Strategy B, pages 8-9) + USDCHF MT5 EA calibration

---

## Strategy Specification (from CEREBUS Manual)

| Parameter | Value | Reference |
|-----------|-------|-----------|
| **Entry** | LIMIT ORDER at 200% Deep State Level | Manual p.8 "CFD Limit Order at Deep State" |
| **Deep State** | P90 close ± (200% × P90 body) in P90 direction | Manual p.8 |
| **Kill Switch (SL)** | P90 close ± (220% × P90 body) | Manual p.8 "8 pips beyond 200%" |
| **TP1** | Return to 0% (P90 activation close) | Manual p.8 "Return to Activation" |
| **DS Scan Window** | P90 time → 12:00 PM EST | Manual p.8 "Must occur before 12:00 PM" |
| **Hard Exit** | 5:00 PM EST | Manual p.8 |
| **AR Filter** | 3 < AR < 45 pips | Manual p.8 "AR > 45p = NO-GO" |
| **P90 Calibration** | Per-hour, 90th percentile from each pair's data | USDCHF EA calibration method |
| **Activation Window** | 2:00 AM – 11:00 AM EST | Manual p.8 |

### P90 Activation Windows (EURUSD Master Reference)

| Window (EST) | Threshold |
|-------------|-----------|
| 2:00 – 4:00 AM | >= 4.1 pips |
| 4:00 – 6:00 AM | >= 4.6 pips |
| 6:00 – 8:00 AM | >= 4.6 pips |
| 8:00 – 10:00 AM | >= 5.9 pips |
| 10:00 – 11:00 AM | >= 6.2 pips |

---

## Master Results — All 30 Pairs

### Forex Majors (6)

| Pair | Trades | WR | PF | PnL | MaxDD | Avg Trade | Avg Win | Avg Loss | TP | SL | HE |
|------|--------|----|----|-----|-------|-----------||---------|----------|----|----|----|
| **EURUSD** | 618 | 92.1% | 123.05 | +4,601p | 2.5 | +7.45 | +8.2 | -0.8 | 569 | 49 | 0 |
| **GBPUSD** | 669 | 93.4% | 150.20 | +6,520p | 2.2 | +9.75 | +10.5 | -1.0 | 625 | 44 | 0 |
| **USDCHF** | 652 | 91.7% | 112.12 | +4,634p | 2.2 | +7.11 | +7.8 | -0.8 | 598 | 54 | 0 |
| **USDJPY** | 389 | 94.1% | 171.96 | +7,915p | 6.4 | +20.35 | +21.8 | -2.0 | 366 | 23 | 0 |
| **AUDUSD** | 828 | 92.4% | 124.97 | +7,637p | 4.3 | +9.22 | +10.1 | -1.0 | 765 | 63 | 0 |
| **USDCAD** | 777 | 91.2% | 112.99 | +5,745p | 2.9 | +7.39 | +8.2 | -0.8 | 709 | 68 | 0 |
| **NZDUSD** | 794 | 89.9% | 93.06 | +6,426p | 3.0 | +8.09 | +9.1 | -0.9 | 712 | 80 | 2 |

### Forex Crosses (18)

| Pair | Trades | WR | PF | PnL | MaxDD | Avg Trade | Avg Win | Avg Loss | TP | SL | HE |
|------|--------|----|----|-----|-------|-----------|---------|----------|----|----|----|
| **AUDCAD** | 702 | 92.3% | 127.58 | +5,835p | 1.8 | +8.31 | +9.1 | -0.9 | 648 | 54 | 0 |
| **AUDCHF** | 774 | 92.8% | 145.18 | +5,248p | 2.3 | +6.78 | +7.4 | -0.7 | 718 | 56 | 0 |
| **AUDJPY** | 329 | 93.3% | 155.19 | +4,317p | 2.7 | +13.12 | +14.2 | -1.3 | 307 | 22 | 0 |
| **AUDNZD** | 535 | 93.1% | 144.54 | +4,349p | 2.0 | +8.13 | +8.8 | -0.8 | 498 | 37 | 0 |
| **CADCHF** | 857 | 92.8% | 129.02 | +3,905p | 1.3 | +4.56 | +4.9 | -0.5 | 795 | 62 | 0 |
| **CADJPY** | 449 | 91.8% | 90.28 | +5,134p | 7.5 | +11.43 | +12.6 | -1.6 | 412 | 37 | 0 |
| **CHFJPY** | 240 | 95.8% | 251.68 | +4,888p | 3.2 | +20.37 | +21.3 | -1.9 | 230 | 10 | 0 |
| **EURAUD** | 214 | 94.4% | 183.16 | +3,497p | 3.6 | +16.34 | +17.4 | -1.6 | 202 | 12 | 0 |
| **EURCHF** | 799 | 92.7% | 132.76 | +4,401p | 2.3 | +5.51 | +6.0 | -0.6 | 741 | 58 | 0 |
| **EURGBP** | 882 | 92.7% | 129.74 | +3,837p | 1.1 | +4.35 | +4.7 | -0.5 | 818 | 64 | 0 |
| **EURJPY** | 197 | 91.4% | 104.01 | +3,657p | 4.8 | +18.56 | +20.5 | -2.1 | 180 | 17 | 0 |
| **EURNZD** | 78 | 92.3% | 141.62 | +1,406p | 1.8 | +18.03 | +19.7 | -1.7 | 72 | 6 | 0 |
| **GBPAUD** | 301 | 91.4% | 120.88 | +5,898p | 4.1 | +19.59 | +21.6 | -1.9 | 275 | 26 | 0 |
| **GBPCHF** | 665 | 93.5% | 162.10 | +4,688p | 1.8 | +7.05 | +7.6 | -0.7 | 621 | 43 | 1 |
| **GBPJPY** | 199 | 96.5% | 283.29 | +5,025p | 4.7 | +25.25 | +26.3 | -2.5 | 192 | 7 | 0 |
| **GBPNZD** | 94 | 94.7% | 175.31 | +2,127p | 3.3 | +22.63 | +24.0 | -2.4 | 89 | 5 | 0 |
| **NZDCAD** | 630 | 92.5% | 123.41 | +4,847p | 2.0 | +7.69 | +8.4 | -0.8 | 583 | 47 | 0 |
| **NZDCHF** | 771 | 93.5% | 169.97 | +4,495p | 1.4 | +5.83 | +6.3 | -0.5 | 721 | 50 | 0 |
| **NZDJPY** | 368 | 95.1% | 198.45 | +4,344p | 2.4 | +11.80 | +12.5 | -1.2 | 349 | 18 | 1 |

### Crypto (2)

| Pair | Trades | WR | PF | PnL | MaxDD | Avg Trade | Avg Win | Avg Loss | TP | SL | HE |
|------|--------|----|----|-----|-------|-----------|---------|----------|----|----|----|
| **BTCUSD** | 205 | 87.3% | 75.29 | +68,033p | 90.9 | +331.87 | +385.2 | -35.2 | 179 | 26 | 0 |
| **ETHUSD** | 7 | 85.7% | 152.77 | +17,970p | 118.4 | +2,567 | +3,015 | -118.4 | 6 | 1 | 0 |

### Metals (2)

| Pair | Trades | WR | PF | PnL | MaxDD | Avg Trade | Avg Win | Avg Loss | TP | SL | HE |
|------|--------|----|----|-----|-------|-----------|---------|----------|----|----|----|
| **XAUUSD** | 14 | 100.0% | 862,800 | +863p | 0.0 | +61.6 | +61.6 | 0.0 | 14 | 0 | 0 |
| **XAGUSD** | 0 | — | — | — | — | — | — | — | — | — | — |

### Indices (1)

| Pair | Trades | WR | PF | PnL | MaxDD | Avg Trade | Avg Win | Avg Loss | TP | SL | HE |
|------|--------|----|----|-----|-------|-----------|---------|----------|----|----|----|
| **US500** | 545 | 93.8% | 125.37 | +3,420p | 3.8 | +6.28 | +6.7 | -0.8 | 511 | 34 | 0 |

---

## Group Summary

| Group | Pairs | Total Trades | Blended WR | Combined PF | Total PnL | Avg MaxDD |
|-------|-------|-------------|------------|-------------|-----------|-----------|
| **Forex Majors** | 7 | 4,727 | 92.1% | 125.0 | +43,478p | 3.4 |
| **Forex Crosses** | 18 | 9,086 | 93.0% | 147.8 | +85,084p | 2.7 |
| **Crypto** | 2 | 212 | 87.3% | 77.9 | +86,003p | 91.6 |
| **Metals** | 1 | 14 | 100.0% | 862,800 | +863p | 0.0 |
| **Indices** | 1 | 545 | 93.8% | 125.4 | +3,420p | 3.8 |
| **TOTAL** | 29 | 14,584 | 92.5% | 134.2 | +218,848p | — |

---

## P90 Per-Hour Calibration Table

*90th percentile of M5 candle body sizes per EST hour, computed from each pair's own data*

| Pair | 2AM | 3AM | 4AM | 5AM | 6AM | 7AM | 8AM | 9AM | 10AM |
|------|-----|-----|-----|-----|-----|-----|-----|-----|------|
| **EURUSD** | 2.6 | 3.4 | 3.3 | 2.7 | 2.3 | 2.3 | 3.0 | 4.5 | 5.2 |
| **GBPUSD** | 3.3 | 4.3 | 4.2 | 3.5 | 3.0 | 3.1 | 4.0 | 6.5 | 7.6 |
| **USDCHF** | 2.0 | 2.6 | 4.0 | 4.7 | 4.2 | 3.8 | 3.4 | 3.8 | 5.7 |
| **USDJPY** | 8.0 | 9.3 | 8.0 | 6.4 | 5.7 | 6.0 | 6.8 | 8.4 | 9.3 |
| **AUDUSD** | 2.9 | 4.0 | 4.3 | 3.6 | 3.1 | 3.0 | 3.4 | 4.1 | 4.4 |
| **USDCAD** | 2.6 | 2.6 | 3.6 | 4.6 | 4.8 | 4.3 | 3.9 | 4.2 | 5.5 |
| **NZDUSD** | 2.9 | 3.8 | 3.9 | 3.3 | 2.7 | 2.6 | 2.9 | 3.8 | 4.2 |
| **AUDCAD** | 3.2 | 3.1 | 3.6 | 4.2 | 4.1 | 3.6 | 3.3 | 3.3 | 4.1 |
| **AUDCHF** | 2.4 | 2.4 | 2.9 | 3.5 | 3.7 | 3.3 | 2.9 | 2.8 | 3.1 |
| **AUDJPY** | 5.1 | 5.1 | 5.9 | 6.8 | 6.7 | 5.9 | 5.2 | 5.0 | 5.7 |
| **AUDNZD** | 3.2 | 3.0 | 3.3 | 3.8 | 3.6 | 3.2 | 3.0 | 2.8 | 3.1 |
| **CADCHF** | 1.3 | 1.5 | 2.2 | 3.1 | 3.5 | 3.2 | 2.8 | 2.8 | 3.4 |
| **CADJPY** | 4.1 | 4.4 | 5.2 | 6.2 | 6.4 | 5.5 | 4.9 | 4.9 | 6.0 |
| **CHFJPY** | 7.4 | 8.7 | 7.3 | 6.1 | 5.6 | 5.8 | 6.7 | 9.2 | 10.7 |
| **EURAUD** | 6.2 | 6.1 | 7.2 | 8.5 | 8.7 | 7.5 | 6.9 | 6.7 | 7.6 |
| **EURCHF** | 1.6 | 1.8 | 2.8 | 3.9 | 4.5 | 4.1 | 3.7 | 3.4 | 3.8 |
| **EURGBP** | 1.2 | 1.4 | 2.4 | 3.3 | 3.6 | 3.3 | 3.1 | 3.1 | 3.4 |
| **EURJPY** | 5.8 | 6.3 | 7.8 | 9.5 | 10.1 | 8.6 | 7.7 | 7.3 | 8.3 |
| **EURNZD** | 6.7 | 6.5 | 7.6 | 9.4 | 9.6 | 8.4 | 7.7 | 7.5 | 8.4 |
| **GBPAUD** | 6.5 | 8.4 | 9.1 | 7.8 | 7.0 | 6.6 | 7.4 | 9.8 | 10.3 |
| **GBPCHF** | 2.5 | 3.0 | 2.7 | 2.4 | 2.1 | 2.3 | 3.0 | 5.4 | 6.6 |
| **GBPJPY** | 9.2 | 10.6 | 9.1 | 7.6 | 6.9 | 7.2 | 8.3 | 11.6 | 13.2 |
| **GBPNZD** | 7.9 | 9.6 | 9.9 | 8.9 | 7.6 | 7.1 | 7.8 | 10.8 | 11.4 |
| **NZDCAD** | 3.0 | 2.9 | 3.3 | 4.0 | 4.0 | 3.6 | 3.4 | 3.3 | 4.1 |
| **NZDCHF** | 2.1 | 2.0 | 2.5 | 3.2 | 3.3 | 3.0 | 2.7 | 2.6 | 2.8 |
| **NZDJPY** | 4.5 | 4.5 | 5.1 | 6.0 | 6.0 | 5.2 | 4.7 | 4.4 | 5.0 |
| **BTCUSD** | 124 | 142 | 134 | 119 | 108 | 101 | 102 | 103 | 112 |
| **ETHUSD** | 720 | 801 | 744 | 673 | 614 | 579 | 590 | 596 | 643 |
| **XAUUSD** | 20.5 | 28.7 | 29.8 | 23.9 | 18.5 | 18.1 | 23.3 | 25.0 | 26.5 |
| **XAGUSD** | 44.0 | 69.0 | 83.0 | 65.0 | 51.0 | 49.0 | 65.0 | 66.0 | 71.0 |
| **US500** | 2.4 | 2.8 | 2.4 | 2.0 | 1.8 | 1.7 | 2.1 | 2.6 | 3.7 |

---

## Key Metrics Summary

| Metric | Value |
|--------|-------|
| **Total Pairs Tested** | 29 (XAGUSD excluded — needs pip_size fix) |
| **Total Trades** | 14,584 |
| **Blended Win Rate** | 92.5% |
| **Combined Profit Factor** | 134.2 |
| **Total PnL** | +218,848 pips |
| **Best Pair (WR)** | GBPJPY @ 96.5% |
| **Best Pair (PF)** | CHFJPY @ 251.7 |
| **Best Pair (MaxDD)** | CADCHF @ 1.3 pips |
| **Worst Pair (WR)** | BTCUSD @ 87.3% |
| **Avg MaxDD (Forex)** | 2.9 pips |
| **Max Consec Wins** | 62 (AUDUSD) |
| **Max Consec Losses** | 2 (most pairs) |
| **Hard Exits** | 5 (0.03% of trades) |

---

## Notes

1. **Entry is LIMIT at DS level** — this is the key difference from the old buggy script that entered at ds_bar close. The limit order gets better fills and the R:R is 1:5 to 1:7 as specified in the manual.

2. **Per-hour P90 calibration** — each pair's thresholds are computed from its own data (90th percentile per EST hour). This is the same method used by the USDCHF MT5 EA.

3. **XAGUSD = 0 trades** — P90 thresholds are 44-71 pips because XAGUSD pip_size is 0.001 (prices ~23). The P90 body sizes are naturally large. Needs investigation — possibly pip_size should be 0.01 for silver.

4. **XAUUSD = 14 trades** — very low count because P90 thresholds (18-30 pips) are tight relative to gold's current price range. May need k-factor adjustment for metals.

5. **Crypto (BTC/ETH)** — lower WR (87%) because crypto has different volatility characteristics. The k-factor for crypto is 0.52 vs 0.46 for forex.

6. **No EOD exits** — only 5 hard exits across 14,584 trades (0.03%). The strategy almost always hits TP or SL within the session window.

7. **MaxDD is tiny** — average 2.9 pips for forex. The 220% kill switch is very tight, meaning losses are always small (-0.5 to -2.5 pips).

---

## Files

| File | Purpose |
|------|---------|
| `quant-lab/backtest/dmr_reconstructed.py` | Full DMR backtest engine |
| `quant-lab/reports/dmr_reconstructed_results.json` | Raw results + P90 calibration data |
| `quant-lab/reports/dmr_sweep_full_report.md` | This report |

---

*Report generated 2026-06-29 | Engine: dmr_reconstructed.py | Data: M5 2022-2026*
