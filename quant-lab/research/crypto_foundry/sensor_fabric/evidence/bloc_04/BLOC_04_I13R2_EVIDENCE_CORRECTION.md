# BLOC 04 — SENSOR-B4-I13R2 Evidence Correction Narrative

> Mandate: SENSOR-B4-I13R2 — Manifest Root Matching + Formal Evidence-Closure Fixpoint
> Start HEAD: `e7e95533e1f1738195ccbf94197b6c59859b5ba4` (branch `agent/crypto-sensor-fabric-build`)
> Remote main at mandate time: `7c7816f382947bbc8a1f2154435fc436f2428fa8`
> Status: **IMPLEMENTATION PASS — PENDING OPERATOR REVIEW** (no self-ratification; I14+ UNAUTHORIZED; research FROZEN)

---

## 1. Scope of this correction

This document corrects the I13/I13R1 evidence record in response to the
SENSOR-B4-I13R2 operator-review blockers:

| Blocker | Finding | Closure |
|---------|---------|---------|
| A | Free-space check silently disabled without an injected disk-usage provider | `_check_free_space` never silently disables; default path uses real `shutil.disk_usage` on the nearest existing ancestor of the target; injected provider is used when supplied; pre-copy estimate + progressive per-blob check with `METADATA_OVERHEAD_BYTES = 64 KiB` |
| B | Metadata parity asserted at count level only | EXACT_METADATA_PARITY matrix compares field-by-field export/restore records, including query-semantic timestamps (`created_at`, `ingested_at`, `response_observed_at`), with byte-stable timestamps via injected fixed clock |
| C | Revision segments/observations/declarations parity not measured | REVISION_PARITY matrix (25 OK rows) measures segments, observations, and declarations by exact key sets, not counts |
| D | DuckDB parity was row-count-only | DUCKDB_IDENTITY_PARITY matrix retrieves accepted identity columns from rebuilt views and compares sorted identity tuples, with source discovery filtered to `EXPECTED_CLOSURE_SET` |
| E | "Unselected evidence absent" law too strong and root selection too broad | Replaced with the 3-class transitive-closure law (§4 below) + unique manifest-root matching (§3) |

Historical I03R1/I04/I11/I12/I13/I13R1 evidence files are **unchanged** versus
start HEAD `e7e95533` (verified: content-identical modulo CRLF working-tree
churn introduced outside this session; git blobs at HEAD are untouched).

---

## 2. Old broad manifest-selection reproduction

The previously accepted exporter resolved result→manifest by
`(provider, venue, native_instrument)` alone. Reproduction: with two current
manifests sharing those three dimensions (adversarial fixture in
`TestI13R2ManifestRootMatching.test_broad_identity_lookalike_manifest_excluded`),
the old law exported both — including a manifest that played no role in
producing the query result — dragging its entire referential closure into the
pack as apparent "leakage". This was the first root cause behind the
bounded-slice "unselected source" finding.

## 3. Unique manifest-root matching law (final)

For every `RawEvidenceResult`, exactly ONE current `PartitionManifest` must
explain it. Matching uses the strongest accepted fields:

- identity dims: `provider`, `venue`, `sensor_family`, `native_instrument`
- `source_granularity`
- window containment: result logical time within
  `[logical_date_start, logical_date_end]`
- `coverage_state` / `integrity_state` where semantically stable
- evidence-binding agreement: T0A `result.blob_refs ⊆ manifest.blob_refs`;
  T0B `result.projection_refs ⊆ manifest.projection_refs`;
  T0B-only lineage refs must agree with projection lineage reachable from the
  candidate manifest; acquisition IDs must resolve to blobs compatible with
  the candidate manifest.

- 0 candidates → `ExportSourceInvalid`
- >1 candidates → explicit ambiguity error (no silent export of
  "every matching-looking manifest")

No synthetic sliced manifests are created: `manifest.blob_refs`,
`manifest.projection_refs`, partition identity, and manifest ID are never
rewritten to fit the query. The original immutable manifest is evidence; if it
is exported, its referential closure is exported with it.

## 4. Formal three-class evidence law

- **QUERY_SELECTED** — evidence explicitly present in `RawEvidenceResult`
  (`acquisition_ids`, `blob_refs`, `projection_refs`, `lineage_refs`).
- **REQUIRED_SUPPORT** — not selected as output but required to reconstruct the
  exact immutable source graph: manifest-referenced blobs and projections,
  projection lineage/schema, required acquisitions, revision prefix, canonical
  declaration evidence, revision-segment `first_acquisition_id` bindings.
- **UNRELATED** — no transitive dependency path from A or B. **Only UNRELATED
  is leakage.**

The old law "unselected evidence must never exist in pack" is replaced by:
**"no evidence outside the minimal transitive support closure."**

## 5. Closure mechanics

- Seed: exact matched-manifest IDs + query-selected refs (never seeded from all
  manifests sharing broad dimensions).
- Monotone fixpoint (`_evidence_closure` in `export.py`): each iteration adds
  dependencies of every object already in the closure; no object disappears;
  no policy branch overwrites an earned dependency. Returns frozen
  `EvidenceClosure` with `blob_shas / acquisition_ids / projection_ids /
  matched_manifests / query_selected_* / support_* / trace / iterations`.
- Expansion edges: `MANIFEST_BLOB_REF`, `MANIFEST_PROJECTION_REF`,
  `PROJECTION_LINEAGE`, `BLOB_ACQUISITIONS` (identity-domain filtered),
  `REVISION_FIRST_ACQUISITION`, `REVISION_SEGMENT_BLOB`,
  `REVISION_PREFIX`, `CANONICAL_DECLARATION`.
