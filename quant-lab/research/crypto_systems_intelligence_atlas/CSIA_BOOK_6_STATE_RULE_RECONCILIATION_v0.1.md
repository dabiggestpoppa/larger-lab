# CSIA — BOOK 6 STATE-RULE RECONCILIATION v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Trigger:** external review finding — a concrete structural contradiction in
> Bloc 6C of Book 6 plan v0.1.
> **Finding accepted:** the v0.1 state vocabulary contains rule-dependent
> states while the plan claims a universal threshold-free property. v0.1's
> claim is **TOO STRONG** and is superseded by this reconciliation.
> **Book 6 plan v0.1, state-vector v0.1, D6M packet v0.1, and pre-ratification
> review v0.1 are preserved UNMODIFIED as historical drafts** and are marked
> superseded-pending-ratification by the v0.2 set. No v0.1 file is edited to
> hide the defect.

---

## 1. Reproduction — where v0.1 hides unratified rules

Audit terms: `threshold-free`, `STABLE`, `VOLATILE`, `EXPANDING`,
`CONTRACTING`, `HIGHER_THAN_OWN_HISTORY`, `LOWER_THAN_OWN_HISTORY`,
`coverage floor`, `comparison basis`, `own-history`, `benchmark`, `threshold`,
`cutoff`, `band`, `epsilon`, `sensitivity`.

| # | Artifact : line | Claim as written | What is actually required | Status |
|---|---|---|---|---|
| 1 | `CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.1.md:43` | "Threshold-free derivable state?" as a per-dimension question | every listed state needs a derivation rule; some need an empirical parameter | **CONTRADICTION** |
| 2 | `CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.1.md:45` | column header "Threshold-free state possible?" | — | **CONTRADICTION** |
| 3 | `CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.1.md:63` | "**Allowed** (descriptive, threshold-free, own-history or data-absence):" followed by `STABLE`, `VOLATILE`, `EXPANDING`, `CONTRACTING`, `HIGHER_THAN_OWN_HISTORY`, `LOWER_THAN_OWN_HISTORY` | each of those six embeds a tolerance / measure / benchmark / transition rule that is unspecified | **CONTRADICTION (6 states)** |
| 4 | `CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.1.md:126` | "INCOMPLETE if coverage is below coverage floor" | a coverage floor is a **rule identity + threshold**, and none is ratified | **CONTRADICTION** |
| 5 | `CSIA_BOOK_6_D2_6_USAGE_HEALTH_RECONCILIATION_v0.1.md:87-96` | "## 5. States that need no threshold … These descriptive states are threshold-free" with the same six states listed | identical defect as #3, repeated as a *permission* | **CONTRADICTION** |
| 6 | `CSIA_BOOK_6_FUNDAMENTAL_MEASUREMENT_STATE_MODELING_PLAN_v0.1.md:151` | "own-history-relative **and threshold-free**: INCREASING/…/STABLE/VOLATILE/EXPANDING/CONTRACTING/HIGHER_THAN_OWN_HISTORY/LOWER_THAN_OWN_HISTORY" | same defect, at plan level | **CONTRADICTION** |
| 7 | `CSIA_BOOK_6_VALIDATION_STRESS_MATRIX_v0.1.md:15` | 6D.1 obligation "coverage floors enforced" | enforces a rule that does not exist | **CONTRADICTION** |

Cross-check: `CSIA_BOOK_6_PRE_RATIFICATION_REVIEW_v0.1.md` row 13 answered "Can
state thresholds be hidden?" with **No**. That answer was **not supported** by
v0.1's own vocabulary, which hid six unratified rules inside label names. Row 13
is re-answered in the v0.2 review against the repaired design.

Naming-collision note (not a defect, recorded to prevent confusion):
`CSIA_BOOK_6_MEASUREMENT_GRAMMAR_v0.1.md:153` defines
`DENOMINATOR_UNSTABLE` (a denominator whose value is contested/stale). This is
**not** the `STABLE` state and must never be read as one.

### Verdict

