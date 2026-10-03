# CSIA — BOOK 6 COMPARISON / CHANGE GRAMMAR — v0.7

**Document ID:** CSIA-B6-CG-007
**Version:** 0.7
**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-03
**Supersedes:** `..._GRAMMAR_v0.6.md` — which **was ratified**, inside the
substrate successor package `BOOK6-COMPARE-SUBSTRATE-v0.2`. This version does
not reverse that ratification; it removes the one clause of it that review v0.4
found not implementable. See §0.2.

**Preserved history — none of these are edited:**
- `..._GRAMMAR_v0.4.md` — RATIFIED, UNCHANGED, IN FORCE
- `..._GRAMMAR_v0.5.md` — draft, never ratified
- `..._GRAMMAR_v0.6.md` — ratified **as written** within
  `BOOK6-COMPARE-SUBSTRATE-v0.2`; §2.4 of it is superseded **prospectively** by
  §2.4 of this document. The defect it contained is corrected forward, never
  retroactively.

**Authority under:** `BOOK6-COMPARE-SUBSTRATE-v0.2` (RATIFIED, STANDS);
boundary v0.4; instantaneous ordering clarification v0.1 (draft).

**This document grants no implementation authority.**

---

## 0. Delta from v0.6

```text
SECTIONS_CHANGED        = 1
SECTIONS_CARRIED_FORWARD = ALL OTHERS, VERBATIM
SCOPE                   = BASELINE TEMPORAL ORDERING ONLY
```

### 0.1 Carry-forward table

| v0.6 section | title | v0.7 status |
|---|---|---|
| §0.1 | phantom language removed | carried unchanged |
| §0.2 | carried forward from v0.5 | carried unchanged |
| §0.3 | repaired doctrine wording | carried unchanged |
| §1 | canonical law | carried unchanged |
| §1.6 | baseline-selection firewall | carried unchanged |
| §2.1 | coverage applicability | carried unchanged |
| §2.2 | `BaselineSelectorSpec` | carried unchanged |
| §2.3 | `PRIOR_COMPARABLE_WINDOW` eligibility | carried unchanged |
| **§2.4** | **deterministic ordering** | **REPLACED — see §1 below** |
| §2.5 | no eligible baseline | carried unchanged |
| §2.6 | multiple eligible baselines | carried unchanged |
| §2.7 | fingerprint | carried unchanged |
| §2.8 | ratification binding | carried unchanged |
| §3 | `ChangeObservation` | carried unchanged |
| §3.1 | authority replay | carried unchanged |
| §3.2 | caller authority | carried unchanged |
| §4 | separations | carried unchanged |
| §5 | authority replay — twenty checks | carried; §5.2/§5.3 annotated |
| §5.4 | check 19/20 separability | carried unchanged |
| §6 | `AC-17` single-meaning absence | carried unchanged |
| §7 | `AC-18` policy is not authority | carried unchanged |
| §8.1 | nullable fields | carried; **annotated** (§3 below) |
| §8.2 | policy parameters | carried unchanged |
| §8.3 | baseline selector inventory | carried unchanged |
| §8.4 | StateRule benchmark separation | carried unchanged |
| §9 | ownership boundary | carried unchanged |
| §10 | contract-class audit | carried unchanged |
| §11 | status | superseded by §4 below |

**No other design change.** GAP-1 through GAP-5 semantics are untouched and are
not reopened by this version.

### 0.2 Relationship to the ratified v0.6

v0.6 is **RATIFIED** (`BOOK6-COMPARE-SUBSTRATE-v0.2`, commit
`18ddfa2805ef8b51a1c46d5f11a34689a6abfd1b`) and that ratification **stands**.
Review v0.4 found §2.4 of v0.6 not implementable for
`WindowClass.INSTANTANEOUS`; that is a readiness verdict, not a reversal.

```text
SUBSTRATE_RATIFICATION_REVERSED = FALSE
GAP_1..GAP_5_REOPENED          = FALSE
CORRECTION_MODE                = PROSPECTIVE
V0_6_ARTIFACT_EDITED           = NO  (historical record preserved)
```

A ratified artifact is not edited in place. v0.6 stays exactly as ratified, and
this successor carries the corrected ordering. The same discipline the phantom
benchmark correction used in v0.6 §0.1 applies here.

---

## 1. §2.4 Deterministic ordering (NORMATIVE — replaces v0.6 §2.4)

### 1.1 Derived ordering keys

