# 🟢 OC2 Maintainer — Hermes Skill

> **Purpose:** Monitor, diagnose, and repair OpenClaw 2 (OC2) gateway and Telegram bot.
> **Trigger:** Run on cron schedule (every 30 min) or when OC2 errors are detected.
> **Agent:** Hermes (HR) — Execution / Maintenance / Self-Healing

---

## 1. MONITORING SEQUENCE

Run this diagnostic sequence every cycle. Log all results to `logs/hermes-oc2-monitor.log`.

### Step 1: Check Gateway Health
```powershell
try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:18790/health" -TimeoutSec 5
    Write-Host "OC2 Health: $($r.status) | OK: $($r.ok)"
} catch {
    Write-Host "OC2 DOWN: $_"
}
```

**If healthy** → Log and proceed to Step 2.
**If down** → Jump to REPAIR SEQUENCE (Section 3).

### Step 2: Check Node Process
```powershell
Get-Process -Name "node" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*18790*' } |
    Select-Object Id, @{N='Mem(MB)';E={[math]::Round($_.WorkingSet64/1MB,1)}}, StartTime
```

**If no process found** → Gateway is down, jump to REPAIR.
**If process found but health check failed** → Process is stuck, jump to REPAIR.
**If memory > 500MB** → Log warning, may need restart.

### Step 3: Check Stuck Sessions
```powershell
$sf = "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\.openclaw\agents\main\sessions\sessions.json"
if (Test-Path $sf) {
    $data = Get-Content $sf -Raw | ConvertFrom-Json
    $count = ($data.PSObject.Properties | Measure-Object).Count
    Write-Host "Active sessions: $count"
    # Check for sessions older than 1 hour
    $now = [DateTimeOffset]::UtcNow
    foreach ($prop in $data.PSObject.Properties) {
        $ts = $prop.Value.updatedAt
        if ($ts) {
            $age = $now - [DateTimeOffset]$ts
            if ($age.TotalHours -gt 1) {
                Write-Host "STALE: $($prop.Name) — age: $($age.TotalHours.ToString('F1'))h"
            }
        }
    }
}
```

**If stale sessions found** → Clean them (see REPAIR Step 4).

### Step 4: Check Event Loop Delays
```powershell
$log = "C:\Users\wifik\Desktop\projects\larger-lab\logs\oc2-watchdog.log"
if (Test-Path $log) {
    Get-Content $log -Tail 20 | Select-String -Pattern "restart|error|stuck|timeout"
}
```

**If restart loop detected** (>3 restarts in 10 min) → Escalate to team-chat.

### Step 5: Check Telegram Connectivity
```powershell
# Check if Telegram API is reachable
try {
    $test = Invoke-WebRequest -Uri "https://api.telegram.org" -TimeoutSec 10
    Write-Host "Telegram API: OK"
} catch {
    Write-Host "Telegram API FAIL: $_"
}
```

---

## 2. ERROR CLASSIFICATION

| Pattern | Severity | Action |
|---------|----------|--------|
| `health: live` | ✅ OK | Log and continue |
| `health: unreachable` | 🔴 CRITICAL | Immediate restart |
| `No API key found` | 🔴 CRITICAL | Check models.json |
| `event loop delay >30s` | 🟡 WARNING | Monitor, restart if persistent |
| `stuck session` | 🟡 WARNING | Clean session |
| `memory >500MB` | 🟡 WARNING | Schedule restart |
| `Telegram timeout` | 🟡 WARNING | Check network, restart if persistent |
| `restart loop >3/10min` | 🔴 CRITICAL | Escalate to team-chat |
| `sessions.json corrupt` | 🔴 CRITICAL | Rebuild sessions.json |

---

## 3. REPAIR SEQUENCE

### Repair Step 1: Soft Restart
```powershell
# Kill existing OC2 process
Get-Process -Name "node" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*18790*' } |
    Stop-Process -Force
Start-Sleep -Seconds 3

# Start fresh
$env:OPENCLAW_HOME = "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2"
node "C:\Users\wifik\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" gateway run --port 18790 --allow-unconfigured

# Wait for health
Start-Sleep -Seconds 10
try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:18790/health" -TimeoutSec 5
    Write-Host "RESTART SUCCESS: $($r.status)"
} catch {
    Write-Host "RESTART FAILED: $_"
}
```

