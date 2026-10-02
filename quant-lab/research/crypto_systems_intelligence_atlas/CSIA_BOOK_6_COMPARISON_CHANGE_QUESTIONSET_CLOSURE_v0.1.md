# CSIA — BOOK 6 COMPARISON / CHANGE QUESTION-SET CLOSURE — v0.1

> **Status:** QUESTION-SET CLOSURE. Ratifies nothing. Implements nothing.
> Does not redesign v0.3 except where a **new concrete design defect** was
> demonstrated during the audit.
> **Date:** 2026-10-01
> **Subject:** amendment plan v0.3 and its governing contracts.
> **Closes:** unasked classes `D-A` (nullable field multi-meaning) and `D-B`
> (policy parameter as hidden threshold) recorded by
> `..._RATIFICATION_READINESS_v0.1.md`.
> **Authority:** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.

---

## 0. Outcome of the closure audit

```text
AMBIGUOUS_NULLABLE_FIELDS               = 6
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY = 5
NEW_DESIGN_DEFECTS_FOUND                = 2 classes / 11 fields
RATIFICATION_READINESS                  = HOLD
```

The two new general classes did their job. Both `D-A` and `D-B` found
**instances that the Q1–Q40 question set could not see**, and all of those
instances are now enumerated with exact field names. This is the closure
working, not the closure failing — but it means the plan is **not** ready for
ratification, and saying otherwise would repeat the exact error
(`OPEN_BLOCKING_D7N_DECISIONS = 0` printed beside a parenthetical that
contradicted it) that this program has already caught once.

---

## 1. `AC-17` — SINGLE-MEANING ABSENCE

```text
AC-17  NO nullable / optional / absent field in ComparisonRule,
       ChangeObservation, ComparisonDerivationBinding, or any seam-facing
       record may use absence to encode more than one semantic state.

For every nullable / optional field, absence has EXACTLY ONE defined meaning.
Where more than one meaning would be natural, the ambiguity is replaced by an
explicit enum / status / discriminator.

ABSENT
!=
UNKNOWN
!=
NOT_APPLICABLE
!=
UNAVAILABLE
!=
NOT_REQUIRED
!=
UNRESOLVED
!=
UNDEFINED
!=
ZERO
!=
FALSE

unless the contract explicitly defines exactly one of those as the single
meaning of absence for that field, and names the discriminator.
```

`AC-17` covers the **class**, not the instance: it binds every present and
future field in every contract in the amendment, and requires an explicit
discriminator wherever absence is conditioned.

---

## 2. Complete nullable-field inventory

Audited from the v0.3 field definitions, not from assumption. **36 nullable,
optional, or absent-capable fields** across four contracts.

### 2.1 `ComparisonRule` — 12 candidates

| # | field | nullable? | meaning of absence | another explicit state exists? | ambiguous? |
|---|---|---|---|---|---|
| R1 | `metric_definition_semantic_fingerprint` | yes (pre-ratification only) | not yet bound at ratification | no | no — discriminated by `registration_state`; post-ratification absence is a rejection, not a second meaning |
| R2 | `coverage_sufficiency_rule_ref` | yes | derived status is `NOT_APPLICABLE` | yes (`coverage_requirement_status`) | **no** — v0.3's repair; explicitly discriminated |
| R3 | `coverage_applicability_source_ref` | yes | *(unspecified in v0.3)* | `coverage_requirement_status` | **YES — F-2** |
| R4 | `supersedes` | yes | *(unspecified in v0.3)* | `version`, `registration_state` | **YES — F-5** |
| R5 | `valid_time.valid_to` | yes | *(unspecified in v0.3)* | no | **YES — F-5** |
| R6 | `unit_divisibility_policy` | yes | *(unspecified in v0.3)* | no | **YES — F-1** |
| R7 | `coverage_requirement_status` | no — required enum | n/a | n/a | no |
| R8 | `superseded` (status-derived) | — | — | — | no |
| R9 | any optional `denominator_requirements` value | yes | not specified | `denominator_semantics` `NOT_APPLICABLE` (accepted) | no — accepted discriminator exists |
| R10 | any optional `cohort_requirements` value | yes | not specified | comparability class (accepted) | no — accepted discriminator exists |
| R11 | `window_compatibility` optional members | yes | not specified | no | no — permissive values are named as required |
| R12 | `missingness_requirements` optional members | yes | not specified | `missingness` on the record | no |

