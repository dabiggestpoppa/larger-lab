# CSIA — BOOK 6 → BOOK 7 CHANGE / RESPONSE SEAM — v0.2

> **Status:** PLANNING / GOVERNANCE ONLY. Defines the reference seam.
> Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.1.md`
> (**preserved unmodified**, now `SUPERSEDED`).
> **Repair:** `R6A-D2` — the v0.1 seam let Book 7 consume a `ChangeObservation`
> that merely carried `status = RATIFIED`. v0.2 requires a **currently
> authoritative** record, re-resolved at use time.
> **Authority under:** `D7N-7 = A` —
> `MEASUREMENT_CHANGE != EVENT_RESPONSE_LINK`.
> **Blocked on:** `BOOK_6_AMENDMENT_REQUIRED = TRUE`; no comparison product
> exists until Book 6 is amended, implemented, regression-reviewed, and
> formally re-accepted.

---

## 0. Repair delta from v0.1

```text
REMOVED  ResponseLink.status: DRAFT | RATIFIED | SUPERSEDED   (self-ratifying)
REMOVED  consumption of a record "carrying status=RATIFIED"
ADDED    consumption requires current_authority = TRUE, re-resolved at use
ADDED    authority_condition field recording the resolution outcome
ADDED    coverage-verdict visibility to Book 7 without granting it any
         coverage authority
```

The one-way direction, the `ALLOWED` / `PROHIBITED` lists, and the worked
transition table of v0.1 are unchanged and carried forward.

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
        comparability, baseline,       direction, comparability status, and
        direction derivation           a replayed coverage verdict
              │                              │
              │  currently authoritative      │  no reverse channel
              ▼  record, cited               ▼
Book 7   response-window linkage,      consume by reference ONLY
        event/action association
```

There is **no reverse channel**. Book 7 cannot write to, correct, re-derive,
annotate, or "adjust for context" a `ChangeObservation`. A correction is a new
Book 6 record under a new rule version.

## 3. The consumption condition (repaired)

```text
A ResponseLink may be formed ONLY against a ChangeObservation for which the
engine can, at link time, re-resolve:

  current_authority = TRUE
    (all eleven grammar v0.2 §4 checks, including ComparisonRule
     ratification + fingerprint, input measurement Book 2 current authority,
     coverage rule ratification + scope match where required, and
     deterministic recomputation)

A record that merely carries a self-declared status — or, in v0.1 terms, a
record with status = "RATIFIED" — is NOT consumable.
```

```text
RECORD EXISTS
!=
CURRENTLY AUTHORITATIVE
```

## 4. What Book 7 may do with a currently authoritative `ChangeObservation`

```text
ALLOWED  cite the change_observation_id
ALLOWED  cite the comparison_rule_ref + version + fingerprint it relied on
ALLOWED  record that the change's valid_time is (or is not) inside a declared
         response window for a declared action
ALLOWED  record NO_CHANGE_OBSERVED when the rule was applied and the outcome
         was NO_CHANGE
ALLOWED  record that the change is NOT_COMPARABLE / INSUFFICIENT_DATA
ALLOWED  read the `coverage_verdict` field as the RATIFIED RULE'S OUTPUT —
         quoted as Book 6's verdict, never recomputed, never overridden, and
         never used by Book 7 as a basis for its own sufficiency judgment
ALLOWED  record response-window linkage as a descriptive relation with
         causal_status capped at ASSOCIATION_ONLY
ALLOWED  emit a missingness/absence state (BASELINE_UNAVAILABLE,
         POST_DATA_UNAVAILABLE, COVERAGE_SUFFICIENCY_UNKNOWN, TOO_EARLY,
         NOT_APPLICABLE, UNKNOWN)
```

## 5. What Book 7 may NOT do

```text
PROHIBITED  compute a delta
PROHIBITED  derive a direction
PROHIBITED  declare two observations comparable or incomparable
PROHIBITED  select or construct a baseline
PROHIBITED  alter a ComparisonRule or propose a local rule variant
PROHIBITED  average or reconcile two ChangeObservations from different rules
PROHIBITED  recompute a normalized value
PROHIBITED  recompute, re-judge, or override a coverage verdict
PROHIBITED  treat a coverage percentage as a sufficiency judgment
PROHIBITED  accept a record on the strength of a self-declared status
PROHIBITED  overwrite, supersede, or annotate a ChangeObservation
PROHIBITED  read a ChangeObservation as a Book 2 claim
PROHIBITED  read a ChangeObservation as a state
PROHIBITED  read a ChangeObservation as health, adoption, materiality,
            significance, merit, or investment judgement
```

If Book 7 needs a comparison that no accepted `ComparisonRule` authorises —
including because the required `CoverageSufficiencyRule` is not ratified — the
correct action is to **record `CHANGE_NOT_MEASURABLE` / `NOT_COMPARABLE` /
`COVERAGE_SUFFICIENCY_UNKNOWN` and request a rule**, never to compute one
locally and never to substitute a raw coverage number for a verdict.

## 6. Planned `ResponseLink` (Book 7 side; shape only) — repaired

