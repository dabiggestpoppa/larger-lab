# ASE-1 Empirical Atomic Terrain Seal

> ASE-1.1 repair: the original raw all-days k=3 result is preserved as a control. The Generation-A gated reproduction is recorded in `ASE_R1_1_REPORT.md` and must be used for contract review.

## Trader-language result

- **Tiers:** the repaired Generation-A gated centroids are 13.714 pips, 22.550 pips, and 34.627 pips; source operational bins remain T1 <20, T2 20-<30, T3 30-<=45, with AR_NO_GO above 45. The prior 218.4p singleton remains preserved only as the raw all-days control.
- **Stability:** chronological subperiod rediscovery and frozen-centroid transport are in `02_terrain/ASE_TIER_STABILITY.csv` and `ASE_TIER_TRANSPORT.csv`; no 2025/2026 outcomes were used.
- **AU normalization:** `ASE_AU_NORMALIZATION.csv` compares raw pips with AU units using CV, IQR/median, MAD/median and Wasserstein distances.
- **1 AU completion:** first-hit probability of either side by tier is {"1": 0.9870689655172412, "2": 0.9856115107913668, "3": 1.0}; this is first-hit terrain, not a strategy result.
- **Failure anatomy:** 77.8% of loop rows fail before 1 AU; the dominant taxonomy is `ORIGIN_BREACH`. Conditional next-event anatomy is in `ASE_LOOP_FAILURE_ANATOMY.csv`.
- **Loops:** 11252 descriptive loop events across 442 valid research days; median 26.0 loops/day (IQR 21.0-30.0); see the parquet ledger.
- **03:00 states:** later 06:00 completion medians by state are {"AR_NO_GO_STATE": 0.6869082959004227, "BALANCED_ASIA": 0.35628671783761245, "FULL_LOOP": 0.5454226119363668, "ONE_SIDED_DOWN": 0.37471776589423433, "ONE_SIDED_UP": 0.3567493540854585, "OVER_COMPLETED": 0.5780089153045879, "PARTIAL_LOOP": 0.46174496644294066}; see `ASE_3AM_STATE_PATHS.csv`.
- **Delivered final range:** 06:00 median 0.442, 09:00 median 0.627, 12:00 median 0.851.
- **Uncertainty:** time-only remaining-range summaries are {"03AM": {"iqr": 33.15000000000123, "median_remaining_pips": 42.80000000000173, "variance": 783.8856881001564}, "06AM": {"iqr": 30.27500000000238, "median_remaining_pips": 34.79999999999927, "variance": 726.0523990602132}, "09AM": {"iqr": 28.274999999999824, "median_remaining_pips": 21.59999999999939, "variance": 637.453609928133}, "12PM": {"iqr": 19.3500000000002, "median_remaining_pips": 8.549999999999386, "variance": 264.4441815790023}}; dispersion contracts across checkpoints, while all final-range fields remain retrospective denominators only.
- **ASE-2:** the repaired lane is `CONTRACT_REPRODUCED_WITH_DATA_DRIFT`; ASE-2 is not authorized here.

## Technical record

- Branch: `agent/atomic-structure-foundry`
- Source: `EURUSDPRO_M5_2023_2025.csv`; SHA256 `46e81261f5799fdebb4a2d2aed045c91ad5f2bbe3324c0275cb3cc322f18b13b`
- Timeframe: M5; timezone normalization: `America/New_York` with DST; valid development interval: `2023-01-03 through 2024-12-31`
- Valid days: 442; loops: 11252
- Tests: 23 unit/contract tests passed; empirical contract checks are recorded in `ASE_TEST_AUDIT.json`.
- Causality: PASS; future perturbation, tail truncation, head truncation and prefix consistency are recorded in `ASE_CAUSALITY_AUDIT.json`.
- Evidence matrix: {"SCALE": "PASS", "NORMALIZATION": "PASS", "STATE": "PASS", "TIME": "PASS", "CAUSALITY": "PASS"}

## Guardrails

- `strategy_pnl_computed = false`
- `optimization_performed = false`
- `confirmation_consumed = false`
- `holdout_consumed = false`
- `ASE2_authorized = false`

The 2025 confirmation interval and 2026+ holdout were read only for source metadata and were not used in state, outcome, tier, AU, loop, or uncertainty calculations.
