# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 1 — IDENTITY, ONTOLOGY, AND TEMPORAL KNOWLEDGE GRAPH
## Detailed Planning Book v0.2

**Document ID:** CSIA-B1-PLAN-001
**Version:** 0.2
**Status:** PLANNED — FROZEN_FOR_REVIEW (planning only; no implementation authorized; NOT ratified)
**Supersedes:** `CSIA_BOOK_1_IDENTITY_ONTOLOGY_TEMPORAL_GRAPH_PLAN_v0.1.md` (preserved unmodified)
**Depends on:** `CSIA_CONSTITUTION_v0.2.md` (NOT yet ratified — pending D1), `CSIA_BOOK_0_RATIFICATION_PACKET.md`, `CSIA_BOOK_1_EXTENSION_ADJUDICATION_v0.1.md`
**Companion:** `CSIA_BOOK_1_PILOT_ONTOLOGY_STRESS_MATRIX.md` (incl. ERRATA v0.1.1)
**Planning branch:** `agent/crypto-systems-intelligence-atlas-plan`
**Constitutional anchors:** §8 (identity), §9 (ontology), §10 (relationships), §11 (hypergraph), §12 (temporal), §7 (claim states) — *all anchors provisional until D1 ratifies v0.2*

---

# CONTRACT CHANGELOG v0.1 → v0.2

Scope discipline: v0.2 incorporates **only** adjudicated required generic amendments (E-1, E-5, E-8, E-10), zero-cost slot reservations (E-2, E-12), clarifications (E-7, E-6 test addition), and terminology/correctness repairs. Everything dependent on D1–D6 or R-1A-5 is marked `PENDING_OPERATOR_DECISION` and was **not** silently chosen.

| # | Change | Trace | Bloc |
|---|---|---|---|
| C-1 | `SECURED_BY`/`SECURES` edge dictionary entries gain mandatory `mechanism` attribute (enum + OTHER(defining)) | E-1 (adj. REQUIRED) | 1C |
| C-2 | DeploymentIdentity `address` field → typed `marker` enum: CONTRACT / NATIVE / ISSUER_ACCOUNT / PROGRAM / MINT_ACCOUNT / CANISTER / PACKAGE / OTHER(family) | E-5 (adj. REQUIRED) | 1A |
| C-3 | Hyperedge registry gains generic `route_attributes` group `{route_spec, state, version, mechanism}` typed per mechanism family; population deferred to Book 3B/4B | E-8 (adj. REQUIRED; E-11 subsumed) | 1C |
| C-4 | `RUNS_ON` (and `VALIDATED_BY`) gain `chain_scope` attribute: CHAIN / SUBNET / SHARD / PARTITION with sub-object references | E-10 (adj. REQUIRED) | 1C (+1B slot note) |
| C-5 | Role-tag registry adds `STATE_CHANNEL` | E-2 (adj. deferable, adopted as reservation) | 1B |
| C-6 | Extension-slot registry adds `finality_device` slot (population → Book 3B); ADV-1D-J note references it | E-12 (adj. deferable, slot reserved) | 1B + 1D |
| C-7 | `MEV_INFRASTRUCTURE` definition string clarified: family manifestations live in family slots, never as tag parameters | E-7 (adj. already-covered) | 1B |
| C-8 | New adversarial tests: T-1A-11 (trustline issuance), T-1A-12 (marker round-trip), T-1C-11 (mechanism attr), T-1C-12 (multi-channel hyperedges), T-1C-13 (subnet scope), T-1B-7 (state-channel tag), T-1D-11 (finality anchoring) | Adjudication tests column | 1A/1B/1C/1D |
| C-9 | R-1A-5 (IBC voucher representation): **PENDING_OPERATOR_DECISION** — Bloc 1A freeze blocked on it; Option C recommended, A acceptable, B rejected (violates Bloc 1D record rules) | E-13 | 1A/1B/1C |
| C-10 | Terminology repair: "zero structural failures" claims replaced by five-category verdict language; Book 1 v0.1's dependency-on-ratification assumption made explicit (constitution anchors provisional until D1) | Session-2 reconciliation | all |
| C-11 | INV-1A-2 wording repaired: the invariant said "no two ACTIVE objects share (object_type, slug)" — clarified that marker/namespace collisions within a type route through disambiguation + Decision Log (consistent with §8.2) | correctness | 1A |
| C-12 | Bloc 1A evidence list adds stress-matrix ERRATA v0.1.1 and adjudication doc as required evidence; all blocs add `PENDING_OPERATOR_DECISION` gates to their exit criteria | reconciliation | all |

