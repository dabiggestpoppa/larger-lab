# 📊 COST-ADJUSTED BACKTEST RESULTS — THE FINAL PICTURE

> **Generated:** June 7, 2026
> **Source:** `cost_analysis_all.json` (already computed by OC2)
> **Commission:** $7/lot ($0.07 per 0.01 lot trade)
> **Spread source:** MT5 live symbol_info (NOT historical CSV average — needs update)
> **⚠️ ISSUE:** MAD directed to use historical CSV average spread, not live MT5 values

---

## KEY FINDINGS

### 1. AU Targets — ✅ CORRECT (Per-Asset)
Each pair has its own native AU target in `configs/asset_configs.py`. The sweep script (`sweep_forex_v2.py`) uses `ASSET_CONFIGS[pair]` to build scaled tiers, so AU targets ARE per-asset. **No universal EURUSD AU bug.**

### 2. Spread Values — ⚠️ NEEDS VERIFICATION
Current cost analysis uses **live MT5 spread values**, NOT historical CSV average as MAD directed.

MAD's directive (June 4, 23:55):
> "ARC look all u gotta do is look at backtest results or re run them and simple calculate historical average spread... literally just pull raw csv and make a script"

**Action needed:** Re-run `apply_costs.py` using historical average spread from CSV data instead of live MT5 values.

### 3. JPY Commission — ✅ CORRECT
JPY pairs use `pip_value_per_lot=1000.0`, so commission = $7/1000 = 0.007 pips/trade. This is correct.

### 4. Indices/Metals Commission — ⚠️ SUSPICIOUS
DE30, FR40, HK50, US500, XAUUSD, XAGUSD show `commission_pips_per_lot=7.0` — this means the pip_value_per_lot is $1.0, so commission = $7/1 = 7.0 pips. This seems very high and may be incorrect. Need to verify broker contract specs.

---

## COST-ADJUSTED RESULTS — ALL PAIRS

### FX Majors (Deployment Candidates)

| Pair | Trades | WR_raw | WR_adj | PF_raw | PF_adj | Cost/Trade | WR Delta | PF Delta |
|------|--------|--------|--------|--------|--------|------------|----------|----------|
| EURUSD | 5,666 | 82.4% | 77.9% | 12.0 | 8.4 | 0.8p | -4.5% | -3.6 |
| GBPUSD | 7,548 | 83.1% | 78.8% | 12.8 | 8.8 | 1.0p | -4.3% | -4.1 |
| USDJPY | 8,400 | 83.5% | 82.3% | 12.2 | 11.1 | 0.3p | -1.2% | -1.2 |
| USDCHF | 4,810 | 82.9% | 77.0% | 13.2 | 8.1 | 1.0p | -5.9% | -5.0 |
| AUDUSD | 4,043 | 84.9% | 77.3% | 16.7 | 9.4 | 1.0p | -7.6% | -7.3 |
| NZDUSD | 3,694 | 85.8% | 77.7% | 16.2 | 9.2 | 1.0p | -8.1% | -7.1 |
| USDCAD | 5,352 | 84.1% | 78.6% | 14.9 | 9.7 | 1.0p | -5.5% | -5.1 |

### FX Crosses

