# CSIA — BOOK 6: FUNDAMENTAL MEASUREMENT AND STATE MODELING — PLAN v0.2 (DRAFT)

> **Status:** **DRAFT / PENDING OPERATOR RATIFICATION.**
> **This plan is NOT implementation-authorized.** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Relationship to v0.1:** v0.2 supersedes v0.1 **only upon operator
> ratification**. v0.1 is preserved unmodified as a historical draft and is
> **not ratifiable in its current state** (see
> `CSIA_BOOK_6_STATE_RULE_RECONCILIATION_v0.1.md` for the reproduced
> structural contradiction: v0.1 claimed a universal threshold-free state
> vocabulary while shipping six rule-dependent state names).
> **Predecessor:** Book 5 `FROZEN_ACCEPTED` (anchor
> `50695ad4ea07b57105e71d04d4e32758849e55e3`; exit gate
> `PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL`).
> **Companions (v0.2 set):** State-Rule Reconciliation v0.1 · State Vector
> Design v0.2 · D6M Decision Packet v0.2 · Pre-Ratification Review v0.2. (v0.1
> companions preserved unmodified.)

---

## 0. Goal and constitutional posture

Turn raw architecture/activity evidence into transparent, evidence-backed
**descriptive** measured state — preserving native truth, inventing no health
parameters, and producing no investment score, ranking, or buy/sell framing
(Constitution §5.3a; Axioms 1, 6, 7, 8). The roadmap goal's "investor-facing"
is operationalized strictly as **transparent and descriptive**; the
Constitution governs where the wording could be read prescriptively.

## 1. Governing doctrine (non-negotiable)

```text
Axiom 1  native architecture before normalization
Axiom 5  time is part of truth (valid time + window + revision)
Axiom 6  missing is not false
Axiom 7  discovery does not imply promotion
Axiom 8  descriptive before predictive
§5.3a    no ranking, no composite score, no target, no buy/sell
D2-6     ANNOUNCED != DEPLOYED != USED; health parameters DEFERRED
Book 5   capital/topology truth owned by Book 5; cross-asset valuation owned
         by Book 6 (plan v0.3 §4); BOOK5_CROSS_ASSET_VALUATION_AUTHORITY=FALSE
Book 2   the only epistemic engine
```

## 2. Grammar (v0.1 grammar, unchanged)

Twenty non-collapsible terms with the core separations:

```text
OBSERVATION != MEASUREMENT != METRIC != NORMALIZATION != STATE
RAW != DERIVED;  STOCK != FLOW;  RATE != RATIO;  COUNT != SUM
DISTRIBUTION != CENTRAL_TENDENCY
```

## 3. Planned contracts (NOT implemented)

- `MeasurementObservation` — subject, metric definition, value+unit (only when
  observed), numerator/denominator (measured subjects with own missingness),
  valid/observed time, window, methodology, Book 2 source claims, coverage,
  missingness, quality flags, native scope, status (OBSERVED|SUPERSEDED).
- `MetricDefinition` — identity, semantic definition, domain, unit, type,
  native/normalized, window/aggregation/denominator semantics, allowed sources,
  required evidence, methodology version, comparability class, architecture
  applicability.
- `MeasurementMethodology` — formula, parameters, window, filters, denominator
  rule, source selection, normalization rule, identity rule — all versioned.
  A value without methodology identity is incomplete.
- `ValuationObservation` — subject, native quantity+unit, **required numeraire
  (no default)**, cited price observation + source class + timestamp,
  conversion methodology, valid/observed time, coverage, staleness, status.
- `StateRule` (v0.2 addition) — a named, versioned, ratified **derivation rule**
  for a Class B/C state: predicate, required inputs, window/comparability
  constraints, benchmark (own-history), tolerance / volatility measure /
  decision rule, and applicability per measurement class. Every Class B/C state
  emission cites a `StateRule` identity; without it the state is unavailable.

## 4. Denominator, window, missingness, revision (first-class; unchanged from v0.1)

- **Denominator** is a measured subject with its own missingness
  (PRESENT / ZERO / UNKNOWN / NOT_APPLICABLE / UNAVAILABLE / UNSTABLE); never
  divide through missingness; a changed denominator identity breaks
  comparability.
- **Window** classes with explicit calendar/timezone, late-data, and revision
  behavior.
- **Missingness** — ten distinct states; no collapse; "0 active users" != "no
  active-user data."
- **Revision** — supersession, never overwrite; closed restatement reasons;
  methodology change = new version; reorg bounded; recomputation recorded.

## 5. The v0.2 state doctrine (the repair this plan exists for)

v0.1's "states are threshold-free" claim is **withdrawn**. The operative rule:

```text
NO EMPIRICAL THRESHOLD != NO DERIVATION RULE
EVERY STATE REQUIRES A DERIVATION RULE; a state is emitted only when every
rule it depends on is EXPLICIT, VERSIONED, and RATIFIED.
```

Three state classes:

