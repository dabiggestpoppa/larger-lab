# BLOC 4 — ACQUISITION + MANIFEST REPOSITORY EVIDENCE (SENSOR-B4-I04)

Checkpoint: SENSOR-B4-I04 — ACQUISITION + MANIFEST REPOSITORY
Target verdict (proposed): `PASS_SENSOR_B4_I04_ACQUISITION_MANIFEST_REPOSITORY`
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA (mandated): `fb00a58775a39b516247bcca7f693a96d45a3086`
  (SENSOR-B4-I03R1-RATIFY)
Authorization SHA (commit 1 of the sequence): `4f04f44c`
  (SENSOR-B4-I04-AUTH — governance only; operator confirms I03/I03R1
  acceptance, reconciles I03R1 root-policy prose chronologically, authorizes
  I04 only)
Ending SHA: see ledger / `git log` (SENSOR-B4-I04E)

## 1. Scope honored

Implemented EXACTLY the authorized I04 envelope: durable EvidenceBlob
metadata, AcquisitionRecord history, append-only PartitionManifest versions,
current-partition pointer semantics, referential integrity between metadata
and physical T0A, concurrency-safe manifest advancement. The storage-layer
sequence is now: SOURCE BYTES → durable T0A blob → durable EvidenceBlob
metadata → durable AcquisitionRecord → append-only logical
PartitionManifest → transactional current-pointer advancement.

NOT implemented (later checkpoints own these): T0B Parquet raw-record
projections (I05), ProjectionLineage (I05), SourceRevision registry (I06),
StorageJobState persistence / resume advancement (I07), DuckDB (I10),
PostgreSQL (I11), raw query service (I12), Bloc 3 live integration /
FetchBatch ingestion (I14), provider network acquisition. No network calls
anywhere in the I04 surface; provider code unchanged.

## 2. I03R1 root-policy prose reconciliation

Historical `BLOC_04_I03R1_DURABILITY_NAMESPACE_SEAL_EVIDENCE.md` remains
immutable. The operator review found one prose/code mismatch: historical
prose said "configured storage root must pre-exist", while the actual
implementation permits a missing configured root (first put durably creates
missing namespace components from the deepest existing ancestor via
`ensure_durable_directory()`). That implementation is safe and was
explicitly allowed by the operator checkpoint; runtime was NOT changed to
make old prose true. The chronological correction is recorded in
`BLOC_04_I04_AUTHORIZATION.md`:

ACTUAL ROOT POLICY:

- existing root directory → use it;
- existing non-directory → fail;
- missing root → may be created through durable directory-chain creation
  from the deepest existing ancestor;
- no blind recursive mkdir + durability assumption.

## 3. Commit sequence (reviewable, per §84)

| Commit | Content |
|---|---|
| `4f04f44c` SENSOR-B4-I04-AUTH | governance only: operator confirms I03/I03R1 acceptance (both verdicts OPERATOR_ACCEPTED; ATOMIC_FILESYSTEM_BACKEND_READY=TRUE; T0A_BLOB_BACKEND_IMPLEMENTED=TRUE), records the ACTUAL ROOT POLICY prose reconciliation, authorizes SENSOR-B4-I04 ONLY |
| `a8a56c04` SENSOR-B4-I04A | AcquisitionRecord persistence-schema reconciliation with the frozen Bloc-3 handoff + 6 handoff-preservation tests |
| `0a160108` SENSOR-B4-I04B | immutable blob + acquisition Parquet catalog repository (`catalog.py`) |
| `06e1b80d` SENSOR-B4-I04C | append-only partition manifests + transactional current pointer + partition locks/CAS (`manifests.py`) |
| `c4bfb33f` SENSOR-B4-I04D | 58 tests: referential integrity, concurrency, pointer crash matrix + deterministic machine evidence generators |
| SENSOR-B4-I04E | this evidence artifact + machine evidence JSONs + ledger update |

## 4. AcquisitionRecord pre-I04 gaps found and closed (I04A)

The I01 `AcquisitionRecord` model lacked the following frozen Bloc-3 handoff
fields; all were added BEFORE any durable catalog record could be persisted
(I04 dependency correction — no acquisition catalog existed yet, so no
lineage was lost):

- `adapter_capability_version` (architecture §4.2 expected it; it never
  landed in the I01 model)
- `endpoint_host` / `endpoint_path` / `request_family` (endpoint identity,
  non-secret reconstruction facts)
- `actual_start` / `actual_end` (ACTUAL returned range, kept distinct from
  `requested_start` / `requested_end` — never inferred; None = unknown)
- `schema_state`
- `evidence_ref` (AdapterEvidenceRef representation)
- `provider_checksum_algorithm` / `provider_checksum_value` /
  `provider_checksum_verified` (replaces the single opaque
  `provider_checksum`; algorithm is never inferred from digest length; H3
  stays separate from H1 blob identity; absent provider checksum stays
  absent)

