# 🔧 Proposed Self-Heal Fleet — Distributed Diagnostic Cron Jobs

> **Author:** SAGE (Systems Architecture Advisor)  
> **Date:** 2026-05-30  
> **Status:** Design Document  
> **Problem:** Monolithic self-heal cron timed out at 180s doing everything in one session.  
> **Solution:** Distribute across 4 focused jobs. Each does ONE thing, fast.

---

## Design Principles

1. **One job, one job.** No job tries to do everything.
2. **LLM stays lean.** Heavy lifting done by Python scripts; LLM only interprets results.
3. **Two-tier output.** Silent log writes by default; alert to MAD only on anomalies.
4. **Staggered schedule.** No two jobs fire at the same time; no job blocks another.
5. **Fail-soft.** If one job fails, the others still run. No cascading dependencies.

---

## Job 1 — STRUCT (Structure & Hygiene Scanner)

**Schedule:** Daily, 6:00 AM EDT  
**Timeout budget:** 45s  
**Runs Python script:** `tools/self_heal.py` (already exists — works fine)

### agentTurn Payload
```
Run the structure & hygiene scanner silently:

  python tools/self_heal.py

Read the report at memory/memory-bank/self-heal-report.md.

IF overall status is "HEALTHY" AND no BLOAT or MISSING files:
  Reply with: "STRUCT: OK — [date]"

IF any issues found (Bloat, Missing files, Stale memory, Recurring error patterns):
  Reply with a structured alert:
  "STRUCT ALERT:
   - [issue 1]
   - [issue 2]
   Severity: LOW/MEDIUM/HIGH"
```

### What it checks
- Bootstrap file bloat (AGENTS.md, MEMORY.md, SOUL.md, HEARTBEAT.md) against defined limits
- Memory drift — stale date sections with active markers
- Error pattern frequency in error-db.json
- Stale state — `__pycache__` dirs, `.bak/.tmp` files, old session logs

### What it outputs
- **Healthy →** Silent STRUCT: OK confirmation (logged in cron history)
- **Issues →** Structured STRUCT ALERT message with severity and specific findings

### Token/time cost
- Python script runs in ~3s, generates <1KB report
- LLM reads report + generates response: ~15-20s, ~1.5K tokens
- **Total estimate: 25s, well under 45s**

---

## Job 2 — PULSE (Cron Fleet Health Monitor)

**Schedule:** Daily, 6:15 AM EDT (15 min after STRUCT)  
**Timeout budget:** 60s  

### agentTurn Payload
```
Review the cron fleet health. Use the OpenClaw `cron` tool to list recent job runs.

Check for each active cron job:
1. Did it run on time in the last 24h?
2. Any consecutive failures (2+ in a row)?
3. Any timeouts?
4. Any jobs that haven't run but should have?

Check these specific stale-process indicators:
- Run: python tools/terminal_cleanup.py --dry-run
  (This lists stale PID files without killing anything)

IF all jobs ran successfully and no stale PIDs:
  Reply: "PULSE: All cron jobs nominal — [date]"

IF anomalies detected:
  Reply with:
  "PULSE ALERT:
   - [job name]: [issue — missed/consecutive fails/timeout]
   - Stale PIDs: [count] ([brief detail])
   Severity: LOW/MEDIUM/HIGH"
```

### What it checks
- All registered cron jobs: on-time execution, consecutive failures, timeout patterns, missed runs
- Stale PID files via terminal_cleanup.py --dry-run

### What it outputs
- **Nominal →** Silent PULSE: OK
- **Anomalies →** PULSE ALERT with which job, what pattern, severity

### Token/time cost
- `cron` tool call: ~5s
- terminal_cleanup.py --dry-run: ~2s
- LLM analysis + response: ~20-30s, ~2K tokens
- **Total estimate: 40s**

---

## Job 3 — ECHO (Memory & Trail Maintenance)

**Schedule:** Daily, 6:30 AM EDT (weekly deep mode on Sundays)  
**Timeout budget:** 55s (daily), 60s (Sunday deep)

### agentTurn Payload — Daily (Mon–Sat)
```
Lightweight maintenance pass:

1. Check if memory/memory-bank/ has session-*.md files older than 14 days.
   Run: python tools/workspace_cleanup.py --scan-only --target memory-bank --age 14

2. Check MEMORY.md size vs the 15000 char limit.
   Just check — don't compress yet. If under 12000 chars, fine. If over, note it.

3. Check if the team-chat.md file in shared-conversations/ is growing beyond 500 lines.
   If so, note it for archive.

IF all within bounds:
  Reply: "ECHO: Bounds OK — [date]"

IF any nearing limits:
  Reply:
  "ECHO NOTE:
   - [file/resource]: [current size vs limit]
   Suggestion: [compress/archive when convenient]"
```

### agentTurn Payload — Weekly Deep (Sunday 6:30 AM)
```
Weekly deep trail maintenance:

1. Run: python tools/workspace_cleanup.py --scan-only --full

2. Count session files in memory/memory-bank/ and shared-conversations/chat-archive/ older than 30 days.

3. Check if MEMORY.md has date sections older than 30 days that reference completed/closed items.

4. Check progress/ directory — any progress files not updated in 14+ days?

IF everything is clean:
  Reply: "ECHO DEEP: Trail clean — [date]"

IF maintenance needed:
  Reply:
  "ECHO DEEP ACTION:
   - [action 1 — e.g., archive 12 session files from memory/memory-bank/]
   - [action 2 — e.g., compress MEMORY.md section from May 1-7]
   Priority: LOW (can be done by OWL during next session)"
```

