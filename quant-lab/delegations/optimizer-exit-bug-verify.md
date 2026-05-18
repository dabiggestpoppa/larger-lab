# [Manager → Optimizer] Task B: Verify Optimizer_v2 Exit Bug

> **From:** Manager v5 | **To:** Optimizer | **Priority:** 2 (MAD Directive 3)
> **Created:** 2026-05-18 00:30 EDT

---

## Objective

MAD Directive 3 asks us to **properly verify** the "all exits labeled SL" claim in optimizer_v2.py. Don't just report "bug found" — prove it with evidence.

---

## Background

The optimizer-2026-05-17.md report claimed:
- **Stall_Harvest_CFD** had 100% WR (88 trades, 0 losses) but ALL 88 exits showed as "sl"
- This was interpreted as a bug where SL/TP were inverted
- **MAD's question:** "If the SL mislabeling bug was real, would EVERY trade win?"

The v4 results show Stall_Harvest_CFD with 30.7% WR (27W/61L) and by_exit: {sl: 61, tp: 27} — which looks correct (more SL hits than TP hits for a 30% WR strategy). This suggests the bug was **fixed in v4**.

But we need to **prove** what was actually wrong in v2.

---

## Investigation Steps

### Step 1: Read the optimizer_v2.py manage_trade function
- File: `projects/trading/nautilus/strategies/optimizer_v2.py`
- Function: `manage_trade()` (around line 157)
- **Question:** Is the exit logic correct? Does `reason: 'sl'` always mean a loss?

### Step 2: Read the optimizer_v2.py Stall_Harvest_CFD function
- Find `run_stall_harvest_cfd()` in optimizer_v2.py
- **Question:** Are SL and TP levels placed correctly relative to entry?
- **Check:** For a mean-reversion trade at 168% stall zone:
  - Entry: at 168% extension (limit order)
  - SL: at 200% extension (further from entry, in the direction of the move)
  - TP: at 0% (reversion back to activation level)
  - **If SL is placed between entry and TP, that's the bug**

### Step 3: Trace 3 specific trades from v2 results
- Load v2 results from `quant-lab/results/optimizer_v2_20260517_060543.json`
- Pick 3 Stall_Harvest_CFD trades (any 3)
- Manually trace: entry price → SL level → TP level → which should hit first
- **Determine:** Was the "SL" actually the TP in disguise?

### Step 4: Compare v2 vs v4 Stall_Harvest implementation
- Read `run_stall_harvest_cfd()` in both optimizer_v2.py and optimizer_v4.py
- **What changed?** Specifically look at:
  - Entry direction
  - SL level calculation
  - TP level calculation
  - manage_trade call parameters

### Step 5: Answer MAD's specific question
**"If the SL mislabeling bug was real, would EVERY trade win?"**
- If SL and TP were swapped, then what was labeled "SL" was actually the profit target
- In that case: every "SL" exit would indeed be a winning trade
- But the PnL per trade would be small (hitting the "SL" = small profit) vs hitting the "TP" = large profit
- **Check:** In v2 results, what's the avg win size for Stall_Harvest? If it's small (~9.9p as reported), that's consistent with SL/TP swap

---

## Output Requirements

Save analysis to: `quant-lab/findings/exit_bug_verification.md`

Include:
1. **manage_trade logic assessment** — Is the exit logic itself correct?
2. **Stall_Harvest SL/TP placement in v2** — Were they swapped?
3. **Trade trace** — 3 specific trades traced manually
4. **v2 vs v4 comparison** — What exactly changed?
5. **Answer to MAD's question** — Would every trade win if SL/TP were swapped?
6. **Conclusion** — Was the bug real? Was it fixed in v4?

---

## Critical Rules (MAD Directive 3)

1. **Don't just report "bug found"** — prove it with evidence
2. **Check if the bug affects ALL trades or just some**
3. **What's the actual P&L impact?** — quantify the damage
4. **Be precise** — trace actual code, don't speculate

---

## Success Criteria

- [ ] manage_trade function logic verified (correct or buggy?)
- [ ] Stall_Harvest v2 SL/TP placement analyzed
- [ ] 3 trades manually traced
- [ ] v2 vs v4 comparison documented
- [ ] MAD's question answered with evidence
- [ ] Conclusion: bug real? fixed? P&L impact quantified?
- [ ] Saved to `quant-lab/findings/exit_bug_verification.md`

---

*Manager v5 — 2026-05-18 00:30 EDT*
