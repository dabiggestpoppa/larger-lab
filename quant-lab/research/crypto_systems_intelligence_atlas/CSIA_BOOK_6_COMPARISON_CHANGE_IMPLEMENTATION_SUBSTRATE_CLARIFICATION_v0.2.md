# CSIA — BOOK 6 COMPARISON / CHANGE IMPLEMENTATION-SUBSTRATE CLARIFICATION — v0.2

**Document ID:** CSIA-B6-ISC-002
**Version:** 0.2
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Kind:** GOVERNANCE SUCCESSOR / ADDENDUM
**Supersedes (before ratification):** draft
`..._IMPLEMENTATION_SUBSTRATE_CLARIFICATION_v0.1.md`. v0.1 was never
ratified, so nothing ratified is replaced.

**Relationship:** successor to, and additive clarification of, the RATIFIED
`CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md` (anchor
`28bfac52c23c891ebb54e9924dedc925a859b359`, ratified in `8557f4df8`).

**Ratified history is NOT rewritten.** No ratified artifact is edited in place.

**This artifact grants no implementation authority.**

---

# 0. All five resolutions

```text
GAP_1_RESOLUTION = 1A-STRICT   keep stored binary64; correct doctrine wording
GAP_2_RESOLUTION = 2D          SAME_METRIC_EXACT_UNIT_IDENTITY
GAP_3_RESOLUTION = 3C          COVERAGE_RULE_PRESENCE_DERIVATION
GAP_4_RESOLUTION = 4D          EXPLICIT_TEMPORAL_COMPARABILITY
GAP_5_RESOLUTION = 5E          COMPARISON-RULE-OWNED BASELINE SELECTOR
```

`GAP_5A / 5B / 5C / 5D` are **NOT SELECTED**.

Sections 1–4 carry v0.1's GAP-1..GAP-4 resolutions forward unchanged. Section 5
is new and covers GAP-5.

---

# 1. GAP-1 — `1A-STRICT` (carried forward unchanged)

```text
CANONICAL_VALUE   = FINITE_STORED_BINARY64
CANONICAL_EQUALITY = EXACT_EQUALITY_OF_STORED_CANONICAL_BINARY64

REAL_NUMBER_EXACTNESS_CLAIM  = FALSE
STORED_VALUE_EXACTNESS_CLAIM = TRUE

MeasurementObservation.value public type change = NOT PERMITTED
EPSILON / math.isclose / APPROXIMATE_EQUALITY    = NOT PERMITTED
Decimal migration / Fraction migration           = NOT PERMITTED
```

`MeasurementObservation.value: float | None` at `book6_records.py:113` unchanged.

```text
FINITE_NUMERIC_INPUT_REQUIRED = TRUE
non-finite (NaN, +Inf, -Inf) -> INSUFFICIENT_DATA
BOOK6_NAN_SENTINEL_INHERITED  = FALSE   (book6_core.py:181 NOT reused)
```

Non-finiteness is rejected at the validated-input boundary via
`math.isfinite()` — exact for binary64, not an approximate predicate.

```text
CANONICAL_ZERO = (value == 0.0)      +0.0 == -0.0
SIGNED_ZERO_SEMANTIC_DISTINCTION = NOT CREATED
```

---

# 2. GAP-2 — `2D` same-metric exact-unit identity (carried forward unchanged)

```text
TEMPORAL_UNIT_COMPATIBILITY = EXACT SAME-METRIC UNIT IDENTITY

arithmetic permitted only when:
 1. baseline observation resolves to the bound metric_definition_ref
 2. comparison observation resolves to the SAME metric_definition_ref
 3. baseline observation.unit   == MetricDefinition.unit
 4. comparison observation.unit == MetricDefinition.unit
```

Substrate: `MetricDefinition.unit` non-nullable at
`book6_definitions.py:148`; `MeasurementObservation.unit` at
`book6_records.py:114`.

```text
UNIT_CONVERSION / ALIASES / DIMENSIONAL_INFERENCE / UNIT_NORMALIZATION
    = NOT PERMITTED
UNIT_CONTRACT_CLASS_ADDED                     = FALSE
NEW_AUTHORITY_BEARING_CONTRACT_CLASS_FOR_UNITS = FALSE
HIDDEN_THIRD_CONTRACT                         = NONE
```

