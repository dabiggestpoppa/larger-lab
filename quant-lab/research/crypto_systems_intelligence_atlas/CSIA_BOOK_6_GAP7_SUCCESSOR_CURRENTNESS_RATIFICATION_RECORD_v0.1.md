# CSIA — Book 6 GAP-7 Successor Currentness Ratification Record v0.1

**Status:** `RATIFIED`
**Record type:** formal governance ratification record
**Date:** 2026-10-04
**Decision id:** `BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1`
**Operator selection:** `RATIFY_SUCCESSOR_CURRENTNESS_SCOPE_PER_RECORD`
**Scope:** `BOOK 6 CURRENTNESS GOVERNANCE — BRANCHED LINEAGE, SUCCESSORS ONLY`
**Grants implementation authority:** `FALSE` (already granted by `BOOK6-IMPL-CONSOLIDATED-v0.4`)

---

## 0. What this record is, and what it is not

This record **ratifies doctrine**. It ratifies a scope question that GAP-7
ratifiation left to be *derived*, converting a derivation into a quotation.

```text
RATIFIES   = THE SCOPE OF FAIL-CLOSED BRANCHING ACROSS A BRANCHED FAMILY
IMPLEMENTS = NOTHING
CHANGES ANY ACCEPTED SOURCE   = FALSE
GAP_7_REOPENED                = FALSE
GAP_6_REOPENED                = FALSE
RATIFIED_DOCTRINE_CHANGED     = FALSE   (see §3.3 — it is confirmed, not amended)
```

## 1. The question

In a branched lineage

```text
A <- B
A <- C
```

`A`'s lineage is invalid and `A` fails closed — that much is settled by `TERM-4`
and by `MULTIPLE_SUCCESSOR_LINEAGE = FAIL_CLOSED`. The open question was the
**scope** of that fail-closed rule:

```text
Q. May B and C independently resolve CURRENT, each being terminal
   (no registered successor) and otherwise valid?
```

Two candidate policies existed, and only one of them is in force.

| | Policy | Effect |
|---|---|---|
| **A** | `PER_RECORD` | `A` not current. `B`, `C` current if each terminal + other conjuncts |
| **B** | `COMPONENT_WIDE` | `A`, `B`, `C` all not current |

---

## 2. What the prior corpus said

```text
clarification v0.3 §1   MULTIPLE_SUCCESSOR_LINEAGE = FAIL_CLOSED
test spec v0.3 §5       TERM-4 | A <- B and A <- C | lineage invalid;
                        fail closed; A not current
```

Neither names `B` or `C`. No ratified artifact invalidates the family. The
corpus was therefore **determinate but silent**: silence from which two readings
could be derived.

## 3. The operator selection

```text
SUCCESSOR_CURRENTNESS_SCOPE = PER_RECORD
COMPONENT_WIDE_FAIL_CLOSED  = NOT ADOPTED
```

### 3.1 Why `PER_RECORD` is the doctrine

Ratification record v0.1 §3 defines current authority for **all**
`MeasurementObservation` records as an exhaustive conjunction over that record's
own attributes:

```text
CURRENT = TERMINAL
     AND STRUCTURALLY_VALID
     AND METHODOLOGY_CURRENT
     AND HAS_SOURCE_CLAIMS
     AND ALL_SOURCE_CLAIMS_CURRENT
```

`TERMINAL` is a fact about a record's **own** registered successor set. `B` has
no registered successor, so `TERMINAL` holds for `B`; `B`'s lineage is not
branched — `B` has one predecessor and no successors.

Refusing `B` would therefore require a **sixth conjunct**, of the form
`NOT_IN_BRANCHED_COMPONENT`, and no prior ratification supplies one.

```text
PRIOR_CONJUNCTS                    = 5
A_SIXTH_CONJUNCT_WAS_RATIFIED      = FALSE
COMPONENT_WIDE_REQUIRES_A_SIXTH    = TRUE
```

### 3.2 What the alternative would have cost

`COMPONENT_WIDE` is not absurd, and it is recorded here as a live option that was
considered. Adopting it would have been **new policy**, not recovered doctrine —
precisely the move the GAP-7 ratification record refused when it withdrew the
`NV-A` claim (§4, `DEFECTIVE_BEHAVIOR_IS_NORMATIVE_EVIDENCE = FALSE`).

