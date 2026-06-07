# 🚨 OpenClaw Gateway Runbook

> **READ THIS FIRST** before debugging any OpenClaw issue. OC2 was down 7 hours on 2026-06-06 because this knowledge wasn't documented. **Do not repeat that mistake.**

---

## ⏱️ 5-MINUTE FIX CHECKLIST (Triage)

```powershell
# Set encoding for emoji safety
$env:PYTHONIOENCODING = "utf-8"

# 1. Is the gateway alive?
try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:18790/health" -TimeoutSec 5
    Write-Host "✅ Gateway: $($h.status)"
} catch {
    Write-Host "❌ Gateway DOWN: $($_.Exception.Message)"
}

# 2. Is the scheduled task running?
$task = Get-ScheduledTask -TaskName "OpenClaw-2-Gateway" -ErrorAction SilentlyContinue
if ($task.State -eq "Ready") { Write-Host "✅ Task: Ready" } else { Write-Host "❌ Task: $($task.State)" }

# 3. Is port 18790 listening?
$listener = Get-NetTCPConnection -State Listen -LocalPort 18790 -ErrorAction SilentlyContinue
if ($listener) { Write-Host "✅ Port: Listening (PID $($listener.OwningProcess))" }
else { Write-Host "❌ Port: NOT listening" }

# 4. Latest log errors
$log = Get-Content "C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-06-06.log" -Tail 100
$log | ForEach-Object {
    try {
        $o = $_ | ConvertFrom-Json
        if ($o.message -match "FailoverError|Unknown model|error|Error") {
            "$($o.time) [$($o.logLevelName)] $($o.message)"
        }
    } catch {}
} | Select-Object -Last 5
```