Grammar policy **P3 `unit_requirements` is WITHDRAWN**: its cited contract does
not exist, so the citation is removed rather than satisfied. That removal is the
mechanism by which GAP-2 closes without a new contract class.

---

# 3. GAP-3 — `3C` coverage-rule-presence derivation (carried forward)

```text
IF a CURRENT, RATIFIED, EXACT-METRIC-SCOPED CoverageSufficiencyRule exists
   for the bound metric:

    coverage_requirement_status       = REQUIRED
    coverage_applicability_source_ref = that rule's authority/binding

ELSE:

    coverage_requirement_status       = UNRESOLVED
    coverage_applicability_source_ref = ABSENT
        (single ratified meaning: NO_UPSTREAM_DETERMINATION_EXISTS)
```

Substrate: `CoverageRuleRegistry` `book6_coverage_rules.py:112`;
`rules_for_metric()` :215; `ratification_of()` :194; `authorize()` :227.
`authorize()` already refuses unregistered, unratified-for-current-version, and
scope-mismatched rules. Every refusal maps to `UNRESOLVED`.

The match is **exact `scope_metric_id` identity**, never a semantic read of
`denominator_rule` or `required_evidence_semantics` free text.

```text
CAN_DERIVE_NOT_APPLICABLE            = FALSE  (intentional)
NOT_APPLICABLE_FROM_ABSENCE          = FORBIDDEN
COVERAGE_SUFFICIENCY_RULES_RATIFIED  = 0      (canonical production)
SYNTHETIC_TEST_RULES_ALLOWED         = TRUE
SYNTHETIC_RULES_ARE_CANONICAL        = FALSE
```

---

# 4. GAP-4 — `4D` explicit temporal comparability (carried forward)

```text
TemporalComparabilityStatus = COMPARABLE | NOT_COMPARABLE | UNRESOLVED
```

Distinct from `CorpusVerdict`, `ComparabilityClass` (`book6_definitions.py:69`),
`StateName`, `ClaimState`. Applies only to the single-metric temporal engine.

```text
NOT_COMPARABLE -> change_kind = NOT_COMPARABLE
UNRESOLVED     -> change_kind = INSUFFICIENT_DATA
                   (or fail before authoritative change emission)
UNRESOLVED -> NOT_COMPARABLE = FORBIDDEN
```

Produced by replay check 19. `NOT_COMPARABLE` finally has a producing check,
closing the v0.4 defect in which `change_kind` contained an unproducible member.

```text
FALSE_COMPARISON_CORPUS = UNCHANGED
book6_comparability.py  = UNCHANGED
CorpusVerdict           = UNCHANGED
authorize_comparison()  = UNCHANGED
```

---

# 5. GAP-5 — `5E` comparison-rule-owned baseline selector

## 5.1 The phantom is retired (Phase 1)

```text
ACCEPTED_BENCHMARK_RULE_NAMESPACE = FALSE
BENCHMARK_RULE_RUNTIME            = NOT_IMPLEMENTED
BENCHMARK_RULES_RATIFIED         = 0
```

Verified against the accepted implementation branch `5f94c3f4`:

```text
$ grep -rn "Benchmark" src/crypto_systems_intelligence_atlas/*.py
(no output — zero matches across all 62 modules)
```

The five-token vocabulary (`PRIOR_COMPARABLE_WINDOW`, `ROLLING_MEAN`,
`ROLLING_MEDIAN`, `HISTORICAL_DISTRIBUTION`, `BASELINE_EPOCH`) was a **planning
vocabulary** named in Book 6 base plan v0.2 §5, which said plainly "**none is
chosen by this plan**". Ratified amendment v0.4 then promoted it into an
"accepted authority substrate reused unmodified". That promotion was the
phantom. History is recorded, not erased; see the ratification-record erratum.

## 5.2 The binding principle

```text
BASELINE SELECTION IS PART OF THE COMPARISON RULE'S DERIVATION SEMANTICS.
IT IS NOT A SEPARATELY AUTHORITY-BEARING BENCHMARK RULE.
```

