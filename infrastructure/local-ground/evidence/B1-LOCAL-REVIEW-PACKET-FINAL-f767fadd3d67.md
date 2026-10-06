# OCE Book 1 — Local Ground Corrected Review Packet (B1-LOCAL, final truth repair)

**Date:** 2026-08-30 (final truth repair)
**Branch:** `oce-program-build`
**Starting SHA (required):** `f79e5ed0bf6287e043a7cbcd58c60109048b3529` (tree `042470a6f4b766019b0a5866c3c373fd90aed645`)
**Implementation HEAD (tested):** `7e5e91c1fc49a461f27cfeb49994e3f4d176ac4f`
**Tested tree:** `85cb2379f614dde118670194dc6a08c59b1f3f54`
**Supersedes:** `B1-LOCAL-REVIEW-PACKET-FINAL-2e65b0a9c4e7.md` (superseded 2026-08-30, preserved) and the
withdrawal in `B1-LOCAL-FINAL-TRUTH-CORRECTION.md`
**Correction records:** `B1-LOCAL-FINAL-TRUTH-CORRECTION.md`, `B1-LOCAL-READINESS-CORRECTION.md`
**Authoritative CI run:** `33311614613` (workflow `b1-local-ground-validation`, push)
**OCE_RUN_ID:** `f767fadd3d67`
**Artifact:** `b1-local-ground-evidence-f767fadd3d67` (id `9732205709`)
**Artifact zip SHA-256:** `ea65df1ba5c7cfae1cdc67ef2df247bf2b495e57926e2ba9d076c54a69af0b41`
**Durable archive:** `evidence/runs/f767fadd3d67/` (exact zip + complete expanded artifact + per-file hashes)
**Recommendation:** **`READY_FOR_OPERATOR_REVIEW`**

---

## 1. What this packet is (and is not)

This packet publishes the **repaired authoritative execution evidence** for
the OCE Book 1 Local Ground final truth repair (B1-L7R25..R27, B1-L8R7..R9,
plus follow-on fixes). It supersedes the earlier readiness claim from run
`33283003794` — that run genuinely passed the checks that existed, but a
source review found recovery-truth gaps the prior gate did not cover; this
packet is the corrected claim backed by the repaired run.

This packet does **not** claim `BOOK_1_COMPLETE`, `GATED_COMPLETE`,
`BOOK_2_AUTHORIZED`, or `CLOUD_DEPLOYED`. Book 1 requires **separate operator
ratification**; Book 2 remains locked. Cloud remains `DEFERRED_BY_OPERATOR` /
`NOT_DEPLOYED`, 0 mutations, recurring cost `$0`.

## 2. The final truth repair series

| Commit | Repair | Content |
|---|---|---|
| `55947dbd` + `6a6a7be2` | B1-L7R25 | phase-safe PostgreSQL recovery: explicit promote/finalize/rollback state machine; quarantine held until every fallible verification passes; catalog existence checks; invalid `ALTER DATABASE IF EXISTS` removed; truthful rollback receipts; injected-failure rollback container tests |
| `e71508d8` + `7e5e91c1` | B1-L7R26 | protected recovery values and fingerprints (md5 over sorted canonical row-JSON per table); staging/canonical/boundary/rollback verifiers compare values, not only counts; independent `pg-verify.py` boundary verifier; bytes-stdout decode fix |
| `6c7a3279` | B1-L7R27 | transient Redis invalidation after successful full replacement (never restored; invalidation failure blocks success; rolled-back recovery leaves the cache untouched) |
| `f66c8b75` | B1-L8R7 | unavailable-service regressions execute in CI via a controlled fake command environment (never skip; never touch the shared stack) |
| `01c29aab` + `0758f2ef` | B1-L8R8 | immutable indexed recovery receipts: one unique operation ID per operation; append-only index with per-receipt hashes; duplicates fail; `latest.json` is not authoritative |
| `468c8086` | B1-L8R9 | independent gate enforces final recovery truth: negative tests execute, rollback regression genuinely runs, success ops prove fingerprints + quarantine-held-then-dropped + Redis invalidation, valid phase ordering, zero CI skips, hash-verified operation index |
| `b80fff44` | B1-L9R3 | corrected premature review state: `VERIFYING` / `BLOCKED_PENDING_B1_REPAIR` / `RECOVERY_TRUTH_GAPS`; prior packet superseded (preserved) |

## 3. Authoritative CI evidence (run `33311614613`, OCE_RUN_ID `f767fadd3d67`)

- **Test totals:** 150 collected / 150 executed / **150 passed / 0 failed /
  0 errors / 0 skipped** (`mandatory_skipped: 0`).
