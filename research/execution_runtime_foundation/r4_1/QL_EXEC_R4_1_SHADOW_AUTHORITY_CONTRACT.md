# QL-EXEC-R4.1 — Shadow Authority Contract

## Authority model

- **PRIMARY OPERATIONAL AUTHORITY** = active TB stack (unchanged, R6.1D
  authority at b48fd35255b41865026a3cba333ae2a2a0d6a004).
- **GENERIC TB SHADOW** = observer only. Zero broker order authority.
- Legacy control path keeps its existing executable canary behaviour.
- Generic PRIMARY and CONTROL paths are both shadow-only.

## Immutable facts

1. `account_observed = true` does NOT imply `order_authority = true`.
2. `desired_state = RUNNING` on the shadow does NOT imply new-risk authority;
   it only permits observation + hypothetical intent construction.
3. `can_submit_new_risk = false` is pinned by the shadow profile and cannot be
   flipped by any single configuration value (defense in depth).

## No automatic failover / promotion

- If the generic shadow dies: legacy TB is completely unaffected.
- If legacy TB dies: generic shadow MUST NOT assume authority.
- There is NO leader election, NO hot-standby order takeover, NO automatic
  promotion.

`automatic_failover_possible = false`
`automatic_promotion_possible = false`

These are enforced by (a) absent write APIs on the shadow broker, (b) the
shadow runtime execution gate pinned false, and (c) separate process/state
identity with no shared authority token.

## Primary shadow parity

Both legacy and generic paths classify PRIMARY (z3 / ±0.25) as shadow:
broker orders = 0 on both sides. Any generic primary broker order => R4.1
FAIL.

## Control shadow parity

Legacy control remains executable per current TB authority. Generic control
is shadow-only: same event time, direction, basis, z, weights, target lots,
entry/exit, stop/session exit — but zero submission.
