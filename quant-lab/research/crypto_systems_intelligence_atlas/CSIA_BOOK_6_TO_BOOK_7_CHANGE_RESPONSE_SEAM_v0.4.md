# CSIA — BOOK 6 → BOOK 7 CHANGE / RESPONSE SEAM — v0.4

> **Status:** PLANNING / GOVERNANCE ONLY. Defines the reference seam.
> Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.3.md`
> (**preserved unmodified**, now `SUPERSEDED`); v0.1, v0.2 preserved.
> **Repairs:** R-4 (coverage quote propagation), plus alignment with the v0.4
> canonical arithmetic (a `ResponseLink` may not read direction or magnitude
> from anything the arithmetic did not produce).
> **Authority under:** `D7N-7 = A` — `MEASUREMENT_CHANGE != EVENT_RESPONSE_LINK`.
> **Blocked on:** `BOOK_6_AMENDMENT_REQUIRED = TRUE`; no comparison product
> exists until Book 6 is amended, implemented, regression-reviewed, and
> formally re-accepted.

---

## 0. Repair delta from v0.3

```text
CHANGED  coverage_verdict_quoted and coverage_requirement_quoted are no
         longer "optional". They are MANDATORY when the source
         ChangeObservation carries the corresponding field. There is no
         Book 7 choice to omit a value the source already holds.

ADDED    coverage_observation_state_quoted  (the v0.4 discriminator, also
         propagated faithfully)

ADDED    RL-12 (no omission of known coverage context)
ADDED    RL-13 (no arithmetic reading beyond the canonical values)

UNCHANGED the one-way direction; no reverse channel; the ALLOWED/PROHIBITED
         lists; the nineteen-check derivation requirement; the worked
         transition table, extended with the new arithmetic rows.
```

---

## 1. The seam in one line

```text
Book 6 ChangeObservation  →  Book 7 ResponseLink
```

Book 7 may ask one question of a Book 6 record: *was this change assessed
inside my declared response window, after this action?* It may ask nothing
else.

## 2. Direction of authority (unchanged)

```text
              OWNS                          MAY DO
Book 6   measurement, comparison,      emit ChangeObservation with canonical
        comparability, baseline,       delta, direction, comparability
        direction derivation           status, and replayed coverage fields
              │                              │
              │  currently authoritative      │  no reverse channel
              ▼  record, cited               ▼
Book 7   response-window linkage,      consume by reference ONLY
        event/action association
```

No reverse channel. A correction is a new Book 6 record under a new rule
version.

## 3. The consumption condition (carried, strengthened)

```text
A ResponseLink may be formed ONLY against a ChangeObservation for which the
engine can, at link time, re-resolve the COMPLETE DERIVATION BINDING to
current_authority = TRUE — all nineteen checks of grammar v0.4 §5.
```

`display_metadata` is **not** part of the binding, is **not** consulted by
check 19, and is **not** copied into a link as a semantic value.

---

## 4. Coverage propagation is mandatory (R-4 repair)

```text
SOURCE_VALUE_PRESENT
→
SEAM_QUOTE_PRESENT

SILENCE_ABOUT_KNOWN_COVERAGE
=
INVALID
```

```text
If the source ChangeObservation carries:
    coverage_requirement_status
    coverage_verdict
    coverage_observation_state
then the ResponseLink carries all three, faithfully.

