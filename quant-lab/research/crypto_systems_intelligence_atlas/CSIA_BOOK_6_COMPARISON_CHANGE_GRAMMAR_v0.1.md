# CSIA — BOOK 6 COMPARISON / CHANGE GRAMMAR — v0.1

> **Status:** PLANNING / GOVERNANCE ONLY. Defines grammar and field-level
> contract shape. Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Authority under:** `D7N-7 = A` (`CHANGE_COMPARISON_OWNER = BOOK_6`) and
> `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.1.md`.
> **Deferred records:** 0 canonical `ComparisonRule`, 0 canonical
> `ChangeObservation` at ratification time.

---

## 1. The five-way separation

```text
MEASUREMENT
  != COMPARISON
  != CHANGE OBSERVATION
  != STATE
  != RESPONSE LINK
```

Each term is a different kind of object, answering a different question, with
a different owner and a different failure mode. Collapsing any adjacent pair
reintroduces the exact defect the response-semantics repair closed.

| Object | Question answered | Owner | Exists before the amendment? |
|---|---|---|---|
| `MeasurementObservation` | what was observed, at what valid time, under what methodology | Book 6 | yes (accepted) |
| `Comparison` | are two observations commensurable | Book 6 | **no — added** |
| `ChangeObservation` | what changed between a baseline and a later observation | Book 6 | **no — added** |
| `State` | what descriptive fundamental state holds, per a ratified rule | Book 6 | yes (accepted) |
| `ResponseLink` | is a change situated inside a declared window after an action | **Book 7** | yes (Book 7 planning) |

### 1.1 Why each boundary is load-bearing

- **`MEASUREMENT != COMPARISON`** — an observation exists whether or not
  anything is being compared to. Requiring a comparison would destroy the
  ability to record a first observation, a lone measurement, or a measurement
  that later turns out incomparable.
- **`COMPARISON != CHANGE OBSERVATION`** — comparability is a *gate*, not a
  result. Two observations can be comparable and produce no change record if
  the comparison methodology has not been bound. A passing gate is not a
  finding.
- **`CHANGE OBSERVATION != STATE`** — a change is arithmetic over two
  measurements; a state is the output of a separately ratified derivation
  rule. Emitting a state from a change would bypass D6M-3's centralized
  operator ratification entirely. **The amendment adds no state class.**
- **`CHANGE OBSERVATION != RESPONSE LINK`** — the ratified D7N-7 separation.
  Book 6 answers "what changed"; Book 7 answers "is that change positioned
  after an action". Book 6 has no concept of an action.

## 2. `ComparisonRule` (planned contract)

A versioned, operator-ratified methodology binding that authorises a specific
class of comparison. No implementation; field set is proposed for review.

```text
ComparisonRule {
  comparison_rule_id:              stable identifier
  version:                         integer; supersession, never mutation
  metric_definition_ref:           the metric this rule compares (required)
  baseline_selection_methodology_ref:   REQUIRED — a cited, ratified method
  comparison_methodology_ref:      REQUIRED — how baseline and comparison
                                    observations are combined
  compatible_methodology_refs:     explicit allow-list of measurement
                                    methodologies compatible with this rule
  unit_requirements:               required unit / dimensional class
  denominator_requirements:        required denominator semantics
  cohort_requirements:             required cohort definition, where relevant
  window_compatibility:            required window class and comparability rule
  coverage_requirements:           minimum comparable coverage
  missingness_requirements:        permitted missingness state
  output_semantics:                which output fields this rule may populate
  valid_time:                      bitemporal (valid_from / valid_to)
  observed_at:                     knowledge time
  status:                          DRAFT | RATIFIED | SUPERSEDED | WITHDRAWN
  generated_from / fingerprints:   content fingerprint over all semantic
                                    fields (Book 6 fingerprint doctrine)
  supersedes:                      previous version, when applicable
}
```

### 2.1 ComparisonRule governance

```text
NO FREE-STRING COMPARISON AUTHORITY
   — a comparison cites a ComparisonRule ref plus a version; a bare string,
     alias, or substring never authorises a comparison.

SELF-AUTHORIZATION REJECTED
   — a caller may not create the rule it then invokes. Ratification is
     centralized operator action, exactly as for StateRule (D6M-3 = A).

MUTATED CONTENT UNDER SAME IDENTITY REJECTS
   — any change to a semantic field changes the content fingerprint and
     requires a new version. This is the Book 6 methodology fingerprint
     doctrine applied to a new class.

SUPERSESSION DOES NOT INHERIT
   — ComparisonRule v2 does not inherit v1's ratification, and a v1-cited
     comparison does not silently run under v2. Callers re-resolve current
     authority at use time.

BOOK 7 MAY NOT CREATE ONE
   — a ComparisonRule is a Book 6 object. Book 7 cites it; it cannot author,
     extend, or locally override it.
}
```

### 2.2 Why baseline selection lives inside the rule, not beside it

Baseline selection is the single most consequential choice in any comparison:
"the value immediately before the event", "the same window last quarter", and
"the declared reference period" can produce different directions from
identical data. Putting selection *inside* the ratified rule means the choice
is versioned, fingerprinted, and attributable — rather than an implicit
property of whoever happened to run the query.

