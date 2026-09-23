# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 1 — IDENTITY, ONTOLOGY, AND TEMPORAL KNOWLEDGE GRAPH
## Detailed Planning Book v0.1

**Document ID:** CSIA-B1-PLAN-001
**Version:** 0.1
**Status:** PLANNED — FROZEN_FOR_REVIEW (planning only; no implementation authorized)
**Depends on:** `CSIA_CONSTITUTION_v0.2.md` (assumed ratified per Book 0 packet D1–D6), `CSIA_BOOK_0_RATIFICATION_PACKET.md`
**Companion:** `CSIA_BOOK_1_PILOT_ONTOLOGY_STRESS_MATRIX.md`
**Planning branch:** `agent/crypto-systems-intelligence-atlas-plan`
**Constitutional anchors:** §8 (identity), §9 (ontology), §10 (relationships), §11 (hypergraph), §12 (temporal), §7 (claim states)

---

# 0. Book-level contract

## Purpose
Create the machine-readable language needed to describe crypto systems without flattening them: canonical identity, node ontology, relationship ontology (including hyperedges), and the bitemporal graph foundation.

## Scope
Blocs 1A (canonical identity), 1B (node ontology), 1C (relationship ontology), 1D (temporal graph). All four blocs are **planning + schema-doctrine blocs** in this book; this document is their full plan.

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
3. All schemas in this document are **planning specifications inside a planning document** — no schema files are created outside planning docs (per operator strict rules).

## Book exit gate
`PASS_CSIA_B1_TEMPORAL_GRAPH_FOUNDATION` (per Roadmap) — achieved when Blocs 1A–1D each pass their own exit gates and the pilot stress matrix validates the ontology against seven unlike architectures (Phase 4 companion doc).

---

# BLOC 1A — CANONICAL IDENTITY

## 1A.1 Purpose
Establish identity as the immutable foundation of the graph: every object gets one canonical, ticker-independent, temporally-stable identity, with explicit handling of the messy reality — ticker collisions, rebrands, forks, migrations, contract deployments, multi-chain presence.

## 1A.2 Scope
- Object ID scheme and minting rules (Constitution §8.2).
- Namespace design (object types as namespaces; chain namespaces for deployments).
- Token vs protocol vs chain vs entity separation.
- Ticker collision resolution.
- Alias and rebrand doctrine.
- Fork identity.
- Migration identity.
- Contract-address / deployment identity, including native markers.
- Multi-chain deployment mapping.
- Identity lifecycle states (ACTIVE / DEPRECATED / HISTORICAL). `[→MI-10]`
- Merge and split operations. `[→CR-06]`

## 1A.3 Non-goals
- Identity verification evidence (Book 2 proves claims about identity; 1A defines identity structure).
- Human-readable display/rendering decisions (Book 9).
- Wallet address identity (addresses of *users* are not CSIA graph objects).

## 1A.4 Inputs
- Constitution §8 (v0.2).
- Roadmap Bloc 1A chapters 1A.1–1A.5.
- Pilot stress matrix cases (companion doc).
- Operator decisions D1–D6 (Book 0 packet).

## 1A.5 Outputs
- ratified identity doctrine section (this doc §1A.6–1A.9);
- identity field schemas (planning-level, below);
- adversarial case catalog (§1A.10);
- test plan (§1A.11);
- evidence artifact list (§1A.12).

## 1A.6 Schemas (planning specification)

### Canonical object identity
```text
ObjectIdentity {
  object_id:            "csia:<type>:<slug>"        // immutable, minted once
  object_type:          primary class from Bloc 1B enumeration
  role_tags:            [role, ...]                  // from Bloc 1B role registry
  canonical_name:       string                       // current display name
  aliases:              [ {name, valid_from, valid_to, name_state}, ... ]
  ticker_symbols:       [ {symbol, context, valid_from, valid_to,
                           collision_group|null}, ... ]
  chain_namespace:      chain object_id | null       // for natively-chain-scoped objects
  deployments:          [DeploymentIdentity, ...]
  entity_relationships: [edge_id, ...]
  lifecycle_state:      ACTIVE | DEPRECATED | HISTORICAL
  valid_from:           timestamp | UNKNOWN(bounded)
  valid_to:             timestamp | OPEN | UNKNOWN(bounded)
  claim_bindings:       [claim_evidence_id, ...]     // per Constitution §7
}
```

### Deployment identity
```text
DeploymentIdentity {
  deployment_id:        "<object_id>@<chain_object_id>:<address|native>"
  chain:                chain object_id (never a chain *name*)
  address:              contract address string | NATIVE_MARKER
  standard:             standard object_id | null     // e.g. ERC-20 vs SPL token vs TRC-20
  decimals:             int | null
  deploy_tx_ref:        evidence pointer | null       // not stored raw; Book 2 binding
  valid_from:           timestamp | UNKNOWN(bounded)
  valid_to:             timestamp | OPEN
  status:               CANONICAL | BRIDGED_REPRESENTATIVE | WRAPPED | DEPRECATED
}
```

### Merge/split event
```text
IdentityResolutionEvent {
  event_id
  kind:            MERGE | SPLIT
  subject_ids:     [object_id, ...]
  survivor_id:     object_id            // for MERGE
  created_ids:     [object_id, ...]     // for SPLIT
  reason
  evidence_refs:   [claim_evidence_id, ...]
  decided_by:      OPERATOR (mandatory)
  decided_at
}
```

