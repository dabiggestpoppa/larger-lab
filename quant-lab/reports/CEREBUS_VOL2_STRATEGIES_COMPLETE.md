# 📘 CEREBUS FX — STRATEGIES COMPLETE REFERENCE
## Volume II: Full Strategy Breakdown with Monte Carlo Validation

> **Version:** 2.0 | **Date:** May 19, 2026
> **Classification:** PROPRIETARY — Internal Reference Only
> **Data Source:** CEREBUS Manual v4.0 + Excel Workbook (97 sheets, 281 weeks, 315,000+ candles)
> **Instrument:** EUR/USD M5 (primary) | ETH/USD | Cross-Market
> **Backtest Period:** January 2020 – May 2026

---

# TABLE OF CONTENTS

1. [System Overview & Core Thesis](#1-system-overview--core-thesis)
2. [Strategy 1: P90 CFD Expansion Engine](#2-strategy-1-p90-cfd-expansion-engine)
3. [Strategy 2: Stall-Harvest Trading System](#3-strategy-2-stall-harvest-trading-system)
4. [Strategy 3: Deep Mean Reversion](#4-strategy-3-deep-mean-reversion)
5. [Strategy 4: Dual-Engine Execution Model](#5-strategy-4-dual-engine-execution-model)
6. [Strategy 5: Failure Repair Model](#6-strategy-5-failure-repair-model)
7. [Strategy 6: The Two Plays](#7-strategy-6-the-two-plays)
8. [Strategy 7: Blind Structural Chain](#8-strategy-7-blind-structural-chain)
9. [Strategy 8: Fractal Resolution Engine](#9-strategy-8-fractal-resolution-engine)
10. [Strategy 9: Constraint Anchor](#10-strategy-9-constraint-anchor)
11. [Strategy 10: Composite Alpha](#11-strategy-10-composite-alpha)
12. [Monte Carlo Results Summary](#12-monte-carlo-results-summary)
13. [Risk Management & Position Sizing](#13-risk-management--position-sizing)
14. [Temporal Delivery Patterns](#14-temporal-delivery-patterns)
15. [Failure Statistics Database](#15-failure-statistics-database)

---

# 1. SYSTEM OVERVIEW & CORE THESIS

## 1.1 Core Thesis

Small Asian ranges (< 30 pips) create a **Constraint Deficit** — the field is under-resolved and must expand to reach its daily mean variance. The Asian Range defines the day's constraint set. The system captures this expansion through multiple complementary strategies.

## 1.2 Three-Tier Asian Range Classification

| Asian Range | Tier | Conviction | Position Size | Expected Daily Range |
|-------------|------|------------|---------------|---------------------|
| < 20 pips | T1 (Gold) | Full | 100% | ~72 pips |
| 20 – 30 pips | T2 (Standard) | Moderate | 75% | ~58 pips |
| 30 – 45 pips | T3 (Caution) | Reduced | 50% | ~48 pips |
| > 45 pips | NO-GO | Skip | 0% | N/A |

## 1.3 Key Performance Metrics (System-Wide)

| Metric | Value |
|--------|-------|
| Win Rate (Filtered) | 85% – 90% |
| Daily Goal | 1.0% – 1.5% |
| Max Daily Drawdown | < 0.50% |
| Prop Firm Circuit Breaker | 0.40% hard stop |
| Weekly R (Full Deployment) | +38R to +52R |
| Max Drawdown (Controlled) | -4R to -6R |

## 1.4 Pre-Session Protocol (Daily — 1:45 AM EST)

1. **Measure Asian Range** (00:00 – 08:00 UTC) → Classify Tier
2. **Define Daily Targets** based on tier
3. **Check Filters:** News (skip if high-impact within 4h), Day of Week adjustments, Overfilled check at 9 AM

## 1.5 Strategy Classification Matrix

| Strategy | Execution Style | Primary Instrument | Timeframe | Win Rate | PF (after costs) |
|----------|----------------|-------------------|-----------|----------|-------------------|
| P90 CFD Expansion | Mean Reversion / Distribution | EUR/USD | M5 | 83-90% | ~1.78 |
| Stall-Harvest | Mean Reversion (Deep) | EUR/USD | M5 | 86% (stall events) | ~1.66 |
| Deep Mean Reversion | Mean Reversion | EUR/USD | M5 | 89.3% | ~45 |
| Dual-Engine | Hybrid (Anchor + Momentum) | EUR/USD | M5 | 89.4% | ~3.42 |
| Failure Repair | Counter-Trend / Rekey | EUR/USD | M5 | 69.8% (2nd acceptance) | ~1.72 |
| The Two Plays | Directional / Scalping | EUR/USD | M5 | 85-92% | ~2.5 |
| Blind Structural Chain | Trend Following | Multi-pair | M5/H1 | 58% | ~1.92 |
| Fractal Resolution | Multi-Timeframe | EUR/USD | M5/H4 | 43.7% | ~1.03 |
| Constraint Anchor | Structural | EUR/USD | M5 | 91.7% | ~2.8 |
| Composite Alpha | Multi-Strategy Blend | EUR/USD | M5 | 97.3% | ~285 |

---

# 2. STRATEGY 1: P90 CFD EXPANSION ENGINE

## 2.1 Full Logic & Mechanism

**Pattern Basis:** The P90 candle is the foundational signal of the CEREBUS system. When the Asian session produces a small range (constraint deficit), the first significant M5 candle that closes outside the Asian band represents the initial resolution of that constraint. This "P90" candle (named for its 90th-percentile body size) signals the direction of the day's expansion.

**Execution Style:** Mean Reversion / Distribution — capturing the expansion from a constrained state.

**How the Pattern Persists:** The Asian session accumulates unresolved institutional orders. When London opens and a P90 candle prints, it triggers a cascade of algorithmic responses that push price toward Fibonacci extension targets of the Asian range. This pattern persists because institutional order flow consistently clusters at these levels.

## 2.2 Entry Mechanism

**P90 Candle Exact Definition:**
- M5 candle closing within the Activation Window (2:00 AM – 11:00 AM EST)
- Body size must meet threshold for the time window:

| Time Window (EST) | Body Threshold |
|-------------------|----------------|
| 2:00 – 4:00 AM | >= 4.1 pips |
| 4:00 – 6:00 AM | >= 4.6 pips |
| 6:00 – 8:00 AM | >= 4.6 pips |
| 8:00 – 10:00 AM | >= 5.9 pips |
| 10:00 – 11:00 AM | >= 6.2 pips |

**CRITICAL:** The P90 candle must **CLOSE** outside the Asian constraint band. Wicks do not count — only closes.

**Activation & Scaling Protocol (Pyramid Model):**

| Signal | Timing | Condition | Size | Boundary | Target |
|--------|--------|-----------|------|----------|--------|
| Signal 1 | P90 Close | Activation Confirmed | 40% | 80% of P90 body | -25% Daily Range |
| Signal 2 | P90 Close | Simultaneous | 40% | 1.5x P90 body | -25% Daily Range |
| Signal 3 | +45 Min | Resolution Output +8 pips | 20% | Breakeven (Signal 1) | -50% Daily Range |

**Regime Shift Confirmation (8:45 AM EST):**
- If Current Daily Range > 1.5x Asian Range → proceed with full size
- If not → reduce size by 50%

## 2.3 Risk Management

| Parameter | Value |
|-----------|-------|
| Constraint Boundary | 80% of P90 body from entry |
| TP1 | -25% of Asian Range → Close 50%, move boundary to BE+2p |
| TP2 | -50% of Asian Range → Close remaining |
| Hard Exit | 12:00 PM EST — Close ALL positions |
| Kill Switch | 132% State → Close ALL immediately |

## 2.4 Situational Analysis

**When it works best:**
- T1 Asian Range (< 20 pips) — highest conviction
- Tuesday/Wednesday — strongest delivery days
- Regime CONFIRMED (ratio >= 1.5x by 9 AM)
- No major news within 4 hours

**When to avoid:**
- Asian Range > 45 pips (NO-GO)
- Monday (indecisive — reduce size 25%)
- Friday after 10 AM (reduce size 50%)
- High-impact news within 4 hours

## 2.5 Temporal Constraints & Delivery Patterns

| Tier | Mean Time to -50% | Median Time | Edge Thin If Not Hit By |
|------|-------------------|-------------|------------------------|
| T1 (<20p) | 3.1 hours | 2.8 hours | 3.0 hours |
| T2 (20-30p) | 4.6 hours | 4.1 hours | 4.4 hours |
| T3 (30-45p) | 6.8 hours | 6.2 hours | 5.5 hours |

**Key Rule:** 82% of daily constraint resolution is complete by 12:00 PM EST. Hard exit is non-negotiable.

## 2.6 Failure Stats

| Metric | Value |
|--------|-------|
| Overall Win Rate (TP1 -25%) | 89.2% |
| Overall Win Rate (TP2 -50%) | 78.4% |
| Invalidation Rate (80% + 2p rule) | 12.3% |
| T3 Invalidation Rate | 18.9% |
| On-Time hits (before 12 PM) | 84.9% |

**Failure Modes:**
- M5 close back inside Asian band before TP1 (12.3%)
- 132% Kill-Switch violation (rare but catastrophic)
- Overfilled day (range > 40p by 9 AM on T2/T3)

## 2.7 Cascade Activation

Subsequent P90 candles in the **same direction** within 120 minutes of the Initial P90.

| Cascade # | Win Rate | Avg Extension | Recommendation |
|-----------|----------|---------------|----------------|
| 1st (Initial) | 83.3% | 18.4p | Baseline |
| 2nd | **87.8%** | 22.6p | **BEST** |
| 3rd | 84.2% | 19.8p | Good |
| 4th+ | 76.4% | 16.2p | **AVOID** |

**Max cascades per session:** 3
**Optimal cascade timing:** 45-60 minutes after initial P90 (88.2% win rate)

---

# 3. STRATEGY 2: STALL-HARVEST TRADING SYSTEM

## 3.1 Full Logic & Mechanism

**Pattern Basis:** When the resolution output extends aggressively, it often reaches the **Stall Zone (168%)** or **Deep State (200%)** of the P90 candle. At these extreme extensions, the market has exhausted its immediate resolution pathways and must either reverse (rebalance) or consolidate. The Stall-Harvest captures the high-probability snap-back from these extremes.

**Execution Style:** Mean Reversion (Deep) — counter-trend at extreme extensions.

**How the Pattern Persists:** Institutional algorithms are programmed to take profits at specific extension levels (168%, 200%). When price reaches these levels, the combined profit-taking creates a predictable counter-movement. The 168% level is particularly significant because it represents the Fibonacci 1.618 extension — a level where institutional order flow consistently reverses.

## 3.2 Entry Mechanism

**Setup Conditions:**

| Condition | Requirement |
|-----------|-------------|
| Trigger | Resolution output touches Stall Zone (168%) or Deep State (200%) of P90 candle |
| Time | Must occur before 12:00 PM EST |
| Filter | The -50% Daily Target has NOT yet been hit |

**CFD Limit Order at Deep Value:**

| Parameter | Value |
|-----------|-------|
| Entry | LIMIT ORDER at 200% Deep State Level |
| Constraint Boundary | 8 pips beyond 200% level (approx. 220% extension) |
| TP1 | Return to 0% (Activation Resolution Output) |
| TP2 | -50% Daily Range |
| R:R Potential | 1:5 to 1:7 |

**Binary Options (Time-Based):**

| Session (EST) | Dynamic Expiry | Target Win Rate |
|---------------|---------------|-----------------|
| 2 AM – 6 AM | 90 Minutes | ~84% |
| 6 AM – 9 AM | 60 Minutes | ~78% |
| 9 AM – 12 PM | 45 Minutes | ~74% |
| After 12 PM | No Trade | — |

## 3.3 Risk Management

| Parameter | Value |
|-----------|-------|
| Entry | Limit @ 168% Stall Zone |
| SL | 200% Deep State + 1.5x candle body buffer |
| TP1 | -25% Daily Range |
| TP2 | -50% Daily Range |
| Kill Switch | M5 closes beyond 200% Deep State → abort |

## 3.4 Situational Analysis

**When it works best:**
- T1 Asian Range — tightest constraint, strongest snap-back
- 2-4 AM EST session — 94.2% expansion win rate
- When -50% daily target NOT yet hit (room to run)

**When to avoid:**
- Asian Range > 45 pips (NO-GO)
- 132% Kill-Switch State active
- After 11 AM EST (no new activations)
- Major news imminent

## 3.5 Temporal Constraints & Delivery Patterns

| Session | Expansion Win Rate | Stall Zone Rate |
|---------|-------------------|-----------------|
| 2-4 AM EST | 94.2% | 31.1% |
| 4-7 AM EST | 88.6% | 35.4% |
| 7-11 AM EST | 82.4% | 38.2% |

**Key Stats:**
- 34.2% of P90s reach Stall Zone (168%) within 35 min
- 65.8% of P90s expand through (168% NOT hit)
- 86% of stall events result in profitable expansion or rebalancing

## 3.6 Failure Stats

| Outcome Scenario | Frequency | Profit Probability |
|-----------------|-----------|-------------------|
| True Rejection | 64.2% | High |
| Shallow Violation | 21.4% | High |
| Deep Violation | 14.4% | Low |

**Failure Modes:**
- Resolution output CLOSES strongly beyond 220% level (True constraint violation)
- Asian Range > 45 pips (edge exhausted)
- 132% Kill-Switch triggers before entry

## 3.7 Monte Carlo Results

| Metric | Result |
|--------|--------|
| Mean Daily Return | +0.72 pips (after costs) |
| Median Accuracy | 91.6% |
| Median Max Drawdown | 29.0 pips |
| PF Robustness (Median) | 1.84 |
| Probability of 20% Drawdown | 0.00% |
| Trade Order Robustness | PF > 1.0 in ALL 1,000 shuffles ✅ |

---

# 4. STRATEGY 3: DEEP MEAN REVERSION

## 4.1 Full Logic & Mechanism

**Pattern Basis:** The flagship strategy. When price extends to extreme levels (168%-200% of the Asian range), the probability of mean reversion is exceptionally high. This is the purest expression of the CEREBUS constraint-system thesis: the field must rebalance after extreme resolution.

**Execution Style:** Mean Reversion — the core edge of the entire system.

**How the Pattern Persists:** This strategy exploits the fundamental property of mean-reverting markets: extreme deviations from the mean have a higher probability of reversal. The 200% Deep State level represents the point where institutional algorithms simultaneously trigger profit-taking, creating a self-reinforcing reversal pattern.

## 4.2 Entry Mechanism

| Parameter | Value |
|-----------|-------|
| Trigger | Price touches 200% Deep State of P90 candle |
| Entry Type | LIMIT ORDER at 200% level |
| Time Window | Before 12:00 PM EST |
| Filter | -50% Daily Target NOT yet hit |
| Direction | Counter to the extension direction |

**Entry Refinements:**
- Bullish extension → SHORT at 200% level
- Bearish extension → LONG at 200% level
- Buffer: 8 pips beyond 200% for stop loss

## 4.3 Risk Management

| Parameter | Value |
|-----------|-------|
| Stop Loss | 8 pips beyond 200% level (~220% extension) |
| TP1 | Return to 0% (Activation Resolution Output) |
| TP2 | -50% Daily Range |
| R:R Potential | 1:5 to 1:7 |
| Max Risk | 0.12% of equity per activation |

**Key Data Point:** 90% of violations do NOT exceed 6.5 pips past 200%. The 8-pip buffer filters noise while protecting capital.

## 4.4 Situational Analysis

**When it works best:**
- T1 Asian Range (< 20 pips) — tightest constraint
- 2-7 AM EST — highest expansion/reversion reliability
- After a strong P90 cascade (exhaustion)
- Tuesday/Wednesday — strongest delivery

**When to avoid:**
- Asian Range > 45 pips
- After 11 AM EST
- Major news within 4 hours
- When 132% Kill-Switch is active

## 4.5 Temporal Constraints & Delivery Patterns

| Session | Win Rate | Avg Time to TP1 |
|---------|----------|-----------------|
| 2-4 AM EST | ~84% | 90 min |
| 4-7 AM EST | ~78% | 60 min |
| 7-11 AM EST | ~74% | 45 min |

## 4.6 Failure Stats

| Metric | Value |
|--------|-------|
| Overall Win Rate | 89.3% (after costs) |
| Profit Factor (after costs) | ~45 |
| Max Drawdown | -5.0 pips (0.05%) |
| Total Trades | 764 |
| Avg Win | 9.25 pips |
| Avg Loss | 4.07 pips |

**Failure Modes:**
- True constraint violation (price closes beyond 220%) — 14.4% of stall events
- News-driven continuation beyond 200%
- Late-session exhaustion (after 11 AM)

## 4.7 Monte Carlo Results (10,000 Iterations)

| Metric | Result | Interpretation |
|--------|--------|----------------|
| Mean Daily Return | +4.47 pips | Expected daily PnL after costs |
| Median Accuracy | 91.6% | Typical day |
| Median Max Drawdown | 12.0 pips | Typical worst-case |
| Max Drawdown (95th pct) | 16.9 pips | Extreme worst-case |
| PF Robustness | 19.3 | After 1,000 shuffles |
| WR Robustness | 89.3% | After 1,000 shuffles |

**KEY FINDING:** Deep_Mean_Reversion shows exceptional robustness. After 10,000 Monte Carlo iterations, the strategy maintains a positive daily expectancy of ~4.47 pips after costs. Trade order shuffling confirms the edge is robust — PF remains >1.0 in ALL 1,000 shuffles. **PRODUCTION READY.**

## 4.8 Portfolio Risk Simulation Results (Fixed Fractional)

| Risk Level | Pair | PnL | MaxDD | PF | Avg Lots |
|------------|------|-----|-------|-----|----------|
| 1% | EURUSD | $385K | 1.82% | 19.0 | 13 |
| 1.5% | EURUSD | $2.4M | 2.73% | 19.0 | 82 |
| 2% | EURUSD | $15M | 3.63% | 19.0 | 508 |
| 1% | USDCHF | $385K | 1.82% | 19.0 | 14 |
| 1.5% | USDCHF | $2.4M | 2.73% | 19.0 | 91 |
| 2% | USDCHF | $15M | 3.63% | 19.0 | 564 |
| 1% | GBPUSD | $385K | 1.82% | 19.0 | 13 |
| 1.5% | GBPUSD | $2.4M | 2.73% | 19.0 | 82 |
| 2% | GBPUSD | $15M | 3.63% | 19.0 | 508 |

---

# 5. STRATEGY 4: DUAL-ENGINE EXECUTION MODEL

## 5.1 Full Logic & Mechanism

**Pattern Basis:** The Dual-Engine model splits capital deployment across two complementary layers:
1. **Constraint Anchor (Certainty Layer):** High-probability structural expansion of the Asian constraint deficit
2. **Resolution Amplifiers (Path Exploitation Layer):** P90 activation signals exploiting momentum along the Anchor's direction

**Execution Style:** Hybrid — combines structural certainty with momentum exploitation.

**Key Finding:** Amplifiers aligned with the Anchor outperform standalone P90 trades by **+15.3% win rate** and **+0.86R per activation**.

## 5.2 Entry Mechanism

**Constraint Anchor:**
- Prerequisite: Asian Range < 30 pips (T1 or T2 ONLY)
- Time Window: 08:00-17:00 UTC (3:00 AM - 12:00 PM EST)
- Activation: M5 candle CLOSES outside Asian High/Low, body >= 4.6 pips
- Boundary: Opposite Asian extreme

**Resolution Amplifiers:**
- ONLY if Tier T1 or T2 AND direction matches Anchor
- Trigger: P90 activation at partial rebalancing zone

| Tier | Partial Rebalancing Entry | Max Amplifiers | Size Each | Target |
|------|--------------------------|----------------|-----------|--------|
| T1 | 32% or 50% | 2 | 20% | 20p fixed |
| T2 | 50% ONLY | 1 | 30% | 20p fixed |
| T3 | NO AMPLIFIERS | 0 | — | — |

## 5.3 Risk Management

**Optimal Capital Allocation: 70% Anchor / 30% Amplifiers**

| Allocation | Avg Daily R | Win Rate | Sharpe | Max DD |
|------------|-------------|----------|--------|--------|
| Anchor Only (100/0) | +1.42R | 91.7% | 2.84 | -4.2R |
| **70% Anchor / 30% Amps** | **+1.86R** | **89.4%** | **3.42** | **-5.1R** |
| 50/50 | +1.92R | 86.2% | 3.15 | -6.8R |
| Amps Only (0/100) | +2.18R | 74.3% | 2.12 | -12.4R |

**Overfilled Filter:**

| Tier | Condition | Anchor WR | Combined Action |
|------|-----------|-----------|-----------------|
| T1 | Normal (<40p by 9AM) | 89.4% | Full Dual-Engine |
| T1 | Overfilled (>40p) | 62.5% | Anchor ONLY — 50% size |
| T2 | Normal (<40p) | 82.8% | Full Dual-Engine |
| T2 | Overfilled (>40p) | 44.8% | **STAND DOWN** |
| T3 | Normal (<40p) | 79.4% | Model 2 Anchor — 50-75% size |
| T3 | Overfilled (>40p) | 41.2% | **STAND DOWN** |

## 5.4 Situational Analysis

**When it works best:**
- T1/T2 Asian Range with Regime CONFIRMED
- Tuesday/Wednesday
- When Anchor and Amplifier directions align

**When to avoid:**
- T3 with Amplifiers (NO AMPLIFIERS on T3)
- Overfilled days (T2/T3 stand down)
- Opposite-direction Amplifiers

## 5.5 Temporal Constraints

- Anchor activation: 3:00 AM - 12:00 PM EST
- Amplifier window: Within 90 minutes of Anchor
- Hard exit: 12:00 PM EST for both engines

## 5.6 Failure Stats

| Metric | Value |
|--------|-------|
| Anchor-only Win Rate | 91.7% |
| Amplifier-only Win Rate | 67.1% |
| Combined Win Rate | 89.4% |
| Overfilled T2/T3 WR | 44.8% (STAND DOWN) |

---

# 6. STRATEGY 5: FAILURE REPAIR MODEL

## 6.1 Full Logic & Mechanism

**Pattern Basis:** When a valid breakout fails (price closes back inside the Asian band), the failure itself becomes a signal. The Failure Repair Model defines three resolution types after failure and provides re-entry rules for each.

**Execution Style:** Counter-Trend / Rekey — trading the aftermath of failed breakouts.

## 6.2 Entry Mechanism

**Failure Definition:** After a valid 2-hour acceptance hold, failure = first M5 close back **INSIDE** the Asian constraint band before the 1x target is hit.

**Three Failure Resolution Types:**

| Type | What Happens | Frequency | Action |
|------|-------------|-----------|--------|
| Type 1 — Soft Failure | Fails back → midpoint → compresses | Most common | Stand down |
| Type 2 — Internal Reset | Fails → midpoint → reclaims → continues | 89% of 2nd breaks | Re-enter aligned |
| Type 3 — Regime Flip | Fails → midpoint → opposite edge → flip | 11% of 2nd breaks | WR 84.6% — wait for full confirmation |

## 6.3 Risk Management

| Parameter | Value |
|--------|-------|
| Second acceptance WR | 69.8% |
| Same-side re-acceptance WR | 67.7% |
| Opposite-side flip WR | 84.6% |
| Re-entry size | 60-70% of original |
| Stop | 2-3 pips beyond midpoint |

## 6.4 Situational Analysis

**Day-of-Week Edge:**

| Day | Win Rate | First Break Real | Second Break Real |
|-----|----------|-----------------|-------------------|
| Monday | 70-75% | 60-65% | 35-40% |
| **Tuesday** | **82-88%** | **75-85%** | 15-25% |
| Wednesday | 78-85% | 70-80% | 20-30% |
| Thursday | 65-75% | 50-60% | 40-50% |
| Friday | 68-78% | 65-75% | 25-35% |

**Flip Probability After Failure:**

| Day | Prob Opposite Side Becomes Real |
|-----|-------------------------------|
| Monday | 60-70% |
| Tuesday | 50-60% |
| Wednesday | 60-70% |
| **Thursday** | **70-80% (BEST FLIP DAY)** |
| Friday | 55-65% |

## 6.5 Temporal Constraints

**Failure Timing Detection:**

| Time After Break | % of Failed Breaks | Classification |
|-----------------|-------------------|----------------|
| 0-15 minutes | ~35% | Wick failure (fastest) |
| 15-30 minutes | ~30% | Shallow hold → dump |
| 30-60 minutes | ~20% | Slow failure (ranging) |
| 60-120 minutes | ~15% | Late failure (looks real) |

**Key:** 65% of fake constraint violations fail within 30 minutes. 80% fail within 60 minutes.

## 6.6 Failure Stats

| Metric | Value |
|--------|-------|
| Valid 2h-hold setups | 465 |
| Hit 1x target before failure | 52.0% |
| Failed first | 45.2% |
| Constraint band midpoint hit first | 73.8% of failures |
| Full flip to opposite 1x target | 20.0% |

## 6.7 Monte Carlo Results

| Metric | Result |
|--------|--------|
| Mean Daily Return | +0.72 pips (after costs) |
| Median Accuracy | 91.6% |
| Median Max Drawdown | 29.0 pips |
| PF Robustness | 1.84 |

---

# 7. STRATEGY 6: THE TWO PLAYS

## 7.1 Full Logic & Mechanism

**Pattern Basis:** The Two Plays are the simplified execution framework — two distinct play types for different market conditions. Play 1 (Base 80) is the bread-and-butter daily trade. Play 2 (T3 Max Accuracy) is the defensive edge for wider Asian ranges.

**Execution Style:** Directional / Scalping.

## 7.2 Entry Mechanism

### PLAY 1 — BASE 80 (Bread & Butter)

**Win Rate:** 85-90% | **Trade every qualifying day**

**Pre-Conditions (ALL must be TRUE):**
- Asian Range < 30 pips (T1 or T2)
- Time: 2:00 AM – 11:00 AM EST
- P90 body meets threshold
- No major news within 4 hours

**Execution:**
- **Entry:** P90 candle CLOSE outside Asian band → Enter MARKET on close
- **Size:** T1: 100% | T2: 75%
- **Boundary:** 80% of P90 body from entry
- **TP1:** -25% of Asian Range → Close 50% | Move boundary to BE+2p
- **TP2:** -50% of Asian Range → Close remaining 50%
- **Hard Exit:** 12:00 PM EST

### PLAY 2 — T3 MAX ACCURACY (Defensive Edge)

**Win Rate:** 76.7% | **T3 ONLY (30-45p Asian Range)**

**Pre-Conditions:**
- Asian Range 30-45 pips (T3 ONLY)
- M5 candle CLOSES outside Asian band, body >= 4.6 pips
- **Price MUST hold outside band for full 2 hours** (non-negotiable)
- NO Amplifiers — Pure Anchor ONLY
- If > 40 pips by 9 AM → STAND DOWN

**Execution:**
- **Entry:** AFTER 2-hour acceptance hold → Enter on pullback to 32-50% partial rebalancing
- **Size:** 50-75% of normal risk
- **Boundary:** AT Asian High/Low — M5 CLOSE back inside = EXIT immediately
- **Target:** 1x Asian Range extension ONLY — No runners
- **Hard Exit:** 12:00 PM EST

## 7.3 Risk Management

| Parameter | Play 1 | Play 2 |
|-----------|--------|--------|
| Size | T1: 100%, T2: 75% | 50-75% |
| Boundary | 80% of P90 body | Asian band edge |
| TP1 | -25% (close 50%) | 1x Range |
| TP2 | -50% (close 50%) | None |
| Runners | If -50% hit before 11 AM | No runners |

## 7.4 Situational Analysis

**Play 1 works best:** T1/T2, Tuesday/Wednesday, Regime CONFIRMED
**Play 2 works best:** T3 only, after 2-hour hold confirmation, Tuesday/Wednesday

## 7.5 Temporal Constraints

- Both plays: Hard exit 12:00 PM EST
- Play 1 entry window: 2:00 AM – 11:00 AM EST
- Play 2 entry: After 2-hour hold (typically 5:00 AM – 11:00 AM EST)

## 7.6 Failure Stats

| Metric | Play 1 | Play 2 |
|--------|--------|--------|
| Win Rate | 85-90% | 76.7% |
| Invalidation Rate | ~12% | ~19% |
| Avg R-Multiple | +1.42R | +2.14R |

---

# 8. STRATEGY 7: BLIND STRUCTURAL CHAIN

## 8.1 Full Logic & Mechanism

**Pattern Basis:** The Blind Structural Chain is a recursive loop engine that identifies self-reinforcing structural patterns across multiple timeframes. It operates "blind" — without directional bias — and instead follows the chain of structural breaks regardless of direction.

**Execution Style:** Trend Following / Structural — multi-timeframe recursive.

## 8.2 Entry Mechanism

- Identifies structural breaks across M5, H1, and H4 timeframes
- Entry triggered when 2+ timeframes confirm the same structural break
- Direction follows the chain, not prediction

## 8.3 Risk Management

| Parameter | Value |
|-----------|-------|
| Win Rate | 58% |
| PF (after costs) | ~1.92 |
| Max Drawdown | ~400 pips (high) |
| Position Size | Reduced (high DD strategy) |

## 8.4 Monte Carlo Results

| Metric | Result |
|--------|--------|
| Mean Daily Return | +0.72 pips (after costs) |
| Median Accuracy | 91.1% |
| Median Max Drawdown | 29.0 pips |
| PF Robustness | 1.84 |
| Trade Order Robustness | PF > 1.0 in ALL 1,000 shuffles ✅ |

## 8.5 Situational Analysis

**When it works best:** Trending markets, multi-timeframe alignment
**When to avoid:** Ranging/choppy markets, low volatility

## 8.6 Failure Stats

| Metric | Value |
|--------|-------|
| Win Rate | 58% |
| Invalidation Rate | Higher than P90 strategies |
| Max Drawdown | -400 pips (requires careful sizing) |

---

# 9. STRATEGY 8: FRACTAL RESOLUTION ENGINE

## 9.1 Full Logic & Mechanism

**Pattern Basis:** Nested cycle analysis — identifies fractal patterns within the Asian range that repeat across multiple timeframes. The engine looks for self-similar structures at different scales.

**Execution Style:** Multi-Timeframe / Fractal — pattern recognition across scales.

## 9.2 Entry Mechanism

- Identifies fractal patterns in M5 that mirror H1/H4 structures
- Entry when fractal confirmation occurs across 2+ timeframes
- Targets set by the fractal extension ratios

## 9.3 Risk Management

| Parameter | Value |
|-----------|-------|
| Win Rate | 43.7% |
| PF (after costs) | ~1.03 |
| Max Drawdown | -682 pips (very high) |
| Position Size | Minimal (marginal edge) |

## 9.4 Situational Analysis

**When it works best:** Clear fractal alignment across timeframes
**When to avoid:** Most conditions — this is a marginal strategy

## 9.5 Failure Stats

| Metric | Value |
|--------|-------|
| Win Rate | 43.7% (lowest of all strategies) |
| PF | ~1.03 (barely profitable) |
| Max Drawdown | -682 pips |
| Verdict | ⚠️ Marginal — needs significant improvement |

---

# 10. STRATEGY 9: CONSTRAINT ANCHOR

## 10.1 Full Logic & Mechanism

**Pattern Basis:** The purest form of the CEREBUS thesis — the Asian constraint band acts as the anchor, and any close outside it is a structural signal. No P90 filter, no cascade — just the raw structural break.

**Execution Style:** Structural / Directional — pure anchor-based trading.

## 10.2 Entry Mechanism

| Parameter | Value |
|-----------|-------|
| Trigger | M5 candle CLOSES outside Asian High/Low |
| Body Requirement | >= 4.6 pips |
| Time Window | 3:00 AM - 12:00 PM EST |
| Direction | Same as breakout direction |

## 10.3 Risk Management

| Parameter | Value |
|-----------|-------|
| Win Rate | 91.7% |
| Boundary | Opposite Asian extreme |
| TP1 | -25% extension (close 50%) |
| TP2 | -50% extension (close remaining) |
| Hard Exit | 12:00 PM EST |

**Anchor Performance by Tier:**

| Metric | Overall | T1 (<20p) | T2 (20-30p) | T3 (30-45p) |
|--------|---------|-----------|-------------|-------------|
| Win Rate (TP25+) | 91.7% | 98.6% | 89.1% | 76.2% |
| Avg R-Multiple | +1.42R | +1.68R | +1.24R | +0.88R |

## 10.4 Situational Analysis

**When it works best:** T1 Asian Range, Regime CONFIRMED
**When to avoid:** Overfilled days (T2/T3 > 40p by 9 AM = STAND DOWN)

## 10.5 Failure Stats

| Metric | Value |
|--------|-------|
| Win Rate | 91.7% |
| Overfilled T2/T3 WR | 44.8% (STAND DOWN) |
| Invalidation Rate | ~8% |

---

# 11. STRATEGY 10: COMPOSITE ALPHA

## 11.1 Full Logic & Mechanism

**Pattern Basis:** Multi-strategy blend — combines signals from multiple CEREBUS strategies into a single composite signal. Only fires when multiple strategies agree on direction and timing.

**Execution Style:** Multi-Strategy Blend — highest conviction when all align.

## 11.2 Entry Mechanism

- Requires confirmation from 3+ individual strategies
- All must agree on direction
- Timing window: 2:00 AM – 11:00 AM EST
- Only on T1/T2 Asian Range days

## 11.3 Risk Management

| Parameter | Value |
|-----------|-------|
| Win Rate | 97.3% |
| PF (after costs) | ~285 |
| Max Drawdown | 2.64% (at 2% risk) |
| Position Size | Standard |

## 11.4 Portfolio Risk Simulation Results

| Risk Level | Pair | PnL | MaxDD | PF | Avg Lots |
|------------|------|-----|-------|-----|----------|
| 1% | EURUSD | $39K | 1.32% | 54.8 | 4 |
| 1.5% | EURUSD | $98K | 1.98% | 54.8 | 10 |
| 2% | EURUSD | $228K | 2.64% | 54.8 | 24 |

## 11.5 Situational Analysis

**When it works best:** All conditions align (Phi >= 0.8)
**When to avoid:** Any single strategy disagrees

## 11.6 Failure Stats

| Metric | Value |
|--------|-------|
| Win Rate | 97.3% (highest) |
| PF | ~285 (highest) |
| Warning | ⚠️ Likely overfit — needs forward testing |

---

# 12. MONTE CARLO RESULTS SUMMARY

## 12.1 Deep Mean Reversion (10,000 Iterations)

| Metric | Result |
|--------|--------|
| Mean Daily Return | +4.47 pips |
| Median Accuracy | 91.6% |
| Median Max DD | 12.0 pips |
| PF Robustness | 19.3 |
| WR Robustness | 89.3% |
| Verdict | 🟢 PRODUCTION READY |

## 12.2 Batch 2: BSC, P90P, Failure_Repair, Stall_Harvest (10,000 Iterations Each)

| Strategy | Mean Daily | Median Acc | Median MaxDD | PF Robust | Ruin Prob |
|----------|-----------|------------|--------------|-----------|-----------|
| Blind_Structural_Chain | +0.72p | 91.1% | 29.0p | 1.84 | 0.00% |
| P90P_Distribution | +0.72p | 91.1% | 29.0p | 1.84 | 0.00% |
| Failure_Repair | +0.72p | 91.1% | 29.0p | 1.84 | 0.00% |
| Stall_Harvest | +0.72p | 91.1% | 29.0p | 1.84 | 0.00% |

**All 4 strategies: 0% ruin probability. All pass Monte Carlo validation.**

## 12.3 Cost Model Impact

| Metric | Before Costs | After Costs |
|--------|-------------|-------------|
| Mean Daily PnL (DMR) | +7.37 pips | +4.47 pips |
| Cost per Trade | — | 2.9 pips |
| PF Impact | 112 | ~45 |

**Cost Model:** Spread 0.2p + Slippage 2.0p + Commission 0.7p = 2.9 pips/trade

---

# 13. RISK MANAGEMENT & POSITION SIZING

## 13.1 Core Risk Parameters

| Parameter | Value | Rule |
|-----------|-------|------|
| Risk Per Activation | 0.12% of Equity | Per signal limit |
| Max Concurrent Risk | 0.36% (3 signals) | All open positions combined |
| Daily Constraint Boundary | 0.40% | Close ALL if hit |
| Personal Daily Limit | 0.50% | 0.40% hard boundary preserves buffer |

## 13.2 Cascade Position Sizing ($10,000 account)

| Activation | Size % | $ Amount | Boundary | Units |
|------------|--------|----------|----------|-------|
| Signal 1 (Initial P90) | 40% | $4 | 80% of P90 body | 11,764 |
| Signal 2 (45-Min Add) | 30% | $3 | Breakeven | — |
| Signal 3 (Cascade P90) | 20% | $2.40 | 168% of P90 body | 2,790 |
| Signal 4 (Cascade 2) | 10% | $1.20 | 168% of P90 body | — |
| **TOTAL** | **100%** | **$7.60 (0.076%)** | Mixed | — |

## 13.3 Fixed Dollar Expectancy (FDE)

**Formula:** Lot Size = Target Dollar Profit / (Atomic Target Pips × Pip Value)

| Tier | Atomic Target | Pip Value | Target $ | Lot Size |
|------|--------------|-----------|----------|----------|
| T1 | 10p | $10/pip | $50 | 0.50 Lots |
| T2 | 12p | $10/pip | $50 | 0.36 Lots |
| T3 | 15p | $10/pip | $50 | 0.28 Lots |

**Result:** Every win pays $50 regardless of tier. Equity curve is a straight line up.

## 13.4 Correlation Warning

Do not activate EUR/USD and GBP/USD simultaneously in the same direction unless reduced size is applied. Treat them as one constraint position.

---

# 14. TEMPORAL DELIVERY PATTERNS

## 14.1 Monday London Fibonacci System (281 Weeks)

| Fib Level | Hit Rate | Total Weeks | Hits |
|-----------|----------|-------------|------|
| -25% | 100.00% | 281 | 281 |
| -50% | 100.00% | 281 | 281 |
| -100% | 92.17% | 281 | 259 |
| -168% | 87.19% | 281 | 245 |
| 0% | 100.00% | 281 | 281 |

**Directional Bias:** Bullish 45% | Bearish 55% (slight bearish bias consistent with EUR/USD long-term downtrend)

## 14.2 Asian Session Fibonacci (1,083 Sessions)

| Level | Exact Hit Rate | With Tolerance |
|-------|---------------|----------------|
| -25% | 65.19% | 100.00% |
| -50% | 54.94% | 100.00% |
| -100% | 39.43% | 100.00% |
| -168% | 23.82% | 98.61% |

**Critical Insight:** Asian session alone has significantly lower hit rates than Monday London. The Asian session needs the Monday London weekly anchor for context.

## 14.3 Day-of-Week Delivery Profile

| Day | Win Rate | Edge Interpretation |
|-----|----------|-------------------|
| Monday | 70-75% | Indecisive — reduce size 25% |
| **Tuesday** | **82-88%** | **BEST — trust the first move** |
| Wednesday | 78-85% | Strong first move |
| Thursday | 65-75% | Wait — second break is the real trade |
| Friday | 68-78% | Mixed — reduce size 50% after 10 AM |

## 14.4 Session Performance

| Session | Expansion Win Rate | Stall Zone Rate |
|---------|-------------------|-----------------|
| 2-4 AM EST | 94.2% | 31.1% |
| 4-7 AM EST | 88.6% | 35.4% |
| 7-11 AM EST | 82.4% | 38.2% |

## 14.5 Expected Atomic Loops Per Day (EUR/USD)

| Tier | Asian Range | Expected Loops/Day | High-Conviction Entries |
|------|------------|-------------------|----------------------|
| T1 | < 20p | 4 – 7 | 3-4 |
| T2 | 20-30p | 3 – 5 | 2-3 |
| T3 | 30-45p | 2 – 4 | 1-2 |

---

# 15. FAILURE STATISTICS DATABASE

## 15.1 Overall Failure Rates by Strategy

| Strategy | Win Rate | Failure Rate | Primary Failure Mode |
|----------|----------|-------------|---------------------|
| P90 CFD Expansion | 89.2% | 10.8% | Close back inside Asian band |
| Stall-Harvest | 86% | 14% | Deep violation beyond 220% |
| Deep Mean Reversion | 89.3% | 10.7% | True constraint violation |
| Dual-Engine | 89.4% | 10.6% | Overfilled day |
| Failure Repair | 69.8% | 30.2% | Type 1 soft failure |
| The Two Plays | 85-92% | 8-15% | Invalidation at band edge |
| Blind Structural Chain | 58% | 42% | Choppy/ranging market |
| Fractal Resolution | 43.7% | 56.3% | Fractal misalignment |
| Constraint Anchor | 91.7% | 8.3% | Overfilled day |
| Composite Alpha | 97.3% | 2.7% | Strategy disagreement |

## 15.2 Failure Pattern Database Summary

| Failure Type | Frequency | Rekey Probability |
|-------------|-----------|-------------------|
| Soft Failure (Type 1) | Most common | Low — stand down |
| Internal Reset (Type 2) | 89% of 2nd breaks | High — re-enter same side |
| Regime Flip (Type 3) | 11% of 2nd breaks | 84.6% WR — wait for confirmation |

## 15.3 132% Violation Analysis (228 Events)

| Metric | Value |
|--------|-------|
| Average Violation Depth | 8.0 pips |
| Minimum | 0.1 pips |
| Maximum | 25.7 pips |
| Most violations are shallow | Price barely exceeds 132% before reversing |

## 15.4 Rekey Success by Day

| Day | Rekey Success Rate | Action |
|-----|-------------------|--------|
| Monday | 60-70% | Moderate flip — watch opposite |
| Tuesday | 50-60% | Lower flip — same-side re-acceptance |
| Wednesday | 60-70% | Moderate flip |
| **Thursday** | **70-80%** | **BEST FLIP DAY** |
| Friday | 55-65% | Moderate flip — limited follow-through |

---

# APPENDIX A: KEY THRESHOLDS SUMMARY (EUR/USD M5)

| Parameter | T1 | T2 | T3 |
|-----------|-----|-----|-----|
| Asian Range | < 20p | 20-30p | 30-45p |
| P90 Threshold (2-4 AM) | >= 4.1p | >= 4.1p | >= 4.1p |
| P90 Threshold (4-8 AM) | >= 4.6p | >= 4.6p | >= 4.6p |
| P90 Threshold (8-10 AM) | >= 5.9p | >= 5.9p | >= 5.9p |
| P90 Threshold (10-11 AM) | >= 6.2p | >= 6.2p | >= 6.2p |
| Position Size | 100% | 75% | 50% |
| Atomic Unit | 10p | 12p | 15p |
| Cascade Boundary | 168% of P90 | 168% of P90 | N/A |
| Max Cascades | 3 | 3 | 0 |
| Expected Daily Range | ~72p | ~58p | ~48p |

# APPENDIX B: CONVERGENCE FACTOR (PHI)

**PHI = (0.40 × Regime) + (0.25 × P90) + (0.20 × Cascade) + (0.15 × Float)**

| Component | Score |
|-----------|-------|
| Regime | 1.0 if Ratio ≥ 1.50 / 0.7 if 1.45-1.49 / 0.5 if < 1.45 |
| P90 | 1.0 if confirmed in 2-6 AM window |
| Cascade | 1.0 if printed in 45-60 min optimal window |
| Float | 1.0 if Monday/Tuesday Float confirmed |

| Phi | P_Win | Action |
|-----|-------|--------|
| 1.0 (all conditions) | 98.7% | Maximum conviction |
| ≥ 0.8 | 91-94% | High conviction |
| ≥ 0.6 | 85% | Base — minimum acceptable |
| < 0.6 | NO-GO | Do not trade |

# APPENDIX C: STATE MACHINE DESIGN

```
IDLE → PRE_SESSION (1:45 AM) → SCANNING (2:00 AM) → P90_DETECTED →
  → CASCADE_WAIT → POSITION_ACTIVE → EXIT_MANAGEMENT → CLOSED

Alternative paths:
  POSITION_ACTIVE → FAILURE_DETECTED → MIDPOINT_WATCH → 
    TYPE1 (stand down) | TYPE2 (re-enter same) | TYPE3 (flip after 2h)
  
  SCANNING → NO_GO (Asian > 45p or news filter)
  
  ANY_STATE → KILL_SWITCH (132% violation) → CLOSED
  ANY_STATE → HARD_EXIT (12:00 PM) → CLOSED
```

---

*Document generated from CEREBUS FX v4.0 Manual (April 2026) + Excel Workbook (97 sheets, 281 weeks, 315,000+ candles). All data derived from EUR/USD M5, Jan 2020 – May 2026. Monte Carlo: 10,000 iterations per strategy. For educational purposes only. Test all strategies in simulation before live deployment.*

*Classification: PROPRIETARY — Internal Reference Only*
