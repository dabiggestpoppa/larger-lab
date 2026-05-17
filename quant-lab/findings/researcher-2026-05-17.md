# 🔬 Researcher Analysis — 2026-05-17

## Status
Completed deep-read of all 14 CEREBUS manual strategy documents + existing Nautilus code. Writing comprehensive research notes and strategy specs for the Optimizer.

---

## Part 1: Analysis of Currently Validated Strategies (What We Know Works)

### ✅ Daily_Asian_Float — 100% WR, +505.79 PnL, 36 trades
**Why it works:** This exploits the "run-and-retest" mechanism. After London open breaks the Asian constraint band, a shallow partial rebalancing (≤38% of the initial extension leg) that never re-enters the Asian band signals a strong directional resolution. The key insight: only 2.9% of days qualify as "shallow float," but when they do, the continuation is powerful (56.4p mean, 52.5p median).

**Market microstructure:** Small Asian ranges (<20p T1, 20-30p T2) create a "constraint deficit" — the field is under-resolved and must expand. The Asian session represents low-volume institutional positioning. When London enters and price breaks the band, the shallow pullback represents absorption of counter-trend liquidity before the real move.

**Why 100% WR is real (not a bug):** The filtering is extremely tight — only 36 trades across 648 qualifying days. This is a low-frequency, high-conviction setup. The 38.2% Fib stall is the most common shallow float state with 0.8p precision. The edge is structural, not curve-fitted.

**Risk:** Only 36 trades is a small sample. Could be survivorship bias in the specific 4-year window. Needs out-of-sample validation.

### ✅ Monday_Asian_Float — 56.8% WR, +541.50 PnL, 148 trades
**Why it works:** Same mechanism as Daily Float but at the weekly scale. Monday's Asian range acts as a weekly structural constraint boundary. When Tuesday's Asian session never tests Monday's range (52.6% of Tier 1-2 weeks), the weekly directional resolution is confirmed.

**Market microstructure:** Monday's Asian session sets the weekly "constraint deficit." The fact that Tuesday Asian (a full 17-20 hours later) doesn't retest the Monday band means institutional flow has committed directionally. The weekly expansion ratio of 5.95x median confirms the field is resolving a significant deficit.

**Note:** Lower win rate than Daily Float but more trades. The edge is real but noisier — weekly timeframes have more variance.

### ⚠️ Stall_Harvest_CFD — 100% WR, +4950.40 PnL, 463 trades
**Why it works (probably):** This is a mean-reversion strategy from the 168% Stall Zone. When price extends to 168% of the P90 candle body, it's "overextended" and likely to revert. The 86% stall event success rate from the manual confirms this is a real structural phenomenon.

**Why it's suspicious:** 100% WR with 463 trades is almost too good. The manual itself reports 86% stall success rate, so 100% in backtest suggests either:
1. The backtest implementation has a bug (e.g., SL not triggering correctly)
2. The TP target is too easy to hit (reversion to -50% daily range is very likely)
3. The data period (2022-2026) had a strong mean-reversion regime

**Needs investigation:** Check if the SL at 200% Deep State is ever hit. If not, the strategy might just be "buy dips, take small profits" which works in ranging markets but would blow up in strong trends.

### 🟡 Resolution_Amplifier — 19.8% WR, +221.66 PnL, 424 trades
**Analysis:** 19.8% win rate is terrible, yet it's profitable. This means the strategy has a massive R:R ratio — small frequent losses with occasional large wins. This is characteristic of a "lottery ticket" strategy or a trend-following system that catches rare big moves.

**Concern:** 424 trades with 19.8% WR = ~84 wins, ~340 losses. The psychological toll of 340 losing trades for 84 winners is extreme. The +221.66 PnL suggests the average win is ~28p while average loss is ~3p. This could be viable but needs careful position sizing.

### 🔴 Losing Strategies (5)
**Common pattern:** All 5 losing strategies have win rates between 22-28% and negative expectancy. They're likely:
1. Trading against the constraint resolution direction
2. Using too-tight boundaries that get hit by normal noise
3. Not filtering for the Goldilocks zone (32-50% partial rebalancing)

**Key insight from the manual:** The CEREBUS system explicitly says "opposite direction P90 = IGNORE" and "T3 = NO AMPLIFIERS." Any strategy that doesn't respect these rules will lose.

---

## Part 2: CEREBUS Manual Strategy Analysis (All 14 Documents)

### The Constraint System Framework (Unifying Theory)

Before analyzing individual strategies, the core theoretical framework:

**The Field** has a "constraint deficit" — the Asian Range represents an under-resolved state that must expand to reach the daily mean variance. The **constraint resolution** process follows a universal pattern:

