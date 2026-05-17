# CEREBUS FX — Complete Strategy Analysis

> **Source:** CEREBUS Manual v4.0 (April 2026) | EUR/USD M5 | 315,000+ Candles | Jan 2022 – Apr 2026
> **Data Period:** 1,098 trading days | 4,842 signals processed | 201 weeks float analysis | 648 days daily float analysis
> **Classification:** PROPRIETARY — For educational purposes only

---

## Table of Contents

1. [System Overview & Core Thesis](#1-system-overview--core-thesis)
2. [Pre-Session Protocol](#2-pre-session-protocol)
3. [Strategy A: CFD Expansion Engine (P90 Core)](#3-strategy-a-cfd-expansion-engine-p90-core)
4. [Strategy B: Deep Mean Rebalancing (Stall-Harvest)](#4-strategy-b-deep-mean-rebalancing-stall-harvest)
5. [Stall-Harvest Trading System](#5-stall-harvest-trading-system)
6. [Dual-Engine Execution Model](#6-dual-engine-execution-model)
7. [Failure Repair Model](#7-failure-repair-model)
8. [The Two Plays — Final Execution Framework](#8-the-two-plays--final-execution-framework)
9. [Daily Setups 1-6](#9-daily-setups-1-6)
10. [Atomic Market Structure](#10-atomic-market-structure)
11. [Risk Management & Position Sizing](#11-risk-management--position-sizing)
12. [Implementation Notes for Nautilus Trader](#12-implementation-notes-for-nautilus-trader)

---

## 1. System Overview & Core Thesis

### Core Thesis
Small Asian ranges (< 30 pips) create a **Constraint Deficit** — the field is under-resolved and must expand to reach its daily mean variance. The Asian Range defines the day's constraint set. The system captures this expansion.

### Key Performance Metrics

| Metric | Value |
|--------|-------|
| Win Rate (Filtered) | 85% – 90% |
| Daily Goal | 1.0% – 1.5% |
| Max Daily Drawdown | < 0.50% |
| Prop Firm Circuit Breaker | 0.40% hard stop |
| Weekly R (Full Deployment) | +38R to +52R |
| Max Drawdown (Controlled) | -4R to -6R |

### Three-Tier Asian Range Classification

| Asian Range | Tier | Conviction | Position Size | Expected Daily Range |
|-------------|------|------------|---------------|---------------------|
| < 20 pips | T1 (Gold) | Full | 100% | ~72 pips |
| 20 – 30 pips | T2 (Standard) | Moderate | 75% | ~58 pips |
| 30 – 45 pips | T3 (Caution) | Reduced | 50% | ~48 pips |
| > 45 pips | NO-GO | Skip | 0% | N/A |

---

## 2. Pre-Session Protocol

**Time:** 1:45 AM EST (Daily)

### Step 1: Measure Asian Range
- **Window:** 00:00 – 08:00 UTC (7:00 PM – 3:00 AM EST)
- Calculate: Asian High – Asian Low = Constraint Deficit
- Classify Tier (T1/T2/T3/NO-GO)

### Step 2: Define Daily Targets
- T1: Target Daily Range ≈ 72 pips
- T2: Target Daily Range ≈ 58 pips
- T3: Target Daily Range ≈ 48 pips

### Step 3: Check Filters
- **News:** High-impact news (NFP, CPI, FOMC) within 4 hours → **SKIP DAY**
- **Day of Week:** Monday → reduce size 25%. Friday → reduce size 50% after 10 AM.
- **Overfilled Check (9 AM):** If daily range > 40 pips by 9 AM EST → T1: Anchor only at 50% size; T2/T3: **STAND DOWN**

---

## 3. Strategy A: CFD Expansion Engine (P90 Core)

**Reference:** Part 1, Pages 5-9 | Part 2, Pages 10-15 | Part 3, Pages 16-19

### 3.1 P90 Candle — Exact Definition

A **P90 candle** is an M5 candle that closes within the **Activation Window** (2:00 AM – 11:00 AM EST) meeting the following body-size threshold:

| Time Window (EST) | Bullish/Bearish Threshold |
|-------------------|--------------------------|
| 2:00 – 4:00 AM | >= 4.1 pips |
| 4:00 – 6:00 AM | >= 4.6 pips |
| 6:00 – 8:00 AM | >= 4.6 pips |
| 8:00 – 10:00 AM | >= 5.9 pips |
| 10:00 – 11:00 AM | >= 6.2 pips |

**Key Rule:** The P90 candle must **CLOSE** outside the Asian constraint band (above Asian High for LONG, below Asian Low for SHORT). Wicks do not count — only closes.

### 3.2 Activation & Scaling Protocol (Pyramid Model)

| Signal | Timing | Condition | Size | Constraint Boundary | Target |
|--------|--------|-----------|------|-------------------|--------|
| Signal 1 | P90 Close | Activation Confirmed | 40% | 80% of P90 body | -25% Daily Range |
| Signal 2 | P90 Close | Simultaneous | 40% | 1.5x P90 body | -25% Daily Range |
| Signal 3 | +45 Min | Resolution Output +8 pips | 20% | Breakeven (Signal 1) | -50% Daily Range |

**Regime Shift Confirmation (8:45 AM EST):**
- If Current Daily Range > 1.5x Asian Range → proceed with full size
- If not → reduce size by 50%

### 3.3 Cascade Activation Rules

**Definition:** Subsequent P90 candles in the **same direction of constraint resolution** within 120 minutes of the Initial P90.

| Cascade # | Win Rate | Avg Extension | Constraint Boundary | Recommendation |
|-----------|----------|---------------|-------------------|----------------|
| 1st (Initial) | 83.3% | 18.4p | 80% of P90 body | Baseline |
| 2nd | **87.8%** | 22.6p | 168% of THIS P90 body | **BEST** |
| 3rd | 84.2% | 19.8p | 168% of THIS P90 body | Good |
| 4th+ | 76.4% | 16.2p | — | **AVOID** |

**Max cascades per session:** 3

**Optimal cascade timing:** 45-60 minutes after initial P90 (88.2% win rate)

**Cascade filters:**
- ✅ Same direction of constraint resolution
- ✅ Within 90 minutes of Initial P90
- ✅ Before 11:00 AM EST
- ✅ Asian Range < 45 pips
- ❌ Opposite direction = IGNORE
- ❌ After 90 minutes = reduce size or skip
- ❌ 4th+ cascade = resolution exhausted

### 3.4 Exit Management

| Exit Condition | Action |
|---------------|--------|
| TP1 (-25% of Asian Range) | Close 50% of total position. Move constraint boundaries to Breakeven. |
| TP2 (-50% of Asian Range) | Close remaining core positions. |
| Hard Exit (12:00 PM EST) | Close ALL positions — 82% of daily constraint resolution complete. |
| Kill Switch (132% State) | Resolution output violates 132% of Asian Range → Close ALL immediately. |

### 3.5 Runner Protocol (if Asian -50% Target hit before 11:00 AM)

| Asian Size | Expected Daily Avg | Current Move (-50%) | Remaining Potential | Action |
|------------|-------------------|--------------------|--------------------|--------|
| < 20 pips | ~72 pips | ~10 pips | ~60 pips left | Hold Runner to Daily -50% |
| 20-30 pips | ~58 pips | ~15 pips | ~40 pips left | Trail Boundary to Daily -25% |
| > 30 pips | ~48 pips | ~24 pips | ~20 pips left | Take Profit — Edge thinning |

**Runner Rules:**
1. Close 50% at Asian -50% target
2. Move Constraint Boundary to Breakeven + 2 pips
3. Target Daily -50% (calculated from Asian High/Low constraint violation)
4. Hard Exit: 12:00 PM EST

---

## 4. Strategy B: Deep Mean Rebalancing (Stall-Harvest)

**Reference:** Part 1, Pages 6-8 | Part 4, Pages 20-29

### 4.1 The Logic
When the resolution output extends aggressively, it often reaches the **Stall Zone (168%)** or **Deep State (200%)** of the P90 candle to harvest available resolution pathways before rebalancing. This creates a high-probability partial rebalancing snap-back opportunity.

### 4.2 Setup Conditions

| Condition | Requirement |
|-----------|-------------|
| Trigger | Resolution output touches Stall Zone (168%) or Deep State (200%) of P90 candle |
| Time | Must occur before 12:00 PM EST |
| Filter | The -50% Daily Target has NOT yet been hit |

### 4.3 Execution — CFD Limit Order at Deep Value

| Parameter | Value |
|-----------|-------|
| Entry | LIMIT ORDER at 200% Deep State Level |
| Constraint Boundary | 8 pips beyond 200% level (approx. 220% extension) |
| TP1 | Return to 0% (Activation Resolution Output) |
| TP2 | -50% Daily Range |
| R:R Potential | 1:5 to 1:7 |

**Rationale:** Data shows 90% of violations do NOT exceed 6.5 pips past 200%. The 8-pip buffer filters noise while protecting capital.

### 4.4 Execution — Binary Options (Time-Based)

| Session (EST) | Dynamic Expiry | Target Win Rate |
|---------------|---------------|-----------------|
| 2 AM – 6 AM | 90 Minutes | ~84% (early session) |
| 6 AM – 9 AM | 60 Minutes | ~78% |
| 9 AM – 12 PM | 45 Minutes | ~74% |
| After 12 PM | No Trade | — |

**Direction:** Same as the direction of constraint resolution if Regime Shift confirmed. Counter-direction if resolution momentum is exhausted.

### 4.5 When to AVOID the Rebalancing Play
- Resolution output CLOSES strongly beyond 220% level (True constraint violation)
- Major news is imminent
- Asian Range was > 45 pips (constraint deficit too wide — edge exhausted)

---

## 5. Stall-Harvest Trading System

**Reference:** Part 4, Pages 20-29

### 5.1 The 168% Stall Zone Mechanism

| Outcome Scenario | Frequency | Profit Probability |
|-----------------|-----------|-------------------|
| True Rejection | 64.2% | High |
| Shallow Violation | 21.4% | High |
| Deep Violation | 14.4% | Low |

**Key Stats:**
- 34.2% of P90s reach Stall Zone State (168%) within 35 min
- 65.8% of P90s expand through (168% NOT hit — resolution continues)
- 86% of stall events result in profitable expansion or rebalancing

### 5.2 Session Performance

| Session | Expansion Win Rate | Stall Zone Rate |
|---------|-------------------|-----------------|
| 2-4 AM EST | 94.2% | 31.1% |
| 4-7 AM EST | 88.6% | 35.4% |
| 7-11 AM EST | 82.4% | 38.2% |

### 5.3 CFD Execution Protocol

| Step | Action | Detail |
|------|--------|--------|
| 1. LIMIT ACTIVATION | 168% Stall Zone | Bullish: Low – (Body × 1.68) / Bearish: High + (Body × 1.68) |
| 2. BOUNDARY PLACEMENT | 200% Deep State | SL at 200%; Buffer = 1.5x candle body beyond 168% |
| 3. TARGET & RISK | -50% Daily Range | R:R 1:4 to 1:6 |
| VIOLATION FILTER | Abort if close > 200% | M5 candle closes beyond 200% Deep State → abort |

### 5.4 Dual-Leg Execution (CFD + Binary Simultaneous)

| Leg | Entry | Boundary/Expiry | Target |
|-----|-------|-----------------|--------|
| CFD | Limit @ 168% | SL at 200% Deep State | -25% / -50% Daily Range |
| Binary | Activation on Touch | Dynamic expiry by session | Time-based expiry |

**Combined effect:** Hedge — one leg profits regardless of resolution direction.

### 5.5 Kill Switches

| Condition | Action |
|-----------|--------|
| Asian Range > 45 pips | NO-GO — constraint deficit too wide |
| 132% Kill-Switch State | Close all positions immediately |
| After 11 AM EST | No new activations |
| Win rate < 80% (20 activations) | PAUSE & recalibrate |

---

## 6. Dual-Engine Execution Model

**Reference:** Part 10, Pages 58-68

### 6.1 Architecture Overview

The Dual-Engine model splits capital deployment across two complementary engines:

1. **Constraint Anchor (Certainty Layer):** High-probability structural expansion of the Asian constraint deficit
2. **Resolution Amplifiers (Path Exploitation Layer):** P90 activation signals exploiting momentum along the Anchor's direction

**Critical Finding:** Amplifiers aligned with the Anchor outperform standalone P90 trades by **+15.3% win rate** and **+0.86R per activation**.

### 6.2 Constraint Anchor — Detailed Rules

**Prerequisite:** Asian Range < 30 pips (T1 or T2 ONLY)

**Time Window:** 08:00-17:00 UTC (3:00 AM - 12:00 PM EST)

**Activation Signal:**
- M5 candle must **CLOSE** outside Asian High or Low
- Body >= 4.6 pips (P90 threshold)
- LONG Anchor: Close > Asian High AND High > Asian High
- SHORT Anchor: Close < Asian Low AND Low < Asian Low

**Constraint Boundary:** Opposite Asian extreme (structural invalidation)

**Targets:**
- TP1: Asian Range × 0.25 (25% extension) — Hit rate ~89-93% in T1/T2
- TP2: Asian Range × 0.50 (50% extension) — Hit rate ~83% in T1/T2

**Anchor Performance:**

| Metric | Overall | T1 (<20p) | T2 (20-30p) | T3 (30-45p) |
|--------|---------|-----------|-------------|-------------|
| Win Rate (TP25+) | 91.7% | 98.6% | 89.1% | 76.2% |
| Avg R-Multiple | +1.42R | +1.68R | +1.24R | +0.88R |

### 6.3 Resolution Amplifiers — Detailed Rules

**Condition:** ONLY if Tier T1 or T2 AND direction matches Anchor

**Trigger:** P90 activation signal pulling back to partial rebalancing zone

| Tier | Partial Rebalancing Entry | Max Amplifiers | Size Each | Boundary | Target |
|------|--------------------------|----------------|-----------|----------|--------|
| T1 | 32% or 50% | 2 | 20% | 80% Fib of P90 | 20p fixed |
| T2 | 50% ONLY | 1 | 30% | 80% Fib of P90 | 20p fixed |
| T3 | NO AMPLIFIERS | 0 | — | — | — |

**Amplifier Performance:**

| Metric | Aligned with Anchor | Standalone (No Anchor) | Synergy Gap |
|--------|--------------------|-----------------------|-------------|
| Win Rate | 82.4% | 67.1% | +15.3% |
| Avg R-Multiple | +2.64R | +1.78R | +0.86R |

### 6.4 Optimal Capital Allocation

**WINNING STRATEGY: 70% Anchor / 30% Amplifiers**

| Allocation | Avg Daily R | Win Rate | Sharpe | Max DD |
|------------|-------------|----------|--------|--------|
| Anchor Only (100/0) | +1.42R | 91.7% | 2.84 | -4.2R |
| **70% Anchor / 30% Amps** | **+1.86R** | **89.4%** | **3.42** | **-5.1R** |
| 50/50 | +1.92R | 86.2% | 3.15 | -6.8R |
| Amps Only (0/100) | +2.18R | 74.3% | 2.12 | -12.4R |

### 6.5 T3 Model 2 Protocol (Post-Resolution Confirmation)

For T3 days (30-45p Asian Range), use Model 2:

**Entry:** Wait 2 hours after constraint violation close outside Asian band. Enter on pullback to 32-50% partial rebalancing of initial extension leg.

| Metric | T1 | T2 | T3 |
|--------|-----|-----|-----|
| Win Rate (1x Range) | 88.2% | 81.4% | 76.7% |
| Avg R-Multiple | +3.12R | +2.45R | +2.14R |
| Profit Factor | 4.15 | 3.28 | 2.88 |

### 6.6 Overfilled Filter (Critical Risk Management)

| Tier | Condition | Anchor WR | Combined Action |
|------|-----------|-----------|-----------------|
| T1 | Normal (<40p by 9AM) | 89.4% | Full Dual-Engine |
| T1 | Overfilled (>40p) | 62.5% | Anchor ONLY — 50% size |
| T2 | Normal (<40p) | 82.8% | Full Dual-Engine |
| T2 | Overfilled (>40p) | 44.8% | **STAND DOWN** |
| T3 | Normal (<40p) | 79.4% | Model 2 Anchor — 50-75% size |
| T3 | Overfilled (>40p) | 41.2% | **STAND DOWN** |

### 6.7 Exit Logic (Separated by Engine)

| Engine | Exit 1 | Exit 2 | Trailing Logic |
|--------|--------|--------|---------------|
| **Constraint Anchor** | Close 50% at -25% extension (91% hit rate) | Close remaining at -50% extension (80% hit rate) | Move ALL boundaries to BE+2p when TP1 hit |
| **Resolution Amplifier** | Close 100% at fixed 20p OR 1:2.5 RR | No extended holding | Exit fully when target hit — no runners |

---

## 7. Failure Repair Model

**Reference:** Part 11, Pages 69-78

### 7.1 Failure Definition
After a valid 2-hour acceptance hold, failure = first M5 close back **INSIDE** the Asian constraint band before the 1x constraint deficit resolution target is hit.

### 7.2 Failure Sequence — Core Data

| Metric | Value |
|--------|-------|
| Valid 2h-hold setups | 465 |
| Hit 1x target before failure | 52.0% |
| Failed first (close back in) | 45.2% |
| Constraint band midpoint hit first | **73.8%** of failures |
| Continue to opposite band edge | 51.0% |
| Full flip to opposite 1x target | 20.0% |

### 7.3 Three Failure Resolution Types

| Type | What Happens | Frequency | Action |
|------|-------------|-----------|--------|
| Type 1 — Soft Failure | Fails back → midpoint hit → compresses. No follow-through. | Most common | Stand down. Wait for new close signal. |
| Type 2 — Internal Reset | Fails → midpoint → reclaims original side → second 2h acceptance → continues. | 89% of second breaks | Wait for second acceptance hold. Re-enter aligned. |
| Type 3 — Regime Flip | Fails → midpoint → opposite edge → opposite violation → second 2h hold → opposite 1x target. | 11% of second breaks | Win rate 84.6%. Wait for full confirmation. |

### 7.4 Second Acceptance Performance

| Metric | Value |
|--------|-------|
| Second signal becomes valid 2h hold | 50.5% |
| Win rate on second accepted move | 69.8% |
| Same-side re-acceptance (Type 2) WR | 67.7% |
| Opposite-side flip (Type 3) WR | 84.6% |

### 7.5 Failure Timing Detection

| Time After Break | % of Failed Breaks | Classification |
|-----------------|-------------------|----------------|
| 0-15 minutes | ~35% | Wick failure (fastest) |
| 15-30 minutes | ~30% | Shallow hold → dump |
| 30-60 minutes | ~20% | Slow failure (ranging) |
| 60-120 minutes | ~15% | Late failure (looks real) |

**Key Numbers:**
- 65% of fake constraint violations fail within 30 minutes
- 80% of fake constraint violations fail within 60 minutes
- Fast rejection = high-probability fake

### 7.6 Day-of-Week Edge

| Day | Win Rate | First Break Real | Second Break Real | Edge Interpretation |
|-----|----------|-----------------|-------------------|---------------------|
| Monday | 70-75% | 60-65% | 35-40% | Indecisive — reduce size |
| **Tuesday** | **82-88%** | **75-85%** | 15-25% | **Trust the first move** |
| Wednesday | 78-85% | 70-80% | 20-30% | Strong first move |
| Thursday | 65-75% | 50-60% | 40-50% | **Wait — second break is the real trade** |
| Friday | 68-78% | 65-75% | 25-35% | Mixed — quick resolution only |

### 7.7 Flip Probability After Failure

| Day | Prob Opposite Side Becomes Real | Action on Failure |
|-----|-------------------------------|-------------------|
| Monday | 60-70% | Moderate flip — watch for opposite signal |
| Tuesday | 50-60% | Lower flip — often same-side re-acceptance |
| Wednesday | 60-70% | Moderate flip — be aware |
| **Thursday** | **70-80%** | **BEST FLIP DAY** — failure often means opposite is real |
| Friday | 55-65% | Moderate flip — limited follow-through |

---

## 8. The Two Plays — Final Execution Framework

**Reference:** Part 12, Pages 79-84

### PLAY 1 — BASE 80 (Bread & Butter)

**Win Rate:** 85-90% | **Trade every qualifying day**

**Pre-Conditions (ALL must be TRUE):**
- Asian Range < 30 pips (T1 or T2)
- Time: 2:00 AM – 11:00 AM EST
- P90 body meets threshold for time window
- No major news within 4 hours

**Execution:**
- **Entry:** Wait for P90 candle CLOSE outside Asian constraint band → Enter MARKET on close
- **Size:** T1: 100% | T2: 75%
- **Constraint Boundary:** 80% of P90 body from entry
- **TP1:** -25% of Asian Range → Close 50% | Move boundary to BE+2p
- **TP2:** -50% of Asian Range → Close remaining 50%
- **Hard Exit:** 12:00 PM EST — Close EVERYTHING

### PLAY 2 — T3 MAX ACCURACY (Defensive Edge)

**Win Rate:** 76.7% | **T3 ONLY (30-45p Asian Range)**

**Pre-Conditions (ALL must be TRUE):**
- Asian Range 30-45 pips (T3 ONLY)
- M5 candle CLOSES outside Asian constraint band
- Body >= 4.6 pips
- **Price MUST hold outside band for full 2 hours** (non-negotiable)
- NO Amplifiers — Pure Anchor ONLY
- If > 40 pips by 9 AM → STAND DOWN

**Execution:**
- **Entry:** AFTER 2-hour acceptance hold → Enter on pullback to 32-50% partial rebalancing
- **Size:** 50-75% of normal risk
- **Constraint Boundary:** AT Asian High/Low — M5 CLOSE back inside band = EXIT immediately (81.2% rule)
- **Target:** 1x Asian Range extension ONLY — No runners
- **Hard Exit:** 12:00 PM EST

### PLAY 3 — REGIME CONFIRMED PUSH (Ceiling)

**Win Rate:** 92-95% | **When all conditions align**

**Checklist (ALL must be TRUE):**
- All Base 80 conditions met
- Regime Ratio >= 1.5x by 9 AM EST
- P90 confirmed in 2-6 AM EST window
- Cascade timing 45-60 min after initial P90
- Tuesday or Wednesday

**Execution:**
- **Size:** T1: 100% | T2: 100% (upgraded from base 75%)
- **Cascade Adds:** T1: Up to 2 cascade P90s (30-90 min from initial) | T2: Max 1 cascade P90 (50% rebal entry)
- **Cascade Boundary:** 168% of NEW P90 body
- **Targets:** TP1: -25% (close 50%) | TP2: -50% (close 25%) | TP3: 168% Stall Zone (close 20%) | Runner: 200% Deep State (hold 5%, T1 only)
- **Hard Exit:** 12:00 PM EST
- **Kill Switch:** 132% Kill-Switch State → Close ALL immediately

---

## 9. Daily Setups 1-6

**Reference:** Pages 112-136

### SETUP 1 — First Breakout Close (Pure Directional Bias)

**Objective:** Isolate the simplest directional bias signal. First M5 candle close outside Asian High/Low after 3 AM EST.

**Overall Results (917 days):**

| Metric | Value |
|--------|-------|
| Hit rate — -25% target | 89.2% |
| Hit rate — -50% target | 78.4% |
| Hit rate — -100% target | 64.1% |
| On-Time hits (before 12 PM) | 84.9% |
| Avg time to -50% from 3 AM | 4.2 hours |
| Invalidation rate (80% + 2p rule) | 12.3% |

**Tier Breakdown:**

| Tier | Hit Rate (-50%) | On-Time % | Avg Time to Hit |
|------|----------------|-----------|-----------------|
| T1 (<20p) | 84.6% | 88.2% | 3.1 hours |
| T2 (20-30p) | 79.1% | 85.4% | 4.5 hours |
| T3 (30-45p) | 68.5% | 76.3% | 6.8 hours |

**Regime Breakdown:**

| Regime | Hit Rate (-50%) | On-Time % |
|--------|----------------|-----------|
| CONFIRMED (≥1.5x) | 86.7% | 88.1% |
| CAUTION (1.45-1.49x) | 74.6% | 82.3% |
| FAILED (<1.45x) | 59.3% | 68.2% |

**Execution:**
1. 3:00 AM EST: Classify Asian Range → T1/T2 = GO | T3 = CAUTION
2. 3:00-11:00 AM: Wait for first M5 candle CLOSE outside Asian band
3. 9:00 AM: Regime checkpoint → CONFIRMED: hold to -50% | CAUTION: trail at -25% | FAILED: target -25% only
4. 12:00 PM: Hard exit
5. Invalidation: M5 close beyond 80% + 2p back inside Asian band → exit immediately

### SETUP 2 — -50% Target Temporal Delivery + EWS Exit

**Objective:** Map exact time thresholds by tier for target delivery. Define EWS (Early Warning Signal) exit protocol.

**Temporal Delivery by Tier:**

| Tier | Mean Time to -50% | Median Time | Edge Thin if -25% Not Hit By | EWS Exit if -50% Not Hit By |
|------|-------------------|-------------|------------------------------|----------------------------|
| T1 (<20p) | 3.1 hours | 2.8 hours | 3.0 hours | 4.2 hours |
| T2 (20-30p) | 4.6 hours | 4.1 hours | 4.4 hours | 6.2 hours |

**EWS (Early Warning Signal) at Targets:**

| Scenario | EWS Trigger | Action |
|----------|------------|--------|
| Price hits -25% + opposite P90 prints | Body ≥ 4.6p, closes against bias | Close remaining 50% immediately |
| Price hits -50% + opposite P90 prints | Body ≥ 4.6p, closes against bias | Close 100% — constraint deficit resolved |
| Price stalls at -40% + opposite P90 prints | Body ≥ 4.6p, closes against bias | Trail boundary to BE+2p, exit on next M5 close against |

**Key Rule:** EWS at targets ≠ reversal. It is momentum exhaustion — a valid exit, not a reversal trade.

### SETUP 3 — T3 First Breakout Close

**Objective:** T3-specific rules. 216 T3 days analyzed.

| Metric | T3 Value | vs T1/T2 |
|--------|----------|----------|
| Hit rate — -25% | 81.5% | Lower than T1 (93%) / T2 (89%) |
| Hit rate — -50% | 68.5% | Primary T3 operating edge |
| Hit rate — -100% | 48.1% | Skip unless Regime CONFIRMED |
| On-Time hits | 72.3% | Slower than T1 (88%) / T2 (85%) |
| Avg time to -50% | 6.8 hours | T2 = 4.6h / T1 = 3.1h |
| Invalidation rate | 18.9% | Higher than T1/T2 (~12%) |

**T3 EWS Behavior (Key Distinction from T1/T2):**
- EWS at -25% (T3): **73.2% continuation** → treat as noise, hold the runner
- EWS at -50% (T3): **41.8% continuation** → genuine momentum exhaustion, exit

**Execution:**
- Size: 50-75% of normal risk
- Target -25%: Close 50%, move boundary to BE+2p. EWS at -25% = HOLD runner (73.2% continue)
- Target -50%: Trail aggressively. EWS at -50% = EXIT fully (41.8% continuation is below threshold)
- No runners beyond -50%
- Timing kill switches: -25% not hit by 5.5h → edge thinning; -50% not hit by 8.5h → stand down

### SETUP 4 — Cascade EWS (Opposite P90 at 45-Min Window)

**Objective:** Test opposite-direction P90 cascade at 45-60 min window. Is it a reversal entry or trim signal?

**Core Results (917 days, 142 Cascade EWS events = 15.5% of days):**

| Metric | Value |
|--------|-------|
| Reversal entry win rate | 64.8% (below CEREBUS 85% standard) |
| Trim/exit effectiveness on Anchor | **78.4%** |
| Avg R-Multiple (reversal entry) | +1.18R |
| Regime FAILED + Cascade EWS WR | 77.1% |

**Verdict:** Cascade EWS is NOT a reversal entry signal (64.8% < 85% standard). It IS a **high-value trim and exit tool** (78.4% effectiveness).

**Three Cascade EWS Patterns:**

| Pattern | Frequency | What Happens | Action |
|---------|-----------|-------------|--------|
| False Cascade | 32.4% | Opposite P90 → price reverses 5-8p → resumes original direction | TRIM only. Do not reverse. |
| Exhaustion Cascade | 49.3% | Opposite P90 → price retraces to -25% → stalls and compresses | TRIM 50-75%. Small runner with tight boundary. |
| Regime Flip Confirmation | 18.3% | Opposite P90 → price reverses AND holds 2+ hours → new direction | VALID reversal entry — ONLY after 2h hold + Regime FAILED. |

**Conditional Reversal Entry (ALL four required):**
1. Regime = FAILED at 9 AM (ratio < 1.45x)
2. Cascade EWS fires in 45-60 min window
3. Resolution output CLOSES beyond 200% Deep State
4. Price HOLDS outside original band for 2 hours
→ Win rate when all conditions met: **77.1%**

### SETUP 5 — 5-Day Anchor Macro Setup (Monthly Constraint Resolution)

**Objective:** Use first 5 trading days of each month as the structural constraint anchor.

| Component | Specification |
|-----------|--------------|
| Anchor | First 5 Trading Days range (High to Low) |
| Activation | M5 CLOSE outside 5-day band + 2-hour hold |
| Target | 2.0x (200% extension) of the 5-day range |
| Win rate | 81-84% |
| Time to target | Days 10-14 (median Day 11.4) |
| Hard exit | Trading Day 15 |
| Invalidation | M5 close back inside the 5-day band |

**Tier Classification (5-Day Range):**

| Tier | 5-Day Range | Expansion Multiplier | Win Rate | Size |
|------|------------|---------------------|----------|------|
| M-T1 | < 60p | 2.8x – 3.2x | ~86% | Full — aggressive |
| M-T2 | 60-90p | 2.1x – 2.5x | ~82% | Standard — core edge |
| M-T3 | 90-125p | 1.5x – 1.9x | ~75% | 50% — defensive |
| NO-GO | > 125p | Skip | < 65% | Stand down |

### SETUP 6 — Post-Failure Repair Sequence

**Objective:** When Setup 5 activation fails, define the repair sequence and re-entry rules.

**Post-Failure Sequence:**
1. Stop out at 5-Day band edge → Exit fully
2. Price rebalances toward midpoint (73.8% frequency) → **Observe only**
3. Midpoint = Decision Zone:
   - **Type 1:** Price stalls and compresses → Stand down
   - **Type 2 (89%):** Price reclaims original breakout side → Same-side re-entry
   - **Type 3 (11%):** Price drives to opposite band → Potential flip (requires full confirmation)

**Midpoint Re-Entry (Same-Side Continuation):**
- Trigger: M5 candle closes back in original breakout direction at midpoint
- Size: 60-70% of original activation size
- Stop: 2-3 pips beyond midpoint
- TP1: Opposite band edge (65-70% hit rate)
- TP2: 100% extension (50-55% hit rate)
- TP3/Runner: 168% extension (30-35%, only if price holds outside band 2h post-TP1)

**Opposite-Side Flip (ALL conditions required):**
1. Initial breakout failed
2. Price rebalanced to midpoint
3. Price continued to OPPOSITE band
4. M5 candle CLOSES outside opposite band
5. Price HOLDS outside for 2 full hours
→ Win rate on confirmed flips: **84.6%**

---

## 10. Atomic Market Structure

**Reference:** Part 15 / Atomic Market Structure, Pages 137-142

### 10.1 The Density Zone

The **Density Zone** is the confluence layer where Atomic Unit completion and Tier Threshold resolution align simultaneously.

| Component | T1 | T2 | T3 |
|-----------|-----|-----|-----|
| Asian Range | < 20p | 20-30p | 30-45p |
| Atomic Unit | 10p | 12p | 15p |
| Tier Threshold | 10p | 15p | 19p |
| 1.44x Shift Target | 14.4p | 17.3p | 21.6p |

### 10.2 The Convergence Factor (Phi)

**PHI = (0.40 × Regime) + (0.25 × P90) + (0.20 × Cascade) + (0.15 × Float)**

| Component | Score |
|-----------|-------|
| Regime | 1.0 if Ratio ≥ 1.50 / 0.7 if 1.45-1.49 / 0.5 if < 1.45 |
| P90 | 1.0 if confirmed in 2-6 AM window |
| Cascade | 1.0 if printed in 45-60 min optimal window |
| Float | 1.0 if Monday/Tuesday Float confirmed |

**Phi to Win Rate:**

| Phi | P_Win | Action |
|-----|-------|--------|
| 1.0 (all conditions) | 98.7% | Maximum conviction |
| ≥ 0.8 | 91-94% | High conviction |
| ≥ 0.6 | 85% | Base — minimum acceptable |
| < 0.6 | NO-GO | Do not trade |

### 10.3 Fixed Dollar Expectancy (FDE)

**Formula:** Lot Size = Target Dollar Profit / (Atomic Target Pips × Pip Value)

| Tier | Atomic Target | Pip Value | Target $ | Lot Size |
|------|--------------|-----------|----------|----------|
| T1 | 10p | $10/pip | $50 | 0.50 Lots |
| T2 | 12p | $10/pip | $50 | 0.36 Lots |
| T3 | 15p | $10/pip | $50 | 0.28 Lots |

**Result:** Every win pays $50 regardless of tier. Equity curve is a straight line up.

### 10.4 Grand Unified Equation

**Expected Return ($) = [Target $ / (Atomic Target_Tier × Pip Value)] × [(Atomic Target_Tier × P_Win(Phi)) – (SL_Structural × (1 – P_EWS))]**

### 10.5 First Impulse Predictor (2-Hour Tier Head Start)

The market telegraphs its final volatility tier within the first valid impulse at 3:00-4:00 AM EST:

| Early Range (3:00-3:30 AM) | First Impulse Size | Predicted Tier | Confidence |
|---------------------------|-------------------|----------------|------------|
| Less than 10 pips | >= 12 pips | T2 (Not T1) | 91% |
| Less than 15 pips | >= 18 pips | T3 (Not T2) | 89% |
| Less than 20 pips | >= 25 pips | NO-GO / Extreme T3 | 94% |
| Any | Less than threshold | Remains current tier | 85% |

### 10.6 Expected Atomic Loops Per Day (EUR/USD)

| Tier | Asian Range | Expected Loops/Day | High-Conviction Entries |
|------|------------|-------------------|----------------------|
| T1 | < 20p | 4 – 7 | 3-4 |
| T2 | 20-30p | 3 – 5 | 2-3 |
| T3 | 30-45p | 2 – 4 | 1-2 |

---

## 11. Risk Management & Position Sizing

### 11.1 Core Risk Parameters

| Parameter | Value | Rule |
|-----------|-------|------|
| Risk Per Activation | 0.12% of Equity | Per signal limit |
| Max Concurrent Risk | 0.36% (3 signals) | All open positions combined |
| Daily Constraint Boundary | 0.40% | Close ALL if hit; no more activations |
| Personal Daily Limit | 0.50% | 0.40% hard boundary preserves buffer |

### 11.2 Cascade Position Sizing Example ($10,000 account)

| Activation | Size % | $ Amount | Boundary | Units |
|------------|--------|----------|----------|-------|
| Signal 1 (Initial P90) | 40% | $4 | 80% of P90 body | 11,764 |
| Signal 2 (45-Min Add) | 30% | $3 | Breakeven | — |
| Signal 3 (Cascade P90) | 20% | $2.40 | 168% of P90 body | 2,790 |
| Signal 4 (Cascade 2) | 10% | $1.20 | 168% of P90 body | — |
| **TOTAL** | **100%** | **$7.60 (0.076%)** | Mixed | — |

### 11.3 Correlation Warning
Do not activate EUR/USD and GBP/USD simultaneously in the same direction of constraint resolution unless reduced size is applied. Treat them as one constraint position.

### 11.4 Weekly Review — Pause & Recalibrate If:
- Win rate drops below 80% over 20-activation sample
- 132% Kill-Switch State violations increase > 50% in a week
- Asian Range (constraint deficit) consistently > 45 pips

---

## 12. Implementation Notes for Nautilus Trader

### 12.1 Data Requirements
- **Primary:** EUR/USD M5 candles (minimum 4 years historical for backtesting)
- **Session markers:** UTC timestamps required for Asian session boundary detection (00:00-08:00 UTC)
- **Real-time:** Live M5 tick data for signal generation

### 12.2 Core Components to Implement

1. **Asian Range Calculator**
   - Input: M5 candles 00:00-08:00 UTC
   - Output: Asian High, Asian Low, Range Size, Tier Classification

2. **P90 Candle Detector**
   - Input: M5 candles in 2:00 AM - 11:00 AM EST window
   - Logic: Body size >= threshold for time window AND close outside Asian band
   - Output: Signal direction, body size, timestamp

3. **Cascade Tracker**
   - Input: P90 signals
   - Logic: Same direction, within 120 min, max 3 cascades
   - Output: Cascade count, validity flag

4. **Regime Classifier (9:00 AM checkpoint)**
   - Input: Daily Range (3AM-9AM) / Asian Range
   - Output: CONFIRMED (≥1.5x) / CAUTION (1.45-1.49x) / FAILED (<1.45x)

5. **Dual-Engine Signal Generator**
   - Constraint Anchor: Close outside Asian band + body >= 4.6p
   - Resolution Amplifier: P90 at partial rebalancing zone + aligned with Anchor
   - Output: Entry signal with type, size, boundary, targets

6. **Overfilled Filter (9:00 AM)**
   - Input: Current daily range at 9:00 AM
   - Logic: > 40 pips → T1: Anchor only 50% / T2/T3: Stand down

7. **Exit Manager**
   - TP1/TP2 targets based on Asian Range extensions
   - 12:00 PM EST hard exit timer
   - 132% Kill-Switch monitor
   - EWS (opposite P90 at targets) detector

8. **Failure Repair State Machine**
   - States: Active → Failed → Midpoint → Type 1/2/3 → Re-entry
   - 2-hour hold timer for second acceptance

### 12.3 Key Thresholds Summary (EUR/USD M5)

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

### 12.4 State Machine Design

The system is best implemented as a **finite state machine** with the following states:

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

### 12.5 Backtesting Priorities

1. **Start with Setup 1 (First Breakout Close)** — simplest signal, 78.4% win rate on -50% target
2. **Add P90 Cascade** — +37% weekly R improvement
3. **Add Dual-Engine** — Anchor + Amplifier synergy
4. **Add Regime Filter** — 9 AM checkpoint for target adjustment
5. **Add Failure Repair** — second acceptance edge (69.8% WR)
6. **Add Macro (Setup 5)** — monthly 5-day anchor for swing trades

### 12.6 Critical Implementation Rules

1. **Closes only, never wicks** — All entry/exit/invalidation signals use M5 candle **closes**, not wicks
2. **81.2% rule** — If M5 closes back inside Asian band, exit immediately (do not wait)
3. **12:00 PM hard exit** — Non-negotiable, close ALL positions
4. **Alignment is mandatory** — Resolution Amplifiers must match Anchor direction (84.2% vs 58.4% WR)
5. **Overfilled = stand down** — T2/T3 with > 40 pips by 9 AM = negative expectancy
6. **Day-of-week matters** — Tuesday/Wednesday = full size. Thursday = wait for second move. Monday/Friday = reduced size.

---

*Document generated from CEREBUS FX v4.0 Manual (April 2026). All data derived from EUR/USD M5, Jan 2022 – Apr 2026, 315,000+ candles. For educational purposes only. Test all strategies in simulation before live deployment.*
