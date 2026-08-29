# OCE Local Ground — State Ledger (B1-LOCAL, A-003)

**Updated:** 2026-08-29
**Branch:** `oce-program-build`
**Decision:** `LOCAL_FIRST_CLOUD_ACTIVATION_DEFERRED`
**Amendment:** OCE-AMEND-A003

## Independent ledger fields

> **CORRECTED 2026-08-29 (repair cycle):** the previous readiness claim was
> premature (Docker absent locally; authoritative CI failed). See
> `B1-LOCAL-READINESS-CORRECTION.md`. Active state below until a successful
> authoritative CI run.

| Field | Value (repair cycle, pre-authoritative-CI) |
|---|---|
| `local_ground_state` | VERIFYING |
| `cloud_plan_state` | NOT_VALIDATED |
| `cloud_activation_state` | DEFERRED_BY_OPERATOR |
| `cloud_deployment_state` | NOT_DEPLOYED |
| `cloud_cost_state` | ZERO |
| `next_local_book` | BLOCKED_PENDING_B1_REPAIR |
| `operator_hold_reason` | AUTHORITATIVE_CI_FAILED |

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
  is VERIFYING / NOT_VALIDATED / BLOCKED_PENDING_B1_REPAIR /
  AUTHORITATIVE_CI_FAILED. Cloud fields remain DEFERRED_BY_OPERATOR /
  NOT_DEPLOYED / ZERO.
