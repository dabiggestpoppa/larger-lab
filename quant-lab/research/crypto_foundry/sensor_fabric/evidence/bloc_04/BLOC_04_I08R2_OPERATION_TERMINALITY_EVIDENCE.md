# SENSOR-B4-I08R2 — Recovery Operation Terminality Evidence

**Checkpoint:** `SENSOR-B4-I08R2` — interrupted-effect replay + terminal action/phase integrity + final-evidence consistency  
**Branch:** `agent/crypto-sensor-fabric-build`  
**Mandatory start:** `3e6d86142c1bbf26f6dfc8732a6961f255f2a3bc`  
**Operator state at freeze:** `PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_HOLD`; I08R1 and I08R2 are `PENDING_OPERATOR_REVIEW` (proposed, not self-ratified); `RECOVERY_SCANNER_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`; `DURABLE_RESUME_IMPLEMENTED = TRUE`; `next_checkpoint_authorized = FALSE`; I09 not started.

## 1. Commit chain (no squash, no amend)

- `79f48d07` — `SENSOR-B4-I08R2A: make recovery operation replay actually terminal and validate canonical operation records`
- `4b53fffc` — `SENSOR-B4-I08R2B: seal quarantine reconciliation manifest and lock-clear crash ordering`
- `df5754b8` — `SENSOR-B4-I08R2C: add operation terminality integrity counterfactual evidence`
- `SENSOR-B4-I08R2D` — freeze evidence and reconcile ledger (this commit)

## 2. Operator finding closed

The immutable I08R1 matrix remains the counterfactual record of the defect:

- `quarantine_crash_after_source_unlink_before_final_action`: `operation_completed=false`, result `OK`;
- `repeat_restart_converges`: `artifacts_stable=false`, result `OK`;
- `no_unjournaled_completed_effect`: `completed_operations=0`, result `OK`.

Those historical bytes are unchanged. I08R2 corrects semantics prospectively and publishes new live evidence; it does not rewrite the false-green I08R1 rows.

## 3. One authoritative open-operation replayer

`apply_plan` now consumes `_replay_open_operations()` before executing the new plan. The replayer:

1. loads every durable operation-phase row;
2. validates each complete envelope canonically;
3. groups rows by the original `operation_id`;
4. rejects contradictory terminals and operation shapes without INTENT;
5. verifies existing terminal rows name one durable, same-operation final `RecoveryAction`;
6. inspects current storage truth for open operations;
7. adopts only mechanically proven landed effects;
8. appends/adopts a missing EFFECT row when needed;
9. adopts an existing action when only the terminal phase was lost, otherwise materializes exactly one final action;
10. appends COMPLETED under the original `operation_id` and `recovery_run_id`.

The replayer report is retained in `last_replay_report`; it is no longer an ignored advisory list.

## 4. Terminality and action ordering

All mutating handlers now use:

`INTENT -> EFFECT_COMMITTED (as effects land) -> final RecoveryAction -> COMPLETED`

and unresolved paths use:

`INTENT -> final RecoveryAction -> UNRESOLVED`

Terminal rows carry `final_action_id`. Canonical validation rejects a terminal row without it. If the named action is absent or belongs to another run/action/object/problem, replay raises `RecoveryOperationCorrupt` rather than silently accepting an unreconstructable terminal state.

The action-without-terminal crash boundary is explicit: replay searches the original run/action/object/problem, adopts the unique existing action id, and appends the terminal phase. Multiple candidates fail closed. The underlying landed effect is not re-executed.

## 5. Intent fingerprints

The INTENT is now the effect-recognition authority, independent of a possibly absent RecoveryAction. Fingerprints include:

- quarantine source relpath, expected byte length, source SHA-256, category, deterministic destination relpath, and destination SHA-256;
- orphan blob SHA, expected EvidenceBlob semantics, expected acquisition id, and acquisition semantic fingerprint;
- orphan manifest partition/id/version/supersedes, expected current-pointer witness, pointer-unreadable sentinel, and blob references;
- job transition and reason digest;
- lock fingerprint, expected job id, and exact lock relpath.

Pointer unreadability is read before INTENT and carried as a sentinel, so the refusal path still has a durable INTENT before UNRESOLVED.

## 6. Quarantine replay truth table

- INTENT + source present + destination absent: remains open; no invented completion.
- Exact destination present + source present: destination is verified, remaining source unlink finishes, then action + COMPLETED are sealed.
- Exact destination present + source absent: destination is verified from the INTENT SHA/locator, then action + COMPLETED are sealed.
- Source absent + destination absent: remains open.
- Destination contains different bytes: typed `RecoveryOperationCorrupt`; foreign bytes are untouched.

