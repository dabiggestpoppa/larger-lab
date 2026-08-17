# TB-R6.1 — PERSISTENT DEMO RUNTIME + NATURAL CANARY — Report

**Status: DEPLOYED_WAITING_NATURAL_CANARY** (runtime deployment PASS; natural canary WAITING — healthy expected state)
**Base:** `68112be136c80eab9b992a339132c4162528a6d7` (R6)

## What was built

A persistent local Windows demo runtime under `quant-lab/runtime/`:

| Component | File | Role |
|---|---|---|
| Supervisor | `tb_supervisor.py` | worker process lifecycle only; bounded backoff (5/15/30/60 s); honors durable desired state |
| Worker | `tb_worker.py` | MT5 / data / strategy / execution / persistence; heartbeat every 10 s; NAV baselines; owned-only PnL |
| Dashboard | `tb_dashboard.py` | read-only `http://127.0.0.1:8765` (localhost only) |
| CLI | `tbctl.py` | `status / start / stop / restart` |
| Auto-start | `install_windows_runtime.ps1` / `uninstall_windows_runtime.ps1` | Task Scheduler logon task (current user, limited) |
| Durable state | `tb_runtime_db.py` + `tb_runtime.db` (SQLite/WAL) | heartbeat, status, daily/deployment NAV, errors |

## Evidence

- **Auto-start:** Task `TB-Runtime-Supervisor` registered (Ready, Interactive/logon, current user) with explicit user approval; supervisor honors `tbctl stop` (STOPPED_BY_USER) so an intentional stop survives reboot.
- **Supervisor:** spawned worker; **auto-restart observed live** (taskkill on worker → respawned ~25 s later with bounded backoff).
- **Worker startup contract:** ledger integrity → reconstruct → broker read → reconcile → warm 159 synchronized historical M5 bars from the real terminal → safe resume; BLOCKED_RECONCILIATION on ambiguity (fail closed).
- **Heartbeat:** 58+ durable rows, monotonic ids, WAL; status derivation GREEN ≤30 s / YELLOW 30–90 s / RED >90 s.
- **Singleton:** second worker blocked live (`SINGLETON_BLOCKED: ... already held by live pid`); stale-pid reclaim verified.
- **Intentional stop:** stop → both processes down, stays stopped, status STOPPED; restart re-enables.
- **MT5 disconnect:** WAITING_FOR_MT5 with 30 s bounded retry (unit-verified); reconnect re-reconciles first.
- **Market closure:** ONLINE_MARKET_CLOSED, no orders, auto-resume (unit-verified + R5.1 live weekend evidence).
- **Dashboard:** HTTP 200 JSON verified; all required fields present; read-only.
- **PnL accounting:** owned-only (TB magic + `TB|` tag); foreign magic and same-magic-no-tag excluded; daily = realized today + open; deployment baseline persists across restarts.
- **Log rotation:** 5 MB × 5 verified bounded.
- **Disk guard:** DEGRADED_DISK fail-closed verified.
- **Nonregression:** R1.1 36/36 · R2 26/26 · R3 40/40 · P6 411/411 · P7 160/160 · runtime audits 29/29 · full-engine replay PRIMARY **194/194** CONTROL **405/405** mismatches **0** · failure injection 8/8 safe · long-run clean. Strategy science unchanged (runtime is entirely new files; zero edits to sealed strategy/persistence code).

## Natural canary

- Signals observed: **0** (control ledger empty; ~1h observation, z > 2.5 events are ~0.4/day).
- `natural_canary_pass = false` → overall status **DEPLOYED_WAITING_NATURAL_CANARY** (not FAIL).
- The runtime stays online; the canary fires when the market provides a signal. No forced trades, no threshold changes.

## Live state at commit

- Service installed: **YES** (task) · Service running: **YES** (supervisor pid 24936, worker pid 18412)
- Dashboard: http://127.0.0.1:8765 — ONLINE / FLAT / MT5 CONNECTED / gate PASS
- Today TB PnL $0.00 · Since deploy $0.00 · Open basket none
- Deployment baseline: GEN-SMOKE, equity $25,254.35 (frozen; survives restarts)

## Caveats

- The logon task points at the current live deployment path (`AppData\Local\Temp\tb-r6`); when the branch is relocated to a stable path, re-run `install_windows_runtime.ps1` (one command) to repoint.
- Actual OS reboot not automated (MANUAL_VALIDATION); process-death/service-restart/persistence all verified live.
- PnL is $0 because no canary trade has occurred — that is the expected state, not a defect.

## Next

**TB-R7-CANARY-DEMO-OPERATIONS-SEAL** once the first natural canary basket completes (target 10–20). Not auto-started.
