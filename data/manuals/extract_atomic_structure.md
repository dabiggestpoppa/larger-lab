# ATOMIC MARKET STRUCTURE — Complete Extraction
## CEREBUS FX v4 Manual | Pages 139-151+ | EUR/USD M5

---

## 1. ATOMIC UNIT DISCOVERY — K-MEANS CLUSTERING METHODOLOGY

### Discovery Formula

**Step 1 — Extract:**
- Calculate Asian Session Range (19:00-03:00 EST) for every trading day over 4 years

**Step 2 — Cluster:**
- Run K-Means clustering (k=3) on distribution of ranges
- Reveals three natural volatility regimes: T1, T2, T3

**Step 3 — The Formula:**
```
Cluster Centroid (C) = Mean Asian Range for that volatility group
Atomic Unit (AU)     = C × 0.50  (exactly 50% of cluster centroid)
Tier Trigger         = AU × 1.20
Density Zone         = AU ± 20%
```

### Why 50%?
- AU = 50% of centroid = the field's micro-resolution step
- The field cannot resolve the full deficit in one move (would violate liquidity constraints)
- Splits resolution into two equal halves:
  - **First Half (Tier Impulse):** Breaks the band. Establishes direction.
  - **Second Half (AU Completion):** Rebalances and completes the cycle.

### Fibonacci Fix — Why Fibs Fail
| Approach | Target Definition | Hit Rate | Why |
|----------|-------------------|----------|-----|
| Fibonacci | 61.8% of impulse (geometric ratio) | 78-82% | Probabilistic average — price crosses near but not at the level |
| K-Means AU | 50% of cluster centroid (measured mean) | 95-98% | Aligns exactly with field's actual resolution step-size |

**When locked to 50% Centroid rule:**
- EUR/USD T1: 98.7%
- ETH T1: 98.0%
- BTC T1: 97.1%
- US500 T1: 92.6%
- Remaining 2-5% failures = spread/slippage/news gaps (not structural)

---

## 2. ATOMIC UNIT SIZES BY TIER (EUR/USD)

| Component | Role | T1 | T2 | T3 |
|-----------|------|----|----|-----|
| Tier Impulse | Direction Setter | ≥10p | ≥15p | ≥19p |
| Atomic Unit | Cycle Completer | **10p** | **12p** | **15p** |
| Combined | Full Resolution | Impulse + AU = Centroid | — | — |
| Tier Trigger (=AU×1.20) | Activation threshold | 12p | 15p | 19p |

### Live Execution Cycle
```
[Impulse >= Tier Trigger] → Direction locked. Band broken.
     ↓
[Pullback to Density Zone (32-50%)] → Partial rebalancing [6].
     ↓
[Opposite Candle Close in DZ] → Entry signal.
     ↓
[Price travels 1 AU] → Cycle complete. Scalp target hit.
     ↓
Cumulative output >= Tier Distribution Target? → Session done.
Otherwise: Reset. New Impulse forms. Cycle N+1 begins.
```

**The Tier Impulse tells you WHERE the field is going.**
**The Atomic Unit tells you HOW FAR before it must pause.**

---

## 3. DENSITY ZONE — THE CERTAINTY FILTER

### Definition
The density zone is the confluence layer where Atomic Unit completion and Tier Threshold resolution align simultaneously.

### Context Table
| Concept | What It Is | How You Use It |
|---------|-----------|----------------|
| Atomic Unit | Micro-step size (T1=10p, T2=12p, T3=15p) | Scalping rebalances inside confirmed direction |
| Tier Threshold | Macro-liquidity boundary (T1=10p, T2=15p, T3=19p) | Structural extremes and new resolution pathway grabs |
| **Density Zone** | **Overlap where both mechanics align** | **Certainty filter. Entries here. Targets here.** |

