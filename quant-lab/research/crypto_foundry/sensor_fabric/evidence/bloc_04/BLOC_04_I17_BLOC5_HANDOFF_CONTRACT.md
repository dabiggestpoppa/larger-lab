# BLOC_04_I17_BLOC5_HANDOFF_CONTRACT

**Checkpoint:** SENSOR-B4-I17 — FINAL BLOC 4 -> BLOC 5 HANDOFF
**Frozen purpose:** *Document stable public interfaces, schema versions, known
limitations, and normalization-ready evidence contract.*
**Branch:** agent/crypto-sensor-fabric-build
**Start head:** `fb813728f32d6e518ed9911470388aec24c1e83e`
**Production source diff:** ZERO — this checkpoint documents and freezes; it
implements nothing.
**Scope:** I17 ONLY. Bloc 5 normalization implementation UNAUTHORIZED.
I18+ UNAUTHORIZED. Research FROZEN.

This document is **append-only** evidence. It rewrites no I01..I16R2 artifact and
no ratification record.

> **The batch is NORMALIZATION-READY EVIDENCE. It is NOT normalized science
> data.** Everything in this contract describes what Bloc 4 can *prove* about
> evidence it already holds. Nothing here supplies a canonical unit, a canonical
> asset, a notional, or a canonical event time — those are Bloc 5's to decide,
> and deciding them wrongly is unrecoverable.

---

## 1. `RawNormalizationBatch` — the complete field contract

22 public fields (pydantic `BaseModel`). Classification is normative.

### SOURCE_IDENTITY
| Field | Type | Notes |
|---|---|---|
| `provider` | str | required |
| `venue` | str | required |
| `sensor_family` | SensorFamily | required; `crypto_sensor_fabric.contracts.enums` |
| `native_instrument` | str | required |
| `source_granularity` | Granularity \| None | default `None`; `crypto_sensor_fabric.probes.enums` |
| `projection_schema_id` | str | required |
| `projection_schema_version` | str | required; strict semver MAJOR.MINOR.PATCH |
| `parser_version` | str | required |

### TIME_EVIDENCE
| Field | Type | Notes |
|---|---|---|
| `logical_time_range_start` | datetime | required |
| `logical_time_range_end` | datetime | required |

### UNIT_EVIDENCE
| Field | Type | Notes |
|---|---|---|
| `source_unit_evidence` | list[SourceUnitEvidence] | the truth-bound declarations |
| `source_unit_contract` | SourceUnitContract \| None | explicit marker; `None` = historical absence |

### LINEAGE
| Field | Type | Notes |
|---|---|---|
| `source_blob_refs` | list[str] | durable T0A digests, not paths |
| `acquisition_refs` | list[str] | durable acquisition ids |

### COVERAGE / QUALITY
| Field | Type | Default |
|---|---|---|
| `coverage_state` | CoverageState | `NOT_ATTEMPTED` |
| `known_gap_intervals` | list[str] | `[]` |
| `history_boundary` | str \| None | `None` |
| `quality_flags` | list[QualityFlagAcquisition] | `[]` |

### INTEGRITY / REVISION
| Field | Type | Default |
|---|---|---|
| `integrity_state` | IntegrityState | `UNVERIFIED` |
| `revision_state` | RevisionState | `UNKNOWN_REVISION` |

### DESCRIPTOR_ONLY
| Field | Type | Notes |
|---|---|---|
| `batch_id` | str | descriptor |
| `raw_rows_or_reader` | str | a descriptor/handle string, e.g. `descriptor://proj-r1`; its interpretation belongs to the registered schema, never to the batch |

**DOWNSTREAM_NOT_CANONICAL — deliberately absent:** canonical asset, canonical
unit, notional, base/quote interpretation, `effective_at`, canonical PIT
timestamps, normalized features. Their absence is the contract, not a gap.

---

## 2. Source identity law

`provider`, `venue`, `sensor_family`, `native_instrument`,
`source_granularity`, `projection_schema_id`, `projection_schema_version`,
`parser_version` are **evidence**. Bloc 5 may use, group by and reconcile them.

Bloc 5 **must not derive storage paths** from them. They identify *what was
acquired and how it was projected*; they say nothing about where bytes live.

---

## 3. Timestamp handoff law

