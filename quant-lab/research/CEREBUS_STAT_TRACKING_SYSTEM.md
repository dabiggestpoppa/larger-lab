# 📊 CEREBUS Stat Tracking System — Complete Documentation

> **Date:** 2026-05-19 09:30 EDT  
> **Source:** `cerebus 3 market hoily grail.xlsx` (97 sheets, 10.5MB)  
> **Purpose:** Document ALL metrics MAD tracks and the exact formulas used  
> **Classification:** INTERNAL — MAD EYES ONLY

---

## 1. OVERVIEW

MAD's CEREBUS system tracks **2,134+ ILM zone touches**, **281 weeks of Fibonacci data**, **487+ pattern formations**, and **356+ timeframe transitions** across multiple instruments. The stat tracking methodology is organized into 97 Excel sheets grouped into phases.

### Core Philosophy
- **Everything is measured** — no claim without data
- **Confidence intervals** on every hit rate (Wilson score, 95%)
- **Session-aware** — all metrics broken down by session
- **Temporal patterns** — day-of-week, weekly, quarterly, monthly
- **Cross-market validation** — same patterns tested across all pairs

---

## 2. HIT RATE CALCULATIONS

### 2.1 Basic Hit Rate
```
Hit Rate = (Hits / Total) × 100
```
- **Hit** = price reached the target level before invalidation
- **Total** = total occurrences of the setup
- Tracked as percentage with 2 decimal places

### 2.2 Wilson Score Confidence Interval (95%)
```
z = 1.96
p = hits / total

CI_low  = p - z × √(p × (1-p) / n)
CI_high = p + z × √(p × (1-p) / n)
```

MAD uses this to validate statistical significance. A claim is only "confirmed" when the CI doesn't overlap with random (50%).

### 2.3 Hit Rate Summary (from `hit_rate_summary` sheet)

| Fib Level | Hit Rate | Total Weeks | Hits |
|-----------|----------|-------------|------|
| **-25%**  | 98.22%   | 281         | 276  |
| **-50%**  | 96.44%   | 281         | 271  |
| **-100%** | 92.17%   | 281         | 259  |
| **-132%** | 87.19%   | 281         | 245  |
| **-168%** | 71.53%   | 281         | 201  |
| **132% Violation** | 71.53% | 281   | 201  |

**Key insight:** The -25% and -50% levels are near-certain (>95% hit rate). The -132% level is the "violation" threshold — when price exceeds this, the pattern is considered failed/invalidated.

---

## 3. FIBONACCI LEVEL TRACKING

### 3.1 Extension Targets (from `Delivery Stats`)

| Target | Hit Rate | Confidence | Sample | Notes |
|--------|----------|------------|--------|-------|
| -25% extension | 90% | High | Multiple sessions | Claimed in multiple documents |
| -50% extension | 82% | High | Multiple sessions | Claimed across reports |
| 72% retracement continuation | 83.5% | ±3.2% | London-NY sessions | Strongest during overlap |

### 3.2 Fibonacci Sequence Catalog (from `Fibonacci Sequences Catalog`)

MAD catalogs common Fibonacci sequences and their completion rates. The primary sequence:

```
AB (72%) → BC (-25%) → CD (61.8%)
```
- **Success rate:** 81.2% (487 patterns tested)
- **Confidence interval:** ±2.8%
- **Source docs:** Doc 8, 15

### 3.3 Monday Fibonacci (from `monday_fibonacci_calculations`)

**Methodology:**
1. Calculate Monday's London session range (open to close)
2. Project Fibonacci extensions from this range
3. Use as targets for Tuesday-Friday
4. Track hit rates per level per day

### 3.4 Thursday Range Targets (from `thursday_range_targets`)

**Methodology:**
1. Calculate Thursday's range
2. Project targets for Friday
3. Thursday has unique delivery profile (end-of-week positioning)

### 3.5 Previous Day Targets (from `previous_day_targets`)

**Methodology:**
1. Calculate previous day's range
2. Project -25% and -50% Fibonacci targets
3. Use as entry/exit levels for current day

---

## 4. SESSION-BASED METRICS

### 4.1 Session Definitions (from `Session & Timing Metrics`)

| Session | Time (UTC) | Label | Characteristics |
|---------|-----------|-------|-----------------|
| **Asian** | 00:00-08:00 | Tokyo+Sydney | Establishes baseline range |
| **London** | 08:00-16:00 | London | Primary trend session |
| **NY** | 13:00-21:00 | New York | Secondary trend session |
| **Overlap** | 13:00-16:00 | London-NY | Highest continuation probability |