---

# 0. Book-level contract

## Purpose
Create the machine-readable language needed to describe crypto systems without flattening them: canonical identity, node ontology, relationship ontology (including hyperedges), and the bitemporal graph foundation.

## Scope
Blocs 1A (canonical identity), 1B (node ontology), 1C (relationship ontology), 1D (temporal graph). All four blocs are **planning + schema-doctrine blocs**; this document is their full contract.

## Non-goals (Book-level)
- No evidence acquisition (Book 2).
- No source registry, no API collectors, no adapters.
- No chain anatomy content (Book 3) — Book 1 defines only the *classes and slots* chains occupy.
- No capital-flow modeling (Book 5) — only capability-edge vocabulary.
- No replay machinery (Book 7D) — 1D defines temporal semantics and schema only. `[→MA-13]`
- No implementation code in this planning phase.

## Book-level invariants
1. Every schema concept in this book traces to a constitutional clause.
2. No schema invented here may contradict Constitution §8–§12; any gap requires a constitutional amendment first.
3. All schemas in this document are **planning specifications inside a planning document** — no schema files are created outside planning docs.
4. **Ratification gating (new in v0.2):** this contract's constitutional anchors are provisional until D1 ratifies Constitution v0.2; no bloc may freeze before its dependencies (including R-1A-5 for Bloc 1A) are decided.

## Book exit gate
`PASS_CSIA_B1_TEMPORAL_GRAPH_FOUNDATION` — achieved when Blocs 1A–1D each pass their own exit gates, the pilot stress matrix validates the ontology (with its five-category verdict qualification), and all `PENDING_OPERATOR_DECISION` items affecting each bloc are resolved.

---

# BLOC 1A — CANONICAL IDENTITY

## 1A.1 Purpose
Establish identity as the immutable foundation of the graph: every object gets one canonical, ticker-independent, temporally-stable identity, with explicit handling of ticker collisions, rebrands, forks, migrations, contract deployments, multi-chain presence, and channel-bound representations.

## 1A.2 Scope
- Object ID scheme and minting rules (Constitution §8.2).
- Namespace design (object types as namespaces; chain namespaces for deployments).
- Token vs protocol vs chain vs entity separation.
- Ticker collision resolution.
- Alias and rebrand doctrine.
- Fork identity.
- Migration identity.
- Deployment identity with typed marker enum (C-2).
- Multi-chain deployment mapping.
- Channel-bound representation identity — **PENDING_OPERATOR_DECISION R-1A-5 (C-9)**.
- Identity lifecycle states (ACTIVE / DEPRECATED / HISTORICAL).
- Merge and split operations.

## 1A.3 Non-goals
- Identity verification evidence (Book 2 proves claims about identity; 1A defines identity structure).
- Human-readable display/rendering decisions (Book 9).
- Wallet address identity (user addresses are not CSIA graph objects).

## 1A.4 Inputs
- Constitution §8 (v0.2 — provisional until D1).
- Roadmap Bloc 1A chapters 1A.1–1A.5.
- Pilot stress matrix + ERRATA v0.1.1; extension adjudication (E-5, E-13).
- Operator decisions D1–D6, R-1A-5.

## 1A.5 Outputs
- Identity doctrine sections (this doc 1A.6–1A.9).
- Identity field schemas (planning-level).
- Adversarial case catalog (1A.10).
- Test plan (1A.11).
- Evidence artifact list (1A.12).

## 1A.6 Schemas (planning specification)

### Canonical object identity
```text
ObjectIdentity {
  object_id:            "csia:<type>:<slug>"        // immutable, minted once
  object_type:          primary class from Bloc 1B enumeration
  role_tags:            [role, ...]                  // from Bloc 1B role registry
  canonical_name:       string
  aliases:              [ {name, valid_from, valid_to, name_state}, ... ]
  ticker_symbols:       [ {symbol, context, valid_from, valid_to,
                           collision_group|null}, ... ]
  chain_namespace:      chain object_id | null
  deployments:          [DeploymentIdentity, ...]
  realizations:         [RealizationIdentity, ...]   // PENDING R-1A-5 Option C;
                                                     // omitted if Option A chosen
  entity_relationships: [edge_id, ...]
  lifecycle_state:      ACTIVE | DEPRECATED | HISTORICAL
  valid_from:           timestamp | UNKNOWN(bounded)
  valid_to:             timestamp | OPEN | UNKNOWN(bounded)
  claim_bindings:       [claim_evidence_id, ...]
}
```

