# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PLAN — v0.3

> **Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.2.md`
> (**preserved unmodified**, now `SUPERSEDED / NOT RATIFIABLE`).
> **Repairs incorporated:** `R6A-D4` (derivation methodology decay),
> `R6A-D5` (coverage applicability source), boundary contract-class
> inconsistency. Audit in
> `CSIA_BOOK_6_COMPARISON_CHANGE_DERIVATION_AUTHORITY_AUDIT_v0.1.md`.
> **Governs:** `..._BOUNDARY_v0.2.md`, `..._GRAMMAR_v0.3.md`,
> `..._SEAM_v0.3.md`
> **Ratifies nothing. Implements nothing. Grants no implementation authority.**

---

## 1. Scope

Add exactly two contract classes to Book 6 — `ComparisonRule` and
`ChangeObservation` — over measurements Book 6 already accepted.

```text
ADDED:     ComparisonRule, ChangeObservation
REUSED:    accepted benchmark-rule namespace (baseline selection)
           accepted coverage-sufficiency rules
UNCHANGED: MetricDefinition, MeasurementMethodology, MeasurementObservation,
           ValuationObservation, NormalizationRule, StateRule,
           FundamentalStateVector, all D6M decisions, all accepted tests
FORBIDDEN: any new state class; any score/rank/grade; any narrative or
           response concept; any Book 5 write-back; any Book 2 promotion;
           any embedded coverage threshold; any self-ratified object status;
           any late-bound derivation ref; any rule-author coverage waiver
```

## 2. `ComparisonRule`

Field set in grammar v0.3 §1. Governance:

```text
- versioned; canonical fingerprint over ALL semantic fields including the
  embedded comparison_semantics section
- baseline_selection_methodology_ref = an ACCEPTED benchmark rule (id +
  version + canonical fingerprint), individually operator-ratified under D6M-3
- comparison_semantics is a REQUIRED section INSIDE the rule's fingerprint —
  not an external ref, so there is no third contract class and no late-bound
  derivation
- NO NUMERIC COVERAGE THRESHOLD on this object
- coverage_requirement_status is DERIVED upstream, never a rule-author choice
- coverage_sufficiency_rule_ref is a CITATION that must agree with the
  derived status; null or mismatched when REQUIRED is rejected
- COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY, established BY THIS
  AMENDMENT using a D6M-3-CONSISTENT pattern; no authority inherited
- REGISTRATION != RATIFICATION; OBJECT STATUS IS NOT AUTHORITY
- BOOTSTRAP: COMPARISON_RULES_RATIFIED = 0
```

## 3. `ChangeObservation`

Field set in grammar v0.3 §3. Requirements:

```text
- Book 6-local derived record; NOT a Book 2 claim; no promotion path
- RATIFIED removed from the derived-record vocabulary
- construction_status (workflow) distinct from record_state (lifecycle) and
  from current_authority (DERIVED)
- derivation_binding_ref recorded and re-resolved at use time
- coverage_verdict is a replayed result, never asserted
- no event, action, response, window, causality, health, or merit field
```

## 4. Derivation binding and authority replay

The v0.2 eleven-check replay becomes **nineteen** (grammar v0.3 §4). The
additions are exactly the dependencies v0.2 never looked at:

```text
 4-6  baseline-selection methodology identity / fingerprint / currentness
 7    comparison semantics fingerprint
