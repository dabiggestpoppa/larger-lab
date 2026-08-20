# CTBT T4 — FORWARD RUNTIME CHECKOUT RECOVERY

Date: 2026-08-20
Status: PASS_FORWARD_RUNTIME_RESTORED

## Problem

The main checkout `C:/Users/wifik/Desktop/larger-lab` was switched to branch
`main` (then `oce/block-1-i1-cloud-ground`) by another actor. That removed the
tracked CTBT runtime files from the active filesystem used by the
already-running forward-shadow collector. The collector process survived in
memory (Python keeps loaded modules), but every tick it failed to re-read
`CTBT_T4_ACTIVATION_SEAL.json` and logged:

```
tick error (non-fatal): [Errno 2] No such file or directory:
  .../t4_runtime_shadow/CTBT_T4_ACTIVATION_SEAL.json
```

## Root cause

- The forward collector and dashboard resolve all runtime paths from
  `Path(__file__)` (see `ctbt_runtime/config.py`), so they were bound to the
  main checkout's filesystem.
- The main checkout is shared / freely switched by other agents, so its
  working tree is NOT a stable runtime root.
- The `state/` directory (gitignored) survived the branch switches — that is
  why processed-bar persistence, ledgers, and operator status were intact.

## Recovery actions

1. **Recorded pre-recovery state:**
   - Collector PID: 10420 (pid file was stale at 21940)
   - Last processed bars: EUR_GBP_USD / GBP_NZD_USD = 2026-08-20T14:55:02
   - Last heartbeat: 2026-08-20T14:57:33Z
   - Forward events: 0 / 0 (none yet — 0 duplicates possible)
2. **Created a dedicated runtime worktree:**
   `C:/Users/wifik/Desktop/larger-lab-ctbt-forward`
   pinned to branch `agent/shallow-well-foundry-ctbt-t1`
   at `f3c6aca28ae9bdc090ca32032f180995cf94a9b5` (SW-CTBT-T4.1).
3. **Migrated live state** (processed-bar files) from the old runtime root
   into the new worktree's `state/` — restart resumes from the last processed
   bar, so no duplicate signals and no clock reset.
4. **Controlled restart:** stopped only the CTBT collector (10420) and the
   transfer dashboard (4404); restarted both from the dedicated worktree.
5. **Added a checkout-drift guard** to `run_shadow_loop.py`:
   - Startup self-check verifies required runtime files exist;
   - Refuses to run from a drifted checkout instead of silently degrading;
   - Records `runtime_root`, `runtime_git_head`, `runtime_self_check_ok` in
     `CTBT_T4_OPERATOR_STATUS.json` every tick.
6. **Linked data read-only** (`quant-lab/data` junction) so the parity tests
   can run inside the worktree (16/16 pass).

## Verified health (19/19 checks)

1. `CTBT_T4_ACTIVATION_SEAL.json` exists and is readable ✓
2. activation timestamp exactly `2026-08-20T12:59:33.677636Z` ✓
3. first eligible M5 bar exactly `2026-08-20T13:05:00Z` ✓
4. EUR_GBP_USD hash `aad0a8e6...44b1a7` ✓
5. GBP_NZD_USD hash `5538d63a...4f62485` ✓
6. provider reconnected (OxSecurities-Demo, login 1114712) ✓
7. completed M5 bars advancing (14:55:02 → 15:00:00 → …) ✓
8. heartbeat updating normally ✓
9. `CTBT_T4_ACTIVATION_SEAL.json not found` error gone ✓
10. processed-bar persistence resumed ✓
11. forward ledgers append-only ✓
12. no duplicate forward events during restore (0 events, no dupes) ✓
13. canonical dashboard 8765 available ✓
14. transfer dashboard 8766 available ✓
15. dashboard data freshness resumes ✓
16. order-prevention PASS ✓
17. demo execution false ✓
18. capital routing false ✓
19. production false ✓

## Operational rule (now enforced)

THE ACTIVE FORWARD COLLECTOR MUST RUN FROM A DEDICATED RUNTIME WORKTREE:

```
C:/Users/wifik/Desktop/larger-lab-ctbt-forward
  (branch agent/shallow-well-foundry-ctbt-t1)
```

Do NOT use the freely-switched main development checkout as its permanent
runtime root. The collector now self-checks at startup and refuses to run if
required runtime files disappear or the checkout drifts.

## Operator commands

Start collector (from the runtime worktree):

```
cd C:/Users/wifik/Desktop/larger-lab-ctbt-forward/research/shallow_well/canonical_tb_transfer/t4_runtime_shadow
nohup python -u -m ctbt_runtime.run_shadow_loop --start > state/ctbt_shadow_console.log 2> state/ctbt_shadow_err.log < /dev/null &
```

Start dashboard:

```
nohup python -u ctbt_dashboard.py --port 8766 > state/ctbt_dashboard.log 2>&1 < /dev/null &
```

Stop collector:

```
python -m ctbt_runtime.run_shadow_loop --stop
```

## Post-recovery state

- Collector PID: 22352 (guarded build), resuming from 15:00:00
- Runtime root: `C:\Users\wifik\Desktop\larger-lab-ctbt-forward\...\t4_runtime_shadow`
- Runtime git head: f3c6aca28ae9bdc090ca32032f180995cf94a9b5
- Tests: 16/16 pass
- Forward evidence rules unchanged; events remain 0 (waiting for natural signals)
