# CSIA — Book 6 GAP-7 Measurement Currentness Test Spec v0.4

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — specification only.
**Date:** 2026-10-05
**Decision id:** none yet. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Amends implementation scope:** `FALSE`
**Changes accepted source:** `FALSE`

**Supersedes:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md`
(39 cases), which superseded v0.2 (27 cases), which superseded v0.1 (24 cases).

**Predecessor ratification:** `BOOK6-GAP7-v0.3` ratified `TEST_SPEC =
..._v0.3.md`, `CASES = 39`.

**Later ratification folded in here:** `BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1`,
which ratified `SUCCESSOR_CURRENTNESS_SCOPE = PER_RECORD`, declined
`COMPONENT_WIDE_FAIL_CLOSED`, and added `TERM-6`.

```text
CANONICAL_RATIFIED_CASES = 40
SUPERSEDED_REQUIREMENTS  =  1   (CARR-21, the v0.2 component-wide outcome)
IMPLEMENTED              = 40
BLOCKED                  =  0
```

---

## 0. What this artifact is, and what it is not

This is a **corpus-precedence cleanup**. It changes no doctrine, no
implementation, no scope, and no authority.

```text
RATIFIES   = NOTHING BY ITSELF (it is DRAFT until the ratification record)
IMPLEMENTS = NOTHING
CHANGES ANY ACCEPTED SOURCE   = FALSE
DOCTRINE_CHANGED              = FALSE
IMPLEMENTATION_SCOPE_CHANGED  = FALSE
BOOK_6_IMPLEMENTATION_AUTHORITY = UNCHANGED (remains TRUE, offline amendment
                                          scope only, per BOOK6-IMPL-CONSOLIDATED-v0.4)
```

The operator had **already made the policy choice**. `PER_RECORD` was selected
at `BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1`. What remained was a stale row in
the carried case set that still demanded the opposite outcome. This artifact
prospectively retires that row. It invents no policy.

```text
POLICY_DECISION_OUTSTANDING      = FALSE
CORPUS_PRECEDENCE_CLEANUP_DONE   = TRUE   (on ratification of this spec)
```

---

## 1. The contradiction this spec resolves

### 1.1 The stale carried outcome

Test spec v0.2 §5 carried:

```text
CURR-21 | branching lineage A <- B, A <- C
        | resolve_current(A/B/C) all refuse
        | is_authoritative_now(A/B/C) all False
```

That is **COMPONENT_WIDE** fail-closed. It refuses `B` and `C` because they
share a predecessor.

### 1.2 How it entered the ratified contract

v0.3 §1 states, verbatim: *"No carried case changed."* v0.3 §3 declares the 19
carried cases **carried unchanged**. The GAP-7 ratification record §8 then binds
the whole set:

```text
TEST_SPEC = CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md
CASES     = 39
19 carried (CURR-1..15 less CURR-7, CURR-16..23 less CURR-24)
```

So the component-wide outcome entered the ratified contract **transitively**, by
carriage. Note precisely what this does and does not say:

```text
v0.2_ITSELF_WAS_RATIFIED                    = FALSE
CARR_21_ENTERED_RATIFIED_CONTRACT_VIA_CARRY = TRUE
```

`v0.2` was `DRAFT_PENDING_OPERATOR_RATIFICATION`. It was never ratified in its
own right. Its result was ratified anyway, because a draft's case set was
adopted wholesale by a later ratification that declared it unchanged.

### 1.3 The later ratification that contradicts it

`BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1` §3 and §5:

```text
SUCCESSOR_CURRENTNESS_SCOPE = PER_RECORD
COMPONENT_WIDE_FAIL_CLOSED  = NOT ADOPTED

TERM-6 | A <- B and A <- C | A not current (TERM-4);
                         B current;
                         C current
