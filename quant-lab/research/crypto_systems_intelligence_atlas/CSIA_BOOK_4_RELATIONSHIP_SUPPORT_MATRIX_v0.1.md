# CSIA Book 4 Relationship Support Matrix

- **Version:** v0.1
- **Status:** PLANNING_ONLY — NOT RATIFIED
- **Scope:** audit only; no Book 1, Book 2, or Book 3 mutation

## Method and preservation rule

This matrix compares Book 4 semantic needs with the accepted Book 1 edge vocabulary,
the accepted Book 1 route attributes/hyperedge primitive, and Book 3-local
architecture relations. “Supported” means the existing semantic can faithfully
carry the claim when required attributes and evidence are present. It does not mean
that every deployment or dependency is already present in the graph.

No new edge type is added by this matrix. `BOOK4_TYPED_EXTENSION_CANDIDATE` and
`CONTRACT_AMENDMENT_REQUIRED` are planning classifications, not graph mutations.

## Accepted Book 1 relation support

| Accepted relation | Book 4 use | Classification | Guardrail / required qualification |
|---|---|---|---|
| `RUNS_ON` | execution host, node, or infrastructure | `ATTRIBUTE_ON_EXISTING_EDGE` | Does not establish settlement, security, or ownership. |
| `SETTLES_TO` | settlement layer | `ATTRIBUTE_ON_EXISTING_EDGE` | Never inferred from bridge or RPC use. |
| `SECURED_BY` | explicit security relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Requires security mechanism and evidence. |
| `VALIDATED_BY` | validator/verifier relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Do not equate validation with a generic dependency. |
| `USES_VM` | execution environment | `ATTRIBUTE_ON_EXISTING_EDGE` | Runtime scope must be explicit. |
| `USES_STANDARD` | protocol/standard compatibility | `ATTRIBUTE_ON_EXISTING_EDGE` | Not a service dependency. |
| `BRIDGES_TO` | bridge serves a chain | `ATTRIBUTE_ON_EXISTING_EDGE` | Does not imply settlement or asset movement in every route. |
| `MESSAGES_TO` | messaging layer to chain | `ATTRIBUTE_ON_EXISTING_EDGE` | Does not imply asset bridge. |
| `ORACLE_FOR` | oracle supplies data to consumer | `ATTRIBUTE_ON_EXISTING_EDGE` | Preserve feed, function, chain, and delivery mechanism. |
| `DATA_FROM` | non-oracle data source | `ATTRIBUTE_ON_EXISTING_EDGE` | Oracle consumption must not be flattened here. |
| `ISSUED_ON` | token issuance/deployment context | `ATTRIBUTE_ON_EXISTING_EDGE` | Token role is not infrastructure role. |
| `NATIVE_TO` | native ecosystem/chain identity | `ATTRIBUTE_ON_EXISTING_EDGE` | Not a dependency class by itself. |
| `COLLATERAL_IN` | Book 5 boundary marker | `BOOK1_ALREADY_SUPPORTS` | Capital semantics remain out of Book 4 scope. |
| `LIQUIDITY_ON` | Book 5 boundary marker | `BOOK1_ALREADY_SUPPORTS` | Technical bridge naming is not liquidity analysis. |
| `DEPENDS_ON` | direct operational dependency | `ATTRIBUTE_ON_EXISTING_EDGE` | Direct, function-specific, evidence-backed; never catch-all. |
| `INTEGRATES_WITH` | optional/degraded interface relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Never promote to dependency without evidence. |
| `BUILT_WITH` | implementation/build stack | `ATTRIBUTE_ON_EXISTING_EDGE` | Does not imply runtime dependency. |
| `FORKED_FROM` | lineage | `ATTRIBUTE_ON_EXISTING_EDGE` | Not a current operational dependency. |
| `GOVERNED_BY` | governance relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Governance is not ownership or failure-domain identity. |
| `STAKED_IN` | Book 5/economic relation | `BOOK1_ALREADY_SUPPORTS` | Do not pull staking economics into Book 4. |
| `RESTAKED_IN` | Book 5/economic relation | `BOOK1_ALREADY_SUPPORTS` | Do not use as infrastructure dependency evidence. |
| `ROUTED_THROUGH` | technical route capability | `ATTRIBUTE_ON_EXISTING_EDGE` | Capital flow and volume remain Book 5. |
| `MIGRATED_FROM` | lifecycle transition | `ATTRIBUTE_ON_EXISTING_EDGE` | Migration does not imply substitutability. |
| `MIGRATED_TO` | lifecycle transition | `ATTRIBUTE_ON_EXISTING_EDGE` | Keep valid time and target function explicit. |
| `OWNED_BY` | ownership relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Ownership does not define a failure domain. |
| `OPERATED_BY` | operator relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Operator overlap is evidence input, not proof. |
| `COMPETES_WITH` | competitive relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Not a dependency or redundancy claim. |
| `COMPLEMENTS` | complementary relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Not a substitute relation. |
| `WRAPS` | wrapper relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Preserve underlying service semantics. |
| `REDEEMS_FOR` | asset/redemption semantics | `BOOK1_ALREADY_SUPPORTS` | Economic meaning remains outside Book 4 dependency work. |
| `PRICES` | pricing relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Distinguish price feed role from generic data. |
| `SECURES` | security service relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Requires mechanism; not every shared provider shares security. |
| `HOSTS` | hosted infrastructure | `ATTRIBUTE_ON_EXISTING_EDGE` | Hosting is not consensus or settlement. |
| `HOSTS_ISSUANCE` | issuance hosting | `ATTRIBUTE_ON_EXISTING_EDGE` | Token identity remains separate from service role. |
| `REALIZES` | realization/fulfillment relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Do not infer dependency from realization. |
| `RECEIVED_VIA` | receipt/route relation | `ATTRIBUTE_ON_EXISTING_EDGE` | Preserve route and destination context. |