```text
effective_end(o), effective_start(o) are DEFINED as:

    if o.window_class in INTERVAL_WINDOW_CLASSES:
        effective_end(o)   := o.window_end
        effective_start(o) := o.window_start
    else:                        # the single non-member: INSTANTANEOUS
        effective_end(o)   := o.valid_time
        effective_start(o) := o.valid_time
```

The projection is **total** over the closed `WindowClass` enum. There is no
third branch. An unrecognised window class is a fail-closed error; it must never
fall through to a default.

```text
ORDERING_KEYS_ARE_DERIVED = TRUE
OBSERVATION_MUTATION      = FALSE
NEW_RECORD_FIELD          = NONE
NEW_TEMPORAL_CONTRACT     = NONE
SYNTHETIC_ZERO_WIDTH_INTERVAL = FALSE
ONE_DAY_CONVENTION        = FALSE
```

### 1.2 The ordering rule

```text
 1. greatest effective_end(candidate),
      strictly before effective_start(comparison)
 2. if tied on effective_end: greatest effective_start(candidate)
 3. if still tied: stable lexical measurement_ref   (FINAL tie-break ONLY)
```

```text
BASELINE_SELECTION_DETERMINISTIC     = TRUE
CALLER_ORDER_AFFECTS_BASELINE        = FALSE
OBSERVED_AT_USED_FOR_ORDERING        = FALSE
INGESTION_TIME_USED_FOR_ORDERING     = FALSE
RANDOM_SELECTION                     = FALSE
LEXICAL_TIEBREAK_ONLY_AFTER_TEMPORAL_TIE = TRUE
```

### 1.3 Strict precedence

```text
eligible requires:  candidate.effective_end <  comparison.effective_start
                     STRICT `<`, never `<=`

STRICT_TEMPORAL_PRECEDENCE = TRUE
```

Strict `<` is what makes *prior* mean prior, and it prevents one instant or one
window boundary serving as both baseline and comparison.

For an instantaneous pair the test collapses to
`candidate.valid_time < comparison.valid_time`. That collapse is intended, and
it is what makes `candidate.valid_time == comparison.valid_time` correctly
**ineligible**.

### 1.4 Invariance on the interval path

For interval observations §1.1 is the identity, so §1.2 reduces **exactly** to
the v0.6 rule:

```text
OLD_INTERVAL_ORDERING_RESULT == NEW_EFFECTIVE_KEY_ORDERING_RESULT
    for identical interval fixtures            REQUIRED
INTERVAL_PATH_CHANGED = FALSE
```

### 1.5 Ordering is downstream of eligibility

```text
AUTHORITY_AND_RECORD_ELIGIBILITY -> ORDERING      (never the reverse)
```

§2.3 eligibility (carried unchanged from v0.6) must be **fully satisfied**
before §1.2 is evaluated. The lexical tie-break in §1.2 step 3 operates only on
observations that already passed every gate, so a `SUPERSEDED` record is removed
before it can be ranked. Ordering never rescues an ineligible candidate.

Record-state gate, over accepted fields only:

```text
eligible requires: observation.status is ObservationStatus.OBSERVED
```

Verified surface: `ObservationStatus` (`book6_grammar.py:264-272`), `status`
(`book6_records.py:129`), `supersedes_measurement_id` (`book6_records.py:130`).
Accepted source has **no** observation currency resolver — unlike
`methodology_is_current()` (`book6_methodology.py:332`). The gate is therefore
ratified as a **condition over the existing enum**, adding no helper and no
contract class.

### 1.6 Mixed temporal shapes

§2.3 condition 8 plus `validate_against_definition()` (`book6_records.py:231`,
window-class assertion at `:251-256`) already bind one `WindowClass` per bound
`MetricDefinition`. Should a candidate and comparison nonetheless fail to resolve
to the same bound definition:

```text
candidate -> STRUCTURALLY INELIGIBLE
comparison -> NOT_COMPARABLE  (existing temporal comparability law)

ORDERING_ACROSS_INCOMPATIBLE_TEMPORAL_SHAPES = NEVER
WINDOW_CLASS_CONVERSION            = FALSE
INSTANTANEOUS_TO_INTERVAL_COERCION = FALSE
INTERVAL_TO_INSTANTANEOUS_COERCION = FALSE
```

---

## 2. Annotations to carried-forward sections

These sections carry their v0.6 text **unchanged**; the notes below say only how
GAP-6 interacts with them. No text in v0.6 is altered.

