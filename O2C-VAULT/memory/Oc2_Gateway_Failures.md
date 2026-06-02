# Oc2 Gateway Failures

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# 🔴 OC2 Gateway — Common Errors & Failures Reference

> **Created by:** PM (Polymorph) — 2026-05-17
> **Purpose:** Quick-reference for OC2 gateway failure patterns, causes, and fixes.
> **⚠️ DO NOT touch any OC2 files directly.** This is a READ-ONLY reference for OC2 to consult.
> **Source:** AGENTS.md, team-chat.md, error-db.json, workspace-state.md, CODEMAP.md

---

## 🔑 Key Facts

| Field | Value |
|-------|-------|
| **Service** | OC2 (OpenClaw 2) — sole OpenClaw gateway |
| **Port** | 18790 |
| **Role** | Execution / Discord / Telegram |
| **Telegram** | @OC2BLRBOT |
| **Config** | `C:\Users\wifik\.openclaw-2\openclaw.json` |
| **Restart command** | `openclaw gateway stop` → `openclaw gateway run --port 18790` → wait 5s → `openclaw gateway probe` |
| **Rule** | 90% of issues fixed by restart. Do NOT debug code first. |

---

## 🚨 Failure Pattern #1 — Gateway Unresponsive / Down

| Field | Value |
|-------|-------|
| **Symptom** | OC2 not responding to messages, health check fails |
| **Most likely cause** | Gateway process crashed or was killed |
| **Fix** | Restart: `openclaw gateway stop` → `openclaw gateway run --port 18790 --allow-unconfigured` → wait 5s → probe |
| **Prevention** | Watchdog cron job runs every 2 min to detect drain stalls |

### Restart Procedure (Step by Step)
1. `openclaw gateway stop`
2. Wait 2 seconds
3. `openclaw gateway run --port 18790 --allow-unconfigured`
4. Wait 5 seconds
5. `openclaw gateway probe` to verify

---

## 🚨 Failure Pattern #2 — Port 18790 Already In Use (EADDRINUSE)

| Field | Value |
|-------|-------|
| **Symptom** | Gateway fails to start, "address already in use" error |
| **Cause** | Stale OC2 process still bound to port 18790 |
| **Fix** | Kill the stale process first, then restart |

### Fix Procedure
```powershell
# Find what's using port 18790
Get-Process -Id (Get-NetTCPConnection -LocalPort 18790).OwningProcess

# Kill it
Stop-Process -Id <PID> -Force

# Wait, then restart
Start-Sleep -Seconds 2
openclaw gateway run --port 18790 --allow-unconfigured
```

---

## 🚨 Failure Pattern #3 — Stale Terminals / Zombie Processes

| Field | Value |
|-------|-------|
| **Symptom** | Multiple old python/node processes consuming memory, port conflicts |
| **Cause** | Agents spawn terminals for tests/servers but don't kill them after completion |
| **Fix** | Run `python tools/terminal_cleanup.py --force` at session start |
| **Prevention** | AGENTS.md Terminal Cleanup Rule (MANDATORY) — kill after EVERY task |

### Manual Cleanup
```powershell
# Kill stale python processes >30 min old
Get-Process -Name "python" -ErrorAction SilentlyContinue |
  Where-Object { $_.StartTime -lt (Get-Date).AddMinutes(-30) } |
  Stop-Process -Force

# Kill stale node processes >30 min old
Get-Process -Name "node" -ErrorAction SilentlyContinue |
  Where-Object { $_.StartTime -lt (Get-Date).AddMinutes(-30) } |
  Stop-Process -Force
```

---

## 🚨 Failure Pattern #4 — Windows CMD Restrictions

| Field | Value |
|-------|-------|
| **Symptom** | File operations fail, encoding errors, path issues |
| **Cause** | Using `cmd.exe` or `subprocess.run(..., shell=True)` instead of PowerShell |
| **Fix** | Always use PowerShell first for Windows operations |

### Correct Pattern
```python
subprocess.run(['powershell', '-NoProfile', '-Command', '...'])
```

