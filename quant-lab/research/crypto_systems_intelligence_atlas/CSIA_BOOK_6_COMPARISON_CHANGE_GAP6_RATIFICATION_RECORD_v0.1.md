# CSIA — Book 6 Comparison/Change GAP-6 Ratification Record v0.1

**Status:** `RATIFIED`
**Date:** 2026-10-04
**Decision id:** `BOOK6-GAP6-v0.2`
**Operator selection:** `RATIFY_GAP6_6E_WINDOW_CLASS_AWARE_ORDERING_KEYS`
**Scope:** `BOOK 6 COMPARISON TEMPORAL ORDERING DOCTRINE ONLY`
**Grants implementation authority:** `FALSE`
**Changes any accepted source:** `FALSE`

```text
GAP_6            = CLOSED / RATIFIED
GAP_6_RESOLUTION = 6E WINDOW_CLASS_AWARE_ORDERING_KEYS

GAP_1..GAP_5_REOPENED     = FALSE
GAP_7_REOPENED            = FALSE
SUBSTRATE_RATIFICATION_REVERSED = FALSE

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 0. What this record is, and what it is not

This record **closes GAP-6 by ratification** of the `6E WINDOW_CLASS_AWARE_ORDERING_KEYS`
design already carried in
`CSIA_BOOK_6_COMPARISON_CHANGE_INSTANTANEOUS_ORDERING_CLARIFICATION_v0.1.md`.

It ratifies **doctrine only**. It grants no implementation authority, changes no
accepted source, adds no test code, creates no branch or worktree, and opens no
new gap.

```text
THIS RECORD RATIFIES    = the 6E ordering-key projection + its ordering rule
THIS RECORD DOES NOT    = authorize implementation of anything
```

---

## 1. Basis verified before ratification

| Source | State |
|---|---|
| `..._GAP6_READINESS_REVIEW_v0.3.md` | `PASS` (12 / 12), `PRE_IMPLEMENTATION_IMPLEMENTABILITY` |
| `..._GAP6_RATIFICATION_PACKET_v0.2.md` | `AWAITING_OPERATOR_DECISION`, option A selected |
| `..._INSTANTANEOUS_ORDERING_CLARIFICATION_v0.1.md` | 6E fully specified |
| `..._GRAMMAR_v0.7.md` | selector set, contract count, invariants |
| `..._AMENDMENT_PLAN_v0.7.md` | standing conditions, regression baselines |
| `..._IMPLEMENTATION_TEST_SPEC_v0.4.md` | test contract, contract-class audit |
| `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md` | `RATIFIED` at `BOOK6-GAP7-v0.3` |

```text
READINESS               = PASS / 12 OF 12
POLICY_GAP              = 0
6E_DESIGN               = FULLY_SPECIFIED
GAP7_DEPENDENCY         = RATIFIED / FULLY_SPECIFIED
```

---

## 2. Ratified effective-key semantics (6E)

For every eligible observation, two **derived, selector-local** ordering keys are
computed at selection time and discarded afterwards.

```text
For o in INTERVAL_WINDOW_CLASSES:      (9 of 10 WindowClass members)
    effective_start(o) = o.window_start
    effective_end(o)   = o.window_end

For o == WindowClass.INSTANTANEOUS:    (the 1 remainder)
    effective_start(o) = o.valid_time
    effective_end(o)   = o.valid_time
```

```text
ORDERING_KEYS_ARE_DERIVED = TRUE
OBSERVATION_MUTATION      = FALSE
STORED_BACK_ONTO_RECORD   = FALSE
NEW_TEMPORAL_CONTRACT     = NONE
NEW_WINDOW_CLASS          = NONE

