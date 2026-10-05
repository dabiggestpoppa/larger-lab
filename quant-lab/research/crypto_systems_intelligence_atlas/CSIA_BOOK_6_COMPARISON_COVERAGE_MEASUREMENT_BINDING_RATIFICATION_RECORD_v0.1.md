# CSIA — Book 6 Comparison Coverage Measurement Binding Ratification Record v0.1

**Status:** `RATIFIED`
**Record type:** governance decision record
**Date:** 2026-10-05
**Decision id:** `BOOK6-COVERAGE-MEASUREMENT-BINDING-v0.1`
**Operator selection:** `BIND_COVERAGE_TO_THE_COMPARISON_MEASUREMENT`
**Resolves:** `CSIA_BOOK_6_COMPARISON_COVERAGE_MEASUREMENT_BINDING_ERRATUM_v0.1.md` §7
**Grants implementation authority:** `FALSE` (already held; unchanged)
**Changes implementation:** `FALSE`

```text
COVERAGE_EVIDENCE_ATTACHES_TO = THE COMPARISON MEASUREMENT
CROSS_MEASUREMENT_COVERAGE_SUBSTITUTION = PROHIBITED
RULE_MATCH_ALONE_IS_NOT_ENOUGH          = TRUE
ERRATUM_S7_OPEN                          = FALSE   (now closed)
IMPLEMENTATION_AUTHORIZED               = TRUE    (offline amendment scope only)
```

---

## 0. What this record is

The measurement-binding erratum (§1–§6 `RATIFIED`) established that coverage
evidence binds to exact measurement identity and that check 16 must not accept
an observation belonging to another measurement. It left **one** question open
at §7, on which the corpus was silent:

> which measurement does the singular `ChangeObservation.coverage_observation_ref`
> canonically cover?

This record closes §7. The operator has ruled. Nothing else is decided here; the
erratum's §1–§6 stand unamended and the substrate it cites is untouched.

The erratum is **not edited**. Its §7 remains `OPEN` as written, exactly as the
grammar v0.7 status-gate erratum left its stray sentence in place; this record is
what discharges it.

---

## 1. The decision

```text
ChangeObservation.coverage_observation_ref
    covers the COMPARISON MEASUREMENT
```

```text
BIND_COVERAGE_TO_THE_COMPARISON_MEASUREMENT   = SELECTED
BIND_COVERAGE_TO_THE_BASELINE_MEASUREMENT     = NOT SELECTED
REQUIRE_DISTINCT_COVERAGE_EVIDENCE_FOR_BOTH   = NOT SELECTED
```

Consequences, and only these:

```text
COMPARISON_MEASUREMENT_COVERAGE_AUTHORIZES = TRUE
BASELINE_MEASUREMENT_COVERAGE_AUTHORIZES   = FALSE   (not decided here; not refused forever)
SAME_METRIC_WRONG_MEASUREMENT              = REFUSED
```

The second line is a statement about **this** decision's scope. It says the
baseline measurement's coverage is not the evidence the comparison replay
consumes. It does not decide whether a future amendment may require baseline
coverage as a second, distinct field; that would be the `REQUIRE_BOTH` option,
which was available and was **not** selected.

---

## 2. Why the ambiguity was real

The erratum's §7.2 audit stands. In summary, fourteen governing artifacts were
checked and none binds the singleton ref to either side. The corpus's own
generic term for the measurement side — *"input measurement"*, used by canonical
checks 10 and 11 — means **all** inputs including the baseline, so it could not
settle the question either. "the comparison input" occurred once, in the
clarification at `:197`, and is not a defined term.

Two readings were genuinely available and neither was ratifiable from the corpus.
That is why the question went to the operator instead of being resolved by the
implementation.

---

## 3. The plurality problem, answered honestly

`ChangeObservation.comparison_measurement_refs` is **plural** — grammar v0.1
`:134` "one or more; non-empty", enforced as `Field(min_length=1)` on a tuple at
[book6_comparison_contracts.py:407](../book6_comparison_contracts.py). The
selected binding names **one** measurement. The tension is real and this record
does not paper over it.

It is resolved by keeping the replay **per-measurement** and refusing to invent
an aggregate:

```text
COVERAGE_REPLAY_GRANULARITY      = ONE MEASUREMENT PER REPLAY
AGGREGATE_COVERAGE_VERDICT       = NOT DEFINED   (and NOT introduced here)
COMPARISON_MEASUREMENTS_REPLAYED = EACH, AGAINST ITS OWN COVERAGE OBSERVATION
```