The accepted Book 1 relationship implementation at the Book 3 acceptance anchor
contains these 35 edge types. The matrix intentionally names them as an audit
surface; it does not alter the enum.

## Book 3-local relation support

| Book 3 relation | Book 4 use | Classification | Guardrail / required qualification |
|---|---|---|---|
| `EXECUTES_WITH` | execution companion/interaction | `BOOK3_ALREADY_SUPPORTS` | Do not relabel as `DEPENDS_ON`; retain Book 3 scope. |
| `USES_DA` | architecture-level DA consumption | `BOOK3_ALREADY_SUPPORTS` | Book 4 may add provider/function/evidence attributes locally. |
| `SEQUENCED_BY` | sequencing relation | `BOOK3_ALREADY_SUPPORTS` | Sequencing does not establish DA, settlement, or RPC dependence. |

Book 3’s accepted projection code explicitly fails closed for unsupported Book 4
semantics and forbids aliasing Book 3-local relations to `DEPENDS_ON`. This matrix
preserves that rule.

## Book 4 semantic classification

| Book 4 semantic need | Preferred representation | Classification | Why |
|---|---|---|---|
| Oracle network, publisher, source, feed, delivery | `ORACLE_FOR` plus typed Book 4 `OracleServiceContext` | `ATTRIBUTE_ON_EXISTING_EDGE` | Existing relation carries consumer/network; local attributes preserve native roles. |
| Oracle attestation versus price feed | typed Book 4 role/context record | `BOOK4_TYPED_EXTENSION_CANDIDATE` | `ORACLE_FOR` alone would flatten function. Candidate only. |
| Message transport to chain | `MESSAGES_TO` | `BOOK1_ALREADY_SUPPORTS` | Direct and semantically distinct from asset bridge. |
| Bridge to served chain | `BRIDGES_TO` | `BOOK1_ALREADY_SUPPORTS` | Preserve bridge-specific verification and route attributes. |
| Canonical bridge | `BRIDGES_TO` plus route/role attributes | `ATTRIBUTE_ON_EXISTING_EDGE` | Canonicality is contextual and time-bound. |
| Light-client/validator/guardian verification | existing validation/security edge or local verification context | `ATTRIBUTE_ON_EXISTING_EDGE` | Mechanism must be explicit; no generic bridge edge explosion. |
| Relayer participation | typed local route/operational context | `BOOK4_TYPED_EXTENSION_CANDIDATE` | `MESSAGES_TO` does not say who relays. |
| Endpoint/client/connection/channel | accepted route attributes or hyperedge | `ATTRIBUTE_ON_EXISTING_EDGE` / `HYPEREDGE_REQUIRED` | Pairwise flattening may lose route structure. |
| Route capability | `ROUTED_THROUGH` | `BOOK1_ALREADY_SUPPORTS` | Book 4 records technical route, not capital volume. |
| DA provider and publication | `USES_DA` plus Book 4 context | `BOOK3_ALREADY_SUPPORTS` / `ATTRIBUTE_ON_EXISTING_EDGE` | Preserve DA, settlement, security, and execution distinctions. |
| Sequencer interaction | `SEQUENCED_BY` plus context | `BOOK3_ALREADY_SUPPORTS` / `ATTRIBUTE_ON_EXISTING_EDGE` | Do not infer a DA relation. |
| RPC provider | `RUNS_ON`, `HOSTS`, or local dependency record | `ATTRIBUTE_ON_EXISTING_EDGE` / `BOOK4_TYPED_EXTENSION_CANDIDATE` | RPC service is not automatically protocol consensus. |
| Indexer/data API | `INTEGRATES_WITH` or local runtime dependency | `ATTRIBUTE_ON_EXISTING_EDGE` / `BOOK4_TYPED_EXTENSION_CANDIDATE` | Indexing can be soft, optional, or product-only. |
| SDK/framework | `BUILT_WITH` plus runtime scope attribute | `ATTRIBUTE_ON_EXISTING_EDGE` | Build-time use is not runtime dependence. |
| Developer tooling | `BUILT_WITH` or local operational/tooling record | `ATTRIBUTE_ON_EXISTING_EDGE` / `BOOK4_TYPED_EXTENSION_CANDIDATE` | Tooling is not protocol infrastructure by default. |
| Direct dependency | `DEPENDS_ON` with function/scope/evidence attributes | `BOOK1_ALREADY_SUPPORTS` | Existing edge is adequate when direct. |
| Transitive dependency | `DependencyPath` projection, not flat edge | `BOOK4_TYPED_EXTENSION_CANDIDATE` | Path provenance is mandatory. |
| Failure domain | `FailureDomain` record linked to mechanisms | `BOOK4_TYPED_EXTENSION_CANDIDATE` / `HYPEREDGE_REQUIRED` | First-class object versus hyperedge is D4-2. |
| Redundancy | `RedundancyAssessment` | `BOOK4_TYPED_EXTENSION_CANDIDATE` | Existing `COMPLEMENTS` or multiple edges do not prove resilience. |
| Substitutability | `SubstitutabilityAssessment` | `BOOK4_TYPED_EXTENSION_CANDIDATE` | Directional and contextual, never universal replacement. |
| Provider/operator identity | `OPERATED_BY`/`OWNED_BY` plus local identity links | `ATTRIBUTE_ON_EXISTING_EDGE` | Identity is not failure-domain equality. |
| Token economic effect | Book 1 token/economic relations, Book 5 boundary | `BOOK1_ALREADY_SUPPORTS` | Never infer service role from token identity. |
| Capital routing economics | out of scope | `CONTRACT_AMENDMENT_REQUIRED` if pulled into Book 4 | Must be handled by Book 5, not silently absorbed. |

