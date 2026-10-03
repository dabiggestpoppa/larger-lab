# CSIA — Book 6 GAP-7 Measurement Currentness Clarification v0.1

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Supersedes for GAP-7:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_DECISION_PACKET_v0.1.md` (superseded by v0.2, not withdrawn)

---

## 1. Resolution summary

```text
GAP_7_RESOLUTION                        = 7A-KERNEL
SINGLE_MEANING_OF_CURRENT               = TRUE
COMPARISON_LOCAL_CURRENTNESS            = PROHIBITED
STATUS_OPTION                           = B-STRICT
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
SUPERSESSION_CURRENTNESS_SOURCE         = REGISTERED LINEAGE TERMINALITY
TERMINALITY                             = STRUCTURAL PROPERTY OF REGISTERED LINEAGE
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE
NV_OUTCOME                              = NV-A  (accepted doctrine, see §6)
```

---

## 2. Repair surface — 7A-KERNEL

`Book6MeasurementRegistry.resolve_current` is the **one** authoritative
current-measurement resolution path. All eight accepted call sites inherit from
it, so one repair covers all of them and no call site needs a local fix.

| # | Call site | Repaired centrally by 7A |
|---|---|---|
| 1 | `book6_core.py:139` `current_value` | yes |
| 2 | `book6_core.py:148` `current_unit` | yes |
| 3 | `book6_core.py:165` `compute_ratio` | yes |
| 4 | `book6_core.py:243` `normalize` | yes |
| 5 | `book6_core.py:337` `_required_input_value` | yes |
| 6 | `book6_core.py:485` `emit_rule_gated_state` | yes |
| 7 | `book6_sensitivity.py:132` `compare_methodology_variants` | yes |
| 8 | `book6_sensitivity.py:193` `compare_sources` | yes |

7B was rejected on measured grounds, not preference: six of eight sites are
outside comparison, and `current_value("A")` was **executed** returning the
superseded `10.0`. A comparison-local filter would leave the kernel's own
sanctioned value read returning historical data.

---

## 3. Status option B-STRICT

```text
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
SUPERSESSION_CURRENTNESS_SOURCE               = REGISTERED LINEAGE TERMINALITY
ObservationStatus                             = LEGACY / DESCRIPTIVE / NON-AUTHORITY-BEARING
```

Rationale, all measured:

- Documentation says the **prior** observation becomes `SUPERSEDED`
  (`book6_records.py:101-102`, `book6_grammar.py:267-268`).
- The model is frozen, so the prior observation **cannot be mutated**.
- The validator requires a `SUPERSEDED` record to name the record **it**
  superseded — its predecessor (`book6_records.py:203-206`).
- Therefore the field behaves as *"this is a superseding restatement"*, not
  *"this record has been superseded"*, and **no valid record can express the
  latter**.

Currentness therefore derives from **structure**, not from a flag that cannot be
set coherently.

Quarantine scope, explicit:

```text
NOT in this round:  rename enum | delete enum | change the validator
                    reinterpret accepted historical records | mutate predecessors
```

### 3.1 Governance invariant

```text
OBSERVATION_STATUS_NOT_AUTHORITY_BEARING = TRUE
```

until a future explicit status-semantics amendment. GAP-7 does not expand into a
measurement-lifecycle redesign.

---

## 4. Terminality

```text
record is TERMINAL  iff  NO registered MeasurementObservation has
                         supersedes_measurement_id == record.measurement_id
```

Terminality is a **structural property of the registered lineage**. It is
decided by nothing else. Explicitly **not** decided by:

```text
status flag | observed_at | caller order | registration order | lexical order
Book 2 claim state
```

Structurally decidable: yes. The successor set is enumerable from
`registry._measurements`, and `measurement_history` already walks it correctly.

---

## 5. Current-authority formula

```text
CURRENT_AUTHORITATIVE_MEASUREMENT(record) requires ALL of:
  1. record exists in registry
  2. supersession lineage is structurally valid (unique successor at every step)
  3. record is TERMINAL in that lineage
  4. definition lookup succeeds
  5. record still validates against its registered MetricDefinition
  6. record's methodology is currently authoritative
  7. missingness/evidence authority path satisfied (§6)
  8. every CITED Book 2 source ref is currently valid

CURRENT = TERMINAL
      AND STRUCTURALLY_VALID
      AND METHODOLOGY_AUTHORITY
      AND BOOK2_OR_RATIFIED_MISSINGNESS_AUTHORITY