### Repair Step 2: Clean Stuck Sessions
```powershell
$sf = "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\.openclaw\agents\main\sessions\sessions.json"
$data = Get-Content $sf -Raw | ConvertFrom-Json
$now = [DateTimeOffset]::UtcNow
$removed = 0
foreach ($prop in $data.PSObject.Properties) {
    $ts = $prop.Value.updatedAt
    if ($ts) {
        $age = $now - [DateTimeOffset]$ts
        if ($age.TotalHours -gt 1) {
            $data.PSObject.Properties.Remove($prop.Name)
            $removed++
            Write-Host "Removed stale: $($prop.Name)"
        }
    }
}
$data | ConvertTo-Json -Depth 10 | Set-Content $sf -Encoding UTF8
Write-Host "Cleaned $removed stale sessions"
```

### Repair Step 3: Fix Config Issues
If `No API key found` error:
```powershell
# Check models.json for placeholder keys
$mf = "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\.openclaw\agents\main\models.json"
$models = Get-Content $mf -Raw | ConvertFrom-Json
foreach ($prop in $models.PSObject.Properties) {
    $key = $prop.Value.apiKey
    if ($key -match "KEY$" -or $key -match "placeholder") {
        Write-Host "WARNING: Placeholder API key in $($prop.Name): $key"
    }
}
```

### Repair Step 4: Nuclear Option (Full Reset)
If soft restart fails:
```powershell
# 1. Kill all node processes for OC2
Get-Process -Name "node" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*18790*' } |
    Stop-Process -Force

# 2. Clear sessions.json
$sf = "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\.openclaw\agents\main\sessions\sessions.json"
@{version=1; sessions=@{}} | ConvertTo-Json | Set-Content $sf -Encoding UTF8

# 3. Clear any lock files
Get-ChildItem "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2" -Filter "*.lock" -Recurse | Remove-Item -Force

# 4. Start fresh
$env:OPENCLAW_HOME = "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2"
Start-Process -WindowStyle Hidden -FilePath "cmd" -ArgumentList '/c "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd"'

# 5. Wait and verify
Start-Sleep -Seconds 15
try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:18790/health" -TimeoutSec 5
    Write-Host "FULL RESET SUCCESS: $($r.status)"
} catch {
    Write-Host "FULL RESET FAILED: $_ — ESCALATE TO TEAM-CHAT"
}
```

---

## 4. REPORTING

After each monitoring cycle, write a status entry:

**To `logs/hermes-oc2-monitor.log`:**
```
[2026-05-16T18:00:00Z] CYCLE: health=live | mem=420MB | sessions=3 | stale=0 | status=OK
[2026-05-16T18:30:00Z] CYCLE: health=down | action=restart | result=success | status=RECOVERED
```

**To `shared-conversations/team-chat.md` (only on issues):**
```
## 🟢 [HR] 2026-05-16 — OC2 Maintenance Report
- **Issue:** Gateway unreachable (health check failed)
- **Action:** Soft restart performed
- **Result:** ✅ Recovered — health=live, PID 12345
- **Sessions cleaned:** 2 stale sessions removed
```

**To `progress/hermes-progress.md`:**
```
#### 🟢 [HR] 2026-05-16 — OC2 Maintenance Cycle
- Health: live | Memory: 420MB | Sessions: 3
- Actions: None needed
```

---

## 5. ESCALATION RULES

Escalate to team-chat when:
1. **Full reset fails** — OC2 won't come back after nuclear option
2. **Restart loop** — >3 restarts in 10 minutes
3. **Config corruption** — openclaw.json or models.json is malformed
4. **Telegram API down** — Can't reach api.telegram.org for >30 minutes
5. **Memory leak** — Node process >1GB

---

## 6. TOOLS AVAILABLE

| Tool | Path | Purpose |
|------|------|---------|
| OC2 Watchdog | `tools/oc2-watchdog.py` | Background health monitor |
| OC2 Doctor | `tools/oc2-doctor.cmd` | Full diagnostic |
| Gateway CMD | `.openclaw-2/gateway.cmd` | Start gateway |
| Sessions | `.openclaw-2/.openclaw/agents/main/sessions/sessions.json` | Session state |
| Config | `.openclaw-2/openclaw.json` | OC2 config |
| Models | `.openclaw-2/.openclaw/agents/main/models.json` | Model/API keys |
| Watchdog Log | `logs/oc2-watchdog.log` | Watchdog history |
| Hermes Log | `logs/hermes-oc2-monitor.log` | This skill's log |
