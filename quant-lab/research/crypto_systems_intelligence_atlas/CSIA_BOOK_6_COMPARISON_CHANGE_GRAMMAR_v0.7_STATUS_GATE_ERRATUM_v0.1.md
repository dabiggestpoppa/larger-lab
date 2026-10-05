# CSIA — Book 6 Grammar v0.7 Status Gate Erratum v0.1

**Status:** `RATIFIED` (erratum — documentation and corpus repair only)
**Record type:** narrow documentation erratum
**Date:** 2026-10-05
**Decision id:** none required. An erratum records a fact about an artifact; it
does not select policy. No operator selection is made or implied here.
**Grants implementation authority:** `FALSE`
**Changes implementation:** `FALSE`
**Reopens GAP-5 / GAP-6 / GAP-7:** `FALSE`

---

## 0. What this record is

`CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.7.md` §1.5 contains the sentence:

```text
Record-state gate, over accepted fields only:

eligible requires: observation.status is ObservationStatus.OBSERVED
```

That sentence is **stray, non-governing, errant draft text**. It is not
superseded law, because there was never ratified law for it to supersede. This
record establishes that and nothing else.

```text
GRAMMAR_v0.7_STATUS_SENTENCE = STRAY / NON-GOVERNING / INCONSISTENT DRAFT TEXT
DOCTRINE_CHANGED             = FALSE
IMPLEMENTATION_CHANGED       = FALSE
RUNG6_REWORK_REQUIRED        = FALSE
STATUS_GATE_GOVERNING        = FALSE
CURRENTNESS_GATE_GOVERNING   = TRUE
```

---

## 1. Fact 1 — the ratified eligibility list has no status gate

`CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md` §2.3 was ratified, and its
eligibility list is eleven conditions:

```text
 1. same subject_ref
 2. same metric_definition_ref
 3. same metric-definition semantic fingerprint
 4. same MeasurementMethodology identity/version where the rule requires it
 5. same exact MetricDefinition.unit
 6. compatible denominator semantics
 7. compatible cohort semantics where applicable
 8. same required WindowClass / window compatibility
 9. candidate valid_time STRICTLY PRECEDES comparison valid_time
10. candidate satisfies input Book 2 authority requirements
11. candidate satisfies missingness requirements
```

No twelfth condition appears. `ObservationStatus` occurs **zero times** in the
whole of grammar v0.6 — not in §2.3, not anywhere in the document.

```text
RATIFIED_ELIGIBILITY_CONDITIONS        = 11
OBSERVATION_STATUS_IN_V0.6             = 0 occurrences
STATUS_ELIGIBILITY_CONDITION_RATIFIED  = FALSE
```

## 2. Fact 2 — v0.6 was ratified as written

`CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md`,
decision id `BOOK6-COMPARE-SUBSTRATE-v0.2`, records verbatim:

> No edit was made to any of the six artifacts ratified here. They are ratified
> **as written**.

So the ratified substrate contains exactly the eleven conditions above, and no
status gate was ever in force.

```text
SUBSTRATE_RATIFIED_AS_WRITTEN = TRUE
```

## 3. Fact 3 — v0.7 declares §2.3 carried unchanged

Grammar v0.7 §0 declares, verbatim:

```text
SECTIONS_CHANGED        = 1
SECTIONS_CARRIED_FORWARD = ALL OTHERS, VERBATIM
```

and its carry-forward table records:

```text
| §2.3 | `PRIOR_COMPARABLE_WINDOW` eligibility | carried unchanged |
| §2.4 | deterministic ordering                | REPLACED          |
```

Its §2.1 annotation repeats it: *"All eleven v0.6 eligibility conditions stand.
GAP-6 adds none and removes none. `GAP_6_ELIGIBILITY_CHANGES = 0`."*

The one changed section is §2.4, the deterministic ordering. The status
sentence sits at grammar v0.7 line 179, inside §1.5 — a subsection of the
replaced §2.4 block.

## 4. Fact 4 — the sentence contradicts three things

