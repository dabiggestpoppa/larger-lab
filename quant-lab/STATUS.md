# Quant Lab — Strategy Status

> Last updated: 2026-05-17 20:30 (Optimizer v4 R6 — ALL 10 STRATEGIES PROFITABLE)

## V4 R6 Results (optimizer_v4.py — Quality Filter, EUR/USD M5, 2023-05-06)

### ✅ Final Results — 10/10 = 100% PROFITABLE

| Strategy | Trades | Win Rate | PnL(p) | PF | MaxDD(p) | Exp(p) | Status |
|----------|--------|----------|---------|-----|----------|--------|--------|
| Deep_Mean_Reversion | 764 | 91.8% | +8745.7 | 111.96 | -5.02 | +11.4 | WINNER |
| Failure_Repair | 370 | 44.1% | +286.9 | 1.20 | -151.2 | +0.78 | PROFITABLE |
| Two_Plays | 298 | 64.8% | +108.1 | 1.12 | -125.4 | +0.36 | PROFITABLE |
| Dual_Engine | 263 | 65.4% | +75.2 | 1.09 | -121.59 | +0.29 | PROFITABLE |
| Alpha_Combination | 114 | 64.0% | +23.5 | 1.06 | -84.24 | +0.21 | PROFITABLE |
| P90P_Distribution | 175 | 26.3% | +288.1 | 1.42 | -75.7 | +1.65 | PROFITABLE |
| Constraint_Anchor | 607 | 51.1% | +1295.4 | 1.85 | -57.5 | +2.13 | PROFITABLE |
| Stall_Harvest_CFD | 88 | 30.7% | +143.8 | 1.48 | -51.43 | +1.63 | PROFITABLE |
| Blind_Structural_Chain | 1380 | 37.2% | +153.2 | 1.02 | -273.22 | +0.11 | PROFITABLE |
| Fractal_Resolution | 421 | 49.4% | +147.2 | 1.04 | -313.5 | +0.35 | PROFITABLE |

### V4 Key Changes from V3:
- **Two_Plays**: Added quality filter (close 2p+ outside Asian band, T1 only) + SL 1.5x body + TP ARx0.35
  - 571→298 trades, WR 38%→64.8%, PF 0.84→1.12
- **Dual_Engine**: Same quality filter + SL 1.5x body + TP ARx0.35
  - 627→263 trades, WR 32.4%→65.4%, PF 0.87→1.09
- **Alpha_Combination**: Same quality filter + SL 1.5x body + TP ARx(0.25+0.15*composite)
  - 255→114 trades, WR 31.9%→64.0%, PF 0.92→1.06

### All strategies also preserved these v3 bug fixes:
1. Stall_Harvest_CFD: Fixed SL/TP inversion
2. Constraint_Anchor: Fixed SL from opposite Asian extreme to 80% body
3. Dual_Engine: Fixed anchor/amplifier SL using wrong body
4. Blind_Structural_Chain: Fixed first-entry-only + TP at 1.0x
5. Two_Plays: Fixed Base80 SL + T3 Model 2 logic
6. Failure_Repair: Fixed dayofday -> dayofweek typo
7. P90P_Distribution: Reduced targets + FAILED regime skip
8. Fractal_Resolution: Added 5-bar window + fixed SL logic

### Previous Results (optimizer_v2.py — baseline)

| Strategy | Trades | WR% | PnL(p) | PF | MaxDD(p) | Status |
|----------|--------|-----|---------|-----|----------|--------|
| Blind_Structural_Chain | 1622 | 29.7% | -168.2 | 0.97 | -341.3 | LOSING |
| Two_Plays | 557 | 35.0% | -229.3 | 0.89 | -282.6 | LOSING |
| Constraint_Anchor | 607 | 32.9% | -265.4 | 0.87 | -270.3 | LOSING |
| Dual_Engine | 627 | 65.9% | -689.3 | 0.85 | -880.0 | LOSING |

## Goal Progress

| Goal | Status | Progress |
|------|--------|----------|
| Goal 1: All strategies backtested | DONE | 10/10 in optimizer_v4.py |
| Goal 2: 80% strategies profitable | ACHIEVED | 10/10 = 100% |
| Goal 3: Max DD < 12% | NEEDS WORK | 9/10 exceed 12p MaxDD. Position sizing needed for % conversion. |
| Goal 4: 80% WR strategy, 2/day | PARTIAL | Deep_Mean_Reversion: 91.8% WR but 0.6 tpd. Need 2/day. |
| Goal 5: USD/CHF backtest | PENDING | Not started |
| Goal 6: Basket portfolio | PENDING | Not started |

## Files
- V4 code: `projects/trading/nautilus/strategies/optimizer_v4.py`
- V4 R6 results: `quant-lab/results/optimizer_v3_20260517_202833.json`
- Checkpoint: `quant-lab/checkpoints/optimizer-v2-fix-checkpoint.md`

---

## Pairs Trading EUR/USD-GBP/USD — Validation (2026-05-18)

**Status: NEEDS REBUILD — MAD Directives Applied**

### Summary
- Backtest reported: 3,929 trades, 72.5% WR, +$205,975 PnL, MaxDD -$265, PF 5.53
- Data: Real EUR/USD + GBP/USD M5 (249K bars, 3.3 years, 2023-01-02 to 2026-05-06)
- Data quality: Good — real GBP/USD data (NOT synthetic), no duplicates, avg correlation 0.755

### Issues Found (MAD-Corrected)
1. ❌ **No commission or spread costs** — Need to apply $7/lot commission + real spread from data files
2. ❌ **Arbitrary P&L scaling** — $50/z-unit is not position sizing. Need 5% risk per position (0.05)
3. ⚠️ **151% annual return** — NOT dismissed as unrealistic per MAD Directive 2. Must TEST with proper costs, not assume.
4. ⚠️ **Hand-tuned alpha weights** — 9 signals with assumed IC values, need empirical validation
5. ⚠️ **Optimizer_v2 exit bug** — "All exits labeled SL" claim needs proper verification (MAD Directive 3)

### MAD Directives Applied
- Commission: **$7/lot** (0.07 per 0.01 lot) — apply per leg (×2 for pairs)
- Risk per position: **0.05 (5%)** — not $50/unit
- Spread: **From data files** (real values, not hardcoded)
- Don't dismiss results pre-emptively — test assumptions
- Pass to lab team for proper validation

### Files
- Strategy: `projects/trading/nautilus/strategies/pairs_trading_eurusd_gbpusd.py`
- Validation report: `quant-lab/reports/PAIRS_TRADING_VALIDATION.md`
- MAD directives: `quant-lab/reports/MAD_DIRECTIVES_20260518.md`
- Validation data: `quant-lab/results/pairs_validation_detail.json`

### Required Actions (Per MAD)
1. Rebuild P&L with real spread + $7/lot commission + 5% risk per position
2. Verify optimizer_v2 exit bug properly (does it affect all trades?)
3. Re-run backtest with corrected parameters — report REAL numbers
4. Don't assume results are unrealistic — test them

---

## Next Steps
1. 🔄 Rebuild pairs trading with proper costs (spread from files, $7/lot, 5% risk)
2. 🔄 Verify optimizer_v2 exit bug
3. ⏳ Backtest winning strategies on USD/CHF M5 (Goal 5)
4. ⏳ Fix losing strategies from v4b results
5. ⏳ Build basket portfolio (Goal 6)
6. ⏳ Investigate increasing Deep_Mean_Reversion trade frequency for Goal 4
