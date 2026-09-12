# BLOC_04_I05 — RAW PROJECTION + LINEAGE EVIDENCE

## Checkpoint

SENSOR-B4-I05 — RAW PROJECTION + LINEAGE LAYER

## SHAs

- **Starting SHA:** `028f44833b43b9a993fa03fa9df864a1f2c2a5dd` (I04R2-RATIFY)
- **Ending SHA:** `c80971d7` (I05D)

## Commits (no squash)

| SHA | Commit |
|---|---|
| `537ad9fc` | SENSOR-B4-I04R2-RATIFY: operator accepts I04R2/I04R1/I04 and authorizes I05 only |
| `d28f3020` | SENSOR-B4-I05A: freeze projection schema registry, reserved metadata and schema fingerprint contracts |
| `70afda3c` | SENSOR-B4-I05B: implement immutable provider-native T0B Parquet writer and projection artifact catalog |
| `6f74cdd4` | SENSOR-B4-I05C: implement complete T0A acquisition lineage and multi-blob lineage repository |
| `c80971d7` | SENSOR-B4-I05D: enable projection-aware logical manifests and adversarial integrity tests |

## Modules Added

- `storage/projection_schema.py` — schema definition, fingerprint, key, registry
- `storage/projections.py` — T0B Parquet writer, projection artifact catalog
- `storage/projection_lineage.py` — lineage repository, multi-blob validation

## Schema Registry

- `ProjectionSchemaDefinition`: frozen schema_id + semver + pa.Schema
- `compute_schema_key`: SHA-256(UTF-8(schema_id + "@" + schema_version)) — full 64-char hex
- `compute_schema_fingerprint`: deterministic structural fingerprint covering field name, Arrow logical type, nullable flag, required _t0_* metadata columns
- `ProjectionSchemaRegistry`: immutable local catalog under `<t0_root>/catalogs/projection_schemas/`
- Same id/version + different structure → `ProjectionSchemaConflict`
- Reserved `_t0_*` columns rejected in provider-native schema

## T0B Parquet Writer

- `write_projection`: staging → verify → publish pipeline
- Injects required `_t0_*` metadata columns (projection_id, source_blob_sha256, acquisition_id, provider, venue, sensor_family, native_instrument, parser_version, schema_version, row_ordinal)
- Validates against registered Arrow schema — no lossy coercion
- Projection SHA-256 = exact stored Parquet bytes
- No-clobber atomic publish via existing durability primitives
- Multi-source: per-row source attribution NULL when not defensible

## Projection Artifact Repository

- `ProjectionArtifactRepository`: immutable metadata catalog
- Same projection_id + same bytes = idempotent
- Same projection_id + different bytes = `ProjectionIdentityConflict`

## Lineage Repository

- `ProjectionLineageRepository`: immutable lineage catalog
- Source order contiguous unique 0..N-1
- Artifact source list exactly matches ordered lineage
- Every lineage acquisition must be usable provenance (not forensic failure)
- Failed forensic acquisitions rejected as projection sources

## Manifest Integration

- `ProjectionLineageResolver` Protocol: injected dependency
- Non-empty projection_refs validated when resolver configured
- Fail closed when no resolver configured
- `DanglingProjectionReference`: projection not found
- `ProjectionSourceMismatch`: source blobs absent from manifest

## Test Counts

- Storage: 660 passed / 2 skipped (baseline 582 → +78 new)
- Full suite: 2039 passed / 0 failed / 3 skipped (baseline 1961 → +78 new)
- New tests: 78 (schema 36 + projections 17 + lineage 20 + manifest 5)
- Ruff: clean on changed scope
- Mypy: changed scope clean (only pre-existing planner.py:79 baseline)
- Network: 0
- Provider changes: none

## Boundary

- I06 NOT started
- Bloc 5 NOT started
- No SourceRevision implementation
- No resume advancement
- No DuckDB / Postgres
- No provider integration
- No network

## Proposed Verdict

PASS_SENSOR_B4_I05_RAW_PROJECTION_LINEAGE

## Next Checkpoint

SENSOR-B4-I06 — SOURCE REVISION / MUTATION REGISTRY

I06 NOT authorized and NOT started.
