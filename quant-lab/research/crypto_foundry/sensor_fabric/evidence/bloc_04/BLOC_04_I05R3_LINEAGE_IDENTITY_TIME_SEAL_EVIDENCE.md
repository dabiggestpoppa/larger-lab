# SENSOR-B4-I05R3 — LINEAGE-MANIFEST IDENTITY + IDEMPOTENT REVALIDATION + UTC TRUTH SEAL

**Checkpoint:** SENSOR-B4-I05R3 (Lineage-Identity + Time-Truth Seal)
**Status:** COMPLETE — proposed `PASS_SENSOR_B4_I05R3_LINEAGE_IDENTITY_TIME_SEALED`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab

---

## 1. Starting SHA

`9ffcf9976d8e4ac804a8fe31cb401e71a343fdbf` (I05R2E evidence freeze).
Verified exactly at session start; clean tree; required I05R2 lineage
(`64310f71` → `3de56e55` → `0d953e3f` → `203fec20` → `9ffcf997`) present.

## 2. Ending SHA / Commit Chain

| Commit | Stage |
|---|---|
| `7793abca` | I05R3A: bind projection context to exactly one lineage manifest |
| `bd75954b` | I05R3B: revalidate idempotent lineage commits against current durable truth |
| `1814c82c` | I05R3C: reject naive projection-context timestamps and seal UTC ordering |
| *(this commit)* | I05R3D: freeze lineage-identity/time evidence and ledger |

No squash.

## 3. Operator Finding (chronology)

I05 → operator review (I05R1 HOLD) → I05R1 → operator review (I05R2 HOLD)
→ I05R2 → operator review found three truth seams → I05R3:

- **A:** `ProjectionCatalogRecord.lineage_manifest_id` was not enforced as
  the binding between a projection and its lineage manifest — an alternate
  lineage identity could publish for an already-bound projection.
- **B:** idempotent lineage re-commit returned cached truth BEFORE
  re-verifying artifact/context/source evidence.
- **C:** `ProjectionCatalogRecord` silently interpreted naive datetimes as
  UTC during serialization (`replace(tzinfo=UTC)`).

## 4. Defect A Repair — Context / Lineage Binding (§3–§8)

- **Three-way binding:** `commit()` now requires
  `lineage_manifest_id` argument == every entry's `lineage_manifest_id` ==
  `context.lineage_manifest_id`, proven BEFORE durable publication.
  Violation → `LineageContextBindingConflict`.
- **Alternate manifest rejected, not written:** the L2 fragment never
  reaches disk (matrix case `alternate_lmid_same_projection` records
  `fragment_written: false`).
- **One authoritative manifest:** lineage revision/versioning is NOT
  implemented (I05 v1 doctrine); changing lineage semantics later requires
  a new projection identity.
- **Load invariant (§6):** on repository construction, if multiple
  committed lineage manifests claim the same `projection_id`, construction
  fails closed with `LineageProjectionIdentityConflict` (protects
  legacy/tampered disk; proven by raw-catalog tamper test).
- **`get_by_projection` (§7):** zero manifests → empty list; more than one
  → `LineageProjectionIdentityConflict`; never concatenates competing
  manifests.
- **Resolver lookup (§8):** the production resolver resolves lineage via
  `lineage.get(context.lineage_manifest_id)` directly — it does not scan
  all fragments for `projection_id` — and then requires every entry's
  `projection_id` to match.

## 5. Defect B Repair — Idempotent Revalidation (§9–§13)

`commit()` was restructured so idempotent content comparison falls through
to FULL re-validation instead of an early `return self._cache[lmid]`:

1. artifact existence (`ProjectionArtifactMissing` when absent)
2. artifact source-list agreement (unconditional, `ArtifactLineageMismatch`)
3. context existence (`ProjectionContextMissing` when absent)
4. three-way lineage_manifest_id binding (§4 above)
5. **artifact physical T0B verification NOW** — new public
   `ProjectionArtifactRepository.verify_physical(projection_id)` re-proves
   SHA/schema/rows/URI containment against the stored bytes
   (`ProjectionCorruption` on drift); the writer's one-time validation is
   not a current proof
6. per-entry T0A source verification: durable blob metadata, physical
   blob verification through `LocalBlobStore`, acquisition existence,
   acquisition→blob binding, usable provenance, provider/venue/sensor/
   instrument/granularity identity match

Only after all of the above may the idempotent manifest be returned.
Required tests (§11–§13): identical re-commit after source-blob
corruption, after context-fragment loss (with repository restart), and
after physical T0B corruption — ALL FAIL.  Historical lineage remains
durable in the corruption cases (I08 owns recovery).

## 6. Defect C Repair — UTC Time Truth (§14–§19)

- `_require_aware()` rejects naive inputs for `logical_date_start`,
  `logical_date_end`, `min_provider_time`, `max_provider_time`,
  `created_at` with `ProjectionPreconditionError` — no implicit UTC
  assignment.
- Offset-aware non-UTC inputs are accepted and serialize normalized to
  UTC: `2026-01-01T12:00:00-05:00` → `2026-01-01T17:00:00+00:00` (§16).
- `from_dict` rejects persisted naive timestamp strings as
  `ProjectionArtifactCatalogCorrupt` — a tampered fragment is never loaded
  by assumption (§18).
- Ordering (§17): `logical_date_end >= logical_date_start` (pre-existing)
  plus NEW `max_provider_time >= min_provider_time` when both exist.
  Missing bounds are never manufactured.