- Policy closure (ALL / FIRST_SEEN / LATEST_SEEN / EXACT_REVISION=N /
  PROVIDER_DECLARED_CANONICAL / ERROR_ON_AMBIGUITY) determines the minimum
  revision state required to reproduce the query selection; structural closure
  (immutable manifest/projection references) may enlarge it — that enlargement
  is classified REQUIRED_SUPPORT and query selection is never altered. Policy
  minimums are never shrunk below their law.
- Cycle safety: visited identity sets; termination is monotone and
  recursion-depth independent.
- `ExportObjectRecord` is NOT extended; the trace is a test/debug structure
  only (per mandate §19).

## 6. Fixpoint trace, idempotence, and bounded-slice proof

Measured in `BLOC_04_I13R2_BOUNDED_SLICE_MATRIX.json`:

- fixpoint iterations = 2 (stable at 2 on both first and second run —
  `C1 == C2`, idempotence proven)
- QUERY_SELECTED: 2 blobs, 2 acquisitions (⊂ pack)
- REQUIRED_SUPPORT: 1 blob, 1 acquisition, with causal inclusion trace rows
  (reasons: `MANIFEST_BLOB_REF`, `BLOB_ACQUISITIONS`,
  `REVISION_FIRST_ACQUISITION`, `REVISION_SEGMENT_BLOB`)
- ACTUAL_PACK_SET == EXPECTED_TRANSITIVE_CLOSURE_SET for blobs, acquisitions,
  revision keys/segments (pack == restored == closure sets)
- true unrelated control (SOL-USDT source, disjoint partition/sensor/date, no
  blob/lineage/revision/declaration edge): absent from pack and restored lake;
  `true_leakage_count = 0`; `unrelated_control_objects = 3` all excluded
- every QUERY_SELECTED ⊆ pack; pack ∩ UNRELATED_CONTROL == ∅

Canonical-policy and EXACT_REVISION=2 fixtures use one controlled two-revision
source key whose selected manifest legitimately contains both revision blobs
(both-revision policy rows succeed); canonical declarations are declared only
on keys actually touched by the query/manifest — no blanket canonicalization
(§25/§26 honored).

## 7. Query-semantics survival

TIME_FILTER_PARITY: `acquired_before` and `observed_before` cutoffs select
identical acquisition IDs on source and restored lakes (4/4 OK rows), proving
the expanded acquisition support closure (all identity-domain acquisitions per
closure blob, per I12 semantics) did not distort query behavior. QUERY_POLICY_PARITY
proves source==restored for default/ALL/FIRST_SEEN/LATEST_SEEN/EXACT_REVISION 1/
EXACT_REVISION 2/PROVIDER_DECLARED_CANONICAL plus refusal parity (10 OK rows).
Restore replay ordering follows the accepted I06 temporal law:
`register_acquisition` replay sorted by `(response_observed_at, acquisition_id)`
deterministic tie-break; `RevisionObservationOrderConflict` is not weakened.

## 8. Byte-stability method

- All matrix builders run in a `TemporaryDirectory`; `_scrub()` replaces the
  tmp-path prefix with `<TMP>` in published content.
- `build_deterministic_lake()` patches `LocalBlobStore.__init__` and
  `BlobMetadataRepository.__init__` to inject `clock=lambda: FIXED` during
  `build_fixture_lake` construction (originals restored in `finally`),
  eliminating wall-clock `EvidenceBlob.created_at` nondeterminism.
- Matrices serialize via `json.dumps(indent=2, sort_keys=True)` + trailing
  newline; digests verified identical across two full runs:

```
RESOURCE_SAFETY            c3c81119…
EXACT_METADATA_PARITY      9c191332…
REVISION_PARITY            29068e5e…
DUCKDB_IDENTITY_PARITY     485deb85…
QUERY_POLICY_PARITY        420abb73…
TIME_FILTER_PARITY         32125013…
BOUNDED_SLICE              4ffac74d…
```

Each matrix also carries exactly one deliberate `SYNTHETIC_COUNTERFACTUAL`
FAIL row documenting a naive surrogate method that must be rejected
(count-only closure, count-only parity, timestamp strip, exception-as-result,
silent free-space bypass, segments-only claim, time-filter surrogate) — the
established append-only evidence convention; all measured rows are OK.

## 9. Regression / static posture at publication

- Focused I13R2 suite: 3 passed.
- Full project regression: **3048 passed, 28 skipped, 0 failures** (skips are
  pre-existing; `tests/` contains only crypto_sensor_fabric storage suites, so
  the full-project run is the complete storage suite; the disjoint non-storage
  run confirms zero tests exist outside it).
- Ruff clean on changed files; `compileall` OK; mypy: 0 new errors in changed
  scope (10 pre-existing errors in untouched `providers/` files = baseline).
- Public boundary preserved: `_segments_by_key`, `_declarations_by_key`,
  `_projection_root` occurrences in `export.py` = 0 (I13R1 seal intact).

## 10. Governance

```
PASS_SENSOR_B4_I13_EXPORT_BACKUP_RESTORE_SEALED     = OPERATOR_HOLD
PASS_SENSOR_B4_I13R1_PUBLIC_AUTHORITY_ATOMIC_CLOSURE_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I13R2_EVIDENCE_FIDELITY_RESOURCE_SEALED = PENDING_OPERATOR_REVIEW
G4-11                                               = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                          = FALSE
I14+                                                = UNAUTHORIZED
research                                            = FROZEN
```

Next step is operator review of the complete I13 → I13R1 → I13R2 chain.
No self-ratification has occurred or will occur.
