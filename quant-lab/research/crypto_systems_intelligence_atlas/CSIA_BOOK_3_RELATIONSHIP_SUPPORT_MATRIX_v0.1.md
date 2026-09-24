# CSIA Book 3 — Relationship Support Matrix v0.1

**BOOK = 3**
**MATRIX_VERSION = v0.1**
**MODE = PLANNING ONLY**
**AUDIT_SOURCE = ACCEPTED BOOK 1 EdgeType**
**BOOK_1_MUTATION = NONE**
**BOOK_3_IMPLEMENTATION_AUTHORITY = FALSE**

## 1. Audit rule

Book 3 reuses an accepted Book 1 edge when the subject, object, direction, and
meaning are faithful. A relation used faithfully is not a Book 1 gap. A missing
Book 3-native architecture relation remains typed and local; it is not silently
aliased to `DEPENDS_ON` or weakened to fit Book 1.

## 2. Support matrix

| Book 3 semantic | Book 1 edge | classification | projection allowed | Book 3 local relation needed | future amendment candidate | notes |
|---|---|---|---|---|---|---|
| `RUNS_ON` | `RUNS_ON` | `BOOK1_ALREADY_SUPPORTS` | YES — faithful direction and domain/range only | NO | NO | Protocol/VM/application execution on the named chain runtime; tokens do not use this edge. |
| `USES_VM` | `USES_VM` | `BOOK1_ALREADY_SUPPORTS` | YES — chain to VM | NO | NO | Use only where a VM object is faithful; native non-VM execution may remain a typed family value without this edge. |
| `SETTLES_TO` | `SETTLES_TO` | `BOOK1_ALREADY_SUPPORTS` | YES — dependent system to settlement chain | NO | NO | Settlement is not automatically security, bridge connectivity, or identity. |
| `SECURED_BY` | `SECURED_BY` | `BOOK1_ALREADY_SUPPORTS` | YES — preserve accepted mechanism semantics | NO | NO | Distinct from `RUNS_ON`, `SETTLES_TO`, `USES_DA`, and `MESSAGES_TO`. |
| `BRIDGES_TO` | `BRIDGES_TO` | `BOOK1_ALREADY_SUPPORTS` | YES — bridge object to served chain | NO | NO | Preserve route/hyperedge semantics; do not substitute for settlement. |
| `MESSAGES_TO` | `MESSAGES_TO` | `BOOK1_ALREADY_SUPPORTS` | YES — messaging layer to chain | NO | NO | Messaging does not imply shared security, settlement, or network identity. |
| `FORKED_FROM` | `FORKED_FROM` | `BOOK1_ALREADY_SUPPORTS` | YES — divergent network to origin/ancestor | NO | NO | Persistent divergence requires a new current object plus this event lineage; shared history alone is insufficient for same identity. |
| `MIGRATED_FROM` | `MIGRATED_FROM` | `BOOK1_ALREADY_SUPPORTS` | YES — destination/dependent object from source | NO | NO | Preserve source identity and valid-time history. |
| `MIGRATED_TO` | `MIGRATED_TO` | `BOOK1_ALREADY_SUPPORTS` | YES — source/object to destination | NO | NO | Pair with source history; never overwrite source into destination. |
| `REALIZES` | `REALIZES` | `BOOK1_ALREADY_SUPPORTS` | YES — realization to canonical economic asset | NO | NO | Preserve accepted Book 1 domain/range and realization lifecycle. |
| `EXECUTES_WITH` | NONE | `BOOK3_RELATION_EXTENSION_CANDIDATE` | NO | YES | YES — only under a separately authorized future amendment process | Typed execution-component relation; never alias to `DEPENDS_ON` and do not mutate Book 1 here. |
| `USES_DA` | NONE | `BOOK3_RELATION_EXTENSION_CANDIDATE` | NO | YES | YES — only under a separately authorized future amendment process | Typed system-to-DA service/domain relation; distinct from settlement, execution, and security. |
| `SEQUENCED_BY` | NONE | `BOOK3_RELATION_EXTENSION_CANDIDATE` | NO | YES | YES — only under a separately authorized future amendment process | Typed ordering/sequencer-domain relation; never alias to `DEPENDS_ON` and do not mutate Book 1 here. |

## 3. Classification totals

```text
BOOK1_ALREADY_SUPPORTS_COUNT = 10
BOOK3_RELATION_EXTENSION_CANDIDATE_COUNT = 3
SILENT_RELATIONSHIP_ALIASES = 0
BOOK_1_CONTRACT_AMENDMENT_COUNT = 0
BOOK_1_MUTATION = NONE
```

## 4. Gate result

```text
RELATIONSHIP_SUPPORT_MATRIX_VERSION = v0.1
RELATIONSHIP_SUPPORT_MATRIX_STATUS = ACCEPTED
BOOK1_ALREADY_SUPPORTS = RUNS_ON, USES_VM, SETTLES_TO, SECURED_BY,
                          BRIDGES_TO, MESSAGES_TO, FORKED_FROM,
                          MIGRATED_FROM, MIGRATED_TO, REALIZES
BOOK3_RELATION_EXTENSION_CANDIDATE = EXECUTES_WITH, USES_DA, SEQUENCED_BY
BOOK_1_FROZEN = TRUE
BOOK_1_MUTATION = NONE
BOOK_3_IMPLEMENTATION_AUTHORITY = FALSE
```
