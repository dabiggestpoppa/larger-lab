# CSIA — BOOK 7 PLAN v0.2 GOVERNANCE ERRATUM — v0.1

> **Status:** APPEND-ONLY GOVERNANCE CORRECTION. Decides nothing; ratifies
> nothing. Supersedes no architecture.
> **Date:** 2026-10-01
> **Corrects:** `CSIA_BOOK_7_NARRATIVE_EVENTS_ECOSYSTEM_EVOLUTION_PLAN_v0.2.md`
> line 180 (historical draft, preserved unmodified).
> **Authoritative already at the time of the defect:**
> `CSIA_BOOK_7_DECISION_READINESS_REVIEW_v0.1.md` (lines 44–45) and
> `CSIA_PLANNING_PROGRESS.md` (lines 1680–1682).

---

## 1. The defect

`CSIA_BOOK_7_NARRATIVE_EVENTS_ECOSYSTEM_EVOLUTION_PLAN_v0.2.md` §11 states:

```text
OPEN_BLOCKING_D7N_DECISIONS = 0 (all 7 classified; see Decision Readiness v0.1)
```

The parenthetical defers to the Decision Readiness review — and that review
disagrees with the number printed beside it. The two authoritative planning
records were already correct:

| Record | Line | Stated value |
|---|---|---|
| `CSIA_BOOK_7_DECISION_READINESS_REVIEW_v0.1.md` | 44 | `OPEN_BLOCKING_D7N_DECISIONS = 2 (D7N-3, D7N-7)` |
| `CSIA_BOOK_7_DECISION_READINESS_REVIEW_v0.1.md` | 45 | `OPEN_DEFERRED_D7N_DECISIONS = 5 (D7N-1, D7N-2, D7N-4, D7N-5, D7N-6)` |
| `CSIA_PLANNING_PROGRESS.md` | 1680–1682 | same 2 / 5 split |

The plan's own summary line is therefore an internal self-contradiction: it
points at a record that refutes it. This is a **governance-record
inconsistency**, not an architectural defect.

## 2. The correction

```text
incorrect historical field:  OPEN_BLOCKING_D7N_DECISIONS = 0
correct field:                OPEN_BLOCKING_D7N_DECISIONS = 2
blocking decisions:           D7N-3 (narrative/evolution state governance)
                              D7N-7 (change-comparison authority)
```

The historical plan v0.2 line 180 is **not edited**. It remains as written, as
the record of what the draft claimed. This erratum is the correction of record.

## 3. Why the wrong value was wrong

`0` is reachable only by a specific and illegitimate inference: *all seven
decisions were classified, therefore none is blocking.* Classification and
resolution are different acts. Classification assigned two of them to the
**blocking** class — meaning plan ratification could not proceed until the
operator answered them. A classification pass does not answer a decision.

The correct reading is: seven decisions surfaced, seven classified, **two
blocking and unanswered**, five deferred. Book 7 ratification was therefore
blocked at the moment plan v0.2 was written — which is exactly what the
plan's own status line (`DRAFT_PENDING_OPERATOR_RATIFICATION`) and the
pre-ratification review's framing already implied.

## 4. What this erratum does NOT change

- **No architecture changed.** No object, contract, field, seam, or boundary
  added, removed, or altered. The classification taxonomy that produced the
  correct count is untouched.
- **No pre-ratification test result changed.** All 45 questions in
  `CSIA_BOOK_7_PRE_RATIFICATION_REVIEW_v0.2.md` remain `PASS` as originally
  written. Several of those questions (notably Q31, Q32, Q34, Q35) assume
  unresolved ownership is surfaced rather than assumed — the corrected count
  *strengthens* those answers, it does not change them.
- **The decision-readiness review was already correct.** No amendment to
  `CSIA_BOOK_7_DECISION_READINESS_REVIEW_v0.1.md` is required or made.
- **The planning ledger was already correct.** No amendment to any earlier
  `CSIA_PLANNING_PROGRESS.md` checkpoint is required or made.
- **Plan v0.2 remains a historical draft.** Status unchanged:
  `DRAFT_PENDING_OPERATOR_RATIFICATION`. It was never ratified, and it is
  still not ratified at the time of this erratum.
- **No ratification occurred under the incorrect field.** No operator ballot
  was recorded, no decision closed, and no authority granted while the
  `= 0` line stood. The operator's subsequent D7N-3/D7N-7 selections were
  recorded against the correct `= 2` count.

## 5. Why not edit the plan in place

Editing a historical governance artifact in place destroys the audit trail
that makes the governance program verifiable: it would leave no record that
the inconsistency ever existed, and it would silently make the plan's own
line agree with a fact it did not agree with when written. The constitution's
append-only discipline for ledger and decision records applies here by the
same reasoning. Correction is by superseding record, never by silent
rewriting.

## 6. State after this erratum

```text
BOOK_7_PLAN_v0.1                        = SUPERSEDED / NOT RATIFIABLE
BOOK_7_PLAN_v0.2                        = HISTORICAL DRAFT
BOOK_7_PLAN_v0.2_BLOCKING_COUNT_AS_WRITTEN = 0   (defective, superseded)
BOOK_7_PLAN_v0.2_BLOCKING_COUNT_CORRECT   = 2   (D7N-3, D7N-7)
OPEN_BLOCKING_D7N_DECISIONS             = 2   (at time of erratum)
DECISION_READINESS_REVIEW_v0.1           = ALREADY CORRECT — UNCHANGED
PLANNING_LEDGER_PRIOR_CHECKPOINTS        = ALREADY CORRECT — UNCHANGED
RATIFICATIONS_PERFORMED_UNDER_WRONG_FIELD = 0
BOOK_7_RATIFIED                         = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY         = FALSE
```

---

*End of erratum. The plan v0.2 document is unmodified; this file is the
correction of record.*
