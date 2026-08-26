# Chapter 7.5 — Robustness Testing

## Mission

Determine whether apparent financial edge survives reasonable perturbations in time, parameters, instruments, regimes, data, and execution rather than existing only at one optimized point.

## 7.5.1 Robustness Axes

As applicable:

```text
walk-forward/out-of-sample
time subperiods
market regimes
instrument cross-section
parameter neighborhoods
entry/exit perturbation
cost/slippage stress
data-source sensitivity
session/timezone perturbation
bootstrap/resampling
signal delay
missing/noisy data
```

## 7.5.2 Parameter Topology

Prefer broad stable regions over isolated optimal peaks. A strategy requiring one exact parameter discovered ex post receives fragility evidence.

## 7.5.3 Multiple Testing

Track the number of variants/hypotheses tried. Selection after many experiments requires appropriate skepticism and statistical treatment; QCAE must not report only the winner.

## 7.5.4 Regime Analysis

CEREBUS framing emphasizes regime alignment. Robustness should identify which structural/regime conditions support or invalidate the edge rather than demanding false universality.

## 7.5.5 Failure Localization

A strategy can fail globally but contain a valid atom under a specific regime. Preserve that conditional evidence without promoting it beyond its validated domain.

## 7.5.6 Stress vs Mutation

Robustness tests should not mutate the strategy until it succeeds. Material logic changes create a new candidate/experiment.

## 7.5.7 Statistical Uncertainty

Report confidence/uncertainty appropriate to sample dependence and trade count. Avoid naive iid assumptions when market observations are dependent.

## Invariants

1. Edge must survive relevant perturbations.
2. All material variants tested are counted.
3. Stable neighborhoods outrank isolated optima.
4. Regime-specific validity is allowed and explicitly bounded.
5. Material strategy changes create new experiments.
6. Statistical treatment respects dependence/sample limitations.

## Exit Criteria

QCAE knows the validated domain, fragility surface, and major failure regimes of the claimed financial capability.
