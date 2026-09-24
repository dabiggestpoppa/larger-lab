# SENSOR-B4-I08R2R1-RATIFY — Complete Recovery Chain Operator Acceptance

**Branch:** `agent/crypto-sensor-fabric-build`  
**Ratification start:** `311fd52b75298e181d5c20f796bff130e8b16770`  
**Documentation correction:** `a349d874` — `SENSOR-B4-I08R2R1-DOC`  
**Main:** unchanged at `7c7816f382947bbc8a1f2154435fc436f2428fa8`

## Accepted chain

The operator accepts the complete chain:

- I08 recovery/quarantine — `00898d66`
- I08R1 effect atomicity and lock authority — `3e6d8614`
- I08R2 operation terminality — `cc97de47`
- I08R2R1 evidence truth, lock-race, and canonical record closure — `311fd52b`

The dedicated documentation commit `a349d874` changes no behavior. It aligns
`clear_job_lock()` documentation with the sealed durable order:

`INTENT → final ownership authority → unlink → parent-directory fsync → EFFECT_COMMITTED → RecoveryAction → COMPLETED`

## Historical evidence treatment

Historical I08, I08R1, and I08R2 matrices remain immutable. Their known
false-green rows are retained as counterfactual evidence of why I08R1,
I08R2, and I08R2R1 were required. Operator acceptance applies to the
superseding implementation and the new I08R2R1 evidence, not to the false
claims inside historical matrices. No historical matrix was regenerated or
rewritten.

Superseding evidence:

- `BLOC_04_I08R2R1_EVIDENCE_TRUTH_MATRIX.json`
- `BLOC_04_I08R2R1_LOCK_CLEAR_RACE_MATRIX.json`
- `BLOC_04_I08R2R1_CANONICAL_RECORD_MATRIX.json`
- `BLOC_04_I08R2R1_MICROSEAL_EVIDENCE.md`

## Verification

- Focused recovery/resume gate: **54 passed**
- Storage suite: **1263 passed / 0 failed / 4 skipped**
- Project gate `pytest tests/ -q`: **2642 passed / 0 failed / 5 skipped**
- The existing Windows manifest-visibility warning was recorded as a warning,
  not a failure.
- Ruff on changed recovery scope: **passed**
- py_compile/compileall: **passed**
- mypy: only the pre-existing `src/crypto_sensor_fabric/probes/planner.py:79`
  dependency error; no new `recovery.py` error.
- Historical evidence hash gates: **passed**
- Provider-source diff from `311fd52b`: **zero**
- I09/quota/storage-estimator diff: **zero**
- Network: **zero**

## Governance transition

- `PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_ACCEPTED`
- `PASS_SENSOR_B4_I08R1_CRASH_TRUTH_EFFECT_ATOMICITY_LOCK_AUTHORITY_SEALED = OPERATOR_ACCEPTED`
- `PASS_SENSOR_B4_I08R2_OPERATION_TERMINALITY_EVIDENCE_CONSISTENCY_SEALED = OPERATOR_ACCEPTED`
- `PASS_SENSOR_B4_I08R2R1_EVIDENCE_TRUTH_LOCK_RACE_CANONICAL_SEALED = OPERATOR_ACCEPTED`
- `RECOVERY_SCANNER_IMPLEMENTED = TRUE`
- `DURABLE_RESUME_IMPLEMENTED = TRUE`
- `G4-02_ATOMIC_DURABILITY_GATE = IMPLEMENTATION_PASS`
- `next_checkpoint_authorized = TRUE`
- `next_checkpoint = SENSOR-B4-I09 QUOTA / STORAGE ESTIMATOR`
- `authorized_scope = I09 ONLY`

I10+ remain unauthorized. Research remains frozen. I09 was not begun in this
ratification prompt; its authorization takes effect only after this governance
commit is pushed.