### PRESERVED SOURCE / ACQUISITION FACTS (reachable through the public contract)
| Field | Surface |
|---|---|
| `logical_time_range_start` / `logical_time_range_end` | `RawNormalizationBatch` |
| `logical_time_start` / `logical_time_end` | `RawEvidenceResult` |
| `requested_start` / `requested_end` | `AcquisitionRecord` |
| `actual_start` / `actual_end` | `AcquisitionRecord` (nullable = unknown, not epoch) |
| `request_started_at` | `AcquisitionRecord` |
| `response_observed_at` | `AcquisitionRecord` |
| `ingested_at` | `AcquisitionRecord` |
| `date_basis` | `PartitionManifest` (EVENT_TIME / PROVIDER_FILE_DATE / SNAPSHOT_TIME / UNKNOWN) |
| `logical_start` / `logical_end` / `acquired_before` / `observed_before` | `RawEvidenceQuery` (filters) |
| `min_provider_time` / `max_provider_time` | `RawProjectionArtifact` (nullable artifact bounds) |

### BLOC 5 CANONICAL DECISIONS (Bloc 4 does not supply them)
`effective_at`; a canonical `observed_at` if it differs from the preserved
acquisition fact; provider-time interpretation where unresolved; all PIT
semantics.

**I17 does not introduce these fields anywhere.**

### Structurally absent time facts — measured, not assumed
Verified absent from every public handoff model at the start head:
`provider_time_raw`, `provider_time_parsed`, `provider_time_unit_assumption`,
`provider_publication_time` — plus `effective_at` and `canonical_observed_at`.

Consequence: **when provider-time facts are unavailable, Bloc 5 must work from
the available acquisition and logical evidence and must label the result as
derived**, not as provider-asserted. Do not imply these fields exist.

---

## 4. Unit contract — the current final form

Three independent vocabularies. **Do not blur them.**

### 4.1 `SourceUnitState` — the frozen pair
| Member | Meaning |
|---|---|
| `VERIFIED_NATIVE` | a declared lexeme, **proven** against the committed rows (§4.4) |
| `UNIT_UNVERIFIED` | no verified static native-unit evidence |

### 4.2 `SourceUnitVariability` — how the declaration behaves across rows
| Member | Paired state | Meaning |
|---|---|---|
| `STATIC_VERIFIED` | `VERIFIED_NATIVE` | one lexeme proven invariant across the committed evidence |
| `ROW_NATIVE` | `UNIT_UNVERIFIED` | per-row / per-level native units live at a durable location |
| `UNIT_UNVERIFIED` | `UNIT_UNVERIFIED` | explicit unknown |

An absent `variability` preserves the I16R1 state/lexeme pair semantics exactly.

### 4.3 `SourceUnitContract` — the explicit marker
| Marker | Meaning |
|---|---|
| `NO_UNIT_FIELDS` | this schema **explicitly declares** it has no unit-bearing field |
| `UNIT_EVIDENCE_DECLARED` | this schema explicitly governs unit evidence (non-empty) |
| *(marker absent)* | `HISTORICAL_UNIT_CONTRACT_ABSENT` — a **third, distinct** state |

### 4.4 `VERIFIED_NATIVE` is truth-bound, not merely declared
`VERIFIED_NATIVE` is proven **at T0B commit time**, after the Arrow table is
built and schema equality established, **before durable publication**:

* the declared lexeme must equal every committed non-null value at the declared
  field or structural path;
* **mismatch**, **mixed** distinct lexemes and an **all-null** location are typed
  refusals (`ProjectionUnitEvidenceConflict`, conflict classes `MISMATCH` /
  `MIXED` / `ALL_NULL`);
* a refusal happens **before durable publication** — no projection is created
  and no handoff is exposed;
* a claim is **never silently downgraded** to `UNIT_UNVERIFIED`;
* null law: null is absence of a value, not disagreement. Partial nulls commit
  when every non-null value matches; an all-null column refuses.

**Bloc 5 may rely on this proof.** If a batch carries `VERIFIED_NATIVE("BTC")`,
the committed rows behind that projection all said `BTC` at commit time.

