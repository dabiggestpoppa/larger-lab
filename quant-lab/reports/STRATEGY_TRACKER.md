# 📊 CEREBUS Quant Lab — Strategy Tracker

> **Created:** 2026-05-17
> **Manager:** QuantLab-Mgr
> **Last Updated:** 2026-05-17 00:38 EDT

## Status Legend
- ✅ **Complete** — Implemented, tested, backtested
- 🔄 **In Progress** — Currently being worked on
- 📋 **Planned** — Scheduled, not started
- ⚠️ **Blocked** — Waiting on dependency
- ❌ **Failed** — Backtest did not meet targets

---

## Strategy Status Overview

| # | Strategy | Phase | Status | WR Target | Daily R Target | Module |
|---|----------|-------|--------|-----------|----------------|--------|
| 1 | P90 Base (CFD Expansion) | 1 | 🔄 Exists | 83.3% | 0.11%* | `p90_base.py` |
| 2 | P90 Cascade Activation | 1 | 📋 Planned | 87.8% | — | `p90_cascade.py` |
| 3 | P90 45-Min Add | 1 | 📋 Planned | 91.2% | — | `p90_45min_add.py` |
| 4 | P90 Cascade + 45-Min Combo | 1 | 📋 Planned | 93.4% | — | `p90_combo.py` |
| 5 | Deep Mean Rebalancing | 2 | 📋 Planned | 78-84% | — | `deep_mean_rebal.py` |
| 6 | Over-Extension Runner | 2 | 📋 Planned | — | +15% add | `over_extension_runner.py` |
| 7 | P90P Distribution Tracker | 2 | 📋 Planned | — | — | `p90p_tracker.py` |
| 8 | Stall-Harvest System | 3 | 📋 Planned | 82-94% | — | `stall_harvest.py` |
| 9 | Monday Asian Float | 3 | 📋 Planned | — | — | `monday_asian_float.py` |
| 10 | Daily Asian Float | 3 | 📋 Planned | — | — | `daily_asian_float.py` |
| 11 | Full-Day Range Regime | 3 | 📋 Planned | — | — | `range_regime.py` |
| 12 | Dual-Engine Execution | 3 | 📋 Planned | — | — | `dual_engine.py` |
| 13 | Failure Repair Model | 4 | 📋 Planned | — | DD -20% | `failure_repair.py` |
| 14 | Two Plays Framework | 4 | 📋 Planned | — | — | `two_plays.py` |
| 15 | Monte Carlo Validation | 4 | 📋 Planned | — | — | `monte_carlo_val.py` |
| 16 | Blind Structural Chain | 4 | 📋 Planned | — | — | `blind_structural.py` |
| 17 | Fractal Resolution Engine | 4 | 📋 Planned | — | — | `fractal_resolution.py` |
| 18 | Daily Setups 1-6 | 4 | 📋 Planned | — | — | `daily_setups.py` |
| 19 | Atomic Market Structure | 4 | 📋 Planned | — | — | `atomic_market.py` |

*P90 Base existing backtest: 147 trades, 0.11% return (needs Nautilus port + cascade to reach target)

---

## Phase 1: Core P90 (Week 1) — 📋 Not Started

### Strategy 1: P90 Base (CFD Expansion Engine)
- **Status:** 🔄 Exists (needs Nautilus port)
- **Manual:** Part 1, Pages 5-6
- **Key Logic:** P90 candle detection → 3-position pyramid → -25%/-50% targets
- **Parameters:**
  - P90 thresholds: 4.1p (2-4AM), 4.6p (4-8AM), 5.9p (8-10AM), 6.2p (10-11AM)
  - Signal 1: 40% @ 80% body boundary → -25% target
  - Signal 2: 40% @ 1.5x body boundary → -25% target
  - Signal 3: 20% @ breakeven → -50% target
- **Existing Results:** 147 trades, 0.11% return (Autopilot v3, not Nautilus)
- **Nautilus Port:** Required — existing code at `projects/trading/backtests/`
- **Blockers:** None

### Strategy 2: P90 Cascade Activation
- **Status:** 📋 Planned
- **Manual:** Part 2, Pages 10-15
- **Key Logic:** 2nd/3rd P90 in same direction within 120min window
- **Parameters:**
  - Max cascades: 3 per session
  - Cascade boundary: 168% of cascade P90 body
  - Optimal timing: 45-60 min after initial
  - Cascade 1 size: 20%, Cascade 2 size: 10%