## 1A.7 Key semantic rules
1. **ID immutability**: `object_id` never changes referent. Rebrand = alias update; migration = deployment/relationship update; the ID persists.
2. **Namespace separation**: `csia:token:usdc` and `csia:protocol:circle` and `csia:entity:circle-internet-group` are distinct objects regardless of shared branding. Type namespaces make same-slug collisions safe.
3. **Ticker rules**:
   - A ticker is an *attribute with context* (venue, chain, valid window), never an identity.
   - Ticker reuse (e.g., historically reused symbols across unrelated tokens) is resolved via `collision_group` — a recorded disambiguation decision, operator-reviewed.
   - No dedup or merge may ever key on ticker alone.
4. **Aliases** carry their own valid-time windows; an alias that becomes another object's canonical name (name reuse across projects) is a collision case, not a merge case.
5. **Forks**: always new `object_id`. `FORKED_FROM` edge is mandatory. Hard-fork chain continuities (e.g., post-split chains both claiming lineage) each get their own ID; the lineage ambiguity is expressed as two competing `FORKED_FROM` edges at `CONTESTED` claim state, not resolved editorially.
6. **Migrations**: same object, new deployments + `MIGRATED_FROM/MIGRATED_TO` edges with valid-time bounds. Token-swap migrations preserve the old token as a separate (deprecated) token object with a `REDEEMS_FOR` edge if a redemption contract exists — otherwise `MIGRATED_TO`.
7. **Contract addresses**: never canonical. The same address string on different chains is different deployments. Address reuse within a chain across time is a collision case.
8. **Native vs bridged**: a bridged representative (e.g., USDC.e on a chain) is a *separate token object* with `status: BRIDGED_REPRESENTATIVE` and a `WRAPS` edge to the canonical token — never the same object.
9. **Merges/splits** are operator-approved events with full history preservation (Constitution §8.3).

## 1A.8 Invariants
- INV-1A-1: every object has exactly one `object_id`, one `object_type`, minted once.
- INV-1A-2: no two ACTIVE objects share an `(object_type, slug)` pair.
- INV-1A-3: every deployment references a chain by `object_id`, never by name/ticker.
- INV-1A-4: deleting an object is impossible; only lifecycle transitions.
- INV-1A-5: every historical alias/ticker window is non-overlapping per object unless explicitly collision-marked.
- INV-1A-6: merge/split events are irreversible (a reverse requires a new event).
- INV-1A-7: a token object without at least one deployment or `NATIVE_TO` edge is invalid (except in `HISTORICAL` pre-launch planning states, which must be marked `UNRESOLVED`).

## 1A.9 Adversarial cases (must be representable without contradiction)
- ADV-1A-A: Two unrelated tokens share ticker "GAS" on different chains.
- ADV-1A-B: One ticker reused by the *same* project across a migration (old dead contract, new contract) — same object, two deployments.
- ADV-1A-C: Project rebrands twice; old name later reused by an unrelated project (alias collision across objects).
- ADV-1A-D: Post-fork chains (e.g., a contested chain split) — two chains, both claiming lineage; competing `FORKED_FROM` edges.
- ADV-1A-E: Token migrates chain via 1:1 swap; old token keeps trading on dead liquidity.
- ADV-1A-F: Bridged representative later becomes natively issued (bridged→native transition, e.g., native USDC rollout) — two objects, relationship changes class, valid-time critical.
- ADV-1A-G: Same contract address string on two different chains.
- ADV-1A-H: Contract address redeployed on same chain after selfdestruct (address reuse across time).
- ADV-1A-I: A "chain" that is actually a protocol on another chain (layer confusion, e.g., networks marketed as L1 that are applications/settlement bridges).
- ADV-1A-J: An entity, its foundation, its token, and its protocol all share one brand name.
- ADV-1A-K: Multi-chain token where one deployment is the canonical issuer and others are burn-and-mint representations — issuer topology must be representable.
- ADV-1A-L: A stablecoin whose issuer rebrands the *token* (not the entity) — ticker change with same object_id.
- ADV-1A-M: Fake copycat deployment impersonating a canonical token (metadata spoofing) — must be classifiable as `QUARANTINED`/spoof, not merged by metadata similarity.

## 1A.10 Tests (planned; no implementation now)
- T-1A-1: ID minting determinism (same inputs → same slug; collision → disambiguation event).
- T-1A-2: no merge on ticker match alone (ADV-1A-A).
- T-1A-3: rebrand preserves identity and alias windows (ADV-1A-C).
- T-1A-4: fork mints new ID + mandatory FORKED_FROM (ADV-1A-D).
- T-1A-5: bridged/native transition produces two objects and a class-changing relationship (ADV-1A-F).
- T-1A-6: deployment uniqueness per (chain, address) and cross-chain same-address separation (ADV-1A-G).
- T-1A-7: merge/split reversibility is event-mediated (INV-1A-6).
- T-1A-8: spoof deployment not merged via metadata similarity (ADV-1A-M).
- T-1A-9: namespace collision safety (`csia:token:x` vs `csia:chain:x`).
- T-1A-10: lifecycle transitions never delete history (INV-1A-4).

