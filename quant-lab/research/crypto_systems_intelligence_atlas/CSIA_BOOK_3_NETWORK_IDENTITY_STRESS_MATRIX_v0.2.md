# CSIA Book 3 — Network Identity Stress Matrix v0.2

**BOOK = 3**
**MATRIX_VERSION = v0.2**
**MODE = PLANNING ONLY**
**STATUS = ACCEPTED FOR BOOK 3 RATIFICATION**
**SUPERSEDES_FOR_RATIFICATION = CSIA_BOOK_3_NETWORK_IDENTITY_STRESS_MATRIX_v0.1.md**
**PRESERVED = v0.1**
**BOOK_1_MUTATION = NONE**
**BOOK_3_IMPLEMENTATION_AUTHORITY = FALSE**
**LIVE_ACQUISITION_AUTHORITY = FALSE**

## 1. Controlling doctrine

**Shared history establishes ancestry. Shared history does not by itself establish
the same current network identity.**

Current identity is assessed through a family-native evidence bundle, including
as applicable: genesis/origin, chain/network ID, namespace, deployment ID,
state-history continuity, consensus continuity, and family-native identifiers.
Every claim remains subject to canonical Book 2 evidence.

## 2. Classification vocabulary

- `SAME_OBJECT`: the same current network identity continues.
- `NEW_OBJECT`: a distinct current network identity.
- `HISTORICAL_CONTINUATION`: history and temporal architecture change remain
  attached to the same current object.
- `FORKED_FROM`: event lineage from a divergent network to its origin/ancestor.
- `MIGRATED_FROM` / `MIGRATED_TO`: non-destructive migration lineage.
- `SUPERSESSION`: explicit historical status; never identity overwrite.
- `SECURITY_RELATIONSHIP_CHANGE`: temporal change to `SECURED_BY` history.
- `UNKNOWN`: evidence does not yet determine identity.
- `CONTESTED`: supported evidence conflicts and remains unresolved.

## 3. Stress matrix

| # | Stress case | Required classification | Evidence and preservation rule |
|---:|---|---|---|
| 1 | Chain is renamed while one canonical network, state history, and deployment continue | `SAME_OBJECT` + `HISTORICAL_CONTINUATION` | Name is a label/version claim, not identity authority; preserve temporal naming history. |
| 2 | Same ticker or name is reused by an unrelated network | `NEW_OBJECT` | Ticker and name are never sufficient; preserve separate origins and histories. |
| 3 | Non-branching protocol upgrade: one canonical network continues with state and deployment continuity and no persistent independent branch | `SAME_OBJECT` + `HISTORICAL_CONTINUATION` | Architecture change is temporal; shared history supports ancestry, while canonical/state/deployment/branch-survival evidence supports current identity. |
| 4 | Persistent fork divergence: separate canonical branches retain independent consensus/state histories and participant authority | `NEW_OBJECT` for each divergent current identity as appropriate | Preserve `FORKED_FROM`, shared ancestry, and pre-fork history for each branch. Do not collapse identity based on shared history. |
| 5 | Temporary or ambiguous split with no evidence that an independent branch persists | `UNKNOWN` | Do not fabricate continuity or new-object status; re-evaluate when canonical, state, consensus, deployment, and branch evidence resolves. |
| 6 | Conflicting canonical evidence about current identity | `UNKNOWN / CONTESTED` | Preserve conflicting claims and evidence; neither branch nor label receives automatic authority. |
| 7 | New-genesis restart | `NEW_OBJECT` by default | Preserve the source as historical/superseded and migration lineage. A family-native continuation exception requires operator review. |
| 8 | Chain/network ID changes during an evidenced migration | Preserve both IDs and typed migration history | Identity follows the full D3-5 evidence bundle, not the ID change alone. |
| 9 | Testnet reset with the same name | `NEW_OBJECT` unless a separately reviewed family-native continuation exception is proven | New genesis/state and deployment discontinuity outweigh reused branding. |
| 10 | State migrates from L1 to L2 | `MIGRATION`; source and destination identities remain distinct | Preserve `MIGRATED_FROM` / `MIGRATED_TO`, valid time, evidence, and source history. |
| 11 | State migrates between deployments of the same operator | Typed migration plus historical objects | Migration does not overwrite source identity; same operator/name is not continuity evidence. |
| 12 | Network changes consensus engine without persistent branch divergence | `SAME_OBJECT` + `HISTORICAL_CONTINUATION` when the full bundle supports continuity | Record temporal consensus transition; architecture change alone is not identity replacement. |
| 13 | Network upgrades VM while preserving one canonical state history | `SAME_OBJECT` + `HISTORICAL_CONTINUATION` when continuity is evidenced | VM change is temporal architecture history. |
| 14 | Parachain leaves shared security | `SECURITY_RELATIONSHIP_CHANGE` | Preserve prior and current `SECURED_BY` intervals; security change is not automatic network replacement. |
| 15 | Modular system adopts a new settlement or security provider | `SECURITY_RELATIONSHIP_CHANGE` or settlement migration as evidenced | Record typed temporal relationship history; do not merge provider, settlement, and execution identities. |
| 16 | Network shuts down and later restarts | `NEW_OBJECT` by default unless D3-2 continuity is independently proven and operator-reviewed | Preserve shutdown, supersession, and restart history. |
| 17 | Network clones another genesis/configuration | `NEW_OBJECT` | Cloned configuration is not shared history; preserve only evidenced migration or supersession lineage. |
| 18 | Bridge representation becomes a native realization | `NEW_REALIZATION` | Preserve canonical economic asset identity, bridge realization, native realization, and temporal lineage. |
| 19 | Wrapped asset changes custodian | `NEW_REALIZATION` or evidenced custody transition | Asset identity remains canonical; realization and custody claims remain temporal and distinct. |

## 4. Binding decision rules

1. Shared history is ancestry evidence, never a sole current-identity proof.
2. Persistent independent canonical branches do not collapse into one object.
3. A non-branching upgrade can preserve identity when canonical, state, deployment,
   and no-persistent-branch conditions are evidenced.
4. Temporary or ambiguous splits remain `UNKNOWN`; conflicts remain `CONTESTED`.
5. New genesis is `NEW_OBJECT` by default. Name, ticker, operator, branding, chain
   ID, namespace, or deployment reuse is insufficient by itself.
6. Genesis is strong but not universally sufficient. No universal single anchor
   exists; D3-5 requires a family-native evidence bundle.
7. Migration, security change, realization change, and upgrade history are typed
   temporal claims. Historical objects are never overwritten.
8. Every identity claim is Book 2 evidence-backed. A planning artifact is not
   runtime evidence.

## 5. Gate result

```text
NETWORK_IDENTITY_MATRIX_VERSION = v0.2
NETWORK_IDENTITY_MATRIX_STATUS = ACCEPTED
STRUCTURAL_FAILURE_COUNT = 0
BLOCKING_OPERATOR_DECISION_COUNT = 0
PERSISTENT_FORK_COLLAPSE = PROHIBITED
NON_BRANCHING_UPGRADE_CONTINUITY = SUPPORTED
NEW_GENESIS_DEFAULT = NEW_OBJECT
NAME_TICKER_IDENTITY_AUTHORITY = NONE
STATE_MIGRATION_IDENTITY_OVERWRITE = PROHIBITED
SHARED_SECURITY_CHANGE_IDENTITY_REPLACEMENT = PROHIBITED
BOOK_1_MUTATION = NONE
BOOK_2_EVIDENCE_BOUNDARY = PASS
BOOK_3_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
```
