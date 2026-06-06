# 🟢 Hermes — Sub-Progress Log

> **Agent:** Hermes (HR)
> **Role:** Execution / Backtesting / Reporting / Tool Builder
> **Sync Rule:** Every 7 updates → auto-sync. Every 20 entries → LLM summarization.
> **Reports to:** CC (Claude Code)

---

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

---

## Status: 🟢 ACTIVE — Phase 3 Complete

### Phase 3 — Documentation Reorganization (2026-06-01)
- [x] Archived `plans/` -> `archive/plans-original/`, moved all contents -> `docs/plans/`
- [x] Removed empty `plans/` directory (21 files + 2 subdirs relocated)
- [x] Archived `system-arch/` -> `archive/system-arch-original/`, moved all contents -> `docs/system-arch/`
- [x] Removed empty `system-arch/` directory (5 .md + 1 .jsonl relocated)
- [x] Moved to `docs/meta/`: AGENTS.md, CLAUDE.md, PRINCIPLES.md, SOUL.md, IDENTITY.md, USER.md, SUB_AGENT_RULES.md, MASTER_PROMPT.md
- [x] Moved to `docs/architecture/`: ARCHITECTURE.md, V3_ARCHITECTURE.md, CODEMAP.md, proposed-self-heal-fleet.md
- [x] Moved to `docs/reference/`: TOOLS.md, CONTRIBUTING.md, HEARTBEAT.md, workspace-state.md
- [x] Verified: Only README.md and MEMORY.md remain at root

---

### Registration (2026-05-31)
- [x] Registered in OCE Command Center as agent `hermes`
- [x] Capabilities: execution, backtesting, reporting, tool_building, telegram, nautilus_trader, strategy_implementation
- [x] Created progress file `progress/hermes-progress.md`
- [x] Posted activation summary to team-chat.md

### Pending Tasks
- [ ] Review phase plans for Hermes assignments (O-4 backtests, O-5+ execution)
- [ ] Check NautilusTrader backtest environment
- [ ] Review CEREBUS strategy implementation status
- [ ] Run pending backtests per phase plan

---
