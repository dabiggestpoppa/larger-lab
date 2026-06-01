---
title: Executor Crash + Monitor Fix — 2026-05-31 05:30 EDT
tags: [incident, executors, monitor, fix, live-trading]
---

# Executor Crash + Monitor Bug Fix

## What Happened
- **05:13 EDT** — Both ST and P90 CASCADE executors errored out ( Cycle 387 / Cycle 2510 )
- **05:16 EDT** — 5AM Overnight Report correctly flagged both as dead
- **No positions at risk** — both flat, no pending orders, balance $87.79

## Root Cause Analysis
1. **Executor crash**: Likely a transient MT5 connection issue at ~5:13 AM. Both exited with "error" status.
2. **Monitor false-negative bug** (pre-existing): `check_process_alive()` used `tasklist` which only shows "python.exe" — NOT the command line. So it **always** reported executors as dead even when running. Monitor was effectively blind.

## Actions Taken
1. **Restarted both executors** — ST (PID cleaned to single instance) + P90 CASCADE (single instance)
2. **Killed duplicate processes** — previous restart attempts left 5 ST and 2 P90 duplicates
3. **Fixed monitor bug** — `check_process_alive()` now uses PowerShell `Get-CimInstance Win32_Process` with CommandLine property
4. **Verified fix** — Monitor now shows both executors ✅ RUNNING, 0 alerts

## Key Metrics Post-Restart
- ST: Cycling normally, `no_signal` (expected — 5AM is outside main entry window sweet spot)
- P90: Cycling normally, `no_signal`
- Account: $87.79 balance, flat, no open positions

## Lessons Learned
- Monitor was producing false "executor dead" alerts — the `tasklist` approach can't see script names
- Need to kill old executor processes before restarting (don't just spawn new ones)
- Executor crash at 5:13 AM may be related to MT5 server maintenance window or daily reset
