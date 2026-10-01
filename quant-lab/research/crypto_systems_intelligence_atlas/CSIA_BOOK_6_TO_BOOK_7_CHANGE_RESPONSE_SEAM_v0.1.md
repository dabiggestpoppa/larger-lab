# CSIA — BOOK 6 → BOOK 7 CHANGE / RESPONSE SEAM — v0.1

> **Status:** PLANNING / GOVERNANCE ONLY. Defines the reference seam.
> Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Authority under:** `D7N-7 = A` —
> `MEASUREMENT_CHANGE != EVENT_RESPONSE_LINK`.
> **Blocked on:** `BOOK_6_AMENDMENT_REQUIRED = TRUE`; no comparison product
> exists until Book 6 is amended, implemented, regression-reviewed, and
> formally re-accepted.

---

## 1. The seam in one line

```text
Book 6 ChangeObservation  →  Book 7 ResponseLink
```

Book 7 may ask one question of a Book 6 record: *was this change assessed
inside my declared response window, after this action?* It may ask nothing
else.

## 2. Direction of authority

```text
              OWNS                          MAY DO
Book 6   measurement, comparison,      emit ChangeObservation with delta,
        comparability, baseline,       direction, and comparability status
        direction derivation
              │                              │
              │  accepted record, cited      │  no reverse channel
              ▼                              ▼
Book 7   response-window linkage,      consume by reference ONLY
        event/action association
```

There is **no reverse channel**. Book 7 cannot write to, correct, re-derive,
annotate, or "adjust for context" a `ChangeObservation`. A correction is a new
Book 6 record under a new rule version.

## 3. What Book 7 may do with an accepted `ChangeObservation`

```text
ALLOWED  cite the change_observation_id
ALLOWED  cite the comparison_rule_ref + version it relied on
ALLOWED  record that the change's valid_time is (or is not) inside a declared
         response window for a declared action
ALLOWED  record NO_CHANGE_OBSERVED when the rule was applied and the outcome
         was NO_CHANGE
ALLOWED  record that the change is NOT_COMPARABLE / INSUFFICIENT_DATA
ALLOWED  record response-window linkage as a descriptive relation with
         causal_status capped at ASSOCIATION_ONLY
ALLOWED  emit a missingness/absence state (BASELINE_UNAVAILABLE,
         POST_DATA_UNAVAILABLE, TOO_EARLY_TO_ASSESS, NOT_APPLICABLE, UNKNOWN)
```

## 4. What Book 7 may NOT do

```text
PROHIBITED  compute a delta
PROHIBITED  derive a direction
PROHIBITED  declare two observations comparable or incomparable
PROHIBITED  select or construct a baseline
PROHIBITED  alter a ComparisonRule or propose a local rule variant
PROHIBITED  average or reconcile two ChangeObservations from different rules
PROHIBITED  recompute a normalized value
PROHIBITED  overwrite, supersede, or annotate a ChangeObservation
PROHIBITED  read a ChangeObservation as a Book 2 claim
PROHIBITED  read a ChangeObservation as a state
PROHIBITED  read a ChangeObservation as health, adoption, materiality,
            significance, merit, or investment judgement
```

If Book 7 needs a comparison that no accepted `ComparisonRule` authorises,
the correct action is to **record `CHANGE_NOT_MEASURABLE` / `INSUFFICIENT_DATA`
and request a rule**, never to compute one locally.

## 5. Planned `ResponseLink` (Book 7 side; shape only)

```text
ResponseLink {
  response_link_id:              stable identifier
  action_ref:                    REQUIRED — the Book 7 action whose window
                                  this link is assessed against
  change_observation_ref:        REQUIRED — the accepted Book 6 record
  comparison_rule_ref:           REQUIRED — propagated, never restated
  response_window_ref:           REQUIRED — the declared Book 7 window
  link_type:                     CHANGE_IN_WINDOW | NO_CHANGE_IN_WINDOW |
                                  NOT_COMPARABLE | NOT_MEASURABLE |
                                  TOO_EARLY | NOT_APPLICABLE
  temporal_position:             the assessed relationship, stated
                                  descriptively (e.g. "change valid_time falls
                                  inside window W")
  causal_status:                 ASSOCIATION_ONLY (the only value Book 7 may
                                  assign without a separately ratified causal
                                  methodology, which does not exist)
  valid_time / observed_at:      bitemporal, inherited from the Book 6 record
  evidence_refs:                 the cited Book 2-authorised records
  status:                        DRAFT | RATIFIED | SUPERSEDED
}
```