- **Expected WR:** 87.8% (2nd cascade), 84.2% (3rd cascade)
- **Blockers:** Depends on P90 Base port

### Strategy 3: P90 45-Min Add
- **Status:** 📋 Planned
- **Manual:** Part 2, Pages 12-13
- **Key Logic:** Time-based add after 45min if resolution output +8p
- **Parameters:**
  - Trigger: 45 min after Signal 1 + 8 pip extension
  - Size: 30% (or 20% if standalone)
  - Boundary: Breakeven (Signal 1)
  - Target: -50% Asian Range
- **Expected WR:** 91.2%
- **Blockers:** Depends on P90 Base port

### Strategy 4: P90 Cascade + 45-Min Combo
- **Status:** 📋 Planned
- **Manual:** Part 2, Page 13
- **Key Logic:** Both cascade AND 45-min triggers = highest conviction
- **Parameters:**
  - Signal 1: Initial P90 (40%)
  - Signal 2: 45-Min Add (30%)
  - Signal 3: Cascade P90 (30%)
  - Total: 100% size across 3 activations
- **Expected WR:** 93.4% ⭐ HIGHEST EDGE
- **Blockers:** Depends on Strategies #2 and #3

---

## Phase 2: Advanced P90 (Week 2) — 📋 Not Started

### Strategy 5: Deep Momentum Rebalancing
- **Status:** 📋 Planned
- **Manual:** Part 1, Pages 6-7
- **Key Logic:** Limit order at 200% Deep State, momentum continuation to distribution tail (NOT mean reversion — this is a momentum ride to -50% daily extension)
- **Parameters:**
  - Trigger: 168% or 200% extension touched
  - Limit order: At 200% level
  - Stop: 8 pips beyond 200% (~220%)
  - TP1: Return to 0% (activation level)
  - TP2: -50% daily range
  - R:R: 1:5 to 1:7
- **Expected WR:** 84% (2-6AM), 78% (6-9AM), 74% (9-12PM)
- **Blockers:** None (independent strategy)

### Strategy 6: Over-Extension Runner
- **Status:** 📋 Planned
- **Manual:** Part 1, Pages 7-8
- **Key Logic:** Hold runner to daily -50% after Asian -50% hit before 11AM
- **Parameters:**
  - Trigger: Asian -50% target hit before 11 AM EST
  - Close 50% at Asian -50%
  - Move SL to breakeven + 2 pips
  - Target: Daily -50%
  - Hard exit: 12 PM EST
- **Expected Impact:** +15% to daily returns when triggered
- **Blockers:** Depends on P90 Base (needs position tracking)

### Strategy 7: P90P Distribution Tracker
- **Status:** 📋 Planned
- **Manual:** Part 5, Page 30+
- **Key Logic:** 2AM/6AM/9AM checkpoints for regime detection
- **Parameters:**
  - Checkpoints: 2 AM, 6 AM, 9 AM EST
  - Regime shift: Daily Range > 1.5x Asian Range
  - Distribution tracking across sessions
- **Expected Impact:** Improves all other strategies' filter accuracy
- **Blockers:** None (independent, but enhances Phase 1 strategies)

---

## Phase 3: Expert Systems (Week 3-4) — 📋 Not Started

### Strategy 8: Stall-Harvest System
- **Status:** 📋 Planned
- **Manual:** Part 4, Pages 20-29
- **Key Logic:** Resolution output stall at 168% → unified CFD+Binary execution
- **Parameters:**
  - CFD leg: Limit at 168%, SL at 200%, TP at -50% daily
  - Binary leg: Dynamic expiry (90min early, 60min mid, 45min late)
  - Session WR: 94.2% (2-4AM), 88.6% (4-7AM), 82.4% (7-11AM)
  - True rejection rate: 64.2%
- **Expected WR:** 82-94% depending on session
- **Blockers:** Complex — needs both CFD and Binary engine support

### Strategy 9: Monday Asian Float
- **Status:** 📋 Planned
- **Manual:** Part 7, Page 38+
- **Key Logic:** Monday-specific Asian range behavior
- **Parameters:** TBD (needs manual deep-dive)
- **Blockers:** Needs researcher analysis of Monday-specific data

### Strategy 10: Daily Asian Float
- **Status:** 📋 Planned
- **Manual:** Part 8, Page 43+
- **Key Logic:** Daily Asian range float mechanism
- **Parameters:** TBD (needs manual deep-dive)
- **Blockers:** Needs researcher analysis

