# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PLAN — v0.5

**Document ID:** CSIA-B6-CAP-005
**Version:** 0.5
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Kind:** NARROW IMPLEMENTATION-SUBSTRATE CLARIFICATION SUCCESSOR

## Relationship to v0.4 — stated precisely

```text
v0.4 = RATIFIED BASE PLAN          (anchor 28bfac52c23c891ebb54e9924dedc925a859b359,
                                     ratified in 8557f4df82a67434951b2f9682142a59125f5153)
v0.5 = NARROW IMPLEMENTATION-SUBSTRATE CLARIFICATION SUCCESSOR
```

**v0.4 is NOT erroneous and NOT unratified.** It was correctly ratified and it
remains in force. v0.5 does not reopen, reverse or replace it. v0.5 records the
substrate precision the v0.4 authorization review found to be under-specified,
and adds nothing beyond that.

**Implementation remains unauthorized until v0.5 is ratified AND the
implementation authorization review v0.2 passes.**

---

# 1. Scope (unchanged from v0.4; count remains 2)

```text
ADDED:     ComparisonRule, ChangeObservation
REUSED:    coverage-sufficiency rules (existing CoverageRuleRegistry)
REMOVED:   the comparison_semantics policy section
           (v0.4 removed it; v0.5 further WITHDRAWS policy P3
            unit_requirements, whose cited contract does not exist)
UNCHANGED: MetricDefinition, MeasurementMethodology, MeasurementObservation,
           ValuationObservation, NormalizationRule, StateRule,
           FundamentalStateVector, all D6M decisions, all accepted tests
```

**Deviation from v0.4 §2, stated openly.** v0.4 §2 listed under `REUSED`
"accepted benchmark-rule namespace". The phantom-citation sweep established that
this namespace **does not exist** in the codebase. v0.5 **does not repeat that
claim** and does not treat the namespace as available. GAP-5 is recorded as OPEN
(§6) rather than silently carried forward or silently dropped.

This is the one place where v0.5's scope statement differs from v0.4's, and the
difference is a **correction of an unverifiable assertion**, not a scope change.

---

# 2. The four resolutions

## 2.1 GAP-1 — `1A-STRICT`

Keep binary64 storage; correct the doctrine wording.

```text
CANONICAL_VALUE  = FINITE_STORED_BINARY64
CANONICAL_EQUALITY = EXACT_EQUALITY_OF_STORED_CANONICAL_BINARY64

REAL_NUMBER_EXACTNESS_CLAIM  = FALSE
STORED_VALUE_EXACTNESS_CLAIM = TRUE

EPSILON / ISCLOSE / TOLERANCE / APPROXIMATE_EQUALITY = NOT PERMITTED
Decimal migration / Fraction migration              = NOT PERMITTED
MeasurementObservation.value public type change     = NOT PERMITTED
```

`MeasurementObservation.value: float | None` (`book6_records.py:113`) unchanged.

## 2.2 GAP-2 — `2D` same-metric exact-unit identity

```text
TEMPORAL_UNIT_COMPATIBILITY = EXACT SAME-METRIC UNIT IDENTITY

arithmetic permitted only when:
  baseline.metric_definition_ref  == bound metric_definition_ref
  comparison.metric_definition_ref == the SAME metric_definition_ref
  baseline.unit   == MetricDefinition.unit
  comparison.unit == MetricDefinition.unit

UNIT_CONVERSION / ALIASES / DIMENSIONAL_INFERENCE / NORMALIZATION = NOT PERMITTED
UNIT_CONTRACT_CLASS_ADDED                     = FALSE
NEW_AUTHORITY_BEARING_CONTRACT_CLASS_FOR_UNITS = FALSE
HIDDEN_THIRD_CONTRACT                         = NONE
```

Policy P3 `unit_requirements` is **WITHDRAWN**. Its cited contract does not
exist; the withdrawal is what closes GAP-2 without adding a contract class.

## 2.3 GAP-3 — `3C` coverage-rule-presence derivation

```text
IF current + ratified + exact-metric-scoped CoverageSufficiencyRule exists:
    coverage_requirement_status       = REQUIRED
    coverage_applicability_source_ref = that rule's authority/binding
ELSE:
    coverage_requirement_status       = UNRESOLVED
    coverage_applicability_source_ref = ABSENT
                                        (NO_UPSTREAM_DETERMINATION_EXISTS)
```

Uses the existing `CoverageRuleRegistry` only. Exact identifier equality; no
semantic heuristic; no new registry; no new authority class.

```text
CAN_DERIVE_NOT_APPLICABLE       = FALSE   (intentional)
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0    (canonical production)
SYNTHETIC_TEST_RULES_ALLOWED    = TRUE
SYNTHETIC_RULES_ARE_CANONICAL   = FALSE
```