### 4.2 Session Performance (from `PHASE 6 - SESSION PROFILE SYNTHESIS`)

- **London-NY Overlap:** 83.5% continuation rate (strongest)
- **Asian Session:** Establishes the baseline for London/NY targets
- **Best session for DMR:** 7-11 UTC
- **Worst session for DMR:** 2-4 UTC (Asian session)

### 4.3 Session Correlation Matrix (from `PHASE 3 - SESSION CORRELATION MATRIX`)

Tracks how sessions interact:
- Asian range → London continuation probability
- London close → NY continuation probability
- Overlap period → daily close correlation

### 4.4 Full Week Session Data (from `session_data_full_week`)

Complete breakdown of all metrics by session by day of week. 1000 rows × 200 columns of granular data.

---

## 5. REKEY PROBABILITY TRACKING

### 5.1 Rekey Definition (from `REKEY HYPOTHESIS TEST RESULTS`)

A "rekey" occurs when:
1. A lower-timeframe pattern (15M) forms under an ILM zone
2. Multiple consecutive patterns fail to break the zone
3. The higher-timeframe (4H) pattern "rekeys" — resets its Fibonacci levels

### 5.2 Rekey Conditions

| Condition | Probability | Occurrences | Source |
|-----------|-------------|-------------|--------|
| **15M 61.8-88% under WILM → 4H rekey** | 94.3% | 218 | Doc 20 |
| Consecutive 15M failures under Daily ILM | ~85% | 356+ | Doc 14, 19 |
| AB→BC→CD pattern failure → rekey | ~78% | 487 | Doc 8, 15 |

### 5.3 Rekey Probability Formula
```
P(rekey) = consecutive_LTF_failures / total_LTF_attempts_under_ILM
```

MAD tracks this per ILM type and per timeframe combination.

---

## 6. TEMPORAL PATTERN METRICS

### 6.1 Day-of-Week Delivery (from `quarterly_analysis`, `session_data_full_week`)

MAD tracks which days deliver the highest hit rates for specific setups:

- **Monday:** Fibonacci calculation day (sets weekly targets)
- **Tuesday-Thursday:** Primary delivery days
- **Friday:** Thursday range targets, end-of-week positioning

### 6.2 Weekly Correlation (from `PHASE 3 - Weekly Correlation & 132% Analysis`)

- Weekly range correlation with daily delivery
- 132% weekly extension analysis
- Monday-to-Friday delivery sequence

### 6.3 Monthly Range Reconnaissance (from `PHASE 4` series)

- Monthly range calculation
- Range window testing (how price behaves at monthly extremes)
- Group A vs Group B analysis (different market conditions)
- Threshold test results

### 6.4 Quarterly Analysis (from `quarterly_analysis`)

- Data grouped into quarters
- Trend detection across quarters
- Seasonal pattern identification

---

## 7. CROSS-MARKET COMPARISON METHODOLOGY

### 7.1 Instruments Tracked

**Forex:**
- EUR/USD, USD/CHF, GBP/USD, USD/JPY
- USD/CAD, AUD/USD, NZD/USD, CHF/JPY

**Indices:**
- DE30 (Germany), FR40 (France)
- US500 (S&P 500), USTEC100 (Nasdaq)

**Commodities:**
- OIL/USD (from OILUSD_H4 and OILUSD_H1 sheets)

### 7.2 Comparison Methodology

Same Fibonacci levels and session analysis applied uniformly:
1. Calculate session ranges per instrument
2. Apply same Fibonacci extensions
3. Compare hit rates across instruments
4. Identify which instruments have highest delivery rates
5. Cross-reference ILM zone behaviors

---

## 8. ILM (INSTITUTIONAL LIQUIDITY MATRIX) ZONE ANALYSIS

### 8.1 ILM Types (from `ILM Zone Behaviors`)

| ILM Type | Hit Rate | Sample | Notes |
|----------|----------|--------|-------|
| **Daily ILM** | 69.0% | 2,134 touches | Most reliable |
| **IELM** (Intraday Extreme) | 48.3% | 2,134 touches | Moderate |
| **WILM** (Weekly) | 34.2% | 2,134 touches | Least reliable alone |

### 8.2 ILM Continuation vs Reversal

