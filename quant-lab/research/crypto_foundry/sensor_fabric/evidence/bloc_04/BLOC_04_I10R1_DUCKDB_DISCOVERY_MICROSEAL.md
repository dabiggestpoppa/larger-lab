# SENSOR-B4-I10R1 — DUCKDB DISCOVERY MICROSEAL

Checkpoint: SENSOR-B4-I10R1 (SCHEMA CONTRACT + MEASURED EVIDENCE + DISCOVERY COST MICROSEAL)
Branch: agent/crypto-sensor-fabric-build
Start HEAD: f400f6edb762e77d30bb4629d423f0afdadb2c51 (SENSOR-B4-I10D-R1)
Remote main at start: 7c7816f382947bbc8a1f2154435fc436f2428fa8
Operator review: I10 NOT ratified; I11 Postgres UNAUTHORIZED; research frozen.

## 1. Scope discipline

Superseded I10A findings were explicitly NOT chased: the final I10 chain
already ships public rebuild/read-only APIs, schema metadata, a read-only
consumer, and temp-file + `os.replace` publication. Root-level
`src/crypto_sensor_fabric/storage/duckdb_catalog.py` is absent at final HEAD
(verified at the start gate). The historical I10A bootstrap defects
(`.bu_tmp/i10a_duckdb_catalog.py` audit) belong to deleted staging and are
documented, not repaired here. `_create_table` is an internal fresh-candidate
builder and was NOT made publicly idempotent.

## 2. Defect A — first-row schema authority (REPAIRED, I10R1A)

