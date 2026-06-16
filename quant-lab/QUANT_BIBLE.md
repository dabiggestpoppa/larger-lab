# 📖 THE QUANT BIBLE — CEREBUS Trading System

> **Compiled:** 2026-06-16
> **Source:** OC2 Telegram chat export + `cost_analysis_all.json` + `SWEEP_MATRIX_V2.md` + `run_9k_config_results.json` + Symmetry Trap reports + DMR reports + CEREBUS full reports + Group Combinatorics + P90 v2 backtest + Holy Grail PDF extraction
> **Purpose:** Single source of truth for all trading configs, formulas, results, and deployment parameters
> **⚠️ RULE #1: NEVER TOUCH THE ENGINE FOR A TEST. ALWAYS CLONE/WRAP. ENGINE IS SACRED.**

---

## ⚡ EXECUTIVE SUMMARY (June 16 Status)

### What's Done
- ✅ Sweep complete: 36 pairs (28 FX + 2 crypto + 2 metals + 4 indices), floor/ceiling/knee for all
- ✅ Cost-adjusted backtest complete (live MT5 spread + historical CSV)
- ✅ AU targets verified: per-asset (NOT universal EURUSD)
- ✅ 8 live execution bugs identified and documented
- ✅ Nautilus strategy diff documented (4 diffs from CSV engine)
- ✅ Symmetry Trap multi-asset backtest complete (18 assets, 11,437 trades)
- ✅ DMR standalone backtest complete (4Y, 284 trades)
- ✅ P90 Kinetic Engine 4Y backtest complete (1,038 trades, 78.7% WR, PF 3.09)
- ✅ Group combinatorics complete (36 pairs ranked by net profit)
- ✅ P90 v2 backtest complete (9,228 trades unlocked config)
- ✅ Holy Grail PDF extraction complete (decision trees, playbooks, pattern definitions)
- ✅ Macro feature engine complete (18 pattern detectors, 102 features/bar)
- ✅ 70/70 macro engine unit tests passing

### What's Blocked
- ⚠️ Spread values need historical CSV average (MAD directive) — current uses live MT5
- ⚠️ Nautilus validation not yet run
- ⚠️ LOW COST HEX config approved but NOT deployed (still running SIGN 7)
- ⚠️ Indices/metals commission suspicious (7 pips/trade at 0.01 lot)

---

## 📐 SECTION 1: CORE FORMULAS & CALCULATIONS

### 1.1 Atomic Unit (AU) Formula

```
AU = Asian Range (in pips) / 2
```

**Per-asset calibration:** Each asset has its own AU based on its own Asian Range distribution. NEVER use a universal AU across assets.

**Tier System (AR = Asian Range in pips):**
| Tier | AR Range | AU | Trigger (AU × 1.20) |
|------|----------|-----|----------------------|
| T1 | ≤ 20p | AR/2 | AU × 1.20 |
| T2 | ≤ 30p | AR/2 | AU × 1.20 |
| T3 | ≤ 45p | AR/2 | AU × 1.20 |
| NO-GO | > 45p | — | Skip session |

### 1.2 P90 Threshold Formula

```
P90 = 90th percentile of impulse size distribution (per asset, per tier)
```

**Calculation method:**
1. Collect all impulse sizes (M5 close beyond swing origin) for a given asset/tier
2. Sort by size
3. Take the 90th percentile value = P90 threshold
4. A P90 impulse = any impulse ≥ P90 threshold

**P90 Body** = |close - open| of the P90 candle
**P90 Impulse** = |close - swing origin| (total excursion)

### 1.3 Monday London Range (MLR) Formula

```
MLR Window: Monday 07:00-15:00 UTC (03:00-11:00 EST)
MLR High = max(high) during MLR window
MLR Low = min(low) during MLR window
MLR Range = MLR High - MLR Low
MLR Mid = MLR Low + (MLR Range / 2)
```

**Forward-fill:** MLR values are forward-filled from Monday 15:00 UTC through Friday (or until next Monday).

**Bias determination:**
- Bullish: MLR close > MLR Mid
- Bearish: MLR close < MLR Mid
- Neutral: MLR close = MLR Mid

### 1.4 Fibonacci Extension Targets (from MLR)