### 2.2 `ChangeObservation` — 8 candidates

| # | field | nullable? | meaning of absence | explicit state? | ambiguous? |
|---|---|---|---|---|---|
| O1 | `absolute_delta` | yes | not defined for this comparison | `change_kind` ∈ {`CHANGE_UNDEFINED`, `NOT_COMPARABLE`, `INSUFFICIENT_DATA`} | **no** — discriminated by `change_kind`; zero is never encoded as absence |
| O2 | `relative_delta` | yes | not defined (incl. zero baseline) | `change_kind` | **no** — same discriminator |
| O3 | `coverage_verdict` | no — enum incl. `UNKNOWN` | n/a | `UNKNOWN` is explicit | **no** — `NULL-3` satisfied: absence never means unknown |
| O4 | `coverage_observation` | yes | *(unspecified in v0.3)* | `coverage_requirement_status` | **YES — F-3** |
| O5 | `coverage_requirement_status` | no — required enum | n/a | n/a | no |
| O6 | `baseline_selection_methodology_ref` | no — required (cited) | n/a | n/a | no |
| O7 | `derivation_binding_ref` | no — required | n/a | n/a | no |
| O8 | `source_measurement_refs` / `baseline_measurement_refs` / `comparison_measurement_refs` | no — non-empty | n/a | n/a | no — non-emptiness is normative, so absence is a rejection |

### 2.3 `ComparisonDerivationBinding` — 4 candidates

| # | field | nullable? | meaning of absence | ambiguous? |
|---|---|---|---|---|
| B1 | `coverage_applicability_resolution_ref` | yes | not applicable | **no** — discriminated by the bound status |
| B2 | `coverage_sufficiency_rule` | yes (where not REQUIRED) | not required | **no** — discriminated |
| B3 | `comparison_semantics_fingerprint` | no — required | n/a | no |
| B4 | `compatible_input_methodology_policy` | no — required | n/a | no |

### 2.4 `ResponseLink` (seam-facing) — 4 candidates

| # | field | nullable? | meaning of absence | ambiguous? |
|---|---|---|---|---|
| L1 | `coverage_verdict_quoted` | yes — marked "optional" | **the underlying record's verdict was not carried across** | **YES — F-4** |
| L2 | `coverage_requirement_quoted` | yes — marked "optional" | same | **YES — F-4** |
| L3 | `causal_status` | no — fixed `ASSOCIATION_ONLY` | n/a | no |
| L4 | `evidence_refs` | yes | *(unspecified in v0.3)* | no — a link without evidence refs is rejected by `RL-1`, so absence is a rejection |

### 2.5 Inventory result

```text
NULLABLE_FIELDS_INVENTORIED           = 36
AMBIGUOUS_NULLABLE_FIELDS             = 6
  F-2  ComparisonRule.coverage_applicability_source_ref
  F-3  ChangeObservation.coverage_observation
  F-4  ResponseLink.coverage_verdict_quoted
  F-4  ResponseLink.coverage_requirement_quoted
  F-5  ComparisonRule.supersedes
  F-5  ComparisonRule.valid_time.valid_to
REQUIRED_OUTCOME                     = 0
ACTUAL                               = 6
VERDICT                              = HOLD
```

### 2.6 The four findings in detail

