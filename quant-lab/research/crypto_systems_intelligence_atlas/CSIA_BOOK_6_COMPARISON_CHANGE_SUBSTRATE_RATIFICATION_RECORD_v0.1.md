# CSIA — Book 6 Comparison / Change: Substrate Ratification Record v0.1

**Status:** `RATIFIED`
**Record type:** formal substrate governance record
**Date:** 2026-10-03
**Decision id:** `BOOK6-COMPARE-SUBSTRATE-v0.2`
**Scope:** `SUBSTRATE GOVERNANCE ONLY`
**Grants implementation authority:** `FALSE`

---

## 0. What this record is, and what it is not

This record ratifies the **implementation substrate** for the Book 6
Comparison / Change amendment. It is a **design / governance** act.

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

Ratification resolves five substrate gaps. It does **not** authorize writing a
line of source or a line of test. Authorization to implement is a separate,
later operator decision, taken on a separate authorization packet.

**No edit was made to any of the six artifacts ratified here.** They are
ratified **as written**, including their
`**Status:** DRAFT_PENDING_OPERATOR_RATIFICATION` headers, which record the
state in which the operator received them. This record is the authority that
discharges that state; the artifacts themselves are historical evidence of what
was decided.

---

## 1. Anchors

### 1.1 Base ratified plan

```text
BASE_V0_4_PLAN_ANCHOR = 28bfac52c23c891ebb54e9924dedc925a859b359
BASE_V0_4_PLAN_COMMIT_MESSAGE = docs(csia): revise Book 6 comparison-change
                                amendment plan to v0.4
BASE_V0_4_RATIFIED_IN         = 8557f4df82a67434951b2f9682142a59125f5153
BASE_V0_4_RATIFICATION_MESSAGE = docs(csia): ratify Book 6 comparison-change
                                 amendment v0.4
```

### 1.2 Successor package anchor

```text
SUCCESSOR_PACKAGE_ANCHOR = 4f2b6b1f52db8ba42f0bdf035cb80f2792868253
SUCCESSOR_PACKAGE_COMMIT = Resolve GAP-5 as 5E comparison-rule-owned baseline
                            selector
```

### 1.3 Verified lineage

Both ancestry relations were verified in the planning worktree before
ratification:

```text
28bfac52 IS ANCESTOR OF 8557f4df   = TRUE   (v0.4 written, then ratified)
8557f4df IS ANCESTOR OF 4f2b6b1f   = TRUE   (ratified base -> successor package)
```

The intervening chain, in order:

```text
f76cf9b95  Audit ratified CSIA plans for phantom citations of accepted artifacts
39aa6d9a7  Resolve Book 6 comparison/change substrate gaps as drafts
4f2b6b1f5  Resolve GAP-5 as 5E comparison-rule-owned baseline selector
```

### 1.4 Accepted implementation baseline (unchanged)

```text
BOOK_6                       = FROZEN_ACCEPTED
BOOK_6_ACCEPTED_ANCHOR       = 3919fb8052e216e94034a753fb258d338c5fa0dc
BOOK_6_ACCEPTANCE_COMMIT     = 5f94c3f40cea4441470c57671f51454da7377361
BOOK_6_IMPLEMENTATION_BRANCH = agent/crypto-systems-intelligence-atlas-book6-build
ACCEPTED_MODULE_COUNT       = 62
COMMIT_COUNT_PAST_ANCHOR    = 1
COMMITS_PAST_ANCHOR         = docs(csia): accept Book 6 fundamental measurement
                              kernel  (the acceptance commit itself)
IMPLEMENTATION_DRIFT        = ZERO
```

Re-verified at the start of this session: planning HEAD `4f2b6b1f` (local ==
origin == ls-remote, clean), implementation HEAD `5f94c3f4` (local == origin ==
ls-remote, clean), anchor is an ancestor, and the single commit past the anchor
is the acceptance commit itself.

```text
$ grep -rn "Benchmark" src/crypto_systems_intelligence_atlas/*.py | wc -l
0
```

---

## 2. Ratified successor artifacts (the six)

Ratified **as written**, with no edit:

| # | Artifact | Lines | Ratified as |
|---|----------|-------|-------------|
| 1 | `CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_SUBSTRATE_CLARIFICATION_v0.2.md` | 527 | substrate clarification |
| 2 | `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md` | 521 | normative grammar |
| 3 | `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.6.md` | 213 | amendment plan |
| 4 | `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.4.md` | 154 | boundary / invariant |
| 5 | `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_ERRATUM_v0.1.md` | 166 | erratum to the v0.4 record |
| 6 | `CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.3.md` | 272 | implementation test contract |

Three supporting reviews, re-verified before ratification and not themselves
re-ratified (they are review verdicts, not governance substrates):

