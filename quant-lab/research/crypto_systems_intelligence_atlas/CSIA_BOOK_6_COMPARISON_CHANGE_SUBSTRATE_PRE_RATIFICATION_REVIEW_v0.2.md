# CSIA — BOOK 6 COMPARISON / CHANGE SUBSTRATE PRE-RATIFICATION REVIEW — v0.2

**Document ID:** CSIA-B6-SPR-002
**Version:** 0.2
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Kind:** PRE-RATIFICATION ADVERSARIAL REVIEW (20 mandatory questions)
**Subject:** substrate clarification v0.2, grammar v0.6, plan v0.6, boundary v0.4,
ratification-record erratum v0.1, test spec v0.3

**This review authorizes nothing.**

---

# 1. Verdict

```text
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_PRE_RATIFICATION_REVIEW_v0.2 = PASS
SCORE = 20 / 20
```

Evidence anchors are files and lines in the accepted implementation branch
`agent/crypto-systems-intelligence-atlas-book6-build` @ `5f94c3f4`.

---

# 2. The twenty questions

## Q1 — Is a `BenchmarkRule` required? **Required NO.**

**NO.** 5E embeds baseline-selection semantics inside `ComparisonRule` as
`BaselineSelectorSpec` (grammar v0.6 §2.2). No `BenchmarkRule` is defined,
referenced, or required. `BENCHMARK_RULE_RUNTIME = NOT_IMPLEMENTED`; zero
`Benchmark*` symbols exist across all 62 runtime modules. Test BASE-20/BASE-21
assert the absence.

## Q2 — Is a `BenchmarkRuleRegistry` required? **Required NO.**

**NO.** `ComparisonRule` operator ratification supplies the authority. No second
registry, no second ledger, no second registration path.
`BASELINE_SELECTOR_INDEPENDENT_REGISTRY = FALSE`.

## Q3 — Is baseline selection independently ratified? **Required NO.**

**NO.** `BASELINE_SELECTOR_INDEPENDENT_RATIFICATION = FALSE`
(substrate v0.2 §5.3). Authority flows entirely from `ComparisonRule`
ratification.

## Q4 — Is baseline selection fingerprint-bound through `ComparisonRule`? **Required YES.**

**YES.** Grammar v0.6 §2.7 requires the selector's semantic content inside the
canonical `ComparisonRule` fingerprint, with mutation invalidating prior
authority. Precedent: `METHODOLOGY_CANONICAL_FIELDS` (`book6_methodology.py:85-97`)
→ `canonical_methodology_spec()` (`:99`) → `methodology_fingerprint()` (`:132`).
Test BASE-22.

## Q5 — Is the initial executable selector set closed? **Required YES.**

**YES.** `BaselineSelectorKind` has 5 members: 1 executable
(`PRIOR_COMPARABLE_WINDOW`), 4 `RESERVED_NOT_EXECUTABLE`. Reserved names are
REJECTED at construction and at replay check 4. No placeholder behaviour.
Tests BASE-2..BASE-5.

## Q6 — Is `PRIOR_COMPARABLE_WINDOW` fully specified? **Required YES.**

**YES.** Grammar v0.6 §2.3 (11 eligibility conditions), §2.4 (closed ordering),
§2.5 (no-baseline outcome), §2.6 (single-observation result). Every condition is
an exact comparison over accepted fields.

## Q7 — Can caller order affect selection? **Required NO.**

**NO.** Ordering is by valid_time END, then START, then stable lexical
measurement_ref. `CALLER_ORDER_AFFECTS_BASELINE = FALSE`. Test BASE-7.

## Q8 — Can `observed_at` replace valid-time ordering? **Required NO.**

**NO.** `observed_at` is not an ordering input.
`OBSERVED_AT_USED_FOR_BASELINE_ORDERING = FALSE`. Test BASE-9 asserts a
newer-`observed_at` candidate with older valid time loses.

## Q9 — Can rolling mean execute? **Required NO.**

**NO.** `ROLLING_MEAN = RESERVED_NOT_EXECUTABLE`; rejected at construction and at
check 4. No aggregation is implemented. Test BASE-2.

## Q10 — Can historical distribution execute? **Required NO.**

**NO.** `HISTORICAL_DISTRIBUTION = RESERVED_NOT_EXECUTABLE`. Test BASE-4.
(`ROLLING_MEDIAN` likewise, test BASE-3; `BASELINE_EPOCH`, test BASE-5.)

## Q11 — Can baseline epoch execute? **Required NO.**

**NO.** `BASELINE_EPOCH = RESERVED_NOT_EXECUTABLE`. No epoch-baseline fallback
exists anywhere. Test BASE-5, and BASE-6 asserts no fallback to one.

## Q12 — Can no eligible baseline silently fall back? **Required NO.**

**NO.** `NO_ELIGIBLE_PRIOR_BASELINE → INSUFFICIENT_DATA /
BASELINE_UNAVAILABLE` (grammar v0.6 §2.5), a first-class outcome. No fallback to
first item, nearest incompatible observation, rolling mean, or epoch. Test
BASE-6.

