# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 1 — IDENTITY, ONTOLOGY, AND TEMPORAL KNOWLEDGE GRAPH
## Detailed Planning Book v0.3

**Document ID:** CSIA-B1-PLAN-001
**Version:** 0.3
**Status:** CONTRACT COMPLETE — READY_FOR_OPERATOR_RATIFICATION (planning only; implementation NOT authorized)
**Supersedes:** v0.2 (preserved), v0.1 (preserved)
**Depends on:** Constitution v0.2 — **RATIFIED** (`CSIA_CONSTITUTION_RATIFICATION_RECORD_v0.2.md`); Book 0 — **RATIFIED** (`CSIA_BOOK_0_RATIFICATION_RECORD_v0.1.md`); Operator Decision Log (D1–D6, R-1A-5=C)
**Companion:** stress matrix + ERRATA v0.1.1; extension adjudication v0.1
**Planning branch:** `agent/crypto-systems-intelligence-atlas-plan`
**Constitutional anchors (now canonical, no longer provisional):** §8 identity, §9 ontology, §10 relationships, §11 hypergraph, §12 temporal, §7 claim states

---

# CONTRACT CHANGELOG v0.1 → v0.2 → v0.3

## v0.1 → v0.2 (reconciliation — see v0.2 for detail)
C-1..C-8: E-1/E-5/E-8/E-10 required amendments adopted; E-2/E-12 slot reservations; E-7 clarification; new tests/cases. C-9: R-1A-5 held PENDING. C-10..C-12: terminology repairs, gating rules.

## v0.2 → v0.3 (ratification + R-1A-5 resolution — this version)

