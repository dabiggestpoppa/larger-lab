# CSIA — BOOK 6 SEAMS AND ANTI-SCORE FIREWALL v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Scope:** Phases 28–31 — Book 5 / Book 4 / Sensor measurement seams and the
> explicit anti-score firewall.
> **Purpose:** prove that each Book 6 measurement class has exactly one
> canonical owner, and that nothing in Book 6 can host an investment score.

---

## 1. Book 5 / Book 6 measurement seam (Phase 28)

Every prior "aggregate candidate" is classified as one of:

- `BOOK_5_TOPOLOGY_DERIVATION` — a fact derivable from Book 5 canonical records
  using Book 5 methodology (it belongs to Book 5 and is measured *over* by
  Book 6, never re-derived here);
- `BOOK_6_MEASUREMENT_METRIC` — a measured, windowed, methodology-versioned
  metric that requires a definition Book 5 does not own (typically because it
  needs a numeraire, a time window, or a normalization).

| Candidate | Classification | Why |
|---|---|---|
| TVL-like totals | **split**: per-construct same-unit stock = `BOOK_5_TOPOLOGY_DERIVATION`; a single cross-venue "TVL" number = **REJECTED** (corpus #6/#7; Book 5 forbids the merge) | heterogeneous capital constructs are not one metric |
| capital concentration | `BOOK_6_MEASUREMENT_METRIC` (distribution over a Book 5 component set) | needs a distribution + window + methodology Book 5 does not define |
| utilization | `BOOK_6_MEASUREMENT_METRIC` (ratio with explicit denominator = supplied) | Book 5 owns supplied/borrowed facts; the ratio is measurement |
| normalized liquidity | `BOOK_6_MEASUREMENT_METRIC` (normalization + depth methodology) | executable depth is a measurement, not a Book 5 record |
| capital efficiency | `BOOK_6_MEASUREMENT_METRIC` (flow/capital ratio, per unit, per window) | requires a time dimension Book 5 does not own |
| common-value exposure | `BOOK_6_MEASUREMENT_METRIC` (ValuationObservation, explicit numeraire) | cross-asset valuation is Book 6 by ratified seam |
| cross-asset capital totals | `BOOK_6_MEASUREMENT_METRIC`, strictly a valuation product (heterogeneous vector → total only under explicit methodology) | the one place Book 6 may total across units — never backward |

**No authority bleed:** Book 6 never re-computes a Book 5 aggregate under a
different method and calls it a correction; a discrepancy is a
methodology-sensitivity finding (6D.2), not a rewrite. `SHARE FRACTION !=
VALUATION` and `PROPORTIONAL != COMMON-NUMERAIRE VALUE` hold at this seam.

## 2. Book 4 / Book 6 seam (Phase 29)

**Book 4 owns (read-only to Book 6):** the dependency graph, failure domains,
substitutability, hard-runtime semantics.

**Book 6 may derive (measurement over Book 4 records):** measured centrality
(degree / betweenness, per a named graph metric), concentration, and
dependency-count distributions.

**Book 6 may not:** add/remove/re-weight a dependency edge, re-scope an edge
family, treat a count as a dependency fact, or use a measurement to override
topology. If measurement and topology disagree, the *measurement* is wrong
(methodology), not the graph.

Centrality is only comparable within a named Book 4 graph metric and a declared
edge-family scope; a `betweenness` value and a `degree` value are different
metrics, never a series.

## 3. Book 6 / Sensor seam (Phase 30 — provisional, D8 not decided)

D8 is **not** performed; the CSIA ↔ Sensor context seam is deferred to the Book
8 gate. This is provisional ownership for planning only:

- Book 6 consumes market observations **only** for an explicitly authorized
  measurement/valuation methodology.
- Book 6 may **not** redefine price state, funding, OI, liquidations, basis, or
  market regime — Sensor retains all market-state mechanics.
- No shared-seam ownership decision is finalized here; `D8 = DEFERRED`.
- Which price-source class is authoritative for a Book 6 valuation is an open
  operator decision (D6M-4), not decided here.

## 4. Anti-score firewall (Phase 31)

### 4.1 Forbidden (constitutionally)

```text
single overall fundamental score
weighted "quality score"
ranked token / protocol / chain list
best / worst ecosystem ordering
buy / sell / hold conversion
valuation-attractiveness state ("cheap", "expensive", "undervalued")
implicit recommendation through label or ordering
```

### 4.2 Permitted (descriptive)

```text
multi-dimensional descriptive vector (no total)
native measurements (with definitions and methods)
normalized dimensions where the comparability matrix licenses them
methodology-sensitivity surfacing
peer / context comparison without investment ordering
descriptive states from the closed vocabulary
own-history comparisons
```

### 4.3 The firewall is structural, not editorial

The firewall must be enforced by the type system and validation, not by review
goodwill. A future Book 6 implementation must make it *impossible* to express:

- a `FundamentalStateVector` with a total/score/rank/grade field (type-level
  prohibition);
- a state name outside the closed vocabulary (enum, not string);
- a percentile/rank normalization as a comparison output (rejected in the
  comparability matrix);
- a valuation output without `numeraire` (required field, no default);
- a normalized metric without a resolvable native-source chain (Axiom 1).

These belong to the 6D firewall test family so they are testable obligations
for the (unauthorized) implementation phase.

## 5. Seam verdict

```text
BOOK_5_SEAM = ONE_DIRECTIONAL (measure-over, never rewrite; split per candidate)
BOOK_4_SEAM = READ_ONLY_GRAPH (derive centrality, never edit topology)
SENSOR_SEAM = PROVISIONAL (market mechanics retained by Sensor; D8 deferred)
ANTI_SCORE_FIREWALL = STRUCTURAL (type-level, testable; no ranking/composite)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
```
