# 🐛 Debugging Guide — Larger-Lab

> **Last Updated:** 2026-05-20
> **Philosophy:** Repair before expansion. Read logs before guessing.

---

## Table of Contents

1. [Debug Philosophy](#1-debug-philosophy)
2. [Common Error Patterns](#2-common-error-patterns)
3. [Debug Tools](#3-debug-tools)
4. [Log File Locations](#4-log-file-locations)
5. [Diagnostic Commands](#5-diagnostic-commands)
6. [Error Database](#6-error-database)
7. [Stale Process Cleanup](#7-stale-process-cleanup)

---

## 1. Debug Philosophy

### The 6 Diagnostic Soft Logic Rules

1. **Starting something new** → Read startup logs. Verify every layer.
2. **Something stuck** → Read error log from LAST action. Not health check.
3. **Config changes** → One change at a time. Test. Next change.
4. **Stuck >30 min** → Stop guessing. Read the log file.
5. **Service won't start** → Check config schema validation errors FIRST.
6. **Behavior ≠ config** → Check for override files.

### Core Principles

- **Repair before expansion** — Never optimize throughput before stabilization
- **Read logs before guessing** — The answer is almost always in the last log entry
- **One fix at a time** — Never apply multiple fixes simultaneously
- **Fail loud** — If you can't be sure something worked, say so explicitly

---

## 2. Common Error Patterns

### ERR-V3-0001: Variable Name Reference

| Field | Value |
|-------|-------|
| **Symptom** | `NameError: name 'signals' not defined` |
| **Cause** | Used `signals` instead of `field.signals` in `_calc_field_pressure` |
| **Fix** | Changed `len(signals)` to `len(field.signals)` |
| **Prevention** | Run tests after every module creation |

### ERR-WIN-0001: Stale Terminals

| Field | Value |
|-------|-------|
| **Symptom** | Multiple old python/node processes running for hours |
| **Cause** | Agents spawn terminals for tests/servers but don't kill them |
| **Fix** | Run `python tools/terminal_cleanup.py --force` at session start |
| **Prevention** | Kill terminals after EVERY task completion |

### ERR-WIN-0002: Windows CMD Restrictions

| Field | Value |
|-------|-------|
| **Symptom** | File operations fail, encoding errors |
| **Cause** | Using `cmd.exe` or `subprocess.run(..., shell=True)` |
| **Fix** | Use PowerShell: `subprocess.run(['powershell', '-NoProfile', '-Command', '...'])` |
| **Prevention** | Always use PowerShell first for Windows operations |

### Floating Point Precision

| Field | Value |
|-------|-------|
| **Symptom** | `AssertionError: 0.30000000000000004 != 0.3` |
| **Cause** | Direct float comparison |
| **Fix** | Use `pytest.approx()`: `assert result == pytest.approx(0.3, abs=1e-6)` |

### API Version Mismatch

| Field | Value |
|-------|-------|
| **Symptom** | `TypeError: got an unexpected keyword argument` |
| **Cause** | API signature changed between versions |
| **Fix** | Check actual signature: `import inspect; print(inspect.signature(cls.method))` |

### Import Errors

| Field | Value |
|-------|-------|
| **Symptom** | `ModuleNotFoundError: No module named 'X'` |
| **Cause** | Missing dependency or wrong Python environment |
| **Fix** | `uv pip install X` or check `.venv` activation |

---

## 3. Debug Tools

### OC2 Doctor (6-Layer Diagnostic)

The OC2 Doctor performs a 6-layer system diagnostic:

```powershell
openclaw doctor --fix
```

| Layer | What It Checks |
|-------|---------------|
| Layer 1 | Gateway process status |
| Layer 2 | Configuration validity |
| Layer 3 | Workspace integrity |
| Layer 4 | Agent connectivity |
| Layer 5 | Memory sync status |
| Layer 6 | External service health |

### Terminal Cleanup

```powershell
# Show what would be killed (dry run)
python tools/terminal_cleanup.py

# Kill stale processes
python tools/terminal_cleanup.py --force

# Kill ALL python/node processes (careful!)
python tools/terminal_cleanup.py --all
```

### Progress Sync

```powershell
# Check sync status
python tools/progress-sync.py --status

# Force sync
python tools/progress-sync.py --force

# Sync specific agent
python tools/progress-sync.py --agent CC
```

### Self Heal

```powershell
# Scan logs for errors and auto-fix
python tools/self_heal.py
```

### Observer Debug

```powershell
# List all observers
python tools/operator/observer-debug.py list

# Check observer health
python tools/operator/observer-debug.py health

# View observer events
python tools/operator/observer-debug.py events
```

### Error Analyzer

```powershell
# Analyze error patterns
python tools/analyze_errors.py
```

---

## 4. Log File Locations

| Log File | Path | Purpose |
|----------|------|---------|
| Hermes Watchdog | `logs/hermes-watchdog.log` | OC2 gateway health, workspace monitoring |
| OC2 Monitor | `logs/oc2-monitor.log` | OC2 process monitoring, heartbeat |
| Phase 10 Monitor | `tools/phase10-monitor.log` | Phase 10 execution tracking |
| Error DB | `memory-bank/error-db.json` | Structured error database |
| Errors & Solutions | `memory-bank/errors-and-solutions.md` | Human-readable error knowledge base |
| OC2 Gateway Failures | `memory-bank/OC2-GATEWAY-FAILURES.md` | Gateway-specific failure patterns |

### Reading Logs

```powershell
# Tail the last 50 lines of watchdog log
Get-Content logs/hermes-watchdog.log -Tail 50

# Search for errors in logs
Select-String -Path "logs/*.log" -Pattern "ERROR|CRITICAL|FATAL" | Select-Object -Last 20

# Search for specific error
Select-String -Path "logs/hermes-watchdog.log" -Pattern "ERR-0007"
```

---

## 5. Diagnostic Commands

### System Health

```powershell
# Check running processes
Get-Process python, node -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, StartTime, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet64/1MB,1)}} -AutoSize

# Check disk space
Get-PSDrive -PSProvider FileSystem | Format-Table Name, @{N='Used(GB)';E={[math]::Round($_.Used/1GB,1)}}, @{N='Free(GB)';E={[math]::Round($_.Free/1GB,1)}}

# Check memory usage
Get-CimInstance Win32_OperatingSystem | Format-Table @{N='Total(GB)';E={[math]::Round($_.TotalVisibleMemorySize/1MB,1)}}, @{N='Free(GB)';E={[math]::Round($_.FreePhysicalMemory/1MB,1)}}

# Check CPU usage
Get-CimInstance Win32_Processor | Format-Table Name, LoadPercentage
```

### OpenClaw Gateway

```powershell
# Check gateway status
openclaw gateway probe

# Stop gateway
openclaw gateway stop

# Start gateway
openclaw gateway start

# Restart gateway
openclaw gateway stop; Start-Sleep -Seconds 5; openclaw gateway start

# Run doctor
openclaw doctor --fix
```

### Python Environment

```powershell
# Check Python version
python --version

# Check uv version
uv --version

# List installed packages
uv pip list

# Check virtual environment
.venv\Scripts\Activate.ps1; python -c "import sys; print(sys.prefix)"
```

### Network

```powershell
# Check if port is in use
netstat -ano | findstr "18790"

# Test API endpoint
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing

# Check DNS resolution
Resolve-DnsName github.com
```

---

## 6. Error Database

The error database (`memory-bank/error-db.json`) is a structured log of all significant errors.

### Schema

```json
{
  "id": "ERR-V3-0001",
  "timestamp": "2026-05-17T15:30:00Z",
  "agent": "CC",
  "service": "V3 Resonance",
  "symptom": "NameError: name 'signals' not defined",
  "cause": "Used 'signals' instead of 'field.signals'",
  "solution": "Changed len(signals) to len(field.signals)",
  "severity": "low",
  "severity_level": 1,
  "attempts": 1,
  "tags": ["v3", "pressure_tracker", "typo"],
  "related": [],
  "status": "resolved",
  "pattern_id": "VAR-NAME-REF"
}
```

### Severity Levels

| Level | Label | Response |
|-------|-------|----------|
| 1 | low | Fix when convenient |
| 2 | medium | Fix before next phase |
| 3 | high | Fix immediately |
| 4 | critical | Stop all work, fix now |

### How to Look Up Errors

```powershell
# Search by error ID
python -c "import json; db=json.load(open('memory-bank/error-db.json')); [print(e) for e in db['entries'] if e['id']=='ERR-V3-0001']"

# Search by tag
python -c "import json; db=json.load(open('memory-bank/error-db.json')); [print(e['id'], e['symptom']) for e in db['entries'] if 'windows' in e['tags']]"
```

### When to Log an Error

Log to `error-db.json` when:
- An error persists after **2+ attempts**
- The error is **not documented** in errors-and-solutions.md
- The error affects **multiple components**
- The error is **intermittent** and hard to reproduce

---

## 7. Stale Process Cleanup

### The Problem

Agents spawn terminals for tests, servers, and background tasks. If not killed after completion, these processes:
- Consume memory and CPU
- Cause port conflicts
- Clutter the workspace
- Slow down the system

### The Solution

**At the start of EVERY session:**
```powershell
python tools/terminal_cleanup.py --force
```

**After EVERY task completion:**
Ask yourself: "Did I spawn any terminals that are still running?" If yes, kill them.

### Manual Cleanup

```powershell
# Kill all python processes (careful!)
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Kill all node processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

# Kill specific process by PID
Stop-Process -Id <PID> -Force

# Kill processes using a specific port
$port = 8000
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### Prevention

The `terminal_cleanup.py` tool uses WMIC to find python/node processes older than 60 minutes and kills them. It:
- Skips the current process
- Reports what was killed
- Supports `--force` flag for actual cleanup
- Supports `--all` flag for aggressive cleanup

---

## Debugging Workflow Summary

```
1. READ the error message (bottom of traceback first)
2. CLASSIFY the error type (import, assertion, type, name, etc.)
3. SEARCH error-db.json for known patterns
4. FORM a hypothesis
5. APPLY one targeted fix
6. VERIFY the fix (run the specific test)
7. RUN broader tests (check for regressions)
8. LOG the error if it took >2 attempts
9. COMMIT the fix
```
