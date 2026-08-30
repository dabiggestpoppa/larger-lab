# OCE Book 1 — Local Ground Final Review Packet (B1-LOCAL, authoritative closure)

**Date:** 2026-08-30
**Branch:** `oce-program-build`
**Starting SHA (required):** `d3df9eb45aeddd8a3dd40ced24a7f2e1d2f0ff41` (tree `53efb9e69b4db2e0326c287d9c4c43aa5199c27b`)
**Implementation HEAD (tested):** `22a30401df1ab5b7fd6121c1f5ac9e75246aa4e0`
**Tested tree:** `1b0208a0a5f944781ee3c98506c3d6173ebe2756`
**Supersedes:** `B1-LOCAL-REVIEW-PACKET.md` (premature claim) and
`B1-LOCAL-REVIEW-PACKET-SUPERSEDING.md` (repair-cycle BLOCKED packet)
**Correction record:** `B1-LOCAL-READINESS-CORRECTION.md`
**Authoritative CI run:** `33283003794` (workflow `b1-local-ground-validation`, push)
**OCE_RUN_ID:** `2e65b0a9c4e7`
**Artifact:** `b1-local-ground-evidence-2e65b0a9c4e7` (id `9723589216`)
**Artifact zip SHA-256:** `1706d61fec025cbbeb03927966bc8c554d3caf6b330108831d0c39af6d763425`
**Recommendation:** **`READY_FOR_OPERATOR_REVIEW`**

---

## 1. What this packet is (and is not)

This packet publishes the **authoritative execution evidence** for the OCE
Book 1 Local Ground recovery-contract closure (B1-L7R21..R24, B1-L8R5..R6).
The full suite ran on the authoritative GitHub Actions runner **with Docker
and PostgreSQL present** and the independent gate passed **45/45 in
`AUTHORITATIVE_CI` mode**.

This packet does **not** claim `BOOK_1_COMPLETE`, `GATED_COMPLETE`,
`BOOK_2_AUTHORIZED`, or `CLOUD_DEPLOYED`. Book 1 requires **separate operator
ratification**; Book 2 remains locked. Cloud remains `DEFERRED_BY_OPERATOR` /
`NOT_DEPLOYED`, 0 mutations, recurring cost `$0`.

## 2. The verified root cause and the repair series

The failed authoritative run `33277742603` (OCE_RUN_ID `be4d71f601b6`) proved
the recovery contract was undefined: silent backup-scope switching, no
explicit restore mode, plain-SQL recovery, and overwritten pre-teardown
diagnostics. The repair series redefined the contract deterministically:

| Commit | Repair | Content |
|---|---|---|
| `e9d0d4aa` | B1-L7R21 | deterministic backup scopes (`--scope state-only\|full`), blocks instead of silent degradation, hash-protected manifest/inventory |
| `36eb5fc0` | B1-L7R22 | explicit restore modes (`--mode state-only\|full-replace --confirm-local-target`), fail-closed cross-checks |
| `48731b7c` | B1-L7R23 | PostgreSQL recovery via verified staging promotion (`pg-recovery.py`, `pg_restore --exit-on-error`, inventory verification, quarantine/rollback) |
| `09d213b7` | B1-L7R24 | safe artifact snapshot replacement + container lifecycle tests (clean-room, populated target, corrupt rejection) |
| `5eb1523f` | B1-L8R5 | pre-teardown / post-cleanup diagnostic namespaces, never overwritten, per-failure identity |
| `ca57b0b7` | B1-L8R6 | ledger truth: superseded premature claim, `VERIFYING`, Book 2 locked, receipt gates |

Follow-on authoritative-iteration fixes on the same series: `426ce2d7`
(valid `--no-privileges` pg_dump flag), `c8d2e0d1` (pg_restore as
`oce_local_admin`), `b5d81407` (live-stack-aware block regression),
`cbb26754` (full Repair-3 receipt + final fail-closed verification),
`6c11797a` (Redis untouched contract), `564a7d80` (durable independent
canonical gate at the restore boundary), `22a30401` (clean-room probe
`-c` binding — the final phantom "missing rows" was a psql flag-binding
defect in the test query, not a restore defect).

## 3. Authoritative CI evidence (run `2e65b0a9c4e7`)

- **Environment:** Ubuntu (Linux `6.17.0-1022-azure`), Python 3.12.14,
  Docker 28.0.4, Compose v2.38.2, real `postgres:16.2-alpine` stack.
- **Test totals:** 117 collected / 117 executed / **116 passed / 0 failed /
  0 errors / 1 skipped** (the single skip is the live-stack-aware block
  regression, skipped truthfully with `mandatory_skipped: 0`).
- **Container-backed:** 18 / 18 executed, **18 passed**, 0 skipped — including
  clean-room DB+artifact restore, populated-target full replacement,
  corrupt-backup rejection, persistence across restarts, Redis-loss
  preservation, structured logs, safe shutdown and verified cleanup.
- **Independent gate:** **PASS 45/45** (`AUTHORITATIVE_CI`) — identity,
  branch/commit/tree, source-clean pre/post (`true`/`true`), totals, zero
  mandatory skips, adversarial 8/8, cloud denial/plan/local-after-denied,
  cleanup verified, recovery receipt in CI, manifest hashes/sizes, cloud
  fields ZERO/DEFERRED/NOT_DEPLOYED.
- **PostgreSQL promotion receipt:** staging → canonical verified (`backup_probe
  2, replace_probe 2, state_probe 4`), `promoted: true`,
  `quarantine_dropped: true`, `final_verification: ok`, `exit_status: 0`,
  `redis_restored: false`, PostgreSQL 16.2.
- **Cleanup:** `cleanup: ok`; containers, network, and volumes removed
  (verified pre/post evidence).
- **Source-clean:** pre `true`, post `true` (0 dirty files either side).

## 4. Mandatory recovery proofs satisfied in CI

- state-only backup deterministic with or without Docker; full backup blocks
  when PostgreSQL or artifact storage unavailable (hardening tests).
- state-only restore never touches containers; full backup cannot use
  state-only restore; state-only backup cannot use full-replace restore;
  unknown scope/mode fail closed.
- populated-database and clean-database full replacement both succeed;
  staging verification failure preserves the original; promotion rollback
  path implemented; zero exit requires verified restored rows (final
  fail-closed canonical gate).
- PostgreSQL archive corruption rejected; protected inventory tampering
  rejected; artifact corruption rejected; artifact replacement removes data
  absent from the snapshot; Redis never restored.
- pre-teardown diagnostics survive runner cleanup unchanged (namespace
  separation regression-gated); post-cleanup evidence proves containers,
  networks and test volumes removed.

## 5. Cloud posture (unchanged, verified)

`cloud_mutations: 0` · `cloud_cost_state: ZERO` · `cloud_activation_state:
DEFERRED_BY_OPERATOR` · `cloud_deployment_state: NOT_DEPLOYED` · no
purchases, no provisioned resources, no provider contact, recurring cost `$0`.
`main` remains `7e7ef7222c4ecdea568b34583fd81406165cc9b6` (untouched).

## 6. Operator action required

1. Confirm the authoritative run `33283003794` shows `success`.
2. Download `b1-local-ground-evidence-2e65b0a9c4e7` and verify the zip
   SHA-256 above and internal OCE_RUN_ID `2e65b0a9c4e7`.
3. Ratify Book 1 Local Ground readiness for the next Book.

Until the operator ratifies, the state ledger holds
`READY_FOR_OPERATOR_REVIEW` (Book 2 locked, no completion claims).
