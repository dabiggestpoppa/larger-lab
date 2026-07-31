# MEMORY.md — OpenClaw 2 Persistent Memory

> Tier 1 memory. Loaded at every session start.
> Replaces Hermes (HR) as the execution agent.

## Identity
- **Tag:** 🟠 [OC2]
- **Name:** OpenClaw 2
- **Role:** Execution / Backtests / Reporting / Discord + Telegram
- **Replaces:** Hermes (HR)
- **Telegram:** @OC2BLRBOT

## Environment
- **Project**: larger-lab — AI agent harness + quantitative trading workspace
- **Stack**: Python 3.11+, Nautilus Trader, VectorBT, FastAPI
- **Package manager**: uv
- **OS**: Windows
- **Gateway port**: 18790 (sole gateway — OC1 deprecated)

## Agent Architecture
- **OC2 (OpenClaw 2)**: Execution / Discord / Telegram — port 18790, Telegram @OC2BLRBOT + Discord (sole OpenClaw gateway)
- **CC (Claude Code)**: Overseer / Architecture
- **AS (Assistant Manager)**: Quality / Testing / Docs
- **PM (Polymorph)**: Debugger / Tool Builder

## Key Rules
1. Never write to another agent sub-progress file
2. Always tag entries with 🟠 [OC2] and timestamp
3. Run progress-sync after completing significant work
4. CC is the only agent who can advance phases
5. Full workspace access

## PowerShell/Windows Execution Gotchas

### Encoding Issues
- **Problem:** Windows PowerShell defaults to `cp1252` encoding, breaking emoji and Unicode
- **Fix:** Always set `$env:PYTHONIOENCODING="utf-8"` before running Python scripts
- **Symptom:** 🔄✅⚠️ characters appear as `?` or cause silent failures

### Process Invocation
- **Problem:** `Start-Process "openclaw"` opens .ps1 in VS Code instead of executing
- **Fix:** Use `Start-Process -File "path\to\script.ps1"` or `Start-Process -WindowStyle Hidden -FilePath "python" -ArgumentList "script.py"`
- **For background processes:** Always use `-WindowStyle Hidden` to avoid terminal timeout

### Terminal Management
- **Problem:** Stale terminals accumulate (76+ hours old), causing port conflicts
- **Fix:** Kill old terminals before starting: `Get-Process powershell | Where-Object {$_.StartTime -lt (Get-Date).AddHours(-1)} | Stop-Process`
- **Best practice:** Use `gateway_watchdog.py` for 24/7 monitoring instead of async terminals

### Working Directory
- **Problem:** Scripts with relative paths fail when terminal CWD differs
- **Fix:** Use full paths: `python "C:\Users\wifik\Desktop\projects\larger-lab\scripts\script.py"`
- **Or:** `Set-Location "C:\Users\wifik\Desktop\projects\larger-lab"` before running

### PID Locking (for Python scripts)
- Always implement PID file locks to prevent duplicate instances
- Check `_PID_FILE` before starting critical services (telegram_gateway, etc.)
- Use `taskkill /F /PID <pid>` to kill stale processes

## SRRA-OPH Status
- Phases 1-7: ✅ Complete (38/38 tests passing)
- Phase 8: ⏳ Planned — Sovereign Coevolution
- Phase 9: ⏳ Planned — Meta-Coherence Governance

## Progress Sync Summary (OC2)
> **Last Sync:** 2026-05-16 07:46 UTC
> **Status:** 🟢 Active
> **Active Phase:** SRRA-OPH Phase 8 — Sovereign Coevolution (Planned)
> **Working Memory:** `progress/openclaw-2-memory.md`