```
For BULLISH bias:
  Target(-25%) = MLR High + (0.25 × MLR Range)
  Target(-50%) = MLR High + (0.50 × MLR Range)
  Target(-100%) = MLR High + (1.00 × MLR Range)
  Target(-168%) = MLR High + (1.68 × MLR Range)
  Kill Switch(132%) = MLR Low - (1.32 × MLR Range)

For BEARISH bias:
  Target(-25%) = MLR Low - (0.25 × MLR Range)
  Target(-50%) = MLR Low - (0.50 × MLR Range)
  Target(-100%) = MLR Low - (1.00 × MLR Range)
  Target(-168%) = MLR Low - (1.68 × MLR Range)
  Kill Switch(132%) = MLR High + (1.32 × MLR Range)
```

### 1.5 132% Kill-Switch Formula

```
Kill Switch = price level where structural invalidation occurs
Bullish: KS = MLR_Low - 1.32 × MLR_Range
Bearish: KS = MLR_High + 1.32 × MLR_Range

Distance to KS (pips) = |close - KS_price| / pip_size
Distance to KS (%) = |close - KS_price| / MLR_Range
```

**Rekey State Machine:**
| State | Condition | Value |
|-------|-----------|-------|
| NORMAL | dist_to_KS > 30 pips | 0 |
| APPROACHING | 15 < dist_to_KS ≤ 30 pips | 1 |
| CRITICAL | dist_to_KS ≤ 15 pips | 2 |
| BREACHED | Price touches/crosses KS | 3 |
| REKEY_SEQUENCE | Post-breach, same day | 4 |

### 1.6 ILM (Impulse Level Monitor) Formula

```
Asian Session: 19:00-03:00 EST (00:00-08:00 UTC)
London Session: 03:00-09:00 EST (08:00-14:00 UTC)

Asian Range = max(high) - min(low) during Asian session
London Range = max(high) - min(low) during London session
Extension Ratio = London Range / Asian Range

ILM States:
  MISALIGNED: Extension Ratio < 1.0
  DAILY_ILM: 1.0 ≤ Extension Ratio < 1.5
  IELM: Extension Ratio ≥ 1.5
  WILM: Monday is DAILY_ILM or IELM → whole week = WILM

Impulse Direction:
  Bullish: London close > Asian midpoint
  Bearish: London close < Asian midpoint
```

### 1.7 Regime Ratio Formula

```
Regime Ratio = London Range / Asian Range

CONFIRMED: Ratio ≥ 1.50 (strong impulse)
CAUTION: 1.45 ≤ Ratio < 1.49 (weak impulse)
FAILED: Ratio < 1.45 (no impulse)
```

### 1.8 Asian Range Percentile (ARP) Formula

```
ARP = percentile rank of current AR vs. recent AR distribution (96-bar / 8h median)

Micro Phase 1 (Expanding): AR > median × 1.2
Micro Phase 2 (Contracting): AR < median × 0.8
Micro Phase 3 (Breakout): Neither expanding nor contracting
```

### 1.9 Density Zone Formula

```
Rolling Std = std(close, window=20)
Rolling Mean = mean(close, window=20)

Density Zone High = Rolling Mean + Rolling Std
Density Zone Low = Rolling Mean - Rolling Std

Compression Ratio = 1 - (2 × Rolling Std) / Recent Range
Recent Range = max(high, 20) - min(low, 20)

High compression: Ratio > 0.5 (tight consolidation)
```

### 1.10 Gamma Zone Formula

```
Gamma levels = Fibonacci extensions from swing points
Gamma 0.618 = Swing ± 0.618 × Impulse
Gamma 1.000 = Swing ± 1.000 × Impulse
Gamma 1.618 = Swing ± 1.618 × Impulse

Gamma Zone = price within ±5% of any gamma level
Gamma Direction: 1 (bullish zone), -1 (bearish zone), 0 (none)
```

### 1.11 NY Sweep Formula

```
NY Sweep Window: 07:00-08:00 UTC (03:00-04:00 EST)
Sweep = price makes new high/low during window then reverses

Bullish Sweep: Makes new low → closes above open (bear trap)
Bearish Sweep: Makes new high → closes below open (bull trap)
```

### 1.12 OCC (Order Close Confirmation) Formula

```
OCC Extreme High = max(close, lookback=20)
OCC Extreme Low = min(close, lookback=20)

At OCC Extreme: close == rolling max/min
OCC Direction: 1 (bullish extreme), -1 (bearish extreme), 0 (none)
```

### 1.13 Wednesday Bifurcation Formula

