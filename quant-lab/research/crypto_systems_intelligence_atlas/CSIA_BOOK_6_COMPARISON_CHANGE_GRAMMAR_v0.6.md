# CSIA — BOOK 6 COMPARISON / CHANGE GRAMMAR — v0.6

**Document ID:** CSIA-B6-CG-006
**Version:** 0.6
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Supersedes:** nothing.

**Preserved history:**
- `..._GRAMMAR_v0.4.md` — **RATIFIED, UNCHANGED, IN FORCE**
- `..._GRAMMAR_v0.5.md` — draft, never ratified; superseded here before
  ratification

**Authority under:** `D7N-7 = A`; boundary v0.4; substrate clarification v0.2
(this document's basis, itself `DRAFT_PENDING_OPERATOR_RATIFICATION`).

**This document grants no implementation authority.**

---

# 0. Delta from v0.5 and v0.4

## 0.1 Phantom language removed (Phase 17)

| phantom term | v0.6 disposition |
|---|---|
| accepted `BenchmarkRule` | **REMOVED** — never existed in runtime |
| `BenchmarkRuleRegistry` | **REMOVED** — never existed |
| benchmark-rule fingerprint | **REMOVED** — replaced by selector-spec fingerprint inside `ComparisonRule` |
| individual benchmark-rule ratification | **REMOVED** — authority is `ComparisonRule` ratification |
| "accepted benchmark-rule namespace" | **REMOVED** — was a planning vocabulary, never accepted |

Each is replaced by the `ComparisonRule`-owned `BaselineSelectorSpec`.

```text
ACCEPTED_BENCHMARK_RULE_NAMESPACE = FALSE
BENCHMARK_RULE_RUNTIME            = NOT_IMPLEMENTED
BENCHMARK_RULES_RATIFIED         = 0
```

## 0.2 What v0.6 carries forward from v0.5 unchanged

§1.0 finite stored binary64 semantics; §1.4 same-metric exact-unit identity;
§2.1 coverage applicability 3C; §3.1–§3.4 `TemporalComparabilityStatus` and its
`change_kind` mapping; §4 separations; §6 `AC-17`; §7 `AC-18`/`AC-18a`;
§8.1 nullable inventory; §8.2 policy inventory (P3 withdrawn); §9 ownership.

**No unrelated redesign.**

## 0.3 Repaired doctrine wording (carried)

| overbroad phrase | canonical replacement |
|---|---|
| "exact canonical equality" | "exact equality of the finite stored canonical binary64 values before any presentation/display transformation" |
| "canonical unrounded value" | "finite stored canonical binary64 value prior to display rounding" |

```text
REAL_NUMBER_EXACTNESS_CLAIM  = FALSE
STORED_VALUE_EXACTNESS_CLAIM = TRUE
```

---

# 1. Canonical law

§1.0 (finite stored binary64, non-finite rejection, canonical zero) and §1.4
(same-metric exact-unit identity) carry from v0.5 verbatim. One v0.6 change:
§1.6 gains the baseline-selection firewall.

## 1.6 baseline-selection firewall (NEW)

Baseline selection is a **derivation inside `ComparisonRule`**, not a policy.

```text
BASELINE_SELECTION_IS_RULE_DERIVATION_SEMANTICS = TRUE
BASELINE_SELECTION_POLICY_PARAMETER              = NOT PERMITTED
LATE_BOUND_BASELINE_POLICY                      = NOT PERMITTED
```

A rule author may not supply a baseline **result**, a baseline **validity**
flag, or a baseline **ordering policy** as free text, callable, or expression.
The only authorable content is the closed `BaselineSelectorSpec` of §2.2.

---

# 2. `ComparisonRule` v0.6

## 2.1 Coverage applicability (carried from v0.5 §2.1, unchanged)

```text
IF a CURRENT, RATIFIED, EXACT-METRIC-SCOPED CoverageSufficiencyRule exists:
    coverage_requirement_status       = REQUIRED
    coverage_applicability_source_ref = that rule's authority/binding
ELSE:
    coverage_requirement_status       = UNRESOLVED
    coverage_applicability_source_ref = ABSENT
        (NO_UPSTREAM_DETERMINATION_EXISTS)
```

`NOT_APPLICABLE` is not derivable. `CAN_DERIVE_NOT_APPLICABLE = FALSE`.

## 2.2 `BaselineSelectorSpec` (NEW — replaces the phantom field)

The phantom field is **removed**:

```text
baseline_selection_methodology_ref   (REQUIRED, citing an ACCEPTED benchmark
                                      rule from a five-member namespace)
```

It is **replaced** by a nested, typed, fingerprinted value object:

```text
baseline_selector: BaselineSelectorSpec   REQUIRED
```

### 2.2.1 Structure

```text
BaselineSelectorSpec {
  selector_kind:              BaselineSelectorKind  REQUIRED
  window_compatibility:       closed requirements    REQUIRED
  methodology_compatibility:  closed requirements    REQUIRED
  denominator_requirements:   closed requirements, where selector-specific
  cohort_requirements:        closed requirements, where selector-specific
  ordering_policy:            BaselineOrderingPolicy REQUIRED (closed enum)
}
```

### 2.2.2 Ownership

```text
BASELINE_SELECTOR_INDEPENDENT_RATIFICATION = FALSE
BASELINE_SELECTOR_INDEPENDENT_REGISTRY      = FALSE
BASELINE_SELECTOR_AUTHORITY                = BOUND_INSIDE_COMPARISON_RULE
```

`BaselineSelectorSpec` is a nested value object. It is **not** a public
authority-bearing contract, not separately ratified, not separately registered,
not a Book 2 `Claim`, not a `StateRule`, not a `BenchmarkRule`. It cannot exist
authoritatively outside a `ComparisonRule`, because it has no registry, no
ratification ledger, and no independent lifecycle.

### 2.2.3 `BaselineSelectorKind` — closed

```text
EXECUTABLE:
    PRIOR_COMPARABLE_WINDOW

RESERVED_NOT_EXECUTABLE:
    ROLLING_MEAN
    ROLLING_MEDIAN
    HISTORICAL_DISTRIBUTION
    BASELINE_EPOCH
```

```text
EXECUTABLE_BASELINE_SELECTOR_COUNT = 1
```

Constructing a `ComparisonRule` whose `selector_kind` is any reserved name is
**REJECTED**. Reserved names are not accepted runtime methods and carry **no
placeholder behaviour**. They may become executable only via separate successor
governance specifying inputs, parameters, window semantics, aggregation
semantics, missingness, fingerprint content, and tests.

### 2.2.4 `BaselineOrderingPolicy` — closed

```text
LATEST_PRIOR_VALID_TIME_END_THEN_START_THEN_LEXICAL_REF
```

The only permitted value. No caller ordering, no `observed_at` economic-time
ordering, no ingestion time, no randomness, no insertion order.

## 2.3 `PRIOR_COMPARABLE_WINDOW` eligibility (Phase 5)

Given the comparison observation, caller-supplied **candidate** baseline refs,
and the bound `ComparisonRule`, a candidate is eligible only if all hold:

```text
 1. same subject_ref
 2. same metric_definition_ref
 3. same metric-definition semantic fingerprint
 4. same MeasurementMethodology identity/version where the rule requires it
 5. same exact MetricDefinition.unit          (§1.4, 2D)
 6. compatible denominator semantics
 7. compatible cohort semantics where applicable
 8. same required WindowClass / window compatibility
 9. candidate valid_time STRICTLY PRECEDES comparison valid_time
10. candidate satisfies input Book 2 authority requirements
11. candidate satisfies missingness requirements
```

Condition 4 uses `MeasurementMethodology.identity` = `ref@version`
(`book6_definitions.py:127–130`): an exact string comparison, not a fuzzy match.

**Selection-bias firewall.** Coverage is an **authorization gate applied AFTER
structural selection**, never a selection input. Using coverage to choose the
candidate would make the authorization gate influence which observation is the
baseline — circular. Only a ratified contract explicitly requiring otherwise
may deviate.

## 2.4 Deterministic ordering (Phase 6)

```text
 1. greatest valid_time END, strictly before comparison valid_time START
 2. if tied: greatest valid_time START
 3. if still tied: stable lexical measurement_ref   (final tie-break ONLY)
```

```text
BASELINE_SELECTION_DETERMINISTIC = TRUE
CALLER_ORDER_AFFECTS_BASELINE    = FALSE
```

The lexical tie-break exists only so a tie resolves to exactly one observation
rather than to implementation-defined behaviour.

## 2.5 No eligible baseline (Phase 7)

```text
NO_ELIGIBLE_PRIOR_BASELINE -> INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
```

No silent fallback: no rolling mean, no epoch baseline, no arbitrary first item,
no nearest incompatible observation. `BASELINE_UNAVAILABLE` is a first-class
outcome.

## 2.6 Multiple eligible baselines (Phase 8)

```text
BASELINE RESULT = ONE MeasurementObservation
```

The selector **selects**; it never **aggregates**. `MetricDefinition.aggregation:
AggregationSemantics` (`book6_definitions.py:151`, closed set `NONE | SUM | MEAN
| LAST | DISTRIBUTION` at `:59–67`) already declares how repeated observations of
a window aggregate. An interval-window observation therefore already carries its
aggregated value; the selector chooses among existing observations.

```text
SELECTOR_AGGREGATES = FALSE
```

If a metric declares `aggregation == NONE` **and** multiple observations exist
for one comparison window, aggregation would be required — that is a genuine
new decision and the outcome is **HOLD and surface it**. `PRIOR_COMPARABLE_WINDOW`
must never silently become `ROLLING_MEAN` or any other aggregator.

## 2.7 Fingerprint (Phase 9)

`BaselineSelectorSpec` semantic content is included **inside** the canonical
`ComparisonRule` fingerprint. Minimum fingerprinted content: `selector_kind`,
window compatibility requirements, methodology compatibility requirements,
denominator/cohort requirements where selector-specific, and the deterministic
ordering policy.

```text
FREE TEXT IN SELECTOR   = NOT PERMITTED
ARBITRARY CALLABLE      = NOT PERMITTED
EXPRESSION LANGUAGE     = NOT PERMITTED
eval / exec             = NOT PERMITTED
```

Mutation under the same `ComparisonRule` identity **must** change the rule
fingerprint and invalidate prior authority. The accepted precedent is
`METHODOLOGY_CANONICAL_FIELDS` (`book6_methodology.py:85–97`) feeding
`canonical_methodology_spec()` (`:99`) and `methodology_fingerprint()` (`:132`).

## 2.8 Ratification binding (Phase 10)

```text
SEPARATE_BENCHMARK_AUTHORITY_BINDING   = NONE
COMPARISON_RULE_BINDS_BASELINE_SELECTOR = TRUE
```

The baseline selector spec fingerprint lives inside the `ComparisonRule`'s own
canonical fingerprint and derivation binding. There is no separate benchmark
authority binding and no late-bound baseline policy.

---

# 3. `ChangeObservation` v0.6

The v0.5 field list carries, with two changes:

```text
REMOVED:  baseline_selection_methodology_ref   (phantom)
ADDED:    baseline_selector_spec_fingerprint   (REQUIRED)
          selected_baseline_measurement_ref    (REQUIRED when a baseline
                                                 was resolved; ABSENT when
                                                 change_kind =
                                                 INSUFFICIENT_DATA /
                                                 BASELINE_UNAVAILABLE)
```

`comparability_status` carries v0.5 §3.1's closed
`TemporalComparabilityStatus` domain and §3.2–§3.4 derivations unchanged.

## 3.1 Authority replay (Phase 12)

At use time the engine **re-resolves** baseline selection rather than trusting a
stored result. It verifies the candidate measurements still exist, their Book 2
authority is current, the metric/methodology/unit/window bindings still match,
and the same deterministic selector still selects the recorded baseline refs.

```text
if current resolution differs from the recorded baseline:
    current_authority = FALSE
    historical ChangeObservation is PRESERVED
    NO silent rebaseline
```

## 3.2 Caller authority (Phase 13)

```text
CALLER MAY provide:      candidate baseline refs (for offline resolution)
CALLER MAY NOT provide:  selected_baseline_ref
                         baseline_selector_result
                         baseline_is_valid
                         benchmark_rule_ref
                         benchmark_methodology_ref
```

If an expected baseline ref is accepted for tests, the engine **recomputes and
compares**; a mismatch **raises**, and stored authority uses the **engine**
result.

---

# 4. Separations (carried unchanged)

No change. Descriptive/prescriptive, measurement/valuation, Book 6/Book 7, and
Book 6/Sensor separations stand as ratified.

---

# 5. Authority replay — TWENTY checks (Phase 11)

The ratified 19-check replay's checks 4–6 were inherited from the phantom
benchmark model. v0.6 replaces them honestly with three selector checks:

```text
 1. ComparisonRule identity and version
 2. ComparisonRule operator-ratification binding
 3. ComparisonRule canonical content fingerprint
 4. baseline selector kind/spec validity
 5. deterministic baseline candidate eligibility
 6. deterministic PRIOR_COMPARABLE_WINDOW resolution
 7. delta_operator validity against the closed set and the arithmetic
 8. baseline measurement refs / selection-result integrity
 9. comparison measurement refs
10. input measurement Book 2 current authority
11. input measurement methodology compatibility
12. coverage applicability resolution
13. coverage-sufficiency rule ref (where REQUIRED)
14. coverage-rule ratification and currentness
15. coverage scope match
16. coverage deterministic verdict
17. metric-definition semantic content match
18. compatible input methodology policy match
19. TEMPORAL COMPARABILITY RESOLUTION
20. deterministic comparison/change recomputation
```

```text
REPLAY_CHECK_COUNT = 20
AGGREGATE_ONLY      = REJECTED
```

**The count is 20 because the structure above contains 20 independently
falsifiable authority checks — not for cosmetic continuity.** If implementation
proves more are needed, the count changes.

## 5.1 Check 4 — selector kind/spec validity

Validates that `baseline_selector` is present, typed, closed-domain, and that
`selector_kind` is **executable**. A reserved name is rejected here, before any
resolution work. Ordering policy must equal the single closed enum value.

## 5.2 Check 5 — candidate eligibility

Re-derives eligibility per §2.3 for every candidate and reports which candidates
were excluded and by which structural requirement. `AGGREGATE_ONLY = REJECTED`:
the check names the failing requirement, not merely "not eligible".

Coverage is **not** an eligibility input (§2.3 selection-bias firewall).

## 5.3 Check 6 — deterministic resolution

Applies §2.4 ordering and reports the selected measurement ref, or
`BASELINE_UNAVAILABLE` when no candidate is eligible. Re-running with the same
candidates in a different order must yield the same result; the check asserts
`CALLER_ORDER_AFFECTS_BASELINE = FALSE`.

## 5.4 Check 19 / check 20 separability

Unchanged from v0.5: check 19 can pass while check 20 fails (recomputed delta
disagrees), and check 19 can refuse so check 20 never runs.

---

# 6. `AC-17` — single-meaning absence (carried, restated)

- `coverage_applicability_source_ref` absent means `NO_UPSTREAM_DETERMINATION_EXISTS` **only**.
- `comparability_status = UNRESOLVED` is a decision meaning only "insufficient authoritative basis to decide".
- `selected_baseline_measurement_ref` absent means `BASELINE_UNAVAILABLE` **only**.
- `NOT_APPLICABLE` is never an absence encoding under this grammar.

---

# 7. `AC-18` / `AC-18a` — policy is not authority (carried, restated)

- No rule-author policy parameter may determine numeric equality, finiteness, unit compatibility, coverage applicability, comparability status, or **baseline selection**.
- Policy **P3 `unit_requirements`** remains **WITHDRAWN**.
- `BaselineSelectorSpec` is a derivation target, not a policy: its content is closed and typed, with no free text, callable, or expression.

---

# 8. Inventories

## 8.1 Nullable fields

```text
NULLABLE_FIELDS_RE_INVENTORIED   = 36
AMBIGUOUS_NULLABLE_FIELDS        = 0
```

`selected_baseline_measurement_ref` is nullable with the **single** meaning
`BASELINE_UNAVAILABLE`. It introduces no new ambiguity because absence and
"not yet computed" are the same condition here — the engine never emits a
partial baseline.

## 8.2 Policy parameters

P1, P2, P4–P10 carry unchanged. **P3 withdrawn.** No new policy parameter is
introduced by v0.6.

## 8.3 NEW — baseline selector inventory

```text
BASELINE_SELECTOR_KIND_MEMBERS        = 5
    EXECUTABLE                        = 1  (PRIOR_COMPARABLE_WINDOW)
    RESERVED_NOT_EXECUTABLE           = 4  (ROLLING_MEAN, ROLLING_MEDIAN,
                                           HISTORICAL_DISTRIBUTION,
                                           BASELINE_EPOCH)
BASELINE_SELECTOR_INDEPENDENT_REGISTRY = FALSE
BASELINE_SELECTOR_INDEPENDENT_RATIFICATION = FALSE
BASELINE_SELECTOR_IN_FINGERPRINT       = TRUE
ORDERING_POLICY_MEMBERS               = 1
SELECTOR_AGGREGATES                   = FALSE
SELECTOR_RESULT_KIND                  = ONE MeasurementObservation
RESERVED_SELECTOR_PLACEHOLDER_BEHAVIOUR = NONE
```

## 8.4 StateRule benchmark separation

```text
BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME     = UNRATIFIED / UNIMPLEMENTED
COMPARISON_RULE_BASELINE_SELECTOR_REUSES_STATE_RULE_AUTHORITY = FALSE
```

`StateRule.benchmark_methodology_ref` (`book6_states.py:178`, enforced at
`:214`) remains a **separate** accepted mechanism for Class C
threshold/benchmark states (`StateClass.C_THRESHOLD_BENCHMARK`,
`book6_states.py:72`). This grammar does not repurpose it, does not satisfy it,
and does not claim to solve Class C benchmark semantics.

---

# 9. Ownership boundary (carried unchanged)

No change.

---

# 10. Contract-class audit (v0.6)

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

| item | why not a new public contract class |
|---|---|
| finite stored binary64 semantics | definition over existing `float` storage |
| same-metric unit identity law | derivation over two existing string fields |
| coverage applicability resolver | uses the existing `CoverageRuleRegistry` |
| `TemporalComparabilityStatus` | closed 3-member enum; a field, no registry |
| `BaselineSelectorSpec` | nested value object; no registry, no ledger, no independent lifecycle; cannot exist authoritatively outside a `ComparisonRule` |
| 20-check replay | a check count |

```text
GAP_5A / 5B / 5C / 5D = NOT SELECTED
GAP_5 = 5E in this grammar (draft, not ratified)
```

---
# 11. Status

```text
STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE

CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.4.md REMAINS RATIFIED AND UNCHANGED.
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.5.md REMAINS AN UNRATIFIED DRAFT.
```

**Not authorized and not performed:** any implementation, source or test change,
any `BenchmarkRule` or `BenchmarkRuleRegistry`, any benchmark-rule ratification,
any rolling mean / rolling median / historical distribution / baseline epoch
implementation, any `observed_at` baseline ordering, any random or caller-order
selection, any caller-selected authoritative baseline, Book 7 or Book 8 work,
live acquisition, and any branch creation, force-push, rebase or history rewrite.