There is no Book 7 option to omit them, and no "optional" marker.
```

v0.3 marked `coverage_verdict_quoted` and `coverage_requirement_quoted`
optional, which permitted a link to exist against a record whose coverage
verdict was `UNKNOWN` while the link itself said nothing — silence about a
known value. That is the `D-A` class reintroduced one layer up, and it is now
closed. `NULL-7` covers the attempt.

**Book 7 still has no authority to recompute, override, or reinterpret these
fields.** Propagation is copying, not adjudication.

---

## 5. `ResponseLink` v0.4

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
                                  COVERAGE_OBSERVATION_UNAVAILABLE |
                                  TOO_EARLY | NOT_APPLICABLE
  authority_condition:           AUTHORITATIVE | DECAYED_RULE |
                                  DECAYED_DERIVATION | UNRESOLVABLE

  temporal_position:             the assessed relationship, stated
                                  descriptively
  causal_status:                 ASSOCIATION_ONLY

  change_kind_quoted:            REQUIRED — the Book 6 canonical change_kind,
                                  copied verbatim
  absolute_delta_quoted:         the Book 6 canonical value when defined;
                                  absence means NOT_COMPUTABLE, never 0
  relative_delta_quoted:         the Book 6 canonical value when defined;
                                  absence means UNDEFINED, never 0/inf/NaN
  delta_operator_quoted:         REQUIRED — the Book 6 delta_operator

  coverage_requirement_status_quoted:   REQUIRED — faithfully propagated
  coverage_observation_state_quoted:     REQUIRED — faithfully propagated
  coverage_verdict_quoted:               REQUIRED — faithfully propagated
  coverage_applicability_source_quoted:  REQUIRED when the source carries it

  valid_time / observed_at:      bitemporal, inherited
  evidence_refs:                 cited Book 2-authorised records
  record_state:                  CURRENT | SUPERSEDED | WITHDRAWN
                                  (lifecycle; not authority)
}
```

### 5.1 Invariants

```text
RL-1  REQUIRES_A_CURRENTLY_AUTHORITATIVE_CHANGE_OBSERVATION under a resolving
      derivation binding. Neither a bare measurement ref nor a self-declared
      status is sufficient.
RL-2  REQUIRES_A_CITED_COMPARISON_RULE — id, version, fingerprint.
RL-3  REQUIRES_A_DECLARED_WINDOW — no window invented at link time.
RL-4  NOT_A_CAUSAL_CLAIM — ASSOCIATION_ONLY. D7N-4 remains OPEN / DEFERRED.
RL-5  NOT_A_MATERIALITY_READING — no tolerance, significance, or "big enough
      to matter" reading. A DELEGATE link is not a MATERIAL link.
RL-6  NOT_A_HEALTH_READING — D6M-5 remains OPEN_DEFERRED.
RL-7  ABSENCE_IS_NOT_NEGATIVE.
RL-8  EXPLICIT_MISSING_LINK — silence is not evidence.
RL-9  NOT_SELF_AUTHORIZING.
RL-10 NO_COVERAGE_AUTHORITY — may quote, never produce, require, or infer.
RL-11 NO_DERIVATION_VARIATION — may not select, alter, or locally vary the
      baseline methodology, delta operator, or any derivation.
RL-12 NO_OMISSION_OF_KNOWN_COVERAGE — every coverage field the source carries
      is propagated. Silence about a known coverage value is INVALID.
RL-13 NO_ARITHMETIC_BEYOND_CANONICAL — direction and magnitude are read only
      from the canonical values Book 6 produced. Book 7 may not re-round, may
      not apply an epsilon, may not reclassify NO_CHANGE as "too small to
      matter", and may not read direction from a display representation.
```

## 6. Prohibited (carried, with RL-12/RL-13 added)

```text
PROHIBITED  compute a delta; derive a direction
PROHIBITED  re-round, apply an epsilon, or reclassify a change
PROHIBITED  select, alter, or locally vary a baseline methodology or the delta
            operator
PROHIBITED  decide that coverage is not applicable
PROHIBITED  omit a coverage field the source record carries
PROHIBITED  average or reconcile ChangeObservations from different rules
PROHIBITED  recompute a normalized value
PROHIBITED  recompute, re-judge, or override a coverage verdict
PROHIBITED  treat a coverage percentage as a sufficiency judgment
PROHIBITED  accept a record on a self-declared status
PROHIBITED  accept a record whose derivation binding no longer re-resolves
PROHIBITED  overwrite, supersede, or annotate a ChangeObservation
PROHIBITED  read a ChangeObservation as a Book 2 claim or a state
PROHIBITED  read a ChangeObservation as health, adoption, materiality,
            significance, merit, or investment judgement
```

