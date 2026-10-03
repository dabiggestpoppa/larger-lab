# CSIA — Book 6 Comparison / Change: Implementation Authorization Review v0.4

**Status:** `HOLD` — REVIEW VERDICT, NOT AN AUTHORIZATION
**Date:** 2026-10-03
**Review kind:** post-ratification, independent re-run
**Ratification under review:** `BOOK6-COMPARE-SUBSTRATE-v0.2`
**Ratification commit:** `18ddfa2805ef8b51a1c46d5f11a34689a6abfd1b`
**Implementation branch audited:** `agent/crypto-systems-intelligence-atlas-book6-build` @ `5f94c3f40cea4441470c57671f51454da7377361`

**No architecture was changed in this review.** The review found a defect in the
ratified substrate; it did not repair it. Repairing it is an operator decision.

---

## 0. Verdict

```text
BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.4
    = HOLD

NO_UNRATIFIED_POLICY_NEEDED          = TRUE
NO_RUNTIME_AUTHORITY_GAP              = TRUE
NUMERIC_REPRESENTATION_SUFFICIENT     = TRUE
UNIT_ARITHMETIC_SOURCE_SUFFICIENT     = TRUE
BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT = NOT_SUPPORTABLE   <-- REGRESSION
COVERAGE_RUNTIME_PATH_SUFFICIENT      = TRUE
ALL_20_REPLAY_CHECKS_IMPLEMENTABLE    = NOT_SUPPORTABLE   <-- REGRESSION
NEGATIVE_SURFACE_TESTS_SPECIFIED      = TRUE
TRACEABILITY_PLAN_COMPLETE            = TRUE
UPSTREAM_FREEZE_PRESERVABLE           = TRUE

SCORE = 8 TRUE / 2 NOT_SUPPORTABLE
```

**Required: 10 / 10 TRUE. Achieved: 8 / 10. Verdict: HOLD.**

**No implementation authorization packet was created.** Phase 20 is
conditioned on 10 / 10 and the condition is not met. Creating a packet now would
be self-authorization by another name.

**This is a regression against review v0.3** (10 TRUE / 0 FALSE). The substrate
was not degraded between v0.3 and ratification — v0.3's verdict on the two
criteria below was **wrong**, and this independent re-run found it. v0.3 remains
in the record as the historical verdict that was reported at ratification time.

---

## 1. The defect (one root cause, two criteria)

### 1.1 The ratified ordering rule

Grammar v0.6 §2.4, ratified at `BOOK6-COMPARE-SUBSTRATE-v0.2`:

```text
 1. greatest valid_time END, strictly before comparison valid_time START
 2. if tied: greatest valid_time START
 3. if still tied: stable lexical measurement_ref   (final tie-break ONLY)
```

Steps 1 and 2 order on **window bounds**. The runtime fields carrying those
bounds are `MeasurementObservation.window_start` and
`MeasurementObservation.window_end`.

### 1.2 The accepted runtime forbids both fields for one window class

`MeasurementObservation._check_window_discipline`
(`book6_records.py:159-179`, accepted at `5f94c3f4`):

```text
if window_class in INTERVAL_WINDOW_CLASSES:
        window_start and window_end are REQUIRED (non-null)
else:
        if window_start is not None or window_end is not None:
                raise MeasurementRecordError(...)   # forbidden
```

`INTERVAL_WINDOW_CLASSES` (`book6_grammar.py:185-199`) contains **9 of the 10**
`WindowClass` members. The single excluded member is `INSTANTANEOUS`
(`book6_grammar.py:171`).

So for a `WindowClass.INSTANTANEOUS` observation, `window_end` is `None` and
`window_start` is `None` — **by validator**, not by omission.

### 1.3 That class is the runtime default, not an edge case

The canonical construction helpers at `book6_support.py:356` and `:393` both
default to:

```text
window_class: WindowClass = WindowClass.INSTANTANEOUS
```

and `book6_support.py:405-419` computes:

```text
interval         = window_class is not WindowClass.INSTANTANEOUS
window_start     = valid_time if interval else None
window_end       = valid_time + timedelta(days=1) if interval else None
```

