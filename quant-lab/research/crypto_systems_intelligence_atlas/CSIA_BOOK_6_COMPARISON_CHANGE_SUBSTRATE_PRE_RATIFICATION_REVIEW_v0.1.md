# CSIA — BOOK 6 COMPARISON / CHANGE SUBSTRATE PRE-RATIFICATION REVIEW — v0.1

**Document ID:** CSIA-B6-SPR-001
**Version:** 0.1
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Kind:** PRE-RATIFICATION ADVERSARIAL REVIEW (20 mandatory questions)
**Subject:** substrate clarification v0.1, grammar v0.5, plan v0.5, test spec v0.2

**This review authorizes nothing.** It records whether the four gap resolutions
can be ratified without smuggling an unr ratified policy.

---

# 1. Verdict

```text
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_PRE_RATIFICATION_REVIEW = PASS
SCORE = 20 / 20
```

Each question is answered with a required answer and a verdict, then evidenced.
Every evidence anchor is a file and line in the **accepted** implementation
branch `agent/crypto-systems-intelligence-atlas-book6-build` @ `5f94c3f4`.

---

# 2. The twenty questions

## Q1 — Does 1A change `MeasurementObservation.value` type? **Required NO.**

**NO.** `1A-STRICT` explicitly retains binary64 storage.
`MeasurementObservation.value: float | None = None` at `book6_records.py:113` is
unchanged. The resolution is a doctrine-precision fix: it *defines* what the
existing `float` means rather than migrating it. Substrate clarification v0.1
§1.3 states `MeasurementObservation.value public type change = NOT PERMITTED`.

## Q2 — Does exact equality claim mathematical real-number exactness? **Required NO.**

**NO.** `CANONICAL_EQUALITY` is defined as exact equality of stored canonical
binary64 values (§1.3), and `REAL_NUMBER_EXACTNESS_CLAIM = FALSE` is asserted
explicitly. Grammar v0.5 §1.0.1 states a canonical value is "not the exact
mathematical real number prior to representation". Test NUM-2 (0.1+0.2 vs 0.3
unequal) is the falsifying case.

## Q3 — Can NaN/Inf enter comparison arithmetic? **Required NO.**

**NO.** `FINITE_NUMERIC_INPUT_REQUIRED = TRUE`. `math.isfinite()` rejects
`NaN`/`±Inf` at the validated-input boundary before any delta computation
(grammar v0.5 §1.0.3). The Book 6 core ratio NaN sentinel (`book6_core.py:181`)
is explicitly **not inherited** (§1.0.3, §2.3). Tests NUM-3/4/5 cover all three
non-finite members.

## Q4 — Does 2D require a new dimensional ontology? **Required NO.**

**NO.** 2D requires only that `MetricDefinition.unit` (non-nullable,
`book6_definitions.py:148`) equal each observation's `unit`
(`book6_records.py:114`). It adds no dimension vector, no compatibility matrix,
no taxonomy. `UNIT_CONTRACT_CLASS_ADDED = FALSE` (§4.7).

## Q5 — Can unit conversion occur? **Required NO.**

**NO.** §4.4 prohibits conversion, aliases, dimensional inference, normalization
and token conversion. A unit or metric mismatch yields
`comparability_status = NOT_COMPARABLE` (§4.6) — never a conversion, never a
repair. Test UNIT-4 asserts the delta stage is never reached on mismatch.

## Q6 — Does same-metric exact-unit identity fully determine arithmetic validity? **Required YES.**

**YES**, for this amendment's scope. A `ComparisonRule` is single-metric
temporal. If both observations resolve to the bound metric and both carry
`MetricDefinition.unit`, the operands are the same unit by construction, so
subtraction is valid and the ratio is dimensionless. No other unit relation is
reachable in a single-metric temporal comparison, so no additional unit law is
needed. (A cross-metric comparison would need more — but that is a different
engine, governed by the unchanged cross-metric corpus.)

## Q7 — Does absence of a coverage rule imply NOT_APPLICABLE? **Required NO.**

**NO.** Grammar v0.5 §2.1: absence yields `UNRESOLVED` with
`coverage_applicability_source_ref` ABSENT, single meaning
`NO_UPSTREAM_DETERMINATION_EXISTS`. `CAN_DERIVE_NOT_APPLICABLE = FALSE` (§2.1,
clarification §5.5). Test CAPP-6 asserts NOT_APPLICABLE is unreachable.

## Q8 — Does a current ratified exact-metric coverage rule imply REQUIRED? **Required YES.**

**YES.** The 3C derivation (§2.1) reads `CoverageRuleRegistry` through
`rules_for_metric()` + `ratification_of()` + `authorize()`. A rule that is
registered, currently ratified, and exact-metric-scoped yields
`coverage_requirement_status = REQUIRED`. Test CAPP-2 exercises this with a
synthetic non-canonical rule.

## Q9 — Can an unratified/wrong-scope/superseded coverage rule imply REQUIRED? **Required NO.**

**NO.** `CoverageRuleRegistry.authorize` already refuses all three: unregistered,
missing current ratification, and scope mismatch. Every refusal maps to
`UNRESOLVED`, never `REQUIRED`. Tests CAPP-3 (unratified), CAPP-4 (wrong scope),
CAPP-5 (superseded).

## Q10 — Can NOT_APPLICABLE be invented? **Required NO.**

**NO.** `NOT_APPLICABLE` is not derivable by absence (Q7), and no derivation
path in grammar v0.5 produces it. `TemporalComparabilityStatus` has no
`NOT_APPLICABLE` member (§8.3 `NOT_APPLICABLE_MEMBER = ABSENT`). Emitting it
requires a future separately-ratified doctrine, which does not exist.

