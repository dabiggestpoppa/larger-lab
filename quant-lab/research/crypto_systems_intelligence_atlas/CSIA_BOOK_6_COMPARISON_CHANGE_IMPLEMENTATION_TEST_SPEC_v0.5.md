# CSIA — Book 6 Comparison/Change: Implementation Test Spec v0.5

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-04
**Proposed decision id:** `BOOK6-GAP6-TIME-TESTS-v0.1`
**Supersedes as a spec:** `..._IMPLEMENTATION_TEST_SPEC_v0.4.md`, whose
**TIME-11 is INVALID** against ratified B-STRICT (section 0).
**This document grants no implementation authority.**

```text
CARRIED_CASES        = 237   (from v0.3, ratified in BOOK6-COMPARE-SUBSTRATE-v0.2)
TIME_CASES          =  15   (TIME-1..TIME-15)
TOTAL               = 252
BLOCKED             =   0
TEST_CODE_WRITTEN   =   0   (specification only)

TIME_11_STATUS_AUTHORITY      = FALSE
TIME_11_TERMINALITY_AUTHORITY = TRUE
```

**This version differs from v0.4 in exactly one case.** TIME-11 is replaced.
Every other case is carried verbatim.

---

## 0. Why v0.4 is superseded

TIME-11 as written in v0.4:

```text
SETUP   two instantaneous observations, SAME metric, SAME valid_time;
        one status == ObservationStatus.SUPERSEDED, one OBSERVED
EXPECT  selection == the OBSERVED one, for ANY lexical relationship,
        including when the SUPERSEDED ref sorts greater
...
"The gate is status is ObservationStatus.OBSERVED"
```

It contains **two** independent defects.

### 0.1 Defect one — status made authority-bearing

Ratified B-STRICT (`BOOK6-GAP7-v0.3`):

```text
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
STATUS_ONLY_CHANGES_CURRENTNESS             = FALSE
SUPERSESSION_CURRENTNESS_SOURCE             = REGISTERED_LINEAGE_TERMINALITY
```

TIME-11 makes `status` the deciding gate. It cannot be ratified in that form.

### 0.2 Defect two — it inverts the ratified ordering

GAP-6 (`BOOK6-GAP6-v0.2`) fixes a three-step ordering whose third step is:

```text
3. if still tied: stable lexical measurement_ref   (FINAL tie-break ONLY)
```

Both TIME-11 candidates share a metric and a `valid_time`, so both derived keys
tie and the lexical tie-break is exactly what fires. TIME-11 demands that the
`OBSERVED` record win "for ANY lexical relationship, **including when the
SUPERSEDED ref sorts greater**" — i.e. status silently outranks the ratified
final tie-break.

```text
TIME_11_CONTRADICTS_B_STRICT        = TRUE
TIME_11_CONTRADICTS_GAP6_ORDERING   = TRUE
TIME_11_CURRENT_FORM                = INVALID
TIME_11_RATIFIABLE_AS_WRITTEN       = FALSE
TIME_1_THROUGH_TIME_15_WHOLESALE_RATIFICATION_OF_v0.4 = BLOCKED
```

### 0.3 What TIME-11 was right about — and is preserved

Its stated purpose was correct and important:

> "a naive implementation would let the lexical tie-break resurrect a dead
> record"

That risk is real and **TIME-11 v0.5 tests it harder than v0.4 did**. The
defect was the *mechanism* (status), not the intent. v0.5 keeps the intent and
replaces the mechanism with lineage/terminality, then adds a four-case status
permutation that proves the outcome is status-invariant.

```text
THE_CASE_IS_REPAIRED_NOT_DELETED = TRUE
THE_INTENDED_RISK_IS_STILL_COVERED = TRUE
AND_IS_STRONGER_THAN_BEFORE = TRUE
```

---

## 1. The TIME group — GAP-6 temporal ordering

15 cases, each independently falsifiable, each stating its own expected result.

### TIME-1 — instantaneous candidate carries no interval, remains eligible
*(carried from v0.4 unchanged)*

```text
SETUP   one WindowClass.INSTANTANEOUS candidate (no window_start/end)
        one WindowClass.INSTANTANEOUS comparison, valid_time later
EXPECT  candidate is ELIGIBLE and is selectable
        candidate.window_start is None AND candidate.window_end is None
FORBID  any code path that populates either field
```

### TIME-2 — `t1 < t2 < t3 < t4` selects `t3`
*(carried unchanged)*

```text
SETUP   instantaneous candidates t1,t2,t3 ; comparison t4 ; t1<t2<t3<t4
EXPECT  selected baseline == t3
        (effective_end(c) == c.valid_time for all c)
```

### TIME-3 — caller order is irrelevant
*(carried unchanged)*

```text
SETUP   TIME-2 fixture, permuted N times in caller/input order
EXPECT  selected baseline == t3 for EVERY permutation
```

### TIME-4 — `observed_at` is irrelevant
*(carried unchanged)*