## 1A.11 Evidence artifacts (for bloc ratification)
- This document §1A as the identity doctrine spec.
- Operator Decision Log entry for the ID scheme and collision-group policy.
- Pilot stress matrix (companion doc) §1A rows demonstrating identity sufficiency for 7 unlike architectures.
- Review record mapping each ADV/T item to a schema rule.

## 1A.12 Operator review points
- R-1A-1: approve ID scheme format and slug policy.
- R-1A-2: approve ticker collision-group policy.
- R-1A-3: approve bridged-representative-as-separate-object rule (impacts many future counts).
- R-1A-4: standing authority pattern for merge/split approvals.

## 1A.13 Exit gate
```text
PASS_CSIA_B1A_IDENTITY_SEALED
Requires: identity doctrine (1A.6–1A.9) reviewed; all 13 adversarial cases
representable; invariants INV-1A-1..7 accepted; operator review points
R-1A-1..4 recorded in Operator Decision Log.
```

---

# BLOC 1B — NODE ONTOLOGY

## 1B.1 Purpose
Define the complete initial set of node classes (primary classes + role tags), the extension mechanism for new classes and architecture-specific classes, and the treatment of unresolved objects — so that no crypto system is ever forced into a wrong shape.

## 1B.2 Scope
- Primary class enumeration (initial set).
- Role-tag registry.
- Architecture-family role-tag/attribute slots (EVM, UTXO, XRPL, SVM, Cosmos, Substrate, Move, ICP, DAG, TON, Hedera, eUTXO, Algorand, privacy, permissioned, modular). `[→MI-09, SG-A]`
- Infrastructure class coverage: sequencers, provers/attestation, intent/solvers, key management, insurance, MEV infrastructure. `[→SG-B]`
- Extension mechanism (proposal → operator review → Decision Log → version bump).
- Unresolved-class doctrine.
- Object lifecycle states.

## 1B.3 Non-goals
- Per-chain anatomy content (Book 3B owns family *models*; 1B owns the *classes and extension slots*).
- Class instantiation / population (Book 2+ evidence).
- Metric/source classes (excluded from domain ontology — Constitution §9.4).

## 1B.4 Inputs
- Constitution §9 (v0.2), IACER §A2, §A5.
- Review issues MA-03, SG-A, SG-B, MI-04, MI-09, MI-10.
- Pilot stress matrix (companion).

## 1B.5 Outputs
- Initial primary-class registry (below).
- Role-tag registry (below).
- Architecture extension-slot registry (below).
- Extension mechanism spec.
- Adversarial cases, tests, evidence, review points, exit gate.

## 1B.6 Schemas / registries (planning specification)

### Initial primary classes (41)
Constitution §9.2 list, carried forward as the Book 1 registry: BLOCKCHAIN, LEDGER, PROTOCOL, TOKEN, STABLECOIN, BRIDGE, ORACLE_NETWORK, INTEROP_PROTOCOL, DATA_AVAILABILITY_NETWORK, DEX, PERP_DEX, LENDING_PROTOCOL, STAKING_PROTOCOL, RESTAKING_PROTOCOL, RWA_PROTOCOL, PAYMENT_SYSTEM, STORAGE_NETWORK, COMPUTE_NETWORK, DEPIN_NETWORK, IDENTITY_SYSTEM, PRIVACY_SYSTEM, WALLET_INFRASTRUCTURE, KEY_MANAGEMENT_INFRASTRUCTURE, RPC_INFRASTRUCTURE, INDEXING_INFRASTRUCTURE, DEVELOPER_TOOLING, SEQUENCER_INFRASTRUCTURE, PROVER_ATTESTATION_INFRASTRUCTURE, INTENT_SOLVER_NETWORK, INSURANCE_SECURITY_PROTOCOL, VM, STANDARD, VALIDATOR_SYSTEM, GOVERNANCE_SYSTEM, ENTITY, ASSET, MARKET, APPLICATION, INTEGRATION, EVENT, NARRATIVE.

### Role-tag registry (initial)
Architecture roles (tags on BLOCKCHAIN/LEDGER): `ROLLUP_OPTIMISTIC`, `ROLLUP_ZK`, `VALIDIUM`, `L3`, `SIDECHAIN`, `APPCHAIN`, `DAG`, `MODULAR`, `MONOLITHIC`, `UTXO`, `EUTXO`, `ACCOUNT`, `EVM`, `SVM`, `MOVE_VM`, `WASM_VM`, `CANISTER_COMPUTE`, `ACTOR_MODEL`, `HASHGRAPH_BFT`, `BRAIDED_POW`, `PURE_POS_INSTANT_FINALITY`, `SHIELDED_POOL`, `PERMISSIONED`, `SUBSTRATE_RELAY`, `IBC_SOVEREIGN`.
Functional roles (tags on PROTOCOL etc.): `LIQUIDITY_ROUTER`, `DATA_DELIVERY`, `CROSS_CHAIN_MESSAGING`, `AUTOMATION`, `PROOF_OF_RESERVE`, `MEV_INFRASTRUCTURE`, `COLLATERAL_HUB`, `YIELD_AGGREGATOR`, `PAYMENT_RAIL`, `SETTLEMENT_ASSET`.

