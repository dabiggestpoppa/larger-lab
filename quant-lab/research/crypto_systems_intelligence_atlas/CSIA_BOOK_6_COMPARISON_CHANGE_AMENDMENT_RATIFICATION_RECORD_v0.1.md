# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT RATIFICATION RECORD — v0.1

> **Status:** `RATIFIED`. This record ratifies a **PLAN** and nothing else.
> Implements nothing. Re-accepts nothing. Ratifies no rule of any kind.
> **Date:** 2026-10-02
> **Operator decision id:** `BOOK6-COMPARE-AMEND-v0.4` (collision-free; does
> not reuse or extend the `D6M-*` or `D7N-*` namespaces)
> **Ratifies:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md`
> **Anchor:** the commit that introduced the ratified plan
> (`28bfac52c23c891ebb54e9924dedc925a859b359`)
> **Scope of authority granted:** permission to open a **separately
> authorized** offline implementation round. That round is **not** authorized
> by this record and has not been requested.

---

## 0. The ratification decision

```text
BOOK                                              = 6
AMENDMENT                                         = COMPARISON / CHANGE
RATIFIED_PLAN                                     = v0.4
PLAN_STATUS                                       = RATIFIED
RATIFIED_PLAN_PATH                                = CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md
RATIFIED_PLAN_ANCHOR                              = 28bfac52c23c891ebb54e9924dedc925a859b359

GRAMMAR                                           = v0.4
BOUNDARY                                          = v0.3
SEAM                                             = v0.4
PRE_RATIFICATION_REVIEW                           = v0.5 / 48 of 48 PASS
RATIFICATION_READINESS                            = v0.3 / PASS
READINESS_SURFACES                                = 16 / 16 PASS

NEW_UNASKED_STRUCTURAL_DEFECTS                    = 0
NEW_DESIGN_DEFECTS_FOUND                          = 0
AMBIGUOUS_NULLABLE_FIELDS                         = 0
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY       = 0
EVERY_KNOWN_DEFECT_HAS_GENERAL_CLASS_COVERAGE     = TRUE

NEW_AUTHORITY_BEARING_CONTRACT_CLASSES             = 2
  ComparisonRule
  ChangeObservation
HIDDEN_THIRD_CONTRACT                             = NONE

COMPARISON_RULES_RATIFIED                         = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED               = 0
BENCHMARK_RULES_RATIFIED                          = 0

BOOK_6_IMPLEMENTATION_AUTHORITY                   = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY                   = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY                   = FALSE
LIVE_ACQUISITION_AUTHORITY                        = FALSE

D6M_5                                             = OPEN_DEFERRED
```

```text
PLAN RATIFIED
!=
IMPLEMENTATION AUTHORIZED
!=
BOOK 6 RE-ACCEPTED
```

## 1. Governing artifacts, each anchored

| artifact | version | introducing commit |
|---|---|---|
| `..._COMPARISON_CHANGE_GRAMMAR_v0.4.md` | v0.4 | `0bde9a5a8532a3b1f7adee7f67aa3da3a587eddb` |
| `..._COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.3.md` | v0.3 | `fbf9d3d8f50b8e427549cc882a0cf31059436966` |
| `..._TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.4.md` | v0.4 | `fbf9d3d8f50b8e427549cc882a0cf31059436966` |
| `..._COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md` | v0.4 | `28bfac52c23c891ebb54e9924dedc925a859b359` |
| `..._COMPARISON_CHANGE_AMENDMENT_PRE_RATIFICATION_REVIEW_v0.5.md` | v0.5 | `384a1a0a337c14d0088a0c5170aa2434c5229f2f` |
| `..._COMPARISON_CHANGE_AMENDMENT_RATIFICATION_READINESS_v0.3.md` | v0.3 | `742223b5f6c2d5d61565422f41484328328d3d57` |

All paths are relative to `quant-lab/research/crypto_systems_intelligence_atlas/`.
Superseded and preserved unmodified: plan v0.3 (`SUPERSEDED / NOT
RATIFIABLE`), grammar v0.1-v0.3, boundary v0.1-v0.2, seam v0.1-v0.3,
pre-ratification review v0.1-v0.4, readiness v0.1-v0.2.

## 2. Ratified doctrine (now binding as design law)

```text
DELTA OPERATORS (closed set, exactly two)
  ABSOLUTE_DELTA = comparison_value - baseline_value
  RELATIVE_DELTA = (comparison_value - baseline_value) / baseline_value
                  where semantically valid
