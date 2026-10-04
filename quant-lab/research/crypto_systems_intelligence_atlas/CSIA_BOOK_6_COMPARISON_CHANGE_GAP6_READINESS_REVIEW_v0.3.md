# CSIA — Book 6 Comparison/Change GAP-6 Readiness Review v0.3

**Status:** `AUDIT_FINDING` — assesses readiness; ratifies nothing.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`

```text
REVIEW_TYPE = PRE_IMPLEMENTATION_IMPLEMENTABILITY
VERDICT     = PASS (12 / 12)
```

**Supersedes:** `..._GAP6_READINESS_REVIEW_v0.2.md` (HOLD, wrong criterion —
see `..._v0.2_ERRATUM.md`), which superseded `..._GAP6_READINESS_RECONCILIATION_v0.1.md`.

---

## 0. What this review is, and what it is not

```text
THIS REVIEW ASKS:
  can a coder implement the ratified GAP-6 design without CHOOSING NEW POLICY?

THIS REVIEW DOES NOT ASK:
  has the code already been written?
```

Implementation was never authorized for Book 6. The comparison/change substrate
is therefore **absent from accepted source**, and that absence is the expected
state before implementation authorization. v0.2 treated that absence as a
readiness failure. That was the wrong question, and this review replaces it.

## 1. The corrected readiness standard

```text
PRE_IMPLEMENTATION_READINESS =
    the coder can implement the ratified design
    without choosing new policy
```

Readiness explicitly does **NOT** require:

```text
ComparisonRule            already implemented
ChangeObservation         already implemented
ordering helper           already implemented
comparison engine         already implemented
tests                     already implemented
```

Those are the work a future implementation authorization is intended to permit.

The invalid inference, stated so it is not repeated:

```text
NOT_IMPLEMENTED  ->  NOT_READY_TO_IMPLEMENT     <-- INVALID
NOT_IMPLEMENTED  ->  IMPLEMENTABILITY_UNASSESSED <-- VALID
```

## 2. Sources audited

```text
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md   RATIFIED
    BOOK6-COMPARE-SUBSTRATE-v0.2 -- the authoritative substrate
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.7.md
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.7.md
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md
CSIA_BOOK_6_COMPARISON_CHANGE_INSTANTANEOUS_ORDERING_CLARIFICATION_v0.1.md  (6E)
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md  RATIFIED
accepted Book 6 source at 5f94c3f40c
```

`GAP-6 6E` is **not** in the ratified substrate record; that record covers
GAP-1..GAP-5 and is scoped `SUBSTRATE GOVERNANCE ONLY`. 6E is proposed by the
instantaneous-ordering clarification and is unratified. That is the correct
pre-ratification posture, and it is why GAP-6 readiness is assessed as a
*proposed* design against ratified substrate.

---

## 3. Implementability audit — the twenty objects (A-T)

Each object was tested against the eight-question standard. Only **#8** (a
coder choice left that changes semantics) creates a policy blocker.

| # | Object | Classification | Basis |
|---|---|---|---|
| A | `ComparisonRule` | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | 2 authority-bearing classes fixed; 20 replay checks enumerate its binding |
| B | `BaselineSelectorSpec` | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | nested value object; ownership, fingerprint content and refusal all specified |
| C | `TemporalComparabilityStatus` | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | closed 3-member set `COMPARABLE \| NOT_COMPARABLE \| UNRESOLVED` |
| D | `ChangeObservation` | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | derived record; authority derived by replay, never asserted |
| E | `ComparisonRule` registry / ratification path | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | identity + version + canonical fingerprint bound at ratification |
| F | 20-check current-authority replay | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | all 20 enumerated in the ratified substrate record §14 |
| G | finite binary64 semantics | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | no NaN/inf policy invented; delta operator validity is check 7 |
| H | same-metric exact-unit identity | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | GAP-2 `2D`: exact `MetricDefinition.unit` string identity |
| I | coverage-rule-presence derivation | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | GAP-3 `3C`: exact `scope_metric_id` identity; absence → `UNRESOLVED` |
| J | `PRIOR_COMPARABLE_WINDOW` selection | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | 11 eligibility conditions + 3-step ordering + 4 reserved selectors |
| K | effective temporal keys | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | total projection over the closed `WindowClass` enum |
| L | strict prior precedence | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | condition 9: strictly precedes |
| M | deterministic lexical tie-break | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | 3rd and **final** tie-break only |
| N | GAP-7 eligibility before ordering | `DEPENDENCY_REQUIRES_GAP7_IMPLEMENTATION` | ratified contract exists; code does not yet |
| O | NV-B currentness semantics | `DEPENDENCY_REQUIRES_GAP7_IMPLEMENTATION` | ratified at `BOOK6-GAP7-v0.3` |
| P | no-resurrection semantics | `DEPENDENCY_REQUIRES_GAP7_IMPLEMENTATION` | ratified; `TERM-5` |
| Q | branching lineage fail-closed | `DEPENDENCY_REQUIRES_GAP7_IMPLEMENTATION` | ratified; resolver-level refusal required |
| R | reserved selectors reject | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | construction refused; no placeholder behaviour |
| S | no aggregation invention | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | `SELECTOR_AGGREGATES = FALSE`; `MetricDefinition.aggregation` owns it |
| T | Class C benchmark separate/deferred | `IMPLEMENTABLE_FROM_RATIFIED_CONTRACT` | `BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED` |

```text
IMPLEMENTABLE_FROM_RATIFIED_CONTRACT = 16
DEPENDENCY_REQUIRES_GAP7_IMPLEMENTATION = 4  (N, O, P, Q)
POLICY_GAP                          = 0
```

**Zero policy gaps.** No object required a coder to choose semantics.

## 4. The four dependencies are ordering constraints, not design gaps

The four `DEPENDENCY_REQUIRES_GAP7_IMPLEMENTATION` items are all GAP-7
semantics. GAP-7 is **ratified and fully specified**; it is simply not yet
implemented. Per Phase 11's required distinction:

```text
DEPENDENCY_NOT_IMPLEMENTED_YET  !=  DEPENDENCY_UNSPECIFIED
```

All four are the **latter-safe** case — fully specified, awaiting code. None is
the **former-dangerous** case where the dependency's meaning is undecided.

Critically, items N, P and Q are *not* optional for correctness. `N` means a
superseded predecessor must be excluded **before** any ordering runs, or 6E's
ordering would be applied to a set containing its own superseded predecessor.
GAP-7 RUNG 1–2 must therefore land **before** comparison consumption — an
implementation-ordering constraint, entirely expressible now.

---

## 5. Consolidated implementation order (plan only, not performed)

```text
RUNG  1  GAP-7 registry currentness primitives / terminality
RUNG  2  GAP-7 resolver hardening + NV-B
RUNG  3  GAP-7 tests / regression            (39-case spec v0.3)
RUNG  4  comparison grammar/types            (ComparisonRule, ChangeObservation,
                                              BaselineSelectorSpec,
                                              TemporalComparabilityStatus)