### Architecture extension slots
Each architecture family declares native attributes that have no EVM equivalent; these live as family-scoped attribute groups on BLOCKCHAIN/LEDGER objects (Book 3B populates them): UTXO-set semantics; XRPL trustlines/UNL; ICP subnets/canisters/reverse-gas; Solana stake/fee markets; Cosmos IBC channels/ICS; Substrate parachain slots/XCM; DAG tip selection/finality devices; TON actor/sharding; Hedera mirror-node semantics; eUTXO validators; shielded-pool proof systems; permissioned membership lists.

### Unresolved class
```text
UnresolvedObject {
  object_id:      "csia:unresolved:<slug>"
  observed_traits: [free-form evidence-bound traits]
  candidate_classes: [primary class guesses with confidence + reasoning]
  resolution_state: UNCLASSIFIED | PENDING_REVIEW | RECLASSIFIED_TO(x)
}
```
Rule: unresolved objects participate in the graph fully (edges may attach); they are never forced into the nearest class. Reclassification is an operator-reviewed event with history.

## 1B.7 Invariants
- INV-1B-1: every node has exactly one primary class.
- INV-1B-2: role tags never substitute for primary class (a DEX role tag does not make something a DEX object).
- INV-1B-3: class additions/deprecations only via extension mechanism; never silent remap.
- INV-1B-4: unresolved objects are first-class; no graph consumer may drop them.
- INV-1B-5: architecture-family attributes never overwrite core slots; they extend.
- INV-1B-6: every class and role tag carries a definition string in the registry.

## 1B.8 Adversarial cases
- ADV-1B-A: A rollup that is also a DA network consumer and has its own token — multi-role representation without class explosion.
- ADV-1B-B: A "DEX" on XRPL (native orderbook, no contracts) — must not require EVM contract semantics.
- ADV-1B-C: An oracle that also settles (hybrid network) — role tags without false primary class.
- ADV-1B-D: A bridge that is canonical (chain-native) vs third-party — class same, roles differ.
- ADV-1B-E: A shared sequencer serving multiple rollups — SEQUENCER_INFRASTRUCTURE with multi-client edges.
- ADV-1B-F: A MEV relay/builder ecosystem — representable as class + roles, not entities-only.
- ADV-1B-G: A privacy pool within a public chain (shielded subset) — PRIVACY_SYSTEM as component object, not whole-chain class change.
- ADV-1B-H: A permissioned enterprise ledger bridged to public rails — PERMISSIONED role tag on LEDGER.
- ADV-1B-I: A governance system that spans chains (multichain DAO) — GOVERNANCE_SYSTEM object distinct from ENTITY.
- ADV-1B-J: A DAG network with probabilistic finality — DAG + finality-device attribute, not "chain with weird consensus."

## 1B.9 Tests
- T-1B-1: every registry entry has definition (INV-1B-6).
- T-1B-2: reclassification preserves edge history (INV-1B-3).
- T-1B-3: unresolved object retains edges through reclassification (INV-1B-4).
- T-1B-4: family attributes extend, never overwrite core (ADV-1B-J).
- T-1B-5: multi-role composition without class duplication (ADV-1B-A, C).
- T-1B-6: no EVM-required field is mandatory for non-EVM classes (ADV-1B-B) — the anti-EVM-bias test.

## 1B.10 Evidence artifacts
- Class/role registries as ratified in this doc (with operator Decision Log entry).
- Pilot stress matrix rows proving family sufficiency.
- Extension-mechanism walkthrough record (one hypothetical class proposed end-to-end).

## 1B.11 Operator review points
- R-1B-1: ratify the 41-class initial registry.
- R-1B-2: ratify role-tag registry and the primary/role separation doctrine.
- R-1B-3: ratify unresolved-object doctrine.
- R-1B-4: approve extension-mechanism workflow.

## 1B.12 Exit gate
```text
PASS_CSIA_B1B_NODE_ONTOLOGY_SEALED
Requires: registries ratified (R-1B-1..4); all adversarial cases representable;
T-1B-6 anti-EVM-bias test accepted as a permanent regression test.
```

---

# BLOC 1C — RELATIONSHIP ONTOLOGY

## 1C.1 Purpose
Define every relationship type with precise semantics before any population: direct/typed edges, hyperedges, dependency/settlement/security, interoperability, capital, governance/entity, competitor/complement — and the rules that make invalid relationships impossible or detectable.

## 1C.2 Scope
- Edge dictionary (definition, direction, domain/range, inverse, temporal class) for all Constitution §10.2 types.
- Hyperedge classes and participant roles (Constitution §11.1).
- Dependency-edge family semantics (DIRECT vs transitive is derived — Book 4E computes; 1C defines only direct).
- Settlement/security edges.
- Interoperability edges.
- Capital capability edges (standing edges only; flows are events per §19.1).
- Governance/entity edges.
- Competitor/complement edges.
- Invalid-relationship rules (Constitution §10.3, expanded).

## 1C.3 Non-goals
- Population of edges (Book 2+ evidence).
- Flow events (Book 5; 1C only reserves the event-object distinction).
- Dependency centrality computation (Book 4E).
- Context Bridge semantics (Book 8).

## 1C.4 Inputs
- Constitution §10–11, §19.1.
- Review issues MA-04, CR-07, MA-09.
- IACER §C5 edge list.
- Pilot stress matrix.

