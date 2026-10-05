# CSIA — Book 6 GAP-7 Test Contract Precedence Ratification Record v0.1

**Status:** `RATIFIED`
**Record type:** formal governance ratification record
**Date:** 2026-10-05
**Decision id:** `BOOK6-GAP7-TEST-PRECEDENCE-v0.1`
**Operator selection:** `RATIFY_TERM6_PER_RECORD_AS_CANONICAL_AND_SUPERSEDE_COMPONENT_WIDE_CARR21`
**Scope:** `BOOK 6 TEST CONTRACT PRECEDENCE ONLY`
**Grants implementation authority:** `FALSE` (already held; unchanged)

**Precondition satisfied:**
`CSIA_BOOK_6_GAP7_TEST_CONTRACT_PRECEDENCE_REVIEW_v0.1.md`
= `10 / 10 PASS`, `BLOCKING = 0`.

---

## 0. What this record is, and what it is not

This record ratifies a **bookkeeping precedence**. It selects nothing new and
permits nothing new.

```text
RATIFIES   = WHICH CARRIED CASE ROW IS CANONICAL ON THE BRANCHED-FAMILY SCOPE
IMPLEMENTS = NOTHING
CHANGES ANY ACCEPTED SOURCE   = FALSE
DOCTRINE_CHANGED              = FALSE
IMPLEMENTATION_SCOPE_CHANGED  = FALSE
```

The substantive policy — `PER_RECORD` — was selected earlier, at
`BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1`. This record does not revisit it,
reopen it, or re-derive it. It applies it to one row the corpus had not yet
updated.

---

## 1. The decision

```text
CARR_21_COMPONENT_WIDE = HISTORICAL / SUPERSEDED
TERM_6_PER_RECORD      = CURRENT / RATIFIED

SUCCESSOR_CURRENTNESS_SCOPE = PER_RECORD
COMPONENT_WIDE_FAIL_CLOSED  = NOT ADOPTED

DOCTRINE_CHANGED             = FALSE
IMPLEMENTATION_SCOPE_CHANGED = FALSE

BOOK_6_IMPLEMENTATION_AUTHORITY = REMAINS TRUE
```

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (OFFLINE AMENDMENT SCOPE ONLY,
                                         unchanged by this record)
```

---

## 2. Why a precedence record was needed at all

No doctrine was in conflict. Only the corpus's record of itself was.

`CARR-21` demanded that `A`, `B` and `C` **all** refuse. `TERM-6` demands that
`B` and `C` resolve on their own conjuncts. Both were reachable from the
ratified corpus, and both claimed the same scenario. An implementer reading the
carried set would have found a ratification telling them to refuse the whole
family, and a later ratification telling them not to.

```text
CORPUS_PRECEDENCE_CLEANUP_REQUIRED = TRUE
CONTRADICTION_WAS_OF_TWO_KINDS
    = A STALE CARRIED ROW AGAINST A LATER RATIFICATION
    = NOT A SOURCE-CODE DEFECT
    = NOT A NEW POLICY QUESTION
```

The operator had already settled the underlying question. What was missing was a
ratified statement of which row governs.

---

## 3. The precedence rule applied

The corpus has a settled ordering principle, stated in the successor record §3.2
and inherited from the NV-B precedent:

```text
A RULE IS NOT DOCTRINE UNLESS A RATIFICATION ADOPTED IT
```

`CARR-21`'s outcome entered the ratified contract by **carriage** — v0.3
declared 19 cases carried unchanged, and `BOOK6-GAP7-v0.3` ratified that set.
`TERM-6` entered by **explicit adoption** — a later ratification naming it, with
its own decision id and its own required outcome.

```text
CARRIED_FROM_DRAFT       = LOWER PRECEDENCE
EXPLICITLY_ADOPTED_LATER = CONTROLS
LATER_RATIFICATION_CONTROLS = TRUE
```

This record codifies that ordering for this case. It is a **confirmation**, in
the same sense the successor record §3.3 was — the outcome is unchanged; only
its status as settled, citable ground is now established.

---

## 4. The canonical branched-family requirement

```text
TERM-4 | A <- B and A <- C | A NOT CURRENT (lineage invalid)
TERM-6 | A <- B and A <- C | B CURRENT iff B's own five conjuncts pass
                         | C CURRENT iff C's own five conjuncts pass