### 4.5 `ROW_NATIVE` — Bloc 4 says *where*, not *what*
The provider-native unit is carried by each row or nested location. Bloc 4 marks
the durable location and **fabricates no batch-level lexeme**. `field_path` is a
**structural tuple**, e.g. `("bids", "item", "quantity_unit")` — never a dotted
string. Bloc 5 receives the location and performs PIT normalization later.

### 4.6 `UNIT_UNVERIFIED` — explicit unknown
It means Bloc 4 has no verified static native-unit evidence. It does **NOT**
mean unitless; it does **NOT** license guessing from row bytes, provider name,
symbol parsing or raw-byte search; and it does **NOT** license downstream
canonicalization without evidence.

### 4.7 `NO_UNIT_FIELDS` vs historical absence
The distinction **survives the handoff** and must be preserved by Bloc 5: an
explicit `NO_UNIT_FIELDS` marker is a positive declaration; an absent marker is
historical absence. Never merge them.

---

## 5. Eight-family unit matrix (frozen)

| Family | Unit-bearing semantic field | Shape | Expected contract | Downstream responsibility |
|---|---|---|---|---|
| `MECHANICAL_TRADE` | `quantity_unit` (top-level) | static scalar, constant | `VERIFIED_NATIVE` + `STATIC_VERIFIED` | canonical unit + notional |
| `MECHANICAL_BOOK_METRIC` | `metric_unit` (top-level, e.g. `BPS`) | static scalar, constant | `VERIFIED_NATIVE` + `STATIC_VERIFIED` | metric semantics; unit is dimensional (`BPS`), not an asset |
| `MECHANICAL_BOOK_SNAPSHOT` | `bids[]/asks[].quantity_unit` | **row-varying, nested per level** | `UNIT_UNVERIFIED` + `ROW_NATIVE` + `field_path` | per-level unit interpretation |
| `MECHANICAL_OPEN_INTEREST` | `native_unit` (frozen vocabulary `BASE_ASSET, CONTRACTS, OTHER, QUOTE_ASSET, USD`) | static scalar | `VERIFIED_NATIVE` + `STATIC_VERIFIED` | contract-multiplier conversion |
| `MECHANICAL_LIQUIDATION` | `quantity_unit` (nullable) | optional / may be all-null | `VERIFIED_NATIVE` when proven; an all-null column **refuses** | quantity normalization |
| `MECHANICAL_FUNDING` | none (dimensionless rate; `funding_interval_seconds` describes the interval) | no unit-bearing fields | `NO_UNIT_FIELDS` | rate semantics, not unit conversion |
| `MECHANICAL_BASIS` | none | no unit-bearing fields | `NO_UNIT_FIELDS` | basis semantics |
| `MECHANICAL_POSITIONING` | none (ratios/counts; `population_definition` is not a unit) | no unit-bearing fields | `NO_UNIT_FIELDS` | population semantics |

**Book-snapshot resolution is `ROW_LEVEL_NESTED_SUPPORT_REQUIRED`.** The flat
alternative is **NOT PROVEN**: no production book projection flattens per-level
unit evidence into a top-level column.

---

## 6. Production schema population — carried prominently

```
BLOC_04_UNIT_CONTRACT_CAPABILITY = PROVEN
PRODUCTION_SCHEMA_POPULATION     = ZERO_AT_BLOC4_BOUNDARY
```

Measured by exhaustive `src/**/*.py` search: **0** production
`ProjectionSchemaDefinition` constructions and **0** registered schemas
carrying `source_unit_evidence`; every construction site is under `tests/`
(verdict `CAPABILITY_PROVEN_POPULATION_ZERO`).

Bloc 4 proves the **generic storage/handoff contract**. No production code
currently registers a projection schema. This is **not hidden** and is **not**
blamed on offline fixtures: the eight-family proofs above exercise *committed
supported-family fixtures* through registration -> commit -> unit truth
validation -> handoff -> public consumer, with **network_calls = 0**.

This is **not** a G4-13 failure. The frozen G4-13 wording binds the **public
handoff surface** (capability), not a registration census.

---

## 7. Lineage contract

```
RawNormalizationBatch
  -> projection identity   (projection_id, schema id/version, parser_version, projection_sha256)
  -> acquisition refs      (acquisition_refs -> AcquisitionRecord)
  -> source blob refs      (source_blob_refs -> T0A digest)
  -> revision evidence     (revision_state, RevisionResolver, SourceRevision)
  -> manifest evidence     (PartitionManifest, ProjectionLineage)
  -> T0A exact bytes       (RawArtifactReader.open_bytes/stream_bytes/verify)
```

