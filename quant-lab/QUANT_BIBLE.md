# 📖 THE QUANT BIBLE — CEREBUS Trading System

> **Compiled:** 2026-06-29 (DMR v2 multi-entry + live deployment)
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
- ✅ Symmetry Trap multi-asset backtest complete (19 assets, 14,088 trades incl. OILUSD)
- ✅ DMR v1 backtest complete (14,582 trades, 92.6% WR, PF 134.2)
- ✅ DMR v2 multi-entry backtest complete (32,102 trades, 91.4% WR, +568,752p PnL, +164% vs v1)
- ✅ DMR live deployment on demo (v1 engine, 5 pairs, ~5 tr/day)
- ✅ DMR Discord bot (clean signals, no scanner noise)
- ✅ P90 Kinetic Engine 4Y backtest complete (1,038 trades, 78.7% WR, PF 3.09)
- ✅ Group combinatorics complete (36 pairs ranked by net profit)
- ✅ P90 v2 backtest complete (9,228 trades unlocked config)
- ✅ **Rekey Intraday Engine complete** (bifurcation model, 7 pairs, 25.8% occurrence, PF 1.25-1.92)
- ✅ **Stall Harvest Engine complete** (P90 deep retracement, 7 pairs, PF 1.07-2.23, CHF/NZD strongest)
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

## � SECTION 1B: AR SIZES & TIER/AU REFERENCE TABLES

### 1B.1 Standard Tier Definitions (Universal)

| Tier | AR Max (pips) | AU Formula | Trigger |
|------|---------------|------------|---------|
| T1 | ≤ 20p | AR / 2 | AU × 1.20 |
| T2 | ≤ 30p | AR / 2 | AU × 1.20 |
| T3 | ≤ 45p | AR / 2 | AU × 1.20 |
| NO-GO | > 45p | Skip session | — |

### 1B.2 Per-Asset Calibrated Tiers (from asset_configs.py)

**Source:** CEREBUS FX v4 Complete Manual + K-Means calibration

#### Forex Majors (k_factor = 0.46)

| Pair | Pip Value | k | T1 AR Max | T1 AU | T1 Trigger | T2 AU | T2 Trigger | T3 AU | T3 Trigger | P90 Threshold | Fixed TP |
|------|-----------|---|-----------|-------|------------|-------|------------|-------|------------|---------------|----------|
| EURUSD | 0.0001 | 0.46 | 60p | 10.0p | 12.0p | 12.0p | 15.0p | 15.0p | 19.0p | 4.6p | 20.0p |
| GBPUSD | 0.0001 | 0.46 | 60p | 13.0p | 16.0p | 16.0p | 19.0p | 20.0p | 24.0p | 5.98p | 26.0p |
| USDCHF | 0.0001 | 0.46 | 60p | 11.0p | 11.0p | 15.0p | 15.0p | 20.0p | 20.0p | 5.06p | 22.0p |
| USDJPY | 0.01 | 0.46 | 60p | 16.0p | 19.0p | 26.0p | 31.0p | 44.0p | 53.0p | 7.36p | 32.0p |
| AUDUSD | 0.0001 | 0.46 | 60p | 11.0p | 13.0p | 14.0p | 17.0p | 18.0p | 21.0p | 5.06p | 22.0p |
| NZDUSD | 0.0001 | 0.46 | 60p | 14.0p | 17.0p | 17.0p | 20.0p | 21.0p | 25.0p | 6.44p | 28.0p |

#### Forex Crosses (k_factor = 0.48)

| Pair | Pip Value | T1 AU | T1 Trigger | T2 AU | T2 Trigger | T3 AU | T3 Trigger | P90 Threshold | SL Method |
|------|-----------|-------|------------|-------|------------|-------|------------|---------------|-----------|
| CHFJPY | 0.01 | 14.0p | 17.0p | 24.0p | 29.0p | 42.0p | 50.0p | 6.72p | OCC_EXACT |
| GBPJPY | 0.01 | 19.0p | 23.0p | 29.0p | 35.0p | 48.0p | 58.0p | 9.12p | OCC_PLUS_5P |
| GBPAUD | 0.0001 | 21.0p | 25.0p | 32.0p | 38.0p | 52.0p | 63.0p | 10.08p | OCC_PLUS_8P |
| GBPNZD | 0.0001 | 24.0p | 29.0p | 36.0p | 43.0p | 59.0p | 71.0p | 11.52p | OCC_PLUS_8P |
| GBPCHF | 0.0001 | 18.0p | 21.0p | 27.0p | 32.0p | 44.0p | 53.0p | 8.64p | OCC_PLUS_6P |
| EURGBP | 0.0001 | 10.0p | 10.0p | 14.0p | 14.0p | 20.0p | 20.0p | 4.60p | OCC_EXACT |
| EURJPY | 0.01 | 16.0p | 19.0p | 26.0p | 31.0p | 44.0p | 53.0p | 7.36p | OCC_EXACT |
| EURAUD | 0.0001 | 14.0p | 17.0p | 20.0p | 24.0p | 30.0p | 36.0p | 6.44p | OCC_EXACT |
| EURCAD | 0.0001 | 12.0p | 14.0p | 18.0p | 22.0p | 26.0p | 31.0p | 5.52p | OCC_EXACT |
| EURNZD | 0.0001 | 18.0p | 22.0p | 27.0p | 32.0p | 40.0p | 48.0p | 8.64p | OCC_EXACT |
| CADCHF | 0.01 | 11.0p | 13.0p | 17.0p | 20.0p | 25.0p | 30.0p | 5.06p | OCC_EXACT |
| AUDCAD | 0.0001 | 10.0p | 12.0p | 15.0p | 18.0p | 22.0p | 26.0p | 4.60p | OCC_EXACT |
| AUDCHF | 0.0001 | 11.0p | 13.0p | 16.0p | 19.0p | 24.0p | 29.0p | 5.06p | OCC_EXACT |
| AUDJPY | 0.01 | 14.0p | 17.0p | 24.0p | 29.0p | 42.0p | 50.0p | 6.72p | OCC_EXACT |
| AUDNZD | 0.0001 | 9.0p | 11.0p | 13.0p | 16.0p | 19.0p | 23.0p | 4.14p | OCC_EXACT |
| NZDJPY | 0.01 | 14.0p | 17.0p | 24.0p | 29.0p | 42.0p | 50.0p | 6.72p | OCC_EXACT |
| NZDCHF | 0.0001 | 12.0p | 14.0p | 18.0p | 22.0p | 28.0p | 34.0p | 5.52p | OCC_EXACT |
| NZDCAD | 0.0001 | 11.0p | 13.0p | 17.0p | 20.0p | 25.0p | 30.0p | 5.06p | OCC_EXACT |
| CADJPY | 0.01 | 12.0p | 14.0p | 20.0p | 24.0p | 32.0p | 38.0p | 5.52p | OCC_EXACT |
| USDCAD | 0.0001 | 10.0p | 12.0p | 15.0p | 18.0p | 22.0p | 26.0p | 4.60p | OCC_EXACT |

#### Indices (k_factor = 0.48)

