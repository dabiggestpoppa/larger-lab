# ASE_RLOCK_SPEC.md

Checkpoint: ASE-2.3-FINAL-MECHANISM-AND-RLOCK-FALSIFICATION-SEAL
Branch: agent/atomic-structure-foundry
Base: 846fa919f13fa50d67bcb734f6c297a0c35f5c80

## Frozen formula (tested exactly, no further adaptation)

At the decision time t = 12:00 (primary), or t in {06:00, 09:00, 12:00} for
the generalized capacity table.

```
G_UP   = H_PRE12 - P_12        (pips)
G_DOWN = P_12 - L_PRE12        (pips)
```

- H_PRE12 / L_PRE12 = full pre-noon day extreme (19:00 D-1 -> 12:00 D)
- P_12 = last completed M5 close before 12:00 (11:55 close)

Expected side excursion must be causal: estimated ONLY from prior development
observations (dates strictly before the current date). No future realized
excursion in the denominator.

Primary estimator:

```
E_PM_SIDE = median prior realized afternoon max side excursion (12:00 -> 17:00)
```

(Estimator sensitivity table E0..E3 defined in ASE_RLOCK_ESTIMATOR_SENSITIVITY.csv)

```
R_LOCK_UP   = G_UP   / E_PM_UP
R_LOCK_DOWN = G_DOWN / E_PM_DOWN
```

## Outcome variables (all from raw bars after 12:00)

- VIOLATION_TOUCH: post-noon high > H_PRE12 (up) or low < L_PRE12 (down)
- VIOLATION_CLOSE: post-noon close > H_PRE12 (up) / close < L_PRE12 (down)

Horizons evaluated separately: 12->17, 12->19, 12->next 03.
Sides evaluated separately; never combined.

## Falsification gates (this checkpoint)

1. subperiod: R_LOCK effect must exist in BOTH 2023 and 2024 (same direction,
   meaningful magnitude)
2. rolling windows 60/90/120 sessions: effect must persist on majority of
   windows, top-vs-bottom bucket violation delta positive and large
3. estimator sensitivity: monotone relationship must survive E0..E3
4. baseline comparison: R_LOCK must beat raw G, G/ATR, morning/ATR, tier,
   time-only on Brier/log-loss/rank correlation
5. calibration: simple logistic on log(R_LOCK) must calibrate OOS
6. monotonicity: fixed development quantile bins must decline monotonically
   for touch and close
7. side symmetry: UP and DOWN both show monotone effect; difference reported
   with bootstrap CI
8. tier interaction: R_LOCK explains tier differences (T3 higher ratio),
   or tier adds
9. horizon: informative at 17, 19, next03
10. generalized capacity: same form at 06AM/09AM/12PM causal boundaries
11. post25: capacity ratio at E25 explains T1/T2/T3 reversal gradient

Final decision enumerated in ASE_R2_FINAL_DECISION.json:
PASS_EMPIRICAL_TRANSITION_ENGINE /
PASS_CONSTRAINT_CAPACITY_ENGINE_ONLY / FAIL_ATOMIC_PREDICTIVE_ENGINE.