### What it checks
- **Daily:** Session file age, MEMORY.md size, team-chat.md growth
- **Weekly Deep:** Full workspace scan, 30-day-old sessions, stale progress files, old MEMORY.md sections

### What it outputs
- **Daily OK →** Silent ECHO: Bounds OK
- **Daily notes →** ECHO NOTE with what's growing and suggestions
- **Weekly clean →** Silent ECHO DEEP: Trail clean
- **Weekly action →** ECHO DEEP ACTION with specific archive/compress tasks (LOW priority — OWL handles next session)

### Token/time cost
- Daily: ~30s, ~2K tokens (lightweight, mostly script output)
- Weekly: ~45s, ~3K tokens (more files to scan, but still script-heavy/LLM-light)

---

## Job 4 — DRIFT (Architecture & Config Alignment)

**Schedule:** Every 3 days, 6:45 AM EDT  
**Timeout budget:** 55s  

### agentTurn Payload
```
Architecture drift detection pass:

1. Check key config files exist and are non-empty:
   - AGENTS.md, SOUL.md, IDENTITY.md, USER.md, TOOLS.md
   - .agent-tags.json, .phase-state.json
   - pyproject.toml

2. Check for structural anomalies:
   - Does oce/backend/main.py exist?
   - Does srrs_opc/ have a pyproject.toml or setup.py?
   - Are there any .py files in the workspace root (not in subdirs) that shouldn't be there?

3. Check phase-state.json — is the current phase consistent with AGENTS.md status table?
   (Read both, compare. If AGENTS says O-7 complete but phase-state says O-6, flag it.)

4. Check for new untracked large files (>1MB) in workspace root or tools/:
   Run: Get-ChildItem -Path . -Recurse -File | Where-Object { $_.Length -gt 1MB -and $_.DirectoryName -notlike '*node_modules*' -and $_.DirectoryName -notlike '*__pycache__*' } | Select-Object FullName, Length

IF everything aligned:
  Reply: "DRIFT: Architecture aligned — [date]"

IF drift detected:
  Reply:
  "DRIFT ALERT:
   - [drift 1 — e.g., phase-state.json says O-6 but AGENTS.md says O-7]
   - [drift 2 — e.g., 3 stray .py files in workspace root]
   Severity: LOW/MEDIUM/HIGH"
```

### What it checks
- Core config file presence and non-emptiness
- Structural integrity (key source files exist)
- Phase state consistency between .phase-state.json and AGENTS.md
- Stray large files that shouldn't be in the workspace

### What it outputs
- **Aligned →** Silent DRIFT: Architecture aligned
- **Drift →** DRIFT ALERT with specific inconsistencies and severity

### Token/time cost
- File existence checks: ~5s
- Phase comparison: ~10s (LLM reads two small files)
- Large file scan: ~3s
- LLM analysis + response: ~15-20s, ~2K tokens
- **Total estimate: 35s**

---

## Fleet Summary

| Job | Schedule | Focus | Script Heavy? | Alert Threshold |
|-----|----------|-------|---------------|-----------------|
| **STRUCT** | Daily 6:00 AM | File bloat, stale state, error patterns | ✅ Yes (self_heal.py) | Any BLOAT/MISSING/recurring errors |
| **PULSE** | Daily 6:15 AM | Cron fleet health, stale PIDs | ✅ Yes (terminal_cleanup.py --dry-run) | Missed runs, consecutive fails, timeouts |
| **ECHO** | Daily 6:30 AM + Weekly deep | Memory/trail maintenance, session archives | ✅ Yes (workspace_cleanup.py --scan-only) | Size bounds exceeded |
| **DRIFT** | Every 3 days 6:45 AM | Config alignment, phase consistency, stray files | ❌ No (LLM file reads + PowerShell) | Phase mismatch, missing configs, stray files |

---

## Alert Routing

- **LOW severity** → Logged only. No MAD notification. OWL reviews during next session.
- **MEDIUM severity** → Logged + included in next OWL→MAD status summary.
- **HIGH severity** → Immediate MAD notification via Telegram message.

---

## What Was Cut (and why)

| Old self-heal task | Where it went | Why |
|-------------------|---------------|-----|
| Memory search (semantic) | **Removed** | Too token-heavy for isolated cron. OWL does this during normal sessions. |
| Running doctor.py | **Removed** | File doesn't exist. Replaced by STRUCT's bootstrap checks. |
| Reading report directories | **Simplified** | ECHO now only checks file counts/ages, not content. |
| Updating MEMORY.md | **Removed from cron** | Too risky for isolated session. OWL handles during normal sessions. |
| Cron health review | **PULSE job** | Dedicated, focused, with pattern detection. |
| Architecture drift | **DRIFT job** | Dedicated, every 3 days (doesn't need daily). |

---

## Implementation Notes

1. **No new Python scripts needed.** The fleet reuses `self_heal.py`, `terminal_cleanup.py`, and `workspace_cleanup.py` — all already exist and work.

2. **Each job is independently schedulable.** If MAD wants to disable DRIFT, it doesn't affect STRUCT/PULSE/ECHO.

3. **The Sunday ECHO deep mode** replaces the old "compress MEMORY.md" behavior but makes it a suggestion to OWL rather than an autonomous edit (safer).

4. **If workspace_cleanup.py doesn't support --scan-only / --age flags**, those are trivial additions (10 lines of argparse). The core `os.walk` + `os.path.getmtime` logic already exists in the file.

5. **Total daily cron time budget:** ~2.5 minutes across 4 jobs (STRUCT 25s + PULSE 40s + ECHO 30s + DRIFT 35s on its days). Well within any reasonable gateway budget.

---

*End of design document.*
