# BLOC 04 — SENSOR-B4-I13R3 Evidence Correction Narrative

> Mandate: SENSOR-B4-I13R3 — Nonvacuous DuckDB/T0B Parity + Fail-Safe Source-Root Containment Microseal
> Start HEAD: `ed7b80bc4b861fd5add71ea2e3a33a2a6b53575f` (branch `agent/crypto-sensor-fabric-build`)
> Remote main at mandate time: `7c7816f382947bbc8a1f2154435fc436f2428fa8`
> Status: **IMPLEMENTATION PASS — PENDING OPERATOR REVIEW** (no self-ratification; I14+ UNAUTHORIZED; research FROZEN)

---

## 1. Operator findings reproduced (failure-first)

**A. Vacuous DuckDB identity parity.** The published
`BLOC_04_I13R2_DUCKDB_IDENTITY_PARITY_MATRIX.json` measured
`v_t0_blobs/v_t0_acquisitions/v_t0_partitions/v_t0_revisions` with
`counts: {source: 0, restored: 0}` on every row. Two root causes:

1. *Wrong rebuild root*: the I13R2 builder passed the LAKE root and the PACK
   root to `rebuild_duckdb_catalog`; the accepted I10/I13 contract (verified
   in `test_i13r1_evidence.py` §34 and `test_i13_export_restore.py` §31) is
   the T0A storage root (`root/"src"/"t0a"`, `restored_root/"t0a"`).
2. *Structural T0B gap*: the accepted lake layout stores T0B projection
   catalogs in the SIBLING `t0b` tree while the I10 discovery root carries
   the T0A blob domain; the T0B lineage gate needs blob metadata, so a
   single-root rebuild of a T0B-bearing fixture fails closed
   (`DuckDBCatalogCorrupt: lineage source blob … has no durable metadata` /
   `manifest … has dangling projection ref`) — the I13R2 builder "succeeded"
   only by reading a catalog with nothing in it.
3. *Revision layout gap*: `v_t0_revisions` read only the I10 canonical
   `catalogs/source_revisions/segments`, while the accepted I12/I13
   `SourceRevisionRegistry` durably writes `<t0a>/revisions/segments` —
   the view was structurally empty for the whole I13 fixture family.

**B. Vacuous T0B metadata parity.** The published EXACT_METADATA_PARITY
measured projection artifact/context/lineage rows = 0 (all sharing the
empty-JSON-array digest `4f53cda1…`). Root cause: the fixture query used the
`RawEvidenceQuery` default `include_t0b=False`, and the shared fixture lake's
manifest carried no `projection_refs` — so no T0B graph was ever exported.

**C. Optional source-root protection.** `protected_source_roots` defaulted
to `[]` and the canonical `_exporter(lake)` composition never passed T0B or
revision roots: destination-overlap protection covered only the T0A blob
store (derived) plus whatever the caller remembered to list.

## 2. Repairs (production, fail-closed)

### DuckDB root law (§3)

`rebuild_duckdb_catalog(data_root, catalog_path, *, projection_root=None)`:
the discovery root is the T0A storage root; `projection_root` names the
sibling T0B tree when the lake uses the split layout. Default `None` reads
every catalog from `data_root` — byte-identical to the pre-I13R3 unified
behavior (all accepted I10/I10R1/I10R2/I13R1/I13R2 call sites unchanged).
Revision discovery now reads BOTH durable layouts
(`catalogs/source_revisions/segments` AND `revisions/segments`,
identity-keyed, divergence fail-closes). Nonvacuity is now provable AND a
single-root rebuild of a T0B-bearing fixture refuses typed — the empty 0/0
"parity" rows are impossible by construction.

### Real T0B roundtrip (§7-§11) — and latent bugs it exposed

The dedicated fixture (`build_t0b_lake`) commits a real projection
(artifact + context + lineage + schema + payload) and a T0B-aware manifest.
The projection resolver's partition-key equality law makes the T0B manifest
a version-2 supersession of v1 on the SAME partition key (CAS + I04 §33
no-gap law) — and exercising that path exposed three latent production
defects, all repaired:

1. *T0B metadata serialization*: `canonical_json_bytes` (a pydantic helper)
   was applied to `ProjectionCatalogRecord` (plain class), lineage entry
   lists, and `ProjectionSchemaDefinition` — the T0B context/lineage/schema
   export paths had NEVER run end-to-end and crashed with
   `AttributeError`. New `_canonical_dict_bytes` provides the same canonical
   JSON discipline for plain-dict records (`to_dict()`/`to_descriptor()`,
   lossless round trips).
2. *Versioned-manifest closure*: a superseding manifest's PREDECESSOR is
   REQUIRED_SUPPORT (new `MANIFEST_PREDECESSOR` fixpoint edge) — the restore
   writer re-appends immutable versions in CAS order, so version N > 1
   cannot replay without version N-1. The matched-manifest set now grows
   inside the monotone fixpoint (never shrinks, §8 law preserved).
3. *Restore replay order + CAS derivation*: manifests replay in
   `(partition_key, manifest_version)` order (the deterministic source
   registration order, mirroring the I06 acquisition replay law); the
   v≥2 CAS `expected_current` is correctly derived as
   `(pointer.previous_manifest_id, version-1)` from the exported source
   pointer (the old code passed the post-append identity as the pre-append
   expectation — unreachable before I13R3, since no accepted fixture had a
   versioned manifest); CURRENT_POINTER objects are one-per-partition-key;
   the restored manifest repository is wired with the restored T0B
   `ProjectionLineageResolver` so the I04 §20 referential gate can validate
   `projection_refs`; T0B replay now precedes manifest replay.

