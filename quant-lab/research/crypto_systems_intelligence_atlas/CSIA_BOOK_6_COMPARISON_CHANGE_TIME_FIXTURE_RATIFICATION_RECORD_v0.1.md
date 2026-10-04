# CSIA — Book 6 TIME Fixture Ratification Record v0.1

**Status:** `RATIFIED`
**Record type:** formal governance ratification record
**Date:** 2026-10-04
**Decision id:** `BOOK6-GAP6-TIME-FIXTURE-v0.1`
**Operator selection:** `RATIFY_CONSTRUCTIBLE_TIME11_STATUS_PERMUTATION_FIXTURE`
**Scope:** `BOOK 6 COMPARISON TEST FIXTURE — TIME-11.1 ONLY`
**Grants implementation authority:** `FALSE` (already granted, unchanged)

**Precondition satisfied:**
`CSIA_BOOK_6_COMPARISON_CHANGE_TIME_FIXTURE_PRE_RATIFICATION_REVIEW_v0.1.md`
= `12 / 12 PASS`, `HOLD = FALSE`.

---

## 0. What this record is

It ratifies a **fixture repair**, not a doctrine change. The TIME-11 assertion
is untouched; only the supporting record shape changed, so that the ratified case
can exist at all.

```text
RATIFIES  = THE TIME-11.1 STRUCTURAL FIXTURE
IMPLEMENTS= NOTHING
DOCTRINE_CHANGED = FALSE
```

## 1. Supersession — narrow, and deliberately so

```text
TIME_SPEC_v0.5 = SUPERSEDED PROSPECTIVELY FOR THE TIME-11.1 FIXTURE ONLY
TIME_SPEC_v0.6 = RATIFIED
v0.5_EDITED    = FALSE
```

v0.5 is **not** withdrawn. It remains ratified for every case other than the
TIME-11.1 structural fixture, and it is not edited.

```text
CASES_CARRIED_FROM_v0.5 = 252
CASES_CHANGED_BY_v0.6   = 0
TIME_CASES              = 15
TOTAL_CASES             = 252
TIME_11_MEANING_CHANGED = FALSE
```

## 2. The ratified fixture

```text
Z <- A <- S
Y <- B
      (no record supersedes B)
```

```text
A.supersedes_measurement_id = Z
S.supersedes_measurement_id = A
B.supersedes_measurement_id = Y

A_TERMINAL = FALSE   (S supersedes A)
B_TERMINAL = TRUE    (no successor)

Z, Y, S = SUPPORT/HISTORY RECORDS ONLY, NEVER CANDIDATES
```

Both `A` and `B` declare an outgoing supersession edge, so either may legally
carry `status = SUPERSEDED` under the **accepted, unmodified** lifecycle
validator. `A` is non-terminal because a *successor exists* — never because a
*status exists*.

## 3. The four permutations, all now constructible

```text
case 1   A=OBSERVED    B=OBSERVED    -> CONSTRUCTIBLE, REGISTERED
case 2   A=SUPERSEDED  B=OBSERVED    -> CONSTRUCTIBLE, REGISTERED
case 3   A=OBSERVED    B=SUPERSEDED  -> CONSTRUCTIBLE, REGISTERED
case 4   A=SUPERSEDED  B=SUPERSEDED  -> CONSTRUCTIBLE, REGISTERED
```

Required outcome in every case:

```text
A_FILTERED_BECAUSE      = TERMINALITY
STATUS_REFUSAL          = FALSE
LEXICAL_TIEBREAK_SEES_A = FALSE
SELECTION               = B

STATUS_CHANGES_TIME11_OUTCOME                    = FALSE
STATUS_IS_ONLY_FIELD_VARIED_ACROSS_THE_FOUR_CASES = TRUE
```

## 4. What this record does NOT do

```text
STATUS_VALIDATOR_EDIT        = FALSE
OBSERVATION_STATUS_CHANGED   = FALSE
NEW_LIFECYCLE_FIELD_ADDED    = FALSE
STATUS_AUTHORITY             = FALSE
REGISTRATION_POLICY_CHANGED  = FALSE
LIFECYCLE_REMEDY_SELECTED    = NONE
DEFERRED_LIFECYCLE_RECORD    = UNCHANGED
B_STRICT_CHANGED             = FALSE
GAP_6_REOPENED               = FALSE
GAP_7_REOPENED               = FALSE
```

The lifecycle incoherence is real and is still deferred. This repair routes
around it rather than resolving it, which is the operator's decision and is
recorded as such. Anyone reading this record should not conclude the validator
is now coherent — it is not, and this record does not pretend otherwise.

## 5. GAP-7 case count, restated

The GAP-7 ratified contract is **40** cases, not 39, following
`BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1`:

```text
PRIOR_CASES          = 39
TERM_6               =  1   (added by BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1)
RATIFIED_GAP7_CASES  = 40

CARR-1..19  CURR-S1..3  TERM-1..6  NV-1..10  STRUCT-1..2
```

`TERM-6` is the paired negative of `TERM-4`: in `A <- B` and `A <- C`, `A` is
not current while `B` and `C` resolve current when their own five conjuncts hold.

```text
SUCCESSOR_CURRENTNESS_SCOPE = PER_RECORD
FAMILY_FAIL_CLOSED           = NOT RATIFIED
```

## 6. Implementation authority

```text
IMPLEMENTATION_AUTHORITY = REMAINS TRUE UNDER BOOK6-IMPL-CONSOLIDATED-v0.4
BOOK_6_IMPLEMENTED       = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

The authorization is unchanged and was never suspended. What changed is that a
blocked case is now buildable.

## 7. Explicit non-actions

```text
STATUS_VALIDATOR_EDITED     = FALSE
OBSERVATION_STATUS_RENAMED  = FALSE
OBSERVATION_STATUS_DELETED  = FALSE
LIFECYCLE_REMEDY_SELECTED   = NONE
REGISTRATION_POLICY_CHANGED = FALSE
DOCTRINE_CHANGED            = FALSE
GAP_6_REOPENED              = FALSE
GAP_7_REOPENED              = FALSE
RATIFIED_RECORD_EDITED      = FALSE
TEST_SPEC_v0.5_EDITED       = FALSE
IMPLEMENTATION_STARTED      = FALSE
SOURCE_CHANGED              = FALSE
BRANCH_CREATED              = FALSE
WORKTREE_CREATED            = FALSE
FROZEN_WORKTREE_MUTATED     = FALSE
BOOK_7_WORKED_ON            = FALSE
CHOIR_TOUCHED               = FALSE
```

## 8. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.6.md        RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_TIME_FIXTURE_PRE_RATIFICATION_REVIEW_v0.1.md  12/12
CSIA_BOOK_6_COMPARISON_CHANGE_TIME_TEST_RATIFICATION_RECORD_v0.1.md   TIME-1..15
CSIA_BOOK_6_GAP7_SUCCESSOR_CURRENTNESS_RATIFICATION_RECORD_v0.1.md   TERM-6
CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md    UNCHANGED
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.4.md law unchanged
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

---

**Status:** `RATIFIED`. The fixture is constructible; doctrine is unchanged.
