# CSIA — Book 6 GAP-7 Ratification Anchor Erratum v0.1

**Status:** `ERRATUM` — an anchoring correction, not a new policy decision.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Corrects the anchoring of:** `BOOK6-GAP7-v0.3`

**This artifact does NOT edit**
`CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md`,
and does NOT rewrite or amend `5ac1e0b14`.

---

## 0. The defect, stated precisely

The GAP-7 ratification record, committed at `5ac1e0b14`, names three artifacts
as its evidentiary basis:

```text
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.3.md
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md
CSIA_BOOK_6_GAP7_PRE_RATIFICATION_REVIEW_v0.3.md
```

It cites `TEST_SPEC_v0.3_CASES = 39` and
`PRE_RAT_v0.3 = 15 / 15 PASS` as ratified facts.

At commit `5ac1e0b14`, those three files were **untracked in git**. They existed
only in the working tree. Verified by direct inspection of the index at that
commit.

```text
GAP7_RATIFICATION_DECISION                       = STANDS
GAP7_EVIDENCE_PACKAGE_GIT_ANCHORED_AT_RATIFICATION = FALSE
```

So the decision was recorded correctly, but the evidence it rests on had no
commit of its own to point at.

## 1. Anchor facts

```text
ORIGINAL_RATIFICATION_COMMIT =
    5ac1e0b14ab9ca8981ef017e75b963c2bb6c44f6

ORIGINAL_OPERATOR_DECISION = BOOK6-GAP7-v0.3

ORIGINAL_DECISION_REMAINS_VALID = TRUE

ORIGINAL_EVIDENCE_FILES_WERE_UNCOMMITTED_AT_DECISION_COMMIT = TRUE

GAP7_V03_EVIDENCE_ANCHOR =
    7488010608102bf5d7217c8f473eb8e088a44144
```

## 2. What did not change

```text
RATIFIED_DOCTRINE_CHANGED         = FALSE
RATIFIED_TEST_CONTRACT_CHANGED    = FALSE
RATIFIED_PRE_RAT_RESULT_CHANGED   = FALSE
RATIFIED_NV_POLICY_CHANGED        = FALSE
RATIFIED_STATUS_DIRECTION_CHANGED = FALSE
RATIFIED_KERNEL_SHAPE_CHANGED     = FALSE

GAP_7                            = RATIFIED / CLOSED
GAP_7_RESOLUTION                 = 7A-KERNEL + B-STRICT + NV-B
TEST_SPEC_v0.3_CASES             = 39
PRE_RAT_v0.3                     = 15 / 15 PASS
```

The anchor commit `748801060` adds the three evidence artifacts with content
**identical to what was cited at ratification time**. It does not revise them.
Had the content differed, the ratification would have needed reopening; it does
not.

## 3. What this erratum is, and is not

```text
THIS_ERRATUM_IS_A_NEW_POLICY_DECISION = FALSE
THIS_ERRATUM_REOPENS_GAP_7            = FALSE
THIS_ERRATUM_CHANGES_ANY_DOCTRINE     = FALSE
THIS_ERRATUM_AMENDS_5ac1e0b14         = FALSE
```

It is a **provenance repair**: the ratified doctrine now points at a commit that
contains its evidence. The ratification stands exactly as recorded.

No claim is made anywhere that the evidence was historically committed at
`5ac1e0b14`. It was not. This erratum records the true timeline:

```text
5ac1e0b14  ratification decision recorded; evidence files still untracked
748801060  evidence package committed and pushed (this repair)
```

## 4. Corrected state

```text
GAP7_RATIFICATION                        = STANDS
GAP7_ORIGINAL_DECISION_COMMIT            = 5ac1e0b14ab9ca8981ef017e75b963c2bb6c44f6
GAP7_EVIDENCE_PACKAGE_ANCHOR             = 7488010608102bf5d7217c8f473eb8e088a44144
EVIDENCE_ANCHOR_ERRATUM                  = v0.1
NO_RETROACTIVE_CONTENT_CHANGE            = TRUE

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
GAP_6_RATIFICATION              = NOT TAKEN UP
```