| Artifact | Verdict |
|----------|---------|
| `..._SUBSTRATE_PRE_RATIFICATION_REVIEW_v0.2.md` | **20 / 20 PASS** |
| `..._IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3.md` | **10 TRUE / 0 FALSE** |
| `..._SUBSTRATE_RATIFICATION_PACKET_v0.2.md` | packet that carried these six |

### 2.1 Gate values verified at ratification

Every value below was re-read from the artifacts in this session, not carried
forward on trust.

```text
PRE_RATIFICATION_REVIEW_v0.2   = 20 / 20 PASS          (verified: Q1..Q20 = 20 PASS / 0 FAIL)
AUTHORIZATION_REVIEW_v0.3      = 10 TRUE / 0 FALSE     (verified: SCORE = 10 TRUE / 0 FALSE)
TEST_SPEC_v0.3_CASES           = 237                   (verified)
TEST_SPEC_v0.3_BLOCKED         = 0                     (verified)
REPLAY_CHECK_COUNT             = 20                    (verified in grammar v0.6, plan v0.6, test spec v0.3)
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2      (verified in boundary v0.4, plan v0.6)
HIDDEN_THIRD_CONTRACT          = NONE                  (verified in boundary v0.4, plan v0.6)
```

On the v0.3 authorization review: that file contains nine literal `FALSE`
tokens, none of which are criterion verdicts. They are authority flags
(`BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`, and siblings) and ratified bindings
(`ACCEPTED_BENCHMARK_RULE_NAMESPACE = FALSE`, `SELECTOR_AGGREGATES = FALSE`,
`CAN_DERIVE_NOT_APPLICABLE = FALSE`, `SUBSTRATE_CLARIFICATION_RATIFIED = FALSE`).
The criterion verdict line is `SCORE = 10 TRUE / 0 FALSE`. The single
`NOT_SUPPORTABLE` token in that file is a **historical citation** of the
superseded v0.2 review (9 TRUE / 1 NOT_SUPPORTABLE), preserved on purpose.

### 2.2 Criterion name set

The v0.3 review carries criterion 7 as `ALL_REPLAY_CHECKS_IMPLEMENTABLE`. The
post-ratification review v0.4 names the same criterion
`ALL_20_REPLAY_CHECKS_IMPLEMENTABLE`, making the count explicit. **This is one
criterion, renamed — not a new criterion and not an eleventh.** A second rename
is already on record: the original `BENCHMARK_RUNTIME_PATH_SUFFICIENT` was
**retired** (the phantom it named does not exist) and replaced by
`BASELINE_SELECTION_RUNTIME_PATH_SUFFICIENT`. Retirements and clarifications are
recorded explicitly rather than applied silently.

---

## 3. GAP-1 — `1A-STRICT`

```text
GAP_1 = CLOSED / 1A-STRICT

CANONICAL_VALUE          = FINITE_STORED_BINARY64
CANONICAL_EQUALITY       = exact equality of finite stored binary64 values
REAL_NUMBER_EXACTNESS_CLAIM  = FALSE
STORED_VALUE_EXACTNESS_CLAIM = TRUE
NONFINITE_INPUT_ALLOWED  = FALSE
REJECTED                 = NaN, +Inf, -Inf
REJECTED_MAPS_TO         = INSUFFICIENT_DATA
```

Canonical zero: `+0.0` and `-0.0` are **both zero**. Stored binary64 equality
gives this for free, and no artifact may reintroduce a distinction between them.

```text
EPSILON_TOLERANCE   = NONE
isclose             = NOT PERMITTED
Decimal migration   = NOT PERMITTED
Fraction migration  = NOT PERMITTED
MEASUREMENT_OBSERVATION_VALUE_TYPE_CHANGE = NONE
```

**Substrate, verified against the accepted implementation branch `5f94c3f4`:**
`MeasurementObservation.value` is `float | None` at `book6_records.py:113` and is
**unchanged** by this amendment. The rationale is honesty, not tolerance: the
system claims exactness of the **stored** value and explicitly disclaims
exactness of the **real number** the measurement approximates. `book6_core.py:181`
carries a NaN sentinel for the accepted kernel's own reasons; that is not
inherited into the comparison arithmetic path, and non-finite input is rejected
before arithmetic rather than propagated.

GAP-1 is a **doctrine correction**, carried forward unchanged from the earlier
draft chain: the defect was the wording, not the representation. Changing the
representation would have destroyed the accepted kernel to fix a sentence.

---

## 4. GAP-2 — `2D` SAME_METRIC_EXACT_UNIT_IDENTITY

```text
GAP_2 = CLOSED / 2D

TEMPORAL_UNIT_COMPATIBILITY = SAME_METRIC_EXACT_UNIT_IDENTITY
```

Arithmetic is permitted only when **all four** hold:

1. the baseline observation resolves to the bound `metric_definition_ref`;
2. the comparison observation resolves to the **same** `metric_definition_ref`;
3. `baseline observation.unit == MetricDefinition.unit`;
4. `comparison observation.unit == MetricDefinition.unit`.