## 2.4 GAP-4 — `4D` explicit temporal comparability

```text
TemporalComparabilityStatus = COMPARABLE | NOT_COMPARABLE | UNRESOLVED
```

Closed, typed, produced by new replay check 19. Distinct from `CorpusVerdict`,
`ComparabilityClass`, `StateName`, `ClaimState`.

```text
NOT_COMPARABLE -> change_kind = NOT_COMPARABLE
UNRESOLVED     -> change_kind = INSUFFICIENT_DATA
                 (or fail before authoritative change emission)
UNRESOLVED mapped to NOT_COMPARABLE = FORBIDDEN
```

`FALSE_COMPARISON_CORPUS` and `book6_comparability.py` are **UNCHANGED**.

---

# 3. Replay — 20 checks

```text
REPLAY_CHECK_COUNT = 20
AGGREGATE_ONLY      = REJECTED

 1-18  unchanged from v0.4
19     TEMPORAL COMPARABILITY RESOLUTION              (NEW)
20     DETERMINISTIC COMPARISON / CHANGE RECOMPUTATION (was v0.4 check 19)
```

All 20 independently falsifiable. Checks 19 and 20 are separately falsifiable:
check 19 can pass while check 20 fails, and check 19 can refuse so check 20 never
runs. The v0.4 replay had no such separation.

---

# 4. Contract count

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

Not new public contract classes: the binary64 clarification, the same-metric unit
identity law, the coverage applicability resolver (existing registry), the
`TemporalComparabilityStatus` enum, and the 20-check replay count.

If the implemented result is not exactly 2, the outcome is **HOLD**.

---

# 5. D6M decision impact

```text
D6M-1  unaffected — ChangeObservation is Book 6-local derived
D6M-2  unaffected — comparison performs no normalization; canonical arithmetic
       is fixed so none can be smuggled in
D6M-3  unaffected — no new state class. Comparison-rule ratification authority
       remains established by the RATIFIED v0.4 amendment on a D6M-3-consistent
       pattern. v0.5 adds no authority and inherits none.
D6M-4  unaffected — valuation authority untouched
D6M-5  unaffected and still OPEN_DEFERRED
```

v0.5 introduces **no new ratification authority of any kind**. It adds no
registry, no ratification path, and no benchmark namespace claim.

---

# 6. GAP-5 — recorded, not resolved

```text
GAP_5 = OPEN
```

The accepted benchmark-rule namespace does not exist. Grammar v0.4 §2's
`baseline_selection_methodology_ref` requirement stands as ratified and is
currently unsatisfiable. v0.5 does not resolve GAP-5, does not invent a
benchmark contract, and does not create a benchmark rule.

A separate operator decision is required before implementation authorization.

---

# 7. Gates

```text
G-1  Zero regressions: all accepted Book 6 tests still pass (1341)
G-2  Zero regressions: full CSIA suite still passes (2162)
G-3  Zero regressions: Sensor suite unchanged from its accepted baseline
     (2325 PASS / 14 FAIL / 4 SKIPPED; the 14 are the known canonical set)
G-4  Book 1-5 mutation count = 0; Sensor mutation count = 0
G-5  New amendment tests cover, each with a CONCRETE REAL TEST FUNCTION:
     stored-binary64 exact equality; non-finite rejection; signed-zero
     handling; same-metric unit identity; unit mismatch refusal; coverage
     applicability derivation (all five branches); temporal comparability
     derivation (all three outcomes); check 19 and check 20 separability
G-6  ruff + mypy clean on new modules
G-7  traceability complete; 20 checks individually traceable
G-8  contract count == 2, HIDDEN_THIRD_CONTRACT == NONE
G-9  no epsilon / isclose / tolerance / Decimal / Fraction anywhere
G-10 re-acceptance required before this amendment's code is Book 6
G-11 FAILURE OF ANY GATE = HOLD
```
work (1341 / 2162 / 2343 = 2325 + 14 + 4), so G-1..G-3 are anchored to verified
numbers rather than remembered ones.

---

# 8. Status

```text
STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE

IMPLEMENTATION_REMAINS_UNAUTHORIZED = TRUE
   until BOTH: (a) this v0.5 is operator-ratified, AND
               (b) implementation authorization review v0.2 passes,
   AND (c) GAP-5 is decided.
```

v0.4 remains ratified and unchanged. This v0.5 does not supersede it; it
clarifies the implementation substrate beneath it.

**Not authorized and not performed:** any implementation, any source or test
change, any float/Decimal/Fraction migration, any epsilon or isclose, any unit
ontology or conversion, any cross-metric corpus mutation, any coverage
applicability heuristic, any `NOT_APPLICABLE` by absence, any new canonical
coverage rule, any rule ratification, any Book 7 or Book 8 work, any live
acquisition, and any branch creation, force-push, rebase or history rewrite.
