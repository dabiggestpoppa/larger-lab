# CSIA — BOOK 6 STATE VECTOR DESIGN v0.2

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Supersedes (upon operator ratification):** `CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.1.md`,
> which is preserved unmodified as a historical draft.
> **Why v0.2 exists:** v0.1 claimed a universal threshold-free vocabulary while
> shipping six rule-dependent state names. See
> `CSIA_BOOK_6_STATE_RULE_RECONCILIATION_v0.1.md` for the reproduction.
> **Grants no implementation authority.**

---

## 1. The corrected doctrine (v0.1's overclaim is withdrawn)

```text
NO EMPIRICAL THRESHOLD  !=  NO DERIVATION RULE

EVERY STATE REQUIRES A DERIVATION RULE.
A STATE IS EMITTED ONLY WHEN EVERY RULE IT DEPENDS ON IS EXPLICIT,
VERSIONED, AND RATIFIED.
```

v0.1's claim that state dimensions are "threshold-free" is **withdrawn as
incorrect**. The accurate statement: *some* states need no empirical cutoff;
others need a threshold or benchmark rule; **all** states need an explicit,
ratified derivation rule.

## 2. Shape: a vector, never a score (unchanged from v0.1)

```text
FundamentalStateVector (PLANNED, not implemented)
  subject_ref
  as_of_valid_time
  schema_ref              the versioned dimension schema for this subject class
  dimensions              the resolved dimension set (below)
  schema_status           SCHEMA_COMPLETE | SCHEMA_INCOMPLETE  (structural)
  data_status             DATA_COMPLETE | DATA_INCOMPLETE      (structural)
  construction_ref        measurement set + methodologies + rules used
```

No `total`, `score`, `rating`, `grade`, `rank`, or weighted blend may exist on
this type (Constitution §5.3a). v0.2 adds no such field and adds no
completeness number.

## 3. State classes (the v0.2 addition)

### CLASS A — availability / observation states

```text
INSUFFICIENT_DATA             a required input is not observed / not usable
NOT_APPLICABLE                the dimension's measurement does not exist for
                              this subject or architecture family
RULE_NOT_RATIFIED             the derivation rule this dimension needs is not
                              ratified (Class B or C)
COVERAGE_SUFFICIENCY_UNKNOWN  coverage was observed; sufficiency is unjudged
                              because no coverage-sufficiency rule is ratified
```

No directional predicate, no threshold, no benchmark. These are the only states
emittable today under a ratified state-availability rule, and they are the
**fallback** for every Class B/C dimension whose rule is unratified.

### CLASS B — specification-only rule states (PENDING_RULE_RATIFICATION)

```text
INCREASING  <=>  current > prior comparable observation
DECREASING  <=>  current < prior comparable observation
UNCHANGED   <=>  current = prior comparable observation
```

Ratifiable without empirical research, but still an operator act (D6M-3), so
not available today. Required in the ratified rule: same methodology version,
unit, denominator (+ its missingness), cohort, window class, a valid
non-superseded prior observation, and a precision/rounding rule. Ordering only —
**never** a statistical-significance claim.

`UNCHANGED` is available only for measurement classes where exact equality is
semantically well defined (discrete counts, presence/absence, set identity).
Where equality is an artifact of rounding or estimation error, `UNCHANGED` is
`UNAVAILABLE_PENDING_RULE`. **`UNCHANGED` is not `STABLE`.**

### CLASS C — threshold / benchmark-dependent states (UNAVAILABLE_PENDING_RULE)

```text
STABLE, VOLATILE, EXPANDING, CONTRACTING,
HIGHER_THAN_OWN_HISTORY, LOWER_THAN_OWN_HISTORY
```

Each needs `state_rule_ref` (a named, versioned, ratified methodology) plus, as
applicable, `benchmark_methodology_ref`, `tolerance_ref` / `volatility_measure_ref`
/ `decision_rule_ref`, and a window. Until then the dimension resolves to a
Class A state. `EXPANDING` / `CONTRACTING` are additionally **DEFERRED** as
generic forms: they must name a target measurement per dimension or not exist
(English meaning is not a specification).

### v0.2 state table (the operative list)

| State | Class | Status today | Required rule identity |
|---|---|---|---|
| INSUFFICIENT_DATA | A | available (availability rule) | `state_availability_rule_ref` |
| NOT_APPLICABLE | A | available | `state_availability_rule_ref` + applicability evidence |
| RULE_NOT_RATIFIED | A | available | presence of the missing rule is the trigger |
| COVERAGE_SUFFICIENCY_UNKNOWN | A | available | coverage observed, no sufficiency rule |
| INCREASING / DECREASING | B | PENDING_RULE_RATIFICATION | `derivation_rule_ref` (incl. window-compatibility + precision) |
| UNCHANGED | B | per-class: PENDING / UNAVAILABLE | equality rule + per-class validity declaration |
| STABLE | C | UNAVAILABLE_PENDING_RULE | `stability_rule_ref` (tolerance / noise / dispersion) |
| VOLATILE | C | UNAVAILABLE_PENDING_RULE | `volatility_measure_ref` + `decision_rule_ref` |
| EXPANDING / CONTRACTING | C | UNAVAILABLE + DEFERRED (generic) | per-dimension `target_measurement_ref` + comparison rule |
| HIGHER/LOWER_THAN_OWN_HISTORY | C | UNAVAILABLE_PENDING_RULE | `benchmark_methodology_ref` + decision rule |

## 4. `StateDimension` v0.2 (explicit rule references)