### Deployment identity (v0.2 — marker enum per C-2/E-5)
```text
DeploymentIdentity {
  deployment_id:        "<object_id>@<chain_object_id>:<marker>"
  chain:                chain object_id (never a chain *name*)
  marker:               CONTRACT(addr) | NATIVE | ISSUER_ACCOUNT(addr)
                      | PROGRAM(program_id) | MINT_ACCOUNT(mint)
                      | CANISTER(canister_id) | PACKAGE(pkg_id)
                      | OTHER(family, defining_string)   // Book 3B families extend
  standard:             standard object_id | null
  decimals:             int | null
  deploy_tx_ref:        evidence pointer | null
  valid_from:           timestamp | UNKNOWN(bounded)
  valid_to:             timestamp | OPEN
  status:               CANONICAL | BRIDGED_REPRESENTATIVE | WRAPPED | DEPRECATED
                        // PENDING R-1A-5: Option A would add CHANNEL_REPRESENTATIVE
}
```

### Realization identity (PENDING_OPERATOR_DECISION R-1A-5 — shown for Option C only; NOT adopted)
```text
RealizationIdentity {
  realization_id:       "<object_id>@<chain_object_id>:<realization_marker>"
  canonical_object:     object_id                     // what this realizes
  mechanism:            IBC | CHAIN_KEY | LOCK_MINT | LIGHT_CLIENT | OTHER(def)
  route_spec:           channel_id | route string     // per C-3 route_attributes
  valid_from / valid_to / claim_bindings:             // Bloc 1D rules apply
}
// NOTE: This schema is presented because the decision packet recommends
// Option C. It is NOT contract until the operator chooses. If Option A is
// chosen, this block is deleted and the deployment-status enum gains
// CHANNEL_REPRESENTATIVE instead.
```

### Merge/split event
Unchanged from v0.1 (IdentityResolutionEvent).

## 1A.7 Key semantic rules
Unchanged from v0.1 (rules 1–9), plus:

10. **Marker typing (C-2):** every deployment carries exactly one marker; the marker *type* is part of deployment identity. Marker-type correction is an operator-reviewed reclassification event, never a silent edit.
11. **Channel-bound representations (PENDING R-1A-5):** IBC vouchers and analogous non-custodial channel-bound forms are representable only per the operator's chosen option; Option B (attribute-level time) is contractually rejected as violating Bloc 1D record-level rules.

## 1A.8 Invariants
- INV-1A-1: every object has exactly one `object_id`, one `object_type`, minted once.
- INV-1A-2: no two ACTIVE objects share an `(object_type, slug)` pair; intra-type slug collisions route through disambiguation slugs + Operator Decision Log (never silent dedup). *(C-11 clarification)*
- INV-1A-3: every deployment references a chain by `object_id`, never by name/ticker.
- INV-1A-4: deleting an object is impossible; only lifecycle transitions.
- INV-1A-5: every historical alias/ticker window is non-overlapping per object unless explicitly collision-marked.
- INV-1A-6: merge/split events are irreversible (a reverse requires a new event).
- INV-1A-7: a token object without at least one deployment, realization, or `NATIVE_TO` edge is invalid (except `HISTORICAL` pre-launch states marked `UNRESOLVED`).
- INV-1A-8 (new, C-2): every deployment marker is a valid enum value; `OTHER` requires a defining string and a Book 3B family registration.

## 1A.9 Adversarial cases
All v0.1 cases ADV-1A-A..M unchanged, plus:

- ADV-1A-N (new): the same canonical asset exists simultaneously as a native-channel IBC voucher on two chains and via a custodial bridge on a third — canonical identity, deployments, and (per R-1A-5 outcome) realizations must all coexist without conflation. **Resolution mechanism PENDING_OPERATOR_DECISION R-1A-5.**

## 1A.10 Tests
All v0.1 tests T-1A-1..10 unchanged, plus:

- T-1A-11 (C-8, from E-6): XRPL trustline issuance — issued asset anchored by ISSUER_ACCOUNT marker; all Bloc 1A invariants hold without contract semantics.
- T-1A-12 (C-8, from E-5): marker enum round-trip for all seven marker types; invalid marker rejected.
- T-1A-13 (C-8, from E-13 — **PENDING R-1A-5**): USDC across multiple IBC channels: multiple channel-bound forms coexist; channel closure ends one form without touching others; multi-hop intermediate forms representable; aggregation to canonical is a derived view only.

