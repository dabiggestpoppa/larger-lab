# CSIA — BOOK 6 COMPARISON / CHANGE IMPLEMENTATION AUTHORIZATION REVIEW — v0.3

**Document ID:** CSIA-B6-IAR-003
**Version:** 0.3
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — REVIEW VERDICT, NOT AN AUTHORIZATION
**Date:** 2026-10-02
**Supersedes as a review:** `..._AUTHORIZATION_REVIEW_v0.2.md`
(`READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION`, 9 TRUE / 1 NOT_SUPPORTABLE)
and v0.1 (HOLD, 5/10). Both are preserved as the historical record.

**Implementation branch audited:** `agent/crypto-systems-intelligence-atlas-book6-build` @ `5f94c3f40cea4441470c57671f51454da7377361`
**Accepted anchor:** `3919fb8052e216e94034a753fb258d338c5fa0dc` (ancestor; 0 implementation drift)
**Runtime tree:** 62 Python modules

**This review authorizes nothing.**

---

# 1. Verdict

```text
BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3
    = READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION

NO_UNRATIFIED_POLICY_NEEDED         = TRUE
NO_RUNTIME_AUTHORITY_GAP             = TRUE
NUMERIC_REPRESENTATION_SUFFICIENT    = TRUE
UNIT_ARITHMETIC_SOURCE_SUFFICIENT    = TRUE
BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT = TRUE
COVERAGE_RUNTIME_PATH_SUFFICIENT     = TRUE
ALL_REPLAY_CHECKS_IMPLEMENTABLE      = TRUE
NEGATIVE_SURFACE_TESTS_SPECIFIED     = TRUE
TRACEABILITY_PLAN_COMPLETE           = TRUE
UPSTREAM_FREEZE_PRESERVABLE          = TRUE

SCORE = 10 TRUE / 0 FALSE
```

**All ten criteria are now TRUE.** For the first time in this program, no
criterion is carried as an exception.

## 1.1 Criterion renamed, as directed

```text
OLD (retired): BENCHMARK_RUNTIME_PATH_SUFFICIENT
NEW:           BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT
```

The old name asserted a benchmark runtime that **does not exist and is not being
created**. Carrying it forward would have been a small phantom of the same family
as the one this review retires: a criterion name implying an authority that
cannot resolve. 5E creates no benchmark runtime, so the criterion is renamed to
describe what actually exists — the `ComparisonRule`-owned baseline selection
path.

## 1.2 Why the tenth criterion can be TRUE

GAP-5's phantom is **retired**, not satisfied. No `BenchmarkRule`, no
`BenchmarkRuleRegistry`, no benchmark fingerprint, and no benchmark ratification
is required anywhere. Baseline selection is a nested, fingerprinted component of
`ComparisonRule`, so the runtime path is `ComparisonRule` ratification plus a
deterministic selector over accepted `MeasurementObservation` fields — all of
which exist.

```text
ACCEPTED_BENCHMARK_RULE_NAMESPACE = FALSE
BENCHMARK_RULE_RUNTIME            = NOT_IMPLEMENTED
BENCHMARK_RULES_RATIFIED         = 0
```

The path is sufficient **because nothing phantom is required**.

---

# 2. Criterion-by-criterion evidence

## 2.1 `NO_UNRATIFIED_POLICY_NEEDED = TRUE`

Every normative statement across substrate v0.2, grammar v0.6, plan v0.6,
boundary v0.4 and test spec v0.3 classifies as a definition over accepted
substrate, a derivation, or a removal:

| statement | class | anchor |
|---|---|---|
| finite stored binary64 semantics | definition | `book6_records.py:113` |
| `math.isfinite()` input rejection | definition | stdlib |
| canonical zero `value == 0.0` | definition | IEEE-754 |
| same-metric unit identity | derivation | `book6_definitions.py:148`, `book6_records.py:114` |
| coverage applicability 3C | derivation | `book6_coverage_rules.py:112/215/194/227` |
| `TemporalComparabilityStatus` | closed enum, no authority | grammar §3.1 |
| `BaselineSelectorSpec` | nested value object, no authority | grammar §2.2 |
| `PRIOR_COMPARABLE_WINDOW` | derivation over accepted fields | grammar §2.3-§2.4 |
| 20-check replay | derivation | grammar §5 |
| withdrawal of policy P3 | **removes** a policy citation | grammar §8.2 |
| retirement of phantom benchmark binding | **removes** an authority claim | grammar §0.1 |

```text
NO_UNRATIFIED_POLICY_NEEDED = TRUE
NEW_VALUES_DOMAINS_OR_DOMAINS_INVENTED = 0
EPSILON / TOLERANCE / MATERIALITY / SIGNIFICANCE = NONE
NEW DELTA OPERATORS = 0
```

The only policy changes are **removals** — P3 withdrawn, phantom benchmark
binding removed. Neither adds authority.

## 2.2 `NO_RUNTIME_AUTHORITY_GAP = TRUE`

Every governance decision routes through an already-accepted registry or ledger:
`CoverageRuleRegistry` for coverage (3C), `ComparisonRule` ratification for
baseline selection (5E), `Book6MethodologyRegistry` for methodology, Book 2 for
input authority. **No new registry, no new ratification path, no new authority
class.**

## 2.3 `NUMERIC_REPRESENTATION_SUFFICIENT = TRUE`

