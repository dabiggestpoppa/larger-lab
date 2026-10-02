# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PLAN — v0.4

> **Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.3.md`
> (**preserved unmodified**, now `SUPERSEDED / NOT RATIFIABLE`); v0.1, v0.2
> preserved.
> **Repairs:** Class A (nullable/absent multi-meaning) and Class B
> (rule-author policy with open or authority-bearing domains).
> **Governs:** `..._BOUNDARY_v0.3.md`, `..._GRAMMAR_v0.4.md`,
> `..._SEAM_v0.4.md`
> **Ratifies nothing. Implements nothing. Grants no implementation authority.**

---

## 1. Repair result

```text
AC_17_SINGLE_MEANING_ABSENCE  = SATISFIED
AC_18_POLICY_NOT_AUTHORITY     = SATISFIED
AC_18a_NO_OPEN_POLICY_DOMAINS  = SATISFIED
AC_18b_DERIVED_OVER_CHOSEN     = SATISFIED
AMBIGUOUS_NULLABLE_FIELDS      = 0
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY = 0
FREE_STRING_POLICY_AUTHORITY   = 0
ARBITRARY_NUMERIC_THRESHOLD_PARAMETERS = 0
ROUNDING_AFFECTS_CHANGE_CLASSIFICATION = FALSE
NO_CHANGE_IS_MATERIALITY       = FALSE
```

## 2. Scope (unchanged; count remains 2)

```text
ADDED:     ComparisonRule, ChangeObservation
REUSED:    accepted benchmark-rule namespace; accepted coverage-sufficiency
           rules
REMOVED:   the comparison_semantics policy section (direction derivation,
           zero-baseline policy, unit divisibility, rounding precision)
UNCHANGED: MetricDefinition, MeasurementMethodology, MeasurementObservation,
           ValuationObservation, NormalizationRule, StateRule,
           FundamentalStateVector, all D6M decisions, all accepted tests
```

## 3. The five repairs, in plan terms

| # | v0.3 problem | v0.4 resolution |
|---|---|---|
| 1 | `delta_formula_basis` free-text (`e.g. post − baseline`) | closed operator set: `ABSOLUTE_DELTA` \| `RELATIVE_DELTA`; availability derived from arithmetic, never chosen; new operators require a contract version, not a string |
| 2 | `direction_derivation` open policy | **REMOVED.** Direction = sign of the canonical **unrounded** absolute delta. Not display, not relative magnitude, not tolerance |
| 3 | `zero_baseline_policy` open policy | **REMOVED.** Fixed fail-closed: absolute delta normal, relative delta `UNDEFINED`/`ABSENT`. Never 0, inf, NaN, capped, or percentage |
| 4 | `unit_divisibility_policy` open policy | **REMOVED.** Derived from the accepted typed unit contract; a rule may cite requirements, never redefine mathematics |
| 5 | `rounding_precision_policy` in the fingerprint | **REMOVED** from authority. Presentation-only `display_metadata`, outside every derivation, fingerprint, and authority check |

Plus the five nullable repairs (`R-2`..`R-5`):

| # | field | v0.4 single meaning |
|---|---|---|
| R-2 | `coverage_applicability_source_ref` | absent = `NO_UPSTREAM_DETERMINATION_EXISTS` only; required when status ∈ {REQUIRED, NOT_APPLICABLE} |
| R-3 | `coverage_observation` | split into `coverage_observation_state` ∈ {PRESENT, UNAVAILABLE, NOT_APPLICABLE} + a ref required iff PRESENT |
| R-4 | seam coverage quotes | mandatory when the source record carries the field; silence about known coverage is INVALID |
| R-5 | `supersedes` | `version == 1` → absent; `version > 1` → required, else rejected |
| R-5 | `valid_time.valid_to` | absent = open-ended / still valid until superseded or withdrawn, and nothing else |

## 4. Canonical arithmetic (new, fixed)

```text
ABSOLUTE_DELTA = comparison_value - baseline_value
RELATIVE_DELTA = (comparison_value - baseline_value) / baseline_value
                 where semantically valid

direction  = SIGN(canonical UNROUNDED absolute_delta)
change_kind derived from direction; NO_CHANGE = exact canonical equality
```

```text
All calculations use the accepted canonical numeric representation.
Display precision never enters any derivation, comparison, coverage verdict,
comparability decision, or authority check.

DISPLAYED EQUALITY != MEASURED EQUALITY
```

## 5. Materiality / tolerance firewall (new, explicit)

```text
NO epsilon field.  NO tolerance field.  NO materiality field.
NO significance field.  NO "negligible" field.

NO_CHANGE means EXACT CANONICAL EQUALITY and nothing else.

NO_CHANGE != NOT_MATERIAL_CHANGE

Any tolerance, materiality, or significance concept requires SEPARATE future
governance — a distinct methodology, separately operator-ratified, exactly as
a coverage-sufficiency rule is. It is not a comparison-rule parameter.
```

This is the repair with the most reach. In v0.3 an unconstrained rounding
value could express "differences below X are not a change" — a significance
threshold through a parameter the anti-score firewall did not name. In v0.4
there is no field through which any such threshold can be expressed.

## 6. Baseline methodology (unchanged)

Four families mapped onto the **accepted** benchmark namespace, **no
universal default**, cited with identity + version + fingerprint, re-resolved
at use time. `BASELINE_UNAVAILABLE` is a first-class outcome.

## 7. Comparability (unchanged; G7 on derived applicability)

Nine gates, any failure → `NOT_COMPARABLE` with both numeric fields absent.
`UNRESOLVED` applicability blocks the comparison outright.
`COMPARABLE != CHANGED`. Book 6 remains the sole normalization authority.

## 8. Missingness (unchanged, with the new discriminator)

```text
BASELINE_UNAVAILABLE          → INSUFFICIENT_DATA, no delta
POST_DATA_UNAVAILABLE         → INSUFFICIENT_DATA, no delta
COVERAGE_SUFFICIENCY_UNKNOWN  → NOT_COMPARABLE
COVERAGE_INSUFFICIENT         → NOT_COMPARABLE
COVERAGE_OBSERVATION_UNAVAILABLE → NOT_COMPARABLE (state = UNAVAILABLE)
COVERAGE_APPLICABILITY_UNRESOLVED  → COMPARISON UNAVAILABLE (fail closed)
NO_CHANGE_OBSERVED            → exact canonical equality; NOT a negative
                                 response, NOT a materiality judgment