| Pair | Pip Value | T1 AU | T1 Trigger | T2 AU | T2 Trigger | T3 AU | T3 Trigger | P90 Threshold | SL Method |
|------|-----------|-------|------------|-------|------------|-------|------------|---------------|-----------|
| DE30 | 1.0 | 20.3p | 24.4p | 30.5p | 36.6p | 45.7p | 54.8p | 9.7p | FIXED_BUFFER |
| FR40 | 1.0 | 17.3p | 20.8p | 26.0p | 31.2p | 38.7p | 46.4p | 8.3p | FIXED_BUFFER |
| US500 | 1.0 | 17.3p | 20.8p | 26.0p | 31.2p | 38.7p | 46.4p | 8.3p | FIXED_BUFFER |
| HK50 | 1.0 | 82.5p | 99.0p | 123.8p | 148.5p | 185.6p | 222.7p | 39.6p | FIXED_BUFFER |

#### Metals (k_factor = 0.50)

| Pair | Pip Value | T1 AU | T1 AR Max | T2 AU | T2 AR Max | T3 AU | T3 AR Max | P90 Threshold | SL Method |
|------|-----------|-------|-----------|-------|-----------|-------|-----------|---------------|-----------|
| XAUUSD | 0.01 | 16.0p | 32.0p | 29.0p | 58.0p | 48.0p | 95.0p | 8.0p | FIXED_BUFFER |
| XAGUSD | 0.0001 | 22.5p | 45.0p | 33.8p | 67.5p | 56.3p | 112.5p | 11.3p | FIXED_BUFFER |

#### Crypto (k_factor = 0.52)

| Pair | Pip Value | T1 AU | T1 AR Max | T2 AU | T2 AR Max | T3 AU | T3 AR Max | P90 Threshold | SL Method |
|------|-----------|-------|-----------|-------|-----------|-------|-----------|---------------|-----------|
| BTCUSD | 1.0 | 205.0p | 750.0p | 545.0p | 1700.0p | 1160.0p | 3000.0p | 106.6p | FIXED_BUFFER |
| ETHUSD | 1.0 | 31.5p | 100.0p | 78.8p | 250.0p | 157.5p | 500.0p | 16.4p | FIXED_BUFFER |

#### Commodities

| Pair | Pip Value | T1 AU | T1 AR Max | T2 AU | T2 AR Max | T3 AU | T3 AR Max | Notes |
|------|-----------|-------|-----------|-------|-----------|-------|-----------|-------|
| OILUSD | 0.01 | Varies by regime | — | — | — | — | — | See 1B.3 |

### 1B.3 OILUSD — Regime-Dependent AR Sizes (in Dollars)

**Source:** Phase 1B OILUSD Session Bifurcation Analysis (678 trading days)
**Note:** OILUSD pip_value = 0.01 (1 cent). 100 pips = $1.00. All values below in dollar denomination.

**AR Mean by Regime:**
| Regime | Days | AR Mean | T1 Count | T2 Count | T3 Count | NO_GO Count |
|--------|------|---------|----------|----------|----------|-------------|
| WAR_SPIKE | 65 | 22p = **$0.22** | 17 | 38 | 6 | 4 |
| NORMALIZATION | 194 | 27p = **$0.27** | 61 | 99 | 20 | 14 |
| PRE_WAR | 198 | 29.2p = **$0.29** | 55 | 113 | 16 | 14 |
| WAR_ONSET | 122 | 30.9p = **$0.31** | 39 | 61 | 15 | 7 |
| CURRENT | 300 | 64.9p = **$0.65** | 117 | 133 | 26 | 24 |

**Standard Tiers (in dollars):**
| Tier | AR Max | AU | Trigger |
|------|--------|-----|---------|
| T1 | 20p = **$0.20** | 10p = $0.10 | 12p = $0.12 |
| T2 | 30p = **$0.30** | 15p = $0.15 | 18p = $0.18 |
| T3 | 45p = **$0.45** | 22.5p = $0.23 | 27p = $0.27 |
| NO_GO | > 45p = **>$0.45** | Skip | — |

**⚠️ CURRENT REGIME ADJUSTMENT:** OILUSD AR mean has shifted to $0.65 (64.9p), far exceeding standard T3 max of $0.45. Proposed adjusted tiers for current regime:

| Tier | AR Max | AU | Trigger |
|------|--------|-----|---------|
| T1 | 35p = **$0.35** | 17.5p = $0.17 | 21p = $0.21 |
| T2 | 55p = **$0.55** | 27.5p = $0.28 | 33p = $0.33 |
| T3 | 80p = **$0.80** | 40p = $0.40 | 48p = $0.48 |
| NO_GO | > 80p = **>$0.80** | Skip | — |

**AU and Trigger at Key AR Levels (dollar denomination):**
| AR | AU | Trigger |
|----|-----|---------|
| 20p ($0.20) | 10p ($0.10) | 12p ($0.12) |
| 25p ($0.25) | 12.5p ($0.12) | 15p ($0.15) |
| 30p ($0.30) | 15p ($0.15) | 18p ($0.18) |
| 35p ($0.35) | 17.5p ($0.17) | 21p ($0.21) |
| 40p ($0.40) | 20p ($0.20) | 24p ($0.24) |
| 45p ($0.45) | 22.5p ($0.23) | 27p ($0.27) |
| 55p ($0.55) | 27.5p ($0.28) | 33p ($0.33) |
| 65p ($0.65) | 32.5p ($0.33) | 39p ($0.39) |
| 80p ($0.80) | 40p ($0.40) | 48p ($0.48) |

**OILUSD ST Tier Distribution (2,651 trades):**
| Tier | Trades | WR | PnL |
|------|--------|-----|------|
| T1 | 1,067 | 73.3% | +3,795.0p |
| T2 | 1,282 | 76.6% | +10,316.4p |
| T3 | 302 | 75.8% | +3,555.9p |

**Key Insight:** T2 is the sweet spot for OILUSD — highest total PnL (+10,316p) with 76.6% WR. The CURRENT regime (AR mean $0.65) frequently exceeds standard T3 max ($0.45), meaning many sessions are NO-GO under standard tiers. Adjusted tiers recommended for current market conditions.

### 1B.4 ST Backtest Tier Results (Per-Asset)

**Symmetry Trap multi-asset tier breakdown (from backtest reports):**

| Pair | T1 Trades | T1 WR | T1 PnL | T2 Trades | T2 WR | T2 PnL | T3 Trades | T3 WR | T3 PnL |
|------|-----------|-------|--------|-----------|-------|--------|-----------|-------|--------|
| EURUSD | 546 | 84.2% | +2,190.8p | 325 | 81.8% | +1,296.8p | 292 | 90.1% | +1,560.5p |
| GBPUSD | 583 | 85.8% | +3,107.5p | 341 | 84.2% | +1,877.9p | 335 | 87.2% | +2,458.9p |
| XAUUSD | 69 | 76.8% | +158.4p | 292 | 83.9% | +3,366.4p | 243 | 87.2% | +3,662.9p |
| BTCUSD | 375 | 90.9% | +30,246.0p | 297 | 93.3% | +60,215.7p | 129 | 96.1% | +61,842.6p |
| DE30 | 501 | 79.0% | +4,557.1p | 368 | 80.7% | +5,514.0p | 276 | 92.4% | +8,395.7p |
| CHFJPY | 298 | 78.2% | +1,257.7p | 222 | 87.4% | +1,775.5p | 231 | 95.7% | +4,133.8p |

### 1B.5 Native Tier Master Table (K-Means Calibrated)

