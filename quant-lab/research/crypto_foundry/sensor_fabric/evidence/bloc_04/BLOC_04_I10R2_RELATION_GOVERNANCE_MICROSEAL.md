# BLOC 04 — SENSOR-B4-I10R2 RELATION GOVERNANCE MICROSEAL

## Scope

This append-only checkpoint repairs only SENSOR-B4-I10R2 durable relation binding, recovery-envelope validation, measured row-count parity, and current governance. I11 PostgreSQL, I12 RawEvidenceQuery, I12+, provider sources, and frozen research/plan contracts are unchanged and unauthorized.

## Relation-binding law

DuckDB discovery now reuses the frozen `ProjectionLineage`, `ProjectionCatalogRecord`, and `RawProjectionArtifact` contracts together with the accepted row-bound, source-order, and artifact/lineage source-list helpers. Before projection discovery succeeds, every manifest must prove:

1. `record_type == projection_lineage_manifest` and nonempty manifest/projection identities.
2. Every entry is a typed `ProjectionLineage` bound to the same manifest and projection.
3. Source order is unique and contiguous `0..N-1`; row bounds are both absent or both present, inclusive, and ordered.
4. The context names the exact durable manifest, and the artifact source list exactly equals the ordered lineage source list.
5. Every source blob and acquisition exists in the already-loaded durable metadata truth; acquisition/blob identity agrees.
6. Acquisition provenance is usable under the accepted metadata predicate.
7. Provider, venue, sensor family, and native instrument agree with projection context; granularity agrees when both sides carry it.

The ordinary rebuild does not instantiate the physical lineage resolver and does not call `LocalBlobStore.verify_blob` or `LocalBlobStore._decode_stats`. T0A payload verification remains owned by explicit I08/I05 integrity machinery.

## Recovery-envelope law

Every durable `RecoveryJournal` action is validated in full before the narrow `v_t0_quarantine` projection is built. The complete frozen envelope must have the expected fields, exact `record_type`, nonempty semantic strings, optional string-only `action_kind` and `operation_id`, parseable object states, an aware `registered_at`, and a recomputed semantic identity. Frozen `StorageObjectType` object types map consistently; internal recovery object types are accepted only with `storage_object_type = null`.

## Measured parity

The R2 fixture executed `SELECT count(*)` against all eight published views and compared each result with the rebuild receipt:

- `v_t0_blobs`: 1
- `v_t0_acquisitions`: 1
- `v_t0_projections`: 1
- `v_t0_partitions`: 1
- `v_t0_gaps`: 1
- `v_t0_revisions`: 1
- `v_t0_quarantine`: 1
- `v_t0_storage_usage`: 4

All eight actual counts equal the receipt counts. Actual schemas equal `VIEW_SCHEMAS`; the metadata stamp is exact; instrumented default rebuild recorded zero `verify_blob` and zero `_decode_stats` calls.

## Evidence truth

Every non-counterfactual evidence predicate is mechanically observed from executed production behavior. Deliberate counterfactual predicates are explicitly synthetic and must evaluate FAIL. The append-only matrices contain:

- `BLOC_04_I10R2_LINEAGE_BINDING_MATRIX.json` — 10 rows.
- `BLOC_04_I10R2_RECOVERY_ENVELOPE_MATRIX.json` — 10 rows.
- `BLOC_04_I10R2_MEASUREMENT_PARITY_MATRIX.json` — 9 rows.
- `BLOC_04_I10R2_RELATION_GOVERNANCE_MICROSEAL.json` — governance summary.

Historical I10 and I10R1 evidence hashes remain byte-for-byte unchanged.

## Governance

```text
PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I10R1_SCHEMA_EVIDENCE_DISCOVERY_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I10R2_RELATION_GOVERNANCE_PARITY_SEALED = PENDING_OPERATOR_REVIEW
G4-09_CATALOG_REBUILD_GATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized = FALSE
recommended_next = OPERATOR REVIEW OF COMPLETE I10 -> I10R1 -> I10R2 CHAIN
I11 = UNAUTHORIZED
research = FROZEN
```

This checkpoint does not self-ratify and does not authorize I11.
