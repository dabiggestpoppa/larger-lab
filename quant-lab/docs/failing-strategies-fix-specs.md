# Failing Strategies — Fix Specifications

> **Date:** 2026-05-18
> **Author:** Quant Lab Manager
> **Context:** 8/10 strategies fail under real cost model (2.9 pips/trade)
> **Conversion Pipeline:** FROZEN for all 8 strategies

---

## Summary

| # | Strategy | PF (after costs) | Core Problem | Fix Effort | Priority |
|---|----------|-----------------|--------------|------------|----------|
| 1 | Failure_Repair | ~0.82 | Thin edge + high frequency | 3-4h | LOW |
| 2 | Dual_Engine | ~0.62 | High frequency kills edge | 4-5h | LOW |
| 3 | Blind_Structural_Chain | ~0.52 | No time exit + wide invalidation | 4-6h | MEDIUM |
| 4 | Two_Plays | ~0.55 | Essentially zero edge | 2-3h | LOWEST |
| 5 | P90P_Distribution | ~0.68 | 20% WR is fundamental flaw | 5-8h | LOW |
| 6 | Fractal_Resolution | ~0.35 | PF 1.03 = no edge | 6-10h | LOWEST |
| 7 | Stall_Harvest | ~0.52 | Was at breakeven (PF 1.00) | 3-4h | LOWEST |
| 8 | Constraint_Anchor | ~0.42 | Negative edge + high frequency | 5-7h | LOW |

**Recommendation:** Only fix BSC (Medium priority). The rest should be abandoned or completely redesigned.

---

## 1. Failure_Repair

### Core Problem
PF of 1.81 before costs is too thin. The strategy relies on failed breakouts "repairing" into continuations, but the avg win ($8.37) is only 1.8× the avg loss ($4.62). With 436 trades, costs (436 × 2.9 = 1,264 pips) exceed the edge.

### What Needs to Change
1. **Reduce trade frequency** — Add a minimum time between first signal and second signal (at least 30 minutes) to filter out choppy conditions
2. **Tighten SL** — Current SL is 1.0× body. Reduce to 0.8× body to improve risk/reward
3. **Add trend filter** — Only take repairs in the direction of the 200-period MA
4. **Require stronger second signal** — Second P90 must have body ≥ 1.5× the first P90 body

### Expected Impact
| Metric | Current | After Fix |
|--------|---------|-----------|
| Trade Count | 436 | ~250-300 |
| Win Rate | 50.0% | ~55-58% |
| PF | 1.81 | ~2.2-2.5 |

### Effort: 3-4 hours
### Priority: LOW — Even with fixes, the edge is marginal

---

## 2. Dual_Engine

### Core Problem
Highest trade count of any strategy (973 trades). The anchor + amplifier approach generates too many low-quality signals. PF of 1.60 is too thin to overcome 2,822 pips in costs.

### What Needs to Change
1. **Reduce to anchor-only mode** — Remove amplifier entries entirely. They add frequency without proportional edge.
2. **Tighten Asian Range filter** — Only T1 (< 20 pips), no T2
3. **Require confirmation** — After breakout, wait for one candle to close in breakout direction before entering
4. **Widen TP** — Current TP is 0.35× AR. Increase to 0.50× AR to improve reward/risk

### Expected Impact
| Metric | Current | After Fix |
|--------|---------|-----------|
| Trade Count | 973 | ~300-400 |
| Win Rate | 51.2% | ~55-60% |
| PF | 1.60 | ~2.0-2.3 |

### Effort: 4-5 hours
### Priority: LOW — High-frequency approaches are structurally disadvantaged

---

## 3. Blind_Structural_Chain

### Core Problem
Three compounding issues (from BSC Gap Analysis):
1. **No time-based exit** — 29% of trades (489/1,686) never resolved
2. **Invalidation threshold too wide** — 80% allows entries on deep pullbacks that are actually reversals
3. **No trend filter** — Enters counter-trend trades

### What Needs to Change
1. **Add time-based exit** — Close trades after 2 hours if no SL/TP hit
2. **Tighten invalidation** — Reduce from 80% to 60%
3. **Add trend filter** — Only take trades in direction of 200-period MA
4. **Require confirmation candle** — After pullback completes, wait for one candle in impulse direction

### Expected Impact
| Metric | Current | After Fix |
|--------|---------|-----------|
| Win Rate | 43.1% | ~58-62% |
| Trade Count | 1,686 | ~1,200-1,400 |
| PF | 1.14 | ~1.6-2.0 |
| Max DD | -963.8p | ~-400p |

### Effort: 4-6 hours
### Priority: MEDIUM — Core concept (impulse + pullback) is sound. Most fixable of the 8.

---

## 4. Two_Plays

### Core Problem
PF of 1.04 before costs means the edge is essentially zero. The strategy was barely profitable in a zero-cost environment. Two different play types (Base 80 + T3 Model 2) dilute focus.

### What Needs to Change
1. **Focus on Play 1 only** — Drop T3 Model 2 entirely. It adds complexity without edge.
2. **Tighten to T1 only** — Only trade when AR < 20 pips (T1). T2 doesn't add value.
3. **Require stronger breakout** — Increase quality close distance from 2p to 3p
4. **Add time filter** — Only take trades before 8AM EST (best volatility window)