```
Wednesday PM Window: 12:00-16:00 UTC (08:00-12:00 EST)
Bifurcation Flag: 1 if Wednesday AND hour in [12, 13, 14, 15]

Stress Level:
  HIGH: dist_to_132 < 15 pips AND Wednesday PM
  MEDIUM: dist_to_132 < 30 pips AND Wednesday PM
  LOW: Wednesday PM only
```

### 1.14 Hard Exit Formula

```
Hard Exit Time: 12:00 PM EST (17:00 UTC)
Minutes to Hard Exit = (17:00 UTC - current_time) in minutes

Hard Exit Imminent: minutes_to_exit ≤ 30 AND minutes_to_exit > 0
All positions must be closed by 17:00 UTC. No exceptions.
```

### 1.15 Gear Shift Formula

```
Gear Shift = target modification signal
Triggered when: regime changes from CONFIRMED to FAILED (or vice versa)

Target Modifier:
  Bullish Gear Shift: TP moves from -25% to -50% AR
  Bearish Gear Shift: TP moves from -25% to -50% AR
```

### 1.16 Friday Asian Anchor (Crypto) Formula

```
For BTC/ETH (24/7 markets):
Friday Asian Anchor = Asian Range from Friday 00:00-08:00 UTC
Used as weekly anchor instead of MLR (no Monday-specific behavior in crypto)

Anchor High = max(high) during Friday Asian window
Anchor Low = min(low) during Friday Asian window
Forward-filled through Sunday
```

### 1.17 3-Leg Pattern Formulas

```
Alpha 3-Leg:
  Leg A: Impulse move (up or down)
  Leg B: Retraces 72% of Leg A (±5% tolerance)
  Leg C: Continuation in Leg A direction
  Min bars per leg: 3, Max bars per leg: 50

Beta 3-Leg:
  Same as Alpha but Leg B retraces 61.8% (golden ratio) of Leg A (±5% tolerance)

AB-CD:
  A→B: Impulse leg
  B→C: Retrace 38.2%-88.6% of A→B
  C→D: Extension 1.272-1.618× A→B
```

### 1.18 Fibonacci Retrace/Extension Level Formulas

```
Fib Retrace Levels (from impulse high to low):
  23.6% = High - 0.236 × Range
  38.2% = High - 0.382 × Range
  50.0% = High - 0.500 × Range
  61.8% = High - 0.618 × Range
  72.0% = High - 0.720 × Range
  78.6% = High - 0.786 × Range
  88.6% = High - 0.886 × Range

Fib Extension Levels (from impulse origin):
  100.0% = Origin + 1.000 × Impulse
  127.2% = Origin + 1.272 × Impulse
  132.0% = Origin + 1.320 × Impulse (kill switch level)
  161.8% = Origin + 1.618 × Impulse
  168.0% = Origin + 1.680 × Impulse
  200.0% = Origin + 2.000 × Impulse
  261.8% = Origin + 2.618 × Impulse

Nearest Fib Level = argmin(|close - fib_level| for all levels)
Dist to Nearest = min(|close - fib_level|)
```

### 1.19 Micro-Macro Phase Formula

```
Micro Phase (based on Asian Range):
  Phase 1 (Expanding): AR > 8h_median × 1.2 → volatility increasing
  Phase 2 (Contracting): AR < 8h_median × 0.8 → consolidation
  Phase 3 (Breakout): Neither → impulse in progress

Macro Phase (based on MLR + Regime):
  Phase 1 (Bullish Confirmed): bias=BULLISH AND regime_ratio ≥ 1.5
  Phase 2 (Bearish Confirmed): bias=BEARISH AND regime_ratio ≥ 1.5
  Phase 3 (Transition): regime_ratio < 1.45

Phase Alignment:
  1 = Micro and Macro agree (both bullish or both bearish)
  -1 = Micro and Macro disagree
  0 = No clear alignment
```

### 1.20 Deep State (DMR) Formula

```
Deep State = P90 close ± 200% of P90 body

Bull P90 → DMR SHORT at DS (high >= DS level)
Bear P90 → DMR LONG at DS (low <= DS level)

TP = P90 activation close (return to origin)
SL = 220% of P90 body from activation
Max 1 trade per day
```

### 1.21 Symmetry Trap Formula

