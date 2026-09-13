# SENSOR-B4-I07 — DURABLE JOB STATE + RESUME COUPLING

**Checkpoint:** SENSOR-B4-I07 (Durable Job State + Resume Coupling)
**Status:** COMPLETE — proposed `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab

---

## 1. Starting SHA

`d09941e75f3da6040254e0e6193dcf670207273b` — the merged PR #3 merge commit on
`main`.  Per operator ratification, `agent/crypto-sensor-fabric-build` was
fast-forwarded to `d09941e7` first (no force, no content change), then the
governance-only ratification commit `b5c8edfe` (SENSOR-B4-I06R1-RATIFY) was
committed and pushed to the crypto branch only (operator standing directive:
crypto branch only, never `main`).

## 2. Commit Chain (no squash)

| Commit | Stage |
|---|---|
| `b5c8edfe` | SENSOR-B4-I06R1-RATIFY (governance only; branch fast-forwarded to main `d09941e7` beforehand) |
| `37a54678` | I07A: durable job state repository with frozen state machine and §16 resume gate (29 tests) |
| `00a47ccd` | I07B: job↔evidence coupling adversarial proof + typed divergence conflicts (11 tests) |
| *(this commit)* | I07C: two deterministic machine matrices + evidence MD + ledger freeze |

## 3. Authority & Scope

Frozen authority: `bloc_04/03_INTEGRITY_ATOMICITY_REVISION_AND_RECOVERY.md`
§15 (job durability: the frozen 12-state vocabulary and "a job may not move
backward silently") and §16 (resume invariant: default `MANIFEST_COMMITTED`
floor; the cursor never advances past unindexed evidence), plus §20 crash
tests 6/7 and the freeze-manifest sequence item
`SENSOR-B4-I07 durable job state/resume coupling`.  The frozen I01 vocabulary
(`StorageJobStatus`, `StorageJobState`, `StorageJobTransition` — built in I01
"vocabulary only; transitions in I07") is used verbatim: ONE canonical
vocabulary, no shadow enums/models (I06R1 §3-§5 doctrine).

NOT in scope (stop gate): recovery scanner, orphan reconciliation, quota,
DuckDB, Postgres, RawEvidenceQuery, provider integration, Bloc 5 (I08+ own
these).

## 4. What Was Built

`quant-lab/src/crypto_sensor_fabric/storage/jobs.py` —
`DurableJobStateRepository`:

- **Append-only durable chain per job**: birth record (PLANNED) + one
  immutable event record per transition (`DurableJsonCatalog`, hashed
  physical names, no-clobber publish, staging → fsync → verify → publish →
  dir fsync).  Current state is MATERIALIZED from the chain — never mutated
  in place.  `StorageJobTransition` records are the public chain view;
  `get_job` returns the frozen `models.StorageJobState`.
- **§15 state machine**: single-step forward progression along the frozen
  linear order; silent backward moves forbidden (and not even a reason can
  legalize PLANNED-entry); entering failure states requires a nonempty
  reason; `FAILED_RETRYABLE → ACQUIRING` retry and
  `CHECKPOINT_ADVANCED → ACQUIRING` batch continuation are the ONLY legal
  annotated backward edges; terminal states (`FAILED_TERMINAL`,
  `QUARANTINED` in v1) have no exits; `expected_from` CAS guard.
- **§16 resume gate** (`advance_checkpoint`): the resume token becomes the
  active resume point ONLY after resolving durable truth — acquisition
  exists, blob physically verified (`has_verified_physical`), and (default
  floor `MANIFEST_COMMITTED`) the manifest exists durably AND contains the
  batch blob.  The explicitly configurable weaker floor `RAW_COMMITTED`
  skips only the manifest check.  `CHECKPOINT_ADVANCED` is reachable ONLY
  through the gate (plain transitions targeting it are typed-conflict
  rejected).  A refused gate NEVER advances the cursor (fail closed).
- **Idempotence without stale trust** (§68 + I05R3 §10 doctrine): an exact
  retry of the already-advanced batch re-proves durable truth before
  returning the committed state; divergent semantics under the same event
  slot are a typed `JobTransitionConflict`, visible after restart.
- **Crash safety**: every state change is ONE atomic catalog commit;
  `AFTER_DIR_FSYNC_BEFORE_RETURN` lost-return races adopt on exact retry
  (disk truth re-derived through a fresh repository — the faulted
  in-memory cache is never trusted); `BEFORE_STAGED_WRITE` crashes leave
  the old chain intact.
- **Coordination**: per-job file lock + in-process lock, re-entrant within
  one thread (the gated path re-enters the transition path), bounded 30s
  wait, locks never auto-deleted (I08 owns stale recovery).
- **Restart validation (fail closed)**: chain linkage, contiguity,
  chronology (never backward), frozen-vocabulary enforcement, and durable
  re-anchoring (I06R1 §11 doctrine) — every committed checkpoint anchor
  (acquisition/manifest) must still resolve durably, anchored blobs must
  still be physically verified.

## 5. Machine Evidence

| Matrix | Cases |
|---|---|
| `BLOC_04_I07_JOB_STATE_MATRIX.json` | 8: forward_chain_contiguous, single_step_enforced, backward_moves_annotated_only, failure_requires_reason, retry_resume_requires_reason, terminal_no_exits, cas_guard, crash_and_identity — all PASS, byte-deterministic |
| `BLOC_04_I07_RESUME_COUPLING_MATRIX.json` | 8: checkpoint_gate_proven_advance, gate_refuses_uncommitted_batch, gate_refuses_status_below_floor, weak_floor_raw_committed, crash_before_advancement_retry_completes (§20 #6), crash_after_publication_adoption, divergent_retry_conflict, restart_reanchoring — all PASS, byte-deterministic |

Both matrices are generated by PURE builders in memory/tmp dirs and
byte-compared against the committed artifacts by pytest (read-only
governance); normal test execution never writes the evidence tree.

## 6. Verification Results

- **Storage suite:** 1000 passed / 0 failed / 3 skipped (fresh baseline
  939/0/3 measured at the I06R1 freeze point + ratification adds none) —
  +61 I07 test nodes, ≥ baseline, 0 failures.
- **ruff:** clean on `jobs.py`, `test_job_state.py`,
  `test_job_state_adversarial.py`, `test_i07_evidence.py`.
- **mypy:** clean on `jobs.py` (the single remaining
  `probes/planner.py:79` error is the documented pre-existing baseline,
  untouched since SENSOR-B2-I02).
- **Evidence governance:** pytest leaves the evidence tree byte-identical
  (verified by `test_evidence_directory_untouched_after_run` and by
  `git status` after suite runs).
- **network = 0; provider source unchanged.**

## 7. Doctrinal Notes

- **One vocabulary**: frozen `StorageJobStatus` / `StorageJobState` /
  `StorageJobTransition` used verbatim; no I07-local clones.
- **No silent backward moves**: every non-forward move carries an explicit,
  persisted reason or is rejected.
- **The cursor never advances past unindexed evidence**: the gate resolves
  acquisition + physical-verification + manifest-committed proof from
  durable truth, never from caller claims.
- **Idempotence ≠ stale trust**: exact retries re-prove; divergence is
  visible and typed.
- **I08 boundary honored**: stale locks and quarantined jobs are preserved
  as recovery evidence, never auto-repaired here.

## 8. Proposal

Proposed verdict: `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED`.
Recommended next checkpoint: SENSOR-B4-I08 RECOVERY / QUARANTINE (NOT
authorized, NOT started).  `DURABLE_RESUME_IMPLEMENTED = TRUE` is now
earned; `RECOVERY_SCANNER_IMPLEMENTED = FALSE`.
