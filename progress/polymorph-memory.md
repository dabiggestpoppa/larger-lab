# 🔴 Polymorph — Working Memory

> **Auto-synced** from `progress/polymorph-progress.md` on every 7th update.
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

## Current Context (2026-05-21 14:07:41 UTC)

### Status
🟢 Active — V3 PHASE 10 COMPLETE

### Active Phase
**V3 Phase 10 — Recursive Field Computation** ✅ COMPLETE

### Pending Tasks
- Build tools/operator/coevolution-debug.py CLI
- Debug coevolution modules (operator_model, constraint_model, coherence_reinforcement, bidirectional_adaptation, cognitive_load, alignment_tracking, anti_manipulation)
- Operator integration for coevolution monitoring
- Build tools/operator/field-debug.py CLI
- Build tools/operator/resonance-debug.py CLI
- Debug Phase 9 modules (resonance_engine, recursive_field_nodes, attractor_mapper, drift_governor, reconstruction_core, continuity_identity_engine)
- field_core infrastructure setup

### Recent Activity
*No entries yet*

---

## Sync Metadata
- **Last Sync:** 2026-05-21 14:07:41 UTC
- **Progress File:** `progress/polymorph-progress.md`
- **Working Memory:** `progress/polymorph-memory.md`
- **Sync Threshold:** 7 updates

## Progress Sync Summary (PM)
> **Last Sync:** 2026-05-21 14:07 UTC
> **Status:** 🟢 Active — V3 PHASE 10 COMPLETE
> **Active Phase:** **V3 Phase 10 — Recursive Field Computation** ✅ COMPLETE
> **Working Memory:** `progress/polymorph-memory.md`


## Sync Metadata
- **Last Sync:** 2026-05-26 14:00 UTC
- **Shared Notes (read-only):** `progress/BUILD-NOTES.md` | `progress/TEAM-NOTES.md` | `progress/phase-11-status.md`
- build_notes: `progress/BUILD-NOTES.md` (updated 2026-06-02 15:00 UTC)
