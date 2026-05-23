# OWL Autopilot — Hourly Workspace + Test Monitor
# Runs as a background loop checking:
#   1. 72h test health (PID, checkpoints, observers)
#   2. Agent progress files (all agents reporting?)
#   3. Agent memory files (all agents syncing?)
#   4. Team chat (recent activity?)
#   5. Git activity (commits in last hour?)
#   6. Workspace health (disk, stale files)

param(
    [int]$IntervalSeconds = 3600,  # 1 hour default
    [int]$TestPid = 7660,
    [string]$WorkspaceRoot = "C:\Users\wifik\Desktop\projects\larger-lab"
)

$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference = "SilentlyContinue"

# State tracking
$script:lastCheckpoint = 1  # Already saw checkpoint #1
$script:lastChatLines = 0
$script:lastGitCommit = ""
$script:checkCount = 0

# Agent roster
$script:agents = @(
    @{Name="CC"; Progress="claude-code-progress.md"; Memory="claude-code-memory.md"},
    @{Name="OC2"; Progress="openclaw-2-progress.md"; Memory="openclaw-2-memory.md"},
    @{Name="AS"; Progress="assistant-progress.md"; Memory="assistant-memory.md"},
    @{Name="PM"; Progress="polymorph-progress.md"; Memory="polymorph-memory.md"},
    @{Name="RL"; Progress="rl-progress.md"; Memory="rl-memory.md"},
    @{Name="Copilot"; Progress="copilot-progress.md"; Memory="copilot-memory.md"}
)

function Get-ElapsedHours {
    if (Test-Path "$WorkspaceRoot\progress\11-1-b-checkpoints.json") {
        $data = Get-Content "$WorkspaceRoot\progress\11-1-b-checkpoints.json" -Raw | ConvertFrom-Json
        if ($data.start_time) {
            return [math]::Round(((Get-Date) - [datetime]$data.start_time).TotalHours, 1)
        }
    }
    return 0
}

function Get-TestHealth {
    $proc = Get-Process -Id $TestPid -ErrorAction SilentlyContinue
    if (-not $proc) { return @{Running=$false} }
    return @{
        Running = $true
        CPU = [math]::Round($proc.TotalProcessorTime.TotalSeconds, 1)
        Threads = $proc.Threads.Count
        MemoryMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
    }
}

function Get-CheckpointData {
    if (Test-Path "$WorkspaceRoot\progress\11-1-b-checkpoints.json") {
        return Get-Content "$WorkspaceRoot\progress\11-1-b-checkpoints.json" -Raw | ConvertFrom-Json
    }
    return $null
}

function Get-AgentStatus {
    $results = @()
    foreach ($agent in $script:agents) {
        $progPath = Join-Path "$WorkspaceRoot\progress" $agent.Progress
        $memPath = Join-Path "$WorkspaceRoot\progress" $agent.Memory
        $progWrite = if (Test-Path $progPath) { (Get-Item $progPath).LastWriteTime } else { $null }
        $memWrite = if (Test-Path $memPath) { (Get-Item $memPath).LastWriteTime } else { $null }
        $results += @{
            Name = $agent.Name
            ProgressWrite = $progWrite
            MemoryWrite = $memWrite
            HasProgress = Test-Path $progPath
            HasMemory = Test-Path $memPath
        }
    }
    return $results
}

function Get-TeamChatActivity {
    $chatPath = "$WorkspaceRoot\shared-conversations\team-chat.md"
    if (Test-Path $chatPath) {
        $lines = (Get-Content $chatPath -ErrorAction SilentlyContinue | Measure-Object).Count
        $lastWrite = (Get-Item $chatPath).LastWriteTime
        return @{Lines = $lines; LastWrite = $lastWrite}
    }
    return @{Lines = 0; LastWrite = $null}
}

function Get-GitActivity {
    $log = git -C $WorkspaceRoot log --oneline -1 --format="%H %s" 2>$null
    return $log
}

# ─── Main Loop ──────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗"
Write-Host "║  🦉 OWL AUTOPILOT — Hourly Workspace + Test Monitor        ║"
Write-Host "╠══════════════════════════════════════════════════════════════╣"
Write-Host "║  Interval:     $($IntervalSeconds)s (1 hour)"
Write-Host "║  Test PID:     $TestPid"
Write-Host "║  Workspace:    $WorkspaceRoot"
Write-Host "║  Started:      $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "╚══════════════════════════════════════════════════════════════╝"
Write-Host ""