**Source:** `quant-lab/reports/tier_discovery_summary.md` + `fx_calibration_summary.md`
**Method:** K-Means Clustering (k=3) on Asian Range per asset
**Note:** These are the ACTUAL native tiers used in backtests, calibrated per-asset from data.
T1 ar_max = T2 boundary, T2 ar_max = T3 boundary. NO_GO = AR > T3 ar_max.

#### Forex Majors

| Pair | Pip | k | T1 AR Max | T1 AU | T1 Trig | T2 AR Max | T2 AU | T2 Trig | T3 AR Max | T3 AU | T3 Trig | P90 Thr | SL Method |
|------|-----|---|-----------|-------|---------|-----------|-------|---------|-----------|-------|---------|---------|-----------|
| EURUSD | 0.0001 | 0.46 | 20.0p | 10.0p | 12.0p | 30.0p | 12.0p | 15.0p | 45.0p | 15.0p | 19.0p | 4.6p | OCC_EXACT |
| GBPUSD | 0.0001 | 0.46 | 26.0p | 13.0p | 16.0p | 39.0p | 16.0p | 19.0p | 59.0p | 20.0p | 24.0p | 5.98p | OCC_EXACT |
| USDCHF | 0.0001 | 0.46 | 20.0p | 11.0p | 11.0p | 30.0p | 15.0p | 15.0p | 45.0p | 20.0p | 20.0p | 5.06p | OCC_EXACT |
| USDJPY | 0.01 | 0.46 | 30.0p | 16.0p | 19.0p | 50.0p | 26.0p | 31.0p | 80.0p | 44.0p | 53.0p | 7.36p | OCC_EXACT |
| AUDUSD | 0.0001 | 0.46 | 20.0p | 11.0p | 13.0p | 30.0p | 14.0p | 17.0p | 45.0p | 18.0p | 21.0p | 5.06p | OCC_EXACT |
| NZDUSD | 0.0001 | 0.46 | 25.0p | 14.0p | 17.0p | 35.0p | 17.0p | 20.0p | 50.0p | 21.0p | 25.0p | 6.44p | OCC_EXACT |

#### Forex Crosses (K-Means Calibrated)

| Pair | Pip | T1 AR Max | T1 AU | T1 Trig | T2 AR Max | T2 AU | T2 Trig | T3 AR Max | T3 AU | T3 Trig | P90 Thr | SL Method |
|------|-----|-----------|-------|---------|-----------|-------|---------|-----------|-------|---------|---------|-----------|
| EURGBP | 0.0001 | 14.7p | 7p | 8p | 23.0p | 14p | 17p | 23.0p | 26p | 32p | 4.6p | OCC_EXACT |
| EURJPY | 0.01 | 55.1p | 29p | 35p | 81.4p | 63p | 75p | 81.4p | 185p | 222p | 26.5p | OCC_EXACT |
| EURAUD | 0.0001 | 52.9p | 27p | 32p | 78.27p | 51p | 61p | 78.27p | 107p | 129p | 25.4p | OCC_EXACT |
| EURNZD | 0.0001 | 59.6p | 28p | 34p | 84.4p | 49p | 59p | 84.4p | 94p | 113p | 28.6p | OCC_EXACT |
| EURCHF | 0.0001 | 18.37p | 9p | 11p | 26.7p | 19p | 23p | 26.7p | 41p | 49p | 4.6p | OCC_EXACT |
| EURCAD | 0.0001 | 28.9p | 13p | 16p | 43.5p | 25p | 31p | 43.5p | 50p | 60p | 5.5p | OCC_EXACT |
| USDCAD | 0.0001 | 23.4p | 11p | 13p | 34.4p | 20p | 24p | 34.4p | 37p | 44p | 5.0p | OCC_EXACT |
| AUDJPY | 0.01 | 42.9p | 21p | 26p | 65.47p | 45p | 53p | 65.47p | 121p | 146p | 20.6p | OCC_EXACT |
| AUDNZD | 0.0001 | 23.57p | 12p | 14p | 34.3p | 24p | 29p | 34.3p | 51p | 62p | 5.0p | OCC_EXACT |
| AUDCHF | 0.0001 | 20.7p | 10p | 12p | 31.2p | 18p | 22p | 31.2p | 37p | 44p | 5.0p | OCC_EXACT |
| AUDCAD | 0.0001 | 26.2p | 13p | 16p | 37.2p | 24p | 29p | 37.2p | 46p | 55p | 5.0p | OCC_EXACT |
| NZDJPY | 0.01 | 37.8p | 20p | 24p | 54.84p | 44p | 53p | 54.84p | 143p | 172p | 18.1p | OCC_EXACT |
| NZDCHF | 0.0001 | 18.4p | 9p | 11p | 26.7p | 18p | 22p | 26.7p | 39p | 47p | 5.0p | OCC_EXACT |
| NZDCAD | 0.0001 | 24.9p | 12p | 15p | 35.44p | 22p | 26p | 35.44p | 42p | 50p | 5.0p | OCC_EXACT |
| CADJPY | 0.01 | 35.7p | 19p | 23p | 54.4p | 43p | 51p | 54.4p | 139p | 166p | 17.1p | OCC_EXACT |
| CADCHF | 0.0001 | 15.0p | 7p | 9p | 22.3p | 14p | 17p | 22.3p | 32p | 38p | 4.6p | OCC_EXACT |
| GBPCAD | 0.0001 | 37.1p | 20p | 24p | 53.94p | 45p | 55p | 53.94p | 329p | 395p | 5.0p | OCC_PLUS_6P |
| GBPJPY | 0.01 | 40.0p | 19p | 23p | 70.0p | 29p | 35p | 100.0p | 48p | 58p | 9.12p | OCC_PLUS_5P |
| GBPAUD | 0.0001 | 45.0p | 21p | 25p | 75.0p | 32p | 38p | 110.0p | 52p | 63p | 10.08p | OCC_PLUS_8P |
| GBPNZD | 0.0001 | 50.0p | 24p | 29p | 85.0p | 36p | 43p | 120.0p | 59p | 71p | 11.52p | OCC_PLUS_8P |
| GBPCHF | 0.0001 | 35.0p | 18p | 21p | 55.0p | 27p | 32p | 80.0p | 44p | 53p | 8.64p | OCC_PLUS_6P |

#### Indices

| Pair | Pip | T1 AR Max | T1 AU | T1 Trig | T2 AR Max | T2 AU | T2 Trig | T3 AR Max | T3 AU | T3 Trig | SL Method |
|------|-----|-----------|-------|---------|-----------|-------|---------|-----------|-------|---------|-----------|
| DE30 | 1.0 | 50.0p | 20p | 24p | 80.0p | 30p | 37p | 120.0p | 46p | 55p | FIXED_BUFFER |
| FR40 | 1.0 | 45.0p | 17p | 21p | 70.0p | 26p | 31p | 100.0p | 39p | 46p | FIXED_BUFFER |
| US500 | 1.0 | 45.0p | 17p | 21p | 70.0p | 26p | 31p | 100.0p | 39p | 46p | FIXED_BUFFER |
| HK50 | 1.0 | 150.0p | 83p | 99p | 200.0p | 124p | 149p | 300.0p | 186p | 223p | FIXED_BUFFER |

#### Metals & Crypto