### 5.1 ResponseLink invariants

```text
RL-1  REQUIRES_AN_ACCEPTED_CHANGE_OBSERVATION — a bare measurement ref is
      never sufficient. This is the repaired rule.
RL-2  REQUIRES_A_CITED_COMPARISON_RULE — the method is always named.
RL-3  REQUIRES_A_DECLARED_WINDOW — no window is invented at link time; the
      window was declared with the action or by a cited window methodology.
RL-4  NOT_A_CAUSAL_CLAIM — causal_status is ASSOCIATION_ONLY. Promotion to a
      causal claim requires a separately ratified methodology (D7N-4 remains
      OPEN / DEFERRED).
RL-5  NOT_A_MATERIALITY_READING — a change in window is not a material event.
RL-6  NOT_A_HEALTH_READING — D6M-5 remains OPEN_DEFERRED; no USED/HEALTHY
      inference is available here or anywhere in Book 7.
RL-7  ABSENCE_IS_NOT_NEGATIVE — a missing later stage, an unmeasured change,
      and an unassessable window each get their own state and are never
      collapsed into a negative response.
RL-8  EXPLICIT_MISSING_LINK — the absence of a ResponseLink is recorded as
      such; silence is not evidence and is not a failed response.
```

## 6. Worked transitions across the seam

| Book 6 emits | Book 7 may conclude | Book 7 must **not** conclude |
|---|---|---|
| `ChangeObservation(INCREASE)` in window | `CHANGE_IN_WINDOW` — a change was observed inside the declared window | "the action caused the increase" |
| `ChangeObservation(DECREASE)` in window | `CHANGE_IN_WINDOW` | "the action harmed the system" |
| `ChangeObservation(NO_CHANGE)` in window | `NO_CHANGE_IN_WINDOW` | "the action failed" |
| `ChangeObservation(NOT_COMPARABLE)` | `NOT_COMPARABLE` | "there was no change" |
| `ChangeObservation(INSUFFICIENT_DATA)` | `NOT_MEASURABLE` | "nothing happened" |
| no `ChangeObservation` exists (no rule covers the metric) | `NOT_MEASURABLE` | "no change occurred" |
| window still open | `TOO_EARLY` | "no response yet" as a finding |
| metric not meaningful for this action | `NOT_APPLICABLE` | "no response" |

The middle column is descriptive linkage. The right column is the class of
error the response-semantics repair exists to prevent.

## 7. Validation of references at use time

```text
A ResponseLink is only well-formed when, at the time it is emitted:
  1. the cited ChangeObservation exists and is an accepted Book 6 record
  2. the cited ComparisonRule version is current-or-explicitly-historical
  3. the underlying measurement refs still resolve
  4. the response window is declared and its boundaries are explicit
  5. no Book 6 field is being asserted that the record does not carry
If any check fails → the link is unresolvable and MUST NOT be emitted.
RATIFIED THEN != AUTHORITATIVE NOW — re-resolution at use time, mirroring the
  Book 6 R3 derivation-binding doctrine.
```

## 8. The seam's honest state right now

```text
BOOK_6_COMPARISON_CONTRACT      = NOT YET ACCEPTED
COMPARISON_RULE_CANONICAL_COUNT = 0
CHANGE_OBSERVATION_CANONICAL_COUNT = 0
BOOK_7_RESPONSELINK_CANONICAL_COUNT = 0
OPERATIVE_POSTURE               = fail-closed — CHANGE_NOT_MEASURABLE
  (D7N-7 interim posture C, superseded as a *default* by the ratified
   doctrine but still the operative behaviour until the comparison contract
   is accepted)
```

The seam is specified and unusable. That is the correct state: the plan
describes a reference that does not yet resolve, rather than inventing a local
comparison to make it resolve.

---

*End of seam contract. Planning artifact.*
