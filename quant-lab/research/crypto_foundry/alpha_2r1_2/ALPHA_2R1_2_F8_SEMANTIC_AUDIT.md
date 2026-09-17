# ALPHA-2R1.2 F8 Semantic Audit

## Frozen F8 Contract Text

```
"rule_id": "F8",
"condition": "control_net_PF >= strategy_net_PF (CI overlap)",
"reason": "STATE_ADDS_NO_VALUE",
"method": "paired_bootstrap_difference",
"n_resamples": 10000,
"seed": 31082026,
"ci_level": 0.95
```

## Three Decomposed Concepts

### A: PF_POINT_ESTIMATE_CONDITION
`control_net_PF >= strategy_net_PF`

This is a direct comparison of two scalar values:
- `strategy_net_PF` = total net return / |total net loss| for the strategy
- `control_net_PF` = total net return / |total net loss| for the matched control

This is deterministic, computed from the full trade ledger. No bootstrap required.

### B: PAIRED_BOOTSTRAP_DIFFERENCE
The method specified is `paired_bootstrap_difference`.

What is bootstrapped:
- Paired net_R observations (strategy trade vs matched control trade)
- Each pair shares approximate market regime via time-proximity matching
- 10,000 resamples with replacement
- For each resample: compute mean(net_R_control) - mean(net_R_strategy)
- Resulting distribution gives CI for the paired difference

What is NOT bootstrapped:
- PF itself. PF is a ratio of sum(positive net_R) / |sum(negative net_R)|.
- The bootstrap does not directly test PF.

### C: CI_OVERLAP
`(CI overlap)` appears in parentheses after the PF condition.

Interpretation options:
1. CI of paired bootstrap difference overlaps zero → strategy and control are statistically indistinguishable
2. CIs of the two PF point estimates overlap
3. Parenthetical qualifier meaning "assessed via CI"

The contract uses `paired_bootstrap_difference` as method, which produces a CI for the net_R difference. Interpretation 1 is most consistent with the method.

## Boolean Trigger Expression — Ambiguity

The frozen text can be parsed as:

**Reading 1 (Conjunction):**
```
F8 = (control_PF >= strategy_PF) AND (bootstrap_CI_overlaps_zero)
```
Both conditions must be true.

**Reading 2 (PF-only):**
```
F8 = (control_PF >= strategy_PF)
```
CI is the reporting method, not a gate.

**Reading 3 (Statistical indistinguishability):**
```
F8 = (bootstrap_CI_overlaps_zero)
```
PF comparison is informational; the statistical test decides.

## Fail-Closed Resolution

The frozen wording does NOT uniquely determine the Boolean expression.

The parenthetical `(CI overlap)` could be:
- An additional conjunction gate (Reading 1)
- A method descriptor (Reading 2)
- The primary condition (Reading 3)

Under the fail-closed ambiguity rule from ALPHA-2R1.2:

**F8_CANONICAL_STATUS = AMBIGUOUS_NON_DECISIVE**

F8 is retained as descriptive evidence only. No strategy's falsification status depends solely on F8.

## Why This Is Safe

All 13 Generation-1 strategies are independently falsified by other frozen rules:

| Strategy | Other falsification rules |
|----------|--------------------------|
| S001 | F3, F4, F10, F12 |
| S002 | F6, F7 |
| S003 | F6, F7, F10 |
| S004 | F3 |
| S005 | F2, F3, F4, F6, F7 |
| S006 | F2, F3, F4, F7 |
| S007 | F3, F6, F7 |
| S008 | F3, F4 |
| S009 | F3, F4 |
| S010 | F3 |
| S011 | F3, F6, F7, F10 |
| S012 | F3, F6, F7, F10 |
| S013 | F3, F6, F7 |

No strategy is classified SURVIVES_DEVELOPMENT based on F8 alone.

## What the Bug Was

The ALPHA-2R1.1 reconciliation script computed:

```python
pf_condition = obs_diff >= 0  # obs_diff = bootstrap mean of (ctrl_net_R - strat_net_R)
```

This is NOT the PF point-estimate comparison. It is the sign of the paired net_R mean difference.

For S009: obs_diff = -0.191 (strategy net_R mean > control net_R mean on paired basis)
But: strategy net_PF = 0.71 < control net_PF = 0.74

The PF and net_R mean can disagree because PF is a ratio (wins/|losses|) while net_R mean is arithmetic.

The script labeled the net_R-based flag as "pf_condition_met", which is factually incorrect.

## Corrected PF Comparisons

Using actual PF point estimates from the immutable strategy/control metrics:

| Strategy | Strat PF | Ctrl PF | Ctrl >= Strat (PF) | Old Script Said |
|----------|----------|---------|---------------------|-----------------|
| S001 | 0.8023 | 0.7614 | FALSE | FALSE ✓ |
| S002 | 1.0163 | 0.7986 | FALSE | FALSE ✓ |
| S003 | 1.0093 | 0.7986 | FALSE | FALSE ✓ |
| S004 | 0.8777 | 0.7986 | FALSE | FALSE ✓ |
| S005 | 0.7702 | 0.7986 | TRUE | TRUE ✓ |
| S006 | 0.5908 | 0.7986 | TRUE | FALSE ✗ |
| S007 | 0.9558 | 0.7519 | FALSE | FALSE ✓ |
| S008 | 0.6220 | 0.7519 | TRUE | FALSE ✗ |
| S009 | 0.7133 | 0.7433 | TRUE | FALSE ✗ |
| S010 | 0.7292 | 0.7433 | TRUE | FALSE ✗ |
| S011 | 0.9922 | 1.2311 | TRUE | TRUE ✓ |
| S012 | 0.8800 | 1.2311 | TRUE | TRUE ✓ |
| S013 | 0.9633 | 0.7614 | FALSE | FALSE ✓ |

Corrected PF-only count: **7** (S005, S006, S008, S009, S010, S011, S012)
Old script count: **3** (S005, S011, S012)
Missed triggers: S006, S008, S009, S010

## Impact Assessment

Under ANY reading of the frozen F8 contract:

- S006, S008, S009, S010 are still FALSIFIED by other rules (F3, F4, F7)
- No strategy changes classification
- SURVIVORS remain 0
- FALSIFIED remains 13

The bug was a labeling error in the pf_condition column, not a classification error.