## 3. `ChangeObservation` (planned contract)

A Book 6-local derived record. **Not a Book 2 claim. Not a state.**

```text
ChangeObservation {
  change_observation_id:           stable identifier
  subject_ref:                     the subject the change is about
  axis:                            MEASUREMENT_CHANGE (Book 6 does not know
                                    USAGE or CAPITAL as semantic axes; those
                                    are Book 7's labels over a generic change)
  metric_definition_ref:           required
  comparison_rule_ref:             REQUIRED — cites the governing rule + version
  baseline_measurement_refs:       one or more; non-empty
  comparison_measurement_refs:     one or more; non-empty
  absolute_delta:                  present only where defined
  relative_delta:                  present only where defined
  change_kind:                     INCREASE | DECREASE | NO_CHANGE |
                                    CHANGE_UNDEFINED | NOT_COMPARABLE |
                                    INSUFFICIENT_DATA
  unit:                            the unit of the emitted deltas
  source_measurement_refs:         full set of underlying observation refs
  measurement_methodology_refs:    methodologies of the underlying observations
  coverage:                        coverage state of the inputs
  missingness:                     missingness state of the inputs
  comparability_status:            COMPARABLE | NOT_COMPARABLE
  valid_time:                      bitemporal; the change's valid interval
  observed_at:                     knowledge time
  status:                          DRAFT | RATIFIED | SUPERSEDED
}
```

### 3.1 ChangeObservation invariants

```text
CO-1  NOT_A_BOOK2_CLAIM — no claim-store write, no promotion path, no
      epistemic authority. It is a derived measurement record.
CO-2  NO_EVENT_SEMANTICS — no narrative, action, response, window, or
      causality fields exist on this object.
CO-3  NO_GOODNESS — no materiality, significance, health, merit, or
      recommendation field exists on this object.
CO-4  DERIVABLE — every emitted value must be reproducible from the cited
      refs and the cited rule version. A value that cannot be recomputed is
      a defect, not a result.
CO-5  FAIL_CLOSED — when any input is missing, incomparable, or undefined, the
      change_kind states that fact and the numeric fields are absent. Absent
      is not zero.
CO-6  IMMUTABLE_HISTORY — a corrected comparison is a new ChangeObservation
      (or a new rule version plus new record); prior records are superseded,
      never overwritten.
CO-7  NOT_A_STATE — a ChangeObservation never becomes a StateDimension, a
      FundamentalStateVector component, or any state output.
}
```

## 4. Baseline selection methodology

Baseline selection **is** methodology. There is no default, no fallback, and
no implicit "last value before the event".

```text
ResponseBaseline / ComparisonBaseline (planned) {
  baseline_ref:                    the selected baseline record(s)
  subject_ref:                     required
  metric_definition_ref:           required
  baseline_window:                 explicit valid-time window
  methodology_ref:                 REQUIRED — how the window's summary is formed
  selection_methodology_ref:       REQUIRED — how the baseline was chosen
  unit:                            required
  denominator_identity:            required where the metric has a denominator
  cohort_ref:                      required where the metric is cohort-scoped
  source_book:                     the owning book of the baseline measurement
}
```

### 4.1 Candidate baseline families (none default)

| Family | Description | Typical fit | Hazard |
|---|---|---|---|
| `IMMEDIATE_PRIOR_COMPARABLE` | nearest prior observation satisfying comparability | fast-moving usage counters | noise; a single anomalous point becomes the reference |
| `PRE_EVENT_WINDOW_SUMMARY` | aggregate over a window preceding the action | noisy series needing smoothing | window choice drives the result |
| `MATCHED_CALENDAR_WINDOW` | same window in a prior comparable period | seasonal protocols, recurring cycles | assumes seasonality exists |
| `DECLARED_REFERENCE_PERIOD` | an operator-declared reference period | benchmarks, pre-agreed baselines | requires governance to declare it |

```text
NO UNIVERSAL DEFAULT BASELINE
BASELINE_UNAVAILABLE is a first-class outcome — never a substituted value
The selection methodology is cited on the record; the chosen family is
  never inferable after the fact
Book 6 receives the requested valid-time window as CONTEXT; it never learns
  why the window was chosen
```

## 5. Comparability gates

A comparison is valid only when **every** applicable gate passes. Any failure
yields `NOT_COMPARABLE` and no delta.

| # | Gate | Failure outcome |
|---|---|---|
| G1 | metric definition identity compatible | `NOT_COMPARABLE` |
| G2 | measurement methodology in the rule's allow-list | `NOT_COMPARABLE` |
| G3 | unit / dimensional class compatible | `NOT_COMPARABLE` |
| G4 | denominator semantics compatible | `NOT_COMPARABLE` |
| G5 | cohort definition compatible | `NOT_COMPARABLE` |
| G6 | window class compatible under the rule | `NOT_COMPARABLE` |
| G7 | coverage valid for the rule's minimum | `NOT_COMPARABLE` |
| G8 | missingness within permitted states | `NOT_COMPARABLE` |
| G9 | valid temporal ordering (baseline valid-time precedes comparison) | `NOT_COMPARABLE` |

