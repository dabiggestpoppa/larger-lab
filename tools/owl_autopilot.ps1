# OWL Autopilot - Hourly Workspace + Test Monitor
# Auto-detects test PID, handles rate limits, checks all agents
param(
    [int]$IntervalSeconds = 3600,
    [string]$WorkspaceRoot = "C:\Users\wifik\Desktop\projects\larger-lab"
)

$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference = "SilentlyContinue"

$script:lastCheckpoint = 1
$script:lastChatLines = 0
$script:lastGitCommit = ""
$script:checkCount = 0
$script:consecutiveErrors = 0

$script:agents = @(
    @{Name="CC"; Progress="claude-code-progress.md"; Memory="claude-code-memory.md"},
    @{Name="OC2"; Progress="openclaw-2-progress.md"; Memory="openclaw-2-memory.md"},
    @{Name="AS"; Progress="assistant-progress.md"; Memory="assistant-memory.md"},
    @{Name="PM"; Progress="polymorph-progress.md"; Memory="polymorph-memory.md"},
    @{Name="PM2"; Progress="PM2-progress.md"; Memory="PM2-memory.md"},
    @{Name="RL"; Progress="rl-progress.md"; Memory="rl-memory.md"},
    @{Name="Copilot"; Progress="copilot-progress.md"; Memory="copilot-memory.md"}
)

function Find-TestPID {
    # Auto-detect the 72h test PID by looking for test_11_1_b in cmdline
    foreach ($proc in Get-Process python -ErrorAction SilentlyContinue) {
        try {
            $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.Id)").CommandLine
            if ($cmd -like "*test_11_1_b*") { return $proc.Id }
        } catch { }
    }
    return $null
}

function Get-ElapsedHours {
    $cpPath = Join-Path $WorkspaceRoot "progress\11-1-b-checkpoints.json"
    if (Test-Path $cpPath) {
        try {
            $data = Get-Content $cpPath -Raw | ConvertFrom-Json
            if ($data.start_time) {
                return [math]::Round(((Get-Date) - [datetime]$data.start_time).TotalHours, 1)
            }
        } catch { }
    }
    return 0
}

function Get-TestHealth($testPid) {
    if (-not $testPid) { return @{Running=$false; Reason="No PID"} }
    $proc = Get-Process -Id $testPid -ErrorAction SilentlyContinue
    if (-not $proc) { return @{Running=$false; Reason="Process not found"} }
    return @{
        Running = $true
        CPU = [math]::Round($proc.TotalProcessorTime.TotalSeconds, 1)
        Threads = $proc.Threads.Count
        MemoryMB = [math]::Round($proc.WorkingSet64 / 1MB, 1)
    }
}

function Get-CheckpointData {
    $cpPath = Join-Path $WorkspaceRoot "progress\11-1-b-checkpoints.json"
    if (Test-Path $cpPath) {
        try { return Get-Content $cpPath -Raw | ConvertFrom-Json } catch { }
    }
    return $null
}

function Get-AgentStatus {
    $results = @()
    foreach ($agent in $script:agents) {
        $progPath = Join-Path $WorkspaceRoot "progress\$($agent.Progress)"
        $memPath = Join-Path $WorkspaceRoot "progress\$($agent.Memory)"
        $progWrite = if (Test-Path $progPath) { (Get-Item $progPath).LastWriteTime } else { $null }
        $memWrite = if (Test-Path $memPath) { (Get-Item $memPath).LastWriteTime } else { $null }
        $results += @{Name=$agent.Name; ProgressWrite=$progWrite; MemoryWrite=$memWrite}
    }
    return $results
}

function Get-TeamChatActivity {
    $chatPath = Join-Path $WorkspaceRoot "shared-conversations\team-chat.md"
    if (Test-Path $chatPath) {
        $content = Get-Content $chatPath -ErrorAction SilentlyContinue
        return @{Lines=($content | Measure-Object).Count; LastWrite=(Get-Item $chatPath).LastWriteTime}
    }
    return @{Lines=0; LastWrite=$null}
}

function Get-GitActivity {
    return git -C $WorkspaceRoot log --oneline -1 --format="%H %s" 2>$null
}

# Main Loop
Write-Host ""
Write-Host "============================================================"
Write-Host "  OWL AUTOPILOT - Hourly Workspace + Test Monitor"
Write-Host "  Auto-detect: test_11_1_b.py"
Write-Host "  Interval: $($IntervalSeconds)s | Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "============================================================"
Write-Host ""

