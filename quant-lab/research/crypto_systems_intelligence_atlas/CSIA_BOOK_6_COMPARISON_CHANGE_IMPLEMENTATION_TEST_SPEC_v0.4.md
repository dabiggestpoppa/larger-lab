# CSIA — Book 6 Comparison/Change: Implementation Test Spec v0.4

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-03
**Supersedes as a spec:** `..._IMPLEMENTATION_TEST_SPEC_v0.3.md` — which is
**RATIFIED** inside `BOOK6-COMPARE-SUBSTRATE-v0.2` and is **carried forward
here, unedited**.

```text
v0.3 = 237 cases, 0 BLOCKED   -> CARRIED IN FULL, NOT EDITED
v0.4 = 237 + 15 TIME cases = 252
ADDITIONS_ONLY               = TRUE
PRIOR_CASE_RENUMBERED        = NONE
PRIOR_CASE_REMOVED           = NONE
TEST_CODE_WRITTEN            = 0   (specification only)
```

**This document grants no implementation authority.**

---

## 1. The TIME group — GAP-6 temporal ordering

15 cases. Each is independently falsifiable and states its own expected result.

### TIME-1 — instantaneous candidate carries no interval, remains eligible

```text
SETUP   one WindowClass.INSTANTANEOUS candidate (no window_start/end)
        one WindowClass.INSTANTANEOUS comparison, valid_time later
EXPECT  candidate is ELIGIBLE and is selectable
        candidate.window_start is None AND candidate.window_end is None
FORBID  any code path that populates either field
```

### TIME-2 — `t1 < t2 < t3 < t4` selects `t3`

```text
SETUP   instantaneous candidates t1,t2,t3 ; comparison t4 ; t1<t2<t3<t4
EXPECT  selected baseline == t3
        (effective_end(c) == c.valid_time for all c)
```

### TIME-3 — caller order is irrelevant

```text
SETUP   TIME-2 fixture, permuted N times in caller/input order
EXPECT  selected baseline == t3 for EVERY permutation
```

### TIME-4 — `observed_at` is irrelevant

```text
SETUP   TIME-2 fixture with observed_at values permuted / inverted
EXPECT  selected baseline == t3 for EVERY observed_at assignment
FORBID  any read of observed_at inside the ordering path
```

### TIME-5 — same `valid_time` tie resolves lexically

```text
SETUP   two instantaneous candidates, identical valid_time,
        measurement_ref values differing
EXPECT  selection == the greater lexical measurement_ref
        (effective_end ties, effective_start ties, tie-break fires)
```

### TIME-6 — same instant is NOT prior

```text
SETUP   instantaneous candidate with valid_time == comparison.valid_time
EXPECT  candidate is INELIGIBLE (strict < fails)
        result -> INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
FORBID  <= in the precedence test
```

### TIME-7 — interval behaviour identical to v0.6

```text
SETUP   identical interval fixtures (non-overlapping [start,end) windows)
EXPECT  OLD_INTERVAL_ORDERING_RESULT == NEW_EFFECTIVE_KEY_ORDERING_RESULT
        for every fixture and every input permutation
```

### TIME-8 — mixed shape rejected before ordering

```text
SETUP   candidate and comparison resolving to different bound
        MetricDefinition / WindowClass
EXPECT  candidate STRUCTURALLY INELIGIBLE;
        comparison NOT_COMPARABLE;
        NO ordering is computed across the shapes
FORBID  any coercion in either direction
```

### TIME-9 — forged interval on an instantaneous record is rejected

```text
SETUP   WindowClass.INSTANTANEOUS observation carrying window_start/end
EXPECT  accepted model rejects at construction
        (_check_window_discipline, book6_records.py:169-175)
        MeasurementRecordError raised
```

### TIME-10 — interval record missing bounds is rejected

```text
SETUP   interval window_class with window_start or window_end None
EXPECT  accepted model rejects (book6_records.py:160-168)
        MeasurementRecordError raised
```

### TIME-11 — superseded record filtered BEFORE the tie-break

```text
SETUP   two instantaneous observations, SAME metric, SAME valid_time;
        one status == ObservationStatus.SUPERSEDED, one OBSERVED
EXPECT  selection == the OBSERVED one, for ANY lexical relationship,
        including when the SUPERSEDED ref sorts greater
ORDER   eligibility (record state) completes BEFORE ordering begins
FORBID  any lexical comparison that could prefer the SUPERSEDED record
```

This is the case where a naive implementation would let the lexical tie-break
resurrect a dead record. The gate is `status is ObservationStatus.OBSERVED`
(`book6_records.py:129`, enum at `book6_grammar.py:264-272`).

### TIME-12 — effective keys never persist

```text
SETUP   run the selector over interval and instantaneous fixtures
EXPECT  MeasurementObservation instances are byte-identical before and after
        (frozen model; model_config extra="forbid", frozen=True)
        no window_start / window_end / derived field is added or written
        no new attribute exists on the model
```