No free-form formula. No expression language. No caller formula.
A new operator requires a NEW CONTRACT VERSION under amendment governance.

direction  = SIGN(canonical UNROUNDED absolute_delta)
  > 0 INCREASE | < 0 DECREASE | = 0 NO_CHANGE (exact canonical equality)
DIRECTION_DERIVATION_RULE = FIXED / NON-CONFIGURABLE
  direction_derivation no longer exists as a field

ZERO_BASELINE_POLICY = FIXED_FAIL_CLOSED
  baseline == 0 -> absolute delta normal; relative delta UNDEFINED / ABSENT
  never 0, infinity, NaN, capped, 100%, or a percentage convention

UNIT_ARITHMETIC_VALIDITY = DERIVED_FROM_UNIT_CONTRACT
  unit_divisibility_policy no longer exists as a field
  a rule may cite unit requirements, never redefine the mathematics

ROUNDING_AFFECTS_CHANGE_CLASSIFICATION = FALSE
DISPLAY_ROUNDING_IS_AUTHORITY          = FALSE
  rounding_precision_policy no longer exists as an authority-bearing field
  display precision is presentation metadata, outside the canonical
  fingerprint and outside authority replay check 19

NO_CHANGE != NOT_MATERIAL_CHANGE
  no epsilon, tolerance, materiality, or significance field exists
```

`AC-17` (single-meaning absence), `AC-18` (policy parameter is not
authority), `AC-18a` (no open policy domains), `AC-18b` (derived semantic
over rule-author choice), `AC-19` (no tolerance/materiality in comparison)
and `AC-20` (display is not authority) are ratified with the plan.

## 3. Governance boundary as ratified

```text
NEW PUBLIC AUTHORITY-BEARING CONTRACT CLASSES = 2
  ComparisonRule
  ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE

COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY,
  established BY THIS AMENDMENT.
  D6M-3 is a governance-PATTERN precedent only; it does NOT grant, extend, or
  lend comparison-rule ratification authority.
  Each comparison rule is individually operator-ratified; at canonical
  bootstrap COMPARISON_RULES_RATIFIED = 0.

REGISTRATION != RATIFICATION
OBJECT STATUS IS NOT AUTHORITY
MUTATED CONTENT UNDER A BOUND IDENTITY REJECTS
SUPERSESSION DOES NOT INHERIT
```

No accepted contract was modified. `MetricDefinition`,
`MeasurementMethodology`, `MeasurementObservation`, `ValuationObservation`,
`NormalizationRule`, `StateRule`, `FundamentalStateVector` and all D6M
decisions are untouched. Book 1-5 and the Constitution require no amendment.

## 4. Derivation binding as ratified

Ratifying a `ComparisonRule` binds, with no late-bound dependency and no
auto-follow:

```text
rule identity / version / canonical fingerprint
baseline benchmark methodology identity / version / canonical fingerprint
delta operator (closed set)
coverage applicability determination
coverage-sufficiency rule identity / version / fingerprint (where REQUIRED)
metric-definition semantic fingerprint
compatible input methodology policy
```

A bare name whose content may drift is not a binding.

## 5. Authority replay as ratified (nineteen checks, re-resolved at each use)

```text
 1 ComparisonRule identity and version
 2 ComparisonRule operator-ratification binding
 3 ComparisonRule canonical content fingerprint
 4 baseline-selection methodology identity and version
 5 baseline-selection methodology canonical fingerprint
 6 baseline-selection methodology current authority
 7 closed delta operator validity
 8 baseline measurements
 9 comparison measurements
10 input measurement Book 2 current authority
11 input measurement methodology compatibility
12 coverage applicability resolution
13 coverage-sufficiency rule ref (where REQUIRED)
14 coverage-rule ratification and currentness
15 coverage scope match
16 deterministic coverage verdict
17 metric-definition semantic content match
18 compatible input methodology policy match
19 deterministic change recomputation
```

```text
ANY CHECK FAILS  ->  current_authority = FALSE, history preserved
RATIFIED THEN    !=  AUTHORITATIVE NOW
```

## 6. `ChangeObservation` status as ratified

```text
ChangeObservation = BOOK 6-LOCAL DERIVED RECORD
NOT a Book 2 Claim
NOT independently ratified
NOT self-authorizing
current_authority is DERIVED by replay, never asserted

