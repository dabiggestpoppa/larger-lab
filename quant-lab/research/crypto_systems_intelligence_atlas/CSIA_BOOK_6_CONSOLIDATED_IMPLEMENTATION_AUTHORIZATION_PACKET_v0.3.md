# CSIA — Book 6 Consolidated Implementation Authorization Packet v0.3

**Status:** `AWAITING_OPERATOR_DECISION` — a choice, not a decision.
**Date:** 2026-10-04
**Proposed decision id:** `BOOK6-IMPL-CONSOLIDATED-v0.3`
**Grants implementation authority:** `TRUE` only under Option A
**Precondition satisfied:** consolidated review **v0.3** = `PASS` (12 / 12)

## Supersession

```text
SUPERSEDES_PROSPECTIVELY =
    CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.2.md
SUPERSESSION_REASON = THE SECOND, INDEPENDENT QUESTION IS NOW CLOSED
v0.2_EDITED = FALSE      (left exactly as committed)
```

Packet v0.2 carried two questions. Question 2 — ratify TIME-1..TIME-15 — has
been answered in this round: the cases were audited, TIME-11 was repaired, and
the corrected 6E falsification contract was ratified. Question 1 is therefore
re-put alone, against a review that reports zero known evidence gaps.

```text
QUESTIONS_IN_v0.2 = 2
QUESTIONS_IN_v0.3 = 1
QUESTION_2_ANSWERED = BOOK6-GAP6-TIME-TESTS-v0.1
```

---

## 0. State at the moment of writing — read this first

```text
IMPLEMENTATION HAS NOT BEGUN.
FRESH BRANCH HAS NOT BEEN CREATED.
FRESH WORKTREE HAS NOT BEEN CREATED.
FROZEN BRANCH UNTOUCHED.        (agent/...-book6-build at 5f94c3f40c)
FROZEN WORKTREE UNTOUCHED.      (0 drift)
ACCEPTED ANCHOR PRESERVED.      (3919fb8052 verified ancestor)
STATUS VALIDATOR UNTOUCHED.
```

This packet is a **question**. Answering it changes nothing until the operator
answers.

---

## 1. What is being asked

```text
Authorize offline implementation of the ENTIRE Book 6 amendment?
```

Two options. `HOLD` is a real option, not a formality.

```text
A. AUTHORIZE_OFFLINE_IMPLEMENTATION
B. HOLD
```

## 2. Required scope

```text
1  GAP-7 kernel currentness hardening
2  comparison / change GAP-1..GAP-6
3  the canonical 20-check authority replay
```

## 3. Required explicit prohibitions

These bind any authorized implementation. The first is the correction this
packet exists to carry.

```text
DO_NOT_CHANGE_OBSERVATION_STATUS_AUTHORITY_SEMANTICS
STATUS_VALIDATOR_LIFECYCLE_CLEANUP = OUT_OF_SCOPE
```

Concretely:

```text
RENAME_OBSERVATION_STATUS              = FORBIDDEN
DELETE_OBSERVATION_STATUS              = FORBIDDEN
SUPERSEDED_STATUS_REFUSES_AUTHORITY    = FORBIDDEN
OBSERVED_STATUS_PREFERRED              = FORBIDDEN
STATUS_VALIDATOR_EDIT                  = FORBIDDEN IN THIS AMENDMENT
STATUS_ONLY_CHANGES_CURRENTNESS        = MUST REMAIN FALSE
CURRENTNESS_RESOLVER_USES_STATUS       = MUST REMAIN FALSE
```

The two `FORBIDDEN` lines above the validator are new in v0.3. They are not
stylistic. TIME-11 v0.4 specified precisely these two behaviours as the
expected outcome of a ratified test, and had that test ever been implemented it
would have written a status-to-currency mapping straight into the kernel.
Ratified TIME-11 now forbids the same thing by test.

```text
TIME_11_USES_OBSERVATION_STATUS_AS_AUTHORITY = FALSE
TIME_11_TERMINALITY_AUTHORITY                = TRUE
```

---

### 3.1 Why the refusal is still correct

The `SUPERSEDED` validator at `book6_records.py:202-215` is genuinely
incoherent — it pairs the `SUPERSEDED` status with the **outgoing** edge while
the status names the **incoming** one. That is a real lifecycle defect, and it
is recorded as such in the deferred lifecycle amendment, which poses five
remedies and selects none.

It is provably **not** an authority defect. The validator is construction-time
bookkeeping: it never returns a currency verdict, and no authority path reads
`status`. Currentness is decided by registered lineage terminality.