### Execution Checklist — Pure Physics
| Question | If No | If Yes |
|----------|-------|--------|
| 1. Did it hit the Threshold? | Ignore. It is noise. | Mark the Extreme High/Low. Wait. |
| 2. Is it pulling back into the Density Zone? | Keep waiting. Do not chase. | Watch the candles. |
| 3. Did an Opposite Candle Close in the Zone? | Keep waiting. | **ENTER.** |

### Exit Rules
| Rule | Specification | Logic |
|------|--------------|-------|
| Target | Next Atomic Unit (T1=10p, T2=12p, T3=15p from entry) | One full atomic loop |
| EWS Filter | Opposite P90 (Body ≥4.5p) within 30-90 min → EXIT | Momentum exhaustion signal |
| Hard Time Exit | 12:00 PM EST — close ALL | Resolution engine shuts down |
| Kill Switch | 132% Asian Range violated → close ALL | Kill-Switch State — constraint set fully invalidated |

### Live Execution — Seven States
```
[STATE 1] IMPULSE DETECTED
  Tier threshold broken (T1: ≥10p | T2: ≥12p | T3: ≥15p)
  Direction of constraint resolution established.

[STATE 2] WAIT FOR PULLBACK
  Watch price retrace toward the Density Zone. Do not chase.

[STATE 3] DENSITY ZONE CONFIRMED
  Price closes inside the zone (±1 pip). Zone is active.

[STATE 4] OPPOSITE CANDLE PRINTS
  Green close if LONG | Red close if SHORT
  Body must be meaningful — dojis do not count.

[STATE 5] ENTER
  Market order on the close. No hesitation.

[STATE 6] TARGET
  Next Density Zone OR Tier Threshold — whichever comes first.
  Scalp target = Atomic Unit | Shift target = 1.44x for runner.

[STATE 7] CLOSE AND RESET
  State 1 repeats. No holding past target. No discretion.
```

---

## 4. THE CONVERGENCE FACTOR (PHI) — WIN RATE SCALING

### Formula
```
PHI = (0.40 × Regime) + (0.25 × P90) + (0.20 × Cascade) + (0.15 × Float)

Where:
  Regime:  1.0 if Ratio >= 1.50  |  0.7 if Ratio 1.45-1.49  |  0.5 if < 1.45
  P90:     1.0 if confirmed in 2-6 AM window
  Cascade: 1.0 if printed in 45-60 min optimal window
  Float:   1.0 if Monday/Tuesday Float confirmed
```

### Phi to Win Rate Mapping
| Phi Level | P_Win | Interpretation |
|-----------|-------|----------------|
| Phi = 1.0 (all conditions) | **98.7%** | Near-perfect setup |
| Phi ≥ 0.8 | 91-94% | High conviction |
| Phi ≥ 0.6 | 85% | — |
| Phi < 0.6 | — | **Base — minimum acceptable** |

---

## 5. FIXED DOLLAR EXPECTANCY (FDE) — TARGET-FIRST SIZING

### Formula
```
LOT SIZE = Target Dollar Profit / (Atomic Target Pips × Pip Value)
```

### Examples (at $10/pip, target $50)
| Tier | Atomic Pips | Lot Size | Result |
|------|------------|----------|--------|
| T1 Day | 10p | 0.50 Lots | Every win pays $50 |
| T2 Day | 14p | 0.36 Lots | Every win pays $50 |
| T3 Day | 18p | 0.28 Lots | Every win pays $50 |

**Equity curve is a straight line up — zero lumpy returns.**

**Why NOT fixed % risk:**
- Fixed % risk on T1 (tight SL) vs T3 (wide SL) creates wildly different dollar outcomes
- FDE inverts: larger pip distance → fewer lots → constant dollar output

---

## 6. THE CEREBUS GRAND UNIFIED EQUATION

```
Expected Return ($) =
  [ Target $ / (Atomic Target_Tier × Pip Value) ]     ← Dynamic Lot Size
  ×
  [ (Atomic Target_Tier × P_Win(Phi))                 ← Weighted Expectancy
    - (SL_Structural × (1 - P_EWS)) ]                 ← Filtered Risk
```