```text
STATE_VOCABULARY_CONTAINS_RULE_DEPENDENT_STATES = TRUE
PLAN_v0.1_THRESHOLD_FREE_CLAIM = TOO_STRONG
CONFLICTS_WITH = D2-6 deferral; D6M-3 open governance; no-hidden-threshold
                  doctrine; pre-ratification row 13
RATIFICATION_BLOCKED = TRUE (v0.1 must not be ratified in this state)
```

## 2. Corrected doctrine (replaces the universal threshold-free claim)

```text
NO EMPIRICAL THRESHOLD != NO DERIVATION RULE

EVERY STATE REQUIRES A DERIVATION RULE.
A STATE MAY BE EMITTED ONLY WHEN ALL RULES REQUIRED TO DERIVE IT ARE
EXPLICIT, VERSIONED, AND RATIFIED.

NO HIDDEN RULE. NO HIDDEN THRESHOLD. NO HIDDEN EPSILON. NO HIDDEN BENCHMARK.
```

Some states need no empirical cutoff. Others need a threshold or benchmark
rule. Neither fact licenses an unratified state, and neither licenses a plan
that claims the whole vocabulary is threshold-free.

## 3. The three state classes

### CLASS A — availability / observation states (no directional rule)

```text
INSUFFICIENT_DATA          required input is not observed / not usable
NOT_APPLICABLE             the dimension's measurement does not exist for this
                           subject or architecture
RULE_NOT_RATIFIED          the required derivation rule is not ratified
COVERAGE_SUFFICIENCY_UNKNOWN   coverage was observed; sufficiency is unjudged
                               (no ratified coverage-sufficiency rule)
```

Class A states are decided by inspecting the input set and the rule registry.
They require **no** directional predicate, **no** threshold, and **no**
benchmark. They are available for emission under the state-availability rule
itself. They are also the *fallback* for every Class B/C state whose rule is
unratified: a dimension that cannot be derived resolves to
`RULE_NOT_RATIFIED` (or `INSUFFICIENT_DATA`), never to a guessed label.

### CLASS B — specification-only rule states (no empirical cutoff)

A state is Class B only if its **complete predicate** is fully specified and
versionable without any data-dependent parameter.

```text
INCREASING  <=>  current observation  >  prior comparable observation
DECREASING  <=>  current observation  <  prior comparable observation
UNCHANGED   <=>  current observation  =  prior comparable observation
```

Even these require, as part of the ratified derivation rule:

1. same methodology version on both observations;
2. same unit;
3. same denominator (and same denominator missingness state);
4. same cohort where the metric is cohort-scoped;
5. **window compatibility** (a window is comparable only to a same-class
   window — a 7-day window is not comparable to a 30-day window);
6. a valid, non-superseded prior comparable observation;
7. a precision / rounding rule (see §4.2);
8. no significance claim: ordering only, never statistical significance.

Status: **PENDING_RULE_RATIFICATION**. Ratifiable by specification alone (no
empirical research), but still requires an operator act under D6M-3 — so not
available today.

### CLASS C — threshold / benchmark-dependent states (UNAVAILABLE_PENDING_RULE)

```text
STABLE, VOLATILE, EXPANDING, CONTRACTING,
HIGHER_THAN_OWN_HISTORY, LOWER_THAN_OWN_HISTORY
```

Each requires, before it may be emitted: a named methodology, a benchmark
definition, a threshold/rule identity, a window, a comparison basis, and a
version. Until that rule is ratified, each is `UNAVAILABLE_PENDING_RULE`, and
the dimension resolves to a Class A state.

## 4. Per-state determination

### 4.1 INCREASING / DECREASING — Class B, pending ratification

Required observations: a current observation and a prior **comparable**
observation (same methodology/unit/denominator/cohort/window class). Comparison
ordering: strict `>` / `<` on the declared numeric or lexicographic ordering of
the measurement type. Window compatibility: only same-class windows. Revision
handling: a superseded prior observation is not a comparison basis; the
superseding one is (or the comparison is re-derived). Missingness: any
non-observed input ⇒ Class A fallback. Precision: comparison uses the
methodology's declared precision; a difference below declared precision is
**not** an increase.

### 4.2 UNCHANGED — Class B, **conditionally available**