The replayed action and terminal phase preserve the original operation/run. A new restart run does not create a second logical operation or duplicate a quarantine artifact.

## 7. Lock-clear atomicity

Explicit clear is never automatic. After authority and fingerprint validation, durable INTENT is written; live owner-map and RLock state are revalidated immediately before the irreversible unlink. The unlink is followed by parent fsync, EFFECT, the final action with actual `{"lock_present": false, "cleared": true}` state, then COMPLETED.

A crash after unlink but before EFFECT is recognized on restart only when the exact INTENT-fingerprinted path is absent and its lock fingerprint/expected job identity match. The original run is closed with one action and one terminal phase. A present lock with an open INTENT remains open.

## 8. Canonical operation-record integrity

`validate_operation_record` enforces the complete envelope, recomputes operation identity from semantic payload fields, checks phase-qualified record ids, requires aware-UTC registration time, rejects unknown schema/phase/record types, requires EFFECT identity and full detail digest, and requires terminal `final_action_id`.

`EFFECT_COMMITTED` physical keys use the full 64-character SHA-256 of the detail, retiring the 16-character collision surface. Exact retry compares every semantic envelope field except `registered_at`.

Published matrix results:

- `BLOC_04_I08R2_OPERATION_TERMINALITY_MATRIX.json`: 15 cases, all `OK`;
- `BLOC_04_I08R2_OPERATION_RECORD_INTEGRITY_MATRIX.json`: 14 tamper cases, all fail closed as `OK` evidence;
- `BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json`: 9 cases, all `OK`.

Normal pytest regenerates these matrices in temporary directories and compares committed bytes. A separate gate proves pytest does not write the committed I08R2 evidence tree. Publication occurred once by explicit module invocation.

## 9. Historical I07 evidence consistency

The I07R1I ledger matrix previously re-derived historical truth from the live, advancing governance ledger. It is now frozen against the normalized `fd961604` Current-state section (SHA-256 `412da2f97b5d9627101e35ad6ebd68be6bd4aa1e8b643cc4400858feb26cb824`) through a checksum-identified semantic projection. This decouples historical evidence from later checkpoint progression while preserving the committed matrix bytes.

The live ledger advances to I08R2, retains the accepted I07 chain as historical truth, and separately retains an explicitly labeled pre-ratification I07R1I snapshot so old checkpoint-time assertions are not rewritten into current state.

## 10. Verification

- Focused I08R2 tests: 11 passed.
- Ledger repair gates: 3 passed.
- Storage suite: **1246 passed / 0 failed / 4 skipped**. Two warnings came from the existing Windows manifest-pointer visibility test; the test passed.
- Complete project test root: **2625 passed / 0 failed / 5 skipped**.
- Fresh starting-SHA baseline before I08R2 was 1232 passed / 3 failed / 4 skipped; the two ledger failures were inherited and are now green; the documented blob-store concurrency flake did not reproduce in the final storage run.
- Unscoped repository-root `pytest -q` is not a valid gate because a pre-existing research script executes `sys.exit(0)` during import; it reached 91 passed / 0 failed before pytest stopped at collection. The project gate is explicitly `pytest tests/ -q` and is green.
- Ruff: `All checks passed!` on the complete changed Python scope.
- mypy (`MYPYPATH=src python -m mypy src/crypto_sensor_fabric/storage/recovery.py`): only the pre-existing `src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]` dependency error; no new recovery.py error.
- Historical evidence: the superseded I08R1 effect-atomicity matrix remains byte-untouched. The seven pre-I05-era JSON files showed their known CRLF-only churn during broad test runs and were restored; no content delta is included.
- External CI: no external success is claimed. Local/repository verification is reported separately.

## 11. Scope and stop gate

No I09 work: no quota engine, storage estimator, DuckDB, Postgres, RawEvidenceQuery, or provider integration. Network = 0. Provider source unchanged. Research not resumed.

`PASS_SENSOR_B4_I08R2_OPERATION_TERMINALITY_EVIDENCE_CONSISTENCY_SEALED = PENDING_OPERATOR_REVIEW` (proposed, not self-ratified).  
`PASS_SENSOR_B4_I08R1_CRASH_TRUTH_EFFECT_ATOMICITY_LOCK_AUTHORITY_SEALED = PENDING_OPERATOR_REVIEW`.  
`PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_HOLD`.  
`recommended_next = SENSOR-B4-I09 QUOTA / STORAGE ESTIMATOR` only after operator acceptance; `next_checkpoint_authorized = FALSE`.

**STOP after I08R2. I09 was not begun.**