while ($true) {
    $script:checkCount++
    $now = Get-Date -Format "HH:mm:ss"
    $elapsed = Get-ElapsedHours

    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Host "[$now] 🔍 CHECK #$script:checkCount | Test elapsed: ${elapsed}h"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # ── 1. TEST HEALTH ──
    $testHealth = Get-TestHealth
    if ($testHealth.Running) {
        Write-Host "  ✅ Test PID $TestPid: Running | Threads=$($testHealth.Threads) | Mem=$($testHealth.MemoryMB)MB"
    } else {
        Write-Host "  ❌ Test PID $TestPid: NOT RUNNING — CHECK IMMEDIATELY"
    }

    # ── 2. CHECKPOINTS ──
    $cpData = Get-CheckpointData
    if ($cpData) {
        $chkCount = $cpData.total_checkpoints
        $passed = $cpData.passed_checkpoints
        $failed = $cpData.failed_checkpoints
        $maxDrift = $cpData.max_drift_score

        # Count observers
        $obsAlive = 0; $obsDegraded = 0; $obsDead = 0
        foreach ($obs in $cpData.observers.PSObject.Properties) {
            switch ($obs.Value.status) {
                "alive" { $obsAlive++ }
                "degraded" { $obsDegraded++ }
                "dead" { $obsDead++ }
            }
        }

        Write-Host "  📊 Checkpoints: $chkCount total | ✅$passed passed | ❌$failed failed | Max drift: $maxDrift"
        Write-Host "  👥 Observers: ✅$obsAlive alive | ⚠️$obsDegraded degraded | 💀$obsDead dead"

        # Alert on new checkpoint
        if ($chkCount -gt $script:lastCheckpoint) {
            $latest = $cpData.checkpoints[-1]
            Write-Host "  🆕 NEW CHECKPOINT #$chkCount: $($latest.status) | Drift=$($latest.drift_score) | State=$($latest.state_hash)"
            $script:lastCheckpoint = $chkCount
        }

        # Alert on failures
        if ($failed -gt 0) {
            Write-Host "  🚨 ALERT: $failed FAILED CHECKPOINT(S) — INVESTIGATE"
        }
        if ($maxDrift -ge 0.1) {
            Write-Host "  🚨 ALERT: Max drift $maxDrift exceeds 0.1 threshold"
        }
        if ($obsDead -gt 0) {
            Write-Host "  🚨 ALERT: $obsDead DEAD OBSERVER(S) — CHECK RECOVERY"
        }
    }

    # ── 3. AGENT PROGRESS ──
    Write-Host ""
    Write-Host "  📋 AGENT STATUS:"
    $agentStatus = Get-AgentStatus
    $staleAgents = @()
    foreach ($a in $agentStatus) {
        $progAge = if ($a.ProgressWrite) { [math]::Round(((Get-Date) - $a.ProgressWrite).TotalHours, 1) } else { "N/A" }
        $memAge = if ($a.MemoryWrite) { [math]::Round(((Get-Date) - $a.MemoryWrite).TotalHours, 1) } else { "N/A" }
        $status = if ($progAge -ne "N/A" -and $progAge -lt 2) { "✅" } elseif ($progAge -ne "N/A" -and $progAge -lt 6) { "⚠️" } else { "❌" }
        Write-Host "    $status $($a.Name): progress=${progAge}h ago | memory=${memAge}h ago"
        if ($progAge -eq "N/A" -or ($progAge -ne "N/A" -and $progAge -gt 6)) {
            $staleAgents += $a.Name
        }
    }
    if ($staleAgents.Count -gt 0) {
        Write-Host "  🚨 STALE AGENTS (no progress >6h): $($staleAgents -join ', ')"
    }

    # ── 4. TEAM CHAT ──
    $chat = Get-TeamChatActivity
    Write-Host ""
    Write-Host "  💬 Team Chat: $($chat.Lines) lines | Last write: $($chat.LastWrite)"
    if ($chat.Lines -gt $script:lastChatLines) {
        $newLines = $chat.Lines - $script:lastChatLines
        Write-Host "  🆕 $newLines new line(s) since last check"
        $script:lastChatLines = $chat.Lines
    }

    # ── 5. GIT ACTIVITY ──
    $gitHead = Get-GitActivity
    Write-Host ""
    Write-Host "  🔧 Git HEAD: $gitHead"
    if ($gitHead -ne $script:lastGitCommit -and $script:lastGitCommit -ne "") {
        Write-Host "  🆕 New commit since last check"
    }
    $script:lastGitCommit = $gitHead

    # ── 6. WORKSPACE HEALTH ──
    $progressFiles = Get-ChildItem "$WorkspaceRoot\progress" -File
    $totalProgressSize = [math]::Round(($progressFiles | Measure-Object -Property Length -Sum).Sum / 1KB, 1)
    Write-Host ""
    Write-Host "  📁 Workspace: $($progressFiles.Count) progress files | ${totalProgressSize}KB total"

    # Check for temp file buildup
    $tempFiles = Get-ChildItem "$WorkspaceRoot\temp" -File -ErrorAction SilentlyContinue
    if ($tempFiles.Count -gt 20) {
        Write-Host "  ⚠️ Temp directory has $($tempFiles.Count) files — consider cleanup"
    }

    Write-Host ""
    Write-Host "[$now] ✅ Check #$script:checkCount complete. Next check in $($IntervalSeconds/60) min."
    Write-Host ""

    Start-Sleep -Seconds $IntervalSeconds
}
