# CSIA — Book 6 Comparison/Change TIME Test Pre-Ratification Review v0.1

**Status:** `AUDIT_FINDING` — assesses; ratifies nothing.
**Date:** 2026-10-04
**Decision id:** none.
**Subject:** `CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.5.md`
**Grants implementation authority:** `FALSE`

```text
REVIEW_TYPE = TEST_CONTRACT_PRE_RATIFICATION
QUESTIONS   = 10
PASS        = 10
FAIL        =  0

RESULT = PASS (10 / 10)
```

---

## 0. Per-case audit of TIME-1..TIME-15

Each case re-read against **current** ratified doctrine, not against v0.4's
own description of itself.

| Case | Subject | Verdict |
|---|---|---|
| TIME-1 | instantaneous stays a point; remains eligible | `CONSISTENT` |
| TIME-2 | `t1<t2<t3<t4` selects `t3` | `CONSISTENT` |
| TIME-3 | caller order irrelevant | `CONSISTENT` |
| TIME-4 | `observed_at` irrelevant | `CONSISTENT` |
| TIME-5 | same `valid_time` tie resolves lexically | `CONSISTENT` |
| TIME-6 | same instant is not prior (strict `<`) | `CONSISTENT` |
| TIME-7 | interval behaviour invariant under effective keys | `CONSISTENT` |
| TIME-8 | mixed shape structurally ineligible, no coercion | `CONSISTENT` |
| TIME-9 | forged interval rejected at construction | `CONSISTENT` |
| TIME-10 | interval missing bounds rejected | `CONSISTENT` |
| **TIME-11** | **eligibility before ordering — by lineage, not status** | `CONSISTENT` (repaired) |
| TIME-12 | derived keys never persist | `CONSISTENT` |
| TIME-13 | no zero-width interval constructed | `CONSISTENT` |
| TIME-14 | no one-day convention | `CONSISTENT` |
| TIME-15 | no `observed_at` ordering path | `CONSISTENT` |

```text
TIME_CASES_CONSISTENT = 15 / 15
CONTRADICTS_RATIFIED_DOCTRINE = 0
```

### 0.1 The prior verdict, for the record

```text
TIME-11 in v0.4 = CONTRADICTS_RATIFIED_DOCTRINE  (status authority-bearing
                                                    AND ordering inverted)
TIME-11 in v0.5 = CONSISTENT
```

TIME-5 and TIME-11 are complementary halves of one property: TIME-5 proves the
lexical tie-break fires when both candidates are terminal; TIME-11 proves it
never sees a candidate that is not. Neither alone is sufficient.

## 1. Production anchors verified read-only at `5f94c3f40c`

```text
TIME-9   book6_records.py:169-175
         non-interval classes may not declare an interval        VERIFIED
TIME-10  book6_records.py:160-168
         interval classes require [start,end) with start < end   VERIFIED
TIME-14  book6_support.py:419
         timedelta(days=1) in windowed_observation; defined at :384,
         called only at :442 within the same module, exported at :608;
         no engine module imports it; external use is test files only  VERIFIED
TIME-11  terminality from registered lineage
         book6_registry.py:172-191 measurement_history walks forward
         via supersedes_measurement_id == chain[-1].measurement_id VERIFIED
```

TIME-14 deserves a note: `windowed_observation` lives in `src/`, not `tests/`,
so "fixture-only" is a claim about the **import graph**, not about file
location. It is exported in `__all__` and therefore importable. The assertion
is true as verified, and must be tested behaviourally rather than structurally.

---

## 2. The ten questions

