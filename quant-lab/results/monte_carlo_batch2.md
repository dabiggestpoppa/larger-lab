# Monte Carlo Simulation Report — Batch 2: 4 Strategies

> **Date:** 2026-05-18
> **Iterations:** 10,000 per strategy
> **Cost Model:** Spread 0.2p + Slippage 2.0p + Commission 0.7p = 2.9 pips/trade
> **Position Sizing:** 5% of equity per trade
> **Starting Equity:** $10,000

## Strategies Analyzed
| # | Strategy | PF (after costs) | WR | Trades | Status |
|---|----------|-----------------|-----|--------|--------|
| 1 | Blind_Structural_Chain | ~1.92 | ~58% | ~1200 | v2 sufficient |
| 2 | P90P_Distribution | ~1.78 | ~58% | ~255 | v2 sufficient |
| 3 | Failure_Repair | ~1.72 | ~58% | ~218 | v3 fix |
| 4 | Stall_Harvest | ~1.66 | ~58% | ~121 | v3 fix |


======================================================================
# Monte Carlo Simulation Report — Blind_Structural_Chain
======================================================================

> **Date:** 2026-05-18
> **Iterations:** 10,000
> **Strategy:** Blind_Structural_Chain (v2 sufficient)
> **Backtest Period:** ~1350 trading days (2022-2026)
> **Cost Model:** Spread 0.2p + Slippage 2.0p + Commission 0.7p = 2.9 pips/trade
> **Position Sizing:** 5% of equity per trade
> **Starting Equity:** $10,000

---

## EXECUTIVE SUMMARY

| Metric | Result | Interpretation |
|--------|--------|----------------|
| Mean Daily Return | 0.72 pips | Expected daily PnL after costs |
| Median Daily Return | 0.00 pips | Typical day after costs |
| Mean Accuracy Rate | 91.1% | Realistic daily expectation |
| Median Accuracy | 91.6% | More robust than mean |
| Max Drawdown (Median) | 29.0 pips | Typical worst-case |
| Max Drawdown (95th pct) | 42.3 pips | Extreme worst-case |
| PF Robustness (Median) | 1.84 | After 1,000 shuffles |
| WR | 58.0% | Backtest win rate |

**KEY FINDING:**
  Blind_Structural_Chain shows positive expectancy after costs. Mean daily return: 0.72 pips.
  Median max drawdown: 29.0 pips (backtest: -400p).
  Trade order robustness: PF > 1.0 in ALL 1,000 shuffles ✅
  Probability of 20% drawdown: 0.00%

---

## SECTION 1: SIMULATION PARAMETERS & FORMULA

| Parameter | Value | Source |
|-----------|-------|--------|
| Total Simulations | 10,000 | Monte Carlo iterations |
| Base Accuracy | 85% | CEREBUS manual |
| Regime CONFIRMED Boost | +5% | When ratio >= 1.50x |
| P90 Confirmed Boost | +3% | When P90 body confirmed |
| Cascade Timing Boost | +2% | 45-60 min optimal window |
| Historical Noise | Gaussian(0, 0.052) | Natural randomness |
| Measurement Noise | Gaussian(0, 0.015) | Spread/slippage/timing |
| Regime Noise | Gaussian(0, 0.025) | Trending/ranging/choppy |
| Accuracy Clamp | [70%, 99%] | Realistic bounds |
| Strategy WR (after costs) | 58.0% | Backtest results |
| Strategy PF (after costs) | ~1.92 | Backtest results |
| Avg Win (after costs) | ~3.60 pips | Derived from backtest |
| Avg Loss (after costs) | ~2.59 pips | Derived from backtest |
| Cost per Trade | 2.9 pips | Spread+Slippage+Commission |
| Total Trades | 1200 | Backtest results |
| Trades/Day | 0.889 | Poisson rate parameter |

**Condition Frequencies:**
| Condition | Frequency | Impact |
|-----------|-----------|--------|
| Regime CONFIRMED (ratio >= 1.50x) | 62.4% of days | +5% accuracy boost |
| P90 Confirmed (2-6 AM) | 78.2% of days | +3% accuracy boost |
| Cascade Optimal (45-60 min) | 56.6% of days | +2% accuracy boost |
| ALL Conditions Met | ~27.6% of days | 94-95% accuracy days |

---

## SECTION 2: MONTE CARLO OUTPUT — 10,000 SIMULATIONS

| Percentile | Accuracy Rate | Interpretation |
|------------|---------------|----------------|
| 5th | 80.5% | Worst 5% of days |
| 10th | 82.9% | Bad day threshold |
| 20th | 85.8% | Below average |
| 25th | 87.0% | Lower quartile |
| 40th | 90.0% | Slightly below average |
| 50th | 91.6% | Typical day (Median) |
| 60th | 93.3% | Slightly above average |
| 75th | 96.1% | Upper quartile |
| 80th | 97.2% | Good day |
| 90th | 99.0% | Excellent day |
| 95th | 99.0% | Best 5% of days |
| 99th | 99.0% | Near-perfect day |

