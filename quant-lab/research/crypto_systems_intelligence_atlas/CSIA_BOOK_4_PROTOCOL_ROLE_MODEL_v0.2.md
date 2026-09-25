# CSIA Book 4 Protocol Role Model

- **Version:** v0.2
- **Date:** 2026-09-24
- **Status:** RECONCILED — PLANNING ACCEPTANCE CANDIDATE
- **Preserves:** `CSIA_BOOK_4_PROTOCOL_ROLE_MODEL_v0.1.md`
- **Scope:** Book 4 planning only

## 1. Role doctrine

A system may hold multiple simultaneous roles. Roles are multi-valued,
non-exclusive, temporal, scoped to a function or environment, and evidence-backed.
Role identity is distinct from token identity, provider identity, operator
identity, owner identity, protocol identity, and economic importance.

A role assignment states what service a system provides, for which function and
scope, through which mechanism, during which valid interval, and under which
Book 2 claims. It does not assert that the system is universally responsible for
every action associated with the role.

## 2. Namespaced role lifecycle state

The v0.1 `state = ACTIVE | HISTORICAL | DECLARED | UNKNOWN` is replaced in the
v0.2 canonical contract with the explicitly namespaced `role_state` domain:

```text
role_state = CURRENT | HISTORICAL | DECLARED_ONLY | UNKNOWN
```

This is a **Book 4 role-lifecycle/domain state**, not a Book 2 ClaimState.
In particular:

```text
role_state = DECLARED_ONLY
```

does not mean or replace:

```text
Book 2 ClaimState = DECLARED
```

A role can be `DECLARED_ONLY` while its supporting Book 2 claim is `OBSERVED`,
`CORROBORATED`, `CONTESTED`, or another accepted state; the two dimensions must be
read independently. A Book 2 `DECLARED` claim can support a role record only as a
declared/proposed role, never as deployed current role truth by itself.

## 3. Candidate role record

```text
RoleAssignment
  role_assignment_id
  system_ref
  role_type
  function
  scope
  mechanism
  consumes[]
  provides[]
  valid_from
  valid_to
  role_state = CURRENT | HISTORICAL | DECLARED_ONLY | UNKNOWN
  book2_claim_refs[]
  source_snapshot_refs[]
```

`book2_claim_refs[]` is mandatory for every canonical role assignment. The role
state is not a confidence score, claim state, or replacement for evidence.

## 4. Role families

### Oracle and data

- `ORACLE_NETWORK`
- `DATA_PUBLISHER`
- `DATA_SOURCE`
- `FEED`
- `PRICE_FEED`
- `ATTESTATION_SERVICE`
- `DELIVERY_LAYER`
- `AUTOMATION_SERVICE`
- `MESSAGING_SERVICE`
- `FALLBACK_SOURCE`

These roles are not interchangeable. A network, publisher, source, feed,
attestation, delivery, automation, and fallback function each require scoped
Book 2 evidence.

### Interoperability

- `MESSAGE_TRANSPORT`
- `ASSET_BRIDGE`
- `CANONICAL_BRIDGE`
- `LIGHT_CLIENT_VERIFIER`
- `VALIDATOR_VERIFIER`
- `GUARDIAN_VERIFIER`
- `ORACLE_ASSISTED_VERIFIER`
- `LOCK_MINT`
- `BURN_MINT`
- `LIQUIDITY_BRIDGE`
- `INTENT_BASED_TRANSFER`
- `CHAIN_NATIVE_INTEROPERABILITY`
- `RELAYER_LAYER`
- `ENDPOINT`
- `CHANNEL`
- `ROUTE`

Messaging is not asset bridging; bridging is not settlement; a route is not a
capital-flow measurement.

### Modular infrastructure

- `DA_NETWORK`
- `DA_PROVIDER`
- `BLOB_DATA_PUBLICATION`
- `SAMPLING_AVAILABILITY_MECHANISM`
- `RETRIEVAL_SERVICE`
- `SEQUENCER`
- `SETTLEMENT_LAYER`
- `SECURITY_PROVIDER`
- `FALLBACK_DA`

`USES_DA`, `SETTLES_TO`, `SECURED_BY`, and `RUNS_ON` remain distinct.

### Developer and operational infrastructure

- `RPC_PROVIDER`
- `NODE_INFRASTRUCTURE`
- `INDEXER`
- `DATA_API`
- `SDK`
- `FRAMEWORK`
- `DEVELOPER_TOOL`
- `WALLET_INFRASTRUCTURE`
- `EXPLORER`
- `OPERATIONAL_PROVIDER`
- `HOSTED_SERVICE`

Runtime, soft-runtime, build-time, developer-tooling, optional-tool, and
hosted-service scope must be recorded independently of role lifecycle state.

## 5. Role invariants

1. A system may have zero, one, or many current roles.
2. A role may apply to one chain, route, service, or environment and not another.
3. A historical role remains historical with valid time and Book 2 lineage.
4. A role does not imply ownership, governance control, token utility, or value.
5. A role does not imply direct consumer dependence.
6. Provider, operator, owner, and failure-domain identities remain separate.
7. A fallback role is conditional and states activation conditions.
8. A route role does not claim capital flow or liquidity.
9. `role_state=UNKNOWN` means the role lifecycle property is unknown; it does not
   change any Book 2 claim state.
10. A role assignment with no Book 2 claim refs is not canonical.
11. An `UNKNOWN` Book 2 claim or domain classification cannot be strengthened by
    a role label.
12. Role assignment is not dependency classification; a Book 4 DependencyRecord
    separately states function, scope, strength, and runtime consequence.

## 6. Role examples as planning stress cases

| System | Candidate role set | Required distinction |
|---|---|---|
| Chainlink | oracle network; feed delivery; automation; messaging; proof/reserve infrastructure | Keep network, feed, delivery, automation, attestation, token, and operator roles separate. |
| Pyth | oracle/data network; publisher ecosystem; price feed; delivery | Keep publisher, feed, update, and chain deployment scopes separate. |
| IBC | messaging framework; interoperability protocol; route fabric | Keep client, connection, channel, relayer, and route structure. |
| Celestia | DA network; modular infrastructure; possible settlement-adjacent dependency | DA use does not imply settlement or security. |
| Alchemy | RPC provider; developer API; hosted node infrastructure | RPC service is not protocol consensus. |
| The Graph | indexer; data API; hosted service candidate | Indexing can be soft runtime, product-only, or optional. |
| SDK | build-time component; developer tooling | Build-time use is not runtime dependence. |

These are schema stress cases, not current deployment claims.

## 7. Changelog

- Replaced ambiguous role `state` with namespaced `role_state`.
- Used `CURRENT | HISTORICAL | DECLARED_ONLY | UNKNOWN` for role lifecycle.
- Explicitly separated role lifecycle from Book 2 ClaimState.
- Preserved multi-valued, temporal, non-exclusive, evidence-backed role doctrine.
- Preserved all v0.1 role families and examples.
- Added no Book 2 claim state and no implementation.
