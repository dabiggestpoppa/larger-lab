# 🦉 OWL Command Center — Task Board

> **Last Updated:** 2026-05-17 02:57 EDT
> **Active Sub-Agents:** 0 (max 5)
> **Current Phase:** Phase 0 ✅ → Phase 1 (P90 Base Port) next

---

## 🔴 ACTIVE TASKS

### T1: P90 Base Engine — Nautilus Port
- **Status:** PENDING
- **Priority:** HIGHEST
- **Agent:** `quant-developer`
- **Description:** Port the core P90 momentum expansion engine from PineScript/manual to Nautilus Trader
- **Requirements:**
  - Asian Range calculation (7PM-3AM EST)
  - P90 candle detection with time-window thresholds
  - Signal 1 + Signal 2 simultaneous entry at P90 close
  - Position sizing: 40% + 40% of equity
  - SL: 80% body (Sig1), 1.5x body (Sig2)
  - TP: -25% Asian Range
  - Extension targets: -25% and -50% of Asian range
  - Hard exit: 12PM EST
  - Kill switch: 132% Asian range violation
  - Daily drawdown protection: 0.40%
- **Source files:**
  - `quant-lab/reports/PART_1___Core_Manual.txt` (primary)
  - `quant-lab/strategies/CEREBUS_V5_LIVE_PERFECT_FORM.pine` (reference)
  - `quant-lab/reports/P90_STRATEGY_GUIDE.md` (implementation notes)
- **Output:** `quant-lab/strategies/nautilus/p90_base.py` + tests
- **Acceptance criteria:** Backtest matches manual's expected 85-90% WR on filtered setups

### T2: Cascade System — Nautilus Port
- **Status:** BLOCKED (depends on T1)
- **Priority:** HIGH
- **Agent:** `quant-developer`
- **Description:** Port cascade activation logic
- **Requirements:**
  - Same-direction P90 detection within 120 min of initial
  - Max 3 cascades per session
  - Optimal timing window: 45-60 min
  - Cascade boundary: 168% of THIS P90 body
  - Cascade sizing: 20% (Cascade 1), 10% (Cascade 2)
  - Combined + 45-Min Add sizing logic
  - Opposite direction P90 = IGNORE (unless 200% + 132% both triggered)
- **Source files:** `quant-lab/reports/PART_2___Cascade_Activation_Analysis.txt`, `PART_3___Cascade_Methodology.txt`
- **Output:** `quant-lab/strategies/nautilus/p90_cascade.py` + tests

### T3: 45-Min Add Logic
- **Status:** BLOCKED (depends on T1)
- **Priority:** HIGH
- **Agent:** `quant-developer`
- **Description:** Port 45-minute add-on logic
- **Requirements:**
  - Trigger: +45 min from initial P90 AND resolution output >= +8 pips
  - Size: 30%, SL: Breakeven, TP: -50% Asian
  - Complementary to cascade (combined WR: 93.4%)
- **Source files:** `quant-lab/reports/PART_2___Cascade_Activation_Analysis.txt`
- **Output:** `quant-lab/strategies/nautilus/p90_add.py` + tests

### T4: P90P Distribution Tracker
- **Status:** BLOCKED (depends on T1)
- **Priority:** MEDIUM
- **Agent:** `quant-developer`
- **Description:** Port the distribution tracker with 3 checkpoints
- **Requirements:**
  - Weighted formula: Tier(40%) + Regime(25%) + P90(20%) + Cascade(10%) + TimeDecay(5%)
  - 3 checkpoints: 2AM, 6AM, 9AM
  - Tier factors: T1=3.12x, T2=2.68x, T3=2.18x
  - Regime ratio = Daily(3-9AM) / Asian Range
  - Accuracy targeting: 94-95% when all conditions met
- **Source files:** `quant-lab/reports/PART_5___P90P_Distribution_Tracker.txt`
- **Output:** `quant-lab/strategies/nautilus/p90p_tracker.py` + tests

### T5: Atomic Market Structure
- **Status:** BLOCKED (depends on T1-T4)
- **Priority:** LOW (separate system)
- **Agent:** `quant-developer`
- **Description:** Port Atomic Structure system (Density Zone, Phi scoring)
- **Requirements:**
  - Density Zone = Atomic Unit + Tier Threshold overlap
  - Phi = 0.40×Regime + 0.25×P90 + 0.20×Cascade + 0.15×Float
  - Fixed Dollar Expectancy sizing
  - 7-state execution protocol
- **Source files:** `quant-lab/reports/ATOMIC_STRUCTURE.txt`
- **Output:** `quant-lab/strategies/nautilus/atomic_structure.py` + tests

### T6: Full System Integration + End-to-End Backtest
- **Status:** BLOCKED (depends on T1-T5)
- **Priority:** LOW
- **Agent:** `quant-optimizer`
- **Description:** Integrate all modules and run full backtest
- **Requirements:**
  - All 5 modules working together
  - 249K bar backtest (Jan 2023 - May 2026)
  - Target: 85-90% WR, PF > 1.5, DD < 0.50%
  - Monte Carlo validation (10K iterations)
- **Output:** `quant-lab/backtests/full_system_results.json` + report

---

## ✅ COMPLETED TASKS

### ✅ Manual Processing (Phase 0)
- Extracted 194-page PDF into structured files
- Saved PineScript V5 source
- Created P90_STRATEGY_GUIDE.md
- Created STRATEGY_GAP_ANALYSIS.md
- Fixed cascade backtest (3 bugs), ran 249K bar backtest
- Identified key sizing discrepancy (manual vs PineScript)

---

## 📋 TASK TEMPLATE

When spawning a sub-agent, create a task file at:
`quant-lab/command-center/tasks/{agent}-{YYYYMMDD-HHmmss}.md`

```markdown
# Task: {TITLE}
- **Agent:** {LABEL}
- **Spawned:** {TIMESTAMP}
- **Session:** {SESSION_ID}
- **Priority:** {LEVEL}

## Objective
{WHAT}

## Requirements
- {REQ1}
- {REQ2}

## Source Files
- {FILE1}
- {FILE2}

## Output
- {OUTPUT_FILE}

## Acceptance Criteria
- {CRITERIA}
```