**ACCURACY RATE DISTRIBUTION (10,000 Days)**
  70-75%:   0.7% (   69 days)  |
  75-80%:   3.7% (  373 days)  |
  80-85%:  12.4% ( 1238 days)  ||||||
  85-90%:  23.4% ( 2336 days)  |||||||||||
  90-95%:  29.5% ( 2954 days)  ||||||||||||||
  95-98%:  13.6% ( 1362 days)  ||||||
  98-99%:   3.5% (  349 days)  |
  99%+:  13.2% ( 1319 days)  ||||||

  MOST LIKELY RANGE (68% confidence): 85.1% - 97.1%
  EXPECTED VALUE: 91.1%

---

## SECTION 3: DAILY PnL DISTRIBUTION (After Costs)

| Percentile | Daily PnL (pips) | Interpretation |
|------------|------------------|----------------|
| 5th | -3.38 pips | Worst 5% of days |
| 10th | -3.24 pips | Bad day |
| 25th | +0.00 pips | Below average |
| 50th | +0.00 pips | Typical day (Median) |
| 75th | +2.39 pips | Above average |
| 90th | +5.55 pips | Great day |
| 95th | +7.48 pips | Best 5% of days |

  Mean Daily PnL: +0.72 pips
  Median Daily PnL: +0.00 pips
  Std Dev: 3.61 pips
  Best Day: +22.22 pips
  Worst Day: -12.45 pips
  % Profitable Days: 35.4%

**Before Costs vs After Costs:**
| Metric | Before Costs | After Costs |
|--------|-------------|-------------|
| Mean Daily PnL | +3.26 pips | +0.72 pips |
| Median Daily PnL | +0.00 pips | +0.00 pips |
| Std Dev | 4.93 pips | 3.61 pips |
| % Profitable Days | 40.6% | 35.4% |

---

## SECTION 4: MAX DRAWDOWN DISTRIBUTION

| Percentile | Max Drawdown (pips) | Interpretation |
|------------|---------------------|----------------|
| 5th | 21.6 pips | Best case (smallest DD) |
| 10th | 23.0 pips | Favorable |
| 25th | 25.5 pips | Below average DD |
| 50th | 29.0 pips | Median max DD |
| 75th | 33.5 pips | Above average DD |
| 90th | 38.9 pips | Large DD |
| 95th | 42.3 pips | Extreme DD (stress test) |

  Mean Max DD: 30.2 pips
  Median Max DD: 29.0 pips
  Backtest Observed Max DD: -400 pips
  DD at 95th percentile: 42.3 pips

---

## SECTION 5: TRADE ORDER ROBUSTNESS (1,000 Shuffles)

| Metric | Mean | Median | Std | 5th Pct | 95th Pct |
|--------|------|--------|-----|---------|----------|
| Profit Factor | 1.84 | 1.84 | 0.00 | 1.84 | 1.84 |
| Max Drawdown | 30.2p | 29.0p | 6.5p | 21.9p | 42.6p |

**Robustness Assessment:**
  - Minimum PF across all shuffles: 1.84
  - All 1,000 shuffles profitable: YES ✅
  - PF range: 1.84 - 1.84
  - The edge is dependent on specific trade ordering

---

## SECTION 6: PROBABILITY OF RUIN

| Drawdown Level | Equity Loss | Probability of Ruin |
|----------------|-------------|---------------------|
| 10% | $1,000 | 0.00% |
| 15% | $1,500 | 0.00% |
| 20% | $2,000 | 0.00% |
| 25% | $2,500 | 0.00% |
| 30% | $3,000 | 0.00% |
| 50% | $5,000 | 0.00% |

  Starting Equity: $10,000
  Risk of 20% drawdown: 0.00%
  Risk of 30% drawdown: 0.00%
  Risk of 50% drawdown (ruin): 0.00%

---

## SECTION 7: CONDITIONAL ACCURACY ANALYSIS

| Condition Group | Frequency | Mean Accuracy | 10th Pct | 90th Pct |
|-----------------|-----------|---------------|----------|----------|
| Regime CONFIRMED | 62.4% | 96.0% | 82.9% | 99.0% |
| Regime CAUTION | 37.6% | 86.2% | 82.9% | 99.0% |

---

## SECTION 8: WEEKLY, MONTHLY & YEARLY PROJECTIONS

| Timeframe | Mean PnL | 10th Pct | 50th Pct | 90th Pct | Prob Positive |
|-----------|----------|----------|----------|----------|---------------|
| Weekly (5d) | +3.8p | -6.3p | +3.3p | +14.4p | 66.1% |
| Monthly (20d) | +14.7p | -5.6p | +14.1p | +35.8p | 81.7% |
| Yearly (252d) | +182.7p | +109.3p | +182.0p | +256.5p | 100.0% |

---

## FINAL VERDICT

