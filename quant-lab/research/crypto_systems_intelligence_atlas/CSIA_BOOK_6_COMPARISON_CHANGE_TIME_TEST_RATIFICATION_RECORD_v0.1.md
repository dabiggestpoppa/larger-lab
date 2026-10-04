# CSIA — Book 6 Comparison/Change TIME Test Ratification Record v0.1

**Status:** `RATIFIED`
**Date:** 2026-10-04
**Decision id:** `BOOK6-GAP6-TIME-TESTS-v0.1`
**Operator selection:**
`RATIFY_TIME_1_THROUGH_TIME_15_AS_GAP6_FALSIFICATION_CONTRACT`
**Grants implementation authority:** `FALSE`
**Ratifies doctrine:** `FALSE` — this ratifies a **test contract** only

```text
TIME-1..TIME-15 = RATIFIED
TIME_CASES      = 15
BLOCKED         =  0

TEST_SPEC_v0.3 = 237 RATIFIED CARRIED CASES  (unchanged)
TEST_SPEC_v0.5 = 252 TOTAL RATIFIED CASES

RATIFIED_DOCTRINE_CHANGED = FALSE
GAP_6_REOPENED            = FALSE
GAP_7_REOPENED            = FALSE
B_STRICT_PRESERVED        = TRUE
IMPLEMENTATION_AUTHORITY  = FALSE

BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 0. What this record ratifies, and what it does not

```text
RATIFIED = the 15 TIME cases as the falsification contract for 6E
NOT      = any doctrine (6E itself was ratified at BOOK6-GAP6-v0.2)
NOT      = any implementation authority
NOT      = any change to B-STRICT or the status validator
```

Ratifying doctrine is not ratifying the test for it. That gap — a ratified
doctrine with no ratified falsification — is precisely what this record closes.

## 1. Preconditions verified

```text
TIME_CASES_CONSISTENT = 15 / 15
CONTRADICTS_RATIFIED_DOCTRINE = 0
PRE_RATIFICATION_v0.1 = PASS (10 / 10)
BLOCKED = 0
DOCTRINE_CHANGED_BY_v0.5 = FALSE
```

Evidence:
`CSIA_BOOK_6_COMPARISON_CHANGE_TIME_TEST_PRE_RATIFICATION_REVIEW_v0.1.md`.

## 2. TIME-11 — the corrected meaning

```text
TIME_11 = A HISTORICAL CANDIDATE IS EXCLUDED BY TERMINALITY, NOT BY STATUS
```

The ratified case, in one statement:

```text
candidate A  same metric, same valid_time as B, same derived keys,
             HAS A REGISTERED SUCCESSOR  ->  A.TERMINAL = FALSE
             LEXICALLY GREATER measurement_ref
candidate B  same everything else        ->  B.TERMINAL = TRUE

A is filtered during ELIGIBILITY, before ordering computes anything
REFUSAL_REASON_A = TERMINALITY
STATUS_REFUSAL   = FALSE
the lexical tie-break NEVER SEES A
selection        = B
```

### 2.1 The status permutation is part of the ratified case

```text
case 1   A=OBSERVED    B=OBSERVED
case 2   A=SUPERSEDED  B=OBSERVED
case 3   A=OBSERVED    B=SUPERSEDED
case 4   A=SUPERSEDED  B=SUPERSEDED

REQUIRED IN ALL FOUR: selection == B, REFUSAL_REASON_A == TERMINALITY,
                      STATUS_REFUSAL == FALSE
