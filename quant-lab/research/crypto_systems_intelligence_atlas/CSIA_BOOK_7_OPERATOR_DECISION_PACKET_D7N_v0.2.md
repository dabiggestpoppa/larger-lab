# CSIA — BOOK 7 OPERATOR DECISION PACKET — D7N v0.2

> **Status:** DECISION PACKET v0.2 — DRAFT. Surfaces operator decisions;
> **decides none.** Directly executable as an operator response sheet: each
> decision carries an `operator_selection:` slot (see §0).
> **Date:** 2026-10-01
> **Authority:** `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **v0.1 preserved unmodified** (`CSIA_BOOK_7_OPERATOR_DECISION_PACKET_D7N_v0.1.md`).
> **Namespace:** `D7N` — verified collision-free in v0.1 and re-verified here
> (decision log / Constitution / roadmap); distinct from the closed `D7`
> (Capital Field) and from `D6M-*`.
> **Change from v0.1:** D7N-1..D7N-6 carried forward verbatim in substance;
> **D7N-7 added** (see §7) — it is genuinely required because the response-layer
> repair introduced a change-comparison concept that no ratified Book 6 contract
> covers, and only the operator can assign its ownership. All options gain
> explicit consequence, amendment-impact, and implementation-impact lines.

---

## 0. Operator response sheet (fill `operator_selection:` for each)

```text
D7N-1  operator_selection: ________  (A | B | C | DEFER)
D7N-2  operator_selection: ________  (A | B | C | DEFER)
D7N-3  operator_selection: ________  (A | B | C | DEFER)
D7N-4  operator_selection: ________  (A | B | DEFER)
D7N-5  operator_selection: ________  (A | B | DEFER)
D7N-6  operator_selection: ________  (A | B | DEFER)
D7N-7  operator_selection: ________  (A | B | C | DEFER)
operator_notes: ______________________________________________
```

An unanswered slot = `DEFER` (nothing is inferred from silence; no default is
applied — the session-integrity rule of the existing decision log). Any
`BOOK_6_AMENDMENT_REQUIRED = TRUE` consequence below is surfaced explicitly, not
inferred by planning.

---

## D7N-1 — EVENT IDENTITY AUTHORITY *(carried from v0.1; content unchanged)*

**Question:** who/what resolves whether two reports describe the same
occurrence, and by what doctrine?

| Option | Model | Consequence | Amendment impact | Implementation impact |
|---|---|---|---|---|
| A | OCCURRENCE_EVIDENCE_FIRST — identity binds on family-defined occurrence signatures (tx ids, proposal ids, incident ids); unresolved groups stay `IDENTITY_CONTESTED` | conservative; event counts never inflate with reports; contested cases visible | none | identity resolution requires signature extraction per family; contested state must be representable |
| B | ADJUDICATED_IDENTITY — a (future) adjudication methodology may merge/split report clusters without occurrence-level signatures first | more complete at scale; introduces a versioned judgment layer | none | requires an adjudication methodology contract + adversarial evidence bar |
| C | HYBRID_DEFERRED — A at implementation; B researched in a later ratified round | A's safety now, B's power only after its own governance | none | A is the default posture; B is a later option |

**Planning posture:** none selected.

## D7N-2 — NARRATIVE IDENTITY METHODOLOGY *(carried)*

**Question:** what canonical rule decides "same narrative" (split/merge/relapse)?

| Option | Model | Consequence | Amendment | Implementation |
|---|---|---|---|---|
| A | OPERATOR_ADJUDICATED — identity operations are recorded operator/research decisions on evidence | maximally honest; scales poorly; fully auditable | none | adjudication queue + decision records; no auto-merge |
| B | RULE_ASSISTED_OPERATOR_CONFIRMED — deterministic candidate detection proposes; operator confirms | scalable with a human gate | none | detection-rule versioning + confirm step |
| C | FULLY_RULE_AUTOMATED — ratified rules merge/split automatically | scales; errors propagate to states/links; needs Book 6-grade evidence bars | none | highest validation burden |

**Planning posture:** none selected.

## D7N-3 — NARRATIVE/EVOLUTION STATE-RULE GOVERNANCE *(carried)*

**Question:** confirm the Book 7-specific state contract and decide vocabulary timing.

| Option | Model | Consequence | Amendment | Implementation |
|---|---|---|---|---|
| A | BOOK7_SPECIFIC_CONTRACT_NOW, VOCABULARY_LATER | governance settled; no names chosen blind | none | contract shape implementable; emissions blocked pending vocabulary round |
| B | CONTRACT + VOCABULARY TOGETHER | fewer rounds; heavier single decision; risk names outrun rule quality (Book 6 v0.1 failure) | none | one large decision surface |
| C | REUSE_BOOK6_CONTRACT | **REJECTED by planning analysis** (different evidence inputs, different failure modes, no authority transfer) | would require Book 6 amendment | — |

**Planning posture:** recommendation A; nothing ratified.

## D7N-4 — CAUSAL-CLAIM GOVERNANCE *(carried)*

**Question:** whether any causal-language (Level 4) methodology may ever be authorized for Book 7, and under what bar.

| Option | Model | Consequence | Amendment | Implementation |
|---|---|---|---|---|
| A | PERMANENT_LEVEL_3_CEILING — CSIA never asserts causality | maximally conservative | none | `causal_status` capped at ASSOCIATION_ONLY forever |
| B | DEFERRED_EVENT_STUDY_GATE — later, only via individually ratified event-study methodologies (identification, counterfactual, scope, reversibility) | preserves research headroom with a hard gate | none | Level 4 vocabulary exists but unreachable until ratification |
| C | TIMELINE_ADJACENCY_SUFFICES | **REJECTED by Constitution §25 / Axiom 3** (v0.1) | — | — |

**Planning posture:** none selected; `causal_status` keeps Level 4 unreachable
until closed. (The response-layer repair reinforces this: a response link is a
change record, never a cause claim.)

## D7N-5 — MARKET-RESPONSE SEAM REPRESENTATION *(carried)*

**Question:** bind the ref-only ceiling as Book 7's permanent boundary.

| Option | Model | Consequence | Amendment | Implementation |
|---|---|---|---|---|
| A | REF_ONLY_BINDING — `MARKET_RESPONSE_REF` is the only rung-6 representation Book 7 ever carries | permanent clean seam | none | rung 6 is a typed field; no semantics code |
| B | REF_NOW_SEMANTICS_LATER — lightweight market annotations after D8 closes | flexible; risks semantic creep into the reserved seam | none | requires Book 8 coordination |
| C | MARKET_RESPONSE_IN_BOOK7 | **REJECTED** (duplicates Sensor/Book 8 ownership, Constitution §4.2/§24) | would require Constitution/Book 8 amendment | — |

**Planning posture:** recommendation A; binding happens via operator decision.

## D7N-6 — HISTORICAL EVOLUTION REPLAY SEMANTICS *(carried)*

**Question:** bind the PRESERVED vs REVALIDATED distinction for Bloc 7D.

| Option | Model | Consequence | Amendment | Implementation |
|---|---|---|---|---|
| A | PRESERVED_ONLY_BINDING — replay machinery diffs only accepted preserved snapshots; unreconstructable = NOT_SUPPORTED | honest ceiling matching Book 2's NOT_IMPLEMENTED precedent | none | diff engine bounded to preserved snapshots |
| B | PRESERVED_PLUS_RECONSTRUCTION_METHODOLOGY — later, separately ratified reconstruction methodologies produce labeled reconstructed snapshots | more usable; each needs explicit uncertainty semantics | none | heavier validation surface |
| C | FULL_HISTORICAL_TRUTH_CLAIM | **REJECTED** (upstream books cannot supply it) | — | — |

**Planning posture:** recommendation A.

---

## 7. D7N-7 — CHANGE-COMPARISON AUTHORITY *(NEW — genuinely required)*

**Why this is a genuine structural decision (Phase 17 test), not doctrine-answerable:**

The response-semantics repair introduced a concept that did not exist in any
ratified contract: a **versioned comparison between a baseline and a later
observation** (baseline selection, comparability gates, change direction/value —
Reconciliation §2–§5). Auditing the frozen accepted books:

```text
Book 6 accepted contracts: MetricDefinition, MeasurementMethodology,
  MeasurementObservation, ValuationObservation, NormalizationRule, StateRule