Exact equality is semantically valid only for measurement classes where equality
is well defined: discrete counts, presence/absence, set identity, and other
exact-valued classes. For continuous measurements, rounded displays, or values
with estimation error, exact equality is an artifact of precision — so
`UNCHANGED` is **UNAVAILABLE_PENDING_RULE** for those classes (it would need a
tolerance, which is Class C).

**`UNCHANGED` is not `STABLE`.** Equality is an identity statement about two
values; stability is a band statement about dispersion over time. They are
different predicates with different required rules. Collapsing them would
smuggle a tolerance into an equality claim.

### 4.3 STABLE — Class C, `UNAVAILABLE_PENDING_RULE`

A realistic STABLE needs at least one of: an absolute tolerance, a relative
tolerance, a noise model, a measurement-precision model, or a historical
dispersion rule. None is ratified. Until a versioned stability methodology is
ratified, STABLE is unavailable, and the dimension resolves to a Class A state.

Epsilon may not be introduced later inside implementation code; a tolerance is
a ratified, versioned rule field, not a constant.

### 4.4 VOLATILE — Class C, `UNAVAILABLE_PENDING_RULE`

`VOLATILE` is **not a primitive state name**. It names a decision over a
volatility measurement, and the candidate measurements are different things:

```text
standard deviation            (dispersion, units of the measure)
median absolute deviation     (robust dispersion)
realized range                (peak-to-trough span)
coefficient of variation      (scale-free dispersion; invalid for
                              interval/ratio/zero-mean measures)
state-transition frequency    (a count of transitions, not dispersion)
```

Each requires a volatility measure, a window, a comparison basis, and a
decision rule. Different choices can disagree on the same data. Therefore
VOLATILE requires a `volatility_measure_ref` + `decision_rule_ref` before
emission, and is unavailable until ratified.

### 4.5 EXPANDING / CONTRACTING — Class C, `UNAVAILABLE_PENDING_RULE` / DEFER

A label may not inherit its meaning from English. "Expanding" must name **what**
is expanding: activity count, capital stock, distribution width, integration
count, liquidity depth, or something else. There is no generic predicate that
works across these dimensions, and the comparison rule differs by dimension.

Determination: the **generic** forms `EXPANDING` / `CONTRACTING` are **DEFER** —
not merely unavailable. They may be introduced only as **dimension-specific**
states with an explicit `target_measurement_ref`, transformation, comparison
rule, window, and ratified methodology. English "expansion" is not a
specification.

### 4.6 HIGHER_THAN_OWN_HISTORY / LOWER_THAN_OWN_HISTORY — Class C

`OWN_HISTORY` is a **benchmark namespace, not a benchmark**. Candidate benchmark
families (planning only — **none is selected here**):

```text
PRIOR_COMPARABLE_WINDOW   the immediately prior same-class window
ROLLING_MEAN              mean over a declared trailing window
ROLLING_MEDIAN            median over a declared trailing window
HISTORICAL_DISTRIBUTION   position within a declared historical distribution
                          (e.g. a declared quantile of the subject's own history)
BASELINE_EPOCH            comparison against a declared origin event/epoch
```

These are not interchangeable and can disagree on the same data. Every such
state must cite `benchmark_methodology_ref`. Without it, the dimension
resolves to `RULE_NOT_RATIFIED` (or `INSUFFICIENT_DATA`) — never to a
self-comparison with an implicit baseline.

## 5. Coverage-floor repair

v0.1 asserted an INCOMPLETE verdict "below coverage floor" while no floor is
ratified, and 6D.1 asserted "coverage floors enforced". Both are repaired by
separating two different objects:

```text
COVERAGE_OBSERVATION     a number + its basis (what fraction of the intended
                         population was actually observed)
COVERAGE_SUFFICIENCY_RULE a ratified rule identity that says what coverage is
                         sufficient *for a given state methodology*
```

Rules:

1. A coverage of 0.72 may be observed without Book 6 judging whether 0.72 is
   sufficient. Observation ≠ judgment.
2. Sufficiency requires `coverage_sufficiency_ref`. Absent that ref, the
   verdict is `COVERAGE_SUFFICIENCY_UNKNOWN` (Class A) — never `INCOMPLETE`
   inferred from a percentage, and never `COMPLETE`.
