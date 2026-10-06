# CSIA — Book 6 Comparison Change Operand Cardinality Ratification Record v0.1

**Status:** `RATIFIED`
**Record type:** governance decision record
**Date:** 2026-10-06
**Decision id:** `BOOK6-COMPARISON-OPERAND-CARDINALITY-v0.1`
**Operator selection:** `RATIFY_ONE_COMPARISON_MEASUREMENT_PER_CHANGEOBSERVATION`
**Resolves:** the open plurality question left untouched by
`CSIA_BOOK_6_COMPARISON_COVERAGE_MEASUREMENT_BINDING_RATIFICATION_RECORD_v0.1.md` §3
**Grants implementation authority:** `FALSE` (already held; unchanged)
**Changes implementation:** `FALSE` (this record is a governance act; the runtime
cardinality firewall it authorises lands as the append-only Rung 8 repair)

```text
ONE_CHANGEOBSERVATION_ONE_COMPARISON_MEASUREMENT          = TRUE
COMPARISON_MEASUREMENT_REFS_AUTHORITATIVE_CARDINALITY     = 1
SELECTED_BASELINE_CARDINALITY                             = 1
BASELINE_CANDIDATE_REF_CARDINALITY                        = 1_OR_MORE
MULTI_COMPARISON_ARITHMETIC_DEFINED                       = FALSE (corpus fact; unchanged here)
MULTI_COMPARISON_ARITHMETIC                               = NOT IMPLEMENTED
MULTI_COMPARISON_COVERAGE_AGGREGATION                     = NOT IMPLEMENTED
MULTI_COMPARISON_CHANGEOBSERVATION                        = NOT AUTHORIZED
NEW AGGREGATION SEMANTICS                                 = NONE
NEW AUTHORITY CLASS                                       = NONE
```

---

## 0. What this record is

The measurement-binding ratification record §3 established that coverage replay
is per-measurement — N comparison measurements are replayed N times, each
against its own coverage observation — and explicitly did **not** decide how N
replayed verdicts populate the singular `ChangeObservation` coverage fields.

This record closes that question at a deeper level. The operator has ruled that
an authoritative `ChangeObservation` describes **one** comparison
`MeasurementObservation` against **one** selected baseline
`MeasurementObservation`. N is not reduced, aggregated, or selected among: N > 1
is simply not authorized for authoritative production.

The decision does not invent new arithmetic. It aligns four already-existing
facts:

1. the Rung 6 selector input is one comparison observation —
   `select_baseline(*, comparison: MeasurementObservation, ...)`;
2. the ratified delta arithmetic has one comparison operand —
   `ABSOLUTE_DELTA = comparison_value - baseline_value`
   (amendment ratification record v0.1 `:84-86`);
3. `ChangeObservation.selected_baseline_measurement_ref` is singular;
4. `ChangeObservation.coverage_observation_ref` is singular and, since the
   measurement-binding ratification, is bound to the comparison measurement.

---

## 1. The decision

```text
AUTHORITATIVE_COMPARISON_MEASUREMENT_CARDINALITY = EXACTLY_ONE
AUTHORITATIVE_SELECTED_BASELINE_CARDINALITY      = EXACTLY_ONE
DELTA_OPERAND_COUNT                              = TWO
COVERAGE_OBSERVATION_COUNT_PER_CHANGE            = ZERO_OR_ONE (existing coverage state)
```

One `ChangeObservation` describes one comparison `MeasurementObservation`
against one selected baseline `MeasurementObservation`.

---

## 2. Schema discipline — restriction, not rewrite

`comparison_measurement_refs` **remains** `tuple[str, ...]` with
`Field(min_length=1)` in the contract schema. The tuple shape is preserved for:

```text
SCHEMA CONTINUITY            = TRUE
HISTORICAL COMPATIBILITY     = TRUE
FUTURE SUCCESSOR GOVERNANCE  = TRUE (out of scope here)
```

The restriction is **executable-cardinality**, imposed at the authoritative
derivation / authorization layer by this amendment's runtime:

```text
AUTHORITATIVE ChangeObservation REQUIRES:
    len(comparison_measurement_refs) == 1

COMPARISON_MEASUREMENT_REFS_SCHEMA_SHAPE_CHANGED = FALSE
HISTORICAL SCHEMA REWRITTEN                      = FALSE
```

The measure-zero-but-real cases `()` are refused separately and first, by the
existing `min_length=1` contract validator, before any cardinality check runs;
both refusals are refusals, and the cardinality firewall treats a set of any
size other than one as unauthorized.

---

## 3. Baseline refs distinction

The two baseline fields are different concepts and this record deliberately does
**not** impose `len(baseline_measurement_refs) == 1`:

```text
baseline_measurement_refs             = the candidate/input baseline reference
                                        set recorded for replay
selected_baseline_measurement_ref     = the ONE baseline actually used in
                                        arithmetic

ARITHMETIC_BASELINE_OPERAND           = selected_baseline_measurement_ref
BASELINE_CANDIDATE_REF_COUNT          = MAY_BE_GREATER_THAN_ONE
SELECTED_BASELINE_REF_COUNT           = EXACTLY_ONE when COMPARABLE arithmetic runs
SELECTOR_INPUT_CANDIDATE_CARDINALITY  = MAY_BE_GREATER_THAN_ONE (Rung 6 unchanged)
```

The selector may receive any number of candidates; exactly one is selected or
`BASELINE_UNAVAILABLE` is reported. Nothing here amends Rung 6.

---

## 4. Comparison refs distinction

For this amendment there is **no** analogous selector over comparison
measurements. The Rung 8 derivation engine receives one comparison observation.

```text
COMPARISON_MEASUREMENT_REFS (authoritative) = EXACTLY ONE comparison operand
COMPARISON_SIDE_AGGREGATION                 = NONE / DOES NOT EXIST
COMPARISON_SIDE_SELECTOR                    = NONE / DOES NOT EXIST
COMPARISON_SIDE_TIE_BREAK                   = NONE / DOES NOT EXIST
COMPARISON_SIDE_REDUCER                     = NONE / DOES NOT EXIST
```

Because no comparison-side selector exists, no ordering policy over comparison
measurements is defined, and none may be invented by the implementation: there
is nothing for a policy to order.

---

## 5. Negative surface — fail closed

For authoritative `ChangeObservation` production, all of the following are
refused with reason `MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED`:

```text
comparison_measurement_refs = ()          REFUSED (min_length=1; firewall treats as unauthorized)
comparison_measurement_refs = (A,)        ACCEPTED
comparison_measurement_refs = (A, B)      REFUSED
comparison_measurement_refs = (A, B, C)   REFUSED
comparison_measurement_refs = (A, B, ...) REFUSED (any count > 1)
```

The refusal must occur **before** any operand is examined or used. In
particular, no implementation may:

```text
PICK_FIRST                           PROHIBITED
PICK_LAST                            PROHIBITED
SORT_LEXICALLY                       PROHIBITED
AVERAGE                              PROHIBITED
SUM                                  PROHIBITED
SELECT_BY_TIME                       PROHIBITED
SELECT_BY_COVERAGE                   PROHIBITED
SELECT_BY_CALLER_ORDER               PROHIBITED
SELECT_BY_ANY_UNRATIFIED_KEY         PROHIBITED
```

Every one of those would be a comparison-side selector, and §4 rules that no
comparison-side selector exists. Silence is impossible: the refusal carries the
required reason string and the offending count.

---

## 6. What this record does not do

```text
CHANGEOBSERVATION_FIELD_ADDED              = NONE
CHANGEOBSERVATION_SCHEMA_REWRITTEN         = FALSE
BASELINE_CANDIDATE_CARDINALITY_IMPOSED     = FALSE
RUNG_6_SELECTOR_AMENDED                    = FALSE
COVERAGE_REPLAY_GRANULARITY_CHANGED        = FALSE (stays ONE MEASUREMENT PER REPLAY)
NEW AGGREGATION SEMANTICS                  = NONE
NEW AUTHORITY-BEARING CLASS                = NONE   (contract count remains exactly 2)
NEW COMPARISON-SIDE SELECTOR OR POLICY     = NONE
UNIT CONVERSION                            = NONE
EPSILON / TOLERANCE                        = NONE
DECIMAL / FRACTION ARITHMETIC              = NONE
SOURCE_FILE_WRITTEN_OR_EDITED_BY_RECORD    = FALSE
TEST_CODE_WRITTEN_OR_EDITED_BY_RECORD      = FALSE
RATIFIED_RECORD_EDITED                     = FALSE
BRANCH_REWRITTEN_OR_REBASED                = FALSE
FROZEN_BOOK_6_WORKTREE_MUTATED             = FALSE
BOOK_7_WORKED_ON                           = FALSE
LIVE_ACQUISITION                           = FALSE
```

---

## 7. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (offline amendment scope only, unchanged)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
RUNG_8_ARITHMETIC               = UNBLOCKED upon commit of this record
```

## 8. Cross-references

```text
CSIA_BOOK_6_COMPARISON_COVERAGE_MEASUREMENT_BINDING_RATIFICATION_RECORD_v0.1.md  §3 open question discharged here
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_v0.1.md              :84-97 delta operators, direction, zero-baseline
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.7.md                                    ordering law (baseline-side only)
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md                                    :134 comparison refs "one or more; non-empty"
book6_comparison_contracts.py                                                    ChangeObservation (class 2 of 2)
book6_comparison_selector.py                                                     select_baseline (singular comparison operand)
book6_comparison_coverage.py                                                     replay_coverage_checks (Rung 7)
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

---

**Status:** `RATIFIED`. One authoritative `ChangeObservation` carries exactly one
comparison measurement and exactly one selected baseline. The tuple shape
stands; multi-comparison production is not authorized. No schema rewrite, no
aggregation semantics, no new authority.
