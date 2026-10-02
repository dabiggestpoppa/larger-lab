# CSIA — BOOK 6 COMPARISON / CHANGE IMPLEMENTATION TEST SPEC — v0.2

**Document ID:** CSIA-B6-ITS-002
**Version:** 0.2
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-02
**Supersedes as a specification:** `..._TEST_SPEC_v0.1.md` (178 cases, 14 BLOCKED).
v0.1 is preserved and remains the ratified-basis reference; v0.2 resolves the 14
blocked cases and adds the gap-resolution coverage the operator required.

**This document specifies tests. It contains NO test code and creates NO tests.**
No source file and no test file is modified by this artifact.

---

# 0. What changed from v0.1

```text
v0.1 cases                     = 178  (164 writable, 14 BLOCKED)
v0.2 cases                     = 178 + 30 new resolution cases = 208
BLOCKED cases remaining        = 0
New families                   = NUM (6), UNIT (4), CAPP (6),
                                 TCMP (7), CHK-19/CHK-20 (2)
```

The 14 v0.1 blocked cases become writable because the four gaps now have ratified
-resolved semantics. Each is mapped in §8.

## 0.1 Fixture discipline (carried from v0.1)

- Every fixture is constructed, not imported from production.
- **Synthetic coverage rules are permitted** (`SYNTHETIC_TEST_RULES_ALLOWED =
  TRUE`) and are marked non-canonical (`SYNTHETIC_RULES_ARE_CANONICAL = FALSE`).
  A passing synthetic test is never evidence that a canonical rule exists.
- Canonical `COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0` is asserted in a dedicated
  test so a future accidental canonical rule fails loudly.
- No test may mutate Book 1–5 or Sensor code.
- No test may import `book6_comparability` into the temporal comparison path.

---

# 1. `NUM-1 .. NUM-6` — stored-binary64 numeric semantics (GAP-1, 1A-STRICT)

Each test asserts stored-value semantics, never real-number idealisation.

```text
NUM-1  EXACT STORED BINARY64 EQUALITY
  Given two stored canonical values equal under == , the engine reports
  NO_CHANGE. Asserts CANONICAL_EQUALITY is exact stored-value equality.
  No epsilon. No isclose.

NUM-2  0.1 + 0.2 vs 0.3 FOLLOWS STORED-VALUE SEMANTICS
  baseline stored 0.3, comparison stored (0.1 + 0.2) = 0.30000000000000004.
  The engine must NOT treat these as equal. change_kind != NO_CHANGE.
  Proves the engine does not idealise to real numbers.

NUM-3  NaN REJECTS
  A stored NaN input yields INSUFFICIENT_DATA (or fail-closed availability).
  Never INCREASE/DECREASE/NO_CHANGE/absolute_delta/relative_delta.

NUM-4  +Inf REJECTS
  Same outcome contract as NUM-3.

NUM-5  -Inf REJECTS
  Same outcome contract as NUM-3.

NUM-6  SIGNED-ZERO CANONICAL HANDLING
  +0.0 vs -0.0: absolute equality -> NO_CHANGE (canonically equal, canonically
  zero). Relative delta with a ±0.0 baseline -> UNDEFINED (zero-baseline
  fail-closed). Asserts NO signed-zero distinction anywhere.
```

**NUM-3/4/5 assert the sentinel is NOT inherited:** the engine rejects
non-finiteness at the input boundary via `math.isfinite()`, and no non-finite
value ever reaches delta arithmetic. The Book 6 core ratio NaN sentinel
(`book6_core.py:181`) is not consulted.

---

# 2. `UNIT-1 .. UNIT-4` — same-metric exact-unit identity (GAP-2, 2D)

