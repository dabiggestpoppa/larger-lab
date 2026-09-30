# CSIA — BOOK 6: FUNDAMENTAL MEASUREMENT AND STATE MODELING — PLAN v0.1 (DRAFT)

> **Status:** **DRAFT / PENDING OPERATOR RATIFICATION.**
> **This plan is NOT implementation-authorized.** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`. No code, no contracts, no metrics are
> implemented by this document.
> **Predecessor:** Book 5 `FROZEN_ACCEPTED` (anchor
> `50695ad4ea07b57105e71d04d4e32758849e55e3`; exit gate
> `PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL`).
> **Ratifies nothing.** The five open `D6M-*` decisions are surfaced, not made.
> **Companions (this planning cycle):** Boundary Review v0.1 · Measurement
> Grammar v0.1 · Native Metrics & Valuation Seam v0.1 · Comparability Matrix
> v0.1 · D2-6 Usage/Health Reconciliation v0.1 · Usage/Health Research Design
> v0.1 · State Vector Design v0.1 · Validation Stress Matrix v0.1 · Metric
> Candidate Matrix v0.1 · Seams & Anti-Score Firewall v0.1 · D6M Decision
> Packet v0.1 · Pre-Ratification Review v0.1.

---

## 0. Goal and constitutional posture

Turn raw architecture/activity evidence into transparent, evidence-backed
**descriptive** measured state — without collapsing native truth, without
inventing health parameters, and without ever producing an investment score,
ranking, or buy/sell framing (Constitution §5.3a; Axioms 1, 6, 7, 8).

Roadmap goal (verbatim): *"Turn raw architecture/activity evidence into
transparent investor-facing state."* Book 6 operationalizes "investor-facing"
strictly as **transparent and descriptive** — never as prescriptive. Where the
roadmap wording could be read prescriptively, the Constitution governs
(descriptive), and this plan resolves it that way.

Canonical blocs and exit gates (roadmap, unchanged):

```text
6A Native metrics            -> PASS_CSIA_B6A_NATIVE_METRICS
6B Comparable dimensions     -> PASS_CSIA_B6B_COMPARISON_LAYER
6C Fundamental state vectors -> PASS_CSIA_B6C_FUNDAMENTAL_STATE_V1
6D Validation                -> PASS_CSIA_B6_FUNDAMENTAL_MEASUREMENT_SEALED
```

## 1. Governing doctrine inherited (non-negotiable)

```text
Axiom 1  native architecture before normalization (normalization only after
         native truth is preserved)
Axiom 5  time is part of truth (valid time + window + revision)
Axiom 6  missing is not false (missingness states; missing != zero)
Axiom 7  discovery does not imply promotion (a source/observation is not a
         metric; only evidence-backed definitions are)
Axiom 8  descriptive before predictive (no forecasting in v0.1)
§5.3a    no ranking, no composite score, no target, no buy/sell
D2-6     ANNOUNCED != DEPLOYED != USED; health parameters DEFERRED
Book 5   capital/topology truth owned by Book 5; cross-asset valuation owned
         by Book 6 (plan v0.3 §4); BOOK5_CROSS_ASSET_VALUATION_AUTHORITY=FALSE
