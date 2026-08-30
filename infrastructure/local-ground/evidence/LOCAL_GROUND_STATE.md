# OCE Local Ground — State Ledger (B1-LOCAL, A-003)

**Updated:** 2026-08-30 (final truth repair)
**Branch:** `oce-program-build`
**Decision:** `LOCAL_FIRST_CLOUD_ACTIVATION_DEFERRED`
**Amendment:** OCE-AMEND-A003

> **CORRECTED 2026-08-30 (final truth repair):** the `READY_FOR_OPERATOR_REVIEW`
> recommendation published after the successful run `33283003794` (OCE_RUN_ID
> `2e65b0a9c4e7`) was **withdrawn pending repaired authoritative execution**.
> That run genuinely passed the checks that existed; a later source review
> found recovery-truth gaps (rollback, exact-value proof, Redis invalidation,
> unavailable-service execution, receipt preservation, archival completeness).
> See `B1-LOCAL-FINAL-TRUTH-CORRECTION.md`. No evidence was falsified or
> discarded; the prior packet
> `B1-LOCAL-REVIEW-PACKET-FINAL-2e65b0a9c4e7.md` is superseded, not deleted.
>
> **RESOLVED 2026-08-30:** the repaired authoritative run **`33311614613`**
> (OCE_RUN_ID **`f767fadd3d67`**, tested HEAD `7e5e91c1`) concluded **success**
> (150/150 passed, 0 skipped, gate 60/60 AUTHORITATIVE_CI) and is the sole
> basis for the current readiness claim. The corrected packet is
> `B1-LOCAL-REVIEW-PACKET-FINAL-f767fadd3d67.md`.

## Independent ledger fields

| Field | Value (2026-08-30, after repaired authoritative CI success) |
|---|---|
| `local_ground_state` | READY_FOR_OPERATOR_REVIEW |
| `cloud_plan_state` | VALIDATED_NO_APPLY |
| `cloud_activation_state` | DEFERRED_BY_OPERATOR |
| `cloud_deployment_state` | NOT_DEPLOYED |
| `cloud_cost_state` | ZERO |
| `next_local_book` | BLOCKED_PENDING_OPERATOR_RATIFICATION |
| `operator_hold_reason` | OPERATOR_RATIFICATION_REQUIRED |

Readiness is published only because the repaired authoritative CI run
`33311614613` succeeded and its downloaded artifact independently
reconciled (150/150 passed, 0 skipped, gate 60/60 AUTHORITATIVE_CI). Book 2
stays locked pending separate operator ratification. Cloud remains
`DEFERRED_BY_OPERATOR` / `NOT_DEPLOYED` / `ZERO`, 0 mutations, $0 cost.

## Recovery-contract correction (2026-08-29)

> The earlier ledger claim — *"a zero-exit restore with missing rows is now
> impossible"* — is **superseded by execution evidence**. Authoritative CI run
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
  links) are rejected before extraction — with 9 dedicated regressions
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

> **SUPERSEDED pending final truth repair (2026-08-30).** Run `33283003794`
> genuinely passed the checks that existed. The `READY_FOR_OPERATOR_REVIEW`
> recommendation it supported was withdrawn after a source review found
> recovery-truth gaps (see `B1-LOCAL-FINAL-TRUTH-CORRECTION.md`). The run's
> evidence remains valid historical truth; it is not deleted or rewritten.

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
stage-status.json); the superseding review packet was
`B1-LOCAL-REVIEW-PACKET-FINAL-2e65b0a9c4e7.md` (now superseded pending this
final repair). The failed-run history (including `33277742603`, `33280331533`,
`33280678356`, `33281049669`, `33282094530`, `33282648769`) is preserved, not
rewritten. **No claim of `BOOK_1_COMPLETE`, `GATED_COMPLETE`,
`BOOK_2_AUTHORIZED`, or `CLOUD_DEPLOYED` is made** — the operator must ratify.

## Final truth repair cycle (2026-08-30)

A source review of the recovery contract found gaps the existing gate did not
cover (rollback semantics, exact-value proof, transient Redis invalidation,
unavailable-service execution, receipt preservation, archival completeness).
Repaired as B1-L7R25..R27 + B1-L8R7..R9 (see
`B1-LOCAL-FINAL-TRUTH-CORRECTION.md` for the full sequence):

