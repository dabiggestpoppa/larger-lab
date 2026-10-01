# CSIA — BOOK 7 ECOSYSTEM EVOLUTION v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Binding predecessors:** Boundary Review v0.1; Event Grammar v0.1.
> **Scope:** Bloc 7D planning — graph diffs, migration description, dependency
> gain/loss, expansion/contraction discipline, historical topology replay,
> event/narrative bitemporality. Book 7 describes evolution *between accepted
> states*; it never duplicates the graph.

---

## 1. Graph-change objects (Phase 25 — planned, not implemented)

```text
GraphDiff               the diff between two ACCEPTED canonical states (two
                        Book 1/3/4/5 accepted snapshots or revisions), with
                        left/right state refs and derivation method ref
NodeChange              one object's appearance/disappearance/role/identity change
EdgeChange              one dependency/relation's formation/removal/modification
DependencyChange        EdgeChange restricted to Book 4 dependency semantics
MigrationChange         identity-bearing move described via Book 3 lineage
TopologySnapshotDiff    aggregate diff over a cohort/scope at two valid times
```

Invariants: every diff cites its two source states (both accepted — never
working state); every change row cites the owning-book record that justifies
it (AB-1 mirror: the diff is a *reading* of Books 1–5 state, not a parallel
graph); diffs are reproducible (same inputs + method ref ⇒ same diff).

## 2. Diff semantics (Phase 26 — change is not judgment)

```text
NODE_ADDED      NODE_REMOVED     EDGE_ADDED      EDGE_REMOVED
EDGE_CHANGED    ROLE_CHANGED     MIGRATED        DEPENDENCY_GAINED
DEPENDENCY_LOST
```

Doctrines:

- **Graph change != good/bad.** A security dependency added may increase
  fragility; a deprecated-bridge removal may reduce risk. No valence is
  attached to any diff row; no "ecosystem health" is derivable from diff
  counts (anti-score firewall applies to evolution surfaces verbatim).
- **Every new edge is not growth:** `EDGE_ADDED` rows carry typed relation
  basis and strength descriptor *as recorded by Book 4* — a re-categorization,
  a quarantine-escape, or a dedup artifact must not masquerade as ecosystem
  expansion.
- **ROLE_CHANGED / MIGRATED** are identity-bearing rows — they resolve through
  Book 3 identity doctrine (§3 below), never through diff heuristics.

## 3. Migrations (Phase 27 — Book 3 continuity consumed)

Required law: `MIGRATION EVENT != NEW OBJECT AUTOMATICALLY`. Whether a
migration created a new identity, preserved one, or forked is decided **only**
by Book 3 doctrine (D3-1 branch-sensitive identity, D3-2 new-genesis, D3-7
state-migration continuity) and its accepted records.

Book 7 tracks (descriptively, referencing Book 3 lineage):

```text
origin / destination         Book 3 MIGRATED_FROM / MIGRATED_TO refs
continuity                   the Book 3 identity outcome (SAME_OBJECT continuation,
                             NEW_OBJECT, FORKED_FROM, UNKNOWN — as Book 3 resolved it)
partial migration            both endpoints still carrying live records
dual-running period          valid-time window where source and destination
                             both operate (temporal fields per Event Grammar §6)
rollback                     a REVERSED occurrence + the Book 3/4 records showing it
completion                   destination-authoritative state reached (per owning books)
```

No Book 7 identity invention: where Book 3 has not resolved identity, the
migration row's continuity is `UNKNOWN` — preserved, never guessed.

## 4. Dependency gain / loss (Phase 28 — Book 4 consumed)

Book 7 may describe: dependency appeared, dependency disappeared, provider
changed, failure domain changed, substitutability changed — each row
referencing the Book 4 DependencyRecord/revision that establishes it.

Book 7 may not: mint a Book 4 dependency fact, promote an announced
integration to an edge, or re-weight/strength-describe beyond what Book 4
records. Where an event (e.g., INTEGRATION announcement) lacks a resolvable
Book 4 record, the row is `CHANGE_CLAIMED` (Event Grammar §7) and feeds
contradiction/absence semantics, not the diff.