## 1C.5 Outputs
- Complete edge dictionary (planning spec below).
- Hyperedge class registry.
- Invalid-relationship rule set.
- Tests, evidence, review points, exit gate.

## 1C.6 Edge dictionary (planning specification — key entries; full dictionary ratified from this spec)

Every edge carries: `{edge_type, subject_id, object_id, claim_binding, valid_from, valid_to, direction semantics per below}`.

Selected critical definitions (illustrating the required rigor; the full 32+ types follow the same template):

```text
RUNS_ON        def: a protocol/VM/application executes on the named chain's
               runtime.  dir: protocol -> chain.  domain: PROTOCOL|APPLICATION
               range: BLOCKCHAIN|LEDGER.  inverse: HOSTS.
               temporal: standing.  NOT valid for tokens (use ISSUED_ON).

SETTLES_TO     def: a system's final trust/security root resolves to the named
               settlement chain. dir: dependent -> settlement.
               domain: BLOCKCHAIN|ROLLUP-role chain. range: BLOCKCHAIN.
               inverse: SETTLES (none). temporal: standing.
               note: rollup -> Ethereum = SETTLES_TO; sidechain with own
               finality and exit bridge = BRIDGES_TO, not SETTLES_TO.

SECURED_BY     def: security of object A is derived from object B's validator
               set/economic security. dir: A -> B. inverse: SECURES.
               temporal: standing. examples: ICS consumer -> provider chain;
               restaked AVS -> EigenLayer.

ISSUED_ON      def: a token has a deployment on the named chain (canonical or
               representation per deployment status). dir: token -> chain.
               range: BLOCKCHAIN|LEDGER. inverse: HOSTS_ISSUANCE.
               temporal: standing per deployment validity.

NATIVE_TO      def: an asset is the native gas/settlement asset of a chain,
               minted by protocol rules not contracts. dir: token -> chain.
               temporal: standing. exclusive with ISSUED_ON per deployment.

COLLATERAL_IN  def: asset A is accepted as collateral by system B.
               dir: asset -> system. inverse: ACCEPTS_COLLATERAL.
               temporal: standing (capability, NOT flow — §19.1).

LIQUIDITY_ON   def: asset A has tradable liquidity hosted in system B.
               dir: asset -> venue. temporal: standing capability.
               capacity metrics attach via measurement layer (Book 6).

DEPENDS_ON     def: A's correct functioning requires B (operational dependency,
               direct). dir: dependent -> dependency. inverse: REQUIRED_BY.
               temporal: standing. note: transitive closure computed in Book 4E,
               never stored as direct edges.

INTEGRATES_WITH def: A advertises/uses B's interface or service, but A functions
               (degraded) without B. dir: integrator -> integrated.
               inverse: INTEGRATED_BY. temporal: standing.
               THE JUNK-DRAWER GUARD: if B is required, use DEPENDS_ON;
               if B is consumed for data, DATA_FROM; if B is mimicked, none.

BRIDGES_TO     def: a bridge object connects two chains. dir: bridge -> chain
               (one edge per chain served) — chain-to-chain connectivity is a
               hyperedge (HE-BRIDGE-ROUTE).

MESSAGES_TO    def: a messaging layer delivers arbitrary messages between
               chains. dir: layer -> chain. temporal: standing.

ORACLE_FOR     def: oracle network supplies price/data to consumer system.
               dir: oracle -> consumer. inverse: PRICED_BY|DATA_FROM.
               temporal: standing.

GOVERNED_BY    def: system A's upgrade/parameter authority is governance B.
               dir: system -> governance. inverse: GOVERNS.
GOVERNED/OWNED/OPERATED_BY connect to ENTITY objects (not each other's chains).

STAKED_IN      def: native asset or receipt is staked in system B for security
               or yield. dir: asset/token -> staking system. inverse: ACCEPTS_STAKE.
RESTAKED_IN    def: staked receipt is re-secured into system B.
               dir: receipt -> restaking system. note: chains of receipts are
               modeled as separate token objects (LRTs) per 1A rules.

FORKED_FROM    def: A's codebase/ledger state derives from B at a point in
               time. dir: fork -> origin. MUST be acyclic. temporal: event-anchored
               (valid_from = fork moment), standing thereafter.

MIGRATED_FROM/TO  def: object A moved its canonical deployment from/to B.
               temporal: event with valid_from = migration completion.

COMPETES_WITH  def: A and B serve substitutable demand. dir: symmetric
               (must be declared once; system normalizes to pair).
               temporal: standing. evidence bar: E2+ (not vibes).
COMPLEMENTS    def: A's use increases B's use (structural complementarity).
               dir: symmetric-declared. evidence bar: E2+ or INFERRED with
               methodology.

WRAPS          def: token B is a 1:1 custodial/synthetic representation of A.
               dir: wrapper -> canonical. inverse: WRAPPED_BY.
               temporal: standing. mandatory for BRIDGED_REPRESENTATIVE objects.

REDEEMS_FOR    def: B redeems 1:1 into A at a defined facility.
               dir: receipt -> underlying. temporal: standing while facility
               exists; valid_to when redemption ends.

ROUTED_THROUGH def: capital route capability exists via C between A and B.
               dir: A -> C (single-hop edges; routes are derivable paths).
               temporal: standing capability. NOT flow (§19.1).

PRICES         def: system A provides valuation for asset B. dir: A -> B.
SECURES        def: inverse reading of SECURED_BY (declared for traversal).

DATA_FROM      def: system A sources data feeds from B. dir: A -> B.
USES_VM        def: chain A executes B (VM object). dir: chain -> VM.
USES_STANDARD  def: object A conforms to standard B. dir: object -> STANDARD.
BUILT_WITH     def: A's client/implementation stack includes B (SDK/framework).
               Weakest structural edge; never upgraded to DEPENDS_ON without
               evidence of requirement.
VALIDATED_BY   def: chain A's blocks are validated by validator system B.
               dir: chain -> VALIDATOR_SYSTEM.
OWNED_BY / OPERATED_BY  def: entity-level custody/operation. dir: system -> ENTITY.
```

