# Quant Lab — Strategy Status

> Last updated: 2026-05-17 06:05 (Optimizer v2 results integrated)

## Validated Results (Nautilus, EUR/USD M5, Jan 2023 – May 2026)

### New Results (optimizer_v2.py — 249,484 bars)

| Strategy | Trades | Win Rate | PnL | Profit Factor | MaxDD | Expectancy | Status |
|----------|--------|----------|-----|---------------|-------|------------|--------|
| Deep_Mean_Reversion | 764 | 91.8% | +8745.7 | 111.96 | -5.0 | +11.4 | ✅ WINNER |
| Failure_Repair | 370 | 38.4% | +214.1 | 1.17 | -144.3 | +0.58 | 🟡 Marginal |
| P90P_Distribution | 255 | 14.9% | +141.4 | 1.12 | -224.7 | +0.56 | 🟡 Marginal |
| Fractal_Resolution | 808 | 43.8% | +197.0 | 1.03 | -679.4 | +0.24 | 🟡 Marginal |
| Blind_Structural_Chain | 1622 | 29.7% | -168.2 | 0.97 | -341.3 | -0.10 | 🔴 Losing |
| Two_Plays | 557 | 35.0% | -229.3 | 0.89 | -282.6 | -0.41 | 🔴 Losing |
| Constraint_Anchor | 607 | 32.9% | -265.4 | 0.87 | -270.3 | -0.44 | 🔴 Losing |
| Dual_Engine | 627 | 65.9% | -689.3 | 0.85 | -880.0 | -1.10 | 🔴 Losing |

### Previous Results (cerabus_v2, EUR/USD)

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

### New Results (optimizer_v2.py — Stall_Harvest fixed version)

| Strategy | Trades | Win Rate | PnL | Profit Factor | MaxDD | Expectancy | Status |
|----------|--------|----------|-----|---------------|-------|------------|--------|
| Stall_Harvest_CFD (fixed) | 88 | 100.0% | +867.5 | 867.46 | 0.0 | +9.9 | ⚠️ BUG — all exits are SL but positive PnL |

## Goal Progress

| Goal | Status | Progress |
|------|--------|----------|
| Goal 1: All strategies backtested | 🔄 In Progress | 14/14 coded, 9 new backtested, 5 old results carried over |
| Goal 2: 80% strategies profitable | 🔴 Behind | 5/14 profitable = 36%. Need 80%. Fixes identified. |
| Goal 3: Max DD < 12% | 🔴 Behind | Most strategies have excessive DD. Position sizing needed. |
| Goal 4: 80% WR strategy, 2/day | ✅ FOUND | Deep_Mean_Reversion: 91.8% WR. Need to increase frequency to 2/day. |
| Goal 5: USD/CHF backtest | ⏳ Pending | Not started |
| Goal 6: Basket portfolio | ⏳ Pending | Not started |

## Key Findings

1. **Deep_Mean_Reversion is the flagship** — 91.8% WR, +8745p PnL, -5p MaxDD across 764 trades
2. **Stall_Harvest has SL/TP inversion bug** — all exits show as SL but with positive PnL
3. **Dual_Engine and Constraint_Anchor have SL too wide** — opposite Asian extreme gives terrible R:R
4. **Blind_Structural_Chain and Two_Plays have entry condition bugs** — WR far below manual predictions
5. **P90P_Distribution targets too ambitious** — 2.18-3.12x AR rarely hit

## Bugs Identified

| Bug | Strategy | Root Cause | Fix |
|-----|----------|-----------|-----|
| SL/TP inversion | Stall_Harvest_CFD | SL placed on profit side | Swap SL/TP directions |
| SL too wide | Constraint_Anchor, Dual_Engine | Using opposite Asian extreme | Use 80% body boundary |
| Entry too loose | Blind_Structural_Chain | Impulse threshold too low | Increase threshold +2-3p |
| Targets too far | P90P_Distribution | 2.18-3.12x AR rarely hit | Reduce to 1.5-2.0x or use as module |
| Entry condition | Two_Plays | Close-outside-band check may be wrong | Debug entry filter |

## Data Available

- `EURUSD!_M5_202301020000_202605061250.csv` — 15MB, EUR/USD M5 (2023-05-06), 249,484 bars
- `EURUSD.PRO_202407010000_202605132122.csv` — 3GB, EUR/USD tick/1M (2024-05-13)
- `USDCHF!_M5_202301020000_202605061250.csv` — 15MB, USD/CHF M5
- `CHFJPY!_M1_202301020000_202605061250.csv` — 75MB, CHF/JPY M1

## Code Base

- Strategies: `projects/trading/nautilus/strategies/`
- Optimizer v2: `projects/trading/nautilus/strategies/optimizer_v2.py`
- Results: `quant-lab/results/optimizer_v2_20260517_060543.json`
- Insights: `quant-lab/insights/optimizer-2026-05-17.md`
- Findings: `quant-lab/findings/researcher-2026-05-17.md`

## Active Manager Directives

See `quant-lab/decisions/manager-2026-05-17.md` for full details.

Priority order:
1. Fix Stall_Harvest SL/TP inversion (30 min)
2. Fix Constraint_Anchor partial exits (1 hour)
3. Fix Dual_Engine SL tightening (1 hour)
4. Debug Two_Plays entry condition (2 hours)
5. Tune Blind_Structural_Chain thresholds (2 hours)
6. Redesign P90P_Distribution as target module (3 hours)
7. Backtest winners on USD/CHF (Goal 5)
8. Build basket portfolio (Goal 6)
