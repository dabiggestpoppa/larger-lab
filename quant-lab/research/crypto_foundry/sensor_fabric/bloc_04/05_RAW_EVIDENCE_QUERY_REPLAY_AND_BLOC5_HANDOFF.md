# BLOC 4 — RAW EVIDENCE QUERY, REPLAY BOUNDARY & BLOC 5 HANDOFF

**Purpose:** define how downstream normalization can request raw evidence deterministically without coupling to filesystem paths or provider-adapter implementations.

---

## 1. Downstream contract

Bloc 5 must consume T0 through a storage/query service, not by globbing directories itself.

Conceptual interfaces:

```text
RawEvidenceCatalog
RawEvidenceQuery
RawEvidenceResult
RawArtifactReader
RawProjectionReader
LineageResolver
RevisionResolver
```

Provider adapter code ends before this boundary.

PIT normalization starts after it.

---

## 2. `RawEvidenceQuery`

Minimum query object:

```text
providers?: list
venues?: list
sensor_families?: list
native_instruments?: list
source_granularities?: list
logical_start?: timestamp/date
logical_end?: timestamp/date
acquired_before?: timestamp
observed_before?: timestamp
integrity_minimum?: enum
coverage_states?: list
revision_policy: enum
include_t0a: bool
include_t0b: bool
projection_schema_ids?: list
limit?: int
```

No implicit default revision selection when multiple source revisions exist.

Recommended default in research tooling:

`revision_policy=ERROR_ON_AMBIGUITY`.

---

## 3. Revision resolution modes

```text
ERROR_ON_AMBIGUITY
ALL
FIRST_SEEN
LATEST_SEEN
EXACT_REVISION
PROVIDER_DECLARED_CANONICAL [only if evidence exists]
```

The raw lake does not know which revision is point-in-time valid for a historical market replay unless provider publication semantics establish it.

Bloc 5 may build a PIT revision resolver from these facts.

---

## 4. `RawEvidenceResult`

Every result item should expose:

```text
provider
venue
sensor_family
native_instrument
source_granularity
logical_time_range
coverage_state
integrity_state
acquisition_ids
blob_refs
projection_refs
revision_state
quality_flags
lineage_refs
```

No returned result may hide source ambiguity.

---

## 5. Artifact reader

`RawArtifactReader` reads exact T0A bytes by blob hash.

Capabilities:

```text
open_bytes(blob_sha256)
stream_bytes(blob_sha256)
verify(blob_sha256)
metadata(blob_sha256)
```

Consumer should not need to know local compression wrapper.

Reader transparently decodes local wrapper compression while preserving/validating source hash.

---

## 6. Projection reader

`RawProjectionReader` accesses T0B Parquet by projection ID or query selection.

Must expose:

```text
projection_schema_id
projection_schema_version
parser_version
source_lineage
```

Bloc 5 can reject incompatible old projections and reparse T0A instead.

---

## 7. Historical replay warning

There are two different “as-of” questions.

### A. System acquisition replay

> What had OUR fabric actually acquired by timestamp X?

Filter primarily by:

`ingested_at <= X`.

Useful for reproducing live scanner behavior after the fabric exists.

### B. Historical market reconstruction

> What information was economically/publicly available in the market by historical timestamp X, regardless of when we downloaded it later?

This requires provider event/publication/effective-time semantics.

A 2022 trade downloaded in 2026 can be valid evidence for a 2022 market reconstruction even though `ingested_at=2026`.

Bloc 4 preserves the required timestamp facts but does NOT decide canonical PIT availability.

That is Bloc 5's job.

Never conflate A and B.

---

## 8. Raw replay cursor

Provide deterministic iteration over raw evidence:

```text
RawReplayCursor(
  query,
  order_by = PROVIDER_EVENT_TIME | SOURCE_ORDER | ACQUISITION_ORDER
)
```

When provider event time is unavailable or ambiguous, replay must expose that limitation rather than fabricating order.

For stream data, frame sequence/session order is authoritative within connection generation when provider sequence is absent.

---

## 9. Ordering semantics

Possible order coordinates:

```text
provider_sequence
provider_event_time
source_file_row_order
stream_frame_sequence
response_observed_at
ingested_at
```

Order precedence is provider/sensor-specific and versioned.

No global “sort by timestamp and pray” rule.

Bloc 5 will establish canonical event ordering where earned.

---

## 10. Raw evidence batch contract into Bloc 5

For normalization, T0 should emit `RawNormalizationBatch` conceptually:

```text
batch_id
provider
venue
sensor_family
native_instrument
projection_schema_id
projection_schema_version
parser_version
raw_rows_or_reader
source_blob_refs
acquisition_refs
logical_time_range
integrity_state
coverage_state
revision_state
quality_flags
```

Bloc 5 then produces T1 canonical observations with direct lineage back to this batch.

---

## 11. Required lineage into T1

Every T1 canonical row later must be able to reference at least:

```text
source_provider
source_venue
source_acquisition_id
source_blob_sha256
source_projection_id?
source_row_locator?
normalization_methodology_id
```

Bloc 4 guarantees the source side of that chain exists.

Bloc 5 guarantees canonical transformations.

---

## 12. Bloc 5 must not mutate T0

Normalization fixes are append-only downstream.

If Bloc 5 discovers a parser problem:

1. mark affected T0B projection invalid;
2. build a new projection from T0A if needed;
3. create a new T1 normalization version;
4. preserve old evidence/history.

Do not “clean up” T0A source bytes.

---

## 13. Coverage handoff

Bloc 5 must receive per raw batch:

```text
coverage_state
known_gap_intervals
source_granularity
history_boundary
revision_state
integrity_state
```

This prevents canonical normalization from interpreting absent rows as market zeros.

---

## 14. Instrument identity handoff

T0 preserves native instrument identity exactly.

Bloc 5 resolves:

- base asset;
- quote asset;
- settlement asset;
- linear/inverse;
- perpetual/future;
- multiplier;
- listing/delisting lifecycle;
- canonical contract identity.

T0 must provide enough native metadata/source evidence to make that resolution possible.

If provider instrument metadata is itself an endpoint/file, it should be stored as evidence under an appropriate metadata acquisition class even if it does not become one of the eight market sensor families.

---

## 15. Timestamp handoff

T0 passes:

```text
provider_time_raw
provider_time_parsed?
provider_time_unit_assumption?
provider_publication_time?
response_observed_at
ingested_at
date_basis
```

Bloc 5 decides:

```text
effective_at
observed_at
canonical availability / PIT semantics
```

No silent timestamp reinterpretation.

---

## 16. Unit handoff

T0 preserves native units/lexical values.

Bloc 5 later decides normalized:

- OI native/base/USD;
- liquidation quote/base/USD;
- funding native interval and normalized equivalent;
- contract multiplier conversion;
- inverse-contract transformations.

If T0 source unit is unknown, pass `UNIT_UNVERIFIED`; do not guess.

---

## 17. Query service failure modes

```text
NO_MATCHING_EVIDENCE
REVISION_AMBIGUITY
INTEGRITY_BELOW_THRESHOLD
PROJECTION_SCHEMA_UNSUPPORTED
BLOB_MISSING
LINEAGE_INCOMPLETE
CATALOG_STALE
STORAGE_BACKEND_UNAVAILABLE
```

No empty DataFrame without a typed reason in infrastructure APIs.

---

## 18. Evidence pack for research claims

Later MECH/LF checkpoints may need a reproducible raw evidence slice.

Support export by query:

```text
provider/sensor/time/instrument selection
+ exact blobs
+ projections
+ manifests
+ checksums
+ query specification
```

This allows a result to be audited without exporting the entire lake.

---

## 19. Read-only doctrine

Raw evidence query APIs are read-only.

Mutation paths are restricted to:

- acquisition writer;
- projection builder;
- manifest append/version writer;
- integrity/recovery subsystem;
- explicit export/backup subsystem.

Research notebooks/scripts receive no delete/overwrite API.

---

## 20. Bloc 5 handoff questions

Bloc 5 planning must answer:

1. canonical instrument identity schema;
2. point-in-time listing/delisting map;
3. linear vs inverse semantics;
4. contract multipliers;
5. quote/settlement conversion;
6. timestamp/effective/observed semantics;
7. source-publication lag semantics;
8. OI unit normalization;
9. liquidation unit/side normalization;
10. funding interval normalization;
11. aggressor-side normalization;
12. book level/depth normalization;
13. native value preservation in T1;
14. row/event duplicate semantics;
15. canonical quality flags;
16. no-zero-fill behavior;
17. source revision PIT policy;
18. lineage from T1 to T0.

---

## 21. Handoff invariant

> Bloc 5 may reinterpret semantics through a versioned normalization method, but it may never lose the ability to show the exact T0 evidence from which that interpretation was produced.