```text
UNIT_CONVERSION              = NOT PERMITTED
UNIT_ALIASES                 = NOT PERMITTED
DIMENSIONAL_INFERENCE        = NOT PERMITTED
DIMENSIONAL_ONTOLOGY         = NOT INTRODUCED
UNIT_NORMALIZATION           = NOT PERMITTED
UNIT_CONTRACT_CLASS_ADDED    = FALSE
NEW_AUTHORITY_BEARING_CONTRACT_CLASS_FOR_UNITS = FALSE
```

**Substrate, verified at `5f94c3f4`:** `MetricDefinition.unit` is
non-nullable — `unit: str = Field(min_length=1)` at `book6_definitions.py:148`.
`MeasurementObservation.unit` is nullable (`str | None` at
`book6_records.py:114`), which is why the comparison is an explicit equality
against the definition rather than a non-null assertion.

**The mechanism that closes this gap is a removal, not an addition.** Grammar
policy **P3 `unit_requirements` is WITHDRAWN** (grammar v0.6:416): it cited a
contract that does not exist, so the citation is withdrawn rather than
satisfied. Withdrawing a phantom is precisely how a gap closes without adding a
third contract class.

Mismatch outcome:

```text
UNIT_MISMATCH -> TemporalComparabilityStatus.NOT_COMPARABLE
```

---

## 5. GAP-3 — `3C` COVERAGE_RULE_PRESENCE_DERIVATION

```text
GAP_3 = CLOSED / 3C
```

The rule is a **presence derivation**, evaluated in this order:

```text
current + ratified + exact-metric-scoped CoverageSufficiencyRule
    -> coverage_requirement_status = REQUIRED
otherwise
    -> coverage_requirement_status = UNRESOLVED
    -> coverage_applicability_source_ref ABSENT
    -> absent means NO_UPSTREAM_DETERMINATION_EXISTS and nothing else
```

```text
CAN_DERIVE_NOT_APPLICABLE       = FALSE
NOT_APPLICABLE_IS_NOT_DERIVABLE = TRUE
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0    (canonical production)
```

`NOT_APPLICABLE` is **never** reachable from an absent rule. An absent rule means
nobody has decided, not that nothing applies. This is the distinction the earlier
drafts kept losing.

**Substrate, verified at `5f94c3f4`:** `CoverageRuleRegistry` at
`book6_coverage_rules.py:112`, with `ratify` (`:177`), `ratification_of`
(`:194`), `rules_for_metric` (`:215`) and `authorize` (`:227`). The derivation
routes entirely through an **already accepted** registry. No new registry, no new
ratification path, no new authority class.

**Synthetic test fixtures may exercise the positive path.** A test may construct a
non-canonical `CoverageSufficiencyRule` in a fixture to prove the `REQUIRED`
branch executes. Such a fixture is **not canonical**, carries no authority, and
must not be counted in `COVERAGE_SUFFICIENCY_RULES_RATIFIED`. The canonical
count remains **0**.

---

## 6. GAP-4 — `4D` EXPLICIT_TEMPORAL_COMPARABILITY

Ratified closed enum — exactly three members, no more:

```text
TemporalComparabilityStatus:
    COMPARABLE
    NOT_COMPARABLE
    UNRESOLVED
```

```text
structural compatibility failure -> NOT_COMPARABLE
missing authoritative determination -> UNRESOLVED

UNRESOLVED != NOT_COMPARABLE
```

The distinction is load-bearing and is ratified as such:
`NOT_COMPARABLE` is a **finding** (the data was examined and cannot be compared);
`UNRESOLVED` is an **absence of a finding** (insufficient authoritative basis to
decide at all). Collapsing them would let "we don't know" masquerade as "we
looked and it fails", and would destroy the fail-closed behaviour Book 6 was
built on.

**Replay check assignment:**

```text
check 19 = TEMPORAL COMPARABILITY RESOLUTION
check 20 = deterministic comparison/change recomputation
```

Check 19 and check 20 are **independently falsifiable**: check 19 can pass while
check 20 fails (recomputed delta disagrees), and check 19 can refuse so that
check 20 never runs.

`NOT_COMPARABLE` now has a **producing check**. This closes the v0.4 defect in
which `change_kind` carried a member that no check could ever produce.

**Untouched by this amendment:**

```text
FALSE_COMPARISON_CORPUS = UNCHANGED   (FC-01..FC-15)
book6_comparability.py  = UNCHANGED
CorpusVerdict           = UNCHANGED
authorize_comparison()  = UNCHANGED
```

The cross-metric corpus is never consulted by the temporal engine. It was not
consulted to design this and must not be consulted to implement it.

---

## 7. GAP-5 — `5E` COMPARISON_RULE_OWNED_BASELINE_SELECTOR

