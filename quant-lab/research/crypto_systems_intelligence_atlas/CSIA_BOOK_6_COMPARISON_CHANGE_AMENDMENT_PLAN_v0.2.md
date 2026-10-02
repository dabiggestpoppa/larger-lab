# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PLAN — v0.2

> **Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.1.md`
> (**preserved unmodified**, now `SUPERSEDED / NOT RATIFIABLE`).
> **Repairs incorporated:** `R6A-D1` coverage sufficiency,
> `R6A-D2` self-ratified derived record, D6M-3 governance-scope bleed. Audit
> in `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RECONCILIATION_v0.1.md`.
> **Governs:** `..._AMENDMENT_BOUNDARY_v0.1.md`,
> `..._COMPARISON_CHANGE_GRAMMAR_v0.2.md`,
> `..._TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.2.md`
> **Authority:** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Ratifies nothing. Implements nothing. Grants no implementation authority.**

---

## 1. Scope (unchanged from v0.1)

Add exactly two contract classes to Book 6 — `ComparisonRule` and
`ChangeObservation` — over measurements Book 6 already accepted.

```text
ADDED:     ComparisonRule, ChangeObservation, baseline-selection methodology
           family, comparability gate set (G7 repaired), numeric change
           semantics, coverage-sufficiency AUTHORITY CHAIN
UNCHANGED: MetricDefinition, MeasurementMethodology, MeasurementObservation,
           ValuationObservation, NormalizationRule, StateRule,
           FundamentalStateVector, all D6M decisions, all accepted tests
FORBIDDEN: any new state class; any score/rank/grade; any narrative or
           response concept; any Book 5 write-back; any Book 2 promotion;
           any embedded coverage threshold; any self-ratified object status
```

## 2. `ComparisonRule` (repaired)

Field set in grammar v0.2 §1. Governance:

```text
- versioned; canonical fingerprint over all semantic fields
- baseline_selection_methodology_ref REQUIRED — no implicit baseline
- comparison_methodology_ref REQUIRED
- compatible_methodology_refs is an explicit allow-list, never a wildcard
- NO NUMERIC COVERAGE THRESHOLD ON THIS OBJECT
- coverage_sufficiency_rule_ref — the accepted Book 6 coverage rule, when the
  metric class requires a verdict
- coverage_scope_requirements — structural scope only (which coverage
  dimensions, which rule scope)
- COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY, established BY THIS
  AMENDMENT using a pattern CONSISTENT WITH D6M-3. D6M-3 does not grant,
  extend, or lend this authority.
- REGISTRATION != RATIFICATION; OBJECT STATUS IS NOT AUTHORITY
- ratification bound to rule id + version + canonical fingerprint
- supersession does not inherit; callers re-resolve current authority
- BOOTSTRAP: COMPARISON_RULES_RATIFIED = 0 — no rule ships canonically active
```

## 3. `ChangeObservation` (repaired)

Field set in grammar v0.2 §3. Requirements:

```text
- Book 6-local derived record; NOT a Book 2 claim; no promotion path
- RATIFIED IS REMOVED from the derived-record vocabulary
- construction_status (CONSTRUCTED) is a workflow marker, not authority
- record_state ∈ {CURRENT, SUPERSEDED, WITHDRAWN, INVALIDATED} is a record
  lifecycle, NOT a Book 2 ClaimState and NOT an authority source
- current_authority ∈ {TRUE, FALSE} is DERIVED at use time by the eleven-check
  re-resolution, never asserted
- change_kind ∈ {INCREASE, DECREASE, NO_CHANGE, CHANGE_UNDEFINED,
                 NOT_COMPARABLE, INSUFFICIENT_DATA}