```text
INCOHERENCE_IS_REAL              = TRUE
INCOHERENCE_IS_AUTHORITY_BEARING = FALSE
REFUSING_THE_REPAIR_IS_CORRECT   = TRUE
```

The tempting repair is the one repair that must be refused. Making a
`SUPERSEDED` record refuse authority would introduce a status-to-currency
mapping the ratified record forbids, and would break `CURR-S1` — which
requires two otherwise identical terminal records differing only in status to
receive the **same** verdict.

---

## 4. Option A — `AUTHORIZE_OFFLINE_IMPLEMENTATION`

### 4.1 What Option A would permit

```text
Creating branch  agent/crypto-systems-intelligence-atlas-book6-comparison-change-build
                 from 5f94c3f40cea4441470c57671f51454da7377361
Creating a fresh worktree for that branch
Writing comparison/change source under the 11-rung order
Writing the ratified GAP-7 39-case and GAP-6 15-case test contracts
Running and committing regression-verified implementation commits
Re-accepting Book 6 under a NEW acceptance commit
```

### 4.2 The GAP-7 work any authorized implementation would perform

Exactly three authority-relevant deltas, plus one explicit non-action:

```text
D1  book6_registry.py:195-216  remove the non-value-bearing early bypass
D2  book6_registry.py:172-191  enforce lineage validity / terminality at the
                                registry, so branching fails closed on WRITE
D3  book6_records.py:202-215   NO STATUS VALIDATOR AUTHORITY CHANGE
D4  8 call sites               inherit the central fix; no consumer workaround
```

```text
STATUS_VALIDATOR_EDIT_REQUIRED   = FALSE
CURRENTNESS_RESOLVER_USES_STATUS = FALSE
```

---

### 4.3 What Option A would NOT permit

```text
Mutating the frozen accepted Book 6 worktree or branch
Implementing on, or deriving from, the planning branch
Changing ObservationStatus authority semantics in any way
Editing the SUPERSEDED validator inside this amendment
Using the historical 19-check replay list
Implementing any reserved selector as a placeholder
Silently aggregating when aggregation == NONE
Inventing a WindowClass conversion or coercion
Opening GAP-1..GAP-7 for any reason
Class C state benchmark implementation
Any Book 7 or Choir work
Any live acquisition
Force-push, rebase, or history rewrite
```

### 4.4 Worktree discipline Option A binds

```text
FRESH_BRANCH_BASE = 5f94c3f40cea4441470c57671f51454da7377361
PRESERVES_ANCHOR  = 3919fb8052e216e94034a753fb258d338c5fa0dc
PLANNING_BRANCH   = UNTOUCHED BY IMPLEMENTATION
FROZEN_WORKTREE   = UNTOUCHED BY IMPLEMENTATION
```

The name was verified collision-free against all remote heads, and again at
this review. It must be re-verified immediately before creation.

## 5. Option B — `HOLD`

Nothing changes. All seven gaps stay CLOSED / RATIFIED, the design stays
complete, the test contracts stay ratified, and implementation stays
unauthorized.

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

`HOLD` remains defensible on the same grounds as before. The one that pointed
at RUNG 6 has been withdrawn — not because the argument was weak, but because
the condition it named has been met.

```text
WANT_A_SECOND_OPINION_ON_THE_REPLAY       (the precedence erratum is recent)
WANT_BOOK_7_SEAM_REVIEWED_FIRST           (the seam was outside review scope)
WANT_TO_BATCH_WITH_OTHER_PROGRAMS        (multi-program sequencing)
WANT_RUNG_6_FALSIFICATION_RATIFIED_FIRST  (SATISFIED 2026-10-04)
```

A fourth is now available and is honest to name: a ratified test contract can
still be a weaker contract. One caveat is recorded rather than buried.

```text
TERMINALITY_SPECIFICITY_PROVEN_BY_TIME_11_ALONE = FALSE
```

TIME-11 as ratified proves that the non-terminal candidate is excluded. It
does not independently prove the exclusion ran through the *terminality* check
rather than some other filter that happens to drop A. A registry-order filter
would pass TIME-11 by accident. The suggested hardening — `TIME-16`, same
fixture with the non-terminal candidate made lexically **smaller** — is
recorded as a strengthening, not a blocker.

```text
KNOWN_EVIDENCE_GAPS = 0        (matrix v0.2)
OPEN_STRENGTHENINGS = 1        (TIME-16, suggested, not required)
```

---

## 6. Regression gates binding any authorized implementation

