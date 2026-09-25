# CSIA Book 4 Dependency Evidence Matrix

- **Version:** v0.1
- **Status:** PLANNING_ONLY — NOT RATIFIED
- **Purpose:** bind every future Book 4 dependency claim to Book 2 provenance

## Evidence invariant

A Book 4 dependency fact is canonical only when it has a scoped Book 2 claim
reference, source snapshot identity where applicable, retrieval/observation time,
and enough evidence to identify the subject, object, function, direction, and
validity. Evidence can establish a bounded claim without establishing a broader
system-wide dependency.

The following are never sufficient alone:

- marketing says “partner” or “integrated”;
- a logo appears on a website;
- a social post claims a relationship;
- two projects share branding or an ecosystem;
- a provider says it is decentralized;
- two providers are listed without deployment or activation evidence;
- a category name implies a shared mechanism.

## Claim-to-evidence matrix

| Book 4 claim | Minimum Book 2 evidence families | Scope qualifiers | Evidence that is insufficient alone | Resulting semantic boundary |
|---|---|---|---|---|
| Oracle consumption | deployed consumer configuration/contracts; official integration documentation tied to version; chain state or feed identity; update/delivery evidence | feed, data type, chain deployment, consumer function, fallback, valid time | Oracle marketing, token price, ecosystem listing, generic `ORACLE_FOR` label | `ORACLE_FOR` plus typed feed context; not generic data integration |
| Oracle publisher/source relation | publisher/source identity; update or attestation mechanism; deployment/configuration evidence | datum, publisher, feed, chain, time | Provider brand or partnership claim | Role assignment and evidence-backed relation |
| Oracle fallback/redundancy | primary and fallback configuration; activation conditions; upstream mapping; failover evidence | function, chain, activation mode, shared upstream | “Multiple feeds” or “multi-oracle” claim | `RedundancyAssessment`, not independence by default |
| Bridge route | deployed source/destination contracts; route configuration; channel/client/connection or endpoint state; verifier configuration | source/destination, asset/function, canonicality, verifier, valid time | Bridge marketing, token listing, route diagram without deployment evidence | `BRIDGES_TO`/`ROUTED_THROUGH` plus route context |
| Message transport | protocol specification plus deployed endpoint/configuration and route state | message type, chain, endpoint, finality, relayer | “Interoperability” or “connected” claim | `MESSAGES_TO`, not `BRIDGES_TO` |
| Relayer participation | relayer implementation/configuration; operator identity; route/endpoint evidence; activation path | route, message, fee, liveness, valid time | Relayer list or permissionless branding | Typed relayer context; no generic `DEPENDS_ON` |
| Light-client/validator/guardian verification | deployed verifier configuration; key/validator/guardian evidence; contract/state or protocol specification | verification function, threshold, chain/route, time | “Secure bridge” or verifier-brand assertion | `VALIDATED_BY`/`SECURED_BY` only with mechanism |
| DA usage | deployed rollup configuration; blob/data publication evidence; official architecture; retrieval path | provider, namespace, chain, safety/liveness consequence, time | Modular-infrastructure branding or “posts to DA” without consumer config | `USES_DA` plus DA function/fallback context |
| DA security relation | proof/availability mechanism, security assumptions, deployment/upgrade evidence | safety/liveness, provider, trust model, time | DA use alone | Separate `SECURED_BY` only with security evidence |
| DA settlement relation | settlement-layer configuration and protocol/rollup evidence | chain, batch finality, dispute/fault path, time | DA publication or bridge route | Separate `SETTLES_TO` |
| Sequencer relation | deployed sequencer configuration; batch/derivation evidence; operator/upgrade governance | chain/rollup, liveness, soft confirmation, time | “Sequenced by” inferred from block production branding | Book 3 `SEQUENCED_BY`; no DA/RPC inference |
| RPC operational dependency | application/operator configuration; deployment manifest; endpoint and failover documentation | chain, method/function, environment, hard/soft/optional scope, time | Provider logo, SDK import, node count | RPC service dependency; not consensus dependency |
| RPC provider hosting | deployment/hosting documentation; backend/operator scope | provider, chain, region, service, time | “Hosted by” marketing | `HOSTS`/`RUNS_ON` with scope, not settlement/security |
| Indexer dependency | consumer configuration; API/query contract; source/index evidence; fallback or freshness behavior | query function, chain, soft/optional/product scope, time | Indexer existence or ecosystem listing | `INTEGRATES_WITH` or soft local dependency |
| SDK build dependency | source manifest; lockfile; import/build config; repository/version evidence | implementation, version, runtime consequence, time | “Built with” logo or framework association | `BUILT_WITH`; build-time unless separately evidenced |
| Developer tooling dependency | repository/build/CI evidence and operator workflow documentation | development, testing, deployment, runtime scope | Tool popularity or partnership | Developer tooling/optional/build-time semantic |
| Failure domain | provider/operator/backend/cloud/process/verifier/custody mechanism evidence; affected configuration | function, component, region, chain, time | Same category, brand, or owner alone | Typed `FailureDomain`; `UNKNOWN` if mechanism absent |
| Redundancy | deployed configuration, provider inventory, activation/failover path, shared-upstream analysis | function, mode, scope, time, shared dependencies | Two-provider count or “active/active” marketing | `RedundancyAssessment`; independent only with evidence |
| Substitutability | technical compatibility; API/contract/spec comparison; deployment and migration/governance constraints | direction, function, context, state, security, downtime, time | “Compatible,” “drop-in,” or competitor claim | `SubstitutabilityAssessment`; no universal replacement |
| Transitive dependency | complete ordered path, relation evidence at each step, valid-time reconciliation, claim refs | subject/target, path length, branch/alternative paths, time | Flattened “depends on” claim | `DependencyPath`; no direct-edge promotion |
| Temporal role/migration | dated configuration, release/deployment snapshot, migration/upgrade record | role/function, old/new provider, effective interval | Current website description | Temporal `RoleAssignment`/migration context |
| Token/infrastructure separation | token identity/economic evidence and service-role evidence separately | token, protocol role, service function, time | Token symbol or token utility alone | No role identity inference from token |

## Evidence-state rules

1. `DECLARED` means a source asserts a relationship but has not supplied sufficient
   deployed or technical evidence.
2. `OBSERVED` means the evidence source was retrieved, with snapshot and time.
3. `VERIFIED` means the evidence supports the exact scoped claim under the Book 2
   contract; it does not mean the relationship is universal or permanent.
4. `CONFLICTED` means sources disagree; retain the conflict and do not strengthen
   the claim.
5. `UNKNOWN` means evidence is absent or insufficient. It is not a synonym for
   false, optional, or independent.

## Planning verdict

**PASS_FOR_PLANNING.** Book 2 can support Book 4 without making marketing,
partnership, or branding into dependency facts. The matrix identifies the evidence
families needed for later authorized acquisition while keeping the current session
planning-only.
