# CSIA — BOOK 6 COMPARISON / CHANGE IMPLEMENTATION TEST SPEC — v0.3

**Document ID:** CSIA-B6-ITS-003
**Version:** 0.3
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Carries forward:** `..._TEST_SPEC_v0.2.md` (208 cases, 0 blocked) in full
**Supersedes:** v0.2 and v0.1 as the governing specification (both unratified)

**This document specifies tests. It contains NO test code and creates NO tests.**

---

# 0. What v0.3 adds

```text
v0.2 cases   = 208  (NUM 6, UNIT 4, CAPP 6, TCMP 7, CHK-19/20 2, + carried)
v0.3 adds    = 23 BASE cases + 6 PHANTOM regression cases = 29
v0.3 total   = 237
BLOCKED      = 0
```

## 0.1 Fixture discipline (carried, extended)

- Every fixture is constructed, not imported from production.
- Synthetic coverage rules are permitted and marked non-canonical.
- Canonical `COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0` is asserted in-test.
- Canonical `BENCHMARK_RULES_RATIFIED = 0` is **also** asserted in-test, so an
  accidental benchmark authority fails loudly.
- No test may mutate Book 1–5 or Sensor code.
- No test may import `book6_comparability` into the temporal comparison path.
- **No test may construct a `BenchmarkRule` or reference a benchmark registry** —
  because neither exists, and a test that referenced one would be the same
  phantom error this spec exists to prevent.

---

# 1. `BASE-1 .. BASE-23` — baseline selector (GAP-5, 5E)

## 1.1 Executable selector and reserved names

```text
BASE-1  PRIOR_COMPARABLE_WINDOW ACCEPTED
  A ComparisonRule with selector_kind = PRIOR_COMPARABLE_WINDOW and the single
  closed ordering policy is constructible and fingerprintable.

BASE-2  ROLLING_MEAN REJECTED AS RESERVED
  Constructing a ComparisonRule with selector_kind = ROLLING_MEAN is REJECTED.
  No placeholder behaviour: there is no partial or degraded path.

BASE-3  ROLLING_MEDIAN REJECTED
BASE-4  HISTORICAL_DISTRIBUTION REJECTED
BASE-5  BASELINE_EPOCH REJECTED
  Each rejected at construction AND at replay check 4 (selector validity).
```

## 1.2 No eligible baseline

```text
BASE-6  NO ELIGIBLE PRIOR OBSERVATION -> BASELINE_UNAVAILABLE
  All candidates fail eligibility -> INSUFFICIENT_DATA /
  BASELINE_UNAVAILABLE. No arithmetic, no silent fallback to the first item,
  to a nearest incompatible observation, to a rolling mean, or to an epoch.
```

## 1.3 Determinism

```text
BASE-7  CALLER ORDER CANNOT ALTER RESULT
  The same candidate set supplied in several different orders yields the same
  selected baseline ref.

BASE-8  LATER VALID PRIOR OBSERVATION WINS
  Among two eligible priors, the one with the greater valid_time END (strictly
  before comparison start) is selected.

BASE-9  OBSERVED_AT CANNOT OVERRIDE VALID-TIME ORDERING
  A candidate with an OLDER valid_time but a NEWER observed_at loses. observed_at
  is not an ordering input.

BASE-17 TIE-BREAK DETERMINISTIC
  Two candidates tied on valid_time END and START resolve by stable lexical
  measurement_ref, and resolve identically across runs.
```

## 1.4 Candidate eligibility exclusion

```text
BASE-10 WRONG METRIC EXCLUDED
BASE-11 WRONG UNIT EXCLUDED              (2D exact-unit identity)
BASE-12 INCOMPATIBLE METHODOLOGY EXCLUDED  (ref@version identity mismatch)
BASE-13 INCOMPATIBLE DENOMINATOR EXCLUDED
BASE-14 INCOMPATIBLE COHORT EXCLUDED WHERE APPLICABLE
BASE-15 INCOMPATIBLE WINDOW CLASS EXCLUDED
BASE-16 STALE / UNAUTHORIZED BOOK 2 INPUT EXCLUDED
```

