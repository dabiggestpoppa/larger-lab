# CSIA — BOOK 6 COMPARISON / CHANGE IMPLEMENTATION-SUBSTRATE CLARIFICATION — v0.1

**Document ID:** CSIA-B6-ISC-001
**Version:** 0.1
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Kind:** GOVERNANCE SUCCESSOR / ADDENDUM
**Relationship:** successor to, and additive clarification of, the ratified
`CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md` (anchor
`28bfac52c23c891ebb54e9924dedc925a859b359`, ratified in `8557f4df82a67434951b2f9682142a59125f5153`).

**Ratified history is NOT rewritten by this artifact.** The ratified v0.4 plan,
grammar v0.4, boundary v0.3, seam v0.4, ratification readiness v0.3 and
ratification record v0.1 all remain in force exactly as ratified. This document
adds substrate precision that the v0.4 authorization review found to be
under-specified. It calls no ratified artifact erroneous or unratified.

**This artifact grants no implementation authority.**

---

# 0. Why this artifact exists

`CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md`
returned HOLD on four gaps. A separate phantom-citation sweep
(`CSIA_RATIFIED_PLAN_PHANTOM_CITATION_SWEEP_v0.1.md`, commit `f76cf9b95`) opened
a fifth, **GAP-5**, which this artifact does **not** resolve. See §8.

The four gaps below are resolved here at the operator's direction. Each
resolution names an already-accepted runtime primitive or introduces no new
authority-bearing contract class.

---

# 1. GAP-1 — canonical numeric representation

## 1.1 Resolution

```text
GAP_1_RESOLUTION = 1A-STRICT
```

Keep existing binary64 float storage. Correct the doctrine precisely.

## 1.2 Canonical value definition

For this amendment, the canonical numeric value is:

```text
CANONICAL_VALUE = FINITE_STORED_BINARY64

defined as: the finite IEEE-754 binary64 value held by
            MeasurementObservation.value
```

It does **not** mean the exact mathematical real number prior to representation.
The distinction is explicit and is not a hedge — it is the definition.

```text
REAL_NUMBER_EXACTNESS_CLAIM     = FALSE
STORED_VALUE_EXACTNESS_CLAIM    = TRUE
```

## 1.3 Canonical equality definition

```text
CANONICAL_EQUALITY = EXACT_EQUALITY_OF_STORED_CANONICAL_BINARY64
```

Two canonical values are canonically equal iff their stored binary64 values are
bitwise-equal under `==` on finite doubles. Nothing else.

```text
EPSILON                   = NOT USED, NOT PERMITTED
math.isclose              = NOT USED, NOT PERMITTED
APPROXIMATE_EQUALITY      = NOT PERMITTED
DISPLAY_ROUNDING_IN_EQUALITY = NOT PERMITTED
Decimal migration         = NOT PERMITTED
Fraction migration        = NOT PERMITTED
MeasurementObservation.value public type change = NOT PERMITTED
```

`MeasurementObservation.value: float | None` at `book6_records.py:113` is
**unchanged**. This resolution is a doctrine-precision fix, not a type change.

## 1.4 Wording repair (Phase 3)

The ratified grammar's overbroad phrasing is replaced **in the successor
grammar v0.5 only**. The ratified v0.4 text is preserved as written.

| v0.4 phrase | v0.5 replacement |
|---|---|
| "exact canonical equality" | "exact equality of the finite stored canonical binary64 values before any presentation/display transformation" |
| "canonical unrounded value" | "finite stored canonical binary64 value prior to display rounding" |

## 1.5 Worked consequence

`0.1 + 0.2` is not a legal construction in this engine — the engine never sums
literals. It compares two **stored** values. Comparing a stored `0.3` against a
stored `0.3` is canonically equal (`NO_CHANGE`). Comparing a stored
`0.1 + 0.2` result (`0.30000000000000004`) against a stored `0.3` is
**canonically unequal**, because the stored binary64 values differ. This is
correct under this amendment, not a defect: the comparison is over stored
values, and real-number idealisation is explicitly disclaimed.

---

# 2. PHASE 1 — finite numeric domain

## 2.1 Requirement

```text
FINITE_NUMERIC_INPUT_REQUIRED = TRUE
```

`NaN`, `+Inf` and `-Inf` **cannot participate** in comparison arithmetic.

## 2.2 Non-finite outcome

A non-finite measurement input yields:

```text
INSUFFICIENT_DATA
```

