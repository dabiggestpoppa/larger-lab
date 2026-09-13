# BLOC 5 — T1 LINEAGE, DUPLICATES, QUALITY & STORAGE GENERATIONS

**Planning status:** COMPLETE DRAFT FOR FREEZE  
**Implementation status:** NOT STARTED  
**Purpose:** define how canonical T1 observations preserve complete T0 lineage, handle duplicate/revised source observations, expose quality states, and remain reproducible across normalization generations.

---

## 1. T1 is rebuildable, not disposable

T1 is derived from immutable T0 evidence.

Therefore T1 can be regenerated when:

- identity mappings improve;
- provider semantics are corrected;
- normalization formulas change;
- PIT availability rules improve.

But regeneration must be **versioned**.

Hard rule:

> Rebuildability does not justify silent overwrite.

---

## 2. Complete lineage chain

Every T1 observation must be traceable through:

```text
T1 observation
↓
normalization generation
↓
T0B projection row(s) / raw batch
↓
AcquisitionRecord
↓
EvidenceBlob SHA256
```

If a canonical field used auxiliary conversion data:

```text
T1 field
↓
ConversionLineage
↓
reference price / FX / contract terms / identity evidence
```

No orphan canonical values.

---

## 3. Lineage objects

### `T1Lineage`

```text
t1_record_id
normalization_generation
raw_projection_refs[]
acquisition_refs[]
evidence_blob_hashes[]
identity_evidence_refs[]
semantic_evidence_refs[]
conversion_lineage_refs[]
code_version
config_version
```

### `FieldLineage`

Used when individual canonical fields require separate derivation.

```text
field_name
source_fields[]
methodology_id
methodology_version
input_record_refs[]
```

This is especially important for normalized OI, liquidation notional, funding equivalents, and inverse-contract conversions.

---

## 4. Deterministic T1 record identity

`t1_record_id` should be reproducible from a deterministic identity key.

Conceptually include:

```text
sensor_family
provider
venue
contract_instance_id
native event/snapshot identity
source revision
normalization generation
```

Do not derive record ID solely from normalized numeric values.

A corrected value should not accidentally collide with the original record.

---

## 5. Duplicate taxonomy

Duplicate-looking rows fall into different classes.

```text
EXACT_SOURCE_DUPLICATE
SAME_PROVIDER_SAME_EVENT_DIFFERENT_ACQUISITION
REST_ARCHIVE_DUPLICATE
LIVE_ARCHIVE_DUPLICATE
REVISION
POSSIBLE_DUPLICATE
NOT_DUPLICATE
NO_SAFE_DEDUPE_KEY
```

These must not be collapsed into one generic `drop_duplicates()` operation.

---

## 6. Event identity strength

Each sensor/provider mapping declares its dedupe strength.

```text
HARD_PROVIDER_ID
HARD_SEQUENCE_KEY
COMPOSITE_EXACT_KEY
SOFT_FINGERPRINT
NO_SAFE_DEDUPE
```

### `HARD_PROVIDER_ID`

Provider gives durable unique trade/event ID.

### `COMPOSITE_EXACT_KEY`

Provider guarantees a documented tuple uniquely identifies an event.

### `SOFT_FINGERPRINT`

Heuristic candidate only.

Soft fingerprints may flag likely duplicates but may not destructively remove evidence without stronger proof.

---

## 7. REST/archive/live overlap

The same venue event may arrive from:

- live WebSocket;
- REST history;
- daily archive;
- monthly archive.

Policy:

1. preserve every T0 acquisition;
2. create one canonical T1 economic event when hard identity proves sameness;
3. attach all confirming source lineage;
4. record disagreement if values differ;
5. classify differing payload as revision/semantic conflict rather than choosing silently.

This converts redundant acquisition into stronger evidence rather than duplicated events.

---

## 8. Cross-provider events are never deduped by default

Kraken and Gate reporting similar liquidation timestamps are different venue events.

Coinalyze reporting a Binance venue value may be evidence about the same venue observation, but dedupe/fusion requires explicit venue/source semantics.

Never dedupe merely because:

```text
timestamp + symbol + value
```

look similar.

---

## 9. Revision model

When the same hard economic event changes under later source evidence:

```text
T1RevisionChain
  original_t1_record_id
  revised_t1_record_id
  revision_reason
  first_known_at
  source_revision_ref
```

Revision does not delete original.

Strict replay can select `AS_KNOWN_THEN`; retrospective research can select a later verified revision.

---

## 10. Quality model

Quality belongs to dimensions rather than one magical score.

Proposed `T1Quality`:

```text
identity_quality
time_quality
semantic_quality
unit_quality
lineage_quality
source_integrity_quality
coverage_quality
replay_quality
```

Each dimension can be:

```text
VERIFIED
ACCEPTABLE_WITH_FLAGS
PARTIAL
UNKNOWN
BLOCKED
QUARANTINED
```

A later Bloc 6 may derive operational sensor-health scores, but Bloc 5 retains the component truth.

---

## 11. Canonical quality flags

Minimum normalization flags:

### Identity

```text
IDENTITY_ALIAS_USED
IDENTITY_LIFECYCLE_BOUNDARY
IDENTITY_AMBIGUOUS
IDENTITY_TERMS_UNVERIFIED
```

### Time

```text
TIME_SEMANTICS_UNVERIFIED
TIME_ARCHIVE_RECONSTRUCTION
TIME_MARKET_AVAILABILITY_UNKNOWN
PIT_REVISION_UNCERTAIN
```

