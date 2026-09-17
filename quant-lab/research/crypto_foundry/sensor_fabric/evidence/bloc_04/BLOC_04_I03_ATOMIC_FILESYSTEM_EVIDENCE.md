# BLOC 4 — ATOMIC FILESYSTEM BACKEND EVIDENCE (SENSOR-B4-I03)

Checkpoint: SENSOR-B4-I03 — ATOMIC FILESYSTEM BACKEND
Target verdict (proposed): `PASS_SENSOR_B4_I03_ATOMIC_FILESYSTEM_BACKEND`
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA (mandated): `e525779a4c214968de4f6c7a728710490cb5939e`
  (SENSOR-B4-I02R1D — ledger reconciliation)
Ratification SHA (commit 1 of the sequence): `d3e920700668adb3ab36eb53c60fe3c6d0efa659`
  (SENSOR-B4-I02R1-RATIFY — governance only; operator accepts I02R1/I02,
  reconciles pytest-node truth, authorizes I03 only)
Ending SHA: see ledger / `git log` (SENSOR-B4-I03D)

## 1. Scope honored

Implemented EXACTLY the authorized I03 envelope: local filesystem backend,
staging, exact-source streaming write, optional ZSTD wrapper, file flush,
file fsync, staged-byte/source verification, same-filesystem validation,
no-clobber atomic publication, parent-directory fsync, immutable final blob
guard, blob existence/open/verify, idempotent duplicate-byte behavior,
fault/crash injection tests — commit sequence THROUGH step 6 of the frozen
doctrine.

NOT implemented (later checkpoints own these): AcquisitionRecord repository
(I04), partition manifests / current pointers / source-revision registry
(I04), durable StorageJobState + resume advancement (I07), T0B Parquet
projections (I05), recovery/quarantine scanning (I08), DuckDB, PostgreSQL,
backfill, live recording, Bloc 5 normalization, provider adapters (Bloc 3
frozen).  No network calls anywhere in the I03 surface.

## 2. Commit sequence (reviewable, per §78)

| Commit | Content |
|---|---|
| `d3e92070` SENSOR-B4-I02R1-RATIFY | governance only: operator accepts I02R1/I02, reconciles test-node truth (+22 net, not "35"), authorizes I03 only |
| `fa95b771` SENSOR-B4-I03A | streaming NONE/ZSTD wrapper (`compression.py`) + low-level no-clobber durability primitives (`atomic.py`) + zstandard dependency + wrapper/primitive tests |
| `fa41aa43` SENSOR-B4-I03B | immutable local T0A blob put/open/verify backend (`blob_store.py`) + package exports + core backend tests |
| `95b21b26` SENSOR-B4-I03C | adversarial seal: race, crash matrix, component + cross-filesystem tests; generated `BLOC_04_I03_CRASH_MATRIX.json` + `BLOC_04_I03_ATOMIC_ORDER.json` |
| SENSOR-B4-I03D | this evidence artifact + ledger update |

## 3. Storage root contract

- `LocalBlobStore(root)` takes an EXPLICIT configurable data root.  Nothing
  is hard-coded: no `~/quant-lab-data`, no `/mnt/data`, no repository root,
  no Desktop path.  The absolute local root is RUNTIME CONFIGURATION and is
  NOT evidence identity.
- `EvidenceBlob.storage_uri` is the backend-neutral object key
  (`blobs/sha256/<h0h1>/<h2h3>/<full_sha>.blob[.zst]`), never an absolute
  workstation path (test-frozen: `str(tmp_path)` never appears in
  `storage_uri`).
- Git contains NO production T0 payloads: tests use `tmp_path` + synthetic
  deterministic fixtures only.
- Initial backend layout limited to what I03 requires:

```
<t0_root>/
    blobs/
        sha256/
            <h0h1>/<h2h3>/<full_sha>.blob[.zst]
    staging/
        [<escaped job_id>/]<nonce>.partial
```

