# 🔴 PM2 (Polymorph 2) — Working Memory

> **Auto-synced** from `progress/PM2-progress.md` on every 7th update.

---

## 🚨 CRITICAL: OpenClaw Gateway Knowledge (2026-06-06 — 7hr outage fix)

### The Two-File Config Trap
**MOST IMPORTANT LESSON** — would have saved 7 hours on 2026-06-06:

OpenClaw 2026.5.7 has **TWO config files**. The CLI edits the wrong one.

| File | What It Is | What Edits It |
|------|-----------|---------------|
| `C:\Users\wifik\.openclaw-2\openclaw.json` | Primary/CLI config (~2.5KB) | `openclaw config set/patch/get` |
| `C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json` | **Gateway runtime — THE REAL ONE** | **Direct file edit ONLY** |

**Rule:** When fixing OpenClaw, edit BOTH files. Always. Atomically (gateway stopped).

### Model Name = Provider Prefix
OpenClaw splits model IDs on `/` and uses the first segment as provider name.
- ✅ `openrouter/owl-alpha` works (provider `openrouter` is registered)
- ❌ `inclusionai/ring-2.6-1t` fails (provider `inclusionai` is NOT registered)

**Always use models with provider prefix matching a registered provider.**

### Fix OC2 in 5 Minutes (Speed-Run)
```powershell
# Stop
Stop-ScheduledTask -TaskName "OpenClaw-2-Gateway"
$proc = Get-NetTCPConnection -State Listen -LocalPort 18790 -EA SilentlyContinue
if ($proc) { Stop-Process -Id $proc.OwningProcess -Force }
Start-Sleep -Seconds 3

# Edit BOTH configs (gateway stopped):
#   "model": "inclusionai/ring-2.6-1t" → "model": "openrouter/owl-alpha"
#   "subagent": { "model": "minimax/minimax-m3" } → "openrouter/owl-alpha"

# Start
Start-ScheduledTask -TaskName "OpenClaw-2-Gateway"
Start-Sleep -Seconds 30
Invoke-RestMethod http://127.0.0.1:18790/health  # should be {"ok":true,"status":"live"}
```

### Tools Created
- `tools/OPENCLAW-RUNBOOK.md` — complete triage + fix guide
- `tools/openclaw_watchdog.py` — auto-restart on health fail, alerts via Telegram

### Key Files (OC2-specific)
- Config 1 (primary): `C:\Users\wifik\.openclaw-2\openclaw.json`
- Config 2 (gateway): `C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json`
- Task: `OpenClaw-2-Gateway` (cmd: `C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd`)
- Log: `C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-06-06.log`
- Bot: @OC2BLRBOT (Telegram)
- Token: `oc2-68cdb0729953cce1aecaf09a9dffddac574c9a674f46aa77` (don't rotate)

### What NEVER To Do
- ❌ `openclaw config set` to fix model issues (edits wrong file)
- ❌ Add `inclusionai` as provider (OpenClaw strips on validation)
- ❌ Edit configs while gateway is running (overwritten on startup)
- ❌ Use model name without registered provider prefix

### What ALWAYS To Do
- ✅ Stop gateway before editing config
- ✅ Edit BOTH config files
- ✅ Verify with `/health` endpoint after restart
- ✅ Check log for `FailoverError: Unknown model` if responding fails
- ✅ Run `openclaw_watchdog.py` for 24/7 monitoring

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

### Assignment — ALL COMPLETE ✅
- **L1.2** arXiv client — ✅ COMPLETE
- **L1.8** Rate limiter — ✅ COMPLETE
- **L2.3** Citation graph builder — ✅ (OC2 built)
- **L3.4** Finding evaluator — ✅ (OC2 built)
- **L3.5** Research router — ✅ (OC2 built)
- **L4.7** Vault sync engine — ✅ COMPLETE
- **L4** OCE frontend pages — ✅ COMPLETE

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