### Expected Impact
| Metric | Current | After Fix |
|--------|---------|-----------|
| Trade Count | 392 | ~150-200 |
| Win Rate | 42.3% | ~50-55% |
| PF | 1.04 | ~1.5-1.8 |

### Effort: 2-3 hours
### Priority: LOWEST — Even with fixes, unlikely to survive costs

---

## 5. P90P_Distribution

### Core Problem
20% WR is a fundamental problem. The strategy needs wins to be 5× larger than losses just to break even. Current avg win (24.12p) / avg loss (5.29p) = 4.6× — close but not enough. Costs tip it over.

### What Needs to Change
1. **Invert the approach** — Instead of entering on P90 direction, enter on mean reversion (like DMR). The 20% WR suggests the P90 direction is actually the WRONG direction.
2. **Or: Add a trend alignment filter** — Only take trades where P90 direction aligns with 200 MA trend
3. **Widen TP** — Current regime-based targets (55-70% of tier factor) are too conservative
4. **Tighten SL** — Current SL is 0.80× body. Reduce to 0.50× body.

### Expected Impact (if inverted)
| Metric | Current | After Fix |
|--------|---------|-----------|
| Win Rate | 20.0% | ~55-65% (inverted) |
| PF | 1.14 | ~1.8-2.2 |

### Effort: 5-8 hours (inversion is a fundamental redesign)
### Priority: LOW — Requires fundamental rethink

---

## 6. Fractal_Resolution

### Core Problem
PF of 1.03 before costs = essentially zero edge. The fractal-based entry detection is generating noise, not signal. Massive MaxDD (-687p) was already disqualifying.

### What Needs to Change
1. **Complete redesign needed** — The fractal detection logic is not producing an edge
2. **If keeping the approach:** Add multi-timeframe confirmation (H1 + M5 alignment)
3. **Reduce frequency** — 808 trades is too many for the edge quality
4. **Add volatility filter** — Only trade when ATR is above its 20-period median

### Expected Impact
| Metric | Current | After Fix |
|--------|---------|-----------|
| Win Rate | 43.7% | ~50-55% |
| PF | 1.03 | ~1.3-1.5 |
| Max DD | -687p | ~-300p |

### Effort: 6-10 hours (essentially a new strategy)
### Priority: LOWEST — Not worth fixing. Better to start fresh.

---

## 7. Stall_Harvest

### Core Problem
Was already at breakeven (PF 1.00) before costs. The 100% WR from optimizer_v2 was a confirmed bug — real performance is ~40%. The strategy has no edge.

### What Needs to Change
1. **Fix the bug first** — The 100% WR bug needs to be understood and documented
2. **If the bug fix changes everything:** Re-evaluate from scratch
3. **If keeping the approach:** Add a minimum AR threshold (current allows AR < 3p which is too tight)
4. **Require session filter** — Only trade during London/NY overlap (8AM-12PM EST)

### Expected Impact
| Metric | Current | After Fix |
|--------|---------|-----------|
| Win Rate | 40.1% | ~48-52% |
| PF | 1.00 | ~1.2-1.4 |

### Effort: 3-4 hours
### Priority: LOWEST — Bug history makes this unreliable

---

## 8. Constraint_Anchor

### Core Problem
Was already unprofitable before costs (PF 0.90). High trade frequency (1,214 trades) + negative edge = worst combination. Costs make it catastrophic.

### What Needs to Change
1. **Reduce frequency by 75%** — Add strict filters: T1 only, London/NY overlap only
2. **Invert the constraint logic** — Current approach enters when AR is near constraints. Instead, enter when AR is in the sweet spot (10-15 pips)
3. **Add mean reversion component** — Combine with DMR-style mean reversion for better entries
4. **Widen SL** — Current SL is too tight, getting stopped out on noise

### Expected Impact
| Metric | Current | After Fix |
|--------|---------|-----------|
| Trade Count | 1,214 | ~200-300 |
| Win Rate | 36.2% | ~48-52% |
| PF | 0.90 | ~1.3-1.6 |

### Effort: 5-7 hours
### Priority: LOW — Negative edge strategies are hard to fix

---

## Overall Recommendation

### Fix Now (Phase 2)
- **Blind_Structural_Chain** — 4-6 hours, most promising fix

### Consider Later (Phase 3)
- **Failure_Repair** — 3-4 hours, marginal
- **Dual_Engine** — 4-5 hours, structural issues
- **P90P_Distribution** — 5-8 hours, needs inversion

### Abandon
- **Two_Plays** — Zero edge
- **Fractal_Resolution** — Zero edge + massive DD
- **Stall_Harvest** — Bug history + no edge
- **Constraint_Anchor** — Negative edge

### Resource Allocation
With limited optimizer time, the priority order should be:
1. **Deep_Mean_Reversion** — Already production-ready, convert now
2. **Composite_Alpha** — Forward test (2-4 hours compute)
3. **BSC Fix** — 4-6 hours development + testing
4. Everything else — Depends on MAD's strategic direction

---

*Failing Strategies Fix Specs — Quant Lab Manager, 2026-05-18*
*Conversion Pipeline: FROZEN for all 8 strategies*