```

`TERM-6` is the **paired negative** of `TERM-4`, on the *same scenario*, with
the *opposite* outcome for `B` and `C`. Both cannot be current falsifiers.

```text
BOTH_CANNOT_BE_CURRENT_FALSIFICATION_REQUIREMENTS = TRUE
LATER_RATIFICATION_CONTROLS                     = TRUE
```

### 1.4 Why later controls

The corpus has a settled ordering rule, stated in the successor record §3.2 and
inherited from the NV-B precedent:

```text
A RULE IS NOT DOCTRINE UNLESS A RATIFICATION ADOPTED IT
THE LATER RATIFICATION IS THE ONE THE OPERATOR ADOPTED
```

`TERM-6` was added by an explicit operator ratification. The component-wide
outcome was inherited by carriage from a draft. Adoption outranks carriage.

```text
CARRIED_FROM_DRAFT        = LOWER PRECEDENCE
EXPLICITLY_ADOPTED_LATER  = CONTROLS
```

---

## 2. Disposition of the stale carried case

### 2.1 Required disposition

```text
CARR-21 = SUPERSEDED_BY_TERM_6
```

### 2.2 Honest statement of what the old case demanded

Recorded plainly, because the old row was not wrong when written — it was
**superseded**:

```text
OLD CARR-21 REQUIRED  : A, B and C ALL REFUSE
OLD CARR-21 OUTCOME WAS NEVER FALSE — IT IS NO LONGER CURRENT
CURRENT REQUIREMENT   : A refuses; B and C resolve on their own conjuncts
```

### 2.3 What this spec does not do

```text
HISTORY_DELETED                 = FALSE
UNRELATED_CASES_RENUMBERED      = FALSE
OLD_ROW_REINTERPRETED           = FALSE
OLD_ROW_CLAIMED_TO_HAVE_MEANT_PER_RECORD = FALSE   (it never did)
```

The old row demanded component-wide refusal. It did not mean `PER_RECORD`, it
did not mean "the record itself", and it is not re-described here as any of
those. It is recorded as what it said, and retired on the single point where a
later ratification overtook it.

**Scope of the supersession is narrow.** `CARR-21` is retired **on the
branched-family scope only**. Every other case, every conjunct, every gate
ordering, and every other carried outcome is carried forward unchanged.

---

## 3. Canonical case set — carried forward from the ratified 40

### 3.1 Mechanical inventory

Enumerated from the ratified case-id namespace, not estimated:

```text
CARR-1..CARR-19      19
CURR-S1..CURR-S3      3
TERM-1..TERM-6        6
NV-1..NV-10          10
STRUCT-1..STRUCT-2    2
                   ----
CANONICAL TOTAL      40
```

This figure is independently confirmed by the implementation's own inventory
assertion (`test_the_forty_ratified_cases_are_all_named_in_this_file`), which
asserts exactly this 40-prefix list and passes at `f705007ea`.

### 3.2 Why the count does **not** fall to 39

This is recorded because the alternative reading is superficially reasonable and
must be closed explicitly rather than left ambiguous.

`CARR-21` is **not a ratified case-id**. Across the entire corpus the only
individual `CARR-<n>` ids that ever appear are `CARR-1` and `CARR-19`, both
purely as range endpoints. v0.2 and the audit source it draws on use the `CURR-*`
namespace and contain **zero** `CARR-` occurrences.

The `CARR-1..CARR-19` range is therefore a **lossy relabeling** of the v0.2
`CURR-*` labels, and the corpus never recorded which `CARR-*` number absorbed
`CURR-21`.

```text
CARR_21_IS_A_RATIFIED_CASE_ID      = FALSE
CARR_21_IS_A_RETIRED_REQUIREMENT   = TRUE
THE_SUPERSESSION_IS_REQUIREMENT_LEVEL, NOT_CASE_ID_LEVEL
```

Consequently the count of canonical case rows is unchanged at **40**, and what
retires is the *requirement* — not a row. Forcing a 39 would require inventing a
`CARR-*` ↔ `CURR-*` mapping that was never recorded, and would disagree with the
implementation's own 40-case inventory.

```text
LIVE_REQUIREMENTS_ON_THE_BRANCHED_FAMILY_SCENARIO = 1   (TERM-6)
WAS_BEFORE_THIS_CLEANUP                          = 2   (TERM-6 + CARR-21)
NO_DUPLICATE_OPPOSITE_FALSIFIERS                 = TRUE
```

### 3.3 A second, minor arithmetic looseness — recorded, not blocking

v0.3's own parenthetical gloss of its carried set — *"(CURR-1..15 less CURR-7,
plus CURR-16..23 less CURR-24)"* — enumerates **22** labels, not the **19** it
declares. The operative ratified figure is 19, and it reconciles against the
ratified total: `19 + 3 + 5 + 10 + 2 = 39`. The gloss is descriptive shorthand
that does not add up; the ratified count does.

```text
OPERATIVE_RATIFIED_COUNT = 19   (governs)
PARENTHETICAL_GLOSS      = 22   (descriptive, inaccurate, non-governing)
COUNT_CONFLICT_BLOCKING   = FALSE
```

This is a labelling defect, not a second contradiction. It is recorded so a
future reader does not mistake it for one.

---

## 4. The canonical branched-family requirement

Single live falsifier for `A <- B`, `A <- C`:

```text
TERM-4 | A <- B and A <- C | A not current (lineage invalid)
TERM-6 | A <- B and A <- C | B current iff B's own five conjuncts pass
                         | C current iff C's own five conjuncts pass