- **Continuation:** 65% (price touches ILM and continues in original direction)
- **Reversal:** 35% (price touches ILM and reverses)
- **Sample:** 1,567 setups

### 8.3 ILM Zone Interaction (from `PHASE 5 - WILM ILM VELOCITY ANALYSIS`)

- Velocity of price approaching ILM zones
- Hit rate by approach angle/speed
- Continuation probability by ILM type

### 8.4 Quarter Level Interaction

- **Hit rate:** 80.5% (3,421 touches)
- **Confidence:** ±10 points
- **Highest precision targeting** of all ILM types

---

## 9. PATTERN FORMATION TRACKING

### 9.1 Pattern Types (from `Pattern Formations`)

| Pattern | Hit Rate | Sample | CI | Source |
|---------|----------|--------|-----|--------|
| **AB(72%)→BC(-25%)→CD(61.8%)** | 81.2% | 487 | ±2.8% | Doc 8, 15 |
| **Alpha sequence formation** | 76.3-78.3% | 892 | Range | Doc 7, 13 |
| **Daily pivot from 1H rekey** | 72.9-78.3% | 1,245 | Range | Doc 3, 11, 16 |

### 9.2 Pattern Failures (from `Pattern Failures & Rekeys`)

- Tracks WHY patterns fail
- Failure → rekey probability
- Consecutive failure tracking
- ILM zone failure correlation

### 9.3 Failure Pattern Database (from `failure_pattern_database`)

Systematic catalog of:
- Failure conditions
- Pre-failure signatures
- Post-failure behavior
- Rekey probability per failure type

---

## 10. TOLERANCE-BASED ENTRY ANALYSIS

### 10.1 Tolerance Bands (from `TOLERANCE_COMPARISON_0.15_0.25_0.50`)

MAD tests three tolerance levels for Fibonacci entries:

| Tolerance | Description | Effect |
|-----------|-------------|--------|
| **±0.15** | Tightest | Fewer entries, highest quality |
| **±0.25** | Medium | Balance of quality and frequency |
| **±0.50** | Widest | Most entries, lower quality |

### 10.2 Application

Applied to Fibonacci level entries to filter noise:
- Price must be within tolerance band of the Fib level to count as valid entry
- Tighter tolerance = fewer false signals but may miss valid moves
- Wider tolerance = more entries but more false signals

---

## 11. TIMEFRAME TRANSITION ANALYSIS

### 11.1 1H → 4H Transition (from `PHASE 3B/3C` sheets)

- **Hit rate:** 76.2-89.5% (range)
- **Sample:** 356 transitions
- **Enhancement factor:** WILM presence increases transition success

### 11.2 15M → 4H Rekey

- **Trigger:** Consecutive 15M 61.8-88% patterns under WILM
- **Success:** 94.3% (highest probability rekey condition)
- **Sample:** 218 occurrences

---

## 12. VALIDATION FRAMEWORK

### 12.1 Top 10 Claims Testing (from `Top 10 Claims - Testing Framework`)

MAD's methodology for validating claims:
1. State the claim clearly
2. Define hit/miss criteria
3. Count total occurrences
4. Calculate hit rate
5. Compute confidence interval
6. Compare to random baseline (50%)
7. Classify: Confirmed / Probable / Unconfirmed / Rejected

### 12.2 Validation Checklist (from `Validation Checklist`)

Systematic checklist for each claim:
- [ ] Sample size ≥ 100
- [ ] Hit rate > 60%
- [ ] CI doesn't overlap 50%
- [ ] Multiple timeframes confirmed
- [ ] Multiple instruments confirmed
- [ ] Session breakdown consistent

### 12.3 Measurement Comparison (from `measurement_comparison`)

Compares different measurement methodologies:
- Close-to-close vs high/low vs wick
- Different session boundary definitions
- Different Fibonacci calculation methods

---

## 13. UNIQUE CALCULATIONS & METHODOLOGIES

### 13.1 WILM Enhancement Factor

When a Weekly ILM zone is present, it enhances:
- Timeframe transition success (+13.3% for 1H→4H)
- Pattern formation reliability
- Rekey probability

### 13.2 Session Overlap Multiplier

During London-NY overlap (13:00-16:00 UTC):
- Continuation probability increases
- Fibonacci targets have higher hit rates
- Pattern formations are more reliable

### 13.3 Consecutive Failure Weighting

MAD weights consecutive failures exponentially:
- 1 failure: baseline rekey probability
- 2 consecutive: 1.5× probability
- 3 consecutive: 2.2× probability
- 4+ consecutive: 3.0× probability (near-certain rekey)

