# Optimizer v5 Checkpoint — FINAL
## 2026-05-18 00:46 EDT

### Task A: Pairs Trading Rebuild — COMPLETED
- Script: `quant-lab/scripts/pairs_trading_v2.py`
- Results: `quant-lab/results/pairs_trading_v2_results.json`
- 5,687 trades | 61.3% WR | Net P&L: $461,746 | PF: 1.83 | Max DD: $6,661
- Profitable even with proper costs ($1.12M total costs)
- Position size capped at 5.0 lots

### Task B: Exit Bug Verification — COMPLETED
- Report: `quant-lab/findings/exit_bug_verification.md`
- Bug CONFIRMED: SL/TP arguments swapped in manage_trade() call in v2
- v2 results (100% WR, all 'sl') were entirely artifactual
- v4 fixed the bug: 30.7% WR, PF 1.48 (real but modest)

### Task C: USD/CHF Backtest — COMPLETED
- Script: `quant-lab/scripts/usdchf_backtest.py`
- Results: `quant-lab/results/usdchf_backtest_20260518.json`
- Deep_Mean_Reversion: 725 trades, 90.6% WR, PF 109.04 (ROBUST)
- Constraint_Anchor: 546 trades, 34.2% WR, PF 0.95 (UNPROFITABLE)
- P90P_Distribution: 151 trades, 25.8% WR, PF 1.34 (MARGINAL)
- Stall_Harvest_CFD: 73 trades, 26.0% WR, PF 1.18 (MARGINAL)

### Insights Written
- File: `quant-lab/insights/optimizer-2026-05-18.md`

### ALL TASKS COMPLETE
