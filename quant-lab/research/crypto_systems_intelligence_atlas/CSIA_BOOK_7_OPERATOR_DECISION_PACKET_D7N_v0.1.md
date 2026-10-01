# CSIA — BOOK 7 OPERATOR DECISION PACKET — D7N v0.1

> **Status:** DECISION PACKET — DRAFT. Surfaces operator decisions; decides
> none. **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE
> REVIEW ONLY. `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Namespace check (Phase 43):** `D7N` searched against
> `CSIA_OPERATOR_DECISION_LOG.md`, `CSIA_CONSTITUTION_v0.2.md`, and the
> roadmap — **0 collisions**. Distinguished from the historical `D7` (Capital
> Field = Book 5 Bloc 5G, RATIFIED/CLOSED — a different, already-closed
> decision), from `D6M-*` (Book 6), and from any Book 0 D7 usage. The `N`
> disambiguator ("Book 7 Narrative/Events") is deliberate.
> **Discipline:** only genuine structural choices are surfaced. Where doctrine
> already answers a question (e.g., "may E4 mint structural truth?" — no, by
> §20.1; "may report count become event count?" — no, by identity doctrine),
> no decision is created; the doctrine binds.

---

## D7N-1 — EVENT IDENTITY AUTHORITY

**Question:** who/what resolves whether two reports describe the same
occurrence, and by what doctrine?

| Option | Model | Consequence |
|---|---|---|
| A | **OCCURRENCE_EVIDENCE_FIRST** — identity binds on family-defined occurrence signatures (tx ids, proposal ids, incident ids); reports attach to resolved events; unresolved groups stay `IDENTITY_CONTESTED` | conservative; event counts never inflated by reports; contested cases stay visible; adjudication is evidence-driven |
| B | **ADJUDICATED_IDENTITY** — a (future) adjudication methodology may merge/split report clusters without occurrence-level signatures first | more complete at scale; introduces a judgment layer that must be versioned and adversarially reviewed; risk of clustering errors becoming identity |
| C | **HYBRID_DEFERRED** — A at implementation; B researched as a separately ratified methodology later | A's safety now; B's power only after its own governance round |

**Planning posture:** none selected. Candidate implications bind only at
implementation authorization. A false identity decision here cannot be undone
silently later (identity is permanent in CSIA).

## D7N-2 — NARRATIVE IDENTITY METHODOLOGY

**Question:** what canonical rule decides "same narrative" (split/merge/relapse)?

| Option | Model | Consequence |
|---|---|---|
| A | **OPERATOR_ADJUDICATED** — identity operations are recorded operator/research decisions on evidence, no automated merging | maximally honest; scales poorly; every split/merge is auditable |
| B | **RULE_ASSISTED_OPERATOR_CONFIRMED** — deterministic candidate detection (canonicalized claim-structure similarity under a versioned rule) proposes; operator confirms | scalable with a human gate; detection-rule versioning required |
| C | **FULLY_RULE_AUTOMATED** — ratified rules merge/split automatically | scales; but narrative identity errors would propagate to states/links — highest risk; would need Book 6-grade adversarial evidence bars |

**Planning posture:** none selected; Narrative Model §1.1 doctrine is written
to be compatible with A or B.

## D7N-3 — NARRATIVE/EVOLUTION STATE-RULE GOVERNANCE + VOCABULARY TIMING

**Question:** confirm the Book 7-specific state contract (not Book 6 code/authority)
and decide when the Class B state vocabulary is selected.

| Option | Model | Consequence |
|---|---|---|
| A | **BOOK7_SPECIFIC_CONTRACT_NOW, VOCABULARY_LATER** — ratify the contract shape (operator-only ratification; three classes; emission binding) this round; select state names in a dedicated later round with rule drafts | governance settled; no names chosen blind; implementation blocked on vocabulary round |
| B | **CONTRACT + VOCABULARY TOGETHER** — one round picks contract and names with full rule drafts | fewer rounds; heavier single decision; risk of names outrunning rule quality (the exact Book 6 v0.1 failure) |
| C | **REUSE_BOOK6_CONTRACT** | REJECTED by planning analysis (different evidence inputs, different failure modes, no authority transfer — see Narrative State Governance §3); listed for completeness |

**Planning posture:** recommendation recorded = A; nothing ratified; zero
state rules ratified at planning close.

## D7N-4 — CAUSAL-CLAIM GOVERNANCE

**Question:** whether any causal-language (Level 4) methodology may ever be
authorized for Book 7, and under what bar.

| Option | Model | Consequence |
|---|---|---|
| A | **PERMANENT_LEVEL_3_CEILING** — CSIA never asserts causality; causal language stays quoted-source or descriptive-level only | maximally conservative; event-study outputs would live outside CSIA state |
| B | **DEFERRED_EVENT_STUDY_GATE** — causal claims permitted later only via individually ratified event-study methodologies (identification strategy, counterfactual basis, scope, reversibility — D6M-5 emergence conditions by analogy) | preserves research headroom with a hard gate; Level 4 vocabulary exists but stays unreachable until then |
| C | **TIMELINE_ADJACENCY_SUFFICES** | REJECTED — contradicts Constitution §25 and Axiom 3; listed for completeness only |

**Planning posture:** none selected; `causal_status` vocabulary keeps Level 4
unreachable until this closes.

## D7N-5 — MARKET-RESPONSE SEAM REPRESENTATION

**Question:** bind the ref-only ceiling as Book 7's permanent boundary.

| Option | Model | Consequence |
|---|---|---|
| A | **REF_ONLY_BINDING** — `MARKET_RESPONSE_REF` is the only rung-6 representation Book 7 will ever carry; all market semantics belong to Sensor/Book 8 | permanent clean seam; ladder completeness honestly stops at rung 5+ref |
| B | **REF_NOW_SEMANTICS_LATER** — Book 7 may grow lightweight market annotations after D8 closes | flexible; risks semantic creep into the reserved seam; requires Book 8 coordination regardless |
| C | **MARKET_RESPONSE_IN_BOOK7** | REJECTED — duplicates Sensor/Book 8 ownership (Constitution §4.2, §24); listed for completeness |

**Planning posture:** recommendation recorded = A; binding happens via
operator decision, not by this packet.

## D7N-6 — HISTORICAL EVOLUTION REPLAY SEMANTICS

**Question:** bind the PRESERVED vs REVALIDATED distinction for Bloc 7D.

| Option | Model | Consequence |
|---|---|---|
| A | **PRESERVED_ONLY_BINDING** — replay machinery diffs only accepted preserved snapshots; time-T reconstruction limited to preserved valid-time records; unreconstructable = NOT_SUPPORTED (never backfilled) | honest ceiling matching Book 2's `HISTORICAL_BOOK2_AUTHORITY_REPLAY = NOT_IMPLEMENTED` precedent |
| B | **PRESERVED_PLUS_RECONSTRUCTION_METHODOLOGY** — allow separately ratified reconstruction methodologies to produce labeled reconstructed snapshots (never presented as accepted state) | more usable for research; each methodology must carry explicit uncertainty semantics and adversarial review |
| C | **FULL_HISTORICAL_TRUTH_CLAIM** | REJECTED — upstream books cannot supply it (Book 2 replay NOT_IMPLEMENTED; not all Books 1–5 records retain full history); listed for completeness |

**Planning posture:** recommendation recorded = A; candidate B is a future
research round, not a planning assumption.

---

## Packet summary

```text
DECISIONS_SURFACED          = 6 (D7N-1..D7N-6)
DECIDED_HERE                = 0
NAMESPACE                   = D7N (collision-free, verified against decision log,
                              constitution, roadmap; distinct from closed D7)
REJECTED_BY_DOCTRINE        = D7N-4/C, D7N-5/C, D7N-6/C (listed for completeness only)
PLANNING_RECOMMENDATIONS    = D7N-3/A, D7N-5/A, D7N-6/A (recommendations only —
                              the operator decides; no default was applied)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