```

```text
resolve_current("A")      -> REFUSE (LINEAGE_INVALID)
resolve_current("B")      -> RETURNS B
resolve_current("C")      -> RETURNS C
is_authoritative_now("A") -> FALSE
is_authoritative_now("B") -> TRUE
is_authoritative_now("C") -> TRUE
```

`TERM-4` and `TERM-6` are **not** duplicates. They are paired negatives
pinning the same scope from opposite sides: `TERM-4` forbids under-refusing `A`,
`TERM-6` forbids over-refusing `B` and `C`. Both remain canonical. Neither is
retired.

```text
COMPONENT_WIDE_REFUSAL_OF_B_OR_C = PROHIBITED
FAIL_CLOSED_SCOPE = THE RECORD WHOSE OWN SUCCESSOR SET IS BRANCHED
```

---

## 5. Everything carried forward unchanged

Recorded so the cleanup's narrowness is auditable:

```text
GAP_7_KERNEL_SHAPE                    = 7A-KERNEL      (unchanged)
STATUS_DIRECTION                      = B-STRICT       (unchanged)
NV_POLICY                             = NV-B           (unchanged)
NV_B_IS_NEW_POLICY                    = TRUE           (unchanged)
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE        (unchanged)
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE  (unchanged)
REGISTRATION_ACCEPTS_B_AND_C           = UNCHANGED ACCEPTED
WRITE_TIME_BRANCH_REJECTION            = NOT AUTHORIZED
RESOLVER_ORDER                        = UNCHANGED (v0.3 §2, steps 1..8)
```

The resolver order is untouched. In particular, lineage validity is still checked
at **step 2**, against the record's **own** successor set. This spec changes
which outcomes are required; it changes nothing about how the resolver decides.

---

## 6. Implementation standing

```text
IMPLEMENTATION_ALREADY_CONFORMS_TO_THIS_SPEC = TRUE   (verified at f705007ea)
RUNG_3_REWORK_REQUIRED                       = FALSE
SOURCE_CHANGE_REQUIRED_BY_THIS_SPEC          = FALSE
```

The Rung 3 implementation already realizes exactly this contract: `A` refuses
at lineage, `B` and `C` resolve on their own conjuncts, and no component-wide
refusal exists anywhere in the resolver or the case tests. The implementation's
`TERM-6` test carries an explicit note that `CARR-21`'s older component-wide
outcome is superseded on this point.

**That note remains correct and is left in place.** It is the implementation's
active falsifier and its provenance trail; this spec confirms it rather than
replacing it.

---

## 7. What this spec does not do

```text
NO source change
NO test code
NO implementation edit
NO status-validator edit
NO lifecycle remedy
NO registration-policy change
NO new currentness policy
NO case renumbering
NO history deletion
NO GAP reopening
NO Book 7
NO live acquisition
```

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (unchanged, offline amendment scope only)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**Next operator action:** ratify or hold this spec via
`CSIA_BOOK_6_GAP7_TEST_CONTRACT_PRECEDENCE_REVIEW_v0.1.md` and
`CSIA_BOOK_6_GAP7_TEST_CONTRACT_PRECEDENCE_RATIFICATION_RECORD_v0.1.md`.