```text
UNIT-1  SAME METRIC + EXACT UNIT -> ARITHMETIC VALID
  baseline and comparison both resolve to the bound metric_definition_ref and
  both carry unit == MetricDefinition.unit. Arithmetic is permitted;
  comparability may reach COMPARABLE.

UNIT-2  SAME METRIC + UNIT MISMATCH -> NOT_COMPARABLE
  Observation unit differs from MetricDefinition.unit. Result is
  comparability_status = NOT_COMPARABLE. NOT a conversion.

UNIT-3  DIFFERENT METRIC REF -> NOT_COMPARABLE
  An observation resolves to a different metric_definition_ref. Result is
  NOT_COMPARABLE.

UNIT-4  NO CONVERSION ATTEMPTED
  On any unit or metric mismatch the engine performs no conversion, alias
  resolution, dimensional inference, or unit normalization. Asserts the delta
  stage is never reached and no converted value is produced.
```

**UNIT-2/3/4 assert NOT_COMPARABLE specifically**, not UNRESOLVED — a unit or
metric mismatch is an explicit structural failure (§3.3), not an absence of
basis.

---

# 3. `CAPP-1 .. CAPP-6` — coverage applicability derivation (GAP-3, 3C)

```text
CAPP-1  NO COVERAGE RULE -> UNRESOLVED
  No rule registered for the metric. coverage_requirement_status = UNRESOLVED;
  coverage_applicability_source_ref ABSENT (NO_UPSTREAM_DETERMINATION_EXISTS).

CAPP-2  CURRENT RATIFIED SCOPED SYNTHETIC RULE -> REQUIRED
  A synthetic, operator-ratified, exact-metric-scoped rule exists.
  coverage_requirement_status = REQUIRED and source_ref names that rule.

CAPP-3  UNRATIFIED RULE -> UNRESOLVED
  A rule is registered but NOT ratified. Status = UNRESOLVED. Registration is
  not ratification (registry R1).

CAPP-4  WRONG-SCOPE RULE -> UNRESOLVED
  A ratified rule scoped to a DIFFERENT metric. authorize() refuses on scope
  mismatch -> UNRESOLVED. Never REQUIRED.

CAPP-5  SUPERSEDED RULE -> UNRESOLVED
  A superseded rule version. Not current -> UNRESOLVED. Never REQUIRED.

CAPP-6  NOT_APPLICABLE CANNOT BE INFERRED
  Absence of a rule yields UNRESOLVED, NEVER NOT_APPLICABLE. Asserts
  CAN_DERIVE_NOT_APPLICABLE = FALSE across every absence-shaped fixture.
```

**CAPP-2/CAPP-4/CAPP-5 exercise the accepted registry's real refusals**
(`CoverageRuleRegistry.authorize`, which refuses missing registration, missing
current ratification, and scope mismatch). CAPP-4/CAPP-5 must use synthetic
non-canonical rules so no canonical rule is created.

---

# 4. `TCMP-1 .. TCMP-7` — temporal comparability (GAP-4, 4D)

```text
TCMP-1  ALL STRUCTURAL GATES PASS -> COMPARABLE
  With a current ratified scoped synthetic coverage rule and SUFFICIENT verdict,
  and all other gates satisfied -> comparability_status = COMPARABLE.

TCMP-2  UNIT MISMATCH -> NOT_COMPARABLE
TCMP-3  INCOMPATIBLE METHODOLOGY -> NOT_COMPARABLE
TCMP-4  COVERAGE INSUFFICIENT -> NOT_COMPARABLE
        (coverage REQUIRED and verdict INSUFFICIENT)
TCMP-5  COVERAGE APPLICABILITY UNRESOLVED -> UNRESOLVED
        (no rule -> UNRESOLVED, NOT NOT_COMPARABLE)
TCMP-6  UNRESOLVED NEVER BECOMES NOT_COMPARABLE
  Asserts the mapping UNRESOLVED -> NOT_COMPARABLE is unreachable across the
  whole fixture matrix. UNRESOLVED -> INSUFFICIENT_DATA only.
TCMP-7  CROSS-METRIC CORPUS NOT CONSULTED
  The temporal comparison path never reads FALSE_COMPARISON_CORPUS, never
  calls authorize_comparison(), never reinterprets CorpusVerdict. Asserts
  book6_comparability is not consulted and FC-01..FC-15 are unchanged.
```

