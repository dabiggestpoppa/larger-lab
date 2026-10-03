# CSIA — Book 6 GAP-7 Measurement Currentness Clarification v0.2

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`

**Supersedes:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.1.md`
— specifically its §6.2, which asserted `NV-A` as accepted doctrine. That
assertion is **withdrawn**; see §5.

---

## 1. Resolution summary

```text
GAP_7_RESOLUTION                        = 7A-KERNEL
GAP_7_KERNEL_WIDE_DEFECT                = TRUE
SINGLE_MEANING_OF_CURRENT               = TRUE
COMPARISON_LOCAL_CURRENTNESS            = PROHIBITED

STATUS_OPTION                           = B-STRICT
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
STATUS_ONLY_CHANGES_CURRENTNESS         = FALSE

SUPERSESSION_CURRENTNESS_SOURCE         = REGISTERED LINEAGE TERMINALITY
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE
MULTIPLE_SUCCESSOR_LINEAGE              = FAIL_CLOSED

NON_VALUE_BEARING_SOURCELESS_CURRENT_AUTHORITY = OPEN_OPERATOR_DECISION
```

Seven of these are unchanged from v0.1 and were **not** reopened: the kernel
shape, the single meaning of current, the prohibition on comparison-local
currentness, the status direction, lineage as the supersession source, no
resurrection, and fail-closed lineage. Only the non-value-bearing entry moved,
and it moved because the evidence for it was wrong, not because the doctrine
was doubted.

---

## 2. Status doctrine — the single rule

```text
Changing ONLY ObservationStatus, with every authority-bearing structural fact
held identical, MUST NOT change the current-authority outcome.
```

Measured against accepted `5f94c3f40c`, the kernel already complies: records
identical except for status (`OBSERVED` vs `SUPERSEDED`) both resolve `CURRENT`.

Accepted source already asserts the same principle in a neighbouring form:

```text
book6_ratification.py:286   OBJECT_STATUS_IS_NOT_AUTHORITY = True
```

That constant is scoped to *rule objects'* self-declared status, not to
observations, so it is **consistent with but not proof of** B-STRICT. B-STRICT
extends the principle to `MeasurementObservation.status`.

### 2.1 Status quarantine boundary

B-STRICT asserts exactly one thing: **`ObservationStatus` is ignored when
computing current authority.** It asserts nothing about whether the name
`SUPERSEDED` is correct.

Measured incoherence, recorded and **deliberately not repaired here**:

```text
book6_grammar.py:264-268   "the prior observation is retained with SUPERSEDED"
book6_records.py:203       a SUPERSEDED observation MUST name the observation
                           it superseded  (supersedes_measurement_id non-empty)
```

A correctly-marked *predecessor* has `supersedes_measurement_id = None`, so it is
**refused** by that validator — for value-bearing and non-value-bearing records
alike. The validator's direction is inverted relative to the docstring that
describes it.

GAP-7 must therefore **not**:

- rename `SUPERSEDED`
- delete the status field
- repair the validator's semantics
- reinterpret any existing record

This is a **separate future lifecycle-cleanup item**. It is out of scope here,
and it does not affect authority, because authority is computed from registered
lineage and never from this field. Recording the incoherence is enough; acting
on it is not authorised.

---

## 3. Why 7A-KERNEL, restated

`resolve_current` has **8 call sites across 3 modules**:

| Site | Comparison-local? |
|---|---|
| `book6_core.py:139` `current_value` | no |
| `book6_core.py:148` `current_unit` | no |
| `book6_core.py:165` `compute_ratio` | no |
| `book6_core.py:243` `normalize` | no |
| `book6_core.py:337` `_required_input_value` | no |
| `book6_core.py:485` `emit_rule_gated_state` | no |
| `book6_sensitivity.py:132` `compare_methodology_variants` | yes |
| `book6_sensitivity.py:193` `compare_sources` | yes |

Six of eight are not comparison code, and comparison code cannot have its own
currentness without violating `COMPARISON_LOCAL_CURRENTNESS = PROHIBITED`. A
repair at any subset of sites leaves the others wrong; a repair inside
`resolve_current` fixes all eight at once. Hence:

```text
KERNEL_WIDE_DEFECT = TRUE
REPAIR_SURFACE     = 7A-KERNEL (single resolver)
```

Measured consequence of the single-resolver requirement: `current_value("A")`
returns the superseded `10.0` while `B = 12.0` is live — a comparison-agnostic
read surface is already returning a non-current value.

---

