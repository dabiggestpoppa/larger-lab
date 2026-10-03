# CSIA — Book 6 Comparison/Change: Instantaneous Ordering Clarification v0.1

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-03
**Proposes:** `GAP-6 = 6E WINDOW_CLASS_AWARE_ORDERING_KEYS`
**Scope:** ONE defect. One clause. Nothing else.
**Grants implementation authority:** `FALSE`

```text
GAP_6_IS_NEW                  = TRUE
GAP_1..GAP_5_REOPENED         = FALSE
SUBSTRATE_RATIFICATION_REVERSED = FALSE

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 1. GAP-6 reproducer

### 1.1 What the defect is NOT

```text
NOT missing valid time
NOT missing window class
NOT missing runtime temporal fields
```

All three exist and work. The defect is narrower and specific:

> **the selector's ratified ordering assumes interval-only fields for all
> eligible observations.**

### 1.2 Verified accepted-runtime facts

All re-verified against `agent/crypto-systems-intelligence-atlas-book6-build`
@ `5f94c3f40cea4441470c57671f51454da7377361`:

| # | Fact | Anchor |
|---|------|--------|
| 1 | `valid_time: datetime` — **required**, no default | `book6_records.py:117` |
| 2 | `window_start: datetime \| None = None` — nullable | `book6_records.py:120` |
| 3 | `window_end: datetime \| None = None` — nullable | `book6_records.py:121` |
| 4 | interval windows: both bounds **required**, `start < end` | `book6_records.py:160-168` |
| 5 | `INSTANTANEOUS`: both bounds **must be absent** | `book6_records.py:169-175` |
| 6 | `INSTANTANEOUS` is the **default** in both canonical fixtures | `book6_support.py:356`, `:393` |
| 7 | same-class window comparison is permitted | `book6_normalization.py:377-390` |
| 8 | ratified ordering keys on END then START then lexical ref | grammar v0.6 §2.4 |

```text
INTERVAL_WINDOW_CLASSES @ book6_grammar.py:185-199
    9 of 10 WindowClass members
    the single excluded member is INSTANTANEOUS @ book6_grammar.py:171
```

### 1.3 The consequence

Facts 1–8 together: for a `WindowClass.INSTANTANEOUS` observation, `window_end`
and `window_start` are `None` **by validator**, so ratified ordering keys 1 and 2
have **no value**. Only key 3 (lexical `measurement_ref`) is defined. The
ordering is therefore undefined exactly where the runtime's default window class
lives.

### 1.4 Mechanical reproduction

`tools/csia_grounding_check.py` re-derives this from the AST, with no hand
reading:

```text
[HIGH] R5_REACHABLE_EXCLUDED_MEMBER  MeasurementObservation.window_end
  - excluded from INTERVAL_WINDOW_CLASSES @ book6_grammar:185:
      WindowClass has 10 members, 1 excluded member
  - constructible by default (TYPED): windowed_observation() @ book6_support:384
  - reachable (UNTYPED): check_windows_comparable() @ book6_normalization:377
      fails closed only on inequality
  - no ratified artifact mentions WindowClass.INSTANTANEOUS
```

---

## 2. Rejected resolutions, and why

`6E` was selected by operator direction. The alternatives are recorded so the
choice is auditable, and so nobody re-proposes them as if they were open.

| Option | Rejected because |
|---|---|
| **A** zero-width `[valid_time, valid_time)` | fabricates an interval the accepted model forbids; contradicts `start < end` discipline |
| **B** one-day `[valid_time, valid_time + 1day)` | invents a day of width for an instantaneous measurement; `book6_support.py:419` uses that span only as a **fixture** convenience, never as ratified semantics |
| **C** exclude `INSTANTANEOUS` from baseline selection | blanket exclusion of the runtime's **default** window class; a large semantic narrowing with no ratified basis |
| **D** refuse all instantaneous temporal comparison | refuses a case the accepted kernel treats as ordinary |

```text
INSTANTANEOUS_REMAINS_POINT        = TRUE
SYNTHETIC_ZERO_WIDTH_INTERVAL      = FALSE
ONE_DAY_CONVENTION                 = FALSE
BLANKET_EXCLUSION_OF_INSTANTANEOUS = FALSE
BLANKET_REFUSAL_OF_INSTANTANEOUS   = FALSE
```

**6E** fabricates nothing, excludes nothing, and refuses nothing. It supplies a
projection so the ordering has a defined value on every eligible observation.

---

## 3. The ordering projection

### 3.1 Definition — selector-local derived keys

```text
For o in INTERVAL_WINDOW_CLASSES:
    effective_end(o)   = o.window_end
    effective_start(o) = o.window_start

