# Chapter 7.2 — Signal Reconstruction

## Mission

Recover the exact information set and decision rule that produces a financial signal so QCAE can test whether the claimed strategy is causally executable rather than a hindsight description.

## 7.2.1 Reconstruction Elements

```text
input variables
source timestamps
feature transforms
lookback windows
state/regime variables
signal threshold
entry condition
exit condition
position sizing
rekey/reset behavior
missing-data behavior
session/timezone rules
```

## 7.2.2 Information-Time Rule

For every input determine when it becomes knowable to the strategy. Bar-close values, revised macro data, future session extremes, and finalized index constituents cannot be treated as available earlier.

## 7.2.3 State Machine

Strategies with path dependence should be reconstructed as explicit state transitions rather than compressed into vectorized hindsight logic.

## 7.2.4 Ambiguity

If paper/code descriptions permit multiple interpretations, implement alternatives or mark unresolved; do not choose the best-performing interpretation after observing outcomes.

## 7.2.5 Reference Reproduction

First attempt faithful reconstruction of the source method. Quant Lab modifications become separate variants with separate identities.

## 7.2.6 CEREBUS Geometry

When evaluating a claimed CEREBUS-compatible strategy, structural events, tier filters, rekeys, checkpoints, and invalidations must be represented according to the governing manual rather than approximate retail analogues.

## Invariants

1. Signal logic is reconstructed at the information time available.
2. Path-dependent logic uses explicit state where required.
3. Ambiguity is not optimized away after seeing results.
4. Source reproduction and Quant Lab variants remain separate.
5. CEREBUS constructs preserve manual semantics.

## Exit Criteria

QCAE has an executable, timestamp-causal signal specification suitable for independent data/backtest validation.
