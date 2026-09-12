# SENSOR-B4-I05R2 — FAIL-CLOSED PROJECTION + LINEAGE PUBLIC API SEAL

**Checkpoint:** SENSOR-B4-I05R2 (Fail-Closed Projection + Lineage Public API Seal)
**Status:** COMPLETE — proposed `PASS_SENSOR_B4_I05R2_FAIL_CLOSED_PUBLIC_API_SEALED`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab

---

## 1. Starting SHA

`3e207c64794dfd9b86771b4140a7f7519a043dc3` (I05R1F evidence freeze).
Verified exactly at session start; clean tree; required I05R1 lineage
`d183216e` → `1aef9524` → `98ee9749` → `4868095b` → `d8cc13e4` →
`9cdf88ac` → `3e207c64` present.

## 2. Ending SHA

Commit chain I05R2A..I05R2E (no squash):

- `64310f71` — I05R2A: remove artifact and lineage persistence verification bypasses
- `3de56e55` — I05R2B: enforce exact physical native schema and T0 row truth in the resolver
- `0d953e3f` — I05R2C: seal projection-ref uniqueness and exact catalog crash boundaries
- `203fec20` — I05R2D: add public-API, schema-attack and restart adversarial proofs
- (this commit) I05R2E: freeze I05R2 evidence and ledger

## 3. Operator HOLD finding

The operator HOLD
(`HOLD_PASS_SENSOR_B4_I05R1_DURABLE_END_TO_END_LINEAGE_SEALED_PENDING_I05R2_FAIL_CLOSED_PUBLIC_API_SEAL`)
found four acceptance seams, all now sealed:

1. **public artifact verification bypass** — `ProjectionArtifactRepository`
   accepted `projection_root=None` / `schema_registry=None` /
   `verify_physical=False` and could persist VALID metadata without
   physical proof;
2. **optional lineage proof dependencies** — the persistent lineage writer
   allowed `artifact_repository=None` / `context_repository=None` and
   conditionally skipped artifact source-list agreement and context
   identity matching;
3. **physical native-schema proof weaker than claim** — only native FIELD
   NAMES were proved, not the exact registered Arrow schema and not the
   stored T0 VALUES;
4. **two acceptance details** — duplicate `projection_refs` were not
   rejected, and the named `AFTER_WRITE_BEFORE_FSYNC` crash boundary fired
   AFTER an `os.fsync()` had already happened inside the open-file block.

## 4. Historical evidence preserved (§2)

Untouched; chronology I05 → operator HOLD → I05R1 → operator HOLD → I05R2:

- `BLOC_04_I05_RAW_PROJECTION_LINEAGE_EVIDENCE.md`
- `BLOC_04_I05R1_DURABLE_END_TO_END_LINEAGE_SEAL_EVIDENCE.md`
- all existing I05/I05R1 machine matrices

`git status` on `evidence/bloc_04/` shows only the NEW I05R2 artifacts.
(The I05R1 evidence *generator* was pointed at a throwaway directory in
I05R2A so suite runs can never mutate frozen I05R1 matrices.)

## 5. Fresh current-HEAD baseline (§43)

Recorded BEFORE any code change (authoritative I05R2 start floor):

| Suite | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| storage | 779 | 776 | 0 | 3 |
| full `tests/crypto_sensor_fabric` | 2159 | 2155 | 0 | 4 |

Final counts exceed this baseline (§19 below).

## 6. Artifact repository constructor contract (§4/§5)

```
ProjectionArtifactRepository(
    catalog_root,
    *,
    projection_root: Path,          # MANDATORY
    schema_registry: ProjectionSchemaRegistry,   # MANDATORY
)
```

No `verify_physical` parameter exists anywhere in the class (proven by
§31C TypeError probes).  Metadata-only unit tests use
`RawProjectionArtifact` / real physical files directly (§6), never this
writer as an unverified metadata sink.

## 7. Artifact bypass removal proof (§6/§7)

- commit without projection_root → TypeError at construction (§31A);
- commit without schema_registry → TypeError at construction (§31B);
- `verify_physical=False` → TypeError: unexpected keyword argument (§31C);
- every first VALID commit proves: safe URI beneath root, file exists,
  exact SHA, Parquet opens via `ParquetFile` (no dataset-discovery Hive
  columns), row count, registered schema resolves, FULL physical schema
  EXACTLY equals `registered.provider_native_schema + T0_METADATA_SCHEMA`
  (§15–§17 — subsumes the per-column checks with one authoritative proof);