3. `PARTIAL_COVERAGE` (a source-established fact about population coverage) is
   **not** the same as `INSUFFICIENT_FOR_THIS_STATE` (a state-methodology
   judgment). `PARTIAL != INSUFFICIENT` unless a ratified state methodology
   says so.
4. The sufficiency rule may legitimately differ per state methodology: a
   threshold-free Class B direction rule may tolerate lower coverage than a
   dispersion-based Class C rule. There is no global floor without a ratified
   global floor rule.

## 6. Vector-completeness repair

v0.1 said any `NOT_APPLICABLE` makes the vector INCOMPLETE. That is **wrong for
architecture-native modeling** (Axiom 1): a metric genuinely not applicable to
an architecture is a structural fact about the subject, not a defect in it.

v0.1 also risks `COMPLETE` reading as a quality judgment. Repaired as two
**non-evaluative, structural** statuses (no score, no percentage, no ordering):

```text
SCHEMA_COMPLETE   every slot in this vector's schema resolves to some state —
                  a derived state, a Class A availability state, or
                  NOT_APPLICABLE. No slot is unresolved.

DATA_COMPLETE     every slot that is APPLICABLE has an observed derivation
                  whose coverage is sufficient under a ratified
                  coverage-sufficiency rule.
```

Consequences:

- `NOT_APPLICABLE` satisfies the schema but not the data requirement: a subject
  may be `SCHEMA_COMPLETE` while not `DATA_COMPLETE`. That is correct, not a
  defect.
- "complete" never means "good", "high quality", or "fully healthy"; it names
  slot resolution only.
- There is no completeness score, no completeness percentage, and no ordering
  of subjects by completeness.

## 7. D6M-3 reframe — state derivation rule governance

v0.1's D6M-3 mixed three different things (state thresholds, usage/health
thresholds, general state-rule governance). Reframed:

```text
D6M-3 = STATE DERIVATION RULE GOVERNANCE
```

It governs, for **Class B and Class C** state methodologies:

- who may ratify a rule-dependent state methodology (and the evidence bar);
- the review cadence;
- versioning and supersession of state rules;
- benchmark rules (`PRIOR_COMPARABLE_WINDOW` vs `ROLLING_MEAN` vs …);
- coverage-sufficiency rules (per state methodology);
- empirical tolerance/threshold rules where a state genuinely needs them.

It governs **descriptive** state rules only. It **does not** authorize health
interpretation, usage thresholds, or adoption judgments. Those remain with
**D6M-5**, the D2-6 empirical usage/health successor. Keeping these separate is
structural: D6M-3 must not become a back door to health governance.

## 8. D6M-4 stress — the original framing is structurally wrong

v0.1's D6M-4 asked the operator to choose **one authoritative price-source
class**. That question offers false alternatives: the stress cases below have
no single correct global winner, because the correct authority depends on the
valuation **purpose** and the **subject**.

| Case | Purpose-appropriate authority | Why a global class fails |
|---|---|---|
| USDC redeemable at $1 (official value) | issuer/redemption (par) value | a $0.997 market print is a market observation, not a refutation of redemption value |
| thin token with an exchange market price | market observation (Sensor-exported), with coverage/staleness | an official/par value is not applicable |
| on-chain collateral marked by an oracle | the protocol's designated oracle observation (Book 2-backed evidence of it) | a market venue price is a different mark for a different purpose |
| perp collateral under a venue index | the venue's index/mark methodology | disagreement with an external market price is not a contradiction; it is a different purpose |
| RWA NAV | issuer/attested NAV at its valid time | a market price for an illiquid instrument may not exist or may not be authoritative |
| illiquid LP token | position NAV (methodology-explicit) or market with coverage caveats — possibly `NOT_AVAILABLE` | no single class fits; refusal is a legitimate outcome |
| wrapped asset | underlying's authoritative price + the wrapper's peg/redemption methodology | a depeg is a *measurement*, not a price-source error |
| stale market | insufficiency against the declared staleness bound | validity is time-relative (bitemporal), not class-relative |
| market closed | `NOT_AVAILABLE` for current valuation; historical valid-time valuation remains | again time-relative |
| oracle divergence | both observations preserved under their own purposes | averaging them would invent a third source |
| Sensor price vs official redemption value divergence | preserved separately; divergence is a finding | a "consensus price" is not available without a ratified reconciliation rule |