1A-STRICT defines the canonical value as the finite stored binary64 and
canonical equality as exact stored-value equality. Doctrine wording repaired
prospectively in grammar v0.6 §0.3. `MeasurementObservation.value` unchanged at
`float | None`. No epsilon, no isclose, no migration. Non-finite rejected at the
boundary; Book 6 NaN sentinel not inherited. Tests NUM-1..NUM-6.

## 2.4 `UNIT_ARITHMETIC_SOURCE_SUFFICIENT = TRUE`

2D fully determines arithmetic validity for single-metric temporal comparison.
Both operands resolve to the bound metric and both carry
`MetricDefinition.unit`. P3 withdrawn, closing the untestable POL-11. No
dimensional ontology, no conversion, no taxonomy. Tests UNIT-1..UNIT-4.

## 2.5 `BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT = TRUE`

The path, with each element verified in the accepted branch:

```text
ComparisonRule operator ratification      (authority; exists by design)
ComparisonRule canonical fingerprint      (precedent: canonical_methodology_spec
                                           book6_methodology.py:99,
                                           methodology_fingerprint :132)
MeasurementObservation fields             book6_records.py:113-119
  subject_ref, metric_definition_ref, unit, valid_time, methodology_ref@version
MeasurementMethodology.identity          book6_definitions.py:127-130
MetricDefinition.unit                     book6_definitions.py:148
MetricDefinition.aggregation             book6_definitions.py:151
WindowClass / INTERVAL_WINDOW_CLASSES    book6_grammar.py:163, 185
```

Selection is exact comparison over these fields plus a closed ordering. No
aggregation is performed by the selector (`SELECTOR_AGGREGATES = FALSE`),
because `MetricDefinition.aggregation` already declares how repeated
observations of a window aggregate — so a baseline observation already carries
its aggregated value.

Tests BASE-1..BASE-23.

## 2.6 `COVERAGE_RUNTIME_PATH_SUFFICIENT = TRUE`

3C is an exact-metric-id lookup against `CoverageRuleRegistry`, whose
`authorize()` already refuses unregistered, unratified-for-current-version and
scope-mismatched rules. No heuristic, no new registry.
`CAN_DERIVE_NOT_APPLICABLE = FALSE`. Tests CAPP-1..CAPP-6.

## 2.7 `ALL_REPLAY_CHECKS_IMPLEMENTABLE = TRUE`

```text
REPLAY_CHECK_COUNT = 20
AGGREGATE_ONLY      = REJECTED
```

Checks 4–6 are the new selector checks replacing the phantom benchmark checks.
All 20 independently falsifiable; checks 19 and 20 separately falsifiable. The
count is 20 because the structure contains 20 independently falsifiable
authority checks — **not** for cosmetic continuity, and it changes if
implementation proves more are needed.

## 2.8 `NEGATIVE_SURFACE_TESTS_SPECIFIED = TRUE`

45 carried negative-surface cases (9 forbidden field names x 5 attack vectors),
plus BASE-2..BASE-5 (reserved selectors rejected), BASE-20/BASE-21 (no benchmark
registry, no `benchmark_rule_ref` field), BASE-23 (no callable/expression),
PHANTOM-1..PHANTOM-6 (phantom-citation regression). No forbidden field is
introduced.

## 2.9 `TRACEABILITY_PLAN_COMPLETE = TRUE`

20 checks individually traceable; 4 fingerprint determinism tests carried;
selector fingerprint content enumerated in grammar v0.6 §2.7.

## 2.10 `UPSTREAM_FREEZE_PRESERVABLE = TRUE`
anchor untouched; 0 commits after acceptance. Regression baselines independently
reproduced: 1341 / 2162 / 2343.

---

# 3. Contract-count audit

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

`BaselineSelectorSpec` adds no class: no registry, no ledger, no independent
lifecycle, cannot exist authoritatively outside a `ComparisonRule`. Boundary
v0.4 §4 classifies it as nested rule content.

---

# 4. Standing condition — recorded, not waived

Phase 8's condition remains live:

```text
IF metric.aggregation == NONE AND multiple observations exist for one
   comparison window:
       -> HOLD and surface as a genuine new operator decision
```

This is a **runtime condition**, not a defect in the substrate. It is recorded so
that if it ever arises during implementation it escalates rather than silently
becoming an aggregator.

---

# 5. Verdict and non-authorizations

```text
REVIEW = READY_PENDING_SUBSTRATE_CLARIFICATION_RATIFICATION

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
SUBSTRATE_CLARIFICATION_RATIFIED = FALSE
D6M_5                           = OPEN_DEFERRED
COMPARISON_RULES_RATIFIED       = 0
BENCHMARK_RULES_RATIFIED        = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
```

**Prerequisites before implementation authorization could be considered:**

1. Operator ratifies substrate clarification v0.2.
2. Operator ratifies grammar v0.6, plan v0.6, boundary v0.4, ratification-record
   erratum v0.1, and test spec v0.3.
3. Operator records the Class C `StateRule` benchmark question as a separate
   open item (it is explicitly out of scope here).
4. This review is re-run post-ratification.

None has occurred.

**Not authorized and not performed:** any implementation, source or test change,
Book 6 re-acceptance, any rule ratification, any `BenchmarkRule` or
`BenchmarkRuleRegistry`, Book 7 or Book 8, live acquisition, and any branch
creation, force-push, rebase or history rewrite.