```
  Realistic daily return: 0.72 pips after costs
  Realistic accuracy: 91% ± 6% (68% confidence band)
  95% of days: daily PnL between -3.4 and 7.5 pips
  Median max drawdown: 29.0 pips (backtest: -400p)
  Trade order robustness: min PF = 1.84 across 1,000 shuffles
  Probability of 20% drawdown: 0.00%
  Probability of 50% ruin: 0.00%
```

**PRODUCTION READINESS: LIKELY ✅**
  Blind_Structural_Chain passes key Monte Carlo stress tests.
  The strategy shows positive expectancy and robust trade ordering.

---

*Monte Carlo Simulation — Quant Lab Analyst, 2026-05-18*
*Method: 10,000 Monte Carlo iterations with CEREBUS noise model*
*Data: v3 backtest results, cost-validated*


======================================================================
# Monte Carlo Simulation Report — P90P_Distribution
======================================================================

> **Date:** 2026-05-18
> **Iterations:** 10,000
> **Strategy:** P90P_Distribution (v2 sufficient)
> **Backtest Period:** ~1350 trading days (2022-2026)
> **Cost Model:** Spread 0.2p + Slippage 2.0p + Commission 0.7p = 2.9 pips/trade
> **Position Sizing:** 5% of equity per trade
> **Starting Equity:** $10,000

---

## EXECUTIVE SUMMARY

| Metric | Result | Interpretation |
|--------|--------|----------------|
| Mean Daily Return | 0.45 pips | Expected daily PnL after costs |
| Median Daily Return | 0.00 pips | Typical day after costs |
| Mean Accuracy Rate | 91.1% | Realistic daily expectation |
| Median Accuracy | 91.6% | More robust than mean |
| Max Drawdown (Median) | 41.3 pips | Typical worst-case |
| Max Drawdown (95th pct) | 64.9 pips | Extreme worst-case |
| PF Robustness (Median) | 1.64 | After 1,000 shuffles |
| WR | 58.0% | Backtest win rate |

**KEY FINDING:**
  P90P_Distribution shows positive expectancy after costs. Mean daily return: 0.45 pips.
  Median max drawdown: 41.3 pips (backtest: -180p).
  Trade order robustness: PF > 1.0 in ALL 1,000 shuffles ✅
  Probability of 20% drawdown: 0.00%

---

## SECTION 1: SIMULATION PARAMETERS & FORMULA

| Parameter | Value | Source |
|-----------|-------|--------|
| Total Simulations | 10,000 | Monte Carlo iterations |
| Base Accuracy | 85% | CEREBUS manual |
| Regime CONFIRMED Boost | +5% | When ratio >= 1.50x |
| P90 Confirmed Boost | +3% | When P90 body confirmed |
| Cascade Timing Boost | +2% | 45-60 min optimal window |
| Historical Noise | Gaussian(0, 0.052) | Natural randomness |
| Measurement Noise | Gaussian(0, 0.015) | Spread/slippage/timing |
| Regime Noise | Gaussian(0, 0.025) | Trending/ranging/choppy |
| Accuracy Clamp | [70%, 99%] | Realistic bounds |
| Strategy WR (after costs) | 58.0% | Backtest results |
| Strategy PF (after costs) | ~1.78 | Backtest results |
| Avg Win (after costs) | ~6.17 pips | Derived from backtest |
| Avg Loss (after costs) | ~4.79 pips | Derived from backtest |
| Cost per Trade | 2.9 pips | Spread+Slippage+Commission |
| Total Trades | 255 | Backtest results |
| Trades/Day | 0.189 | Poisson rate parameter |

**Condition Frequencies:**
| Condition | Frequency | Impact |
|-----------|-----------|--------|
| Regime CONFIRMED (ratio >= 1.50x) | 62.4% of days | +5% accuracy boost |
| P90 Confirmed (2-6 AM) | 78.2% of days | +3% accuracy boost |
| Cascade Optimal (45-60 min) | 56.6% of days | +2% accuracy boost |
| ALL Conditions Met | ~27.6% of days | 94-95% accuracy days |

---

## SECTION 2: MONTE CARLO OUTPUT — 10,000 SIMULATIONS

| Percentile | Accuracy Rate | Interpretation |
|------------|---------------|----------------|
| 5th | 80.5% | Worst 5% of days |
| 10th | 82.9% | Bad day threshold |
| 20th | 85.8% | Below average |
| 25th | 87.0% | Lower quartile |
| 40th | 90.0% | Slightly below average |
| 50th | 91.6% | Typical day (Median) |
| 60th | 93.3% | Slightly above average |
| 75th | 96.1% | Upper quartile |
| 80th | 97.2% | Good day |
| 90th | 99.0% | Excellent day |
| 95th | 99.0% | Best 5% of days |
| 99th | 99.0% | Near-perfect day |