```text
GAP_5 = CLOSED / 5E

ACCEPTED_BENCHMARK_RULE_NAMESPACE = FALSE
BENCHMARK_RULE_RUNTIME            = NOT_IMPLEMENTED
BENCHMARK_RULES_RATIFIED         = 0
```

The binding principle, ratified verbatim:

```text
BASELINE SELECTION IS PART OF THE COMPARISON RULE'S DERIVATION SEMANTICS.
IT IS NOT A SEPARATELY AUTHORITY-BEARING BENCHMARK RULE.
```

`ComparisonRule` operator ratification already binds identity, version,
canonical fingerprint, derivation semantics and supersession. Baseline-selection
semantics therefore live **inside** that existing binding as a closed, typed,
fingerprinted component — requiring no second registry, no second ledger, and no
second ratification act.

### 7.1 `BaselineSelectorSpec` ownership

`BaselineSelectorSpec` is a **nested value object** carried by `ComparisonRule`.
It is **not** a public authority-bearing contract, a separately ratified object, a
separately registered object, a Book 2 Claim, a `StateRule`, or a
`BenchmarkRule`.

```text
BASELINE_SELECTOR_AUTHORITY               = BOUND_INSIDE_COMPARISON_RULE
BASELINE_SELECTOR_INDEPENDENT_RATIFICATION = FALSE
BASELINE_SELECTOR_INDEPENDENT_REGISTRY     = FALSE
BASELINE_SELECTOR_LIFECYCLE_AUTHORITY      = NONE
BASELINE_SELECTOR_IS_NOT_A_BOOK_2_CLAIM    = TRUE
BASELINE_SELECTOR_IS_NOT_A_STATE_RULE     = TRUE
BASELINE_SELECTOR_IS_NOT_A_BENCHMARK_RULE = TRUE
COMPARISON_RULE_BINDS_BASELINE_SELECTOR    = TRUE
COMPARISON_RULE_FINGERPRINTS_SELECTOR      = TRUE
```

The selector is **semantic content of `ComparisonRule`** and is covered by that
rule's canonical fingerprint. Changing the selector changes the fingerprint,
which changes the rule's identity for ratification purposes.

`GAP_5A / 5B / 5C / 5D = NOT SELECTED`.

---

## 8. Executable selector set

Ratified exactly:

```text
EXECUTABLE_BASELINE_SELECTOR_COUNT = 1
EXECUTABLE_BASELINE_SELECTOR      = PRIOR_COMPARABLE_WINDOW
```

Reserved, and **non-executable**:

```text
RESERVED_NOT_EXECUTABLE:
    ROLLING_MEAN
    ROLLING_MEDIAN
    HISTORICAL_DISTRIBUTION
    BASELINE_EPOCH
RESERVED_NOT_EXECUTABLE_COUNT = 4
```

Constructing a `ComparisonRule` whose `selector_kind` is any reserved name is
**REJECTED**. Reserved names are not accepted runtime methods and carry **no
placeholder behaviour whatsoever** — no stub, no default, no "not yet
implemented" branch that returns a value. Reserved names may become executable
only via separate successor governance specifying inputs, parameters, window
semantics, aggregation semantics, missingness, fingerprint content and tests.

This ratification therefore **does not** create a rolling mean, a rolling
median, a historical distribution, or a baseline epoch.

---

## 9. `PRIOR_COMPARABLE_WINDOW` — eligibility

Required eligibility, all conditions:

1. same `subject_ref`;
2. same `metric_definition_ref`;
3. same **metric-definition semantic fingerprint**;
4. required exact methodology identity/version;
5. same exact `MetricDefinition.unit`;
6. compatible denominator;
7. compatible cohort where applicable;
8. compatible `WindowClass`;
9. candidate `valid_time` **strictly precedes** comparison `valid_time`;
10. Book 2 authority current;
11. missingness requirements satisfied.

**Substrate, verified at `5f94c3f4`:** methodology identity is a
fully-qualified `ref@version` string, produced by `MethodologyRef.identity()` at
`book6_definitions.py:127-130`. Eligibility is therefore an **exact string
identity** on `ref@version` — not a prefix match, not a family match.

### 9.1 Coverage is a gate, never a selector input

Coverage is an **authorization gate applied AFTER structural selection**. It is
**not** an input to selector eligibility.

```text
COVERAGE_INFLUENCES_BASELINE_SELECTION = FALSE
```

If coverage were a selector input, the authorization gate would influence which
observation becomes the baseline — circular reasoning. Only a ratified contract
explicitly requiring otherwise may deviate.

### 9.2 Deterministic ordering

```text
 1. greatest valid_time END, strictly before comparison valid_time START
 2. if tied: greatest valid_time START
 3. if still tied: stable lexical measurement_ref   (final tie-break ONLY)
```