```text
COMPONENT_WIDE_WOULD_BE = NEW POLICY, NOT DOCTRINE RECOVERY
NV_B_PRECEDENT_FOLLOWS  = A RULE IS NOT DOCTRINE UNLESS A RATIFICATION ADOPTED IT
```

Consistency with that precedent required the operator to *adopt* whichever scope
was chosen. This record is that adoption.

### 3.3 This is a confirmation, not an amendment

```text
RATIFIED_DOCTRINE_CHANGED = FALSE
PRIOR_CONJUNCTS_UNCHANGED = TRUE
PRIOR_RATIFICATIONS_UNTOUCHED = TRUE
```

Ratifying `PER_RECORD` adopts the reading that the existing five-conjunct
definition already implies. No accepted source is touched and no prior
ratification is reopened. What changes is the *status* of the reading: it was an
interpretation, and it is now doctrine that a future implementer may cite
directly instead of re-deriving.

---

## 4. The ratified rule

```text
IN A BRANCHED LINEAGE  A <- B  AND  A <- C:

  A  -> NOT CURRENT        (lineage invalid; TERM-4)
  B  -> EVALUATED ON ITS OWN CONJUNCTS
  C  -> EVALUATED ON ITS OWN CONJUNCTS

  B AND C ARE CURRENT IFF EACH IS
      TERMINAL
      AND STRUCTURALLY_VALID
      AND METHODOLOGY_CURRENT
      AND HAS_SOURCE_CLAIMS
      AND ALL_SOURCE_CLAIMS_CURRENT
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
A_FAILS_CLOSED                          = UNCHANGED (TERM-4)
REGISTRATION_ACCEPTS_B_AND_C            = UNCHANGED ACCEPTED
WRITE_TIME_BRANCH_REJECTION             = NOT AUTHORIZED (packet v0.4 §3)
STATUS_BASED_REFUSAL                    = FORBIDDEN (B-STRICT)
FAIL_CLOSED_SCOPE_WIDENED               = NO
FAIL_CLOSED_SCOPE_NARROWED              = YES — TO THE RECORD ITS OWN LINEAGE
```

Note the direction. This ratification **narrows** fail-closed scope from "any
record in a branched component" to "the record whose own successor set is
branched". It forbids more than it permits. It cannot weaken any other ratified
rule, and it cannot grant authority.

## 5. `TERM-6` — the falsification case

`TERM-4` proves `A` fails closed. It does **not** prove `B` and `C` survive,
because `TERM-4` never asks about them. Without a case, the doctrine in §4 would
be unfalsifiable, and an implementation that over-refused the whole family would
pass `TERM-4` cleanly.

```text
TERM-6 | A <- B and A <- C | A not current (TERM-4);
                         B current;
                         C current
```

All other gates pass for `B` and `C`: registered, structurally valid, definition
resolves, methodology current, `source_claim_refs != ()`, all cited Book 2 claims
current.

```text
resolve_current("A")            -> REFUSE   (LINEAGE_INVALID)
resolve_current("B")            -> RETURNS B
resolve_current("C")            -> RETURNS C
is_authoritative_now("B")       -> TRUE
is_authoritative_now("C")       -> TRUE
```

### 5.1 What `TERM-6` forbids

```text
REFUSING_B_OR_C             = THE FAILURE MODE THIS CASE EXISTS TO CATCH
CHOOSING_B_OR_C_AS "THE" SUCCESSOR = PROHIBITED
UNREGISTERING_A, B OR C     = PROHIBITED
```

`TERM-6` is the paired negative of `TERM-4`. `TERM-4` forbids under-refusing;
`TERM-6` forbids over-refusing. Together they pin the scope from both sides.

### 5.2 Case count consequence

```text
PRIOR_RATIFIED_GAP7_CASES = 39  (CARR-1..19, CURR-S1..3, TERM-1..5,
                                 NV-1..10, STRUCT-1..2)
TERM_6                     = ADDED
RATIFIED_GAP7_CASES_NOW    = 40
```

`TERM-6` was checked against the whole corpus before naming: **0 prior
occurrences**, so no case id is reused.

---

## 6. Interaction with `BOOK6-IMPL-CONSOLIDATED-v0.4`

The authorization names *"the ratified GAP-7 39-case test contract"*. That figure
is now 40. This is not a defect and does not require re-authorization, for a
reason worth stating rather than assuming:

```text
A_FALSIFICATION_CASE_IS_A_PROHIBITION_NOT_A_PERMISSION
A_NEW_CASE_CAN_CONSTRAIN_THE_IMPLEMENTATION
A_NEW_CASE_CANNOT_EXPAND_IMPLEMENTATION_SCOPE
```

Adding `TERM-6` forbids an implementation that `39` cases would not have
caught. It widens nothing. The authorized scope — GAP-7 hardening, GAP-1..GAP-6,
20-check replay, regression and traceability — is unchanged.

```text
AUTHORIZATION_REISSUED_REQUIRED = FALSE
AUTHORIZED_SCOPE_CHANGED        = FALSE
IMPLEMENTATION_NOW_FURTHER_CONSTRAINED = TRUE
```

The authorization also already recorded
`SUCCESSOR_CURRENTNESS_SCOPE = PER_RECORD` in its implementation law
(packet v0.4 §11.1). This record converts that law's basis from interpretation
to ratified doctrine. **The law does not change. Its warrant does.**

## 7. What this record discharges

Consolidated authorization review v0.4 §6.4 recorded the interpretive caveat
and left it open:

```text
REJECTED_ALTERNATIVE = COMPONENT_WIDE_FAIL_CLOSED
REJECTION_GROUND     = REQUIRES AN UNRATIFIED SIXTH CONJUNCT
IS_THIS_A_HOLD_TRIGGER = NO — ... so the operator can override it
                         before implementation begins
```

```text
CAVEAT_DISCHARGED_BY_THIS_RECORD = TRUE
REVIEW_v0.4_EDITED               = FALSE   (the caveat stands as history)
```

Review v0.4 is not edited. It recorded an audit finding that was true when made,
and the caveat is now answered by a later recorded decision — which is exactly
how this corpus is meant to work.

```text
OPEN_STRENGTHENINGS_BEFORE = 2   (TIME-16; successor-scope)
OPEN_STRENGTHENINGS_NOW    = 1   (TIME-16 only)
```

## 8. Residual, recorded not blocking

```text
SUCCESSOR_FAMILY_SCOPE_NOW_UNAMBIGUOUS = TRUE
COMPONENT_WIDE_POSSIBLE_LATER         = ONLY VIA A NEW RATIFICATION
```

If a future requirement makes component-wide fail-closed desirable — for
instance, so that a branched lineage cannot leave two simultaneous current
answers — that is legitimate policy, but it must be **ratified as a sixth
conjunct**, with its own decision id, its own falsification cases, and an
explicit acknowledgement that it is new policy rather than recovered doctrine.

This is not a pending gap. It is the correct future route.

## 9. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (granted by BOOK6-IMPL-CONSOLIDATED-v0.4,
                                         unchanged by this record)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
IMPLEMENTATION_STARTED         = FALSE
```

## 10. Explicit non-actions

```text
IMPLEMENTATION_STARTED            = FALSE
SOURCE_FILE_WRITTEN               = FALSE
SOURCE_FILE_EDITED                = FALSE
TEST_CODE_WRITTEN                 = FALSE
TEST_CASE_EXECUTED                = FALSE
BRANCH_CREATED                    = FALSE
WORKTREE_CREATED                  = FALSE
FROZEN_WORKTREE_MUTATED           = FALSE
GAP_7_REOPENED                    = FALSE
GAP_6_REOPENED                    = FALSE
RATIFIED_RECORD_EDITED            = FALSE
TEST_SPEC_v0.3_EDITED             = FALSE
REVIEW_v0.4_EDITED                = FALSE
PACKET_v0.4_EDITED                = FALSE
COMPONENT_WIDE_ADOPTED            = FALSE
REGISTRATION_POLICY_CHANGED       = FALSE
WRITE_TIME_BRANCH_REJECTION       = NOT AUTHORIZED
STATUS_VALIDATOR_TOUCHED          = FALSE
BOOK_7_WORKED_ON                  = FALSE
CHOIR_TOUCHED                     = FALSE
```

## 11. Cross-references

```text
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md  five conjuncts
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.3.md         MULTIPLE_SUCCESSOR_LINEAGE
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md            TERM-1..TERM-5
CSIA_BOOK_6_GAP7_SUCCESSOR_CURRENTNESS_RATIFICATION_RECORD_v0.1.md     this record; TERM-6
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.4.md    §6.3, §6.4 caveat
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.4.md    §3.3, §11.1 law
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

---

**Status:** `RATIFIED`. Successor currentness is doctrine, not an interpretation.
Nothing has been implemented.