```

`ObservationStatus` is **absent** from this formula by design.

### 5.1 Step 5 — structural revalidation

`validate_against_definition` carries the docstring *"Checked at use, not only
at construction: a forged `model_copy` must not be able to assert a unit,
category or denominator role the definition forbids"* (`book6_records.py:234-236`).
`resolve_current` does not call it.

Measured answer to "is this redundant?":

| Property | Result |
|---|---|
| `MetricDefinition` frozen | yes — assignment refused |
| duplicate `metric_id` re-registration | refused |
| supersede / replace / invalidate API | **none** |
| live revalidation therefore | **redundant but harmless** |

Because definitions can never change, step 5 cannot presently change a verdict.
It is retained because the function's own accepted docstring already promises
use-time checking, and because redundancy here costs correctness nothing while
removing it would contradict an accepted contract. **No definition versioning is
invented.**

### 5.2 Step 6 — methodology applies to every record

`methodology_ref` is `Field(min_length=1)` — required on every
`MeasurementObservation`, value-bearing or not. `validate_against_definition:262`
binds it to the definition's methodology **without** gating on
`is_value_bearing`; a drifted non-value-bearing record was measured as refused.

```text
METHODOLOGY_AUTHORITY_APPLIES_TO_NON_VALUE_BEARING = TRUE
```

There is no accepted exception, so none is inferred.

---

## 6. Non-value-bearing authority doctrine

### 6.1 Measured table — all eight states, `source_claim_refs=()`

| MissingnessState | Must cite Book 2? | May carry `()`? | What establishes authority | Methodology applies? | Terminality applies? |
|---|---|---|---|---|---|
| `NOT_APPLICABLE` | no | **yes** | structural + methodology | yes | yes |
| `NOT_SUPPORTED` | no | **yes** | structural + methodology | yes | yes |
| `NOT_AVAILABLE` | no | **yes** | structural + methodology | yes | yes |
| `NOT_COLLECTED` | no | **yes** | structural + methodology | yes | yes |
| `SOURCE_UNAVAILABLE` | no | **yes** | structural + methodology | yes | yes |
| `STALE` | no | **yes** | structural + methodology | yes | yes |
| `PARTIAL_COVERAGE` | no | **yes** | structural + methodology | yes | yes |
| `UNKNOWN` | no | **yes** | structural + methodology | yes | yes |

All eight were **measured** to REGISTER and RESOLVE with empty refs. The
requirement to cite applies only to the two value-bearing states
(`book6_records.py:152-155`, inside the `VALUE_BEARING_MISSINGNESS` branch).

### 6.2 Source-less missingness — NV-A, from accepted doctrine

`test_book6_missingness.py:111` constructs a `NOT_COLLECTED` record with
`claim_refs=()`, **registers it successfully**, and asserts only that
`current_value` refuses with "absence is not zero".

```text
NV_OUTCOME = NV-A
SOURCE_LESS_MISSINGNESS = STRUCTURAL
current iff TERMINAL and STRUCTURALLY_VALID and METHODOLOGY_CURRENT
```

**No new policy is invented.** NV-A is the already-ratified behaviour, written
down. The value-bearing rule is **not** imposed on missingness records.

### 6.3 Cited non-value-bearing records

Where refs **are** present, step 8 must resolve them live. Measured today:

```text
non-value-bearing + cited claim decayed to STALE -> is_authoritative_now = True
value-bearing control, same decay                -> is_authoritative_now = False
```

The early return is gated on `is_value_bearing` alone, so it defeats cited Book 2
authority as well. This **corrects** the audit brief, which recorded the cited
case as already behaving correctly.

---

## 7. No resurrection and lineage failure

```text
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE
```

- `A <- B`; B loses Book 2 authority -> A historical, B not authoritative, `CURRENT = NONE`
- `A <- B`; B loses methodology authority -> same
- `A <- B <- C`; C loses authority -> A and B stay historical, `CURRENT = NONE`

Terminality is checked before any authority computation, so a predecessor is
refused on step 3 regardless of what its own claim and methodology are doing.
There is no path by which `A` re-enters.

Lineage failure is preserved and made uniform:

```text
A <- B ,  A <- C     ->  lineage INVALID
resolve_current(A)      -> REFUSE
is_authoritative_now(A) = False
is_authoritative_now(B) = False
is_authoritative_now(C) = False
```

No branch selection by lexical id, `observed_at`, registration order, or caller
preference. `measurement_history`'s existing refusal is correct and is extended
to the authority path rather than replaced.

---

## 8. Resolver ordering

```text
resolve_current(measurement_id):
  1  registered lookup                      refuse if absent
  2  lineage validity (unique successor)    refuse if branched
  3  TERMINALITY                            refuse if a successor exists
  4  definition lookup                      refuse if absent
  5  structural validation                  refuse on drift
  6  methodology authority                  refuse if not current
  7  missingness/evidence path              NV-A branch, see section 6
  8  Book 2 authority, if refs are cited    refuse if any ref decayed
  9  return record

is_authoritative_now(id):  calls resolve_current; False on ANY failure
```

No authority-bearing early return before step 9. The existing
`if not observation.is_value_bearing: return observation` moves **after** steps
2-6, and the Book 2 step becomes conditional on refs being non-empty — because
`resolve_source_claim_refs(())` refuses by design (`book6_provenance.py:114`),
scoped by its own message to *"an observation asserting a value"*.

---

## 9. History is preserved

```text
registered_measurement(id)  -> historical accessor, MAY return historical records
measurement_history(id)     -> historical accessor, MAY return historical records
resolve_current(id)         -> MUST NOT return a non-current record
```

```text
QUERYABLE_HISTORY != CURRENT_AUTHORITY
```

`resolve_current` never mutates: no record, no store, no order list. Records stay
frozen and predecessors are never rewritten.

---

## 10. What this artifact does not do

- No implementation. Accepted Book 6 stays at `5f94c3f40c`.
- No test code.
- No GAP-6 ratification, no GAP-7 ratification.
- No `ObservationStatus` rename, deletion, reinterpretation, or validator change.
- No predecessor mutation, no resurrection.
- No comparison-local currentness.
- No invented source-less missingness policy — NV-A is recorded from accepted
  behaviour, not chosen for convenience.
- No definition versioning.
- No Choir work.