## Q13 — Does selector mutation require new `ComparisonRule` fingerprint/version/ratification? **Required YES.**

**YES.** Grammar v0.6 §2.7: mutation under the same rule identity changes the
fingerprint and invalidates prior authority, so a new version and a new operator
ratification are required. Test BASE-22.

## Q14 — Does contract count remain 2? **Required YES.**

**YES.** `NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2`
(`ComparisonRule`, `ChangeObservation`); `HIDDEN_THIRD_CONTRACT = NONE`.
`BaselineSelectorSpec` has no registry, no ledger, no independent lifecycle, and
cannot exist authoritatively outside a `ComparisonRule`. Boundary v0.4 §4.

## Q15 — Does this repair solve Class C `StateRule` benchmark semantics? **Required NO.**

**NO.** `StateRule.benchmark_methodology_ref` (`book6_states.py:178`, enforced
at `:214`) is a **separate** accepted mechanism for Class C threshold/benchmark
states (`StateClass.C_THRESHOLD_BENCHMARK`, `book6_states.py:72`).
`BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED`.
`COMPARISON_RULE_BASELINE_SELECTOR_REUSES_STATE_RULE_AUTHORITY = FALSE`. This
repair closes only the comparison/change baseline path and does not claim to
solve Class C semantics.

## Q16 — Is the phantom benchmark claim removed prospectively? **Required YES.**

**YES.** Grammar v0.6 §0.1 removes all five phantom terms; plan v0.6 §1 drops the
`REUSED: accepted benchmark-rule namespace` line; substrate v0.2 §5.1 sets
`ACCEPTED_BENCHMARK_RULE_NAMESPACE = FALSE`. Ratified v0.4 text is untouched and
the erratum records the history verbatim.

## Q17 — Is ratified v0.4 history preserved? **Required YES.**

**YES.** Grammar v0.4, plan v0.4, boundary v0.3, seam v0.4, readiness v0.3 and
ratification record v0.1 are unmodified. No ratified artifact is edited in place;
corrections are additive successors.

## Q18 — Does the ratification record get rewritten? **Required NO.**

**NO.** The erratum is a separate artifact. `ORIGINAL_RECORD_REMAINS_HISTORICAL
= TRUE`; `RETROACTIVE_CORRECTION_CLAIMED = FALSE`. It quotes the original
statements verbatim and corrects prospectively.

## Q19 — Does phantom-citation regression coverage exist? **Required YES.**

**YES.** Test spec v0.3 §2 defines `PHANTOM-1..PHANTOM-6` with four
classification categories (`RUNTIME_REQUIRED`, `GOVERNANCE_ONLY`,
`FORWARD_SPECIFICATION`, `PROHIBITED / NEGATED`); only unresolved
`RUNTIME_REQUIRED` fails. Prose claims are scanned (PHANTOM-5) and a grep-only
checker fails itself (PHANTOM-6, from the `CapitalPrincipalLineageGraph`
false positive). Boundary v0.4 §2–§3 encodes the invariant.

## Q20 — Are GAP-1..GAP-5 all now implementation-specifiable without coder policy? **Required YES.**

**YES.** GAP-1 `1A-STRICT`, GAP-2 `2D`, GAP-3 `3C`, GAP-4 `4D`, GAP-5 `5E` each
name accepted substrate or introduce no contract. Test spec v0.3 covers all five
families (NUM, UNIT, CAPP, TCMP, BASE) with `BLOCKED = 0`.

---

# 3. Score and scope

```text
Q1  .. Q20  = 20 PASS / 0 FAIL
SCORE        = 20 / 20
VERDICT      = PASS
```

## 3.1 One standing condition, recorded not waived

Phase 8's `HOLD and surface it` condition remains live: if a metric declares
`aggregation == NONE` **and** multiple observations exist for one comparison
window, `PRIOR_COMPARABLE_WINDOW` cannot select one without aggregating, and that
is a genuine new operator decision rather than an implementation detail
(substrate v0.2 §5.9; grammar v0.6 §2.6). It is recorded, not resolved by
assumption. It is a runtime condition, not a defect in this specification.

---

# 4. What this PASS means

```text
MEANS:
  - All five resolutions are self-consistent and add no unratifiable policy.
  - GAP-5 is closed by removing the phantom claim, not by satisfying it.
  - No BenchmarkRule, registry, or benchmark authority is required anywhere.
  - Ratified history is preserved and corrections are additive.

  - That implementation is authorized.
  - That Class C StateRule benchmark semantics are solved.
  - That the Phase 8 aggregation condition is resolved.

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**Not authorized and not performed:** any implementation, source or test change,
any `BenchmarkRule` or `BenchmarkRuleRegistry`, any benchmark-rule ratification,
any rolling mean / rolling median / historical distribution / baseline epoch
implementation, any `observed_at` baseline ordering, any random or caller-order
selection, Book 7 or Book 8 work, live acquisition, and any branch creation,
force-push, rebase or history rewrite.