- **R25 phase-safe recovery rollback:** explicit promote/finalize/rollback
  state machine; quarantine held until every fallible verification passes;
  rollback driven by actual phase (not the inverse of `promoted`); existence
  proven via the `pg_database` catalog before any ALTER/DROP DATABASE; invalid
  `ALTER DATABASE IF EXISTS` syntax removed; truthful rollback receipt fields;
  injected-failure rollback container tests.
- **R26 protected values and fingerprints:** deterministic per-table value
  fingerprints (md5 over sorted canonical row-JSON) in the protected
  inventory; staging/canonical/external-boundary/rollback verifiers compare
  fingerprints, so identical counts with different values fail closed.
- **R27 transient Redis invalidation:** after PostgreSQL and artifact
  replacement pass final verification, the local cache is invalidated and
  verified; Redis is never restored; invalidation failure blocks success with
  a preserved receipt; stale cache never survives replacement of truth.
- **L8R7 unavailable-service execution:** the full-backup-block regression
  (and postgres/artifact-unavailable variants) execute in CI via a controlled
  fake command environment — never skipping, never touching the shared stack.
- **L8R8 immutable indexed receipts:** every operation gets one unique ID and
  an append-only index entry; receipts live in `operations/<operation-id>/`
  with recorded hashes; duplicates fail; a `latest.json` pointer is not
  authoritative.
- **L8R9 final recovery truth in the gate:** the independent gate requires
  the negative tests to execute, the rollback regression to genuinely run, the
  success operation to prove fingerprints + quarantine-held-then-dropped +
  Redis invalidation, valid phase ordering, zero skips in CI, and hash-verified
  operation receipts — a green test count cannot override a failed invariant.

Local static revalidation on the repaired implementation: hardening 39
passed, gate regressions 43 passed (including the new recovery-truth
rejections), portability/compose/contract suites green. The authoritative
container-backed CI run on the repaired implementation is pending and is the
sole basis for the next readiness claim.

## Final truth repair closure (2026-08-30)

Authoritative CI run **`33311614613`** (workflow `b1-local-ground-validation`,
push, OCE_RUN_ID **`f767fadd3d67`**) on tested HEAD
`7e5e91c1fc49a461f27cfeb49994e3f4d176ac4f` / tree
`85cb2379f614dde118670194dc6a08c59b1f3f54` concluded **success**:

- **150 collected / 150 executed / 150 passed / 0 failed / 0 errors /
  0 skipped** — zero skips; `mandatory_skipped: 0`.
- Container-backed: **21 / 21 executed, 21 passed**, 0 skipped — including
  the new post-promotion injected-failure rollback, rollback-failure
  regression, and Redis-invalidation-failure blocking tests.
- Unavailable-service negative tests **executed and passed** in CI (fake
  command environment; no skips).
- Independent gate: **PASS 60/60** (`AUTHORITATIVE_CI`); source-clean pre/post
  `true`; cleanup verified; adversarial 8/8; operation index **23 operations
  hash-verified**; success ops prove fingerprints + quarantine
  held-then-dropped + Redis invalidation; rollback regression executed;
  invalid rollback SQL absent; cloud `0` mutations / `ZERO` /
  `DEFERRED_BY_OPERATOR` / `NOT_DEPLOYED`.
- Artifact `b1-local-ground-evidence-f767fadd3d67` (id `9732205709`), zip
  SHA-256 `ea65df1ba5c7cfae1cdc67ef2df247bf2b495e57926e2ba9d076c54a69af0b41`,
  downloaded and independently reconciled (evidence-manifest 37/37 match;
  recovery-ops verify ok).

Evidence archived in `evidence/runs/f767fadd3d67/` (exact zip byte-for-byte +
complete expanded artifact + per-file hashes); the corrected packet is
`B1-LOCAL-REVIEW-PACKET-FINAL-f767fadd3d67.md`. The prior successful run
`33283003794`, all failed runs, and every prior packet remain preserved. **No
claim of `BOOK_1_COMPLETE`, `GATED_COMPLETE`, `BOOK_2_AUTHORIZED`, or
`CLOUD_DEPLOYED` is made** — the operator must ratify.

## Machine-readable copy

