# CSIA Book 4 — Protocol, Infrastructure, and Dependency Atlas Plan

- **Plan version:** v0.1
- **Date:** 2026-09-24
- **Status:** PLANNING_ONLY — NOT RATIFIED
- **Authority:** Book 4 planning only
- **Implementation authority:** false
- **Live acquisition authority:** false
- **Book 5:** NOT_STARTED

## 1. Purpose

Book 4 maps the systems between chains and applications. Its central problem is
**dependency semantics**, not protocol cataloging. It must explain what service a
protocol provides, who consumes it, what the protocol directly and transitively
depends upon, what depends upon it, where failures can correlate, whether apparent
redundancy is real, and what can be substituted under stated conditions and time.

The plan is deliberately offline. It proposes schemas, classifications, evidence
contracts, stress tests, and decision points. It does not assert current deployment
coverage, acquire live data, or implement source code.

## 2. Authority and preservation constraints

Books 1, 2, and 3 remain frozen and accepted. Book 4 planning may reuse their
accepted contracts but must not mutate them. No dependency relationship is added to
an accepted graph merely because it is a Book 4 planning candidate.

This plan does not authorize:

- source code, tests, collectors, databases, graph databases, or live RPC;
- Book 1, Book 2, Book 3, or Sensor changes;
- Book 5 capital plumbing or capital-flow collection;
- a universal numeric dependency score;
- partnership or branding as dependency evidence;
- integration as hard dependency;
- a catch-all `DEPENDS_ON` model.

## 3. Governing doctrine

The following rules are mandatory throughout Book 4 planning and any later
operator-ratified implementation:

- **B4-P1 — INTEGRATION != DEPENDENCY.** An interface may be used optionally or
  consumed by only one function; this does not establish an operational dependency.
- **B4-P2 — DEPENDENCY != FAILURE DOMAIN.** A required relationship does not prove
  that a failure propagates, and a failure domain need not be a single dependency.
- **B4-P3 — FAILURE DOMAIN != OWNERSHIP.** Common control or ownership may be
  relevant evidence, but is neither definition nor proof of correlated failure.
- **B4-P4 — SHARED PROVIDER != SHARED SECURITY.** Provider overlap does not prove
  identical trust, security, or compromise boundaries.
- **B4-P5 — MESSAGING != BRIDGING.** Message transport does not inherently move,
  lock, mint, burn, or bridge assets.
- **B4-P6 — BRIDGING != SETTLEMENT.** A bridge route does not establish the
  settlement layer of a chain or rollup.
- **B4-P7 — ORACLE CONSUMPTION != GENERIC DATA INTEGRATION.** A price or
  attestation feed is not flattened into a generic `DATA_FROM` relationship.
- **B4-P8 — REDUNDANCY != SUBSTITUTABILITY.** A second provider does not prove that
  switching is technically, operationally, or economically possible.
- **B4-P9 — MULTIPLE PROVIDERS != FAILURE INDEPENDENCE.** Multiple brands may
  share cloud, operator, upstream data, verifier, code, or governance.
- **B4-P10 — DIRECT DEPENDENCY != TRANSITIVE DEPENDENCY.** A transitive relation
  must retain the ordered path that supports it.
- **B4-P11 — A PROTOCOL MAY HAVE MULTIPLE INFRASTRUCTURE ROLES.** Roles are
  multi-valued and non-exclusive.
- **B4-P12 — ROLE IDENTITY != TOKEN IDENTITY.** Economic or governance token
  effects are not the service-role definition.
- **B4-P13 — DEPENDENCY STRENGTH MUST BE EVIDENCE-BACKED.** Strength describes
  architecture, not investment importance, and cannot be asserted from branding.
- **B4-P14 — UNKNOWN DEPENDENCY MUST REMAIN UNKNOWN.** Missing or conflicting
  evidence may not be collapsed into a stronger or weaker claim.