```text
BASELINE_SELECTION_DETERMINISTIC  = TRUE
CALLER_ORDER_AFFECTS_BASELINE     = FALSE
OBSERVED_AT_USED_FOR_BASELINE_ORDERING = FALSE
RANDOM_SELECTION                  = FALSE
```

Re-running with the same inputs yields the same baseline, regardless of
insertion order or caller sequence.

**On `RANDOM_SELECTION = FALSE`, stated precisely.** This is a **normalized
restatement**, not a literal token lifted from an artifact. The ratified grammar
carries the substance at grammar v0.6:174 ("no randomness"), :261
(`ARBITRARY CALLABLE = NOT PERMITTED`) and :519 ("any random or caller-order"),
together with `BASELINE_SELECTION_DETERMINISTIC = TRUE` at :213. Recorded here
in this exact form so that a later grep does not "confirm" a token that was
never written, and does not miss one either.

### 9.3 No eligible candidate

```text
NO_ELIGIBLE_PRIOR_BASELINE -> INSUFFICIENT_DATA / BASELINE_UNAVAILABLE
BASELINE_RESULT            = ONE MeasurementObservation
```

**No fallback.** No silent fallback: no rolling mean, no epoch baseline, no
arbitrary first item, no nearest incompatible observation. `BASELINE_UNAVAILABLE`
is a **first-class result**, not an error to be patched over. Absent
`selected_baseline_measurement_ref` means `BASELINE_UNAVAILABLE` and nothing
else.

---

## 10. Aggregation boundary

```text
SELECTOR_AGGREGATES = FALSE
```

Aggregation semantics belong to `MetricDefinition.aggregation`, not to the
baseline selector.

**Substrate, verified at `5f94c3f4`:**
`MetricDefinition.aggregation: AggregationSemantics` at
`book6_definitions.py:151`, whose closed set at `book6_definitions.py:59-67` is
`NONE | SUM | MEAN | LAST | DISTRIBUTION`. The set is closed; no new member may
be introduced by this amendment.

### 10.1 Standing condition (recorded, not a blocker)

If implementation encounters

```text
aggregation == NONE
AND multiple raw observations would require a NEW aggregation
   in order to obtain a single baseline value
```

then implementation must **HOLD that case** and surface a **concrete operator
decision**. It must not invent an aggregation to get past the case.

This is recorded as a **standing condition**, not as a blocker. It does **not**
block this ratification, and it does **not** block a later implementation
authorization: implementation is not authorized yet, and when it is authorized
this condition is one of the things it must honour.

`SELECTOR_AGGREGATES = FALSE` also means the pre-ratification review's concern
about an aggregation HOLD case (§2.3) is discharged: no selector aggregates, so
the selector cannot silently create an aggregation.

---

## 11. Phantom-citation correction (ratified prospectively)

```text
PHANTOM_BENCHMARK_CLAIM          = SUPERSEDED_PROSPECTIVELY
ORIGINAL_RATIFIED_RECORD_PRESERVED = TRUE
RETROACTIVE_CORRECTION_CLAIMED   = FALSE
```

### 11.1 What the phantom was

Book 6 base plan v0.2 §5 named a five-token vocabulary
(`PRIOR_COMPARABLE_WINDOW`, `ROLLING_MEAN`, `ROLLING_MEDIAN`,
`HISTORICAL_DISTRIBUTION`, `BASELINE_EPOCH`) and said plainly that **none is
chosen by that plan**. Ratified amendment v0.4 then promoted that planning
vocabulary into an "accepted authority substrate reused unmodified". That
promotion was the phantom. The accepted implementation has **zero** occurrences
of `Benchmark` across all 62 modules.

The phantom was ratified *and propagated* across five artifacts, which is why it
took a dedicated audit to find. The audit is preserved as
`CSIA_RATIFIED_PLAN_PHANTOM_CITATION_SWEEP_v0.1.md` (commit `f76cf9b95`).

### 11.2 How the correction is effected

**Prospectively only.** The v0.4 artifacts — plan v0.4, grammar v0.4, boundary
v0.3, seam v0.4, readiness v0.3, and the v0.1 ratification record — **remain
historical ratified records and are not edited in place**. The erratum (ratified
here as artifact 5) quotes them verbatim and supersedes them going forward.

Historical phantom sites, quoted by the erratum and left untouched:

| Artifact | Site |
|----------|------|
| `..._AMENDMENT_RATIFICATION_RECORD_v0.1.md` | lines 152, 230 |
| `..._AMENDMENT_BOUNDARY_v0.3.md` | line 41 |
| `..._AMENDMENT_PLAN_v0.4.md` | lines 35, 134 |
| `..._GRAMMAR_v0.4.md` | line 246 |

Superseded prospectively by boundary v0.4 §2 and grammar v0.6 §0.1.

`RETROACTIVE_CORRECTION_CLAIMED = FALSE`: the record does not pretend the earlier
ratification never happened. What was ratified was believed true at the time; the
error is corrected going forward, and the error itself is preserved.