RULE RATIFIED     != CHANGE EXISTS
CHANGE EXISTS     != CURRENTLY AUTHORITATIVE
OBJECT STATUS     != AUTHORITY
```

## 7. Book 7 seam as ratified

Book 7 may consume only a `CURRENTLY AUTHORITATIVE` `ChangeObservation`, by
reference. It may reference a change and link it to an action / event window.
It may **not** recompute a change, choose a baseline, change arithmetic, apply
rounding, apply epsilon, apply tolerance, reclassify a small change, omit known
coverage context, or overwrite Book 6 output.

```text
SOURCE_VALUE_PRESENT -> SEAM_QUOTE_PRESENT
SILENCE_ABOUT_KNOWN_COVERAGE = INVALID
```

`RL-1` ... `RL-13` ratified. No Book 7 architecture changed, no Book 7 decision
closed, and `D7N-7 = A` remains binding.

## 8. D6M series as ratified

```text
D6M-1  UNCHANGED  - ChangeObservation is Book 6-local derived
D6M-2  UNCHANGED  - no normalization in comparison; canonical arithmetic is
                   fixed, so none can be smuggled in
D6M-3  UNCHANGED  - no new state class; comparison-rule ratification
                   authority established BY THIS AMENDMENT on a
                   D6M-3-consistent pattern; NO authority inherited; the
                   accepted benchmark namespace is reused unmodified
D6M-4  UNCHANGED  - valuation authority untouched
D6M-5  OPEN_DEFERRED - no usage / health semantics added
```

`D2_6 = IN_FORCE`, unmodified. No usage, health, or adoption interpretation
was added by this amendment.

## 9. Accepted residual limitations (limitations, not hidden features)

```text
no first-class MetricDefinition versioning - metric definition content is
  fingerprint-bound at ratification instead
no tolerance / materiality methodology
no shared versioned delta-operator class - the operator set is closed and
  fixed in the grammar; a new operator requires a contract version
no causal methodology - D7N-4 OPEN / DEFERRED
no usage / health semantics - D6M-5 OPEN_DEFERRED
all canonical rule counts remain 0
no historical Book 2 point-in-time authority replay
```

## 10. What this record does not authorize

```text
NO BOOK 6 IMPLEMENTATION
NO BOOK 6 RE-ACCEPTANCE
NO BOOK 7 RATIFICATION
NO BOOK 7 IMPLEMENTATION
NO BOOK 8
NO D8
NO LIVE ACQUISITION / RPC / NETWORK / DATABASE / GRAPH DATABASE
NO COMPARISON-RULE RATIFICATION
NO BENCHMARK-RULE RATIFICATION
NO COVERAGE-SUFFICIENCY-RULE RATIFICATION
NO MATERIALITY / TOLERANCE METHODOLOGY
NO HEALTH / USAGE THRESHOLDS
NO CAUSALITY SEMANTICS
NO SCORE / RANK / GRADE / BUY / SELL
```

Book 6 remains `FROZEN_ACCEPTED` on its existing accepted implementation
anchor `3919fb8052e216e94034a753fb258d338c5fa0dc`. This amendment is ratified
as a plan; it has not been implemented on that lineage, and the Book 6
implementation anchor is therefore unchanged by this record.

---

## 11. Next gate

```text
NEXT = BOOK 6 COMPARISON / CHANGE AMENDMENT OFFLINE IMPLEMENTATION
       AUTHORIZATION REVIEW
```

That review is a separate operator act. It grants nothing by existing, and
the five-step ladder remains: plan ratification (this record) -> separate
implementation authorization -> implementation on the accepted lineage ->
regression / hardening review -> formal Book 6 re-acceptance. Only the first
step has occurred.

---

*End of ratification record v0.1. Ratifies the PLAN v0.4 only. Implements
nothing; re-accepts nothing; ratifies no rule.*