### Variables
| Variable | Values |
|----------|--------|
| Atomic Target_Tier | T1: 10p \| T2: 12p \| T3: 15p |
| P_Win(Phi) | Win rate at current field state (87-98.7%) |
| SL_Structural | Structural constraint boundary [8] in pips |
| P_EWS | Probability EWS exits before SL is hit (~78%) |

### Example (T2 Day, Phi=1.0, target $50)
```
Lot Size = $50 / (14p × $10) = 0.357 lots
Expected = 0.357 × [(14p × 0.987) - (tiny SL × 0.013)]
         = ~$49.35 per trade
```

---

## 7. FIRST IMPULSE PREDICTOR — 2-HOUR TIER HEAD START

### Concept
The market telegraphs its final volatility tier within the first valid impulse at 3:00-4:00 AM EST. Predicts final tier with 88-91% accuracy.

### Prediction Table
| Early Range (3:00-3:30 AM) | First Impulse Size | Predicted Tier | Confidence | Action |
|---------------------------|-------------------|----------------|------------|--------|
| Less than 10 pips | ≥12 pips | T2 (Not T1) | 91% | Load T2 parameters immediately |
| Less than 15 pips | ≥18 pips | T3 (Not T2) | 89% | Load T3 parameters immediately |
| Less than 20 pips | ≥25 pips | NO-GO / Extreme T3 | 94% | Stand down or Max Vol settings |
| Any | Less than threshold | Remains current tier | 85% | Wait for 3AM confirmation |

### Logic
- If a T1 day (<20p) suddenly prints a 15p+ move at 3:15 AM, statistically impossible to close as T1
- T2 energy already injected → adjust parameters instantly
- Gives 2-hour advantage over standard 3AM classification

---

## 8. 1.44x SHIFT TARGETS — EUR/USD M5

| Tier | Asian Range | Atomic Unit | 1.44x Shift Target | Shift Band |
|------|------------|------------|-------------------|------------|
| T1 | <20p | 10 pips | **14.4 pips** | 12.0 – 16.8 pips |
| T2 | 20-30p | 12 pips | **17.3 pips** | 14.4 – 20.2 pips |
| T3 | 30-45p | 15 pips | **21.6 pips** | 18.0 – 25.2 pips |

---

## 9. EXPECTED ATOMIC LOOPS PER DAY — EUR/USD

| Metric | EUR/USD Value |
|--------|--------------|
| Avg Loops per Day (all tiers) | **~4.2** |
| Total Valid Setups (4 Years) | **~12,480** (86% of qualifying days) |
| Win Rate (Filtered with EWS) | **98.7%** |
| Avg Profit per Trade (FDE logic) | **$50.00** — flat regardless of tier |
| Live High-Conviction Entries/Day | **~3-4** |

### By Tier
| Tier | Asian Range | Expected Loops/Day | High-Conviction Entries | Notes |
|------|------------|--------------------|------------------------|-------|
| T1 | <20p | 4 – 7 | 3-4 | Tight constraint deficit — clean repetitive stepping. Highest frequency. |
| T2 | 20-30p | 3 – 5 | 2-3 | Balanced resolution. Standard loop frequency. Core bread-and-butter. |
| T3 | 30-45p | 2 – 4 | 1-2 | Wider range — fewer clean cycles, more noise. Trade only perfect setups. |

### Execution Notes
- **T1 Day:** Expect 4-7 loops → Trade first 3-4 high-conviction → Stand down 12PM
- **T2 Day:** Expect 3-5 loops → Trade 2-3 setups → Quality over frequency
- **T3 Day:** Expect 2-4 loops → Trade 1-2 setups ONLY with full Density Zone + Opposite Close. Do not force entries.

---

## 10. DISTRIBUTION SYMMETRY TRAP

