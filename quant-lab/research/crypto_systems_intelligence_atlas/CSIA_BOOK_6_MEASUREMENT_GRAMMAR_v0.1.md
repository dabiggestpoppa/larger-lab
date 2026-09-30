# CSIA — BOOK 6 MEASUREMENT GRAMMAR AND RECORD CONTRACTS v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Scope:** Phases 3–10 — grammar, observation record, metric definition,
> denominator doctrine, window doctrine, missingness, revision/restatement,
> methodology identity.
> **Grants no implementation authority.**

---

## 1. Grammar first, names later

A metric name is a label. The grammar is the contract. Book 6 defines the
grammar before any metric exists, so that "active addresses" cannot enter the
system as an undefined word.

### 1.1 The terms (each distinct, none collapsible)

| Term | Definition | Not to be confused with |
|---|---|---|
| **RAW OBSERVATION** | what a source reported, uninterpreted, in the source's own terms | a metric |
| **MEASUREMENT** | a raw observation bound to a definition, unit, window, and method | a raw reading |
| **METRIC** | a named, defined, versioned measurement concept (e.g. "fees paid per transaction") | a value |
| **DERIVED METRIC** | a metric computed from other metrics under a stated formula | a raw metric |
| **NORMALIZED METRIC** | a derived metric transformed for comparison under a stated normalization rule | a raw metric |
| **RATE** | value per unit time (flow ÷ time) | a stock |
| **RATIO** | dimensionless quotient of two like quantities | a rate |
| **COUNT** | cardinality of a population defined by an identity rule | a sum of values |
| **STOCK** | quantity held at an instant | a flow |
| **FLOW** | quantity accumulated over a window | a stock |
| **DISTRIBUTION** | the shape of values across a population (quantiles, spread) | a mean |
| **INDEX** | a dimensionless composite of standardized components | a metric |
| **STATE DIMENSION** | one named axis of descriptive state (e.g. activity) | a state vector |
| **STATE VECTOR** | the full set of state dimensions for a subject, never weighted into one number | a score |
| **BENCHMARK** | a reference observation for context, itself versioned and defined | a threshold |
| **COHORT** | an explicit, versioned set of subjects eligible for comparison | "all subjects" |
| **METHODOLOGY** | the versioned identity of how a value was produced (formula, window, filters, denominator, sources) | a note |
| **DENOMINATOR** | the named divisor, with its own identity and missingness | an implicit constant |
| **COVERAGE** | the fraction of the intended population actually observed, with its own basis | a confidence score |
| **MISSINGNESS** | the state describing why a value is absent or partial | zero |
| **UNCERTAINTY** | the declared epistemic spread of a value under its methodology | missingness |

### 1.2 The core separations

```text
OBSERVATION   != MEASUREMENT   (an observation has no definition binding)
MEASUREMENT   != METRIC        (a measurement is an instance; a metric is the definition)
METRIC        != NORMALIZATION (normalization is a transformation, always a separate act)
NORMALIZATION != STATE         (state is derived from measurements + rules, not from a transform)
RAW           != DERIVED       (derivation is recorded, never silent)
STOCK         != FLOW          (instant vs window)
RATE          != RATIO         (time-bearing vs dimensionless)
COUNT         != SUM           (cardinality vs aggregation)
DISTRIBUTION  != CENTRAL_TENDENCY
```

**No "normalized metric" may exist without a preserved native measurement**
(Axiom 1: normalization occurs only after native truth is preserved).

## 2. `MeasurementObservation` (planned contract — NOT implemented)

The canonical record of one measured value for one subject, under one
methodology, over one window.