| # | Change | Trace | Bloc |
|---|---|---|---|
| C-13 | All `PENDING_OPERATOR_DECISION` markers for D1–D6 removed; constitutional anchors declared canonical per ratification record | D1–D6 | all |
| C-14 | R-1A-5 resolved = **Option C**: `RealizationIdentity` schema adopted as contract (was conditional preview in v0.2); deployment-status enum change (Option A's `CHANNEL_REPRESENTATIVE`) **not** adopted | R-1A-5=C, E-13 | 1A |
| C-15 | `REALIZATION` added to node-class registry (41 → **42** primary classes) with full definition; INV-1B-8 added to guard deployment/realization separation | R-1A-5=C | 1B |
| C-16 | `REALIZES` and `RECEIVED_VIA` edge dictionary entries adopted as contract (were conditional in v0.2); T-1C-14 un-conditioned | R-1A-5=C | 1C |
| C-17 | Realization lifecycle states defined: ACTIVE / CLOSED / MIGRATED / HISTORICAL / UNKNOWN — consistent with §8.1 lifecycle doctrine (no new vocabulary invented) | R-1A-5=C, operator doctrine | 1A/1D |
| C-18 | New invariants INV-1A-9..11 (realization non-identity, non-destruction, lineage) and INV-1C-7 (realization aggregation is derived-only) | operator doctrine items 1–8 | 1A/1C |
| C-19 | New adversarial case ADV-1A-O (two paths, one destination, distinct realizations) and ADV-1D-L (channel closure + migration lineage replay) | operator doctrine items 3–4 | 1A/1D |
| C-20 | Book-level gating block updated: D1–D6 recorded; R-1A-5 resolved; gates now depend only on bloc review outcomes + operator bloc ratification | D1–D6, R-1A-5 | all |
| C-21 | D7/D8 remain explicitly deferred (NOT removed) | operator session | book |
| C-22 | v0.2's conditional-block on the 42nd class lifted; registry final at 42 | R-1A-5=C | 1B |

No unrelated scope added. No Book 2 concepts. Minimum-sufficient ontology, native-architecture-first, bitemporal truth, provenance, hyperedge semantics, and no-EVM-bias requirements all preserved unchanged.

---

# 0. Book-level contract

## Purpose
Create the machine-readable language needed to describe crypto systems without flattening them: canonical identity, node ontology, relationship ontology (including hyperedges), and the bitemporal graph foundation.

## Scope
Blocs 1A (canonical identity), 1B (node ontology), 1C (relationship ontology), 1D (temporal graph). All four blocs are planning + schema-doctrine blocs; this document is their full contract.

## Non-goals (Book-level)
- No evidence acquisition (Book 2). No source registry, API collectors, adapters.
- No chain anatomy content (Book 3) — Book 1 defines only the classes and slots chains occupy.
- No capital-flow modeling (Book 5) — only capability-edge vocabulary.
- No replay machinery (Book 7D) — 1D defines temporal semantics and schema only.
- No implementation code.

## Book-level invariants
1. Every schema concept traces to a constitutional clause (now ratified).
2. No schema may contradict Constitution §8–§12; gaps require amendment first.
3. All schemas are planning specifications inside planning documents.
4. All seven operator decisions (D1–D6, R-1A-5) are resolved and incorporated; D7/D8 remain deferred and out of scope.

## Book exit gate
`PASS_CSIA_B1_TEMPORAL_GRAPH_FOUNDATION` — all four blocs pass their exit gates, cross-bloc consistency review passes, post-decision stress review passes, and the operator ratifies the book.

---

# BLOC 1A — CANONICAL IDENTITY

## 1A.1 Purpose
Identity as the immutable foundation: canonical, ticker-independent, temporally-stable identity for every object — including channel-bound realizations of assets.

## 1A.2 Scope
As v0.2, with the realization schema now contractual (C-14).

## 1A.3 Non-goals
As v0.2.

## 1A.4 Inputs
Constitution v0.2 (RATIFIED); operator decisions D1–D6 + R-1A-5=C (Decision Log); stress matrix + ERRATA; adjudication v0.1.

## 1A.5 Outputs
As v0.2, with realization doctrine among the ratified outputs.

## 1A.6 Schemas (planning specification)

### Canonical object identity
```text
ObjectIdentity {
  object_id:            "csia:<type>:<slug>"
  object_type:          primary class from Bloc 1B enumeration (42-class registry)
  role_tags:            [role, ...]
  canonical_name:       string
  aliases:              [ {name, valid_from, valid_to, name_state}, ... ]
  ticker_symbols:       [ {symbol, context, valid_from, valid_to,
                           collision_group|null}, ... ]
  chain_namespace:      chain object_id | null
  deployments:          [DeploymentIdentity, ...]      // issuance forms
  realizations:         [RealizationIdentity, ...]     // travel forms (contractual)
  entity_relationships: [edge_id, ...]
  lifecycle_state:      ACTIVE | DEPRECATED | HISTORICAL
  valid_from:           timestamp | UNKNOWN(bounded)
  valid_to:             timestamp | OPEN | UNKNOWN(bounded)
  claim_bindings:       [claim_evidence_id, ...]
}
```

### Deployment identity (issuance semantics — unchanged by R-1A-5)
```text
DeploymentIdentity {
  deployment_id:        "<object_id>@<chain_object_id>:<marker>"
  chain:                chain object_id
  marker:               CONTRACT(addr) | NATIVE | ISSUER_ACCOUNT(addr)
                      | PROGRAM(program_id) | MINT_ACCOUNT(mint)
                      | CANISTER(canister_id) | PACKAGE(pkg_id)
                      | OTHER(family, defining_string)
  standard / decimals / deploy_tx_ref:   as v0.2
  valid_from / valid_to:                 as v0.2
  status:               CANONICAL | BRIDGED_REPRESENTATIVE | WRAPPED | DEPRECATED
}
```

### Realization identity (CONTRACTUAL — R-1A-5 Option C) `[C-14, C-17]`
```text
RealizationIdentity {
  realization_id:            "<object_id>@<chain_object_id>:<realization_marker>"
  canonical_asset_id:        object_id            // the ONE economic asset
  chain_id:                  chain object_id      // destination chain
  local_asset_identifier:    denom | token id | contract-of-record string
                             (the chain-local name, e.g. ibc/<hash>)
  representation_mechanism:  IBC | CHAIN_KEY | LOCK_MINT | LIGHT_CLIENT
                           | OTHER(defining_string)
  route: {
    path:                    route identity (path id or derivation)
    channel_sequence:        [channel_id, ...] in hop order
    multi_hop_route:         [ (chain, channel, port), ... ] full hop list
  }
  valid_from:                timestamp | UNKNOWN(bounded)
  valid_to:                  timestamp | OPEN        // closure = world-change
  status:                    ACTIVE | CLOSED | MIGRATED | HISTORICAL | UNKNOWN
  migration_from:            realization_id | null   // lineage, non-destructive
  migration_to:              realization_id | null
  claim_bindings:            [claim_evidence_id, ...]   // provenance per realization
}
representation_mechanism enum: IBC | CHAIN_KEY | LOCK_MINT | LIGHT_CLIENT |
  OTHER(defining_string)
```

**Doctrine (operator-confirmed, normative):** a REALIZATION is a temporally versioned, chain-local manifestation of the SAME canonical economic asset. It is **not** a new economic asset, **not** an attribute blob, **not** automatically a protocol deployment.

### Merge/split event
Unchanged from v0.1/v0.2.

## 1A.7 Key semantic rules
Rules 1–11 from v0.1/v0.2 stand, plus:

12. **Realization ≠ asset (doctrine item 1):** a realization never becomes a `csia:token:*` object and never merges with the canonical asset.
13. **Multiple realizations per asset (item 2):** N realizations map to one canonical asset; the mapping is via `canonical_asset_id` + `REALIZES` edges.
14. **Path distinctness (item 3):** two distinct paths to the same destination remain distinct realizations where history or capital-routing analysis requires it (ADV-1A-O).
15. **Closure is non-destructive (item 4):** channel closure sets `status: CLOSED` + `valid_to`; the realization remains queryable forever (INV-1A-10).
16. **Migration is lineage (item 5):** migration creates `migration_from/migration_to` pointers and `MIGRATED_FROM/TO` edges; no destructive replacement (INV-1A-11).
17. **Aggregation is derived (item 6):** asset-level research rolls realizations up to the canonical asset as a **derived view** (INV-1C-7); realizations remain primary data (item 7: capital-flow research may inspect them separately; item 8: provenance is realization-specific via per-realization claim_bindings).

## 1A.8 Invariants
INV-1A-1..8 as v0.2, plus:

- INV-1A-9 (C-18): every realization references exactly one canonical asset; a realization may never serve as another realization's canonical asset (no chains of realizations — multi-hop is expressed in `route`, not nested realization-of-realization).
- INV-1A-10 (C-18): CLOSED/MIGRATED realizations remain queryable forever; no deletion (extends INV-1D-1 to realizations).
- INV-1A-11 (C-18): migration lineage is a linked chain (`migration_from`/`migration_to`); cycles are invalid; lineage history is never rewritten.

## 1A.9 Adversarial cases
ADV-1A-A..N as v0.2 (ADV-1A-N's "resolution mechanism PENDING" note is resolved: representable per the realization schema), plus:

- ADV-1A-O (C-19): USDC reaches Osmosis via two different IBC paths (direct from Ethereum-asset hub, and multi-hop via another chain) — two distinct realizations on the same destination chain, same canonical asset, distinct `local_asset_identifier` + `route`; both aggregate to `csia:token:usdc` in derived views only.

## 1A.10 Tests
T-1A-1..13 as v0.2, with:
- T-1A-13 un-conditioned (C-16): USDC across multiple IBC channels — multiple realizations coexist; channel closure closes one without touching others; multi-hop intermediate forms representable; aggregation to canonical is derived-only. **Now contractual.**

## 1A.11 Evidence artifacts
As v0.2; the R-1A-5 decision record now exists (Decision Log) — required evidence present.

## 1A.12 Operator review points
R-1A-1..R-1A-4 remain for bloc review. **R-1A-5: CLOSED** (Option C, recorded).

## 1A.13 Exit gate
```text
PASS_CSIA_B1A_IDENTITY_SEALED
Requires: identity doctrine (1A.6–1A.9, v0.3) reviewed at bloc review;
all 15 adversarial cases representable; invariants INV-1A-1..11 accepted;
R-1A-1..4 recorded. R-1A-5 is closed (Option C).
D1 gating: SATISFIED (Constitution ratified).
```

---

# BLOC 1B — NODE ONTOLOGY

## 1B.1–1B.5 Purpose/Scope/Non-goals/Inputs/Outputs
As v0.2, with R-1A-5=C incorporated (C-15).

## 1B.6 Schemas / registries (v0.3 changes only)

### Initial primary classes — final at **42**
The 41-class registry of v0.2 **plus**:

```text
REALIZATION
  definition: a temporally versioned, chain-local manifestation of one
  canonical economic asset, produced by a representation mechanism (IBC,
  chain-key, lock-and-mint, light-client) along an explicit route. NOT a
  new economic asset; NOT an attribute blob; NOT a protocol deployment.
  Identity: see 1A.6 RealizationIdentity. Lifecycle: ACTIVE | CLOSED |
  MIGRATED | HISTORICAL | UNKNOWN. Aggregation to the canonical asset is
  a derived view only.
  (Adopted via R-1A-5 = C; closes stress-matrix E-13.)
```

Role tags and family slots: unchanged from v0.2 (STATE_CHANNEL tag, finality_device slot, MEV clarification all stand).

### Unresolved class
Unchanged.

## 1B.7 Invariants
INV-1B-1..7 as v0.2, plus:

- INV-1B-8 (C-15): REALIZATION and DeploymentIdentity are distinct concepts; a deployment never doubles as a realization and vice versa. Deployments = issuance forms (how an asset comes to exist on a chain); realizations = travel forms (how an existing asset is represented elsewhere along a route).

## 1B.8–1B.9 Adversarial cases / Tests
As v0.2 (ADV-1B-A..K; T-1B-1..8). Class count references updated to 42.

## 1B.10–1B.12 Evidence / Review points / Exit gate
As v0.2; R-1B-1 ratifies the 42-class registry (final — no conditional count).

---

# BLOC 1C — RELATIONSHIP ONTOLOGY

## 1C.1–1C.5 Purpose/Scope/Non-goals/Inputs/Outputs
As v0.2, with realization edges now contractual (C-16).

## 1C.6 Edge dictionary (v0.3 changes only; all v0.1/v0.2 entries stand)

```text
REALIZES       (CONTRACTUAL — R-1A-5 Option C)
               def: a chain-local realization represents the canonical
               economic asset. dir: realization -> canonical asset.
               domain: REALIZATION. range: TOKEN | STABLECOIN | ASSET.
               inverse: REALIZED_BY. temporal: standing per realization
               validity (ACTIVE..CLOSED/MIGRATED).
               note: aggregation rollups (asset-level totals across
               realizations) are derived views, never stored edges.

RECEIVED_VIA   (CONTRACTUAL — R-1A-5 Option C)
               def: a realization arrived via the referenced channel/route.
               dir: realization -> route/channel identity. temporal:
               standing while the route holds; valid_to at channel closure.
               note: existing relationship names only — no new vocabulary
               was required for realization lineage; MIGRATED_FROM/TO
               (already in the dictionary) carry realization migration.
```

All other entries (SECURED_BY mechanism, RUNS_ON/VALIDATED_BY chain_scope, hyperedge route_attributes) unchanged from v0.2.

## 1C.7 Hyperedge rules — unchanged from v0.2 (route_attributes contractual; population Book 3B/4B).

## 1C.8 Invalid-relationship rules — IR-1..IR-12 as v0.2, plus:
- IR-13 (new): `REALIZES` edges must terminate at a canonical asset object; realization→realization REALIZES edges are invalid (INV-1A-9).

## 1C.9 Invariants — INV-1C-1..6 as v0.2, plus:
- INV-1C-7 (C-18): cross-realization aggregation (totals per asset) exists only as derived views; primary data stays at realization granularity (capital-flow analysis may always inspect realizations separately).

## 1C.10 Adversarial cases — ADV-1C-A..L as v0.2 (ADV-1C-K unchanged).

## 1C.11 Tests — T-1C-1..13 as v0.2; T-1C-14 un-conditioned (contractual).

## 1C.12 Review points — R-1C-1..5 as v0.2.

## 1C.13 Exit gate
```text
PASS_CSIA_B1C_RELATIONSHIP_ONTOLOGY_SEALED
As v0.2 with: dictionary final (REALIZES/RECEIVED_VIA contractual);
IR-13 test-mapped; INV-1C-7 accepted. No R-1A-5 dependency remains.
```

---

# BLOC 1D — TEMPORAL GRAPH

## 1D.1–1D.5 All as v0.2.

## 1D.6 Temporal schema rules — R1–R10 unchanged (they remain the contract that disqualified R-1A-5 Option B). All records — including realizations — carry the six timestamps; realizations are records, never attribute sets.

### Realization lifecycle semantics (C-17, new subsection)
```text
ACTIVE      valid_to = open; realization currently usable.
CLOSED      valid_to set (world change: channel/route closed, facility
            ended). Historical realization remains queryable forever.
MIGRATED    status marks lineage handoff; migration_from/migration_to
            link the chain; old realization CLOSED-or-MIGRATED, new one
            ACTIVE. No destruction.
HISTORICAL  pre-ratification or pre-discovery forms retained for replay.
UNKNOWN     mechanism/route known only partially; UNKNOWN(bounded) rules
            of R9 apply to any uncertain time fields.
```
Path/channel lifecycle (closure, migration) is expressed at record level — the exact property that rejected the attribute-only alternative.

## 1D.7–1D.9 Invariants / Adversarial cases / Tests
As v0.2, plus:

- ADV-1D-L (C-19): a channel closes and its asset later migrates to a new channel — old realization CLOSED→MIGRATED with lineage pointers, new realization ACTIVE; as-known(k) replay before the closure shows only the then-live realization; no history erased (exercises INV-1A-10/11 + RC-1/RC-2).
- T-1D-12 (new): realization lifecycle replay per ADV-1D-L.

## 1D.10–1D.12 Evidence / Review points / Exit gate
As v0.2, with T-1D-12 added to the test list.

---

# Book 1 consolidated dependency and gate map (v0.3)

```text
1A IDENTITY ──┐
              ├──> 1C RELATIONSHIPS ──> 1D TEMPORAL ──> PASS_CSIA_B1_...
1B NODE ONTOLOGY ──┘        │                  │
                            └── validated by ──┴──> PILOT STRESS MATRIX
                                                    + cross-bloc review
                                                    + post-decision stress

GATING (v0.3):
  D1–D6: RESOLVED (Constitution + Book 0 RATIFIED). No gating remains.
  R-1A-5: RESOLVED (= C). No gating remains.
  Remaining gates: bloc reviews R-1A-1..4, R-1B-1..4, R-1C-1..5, R-1D-1..4
  -> READY_FOR_OPERATOR_RATIFICATION -> operator bloc/book ratification.
  D7 (Book 5 gate) and D8 (Book 8 gate): DEFERRED, unaffected.
```

End of Book 1 detailed planning book v0.3.