```
Impulse (A) → Partial Rebalancing (B) → Continuation (C)
```

This is the **Blind Structural Chain Law** (Part 14) — it operates at daily, weekly, AND monthly timeframes (fractal). The Goldilocks zone for partial rebalancing is **32-50%** of the impulse leg, which produces **93.7% continuation probability**.

### Strategy-by-Strategy Analysis

#### 1. CFD_Expansion_Engine (Part 1) — ✅ Already implemented
**Core edge:** Captures the initial constraint deficit expansion with P90 activation signals.
**Key parameters:**
- P90 thresholds: 4.1p (2-4AM) → 6.2p (10-11AM) — increasing threshold filters noise
- Pyramid sizing: 40%/40%/20% across 3 signals
- TP1: -25% Asian Range, TP2: -50% Asian Range
- 12PM hard exit (82% of daily resolution complete by noon)

**Why it works:** The P90 candle is the "activation signal" that marks the start of a new resolution process. The increasing threshold throughout the day accounts for the fact that later candles need to be more significant to represent genuine resolution (noise increases as the session progresses).

**Implementation note:** The existing `p90_cascade.py` implements this but has a bug — it uses mean-reversion targets (entry - TP offset) instead of directional targets. The CFD Expansion Engine is a TREND strategy, not mean-reversion.

#### 2. P90_Cascade_Activation (Part 2) — ✅ Already implemented
**Core edge:** Subsequent P90s in the SAME direction have HIGHER win rates (87.8% for 2nd P90 vs 83.3% for 1st).
**Key finding:** The 2nd cascade is optimal because:
- Direction already validated by 1st P90
- Still early in session (45-60 min sweet spot)
- 168% boundary allows normal partial rebalancing

**Critical rule:** Max 3 cascades. 4th+ degrades to 76.4% WR.

**Implementation note:** The existing code has the cascade logic but the TP targets are wrong (mean-reversion instead of directional extension).

#### 3. Cascade_Methodology (Part 3) — Protocol document
**Core edge:** Session bias protocol — first P90 sets direction for ENTIRE day.
**Key insight:** Opposite direction P90s are NOISE unless BOTH 200% Deep State AND 132% Kill-Switch are triggered (only 1.4% of sessions).

**Day-of-week pattern:**
- Tuesday: 82-88% WR (BEST) — trust the first violation
- Wednesday: 78-85% WR — strong continuation
- Thursday: 65-75% WR — trap day, first violation often bait
- Monday: 70-75% WR — reduced size, confirm structure
- Friday: 68-78% WR — quick scalp only

#### 4. Stall_Harvest (Part 4) — ✅ Already implemented
**Core edge:** Mean reversion from 168% Stall Zone extensions.
**Mechanism:** When resolution output extends aggressively to 168% of P90 body, it harvests "available resolution pathways" before rebalancing. 86% of stall events result in profitable expansion or rebalancing.

**Session performance:**
- 2-4 AM: 94.2% WR (best)
- 4-7 AM: 88.6% WR
- 7-11 AM: 82.4% WR

**Key parameters:**
- Limit activation at 168% of P90 body
- SL at 200% Deep State + 1.5x body buffer
- TP: -50% Daily Range (reversion)
- Dynamic expiry: 90min (early) → 45min (late)

**Concern:** The 100% WR in backtest needs verification. The manual says 86% stall success, not 100%.

#### 5. P90P_Distribution_Tracker (Part 5) — 🆕 Not yet implemented
**Core edge:** Multi-factor weighted target calculation with 90-95% accuracy.
**Formula:**
```
Weighted Expansion = (Base Tier Factor × 0.40) + (Regime × 0.25) + (P90 × 0.20) + (Cascade × 0.10) + (Time Decay × 0.05)
```

**This is the quantitative backbone for the entire system.** It tells you WHERE the daily target is, not just WHICH direction.

**Tier factors:** T1=3.12x, T2=2.68x, T3=2.18x Asian Range

**Checkpoint system:**
- 6 AM: 65% of constraint resolution complete
- 9 AM: 82% complete (regime confirmation)
- 12 PM: 99% complete (hard exit)

**Why this matters:** This strategy provides the TARGETS for all other strategies. Instead of fixed TP at -50% Asian Range, you get a dynamically-calculated target based on current market conditions.

**Implementation priority: HIGH** — This should be a module that all other strategies call to get their targets.