## 4. What the accepted sources *do* settle

These are settled by accepted source and need no operator decision.

```text
REGISTRATION_IS_NOT_AUTHORITY                        = True   (book6_registry.py)
STRUCTURAL_VALIDATION_ENFORCED_AT_REGISTRATION        = True   (measured)
DUPLICATE_METRIC_DEFINITION_REFUSED                  = True   (measured)
METRIC_DEFINITION_HAS_NO_SUPERSEDE_REPLACE_INVALIDATE = True   (measured)
METHODOLOGY_AUTHORITY_APPLIES_TO_NON_VALUE_BEARING    = True   (measured)
NON_VALUE_BEARING_CAN_BE_HISTORICAL                  = True   (measured)
SOURCE_LESS_MISSINGNESS_CONSTRUCTIBILITY              = ACCEPTED (measured)
SOURCE_LESS_MISSINGNESS_CONSTRUCTION_WITH_EMPTY_REFS = ACCEPTED (measured)
ABSENCE_IS_NOT_ZERO                                  = True   (test_book6_missingness.py:111)
```

Structural validation is enforced **at registration** (`register_measurement` →
`validate_against_definition`), not only at use: a record bound to an
unregistered metric definition is refused. It is nevertheless **necessary, not
sufficient**, for authority — it says nothing about lineage, methodology or
evidence.

---

## 5. What the accepted sources do *not* settle

### 5.1 The withdrawn claim

v0.1 §6.2 stated, verbatim in effect:

> *"**No new policy is invented.** NV-A is the already-ratified behaviour, written
> down. The value-bearing rule is not imposed on missingness records."*

That sentence is withdrawn. It rests on an inference that does not hold:

```text
ACCEPTED_CONSTRUCTION_BEHAVIOR != ACCEPTED_CURRENT_AUTHORITY_DOCTRINE
```

### 5.2 Why — the evidence chain, examined

The whole v0.1 case rested on `test_book6_missingness.py:111`. That test:

```text
constructs a NOT_COLLECTED record with claim_refs=()   -> yes
registers it                                            -> yes
asserts current_value refuses "absence is not zero"     -> yes
calls resolve_current                                    -> NO
calls is_authoritative_now                              -> NO
```

It establishes **constructibility**, **registration legality**, and **value
non-readability**. It establishes nothing about current authority.

A corpus-wide search then found **no** accepted source that states what makes a
missingness assertion authoritative now:

- `resolve_current` (`book6_registry.py:195-216`) names **zero**
  `MissingnessState` members; the substring `missingness` does not appear in
  its body at all. The early return is gated on `is_value_bearing`, which is
  `missingness_state in VALUE_BEARING_MISSINGNESS` — a **value-forbiddance**
  partition reused as an **authority** partition.
- The ratified measurement grammar (`CSIA_BOOK_6_MEASUREMENT_GRAMMAR_v0.1.md`
  §6) defines the ten states **descriptively** — what each one *means* — and
  adds only one normative sentence: a dimension with a non-observed state
  resolves to `INSUFFICIENT_DATA`, never to zero. That is a **downstream
  resolution** rule. It says nothing about authority.
- `CSIA_BOOK_6_PLAN_RATIFICATION_RECORD_v0.1.md` mentions missingness once, in a
  scope sentence delegating authority *plus* missingness semantics to Book 6. It
  states no per-state rule.
- Every `NOT_APPLICABLE` hit in the governance corpus belongs to
  `coverage_requirement_status` / `coverage_observation_state` — a **different
  enum**. None of them is a `MissingnessState`.

### 5.3 Per-state matrix — measured, not inferred

Each row was executed independently. **No row is inferred from another.**

| State | Construct w/o refs | Register | Explicit governance says current-authoritative w/o refs | Cited refs permitted | Cited refs must be re-validated | Supported by accepted source? |
|---|---|---|---|---|---|---|
| `NOT_APPLICABLE` | ALLOWED | ALLOWED | **none found** | yes | **NO — bypassed** | construct only |
| `NOT_SUPPORTED` | ALLOWED | ALLOWED | **none found** | yes | **NO — bypassed** | construct only |
| `NOT_AVAILABLE` | ALLOWED | ALLOWED | **none found** | yes | **NO — bypassed** | construct only |
| `NOT_COLLECTED` | ALLOWED | ALLOWED | **none found** | yes | **NO — bypassed** | construct only |
| `SOURCE_UNAVAILABLE` | ALLOWED | ALLOWED | **none found** | yes | **NO — bypassed** | construct only |
| `STALE` | ALLOWED | ALLOWED | **none found** | yes | **NO — bypassed** | construct only |
| `PARTIAL_COVERAGE` | ALLOWED | ALLOWED | **none found** | yes | **NO — bypassed** | construct only |
| `UNKNOWN` | ALLOWED | ALLOWED | **none found** | yes | **NO — bypassed** | construct only |