```text
SETUP   TIME-2 fixture with observed_at values permuted / inverted
EXPECT  selected baseline == t3 for EVERY observed_at assignment
FORBID  any read of observed_at inside the ordering path
```

### TIME-5 — same `valid_time` tie resolves lexically
*(carried unchanged)*

```text
SETUP   two instantaneous candidates, identical valid_time,
        measurement_ref values differing
EXPECT  selection == the greater lexical measurement_ref
        (effective_end ties, effective_start ties, tie-break fires)
```

TIME-5 is the **control** for TIME-11. Here both candidates are terminal, both
survive eligibility, and the lexical tie-break correctly decides. TIME-11 is
the same tie with one candidate removed earlier, by terminality. Between them
they pin both halves: the tie-break fires when it should, and does not when it
should not.

### TIME-6 — same instant is NOT prior
*(carried unchanged)*

```text
SETUP   instantaneous candidate with valid_time == comparison.valid_time
EXPECT  candidate is INELIGIBLE (strict < fails)
        result -> INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
FORBID  <= in the precedence test
```

### TIME-7 — interval behaviour identical to v0.6
*(carried unchanged)*

```text
SETUP   identical interval fixtures (non-overlapping [start,end) windows)
EXPECT  OLD_INTERVAL_ORDERING_RESULT == NEW_EFFECTIVE_KEY_ORDERING_RESULT
        for every fixture and every input permutation
```

### TIME-8 — mixed shape rejected before ordering
*(carried unchanged)*

```text
SETUP   candidate and comparison resolving to different bound
        MetricDefinition / WindowClass
EXPECT  candidate STRUCTURALLY INELIGIBLE;
        comparison NOT_COMPARABLE;
        NO ordering is computed across the shapes
FORBID  any coercion in either direction
```

### TIME-9 — forged interval on an instantaneous record is rejected
*(carried unchanged)*

```text
SETUP   WindowClass.INSTANTANEOUS observation carrying window_start/end
EXPECT  accepted model rejects at construction
        (_check_window_discipline, book6_records.py:169-175)
        MeasurementRecordError raised
```

### TIME-10 — interval record missing bounds is rejected
*(carried unchanged)*

```text
SETUP   interval window_class with window_start or window_end None
EXPECT  accepted model rejects (book6_records.py:160-168)
        MeasurementRecordError raised
```

### TIME-11 — non-terminal predecessor filtered BEFORE ordering, by lineage

**REPLACES the v0.4 case.** Mechanism changed from status to terminality;
intent preserved and strengthened.

```text
SETUP   comparison  C, instantaneous, valid_time = T
        candidate   A, instantaneous, valid_time = T - delta
        candidate   B, instantaneous, valid_time = T - delta

        A and B share: same metric_definition_ref, same semantic fingerprint,
                       same unit, same methodology, same missingness class,
                       same effective_end, same effective_start (both = valid_time)

        A has a REGISTERED SUCCESSOR in the lineage graph
          -> A.TERMINAL = FALSE
        B has no registered successor
          -> B.TERMINAL = TRUE

        A is given the LEXICALLY GREATER measurement_ref
          (so that, had A survived eligibility, A would win the tie-break)

EXPECT  A is filtered during ELIGIBILITY, before any ordering is computed
        refusal reason for A == TERMINALITY
        A never reaches the ordering phase
        the lexical tie-break NEVER SEES A
        B remains eligible
        selection == B
```

```text
ORDER   eligibility / currentness (terminality) COMPLETES BEFORE ordering
REFUSAL_REASON_A   = TERMINALITY
STATUS_REFUSAL     = FALSE
TIME_11_STATUS_AUTHORITY      = FALSE
TIME_11_TERMINALITY_AUTHORITY = TRUE
```

The refusal for A is `TERMINAL = FALSE`, and nothing else. It is **not** a
status refusal. A record is historical because a registered successor exists —
`SUPERSESSION_CURRENTNESS_SOURCE = REGISTERED_LINEAGE_TERMINALITY`.

```text
FORBID  treating A's status as the reason for exclusion
FORBID  preferring any candidate because its status is OBSERVED
FORBID  allowing the lexical tie-break to resurrect a non-terminal record
FORBID  any status validator edit, rename, or deletion (see
        ..._STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md)
```

#### TIME-11.1 — status permutation (four cases, one outcome)

The identical structural fixture runs under all four status assignments. Status
is the **only** thing that varies.

```text
case 1   A.status = OBSERVED      B.status = OBSERVED
case 2   A.status = SUPERSEDED    B.status = OBSERVED
case 3   A.status = OBSERVED      B.status = SUPERSEDED
case 4   A.status = SUPERSEDED    B.status = SUPERSEDED
```

**Required outcome in all four cases, with no exception:**

```text
A filtered because TERMINAL = FALSE
B eligible because TERMINAL = TRUE
selection == B

STATUS_CHANGES_TIME11_OUTCOME = FALSE
REFUSAL_REASON_A              = TERMINALITY
STATUS_REFUSAL                = FALSE
```