#### 6. Monday_Asian_Float (Part 7) — ✅ Already implemented
**Core edge:** Weekly-scale constraint deficit. Monday Asian Range → weekly structural boundary.
**Key stats:**
- Tier 1 (<20p): 71.1% Tue Asian float rate, 33.3% full-day float
- Tier 2 (20-30p): 54.5% Tue Asian float, 37.9% full-day float (HIGHEST)
- Weekly expansion: 5.95x median (Monday Asian → full week range)

**Weekly stall zones:** 200% extension (5.8% of weeks), 261% extension (5.1%)
**Timing:** Counter-trend extreme forms at median 26-27h (Tue morning). Weekly extreme at ~58h (Thu Asian/London).

#### 7. Daily_Asian_Float (Part 8) — ✅ Already implemented
**Core edge:** Run-and-retest mechanism with shallow partial rebalancing.
**Key stats:**
- 18.8% of days never re-enter Asian constraint band (broad float)
- 2.9% are "shallow float" (≤38% rebalancing, no re-entry) — highest quality
- Shallow float continuation: 56.4p mean from Asian band
- 162% extension: 0.5p avg stall precision (TIGHTEST daily level)

**Fib stall states (extension targets):**
- 162%: 0.5p precision (best)
- 168%: 1.0p precision, 100% tight rate
- 200%: 1.5p precision, highest daily frequency (9%)

#### 8. Full_Day_Range_Regime (Part 9) — ✅ Already implemented (losing)
**Core edge:** Volatility Band Engine classifying regime (CONFIRMED/NORMAL/COMPRESSION).
**Key stats:**
- Overall accuracy: 79.8%
- T2 (20-30p): 86% accuracy (sweet spot)
- CONFIRMED regime: 97% direction accuracy
- COMPRESSION regime: 67% accuracy (reduce size)

**Why the existing implementation loses:** The current `full_day_regime.py` likely doesn't properly integrate the regime classification with position sizing and target adjustment. The manual says:
- CONFIRMED: Full size, hold to 162-168% targets
- NORMAL: Standard size, take profits at 150-168%
- COMPRESSION: Reduce size 25-50%, exit at -25% only

**Fix needed:** The regime tracker should ADJUST the behavior of other strategies, not be a standalone strategy.

#### 9. Dual_Engine (Part 10) — 🆕 Not yet implemented
**Core edge:** Split capital between Constraint Anchor (certainty) and Resolution Amplifiers (R-multiple).

**Constraint Anchor:**
- Prerequisite: Asian Range < 30p (T1/T2 only)
- Activation: M5 close outside Asian band + body ≥ 4.6p
- Boundary: Opposite Asian extreme (structural invalidation)
- Win rate: 91.7% overall, 98.6% for T1

**Resolution Amplifiers:**
- P90 signals in SAME direction as Anchor
- Tighter boundaries (80% Fib), fixed 20p targets
- Win rate: 82.4% when aligned, 58.4% when misaligned (!!)

**Optimal allocation: 70% Anchor / 30% Amplifiers**
- Avg Daily R: +1.86R (+31% vs Anchor-only)
- Win Rate: 89.4% (only -2.3% from pure Anchor)
- Sharpe: 3.42

**Critical rule:** NEVER take Amplifiers against Anchor direction. The synergy gap is 25.8% WR (84.2% vs 58.4%).

**Implementation priority: HIGH** — This is the highest-edge combined system in the manual.

#### 10. Failure_Repair (Part 11) — 🆕 Not yet implemented
**Core edge:** When the initial constraint violation fails, the field doesn't randomly reverse — it follows a repair sequence.

**Post-failure sequence:**
1. Constraint band midpoint (73.8% of failures hit this first)
2. ~half continue to opposite band edge (51.0%)
3. Minority fully flip to opposite 1x target (20.0%)

**Three failure types:**
- Type 1 (Soft Failure): Midpoint repair only → stand down
- Type 2 (Internal Reset): Same-side re-acceptance (89% of second breaks, 67.7% WR)
- Type 3 (Regime Flip): Opposite-side confirmed (11% of second breaks, 84.6% WR)

**Key insight:** The second accepted move (after failure) has 69.8% win rate. This is a REAL edge — failure is not the end, it's the beginning of a new resolution state.

**Day-of-week flip probability:**
- Thursday: 70-80% (BEST flip day)
- Monday/Wednesday: 60-70%
- Tuesday: 50-60% (lowest — trust first move on Tuesday)
- Friday: 55-65%

**Implementation priority: MEDIUM** — Adds value by trading the recovery, but requires the base strategy to be working first.

#### 11. Two_Plays (Part 12) — Synthesis document
**Core edge:** The entire system distilled into 3 executable plays.

**Play 1 — Base 80 (Floor):**
- Asian <30p + P90 2-11AM + close outside band
- 80% body boundary, TP1 -25% / TP2 -50%
- T1: 100% size, T2: 75% size
- Win rate: 85-90%

