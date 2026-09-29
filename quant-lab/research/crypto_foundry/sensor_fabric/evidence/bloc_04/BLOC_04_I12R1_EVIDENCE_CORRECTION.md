# SENSOR-B4-I12R1 — EVIDENCE CORRECTION

> Mandate: SENSOR-B4-I12R1 — end-to-end query semantics + replay dispatch +
> inventory fail-closed microseal
> Base: `0fa09eda3d075742e8f7f048a69882ce3ab705a7` (I12 chain head)
> Status: **PENDING_OPERATOR_REVIEW** (append-only correction; the original
> I12 publication is immutable and remains the historical record)

---

## 1. Why this correction exists

Static operator review of the I12 publication found four acceptance
blockers. The I12 evidence had claimed *"every RawEvidenceQuery filter is
mechanically evaluated"*, but the end-to-end pipeline inside
`RawEvidenceQueryService.execute()` did not enforce four contract surfaces.
That overbroad claim is hereby **superseded**; the original I12 matrices
remain as the historical record of what was measured at I12 time.

## 2. Failure-first reproductions (all recorded BEFORE repair)

### DEFECT A — revision policy was not part of the query reduction
- **Original failing behavior:** `execute()` never called the I06
  `SourceRevisionRegistry`; a two-revision source with the default
  `ERROR_ON_AMBIGUITY` policy returned results silently, `limit=1` reached
  truncation, and `EXACT_REVISION=2` returned every revision.
- **Exact repair:** revision resolution is wired into `execute()` (step 6 of
  the documented pipeline) through the accepted I06 registry; explicit
  policies on an unwired service are a typed `QueryValidationError`.
- **Post-fix measured behavior:** ambiguity raises through `execute()`
  (including `limit=1`, proving limit is step 14, never a suppressor);
  EXACT/FIRST/LATEST/ALL/CANONICAL each change the selected
  acquisitions/blobs. Measured in `BLOC_04_I12R1_REVISION_INTEGRATION_MATRIX`
  (12 rows) and `BLOC_04_I12R1_QUERY_END_TO_END_MATRIX` (12 rows).

### DEFECT B — include modes / projection_schema_ids were not enforced
- **Original failing behavior:** `execute()` only rejected
  `include_t0a=False and include_t0b=False`; T0A/T0B selection and schema
  filtering were not applied to the result fields.
- **Exact repair:** `_build_result` selects representations: `blob_refs` =
  selected T0A; `projection_refs` = selected T0B (schema-filtered from
  durable metadata only, zero payload bytes opened); `lineage_refs` = the
  T0A sources REQUIRED by the selected T0B (provenance, never pretended
  T0A output).
- **Post-fix measured behavior:** `BLOC_04_I12R1_REPRESENTATION_SELECTION_MATRIX`
  (10 rows) measures all four flag combinations, schema match/mismatch with
  the frozen documented T0A-fallback behavior (option A), fresh-repository
  fail-closed on corrupt lineage, and a structural introspection row proving
  zero payload opens.

### DEFECT C — replay order dispatch used string identity
- **Original failing behavior:** `ordered_acquisitions` compared
  `order_by is ACQUISITION_ORDER` etc.; dynamically constructed equal
  strings validated by equality but fell through to the wrong branch.
- **Exact repair:** typed `ReplayOrder` enum with backward-compatible string
  coercion (the public string constants remain, one source of truth); zero
  identity comparisons remain in `replay.py` (structurally scanned in
  evidence).
- **Post-fix measured behavior:** `BLOC_04_I12R1_REPLAY_DISPATCH_MATRIX`
  (6 rows): enum/literal/dynamic/deserialized inputs dispatch identically
  for all three modes; unknown modes are typed `QueryValidationError`.

### DEFECT D — pointer alias could duplicate current inventory
- **Original failing behavior:** `list_all_current_manifests()` enumerated
  pointer files and resolved each payload's declared key without proving the
  enumerated PHYSICAL path is the canonical hash locator for that key; an
  alias `.json` duplicating a valid canonical payload enumerated the same
  logical current manifest twice.
- **Exact repair:** every enumerated pointer must satisfy
  `path == _pointer_path(_partition_hash(pointer.partition_key))` or raise
  `CurrentPointerCorrupt`; returned `partition_key` uniqueness is asserted
  (no silent dedupe).
- **Post-fix measured behavior:** `BLOC_04_I12R1_INVENTORY_FAIL_CLOSED_MATRIX`
  (8 rows): alias, malformed, and payload-mismatch pointers fail closed;
  canonical enumeration returns unique keys.

### ADDITIONAL §17 DEFECTS — catalog family physical aliases
- **Original failing behavior (REPRODUCED before repair):** copying a
  committed blob-metadata or acquisition fragment under a non-canonical
  filename duplicated the logical inventory row (`1 → 2` measured in the
  failure-first probe) — the enumerators trusted any `*.parquet` in the
  family directory.