STATUS_CHANGES_TIME11_OUTCOME = FALSE
```

Case 1 is load-bearing: A reads `OBSERVED` and is still excluded. That is what
distinguishes *status is never consulted* from *status happens not to be
decisive here*.

## 3. B-STRICT preserved — and enforced by this record

```text
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE   (unchanged)
STATUS_ONLY_CHANGES_CURRENTNESS             = FALSE   (unchanged)
SUPERSESSION_CURRENTNESS_SOURCE             = REGISTERED_LINEAGE_TERMINALITY
```

Ratifying TIME-11 v0.5 **enforces** B-STRICT rather than touching it. The case
now *requires* that status never change the outcome, which is the ratified
position written as a falsifiable assertion.

```text
B_STRICT_PRESERVED   = TRUE
B_STRICT_REVISED     = FALSE
B_STRICT_STRENGTHENED_BY_THIS_RATIFICATION = TRUE   (by test, not by wording)
```

### 3.1 What is still forbidden

```text
STATUS_VALIDATOR_EDIT_REQUIRED      = FALSE
CURRENTNESS_RESOLVER_USES_STATUS    = FALSE
RENAME_OBSERVATION_STATUS           = FORBIDDEN
DELETE_OBSERVATION_STATUS           = FORBIDDEN
SUPERSEDED_STATUS_REFUSES_AUTHORITY = FORBIDDEN
OBSERVED_PREFERRED_TEST             = FORBIDDEN
SUPERSEDED_REFUSAL_TEST             = FORBIDDEN
```

## 4. The superseded case, and why wholesale ratification was blocked

```text
TIME_v0.4 = SUPERSEDED / TIME-11 STATUS CONTRADICTION
TIME-11 v0.4 = CONTRADICTS_B_STRICT      = TRUE
TIME-11 v0.4 = CONTRADICTS_GAP6_ORDERING = TRUE
TIME_v0.5 = RATIFIED
```

v0.4 is **not edited**. Its 14 sound cases are carried verbatim into v0.5; its
TIME-11 is replaced. The governance rule that committed ratified material is
corrected by successor, not by in-place edit, is applied here to a draft as a
matter of consistency.

---

## 5. Consequence

```text
RATIFIED 6E DOCTRINE            = TRUE   (BOOK6-GAP6-v0.2)
RATIFIED 6E FALSIFICATION CASES = 15     (this record)
DRAFT_ONLY 6E CASES             =  0
RUNG_6                         = GREEN
```

The traceability finding that put Rung 6 at AMBER — a ratified doctrine with
zero ratified tests able to fail it — is closed. Rung 6 is now the only rung
whose falsification is ratified *and* status-invariant.

## 6. The pattern this session closes

This is the third time the corpus has found a check that could not fail, and
each instance was the same shape:

```text
1  v0.4 replay checks 4-6   named an object that does not exist
2  review v0.1 delta D3     instructed a status-to-currency mapping that
                            ratified doctrine forbids
3  TIME-11 v0.4             made status the deciding gate, and inverted the
                            ratified ordering while doing it
```

The invariant behind all three is the corpus's own standard:

```text
A CHECK THAT CANNOT FAIL IS NOT A CHECK
A CONTRACT WITH NO RATED FAILING CASE IS NOT A CONTRACT
```

TIME-11 v0.4 was the subtlest of the three, because unlike checks 4-6 it named
a real, existing field and would have failed loudly on any correct
implementation — it was not vacuous, it was **wrong**. A wrong test is worse
than an absent one: it certifies the opposite of the ratified position.

```text
TIME_11_v0.4_WOULD_HAVE_CERTIFIED = THE INVERSE OF B-STRICT
```

## 7. What this record did not do

```text
RATIFIED_ANY_NEW_DOCTRINE     = FALSE
REVISED_B_STRICT              = FALSE
REOPENED_GAP_6                = FALSE
REOPENED_GAP_7                = FALSE
REOPENED_GAP_1..GAP_5         = FALSE
EDITED_v0.4                   = FALSE
EDITED_ANY_RATIFIED_RECORD    = FALSE
EDITED_THE_STATUS_VALIDATOR   = FALSE
AUTHORIZED_IMPLEMENTATION     = FALSE
CREATED_BRANCH_OR_WORKTREE    = FALSE
MUTATED_FROZEN_BOOK6_WORKTREE = FALSE
SOURCE_CHANGED                = FALSE
TEST_CODE_WRITTEN             = FALSE
```

## 8. Residual, recorded not blocking

```text
TERMINALITY_SPECIFICITY_PROVEN_BY_TIME_11_ALONE = FALSE
```

An implementation could satisfy TIME-11 v0.5 by filtering on some property
correlated with terminality rather than terminality itself — for instance,
filtering in registry order and happening to encounter the non-terminal
candidate first. The permutation closes the *status* leak, which was the
defect. A `TIME-16` with the non-terminal candidate lexically **smaller**
would close the rest.

```text
RESIDUAL_IS_A_STRENGTHENING_NOT_A_CORRECTION = TRUE
DOES_NOT_BLOCK_RATIFICATION                   = TRUE
```

## 9. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.5.md      RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_TIME_TEST_PRE_RATIFICATION_REVIEW_v0.1.md  PASS 10/10
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md      SUPERSEDED
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md       6E doctrine
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md B-STRICT
CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md     out of scope
CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.2.md           RUNG 6 GREEN
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```