## 1A.11 Evidence artifacts
Unchanged from v0.1, plus:
- Stress-matrix ERRATA v0.1.1 and `CSIA_BOOK_1_EXTENSION_ADJUDICATION_v0.1.md` (E-5, E-13 rows).
- R-1A-5 operator decision record (Operator Decision Log) — **required for freeze**.

## 1A.12 Operator review points
- R-1A-1..R-1A-4 unchanged from v0.1.
- R-1A-5: IBC voucher representation — **decided via `CSIA_OPERATOR_DECISION_PACKET_BOOK0_BOOK1_v0.1.md` Part II; blocking Bloc 1A freeze.**

## 1A.13 Exit gate
```text
PASS_CSIA_B1A_IDENTITY_SEALED
Requires: identity doctrine (1A.6–1A.9, v0.2) reviewed; all 14 adversarial
cases representable; invariants INV-1A-1..8 accepted; operator review
points R-1A-1..5 recorded in Operator Decision Log.
PENDING_OPERATOR_DECISION: R-1A-5 (blocks this gate); D1 (blocks all gates).
```

---

# BLOC 1B — NODE ONTOLOGY

## 1B.1 Purpose
Unchanged from v0.1.

## 1B.2 Scope
Unchanged from v0.1, plus: finality-device slot reservation (C-6); `STATE_CHANNEL` tag (C-5).

## 1B.3 Non-goals
Unchanged from v0.1.

## 1B.4 Inputs
Unchanged from v0.1, plus adjudication (E-2, E-7, E-12) and ERRATA v0.1.1.

## 1B.5 Outputs
Unchanged from v0.1.

## 1B.6 Schemas / registries (planning specification)

### Initial primary classes
The 41-class registry from v0.1 stands **unchanged in v0.2** — no class was adjudicated as required. (`REALIZATION` at 42 classes exists only if the operator chooses R-1A-5 Option C; until then the registry is frozen at 41.)

### Role-tag registry (v0.2 changes only)
- Architecture roles: v0.1 list **plus** `STATE_CHANNEL` (C-5/E-2).
- Functional roles: v0.1 list, with `MEV_INFRASTRUCTURE` definition clarified (C-7/E-7): *"family-specific manifestations (Ethereum builder/relay, Solana block-engine) live in family extension slots; the tag itself takes no family parameters."*

### Architecture extension slots (v0.2 changes only)
- v0.1 slot list stands, **plus** `finality_device` slot (C-6/E-12): `LINEAR_DETERMINISTIC | PROBABILISTIC | DECLARATIVE_DAG | BFT_INSTANT | OPTIMISTIC | ZK_ROLLUP | OTHER(defining)` — *registry and semantics reserved here; value-population owned by Book 3B* (recorded INFORMATION GAP in stress-matrix errata).
- Subnet/shard sub-objects: family-scoped scope-objects (referenced by chain_scope per C-4) are noted here for Book 3B family models; Book 1 reserves the reference mechanism only.

### Unresolved class
Unchanged from v0.1.

## 1B.7 Invariants
All v0.1 invariants INV-1B-1..6 unchanged, plus:
- INV-1B-7 (new, C-6): family slots may reserve value-sets; they may not declare values without a family registration (prevents slot inflation).

## 1B.8 Adversarial cases
All v0.1 cases ADV-1B-A..J unchanged, plus:
- ADV-1B-K (new): a state-channel L2 (Lightning-style) must carry `STATE_CHANNEL` + `PAYMENT_RAIL` roles and must NOT require `USES_VM` or a VM object (exercises C-5 and the anti-EVM-bias test path).

## 1B.9 Tests
All v0.1 tests T-1B-1..6 unchanged, plus:
- T-1B-7 (C-8, from E-2): state-channel L2 representation per ADV-1B-K.
- T-1B-8 (new, C-6): finality-device slot accepts registered family values, rejects unregistered ones (INV-1B-7).

## 1B.10 Evidence artifacts
Unchanged from v0.1, plus adjudication rows E-2, E-7, E-12.

## 1B.11 Operator review points
R-1B-1..4 unchanged from v0.1 (R-1B-1 now reviews the 41-class registry *as clarified by v0.2*, noting the potential 42nd class is pending R-1A-5).