- coverage_observation is a NUMBER + BASIS, never a verdict
- coverage_verdict is the replayed result of a ratified rule, never asserted
- numeric fields ABSENT when undefined; absence is never 0
- every emitted value reproducible from cited refs + cited rule version
- bitemporal; corrections supersede, never overwrite
- no event, action, response, window, causality, health, or merit field
```

## 4. Coverage doctrine (restored)

```text
COVERAGE_OBSERVATION != COVERAGE_SUFFICIENCY_RULE
```

A `ComparisonRule` may state that coverage must be assessed, which
dimensions are relevant, and which rule scope is required. It may not define
numeric sufficiency. The five-step chain:

```text
CoverageObservation
→ ratified CoverageSufficiencyRule (registry/ledger, not object status)
→ scope match against metric definition + coverage dimensions
→ deterministic sufficiency verdict
→ ComparisonRule may pass gate G7
```

```text
NO RAW NUMBER → VERDICT SHORTCUT
NO GLOBAL FLOOR — no default threshold now or later absent a separately
  ratified global floor rule
```

### 4.1 Zero-rule bootstrap

```text
CANONICAL_COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
CANONICAL_COMPARISON_RULES_RATIFIED          = 0

⇒ A ComparisonRule requiring a coverage verdict is UNUSABLE until such a rule
  is separately ratified.

COMPARISON_RULE_RATIFICATION != COVERAGE_RULE_RATIFICATION
```

Correct fail-closed behaviour. The amendment auto-ratifies no coverage rule,
ships no default, and relaxes no gate.

## 5. Baseline methodology (unchanged)

Four candidate families, **no universal default**. `selection_methodology_ref`
mandatory. `BASELINE_UNAVAILABLE` is a first-class outcome. Book 6 receives
the requested valid-time window as *context* and never learns why.

## 6. Comparability (G7 repaired)

Nine gates; any failure → `NOT_COMPARABLE` with both numeric fields absent.

```text
G7 (v0.1): coverage valid for the rule's minimum          ← DEFECTIVE
G7 (v0.2): coverage verdict obtained via the §4 chain and
           SUFFICIENT; absent/unratified/out-of-scope/superseded/failed
           → NOT_COMPARABLE. A self-declared number is never a verdict.
```

`COMPARABLE != CHANGED`. Book 6 remains the sole normalization authority
(D6M-2).

## 7. Missingness (unchanged, with coverage now precise)

```text
BASELINE_UNAVAILABLE      → INSUFFICIENT_DATA, no delta
POST_DATA_UNAVAILABLE     → INSUFFICIENT_DATA, no delta
COVERAGE_SUFFICIENCY_UNKNOWN → NOT_COMPARABLE (no ratified rule)
COVERAGE_INSUFFICIENT     → NOT_COMPARABLE (ratified rule says insufficient)
COVERAGE_RULE_SUPERSEDED  → current authority decays; record preserved
NO_CHANGE_OBSERVED        → a valid change_kind; NOT a negative response
```

`NO CHANGE` ≠ `NO DATA`; `ZERO_VALUE` ≠ `ZERO_CHANGE`.

## 8. Numeric change (unchanged)

```text
absolute_delta = comparison_value - baseline_value
relative_delta = (comparison_value - baseline_value) / baseline_value
```

Zero baseline → relative delta **absent, fail-closed** (never 0/inf/NaN).
Absent for missing baseline, missing comparison observation, incompatible
unit, invalid coverage / missingness / temporal order. No hidden currency
conversion. Absent field ≠ 0.

## 9. D6M compatibility (clarified, still zero amendments)

| Decision | Status under this amendment |
|---|---|
| D6M-1 (measurement-object authority) | unaffected — `ChangeObservation` is Book 6-local derived, like `NormalizationRule` output |
| D6M-2 (normalization separate) | unaffected — comparison performs no normalization |
| D6M-3 (state-rule governance) | unaffected — **no new state class**; comparison-rule governance is established by this amendment using a D6M-3-*consistent* pattern. **No authority is inherited from D6M-3**, and D6M-3 is neither extended nor reinterpreted. |
| D6M-4 (valuation authority) | unaffected — explicit numeraire, Book 2 price provenance, no global price source. Valuation may read a `ChangeObservation`; comparison gains no valuation authority. |
| D6M-5 (usage / health) | unaffected and still `OPEN_DEFERRED` — a change record is not a health, adoption, or usage-sufficiency reading |

**No D6M amendment is required. No prior decision is silently expanded.**

## 10. Book 5 / valuation non-impact (unchanged)

Book 5 is read-only. No write-back path into Book 5 economic records, native
quantities, or principal topology. Valuation (D6M-4) untouched.

## 11. Anti-score firewall extension (unchanged, plus coverage verdict)

```text
PROHIBITED  MATERIAL_CHANGE  SIGNIFICANT_CHANGE  GOOD_CHANGE  BAD_CHANGE
            HEALTHY_CHANGE   ADOPTION_SUCCESS_CHANGE  IMPROVING  DETERIORATING
            COMPOSITE_SCORE  RANK  GRADE  RECOMMENDATION
            any numeric coverage sufficiency threshold on a ComparisonRule
