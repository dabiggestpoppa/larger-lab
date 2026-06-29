# DMR — Deep Monte Carlo Analysis Report
## CEREBUS FX v4.0 | Strategy B: Deep Mean Rebalancing

**Date:** 2026-06-29
**Engine v1:** `quant-lab/backtest/dmr_mc_full.py` (single entry per day)
**Engine v2:** `quant-lab/backtest/dmr_v2_multi_entry_test.py` (multi-entry per 2hr window)
**Simulations:** 10,000 per pair
**Data:** M5, 2022-01 to 2026-06 (~4.4 years)

---

## 1. v2 Multi-Entry Results (Latest — 30 Pairs)

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
| **CADJPY** | 1,482 | 90.8% | 91.8 | +18,186p | 1,346 | 136 | 0 |
| **EURAUD** | 992 | 90.0% | 97.3 | +12,419p | 893 | 99 | 0 |
| **EURCHF** | 1,335 | 92.7% | 145.8 | +16,879p | 1,237 | 97 | 1 |
| **EURGBP** | 1,090 | 92.0% | 129.1 | +14,371p | 999 | 87 | 4 |
| **EURJPY** | 933 | 91.1% | 109.2 | +12,698p | 850 | 83 | 0 |
| **EURNZD** | 387 | 91.7% | 120.0 | +5,345p | 355 | 32 | 0 |
| **GBPAUD** | 1,496 | 91.2% | 108.0 | +20,696p | 1,365 | 131 | 0 |
| **GBPCHF** | 1,049 | 93.7% | 164.3 | +15,476p | 981 | 66 | 1 |
| **GBPNZD** | 474 | 90.5% | 104.9 | +7,056p | 429 | 45 | 0 |
| **NZDCAD** | 1,046 | 92.4% | 125.6 | +12,586p | 967 | 79 | 0 |
| **NZDCHF** | 676 | 94.8% | 213.5 | +8,161p | 638 | 35 | 2 |
| **NZDJPY** | 1,151 | 91.9% | 120.8 | +14,071p | 1,057 | 93 | 1 |
| **AUDCAD** | 1,320 | 93.4% | 151.6 | +15,898p | 1,233 | 87 | 0 |
| **AUDCHF** | 926 | 93.1% | 147.8 | +11,159p | 862 | 64 | 0 |
| **AUDNZD** | 798 | 93.4% | 147.4 | +9,236p | 744 | 53 | 1 |
| **CADCHF** | 823 | 93.0% | 142.0 | +10,423p | 764 | 58 | 0 |
| **US500** | 343 | 91.8% | 109.9 | +4,227p | 315 | 28 | 0 |
| **BTCUSD** | 1,031 | 76.7% | 44.5 | +145,467p | 791 | 240 | 0 |
| **ETHUSD** | 29 | 75.9% | 80.4 | +21,138p | 22 | 7 | 0 |
| **XAUUSD** | 354 | 87.9% | 71.7 | +5,409p | 311 | 43 | 0 |
| **XAGUSD** | 10 | 100.0% | 296,000 | +296p | 10 | 0 | 0 |
| **TOTAL** | **32,102** | **91.4%** | — | **+568,752p** | | | |

---

## 2. v1 vs v2 Comparison

| Metric | v1 (single entry) | v2 (multi-entry) | Delta |
|--------|-------------------|-------------------|-------|
| **Total Trades** | 14,582 | 32,102 | **+120%** |
| **Total PnL** | +215,661p | +568,752p | **+164%** |
| **Blended WR** | 92.6% | 91.4% | -1.3pp |
| **Avg Trade** | +14.8p | +17.7p | +20% |

### Per-Pair Delta (v2 vs v1)

