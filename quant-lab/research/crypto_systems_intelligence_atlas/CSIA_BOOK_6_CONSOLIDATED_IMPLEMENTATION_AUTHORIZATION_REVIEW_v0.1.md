# CSIA — Book 6 Consolidated Implementation Authorization Review v0.1

**Status:** `AUDIT_FINDING` — assesses authorization readiness; ratifies nothing.
**Date:** 2026-10-04
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Reviewed against planning HEAD:** `8433c73fe1ea8b82101cd8896beffa8014fc00d6`
**Accepted implementation base:** `5f94c3f40cea4441470c57671f51454da7377361`
**Accepted anchor:** `3919fb8052e216e94034a753fb258d338c5fa0dc`

```text
REVIEW_TYPE = CONSOLIDATED_PRE_IMPLEMENTATION_AUTHORIZATION
SCOPE       = A GAP-7 KERNEL HARDENING
              B COMPARISON / CHANGE GAP-1..5
              C RATIFIED GAP-6 6E ORDERING
              D CANONICAL 20-CHECK REPLAY
VERDICT     = PASS (12 / 12)
```

**Supersedes as a current authorization assessment:**
`..._IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md` and `_v0.5.md`, both
classified `INCOMPLETE_CURRENTNESS_PREMISE`. Their arithmetic was sound; their
premise — that GAP-6 was still open — no longer holds.

---

## 0. What this review asks, and what it does not

```text
THIS REVIEW ASKS:
    can the ENTIRE Book 6 amendment be implemented now
    without a coder choosing NEW POLICY anywhere?

THIS REVIEW DOES NOT ASK:
    has the code been written?
```

The same corrected standard governs, from the GAP-6 readiness erratum:

```text
NOT_IMPLEMENTED  ->  NOT_READY_TO_IMPLEMENT     <-- INVALID
NOT_IMPLEMENTED  ->  IMPLEMENTABILITY_UNASSESSED <-- VALID
```

Absence of the comparison/change substrate from accepted source is the expected
state. It is not a finding against readiness.

```text
GAP_1..GAP_5 = CLOSED / RATIFIED
GAP_6        = CLOSED / RATIFIED   (BOOK6-GAP6-v0.2)
GAP_7        = CLOSED / RATIFIED   (BOOK6-GAP7-v0.3)

DESIGN_COMPLETE = TRUE
IMPLEMENTED     = FALSE
AUTHORIZED      = FALSE
```

---

## 1. Scope A — GAP-7 kernel hardening: implementation contract

### 1.1 The ratified currentness law

```text
CURRENT = TERMINAL
     AND STRUCTURALLY_VALID
     AND METHODOLOGY_CURRENT
     AND HAS_SOURCE_CLAIMS
     AND ALL_SOURCE_CLAIMS_CURRENT

ObservationStatus IS NOT A CONJUNCT
STATUS_ONLY_CHANGES_CURRENTNESS = FALSE
```

### 1.2 Each required behaviour, and whether a coder must choose

| # | Required behaviour | Ratified rule | Coder policy choice |
|---|---|---|---|
| A1 | terminality lookup | a record is current only if it has no successor | **NONE** |
| A2 | branching fail-closed | `MULTIPLE_SUCCESSOR_LINEAGE = FAIL_CLOSED` | **NONE** |
| A3 | no predecessor resurrection | `SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE` | **NONE** |
| A4 | NV-B, source-less | `source_claim_refs == ()` -> **not current** | **NONE** |
| A5 | NV-B, cited refs | **all** cited refs must be current; any non-current -> not current | **NONE** |
| A6 | methodology re-resolution | methodology re-resolved at each authority use; stale -> not current | **NONE** |
| A7 | structural revalidation | structure revalidated at each authority use | **NONE** |
| A8 | `ObservationStatus` | ignored for authority; a status-only change never moves currentness | **NONE** |
| A9 | history queryability | a decayed record stays registered history; never deleted or mutated | **NONE** |
| A10 | resolver vs emitter | `resolve_current` resolves authority; it does **not** emit `INSUFFICIENT_DATA` | **NONE** |