* **Authoritative IDs:** `projection_id`, `acquisition_id`,
  `blob_sha256`, `partition_manifest_id`, `source_revision_key`,
  `projection_sha256`, `manifest_sha256`.
* **Public resolution:** `RawProjectionReader.get_artifact/projection_metadata/
  resolve_lineage`, `PartitionManifestRepository.get_manifest/get_current_manifest/list_manifest_versions`,
  `AcquisitionRepository.get_acquisition/list_acquisitions_for_blob`,
  `RawArtifactReader.metadata/verify`, `RevisionResolver.resolve`.
* **Integrity proof points:** T0A content hash, projection/schema binding,
  manifest reference, unit claim validation at T0B, lineage validity
  (`ProjectionLineageResolver.validate_projection_ref`), revision identity.

**Bloc 5 must carry this lineage into every normalized output.** A normalized
row that cannot name its projection, acquisition and blob did not come from
this contract.

---

## 8. Revision contract

`RawEvidenceQuery.revision_policy` (default **`ERROR_ON_AMBIGUITY`**):

| Policy | Use when |
|---|---|
| `ERROR_ON_AMBIGUITY` | **default**; PIT normalization must leave this on unless a policy decision is recorded |
| `FIRST_SEEN` | the first observation is authoritative for the PIT window |
| `LATEST_SEEN` | the latest observation is authoritative — a deliberate, recorded choice |
| `EXACT_REVISION` | paired with `exact_revision_number`; pin one revision |
| `ALL` | every revision is in scope; the caller must disambiguate downstream |
| `PROVIDER_DECLARED_CANONICAL` | only when the provider declares a canonical revision |

**Do not choose a default silently.** PIT normalization must make its resolution
policy explicit and recorded alongside the output. `RevisionState.SOURCE_MUTATION`
must never be normalized away unnoticed, and `UNKNOWN_REVISION` is never
permission to assume the latest.

---

## 9. Missingness contract

Distinct states on the public surface:

* `RawEvidenceQueryService` -> `QueryOutcome(results, no_matching_evidence, reason)`
  — a **typed absence**, not an empty frame.
* `NoMatchingEvidence` — typed error/refusal for an impossible query.
* `CoverageState`: `COMPLETE_SOURCE_BOUNDARY`, `PARTIAL`, `KNOWN_GAP`,
  `EMPTY_CONFIRMED`, `NOT_ATTEMPTED`, `FAILED`, `ACCESS_BLOCKED`,
  `HISTORY_UNAVAILABLE`, `QUARANTINED`, `REVISION_CONFLICT`.
* `PartitionManifest.gap_count` + `RawNormalizationBatch.known_gap_intervals`
  + `history_boundary` quantify absence.
* `DateBasis.UNKNOWN` keeps date semantics honest.

**Rule: NONE never becomes numeric zero.** `EMPTY_CONFIRMED` is a positive
finding; `NOT_ATTEMPTED` is not empty; `HISTORY_UNAVAILABLE` is not zero volume;
`KNOWN_GAP` must not be interpolated over. There is no empty-DataFrame ambiguity
anywhere on this surface.

---

## 10. Integrity contract

**Bloc 5 may rely on:** T0A content hash verified
(`RawArtifactReader.verify`); projection/schema binding (exact schema equality
at commit); manifest references; unit claim validation (T0B, §4.4); lineage
validity; revision identity; `IntegrityState` never silently upgrading.

**Bloc 5 must still validate itself:** the correctness of its own
canonicalization, cross-source reconciliation, and that every normalized row
remains traceable to the evidence it claims.

`PROVIDER_HASH_VERIFIED` is strictly stronger than `LOCAL_HASH_VERIFIED` —
never collapse the two. `integrity_minimum` on the query is the supported way
to filter.

---

## 11. Query contract

`RawEvidenceQuery` (17 fields): `providers`, `venues`, `sensor_families`,
`native_instruments`, `source_granularities`, `logical_start`, `logical_end`,
`acquired_before`, `observed_before`, `integrity_minimum` (default
`UNVERIFIED`), `coverage_states`, `revision_policy` (default
`ERROR_ON_AMBIGUITY`), `include_t0a` (default `True`), `include_t0b` (default
`False`), `projection_schema_ids`, `limit`, `exact_revision_number`.

