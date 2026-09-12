# OCE Book 2 — Control Plane Evidence Record

**Date:** 2026-08-30
**Branch:** `oce-program-build`
**Implementation SHA:** `1ad1bee4` (verified green; final R9 implementation — see commit table below)
**Implementation tree:** `554cbed0a7b09deb8c535535dec0b102efedfdbb`
**Starting SHA (this closure):** `55d332f5968899536f7982674fee3dfaea922716`
**Starting SHA (Book 2 original):** `ac0e239386aa100349f5dc904acdb52345659090`

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
| `747f41d9` | B2-R6: runnable local HTTP service (FastAPI) + minimal operator console + service-boundary read auth (gaps 7/8/9) + one-command local runtime (start-local.sh) + worker loop |
| `a6ac42cf` | B2-R6R2: fix latent bugs exposed by first real CI run of the HTTP integration tests (unbound `clock` in PG `cancel_job`/`quarantine_job` → HTTP 400; console path resolved one level too shallow → "console unavailable") + PG cancel/quarantine regression test |
| `c84766bd` | B2-R7: harden one-command local lifecycle — no predictable default password (ephemeral generated secret in `.runtime/`, 0700/0600, gitignored), runtime-owned PID files replace `pkill -f`, stale-PID safety, `oce_local` CLI (configure/doctor/start/migrate/wait-ready/smoke/restart/recover/stop/destroy), loopback-only ports, durable volume preserved on stop, `destroy --yes` explicit authorization, 19 lifecycle tests |
| `49b95ed0` | B2-R7R1: make `oce_b2_compose` self-sufficient (src on sys.path) — fixes "No module named 'oce_control'" in CI |
| `2a97affb` | B2-R8(+R8R1): fail-closed evidence orchestration — 23-step runner (`run_b2_validation.py`), mandatory test registry (`b2_registry.py`, single source of truth), independent gate parses JUnit XML directly (exact totals, every mandatory node id, categories, no duplicates), cleanup verified BEFORE the gate and blocks promotion, source clean before/after, manifest generated LAST, read-only final package verifier |
| `275ea9ec` | B2-R9: harden CI — shared runner invoked exactly once with preserved exit code, pinned action revisions, `if: always()` evidence upload (PASS/FAIL/BLOCKED), machine-readable `oce_run_id` job output, trusted commit passed to the gate, workflow-provenance marker (never mistaken for Book 1), 16 gate regression tests |
| `d4eb4660` | B2-R9R1: PID liveness on Windows (kill(0) is a no-op there) + /proc cmdline + SIGKILL guard + credential-only cloud check (runner noise like `AZURE_EXTENSION_DIR` no longer trips) |
| `f353531c` | B2-R9R2: treat zombie processes as dead in the PID wait loop (Linux) |
| `1ad1bee4` | B2-R9R3: fix registry node-id canonicalization to junit form (`module.Class::test`) — the final test-identity fix; verified green |
| (evidence-only, next) | B2-R10: archive authoritative durable control-plane evidence; record references only the final run |

## Final authoritative run (B2-R10)

