# 🔴 PM2 (Polymorph 2) — Working Memory

> **Auto-synced** from `progress/PM2-progress.md` on every 7th update.

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

## Current Context (2026-06-06)

### Status
🟢 BUILDING — O2C Research Mesh L1 complete, waiting for L1 GATE

### Assignment
- **L1.2** arXiv client — ✅ COMPLETE
- **L1.8** Rate limiter — ✅ COMPLETE
- **L2.3** Citation graph builder — ⏳ After L1 GATE
- **L3.4** Finding evaluator — ⏳ After L2 GATE
- **L3.5** Research router — ⏳ After L2 GATE
- **L4.7** Vault sync engine — ⏳ After L4 API
- **L4** OCE frontend pages — ⏳ After L3 GATE

### Sync Infrastructure (Verified 2026-06-03)
- `tools/progress-sync.py` — ✅ Code correct, daemon not running
- `tools/obsidian_vault_sync.py` — ✅ Code correct, daemon running
- `tools/gateway_watchdog.py` — ✅ Code correct, not running
- `tools/po_watchdog.py` — ✅ Code correct, not running
- `tools/pm2_autopilot.py` — ⚠️ Was spamming git, killed
- `scripts/start_telegram_gateway.py` — ⚠️ Crashes on start
- Git — ⚠️ 20+ spam commits from autopilot on master
- Vault — ✅ Sync daemon active

### Key Rules
1. Monitor, don't build (unless something wrong)
2. Test when CC is done
3. Report to team-chat.md
4. ONE system — integrate into OCE
5. Simplicity first
- build_notes: `progress/BUILD-NOTES.md` (updated 2026-06-02 15:00 UTC)
