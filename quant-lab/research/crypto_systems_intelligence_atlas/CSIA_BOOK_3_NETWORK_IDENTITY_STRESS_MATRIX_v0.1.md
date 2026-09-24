# CSIA Book 3 — Network Identity Stress Matrix v0.1

**MODE = PLANNING ONLY**
**PURPOSE = expose identity ambiguity without inventing a universal chain-ID rule**

## Classification vocabulary

- `SAME_OBJECT`: same network identity and continuing history.
- `NEW_OBJECT`: distinct network identity.
- `NEW_REALIZATION`: same economic or protocol object represented by a new
  chain-local form.
- `MIGRATION`: explicit state or settlement migration relationship.
- `SUPERSESSION`: prior object remains historical but no longer current.
- `HISTORICAL_CONTINUATION`: historical relationship is preserved while current
  authority is explicitly changed.
- `OPERATOR_DECISION`: evidence is insufficient for a final governance choice.

| # | Stress case | Provisional planning result | Required evidence and decision boundary |
|---:|---|---|---|
| 1 | Chain renames but genesis unchanged | **HISTORICAL_CONTINUATION** | Same genesis/config and state history support continuation; rename is a label/version claim, not automatically a new object. Final naming authority remains operator-governed. |
| 2 | Same ticker, unrelated network | **NEW_OBJECT** | Different genesis, namespace, validators, and state history; ticker is never sufficient identity evidence. |
| 3 | Chain ID changes during migration | **OPERATOR_DECISION: D3-5** | Preserve prior chain ID, new chain ID, and migration edge; final same-object/new-object decision depends on state and settlement continuity. |
| 4 | Hard fork with shared history | **HISTORICAL_CONTINUATION** | Fork edge, shared genesis/history, and rule divergence must be explicit; fork does not erase ancestry. |
| 5 | Testnet reset with same name | **NEW_OBJECT** unless continuity is proven | New genesis/state and separate deployment identity require a new object; a reused name is only a label. |
| 6 | Mainnet restarts from new genesis | **NEW_OBJECT + MIGRATION** | Preserve old network as historical/superseded and link restart to migration; operator decision D3-2 applies to restart semantics. |
| 7 | L1 migrates state to L2 | **MIGRATION / NEW_REALIZATION** | Preserve L1 historical object and L2 identity; state migration does not make L2 the same network. |
| 8 | Appchain changes consensus engine | **HISTORICAL_CONTINUATION** | Record temporal consensus transition; identity remains only if namespace, genesis/state continuity, and operator evidence support it. |
| 9 | Chain upgrades VM but preserves state | **HISTORICAL_CONTINUATION** | VM implementation changes are architecture history, not automatic identity replacement. |
| 10 | Parachain leaves shared security | **HISTORICAL_CONTINUATION + SECURITY_MIGRATION** | Preserve relay history and record security relationship change; do not rewrite prior `SECURED_BY`. |
| 11 | Cosmos chain adopts replicated security | **SECURITY_RELATIONSHIP_CHANGE** | Consensus/security change is temporal architecture history; identity remains distinct from security provider. |
| 12 | Network shuts down and later restarts | **OPERATOR_DECISION: D3-2** | Determine whether restart is continuation, new object, or migration based on genesis, state, namespace, and operator evidence. |
| 13 | Chain clones another genesis/config | **NEW_OBJECT** | Cloned configuration is not shared history; preserve `CLONES_FROM` or `MIGRATION_FROM` relationship if evidenced. |
| 14 | Bridge representation becomes native asset | **NEW_REALIZATION** | Preserve economic asset identity and historical bridge realization; native realization is a new explicit binding. |
| 15 | Wrapped asset changes custodian | **NEW_REALIZATION** | Asset identity remains canonical; custodian and chain-local realization change as separate historical claims. |

## Decision rules proposed for operator ratification

1. A genesis/config identity anchor is necessary but not always sufficient.
2. A name or ticker alone is never sufficient.
3. Shared history can support `HISTORICAL_CONTINUATION`; it does not erase a fork or
   migration edge.
4. A new chain ID, namespace, genesis, or deployment may indicate a new object but
   requires state and operator evidence.
5. Settlement migration, security migration, and realization migration are typed
   relationships, not identity rewrites.
6. `UNKNOWN` remains explicit when evidence cannot distinguish continuation from a
   new object.

## Gate result

```text
NETWORK_IDENTITY_STRESS_MATRIX = COMPLETE_FOR_REVIEW
STRUCTURAL_FAILURE_COUNT = 0
GOVERNANCE_SENSITIVE_DECISIONS = D3-1, D3-2, D3-5
BOOK_1_MUTATION = NONE
```