* Time bounds are **logical** bounds plus separate acquisition/observation bounds.
* Source filters are explicit lists; an empty list means unconstrained.
* Projection selection is by `projection_schema_ids`.
* `limit` is a bound, not a pagination contract — there is no cursor API.
* **Result ordering is not a guaranteed contract of `execute()`.** When ordering
  matters, use `RawReplayCursor.replay(query, order_by=...)` with an explicit
  `ReplayOrder` (`ACQUISITION_ORDER` — the default and an *ingestion* order —
  `PROVIDER_EVENT_TIME`, `SOURCE_ORDER`).
* **No hidden filesystem assumptions.** Typed refusals
  (`CatalogStale`, `LineageIncomplete`, `IntegrityBelowThreshold`,
  `QueryBlobMissing`, `ProjectionSchemaUnsupported`, `ReplayOrderUnavailable`,
  `StorageBackendUnavailable`, `RevisionAmbiguity`) surface conditions instead of
  silently returning less data.

---

## 12. Path-independence contract

Bloc 5 **must not know**: blob paths, manifest paths, catalog directory layout,
the DuckDB file path, or any projection storage layout. All access goes through
public Bloc 4 interfaces. This is verified, not merely intended: G4-13 consumer
restrictions are public-storage-only, no provider-adapter imports, no filesystem
traversal, no private storage maps, no absolute root assumptions.

`projection_uri` and `raw_rows_or_reader` are **opaque descriptors**. Parsing
them is prohibited.

---

## 13. DuckDB law

`rebuild_duckdb_catalog` / `ReadOnlyDuckDBCatalog` exist in
`storage.duckdb_catalog` but are **deliberately NOT exported**: they are not part
of the public handoff surface.

> **DuckDB is disposable discovery/query acceleration, never durable source of
> truth.** Bloc 5 cannot rely on DuckDB as evidence authority and must not depend
> on these symbols. They are intentionally unreachable through the public package.

---

## 14. Postgres law

> **Postgres is operational metadata/state only — never bulk raw evidence
> authority.** Every table is reconstructible from durable sources via
> `reconstruct_snapshot`; losing the database loses no evidence.

* `TABLE_SCHEMAS` is the sole table-shape authority; `SCHEMA_VERSION` versions it.
* `redact_dsn` keeps credentials out of logs and evidence.
* **Carry-forward limitation:** G4-10's final acceptance included a **no-live-DSN
  environment limitation** (`SENSOR_FABRIC_POSTGRES_DSN` and `DATABASE_URL` both
  unset); the gate rested on the current-head contract test plus accepted prior
  I11 live evidence. **No new live database run is claimed by I17.**

---

## 15. Export / restore law (portability)

`EvidencePackExporter.export_query` -> `EvidencePackVerifier.verify_pack` ->
`EvidencePackRestorer.restore_pack(pack_root, destination, source_revision_keys)`.

* A pack restores into a **new, unrelated, empty root**;
  `RestoreDestinationNotEmpty` is raised otherwise and must not be worked around.
* Identity, hash, query, revision and lineage parity are preserved, so a restored
  root answers the same queries.
* **No source-root path assumptions** travel with the pack.
* `PACK_SCHEMA_VERSION` is `"1"` and must match **exactly**; anything else raises
  `PackUnsupportedVersion`. There is no cross-version migration.

This is the reproducibility guarantee a Bloc 5 pipeline can rely on.

---

## 16. Bloc 3 handoff law (upstream causality)

```
FetchBatch / RawPayloadEnvelope -> T0 persistence -> manifest durability -> checkpoint advance
```

`StorageJobStatus` encodes the order: `ACQUIRING` -> `RAW_STAGED` ->
`RAW_COMMITTED` -> `PROJECTION_PENDING` -> `PROJECTION_COMMITTED` ->
`MANIFEST_COMMITTED` -> `CHECKPOINT_ADVANCED` -> `COMPLETE`.

