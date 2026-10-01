# CSIA — BOOK 7 RESPONSE SEMANTANTICS RECONCILIATION v0.1

> **Status:** PLANNING REPAIR DOCUMENT — DRAFT. Not ratified. No implementation.
> **Trigger:** external review finding — Book 7 Bloc 7C permits a post-action
> observation to satisfy response semantics without proving a change.
> **Authorization:** operator-authorized Book 7 planning repair only.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Reviewed at head:** `393821616d140beb0ed56051f08ba6248f9bcada`
> **Supersedes:** the response semantics of `CSIA_BOOK_7_ACTION_LADDER_AND_CAUSALITY_v0.1.md`
> §1.3, §1.4, §4 (v0.1 preserved unmodified as history; successor = Action
> Ladder v0.2). All v0.1 artifacts are preserved, not rewritten.

---

## 1. Defect reproduction (Phase 1)

```text
POST_ACTION_OBSERVATION_CAN_CURRENTLY_SATISFY_RESPONSE_SEMANTICS = TRUE
PLAN_v0.1_RESPONSE_DEFINITION                                = TOO_WEAK
```

### 1.1 Every defective location (audit of all Book 7 artifacts)

| # | File:line | Current text | Defect |
|---|---|---|---|
| 1 | `CSIA_BOOK_7_ACTION_LADDER_AND_CAUSALITY_v0.1.md:75-76` | "USAGE RESPONSE OBSERVED = a Book 6 MeasurementObservation ref whose valid time follows the action's effective time, linked by recorded relation" | **primary defect** — one post-action observation satisfies the rung; no baseline, no change, no comparison methodology |
| 2 | same file `:79` | "the rung records *that measured change followed*" | asserts a change that was never required to be computed |
| 3 | same file `:86-95` | capital rung "consuming Books 5 and 6" (no baseline/comparison requirement at all) | same leak on the capital axis |
| 4 | same file `:170` | "NO_RESPONSE_OBSERVED — window elapsed, measurement exists, no change recorded" | "no change recorded" is not "no change"; no valid baseline, no comparison validity, no closed-window test, no response predicate |
| 5 | `CSIA_BOOK_7_..._PLAN_v0.1.md:72-73` | "USAGE RESPONSE: Book 6 refs only … CAPITAL RESPONSE: Book 5/6 refs only" | plan summary inherits the weak rule |
| 6 | same plan `:76` | six-state absence vocabulary propagated | propagates weak `NO_RESPONSE_OBSERVED` |
| 7 | `CSIA_BOOK_7_PRE_RATIFICATION_REVIEW_v0.1.md` Q5, Q10 | "rung-4 requires a Book 6 MeasurementObservation ref"; "six-state absence vocabulary" | PASS evidence for Q5/Q10 rested on the weak rule — review invalidated, rebuilt as v0.2 (45 questions) |
| 8 | `CSIA_BOOK_7_FALSE_POSITIVE_CORPUS_v0.1.md` cases 5, 6, 7, 8 | "usage increased after T"; "capital response observed" | ALLOWED conclusions presume a proven change without baseline/comparison methodology |
| 9 | `CSIA_BOOK_7_SEAMS_AND_FIREWALL_v0.1.md:37` | only `USAGE RESPONSE OBSERVED != USAGE HEALTH` | firewall does not forbid change-unproven responses |

### 1.2 The semantic leak, stated precisely

```text
pre-action usage = 100        post-action usage = 100
→ a post-action observation EXISTS
→ v0.1 semantics: USAGE_RESPONSE_OBSERVED          (WRONG)
→ repaired semantics: OBSERVED_CHANGE = NOT_PROVEN;
                        response assessment = CHANGE_NOT_MEASURABLE or
                        NO_CHANGE_OBSERVED (depending on methodology basis)
```

The leak is not a wording problem — it is an internal doctrine contradiction:

```text
v0.1:  TEMPORAL ORDER -> RESPONSE        (permitted)
Causality Doctrine v0.1: TEMPORAL ORDER -/-> CAUSATION (prohibited)
```

A system that cannot assert causation from sequence must not assert *response*
from sequence either; response is a change claim, one step stronger than order.
Book 6 taught the same lesson in the opposite direction (state name ≠ derivation
rule); this is its mirror image (**observation ≠ change**).

## 2. Three distinct objects (Phase 2)

