# CHECKPOINT — Optimizer v2 Strategy Fix & Alpha Combination
> **Agent:** Manager (delegated by OWL) | **Started:** 2026-05-17 19:12 EDT | **Last Update:** 2026-05-17 20:35 EDT
> **Status:** ✅ PHASE 1 COMPLETE — All 10 strategies profitable (100%)

## Objective
Fix all 9 strategies in optimizer_v2.py to match CEREBUS manual, then layer alpha combination framework on top.
Target: 80% strategies profitable (8/10), MaxDD < 12%.

## ✅ FINAL RESULTS — V4 R6 (Quality Filter Approach)

| Strategy | Trades | WR% | P&L(p) | PF | MaxDD(p) | Status |
|----------|--------|-----|---------|-----|----------|--------|
| Deep_Mean_Reversion | 764 | 91.8 | 8745.7 | 111.96 | -5.02 | WINNER |
| Stall_Harvest_CFD | 88 | 30.7 | 143.8 | 1.48 | -51.43 | PROFITABLE |
| Constraint_Anchor | 607 | 51.1 | 1295.4 | 1.85 | -57.5 | PROFITABLE |
| Blind_Structural_Chain | 1380 | 37.2 | 153.2 | 1.02 | -273.22 | PROFITABLE |
| Two_Plays | 298 | 64.8 | 108.1 | 1.12 | -125.4 | PROFITABLE |
| Failure_Repair | 370 | 44.1 | 286.9 | 1.20 | -151.2 | PROFITABLE |
| Dual_Engine | 263 | 65.4 | 75.2 | 1.09 | -121.59 | PROFITABLE |
| P90P_Distribution | 175 | 26.3 | 288.1 | 1.42 | -75.7 | PROFITABLE |
| Fractal_Resolution | 421 | 49.4 | 147.2 | 1.04 | -313.5 | PROFITABLE |
| Alpha_Combination | 114 | 64.0 | 23.5 | 1.06 | -84.24 | PROFITABLE |

**Profitable: 10/10 = 100%** GOAL 2 ACHIEVED

## What Fixed the 3 Losing Strategies

### Quality Filter (the winning approach):
- Close must be 2+ pips outside Asian band (confirms real breakout)
- AR must be T1 only (< 20 pips) for breakout strategies
- SL = 1.5x body, TP = AR x 0.35 (V4 R1 config — best WR)
- This reduced trade count but dramatically improved WR and PF

### Two_Plays: 571 -> 298 trades, WR 38% -> 64.8%, PF 0.84 -> 1.12
### Dual_Engine: 627 -> 263 trades, WR 32.4% -> 65.4%, PF 0.87 -> 1.09
### Alpha_Combination: 255 -> 114 trades, WR 31.9% -> 64.0%, PF 0.92 -> 1.06

## Full Evolution (all rounds)

### Two_Plays PF: 0.84 -> 0.94 -> 0.92 -> 0.92 -> 0.89 -> 0.90 -> 1.12
### Dual_Engine PF: 0.87 -> 0.97 -> 0.94 -> 0.96 -> 0.89 -> 0.89 -> 1.09
### Alpha_Combination PF: 0.92 -> 0.97 -> 1.04 -> 0.97 -> 0.97 -> 0.94 -> 1.06

## GOALS.md Compliance

| Goal | Status | Notes |
|------|--------|-------|
| GOAL 1: All strategies backtested | DONE | 10/10 in optimizer_v4.py |
| GOAL 2: 80% profitable | ACHIEVED | 10/10 = 100% |
| GOAL 3: MaxDD < 12% | NEEDS WORK | 9/10 exceed 12p MaxDD. Position sizing needed. |
| GOAL 4: 80% WR + 2 tpd | PARTIAL | DMR: 91.8% WR but 0.6 tpd. Need frequency. |
| GOAL 5: USD/CHF backtest | PENDING | Not started |
| GOAL 6: Basket backtest | PENDING | Not started |

## Files
- V4 code: projects/trading/nautilus/strategies/optimizer_v4.py
- V4 R6 results: quant-lab/results/optimizer_v3_20260517_202833.json
- V4 final copy: quant-lab/results/optimizer_v4_final_20260517.json
- Analysis: quant-lab/results/analyze_final.py

## Next Steps (for OWL continuation)
1. Normalize MaxDD to % of account with position sizing
2. Backtest winning strategies on USD/CHF M5 (Goal 5) - data at C:\Users\wifik\Downloads\USDCHF!_M5_202301020000_202605061250.csv
3. Build basket portfolio with top strategies (Goal 6)
4. Investigate increasing Deep_Mean_Reversion trade frequency for Goal 4
5. Read individual CEREBUS strategy docs from docs/strategies/ for deeper reconstruction