**F-2 — `coverage_applicability_source_ref`.** v0.3:62 describes it as "the
accepted determination this status was read from". When the derived status is
`REQUIRED` or `NOT_APPLICABLE`, a determination exists and must be recorded.
When the status is `UNRESOLVED`, **there is no determination to read from** —
upstream is silent. So absence means *either* "no determination exists" *or*
"a determination existed and was not recorded". The second is a defect and the
first is correct behaviour, and nothing in v0.3 separates them. Under `AC-17`
this requires an explicit statement: absence means "no upstream determination
exists", and a missing citation under a `REQUIRED`/`NOT_APPLICABLE` status is
a rejection.

**F-3 — `ChangeObservation.coverage_observation`.** For a metric whose derived
status is `NOT_APPLICABLE`, no coverage observation is produced. For a metric
that is `REQUIRED` but whose coverage was not measured, also no observation.
Absence therefore conflates *not applicable* with *not measured* — the exact
`D-A` shape, on a different field, invisible to Q35 because Q35 only asked
about `coverage_sufficiency_rule_ref`. The discriminator is already present on
the record (`coverage_requirement_status`); what is missing is the statement
that absence is read *through* that discriminator.

**F-4 — the seam's "optional" quoted fields.** `ResponseLink` marks
`coverage_verdict_quoted` and `coverage_requirement_quoted` optional. The
underlying `ChangeObservation` always carries both (one as an enum value,
including an explicit `UNKNOWN`). So a link that omits them is **silent about
a field the source record always had** — a link may exist against a record
whose coverage verdict was `UNKNOWN` while the link itself says nothing. That
is silence-as-ambiguity reintroduced one layer up, and it is precisely the
`RL-7`/absence-integrity principle applied to the wrong field. Required: if
the source record carries the field, the link **must** carry it; the link is
not permitted to be silent about a known value.

**F-5 — `supersedes` and `valid_time.valid_to`.** Both are conventional and
both are unspecified. `supersedes` absent should mean "this is the first
version"; it could equally be read as "supersession is unknown". `valid_to`
absent should mean "still valid"; it could be read as "end unknown". Neither
ambiguity is dangerous in isolation, but `AC-17` is a class rule and these are
instances of it, and the program has already learned that seemingly harmless
absences are where waivers hide.

---

## 3. `AC-18` — DECLARATIVE POLICY, NOT TUNABLE AUTHORITY

```text
AC-18  No rule-author-settable policy parameter may:
         make a comparison more permissive
         manufacture sufficiency
         weaken a fail-closed gate
         create a hidden threshold
         create materiality or significance
         create health or adoption semantics
         override upstream authority
         bypass a separately operator-ratified rule authority

POLICY PARAMETER
!=
SUFFICIENCY AUTHORITY

POLICY PARAMETER
!=
THRESHOLD AUTHORITY

POLICY PARAMETER
!=
GATE WAIVER
```

Additionally, and as the operative half:

```text
AC-18a  EVERY rule-author-settable policy parameter MUST be a CLOSED ENUM or
        a TYPED POLICY OBJECT with a finite, enumerated value domain and a
        declared semantic for EVERY value.

        A value domain that is open, example-illustrated, or free-text is
        INVALID for an authority-bearing parameter.
```

---

## 4. Complete policy-parameter inventory

### 4.1 `comparison_semantics` embedded parameters — 5

| # | parameter | v0.3 declaration | closed enum? | more permissive possible? | acts as hidden threshold? | fingerprinted? |
|---|---|---|---|---|---|---|
| P1 | `delta_formula_basis` | "e.g. post − baseline; (post − baseline) / baseline" | **NO — open example** | **YES** (F-1) | **YES** (F-1) | yes (inside the rule fingerprint) |
| P2 | `direction_derivation` | "how INCREASE / DECREASE are derived" | **NO** | **YES** (F-1) | **YES** (F-1) | yes |
| P3 | `zero_baseline_policy` | "REQUIRED; fail-closed for relative" | **NO** | **YES** (F-1) | partially (F-1) | yes |
| P4 | `unit_divisibility_policy` | "when a relative delta is defined" | **NO** | **YES** (F-1) | partially (F-1) | yes |
| P5 | `rounding_precision_policy` | "declared, never implicit" | **NO** | **YES** (F-1) | **YES** (F-1) | yes |