`ComparisonRule` operator ratification already binds identity, version, canonical
fingerprint, derivation semantics, and supersession. Baseline-selection semantics
therefore live **inside** that binding as a closed, typed, fingerprinted
component — requiring no second registry, no second ledger, and no second
ratification act.

## 5.3 `BaselineSelectorSpec` ownership (Phase 2)

`BaselineSelectorSpec` is a **nested value object** carried by `ComparisonRule`.
It is **not**:

```text
a public authority-bearing contract
a separately ratified object
a separately registered object
a Book 2 Claim
a StateRule
a BenchmarkRule
```

```text
BASELINE_SELECTOR_INDEPENDENT_RATIFICATION = FALSE
BASELINE_SELECTOR_INDEPENDENT_REGISTRY      = FALSE
BASELINE_SELECTOR_AUTHORITY                = BOUND_INSIDE_COMPARISON_RULE
```

A `BaselineSelectorSpec` **cannot exist authoritatively outside a
`ComparisonRule`**: it has no registry, no ratification ledger, no independent
lifecycle, and it is fingerprinted as `ComparisonRule` content.

## 5.4 Contract count (Phase 3)

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

`BaselineSelectorSpec` does not raise the count because it cannot exist
authoritatively outside a `ComparisonRule`, has no registry, has no ratification
ledger, has no independent lifecycle authority, and is fingerprinted as
`ComparisonRule` content.

## 5.5 Initial executable selector set (Phase 4)

For amendment implementation v1, **exactly one** executable selector is ratified:

```text
EXECUTABLE_BASELINE_SELECTOR_COUNT = 1
EXECUTABLE_BASELINE_SELECTOR      = PRIOR_COMPARABLE_WINDOW
```

The remaining four historical names are **reserved and non-executable**:

```text
ROLLING_MEAN            = RESERVED_NOT_EXECUTABLE
ROLLING_MEDIAN          = RESERVED_NOT_EXECUTABLE
HISTORICAL_DISTRIBUTION = RESERVED_NOT_EXECUTABLE
BASELINE_EPOCH          = RESERVED_NOT_EXECUTABLE
```

Constructing an executable `ComparisonRule` naming a reserved selector is
**REJECTED**. They are not accepted runtime methods. They may become executable
only via separate successor governance defining inputs, parameters, window
semantics, aggregation semantics, missingness, fingerprint content, and tests.
**No placeholder behaviour.**

## 5.6 `PRIOR_COMPARABLE_WINDOW` semantics (Phase 5)

Input to the offline engine:

```text
- the current / comparison observation, or comparison window
- candidate baseline MeasurementObservation refs supplied by the caller
- the bound ComparisonRule
```

A candidate is **eligible** only if every structural identity matches:

```text
 1. same subject_ref
 2. same metric_definition_ref
 3. same metric-definition semantic fingerprint
 4. same MeasurementMethodology identity/version where the rule requires it
 5. same exact MetricDefinition.unit          (2D)
 6. compatible denominator semantics
 7. compatible cohort semantics where applicable
 8. same required WindowClass / window compatibility
 9. candidate valid time STRICTLY PRECEDES the comparison valid time
10. candidate satisfies input Book 2 authority requirements
11. candidate satisfies missingness requirements
```

Methodology identity is fully qualified: `MeasurementMethodology.identity`
returns `ref@version` (`book6_definitions.py:127–130`), so condition 4 is an
exact string comparison, not a fuzzy match.

**Selection-bias firewall.** Coverage result is **not** used to select the
candidate. Coverage is an **authorization gate applied after structural
selection**. Using coverage to *select* would let the authorization gate
influence which observation is treated as the baseline — a circularity. Only a
ratified comparison contract that explicitly requires otherwise may deviate.

## 5.7 Deterministic ordering (Phase 6)

Among eligible candidates, choose the **latest valid prior** candidate under a
closed deterministic ordering:

```text
 1. greatest valid_time END, strictly before comparison valid_time START
 2. if tied: greatest valid_time START
 3. if still tied: stable lexical measurement_ref  (deterministic final
    tie-break ONLY)
```