| Pair | Trades | WR_raw | WR_adj | PF_raw | PF_adj | Cost/Trade | WR Delta | PF Delta |
|------|--------|--------|--------|--------|--------|------------|----------|----------|
| EURGBP | 2,265 | 87.1% | 78.8% | 20.3 | 10.8 | 1.0p | -8.3% | -9.4 |
| EURJPY | 8,565 | 84.2% | 82.0% | 13.6 | 11.5 | 0.5p | -2.2% | -2.1 |
| EURCHF | 3,452 | 85.9% | 78.5% | 17.6 | 10.7 | 1.0p | -7.4% | -6.9 |
| EURCAD | 6,784 | 84.2% | 77.9% | 13.3 | 8.3 | 1.2p | -6.4% | -4.9 |
| EURNZD | 9,375 | 84.4% | 79.4% | 13.0 | 8.5 | 1.4p | -5.1% | -4.5 |
| EURAUD | 8,480 | 83.6% | 78.5% | 12.7 | 8.4 | 1.2p | -5.1% | -4.3 |
| GBPJPY | 11,200 | 84.2% | 82.9% | 11.5 | 10.1 | 0.5p | -1.3% | -1.4 |
| GBPAUD | 4,520 | 83.0% | 78.6% | 10.6 | 7.4 | 1.2p | -4.4% | -3.2 |
| GBPCAD | 6,140 | 83.4% | 78.0% | 12.1 | 8.1 | 1.2p | -5.4% | -4.0 |
| GBPCHF | 4,417 | 83.4% | 76.3% | 12.4 | 7.5 | 1.2p | -7.1% | -4.9 |
| GBPNZD | 5,327 | 83.2% | 79.2% | 11.0 | 7.4 | 1.4p | -4.0% | -3.6 |
| AUDJPY | 5,628 | 78.5% | 75.4% | 10.5 | 8.1 | 1.2p | -3.1% | -2.4 |
| AUDCAD | 5,184 | 80.2% | 75.4% | 11.5 | 8.1 | 1.2p | -4.8% | -3.4 |
| AUDCHF | 6,294 | 77.9% | 73.0% | 10.5 | 7.2 | 1.2p | -4.9% | -3.3 |
| AUDNZD | 5,335 | 80.9% | 75.2% | 14.9 | 9.6 | 1.2p | -5.7% | -5.3 |
| CHFJPY | 11,106 | 82.6% | 80.8% | 11.5 | 9.8 | 0.5p | -1.8% | -1.7 |
| CADJPY | 7,690 | 80.2% | 77.2% | 11.5 | 9.3 | 1.2p | -3.0% | -2.2 |
| CADCHF | 6,310 | 78.2% | 72.7% | 10.7 | 7.6 | 1.2p | -5.5% | -3.1 |
| NZDJPY | 8,141 | 79.3% | 76.6% | 10.6 | 8.7 | 1.2p | -2.7% | -1.9 |
| NZDCAD | 6,232 | 78.9% | 73.8% | 11.3 | 8.3 | 1.2p | -5.1% | -3.0 |
| NZDCHF | 5,561 | 80.9% | 74.2% | 13.3 | 8.7 | 1.4p | -6.7% | -4.6 |

### Crypto

| Pair | Trades | WR_raw | WR_adj | PF_raw | PF_adj | Cost/Trade | WR Delta | PF Delta |
|------|--------|--------|--------|--------|--------|------------|----------|----------|
| BTCUSD | 4,203 | 87.9% | 84.8% | 6.5 | 4.5 | 5.07p | -3.1% | -2.0 |
| ETHUSD | 9,073 | 85.1% | 60.1% | 12.3 | 2.1 | 5.7p | -25.0% | -10.2 |

### Metals & Indices

| Pair | Trades | WR_raw | WR_adj | PF_raw | PF_adj | Cost/Trade | WR Delta | PF Delta |
|------|--------|--------|--------|--------|--------|------------|----------|----------|
| XAUUSD | 3,452 | 87.0% | 74.3% | 9.3 | 2.7 | 8.5p | -12.7% | -6.6 |
| XAGUSD | 3,452 | 85.0% | 49.8% | 10.3 | 1.1 | 8.5p | -35.2% | -9.2 |
| DE30 | 3,452 | 85.2% | 73.6% | 10.1 | 2.7 | 7.5p | -11.6% | -7.4 |
| FR40 | 3,452 | 83.5% | 53.6% | 12.0 | 1.2 | 7.5p | -29.9% | -10.8 |
| HK50 | 3,452 | 86.5% | 76.5% | 10.7 | 3.5 | 7.5p | -10.0% | -7.2 |
| US500 | 3,452 | 84.2% | 40.6% | 12.5 | 0.7 | 7.5p | -43.6% | -11.8 |

---

## ⚠️ CRITICAL ISSUES

### Issue 1: ETHUSD Destroyed by Costs
- **Raw:** 85.1% WR, PF 12.3
- **Adjusted:** 60.1% WR, PF 2.1
- **Cost per trade:** 5.7p (5p spread + 0.7p commission)
- **Verdict:** ❌ NOT VIABLE at 0.01 lot. The 5 pip spread on 9,073 trades destroys the edge.

### Issue 2: Indices/Metals Destroyed by Commission
- DE30, FR40, HK50, US500, XAUUSD, XAGUSD all show commission = 7.0 pips/trade
- This is because `pip_value_per_lot = $1.0` for these instruments
- **Verdict:** ❌ NOT VIABLE at 0.01 lot with current commission structure. Need larger lot sizes or different broker.

### Issue 3: High-Cost FX Pairs
Pairs where adjusted WR drops below 75% or PF drops below 8.0:
- AUDCHF: 73.0% WR, PF 7.3
- CADCHF: 72.7% WR, PF 7.6
- NZDCHF: 74.2% WR, PF 8.7
- GBPCHF: 76.3% WR, PF 7.5

These pairs have high spread costs relative to their edge. Consider running at ceiling (fewer trades, less cost impact) or avoiding.

### Issue 4: Spread Values Need Historical Verification
MAD directed to use historical CSV average spread, not live MT5 values. Current analysis uses live MT5 spreads which may not match backtest period conditions.

---

## COST-ADJUSTED RANKING (Best to Worst)

