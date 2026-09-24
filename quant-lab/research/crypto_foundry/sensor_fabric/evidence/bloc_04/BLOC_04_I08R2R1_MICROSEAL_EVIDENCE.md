# SENSOR-B4-I08R2R1 — Evidence Truth + Lock-Clear Race + Canonical Record Microseal

**Checkpoint:** `SENSOR-B4-I08R2R1`  
**Branch:** `agent/crypto-sensor-fabric-build`  
**Mandatory start:** `cc97de4709407cad2d3204db6e184c42254b13fe`  
**Main baseline:** `7c7816f382947bbc8a1f2154435fc436f2428fa8` (unchanged)  
**Operator state:** proposed seal only; no self-ratification; I09 not authorized or started.

## 1. Commit chain

1. `d0b0360e` — `SENSOR-B4-I08R2R1A: repair evidence truth derivation and prove false-green counterfactual`
2. `79469d4e` — `SENSOR-B4-I08R2R1B: close lock-clear race and bind exact terminal outcomes`
3. `3ee122ab` — `SENSOR-B4-I08R2R1C: publish measured matrices and preserve historical bytes`
4. `SENSOR-B4-I08R2R1D` — this evidence narrative, governance reconciliation, final gates, and push

No merge, rebase, reset, amend, squash, or force push was used.

## 2. Operator findings reproduced

### 2.1 False-green I08R2 evidence

The committed historical `BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json` contains two material false-green rows:

- `crash_after_unlink_replays_original` reported `result=OK` while `replay_closed=false` because the builder measured the return of `apply_plan`; that return lists newly applied actions and is not the restart replay report.
- `present_lock_intent_not_false_completed` reported `result=OK` while `no_action=false` and `report_left_open=false` because the proof executed a full scan, creating a legitimate separate record-only action instead of isolating the open explicit-clear operation with an empty plan.

The builder also derived several measured verdicts from hard-coded `OK` values rather than from required invariants. The executable proof, not the JSON, was repaired.

### 2.2 Lock-clear final-boundary race

The old `clear_job_lock` flow released the per-job `RLock` between the final ownership checks and `Path.unlink()`. Another local thread could acquire that same lock authority and establish a live owner before the stale clear unlinked the physical lock.

### 2.3 Canonical-record seams

Targeted attacks reproduced all three unsafe or inaccurate states:

- aware `+05:00` timestamps passed validation despite the claimed actual-UTC contract;
- malformed `before_state` or `after_state` JSON leaked `json.JSONDecodeError`;
- terminal ownership accepted a coarse run/action/object/problem match without exact `operation_id` binding and a full canonical comparison to the named action's resolution and after-state.

## 3. Repairs

- Corrected I08R2 lock scenarios now read `RecoveryEngine.last_replay_report`; open-operation isolation uses an empty plan. Every measured row declares `required_invariants`, and `result` is `OK` if and only if every named invariant is boolean `true`.
- The forced-false crash row keeps every other success predicate but sets `replay_closed=false`; its committed verdict is `FAIL`.
- `clear_job_lock` holds the repository's per-job `RLock` continuously across final owner-map validation, physical unlink, and parent-directory fsync, releasing only in `finally`.
- Operation timestamps now require an aware value with exactly zero UTC offset. Writers canonicalize through `coerce_utc`; durable validation rejects naive and non-zero offsets with `RecoveryOperationCorrupt`.
- Malformed state JSON is wrapped as `RecoveryOperationCorrupt`.
- RecoveryActions carry exact `operation_id` operational binding. Terminal writers verify that binding and resolution; terminal replay also recomputes action identity and compares canonical full outcome, including resolution and after-state, with the terminal claim.
- Replay adoption of an action-without-terminal now seals the exact durable action resolution rather than regenerating different outcome wording.

## 4. Deterministic R2R1 matrices

- `BLOC_04_I08R2R1_EVIDENCE_TRUTH_MATRIX.json` — 5 rows: 4 measured/preservation rows `OK`, plus 1 deliberate forced-false counterfactual row `FAIL`.
  - SHA-256: `ae4d5a6afe0ba130b585113abc2150992d898553072640eb20a3a8146cd4d01e`
- `BLOC_04_I08R2R1_LOCK_CLEAR_RACE_MATRIX.json` — 3 rows, all `OK`: contender blocked at both unlink and fsync, exact successful order, and held-lock refusal without unlink.
  - SHA-256: `a334ae9738e5d57d8eba351c995638ffd1c2ec257f0b6221fd5f95c6daaf3e6f`
- `BLOC_04_I08R2R1_CANONICAL_RECORD_MATRIX.json` — 7 rows, all `OK`: UTC acceptance/rejections, two malformed-state attacks, coarse-action rejection, and exact-bound-action/divergent-outcome rejection.
  - SHA-256: `e2c26c422a5beabf311affadee09d46d4aceac5479ae86cf54b2acf823cc698e`