A `ChangeObservation` carrying N comparison measurement refs is replayed N times,
each time with the exact `comparison_measurement_ref` under test and the coverage
observation attached to **that** measurement. Nothing here says how N replayed
verdicts become one field on the record — that question is untouched and no
aggregation semantics are created, because

```text
NEW AGGREGATION SEMANTICS = NONE
```

The single `coverage_observation_ref` field is unchanged. How a plural
comparison set populates it is a later question for a later amendment, and this
record does not pre-empt it.

---

## 4. The replay obligation this authorises

`replay_coverage_checks` must receive the expected identity as an explicit,
exact input — never inferred:

```text
replay_coverage_checks(..., comparison_measurement_ref: str, ...)

INFER_FROM_RULE_ID           = PROHIBITED
INFER_FROM_METRIC_ID         = PROHIBITED
INFER_FROM_CALLER_CONVENTION = PROHIBITED
INFER_FROM_THE_OBSERVATION   = PROHIBITED
INFER_FROM_REGISTRY_ORDERING = PROHIBITED
OMISSION                     = STRUCTURALLY IMPOSSIBLE (required parameter)
```

The inference prohibition is the reason the parameter carries no default and no
optional path. A default would let the engine pick an identity, and any identity
it could pick — the metric, the rule, the observation itself — is either
meaningless or the substitution itself.

Check 16's binding, **before** any `observed_fraction` is read:

```text
coverage_observation.measurement_id == comparison_measurement_ref
  NO   -> CHECK 16 = FAIL, VERDICT = UNKNOWN, COMPARABILITY = UNRESOLVED,
          reason: coverage observation belongs to another measurement
  YES  -> observed_fraction >= required_fraction -> SUFFICIENT
          observed_fraction <  required_fraction -> INSUFFICIENT
```

```text
WRONG_MEASUREMENT_PRODUCES_SUFFICIENT   = PROHIBITED
WRONG_MEASUREMENT_PRODUCES_INSUFFICIENT = PROHIBITED
WRONG_MEASUREMENT_IS_A_FINDING          = FALSE   (an absence of basis, not a verdict)
```

The last two blocks are the same requirement from the erratum §5.3, restated
here so the decision and its consequence sit together.

---

## 5. What this record does not do

```text
CHANGEOBSERVATION_FIELD_ADDED       = NONE
NEW COVERAGE OBSERVATION SCHEMA      = NONE
NEW AGGREGATION SEMANTICS            = NONE
NEW AUTHORITY-BEARING CLASS          = NONE   (contract count remains exactly 2)
NEW COVERAGE REGISTRY                = NONE
NEW COVERAGE POLICY                  = NONE
COVERAGERULE_REGISTRY AUTHORITY      = UNCHANGED
GAP_3 / GAP_4 REOPENED               = FALSE
BASELINE_COVERAGE_DECIDED            = FALSE   (out of scope by selection)
SOURCE_FILE_WRITTEN_OR_EDITED        = FALSE
TEST_CODE_WRITTEN_OR_EDITED          = FALSE
ERRATUM_EDITED                       = FALSE   (history preserved)
RATIFIED_RECORD_EDITED               = FALSE
BRANCH_REWRITTEN_OR_REBASED          = FALSE
FROZEN_BOOK_6_WORKTREE_MUTATED       = FALSE
BOOK_7_WORKED_ON                     = FALSE
LIVE_ACQUISITION                     = FALSE
```

---

## 6. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (offline amendment scope only, unchanged)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## 7. Cross-references

```text
CSIA_BOOK_6_COMPARISON_COVERAGE_MEASUREMENT_BINDING_ERRATUM_v0.1.md  §1-§6 ratified, §7 discharged
CSIA_BOOK_6_COMPARISON_COVERAGE_REPLAY_BINDING_CLARIFICATION_v0.1.md    §4 validation 4, §6
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md                            canonical checks 12-16, 19
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.3.md                            coverage_observation (singleton)
book6_comparison_contracts.py                                           comparison_measurement_refs:407
book6_definitions.py                                                    CoverageObservation:192
book6_registry.py                                                       register_coverage:152, coverage_of:398
book6_comparison_coverage.py                                            replay_coverage_checks (Rung 7)
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

---

**Status:** `RATIFIED`. The erratum's open question is closed. The comparison
measurement's coverage is the evidence; the baseline's is not. No schema, no
aggregation semantics, no new authority.