### Hyperedge classes (initial)
```text
HE-ISSUANCE     participants: ISSUER(entity), TOKEN, HOST_CHAIN,
                SETTLEMENT_CHAIN(optional).  example: USDC/Base/Circle/ETH.
HE-BRIDGE-ROUTE participants: BRIDGE, CHAIN_A, CHAIN_B, ASSET(optional).
HE-COLLATERAL-LOOP participants: ASSET, VENUE, COLLATERAL_SITE, CHAIN.
HE-SECURITY-SHARE participants: PROVIDER_CHAIN, CONSUMER_CHAIN(s), MECHANISM.
HE-ORACLE-DELIVERY participants: ORACLE, DATA_PUBLISHER(optional), CONSUMER,
                CHAIN.
```
Rule: any multi-party fact that changes meaning when decomposed (Constitution §11.1) must use a hyperedge; the class list above is the initial registry, extensible via 1B extension mechanism.

## 1C.7 Invalid-relationship rules (expanded)
- IR-1: edge endpoints must satisfy the edge dictionary domain/range.
- IR-2: `TOKEN -RUNS_ON-> CHAIN` invalid → use `ISSUED_ON`/`NATIVE_TO`.
- IR-3: `FORKED_FROM` cycles invalid.
- IR-4: `SETTLES_TO` cycles within a settlement hierarchy invalid (settlement must be a DAG).
- IR-5: self-edges invalid except flagged `WRAPS` self-cases.
- IR-6: `valid_from > valid_to` invalid.
- IR-7: an edge asserting requirement (semantics of DEPENDS_ON) may not be recorded as INTEGRATES_WITH (semantics guard, test-enforced).
- IR-8: competitor/complement edges require E2+ evidence or INFERRED+methodology; E4-only is invalid.
- IR-9: hyperedge decomposition into pairs may only exist as derived views (never as primary data).
- IR-10: an edge without a claim_binding (evidence pointer) is invalid at canonical state.

## 1C.8 Invariants
- INV-1C-1: every populated edge type has a complete dictionary entry.
- INV-1C-2: every canonical edge has exactly one claim_binding at minimum DECLARED state.
- INV-1C-3: inverse consistency — if A-R->B exists, B-R'->A either exists or R has declared no inverse.
- INV-1C-4: capability edges never store flow magnitudes (flow = events, Book 5).
- INV-1C-5: hyperedge role coverage — every declared participant role is filled.

## 1C.9 Adversarial cases
- ADV-1C-A: Announcement of integration where only announcement exists (E4) — must land as narrative reference, not edge.
- ADV-1C-B: Integration exists (contract deployed) but unused — INTEGRATES_WITH at OBSERVED, with zero-usage measurement (Book 6), not DEPENDS_ON.
- ADV-1C-C: Dependency discovered after outage (B down → A down) — retroactive DEPENDS_ON with late observed_at, valid_from at true start when provable.
- ADV-1C-D: Two competing "canonical" bridges to the same chain — both BRIDGES_TO, hyperedge routes distinguish.
- ADV-1C-E: A chain that settles to two parents (dual-settlement rollup) — two SETTLES_TO edges, legal, flagged multi-settlement.
- ADV-1C-F: Oracle feeds that are themselves derived from another oracle — DATA_FROM chain, cycle detection.
- ADV-1C-G: "Partnership" press releases (no structural artifact) — E4, never an edge.
- ADV-1C-H: Governance captured/changed via onchain vote — GOVERNED_BY valid-time change with event evidence.
- ADV-1C-I: Wrapped asset losing backing (depeg) — WRAPS edge gets valid_to or CONTESTED claim; depeg path is Book 5/7 territory but edge must express end.
- ADV-1C-J: Restaking recursion (LRT of LRT) — token-object chains per 1A, RESTAKED_IN edges between objects, depth representable.

## 1C.10 Tests
- T-1C-1: domain/range violation detection (IR-1, IR-2).
- T-1C-2: FORKED_FROM and SETTLES_TO acyclicity (IR-3, IR-4).
- T-1C-3: junk-drawer guard — DEPENDS_ON semantics not recorded as INTEGRATES_WITH (IR-7).
- T-1C-4: E4-only edge rejection (IR-8, ADV-1C-A/G).
- T-1C-5: inverse consistency (INV-1C-3).
- T-1C-6: hyperedge decomposition exists only as derived views (IR-9).
- T-1C-7: capability edges hold no magnitudes (INV-1C-4).
- T-1C-8: late-discovery dependency uses bitemporal fields correctly (ADV-1C-C).
- T-1C-9: edge-without-claim-binding rejected (IR-10).
- T-1C-10: dual settlement representation (ADV-1C-E).