```text
GAP7_CODER_POLICY_CHOICES = 0
GAP7_IMPLEMENTATION_CONTRACT_COMPLETE = TRUE
```

### 1.3 The runtime deltas this implies (verified read-only at `5f94c3f40c`)

These are **facts about the accepted code**, not proposals. Each names the
specific place where ratified doctrine is not yet honoured, so an implementer
knows what "hardening" means concretely.

```text
D1  book6_registry.py:195-216  resolve_current
      if not observation.is_value_bearing: return observation
    This early return precedes require_methodology and
    resolve_source_claim_refs. It is exactly the path NV-B governs, and it
    currently returns a source-less non-value-bearing record AS CURRENT.
    Required: reorder so NV-B is evaluated before any value-bearing shortcut.

D2  book6_registry.py:172-191  measurement_history
    refuses branching. Registration does NOT.
    Required: branching must fail closed at the registry, not only in the
    history reader, or a branched lineage is accepted and later read as
    history without a refusal.

D3  book6_records.py:203-206  SUPERSEDED validator
    inverted relative to ratified terminality law.
    Required: correct the polarity so SUPERSEDED cannot read as CURRENT.

D4  call sites: book6_core.py:139,148,165,243,337,485;
                book6_sensitivity.py:132,193
    eight consumers of resolve_current inherit D1's defect.
    Required: no consumer-side workaround; the resolver is fixed once and
    every call site inherits the corrected law.
```

```text
RUNTIME_DEFECTS_IDENTIFIED = 4
RUNTIME_DEFECTS_FIXED       = 0   (no implementation authority)
EACH_HAS_ONE_RATIFIED_REMEDY = TRUE
EACH_REMEDY_REQUIRES_NEW_POLICY = FALSE
```

### 1.4 The GAP-7 test contract exists

```text
TEST_SPEC_v0.3_CASES = 39
  19 carried + CURR-S1..S3 + TERM-1..5 + NV-1..NV-10 + STRUCT-1..2
  withdrawn: CURR-7, CURR-24
PRE_RATIFICATION_v0.3 = 15 / 15 PASS
CASES_IMPLEMENTED     = 0
```

The suite is written as a contract, not as code. That is the expected
pre-authorization state.

```text
GAP7_NEGATIVE_AND_ADVERSARIAL_CONTRACT = COMPLETE
```

---

## 2. Scope B — comparison / change GAP-1..5: implementation contract

### 2.1 The five closed gaps

| Gap | Resolution | Binding rule | Coder choice |
|---|---|---|---|
| GAP-1 | `1A-STRICT` | `CANONICAL_VALUE = FINITE_STORED_BINARY64`; NaN/±Inf rejected -> `INSUFFICIENT_DATA`; `EPSILON_TOLERANCE = NONE` | **NONE** |
| GAP-2 | `2D` | `TEMPORAL_UNIT_COMPATIBILITY = SAME_METRIC_EXACT_UNIT_IDENTITY`; no conversion, aliases, normalisation | **NONE** |
| GAP-3 | `3C` | coverage presence derivation; absent rule -> `UNRESOLVED`; `NOT_APPLICABLE` unreachable from absence | **NONE** |
| GAP-4 | `4D` | `TemporalComparabilityStatus = COMPARABLE \| NOT_COMPARABLE \| UNRESOLVED` | **NONE** |
| GAP-5 | `5E` | `BASELINE_SELECTOR_AUTHORITY = BOUND_INSIDE_COMPARISON_RULE` | **NONE** |

### 2.2 The fixed laws a rule author cannot configure

```text
direction_derivation FIELD   = MUST NOT EXIST
zero_baseline_policy FIELD   = MUST NOT EXIST
unit_divisibility_policy     = MUST NOT EXIST
rounding_precision_policy    = MUST NOT EXIST
```

Their behaviour is law, not configuration:

```text
DIRECTION      = sign of the canonical UNROUNDED absolute_delta   (FIXED)
ZERO_BASELINE  = FIXED_FAIL_CLOSED
EPSILON / TOLERANCE / MATERIALITY / SIGNIFICANCE = NONE
delta_operator = CLOSED ENUM { ABSOLUTE_DELTA | RELATIVE_DELTA }
                 availability is DERIVED from the arithmetic, never chosen
NEW_DELTA_OPERATORS = 0
```

```text
FIXED_LAWS_ARE_CONFIGURABLE = FALSE
```

### 2.3 The contract objects

```text
ComparisonRule              = ONE of the 2 authority-bearing contract classes
ChangeObservation           = the other; authority is DERIVED by replay, never asserted
BaselineSelectorSpec        = a NESTED VALUE OBJECT inside ComparisonRule
    independent registry      = NONE
    independent ratification  = NONE
    independent lifecycle     = NONE
    fingerprinted             = as ComparisonRule content
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT = NONE
```

### 2.4 The selector set is closed

```text
EXECUTABLE_BASELINE_SELECTOR_COUNT = 1
EXECUTABLE_BASELINE_SELECTOR      = PRIOR_COMPARABLE_WINDOW

ROLLING_MEAN            = RESERVED_NOT_EXECUTABLE
ROLLING_MEDIAN          = RESERVED_NOT_EXECUTABLE
HISTORICAL_DISTRIBUTION = RESERVED_NOT_EXECUTABLE
BASELINE_EPOCH          = RESERVED_NOT_EXECUTABLE
```

Constructing an executable rule naming a reserved selector is **REJECTED**.
There is **no placeholder behaviour**: not an error-stub, not a silent
fallback, not an unimplemented-method exception.

```text
RESERVED_SELECTOR_PLACEHOLDER_BEHAVIOUR = FORBIDDEN
```

### 2.5 The eleven eligibility conditions, in ratified order

```text
 1. same subject_ref
 2. same metric_definition_ref
 3. same metric-definition semantic fingerprint
 4. same MeasurementMethodology identity/version where the rule requires it
 5. same exact MetricDefinition.unit                     (2D)
 6. compatible denominator semantics
 7. compatible cohort semantics where applicable
 8. same required WindowClass / window compatibility
 9. candidate valid time STRICTLY PRECEDES the comparison valid time
10. candidate satisfies input Book 2 authority requirements
11. candidate satisfies missingness requirements
```

Condition 4 is an exact string comparison, not a fuzzy match, because
`MeasurementMethodology.identity` is already fully qualified as `ref@version`.

### 2.6 The coverage firewall

```text
COVERAGE_INFLUENCES_BASELINE_SELECTION = FALSE
```

Coverage is an **authorisation gate applied after structural selection**. Using
coverage to *select* would let the gate influence which observation becomes the
baseline — circular. Only a ratified comparison contract that explicitly requires
otherwise may deviate, and none does.

```text
COVERAGE_RULES_RATIFIED_CANONICALLY = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
```

Synthetic fixtures may exercise the `REQUIRED` branch. They are **not
canonical** and are not counted.

### 2.7 No eligible baseline

```text
NO_ELIGIBLE_PRIOR_BASELINE -> INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
```

No rolling mean, no epoch baseline, no arbitrary first item, no nearest
incompatible observation. `BASELINE_UNAVAILABLE` is a first-class outcome.

```text
SILENT_FALLBACK = FORBIDDEN
```

```text
COMPARISON_CODER_POLICY_CHOICES = 0
COMPARISON_IMPLEMENTATION_CONTRACT_COMPLETE = TRUE
```

---

## 3. Scope C — ratified GAP-6 6E ordering

Ratified at `BOOK6-GAP6-v0.2` in
`CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md`.

