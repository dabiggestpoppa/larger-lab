# OC2 Debugging — RESOLVED 2026-06-06 20:32 EST

## ✅ STATUS: FIXED — OC2 BACK ONLINE

**Bot:** @OC2BLRBOT on Telegram
**Gateway:** `http://127.0.0.1:18790/health` → `{"ok": true, "status": "live"}`
**Downtime:** ~7 hours (13:30 → 20:30 EST)
**Fix committed:** 2026-06-06 20:32

> **For complete runbook, see [`tools/OPENCLAW-RUNBOOK.md`](../tools/OPENCLAW-RUNBOOK.md) — 5-minute fix checklist + diagnostics.**

## 🎯 ACTUAL ROOT CAUSE (finally confirmed)

There were **TWO config files** and all previous attempts edited the wrong one:

| File | What It Is | What Edits It |
|------|-----------|---------------|
| `C:\Users\wifik\.openclaw-2\openclaw.json` | Primary/CLI config (2,554 bytes) | `openclaw config set/patch/get` CLI |
| `C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json` | **Gateway runtime config (5,714 bytes) — THE REAL ONE** | Direct file edit only |

The `openclaw config` CLI says `Config valid: $OPENCLAW_HOME\.openclaw\openclaw.json` — but `$OPENCLAW_HOME` isn't expanded; the CLI points to a path that doesn't exist as a file. The **gateway actually loads from the deeper `.openclaw-2/.openclaw/openclaw.json`**.

**The previous 14 attempts edited the wrong file.** The CLI was validating and writing the primary config, while the gateway was happily reading the still-broken runtime config.

## 🐛 Secondary Issue