Book 6 has NO comparison/change product and NO baseline contract.
Book 7 therefore cannot resolve the comparison by reference.
```

Constitution/Axiom doctrine does not answer it: Axiom 1 makes Book 6 the
measurement authority, but a comparison across two measurements is a *new*
contract class that no existing owner defines. Only the operator can assign its
ownership. (This is the same shape as the D6M-1 "measurement-object authority
boundary" decision that Book 6 faced and the operator answered.)

**Question:** who owns change-comparison semantics (baseline selection,
comparability gates, change direction/value, change methodology governance)?

| Option | Model | Consequence | Amendment impact | Implementation impact |
|---|---|---|---|---|
| A | BOOK6_OWNED_COMPARISON — add a `ComparisonRule`/`ChangeObservation` contract to Book 6; Book 7 references it | measurement/comparison authority stays in one place; consistent with Axiom 1 | **`BOOK_6_AMENDMENT_REQUIRED = TRUE`** (Book 6 is FROZEN_ACCEPTED at anchor `3919fb80…`; an amendment + re-acceptance round is required before use) | Book 6 re-opens (plan + implementation), then Book 7 consumes; slower, single owner |
| B | BOOK7_OWNED_LINKAGE_METHODOLOGY — Book 7 owns the comparison methodology over Book 6 *references* (never copying values); comparability gates cite Book 6 semantics | no upstream amendment; keeps Book 6 frozen | none | Book 7 owns one new methodology class; must not drift into a measurement engine; requires the seam recorded on every record (`BOOK7_LINKAGE_METHODOLOGY`) |
| C | DEFER_BOTH — no comparison product until a later round; responses stay `CHANGE_NOT_MEASURABLE` | most conservative; bloc 7C response rungs ship semantically but emit no change | none | fail-closed interim posture (the default planning stance until D7N-7 closes) |

**Interim posture until D7N-7 closes:** option C — fail-closed
(`CHANGE_NOT_MEASURABLE`). Planning selected no option.

## 8. Packet summary

```text
DECISIONS_SURFACED   = 7 (D7N-1..D7N-7)
CARRIED_FORWARD     = 6 (D7N-1..D7N-6, content unchanged)
NEW                 = 1 (D7N-7, with proof of genuineness)
DECIDED_HERE        = 0
REJECTED_BY_DOCTRINE = D7N-4/C, D7N-5/C, D7N-6/C, D7N-3/C (carried; for completeness only)
OPERATOR_SLOTS      = 7 (fillable in §0; unanswered = DEFER; no defaults)
INTERIM_POSTURES    = D7N-7 → C (fail-closed); all others → no-selection
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