- **B4-P15 — BOOK 4 MUST NOT ABSORB CAPITAL PLUMBING FROM BOOK 5.** Technical
  routes and dependencies stop short of capital flow, liquidity, yield, and
  economic concentration analysis.

## 4. Representation principles

1. Reuse accepted Book 1 edges and the accepted hyperedge primitive where faithful.
2. Prefer a typed local record or attributes on an existing edge over a new edge type.
3. Project only when semantics, identity, time, and evidence survive projection.
4. Preserve Book 3-local `EXECUTES_WITH`, `USES_DA`, and `SEQUENCED_BY`; do not
   alias Book 3 relations to `DEPENDS_ON`.
5. Keep source, destination, function, mechanism, evidence, and valid time explicit.
6. Unknown classifications remain visible and queryable.
7. Infrastructure role identity is separate from token identity and ownership.
8. No candidate is added automatically; the relationship-support matrix classifies
   support and operator decisions without self-ratifying extensions.

## 5. Candidate Book 4 local records

The names below are planning candidates, not a ratified schema.

### 5.1 `DependencyRecord`

```text
dependency_id
subject_ref
object_ref
function
direction = subject_to_object
relation_basis                 # existing edge or Book 4 typed semantic
dependency_class               # candidate class, multi-valued only if justified
dependency_strength            # REQUIRED | PRIMARY | FALLBACK | OPTIONAL |
                               # LEGACY | DEPRECATED | UNKNOWN
runtime_scope                  # HARD_RUNTIME | SOFT_RUNTIME | BUILD_TIME |
                               # CONTROL_PLANE | OUT_OF_BAND | UNKNOWN
criticality_basis[]            # evidence-backed consequences, not a score
mechanism[]                    # protocol/configuration/operator path
direct_or_transitive           # direct claims only; transitive via DependencyPath
valid_from
valid_to
observed_at
book2_claim_refs[]
source_snapshot_refs[]
confidence_state               # only if defined consistently with Book 2
```

Required invariants:

- A `BUILT_WITH` claim may produce a `BUILD_TIME` dependency but never an inferred
  `HARD_RUNTIME` dependency.
- An `INTEGRATES_WITH` edge may support a candidate optional dependency only when
  function and evidence establish it; B4-P1 still applies.
- A dependency without a mechanism and evidence remains `UNKNOWN`.
- Strength is a descriptor, not a numeric or cross-domain ordinal.

### 5.2 `DependencyPath`

```text
path_id
subject_ref
target_ref
ordered_nodes[]                # A -> B -> C
ordered_relations[]
path_length
derivation_rule
valid_from
valid_to
book2_claim_refs[]
source_snapshot_refs[]
```

A derived transitive dependency must preserve the full path, relation sequence,
length, validity, and claims. It must not silently flatten `A -> B -> C` into
`A DEPENDS_ON C`. Storage versus derivation is deferred to D4-3.

### 5.3 `FailureDomain`

```text
domain_id
domain_type
provider_or_object_refs[]
affected_system_refs[]
mechanism[]                    # technical mechanism required
correlation_basis[]
scope                          # service, function, region, chain, environment, etc.
valid_from
valid_to
book2_claim_refs[]
source_snapshot_refs[]
state = SHARED_FAILURE_DOMAIN | PARTIAL_SHARED_DOMAIN |
        INDEPENDENT | UNKNOWN
```

A category or provider brand alone cannot establish `SHARED_FAILURE_DOMAIN`. The
claim requires a technical mechanism such as shared verification, operator control,
backend, cloud account/region, sequencer process, data source, or custody control.
Ownership and governance are evidence inputs, never substitutes for mechanism.

### 5.4 `RedundancyAssessment`

