# SENSOR-B4-I10 — Rebuildable DuckDB Discovery Catalog

## Scope and authority

I10 adds `crypto_sensor_fabric.storage.duckdb_catalog` as a rebuildable,
non-authoritative discovery index over accepted Bloc-4 durable evidence. The
mandatory start was ratified I09R1 commit
`4b8793635e4b2634013542a2c35653c27de96ff6`; expected and observed remote main
was `7c7816f382947bbc8a1f2154435fc436f2428fa8`.

DuckDB owns no raw T0A bytes, manifest history, current pointer, revision
authority, recovery/resume state, quota policy, PostgreSQL role, or T1
normalization semantics. Deleting its file removes only a disposable index.
`rebuild_duckdb_catalog(data_root, catalog_path)` reads durable evidence,
builds a new same-directory temporary catalog, validates it through a read-only
connection, fsyncs it, and atomically replaces the prior rebuildable output.
A failed build never publishes partial output.

## Durable inputs and views

The rebuild consumes accepted EvidenceBlob and AcquisitionRecord Parquet
manifests, projection artifact/context/lineage JSON catalogs and physical
Parquet artifacts, partition manifests and current pointers, source-revision
segment evidence, and recovery action evidence. Blob content is verified via
the accepted `LocalBlobStore` decoder, so NONE and ZSTD representations retain
the frozen H1 identity law.

Eight typed views are implemented:

- `v_t0_blobs`
- `v_t0_acquisitions`
- `v_t0_projections`
- `v_t0_partitions`
- `v_t0_gaps`
- `v_t0_revisions`
- `v_t0_quarantine`
- `v_t0_storage_usage`

All eight are populated from currently durable evidence. None is deferred or
empty by design. A genuinely empty evidence root still receives all eight typed
empty views. `v_t0_storage_usage` is infrastructure accounting only: priority
values describe storage policy, never market importance, and universe tier
remains NULL because it is not durably recorded on these source rows.

## G4-09 proofs

The adversarial fixture constructs T0A bytes, blob and acquisition metadata,
a T0B projection plus context and lineage, a partition/current pointer, a
revision, and quarantine evidence through accepted storage APIs. Canonical rows
from all views are captured with explicit ordering, the DuckDB file is
destroyed, the complete durable evidence-tree path/SHA-256 snapshot is
unchanged, and the catalog is rebuilt. All view rows match exactly. A second
independent output from identical evidence is also equivalent.

Corrupt partition Parquet, corrupt projection JSON, missing projection
artifacts, missing blobs, dangling current pointers, and malformed revision
JSON fail with `DuckDBCatalogCorrupt`; corruption is never converted to
absence. Failed and quarantined missingness remain explicit and no missing
value is numeric-zero-filled. Two revisions of one source remain two rows; I10
does not select a latest revision.

Canonical IDs and backend-neutral object keys survive root relocation.
Absolute local paths appear only as rebuildable operational fields and never
form canonical blob, acquisition, or projection identity.

Normal consumers use `ReadOnlyDuckDBCatalog`, which opens DuckDB read-only,
accepts one SELECT statement, disables external access in the published
catalog, and exposes canonical ordered view snapshots. The rebuild remains the
only write boundary.

## Performance boundary

A single synthetic manifest fragment containing 10,000 metadata rows was
discovered alongside the valid fixture manifest: 10,001 partition rows total.
The reader uses Parquet metadata only and never loads raw T0A payloads for
discovery. This is an informational usability proof, not a millions-of-files
warehouse optimization claim.

## Deterministic evidence

| Artifact | Rows | OK | Deliberate FAIL |
|---|---:|---:|---:|
| `BLOC_04_I10_CATALOG_REBUILD_MATRIX.json` | 5 | 4 | 1 |
| `BLOC_04_I10_VIEW_EQUIVALENCE_MATRIX.json` | 8 | 8 | 0 |
| `BLOC_04_I10_EVIDENCE_IMMUTABILITY_MATRIX.json` | 2 | 2 | 0 |
| `BLOC_04_I10_CORRUPTION_DISCOVERY_MATRIX.json` | 6 | 6 | 0 |
| `BLOC_04_I10_PORTABILITY_MATRIX.json` | 4 | 4 | 0 |

Every measured row declares nonempty `required_invariants`; `result == OK`
iff every named invariant is boolean true. The deliberate counterfactual
`counterfactual_failed_rebuild_overwrites` records both expected predicates as
false and therefore evaluates to FAIL. `duckdb_rebuild.json` is the compact
repository-consistent summary. Normal pytest regenerates all six artifacts in
memory and byte-compares committed files without rewriting them.

## Verification

- Focused I10 rebuild/adversarial suite: 15 passed.
- I10 evidence determinism: 1 passed.
- Required I07/I08/I09/I09R1 regressions: 178 passed.
- Complete storage suite: 1404 passed, 4 skipped. One pre-existing Windows
  reader-thread warning was emitted; no test failed.
- Project `pytest tests/ -q`: 2784 passed, 5 skipped.
- Ruff changed scope and compileall: passed.
- Mypy changed scope: no I10 errors; only the known pre-existing
  `src/crypto_sensor_fabric/probes/planner.py:79` error remains.
- Historical I08, I09, and I09R1 evidence hashes remain unchanged.
- Provider, I11 PostgreSQL, and I12 query API diffs: zero.
- Frozen `bloc_04` contract diff: zero.
- Network calls: zero.

## Governance

```text
PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED = PENDING_OPERATOR_REVIEW
G4-09_CATALOG_REBUILD_GATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized = FALSE
recommended_next = OPERATOR REVIEW OF SENSOR-B4-I10
```

I11 and later remain unauthorized. Research remains frozen. I10 does not
self-ratify G4-09.