**TCMP-6 is the decisive GAP-4 test.** The ratified v0.4 grammar had no producing
check for `NOT_COMPARABLE`; the new check 19 must produce it, and must never
produce it from an `UNRESOLVED` basis.

---

# 5. `CHK-19` / `CHK-20` — replay separability

```text
CHK-19  TEMPORAL COMPARABILITY INDEPENDENTLY FALSIFIABLE
  Each comparability gate in grammar v0.5 §3.2 can be made to fail by a single
  fixture mutation while checks 1-18 and 20 still pass. Proves check 19 is
  independently falsifiable and reports the specific failed gate
  (AGGREGATE_ONLY = REJECTED).

CHK-20  DETERMINISTIC RECOMPUTATION INDEPENDENTLY FALSIFIABLE
  A comparison that passes check 19 (COMPARABLE) can still fail check 20 when
  the recorded delta disagrees with the recomputed delta. Also: when check 19
  is NOT_COMPARABLE or UNRESOLVED, check 20 does not recompute a change.
```

CHK-19/CHK-20 together prove the two new checks are **separable**, which the v0.4
19-check replay could not demonstrate.

---

# 6. The 14 previously blocked cases — now writable

Every v0.1 blocked case is listed with the resolution that unblocks it and the
v0.2 case that carries it. **All 14 are resolved.**

| v0.1 case | was blocked by | resolution | v0.2 carrier |
|---|---|---|---|
| `COV-6` | GAP-3 | 3C presence derivation — absence yields `UNRESOLVED` | `CAPP-1` |
| `CHG-1` | GAP-1, GAP-2 | 1A-STRICT + 2D | `NUM-1`, `UNIT-1`, `TCMP-1` |
| `CHG-2` | GAP-1, GAP-2 | 1A-STRICT + 2D | `NUM-1`, `UNIT-1` |
| `CHG-3` | GAP-1 (**decisive**) | 1A-STRICT — equality is exact stored binary64 `==` | `NUM-1`, `NUM-2` |
| `CHG-5` | GAP-2 | 2D — subtraction valid only under same-metric exact-unit identity | `UNIT-1`, `UNIT-2` |
| `POL-3` | GAP-2 (untestable) | P3 **WITHDRAWN** — the untestable citation is removed, not satisfied | `UNIT-4` |
| `POL-11` | GAP-2 | 2D — a rule cannot declare units compatible because compatibility is derived, not authored | `UNIT-4` |
| `UNIT-1` | GAP-2 | 2D — identical units permit subtraction | `UNIT-1` |
| `UNIT-2` | GAP-2 | 2D — incompatible units refused by derivation, never by a rule | `UNIT-2`, `UNIT-3` |
| `UNIT-3` | GAP-2 | 2D — relative ratio dimensionless under same unit | `UNIT-1` |
| `UNIT-4` | GAP-2 | 2D — compatibility is derived; no rule can declare it | `UNIT-4` |
| `UNIT-5` | GAP-2 | 2D — no caller override exists; validity is derived, never asserted | `UNIT-4` |
| `COV-9` (implied by COV-6 family) | GAP-3 | 3C | `CAPP-1..CAPP-6` |
| replay check 19 | GAP-4 | 4D — dedicated temporal comparability check added | `CHK-19` |

**Count reconciliation:** v0.1's `UNIT-1..UNIT-5` are superseded by v0.2's
`UNIT-1..UNIT-4` with different semantics (the old UNIT-3 "dimensionless result"
case becomes the relative-delta case under same-unit identity; the old UNIT-4/5
override cases collapse into UNIT-4). This is a deliberate re-scoping, not a
deletion: every old case's *intent* is preserved and re-expressed against the
resolved semantics. The mapping is recorded here so no coverage is silently lost.

**`AGGREGATE_ONLY = REJECTED`** applies to the new check 19 as well: TCMP-1..TCMP-7
each isolate a single gate, and CHK-19 requires a named failed gate, never a bare
boolean.

---

# 7. Carried families (unchanged from v0.1)

