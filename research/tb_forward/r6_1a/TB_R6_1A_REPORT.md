# TB-R6.1A — STABLE LOCAL RUNTIME SEAL — Report

**Status: STABLE_DEPLOYED_WAITING_NATURAL_CANARY** (stable deployment PASS; natural canary WAITING — healthy)
**Base:** `61cecf7d2a44c7a9f33b0f1bd060f79a15cf613f`

## What changed

1. **Stable path.** The runtime moved out of `AppData\Local\Temp\tb-r6` to a
   durable Desktop git worktree of `tb-forward-engine`:
   `C:\Users\wifik\Desktop\larger-lab-tb-forward-engine` (following the
   user's existing Desktop worktree convention — `larger-lab-cerebus`,
   `tbx-d01-seal`). The temp worktree was removed; it is no longer
   authoritative.
2. **Task Scheduler repoint.** `TB-Runtime-Supervisor` now launches the
   supervisor from the stable path (AtLogOn, current user, limited, verified
   via task XML). Registered with explicit user approval.
3. **Controlled handoff.** Old runtime intentionally stopped and verified
   down → temp worktree removed → stable worktree created → task repointed →
   started from stable path → reconcile (flat/clean, 220-bar warm) → exactly
   one worker (a duplicate attempt was blocked by the singleton guard).
4. **Accounting seal.** Deployment generation converted ONCE (before any
   natural trade): **TB-R6-FWD-DEMO-001**, baseline equity $25,254.35,
   reset reason `STABLE_DEPLOYMENT_CUTOVER_BEFORE_FIRST_NATURAL_TRADE`.
   Daily boundary frozen to the **broker/server account day** (UTC+3; day
   rolls 00:00 server = 21:00 UTC), derived from the live calibrated offset.
   Dashboard now shows **TODAY TB PNL $ / TODAY TB RETURN % / TB SINCE DEPLOY
   $ / TB SINCE DEPLOY %**, TB-owned only (magic + `TB|` tag + ledger
   linkage); heartbeat schema v2 (`today_pnl_pct`) with auto-migration.

## Evidence

- Stable path: worker log shows startup from the stable worktree (reconcile,
  warm 220 bars, server-day NAV, deployment NAV).
- Task: XML verified — command/args point at the stable path, AtLogOn,
  StartWhenAvailable, restart policy, current-user principal, Ready.
- Singleton: one worker (15444); duplicate attempt logged
  `SINGLETON_BLOCKED: ... already held by live pid 15444`.
- Heartbeat: 105+ rows, monotonic, WAL; fresh 2–10 s; dashboard ONLINE.
- MT5 connected, account gate PASS, reconciliation before execution.
- PnL: today $0.00 (0.000%), deploy $0.00 (0.000%) — no trades yet.
- Daily-return accounting: 5 new unit tests (server-day boundary, midnight
  epoch 21:00 UTC, exclusion of pre-midnight/foreign deals, 1.0% return math).

## Nonregression (fresh from the stable worktree)

- Full-engine replay: PRIMARY **194/194**, CONTROL **405/405**, 0 mismatches
  (265,809 bars, max z diff 1e-12).
- Suites: R1.1 36/36 · R2 26/26 · R3 40/40 · P6 411/411 · P7 160/160 ·
  runtime audits **34/34**. Failure injection 8/8 + long-run from the sealed
  R6.1 artifacts (strategy path untouched).
- Strategy science: **unchanged**. R6.1A edits are confined to runtime
  accounting/monitoring (worker daily boundary, DB schema v2, dashboard).

## Live state

- Service running: YES (supervisor 13720, worker 15444) from the stable path
- Dashboard: http://127.0.0.1:8765 — ONLINE / FLAT / MT5 CONNECTED / gate PASS
- Natural canary: WAITING (0 signals) — event-driven; the engine may wait
  days. No forced trades.

## Caveats

- Actual OS reboot: **MANUAL_VALIDATION_PENDING** (not automated); all
  component behaviors (process termination, service restart, persistent
  state, desired-state, baseline) verified live.
- The fresh runtime DB at the stable path starts heartbeat history anew
  (documented one-time cutover; no trades existed to preserve).

## Next

**TB-R6.2-NATURAL-CANARY-EVIDENCE-SEAL** — evidence-only checkpoint when the
first natural z2.5 basket lifecycle completes; analyzes existing logs/ledger,
no strategy code changes. R6 becomes fully PASS then; R7 (10–20 baskets)
thereafter, awaiting human authorization.