```text
BASELINE_SELECTION_DETERMINISTIC = TRUE
CALLER_ORDER_AFFECTS_BASELINE    = FALSE
```

Prohibited as ordering inputs: `observed_at` as economic-time ordering, caller
list order, insertion order, randomness, latest ingestion time. The lexical
`measurement_ref` tie-break exists only so a tie resolves to exactly one
observation rather than to implementation-defined behaviour.

## 5.8 No eligible baseline (Phase 7)

```text
NO_ELIGIBLE_PRIOR_BASELINE
    -> INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
```

There is **no silent fallback**: no rolling mean, no epoch baseline, no
arbitrary first item, no nearest incompatible observation. `BASELINE_UNAVAILABLE`
is a first-class outcome under the existing v0.5 missingness contract.

## 5.9 Multiple eligible baselines (Phase 8)

Deterministic selection must yield **exactly one** baseline
window/observation set.

```text
BASELINE RESULT = ONE MeasurementObservation
```

**Substrate finding that resolves this without inventing aggregation.**
`MetricDefinition.aggregation: AggregationSemantics` already exists
(`book6_definitions.py:151`), with the accepted closed set `NONE | SUM | MEAN |
LAST | DISTRIBUTION` (`book6_definitions.py:59–67`). An observation of an
interval window class (`INTERVAL_WINDOW_CLASSES`, `book6_grammar.py:185`)
already **carries the aggregated value** that the metric's declared aggregation
semantics produced. The selector selects among existing observations; it never
computes an aggregate.

Therefore:

```text
PRIOR_COMPARABLE_WINDOW does NOT aggregate. It selects.
Aggregation semantics belong to the MetricDefinition, not to the selector.
```

If a metric declares `aggregation == NONE` and multiple observations exist for
one comparison window, that is **not** a selector problem — it is a genuine new
decision, and the outcome is:

```text
HOLD and surface it. Do NOT silently aggregate.
Do NOT let PRIOR_COMPARABLE_WINDOW become ROLLING_MEAN or any other aggregator.
```

This is the only path by which 5E could require a new operator decision, and it
is recorded here rather than resolved by assumption.
## 5.10 Selector fingerprint (Phase 9)

`BaselineSelectorSpec` semantic content is included **inside the canonical
`ComparisonRule` fingerprint**. Minimum fingerprinted content:

```text
selector_kind
window compatibility requirements
methodology compatibility requirements
denominator / cohort requirements, where selector-specific
any deterministic ordering policy
```

```text
FREE TEXT IN SELECTOR FINGERPRINT = NOT PERMITTED
ARBITRARY CALLABLE                = NOT PERMITTED
EXPRESSION LANGUAGE               = NOT PERMITTED
eval / exec                       = NOT PERMITTED
```

Mutation under the same `ComparisonRule` identity **must** change the rule
fingerprint and invalidate prior authority. The accepted precedent for a
drift-guarded canonical field list is `METHODOLOGY_CANONICAL_FIELDS`
(`book6_methodology.py:85-97`), which pins exactly which fields enter
`canonical_methodology_spec()` (`:99`) and therefore `methodology_fingerprint()`
(`:132`).

## 5.11 Ratification-binding repair (Phase 10)

The phantom binding is **removed**:

```text
baseline benchmark methodology identity / version / canonical fingerprint
```

It is replaced by the **baseline selector spec fingerprint inside the
`ComparisonRule`'s own canonical fingerprint / derivation binding**.

```text
SEPARATE_BENCHMARK_AUTHORITY_BINDING   = NONE
COMPARISON_RULE_BINDS_BASELINE_SELECTOR = TRUE
LATE_BOUND_BASELINE_POLICY             = NOT PERMITTED
```

## 5.12 Baseline authority replay (Phase 12)

At use time the engine **re-resolves** baseline selection rather than trusting a
stored result. It verifies:

```text
- candidate measurements still exist
- their Book 2 authority remains current
- metric / methodology / unit / window bindings still match
- the same deterministic selector still selects the recorded baseline refs
```