For o == WindowClass.INSTANTANEOUS:
    effective_end(o)   = o.valid_time
    effective_start(o) = o.valid_time
```

```text
ORDERING_KEYS_ARE_DERIVED = TRUE
OBSERVATION_MUTATION      = FALSE
STORED_BACK_ONTO_RECORD   = FALSE
NEW_TEMPORAL_CONTRACT     = NONE
```

These are **derived, selector-local keys**. They are computed at selection time
and discarded afterwards. They are not fields, not properties on
`MeasurementObservation`, not a new temporal contract, and not a change to the
accepted record.

### 3.2 The projection is total and needs no default branch

Every `WindowClass` member is either in `INTERVAL_WINDOW_CLASSES` (9 of 10) or
is `INSTANTANEOUS` (the 1 remainder). There is no third case, so the projection
is **total over the closed enum**. Implementation must not add an "else" arm with
a fallback value; an unrecognised window class is a fail-closed error, not a
default.

### 3.3 Why deriving is not fabricating

The prohibition is against inventing a *temporal fact* about the measurement.
`effective_end == effective_start == valid_time` for an instantaneous observation
asserts nothing new about the record: it says that a point occupies the
interval `[t, t]`, which is true of every point, and the accepted model already
carries `valid_time` as that point. No interval field is created, populated, or
implied on the record.

The distinction matters because option **B** would assert something *false*: that
an instantaneous measurement spans a day.

---

## 4. Ordering and precedence

### 4.1 Priority order (ratified v0.6 order, generalized)

```text
1. greatest effective_end(candidate), strictly before effective_start(comparison)
2. if tied on effective_end: greatest effective_start(candidate)
3. if still tied: stable lexical measurement_ref   (FINAL tie-break ONLY)
```

```text
CALLER_ORDER_AFFECTS_BASELINE     = FALSE
OBSERVED_AT_USED_FOR_ORDERING     = FALSE
INGESTION_TIME_USED_FOR_ORDERING  = FALSE
RANDOM_SELECTION                  = FALSE
```

`observed_at` is **knowledge time**; `valid_time` is the **economic/semantic
axis**. This is a temporal-selection rule, not a bitemporal rewrite. Nothing in
GAP-6 touches how observations are recorded, only how a prior baseline is picked
among eligible ones.

### 4.2 Strict precedence

```text
eligible requires:  candidate.effective_end < comparison.effective_start
                     (strict <, never <=)

STRICT_TEMPORAL_PRECEDENCE = TRUE
```

Strict `<` preserves *prior means prior* and prevents the same instant or window
boundary being selected as both baseline and comparison.

### 4.3 Collapse for instantaneous pairs

When both sides are instantaneous, the projection reduces the precedence test to:

```text
candidate.valid_time < comparison.valid_time
```

which is the intended reading, not an accident. Consequences, both ratified:

- `t3.valid_time < t4.valid_time` ⇒ `t3` is eligible for comparison `t4`
- `t4.valid_time == t4.valid_time` ⇒ **not** eligible (TIME-6)
- two candidates sharing a `valid_time` tie on both derived keys and fall
  through to the lexical tie-break

---

## 5. Window-class compatibility

### 5.1 What "compatible WindowClass" already means

Eligibility condition 8 ("same required WindowClass / window compatibility") is
already enforced by accepted runtime: `validate_against_definition()`
(`book6_records.py:231`) raises when

```python
if observation.window_class is not definition.window_class:   # :251-256
```

So for one `ComparisonRule`, one bound `MetricDefinition` fixes the
`WindowClass` for both baseline and comparison observations. Mixed shapes are
already structurally impossible inside a single rule.

```text
WINDOW_CLASS_CONVERSION               = FALSE
INSTANTANEOUS_TO_INTERVAL_COERCION    = FALSE
INTERVAL_TO_INSTANTANEOUS_COERCION    = FALSE
WINDOW_CLASS_ADDED                    = NONE
```

### 5.2 Mixed-shape defense

Even though §5.1 should make mixed shapes impossible, the negative cases are
ratified explicitly:

```text
if candidate and comparison do not resolve to the same bound
   MetricDefinition / WindowClass:
        candidate is STRUCTURALLY INELIGIBLE
        and the comparison is NOT_COMPARABLE
        under the existing temporal comparability law

