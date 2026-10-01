# CSIA — BOOK 7 BOUNDARY REVIEW v0.1

> **Status:** PLANNING DOCUMENT — GOVERNANCE REVIEW. Not ratified.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> **Grants no implementation authority.** `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Predecessor state:** Book 6 `FROZEN_ACCEPTED` at accepted implementation anchor
> `3919fb8052e216e94034a753fb258d338c5fa0dc`, acceptance commit
> `5f94c3f40cea4441470c57671f51454da7377361`, exit gate
> `PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL`.
> **Scope:** ownership boundaries only. No event grammar, no contracts, no
> implementation (companion docs follow).

---

## 1. Why this document exists

Book 7 is the first book whose canonical inputs are *speech about the system*
(news, announcements, roadmaps, governance discourse, social propagation) rather
than the system itself. That is the classic capture point: narrative invites the
silent promotion of "people said X" into "X is true." Axiom 3 — EVIDENCE
OUTRANKS NARRATIVE — and the §20–21 firewall exist to prevent it. This review
fixes ownership **before** event ontologies, narrative grammars, or any grammar
companion is drafted, so the Book 7 model has somewhere safe to land.

## 2. Canonical ownership map (resolved with every neighbor)

| Owner | Canonical authority (sole) | Book 7 posture |
|---|---|---|
| **BOOK 1** | identity, ontology, temporal graph, deployment identity, bitemporal truth | consumed by reference (object IDs, bitemporal axes); never re-modeled |
| **BOOK 2** | evidence, claims, promotion, contradiction — the **only epistemic engine** | every truth-bearing product of Book 7 resolves to Book 2 authority; narrative evidence is E4 class only |
| **BOOK 3** | native architecture truth, network identity, migration/continuity | migration event references Book 3 `MIGRATED_FROM`/`MIGRATED_TO` lineage; Book 7 never mints identity |
| **BOOK 4** | dependency graph truth, failure domains, substitutability, hard runtime | dependency gain/loss events reference Book 4 records; Book 7 never mints a dependency fact |
| **BOOK 5** | economic records, capital topology, principal vectors, liabilities | capital response references Book 5/6 records; never rewritten |
| **BOOK 6** | measurement definitions, methodologies, descriptive measured state | usage/capital responses consume `MeasurementObservation` / `FundamentalStateVector` refs; never recomputed, no thresholds |
| **BOOK 7** | **events, occurrence history, narrative objects, action linkage, ecosystem-evolution description (this book)** | — |
| **BOOK 8** | structural ↔ market Context Bridge | receives only a forward seam (market response as a **reference**; see §4 below) |
| **SENSOR** | mechanical market observation, market-state mechanics | untouched; no market semantics defined in Book 7 |

## 3. The master separation Book 7 must preserve

```text
Axiom 3:      EVIDENCE OUTRANKS NARRATIVE
D2-6:         ANNOUNCED != DEPLOYED != USED          (parameters deferred, D6M-5)
§20/20.1:     narrative corroboration (E4, at any scale) may raise a NARRATIVE's
              state but never a STRUCTURAL claim's state
§21:          the narrative-to-action ladder is constitutional
§5.3a:        descriptive only; no ranking/score/target/prescriptive language
§25:          sequence does not prove causality
```

Narrative may establish: that a narrative exists; what it claims; who propagates
it; what objects it references. It does **NOT** establish that the claimed
system change is true. Truth of the world stays owned by the book that owns the
world-domain: Book 2 authority, applied through the owning structural book.

## 4. Required separations, owner by owner

- **Book 2:** Book 7 introduces no claim state, no promotion rule, no second
  epistemic engine. Narrative existence (`NARRATIVE EXISTS`) is a Book 7-record /
  E4-class fact. Narrative-internal claims of fact (`"the upgrade is live"`)
  are **claims**, routed to Book 2 evidence classes like any other claim;
  they carry no authority because they circulated.
- **Book 3 (identity/migration):** a migration event does not create or resolve
  identity. `MIGRATED_FROM / MIGRATED_TO`, fork identity (D3-1), new-genesis
  (D3-2), state-migration continuity (D3-7) remain Book 3 doctrine. Book 7
  records that the world reported/brought about a migration and **cites** the
  Book 3 identity outcome.
- **Book 4 (dependencies):** "dependency appeared/disappeared/provider changed"
  events describe the graph; the graph itself is Book 4's. An event record
  without a resolvable Book 4 dependency record may only state
  `CHANGE_CLAIMED`, never `CHANGED`.
- **Book 5 (capital):** capital-response rungs reference canonical Book 5
  economic records and Book 6 measurements. Book 7 owns none, recomputes none,
  and never writes principal-liability topology back.
- **Book 6 (measurement/state):** `USAGE RESPONSE` rungs are Book 6
  MeasurementObservation refs + a timeline relation. Book 7 may not recompute a
  measurement, invent a usage threshold, invent a health state, or override
  missingness. `USAGE RESPONSE OBSERVED != USAGE HEALTH` (D6M-5 untouched).
- **Book 8:** during Book 7, market response exists **only** as
  `MARKET_RESPONSE_REF` — a forward seam. No market-regime semantics, no
  combined CSIA+Sensor confirmation states, no market lag windows, no D8
  decision. Book 8 will own identity mapping to Sensor, temporal/lag alignment,
  combined context states, and bridge validation.
- **Sensor:** no market mechanics are defined, measured, or interpreted here.

## 5. Anti-bleed rules (mechanically checkable at implementation time)

```text
AB-1  NO STRUCTURAL WRITE:  Book 7 artifacts may not create/modify any Book 1-5
      canonical fact or Book 6 measurement; they may only HOLD REFERENCES to them.