## Hyperedge decision rules

Use a pairwise edge when the direct relation is stable and attributes preserve
function and scope. Use an accepted hyperedge when the claim depends on a set of
participants whose roles and ordering matter, especially for oracle deployment
context, rollup infrastructure bundles, and bridge routes. A hyperedge must retain
node/role/relation provenance and must not be a disguised catch-all dependency.

Examples requiring structured preservation:

- protocol → feed X → chain deployment Y → operator set Z → fallback Q;
- rollup → sequencer S → DA D → settlement E → bridge B → RPC P;
- chain A → client/connection/channel → relayer → chain B;
- source chain → source contract → verifier → message layer → destination contract.

## Candidate extension disposition

No candidate is ratified. The relationship audit identifies these extension
candidates for operator review: `VERIFIED_BY`, `RELAYED_BY`, `USES_ENDPOINT`,
`USES_RELAYER`, `TRANSPORTS_FOR`, and `ROUTE_DEPENDS_ON`. Their absence from
Book 1 is not a defect by itself. The preferred default is a typed attribute or
local record on an accepted relation unless the semantic cannot be represented
without losing causality.

## Audit verdict

**PASS_FOR_PLANNING.** Existing Book 1 relations and the Book 1 hyperedge primitive
cover much of the needed vocabulary. Book 3’s three local architecture relations
cover execution, DA, and sequencing. Book 4 needs a local typed dependency layer
for evidence, temporal scope, paths, failure domains, redundancy, and
substitutability, with any future cross-book amendment requiring a separate
operator decision and proof of a contract gap.