| # | Conflicting authority | Ruling |
|---|---|---|
| a | v0.7's **own declared change scope** | `SECTIONS_CHANGED = 1`, and that one section is §2.4 ordering. A status eligibility gate is a §2.3 change, which v0.7 says it did not make. |
| b | `BOOK6-GAP7-v0.3` **B-STRICT** | `OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE`, `STATUS_ONLY_CHANGES_CURRENTNESS = FALSE`, `SUPERSESSION_CURRENTNESS_SOURCE = REGISTERED_LINEAGE_TERMINALITY` |
| c | **`TIME-11` ratified status invariance** | `REFUSAL_REASON_A = TERMINALITY`, `STATUS_REFUSAL = FALSE`, `TIME_11_TERMINALITY_AUTHORITY = TRUE` |

TIME-11 is decisive on its own terms. It is the case where two candidates tie
on every structural axis, one is non-terminal, and **the non-terminal one is
given the lexically greater ref**. A status gate would let that case pass
through the gate the ratified fixture was specifically rebuilt to prevent.

## 5. Conclusion

```text
V07_STATUS_SENTENCE_IS_INTERNALLY_INCONSISTENT_WITH_V07_CHANGE_SCOPE = TRUE

GRAMMAR_v0.7_STATUS_SENTENCE = STRAY / NON-GOVERNING / INCONSISTENT DRAFT TEXT
```

The sentence has **no implementation authority**. It is not withdrawn doctrine
and it is not a policy choice; it is text that contradicts the document's own
declared scope and two later ratifications, inside a section the document
declares it replaced.

### 5.1 What this record explicitly does NOT say

```text
"ratified status eligibility was superseded"          NOT SAID — nothing was ratified
"the operator rejected a status gate"                  NOT SAID — no choice was made
GAP_5_REOPENED                                          = FALSE
GAP_6_REOPENED                                          = FALSE
GAP_7_REOPENED                                          = FALSE
NEW_CURRENTNESS_POLICY                                  = NONE
```

## 6. The governing gate, restated

The record-state gate for a baseline candidate is the **GAP-7 currentness
authority**, evaluated before any ordering runs:

```text
BASELINE_RECORD_AUTHORITY_GATE = GAP7 CURRENTNESS
OBSERVATION_STATUS_GATE       = NOT GOVERNING
ELIGIBILITY_PRECEDES_ORDERING = TRUE   (BOOK6-GAP6-v0.2)
ORDERING_SEES_INELIGIBLE_RECORDS = FALSE
A historical predecessor NEVER reaches the lexical tie-break
```

This is not a new selection. It is the reading the ratified documents already
require, stated in one place so the stray sentence cannot be cited against it
later.

## 7. Effect on the implementation

```text
IMPLEMENTATION_CHANGED   = FALSE
RUNG6_REWORK_REQUIRED    = FALSE
RUNG_6_STATUS            = VALID
SOURCE_EDITED_BY_THIS_RECORD = FALSE
```

Rung 6 already gates candidates on injected GAP-7 currentness and never reads
`ObservationStatus`. That implementation is **correct under the ratified
authority chain** and requires no rework. This record confirms it rather than
changing it.

## 8. What this record does not do

```text
SOURCE_FILE_WRITTEN_OR_EDITED = FALSE
TEST_CODE_WRITTEN_OR_EDITED  = FALSE
GRAMMAR_v0.6_EDITED           = FALSE
GRAMMAR_v0.7_EDITED           = FALSE   (the stray text is preserved as history)
SUBSTRATE_RATIFICATION_EDITED = FALSE
GAP_RECORD_EDITED             = FALSE
BRANCH_REWRITTEN_OR_REBASED   = FALSE
FROZEN_BOOK_6_WORKTREE_MUTATED = FALSE
BOOK_7_WORKED_ON              = FALSE
LIVE_ACQUISITION              = FALSE
```

A ratified or superseded artifact is not edited in place. The stray sentence
stays in grammar v0.7 exactly as written; this erratum is the record that
discharges it. That is the same correction discipline the phantom benchmark
repair used.

## 9. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (offline amendment scope only, unchanged)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## 10. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md                 ratified eleven conditions
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md  ratified as written
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.7.md                 the stray sentence, line 179
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md  B-STRICT
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md        ELIGIBILITY_PRECEDES_ORDERING
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.6.md       TIME-11, TIME-11.1
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

---

**Status:** `RATIFIED`. One sentence of draft text is recorded as errant. No
doctrine changed and no implementation changed.