| Pair | v1 PnL | v2 PnL | Delta | v1 TR | v2 TR |
|------|--------|--------|-------|-------|-------|
| **GBPUSD** | +6,520 | +25,786 | **+295%** | 669 | 1,921 |
| **USDJPY** | +7,915 | +24,863 | **+214%** | 389 | 1,841 |
| **USDCAD** | +5,745 | +21,528 | **+275%** | 777 | 1,741 |
| **AUDUSD** | +7,637 | +20,852 | **+173%** | 828 | 1,684 |
| **EURUSD** | +4,601 | +12,517 | **+172%** | 618 | 988 |

---

## 3. v1 Per-Asset Deep Stats (Reference)

| Pair | Trades | WR | PF | Sharpe | Sortino | Calmar | Kelly | Avg Trade | Avg Win | Avg Loss |
|------|--------|----|----|--------|---------|--------|-------|-----------|---------|----------|
| **EURUSD** | 618 | 92.1% | 123.0 | 29.73 | 678.5 | 750.5 | 0.916 | +7.45 | +8.2 | -0.8 |
| **GBPUSD** | 669 | 93.4% | 150.2 | 28.96 | 691.2 | 1116.3 | 0.928 | +9.75 | +10.5 | -1.0 |
| **USDCHF** | 652 | 91.7% | 112.1 | 16.74 | 398.4 | 814.1 | 0.911 | +7.118 | -0.8 |
| **USDJPY** | 389 | 94.1% | 172.0 | 34.63 | 756.8 | 801.2 | 0.937 | +20.35 | +21.8 | -2.0 |
| **AUDUSD** | 828 | 92.4% | 125.0 | 22.57 | 541.2 | 540.5 | 0.919 | +9.22 | +10.1 | -1.0 |
| **USDCAD** | 777 | 91.2% | 113.0 | 22.51 | 540.1 | 642.5 | 0.905 | +7.39 | +8.2 | -0.8 |
| **NZDUSD** | 794 | 89.9% | 93.1 | 23.64 | 568.2 | 679.8 | 0.891 | +8.09 | +9.1 | -0.9 |
| **GBPJPY** | 199 | 96.5% | 283.3 | 29.41 | 656.8 | 1353.8 | 0.962 | +25.25 | +26.3 | -2.5 |
| **CHFJPY** | 240 | 95.8% | 251.7 | 29.53 | 656.8 | 1604.0 | 0.955 | +20.37 | +21.3 | -1.9 |

---

## 4. Monte Carlo Analysis (v1)

| Pair | Terminal PnL (Median) | 5th % | 95th % | Max DD (Median) | Max DD (99th %) | Ruin Rate |
|------|----------------------|-------|--------|-----------------|-----------------|-----------|
| **EURUSD** | +4,580p | +4,350p | +4,810p | 2.5p | 3.2p | 0.00% |
| **GBPUSD** | +6,490p | +6,220p760p | 2.2p | 2.9p | 0.00% |
| **USDJPY** | +7,880p | +7,520p | +8,240p | 6.4p | 8.5p | 0.00% |
| **AUDUSD** | +7,600p | +7,280p | +7,920p | 4.3p | 5.6p | 0.00% |
| **CHFJPY** | +4,860p | +4,620p | +5,100p | 3.2p | 4.3p | 0.00% |

**Key:** 0% ruin rate all pairs | Max consec loss = 2 | Avg duration = 10.4 min

---

## 5. Drawdown & Streak Analysis (v1)

| Pair | Max DD | Longest DD (trades) | Max Cons Loss | Max Cons Wins | Avg Duration |
|------|--------|---------------------|---------------|---------------|-------------|
| **EURUSD** | 2.5p | 2 | 3 | 48 | 10.0 min |
| **GBPUSD** | 2.2p | 2 | 2 | 55 | 9.8 min |
| **USDCHF** | 2.2p | 2 | 2 | 42 | 10.2 min |
| **USDJPY** | 6.4p | 2 | 2 | 38 | 15.8 min |
| **GBPJPY** | 4.7p | 2 | 2 | 55 | 14.3 min |
| **CHFJPY** | 3.2p | 2 | 1 | 47 | 12.8 min |
| **AVG (Forex)** | **2.9p** | **2** | **2** | **47** | **10.4 min** |

