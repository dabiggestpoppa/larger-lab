# ASE-1.1 Generation-A Tier / AU Contract Audit

## Contract result

The prior full-sample k-means was invalid for Generation-A because it calibrated on NO-GO sessions. The repaired contract retains every valid development session in the census, marks `AR > 45 pips` as `AR_NO_GO_STATE`, and fits k=3 only on the valid calibration universe.

## Frozen Generation-A EURUSD contract

- Session: `19:00` through `02:55` America/New_York, with the evening assigned to the following research date.
- AR: `(AsianHigh - AsianLow) / 0.0001`.
- AR gate: `AR > 45` is NO-GO; `AR == 45` remains T3 under the executable source wording. See `ASE_AR_MAX_BOUNDARY_AUDIT.md`.
- Calibration: deterministic k=3 on valid, non-NO-GO sessions only; centroids sorted ascending.
- Operational bins: T1 `<20`, T2 `20-<30`, T3 `30-<=45`. These are source-backed operational boundaries, stored separately from raw cluster cutoffs.
- Raw AU: `0.5 * raw centroid`.
- Operational AU: Generation-A EURUSD values `10`, `12`, `15` pips for T1/T2/T3.
- Raw trigger: `1.2 * AU_RAW`.
- Operational trigger: `12`, `15`, `19` pips for T1/T2/T3.
- Density zone: `[0.8, 1.2] * AU_OPERATIONAL` from the relevant impulse extreme.
- Shift ceiling: `1.44 * AU`, separately represented.

The operational AU/trigger mapping is a source-contract reproduction, not an outcome fit. Its explanatory claims remain `SOURCE_CLAIM` / `MECHANISTIC_HYPOTHESIS` unless independently demonstrated.

## Audit lanes

`RAW_ALL_DAYS_K3_CONTROL` is preserved as the prior failure control. `GENERATION_A_GATED_K3` is the repaired calibration lane. No PnL, 2025 confirmation, 2026 holdout, or parameter search is used.