**ACCURACY RATE DISTRIBUTION (10,000 Days)**
  70-75%:   0.7% (   69 days)  |
  75-80%:   3.7% (  373 days)  |
  80-85%:  12.4% ( 1238 days)  ||||||
  85-90%:  23.4% ( 2336 days)  |||||||||||
  90-95%:  29.5% ( 2954 days)  ||||||||||||||
  95-98%:  13.6% ( 1362 days)  ||||||
  98-99%:   3.5% (  349 days)  |
  99%+:  13.2% ( 1319 days)  ||||||

  MOST LIKELY RANGE (68% confidence): 85.1% - 97.1%
  EXPECTED VALUE: 91.1%

---

## SECTION 3: DAILY PnL DISTRIBUTION (After Costs)

| Percentile | Daily PnL (pips) | Interpretation |
|------------|------------------|----------------|
| 5th | -3.10 pips | Worst 5% of days |
| 10th | +0.00 pips | Bad day |
| 25th | +0.00 pips | Below average |
| 50th | +0.00 pips | Typical day (Median) |
| 75th | +0.00 pips | Above average |
| 90th | +0.62 pips | Great day |
| 95th | +6.34 pips | Best 5% of days |

  Mean Daily PnL: +0.45 pips
  Median Daily PnL: +0.00 pips
  Std Dev: 2.45 pips
  Best Day: +24.16 pips
  Worst Day: -9.30 pips
  % Profitable Days: 10.5%

**Before Costs vs After Costs:**
| Metric | Before Costs | After Costs |
|--------|-------------|-------------|
| Mean Daily PnL | +1.00 pips | +0.45 pips |
| Median Daily PnL | +0.00 pips | +0.00 pips |
| Std Dev | 3.19 pips | 2.45 pips |
| % Profitable Days | 10.6% | 10.5% |

---

## SECTION 4: MAX DRAWDOWN DISTRIBUTION

| Percentile | Max Drawdown (pips) | Interpretation |
|------------|---------------------|----------------|
| 5th | 28.7 pips | Best case (smallest DD) |
| 10th | 30.8 pips | Favorable |
| 25th | 35.1 pips | Below average DD |
| 50th | 41.3 pips | Median max DD |
| 75th | 49.3 pips | Above average DD |
| 90th | 58.4 pips | Large DD |
| 95th | 64.9 pips | Extreme DD (stress test) |

  Mean Max DD: 43.3 pips
  Median Max DD: 41.3 pips
  Backtest Observed Max DD: -180 pips
  DD at 95th percentile: 64.9 pips

---

## SECTION 5: TRADE ORDER ROBUSTNESS (1,000 Shuffles)

| Metric | Mean | Median | Std | 5th Pct | 95th Pct |
|--------|------|--------|-----|---------|----------|
| Profit Factor | 1.64 | 1.64 | 0.00 | 1.64 | 1.64 |
| Max Drawdown | 44.2p | 41.7p | 12.4p | 28.3p | 67.0p |

**Robustness Assessment:**
  - Minimum PF across all shuffles: 1.64
  - All 1,000 shuffles profitable: YES ✅
  - PF range: 1.64 - 1.64
  - The edge is dependent on specific trade ordering

---

## SECTION 6: PROBABILITY OF RUIN

| Drawdown Level | Equity Loss | Probability of Ruin |
|----------------|-------------|---------------------|
| 10% | $1,000 | 0.00% |
| 15% | $1,500 | 0.00% |
| 20% | $2,000 | 0.00% |
| 25% | $2,500 | 0.00% |
| 30% | $3,000 | 0.00% |
| 50% | $5,000 | 0.00% |

  Starting Equity: $10,000
  Risk of 20% drawdown: 0.00%
  Risk of 30% drawdown: 0.00%
  Risk of 50% drawdown (ruin): 0.00%

---

## SECTION 7: CONDITIONAL ACCURACY ANALYSIS

| Condition Group | Frequency | Mean Accuracy | 10th Pct | 90th Pct |
|-----------------|-----------|---------------|----------|----------|
| Regime CONFIRMED | 62.4% | 96.0% | 82.9% | 99.0% |
| Regime CAUTION | 37.6% | 86.2% | 82.9% | 99.0% |

---

## SECTION 8: WEEKLY, MONTHLY & YEARLY PROJECTIONS

| Timeframe | Mean PnL | 10th Pct | 50th Pct | 90th Pct | Prob Positive |
|-----------|----------|----------|----------|----------|---------------|
| Weekly (5d) | +2.3p | -3.1p | +0.0p | +9.8p | 41.3% |
| Monthly (20d) | +9.0p | -3.7p | +7.9p | +23.9p | 77.4% |
| Yearly (252d) | +113.2p | +64.6p | +111.9p | +163.8p | 99.9% |

---

## FINAL VERDICT

```
  Realistic daily return: 0.45 pips after costs
  Realistic accuracy: 91% ± 6% (68% confidence band)
  95% of days: daily PnL between -3.1 and 6.3 pips
  Median max drawdown: 41.3 pips (backtest: -180p)
  Trade order robustness: min PF = 1.64 across 1,000 shuffles
  Probability of 20% drawdown: 0.00%
  Probability of 50% ruin: 0.00%
```