### Wrong Pattern (DO NOT USE)
```python
subprocess.run(..., shell=True)  # Uses cmd.exe — causes issues
```

---

## 🚨 Failure Pattern #5 — Drain Watchdog Triggers

| Field | Value |
|-------|-------|
| **Symptom** | Gateway log shows "still draining" repeated, "drain timeout reached", or "failed to reacquire gateway lock" |
| **Cause** | Sub-agents still running when gateway tries to restart/shutdown |
| **Fix** | Watchdog auto-kills active sub-agents, waits 5s, then restarts gateway |
| **Log location** | `C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-YYYY-MM-DD.log` |

### Manual Intervention (if watchdog fails)
```powershell
# List active sub-agents via openclaw CLI
# Kill each one
# Wait 5 seconds
# Restart gateway
```

---

## 🚨 Failure Pattern #6 — OCE Backend Failures (Port 3000)

| Field | Value |
|-------|-------|
| **Symptom** | OCE dashboard at `http://localhost:3000/` not loading |
| **Cause** | `python oce/backend/main.py` crashed (Exit Code 1) |
| **Fix** | Check for stale process on port 3000, kill it, restart |

### Fix Procedure
```powershell
# Check what's on port 3000
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue).OwningProcess

# Kill stale OCE process
Stop-Process -Id <PID> -Force

# Restart OCE
cd C:\Users\wifik\Desktop\projects\larger-lab
.venv\Scripts\python.exe oce/backend/main.py
```

---

## 🚨 Failure Pattern #7 — Test Failures After Code Changes

| Field | Value |
|-------|-------|
| **Symptom** | `pytest` exits with code 1, tests fail |
| **Common causes** | Variable name typos, wrong imports, duplicate keyword args, wrong object types |
| **Fix** | Read error trace from LAST action, not health check. One fix at a time. |

### Common Test Error Patterns (from workspace history)
| Error | Cause | Fix |
|-------|-------|-----|
| `NameError: name 'signals' not defined` | Used `signals` instead of `field.signals` | Qualify variable with object prefix |
| `duplicate keyword arg` | Same parameter passed twice in function call | Remove duplicate |
| `wrong object for field_manager` | Passed incorrect type to function | Check caller, verify expected type |
| `SignalPacket import error` | Wrong import path | Verify module location and import path |

---

## 🚨 Failure Pattern #8 — Context Monitor Alerts

| Field | Value |
|-------|-------|
| **Symptom** | Context usage at 75%, 90%, or 95% thresholds |
| **Cause** | Long conversation, large file reads, too many tool outputs |
| **Fix** | Summarize and start fresh. Surface the breach. Do not silently overrun. |
| **Thresholds** | 75% = warning, 90% = critical, 95% = emergency |

---

## 📋 Quick Diagnostic Checklist

When OC2 gateway fails, check in this order:

1. ✅ Is the gateway process running? → `Get-Process -Name "node" | Where-Object { $_.CommandLine -match 'openclaw' }`
2. ✅ Is port 18790 in use? → `Get-NetTCPConnection -LocalPort 18790`
3. ✅ Any stale terminals? → `python tools/terminal_cleanup.py --force`
4. ✅ Check gateway log → `C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-YYYY-MM-DD.log`
5. ✅ Just restart → 90% of issues fixed by restart
6. ✅ Still broken? → Read error log from LAST action, classify error type, form hypothesis

---

## 📊 Error Severity Reference

| Severity | Level | Meaning | Action |
|----------|-------|---------|--------|
| LOW | 1 | Caught immediately, minimal impact | Fix when convenient |
| MEDIUM | 2 | Wastes resources, causes conflicts | Fix same session |
| HIGH | 3 | Blocks workflow, cascading failures | Fix immediately |
| CRITICAL | 4 | System down, data loss risk | Drop everything, fix now |

---

## 🔗 Related Files (DO NOT EDIT — Reference Only)

