# BLOC 05 — SENSOR-B5-I06E1 PROVIDER-DOCUMENTATION COLLECTION BRIEF

**Checkpoint:** SENSOR-B5-I06 · **Base:** `32a89743656adb638cdaf688b62be505202f1876`
**Status:** DOCUMENTATION INVENTORY ONLY — this brief is not production schema,
not an authorization to create provider rows, and not evidence of anything.

## 1. Purpose (I06E1 sections 00 M3/M4, 07)

The accepted I05 provider time-semantics registry admits **zero** real
provider rows (proved by RS-13 and the scope row
`provider_registry_admits_zero_real_rows`). Real-provider availability
derivations therefore remain blocked, by design, until contemporaneous
documentation exists. This brief identifies the exact evidence that must be
collected — provider by provider — before any real-provider row can even be
proposed for operator review. Missing latency documentation must never
become an assumed zero-delay policy (RS-14).

## 2. Required fields per provider document

Every candidate provider/venue entry, once evidenced, must be describable by
exactly these fields. Each field is either **SOURCE** (copied from a citable
provider document) or **INTERPRETATION** (our proposed reading, requiring
operator approval). Source evidence and proposed interpretation must never be
merged in one field.

```text
PROVIDER_ID
MARKET_OR_VENUE
OBSERVATION_FAMILY
TIMESTAMP_SEMANTICS
PUBLICATION_MODEL
LATENCY_EVIDENCE_SOURCE
AVAILABILITY_DERIVATION_RULE
SOURCE_VERSION
VALIDITY_WINDOW
KNOWLEDGE_WINDOW
REPLAY_RESTRICTIONS
```

Field classes:

| Field | Class | Notes |
|---|---|---|
| PROVIDER_ID | SOURCE | canonical provider identifier as used by the ingestion layer |
| MARKET_OR_VENUE | SOURCE | exact venue/market the document governs |
| OBSERVATION_FAMILY | SOURCE | which sensor families the semantics apply to (trades, liquidations, OI, funding, book, positioning) |
| TIMESTAMP_SEMANTICS | SOURCE + INTERPRETATION | the document's literal statement of what each timestamp field means; interpretation maps it onto the frozen timestamp-role vocabulary |
| PUBLICATION_MODEL | SOURCE + INTERPRETATION | snapshot vs stream, revision/correction policy as documented; interpretation maps onto the frozen availability-basis ladder rungs only |
| LATENCY_EVIDENCE_SOURCE | SOURCE | the document/section stating publication delay — or an explicit "no latency statement found" |
| AVAILABILITY_DERIVATION_RULE | INTERPRETATION | the proposed ladder rung and derivation; operator approval required |
| SOURCE_VERSION | SOURCE | document version, retrieval date, URL/archive reference |
| VALIDITY_WINDOW | SOURCE | when the documentation was in force |
| KNOWLEDGE_WINDOW | SOURCE | when the documentation was publicly knowable (must not be conflated with VALIDITY_WINDOW) |
| REPLAY_RESTRICTIONS | SOURCE + INTERPRETATION | licensing/redistribution constraints on replaying this data |

## 3. Inventory status at I06E1

| PROVIDER_ID | MARKET_OR_VENUE | OBSERVATION_FAMILY | TIMESTAMP_SEMANTICS | PUBLICATION_MODEL | LATENCY_EVIDENCE_SOURCE | AVAILABILITY_DERIVATION_RULE | SOURCE_VERSION | VALIDITY_WINDOW | KNOWLEDGE_WINDOW | REPLAY_RESTRICTIONS |
|---|---|---|---|---|---|---|---|---|---|---|
| _(none collected)_ | — | — | — | — | — | — | — | — | — | — |

**Zero rows.** No real-provider latency values or timestamp-semantics
mappings are authorized at this checkpoint, so the inventory ships empty.

## 4. Admission rules for future rows (proposed, not executed)

1. Every SOURCE field must cite a retrievable provider document; anything
   uncited stays empty — absence is honest, invention is forbidden.
2. A row with "no latency statement found" cannot produce a
   latency-adjusted availability time; it can at most support a rung whose
   derivation does not depend on latency, if the operator approves.
3. No row becomes production schema by collection alone: new registry rows
   require an operator-authorized checkpoint (Option C confidence review is
   the designated trigger point for reopening methodology).
4. Synthetic fixtures used in I06 evidence (e.g. `SYNTHETIC_FIXTURE_ONLY`)
   must never appear in this inventory; they establish logical correctness
   only and carry no provider authority.

*End of I06E1 provider-documentation collection brief.*
