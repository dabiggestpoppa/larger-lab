# CSIA Book 4 — Protocol, Infrastructure, and Dependency Atlas Plan

- **Plan version:** v0.2
- **Date:** 2026-09-24
- **Status:** RECONCILED — READY FOR OPERATOR RATIFICATION
- **Scope:** planning only
- **Book 4 implementation authority:** false
- **Live acquisition authority:** false
- **Book 5:** NOT_STARTED
- **Supersedes:** Book 4 v0.1 only for the epistemic-state correction and D4 decisions
- **Preserves:** all v0.1 artifacts as historical planning records

## 1. Goal and boundary

Book 4 maps systems between chains and applications: infrastructure services,
consumers, direct and transitive dependencies, dependents, shared failure domains,
redundancy, substitutability, and temporal change. Its central problem is
**dependency semantics**, not cataloging.

Book 4 owns technical dependencies, service relationships, routes, failure
mechanisms, redundancy, and function-specific substitutability. Book 5 owns
capital routing, liquidity, collateral, stablecoin supply, credit, staking/yield,
derivatives, economic flow, value locked, and capital concentration.

No Book 4 implementation, live acquisition, RPC, collector, database, graph
database, source-code change, test change, or Books 1–3/Sensor mutation is
authorized by this plan.

## 2. Governing doctrine

The v0.1 B4-P1 through B4-P15 doctrine remains in force, including:

- integration is not dependency;
- dependency is not failure domain;
- failure domain is not ownership;
- shared provider is not shared security;
- messaging is not bridging;
- bridging is not settlement;
- oracle consumption is not generic data integration;
- redundancy is not substitutability;
- multiple providers are not failure independence;
- direct is not transitive dependency;
- multiple infrastructure roles are allowed;
- role identity is not token identity;
- dependency strength is evidence-backed;
- unknown remains unknown;
- Book 4 does not absorb Book 5 capital plumbing.

## 3. Exact Book 2 epistemic inheritance

Book 4 owns no claim-state machine. It inherits the accepted Book 2 ClaimState
contract exactly:

```text
DECLARED
OBSERVED
INFERRED
CORROBORATED
CONTESTED
UNRESOLVED
STALE
REJECTED
SUPERSEDED
```

Every canonical Book 4 fact carries `book2_claim_refs[]`. Book 2 owns claim
promotion, methodology, lineage, contradiction, staleness, rejection, and
supersession. Book 4 reads those states and may add only domain scope and type.

`UNKNOWN` is a Book 4 domain classification value, not a Book 2 ClaimState.
For example:

```text
Book 2 claim state: CORROBORATED
Book 4 dependency strength: UNKNOWN
```

The second dimension does not override the first. A contested, unresolved, stale,
rejected, or superseded Book 2 claim cannot support stronger Book 4 truth.

The v0.1 generic `confidence_state` candidate is removed from the canonical v0.2
contract. Any future convenience field must be a derived, namespaced view of
Book 2 state and never independent authority.

## 4. Canonical Book 4 local records

These are planning contracts for a future authorized implementation.

### 4.1 `DependencyRecord`

```text
dependency_id
subject_ref
object_ref
function
scope
relation_basis
dependency_class
runtime_scope
strength_descriptor
mechanism[]
valid_time
book2_claim_refs[]
source_snapshot_refs[]
```

`direct_or_transitive` is not a flattened transitive authority. Direct records
name their direct relation; transitive dependencies derive from ordered paths.

### 4.2 `DependencyStrengthDescriptor`

```text
descriptor_id
state = REQUIRED | PRIMARY | FALLBACK | OPTIONAL |
        LEGACY | DEPRECATED | UNKNOWN
function
scope
mechanism[]
valid_time
book2_claim_refs[]
```

This is a typed evidence-backed descriptor, not a bare enum and not a numeric
score. It describes architecture, lifecycle, and function—not investment
importance.

### 4.3 `DependencyPath`

```text
path_id
subject_ref
target_ref
ordered_nodes[]
ordered_relations[]
path_length
valid_time
book2_claim_refs[]
source_snapshot_refs[]
```

`A -> B -> C` remains an ordered path. It is not silently stored as canonical
`A DEPENDS_ON C`. Caching or materialization may later be a derived view only.

### 4.4 `FailureDomain`

```text
domain_id
domain_type
provider_refs[]
operator_refs[]
owner_refs[]
protocol_refs[]
affected_system_refs[]
mechanism[]
correlation_scope
valid_time
book2_claim_refs[]
```

A FailureDomain is a first-class Book 4 record, separate from provider, operator,
owner, and protocol identity. An optional Book 1 hyperedge may represent an
inherently multi-party causal mechanism when a record plus links would lose roles
or ordering.

### 4.5 `RedundancyAssessment`

```text
redundancy_id
function
providers[]
activation_mode
shared_upstreams[]
shared_failure_domain_refs[]
independence_dimensions[]
state = CORRELATED_REDUNDANCY | INDEPENDENT_REDUNDANCY |
        UNKNOWN
valid_time
book2_claim_refs[]
```

Correlated redundancy is not inferred from a common brand or category. Independent
redundancy requires positive evidence across material failure dimensions.

### 4.6 `SubstitutabilityAssessment`

