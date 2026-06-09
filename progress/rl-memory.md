# 🦉 OWL — Working Memory

> **Auto-synced** from `progress/rl-progress.md` on every 7th update.
> This is working memory — compact, current, task-focused.
> Max ~2,000 chars. Prune old entries when full.

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

## Current Context (2026-06-08)

### Status
🟢 Active — DUPLICATE CRISIS RESOLVED

### Active Phase
**PO × VTuber Integration** — P3.4 pending

### Recent Activity
#### [RL] 2026-06-08 — Duplicate Process Crisis Resolved
- Created `quant-lab/mt5/clean_bridge.py` with Windows mutex singleton
- Updated `scripts/signal_bot.py` with singleton enforcement
- Updated `scripts/process_registry.py` to use clean_bridge
- Added FR40.PRO to `quant-lab/mt5/deploy_config.py`
- Created `scripts/start_clean_bridge.ps1` for explicit venv startup
- **Root cause:** UV Python spawning as child of venv bridge (PID parent chain)
- **Solution:** Windows named mutex + kill-all-duplicates on startup

### V3 Phases 7-9 (2026-05-18)
- Phase 7 multiscale modules verified (7 modules, 24 tests)
- Phase 8 coevolution tests (76 tests passing)
- Phase 9 research: field coherence, DSPy attractor optimization, positional reference systems
- **Next:** DSPy research for operator coevolution patterns

#### [RL] 2026-05-18 12:15 UTC — Phase 9 Assignment Received
- Phase 9: Sovereign Field Emergence — Research Lead tasks assigned
- RL-P9.1: Research field coherence patterns
- RL-P9.2: DSPy for attractor optimization
- RL-P9.3: Research positional reference systems
- RL-P9.4: Emergent behavior analysis
- **Ready to begin after CC builds Phase 9 modules**

---

## Sync Metadata
- **Last Sync:** 2026-05-21 14:07:41 UTC
- **Progress File:** `progress/rl-progress.md`
- **Working Memory:** `progress/rl-memory.md`
- **Sync Threshold:** 7 updates


## Sync Metadata
- **Last Sync:** 2026-05-26 14:00 UTC
- **Shared Notes (read-only):** `progress/BUILD-NOTES.md` | `progress/TEAM-NOTES.md` | `progress/phase-11-status.md`
- build_notes: `progress/BUILD-NOTES.md` (updated 2026-06-02 15:00 UTC)
