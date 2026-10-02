# CSIA — BOOK 6 → BOOK 7 CHANGE / RESPONSE SEAM — v0.3

> **Status:** PLANNING / GOVERNANCE ONLY. Defines the reference seam.
> Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.2.md`
> (**preserved unmodified**, now `SUPERSEDED`); v0.1 also preserved.
> **Repair:** the consumption condition is strengthened from "a
> `ChangeObservation` whose eleven checks re-resolve" to **"a
> `ChangeObservation` whose COMPLETE DERIVATION BINDING re-resolves"** — the
> nineteen-check replay of grammar v0.3 §4, which now includes the
> baseline-selection and comparison methodologies and the derived coverage
> applicability.
> **Authority under:** `D7N-7 = A` — `MEASUREMENT_CHANGE != EVENT_RESPONSE_LINK`.
> **Blocked on:** `BOOK_6_AMENDMENT_REQUIRED = TRUE`; no comparison product
> exists until Book 6 is amended, implemented, regression-reviewed, and
> formally re-accepted.

---

## 0. Repair delta from v0.2

```text
STRENGTHENED  the consumption condition from an 11-check to a 19-check
              re-resolution covering the COMPLETE derivation binding
ADDED         the derivation-binding requirement to the well-formedness
              conditions: a link is invalid if the baseline-selection
              methodology, comparison semantics, coverage applicability, or
              metric-definition content no longer re-resolve — even when the
              ChangeObservation's own bytes are unchanged
ADDED         DECAYED_DERIVATION as an explicit authority_condition outcome
UNCHANGED     one-way direction; no reverse channel; the ALLOWED/PROHIBITED
              lists; RL-1..RL-10; the worked transition table (extended with
              derivation-decay rows)
```

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
        direction derivation           a replayed coverage verdict, under a
                                       ratified derivation binding
              │                              │
              │  currently authoritative      │  no reverse channel
              ▼  record, cited               ▼
Book 7   response-window linkage,      consume by reference ONLY
        event/action association
```

No reverse channel: Book 7 cannot write to, correct, re-derive, annotate, or
"adjust for context" a `ChangeObservation`. A correction is a new Book 6
record under a new rule version.

## 3. The consumption condition (v0.3)

```text
A ResponseLink may be formed ONLY against a ChangeObservation for which the
engine can, at link time, re-resolve the COMPLETE DERIVATION BINDING to
current_authority = TRUE — all nineteen checks of grammar v0.3 §4, including:

  - baseline-selection methodology identity / fingerprint / currentness
  - comparison semantics fingerprint
  - coverage applicability resolution (REQUIRED | NOT_APPLICABLE | UNRESOLVED)
  - coverage-sufficiency rule ratification, currentness, scope, verdict
  - metric-definition semantic content match
  - input methodology compatibility policy
  - deterministic recomputation

A record that merely carries a self-declared status — or, in v0.1 terms, a
record with status = "RATIFIED" — is NOT consumable.
```

```text
RECORD EXISTS
!=
CURRENTLY AUTHORITATIVE

DERIVATION BINDING RESOLVES
!=
CURRENTLY AUTHORITATIVE   (both are required)
```

## 4. What Book 7 may do with a currently authoritative `ChangeObservation`

```text
ALLOWED  cite the change_observation_id
ALLOWED  cite the comparison_rule_ref + version + fingerprint
ALLOWED  cite the derivation_binding_ref relied upon
ALLOWED  record that the change's valid_time is (or is not) inside a declared
         response window for a declared action
ALLOWED  record NO_CHANGE_OBSERVED when the rule was applied and the outcome
         was NO_CHANGE
ALLOWED  record that the change is NOT_COMPARABLE / INSUFFICIENT_DATA
ALLOWED  read the `coverage_verdict` as the RATIFIED RULE'S OUTPUT — quoted as
         Book 6's verdict, never recomputed, never overridden, never used by
         Book 7 as a basis for its own sufficiency judgment
ALLOWED  read `coverage_requirement_status` as Book 6's derived determination
ALLOWED  record a missingness/absence state (BASELINE_UNAVAILABLE,
         POST_DATA_UNAVAILABLE, COVERAGE_SUFFICIENCY_UNKNOWN,
         COVERAGE_APPLICABILITY_UNRESOLVED, TOO_EARLY, NOT_APPLICABLE, UNKNOWN)
```