No helper anywhere resolves effective window bounds for an instantaneous
observation. `window_end` appears outside `book6_records.py` exactly **once**,
on that constructor line, setting it to `None`.

### 1.4 The case is reachable

`book6_normalization.check_windows_comparable` (`book6_normalization.py:377-390`)
fails closed only when `current_window_class != prior_window_class`. Same-class
comparison — `INSTANTANEOUS` against `INSTANTANEOUS` — **passes**. Eligibility
condition 8 requires "same required WindowClass / window compatibility", so an
`INSTANTANEOUS` candidate is eligible, and the selector then has no END and no
START to order it by.

### 1.5 The package never addresses it

```text
$ grep -rn "INSTANTANEOUS" CSIA_BOOK_6_COMPARISON_CHANGE_*.md
(no output)
```

The word appears in **none** of the nine package artifacts, not in the
clarification, not in the grammar, not in plan v0.6, not in test spec v0.3. The
ratified package neither defines a resolution for this case nor excludes it.

### 1.6 Consequence

Implementation would have to invent one of the following, none of which is
ratified:

1. treat an instantaneous window as `[valid_time, valid_time)`;
2. treat it as `[valid_time, valid_time + 1day)` (the fixture convention at
   `book6_support.py:419`, which is a **fixture** convention, not ratified
   semantics);
3. exclude `INSTANTANEOUS` from baseline selection entirely — which would make
   the runtime's **default** window class un-comparable, a large semantic
   narrowing that is nowhere ratified;
4. refuse to compare instantaneous windows at all.

Each is a real semantic choice with different observable behaviour. Choosing one
inside an implementation session is exactly what the governance process exists
to prevent. **The review does not choose.**

---

## 2. Criteria affected

### 2.1 `BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT = NOT_SUPPORTABLE`

Every other eligibility field the ratified selector needs **exists** and was
verified on `MeasurementObservation` / `MetricDefinition` at `5f94c3f4`:

| Eligibility condition | Runtime field | Resolves? |
|---|---|---|
| same `subject_ref` | `subject_ref` (`book6_records.py:109`) | yes |
| same `metric_definition_ref` | `metric_definition_ref` (`:110`) | yes |
| metric-definition semantic fingerprint | derived from frozen `MetricDefinition` | yes |
| exact methodology `ref@version` | `methodology_ref` + `methodology_version` (`:118-119`) | yes |
| same exact `MetricDefinition.unit` | `unit` (`:114`) vs `MetricDefinition.unit` (`book6_definitions.py:148`) | yes |
| compatible denominator | `denominator: DenominatorRef \| None` (`:116`) | yes |
| compatible cohort | `native_scope` / `source_claim_refs` (`:124`) | yes |
| compatible `WindowClass` | `window_class` (`:122`) | yes |
| candidate `valid_time` strictly precedes | `valid_time` (`:117`) | yes |
| Book 2 authority current | `source_claim_refs` + Book 2 | yes |
| missingness satisfied | `missingness_state` (`:112`) | yes |
| **ordering key: window END** | **`window_end` — `None` for INSTANTANEOUS** | **NO** |
| **ordering key: window START** | **`window_start` — `None` for INSTANTANEOUS** | **NO** |

Eleven of eleven eligibility conditions resolve. Both **ordering** keys do not,
for the runtime's default window class. Determinism itself is unaffected
(`BASELINE_SELECTION_DETERMINISTIC = TRUE` still holds for interval windows) —
what fails is that there is no defined *rule* to follow for instantaneous ones.

### 2.2 `ALL_20_REPLAY_CHECKS_IMPLEMENTABLE = NOT_SUPPORTABLE`

Checks 5 and 6 are:

```text
 5. deterministic baseline candidate eligibility
 6. deterministic PRIOR_COMPARABLE_WINDOW resolution
```

Both execute the ordering rule. For an `INSTANTANEOUS` candidate, check 6 has
no defined resolution to compute. Test spec v0.3 contains no `INSTANTANEOUS`
ordering case, so the gap is **invisible to the ratified 237-case contract** —
`TEST_SPEC_BLOCKED = 0` does not cover it, and cannot, because the question was
never asked.

The remaining 18 checks resolve against accepted runtime symbols and ratified
governance.

---

## 3. Criteria that remain TRUE (independently re-verified)