### Three Layers
| Layer | Mechanism | What It Does | Why It Matters |
|-------|-----------|--------------|----------------|
| 1 — Bias Lock | First M5 close outside Asian Range | Sets directional bias for entire session | Stops fighting macro flow — path of least resistance locked |
| 2 — Atomic Entry | Impulse >= trigger in bias direction + opposite close pullback | Gives high-probability entry after risk is released | Enter with the flow but after breakout risk is absorbed |
| 3 — Distribution Target | Hold to -25%/-50%/-100% AR extension | Scales R-multiple far beyond atomic scalp | Pullback entry means holding to 50% AR becomes low risk swing |

### Targets
- Scalp: Close at 1 Atomic Unit (10/12/15p)
- Distribution: Hold to -25%, -50%, or -100% of Asian Range extension
- **Validated across 11 assets: 83-86% WR with +1.84R avg**

### Execution Code Template
```python
# LAYER 1: LOCK BIAS — first M5 close outside Asian band
for idx, row in bias_window.iterrows():
    if row['close'] > asian_high: bias = 1; break
    if row['close'] < asian_low: bias = -1; break

# LAYER 2: ATOMIC ENTRY — impulse (body >= atomic*0.5) + opposite close
for idx, row in post_bias.iterrows():
    if bias==1 and row['close']>row['open'] and body>=atomic*0.5:
        if next_candle['close'] < next_candle['open']:
            entry = next_candle['close']; break  # LONG ENTRY
    if bias==-1 and row['close']<row['open'] and body>=atomic*0.5:
        if next_candle['close'] > next_candle['open']:
            entry = next_candle['close']; break  # SHORT ENTRY

# LAYER 3: TARGETS — -25%/-50%/-100% of Asian Range from band edge
t25  = asian_edge + ar * 0.25 * bias
t50  = asian_edge + ar * 0.50 * bias
t100 = asian_edge + ar * 1.00 * bias

# SL = M5 close back inside Asian band (81.2% rule — not wick, close only)
# Hard exit = 12:00 PM EST
```

### DE30 Validated Backtest — 847 Sessions
| Metric | Value | Notes |
|--------|-------|-------|
| Total Sessions | 847 | ~3.1 trades/day avg |

---

## 11. GEAR SHIFT OVERRIDE — MIRRORED MOVE

### Concept
When the opening Asian Range classifies as T1 but the first impulse exceeds the T2 trigger threshold, the field has intraday-reclassified. Upgrades the target to the shifted tier's Atomic Unit.

### Live Execution Rules
```
IF base_tier == T1 AND impulse >= 15p → USE T2 AU (12p) as target
IF base_tier == T1 AND impulse >= 19p → USE T3 AU (15p) as target
IF base_tier == T2 AND impulse >= 19p → USE T3 AU (15p) as target
IF base_tier == T3 AND impulse >= 25p → USE MT25 AU (25p) as target
ELSE → USE original day-tier AU

SL = EXACT OCC Extreme (zero buffer, close-only invalidation)
Hard Exit = 12:00 PM EST
Session = 3AM – 12PM EST
```

### Backtest Results — EUR/USD M5 (Jan 2023 – May 2026)

**Target Comparison:**
| Target Type | Trades | Win Rate | Avg PnL | Avg R | Profit Factor |
|-------------|--------|----------|---------|-------|---------------|
| ORIGINAL AU (Day Tier) | 482 | 74.3% | +9.1p | 1.12R | 2.68 |
| MIRRORED AU (Shifted Tier) | 482 | 89.1% | +16.8p | 2.04R | 5.94 |

**Breakdown by Shift Type:**
| Shift Type | Trades | Win Rate | Avg PnL | Avg R | Notes |
|------------|--------|----------|---------|-------|-------|
| T1 → T2 | 284 | 91.2% | +13.6p | 2.18R | **Highest frequency (59%) + highest WR** |
| T1 → T3 | 78 | 85.9% | +18.2p | 1.92R | Strong R, moderate frequency |
| T2 → T3 | 94 | 87.2% | +16.4p | 1.88R | Solid confirmation of shift logic |
| T3 → MT25 | 26 | 80.8% | +24.6p | 1.74R | Lower WR — massive PnL per win |

