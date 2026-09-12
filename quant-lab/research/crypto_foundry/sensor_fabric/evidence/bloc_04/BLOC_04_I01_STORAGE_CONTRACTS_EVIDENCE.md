# BLOC 4 — STORAGE CONTRACTS EVIDENCE (SENSOR-B4-I01)

Checkpoint: SENSOR-B4-I01 — STORAGE MODELS + ENUMS
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA: `34a8130ace7d8de161ecddcad7dfd36bdb551c7e`
Ratification SHA: `049baf52` (SENSOR-B3-I11R1-RATIFY)
Ending SHA: see ledger / `git log` (I01D)

## 1. Operator Bloc 3 ratification

- `PASS_SENSOR_B3_I11R1_HANDOFF_CONSISTENCY_SEALED` = OPERATOR_ACCEPTED
- `PASS_BLOC_03_IMPLEMENTATION` = OPERATOR_ACCEPTED
- `BLOC_03_IMPLEMENTATION_COMPLETE = TRUE`, `BLOC_03_FROZEN = TRUE`
- `NETWORK_VALIDATION = PASS`, `REAL_PROVIDER_ADAPTERS = 4`,
  `PRODUCTION_PATHS = 17/17`, `PHYSICAL_PRODUCTION_SYMBOL_CHECKS = 18/18`
- `BLOC_04_PLAN = PASS_BLOC_04_PLAN_FROZEN`
- Authorized ONLY SENSOR-B4-I01 (storage models + enums).

## 2. Authority documents

1. `BLOC_03_HANDOFF_INDEX.md`
2. `BLOC_04_INPUT_MANIFEST.md`
3. `bloc_04/07_BLOC_04_FREEZE_MANIFEST.md` (final authority; conflicts with older
   docs are resolved in ITS favor)
4. `bloc_04/01_T0_RAW_EVIDENCE_LAKE_ARCHITECTURE.md`
5. `bloc_04/02_PARTITION_MANIFEST_AND_FILE_FORMAT_CONTRACTS.md`
6. `bloc_04/03_INTEGRITY_ATOMICITY_REVISION_AND_RECOVERY.md`
7. `bloc_04/04_STORAGE_FOOTPRINT_RETENTION_DUCKDB_POSTGRES_BACKUP.md`
8. `bloc_04/05_RAW_EVIDENCE_QUERY_REPLAY_AND_BLOC5_HANDOFF.md`
9. `bloc_04/06_ACCEPTANCE_TESTS_AND_STAGED_IMPLEMENTATION_COMMITS.md`
10. existing repository coding/model conventions (Pydantic v2, extra="forbid",
    `normalize_utc_datetimes()`).

## 3. Revision-policy reconciliation (freeze §4)

The older partition-doc vocabulary `LATEST_ACQUIRED` / `FIRST_ACQUIRED`
(`02_...md` §544–545) is NOT introduced anywhere in the storage package.  The
final frozen vocabulary is used exclusively:

`ERROR_ON_AMBIGUITY · ALL · FIRST_SEEN · LATEST_SEEN · EXACT_REVISION ·
PROVIDER_DECLARED_CANONICAL`

No aliasing.  `RawEvidenceQuery.revision_policy` defaults to
`ERROR_ON_AMBIGUITY` (research-safe: never silently pick a revision).

## 4. Package layout

```
quant-lab/src/crypto_sensor_fabric/storage/
    __init__.py      (frozen public exports)
    enums.py         (frozen enum vocabularies)
    models.py        (16 frozen storage models + canonical_json_bytes helper)

quant-lab/tests/crypto_sensor_fabric/storage/
    __init__.py
    test_enums.py
    test_models.py
    test_serialization.py
```

NOT created (belong to later checkpoints): paths.py, checksums.py, atomic.py,
blob_store.py, manifests.py, query.py, replay.py, duckdb_catalog.py,
postgres_repository.py.