```text
B1 = 107   B2 = 108   B3 =  83   B4 = 230   B5 = 293   B6 = 1341   TOTAL = 2162
R1 =  93   R2 =  46   R3 =  45

MAY INCREASE  = B6, and therefore TOTAL
MUST NOT MOVE = B1, B2, B3, B4, B5, R1, R2, R3
```

Sensor, pinned and not reopened:

```text
PINNED_TO = 5f94c3f40cea4441470c57671f51454da7377361
2325 passed / 14 failed / 4 skipped / 0 xfailed   (2343 collected)
The 14 are the canonical evidence-matrix set, pinned by identity.
```

```text
BOOK6_TREE_FINGERPRINT_REQUIRED_FOR_AUTHORIZATION = FALSE
```

A baseline manifest is optional hardening for RUNG 11, not a gate. It is not
raised as a blocker here.

---

## 7. The second question — now closed

Packet v0.2 put two independent questions. The second is answered.

```text
QUESTION 1  AUTHORIZE_OFFLINE_IMPLEMENTATION  |  HOLD         <- OPEN, this packet
QUESTION 2  RATIFY TIME-1..TIME-15 as the 6E falsification contract
                                                        <- CLOSED
            = BOOK6-GAP6-TIME-TESTS-v0.1
```

```text
TIME-1..TIME-15                          = RATIFIED
RUNG 6                                    = GREEN
ALL RUNGS                                = GREEN  (11 / 11)
B-STRICT                                 = PRESERVED
STATUS VALIDATOR                         = OUT OF SCOPE

TEST_SPEC_v0.3_CARRIED_CASES = 237
TEST_SPEC_v0.5_TOTAL_CASES    = 252
```

The mechanism by which it was answered matters as much as the answer. TIME-11
in v0.4 was not merely under-specified — it specified the **inverse** of
B-STRICT, and presented it as a ratified-test-shaped gate. No mechanical check
in the corpus would have caught it. Comparison against the ratified record
caught it.

```text
MECHANICAL_CHECKS_THAT_WOULD_HAVE_CAUGHT_IT = 0
DOCTRINE_COMPARISON_CAUGHT_IT               = 1
```

A fourth defect class is now named in the traceability matrix: **A WRONG
TEST**. It is recorded because the next corpus will produce one again, and
because the class has a detection method — read the test against the ratified
record, not just against the code.

---

## 8. Exact next operator action

```text
1. Read   CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3.md
2. Select exactly one:
     BOOK6-IMPL-CONSOLIDATED-v0.3 = AUTHORIZE_OFFLINE_IMPLEMENTATION
                                  | HOLD
```

That is the whole remaining decision. Nothing else is pending.

```text
DECISIONS_OUTSTANDING = 1
```

Until the selection is recorded:

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## 9. Supporting artifacts

```text
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3.md   PASS 12/12
CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.2.md            11 GREEN
CSIA_BOOK_6_COMPARISON_CHANGE_TIME_TEST_RATIFICATION_RECORD_v0.1.md    RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_TIME_TEST_PRE_RATIFICATION_REVIEW_v0.1.md  PASS 10/10
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.5.md        252 cases
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md   RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md         RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md    RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md       RATIFIED
CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md                     PINNED
CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md     OUT OF SCOPE
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.2.md   SUPERSEDED
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.2.md   SUPERSEDED
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md         SUPERSEDED
CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.1.md            SUPERSEDED
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

## 10. Explicit non-actions taken in producing this packet

```text
IMPLEMENTATION_STARTED       = FALSE
SOURCE_FILE_WRITTEN          = FALSE
TEST_FILE_WRITTEN            = FALSE
TEST_CASE_EXECUTED           = FALSE
BRANCH_CREATED               = FALSE
WORKTREE_CREATED             = FALSE
FROZEN_BRANCH_TOUCHED         = FALSE
FROZEN_WORKTREE_TOUCHED       = FALSE
STATUS_VALIDATOR_TOUCHED     = FALSE
OBSERVATION_STATUS_RENAMED   = FALSE
OBSERVATION_STATUS_DELETED   = FALSE
RATIFIED_RECORD_EDITED       = FALSE
PACKET_v0.2_EDITED           = FALSE
REVIEW_v0.2_EDITED           = FALSE
TEST_SPEC_v0.4_EDITED        = FALSE
MATRIX_v0.1_EDITED           = FALSE
GAP_REOPENED                 = FALSE
BOOK_7_WORKED_ON             = FALSE
CHOIR_TOUCHED                = FALSE
```

---

**Status:** `AWAITING_OPERATOR_DECISION`. Nothing has been implemented.
