# CSIA Book 4 Dependency Evidence Matrix

- **Version:** v0.2
- **Date:** 2026-09-24
- **Status:** RECONCILED — PLANNING ACCEPTANCE CANDIDATE
- **Preserves:** `CSIA_BOOK_4_DEPENDENCY_EVIDENCE_MATRIX_v0.1.md`
- **Scope:** Book 4 planning only

## 1. Epistemic ownership

Book 4 does not own claim state. It inherits the exact accepted Book 2 contract:

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

Every canonical Book 4 fact references canonical Book 2 claims through
`book2_claim_refs[]`. Book 4 may scope, type, combine, or reject a domain record,
but it cannot promote, demote, rename, or transition a Book 2 claim.

## 2. Book 2 state handling in Book 4

| Book 2 ClaimState | Book 4 handling |
|---|---|
| `DECLARED` | May support a declared or proposed relationship only; insufficient for deployed dependency truth. |
| `OBSERVED` | Supports the exact observed scope only; do not generalize to universal or permanent dependence. |
| `INFERRED` | May support a bounded derived record only when methodology, parent claims, and terminating lineage are retained. |
| `CORROBORATED` | May support stronger structural truth only when all Book 2 promotion rules and Book 4 scope requirements are satisfied. |
| `CONTESTED` | Do not strengthen Book 4 dependency truth; preserve the dispute and competing claims. |
| `UNRESOLVED` | Fail closed for canonical Book 4 truth. |
| `STALE` | Cannot establish current dependency truth; preserve historical context only. |
| `REJECTED` | Cannot support Book 4 truth. |
| `SUPERSEDED` | Historical only; not current truth. |

No alternate Book 4 claim state is introduced. `UNKNOWN` is reserved for a Book 4
**domain classification** such as dependency strength, role state, failure-domain
classification, or redundancy state. It is not a Book 2 ClaimState.

Example:

```text
Book 2 claim state: CORROBORATED
Book 4 dependency strength: UNKNOWN
```

The domain classification does not upgrade or downgrade the Book 2 claim. A Book
2 claim in `CONTESTED`, `UNRESOLVED`, `STALE`, `REJECTED`, or `SUPERSEDED` state
cannot be used to strengthen Book 4 truth regardless of a domain value.

## 3. Claim-to-evidence contract

| Book 4 claim | Canonical Book 2 evidence required | Scope and lineage requirements |
|---|---|---|
| Oracle consumption | Consumer contract/config, feed/deployment identity, versioned technical integration evidence, and chain state where applicable | Feed, function, chain deployment, update/delivery mechanism, and valid time |
| Publisher/source/update relation | Publisher/source identity and update, signing, or attestation mechanism | Preserve source lineage, feed, chain, and methodology |
| Bridge route | Source/destination contracts, route config, endpoint/channel/verifier state | Source, destination, asset/function, canonicality, verifier, and time |
| Message transport | Protocol specification plus deployed endpoint/configuration | Message type, chain, endpoint, finality, and relayer scope |
| Relayer participation | Relayer implementation/config, operator, route, and activation evidence | Route, message, liveness, operator, and time |
| DA usage | Rollup config, blob/data publication, retrieval, and official technical architecture | Provider, namespace, function, safety/liveness consequence, and time |
| DA security or settlement | Separate mechanism and settlement/fault-path evidence | Must not be inferred from `USES_DA` or bridge evidence |
| Sequencer relation | Sequencer config, batch/derivation, and operator/upgrade evidence | Rollup/chain, liveness, confirmation, and time |
| RPC operational dependence | Application/operator config, deployment manifest, endpoint and failover evidence | Chain, method/function, environment, hard/soft/optional scope |
| Indexer dependence | Consumer config, API/query contract, source/index and freshness/fallback evidence | Query function, chain, product/runtime scope, and time |
| SDK/build dependence | Source manifest, lockfile, import/build config, and version evidence | Implementation, build/runtime consequence, and time |
| Failure domain | Provider/operator/backend/cloud/process/verifier/custody mechanism and affected config | Function, component, region, chain, correlation, and time |
| Redundancy | Provider inventory, activation/failover path, shared upstream and mechanism evidence | Function, mode, shared failure domains, independence dimensions, and time |
| Substitutability | Compatibility plus deployment, migration, governance, state, security, and downtime constraints | Direction, function, context, incumbent/candidate, and time |
| Transitive dependence | Complete ordered path with claim refs at every step | Preserve path nodes, relations, length, branch alternatives, and time |
| Role assignment | Role-specific service, configuration, deployment, and operator evidence | Role lifecycle state, function, scope, mechanism, and time |

## 4. Evidence that is insufficient alone

The following cannot establish a canonical Book 4 dependency:

- a partnership or integration announcement;
- a provider logo, ecosystem listing, or social post;
- a token symbol, token utility, or economic incentive;
- a category or provider brand;
- a provider’s “decentralized,” “secure,” or “critical infrastructure” description;
- two listed providers without deployment and activation evidence;
- a declared fallback without activation behavior;
- shared ownership or governance without technical mechanism.

These sources may support a Book 2 `DECLARED` claim, but not stronger deployed
truth by themselves.

## 5. Domain-state namespace

The following are Book 4 domain classifications and are intentionally separate
from Book 2 ClaimState:

- `DependencyStrengthDescriptor.state`:
  `REQUIRED | PRIMARY | FALLBACK | OPTIONAL | LEGACY | DEPRECATED | UNKNOWN`
- `role_state`:
  `CURRENT | HISTORICAL | DECLARED_ONLY | UNKNOWN`
- `FailureDomain.state`:
  `SHARED_FAILURE_DOMAIN | PARTIAL_SHARED_DOMAIN | INDEPENDENT | UNKNOWN`
- `RedundancyAssessment.state`:
  `CORRELATED_REDUNDANCY | INDEPENDENT_REDUNDANCY | UNKNOWN`
- `SubstitutabilityAssessment.change_class`:
  `DROP_IN | CONFIG_CHANGE | CONTRACT_CHANGE | PROTOCOL_UPGRADE |
  MIGRATION_REQUIRED | ECONOMICALLY_INFEASIBLE | NO_KNOWN_SUBSTITUTE | UNKNOWN`

None is a claim state, confidence scalar, or replacement for `book2_claim_refs[]`.

## 6. Promotion and fail-closed rules

1. A Book 4 record with no Book 2 claim refs is not canonical.
2. A `DECLARED` claim cannot support deployed dependency truth.
3. An `OBSERVED` claim remains bounded to what was observed.
4. An `INFERRED` claim retains methodology and parent lineage.
5. A `CORROBORATED` claim may support structural truth only when the Book 4
   function, scope, mechanism, valid time, and minimum evidence requirements pass.
6. `CONTESTED`, `UNRESOLVED`, `STALE`, `REJECTED`, and `SUPERSEDED` cannot
   strengthen current Book 4 truth.
7. Domain `UNKNOWN` never changes the underlying Book 2 state.
8. A future implementation may derive a view of Book 2 state, but it cannot own
   an independent confidence state.

## 7. Verdict

**RECONCILED / ACCEPTED FOR BOOK 4 RATIFICATION.** Book 4 v0.2 uses the exact Book 2
epistemic contract, binds canonical facts to Book 2 claims, and keeps domain
classification values explicitly separate. No Book 2 amendment is required.