- **Exact repair:** both enumerators now require the physical filename to
  equal the accepted I04 canonical locator (`{blob_sha256}.{encoding}.parquet`
  / `sha256(acquisition_id).parquet`), raising `CatalogIntegrityError`
  otherwise. No writer semantics changed; no silent dedupe.
- **Post-fix measured behavior:** both alias rows in
  `BLOC_04_I12R1_INVENTORY_FAIL_CLOSED_MATRIX` measure the typed refusal.
- **I06 source-revision list-all:** `I06_ALIAS_GUARD = EXISTING_LAW_SUFFICIENT`
  — the accepted I06 law already binds each durable fragment's logical_id to
  `segment_id = (source_revision_key, revision_number)` at load; an aliased
  physical copy fails closed with `SourceRevisionCatalogCorrupt`. **I06 was
  NOT modified.**

## 3. Final documented query pipeline (implementation matches documentation)

1. complete authoritative inventory (`RawInventorySnapshot`)
2. metadata filters (providers/venues/sensor/instrument/granularity)
3. logical/time filters (range intersection; acquired_before = ingested_at;
   observed_before = response_observed_at)
4. candidate acquisition grouping per blob (time-cut, catalog-divergence
   typed `CatalogStale`)
5. source revision key derivation (accepted identity factory)
6. I06 revision resolution (selected-revision reduction; ambiguity raises
   HERE, before any result exists)
7. selected acquisition/blob reduction (deselected blobs are skipped, the
   manifest survives if any blob remains selected — loop-control regression
   test `test_exact_revision_two_returns_rev2_manifest_not_dropped`)
8. integrity admissibility lattice (failure states never promoted)
9. coverage semantics (missingness is its own state)
10. representation selection: include_t0a → `blob_refs`;
    include_t0b + projection_schema_ids → `projection_refs` (metadata only)
11. T0B schema eligibility
12. T0B lineage validation BEFORE publication (`LineageIncomplete`, even at
    `limit=1`)
13. canonical deterministic result ordering
14. `limit` LAST — provably unable to suppress any refusal above.

## 4. Typed revision-error mapping law (§5, §18)

| I06 exception | I12 typed boundary | Law |
|---|---|---|
| `RevisionAmbiguityError` | `RevisionAmbiguity` | epistemic ambiguity ≠ backend failure |
| `RevisionTemporalAmbiguity` | `RevisionAmbiguity` | same — `__cause__` preserved |
| `RevisionResolutionUnavailable` | `RevisionCanonicalUnavailable` | absent declaration ≠ ambiguity |
| `RevisionNotFound` | `NoMatchingEvidence` | missing requested revision ≠ corruption |
| `RevisionConfigurationError` | `RevisionPolicyInvalid` | caller error |
| `SourceRevisionCatalogCorrupt` | `RevisionPolicyInvalid` | registry corruption ≠ no-match |

Measured (including `__cause__` identity) in the REVISION_INTEGRATION matrix.

## 5. Matrix row counts (each exactly one explicit synthetic FAIL)

| Matrix | Rows | OK | FAIL (synthetic counterfactual) |
|---|---|---|---|
| BLOC_04_I12R1_QUERY_END_TO_END | 12 | 11 | 1 |
| BLOC_04_I12R1_REVISION_INTEGRATION | 12 | 11 | 1 |
| BLOC_04_I12R1_REPRESENTATION_SELECTION | 10 | 9 | 1 |
| BLOC_04_I12R1_REPLAY_DISPATCH | 6 | 5 | 1 |
| BLOC_04_I12R1_INVENTORY_FAIL_CLOSED | 8 | 7 | 1 |
| **Total** | **48** | **43** | **5** |

Every measured row carries its production-measured payload (selected
revision numbers, acquisition ids, blob refs, projection refs, exception
class + `__cause__`, partition keys, replay orderings, opened-blob lists).
Anti-tautology classification: PRODUCTION_BEHAVIOR /
ADVERSARIAL_MUTATION / STRUCTURAL_INTROSPECTION on every non-counterfactual
row. The committed artifacts regenerate byte-identically (read-only pytest
wrappers enforce this on every run).

## 6. Governance

- `PASS_SENSOR_B4_I12_RAW_QUERY_REPLAY_SEALED = OPERATOR_HOLD`
- `PASS_SENSOR_B4_I12R1_END_TO_END_QUERY_SEALED = PENDING_OPERATOR_REVIEW`
- `G4-10_OPERATIONAL_METADATA_GATE = IMPLEMENTATION_PASS` (unchanged)
- `next_checkpoint_authorized = FALSE`
- `recommended_next = OPERATOR REVIEW OF COMPLETE I12 -> I12R1 CHAIN`
- I13 / I13+ = **UNAUTHORIZED**; research = **FROZEN**; no self-ratification.