```
Entry Pipeline (3 steps, all mandatory):
  1. Impulse: M5 close beyond Tier Trigger (AU × 1.20) from swing origin
  2. Retrace (DZ): Pullback ≥ 1 AU OR 38.2-50% Fib retracement
  3. OCC: M5 candle closes BACK in impulse direction

Trade Management:
  Entry: Close of OCC candle (limit, not market)
  SL: Zero-Buffer Impulse Extreme (close-only invalidation)
  TP: Exactly 1 AU from entry (single target, no ladder)

Option B — Continuous Loop: Up to 3-5 loops per session.
Engine resets swing origin after each trade exit.
Loop cap = 5 (safety max).

80% Kill Switch: M5 close past 80% of impulse leg = pathway VOID. Session terminated.
```

---

## 📊 SECTION 2: BACKTEST RESULTS

### 2.1 P90 Kinetic Engine — 4Y EURUSD (2023-07 to 2026-05)

**Data:** 216,820 bars, 911 sessions | **Account:** $85.26 | **Lot:** 0.01

| Metric | Value |
|--------|-------|
| **Total Trades** | **1,038** |
| **Win Rate** | **78.7%** |
| Wins / Losses | 817 / 221 |
| **Gross Profit** | +4,814.2 pips |
| **Gross Loss** | -1,559.3 pips |
| **Profit Factor** | **3.09** |
| Avg Trade | +3.14 pips |
| Avg R-Multiple | 0.84R |
| Max Drawdown | 72.2 pips |

**Per-Variant Breakdown:**
| Variant | Trades | WR | PnL | AvgR | % of Trades |
|---------|--------|-----|------|------|-------------|
| INITIAL | 403 | 61.0% | +581.7p | 1.07R | 38.8% |
| CASCADE | 439 | **85.4%** | **+1,444.1p** | 0.53R | 42.3% |

**P90 Monte Carlo (10,000 Simulations):**
| Metric | Value |
|--------|-------|
| Median PnL | +3,254.9 pips |
| Best Case | +4,003.6 pips |
| Worst Case | +2,525.4 pips |
| 10th Percentile | +3,012.0 pips |
| 90th Percentile | +3,499.1 pips |
| Risk of Ruin (>850p DD) | **0.0%** |
| Median Return @ 0.01 lots | **38.29% of account** |

### 2.2 Symmetry Trap Engine — 4Y EURUSD (2023-07 to 2026-05)

**Data:** 216,820 bars, 910 sessions | **Account:** $85.26 | **Lot:** 0.03

| Metric | Value |
|--------|-------|
| **Total Trades** | **892** |
| **Win Rate** | **85.7%** |
| Wins / Losses | 764 / 125 |
| **Gross Profit** | +4,224.6 pips |
| **Gross Loss** | -497.0 pips |
| **Profit Factor** | **8.18** |
| **Sharpe Ratio** | **11.80** |
| **Max Drawdown** | **39.3 pips (0.04%)** |
| Avg Trade | +4.17 pips |
| Avg Win | 5.53 pips |
| Avg Loss | -3.97 pips |

**Long vs Short:** Balanced (exact split depends on session direction)

### 2.3 Symmetry Trap — Multi-Asset (18 Assets)

**Total: 11,437 trades | +7,009.9 pips**

| Asset | Trades | WR% | PnL (pips) | PF | Sharpe | MaxDD |
|-------|--------|-----|------------|----|--------|-------|
| BTCUSD | 582 | 22.3% | +6,525.0 | 1.14 | 0.65 | 3,905.7 |
| DE30 | 986 | 37.1% | +2,062.6 | 1.20 | 1.11 | 560.9 |
| XAUUSD | 366 | 74.9% | +1,511.3 | 1.18 | 0.93 | 720.1 |
| FR40 | 834 | 36.7% | +980.9 | 1.17 | 0.89 | 557.6 |
| GBPUSD | 997 | 38.8% | +240.5 | 1.04 | 0.30 | 269.6 |
| USDJPY | 486 | 32.5% | +197.7 | 1.06 | 0.34 | 386.3 |
| EURUSD | 886 | 44.0% | +155.2 | 1.03 | 0.24 | 429.6 |
| GBPJPY | 617 | 36.8% | +100.4 | 1.02 | 0.12 | 533.7 |
| USDCHF | 847 | 39.9% | +71.1 | 1.02 | 0.11 | 323.3 |
| CHFJPY | 623 | 33.7% | +56.9 | 1.01 | 0.08 | 539.4 |
| GBPAUD | 551 | 35.6% | -6.1 | 1.00 | -0.01 | 726.0 |
| GBPCHF | 631 | 31.2% | -282.4 | 0.93 | -0.50 | 463.3 |
| GBPNZD | 514 | 32.9% | -313.0 | 0.94 | -0.40 | 626.0 |
| XAGUSD | 469 | 54.8% | -409.4 | 0.95 | -0.27 | 1,633.4 |
| AUDUSD | 620 | 37.9% | -422.0 | 0.88 | -0.90 | 471.3 |
| NZDUSD | 547 | 33.5% | -518.7 | 0.84 | -1.17 | 738.6 |
| ETHUSD | 395 | 19.8% | -619.9 | 0.82 | -1.21 | 895.9 |
| US500 | 303 | 25.7% | -782.3 | 0.64 | -3.11 | 886.1 |
| HK50 | 183 | 13.7% | -1,537.9 | 0.65 | -2.16 | 1,707.0 |