### 13.4 Low-Frequency High-Accuracy Tracker (from `Low-Freq High-Accuracy Tracker`)

Tracks rare but high-probability setups:
- Occur less frequently but have >85% hit rates
- Require multiple confluence factors
- ILM + Fibonacci + Session + Timeframe alignment

---

## 14. DATA ORGANIZATION FRAMEWORK

### 14.1 Phase Structure

| Phase | Focus | Sheets |
|-------|-------|--------|
| Phase 2 | Validation & baseline metrics | PHASE 2 VALIDATION RESULTS, Delivery Stats, Pattern Formations, Pattern Failures & Rekeys, ILM Zone Behaviors, Session & Timing Metrics, Fibonacci Sequences Catalog, Validation Checklist, Failure Pattern Database |
| Phase 3 | Weekly correlation & 132% analysis | PHASE 3 series (Weekly Correlation, 132% Deep Dive, Comprehensive Analysis, Temporal Delivery) |
| Phase 4 | Monthly range reconnaissance | PHASE 4 series (Monthly Range, Dataset, Range Window Testing, Group Analysis) |
| Phase 5 | WILM velocity analysis | PHASE 5 - WILM ILM VELOCITY ANALYSIS |
| Phase 6 | Session profile synthesis | PHASE 6 - SESSION PROFILE SYNTHESIS |
| Phase 7 | Model synthesis & integration | PHASE 7 - MODEL SYNTHESIS & INTEGRATION |

### 14.2 Sheet Naming Convention

- **PHASE X** — Phase results and analysis
- **hit_rate_summary** — Master hit rate table
- **Delivery Stats** — Claim/pattern delivery rates
- **TOLERANCE_COMPARISON** — Tolerance band results
- **OILUSD_H4/H1** — Instrument-specific data

---

## 15. INTEGRATION WITH BACKTEST FRAMEWORK

### 15.1 How to Use in Backtests

```python
from cerebus_stat_tracker import CerebusStatTracker

tracker = CerebusStatTracker()

# Load your backtest results
trades = [
    {"result": "win", "pnl": 5.2, "session": "London", "fib_level": "-25%", ...},
    ...
]
tracker.load_trades(trades)

# Generate report
report = tracker.generate_full_report()
print(report)

# Or get specific metrics
fib_analysis = tracker.fib_level_analysis()
session_perf = tracker.session_analysis()
rekey_prob = tracker.rekey_probability()
```

### 15.2 Validation Criteria

A strategy is considered **validated** when:
1. Overall hit rate > 60%
2. 95% CI doesn't overlap 50%
3. Sample size ≥ 100 trades
4. Profitable across multiple sessions
5. Profitable across multiple instruments
6. Positive expectancy after costs

---

## 16. KEY REFERENCE VALUES

From MAD's Excel (ground truth):

| Metric | Value | Source Sheet |
|--------|-------|-------------|
| -25% Fib hit rate | 98.22% (276/281) | hit_rate_summary |
| -50% Fib hit rate | 96.44% (271/281) | hit_rate_summary |
| -100% Fib hit rate | 92.17% (259/281) | hit_rate_summary |
| -132% Fib hit rate | 87.19% (245/281) | hit_rate_summary |
| -168% Fib hit rate | 71.53% (201/281) | hit_rate_summary |
| AB→BC→CD pattern | 81.2% (487 patterns) | Delivery Stats |
| 72% retracement continuation | 83.5% | Delivery Stats |
| 1H→4H transition | 76.2-89.5% | Delivery Stats |
| Rekey (best condition) | 94.3% (218 occ) | Delivery Stats |
| Daily ILM hit rate | 69.0% (2134 touches) | Delivery Stats |
| IELM hit rate | 48.3% | Delivery Stats |
| WILM hit rate | 34.2% | Delivery Stats |
| ILM continuation | 65% vs 35% reversal | Delivery Stats |
| Quarter level hit rate | 80.5% (3421 touches) | Delivery Stats |
| Alpha pattern | 76.3-78.3% (892 patterns) | Delivery Stats |
| Daily pivot from 1H rekey | 72.9-78.3% (1245 days) | Delivery Stats |

---

*This document is the authoritative reference for MAD's stat tracking methodology.*
*All values sourced directly from the CEREBUS Excel file.*
*Last updated: 2026-05-19*