### 4.2 `ComparisonRule` structural parameters — 7

| # | parameter | closed? | permissive value? | hidden threshold? | silently changes upstream authority? |
|---|---|---|---|---|---|
| P6 | `compatible_methodology_refs` | yes — explicit allow-list, never a wildcard | no — a wider list widens *admission*, not *verdict* | no | no |
| P7 | `unit_requirements` | yes — required dimensional class | no | no | no |
| P8 | `denominator_requirements` | yes | no | no | no |
| P9 | `cohort_requirements` | yes | no | no | no |
| P10 | `window_compatibility` | yes | no | no | no |
| P11 | `missingness_requirements` | yes — permitted states named | no | no | no |
| P12 | `output_semantics` | yes — names which output fields may be populated | no | no | no |

### 4.3 `ComparisonDerivationBinding` — 2

| # | parameter | closed? | permissive? | hidden threshold? |
|---|---|---|---|---|
| P13 | `compatible_input_methodology_policy` | yes | no | no |
| P14 | `coverage_applicability_resolution_ref` | yes — cites a derived determination | **no** — a rule cannot author it (the v0.3 repair) | no |

### 4.4 Inventory result

```text
POLICY_PARAMETERS_INVENTORIED         = 14
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY = 5
  P1 delta_formula_basis
  P2 direction_derivation
  P3 zero_baseline_policy
  P4 unit_divisibility_policy
  P5 rounding_precision_policy
REQUIRED_OUTCOME                     = 0
ACTUAL                               = 5
VERDICT                              = HOLD
```

### 4.5 Finding F-1 in detail

The five `comparison_semantics` parameters are the rule's entire derivation
meaning, and they are the five that carry the authority. v0.3 declares them
as *required* and inside the canonical fingerprint — which is the correct
governance shape — but it never constrains their **value domains**. P1 is
written as `e.g. post − baseline; (post − baseline) / baseline`, which is an
illustration, not an enumeration. A free-form, fingerprinted, operator-ratified
formula field is still a free-form formula field: ratification guarantees
*who* chose it, not *what was chosen*.

This matters concretely:

- `delta_formula_basis` could be set to a formula the amendment never
  contemplated, including one that returns a bounded or clipped value where
  the arithmetic is undefined — a manufactured verdict from an undefined
  quantity.
- `direction_derivation` could classify a change without reference to the
  delta at all.
- `zero_baseline_policy` could select a "percentage convention" or a capped
  substitute, converting an undefined relative delta into a number.
- `rounding_precision_policy` could suppress small but real changes, i.e. act
  as a materiality threshold by another name.

Every one of those is a *policy parameter acting as authority*, which is
exactly what `D-B` named and what `AC-18` forbids. Fingerprinting does not
fix it: a fingerprinted permissive policy is still a permissive policy.

**Required:** all five become closed enums (or typed policy objects) with a
declared semantic for every value, and the permissive values that the
fail-closed doctrine already implies — capping, substituting, suppressing —
are removed from the domain rather than merely discouraged.

---

## 5. Special stress: rounding / precision (Phase 7)

`rounding_precision_policy` can flip the direction classification:

```text
baseline = 100.000,  post = 100.004

precision 2 decimals → 100.00 vs 100.00 → delta 0.000 → NO_CHANGE
precision 3 decimals → 100.004 vs 100.000 → delta 0.004 → INCREASE
```

Both are legitimate under different explicitly ratified rules. **Neither is
globally more correct**, and the correct behaviour is to refuse to choose.

```text
PASS (as a doctrine)   the policy is REQUIRED, explicit, fingerprinted, and
                      ratified with the rule; changing it changes the rule
                      fingerprint and forces a new version + new ratification
FAIL (as a contract)   the value domain is unconstrained, so "a precision
                      coarse enough to suppress every change below some
                      magnitude" is currently a legal value — a materiality
                      threshold in disguise (F-1)
```