**Aggregate Tier Summary:**
| Tier | Total Trades | Avg WR% | Total PnL |
|------|-------------|---------|-----------|
| T1 | 5,709 | 40.0% | +2,961.4p |
| T2 | 3,196 | 33.6% | +2,678.0p |
| T3 | 2,532 | 31.3% | +1,370.5p |

### 2.4 DMR (Deep Mean Reversion) — 4Y EURUSD (2023-07 to 2026-05)

**Data:** 216,820 bars, 912 sessions | **Account:** $85.26 | **Lot:** 0.03

| Metric | Value |
|--------|-------|
| **Total Trades** | **284** |
| **Win Rate** | **19.0%** |
| Wins / Losses | 54 / 230 |
| **Gross Profit** | +600.6 pips |
| **Gross Loss** | -277.2 pips |
| **Profit Factor** | **2.17** |
| **Sharpe Ratio** | **3.59** |
| Avg Trade | +1.14 pips |
| Max Drawdown | 38.4 pips |
| Avg Win | 11.1 pips |
| Avg Loss | -1.2 pips |
| Max Consec Losses | **31** |

**⚠️ Data Discrepancy:** Historical MT5 EA shows 435 trades, 92.2% WR, +938.1p (2Y). CSV backtest does NOT reproduce this. Root cause: entry trigger logic, SL/TP calculation, trade filtering, or exit conditions differ between MT5 EA and CSV simulation.

**PF 2.17 at 19% WR:** High-payoff, low-WR profile. Avg win (11.1p) is 9x avg loss (1.2p). Characteristic of trend-following payoff applied to mean reversion. However, 31 consecutive losses = ~70 pips DD at 0.01 lots.

### 2.5 Group Combinatorics — Full Universe (36 Pairs)

**Operating points: FLOOR, CEILING, KNEE (best config per pair)**