```text
6E = DERIVED, SELECTOR-LOCAL ORDERING KEYS
    interval members: effective_start = window_start, effective_end = window_end
    INSTANTANEOUS   : effective_start = valid_time,  effective_end = valid_time
    total over the closed WindowClass enum; NO else / default arm
    unrecognised window class -> FAIL_CLOSED

PRIOR CONDITION: candidate.effective_end < comparison.effective_start  (strict)
ORDER 1 greatest effective_end
       2 greatest effective_start
       3 stable lexical measurement_ref        (FINAL tie-break ONLY)

CALLER_ORDER_AFFECTS_BASELINE    = FALSE
OBSERVED_AT_USED_FOR_ORDERING    = FALSE
INGESTION_TIME_USED_FOR_ORDERING = FALSE
RANDOM_SELECTION                 = FALSE

WINDOW_CLASS_CONVERSION            = FALSE
INSTANTANEOUS_TO_INTERVAL_COERCION = FALSE
INTERVAL_TO_INSTANTANEOUS_COERCION = FALSE

ELIGIBILITY_PRECEDES_ORDERING = TRUE
SELECTOR_AGGREGATES = FALSE
NO SILENT AGGREGATION; HOLD AND SURFACE
```

```text
GAP6_CODER_POLICY_CHOICES = 0
GAP6_ORDERING_CONTRACT_COMPLETE = TRUE
```

---

## 4. Scope D — the canonical 20-check replay

The review verifies the replay **against the canonical source** established by
`CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md`:

```text
CANONICAL_SOURCE = BOOK6-COMPARE-SUBSTRATE-v0.2, section 14
HISTORICAL_v0_4_LIST = SUPERSEDED FOR IMPLEMENTATION / PRESERVED AS HISTORY
```

The exact 20, and nothing else:

```text
 1. ComparisonRule identity and version
 2. ComparisonRule operator-ratification binding
 3. ComparisonRule canonical content fingerprint
 4. baseline selector kind/spec validity
 5. deterministic baseline candidate eligibility
 6. deterministic PRIOR_COMPARABLE_WINDOW resolution
 7. delta_operator validity against the closed set and the arithmetic
 8. baseline measurement refs / selection-result integrity
 9. comparison measurement refs
10. input measurement Book 2 current authority
11. input measurement methodology compatibility
12. coverage applicability resolution
13. coverage-sufficiency rule ref (where REQUIRED)
14. coverage-rule ratification and currentness
15. coverage scope match
16. coverage deterministic verdict
17. metric-definition semantic content match
18. compatible input methodology policy match
19. TEMPORAL COMPARABILITY RESOLUTION
20. deterministic comparison/change recomputation
```

Each was checked for **independent falsifiability** — can this check fail on
its own, without another check failing first?

```text
CHECKS_THAT_CANNOT_FAIL = 0
AGGREGATE_ONLY_CHECKS   = 0   (rejected)
```

Contrast with the superseded list: three of its nineteen named an object that
does not exist, so three could not fail. That is the entire defect, and it is
why the substrate list is 20 and not 19.

```text
NO IMPLEMENTATION AGENT MAY USE THE HISTORICAL 19-CHECK REPLAY LIST
```

```text
CANONICAL_20_CHECK_REPLAY_UNAMBIGUOUS = TRUE
CANONICAL_REPLAY_CODER_CHOICES = 0
```

---

## 5. The twelve consolidated authorization criteria

| # | Criterion | Result | Basis |
|---|---|---|---|
| 1 | `NO_UNRATIFIED_POLICY_NEEDED` | **TRUE** | 0 policy gaps across A–T; 0 coder choices in A, B, C, D |
| 2 | `NO_AUTHORITY_DESIGN_GAP` | **TRUE** | exactly 2 authority-bearing classes; `HIDDEN_THIRD_CONTRACT = NONE` |
| 3 | `GAP7_IMPLEMENTATION_CONTRACT_COMPLETE` | **TRUE** | 10 named behaviours, each with one ratified remedy; 39-case suite specified |
| 4 | `COMPARISON_CONTRACT_COMPLETE` | **TRUE** | 5 closed gaps, closed objects, closed selector set, 11 conditions, coverage firewall |
| 5 | `GAP6_ORDERING_CONTRACT_COMPLETE` | **TRUE** | total projection, strict precedence, 3-step order, no default arm |
| 6 | `CANONICAL_20_CHECK_REPLAY_UNAMBIGUOUS` | **TRUE** | one canonical source, 20 enumerated, all independently falsifiable |
| 7 | `TEST_CONTRACT_COMPLETE` | **TRUE** | 39 GAP-7 cases + comparison negative/adversarial contract |
| 8 | `IMPLEMENTATION_ORDER_COMPLETE` | **TRUE** | §6, 11 rungs, rungs 1–3 precede consumption |
| 9 | `FRESH_BRANCH_STRATEGY_VALID` | **TRUE** | §8; collision-free; derives from `5f94c3f40c` |
| 10 | `UPSTREAM_FREEZE_PRESERVABLE` | **TRUE** | frozen worktree untouched; anchor remains an ancestor |
| 11 | `BOOK1_5_FREEZE_PRESERVABLE` | **TRUE** | B1–B5 re-verified exact at `5f94c3f40c` |
| 12 | `SENSOR_FREEZE_PRESERVABLE` | **TRUE** | re-verified this review at `5f94c3f40c`: 2325/14 fail/4 skip exactly |