Test-frozen: only `blobs` + `staging` directories are ever created; no
`projections/`, `catalogs/`, `duckdb/`, `postgres/`, `exports/`, `quarantine/`.

## 4. Long-component guard (closes I02R1's LONG_COMPONENT_CHECK_REQUIRED_IN_I03)

- Before opening/writing ANY artifact path, every backend-controlled
  object-key component is validated against the filesystem's supported
  component length: POSIX queries `os.pathconf(path, "PC_NAME_MAX")`;
  Windows (no pathconf) uses the documented 255 UTF-16-unit NTFS limit
  (components are ASCII after canonical escaping, so units == bytes there).
- Fail closed with typed `ComponentTooLong` — never truncate, normalize,
  hash native identity, or silently shorten.  A too-long escaped native
  identity fails explicitly (test-frozen).
- Enforced at BOTH write surfaces: the final blob key (injected tiny
  name_max proves failure BEFORE the final fanout namespace is created; raw
  `OSError ENAMETOOLONG` is never the primary contract) and the
  caller-supplied `job_id` staging identity (over-limit job_id fails typed
  BEFORE the staging directory or file exists).

## 5. Same-filesystem enforcement

- Staging and final destination are always on the same filesystem (both
  under the configured root).  Before final publication, device identity is
  verified via `st_dev` (`os.stat(...).st_dev`) — the accepted POSIX-styled
  proof; Windows exposes the volume id here.
- Cross-device atomic commit FAILS CLOSED with
  `CrossFilesystemAtomicityError`.  There is NO copy+delete fallback on the
  commit boundary — that would destroy the atomicity contract (test-frozen
  via dependency-injected device probe; no second physical mount required
  in CI).

## 6. H1 / H2 / H3 separation (test-frozen)

| Layer | Definition | Behavior |
|---|---|---|
| H1 `blob_sha256` | SHA-256 of EXACT provider-source bytes, computed BEFORE wrapper compression | invariant across NONE/ZSTD; never replaced by H2 |
| H2 stored-object SHA-256 | SHA-256 of the STORED bytes (wrapper included) | computed for staged wrapper bytes; equals H1 ONLY for NONE; for ZSTD normally differs |
| H3 provider checksum | optional, EXPLICIT algorithm (SHA256 / MD5 / CRC32), verified against exact DECODED source bytes | never inferred, never mandatory, never promoted to T0 identity |

- H3 mismatch → `ProviderChecksumMismatch` BEFORE any usable final commit;
  no silent ignore; staged evidence preserved (I08 owns long-term
  quarantine placement).
- No JSON formatting, newline normalization, text decoding, encoding
  conversion, or projection parsing anywhere in the hash path.

## 7. Streaming behavior

- `put(source)` reads the caller's binary stream at its CURRENT position
  with bounded `read(chunk_size)` (configurable, default = I02
  `DEFAULT_CHUNK_SIZE`); no unbounded `read()`, no `bytes(stream)`, no
  full-object materialization (3 MiB streamed fixture; no 1 GiB load).
- Non-seekable sources accepted; the caller's stream is NEVER closed
  (ownership preserved, test-frozen); H1 + byte counts computed while
  streaming.
- Fault-injection adversarial reader proves a concurrent reader can never
  observe half-written final bytes (§61 gate).

## 8. NONE encoding

Stored bytes == exact source bytes, byte for byte.  After durable commit,
decoded read == source bytes exactly.  H1 == H2 for NONE.  Empty source
`b""` is valid evidence: hashes correctly, stores correctly, opens as
`b""`, verifies correctly.

## 9. ZSTD encoding

- Frozen `StorageEncoding.ZSTD` wrapper implemented with the
  repository-approved `zstandard>=0.23.0` package (standard maintained
  library, ships `py.typed` + stubs; added to `pyproject.toml` + `uv.lock`
  per dependency policy).  NO gzip/bz2/lzma substitute.
