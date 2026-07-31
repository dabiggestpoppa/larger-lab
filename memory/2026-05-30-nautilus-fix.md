# Nautilus Backtest Fix — 2026-05-30 22:55 EDT

## Root Cause
- `lot_size` passed as `Decimal("0.01")` (lot-based) instead of `Decimal("1000")` (unit-based) in Nautilus v1.226
- Symptom: Orders submitted (900-1800) but 0 positions filled (micro-unit sizing = effectively zero)
- Discovery: Sub-agents independently confirmed that `lot_size=1000` produced 173 positions, 82.4% WR on ST/EURUSD

## Fix Applied
- `run_cerebus_backtest.py`: Default `lot_size` changed from `Decimal("0.01")` to `Decimal("1000")`
- Added strategy-level stat extraction (`strategy.total_trades/wins/losses/pnl`) as ground truth
- Works for all pairs including USDCHF (which has Nautilus CHF/USD conversion issue for engine-level PnL)

## Smoke Test Result
- ST/EURUSD 5K bars: 48 trades, 77.1% WR, +175.3 pips (confirmed fix works)

## Full Backtest Status
- 4 sub-agents spawned at 22:55 EDT with fixed runner (30-min timeout each)
  1. naut_st_eurusd_v2 — Symmetry Trap / EURUSD
  2. naut_st_usdchf_v2 — Symmetry Trap / USDCHF
  3. naut_p90_eurusd_v2 — P90 / EURUSD
  4. naut_p90_usdchf_v2 — P90 / USDCHF

## Benchmarks (from CSV engines)
- P90 EURUSD: 1,038 trades, 78.7% WR, PF 3.09, +4,814p
- Symmetry Trap EURUSD: 574-892 trades, 85-91% WR, PF 8-23
- USDCHF both strategies: should be in similar_WR range (cross-validation)