| # | Question | Answer | Basis |
|---|---|---|---|
| 1 | Are all 15 TIME cases consistent with ratified 6E? | **YES** | §0 table; TIME-11 repaired to lineage mechanism |
| 2 | Does any TIME case make `ObservationStatus` authority-bearing? | **NO** | TIME-11 v0.5 pins `STATUS_REFUSAL = FALSE` across four permutations |
| 3 | Does TIME-11 use terminality? | **YES** | `REFUSAL_REASON_A = TERMINALITY`; A has a registered successor |
| 4 | Is TIME-11 invariant under status permutations? | **YES** | all four cases require `selection == B`, `STATUS_CHANGES_TIME11_OUTCOME = FALSE` |
| 5 | Does any TIME case mutate `MeasurementObservation`? | **NO** | TIME-12 asserts byte-identical instances; frozen model, `extra="forbid"` |
| 6 | Does any TIME case fabricate interval semantics? | **NO** | TIME-1/13 forbid population and `[t,t]`; keys are derived and discarded |
| 7 | Does any TIME case use `observed_at` for ordering? | **NO** | TIME-4/15 forbid any read inside the ordering path |
| 8 | Does any TIME case use caller order? | **NO** | TIME-3 requires invariance under every permutation |
| 9 | Does any TIME case introduce aggregation? | **NO** | `SELECTOR_AGGREGATES = FALSE`; no TIME case aggregates or invents aggregation |
| 10 | Does v0.5 carry the 237 ratified v0.3 cases unchanged? | **YES** | §2 carried groups verbatim; none edited, renumbered, or removed |

```text
PASS = 10 / 10
HOLD_REQUIRED = FALSE
```

### 2.1 Question 2 — how it was established

Not by reading the word "status" in the case. Every TIME case was checked for
whether status is **decisive**, and specifically whether a case would still
pass if `ObservationStatus` were deleted from the model entirely.

```text
WOULD_THE_CASE_STILL_BE_MEANINGFUL_IF_STATUS_WERE_DELETED =
    TIME-1..TIME-10, TIME-12..TIME-15 : TRUE
    TIME-11 v0.4                      : FALSE  (status WAS the gate)
    TIME-11 v0.5                      : TRUE   (status only permuted)
```

That is the operative test for B-STRICT compliance, and TIME-11 v0.5 is the
only TIME case that needed it.

---

## 3. Recommendation

```text
RATIFY_TIME_1_THROUGH_TIME_15_AS_GAP6_FALSIFICATION_CONTRACT = RECOMMENDED
```

On these grounds and no others:

```text
TIME_CASES_CONSISTENT     = 15 / 15
PRE_RATIFICATION          = 10 / 10 PASS
BLOCKED_CASES             = 0
DOCTRINE_CHANGED_BY_v0.5  = FALSE
B_STRICT_PRESERVED        = TRUE
```

Ratifying the corrected contract closes the last known evidence gap: RUNG 6
would move from AMBER to GREEN, and every implementation rung would have
ratified falsification.

### 3.1 One honest caveat

TIME-11 v0.5 is **stronger** than v0.4 but still tests a property that a
sufficiently determined implementation could satisfy by accident — for example,
one that filters candidates in registry order and happens to hit A first. The
permutation matrix closes the *status* leak, which was the defect. It does not
prove the implementation reasons about terminality specifically rather than
filtering on some other correlated property.

```text
TERMINALITY_SPECIFICITY_PROVEN_BY_TIME_11_ALONE = FALSE
TIME_11_PROVES = status is not consulted; ordering never sees a non-terminal
                 candidate; the winner is B in all four permutations
```

Closing that residual would need a case where the non-terminal candidate is
lexically *smaller*, so that registry-order filtering would pick the wrong one.
That is a strengthening, not a correction, and it does not block ratification.

```text
RECOMMENDATION_IS_TO_RATIFY_AS_WRITTEN = TRUE
OPTIONAL_FUTURE_STRENGTHENING          = TIME-16 (non-terminal, lexically smaller)
```

## 4. What this review did not do

```text
RATIFIED_ANYTHING            = FALSE
IMPLEMENTATION_AUTHORIZED    = FALSE
SOURCE_CHANGED               = FALSE
TEST_CODE_WRITTEN            = FALSE
EDITED_v0.4                  = FALSE
EDITED_ANY_RATIFIED_RECORD   = FALSE
GAP_REOPENED                 = FALSE
B_STRICT_REVISED             = FALSE
STATUS_VALIDATOR_TOUCHED     = FALSE
```

## 5. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.5.md      subject
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md      superseded TIME-11
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md      6E doctrine
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md B-STRICT
CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md    out of scope
CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.1.md           RUNG 6 AMBER
```
