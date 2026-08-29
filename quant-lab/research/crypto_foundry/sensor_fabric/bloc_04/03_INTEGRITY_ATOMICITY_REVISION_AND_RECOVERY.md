# BLOC 4 — INTEGRITY, ATOMICITY, REVISION & RECOVERY

**Purpose:** ensure T0 evidence survives crashes, partial writes, repeated downloads, provider mutations, and disk faults without silent corruption or evidence loss.

---

## 1. Atomic-write doctrine

A raw artifact is either durably committed or not committed.

No consumer may observe a half-written blob/projection as valid evidence.

### Filesystem commit sequence

For each blob/projection:

```text
1. write to staging path on SAME filesystem
2. flush userspace buffers
3. fsync file
4. compute/verify checksum from staged bytes
5. rename staging → final path atomically
6. fsync parent directory
7. record durable metadata transaction
8. only then advance resume/job state
```

Cross-filesystem rename is prohibited for the atomic commit path.

Staging and final destination must share filesystem/device unless backend proves equivalent atomic semantics.

---

## 2. Temp/staging naming

```text
<t0_root>/staging/<job_id>/<artifact_id>.partial
```

Staging files MUST encode enough metadata in a sidecar or operational record to support crash recovery.

Never infer a committed file merely because a `.partial` exists.

---

## 3. Crash matrix

### Crash before fsync

Result:

`UNCOMMITTED_STAGING`

Safe action:

- validate if possible;
- otherwise discard staging and refetch;
- do not advance resume token.

### Crash after blob rename but before metadata transaction

Result:

`ORPHAN_DURABLE_BLOB`

Recovery:

- hash and validate blob;
- reconcile with staged job metadata/request fingerprint;
- either register acquisition or move to quarantine if context is insufficient.

Never delete automatically before evidence reconciliation.

### Crash after acquisition metadata but before projection

T0A remains valid.

Projection can be rebuilt.

Job status:

`RAW_COMMITTED_PROJECTION_PENDING`

### Crash after projection but before partition manifest update

Projection is orphaned-but-recoverable.

Rebuild manifest from projection/acquisition metadata.

### Crash before resume advancement

Re-fetch may occur.

Content addressing deduplicates identical bytes while repeated acquisition remains auditable.

This is preferred to advancing resume beyond durable evidence.

---

## 4. Exactly-once is not required at acquisition level

Network ingestion should target:

**at-least-once acquisition + idempotent durable storage.**

Why:

- exchanges may repeat pages/messages;
- reconnect boundaries are uncertain;
- exact source semantics vary;
- falsely claiming exactly-once can drop evidence.

Bloc 4 guarantees:

- exact duplicate bytes need not consume duplicate blob storage;
- repeated acquisition records remain visible;
- downstream normalization later handles event-level duplicates explicitly.

---

## 5. Checksum layers

Three separate hashes/checksums may exist.

### H1 — source-byte SHA256

Mandatory.

Computed over exact provider bytes.

### H2 — stored-object checksum

Optional but recommended when local compression/wrapping is applied.

Validates storage object bytes without decompression.

### H3 — provider checksum

Optional when provider publishes checksum.

All three must be distinguishable.

Do not compare a provider MD5 against local SHA256 field.

---

## 6. Integrity verification schedules

### On write

Every artifact:

- source hash calculated;
- stored hash verified;
- provider checksum validated when supplied.

### Periodic scrub

Configurable sample/full scrub:

```text
DAILY: recent/high-value partitions sample
WEEKLY: broader sample
MONTHLY/OPERATOR: full critical-sensor scrub when practical
```

The planner does not mandate exact wall-clock cron; implementation should expose configurable schedules.

High-priority scrub order:

1. liquidation evidence;
2. OI/funding;
3. T0A source archives;
4. live raw stream chunks;
5. high-volume replaceable projections.

---

## 7. Corruption response

On checksum mismatch:

1. mark blob `QUARANTINED_INTEGRITY_FAILURE`;
2. prevent new projections/canonical promotion;
3. identify acquisitions/manifests referencing blob;
4. downgrade affected coverage;
5. attempt refetch ONLY if source is still free/available and policy permits;
6. retain corrupted bytes until operator/recovery policy decides disposition;
7. create explicit recovery evidence.

Never silently overwrite corrupted bytes with refetched content under same identity.

A refetch necessarily has a new verified hash if bytes differ.

---

## 8. Source revisions

Provider-side data can mutate.

Examples:

- monthly archive replaced;
- historical API backfills missing records;
- exchange corrects timestamps;
- aggregator revises history.

Revision identity uses a `source_revision_key` derived from source location/request semantics, not content hash.

```text
source_revision_key
revision_number
blob_sha256
first_seen_at
last_seen_at
revision_reason
```

### Revision states

```text
STABLE
IDENTICAL_REFETCH
SOURCE_MUTATION
PROVIDER_DECLARED_REVISION
UNKNOWN_REVISION
```

T0 stores all revisions.

Bloc 5 decides canonical PIT use.

---

## 9. Mutation alert thresholds

Any change in bytes for the same immutable-looking provider archive/request boundary should emit an alert/evidence event.

Severity:

```text
INFO     identical refetch
NOTICE   provider-declared revision
WARNING  unexplained source mutation
BLOCKER  mutation combined with timestamp/semantic/schema drift
```

No source mutation is silently normalized away.

---

## 10. Projection invalidation

T0B projection may become invalid when:

- parser bug discovered;
- schema semantics reinterpreted;
- source blob integrity fails;
- lineage incomplete;
- timestamp parse wrong;
- native numeric precision lost.

Projection state:

```text
VALID
SUPERSEDED
INVALID_PARSER
INVALID_SOURCE
INVALID_LINEAGE
```

Invalid projection remains in history but is excluded from usable discovery views.

New projection points to same T0A source evidence under new parser/schema version.

---

## 11. Numeric precision rule

Raw provider numeric strings should not be prematurely converted to binary floating point when doing so loses evidence.

T0B guidance:

- preserve original string when provider sends decimal strings and ambiguity matters;
- additionally parse to Decimal-compatible Arrow decimal where scale is known;
- never discard raw lexical representation solely for convenience;
- timestamps preserve raw value + parsed interpretation when units are uncertain or provider semantics historically changed.

Bloc 5 will select canonical types.

---

## 12. Timestamp integrity

T0 should preserve:

```text
provider_time_raw
provider_time_parsed
provider_time_unit_assumption
date_basis
response_observed_at
ingested_at
```

If timestamp unit/meaning is uncertain:

flag:

`TIMESTAMP_SEMANTICS_UNVERIFIED`

Do not fabricate confidence.

---

## 13. Dedupe rules

### Byte dedupe

Allowed automatically by source hash.

### Request dedupe

A scheduler may avoid issuing an identical completed immutable request when policy says no refresh is needed.

But repeated probes/audits may intentionally re-acquire.

### Row/event dedupe

NOT a Bloc 4 semantic responsibility.

T0B may expose exact duplicate provider rows, with row ordinal/source lineage intact.

Later normalization handles economic duplicate policy.

---

## 14. Manifest concurrency

Multiple adapter jobs may write simultaneously.

Rules:

- blobs are content-addressed and naturally conflict-safe after checksum verification;
- acquisition IDs are unique;
- manifest version increments require transactional compare-and-swap or DB locking;
- no two writers may mutate same manifest row in place;
- partition manifests are append-only versions;
- current pointer update is transactional.

PostgreSQL advisory/row locks are acceptable for manifest-current pointer coordination.

Raw file locks alone are not sufficient for distributed/future multi-process operation.

---

## 15. Job durability

`StorageJobState` must survive process restart.

State transitions:

```text
PLANNED
ACQUIRING
RAW_STAGED
RAW_COMMITTED
PROJECTION_PENDING
PROJECTION_COMMITTED
MANIFEST_COMMITTED
CHECKPOINT_ADVANCED
COMPLETE
FAILED_RETRYABLE
FAILED_TERMINAL
QUARANTINED
```

A job may not move backward silently.

Recovery may append a new transition explaining repair.

---

## 16. Resume invariant

For paginated/backfill jobs:

```text
resume_token_after(N)
```

may be persisted as the active resume point only if batch N's required T0 evidence has reached `MANIFEST_COMMITTED` or an explicitly configured minimum durable state.

Recommended default:

`MANIFEST_COMMITTED`.

This prevents cursor advancement past unindexed evidence.

---

## 17. Orphan reconciliation

Implement recovery scanner for:

- stale `.partial` files;
- final blobs absent from blob catalog;
- projections absent from projection catalog;
- manifests referencing missing blobs;
- acquisitions referencing quarantined blobs;
- job states ahead of durable evidence.

Recovery output:

```text
recovery_run_id
object_type
object_id
problem
resolution
before_state
after_state
evidence_ref
```

No silent repair.

---

## 18. Quarantine structure

```text
<t0_root>/quarantine/
  integrity/
  malformed/
  unknown_context/
  secret_leak_prevented/
  schema_drift/
```

Quarantine is not usable T0 evidence for canonical promotion.

It remains inspectable for debugging.

If a payload is detected to contain a secret that should never have been persisted, security policy may require secure deletion rather than normal immutable retention. This is the explicit exception to raw immutability.

---

## 19. Secret scanning/redaction boundary

Metadata headers/query fields are sanitized BEFORE persistence.

Raw market-data bodies are expected to be public and normally preserved exactly.

If a source body unexpectedly includes credentials/private-account data:

- block promotion;
- quarantine securely;
- emit `SENSITIVE_DATA_DETECTED`;
- follow security deletion policy;
- do not commit fixture/raw evidence to Git.

No trading/private API keys belong in this fabric.

---

## 20. Recovery acceptance tests

Implementation must simulate at least:

1. crash halfway through blob write;
2. crash after blob rename;
3. crash after acquisition DB commit;
4. crash after projection write;
5. crash before manifest-current pointer update;
6. crash before resume advancement;
7. identical refetch;
8. same request with mutated bytes;
9. corrupted stored blob;
10. missing manifest target;
11. parser bug/projection rebuild;
12. concurrent writers to same logical partition.

Expected result:

No lost committed evidence, no cursor skipping, no silent overwrite, no half-valid object.

---

## 21. Final doctrine

> Prefer duplicate acquisition over missing evidence. Prefer explicit revision over overwrite. Prefer quarantine over silent repair. Advance cursors only behind durable truth.