ORDERING_ACROSS_INCOMPATIBLE_TEMPORAL_SHAPES = NEVER
```

The selector must not derive an ordering across incompatible temporal shapes. It
does not coerce one into the other, and it does not pick "the closest" shape.

---

## 6. Eligibility precedes ordering

```text
AUTHORITY_AND_RECORD_ELIGIBILITY -> ORDERING
NOT the reverse.
```

The ordering rule may only rank observations that have **already passed** every
eligibility gate. Gates include Book 2 authority currency, methodology
identity/currentness, missingness, and record state. Ordering never rescues an
ineligible candidate and never ranks first and filters after.

### 6.1 Supersession — the stress case

Two measurements for the same metric and the same `valid_time`, one superseding
the other, is precisely where a lexical tie-break could accidentally resurrect a
dead record. The ratified order of operations prevents it: the superseded
observation is removed by the **eligibility** gate before ordering is reached,
so the lexical tie-break never sees it.

**Accepted-runtime surface, verified at `5f94c3f4`:**

| Element | Anchor | State |
|---|---|---|
| `ObservationStatus.OBSERVED / SUPERSEDED` | `book6_grammar.py:264-272` | present |
| `status: ObservationStatus = OBSERVED` | `book6_records.py:129` | present |
| `supersedes_measurement_id: str \| None` | `book6_records.py:130` | present |
| a currency resolver (e.g. `observation_is_current()`) | — | **ABSENT** |

```text
RECORD_STATE_FIELDS_PRESENT = TRUE
RECORD_STATE_RESOLVER_ABSENT = TRUE
NO_BLOCKER = TRUE
```

**This is recorded as a surface fact, not concealed.** The fields and the enum
exist and are typed, so the gate is a condition over accepted state:

```text
eligible requires: observation.status is ObservationStatus.OBSERVED
```

By contrast `Book6MethodologyRegistry.methodology_is_current()`
(`book6_methodology.py:332`) exists for methodologies — the observation analogue
does not. GAP-6 therefore ratifies the **condition**, not a new helper, and adds
no contract class. No precedence is invented: `SUPERSEDED` is excluded because
it is not current, not because it sorts lower.

---

## 7. Invariance of the interval path

For interval observations the projection is an identity:

```text
effective_end(o)   = o.window_end
effective_start(o) = o.window_start
```

so the three-step rule reduces **exactly** to the ratified v0.6 rule.

```text
OLD_INTERVAL_ORDERING_RESULT == NEW_EFFECTIVE_KEY_ORDERING_RESULT
    for identical interval fixtures            REQUIRED
INTERVAL_PATH_CHANGED = FALSE
```

This is testable as an equivalence over identical fixtures (TIME-7), and it is
the reason GAP-6 is safe to apply across the whole selector rather than only to
the instantaneous branch.

---

## 8. Authority and contract count

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
    ComparisonRule
    ChangeObservation

BaselineSelectorSpec        = nested value object, not a third class
TemporalComparabilityStatus = closed enum field, not a third class
Ordering projection         = SELECTOR-LOCAL DERIVED KEYS, not a class

HIDDEN_THIRD_CONTRACT = NONE
NEW_RECORD_FIELD = NONE
NEW_REGISTRY = NONE
NEW_RATIFICATION_AUTHORITY = NONE
NEW_WINDOW_CLASS = NONE
```

GAP-6 adds **no** public surface. It adds a definition inside the already-ratified
selector's derivation semantics.

---

## 9. Carried-forward standing conditions — unchanged

```text
SELECTOR_AGGREGATES = FALSE
```

If metric aggregation semantics cannot yield a single comparable value from a
selected window, implementation must **HOLD that runtime case** and surface a
concrete operator decision. **GAP-6 does not authorize aggregation.**

Class C remains `DEFERRED / UNIMPLEMENTED / NOT A BLOCKER`. Reserved selectors
remain `RESERVED_NOT_EXECUTABLE`. Neither is affected by GAP-6.

---

## 10. What this clarification does not do

```text
IMPLEMENTATION                    = NONE
SOURCE_CHANGE                     = NONE
TEST_CODE                         = NONE
MEASUREMENTOBSERVATION_CONTRACT   = UNCHANGED
REOPENED_GAPS                     = NONE   (GAP-1..GAP-5 stand as ratified)
SUBSTRATE_RATIFICATION            = STANDS
CLASS_C_DESIGN                    = NONE
AGGREGATION_INVENTION             = NONE
```

---

## 11. Status

```text
GAP_6 = 6E PROPOSED / NOT RATIFIED
STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

Ratifying this clarification would resolve GAP-6 and permit the readiness
re-run to be re-evaluated against a complete substrate. It still would not
authorize implementation.

---

*Next: grammar v0.7 (baseline temporal ordering only), plan v0.7, test spec
v0.4, pre-ratification review, authorization review v0.5.*
