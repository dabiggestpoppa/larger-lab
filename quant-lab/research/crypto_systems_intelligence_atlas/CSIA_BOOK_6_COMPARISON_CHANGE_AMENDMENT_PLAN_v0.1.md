# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PLAN — v0.1

> **Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
> **Date:** 2026-10-01
> **Book:** 6 — FUNDAMENTAL MEASUREMENT AND STATE MODELING (amended)
> **Triggered by:** `D7N-7 = A` (`CHANGE_COMPARISON_OWNER = BOOK_6`)
> **Governs:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.1.md`,
> `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md`,
> `CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.1.md`
> **Authority:** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **This plan ratifies nothing and implements nothing.**

---

## 1. Scope

Add exactly two contract classes to Book 6 — `ComparisonRule` and
`ChangeObservation` — plus the methodology and gate machinery they require.
Nothing else in Book 6 changes.

```text
ADDED:     ComparisonRule, ChangeObservation, baseline-selection methodology
           family, comparability gate set, numeric change semantics
UNCHANGED: MetricDefinition, MeasurementMethodology, MeasurementObservation,
           ValuationObservation, NormalizationRule, StateRule,
           FundamentalStateVector, all D6M decisions, all accepted tests
FORBIDDEN: any new state class, any score/rank/grade, any narrative or
           response concept, any Book 5 write-back, any Book 2 promotion
```

## 2. `ComparisonRule`

Full field set in the grammar §2. Governance requirements:

```text
- versioned; content fingerprint over all semantic fields (Book 6 doctrine)
- baseline_selection_methodology_ref REQUIRED — no implicit baseline
- comparison_methodology_ref REQUIRED
- compatible_methodology_refs is an explicit allow-list, never a wildcard
- centralized operator ratification only (D6M-3 = A pattern); no self-authoring
- supersession does not inherit; callers re-resolve current authority
- status lifecycle: DRAFT | RATIFIED | SUPERSEDED | WITHDRAWN
- bootstrap canonical count = 0
```

## 3. `ChangeObservation`

Full field set in the grammar §3. Requirements:

```text
- Book 6-local derived record; NOT a Book 2 claim; no promotion path
- change_kind ∈ {INCREASE, DECREASE, NO_CHANGE, CHANGE_UNDEFINED,
                 NOT_COMPARABLE, INSUFFICIENT_DATA}