Each asserts the candidate is excluded **by the named structural requirement**,
not by an aggregate boolean (`AGGREGATE_ONLY = REJECTED`), and that the engine
still selects correctly from the remaining eligible set.

## 1.5 Caller authority and authority decay

```text
BASE-18 EXPECTED SELECTED BASELINE MISMATCH REJECTS
  An expected selected_baseline_ref that disagrees with the engine's own
  resolution RAISES. Stored authority uses the ENGINE result.

BASE-19 SELECTED BASELINE CHANGES AFTER AUTHORITY DECAY
  When Book 2 authority for the recorded baseline decays, re-resolution
  differs -> current_authority = FALSE, history preserved, NO silent rebaseline.
```

## 1.6 Negative surface — no phantom benchmark

```text
BASE-20 NO BENCHMARKRULE REGISTRY REQUIRED
  Asserts no registry, no registration call, and no import of any benchmark
  module exists or is needed. Uses only ComparisonRule ratification.

BASE-21 NO benchmark_rule_ref FIELD
  ComparisonRule and ChangeObservation have no benchmark reference field
  (extra="forbid" makes any attempt a ValidationError).

BASE-22 SELECTOR MUTATION CHANGES COMPARISONRULE FINGERPRINT
  Mutating selector_kind, ordering policy, or any selector requirement under the
  same rule identity changes the canonical fingerprint and invalidates prior
  authority.

BASE-23 NO CALLER CALLBACK / EXPRESSION
  No free text, callable, expression, eval or exec may influence selection.
  Any attempt is rejected.
```

---

# 2. `PHANTOM-1 .. PHANTOM-6` — phantom-citation regression (Phase 22)

This family exists so the defect class does not recur. It is a **governance
test**, not a runtime test: it checks that governance claims about accepted
substrate resolve.

```text
PHANTOM-1 RUNTIME_REQUIRED CLAIMS RESOLVE
  Every existence claim about accepted runtime substrate resolves to a runtime
  symbol (file + line) or the claim fails.

PHANTOM-2 GOVERNANCE_ONLY CLAIMS RESOLVE
  Every claim classified GOVERNANCE_ONLY resolves to a ratified artifact that
  states the item's runtime status.

PHANTOM-3 FORWARD SPECIFICATIONS ARE NOT FAILURES
  Items labelled FORWARD_SPECIFICATION (ComparisonRule, ChangeObservation,
  BaselineSelectorSpec, TemporalComparabilityStatus) do not fail the check.
  The check must not flag intended-to-create artifacts.

PHANTOM-4 PROHIBITED / NEGATED ARE NOT FAILURES
  Items labelled PROHIBITED or NEGATED (reserved selectors, NO_ELIGIBLE_*
  outcomes, forbidden field names) do not fail the check.

PHANTOM-5 PROSE CITATIONS ARE SCANNED, NOT JUST CODE FONT
  The check scans prose existence claims ("the accepted X", "derived from the
  accepted Y", "reused unmodified", "already-ratified Z"). A symbol-only scan is
  insufficient: the original GAP-2 defect ("an accepted unit contract") had no
  code font at all.

PHANTOM-6 NO SIMPLISTIC GREP-ONLY CHECK
  Resolution is prefix/suffix aware and assertion-verb aware. A pure exact
  substring match is a FAILURE of the checker itself, because it produced a
  false phantom on CapitalPrincipalLineage vs
  CapitalPrincipalLineageGraph during the sweep that found this defect.
```

**Only `RUNTIME_REQUIRED` unresolved references fail.** The four categories
exist so legitimate forward specifications and explicit prohibitions are not
mistaken for defects.

**Required categories for every existence claim:**