## Q11 — Is temporal comparability distinct from the cross-metric corpus? **Required YES.**

**YES.** `TemporalComparabilityStatus` (3 members) is not `CorpusVerdict` (3
different members), not `ComparabilityClass` (6 members), not `StateName`, not
`ClaimState`. The corpus is cross-metric-pair scoped; the temporal engine is
single-metric. Test TCMP-7 asserts `book6_comparability` is never consulted and
FC-01..FC-15 are unchanged.

## Q12 — Is comparability_status closed and typed? **Required YES.**

**YES.** Grammar v0.5 §3.1 defines the field's domain as the closed 3-member
`TemporalComparabilityStatus`. `CLOSED_DOMAIN = TRUE` (§8.3). The ratified v0.4
listed the field REQUIRED with no domain; that is precisely the GAP-4 defect and
it is closed.

## Q13 — Does NOT_COMPARABLE have a producing check? **Required YES.**

**YES.** New replay check **19** (temporal comparability resolution) derives it
deterministically and emits the specific failed gate. The ratified v0.4 had no
producing check for `NOT_COMPARABLE` (the GAP-4 defect). §5.1, test CHK-19.

## Q14 — Is UNRESOLVED distinct from NOT_COMPARABLE? **Required YES.**

**YES.** §3.3–§3.4 and grammar v0.5: `NOT_COMPARABLE` = an explicit structural
requirement **failed**; `UNRESOLVED` = insufficient authoritative basis to
decide. `UNRESOLVED_MAPPED_TO_NOT_COMPARABLE = FORBIDDEN`. Test TCMP-6 asserts
the mapping is unreachable.

## Q15 — Is deterministic recomputation now check 20? **Required YES.**

**YES.** Grammar v0.5 §5: check 19 = temporal comparability resolution (NEW);
check 20 = deterministic recomputation (was v0.4 check 19). Ordering is
normative — recomputation does not run unless comparability is `COMPARABLE`.

## Q16 — Are all 20 checks independently falsifiable? **Required YES.**

**YES.** Each check has at least one named negative test making it fail alone.
Checks 19 and 20 are **separable**: check 19 can pass while check 20 fails
(recomputed delta disagrees), and check 19 can refuse so check 20 never runs.
Test spec v0.2 CHK-19/CHK-20.

## Q17 — Does contract count remain exactly 2 new public authority-bearing classes? **Required YES.**

**YES.** Grammar v0.5 §10 and plan v0.5 §4: `ComparisonRule` and
`ChangeObservation` only. The binary64 clarification, same-metric unit law,
coverage resolver, `TemporalComparabilityStatus` enum, and 20-check replay are
each explicitly **not** new public contract classes (none adds a registry or its
own ratification). `HIDDEN_THIRD_CONTRACT = NONE`.

## Q18 — Does any resolution require Books 1–5 mutation? **Required NO.**

**NO.** Every resolution operates on Book 6-local state: existing
`MeasurementObservation`/`MetricDefinition` fields, the existing
`CoverageRuleRegistry`, and new Book 6 comparison/change modules. Book 1–5 code
is read-only input. Gate G-4 requires Book 1–5 mutation count = 0.

## Q19 — Does any resolution authorize implementation? **Required NO.**

**NO.** All four successor artifacts are `DRAFT_PENDING_OPERATOR_RATIFICATION`.
`BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`. Ratifying the clarification would
authorize creating grammar v0.5 and plan v0.5, not writing code.

## Q20 — Are all previously blocked test families now specifiable without invention? **Required YES.**

**YES.** All 14 v0.1 blocked cases are mapped to resolved semantics (test spec
v0.2 §6). No blocked case requires inventing a policy, an absent state, or a
contract. `BLOCKED_REMAINING = 0`.

---

# 3. Score

```text
Q1  .. Q20  = 20 PASS / 0 FAIL
SCORE        = 20 / 20
VERDICT      = PASS
```

## 3.1 Note on scope — GAP-5

This review covers the four gaps the operator directed. **GAP-5
(accepted benchmark-rule namespace) remains OPEN** and is **not** answered by
any of the twenty questions. It was opened by the phantom-citation sweep after
the four-gap direction was formed. It is recorded in the authorization review
v0.2 as a still-open item that must be decided before implementation
authorization. Its absence here is a scope statement, not an oversight, and no
question above is being answered loosely to accommodate it.

---

# 4. What this PASS does and does not mean

```text
MEANS:
  - The four resolutions are self-consistent and add no unr ratified policy.
  - Every question is answered with its required answer and evidenced against
    the accepted implementation branch.
  - The successor artifacts are coherent with each other and with the RATIFIED
    v0.4 base (which is preserved, not rewritten).

DOES NOT MEAN:
  - That GAP-5 is resolved. It is OPEN.
  - That any artifact is ratified. All successors are
    DRAFT_PENDING_OPERATOR_RATIFICATION.
  - That implementation is authorized. BOOK_6_IMPLEMENTATION_AUTHORITY =
    FALSE.

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**Not authorized and not performed:** any implementation, any source or test
change, any float/Decimal/Fraction migration, any epsilon or isclose, any unit
ontology or conversion, any cross-metric corpus mutation, any coverage
applicability heuristic, any `NOT_APPLICABLE` by absence, any new canonical
coverage rule, any rule ratification, any Book 7 or Book 8 work, any live
acquisition, and any branch creation, force-push, rebase or history rewrite.
