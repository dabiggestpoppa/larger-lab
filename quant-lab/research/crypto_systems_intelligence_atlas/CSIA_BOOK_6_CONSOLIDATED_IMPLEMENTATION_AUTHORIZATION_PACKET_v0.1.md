# CSIA — Book 6 Consolidated Implementation Authorization Packet v0.1

**Status:** `AWAITING_OPERATOR_DECISION` — a choice, not a decision.
**Date:** 2026-10-04
**Proposed decision id:** `BOOK6-IMPL-CONSOLIDATED-v0.1` (collision-free; unused
prefix, does not reuse `BOOK6-COMPARE-*`, `BOOK6-GAP6-*`, `BOOK6-GAP7-*`,
`D6M-*` or `D7N-*` namespaces)
**Grants implementation authority:** `TRUE` only under Option A
**Precondition satisfied:** consolidated review v0.1 = `PASS` (12 / 12)

---

## 0. State at the moment of writing — read this first

```text
IMPLEMENTATION HAS NOT BEGUN.          <-- no source file was written
FRESH BRANCH HAS NOT BEEN CREATED.      <-- not created, not pushed
FRESH WORKTREE HAS NOT BEEN CREATED.    <-- not created
FROZEN BRANCH UNTOUCHED.                <-- agent/...-book6-build still at 5f94c3f40c
FROZEN WORKTREE UNTOUCHED.              <-- 0 drift, verified this session
ACCEPTED ANCHOR PRESERVED.              <-- 3919fb8052 verified ancestor
```

This packet is a **question**. Answering it changes nothing until the operator
answers.

---

## 1. What is being asked

The operator is asked **one** question:

```text
Authorize offline implementation of the ENTIRE Book 6 amendment
(GAP-7 hardening + comparison/change GAP-1..6 + canonical 20-check replay)?
```

Two options. `HOLD` is a real option, not a formality.

```text
A. AUTHORIZE_OFFLINE_IMPLEMENTATION
B. HOLD
```

## 2. What the operator is NOT being asked

```text
NOT asked: to ratify anything (GAP-1..GAP-7 are all CLOSED / RATIFIED)
NOT asked: to ratify GAP-6 again (BOOK6-GAP6-v0.2, this session)
NOT asked: to ratify GAP-7 again (BOOK6-GAP7-v0.3)
NOT asked: to re-open the Class C state benchmark (UNRATIFIED / UNIMPLEMENTED)
NOT asked: to choose a baseline selector (exactly one is executable, ratified)
NOT asked: to choose delta semantics, direction, or zero-baseline behaviour
NOT asked: to choose a coverage rule (none is ratified; presence-derived)
NOT asked: to decide D6M items (0 closed, 0 changed by GAP-6)
NOT asked: to authorize Book 7 or live acquisition
```

---

## 3. Why the question is being asked now

Three things changed this session, and together they are why the consolidated
question can now be put:

```text
1. GAP-6 is CLOSED / RATIFIED      -> no open comparison/change gap remains
2. Replay precedence is settled    -> one canonical 20-check list, not two
3. The readiness criterion is fixed-> implementability, not "is it written yet"
```

Under the corrected criterion, the consolidated review scored **12 / 12 TRUE**:

```text
NO_UNRATIFIED_POLICY_NEEDED            = TRUE
NO_AUTHORITY_DESIGN_GAP                 = TRUE
GAP7_IMPLEMENTATION_CONTRACT_COMPLETE   = TRUE
COMPARISON_CONTRACT_COMPLETE            = TRUE
GAP6_ORDERING_CONTRACT_COMPLETE         = TRUE
CANONICAL_20_CHECK_REPLAY_UNAMBIGUOUS   = TRUE
TEST_CONTRACT_COMPLETE                  = TRUE
IMPLEMENTATION_ORDER_COMPLETE           = TRUE
FRESH_BRANCH_STRATEGY_VALID             = TRUE
UPSTREAM_FREEZE_PRESERVABLE             = TRUE
BOOK1_5_FREEZE_PRESERVABLE              = TRUE
SENSOR_FREEZE_PRESERVABLE               = TRUE
```

Evidence:
`CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md`.

---

## 4. Option A — `AUTHORIZE_OFFLINE_IMPLEMENTATION`

Authorizes a single, offline, governance-contained implementation effort on a
fresh branch.

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

### 4.2 What Option A would NOT permit

```text
Mutating the frozen accepted Book 6 worktree or branch
Implementing on the planning branch, or deriving from it
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

### 4.3 The worktree discipline Option A binds

```text
FRESH_BRANCH_BASE = 5f94c3f40cea4441470c57671f51454da7377361
PRESERVES_ANCHOR  = 3919fb8052e216e94034a753fb258d338c5fa0dc
PLANNING_BRANCH   = UNTOUCHED BY IMPLEMENTATION
FROZEN_WORKTREE   = UNTOUCHED BY IMPLEMENTATION
```

The name is verified collision-free against all 42 remote heads as of this
session. It must be re-verified immediately before creation, because a branch
may appear in the interim.

---

## 5. Option B — `HOLD`

Nothing changes. All seven gaps stay CLOSED / RATIFIED, the design stays
complete, and the implementation stays unauthorized.

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

`HOLD` is defensible on several grounds, and this packet does not argue against
any of them:

```text
PREFER_RATIFY_AFTER_IMPLEMENTATION  -- though GAP-6 is now ratified, so this
                                       rationale is spent
