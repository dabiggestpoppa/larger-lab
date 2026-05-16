# CEREBUS FX Manual — Strategy Reconstruction Plan

> **Goal:** Reproduce ALL P90 strategies from the CEREBUS FX v4.0 manual as individual, backtestable Nautilus strategies.
> **Target:** Match or exceed stated win rates (85-90%) and daily returns (1.0-1.5%).
> **Approach:** Each strategy is a separate, distilled module — not one monolithic strategy.

---

## Manual-Stated Performance Targets

| Metric | Target |
|--------|--------|
| Win Rate (Filtered) | 85% – 90% |
| Daily Goal | 1.0% – 1.5% |
| Max Daily Drawdown | < 0.50% |
| Prop Firm Circuit Breaker | 0.40% loss |
| Risk Per Activation | 0.12% of Equity |
| Max Concurrent Risk | 0.36% (3 signals) |

---

## Strategy Inventory (from Manual)

### CORE P90 STRATEGIES

| # | Strategy | Page | Status | Key Logic |
|---|----------|------|--------|-----------|
| 1 | **P90 Base (CFD Expansion Engine)** | 5-6 | ✅ Converted | P90 candle → 3-position pyramid → -25%/-50% targets |
| 2 | **P90 Cascade Activation** | 10-13 | 📋 Planned | 2nd/3rd P90 in same direction, 168% boundary |
| 3 | **P90 45-Min Add** | 12-13 | 📋 Planned | Time-based add after 45min + 8p extension |
| 4 | **P90 Cascade + 45-Min Combo** | 13 | 📋 Planned | Both triggers = 93.4% win rate |
| 5 | **Deep Mean Rebalancing** | 6-7 | 📋 Planned | 168%/200% stall zone → limit order reversion |
| 6 | **Over-Extension Runner** | 7-8 | 📋 Planned | Hold runner to daily -50% after -50% hit |
| 7 | **P90P Distribution Tracker** | 30+ | 📋 Planned | 2AM/6AM/9AM checkpoints, regime detection |

### ADVANCED STRATEGIES

| # | Strategy | Page | Status | Key Logic |
|---|----------|------|--------|-----------|
| 8 | **Stall-Harvest System** | 20+ | 📋 Planned | Resolution output stall → harvest |
| 9 | **Monday Asian Float** | 38+ | 📋 Planned | Monday-specific Asian range behavior |
| 10 | **Daily Asian Float** | 43+ | 📋 Planned | Daily Asian range float mechanism |
| 11 | **Full-Day Range Regime** | 51+ | 📋 Planned | Regime-based daily range tracking |
| 12 | **Dual-Engine Execution** | 58+ | 📋 Planned | CFD + Binary/Mean Reversion engines |
| 13 | **Failure Repair Model** | 78+ | 📋 Planned | Failure sequence analysis |
| 14 | **Two Plays Framework** | 79+ | 📋 Planned | Final execution framework |
| 15 | **Monte Carlo Validation** | 35+ | 📋 Planned | Triple-engine Monte Carlo |
| 16 | **Blind Structural Chain** | 90+ | 📋 Planned | Recursive loop engine |
| 17 | **Fractal Resolution Engine** | 100+ | 📋 Planned | Nested cycle analysis |
| 18 | **Setups 1-6** | 109+ | 📋 Planned | Daily setup ideas |
| 19 | **Atomic Market Structure** | 131+ | 📋 Planned | Density zone, unified equation |

---

## Current Backtest Results (Autopilot v3, Iteration 24)

| Strategy | Trades | PnL | Return % |
|----------|--------|-----|----------|
| P90_Base_Strategy | 147 | 11.01 | 0.11% |
| RSI_Reversion | 349 | 32.84 | 0.33% |
| Asian_Breakout | 1270 | 6.24 | 0.06% |

**Gap to target:** Need 1.0-1.5% daily return. Currently at 0.33% best.
**Key insight:** The P90_Base is profitable but needs cascade + add logic to reach target.

---

## Implementation Priority

### Phase 1: Core P90 (This Week)
1. ✅ P90 Base Strategy (done)
2. 📋 P90 Cascade Activation
3. 📋 P90 45-Min Add
4. 📋 P90 Cascade + 45-Min Combo

### Phase 2: Advanced P90 (Week 2)
5. 📋 Deep Mean Rebalancing
6. 📋 Over-Extension Runner
7. 📋 P90P Distribution Tracker (full)

### Phase 3: Expert Systems (Week 3-4)
8. 📋 Stall-Harvest System
9. 📋 Monday/Daily Asian Float
10. 📋 Full-Day Range Regime
11. 📋 Dual-Engine Execution

### Phase 4: Meta-Strategies (Week 5+)
12. 📋 Failure Repair Model
13. 📋 Two Plays Framework
14. 📋 Monte Carlo Validation
15. 📋 Fractal Resolution Engine

---

## Key Parameters (from Manual)

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

### Deep Mean Rebalancing
| Parameter | Value |
|-----------|-------|
| Trigger | 168% or 200% extension touched |
| Limit order | At 200% level |
| Stop | 8 pips beyond 200% (~220%) |
| TP1 | Return to 0% (activation level) |
| TP2 | -50% daily range |
| R:R potential | 1:5 to 1:7 |
| Win rate (2-6 AM) | ~84% |
| Win rate (6-9 AM) | ~78% |
| Win rate (9-12 PM) | ~74% |