```text
POST_ACTION_OBSERVATION != OBSERVED_CHANGE
OBSERVED_CHANGE        != CAUSAL_RESPONSE
RESPONSE_LINK          != CAUSAL_CLAIM
UNOBSERVED_CHANGE      != NO_CHANGE
ZERO_VALUE             != ZERO_CHANGE
MATERIALITY            != RESPONSE
```

### 2.1 `PostActionObservation` (the only thing an observation can be)

A Book 5 / Book 6 canonical observation whose valid time falls at or after the
action's effective time. Pure observation record; asserts nothing about change.

```text
post_observation_id
subject_ref
axis                     USAGE | CAPITAL
observation_ref          typed Book 5 economic record ref OR Book 6
                         MeasurementObservation ref (never a copy of the value)
action_context_ref       action link + effective-time ref (for provenance only)
valid_time               preserved from the owning record
observed_at              preserved from the owning record
comparability_metadata_ref  the owning record's Book 6 identity/window/coverage facts
response_status          UNASSESSED (the default; may only be advanced by a
                         ResponseLink referencing an ObservedChange)
```

Book 7 holds the **reference**. It does not copy, recompute, or reinterpret the
value (no Book 6 recomputation; no Book 5 write-back).

### 2.2 `ObservedChange` (the thing that actually must be proven)

A versioned comparison between a valid baseline and one or more later
comparable observations, under an explicit, cited comparison methodology.

```text
response_change_id
axis                     USAGE | CAPITAL
subject_ref
baseline_ref             ResponseBaseline (§3)
post_observation_refs[]  one or more PostActionObservations
comparison_methodology_ref   REQUIRED — the comparison semantics identity
window_methodology_ref      REQUIRED for the post window
comparison_semantics     DELTA_ABSOLUTE | DELTA_RELATIVE (Book 6-supported only)
                         | DISTRIBUTION_SHIFT | THRESHOLD_BREACH_BOOK6_DEFINED
                         | NO_CHANGE_PER_METHODOLOGY | NOT_COMPARABLE
change_direction         ONLY where a Book 6 product already supports it
change_value             ONLY where a Book 6 product already supports it
comparability_status     COMPARABLE | NOT_COMPARABLE | BASELINE_UNAVAILABLE
                         | POST_DATA_UNAVAILABLE | UNKNOWN
valid_time / observed_at
ownership_seam           BOOK6_PRODUCT | BOOK7_LINKAGE_METHODOLOGY  (D7N-7)
```

**Book 7 never asserts a change it cannot cite.** If Book 6 does not supply the
necessary comparison product, the change is recorded only under an explicitly
ratified Book 7 comparison methodology whose owner is fixed by `D7N-7`; Book 7
never silently becomes a measurement engine. Until `D7N-7` closes, the
conservative posture stands: **no change product may be emitted at all**
(`CHANGE_NOT_MEASURABLE` is the only legal response outcome).

### 2.3 `ResponseLink` (Book 7's own linkage — descriptive, non-causal)

States that an `ObservedChange` was assessed within a declared response window
after a declared action.

```text
response_link_id
action_ref
action_effective_time_ref
response_change_ref        an ObservedChange — REQUIRED for CHANGE_OBSERVED
window_methodology_ref     REQUIRED
assessment_result          CHANGE_OBSERVED | NO_CHANGE_OBSERVED
                           | CHANGE_NOT_MEASURABLE | BASELINE_UNAVAILABLE
                           | POST_DATA_UNAVAILABLE | NOT_COMPARABLE
                           | TOO_EARLY_TO_ASSESS | NOT_APPLICABLE | UNKNOWN
causal_status              <= TEMPORAL_PRECEDENCE_ONLY | ASSOCIATION_ONLY
                           (never CAUSAL_PER_RATIFIED_METHODOLOGY in Book 7 —
                            Causality Doctrine D7N-4 gate)
materiality_status         NOT_A_BOOK_7_CONCEPT (recorded as absent, never inferred)
sensitivity_note_ref       methodology-sensitivity record (§12)
```

`RESPONSE_LINK != CAUSAL_CLAIM` is enforced by the closed `causal_status`
vocabulary, exactly as the causality doctrine already requires.

## 3. Baseline contract (Phase 3)