| File | Purpose |
|------|---------|
| `AGENTS.md` | OC2 restart rule, terminal cleanup rule |
| `CLAUDE.md` | 12-rule behavioral contract |
| `memory-bank/error-db.json` | Structured error database |
| `memory-bank/errors-and-solutions.md` | Error knowledge base |
| `shared-conversations/team-chat.md` | Team coordination hub |
| `workspace-state.md` | Cross-agent relay hub |
| `tools/terminal_cleanup.py` | Stale process killer |
| `tools/progress-sync.py` | Agent progress auto-sync |

---

> **PM Note:** This file is for OC2's reference only. Do not modify any OC2 config files, agent files, or gateway files unless explicitly tasked by the operator. This is a READ-ONLY diagnostic reference.

LINKS:
[[Codemap]]
[[System Architecture]]
[[V3 Cognitive Field]]
[[Agents]]
[[Cg 1 Revised]]
[[Claude]]
[[Code Quality]]
[[Debugging]]
[[Harness Engineering]]
[[Operator Rules]]
[[Principles]]
[[Testing]]
[[Tools]]
[[User]]
[[2026 05 17]]
[[2026 05 18]]
[[2026 05 20]]
[[2026 05 21]]
[[2026 05 30]]
[[2026 05 30 Evening]]
[[2026 05 30 Nautilus Fix]]
[[2026 05 31]]
[[2026 06 01]]
[[Active Strategies Performance]]
[[Agent Topology]]
[[Api Execution Architecture 20260531]]
[[Api Reference Summary]]
[[Api Test Note]]
[[Backtest Campaign Status 20260531]]
[[Backtest Campaign V3 Results]]
[[Backtest Phase Status]]
[[Build Patterns]]
[[Build Progress 20260531]]
[[Cc Phase 01 Build Certification Report]]
[[Cerebus Nt8 Deployment Campaign 20260531]]
[[Daily Runtime 20260531]]
[[Dashboard Build Complete]]
[[Doctor Prescription]]
[[Errors And Solutions]]
[[Executor Crash 20260531]]
[[Failure Index Oc2]]
[[Foundational Principles]]
[[Hermes Agent Activation Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Hermes Obsidian Test   Vault Working]]
[[Journal 20260602T004840Z Command Graph]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Graph Summary]]
[[Journal 20260602T004840Z Sync]]
[[Journal 20260602T004841Z Conversation]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Spawn Research]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Task Update]]
[[Keyerror Data Validation 20260531 0245]]
[[Live Deployment Status]]
[[Master Plan Assessment 20260531]]
[[Module Guide Summary]]
[[O2C Pipeline]]
[[Observer Core O1 O7]]
[[Obsidian Vault Connection Info]]
[[Oc2 Identity]]
[[Oc2 Vault Access Guide]]
[[Ontology Core Summary]]
[[Operational State 20260531]]
[[Option A Confirmed 20260531]]
[[Pm2 Test Note]]
[[Progress]]
[[Python Vs Nautilus Tradecount Investigation 20260601]]
[[Quantlab Bible]]
[[Sage Audit 20260531 Environment Utilization]]
[[Sage Audit 20260531 Environment Utilization V2]]
[[Sage Audit Environment Utilization]]
[[Self Heal Report]]
[[Session 20260531 2200]]
[[Session Testagent 20260531 0245]]
[[Session Testagent 20260531 0245 Full]]
[[Srra Oph]]
[[Task Flow]]
[[Team Phase01 Status]]
[[Team Roster]]
[[Test Note]]
[[Test Pattern]]
[[Track A Build Complete 20260531]]
[[Track A Build Status]]
[[Track A Ninjascript Build 20260531]]
[[Tradovate Api Discovery 20260531]]
[[Vault Distillation 20260531 0245]]
[[Welcome]]
[[Action]]
[[Cal]]
[[Dashboard]]
[[Failures]]
[[Minimal]]
[[Network Patterns]]
[[Patterns]]
[[Pitfalls]]
[[Server]]
[[Sources]]
[[System]]
[[Template Integrity]]
[[Usage]]
[[Workflow]]
[[Memory]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Openrouter Gateway]]
[[Telegram Gateway]]