### Semantics/units

```text
SEMANTICS_UNVERIFIED
UNIT_NATIVE_ONLY
UNIT_CONVERSION_BLOCKED
STABLECOIN_CONVERSION_UNAVAILABLE
REFERENCE_PRICE_UNAVAILABLE
```

### Event/dedupe

```text
DUPLICATE_CONFIRMED
DUPLICATE_CANDIDATE
REVISION_PRESENT
SOURCE_DISAGREEMENT
NO_SAFE_DEDUPE_KEY
```

### Books

```text
BOOK_SEQUENCE_GAP
BOOK_PARTIAL_ONLY
BOOK_DEPTH_UNKNOWN
```

### Lineage

```text
LINEAGE_COMPLETE
LINEAGE_PARTIAL
LINEAGE_BROKEN
```

`LINEAGE_BROKEN` is blocking.

---

## 12. Missingness vocabulary

T1 preserves Bloc 1/4 missing reasons and adds normalization-specific reasons.

```text
NOT_REPORTED
NOT_SUPPORTED
NOT_YET_LISTED
DELISTED
HISTORY_UNAVAILABLE
PROVIDER_EMPTY
ACCESS_BLOCKED
SOURCE_GAP
IDENTITY_BLOCKED
TIME_BLOCKED
SEMANTICS_BLOCKED
CONVERSION_BLOCKED
QUARANTINED
```

No generic `missing=true` should erase the reason.

---

## 13. T1 generation model

A T1 build is identified by:

```text
T1Generation
  generation_id
  created_at
  code_commit
  identity_registry_version
  semantic_registry_version
  methodology_registry_version
  time_semantics_version
  source_revision_mode
  input_manifest_refs[]
```

A generation is immutable after successful publication.

A new methodology creates a new generation.

---

## 14. T1 storage layout

T1 storage is analytical and provider/venue aware.

Recommended logical partitioning:

```text
t1/
  sensor_family=<...>/
  venue=<...>/
  year=YYYY/
  month=MM/
  [day=DD when volume requires]
```

Contract/instrument remains a column rather than always a filesystem partition to avoid pathological small-file counts.

High-volume trades/books may add bucketing after measurement.

No storage path becomes the semantic identity; manifests/catalogs remain authoritative.

---

## 15. T1 format

Default:

```text
Parquet + Arrow-compatible schemas
```

Compression:

```text
zstd by default, configurable after benchmarks
```

Schema metadata should include generation/methodology references.

No CSV as canonical storage.

---

## 16. Atomic T1 publication

A generation or partition should become visible only after:

1. normalization succeeds;
2. schema validates;
3. lineage validates;
4. row counts/checksums recorded;
5. invariant tests pass;
6. files are atomically promoted;
7. generation manifest is committed.

Partial staging files remain invisible to canonical queries.

---

## 17. T1 manifest

`T1PartitionManifest`:

```text
generation_id
sensor_family
venue
partition_boundary
row_count
first_event_at
last_event_at
source_provider_set[]
contract_count
quality_flag_counts
replay_eligible_count
retrospective_only_count
checksum
input_manifest_refs[]
created_at
```

This supports coverage audits without scanning all data.

---

## 18. Canonical query modes

Planned T1 query API must require explicit choices for ambiguous dimensions.

```text
revision_mode
replay_mode
quality_minimum
include_native_only
include_revisions
```

Strict defaults:

```text
revision_mode = ERROR_ON_AMBIGUITY or AS_KNOWN_THEN when replaying
quality_minimum = no blocking flags
```

Do not silently select latest corrections.

---

## 19. Research-safe query boundary

Research code should query:

```python
query_t1(sensor_family, ...)
```

not:

```python
read_parquet(".../binance/...")
```

The query layer applies:

- identity rules;
- generation selection;
- revision mode;
- quality filters;
- replay eligibility.

This prevents notebooks from accidentally bypassing PIT constraints.

---

## 20. Quarantine

Rows can be retained but quarantined for:

```text
schema failure
identity ambiguity
lineage break
impossible units
invalid side mapping
book sequence corruption
source revision conflict
```

Quarantine records include reason, evidence refs, and required remediation.

No quarantined row enters standard canonical queries.

---

## 21. Audit outputs

Every normalization run should emit:

```text
normalization_report.json
lineage_report.json
duplicate_report.json
quality_report.json
replay_eligibility_report.json
partition_manifest.json
```

These are evidence for Bloc 6 and final validation.

---

## 22. Reproducibility requirement

Given:

- same T0 evidence manifests;
- same code commit;
- same registries;
- same methodology versions;
- same revision mode;

T1 generation output must be deterministic modulo explicitly documented nondeterministic metadata such as wall-clock build timestamp.

Row ordering and checksums should be canonicalized for reproducibility tests.

---

## 23. Invariants

1. every T1 row has complete T0 lineage;
2. cross-venue records are never deduped by similarity;
3. confirmed same-event multi-path evidence can collapse economically while preserving all source refs;
4. soft fingerprint does not destructively dedupe;
5. revisions append;
6. generation is immutable after publish;
7. blocking quality states fail closed;
8. canonical queries do not bypass generation/revision/PIT rules;
9. no zero-fill;
10. same inputs/config produce deterministic T1 outputs.

---

## 24. Handoff

The next Bloc 5 document defines the complete **acceptance-test program, provider fixture matrix, staged implementation commits, and Bloc 6 handoff**.