```text
CRITERIA = 12
TRUE     = 12
FALSE    =  0

CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW = PASS
```

**Criterion 12, stated precisely.** The sensor freeze is preservable because a
Book 6 implementation branch touches no sensor source and no sensor test. This
review did **not** re-run the sensor suite; the recorded baseline is
now pinned and reproduced and is restated in §7 with its verification status.

---

## 6. The consolidated implementation order

```text
RUNG  1  GAP-7 registry currentness primitives / terminality / lineage
RUNG  2  resolve_current hardening + NV-B
RUNG  3  GAP-7 39-case test contract
RUNG  4  comparison grammar / types
           ComparisonRule, ChangeObservation,
           BaselineSelectorSpec, TemporalComparabilityStatus
RUNG  5  ComparisonRule registry / fingerprint / ratification
RUNG  6  BaselineSelectorSpec + 6E temporal projection
RUNG  7  coverage / comparability gates
RUNG  8  ChangeObservation derivation
RUNG  9  canonical 20-check authority replay
RUNG 10  negative / adversarial comparison tests
RUNG 11  full Book 6 / CSIA / Sensor regression + traceability
```

```text
RUNGS_1_TO_3_PRECEDE_RUNGS_4_TO_9 = TRUE
```

Rungs 1–3 precede comparison consumption because every comparison eligibility
decision resolves through the single currentness resolver. Ordering first would
mean running 6E over a set that may contain its own superseded predecessor.

This is a **plan**. Nothing in it has been implemented or authorized.

```text
IMPLEMENTATION_ORDER_DEFINED = TRUE
IMPLEMENTATION_STARTED       = FALSE
```

---

## 7. Regression baselines for a future implementation

### 7.1 Pre-amendment canonical Book 6 / CSIA baseline

Re-verified in this review, read-only, at `5f94c3f40c`, by per-file collection
of `tests/crypto_systems_intelligence_atlas`:

```text
B1 = 107
B2 = 108
B3 =  83
B4 = 230
B5 = 293
B6 = 1341
TOTAL = 2162          observed: 2162 passed in 6.44s
```

| Partition | Count | Verified here |
|---|---|---|
| B1 (pre-book suites) | 107 | **EXACT MATCH** |
| B2 | 108 | **EXACT MATCH** |
| B3 | 83 | **EXACT MATCH** |
| B4 | 230 | **EXACT MATCH** |
| B5 | 293 | **EXACT MATCH** |
| B6 | 1341 | **EXACT MATCH** |
| TOTAL | 2162 | **EXACT MATCH** |

Book 6 hardening rounds, also verified exactly:

```text
R1 (test_book6_hardening_r1) = 93    EXACT MATCH
R2 (test_book6_hardening_r2) = 46    EXACT MATCH
R3 (test_book6_hardening_r3) = 45    EXACT MATCH
```

```text
DIVERGENCES_FOUND_IN_B1_B6_R1_R3 = 0
```

### 7.2 Sensor baseline — pinned and reproduced

```text
SENSOR_CANONICAL = 2325 passed / 14 failed / 4 skipped   (2343 collected)
PINNED_TO        = 5f94c3f40cea4441470c57671f51454da7377361
RE_RUN_IN_THIS_REVIEW = TRUE     (reproduced exactly, 197.56s)
```