| Pair | Pip | T1 AR Max | T1 AU | T1 Trig | T2 AR Max | T2 AU | T2 Trig | T3 AR Max | T3 AU | T3 Trig | SL Method |
|------|-----|-----------|-------|---------|-----------|-------|---------|-----------|-------|---------|-----------|
| XAUUSD | 0.01 | 32.0p | 16p | 19p | 58.0p | 29p | 35p | 95.0p | 48p | 58p | FIXED_BUFFER |
| XAGUSD | 0.0001 | 45.0p | 23p | 27p | 67.5p | 34p | 41p | 112.5p | 56p | 68p | FIXED_BUFFER |
| BTCUSD | 1.0 | 750p | 205p | 246p | 1700p | 545p | 654p | 3000p | 1160p | 1392p | FIXED_BUFFER |
| ETHUSD | 1.0 | 100p | 32p | 38p | 250p | 79p | 95p | 500p | 158p | 189p | FIXED_BUFFER |

#### Commodities

| Pair | Pip | T1 AR Max | T1 AU | T1 Trig | T2 AR Max | T2 AU | T2 Trig | T3 AR Max | T3 AU | T3 Trig | Notes |
|------|-----|-----------|-------|---------|-----------|-------|---------|-----------|-------|---------|-------|
| OILUSD | 0.01 | 20p ($0.20) | 10p ($0.10) | 12p ($0.12) | 30p ($0.30) | 12p ($0.12) | 15p ($0.15) | 45p ($0.45) | 15p ($0.15) | 19p ($0.19) | See 1B.3 for regime-adjusted |

### 1B.5 Key AR Size Observations

**Typical Asian Range Sizes by Asset Class:**
| Asset Class | Typical AR Range | Notes |
|-------------|-----------------|-------|
| EURUSD | 20-60 pips | Most liquid, tightest range |
| GBPUSD | 25-70 pips | Slightly wider than EURUSD |
| USDJPY | 30-90 pips | Higher pip value, wider range |
| CHFJPY | 25-80 pips | Cross, moderate range |
| GBPJPY | 40-120p | Highest volatility major cross |
| XAUUSD | 30-100p | Metal, wide range |
| BTCUSD | 500-3000p | Crypto, extremely wide range |
| DE30 | 40-150p | Index, moderate range |
| OILUSD | $0.22-$0.65 | Regime-dependent (see 1B.3). CURRENT regime needs adjusted tiers. |

**AU = AR / 2 (always)**

**Trigger = AU × 1.20 (always)**

**P90 Threshold = AU × k_factor (per asset class)**

**Fixed TP = AU × 2.0 (for dual-entry SL calculation)**

---

## 📊 SECTION 2: BACKTEST RESULTS

### 2.10 Rekey Intraday Engine — Bifurcation Model (2026-06-29)

**Source:** Holy Grail Phase 4 — Bifurcation Mechanics
**Engine:** `quant-lab/engines/rekey_intraday.py`
**Config:** `quant-lab/config/rekey_strategy.yaml`

**Session Windows (EST):**
| Session | Time | Duration | Purpose |
|---------|------|----------|---------|
| Asian Range | 7:00 PM - 3:00 AM | 8 hours | Range observation + bias |
| London Open | 2:00 AM - 6:00 AM | 4 hours | Anchor establishment |
| Trading Window | 3:00 AM - 12:00 PM | 9 hours | Entry execution |

**Trade Setup:**
| Parameter | Value |
|-----------|-------|
| Entry | 50% consolidation between band edge and 132% |
| SL | 132% level + 5 pips |
| TP | 0 level (opposite band) |
| Bifurcation Rate | 49.4% (EURUSD) |
| Trade Occurrence | 25.8% of sessions |

**Results (7 FX pairs):**
| Pair | Trades | WR | Net PnL | PF |
|------|--------|-----|---------|-----|
| AUDNZD | 220 | 60.9% | +659p | 1.92 |
| EURGBP | 198 | 60.6% | +387p | 1.58 |
| GBPCAD | 270 | 50.4% | +917p | 1.31 |
| EURUSD | 194 | 52.1% | +317p | 1.25 |
| EURCHF | 231 | 55.8% | +298p | 1.26 |

**Key Finding:** Bifurcation rate matches Holy Grail prediction (42-51%). TP2 (extension) hit 97% of wins.

---

### 2.11 Stall Harvest — P90 Deep Retracement (2026-06-29)

**Source:** CEREBUS Manual — Stall Harvest Trading System
**Engine:** `quant-lab/engines/stall_harvest_test.py`

**Trade Setup:**
| Parameter | Value |
|-----------|-------|
| Entry | 168% of P90 body from P90 extreme |
| SL | 200% + 1.5x body buffer |
| TP1 | P90 close (0% = return to range) |
| TP2 | P90 extension (high + 85% body for bullish) |

**Results (7 FX pairs):**
| Pair | Trades | WR | Net PnL | PF |
|------|--------|-----|---------|-----|
| USDCHF | 300 | 65.7% | +1247p | 2.23 |
| NZDUSD | 240 | 62.5% | +708p | 1.81 |
| AUDUSD | 268 | 60.4% | +659p | 1.67 |
| EURUSD | 270 | 57.8% | +547p | 1.46 |
| GBPUSD | 298 | 55.0% | +493p | 1.35 |
| USDCAD | 318 | 54.1% | +481p | 1.34 |
| USDJPY | 148 | 48.6% | +51p | 1.07 |

**Key Finding:** TP2 (extension) hit 97% of winning trades. TP1 (P90 close) hit 0% — deep 168% entry means price hits extension target before returning to P90 close. CHF and NZD pairs strongest.

---

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

### 2.3 Symmetry Trap — Multi-Asset (19 Assets)

**Total: 14,088 trades | +24,677.2 pips** (including OILUSD)

| Asset | Trades | WR% | PnL (pips) | PF | Sharpe | MaxDD |
|-------|--------|-----|------------|----|--------|-------|
| OILUSD | 2,651 | 75.2% | +17,667.3 | 6.54 | 9.06 | 89.7 |
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

**Aggregate Tier Summary (18 assets, ex-OILUSD):**
| Tier | Total Trades | Avg WR% | Total PnL |
|------|-------------|---------|-----------|
| T1 | 5,709 | 40.0% | +2,961.4p |
| T2 | 3,196 | 33.6% | +2,678.0p |
| T3 | 2,532 | 31.3% | +1,370.5p |

### 2.3b OILUSD — Symmetry Trap Deep Dive

**Data:** 2,651 trades | **Engine:** Symmetry Trap (Regime-Adaptive) | **Generated:** 2026-06-01

| Metric | Value |
|--------|-------|
| **Total Trades** | **2,651** |
| **Win Rate** | **75.2%** |
| **Profit Factor** | **6.54** |
| **Total PnL** | **+17,667.3 pips** |
| **Max Drawdown** | **89.7 pips (0.1%)** |
| **Expectancy** | **6.66 pips/trade** |
| **Sharpe** | **9.06** |
| **Sortino** | **15.24** |

**Monte Carlo (10,000 Simulations):**
| Metric | Value |
|--------|-------|
| Equity P5 | +16,696.7 pips |
| Equity P25 | +17,251.7 pips |
| Equity Median | +17,656.1 pips |
| Equity P75 | +18,065.0 pips |
| Equity P95 | +18,668.2 pips |
| Max DD Median | 72.0 pips |
| Max DD P95 | 99.0 pips |
| Ruin (10%) | 0.0% |
| Ruin (20%) | 0.0% |
| Ruin (30%) | 0.0% |
| Kelly | 0.606 |
| Half-Kelly | 0.303 |