### Fail-safe source boundary (§12-§17)

- Public READ-ONLY `root` properties added: `ProjectionArtifactRepository`
  (plus `projection_root`), `ProjectionContextRepository`,
  `ProjectionLineageRepository`, `ProjectionSchemaRegistry`,
  `SourceRevisionRegistry` (§14 option B; no write surface exposed; the
  I13R1 public-boundary seal is intact — see §5).
- The exporter now DERIVES every wired dependency's source boundary at
  construction (T0A blob store root + artifact/context/lineage/schema/revision
  roots) and REFUSES CONSTRUCTION with the typed
  `ExportSourceBoundaryUnproven` error when a wired dependency cannot prove
  its root (§15 fail-closed). `protected_source_roots` still works as an
  EXTENSION for additional trees — never a substitute.
- `_validate_destination` protects the store root plus every derived
  boundary by default: no caller-specific override is required for safe
  composition (§16).

## 3. Measured evidence (append-only, byte-stable, digests verified across two runs)

```
DUCKDB_NONVACUOUS_IDENTITY  c5af877aece80cca4506fc3ab29fa81e6d49e864ac419548d93adb76216b3d0f
T0B_PARITY                  c866fe5c187bd134af5b60fbade3e62d3ee3d7b19c0a6b043c60c0618fe74222
SOURCE_BOUNDARY             e239e0eaf8601181b59dc16ceb1017f2317b4b300571ff3e18390fbb57cd7cd7
```

- **DUCKDB_NONVACUOUS_IDENTITY** (7 rows, 6 measured OK + 1 synthetic):
  every view carries positive counts on BOTH sides and literal set equality
  SOURCE(filtered to pack closure) == PACK_EXPECTED == RESTORED:
  `v_t0_blobs` 2/2, `v_t0_acquisitions` 2/2, `v_t0_partitions` 2/2,
  `v_t0_revisions` 2/2, `v_t0_projections` 1/1 (identity columns per §5,
  accepted I10 names). Plus: single-root rebuild of the T0B fixture refuses
  typed (`DuckDBCatalogCorrupt`). Synthetic: empty==empty parity ratifies
  nothing.
- **T0B_PARITY** (8 rows, 7 measured OK + 1 synthetic): pre-export query
  returns nonempty `projection_refs`/`lineage_refs`; artifact/context/
  lineage/schema rows all nonempty with literal canonical equality;
  three-way payload SHA parity (`5d4c04ce…` source == pack == restored
  physical) verified through public `open_payload()`/`verify_physical()`
  only; restored T0B query-result digest equals source WITH nonempty T0B
  refs (usable, not merely present). Synthetic: 0-row parity proves
  nothing.
- **SOURCE_BOUNDARY** (15 rows, 14 measured OK + 1 synthetic): destination
  inside/equal to every protected family refused with
  `ExportDestinationUnsafe` without any caller override — T0A blob root
  (equal + child), T0A catalog root (child), revision registry root, T0B
  payload root (equal + child), T0B projection/context/lineage/schema
  catalogs (children); symlink-into-source refusal measured through the
  production parent-chain symlink guard (structural equivalent on
  no-symlink-privilege platforms per §24); external-destination success
  control exports; constructor with an unproven-boundary dependency refuses
  (`ExportSourceBoundaryUnproven`); private-access seal counts 0/0/0.
  Synthetic: opt-in protection lets accidental compositions write into
  source trees.

## 4. Regression / static posture at publication

- Focused I13R3 suite: 2 passed (all matrix rows real-OK; published
  nonvacuity asserted: every identity row with counts carries
  `source_count > 0 AND restored_count > 0`).
- I13/I13R2 focused suites re-run unchanged and green; full project
  regression: **see governance ledger block** (3048+ passed, 0 failures
  pre-I13R3 additions; final counts in the ledger).
- Ruff clean on changed files; compileall OK; mypy 0 new errors in changed
  production scope; structural greps `_segments_by_key`/`_declarations_by_key`/
  `_projection_root` in export.py = **0** (I13R1 seal intact; the new root
  accessors are read-only properties, §17).

## 5. Historical evidence immutability

I13/I13R1/I13R2 matrices are NOT modified (§18): the empty I13R2 DuckDB/T0B
rows remain the historical proof of what R2 measured. Content verified
unchanged vs start HEAD `ed7b80bc` (the 7 pre-existing CRLF working-tree
files are outside this session's scope; git blobs untouched).

## 6. Governance

```
PASS_SENSOR_B4_I13_EXPORT_BACKUP_RESTORE_SEALED      = OPERATOR_HOLD
PASS_SENSOR_B4_I13R1_PUBLIC_AUTHORITY_ATOMIC_CLOSURE_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I13R2_EVIDENCE_FIDELITY_RESOURCE_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I13R3_NONVACUOUS_PARITY_BOUNDARY_SEALED = PENDING_OPERATOR_REVIEW
G4-11_EXPORT_RESTORE_GATE                            = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                           = FALSE
recommended_next                                     = OPERATOR REVIEW OF COMPLETE I13 -> I13R1 -> I13R2 -> I13R3 CHAIN
I14+                                                 = UNAUTHORIZED
research                                             = FROZEN
```

No self-ratification. I14 not started.