```text
NO FABRICATED DELTA FROM A FAILED GATE
NO BOOK 7 NORMALIZATION — Book 6 remains the sole normalization authority
  (D6M-2), and comparison consumes already-valid values
COMPARABLE != CHANGED — passing all nine gates authorises a comparison; it
  does not assert that any change exists
```

## 6. Change semantics

```text
INCREASE             — defined and the comparison value is greater
DECREASE             — defined and the comparison value is lesser
NO_CHANGE            — defined and the comparison value is equal
CHANGE_UNDEFINED     — comparison is sound but the metric's change is not
                       arithmetically defined (e.g. a ratio crossing a
                       singular point)
NOT_COMPARABLE       — one or more comparability gates failed
INSUFFICIENT_DATA    — inputs exist but cannot support the comparison
```

### 6.1 Prohibited change semantics

```text
MATERIAL_CHANGE          — not permitted; requires its own governance
SIGNIFICANT_CHANGE       — not permitted; requires a statistical methodology
GOOD_CHANGE              — prohibited permanently under the anti-score firewall
BAD_CHANGE               — prohibited permanently
HEALTHY_CHANGE           — prohibited; D6M-5 remains OPEN_DEFERRED
ADOPTION_SUCCESS_CHANGE  — prohibited; D6M-5 remains OPEN_DEFERRED
IMPROVING / DETERIORATING — prohibited; goodness is not a measurement output
```

A future operator decision could ratify a *materiality* methodology. It could
never ratify `GOOD_CHANGE` / `BAD_CHANGE` — those are judgments, and the
constitution's descriptive-before-prescriptive boundary (§5.3a) forecloses
them structurally, not merely by policy.

## 7. Numeric change semantics

Where the arithmetic is defined:

```text
absolute_delta = comparison_value - baseline_value
relative_delta = (comparison_value - baseline_value) / baseline_value
```

| Situation | `absolute_delta` | `relative_delta` | `change_kind` |
|---|---|---|---|
| baseline > 0, both present, comparable | emitted | emitted | `INCREASE` / `DECREASE` / `NO_CHANGE` |
| baseline = 0 | emitted | **absent — fail closed** | as above |
| baseline < 0 (valid for some metrics) | emitted | emitted, with sign semantics declared by the rule | as above |
| baseline absent (`BASELINE_UNAVAILABLE`) | absent | absent | `INSUFFICIENT_DATA` |
| comparison observation absent | absent | absent | `INSUFFICIENT_DATA` |
| units incompatible | absent | absent | `NOT_COMPARABLE` |
| temporal order invalid | absent | absent | `NOT_COMPARABLE` |
| coverage / missingness invalid | absent | absent | `NOT_COMPARABLE` |

```text
ZERO_BASELINE_RELATIVE_DELTA = FAIL_CLOSED (never 0, never inf, never NaN)
MISSING_BASELINE            != ZERO
MISSING_POST_DATA           != ZERO
ZERO_VALUE                  != ZERO_CHANGE
NO_HIDDEN_CURRENCY_CONVERSION — value comparison occurs in a declared unit;
  cross-unit comparison requires an explicit, cited conversion methodology and
  is out of scope for this amendment
ABSENT NUMERIC FIELD        != 0 — absence is represented by the absent field
  plus an explicit change_kind, never by a zero value
```

## 8. Methodology sensitivity

Different legitimate baseline or comparison methodologies can produce
different `ChangeObservation` records from identical source measurements. This
is not an error; it is a property of the domain.

```text
MS-1  Parallel records are PRESERVED. Two rules, two ChangeObservations, both
      retained with their rule refs.
MS-2  NEVER AVERAGED. There is no averaging across methodologies.
MS-3  NEVER SILENTLY SELECTED. No "preferred" flag, no default rule, no
      tie-break that hides a disagreement.
MS-4  DISAGREEMENT IS VISIBLE. When two legitimate methods disagree on
      direction, both directions are published; the disagreement is a fact
      about method sensitivity, not a defect to be resolved silently.
MS-5  CONSUMERS MUST CITE. A downstream consumer — including every Book 7
      ResponseLink — must cite the exact ChangeObservation and
      ComparisonRule it relied upon. A consumer may not say "there was a
      change" without naming the method that found it.
```

This is the same discipline Book 6 already applies to `MeasurementMethodology`
content fingerprints and to the deferred-state fail-closed posture, extended
to a new contract class.

## 9. Ownership boundary restated

```text
Book 6 owns:  measurement; comparison; comparability truth; baseline
              selection methodology; numeric delta; direction derivation;
              measurement normalization (D6M-2)
Book 7 owns:  event identity; action identity; response-window declaration;
              the descriptive linkage from an accepted ChangeObservation to
              an action
Neither owns: causal inference; materiality; health; investment merit
```

---

*End of grammar. Planning artifact; no contract here is implemented or
ratified.*
