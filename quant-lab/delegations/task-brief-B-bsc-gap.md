# Task Brief B — Blind_Structural_Chain Gap Analysis

> **Created:** 2026-05-18 08:00 EDT
> **Author:** Quant Lab Manager (SAGE-Directed)
> **Priority:** CRITICAL — Phase 0 Gate
> **Owner:** Researcher

---

## Objective

Investigate and explain the 64-percentage-point gap between predicted (93.7%) and actual (29.7%) performance in the Blind_Structural_Chain strategy. This is the #1 research priority in the Quant Lab.

## The Problem

Blind_Structural_Chain has a massive performance gap:
- **Predicted Win Rate:** 93.7% (from the strategy's internal logic/model)
- **Actual Win Rate:** 29.7% (from backtest results)
- **Gap:** 64 percentage points

This is not a minor calibration issue. Something is fundamentally broken between what the strategy THINKS it will do and what it ACTUALLY does.

## Key Questions to Answer

### 1. Logic-Implementation Gap
- Does the Python implementation (`quant-lab/conversions/strategy-code/blind_structural_chain.py`) correctly implement the intended strategy logic?
- Are there any bugs in the entry/exit conditions?
- Are the structural chain calculations correct?

### 2. Prediction Methodology
- How was the 93.7% predicted WR calculated?
- Is the prediction based on in-sample data (overfitting)?
- Is the prediction model using future data (look-ahead bias)?

### 3. Market Regime Sensitivity
- Does the strategy work in specific market conditions but fail in others?
- What market regimes were present in the backtest period?
- Is the 93.7% prediction from a specific regime that doesn't generalize?

### 4. Position Sizing Interaction
- The strategy has very high MaxDD (-963.8p / 9.64%) — does the position sizing interact badly with the structural chain logic?
- Are losses concentrated in specific trade sequences?

### 5. Data Quality
- Is the backtest using the same data the prediction was based on?
- Any gaps, bad ticks, or data issues?

## Files to Analyze

| File | Purpose |
|------|---------|
| `quant-lab/conversions/strategy-code/blind_structural_chain.py` | Strategy implementation |
| `quant-lab/results/` | Backtest results (find the v4 results for BSC) |
| `srrs_opc/` | SRRA-OPH core modules (BSC may use components from here) |
| Any optimizer output files referencing BSC | Performance data |

## Research Methodology

1. **Code Review:** Read the full BSC implementation. Trace the logic flow. Identify any discrepancies between the structural chain concept and the code.

2. **Prediction Audit:** Find where the 93.7% prediction comes from. Trace the calculation. Check for look-ahead bias, overfitting, or methodological errors.

3. **Trade-Level Analysis:** If possible, examine individual trade outcomes. Look for patterns in losing trades. Are losses random or systematic?

4. **Regime Analysis:** Segment backtest results by market regime (trending, ranging, volatile, calm). See if the strategy works in any specific regime.

5. **Comparison:** Compare BSC's actual performance profile to other strategies that use similar structural analysis. What's different?

## Expected Output

Save results to: `quant-lab/research/bsc-gap-analysis-2026-05-18.md`

Format:
```
1. Executive Summary (what's broken, in 3 sentences)
2. Root Cause Analysis (detailed findings)
3. Prediction vs Reality (where the 93.7% came from)
4. Code Issues Found (if any)
5. Market Regime Findings (if any)
6. Recommendations:
   a. Fixable? If so, how?
   b. Not fixable? If so, what to do instead
7. Estimated effort to fix (if fixable)
```

## Success Criteria

- Identify the PRIMARY root cause of the 64pp gap
- Determine if the strategy is fixable or fundamentally flawed
- If fixable: provide specific code/logic changes needed
- If not fixable: recommend whether to abandon or repurpose the approach

## Estimated Effort

- Code review: 1-2 hours
- Prediction audit: 1-2 hours
- Trade-level analysis: 1-2 hours
- Regime analysis: 1 hour
- Write-up: 1 hour

**Total: 5-8 hours**

## Dependencies

- None. This is independent of Task Brief A.
- Should be done in PARALLEL with Task Brief A.

## Why This Matters

BSC is the strategy with the largest prediction-reality gap in the entire lab. If we can understand WHY it fails, we likely learn something important about structural analysis in general — knowledge that applies to other strategies and to the SRRA system.

---

*Task Brief B — Blind_Structural_Chain Gap Analysis — Manager 2026-05-18 08:00 EDT*