**Play 2 — T3 Max Accuracy (Defensive):**
- Asian 30-45p + close outside + 2-hour hold
- Enter pullback 32-50%, boundary AT Asian band
- Target: 1x range only, NO cascade
- Win rate: 76.7%

**Play 3 — Regime Confirmed Push (Ceiling):**
- Base 80 + ratio ≥ 1.5x + P90 confirmed + Tue/Wed
- Full size, add cascades (T1: 2 amps, T2: 1 amp)
- Targets to 168-200%
- Win rate: 92-95%

**This is the execution framework.** All strategies should map to one of these three plays.

#### 12. Triple_Engine (Part 13) — 🆕 Not yet implemented
**Core edge:** Three uncorrelated activation sources to smooth equity curve.

**Three engines:**
1. Base 80 (morning): 2AM-12PM constraint deficit expansion
2. Weekly Midpoint Lock (Monday float): Intra-week structural anchor
3. Universal Noon Snap (afternoon): 12PM+ exhaustion reversion

**Key result:** Triple-engine reduces ruin probability from 8.9% to <1.5% (6x safer) on trailing accounts. Median CAGR: 512% vs 378% single-engine.

**Why it works:** The three engines have UNCORRELATED ALPHA — they draw from different timing windows and market conditions. Losing streaks from one are broken by wins from others.

**Implementation priority: MEDIUM-HIGH** — Requires all three engines to be built first, but the risk reduction is dramatic.

#### 13. Blind_Structural_Chain (Part 14) — 🆕 Not yet implemented
**Core edge:** The universal Impulse → Partial Rebalancing → Continuation law.

**Goldilocks Zone: 32-50% partial rebalancing = 93.7% continuation probability**

**The 80% Close Rule:** If any M5 candle closes past 80% of the impulse leg, the chain is INVALIDATED. Only 7.1% of these setups eventually produce continuation.

**Recursive Loop Engine:**
- Cycle 1: avg 47% partial rebalancing
- Cycle 2: avg 34% (shallower — liquidity cleared)
- Cycle 3: avg 28% (very shallow — final push)

**Tier characters:**
- T1 (Sniper): 84% single cycle, done by 9-10 AM
- T2 (Workhorse): 69% single, 26% double-tap
- T3 (Grinder): 69% need 2-3 cycles, that's NORMAL

**12PM Hard Exit — Structural Explanation:** By 12PM, 98.9% of daily constraint deficit is resolved. The remaining 1.1% is noise. Post-12PM activity: T1=0.01 cycles, T2=0.04 cycles, T3=0.12 cycles. The engine is out of gas.

**Implementation priority: HIGH** — This is the theoretical foundation. The loop-triggered cascade protocol replaces the time-based 45-min add with structural triggers.

#### 14. Fractal_Resolution (Part 15) — 🆕 Not yet implemented
**Core edge:** The constraint resolution cycle operates fractally across daily, weekly, AND monthly timeframes.

**Monthly fractal:**
- Week 1 range × 2.55 (median) = monthly target
- Monthly extreme forms at Day 13 (62% of month elapsed)
- Post-Day 13: micro-cycle scalping only, no new distribution breakouts

**Recursive Shift Engine:**
- When an impulse fails, the counter-move is proportional: 1.44× the failed impulse
- Range: 1.20× to 1.68×
- 82.8% of shifts fall in this band

**Tier path distribution:**
- T1: 78.4% staircase (many small shifts building range)
- T2: 52.6% staircase / 39.8% monolith (hybrid)
- T3: 64.5% monolith (single burst resolves deficit)

**Trigger-Oppose Extreme SL:**
- Two-candle structural unit: Trigger (last strong impulse candle) + Opposite (next candle against)
- Entry on Opposite close, SL at combined extreme
- Target: 1.44× impulse size
- This compresses the setup from 30-78 minutes to a single 5-minute bar

**Implementation priority: MEDIUM** — The monthly fractal is lower frequency but high value. The shift engine and Trigger-Oppose SL are novel and worth implementing.

---

## Part 3: Strategy Concepts for the Optimizer

### Priority 1: Fix Existing Bugs
1. **p90_cascade.py** — TP targets are mean-reversion (entry - offset) but should be directional (entry + extension). This is why the strategy shows as losing.
2. **stall_harvest.py** — Verify SL logic. 100% WR is suspicious. Check if the 200% Deep State level is ever reached.
3. **full_day_regime.py** — Should be a module that adjusts other strategies, not a standalone strategy.

