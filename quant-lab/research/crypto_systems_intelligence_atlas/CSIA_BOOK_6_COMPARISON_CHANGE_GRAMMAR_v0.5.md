# CSIA — BOOK 6 COMPARISON / CHANGE GRAMMAR — v0.5

**Document ID:** CSIA-B6-CG-005
**Version:** 0.5
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Supersedes:** nothing. `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.4.md` is
**PRESERVED IN FULL AND REMAINS RATIFIED**. This document is its additive
successor, differing only where the four gap resolutions require.
**Authority under:** `D7N-7 = A`; boundary v0.3; substrate clarification v0.1
(this document's basis, itself `DRAFT_PENDING_OPERATOR_RATIFICATION`).

**Ratified history is not rewritten.** Every v0.4 section not listed in §0.2
below stands verbatim. This document adds, tightens or corrects; it does not
delete ratified law and does not call any ratified artifact erroneous.

**This document grants no implementation authority.**

---

# 0. Delta from v0.4

## 0.1 What this version changes

| § | change | driver |
|---|---|---|
| §1.0 | **NEW** — finite stored binary64 semantics, non-finite rejection, canonical zero | GAP-1 `1A-STRICT` |
| §1.4 | **REPLACED** — unit divisibility no longer derived from an "accepted contract"; becomes same-metric exact-unit identity | GAP-2 `2D` |
| §2 | **AMENDED** — `baseline_selection_methodology_ref` semantics clarified; GAP-5 left open, not silently resolved | scope honesty |
| §3 | **AMENDED** — `comparability_status` gains its closed domain and producer | GAP-4 `4D` |
| §5 | **AMENDED** — 19 checks become 20; new check 19 = temporal comparability resolution | GAP-4 `4D`, Phase 15 |
| §8.3 | **NEW** — temporal comparability enum inventory | GAP-4 `4D` |

## 0.2 What this version does NOT change

Everything else in v0.4 stands verbatim: the §0 repair delta, §1.1 delta
operator vocabulary, §1.2 direction law, §1.3 zero-baseline law, §1.5 rounding
firewall, §1.6 tolerance/materiality firewall, §2.1 prohibited fields, §2.2
registry governance, §3.1 `coverage_observation_state`, §3.2 invariants, §4
separations, §6 `AC-17`, §7 `AC-18`/`AC-18a`, §8.1 nullable inventory,
§8.2 policy inventory, §9 ownership boundary.

**No unrelated redesign.** In particular the §2 `ComparisonRule` field list, the
§3 `ChangeObservation` field list, and the §5.1–§5.18 checks are carried
unchanged apart from the three amendments above.

## 0.3 Repaired doctrine wording

Two v0.4 phrases overstate what binary64 storage can support. They are corrected
**here**, prospectively, and the v0.4 text is left as written.

| v0.4 phrase | v0.5 canonical phrase |
|---|---|
| "exact canonical equality" | "exact equality of the finite stored canonical binary64 values before any presentation/display transformation" |
| "canonical UNROUNDED absolute_delta" / "canonical unrounded values" | "finite stored canonical binary64 value prior to display rounding" |

```text
REAL_NUMBER_EXACTNESS_CLAIM  = FALSE
STORED_VALUE_EXACTNESS_CLAIM = TRUE
```

---

# 1. Canonical law (v0.4 §1, with §1.0 added and §1.4 replaced)

## 1.0 NEW — finite stored binary64 semantics

### 1.0.1 Canonical value

```text
CANONICAL_VALUE = FINITE_STORED_BINARY64

the finite IEEE-754 binary64 value held by MeasurementObservation.value
(book6_records.py:113, type float | None — UNCHANGED)
```

A canonical value is **not** the exact mathematical real number prior to
representation. No claim of real-number exactness is made anywhere in this
grammar.

### 1.0.2 Canonical equality

```text
CANONICAL_EQUALITY = EXACT_EQUALITY_OF_STORED_CANONICAL_BINARY64
```

Two canonical values are canonically equal iff their stored binary64 values are
equal under `==`, both finite. Nothing else qualifies.

```text
EPSILON / TOLERANCE / math.isclose / APPROXIMATE_EQUALITY
    = NOT PERMITTED in any equality, direction, or change determination
DISPLAY_ROUNDING in any derivation = NOT PERMITTED
Decimal / Fraction migration       = NOT PERMITTED
```

### 1.0.3 Finite numeric domain

```text
FINITE_NUMERIC_INPUT_REQUIRED = TRUE
```

`NaN`, `+Inf`, `-Inf` **cannot participate** in comparison arithmetic.

```text
non_finite(baseline.value)    -> INSUFFICIENT_DATA
non_finite(comparison.value)  -> INSUFFICIENT_DATA
```

A non-finite input never yields `INCREASE`, `DECREASE`, `NO_CHANGE`,
`absolute_delta` or `relative_delta`.

The Book 6 core ratio NaN sentinel (`book6_core.py:181`, inside `RatioResult`)
is **NOT inherited**. That sentinel is a ratio-convenience mechanism with
different semantics; carrying it into comparison would make NaN a representable
value and defeat this clause. Non-finiteness is rejected at the validated-input
boundary via `math.isfinite()`, which is exact for binary64 and is not an
approximate predicate.

### 1.0.4 Canonical zero

```text
CANONICAL_ZERO = (value == 0.0)
```

Both `+0.0` and `-0.0` are canonical zero.

| use | result |
|---|---|
| `+0.0` vs `-0.0` absolute equality | `NO_CHANGE` — canonically equal, canonically zero |
| relative denominator is `+0.0` or `-0.0` | zero-baseline fail-closed — `relative_delta = UNDEFINED` |
| absolute delta is `+0.0` | direction `NO_CHANGE` |

```text
SIGNED_ZERO_SEMANTIC_DISTINCTION = NOT CREATED
```

No positive/negative zero distinction is introduced in any delta, direction,
`change_kind`, or fingerprint. Rationale: IEEE-754 signed zero encodes a
sign-of-underflow representation artifact, not a measurement fact; admitting it
would import a representation artifact into a descriptive comparison.

### 1.0.5 Worked consequence

The engine compares two **stored** values; it never sums literals. A stored
`0.30000000000000004` (the result of `0.1 + 0.2`) is **canonically unequal** to a
stored `0.3`. That is correct under this grammar, not a defect.

### 1.4 REPLACED — same-metric exact-unit identity

**v0.4 §1.4 stated** that `unit_divisibility_policy` is "REMOVED, derived from
the accepted typed unit contract". **That derivation is withdrawn.** No accepted
typed unit contract exists, and the v0.4 authorization review established that
the citation was unverifiable and made POL-11 untestable.

**v0.5 law.** A temporal comparison may perform arithmetic **only** when:

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

Conditions 3 and 4 compare two already-accepted fields exactly:
`MetricDefinition.unit` (non-nullable, `book6_definitions.py:148`) and
`MeasurementObservation.unit` (`book6_records.py:114`). Exact string equality is
the whole rule — it is fully specified and fully testable.

Under §1.4 conditions:

```text
ABSOLUTE_DELTA = comparison_value - baseline_value
    -> same unit as the metric (both operands already that unit)

RELATIVE_DELTA = (comparison_value - baseline_value) / baseline_value
    -> dimensionless where baseline_value != CANONICAL_ZERO
```

No dimensional reasoning is required, because both operands are already the
metric's own unit.

```text
UNIT_CONVERSION / UNIT_ALIASES / DIMENSIONAL_INFERENCE / UNIT_NORMALIZATION
    = NOT PERMITTED
CONVERTIBILITY / DIMENSIONAL_EQUIVALENCE / UNIT_TAXONOMY / UNIT_SCALING
    = OUT OF SCOPE for this amendment
```

Any condition above that fails yields `comparability_status = NOT_COMPARABLE`
(§3, §5 check 19). Never a conversion, never a repair.

```text
UNIT_CONTRACT_CLASS_ADDED                     = FALSE
NEW_AUTHORITY_BEARING_CONTRACT_CLASS_FOR_UNITS = FALSE
HIDDEN_THIRD_CONTRACT                         = NONE
```

---

# 2. `ComparisonRule` (v0.4 §2 carried, with one amendment)

The v0.4 §2 field list is carried verbatim except as noted in §2.1 below. The
authority-bearing content is unchanged: this document introduces **no new
field** to `ComparisonRule`.

## 2.1 AMENDED — coverage applicability derivation

`ComparisonRule.coverage_applicability_source_ref` is **DERIVED**, never
authored:

```text
IF a CURRENT, RATIFIED, EXACT-METRIC-SCOPED CoverageSufficiencyRule exists
   for the bound metric:

    coverage_requirement_status       = REQUIRED
    coverage_applicability_source_ref = that exact rule's authority/binding

ELSE:

    coverage_requirement_status       = UNRESOLVED
    coverage_applicability_source_ref = ABSENT
        (single ratified meaning: NO_UPSTREAM_DETERMINATION_EXISTS)
```

The derivation reads the **already-accepted** `CoverageRuleRegistry`
(`book6_coverage_rules.py:112`) through `rules_for_metric()`,
`ratification_of()` and `authorize()`. `authorize()` already refuses on missing
registration, missing current ratification, and scope mismatch. Every refusal
maps to `UNRESOLVED`.

The derivation is an **exact identifier equality** against a registry. It is not
a semantic match, and no free-text (`denominator_rule`,
`required_evidence_semantics`) is interpreted.

```text
NOT_APPLICABLE derived from ABSENCE of a rule = FORBIDDEN
CAN_DERIVE_NOT_APPLICABLE = FALSE
```

Absence means `UNRESOLVED` only. `NOT_APPLICABLE` requires a future, separately
ratified doctrine that provides an explicit authoritative determination. It is
unreachable in this amendment's runtime, intentionally.

Canonical production has `COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0`, so **every**
canonical comparison resolves to `UNRESOLVED` and is fail-closed. Synthetic,
non-canonical operator-ratified fixture rules MAY be used in tests
(`SYNTHETIC_TEST_RULES_ALLOWED = TRUE`, `SYNTHETIC_RULES_ARE_CANONICAL = FALSE`)
to exercise the `REQUIRED` + `SUFFICIENT` path without creating a canonical rule.

## 2.2 OPEN — `baseline_selection_methodology_ref` (GAP-5 NOT resolved)

v0.4 §2 requires `baseline_selection_methodology_ref` to be a REQUIRED ref to an
ACCEPTED, individually operator-ratified benchmark rule. The phantom-citation
sweep established that no benchmark-rule namespace exists in the codebase.

**This grammar does not resolve GAP-5 and does not pretend to.** The v0.4
requirement stands as ratified until the operator decides. Implementation must
not treat this field as satisfiable, and must not invent a substitute.

```text
GAP_5 = OPEN. Decided by a separate operator decision before implementation
        authorization. See substrate clarification v0.1 §10.
```

---

# 3. `ChangeObservation` (v0.4 §3 carried, with comparability amended)

The v0.4 §3 field list is carried verbatim except `comparability_status`, which
gains its closed domain and producer.

## 3.1 AMENDED — `comparability_status` closed domain

v0.4 listed `comparability_status` as REQUIRED **with no value domain and no
producing check**. That was the GAP-4 defect: `change_kind = NOT_COMPARABLE`
existed but no check could produce it.

v0.5 defines the field's domain explicitly:

```text
comparability_status:  TemporalComparabilityStatus
                       COMPARABLE | NOT_COMPARABLE | UNRESOLVED
```

`TemporalComparabilityStatus` is **not** `CorpusVerdict`, **not**
`ComparabilityClass`, **not** `StateName`, **not** `ClaimState`. It applies only
to the single-metric temporal comparison/change engine.

**Producer.** New replay check **19** (§5) derives it deterministically and emits
both the status and the specific failed gate.

```text
COMPARABLE      -> all applicable structural gates pass (§3.2)
NOT_COMPARABLE  -> an explicit structural requirement FAILED (§3.3)
UNRESOLVED      -> insufficient authoritative basis to decide (§3.4)

UNRESOLVED is NEVER mapped to NOT_COMPARABLE.
```

## 3.2 `COMPARABLE` derivation

```text
 1. same metric-definition semantic binding
 2. same-metric exact-unit identity                    (§1.4)
 3. input methodology compatibility
 4. denominator compatibility
 5. cohort compatibility where applicable
 6. window compatibility
 7. missingness requirements
 8. coverage applicability resolved
 9. where coverage REQUIRED: rule current+ratified, scope matches,
    verdict SUFFICIENT
10. all required source observations available and finite  (§1.0.3)
```

## 3.3 `NOT_COMPARABLE` derivation

An **explicit structural compatibility requirement failed**:

```text
wrong metric binding | unit mismatch | methodology not permitted
denominator mismatch | cohort mismatch | window incompatibility
coverage REQUIRED + verdict INSUFFICIENT | coverage rule scope mismatch

NOT_COMPARABLE != INSUFFICIENT_DATA
NOT_COMPARABLE != UNRESOLVED_AUTHORITY
```

A structural failure is a decision; absence of basis is not a failure.

## 3.4 `UNRESOLVED` derivation and `change_kind` mapping

```text
comparability_status = NOT_COMPARABLE
    -> change_kind = NOT_COMPARABLE

comparability_status = UNRESOLVED
    -> change_kind = INSUFFICIENT_DATA
       (or fail before authoritative change emission)

comparability_status = COMPARABLE
    -> arithmetic stage may derive INCREASE | DECREASE | NO_CHANGE |
       CHANGE_UNDEFINED per the delta operator and zero-baseline law
```

`UNRESOLVED` arises when coverage applicability is `UNRESOLVED`, required
upstream authority is unavailable, or a required observation is absent **where
that absence does not itself establish structural incompatibility**.

`NOT_COMPARABLE` now has a producing check. The v0.4 defect is closed.

---

# 4. Separations (v0.4 §4 — carried unchanged)

No change. The descriptive/prescriptive, measurement/valuation, Book 6/Book 7,
and Book 6/Sensor separations stand as ratified.

---

# 5. Authority replay — TWENTY checks (v0.4 §5 amended)

```text
REPLAY_CHECK_COUNT = 20
AGGREGATE_ONLY      = REJECTED
```

Checks **1–18 are unchanged** from v0.4, in the same order and with the same
content. Check 19 of v0.4 becomes check 20. One check is inserted.

```text
 1. ComparisonRule identity and version
 2. ComparisonRule operator-ratification binding
 3. ComparisonRule canonical content fingerprint
 4. baseline-selection methodology identity and version
 5. baseline-selection methodology canonical fingerprint
 6. baseline-selection methodology current availability / authority
 7. delta_operator validity against the closed set and the arithmetic
 8. baseline measurement refs
 9. comparison measurement refs
10. input measurement Book 2 current authority
11. input measurement methodology compatibility
12. coverage applicability resolution              (§2.1 derivation)
13. coverage-sufficiency rule ref (where REQUIRED)
14. coverage-rule ratification and currentness
15. coverage scope match
16. coverage deterministic verdict
17. metric-definition semantic content match
18. compatible input methodology policy match
19. TEMPORAL COMPARABILITY RESOLUTION              <<< NEW
20. deterministic comparison/change recomputation  (was v0.4 check 19)
```

## 5.1 Check 19 — temporal comparability resolution (NEW)

Derives `comparability_status` deterministically per §3.2–§3.4 and emits:

```text
comparability_status ∈ {COMPARABLE, NOT_COMPARABLE, UNRESOLVED}
failed_gate          = <named gate> | NONE
```

`AGGREGATE_ONLY = REJECTED`: the check reports **which** gate failed, not merely
that something failed. A failure must be localisable to one named gate.

Check 19 is **independently falsifiable**: any single gate in §3.2 can be made
to fail by one fixture mutation while checks 1–18 and 20 continue to pass.

**Ordering is normative.** Check 19 precedes check 20 because comparability is a
precondition of arithmetic. Recomputation must not execute against an unresolved
or refused comparison.

```text
comparability_status != COMPARABLE  ->  check 20 does not recompute a
                                       change; authority is FALSE
```

## 5.2 Check 20 — deterministic recomputation (was v0.4 check 19)

Recomputes the delta, direction, and `change_kind` from the **finite stored
canonical binary64 values** prior to display rounding (§1.0).

```text
`display_metadata` is NOT an input to check 20 and is NOT in check 3's
fingerprint scope. (carried from v0.4)
```

Non-finite inputs are rejected before recomputation (§1.0.3). A non-finite input
fails check 20 with `INSUFFICIENT_DATA` and never yields a delta.

Canonical zero (`+0.0` or `-0.0`) baseline under `RELATIVE_DELTA` yields
`CHANGE_UNDEFINED` / absent `relative_delta`, never 0, inf, or NaN (§1.0.4,
v0.4 §1.3).

If any check fails: `current_authority = FALSE`; history preserved.

## 5.3 Independent falsifiability

All 20 checks are independently falsifiable. Check 19 and check 20 are
falsifiable **separately**: a comparison can pass check 19 (`COMPARABLE`) and
fail check 20 (a recomputed delta disagrees with the recorded delta), and vice
versa (check 19 refuses as `NOT_COMPARABLE`, so check 20 never runs). The
v0.4 replay had no check 19 equivalent, so the two were not separable.

---

# 6. `AC-17` — single-meaning absence (carried, restated)

Carried from v0.4 unchanged. Applied to the new fields:

- `coverage_applicability_source_ref` absent means
  `NO_UPSTREAM_DETERMINATION_EXISTS` **only**.
- `comparability_status = UNRESOLVED` is a decision, not an absence, and means
  only "insufficient authoritative basis to decide".
- `NOT_APPLICABLE` is never an absence encoding under this grammar.

---

# 7. `AC-18` / `AC-18a` — policy is not authority (carried, restated)

Carried from v0.4 unchanged. Restated against v0.5:

- No rule-author policy parameter may determine numeric equality, finiteness,
  unit compatibility, coverage applicability, or comparability status.
- `unit_divisibility_policy` (v0.4 §1.4) is **withdrawn as a derivation**, not
  replaced by a policy. v0.5 §1.4 is a derivation from already-accepted fields.
- The 20-check replay is a derivation, not a policy.

---

# 8. Inventories

## 8.1 Nullable fields (v0.4 §8.1 carried unchanged)

```text
NULLABLE_FIELDS_RE_INVENTORIED   = 36
AMBIGUOUS_NULLABLE_FIELDS        = 0
NULL-1..NULL-9 = PASS
```

No nullable field is added or removed by v0.5. `comparability_status` is
**REQUIRED with a closed domain**, not a nullable field. This is deliberate: an
absent comparability status would reintroduce exactly the ambiguity GAP-4
identified.

## 8.2 Policy parameters (v0.4 §8.2 carried, one withdrawal)

P1–P10 carry unchanged **except P3**, which is withdrawn:

| policy | v0.4 | v0.5 |
|---|---|---|
| P1 `delta_operator` | closed enum {ABSOLUTE_DELTA, RELATIVE_DELTA}; availability derived | carried |
| P2 `compatible_methodology_refs` | explicit allow-list, no wildcard | carried |
| **P3 `unit_requirements`** | **"cites the accepted unit contract; cannot redefine it"** | **WITHDRAWN** — the cited contract does not exist. Unit validity is now derived by §1.4 from `MetricDefinition.unit` and observation `unit`. No rule-author unit policy is consulted. |
| P4 `denominator_requirements` | required, closed | carried |
| P5 `cohort_requirements` | required where relevant, closed | carried |
| P6 `window_compatibility` | required, closed | carried |
| P7 `missingness_requirements` | permitted states named, closed | carried |
| P8 `output_semantics` | names the populable output fields, closed | carried |
| P9 `compatible_input_methodology_policy` | closed | carried |
| P10 `coverage_applicability_resolution_ref` | cites a derived determination; not authorable | carried — derivation now specified by §2.1 |

Withdrawing P3 is the mechanism by which GAP-2 closes **without** adding a unit
contract class. POL-11 becomes testable because no untestable citation remains.

## 8.3 NEW — temporal comparability inventory

```text
TEMPORAL_COMPARABILITY_ENUM_MEMBERS = 3
    COMPARABLE
    NOT_COMPARABLE
    UNRESOLVED
CLOSED_DOMAIN                        = TRUE
PRODUCING_CHECK                      = 19
NOT_APPLICABLE_MEMBER                = ABSENT (correctly)
CROSS_METRIC_CORPUS_CONSULTED        = FALSE
```

## 8.4 NEW — numeric domain inventory

```text
CANONICAL_VALUE_TYPE             = IEEE-754 binary64 (UNCHANGED)
FINITE_NUMERIC_INPUT_REQUIRED    = TRUE
NON_FINITE_MEMBERS_REJECTED      = NaN, +Inf, -Inf
NON_FINITE_OUTCOME               = INSUFFICIENT_DATA
BOOK6_NAN_SENTINEL_INHERITED     = FALSE
EPSILON / ISCLOSE / TOLERANCE    = ABSENT
SIGNED_ZERO_DISTINCTION          = NOT CREATED
CANONICAL_ZERO_PREDICATE         = (value == 0.0)
REAL_NUMBER_EXACTNESS_CLAIM      = FALSE
STORED_VALUE_EXACTNESS_CLAIM     = TRUE
```

---

# 9. Ownership boundary (v0.4 §9 carried unchanged)

No change.

---
# 10. Contract-class audit (v0.5)

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

Not new public authority-bearing contract classes:

| item | why not |
|---|---|
| finite stored binary64 semantics (§1.0) | a definition over existing `float` storage; no type, field, or registry added |
| same-metric exact-unit identity (§1.4) | a derivation over two existing string fields |
| coverage applicability resolver (§2.1) | uses the existing `CoverageRuleRegistry`; adds no registry |
| `TemporalComparabilityStatus` (§3.1) | a closed 3-member enum; a field of the engine, not an authority record with its own registry and ratification |
| 20-check replay (§5) | a check count; adds no contract |

```text
GAP_5 = OPEN — benchmark-rule namespace, NOT resolved by this grammar.
        The v0.4 §2 requirement stands as ratified and remains unsatisfiable.
        Operator decision required before implementation authorization.
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
```

**Not authorized and not performed:** any implementation, any source or test
change, any float/Decimal/Fraction migration, any epsilon or isclose, any unit
ontology or conversion, any cross-metric corpus mutation, any coverage
applicability heuristic, any `NOT_APPLICABLE` by absence, any new canonical
coverage rule, any rule ratification, any Book 7 or Book 8 work, any live
acquisition, and any branch creation, force-push, rebase or history rewrite.