RUNG  5  ComparisonRule registry / fingerprint / ratification
RUNG  6  baseline selector + 6E temporal projection
RUNG  7  coverage / comparability gates
RUNG  8  ChangeObservation derivation
RUNG  9  20-check authority replay
RUNG 10  comparison negative/adversarial tests
RUNG 11  full Book 6 / CSIA / Sensor regression + traceability
```

Rungs 1–3 must precede rungs 4–9, because every comparison eligibility decision
depends on the single kernel currentness resolver. This is a planning record
only. **Nothing in this order has been implemented or authorized.**

## 6. The twelve criteria

| # | Criterion | Result |
|---|---|---|
| 1 | `NO_UNRATIFIED_POLICY_NEEDED` | **TRUE** — 0 policy gaps across A–T |
| 2 | `NO_RUNTIME_AUTHORITY_DESIGN_GAP` | **TRUE** — 2 authority-bearing classes fixed; no hidden third |
| 3 | `GAP7_DEPENDENCY_FULLY_SPECIFIED` | **TRUE** — ratified `BOOK6-GAP7-v0.3`, 39-case contract |
| 4 | `NUMERIC_SEMANTICS_FULLY_SPECIFIED` | **TRUE** — closed delta operator set; check 7 |
| 5 | `UNIT_SEMANTICS_FULLY_SPECIFIED` | **TRUE** — exact `MetricDefinition.unit` identity (2D) |
| 6 | `BASELINE_SELECTOR_FULLY_SPECIFIED` | **TRUE** — 1 executable, 4 reserved-non-executable, ordering closed |
| 7 | `TEMPORAL_ORDERING_FULLY_SPECIFIED` | **TRUE** — total projection, 3-step ordering, no default branch |
| 8 | `COVERAGE_PATH_FULLY_SPECIFIED` | **TRUE** — presence derivation with single `UNRESOLVED` absent meaning |
| 9 | `20_CHECK_REPLAY_FULLY_SPECIFIED` | **TRUE** — ratified §14, all 20 enumerated |
| 10 | `NEGATIVE_TEST_CONTRACT_COMPLETE` | **TRUE** — reserved selectors, absent coverage, `UNRESOLVED`, `BASELINE_UNAVAILABLE` |
| 11 | `UPSTREAM_FREEZE_PRESERVABLE` | **TRUE** — a fresh branch preserves `5f94c3f4` |
| 12 | `CONSOLIDATED_IMPLEMENTATION_ORDER_DEFINED` | **TRUE** — §5 above |

```text
CRITERIA = 12
TRUE     = 12
FALSE    =  0

GAP_6_READINESS = PASS
```

## 7. The one standing condition, recorded not resolved

The ratified substrate record §10.1 records a standing condition:

```text
metric declares aggregation == NONE AND multiple observations exist
for one comparison window
    -> HOLD and surface it. Do NOT silently aggregate.
```

This is a **deliberate refusal to invent**, not a gap. It is fully specified as
a refusal, so it does not block readiness; it is recorded so the implementer
knows to stop rather than aggregate.

## 8. Verdict and standing state

```text
GAP6_READINESS_v0.3 = PASS
GAP_6               = 6E DESIGN VALID / RATIFICATION NOT TAKEN UP
GAP_6_RATIFICATION  = NOT TAKEN UP

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**This is a PASS on implementability, not a ratification.** The operator's
remaining choice is whether to ratify `6E WINDOW_CLASS_AWARE_ORDERING_KEYS`. This
review does not ratify it, and does not authorize implementation.