---

## 12. Boundary invariant

```text
RESOLUTION_BEFORE_CLASSIFICATION = TRUE
```

Any claim that a substrate is **accepted**, **existing**, **reused**, **already
ratified**, or **reused unmodified** must **resolve** before it can be excluded
from scope. It must resolve to either:

- a **runtime symbol**, or
- a **ratified governance artifact** that explicitly defines it as
  governance-only / intentionally non-runtime.

Classification categories:

```text
RUNTIME_REQUIRED       -> must resolve to a runtime symbol, or FAIL
GOVERNANCE_ONLY        -> must resolve to a ratified artifact, or FAIL
FORWARD_SPECIFICATION  -> labelled as intended-to-create; not a failure
PROHIBITED / NEGATED   -> labelled as forbidden/rejected; not a failure
```

Only `RUNTIME_REQUIRED` unresolved references fail. The other three categories
exist so the test does not flag legitimate forward specifications
(`ComparisonRule`, `BaselineSelectorSpec`) or explicit prohibitions as defects.

**Naming note, recorded honestly.** The operator's instruction named the fourth
category `PROHIBITED_NEGATED`. The ratified artifact spells it
`PROHIBITED / NEGATED` (boundary v0.4:109). Same category, different spelling.
Both forms are recorded here so a later search matches either. This is a naming
normalization, not a substantive change and not a fourth-versus-three-category
disagreement.

### 12.1 No grep-only validator

**A grep-only test is not sufficient to enforce this invariant**, and is
explicitly rejected. Two hard-won reasons, both from the audit that found the
phantom:

1. The first pass reported `CapitalPrincipalLineage` as a phantom when it exists
   as `CapitalPrincipalLineageGraph` — a **suffix**, not a match failure. An
   exact-name symbol pass produces a false positive.
2. The Book 6 defect itself ("an accepted unit contract") appeared in **prose
   with no code font at all**, so a symbol scan would have missed it entirely.

Existence must be resolved with judgement against source and against ratified
artifacts. A validator that only greps will eventually be wrong in one of those
two directions, and neither direction is acceptable in a governance control.

---

## 13. Public contract count

```text
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2

    ComparisonRule
    ChangeObservation
```

Explicitly **not** a third contract class:

```text
BaselineSelectorSpec        = NESTED VALUE OBJECT, not a third class
TemporalComparabilityStatus = CLOSED ENUM FIELD, not a third class
Coverage applicability resolver = DERIVATION, not a third class
UnitContract                = NOT ADDED

HIDDEN_THIRD_CONTRACT = NONE
```

The count is 2 because each additional public authority-bearing class would
require its own registry or ratification path. GAP-2 closed by **withdrawing** a
policy citation (P3) and GAP-5 closed by **nesting** an existing value object,
so neither gap added a class.

---

## 14. Ratified 20-check replay

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

```text
REPLAY_CHECK_COUNT              = 20
ALL_20_INDEPENDENTLY_FALSIFIABLE = TRUE
AGGREGATE_ONLY                  = REJECTED
```

Checks 4–6 were inherited from the phantom benchmark model in v0.4. Grammar v0.6
replaces them honestly with three selector checks. **The total stays 20, but not
for cosmetic continuity** — it is 20 because this structure contains 20
independently falsifiable authority checks. If implementation proves more are
needed, the count changes; it is not pinned by nostalgia.

---

## 15. Ratified implementation test contract

```text
TEST_SPEC_v0.3          = RATIFIED AS THE IMPLEMENTATION TEST CONTRACT
TEST_SPEC_CASES         = 237
TEST_SPEC_BLOCKED       = 0
TEST_SPEC_GROUPS        = A..H  (plus negative-surface groups)
```

237 cases, **0 blocked**. The count rose from 208 (v0.2) to 237 (v0.3) because
GAP-5 (`5E`) added the selector eligibility, ordering, reserved-name rejection
and no-eligible-baseline cases that did not exist when `5E` was still an open
choice among five options. `BLOCKED = 0` means every case is fully specified:
none is waiting on an unratified policy.

**The test contract is ratified as a specification only.** No test code was
written, and none is authorized by this record.

---

## 16. Class C StateRule benchmark — explicit defer

Recorded without opening another decision packet. **No Class C design work was
done in this session.**

```text
BOOK6_CLASS_C_STATE_BENCHMARK_RUNTIME = UNRATIFIED / UNIMPLEMENTED
CLASS_C_BENCHMARK_GOVERNANCE           = DEFERRED
CLASS_C_STATE_RULES_RATIFIED           = 0  (canonical)
CLASS_C_BENCHMARK_METHODOLOGIES_RATIFIED = 0 (canonical)

COMPARISON_BASELINE_SELECTOR_USES_CLASS_C_AUTHORITY = FALSE
COMPARISON_RULE_BASELINE_SELECTOR_REUSES_STATE_RULE_AUTHORITY = FALSE

CLASS_C_BENCHMARK_BLOCKS_COMPARISON_SUBSTRATE_RATIFICATION = FALSE
CLASS_C_BENCHMARK_BLOCKS_COMPARISON_IMPLEMENTATION_AUTHORIZATION = FALSE
CLASS_C_BENCHMARK_BLOCKS_THIS_RATIFICATION = FALSE
```