```text
StateDimension (PLANNED)
  dimension_id
  state
  state_class            A | B | C
  derivation_rule_ref    REQUIRED for Class B/C; null only for Class A
  benchmark_methodology_ref  REQUIRED for own-history Class C states
  tolerance_ref / volatility_measure_ref / decision_rule_ref  as applicable
  coverage_observation   a number + basis (NOT a sufficiency verdict)
  coverage_sufficiency_ref  REQUIRED to judge sufficiency; absent ⇒
                           COVERAGE_SUFFICIENCY_UNKNOWN
  missingness            per-dimension, never inherited
  measurement_refs       the observations used
  methodology_ref        the measurement methodology(ies) used
  valid_time / observed_at
  sensitivity_note       if the state flips under a reasonable rule variant
```

`state` and `state_class` are a closed enum pair, not free strings: an
unratified Class C state cannot be written to the field because its rule
identity does not exist.

## 5. Coverage: observation ≠ sufficiency (v0.1 defect repaired)

v0.1 asserted INCOMPLETE "below coverage floor" and 6D.1 asserted "coverage
floors enforced" — while no floor is ratified. v0.2 separates:

```text
COVERAGE_OBSERVATION      what fraction of the intended population was
                          observed, plus its basis
COVERAGE_SUFFICIENCY_RULE a ratified rule identity declaring what coverage is
                          sufficient FOR A GIVEN STATE METHODOLOGY
```

- Coverage 0.72 is observable; whether 0.72 is sufficient is a separate,
  rule-governed judgment.
- Without `coverage_sufficiency_ref`, no COMPLETE/INCOMPLETE verdict is
  derived from a percentage; the dimension carries
  `COVERAGE_SUFFICIENCY_UNKNOWN`.
- `PARTIAL_COVERAGE` (source-established) != `INSUFFICIENT_FOR_THIS_STATE`
  (methodology judgment). Never conflated without a ratified rule.
- Sufficiency may legitimately differ per state methodology. There is no
  global floor absent a ratified global floor rule.

## 6. Vector status: SCHEMA vs DATA (v0.1 defect repaired)

v0.1 said any `NOT_APPLICABLE` makes a vector INCOMPLETE. That is **wrong for
architecture-native modeling** (Axiom 1): a metric genuinely not applicable to
an architecture is a structural fact, not a defect. v0.2 uses two
**non-evaluative, structural** statuses:

```text
SCHEMA_COMPLETE   every slot in the subject's schema resolves to a state —
                  a derived state, any Class A state, or NOT_APPLICABLE.
                  No slot unresolved.

DATA_COMPLETE     every APPLICABLE slot has an observed derivation whose
                  coverage is sufficient under a ratified sufficiency rule
                  (or is a Class A state for a non-availability reason).
```

- A subject may be `SCHEMA_COMPLETE` and not `DATA_COMPLETE`; that is correct
  architecture-native behavior, not incompleteness.
- "complete" names **slot resolution only**. It never means good, high quality,
  healthy, or strong — no quality reading is permitted on these fields.
- No completeness score, percentage, or ordering exists.

## 7. Descriptive vs prescriptive boundary (unchanged, still binding)

Allowed vocabulary is exactly the Class A + ratified Class B/C lists above.
Prohibited (constitutional, §5.3a): ATTRACTIVE, STRONG_BUY, UNDERVALUED,
OVERVALUED, TOP_TIER, HIGH_QUALITY, WINNER, BEST, BUY, SELL, HEALTHY, STRONG,
ROBUST, PROMISING, INVESTABLE — and any composite, ranking, or target. v0.2 adds
no state name that could carry investment intent; `HEALTHY` remains prohibited
while D2-6 defers health parameters.

## 8. Derivation and replay (unchanged in principle, tightened)

A state is replayable only if `measurement_refs` + `methodology_ref` +
`derivation_rule_ref` (+ benchmark / tolerance / sufficiency refs as
applicable) + window all resolve. A state whose rule identity is absent cannot
be produced at all — the failure mode is a missing rule, not a default label.
Inputs going Book 2-non-current make the state recompute or resolve to a Class
A state; the R4/R5 "registered-then ≠ authoritative-now" discipline applies.

## 9. What v0.2 changes relative to v0.1 (delta)

| Area | v0.1 | v0.2 |
|---|---|---|
| Vocabulary property | "threshold-free" | withdrawn; rule-gated |
| State classes | none | A / B / C taxonomy |
| STABLE / VOLATILE | allowed, no rule | UNAVAILABLE_PENDING_RULE |
| EXPANDING / CONTRACTING | allowed, no target | UNAVAILABLE + DEFERRED (generic) |
| own-history states | allowed, implicit baseline | UNAVAILABLE; benchmark namespace + `benchmark_methodology_ref` |
| UNCHANGED | absent (STABLE used) | present, distinct from STABLE, per-class |
| Coverage | "coverage floor" (unratified) | observation vs sufficiency + `coverage_sufficiency_ref` |
| Vector status | COMPLETE/INCOMPLETE; NOT_APPLICABLE ⇒ incomplete | SCHEMA_COMPLETE / DATA_COMPLETE; NOT_APPLICABLE satisfies schema |
| Rule references | `methodology_ref` only | explicit `derivation_rule_ref`, `benchmark_methodology_ref`, tolerance/volatility/decision refs |

## 10. Verdict

```text
THRESHOLD_FREE_OVERCLAIM = WITHDRAWN
STATE_CLASSES = 3 (A availability / B specification-only / C threshold-benchmark)
CLASS_C_STATES = UNAVAILABLE_PENDING_RULE (explicit list in reconciliation §10)
HIDDEN_CUTOFF = NONE; HIDDEN_EPSILON = NONE; HIDDEN_BENCHMARK = NONE
COVERAGE_OBSERVATION != COVERAGE_SUFFICIENCY
VECTOR_STATUS = SCHEMA_COMPLETE / DATA_COMPLETE (non-evaluative)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
```