**Regime Breakdown:**
| Regime | Trades | WR | PnL | PF |
|--------|--------|-----|------|-----|
| PRE_WAR | 608 | 74.5% | +2,930.0p | 4.36 |
| WAR_ONSET | 395 | 74.2% | +2,171.3p | 5.08 |
| WAR_SPIKE | 230 | 68.3% | +793.9p | 4.25 |
| NORMALIZATION | 566 | 73.3% | +3,025.0p | 8.08 |

### 2.3c OILUSD — 132% Realignment Trigger (Bifurcation Analysis)

**Source:** Holy Grail PDF — Phase 1B OILUSD Session Bifurcation Analysis (678 trading days)

**Key Findings:**
| Metric | Value |
|--------|-------|
| Total Trading Days | 678 |
| Bifurcation Rate | 51.5% (Asian Range ≠ London Open) |
| **132% Trigger Success** | **98.0%** (expected ~70%, achieved 98%) |
| Asian Open Predictive | 77.4% containment rate |
| London Dominance | London 132% hits first 63.3% of time during bifurcation |
| Perfect Target Clustering | -25% and -50% within 10 pips 100% of time when aligned |
| Monday London Weekly Bias | 55.0% reach -168% by Friday, 65.1% reach -100% |

**Session Definitions (EST):**
| Session | Time | Duration |
|---------|------|----------|
| Asian Range | 7:00 PM - 3:00 AM | 8 hours |
| London Open | 2:00 AM - 6:00 AM | 4 hours |
| Asian Open Range | 6:00 PM - 9:30 PM | 3.5 hours |
| Monday London | Mon 3:00 AM - 11:00 AM | 8 hours |
| NY-AM | 6:00 AM - 9:00 AM | 3 hours |
| NY-PM | 9:00 AM - 11:00 AM | 2 hours |
| Black Zone | 12:00 PM - 7:00 PM | 7 hours |

**Cross-Asset Validation (EUR/USD, OIL/USD, ETH/USD):**
- 132% invalidation is universal: 70-75% violation rate
- -25% and -50% targets: >89% hit rate across all markets
- OIL/USD: 98% hit rate on 132% realignment trigger during bifurcation
- 1,401 sessions analyzed

### 2.4 DMR (Deep Mean Rebalancing) — Multi-Asset (30 Pairs, 4.4 Years)

**Data:** M5, 2022-01 to 2026-06 (~4.4 years) | **Engine:** `dmr_reconstructed.py` + `dmr_v2_multi_entry_test.py`

#### v2 Multi-Entry Results (Latest — One P90 per 2hr Window)

| Pair | Trades | WR | PF | PnL | TP | SL |
|------|--------|----|----|-----|----|----|-----|
| **EURUSD** | 988 | 92.4% | 122.6 | +12,517p | 913 | 75 |
| **GBPUSD** | 1,921 | 92.2% | 118.2 | +25,786p | 1,771 | 150 |
| **USDCHF** | 1,425 | 91.2% | 122.3 | +19,449p | 1,298 | 125 |
| **USDJPY** | 1,841 | 90.2% | 95.6 | +24,863p | 1,661 | 180 |
| **AUDUSD** | 1,684 | 92.6% | 136.3 | +20,852p | 1,5604 |
| **USDCAD** | 1,741 | 92.2% | 119.0 | +21,528p | 1,605 | 135 |
| **NZDUSD** | 1,352 | 91.3% | 115.2 | +15,960p | 1,232 | 117 |
| **GBPJPY** | 1,095 | 92.0% | 117.1 | +16,192p | 1,007 | 88 |
| **CHFJPY** | 1,129 | 90.5% | 104.3 | +16,132p | 1,022 | 107 |
| **TOTAL** | **32,102** | **91.4%** | — | **+568,752p** | | |

#### v1 vs v2 Comparison

| Metric | v1 (single entry) | v2 (multi-entry) | Delta |
|--------|-------------------|-------------------|-------|
| **Total Trades** | 14,582 | 32,102 | **+120%** |
| **Total PnL** | +215,661p | +568,752p | **+164%** |
| **Blended WR** | 92.6% | 91.4% | -1.3pp |
| **0% Ruin Rate** | ✅ All pairs | ✅ All pairs | — |

#### Key DMR Stats

| Metric | Value |
|--------|-------|
| **Max Consec Losses** | 2 (most forex pairs) |
| **Avg MaxDD (Forex)** | 2.9 pips |
| **Avg Trade Duration** | 10.4 minutes |
| **Kelly Criterion** | > 0.90 (all forex) |
| **Hard Exits** | 5 of 14,584 (0.03%) |
| **Live Deployment** | v1 on demo (5 pairs), v2 ready |

**Full per-pair breakdown:** [`reports/dmr_mc/dmr_deep_analysis_report.md`](reports/dmr_mc/dmr_deep_analysis_report.md)
**DMR Mini Bible:** [`reports/dmr_mc/DMR_BIBLE.md`](reports/dmr_mc/DMR_BIBLE.md)

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
- **OILUSD is the best ST performer** — 75.2% WR, PF 6.54, Sharpe 9.06, 0% ruin rate
- **OILUSD 132% realignment trigger: 98% hit rate** during bifurcation (Holy Grail PDF validated)

---

## 📁 SECTION 5: KEY FILES & REFERENCES

| File | Purpose |
|------|---------|
| `quant-lab/engines/symmetry_trap.py` | Symmetry Trap engine (Model B) |
| `quant-lab/engines/rekey_intraday.py` | Rekey Intraday engine (bifurcation model) |
| `quant-lab/engines/stall_harvest_test.py` | Stall Harvest engine (P90 deep retracement) |
| `quant-lab/config/rekey_strategy.yaml` | Rekey strategy configuration |
| `quant-lab/backtest/dmr_reconstructed.py` | DMR v1 backtest engine (single entry) |
| `quant-lab/backtest/dmr_v2_multi_entry_test.py` | DMR v2 backtest engine (multi-entry) |
| `quant-lab/backtest/dmr_mc_full.py` | DMR Monte Carlo + deep stats |
| `quant-lab/backtest/dmr_combinatorics.py` | DMR portfolio combinatorics |
| `quant-lab/mt5/dmr_multi_pair_live.py` | DMR v1 live engine (demo) |
| `quant-lab/mt5/dmr_multi_pair_live_v2.py` | DMR v2 live engine (ready) |
| `scripts/discord_dmr_bot.py` | DMR Discord bot (clean signals) |
| `quant-lab/backtest/run_p90_v2.py` | P90 Kinetic Engine v2 |
| `quant-lab/ml/phase1_data/macro/` | Macro feature engine (18 pattern detectors) |
| `quant-lab/ml/tests/test_macro_engine.py` | 70 macro engine unit tests |
| `quant-lab/reports/GROUP_COMBINATORICS_FULL.md` | Full universe rankings |
| `quant-lab/reports/SYMMETRY_TRAP_FINAL_COMPOSITE_REPORT.md` | ST detailed results |
| `quant-lab/reports/DMR_FINAL_COMPOSITE_REPORT.md` | DMR detailed results |
| `quant-lab/reports/cerebus_full_report_final.md` | CEREBUS full report |
| `quant-lab/reports/st_multi_asset_report.md` | ST multi-asset results |
| `shared-conversations/team-chat.md` | Team coordination hub |

