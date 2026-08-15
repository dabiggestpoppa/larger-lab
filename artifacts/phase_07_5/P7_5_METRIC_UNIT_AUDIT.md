# P7.5 Metric / Unit Audit

**Base:** db9f8c62 · **Date:** 2026-08-15

## Problem

Phase 7 baselines reported Calmar values in the hundreds-to-thousands and
annualized return in bps while drawdown was a unitless ratio, mixing units.
A second defect: drawdown ratio divided by the running peak, which is near
zero early in the curve and yields meaningless ratios > 1 (e.g. 2.8 on a
+9.9 bps peak).

## Repair (used by all P7.5 simulations)

| Field | Unit |
|---|---|
| per-trade PnL | bps of notional per vol-normalized position |
| equity / cumulative return | bps |
| peak equity | bps |
| drawdown | bps: peak − equity |
| max drawdown ratio | unitless: (peak_eq_base − eq_base)/peak_eq_base against a fixed capital base of 10000 bps → always in [0, 1) |
| annualized return | decimal: mean_pnl_bps / 10000 × trades_per_year |
| Calmar | annualized_return_decimal / max_drawdown_ratio (unitless) |

## Tests added

- `test_drawdown_units_consistent` — drawdown_bps equals peak−equity (bps),
  drawdown_ratio equals drawdown_bps/peak (unitless); ratio in [0,1].
- `test_calmar_unit_mismatch_detected` — Calmar computed from bps vs decimal
  must differ by exactly the /10000 factor.
- `test_equity_chronological` — equity built from unsorted input must equal
  equity built from chronologically sorted input.
