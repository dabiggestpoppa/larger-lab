# OCE Local Ground â€” State Ledger (B1-LOCAL, A-003)

**Updated:** 2026-08-30
**Branch:** `oce-program-build`
**Decision:** `LOCAL_FIRST_CLOUD_ACTIVATION_DEFERRED`
**Amendment:** OCE-AMEND-A003

## Independent ledger fields

> **CORRECTED 2026-08-29 (repair cycle):** the previous readiness claim was
> premature (Docker absent locally; authoritative CI failed). See
> `B1-LOCAL-READINESS-CORRECTION.md`. The active state below reflects the
> **successful authoritative CI run `33283003794`** (OCE_RUN_ID
> `2e65b0a9c4e7`) and remains pending **separate operator ratification** —
> Book 1 is not self-completing and Book 2 stays locked.

| Field | Value (2026-08-30, after authoritative CI success) |
|---|---|
| `local_ground_state` | READY_FOR_OPERATOR_REVIEW |
| `cloud_plan_state` | VALIDATED_NO_APPLY |
| `cloud_activation_state` | DEFERRED_BY_OPERATOR |
| `cloud_deployment_state` | NOT_DEPLOYED |
| `cloud_cost_state` | ZERO |
| `next_local_book` | BLOCKED_PENDING_OPERATOR_RATIFICATION |
| `operator_hold_reason` | OPERATOR_RATIFICATION_REQUIRED |

## Recovery-contract correction (2026-08-29)

> The earlier ledger claim â€” *"a zero-exit restore with missing rows is now
> impossible"* â€” is **superseded by execution evidence**. Authoritative CI run
> `33277742603` (OCE_RUN_ID `be4d71f601b6`) reached the Docker acceptance
> phase (104 executed / 100 passed / 4 failed) and failed truthfully on four
> recovery-contract defects:
>
> 1. `test_09_clean_room_local_restore_succeeds`
> 2. `test_10_restore_meets_declared_recovery_targets`
> 3. `test_30_documented_operator_walkthrough_passes`
> 4. `test_ctl_clean_room_database_artifact_restore`
>
> The first three restored a full dump into a populated DB and failed on
> `relation "state_probe" already exists`; the fourth returned success without
> recovering `b1=alpha`/`b2=beta`. This disproved the fail-closed-restore claim
> and exposed the undefined recover contract (silent backup-scope switching,
> no explicit restore mode, plain-SQL recovery, overwritten diagnostics).
>
> The failed claim is preserved, not deleted. The current state remains
> `VERIFYING`; the blocker is the recovery-mode and database-promotion
> contract (B1-L7R21..R24, B1-L8R5..R6). No readiness claim is published
> until authoritative CI succeeds. Book 2 stays locked. Cloud remains
> `DEFERRED_BY_OPERATOR` / `NOT_DEPLOYED` / `ZERO`, 0 mutations, $0 cost.

## Runtime repair cycle (2026-08-29)

Failed authoritative CI run `33257653064` (OCE_RUN_ID `f6514d95caed`, phase
`acceptance-tests`, cleanup `not-run`) exposed runtime defects, repaired as
B1-L7R10..R16:

- Prometheus `/-/ready` healthcheck; invalid config fails closed;
- single session-scoped compose stack owner with verified volume cleanup;
- portable `docker compose ps --format json` parser (array / object / NDJSON);
- bounded PostgreSQL readiness after every start/restart;
- isolated Redis-loss test (only Redis container+volume destroyed;
  PostgreSQL truth and volume identity survive);
- portable script execution (exec modes `100755`, bash invocation);
- real clean-room backup/restore of PostgreSQL + artifacts into empty volumes;
- failure-safe cleanup and diagnostics that never mask the exit code and never
  mutate evidence after the final manifest;
- gate/verifier require machine-readable cleanup + AUTHORITATIVE_CI evidence.

Local static revalidation (RUN `b02d61777638`): gate PASS 34/34, 79 passed /
0 failed / 0 errors / 16 truthful container skips (no Docker on this host),
final-package verifier PASS, `LOCAL_STATIC_READY_CI_REQUIRED`.

## Final-runtime closure cycle (2026-08-29)

Authoritative CI run `33269051570` (OCE_RUN_ID `e883791fd22c`) reached the
Docker-backed acceptance phase (95 executed / 91 passed / 4 failed) and
failed truthfully on runtime defects now repaired as B1-L7R17..R20,
B1-L8R3, B1-L8R4:

- **R17 health convergence:** the shared stack must reach simultaneous stable
  health (bounded deadline + stability window) after every full start, restart
  or `down`/`up`; no transition test returns while any mandatory service is
  still `starting`; safe-shutdown test restores the stack afterward.
- **R18 fail-closed restore:** PostgreSQL dumps applied with `ON_ERROR_STOP`
  inside a single transaction, readiness verified before restore, restore
  receipts written; a zero-exit restore that loses rows is now impossible
  (B1-L7R18).
- **R19 backup/artifact hardening:** `backup-info.json` is hash-protected
  inside the manifest; unsafe manifest paths (absolute / `..` / duplicate /
  missing / malformed) and unsafe artifact tar members (absolute path, OOB
  links) are rejected before extraction â€” with 9 dedicated regressions
  (B1-L7R19).
- **L8R3 structured logs + pre-teardown diagnostics:** the log test verifies
  the json-file driver + rotation options independently and accepts combined
  stdout+stderr (PostgreSQL logs on stderr); a pre-teardown hook captures
  real container diagnostics before the session fixture removes them.