Book 2   the only epistemic engine
```

## 2. Measurement grammar (Phase 3 — see Grammar v0.1)

Twenty non-collapsible terms; the core separations:

```text
OBSERVATION != MEASUREMENT != METRIC != NORMALIZATION != STATE
RAW != DERIVED;  STOCK != FLOW;  RATE != RATIO;  COUNT != SUM
DISTRIBUTION != CENTRAL_TENDENCY
```

No metric name carries undocumented semantics. A "metric definition" answers:
what is measured, in what unit, over what window, under what methodology, with
what denominator, from which sources, within which cohort — "active addresses"
is a label, not a definition.

## 3. Planned contracts (NOT implemented)

### 3.1 `MeasurementObservation`

Mandatory: subject_ref, metric_definition_ref, value+unit (only when observed),
numerator/denominator (with own observations + missingness), valid_time,
observed_at, window_start/end, methodology_ref, source_claim_refs, coverage,
missingness_state, quality_flags, native_scope, status (OBSERVED|SUPERSEDED).
Mandatory-by-class is tabulated in the Grammar v0.1 §2.1.

### 3.2 `MetricDefinition`

Identity, semantic definition, subject domain, unit, measurement type,
native-vs-normalized, window semantics, aggregation semantics, denominator
semantics, allowed source families, required evidence tier, methodology
version, comparability class, architecture applicability.

### 3.3 `MeasurementMethodology`

Formula, parameters, window rule, filters, denominator rule, source selection,
normalization rule, identity rule — all versioned. **A value without
methodology identity is incomplete.** Same name + different methodology ≠ same
comparable observation.

### 3.4 `ValuationObservation` (Book 5 → Book 6 seam)

Subject, native quantity+unit, **required numeraire (no default)**, cited price
observation + source + timestamp, conversion methodology, valid time,
observed_at, coverage, staleness, status. No hidden USD; no mixed timestamps;
no valuation of an aggregate unless methodology permits; no attractiveness.

## 4. Denominator + window + missingness + revision (first-class)

- **Denominator:** a first-class measured subject with its own missingness.
  States: PRESENT / ZERO / UNKNOWN / NOT_APPLICABLE / UNAVAILABLE / UNSTABLE.
  Never divide through missingness; zero denominator → UNDEFINED_RATIO (not a
  number); a changed denominator identity makes series non-comparable.
- **Window:** INSTANTANEOUS / BLOCK-EPOCH / DAILY / ROLLING / CALENDAR_WEEK /
  CALENDAR_MONTH / QUARTER / LIFETIME / EVENT_BOUNDED / CUSTOM, each with
  timezone/calendar, late-data, and revision behavior explicit.
- **Missingness:** OBSERVED / ZERO_OBSERVED / NOT_APPLICABLE / NOT_SUPPORTED /
  NOT_AVAILABLE / NOT_COLLECTED / SOURCE_UNAVAILABLE / STALE / PARTIAL_COVERAGE
  / UNKNOWN — stress-tested (6D.1) before names are ratified; **"0 active
  users" != "no active-user data."**
- **Revision:** supersession, never overwrite; restatement reasons from a closed
  set; methodology change = new version; reorg bounded; derived
  metrics/states recompute as recorded supersessions.

## 5. Bloc 6A — native metrics (Phase 11)

Native measurement families per 6A.1 (chain), 6A.2 (protocol), 6A.3 (token),
6A.4 (capital, measuring over Book 5), 6A.5 (developer, source-tagged). Each
family declares architecture applicability; a family absent for a family is
NOT_SUPPORTED, never zero. **No valuation semantics leak into Book 5.** No
family is forced onto every chain. No protocol economic model is assumed
shared. Token ≠ protocol ≠ chain (Axiom 2).

## 6. Bloc 6B — comparable dimensions (Phase 14)

The nine roadmap dimensions (activity, capital, liquidity, developer growth,
integration growth, dependency centrality, token utility, value capture,
economic security) each fully answered in the Comparability Matrix v0.1
(native inputs, architecture support, comparability destroyers, denominator,
allowed transformation, missingness propagation, methodology requirement).
**Native before normalized is binding** (Axiom 1). Cohorts are explicit and
versioned; "all chains" is never an automatic cohort. Normalization candidates
are listed with structural-validity notes; PERCENTILE_WITHIN_COHORT is
**rejected** (a ranking surface in disguise). Several normalizations are invalid
for specific (metric × cohort) pairs.

## 7. Bloc 6C — fundamental state vectors (Phase 20)

A `FundamentalStateVector` is a **vector of descriptive state dimensions** —
never a score, total, grade, rank, or weighted composite (Constitution §5.3a;
roadmap "no composite investment rating"). Each dimension carries state,
measurement refs, methodology ref, valid/observed time, missingness, coverage,
epistemic status, and a sensitivity note. States are **own-history-relative**
and threshold-free: INCREASING/DECREASING/STABLE/VOLATILE/EXPANDING/CONTRACTING/
HIGHER_THAN_OWN_HISTORY/LOWER_THAN_OWN_HISTORY/INSUFFICIENT_DATA/
NOT_APPLICABLE. Prescriptive names (ATTRACTIVE, HEALTHY, TOP_TIER, BUY, …) are
constitutionally prohibited. Every state is replayable from stored
measurement_refs + methodology + window; no state from analyst prose; no hidden
weights; no hidden thresholds.

## 8. Bloc 6D — validation (Phase 23)

Five families, planned as future test obligations: 6D.1 missingness, 6D.2
methodology sensitivity (flips are surfaced), 6D.3 historical sanity
(supersession preserves originals), 6D.4 cross-source parity (no silent
averaging; Book 2 governs currency), 6D.5 false-comparison detection (15-row
corpus refused or gated). Plus the anti-score firewall tests. None run yet —
no Book 6 code exists.

## 9. D2-6 reconciliation (Phase 18)

D2-6 remains in force. Four layers — USAGE OBSERVATION / USAGE METRIC / USAGE
STATE / HEALTH INTERPRETATION — with HEALTH deferred. USED must be
evidence-backed; a "used"-like state reads INSUFFICIENT_DATA until parameters
are ratified. No threshold, band, cutoff, weight, or score is invented anywhere
in this plan. The empirical phase is **designed, not executed**; candidates must
emerge from distributions under five conditions. Successor decision class
namespaced **D6M-5**.

## 10. Open operator decisions (Phase 32)

`D6M-1` measurement-object authority boundary · `D6M-2` normalization contract
shape · `D6M-3` state-threshold governance · `D6M-4` valuation price-source
authority · `D6M-5` empirical usage-state governance. None is decided here;
conservative planning defaults are documented in the D6M packet and are
reversible.

## 11. Boundaries (Phase 2, carried)

Book 2 = evidence/claims (only epistemic engine) · Book 3 = native architecture
truth · Book 4 = dependency truth (read-only to Book 6) · Book 5 = capital
topology/principal truth · Book 6 = measurement definitions + descriptive state
· Book 7 = events/narrative · Book 8 = CSIA↔Sensor seam (D8 deferred) · Sensor
= market mechanics (retained). Three anti-bleed rules are binding: Book 6 may
not rewrite a subject truth it measures, may not manufacture a number in a
domain it does not own, and may not upgrade measurement into subject truth.

## 12. Exit evidence requirements (future phases, unauthorized today)

To earn each gate, a future implementation must provide: ratified 6A metric
definitions with preserved native measurements; a 6B comparability matrix with
no unresolved cells; a 6C state-vector implementation with a structural
anti-score firewall and replayable states; a 6D validation run green across all
five families plus the corpus; and a D2-6 reconciliation that keeps the
deferral intact. Evidence requirements are documented, not exercised.

## 13. Plan status

```text
BOOK_6_PLAN = v0.1 DRAFT_PENDING_OPERATOR_RATIFICATION
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
BOOK_1..5 / CONSTITUTION amendments = NONE required (Book 2 conditional on D6M-1)
```