```text
redundancy_id
function
subject_ref
provider_refs[]
state = DECLARED_REDUNDANCY | DEPLOYED_REDUNDANCY |
        ACTIVE_FAILOVER | MANUAL_FAILOVER |
        INDEPENDENT_REDUNDANCY | CORRELATED_REDUNDANCY |
        UNVERIFIED_REDUNDANCY
activation_path[]
shared_dependencies[]
valid_time
book2_claim_refs[]
```

`INDEPENDENT_REDUNDANCY` is a high-specificity state and must cite the dimensions
that remain independent. Absence of contrary evidence does not justify it.

### 5.5 `SubstitutabilityAssessment`

```text
assessment_id
function
incumbent_ref
candidate_ref
direction
context
valid_from
valid_to
change_class = DROP_IN | CONFIG_CHANGE | CONTRACT_CHANGE |
               PROTOCOL_UPGRADE | MIGRATION_REQUIRED |
               ECONOMICALLY_INFEASIBLE | NO_KNOWN_SUBSTITUTE | UNKNOWN
technical_compatibility[]
governance_requirements[]
migration_requirements[]
state_impact[]
security_impact[]
downtime_risk[]
book2_claim_refs[]
```

There is no universal `A REPLACES B` fact. Assessment is directional, contextual,
function-specific, and time-valid. A substitute for price delivery may not substitute
for attestation, messaging, verification, or settlement security.

## 6. Candidate dependency classes and strength

Book 4 will investigate, but not blindly ratify:

- `HARD_RUNTIME`
- `SOFT_RUNTIME`
- `BUILD_TIME`
- `CONTROL_PLANE`
- `DATA`
- `SECURITY`
- `SETTLEMENT`
- `EXECUTION`
- `MESSAGING`
- `ORACLE`
- `RPC`
- `INDEXING`
- `SEQUENCING`
- `DA`
- `GOVERNANCE`
- `OPERATOR`
- `CUSTODY`
- `LIQUIDITY` as a technical dependency category only, not Book 5 economics
- `OPTIONAL_INTEGRATION`
- `UNKNOWN`

Each class must be investigated as a Book 1 projection, Book 3-local relation,
Book 4-local typed semantic, or attribute on an existing accepted relation. A class
must not become a synonym for `DEPENDS_ON`.

Strength candidates are `REQUIRED`, `PRIMARY`, `FALLBACK`, `OPTIONAL`, `LEGACY`,
`DEPRECATED`, and `UNKNOWN`. The planning default is a typed evidence-backed
descriptor object rather than a bare enum, pending D4-1. These labels describe
architecture and lifecycle state; they do not score investment importance.

## 7. Pairwise edges and hyperedges

### 7.1 Pairwise edge sufficient

Use a pairwise accepted edge when the relationship has stable endpoints, a direct
semantic basis, and no material loss of function, mechanism, or temporal context.
Typed attributes may carry class, strength, scope, and evidence.

Examples to investigate include direct chain messaging, a direct bridge-to-chain
relation, a direct `RUNS_ON`, and a direct Book 3 `USES_DA` relation.

### 7.2 Hyperedge required or preferred

Use the accepted Book 1 hyperedge primitive when a claim depends on a structured
set of participants and roles that pairwise flattening would misstate, including:

- protocol + specific feed + chain deployment + operator set + fallback feed;
- sequencer + DA + settlement + bridge + RPC exposure as distinct relations;
- IBC chain/client/connection/channel/relayer/destination chain route;
- bridge source contract + verifier/guardian + message layer + destination
  contract + destination chain;
- multi-provider redundancy and the shared upstream that correlates it.

A hyperedge preserves the accepted primitive; it does not justify duplicating it
into a Book 4-only graph or automatically creating nodes or edges.

## 8. Bloc 4A — Oracle and data infrastructure

### 8.1 Scope

Plan family-native representation for Chainlink, Pyth, RedStone, API3, and future
material oracle/data systems without asserting current coverage.

Native concepts include:

- oracle network;
- data publisher;
- data source;
- feed and feed family;
- consumer;
- delivery layer and delivery mechanism;
- update and aggregation mechanism;
- chain deployment;
- cross-chain delivery;
- proof or attestation mechanism;
- fallback source;
- token role;
- operator/entity;
- failure domain.

Candidate role distinctions include `ORACLE_NETWORK`, `DATA_SOURCE`, `FEED`,
`PRICE_FEED`, `ATTESTATION_SERVICE`, `DELIVERY_LAYER`, `AUTOMATION_SERVICE`,
and `MESSAGING_SERVICE`. Oracle functions are not flattened into `ORACLE_FOR`.

### 8.2 Questions and acceptance tests

- Is the consumer dependent on a specific feed, or only integrated with a service?
- Is the oracle primary, fallback, optional, legacy, deprecated, or unknown?
- Which function and chain deployment does the relation cover?
- Can a feed be replaced without protocol redesign, and under what conditions?
- Do multiple feeds have independent publishers, upstreams, delivery paths, and
  aggregation mechanisms?
- Is a token economically relevant to service operation, without confusing token
  identity with role identity?
- Is delivery or fallback chain-specific?
- What mechanism causes a failure to propagate across feeds or providers?

## 9. Bloc 4B — Interoperability, messaging, and bridges

### 9.1 Scope and family distinctions

Plan distinct representations for IBC, CCIP, LayerZero, Wormhole, Axelar,
canonical rollup bridges, and major third-party bridges. Do not normalize them all
to a generic bridge.

Candidate roles include message transport, asset bridge, canonical bridge,
light-client verification, validator/guardian verification, oracle-assisted
verification, lock/mint, burn/mint, liquidity bridge, intent-based transfer,
chain-native interoperability, relayer layer, endpoint, channel, and route.

Preserve accepted Book 1 semantics where faithful:

- `MESSAGES_TO` — a messaging layer to a chain;
- `BRIDGES_TO` — a bridge to a served chain;
- `ROUTED_THROUGH` — a capital-route capability via an interop/bridge system,
  subject to the Book 5 boundary.

Audit only; do not automatically add `VERIFIED_BY`, `RELAYED_BY`, `USES_ENDPOINT`,
`USES_RELAYER`, `TRANSPORTS_FOR`, or `ROUTE_DEPENDS_ON`.

### 9.2 Questions and acceptance tests

- Does the system transport messages, verify state, move assets, or do several?
- Which verifier model and security assumptions apply?
- Are relayers part of the trust/availability path, merely operational actors, or
  permissionlessly interchangeable?
- Is the bridge canonical for a chain or a third-party route?
- Does a route require a client, connection, channel, endpoint, liquidity, or
  destination contract that a pairwise edge would hide?
- Does the route establish settlement? It must not.
- Which technical route facts belong in Book 4 while capital flow remains in Book 5?

## 10. Bloc 4C — Data availability and modular infrastructure

### 10.1 Scope

Plan Celestia, EigenDA, Avail, Ethereum native DA, and future material DA systems.
Book 3 architecture-level `USES_DA` remains authoritative for its accepted scope.

Book 4 must be able to represent DA provider, consumer, blob/data publication,
sampling/availability mechanism, retrieval dependency, sequencer interaction,
settlement interaction, security dependency, fallback DA, and provider migration.

`USES_DA`, `SETTLES_TO`, `SECURED_BY`, and `RUNS_ON` remain separate. DA
consumption does not automatically establish settlement, security equivalence, or
execution-host equivalence.

### 10.2 Questions and acceptance tests

- What exact publication and retrieval path is used?
- Is DA required for liveness, safety, state recovery, or only an optional path?
- Which sampling/availability proof and trust assumptions apply?
- What happens when the primary DA is unavailable?
- Can fallback DA operate under the existing protocol, and what evidence proves it?
- What technical and governance changes are required to migrate providers?

## 11. Bloc 4D — RPC, indexing, and developer infrastructure

### 11.1 Scope

