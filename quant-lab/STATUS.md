# Quant Lab — Strategy Status

> Last updated: 2026-05-17 05:12 (Manager initialization)

## Validated Results (Nautilus, EUR/USD)

| Strategy | Trades | Win Rate | PnL | Profit Factor | Expectancy | Status |
|----------|--------|----------|-----|---------------|------------|--------|
| Daily_Asian_Float | 36 | 100% | +505.79 | 505.79 | +14.05 | ✅ WINNER (small sample) |
| Monday_Asian_Float | 148 | 56.8% | +541.50 | 1.36 | +3.66 | ✅ WINNER |
| Stall_Harvest_CFD | 463 | 100% | +4950.40 | 4950.40 | +10.69 | ⚠️ SUSPICIOUS — review for overfit |
| Resolution_Amplifier | 424 | 19.8% | +221.66 | 1.31 | +0.52 | 🟡 Marginal (low WR, positive) |
| Cascade_Combo_45min | 1764 | 26.3% | -485.56 | 0.93 | -0.28 | 🔴 Losing |
| Full_Day_Regime | 764 | 25.9% | -651.11 | 0.77 | -0.85 | 🔴 Losing |
| CFD_Expansion | 764 | 22.3% | -412.17 | 0.86 | -0.54 | 🔴 Losing |
| Constraint_Anchor | 607 | 58.2% | -1450.40 | 0.59 | -2.39 | 🔴 Losing (high WR, bad R:R) |
| P90_Cascade | 1291 | 27.5% | -2364.81 | 0.66 | -1.83 | 🔴 Losing |

## Autopilot Results (v3, May 15 — EUR/USD)

| Strategy | Return | Status |
|----------|--------|--------|
| RSI_Reversion | +0.33% | 🟡 Marginal (tiny) |
| EMA_Cross | +0.21% | 🟡 Marginal (tiny) |
| CEREBUS_WMA | +0.18% | 🟡 Marginal (tiny) |
| P90_Base | +0.11% | 🟡 Marginal (tiny) |
| Asian_Breakout | -0.45% | 🔴 Losing |
| Symmetry_Trap | -0.93% | 🔴 Losing |

Note: Autopilot profits are sub-1% — likely not significant after costs.

## P90 Unified Deep-Dive (May 15, EUR/USD)

| Strategy | Win Rate | PnL (pips) | PF | Notes |
|----------|----------|------------|-----|-------|
| P90_Base | 35.6% | -138.47 | 0.93 | Losing |
| P90_Cascade | 33.9% | -40.51 | 0.96 | Losing |
| P90_Cascade_Combo | 34.2% | -7.71 | 0.99 | Near break-even |

**Key Finding — Cascade_1 Edge:**
- cascade_1 activation: 51.5% WR, positive PnL (both Cascade variants)
- initial_p90 activation: 26.4% WR, losing PnL
- **The initial trade drags down the whole strategy. Cascade_1 alone shows genuine edge.**

## Manual Strategies to Reproduce

From CEREBUS manual (docs/strategies/), these have NOT been reproduced yet:

1. **Blind_Structural_Chain** — Part 14
2. **Triple_Engine** — Part 13 (Deep Dive Monte Carlo)
3. **Two_Plays** — Part 12
4. **Failure_Repair** — Part 11
5. **Dual_Engine** — Part 10
6. **Full_Day_Range_Regime** — Part 9 (in progress, losing)
7. **P90P_Distribution_Tracker** — Part 5
8. **Fractal_Resolution** — Part 15 (Resolution_Amplifier is a first attempt)

## Data Available

- `EURUSD.PRO_202407010000_202605132122.csv` — ~3GB, EUR/USD (2024-05-13)
- `US500_202407010100_202605132122.csv` — ~5GB, US500
- Various M1/M5 pairs from 2023-01-02 to 2026-05-06

## Code Base

- Strategies: `projects/trading/nautilus/strategies/`
- Pipeline: `projects/trading/nautilus/full_pipeline.py`
- Backtest engine: `projects/trading/nautilus/backtest_engine.py`
- Data loader: `projects/trading/nautilus/data_loader.py`
- Reports: `projects/trading/nautilus/reports/all_results.json`

## Active Manager Directives

See `quant-lab/decisions/manager-2026-05-17.md` for full details.

Priority order:
1. Investigate Stall_Harvest_CFD for overfitting
2. Optimize P90 cascade_1 (skip initial trade — 51.5% WR edge)
3. Fix Constraint_Anchor R:R ratio
4. Reproduce unreproduced manual strategies