## 5. What Book 7 may NOT do

```text
PROHIBITED  compute a delta
PROHIBITED  derive a direction
PROHIBITED  declare two observations comparable or incomparable
PROHIBITED  select or construct a baseline
PROHIBITED  select, alter, or locally vary a benchmark / baseline methodology
PROHIBITED  alter a ComparisonRule or propose a local rule variant
PROHIBITED  vary the comparison semantics (delta basis, zero-baseline policy,
            direction derivation, precision)
PROHIBITED  decide that coverage is not applicable
PROHIBITED  average or reconcile two ChangeObservations from different rules
PROHIBITED  recompute a normalized value
PROHIBITED  recompute, re-judge, or override a coverage verdict
PROHIBITED  treat a coverage percentage as a sufficiency judgment
PROHIBITED  accept a record on the strength of a self-declared status
PROHIBITED  accept a record whose derivation binding no longer re-resolves
PROHIBITED  overwrite, supersede, or annotate a ChangeObservation
PROHIBITED  read a ChangeObservation as a Book 2 claim or as a state
PROHIBITED  read a ChangeObservation as health, adoption, materiality,
            significance, merit, or investment judgement
```

If Book 7 needs a comparison that no accepted `ComparisonRule` authorises —
including because the required coverage rule is unratified or the coverage
applicability is `UNRESOLVED` — the correct action is to **record
`CHANGE_NOT_MEASURABLE` / `NOT_COMPARABLE` / `COVERAGE_SUFFICIENCY_UNKNOWN`
and request a rule**, never to compute one locally and never to substitute a
raw coverage number for a verdict.

## 6. Planned `ResponseLink` (Book 7 side) — v0.3

```text
ResponseLink {
  response_link_id:              stable identifier
  action_ref:                    REQUIRED
  change_observation_ref:        REQUIRED — a CURRENTLY AUTHORITATIVE record
                                  under a resolving derivation binding
  comparison_rule_ref:           REQUIRED — id + version + fingerprint
  derivation_binding_ref:        REQUIRED — propagated, never restated
  response_window_ref:           REQUIRED — the declared Book 7 window
  link_type:                     CHANGE_IN_WINDOW | NO_CHANGE_IN_WINDOW |
                                  NOT_COMPARABLE | NOT_MEASURABLE |
                                  COVERAGE_SUFFICIENCY_UNKNOWN |
                                  COVERAGE_APPLICABILITY_UNRESOLVED |
                                  TOO_EARLY | NOT_APPLICABLE
  authority_condition:           AUTHORITATIVE | DECAYED_RULE | DECAYED_DERIVATION |
                                  UNRESOLVABLE
  temporal_position:             the assessed relationship, stated
                                  descriptively
  causal_status:                 ASSOCIATION_ONLY
  coverage_verdict_quoted:       optional; Book 6's replayed verdict, quoted
                                  only
  coverage_requirement_quoted:   optional; Book 6's derived tri-state, quoted
                                  only
  valid_time / observed_at:      bitemporal, inherited
  evidence_refs:                 cited Book 2-authorised records
  record_state:                  CURRENT | SUPERSEDED | WITHDRAWN
                                  (lifecycle; NOT authority)
}
```

### 6.1 `ResponseLink` invariants

```text
RL-1  REQUIRES_A_CURRENTLY_AUTHORITATIVE_CHANGE_OBSERVATION under a resolving
      derivation binding. A bare measurement ref is never sufficient; neither
      is a record carrying a self-declared status.
RL-2  REQUIRES_A_CITED_COMPARISON_RULE — id, version, and fingerprint.
RL-3  REQUIRES_A_DECLARED_WINDOW — no window is invented at link time.
RL-4  NOT_A_CAUSAL_CLAIM — causal_status is ASSOCIATION_ONLY. D7N-4 remains
      OPEN / DEFERRED, so no causal methodology exists to cite.
RL-5  NOT_A_MATERIALITY_READING.
RL-6  NOT_A_HEALTH_READING — D6M-5 remains OPEN_DEFERRED.
RL-7  ABSENCE_IS_NOT_NEGATIVE.
RL-8  EXPLICIT_MISSING_LINK — silence is not evidence.
RL-9  NOT_SELF_AUTHORIZING — record_state confers no authority.
RL-10 NO_COVERAGE_AUTHORITY — Book 7 may quote a coverage verdict and the
      applicability tri-state but may never produce, require, or infer one.
RL-11 NO_DERIVATION_VARIATION — Book 7 may not select, alter, or locally vary
      the baseline methodology or the comparison semantics; a derivation
      change is a new Book 6 rule version with new operator ratification.
```

