# DMR (Deep Mean Reversion) — FULL CEREBUS LOGIC — MT5 Backtest Results

**Date:** 2026-05-19 14:28
**Symbol:** EURUSD
**Timeframe:** M5
**Period:** 2022-01-01 to 2026-05-01

## Performance Summary

| Metric | Value |
|--------|-------|
| Total Trades | 1012 |
| Win Rate | 11.1% |
| Wins/Losses | 112/900 |
| Total Pips | 150.96 |
| Profit Factor | 1.15 |
| Max Drawdown | $-1270.72 (10.56%) |
| Expectancy | 0.149 pips |
| Final Equity | $11528.79 |
| Total Return | 15.3% |

## Exit Reason Distribution

| Reason | Count | PnL |
|--------|-------|-----|
| sl | 900 | $-10372.22 |
| hard_exit | 1 | $47.0 |
| tp | 111 | $11854.0 |

## Tier Breakdown

| Tier | Trades | WR | PnL | Pips |
|------|--------|----|----|------|
| T1 | 966% | 10.7% | $1086.35 | 107.7 |
| T2 | 46% | 19.6% | $442.43 | 43.3 |

## Cascade Breakdown

| Level | Trades | WR | PnL |
|-------|--------|----|-----|
| Cascade_0 | 457 | 17.5% | $4186.6 |
| Cascade_1 | 292 | 6.5% | $-1186.2 |
| Cascade_2 | 263 | 4.9% | $-1471.62 |

## Comparison with Python Optimizer

| Metric | Optimizer | MT5 Full | Delta |
|--------|-----------|----------|-------|
| Total Trades | 764 | 1012 | 248 |
| Win Rate | 91.8% | 11.1% | -80.7% |
| Total Pips | 8745.68 | 150.96 | -8594.7 |
| Profit Factor | 111.96 | 1.15 | -110.81 |
| Max DD | -5.02 pips | $-1270.72 | — |

## Key Differences from Simplified Version

The simplified version (dmr_mt5_backtest.py) used:
- Entry on P90 close (not Deep State touch)
- SL at 80% of P90 body (not Kill Switch at 220%)
- TP at Asian Range extensions (not activation level)
- No cascade/pyramid system
- No regime confirmation
- Result: 49.9% WR, -$210 PnL

This FULL version implements:
