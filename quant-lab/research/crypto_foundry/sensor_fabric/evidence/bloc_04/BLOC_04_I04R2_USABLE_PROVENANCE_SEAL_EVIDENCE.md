# SENSOR-B4-I04R2 — USABLE-ACQUISITION PROVENANCE + STREAMING H3 SEAL

Chronology: **I04 original → operator review → I04R1 repair → operator review → I04R2 repair.**
The historical I04 evidence (`BLOC_04_I04_ACQUISITION_MANIFEST_EVIDENCE.md`,
`BLOC_04_I04_CATALOG_SCHEMAS.json`, `BLOC_04_I04_MANIFEST_CONCURRENCY.json`,
`BLOC_04_I04_AUTHORIZATION.md`) and the historical I04R1 evidence
(`BLOC_04_I04R1_PROVENANCE_INTEGRITY_SEAL_EVIDENCE.md`,
`BLOC_04_I04R1_PROVENANCE_MATRIX.json`, `BLOC_04_I04R1_POINTER_SCHEMA.json`)
are NOT rewritten.  This file chronologically supersedes the affected claims
in the operator's original-claim → finding → correction → proof form.

## Checkpoint facts

- Starting SHA (exact): `c242425234fe9e0ec4bbc4266de149701da8e91e` (SENSOR-B4-I04R1E),
  clean tree, required I04R1 lineage verified (efde5fea → df0d28ca → 0a112ccf →
  cdef2ab3 → c2424252).
- Commits (per preferred sequence §34, no squash):
  1. `643b171c` SENSOR-B4-I04R2A — separate forensic acquisition history from usable manifest provenance
  2. `c9ec3ef9` SENSOR-B4-I04R2B — make H3 verification bounded and streaming-safe
  3. `383c9183` SENSOR-B4-I04R2C — seal usable-provenance adversarial matrix
  4. (this commit) SENSOR-B4-I04R2D — freeze I04R2 evidence and ledger
- Ending SHA: see ledger / `git log` (SENSOR-B4-I04R2D)
- Operator hold: `HOLD_PASS_SENSOR_B4_I04R1_PROVENANCE_INTEGRITY_SEALED_PENDING_I04R2_USABLE_PROVENANCE_SEAL` — the ONE remaining provenance contradiction (usable provenance vs durable history) plus the unbounded H3 read closed by this microseal.

## Operator finding — the provenance contradiction

- **Original (post-I04R1) behavior:** an acquisition carrying
  `provider_checksum_verified=False` plus explicit failure evidence was
  intentionally retained as FORENSIC FAILURE EVIDENCE (I04R1 §19).  But
  `find_matching_acquisitions()` / `has_matching_acquisition()` matched on
  durable acquisition IDENTITY only: a failed acquisition could therefore
  SATISFY the `LOCAL_HASH_VERIFIED` PartitionManifest provenance gate.
  Durable history and usable provenance were collapsed.
- **Correction (I04R2 §3/§5/§11/§13):** three concepts are now frozen
  separately — DURABLE ACQUISITION HISTORY (every acquisition fact worth
  preserving, including failures), MATCHING ACQUISITION IDENTITY
  (provider/venue/sensor/instrument/granularity match), and USABLE MANIFEST
  PROVENANCE (a matching acquisition eligible to support scientific manifest
  truth).  ONE authoritative module-level predicate,
  `is_usable_manifest_provenance(record)` in `catalog.py`, defines
  eligibility; `AcquisitionRepository.is_usable_manifest_provenance` is a
  class-surface alias.  No eligibility rule is duplicated between
  `has_usable_matching_acquisition`, `has_earned_h3_proof` and
  PartitionManifestRepository (I04R2 §13).

## Usable-provenance predicate (I04R2 §5)

A record is usable ONLY if ALL hold:

1. `record.blob_sha256 is not None` — durable source bytes exist;
2. `record.failure_ref is None` — no explicit failure evidence attached
   (I04R2 §10: presence itself disqualifies; arbitrary failure_ref strings
   are never interpreted);
3. the record is NOT an explicitly failed numeric HTTP/source outcome
   (>= 400, reusing the closed I04R1 parsing — I04R2 §6): a failed outcome
   whose response body was archived stays forensic T0A evidence, never
   manifest provenance;
4. `record.provider_checksum_verified is not False` (I04R2 §7): H3=False is
   NEVER usable, even when provider/venue/sensor/instrument/granularity all
   match.

Quality flags (`PARTIAL_INTERVAL`, `SCHEMA_ADDITIVE`, `LIMITED`,
`RATE_LIMITED`) NEVER automatically disqualify (I04R2 §5): partial data can
still be truthful evidence.

## H3 semantics (I04R2 §7/§8/§9/§12)

- **H3=False** (`provider_checksum_verified=False`): durable, queryable
  forensic failure history — never usable provenance, never provider
  integrity evidence.
- **H3=None**: may support `LOCAL_HASH_VERIFIED` or `UNVERIFIED` manifest
  provenance when all other usability conditions pass; H3 is optional for
  local integrity; it may NOT support `PROVIDER_HASH_VERIFIED`.
- **H3=True**: only reaches durable history after I04R1 repository
  recomputation over the exact source bytes; may support
  `LOCAL_HASH_VERIFIED` and, where required for EVERY ref,
  `PROVIDER_HASH_VERIFIED`.
- **has_earned_h3_proof** now requires usable-provenance eligibility FIRST
  (I04R2 §12): a record cannot become provider-integrity evidence merely
  because `provider_checksum_verified=True` while it simultaneously carries
  a `failure_ref` or an explicitly failed numeric status.

## Separate read APIs (I04R2 §11)

- FORENSIC/HISTORICAL reads (UNCHANGED enumeration): `list_acquisitions_for_blob()`
  and `find_matching_acquisitions()` / `has_matching_acquisition()` return
  ALL durable records including failures.
- USABLE provenance reads (NEW): `find_usable_matching_acquisitions()` /
  `has_usable_matching_acquisition()` filter identity matches through the
  one predicate.  `PartitionManifestRepository` publication now consumes the
  USABLE gate exclusively; forensic history enumeration is not silently
  changed.
- Identity matching is factored into one shared `_identity_matches` rule
  applied BEFORE eligibility (I04R2 §17) — wrong provider/venue/sensor/
  instrument/granularity regressions from I04R1 remain green.
- Typed error: `NoUsableAcquisitionProvenance(MissingAcquisitionProvenance)`
  raised when matching durable history exists but none of it is usable
  (I04R2 §14 sanctions the more specific typed error; subclassing keeps
  pre-I04R2 callers working).

## Forensic failure behavior preserved (I04R2 §4)

Provider checksum mismatch + `provider_checksum_verified=False` + explicit
failure evidence may STILL be durably persisted (I04R1 §19 recomputation
honesty unchanged: `verified=False` requires an observed mismatch — the
usable-provenance layer never relaxes it).  Failed records are never deleted
or rejected merely because they cannot support a normal data manifest; they
remain queryable through `get_acquisition` / `list_acquisitions_for_blob`
after a manifest rejection.

## Streaming H3 defect (I04R2 §20-§26)

- **Old behavior:** I04R1 `_validate_provider_checksum_claim` did
  `open_blob(...) → stream.read()` — an unbounded read materializing the
  ENTIRE decoded T0A artifact in memory before byte-based verification,
  conflicting with the evidence-lake bounded-stream doctrine and unsafe for
  large archives.
- **New API (`storage/checksums.py`, I04R2 §21):**
  `compute_checksum_stream(stream, algorithm, *, chunk_size=DEFAULT_CHUNK_SIZE)`
  → `ChecksumStreamResult(hex_digest, byte_length)` and
  `verify_checksum_stream(stream, algorithm, expected_hex, *, chunk_size=...)`.
  Only the existing explicit algorithms SHA256 / MD5 / CRC32 are supported —
  no new algorithms.
- **Streaming semantics (I04R2 §22):** configurable positive `chunk_size`
  (validated; bool/zero/negative rejected); NEVER calls `read()` without a
  size; bounded memory; works on non-seekable decoded source streams (e.g.
  the ZSTD `stream_reader`); begins at the current stream position and never
  rewinds; does NOT close the caller-owned stream; EXACT parity with the
  byte-based `compute_checksum`/`verify_checksum`, which are behaviorally
  UNCHANGED (I04R2 §26 — existing I02 tests remain green).
- **CRC32 streaming (I04R2 §23):** updates incrementally across chunks via
  `zlib.crc32(chunk, running)` and preserves the canonical representation —
  8 lowercase hex chars with leading zeros (`00000000` for the empty stream;
  no decimal ambiguity).
- **Repository use (I04R2 §24):** `AcquisitionRepository` H3 recomputation
  now streams over `LocalBlobStore.open_blob(...)` — decoded T0A bytes are
  never materialized solely to verify H3.  A malformed expected value is
  rejected by `verify_checksum_stream` BEFORE any byte is consumed.
- **Bounded-read proof (I04R2 §25):** an 8 MiB deterministic logical stream
  (generated block-by-block, no 1 GiB allocation, no RNG, no wall clock)
  proves: no unbounded read; every requested read size <= `chunk_size`
  (tracked by a probe reader); checksum parity against the identical logical
  sequence; exact byte count returned by the helper.

## Machine evidence (I04R2 §30)

`BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json` — deterministic (injected
clocks, fixed identities, no wall-clock nondeterminism), byte-stable across
regeneration.  Eight cases with `durable_acquisition_count`,
`usable_acquisition_count`, `manifest_allowed`, `provider_integrity_allowed`,
`expected_error`, `test_name`:

| case | durable | usable | manifest | provider | expected_error |
|---|---|---|---|---|---|
| clean_no_h3 | 1 | 1 | true | false | null (PROVIDER → UnearnedProviderIntegrityClaim) |
| clean_h3_true | 1 | 1 | true | true | null |
| failed_h3_false | 1 | 0 | false | false | NoUsableAcquisitionProvenance |
| failed_http_with_body | 1 | 0 | false | false | NoUsableAcquisitionProvenance |
| failure_ref_with_body | 1 | 0 | false | false | NoUsableAcquisitionProvenance |
| failed_plus_clean | 2 | 1 | true | false | null |
| wrong_provider_clean | 1 | 0 | false | false | MissingAcquisitionProvenance |
| provider_integrity_clean_h3 | 1 | 1 | true | true | null |

## Test floor (I04R2 §32) and required coverage (I04R2 §33)

- Baseline at start: storage 534 passed / 2 skipped (platform skips); full
  suite 1913 passed / 0 failed / 3 skipped — matches the sealed I04R1
  evidence exactly.
- After I04R2: storage 582 passed / 2 skipped (534 + 48 new nodes: 29
  usable-provenance + 18 streaming checksum + 1 machine-evidence); full
  suite 1961 passed / 0 failed / 3 skipped (1964 collected).  Floor >= 1913
  held; failures = 0.
- All §33 required tests present: failed H3 persists as forensic history /
  cannot support LOCAL / cannot support PROVIDER; HTTP 503-with-body and
  failure_ref-with-body cannot support manifests; clean H3 None supports
  LOCAL; clean earned H3 True supports LOCAL and PROVIDER; failed+clean
  supports via clean only; `list_acquisitions_for_blob` still returns failed
  records; usable read excludes failed records; wrong provider/sensor/
  instrument/granularity remain rejected; streaming SHA256/MD5/CRC32 parity;
  nonseekable streaming; no read() without size; caller stream remains open;
  large logical stream bounded; original I04R1 pointer tests, secret tests,
  P1-P5 crash matrix and 8-writer CAS remain green (same storage suite run).

## Boundary (I04R2 §27/§28/§35/§36)

- Pointer repairs (schema_version, strict types, partition binding, ancestry
  binding), secret vocabulary, blobless closed rule: UNCHANGED (no I04R1
  repair reopened).
- No T0B, no RawProjectionArtifact repository, no ProjectionLineage
  repository, no T0B provider-native rows, no projection schema registry, no
  parser execution, no projection manifest, no multi-blob projection writer.
- No SourceRevision, no resume advancement, no DuckDB, no Postgres, no
  provider integration.  Network = 0.  Provider code unchanged.
- I05 NOT started.  next_checkpoint_authorized = FALSE.  STOP GATE honored —
  evidence returned for operator review.

## Flags

```text
T0A_EVIDENCE_PIPELINE_COMPLETE        = TRUE
BLOB_METADATA_REPOSITORY_IMPLEMENTED  = TRUE
ACQUISITION_REPOSITORY_IMPLEMENTED    = TRUE
MANIFEST_REPOSITORY_IMPLEMENTED       = TRUE
CURRENT_POINTER_SEMANTICS_READY       = TRUE
T0B_STORAGE_IMPLEMENTED               = FALSE
next_checkpoint_authorized            = FALSE
```