```text
ResponseBaseline (planned)
  baseline_id
  subject_ref
  axis                    USAGE | CAPITAL
  metric_definition_ref   REQUIRED — Book 6 MetricDefinition identity
  baseline_window         window class + valid span + window_methodology_ref
  selection_methodology_ref   REQUIRED — baseline selection IS methodology
  unit
  denominator_identity_ref     where the metric is a ratio (Book 6 denominator
                               identity; a changed denominator breaks comparability)
  cohort_ref                  where cohort-scoped
  source_book            BOOK_6 | BOOK_5
  observation_refs[]
  comparability_decl
  valid_time / observed_at
```

**No silent baseline.** "The last value before the event" is *never* an
implicit default; a baseline exists only with a cited
`selection_methodology_ref`. Candidate baseline models (no universal default is
selected by this document — the choice is part of the cited methodology):

```text
IMMEDIATE_PRIOR_COMPARABLE   closest compatible prior window
PRE_EVENT_WINDOW_SUMMARY     summary over a declared pre-event window
MATCHED_CALENDAR_WINDOW      calendar-matched comparable period (seasonality control)
DECLARED_REFERENCE_PERIOD    operator/research-declared reference period
```

## 4. Comparability requirements (Phase 4)

An `ObservedChange` may be constructed **only** where the baseline and post
observations are compatible under Book 6 semantics:

```text
same metric definition (Book 6 identity)
compatible methodology (Book 6 methodology identity/version relationship)
same unit
same denominator semantics (Book 6 denominator identity)
same cohort (where cohort-scoped)
compatible window class (Book 6 window semantics)
comparable coverage (Book 6 coverage semantics)
non-missing observations (missingness states preserved — NOT_SUPPORTED != 0)
valid temporal ordering (baseline window precedes post window; gaps explicit)
```

Rules:

- Any failed requirement ⇒ `comparability_status = NOT_COMPARABLE` ⇒ the
  response outcome is `NOT_COMPARABLE`, never a change in any direction.
- **Book 7 invents no normalization.** Book 6 remains measurement authority;
  `NORMALIZED_WITHOUT_NATIVE_LINEAGE = INVALID` (D6M-2) continues to bind
  anything Book 7 references.
- No percentile, no ranking, no cohort-relative normalization (Book 6 doctrine,
  unchanged).

## 5. Usage-response repair (Phase 6)

```text
USAGE_RESPONSE_LINKED requires ALL SEVEN:
  1. a valid deployed-action effective time (Book 2-backed, owning-book resolved)
  2. a valid ResponseBaseline — or an explicitly baseline-free comparison
     methodology where such a methodology is genuinely meaningful (Book 6
     supports absolute-threshold comparisons; the exemption must be named)
  3. one or more PostActionObservations (Book 6 refs)
  4. Book 6-compatible comparability (all §4 requirements)
  5. a versioned comparison/change methodology (cited)
  6. an ObservedChange result (CHANGE_OBSERVED or NO_CHANGE_OBSERVED)
  7. the assessed change falls within a declared response window
     (window_methodology_ref cited)
```

Book 7 may then record `USAGE_RESPONSE_LINKED` — a descriptive relation with
`causal_status <= ASSOCIATION_ONLY`. It may **never** imply causation, health,
adoption success, materiality, or investment merit. A rung that fails any gate
stops at rung 3 (`DEPLOYED`) with a precise outcome state — never a fabricated
rung-4.

## 6. Capital-response repair (Phase 7)

Identical doctrine on the capital axis, with Book 5 records as the canonical
capital source:

```text
CAPITAL_RESPONSE_LINKED requires:
  Book 5 economic records and/or Book 6 measurements, authoritative and current
  a valid ResponseBaseline (selection methodology cited)
  comparable PostActionObservations (§4 requirements)
  an explicit comparison/change methodology (cited)
  an explicit response window (cited)
  an ObservedChange result
```

- No capital observation after an event ever implies a capital response by
  itself.
