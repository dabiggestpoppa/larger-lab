# [Manager v5] Checkpoint — Pipeline Coordinator

> **Date:** 2026-05-18 00:30 EDT
> **Role:** Pipeline Coordinator (sub-agent of OWL)
> **Purpose:** Full state snapshot for resumption if timeout occurs

---

## What Was Done

### 1. Read All Critical Files
- ✅ `MANAGER.md` — Operating instructions
- ✅ `GOALS.md` — 6 goals, priority order
- ✅ `STATUS.md` — Current state of all strategies
- ✅ `MAD_DIRECTIVES_20260518.md` — 5 MAD directives
- ✅ `PROTOCOL.md` — Communication protocol
- ✅ `unified_results.json` — 4 new strategies (all losing)
- ✅ `CEREBUS_STRATEGY_ANALYSIS.md` — Strategy implementation reference
- ✅ `PAIRS_TRADING_VALIDATION.md` — Validation report
- ✅ `optimizer_v4_final_20260517.json` — V4 final results (10/10 profitable)
- ✅ `optimizer-2026-05-17.md` — Optimizer insights (v2 analysis)

### 2. Assessed Current State

**V4 R6 (EUR/USD M5, no costs):** 10/10 strategies profitable
- Deep_Mean_Reversion: 91.8% WR, PF 111.96 — FLAGSHIP
- All others: PF 1.02-1.85, positive expectancy

**Unified Results (new strategies):** 0/4 profitable despite >50% WR
- p90_alpha_combo: 51.2% WR, -$300, PF 0.73
- hmm_regime: 55.9% WR, -$57
- multi_tf: 55.5% WR, -$290
- sentiment_enhanced: 48.0% WR, -$200

**Pairs Trading:** +$206K PnL is artifact (no costs, arbitrary $50/z-unit)
- Data is GOOD (real GBP/USD, 0.755 avg correlation)
- Needs rebuild with proper cost model

### 3. Made Decisions

**GO:** All 10 V4 strategies (pending cost validation)
**HOLD → Rebuild:** Pairs Trading (MAD Directive)
**NO-GO:** 4 new strategies from unified_results (need rebuild)

### 4. Priority Queue Established
1. Task A: Pairs Trading Rebuild (MAD Directive 1)
2. Task B: Verify Optimizer_v2 Exit Bug (MAD Directive 3)
3. Task C: USD/CHF Backtest (Goal 5)
4. Cost model validation for V4 strategies
5. Fix losing new strategies
6. Goal 3: Max Drawdown < 12%
7. Goal 6: Basket portfolio

### 5. Files Created

| File | Purpose |
|------|---------|
| `quant-lab/decisions/manager-2026-05-18.md` | Main decision document |
| `quant-lab/delegations/optimizer-pairs-rebuild.md` | Task A: Pairs rebuild |
| `quant-lab/delegations/optimizer-exit-bug-verify.md` | Task B: Exit bug verify |
| `quant-lab/delegations/optimizer-usdchf.md` | Task C: USD/CHF backtest |
| `quant-lab/checkpoints/manager-v5-checkpoint.md` | This file |

---

## What Needs to Happen Next

### Immediate (Optimizer Tasks)
1. **Task A:** Optimizer reads `optimizer-pairs-rebuild.md` and executes
2. **Task B:** Optimizer reads `optimizer-exit-bug-verify.md` and executes (can parallelize with A)
3. **Task C:** After A+B complete, Optimizer reads `optimizer-usdchf.md` and executes

### After Optimizer Completes Tasks A-C
4. Re-run all 10 V4 strategies with proper cost model
5. Assess if Goal 2 (80% profitable) still holds with costs
6. Fix the 4 losing new strategies
7. If strategies still profitable with costs → escalate to MAD for Goal 2 achievement

### Pending Items Not Yet Delegated
- Cost model validation for V4 strategies
- Fix losing unified strategies
- Goal 3: Max Drawdown optimization
- Goal 4: Increase Deep_Mean_Reversion frequency to 2/day
- Goal 6: Basket portfolio

---

## Key Data Files Reference

| File | Path | Size |
|------|------|------|
| EUR/USD M5 | `C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv` | 15MB |
| GBP/USD M5 | `C:\Users\wifik\Downloads\GBPUSD!_M5_202301020000_202605061250.csv` | 15MB |
| USD/CHF M5 | `C:\Users\wifik\Downloads\USDCHF!_M5_202301020000_202605061250.csv` | 15MB |
| CHF/JPY M1 | `C:\Users\wifik\Downloads\CHFJPY!_M1_202301020000_202605061250.csv` | ~75MB |
| EUR/USD Tick | `C:\Users\wifik\Downloads\EURUSD.PRO_202407010000_202605132122.csv` | 3.3GB |

**All M5 CSV files have:** `<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>` columns
**EUR/USD Tick CSV has:** `<DATE> <TIME> <BID> <ASK> <LAST> <VOLUME> <FLAGS>` columns

---

## Cost Model Parameters (MAD Authorized)

- **Commission:** $7/lot (0.07 per 0.01 lot)
- **Risk per position:** 0.05 (5%) of equity
- **Spread:** From CSV SPREAD column (real values)
- **Pairs trading:** Costs per leg (×2)

---

## Strategy Files Reference

| File | Purpose |
|------|---------|
| `projects/trading/nautilus/strategies/optimizer_v4.py` | V4 strategies (10 strategies, all profitable) |
| `projects/trading/nautilus/strategies/optimizer_v2.py` | V2 strategies (baseline, has bugs) |
| `projects/trading/nautilus/strategies/pairs_trading_eurusd_gbpusd.py` | Pairs trading (needs rebuild) |
| `quant-lab/research/CEREBUS_STRATEGY_ANALYSIS.md` | Manual strategy reference |

---

## Critical Context for Resumption

### What MAD Cares About
1. **Pairs Trading Rebuild** — MAD explicitly ordered this
2. **Don't dismiss results** — test, don't assume
3. **Proper bug verification** — prove with evidence
4. **Use the pipeline** — Manager → Optimizer → Researcher
5. **Stay skeptical** — 10/10 profitable with no costs needs validation

### What the Optimizer Needs to Know
- All CSV files have SPREAD column → use it
- Use 5% risk per position, not $50/unit
- Commission $7/lot per leg
- Don't change strategy logic, only cost model
- Report REAL numbers, even if they're worse

---

*Manager v5 Checkpoint — 2026-05-18 00:30 EDT*
*OWL can resume by reading this file and delegating Tasks A, B, C to the Optimizer*