## 7. Worked transitions

| Book 6 emits | Book 7 may conclude | Book 7 must **not** conclude |
|---|---|---|
| authoritative `ChangeObservation(INCREASE)` in window | `CHANGE_IN_WINDOW` | "the action caused the increase" |
| authoritative `ChangeObservation(DECREASE)` in window | `CHANGE_IN_WINDOW` | "the action harmed the system" |
| authoritative `ChangeObservation(NO_CHANGE)` in window | `NO_CHANGE_IN_WINDOW` | "the action failed" / "the change was negligible" |
| `absolute_delta = +0.004` displayed as `100.00 vs 100.00` | `CHANGE_IN_WINDOW` (canonical INCREASE) | "no change — the values display as equal" |
| `ChangeObservation(NOT_COMPARABLE)` | `NOT_COMPARABLE` | "there was no change" |
| `ChangeObservation(INSUFFICIENT_DATA)` | `NOT_MEASURABLE` | "nothing happened" |
| `COVERAGE_SUFFICIENCY_UNKNOWN` | `COVERAGE_SUFFICIENCY_UNKNOWN` | "coverage is high enough" |
| `coverage_observation_state = UNAVAILABLE` | `COVERAGE_OBSERVATION_UNAVAILABLE` | "coverage was adequate" |
| `COVERAGE_APPLICABILITY_UNRESOLVED` | `COVERAGE_APPLICABILITY_UNRESOLVED` | "coverage is not needed" |
| no `ComparisonRule` covers the metric | `NOT_MEASURABLE` | "no change occurred" |
| record exists; its rule withdrawn or superseded | link **invalid** (`DECAYED_RULE`) | consume it because its bytes are unchanged |
| record exists; its baseline methodology superseded | link **invalid** (`DECAYED_DERIVATION`) | consume it because `record_state = CURRENT` |
| record exists; metric definition semantics drifted | link **invalid** (`DECAYED_DERIVATION`) | consume it because the ref still resolves |
| source carries a coverage verdict; link omits the quote | link **INVALID** (`RL-12`) | publish a link silent about known coverage |
| window still open | `TOO_EARLY` | "no response yet" as a finding |
| metric not meaningful for this action | `NOT_APPLICABLE` | "no response" |

## 8. Well-formedness at use time

```text
A ResponseLink is only well-formed when, at the moment it is emitted:
  1. the cited ChangeObservation resolves and its complete derivation binding
     re-resolves to current_authority = TRUE (all nineteen checks)
  2. the ComparisonRule version and fingerprint still resolve
  3. the baseline-selection methodology still resolves at the bound version
  4. the delta_operator is still in the closed set and applicable
  5. the underlying measurement refs still carry current Book 2 authority
  6. the coverage applicability still resolves to the same tri-state
  7. the coverage rule ref, where REQUIRED, is ratified, in scope, current
  8. the metric-definition semantic content still matches the bound
     fingerprint
  9. the response window is declared with explicit boundaries
 10. every coverage field the source carries is propagated
 11. no arithmetic value was recomputed, re-rounded, or reclassified
 12. no Book 6 field is asserted that the record does not carry
If any check fails → the link is unresolvable and MUST NOT be emitted.
RATIFIED THEN != AUTHORITATIVE NOW.
```

## 9. Current state

```text
BOOK_6_COMPARISON_CONTRACT                = NOT YET ACCEPTED
COMPARISON_RULE_CANONICAL_COUNT           = 0
COVERAGE_SUFFICIENCY_RULE_CANONICAL_COUNT = 0
CHANGE_OBSERVATION_CANONICAL_COUNT        = 0
BOOK_7_RESPONSELINK_CANONICAL_COUNT       = 0
OPERATIVE_POSTURE                         = fail-closed — CHANGE_NOT_MEASURABLE
```

Specified and unusable — the correct state.

---

*End of seam v0.4. v0.3 and earlier preserved unmodified. Planning artifact.*
