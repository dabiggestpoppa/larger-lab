# 🔧 Optimizer Report — 2026-05-17

## Status
Completed backtesting all 9 strategies from optimizer_v2.py on EUR/USD M5 (249,484 bars, Jan 2023 – May 2026).

## Results Summary

| Strategy | Trades | WR% | P&L(p) | PF | MaxDD | Exp | Verdict |
|----------|--------|-----|--------|----|-------|-----|---------|
| Deep_Mean_Reversion | 764 | 91.8 | +8745.7 | 111.96 | -5.0 | +11.4 | ✅ WINNER |
| Stall_Harvest_CFD | 88 | 100.0 | +867.5 | 867.46 | 0.0 | +9.9 | ⚠️ SUSPICIOUS |
| Failure_Repair | 370 | 38.4 | +214.1 | 1.17 | -144.3 | +0.58 | 🟡 Marginal |
| P90P_Distribution | 255 | 14.9 | +141.4 | 1.12 | -224.7 | +0.56 | 🟡 Marginal |
| Fractal_Resolution | 808 | 43.8 | +197.0 | 1.03 | -679.4 | +0.24 | 🟡 Marginal |
| Blind_Structural_Chain | 1622 | 29.7 | -168.2 | 0.97 | -341.3 | -0.10 | 🔴 Losing |
| Two_Plays | 557 | 35.0 | -229.3 | 0.89 | -282.6 | -0.41 | 🔴 Losing |
| Constraint_Anchor | 607 | 32.9 | -265.4 | 0.87 | -270.3 | -0.44 | 🔴 Losing |
| Dual_Engine | 627 | 65.9 | -689.3 | 0.85 | -880.0 | -1.10 | 🔴 Losing |

## Key Findings

### ✅ Deep_Mean_Reversion — NEW WINNER
- **91.8% WR, +8745p PnL, PF 111.96, MaxDD only -5p**
- 701 wins / 63 losses across 764 trades
- Avg win 12.6p vs avg loss -1.25p — incredible R:R
- This is the **flagship strategy** — meets Goal 4 (80% WR target)
- **Concern**: 100% TP hit rate (700/764) suggests the TP target (reversion to activation level) may be too easy. The SL at 220% extension is rarely hit (only 63 times). Need to verify this isn't a bug in the mean-reversion TP logic.

### ⚠️ Stall_Harvest_CFD — Still Suspicious
- **100% WR, 88 trades, 0 losses** — but ALL 88 exits are SL hits
- This means the TP was NEVER hit — every trade was stopped out
- Yet PnL is positive (+867p) because avg win is +9.9p
- **BUG FOUND**: The `by_exit` shows "sl: 88" — ALL trades exited via SL. This is wrong — the SL should only hit on losses. The trade management appears to be treating SL hits as winning exits.
- **NEEDS FIX**: The stall zone entry logic is likely inverted — entering in the wrong direction.

### 🔴 Dual_Engine — High WR but Catastrophic Losses
- **65.9% WR** looks good, but **-689p PnL** and **-880 MaxDD**
- Avg loss is -21.56p vs avg win +9.5p — losses are 2.3x larger
- The Anchor SL at opposite Asian extreme is too wide
- **Fix needed**: Use 80% body boundary as SL (per manual), not opposite Asian extreme
- The amplifier component adds trades but the R:R is broken

### 🔴 Constraint_Anchor — Same Problem
- 32.9% WR, avg loss -5.19p vs avg win +9.23p
- SL is at opposite Asian extreme (too wide) — 407 SL hits vs only 199 TP hits
- **Fix needed**: Tighten SL to 80% body boundary per Dual_Engine manual

### 🔴 Blind_Structural_Chain — Too Many Losing Trades
- 1622 trades but 29.7% WR, -168p PnL
- 1136 SL hits vs 474 TP hits — the SL is too tight or entry timing is wrong
- The 32-50% Goldilocks zone entry needs refinement
- **Fix needed**: The impulse threshold and pullback detection needs tuning

### 🟡 P90P_Distribution — Low WR but Positive
- 14.9% WR but +141p PnL — classic lottery ticket profile
- Avg win +34p vs avg loss -5.3p — 6.4x R:R
- Only 12 TP hits out of 255 trades — the dynamic targets are too far
- **Fix needed**: The weighted factor (2.18-3.12x AR) produces targets that are too ambitious

### 🟡 Failure_Repair — Promising Direction
- 38.4% WR but +214p PnL, PF 1.17
- Avg win +10.5p vs avg loss -5.6p — 1.9x R:R
- The repair edge is real but needs tighter filters

### 🟡 Fractal_Resolution — Positive but High DD
- 43.8% WR, +197p PnL, PF 1.03
- But MaxDD is -679p — too risky as-is
- The shift engine catches the 1.44x counter-moves but SL is too wide

### 🔴 Two_Plays — Base 80 Needs Work
- 35% WR, -229p PnL
- The P90 close-outside-band filter may not be working correctly
- Need to verify the entry condition logic

## Stall_Harvest Bug Analysis

The Stall_Harvest_CFD result is definitely a bug:
1. All 88 exits show as "sl" — but with 100% WR and +867p PnL
2. This means `manage_trade` is returning `reason: 'sl'` but with positive PnL
3. The SL level is likely placed on the wrong side of entry for a mean-reversion trade
4. When price touches the "SL" level, it's actually hitting the target direction
5. **Root cause**: The entry direction and SL/TP are inverted — the "SL" is effectively the TP

## Next Fixes Needed

1. **Stall_Harvest**: Invert entry direction — the strategy enters at 168% stall zone expecting reversion, but SL/TP are swapped
2. **Dual_Engine + Constraint_Anchor**: Fix SL from opposite Asian extreme to 80% body boundary
3. **Blind_Structural_Chain**: Tune impulse thresholds and widen SL buffer
4. **P90P_Distribution**: Reduce weighted factor targets or add proximity filter
5. **Two_Plays**: Debug entry condition — verify close-outside-band check is working

## Data Available
- EUR/USD M5: 249,484 bars (Jan 2023 – May 2026) — already loaded
- Results saved to: quant-lab/results/optimizer_v2_20260517_060543.json