- ZSTD changes STORED bytes only — never H1, never source `byte_length`.
- Round trip: source SHA before compression == SHA of decoded open_blob
  bytes; stored file is a compressed ZSTD frame; H1 != H2 test-frozen on a
  compressible fixture.
- Deterministic: encoding the same bytes twice yields identical stored
  bytes (no embedded timestamps in frames).

## 10. Stage durability + staged verification (through step 6)

Operation order test-frozen (§65):

```
STAGE_WRITE < FILE_FLUSH < FILE_FSYNC < STAGE_VERIFY
            < ATOMIC_PUBLISH < PARENT_DIR_FSYNC < SUCCESS_RETURN
```

1. Staging artifact created `O_EXCL` with conservative `0o600`
   (never world-writable; POSIX-only mode assertions skipped on Windows).
2. Streaming write → `flush()` (userspace buffers) → `os.fsync(fd)` while
   the write handle is OPEN.  fsync failure = no publication, no fake
   success.
3. STAGED VERIFICATION re-opens the staged artifact: stored bytes re-hashed
   (H2 check), wrapper decoded, decoded H1 recomputed and compared to the
   source H1, decoded length compared, optional H3 recomputed.  Successful
   compressor return alone is never trusted (for ZSTD the staged wrapper is
   actually decoded and H1 recomputed from decoded bytes).
4. NO-CLOBBER publication: `os.link(staging, final)` — the final NAME
   appears only when the fully-written, fully-fsynced inode is linked; a
   blind overwrite-capable `os.replace`/`rename` is never used as final
   semantics.  An existing final name yields `AtomicPublishTargetExists`
   (primitive level) / verified reuse or typed conflict (store level).
5. PARENT-DIRECTORY FSYNC after the final entry appears; the success result
   is returned only AFTER directory fsync succeeds.  A success result
   before parent fsync is a failing test (§64).
6. Platform truth: POSIX = open dir `O_RDONLY` + fsync; Windows = open with
   `FILE_FLAG_BACKUP_SEMANTICS` + `FlushFileBuffers` (documented NTFS
   directory-flush mechanism).  If a platform cannot flush a directory,
   typed `DurabilityUnsupported` is raised — durability is never claimed
   without proof.  Verified platform for this checkpoint: Windows NTFS
   (local checkout) with POSIX code paths exercised by the portable test
   suite; NFS/distributed semantics NOT assumed.

## 11. Atomic publish primitive + reuse

`atomic.publish_no_replace()` is the generic low-level primitive (staged
writer → verified staged object → atomic publish → directory fsync), kept
free of T0A hash semantics so I05 T0B projection writing can reuse it.
`blob_store.py` applies T0A hash/identity policy on top.  No premature
Parquet/projection code.

## 12. Existing-object / duplicate / concurrency semantics

- EXISTING FINAL, VALID: never overwritten; opened + verified; truthful
  `REUSED_EXISTING` disposition (idempotent byte dedupe); final mtime and
  content untouched; the caller's own staging is cleaned only AFTER the
  existing final verifies.
- EXISTING FINAL, INVALID (corrupt collision, adversarially planted):
  typed `ExistingBlobIntegrityConflict`; NOT overwritten, NOT deleted, NOT
  repaired; staging preserved; recovery/quarantine policy is I08.
- DUPLICATE WRITE: one immutable final physical object per requested
  wrapper encoding; second write changes nothing at the final path and
  returns `REUSED_EXISTING`.
- CONCURRENT IDENTICAL WRITERS: 8 threads race the same content — exactly
  one `COMMITTED_NEW`, 7 `REUSED_EXISTING`, exactly one final file, winner
  verifies, no corruption/overwrite/partial final.  Concurrent DISTINCT
  writers show no crosstalk.
- `blob_exists` is PRESENCE ONLY — never implies verified integrity.
- MISSING blob = typed `BlobMissing` (distinct from empty source and from
  integrity failure).  CORRUPTED committed blob =
  `QUARANTINED_INTEGRITY_FAILURE` via `verify_blob`'s typed `IntegrityCheck`
  — detection only, loud failure, no repair (I08 owns recovery).