### Repaired doctrine

```text
PRICE_AUTHORITY = PURPOSE x SUBJECT x VALID_TIME x METHODOLOGY
```

- There is **no** universal authoritative price-source class.
- **Book 2 remains the epistemic authority** for the evidence behind each price
  observation; Book 6 never re-adjudicates source evidence.
- **Book 6 methodology** selects the correct price-observation *class* for the
  declared valuation purpose, and must cite it.
- Divergence between classes is preserved, never averaged.
- **D8 remains untouched**: no shared CSIA↔Sensor seam decision is made here,
  and Sensor retains all market-state mechanics.

D6M-4 is therefore **re-framed** (not withdrawn): it now asks whether to adopt
this purpose-specific authority doctrine, and who ratifies
price-observation-class-per-purpose rules — not which class wins globally.

## 9. D6M decision audit (all five re-evaluated)

| ID | v0.1 framing | v0.2 disposition |
|---|---|---|
| D6M-1 | measurement-object authority boundary (Book 2 claim vs Book 6-local record) | **RETAINED, unchanged.** The conservative default (Book 6-local derived record) holds; it is the only decision that can force a Book 2/Constitution amendment |
| D6M-2 | normalization contract shape (attribute vs separate contract) | **RETAINED, leaning recorded.** A separate `NormalizationRule` contract is structurally cleaner: it makes native-source lineage a first-class, replayable, type-enforced object. Still the operator's call |
| D6M-3 | mixed state / usage / health thresholds | **REFRAMED** → state derivation rule governance (§7); must not absorb D6M-5 |
| D6M-4 | choose one authoritative price-source class | **REFRAMED** → adopt purpose×subject×valid-time×methodology authority doctrine + its rule-ratification governance (§8). The original question offered false alternatives and is repaired, not re-asked |
| D6M-5 | empirical usage/health governance (D2-6 successor) | **RETAINED, unchanged.** Still deferred; the empirical phase remains designed-not-executed |

```text
OPEN_D6M_DECISIONS = 5 (D6M-1, D6M-2, D6M-3-reframed, D6M-4-reframed, D6M-5)
DECISIONS_RECORDED = 0
```

## 10. Unratified rule-dependent states (explicit list)

Emission must be refused for every one of these until its rule is ratified:

```text
STABLE                     (tolerance / noise / dispersion rule)
VOLATILE                   (volatility measure + decision rule)
EXPANDING                  (target measurement + comparison rule; generic form
                            additionally DEFERRED)
CONTRACTING                (same as EXPANDING)
HIGHER_THAN_OWN_HISTORY    (benchmark family + decision rule)
LOWER_THAN_OWN_HISTORY     (benchmark family + decision rule)
UNCHANGED                  (per measurement class: unavailable where exact
                            equality is not semantically valid)
INCREASING / DECREASING    (derivation rule + window-compatibility + precision)
```

Class A states (`INSUFFICIENT_DATA`, `NOT_APPLICABLE`, `RULE_NOT_RATIFIED`,
`COVERAGE_SUFFICIENCY_UNKNOWN`) require no such rule and are the only states
available for emission under a ratified state-availability rule.

## 11. Reconciliation verdict

```text
CONTRADICTION_REPRODUCED = TRUE (7 sites, 5 artifacts)
THRESHOLD_FREE_CLAIM = TOO_STRONG (superseded by §2 doctrine)
STATE_CLASSES = 3 (A availability / B specification-only / C threshold-benchmark)
CLASS_C_STATES = UNAVAILABLE_PENDING_RULE (explicit list, §10)
COVERAGE = OBSERVATION != SUFFICIENCY (separate objects + rule ref)
VECTOR_STATUS = SCHEMA_COMPLETE / DATA_COMPLETE (non-evaluative; v0.1 error fixed)
D6M-3 = REFRAMED (state rule governance; not health)
D6M-4 = REFRAMED (purpose-specific price authority; false alternatives removed)
OPEN_D6M_DECISIONS = 5 (0 recorded)
BOOK_6_PLAN_v0.1 = SUPERSEDED_PENDING_RATIFICATION (not ratified)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
```