BLANKET_EXCLUSION_OF_INSTANTANEOUS = FALSE
BLANKET_REFUSAL_OF_INSTANTANEOUS   = FALSE
```

The projection is **total over the closed `WindowClass` enum**. There is no third
case, so implementation must **not** add an `else` arm or default fallback:

```text
UNRECOGNISED_WINDOW_CLASS = FAIL_CLOSED_ERROR   (not a default value)
```

Deriving is not fabricating. `effective_end == effective_start == valid_time` for
an instantaneous observation asserts nothing new about the record: a point
occupies the interval `[t, t]`, and `valid_time` already carries that point. No
interval field is created, populated, or implied on the record.

```text
FABRICATED_INTERVAL   = FALSE
ZERO_WIDTH_INTERVAL_AS_FACT_ABOUT_RECORD = FALSE
ONE_DAY_CONVENTION    = FALSE
```

---

## 3. Ratified strict precedence and three-step ordering

### 3.1 The binding prior condition

A candidate is eligible for comparison `c` only if:

```text
candidate.effective_end  <  comparison.effective_start
```

```text
STRICT_TEMPORAL_PRECEDENCE = TRUE
LESS_THAN_IS_STRICT        = TRUE    (never <=)
```

Strict `<` preserves *prior means prior*, and prevents the same instant or a
shared window boundary being selected as both baseline and comparison.

### 3.2 The three-step ordering

```text
1. greatest effective_end(candidate)
2. if tied on effective_end: greatest effective_start(candidate)
3. if still tied: stable lexical measurement_ref        (FINAL tie-break ONLY)
```

```text
CALLER_ORDER_AFFECTS_BASELINE     = FALSE
OBSERVED_AT_USED_FOR_ORDERING     = FALSE   (observed_at is knowledge time)
INGESTION_TIME_USED_FOR_ORDERING  = FALSE
RANDOM_SELECTION                  = FALSE
LEXICAL_IS_FINAL_TIEBREAK_ONLY    = TRUE
DETERMINISTIC_SELECTION           = TRUE
```

`observed_at` is **knowledge time**; `valid_time` is the **economic/semantic
axis**. This is a temporal-selection rule, not a bitemporal rewrite.

The lexical tie-break exists **only** so that a remaining tie resolves to
exactly one observation rather than to implementation-defined behaviour. It is
a determinism device, not a semantic preference, and it is **final**.

### 3.3 Instantaneous collapse

When both sides are instantaneous the precedence test reduces to the intended
reading:

```text
candidate.valid_time < comparison.valid_time
```

Two candidates sharing a `valid_time` tie on both derived keys and fall through
to step 3.

---

## 4. Ratified WindowClass boundary

Compatibility is **supplied by binding**, never by conversion.

```text
WINDOW_CLASS_CONVERSION            = FALSE
INSTANTANEOUS_TO_INTERVAL_COERCION = FALSE
INTERVAL_TO_INSTANTANEOUS_COERCION = FALSE
WINDOW_CLASS_ADDED                 = NONE
```

For one `ComparisonRule`, one bound `MetricDefinition` fixes the `WindowClass`
for **both** the baseline and the comparison observation. Accepted runtime
already enforces this through `validate_against_definition()`, which raises when
an observation's `window_class` differs from its definition's.

Mixed-shape and wrong-definition records are therefore **structurally ineligible
before ordering**:

```text
IF candidate and comparison do not resolve to the same bound
   MetricDefinition / WindowClass:
        candidate is STRUCTURALLY INELIGIBLE
        the comparison is NOT_COMPARABLE
```

---

## 5. Ratified eligibility-before-ordering dependency (GAP-7)

GAP-7 currentness gates are evaluated **before** any temporal ordering runs.
The ratified conceptual order is fixed:

```text
1. current-authority / structural record eligibility
2. metric / methodology / unit / window compatibility
3. baseline candidate eligibility
4. temporal ordering                       <- 6E keys are consumed HERE ONLY
```

```text
ELIGIBILITY_PRECEDES_ORDERING = TRUE
ORDERING_SEES_INELIGIBLE_RECORDS = FALSE
```

Two consequences are binding:

```text
A historical predecessor NEVER reaches the lexical tie-break.
A source-less non-value-bearing record under NV-B NEVER reaches ordering
as a current record.
```

Rationale: 6E ordering applied to a set containing its own superseded
predecessor would select a non-current record as baseline. GAP-7 RUNG 1–2 must
therefore land **before** comparison consumption. This is an implementation
ordering constraint, entirely expressible now.

```text
GAP7_DEPENDENCY_STATUS = RATIFIED / FULLY_SPECIFIED / NOT YET IMPLEMENTED
DEPENDENCY_NOT_IMPLEMENTED_YET  !=  DEPENDENCY_UNSPECIFIED
```

---

## 6. Ratified aggregation boundary

```text
SELECTOR_AGGREGATES = FALSE
```

`MetricDefinition.aggregation` remains the sole owner of aggregation semantics.
The baseline selector selects a record; it never aggregates records.

### 6.1 The standing refusal

```text
metric declares aggregation == NONE
AND
the selected comparison window would require inventing an aggregation
    -> HOLD THAT RUNTIME CASE and surface a concrete operator decision