## 1B.12 Exit gate
```text
PASS_CSIA_B1B_NODE_ONTOLOGY_SEALED
Requires: registries (v0.2) ratified (R-1B-1..4); all adversarial cases
(ADV-1B-A..K) representable; T-1B-6 anti-EVM-bias test accepted as a
permanent regression test.
PENDING_OPERATOR_DECISION: D1 (blocks all gates); registry final count
waits on R-1A-5 outcome (42nd class conditional).
```

---

# BLOC 1C — RELATIONSHIP ONTOLOGY

## 1C.1 Purpose
Unchanged from v0.1.

## 1C.2 Scope
Unchanged from v0.1, plus: security-mechanism attribute (C-1); route-attribute group on hyperedges (C-3); chain_scope attribute (C-4); conditional REALIZES/RECEIVED_VIA edge entries **PENDING R-1A-5**.

## 1C.3 Non-goals
Unchanged from v0.1.

## 1C.4 Inputs
Unchanged from v0.1, plus adjudication (E-1, E-8, E-10, E-11, E-13).

## 1C.5 Outputs
Unchanged from v0.1.

## 1C.6 Edge dictionary (v0.2 changes only; all v0.1 entries stand)

```text
SECURED_BY     (v0.2, C-1/E-1) — adds mandatory attribute:
               mechanism: POW | POS | DPOS | BFT_FAMILY | THRESHOLD_BFT
                        | HYBRID | FEDERATED | OTHER(defining_string)
               family-specific refinement populates in Book 3B. Mechanism
               is temporal (PoW→PoS transitions are world-changes).

SECURES        (v0.2) — inverse of SECURED_BY; carries the same mechanism.

RUNS_ON        (v0.2, C-4/E-10) — adds attribute:
               chain_scope: CHAIN | SUBNET(subnet_ref) | SHARD(shard_ref)
                          | PARTITION(partition_ref)
               subnet/shard/partition references resolve to family-scoped
               scope-objects by object_id (Book 3B owns the objects).

VALIDATED_BY   (v0.2, C-4/E-10) — same chain_scope attribute; enables
               subnet-level validation representation (ICP).

REALIZES       (PENDING_OPERATOR_DECISION R-1A-5, Option C only)
               def: chain-local realization object represents the canonical
               economic asset. dir: realization -> canonical asset.
               inverse: REALIZED_BY. temporal: standing per realization.
RECEIVED_VIA   (PENDING_OPERATOR_DECISION R-1A-5, Option C only)
               def: realization arrived via the referenced channel/route.
               dir: realization -> channel/route. temporal: standing while
               route holds.
```

## 1C.7 Hyperedge rules (v0.2 changes only)

```text
Hyperedge registry (v0.2, C-3/E-8): every HE-BRIDGE-ROUTE (and, by
extension, HE-ISSUANCE where routes matter) carries a route_attributes
group:
  route_attributes: { route_spec (channel_id | route string),
                       state, version, mechanism }
mechanism family typing: IBC_CHANNEL | CHAIN_KEY | LOCK_MINT |
  LIGHT_CLIENT | OTHER(defining). Attribute VALUES are populated in
  Book 3B/4B (Information Gap recorded in stress-matrix errata); the
  attribute GROUP is contractual in Book 1.
```
All other v0.1 hyperedge classes and rules unchanged. E-11 (chain-key mechanism) is subsumed by this group — adjudication mapping recorded.

## 1C.8 Invalid-relationship rules
All v0.1 rules IR-1..IR-10 unchanged, plus:
- IR-11 (new, C-1): SECURED_BY/SECURES edges without a mechanism attribute are invalid.
- IR-12 (new, C-3): HE-BRIDGE-ROUTE without route_attributes is invalid at canonical state.

## 1C.9 Invariants
All v0.1 invariants INV-1C-1..5 unchanged, plus:
- INV-1C-6 (new): mechanism and route_attributes groups are temporal per record; their history replays under Bloc 1D rules (never attribute-level time — the defect that disqualified R-1A-5 Option B).

## 1C.10 Adversarial cases
All v0.1 cases ADV-1C-A..J unchanged, plus:
- ADV-1C-K (new): same asset routed over two distinct IBC channels on the same chain — two HE-BRIDGE-ROUTE hyperedges with distinct route_attributes; one channel closes (valid_to on one hyperedge only). *(C-8/T-1C-12)*
- ADV-1C-L (new): a chain's security mechanism changes (PoW→PoS) — SECURED_BY mechanism attribute transitions via a new record with valid_from at the merge/transition point; history preserved. *(C-8/T-1C-11)*

