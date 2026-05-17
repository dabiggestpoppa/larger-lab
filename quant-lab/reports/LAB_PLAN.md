# 🧪 CEREBUS Quant Lab — Master Plan

> **Created:** 2026-05-17
> **Manager:** QuantLab-Mgr (OWL Sub-Agent)
> **Lab Version:** 1.0.0
> **Target Instrument:** EUR/USD M5
> **Nautilus Backend:** `projects/trading/nautilus/`

---

## 🎯 Mission

Reconstruct all 19 strategies from the CEREBUS FX manual as individual, backtestable Nautilus Trader strategies. Achieve stated performance targets through systematic implementation, testing, and optimization.

---

## 📊 Performance Targets (from Manual)

| Metric | Target | Current Best | Gap |
|--------|--------|-------------|-----|
| Win Rate (Filtered) | 85% – 90% | ~83% (P90 base) | -2% to -7% |
| Daily Return | 1.0% – 1.5% | 0.33% (RSI_Reversion) | -0.67% to -1.17% |
| Max Daily Drawdown | < 0.50% | TBD | — |
| Prop Firm Circuit Breaker | 0.40% loss | TBD | — |
| Risk Per Activation | 0.12% of Equity | TBD | — |
| Max Concurrent Risk | 0.36% (3 signals) | TBD | — |

**Key Insight:** The P90 base strategy alone is insufficient. Cascade activation + 45-min add combo (93.4% WR stated) is the primary path to target. Deep Mean Rebalancing (1:5 to 1:7 R:R) is the secondary edge.

---

## 📋 Full Strategy Inventory (19 Strategies)

### CORE P90 STRATEGIES (Manual Part 1-3, Pages 5-19)

| # | Strategy | Manual Ref | Key Logic | Nautilus Module |
|---|----------|------------|-----------|-----------------|
| 1 | **P90 Base (CFD Expansion Engine)** | Part 1, P5-6 | P90 candle → 3-position pyramid → -25%/-50% targets | `p90_base.py` ✅ Converted |
| 2 | **P90 Cascade Activation** | Part 2, P10-15 | 2nd/3rd P90 same direction, 168% boundary, 120min window | `p90_cascade.py` |
| 3 | **P90 45-Min Add** | Part 2, P12-13 | Time-based add after 45min + 8p extension | `p90_45min_add.py` |
| 4 | **P90 Cascade + 45-Min Combo** | Part 2, P13 | Both triggers = 93.4% WR (highest edge) | `p90_combo.py` |
| 5 | **Deep Momentum Rebalancing** | Part 1, P6-7 | 168%/200% stall zone → limit order at extension, ride to -50% tail, 1:5-1:7 R:R | `deep_momentum_rebal.py` |
| 6 | **Over-Extension Runner** | Part 1, P7-8 | Hold runner to daily -50% after Asian -50% hit | `over_extension_runner.py` |
| 7 | **P90P Distribution Tracker** | Part 5, P30+ | 2AM/6AM/9AM checkpoints, regime detection | `p90p_tracker.py` |

### ADVANCED STRATEGIES (Manual Part 4-11)

| # | Strategy | Manual Ref | Key Logic | Nautilus Module |
|---|----------|------------|-----------|-----------------|
| 8 | **Stall-Harvest System** | Part 4, P20-29 | Resolution output stall at 168% → CFD+Binary unified execution | `stall_harvest.py` |
| 9 | **Monday Asian Float** | Part 7, P38+ | Monday-specific Asian range behavior | `monday_asian_float.py` |
| 10 | **Daily Asian Float** | Part 8, P43+ | Daily Asian range float mechanism | `daily_asian_float.py` |
| 11 | **Full-Day Range Regime** | Part 10, P51+ | Regime-based daily range tracking | `range_regime.py` |
| 12 | **Dual-Engine Execution** | Part 10, P58+ | CFD + Binary/Momentum engines (extension-based, NOT reversion) | `dual_engine.py` |
| 13 | **Failure Repair Model** | Part 11, P78+ | Failure sequence analysis & auto-repair | `failure_repair.py` |
| 14 | **Two Plays Framework** | Part 12, P79+ | Final execution framework (unified) | `two_plays.py` |
| 15 | **Monte Carlo Validation** | Part 6+13, P35+85 | Triple-engine Monte Carlo validation | `monte_carlo_val.py` |
| 16 | **Blind Structural Chain** | Part 14, P90+ | Recursive loop engine | `blind_structural.py` |
| 17 | **Fractal Resolution Engine** | Part 15, P100+ | Nested cycle analysis | `fractal_resolution.py` |
| 18 | **Daily Setups 1-6** | Daily Setups, P109+ | Context framework + 6 daily setup ideas | `daily_setups.py` |
| 19 | **Atomic Market Structure** | Atomic, P131+ | Density zone, grand unified equation, shift targets | `atomic_market.py` |