## 5. Ecosystem expansion / contraction (Phase 29 — dimension-specific only)

The English words are **hidden judgments unless dimension-bound**. "Expanding"
without a dimension is a private score. Planned doctrine:

- Evolution states are **dimension-specific**, each with its own derivation
  rule (unratified in planning): e.g., object-count evolution, integration-count
  evolution, economic-function coverage evolution, capital-route evolution,
  active-deployment evolution — each keyed to the owning book's records.
- **Generic EXPANSION / CONTRACTION is rejected** as an unqualified scalar
  (mirrors Book 6's rejection of generic EXPANDING/CONTRACTING; D6M-3 Class C
  discipline applies by analogy — threshold-style judgment is deferred and
  needs individual ratification).
- **No universal ecosystem-size scalar:** no single number may represent
  "ecosystem size" (that is a composite score by another name — §5.3a).
- Any dimension-specific state must remain descriptive, replayable,
  evidence-linked, versioned, non-prescriptive (Narrative State Governance §2
  rules apply to evolution states identically).

## 6. Historical topology replay (Phase 30 — honest capability audit)

Book 6 already established the pattern: Book 2 historical authority replay is
NOT_IMPLEMENTED; preserved record != revalidated authority. Book 7 inherits the
audit obligation for Books 1–4:

```text
PRESERVED_GRAPH_HISTORY        what accepted snapshots/records actually retain
                               (Book 1 bitemporal model, Book 3 dossier history,
                               Book 4 dependency valid-time records, Book 5
                               versioned snapshots per D5CAP-3)
REVALIDATED_HISTORICAL_TOPOLOGY  reconstructing "the accepted graph as it stood
                               at time T, re-verified against evidence"
```

Planned honest findings (to be verified at implementation time, not assumed):

- What can be reconstructed at time T = only what accepted records preserved
  with valid-time spans; snapshots are diffable where preserved.
- What is preserved as event history = Book 7's own occurrence records going
  forward.
- What is only current-state authoritative = records without retained history;
  for those, time-T reconstruction is NOT_SUPPORTED (not zero, not silently
  current-values-backfilled — Axiom 6).
- Replay machinery (Bloc 7D obligation, `[→MA-13]`) generates diffs only
  between states that exist; it never fabricates intermediate topology.
- The distinction above is surfaced for binding confirmation as candidate
  decision `D7N-6`.

## 7. Event / narrative bitemporality (Phase 31)

Every consequential Book 7 object (EventOccurrence, NarrativePropagation,
NarrativeActionLink, GraphDiff) carries the Book 1 bitemporal axes plus
source time where relevant:

```text
valid time        when the thing held in the world (occurrence window,
                  propagation epoch, link validity)
observation time  when CSIA learned/recorded it
source time       when the source emitted it (source_published_at)
revision time     supersession chain (records replaced, world-change via valid_to)
```

Narrative knowledge arrives after events; late discovery enters the
transaction-time axis late (§12.2 late-discovery rule). **History is never
rewritten** to make later evidence appear contemporaneous; corrections
supersede records, they do not overwrite them.

## 8. Verdict

```text
GRAPH_DIFF_OBJECTS      = PLANNED (6 concepts; accepted-states-only inputs)
DIFF_SEMANTICS          = PLANNED (9 row types; no valence; no growth-by-edge-count)
MIGRATION_DOCTRINE      = PLANNED (Book 3 identity consumed; no invention)
DEPENDENCY_SEAM         = PLANNED (Book 4 records referenced, never minted)
EXPANSION_CONTRACTION   = REJECTED AS GENERIC SCALAR (dimension-specific states only)
HISTORICAL_REPLAY       = PRESERVED != REVALIDATED doctrine drafted; D7N-6 open
BITEMPORALITY           = PLANNED (4 time axes; late-discovery; no rewrite)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
