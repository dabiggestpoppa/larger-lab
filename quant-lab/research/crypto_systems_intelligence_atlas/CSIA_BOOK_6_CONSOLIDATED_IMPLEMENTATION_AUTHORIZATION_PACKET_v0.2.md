# CSIA — Book 6 Consolidated Implementation Authorization Packet v0.2

**Status:** `AWAITING_OPERATOR_DECISION` — a choice, not a decision.
**Date:** 2026-10-04
**Proposed decision id:** `BOOK6-IMPL-CONSOLIDATED-v0.2`
**Grants implementation authority:** `TRUE` only under Option A
**Precondition satisfied:** consolidated review **v0.2** = `PASS` (12 / 12)

## Supersession

```text
SUPERSEDES_PROSPECTIVELY =
    CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.1.md
SUPERSESSION_REASON = INHERITED THE REVIEW_v0.1 GAP-7 STATUS CONTRADICTION
v0.1_EDITED = FALSE      (left exactly as committed)
```

Packet v0.1 asked the right question against a review that carried one
self-contradictory instruction. Review v0.2 removes it. The question is
therefore re-put against a sound review.

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
STATUS_VALIDATOR_EDIT                  = FORBIDDEN IN THIS AMENDMENT
STATUS_ONLY_CHANGES_CURRENTNESS        = MUST REMAIN FALSE
CURRENTNESS_RESOLVER_USES_STATUS       = MUST REMAIN FALSE
```

### 3.1 Why this prohibition is load-bearing

The `SUPERSEDED` validator at `book6_records.py:202-215` is genuinely
incoherent — it pairs the `SUPERSEDED` status with the **outgoing** edge while
the status names the **incoming** one. That is a real lifecycle defect.

It is also, provably, **not** an authority defect: the validator is
construction-time bookkeeping, it never returns a currency verdict, and no
authority path reads `status`. Currentness is decided by registered lineage
terminality, per the ratified record.

So the tempting repair is the one repair that must be refused. Making a
`SUPERSEDED` record refuse authority would introduce a status-to-currency
mapping the ratified record forbids, and would break `CURR-S1` — which
requires two otherwise identical terminal records differing only in status to
receive the **same** verdict.

```text
INCOHERENCE_IS_REAL            = TRUE
INCOHERENCE_IS_AUTHORITY_BEARING = FALSE
REFUSING_THE_REPAIR_IS_CORRECT = TRUE
```

---

## 4. Option A — `AUTHORIZE_OFFLINE_IMPLEMENTATION`

### 4.1 What Option A would permit

```text
Creating branch  agent/crypto-systems-intelligence-atlas-book6-comparison-change-build
                 from 5f94c3f40cea4441470c57671f51454da7377361
Creating a fresh worktree for that branch
Writing comparison/change source under the 11-rung order
Writing the GAP-7 39-case test contract
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
complete, and implementation stays unauthorized.

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

`HOLD` remains defensible on the same grounds as before, plus one new:

```text
WANT_A_SECOND_OPINION_ON_THE_REPLAY       (the precedence erratum is recent)
WANT_BOOK_7_SEAM_REVIEWED_FIRST           (the seam was outside review scope)
WANT_TO_BATCH_WITH_OTHER_PROGRAMS        (multi-program sequencing)
WANT_RUNG_6_FALSIFICATION_RATIFIED_FIRST  (new: see section 7)
```

The last is the strongest of these, and it is a sequencing preference rather
than a design problem. Saying so explicitly is better than defaulting to a hold
that looks like a defect.

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

## 7. A second, independent question (carried, not created by this review)

```text
QUESTION 1  AUTHORIZE_OFFLINE_IMPLEMENTATION  |  HOLD
QUESTION 2  RATIFY TIME-1..TIME-15 as the 6E falsification contract  |  PROCEED
```

Rung 6's 6E falsification cases remain draft. This was surfaced by the
traceability matrix and is unchanged by review v0.2.

```text
RATIFY  -> test spec v0.4 ratified at 252 cases; Rung 6 AMBER -> GREEN
PROCEED -> 6E implements with zero ratified tests able to falsify it
```

The two questions are independent. Neither answer grants implementation
authority.

## 8. Exact next operator action

```text
1. Read   CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.2.md
2. Select exactly one:
     BOOK6-IMPL-CONSOLIDATED-v0.2 = AUTHORIZE_OFFLINE_IMPLEMENTATION
                                   | HOLD
3. Optionally, and independently:
     RATIFY TIME-1..TIME-15  |  PROCEED WITHOUT THEM
```

Until those selections are recorded:

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## 9. Supporting artifacts

```text
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.2.md   PASS 12/12
CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.1.md            RUNG 6 AMBER
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md        RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md   RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md      RATIFIED
CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md                    PINNED
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md  SUPERSEDED
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.1.md  SUPERSEDED
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

## 10. Explicit non-actions taken in producing this packet

```text
IMPLEMENTATION_STARTED       = FALSE
SOURCE_FILE_WRITTEN          = FALSE
TEST_FILE_WRITTEN            = FALSE
BRANCH_CREATED               = FALSE
WORKTREE_CREATED             = FALSE
FROZEN_BRANCH_TOUCHED         = FALSE
FROZEN_WORKTREE_TOUCHED       = FALSE
STATUS_VALIDATOR_TOUCHED     = FALSE
OBSERVATION_STATUS_RENAMED   = FALSE
OBSERVATION_STATUS_DELETED   = FALSE
RATIFIED_RECORD_EDITED       = FALSE
PACKET_v0.1_EDITED           = FALSE
BOOK_7_WORKED_ON             = FALSE
CHOIR_TOUCHED                = FALSE
```