```text
RUNTIME_REQUIRED       must resolve to a runtime symbol, or FAIL
GOVERNANCE_ONLY        must resolve to a ratified artifact, or FAIL
FORWARD_SPECIFICATION  must be labelled intended-to-create; not a failure
PROHIBITED / NEGATED   must be labelled forbidden/rejected; not a failure
```

---

# 3. Carried families from v0.2 (unchanged)

```text
COV-1..COV-12   (12)  coverage applicability and sufficiency
CHG-1..CHG-8    (8)   change observation and delta arithmetic
METH-1..METH-5  (5)   methodology compatibility and sensitivity
NULL-1..NULL-9  (9)   absence has exactly one meaning
REPLAY 1..20    (20)  the twenty replay checks, independently falsifiable
POL-1..POL-11   (11)  policy is not authority (P3 withdrawn)
NEG-SURFACE     (45)  negative surface: 9 field names x 5 attack vectors
FINGERPRINT     (4)   canonical fingerprint determinism
DISPLAY         (n)   display-independence
ANTI-CREEP      (n)   anti-creep and boundary
BOOK7-SEAM      (n)   Book 7 seam read-only contract
REGISTRY        (n)   rule registry and governance
TRACEABILITY    (n)   traceability plan
NUM-1..NUM-6    (6)   stored-binary64 semantics
UNIT-1..UNIT-4  (4)   same-metric unit identity
TCMP-1..TCMP-7  (7)   temporal comparability
CHK-19/CHK-20   (2)   replay separability
```

The 20 replay checks now have the v0.6 structure: checks 4-6 are the selector
checks replacing the phantom benchmark checks.

---

# 4. Totals and gates

```text
v0.3 total                              = 237
BLOCKED remaining                       = 0
NEW baseline-selector cases             = 23  (BASE-1..BASE-23)
NEW phantom-regression cases            = 6   (PHANTOM-1..PHANTOM-6)
TEST CODE WRITTEN                       = 0   (specification only)

REPLAY_CHECK_COUNT                      = 20
NEGATIVE_SURFACE_CASES                  = 45
CANONICAL_COVERAGE_RULES_RATIFIED       = 0  (asserted in-test)
CANONICAL_BENCHMARK_RULES_RATIFIED      = 0  (asserted in-test)
SYNTHETIC_TEST_RULES_ALLOWED            = TRUE
SYNTHETIC_RULES_ARE_CANONICAL           = FALSE
```

```text
G-1  all accepted Book 6 tests still pass (1341)
G-2  full CSIA suite still passes (2162)
G-3  Sensor unchanged from accepted baseline (2325 PASS / 14 FAIL / 4 SKIPPED)
G-4  Book 1-5 mutation count = 0; Sensor mutation count = 0
G-6  ruff + mypy clean on new modules
G-7  20 checks individually traceable
G-8  contract count == 2; HIDDEN_THIRD_CONTRACT == NONE
G-9  no epsilon / isclose / tolerance / Decimal / Fraction anywhere
G-10 no BenchmarkRule / BenchmarkRuleRegistry / benchmark fingerprint exists
G-11 no rolling mean / median / distribution / epoch implementation
G-12 no observed_at baseline ordering; no random or caller-order selection
G-14 phantom-citation regression check passes (PHANTOM-1..PHANTOM-6)
```

---

# 5. Spec verdict

```text
ALL_CASES_SPECIFIABLE_WITHOUT_INVENTION = TRUE
BLOCKED_REMAINING                       = 0
TEST_CODE_WRITTEN                       = 0
PHANTOM_CITATION_REGRESSION_COVERAGE    = TRUE

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

This specification is complete and writable **once substrate clarification v0.2
and its successors are operator-ratified**. It is not authorization to write the
tests.

**Not authorized and not performed:** any test file creation or modification,
any source change, any `BenchmarkRule` or `BenchmarkRuleRegistry`, any
benchmark-rule ratification, any rolling mean / rolling median / historical
distribution / baseline epoch implementation, any `observed_at` baseline
ordering, any caller-order selection, any canonical coverage or benchmark rule
ratification, and any live acquisition.