```text
if current resolution differs from the recorded baseline:
    current_authority = FALSE
    historical ChangeObservation is PRESERVED
    NO silent rebaseline
```

## 5.13 Caller authority (Phase 13)

Caller **may** provide, for offline resolution:

```text
candidate baseline refs
```

Caller may **NOT** authoritatively provide:

```text
selected_baseline_ref
baseline_selector_result
baseline_is_valid
benchmark_rule_ref
benchmark_methodology_ref
```

If an expected baseline ref is accepted for tests, the engine **recomputes and
compares**; a mismatch **raises**, and stored authority uses the **engine**
result, never the caller's.

## 5.14 StateRule benchmark impact (Phase 15)

`StateRule.benchmark_methodology_ref` (`book6_states.py:178`, enforced at
`:214`) is a **separate, accepted Book 6 mechanism** for Class C threshold /
benchmark states (`StateClass.C_THRESHOLD_BENCHMARK`, `book6_states.py:72`).

```text
BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED
COMPARISON_RULE_BASELINE_SELECTOR_REUSES_STATE_RULE_AUTHORITY = FALSE
```

This GAP-5 repair closes **only** the comparison/change amendment's baseline
path. It does **not** repurpose `BaselineSelectorSpec` as `StateRule` benchmark
authority, and it does **not** pretend to solve Class C state benchmark
semantics. The two remain separate, both currently unratified.

## 5.15 Replay repair (Phase 11)

The ratified 19-check replay's checks 4–6 were inherited from the phantom
benchmark model. v0.6 grammar replaces them honestly. Total stays **20** — but
not for cosmetic continuity: it is 20 because the successor structure below
contains 20 independently falsifiable authority checks. If implementation
proves more are needed, the count changes; it is not pinned by nostalgia.

## 5.16 Summary

```text
ACCEPTED_BENCHMARK_RULE_NAMESPACE      = FALSE
BENCHMARK_RULE_RUNTIME                 = NOT_IMPLEMENTED
BENCHMARK_RULES_RATIFIED              = 0
BASELINE_SELECTOR_INDEPENDENT_RATIFICATION = FALSE
BASELINE_SELECTOR_INDEPENDENT_REGISTRY      = FALSE
BASELINE_SELECTOR_AUTHORITY            = BOUND_INSIDE_COMPARISON_RULE
EXECUTABLE_BASELINE_SELECTOR_COUNT     = 1
EXECUTABLE_BASELINE_SELECTOR          = PRIOR_COMPARABLE_WINDOW
ROLLING_MEAN / ROLLING_MEDIAN / HISTORICAL_DISTRIBUTION / BASELINE_EPOCH
                                    = RESERVED_NOT_EXECUTABLE
BASELINE_SELECTION_DETERMINISTIC      = TRUE
CALLER_ORDER_AFFECTS_BASELINE         = FALSE
OBSERVED_AT_USED_FOR_BASELINE_ORDERING = FALSE
NO_ELIGIBLE_PRIOR_BASELINE            = INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
BASELINE_RESULT                       = ONE MeasurementObservation
SELECTOR_AGGREGATES                   = FALSE
SEPARATE_BENCHMARK_AUTHORITY_BINDING   = NONE
COMPARISON_RULE_BINDS_BASELINE_SELECTOR = TRUE
BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME  = UNRATIFIED / UNIMPLEMENTED
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT                 = NONE

GAP_5A / 5B / 5C / 5D = NOT SELECTED
```

---

# 6. Status

```text
STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

Ratifying this artifact does not authorize implementation. It authorizes the
successor grammar v0.6, plan v0.6, boundary v0.4, ratification-record erratum
v0.1, and test spec v0.3, after which the authorization review v0.3 must pass.

**Not authorized and not performed:** any implementation, source or test change,
any `BenchmarkRule`, any `BenchmarkRuleRegistry`, any benchmark-rule
ratification, any rolling mean / rolling median / historical distribution /
baseline epoch implementation, any `observed_at` baseline ordering, any
random or caller-order selection, any caller-selected authoritative baseline,
Book 7 or Book 8 work, live acquisition, and any branch creation, force-push,
rebase or history rewrite.