Plan providers, nodes, indexers, data APIs, SDKs, frameworks, wallets where
infrastructural, explorers, and developer tooling. Candidate examples include
Alchemy, Infura, QuickNode, The Graph, Subsquid, Helius, Tenderly, Foundry,
Hardhat, Cosmos SDK, OP Stack, Arbitrum Orbit, Substrate, Move tooling, and Solana
tooling. Inclusion is a schema stress test, not a current-fact claim.

Mandatory distinctions:

- runtime dependency;
- soft runtime dependency;
- build-time dependency;
- developer tooling;
- operational provider;
- optional tool;
- hosted service.

A protocol built with an SDK is not operationally dependent on that SDK at runtime.
RPC availability, indexer freshness, and consensus execution are distinct.

### 11.2 Questions and acceptance tests

- Is the service required for transaction submission, reads, state reconstruction,
  indexing, monitoring, development, or only optional convenience?
- Is the dependency hard, degraded-mode, failover-capable, or unknown?
- Do multiple RPC brands terminate on shared cloud, backend, operator, or upstream?
- Is an indexer required for protocol execution or only for a product/interface?
- Does SDK usage stop at build time or embed a runtime contract dependency?
- Which service boundaries remain independent under failure?

## 12. Bloc 4E — Dependency centrality, failure, redundancy, and substitution

This is the central planning bloc. It applies dependency classes and strength only
when function, mechanism, directness, valid time, and Book 2 evidence are explicit.

It must distinguish:

- direct from path-derived transitive dependencies;
- a dependency relation from a correlated failure mechanism;
- declared, deployed, active, manual, independent, correlated, and unverified
  redundancy;
- directional and contextual substitutability from universal replacement;
- provider/operator identity from failure-domain identity;
- architecture dependency from investment importance.

The central output is a queryable planning model in a future authorized
implementation, not an “everything depends on everything” graph.

## 13. Book 2 evidence contract

Every Book 4 dependency claim must bind to Book 2 provenance, snapshot identity,
retrieval time, and claim scope. Candidate evidence families include:

- **Oracle consumption:** deployed configuration, consuming contracts, official
  integration documentation tied to a version, and observed chain state.
- **Bridge route:** deployed contracts, channel/client/connection state where
  applicable, route configuration, endpoint and verifier configuration.
- **DA usage:** deployed rollup configuration, batch/blob publication evidence, and
  versioned official architecture documentation.
- **RPC operational dependency:** application or operator configuration where
  observable, deployment manifests, fallback behavior, operator documentation.
- **SDK/build dependency:** repository manifest, lockfile, source import, and build
  configuration.
- **Failure domain:** provider, operator, verifier, backend, cloud, process, or
  custody mechanism evidence.
- **Redundancy:** deployed configuration plus activation and failover behavior.
- **Substitutability:** compatibility evidence plus deployment, migration, state,
  governance, security, and downtime constraints.

Marketing partnership, logo placement, social-post claims, and shared ecosystem
branding are not sufficient canonical evidence. Unknown remains unknown when the
available evidence cannot distinguish alternatives.

## 14. Book 4 / Book 5 boundary

Book 4 owns technical dependencies, infrastructure relationships, service
consumption, failure domains, redundancy, substitutability, and protocol connectivity.

Book 5 owns capital routing economics, liquidity, collateral, stablecoin supply,
credit, staking/yield, derivatives, economic flow, value locked, and capital
concentration.

Examples:

- “USDC uses a bridge” is a Book 4 technical route/dependency claim; the amount of
  USDC routed through it is Book 5.
- “A DEX depends on an oracle” is Book 4; DEX liquidity depth is Book 5.
- A Book 4 route may name a technical liquidity bridge, but must not measure or rank
  its capital role.
- `LIQUIDITY`, if retained as a technical dependency class, must not become a
  capital-plumbing or investment-importance score.

Any artifact that cannot state this boundary without absorbing Book 5 economics is
out of scope.