```

```text
resolve_current("A")      -> REFUSE (LINEAGE_INVALID)
resolve_current("B")      -> RETURNS B
resolve_current("C")      -> RETURNS C
is_authoritative_now("A") -> FALSE
is_authoritative_now("B") -> TRUE
is_authoritative_now("C") -> TRUE
```

`TERM-4` and `TERM-6` are **retained together**. They are paired negatives, not
duplicates: `TERM-4` forbids under-refusing `A`, `TERM-6` forbids over-refusing
`B` and `C`. Between them they pin the scope from both sides.

```text
TERM_4_STATUS = CURRENT / RATIFIED
TERM_6_STATUS = CURRENT / RATIFIED
LIVE_REQUIREMENTS_ON_THIS_SCENARIO = 2   (one per side)
SUPERSEDED_REQUIREMENTS_ON_THIS_SCENARIO = 1   (CARR-21)
```

### 4.1 What this forbids

```text
REFUSING_B_OR_C_BECAUSE_THEY_SHARE_A_PREDECESSOR = PROHIBITED
REFUSING_B_OR_C_BECAUSE_A_IS_BRANCHED           = PROHIBITED
COMPONENT_WIDE_FAIL_CLOSED_IMPLEMENTED           = PROHIBITED
REFUSAL_REASON_READS_A_PREDECESSOR               = NONE
```

### 4.2 What this does not touch

```text
A_FAILS_CLOSED                     = UNCHANGED (TERM-4)
REGISTRATION_ACCEPTS_B_AND_C       = UNCHANGED ACCEPTED
WRITE_TIME_BRANCH_REJECTION        = NOT AUTHORIZED
STATUS_BASED_REFUSAL               = FORBIDDEN (B-STRICT)
FAIL_CLOSED_SCOPE_NARROWED         = TO THE RECORD'S OWN LINEAGE
RESOLVER_ORDER                     = UNCHANGED (v0.3 §2, steps 1..8)
```

---

## 5. Historical provenance preserved

Recorded so the corpus is not quietly tidied:

```text
CARR_21_OLD_REQUIREMENT = A, B AND C ALL REFUSE  (component-wide)
CARR_21_WAS_FALSE       = FALSE      (it was never wrong when written)
CARR_21_IS_CURRENT      = FALSE      (it is no longer current)
```

The lineage is recorded end to end:

```text
v0.2  CURR-21 states the component-wide outcome          [DRAFT, never ratified]
v0.3  declares 19 cases carried unchanged               [DRAFT]
GAP7  ratifies TEST_SPEC=v0.3, CASES=39                  [RATIFIED  BOOK6-GAP7-v0.3]
SUC   ratifies PER_RECORD, declines COMPONENT_WIDE,
      adds TERM-6                                        [RATIFIED  ...-v0.1]
v0.4  prospectively supersedes the component-wide row    [DRAFT -> ratified here]
```

```text
HISTORY_DELETED                          = FALSE
UNRELATED_CASES_RENUMBERED               = FALSE
OLD_ROW_REINTERPRETED                    = FALSE
OLD_ROW_CLAIMED_TO_HAVE_MEANT_PER_RECORD = FALSE
V0.2_ITSELF_WAS_RATIFIED                  = FALSE   (recorded, not overstated)
CARR_21_ENTERED_VIA_CARRIAGE              = TRUE
```

The old row is recorded as what it said. It is retired on the single point a
later ratification overtook it, and on no other.

---

## 6. Canonical case accounting

```text
CARR-1..CARR-19      19
CURR-S1..CURR-S3      3
TERM-1..TERM-6        6
NV-1..NV-10          10
STRUCT-1..STRUCT-2    2
                   ----