```text
MeasurementObservation (PLANNED, not implemented)
  measurement_id        identity of this observation instance
  subject_ref           the thing measured (Book 1 object/deployment identity)
  metric_definition_ref the MetricDefinition it is an instance of
  value                 the measured value, in `unit`; ABSENT when missingness != OBSERVED
  unit                  the unit of `value` (native unit; never implicit)
  numerator_ref         optional explicit numerator (for ratios/rates), with its own observation
  denominator_ref       optional explicit denominator, with its own observation + missingness
  valid_time            when the value is true of the subject (bitemporal, Book 1)
  observed_at           when the source reported it
  window_start          window semantics (see §5)
  window_end
  methodology_ref       the versioned methodology identity (see §7)
  source_claim_refs     Book 2 authority for the inputs (required to assert a value)
  coverage              the observed fraction of the intended population + its basis
  missingness_state     one of the missingness states (§6)
  quality_flags         typed flags (e.g. partial coverage, late data, est. method)
  native_scope          the architecture/protocol family this value is native to
  status                OBSERVED | SUPERSEDED (never overwritten; see §8)
  supersedes_ref        explicit link when this is a revision
```

### 2.1 Mandatory fields by metric class

Mandatory is **resolved by class**, not blanket:

| Field | native count/rate | ratio/rate | stock/flow value | normalized metric | state dimension input |
|---|---|---|---|---|---|
| `value` + `unit` | required (when observed) | required | required | required | n/a (derived) |
| `numerator_ref` | n/a | required | n/a | required if derived | n/a |
| `denominator_ref` | n/a | required | n/a | required if derived | n/a |
| `coverage` | required | required | required | required | required |
| `missingness_state` | required | required | required | required | required |
| `methodology_ref` | required | required | required | required | required |
| `source_claim_refs` | required | required | required | required (chains to native) | required |
| `native_scope` | required | required | required | required | required |
| `window_start`/`end` | required for any windowed metric | required | required | required | required |

`value` is present **only** when `missingness_state = OBSERVED` or
`ZERO_OBSERVED`. A record cannot carry a value with a non-observed
missingness state, and cannot carry an observed state with no value (Axiom 6).

## 3. `MetricDefinition` (planned contract — NOT implemented)

```text
MetricDefinition (PLANNED, not implemented)
  metric_id
  name
  semantic_definition     a sentence a careful reader can audit, not a label
  subject_domain          what may be a subject of this metric (chain/protocol/token/capital/developer)
  measurement_type        COUNT | RATE | RATIO | STOCK | FLOW | DISTRIBUTION | INDEX | SCALAR-QUANTITY
  unit                   the unit (or unit-of-analysis); never implied
  native_or_normalized    NATIVE | NORMALIZED
  window_semantics        which window class (§5) is legal
  aggregation_semantics   how repeated observations aggregate (sum? mean? none? last?)
  denominator_semantics   the named denominator rule, or NOT_APPLICABLE
  allowed_source_families which source classes may back this metric
  required_evidence       the Book 2 evidence tier floor
  methodology_version     the methodology identity this definition pins
  comparability_class     the cohort family within which it is comparable (§6B)
  applies_to_architectures which architecture families it is native to (else NOT_APPLICABLE)
```

### 3.1 A name is not a definition

"Active addresses" is **incomplete** until it answers: active by what action?
over what window? unique by what identity rule? native chain accounts only or
also contract-generated addresses? sybil-sensitive? Which of these are
definition fields (mandatory) vs methodology (versioned)? The split is:
**what is being counted** belongs to `semantic_definition`; **how it is counted
at a point in time** belongs to the methodology version. Both are mandatory;
neither may live in the name.

## 4. Denominator doctrine (first-class)

Every ratio/rate/normalization names its denominator explicitly. The denominator
is a first-class subject with its own identity, its own observation, and its own
missingness. It is never a constant, never implicit, never inline.

### 4.1 Denominator states (distinct)

```text
DENOMINATOR_PRESENT      a real observed denominator exists
DENOMINATOR_ZERO         the denominator is observed and equals zero
DENOMINATOR_UNKNOWN      the denominator's identity or value is not determined
DENOMINATOR_NOT_APPLICABLE the metric has no denominator by definition
DENOMINATOR_UNAVAILABLE  the denominator should exist for this subject but its source is unavailable
DENOMINATOR_UNSTABLE     the denominator's value is contested/stale (Book 2 non-current)
```