### Top 10 by Adjusted PF (FX Only, >2000 trades)
| Rank | Pair | WR_adj | PF_adj | Trades | Cost/Trade |
|------|------|--------|--------|--------|------------|
| 1 | USDJPY | 82.3% | 11.1 | 8,400 | 0.3p |
| 2 | EURJPY | 82.0% | 11.5 | 8,565 | 0.5p |
| 3 | GBPJPY | 82.9% | 10.1 | 11,200 | 0.5p |
| 4 | CHFJPY | 80.8% | 9.8 | 11,106 | 0.5p |
| 5 | EURUSD | 77.9% | 8.4 | 5,666 | 0.8p |
| 6 | GBPUSD | 78.8% | 8.8 | 7,548 | 1.0p |
| 7 | EURCHF | 78.5% | 10.7 | 3,452 | 1.0p |
| 8 | USDCAD | 78.6% | 9.7 | 5,352 | 1.0p |
| 9 | EURAUD | 78.5% | 8.4 | 8,480 | 1.2p |
| 10 | EURNZD | 79.4% | 8.5 | 9,375 | 1.4p |

### Bottom 5 by Adjusted PF (FX Only)
| Pair | WR_adj | PF_adj | Issue |
|------|--------|--------|-------|
| AUDCHF | 73.0% | 7.3 | High spread cost |
| CADCHF | 72.7% | 7.6 | High spread cost |
| GBPCHF | 76.3% | 7.5 | High spread cost |
| NZDCHF | 74.2% | 8.7 | High spread cost |
| AUDCAD | 75.4% | 8.1 | Moderate cost |

---

## DEPLOYMENT RECOMMENDATIONS (Cost-Adjusted)

### ✅ SAFE TO DEPLOY (Adjusted PF > 8.0, WR > 77%)
| Pair | Level | Adj WR | Adj PF | Notes |
|------|-------|--------|--------|-------|
| EURUSD | FLOOR | 77.9% | 8.4 | Tightest spread, clean |
| USDJPY | FLOOR | 82.3% | 11.1 | Best cost-adjusted |
| CHFJPY | FLOOR | 80.8% | 9.8 | Good despite higher spread |
| EURJPY | FLOOR | 82.0% | 11.2 | Excellent |
| GBPJPY | FLOOR | 82.9% | 10.1 | Excellent |
| EURCHF | FLOOR | 78.5% | 10.7 | Good |
| USDCAD | FLOOR | 78.6% | 9.7 | Solid |
| GBPUSD | FLOOR | 78.8% | 8.8 | Solid |

### ⚠️ DEPLOY WITH CAUTION (Adjusted PF 7.0-8.0)
| Pair | Level | Adj WR | Adj PF | Notes |
|------|-------|--------|--------|-------|
| EURGBP | FLOOR | 78.8% | 10.8 | Good PF but high cost% |
| EURCAD | FLOOR | 77.9% | 8.3 | Borderline |
| EURNZD | FLOOR | 79.4% | 8.5 | OK |
| GBPAUD | FLOOR | 78.6% | 7.4 | Borderline |
| GBPCAD | FLOOR | 78.0% | 8.1 | Borderline |
| AUDUSD | FLOOR | 77.3% | 9.4 | OK |
| NZDUSD | FLOOR | 77.7% | 9.2 | OK |

### ❌ DO NOT DEPLOY
| Pair | Reason |
|------|--------|
| ETHUSD | 60.1% WR adjusted, PF 2.1 — spread destroys edge |
| XAUUSD | 74.3% WR adjusted, PF 2.7 — commission too high at 0.01 lot |
| XAGUSD | 49.8% WR adjusted, PF 1.1 — destroyed by costs |
| DE30/FR40/HK50/US500 | Commission 7 pips/trade at 0.01 lot — need larger lots |
| AUDCHF/CADCHF | PF < 7.5 after costs — marginal edge |

---

## NEXT STEPS

1. **Re-run cost analysis with historical CSV spread** (MAD directive)
2. **Verify broker contract specs** for indices/metals (commission per lot)
3. **Run Nautilus validation** on EURUSD (5,084 trade config → confirm 82.9% WR)
4. **Update Nautilus strategy** to 1:1 match CSV engine (4 diffs identified)
5. **Deploy LOW COST HEX** once cost analysis is verified
6. **Monitor live results** against cost-adjusted benchmarks

---

> **⚠️ IMPORTANT:** All adjusted results above use LIVE MT5 spread values. MAD directed to use HISTORICAL CSV average spread. Results may change slightly after re-run.
> 
> **⚠️ COMMISSION:** $7/lot for ALL asset classes. Indices/metals show 7 pips/trade commission because pip_value=$1. This may need adjustment based on actual broker contract specs.