- **No Book 5 write-back** (principal topology, liability obligations, capital
  records remain Book 5's; Book 7 reads only).
- Capital *flows* claimed by narratives are `CHANGE_CLAIMED` occurrences until
  Book 5/6 records exist.

## 7. Zero / unchanged / missing — nine outcomes, never collapsed (Phase 8)

```text
CHANGE_OBSERVED          an ObservedChange exists and satisfies the response
                         predicate under the cited methodology
NO_CHANGE_OBSERVED       the comparison ran validly and found no change under the
                         cited methodology (NOT a failure; NOT a negative response)
CHANGE_NOT_MEASURABLE    no comparison methodology/product is available for this
                         axis+subject (includes the D7N-7 interim posture)
BASELINE_UNAVAILABLE     no valid baseline could be constructed
POST_DATA_UNAVAILABLE    baseline valid, post-action data missing
NOT_COMPARABLE           baseline/post present but incompatible (§4)
TOO_EARLY_TO_ASSESS      inside the declared assessment window (window ref cited)
NOT_APPLICABLE           the response axis is meaningless for this action family
UNKNOWN                  cannot be established — preserved
```

Non-collapsions, each a testable invariant:

```text
NO CHANGE            != NO DATA          (NO_CHANGE_OBSERVED requires a valid run)
NO CHANGE            != NEGATIVE RESPONSE (no polarity is asserted)
ZERO VALUE           != ZERO CHANGE      (a 0 measurement is a value; a change is a comparison result)
ABSENCE OF CHANGE    != CHANGE NOT MEASURED (unknown vs measured-nil)
MISSING BASELINE     != MISSING POST DATA (different missingness cells)
```

This vocabulary **refines** the v0.1 six-state absence list (preserved as
history) and supersedes `NO_RESPONSE_OBSERVED` at the response rung — see §9.

## 8. NO_RESPONSE_OBSERVED repair (Phase 9)

v0.1 defined it as "window elapsed, measurement exists, no change recorded" —
which asserts a proven absence from an unproven basis.

```text
NO_RESPONSE_OBSERVED may be asserted ONLY when ALL hold:
  - an applicable response methodology exists and is cited
  - the assessment window has CLOSED (window ref)
  - a valid baseline exists
  - post-action observations exist
  - the comparison is valid (comparability_status = COMPARABLE)
  - the defined response predicate is NOT satisfied

Otherwise, a more specific state from §7 MUST be used:
  no methodology        -> CHANGE_NOT_MEASURABLE
  no baseline           -> BASELINE_UNAVAILABLE
  no post data          -> POST_DATA_UNAVAILABLE
  incompatible          -> NOT_COMPARABLE
  window open           -> TOO_EARLY_TO_ASSESS
  silence, nothing else -> UNKNOWN
```

**Silence is not evidence.** A rung-4 cell may never be filled by the passage
of time, by absence of records, or by the absence of research attention.

## 9. Response predicate (Phase 10)

A "response" is not a metaphysical category — it is the output of a **declared,
versioned response predicate** over an `ObservedChange`, per (axis × subject ×
action family × methodology).

```text
RESPONSE_PREDICATE (planned)
  predicate_id / version
  axis + subject scope + action-family scope
  input                  ObservedChange (never a raw observation)
  criterion              P1 EXISTENCE: an ObservedChange exists under cited
                               comparison methodology M
                         P2 BOOK6_DEFINED_DIRECTION: M itself yields a
                               direction/threshold verdict Book 6 already defines
                         P3 THRESHOLD_MATERIAL: a magnitude/materiality threshold
  rationale              explicit; versioned; replayable
  evidence_binding       input refs + methodology refs + window ref
```

Dispositions:

```text
P1 EXISTENCE                    = SELECTED (the only default-permitted form;
                                  it asserts "a measured change was recorded",
                                  never "a meaningful/successful change")
P2 BOOK6_DEFINED_DIRECTION      = PERMITTED only where the Book 6 methodology
                                  already defines the verdict (cited, not invented)
P3 THRESHOLD_MATERIAL           = DEFERRED (Class C discipline: empirical
                                  parameters require the D6M-5-style emergence
                                  bar + individual ratification; no such rule
                                  is selected, designed, or ratifiable here)
```

Consequences recorded:

- **No materiality in Book 7.** "Material response" is not a Book 7 concept;
  the field does not exist, so it cannot be filled in. Change of any size is
  recorded descriptively; whether a change is *important* is the operator's
  judgment outside the system, or a future explicitly authorized study.
- A response without a predicate is not a response — it is an unclassified
  observation, and stays `UNASSESSED`.

## 10. Methodology sensitivity (Phase 12)

A response determination is a **methodology-relative** claim, so it must be
re-evaluated under the declared alternatives that could plausibly flip it:

```text
declared alternatives: alternative baseline-selection methodologies,
alternative comparison methodologies, alternative window methodologies,
Book 6 methodology variants (where Book 6 defines them)
recorded per ResponseLink: sensitivity_note_ref (outcomes per alternative)
```

Rules: divergent outcomes across methodologies are **preserved side by side,
never averaged, never silently resolved** (Book 6's methodology-sensitivity
family, inherited); a `CHANGE_OBSERVED` that appears only under one baseline
choice is recorded as methodology-dependent in its own right; no methodology is
a default; methodology identity is always citeable on the record.

## 11. Incentive / confounder handling (Phase 13)

Incentive programs (airdrops, subsidies, fee rebates, emissions, campaign
incentives) and other confounders are recorded as `EventOccurrence` +
`EventObjectImpact` where owning-book records exist, and may be attached to a
`ResponseLink` as **contextual annotations**.

```text
ALLOWED:     annotate a measured change with a concurrent incentive event
FORBIDDEN:   discount, adjust, weight, or negate the measured change
FORBIDDEN:   use the annotation to assert the action (not the incentive) caused
             the change
FORBIDDEN:   use an incentive-driven change as evidence that an action
             "worked" (corpus case 6 stands)
```

An observed change under incentives is a true observation; its attribution is
what the causal layer forbids. Confounder knowledge sharpens the *context*, and
never rewrites the *measurement*.

## 12. Ownership seam (Phase 5 — recorded, not decided)

| Question | Status |
|---|---|
| Does accepted Book 6 (anchor `3919fb8052e216e94034a753fb258d338c5fa0dc`) supply a comparison/change product? | **No.** Accepted Book 6 contracts are MetricDefinition, MeasurementMethodology, MeasurementObservation, ValuationObservation, NormalizationRule, StateRule — no change/comparison product exists. |
| May Book 7 compute the change? | **Not by default.** Only under an explicitly ratified Book 7 comparison methodology, and only with the ownership seam recorded on every record (`BOOK7_LINKAGE_METHODOLOGY`). |
| Which is correct? | **Operator decision — `D7N-7` (CHANGE_PRODUCT_OWNERSHIP_SEAM).** Genuinely required: Book 6 is FROZEN_ACCEPTED, so a Book 6 change product implies a Book 6 amendment + re-acceptance; doctrine does not settle which owner is correct. |
| Interim posture until D7N-7 closes | **Fail-closed:** `CHANGE_NOT_MEASURABLE`; no change product may be emitted. |

## 13. Verdict

```text
DEFECT_REPRODUCED                          = TRUE (9 locations, §1.1)
DEFECT_RECLASSIFIED                         = STRUCTURAL SEMANTIC LEAK (observation != change)
THREE_OBJECTS_DEFINED                      = COMPLETE (PostActionObservation,
                                              ObservedChange, ResponseLink)
BASELINE_CONTRACT                          = PLANNED (selection is methodology; no default)
COMPARABILITY_REQUIREMENTS                 = PLANNED (9 Book 6-compatible gates)
USAGE_RESPONSE_REPAIRED                    = COMPLETE (7-gate rule)
CAPITAL_RESPONSE_REPAIRED                  = COMPLETE (same doctrine, Book 5 source)
OUTCOME_VOCABULARY                          = 9 states, 6 non-collapsions
NO_RESPONSE_OBSERVED_REPAIRED              = COMPLETE (6-condition assertion rule)
RESPONSE_PREDICATE                          = P1 selected; P2 permitted-if-cited; P3 DEFERRED
MATERIALITY_SEPARATED                       = TRUE (no materiality concept exists in Book 7)
METHODOLOGY_SENSITIVITY                     = PLANNED (preserved, un-averaged)
INCENTIVE_CONFOUNDER                        = CONTEXT ONLY (no adjustment, no attribution)
OWNERSHIP_SEAM                              = D7N-7 OPEN (interim fail-closed)
STRUCTURAL_FAILURE_COUNT_AFTER_REPAIR      = 0
BOOK_7_IMPLEMENTATION_AUTHORITY             = FALSE
```

Successors required by this reconciliation: Action Ladder v0.2, Causality
Doctrine v0.2, False-Positive Corpus v0.2, Plan v0.2, Pre-Ratification Review
v0.2 (45 questions), D7N Packet v0.2, Decision Readiness Review v0.1.
