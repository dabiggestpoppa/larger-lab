# SENSOR-B4-I05R4 — EVIDENCE IMMUTABILITY + SEALED VERIFIER + SERVICE RETRY SEAL

**Checkpoint:** SENSOR-B4-I05R4 (Evidence Immutability + Sealed Verifier + Service Retry)
**Status:** COMPLETE — proposed `PASS_SENSOR_B4_I05R4_EVIDENCE_INTERFACE_RETRY_SEALED`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab

---

## 1. Starting SHA

`aa74232f091a0ee249692e03bf2422dd275d00ea` (I05R3D evidence freeze).
Verified exactly at session start; clean tree; required I05R3 lineage
(`7793abca` → `bd75954b` → `1814c82c` → `aa74232f`) present.

## 2. Ending SHA / Commit Chain

| Commit | Stage |
|---|---|
| `5a982b80` | I05R4A: make checkpoint evidence tests read-only and portable |
| `f08c3019` | I05R4B: seal mandatory artifact-verifier interface in lineage commits |
| `1855844c` | I05R4C: make projection context/service retry idempotent across clock movement |
| `b9802e39` | I05R4D: add partial-chain retry, evidence-immutability and interface adversarial proofs |
| *(this commit)* | I05R4E: freeze I05R4 evidence and ledger |

No squash.

## 3. Four-Dimension Audit Disposition (§3)

**BLOCKING NOW — accepted and closed in this checkpoint:**

1. Evidence tests mutate frozen evidence — closed (R4A, §10–§13).
2. Optional `hasattr` physical-verification gate — closed (R4B, §4–§8).
3. Service retry/idempotence defeated by clock movement — closed
   (R4C/R4D, §19–§30).

**FIX NARROWLY NOW — closed:**

4. Hardcoded `C:/tmp_r3e_proj` / `C:/tmp_e2e_proj` acceptance roots —
   replaced by pytest `tmp_path`-derived roots (R4A, §16).
5. Dynamic `__import__("pyarrow", ...)` noise in I05R3 evidence fixture —
   replaced by a plain `import pyarrow as pa` (R4A, §18).

**PARKED — recorded as `DESIGN_DEBT_PARKED`, deliberately not touched:**

| # | Item | Register key |
|---|---|---|
| 6 | Split 1,401-line `projections.py` | `PARKED_I05_DESIGN_DEBT: PROJECTIONS_MODULE_DECOMPOSITION` |
| 7 | ~1,000-line test-suite deduplication (no `conftest.py`; 4 Stack classes; ≥8 `_acq` builders; 18 duplicated clocks) | `PARKED_I05_DESIGN_DEBT: TEST_FIXTURE_CONSOLIDATION` |
| 8 | Remove/deprecate `get_by_projection` (diagnostic surface retained per §34) | `PARKED_I05_DESIGN_DEBT: GET_BY_PROJECTION_RETENTION` |
| 9 | `json_entry` JSON round-trip helper | `PARKED_I05_DESIGN_DEBT: JSON_ENTRY_CLEANUP` |
| 10 | Broad pydantic conversion of `ProjectionCatalogRecord` | `PARKED_I05_DESIGN_DEBT: CONTEXT_MODEL_PYDANTIC` |

Cleanup scope was deliberately prevented from delaying I06 (§32/§33/§35).

## 4. Defect B Repair — Read-Only Evidence Policy (§10–§15)

**The defect:** I05R3 evidence tests wrote the regenerated matrix into the
committed evidence tree, then compared generation #1 against generation #2
— a production behavior change would silently rewrite governance history
and the test would still pass.

**The repair:**

- Generators are pure: `build → dict`, serialized canonically in memory by
  `stable_evidence_bytes(payload)` (§31). The test layer compares bytes; it
  does not own publication.
- I05R3 tests now assert: generation #1 == generation #2 == **committed
  file bytes**. A future behavior change that alters matrix output FAILS.
- Same read-only pattern applied to I05R1 and I05R2 matrix tests.
- I05R4's own matrices follow §14: generated once explicitly by a
  human-invoked publication step, committed, then verified read-only by
  tests. The I05R3 self-update bug was not recreated (§38).
- `EVIDENCE_DIR` is now read-only from pytest's perspective (§12).

**Worktree immutability proof (§15):** after the full storage suite and
full sensor-fabric suite at the final state:

```
git diff --exit-code -- quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_04
→ EVIDENCE TREE CLEAN
git status --porcelain (evidence paths, tracked files) → empty
aggregate sha256 of tracked evidence tree → b3b66e5e16bcbaa2b8bae57a959af336d15df1e9ff575e8f338cb06c12257b8a
= identical to the pre-checkpoint baseline (§41)
```

Historical I05/I05R1/I05R2/I05R3 evidence bytes are untouched (§2).

## 5. Defect A Repair — Sealed Verifier Contract (§4–§9)

- New `runtime_checkable` `ProjectionArtifactVerifier` Protocol
  (`projection_lineage.py`): `get(projection_id)` +
  `verify_physical(projection_id) -> None` (§5).
- `ProjectionLineageRepository` enforces the capability at **CONSTRUCTION**
  via `isinstance(artifact_repository, ProjectionArtifactVerifier)`; a
  substitute exposing `get` without `verify_physical` raises
  `LineageConfigurationError` before any lineage can exist (§7).
- The commit path now calls `self._artifact_repository.verify_physical(pid)`
  **UNCONDITIONALLY** on every first and idempotent commit — the
  `hasattr(...)` optional branch is deleted (§6).
- Verifier failure (`ProjectionCorruption` on T0B drift) propagates through
  idempotent re-commit — no cached success (§8; spy test proves
  `verify_physical` fires on every commit path, §36.2).
- §9 honored: service construction guards unchanged; capability contracts
  replaced private-attribute probing; no service redesign.

## 6. Defect C Repair — Retry Across Clock Movement (§19–§30)

- **Doctrine (§20/§21/§22):** `created_at` is first-seen operational
  metadata. `ProjectionContextRepository.commit` compares ALL scientific /
  structural immutable fields (projection_id, provider, venue,
  sensor_family, native_instrument, source_granularity, partition_key,
  logical_date_start/end, projection_schema_id/version, schema_key,
  schema_fingerprint, parser_version, projection_uri, projection_sha256,
  row_count, min/max_provider_time, lineage_manifest_id, quality_flags)
  and excludes ONLY `created_at`.
- Identical scientific re-commit returns the FIRST committed record —
  original `created_at` preserved, never rewritten, fragment untouched
  (§23). Any scientific difference still raises `ProjectionIdentityConflict`
  (§24; proven across provider, partition, schema version, parser version,
  projection SHA, lineage_manifest_id, row_count, quality flags).
- **Real service T1→T2 double-commit (§25):** attempt 1 at T1, attempt 2 at
  T2 with repositories restarted from disk — SUCCESS; artifact physically
  re-verified; context reuses the T1 record; lineage revalidates; no
  duplicate scientific identity.
- **Context-before-lineage crash state (§26):** physical T0B + artifact +
  context durable, lineage absent — the production resolver FAILS CLOSED
  on manifest projection-ref validation. Partial science never masquerades
  as a complete chain.
- **Partial-chain retry (§27/§28):** retry at T2 through the real
  `T0BProjectionService` completes the missing lineage; the physical file,
  artifact metadata and T1 context are reused, NOT deleted or rewritten;
  resolver passes afterward and the recovered chain survives a full
  repository restart (§36.18).
- **Alternate lineage retry (§29):** same projection_id + different
  `lineage_manifest_id` → typed failure; the I05R3 three-way binding
  remains authoritative.
- **Changed rows retry (§30):** same projection_id + scientifically
  different rows → `ProjectionIdentityConflict`; retry is not overwrite
  permission.

## 7. Portable Test Roots (§16/§17)

- `test_end_to_end_projection.py`: `Chain.root = tmp_path / "t0b"`;
  `C:/tmp_e2e_proj` and its global teardown removed.
- `test_i05r3_evidence.py`: `Stack.root = tmp_path / "t0b"`;
  `C:/tmp_r3e_proj` removed; the dynamic `__import__('hashlib')` physical-key
  computation replaced by the canonical `catalog_physical_key` helper.
- Narrow consolidation only — no mass test rewrite (§17/§33).

## 8. Machine Evidence (§37/§38)

Deterministic, byte-stable, generated in memory and verified read-only
against the committed files:

- `BLOC_04_I05R4_EVIDENCE_IMMUTABILITY_MATRIX.json` — 5 cases:
  `i05r3_lineage_generated_matches_committed` (TRUE),
  `i05r3_time_generated_matches_committed` (TRUE),
  `pytest_evidence_tree_unchanged`,
  `portable_i05r3_root` (hardcoded absent / tmp_path present),
  `portable_e2e_root` (hardcoded absent / tmp_path present).
- `BLOC_04_I05R4_VERIFIER_INTERFACE_MATRIX.json` — 4 cases:
  `artifact_verifier_valid`, `artifact_verifier_missing_verify_physical`
  (fails at construction, `LineageConfigurationError`),
  `artifact_verify_failure_propagates`, `lineage_commit_unconditional_verify`
  (no `hasattr` in the commit path — source-level proof).
- `BLOC_04_I05R4_SERVICE_RETRY_MATRIX.json` — 8 cases:
  `context_t1_t2_idempotent` (first preserved), `context_scientific_conflict`,
  `service_repeat_complete_chain`, `partial_context_without_lineage_not_visible`,
  `partial_context_retry_completed`, `alternate_lmid_retry_rejected`,
  `changed_projection_retry_rejected`, `restart_after_retry_valid`.

No wall-clock nondeterminism.

## 9. Baseline (§40) and Final Counts (§43)

Fresh pre-change HEAD baseline (recorded, not copied):

- storage: **855 passed / 0 failed / 3 skipped** (858 collected)
- full suite: **2234 passed / 0 failed / 4 skipped** (2238 collected)

Final state:

| Check | Result |
|---|---|
| storage | **872 passed / 0 failed / 3 skipped** (875 collected) |
| full suite | **2251 passed / 0 failed / 4 skipped** (2255 collected) |
| ruff (changed scope) | clean |
| mypy (changed scope) | clean (pre-existing `probes/planner.py:79` baseline only) |
| network calls | 0 |
| provider source changes | none |
| evidence tree after suites | git diff clean; tracked bytes identical to baseline |
| I05R3 UTC/time tests | green (within the 872/2251) |
| I05R2 public-API/schema/crash tests | green |
| I05R1 restart/corruption tests | green |

Final passing counts exceed the fresh baseline (+17 storage, +17 full).

## 10. Gates

- [x] exact start `aa74232f...`; historical I05–I05R3 evidence bytes untouched
- [x] I05R3 + I05R4 evidence tests never write the evidence tree
- [x] regenerated I05R3 matrices equal committed bytes (both)
- [x] post-suite evidence git diff clean; tracked hash identical to baseline
- [x] no hardcoded `C:/tmp_r3e_proj` or `C:/tmp_e2e_proj` acceptance roots
- [x] lineage artifact verifier contract explicit; missing capability fails at construction
- [x] no `hasattr`-based optional verification in the commit path
- [x] every lineage first/idempotent commit calls the physical verifier; failure prevents success
- [x] `created_at` offset-aware, first-seen, never rewritten, excluded from scientific identity alone
- [x] all other context fields remain strict immutable identity
- [x] real service T1→T2 rerun succeeds; partial chain not resolver-valid; retry completes lineage
- [x] partial retry preserves durable intermediate truth; alternate lmid retry fails; changed bytes fail
- [x] recovered chain survives full restart
- [x] broad `projections.py` refactor NOT performed; broad test rewrite NOT performed
- [x] I06 NOT started; network = 0; provider source unchanged
- [x] 0 failures; ruff clean; mypy changed-scope clean; research NOT resumed

## 11. Proposed Verdicts

1. `PASS_SENSOR_B4_I05R4_EVIDENCE_INTERFACE_RETRY_SEALED` — earned.
2. Then operator may accept `PASS_SENSOR_B4_I05R3_LINEAGE_IDENTITY_TIME_SEALED`.
3. Then `PASS_SENSOR_B4_I05R2_FAIL_CLOSED_PUBLIC_API_SEALED`.
4. Then `PASS_SENSOR_B4_I05R1_DURABLE_END_TO_END_LINEAGE_SEALED`.
5. Then `PASS_SENSOR_B4_I05_RAW_PROJECTION_LINEAGE`.

**Recommended next:** SENSOR-B4-I06 SOURCE REVISION / MUTATION REGISTRY —
**NOT authorized; NOT started.**

**STOP GATE honored.** Evidence returned to operator.