**Rankings by Net Profit (best config per pair):**
| Rank | Pair | Category | Config | Net $ | WR | PF | Cost% | Tr/d |
|------|------|----------|--------|-------|-----|-----|-------|------|
| 1 | BTCUSD | CRYPTO | FLOOR | $721,151 | 75.2% | 8.1 | 17.0% | 2.61 |
| 2 | ETHUSD | CRYPTO | FLOOR | $44,665 | 76.1% | 8.2 | 50.7% | 5.63 |
| 3 | DE30 | INDEX | FLOOR | $35,296 | 84.3% | 10.8 | 18.5% | 2.41 |
| 4 | HK50 | INDEX | FLOOR | $23,082 | 81.6% | 9.7 | 8.9% | 0.45 |
| 5 | FR40 | INDEX | FLOOR | $19,952 | 84.6% | 10.5 | 29.3% | 3.27 |
| 6 | US500 | INDEX | FLOOR | $16,654 | 83.4% | 12.3 | 13.6% | 2.86 |
| 7 | EURNZD | FOREX | FLOOR | $5,835 | 79.4% | 11.9 | 10.0% | — |
| 8 | GBPNZD | FOREX | FLOOR | $5,715 | 79.2% | 11.4 | 10.1% | — |
| 9 | GBPCAD | FOREX | FLOOR | $4,889 | 80.0% | 10.9 | 13.1% | — |
| 10 | GBPUSD | FOREX | BEST_NET | $4,630 | 81.7% | 12.2 | 16.1% | — |
| 11 | GBPJPY | FOREX | FLOOR | $4,275 | 80.5% | 11.3 | 17.0% | — |
| 12 | GBPAUD | FOREX | FLOOR | $4,240 | 80.8% | 10.6 | 11.3% | — |
| 13 | EURCAD | FOREX | FLOOR | $4,090 | 80.7% | 11.1 | 16.8% | — |
| 14 | CHFJPY | FOREX | FLOOR | $4,026 | 80.8% | 10.0 | 31.7% | — |
| 15 | USDJPY | FOREX | BEST_NET | $3,679 | 81.2% | 11.0 | 13.9% | — |
| 16 | USDCAD | FOREX | FLOOR | $3,452 | 80.9% | 11.6 | 17.5% | — |
| 17 | EURAUD | FOREX | FLOOR | $3,158 | 80.7% | 12.3 | 10.5% | — |
| 18 | EURUSD | FOREX | FLOOR | $2,839 | 82.9% | 12.5 | 15.1% | 4.17 |
| 19 | XAUUSD | METAL | KNEE | $2,790 | 84.6% | 16.2 | 12.7% | 0.69 |
| 20 | CADJPY | FOREX | FLOOR | $2,681 | 80.2% | 11.5 | 23.1% | — |
| 21 | NZDCAD | FOREX | FLOOR | $2,584 | 78.9% | 11.3 | 22.4% | — |
| 22 | NZDJPY | FOREX | FLOOR | $2,541 | 79.3% | 10.6 | 25.2% | — |
| 23 | AUDJPY | FOREX | FLOOR | $2,499 | 78.5% | 10.5 | 19.1% | — |
| 24 | GBPCHF | FOREX | BEST_NET | $2,472 | 80.9% | 10.8 | 17.7% | — |
| 25 | AUDNZD | FOREX | BEST_NET | $2,463 | 80.9% | 14.9 | 20.6% | — |
| 26 | USDCHF | FOREX | FLOOR | $2,405 | 80.3% | 11.0 | 25.4% | — |
| 27 | AUDCAD | FOREX | FLOOR | $2,293 | 80.2% | 11.5 | 21.3% | — |
| 28 | AUDUSD | FOREX | FLOOR | $2,267 | 80.0% | 11.8 | 20.2% | — |
| 29 | EURCHF | FOREX | FLOOR | $2,177 | 81.0% | 12.0 | 25.4% | — |
| 30 | NZDUSD | FOREX | FLOOR | $2,156 | 80.3% | 11.6 | 19.9% | — |
| 31 | AUDCHF | FOREX | FLOOR | $1,846 | 77.9% | 10.5 | 29.0% | — |
| 32 | NZDCHF | FOREX | BEST_NET | $1,812 | 80.9% | 13.3 | 26.9% | — |
| 33 | CADCHF | FOREX | FLOOR | $1,794 | 78.2% | 10.7 | 29.7% | — |
| 34 | EURGBP | FOREX | FLOOR | $1,256 | 84.3% | 14.8 | 29.2% | 1.39 |
| 35 | EURJPY | FOREX | FLOOR | $1,070 | 88.1% | 18.0 | 9.5% | 0.35 |
| 36 | XAGUSD | METAL | CEILING | $85 | 91.1% | 26.8 | 22.2% | 0.20 |

**Categories:**
- **Max Profit (>$3K):** 17 pairs
- **Low Cost (<10%):** HK50 (8.9%), EURJPY (9.5%)
- **High Accuracy (>85%):** EURJPY (88.1%), XAGUSD (91.1%)

### 2.6 9K Trade Unlock Config — EURUSD

**The config that unlocked 9,228 trades (from MAX SWEEP INSIGHT):**

| Parameter | Old (Baseline) | New (Unlock) | Impact |
|-----------|---------------|--------------|--------|
| AR gate | ar_max=20/30/45 | ar_max=999 (disabled) | +274% trades |
| T1 trigger | 12 pips | 8-10 pips | +261% trades |
| Session cutoff | 12:00 PM EST | 4:00 PM EST | +20% trades |
| DZ floor | 32% (Loop 1) | 20% (all loops) | +10% trades |
| **Combined** | **1,125 trades** | **9,228 trades** | **+720%** |

**Results:**
| Metric | Baseline | Unlock |
|--------|----------|--------|
| Trades | 1,125 | 9,228 |
| WR | 84.6% | 84.3% |
| PF | 8.18 | 11.74 |
| PnL | +5,100p | +43,918p |
| Tr/Day | 0.84 | 6.90 |

**Key insight:** The AR gate was the #1 suppressor — silently killing entire trading days where Asian Range exceeded threshold. The 12-pip trigger was #2 — filtering out micro-impulses. Both are independent (multiplicative effect).