- idempotent commit compares ALL immutable fields and then RE-VERIFIES
  physical truth (§8) — no success from stale cache.

## 8. Lineage dependency contract (§9/§10)

```
ProjectionLineageRepository(
    catalog_root, *,
    blob_store,                   # MANDATORY (sentinel default)
    blob_metadata_repository,     # MANDATORY
    acquisition_repository,       # MANDATORY
    artifact_repository,          # MANDATORY
    context_repository,           # MANDATORY
)
```

Any omitted/None dependency → typed `LineageConfigurationError` at
CONSTRUCTION.  There is no dependency-starved commit path.

## 9. Missing-artifact result (§11)

`commit` for a projection_id without a committed
`RawProjectionArtifact` → `ProjectionArtifactMissing` BEFORE publication;
nothing durable is written; §31F proves it end to end.

## 10. Missing-context result (§12)

`commit` for a projection_id without a committed
`ProjectionCatalogRecord` → `ProjectionContextMissing` BEFORE publication;
§31G proves it end to end.

## 11. Source-list + identity ALWAYS (§13/§14)

Artifact source list vs ordered lineage (`ArtifactLineageMismatch`) and
provider/venue/sensor_family/native_instrument (+granularity where both
known) against the context are enforced UNCONDITIONALLY in the real commit
path — not only in the later resolver.

## 12. Exact native-schema comparison method (§15–§17)

`table.schema.equals(pa.schema(registered.provider_native_schema +
list(T0_METADATA_SCHEMA)), check_metadata=False)` — exact structural
equality covering field order, names, Arrow types, nullability, nested
child structure, decimal precision/scale, timestamp units/timezones.
`pq.ParquetFile(path).read()` is used (NOT `pq.read_table`) so Hive
partition columns inferred from the `provider=.../venue=...` layout can
never masquerade as stored schema.  A file whose native `price` is string
while registered `price` is double is REJECTED even with a correct SHA
(§32).

## 13. Production resolver physical proof (§18–§22)

`ProjectionLineageResolver._verify_physical` re-proves at READ time:

- physical SHA vs committed (writer history is void — §22);
- EXACT full-schema equality (§16/§18);
- T0 constant VALUES on EVERY row equal to the committed context (§19):
  `_t0_projection_id/_t0_provider/_t0_venue/_t0_sensor_family/
  _t0_native_instrument/_t0_parser_version/_t0_schema_version`;
- row ordinals exactly contiguous `0..row_count-1` (§20);
- physical row lineage (§21): single-source exact on every row;
  multi-source rows either (NULL, NULL) or an exact committed pair —
  one-sided (blob, NULL)/(NULL, acq) and undeclared pairs rejected.

## 14. Adversarial attack proofs (§31–§34) — 35 tests

- **bypass (§31, 7 tests):** construction gates, orphan lineage,
  contextless lineage;
- **native schema attacks (§32):** correct SHAs over malicious bytes —
  wrong type, wrong nullability, wrong field order, wrong nested-child
  nullability all REJECTED by the artifact repository; the resolver
  rejects forged bytes at read time (SHA gate, then exact-schema gate,
  then T0-value gate);
- **T0 value attacks (§33):** seven mutated constants
  (provider/venue/sensor/instrument/parser/schema_version/projection_id)
  plus noncontiguous ordinals [0,2] — all rejected even when schema+SHA
  agree;
- **row-lineage attacks (§34):** single-source wrong acquisition, wrong
  blob, multi-source undeclared pair, one-sided pairs — all rejected.

## 15. Duplicate projection refs (§23/§24)

`PartitionManifest._validate_projection_refs_unique` model validator:
`["p1", "p1"]` → `ValueError("projection_refs contains duplicate
projection id ...")` BEFORE persistence; unique refs accepted; historical
manifests unaffected.  One authoritative rule, no silent dedupe.

## 16. Corrected crash order (§25–§28)

```
open staged file
→ write canonical bytes
→ flush userspace buffers
→ FAULT: AFTER_WRITE_BEFORE_FSYNC     (0 file fsyncs so far)
→ fsync file descriptor (the ONE file fsync)
→ close
→ FAULT: AFTER_FSYNC_BEFORE_VERIFY
→ reopen/verify
→ FAULT: AFTER_VERIFY_BEFORE_PUBLISH
→ publish no-clobber
→ FAULT: AFTER_PUBLISH_BEFORE_DIR_FSYNC
→ fsync parent directory
→ FAULT: AFTER_DIR_FSYNC_BEFORE_RETURN
→ success
```