Measured uniformity (this is itself a finding — see below):

```text
CONSTRUCTION_UNIFORM_ACROSS_ALL_8 = True
AUTHORITY_UNIFORM_ACROSS_ALL_8    = True
CITED_REF_BYPASS_UNIFORM          = True
```

Queryability and value-readability were also measured separately, and are
uniform: every state is queryable, and `current_value` refuses for every state.

**The uniformity is not doctrine, and must not be mistaken for it.** The one
uniform authority rule in the accepted kernel is produced by
`missingness_state in VALUE_BEARING_MISSINGNESS` — a partition that exists to
decide whether a *numeric value may be present*. It happens to be consulted at
the authority step because of the early return. Its uniformity across all eight
states is an artifact of that single `in` test, not a considered per-state
policy. Uniform observed behaviour from a defective branch is exactly what
`DEFECTIVE_BEHAVIOR_IS_NORMATIVE_EVIDENCE = FALSE` forbids citing.

### 5.4 The five distinctions that must not be collapsed

```text
1 CONSTRUCTION LEGALITY   may the record be built at all?
2 REGISTRATION LEGALITY   may the registry accept it?
3 QUERYABILITY            can it still be read back after authority is lost?
4 CURRENT AUTHORITY       does resolve_current return it?
5 VALUE READABILITY       may current_value return a number from it?
```

Accepted behaviour: `1 YES`, `2 YES`, `3 YES`, `4 YES (defectively sourced)`,
`5 NO`. The review's objection was to step 4 being asserted from steps 1–3 and 5.
It is not.

---

## 6. Cited non-value-bearing records — settled, no operator decision needed

This part of GAP-7 is **not** open, because accepted source already requires
the behaviour, independently of any NV policy.

```text
book6_registry.py:198-201   "Fails closed when any cited Book 2 claim is
                             unknown, non-current, or has detached evidence."
book6_support.py:165-171    "Registration is still not authority - every read
                             re-resolves the cited Book 2 claims and the
                             methodology."
```

Measured against accepted `5f94c3f40c`, both statements are **false** for
non-value-bearing records: a cited claim decayed to `STALE` leaves
`resolve_current` returning the record, on all eight states.

```text
CITED_REF_PRESENT -> LIVE_BOOK2_REVALIDATION_REQUIRED = TRUE
Decayed cited ref -> not current-authoritative            (required)
No early-return bypass                                    (required)
```

This holds under **every** candidate NV policy, including NV-A. A record that
*cites* a source has made a falsifiable claim; letting that claim survive the
source's decay is not a defensible reading under any option.

### 6.1 Methodology — the same bypass, independently

`book6_methodology.py:19-26` requires every authority-bearing surface to resolve
methodology identity *"before it may authorize anything"*, and **explicitly
lists** `MeasurementObservation.methodology_ref + methodology_version`. Measured
with the methodology invalidated after registration:

```text
value-bearing     -> REFUSED   (methodology re-resolved)
non-value-bearing -> CURRENT   (methodology NOT re-resolved)
```

```text
METHODOLOGY_AUTHORITY_APPLIES_TO_NON_VALUE_BEARING = TRUE  (re-verified)
```

This is a second, independent instance of the early return. It is fixed by
removing the early return, not by choosing an NV policy.

---

## 7. The open decision

```text
NON_VALUE_BEARING_SOURCELESS_CURRENT_AUTHORITY = OPEN_OPERATOR_DECISION
```

Accepted doctrine does not settle it. The operator must choose among NV-A,
NV-B, NV-C, or HOLD. See `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_DECISION_PACKET_v0.3.md`.

What is **not** open, and does not wait on this decision:

- cited refs are live-revalidated (policy-invariant, §6)
- methodology is live-re-resolved (policy-invariant, §6.1)
- status is quarantined (§2)
- terminality comes from registered lineage (§1)
- predecessors never resurrect; branching fails closed (§1)
- single resolver at 7A-KERNEL (§3)
- source-less construction and registration stay legal under **all** options

```text
GAP_7_RATIFIED        = FALSE
GAP_6_RATIFICATION    = HOLD_PENDING_GAP7
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```