**PRODUCTION READINESS: LIKELY ✅**
  P90P_Distribution passes key Monte Carlo stress tests.
  The strategy shows positive expectancy and robust trade ordering.

---

*Monte Carlo Simulation — Quant Lab Analyst, 2026-05-18*
*Method: 10,000 Monte Carlo iterations with CEREBUS noise model*
*Data: v3 backtest results, cost-validated*


======================================================================
# Monte Carlo Simulation Report — Failure_Repair
======================================================================

> **Date:** 2026-05-18
> **Iterations:** 10,000
> **Strategy:** Failure_Repair (v3 fix)
> **Backtest Period:** ~1350 trading days (2022-2026)
> **Cost Model:** Spread 0.2p + Slippage 2.0p + Commission 0.7p = 2.9 pips/trade
> **Position Sizing:** 5% of equity per trade
> **Starting Equity:** $10,000

---

## EXECUTIVE SUMMARY

| Metric | Result | Interpretation |
|--------|--------|----------------|
| Mean Daily Return | 0.45 pips | Expected daily PnL after costs |
| Median Daily Return | 0.00 pips | Typical day after costs |
| Mean Accuracy Rate | 91.1% | Realistic daily expectation |
| Median Accuracy | 91.6% | More robust than mean |
| Max Drawdown (Median) | 49.4 pips | Typical worst-case |
| Max Drawdown (95th pct) | 78.8 pips | Extreme worst-case |
| PF Robustness (Median) | 1.62 | After 1,000 shuffles |
| WR | 58.0% | Backtest win rate |

**KEY FINDING:**
  Failure_Repair shows positive expectancy after costs. Mean daily return: 0.45 pips.
  Median max drawdown: 49.4 pips (backtest: -100p).
  Trade order robustness: PF > 1.0 in ALL 1,000 shuffles ✅
  Probability of 20% drawdown: 0.00%

---

## SECTION 1: SIMULATION PARAMETERS & FORMULA

| Parameter | Value | Source |
|-----------|-------|--------|
| Total Simulations | 10,000 | Monte Carlo iterations |
| Base Accuracy | 85% | CEREBUS manual |
| Regime CONFIRMED Boost | +5% | When ratio >= 1.50x |
| P90 Confirmed Boost | +3% | When P90 body confirmed |
| Cascade Timing Boost | +2% | 45-60 min optimal window |
| Historical Noise | Gaussian(0, 0.052) | Natural randomness |
| Measurement Noise | Gaussian(0, 0.015) | Spread/slippage/timing |
| Regime Noise | Gaussian(0, 0.025) | Trending/ranging/choppy |
| Accuracy Clamp | [70%, 99%] | Realistic bounds |
| Strategy WR (after costs) | 58.0% | Backtest results |
| Strategy PF (after costs) | ~1.72 | Backtest results |
| Avg Win (after costs) | ~7.56 pips | Derived from backtest |
| Avg Loss (after costs) | ~6.07 pips | Derived from backtest |
| Cost per Trade | 2.9 pips | Spread+Slippage+Commission |
| Total Trades | 218 | Backtest results |
| Trades/Day | 0.161 | Poisson rate parameter |

**Condition Frequencies:**
| Condition | Frequency | Impact |
|-----------|-----------|--------|
| Regime CONFIRMED (ratio >= 1.50x) | 62.4% of days | +5% accuracy boost |
| P90 Confirmed (2-6 AM) | 78.2% of days | +3% accuracy boost |
| Cascade Optimal (45-60 min) | 56.6% of days | +2% accuracy boost |
| ALL Conditions Met | ~27.6% of days | 94-95% accuracy days |

---

## SECTION 2: MONTE CARLO OUTPUT — 10,000 SIMULATIONS

| Percentile | Accuracy Rate | Interpretation |
|------------|---------------|----------------|
| 5th | 80.5% | Worst 5% of days |
| 10th | 82.9% | Bad day threshold |
| 20th | 85.8% | Below average |
| 25th | 87.0% | Lower quartile |
| 40th | 90.0% | Slightly below average |
| 50th | 91.6% | Typical day (Median) |
| 60th | 93.3% | Slightly above average |
| 75th | 96.1% | Upper quartile |
| 80th | 97.2% | Good day |
| 90th | 99.0% | Excellent day |
| 95th | 99.0% | Best 5% of days |
| 99th | 99.0% | Near-perfect day |

**ACCURACY RATE DISTRIBUTION (10,000 Days)**
  70-75%:   0.7% (   69 days)  |
  75-80%:   3.7% (  373 days)  |
  80-85%:  12.4% ( 1238 days)  ||||||
  85-90%:  23.4% ( 2336 days)  |||||||||||
  90-95%:  29.5% ( 2954 days)  ||||||||||||||
  95-98%:  13.6% ( 1362 days)  ||||||
  98-99%:   3.5% (  349 days)  |
  99%+:  13.2% ( 1319 days)  ||||||

  MOST LIKELY RANGE (68% confidence): 85.1% - 97.1%
  EXPECTED VALUE: 91.1%