No fsync occurs before `AFTER_WRITE_BEFORE_FSYNC` (§26/§27); the fake
double-boundary evidence is gone.

## 17. AFTER_WRITE_BEFORE_FSYNC proof (§36)

An fsync SPY (`_FsyncSpy` intercepting `atomic.fsync_file` /
`fsync_directory`) proves with counted REAL calls: faulting at
`AFTER_WRITE_BEFORE_FSYNC` raises with **zero** file fsyncs performed; an
unfaulted commit performs **exactly one** file fsync plus parent-dir
fsync; post-publish faults leave the final object as crash evidence while
the crashing invocation never claims success and a fresh instance sees the
fragment (restart semantics recorded per boundary).

## 18. Machine evidence (§42)

Deterministic (injected clocks, fixed identities, generate-twice
byte-stability asserted):

- `BLOC_04_I05R2_PUBLIC_API_MATRIX.json` — 7 cases: artifact_no_root,
  artifact_no_schema_registry, artifact_valid_physical,
  lineage_no_artifact_repo, lineage_no_context_repo,
  lineage_nonexistent_projection, lineage_valid_full_dependencies;
- `BLOC_04_I05R2_PHYSICAL_SCHEMA_MATRIX.json` — 11 cases: exact_schema,
  wrong_native_type, wrong_native_nullability, wrong_native_order,
  wrong_nested_type, wrong_t0_provider, wrong_t0_parser,
  wrong_projection_id, bad_row_ordinal, bad_single_source_lineage,
  bad_multi_source_pair;
- `BLOC_04_I05R2_CRASH_BOUNDARY_MATRIX.json` — 7 cases (6 fault
  boundaries + unfaulted control) with actual spy-counted fsync counts,
  staging/final existence, success-claimed and restart-visibility fields.

## 19. Final test counts (§44)

| Suite | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| storage | 831 | 828 | 0 | 3 |
| full `tests/crypto_sensor_fabric` | 2211 | 2207 | 0 | 4 |

- Storage baseline 776 passed → final 828 passed (+52).
- Full-suite baseline 2155 passed → final 2207 passed (+52).
- 0 failures; skips are platform skips (POSIX-only on Windows).

## 20. Ruff / mypy / network / provider

- **ruff:** clean on all changed scope
  (`src/crypto_sensor_fabric/storage/`, `tests/crypto_sensor_fabric/storage/`).
- **mypy:** clean on changed scope; the only error is the PRE-EXISTING
  `probes/planner.py:79` baseline documented since I04R1 (untouched file).
- **network:** 0.
- **provider source changes:** none.

## 21. Scope discipline (§37–§39)

NOT done: I06 revisions.py / SourceRevisionRepository / source_revision_key /
mutation classifier / FIRST_SEEN / LATEST_SEEN; I07 job-state transitions or
resume advancement; recovery scanner; quota engine; DuckDB; Postgres;
RawEvidenceQuery; Bloc-3 integration; backfill; live recorder; Bloc-5
semantics (no canonical instruments/units, no USD/OI/funding/liquidation
normalization, no cross-venue state).  T0 only.

## 22. Ledger flags if earned

```
T0B_PROJECTION_SCHEMA_READY           = TRUE
T0B_PHYSICAL_PROJECTION_WRITER_READY  = TRUE
T0B_PROJECTION_CATALOG_IMPLEMENTED    = TRUE
T0B_LINEAGE_REPOSITORY_IMPLEMENTED    = TRUE
T0B_TO_T0A_LINEAGE_COMPLETE           = TRUE
T0B_STORAGE_IMPLEMENTED               = TRUE
SOURCE_REVISION_REGISTRY_IMPLEMENTED  = FALSE
DURABLE_RESUME_IMPLEMENTED            = FALSE
next_checkpoint_authorized            = FALSE
```

## 23. Proposed verdicts

- `PASS_SENSOR_B4_I05R2_FAIL_CLOSED_PUBLIC_API_SEALED` (proposed)
- then operator may accept `PASS_SENSOR_B4_I05R1_DURABLE_END_TO_END_LINEAGE_SEALED`
- then operator may accept `PASS_SENSOR_B4_I05_RAW_PROJECTION_LINEAGE`

## 24. STOP gate

After I05R2: STOP.  I06 (SOURCE REVISION / MUTATION REGISTRY) NOT started;
research NOT resumed.  Evidence returned for operator review.