**Non-Shifted Baseline (Zero Buffer, No Gear Shift):**
| Metric | Value |
|--------|-------|
| Trades | 2,148 |
| Win Rate | 91.4% |
| Avg PnL | +11.2p |
| Avg R-Multiple | 1.68R |

**Expectancy Comparison — Three Configurations:**
| Configuration | Win Rate | Avg R | Expectancy/Trade | Improvement |
|---------------|----------|-------|------------------|-------------|
| Original AU + Buffer SL | ~86% | ~1.0R | +0.89R | — |
| Mirrored AU + Buffer SL | 86.6% | 1.52R | +1.52R | +71% |
| **Mirrored AU + Zero Buffer** | **89.1%** | **2.04R** | **+2.04R** | **+129%** |

### Key Findings
- Zero Buffer + Mirrored Move = **optimal configuration**
- T1→T2 shift = statistical sweet spot (59% of all shifts, 91.2% WR)
- Close-only invalidation added +2.5% WR on shifted impulses vs buffered test
- Combined upgrade: **+129% expectancy improvement** over original
- Non-shifted baseline at 91.4% = gear shift is purely additive (doesn't degrade normal ops)

---

## 12. ETH/USD — GEAR SHIFT OVERRIDE RESULTS

### Comparison
| Target Type | Trades | Win Rate | Avg PnL | Avg R | Profit Factor |
|-------------|--------|----------|---------|-------|---------------|
| ORIGINAL AU | 1,842 | 76.8% | +28.4 pts | 1.18R | 2.94 |
| MIRRORED AU | 1,842 | 88.4% | +41.6 pts | 1.92R | 5.48 |

### ETH/USD Execution Rules
```
IF T1 day and impulse >= 50 pts → USE T2 AU (42 pts)
IF T1/T2 day and impulse >= 62 pts → USE T3 AU (52 pts)
IF impulse < next tier trigger → USE original day-tier AU
SL = EXACT OCC Extreme (zero buffer, close-only invalidation)
Hard exit: 12:00 PM EST | Regime filter: 9AM checkpoint required
T3 days: anchor-only mode, no gear shift extension
```

### ETH-Specific Insights
- Gear shift more pronounced on ETH than EUR/USD
- Despite crypto wick volatility, close-only invalidation maintained 88.4% WR
- Regime filter matters more for ETH: T1/T2 WR drops to ~80% on FAILED vs 90%+ on CONFIRMED
- Structural map identical to EUR/USD — only execution parameters scale

---

## 13. BTC/USD — GEAR SHIFT RESULTS (Jan 2024 – May 2026)

| Target Type | Trades | Win Rate | Avg PnL | Avg R | Profit Factor |
|-------------|--------|----------|---------|-------|---------------|
| ORIGINAL AU | 1,428 | 74.6% | +148.2 pts | 1.08R | 2.54 |
| MIRRORED AU | 1,428 | 86.8% | +234.6 pts | 1.82R | 4.96 |

### BTC-Specific Notes
- Spread filter required: skip entry if spread exceeds 15 pts
- Regime filter critical: T1/T2 WR drops to ~78% on FAILED vs 87%+ on CONFIRMED
- T3 days: Model 2 anchor-only mode
- +83% expectancy improvement from original buffered configuration

---

## 14. CROSS-ASSET COMPARISON — THREE MONSTERS

| Metric | EUR/USD | ETH/USD | BTC/USD | Pattern |
|--------|---------|---------|---------|---------|
| Mirrored WR | 89.1% | 88.4% | 86.8% | Consistent across vol scales |
| Mirrored Avg R | 2.04R | 1.92R | 1.82R | Slight decline with vol |
| Non-Shifted WR | 91.4% | 89.8% | 87.2% | Base engine intact |
| Best Shift | T1→T2 91.2% | T1→T2 90.2% | T1→T2 88.4% | **T1→T2 dominant universally** |
| Profit Factor | 5.94 | 5.48 | 4.96 | All above 4.0 threshold |
| Sharpe Ratio | 4.82 | 4.46 | 3.94 | All above institutional standard |
| Avg Win | +16.8p | +41.6 pts | +234.6 pts | Scales with volatility |
| Avg Loss | -5.2p | -12.8 pts | -78.4 pts | Zero buffer compresses risk |
| Net Expectancy | +13.2p | +32.0 pts | +173.8 pts | After spread/slippage |

**Universal Law: Mirrored Move + Zero Buffer holds fractally across all three assets.**

### Monte Carlo Simulation — 10,000 Iterations, $10K Start, 1% Risk
| Metric | EUR/USD | ETH/USD | BTC/USD |
|--------|---------|---------|---------|
| Median Final Balance | $142,800 | $128,400 | $108,600 |
| Mean Final Balance | $158,200 | $141,900 | $119,800 |
| 90th Percentile | $248,000 | $224,000 | $192,000 |
| 10th Percentile | $52,400 | $46,800 | $38,200 |
| Median CAGR | 412% | 378% | — |

---

## 15. TIER IMPULSE TRIGGERS — ALL 19 ASSETS (UNIVERSAL REFERENCE)

### FX Majors
| Asset | Pip | T1 Trigger | T2 Trigger | T3 Trigger | T1→T2 Shift | T1→T3 Shift | T2→T3 Shift |
|-------|-----|------------|------------|------------|-------------|-------------|-------------|
| EUR/USD | 0.0001 | ≥12p | ≥15p | ≥19p | impulse≥15p | impulse≥19p | impulse≥19p |
| GBP/USD | 0.0001 | ≥16p | ≥19p | ≥24p | impulse≥16p | impulse≥24p | impulse≥24p |
| USD/CHF | 0.0001 | ≥13p | ≥18p | ≥24p | impulse≥13p | impulse≥24p | impulse≥24p |
| USD/JPY | 0.01 | ≥19p | ≥31p | ≥53p | impulse≥19p | impulse≥53p | impulse≥53p |
| AUD/USD | 0.0001 | ≥16p | ≥20p | ≥25p | impulse≥16p | impulse≥25p | impulse≥25p |
| NZD/USD | 0.0001 | ≥17p | ≥20p | ≥25p | impulse≥17p | impulse≥25p | impulse≥25p |

### GBP Crosses
| Asset | Pip | T1 Trigger | T2 Trigger | T3 Trigger | T1→T2 Shift | Gear Shift to T3 |
|-------|-----|------------|------------|------------|-------------|-----------------|
| GBP/JPY | 0.01 | ≥23p | ≥44p | ≥85p | impulse≥23p | impulse≥85p |
| GBP/AUD | 0.0001 | ≥17p | ≥29p | ≥50p | impulse≥17p | impulse≥50p |
| GBP/NZD | 0.0001 | ≥18p | ≥32p | ≥61p | impulse≥18p | impulse≥61p |
| GBP/CHF | 0.0001 | ≥16p | ≥28p | ≥53p | impulse≥16p | impulse≥53p |
| CHF/JPY | 0.01 | ≥17p | ≥29p | ≥50p | impulse≥17p | impulse≥50p |

### Indices, Metals, Crypto
| Asset | Pip | T1 Trigger | T2 Trigger | T3 Trigger | T1→T2 Shift | Gear Shift to T3 |
|-------|-----|------------|------------|------------|-------------|-----------------|
| US500 | 1.0 | ≥25 pts | ≥47 pts | ≥90 pts | impulse≥25pts | impulse≥90pts |
| NAS100 | 1.0 | ≥41 pts | ≥77 pts | ≥146 pts | impulse≥41pts | impulse≥146pts |
| DE30 | 1.0 | ≥23 pts | ≥44 pts | ≥85 pts | impulse≥23pts | impulse≥85pts |
| FR40 | 1.0 | ≥23 pts | ≥44 pts | ≥85 pts | impulse≥23pts | impulse≥85pts |
| HK50 | 1.0 | ≥110 pts | ≥204 pts | ≥390 pts | impulse≥110pts | impulse≥390pts |
| XAU/USD | 1.0 | ≥19 pts | ≥35 pts | ≥58 pts | impulse≥19pts | impulse≥58pts |
| XAG/USD | 0.01 | ≥8.5 pts | ≥14.5 pts | ≥25 pts | impulse≥8.5pts | impulse≥25pts |
| ETH/USD | 1.0 | ≥42 pts | ≥52 pts | ≥65 pts | impulse≥50pts | impulse≥62pts |
| BTC/USD | 1.0 | ≥246 pts | ≥654 pts | ≥1392 pts | impulse≥246pts | impulse≥1392pts |

---

## 16. UNIVERSAL GEAR SHIFT RULE

**When the session's first impulse exceeds the NEXT tier's trigger threshold, the field has intraday-reclassified. Use the shifted tier's Atomic Unit as target.**

- SL remains at OCC extreme (zero buffer, close-only) — no change to risk logic
- This is a pure expectancy upgrade
- Non-shifted days: run original day-tier AU at 89-92% WR
- Shifted days: run mirrored AU at 85-91% WR with significantly higher R-multiple
- T1→T2 is the primary alpha source on ALL assets (59% of all shifts)

---

## 17. PORTFOLIO DEPLOYMENT — THREE MONSTERS

### Portfolio Allocation
| Asset | Weight | Rationale |
|-------|--------|-----------|
| EUR/USD | 40% | Highest Sharpe (4.82), lowest ruin, cleanest structure |
| ETH/USD | 35% | Strong balance of WR and frequency |
| BTC/USD | 25% | Highest absolute PnL but widest variance |

### Portfolio Monte Carlo (40/35/25, 0.75% risk each)
| Metric | Value |
|--------|-------|
| Median CAGR | 448% |
| Max DD 95th Pctile | 6.8% |
| Trailing Ruin (6% DD) | 0.6% |
| EUR-ETH Correlation | 0.34 |
| EUR-BTC Correlation | 0.22 |
| ETH-BTC Correlation | 0.68 |
| Ruin Reduction | 68% lower than single-asset |

### Universal Execution Rules
```
1. SL = EXACT OCC Extreme (zero buffer, close-only invalidation)
2. IF impulse >= next tier trigger → USE shifted tier AU as target
3. IF impulse < next tier trigger  → USE original day-tier AU
4. Hard exit: 12:00 PM EST
5. Regime filter: 9AM checkpoint — reduce size 50% if FAILED
6. BTC/ETH: add spread filter
7. BTC: Option A only — no continuous loop stacking
```

### Risk Settings & Loss Protocol
| Account Type | Risk/Trade | Daily Loss Limit | Consec Losses → Action |
|-------------|------------|------------------|----------------------|
| Prop Trailing (6% DD) | 0.75% | 0.40% | 3 consecutive → check filters |
| Prop Static (10% DD) | 1.00% | 1.0% | 4 consecutive → quarterly noise |
| Personal (30% DD) | 1-2% | 2-3% | 5+ → reduce to 0.75% |

### Intraday Loss Streak Protocol
| Losses | Action |
|--------|--------|
| 1-2 | Execute next qualified setup normally |
| 3 | Continue — monthly median event |
| 4 | Check: Spread? News? Regime FAILED? |
| 5 | Reduce risk to 0.50% for remainder |
| 6+ | Stand down for the session |

**The edge is structural, not discretionary. If it qualifies, you execute.**

---

## 18. DISTRIBUTION SYMMETRY TRAP — MULTI-ASSET BACKTEST (11 ASSETS)

| Asset | Trades | Win Rate | Avg PnL |
|-------|--------|----------|---------|
| EUR/USD | 892 | 86.4% | +12.4 pips |
| USD/CHF | 870 | 85.8% | +11.8 pips |
| ETH/USD | 920 | 84.2% | +42.3 pts |
| BTC/USD | 940 | 83.1% | +218 pts |
| XAU/USD | 880 | 86.2% | +24.6 pts |
| NAS100 | 910 | 85.3% | +58.4 pts |
| DE30 | 870 | 86.1% | +52.3 pts |
| FR40 | 860 | 85.7% | +51.8 pts |
| HK50 | 890 | 84.4% | +142 pts |
| CHF/JPY | 850 | 85.2% | +18.4 pips |
| XAG/USD | 820 | 84.1% | +9.2 pips |

**Win rates cluster 83-86% across all 11 assets — forex, crypto, metals, indices. Fractal pattern.**

### Overall Metrics
| Metric | Value |
|--------|-------|
| Total Return | +579% ($10k → $67,924) |
| Max Drawdown | 3.9% |
| Profit Factor | 3.82 |
| Avg Trade Duration | 3.4 hours |

---

## 19. DISTRIBUTION SYMMETRY TRAP — EXECUTION PROTOCOL

### Pre-Session (2:45 AM EST)
- Measure Asian Range (7PM-3AM) → Classify Tier
- Mark Asian High/Low

### Layer 1 — Bias Lock (3AM-12PM)
- Wait for FIRST M5 CLOSE outside Asian band
- LONG if close > Asian High | SHORT if close < Asian Low

### Layer 2 — Atomic Entry
- Wait for impulse candle in bias direction (body >= AU x 0.5)
- Wait for NEXT candle to close OPPOSITE direction
- Enter MARKET on pullback candle close

### Layer 3 — Targets
- T25 (AR x 0.25) → Close 50%
- T50 (AR x 0.50) → Close 40%
- T100 (AR x 1.00) → Close remaining 10% runner
- Move SL to breakeven after T25

### Position Sizing
| Parameter | Value |
|-----------|-------|
| Risk per trade | 0.25% |
| Max daily loss | 1.0% (4 trades x 0.25%) |
| Bias filter | First M5 band close (reduces false signals ~22%) |

---

## 20. POST-TARGET REVERSAL ANALYSIS

### Reversal Rates by Target
| Target | Opp -25% Hit | Band Retest | Full Reversal |
|--------|-------------|-------------|---------------|
| -25% | 3.8% | 22.4% | **4.2%** |
| -50% | 2.1% | 12.6% | **2.8%** |
| -85% | 1.4% | 8.4% | **1.9%** |

### By Tier (All Targets Combined)
| Tier | Full Reversal | Mode |
|------|--------------|------|
| T1 | 2.6% | Aggressive holding |
| T2 | 3.4% | Standard management |
| T3 | 6.2% | Defensive — take profit at first target |

### By Hour of Target Touch (EST)
| Hour | Full Rev | Note |
|------|---------|------|
| 3-4 AM | 1.6% | Cleanest delivery — hold runners |
| 4-5 AM | 2.2% | High conviction |
| 5-6 AM | 3.4% | Degradation begins |
| 6-8 AM | 4.8% | US pre-open noise |
| 8-10 AM | 6.4% | Significant decay |
| 10 AM-12 PM | 9.6% | Edge decay zone |

**81.2% rule does NOT apply to completed targets** — only to failed breakouts.

---

## 21. REVERSE ATOMIC DELIVERY MAP

### First Internal Level After Reversal
| Target | 38.2% Fib | 50% Fib | Combined |
|--------|-----------|---------|----------|
| -25% | 34.6% | 28.8% | **63.4%** |
| -50% | 38.4% | 32.2% | **70.6%** |
| -85% | 42.6% | 30.4% | **73.0%** |

**The 38.2-50% zone absorbs 63-73% of all post-target reversals.**

### Reverse Delivery Quantized to AUs (-25% target)
| Metric | Value |
|--------|-------|
| Avg Delivery | 11.8p |
| Matches T1 AU (10p) | 48.2% |
| Matches T2 AU (12p) | 32.6% |
| Matches 1.44x Shift | 12.4% |

---

*Extracted from CEREBUS FX v4 Complete Manual, Pages 139-214*
*This is the deepest layer of market analysis in the Cerebus framework.*
