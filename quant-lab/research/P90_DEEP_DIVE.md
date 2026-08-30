# P90 Deep Dive — Complete System Analysis

> **Source:** CEREBUS Manual v4.0 (April 2026) | EUR/USD M5 | 315,000+ Candles
> **Focus:** P90 Candle System — Definition, Cascade Activation, Tier System, Asian Range, Position Pyramid
> **Classification:** PROPRIETARY — For educational purposes only

---

## Table of Contents

1. [What Is a P90 Candle — Exact Definition](#1-what-is-a-p90-candle--exact-definition)
2. [P90 as Activation Signal](#2-p90-as-activation-signal)
3. [Cascade Activation Rules](#3-cascade-activation-rules)
4. [45-Minute Add Rules](#4-45-minute-add-rules)
5. [Cascade + 45-Min Add Combination](#5-cascade--45-min-add-combination)
6. [Tier System (T1/T2/T3)](#6-tier-system-t1t2t3)
7. [Asian Range Calculation](#7-asian-range-calculation)
8. [Position Pyramid Rules](#8-position-pyramid-rules)
9. [Constraint Boundary Optimization](#9-constraint-boundary-optimization)
10. [P90P Window Distribution Tracker](#10-p90p-window-distribution-tracker)
11. [Implementation Specification](#11-implementation-specification)

---

## 1. What Is a P90 Candle — Exact Definition

### Formal Definition
A **P90 candle** is an M5 (5-minute) candle that:
1. **Closes** within the Activation Window (2:00 AM – 11:00 AM EST)
2. Meets or exceeds the **body-size threshold** for its specific time sub-window
3. **Closes outside** the Asian constraint band (above Asian High for bullish, below Asian Low for bearish)

### Body-Size Thresholds by Time Window

| Time Window (EST) | Body Threshold | Rationale |
|-------------------|---------------|-----------|
| 2:00 – 4:00 AM | **>= 4.1 pips** | Early London — lower volatility, tighter threshold |
| 4:00 – 6:00 AM | **>= 4.6 pips** | London session ramping — moderate threshold |
| 6:00 – 8:00 AM | **>= 4.6 pips** | London-NY overlap begins — same threshold |
| 8:00 – 10:00 AM | **>= 5.9 pips** | NY session open — higher volatility, wider threshold |
| 10:00 – 11:00 AM | **>= 6.2 pips** | Late window — highest threshold, edge thinning |

### Critical Rules
- **Close only:** The candle must **CLOSE** outside the Asian band. Wicks do not count.
- **Body size:** Measured as |Close – Open| of the M5 candle.
- **Direction:** Bullish P90 = Close > Asian High. Bearish P90 = Close < Asian Low.
- **One per direction per window:** Multiple P90s can fire in the same direction (these become cascades). Opposite-direction P90s are generally ignored.

### What P90 Is NOT
- It is NOT any large candle — it must close outside the Asian band
- It is NOT a wick-based signal — only closes matter
- It is NOT a standalone prediction — it is an **activation signal** marking the start of a new constraint-resolution process
- It is NOT valid after 11:00 AM EST — the activation window closes

---

## 2. P90 as Activation Signal

### Role in the Constraint-System Framework

In CEREBUS vocabulary, the P90 candle is an **Activation Signal [9]** — a defined condition showing that a new constraint-resolution process has started. It marks the transition from the Asian session's constraint deficit to the London/NY session's resolution output.

### Signal Hierarchy

```
Asian Range (Constraint Deficit) 
    → P90 Candle (Activation Signal)
        → Direction of Constraint Resolution Established
            → Cascade P90s (Momentum Confirmation)
                → 45-Min Add (Time-Based Confirmation)
```

### First P90 = Bias Setter
The **first P90** in the 2:06 AM EST window sets the **direction of constraint resolution [3]** for the entire session. All subsequent P90s in the same direction are valid cascade activations. Opposite-direction P90s are ignored unless a full regime reversal is confirmed (both 200% Deep State AND 132% Kill-Switch triggered).

---

## 3. Cascade Activation Rules

### Definition
A **Cascade P90** is a subsequent P90 candle in the **same direction of constraint resolution** that occurs within 120 minutes of the Initial P90.

### Cascade Activation Protocol

| Step | Action | Timing | Condition | Size | Boundary |
|------|--------|--------|-----------|------|----------|
| 1 | Initial P90 | 2-11 AM EST | P90 close >= threshold | 40% | 80% of P90 body |
| 2 | 45-Min Add | +45 min from Signal 1 | Resolution output +8 pips | 30% | Breakeven (Signal 1) |
| 3 | Cascade P90 (1st) | 30-90 min from Signal 1 | New P90 same direction | 20% | 168% of THIS P90 body |
| 4 | Cascade P90 (2nd) | 60-90 min from Signal 1 | New P90 same direction | 10% | 168% of THIS P90 body |

### Cascade Validation — VALID

- ✅ Same direction of constraint resolution [3]
- ✅ Within 90 minutes of Initial P90 (optimal: 45-60 min)
- ✅ Before 11:00 AM EST
- ✅ Asian Range < 45 pips
- ✅ -25% / -50% targets NOT already hit
- ✅ 132% Kill-Switch NOT triggered
- ✅ Max 3 cascades per session

### Cascade Validation — INVALID

- ❌ Opposite direction of constraint resolution
- ❌ More than 90 minutes after Initial P90
- ❌ After 11:00 AM EST
- ❌ Asian Range > 45 pips
- ❌ -25% / -50% targets already hit
- ❌ 132% Kill-Switch already triggered
- ❌ 4th+ cascade attempt (resolution exhausted)
- ❌ Major news within 60 minutes

### Cascade Performance Statistics

| Cascade # | Signals | Win Rate | Avg Extension | Avg Hold | Conflict Rate | Recommendation |
|-----------|---------|----------|---------------|----------|---------------|----------------|
| 1st (Initial) | 3,262 | 83.3% | 18.4p | 89 min | 16.7% | Baseline |
| 2nd | 1,847 | **87.8%** | 22.6p | 76 min | 12.2% | **BEST** |
| 3rd | 892 | 84.2% | 19.8p | 82 min | 15.8% | Good |
| 4th+ | 318 | 76.4% | 16.2p | 94 min | 23.6% | **AVOID** |

**Why the 2nd Cascade Outperforms:**
1. Direction already validated by 1st P90
2. Still early in session — resolution deficit has room to expand
3. 168% Constraint Boundary allows normal partial rebalancing
4. Net EV: 168% boundary is +0.32R better than 80% boundary

### Cascade Timing Analysis

| Time After 1st P90 | Signals | Win Rate | Avg Extension | Recommendation |
|-------------------|---------|----------|---------------|----------------|
| 15-30 min | 412 | 82.4% | 19.8p | Too soon — resolution not confirmed |
| 30-45 min | 687 | 86.8% | 21.4p | Good |
| **45-60 min** | **524** | **88.2%** | **23.2p** | **BEST — Resolution Sweet Spot** |
| 60-90 min | 224 | 85.4% | 20.8p | Good |
| 90-120 min | 98 | 79.8% | 17.4p | Late — Reduce size |

### Cascade Timeline Example

```
2:30 AM: P90 LONG activation (4.2p) → Signal 1 @ 1.0850
         Constraint Boundary: 1.0847 (80% of 4.2p = 3.4p)
         Direction of Constraint Resolution: LONG established

3:15 AM: P90 LONG activation (5.1p) → Signal 2 @ 1.0858
         Constraint Boundary: 1.0849 (168% of 5.1p = 8.6p) ← WIDER
         Same direction = VALID CASCADE

4:00 AM: P90 LONG activation (4.8p) → Signal 3 @ 1.0865
         Constraint Boundary: 1.0857 (168% of 4.8p = 8.1p)
         Same direction = VALID CASCADE

4:45 AM: P90 SHORT prints (5.2p) → IGNORE
         Opposite direction of constraint resolution = NOT VALID

12:00 PM: HARD EXIT — Close ALL positions
```

---

## 4. 45-Minute Add Rules

### Definition
The **45-Min Add** is a time-based (not signal-based) position addition that triggers 45 minutes after the Initial P90 if the resolution output has extended by +8 pips.

### Rules

| Parameter | Value |
|-----------|-------|
| Trigger | +45 minutes from Initial P90 AND resolution output +8 pips |
| Size | 30% of total risk |
| Constraint Boundary | Breakeven (Signal 1 output level) |
| Target | -50% Asian Range |
| Max per session | 1 |

### Cascade vs 45-Min Add Comparison

| Metric | 45-Min Add (Original) | Cascade P90 (New) | Winner |
|--------|----------------------|-------------------|--------|
| Trigger | Time-based (+45 min) | Signal-based (new P90) | Cascade |
| Condition | Resolution output +8p | New P90 candle | Cascade |
| Win Rate | 91.2% | 87.8% | 45-Min Add |
| Frequency | 64.3% of signals | 56.6% of signals | 45-Min Add |
| Boundary Method | Breakeven | 168% of new P90 | Cascade |
| Avg Extension | 26.8 pips | 22.6 pips | 45-Min Add |
| Combined Win Rate | — | — | **93.4% (both)** |

**Key Insight:** The 45-Min Add and Cascade P90 are **complementary, not competing**. They capture different aspects of the same resolution process. When both trigger, the combined win rate is **93.4%**.

---

## 5. Cascade + 45-Min Add Combination

### Three Scenarios

**When BOTH Trigger (Highest Resolution Conviction):**
- Signal 1: Initial P90 (40% size)
- Signal 2: 45-Min Add (30% size)
- Signal 3: Cascade P90 (30% size)
- Total: 100% size across 3 activations
- **Combined Win Rate: 93.4%**

**When ONLY 45-Min Triggers:**
- Signal 1: Initial P90 (50% size)
- Signal 2: 45-Min Add (50% size)

**When ONLY Cascade Triggers:**
- Signal 1: Initial P90 (50% size)
- Signal 2: Cascade P90 (50% size)

---

## 6. Tier System (T1/T2/T3)

### Asian Range Tier Classification

| Asian Range | Tier | Conviction | Position Size | Expected Daily Range | Expansion Factor |
|-------------|------|------------|---------------|---------------------|-----------------|
| < 20 pips | **T1 (Gold)** | Full | 100% | ~72 pips | 3.12x |
| 20 – 30 pips | **T2 (Standard)** | Moderate | 75% | ~58 pips | 2.68x |
| 30 – 45 pips | **T3 (Caution)** | Reduced | 50% | ~48 pips | 2.18x |
| > 45 pips | **NO-GO** | Skip | 0% | N/A | — |

### Tier Performance by Cascade

| Metric | T1 (<20p) | T2 (20-30p) | T3 (30-45p) |
|--------|-----------|-------------|-------------|
| Anchor Win Rate | 98.6% | 89.1% | 76.2% |
| Anchor Avg R | +1.68R | +1.24R | +0.88R |
| Amplifier WR (Aligned) | 86.2% | 79.4% | N/A |
| Cascade Max | 2 Amplifiers | 1 Amplifier | 0 Amplifiers |
| Combined Daily R | +2.68R | +1.82R | +1.35R |

### Tier-Specific Rules

**T1 (Gold) — Aggressive Deployment:**
- Up to 2 Amplifiers per Anchor
- Amplifier entry zones: 32% or 50% partial rebalancing
- Win Rate with Dual-Engine: 91%
- If overfilled (>40p by 9 AM): Anchor-only at 50% size

**T2 (Standard) — Standard Deployment:**
- Max 1 Amplifier per Anchor
- Amplifier entry zone: 50% partial rebalancing ONLY
- Skip entirely if overfilled (>40 pips by 9 AM EST)

**T3 (Caution) — Defensive / Pure Anchor:**
- NO AMPLIFIERS under any circumstances
- Use Model 2 protocol: 2-hour confirmation after break
- Size: 50-75% of normal risk
- If overfilled: STAND DOWN

### Target Trimming by Tier

**T1 (Asian < 20 pips):**
- TP1 (Asian -25%): ~5 pips → Trim 20%
- TP2 (Asian -50%): ~10 pips → Trim 50%
- TP3 (Daily -50%): ~36 pips → Trim 25%
- Runner (Daily -100%): ~72 pips → Hold 5%

**T2 (Asian 20-30 pips):**
- TP1 (Asian -25%): ~6 pips → Trim 20%
- TP2 (Asian -50%): ~12 pips → Trim 50%
- TP3 (Daily -50%): ~29 pips → Trim 30%
- Runner: Skip (edge thin)

**T3 (Asian 30-45 pips):**
- TP1 (Asian -25%): ~9 pips → Trim 30%
- TP2 (Asian -50%): ~18 pips → Trim 70%
- TP3+: Skip entirely

---

## 7. Asian Range Calculation

### Definition
The **Asian Range** is the distance between Asian High and Asian Low during the Asian session.

### Calculation Parameters

| Parameter | Value |
|-----------|-------|
| Session Start | 00:00 UTC (7:00 PM EST previous day) |
| Session End | 08:00 UTC (3:00 AM EST) |
| Measurement | MAX(High) – MIN(Low) across all M5 candles in window |
| Classification | T1/T2/T3/NO-GO per tier thresholds |

### Asian Range as Constraint Deficit
The Asian Range represents the **Constraint Deficit [11]** — the field is under-resolved during the Asian session and must expand to reach its daily mean variance. This is the "coiled spring" mechanic.

### Statistical Properties

| Metric | T1 (<20p) | T2 (20-30p) | T3 (30-45p) | All Tiers |
|--------|-----------|-------------|-------------|-----------|
| Expected Daily Range | ~72p | ~58p | ~48p | — |
| Expansion Factor | 3.12x | 2.68x | 2.18x | — |
| Weekly Expansion (mean) | — | — | — | 6.62x |
| Weekly Expansion (median) | — | — | — | 5.95x |

### Asian Range Float Statistics

**Daily Float (price never re-enters Asian band):**
- Broad float: 18.8% of all days
- Shallow float (<=38% partial rebalancing, no re-entry): 2.9%
- Float day median partial rebalancing: 14.4 pips from initial peak
- Float day 90th percentile rebalancing: 36.8 pips (constraint boundary upper bound)
- Float day median buffer from band: 8.4 pips

**Weekly Float (Monday Asian band holds):**
- Tue Asian float (T1): 71.1%
- Tue Asian float (T2): 54.5%
- True 24h float (T2): 37.9% — HIGHEST
- 48h float (T2): 25.8%

---

## 8. Position Pyramid Rules

### Standard Pyramid (Base 80 Play)

```
Signal 1 (Initial P90):  40% size | Boundary: 80% of P90 body
Signal 2 (Simultaneous): 40% size | Boundary: 1.5x P90 body
Signal 3 (45-Min Add):   20% size | Boundary: Breakeven
```

### Cascade Pyramid (Full Deployment)

```
Signal 1 (Initial P90):  40% size | Boundary: 80% of P90 body
Signal 2 (45-Min Add):    30% size | Boundary: Breakeven
Signal 3 (Cascade P90):   20% size | Boundary: 168% of new P90 body
Signal 4 (Cascade 2):     10% size | Boundary: 168% of new P90 body
```

### Dual-Engine Pyramid

**T1 (Gold):**
```
Constraint Anchor: 60% | Boundary: Opposite Asian extreme
Resolution Amp 1:  20% | Boundary: 80% Fib of P90 | Target: 20p fixed
Resolution Amp 2:  20% | Boundary: 80% Fib of P90 | Target: 20p fixed
```

**T2 (Standard):**
```
Constraint Anchor: 70% | Boundary: Opposite Asian extreme
Resolution Amp 1:  30% | Boundary: 80% Fib of P90 | Target: 20p fixed
```

**T3 (Caution):**
```
Constraint Anchor: 100% | Boundary: Opposite Asian extreme | Model 2 protocol
NO AMPLIFIERS
```

### Position Sizing Example ($10,000 account, 0.12% risk per activation)

| Signal | Size % | $ Risk | Boundary | Units |
|--------|--------|--------|----------|-------|
| Initial P90 | 40% | $4.00 | 80% of 4.2p = 3.4p | 11,764 |
| 45-Min Add | 30% | $3.00 | Breakeven | — |
| Cascade P90 | 20% | $2.40 | 168% of 5.1p = 8.6p | 2,790 |
| Cascade 2 | 10% | $1.20 | 168% of 4.8p = 8.1p | — |
| **TOTAL** | **100%** | **$7.60 (0.076%)** | Mixed | — |

**Max concurrent risk:** $36 (0.36%) — well under the limit.

---

## 9. Constraint Boundary Optimization

### Boundary Methods Compared (Cascade Context)

| Boundary Method | Win Rate | Avg Distance | Conflict Rate | R:R | Recommendation |
|----------------|----------|-------------|---------------|-----|----------------|
| 80% Fib (Standard) | 83.3% | 6.4p | 16.7% | 1:2.9 | Too tight for cascade |
| 1.5x Candle | 85.8% | 7.8p | 14.2% | 1:2.9 | Good |
| **168% Fib (Stall Zone)** | **87.8%** | **8.6p** | **12.2%** | **1:2.6** | **BEST for cascade** |
| 200% Fib | 88.2% | 10.2p | 11.8% | 1:2.2 | Too wide |

### Why 168% Stall Zone Is Optimal for Cascade

- Standard 80% Fib: Good for initial activation, too tight for cascade partial rebalancing
- Cascade 168% Stall Zone: 8.6p avg, conflict rate 12.2% (-4.5% vs standard)
- Net EV: 168% boundary is **+0.32R better** than 80% boundary
- Trade-off: Lower R:R (1:2.6) but HIGHER win rate (+4.5%)

### Fibonacci Extension States (Constraint Boundaries)

| Level | State | Action |
|-------|-------|--------|
| 168% | Stall Zone State | Watch for Binary Activation / Limit Order |
| 200% | Deep State | Limit Activation (constraint boundary +8p) |
| 220% | Violation State | Hard Constraint Boundary / Exit All |
| 132% (of Asian) | Kill-Switch State | Kill Switch — Close All Immediately |

---

## 10. P90P Window Distribution Tracker

### Enhanced Core Formula

**P90P WINDOW** = 7:00 PM EST (Day N-1) → 12:00 PM EST (Day N)

**FINAL TARGET** = Asian Range × Weighted Expansion Factor

**Weighted Expansion** = (Base Tier Factor × 0.40) + (Regime Adjustment × 0.25) + (P90 Confirmation × 0.20) + (Cascade Timing × 0.10) + (Time Decay × 0.05)

**PRECISION ZONE** = ±(Asian Range × Confidence Buffer)

### Tier Factors

| Asian Range Tier | Base Factor | Regime Boost | P90 Boost | Cascade Boost | Max Precision |
|-----------------|-------------|-------------|-----------|---------------|---------------|
| < 20 pips (T1) | 3.12x | +0.31x | +0.15x | +0.08x | ±2.5 pips |
| 20-30 pips (T2) | 2.68x | +0.27x | +0.13x | +0.07x | ±3.0 pips |
| 30-45 pips (T3) | 2.18x | +0.22x | +0.11x | +0.05x | ±3.5 pips |
| > 45 pips (NO-GO) | 1.52x | +0.00x | +0.00x | +0.00x | SKIP |

### 6:00 AM EST Checkpoint

| Tier | Base Expected at 6 AM | P90 Adjustment | Acceptable Zone | Confidence |
|------|----------------------|----------------|-----------------|------------|
| T1 | Asian × 2.03 | +0.10x | ±2.5 pips | 93-95% |
| T2 | Asian × 1.74 | +0.09x | ±3.0 pips | 90-92% |
| T3 | Asian × 1.42 | +0.07x | ±3.5 pips | 88-90% |

**Decision Rules:**
- In Zone + P90 Confirmed → HIGH CONFIDENCE (92-95%) → Target = Current ÷ 0.65 × 1.05
- In Zone + No P90 → MODERATE CONFIDENCE (88-90%) → Target = Current ÷ 0.65
- Below Lower Bound → Reduce target 8-12%
- Above Upper Bound → Take profits at -50%

### 9:00 AM EST Checkpoint (Key to 95% Accuracy)

**Regime Ratio** = Daily Range (3AM-9AM) ÷ Asian Range

| Regime | Ratio | Completion % | Final Target Formula | Precision | Accuracy |
|--------|-------|-------------|---------------------|-----------|----------|
| CONFIRMED | >= 1.50 | 90.2% | Current ÷ 0.902 | ±2.0-2.5p | 94-95% |
| CAUTION | 1.45-1.49 | 86.1% | Current ÷ 0.861 | ±2.5-3.0p | 90-92% |
| FAILED | < 1.45 | 73.8% | Current ÷ 0.738 × 0.90 | ±3.5-4.5p | 85-88% |

### Enhanced Formula (All Conditions Met)

**Final Target** = (Current Range ÷ Completion%) × Regime Boost

| Regime | Completion | Boost |
|--------|-----------|-------|
| CONFIRMED | 90.2% | ×1.10 |
| CAUTION | 86.1% | ×1.05 |
| FAILED | 73.8% | ×0.90 |

### Accuracy Breakdown

| Conditions | Accuracy Within | Hit Rate |
|-----------|----------------|----------|
| Pre-Session (Base Only) | ±10 pips | 78% |
| Pre-Session + P90 | ±7 pips | 84% |
| 6 AM + P90 | ±4 pips | 89% |
| 9 AM + Regime CONFIRMED | ±3 pips | 91% |
| 9 AM + Regime + P90 | ±2.5 pips | **94-95%** |
| 11 AM (All Conditions) | ±2 pips | 96% |

---

## 11. Implementation Specification

### P90 Detector — Pseudocode

```python
class P90Detector:
    """
    Detects P90 candles and manages cascade activation state.
    """
    
    # Body size thresholds by time window (EST)
    THRESHOLDS = {
        (2, 4): 4.1,    # 2:00-4:00 AM
        (4, 6): 4.6,    # 4:00-6:00 AM
        (6, 8): 4.6,    # 6:00-8:00 AM
        (8, 10): 5.9,   # 8:00-10:00 AM
        (10, 11): 6.2,  # 10:00-11:00 AM
    }
    
    def __init__(self, asian_high: float, asian_low: float):
        self.asian_high = asian_high
        self.asian_low = asian_low
        self.initial_p90_time = None
        self.initial_p90_direction = None
        self.cascade_count = 0
        self.max_cascades = 3
        self.cascade_window_min = 30   # min minutes after initial
        self.cascade_window_max = 90   # max minutes after initial
        self.optimal_cascade_min = 45  # optimal window start
        self.optimal_cascade_max = 60  # optimal window end
    
    def get_threshold(self, est_hour: float) -> float:
        """Return the P90 body threshold for a given EST hour."""
        for (start, end), threshold in self.THRESHOLDS.items():
            if start <= est_hour < end:
                return threshold
        return None  # Outside activation window
    
    def check_p90(self, candle: dict) -> dict:
        """
        Check if an M5 candle qualifies as P90.
        
        Args:
            candle: {open, high, low, close, timestamp}
        
        Returns:
            {is_p90: bool, direction: 'LONG'|'SHORT'|None, 
             body_size: float, is_cascade: bool, cascade_num: int}
        """
        est_hour = get_est_hour(candle['timestamp'])
        threshold = self.get_threshold(est_hour)
        
        if threshold is None:
            return {'is_p90': False}
        
        body_size = abs(candle['close'] - candle['open'])
        
        # Check close outside Asian band
        is_bullish = candle['close'] > self.asian_high
        is_bearish = candle['close'] < self.asian_low
        
        if not (is_bullish or is_bearish):
            return {'is_p90': False}
        
        if body_size < threshold:
            return {'is_p90': False}
        
        direction = 'LONG' if is_bullish else 'SHORT'
        
        # Check if this is initial or cascade
        is_cascade = False
        cascade_num = 0
        
        if self.initial_p90_time is None:
            # First P90 — Bias Setter
            self.initial_p90_time = candle['timestamp']
            self.initial_p90_direction = direction
            cascade_num = 1
        else:
            # Check cascade validity
            minutes_elapsed = (candle['timestamp'] - self.initial_p90_time).minutes
            
            if (direction == self.initial_p90_direction and
                self.cascade_count < self.max_cascades and
                self.cascade_window_min <= minutes_elapsed <= self.cascade_window_max):
                
                is_cascade = True
                self.cascade_count += 1
                cascade_num = self.cascade_count + 1
            else:
                # Invalid cascade — opposite direction or too late
                return {'is_p90': True, 'direction': direction, 
                        'body_size': body_size, 'is_cascade': False,
                        'cascade_num': 0, 'valid': False}
        
        return {
            'is_p90': True,
            'direction': direction,
            'body_size': body_size,
            'is_cascade': is_cascade,
            'cascade_num': cascade_num,
            'valid': True,
            'in_optimal_window': (self.optimal_cascade_min <= minutes_elapsed 
                                  <= self.optimal_cascade_max) if is_cascade else None
        }
    
    def get_boundary(self, p90_body_size: float, is_cascade: bool) -> float:
        """Calculate constraint boundary distance from entry."""
        if is_cascade:
            return p90_body_size * 1.68  # 168% Stall Zone
        else:
            return p90_body_size * 0.80  # 80% Fib
    
    def get_position_size(self, is_cascade: bool, cascade_num: int, 
                          total_risk_pct: float) -> float:
        """Calculate position size as percentage of total risk."""
        if not is_cascade:
            return total_risk_pct * 0.40  # Initial P90: 40%
        
        if cascade_num == 2:
            return total_risk_pct * 0.20  # 1st Cascade: 20%
        elif cascade_num == 3:
            return total_risk_pct * 0.10  # 2nd Cascade: 10%
        
        return 0.0
```

### Cascade State Machine

```python
class CascadeStateMachine:
    """
    Manages the full P90 cascade lifecycle.
    
    States:
        IDLE → Waiting for first P90
        INITIAL_P90 → First P90 detected, direction set
        CASCADE_WAIT → Watching for cascade P90s (30-90 min window)
        POSITION_ACTIVE → Positions open, managing exits
        HARD_EXIT → 12:00 PM EST, all positions closed
        KILL_SWITCH → 132% violation, emergency exit
    """
    
    STATES = ['IDLE', 'INITIAL_P90', 'CASCADE_WAIT', 
              'POSITION_ACTIVE', 'HARD_EXIT', 'KILL_SWITCH']
    
    def __init__(self, asian_high, asian_low, asian_range, tier):
        self.detector = P90Detector(asian_high, asian_low)
        self.state = 'IDLE'
        self.positions = []
        self.direction = None
        self.asian_range = asian_range
        self.tier = tier
        self.tp1_hit = False
        self.tp2_hit = False
    
    def calculate_targets(self, entry_price, direction):
        """Calculate TP1 and TP2 based on Asian Range."""
        if direction == 'LONG':
            tp1 = entry_price + (self.asian_range * 0.25)
            tp2 = entry_price + (self.asian_range * 0.50)
        else:
            tp1 = entry_price - (self.asian_range * 0.25)
            tp2 = entry_price - (self.asian_range * 0.50)
        return tp1, tp2
    
    def check_kill_switch(self, current_price, direction):
        """Check if 132% of Asian Range is violated."""
        if direction == 'LONG':
            kill_level = self.detector.asian_high - (self.asian_range * 1.32)
            return current_price < kill_level
        else:
            kill_level = self.detector.asian_low + (self.asian_range * 1.32)
            return current_price > kill_level
    
    def check_45_min_add(self, current_price, direction, minutes_elapsed, signal1_price):
        """Check if 45-min add conditions are met."""
        if minutes_elapsed >= 45:
            if direction == 'LONG':
                return current_price >= signal1_price + 8  # +8 pips
            else:
                return current_price <= signal1_price - 8
        return False
```

### Key Parameters Summary for Nautilus Trader

```python
P90_CONFIG = {
    # Time windows (EST)
    'activation_window_start': '02:00',
    'activation_window_end': '11:00',
    'hard_exit_time': '12:00',
    
    # Body thresholds by window (pips)
    'thresholds': {
        '02:00-04:00': 4.1,
        '04:00-06:00': 4.6,
        '06:00-08:00': 4.6,
        '08:00-10:00': 5.9,
        '10:00-11:00': 6.2,
    },
    
    # Cascade parameters
    'max_cascades': 3,
    'cascade_window_min_minutes': 30,
    'cascade_window_max_minutes': 90,
    'optimal_cascade_min_minutes': 45,
    'optimal_cascade_max_minutes': 60,
    
    # Position sizing
    'initial_p90_size': 0.40,
    'cascade_1_size': 0.20,
    'cascade_2_size': 0.10,
    '45_min_add_size': 0.30,
    
    # Constraint boundaries
    'initial_boundary_pct': 0.80,    # 80% of P90 body
    'cascade_boundary_pct': 1.68,    # 168% of P90 body (Stall Zone)
    
    # Targets (as fraction of Asian Range)
    'tp1_pct': 0.25,
    'tp2_pct': 0.50,
    'daily_target_pct': 0.50,
    
    # Risk limits
    'risk_per_activation': 0.0012,   # 0.12% of equity
    'max_concurrent_risk': 0.0036,   # 0.36% of equity
    'daily_hard_stop': 0.0040,       # 0.40% of equity
    'kill_switch_pct': 1.32,         # 132% of Asian Range
    
    # Tier thresholds (pips)
    't1_threshold': 20,
    't2_threshold': 30,
    't3_threshold': 45,
    
    # Tier position sizing
    't1_size': 1.00,
    't2_size': 0.75,
    't3_size': 0.50,
}
```

---

*PDocument generated from CEREBUS FX v4.0 Manual (April 2026). All data derived from EUR/USD M5, Jan 2022 – Apr 2026, 315,000+ candles. For educational purposes only. Test all strategies in simulation before live deployment.*