**A checkpoint never precedes its durable manifest commit.** Bloc 5 receives only
already-accepted durable evidence, so it never re-implements durability. Note
`Bloc3StorageHandoff` is **not** exported: upstream causality is observable
through the exported job vocabulary and `DurableJobStateRepository`, which is
all a downstream consumer needs.

---

## 17. Security / hardening truths carried forward

* Secret-safe metadata (`SecretBearingAcquisitionMetadata`, `redact_dsn`).
* Path containment (`resolve_under_root`, `escape_path_segment`) and static
  symlink protection.
* TOCTOU custody and corruption fail-closed (`BlobIntegrityError`,
  `ExistingBlobIntegrityConflict`, `ProjectionCorruption`, catalog-corruption
  errors).
* Resource bounds (below).

**Known limitation, recorded exactly:** POSIX runtime TOCTOU was **structurally
verified** (`O_DIRECTORY`/`O_NOFOLLOW` per component, `dst_dir_fd` to `os.link`)
but **NOT runtime-measured on this Windows host**:
`POSIX_RUNTIME_TOCTOU = NOT_MEASURED_ON_THIS_HOST`. No POSIX runtime evidence is
fabricated, and I17 makes no new claim about it.

---

## 18. Resource contract — guardrails, not semantic limits

**Configurable operational guardrails** (limits you configure, with accepted
priority behavior): hash/write chunk size; query result bound; export ceilings
(`max_objects` 1,000,000; `max_total_bytes` 1 TiB; `max_object_bytes` 8 GiB;
`max_manifest_bytes` 64 MiB); quota/watermark policy (`StorageQuotaState`,
`StoragePriority` P0-P3, `DiskPressure` NORMAL/WATCH/CONSTRAINED/CRITICAL —
at CRITICAL optional P1-P3 are blocked before P0, and P0 proceeds with WARN;
T0A auto-delete count = 0); revision-chain scale.

**Measured scale** (accepted evidence): 10,000 actual manifest rows scanned by
production reader code with peak 56.2 MB; 1 GiB-equivalent streaming hash peak
1.05 MB; 64 MiB-equivalent T0A streaming write peak 555.9 KB with exact SHA
identity; 150 projections rebuilt in 3.61 s.

**Semantic limits: none.** This is why the Bloc 4 verdict is
`PASS_BLOC_04_IMPLEMENTED` with **no data-volume suffix**.

---

## 19. Normalization ownership and prohibitions

The normative ownership table and the hard "do not infer" registry are
frozen as separate artifacts:

* `BLOC_04_I17_NORMALIZATION_OWNERSHIP.json`
* `BLOC_04_I17_DOWNSTREAM_PROHIBITIONS.json`

Summary: **Bloc 4 owns** exact raw evidence, acquisition facts, public
projections, source-unit evidence, lineage, revision truth, missingness/coverage
truth and integrity. **Bloc 5 owns** canonical asset identity, canonical units,
quantity conversion, notional normalization, base/quote interpretation,
`effective_at`, canonical PIT timestamps, normalized science features and
cross-provider semantic reconciliation. **There is no overlap.**

---

## 20. Handoff contract status (frozen)

```
BLOC_04_TO_BLOC_05_HANDOFF_CONTRACT = DOCUMENTED
NORMALIZATION_READY_EVIDENCE        = TRUE
BLOC_05_NORMALIZATION_IMPLEMENTED   = FALSE
PRODUCTION_SCHEMA_POPULATION        = ZERO_AT_BLOC4_BOUNDARY
```

`NORMALIZATION_READY_EVIDENCE = TRUE` means: the evidence Bloc 4 emits is
sufficient for a downstream PIT normalization **to be specified and
implemented** without filesystem knowledge and without guessing units. It does
**not** mean any normalized data exists.

**Companion artifacts:**
`BLOC_04_I17_PUBLIC_INTERFACE_MATRIX.json`,
`BLOC_04_I17_SCHEMA_VERSION_MATRIX.json`,
`BLOC_04_I17_KNOWN_LIMITATIONS.json`,
`BLOC_04_I17_NORMALIZATION_OWNERSHIP.json`,
`BLOC_04_I17_DOWNSTREAM_PROHIBITIONS.json`,
`BLOC_04_I17_HANDOFF_EXAMPLE.md`.

No normalization was implemented. Research remains FROZEN. STOP.