**⚠️ NOT yet deployed as standard.** Current Bible config uses calibrated values (AR gate ar_max=60, trigger=10p, 4PM cutoff) giving ~5,000-7,000 trades. The 9K config needs testing across all pairs before deployment.

### 2.7 Cost-Adjusted Results — Viable FX (12 Pairs)

**Using MT5 live spread + flat $0.07 commission:**

| Pair | WR | PF | Net $ | Cost% |
|------|-----|-----|--------|-------|
| EURNZD | 79.4% | 11.9 | $5,727 | 11.7% |
| GBPNZD | 79.2% | 11.4 | $5,608 | 11.7% |
| GBPCAD | 80.0% | 10.9 | $4,889 | 13.1% |
| GBPUSD | 80.8% | 11.3 | $4,776 | 13.8% |
| CHFJPY | 80.8% | 10.0 | $4,559 | 22.6% |
| GBPJPY | 80.5% | 11.3 | $4,401 | 14.6% |
| GBPAUD | 80.8% | 10.6 | $4,240 | 11.3% |
| EURCAD | 80.7% | 11.1 | $4,090 | 16.8% |
| USDCAD | 80.9% | 11.6 | $3,574 | 14.6% |
| USDJPY | 80.4% | 10.5 | $3,548 | 16.8% |
| EURAUD | 80.7% | 12.3 | $3,158 | 10.5% |
| EURUSD | 82.9% | 12.5 | $2,895 | 13.4% |

**Viable Crypto/Metals/Indices:**
| Pair | WR | PF | Net $ | Cost% | Notes |
|------|-----|-----|--------|-------|-------|
| BTCUSD | 75.2% | 8.1 | $8,181 | 5.8% | Best single asset |
| DE30 | 84.3% | 10.8 | $414 | 4.5% | No commission |
| FR40 | 84.6% | 10.5 | $256 | 9.3% | No commission |
| HK50 | 81.6% | 9.7 | $250 | 1.4% | No commission |
| US500 | 83.4% | 12.3 | $170 | 11.9% | No commission |
| XAUUSD | 84.9% | 11.8 | $146 | 57.7% | High spread cost |

### 2.8 Post-Target Reversal Rates (from Holy Grail Manual p.155-158)

**n=3,776 touches**

| Target | Full Reversal | Deep Band Retest | Opp -25% Hit |
|--------|--------------|------------------|--------------|
| -25% | 4.2% | 22.4% | 3.8% |
| -50% | 2.8% | 12.6% | 2.1% |
| -85% | 1.9% | 8.4% | 1.4% |

**By Tier (All Targets Combined):**
| Tier | Full Reversal | Operational Mode |
|------|--------------|------------------|
| T1 (AR ≤ 20p) | Higher reversal rate | Scalping |
| T2 (AR ≤ 30p) | Medium reversal | Standard |
| T3 (AR ≤ 45p) | Lower reversal | Trend following |

### 2.9 Macro Feature Engine — EURUSD M5 E2E

**463K bars × 107 columns (102 macro features) in 154.7s**

| Category | Count/Value |
|----------|-------------|
| MLR bars | 382,463 (82.6%) |
| Bias | BEARISH 50.8%, BULLISH 49.2% |
| ILM WILM | 227,243 (49.1%) |
| ILM MISALIGNED | 176,544 (38.1%) |
| ILM DAILY_ILM | 31,092 (6.7%) |
| ILM IELM | 28,224 (6.1%) |
| Regime FAILED | 333,503 (72.0%) |
| Regime CONFIRMED | 122,112 (26.4%) |
| Regime CAUTION | 7,488 (1.6%) |
| 132% avg distance | 95.1 pips |
| 132% min distance | 0.0 pips |
| Rekey NORMAL | 387,926 (83.9%) |
| Rekey BREACHED | 33,790 (7.3%) |
| Rekey REKEY_SEQ | 24,766 (5.3%) |
| Alpha patterns | 1,438 |
| Beta patterns | 1,379 |
| AB-CD patterns | 583 |
| NY Sweep | 1 |
| Gamma zones | 2,765 |
| OCC extremes | 67,894 |
| ILM zone hits | 275,122 |
| Density zone | 186,438 |
| Wednesday bifurcation | 11,040 |
| Hard exit imminent | 9,622 |
| Gear shift | 331 |
| Fib retrace hits | 276,641 |
| Phase aligned | 6,136 |
| Phase opposed | 5,242 |
| Any pattern | 280,807 (60.6%) |