## 1C.11 Evidence artifacts
- Full edge dictionary ratified from §1C.6 template (planning doc section + Decision Log entry).
- Hyperedge registry entry.
- Pilot stress matrix edge-type coverage rows.
- Invalid-relationship rule test mapping.

## 1C.12 Operator review points
- R-1C-1: ratify edge dictionary semantics (notably DEPENDS_ON vs INTEGRATES_WITH vs BUILT_WITH boundaries).
- R-1C-2: ratify settlement vs bridge distinction rule.
- R-1C-3: ratify hyperedge class registry.
- R-1C-4: ratify evidence bar for competitor/complement edges.

## 1C.13 Exit gate
```text
PASS_CSIA_B1C_RELATIONSHIP_ONTOLOGY_SEALED
Requires: full edge dictionary ratified; hyperedge registry ratified;
all invalid-relationship rules test-mapped; ADV-1C-A..J representable;
review points R-1C-1..4 recorded.
```

---

# BLOC 1D — TEMPORAL GRAPH

## 1D.1 Purpose
Define the bitemporal schema and semantics for the entire graph — the six timestamps, stale states, uncertainty in valid time, supersession, and the *contract* for historical replay — such that no current-state view can ever silently overwrite history.

## 1D.2 Scope
- Bitemporal axis definitions (Constitution §12.1).
- Six-timestamp semantics (§12.2) instantiated as concrete schema rules.
- Stale-state derivation policy.
- Historical replay *contract* (what must be reconstructible; machinery = Book 7D). `[→MA-13]`
- Migration temporal semantics.
- Relationship appearance/disappearance.
- Uncertain valid time representation.
- Graph schema-migration doctrine (how the temporal schema itself evolves).

## 1D.3 Non-goals
- Replay engines, snapshots infrastructure, change-detection jobs (Books 7D/2).
- Event ontology (Book 7A).
- Time alignment with Crypto Sensor (Book 8B).

## 1D.4 Inputs
- Constitution §12 (bitemporal), §7 (STALE derivation), §29 (reproducibility).
- Review issues MA-02, MA-13, MI-03.
- Pilot stress matrix temporal rows.

## 1D.5 Outputs
- Temporal schema rules (below).
- Stale policy.
- Replay contract.
- Tests, evidence, review points, exit gate.

## 1D.6 Temporal schema rules (planning specification)
```text
Every temporal node/edge/hyperedge record carries:
  observed_at         TRANSACTION — when CSIA first observed this fact
  ingested_at         TRANSACTION — when the evidence entered storage
  superseded_at       TRANSACTION — when a later record replaced THIS record
                      about the same claim (null if current)
  valid_from          VALID — fact began holding in the world (best evidence;
                      may be UNKNOWN(bounded))
  valid_to            VALID — fact ended in the world (null = still holds;
                      may be UNKNOWN(bounded))
  source_published_at VALID-anchor — publication time of the evidence

Derived/required consistency:
  R1  valid_from <= valid_to (when both known)
  R2  ingested_at >= observed_at is not guaranteed (backfill may ingest before
      formal observation pipeline); observed_at <= now
  R3  superseded_at >= observed_at
  R4  a record with superseded_at != null is queryable forever (never deleted)
  R5  current view = records with superseded_at = null (transaction-time filter)
  R6  as-of(valid_t) view = records where valid_from <= valid_t AND
      (valid_to > valid_t OR valid_to = null|open)   [valid-time filter]
  R7  as-known(transaction_t) view = records where observed_at <= transaction_t
      AND (superseded_at > transaction_t OR superseded_at = null)
  R8  late-discovered historical fact: observed_at ≈ now, valid_from in past —
      both views must handle without rewriting other records
  R9  uncertain valid time: valid_from/valid_to may be
      UNKNOWN{earliest_bound, latest_bound, confidence_ref} — queries must
      treat UNKNOWN bounds explicitly, not as null/open
  R10 chain timestamp precision preserved at source; comparison-layer
      normalization is derived, original recoverable
```

### Stale-state policy
```text
STALE is computed, never stored as authored state (Constitution §7.1):
  edge/node is STALE_AS_OF(t) when:
    - its claim_binding evidence has not been re-verified within policy
      window W (policy per relationship family, set in Book 2), OR
    - its valid_to is UNKNOWN(bounded) with last_bound far past, OR
    - its source is expired/dead (source health, Book 2C)
  STALE never changes claim state; it annotates display and triggers
  re-verification queues (Book 9E).
```

### Supersession semantics
- Supersession is record-level: a new record about the same claim supersedes the old one and links `supersedes: record_id`.
- Supersession chains are preserved in full (no pointer collapse).
- World-change vs record-replacement: a bridge shutdown sets `valid_to` on the edge (world change); a correction of the bridge's start date creates a superseding record with corrected `valid_from` (record replacement). Both mechanisms coexist.

### Relationship appearance/disappearance
- Appearance: edge record with `valid_from` (or UNKNOWN bounds) and evidence.
- Disappearance: two legal forms — (a) `valid_to` set (world change, evidence-bound); (b) `REJECTED`/`SUPERSEDED` on the claim (evidence failure). A disappeared edge is never deleted; queries-as-of honor both forms.