```text
CLASS A  availability/observation: INSUFFICIENT_DATA, NOT_APPLICABLE,
         RULE_NOT_RATIFIED, COVERAGE_SUFFICIENCY_UNKNOWN — no directional rule
CLASS B  specification-only:       INCREASING, DECREASING, UNCHANGED(per class)
         — ratifiable without empirical research, still an operator act
CLASS C  threshold/benchmark:      STABLE, VOLATILE, EXPANDING, CONTRACTING,
         HIGHER/LOWER_THAN_OWN_HISTORY — UNAVAILABLE_PENDING_RULE
         (EXPANDING/CONTRACTING also DEFERRED as generic forms)
```

Two further repairs:

- **Coverage:** `COVERAGE_OBSERVATION` != `COVERAGE_SUFFICIENCY_RULE`; a
  coverage percentage never becomes a sufficiency judgment without a
  `coverage_sufficiency_ref`.
- **Vector status:** `SCHEMA_COMPLETE` / `DATA_COMPLETE` (non-evaluative).
  `NOT_APPLICABLE` satisfies the schema and does **not** defect an
  architecture-native vector (fixes the v0.1 error); no completeness score.

Own-history comparison cites a `benchmark_methodology_ref` drawn from a
benchmark **namespace** (`PRIOR_COMPARABLE_WINDOW`, `ROLLING_MEAN`,
`ROLLING_MEDIAN`, `HISTORICAL_DISTRIBUTION`, `BASELINE_EPOCH`); none is chosen
by this plan.

## 6. Bloc 6A — native metrics (unchanged from v0.1)

Chain / protocol / token / capital / developer families, each with declared
architecture applicability; NOT_SUPPORTED rather than zero; no valuation
semantics into Book 5; token ≠ protocol ≠ chain.

## 7. Bloc 6B — comparable dimensions (unchanged from v0.1)

Nine dimensions fully answered in the Comparability Matrix v0.1;
native-before-normalized binding; cohorts explicit and versioned;
PERCENTILE_WITHIN_COHORT rejected as a ranking surface.

## 8. Bloc 6C — fundamental state vectors (v0.2)

A vector of descriptive state dimensions — never a score, total, grade, rank,
or weighted composite. Each dimension carries state, state class, explicit rule
references, benchmark identity where applicable, coverage observation +
sufficiency ref, missingness, sensitivity note, valid/observed time. States are
rule-gated per §5. Prescriptive names remain constitutionally prohibited; no
composite may be formed.

## 9. Bloc 6D — validation (unchanged obligations, extended)

Five families (missingness, methodology sensitivity, historical sanity,
cross-source parity, false-comparison detection) plus the anti-score firewall.
v0.2 adds rule-integrity obligations: a state may not be emitted without a
ratified `StateRule`; no hidden tolerance/benchmark; coverage sufficiency
never inferred from a percentage. No test has been run — no Book 6 code exists.

## 10. D2-6 reconciliation (unchanged, still binding)

D2-6 in force; four layers (USAGE OBSERVATION / USAGE METRIC / USAGE STATE /
HEALTH INTERPRETATION); USED evidence-backed; no threshold/band/weight invented;
empirical phase designed-not-executed; successor decision class D6M-5. The
state-rule governance decision (D6M-3) is explicitly **separated** from health
governance so descriptive state rules cannot become a health back door.

## 11. Price authority (v0.2 doctrine, subject to D6M-4)

```text
PRICE_AUTHORITY = PURPOSE x SUBJECT x VALID_TIME x METHODOLOGY
```

No universal price-source class; Book 2 remains epistemic authority for source
evidence; Book 6 methodology selects the price-observation class per purpose
and cites it; divergence preserved, not averaged; D8 untouched.

## 12. Open operator decisions (D6M packet v0.2)

`D6M-1` measurement-object authority boundary (default: Book 6-local derived
record) · `D6M-2` normalization contract shape (leaning: separate
NormalizationRule) · `D6M-3` state derivation rule governance (reframed; must
not absorb D6M-5) · `D6M-4` price-authority doctrine adoption (reframed) ·
`D6M-5` empirical usage/health governance (deferred). None decided here.

## 13. Boundaries (unchanged)

Book 2 = evidence/claims (only engine) · Book 3 = native architecture truth ·
Book 4 = dependency truth (read-only) · Book 5 = capital topology (measure-over,
never rewrite) · Book 6 = measurement definitions + descriptive state · Book 7 =
events/narrative · Book 8 = CSIA↔Sensor seam (D8 deferred) · Sensor = market
mechanics (retained). Three anti-bleed rules binding.

## 14. Exit evidence requirements (future, unauthorized)

6A: ratified metric definitions with preserved native measurements. 6B: a
comparability matrix with no unresolved cells. 6C: a state-vector implementation
whose states are rule-gated (no unratified rule can produce a label), a
structural anti-score firewall, and SCHEMA/DATA status without a quality
reading. 6D: green across all five families, the false-comparison corpus, and
the new rule-integrity obligations. D2-6: deferral intact.

## 15. Plan status

```text
BOOK_6_PLAN = v0.2 DRAFT_PENDING_OPERATOR_RATIFICATION
BOOK_6_PLAN_v0.1 = SUPERSEDED (not ratifiable in current state)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
BOOK_1/3/4/5 amendment = NONE; Book 2 = conditional on D6M-1 off-default;
Constitution = conditional on D6M-1
```
