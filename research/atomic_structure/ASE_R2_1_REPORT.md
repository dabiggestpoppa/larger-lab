# ASE-2.1 — Path Reconstruction + Predictive Baseline Repair

## Trader review

1. **Post-noon variance:** measured from raw M5 close-to-close log returns in `ASE_VARIANCE_CLOCK.csv`; each day is partitioned into Asia, London, overlap, and afternoon segments.
2. **Morning high/low breaks:** raw path reconstruction finds 351/442 days with at least one post-noon touch of a prior morning extreme. T1/T2/T3 breakdowns are in `ASE_NOON_EXTREME_HOLD.csv`; touch and close are separate.
3. **Predictors:** causal morning-range/ATR buckets are in `ASE_NOON_ATR_CONDITIONING.csv`. No claim of monotonicity is made without a proper out-of-sample lock-ratio score.
4. **R_LOCK:** the raw path and prior-day ATR series are reconstructed; expected afternoon excursion remains conservatively marked as requiring a fuller cross-fitted model rather than using future outcomes.
5. **-25 lock:** 433 first chronological -25 events were reconstructed from raw M5 paths. Opposite-band touch and close-beyond outcomes are in `ASE_POST25_REVERSAL_MATRIX.csv`.
6. **Post-25 state change:** event ledgers preserve the exact hit path and first-event ordering. The state-transition artifact is explicitly marked as path-reconstructed but not promoted as a completed windowed inference because that comparison requires additional preregistered feature extraction.
7. **Remaining-range prediction:** chronological walk-forward rows contain 1,764 checkpoint/date scores with prior-date-only training and a minimum-cell fallback policy. These are the correct predictive artifacts, replacing the prior in-sample-only summaries.
8. **Transition prediction:** the inherited count tables remain descriptive; a richer walk-forward probability score is not promoted as successful merely because counts exist.
9. **ML:** not authorized. ASE-2.1 remains `PARTIAL_TRANSITION_STRUCTURE`; path reconstruction is complete, but the predictive transition score and full lock-ratio cross-fit are not claimed as complete merely from descriptive outputs.

## Technical

- Branch: `agent/atomic-structure-foundry`
- Base checkpoint: `9dccc72c63f8272af384b1356aae0f3b8394398e`
- Dataset: EURUSDPRO M5, SHA256 `46e81261f5799fdebb4a2d2aed045c91ad5f2bbe3324c0275cb3cc322f18b13b`
- Development: 2023-01-03 through 2024-12-31
- Reconstructed sessions: 442
- Noon path rows: 442
- First -25 path rows: 433
- Walk-forward rows: 1,764
- ATR: ATR20 and ATR14 use prior completed daily ranges only; current day excluded
- Event calendar: unavailable locally
- Causality: raw path uses completed M5 bars and development-only partition; no 2025/2026 outcomes consumed

## Guardrails

`strategy_pnl_computed=false`, `optimization_performed=false`, `confirmation_consumed=false`, `holdout_consumed=false`, `ASE3_authorized=false`.
