# CSIA — BOOK 6 COMPARISON / CHANGE SUBSTRATE RATIFICATION PACKET — v0.2

**Document ID:** CSIA-B6-SRP-002
**Version:** 0.2
**Status:** `AWAITING_OPERATOR_DECISION`
**Date:** 2026-10-02
**Kind:** OPERATOR DECISION PACKET — ratification only, never implementation

**This packet does not ratify anything and does not authorize implementation.**

---

# 1. What is being decided

Ratification of the implementation-substrate clarification for the Book 6
Comparison/Change amendment, comprising six successor artifacts:

| # | artifact | status |
|---|---|---|
| 1 | `..._IMPLEMENTATION_SUBSTRATE_CLARIFICATION_v0.2.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |
| 2 | `..._COMPARISON_CHANGE_GRAMMAR_v0.6.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |
| 3 | `..._COMPARISON_CHANGE_AMENDMENT_PLAN_v0.6.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |
| 4 | `..._AMENDMENT_BOUNDARY_v0.4.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |
| 5 | `..._AMENDMENT_RATIFICATION_RECORD_ERRATUM_v0.1.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |
| 6 | `..._IMPLEMENTATION_TEST_SPEC_v0.3.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` |

Gating reviews:

| review | result |
|---|---|
| `..._SUBSTRATE_PRE_RATIFICATION_REVIEW_v0.2.md` | **20 / 20 PASS** |
| `..._IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3.md` | **READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION** — **10 TRUE / 0 FALSE** |

---

# 2. The five resolutions, including GAP-5E

| gap | resolution | one-line meaning | new contract class? |
|---|---|---|---|
| GAP-1 | `1A-STRICT` | canonical value = finite stored binary64; equality = exact stored `==`; non-finite rejected | no |
| GAP-2 | `2D` | arithmetic only under same-metric exact-unit identity; mismatch = `NOT_COMPARABLE`; P3 withdrawn | no |
| GAP-3 | `3C` | coverage applicability from exact-metric current ratified rule presence; absence = `UNRESOLVED` | no |
| GAP-4 | `4D` | `TemporalComparabilityStatus` produced by replay check 19 | no |
| **GAP-5** | **`5E`** | **`BaselineSelectorSpec` nested inside `ComparisonRule`; no `BenchmarkRule`, no registry; one executable selector** | **no** |

```text
GAP_5A / 5B / 5C / 5D = NOT SELECTED

NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

## 2.1 What GAP-5E retires

```text
ACCEPTED_BENCHMARK_RULE_NAMESPACE = FALSE
BENCHMARK_RULE_RUNTIME            = NOT_IMPLEMENTED
BENCHMARK_RULES_RATIFIED         = 0

EXECUTABLE_BASELINE_SELECTOR_COUNT = 1
EXECUTABLE_BASELINE_SELECTOR      = PRIOR_COMPARABLE_WINDOW
ROLLING_MEAN / ROLLING_MEDIAN / HISTORICAL_DISTRIBUTION / BASELINE_EPOCH
                                    = RESERVED_NOT_EXECUTABLE
```

---

# 3. What ratification would mean — and would not mean

```text
RATIFYING WOULD:
  - fix GAP-1 as 1A-STRICT, GAP-2 as 2D, GAP-3 as 3C, GAP-4 as 4D, GAP-5 as 5E
  - retire the phantom benchmark claim prospectively
  - establish grammar v0.6, plan v0.6, boundary v0.4, erratum v0.1 and test
    spec v0.3 as the governing substrate
  - encode the phantom-citation boundary invariant mechanically

RATIFYING WOULD NOT:
  - authorize any implementation
  - authorize any test code
  - re-accept Book 6
  - ratify any ComparisonRule, benchmark rule, or coverage rule
  - create any BenchmarkRule or BenchmarkRuleRegistry
  - solve Class C StateRule benchmark semantics (explicitly out of scope)
  - resolve the Phase 8 aggregation standing condition
```

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE  (before and after)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

# 4. Ratified history is preserved

```text
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md            = RATIFIED, UNCHANGED
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.4.md                    = RATIFIED, UNCHANGED
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.3.md         = RATIFIED, UNCHANGED
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_v0.1.md
                                                                     = RATIFIED, UNCHANGED
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.5.md            = DRAFT, superseded
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.5.md                    = DRAFT, superseded
```

No ratified artifact is edited in place. The phantom correction is prospective
via a separate erratum that quotes the original text verbatim and claims no
retroactive correction.

---

# 5. Standing conditions — recorded, not waived

1. **Phase 8 aggregation condition.** If a metric declares
   `aggregation == NONE` and multiple observations exist for one comparison
   window, the implementation must **HOLD and surface** a new operator decision.
   It must not silently aggregate.
2. **Class C `StateRule` benchmark.** `BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME =
   UNRATIFIED / UNIMPLEMENTED`. This amendment does not touch it and does not
   claim to solve it.
3. **Canonical zero-rule state.** `COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0` and
   `BENCHMARK_RULES_RATIFIED = 0`, so canonical comparisons remain fail-closed.

---

# 6. The operator choice

```text
OPTION A   RATIFY_SUBSTRATE_CLARIFICATION_v0.2_AND_SUCCESSORS
           Ratify artifacts 1-6 as the governing Book 6 Comparison/Change
           implementation substrate. FIXES GAP-1..GAP-5 including 5E.
           Grants NO implementation authority.
           Retires the phantom benchmark claim prospectively.

OPTION B   HOLD
           Take no ratification action. GAP-1..GAP-5 remain unresolved and the
           phantom benchmark claim remains in force inside the ratified record.
           Grants NO implementation authority.
```

**Both options grant no implementation authority.** The difference is whether
the five gaps are fixed and the phantom retired on the record.

---

# 7. Recommended sequencing

```text
1. Decide the Class C StateRule benchmark question (separate, explicitly out
   of scope here) so it is not silently inherited later
2. RATIFY_SUBSTRATE_CLARIFICATION_v0.2_AND_SUCCESSORS or HOLD
3. Re-run the implementation authorization review post-ratification
4. Only then consider implementation authorization
```

---

# 8. State at time of packet

```text
GAP_1..GAP_5 = RESOLVED IN DRAFT, NOT RATIFIED
               (1A-STRICT, 2D, 3C, 4D, 5E)
PHANTOM_CITATION_SWEEP        = COMPLETE
PHANTOM_BENCHMARK             = RETIRED PROSPECTIVELY, NOT YET RATIFIED
PRE_RATIFICATION_REVIEW_v0.2  = 20 / 20 PASS
IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3
                               = READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION
                                 10 TRUE / 0 FALSE
TEST_SPEC_v0.3                = 237 cases, 0 BLOCKED
REPLAY_CHECK_COUNT            = 20
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
COMPARISON_RULES_RATIFIED       = 0
BENCHMARK_RULES_RATIFIED        = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
D6M_5                           = OPEN_DEFERRED
```

**Not authorized and not performed by this packet:** any ratification, any
implementation, any source or test change, any `BenchmarkRule` or
`BenchmarkRuleRegistry`, any benchmark-rule ratification, Book 6 re-acceptance,
Book 7 or Book 8, live acquisition, and any branch creation, force-push, rebase
or history rewrite.

```text
STOP. Do not ratify. Do not implement.
```