## 13. Crash / fault matrix (deterministic, injected hooks — no killed runner)

Machine-readable: `evidence/bloc_04/BLOC_04_I03_CRASH_MATRIX.json`
(generated by `TestCrashMatrix::test_crash_matrix_artifact_written`, never
hand-declared).

| Point | Injected at | final_exists | staging_exists | success_returned | Expected state |
|---|---|---|---|---|---|
| A | during staged write | FALSE | TRUE | FALSE | `UNCOMMITTED_STAGING` |
| B | after write, before file fsync | FALSE | TRUE | FALSE | `UNCOMMITTED_STAGING` |
| C | after file fsync, before staged verify | FALSE | TRUE | FALSE | `UNCOMMITTED_STAGING` |
| D | after verify, before final publication | FALSE | TRUE | FALSE | `UNCOMMITTED_STAGING` |
| E | after final publication, before parent fsync | TRUE | TRUE | FALSE | `ORPHAN_DURABLE_BLOB` |
| F | after parent fsync, before return | TRUE | TRUE | FALSE | `DURABLE_COMMITTED` |

- A–D: the final committed path never exists; no durable-success result is
  emitted.
- E: the final path MAY exist (namespace publication happened) but the
  operation NEVER reports successful durable commit — future I08
  `ORPHAN_DURABLE_BLOB` reconciliation territory.
- F: the blob is durably committed; a retry verifies/dedupes safely
  (`REUSED_EXISTING`, test-frozen).  No resume/cursor assertions exist in
  I03.
- NO auto-recovery: no stale-partial scanning, no automatic destructive
  cleanup of crash artifacts; ordinary successful commits clean only their
  own transient staging; ambiguous integrity failures preserve staging
  evidence.

## 14. Atomic order evidence

Machine-readable: `evidence/bloc_04/BLOC_04_I03_ATOMIC_ORDER.json`
(generated by `TestOperationOrder::test_atomic_order_artifact_written`) —
records the proven operation sequence
`stage_write → file_flush → file_fsync → stage_verify → device_check →
atomic_publish → parent_dir_fsync → staging_cleanup → success_return`
against the frozen seven-operation canonical contract.

## 15. Clock / metadata

`created_at` is metadata, NOT content identity: an injectable clock makes
tests deterministic (`FIXED = 2026-09-04T12:00:00Z`); wall-clock time never
contaminates content digest, object key, or dedupe identity.

## 16. Gates adjudication (I03 §72)

| Gate | Result | Proof |
|---|---|---|
| I03-G1 SOURCE EXACTNESS | PASS | put/open exact round-trips: empty, NUL, all byte values, JSON, random binary, 3 MiB streamed (both encodings) |
| I03-G2 STAGING ISOLATION | PASS | faults A–D never expose a final; adversarial concurrent reader never sees partial final bytes |
| I03-G3 FILE DURABILITY | PASS | flush + `os.fsync(fd)` while handle open, before publication (operation-order recorder) |
| I03-G4 STAGED VERIFICATION | PASS | staged artifact re-opened; H2 + decoded H1 + length verified BEFORE publication |
| I03-G5 NO-CLOBBER ATOMICITY | PASS | `os.link` no-replace; existing final never overwritten; corrupt existing → typed conflict |
| I03-G6 DIRECTORY DURABILITY | PASS | parent-dir fsync before success return; success-before-fsync = failing test |
| I03-G7 IDEMPOTENT DUPLICATE | PASS | same bytes → one final, `REUSED_EXISTING`, final untouched |
| I03-G8 CONCURRENT PUBLISH | PASS | 8-thread same-hash race: 1 new / 7 reused / 1 final / all verify |
| I03-G9 CROSS-FILESYSTEM DENIAL | PASS | injected st_dev probe; commit denied, no copy fallback |
| I03-G10 LONG-COMPONENT DENIAL | PASS | typed `ComponentTooLong` BEFORE artifact write (final key + job_id) |
| I03-G11 WRAPPER REVERSIBILITY | PASS | NONE and ZSTD restore exact source; H1 != H2 frozen for ZSTD |
| I03-G12 IMMUTABILITY | PASS | no public overwrite method; repeated put never changes final bytes |