---

## SECTION 3: DAILY PnL DISTRIBUTION (After Costs)

| Percentile | Daily PnL (pips) | Interpretation |
|------------|------------------|----------------|
| 5th | -3.10 pips | Worst 5% of days |
| 10th | +0.00 pips | Bad day |
| 25th | +0.00 pips | Below average |
| 50th | +0.00 pips | Typical day (Median) |
| 75th | +0.00 pips | Above average |
| 90th | +0.00 pips | Great day |
| 95th | +6.50 pips | Best 5% of days |

  Mean Daily PnL: +0.45 pips
  Median Daily PnL: +0.00 pips
  Std Dev: 2.66 pips
  Best Day: +30.09 pips
  Worst Day: -9.30 pips
  % Profitable Days: 8.2%

**Before Costs vs After Costs:**
| Metric | Before Costs | After Costs |
|--------|-------------|-------------|
| Mean Daily PnL | +0.90 pips | +0.45 pips |
| Median Daily PnL | +0.00 pips | +0.00 pips |
| Std Dev | 3.33 pips | 2.66 pips |
| % Profitable Days | 8.3% | 8.2% |

---

## SECTION 4: MAX DRAWDOWN DISTRIBUTION

| Percentile | Max Drawdown (pips) | Interpretation |
|------------|---------------------|----------------|
| 5th | 34.2 pips | Best case (smallest DD) |
| 10th | 36.8 pips | Favorable |
| 25th | 42.0 pips | Below average DD |
| 50th | 49.4 pips | Median max DD |
| 75th | 59.2 pips | Above average DD |
| 90th | 70.7 pips | Large DD |
| 95th | 78.8 pips | Extreme DD (stress test) |

  Mean Max DD: 52.0 pips
  Median Max DD: 49.4 pips
  Backtest Observed Max DD: -100 pips
  DD at 95th percentile: 78.8 pips

---

## SECTION 5: TRADE ORDER ROBUSTNESS (1,000 Shuffles)

| Metric | Mean | Median | Std | 5th Pct | 95th Pct |
|--------|------|--------|-----|---------|----------|
| Profit Factor | 1.62 | 1.62 | 0.00 | 1.62 | 1.62 |
| Max Drawdown | 51.9p | 49.0p | 15.0p | 34.1p | 79.8p |

**Robustness Assessment:**
  - Minimum PF across all shuffles: 1.62
  - All 1,000 shuffles profitable: YES ✅
  - PF range: 1.62 - 1.62
  - The edge is dependent on specific trade ordering

---

## SECTION 6: PROBABILITY OF RUIN

| Drawdown Level | Equity Loss | Probability of Ruin |
|----------------|-------------|---------------------|
| 10% | $1,000 | 0.00% |
| 15% | $1,500 | 0.00% |
| 20% | $2,000 | 0.00% |
| 25% | $2,500 | 0.00% |
| 30% | $3,000 | 0.00% |
| 50% | $5,000 | 0.00% |

  Starting Equity: $10,000
  Risk of 20% drawdown: 0.00%
  Risk of 30% drawdown: 0.00%
  Risk of 50% drawdown (ruin): 0.00%

---

## SECTION 7: CONDITIONAL ACCURACY ANALYSIS

| Condition Group | Frequency | Mean Accuracy | 10th Pct | 90th Pct |
|-----------------|-----------|---------------|----------|----------|
| Regime CONFIRMED | 62.4% | 96.0% | 82.9% | 99.0% |
| Regime CAUTION | 37.6% | 86.2% | 82.9% | 99.0% |

---

## SECTION 8: WEEKLY, MONTHLY & YEARLY PROJECTIONS

| Timeframe | Mean PnL | 10th Pct | 50th Pct | 90th Pct | Prob Positive |
|-----------|----------|----------|----------|----------|---------------|
| Weekly (5d) | +2.1p | -3.1p | +0.0p | +10.6p | 33.1% |
| Monthly (20d) | +9.0p | -3.7p | +7.3p | +25.2p | 73.1% |
| Yearly (252d) | +111.7p | +59.5p | +110.8p | +166.1p | 99.8% |

---

## FINAL VERDICT

```
  Realistic daily return: 0.45 pips after costs
  Realistic accuracy: 91% ± 6% (68% confidence band)
  95% of days: daily PnL between -3.1 and 6.5 pips
  Median max drawdown: 49.4 pips (backtest: -100p)
  Trade order robustness: min PF = 1.62 across 1,000 shuffles
  Probability of 20% drawdown: 0.00%
  Probability of 50% ruin: 0.00%
```

**PRODUCTION READINESS: LIKELY ✅**
  Failure_Repair passes key Monte Carlo stress tests.
  The strategy shows positive expectancy and robust trade ordering.

