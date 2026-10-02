# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PLAN — v0.6

**Document ID:** CSIA-B6-CAP-006
**Version:** 0.6
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Kind:** NARROW ADDITIVE SUCCESSOR — substrate correction across GAP-1..GAP-5

## Relationship to earlier versions — stated precisely

```text
v0.4 = RATIFIED BASE PLAN   (anchor 28bfac52c23c891ebb54e9924dedc925a859b359,
                              ratified in 8557f4df8)  — IN FORCE, UNCHANGED
v0.5 = DRAFT, never ratified — SUPERSEDED BEFORE RATIFICATION
v0.6 = NARROW ADDITIVE SUCCESSOR correcting substrate assumptions across
       GAP-1..GAP-5, including the phantom benchmark claim
```

**v0.4 is NOT erroneous and NOT unratified.** It was correctly ratified and
remains in force. v0.6 does not reopen, reverse or replace it. v0.6 records the
substrate precision the authorization reviews found under-specified, and
records the one place where a ratified artifact asserted an authority that
never existed — stated as history, corrected prospectively.

**Implementation remains unauthorized until v0.6 and its successors are
operator-ratified AND the implementation authorization review v0.3 passes.**

---

# 1. Scope (count remains 2)

```text
ADDED:     ComparisonRule, ChangeObservation
REUSED:    coverage-sufficiency rules (existing CoverageRuleRegistry)
REMOVED:   the comparison_semantics policy section (v0.4);
           policy P3 unit_requirements (v0.6 — cited contract never existed);
           baseline_selection_methodology_ref (v0.6 — phantom field)
ADDED v0.6: baseline_selector: BaselineSelectorSpec (nested value object)
UNCHANGED: MetricDefinition, MeasurementMethodology, MeasurementObservation,
           ValuationObservation, NormalizationRule, StateRule,
           FundamentalStateVector, all D6M decisions, all accepted tests
```

---

# 2. The five resolutions

```text
GAP_1 = 1A-STRICT   keep stored binary64; exact stored-value equality;
                    finite input required; no epsilon, no migration
GAP_2 = 2D          same-metric exact-unit identity; no conversion;
                    P3 withdrawn
GAP_3 = 3C          coverage applicability from exact-metric current ratified
                    rule presence; absence = UNRESOLVED; NOT_APPLICABLE
                    not derivable
GAP_4 = 4D          TemporalComparabilityStatus with a producing check;
                    UNRESOLVED never maps to NOT_COMPARABLE
GAP_5 = 5E          ComparisonRule-owned BaselineSelectorSpec;
                    no BenchmarkRule, no BenchmarkRuleRegistry;
                    one executable selector (PRIOR_COMPARABLE_WINDOW);
                    four reserved names non-executable
```

`GAP_5A / 5B / 5C / 5D` are **NOT SELECTED**.

---

# 3. Baseline selection (5E)

```text
BASELINE_SELECTOR_AUTHORITY            = BOUND_INSIDE_COMPARISON_RULE
BASELINE_SELECTOR_INDEPENDENT_REGISTRY = FALSE
BASELINE_SELECTOR_INDEPENDENT_RATIFICATION = FALSE

EXECUTABLE_BASELINE_SELECTOR_COUNT = 1
EXECUTABLE_BASELINE_SELECTOR      = PRIOR_COMPARABLE_WINDOW
ROLLING_MEAN / ROLLING_MEDIAN / HISTORICAL_DISTRIBUTION / BASELINE_EPOCH
                                    = RESERVED_NOT_EXECUTABLE

ordering: greatest valid_time END strictly before comparison start;
          then greatest valid_time START; then stable lexical measurement_ref
BASELINE_SELECTION_DETERMINISTIC  = TRUE
CALLER_ORDER_AFFECTS_BASELINE     = FALSE
OBSERVED_AT_USED_FOR_BASELINE_ORDERING = FALSE

NO_ELIGIBLE_PRIOR_BASELINE -> INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
BASELINE RESULT            = ONE MeasurementObservation
SELECTOR_AGGREGATES        = FALSE   (aggregation is MetricDefinition's)
```