### TIME-13 — no zero-width interval constructed

```text
FORBID  any code path producing [t, t]
        any assignment of window_start == window_end
        any accepted-model violation (start >= end raises; TIME-10)
ASSERT  instantaneous records keep both interval fields None
```

### TIME-14 — no one-day convention exists

```text
FORBID  any use of timedelta(days=1) in the SELECTOR
ASSERT  the fixture span at book6_support.py:419 is fixture-only and is
        never reachable from production ordering
```

### TIME-15 — no `observed_at` ordering path exists

```text
FORBID  any read of observation.observed_at inside the ordering/selection code
ASSERT  observed_at is read only where knowledge time is genuinely required
```

---

## 2. Carried groups — unchanged from v0.3

All of the following are carried **verbatim**; no case is edited, renumbered, or
removed.

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
NUM-1..NUM-6    (6)   stored-binary64 semantics          (GAP-1)
UNIT-1..UNIT-4  (4)   same-metric unit identity         (GAP-2)
TCMP-1..TCMP-7  (7)   temporal comparability            (GAP-4)
CHK-19/CHK-20   (2)   replay separability
BASE-1..BASE-23 (23)  baseline selector (incl. reserved-name rejection)
PHANTOM-1..6    (6)   phantom-citation regression
```

```text
CARRIED_CASES = 237
CARRIED_UNCHANGED = TRUE
```

---

## 3. Totals and gates

```text
v0.4 total                              = 252
  carried from v0.3                     = 237
  new TIME cases                        = 15   (TIME-1..TIME-15)

BLOCKED remaining                       = 0
TEST CODE WRITTEN                       = 0   (specification only)

REPLAY_CHECK_COUNT                      = 20
NEGATIVE_SURFACE_CASES                  = 45
CANONICAL_COVERAGE_RULES_RATIFIED       = 0  (asserted in-test)
CANONICAL_BENCHMARK_RULES_RATIFIED      = 0  (asserted in-test)
SYNTHETIC_TEST_RULES_ALLOWED            = TRUE
SYNTHETIC_RULES_ARE_CANONICAL           = FALSE

NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT                    = NONE
```

### 3.1 Gates — v0.3 gates carried, GAP-6 gates added

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

G-16 no window_start / window_end is ever written by the selector   (TIME-1,13)
G-17 effective ordering keys never persist onto the record           (TIME-12)
G-18 OLD_INTERVAL_ORDERING_RESULT == NEW_EFFECTIVE_KEY_ORDERING_RESULT
                                                            (TIME-7)
G-19 eligibility completes BEFORE ordering; tie-break sees only
     eligible candidates                                     (TIME-11)
```

`FAILURE OF ANY GATE = HOLD`.

### 3.2 TIME case → gate / rule traceability

| Cases | Rule under test |
|---|---|
| TIME-1, TIME-13 | `INSTANTANEOUS_REMAINS_POINT`; `SYNTHETIC_ZERO_WIDTH_INTERVAL = FALSE` |
| TIME-2, TIME-5 | `effective_end/effective_start` projection; `LEXICAL_TIEBREAK_ONLY_AFTER_TEMPORAL_TIE` |
| TIME-3, TIME-15 | `CALLER_ORDER_AFFECTS_BASELINE = FALSE`; `OBSERVED_AT_USED_FOR_ORDERING = FALSE` |
| TIME-4 | `OBSERVED_AT_USED_FOR_ORDERING = FALSE` |
| TIME-6 | `STRICT_TEMPORAL_PRECEDENCE = TRUE` |
| TIME-7 | interval-path invariance |
| TIME-8 | `WINDOW_CLASS_CONVERSION = FALSE`; mixed-shape defense |
| TIME-9, TIME-10 | accepted model unchanged (`book6_records.py:159-179`) |
| TIME-11 | `AUTHORITY_AND_RECORD_ELIGIBILITY -> ORDERING` |
| TIME-12 | `ORDERING_KEYS_ARE_DERIVED`; `OBSERVATION_MUTATION = FALSE` |
| TIME-14 | `ONE_DAY_CONVENTION = FALSE` |

---

## 4. Spec verdict

```text
ALL_CASES_SPECIFIABLE_WITHOUT_INVENTION = TRUE
BLOCKED_REMAINING                       = 0
TEST_CODE_WRITTEN                       = 0
PRIOR_CASES_EDITED                      = 0
NEW_GATES_ADDED                         = 4   (G-16..G-19)

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 5. Status

```text
TEST_SPEC = v0.4 DRAFT_PENDING_OPERATOR_RATIFICATION
GAP_6     = 6E PROPOSED / NOT RATIFIED
GAP_1..GAP_5 = CLOSED / UNCHANGED / NOT REOPENED
```

**No test code was written.** This document is a specification. Implementation
remains unauthorized.