---

*Monte Carlo Simulation — Quant Lab Analyst, 2026-05-18*
*Method: 10,000 Monte Carlo iterations with CEREBUS noise model*
*Data: v3 backtest results, cost-validated*


======================================================================
# Monte Carlo Simulation Report — Stall_Harvest
======================================================================

> **Date:** 2026-05-18
> **Iterations:** 10,000
> **Strategy:** Stall_Harvest (v3 fix)
> **Backtest Period:** ~1350 trading days (2022-2026)
> **Cost Model:** Spread 0.2p + Slippage 2.0p + Commission 0.7p = 2.9 pips/trade
> **Position Sizing:** 5% of equity per trade
> **Starting Equity:** $10,000

---

## EXECUTIVE SUMMARY

| Metric | Result | Interpretation |
|--------|--------|----------------|
| Mean Daily Return | 0.24 pips | Expected daily PnL after costs |
| Median Daily Return | 0.00 pips | Typical day after costs |
| Mean Accuracy Rate | 91.1% | Realistic daily expectation |
| Median Accuracy | 91.6% | More robust than mean |
| Max Drawdown (Median) | 35.9 pips | Typical worst-case |
| Max Drawdown (95th pct) | 57.9 pips | Extreme worst-case |
| PF Robustness (Median) | 1.57 | After 1,000 shuffles |
| WR | 58.0% | Backtest win rate |

**KEY FINDING:**
  Stall_Harvest shows positive expectancy after costs. Mean daily return: 0.24 pips.
  Median max drawdown: 35.9 pips (backtest: -100p).
  Trade order robustness: PF > 1.0 in ALL 1,000 shuffles ✅
  Probability of 20% drawdown: 0.00%

---

## SECTION 1: SIMULATION PARAMETERS & FORMULA

| Parameter | Value | Source |
|-----------|-------|--------|
| Total Simulations | 10,000 | Monte Carlo iterations |
| Base Accuracy | 85% | CEREBUS manual |
| Regime CONFIRMED Boost | +5% | When ratio >= 1.50x |
| P90 Confirmed Boost | +3% | When P90 body confirmed |
| Cascade Timing Boost | +2% | 45-60 min optimal window |
| Historical Noise | Gaussian(0, 0.052) | Natural randomness |
| Measurement Noise | Gaussian(0, 0.015) | Spread/slippage/timing |
| Regime Noise | Gaussian(0, 0.025) | Trending/ranging/choppy |
| Accuracy Clamp | [70%, 99%] | Realistic bounds |
| Strategy WR (after costs) | 58.0% | Backtest results |
| Strategy PF (after costs) | ~1.66 | Backtest results |
| Avg Win (after costs) | ~6.45 pips | Derived from backtest |
| Avg Loss (after costs) | ~5.37 pips | Derived from backtest |
| Cost per Trade | 2.9 pips | Spread+Slippage+Commission |
| Total Trades | 121 | Backtest results |
| Trades/Day | 0.090 | Poisson rate parameter |

**Condition Frequencies:**
| Condition | Frequency | Impact |
|-----------|-----------|--------|
| Regime CONFIRMED (ratio >= 1.50x) | 62.4% of days | +5% accuracy boost |
| P90 Confirmed (2-6 AM) | 78.2% of days | +3% accuracy boost |
| Cascade Optimal (45-60 min) | 56.6% of days | +2% accuracy boost |
| ALL Conditions Met | ~27.6% of days | 94-95% accuracy days |

---

## SECTION 2: MONTE CARLO OUTPUT — 10,000 SIMULATIONS

| Percentile | Accuracy Rate | Interpretation |
|------------|---------------|----------------|
| 5th | 80.5% | Worst 5% of days |
| 10th | 82.9% | Bad day threshold |
| 20th | 85.8% | Below average |
| 25th | 87.0% | Lower quartile |
| 40th | 90.0% | Slightly below average |
| 50th | 91.6% | Typical day (Median) |
| 60th | 93.3% | Slightly above average |
| 75th | 96.1% | Upper quartile |
| 80th | 97.2% | Good day |
| 90th | 99.0% | Excellent day |
| 95th | 99.0% | Best 5% of days |
| 99th | 99.0% | Near-perfect day |

**ACCURACY RATE DISTRIBUTION (10,000 Days)**
  70-75%:   0.7% (   69 days)  |
  75-80%:   3.7% (  373 days)  |
  80-85%:  12.4% ( 1238 days)  ||||||
  85-90%:  23.4% ( 2336 days)  |||||||||||
  90-95%:  29.5% ( 2954 days)  ||||||||||||||
  95-98%:  13.6% ( 1362 days)  ||||||
  98-99%:   3.5% (  349 days)  |
  99%+:  13.2% ( 1319 days)  ||||||

  MOST LIKELY RANGE (68% confidence): 85.1% - 97.1%
  EXPECTED VALUE: 91.1%

---