## 7. Worked transitions across the seam

| Book 6 emits | Book 7 may conclude | Book 7 must **not** conclude |
|---|---|---|
| authoritative `ChangeObservation(INCREASE)` in window | `CHANGE_IN_WINDOW` | "the action caused the increase" |
| authoritative `ChangeObservation(DECREASE)` in window | `CHANGE_IN_WINDOW` | "the action harmed the system" |
| authoritative `ChangeObservation(NO_CHANGE)` in window | `NO_CHANGE_IN_WINDOW` | "the action failed" |
| `ChangeObservation(NOT_COMPARABLE)` | `NOT_COMPARABLE` | "there was no change" |
| `ChangeObservation(INSUFFICIENT_DATA)` | `NOT_MEASURABLE` | "nothing happened" |
| `COVERAGE_SUFFICIENCY_UNKNOWN` | `COVERAGE_SUFFICIENCY_UNKNOWN` | "coverage is high enough" |
| `COVERAGE_APPLICABILITY_UNRESOLVED` | `COVERAGE_APPLICABILITY_UNRESOLVED` | "coverage is not needed" |
| no `ComparisonRule` covers the metric | `NOT_MEASURABLE` | "no change occurred" |
| record exists; its rule withdrawn or superseded | link **invalid** (`DECAYED_RULE`) | consume it because its bytes are unchanged |
| record exists; its baseline methodology superseded (METH-2) | link **invalid** (`DECAYED_DERIVATION`) | consume it because `record_state = CURRENT` |
| record exists; metric definition semantics drifted | link **invalid** (`DECAYED_DERIVATION`) | consume it because the ref still resolves |
| window still open | `TOO_EARLY` | "no response yet" as a finding |
| metric not meaningful for this action | `NOT_APPLICABLE` | "no response" |

The middle column is descriptive linkage. The right column is the class of
error the whole repair chain exists to prevent — now including the errors
where the record itself is unchanged and only its dependencies moved.

## 8. Well-formedness at use time

```text
A ResponseLink is only well-formed when, at the moment it is emitted:
  1. the cited ChangeObservation resolves and its COMPLETE derivation binding
     re-resolves to current_authority = TRUE (grammar v0.3 §4, all 19 checks)
  2. the cited ComparisonRule version and fingerprint still resolve
  3. the baseline-selection methodology still resolves at the bound version
  4. the comparison semantics fingerprint still matches
  5. the underlying measurement refs still carry current Book 2 authority
  6. the coverage applicability still resolves to the same tri-state
  7. the coverage rule ref, where REQUIRED, is still ratified, in scope, and
     current
  8. the metric-definition semantic content still matches the bound
     fingerprint
  9. the response window is declared and its boundaries explicit
 10. no Book 6 field is being asserted that the record does not carry
If any check fails → the link is unresolvable and MUST NOT be emitted.
RATIFIED THEN != AUTHORITATIVE NOW.
```

## 9. The seam's honest state right now

```text
BOOK_6_COMPARISON_CONTRACT                = NOT YET ACCEPTED
COMPARISON_RULE_CANONICAL_COUNT           = 0
COVERAGE_SUFFICIENCY_RULE_CANONICAL_COUNT = 0
CHANGE_OBSERVATION_CANONICAL_COUNT        = 0
BOOK_7_RESPONSELINK_CANONICAL_COUNT       = 0
OPERATIVE_POSTURE                         = fail-closed — CHANGE_NOT_MEASURABLE
```

The seam is specified and unusable — which is the correct state: it describes
a reference that does not yet resolve, rather than inventing a local
comparison to make it resolve.

---

*End of seam v0.3. v0.2 and v0.1 preserved unmodified and superseded. Planning
artifact.*
