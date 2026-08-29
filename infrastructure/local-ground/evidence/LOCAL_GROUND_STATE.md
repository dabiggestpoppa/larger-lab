# OCE Local Ground — State Ledger (B1-LOCAL, A-003)

**Updated:** 2026-08-29
**Branch:** `oce-program-build`
**Decision:** `LOCAL_FIRST_CLOUD_ACTIVATION_DEFERRED`
**Amendment:** OCE-AMEND-A003

## Independent ledger fields

> **CORRECTED 2026-08-29 (repair cycle):** the previous readiness claim was
> premature (Docker absent locally; authoritative CI failed). See
> `B1-LOCAL-READINESS-CORRECTION.md`. Active state below until a successful
> authoritative CI run is operator-confirmed.

| Field | Value (repair cycle, after local static revalidation) |
|---|---|
| `local_ground_state` | VERIFYING |
| `cloud_plan_state` | VALIDATED_NO_APPLY |
| `cloud_activation_state` | DEFERRED_BY_OPERATOR |
| `cloud_deployment_state` | NOT_DEPLOYED |
| `cloud_cost_state` | ZERO |
| `next_local_book` | BLOCKED_PENDING_B1_REPAIR |
| `operator_hold_reason` | AUTHORITATIVE_CI_CONFIRMATION_PENDING |

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