- **CI run:** `33336667766` — conclusion **success** — https://github.com/dabiggestpoppa/larger-lab/actions/runs/33336667766
- **OCE_RUN_ID:** `2617ed5323ea`
- **Artifact:** `b2-control-plane-evidence-2617ed5323ea` (id `9739247626`)
- **Outer ZIP SHA-256:** `3c3685b293d103ad5d5bbb2effcee0dd15336ffe3990b7b518b68b64c6e19d65` (matches GitHub's artifact digest; size 26374)
- **Internal manifest:** 24 entries, every SHA-256 and size re-verified `ALL MATCH`
- **Independent gate:** PASS 90/90 checks; **final package verifier:** PASS 97/97 checks
- **Stage status:** `PASS` (gate_status PASS, exit 0)
- **Durable archive:** `C:/Users/wifik/Desktop/oce-b2-archive/2617ed5323ea/` (original ZIP preserved + expanded copy + `provenance.json` + `verification.json`)
- **Evidence commit:** see "Confirmation" below for the R10 evidence-only commit SHA

## Test totals

| Test class | Result |
|---|---|
| Unit tests | 96/96 PASS |
| Schema tests | 10/10 PASS |
| Control plane tests | 66/66 PASS |
| Lifecycle (B2-R7) | 19/19 PASS |
| Gate regressions (B2-R9) | 16/16 PASS |
| Container-backed (PG 10 + Redis 2 + Worker 13 + Scheduler 7 + HTTP API 6) | 38/38 PASS in CI (real compose stack) |
| Mandatory FAIL | 0 |
| Mandatory BLOCKED | 0 |
| Mandatory SKIPPED | 0 in CI (gate-enforced); truthful local skips without Docker |
| **CI total (run `33336667766`)** | **169/169 PASS, 0 skipped, 0 failed, 0 errors** (verified from junit.xml + gate) |

Per-category (final run): unit 79, postgres 10, redis 2, scheduler 7, worker 13, api 6, po-hermes-boundary 11, adversarial 6, local-lifecycle 19, validation-regression 16 — sum 169.

## Gate results

| Gate | Result |
|---|---|
| Local gate | PASS (131/131 executed locally; 38 truthful container skips without Docker; container suite verified in CI) |
| **CI gate (B2-R10 final)** | PASS — run `33336667766` on `1ad1bee4`, gate `independent-gate-b2.py` 90/90 + final verifier 97/97, 169 passed / 0 skipped / 0 failed, all categories executed, cleanup verified before promotion, manifest hashes match, source clean before and after |
| HTTP service (B2-R6) | PASS (FastAPI on loopback, health unauthenticated, all other endpoints require X-OCE-Grant/X-OCE-Actor, 401/403 semantics) |
| Operator console (B2-R6) | PASS (served at /console, / redirects, read grant drives dashboard data) |
| Read authorization (B2-R6) | PASS (inspect/list/system/audit denied without 'read' grant; submit grant does not unlock reads; denials recorded) |
| Local lifecycle (B2-R7) | PASS (deterministic CLI: configure/doctor/start/migrate/wait-ready/smoke/restart/recover/stop/destroy; PID-file ownership; loopback-only ports; no predictable default secret; durable volume preserved on stop; destroy requires `--yes`) |
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
| Validation regressions (B2-R9) | PASS (failing test, missing mandatory test, skipped container test, wrong commit, dirty source, missing cleanup evidence, `removed:false`, altered manifest, stage-log mutation, uploadable failure evidence — all make the gate FAIL) |

## Cloud posture

- `cloud_mutations: 0`
- `cloud_cost_state: ZERO`
- `cloud_activation_state: DEFERRED_BY_OPERATOR`
- `cloud_deployment_state: NOT_DEPLOYED`
- Recurring cloud cost: `$0`

## CI history (this closure, honest)

| Run | Commit | Result | What it proved |
|---|---|---|---|
| `33335958137` | `c84766bd` | FAIL | B2-R7 push: compose helper couldn't import `oce_control` in the runner heredoc ("No module named 'oce_control'") — fixed by R7R1 |
| `33336139320` | `275ea9ec` | FAIL | B2-R9 push with the new 23-step runner + registry: 167/169 passed (2 lifecycle CI-only failures: Windows-agnostic PID liveness + cloud-check false positive on `AZURE_EXTENSION_DIR`) |
| `33336422552` | `d4eb4660` | FAIL | R9R1: 168/169 — remaining lifecycle PID-confirmation failure on Linux zombies |
| `33336539326` | `f353531c` | FAIL | R9R2: 169/169 tests passed but the gate rejected — registry node-id canonicalization for class-based tests (`module::Class` vs junit `module.Class`) |
| `33336667766` | `1ad1bee4` | **PASS** | Final: 169/169, 0 skipped/failed/errors, gate 90/90, final verifier 97/97, manifest hashes match, cleanup verified, source clean before+after |

Earlier history (B2-R5/R6, superseded): `33323109626` FAIL, `33323293374` FAIL, `33323666233` PASS (121/121), `33324373405` FAIL, `33324771835` FAIL, `33325630728` PASS (134/134, `a6ac42cf`), `33325801430` PASS. The R10 record references only the final authoritative run `33336667766` as Book 2's pass evidence.

## Confirmation

- `main` untouched at `7e7ef722`
- Book 3 was not started
- No cloud resources purchased, provisioned, or deployed
- PostgreSQL is authoritative truth; Redis is transient transport only
- Local is the default and authoritative runtime
- All permission checks at the service boundary
- Book 2 CI is authoritative: `b2-control-plane-validation` on `oce-program-build`, zero skips enforced by the independent gate
- R10 evidence-only commit: `(see git log — B2-R10: archive authoritative durable control-plane evidence)`

## Book 2 ratification (B3 preamble)

- **Commit:** `(first Book 3 commit — see git log, message `B2: ratify durable control-plane checkpoint`)`
- **Decision:** `RATIFIED / GATED_COMPLETE`
- **Frozen contracts:**
  - PostgreSQL authority contract (pg_store `0001`–`0003`; PG authoritative, Redis transport-only)
  - Redis transport boundary (disposable, reconstructable from PG, never sole truth)
  - Migration history (`0001`–`0003`, numbered & reversible)
  - API contracts (FastAPI loopback-only, auth on all endpoints except health)
  - Authority and denial behavior (grants, denials, service-boundary checks)
  - Scheduler semantics (PG-persisted, advisory-lock duplicate prevention, restart recovery)
  - Local lifecycle (`oce_local` CLI, ephemeral secret, PID-file ownership, durable volume)
  - Evidence model (23-step runner, JUnit-parsing gate, manifest-`last`, read-only verifier)
  - PO/Hermes separation
  - Cloud-dormant posture (mutations 0, cost `$0`)
- **Nullification constraint:** Book 3 may extend Book 2 but may not silently weaken it.

## Result: `READY_FOR_OPERATOR_REVIEW`

Book 2 control plane is implemented, hardened, tested, durably archived, and now **RATIFIED**. Book 3 (Worker Fabric) begins from here. Cloud remains deferred.
