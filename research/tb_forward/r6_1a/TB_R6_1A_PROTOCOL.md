# TB-R6.1A — STABLE LOCAL RUNTIME SEAL

**Base:** `61cecf7d2a44c7a9f33b0f1bd060f79a15cf613f` (R6.1)
**Scope:** final operational hardening only — NO strategy, NO execution-model,
NO alpha changes. Replace the temporary deployment path with a stable
persistent installation and seal monitoring/accounting.

## Why this checkpoint

The R6.1 Task Scheduler entry pointed at a runtime under
`AppData\Local\Temp\tb-r6` — a temporary location, unacceptable as the
long-lived authoritative deployment path.

## Stable path

Following the user's established Desktop worktree convention
(`larger-lab-cerebus`, `tbx-d01-seal`), the runtime now lives at:

    C:\Users\wifik\Desktop\larger-lab-tb-forward-engine

a durable git worktree of branch `tb-forward-engine` @ 61cecf7d, owned by the
user's permanent larger-lab repository. The temp worktree was removed; the
temp path is no longer authoritative.

## Controlled handoff (never two executable workers)

1. intentional stop of the temp runtime (`tbctl stop`) — verified both
   processes down
2. temp worktree removed (branch freed)
3. stable worktree created at the Desktop path
4. Task Scheduler task repointed to the stable supervisor
   (explicit user approval for the exact schtasks command)
5. started from the stable path; ledger/broker reconciliation ran before
   execution was enabled
6. singleton verified (one worker); heartbeat + dashboard verified

## Accounting seal

- Deployment generation converted ONCE, before any natural trade:
  `GEN-*` → **TB-R6-FWD-DEMO-001**; baseline reset reason recorded:
  `STABLE_DEPLOYMENT_CUTOVER_BEFORE_FIRST_NATURAL_TRADE`. Never reset again
  on normal restart.
- Daily boundary frozen: **broker/server account day** (calibrated server
  clock; this broker UTC+3; 00:00 server = 21:00 UTC). Daily baseline
  persists across worker/dashboard/supervisor restarts.
- Dashboard now shows TODAY TB PNL $, TODAY TB RETURN %, TB SINCE DEPLOY $,
  TB SINCE DEPLOY % — all TB-owned only (magic + `TB|` tag + ledger linkage).

## Status logic

- STABLE_DEPLOYED_WAITING_NATURAL_CANARY: stable deployment passes, no
  natural trade yet — expected and healthy.
- R6.2 (evidence-only, later): analyze existing logs/ledger when the first
  natural z2.5 lifecycle completes; no strategy code changes.
- R7 after that: 10–20 completed natural control baskets.

## Post-seal behavior

- Natural canary continues; the engine may wait days — correct.
- MT5 disconnect → DEGRADED/WAITING_FOR_MT5, reconnect reconciles first.
- Weekend → ONLINE_MARKET_CLOSED, no orders, auto-resume.
- Worker crash → supervisor bounded backoff restart; no duplicate trade.
- `tbctl stop` → STOPPED_BY_USER persisted; no watchdog override.