The specific failure: an unconstrained precision policy lets a rule author
express "changes smaller than X are NO_CHANGE". That is a **significance
threshold**, prohibited by the plan's own anti-score firewall — reachable
through a parameter the firewall does not name.

## 6. Special stress: zero-baseline policy (Phase 8)

Intended doctrine: absolute delta may remain valid; relative delta is absent
/ undefined.

```text
PASS   no alternative permissive mode is *specified* — v0.3 says fail-closed
FAIL   the parameter is unconstrained, so a policy value that substitutes 0,
       a capped value, or a percentage convention is not excluded by the
       contract. "Specified fail-closed" is not the same as "only fail-closed
       is possible" (F-1)
```

This is the distinction the whole closure turns on: **v0.3 describes the
intended behaviour but does not foreclose the alternatives.**

## 7. Special stress: free-string / dynamic policy (Phase 9)

| risk | present in v0.3? |
|---|---|
| free-string policy names | **partly** — P1–P5 value domains open |
| free-form formulas | **YES** — P1 `delta_formula_basis` is illustrated, not enumerated |
| caller-defined expressions | not specified; foreclosed by the same fix |
| dynamic evaluation (`eval` / `exec`) | **absent** — no such mechanism is proposed anywhere |
| arbitrary numeric parameters | **partly** — P5 precision is numeric and unbounded in domain |

```text
NO_EVAL            = TRUE   (nothing in v0.3 proposes dynamic evaluation)
NO_EXEC            = TRUE
NO_CALLBACK        = TRUE
FREE_STRING_POLICY_AUTHORITY = PARTLY PRESENT (F-1, five parameters)
```

---

## 8. Repairs required

**No artifact was rewritten in this session.** The repairs are specified here
so a successor can be produced deterministically.

| # | repair | class | artifact affected |
|---|---|---|---|
| R-1 | `AC-18a`: closed enum / typed policy object for `delta_formula_basis`, `direction_derivation`, `zero_baseline_policy`, `unit_divisibility_policy`, `rounding_precision_policy`, with a declared semantic per value; remove capping/substituting/suppressing values from the domain | D-B | grammar v0.4 |
| R-2 | `coverage_applicability_source_ref`: absence means "no upstream determination exists"; a missing citation under `REQUIRED`/`NOT_APPLICABLE` is a rejection | D-A | grammar v0.4 |
| R-3 | `ChangeObservation.coverage_observation`: absence read **through** `coverage_requirement_status`; state the discriminator explicitly | D-A | grammar v0.4 |
| R-4 | seam: `coverage_verdict_quoted` / `coverage_requirement_quoted` must be carried when the source record carries them; a link may not be silent about a known value | D-A | seam v0.4 |
| R-5 | `supersedes` absence = "first version"; `valid_time.valid_to` absence = "still valid" | D-A | grammar v0.4 |

```text
ARTIFACTS_NOT_CREATED_THIS_SESSION = grammar v0.4, plan v0.4, seam v0.4
REASON = the operator authorization is QUESTION-SET CLOSURE + FINAL
         RATIFICATION-READINESS REVIEW ONLY. The repairs above are specified
         so a successor can be produced deterministically once authorized.
         Creating v0.4 here would exceed the authorized scope.
```

---

## 9. Summary

```text
AC_17_SINGLE_MEANING_ABSENCE = DEFINED (audit found 6 instances)
AC_18_POLICY_NOT_AUTHORITY  = DEFINED (audit found 5 instances)
NULLABLE_FIELDS_INVENTORIED = 36
AMBIGUOUS_NULLABLE_FIELDS   = 6   (required 0)
POLICY_PARAMETERS_INVENTORIED = 14
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY = 5   (required 0)
NEW_DESIGN_DEFECTS_FOUND    = 2 classes / 11 fields
RATIFICATION_READINESS      = HOLD
```

---

*End of closure. Invariants defined; instances found; no artifact rewritten;
nothing ratified.*