```text
NO_UNRATIFIED_POLICY_NEEDED       = TRUE
NO_RUNTIME_AUTHORITY_GAP           = TRUE
NUMERIC_REPRESENTATION_SUFFICIENT  = TRUE
UNIT_ARITHMETIC_SOURCE_SUFFICIENT  = TRUE
COVERAGE_RUNTIME_PATH_SUFFICIENT   = TRUE
NEGATIVE_SURFACE_TESTS_SPECIFIED   = TRUE
TRACEABILITY_PLAN_COMPLETE         = TRUE
UPSTREAM_FREEZE_PRESERVABLE        = TRUE
```

**`NO_UNRATIFIED_POLICY_NEEDED`** — grammar v0.6 §8.2 carries the only policy
change: **P3 `unit_requirements` is WITHDRAWN** (`:416`). P1, P2, P4–P10 carry
unchanged (`:437`); no new policy parameter is introduced. The change is a
removal, which cannot create an unratified dependency. Verified by reading the
policy inventory rather than trusting the summary.

**`NO_RUNTIME_AUTHORITY_GAP`** — every governance decision routes through an
already-accepted registry or ledger: `CoverageRuleRegistry`
(`book6_coverage_rules.py:112`), `ComparisonRule` ratification (itself),
`Book6MethodologyRegistry` (`book6_methodology.py:178`), Book 2 for input
authority. No new registry, no new ratification path, no new authority class.
Verified by reading the four substrate anchors.

**`NUMERIC_REPRESENTATION_SUFFICIENT`** — GAP-1 `1A-STRICT` ratified:
`CANONICAL_VALUE = FINITE_STORED_BINARY64`, exact stored `==`,
`REAL_NUMBER_EXACTNESS_CLAIM = FALSE`, non-finite rejected to
`INSUFFICIENT_DATA`. `MeasurementObservation.value` is `float | None`
(`book6_records.py:113`) and needs no change. Sufficient.

**`UNIT_ARITHMETIC_SOURCE_SUFFICIENT`** — GAP-2 `2D` ratified:
`TEMPORAL_UNIT_COMPATIBILITY = SAME_METRIC_EXACT_UNIT_IDENTITY`. Source is
`MetricDefinition.unit`, non-nullable (`book6_definitions.py:148`); observation
side is `unit` (`book6_records.py:114`). No conversion machinery needed, no
dimensional ontology, no `UnitContract`. Sufficient.

**`COVERAGE_RUNTIME_PATH_SUFFICIENT`** — GAP-3 `3C` ratified.
`CoverageRuleRegistry` (`book6_coverage_rules.py:112`) exposes
`rules_for_metric` (`:215`), `ratification_of` (`:194`), `authorize` (`:227`)
and `ratify` (`:177`) — exactly the four operations the presence derivation and
the `REQUIRED` branch need. Sufficient, with **0 canonical rules ratified**, so
the derivation today yields `UNRESOLVED` — which is the ratified, fail-closed
outcome, not a gap.

**`NEGATIVE_SURFACE_TESTS_SPECIFIED`** — test spec v0.3 specifies **45**
negative-surface cases (9 field names × 5 attack vectors, `:198`, `:226`),
plus `BASE-2`–`BASE-5` reserved-selector rejection, `BASE-18` baseline-mismatch
rejection, and `AGGREGATE_ONLY = REJECTED` (`:99`). Genuinely specified.

**`TRACEABILITY_PLAN_COMPLETE`** — plan v0.6 carries gates **G-1** through
**G-14** (`:164-183`), including G-7 "20 checks individually traceable". The
gates cover zero-regression, contract count, no-epsilon, no-benchmark-namespace,
no-reserved-selector-implementation, no-`observed_at`-ordering, re-acceptance,
and the phantom-citation regression check. Complete.

**`UPSTREAM_FREEZE_PRESERVABLE`** — G-1 (Book 6 = 1341), G-2 (full CSIA =
2162), G-3 (Sensor unchanged), G-4 (Books 1–5 and Sensor mutation count = 0).
This amendment adds new Book 6 modules only; it modifies no frozen upstream.
Re-verified at `5f94c3f4`: accepted tree clean, exactly one commit past the
anchor, and that commit is the acceptance commit itself.