Normal pytest generates these matrices only in temporary directories and byte-compares them to the committed files. A meta-test evaluates every committed R2R1 row from its declared required invariants.

The successful clear order is mechanically observed as:

`INTENT -> UNLINK -> FSYNC -> EFFECT -> RecoveryAction -> COMPLETED`

A separate contender thread cannot acquire the per-job authority at either the unlink or fsync boundary. A lock already held by another thread causes typed refusal and leaves the physical lock intact.

## 5. Historical evidence preserved

Historical false-green evidence was not rewritten. Preservation is both semantic and byte-exact:

- `BLOC_04_I08_CRASH_MATRIX.json` — `cc5c71694a9177314c2a872a28463c7c0d531a6805bc6a9f26083949f195d63f`
- `BLOC_04_I08_QUARANTINE_MATRIX.json` — `4f501f64da491fb62003377fdd7999c35983b7f4119be70b44563bc713fcc9e0`
- `BLOC_04_I08_RECOVERY_IDEMPOTENCE_MATRIX.json` — `7a82d6c52bd0acfd59e682684128d4f8c8b9f672ae7c7aa5399c303a57251913`
- `BLOC_04_I08_RECOVERY_SCAN_MATRIX.json` — `8a288e8bbe6ddbd39a03480b08bc573e54b92a59b1cf08f72d8dc2817aabb237`
- `BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json` — `d951399cfdb09e5164be8a38515744baf3ebb3f56f6b07c48fb23d79579d829d`
- `BLOC_04_I08R1_EFFECT_ATOMICITY_MATRIX.json` — `21b0ea691448fbe16a00982838864c0e064c0187808c2f3d4fe09c398fb29e35`
- `BLOC_04_I08R1_LOCK_RUN_ID_MATRIX.json` — `c71d06fe14f7c15137a8ae57529af51289cea4d1cbe823ce21e5976917efc8a8`
- `BLOC_04_I08R1_STREAMING_QUARANTINE_MATRIX.json` — `4f2146f415dfc5fed3b6f5e71d57b2f7ff55af9d415046f70de2c84cc5d37c06`
- `BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json` — `a119bfa98367552ed77cc35015513532305a274d4c634df041c9cc65dd043713`
- `BLOC_04_I08R2_OPERATION_RECORD_INTEGRITY_MATRIX.json` — `c3983023de941edc220abb51d6bb2a9095ab34b44e8b3a7c822bed40b712beb3`
- `BLOC_04_I08R2_OPERATION_TERMINALITY_MATRIX.json` — `86625d2df8ea329df61420f29f56e070f40bbafb149ca917c6855946c1d40ba8`

## 6. Verification

- Focused R2R1 evidence + adversarial modules: **17 passed**.
- I08R2/I08R1/I07 focused regression set: **66 passed**.
- Complete `crypto_sensor_fabric/storage` suite: **1263 passed / 0 failed / 4 skipped**.
- Complete project gate `pytest tests/ -q`: first run reproduced the documented unrelated blob-store concurrency flake (**2641 passed / 1 failed / 5 skipped**); the isolated failed test passed on rerun; the final full run was **2642 passed / 0 failed / 5 skipped**.
- Unscoped repository-root `pytest -q` is not claimed as valid: a pre-existing research module executes `sys.exit(0)` during import. The valid full gate is `pytest tests/ -q`.
- Ruff on every changed Python scope: `All checks passed!`.
- compileall on changed modules: passed.
- mypy using the repository convention (`MYPYPATH=src python -m mypy src/crypto_sensor_fabric/storage/recovery.py`): only the pre-existing `src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]` dependency error; no new `recovery.py` error.
- The seven known pre-I05-era evidence files showed their known CRLF-only churn during broad suites and were restored; no historical content delta is included.
- Provider adapter source diff from the mandatory start: zero. I09/quota/storage-estimator diff: zero. Network calls: zero.

## 7. Governance and stop gate

`PASS_SENSOR_B4_I08R2R1_EVIDENCE_TRUTH_LOCK_RACE_CANONICAL_SEALED = PENDING_OPERATOR_REVIEW` (proposed; not self-ratified).

`PASS_SENSOR_B4_I08R2_OPERATION_TERMINALITY_EVIDENCE_CONSISTENCY_SEALED = OPERATOR_HOLD`  
`PASS_SENSOR_B4_I08R1_CRASH_TRUTH_EFFECT_ATOMICITY_LOCK_AUTHORITY_SEALED = OPERATOR_HOLD`  
`PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_HOLD`  
`RECOVERY_SCANNER_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`  
`DURABLE_RESUME_IMPLEMENTED = TRUE`  
`next_checkpoint_authorized = FALSE`  
`recommended_next = operator review of the complete I08 -> I08R1 -> I08R2 -> I08R2R1 chain.`

I09 may begin only after explicit operator acceptance. This checkpoint stops after push.