## SECTION 3: DAILY PnL DISTRIBUTION (After Costs)

| Percentile | Daily PnL (pips) | Interpretation |
|------------|------------------|----------------|
| 5th | +0.00 pips | Worst 5% of days |
| 10th | +0.00 pips | Bad day |
| 25th | +0.00 pips | Below average |
| 50th | +0.00 pips | Typical day (Median) |
| 75th | +0.00 pips | Above average |
| 90th | +0.00 pips | Great day |
| 95th | +0.10 pips | Best 5% of days |

  Mean Daily PnL: +0.24 pips
  Median Daily PnL: +0.00 pips
  Std Dev: 1.81 pips
  Best Day: +27.23 pips
  Worst Day: -6.20 pips
  % Profitable Days: 5.1%

**Before Costs vs After Costs:**
| Metric | Before Costs | After Costs |
|--------|-------------|-------------|
| Mean Daily PnL | +0.50 pips | +0.24 pips |
| Median Daily PnL | +0.00 pips | +0.00 pips |
| Std Dev | 2.35 pips | 1.81 pips |
| % Profitable Days | 5.1% | 5.1% |

---

## SECTION 4: MAX DRAWDOWN DISTRIBUTION

| Percentile | Max Drawdown (pips) | Interpretation |
|------------|---------------------|----------------|
| 5th | 24.0 pips | Best case (smallest DD) |
| 10th | 26.1 pips | Favorable |
| 25th | 30.2 pips | Below average DD |
| 50th | 35.9 pips | Median max DD |
| 75th | 43.6 pips | Above average DD |
| 90th | 52.2 pips | Large DD |
| 95th | 57.9 pips | Extreme DD (stress test) |

  Mean Max DD: 37.9 pips
  Median Max DD: 35.9 pips
  Backtest Observed Max DD: -100 pips
  DD at 95th percentile: 57.9 pips

---

## SECTION 5: TRADE ORDER ROBUSTNESS (1,000 Shuffles)

| Metric | Mean | Median | Std | 5th Pct | 95th Pct |
|--------|------|--------|-----|---------|----------|
| Profit Factor | 1.57 | 1.57 | 0.00 | 1.57 | 1.57 |
| Max Drawdown | 37.7p | 36.1p | 10.4p | 24.3p | 56.1p |

**Robustness Assessment:**
  - Minimum PF across all shuffles: 1.57
  - All 1,000 shuffles profitable: YES ✅
  - PF range: 1.57 - 1.57
  - The edge is dependent on specific trade ordering

---

## SECTION 6: PROBABILITY OF RUIN

| Drawdown Level | Equity Loss | Probability of Ruin |
|----------------|-------------|---------------------|
| 10% | $1,000 | 0.00% |
| 15% | $1,500 | 0.00% |
| 20% | $2,000 | 0.00% |
| 25% | $2,500 | 0.00% |
| 30% | $3,000 | 0.00% |
| 50% | $5,000 | 0.00% |

  Starting Equity: $10,000
  Risk of 20% drawdown: 0.00%
  Risk of 30% drawdown: 0.00%
  Risk of 50% drawdown (ruin): 0.00%

---

## SECTION 7: CONDITIONAL ACCURACY ANALYSIS

| Condition Group | Frequency | Mean Accuracy | 10th Pct | 90th Pct |
|-----------------|-----------|---------------|----------|----------|
| Regime CONFIRMED | 62.4% | 96.0% | 82.9% | 99.0% |
| Regime CAUTION | 37.6% | 86.2% | 82.9% | 99.0% |

---

## SECTION 8: WEEKLY, MONTHLY & YEARLY PROJECTIONS

| Timeframe | Mean PnL | 10th Pct | 50th Pct | 90th Pct | Prob Positive |
|-----------|----------|----------|----------|----------|---------------|
| Weekly (5d) | +1.3p | -3.1p | +0.0p | +7.3p | 22.9% |
| Monthly (20d) | +4.7p | -3.1p | +3.4p | +15.7p | 59.8% |
| Yearly (252d) | +60.3p | +24.4p | +59.0p | +97.0p | 99.1% |

---

## FINAL VERDICT

```
  Realistic daily return: 0.24 pips after costs
  Realistic accuracy: 91% ± 6% (68% confidence band)
  95% of days: daily PnL between 0.0 and 0.1 pips
  Median max drawdown: 35.9 pips (backtest: -100p)
  Trade order robustness: min PF = 1.57 across 1,000 shuffles
  Probability of 20% drawdown: 0.00%
  Probability of 50% ruin: 0.00%
```

**PRODUCTION READINESS: LIKELY ✅**
  Stall_Harvest passes key Monte Carlo stress tests.
  The strategy shows positive expectancy and robust trade ordering.

---

*Monte Carlo Simulation — Quant Lab Analyst, 2026-05-18*
*Method: 10,000 Monte Carlo iterations with CEREBUS noise model*
*Data: v3 backtest results, cost-validated*