- `_canonical_utc` retains a fail-closed backstop (`ProjectionPreconditionError`
  if a naive datetime ever reaches serialization) rather than coercing.
- `created_at` remains operational metadata; it does not enter projection
  content SHA, schema identity, or T0 evidence identity (doctrine
  unchanged) but is now required timezone-aware (§19).

## 7. Crash-Evidence Wording Clarification (§20)

No code change required.  Chronological clarification only: the I05R2
sequence closes the staged handle before `AFTER_WRITE_BEFORE_FSYNC` and
performs durability fsync through `fsync_file()` afterwards:

```
open → write → flush → close → AFTER_WRITE_BEFORE_FSYNC
→ reopen/fsync via fsync_file → verify → publish → dir fsync → success
```

The essential invariant is unchanged and remains proven by the I05R2
fsync-spy matrix: ZERO fsync calls occur before the
`AFTER_WRITE_BEFORE_FSYNC` fault.  Historical I05R2 prose is preserved
untouched per §2.

## 8. Fresh Baseline (§26)

Pre-repair HEAD baseline (recorded because 9ffcf997 is the I05R2 evidence
freeze itself, so historical counts DO attest this start point — the
baseline was re-run fresh anyway):

- storage: **828 passed / 0 failed / 3 skipped** (831 collected)
- full suite: **2207 passed / 0 failed / 4 skipped** (2211 collected)

## 9. Final Verification (§26/§29)

| Check | Result |
|---|---|
| storage | **855 passed / 0 failed / 3 skipped** (858 collected) |
| full suite | **2234 passed / 0 failed / 4 skipped** (2238 collected) |
| ruff (changed scope) | clean |
| mypy (changed scope) | clean (pre-existing `probes/planner.py:79` baseline only) |
| network calls | 0 |
| provider source changes | none |
| historical I05/I05R1/I05R2 evidence | untouched |
| I06 started | **NO** |

Final passing counts exceed the fresh baseline (+27 storage, +27 full).

## 10. Machine Evidence (§25)

Deterministic, byte-stable across two generations (asserted in-test):

- `BLOC_04_I05R3_LINEAGE_IDENTITY_MATRIX.json` — 7 cases:
  `context_lmid_exact`, `alternate_lmid_same_projection`,
  `duplicate_lineage_projection_restart`, `idempotent_healthy`,
  `idempotent_source_corrupt`, `idempotent_context_missing`,
  `idempotent_artifact_corrupt`.
- `BLOC_04_I05R3_TIME_CONTRACT_MATRIX.json` — 8 cases:
  `naive_logical_start`, `naive_logical_end`, `naive_min_provider_time`,
  `naive_max_provider_time`, `naive_created_at`,
  `offset_aware_normalized`, `persisted_naive_reload`,
  `inverted_provider_range`.

No wall-clock content (injected `FIXED` clock; fixed identities).

## 11. Required Test Coverage (§21)

All 16 required cases green:

1. context L1 + commit L2 → `LineageContextBindingConflict` ✔
2. alternate manifest not durably written ✔
3. restart with two manifests claiming one projection → fail closed ✔
4. resolver resolves through `context.lineage_manifest_id` ✔
5. idempotent healthy commit succeeds after full revalidation ✔
6. idempotent after source-blob corruption fails ✔
7. idempotent after context loss (restart) fails ✔
8. idempotent after T0B corruption fails ✔
9–13. naive logical start/end, min/max provider time, created_at rejected ✔
14. offset-aware non-UTC accepted and normalized ✔
15. persisted naive fragment fails reload ✔
16. inverted provider range rejected ✔

Plus: I05R2 schema/T0-value/crash/duplicate-ref regressions and I05R1
restart/corruption regressions all remain green (within the 855/2234).

## 12. Gates

- [x] exact start `9ffcf997...`
- [x] historical evidence untouched
- [x] three-way context/lineage binding before publication
- [x] alternate lineage manifest rejected + never durable
- [x] duplicate projection-lineage ownership fails closed on restart
- [x] resolver lineage lookup through context lmid
- [x] idempotent commit re-proves the durable chain (incl. physical T0B)
- [x] source/context/artifact corruption prevents idempotent success
- [x] naive projection-context timestamps rejected; aware normalized to UTC
- [x] provider min/max ordering enforced; nothing manufactured
- [x] persisted naive timestamp fails closed on reload
- [x] no SourceRevision implementation (I06 locked)
- [x] no I07+ work, no DuckDB/Postgres/RawEvidenceQuery
- [x] network = 0; provider code unchanged
- [x] 0 test failures; ruff clean; changed-scope mypy clean
- [x] I06 NOT started; research NOT resumed

## 13. Proposed Verdicts

1. `PASS_SENSOR_B4_I05R3_LINEAGE_IDENTITY_TIME_SEALED` — earned.
2. Then operator may accept `PASS_SENSOR_B4_I05R2_FAIL_CLOSED_PUBLIC_API_SEALED`.
3. Then `PASS_SENSOR_B4_I05R1_DURABLE_END_TO_END_LINEAGE_SEALED`.
4. Then `PASS_SENSOR_B4_I05_RAW_PROJECTION_LINEAGE`.

**Recommended next:** SENSOR-B4-I06 SOURCE REVISION / MUTATION REGISTRY —
**NOT authorized; NOT started.**

**STOP GATE honored.** Evidence returned to operator.
