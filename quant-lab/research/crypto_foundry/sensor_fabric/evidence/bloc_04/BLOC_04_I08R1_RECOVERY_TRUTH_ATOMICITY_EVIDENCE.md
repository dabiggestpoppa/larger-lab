# SENSOR-B4-I08R1 — Recovery Truth Hardening

**Checkpoint:** SENSOR-B4-I08R1 — recovery effect atomicity + frozen crash-matrix truth + lock-clear authority + run-identity seal
**Branch:** agent/crypto-sensor-fabric-build
**Starting SHA:** 00898d666fa4a595af02321e1eedbf543717a455
**Ending SHA:** the final commit of the chain below (a documentation
correction commit; the evidence-freeze commit itself is `ab15fd9d`)
**Operator review state at freeze:** `PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_HOLD`; I08R1 is `PENDING_OPERATOR_REVIEW` (proposed, not self-ratified); the complete I07 chain remains `OPERATOR_ACCEPTED`; `DURABLE_RESUME_IMPLEMENTED = TRUE`; `next_checkpoint_authorized = FALSE`; I09 NOT started. Historical I08/I07 evidence untouched.

## -1. Commit chain (I08R1A-D, no squash)

- `b83d65ef` SENSOR-B4-I08R1A: make recovery effects journal-first replayable and stream quarantine bytes
- `906ae137` SENSOR-B4-I08R1B: rebuild frozen crash scenarios with true I06 I07 projection and manifest boundaries
- `077494be` SENSOR-B4-I08R1C: seal explicit lock-clear authority generated run identity and typed job scanning
- `ab15fd9d` SENSOR-B4-I08R1D: freeze I08R1 evidence and reconcile ledger
- (final commit) docs correction: replace the pre-written predicted freeze
  SHA in this MD with the actual freeze commit `ab15fd9d` (the freeze SHA
  could not be known before committing; correction commit is the ending SHA)

## 0. Operator defects addressed (§0)

The six operator-found defects, and where each is sealed:

- **A — effect outruns evidence:** recovery-operation journal (`catalogs/recovery/operations/`) with durable INTENT before every irreversible effect (§3-§5 below; source: `RecoveryOperationJournal`, `_record_intent`).
- **B — crash matrix not faithful:** the committed I08 matrix is historical first-pass evidence; the new authoritative `BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json` instantiates the ACTUAL frozen §20 boundaries (§10-§22 below; `test_i08r1_crash_truth.py`).
- **C — lock clear without owner authority:** `clear_job_lock` owner repository is MANDATORY; RLock probe alone is insufficient (§23-§25 below).
- **D — run ids from `id(self)`:** operational generation is `uuid.uuid4().hex` behind a `recovery-` prefix — 128 bits of cryptographic randomness, no process memory, no wall clock (§26 below).
- **E — `read_bytes()` quarantine copy:** `_quarantine_file` streams in bounded chunks with the digest computed in the same pass; a monkeypatch guard proves `Path.read_bytes` never touches the payload (§9/§31 below).
- **F — `_scan_jobs` swallow-all:** only typed job-class failures classify as `JOB_DURABILITY_DIVERGENCE`; `JobLockHeld` is skipped (lock files classify separately); unexpected exceptions propagate (§27 below).

## 1. Recovery-operation journal design (§4)

`RecoveryOperationJournal` over the shared `DurableJsonCatalog` primitive at `<t0_root>/catalogs/recovery/operations/` (`logical_id_field="recovery_operation_id"`). Phases: `INTENT`, `EFFECT_COMMITTED`, `COMPLETED`, `UNRESOLVED`. Operation identity = SHA-256 over the canonical semantic set `(recovery_run_id, action_kind, object_type, object_id, problem, resolution, before_state, after_state)`; registration time is EXCLUDED. Each phase is its own append-only physical row (phase is part of the record key); `EFFECT_COMMITTED` rows are detail-qualified because one operation (the orphan two-step reconciliation) may commit SEVERAL durable effects. Exact retry is idempotent (adopted, not duplicated); divergent content under one record id raises typed `RecoveryActionConflict`; one row is never mutated in place. States are stored as canonical JSON strings (frozen envelope text columns) and parsed where consumed.

## 2. Effect-before-evidence ordering (§3/§5)

