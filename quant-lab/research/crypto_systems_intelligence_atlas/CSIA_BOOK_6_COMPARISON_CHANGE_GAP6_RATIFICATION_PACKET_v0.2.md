# CSIA — Book 6 Comparison/Change GAP-6 Ratification Packet v0.2

**Status:** `AWAITING_OPERATOR_DECISION` — a choice, not a decision.
**Date:** 2026-10-03
**Decision id:** proposed `BOOK6-GAP6-v0.2` (collision-free; does not reuse
`D6M-*`, `D7N-*`, `BOOK6-COMPARE-*` or `BOOK6-GAP7-v0.3` namespaces)
**Grants implementation authority:** `FALSE` under every option
**Supersedes:** `..._GAP6_RATIFICATION_PACKET_v0.1.md`

**Precondition satisfied:**
`CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_READINESS_REVIEW_v0.3.md` = `PASS` (12/12),
`REVIEW_TYPE = PRE_IMPLEMENTATION_IMPLEMENTABILITY`.

---

## 1. What is being asked

The operator is asked **one** question:

```text
Ratify GAP-6 as 6E WINDOW_CLASS_AWARE_ORDERING_KEYS?
```

Two options. `HOLD` is a real option, not a formality.

## 2. What the operator is NOT being asked

```text
NOT asked: authorize Book 6 implementation
NOT asked: ratify GAP-7 (already ratified at BOOK6-GAP7-v0.3)
NOT asked: ratify GAP-1..GAP-5 (already ratified at BOOK6-COMPARE-SUBSTRATE-v0.2)
NOT asked: choose a per-state missingness authority table
NOT asked: choose a baseline selector (already ratified: exactly one executable)
NOT asked: approve aggregation semantics
```

## 3. What 6E is

A **selector-local, derived** temporal projection so ordering has a defined value
on every eligible observation. It adds no field, mutates no record, and creates
no new temporal contract.

```text
For o in INTERVAL_WINDOW_CLASSES:      (9 of 10 WindowClass members)
    effective_end(o)   = o.window_end
    effective_start(o) = o.window_start

For o == WindowClass.INSTANTANEOUS:    (the 1 remainder)
    effective_end(o)   = o.valid_time
    effective_start(o) = o.valid_time
```

The projection is **total over the closed enum**. There is no third case, so
implementation must not add an `else` arm with a fallback: an unrecognised
window class is a fail-closed error.

```text
ORDERING_KEYS_ARE_DERIVED = TRUE
OBSERVATION_MUTATION      = FALSE
STORED_BACK_ONTO_RECORD   = FALSE
NEW_TEMPORAL_CONTRACT     = NONE

BLANKET_EXCLUSION_OF_INSTANTANEOUS = FALSE
BLANKET_REFUSAL_OF_INSTANTANEOUS   = FALSE
```

## 4. The ordering 6E feeds

```text
1. greatest effective_end(candidate), strictly before effective_start(comparison)
2. if tied on effective_end: greatest effective_start(candidate)
3. if still tied: stable lexical measurement_ref   (FINAL tie-break ONLY)
```

```text
CALLER_ORDER_AFFECTS_BASELINE     = FALSE
OBSERVED_AT_USED_FOR_ORDERING     = FALSE   (observed_at is knowledge time)
INGESTION_TIME_USED_FOR_ORDERING  = FALSE
RANDOM_SELECTION                  = FALSE
```

The lexical tie-break exists **only** so a tie resolves to exactly one
observation rather than to implementation-defined behaviour.

## 5. Option A — `RATIFY_GAP6_6E_WINDOW_CLASS_AWARE_ORDERING_KEYS`

Ratifies the projection and the 3-step ordering as Book 6 comparison doctrine,
closing GAP-6.

```text
GAP_6                    = CLOSED / RATIFIED
GAP_6_RESOLUTION         = 6E WINDOW_CLASS_AWARE_ORDERING_KEYS
BOOK_6_COMPARISON_GAP6   = RATIFIED
```

**Consistency with ratified substrate.** 6E adds no new object. The ratified
substrate record already fixes: 2 authority-bearing contract classes, exactly
one executable selector, exact-unit identity, presence-derived coverage,
`TemporalComparabilityStatus`, and the 20-check replay. 6E supplies the
ordering keys that substrate's selector consumes. It changes no count and no
closed set.

**Consequence.** GAP-6 ratification does not by itself make anything
implemented. It completes the Book 6 *design*, which is the precondition for a
future implementation authorization covering GAP-7 + comparison/change together.

## 6. Option B — `HOLD`

GAP-6 stays open. Nothing else changes.

```text
GAP_6 = 6E DESIGN VALID / NOT RATIFIED
```

The design remains available for a later ratification round.

## 7. Comparison of options

| | A — ratify 6E | B — hold |
|---|---|---|
| closes GAP-6 | yes | no |
| authorizes implementation | **no** | no |
| requires new policy choice | no | no |
| design status after | complete | open |
| blocks Book 6 implementation | no | effectively yes, by incompleteness |

## 8. Recommendation

**Option A**, on the following grounds and no others:

```text
NO_UNRATIFIED_POLICY_NEEDED    = TRUE    (0 policy gaps across A-T)
DESIGN_INTERNALLY_CONSISTENT    = TRUE    (adds no object, no closed set, no count)
DEPENDENCY_FULLY_SPECIFIED      = TRUE    (GAP-7 ratified, 4 ordering constraints)
READINESS_VERIFIED_ON_CORRECT_QUESTION = TRUE  (PASS 12/12)
```

Option B is defensible if the operator wants GAP-6 ratified *after* GAP-7 is
implemented rather than before. That sequencing preference is legitimate; this
review does not override it. It should be made explicitly rather than by
defaulting to a hold that looks like a design problem.

## 9. Scope of any ratification

```text
SCOPE                        = BOOK 6 COMPARISON ORDERING DOCTRINE ONLY
GRANTS IMPLEMENTATION_AUTHORITY = FALSE
CHANGES ANY ACCEPTED SOURCE  = FALSE
RATIFIES GAP-7               = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

```text
NEXT = operator selects A or B.
       Implementation of GAP-7 rungs 1-3 and comparison rungs 4-11 remains a
       SEPARATE, LATER authorization that must cover BOTH.
```