---

## 🔧 SECTION 3: CONFIGURATION PARAMETERS

### 3.1 Current Bible Config (Calibrated)

```
ar_max = 60 (AR gate — allows moderate AR sessions)
trigger = 10 pips (T1 trigger)
session_cutoff = 16:00 UTC (4PM EST)
dz_floor = 20% (all loops)
dz_ceil = 50%
max_loops = 5
sl_mode = zero_buffer_extreme
tp_mode = dual (-25% AR / -50% AR)
```

### 3.2 9K Unlock Config (Not Yet Deployed)

```
ar_max = 999 (AR gate disabled)
trigger = 8-10 pips (per-asset coefficient)
session_cutoff = 16:00 UTC (4PM EST)
dz_floor = 20% (all loops)
dz_ceil = 50%
max_loops = 5
```

### 3.3 Per-Asset Trigger Coefficients

Each pair's trigger = native_trigger × coefficient (NOT universal 8-10p). Coefficients range from 0.55x (high-trigger crosses) to 0.83x (EURUSD). Same methodology as frequency normalization sweep — per-asset scaling.

### 3.4 Nautilus Strategy Diffs from CSV Engine

1. **DZ floor:** Nautilus 32% (loop 1) vs CSV 20%
2. **Kill switch:** Nautilus active vs CSV removed
3. **Swing origin after exit:** Nautilus uses entry_price vs CSV uses exit_price
4. **Session handling:** Nautilus may filter sessions differently

---

## ⚠️ SECTION 4: CRITICAL RULES & LESSONS

### Ironclad Rules (from CEREBUS BUILD.txt)
1. No retail indicators (RSI, MACD, BB) — constraint-system metrics ONLY
2. Time-series split only — never random train/test
3. 132% kill-switch must be top-5 SHAP feature
4. Wednesday PM bifurcation stress test mandatory
5. 12PM EST hard exit — no exceptions
6. RAG purity — no LLM fine-tuning, only retrieval
7. Close-only SL — M5 CLOSE beyond OCC Extreme
8. Zero-buffer OCC — SL at exact impulse extreme
9. Gear Shift modifies TARGET ONLY — SL never changes
10. No online learning — model frozen between quarterly re-trains
11. Fallback to hardcoded — confidence < 0.6 → manual tiers
12. Separation of church and state — Macro/Micro isolated

### Lessons Learned
- **AR gate was the #1 trade suppressor** — silently killing entire trading days
- **12-pip trigger was #2 suppressor** — filtering out micro-impulses
- **Per-asset calibration is mandatory** — universal values don't work across asset classes
- **Pattern recognition is expensive** — 154.7s for 463K bars with all patterns, but correct
- **Holy Grail PDFs contain structured pattern definitions** — decision trees and playbooks are gold mines
- **DMR CSV backtest ≠ MT5 EA** — 19% WR vs 92.2% WR, root cause in entry/exit logic differences
- **Symmetry Trap works best on XAUUSD** — 74.9% WR, PF 1.18, but LOW_WR on most FX pairs
- **BTCUSD is the best single asset** — $721K net profit in group combinatorics

---

## 📁 SECTION 5: KEY FILES & REFERENCES

| File | Purpose |
|------|---------|
| `quant-lab/engines/symmetry_trap.py` | Symmetry Trap engine (Model B) |
| `quant-lab/engines/dmr_standalone_backtest.py` | DMR standalone backtest |
| `quant-lab/backtest/run_p90_v2.py` | P90 Kinetic Engine v2 |
| `quant-lab/ml/phase1_data/macro/` | Macro feature engine (18 pattern detectors) |
| `quant-lab/ml/tests/test_macro_engine.py` | 70 macro engine unit tests |
| `quant-lab/reports/GROUP_COMBINATORICS_FULL.md` | Full universe rankings |
| `quant-lab/reports/SYMMETRY_TRAP_FINAL_COMPOSITE_REPORT.md` | ST detailed results |
| `quant-lab/reports/DMR_FINAL_COMPOSITE_REPORT.md` | DMR detailed results |
| `quant-lab/reports/cerebus_full_report_final.md` | CEREBUS full report |
| `quant-lab/reports/st_multi_asset_report.md` | ST multi-asset results |
| `shared-conversations/team-chat.md` | Team coordination hub |
