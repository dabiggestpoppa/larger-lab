# CSIA — BOOK 6 OPERATOR DECISION PACKET (D6M) v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. **No decision is made here.**
> **Namespace:** `D6M-*` (Book 0 already owns `D6`; no collision).
> **Purpose:** surface only decisions the planning stress proved to be
> genuinely structural — i.e. where the alternatives have materially different
> architecture consequences and doctrine does not already answer the question.
> **Grants no implementation authority.**

---

## 0. Discipline applied

A decision is surfaced **only** if all three hold:

1. existing doctrine does **not** already answer it;
2. the alternatives lead to materially different architecture (type shape,
   authority flow, amendment surface, or validation obligations);
3. planning cannot proceed responsibly without a choice.

Everything doctrine already fixes was fixed in the Book 6 sub-documents and is
**not** re-litigated here: native-before-normalized, missing ≠ zero,
descriptive-not-prescriptive, no composite score, ANNOUNCED ≠ DEPLOYED ≠ USED,
Book 2 is the only epistemic engine, Book 5 owns capital truth, Sensor owns
market mechanics.

**Five decisions qualify.**

---

## D6M-1 — Measurement-object authority boundary

**Question.** Is a `MeasurementObservation` a **Book 2 claim** (mintable into
the epistemic engine, carrying claim states and tier promotion), or a
**Book 6-local derived record** that *cites* Book 2 authority for its inputs?

**Why it is structural.** It decides whether measurement currency is expressed
in Book 2 claim states (CONTATED/STALE/REJECTED/SUPERSEDED) or in Book 6
missingness/revision states; whether Book 2 needs a Proposition/claim-vocabulary
amendment; and whether measurement decay reuses the R4/R5 seal machinery.

| Option | Consequence |
|---|---|
| **A. Book 6-local derived record (recommended default)** | no Book 2 amendment; measurement currency = missingness + supersession + live re-resolution of cited claims; single epistemic engine preserved trivially |
| B. Book 2 claim | measurement promotion becomes an epistemic act; requires a Book 2 vocabulary amendment and a decision on which tier a derived measurement occupies; risks measurement re-deciding evidence status |
| C. Hybrid (claim for "headline" metrics only) | two currency models; a measurement could be simultaneously a claim and a record; hardest to keep consistent |

**Planning default if undecided:** Option A (conservative; no amendment).

**Amendment impact:** Book 2 amendment required **only** under B/C; Constitution
amendment possibly required under B (epistemic tier for measurements).

---

## D6M-2 — Normalization contract shape

**Question.** Is normalization (a) an attribute on `MetricDefinition`
(`native_or_normalized`), or (b) a **separate contract class**
(`NormalizationRule` producing a distinct normalized-measurement type)?

**Why it is structural.** (A) is one type with a flag; (B) makes the
native→normalized derivation a first-class object with its own identity,
inputs, and validation. Axiom 1 requires native preservation either way, but
(B) makes the preservation *structurally* unbreakable and makes
methodology-sensitivity reporting natural, at the cost of a second type to
validate.

| Option | Consequence |
|---|---|
| **A. Attribute on the definition** | simpler type surface; native-source chain enforced by validation, not by type |
| B. Separate contract class (recommended) | native→normalized is a typed, replayable derivation; Axiom 1 is type-enforced; sensitivity envelope attaches to the rule |

---

## D6M-3 — State-threshold governance (D2-6-linked)

**Question.** *If/when* usage/health or state thresholds are ever ratified
(currently deferred by D2-6), **who authors them, at what cadence, with what
evidence bar, and are they per-dimension or global?**

**Why it is structural.** Without a governance answer, any state requiring a
threshold is permanently `INSUFFICIENT_DATA`. Global thresholds would also
create the cross-subject adoption judgment D2-6 deliberately avoided;
per-dimension thresholds are more numerous but stay descriptive. The choice
determines the ratification workflow the program inherits.

Planning position (not a decision): thresholds, if ever ratified, are
**per-dimension, cohort-scoped, methodology-versioned, descriptive-only, and
never weighted into a total** (the research-design doc's five conditions). The
open part is *governance* (author, cadence, evidence bar), not shape.

---

## D6M-4 — Valuation price-source authority

**Question.** Which price-source class is authoritative for a Book 6
`ValuationObservation`: evidence-backed reference price, oracle observation,
official redemption value, or a Sensor-exported market observation?

**Why it is structural.** It determines staleness handling, divergence
behavior when sources disagree, cross-source comparability, and whether
valuation is available when a market is closed. It also touches the Book 6 ↔
Sensor seam, which is otherwise D8-deferred — so Book 6 needs *a* provisional
rule without pre-empting D8.

Planning position (not a decision): valuation requires an **explicit cited
price observation with a timestamp and a staleness bound**; disagreement between
sources is preserved, not averaged; no source is a "price of record" for
trading purposes (Sensor retains market mechanics; D8 remains deferred).

---

## D6M-5 — Empirical usage-state governance (D2-6 successor)

**Question.** Who runs the designed empirical research, and what operator
decision class results from it (threshold ratification cadence, evidence bar
for a `USED` state, review triggers)?

**Why it is structural.** D2-6 deferred the parameters; closing them requires a
governed empirical phase and a ratification path. This is the successor
decision class to D2-6, namespaced `D6M-*` to avoid collision with Book 0's
`D6`.

Planning position (not a decision): the research design
(`CSIA_BOOK_6_USAGE_HEALTH_RESEARCH_DESIGN_v0.1.md`) is ready but **not
authorized to execute**; candidates must satisfy its five emergence conditions
(distribution-derived, methodology-robust, cohort-scoped, descriptive-only,
reversible) before any operator decision is opened.

---

## Packet verdict

```text
OPEN_D6M_DECISIONS = 5 (D6M-1..D6M-5)
DECISIONS_MADE_HERE = NONE
BOOK_6_PLAN = may proceed to DRAFT v0.1 with documented planning defaults
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
```

No decision is pre-empted. Planning defaults are conservative and reversible; if
the operator decides otherwise, the affected Book 6 sub-documents are revised
before ratification (and Book 2/Constitution amendments only if D6M-1 → B/C).