---

## 4. Naming normalizations recorded (not defects)

Recorded so that a later search matches either form.

| Governance term | Accepted runtime field | Note |
|---|---|---|
| `measurement_ref` (grammar v0.6 ordering tie-break; also `selected_baseline_measurement_ref`) | `MeasurementObservation.measurement_id` (`book6_records.py:108`) | same identity field; grammar uses the `*_ref` house style |
| `valid_time END` / `valid_time START` | `window_end` / `window_start` (`book6_records.py:120-121`) | **NOT a pure rename — see §1** |

---

## 5. Standing conditions carried forward (unchanged by this review)

1. **Aggregation HOLD case.** `aggregation == NONE` with multiple raw
   observations needing a new aggregation → implementation must HOLD the case
   and surface a concrete operator decision. (`SELECTOR_AGGREGATES = FALSE`.)
2. **Class C.** `DEFERRED / UNIMPLEMENTED / NOT A BLOCKER`.
   `BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED`.
3. **Reserved selectors.** `ROLLING_MEAN`, `ROLLING_MEDIAN`,
   `HISTORICAL_DISTRIBUTION`, `BASELINE_EPOCH` remain
   `RESERVED_NOT_EXECUTABLE`; construction or replay with any of them is
   REJECT, with no placeholder.

None of the three caused this HOLD.

---

## 6. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE

IMPLEMENTATION_AUTHORIZATION_PACKET = NOT CREATED  (condition 10/10 not met)
```

The ratification `BOOK6-COMPARE-SUBSTRATE-v0.2` stands and is **not** reversed
by this review. Ratification was a substrate-governance act; this is an
implementation-readiness verdict. The substrate remains ratified — one clause of
it is not yet implementable.

---

## 7. Options for the operator (this review chooses none)

Four resolutions are available. They are listed so the decision is cheap to
make, not so that it can be inferred. **Each is a real semantic choice with
different observable behaviour, and this review does not recommend one.**

| # | Resolution | Effect | Cost |
|---|---|---|---|
| A | Ratify that an instantaneous window orders as `[valid_time, valid_time)` (zero-width at the valid time) | END = START = `valid_time`; the existing three-step ordering works unchanged for all ten window classes | one grammar clause; zero runtime change; makes the fixture convention at `book6_support.py:419` **governance**, which it currently is not |
| B | Ratify that an instantaneous window orders as `[valid_time, valid_time + 1day)` | matches the existing fixture convention; END = `valid_time + 1day` | one grammar clause; asserts a 1-day width for a zero-width concept, which is semantically wrong for an instant |
| C | Ratify that `INSTANTANEOUS` candidates are **not eligible** for baseline selection | selector runs only on the nine interval classes | makes the runtime's **default** window class un-comparable; a large narrowing that would need its own justification |
| D | Ratify that comparisons involving an instantaneous window **refuse** (`INSUFFICIENT_DATA`) | strictest option | refuses a case the accepted runtime treats as ordinary |

A successor package (clarification v0.3, grammar v0.7) would carry the chosen
resolution, plus test-spec cases for it, after which this review re-runs.

**A note on option A.** It is the smallest change and the only one that leaves
the ordering rule untouched, but it must be ratified explicitly. It is precisely
the kind of "obvious reading" that this program has twice been burned by — the
phantom benchmark vocabulary was an obvious reading at the time. Ratifying the
obvious reading is the operator's call, not the reviewer's.

---

## 8. What this review did not do

```text
ARCHITECTURE CHANGED          = NONE
GRAMMAR_EDITED                = NONE
PLAN_EDITED                   = NONE
TEST_SPEC_EDITED              = NONE
RATIFICATION_RECORD_REVERSED  = NONE
SOURCE_CHANGED                = NONE
TEST_CODE_WRITTEN             = NONE
CLASS_C_DESIGNED              = NONE
CLASS_C_BENCHMARK_RULE        = NONE
COVERAGE_RULE_RATIFIED        = NONE
COMPARISON_RULE_RATIFIED      = NONE
```

The defect was **found and reported, not repaired**. Repairing it would require
inventing semantics the operator has not ratified, which is the specific failure
mode the governance process exists to prevent.
