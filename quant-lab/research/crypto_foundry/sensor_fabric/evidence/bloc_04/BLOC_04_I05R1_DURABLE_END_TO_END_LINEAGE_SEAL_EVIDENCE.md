# SENSOR-B4-I05R1 — DURABLE CATALOG + END-TO-END PROJECTION LINEAGE SEAL

**Checkpoint:** SENSOR-B4-I05R1 (Durable Catalog + End-to-End Projection Lineage Seal)
**Status:** COMPLETE — proposed `PASS_SENSOR_B4_I05R1_DURABLE_END_TO_END_LINEAGE_SEALED`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab

---

## 1. Starting SHA

`6160960de8451c507c84a3b7565fba7b6200f220` (I05E + quality-flag type repair).
Verified exactly at session start; clean tree; required lineage
`537ad9fc` → `d28f3020` → `70afda3c` → `6f74cdd4` → `c80971d7` → `5c4f8070` → `6160960d` present.

## 2. Ending SHA

See the ledger commit — I05R1A..I05R1F sequence (no squash):

- `d183216e` — I05R1A: make projection catalogs atomic durable and corruption-intolerant
- `1aef9524` — I05R1B: seal safe catalog identities and exact schema fidelity
- `98ee9749` — I05R1C: integrate verified projection artifact and lineage resolver end to end
- `4868095b` — I05R1D: seal row-lineage ownership and projection publication preconditions
- `d8cc13e4` — I05R1E: add restart crash concurrency and corruption adversarial proof
- `9cdf88ac` — I05R1E: lint hygiene for changed scope
- (this commit) I05R1F: freeze I05R1 evidence, machine matrices and ledger

## 3. Operator HOLD finding

The operator HOLD (`HOLD_PASS_SENSOR_B4_I05_RAW_PROJECTION_LINEAGE_PENDING_I05R1_DURABLE_END_TO_END_LINEAGE_SEAL`)
identified that several I05 implementation surfaces did not satisfy the
durability/provenance claims recorded by I05. Additionally, production code
changed at `6160960d` AFTER the I05 evidence freeze, so the historical I05
evidence (660 storage / 2039 full) did not attest the starting HEAD.

## 4. Historical I05 evidence preserved

Untouched (chronology I05 → operator review → I05R1):

- `BLOC_04_I05_RAW_PROJECTION_LINEAGE_EVIDENCE.md`
- `BLOC_04_I05_PROJECTION_SCHEMA_MATRIX.json`
- `BLOC_04_I05_LINEAGE_MATRIX.json`
- `BLOC_04_I05_PROJECTION_INTEGRITY.json`

No historical file was rewritten. The test-count wording reconciliation from
the RATIFY commit stands: "582 passing storage tests (584 collected)".

## 5. Fresh current-HEAD baseline (recorded BEFORE repair)

Because `6160960d` postdated the I05 evidence freeze, a fresh baseline was
recorded as the authoritative I05R1 start floor (§58):

| Suite | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| storage | 665 | 663 | 0 | 2 |
| full `tests/crypto_sensor_fabric` | 2045 | 2042 | 0 | 3 |

Final I05R1 counts exceed this baseline (§23 below).

## 6. Catalog durability mechanism (Defect A)

New shared primitive `storage/json_catalog.py::DurableJsonCatalog` — the ONE
publication path for all immutable projection catalog truth (schema
definitions, artifact records, projection context records, lineage
manifests).  It reuses the accepted I03/I03R1 contract, never a weaker layer:

```
durable directory chain
→ staging (same filesystem)
→ write + flush
→ file fsync (handle open) + post-close re-sync
→ reopen/verify (exact canonical bytes re-parsed)
→ no-clobber atomic publish (os.link)
→ parent-directory fsync
→ success
```

Properties (all proven by tests):

- immutable history: idempotent reuse only for byte-identical content;
  same logical ID + differing content → `JsonCatalogConflict`;
- deterministic crash matrix at six injected fault boundaries
  (`CatalogFaultPoint`); post-publish faults preserve the final object as
  crash evidence and no success is claimed;
- canonical JSON bytes (`sorted_keys`, compact separators);
- canonical commit-order operation tags for evidence.

Repaired repositories now all persist through this primitive:

- `ProjectionSchemaRegistry` (was raw `write_text` + silent corrupt skip)
- `ProjectionArtifactRepository` (was raw `write_text` + raw `<id>.json`)
- `ProjectionContextRepository` (new)
- `ProjectionLineageRepository` (was raw `write_text` + raw `<lmid>.json`)

## 7. Catalog physical key formula (Defect C)

```
physical_filename = SHA256(UTF8(logical_id)).hexdigest() + ".json"
```

Full 64 lowercase hex + fixed suffix.  Raw logical IDs (projection_id,
lineage_manifest_id, schema identity) NEVER touch the filesystem namespace,
so `/`, `..`, `\`, NUL and absolute paths cannot escape a catalog root.

Physical-key binding (§9): on every load the filename is recomputed from the
logical ID stored INSIDE the fragment and must match exactly — a file cannot
masquerade under another logical identity (`JsonCatalogCorrupt`).

## 8. Corruption behavior (Defect A/§7) — never disappears

Every load path fails closed with typed errors; a corrupt committed object
can never silently become "not registered":

- schema catalog → `ProjectionSchemaCatalogCorrupt`
  (invalid JSON, key drift, fingerprint tamper, T0-contract drift,
  masquerading filename);
- artifact catalog → `ProjectionArtifactCatalogCorrupt`
  (invalid JSON, wrong record_type, unparseable model, binding violation);
- context catalog → `ProjectionArtifactCatalogCorrupt` (same family);
- lineage catalog → `ProjectionLineageCatalogCorrupt`
  (invalid JSON, wrong record_type, zero entries, id disagreement).

Tested: corrupt fragments remain on disk after the failed restart —
detection only; quarantine/recovery is I08's job (I05R1 fails closed).

## 9. Exact schema-fidelity contract (Defect E)

`projection_schema.py` rewritten:

- The fingerprint hashes the FULL ordered required T0 metadata schema
  (name + Arrow type + nullable per column) — `_t0_row_ordinal`
  int64→string now changes the fingerprint (§34/§35).  The canonical
  `T0_METADATA_SCHEMA` is defined ONCE and shared by fingerprint
  generation, the writer, staged validation and readers.
- Lossless Arrow type descriptors for every supported structural dimension:
  timestamp unit+timezone, time32/time64/duration units, date units,
  decimal precision/scale, fixed-size-binary width, list/large-list child
  name+nullability, struct child order/name/type/nullability, map
  key/value+keys_sorted, integer widths/sign, float widths.
- Fail closed on unsupported types (dictionary, union, unexpected nested)
  and malformed descriptors → `UnsupportedProjectionSchemaType`; the
  `getattr(pa, name)()` fallback is REMOVED.
- `ProjectionSchemaDefinition` eagerly verifies a lossless descriptor
  round trip before anything registers.
- Registry reload self-validation (§38): stored `schema_key` must rehash
  from stored id/version; stored fingerprint must recompute exactly; stored
  T0 schema must equal the current registered T0 contract; physical
  filename must equal `sha256(identity) + ".json"`.

## 10. Writer preconditions (Defect D + §28-§33)

`write_projection` now validates ALL cheap deterministic inputs BEFORE
physical publication:

- reserved `_t0_*` keys in provider-native rows → `ProjectionPreconditionError`
  (T0 metadata belongs exclusively to the projection layer; injected values
  overwrite by construction — §24);
- quality flags: `QualityFlagAcquisition` enum or exact string normalized
  BEFORE publication; invalid flags fail with no T0B bytes and clean staging
  (§29 — includes the post-I05 `6160960d` repair moved to pre-publication);
- source hashes: full SHA-256 syntax, uniqueness, parallel acquisition-id
  list, nonempty identity strings, nonnegative shard, path-structural
  projection_id rejection (§28);
- registered-schema gate: the registry must contain the exact
  id/version/fingerprint — an in-memory definition is not authority (§30);
- exact native row-field contract: unknown keys and missing non-nullable
  fields → `ProjectionSchemaMismatch`; nullable-missing becomes null (§31);
  no lossy coercion (§32);
- optional row-level attribution via a SEPARATE typed argument
  (`RowProjectionLineage`), validated against the declared source set
  pre-publication (§26/§27) — never through provider-native row dicts;
- staged Parquet re-verification (§33): full schema, T0 constants on every
  row (projection/provider/venue/sensor/instrument/parser/schema_version),
  contiguous row ordinals, single-source exact row lineage, multi-source
  non-null pairs within the declared set.

## 11. Artifact physical verification (§22/§23)

`ProjectionArtifactRepository.commit` may not accept arbitrary metadata.
Before first commit: `projection_uri` resolves safely beneath root, the file
exists, its exact SHA-256 equals `projection_sha256`, the Parquet opens,
`row_count` agrees, the registered schema agrees, every required `_t0_*`
column is present with the canonical type.  `state=VALID` is accepted only
after that proof.  Idempotence compares ALL immutable semantic fields
(§21); same bytes + different partition is a conflict.

## 12. Lineage commit gates (Defect B, §11-§13)

`ProjectionLineageRepository.commit` ENFORCES, before durable publication:

- nonempty; shared `lineage_manifest_id` and `projection_id`;
- the explicit `commit(lmid, entries)` argument binds to every entry (§19);
- row bounds both-or-none, inclusive, ordered (§20);
- `source_order` contiguous unique 0..N-1;
- artifact source list exactly matches the ordered lineage (§16);
- every source blob: durable EvidenceBlob metadata AND physical
  `LOCAL_HASH_VERIFIED` through `LocalBlobStore` (§48 — no metadata-only
  proof, no stale in-memory dictionaries);
- every source acquisition: exists durably, references the exact lineage
  blob, and is USABLE provenance (forensic failure never becomes T0B
  lineage — §17/§18);
- provider/venue/sensor_family/native_instrument match the projection
  context; granularity matches where both known — a KRAKEN projection can
  never use a GATE acquisition over identical bytes (§13);
- idempotence covers ALL lineage fields INCLUDING row bounds (§18).

Production commits read durable repositories only (§12); dictionary-based
`validate_lineage_source` remains a unit-test helper.

## 13. Production resolver (Defect B, §15/§16)

`storage/projection_resolver.py::ProjectionLineageResolver` — the REAL
implementation of the `ProjectionLineageResolver` protocol consumed by
`PartitionManifestRepository` (the I05D stub is no acceptance proof).  It
loads, from durable repositories only: artifact, context, physical Parquet,
registered schema, complete lineage, source acquisitions, source blobs —
and verifies the complete chain:

artifact+context+lineage identity agreement → physical SHA/row-count/T0
columns → registered schema fingerprint → lineage completeness → usable
identity-matched sources → partition match (partition_key, provider, venue,
sensor_family, native_instrument, granularity, logical window intersection)
→ manifest source visibility (every projection source blob in
`blob_refs`).

Typed failures: `ProjectionChainBroken`, `ProjectionPartitionMismatch`,
`ProjectionSourceHidden`, plus lineage/catalog corruption errors.

## 14. T0BProjectionService (§42)

One orchestration object earning the transition in the frozen order:
verify T0A sources → verify usable acquisitions → resolve registered
schema → validate inputs → write/verify/publish Parquet → commit artifact →
commit context → commit lineage → STOP (manifest publication is the
manifest repository's step; I07 resume advancement is NOT here).

## 15. End-to-end proof (§17/§44) — no stub on the acceptance path

`test_end_to_end_projection.py` builds the full real chain — actual
`LocalBlobStore`, `BlobMetadataRepository`, `AcquisitionRepository`,
`ProjectionSchemaRegistry`, writer, `ProjectionArtifactRepository`,
`ProjectionContextRepository`, `ProjectionLineageRepository`, the
production resolver, and `PartitionManifestRepository`:

- single-source real chain: resolver accepts against a real manifest;
- multi-source real chain: `[A, B]` artifact order = lineage order 0,1;
- wrong provider (GATE bytes == KRAKEN bytes) rejected;
- wrong acquisition/blob pair rejected;
- failed acquisition (failure_ref + H3=False) rejected AND preserved as
  forensic history;
- missing physical source rejected;
- missing artifact / missing lineage rejected;
- wrong partition rejected; hidden source blob rejected;
- dangling projection rejected;
- RESTART: all Python objects discarded, every repository reinstantiated
  from disk, the manifest projection_ref revalidated with the REAL
  production resolver — chain survives restart (§44).

## 16. Corruption restart matrix (§45)

After a valid chain, separately corrupting: schema fragment / physical
Parquet / artifact fragment / context fragment / lineage fragment → each
restart fails closed with the corresponding typed corruption error; no
skip, no silent disappearance, no automatic re-registration, no stale
cache; corrupt fragments remain on disk as evidence.

## 17. Crash matrix + concurrency (§46/§47)

- Catalog crash matrix at six deterministic boundaries
  (`CatalogFaultPoint`): pre-publish faults leave no final object;
  post-publish faults preserve the final object as crash evidence; nothing
  is ever claimed as committed in a crashing process.
- Concurrent identical schema/artifact/lineage commits from independent
  instances: adopt/reuse, exactly one physical fragment, same semantic
  result.
- Conflicting content under the same identity: typed conflict, exactly one
  truth intact.

## 18. Machine evidence (§57)

Deterministic (injected clocks, fixed identities, generation-twice
byte-stability asserted):

- `BLOC_04_I05R1_DURABILITY_MATRIX.json` — crash boundaries + idempotence
  for schema/artifact/context/lineage catalogs;
- `BLOC_04_I05R1_END_TO_END_LINEAGE_MATRIX.json` — all fifteen cases:
  single/multi-source real chains, wrong provider, wrong acquisition blob,
  failed acquisition, missing physical blob, missing artifact, missing
  lineage, wrong partition, hidden source blob, restart_valid,
  restart_corrupt_schema/projection/artifact/lineage;
- `BLOC_04_I05R1_SCHEMA_FIDELITY_MATRIX.json` — t0_metadata_type_change,
  time32/time64 units, timestamp timezone, list/struct child nullability,
  decimal precision/scale, unsupported_arrow_type, schema_key_tamper,
  schema_fingerprint_tamper.

## 19. Final test counts (§59)

| Suite | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| storage | 779 | 776 | 0 | 3 |
| full `tests/crypto_sensor_fabric` | 2159 | 2155 | 0 | 4 |

- Storage baseline 663 passed → final 776 passed (+113).
- Full-suite baseline 2042 passed → final 2155 passed (+113).
- 0 failures; skips are platform skips (POSIX-only cases on Windows) —
  unchanged doctrine.

## 20. Ruff / mypy / network / provider

- **ruff:** clean on all changed scope (`src/crypto_sensor_fabric/storage/`,
  `tests/crypto_sensor_fabric/storage/`).
- **mypy:** clean on changed scope
  (`json_catalog.py`, `projection_schema.py`, `projections.py`,
  `projection_lineage.py`, `projection_resolver.py`); the only error is the
  PRE-EXISTING `probes/planner.py:79` baseline documented in the I04R1
  ledger (untouched file).
- **network:** 0.
- **provider source changes:** none.

## 21. Scope discipline (§53-§55)

NOT done: I06 SourceRevision / SOURCE_MUTATION / FIRST_SEEN / LATEST_SEEN;
resume advancement or StorageJobState; recovery scanner; quota engine;
DuckDB; Postgres; RawEvidenceQuery; Bloc-5 semantics (no canonical asset,
no USD notional, no side reinterpretation, no funding/OI/liquidation
normalization); no network; no provider integration.

## 22. Ledger flags if earned

```
T0A_EVIDENCE_PIPELINE_COMPLETE        = TRUE
T0B_PROJECTION_SCHEMA_READY           = TRUE
T0B_PHYSICAL_PROJECTION_WRITER_READY  = TRUE
T0B_PROJECTION_CATALOG_IMPLEMENTED    = TRUE
T0B_LINEAGE_REPOSITORY_IMPLEMENTED    = TRUE
T0B_TO_T0A_LINEAGE_COMPLETE           = TRUE
T0B_STORAGE_IMPLEMENTED               = TRUE
SOURCE_REVISION_REGISTRY_IMPLEMENTED  = FALSE
DURABLE_RESUME_IMPLEMENTED            = FALSE
next_checkpoint_authorized            = FALSE
```

## 23. Proposed verdicts

- `PASS_SENSOR_B4_I05R1_DURABLE_END_TO_END_LINEAGE_SEALED` (proposed)
- then operator may accept `PASS_SENSOR_B4_I05_RAW_PROJECTION_LINEAGE`

## 24. STOP gate

After I05R1: STOP.  I06 (SOURCE REVISION / MUTATION REGISTRY) NOT started;
research NOT resumed; Bloc 5 NOT started.  Evidence returned to operator.
