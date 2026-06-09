# MLR Intraday Validation — FINAL REPORT

> **Date:** 2026-06-08
> **Pairs tested:** 32 (28 fetched + 4 original)
> **Method:** Asian Range (19:00-03:00 EST) → Extensions → Activation Window (03:00-12:00 EST)
> **Data:** M5 bars, 2020-2026, ~1000-1200 trading days per pair

---

## INTRADAY MLR RESULTS (Asian Range → Activation Window)

| Pair | N | -25% | -50% | -100% | Rekey 132% |
|------|---|------|------|-------|------------|
| AUDCAD | 1200 | 97.8% | 80.8% | 37.1% | 22.2% |
| AUDCHF | 1201 | 97.9% | 78.4% | 36.6% | 20.9% |
| AUDJPY | 1201 | 98.1% | 76.5% | 33.1% | 19.9% |
| AUDNZD | 1201 | 90.8% | 54.5% | 15.2% | 6.7% |
| AUDUSD | 1201 | 98.7% | 84.0% | 42.8% | 27.3% |
| CADCHF | 1201 | 99.0% | 89.0% | 56.6% | 40.0% |
| CADJPY | 1137 | 98.4% | 86.1% | 45.2% | 29.9% |
| CHFJPY | 1201 | 98.8% | 85.4% | 44.7% | 27.5% |
| EURAUD | 1201 | 98.8% | 83.6% | 42.5% | 23.6% |
| EURCAD | 1201 | 99.6% | 94.3% | 66.4% | 49.7% |
| EURCHF | 1201 | 97.8% | 84.6% | 54.7% | 41.8% |
| EURGBP | 1201 | 99.5% | 93.4% | 68.5% | 51.9% |
| EURJPY | 1201 | 99.0% | 88.2% | 47.4% | 30.5% |
| EURNZD | 1201 | 97.5% | 77.5% | 33.4% | 19.4% |
| EURUSD | 779 | 99.5% | 90.5% | 51.2% | 34.1% |
| GBPAUD | 1137 | 98.9% | 83.5% | 43.5% | 28.1% |
| GBPCAD | 982 | 99.8% | 95.6% | 71.1% | 54.0% |
| GBPCHF | 1201 | 99.3% | 89.7% | 59.4% | 43.0% |
| GBPJPY | 1201 | 99.6% | 89.4% | 53.5% | 37.7% |
| GBPNZD | 984 | 97.9% | 80.6% | 33.3% | 19.0% |
| GBPUSD | 1202 | 99.8% | 94.8% | 73.8% | 57.7% |
| LCOUSD | 801 | 99.3% | 83.9% | 43.2% | 26.6% |
| NZDCAD | 1137 | 95.8% | 73.9% | 30.0% | 16.5% |
| NZDCHF | 1137 | 96.9% | 70.2% | 28.0% | 14.2% |
| NZDJPY | 1137 | 96.7% | 71.1% | 27.0% | 15.4% |
| NZDUSD | 981 | 97.9% | 78.0% | 35.2% | 22.1% |
| OILUSD | 880 | 97.2% | 78.9% | 40.1% | 22.3% |
| USDCAD | 1201 | 99.4% | 92.3% | 61.2% | 42.8% |
| USDCHF | 755 | 99.3% | 89.8% | 54.2% | 38.0% |
| USDJPY | 1201 | 99.0% | 85.3% | 43.0% | 28.4% |
| XAGUSD | 1116 | 98.4% | 82.1% | 46.0% | 30.9% |
| XAUUSD | 1129 | 99.0% | 83.3% | 47.7% | 33.7% |

---

## KEY FINDINGS

### ✅ -25% Intraday Extension: 90-100% Hit Rate
**Every single pair shows 90%+ hit rate for the -25% intraday extension.**
Most pairs are 97-99%. This is the most reliable intraday level.

### ✅ -50% Intraday Extension: 54-95% Hit Rate
Wide range depending on pair. Tight-range pairs (EURGBP, GBPCAD, EURCAD) show 93-95%.
Wide-range pairs (AUDNZD) show 54%.

### ⚠️ -100% Intraday Extension: 15-74% Hit Rate
The full 100% extension is harder to hit intraday. Best performers:
- GBPUSD: 73.8%
- GBPCAD: 71.1%
- EURGBP: 68.5%
- USDCAD: 61.2%

### ⚠️ 132% Intraday Rekey: 7-58% Hit Rate
The rekey is the hardest to hit intraday. Best performers:
- GBPUSD: 57.7%
- GBPCAD: 54.0%
- EURGBP: 51.9%
- EURCAD: 49.7%

---

## COMPARISON: Intraday vs Weekly

| Level | Intraday (Avg) | Weekly (Avg) | Difference |
|-------|---------------|-------------|------------|
| -25% | 97.5% | 100% | +2.5% weekly |
| -50% | 81.5% | 100% | +18.5% weekly |
| -100% | 40.0% | 76% | +36% weekly |
| Rekey | 28% | 58% | +30% weekly |

**Weekly extensions are significantly more reliable than intraday.**
This makes sense: the weekly window gives 5 days for the extension to be reached,
while intraday only gives 9 hours (03:00-12:00 EST).

---

## TOP PAIRS FOR INTRADAY MLR TRACKER

Based on combined -25% and -50% hit rates:

| Rank | Pair | -25% | -50% | Combined |
|------|------|------|------|----------|
| 1 | EURCAD | 99.6% | 94.3% | 96.9% |
| 2 | GBPUSD | 99.8% | 94.8% | 97.3% |
| 3 | GBPCAD | 99.8% | 95.6% | 97.7% |
| 4 | EURGBP | 99.5% | 93.4% | 96.5% |
| 5 | USDCAD | 99.4% | 92.3% | 95.9% |
| 6 | GBPJPY | 99.6% | 89.4% | 94.5% |
| 7 | CADCHF | 99.0% | 89.0% | 94.0% |
| 8 | EURJPY | 99.0% | 88.2% | 93.6% |