```

```text
SILENT_AGGREGATION       = FORBIDDEN
INVENTED_AGGREGATION     = FORBIDDEN
THIS_IS_A_DESIGN_GAP     = FALSE   -- it is a recorded refusal to invent
```

This refusal is **fully specified as a refusal**, so it does not block
implementability. It is recorded so that an implementer knows to **stop and
surface**, rather than to aggregate.

---

## 7. Invariants unchanged by this ratification

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT                        = NONE
```

The derived ordering keys are **not** a third contract class. They are
definitions inside the already-ratified selector's derivation semantics.

```text
CONTRACT_COUNT_CHANGED_BY_GAP6 = FALSE
EXECUTABLE_BASELINE_SELECTOR_COUNT = 1
EXECUTABLE_BASELINE_SELECTOR       = PRIOR_COMPARABLE_WINDOW
ROLLING_MEAN / ROLLING_MEDIAN / HISTORICAL_DISTRIBUTION / BASELINE_EPOCH
                                  = RESERVED_NOT_EXECUTABLE
TemporalComparabilityStatus = COMPARABLE | NOT_COMPARABLE | UNRESOLVED
BASELINE_SELECTOR_AUTHORITY = BOUND_INSIDE_COMPARISON_RULE

MEASUREMENT_OBSERVATION_CONTRACT = UNCHANGED
BOOK_6_CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED
D6M_ITEMS_CLOSED_BY_GAP_6 = 0
D6M_ITEMS_CHANGED_BY_GAP_6 = 0
```

### 7.1 Replay count unchanged

```text
COMPARISON_REPLAY_CHECK_COUNT = 20      (canonical; see the replay precedence erratum)
THIS_RECORD_CHANGES_REPLAY_COUNT = FALSE
THIS_RECORD_CHANGES_ANY_REPLAY_CHECK = FALSE
```

---

## 8. Replay precedence — pointer, not a second statement

Two ratified records enumerate a comparison authority replay at different
counts: 19 in `BOOK6-COMPARE-AMEND-v0.4`, 20 in
`BOOK6-COMPARE-SUBSTRATE-v0.2`. Both remain ratified and **neither is edited**.

The precedence between them is settled by the separate, additive, non-retroactive
artifact:

```text
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md
```

```text
IMPLEMENTATION_CANONICAL_REPLAY = 20
RETROACTIVE_REWRITE             = FALSE
HISTORICAL_RECORD_PRESERVED     = TRUE
```

---

## 9. What this ratification explicitly does NOT do

```text
IMPLEMENTATION_AUTHORIZED            = FALSE
SOURCE_CHANGED                      = FALSE
TEST_CODE_WRITTEN                    = FALSE
BRANCH_CREATED                      = FALSE
WORKTREE_CREATED                    = FALSE
FROZEN_BOOK6_WORKTREE_TOUCHED        = FALSE
ACCEPTED_IMPLEMENTATION_ANCHOR_MOVED = FALSE
GAP_7_REOPENED                      = FALSE
GAP_1..GAP_5_REOPENED                = FALSE
BOOK_7_WORK                         = FALSE
CHOIR_WORK                          = FALSE
HISTORICAL_19_CHECK_REPLAY_USABLE   = FALSE   (for implementation)
```

---

## 10. Standing state after this decision

```text
GAP_1..GAP_5 = CLOSED / RATIFIED
GAP_6        = CLOSED / RATIFIED
GAP_6_RESOLUTION = 6E WINDOW_CLASS_AWARE_ORDERING_KEYS
GAP_7        = CLOSED / RATIFIED
GAP_7_RESOLUTION = 7A-KERNEL + B-STRICT + NV-B

BOOK_6_COMPARISON_DESIGN  = COMPLETE
COMPARISON_REPLAY         = 20 CHECKS / CURRENT

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

### 10.1 Next

```text
NEXT = CONSOLIDATED BOOK 6 IMPLEMENTATION AUTHORIZATION REVIEW
```

Implementation of GAP-7 rungs 1–3 and comparison/change rungs 4–11 remains a
**separate, later** authorization that must cover **both**. The only remaining
operator gate is an explicit selection of `AUTHORIZE_OFFLINE_IMPLEMENTATION`.

---

## 11. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md  (RATIFIED)
CSIA_BOOK_6_COMPARISON_CHANGE_INSTANTANEOUS_ORDERING_CLARIFICATION_v0.1.md
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_READINESS_REVIEW_v0.3.md  (PASS 12/12)
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_PACKET_v0.2.md  (this selection)
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md  (RATIFIED)
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```