```

## 9. D6M compatibility (unchanged)

| Decision | Status |
|---|---|
| D6M-1 | unaffected — `ChangeObservation` is Book 6-local derived |
| D6M-2 | unaffected — no normalization in comparison; canonical arithmetic is now fixed so none can be smuggled in |
| D6M-3 | unaffected — no new state class. Comparison-rule ratification authority established **by this amendment** using a D6M-3-*consistent* pattern; **no authority inherited**. The accepted benchmark namespace is reused under D6M-3's existing individual-ratification rule, unmodified |
| D6M-4 | unaffected — valuation authority untouched |
| D6M-5 | unaffected and still `OPEN_DEFERRED` |

**No D6M amendment required. No prior decision silently expanded.**

## 10. Book 5 / valuation non-impact (unchanged)

Book 5 is read-only. No write-back path. Valuation (D6M-4) untouched.

## 11. Anti-score firewall (extended)

```text
PROHIBITED  MATERIAL_CHANGE  SIGNIFICANT_CHANGE  GOOD_CHANGE  BAD_CHANGE
            HEALTHY_CHANGE   ADOPTION_SUCCESS_CHANGE  IMPROVING  DETERIORATING
            COMPOSITE_SCORE  RANK  GRADE  RECOMMENDATION
            any numeric coverage sufficiency threshold on a ComparisonRule
            any tolerance / epsilon / materiality / significance field
            any custom arithmetic or expression language
```

## 12. Book 7 seam (v0.4)

Coverage propagation mandatory; nineteen-check derivation binding required;
no Book 7 local comparison; no omitted coverage context. Full contract in
`CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.4.md`.

## 13. Accepted limitations (unchanged, plus)

```text
offline deterministic kernel only; no live acquisition; no RPC; no network
collectors; no CEX feeds; no persistent DB; no graph DB; no production
scheduler; no dashboard; no Book 7; no Book 8; no D8; no historical Book 2
point-in-time authority replay; no canonical Class B StateRule ratified; no
Class C rule semantics; no canonical ComparisonRule ratified; no canonical
coverage-sufficiency rule ratified; no canonical benchmark rule ratified; no
usage/health empirical research; no trading or execution authority; no
materiality methodology; no tolerance concept; no causal inference; no
first-class MetricDefinition versioning (content-bound at ratification
instead); no shared versioned comparison-semantics class (semantics are now
fixed law, so the question no longer arises).
```

The last item is worth noting: because v0.4 **deleted** the
`comparison_semantics` section rather than embedding it, the v0.3 limitation
"comparison semantics are per-rule rather than shared" is **resolved rather
than deferred**. Direction, zero-baseline, unit validity, and precision are no
longer per-rule at all.

## 14. Implementation exit gates

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
     absence; Book 7 read-only seam;
     COV-1..COV-12; CHG-1..CHG-8; METH-1..METH-5;
     NULL-1..NULL-9; POL-1..POL-11;
     the nineteen replay checks, each independently falsifiable;
     the fixed direction/zero-baseline/unit laws (no field exists to vary);
     display-independence (rounding cannot change any outcome)
G-6  Ruff PASS on the full Book 6/CSIA scope; mypy PASS on CSIA source
G-7  Traceability matrix regenerated; every new gate resolves to a concrete
     real test function
G-8  Anti-creep invariants AC-1..AC-20 verified mechanically
G-9  D6M-1..D6M-5 verified unchanged
G-10 Formal Book 6 re-acceptance with a new ACCEPTED_IMPLEMENTATION_ANCHOR
G-11 Only then: Book 7 plan ratification may proceed
```

**G-5 note on the fixed laws:** because direction, zero-baseline, and unit
validity are now *fixed* rather than configurable, their tests are negative
tests — asserting that no such field exists on the model and that no
constructor argument can introduce one. That is a stronger guarantee than a
test enumerating permitted values, and it is why `POL-8`/`POL-9`/`POL-10`/
`POL-11` are all rejection cases rather than enumeration cases.

## 15. Book 7 consequence (unchanged)

```text
BOOK_7_PLAN_RATIFICATION = BLOCKED_PENDING_BOOK6_AMENDMENT
BOOK_7_RATIFICATION_BLOCKER = BOOK6_COMPARISON_CONTRACT_NOT_YET_ACCEPTED
BOOK_7_PLAN = READY_PENDING_BOOK6_COMPARISON_AMENDMENT
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```

## 16. Plan status

```text
BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.3 = SUPERSEDED / NOT RATIFIABLE
BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN      = v0.4 DRAFT_PENDING_OPERATOR_RATIFICATION
PRE_RATIFICATION_REVIEW                      = v0.5 (48 / 48) — companion
RATIFICATION_READINESS                       = see readiness v0.3
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

---

*End of plan v0.4. Draft; ratifies nothing; implements nothing; grants no
implementation authority.*