(or another already-ratified fail-closed availability outcome). It **never**
yields:

```text
INCREASE
DECREASE
NO_CHANGE
absolute_delta
relative_delta
```

## 2.3 The Book 6 NaN sentinel is not inherited

`book6_core.py:181` injects `float("nan")` as an undefined-ratio denominator
sentinel inside `RatioResult`. **The new comparison/change engine must not
inherit this sentinel.** That mechanism is a Book 6 core ratio convenience with
different semantics; importing it would make NaN a *representable value* in the
comparison path and would defeat §2.1.

Non-finiteness is **rejected at the boundary**, before arithmetic, as a
validated-input condition — not carried as a sentinel value.

## 2.4 Enforcement point

Validation precedes delta computation:

```text
non_finite(baseline.value)    -> INSUFFICIENT_DATA
non_finite(comparison.value)  -> INSUFFICIENT_DATA
```

Non-finite is detected by `math.isfinite()`, which is exact for binary64 and is
not an approximate predicate.

---

# 3. PHASE 2 — zero semantics

## 3.1 Canonical zero

For stored binary64:

```text
CANONICAL_ZERO = (value == 0.0)
```

Both `+0.0` and `-0.0` satisfy this predicate. Under IEEE-754, `+0.0 == -0.0`
is `True`.

## 3.2 Required behaviour

```text
+0.0 and -0.0 are canonical zero for this amendment
```

| use | signed-zero result |
|---|---|
| absolute equality of `+0.0` and `-0.0` | `NO_CHANGE` where appropriate — they are canonically equal and canonically zero |
| relative denominator when baseline is `+0.0` or `-0.0` | zero-baseline fail-closed — `relative_delta = UNDEFINED` |
| `direction_derivation` from an absolute delta of `+0.0` | `NO_CHANGE` (delta is zero) |

## 3.3 Prohibited

```text
SIGNED_ZERO_SEMANTIC_DISTINCTION = NOT CREATED
```

No positive-zero / negative-zero distinction is introduced anywhere: not in the
delta, not in direction, not in `change_kind`, not in any fingerprint.

This is deliberate and is stated so a later reader does not "fix" it as an
oversight. The rationale is that IEEE-754 signed zero carries sign-of-underflow
metadata that is **not** a measurement fact. Treating it as one would import a
representation artifact into a descriptive comparison, which the Constitution's
descriptive/prescriptive firewall (§5.3a) forbids.

---

# 4. GAP-2 — unit arithmetic source of truth

## 4.1 Resolution

```text
GAP_2_RESOLUTION = 2D  SAME_METRIC_EXACT_UNIT_IDENTITY
```

Options 2A, 2B and 2C are **not** selected.

**Rationale.** A `ComparisonRule` is a **single-metric temporal comparison**. It
compares one metric to itself across two time points. It is not a cross-unit
arithmetic engine, and no general dimensional-unit contract is required for it.

## 4.2 The narrower law (Phase 4)

A temporal comparison may perform arithmetic **only** when all of the following
hold:

```text
 1. baseline observation resolves to the bound metric_definition_ref
 2. comparison observation resolves to the SAME metric_definition_ref
 3. baseline observation.unit   == MetricDefinition.unit
 4. comparison observation.unit == MetricDefinition.unit
 5. therefore baseline observation.unit == comparison observation.unit
```

```text
TEMPORAL_UNIT_COMPATIBILITY = EXACT SAME-METRIC UNIT IDENTITY
```

## 4.3 Substrate already accepted

Conditions 3 and 4 require no new field. `MetricDefinition.unit` exists and is
**non-nullable** at `book6_definitions.py:148`:

```python
unit: str = Field(min_length=1)
```

and `MeasurementObservation.unit: str | None` exists at
`book6_records.py:114`. The comparison is a plain exact string equality between
an already-accepted model field and an already-accepted model field. This is
the same shape as the existing `unit_requirements` string check, and it is
**testable** — unlike the ratified P3's untestable "accepted unit contract"
citation.

## 4.4 Prohibited under 2D

```text
UNIT_CONVERSION                = NOT PERMITTED
UNIT_ALIASES                   = NOT PERMITTED
DIMENSIONAL_INFERENCE           = NOT PERMITTED
"USD" -> "cents"               = NOT PERMITTED
TOKEN_CONVERSION                = NOT PERMITTED
UNIT_NORMALIZATION             = NOT PERMITTED
GENERAL_UNIT_TAXONOMY          = OUT OF SCOPE
UNIT_SCALING                   = OUT OF SCOPE
CONVERTIBILITY                  = OUT OF SCOPE
DIMENSIONAL_EQUIVALENCE         = OUT OF SCOPE
```