while ($true) {
    $script:checkCount++
    $now = Get-Date -Format "HH:mm:ss"

    # Auto-detect test PID each cycle
    $testPid = Find-TestPID
    $elapsed = Get-ElapsedHours

    Write-Host "------------------------------------------------------------"
    $pidStr = if ($testPid) { $testPid } else { "NONE" }; Write-Host "[$now] CHECK #$script:checkCount | Test: ${elapsed}h | PID: $pidStr"
    Write-Host "------------------------------------------------------------"

    try {
        # 1. TEST HEALTH
        $testHealth = Get-TestHealth $testPid
        if ($testHealth.Running) {
            Write-Host "  [OK] Test PID $testPid : Running | Threads=$($testHealth.Threads) | Mem=$($testHealth.MemoryMB)MB"
        } else {
            Write-Host "  [FAIL] Test not running ($($testHealth.Reason)) - ATTEMPTING RESTART"
            # Try to restart
            $startCmd = "cd $WorkspaceRoot; python tools/testing/long_horizon/test_11_1_b.py --hours 72"
            Write-Host "  Restarting: $startCmd"
            Start-Process powershell -ArgumentList "-Command", $startCmd -WindowStyle Normal
            Start-Sleep -Seconds 10
            $newPid = Find-TestPID
            if ($newPid) {
                Write-Host "  [RESTARTED] New PID: $newPid"
                & python (Join-Path $WorkspaceRoot "tools\terminal_cleanup.py") --register $newPid
            } else {
                Write-Host "  [ERROR] Restart failed - manual intervention needed"
            }
        }

        # 2. CHECKPOINTS
        $cpData = Get-CheckpointData
        if ($cpData) {
            $chkCount = $cpData.total_checkpoints
            $passed = $cpData.passed_checkpoints
            $failed = $cpData.failed_checkpoints
            $maxDrift = $cpData.max_drift_score

            $obsAlive = 0; $obsDegraded = 0; $obsDead = 0
            foreach ($obs in $cpData.observers.PSObject.Properties) {
                switch ($obs.Value.status) {
                    "alive" { $obsAlive++ }
                    "degraded" { $obsDegraded++ }
                    "dead" { $obsDead++ }
                }
            }

            Write-Host "  Checkpoints: $chkCount | Passed: $passed | Failed: $failed | Drift: $maxDrift"
            Write-Host "  Observers: Alive=$obsAlive | Degraded=$obsDegraded | Dead=$obsDead"

            if ($chkCount -gt $script:lastCheckpoint) {
                $latest = $cpData.checkpoints[-1]
                Write-Host "  [NEW] CHECKPOINT #${chkCount}: $($latest.status) | Drift=$($latest.drift_score)"
                $script:lastCheckpoint = $chkCount
            }
            if ($failed -gt 0) { Write-Host "  [ALERT] $failed FAILED CHECKPOINT(S)" }
            if ($maxDrift -ge 0.1) { Write-Host "  [ALERT] Drift $maxDrift exceeds threshold" }
            if ($obsDead -gt 0) { Write-Host "  [ALERT] $obsDead DEAD OBSERVER(S)" }
        }

        # 3. AGENT STATUS
        Write-Host ""
        Write-Host "  AGENT STATUS:"
        $agentStatus = Get-AgentStatus
        $staleAgents = @()
        foreach ($a in $agentStatus) {
            $progAge = if ($a.ProgressWrite) { [math]::Round(((Get-Date) - $a.ProgressWrite).TotalHours, 1) } else { -1 }
            $memAge = if ($a.MemoryWrite) { [math]::Round(((Get-Date) - $a.MemoryWrite).TotalHours, 1) } else { -1 }
            $progStr = if ($progAge -ge 0) { "${progAge}h ago" } else { "MISSING" }
            $memStr = if ($memAge -ge 0) { "${memAge}h ago" } else { "MISSING" }
            $icon = if ($progAge -ge 0 -and $progAge -lt 2) { "[OK]" } elseif ($progAge -ge 0 -and $progAge -lt 6) { "[WARN]" } else { "[STALE]" }
            Write-Host "    $icon $($a.Name): progress=$progStr | memory=$memStr"
            if ($progAge -lt 0 -or $progAge -gt 6) { $staleAgents += $a.Name }
        }
        if ($staleAgents.Count -gt 0) {
            Write-Host "  [ALERT] Stale agents: $($staleAgents -join ', ')"
        }

        # 4. TEAM CHAT
        $chat = Get-TeamChatActivity
        Write-Host ""
        Write-Host "  Team Chat: $($chat.Lines) lines | Last: $($chat.LastWrite)"
        if ($chat.Lines -gt $script:lastChatLines -and $script:lastChatLines -gt 0) {
            Write-Host "  [NEW] $($chat.Lines - $script:lastChatLines) new line(s)"
        }
        $script:lastChatLines = $chat.Lines

        # 5. GIT
        $gitHead = Get-GitActivity
        Write-Host "  Git: $gitHead"
        if ($gitHead -ne $script:lastGitCommit -and $script:lastGitCommit -ne "") {
            Write-Host "  [NEW] New commit"
        }
        $script:lastGitCommit = $gitHead

        # Reset error counter on success
        $script:consecutiveErrors = 0

    } catch {
        $script:consecutiveErrors++
        Write-Host "  [ERROR] Check failed: $_ (consecutive: $($script:consecutiveErrors))"
        if ($script:consecutiveErrors -ge 3) {
            Write-Host "  [WARN] 3 consecutive errors - possible rate limit. Extending interval."
            Start-Sleep -Seconds 300  # Extra 5 min cooldown
            $script:consecutiveErrors = 0
        }
    }

    Write-Host ""
    Write-Host "[$now] Check #$script:checkCount complete. Next in $($IntervalSeconds/60) min."
    Write-Host ""

    Start-Sleep -Seconds $IntervalSeconds
}