Model resolver: OpenClaw 2026.5.7 splits model IDs on `/` and uses the first segment as the **provider name**. So `inclusionai/ring-2.6-1t` → provider `inclusionai` (which doesn't exist). Only `openrouter` and `nvidia` were registered. The fix: use a model name whose provider prefix matches a registered provider — `openrouter/owl-alpha`.

## 🛠️ WHAT ACTUALLY FIXED IT

1. **Stop the gateway cleanly** — `Stop-ScheduledTask OpenClaw-2-Gateway` + `Stop-Process -Force` on the node process holding port 18790
2. **Edit BOTH config files** (atomic, with gateway stopped so no overwrite race):
   - `agents.defaults.model` → `openrouter/owl-alpha`
   - `agents.defaults.subagent.model` → `openrouter/owl-alpha`
   - Removed dead entries: `inclusionai/ring-2.6-1t`, `minimax/minimax-m3` from both `agents.defaults.models` and `openrouter` provider's `models[]`
   - Removed `minimax` plugin entry
   - Updated `meta.lastTouchedVersion` and `wizard.lastRunVersion` from `2026.6.1` → `2026.5.7` (kills spurious version warnings)
3. **Restart via scheduled task** — `Start-ScheduledTask OpenClaw-2-Gateway`
4. **Verified**: model resolution succeeded (`openrouter/openrouter/owl-alpha` loaded in 6432ms), Telegram provider started (`@OC2BLRBOT`), agent processed user message and sent response.

## 📋 EXACT CONFIG CHANGES

**BEFORE (broken):**
```json
"agents": {
  "defaults": {
    "model": "inclusionai/ring-2.6-1t",
    "subagent": { "model": "minimax/minimax-m3" },
    "models": {
      "inclusionai/ring-2.6-1t": { "alias": "ring" },
      "minimax/minimax-m3": { "alias": "minimax" },
      ...
    }
  }
}
```

**AFTER (working):**
```json
"agents": {
  "defaults": {
    "model": "openrouter/owl-alpha",
    "subagent": { "model": "openrouter/owl-alpha" },
    "models": {
      "openrouter/owl-alpha": { "alias": "owl" },
      "nvidia/nemotron-3-ultra-550b-a55b": { "alias": "nemotron" }
    }
  }
}
```

## 📁 KEY FILES (REFERENCED FOR FUTURE FIXES)

- **Config 1 (primary/CLI):** `C:\Users\wifik\.openclaw-2\openclaw.json`
- **Config 2 (gateway runtime):** `C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json`
- **Scheduled task:** `OpenClaw-2-Gateway` (cmd: `C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd`)
- **Launch script:** `C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd`
- **Log file:** `C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-06-06.log`
- **Telegram bot:** @OC2BLRBOT
- **Auth token:** `oc2-68cdb0729953cce1aecaf09a9dffddac574c9a674f46aa77` (do not rotate casually)

## 🚨 NEVER DO THESE AGAIN

- ❌ Don't use `openclaw config set` CLI to fix this — it edits the wrong file
- ❌ Don't edit `inclusionai/ring-2.6-1t` model — that model is gone, no provider for it
- ❌ Don't downgrade OpenClaw — 2026.5.7 is the working version
- ❌ Don't add `inclusionai` as a provider — OpenClaw strips it on validation
- ❌ Don't edit configs while gateway is running — race condition overwrites your changes

## ✅ ALWAYS DO THIS

- ✅ Edit BOTH config files atomically (gateway stopped)
- ✅ Use `openrouter/owl-alpha` as the model — it's the only one fully registered
- ✅ Verify with `/health` endpoint AND log inspection
- ✅ If CLI is needed, use `openclaw config set agents.defaults.model openrouter/owl-alpha` AND also manually edit the deeper config file

## 📊 LESSONS LEARNED

1. **Two-file config trap**: OpenClaw 2026.5.7 has dual config paths. The CLI is misleading about which one it writes to. Future agents: when fixing OpenClaw, always edit the deeper file at `<HOME>/.openclaw-X/.openclaw/openclaw.json`.

2. **Model name = provider prefix**: OpenClaw uses the first `/`-segment of the model ID as the provider name. Always use a model whose prefix matches a registered provider (e.g., `openrouter/owl-alpha` works because `openrouter` is registered; `inclusionai/ring-2.6-1t` fails because `inclusionai` isn't registered).

3. **Always stop before edit**: The gateway overwrites parts of the config on startup. Stop it cleanly first, then edit, then restart.

4. **Scheduled task is the source of truth**: `OpenClaw-2-Gateway` is the Windows task that restarts the gateway on logon. Use `Stop-ScheduledTask` / `Start-ScheduledTask` to control it cleanly.

5. **Watchdog needed**: A 7-hour outage should not happen. Need `openclaw_watchdog.py` that:
   - Pings `/health` every 60s
   - Checks log for `FailoverError` in last 5 min
   - Auto-restarts gateway on health fail
   - Alerts via Telegram

## 🔄 NEXT STEPS

- [x] OC2 fixed and verified
- [x] Created `tools/OPENCLAW-RUNBOOK.md` (complete triage + fix guide)
- [ ] Create `tools/openclaw_watchdog.py` (auto-restart on health fail)
- [ ] Update all agent memory files with the two-file trap lesson
- [ ] Add to onboarding: "How to debug OC2 if it goes down"
- [ ] Consider running gateway in foreground to see real-time errors

## 📞 IF OC2 GOES DOWN AGAIN

**Speed-run this checklist:**

1. `Invoke-RestMethod http://127.0.0.1:18790/health` — is it up?
2. If down, check `Get-ScheduledTask OpenClaw-2-Gateway` — is it running?
3. Check last 50 lines of log for errors
4. If `FailoverError: Unknown model` → check `C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json` → `agents.defaults.model` → must be a model with a registered provider prefix
5. Fix both config files atomically (gateway stopped)
6. Restart via scheduled task
7. Verify with `/health` and Telegram test message

**Total time should be: 5-10 minutes** if you know the two-file trap. (It took 7 hours today because nobody found the deeper config file.)  
- OC2 Bot: ❌ Online but not responding to messages

## Root Cause (100% Confirmed)
OpenClaw 2026.6.1 changed model resolution. Error:
```
FailoverError: Unknown model: inclusionai/ring-2.6-1t
Found agents.defaults.models["inclusionai/ring-2.6-1t"], but no matching models.providers["inclusionai"].models[] entry.
```

The model `inclusionai/ring-2.6-1t` needs a provider named `inclusionai` but only `openrouter` provider exists.

## Secondary Issue
OpenClaw overwrites `.openclaw-2/openclaw.json` on every startup, reverting manual config changes.

## ALL Attempts (14 total — ALL FAILED)
1. Kill/restart gateway
2. Change model to openrouter/auto
3. Clean reinstall OpenClaw
4. openclaw doctor --fix
5. Delete session state
6. Change tools.profile
7. Add inclusionai provider (stripped by OpenClaw)
8. Set model to owl-alpha (reverted)
9. Read-only config (OpenClaw couldn't start)
10. Disable duplicate scheduled tasks
11. Delete OpenClaw-1-Gateway scheduled task
12. Downgrade OpenClaw to 2026.5.7
13. Add inclusionai provider with baseUrl (still fails)
14. Remove inclusionai alias from models (reverted on startup)

## What MIGHT Work (Not Yet Tried)
1. Use `openclaw config set` CLI to change model
2. Completely replace config with a known-working version from another agent
3. Run OC2 with `--model openrouter/auto` flag if supported
4. Check if Hermes uses a different model config that works

## Key Files
- Config: `.openclaw-2/openclaw.json`
- Debug log: `C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-06-06.log`
- Sessions: `.openclaw-2/.openclaw/agents/main/sessions/`

## Recommendation
Ask CC (Claude Code) to fix this. The issue is:
1. OpenClaw 2026.6.1 model resolution is broken for `inclusionai/ring-2.6-1t`
2. OpenClaw overwrites config on startup
3. Need to either: use `openclaw config set`, or fix the provider registration in a way OpenClaw accepts, or downgrade to a version that doesn't have this issue
