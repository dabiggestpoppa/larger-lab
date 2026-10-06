# OCE Book 1 Local Ground — Readiness Correction Record

**Date:** 2026-08-29 (repair cycle)
**Branch:** `oce-program-build`
**Supersedes:** the premature `LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW` claim in
`B1-LOCAL-REVIEW-PACKET.md` (evidence commit `793289c6`, packet `1fd3f014`)
and the associated `BUILD_STATUS_LEDGER.md` / `CHECKPOINT_REGISTRY.md` rows.

## What happened (truthful sequence)

1. Local static validation passed (RUN `52f60c556f50`, 37 tests) **but** every
   Docker-backed test was skipped because Docker was absent on the local host.
2. The readiness claim `LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW` was published
   anyway — premature: container behavior was unverified.
3. Authoritative CI runs failed. First observed failure (this repair cycle's
   reference): run `33256476708`, OCE_RUN_ID `2399ec674c09`, **failed phase
   `doctor`**, exact error `FileNotFoundError: [Errno 2] No such file or
   directory: 'wsl'` — the environment doctor probed `wsl` unconditionally on
   Ubuntu, which has no `wsl` executable.
4. Therefore the readiness claim was unsupported. This record supersedes it.

## Corrected active state (until a successful authoritative CI run)

| Field | Value |
|---|---|
| `local_ground_state` | VERIFYING |
| `cloud_plan_state` | NOT_VALIDATED (to be revalidated by the repair run) |
| `cloud_activation_state` | DEFERRED_BY_OPERATOR |
| `cloud_deployment_state` | NOT_DEPLOYED |
| `cloud_cost_state` | ZERO |
| `next_local_book` | BLOCKED_PENDING_B1_REPAIR |
| `operator_hold_reason` | AUTHORITATIVE_CI_FAILED |

## Repair scope (this cycle)

- Platform-safe environment doctor (missing optional tools never raise; WSL
  probed only when present).
- Repository identity corrected to `dabiggestpoppa/larger-lab` everywhere in
  Local Ground (code, contracts, evidence, docs) + regression test.
- Independent gate (32 machine-parseable conditions) + safe finalization
  sequence + read-only final-package verifier.
- Machine-readable test registry (JUnit XML + OCE test-summary JSON), truthful
  skip handling, and `LOCAL_STATIC_READY_CI_REQUIRED` vs
  `AUTHORITATIVE_CI` mode distinction.
- Real container-backed lifecycle tests executed in CI.
- Pinned CI dependencies; failure evidence preserved (failure-context.json).

## Not changed

- A-003 architecture; local default; cloud deferred; no purchase/provisioning/
  deployment; `main` untouched; A-002 PO/Hermes boundary; failed-run history
  preserved (no deletion, no rewrite).
