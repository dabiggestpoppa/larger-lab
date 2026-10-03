# CSIA — Book 6 Comparison/Change: Implementation Authorization Review v0.5

**Status:** `READY_PENDING_GAP6_RATIFICATION` — REVIEW VERDICT, NOT AN
AUTHORIZATION
**Date:** 2026-10-03
**Supersedes as a review:** `..._AUTHORIZATION_REVIEW_v0.4.md` (HOLD, 8 TRUE / 2
NOT_SUPPORTABLE) and v0.3 (10 TRUE / 0 FALSE). Both preserved as history.
**Implementation branch audited:** `agent/crypto-systems-intelligence-atlas-book6-build`
@ `5f94c3f40cea4441470c57671f51454da7377361`

**Architecture was not changed in this review.** The review re-ran the ten
criteria against accepted runtime, the ratified v0.6 substrate, and the **draft**
GAP-6 clarification.

---

## 0. Verdict

```text
BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.5
    = READY_PENDING_GAP6_RATIFICATION

NO_UNRATIFIED_POLICY_NEEDED          = TRUE
NO_RUNTIME_AUTHORITY_GAP              = TRUE
NUMERIC_REPRESENTATION_SUFFICIENT     = TRUE
UNIT_ARITHMETIC_SOURCE_SUFFICIENT     = TRUE
BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT = TRUE
COVERAGE_RUNTIME_PATH_SUFFICIENT      = TRUE
ALL_20_REPLAY_CHECKS_IMPLEMENTABLE    = TRUE
NEGATIVE_SURFACE_TESTS_SPECIFIED      = TRUE
TRACEABILITY_PLAN_COMPLETE            = TRUE
UPSTREAM_FREEZE_PRESERVABLE           = TRUE

SCORE = 10 TRUE / 0 FALSE
```

**Upgraded from v0.4's 8 / 2.** The two criteria that were `NOT_SUPPORTABLE` are
now supported by the GAP-6 draft.

---

## 1. What changed since v0.4

| Criterion | v0.4 | v0.5 | Why |
|---|---|---|---|
| `BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT` | NOT_SUPPORTABLE | **TRUE** | the ordering keys now resolve for every `WindowClass` member |
| `ALL_20_REPLAY_CHECKS_IMPLEMENTABLE` | NOT_SUPPORTABLE | **TRUE** | checks 5 and 6 have a defined resolution for every eligible shape |
| other eight | TRUE | TRUE | unchanged |

The eight unchanged criteria were **re-verified**, not carried forward on trust —
see §2.

### 1.1 An honest qualifier on the upgrade

Both criteria are supported **conditional on GAP-6 being ratified**. The
clarification, grammar v0.7, plan v0.7 and test spec v0.4 are all
`DRAFT_PENDING_OPERATOR_RATIFICATION`. If the operator declines GAP-6, these two
criteria revert to `NOT_SUPPORTABLE` and the verdict reverts to HOLD.

```text
CONDITIONAL_ON_GAP6_RATIFICATION = TRUE
GAP6_RATIFIED                    = FALSE
```

---

## 2. The two upgraded criteria

### 2.1 `BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT = TRUE`

Re-verified field by field against `5f94c3f4`. GAP-6 changes nothing about which
fields exist; it changes whether the **ordering keys** have a value.

| Requirement | Runtime resolution | Status |
|---|---|---|
| same `subject_ref` | `book6_records.py:109` | resolves |
| same `metric_definition_ref` | `:110` | resolves |
| metric-definition fingerprint | frozen `MetricDefinition` | derives |
| exact methodology `ref@version` | `methodology_ref` + `methodology_version` `:118-119` | resolves |
| same exact `MetricDefinition.unit` | `:114` vs `book6_definitions.py:148` | resolves |
| compatible denominator | `:116` | resolves |
| compatible cohort | `native_scope` `:124` | resolves |
| compatible `WindowClass` | `window_class` `:122`; asserted by `validate_against_definition` `:251-256` | resolves |
| candidate strictly precedes | `valid_time` `:117`; effective keys via GAP-6 | **resolved by GAP-6** |
| Book 2 authority current | `source_claim_refs` `:123` | resolves |
| missingness satisfied | `missingness_state` `:112` | resolves |
| **ordering key: END** | `window_end` `:121` **or** `valid_time` via projection | **resolved by GAP-6** |
| **ordering key: START** | `window_start` `:120` **or** `valid_time` via projection | **resolved by GAP-6** |
| tie-break key | `measurement_id` `:108` | resolves |
| record state | `status` `:129`, enum `book6_grammar.py:264-272` | resolves |

```text
UNRESOLVED_REMAINING = 0
```

Every ordering key now has a defined value for **every** `WindowClass` member.
The projection is total over the closed enum, so there is no shape for which the
selector lacks a key.

### 2.2 `ALL_20_REPLAY_CHECKS_IMPLEMENTABLE = TRUE`

Checks 5 and 6 execute the ordering. Under v0.6 they had no resolution for
`WindowClass.INSTANTANEOUS`; grammar v0.7 §1.1–§1.2 supplies one. The remaining
18 checks were re-verified against accepted symbols and ratified governance.

```text
REPLAY_CHECK_COUNT                 = 20
ALL_20_INDEPENDENTLY_FALSIFIABLE   = TRUE
CHECKS_5_AND_6_IMPLEMENTABLE       = TRUE   (was NOT_SUPPORTABLE in v0.4)
```

---

## 3. The eight unchanged criteria — re-verified

