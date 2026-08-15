# P7.5 Validation Label Audit

**Date:** 2026-08-15 · **Base:** db9f8c62

## Renaming

The segment `2025-07-01 .. 2026-06-01` (previously labelled "untouched" in Phase 7
artifacts) is renamed to **`RELATIONSHIP_CONFIRMED_OOS`** in all Phase 7.5 artifacts.

## Status

- It is **untouched with respect to Phase-7 execution-parameter selection**:
  entry delay, holding period and pair were chosen from `inner_sel` /
  `inner_val` only.
- It is **NOT untouched with respect to relationship discovery/promotion**:
  Phase 6 used this segment as its holdout to validate relationship families
  (candidate freeze + holdout labels). The families themselves were therefore
  selected/promoted with this data.

## Consequence

- We do **not** claim final independent holdout validation for Phase 7.5.
- The first true post-discovery out-of-sample period is anything from
  `2026-06-01` onward — reported separately (FORWARD_OOS) when data exists.
- All Phase 7.5 statements that quote `RELATIONSHIP_CONFIRMED_OOS` numbers must carry this
  caveat.

## Affected Phase 7 artifacts (renamed in copies under artifacts/phase_07_5/)

- `P7_EUR_JPY_BASELINE_RESULTS.csv` → `split` column renamed
- `P7_JPY_CHF_BASELINE_RESULTS.csv` → `split` column renamed
- `P7_ENTRY_DELAY_SURFACE.csv` → `split` column renamed
- `P7_PAIR_SPACE_COMPARISON.csv` → `split` column renamed
- `PHASE_7_DECISION.json` → `validation` keys relabelled