**Reason, as ratified.** `StateRule.benchmark_methodology_ref` is a **separate
Class C mechanism**, enforced at `book6_states.py:214` (field declared at
`book6_states.py:178`), serving `StateClass.C_THRESHOLD_BENCHMARK`
(`book6_states.py:72`). It is a mechanism for Class C threshold/benchmark
**states**. `BaselineSelectorSpec` belongs only to `ComparisonRule`. The
comparison amendment does **not** reuse `StateRule` benchmark authority, extend
it, ratify it, implement it, or solve it. Accepted Book 6 already fail-closes
Class C pending ratified rules.

The two remain separate Book 6 concerns, **both currently unratified**, and
Class C is **not** a dependency of this comparison/change amendment.

The blocking flags above are conditional, as ratified: they hold **unless source
implementation later demonstrates an actual dependency**. If a future
implementation attempt turns out to touch `StateRule.benchmark_methodology_ref`,
these flags fall away and the question must return to the operator as a new
decision — it must not be resolved inside an implementation session.

---

## 17. Canonical rule counts

Every canonical count is **zero**. Ratification adds governance structure and
rules; it ratifies **no** new runtime rule.

```text
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0  (canonical production)
BENCHMARK_RULES_RATIFIED            = 0
CLASS_C_STATE_RULES_RATIFIED        = 0
CLASS_C_BENCHMARK_METHODOLOGIES_RATIFIED = 0
COMPARISON_RULES_RATIFIED           = 0  (ratification of any ComparisonRule is
                                        out of scope and was not performed)
EPSILON / TOLERANCE / MATERIALITY / SIGNIFICANCE = NONE
NEW_VALUES_DOMAINS_OR_DOMAINS_INVENTED = 0
NEW_DELTA_OPERATORS                = 0
```

Synthetic, non-canonical test fixtures may construct a `CoverageSufficiencyRule`
to exercise the `REQUIRED` branch. Such a fixture carries **no** authority and is
not counted above.

---

## 18. Standing conditions (recorded, not blockers)

1. **Aggregation HOLD case.** If implementation encounters
   `aggregation == NONE` with multiple raw observations requiring a new
   aggregation to obtain one baseline value, implementation must **HOLD** that
   case and surface a concrete operator decision. It must not invent an
   aggregation. (See §10.1.)
2. **Class C.** Deferred and unimplemented; not a blocker unless implementation
   unexpectedly touches it. (See §16.)
3. **Reserved selectors.** `ROLLING_MEAN`, `ROLLING_MEDIAN`,
   `HISTORICAL_DISTRIBUTION`, `BASELINE_EPOCH` remain
   `RESERVED_NOT_EXECUTABLE`. Construction or replay using any of them is
   **REJECT**, with no placeholder. They become executable only via separate
   successor governance. (See §8.)

---

## 19. Verification performed for this ratification

| # | Verification | Result |
|---|--------------|--------|
| 1 | planning branch `agent/crypto-systems-intelligence-atlas-plan` | correct |
| 2 | planning HEAD == origin == ls-remote == `4f2b6b1f` | TRUE |
| 3 | planning worktree clean | TRUE |
| 4 | implementation branch `agent/crypto-systems-intelligence-atlas-book6-build` | correct |
| 5 | implementation HEAD == origin == ls-remote == `5f94c3f4` | TRUE |
| 6 | implementation worktree clean | TRUE |
| 7 | `3919fb80` is an ancestor of implementation HEAD | TRUE |
| 8 | exactly 1 commit past the anchor, and it is the acceptance commit | TRUE |
| 9 | `grep -rn "Benchmark" *.py` across 62 modules | 0 matches |
| 10 | all nine package artifacts present | TRUE |
| 11 | six ratified artifacts still `DRAFT_PENDING_OPERATOR_RATIFICATION` (unedited) | TRUE |
| 12 | `28bfac52` ancestor of `8557f4df`; `8557f4df` ancestor of `4f2b6b1f` | TRUE |
| 13 | PRE_RAT = 20 / 20 PASS | TRUE |
| 14 | AUTH_REVIEW = 10 TRUE / 0 FALSE | TRUE |
| 15 | TEST_SPEC = 237 cases, BLOCKED = 0 | TRUE |
| 16 | REPLAY_CHECK_COUNT = 20 | TRUE |
| 17 | CONTRACT_COUNT = 2, HIDDEN_THIRD = NONE | TRUE |
| 18 | GAP-1..GAP-5 resolutions stated in substrate clarification v0.2:25-29 | TRUE |
| 19 | every runtime anchor cited in this record resolves in `5f94c3f4` source | TRUE |
| 20 | decision id `BOOK6-COMPARE-SUBSTRATE-v0.2` collision-free | TRUE |

