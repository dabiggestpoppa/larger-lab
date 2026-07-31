# 2026-06-02 Afternoon Notes (15:00-22:00 EDT)

## ML — DELETED (21:30 EDT)
- MAD ordered complete deletion of ML pipeline (quant-lab/ml/ directory)
- Reason: ML regime classifier is a meta-layer that adds complexity for marginal 2-3% edge
- MAD's call: "Regime classifier is not where profits come from"
- ML is DEAD. Do not bring it up again.

## MC COMPARATOR — BUILT (21:30 EDT)
- Created quant-lab/mt5/mc_comparator.py
- Compares live daily P&L against Monte Carlo backtest thresholds
- Per-asset thresholds extracted from MC results (per-asset/*_mc_results.json)
- Flags: loss count, WR, loss streak vs MC 95th percentile
- Aggregate threshold: max 8 losses/day, min 65% WR, max 5 loss streak
- First run: 40tr, W8 L31, WR 20% — ALL RED FLAGS (pre-fix signals)
- Purpose: detect deployment errors, not predict trades

## VS Team Build Summary
- Full 5-phase ML pipeline built then deleted per MAD directive
- 22 content commits + ~50 PM2 auto-sync commits
- All tier configs updated with correct session boundary (Asia = prev day 19:00-03:00 EST)
- VS team completed work ~18:00, went idle after
- 80/80 tests passing at time of deletion

## Live Trading (End of Day)
- Final: 40 closed trades, W8 L31, WR 20.5%, Net -$5.03
- Balance: $70.37 | Equity: $70.83
- All losing trades from OLD pre-fix signals
- Post-fix signals should match MC expectations tomorrow
- Open positions: GBPUSD BUY + GBPAUD BUY (both small, positive floating)

## Infrastructure
- OCE backend running (:8000), frontend (:3000)
- OpenClaw gateway (:18790)
- Telegram gateway (both PO and OC2)
- PM2 monitor daemon auto-committing workspace changes
- Workspace monitor cron set (every 5 min)
- MC comparator ready for tomorrow's session

## Key Bug Fixes Deployed Today
1. ST SL at impulse extreme → OCC extreme (was placing SL in profit territory)
2. P90 SL at 80% body → candle extreme + spread buffer (was 3-5p, too tight)
3. Bridge clamping (50pt buffer) → only clamp when SL/TP on wrong side
4. Asian session grouping → bars 00:00-03:00 belong to previous day's session
5. Executor validation tolerance → 1-point tolerance added
6. Duplicate executor kill → only bridge + guardian should run
7. RR tracking added to all MT5 reports