### 4.2 Rules

1. **Never divide through missingness.** A ratio with an unknown/unavailable
   denominator is not a ratio; it is `NOT_AVAILABLE`. Division by
   `DENOMINATOR_UNKNOWN` is a structural failure.
2. **`DENOMINATOR_ZERO` is not a number.** A ratio with an observed-zero
   denominator is `UNDEFINED_RATIO` (Axiom 6: zero and missing differ). It is
   not zero, not infinity-as-a-value, not dropped.
3. **Never silently change the denominator across time.** A denominator whose
   identity changed between windows makes the two ratios non-comparable
   (`NOT_COMPARABLE_DENOMINATOR_CHANGED`), even if both are individually valid.
4. **The denominator is itself measured.** It is a `MeasurementObservation`
   with the same grammar; it is not a bare number in a formula.

Examples bound to doctrine: "transactions per day" (denominator = window
length + block inclusion rule); "fees per transaction" (denominator =
transaction identity rule, which differs per chain); "revenue per active user"
(denominator = user identity rule, sybil-sensitive); "stablecoin supply share"
(denominator = the comparison set, which is a cohort, not a global); "borrow
utilization" (denominator = supplied principal, not deposits, not TVL);
"validator concentration" (denominator = validator set under a
counting rule — entities vs keys vs seats).

## 5. Window / time doctrine

### 5.1 Window classes

```text
INSTANTANEOUS     a point in valid time (stock)
BLOCK/EPOCH        per block/slot/epoch (chain-native; length varies by family)
DAILY              calendar day (timezone declared)
ROLLING            trailing N of a declared unit (e.g. trailing 7d)
CALENDAR_WEEK      ISO or declared week convention
CALENDAR_MONTH     calendar month (declared timezone)
QUARTER            calendar quarter
LIFETIME           since a declared origin event
EVENT_BOUNDED      bounded by two events (e.g. deployment -> deprecation)
CUSTOM             explicitly parameterized; must be declared, never implicit
```

### 5.2 Per-metric time requirements (all explicit)

For every metric: `valid_time` (when true), `observed_at` (when reported),
`window_start`/`window_end`, the **calendar/timezone convention**, the
**late-data behavior**, and the **revision behavior** are mandatory. "Monthly
activity" is not a metric until the month boundary, timezone, late-block
policy, and revision policy are stated.

- **Timezone:** a calendar-day metric declares its timezone; chains with
  block-time cadence declare block/epoch instead of forcing calendar days.
- **Late data:** late blocks/indexer lag extend or revise the window; the
  behavior (extend window vs supersede) is declared per methodology.
- **Revision:** restatements supersede, never overwrite (§8).

## 6. Missingness model

Book 6 inherits Axiom 6 (`missing != false`) and extends it. Candidate missingness
states (stressed in the validation matrix before any name is ratified):

```text
OBSERVED             a value was observed
ZERO_OBSERVED        a value of zero was observed (genuinely zero, not missing)
NOT_APPLICABLE       the metric does not apply to this subject (e.g. per-transaction fee on a chain with no per-transaction fee)
NOT_SUPPORTED        the architecture/protocol does not expose this measurement at all
NOT_AVAILABLE        it could apply but the source is unavailable
NOT_COLLECTED        it could apply and was not collected in this window
SOURCE_UNAVAILABLE   the specific source backing it is down/absent
STALE                a prior value exists but is past its freshness bound
PARTIAL_COVERAGE     a value exists but coverage < the methodology's floor
UNKNOWN              we do not know the missingness state itself
```

Key separations, to be stress-tested before ratification:

```text
"0 active users"      != "no active-user data"      (ZERO_OBSERVED != NOT_COLLECTED)
"no per-tx fee"       != "per-tx fee was 0"         (NOT_APPLICABLE != ZERO_OBSERVED)
"we didn't look"      != "looked, found nothing"     (NOT_COLLECTED != OBSERVED zero)
"chain has no concept of this" != "we couldn't read it"  (NOT_SUPPORTED != SOURCE_UNAVAILABLE)
```

**No state collapses into another.** A dimension with a non-observed
missingness state resolves to `INSUFFICIENT_DATA`, never to zero or to
"declining".

## 7. Methodology identity

```text
MeasurementMethodology (PLANNED, not implemented)
  methodology_id
  version
  formula
  parameters            (typed; e.g. sybil-filter cutoffs, wash-filter rules)
  window_rule           (the window class + parameters)
  filters               (typed inclusion/exclusion)
  denominator_rule      (the denominator identity rule)
  source_selection      (which source classes, tie-break order)
  normalization_rule    (if normalized; the transform)
  identity_rule         (how subjects are counted — the unit of "user", "address", "validator")
```

**A metric value without methodology identity is incomplete.** The same metric
name under a different methodology is a **different comparable observation**;
it is not a revision of the first and not automatically comparable to it
(`NOT_COMPARABLE_METHODOLOGY`). Methodology change creates a new
methodology_id version and a superseding observation with an explicit
restatement reason — history is preserved.

## 8. Revision / restatement model

A measurement may be revised after: late blocks, indexer correction, source
backfill, methodology change, chain reorg, or protocol accounting correction.

Rules:

1. **Never overwrite historical measurement truth.** A revision emits a new
   observation with `status = OBSERVED`, `supersedes_ref` = prior observation,
   and an explicit `restatement_reason` from the closed set
   {LATE_BLOCKS, INDEXER_CORRECTION, SOURCE_BACKFILL, METHODOLOGY_CHANGE,
   CHAIN_REORG, PROTOCOL_ACCOUNTING_CORRECTION}.
2. The prior observation is retained with `status = SUPERSEDED` and stays
   queryable (Book 1 bitemporal truth; Book 5 flow-ledger precedent).
3. A methodology change produces a *new methodology version* and a superseding
   observation; it does not relabel the old value.
4. A reorg revision is time-bounded to the reorged window; windows outside the
   reorg are untouched.
5. Derived metrics and states recompute from the current observation set; the
   recomputation is itself recorded (a state/derived observation supersedes its
   prior instance), never silently in place.

## 9. Cross-references to accepted doctrine

- Axiom 1 — native before normalized: preserved native measurement is a
  precondition of any normalized metric (grammar, §1.2; normalization, later
  doc).
- Axiom 5 — time is part of truth: valid time + window + revision (§5, §8).
- Axiom 6 — missing is not false: missingness states (§6); denominator states
  (§4.1).
- Axiom 7 — discovery ≠ promotion: a source is not a metric; a raw observation
  is not a measurement (§1).
- Axiom 8 — descriptive before predictive: the grammar contains no forecast
  class; state is descriptive (state-vector doc).
- §5.3a descriptive/prescriptive: no score, no ranking, no target in the
  grammar; the measurement record has no "attractiveness" field.
- Book 5 v0.3 §4: common-value products (numeraire, price) are Book 6
  measurement products, never Book 5 fields; `SHARE FRACTION != VALUATION`.

## 10. Grammar verdict

```text
MEASUREMENT_GRAMMAR = DEFINED (draft)
DENOMINATOR_DOCTRINE = FIRST_CLASS
WINDOW_DOCTRINE = EXPLICIT
MISSINGNESS_MODEL = DISTINCT_STATES
METHODOLOGY_IDENTITY = REQUIRED
REVISION_MODEL = SUPERSESSION_NOT_OVERWRITE
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

No term collapses into another. No metric name carries undocumented semantics.
No record may assert a value without Book 2 authority, a unit, a window, and a
methodology.