## 4.5 Arithmetic under exact same-unit identity (Phase 5)

Given §4.2 holds:

```text
ABSOLUTE_DELTA = comparison_value - baseline_value
```

has the same unit as the metric. No dimensional reasoning is needed, because both
operands are already the metric's own unit.

```text
RELATIVE_DELTA = (comparison_value - baseline_value) / baseline_value
```

is **dimensionless** where `baseline_value != canonical zero`.

This amendment does **not** decide general convertibility, dimensional
equivalence, unit taxonomy or unit scaling. Those remain out of scope.

## 4.6 Unit failure (Phase 6)

Any of:

```text
observation metric ref differs from the bound metric_definition_ref
OR
observation unit differs from MetricDefinition.unit
```

must produce:

```text
comparability_status = NOT_COMPARABLE
```

**not** a conversion attempt, and not a repair.

## 4.7 Contract count

```text
UNIT_CONTRACT_CLASS_ADDED                   = FALSE
NEW_AUTHORITY_BEARING_CONTRACT_CLASS_FOR_UNITS = FALSE
HIDDEN_THIRD_CONTRACT                       = NONE
```

2D closes GAP-2 by **removing** the phantom citation rather than satisfying it.
The ratified grammar's P3 ("cites the accepted unit contract") and §1.4 (unit
divisibility derived from an accepted contract) are superseded in grammar v0.5
by §4.2's same-metric identity law, which is fully determined by already-accepted
fields.

This also resolves, by the same act, the strengthened GAP-2 finding recorded in
the phantom-citation sweep §5: the nearest candidate unit substrate
(`CSIA_BOOK_5_UNIT_DOMAIN_VALUATION_SEAM_DOCTRINE_v0.1.md`) self-declares NOT
RATIFIED and defines no dimensional algebra. 2D requires none.

---

# 5. GAP-3 — coverage applicability

## 5.1 Resolution

```text
GAP_3_RESOLUTION = 3C  COVERAGE-RULE-PRESENCE DERIVATION
```

Purely vacuous 3A is **not** selected. Semantic heuristics under 3B are **not**
selected and **must not** be invented.

## 5.2 The derivation law (Phase 7)

Use the **already-accepted** `CoverageRuleRegistry` and its operator-ratification
authority. No new registry, no new authority class.

```text
IF a CURRENT, RATIFIED, EXACT-METRIC-SCOPED CoverageSufficiencyRule
   exists for the bound metric:

    coverage_requirement_status      = REQUIRED
    coverage_applicability_source_ref = that exact coverage rule
                                         authority/binding

ELSE:

    coverage_requirement_status      = UNRESOLVED
    coverage_applicability_source_ref = ABSENT
                                      (single ratified meaning:
                                       NO_UPSTREAM_DETERMINATION_EXISTS)
```

## 5.3 Why this is not a heuristic

3B was rejected because deriving applicability from prose (a `denominator_rule`
string, a `required_evidence_semantics` string, a similarity match) is
unfalsifiable and is the "matching = prohibited heuristic" failure the review
named. 3C is not that:

| | 3B (rejected) | 3C (selected) |
|---|---|---|
| input | free-text strings | an **exact-metric-id equality** against a registry |
| source of truth | an author's description | `CoverageRuleRegistry` + `RatificationLedger` |
| falsifiable | no | yes — every branch is an exact lookup |
| heuristic | yes (semantic match) | no (identity match) |
| new authority class | would require one | **none** |

`coverage_applicability_source_ref` is derived by exact identifier equality, not
by interpreting meaning. The ratified §8.1 single-meaning rule still holds:
absent means `NO_UPSTREAM_DETERMINATION_EXISTS` **only**.

## 5.4 Accepted substrate used

`CoverageRuleRegistry` (`book6_coverage_rules.py:112`) already provides every
primitive 3C needs:

```text
rules_for_metric(metric_id)   -> registered rules scoped to that metric,
                                id-ordered
ratification_of(rule_ref)     -> live RatificationRecord or None
authorize(metric_id, rule_ref)-> currently-ratified + in-scope, or REFUSES
```

`authorize()` already enforces the three conditions 3C needs, and its docstring
already states the governing property:

```text
the rule must exist, must carry a registry ratification decision for its
CURRENT version, and must scope to the metric being judged. A scope mismatch
is a refusal, not a silent pass.
```

Scope mismatch, missing ratification and missing registration are all **refusals**
— which map to `UNRESOLVED`, never to `NOT_APPLICABLE` and never to `REQUIRED`.

## 5.5 `NOT_APPLICABLE` remains closed (Phase 8)

```text
NOT_APPLICABLE derived from ABSENCE of a rule = FORBIDDEN
Absence means UNRESOLVED only.
CAN_DERIVE_NOT_APPLICABLE = FALSE
```

`NOT_APPLICABLE` may be emitted **only** if some future, separately ratified
doctrine provides an explicit authoritative determination. For this amendment's
runtime it is unreachable, and this is intentional.

## 5.6 Canonical zero-rule consequence (Phase 9)

```text
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0   (canonical production state)
```

Therefore, in canonical production, **every** comparison resolves to:

```text
coverage_requirement_status      = UNRESOLVED
coverage_applicability_source_ref = ABSENT
```

Canonical comparison remains **fail-closed** until a coverage rule is separately
ratified. This is the correct and intended state. It is not a defect to be
worked around.

## 5.7 Synthetic positive path

Implementation tests may use **synthetic, non-canonical, operator-ratified
fixture rules**.

```text
CANONICAL_RULE_COUNT         = 0
SYNTHETIC_TEST_RULES_ALLOWED = TRUE
SYNTHETIC_RULES_ARE_CANONICAL = FALSE
```

This gives a real, executed positive path (`REQUIRED` + `SUFFICIENT`) without
silently creating a canonical rule. The accepted codebase already anticipates
this: `COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP: Final[int] = 0` at
`book6_coverage_rules.py`, whose comment records that `DATA_COMPLETE` is
"unreachable without a synthetic local fixture."

Synthetic rules must be distinguishable from canonical ones in test output, so a
passing synthetic test can never be mistaken for evidence that a canonical rule
exists.

---

# 6. GAP-4 — temporal comparability

## 6.1 Resolution

```text
GAP_4_RESOLUTION = 4D  EXPLICIT TEMPORAL COMPARABILITY DOMAIN
```

The existing cross-metric `FALSE_COMPARISON_CORPUS` is **not** reused.
`ComparabilityClass` is **not** reused.

## 6.2 Why the corpus cannot be reused (Phase 16)

```text
FALSE_COMPARISON_CORPUS = UNCHANGED
book6_comparability.py  = UNCHANGED
```

The accepted corpus is **cross-metric-pair scoped** (15 rows, FC-01..FC-15,
`CorpusVerdict = NOT_COMPARABLE | CONDITIONAL | AS_DISTINCT`). A
`ComparisonRule` is **single-metric temporal**. The scopes do not overlap, and
`corpus_row_for` already raises on ungoverned pairs. Reinterpreting `CorpusVerdict`
for temporal comparison would mutate an accepted artifact's meaning — the exact
prohibited move.

Temporal comparability does **not**: insert self-pair rows, invent corpus rows,
reinterpret `CorpusVerdict`, or mutate `authorize_comparison()`.

## 6.3 The new closed enum (Phase 10)

```text
TemporalComparabilityStatus:

    COMPARABLE
    NOT_COMPARABLE
    UNRESOLVED
```

This is **NOT** `CorpusVerdict`, **NOT** `ComparabilityClass`, **NOT**
`StateName`, **NOT** `ClaimState`. It applies **only** to the single-metric
temporal comparison/change engine.

It is a closed enum with three members. It is a field of the comparison/change
engine, not a new public authority-bearing contract class (see §7).

## 6.4 `COMPARABLE` derivation (Phase 11)

`COMPARABLE` requires **all applicable structural gates to pass**:

```text
 1. same metric-definition semantic binding
 2. same-metric exact-unit identity              (GAP-2 / §4.2)
 3. input methodology compatibility
 4. denominator compatibility
 5. cohort compatibility where applicable
 6. window compatibility
 7. missingness requirements
 8. coverage applicability resolved
 9. and where coverage is REQUIRED:
      - coverage rule current / ratified
      - coverage scope matches
      - coverage verdict = SUFFICIENT
10. all required source observations available
```

Every gate is falsifiable by at least one named negative test.

## 6.5 `NOT_COMPARABLE` derivation (Phase 12)

`NOT_COMPARABLE` means an **explicit structural compatibility requirement
FAILED**:

```text
 - wrong metric binding
 - unit mismatch
 - methodology not permitted
 - denominator mismatch
 - cohort mismatch
 - window incompatibility
 - coverage REQUIRED + verdict INSUFFICIENT
 - coverage rule scope mismatch
```

```text
NOT_COMPARABLE != INSUFFICIENT_DATA
NOT_COMPARABLE != UNRESOLVED_AUTHORITY
```

A structural failure is a **decision**. Absence of basis is not a failure.

## 6.6 `UNRESOLVED` derivation (Phase 13)

`UNRESOLVED` means the engine **lacks sufficient authoritative basis to decide**
comparability:

```text
 - coverage applicability UNRESOLVED      (canonical state under 3C)
 - required upstream authority unavailable
 - required observation unavailable, where that absence does not itself
   establish structural incompatibility
```

```text
TemporalComparabilityStatus.UNRESOLVED
    -> change_kind = INSUFFICIENT_DATA
    OR no authoritative ChangeObservation output,
       according to the existing record-creation contract
```

**`UNRESOLVED` is never mapped to `NOT_COMPARABLE`.** This is the single most
important invariant in §6, and it is the direct answer to the ratified grammar
v0.4 GAP-4 defect, where `NOT_COMPARABLE` was a `change_kind` member that no
check could produce.

Under 3C + 4D, with `COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0`, **every canonical
comparison resolves to `UNRESOLVED` -> `INSUFFICIENT_DATA`.** That is the
honest fail-closed outcome, and it is what makes the amendment safe to ship.

## 6.7 `change_kind` mapping (Phase 14)

Required deterministic mapping:

```text
comparability_status = NOT_COMPARABLE
    -> change_kind = NOT_COMPARABLE

comparability_status = UNRESOLVED
    -> change_kind = INSUFFICIENT_DATA
       (or fail before authoritative change emission)

comparability_status = COMPARABLE
    -> the arithmetic stage may derive:
         INCREASE
         DECREASE
         NO_CHANGE
         CHANGE_UNDEFINED
       depending on the selected delta operator and the zero-baseline law
```

`NOT_COMPARABLE` now has a **producing check** (new replay check 19). The
ratified v0.4 defect — a `change_kind` member with no producer — is closed.

---

# 7. PHASE 15 — replay becomes twenty checks

## 7.1 The ratified gap

The ratified v0.4 replay has **19 checks** and contains **no producing
comparability check**. Checks 12–16 concern coverage and checks 17–18 concern
metric/methodology matching, but nothing resolves temporal comparability as a
single decidable outcome. This is not to be pretended covered.

## 7.2 New numbering

```text
REPLAY_CHECK_COUNT = 20
AGGREGATE_ONLY      = REJECTED
```

```text
 1-18  unchanged from v0.4
19     TEMPORAL COMPARABILITY RESOLUTION
       -> derives TemporalComparabilityStatus deterministically
20     DETERMINISTIC COMPARISON / CHANGE RECOMPUTATION
       -> recomputes delta, direction, change_kind from stored canonical
          binary64 values (was check 19 in v0.4)
```

Check 19 is inserted **immediately before** deterministic recomputation, because
comparability is a precondition of arithmetic: recomputation must not run on an
unresolved or refused comparison.

Each of the 20 checks is **independently falsifiable** — each has at least one
named negative test that makes it fail while the other 19 are unaffected.

## 7.3 Why not aggregate

`AGGREGATE_ONLY = REJECTED`. A single "comparability OK" boolean that cannot be
localised to a failing gate is exactly the untestable surface the review rejected
in the ratified 19-check replay. Check 19 emits the **status and the specific
failed gate**, so a failure names its cause.

---

# 8. PHASE 16 — cross-metric corpus impact

```text
FALSE_COMPARISON_CORPUS = UNCHANGED
book6_comparability.py  = UNCHANGED
CorpusVerdict           = UNCHANGED
authorize_comparison()  = UNCHANGED
ComparabilityClass      = UNCHANGED
FC-01 .. FC-15          = UNCHANGED
```

The accepted cross-metric comparability corpus retains its existing purpose
entirely. This amendment adds a **parallel, separately-scoped** temporal
mechanism and touches none of it.

---

# 9. PHASE 17 — contract count audit

After all four resolutions:

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

These are **NOT** new public contract classes:

| item | why not |
|---|---|
| stored-binary64 numeric clarification | a definition of existing `float` storage; no new type, no field, no registry |
| same-metric unit identity law | a derivation rule over two already-accepted string fields |
| coverage applicability resolver | uses the **existing** `CoverageRuleRegistry`; adds no registry |
| `TemporalComparabilityStatus` enum | a closed 3-member enum; a field of the engine, not an authority-bearing record with its own registry and ratification |
| 20-check replay | a check-count change; adds no contract |

If the implemented result is not exactly 2 with no hidden third, the outcome is
**HOLD**.

---

# 10. GAP-5 is NOT resolved here — scope boundary

The phantom-citation sweep (`f76cf9b95`) opened a **fifth** gap. This artifact
does **not** resolve it, and it must not be read as having done so.

```text
GAP_5 = ACCEPTED BENCHMARK-RULE NAMESPACE   = STILL OPEN
```

Grammar v0.4 §2 line 246 requires a non-null `baseline_selection_methodology_ref`
citing an ACCEPTED, individually operator-ratified benchmark rule from the closed
domain `PRIOR_COMPARABLE_WINDOW | ROLLING_MEAN | ROLLING_MEDIAN |
HISTORICAL_DISTRIBUTION | BASELINE_EPOCH`. Zero `Benchmark*` symbols exist
across all 62 runtime modules; `BENCHMARK_RULES_RATIFIED = 0`; and the field has
no defined absent state.

**Why it is out of scope for this artifact.** The operator's direction for this
session named four gaps (GAP-1..GAP-4) and gave resolutions for each. GAP-5 was
opened after that direction was formed and no resolution was given for it.
Choosing one here would be the operator's decision, not this artifact's.

**What this means for the authorization review.** Because the four resolutions
below make canonical comparison resolve `UNRESOLVED -> INSUFFICIENT_DATA` (§6.6),
GAP-5 does not block the *clarification* — but it does remain an open item that
must be decided before implementation authorization is granted. This is recorded
in the authorization review v0.2 rather than being quietly absorbed.

---

# 11. Resolution summary

```text
GAP_1_RESOLUTION = 1A-STRICT
                   keep binary64 storage; correct doctrine wording
GAP_2_RESOLUTION = 2D  SAME_METRIC_EXACT_UNIT_IDENTITY
                   no dimensional ontology; no conversion
GAP_3_RESOLUTION = 3C  COVERAGE-RULE-PRESENCE_DERIVATION
                   existing registry; absence => UNRESOLVED
GAP_4_RESOLUTION = 4D  EXPLICIT_TEMPORAL_COMPARABILITY
                   TemporalComparabilityStatus; corpus untouched
```

```text
FINITE_NUMERIC_INPUT_REQUIRED       = TRUE
NON_FINITE_OUTCOME                  = INSUFFICIENT_DATA
BOOK6_NAN_SENTINEL_INHERITED        = FALSE
CANONICAL_ZERO                      = (value == 0.0)   [+0.0 == -0.0]
SIGNED_ZERO_SEMANTIC_DISTINCTION    = NOT CREATED
TEMPORAL_UNIT_COMPATIBILITY         = EXACT SAME-METRIC UNIT IDENTITY
UNIT_CONVERSION                     = NOT PERMITTED
CAN_DERIVE_NOT_APPLICABLE           = FALSE
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0  (canonical)
SYNTHETIC_TEST_RULES_ALLOWED        = TRUE
SYNTHETIC_RULES_ARE_CANONICAL       = FALSE
UNRESOLVED_MAPPED_TO_NOT_COMPARABLE = FORBIDDEN
REPLAY_CHECK_COUNT                  = 20
FALSE_COMPARISON_CORPUS             = UNCHANGED
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT               = NONE

GAP_5 = STILL OPEN (not resolved by this artifact)
```

---

# 12. Status

```text
STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE

Ratifying this artifact does NOT authorize implementation. It authorizes the
creation of successor grammar v0.5 and plan v0.5, after which the
implementation authorization review v0.2 must pass, after which a separate
operator decision is required.
```

**Not authorized and not performed by this artifact:** any implementation, any
source or test change, any float/Decimal/Fraction migration, any epsilon or
isclose, any unit ontology or conversion, any cross-metric corpus mutation, any
coverage applicability heuristic, any `NOT_APPLICABLE` by absence, any new
canonical coverage rule, any rule ratification, any Book 7 or Book 8 work, any
live acquisition, and any branch creation, force-push, rebase or history rewrite.