Case 1 is the sharpest of the four. Here A reads `OBSERVED` and is still
excluded, and B reads `SUPERSEDED` and is still selected. An implementation
that passes cases 2-4 by ignoring status could still fail case 1 by
*treating* `SUPERSEDED` as innocent rather than as absent. Only case 1 proves
status is not merely *not decisive* but **not consulted at all**.

```text
CASE_1_IS_LOAD_BEARING = TRUE
CASES_2_TO_4_ALONE_ARE_INSUFFICIENT = TRUE
```

#### TIME-11.2 — why this is stronger than the v0.4 case

```text
v0.4  asserted a single outcome driven by status
      -> would pass an implementation that filtered by status
      -> could not distinguish "ignores status" from "honours status"

v0.5  permutes status over a fixed structure
      -> passes ONLY an implementation that never reads status
      -> additionally pins the refusal reason, not just the winner
      -> additionally pins ordering as the phase A never reaches
```

```text
INDEPENDENTLY_FALSIFIABLE = TRUE
V0_5_IS_STRICTLY_STRONGER_THAN_V0_4 = TRUE
```

### TIME-12 — effective keys never persist
*(carried from v0.4 unchanged)*

```text
SETUP   run the selector over interval and instantaneous fixtures
EXPECT  MeasurementObservation instances are byte-identical before and after
        (frozen model; model_config extra="forbid", frozen=True)
        no window_start / window_end / derived field is added or written
        no new attribute exists on the model
```

### TIME-13 — no zero-width interval constructed
*(carried unchanged)*

```text
FORBID  any code path producing [t, t]
        any assignment of window_start == window_end
        any accepted-model violation (start >= end raises; TIME-10)
ASSERT  instantaneous records keep both interval fields None
```

### TIME-14 — no one-day convention exists
*(carried unchanged)*

```text
FORBID  any use of timedelta(days=1) in the SELECTOR
ASSERT  the fixture span at book6_support.py:419 is fixture-only and is
        never reachable from production ordering
```

Verified at `5f94c3f40c`: `windowed_observation` is defined at
`book6_support.py:384`, called only within that same module (`:442`) and
exported at `:608`. Its external consumers are test files only; **no engine
module imports it**. The assertion is therefore a genuine behavioural claim
about the import graph and must be tested as one.

### TIME-15 — no `observed_at` ordering path exists
*(carried unchanged)*

```text
FORBID  any read of observation.observed_at inside the ordering/selection code
ASSERT  observed_at is read only where knowledge time is genuinely required
```

---

## 2. Carried groups — unchanged from v0.3

Carried **verbatim**; no case edited, renumbered, or removed.

```text
COV-1..COV-12   (12)  coverage applicability and sufficiency
CHG-1..CHG-8    (8)   change observation and delta arithmetic
METH-1..METH-5  (5)   methodology compatibility and sensitivity
NULL-1..NULL-9  (9)   absence has exactly one meaning
REPLAY 1..20    (20)  the twenty replay checks, independently falsifiable
POL-1..POL-11   (11)  policy is not authority (P3 withdrawn)
NUM / UNIT / CAPP / TCMP / BASE / PHANTOM groups and carried CURR-* cases
                (172)  remainder of the ratified 237
```

---

## 3. Accounting

```text
CARRIED_CASES           = 237
TIME_CASES              =  15
TOTAL                   = 252
BLOCKED                 =   0
CASES_EDITED_FROM_v0.4  =   1   (TIME-11 only)
CASES_CARRIED_FROM_v0_4 =  14   (TIME-1..TIME-10, TIME-12..TIME-15)
PRIOR_CASE_RENUMBERED   = NONE
PRIOR_CASE_REMOVED      = NONE
TEST_CODE_WRITTEN       =   0
```

```text
RATIFIED_DOCTRINE_CHANGED_BY_v0.5 = FALSE
GAP_6_REOPENED_BY_v0.5            = FALSE
GAP_7_REOPENED_BY_v0.5            = FALSE
B_STRICT_PRESERVED                = TRUE
IMPLEMENTATION_AUTHORITY          = FALSE
```

v0.5 changes **no doctrine**. It replaces one defective test with a correct
test for the same ratified behaviour. Every case remains independently
falsifiable.

## 4. What v0.5 does not change

```text
GAP-1..GAP-5 rulings                 unchanged
GAP-6 6E projection and ordering     unchanged
GAP-7 B-STRICT                       unchanged
canonical 20-check replay            unchanged
the ratified 237 cases               unchanged
ObservationStatus semantics          unchanged
the status validator                 unchanged (deferred lifecycle amendment)
BOOK_6_IMPLEMENTATION_AUTHORITY      = FALSE
```

## 5. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md  superseded TIME-11
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.3.md  237 carried cases
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md  6E doctrine
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md  B-STRICT
CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md  out of scope
CSIA_BOOK_6_COMPARISON_CHANGE_TIME_TEST_PRE_RATIFICATION_REVIEW_v0.1.md
```