Already present and preserved: `provider_id`, `sensor_family`,
`native_instrument_id`, `request_fingerprint`, `blob_sha256`,
`retrieval_timestamp` (UTC), requested range, `adapter_version`,
resume/page identity, quality flags, source/native status, and the
retrieval/observation/ingestion timestamp separation
(`request_started_at` / `response_observed_at` / `ingested_at` — `ingested_at`
is never used as historical market availability time).

Frozen Bloc-3 types were reused, not duplicated: the reconciled model
imports/reuses the existing `SchemaState`, `AdapterEvidenceRef`,
`ResumeToken`, `QualityFlagAcquisition`, and `Granularity` types — no second
competing enum was created.

## 5. Final AcquisitionRecord persistent fields

See `BLOC_04_I04_CATALOG_SCHEMAS.json` (acquisitions family, schema version
1.0.0) for the exact stable Arrow schema: field names, logical types,
nullability, and model source. No field is dropped lossily; no Python
repr/pickle is persisted; resume tokens use the stable canonical JSON
serialization; quality flags are `LIST<STRING>`; evidence refs / schema
state preserve exact values and types.

## 6. Bloc-3 handoff preservation matrix

See `BLOC_04_I04_CATALOG_SCHEMAS.json` + the I04A handoff-preservation tests
in `tests/crypto_sensor_fabric/storage/test_models.py` (6 tests): every
frozen BLOC_04_INPUT_MANIFEST §2 fact (provider identity, sensor family,
native instrument, endpoint identity, request fingerprint, blob/raw hash,
retrieval timestamp, requested range, actual range, adapter version, schema
state, evidence ref, resume/page identity, quality flags, source/native
status, provider checksum triple) round-trips through the model and the
Arrow schema without loss.

## 7. Catalog physical layout

Immutable fragments live under `<t0_root>/catalogs/manifests/`; the current
pointer lives under `<t0_root>/catalogs/current/partitions/`; partition
locks under `<t0_root>/catalogs/locks/partitions/`; staging (same-device,
short path) under `<t0_root>/catalogs/staging/`:

```
<t0_root>/
    catalogs/
        manifests/
            blobs/          <blob_sha256>-<hash>.parquet
            acquisitions/   <safe-storage-key>-<hash>.parquet
            partitions/     <32-hex-hash>/
                                v00000001-<hash>.parquet
                                v00000002-<hash>.parquet
        current/
            partitions/     <32-hex-hash>.json   (mutable operational pointer)
        locks/
            partitions/     <32-hex-hash>.lock/  (atomic-mkdir no-replace)
        staging/            <nonce>-<family>.partial
    blobs/sha256/<h0h1>/<h2h3>/<full_sha>.blob[.zst]   (I03, unchanged)
```

Physical catalog locators are hashes (SHA-256 of exact UTF-8 identity
strings) — pure physical keys that never allow provider/native strings to
create unsafe path components. They do NOT replace the stored
`acquisition_id` / `partition_key` / `manifest_id` as logical identity: the
pointer JSON and every fragment embed the exact original logical identity.

## 8. EvidenceBlob catalog behavior

- `BlobMetadataRepository`: durable append-only EvidenceBlob metadata rows,
  one immutable Parquet fragment per blob.
- Physical blob verification gate: a blob-metadata row commits ONLY after
  (1) the physical EvidenceBlob object is present, (2) it verifies, and (3)
  the metadata's `blob_sha256`/`byte_length`/`integrity_state` match the
  verified object. No metadata record points at missing/unverified bytes.
- Idempotence: same `blob_sha256` + semantically identical metadata →
  idempotent reuse; same `blob_sha256` + conflicting immutable metadata
  (byte_length / storage_encoding / storage_uri / integrity-defining
  fields) → typed failure (`BlobMetadataConflict`), never overwrite.
- Empty body `b""` is a valid zero-byte blob (standard SHA256 empty digest,
  `byte_length=0`) — empty evidence is NOT treated as absent acquisition.
- Repeated acquisitions may reference the same blob (only physical bytes
  are deduped; acquisition history is not).

## 9. Acquisition repository behavior

- `AcquisitionRepository`: one immutable Parquet fragment per acquisition
  event; `acquisition_id` is immutable — same id + exact same semantic
  record → idempotent; same id + any differing field → typed
  `AcquisitionIdentityConflict`, old facts never mutated.
- Acquisition append requires the blob's durable metadata to exist when a
  blob ref is present (blob metadata is never auto-created from acquisition
  fields). A missing blob link is only legal with explicit
  failed/unavailable status or an explicit failure ref — a "successful
  acquisition + no blob + no failure reason" is never silently persisted.