---

## 📊 SECTION 6: P90 BINARY EXCURSION TEST — CALIBRATED (June 16, 2026)

### 6.1 Methodology

**Per-asset calibrated P90 thresholds — each pair's own historical data determines its thresholds.**

```
Window:        3AM-12PM EST (08:00-17:00 UTC)
Calibration:   90th percentile of M5 body sizes per 2h UTC bucket, computed per asset
Entry:         Close of P90 candle (body >= asset-specific 90th percentile threshold)
Direction:     LONG if close > open (bullish), SHORT if close < open (bearish)
Expiry:        Fixed time window (1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120 min)
Win:           ANY future M5 candle CLOSES in trade direction before expiry
Loss:          ANY future M5 candle CLOSES against trade direction before expiry
```

**Key difference from earlier test**: Each pair's P90 thresholds are computed from its OWN historical M5 data. No universal EURUSD thresholds applied to all pairs.

### 6.2 Calibrated P90 Thresholds (pips by 2h UTC bucket)

| Pair | 8-10 | 10-12 | 12-14 | 14-16 |
|------|------|-------|-------|--------|
| EURUSD | 4.10 | 5.50 | 4.50 | 5.70 |
| GBPUSD | 5.40 | 7.30 | 6.20 | 7.50 |
| USDJPY | 7.60 | 8.60 | 6.50 | 8.70 |
| USDCHF | 3.60 | 5.10 | 4.10 | 5.20 |
| AUDUSD | 3.80 | 4.20 | 3.30 | 4.20 |
| NZDUSD | 3.40 | 4.00 | 3.20 | 4.00 |
| USDCAD | 4.30 | 6.60 | 8.10 | 5.70 |
| EURGBP | 3.50 | 3.80 | 4.00 | 2.80 |
| GBPJPY | 10.00 | 12.50 | 9.80 | 11.20 |
| GBPAUD | 8.60 | 9.90 | 8.40 | 9.60 |
| GBPNZD | 9.40 | 10.90 | 9.40 | 10.80 |
| GBPCHF | 4.30 | 6.40 | 5.40 | 6.00 |
| GBPCAD | 7.20 | 9.70 | 10.50 | 7.40 |
| EURJPY | 7.80 | 9.40 | 10.50 | 7.00 |
| EURAUD | 7.20 | 8.90 | 10.60 | 7.10 |
| EURNZD | 8.00 | 9.80 | 11.00 | 7.30 |
| EURCHF | 3.90 | 4.40 | 5.00 | 3.40 |
| EURCAD | 5.80 | 8.00 | 9.10 | 6.30 |
| AUDJPY | 5.30 | 6.60 | 8.20 | 5.70 |
| AUDNZD | 3.00 | 3.60 | 4.00 | 2.80 |
| AUDCHF | 3.20 | 3.90 | 4.60 | 3.10 |
| AUDCAD | 3.50 | 5.00 | 5.70 | 3.90 |
| NZDJPY | 4.80 | 5.90 | 7.00 | 4.90 |
| NZDCHF | 2.90 | 3.40 | 3.90 | 2.70 |
| NZDCAD | 3.40 | 4.70 | 5.30 | 3.60 |
| CADJPY | 5.10 | 7.10 | 8.50 | 5.80 |
| CADCHF | 3.10 | 4.10 | 4.70 | 3.20 |
| XAUUSD | 24.20 | 25.20 | 22.20 | 31.80 |
| XAGUSD | 6.50 | 6.60 | 5.60 | 8.50 |
| BTCUSD | 102.70 | 113.50 | 104.70 | 125.10 |
| ETHUSD | 5.94 | 6.48 | 6.14 | 7.14 |
| SOLUSD | 0.41 | 0.44 | 0.41 | 0.47 |
| XRPUSD | 39.00 | 43.00 | 40.00 | 45.00 |
| US500 | 2.35 | 3.55 | 2.90 | 3.82 |

### 6.3 Full Expiry Sweep — Ranked by 120min WR

**All 34 pairs exceed 85% WR at 120min expiry with calibrated thresholds.**

| Rank | Pair | 120min WR | Signals | Best | >=75% Windows |
|------|------|-----------|---------|------|---------------|
| 1 | US500 | 88.0% | 11,498 | 120m | 30,45,60,90,120 |
| 2 | BTCUSD | 87.6% | 33,184 | 120m | 30,45,60,90,120 |
| 3 | NZDUSD | 87.6% | 10,972 | 120m | 30,45,60,90,120 |
| 4 | SOLUSD | 87.5% | 14,734 | 120m | 30,45,60,90,120 |
| 5 | USDCHF | 87.5% | 11,619 | 120m | 30,45,60,90,120 |
| 6 | AUDUSD | 87.4% | 11,068 | 120m | 30,45,60,90,120 |
| 7 | GBPUSD | 87.3% | 13,116 | 120m | 30,45,60,90,120 |
| 8 | XAUUSD | 87.3% | 21,413 | 120m | 30,45,60,90,120 |
| 9 | GBPJPY | 87.2% | 15,006 | 120m | 30,45,60,90,120 |
| 10 | USDJPY | 87.2% | 13,839 | 120m | 30,45,60,90,120 |
| 11 | EURUSD | 87.1% | 11,875 | 120m | 30,45,60,90,120 |
| 12 | XAGUSD | 87.1% | 15,710 | 120m | 30,45,60,90,120 |
| 13 | XRPUSD | 87.1% | 27,772 | 120m | 30,45,60,90,120 |
| 14 | GBPAUD | 86.9% | 14,351 | 120m | 30,45,60,90,120 |
| 15 | GBPCHF | 86.8% | 11,839 | 120m | 30,45,60,90,120 |
| 16 | NZDCAD | 86.7% | 11,610 | 120m | 30,45,60,90,120 |
| 17 | GBPNZD | 86.6% | 14,850 | 120m | 45,60,90,120 |
| 18 | USDCAD | 86.6% | 13,435 | 120m | 30,45,60,90,120 |
| 19 | AUDCHF | 86.5% | 12,196 | 120m | 45,60,90,120 |
| 20 | ETHUSD | 86.3% | 21,245 | 120m | 45,60,90,120 |
| 21 | AUDCAD | 86.2% | 12,263 | 120m | 45,60,90,120 |
| 22 | CADJPY | 86.2% | 12,569 | 120m | 45,60,90,120 |
| 23 | CADCHF | 86.1% | 12,148 | 120m | 45,60,90,120 |
| 24 | EURCAD | 86.1% | 13,418 | 120m | 45,60,90,120 |
| 25 | EURJPY | 86.1% | 13,830 | 120m | 45,60,90,120 |
| 26 | EURAUD | 86.0% | 14,034 | 120m | 45,60,90,120 |
| 27 | EURCHF | 86.0% | 12,179 | 120m | 45,60,90,120 |
| 28 | NZDJPY | 86.0% | 12,191 | 120m | 45,60,90,120 |
| 29 | EURGBP | 85.9% | 11,950 | 120m | 45,60,90,120 |
| 30 | EURNZD | 85.9% | 14,317 | 120m | 45,60,90,120 |
| 31 | NZDCHF | 85.9% | 11,602 | 120m | 45,60,90,120 |
| 32 | AUDJPY | 85.8% | 13,292 | 120m | 45,60,90,120 |
| 33 | GBPCAD | 85.6% | 11,372 | 120m | 45,60,90,120 |
| 34 | AUDNZD | 85.1% | 12,169 | 120m | 45,60,90,120 |