```text
assessment_id
function
candidate_ref
incumbent_ref
direction
context
change_class = DROP_IN | CONFIG_CHANGE | CONTRACT_CHANGE |
               PROTOCOL_UPGRADE | MIGRATION_REQUIRED |
               ECONOMICALLY_INFEASIBLE | NO_KNOWN_SUBSTITUTE | UNKNOWN
technical_change[]
governance_requirements[]
migration_requirements[]
state_impact[]
security_impact[]
downtime_risk[]
valid_time
book2_claim_refs[]
```

There is no universal `REPLACES` relation. `A` substituting for `B` does not
imply the reverse.

## 5. Dependency classes

The planning classes remain candidates to be represented with typed context:
`HARD_RUNTIME`, `SOFT_RUNTIME`, `BUILD_TIME`, `CONTROL_PLANE`, `DATA`, `SECURITY`,
`SETTLEMENT`, `EXECUTION`, `MESSAGING`, `ORACLE`, `RPC`, `INDEXING`, `SEQUENCING`,
`DA`, `GOVERNANCE`, `OPERATOR`, `CUSTODY`, `OPTIONAL_INTEGRATION`, and `UNKNOWN`.
A class is not a synonym for dependency and is not an investment score.

## 6. Five Book 4 blocs

### 4A — Oracle and data infrastructure

Represent oracle network, publisher, source, feed, feed family, consumer,
delivery, update, aggregation, chain deployment, attestation, fallback, token
role, operator, and failure domain. Keep price feeds, attestation services,
delivery layers, automation, and messaging distinct. Test dependency strength,
chain scope, source concentration, fallback, and substitutability through Book 2.

### 4B — Interoperability, messaging, and bridges

Represent message transport, asset bridge, canonical bridge, light-client,
validator/guardian, oracle-assisted verification, lock/mint, burn/mint, liquidity
bridge, intent transfer, chain-native interoperability, relayer, endpoint,
channel, and route. Preserve Book 1 `MESSAGES_TO`, `BRIDGES_TO`, and
`ROUTED_THROUGH`. Bridging never implies settlement; IBC never becomes generic
bridge semantics.

### 4C — Data availability and modular infrastructure

Represent DA provider, consumer, publication, sampling/availability, retrieval,
sequencer interaction, settlement interaction, security dependency, fallback DA,
and migration. Keep Book 3 `USES_DA` distinct from `SETTLES_TO`, `SECURED_BY`,
and `RUNS_ON`.

### 4D — RPC, indexing, and developer infrastructure

Represent RPC providers, nodes, indexers, APIs, SDKs, frameworks, developer tools,
explorers, wallets where infrastructural, hosted services, and operational
providers. Distinguish hard runtime, soft runtime, build-time, developer tooling,
optional tool, and hosted service. `BUILT_WITH` is not runtime dependence.

### 4E — Dependency centrality and stress semantics

Apply direct paths, mechanism-based failure domains, redundancy assessments, and
directional substitutability only with function, scope, valid time, and Book 2
provenance. No current deployment facts are acquired by this plan.

## 7. Pairwise versus hyperedge rules

Use an accepted pairwise edge where direct semantics and qualifiers fit. Use the
existing Book 1 hyperedge primitive when participant roles, ordering, or causal
mechanism would be lost by flattening—for example a feed deployment with operator
and fallback, a rollup’s sequencer/DA/settlement/RPC bundle, an IBC route, or a
bridge verifier and message path. Hyperedges do not create automatic dependency
edges or candidate Book 1 amendments.

## 8. Book 2 evidence boundary

Every future canonical Book 4 fact references Book 2 claims. Appropriate evidence
families include deployed configuration, contracts, runtime manifests, protocol
or operator configuration, observed deployed state, versioned technical
specifications, source manifests, and explicit failover or migration evidence.
Marketing, partnership, logo, social-post, and branding-only evidence are
insufficient. Current facts remain unacquired in this session.

## 9. D4 operator decisions

| ID | Decision | Status |
|---|---|---|
| D4-1 | Typed evidence-backed strength descriptor object | RATIFIED / CLOSED |
| D4-2 | First-class FailureDomain with optional hyperedge representation | RATIFIED / CLOSED |
| D4-3 | Derive transitive dependencies from ordered DependencyPath records | RATIFIED / CLOSED |
| D4-4 | Store evidence-backed, directional SubstitutabilityAssessment records | RATIFIED / CLOSED |
| D4-5 | Book 4 local typed layer first; reuse Books 1–3 where faithful | RATIFIED / CLOSED |
| D4-6 | Conservative eight-part HARD_RUNTIME evidence rule | RATIFIED / CLOSED |
| D4-7 | Correlated redundancy references explicit FailureDomains | RATIFIED / CLOSED |
| D4-8 | Provider, operator, owner, and failure-domain identities remain separate | RATIFIED / CLOSED |

## 10. v0.1 → v0.2 changelog

- Reconciled Book 4 evidence states to the exact accepted Book 2 ClaimState set.
- Removed the v0.1 generic `confidence_state` candidate.
- Clarified Book 4 domain `UNKNOWN` versus Book 2 epistemic state.
- Renamed/clarified role lifecycle state as `role_state`, separate from Book 2.
- Recorded D4-1 through D4-8 as ratified and closed.
- Preserved all v0.1 artifacts and all Books 1–3 contracts.
- Added no implementation, acquisition, score, database, or Book 5 scope.

## 11. Next action

Operator ratification is the only next action for this planning pass. A separate
authorization is required before any Book 4 offline implementation.