```text
ResponseLink {
  response_link_id:              stable identifier
  action_ref:                    REQUIRED — the Book 7 action whose window
                                  this link is assessed against
  change_observation_ref:        REQUIRED — a CURRENTLY AUTHORITATIVE Book 6
                                  record
  comparison_rule_ref:           REQUIRED — propagated, never restated
  response_window_ref:           REQUIRED — the declared Book 7 window
  link_type:                     CHANGE_IN_WINDOW | NO_CHANGE_IN_WINDOW |
                                  NOT_COMPARABLE | NOT_MEASURABLE |
                                  COVERAGE_SUFFICIENCY_UNKNOWN | TOO_EARLY |
                                  NOT_APPLICABLE
  authority_condition:           the resolution outcome at link time —
                                  AUTHORITATIVE | DECAYED | UNRESOLVABLE
  temporal_position:             the assessed relationship, stated
                                  descriptively
  causal_status:                 ASSOCIATION_ONLY (the only value Book 7 may
                                  assign without a separately ratified causal
                                  methodology, which does not exist)
  coverage_verdict_quoted:       optional; Book 6's replayed verdict, quoted
                                  only — never judged by Book 7
  valid_time / observed_at:      bitemporal, inherited from the Book 6 record
  evidence_refs:                 the cited Book 2-authorised records
  record_state:                  CURRENT | SUPERSEDED | WITHDRAWN
                                  (record lifecycle; NOT authority, NOT a
                                  Book 2 ClaimState)
}
```

### 6.1 `ResponseLink` invariants

```text
RL-1  REQUIRES_A_CURRENTLY_AUTHORITATIVE_CHANGE_OBSERVATION — a bare
      measurement ref is never sufficient, and neither is a record carrying a
      self-declared status. This is the v0.2 repair of the v0.1 gap.
RL-2  REQUIRES_A_CITED_COMPARISON_RULE — the method is always named, with
      version and fingerprint.
RL-3  REQUIRES_A_DECLARED_WINDOW — no window is invented at link time.
RL-4  NOT_A_CAUSAL_CLAIM — causal_status is ASSOCIATION_ONLY. Promotion
      requires a separately ratified causal methodology (D7N-4 remains
      OPEN / DEFERRED).
RL-5  NOT_A_MATERIALITY_READING — a change in window is not a material event.
RL-6  NOT_A_HEALTH_READING — D6M-5 remains OPEN_DEFERRED; no USED/HEALTHY
      inference is available here or anywhere in Book 7.
RL-7  ABSENCE_IS_NOT_NEGATIVE — a missing later stage, an unmeasured change,
      and an unassessable window each get their own state and are never
      collapsed into a negative response.
RL-8  EXPLICIT_MISSING_LINK — the absence of a ResponseLink is recorded as
      such; silence is not evidence and is not a failed response.
RL-9  NOT_SELF_AUTHORIZING — record_state = CURRENT confers no authority; a
      link formed against a decayed record is invalid, and re-resolution at
      use time governs.
RL-10 NO_COVERAGE_AUTHORITY — Book 7 may quote a coverage verdict but may not
      produce, require, or infer one.
```

## 7. Worked transitions across the seam

| Book 6 emits | Book 7 may conclude | Book 7 must **not** conclude |
|---|---|---|
| authoritative `ChangeObservation(INCREASE)` in window | `CHANGE_IN_WINDOW` | "the action caused the increase" |
| authoritative `ChangeObservation(DECREASE)` in window | `CHANGE_IN_WINDOW` | "the action harmed the system" |
| authoritative `ChangeObservation(NO_CHANGE)` in window | `NO_CHANGE_IN_WINDOW` | "the action failed" |
| `ChangeObservation(NOT_COMPARABLE)` | `NOT_COMPARABLE` | "there was no change" |
| `ChangeObservation(INSUFFICIENT_DATA)` | `NOT_MEASURABLE` | "nothing happened" |
| `COVERAGE_SUFFICIENCY_UNKNOWN` (no ratified rule) | `COVERAGE_SUFFICIENCY_UNKNOWN` | "coverage is high enough" |
| no `ComparisonRule` covers the metric | `NOT_MEASURABLE` | "no change occurred" |
| record exists but its rule was superseded | link **invalid** (`authority_condition = DECAYED`) | consume it anyway because it says `status = CURRENT` |
| window still open | `TOO_EARLY` | "no response yet" as a finding |
| metric not meaningful for this action | `NOT_APPLICABLE` | "no response" |

The middle column is descriptive linkage. The right column is the class of
error the response-semantics repair exists to prevent.

## 8. Validation of references at use time

```text
A ResponseLink is only well-formed when, at the time it is emitted:
  1. the cited ChangeObservation resolves and re-resolves to
     current_authority = TRUE (grammar v0.2 §4, all eleven checks)
  2. the cited ComparisonRule version and fingerprint still resolve
  3. the underlying measurement refs still carry current Book 2 authority
  4. the coverage rule ref, where required, is still ratified, in scope, and
     current
  5. the response window is declared and its boundaries explicit
  6. no Book 6 field is being asserted that the record does not carry
If any check fails → the link is unresolvable and MUST NOT be emitted.
RATIFIED THEN != AUTHORITATIVE NOW.
```

## 9. The seam's honest state right now

```text
BOOK_6_COMPARISON_CONTRACT             = NOT YET ACCEPTED
COMPARISON_RULE_CANONICAL_COUNT        = 0
COVERAGE_SUFFICIENCY_RULE_CANONICAL_COUNT = 0
CHANGE_OBSERVATION_CANONICAL_COUNT     = 0
BOOK_7_RESPONSELINK_CANONICAL_COUNT    = 0
OPERATIVE_POSTURE                      = fail-closed — CHANGE_NOT_MEASURABLE
```

The seam is specified and unusable. That is the correct state: it describes a
reference that does not yet resolve, rather than inventing a local comparison
to make it resolve.

---

*End of seam v0.2. v0.1 preserved unmodified and superseded. Planning artifact.*
