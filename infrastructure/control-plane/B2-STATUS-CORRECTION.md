# OCE Book 2 — Status Correction (B2-R1)

**Date:** 2026-08-30
**Stage:** `AUTHORIZED_STAGE=OCE-BOOK-2-DURABLE-CONTROL-PLANE-CLOSURE`
**Previous status:** `READY_FOR_OPERATOR_REVIEW` (premature — recorded in commit `7177f528`)
**Corrected status:** **`BLOCKED_DURABLE_RUNTIME`**

## 1. Why the earlier status was premature

Commit `7177f528` ("B2: archive authoritative control-plane evidence") reported
`READY_FOR_OPERATOR_REVIEW` on the strength of 76/76 passing unit tests. Those
tests validate the **in-memory model only**. They prove nothing about the
durable runtime the mission requires. The audit found the following gaps:

| # | Gap | Truth |
|---|-----|-------|
| 1 | `JobStore` entirely in memory | No durable state whatsoever |
| 2 | `job_store.py` references `pg_store.py` | File does not exist |
| 3 | PostgreSQL migration package | Absent |
| 4 | Redis availability simulated via boolean flags | No real Redis code path |
| 5 | Redis transport/lease/queue/cache/reconstruction | Absent |
| 6 | Local Docker/Podman Compose control-plane stack | Absent |
| 7 | `ControlPlaneAPI` is a Python façade | Not a runnable HTTP service |
| 8 | Book 2 UI / operator console | Absent |
| 9 | Read endpoints without service-boundary authorization | Permission gaps |
| 10 | Worker admission without authentication | Any worker id accepted |
| 11 | Worker claim without capability enforcement | Any worker can claim any job |
| 12 | Idempotency-key reuse with different payload | Not rejected |
| 13 | Job payloads not validated against job-type schemas | Admission gap |
| 14 | PG/Redis recovery tests use simulated state | Not service-failure proof |
| 15 | Scheduler restart recovery not proven on persistent state | Only in-memory |
| 16 | Evidence record claims authoritative gate | No authoritative runner existed |
| 17 | GitHub Actions runs only Book 1 workflow | No Book 2 CI |
| 18 | CI run `33316972933` succeeded | Did not execute Book 2 tests |
| 19 | No Book 2 run ID / artifact / manifest / hash reconciliation / independent gate | Absent |
| 20 | Staged Book 2 history incomplete | One broad chapter + one repair only |

## 2. What the 76/76 result actually proves

Preserved as: **"in-memory model validation"** (`UNIT_TEST_PASS` mode). Valid
evidence that the domain logic (authority, state machines, idempotency rules,
scheduler math, evidence hashing, boundaries) is sound. Explicitly **not**
evidence of a durable runtime.

## 3. Frozen runtime contract

`contracts/runtime-contract.json` (v2.1) freezes the storage, transport, API,
worker, scheduler, authority, evidence and local-deployment interfaces, and
defines the two execution modes:

- `in-memory` — non-authoritative, may report only `UNIT_TEST_PASS`;
- `durable` — PostgreSQL authoritative + Redis transport; the only mode that
  may report production readiness.

## 4. Repair plan

Waves B2-R2..B2-R10 close the gaps above in order: PostgreSQL store → Redis
transport → durable scheduler/worker → local API + console → PO/Hermes
boundaries → one-command local stack → authoritative validation → CI →
evidence archive. `main` untouched; Book 3 not started.