## 1C.11 Tests
All v0.1 tests T-1C-1..10 unchanged, plus:
- T-1C-11 (C-8): mechanism attribute mandatory; PoW≠PoS≠BFT values; mechanism-change over valid-time.
- T-1C-12 (C-8): multi-channel hyperedges per ADV-1C-K; include one chain-key route case (E-11 subsumption check).
- T-1C-13 (C-8): subnet chain_scope per RUNS_ON/VALIDATED_BY; subnet removal sets valid_to.
- T-1C-14 (PENDING R-1A-5): REALIZES/RECEIVED_VIA semantics per chosen option (present only if Option C).

## 1C.12 Operator review points
R-1C-1..4 unchanged from v0.1, plus:
- R-1C-5 (new): ratify the route_attributes group and mechanism enum as adjudicated (C-1, C-3).

## 1C.13 Exit gate
```text
PASS_CSIA_B1C_RELATIONSHIP_ONTOLOGY_SEALED
Requires: full edge dictionary (v0.2) ratified; hyperedge registry with
route_attributes ratified; all invalid-relationship rules IR-1..12
test-mapped; ADV-1C-A..L representable; review points R-1C-1..5 recorded.
PENDING_OPERATOR_DECISION: D1 (blocks all gates); R-1A-5 outcome folds
conditional edges into the dictionary before freeze.
```

---

# BLOC 1D — TEMPORAL GRAPH

## 1D.1 Purpose — unchanged from v0.1.
## 1D.2 Scope — unchanged from v0.1, plus: ADV-1D-J finality-anchoring explicitly references the reserved finality_device slot (C-6).
## 1D.3 Non-goals — unchanged from v0.1.
## 1D.4 Inputs — unchanged from v0.1, plus adjudication (E-12) and ERRATA v0.1.1.
## 1D.5 Outputs — unchanged from v0.1.

## 1D.6 Temporal schema rules — **all v0.1 rules R1–R10 unchanged** (they were the contract that disqualified R-1A-5 Option B; no change was adjudicated).

### Stale policy, supersession, appearance/disappearance, migration semantics, replay contract RC-1..RC-4, schema-migration doctrine — all unchanged from v0.1.

## 1D.7 Invariants — all v0.1 invariants INV-1D-1..6 unchanged.

## 1D.8 Adversarial cases — all v0.1 cases ADV-1D-A..J unchanged, plus:
- ADV-1D-K (new, C-8/E-12): a DAG-network fact whose valid-time anchor is its declared finality device (from the reserved slot) rather than block appearance — replay as-known(k) honors the declared device at that time, including across a finality-device upgrade.

## 1D.9 Tests — all v0.1 tests T-1D-1..10 unchanged, plus:
- T-1D-11 (C-8, from E-12): finality-anchored valid time per ADV-1D-K, including device-upgrade transitions.

## 1D.10 Evidence artifacts — unchanged from v0.1, plus adjudication row E-12 and the stress-matrix five-category verdict.

## 1D.11 Operator review points — R-1D-1..4 unchanged from v0.1.

## 1D.12 Exit gate
```text
PASS_CSIA_B1_TEMPORAL_GRAPH_FOUNDATION
Requires: temporal rules R1–R10 ratified; stale policy ratified; replay
contract accepted as Book 7D binding input; all 11 adversarial cases
representable; review points R-1D-1..4 recorded.
PENDING_OPERATOR_DECISION: D1 (blocks all gates). Bloc 1D itself has no
R-1A-5 dependency but its record-level rules govern the R-1A-5 outcome.
```

---

# Book 1 consolidated dependency and gate map (v0.2)

```text
1A IDENTITY ──┐
              ├──> 1C RELATIONSHIPS ──> 1D TEMPORAL ──> PASS_CSIA_B1_...
1B NODE ONTOLOGY ──┘        │                  │
                            └── validated by ──┴──> PILOT STRESS MATRIX
                            (five-category verdict; ERRATA v0.1.1)

GATING (new in v0.2):
  D1 (Constitution ratification) gates EVERY bloc freeze.
  R-1A-5 gates Bloc 1A freeze; its outcome folds into 1C before freeze.
  E-1/E-5/E-8/E-10 are folded into this v0.2 and ride the normal review points.
```

End of Book 1 detailed planning book v0.2.
