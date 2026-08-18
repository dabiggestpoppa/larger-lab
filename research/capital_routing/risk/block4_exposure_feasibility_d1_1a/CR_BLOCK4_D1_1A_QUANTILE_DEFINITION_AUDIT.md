# CR-BLOCK4-D1.1A QUANTILE DEFINITION AUDIT

## Question

The D1 plan report and the D1.1 method record different quantile values for
the same economic-target book. Is this (A) same book + different statistical
definitions, (B) different columns/books, or (C) a genuine inconsistency?

## Source audit

| fact | value |
|---|---|
| same source book | **True** |
| canonical book hash (D1 source) | `b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a` |
| canonical book hash (D1.1 source) | `b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a` |
| D1 source | CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv -> notional_multiple_equity (ACCEPT_FULL) |
| D1.1 source | CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv -> target_notional_account_ccy at E=1 (ACCEPT_FULL) |
| max abs value diff between sources | 4.983e-13 (float-op-order noise) |

Both sources are the same 826 accepted events; the two columns agree to
~1e-13 (the D1.1 translations were computed through the D0.1 core at E=1, the
D1 multipliers by the R1 engine — identical formula, different float-op
order).

## Definition A — DESCRIPTIVE_DISTRIBUTION_QUANTILE (D1 plan)

Formula: pandas `Series.quantile(q)` — linear interpolation between order
statistics (numpy type-7 / R-7 default). These are ESTIMATES of the
underlying distribution of target-notional multiples.

| quantile | value |
|---|---|
| q25 | 1.1023374233055268 |
| q50 | 1.9842341231185205 |
| q75 | 3.513366582731397 |
| q95 | 7.61048370479638 |
| q99 | 16.036374775248472 |

Reproduces the D1-recorded values exactly (median 1.9842341231185 etc.).

## Definition B — RANK_BIN_EDGE (D1.1 quantile-distortion bins)

Formula: nearest-rank (inverted CDF): the value of the event at rank fraction
q — `sorted[ceil(n*q) - 1]` of the 826-event book. These are the EVENT VALUES
at rank boundaries, used ONLY to assign events to frozen quantile bins (never
recomputed per cap).

| edge | value |
|---|---|
| q25 | 1.102320085105 |
| q50 | 1.979422975748 |
| q75 | 3.524935294373 |
| q95 | 7.61103477694 |
| q99 | 16.159547393888 |

Reproduces the D1.1-recorded edges exactly (q50 1.979422975748 etc.).

## Verdict

**A. same source book, different statistical definitions — DESCRIPTIVE_DISTRIBUTION_QUANTILE (interpolated distribution estimate) vs RANK_BIN_EDGE (rank-fraction event value).**

- `quantile_difference_explained = true`
- `source_distribution_mismatch = false`
- The two numbers must never be conflated: label them
  DESCRIPTIVE_DISTRIBUTION_QUANTILE vs RANK_BIN_EDGE.
- No STOP condition triggered; D1.2 planning may proceed after human review.
