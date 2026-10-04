# CSIA — GAP-6 Readiness Review v0.2 Erratum

**Status:** `ERRATUM` — corrects a methodology, not a measurement.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Corrects:** `CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_READINESS_REVIEW_v0.2.md`
**Successor:** `..._GAP6_READINESS_REVIEW_v0.3.md` (`PASS`, 12/12)

---

## 0. What is and is not corrected

```text
SOURCE_INVENTORY_FINDINGS_REMAIN_FACTUAL = TRUE
COMPARISON_CHANGE_SOURCE_ABSENT          = TRUE
SOURCE_ABSENCE_IS_READINESS_FAILURE     = FALSE

v0.2_VERDICT = SUPERSEDED
```

**The measurements in v0.2 stand.** Every grep it ran was accurate. The
comparison/change substrate genuinely is absent from accepted `5f94c3f4`:
`ComparisonRule`, `ChangeEngine`, `ordering_key` — no matches across `src/` and
`tests/`.

**The inference drawn from them was wrong.** That is the only thing corrected.

## 1. The invalid inference

v0.2 reasoned:

```text
comparison/change substrate absent from accepted source
    -> 6E's ordering subject has no code
    -> 6E cannot be verified
    -> GAP_6_READINESS = HOLD
```

The middle step is where the error is. The final implication:

```text
NOT_IMPLEMENTED  ->  NOT_READY_TO_IMPLEMENT     <-- INVALID
```

is not sound. Implementation has **never** been authorized for Book 6. Absence of
implementation is the expected pre-authorization state, so its presence carries
no information about whether the *design* is implementable.

The three equivalences the operator identified, which v0.2 collapsed:

```text
"ComparisonRule absent from accepted source"
    != "ComparisonRule cannot be implemented from ratified specification"

"ordering_key absent"
    != "ordering semantics are unspecified"

"ChangeEngine absent"
    != "change engine architecture is unimplementable"
```

All three hold for this case: the ratified substrate record
(`BOOK6-COMPARE-SUBSTRATE-v0.2`) specifies each of them in full.

## 2. The correct pre-implementation question

```text
CAN THE RATIFIED DESIGN BE IMPLEMENTED WITHOUT INVENTING NEW POLICY?
```

not

```text
DOES THE IMPLEMENTATION ALREADY EXIST?
```

v0.2 answered the second question. That question has a known answer — no — and
its answer changes only when someone writes code. Readiness should change when
the operator ratifies or withdraws something.

## 3. Per-item classification of v0.2's findings

Every FAIL and UNVERIFIABLE in v0.2, classified:

| v0.2 finding | Class | Reading |
|---|---|---|
| source-less missingness resolves `CURRENT` | **B** | accepted runtime prerequisite absent — a real GAP-7 implementation gap, already ratified for repair |
| superseded predecessor resolves `CURRENT` | **B** | same; GAP-7 `TERM-*` contract exists |
| cited NV + decayed claim resolves `CURRENT` | **B** | same; GAP-7 `NV-3` contract exists |
| methodology not re-resolved for NV | **B** | same; GAP-7 `NV-9` contract exists |
| 6E temporal projection unverifiable | **C** | ordering code not yet written — expected |
| effective-key ordering unverifiable | **C** | same |
| interval ordering unverifiable | **C** | same |
| caller-order irrelevance unverifiable | **C** | same |
| `observed_at` irrelevance unverifiable | **C** | same |
| lexical tie-break unverifiable | **C** | same |

```text
CLASS_A (would require new policy)      = 0
CLASS_B (accepted prerequisite absent)  = 4   -> all GAP-7, already ratified
CLASS_C (code not yet written)          = 6   -> NOT a readiness blocker
```

**Class C is not a readiness blocker**, and v0.2 treated it as one. The four
class-B findings are real, but they are *GAP-7 implementation* gaps with a
ratified contract — not GAP-6 design gaps. They belong to an implementation
order, which is exactly what `CONSOLIDATED_IMPLEMENTATION_ORDER_DEFINED`
captures.

## 4. The corrected outcome

```text
GAP6_READINESS_v0.2 = HOLD      (wrong criterion)
GAP6_READINESS_v0.3 = PASS      (pre-implementation implementability, 12/12)

GAP_6 = STILL NOT RATIFIED
```

A `HOLD` that rests on "the code isn't written yet" tells the operator nothing
actionable, because the only thing that would clear it is the authorization they
have not given. The corrected review answers a question the operator can act on.

## 5. Standing state — unchanged by this erratum

```text
GAP_6                          = 6E DESIGN VALID / RATIFICATION NOT TAKEN UP
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

No artifact is rewritten. v0.2 remains in history as a record of a wrong
methodology, with its accurate source inventory intact.
