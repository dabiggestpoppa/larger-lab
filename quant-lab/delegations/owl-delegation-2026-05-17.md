# 🦉 OWL Delegation Order — 2026-05-17 17:18

> **From:** OWL (OC2) Sovereign Operator
> **To:** Manager (Quant Lab)
> **Priority:** CRITICAL
> **Type:** Bug Fix Sprint — 5 Strategies

---

## Directive

MAD has directed that all Lab bug fixes be delegated through the Manager → Optimizer pipeline. You are the Manager. Execute the priority queue below.

## Your Authority

You have full authority to:
- Assign work to Optimizer and Researcher
- Deploy Poly-Agent (max 2 concurrent) if Optimizer gets stuck
- Make go/no-go calls on fixed strategies
- Re-prioritize within this task set

## Priority Queue (Execute In Order)

### Task 1: Fix Stall_Harvest SL/TP Inversion (30 min target)
- **Strategy:** Stall_Harvest_CFD
- **Bug:** SL placed on profit side — all 88 exits show as "SL" but with positive PnL
- **Fix:** Swap SL/TP directions in the strategy code
- **Expected:** ~86% WR (per manual) with positive expectancy
- **File:** `projects/trading/nautilus/strategies/stall_harvest_cfd.py` (or similar)
- **Success Criteria:** After fix, SL exits should be losses, TP exits should be profits, overall PnL positive

### Task 2: Fix Constraint_Anchor Partial Exits (1 hr target)
- **Strategy:** Constraint_Anchor
- **Bug:** SL at opposite Asian extreme is too wide (407 SL hits vs 199 TP hits)
- **Fix:** Implement TP1 (25% extension, close 50%) + TP2 (50% extension, close 50%). At TP1, move all boundaries to BE+2p
- **Expected:** WR improves from 32.9% to ~60%+
- **Success Criteria:** WR > 50%, PF > 1.0

### Task 3: Fix Dual_Engine SL Tightening (1 hr target)
- **Strategy:** Dual_Engine
- **Bug:** SL at opposite Asian extreme gives terrible R:R (65.9% WR but -1.10 expectancy)
- **Fix:** Change SL from opposite Asian extreme to 80% body boundary
- **Expected:** Avg loss reduces from -21.6p to ~-5p, expectancy turns positive
- **Success Criteria:** Positive expectancy, PF > 1.0

### Task 4: Debug Two_Plays Entry Condition (2 hr target)
- **Strategy:** Two_Plays
- **Bug:** Entry filter not working — 35% WR vs manual's 85-90% prediction
- **Fix:** Debug the close-outside-band entry filter. Check if the band calculation is correct
- **Expected:** WR should approach 85-90% per manual
- **Success Criteria:** WR > 70%, PF > 1.0

### Task 5: Tune Blind_Structural_Chain Thresholds (2 hr target)
- **Strategy:** Blind_Structural_Chain
- **Bug:** Entry too loose — 29.7% WR vs manual's 93.7% prediction
- **Fix:** Increase impulse threshold by +2-3p. Tighten entry conditions
- **Expected:** WR should improve significantly toward manual prediction
- **Success Criteria:** WR > 60%, PF > 1.0

### Task 6: Redesign P90P_Distribution as Target Module (3 hr target)
- **Strategy:** P90P_Distribution
- **Bug:** Targets too ambitious (2.18-3.12x AR) — only 12 TP hits out of 255 trades
- **Fix:** Don't use as standalone. Redesign as a dynamic TP calculation module for all other strategies
- **Expected:** Module that calculates weighted expansion targets for other strategies
- **Success Criteria:** Working module integrated into at least 2 other strategies

## Reporting Requirements

After each task:
1. Update `quant-lab/STATUS.md` with new results
2. Write decision to `quant-lab/decisions/manager-YYYY-MM-DD.md`
3. If a strategy meets MAD notification criteria (WR > 50%, PF > 1.3, expectancy > 0, sample > 200), escalate to OWL immediately
4. If stuck >30 min on any task, write BLOCKED.md and escalate to OWL

## Go/No-Go Criteria (Per Strategy)

| Criterion | Threshold |
|-----------|-----------|
| Win Rate | ≥ 50% (or within 10% of manual prediction) |
| Profit Factor | > 1.0 |
| Expectancy | > 0 |
| Max Drawdown | ≤ 12% |
| Sample Size | ≥ 100 trades |
| No Critical Bugs | — |

## Data & Code Locations

- **Strategy code:** `projects/trading/nautilus/strategies/`
- **Optimizer v2:** `projects/trading/nautilus/strategies/optimizer_v2.py`
- **EUR/USD M5 data:** `EURUSD!_M5_202301020000_202605061250.csv`
- **Results:** `quant-lab/results/`
- **Status:** `quant-lab/STATUS.md`
- **Goals:** `quant-lab/GOALS.md`

## End State

When all 6 tasks are complete:
- All 5 broken strategies should be profitable (or documented as NO-GO with reasons)
- P90P_Distribution redesigned as a module
- Overall profitable strategy rate should be 80%+ (Goal 2)
- Ready for Goal 5 (USD/CHF backtest) and Goal 6 (Basket portfolio)

---

**Execute. Report progress. Escalate blockers.**
