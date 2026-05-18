# MAD Directives — 2026-05-18 00:10 EDT

> **Source:** MAD feedback on Pairs Trading Validation Report
> **Priority:** CRITICAL — Affects all quant lab work going forward

---

## Directive 1: Pairs Trading — Use Real Spread from Data Files + 5% Risk
- **Current bug:** Pairs Trading strategy uses arbitrary $50/z-unit P&L scaling
- **Fix:** Use actual spread values from CSV data files (bid/ask columns if present, or compute from OHLC)
- **Position sizing:** Risk **0.05 (5%)** per position — NOT $50/unit
- **Commission:** $7 per lot (0.07 per 0.01 lot) — apply per leg (×2 for pairs)
- **Spread cost:** Must be computed from actual data, not hardcoded

## Directive 2: Don't Be Pessimistic — Test, Don't Assume
- **Problem:** Validation agent dismissed 151% annual return as "unrealistic" without testing
- **Rule:** It's OK to be skeptical, but **assumptions must be tested every time**
- **"Unrealistic" is not a finding** — it's a hypothesis that needs validation
- **Correct approach:** "This seems high. Let me test it with proper costs and position sizing to see what the real number is."
- **Never dismiss new info just because it differs from expectations**

## Directive 3: Double-Check Bug Claims
- **Question MAD asked:** "If the SL mislabeling bug was real, would EVERY trade win?"
- **Action:** Have the lab properly verify the optimizer_v2 exit reporting bug
- **Don't just report "bug found"** — prove it with evidence
- **Check:** Does the bug affect ALL trades or just some? What's the actual impact on P&L?

## Directive 4: Pass to the Lab Team — They Know Best
- **Don't make recommendations in isolation** — pass notes to Manager/Optimizer/Researcher
- **The lab team should validate or clarify** and update OWL
- **OWL's role:** Route MAD's directives to the right agents, monitor, report back

## Directive 5: Use the Proper Lab Pipeline — Not Random Sub-Agents
- **Problem:** OWL has been spawning one-off sub-agents that just die on timeout
- **Correct approach:** Use the established Manager → Optimizer → Researcher pipeline
- **Manager** decides priorities and assigns work
- **Optimizer** runs backtests and fixes bugs
- **Researcher** digs into anomalies and patterns
- **Don't spawn random agents with a task** — that's not the lab, that's chaos

---

## Action Items for Lab

### A. Pairs Trading Rebuild (Priority — MAD Directive)
1. Read MAD's directives above
2. Rebuild P&L calculation using:
   - Real spread from data files
   - 5% risk per position (0.05)
   - $7/lot commission (×2 legs for pairs)
   - Proper position sizing (not $50/unit)
3. Re-run backtest with corrected parameters
4. Report REAL numbers — don't dismiss them pre-emptively
5. Save to `quant-lab/results/pairs_trading_v2_results.json`
6. Update `quant-lab/reports/PAIRS_TRADING_VALIDATION.md` with corrected results

### B. Verify Optimizer_v2 Exit Bug (MAD Directive 3)
1. Check if the "all exits labeled SL" bug in optimizer_v2 is real
2. If real: does it affect all trades or just some?
3. What's the actual P&L impact?
4. Document findings in `quant-lab/findings/exit_bug_verification.md`

### C. USD/CHF Backtest (Goal 5 — from HEARTBEAT)
1. Backtest top strategies on USD/CHF M5 data
2. Data: `C:\Users\wifik\Downloads\USDCHF!_M5_202301020000_202605061250.csv`
3. Use proper costs: spread from file + $7/lot commission
4. Risk 0.05 per position

### D. Losing Strategies Fix (from HEARTBEAT Priority 4)
1. Fix remaining losing strategies from v4b results
2. Use proper cost model (spread + commission)
3. Risk 0.05 per position

---

## Key Parameters (MAD Authorized)
- **Commission:** $7 per lot (0.07 per 0.01 lot)
- **Risk per position:** 0.05 (5%)
- **Spread:** From data files (real values)
- **Pairs trading:** Apply costs per leg (×2)

---

_Last updated: 2026-05-18 00:10 EDT by OWL per MAD's directives_
