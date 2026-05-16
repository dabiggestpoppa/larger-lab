# 🦉 OWL — Working Memory

> **Auto-synced** from `progress/rl-progress.md` on every 3th update.
> This is working memory — compact, current, task-focused.
> Max ~2,000 chars. Prune old entries when full.

---

## Current Context (2026-05-16 13:18:36 UTC)

### Status
Unknown

### Active Phase
None

### Pending Tasks
- None

### Recent Activity
#### 🦉 [RL] 2026-05-16 — Both Gateways Fixed & Running 24/7
- **Root cause of both gateways failing**: `gateway.cmd` used `openclaw gateway --port X` instead of `openclaw gateway run --port X --allow-unconfigured`
- **Fixes applied**:
  - Fixed `C:\Users\wifik\.openclaw\gateway.cmd` — added `run` subcommand and `--allow-unconfigured`
  - Fixed `C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd` — same fix
  - Fixed OC2 startup file to properly call its `gateway.cmd` with full path
  - Created `tools\gateway-watchdog.cmd` — checks both gateways every 60s, restarts if down
  - Created `tools\register-gateway-tasks.ps1` — Scheduled Task registration (requires Admin)
  - Added watchdog to startup folder for automatic 24/7 monitoring
- **Status**: ✅ Both gateways live and healthy
  - OC1 (port 18789): `{"ok":true,"status":"live"}` — PID 19844
  - OC2 (port 18790): `{"ok":true,"status":"live"}` — PID 41592
- **Auto-start**: Startup folder entries for both gateways + watchdog
- **Note**: For even more reliable auto-start, run `tools\register-gateway-tasks.ps1` as Administrator to create Windows Scheduled Tasks with restart-on-failure

#### 🦉 [RL] 2026-05-16 — OC1 Telegram Not Responding (Diagnosis)
- **Symptom**: OC1 gateway running (port 18789) but Telegram bot @finalstrawclawbot not responding
- **Root cause 1**: Missing `openrouter` provider in OC1's `openclaw.json` — only had poolside/nvidia/deepseek, causing fallback to `openai` provider → "No API key found" error
- **Root cause 2**: OC1's `models.json` has placeholder `"apiKey": "OPENROUTER_API_KEY"` instead of actual key
- **Root cause 3**: Telegram API connectivity issues — DNS resolution slow, fetch timeouts, event loop delays up to 104s
- **Root cause 4**: 203 Telegram commands registered (limit 100), causing command sync failures
- **Fix applied**: Added openrouter provider to OC1's `openclaw.json`
- **Status**: After restart, OC1 health check failed — needs further investigation in new chat
- **OC2**: Working fine throughout, no changes needed
- **Detailed notes**: See `/memories/session/oc1-gateway-diagnosis.md`

#### 🦉 [RL] 2026-05-16 — Gateway Diagnostics Complete, Ready for Fix
- **Current state**: Both gateways running (OC1 PID 14520, OC2 PID 21768)
- **OC2 issue identified**: Stuck Telegram session `agent:main:telegram:direct:8258195396` blocking event loop for 1000+ seconds
- **Root cause**: Event-loop starvation from stuck session → Telegram polling stalls every ~180s → forced restarts
- **Fixes needed**:
  1. Clear stuck session from OC2's `sessions.json`
  2. Disable native Telegram commands (`channels.telegram.commands.native: false`) to avoid 203-command overload
  3. Restart both gateways cleanly
- **PowerShell spam issue**: `openclaw gateway probe` without `--token` hangs forever → terminal timeout → new terminal spawned → infinite loop
- **Solution**: Use venv-based Python scripts for gateway management instead of CLI commands

---

## Sync Metadata
- **Last Sync:** 2026-05-16 13:18:36 UTC
- **Progress File:** `progress/rl-progress.md`
- **Working Memory:** `progress/rl-memory.md`
- **Sync Threshold:** 3 updates