## 15. Planning packet deliverables

1. This plan.
2. `CSIA_BOOK_4_RELATIONSHIP_SUPPORT_MATRIX_v0.1.md`
3. `CSIA_BOOK_4_PROTOCOL_ROLE_MODEL_v0.1.md`
4. `CSIA_BOOK_4_INFRASTRUCTURE_PILOT_MATRIX_v0.1.md`
5. `CSIA_BOOK_4_DEPENDENCY_ADVERSARIAL_REVIEW_v0.1.md`
6. `CSIA_BOOK_4_FAILURE_DOMAIN_STRESS_MATRIX_v0.1.md`
7. `CSIA_BOOK_4_SUBSTITUTABILITY_STRESS_MATRIX_v0.1.md`
8. `CSIA_BOOK_4_DEPENDENCY_EVIDENCE_MATRIX_v0.1.md`
9. `CSIA_BOOK_4_PRE_RATIFICATION_REVIEW_v0.1.md`
10. A Book 4 checkpoint appended to `CSIA_PLANNING_PROGRESS.md`.

The matrices are planning instruments. They must not be misread as a current
deployment or investment atlas.

## 16. Ratification and exit criteria

A later operator may ratify the planning packet only after reviewing structural
failures, required extensions, information gaps, and D4-1 through D4-8. This plan
does not self-ratify any type, field, decision, or implementation.

A pre-ratification review must verify:

- oracle/data systems remain unflattened;
- messaging, bridges, verification, and settlement remain distinct;
- DA remains distinct from settlement and security;
- build-time and runtime dependencies remain distinct;
- strength is not a fake universal score;
- transitive paths retain provenance;
- failure domains require technical mechanisms;
- redundancy does not imply independence;
- substitution is directional, contextual, and time-valid;
- Book 5 remains separate;
- all claims bind through Book 2;
- Books 1–3 remain frozen.

## 17. Open operator decisions D4-1 through D4-8

| ID | Decision | Planning recommendation | Reversibility | Blocking |
|---|---|---|---|---|
| D4-1 | Dependency strength: bare enum or typed evidence-backed descriptor? | Prefer a typed descriptor containing category, scope, mechanism, evidence, and valid time. | High before schema freeze | Non-blocking for planning; blocking for schema ratification |
| D4-2 | Failure domains: first-class objects or hyperedges? | Default to typed first-class objects that may participate in accepted hyperedges; operator must confirm. | High before implementation | Blocking for storage contract |
| D4-3 | Store or derive transitive dependencies? | Derive from ordered paths by default; persist only validated path projections if needed. | High | Non-blocking for planning |
| D4-4 | Store substitution or compute from function-specific compatibility evidence? | Compute/assess by function and time; do not store a universal replacement fact. | High | Non-blocking for planning |
| D4-5 | Extend Book 1 later or retain a Book 4 local typed layer? | Default to local typed records plus faithful projections; amend Books 1–3 only if a proven contract gap is separately authorized. | High | Blocking only for any cross-book amendment |
| D4-6 | Minimum evidence for `HARD_RUNTIME`? | Require named function, deployed/use evidence, failure consequence, directness, valid time, and Book 2 provenance; consensus/operator context must be explicit. | High | Blocking for classification use |
| D4-7 | How to represent correlated redundancy? | Use `CORRELATED_REDUNDANCY` with the shared mechanism and affected functions; never collapse to independent. | High | Non-blocking for planning |
| D4-8 | How do provider/operator identity and failure-domain identity interact? | Keep identity separate; link through typed mechanism and correlation assessments, never equality. | High | Blocking for failure-domain schema |

None of these recommendations is self-ratified.

## 18. Exact next operator action after planning

Review this packet and D4-1 through D4-8, then issue an explicit planning-ratification
decision. Do not authorize Book 4 implementation or live acquisition as a implied
consequence of planning completion.
