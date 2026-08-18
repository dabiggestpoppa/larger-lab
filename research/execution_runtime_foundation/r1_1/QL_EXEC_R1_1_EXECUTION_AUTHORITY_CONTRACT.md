# QL-EXEC-R1.1 EXECUTION AUTHORITY CONTRACT

## Function
`derive_execution_authority(profile, observed_state, runtime_state, compatibility_state) -> ExecutionAuthorityDecision`

DEFAULT DENY. A config profile can never declare itself READY.

## Gates (new-risk)
1. `operator_execution_requested == true`
2. account role is a direct-execution role
   (`EXCLUSIVE_STRATEGY_MASTER` or `PORTFOLIO_MASTER`)
3. authentication satisfied (centralized `authentication_satisfied`)
4. transport connected
5. identity matched (centralized `identity_gate`)
6. runtime `RUNNING` (not intentionally stopped)
7. not safety-blocked
8. reconciliation clean
9. hedging/netting compatibility passes

All must pass. Any failure denies and records the exact blocking gate in
`reasons`.

## Manage / close existing risk
`can_manage_owned_existing_risk` and `can_close_owned_risk` do NOT require
operator new-risk permission, reconciliation, or compatibility. They DO
require: transport connected, authentication satisfied, identity matched,
runtime RUNNING, not safety-blocked.

Frozen policy: identity / account truth stays strong enough to prevent
closing a position on the wrong account.

## Foreign risk
`can_modify_foreign_risk` is ALWAYS `False`.

## Follower / Mirror
`FOLLOWER` and `MIRROR` never receive `can_submit_new_risk`, regardless of
authentication mode.

## Negative injections (all must deny new risk)
- `operator_execution_requested=false`
- `identity_matched=false`
- `reconciled=false`
- runtime `STOPPED_BY_USER`
- `safety_block=true`
- role `FOLLOWER`
- role `MIRROR`
- unknown shared account mode
- `EXTERNAL_SESSION` with `authenticated=false`
- `RUNTIME_CREDENTIALS` with missing secret
- `RUNTIME_CREDENTIALS` with secret present but `authenticated=false`

Each decision's `reasons` must name the exact blocking gate.