```

## 12. Book 7 seam (v0.2)

`ChangeObservation` → Book 7 `ResponseLink`, with the repaired condition:
Book 7 may consume **only a `CURRENTLY AUTHORITATIVE` `ChangeObservation`**,
never one merely carrying a self-declared status. Full contract in
`CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.2.md`.

## 13. Accepted limitations (unchanged)

```text
offline deterministic kernel only; no live acquisition; no RPC; no network
collectors; no CEX feeds; no persistent DB; no graph DB; no production
scheduler; no dashboard; no Book 7; no Book 8; no D8; no historical Book 2
point-in-time authority replay; no canonical Class B StateRule ratified; no
Class C rule semantics; no canonical ComparisonRule ratified; no canonical
CoverageSufficiencyRule ratified; no usage/health empirical research; no
trading or execution authority; no materiality methodology; no causal
inference.
```

## 14. Implementation exit gates (extended)

```text
G-1  Zero regressions: all accepted Book 6 tests still pass (1341)
G-2  Zero regressions: full CSIA suite still passes (2162)
G-3  Zero regressions: Sensor suite unchanged from its accepted baseline
     (2325 PASS / 14 FAIL / 4 SKIPPED; the 14 are the known canonical set)
G-4  Book 1–5 mutation count = 0; Sensor mutation count = 0
G-5  New amendment tests cover: comparability gates; zero-baseline
     fail-closed; missing baseline; missing post data; NOT_COMPARABLE;
     methodology-sensitivity non-averaging; no-Book2-promotion;
     no-state-emission; anti-score field absence; Book 7 read-only seam;
     COV-1..COV-8; CHG-1..CHG-8
G-6  Ruff PASS on the full Book 6/CSIA scope; mypy PASS on CSIA source
G-7  Traceability matrix regenerated from executable traceability; every new
     gate resolves to a concrete real test function
G-8  Anti-creep invariants AC-1..AC-10 verified mechanically
G-9  D6M-1..D6M-5 verified unchanged
G-10 Formal Book 6 re-acceptance with a new ACCEPTED_IMPLEMENTATION_ANCHOR
G-11 Only then: Book 7 plan ratification may proceed
```

**G-5 extended for this revision:** all sixteen new adversarial cases
(`COV-1..8`, `CHG-1..8`) must have concrete real test functions, and each must
be traceable in the regenerated matrix. A pass on the aggregate is not a
substitute for a pass on each case.

## 15. Book 7 consequence (unchanged)

```text
BOOK_7_PLAN_RATIFICATION = BLOCKED_PENDING_BOOK6_AMENDMENT
BOOK_7_RATIFICATION_BLOCKER = BOOK6_COMPARISON_CONTRACT_NOT_YET_ACCEPTED
BOOK_7_PLAN = READY_PENDING_BOOK6_COMPARISON_AMENDMENT
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```

Book 7 has no local fallback and does not degrade to "post-action observation
implies response". Its response rung stays fail-closed at
`CHANGE_NOT_MEASURABLE`.

## 16. Plan status

```text
BOOK_6_AMENDMENT_PLAN_v0.1 = SUPERSEDED / NOT RATIFIABLE
BOOK_6_AMENDMENT_PLAN      = v0.2 DRAFT_PENDING_OPERATOR_RATIFICATION
PRE_RATIFICATION_REVIEW    = v0.2 (30 / 30 PASS) — companion artifact
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
NEXT = operator ratification review of this amendment plan v0.2
```

---

*End of plan v0.2. Draft; ratifies nothing; implements nothing; grants no
implementation authority.*