### 2.1 §2.3 eligibility — unchanged

All eleven v0.6 eligibility conditions stand. GAP-6 adds none and removes none.

```text
GAP_6_ELIGIBILITY_CHANGES = 0
```

Two conditions are load-bearing for GAP-6 and are called out here so no one reads
them as sufficient on their own:

- condition 8 (compatible `WindowClass`) — the reason mixed shapes cannot arise
  inside one `ComparisonRule` (§1.6 above)
- condition 9 (`valid_time` strictly precedes) — under §1.3 this is evaluated on
  **effective** keys, not on `valid_time` directly

### 2.2 §5.2 / §5.3 replay checks — unchanged, now implementable

```text
check 5 = deterministic baseline candidate eligibility
check 6 = deterministic PRIOR_COMPARABLE_WINDOW resolution
```

v0.6 defined these checks but they were **not implementable** for
`WindowClass.INSTANTANEOUS`, because check 6 had no defined resolution. §1.1–§1.2
supplies that resolution. Check 19 / check 20 separability (§5.4) is unaffected.

```text
REPLAY_CHECK_COUNT          = 20   (unchanged)
AGGREGATE_ONLY              = REJECTED   (unchanged)
ALL_20_INDEPENDENTLY_FALSIFIABLE = TRUE
```

### 2.3 §8.1 nullable inventory — annotated

`window_start` and `window_end` are nullable **by accepted design**, not by
oversight, and their nullability is gated: required for the nine interval
classes, forbidden for `INSTANTANEOUS` (`book6_records.py:159-179`). GAP-6 reads
that gate; it does not change it.

```text
NULLABLE_FIELDS_CHANGED = 0
MEASUREMENT_OBSERVATION_CONTRACT = UNCHANGED
```

### 2.4 §10 contract-class audit — unchanged outcome

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE
```

The derived ordering keys are **not** a third class. They are a definition inside
the already-ratified selector's derivation semantics.

---

## 3. Unchanged invariants — restated for completeness

```text
CANONICAL_VALUE            = FINITE_STORED_BINARY64        (GAP-1, 1A-STRICT)
TEMPORAL_UNIT_COMPATIBILITY = SAME_METRIC_EXACT_UNIT_IDENTITY  (GAP-2, 2D)
CAN_DERIVE_NOT_APPLICABLE  = FALSE                          (GAP-3, 3C)
TemporalComparabilityStatus = COMPARABLE | NOT_COMPARABLE | UNRESOLVED  (GAP-4, 4D)
BASELINE_SELECTOR_AUTHORITY = BOUND_INSIDE_COMPARISON_RULE  (GAP-5, 5E)

ACCEPTED_BENCHMARK_RULE_NAMESPACE = FALSE
BENCHMARK_RULE_RUNTIME            = NOT_IMPLEMENTED
BENCHMARK_RULES_RATIFIED         = 0
EXECUTABLE_BASELINE_SELECTOR_COUNT = 1
EXECUTABLE_BASELINE_SELECTOR     = PRIOR_COMPARABLE_WINDOW
ROLLING_MEAN / ROLLING_MEDIAN / HISTORICAL_DISTRIBUTION / BASELINE_EPOCH
                                  = RESERVED_NOT_EXECUTABLE
SELECTOR_AGGREGATES              = FALSE
NO_ELIGIBLE_PRIOR_BASELINE       -> INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
COVERAGE_INFLUENCES_BASELINE_SELECTION = FALSE
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
```

---

## 4. Status

```text
GRAMMAR = v0.7 DRAFT_PENDING_OPERATOR_RATIFICATION

GAP_6 = 6E PROPOSED / NOT RATIFIED
GAP_1..GAP_5 = CLOSED / UNCHANGED / NOT REOPENED
SUBSTRATE_RATIFICATION = STANDS

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**Not authorized and not performed:** any implementation; any source or test
change; any change to `MeasurementObservation`; any fabricated interval; any
one-day convention; any exclusion of `INSTANTANEOUS`; any `observed_at` or
caller-order ordering; any window-class coercion; any aggregation invention;
any reopening of GAP-1 through GAP-5; any reversal of
`BOOK6-COMPARE-SUBSTRATE-v0.2`.

---

*Companion: `CSIA_BOOK_6_COMPARISON_CHANGE_INSTANTANEOUS_ORDERING_CLARIFICATION_v0.1.md`.*