WANT_A_SECOND_OPINION_ON_THE_REPLAY  -- the precedence erratum is recent
WANT_BOOK_7_SEAM_REVIEWED_FIRST      -- the Book 6 -> Book 7 seam is specified
                                       but was not in the review scope
WANT_TO_BATCH_WITH_OTHER_PROGRAMS   -- multi-program sequencing preference
```

The last two are the substantive ones. If either is the real reason, saying so
explicitly is better than defaulting to a hold that looks like a design
problem.

---

## 6. Comparison of options

| | A — authorize offline implementation | B — hold |
|---|---|---|
| closes any gap | no (all closed) | no |
| changes accepted source | yes, on a fresh branch | no |
| requires new policy choice | no | no |
| Book 6 design status after | complete | complete |
| Book 6 implementation status after | implemented | unimplemented |
| Book 7 unblocked | yes, after re-acceptance | no |
| reversible | yes, branch is disposable | n/a |
| risk if wrong | a fresh branch is discarded | delay only |
| risk of doing nothing | Book 7 stays blocked | none immediate |

The asymmetry favours A: an implementation on a disposable fresh branch can be
thrown away at no cost, whereas the `BASELINE_UNAVAILABLE`, NV-B and replay
semantics will remain unexercised by real tests for as long as the hold lasts.
But the decision is the operator's, and this packet records rather than decides.

---

## 7. Regression gates binding any authorized implementation

Independently re-verified this session at `5f94c3f40c`, read-only:

```text
B1 = 107    EXACT      B5 =  293   EXACT
B2 = 108    EXACT      B6 = 1341   EXACT
B3 =  83    EXACT      TOTAL = 2162 EXACT
B4 = 230    EXACT      R1 = 93, R2 = 46, R3 = 45   EXACT
```

```text
MAY INCREASE  = B6, and therefore TOTAL
MUST NOT MOVE = B1, B2, B3, B4, B5, R1, R2, R3
MUST NOT TOUCH = any sensor source or test
```

A decrease is a regression, not a progress report.

```text
SENSOR_BASELINE_REPINNED_TO_A_NAMED_COMMIT = TRUE
SENSOR_BASELINE_PINNED_TO = 5f94c3f40cea4441470c57671f51454da7377361
```

The sensor baseline is now pinned to a named commit and was re-run during
review: **2325 passed / 14 failed / 4 skipped**, exactly as recorded. The 14 are
failures, not xfails — the corpus wording was "2325 PASS / 14 FAIL / 4 SKIPPED"
and an xfail reading would have produced a freeze gate that cannot fail.

Note the framing, corrected during review: this is a **CSIA-lineage**
measurement. The sensor programme's own branch tip now collects 3353 tests, and
the two sensor worktrees collect 2850 and 3353. Neither is the reference point.
The reference point is the CSIA lineage, which collects exactly 2343 on both the
planning and Book 6 build branches. See
`CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md` for the pin, the 14
failures named individually, and the tree fingerprints that verify the freeze
in about a second without running pytest.

---

## 8. Exact next operator action

```text
1. Read   CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md
2. Select exactly one:
     BOOK6-IMPL-CONSOLIDATED-v0.1 = AUTHORIZE_OFFLINE_IMPLEMENTATION
                                   | HOLD
3. If HOLD: nothing further is needed; the state below stands unchanged.
   If AUTHORIZE: a fresh branch is created from 5f94c3f40c, and the 11-rung
   order is executed under regression gates.
```

Until that selection is recorded:

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 9. Supporting artifacts

```text
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md   PASS 12/12
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PREVIEW_v0.1.md  (scope preview)
CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md                 PINNED
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md          RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md        RATIFIED
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md   RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md     RATIFIED
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

## 10. Explicit non-actions taken in producing this packet

```text
IMPLEMENTATION_STARTED         = FALSE
SOURCE_FILE_WRITTEN            = FALSE
TEST_FILE_WRITTEN              = FALSE
BRANCH_CREATED                 = FALSE
WORKTREE_CREATED               = FALSE
FROZEN_BRANCH_TOUCHED           = FALSE
FROZEN_WORKTREE_TOUCHED         = FALSE
ACCEPTED_ANCHOR_MOVED           = FALSE
RATIFIED_RECORD_EDITED          = FALSE
RATIFIED_GAP_REOPENED           = FALSE
BOOK_7_WORKED_ON                = FALSE
CHOIR_TOUCHED                   = FALSE   (md5 8ddc60567c0e758564168f583cc2df48 unchanged)
```