**`NO_UNRATIFIED_POLICY_NEEDED = TRUE`** — grammar v0.6 §8.2: only policy change
is P3 `unit_requirements` **withdrawn** (a removal). P1, P2, P4–P10 unchanged.
GAP-6 introduces **no** policy parameter at all:
`NEW_POLICY_PARAMETERS_FROM_GAP6 = 0`. A removal cannot create a dependency, and
adding nothing cannot create one.

**`NO_RUNTIME_AUTHORITY_GAP = TRUE`** — every decision routes through accepted
surface: `CoverageRuleRegistry` (`book6_coverage_rules.py:112`),
`ComparisonRule` ratification (itself), `Book6MethodologyRegistry`
(`book6_methodology.py:178`), Book 2. GAP-6 adds **no** registry, ratification
path, or authority class, and needs none.

**`NUMERIC_REPRESENTATION_SUFFICIENT = TRUE`** — GAP-1 `1A-STRICT` untouched.
`FINITE_STORED_BINARY64`, exact stored `==`, non-finite → `INSUFFICIENT_DATA`.
`value: float | None` (`:113`) unchanged.

**`UNIT_ARITHMETIC_SOURCE_SUFFICIENT = TRUE`** — GAP-2 `2D` untouched.
`MetricDefinition.unit` non-nullable (`book6_definitions.py:148`). Untouched by
GAP-6, which is temporal.

**`COVERAGE_RUNTIME_PATH_SUFFICIENT = TRUE`** — GAP-3 `3C` untouched.
`CoverageRuleRegistry` exposes `rules_for_metric` (`:215`), `ratification_of`
(`:194`), `authorize` (`:227`), `ratify` (`:177`) — exactly what the presence
derivation needs. Still **0 canonical rules ratified**, so the derivation yields
`UNRESOLVED`, which is the ratified fail-closed outcome.

**`NEGATIVE_SURFACE_TESTS_SPECIFIED = TRUE`** — test spec v0.3 carries **45**
negative-surface cases (9 field names × 5 attack vectors). v0.4 adds **15** TIME
cases, including the negative ones: TIME-6 (same instant not prior), TIME-8
(mixed shape), TIME-9/TIME-10 (forged and missing interval bounds rejected by the
accepted model), TIME-11 (superseded filtered before tie-break), TIME-13/TIME-14
(no zero-width, no one-day), TIME-15 (no `observed_at` path).

```text
NEGATIVE_SURFACE_CASES = 45   (carried)
TIME_CASES             = 15   (new, GAP-6)
TOTAL_CASES            = 252
```

**`TRACEABILITY_PLAN_COMPLETE = TRUE`** — plan v0.7 carries G-1..G-15 and adds
G-16..G-19, each tied to specific TIME cases; test spec v0.4 §3.2 maps every TIME
case to the rule it tests. Every replay check remains individually traceable.

**`UPSTREAM_FREEZE_PRESERVABLE = TRUE`** — re-verified: implementation worktree
clean at `5f94c3f4`, exactly one commit past the accepted anchor and that commit
is the acceptance commit itself, zero `Benchmark` matches across 62 modules, 0
Book 1–5 mutations. GAP-6 changes **no** accepted file and alters
`MeasurementObservation` **not at all**.

---

## 4. Structural checks specific to GAP-6

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT = NONE
NEW_RECORD_FIELD      = NONE
NEW_REGISTRY          = NONE
NEW_WINDOW_CLASS      = NONE
NEW_TEMPORAL_CONTRACT = NONE
MEASUREMENTOBSERVATION_CONTRACT_CHANGED = FALSE

SYNTHETIC_ZERO_WIDTH_INTERVAL = FALSE
ONE_DAY_CONVENTION            = FALSE
BLANKET_EXCLUSION_OF_INSTANTANEOUS = FALSE
BLANKET_REFUSAL_OF_INSTANTANEOUS   = FALSE
WINDOW_CLASS_CONVERSION        = FALSE
OBSERVED_AT_ORDERING           = FALSE
CALLER_ORDER_ORDERING          = FALSE
AGGREGATION_INVENTION          = FALSE
```

The ordering projection is a **definition inside the already-ratified selector's
derivation semantics**. It is not a class, so the contract count stays at 2.

---

## 5. Residual risk, stated plainly

Three things this review could not eliminate:

1. **GAP-6 is a draft.** The two upgraded criteria are conditional on its
   ratification. Declining it returns the verdict to HOLD.
2. **No code was executed.** Every criterion is a static reading of accepted
   source plus draft governance. The determinism argument for instantaneous
   ordering is a proof sketch over a closed enum, not a test run.
3. **The observation currency resolver is absent.** Accepted source has
   `ObservationStatus` and `status` but no `observation_is_current()` helper,
   unlike `methodology_is_current()` (`book6_methodology.py:332`). The GAP-6 gate
   is therefore a condition over the existing enum. This is sufficient and needs
   no new class, but it is a real asymmetry in accepted source, not an oversight
   in the draft.

```text
RESIDUAL_RISK_ITEMS = 3
NONE_IS_A_BLOCKER   = TRUE
```

---

## 6. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE

IMPLEMENTATION_AUTHORIZED = NO
REVIEW_VERDICT           = READY_PENDING_GAP6_RATIFICATION
```

`READY_PENDING_GAP6_RATIFICATION` is **not** an authorization. The next operator
action is a ratification decision on GAP-6, not an implementation decision.

**Not authorized and not performed:** any implementation; any source or test
change; any change to `MeasurementObservation`; any Class C design; any coverage
or `ComparisonRule` ratification; any reopening of GAP-1..GAP-5; any reversal of
`BOOK6-COMPARE-SUBSTRATE-v0.2`.
