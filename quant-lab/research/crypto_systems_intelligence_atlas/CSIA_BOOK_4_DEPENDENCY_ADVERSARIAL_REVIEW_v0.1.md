# CSIA Book 4 Dependency Adversarial Review

- **Version:** v0.1
- **Status:** PLANNING_ONLY — NOT RATIFIED
- **Review question:** can the proposed model fail safely when relation labels are confused?

## Review method

Each case is treated as a hostile input to the planning model. A `PASS` means the
model preserves the distinction and requires evidence. It does not mean the case’s
current architecture has been verified. `UNKNOWN` is a valid and often required
result.

## Required adversarial cases

| # | Attack / test | Expected model behavior | Result |
|---:|---|---|---|
| 1 | `INTEGRATES_WITH` is treated as `DEPENDS_ON`. | Reject the inference. Require a named function, consumption evidence, and failure consequence. Integration may remain optional. | PASS |
| 2 | `DEPENDS_ON` is treated as hard runtime failure. | Retain strength and runtime scope separately. A dependency may be build-time, soft, fallback, or governance/control-plane. | PASS |
| 3 | `BUILT_WITH` is treated as runtime dependency. | Classify as build-time unless runtime evidence independently establishes a dependency. | PASS |
| 4 | `ORACLE_FOR` is treated as single-source oracle dependence. | Preserve feed, function, chain deployment, source, delivery, fallback, and valid time; do not infer single-source from a relation. | PASS |
| 5 | `MESSAGES_TO` is treated as asset bridging. | Keep message transport distinct from lock/mint, burn/mint, liquidity, and asset-transfer roles. | PASS |
| 6 | `BRIDGES_TO` is treated as settlement. | Keep `SETTLES_TO` independent and require explicit settlement evidence. | PASS |
| 7 | `USES_DA` is treated as `SECURED_BY`. | Keep DA publication/retrieval, settlement, security, and execution semantics separate. | PASS |
| 8 | Two providers are treated as independent redundancy. | Require activation path and shared-mechanism checks; otherwise use correlated or unverified redundancy. | PASS |
| 9 | One provider is treated as one identical failure domain. | Keep provider identity separate from failure-domain identity; evaluate function, backend, operator, cloud, and mechanism. | PASS |
| 10 | A transitive dependency is flattened to a direct edge. | Require ordered `A -> B -> C` path, relation sequence, path length, valid time, and claims. | PASS |
| 11 | Substitutability is treated as global replacement. | Require direction, function, context, valid time, technical change, governance, state, and security constraints. | PASS |
| 12 | Canonical and third-party bridges are merged. | Preserve route product, verifier, canonicality, and route scope; do not infer equivalence. | PASS |
| 13 | IBC is normalized to generic bridge semantics. | Preserve IBC client/connection/channel/relayer/route structure and `MESSAGES_TO`, `BRIDGES_TO`, and `ROUTED_THROUGH` distinctions. | PASS |
| 14 | RPC provider dependence is treated as consensus dependence. | Classify service function and runtime scope; do not derive consensus or settlement from an RPC endpoint. | PASS |
| 15 | Shared SDK is treated as shared operational risk. | Treat `BUILT_WITH` as implementation/build evidence until a runtime mechanism is evidenced. | PASS |
| 16 | Token role is treated as infrastructure role. | Keep token identity/economic effects separate from service role and technical dependency. | PASS |
| 17 | Book 5 capital routing is pulled into Book 4. | Keep technical route/dependency in Book 4; route capital, liquidity, collateral, supply, and concentration to Book 5. | PASS |

## Additional adversarial cases

| Attack | Expected behavior | Result |
|---|---|---|
| A system is called a dependency because it is a partner. | Partnership, logo, branding, and social posts are insufficient. Require Book 2 evidence. | PASS |
| A system is called independent because it is decentralized. | Decentralization is not a failure-domain proof; inspect operators, cloud, verifier, code, governance, and upstream. | PASS |
| An unavailable fallback is called active failover. | Require deployed configuration and activation/failover evidence; otherwise `DECLARED_REDUNDANCY` or `UNVERIFIED_REDUNDANCY`. | PASS |
| A provider switch is called a drop-in substitute. | Test contracts, APIs, semantics, state, governance, security, downtime, and migration. | PASS |
| DA is called a settlement layer because data is posted there. | Require independent settlement evidence and preserve `USES_DA` versus `SETTLES_TO`. | PASS |
| A route is called secure because it has a bridge. | Require verifier and mechanism evidence; a bridge label is not a security conclusion. | PASS |
| Unknown evidence is converted into `OPTIONAL`. | Unknown remains unknown; optional requires evidence of a non-required function or fallback behavior. | PASS |
| Same provider brand is used to infer same cloud or operator. | Treat brand as identity input only; verify backend, region, account, and operator mechanism. | PASS |

## Structural-failure review

The planning model must fail closed rather than silently flatten a claim. A proposed
future implementation should reject or quarantine a record when:

- relation direction, function, or scope is missing for a dependency claim;
- directness is asserted without a direct relation or a complete dependency path;
- failure domain lacks a technical mechanism;
- redundancy lacks provider, activation, and valid-time context;
- substitutability is asserted without function and directional context;
- a Book 2 claim reference or source snapshot is absent;
- a Book 5 economic claim enters a Book 4 dependency record;
- a Book 3-local relation is aliased to Book 1 `DEPENDS_ON` without authorization.

These are guardrail conditions, not observed implementation defects. No structural
failure is found in the planning packet because no runtime schema has been changed.

## Required planning responses

- Keep `DependencyRecord` separate from `RoleAssignment`.
- Keep `DependencyPath` provenance mandatory for transitive claims.
- Keep `FailureDomain` mechanism-based and identity-distinct.
- Keep redundancy and substitutability as separate assessments.
- Keep accepted Book 1 edges and Book 3 relations as the first representation
  choice; reserve extensions for proven semantic gaps.
- Keep all current-fact questions marked as information gaps.

## Verdict

**PASS_FOR_PLANNING / NO STRUCTURAL FAILURE IDENTIFIED.** The 17 required attacks
are all rejected by the proposed semantics. The review identifies required evidence
and operator decisions, not permission to implement Book 4 or acquire live data.