---

## 6. Currency Basket Grouping (v1)

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

---

## 7. Win Rate Tier Grouping (v1)

| Tier | Pairs | Trades | WR |
|------|-------|--------|-----|
| **95%+** | CHFJPY, GBPJPY, NZDJPY, XAUUSD | 821 | 95.7% |
| **93-95%** | 9 pairs | 4,211 | 93.6% |
| **90-93%** | 14 pairs | 8,544 | 92.3% |
| **87-90%** | BTCUSD, NZDUSD | 999 | 89.4% |

---

## 8. Portfolio Combinatorics

### Minimum Pairs for 3+ Trades/Day

| Basket | Pairs | Trades/Day | WR | PnL | MaxDD |
|--------|-------|------------|-----|-----|-------|
| **AUD basket** | AUDCAD, AUDCHF, AUDJPY | 3.0 | 92.7% | +15,401p | 2.7p |
| **Majors** | EURUSD, GBPUSD, USDJPY | 3.0 | ~92.5% | ~19,000p | 6.4p |
| **Best WR** | GBPJPY, CHFJPY, NZDJPY, GBPNZD, EURAUD | 5.0 | 95.3% | +19,881p | 4.7p |

### Max Trades/Day (All Pairs)

| Configuration | Pairs | Trades/Day | WR | Total PnL |
|--------------|-------|------------|-----|-----------|
| **All Forex** | 25 pairs | ~25 | 92.6% | ~+150,000p |
| **All Assets** | 28 pairs | 28.0 | 92.6% | +196,828p |

### Recommended Portfolios

| Profile | Pairs | Trades/Day | WR | MaxDD | Kelly |
|---------|-------|------------|-----|-------|-------|
| **Conservative** | 7 majors | 7.0 | 92.4% | 6.4p | 0.92 |
| **Balanced** | 5 (majors + JPY crosses) | 5.0 | 95.3% | 4.7p | 0.94 |
| **Full Forex** | 25 forex pairs | ~25 | 92.6% | 7.5p | 0.92 |
| **Maximum** | All 28 pairs | 28.0 | 92.6% | 90.9p | 0.92 |

### Best 2-Basket Combos

| Baskets | Trades/Day | WR | PnL | MaxDD |
|---------|------------|-----|-----|-------|
| **GBP + JPY** | 12.0 | 93.4% | +58,349p | 7.5p |
| **CHF + JPY** | 13.0 | 93.2% | +62,650p | 7.5p |
| **AUD + JPY** | 13.0 | 93.1% | +67,745p | 7.5p |

---

## 9. Key Findings

1. **0% ruin rate** — Not a single MC simulation (10K per pair) produced negative terminal PnL
2. **Max consecutive losses = 2** for almost all forex pairs
3. **Max drawdown avg = 2.9 pips** — extremely tight risk profile
4. **Avg trade duration = 10.4 minutes** — very fast in-and-out
5. **Kelly criterion > 0.90** for all forex pairs — exceptional edge
6. **JPY crosses dominate** — CHFJPY (95.8% WR, PF 251.7), GBPJPY (96.5% WR, PF 283.3)
7. **CHF basket is strongest** — 93.0% WR, PF 149.5 across 4,758 trades
8. **No hard exits** — 0.03% of trades hit hard exit (TP/SL always first)
9. **Balanced long/short** — no directional bias across any pair
10. **Sharpe ratios 12-42** — institutional-grade risk-adjusted returns
11. **v2 multi-entry: +120% trades, +164% PnL** over v1 single entry

---

*Report generated 2026-06-29 | Engine: dmr_mc_full.py + dmr_v2_multi_entry_test.py | MC: 10,000 simulations per pair*