Bloc 4 acceptance gate G4-01 (EXACT EVIDENCE GATE): I03 earns the
BYTE-STORAGE portion only — `stored(source_bytes) → read() == source_bytes`
and `SHA256(read()) == EvidenceBlob.blob_sha256` (test-frozen).  The FULL
Bloc 4 program is NOT claimed complete.

## 17. Test / toolchain accounting (this checkout, I03C+)

pytest-node truth (collect-only, Python 3.12.13, pytest 8.x):

| Storage test file | Collected nodes |
|---|---|
| `test_enums.py` | 18 |
| `test_models.py` | 81 |
| `test_serialization.py` | 16 |
| `test_checksums.py` | 35 |
| `test_paths.py` | 109 |
| `test_compression.py` | 34 |
| `test_atomic.py` | 22 |
| `test_blob_store.py` | 51 |
| `test_blob_store_adversarial.py` | 24 |
| **storage total** | **390** |

- I03 net: +131 storage nodes (259 → 390).
- Full suite: **1770 collected** = 1768 runnable + 2 environment-skipped
  (1 env-gated live-smoke `sensor_network_smoke` + 1 POSIX-only permission
  assertion skipped on Windows).
- Full suite execution: **1768 passed / 0 failed / 2 skipped** (floor was
  ≥1638 passed / 0 failed).
- ruff: clean on changed scope (all storage src + tests).
- mypy: clean on changed scope (`zstandard` resolves via its shipped
  `py.typed`; the 4 remaining repo-baseline errors are the documented
  pre-existing yaml/planner items in untouched Bloc 2/3 modules:
  `probes/planner.py:22/79`, `providers/probe_base.py:16`,
  `providers/base/capabilities.py:45`).
- Network calls in I03: **0**.  Provider code changes: **none**.

## 18. Provider independence / security / data

- `compression.py`, `atomic.py`, `blob_store.py` import NO provider adapter
  and NO network library (source-inspection test-frozen); importing
  `crypto_sensor_fabric.storage` loads no provider adapter module
  (subprocess test-frozen).  Storage stays provider-independent; adapters
  still do not import storage (Bloc 3 integration waits for I14).
- No AcquisitionRecord persistence, no manifest persistence, no resume
  advancement, no T0B projection persistence, no DuckDB, no Postgres.
- Tests use `tmp_path` + synthetic fixture bytes only; no provider data
  collected, no live exchange responses written, no production T0 root.
- Zero network calls; no secrets persisted (source bytes are opaque PUBLIC
  market-data; the full secret scanner remains I15).

## 19. Verdict proposed

```
PASS_SENSOR_B4_I03_ATOMIC_FILESYSTEM_BACKEND
```

State flags:

```text
STORAGE_MODEL_CONTRACTS_READY    = TRUE
CONTENT_ADDRESSING_READY         = TRUE
PATH_CONTRACT_READY              = TRUE
CHECKSUM_PRIMITIVES_READY        = TRUE
ATOMIC_FILESYSTEM_BACKEND_READY  = TRUE
T0A_BLOB_BACKEND_IMPLEMENTED     = TRUE
T0A_EVIDENCE_PIPELINE_COMPLETE   = FALSE   # AcquisitionRecord + PartitionManifest persistence = I04
MANIFEST_REPOSITORY_IMPLEMENTED  = FALSE
T0B_STORAGE_IMPLEMENTED          = FALSE
```

STOP after I03: I04 (ACQUISITION + MANIFEST REPOSITORY) is NOT started and
requires operator authorization.  Bloc 5 NOT started.  MECH21/LF14 NOT
resumed.
