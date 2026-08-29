# OCE Local Ground — State Ledger (B1-LOCAL, A-003)

**Updated:** 2026-08-29
**Branch:** `oce-program-build`
**Decision:** `LOCAL_FIRST_CLOUD_ACTIVATION_DEFERRED`
**Amendment:** OCE-AMEND-A003

## Independent ledger fields

| Field | Value (2026-08-29, RUN `52f60c556f50`) |
|---|---|
| `local_ground_state` | LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW |
| `cloud_plan_state` | VALIDATED_NO_APPLY |
| `cloud_activation_state` | DEFERRED_BY_OPERATOR |
| `cloud_deployment_state` | NOT_DEPLOYED |
| `cloud_cost_state` | ZERO |
| `next_local_book` | B2 |
| `operator_hold_reason` | CLOUD_PURCHASE_DEFERRED |

## Machine-readable copy

The same fields are enforced by `contracts/local-ground-contract.json`
(`ledger_model`) and written live by `scripts/oce-ctl local status` into
`var/state.json`.

## Change record

- 2026-08-29 — A-003 ratified; Local Ground split from Cloud Activation; cloud
  purchase hold preserved as historical truth; zero cloud cost, zero cloud
  mutations.
- 2026-08-29 — Local Ground validation passed (37 tests, 5/5 adversarial,
  cloud apply denied, independent gate LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW,
  RUN `52f60c556f50`); ledger fields updated to READY_FOR_OPERATOR_REVIEW /
  VALIDATED_NO_APPLY. Cloud fields remain DEFERRED_BY_OPERATOR / NOT_DEPLOYED /
  ZERO. Pending operator ratification before B2 begins.
