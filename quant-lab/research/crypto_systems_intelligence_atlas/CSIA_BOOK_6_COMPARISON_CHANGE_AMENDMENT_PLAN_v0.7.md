# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT PLAN — v0.7

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-03
**Relationship:**

```text
v0.6 = RATIFIED SUCCESSOR (inside BOOK6-COMPARE-SUBSTRATE-v0.2) — STANDS
v0.7 = NARROW GAP-6 TEMPORAL-ORDERING SUCCESSOR
```

**This plan does not reopen GAP-1..GAP-5.** It adds GAP-6 and nothing else.

**Grants implementation authority:** `FALSE`

---

## 1. Scope — unchanged, still 2

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

GAP-6 adds a **definition inside the selector's derivation semantics**. It adds
no public class, no registry, no ratification authority, no record field, and no
`WindowClass`.

---

## 2. The six resolutions

| Gap | Resolution | Status | Reopened by v0.7? |
|---|---|---|---|
| GAP-1 | `1A-STRICT` | CLOSED / ratified | **NO** |
| GAP-2 | `2D SAME_METRIC_EXACT_UNIT_IDENTITY` | CLOSED / ratified | **NO** |
| GAP-3 | `3C COVERAGE_RULE_PRESENCE_DERIVATION` | CLOSED / ratified | **NO** |
| GAP-4 | `4D EXPLICIT_TEMPORAL_COMPARABILITY` | CLOSED / ratified | **NO** |
| GAP-5 | `5E COMPARISON_RULE_OWNED_BASELINE_SELECTOR` | CLOSED / ratified | **NO** |
| **GAP-6** | **`6E WINDOW_CLASS_AWARE_ORDERING_KEYS`** | **PROPOSED / NOT RATIFIED** | new |

```text
GAP_6_IS_NEW                    = TRUE
GAP_1..GAP_5_REOPENED           = FALSE
SUBSTRATE_RATIFICATION_REVERSED = FALSE
```

### 2.1 Why GAP-6 is new and not a GAP-5 regression

GAP-5 (`5E`) closed **who owns baseline selection**: it bound the selector inside
`ComparisonRule` and retired the phantom benchmark namespace. It did not specify
the ordering **keys**. v0.6 §2.4 specified those keys assuming interval fields,
which is sound only for the nine interval window classes.

GAP-6 is therefore a distinct defect in a distinct clause, discovered by an
independent readiness re-run (`..._AUTHORIZATION_REVIEW_v0.4.md`), not by
reopening GAP-5.

---

## 3. What v0.7 changes in the plan

| v0.6 plan section | v0.7 status |
|---|---|
| §1 scope (count 2) | carried unchanged |
| §2 the five resolutions | extended with GAP-6 (additive) |
| §3 baseline selection (5E) | carried; ordering sub-clause now points at grammar v0.7 §1 |
| §4 replay — 20 checks | carried; check count unchanged |
| §5 contract count | carried unchanged (still 2) |
| §6 D6M decision impact | carried unchanged |
| §7 StateRule benchmark out of scope | carried unchanged |
| §8 gates G-1..G-15 | carried; **G-16..G-19 added** (below) |
| §9 status | superseded by §6 below |

### 3.1 New GAP-6 gates

```text
G-16 no window_start / window_end is ever populated or written by the selector;
     INSTANTANEOUS observations carry none (accepted model unchanged)
G-17 effective ordering keys are derived and discarded; they never persist onto
     MeasurementObservation and no new temporal contract exists
G-18 OLD_INTERVAL_ORDERING_RESULT == NEW_EFFECTIVE_KEY_ORDERING_RESULT on
     identical interval fixtures
G-19 eligibility (authority, record state, missingness, window class) is fully
     applied BEFORE ordering; the lexical tie-break never sees an ineligible
     candidate
```

`G-15 FAILURE OF ANY GATE = HOLD` carries forward and now covers G-16..G-19.

---

## 4. Replay — still 20 checks

```text
REPLAY_CHECK_COUNT                 = 20
ALL_20_INDEPENDENTLY_FALSIFIABLE   = TRUE
AGGREGATE_ONLY                     = REJECTED
```

Checks 5 and 6 are unchanged in name and wording. What changes is that they are
now **implementable for every eligible window class**; before GAP-6, check 6 had
no defined resolution for `WindowClass.INSTANTANEOUS`.

---

## 5. Test contract — carried plus TIME group

```text
TEST_SPEC_v0.3 CASES = 237  (ALL CARRIED FORWARD UNCHANGED)
TEST_SPEC_v0.4 CASES = 237 + 15 = 252
TIME_CASES_ADDED     = 15   (TIME-1 .. TIME-15)
TEST_SPEC_BLOCKED    = 0
```

No prior case is edited, renumbered, or removed. The TIME group is purely
additive and covers the GAP-6 surface. Full enumeration in
`CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md`.

```text
REGRESSION_BASELINES_UNCHANGED = TRUE   (1341 Book 6 / 2162 CSIA / 2343 Sensor)
```

---

## 6. Standing conditions — unchanged by v0.7

```text
SELECTOR_AGGREGATES = FALSE
```

If metric aggregation semantics cannot yield a single comparable value from a
selected window, implementation must HOLD that runtime case and surface a
concrete operator decision. **GAP-6 does not authorize aggregation.**

```text
CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED
CLASS_C_BENCHMARK_GOVERNANCE    = DEFERRED
CLASS_C_BENCHMARK_BLOCKS_ANYTHING_HERE = FALSE

ROLLING_MEAN / ROLLING_MEDIAN / HISTORICAL_DISTRIBUTION / BASELINE_EPOCH
    = RESERVED_NOT_EXECUTABLE
```

Both remain untouched by this plan.

---

## 7. D6M decision impact — none

The standing D6M items (`D6M_1..D6M_5`) are unchanged. GAP-6 resolves a
temporal-ordering determinism question; it does not alter any open D6M decision
and closes none of them.

```text
D6M_ITEMS_CLOSED_BY_GAP_6 = 0
D6M_ITEMS_CHANGED_BY_GAP_6 = 0
```

---

## 8. Status

```text
PLAN = v0.7 DRAFT_PENDING_OPERATOR_RATIFICATION

GAP_6     = 6E PROPOSED / NOT RATIFIED
GAP_1..5  = CLOSED / UNCHANGED / NOT REOPENED
SUBSTRATE_RATIFICATION = STANDS

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**Not authorized and not performed:** any implementation; any source or test
change; any change to `MeasurementObservation`; any fabricated interval; any
one-day convention; any exclusion of `INSTANTANEOUS`; any `observed_at` or
caller-order ordering; any window-class coercion; any aggregation invention; any
reopening of GAP-1..GAP-5; any reversal of `BOOK6-COMPARE-SUBSTRATE-v0.2`.

---

*Companions: instantaneous ordering clarification v0.1; grammar v0.7; test spec
v0.4.*