- Same request fingerprint / different bytes: two acquisitions may both be
  stored (T0 preserves evidence); no collapsing, no canonical labeling
  (revision relationship is I06's).
- Resume/page facts are persisted as observed facts only; `resume_token`
  is never activated/advanced (I07 owns active resume coupling).

## 10. Partition identity / manifest versioning

- Partition identity = logical coordinates: provider, venue, sensor_family,
  native_instrument, source_granularity, logical date/range basis (no
  canonicalization of asset identity, no symbol conversion).
- v1: `manifest_version=1`, `supersedes_manifest_id=None`, requires NO
  current pointer to exist (else conflict).
- vN: requires current to exist; version = current+1; supersedes =
  current's `partition_manifest_id`; partition-key coordinates must match —
  else fail closed. No version gaps (v1→v3 without v2 rejected;
  non-current supersedes rejected).
- Every version is a COMPLETE logical snapshot (immutable fragment), never
  an in-place delta. Fragments are never overwritten.
- `projection_refs` is EMPTY for I04 writes (I05 owns projections); a
  commit carrying dangling projection refs fails closed — no placeholders.

## 11. Current pointer / lock / CAS semantics

- `PartitionCurrentPointer` is a small MUTABLE operational object
  (partition_key, partition_manifest_id, manifest_version,
  previous_manifest_id, updated_at) — NOT historical raw evidence. It is
  the ONLY mutable catalog object; overwrite semantics are forbidden for
  every historical fragment.
- Transactional update: stage → fsync pointer file → atomic replace →
  fsync pointer parent directory; readers always see a valid old or new
  pointer, never partial/truncated JSON.
- `append_partition_manifest()` requires `expected_current`: None for v1,
  `(current_manifest_id, current_version)` for vN. Actual mismatch →
  `ManifestCASConflict`; stale writers never silently retry onto a newer
  base.
- Partition-scoped coordination: atomic `mkdir` no-replace lock directory
  `catalogs/locks/partitions/<hash>.lock/` — exactly one local-filesystem
  writer holds it; inside the lock: read current → compare expected →
  validate next manifest → verify blob refs → publish immutable fragment →
  atomically update pointer → fsync → release.
- Lock crash policy: a crash may leave the lock directory; I04 NEVER
  auto-deletes stale locks — `ManifestLockHeld`/`RecoveryRequired`
  fail closed (I08 owns stale-lock recovery). Tests remove only their own
  synthetic locks.
- Local vs distributed: the filesystem lock/CAS protects INITIAL LOCAL
  multi-process writers only; it is explicitly NOT distributed
  coordination (I11 PostgreSQL owns durable database-backed coordination
  for the broader runtime later).
- Windows robustness: pointer replacement tolerates transient reader
  file-lock contention with a bounded retry before surfacing failure.

## 12. Pointer crash matrix (P1-P5)

Deterministic fault injection around the manifest-append transaction
(`RaisePointerFaultHook` / `PointerFaultPoint`):

| Point | Expected |
|---|---|
| P1 before manifest publication | old current, no new manifest |
| P2 after publication / before pointer stage | old current, new immutable orphan manifest possible |
| P3 after pointer stage+fsync / before replace | old current, new immutable manifest + staged pointer |
| P4 after pointer replace / before parent fsync | new pointer visible, success NOT returned; retry must re-establish pointer-parent durability before success |
| P5 after parent fsync / before return | new pointer durable, success not returned; retry/CAS resolves idempotently |

No corrupted current pointer in any case. A durably-published manifest that
never became current is orphan append evidence — never deleted
automatically; I04 retry may recognize the exact same manifest_id + content
and finish the intended transition if the expected base still permits it
(no broad scanner). Visible pointer ≠ proven durable pointer: retry after
P4 validates pointer content, the referenced manifest, and the referenced
blobs, fsyncs the pointer parent, and only then reports durable success.

## 13. Referential integrity / integrity vs coverage

- Before publication, every manifest `blob_ref` must (a) exist in the blob
  metadata catalog, (b) correspond to a physical blob object, and (c)
  verify at or above the manifest's claimed integrity state. Missing → fail
  (no dangling refs).
- A manifest never claims integrity stronger than its referenced evidence
  (e.g. all blobs LOCAL_HASH_VERIFIED → manifest may claim
  LOCAL_HASH_VERIFIED; any missing/quarantined blob → downgrade).
- `coverage_state` and `integrity_state` are preserved independently:
  coverage PARTIAL + integrity LOCAL_HASH_VERIFIED is valid; coverage is
  never upgraded because bytes verify, bytes never downgraded because
  coverage is partial.
- `blob_refs` are logical content-identity refs; blob files are never
  duplicated into partition directories (T0A physical layout stays
  provider-independent).

## 14. Read APIs (minimum, no raw query service)

- `get_blob_metadata(blob_sha256)` — typed NotFound for a missing id
- `get_acquisition(acquisition_id)` — typed NotFound
- `get_manifest(manifest_id)` — typed NotFound
- `get_current_manifest(partition_key)` — typed NotFound if no current
- `list_manifest_versions(partition_key)` — empty list allowed
- `list_orphan_manifest_fragments(partition_key)` — internal validation

The general RawEvidenceQuery API (I12) is NOT built.

## 15. Catalog rebuildability

Immutable fragments carry full logical identity and typed values (no
Python-only opaque objects, no repr strings), so later DuckDB (I10) and
PostgreSQL operational state (I11) rebuilders can import them without
reading provider adapters. I04 does NOT implement those rebuilders.

## 16. Parquet verification / determinism

- Before publication a staged fragment is reopened and validated: it
  parses, its schema matches the stable explicit Arrow schema exactly, it
  contains exactly the expected record(s), and deterministic identity
  fields match. A corrupt/unreadable fragment can never become catalog
  truth.
- Semantic determinism: read(fragment) → exact expected model value.
  Byte-identical Parquet across PyArrow versions is NOT claimed (frozen
  metadata/options make that unrealistic); immutable fragment hashes are
  still recorded.
- The machine-evidence artifacts themselves are byte-stable across
  regeneration (verified by sha256 across independent runs).

## 17. Verification results (canonical uv-managed .venv, Python 3.12)

- Storage suite: 488 passed / 2 skipped / 0 failed (490 collected;
  426 → 490 nodes, +64)
- Full crypto sensor fabric suite: **1867 passed / 0 failed / 3 skipped**
  (1870 collected; floor was >=1803 / 0 failed)
- ruff: clean on the changed scope (src: models/catalog/manifests/__init__;
  tests: storage suite)
- mypy: clean on the changed storage scope — only the pre-existing
  `probes/planner.py:79` baseline and `zstandard` stub noise (no py.typed)
  remain
- network calls: 0
- provider code changes: none
- Postgres work: none · DuckDB work: none · revision work: none · active
  resume work: none · T0B work: none

(Environment note: running the suite with the SYSTEM Python 3.11 fails 32
compression tests with `ModuleNotFoundError: zstandard` — interpreter
mix-up, not a code problem; the uv-managed `.venv` Python 3.12 is the
canonical runner.)

## 18. Evidence packet

- `BLOC_04_I04_CATALOG_SCHEMAS.json` — stable Arrow schemas per catalog
  family (blobs / acquisitions / partitions): field names, logical types,
  nullability, model source, schema version.
- `BLOC_04_I04_MANIFEST_CONCURRENCY.json` — deterministic cases:
  first_manifest, sequential_v2, eight_writer_same_base (winner-count 1,
  winner ∈ candidate set, candidate-set fingerprint — winner identity is
  scheduling-dependent by design and recorded as such), stale_writer,
  duplicate_exact_manifest, identity_conflict, pointer_P1..P5 crash matrix
  (expected current, winner count, final version, current manifest id,
  orphan count, test names). No wall-clock nondeterminism.
- `BLOC_04_I04_AUTHORIZATION.md` — governance authorization + ACTUAL ROOT
  POLICY reconciliation.
- Historical I03/I03R1 evidence untouched (byte-equality assertions pin
  them).

## 19. Proposed verdict / next

Proposed: `PASS_SENSOR_B4_I04_ACQUISITION_MANIFEST_REPOSITORY`.

Flags: STORAGE_MODEL_CONTRACTS_READY=TRUE · CONTENT_ADDRESSING_READY=TRUE ·
ATOMIC_FILESYSTEM_BACKEND_READY=TRUE · T0A_BLOB_BACKEND_IMPLEMENTED=TRUE ·
BLOB_METADATA_REPOSITORY_IMPLEMENTED=TRUE ·
ACQUISITION_REPOSITORY_IMPLEMENTED=TRUE · MANIFEST_REPOSITORY_IMPLEMENTED=TRUE ·
CURRENT_POINTER_SEMANTICS_READY=TRUE · T0A_EVIDENCE_PIPELINE_COMPLETE=TRUE
(storage-layer pipeline) · BLOC3_T0A_INTEGRATION_COMPLETE=FALSE (I14) ·
T0B_STORAGE_IMPLEMENTED=FALSE · SOURCE_REVISION_REGISTRY_IMPLEMENTED=FALSE ·
DURABLE_RESUME_IMPLEMENTED=FALSE.

next_checkpoint_authorized = FALSE. Recommended next: SENSOR-B4-I05 RAW
PROJECTION + LINEAGE LAYER — NOT started. I05 NOT begun; Bloc 5 NOT begun;
MECH21/LF14 NOT resumed.