- **Container-backed:** 21 / 21 executed, **21 passed**, 0 skipped — including
  real clean-room DB+artifact restore, populated-target full replacement,
  **post-promotion injected-failure rollback**, **rollback-failure
  regression**, **Redis-invalidation-failure blocking**, corrupt-backup
  rejection, persistence across restarts, Redis-loss preservation, structured
  logs, safe shutdown and verified cleanup.
- **Unavailable-service negative path:** `test_full_backup_blocked_without_
  docker_or_services` plus postgres/artifact-unavailable and
  state-only-works-without-docker variants all **executed and passed** in CI
  (no skips).
- **Independent gate:** **PASS 60/60** (`AUTHORITATIVE_CI`) — identity,
  branch/commit/tree, source-clean pre/post (`true`/`true`), totals, zero
  skips, container execution, adversarial 8/8, cloud denial/plan/
  local-after-denied, cleanup verified, recovery receipts, **operation index
  (23 operations, hash-verified)**, **success-op fingerprints + quarantine
  held-then-dropped + Redis invalidation**, **rollback-regression executed**,
  **no invalid rollback SQL**, manifest hashes/sizes, cloud fields
  ZERO/DEFERRED/NOT_DEPLOYED.
- **PostgreSQL recovery receipts (success ops):** promote — `quarantine_held:
  true`, staging/canonical verification `ok` with **value fingerprints**;
  finalize — `promoted: true`, `final_verification: ok` (fingerprints),
  `quarantine_dropped: true`, `quarantine_removal_verified: true`,
  `exit_status: 0`, `redis_restored: false`; phase ordering canonical
  (8+3 phases).
- **Rollback receipts:** injected-failure op — `rollback_required/attempted/
  succeeded: true`, `original_canonical_restored: true`, `rollback_
  verification: ok`, `exit_status: 1`; rollback-failure op — truthfully
  `rollback_failed: true`, original not restored, `exit_status: 1`.
- **Redis:** `redis_restored: false`, `redis_invalidation_required: true`,
  `redis_invalidation_attempted: true`, `redis_invalidated: true`,
  `redis_verification: ok`; the invalidation-failure receipt records
  `redis_failure` and blocks clean success.
- **Cleanup:** `cleanup: ok`; containers, network, and volumes removed
  (verified pre/post evidence).
- **Source-clean:** pre `true`, post `true` (0 dirty files either side).

## 4. Mandatory recovery proofs satisfied in CI

- state-only backup deterministic with or without Docker; full backup blocks
  when PostgreSQL or artifact storage unavailable (executed in CI, never
  skipped).
- state-only restore never touches containers; full backup cannot use
  state-only restore; state-only backup cannot use full-replace restore;
  unknown scope/mode fail closed.
- populated-database and clean-database full replacement both succeed with
  **exact protected values** (fingerprints), not only row counts; staging
  verification failure preserves the original; post-promotion failure rolls
  back and restores the original canonical truth; rollback failure returns
  nonzero and preserves evidence.
- PostgreSQL archive corruption rejected; protected inventory tampering
  rejected; artifact corruption rejected; artifact replacement removes data
  absent from the snapshot; Redis never restored and invalidated only after
  replacement is irreversible; a failed/rolled-back recovery leaves the cache
  untouched.
- Every backup/restore/recovery operation is indexed immutably with
  hash-protected receipts (23 operations); later operations cannot overwrite
  earlier evidence; `latest.json` is not authoritative.
- pre-teardown diagnostics survive runner cleanup unchanged; post-cleanup
  evidence proves containers, networks and test volumes removed.

## 5. Cloud posture (unchanged, verified)

`cloud_mutations: 0` · `cloud_cost_state: ZERO` · `cloud_activation_state:
DEFERRED_BY_OPERATOR` · `cloud_deployment_state: NOT_DEPLOYED` · no
purchases, no provisioned resources, no provider contact, recurring cost `$0`.
`main` remains `7e7ef7222c4ecdea568b34583fd81406165cc9b6` (untouched).

## 6. Operator action required

1. Confirm the authoritative run `33311614613` shows `success`.
2. Download `b1-local-ground-evidence-f767fadd3d67` and verify the zip
   SHA-256 above and internal OCE_RUN_ID `f767fadd3d67`; the durable archive
   in `evidence/runs/f767fadd3d67/` preserves the exact zip byte-for-byte
   plus the complete expanded artifact with per-file hashes.
3. Ratify Book 1 Local Ground readiness for the next Book.

Until the operator ratifies, the state ledger holds
`READY_FOR_OPERATOR_REVIEW` (Book 2 locked, no completion claims).