Pre-repair reproduction (v_t0_storage_usage, PARTITION row first with
`stored_bytes=None`): `PRAGMA table_info` showed `stored_bytes VARCHAR`
(the later T0B row's integer was even stored as the string '12345').
Empty datasets used a different, hard-coded DDL — one logical view, two
possible physical schemas.

Repair: ONE ordered contract `VIEW_SCHEMAS` (8 views × exact
(name, SQL type) pairs) now drives CREATE TABLE, INSERT column order, and
pre-publication validation for empty, single-row, many-row, and
nullable-first-row datasets alike. SQL types are never inferred from runtime
values; dict insertion order never shapes a table; identifiers are quoted
with a fixed helper.

## 3. Strict row shape (REPAIRED, I10R1A)

Pre-repair: a later row missing an expected field was silently NULL-backfilled
via `row.get(key)` (reproduced: `KNOWN_GAP` gap row with NULL detail).

Repair: `_require_contract_row` enforces EXACT key-set equality against the
contract; missing keys and extra keys raise the new typed
`DuckDBCatalogShapeCorrupt`; None is accepted only in columns nullable by
frozen discovery semantics (durable `gap_count: int | None`, optional
`supersedes_manifest_id`, optional `action_kind`, acquisition convenience
fields, storage-usage dimensions a record does not own); wrong scalar/list
types are refused before DuckDB could coerce them into plausible data.

## 4. Build transaction + full pre-publication validation (REPAIRED, I10R1A)

The candidate catalog is now built inside one explicit `BEGIN TRANSACTION` …
`COMMIT` (metadata, tables, rows, views). On failure: ROLLBACK, close,
temporary file deleted, previously published catalog byte-identical. The
temporary-file + `os.replace` publication design was preserved (it protects
the published file; the transaction makes the candidate itself coherent).

`_validate_database` now proves before publication: exactly one
`catalog_metadata` row, `schema_version == "1.0"`,
`role == rebuildable_discovery_non_authoritative`, all eight views present,
and per-view exact column names, order, and SQL types against
`VIEW_SCHEMAS`, plus expected row counts. A catalog whose rows are right but
schema is wrong can no longer be published.

## 5. Read-only open refuses stale catalogs (REPAIRED, I10R1A/B)

`ReadOnlyDuckDBCatalog.__init__` validates `catalog_metadata`: existence,
exactly one row, `schema_version == CATALOG_SCHEMA_VERSION`, and
`data_root_role == rebuildable_discovery_non_authoritative`. Attacks proven
refused (typed `DuckDBCatalogVersionError`, before any discovery use):
missing metadata, duplicate metadata rows, older version, future/unknown
version, wrong role. No silent migration.

## 6. Defect B — storage-usage dimension collapse (REPAIRED, I10R1B)

Pre-repair reproduction: providerA/SENSOR_X and providerB/SENSOR_Y T0B rows
sharing state collapsed into ONE row attributed to whichever row initialized
the bucket (providerA).

Repair: aggregates are keyed by the FULL dimension tuple present in the
output (evidence_class, integrity/state, provider, sensor_family,
storage_priority, universe_tier). T0A blob-level rows keep NULL
provider/sensor — identity the durable blob record does not own is never
falsely attributed; NULL is preferred over false attribution. Multi-provider
and multi-sensor separation plus object/byte reconciliation are pinned by
tests and measured matrix rows.

## 7. Defect C — rebuild read all T0A bytes (REPAIRED, I10R1B)

Pre-repair: `_read_blobs` called `LocalBlobStore.verify_blob` for EVERY blob
— stored bytes read, hashed, source decoded/decompressed, H1 recomputed
(reproduced: 1 call per blob; 16 MiB blob ⇒ full payload read during
"discovery").

Repair: default rebuild reads ZERO payload bytes. Discovery validates
metadata-level physical facts only — safe resolved object key, object
exists, regular file, stored size matches durable metadata — and uses the
durable `integrity_state` as discovery metadata. Guarded tests prove
`verify_blob` and `_decode_stats` are NEVER invoked by default rebuild, and
an 8 MiB blob is discovered without reading a single payload byte. Missing
physical blobs and stored-size divergence still fail typed (metadata-level
checks retained). Full H1 verification remains owned by the existing
integrity/recovery machinery as an explicit operation.

## 8. Defect D — recovery actions not semantically validated (REPAIRED, I10R1C)

Pre-repair reproduction: a committed action stripped of
`recovery_run_id/object_type/object_id/problem/resolution` became a
plausible all-NULL discovery row.

Repair: `_read_quarantine` enforces the authoritative I08 contract —
nonempty bound id, nonempty run/object/object_id/problem/resolution — and
re-derives the logical id with `recovery.action_identity` (I08 §7); identity
divergence fails typed. Malformed durable recovery evidence now raises
`DuckDBCatalogShapeCorrupt`; it never becomes NULL discovery data.

## 9. Defect E — orphan projection lineage (REPAIRED, I10R1C)

Pre-repair reproduction (with a self-consistent content-addressed fragment):
a lineage manifest claiming `projection-does-not-exist` was silently ignored.

Repair: lineage-owned projection ids must be exactly coherent with accepted
artifact ids (and context ids, already enforced). Any impossible extra or
dangling durable relation fails `DuckDBCatalogCorrupt`. Evidence is never
deleted or repaired by discovery.

## 10. Missingness preservation (PINNED, I10R1C)

The frozen `CoverageState` vocabulary (PARTIAL, KNOWN_GAP, EMPTY_CONFIRMED,
NOT_ATTEMPTED, FAILED, ACCESS_BLOCKED, HISTORY_UNAVAILABLE, QUARANTINED,
REVISION_CONFLICT) is proven to pass through `v_t0_gaps` verbatim for
current partitions — parametrized over all ten members, including
COMPLETE_SOURCE_BOUNDARY never becoming a gap merely for having no events,
no numeric zero-fill, no generic "missing" collapse, and acquisition-derived
fallbacks kept as separate rows from partition coverage truth.

## 11. Defect F — static I10 evidence (RECORDED, I10R1D)

Negative control executed against the ORIGINAL static builder
(`test_i10_evidence.py`): with production `rebuild_duckdb_catalog` DESTROYED
(replaced by a raising test double), the static builder still emitted
all-OK matrices byte-identical to the committed historical evidence —
`new_catalog_published: OK`, `schema_equal: True`,
`row_count_equal: True`, `canonical_rows_equal: True` as literals. This
historical false-green capability is recorded in
`BLOC_04_I10R1_RUNTIME_EVIDENCE_TRUTH_MATRIX.json` (row
`original_static_builder_false_green_negative_control`, result OK). The
original I10 evidence files were NOT rewritten; they remain historical
evidence of the static-builder flaw.

## 12. Measured R1 evidence (I10R1D)

Every R1 boolean is an OBSERVED fact from executing production behavior in
deterministic temp roots: schema equality from actual PRAGMA output,
row counts from actual queries, destroy/rebuild equivalence from actual
rebuild-A vs rebuild-B rows, failed-build preservation from actual
before/after SHA-256 of the published file, typed refusals from actually
caught exceptions, discovery cost from an instrumented verify/decode spy,
provider separation from actual multi-provider query output, and version
refusals from actual stale-catalog open attempts. Rows carry
`required_invariants`; `result == "OK"` IFF every named invariant is
boolean true. Each matrix contains exactly one deliberate counterfactual
FAIL whose false predicate is represented in the row (never a fabricated
result), enforced by `test_i10r1_deliberate_counterfactual_fails_are_represented`.

Matrices (append-only, byte-compared by pytest, never rewritten by it):
- BLOC_04_I10R1_SCHEMA_CONTRACT_MATRIX.json (7 rows: 6 OK, 1 deliberate FAIL)
- BLOC_04_I10R1_RUNTIME_EVIDENCE_TRUTH_MATRIX.json (4 rows: 3 OK, 1 deliberate FAIL)
- BLOC_04_I10R1_STORAGE_USAGE_DIMENSION_MATRIX.json (5 rows: 4 OK, 1 deliberate FAIL)
- BLOC_04_I10R1_DISCOVERY_COST_MATRIX.json (6 rows: 5 OK, 1 deliberate FAIL)
- BLOC_04_I10R1_DURABLE_RELATION_MATRIX.json (5 rows: 4 OK, 1 deliberate FAIL)
- BLOC_04_I10R1_DUCKDB_DISCOVERY_MICROSEAL.json (governance summary)

Historical I10 artifacts (SHA-256 frozen before edits and re-verified by
test): BLOC_04_I10_CATALOG_REBUILD_MATRIX.json (eca261e8…),
BLOC_04_I10_VIEW_EQUIVALENCE_MATRIX.json (e7aefdc7…),
BLOC_04_I10_EVIDENCE_IMMUTABILITY_MATRIX.json (6c069d35…),
BLOC_04_I10_CORRUPTION_DISCOVERY_MATRIX.json (3883c7ca…),
BLOC_04_I10_PORTABILITY_MATRIX.json (68fc8766…),
BLOC_04_I10_DUCKDB_REBUILD_EVIDENCE.md (2df4f210…),
duckdb_rebuild.json (677e2327…).

## 13. Governance

- PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED = OPERATOR_HOLD
- PASS_SENSOR_B4_I10R1_SCHEMA_EVIDENCE_DISCOVERY_SEALED = PENDING_OPERATOR_REVIEW
- G4-09_CATALOG_REBUILD_GATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
- next_checkpoint_authorized = FALSE
- recommended_next = OPERATOR REVIEW OF COMPLETE I10 -> I10R1 CHAIN
- I11 Postgres: UNAUTHORIZED (zero diff). I12 RawEvidenceQuery: zero diff.
  Research: frozen. Network: zero. Provider source: zero diff.
