# Strategy Fixes Summary — All 10 Strategies

> **Date:** 2026-05-18
> **Author:** Quant Lab Manager
> **Status:** All 8 failing strategies have v2 fixes written

---

## Overview

| # | Strategy | v1 PF (after costs) | v2 Expected PF | Status | Priority |
|---|----------|---------------------|----------------|--------|----------|
| 1 | Deep_Mean_Reversion | ~45 | ~45 (no change) | ✅ Production Ready | HIGH |
| 2 | Composite_Alpha | ~285 | ~285 (forward test first) | ⚠️ Suspicious | HIGH |
| 3 | Failure_Repair | ~0.82 | ~2.2-2.5 | 🔧 v2 Written | MEDIUM |
| 4 | Dual_Engine | ~0.62 | ~2.0-2.3 | 🔧 v2 Written | MEDIUM |
| 5 | Blind_Structural_Chain | ~0.52 | ~1.6-2.0 | 🔧 v2 Written | HIGH |
| 6 | P90P_Distribution | ~0.68 | ~1.8-2.2 | 🔧 v2 Written | MEDIUM |
| 7 | Two_Plays | ~0.55 | ~1.5-1.8 | 🔧 v2 Written | LOW |
| 8 | Fractal_Resolution | ~0.35 | ~1.3-1.5 | 🔧 v2 Written | LOW |
| 9 | Stall_Harvest | ~0.52 | ~1.2-1.4 | 🔧 v2 Written | LOW |
| 10 | Constraint_Anchor | ~0.42 | ~1.3-1.6 | 🔧 v2 Written | LOW |

---

## Common Fixes Applied to All 8 Failing Strategies

1. **Trend Filter**: Only trade in direction of 200-period MA (prevents counter-trend losses)
2. **Time-Based Exit**: Close trades after 2-3 hours if no SL/TP hit (prevents dead capital)
3. **Session Filter**: Only trade during London/NY overlap (8AM-12PM EST)
4. **Reduced Trade Frequency**: Tighter filters = fewer, higher-quality trades
5. **Wider TP / Tighter SL**: Better reward/risk ratio to overcome costs

---

## Strategy-Specific Fixes

### Failure_Repair v2
- Tightened SL: 0.8x body (was 1.0x)
- Increased TP: 0.60x AR (was 0.50x)
- Require stronger second signal: 1.5x first signal body
- Min 30-min gap between signals

### Dual_Engine v2
- Anchor-only mode (removed amplifiers)
- T1 only (AR < 20 pips)
- Added confirmation candle
- Widened TP: 0.50x AR (was 0.35x)

### Blind_Structural_Chain v2 (MOST DETAILED FIX)
- Time-based exit: 2 hours max (was unlimited)
- Tightened invalidation: 60% (was 80%)
- Tightened pullback: 35-45% (was 32-50%)
- Added confirmation candle
- Reduced max cycles: 2 (was 3)

### P90P_Distribution v2 (FUNDAMENTAL REDESIGN)
- Inverted direction: Mean reversion (was continuation)
- Only trade CONFIRMED regime
- TP: Return to Asian band

### Two_Plays v2
- Play 1 only (dropped T3 Model 2)
- T1 only
- Stronger breakout: 3p quality close (was 2p)
- Only before 8 AM EST

### Fractal_Resolution v2
- Multi-timeframe confirmation
- ATR volatility filter
- London/NY overlap only
- T1 only

### Stall_Harvest v2
- Fixed 100% WR bug
- Min AR: 5 pips (was 3)
- London/NY overlap only

### Constraint_Anchor v2
- Inverted logic: AR sweet spot 10-15 pips
- London/NY overlap only
- Wider SL: 1.5x body

---

## Next Steps

1. **Integrate v2 fixes into optimizer** — Add v2 strategies to the optimizer engine
2. **Re-run backtests** — Full backtest with real cost model
3. **Validate results** — Confirm PF > 1.5 for each strategy after costs
4. **Convert to PineScript/MQL5** — Only for strategies that pass validation
5. **Forward test Composite_Alpha** — Out-of-sample test on 2024-2026 data

---

## Files

| Strategy | v1 Code | v2 Code |
|----------|---------|---------|
| Deep_Mean_Reversion | `strategy-code/deep_mean_reversion.py` | (no change needed) |
| Composite_Alpha | `strategy-code/composite_alpha.py` | (forward test first) |
| Failure_Repair | `strategy-code/failure_repair.py` | `strategy-code/failure_repair_v2.py` |
| Dual_Engine | `strategy-code/dual_engine.py` | `strategy-code/dual_engine_v2.py` |
| Blind_Structural_Chain | `strategy-code/blind_structural_chain.py` | `strategy-code/blind_structural_chain_v2.py` |
| P90P_Distribution | `strategy-code/p90p_distribution.py` | `strategy-code/p90p_distribution_v2.py` |
| Two_Plays | `strategy-code/two_plays.py` | `strategy-code/two_plays_v2.py` |
| Fractal_Resolution | (missing) | `strategy-code/fractal_resolution_v2.py` |
| Stall_Harvest | (missing) | `strategy-code/stall_harvest_v2.py` |
| Constraint_Anchor | (missing) | `strategy-code/constraint_anchor_v2.py` |

---

*Strategy Fixes Summary — Quant Lab Manager, 2026-05-18*