**Runtime anchors cited above, all resolved against `5f94c3f4`:**

| Claim | Resolution |
|-------|------------|
| `MeasurementObservation.value` is `float \| None` | `book6_records.py:113` |
| `MeasurementObservation.unit` is `str \| None` | `book6_records.py:114` |
| `MetricDefinition.unit` non-nullable | `book6_definitions.py:148` |
| `MetricDefinition.aggregation` | `book6_definitions.py:151` |
| `AggregationSemantics` closed set | `book6_definitions.py:59-67` |
| methodology identity `ref@version` | `book6_definitions.py:127-130` |
| `CoverageRuleRegistry` + 4 methods | `book6_coverage_rules.py:112,177,194,215,227` |
| `StateRule.benchmark_methodology_ref` | `book6_states.py:178` (enforced `:214`) |
| `StateClass.C_THRESHOLD_BENCHMARK` | `book6_states.py:72` |

This table is itself an application of §12: every existence claim resolves to a
runtime symbol before being relied on.

---

## 20. Verdict

```text
SUBSTRATE_CLARIFICATION      = v0.2 RATIFIED
GRAMMAR                      = v0.6 RATIFIED SUCCESSOR
PLAN                         = v0.6 RATIFIED SUCCESSOR
BOUNDARY                     = v0.4 RATIFIED SUCCESSOR
RATIFICATION_RECORD_ERRATUM  = v0.1 RATIFIED
TEST_SPEC                    = v0.3 RATIFIED IMPLEMENTATION CONTRACT

GAP_1 = CLOSED / 1A-STRICT
GAP_2 = CLOSED / 2D
GAP_3 = CLOSED / 3C
GAP_4 = CLOSED / 4D
GAP_5 = CLOSED / 5E
GAP_1..GAP_5 = ALL CLOSED

CLASS_C_BENCHMARK = DEFERRED / UNIMPLEMENTED / NOT A BLOCKER

REPLAY_CHECK_COUNT        = 20
TEST_SPEC_CASES           = 237
TEST_SPEC_BLOCKED         = 0
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT     = NONE

COVERAGE_SUFFICIENCY_RULES_RATIFIED        = 0
BENCHMARK_RULES_RATIFIED                   = 0
CLASS_C_STATE_RULES_RATIFIED               = 0
CLASS_C_BENCHMARK_METHODOLOGIES_RATIFIED   = 0
COMPARISON_RULES_RATIFIED                  = 0

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE

SCOPE        = SUBSTRATE GOVERNANCE ONLY
IMPLEMENTATION_AUTHORITY = FALSE

STATUS       = RATIFIED
NEXT         = POST-RATIFICATION IMPLEMENTATION AUTHORIZATION REVIEW (v0.4)
```

### 20.1 What ratification did

It closed five substrate gaps with ratified, falsifiable, implementable
semantics. It retired a phantom authority that had been ratified and propagated.
It bound baseline selection to `ComparisonRule` instead of a benchmark namespace
that never existed. It fixed a fail-open hole where "no coverage rule exists"
would have been read as "coverage does not apply". It gave `NOT_COMPARABLE` a
producing check. And it did all of this without adding a single new public
authority-bearing contract class.

### 20.2 What ratification did not do

**Not authorized and not performed:** any implementation; any source change; any
test code; any `BenchmarkRule`; any `BenchmarkRuleRegistry`; any benchmark-rule
ratification; any rolling mean, rolling median, historical distribution or
baseline epoch implementation; any `observed_at` baseline ordering; any random or
caller-order selection; any caller-selected authoritative baseline; any coverage
rule ratification; any `ComparisonRule` ratification; any Class C benchmark
design; Book 6 re-acceptance; Book 7 or Book 8; live acquisition; branch
creation; force-push; rebase; amend; history rewrite.

The ratified artifacts carry `DRAFT_PENDING_OPERATOR_RATIFICATION` headers and
that is correct. They are evidence of what was presented. This record is the
authority that accepted it.

---

## 21. Next operator action

Ratification is complete and pushed. The next step is **not** implementation.

The post-ratification implementation authorization review v0.4 re-runs the ten
implementation-readiness criteria independently against the now-ratified
substrate. Only if it returns **10 / 10 TRUE** does an authorization packet
become available for an operator decision.

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

remains in force until an operator makes an **explicit, separate** selection.
Nothing in this record, and nothing in review v0.4, self-authorizes anything.

---

*End of ratification record. This document is a governance artifact. It contains
no source code and no test code.*
