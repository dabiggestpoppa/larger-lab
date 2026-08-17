# TB-R6.1 — PERSISTENT DEMO RUNTIME + NATURAL CANARY

**Base:** `68112be136c80eab9b992a339132c4162528a6d7` (R6 demo execution canary)
**Profile:** `local_windows` (implemented); `windows_vps` template documented only.

## Mission

Convert the proven R6 demo engine into a persistent local Windows runtime that
stays online across the trading week with no daily manual startup, while
continuing the natural TB-FROZEN-CONTROL canary until at least one complete
natural basket lifecycle is observed. Add a simple read-only local dashboard.

## Architecture

```
Windows logon task (Task Scheduler, current user, limited)
        └─> tb_supervisor.py        process lifecycle ONLY (bounded backoff
            │                        restart; honors durable desired-state)
                └─> tb_worker.py     MT5 / data / strategy / execution /
                │                    persistence; heartbeat every 10 s
                └─> tb_dashboard.py  read-only http://127.0.0.1:8765
                └─> tbctl.py         status | start | stop | restart
```

- **Supervisor ≠ strategy.** The worker never supervises itself; the
  supervisor never trades.
- **Durable state:** `quant-lab/state/tb_runtime.db` (SQLite/WAL) —
  `runtime_status` (desired state, NAV baselines), `runtime_heartbeat`,
  `runtime_errors`, `daily_nav`, `deployment_nav`. PID files + desired-state
  flag for singleton and intentional-stop semantics.
- **Worker startup contract** (every start, incl. after crash/reboot):
  ledger integrity → state reconstruction → broker position read →
  reconciliation → warm frozen rolling window from real terminal history →
  safe resume. BLOCKED_RECONCILIATION / BLOCKED_LEDGER = no new orders.
- **Natural canary:** TB-FROZEN-CONTROL (z > 2.5, z0 exit) executes on the
  approved DEMO account only; TB-FWD-V1 stays SHADOW ONLY (order_send = 0).
- **Execution gates (frozen):** MAX_QUOTE_AGE_MS=2000,
  MAX_CROSS_LEG_SKEW_MS=1000, SPREAD_MAX_PTS=100, GATE_K residual ≤ 10%,
  basket notional $5,000. Identity gate (OxSecurities-Demo / DEMO / USD)
  must pass before any order.
- **PnL ownership:** only positions/deals with TB magic + `TB|` tag count;
  foreign/manual positions never touched.

## Two independent statuses

- `runtime_deployment_pass` — infrastructure evidence (auto-start, supervisor,
  heartbeat, dashboard, tbctl, auto-restart, intentional stop, reconciliation,
  singleton, disconnect/market-closure handling, PnL baselines, log rotation,
  disk guard, parity).
- `natural_canary_pass` — at least ONE genuine z2.5 signal → preflight →
  3/3 demo open → OPEN_VERIFIED → canonical exit → 3/3 close → flat.

Healthy expected outcome when no signal occurs: **DEPLOYED_WAITING_NATURAL_CANARY**
(runtime PASS, canary WAITING). No forced trades; the runtime may wait days.

## Status logic

- PASS: runtime deployment passes AND natural canary completes.
- DEPLOYED_WAITING_NATURAL_CANARY: runtime deployment passes; canary waiting.
- FAIL: unsafe supervision, duplicate worker, reconciliation failure,
  persistence failure, or strategy regression.

## Safety

- No real order_send from PRIMARY (0 calls). CONTROL executes demo only.
- Dashboard read-only; operational control via tbctl / OS task only.
- Localhost-only dashboard; no credentials stored in config; login masked.