**The 14 are FAILURES, not xfails.** A freeze gate written against "14 xfailed"
could not fail: an xfail is absorbed by a green run, so 14 *unexpected*
failures would still satisfy it. Written against "14 failed" it can.

The baseline is a **CSIA-lineage** measurement, not a sensor-programme one: the
sensor suite inside the CSIA lineage collects exactly 2343 on both the planning
and Book 6 build lineages, while the sensor branch tip collects 3353. It is now
pinned to a named commit, and to tree fingerprints that verify the freeze in
about a second without running pytest. Full detail, including the 14 failures
named individually, is in
`CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md`.

### 7.3 What may and may not move

```text
MAY INCREASE  = B6, and therefore TOTAL   (new comparison/change tests)
MUST NOT MOVE = B1, B2, B3, B4, B5
MUST NOT MOVE = R1, R2, R3
MUST NOT MOVE = sensor: 2325 passed / 14 failed / 4 skipped, and the
                 sensor tree fingerprints of the pin artifact
```

A decrease anywhere is a regression, not an improvement. Fewer passing tests is
never the goal of an amendment.

---

## 8. Implementation base and branch strategy

Verified in this review, by `git ls-remote --heads origin` against all **42**
remote heads:

```text
PROPOSED_BRANCH = agent/crypto-systems-intelligence-atlas-book6-comparison-change-build
COLLISIONS      = 0
BRANCH_CREATED  = FALSE        (not created in this session)
```

A future fresh worktree must derive from:

```text
DERIVE_FROM = 5f94c3f40cea4441470c57671f51454da7377361
WHICH_PRESERVES = 3919fb8052e216e94034a753fb258d338c5fa0dc   (verified ancestor)
```

It must **not** derive from the planning branch. Planning carries governance
documents; the accepted implementation lineage is the Book 6 build branch. A
Book 6 implementation branched from planning would drag the planning corpus in
and lose the accepted anchor's isolation.

```text
DERIVE_FROM_PLANNING = FORBIDDEN
FROZEN_WORKTREE_MUTATED = FALSE   (verified 0 drift, HEAD 5f94c3f40c)
```

---

## 9. Verdict

```text
CONSOLIDATED_REVIEW = PASS
CRITERIA = 12 / 12 TRUE

BOOK_6_DESIGN_COMPLETE   = TRUE
BOOK_6_IMPLEMENTED       = FALSE
BOOK_6_RE_ACCEPTED       = FALSE

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

This review is a **PASS on implementability**. It is not an authorization. The
only remaining operator gate is an explicit selection of
`AUTHORIZE_OFFLINE_IMPLEMENTATION`.

---

## 10. Observations recorded, not acted on

```text
OBS-1  CSIA_PLANNING_PROGRESS.md line 2757 is a closing code fence that carries
       an info tag instead of being bare. It is PRE-EXISTING at HEAD and
       cosmetic, affecting the rendering of the span that follows, not any value.
       It is NOT repaired here: the corpus rule is additive errata, not in-place
       editing of committed lines. No semantic content is affected.

OBS-3  The sensor baseline framing was corrected: it is a CSIA-lineage
       measurement pinned to 5f94c3f40c, not a sensor-branch measurement. See
       CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md.

OBS-2  The comparison/change substrate remains entirely absent from accepted
       source. Zero occurrences of ComparisonRule, ChangeObservation,
       BaselineSelectorSpec, TemporalComparabilityStatus or ordering keys in
       src/ or tests/. Expected pre-authorization state, not a defect.
```

---

## 11. What this review did not do

```text
RATIFIED_ANYTHING            = FALSE
IMPLEMENTATION_AUTHORIZED    = FALSE
SOURCE_CHANGED               = FALSE
TEST_CODE_WRITTEN            = FALSE
BRANCH_CREATED               = FALSE
WORKTREE_CREATED             = FALSE
FROZEN_WORKTREE_TOUCHED       = FALSE
RATIFIED_RECORD_EDITED       = FALSE
```
