# Majors Group Report - Progress

**Status:** COMPLETE  
**Time:** 2026-05-31 01:02 AM EDT

## Task: Generate Majors Group combined MC report

### Files Generated
- `quant-lab/reports/groups/majors_report.md` - Full markdown report
- `quant-lab/reports/groups/majors_mc_results.json` - MC simulation results JSON

### Combined Pool Summary
- **Total Pool Trades:** 3,784
  - EURUSD: 500 (equity curve sampling)
  - GBPUSD: 500 (equity curve sampling)
  - USDCHF: 500 (equity curve sampling)
  - USDJPY: 729 (explicit per-trade PnL)
  - AUDUSD: 828 (explicit per-trade PnL)
  - NZDUSD: 727 (explicit per-trade PnL)
- **Blended Win Rate:** 94.0% (3557W / 227L)
- **Combined Profit Factor:** 47.29
- **Combined Sharpe (approx):** 82.94

### Monte Carlo Results (10,000 iterations)
- **Terminal PnL:** $2,754.50 (deterministic — same pool sum)
- **All simulations profitable:** 100.0%
- **Median Max Drawdown:** $2.83 (0.028%)
- **Worst Observed DD:** $5.27 (0.053%)
- **Ruin Probability:** 0.0000%

### Key Findings
- All 6 assets individually show 0% ruin probability
- NZDUSD best standalone MC PnL ($4,213.60), EURUSD lowest ($572.29)
- T3 tier maintains 96.0% WR across group average
- No flags raised — all risk parameters within thresholds
- No engine code modified — report generation only

### Notes
- EURUSD/GBPUSD/USDCHF MC data lacks per-trade PnL arrays; extracted from equity curves sampled every 10 trades (divided by 10 for per-trade estimate)
- USDJPY/AUDUSD/NZDUSD have explicit per-trade PnL arrays from their MC runs
- MC simulation randomizes trade order; terminal PnL is pool-deterministic, drawdown is order-dependent
- Did NOT touch engine code, did NOT commit