## 5. Models implemented (all 16, names frozen)

`EvidenceBlob`, `AcquisitionRecord`, `RawProjectionArtifact`,
`ProjectionLineage`, `PartitionManifest`, `StorageJobState`,
`StorageJobTransition`, `SourceRevision`, `IntegrityCheck`,
`StorageQuotaState`, `BackupState`, `RawEvidenceQuery`, `RawEvidenceResult`,
`RawNormalizationBatch`, `RecoveryAction`, `ExportManifest` — all exported
from `crypto_sensor_fabric.storage` (verified).

## 6. Enums implemented (exact frozen member sets)

- `IntegrityState` — UNVERIFIED, LOCAL_HASH_VERIFIED, PROVIDER_HASH_VERIFIED,
  QUARANTINED_INTEGRITY_FAILURE, MISSING_BLOB, PROJECTION_INVALID
- `CoverageState` — COMPLETE_SOURCE_BOUNDARY, PARTIAL, KNOWN_GAP,
  EMPTY_CONFIRMED, NOT_ATTEMPTED, FAILED, ACCESS_BLOCKED, HISTORY_UNAVAILABLE,
  QUARANTINED, REVISION_CONFLICT
- `RevisionPolicy` — ERROR_ON_AMBIGUITY, ALL, FIRST_SEEN, LATEST_SEEN,
  EXACT_REVISION, PROVIDER_DECLARED_CANONICAL (NO FIRST_ACQUIRED/LATEST_ACQUIRED)
- `RevisionState` — STABLE, IDENTICAL_REFETCH, SOURCE_MUTATION,
  PROVIDER_DECLARED_REVISION, UNKNOWN_REVISION
- `ProjectionState` — VALID, SUPERSEDED, INVALID_PARSER, INVALID_SOURCE,
  INVALID_LINEAGE
- `StorageEncoding` — NONE, ZSTD
- `DateBasis` — EVENT_TIME, PROVIDER_FILE_DATE, SNAPSHOT_TIME, UNKNOWN
- `StoragePriority` — P0, P1, P2, P3 (storage policy only, not market score)
- `DiskPressure` — NORMAL, WATCH, CONSTRAINED, CRITICAL (thresholds NOT baked in)
- `BackupClass` — UNBACKED, MANIFEST_BACKED, SECOND_COPY_VERIFIED,
  OFFSITE_VERIFIED
- `StorageJobStatus` — PLANNED, ACQUIRING, RAW_STAGED, RAW_COMMITTED,
  PROJECTION_PENDING, PROJECTION_COMMITTED, MANIFEST_COMMITTED,
  CHECKPOINT_ADVANCED, COMPLETE, FAILED_RETRYABLE, FAILED_TERMINAL, QUARANTINED
- `StorageObjectType` — EVIDENCE_BLOB, ACQUISITION_RECORD, RAW_PROJECTION,
  PARTITION_MANIFEST, SOURCE_REVISION, STORAGE_JOB, EXPORT_MANIFEST

Integrity and coverage are separate enum classes (disjoint member names).

## 7. Validation invariants enforced

- SHA-256 fields: 64 lowercase hex syntax only (no hashing, no file/stream
  access in I01)
- nonnegative byte lengths, row counts, revision numbers, manifest versions,
  gap counts, verified counts, total bytes, limits (no negative sentinels)
- `requested_end >= requested_start`, `logical_date_end >= logical_date_start`,
  `logical_time_end >= logical_time_start`, `last_seen_at >= first_seen_at`,
  `source_row_end >= source_row_start` (never silently swapped)
- `manifest_version >= 1`, `revision_number >= 1`
- all datetimes timezone-aware and UTC-normalized (naive rejected)
- `extra="forbid"` everywhere (unknown persisted metadata fails closed)
- `StorageJobTransition` noop transition rejected
- `BackupState` default `UNBACKED`; `RawEvidenceQuery` default revision policy
  `ERROR_ON_AMBIGUITY`

