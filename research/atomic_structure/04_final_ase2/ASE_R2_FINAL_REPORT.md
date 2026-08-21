# ASE_R2_FINAL_REPORT.md

Checkpoint: ASE-2.3-FINAL-MECHANISM-AND-RLOCK-FALSIFICATION-SEAL
Branch: agent/atomic-structure-foundry
Base: 846fa919f13fa50d67bcb734f6c297a0c35f5c80

## Executive Summary

ASE-2.3 performs the final bounded falsification of the surviving R_LOCK mechanism and seals the Atomic Structure Engine development program.

**Result: FAIL_ATOMIC_PREDICTIVE_ENGINE**

The R_LOCK ratio (gap-to-expected-excursion) is a robust rank effect (spearman −0.59/−0.54), but it adds **no incremental predictive information beyond raw gap distance (G)**. The CCE (Constraint Capacity Engine) hypothesis is falsified: normalizing by expected excursion does not improve calibration beyond the distance itself.

## Falsified Hypotheses (from ASE-2.2, now frozen)

| Hypothesis | Verdict | Evidence |
|---|---|---|
| NOON_LOCK_GENERAL | NOT SUPPORTED | T3 H17 touch hold 36% (not ~98%) |
| POST25_UNIVERSAL_LOCK | NOT SUPPORTED | Overall 50% reversal (not ~4.2%) |
| REMAINING_RANGE_ATOMIC_HIERARCHY | NOT SUPPORTED OOS | Hierarchy MAE worse than B0 |
| NEXT_LOOP_DIRECTION_ATOMIC_STATE | NOT SUPPORTED OOS | Richer models worse log-loss |
| FAILURE_TYPE_DIRECTIONAL_EDGE | LOW/NOT SUPPORTED | Near 50/50 next-direction |
| RLOCK_ADDS_INCREMENTAL_INFO | NOT SUPPORTED | Conditional-G spearman −0.12/−0.15 |

## R_LOCK Falsification Results

### Robustness (survives all)
- Subperiod: 2023 UP −0.52, DN −0.54; 2024 UP −0.66, DN −0.54
- Estimator sensitivity: E0–E3 spearman −0.54 to −0.66
- Rolling windows 60/90/120: stable across all windows
- Monotone buckets: violation rate 87%→7% across R_LOCK quintiles

### Incremental Info (fails)
- R_LOCK vs G: brier 0.1569 vs 0.1568 (UP), 0.1887 vs 0.1843 (DN) — **no improvement**
- R_LOCK vs G/ATR: brier 0.1569 vs 0.1577 (UP) — **marginally worse**
- Conditional-G spearman: −0.12 (UP), −0.15 (DN) — **weak residual**
- Bootstrap P(RLOCK better than G): ~0.50 — **no significant improvement**

### Interpretation
The capacity ratio R_LOCK = G / E is essentially a reparameterization of G. The denominator E (expected excursion) is highly correlated with G's scale, so the ratio doesn't carry independent information. The "constraint capacity" mechanism is real in the sense that larger gaps break more often, but the capacity ratio itself doesn't add predictive power beyond the gap distance alone.

## State Compression

| Variable | Brier | Log-Loss | vs NULL |
|---|---|---|---|
| G (gap) | 0.157 | 0.488 | −0.093 |
| RLOCK | 0.157 | 0.488 | −0.093 |
| balance | 0.208 | 0.612 | −0.081 |
| mr_atr | 0.237 | 0.666 | −0.027 |
| tier | 0.239 | 0.672 | −0.021 |
| E1 (expected) | 0.239 | 0.670 | −0.023 |
| 3am_state | 0.239 | 0.672 | −0.021 |
| loop_bucket | 0.240 | 0.700 | +0.007 |

**Minimum surviving state: G (gap distance) + directional_balance**

## Generalized Capacity Checkpoints

The capacity ratio works at 06:00 and 09:00 (as expected from the raw gap effect), but the mechanism doesn't add value beyond gap distance at any checkpoint.

## Touch vs Close

Side-specific touch and close violation rates are consistent with the gap-distance interpretation — larger gaps break more often regardless of completion semantics.

## Program Routing

**Seal ASE development as failed. No rescue chain.**

The CCE (Constraint Capacity Engine) hypothesis is falsified: capacity ratio adds no info beyond gap distance. The broader Atomic transition engine hypotheses are all falsified.

Directional balance is a strong descriptive predictor (brier 0.208) but not a mechanism — it's a state variable that correlates with violation probability.

## Explicit Disclaimers

```
strategy_pnl_computed = false
optimization_performed = false
confirmation_consumed = false
holdout_consumed = false
ASE3_authorized = false
```

## Files Produced

- ASE_EVIDENCE_LINEAGE_AUDIT.md
- ASE_EVIDENCE_LINEAGE.json
- ASE_RLOCK_SPEC.md
- ASE_RLOCK_SUBPERIOD.csv
- ASE_RLOCK_ROLLING.csv
- ASE_RLOCK_ESTIMATOR_SENSITIVITY.csv
- ASE_RLOCK_BASELINE_COMPARISON.csv
- ASE_RLOCK_CALIBRATION.csv
- ASE_RLOCK_MONOTONICITY.csv
- ASE_RLOCK_SIDE_SYMMETRY.csv
- ASE_RLOCK_TIER_INTERACTION.csv
- ASE_RLOCK_HORIZON_STABILITY.csv
- ASE_GENERALIZED_CAPACITY_CHECKPOINTS.csv
- ASE_RLOCK_TOUCH_VS_CLOSE.csv
- ASE_POST25_CAPACITY_ANALYSIS.csv
- ASE_STATE_COMPRESSION.csv
- ASE_DAY_BOUNDARY_INDICATORS.parquet
- ASE_RLOCK_MASTER.csv
- ASE2_FINAL_BOOTSTRAP.csv
- ASE_R2_FINAL_REPORT.md
- ASE_R2_FINAL_DECISION.json