AB-2  NO NARRATIVE PROMOTION: no path exists by which E4 narrative evidence
      raises a structural claim's state (§20.1), duplicates Book 2 ClaimState,
      or creates a parallel claim lifecycle.
AB-3  NO COUNT-TO-TRUTH: report count, propagation count, and duration of
      circulation are descriptive propagation attributes; no rule may convert
      them into occurrence truth, event importance, or narrative quality
      without a separately ratified derivation rule.
```

## 6. What Book 7 owns (precise statement)

- **Event ontology:** what an event is, how many events a set of reports
  comprises, event identity, families, lifecycle, temporal windows.
- **Occurrence history:** what happened, when, verified against evidence-class
  gates — always as a **consumer** of Book 2 evidence.
- **Narrative objects:** identity, origin, propagation, contradiction, states
  (rule-gated; none ratified in planning).
- **Action linkage:** the declared/deployed/usage/capital response linking
  between narratives, claims, actions, and measured responses — as
  observations, never as causation.
- **Ecosystem evolution description:** graph diffs between accepted states,
  migration narratives, dependency gain/loss narratives, dimension-specific
  evolution states, historical-topology limitation accounting.
- **Replay machinery for temporal history** (Constitution §12.2 `[→MA-13]`):
  the Book 7 Bloc 7D obligation to generate diffs between preserved accepted
  snapshots — respecting, not expanding, upstream historical capability.

## 7. Interactions this review does NOT settle

- The exact event identity doctrine (occurrence-evidence-first vs adjudication)
  → surfaced as candidate operator decision `D7N-1`.
- Narrative identity methodology (when two phrasings are one narrative)
  → candidate `D7N-2`.
- Whether Book 7 narrative-state rules adopt the Book 6 governance pattern or a
  Book 7-specific contract → candidate `D7N-3`.
- Causal-language governance for event-study outputs → candidate `D7N-4`.
- Binding confirmation of the ref-only market-response ceiling → candidate
  `D7N-5` (until D8, no market semantics anywhere).
- Binding confirmation of preserved-vs-revalidated historical topology
  semantics → candidate `D7N-6`.

None of the above is decided in this review; all remain OPEN for the operator.

## 8. Book amendment audit

| Book | Amendment required? |
|---|---|
| BOOK 1 | **NO** — bitemporal axes and replay-machinery assignment already exist (§12.2 `[→MA-13]`: "replay machinery ownership is Book 7 Bloc 7D") |
| BOOK 2 | **NO** — evidence classes including E4 already defined; D2-6 in force |
| BOOK 3 | **NO** — migration/identity doctrine consumed as-is |
| BOOK 4 | **NO** — dependency record contracts consumed as-is |
| BOOK 5 | **NO** — D7 closed; capital topology consumed as-is |
| BOOK 6 | **NO** — measurement/state contracts consumed as-is; D6M* in force |
| Constitution | **NO** — Axiom 3, §5.3a, §20–21, §25 already ratified |

## 9. Boundary verdict

```text
BOOK_7_BOUNDARY_REVIEW      = COMPLETE
BOOK_2_AMENDMENT_REQUIRED   = FALSE   (and Books 1,3,4,5,6 + Constitution = FALSE)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY  = FALSE
```

Boundary capture blocked at the door: Book 7 is a *teller*, not a *maker* of
truth. Every subsequent Book 7 planning artifact is bound by AB-1..AB-3.