**If you see `FailoverError: Unknown model` → go to [Model Resolution Fix](#model-resolution-fix)**

**If you see nothing in logs → check the scheduled task logs in Event Viewer**

---

## 🔧 Model Resolution Fix (THE MOST COMMON ISSUE)

### Symptom
```
FailoverError: Unknown model: inclusionai/ring-2.6-1t
requestedProvider: "inclusionai"
candidateProvider: "inclusionai"
```

### Root Cause
OpenClaw splits model IDs on `/` and uses the first segment as the provider name. If `inclusionai` isn't a registered provider → fail.

### Fix (5 min)

```powershell
# Step 1: Stop gateway
Stop-ScheduledTask -TaskName "OpenClaw-2-Gateway"
Start-Sleep -Seconds 3
$node = Get-NetTCPConnection -State Listen -LocalPort 18790 -ErrorAction SilentlyContinue
if ($node) { Stop-Process -Id $node.OwningProcess -Force }
Start-Sleep -Seconds 3

# Step 2: Edit BOTH config files (CRITICAL — see Two-File Trap below)
# File A: C:\Users\wifik\.openclaw-2\openclaw.json
# File B: C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json
# In BOTH: change "model": "inclusionai/ring-2.6-1t" → "model": "openrouter/owl-alpha"
# Also change "subagent": { "model": "minimax/minimax-m3" } → "openrouter/owl-alpha"

# Step 3: Restart
Start-ScheduledTask -TaskName "OpenClaw-2-Gateway"
Start-Sleep -Seconds 30

# Step 4: Verify
$h = Invoke-RestMethod -Uri "http://127.0.0.1:18790/health" -TimeoutSec 5
Write-Host "Status: $($h.status)"
```

---

## 🪤 Two-File Config Trap (THE OTHER MOST COMMON ISSUE)

OpenClaw 2026.5.7 has TWO config files that BOTH must be in sync:

| File | Size | Edits It | Used By |
|------|------|----------|---------|
| `C:\Users\wifik\.openclaw-2\openclaw.json` | ~2.5 KB | `openclaw config` CLI | Validation only |
| `C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json` | ~5.7 KB | **Direct file edit** | **Gateway runtime** |

**The `openclaw config` CLI lies.** It reports `Config valid: $OPENCLAW_HOME\.openclaw\openclaw.json` but `$OPENCLAW_HOME` isn't expanded, and the actual file it writes is the primary one. The gateway reads the DEEPER file.

### Rule: When fixing config issues, edit BOTH files. Always.

```powershell
# Quick check: are both files in sync on the model?
$f1 = (Get-Content "C:\Users\wifik\.openclaw-2\openclaw.json" -Raw | ConvertFrom-Json).agents.defaults.model
$f2 = (Get-Content "C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json" -Raw | ConvertFrom-Json).agents.defaults.model
Write-Host "Primary config model: $f1"
Write-Host "Gateway config model:  $f2"
if ($f1 -ne $f2) { Write-Host "❌ MISMATCH — gateway will use $f2" } else { Write-Host "✅ In sync" }
```

---

## 🏗️ Architecture Reference

### OpenClaw 2026.5.7 Components

```
Windows Scheduled Task: OpenClaw-2-Gateway
  └─> cmd: gateway.cmd
        └─> node openclaw.mjs gateway run --port 18790
              ├─> Loads config: C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json
              ├─> Listens on: 127.0.0.1:18790
              ├─> Telegram: @OC2BLRBOT (token 8945439460:AAHZT2Xx...)
              └─> Model: openrouter/owl-alpha (via OpenRouter)
```

### Config File Sections (deeper file)

```json
{
  "agents": {
    "defaults": {
      "model": "openrouter/owl-alpha",       // PRIMARY model
      "subagents": {
        "model": "openrouter/owl-alpha",     // Sub-agent model
        "maxConcurrent": 5,
        "runTimeoutSeconds": 900
      },
      "models": { ... },                     // Aliases
      "workspace": "C:\\...\\larger-lab"
    }
  },
  "models": {
    "providers": {
      "openrouter": { "baseUrl": "...", "models": [...] },
      "nvidia": { ... }
      // No "inclusionai" provider — that's why ring-2.6-1t fails
    }
  },
  "channels": { "telegram": { ... } },
  "commands": { "ownerAllowFrom": ["telegram:8258195396"] }
}
```

---

## 🔍 Diagnostics

### Check Gateway Logs

```powershell
$log = "C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-06-06.log"
# Last 5 errors with timestamps
Get-Content $log -Tail 500 | ForEach-Object {
    try {
        $o = $_ | ConvertFrom-Json
        if ($o.logLevelName -in @("ERROR", "WARN")) {
            "$($o.time) [$($o.logLevelName)] $($o.message)"
        }
    } catch {}
} | Select-Object -Last 10
```

### Check What Model is Loaded

```powershell
$log = Get-Content "C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-06-06.log" -Tail 200
$log | ForEach-Object {
    try {
        $o = $_ | ConvertFrom-Json
        if ($o.message -match "agent model:") { $o.message }
    } catch {}
} | Select-Object -Last 1
# Expected: "agent model: openrouter/openrouter/owl-alpha (thinking=medium, fast=off)"
```

### Test Telegram Round-Trip

Send a message to @OC2BLRBOT and check:

```powershell
$log = Get-Content "C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-06-06.log" -Tail 100
$log | ForEach-Object {
    try {
        $o = $_ | ConvertFrom-Json
        if ($o.message -match "telegram sendMessage|telegram.*chat=8258195396") {
            "$($o.time) - $($o.message)"
        }
    } catch {}
} | Select-Object -Last 5
```

If you see `telegram sendMessage ok` after a message → bot is responding.

---

## 🚫 Common Mistakes (DON'T DO THESE)

| Mistake | Why It Fails | What To Do Instead |
|---------|--------------|---------------------|
| `openclaw config set agents.defaults.model ...` | Edits wrong file | Edit both files directly |
| Edit config while gateway is running | OpenClaw overwrites on startup | Stop gateway first |
| Add `inclusionai` provider | OpenClaw strips unknown providers | Use `openrouter/*` models instead |
| Use `inclusionai/ring-2.6-1t` as model | No `inclusionai` provider registered | Use `openrouter/owl-alpha` |
| Downgrade OpenClaw | 2026.5.7 is the working version | Stay on 2026.5.7 |
| Delete `~/.openclaw-2/.openclaw/sessions/` | Loses conversation history | Only delete if explicitly needed |
| Run `openclaw doctor --fix` | Doctor operates on wrong file | Manual config edit |

---

## 🔄 Restart Procedure (Standard)

```powershell
# 1. Stop
Stop-ScheduledTask -TaskName "OpenClaw-2-Gateway"
Start-Sleep -Seconds 3
$proc = Get-NetTCPConnection -State Listen -LocalPort 18790 -ErrorAction SilentlyContinue
if ($proc) { Stop-Process -Id $proc.OwningProcess -Force }
Start-Sleep -Seconds 3

# 2. Verify port is free
$port = Get-NetTCPConnection -State Listen -LocalPort 18790 -ErrorAction SilentlyContinue
if ($port) { Write-Error "Port 18790 still in use" }

# 3. (Optional) Edit configs here

# 4. Start
Start-ScheduledTask -TaskName "OpenClaw-2-Gateway"

# 5. Wait for ready
Start-Sleep -Seconds 30
$h = Invoke-RestMethod -Uri "http://127.0.0.1:18790/health" -TimeoutSec 5
Write-Host "Status: $($h.status)"
```

---

## 🆘 Emergency: Everything Broken

If gateway won't start, configs are corrupt, nothing makes sense:

```powershell
# 1. Stop everything
Stop-ScheduledTask -TaskName "OpenClaw-2-Gateway" -ErrorAction SilentlyContinue
Get-NetTCPConnection -State Listen -LocalPort 18790 -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# 2. Save current config as backup
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item "C:\Users\wifik\.openclaw-2\openclaw.json" "C:\Users\wifik\.openclaw-2\openclaw.json.bak.$ts"
Copy-Item "C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json" "C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json.bak.$ts"

# 3. Restore from known-good config (if exists)
# If you have a backup from when OC2 was last working, copy it back

# 4. Or rebuild config from scratch using this template
# (See "Minimal Working Config" below)
```

### Minimal Working Config (template)

```json
{
  "agents": {
    "defaults": {
      "workspace": "C:\\\\Users\\\\wifik\\\\Desktop\\\\projects\\\\larger-lab",
      "model": "openrouter/owl-alpha",
      "subagent": { "maxConcurrent": 2, "model": "openrouter/owl-alpha" },
      "models": {
        "openrouter/owl-alpha": { "alias": "owl" }
      }
    }
  },
  "gateway": {
    "mode": "local",
    "auth": { "mode": "token", "token": "oc2-68cdb0729953cce1aecaf09a9dffddac574c9a674f46aa77" },
    "port": 18790,
    "bind": "loopback",
    "tailscale": { "mode": "off", "resetOnExit": false }
  },
  "tools": { "profile": "coding" },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "8945439460:AAHZT2Xx0jHaApejRJYi-xORG5FkKNAQ5yM",
      "dmPolicy": "open",
      "groups": { "*": { "requireMention": true } }
    }
  },
  "commands": { "ownerAllowFrom": ["telegram:8258195396"] },
  "models": {
    "providers": {
      "openrouter": {
        "baseUrl": "https://openrouter.ai/api/v1",
        "apiKey": "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",
        "models": [{ "id": "openrouter/owl-alpha", "name": "openrouter/owl-alpha" }]
      }
    }
  },
  "meta": { "lastTouchedVersion": "2026.5.7", "lastTouchedAt": "2026-06-06T22:24:59.039Z" }
}
```

---

## 📞 Escalation

If you've tried the above and OC2 is still down after 30 minutes:

1. **CC (Claude Code)** — primary owner
2. **PM2 (this agent)** — for systematic fixes
3. **Operator** (wifik / dabiggestpoppa) — final escalation

Before escalating, capture:
- Last 200 lines of log file
- Output of the diagnostic script above
- What you've already tried

---

## 🛡️ Prevention: Watchdog (TODO)

Create `tools/openclaw_watchdog.py` that:
- Pings `/health` every 60s
- Checks log for `FailoverError` in last 5 min
- Auto-restarts gateway on health fail
- Alerts via Telegram on repeated failures

This would have caught today's 7-hour outage in 60 seconds.