---

## 🗓️ Implementation Phases

### Phase 1: Core P90 — Week 1 (HIGHEST PRIORITY)
**Goal:** Implement the core P90 engine with cascade and combo logic
**Target:** 87-93% WR, capture primary edge

| Priority | Strategy | Agent | Est. Effort |
|----------|----------|-------|-------------|
| 1 | P90 Base (refactor to Nautilus) | Optimizer | 2-4 hrs (exists, needs port) |
| 2 | P90 Cascade Activation | Optimizer | 4-6 hrs |
| 3 | P90 45-Min Add | Optimizer | 3-4 hrs |
| 4 | P90 Cascade + 45-Min Combo | Optimizer | 2-3 hrs (combines #2+#3) |

**Phase 1 Gate Criteria:**
- [ ] All 4 strategies pass unit tests
- [ ] Backtest shows >85% WR on EUR/USD M5 (2022-2026)
- [ ] Combo strategy shows >90% WR in backtest
- [ ] Max daily drawdown <0.50%

### Phase 2: Advanced P90 — Week 2
**Goal:** Add momentum rebalancing and runner logic for additional edge (extension targets, NOT reversion)
**Target:** +37% weekly R from cascade, 1:5-1:7 R:R on rebalancing

| Priority | Strategy | Agent | Est. Effort |
|----------|----------|-------|-------------|
| 5 | Deep Mean Rebalancing | Optimizer | 4-6 hrs |
| 6 | Over-Extension Runner | Optimizer | 2-3 hrs |
| 7 | P90P Distribution Tracker | Researcher + Optimizer | 6-8 hrs |

**Phase 2 Gate Criteria:**
- [ ] Deep Mean Rebalancing shows >78% WR in backtest
- [ ] Runner protocol adds +15% to daily returns
- [ ] Distribution tracker correctly identifies regime 80%+ of time

### Phase 3: Expert Systems — Week 3-4
**Goal:** Implement session-specific and regime-based strategies
**Target:** Capture edge across all market conditions

| Priority | Strategy | Agent | Est. Effort |
|----------|----------|-------|-------------|
| 8 | Stall-Harvest System | Optimizer | 8-10 hrs |
| 9 | Monday Asian Float | Optimizer | 3-4 hrs |
| 10 | Daily Asian Float | Optimizer | 4-5 hrs |
| 11 | Full-Day Range Regime | Researcher + Optimizer | 5-7 hrs |
| 12 | Dual-Engine Execution | Optimizer | 6-8 hrs |

**Phase 3 Gate Criteria:**
- [ ] Stall-Harvest shows >82% WR across all sessions
- [ ] Asian Float strategies add edge on specific days
- [ ] Dual-Engine shows positive expectancy in backtest

### Phase 4: Meta-Strategies — Week 5+
**Goal:** Validation, optimization, and unified execution framework
**Target:** Robust, self-improving system

| Priority | Strategy | Agent | Est. Effort |
|----------|----------|-------|-------------|
| 13 | Failure Repair Model | PM + Optimizer | 6-8 hrs |
| 14 | Two Plays Framework | Optimizer | 4-6 hrs |
| 15 | Monte Carlo Validation | Researcher | 4-5 hrs |
| 16 | Blind Structural Chain | PM + Optimizer | 8-10 hrs |
| 17 | Fractal Resolution Engine | Researcher + Optimizer | 8-10 hrs |
| 18 | Daily Setups 1-6 | Researcher | 5-7 hrs |
| 19 | Atomic Market Structure | Researcher + Optimizer | 10+ hrs |

**Phase 4 Gate Criteria:**
- [ ] Monte Carlo validation confirms positive expectancy
- [ ] Failure repair model reduces drawdown by >20%
- [ ] Unified framework passes 77+ test threshold

---

## 👥 Agent Task Assignments

### 🔧 Optimizer Agent (Primary Coder)
**Responsibilities:**
- Implement all strategies as Nautilus Trader modules
- Write backtest configurations for each strategy
- Run backtests and collect results
- Optimize parameters based on results

**Current Tasks:**
1. Port existing P90_Base to Nautilus (`quant-lab/strategies/p90_base.py`)
2. Implement P90 Cascade Activation
3. Implement P90 45-Min Add
4. Implement Combo logic

**Code Standards:**
- Each strategy is a separate Python module in `quant-lab/strategies/`
- Each strategy has a corresponding test file in `quant-lab/tests/`
- All parameters from `lab_config.yaml` are configurable
- Log all signals and trades for post-analysis

### 🔬 Researcher Agent (Analysis)
**Responsibilities:**
- Analyze CEREBUS manual for strategy logic extraction
- Document edge cases and filter conditions
- Analyze backtest results and suggest improvements
- Research additional market structure patterns

**Current Tasks:**
1. Extract complete parameter tables from manual (pages 20-131)
2. Document Stall-Harvest execution protocol in detail
3. Analyze Asian Range Float mechanisms
4. Research regime detection algorithms

### 📊 Lab Manager (This Agent)
**Responsibilities:**
- Coordinate between Optimizer and Researcher
- Track strategy implementation progress
- Manage phase gates and quality criteria
- Report to OWL / team-chat

**Current Tasks:**
1. Maintain STRATEGY_TRACKER.md
2. Review backtest results weekly
3. Update LAB_PLAN.md as strategies complete
4. Post progress to team-chat

---

## 📈 Backtest Plan

### Data Requirements
- **Instrument:** EUR/USD
- **Timeframe:** M5
- **Period:** January 2022 – March 2026 (315,000+ candles)
- **Source:** MT5 via Nautilus data adapter

### Backtest Sequence
1. **P90 Base** → Establish baseline (target: 83% WR)
2. **P90 + Cascade** → Validate cascade edge (target: 87.8% WR)
3. **P90 + 45-Min Add** → Validate time-based add (target: 91.2% WR)
4. **P90 Combo** → Validate combined edge (target: 93.4% WR)
5. **Deep Momentum Rebalancing** → Validate momentum continuation to extension target (target: 78-84% WR)
6. **Over-Extension Runner** → Validate runner protocol (target: +15% return)
7. **Stall-Harvest** → Validate unified execution (target: 82-94% WR)
8. **Full Portfolio** → All strategies combined (target: 1.0-1.5% daily)

### Key Metrics to Track
| Metric | How to Measure |
|--------|---------------|
| Win Rate | TP1+TP2 hits / total signals |
| Avg R:R | Avg win size / avg loss size |
| Max Drawdown | Largest peak-to-trough decline |
| Daily Return | Sum of PnL / equity / trading days |
| Sharpe Ratio | Mean return / std of return |
| Recovery Factor | Net profit / max drawdown |
| Weekly R | Sum of R-multiple per week |

---

## 🔑 Key Parameters (Quick Reference)

### Tier System
| Tier | Asian Range | Position Size | Expansion Factor |
|------|-------------|---------------|------------------|
| T1 (Gold) | < 20 pips | 100% | 3.12x |
| T2 (Standard) | 20-30 pips | 75% | 2.68x |
| T3 (Caution) | 30-45 pips | 50% | 2.18x |
| NO-GO | > 45 pips | 0% | 1.52x |

### P90 Candle Thresholds (EST)
| Time Window | Bull/Bear Threshold |
|-------------|---------------------|
| 2:00-4:00 AM | >= 4.1 pips |
| 4:00-6:00 AM | >= 4.6 pips |
| 6:00-8:00 AM | >= 4.6 pips |
| 8:00-10:00 AM | >= 5.9 pips |
| 10:00-11:00 AM | >= 6.2 pips |

### Position Sizing
| Signal | Size | Boundary | Target |
|--------|------|----------|--------|
| Signal 1 (P90 Close) | 40% | 80% of P90 body | -25% Asian Range |
| Signal 2 (P90 Close) | 40% | 1.5x P90 body | -25% Asian Range |
| Signal 3 (45-min add) | 20% | Breakeven | -50% Asian Range |
| Cascade 1 (2nd P90) | 20% | 168% of P90 body | -50% Asian Range |

### Exit Rules
| Condition | Action |
|-----------|--------|
| TP1 (-25% Asian Range) | Close 50%, move SL to breakeven |
| TP2 (-50% Asian Range) | Close remaining core |
| Hard Exit (12:00 PM EST) | Close ALL |
| Kill Switch (132% Asian) | Close ALL immediately |
| Hold Time (120 min) | Close ALL |

### Cascade Rules
| Rule | Value |
|------|-------|
| Max cascades per session | 3 |
| Cascade window | Within 120 min of initial P90 |
| Optimal cascade timing | 45-60 min after initial |
| Cascade boundary | 168% of cascade P90 body |
| 2nd cascade win rate | 87.8% (best) |
| Cascade + Add combo WR | 93.4% |

---

## 📁 Directory Structure

```
quant-lab/
├── config/
│   └── lab_config.yaml          # Lab configuration
├── strategies/
│   ├── p90_base.py              # ✅ Exists (needs Nautilus port)
│   ├── p90_cascade.py           # 📋 Phase 1
│   ├── p90_45min_add.py         # 📋 Phase 1
│   ├── p90_combo.py             # 📋 Phase 1
│   ├── deep_mean_rebal.py       # 📋 Phase 2
│   ├── over_extension_runner.py # 📋 Phase 2
│   ├── p90p_tracker.py          # 📋 Phase 2
│   └── ... (Phase 3-4 strategies)
├── tests/
│   ├── test_p90_base.py
│   ├── test_p90_cascade.py
│   └── ...
├── backtests/
│   └── (Nautilus backtest results)
├── reports/
│   ├── LAB_PLAN.md              # This file
│   ├── STRATEGY_TRACKER.md      # Strategy status
│   └── backtest_results/        # Detailed backtest reports
└── research/
    └── (Research notes, manual extracts)
```

---

## 🚦 Phase Gate Criteria

### Phase 1 → Phase 2
- P90 Base + Cascade + 45-Min + Combo all implemented
- Backtest WR > 85% on combo strategy
- All unit tests passing

### Phase 2 → Phase 3
- Deep Mean Rebalancing shows 1:3+ R:R in backtest
- Runner protocol adds measurable return
- Distribution tracker operational

### Phase 3 → Phase 4
- At least 3 advanced strategies show positive expectancy
- Combined daily return > 0.8% (approaching target)
- Max daily drawdown < 0.50%

### Phase 4 → Live
- All strategies implemented and tested
- Monte Carlo validation confirms edge
- Combined daily return > 1.0% in backtest
- Full 315,000+ candle backtest passes

---

## 📝 Notes

- **Existing code:** P90_Base_Strategy exists at `projects/trading/backtests/` — port to Nautilus first
- **Nautilus path:** `projects/trading/nautilus/`
- **Data:** EUR/USD M5, 315,000+ candles (Jan 2022 – Mar 2026)
- **Critical path:** Cascade + 45-Min Combo (93.4% WR) is the highest-edge setup — prioritize
- **Risk management:** 0.40% daily circuit breaker is NON-NEGOTIABLE
- **Monday/Friday:** Reduce size per manual (Mon -25%, Fri -50% after 10AM)
