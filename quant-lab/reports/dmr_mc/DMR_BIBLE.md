# 📖 DMR BIBLE — Deep Mean Rebalancing Reference
## CEREBUS FX v4.0 | Strategy B: Resolution Output Stall Play

> **Last Updated:** 2026-06-29
> **Strategy Owner:** MAD LABS — Research Lead (RL)
> **Status:** ✅ VALIDATED — v1 Live on Demo, v2 Ready for Deployment

---

## 📋 TABLE OF CONTENTS

1. [Strategy Specification](#1-strategy-specification)
2. [P90 Calibration](#2-p90-calibration)
3. [Version History](#3-version-history)
4. [v2 Multi-Entry Results (Latest)](#4-v2-multi-entry-results-latest)
5. [v1 vs v2 Comparison](#5-v1-vs-v2-comparison)
6. [Monte Carlo Analysis](#6-monte-carlo-analysis)
7. [Portfolio Combinatorics](#7-portfolio-combinatorics)
8. [Grouping Analysis](#8-grouping-analysis)
9. [Live Deployment Config](#9-live-deployment-config)
10. [File Index](#10-file-index)

---

## 1. STRATEGY SPECIFICATION

### Source
CEREBUS FX v4.0 Manual, Strategy B (pages 8-9)

### Core Logic
```
P90 impulse → Price extends to 200% Deep State →
Enter LIMIT ORDER at DS → Price snaps back to activation (TP) →
Kill switch at 220% if continuation (SL)
```

### Parameters

| Parameter | Value | Reference |
|-----------|-------|-----------|
| **Entry** | LIMIT ORDER at 200% Deep State Level | Manual p.8 |
| **Deep State** | P90 close ± (200% × P90 body) in P90 direction | Manual p.8 |
| **Kill Switch (SL)** | P90 close ± (220% × P90 body) | Manual p.8 "8 pips beyond 200%" |
| **TP1** | Return to 0% (P90 activation close) | Manual p.8 |
| **DS Scan Window** | P90 time → 12:00 PM EST | Manual p.8 |
| **Hard Exit** | 5:00 PM EST | Manual p.8 |
| **AR Filter** | 3 < AR < 45 pips | Manual p.8 |
| **P90 Calibration** | Per-hour, 90th percentile from each pair's data | USDCHF EA method |
| **Activation Window** | 2:00 AM – 11:00 AM EST | Manual p.8 |
| **R:R Potential** | 1:5 to 1:7 | Manual p.8 |

### P90 Activation Windows (EURUSD Master Reference)

| Window (EST) | Threshold |
|-------------|-----------|
| 2:00 – 4:00 AM | >= 4.1 pips |
| 4:00 – 6:00 AM | >= 4.6 pips |
| 6:00 – 8:00 AM | >= 4.6 pips |
| 8:00 – 10:00 AM | >= 5.9 pips |
| 10:00 – 11:00 AM | >= 6.2 pips |

### When to AVOID (from Manual)
- Resolution output CLOSES strongly beyond 220% level
- Major news is imminent
- Asian Range > 45 pips (constraint deficit too wide)
- After 12:00 PM EST (DS scan window closed)

---

## 2. P90 CALIBRATION

### Method
Per-hour P90 thresholds computed from each pair's own M5 data (90th percentile of candle body sizes per EST hour). This matches the USDCHF MT5 EA calibration method.

### Calibration Table

| Pair | 2AM | 3AM | 4AM | 5AM | 6AM | 7AM | 8AM | 9AM | 10AM |
|------|-----|-----|-----|-----|-----|-----|-----|-----|------|
| **EURUSD** | 2.6 | 3.4 | 3.3 | 2.7 | 2.3 | 2.3 | 3.0 | 4.5 | 5.2 |
| **GBPUSD** | 3.3 | 4.3 | 4.2 | 3.5 | 3.0 | 3.1 | 4.0 | 6.5 | 7.6 |
| **USDCHF** | 2.0 | 2.6 | 4.0 | 4.7 | 4.2 | 3.8 | 3.4 | 3.8 | 5.7 |
| **USDJPY** | 8.0 | 9.3 | 8.0 | 6.4 | 5.7 | 6.0 | 6.8 | 8.4 | 9.3 |
| **GBPJPY** | 9.2 | 10.6 | 9.1 | 7.6 | 6.9 | 7.2 | 8.3 | 11.6 | 13.2 |
| **CHFJPY** | 7.4 | 8.7 | 7.3 | 6.1 | 5.6 | 5.8 | 6.7 | 9.2 | 10.7 |
| **BTCUSD** | 124 | 142 | 134 | 119 | 108 | 101 | 102 | 103 | 112 |
| **US500** | 2.4 | 2.8 | 2.4 | 2.0 | 1.8 | 1.7 | 2.1 | 2.6 | 3.7 |

*Full 30-pair calibration table in `dmr_deep_analysis_report.md`*

---

## 3. VERSION HISTORY

### v1 (Current Live)
- Single P90 entry per day (first valid P90 only)
- 14,582 trades, 92.6% WR, +215,661p PnL
- Running live on demo account

### v2 (Ready for Deployment)
- Multi-entry: one P90 per 2-hour window
- 32,102 trades, 91.4% WR, +568,752p PnL
- **+120% trades, +164% PnL** over v1
- Rolls the chain: after first P90 fires, looks for next one in next window

---

## 4. v2 MULTI-ENTRY RESULTS (LATEST — 30 PAIRS)

| Pair | Trades | WR | PF | PnL | TP | SL | HE |
|------|--------|----|----|-----|----|----|-----|
| **EURUSD** | 988 | 92.4% | 122.6 | +12,517p | 913 | 75 | 0 |
| **GBPUSD** | 1,921 | 92.2% | 118.2 | +25,786p | 1,771 | 150 | 0 |
| **USDCHF** | 1,425 | 91.2% | 122.3 | +19,449p | 1,298 | 125 | 2 |
| **USDJPY** | 1,841 | 90.2% | 95.6 | +24,863p | 1,661 | 180 | 0 |
| **AUDUSD** | 1,684 | 92.6% | 136.3 | +20,852p | 1,560 | 124 | 0 |
| **USDCAD** | 1,741 | 92.2% | 119.0 | +21,528p | 1,605 | 135 | 1 |
| **NZDUSD** | 1,352 | 91.3% | 115.2 | +15,960p | 1,232 | 117 | 3 |
| **GBPJPY** | 1,095 | 92.0% | 117.1 | +16,192p | 1,007 | 88 | 0 |
| **CHFJPY** | 1,129 | 90.5% | 104.3 | +16,132p | 1,022 | 107 | 0 |
| **AUDJPY** | 1,181 | 91.4% | 116.1 | +14,276p | 1,079 | 102 | 0 |
| **+ 20 more** | | | | | | | |
| **TOTAL** | **32,102** | **91.4%** | — | **+568,752p** | | | |

---

## 5. v1 vs v2 COMPARISON

| Metric | v1 (single entry) | v2 (multi-entry) | Delta |
|--------|-------------------|-------------------|-------|
| **Total Trades** | 14,582 | 32,102 | **+120%** |
| **Total PnL** | +215,661p | +568,752p | **+164%** |
| **Blended WR** | 92.6% | 91.4% | -1.3pp |
| **Avg Trade** | +14.8p | +17.7p | +20% |

### Per-Pair Delta

| Pair | v1 PnL | v2 PnL | Delta |
|------|--------|--------|-------|
| **GBPUSD** | +6,520 | +25,786 | **+295%** |
| **USDJPY** | +7,915 | +24,863 | **+214%** |
| **USDCAD** | +5,745 | +21,528 | **+275%** |
| **AUDUSD** | +7,637 | +20,852 | **+173%** |
| **EURUSD** | +4,601 | +12,517 | **+172%** |

---

## 6. MONTE CARLO ANALYSIS

### Simulation Parameters
- **Runs:** 10,000 per pair
- **Method:** Random shuffle of per-trade PnL (preserves distribution)
- **Initial Balance:** $10,000 reference

### Key Findings

| Metric | Value |
|--------|-------|
| **Ruin Rate** | 0.00% (all pairs) |
| **Max Consec Losses** | 2 (most forex pairs) |
| **Avg MaxDD (Forex)** | 2.9 pips |
| **Avg Trade Duration** | 10.4 minutes |
| **Trades/Day** | 1.0 per pair (v1), ~2.2 per pair (v2) |
| **Hard Exits** | 5 of 14,584 (0.03%) |

---

## 7. PORTFOLIO COMBINATORICS

### Minimum Pairs for 3+ Trades/Day

| Basket | Pairs | Trades/Day | WR | MaxDD |
|--------|-------|------------|-----|-------|
| **AUD basket** | AUDCAD, AUDCHF, AUDJPY | 3.0 | 92.7% | 2.7p |
| **Majors** | EURUSD, GBPUSD, USDJPY | 3.0 | ~92.5% | 6.4p |
| **Best WR** | GBPJPY, CHFJPY, NZDJPY, GBPNZD, EURAUD | 5.0 | 95.3% | 4.7p |

### Recommended Portfolios

| Profile | Pairs | Trades/Day | WR | MaxDD | Kelly |
|---------|-------|------------|-----|-------|-------|
| **Conservative** | 7 majors | 7.0 | 92.4% | 6.4p | 0.92 |
| **Balanced** | 5 (majors + JPY crosses) | 5.0 | 95.3% | 4.7p | 0.94 |
| **Full Forex** | 25 forex pairs | ~25 | 92.6% | 7.5p | 0.92 |
| **Maximum** | All 28 pairs | 28.0 | 92.6% | 90.9p | 0.92 |

---

## 8. GROUPING ANALYSIS

### By Currency Basket (v1)

| Basket | Pairs | Trades | WR | PF | PnL |
|--------|-------|--------|----|----|-----|
| **CHF** | 7 | 4,758 | 93.0% | 149.5 | +32,258p |
| **JPY** | 7 | 2,171 | 93.8% | 156.7 | +35,280p |
| **GBP** | 6 | 2,810 | 93.3% | 155.5 | +28,094p |
| **AUD** | 7 | 3,683 | 92.7% | 136.8 | +36,782p |
| **NZD** | 7 | 3,270 | 92.6% | 134.0 | +27,994p |
| **EUR** | 6 | 2,788 | 92.6% | 130.2 | +21,399p |
| **USD** | 8 | 5,272 | 92.1% | 124.5 | +46,898p |
| **CAD** | 5 | 3,415 | 92.2% | 114.2 | +25,466p |

### By Win Rate Tier (v1)

| Tier | Pairs | Trades | WR |
|------|-------|--------|-----|
| **95%+** | CHFJPY, GBPJPY, NZDJPY, XAUUSD | 821 | 95.7% |
| **93-95%** | 9 pairs | 4,211 | 93.6% |
| **90-93%** | 14 pairs | 8,544 | 92.3% |
| **87-90%** | BTCUSD, NZDUSD | 999 | 89.4% |

---

## 9. LIVE DEPLOYMENT CONFIG

### Current Live (v1)
```python
# 5 pairs, ~5 trades/day
DMR_LIVE = ["EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "CHFJPY"]
```

### Recommended Upgrade (v2)
```python
# Same pairs, but multi-entry per 2hr window
# Expected: ~11 trades/day (2.2x per pair)
DMR_LIVE_V2 = ["EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "CHFJPY"]
```

### Full Portfolio (v2)
```python
# All 25 forex pairs, ~55 trades/day
DMR_FULL = [
    "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD",
    "EURGBP", "EURJPY", "EURAUD", "EURCHF", "EURNZD",
    "GBPJPY", "GBPAUD", "GBPCHF", "GBPNZD",
    "AUDJPY", "AUDNZD", "AUDCAD", "AUDCHF",
    "CADJPY", "CADCHF",
    "NZDCHF", "NZDJPY", "NZDCAD", "CHFJPY",
]
```

### Risk Parameters

| Parameter | Value |
|-----------|-------|
| **Risk per trade** | 0.25% (prop) / 0.75% (trailing) |
| **Max daily loss** | 0.40% equity |
| **Max consecutive losses** | 6+ → stand down |
| **Kelly fraction** | Half-Kelly (0.45-0.48) |
| **Lot sizing** | FDE (Fixed Dollar Exposure) |

### Kill Switches

| Condition | Action |
|-----------|--------|
| **132% AR violation** | Close ALL immediately |
| **6+ consecutive losses** | Stand down — session done |
| **3 losing days** | Reduce risk temporarily |
| **7+ losing days** | Kill switch activated |

---

## 10. FILE INDEX

| File | Purpose |
|------|---------|
| `quant-lab/backtest/dmr_reconstructed.py` | v1 backtest engine (single entry) |
| `quant-lab/backtest/dmr_v2_multi_entry_test.py` | v2 backtest engine (multi-entry) |
| `quant-lab/backtest/dmr_mc_full.py` | Monte Carlo + deep stats |
| `quant-lab/backtest/dmr_combinatorics.py` | Portfolio combinatorics |
| `quant-lab/mt5/dmr_multi_pair_live.py` | v1 live engine (running on demo) |
| `quant-lab/mt5/dmr_multi_pair_live_v2.py` | v2 live engine (ready) |
| `scripts/discord_dmr_bot.py` | Discord bot (DMR-only signals) |
| `quant-lab/reports/dmr_sweep_full_report.md` | Full sweep report (30 pairs) |
| `quant-lab/reports/dmr_mc/dmr_deep_analysis_report.md` | Deep MC analysis |
| `quant-lab/reports/dmr_mc/DMR_BIBLE.md` | This file |
| `quant-lab/reports/dmr_mc/dmr_mc_full_results.json` | Raw MC data |
| `quant-lab/reports/dmr_v2_multi_entry_results.json` | v2 results |
| `quant-lab/configs/asset_configs.py` | Per-asset pip sizes, k-factors |

---

## Key Patterns Discovered

1. **0% ruin rate** — Not a single MC simulation produced negative terminal PnL
2. **Max consecutive losses = 2** — Strategy rarely loses twice in a row
3. **Max drawdown avg = 2.9 pips** — Extremely tight risk profile
4. **Kelly > 0.90** — Exceptional edge across all forex
5. **JPY crosses dominate** — CHFJPY, GBPJPY, NZDJPY are the sweet spot
6. **CHF basket is strongest** — 93.0% WR, PF 149.5
7. **No hard exits** — 0.03% hit hard exit (TP/SL always first)
8. **Balanced long/short** — No directional bias
9. **Avg duration 10.4 min** — Very fast in-and-out
10. **v2 multi-entry: +120% trades, +164% PnL** — Massive improvement

---

*DMR Bible v2.0 | 2026-06-29 | MAD LABS Quant Research*