GAP7_CURRENT_TEST_CONTRACT = 40
```

Two findings recorded at ratification, neither blocking:

**6.1 `CARR-21` is not a ratified case-id.** Across the corpus the only
individual `CARR-<n>` ids that ever appear are `CARR-1` and `CARR-19`, both as
range endpoints. v0.2 and the audit source use the `CURR-*` namespace and
contain zero `CARR-` occurrences. The stale outcome was carried as *content*
inside the lossy `CARR-1..CARR-19` relabeling, whose correspondence to the v0.2
`CURR-*` labels was never recorded.

```text
SUPERSESSION_LEVEL = REQUIREMENT, NOT CASE_ID
CANONICAL_CASE_COUNT_UNCHANGED = 40
RATIFIED_39_FIGURE_STALE       = FALSE   (it was correct for v0.3)
```

This is why the count does not fall to 39. Forcing a 39 would require inventing
a mapping the corpus never recorded and would disagree with the
implementation's own 40-case inventory assertion.

**6.2 v0.3's carried-set gloss does not add up.** *"(CURR-1..15 less CURR-7,
plus CURR-16..23 less CURR-24)"* enumerates 22 labels against a declared 19.
The operative figure is 19 and reconciles against the ratified total
(`19 + 3 + 5 + 10 + 2 = 39`); the gloss is non-governing shorthand.

```text
LABELLING_DEFECTS_RECORDED = 2
BLOCKING                    = 0
```

---

## 7. Implementation standing — no rework

```text
RUNG_3_REWORK_REQUIRED = FALSE
RUNG_3_IMPLEMENTATION  = ALREADY COMPLIANT
```

Verified behaviourally at `f705007ea`, not inferred from test names:

```text
A -> REFUSE (LINEAGE_INVALID)   B -> RETURNS B   C -> RETURNS C
A.auth = False                  B.auth = True    C.auth = True
NO_COMPONENT_WIDE_REFUSAL_PRESENT = TRUE
```

The implementation never asserted the component-wide outcome, so nothing has to
be unwound. Its `TERM-6` test already carries a note that `CARR-21`'s older
outcome is superseded on this point — that note is **correct and remains**. This
record confirms it; it does not replace it.

```text
IMPLEMENTATION_TRACEABILITY_EDITED_SOLELY_TO_REWRITE_HISTORY = FALSE
IMPLEMENTATION_TERM_6_ROW_REMAINS_THE_ACTIVE_FALSIFIER       = TRUE
```

---

## 8. What this record does not do

```text
NEW_CURRENTNESS_POLICY        = FALSE
SOURCE_FILE_WRITTEN           = FALSE
SOURCE_FILE_EDITED            = FALSE
TEST_CODE_WRITTEN             = FALSE
STATUS_VALIDATOR_TOUCHED      = FALSE
LIFECYCLE_REMEDY_APPLIED      = FALSE
REGISTRATION_POLICY_CHANGED   = FALSE
STATUS_ONLY_CHANGES_CURRENTNESS = FALSE   (B-STRICT intact)
CASE_RENUMBERING              = FALSE
HISTORY_DELETED               = FALSE
GAP_7_REOPENED                = FALSE
GAP_6_REOPENED                = FALSE
PRIOR_RATIFICATION_EDITED     = FALSE
TEST_SPEC_v0.3_EDITED         = FALSE
RUNG_1_TO_RUNG_3_COMMITS_EDITED = FALSE
BRANCH_REWRITTEN_OR_REBASED   = FALSE
FROZEN_BOOK_6_WORKTREE_MUTATED = FALSE
BOOK_7_WORKED_ON              = FALSE
CHOIR_TOUCHED                 = FALSE
LIVE_ACQUISITION              = FALSE
```

---

## 9. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (REMAINS TRUE — offline amendment
                                         scope only, BOOK6-IMPL-CONSOLIDATED-v0.4)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
BOOK_6_IMPLEMENTED             = FALSE   (Rung 4 pending)
```

The authorization is **not re-issued** and **not suspended**. This record
constrains the implementation further and grants it nothing.

```text
AUTHORIZATION_REISSUED_REQUIRED = FALSE
AUTHORIZED_SCOPE_CHANGED        = FALSE
IMPLEMENTATION_NOW_FURTHER_CONSTRAINED = TRUE
```

---

## 10. Cross-references

```text
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.2.md                 CURR-21 source
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md                 carried set; TERM-1..5
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.4.md                 canonical successor
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md       CASES = 39
CSIA_BOOK_6_GAP7_SUCCESSOR_CURRENTNESS_RATIFICATION_RECORD_v0.1.md         PER_RECORD; TERM-6
CSIA_BOOK_6_GAP7_TEST_CONTRACT_PRECEDENCE_REVIEW_v0.1.md                   10 / 10 PASS
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.4.md       implementation authority
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

---

**Status:** `RATIFIED`. The corpus now agrees with itself. Nothing was built.