The following v0.1 families are carried **verbatim in intent** and remain
required. They are listed so the 208-case total is auditable.

```text
COV-1..COV-12   (12)  coverage applicability and sufficiency
CHG-1..CHG-8    (8)   change observation and delta arithmetic
METH-1..METH-5  (5)   methodology compatibility and sensitivity
NULL-1..NULL-9  (9)   absence has exactly one meaning
REPLAY 1..20    (20)  the twenty replay checks, each independently falsifiable
POL-1..POL-11   (11)  policy is not authority (P3 withdrawn, rest as rejection)
NEG-SURFACE     (45)  negative surface: 9 field names x 5 attack vectors
FINGERPRINT     (4)   canonical fingerprint determinism
DISPLAY         (n)   display-independence
ANTI-CREEP      (n)   anti-creep and boundary
BOOK7-SEAM      (n)   Book 7 seam read-only contract
REGISTRY        (n)   rule registry and governance
TRACEABILITY    (n)   traceability plan
NUM-1..NUM-6    (6)   NEW - stored-binary64
UNIT-1..UNIT-4  (4)   NEW - same-metric unit identity
CAPP-1..CAPP-6  (6)   NEW - coverage applicability
TCMP-1..TCMP-7  (7)   NEW - temporal comparability
CHK-19/CHK-20   (2)   NEW - replay separability
```

The 20 replay checks now include the NEW check 19 (temporal comparability);
check 20 is deterministic recomputation. The 45-case negative surface and the
fingerprint tests are unchanged: none of them depends on the four gaps.

**Canonical coverage-rule count is asserted = 0** in a dedicated carried test, so
that if a future change ever creates a canonical coverage rule, the suite fails
loudly rather than silently changing the fail-closed baseline.

---

# 8. Case totals

```text
v0.1 total                              = 178
v0.1 writable                           = 164
v0.1 BLOCKED                            = 14
v0.2 new resolution cases               = 30  (NUM 6, UNIT 4, CAPP 6,
                                                TCMP 7, CHK-19/20 2,
                                                replay-check-19 delta 1)
v0.2 total                              = 208
v0.2 BLOCKED remaining                  = 0

REPLAY_CHECK_COUNT                      = 20
NEGATIVE_SURFACE_CASES                  = 45
CANONICAL_COVERAGE_RULES_RATIFIED       = 0  (asserted in-test)
SYNTHETIC_TEST_RULES_ALLOWED            = TRUE
SYNTHETIC_RULES_ARE_CANONICAL           = FALSE
```

---

# 9. Regression obligations

```text
G-1  all accepted Book 6 tests still pass (1341)
G-2  full CSIA suite still passes (2162)
G-3  Sensor unchanged from accepted baseline (2325 PASS / 14 FAIL / 4 SKIPPED)
G-4  Book 1-5 mutation count = 0; Sensor mutation count = 0
G-6  ruff + mypy clean on new modules
G-7  20 checks individually traceable
G-8  contract count == 2; HIDDEN_THIRD_CONTRACT == NONE
G-9  no epsilon / isclose / tolerance / Decimal / Fraction anywhere
```

The baselines 1341 / 2162 / 2343 were independently reproduced during this
planning work, so these obligations are anchored to measured numbers.

---

# 10. Spec verdict

```text
ALL_PREVIOUSLY_BLOCKED_CASES_WRITABLE   = TRUE   (14/14 resolved)
NEW_CASES_FULLY_SPECIFIABLE_WITHOUT_INVENTION = TRUE
BLOCKED_REMAINING                       = 0
TEST_CODE_WRITTEN                       = 0   (specification only)

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

This specification is complete and writable **once the substrate clarification
v0.1 and its successors are operator-ratified**. It is not authorization to
write the tests.

**Not authorized and not performed:** any test file creation or modification, any
source change, any float/Decimal/Fraction migration, any epsilon or isclose, any
unit ontology or conversion, any cross-metric corpus mutation, any new canonical
coverage rule, any rule ratification, and any live acquisition.