## 8. T0 doctrine honored

- T0A (`EvidenceBlob`) = exact source artifact; T0B (`RawProjectionArtifact`)
  = rebuildable projection, subordinate (no override semantics implemented —
  models only)
- `blob_sha256` = hash of EXACT provider-source bytes BEFORE wrapper compression
- acquisition identity != blob identity (`AcquisitionRecord.blob_sha256` is an
  optional reference, not the record's own identity)
- logical partition (`PartitionManifest.partition_key`) != physical blob
  address (`EvidenceBlob.storage_uri`)
- coverage (`CoverageState`) and integrity (`IntegrityState`) separate
- missingness explicit: no numeric-zero semantics, `NOT_ATTEMPTED`/`FAILED`/
  `EMPTY_CONFIRMED`/`KNOWN_GAP` distinct
- no canonical asset/unit fields anywhere; `RawNormalizationBatch` forbids
  canonical_asset_id / canonical_notional / effective_at / normalized_* fields
  (Bloc 5 owns those)
- no secret-bearing fields (no API keys, tokens, cookies, credentials)

## 9. Deterministic serialization

`canonical_json_bytes()` helper (UTF-8, `sort_keys=True`, compact separators,
enum values explicit, UTC ISO-8601, no wall-clock auto-population).  Tests
prove: same input → byte-identical; different input → different bytes;
timezone-equivalent input → same normalized UTC representation; field
insertion order irrelevant; no `datetime.now()` contamination.

## 10. Bloc 3 bridge + dependency direction

- Storage imports frozen shared types: `SensorFamily`, `Granularity`,
  `QualityFlagAcquisition`, `ResumeToken`, `AdapterEvidenceRef`,
  `RawPayloadEnvelope` (in tests)
- Importing `crypto_sensor_fabric.storage` loads ONLY `providers.base.*`
  shared contracts — NO provider adapter implementation (kraken/gate/okx/
  deribit) is loaded
- Provider adapters do NOT import storage (unchanged provider code)
- No circular import; Bloc 3 remains independently usable

## 11. Tests

New storage tests: **78** (test_enums 24 + test_models 40 + test_serialization
14 — see commit notes for exact counts).  Full `crypto_sensor_fabric` suite:
**1457 passed / 0 failed / 1 skipped** (skip = env-gated live smoke,
fail-closed; normal suite makes ZERO network calls).

- ruff: clean (storage scope)
- changed-scope mypy: `Success: no issues found` (storage scope; the known
  pre-existing baseline in untouched probe/rest modules is separated, not hidden)

## 12. Constraints honored

- network calls: 0
- filesystem writes by storage runtime: 0 (models only — no I/O)
- no hashing implementation (format validation only)
- no compression implementation
- no path implementation
- no atomic write backend
- no manifest repository / persistence
- no DuckDB, no Postgres, no Parquet
- provider implementation code: UNCHANGED
- I02 (content addressing + paths + checksums): NOT started
- Bloc 5: NOT started; MECH21/LF14: NOT resumed

## 13. Proposed verdict

`PASS_SENSOR_B4_I01_STORAGE_CONTRACTS_FROZEN` — the immutable evidence lake now
has a stable typed vocabulary but DOES NOT yet have a storage backend.

Readiness state: `STORAGE_MODEL_CONTRACTS_READY = TRUE` · `T0A_STORAGE_IMPLEMENTED
= FALSE` · `T0B_STORAGE_IMPLEMENTED = FALSE` · `ATOMIC_BACKEND_IMPLEMENTED =
FALSE` · `MANIFEST_REPOSITORY_IMPLEMENTED = FALSE`.
`next_checkpoint_authorized = FALSE`; recommended next: **SENSOR-B4-I02
CONTENT ADDRESSING + PATHS + CHECKSUMS** (NOT started).
