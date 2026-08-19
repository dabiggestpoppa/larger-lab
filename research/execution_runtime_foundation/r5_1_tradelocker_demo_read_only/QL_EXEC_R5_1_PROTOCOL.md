# QL-EXEC-R5.1 — TradeLocker DEMO Read-Only Integration

**Checkpoint:** `QL-EXEC-R5.1-TRADELOCKER-DEMO-READ-ONLY-INTEGRATION`
**Base:** `832ac0f43ab8cce8f3a09057740668fc25e07ce8` (R5 PASS)
**Status:** `WAITING_TRADELOCKER_DEMO_ACCESS` — implementation + offline read-only
proof complete; no demo credentials were provided, so no real connection was
attempted and **zero** network calls were made.

## Mission

Verify the R5 `TradeLockerBrokerSession` binds to a REAL TradeLocker DEMO API
and normalizes actual provider truth into the generic `BrokerSession` contract
**without any write authority**. This checkpoint is READ ONLY by construction.

## What was built (this checkpoint)

1. **`execution_runtime/tradelocker/readonly.py`** — the read-only barrier layer:
   - `ReadOnlyProviderWriteForbiddenError`
   - `ReadOnlyTransport` — denies every non-GET request except the two auth
     POSTs (`/auth/jwt/token`, `/auth/jwt/refresh`) **before it leaves the
     process**; counts every blocked attempt
   - `ReadOnlyTradeLockerBrokerSession` — `submit_order` / `close_position` /
     `cancel_order` raise (never fake success); reads delegate unchanged
   - `assert_demo_environment()` — refuses any base URL whose host is not
     exactly `demo.tradelocker.com` (substring spoofing rejected)
   - `DemoReadOnlyAudit` — the shared read-only audit pipeline (auth → account
     discovery → per-account config/instruments/quotes/positions/orders/
     history/clock → multi-account isolation → TB symbol availability →
     health). The SAME code runs offline (FakeTradeLocker) and against the
     real demo (UrllibTransport).
   - `render_artifacts()` — splits an audit into the live-derived artifact
     files.
2. **`runtime/tradelocker_demo_readonly.py`** — operator runner:
   - credentials from env only (`TRADELOCKER_EMAIL`, `TRADELOCKER_PASSWORD`,
     `TRADELOCKER_SERVER`, optional `TRADELOCKER_DEV_API_KEY`)
   - no credentials → `WAITING_TRADELOCKER_DEMO_ACCESS`, exit 0, no connection
   - demo gate → `BLOCKED_NON_DEMO_ENVIRONMENT`, exit 2
   - audit failure → `AUDIT_FAILED`, exit 2 (never fabricates success)
   - success → `PASS (HEALTHY_READ_ONLY)` and writes the live artifacts
3. **`execution_runtime/tests/test_execution_runtime_r5_1_demo_readonly.py`** —
   31 offline tests covering the full 32-item matrix (offline halves), all
   write barriers, the audit pipeline, secrets hygiene, and the waiting path.

## The four order-prevention barriers

| # | Barrier | Enforcement | Offline proof |
|---|---------|-------------|---------------|
| 1 | Runtime authority gate | `can_submit_new_risk = False` on every audit run | `test_r5_1_audit_write_counters_zero` |
| 2 | Session barrier | `ReadOnlyTradeLockerBrokerSession` raises on submit/close/cancel | `test_r5_1_session_write_methods_blocked` |
| 3 | Transport barrier | `ReadOnlyTransport` denies all non-GET except auth POSTs | transport deny tests (orders POST/DELETE, positions DELETE) |
| 4 | Capability profile + env gate | `can_submit_new_risk=false`; non-demo URL refused pre-connection | `test_r5_1_demo_environment_gate_refuses_non_demo` |

Any single barrier failing independently cannot expose order authority. All
four are independently testable and all four hold (`broker_write_calls = 0`,
`transport_write_attempts = 0`).

## Evidence

- Full offline gate: **490/490** tests pass (459 R5 baseline + 31 new).
- Offline read-only audit over FakeTradeLocker: `HEALTHY_READ_ONLY`, 2
  accounts discovered (accountId 101/102, accNum 1000001/1000002 retained
  separately), config hash deterministic, 7 instruments with INFO+TRADE routes,
  quotes with provider server timestamps, pending order + filled execution with
  distinct orderId/positionId, foreign position normalized un-owned, TB trio
  `ALL_3_AVAILABLE`, write counters all zero.
- Artifacts: `r5_1_tradelocker_demo_read_only/` (23 files).

## Status honesty

No real TradeLocker demo account was reachable: no credentials exist in this
environment (and none are committed). The runner is ready: with
`TRADELOCKER_EMAIL`/`TRADELOCKER_PASSWORD`/`TRADELOCKER_SERVER` set it will
execute the identical, offline-proven audit against the real demo and emit the
live artifacts. Until then the status is `WAITING_TRADELOCKER_DEMO_ACCESS`,
NOT PASS, and `r5_2_authorized = false`.

## Constraints honored

- No orders, no modifications, no closes, no positions created.
- No MT5/TB/R4.2 shadow changes; Task Scheduler untouched; no dashboard/
  watcher/supervisor changes.
- No credentials in repo, DB, or logs; auth headers never logged.
- No "tiny test order" — read-only API truth is sufficient for R5.1.
