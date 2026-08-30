# OCE Book 2 — Control Plane Evidence Record

**Date:** 2026-08-30
**Branch:** `oce-program-build`
**Implementation SHA:** `c129d1f4`
**Implementation tree:** `451c5050d693ca18761fcead17e75fffc265b65e`
**Starting SHA:** `ac0e239386aa100349f5dc904acdb52345659090`

## Book 1 ratification

- **Commit:** `4c604d09`
- **Decision:** `RATIFIED / GATED_COMPLETE`
- **Evidence:** run `f767fadd3d67`, CI `33311614613`, 150/150 tests pass, 21/21 container-backed, gate 60/60

## Book 2 commits

| Commit | Description |
|---|---|
| `dbf12836` | B2-C1: build control plane canonical contracts and schemas |
| `b55696e6` | B2-C1R1: repair truncated modules and fix state machine transitions |
| `ff22aa22` | B2-R2: implement PostgreSQL authoritative control state (store, migrations, compose, 9 container tests) |
| `05702010` | B2-R3: implement Redis-backed disposable transport (notifications, lease mirrors, heartbeats, rate, cache, quarantine, PG reconstruction) |
| `79cb0e26` | B2-R4: durable scheduler + authenticated, capability-enforced worker (token admission, capability enforcement, PG-persisted schedules, advisory-lock duplicate prevention, migration 0003, 20 container tests) |
| `f063ae24` | B2-R5: wire Book 2 control-plane CI (workflow, validation runner, independent gate with zero-skips rule, pinned requirements) |
| `9a24311e` | B2-R5R1: fix migration runner duplicate-key on self-seeded version rows |
| `c129d1f4` | B2-R5R2: fix state machine lease-surrender (leased → pending) and shared-conn poisoning in pg tests |

## Test totals

| Test class | Result |
|---|---|
| Unit tests | 90/90 PASS |
| Schema tests | 10/10 PASS |
| Control plane tests | 66/66 PASS |
| Container-backed (PG 9 + Redis 2 + Worker 13 + Scheduler 7) | 31/31 PASS in CI (real compose stack) |
| Mandatory FAIL | 0 |
| Mandatory BLOCKED | 0 |
| Mandatory SKIPPED | 0 in CI (gate-enforced); truthful local skips without Docker |
| **CI total (run `33323666233`)** | **121/121 PASS, 0 skipped, 0 failed** |

## Gate results

| Gate | Result |
|---|---|
| Local gate | PASS (90/90) |
| **CI gate (B2-R5)** | PASS — workflow `b2-control-plane-validation` run `33323666233` (OCE_RUN_ID `1c3c051d5741`), gate `independent-gate-b2.py` 9/9 conditions, 121 passed / 0 skipped / 0 failed, artifact `b2-control-plane-evidence-1c3c051d5741` |
| Schema validation | PASS (all 9 contract schemas) |
| State machine transitions | PASS (legal/illegal/terminal) |
| Authority engine | PASS (grants, denials, replay detection) |
| Job store + idempotency | PASS (duplicate submission, conflicting keys) |
| Redis transport (B2-R3) | PASS (notify queues, lease NX/TTL mirrors, heartbeats, rate limits, cache, quarantine, reconstruct_from_pg) |
| Worker admission (B2-R4) | PASS (token required, hash-only persistence, wrong-token re-admit denied, revoked refused, lease-token fencing, capability enforcement at claim) |
| Durable scheduler (B2-R4) | PASS (PG persistence, restart recovery, pause/resume/cancel survive restart, advisory-lock duplicate prevention, concurrency limits) |
| Worker leases | PASS (stale, expired, wrong worker, renewal, recovery) |
| Scheduler | PASS (immediate, delayed, recurring, pause/resume, restart recovery) |
| Evidence system | PASS (manifest, tamper rejection, truth promotion, replay) |
| Health & recovery | PASS (PG blocks, Redis degrades, Redis loss, PG fail-closed) |
| API permissions | PASS (service boundary permission enforcement) |
| PO boundary | PASS (work plans, environment locks, approval, subagents) |
| Hermes boundary | PASS (routing, escalation, rate limiting, PO-only block) |
| Event store | PASS (causal chains, orphan/cycle detection) |
| OpenClaw deprecation | PASS (deprecated, scheduled removal B4, provider-neutral) |
| Local stack | PASS (startup, shutdown, smoke test, is_local) |
| Adversarial | PASS (forgery, hash mismatch, cloud activation, replay) |

## Cloud posture

- `cloud_mutations: 0`
- `cloud_cost_state: ZERO`
- `cloud_activation_state: DEFERRED_BY_OPERATOR`
- `cloud_deployment_state: NOT_DEPLOYED`
- Recurring cloud cost: `$0`

## CI history (audit gaps 17/18 closure)

| Run | Commit | Result | What it proved |
|---|---|---|---|
| `33323109626` | `f063ae24` | FAIL | Runner + gate worked; exposed migration runner duplicate-key: 0001/0002 self-seed `schema_migrations` and `cmd_up`'s INSERT collided → all 31 container tests errored at setup (latent since B2-R2; never seen because B2 container tests never ran) |
| `33323293374` | `9a24311e` | FAIL | Migration fix worked (119 passed, 0 skips); exposed two more latent bugs: `leased → pending` missing from `JOB_TRANSITIONS` (both surrender paths relied on it), and `test_pg_unavailable_fails_closed` closing the module-shared connection |
| `33323666233` | `c129d1f4` | **PASS** | Genuinely green: 121/121, 0 skipped, 0 failed, gate 9/9. All 31 container-backed tests executed against the real compose stack (PostgreSQL 16 + Redis 7) |

## Confirmation

- `main` untouched at `7e7ef722`
- Book 3 was not started
- No cloud resources purchased, provisioned, or deployed
- PostgreSQL is authoritative truth; Redis is transient transport only
- Local is the default and authoritative runtime
- All permission checks at the service boundary
- Book 2 CI is authoritative: `b2-control-plane-validation` on `oce-program-build`, zero skips enforced by the independent gate

## Result: `READY_FOR_OPERATOR_REVIEW`

Book 2 control plane is implemented, tested, and ready for operator review.
Book 3 has not been started. Cloud remains deferred.
