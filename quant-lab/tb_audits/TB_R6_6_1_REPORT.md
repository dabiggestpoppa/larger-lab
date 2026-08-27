# TB-R6.6.1 - Persistent Windows Forward Runtime Seal

## Executive Summary

The TB forward test was down for ~18 hours due to a single root cause:
the scheduled task used only a LogonTrigger, which does not re-fire
after user logoff. All 4 processes died when the Windows session terminated.

## What Was Fixed

### 1. Scheduled Task Configuration
- Before: LogonTrigger only, battery-restricted, no restart-on-failure
- After: BootTrigger + LogonTrigger, battery-unrestricted, RestartOnFailure(3, 1min)
- Installer updated: install_windows_runtime.ps1 now matches live config

### 2. Supervisor Restart Logic
- Added worker_proc.poll() to detect immediate worker exit
- Retains bounded backoff instead of spawning infinite workers

### 3. Watchdog Alarm
- CRITICAL_RUNTIME_STALE surfaced to dashboard + Telegram
- External health check script created for out-of-process monitoring

### 4. Signal Regression Fixture
- Aug 27 15:25 UTC signal preserved as deterministic test fixture
- Raw closes: GBPAUD=1.88835, GBPNZD=2.28268, AUDNZD=1.20817
- Expected z=-3.536982, PRIMARY and CONTROL both eligible

## Verification Results

| Test | Result |
|------|--------|
| Scheduled task parity | PASS |
| MT5 connectivity | PASS |
| Worker crash restart | PASS (17s) |
| Worker kill drill | PASS |
| 5-min soak | PASS |
| Signal regression | PASS |

## Remaining Risk

MT5 Python API requires user-session access. Logoff may kill processes.
Operator should reboot and log off to verify survival.

## Decision

PARTIAL_RUNTIME_REPAIR_NEEDS_OPERATOR_REBOOT_TEST
