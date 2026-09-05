# BLOC 4 — LINEAGE + SCHEMA MICROSEAL EVIDENCE (SENSOR-B4-I01R1)

Checkpoint: SENSOR-B4-I01R1 — PROJECTION VERSION + T0 LINEAGE + DATE-BASIS SEAL
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA: `6d0f23d9430a2855dbc81ae595d09da294c044fb`
Ending SHA: see ledger / `git log` (I01R1C)

## 1. Chronology

```
I01 original          -> storage models + enums frozen (BLOC_04_I01_STORAGE_CONTRACTS_EVIDENCE.md, immutable)
operator review       -> HOLD_PASS_SENSOR_B4_I01_STORAGE_CONTRACTS_FROZEN_PENDING_I01R1_LINEAGE_SCHEMA_SEAL
I01R1 correction      -> this artifact: five narrow contract defects sealed BEFORE hashes/paths/IDs depend on them
```

The original I01 evidence is preserved as history; it is not erased or
rewritten.  This artifact supersedes only the affected contract details.

## 2. Projection version mismatch found (defect A)

`RawProjectionArtifact.projection_schema_version` and
`RawNormalizationBatch.projection_schema_version` were modeled as `int`,
but the frozen T0B contract defines SEMANTIC versioning
(PATCH = metadata/doc-compatible, MINOR = backward-compatible additive,
MAJOR = removal/type/timestamp-semantic change).

## 3. Final semantic-version representation

`projection_schema_version: str` validated strictly as `MAJOR.MINOR.PATCH`
via a closed helper (`_validate_semver`, no external dependency):

- accepted: `1.0.0`, `1.1.0`, `2.0.0`
- rejected: `1`, `"1"`, `"v1"`, `"1.0"`, `"1.0.0-beta"`, `"01.0.0"`,
  negative components, whitespace-padded forms

Applied to BOTH `RawProjectionArtifact` and `RawNormalizationBatch`.  No
integer projection version remains in public storage contracts.  Canonical
serialization emits the version exactly as a string (e.g.
`"projection_schema_version":"1.0.0"`).  No auto-bump / PATCH-MINOR-MAJOR
decision logic was implemented (that belongs to projection/schema lifecycle).

## 4. Source-lineage minimum invariants (defect B)

- `RawProjectionArtifact.source_blob_sha256` is now `Field(min_length=1)` —
  a T0B projection MUST reference one or more T0A blobs; `[]` is rejected.
- The same list must be SET-UNIQUE: duplicate source blob refs fail closed
  (repeated acquisition of the same blob is expressed via `ProjectionLineage`,
  which owns acquisition identity + `source_order` ordering).
- `RawNormalizationBatch` requires BOTH `source_blob_refs` (>= 1 T0A hash,
  set-unique) AND `acquisition_refs` (>= 1) — T1 lineage must trace back to
  T0; a source-less normalization batch is forbidden.

## 5. SHA-reference validation coverage (defect D)

The 64-lowercase-hex syntax validator now applies to every field that
semantically is a T0A blob SHA (syntax only, no hashing in I01R1):

`EvidenceBlob.blob_sha256` · `AcquisitionRecord.blob_sha256` ·
`RawProjectionArtifact.source_blob_sha256` · `RawProjectionArtifact.projection_sha256` ·
`ProjectionLineage.source_blob_sha256` · `PartitionManifest.blob_refs` ·
`RawEvidenceResult.blob_refs` · `RawNormalizationBatch.source_blob_refs` ·
`SourceRevision.blob_sha256` · `StorageJobState.last_committed_blob_sha256`.

Non-SHA fields (projection_refs, acquisition_ids, lineage_refs, manifest IDs)
are NOT treated as hashes — their contracts do not say they are.  Duplicate
physical blob refs are REJECTED (not silently deduplicated) wherever set
semantics apply; ordering is owned by `ProjectionLineage.source_order`.

## 6. DateBasis default correction (defect C)

`PartitionManifest.date_basis` default changed `EVENT_TIME` -> `UNKNOWN`.
A caller must explicitly assert `EVENT_TIME` / `PROVIDER_FILE_DATE` /
`SNAPSHOT_TIME` when evidence supports it.  No code infers EVENT_TIME from
logical dates, ingested_at, provider or sensor.  Tests: omitted -> UNKNOWN;
explicit each value -> preserved.

## 7. Timestamp min/max guards (defect E)

- `RawProjectionArtifact`: `max_provider_time >= min_provider_time` when both
  present; one-sided bounds remain representable (min known / max unknown is
  distinct from min == max — the absent side is never fabricated).
- `PartitionManifest`: `max_time >= min_time` when both present; one-sided
  allowed.
- `RawEvidenceResult` / `RawNormalizationBatch` logical start/end validation
  already existed and is unchanged.

## 8. Schema version vs parser version

`projection_schema_version` != `parser_version` != `adapter_version` remain
distinct fields; a parser release does not imply a projection schema semantic
change, and a schema MAJOR change does not rewrite T0A.  Test asserts the
fields are separately preserved.

## 9. Deterministic serialization regression

Re-run after the semver change: same semantic model input -> byte-identical;
timezone-equivalent input -> same UTC bytes; dict insertion order ->
byte-identical; projection version preserved exactly as string; date_basis
UNKNOWN serialized explicitly; different semver -> different canonical bytes;
no wall-clock values introduced automatically.

## 10. Bloc 3 bridge regression

RawPayloadEnvelope / FetchBatch / ResumeToken storage bridge tests re-run
green: no loss of provider_id / sensor_family / native instrument / request
fingerprint / adapter version / raw content hash.  Provider adapters do not
import storage; no circular dependency.

## 11. Public API

All 16 frozen model names retained, unrenamed.  No new public exports added
(the semver validation is an internal helper, not a new public contract).

## 12. Tests

Storage tests: **115** (78 from I01 + 37 new I01R1: semver accept/reject,
zero/malformed/duplicate source refs, normalization batch lineage, hash-ref
surfaces, date-basis defaults, timestamp order, semver serialization).
Full `crypto_sensor_fabric` suite: **1494 passed / 0 failed / 1 skipped**
(skip = env-gated live smoke; normal suite makes ZERO network calls).
ruff clean; changed-scope mypy clean (only the known pre-existing baseline in
untouched probe/rest modules remains — separated, not hidden).

## 13. Constraints honored

- network calls: 0
- storage runtime filesystem writes: 0 (models only)
- no streaming SHA256 / content IDs / blob paths / path escaping / zstd /
  atomic writes / fsync / rename / blob store / partition persistence /
  manifest repository / DuckDB / Postgres / Parquet / revision repository /
  query service / replay
- provider code: UNCHANGED
- revision policy, T0A/T0B authority, acquisition != blob identity,
  integrity != coverage, missing != zero, no canonical market semantics:
  all unchanged
- original I01 evidence preserved
- I02 (content addressing + paths + checksums): NOT started

## 14. Proposed verdicts

- `PASS_SENSOR_B4_I01R1_STORAGE_CONTRACTS_SEALED`
- then operator acceptance of `PASS_SENSOR_B4_I01_STORAGE_CONTRACTS_FROZEN`
- `STORAGE_MODEL_CONTRACTS_READY = TRUE`; T0A/T0B/ATOMIC_BACKEND/
  MANIFEST_REPOSITORY_IMPLEMENTED = FALSE
- `next_checkpoint_authorized = FALSE`; recommended next: **SENSOR-B4-I02
  CONTENT ADDRESSING + PATHS + CHECKSUMS** (NOT started)