Every mutating handler now sequences: revalidate (I08 §28) → `_record_intent` (durable INTENT) → irreversible effect → `_record_effect` (append-only commit phase) → `_record_outcome` (COMPLETED or UNRESOLVED) → frozen `RecoveryAction`. If INTENT publication fails, the exception escapes BEFORE any mutation was attempted. Wired handlers: corrupt-blob quarantine, staging quarantine, orphan-projection quarantine, unknown-context quarantine, orphan-blob two-step reconciliation, orphan-manifest reconciliation, job-divergence transition, lock-only records, and the explicit `clear_job_lock` (INTENT before the unlink).

## 3. Interrupted-operation replay (§6/§8)

`apply_plan` first runs `_finalize_open_operations`: open operations (INTENT/EFFECT_COMMITTED without COMPLETED/UNRESOLVED) whose effect already landed are ADOPTED — quarantine kinds when the canonical object is already absent under a prior durable record for the same object+problem; reconciliation kinds when the exact metadata/acquisition/manifest is already committed. A restarted apply therefore recognizes its own prior effect instead of re-planning over it or misreading it as a stale plan. Adoption only runs inside APPLY; scan stays read-only. Proven: `BLOC_04_I08R1_EFFECT_ATOMICITY_MATRIX.json` cases `quarantine_crash_after_publish_before_source_unlink`, `quarantine_crash_after_source_unlink_before_final_action`, `manifest_reconcile_crash_after_repository_commit_before_final_action`, `repeat_restart_converges`, `no_unjournaled_completed_effect` — all `OK` (8/8 cases in the matrix).

## 4. Orphan-blob two-step reconciliation (§7)

Preflight before any mutation: physical bytes verify against the content-addressed name; registered `EvidenceBlob` identity matches the orphan; acquisition `blob_sha256` matches; existing metadata/acquisition conflicts are typed (`RecoveryActionConflict` / acquisition identity gates) before effect. Then INTENT → step 1 append/adopt exact metadata (EFFECT row, detail-qualified) → step 2 append/adopt exact acquisition (EFFECT row) → COMPLETED. A crash after step 1: the retry scan surfaces a typed `ORPHAN_BLOB_CONTINUATION` finding (metadata durable, acquisition missing) and apply completes step 2 through the public `append_acquisition` API — never "nothing registered" when metadata exists, never a false stale-plan conflict. Proven in `test_crash_8_i06...`-adjacent case `metadata_before_acquisition_registered_context` (crash 2b) and matrix cases `orphan_blob_crash_after_metadata_before_acquisition` / `orphan_blob_retry_completes_acquisition`.

## 5. Streaming quarantine (§9/§31)

`_quarantine_file` copies via `_quar_copy_stream`: fixed 1 MiB chunks, SHA-256 accumulated in the same pass, `fsync` on the staged file, `publish_no_replace` (atomic no-clobber), directory fsync, and source unlink ONLY after the destination is durably present (parent fsync after unlink). Exact retry adopts an identical destination; different bytes at the same deterministic locator raise typed `RecoveryQuarantineConflict`. The §9 proof (`test_large_source_chunked_and_read_bytes_not_used` + matrix `path_read_bytes_not_used`) uses a 4 MiB corrupt payload, shrinks the chunk to 256 KiB to force multiple iterations, and monkeypatches `Path.read_bytes` with a size guard: zero reads ≥ 1 MiB occur during apply. Matrix `BLOC_04_I08R1_STREAMING_QUARANTINE_MATRIX.json`: 6/6 `OK`.

## 6. Corrected frozen crash scenarios (§10-§22, §29)

`BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json` is the authoritative crash-boundary proof: 13 rows (frozen scenarios 1-12 plus crash-2b), each recording `frozen_scenario`, `constructed_pre_crash_state`, `injected_crash_boundary`, `post_restart_state`, `recovery_result`, `cursor_effect`, `history_effect`, `result` — all `OK` under per-scenario verifiers (`_TRUTH` map; booleans legitimately False where doctrine demands False, e.g. crash 6's `cursor_auto_advanced=False`). Key corrections over the historical matrix:

- **Crash 2:** BOTH branches — no context → `unknown_context` quarantine; registered context → replayable metadata+acquisition reconciliation with the mid-commit continuation finding.
- **Crash 3:** real T0A + acquisition durable, projection absent, scan clean (`projection_manufactured=False`) — the frozen "rebuildable, no invention" truth.
- **Crash 4:** a real CATALOGED projection (physical artifact + projection catalog row + T0A lineage) with NO manifest reference is detected (`cataloged_yet_finding=True`) — a catalog row alone is NOT health; recorded evidence-only, artifact never moved.
- **Crash 5:** a VALID v2 fragment (`supersedes == durable v1`, refs verify) durably published before the pointer update; recovery reconciles through the public CAS API; a separate invalid-ancestry test proves an unrelated `supersedes` stays UNRESOLVED (no latest-wins).
- **Crash 6:** the process dies BEFORE `advance_checkpoint` — job still `MANIFEST_COMMITTED` with `checkpoint_anchors=(None, None)`; recovery scan/apply does NOT advance the cursor; a later explicit acquisition/checkpoint retry remains possible.
- **Crash 7:** actual I06 `SourceRevisionRegistry` semantics: same source identity, same exact bytes → `IDENTICAL_REFETCH`, no fake content revision.
- **Crash 8:** actual I06 `SOURCE_MUTATION` with genuinely DIFFERENT bytes (distinct blob sha) at a strictly later `response_observed_at` (I06 §40: same-`seen_at` mutation cannot prove source order and fails closed) — the mutated acquisition is appended ONCE with its final facts (I04 §28 first-append-wins).
- **Crash 9:** corrupt bytes → integrity quarantine (streamed, restart-convergent), canonical unusable, history preserved, operation replayable after interruption.
- **Crash 10:** manifest immutable, target absence explicit, fail-closed; the reappearing-target variant proves the stale-plan typed conflict (bytes restored to the ORIGINAL content sha — mutated bytes would be a different blob).
- **Crash 11 — measured CONTRACT GAP (explicit, not faked):** no public projection-invalidation API exists anywhere in `src/` (`test_crash_11_projection_contract_gap_is_explicit` asserts the absence and will fail if an API appears, forcing an upgrade to real INVALID_PARSER semantics). The scenario proves the recoverable part: T0A retained, projection still cataloged, rebuildable, source never rewritten. No orphan junk file is disguised as parser invalidation.
- **Crash 12:** two writers from the same current pointer; exactly one wins, the loser receives typed `ManifestCASConflict`, the current pointer never silently branches.

## 7. Lock-clear authority (§23-§25, §30)

`clear_job_lock(lock_id, *, expected_job_id, owner_repository, run_id)` — the owner repository is a REQUIRED keyword: omission is a Python-contract refusal (TypeError), `None` is typed `RecoveryConfigurationError`, an owner object without `_lock_owners` truth is refused, a fingerprint mismatch is refused. Before removal: expected job id must hash exactly to the lock id, the lock must exist, the job must have NO live `_lock_owners` entry (the load-bearing check — the RLock probe alone is insufficient because the owning thread can always re-acquire an RLock; `test_clear_same_thread_reentrant_owner_rejected` proves reentrancy cannot bypass the owner map), and the RLock probe must succeed. The RecoveryAction + INTENT are journaled before the unlink. `apply_plan` NEVER clears locks; no TTL; no process-death inference. Matrix `BLOC_04_I08R1_LOCK_RUN_ID_MATRIX.json`: 7/7 `OK` including `foreign_lock_not_auto_deleted` (scan/apply record `lock_present=True, cleared=False` and never delete).

## 8. Run identity (§26, §30)

`new_run_id()` = `f"recovery-{uuid.uuid4().hex}"` — 128 bits of cryptographic randomness per call; no `id(self)`, no process-local counter, no wall-clock formatting, no temp paths. `test_generated_run_ids_cross_instance_unique`: 64 ids across two identical engines at different roots, zero collisions, all 32-hex. Evidence builders/tests pass EXPLICIT deterministic ids (`evidence-run-fixed` etc.); constructor-supplied ids stick for the engine lifetime, call-site ids override once, generation is used only when no explicit id exists.

## 9. Typed job scanning (§27)

`_scan_jobs` catches ONLY `JobError`: `JobLockHeld` (active-writer contention) is skipped — the physical lock file is classified separately as `LOCK_PRESENT_OWNER_UNPROVEN`; other typed job failures (genuine durable-chain/proof failures such as `JobCatalogCorrupt`) classify as `JOB_DURABILITY_DIVERGENCE`. Any OTHER exception (I/O, programming errors) propagates out of `scan` — it must never masquerade as corruption. Proven: `test_healthy_job_currently_lock_held_not_corruption` (healthy chain + held lock → no divergence finding), `test_forged_invalid_chain_is_durability_divergence` (true corruption still detected), `test_unexpected_repository_failure_not_mislabeled` (injected `OSError` propagates typed).

## 10. Historical matrix honesty (§33)

`BLOC_04_I08_CRASH_MATRIX.json` is UNTOUCHED on disk and remains I08's committed evidence. Chronological statement: the I08 crash matrix was a first-pass scenario approximation; operator review found specific cases whose constructed state did not instantiate the frozen boundary (crash 4 uncataloged junk parquet, crash 5 invalid supersedes target, crash 6 called `_checkpoint` FIRST — the opposite boundary, crash 7 proved dedupe not I06 classification, crash 8 reused the same blob sha, crash 11 disguised an uncataloged file as parser invalidation). After I08R1 it must NOT be read as 12/12 authoritative; `BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json` is the authoritative crash-boundary proof. Historical I08 tests encoding a false premise (optional `owner_repository`) were corrected in place per §36 with real job repositories wired; the corrections are documented here.

## 11. I07/I08 regression firewall (§36)

All accepted I07 guarantees remain green in the final recorded runs: validated public `get_job`/`list_transitions`, failed outer-entry rollback, same-thread retry revalidation, catalog RLock, safe hashed lock paths, persisted-floor retries, checkpoint proof V1. Original I08 scan/apply semantics unchanged: read-only deterministic scan, typed conflicts, no silent overwrite, no invented provenance, no latest-wins, no cursor auto-advance, no automatic lock deletion. Historical I08 test-module changes: three lock-clear call sites wired with mandatory owner repositories (defect C contract) — documented in §10; no historical evidence file modified.

## 12. Evidence governance (§40)

Builders in `test_i08r1_evidence.py` are pure; normal pytest generates to tmp and compares byte-for-byte against committed files (`test_generated_matches_committed`, 4 matrices); `test_evidence_directory_untouched_after_run` proves pytest never writes the committed I08R1 evidence. Publication happened once via the explicit module invocation. After the final suites the seven documented pre-existing CRLF-churn legacy files (I03R1/I04 era, whole-file line-ending rewrites with zero content delta, numstat N/N) were restored — evidence tree clean at commit.

## 13. Fresh baseline and final counts (§35)

Fresh baseline at `00898d66` (measured, not copied): storage **1191 passed / 0 failed / 4 skipped**; full **2570 passed / 0 failed / 5 skipped**.

Final at the I08R1 tree (recorded runs at the committed content):
- storage: **1235 passed / 0 failed / 4 skipped** (+44 vs baseline: 23 crash-truth + 16 lock/run-id/streaming + 5 evidence-gate tests, minus 0)
- full: **2614 passed / 0 failed / 5 skipped** (+44)
- zero failures; the documented unrelated blob-store concurrency flake did not reproduce.

## 14. Ruff / mypy (§32) — precise statements

- Ruff: `All checks passed!` on the complete changed scope (`recovery.py`, `test_recovery.py`, `test_recovery_crash_matrix.py`, `test_i08r1_crash_truth.py`, `test_i08r1_lock_runid_streaming.py`, `test_i08r1_evidence.py`).
- mypy production source (`MYPYPATH=src`): `recovery.py` — the ONLY error in its dependency closure is the exact documented pre-existing `probes/planner.py:79 [call-overload]` baseline. No new error class or instance.
- mypy new test modules (source root configured `MYPYPATH=src;tests/crypto_sensor_fabric/storage` + `--explicit-package-bases`, the I07R1G/I07R1H/I08 convention): the three I08R1 modules carry exactly the same error CLASSES as the pre-existing suite baseline — `method-assign` on the injected-death monkeypatches (4 sites, same class the I07-era injected-fault tests use) — and zero import-not-found or arg-type residue. The only remaining error per run is the `probes/planner.py:79` baseline. Repo policy note: the repository has no `[tool.mypy]` section; tests are not part of a clean-gate policy — stated, not claimed clean.

## 15. Scope boundaries (§21/§22/§23/§38)

No I09 (no quota engine, no disk-pressure thresholds, no pause engine); no DuckDB; no Postgres; no RawEvidenceQuery service; no general replay API; no provider integration; no I07 harness extraction; no jobs.py refactor. Network = 0. Provider source unchanged (`git status`: no `providers/` modifications). Research NOT resumed. I09 NOT started.

## 16. Proposed verdict and stop gate (§34/§38/§39)

- `PASS_SENSOR_B4_I08R1_CRASH_TRUTH_EFFECT_ATOMICITY_LOCK_AUTHORITY_SEALED = PENDING_OPERATOR_REVIEW` (proposed; NOT self-ratified).
- `PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_HOLD` (unchanged, awaiting operator acceptance).
- `RECOVERY_SCANNER_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`; `DURABLE_RESUME_IMPLEMENTED = TRUE`; `next_checkpoint_authorized = FALSE`.
- STOP GATE honored: I09 NOT started; research NOT resumed.