Coverage is an **authorization gate after** structural selection, never a
selection input — using it to select would make the gate circular.

---

# 4. Replay — 20 checks

```text
REPLAY_CHECK_COUNT = 20
AGGREGATE_ONLY      = REJECTED

 1-3   ComparisonRule identity / ratification / fingerprint   (carried)
 4     baseline selector kind/spec validity                   (NEW, replaces
                                                              phantom 4-6)
 5     deterministic baseline candidate eligibility           (NEW)
 6     deterministic PRIOR_COMPARABLE_WINDOW resolution      (NEW)
 7-18  delta operator, measurement refs, Book 2 authority,
       methodology, coverage 12-16, metric content, input
       methodology policy                                     (carried)
19     TEMPORAL COMPARABILITY RESOLUTION                      (carried from v0.5)
20     DETERMINISTIC COMPARISON/CHANGE RECOMPUTATION          (carried from v0.5)
```

Checks 4–6 replace the phantom benchmark checks. The count stays 20 because the
structure contains 20 independently falsifiable authority checks — **not** for
cosmetic continuity.

---

# 5. Contract count

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

`BaselineSelectorSpec` adds no class: it is a nested value object with no
registry, no ledger, no independent lifecycle, and it cannot exist
authoritatively outside a `ComparisonRule`.

---

# 6. D6M decision impact

```text
D6M-1  unaffected
D6M-2  unaffected
D6M-3  unaffected — no new state class; comparison-rule ratification authority
       remains as established by the RATIFIED v0.4 amendment. v0.6 adds no
       authority and inherits none.
D6M-4  unaffected
D6M-5  unaffected and still OPEN_DEFERRED
```

---

# 7. StateRule benchmark — explicitly out of scope

```text
BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED
```

`StateRule.benchmark_methodology_ref` (`book6_states.py:178`) is a separate
accepted mechanism. v0.6 neither repurposes it nor claims to solve Class C
benchmark semantics.

---

# 8. Gates

```text
G-1  Zero regressions: all accepted Book 6 tests still pass (1341)
G-2  Zero regressions: full CSIA suite still passes (2162)
G-3  Zero regressions: Sensor unchanged from accepted baseline
     (2325 PASS / 14 FAIL / 4 SKIPPED)
G-4  Book 1-5 mutation count = 0; Sensor mutation count = 0
G-5  New amendment tests cover, each with a CONCRETE REAL TEST FUNCTION:
     stored-binary64 equality; non-finite rejection; signed-zero; same-metric
     unit identity; coverage applicability (all branches); temporal
     comparability (all three); selector validity; candidate eligibility;
     deterministic resolution; caller-authority refusal; reserved-selector
     rejection; fingerprint mutation; authority decay
G-6  ruff + mypy clean on new modules
G-7  traceability complete; 20 checks individually traceable
G-8  contract count == 2; HIDDEN_THIRD_CONTRACT == NONE
G-9  no epsilon / isclose / tolerance / Decimal / Fraction anywhere
G-10 no BenchmarkRule / BenchmarkRuleRegistry / benchmark fingerprint exists
G-11 no rolling mean / median / distribution / epoch implementation
G-12 no observed_at baseline ordering; no random or caller-order selection
G-13 re-acceptance required before this amendment's code is Book 6
G-14 phantom-citation regression check passes (boundary v0.4 invariant)
G-15 FAILURE OF ANY GATE = HOLD
```

Baselines 1341 / 2162 / 2343 were independently reproduced during this planning
work, so G-1..G-3 are anchored to measured numbers.

---

# 9. Status

```text
STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE


IMPLEMENTATION_REMAINS_UNAUTHORIZED = TRUE
```

v0.4 remains ratified and unchanged. v0.5 remains an unratified draft.

**Not authorized and not performed:** any implementation, source or test change,
any `BenchmarkRule` or `BenchmarkRuleRegistry`, any benchmark-rule ratification,
any rolling mean / rolling median / historical distribution / baseline epoch
implementation, any `observed_at` baseline ordering, any random or caller-order
selection, any caller-selected authoritative baseline, Book 7 or Book 8 work,
live acquisition, and any branch creation, force-push, rebase or history rewrite.