12    coverage applicability resolution (derived tri-state)
17    metric-definition semantic content match
```

A `ComparisonRule` is ratified against a **derivation context**, not merely
its own bytes. A byte-identical rule over a changed dependency is stale, not
current.

## 5. Coverage doctrine

```text
COVERAGE_OBSERVATION != COVERAGE_SUFFICIENCY_RULE
COVERAGE_REQUIRED     != RULE_AUTHOR_DISCRETION
```

Applicability is **derived from accepted upstream semantics** and resolved
through a tri-state:

```text
REQUIRED       → G7 evaluated; missing/insufficient verdict → NOT_COMPARABLE
UNRESOLVED     → G7 not evaluated; COMPARISON UNAVAILABLE (fail closed)
NOT_APPLICABLE → G7 skipped, upstream determination cited on the record
```

The amendment reads the accepted `MetricDefinition` and bound
`MeasurementMethodology`; it does **not** add an applicability field to an
accepted contract. Upstream silence is `UNRESOLVED`, which fails closed.

## 6. Baseline methodology

Four candidate families, mapped onto the **accepted** benchmark namespace
(grammar v0.3 §1.2), **no universal default**. Baseline selection is
methodology, cited with identity + version + fingerprint, and re-resolved at
use time. `BASELINE_UNAVAILABLE` is a first-class outcome.

## 7. Comparability

Nine gates, G7 rebuilt on the derived applicability tri-state. Any failure →
`NOT_COMPARABLE` with both numeric fields absent. `COMPARABLE != CHANGED`.
Book 6 remains the sole normalization authority (D6M-2).

## 8. Missingness

```text
BASELINE_UNAVAILABLE         → INSUFFICIENT_DATA, no delta
POST_DATA_UNAVAILABLE        → INSUFFICIENT_DATA, no delta
COVERAGE_SUFFICIENCY_UNKNOWN → NOT_COMPARABLE (REQUIRED, no ratified rule)
COVERAGE_INSUFFICIENT        → NOT_COMPARABLE (ratified rule says insufficient)
COVERAGE_APPLICABILITY_UNRESOLVED → COMPARISON UNAVAILABLE (fail closed)
NO_CHANGE_OBSERVED           → a valid change_kind; NOT a negative response
```

`NO CHANGE` ≠ `NO DATA`; `ZERO_VALUE` ≠ `ZERO_CHANGE`.

## 9. Numeric change

Unchanged. `absolute_delta = comparison − baseline`;
`relative_delta = (comparison − baseline) / baseline`. Zero baseline →
relative delta **absent, fail-closed**. Absent for missing baseline, missing
comparison observation, incompatible unit, invalid coverage / missingness /
temporal order. No hidden currency conversion. Absent field ≠ 0.

## 10. Methodology sensitivity

Parallel `ChangeObservation` records from different legitimate rules are
preserved side by side. Never averaged, never silently selected, never
reconciled. Every consumer (each Book 7 `ResponseLink`) must cite the exact
record and rule relied upon.

## 11. D6M compatibility

| Decision | Status |
|---|---|
| D6M-1 (measurement-object authority) | unaffected — `ChangeObservation` is Book 6-local derived |
| D6M-2 (normalization separate) | unaffected — comparison performs no normalization |
| D6M-3 (state-rule governance) | unaffected — no new state class. Comparison-rule ratification authority is established **by this amendment** using a D6M-3-*consistent* pattern; **no authority is inherited**. The **accepted** benchmark namespace is reused under D6M-3's existing individual-ratification rule, unmodified. |
| D6M-4 (valuation authority) | unaffected — explicit numeraire, Book 2 price provenance, no global price source |
| D6M-5 (usage / health) | unaffected and still `OPEN_DEFERRED` — a change record is not a health, adoption, or usage-sufficiency reading |

**No D6M amendment is required. No prior decision is silently expanded.**

## 12. Book 5 / valuation non-impact

Book 5 is read-only. No write-back path. Valuation (D6M-4) untouched.

## 13. Anti-score firewall extension

Unchanged, plus: no embedded coverage threshold, no coverage waiver, no
nullable field with multiple meanings, no late-bound derivation.

```text
PROHIBITED  MATERIAL_CHANGE  SIGNIFICANT_CHANGE  GOOD_CHANGE  BAD_CHANGE
            HEALTHY_CHANGE   ADOPTION_SUCCESS_CHANGE  IMPROVING  DETERIORATING
            COMPOSITE_SCORE  RANK  GRADE  RECOMMENDATION
            any numeric coverage sufficiency threshold on a ComparisonRule
```

## 14. Book 7 seam (v0.3)

A Book 7 `ResponseLink` may consume only a `ChangeObservation` whose
**complete derivation binding** is currently authoritative (grammar v0.3 §4,
nineteen checks). Full contract in
`CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.3.md`.

## 15. Accepted limitations

Unchanged from v0.2, plus: no new version mechanism for `MetricDefinition`
(mitigated by content-binding at ratification; a separate amendment would be
required for first-class versioning); no shared/versioned comparison-semantics
class (semantics are per-rule, embedded — extracting a shared class is a
future operator decision that would admit a third contract class).

## 16. Implementation exit gates

```text
G-1  Zero regressions: all accepted Book 6 tests still pass (1341)
G-2  Zero regressions: full CSIA suite still passes (2162)
G-3  Zero regressions: Sensor suite unchanged from its accepted baseline
     (2325 PASS / 14 FAIL / 4 SKIPPED; the 14 are the known canonical set)
G-4  Book 1–5 mutation count = 0; Sensor mutation count = 0
G-5  New amendment tests cover, each with a CONCRETE REAL TEST FUNCTION:
     comparability gates; zero-baseline fail-closed; missing baseline;
     missing post data; NOT_COMPARABLE; methodology-sensitivity
     non-averaging; no-Book2-promotion; no-state-emission; anti-score field
     absence; Book 7 read-only seam; COV-1..COV-12; CHG-1..CHG-8;
     METH-1..METH-5; the nineteen-check replay with each check individually
     falsifiable
G-6  Ruff PASS on the full Book 6/CSIA scope; mypy PASS on CSIA source
G-7  Traceability matrix regenerated; every new gate resolves to a concrete
     real test function
G-8  Anti-creep invariants AC-1..AC-16 verified mechanically
G-9  D6M-1..D6M-5 verified unchanged
G-10 Formal Book 6 re-acceptance with a new ACCEPTED_IMPLEMENTATION_ANCHOR
G-11 Only then: Book 7 plan ratification may proceed
```

**G-5 note:** each of the nineteen replay checks must be independently
falsifiable — a test that removes one dependency and observes authority decay
— not merely a test that the happy path passes.

## 17. Book 7 consequence (unchanged)

```text
BOOK_7_PLAN_RATIFICATION = BLOCKED_PENDING_BOOK6_AMENDMENT
BOOK_7_RATIFICATION_BLOCKER = BOOK6_COMPARISON_CONTRACT_NOT_YET_ACCEPTED
BOOK_7_PLAN = READY_PENDING_BOOK6_COMPARISON_AMENDMENT
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```

## 18. Plan status

```text
BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.2 = SUPERSEDED / NOT RATIFIABLE
BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN      = v0.3 DRAFT_PENDING_OPERATOR_RATIFICATION
PRE_RATIFICATION_REVIEW                      = v0.3 (40 / 40) — companion
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
NEXT = operator ratification review of this amendment plan v0.3
```

---

*End of plan v0.3. Draft; ratifies nothing; implements nothing; grants no
implementation authority.*