### 6.4 Key Findings

1. **Universal edge confirmed**: ALL 34 pairs exceed 85% WR at 120min with calibrated thresholds
2. **US500 #1 at 88.0%**: Indices show the strongest binary edge
3. **BTCUSD 87.6%**: Crypto has massive directional follow-through
4. **XRPUSD 87.1%**: Highest crypto at 27K+ signals
5. **Gold 87.3%**: Consistent with previous test
6. **EURUSD 87.1%**: Baseline pair, solid as expected
7. **GBP crosses 86-87%**: Confirms manual's GBP cluster finding
8. **JPY pairs 86-87%**: Higher vol but strong directional edge
9. **AUDNZD lowest at 85.1%**: Still well above 75% threshold
10. **30min cascade window**: Most pairs hit 75%+ WR at 30min expiry
11. **45min sweet spot**: 78-82% WR across most pairs
12. **1-3min = 0%**: Price needs minimum 5min to establish direction
13. **Calibrated vs universal**: Calibrated thresholds produce slightly lower but more accurate WR — no inflated results from wrong thresholds

### 6.5 Data Sources & Files

- `quant-lab/backtest/run_p90_binary_calibrated.py` — Per-asset calibrated binary test
- `quant-lab/reports/hyperliquid_full/p90_binary_calibrated_all_pairs.json` — Full results JSON
- `quant-lab/reports/P90_BINARY_FULL_BREAKDOWN.md` — Per-pair detailed breakdown
- `quant-lab/reports/P90_BINARY_TEST_FULL_RESULTS.md` — Earlier universal-threshold results

**MT5 Data**: BTCUSD, ETHUSD, SOLUSD, XRPUSD fetched June 16, 2026 (435K-463K bars)
**USDSEK**: Not available on OxSecurities broker

### 6.1 Methodology

**The simplest possible test of P90 edge — no targets, no SL, no tiers, no Asian Range filter.**

```
Window:        3AM-12PM EST (08:00-17:00 UTC)
Entry:         Close of P90 candle (body >= 90th percentile threshold for 2h bucket)
Direction:     LONG if close > open (bullish), SHORT if close < open (bearish)
Expiry:        Fixed time window (1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120 min)
Win:           ANY future M5 candle CLOSES in trade direction before expiry
Loss:          ANY future M5 candle CLOSES against trade direction before expiry
Timeout:       Neither within expiry window (excluded from WR)
```

**P90 Thresholds (by 2-hour UTC bucket):**
| UTC Hour | EST Hour | Threshold |
|----------|----------|-----------|
| 8-10 | 3-5AM | 4.1 pips |
| 10-12 | 5-7AM | 4.6 pips |
| 12-14 | 7-9AM | 4.6 pips |
| 14-16 | 9-11AM | 5.9 pips |
| 16-17 | 11AM-12PM | 6.2 pips |

**Source file:** `quant-lab/backtest/run_p90_binary_simple.py`
**Results file:** `quant-lab/reports/hyperliquid_full/p90_binary_simple_all_pairs.json`

### 6.2 Full Expiry Sweep Results (1-120 min)

**All 31 pairs tested (27 FX + 4 crypto). Every single pair exceeds 83% WR at 120min expiry.**

**Crypto pairs (new — fetched from MT5 June 16):**

| Pair | 5m | 10m | 15m | 20m | 30m | 45m | 60m | 90m | 120m | Best |
|------|-----|-----|-----|-----|-----|-----|-----|-----|------|------|
| XAUUSD | 48.6 | 61.0 | 67.5 | 71.4 | 76.4 | 80.6 | 83.4 | 86.6 | **88.4** | 120m |
| GBPJPY | 48.4 | 60.9 | 67.2 | 71.4 | 76.4 | 80.7 | 83.1 | 86.2 | **87.9** | 120m |
| GBPAUD | 47.9 | 60.5 | 67.0 | 71.0 | 76.2 | 80.3 | 83.0 | 86.1 | **87.9** | 120m |
| GBPNZD | 48.1 | 60.4 | 66.9 | 70.9 | 76.0 | 80.3 | 82.9 | 85.9 | **87.8** | 120m |
| XAGUSD | 48.2 | 60.5 | 66.8 | 70.7 | 75.6 | 80.0 | 82.7 | 85.7 | **87.5** | 120m |
| CHFJPY | 48.1 | 60.7 | 66.9 | 70.9 | 75.9 | 80.1 | 82.5 | 85.7 | **87.5** | 120m |
| EURCAD | 47.9 | 60.0 | 66.5 | 70.4 | 75.6 | 79.8 | 82.4 | 85.5 | **87.3** | 120m |
| EURNZD | 47.9 | 60.4 | 66.5 | 70.7 | 75.7 | 79.9 | 82.4 | 85.4 | **87.2** | 120m |
| USDCHF | 48.0 | 60.4 | 66.9 | 71.0 | 75.7 | 79.7 | 82.3 | 85.5 | **87.2** | 120m |
| GBPUSD | 48.5 | 60.6 | 67.1 | 71.2 | 76.0 | 80.1 | 82.7 | 85.8 | **87.7** | 120m |
| USDJPY | 48.4 | 61.0 | 67.4 | 71.3 | 76.1 | 80.1 | 82.6 | 85.8 | **87.6** | 120m |
| US500 | 49.9 | 61.9 | 67.8 | 71.4 | 76.4 | 80.2 | 82.8 | 85.9 | **87.6** | 120m |
| EURUSD | 47.8 | 59.9 | 66.1 | 70.0 | 75.1 | 79.1 | 81.8 | 85.3 | **87.1** | 120m |
| GBPCAD | 48.3 | 60.7 | 66.9 | 70.9 | 75.7 | 80.0 | 82.4 | 85.4 | **87.1** | 120m |
| AUDUSD | 47.3 | 60.0 | 66.2 | 70.1 | 75.4 | 79.6 | 82.2 | 85.1 | **87.0** | 120m |
| NZDUSD | 48.0 | 60.6 | 66.9 | 70.7 | 75.9 | 79.9 | 82.4 | 85.3 | **87.0** | 120m |
| EURAUD | 47.7 | 60.2 | 66.5 | 70.7 | 75.6 | 79.9 | 82.4 | 85.3 | **86.9** | 120m |
| USDCAD | 48.6 | 60.7 | 66.9 | 70.8 | 76.0 | 80.0 | 82.3 | 85.2 | **86.7** | 120m |
| AUDJPY | 47.4 | 60.1 | 66.4 | 70.1 | 75.1 | 79.4 | 81.8 | 84.9 | **86.7** | 120m |
| NZDCAD | 47.9 | 60.4 | 66.2 | 70.1 | 75.2 | 79.4 | 82.2 | 85.0 | **86.7** | 120m |
| CADJPY | 47.8 | 60.1 | 66.4 | 70.3 | 75.2 | 79.5 | 82.0 | 85.0 | **86.7** | 120m |
| EURJPY | 47.7 | 60.2 | 66.5 | 70.6 | 75.6 | 79.7 | 82.1 | 85.1 | **86.8** | 120m |
| GBPCHF | 47.9 | 59.8 | 65.9 | 70.0 | 75.2 | 79.2 | 81.8 | 85.2 | **86.8** | 120m |
| AUDCAD | 47.7 | 60.0 | 66.4 | 70.2 | 74.9 | 79.2 | 81.7 | 84.5 | **86.3** | 120m |
| AUDCHF | 46.7 | 58.7 | 65.0 | 69.0 | 74.1 | 78.3 | 81.1 | 84.4 | **86.2** | 120m |
| NZDJPY | 47.1 | 60.1 | 66.4 | 70.2 | 75.2 | 79.3 | 81.9 | 84.9 | **86.6** | 120m |
| NZDCHF | 46.6 | 58.0 | 64.4 | 67.9 | 73.5 | 77.3 | 80.2 | 83.4 | **85.4** | 120m |
| CADCHF | 46.8 | 58.9 | 65.5 | 69.4 | 74.3 | 78.3 | 80.9 | 84.2 | **85.8** | 120m |
| EURCHF | 46.0 | 58.2 | 64.5 | 68.2 | 73.6 | 78.1 | 80.6 | 84.0 | **85.8** | 120m |
| EURGBP | 45.9 | 58.5 | 64.6 | 68.6 | 73.6 | 78.0 | 80.6 | 84.1 | **85.9** | 120m |
| AUDNZD | 43.7 | 55.4 | 61.9 | 65.6 | 70.9 | 75.3 | 77.8 | 81.7 | **83.8** | 120m |
| XRPUSD | 46.9 | 59.4 | 66.1 | 70.3 | 75.5 | 79.9 | 82.6 | 85.8 | **87.8** | 120m |
| BTCUSD | 47.3 | 59.4 | 65.9 | 69.7 | 74.7 | 78.8 | 81.9 | 85.2 | **87.1** | 120m |
| SOLUSD | 47.0 | 59.2 | 65.7 | 69.6 | 74.5 | 78.8 | 81.7 | 84.9 | **87.1** | 120m |
| ETHUSD | 45.5 | 56.9 | 63.2 | 66.7 | 71.7 | 75.3 | 78.5 | 81.2 | **83.3** | 120m |