The same fields are enforced by `contracts/local-ground-contract.json`
(`ledger_model`) and written live by `scripts/oce-ctl local status` into
`var/state.json`.

## Change record

- 2026-08-29 — A-003 ratified; Local Ground split from Cloud Activation; cloud
  purchase hold preserved as historical truth; zero cloud cost, zero cloud
  mutations.
- 2026-08-29 — Local Ground static validation passed (RUN `52f60c556f50`); a
  premature READY claim was published (superseded).
- 2026-08-29 (repair) — Readiness claim corrected after authoritative CI
  failed (run `33256476708`, phase `doctor`, `wsl` FileNotFoundError): state
  is VERIFYING / BLOCKED_PENDING_B1_REPAIR / AUTHORITATIVE_CI_FAILED.
- 2026-08-29 (repair) — Repairs B1-L7R3..R9 + R6R1..R6R3 pushed; local static
  suite revalidated on the repaired implementation (RUN `316637514bfa`):
  67 passed / 0 failed / 0 errors / 14 truthful container skips (Docker
  absent on this host), independent gate 34/34 PASS (LOCAL_STATIC mode),
  final-package verifier PASS, cloud plan deterministic + zero mutation,
  cloud apply denied rc 5. Result `LOCAL_STATIC_READY_CI_REQUIRED` — full
  readiness requires the authoritative container-backed CI run, which the
  operator must confirm (repo is private; the agent cannot read Actions).
  Active state: local_ground_state=VERIFYING, cloud_plan_state=
  VALIDATED_NO_APPLY (revalidated), next_local_book=BLOCKED_PENDING_B1_REPAIR,
  operator_hold_reason=AUTHORITATIVE_CI_CONFIRMATION_PENDING. Cloud fields
  remain DEFERRED_BY_OPERATOR / NOT_DEPLOYED / ZERO; 0 mutations; $0 cost.
- 2026-08-29/30 — Recovery-contract repair series B1-L7R21..R24 + B1-L8R5..R6
  pushed from `d3df9eb4` and iterated to green: authoritative run
  `33283003794` succeeded (116 passed / 0 failed, 18/18 container-backed,
  gate 45/45 AUTHORITATIVE_CI). Active state updated to
  READY_FOR_OPERATOR_REVIEW pending separate operator ratification;
  next_local_book=BLOCKED_PENDING_OPERATOR_RATIFICATION. Cloud unchanged
  (DEFERRED_BY_OPERATOR / NOT_DEPLOYED / ZERO; 0 mutations; $0).
- 2026-08-30 (final truth repair) — Source review found recovery-truth gaps in
  the `33283003794` gate coverage (rollback, exact-value proof, Redis
  invalidation, unavailable-service execution, receipt preservation, archival
  completeness). The READY_FOR_OPERATOR_REVIEW recommendation was withdrawn
  pending repaired authoritative execution; repair series B1-L7R25..R27 +
  B1-L8R7..R9 pushed from `f79e5ed0`. Active state:
  local_ground_state=VERIFYING, next_local_book=BLOCKED_PENDING_B1_REPAIR,
  operator_hold_reason=RECOVERY_TRUTH_GAPS. Cloud unchanged
  (DEFERRED_BY_OPERATOR / NOT_DEPLOYED / ZERO; 0 mutations; $0). `main`
  untouched.
- 2026-08-30 (final truth repair, resolved) — The repaired authoritative run
  `33311614613` (OCE_RUN_ID `f767fadd3d67`, HEAD `7e5e91c1`) succeeded after
  the bytes-stdout decode fix (`7e5e91c1`): 150/150 passed, 0 skipped, gate
  60/60 AUTHORITATIVE_CI, container-backed 21/21, operation index 23 ops
  verified. Active state updated to READY_FOR_OPERATOR_REVIEW pending
  separate operator ratification; next_local_book=
  BLOCKED_PENDING_OPERATOR_RATIFICATION. Evidence archived in
  `evidence/runs/f767fadd3d67/`; corrected packet
  `B1-LOCAL-REVIEW-PACKET-FINAL-f767fadd3d67.md`. Cloud unchanged
  (DEFERRED_BY_OPERATOR / NOT_DEPLOYED / ZERO; 0 mutations; $0). `main`
  untouched at `7e7ef722`.