### Migration temporal semantics
- A migration is a pair of deployment/relationship transitions sharing a migration event anchor: old deployment `valid_to ≈ migration_time`, new deployment `valid_from ≈ migration_time`, with the *observed* confirmation times recorded separately (transaction time).
- Overlap windows (bridged transition periods where both deployments live) are legal and represented; `≈` semantics use bounded uncertainty, not fabricated exact instants.

### Historical replay contract (what Book 7D machinery must satisfy)
- RC-1: reconstruct the full graph as-of any valid timestamp t.
- RC-2: reconstruct the graph as-known at any transaction timestamp k ("what did we believe then").
- RC-3: replay must include unresolved/stale/contested states as they were, not retroactively cleaned.
- RC-4: schema evolution (this document's own migrations) must not break RC-1/RC-2 — schema version is part of the replay key.

### Schema migration doctrine
- The temporal schema itself is versioned; migrations are additive-first (extend, don't mutate); destructive schema changes require operator Decision Log entry and dual-write verification periods.

## 1D.7 Invariants
- INV-1D-1: no record is ever deleted or mutated in place; corrections are superseding records.
- INV-1D-2: current views derive from transaction-time filters, never from overwriting.
- INV-1D-3: every temporal record satisfies consistency rules R1–R3 or is flagged INVALID.
- INV-1D-4: UNKNOWN bounds are queryable and distinguishable from null/open.
- INV-1D-5: STALE is computable from stored fields + policy only (no authored staleness).
- INV-1D-6: replay contract RC-1..RC-4 is testable from schema alone (property, not machinery).

## 1D.8 Adversarial cases
- ADV-1D-A: Fact observed today, true since 3 years ago, evidence published 2 years ago (late triple discovery) — all three times distinct and consistent.
- ADV-1D-B: Source retracts an integration claim — claim REJECTED; edge valid_to untouched (evidence failure vs world change distinguished).
- ADV-1D-C: Two sources give different valid_from for the same dependency — CONTESTED claim, two record candidates, no averaging.
- ADV-1D-D: Bridge live for 2 years, exact start date unknown to the day — UNKNOWN bounded valid_from.
- ADV-1D-E: Migration with 2-week dual-running window — overlapping deployments representable.
- ADV-1D-F: Backfilled historical sweep ingests 10,000 past facts in one batch — ingested_at identical, observed_at staggered, valid_from historical; replay integrity preserved.
- ADV-1D-G: A stale edge that is still true (no re-verification happened) — STALE annotation without state corruption.
- ADV-1D-H: Schema v2 adds a field; as-known(k) replay before schema v2 must not fabricate the field.
- ADV-1D-I: Superseded record's evidence is later revalidated as correct — supersession chain preserved, no rewrite; revalidation is a new claim state transition.
- ADV-1D-J: Chain reorgs (reorg-sensitive facts, e.g., finality assumptions) — valid-time anchored to finality, not block appearance, for finality-class claims.

## 1D.9 Tests
- T-1D-1: R1–R3 consistency enforcement (INV-1D-3).
- T-1D-2: as-of and as-known views produce correct results for ADV-1D-A.
- T-1D-3: retraction path (ADV-1D-B) vs world-change path distinct.
- T-1D-4: contested temporal candidates coexist (ADV-1D-C).
- T-1D-5: UNKNOWN bounded time in queries (ADV-1D-D, INV-1D-4).
- T-1D-6: dual-running migration windows (ADV-1D-E).
- T-1D-7: bulk backfill replay integrity (ADV-1D-F).
- T-1D-8: STALE computability from fields+policy (INV-1D-5, ADV-1D-G).
- T-1D-9: schema-versioned replay (ADV-1D-H, RC-4).
- T-1D-10: no-deletion enforcement (INV-1D-1).

## 1D.10 Evidence artifacts
- Temporal schema rules ratified (this section + Decision Log).
- Replay contract accepted as Book 7D input requirement.
- Pilot stress matrix temporal rows.
- Test-mapping record.

## 1D.11 Operator review points
- R-1D-1: ratify bitemporal field semantics (§12.2 instantiation).
- R-1D-2: ratify stale-policy as derived-only.
- R-1D-3: ratify replay contract as a binding requirement on Book 7D.
- R-1D-4: ratify schema-migration doctrine.

## 1D.12 Exit gate
```text
PASS_CSIA_B1_TEMPORAL_GRAPH_FOUNDATION
Requires: temporal rules R1–R10 ratified; stale policy ratified; replay
contract accepted as Book 7D binding input; all 10 adversarial cases
representable; review points R-1D-1..4 recorded.
```

---

# Book 1 consolidated dependency and gate map

```text
1A IDENTITY ──┐
              ├──> 1C RELATIONSHIPS ──> 1D TEMPORAL ──> PASS_CSIA_B1_...
1B NODE ONTOLOGY ──┘        │                  │
                            └── validated by ──┴──> PILOT STRESS MATRIX
                                                    (7 unlike architectures)
```

1A and 1B are parallelizable; 1C requires both (domain/range constraints reference classes and identities); 1D is technically independent but gates the book exit; the pilot stress matrix (companion doc) is the book-level validation instrument.

End of Book 1 detailed planning book.
