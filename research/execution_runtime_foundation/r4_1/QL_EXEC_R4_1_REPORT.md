# QL-EXEC-R4.1 — Report

Checkpoint: QL-EXEC-R4.1-TB-GENERIC-RUNTIME-SHADOW-DEPLOYMENT-PLAN
Status: PASS (plan only)
Base: 750a14bf20bf0869f452d8df20138e58bbb091e5

## What this checkpoint produced

A complete, frozen, safe deployment plan for running the generic TB runtime
side-by-side with the active TB stack in SHADOW ONLY mode — with zero broker
order authority enforced by four independent barriers.

## Key decisions

1. **Shadow mode is first-class** (`SHADOW_OBSERVE_ONLY`), enforced below
   strategy level by runtime authority gate + read-only broker + immutable
   profile + (optional) process capability denial.

2. **Market-data path = Option B** (`LEGACY_EXPORT_READ_ONLY_SNAPSHOT`),
   because concurrent MT5 read safety is UNRESOLVED. The shadow consumes
   read-only exported snapshots, avoiding a second MT5 attach entirely.

3. **No automatic failover / promotion.** If the shadow dies, legacy TB is
   unaffected; if legacy TB dies, the shadow never assumes authority.

4. **Tolerances and evidence-stop rule frozen pre-observation.** 1000
   synchronized bars + 5 trading days + restart/market-close drills; exact
   equality for deterministic quantities, tight epsilons for floating point.

## Authority freeze

- tb-forward-engine: b48fd35255b41865026a3cba333ae2a2a0d6a004 (unchanged)
- capital-routing: 73f760ce09e7109b23732fb7ff2ec8ad455a563e (moved from
  f52d5f48; irrelevant to R4.1 — no CR science used)
- main: dfdca6acd829cda4c084cd3bd217ab606348b660 (unchanged)

## Non-interference

No source file was modified, no test was run, no broker was contacted, no
order was attempted, and no active TB state path was written.

## Pass gate

All 12 R4.1 pass-gate criteria are satisfied by construction of the plan.

## Next

QL-EXEC-R4.2-TB-GENERIC-RUNTIME-LIVE-SHADOW-CANARY (r4_2_authorized = false
until human review).