- numeric fields ABSENT when undefined; absence is never 0
- every emitted value reproducible from cited refs + cited rule version
- bitemporal; corrections supersede, never overwrite
- no event, action, response, window, causality, health, or merit field
```

## 4. Baseline methodology

Four candidate families, **no universal default** (grammar §4.1). The
selected family and its selection methodology are cited on every record. When
no valid baseline exists, the outcome is `BASELINE_UNAVAILABLE` — never a
substituted value, never "the last value we have".

Book 6 may receive the requested valid-time window as **context**. It must
not learn why the window was chosen, and it must never receive narrative,
event, or causal semantics.

## 5. Comparability

Nine gates (grammar §5), all must pass, any failure → `NOT_COMPARABLE` and no
delta. Book 6 remains the sole normalization authority (D6M-2); comparison
consumes already-valid values and performs no normalization of its own.

```text
COMPARABLE != CHANGED — passing the gates authorises a comparison, not a finding
```

## 6. Missingness

```text
BASELINE_UNAVAILABLE      → INSUFFICIENT_DATA, no delta
POST_DATA_UNAVAILABLE     → INSUFFICIENT_DATA, no delta
TOO_EARLY (Book 7 window) → TOO_EARLY_TO_ASSESS (Book 7 side)
COVERAGE_INVALID          → NOT_COMPARABLE
MISSINGNESS_INVALID       → NOT_COMPARABLE
NO_CHANGE_OBSERVED        → a valid change_kind; NOT a negative response
```

`NO CHANGE` and `NO DATA` remain strictly distinct. `ZERO_VALUE` and
`ZERO_CHANGE` remain strictly distinct.

## 7. Numeric change

```text
absolute_delta = comparison_value - baseline_value
relative_delta = (comparison_value - baseline_value) / baseline_value
```

Absent (fail-closed) for: zero baseline (relative only), missing baseline,
missing comparison observation, incompatible unit, invalid coverage,
invalid missingness, invalid temporal order. No hidden currency conversion.
No `NaN`, no `inf`, no silent zero.

## 8. Methodology sensitivity

Parallel `ChangeObservation` records from different legitimate
`ComparisonRule` versions are preserved side by side. Never averaged, never
silently selected, never reconciled. Every downstream consumer (including
each Book 7 `ResponseLink`) must cite the exact record and rule it relied on.

## 9. D6M compatibility

| Decision | Status under this amendment |
|---|---|
| D6M-1 (measurement-object authority) | unaffected — `ChangeObservation` is Book 6-local derived, like `NormalizationRule` output |
| D6M-2 (normalization separate) | unaffected — comparison performs no normalization |
| D6M-3 (state-rule governance, centralized operator ratification) | unaffected — no new state class; the comparison-rule ratification pattern mirrors but does not extend D6M-3 |
| D6M-4 (valuation authority) | unaffected — explicit numeraire and Book 2 price-provenance requirements unchanged; valuation may consume `ChangeObservation` as a read-only input but gains no authority |
| D6M-5 (usage / health) | unaffected and still `OPEN_DEFERRED` — a change record is not a health, adoption, or usage-sufficiency reading |

**No D6M amendment is required. No prior decision is silently expanded.**

## 10. Book 5 / valuation non-impact

Book 5 is read-only. The amendment adds no write-back path into Book 5
economic records, native quantities, or principal topology. Valuation
(D6M-4) is untouched: no new price source, no global price authority, no
change in the explicit-numeraire requirement. A valuation observation may
later reference a `ChangeObservation`, but comparison does not reach into
valuation and valuation does not gain comparison authority.

## 11. Anti-score firewall extension

The accepted Book 6 firewall (no `overall_score`, `quality_score`, `rating`,
`grade`, `rank`, `weighted_total`, `buy`, `sell`, `attractive`,
`undervalued`, `overvalued`, `top_tier`, `healthy`) is extended to the two
new contracts. Prohibited by construction:

```text
MATERIAL_CHANGE  SIGNIFICANT_CHANGE  GOOD_CHANGE  BAD_CHANGE
HEALTHY_CHANGE   ADOPTION_SUCCESS_CHANGE  IMPROVING  DETERIORATING
COMPOSITE_SCORE  RANK  GRADE  RECOMMENDATION
```

`CHANGE_UNDEFINED` and `NOT_COMPARABLE` are the honest outcomes when a
materiality question is asked; they are not a licence to add a materiality
field later without its own operator decision.

## 12. Book 7 seam

`ChangeObservation` → Book 7 `ResponseLink` (seam artifact §3–§5). Book 7
may assess whether an accepted change falls inside a declared response
window. Book 7 may not modify delta, direction, comparability, baseline, or
measurement methodology. There is no reverse channel.

## 13. Accepted limitations

```text
offline deterministic kernel only; no live acquisition; no RPC; no network
collectors; no CEX feeds; no persistent DB; no graph DB; no production
scheduler; no dashboard; no Book 7; no Book 8; no D8; no historical Book 2
point-in-time authority replay; no canonical Class B StateRule ratified; no
Class C rule semantics; no usage/health empirical research; no trading or
execution authority; no materiality methodology; no causal inference.
```

## 14. Implementation exit gates

**None of these are performed in this session.** They are the criteria a
future authorized implementation must meet.

```text
G-1  Zero regressions: all accepted Book 6 tests still pass (1341)
G-2  Zero regressions: full CSIA suite still passes (2162)
G-3  Zero regressions: Sensor suite unchanged from its accepted baseline
     (2325 PASS / 14 FAIL / 4 SKIPPED; the 14 are the known canonical set)
G-4  Book 1–5 mutation count = 0; Sensor mutation count = 0
G-5  New amendment tests cover: comparability gates, zero-baseline
     fail-closed, missing-baseline, missing-post-data, NOT_COMPARABLE,
     methodology-sensitivity non-averaging, no-Book2-promotion,
     no-state-emission, anti-score field absence, Book 7 read-only seam
G-6  Ruff PASS on the full Book 6/CSIA scope; mypy PASS on CSIA source
G-7  Traceability matrix regenerated from executable traceability; every new
     gate resolves to a concrete real test function
G-8  Anti-creep invariants AC-1..AC-10 verified mechanically
G-9  D6M-1..D6M-5 verified unchanged
G-10 Formal Book 6 re-acceptance with a new ACCEPTED_IMPLEMENTATION_ANCHOR
G-11 Only then: Book 7 plan ratification may proceed
```

## 15. Book 7 consequence

```text
BOOK_7_PLAN_RATIFICATION = BLOCKED_PENDING_BOOK6_AMENDMENT
BOOK_7_RATIFICATION_BLOCKER = BOOK6_COMPARISON_CONTRACT_NOT_YET_ACCEPTED
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_PLAN_v0.2 = structurally ready, 45/45 pre-ratification PASS, NOT ratified
```

Book 7 has no local fallback. It does not compute comparisons, and it does not
degrade to "post-action observation implies response" — the defect this whole
amendment chain exists to close. Until the comparison contract is accepted,
Book 7's response rung stays fail-closed at `CHANGE_NOT_MEASURABLE`.

## 16. Plan status

```text
BOOK_6_AMENDMENT_PLAN = v0.1 DRAFT_PENDING_OPERATOR_RATIFICATION
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
NEXT = operator review / ratification of this narrow amendment
```

---

*End of plan. Draft; ratifies nothing; implements nothing.*