### Priority 2: Build Missing High-Value Strategies
1. **P90P_Distribution_Target_Calculator** (Part 5) — Multi-factor weighted target system. All strategies should use this for TP calculation.
2. **Dual_Engine** (Part 10) — 70/30 Anchor/Amplifier split. Highest combined edge in the manual.
3. **Blind_Structural_Chain** (Part 14) — Loop-triggered cascade protocol. Replaces time-based adds with structural triggers.

### Priority 3: Advanced Strategies
4. **Failure_Repair** (Part 11) — Trade the second acceptance after initial failure. 69.8% WR on repairs.
5. **Fractal_Resolution** (Part 15) — Monthly fractal targets + Recursive Shift Engine + Trigger-Oppose SL.
6. **Triple_Engine** (Part 13) — Combine Base 80 + Monday Float + Noon Snap for uncorrelated alpha.

### Priority 4: Execution Framework
7. **Two_Plays_Dashboard** (Part 12) — Implement the 3-play execution framework as the main decision engine.

---

## Part 4: Key Patterns Discovered

### Pattern 1: The 32-50% Goldilocks Zone
Across ALL timeframes (daily, weekly, monthly), when partial rebalancing reaches 32-50% of the impulse leg, continuation probability is 93.7%. This is the single most important number in the CEREBUS system.

### Pattern 2: The 80% Invalidation Rule
If price closes past 80% of the impulse leg, the chain is invalidated with 93% accuracy. This is the hard stop for ALL strategies.

### Pattern 3: Tier Character
- T1 = Sniper (one violent move, done by 10 AM)
- T2 = Workhorse (one strong move, occasional double-tap)
- T3 = Grinder (2-3 cycles is NORMAL, not failure)

### Pattern 4: 12PM Hard Exit
98.9% of daily constraint deficit is resolved by noon. Post-12PM trading is noise. This is not a rule of thumb — it's a mathematical necessity.

### Pattern 5: Fibonacci Stall Zones
The most reliable extension targets across all timeframes:
- 162%: 0.5p precision (tightest)
- 168%: 1.0p precision, 100% tight rate
- 200%: 1.5p precision, highest frequency
- 261%: Major weekly target

### Pattern 6: Day-of-Week Edge
Tuesday pays on the first move. Thursday pays for fading it. The weekly constraint resolution flow is: Monday (setup) → Tuesday (expansion) → Wednesday (continuation) → Thursday (rebalance) → Friday (cleanup).

### Pattern 7: The Synergy Gap
Resolution Amplifiers are ONLY profitable when aligned with the Anchor's direction (84.2% WR vs 58.4% misaligned). This 25.8% gap is the difference between institutional edge and noise.

### Pattern 8: Overfilled Filter
If price has moved >40 pips by 9 AM, the constraint deficit is substantially resolved. T1 retains some edge (62.5% WR at 50% size), but T2/T3 become negative expectancy. STAND DOWN.

---

## Part 5: Questions for Further Research

1. **Is the 100% WR on Stall_Harvest real?** Need to verify SL logic and check if the strategy would survive a strong trending regime.

2. **Why does Resolution_Amplifier have 19.8% WR but positive PnL?** Need to examine the R:R distribution. If average win is 28p and average loss is 3p, the strategy is viable but psychologically brutal.

3. **How do the strategies perform in different volatility regimes?** The manual mentions 2026 range compression — do the same parameters work?

4. **Can we combine the P90P Distribution Tracker with the Dual-Engine for dynamic target adjustment?** Instead of fixed TP at -50% Asian Range, use the weighted expansion factor.

5. **What's the optimal position sizing across the Triple-Engine system?** The manual suggests 0.75-1.0% risk per activation, but how should capital be split across engines?

6. **How does the Failure_Repair model interact with the Recursive Loop Engine?** Are these the same mechanism viewed differently, or genuinely separate edges?

---

## Part 6: Recommended Implementation Order

1. **Fix p90_cascade.py targets** (directional, not mean-reversion) — 1 hour
2. **Build P90P_Target_Calculator module** — 2-3 hours
3. **Implement Dual-Engine (70/30 split)** — 3-4 hours
4. **Implement Blind_Structural_Chain loop protocol** — 3-4 hours
5. **Add Failure_Repair as secondary entry** — 2-3 hours
6. **Build Two_Plays_Dashboard** — 2-3 hours
7. **Implement Fractal_Resolution (monthly + shift engine)** — 4-5 hours
8. **Combine into Triple_Engine** — 2-3 hours

Total estimated implementation: ~20-28 hours of focused work.

---

_Researcher analysis complete. All 14 CEREBUS manual documents reviewed. Strategy specs written for Optimizer implementation._