### Strategy 11: Full-Day Range Regime
- **Status:** 📋 Planned
- **Manual:** Part 10, Page 51+
- **Key Logic:** Regime-based daily range tracking
- **Parameters:** TBD
- **Blockers:** Needs researcher analysis

### Strategy 12: Dual-Engine Execution
- **Status:** 📋 Planned
- **Manual:** Part 10, Page 58+
- **Key Logic:** CFD + Binary/Momentum engines working together (momentum ride, NOT mean reversion)
- **Parameters:** TBD
- **Blockers:** Depends on CFD engine (P90 Base) and Binary engine support

---

## Phase 4: Meta-Strategies (Week 5+) — 📋 Not Started

### Strategy 13: Failure Repair Model
- **Status:** 📋 Planned
- **Manual:** Part 11, Page 78+
- **Key Logic:** Failure sequence analysis & auto-repair protocol
- **Expected Impact:** Reduces drawdown by >20%
- **Blockers:** Needs sufficient backtest data from Phase 1-3

### Strategy 14: Two Plays Framework
- **Status:** 📋 Planned
- **Manual:** Part 12, Page 79+
- **Key Logic:** Final execution framework — unified decision engine
- **Blockers:** Depends on multiple strategies being implemented first

### Strategy 15: Monte Carlo Validation
- **Status:** 📋 Planned
- **Manual:** Part 6 + Part 13, Pages 35 + 85+
- **Key Logic:** Triple-engine Monte Carlo simulation for strategy validation
- **Expected Impact:** Confirms statistical edge, estimates tail risk
- **Blockers:** Needs backtest results from all strategies

### Strategy 16: Blind Structural Chain
- **Status:** 📋 Planned
- **Manual:** Part 14, Page 90+
- **Key Logic:** Recursive loop engine for structural analysis
- **Blockers:** Complex — needs PM + Optimizer collaboration

### Strategy 17: Fractal Resolution Engine
- **Status:** 📋 Planned
- **Manual:** Part 15, Page 100+
- **Key Logic:** Nested cycle analysis across timeframes
- **Blockers:** Complex — needs multi-timeframe data

### Strategy 18: Daily Setups 1-6
- **Status:** 📋 Planned
- **Manual:** Daily Setups, Page 109+
- **Key Logic:** Context framework + 6 daily setup ideas
- **Blockers:** Needs researcher analysis of manual pages 109-130

### Strategy 19: Atomic Market Structure
- **Status:** 📋 Planned
- **Manual:** Atomic Market Structure, Page 131+
- **Key Logic:** Density zone, grand unified equation, shift targets
- **Blockers:** Most complex — needs extensive research

---

## Progress Metrics

### Implementation Progress
| Phase | Total | Complete | In Progress | Planned | % Done |
|-------|-------|----------|-------------|---------|--------|
| Phase 1 | 4 | 0 | 1 | 3 | 25% (exists, not ported) |
| Phase 2 | 3 | 0 | 0 | 3 | 0% |
| Phase 3 | 5 | 0 | 0 | 5 | 0% |
| Phase 4 | 7 | 0 | 0 | 7 | 0% |
| **Total** | **19** | **0** | **1** | **18** | **5%** |

### Backtest Results (So Far)
| Strategy | Trades | WR | Daily Return | Status |
|----------|--------|-----|-------------|--------|
| P90_Base_Strategy | 147 | TBD | 0.11% | 🔄 Needs Nautilus port |
| RSI_Reversion | 349 | TBD | 0.33% | ❌ Not CEREBUS |
| Asian_Breakout | 1270 | TBD | 0.06% | ❌ Not CEREBUS |

### Targets vs Current
| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| Win Rate | 85-90% | ~83% (est.) | -2% to -7% |
| Daily Return | 1.0-1.5% | 0.33% | -0.67% to -1.17% |
| Max DD | <0.50% | TBD | — |

---

## Change Log

| Date | Change | By |
|------|--------|-----|
| 2026-05-17 | Initial LAB_PLAN.md and STRATEGY_TRACKER.md created | QuantLab-Mgr |
| 2026-05-17 | All 19 strategies inventoried from manual | QuantLab-Mgr |
| 2026-05-17 | Phase 1-4 implementation plan defined | QuantLab-Mgr |
| 2026-05-17 | Agent task assignments created | QuantLab-Mgr |