### 6.3 Key Findings

1. **Universal edge**: ALL 31 pairs (27 FX + 4 crypto) exceed 83% WR at 120min expiry
2. **Gold (XAUUSD) highest**: 88.4% WR at 120min
3. **XRPUSD 87.8%**: Strongest crypto, 30min expiry already at 75.5% WR
4. **BTCUSD 87.1%**: 45min expiry at 78.8% — solid cascade window
5. **SOLUSD 87.1%**: Matches BTC, 45min at 78.8%
6. **ETHUSD 83.3%**: Lowest crypto but still strong, needs 45min for 75%+ WR
7. **GBP crosses cluster 87-88%**: Confirms manual's "GBP cluster 89-91%" finding
8. **JPY pairs 85-88%**: Higher volatility but strong directional follow-through
9. **Indices (US500) 87.6%**: Strong edge even on indices
10. **AUDNZD lowest at 83.8%**: Still well above 75% threshold
11. **30min expiry = 75%+ WR** for most pairs → cascade add window
12. **45min expiry = 78-81% WR** → the "resolution sweet spot" from manual
13. **1-3min expiry = 0% WR**: Price needs at least 5 min to establish direction
14. **5min expiry ≈ 48% WR**: Essentially a coin flip on next candle
15. **USDSEK**: Not available on OxSecurities broker — needs alternative data source

### 6.4 Cascade Timing Implications

The binary test proves the cascade timing windows from the manual:

| Time After 1st P90 | Avg WR Across Pairs | Recommendation |
|--------------------|---------------------|----------------|
| 5-10 min | 48-60% | Too early — noise |
| 15-20 min | 66-71% | Approaching edge |
| **30-45 min** | **75-80%** | **Cascade add window** |
| **45-60 min** | **78-82%** | **Resolution sweet spot** |
| 60-90 min | 81-86% | Good continuation |
| 90-120 min | 84-88% | Late but valid |

**Operational rule**: Add cascade position at 30-45 min mark when binary WR crosses 75%.

### 6.5 Per-Asset Optimal Expiry Windows (WR ≥ 75%)

| Pair | Min Expiry for 75% WR | Optimal Expiry | Max WR |
|------|----------------------|----------------|--------|
| EURUSD | 30min | 120min | 87.1% |
| GBPUSD | 30min | 120min | 87.7% |
| USDCHF | 30min | 120min | 87.2% |
| USDJPY | 30min | 120min | 87.6% |
| AUDUSD | 30min | 120min | 87.0% |
| NZDUSD | 30min | 120min | 87.0% |
| EURGBP | 45min | 120min | 85.9% |
| EURJPY | 30min | 120min | 86.8% |
| EURAUD | 30min | 120min | 86.9% |
| EURNZD | 30min | 120min | 87.2% |
| EURCHF | 45min | 120min | 85.8% |
| EURCAD | 30min | 120min | 87.3% |
| USDCAD | 30min | 120min | 86.7% |
| CHFJPY | 30min | 120min | 87.5% |
| GBPJPY | 30min | 120min | 87.9% |
| GBPAUD | 30min | 120min | 87.9% |
| GBPNZD | 30min | 120min | 87.8% |
| GBPCHF | 30min | 120min | 86.8% |
| AUDJPY | 30min | 120min | 86.7% |
| AUDNZD | 45min | 120min | 83.8% |
| AUDCHF | 45min | 120min | 86.2% |
| AUDCAD | 45min | 120min | 86.3% |
| NZDJPY | 30min | 120min | 86.6% |
| NZDCHF | 45min | 120min | 85.4% |
| NZDCAD | 30min | 120min | 86.7% |
| CADJPY | 30min | 120min | 86.7% |
| CADCHF | 45min | 120min | 85.8% |
| GBPCAD | 30min | 120min | 87.1% |
| XAUUSD | 30min | 120min | 88.4% |
| XAGUSD | 30min | 120min | 87.5% |
| US500 | 30min | 120min | 87.6% |
| BTCUSD | 45min | 120min | 87.1% |
| ETHUSD | 45min | 120min | 83.3% |
| SOLUSD | 45min | 120min | 87.1% |
| XRPUSD | 30min | 120min | 87.8% |

### 6.6 Data Sources & Notes

**MT5 Data (OxSecurities-Live broker):**
- BTCUSD, ETHUSD, SOLUSD, XRPUSD: Fetched June 16, 2026 (463K-461K bars, 2022-2026)
- USDSEK: **NOT available** on this broker — needs alternative source
- All M5 data saved as `quant-lab/data/{SYMBOL}_M5.csv`

**Asset Config Additions:**
- XRPUSD: Added to `quant-lab/configs/asset_configs.py` (pip=0.0001, k=0.52, crypto tier)
- USDSEK: Added to `quant-lab/configs/asset_configs.py` (pip=0.0001, k=0.46, forex tier)
- BTCUSD, ETHUSD, SOLUSD: Already existed in config

**Files:**
- `quant-lab/backtest/run_p90_binary_simple.py` — Main binary test (FX pairs)
- `quant-lab/backtest/run_p90_binary_new_pairs.py` — Crypto pairs binary test
- `quant-lab/reports/hyperliquid_full/p90_binary_simple_all_pairs.json` — Full results JSON