- **gate/test reconciliation:** every mandatory container test must execute
  and pass in CI; hardening suite added to the shared runner.

Local static revalidation (RUN `02ec89b0f012`): gate PASS 42/42, 104
collected / 87 passed / 0 failed / 0 errors / 17 truthful container skips,
final-package verifier PASS, `LOCAL_STATIC_READY_CI_REQUIRED`. Full
readiness requires the authoritative container-backed CI run on the repaired
implementation, which awaits operator confirmation (private repo).

## Authoritative closure cycle (2026-08-30)

Authoritative CI run **`33283003794`** (workflow `b1-local-ground-validation`,
push, OCE_RUN_ID **`2e65b0a9c4e7`**) on tested HEAD
`22a30401df1ab5b7fd6121c1f5ac9e75246aa4e0` / tree
`1b0208a0a5f944781ee3c98506c3d6173ebe2756` concluded **success**:

- **117 collected / 117 executed / 116 passed / 0 failed / 0 errors / 1
  skipped** (the single skip is the live-stack-aware block regression,
  `mandatory_skipped: 0`).
- Container-backed: **18 / 18 executed, 18 passed**, 0 skipped — real
  clean-room DB+artifact restore, populated-target full replacement,
  corrupt-backup rejection, persistence/restart, Redis-loss, structured
  logs, safe shutdown and verified cleanup.
- Independent gate: **PASS 45/45** (`AUTHORITATIVE_CI`); source-clean pre
  and post `true`; cleanup verified (containers/network/volumes removed);
  adversarial 8/8; cloud `0` mutations / `ZERO` / `DEFERRED_BY_OPERATOR` /
  `NOT_DEPLOYED`.
- PostgreSQL promotion receipt in CI: staging/canonical/final verification
  all `ok` (`backup_probe 2, replace_probe 2, state_probe 4`), `promoted`,
  `quarantine_dropped`, `exit_status 0`, `redis_restored false`, PG 16.2.
- Artifact `b1-local-ground-evidence-2e65b0a9c4e7` (id `9723589216`), zip
  SHA-256 `1706d61fec025cbbeb03927966bc8c554d3caf6b330108831d0c39af6d763425`.

Evidence archived in `evidence/runs/2e65b0a9c4e7/` (PROVENANCE.json +
stage-status.json); the superseding review packet is
`B1-LOCAL-REVIEW-PACKET-FINAL-2e65b0a9c4e7.md`. The failed-run history
(including `33277742603`, `33280331533`, `33280678356`, `33281049669`,
`33282094530`, `33282648769`) is preserved, not rewritten. **No claim of
`BOOK_1_COMPLETE`, `GATED_COMPLETE`, `BOOK_2_AUTHORIZED`, or
`CLOUD_DEPLOYED` is made** — the operator must ratify.

## Machine-readable copy

The same fields are enforced by `contracts/local-ground-contract.json`
(`ledger_model`) and written live by `scripts/oce-ctl local status` into
`var/state.json`.

## Change record

- 2026-08-29 â€” A-003 ratified; Local Ground split from Cloud Activation; cloud
  purchase hold preserved as historical truth; zero cloud cost, zero cloud
  mutations.
- 2026-08-29 â€” Local Ground static validation passed (RUN `52f60c556f50`); a
  premature READY claim was published (superseded).
- 2026-08-29 (repair) â€” Readiness claim corrected after authoritative CI
  failed (run `33256476708`, phase `doctor`, `wsl` FileNotFoundError): state
  is VERIFYING / BLOCKED_PENDING_B1_REPAIR / AUTHORITATIVE_CI_FAILED.
- 2026-08-29 (repair) â€” Repairs B1-L7R3..R9 + R6R1..R6R3 pushed; local static
  suite revalidated on the repaired implementation (RUN `316637514bfa`):
  67 passed / 0 failed / 0 errors / 14 truthful container skips (Docker
  absent on this host), independent gate 34/34 PASS (LOCAL_STATIC mode),
  final-package verifier PASS, cloud plan deterministic + zero mutation,
  cloud apply denied rc 5. Result `LOCAL_STATIC_READY_CI_REQUIRED` â€” full
  readiness requires the authoritative container-backed CI run, which the
  operator must confirm (repo is private; the agent cannot read Actions).
  Active state: local_ground_state=VERIFYING, cloud_plan_state=
  VALIDATED_NO_APPLY (revalidated), next_local_book=BLOCKED_PENDING_B1_REPAIR,
  operator_hold_reason=AUTHORITATIVE_CI_CONFIRMATION_PENDING. Cloud fields
  remain DEFERRED_BY_OPERATOR / NOT_DEPLOYED / ZERO; 0 mutations; $0 cost.
- 2026-08-29/30 â€” Recovery-contract repair series B1-L7R21..R24 + B1-L8R5..R6
  pushed from `d3df9eb4` and iterated to green: authoritative run
  `33283003794` succeeded (116 passed / 0 failed, 18/18 container-backed,
  gate 45/45 AUTHORITATIVE_CI). Active state updated to
  READY_FOR_OPERATOR_REVIEW pending separate operator ratification;
  next_local_book=BLOCKED_PENDING_OPERATOR_RATIFICATION. Cloud unchanged
  (DEFERRED_BY_OPERATOR / NOT_DEPLOYED / ZERO; 0 mutations; $0).
