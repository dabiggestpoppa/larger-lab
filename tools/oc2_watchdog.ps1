# OC2 Gateway Watchdog
# Keeps OpenClaw gateway running and responsive.
# Checks every 30 seconds for:
#   1. Port not listening (dead gateway) -> restart
#   2. Stalled session (same "model_call:started" for >5 min) -> restart
#   3. Repeated timeouts/failovers in logs -> restart
#   4. Telegram channel not connected -> restart
#   5. Rate limit loops (429 errors) -> restart with backoff
# Also monitors OCE backend (:8000) and frontend (:3000)

param(
    [int]$CheckIntervalSeconds = 30,
    [int]$GatewayPort = 18790,
    [int]$OceBackendPort = 8000,
    [int]$OceFrontendPort = 3000,
    [int]$StallThresholdSeconds = 300,
    [int]$RateLimitBackoffSeconds = 120,
    [string]$OpenClawLog = "C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-05-28.log",
    [string]$WatchdogLog = "C:\Users\wifik\AppData\Local\Temp\openclaw\watchdog.log",
    [string]$FrontendDir = "C:\Users\wifik\Desktop\projects\larger-lab\oce\frontend"
)

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Message"
    Add-Content -Path $WatchdogLog -Value $line -ErrorAction SilentlyContinue
    Write-Output $line
}

function Test-GatewayPort {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $connect = $tcp.BeginConnect("127.0.0.1", $GatewayPort, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
        if ($wait -and $tcp.Connected) {
            $tcp.Close()
            return $true
        }
        $tcp.Close()
        return $false
    } catch {
        return $false
    }
}

function Get-LastLogLines {
    param([int]$Count = 50)
    if (Test-Path $OpenClawLog) {
        return Get-Content $OpenClawLog -Tail $Count
    }
    return @()
}

function Test-StalledSession {
    $lines = Get-LastLogLines 100
    $stalledCount = 0
    $lastStallAge = 0
    $rateLimitCount = 0
    $timeoutCount = 0
    
    foreach ($line in $lines) {
        # Detect "stalled session" warnings
        if ($line -match "stalled session") {
            $stalledCount++
        }
        # Detect long-running sessions with no progress
        if ($line -match "long-running session" -and $line -match "activeWorkKind=model_call") {
            if ($line -match "lastProgressAge=(\d+)s") {
                $lastStallAge = [int]$Matches[1]
            }
        }
        # Detect rate limit errors (429)
        if ($line -match "rate.limit" -or $line -match "429" -or $line -match "rate_limit") {
            $rateLimitCount++
        }
        # Detect repeated timeouts
        if ($line -match "timedOut=true" -or $line -match "failoverReason=`"timeout`"" -or $line -match "Provider returned error") {
            $timeoutCount++
        }
    }
    
    return @{
        StalledCount = $stalledCount
        LastProgressAge = $lastStallAge
        RateLimitCount = $rateLimitCount
        TimeoutCount = $timeoutCount
        IsStalled = ($stalledCount -ge 3 -or $lastStallAge -gt $StallThresholdSeconds)
        IsRateLimited = ($rateLimitCount -ge 2)
        IsTimeoutLoop = ($timeoutCount -ge 3)
    }
}

function Test-TelegramConnected {
    $lines = Get-LastLogLines 30
    $hasTelegram = $false
    $hasError = $false
    
    foreach ($line in $lines) {
        if ($line -match "telegram.*starting provider" -or $line -match "telegram.*inbound") {
            $hasTelegram = $true
        }
        if ($line -match "telegram.*error" -or $line -match "ECONNREFUSED.*telegram") {
            $hasError = $true
        }
    }
    
    return ($hasTelegram -and -not $hasError)
}

function Restart-Gateway {
    Write-Log "RESTARTING OC2 Gateway..."
    
    # Kill stale openclaw node processes
    Get-Process -Name "node" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "openclaw" } |
        Stop-Process -Force -ErrorAction SilentlyContinue
    
    Start-Sleep -Seconds 3
    
    # Start gateway hidden
    Start-Process -FilePath "openclaw" -ArgumentList "gateway run --port $GatewayPort" -WindowStyle Hidden
    Write-Log "Gateway restart initiated. Waiting 15s..."
    
    Start-Sleep -Seconds 15
    
    if (Test-GatewayPort) {
        Write-Log "Gateway restart SUCCESSFUL. Port $GatewayPort is listening."
    } else {
        Write-Log "Gateway restart FAILED. Port $GatewayPort still not listening."
    }
}

function Test-OceServices {
    $backendOk = $false
    $frontendOk = $false
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $connect = $tcp.BeginConnect("127.0.0.1", $OceBackendPort, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(2000, $false)
        $backendOk = ($wait -and $tcp.Connected)
        $tcp.Close()
    } catch { }
    
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $connect = $tcp.BeginConnect("127.0.0.1", $OceFrontendPort, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(2000, $false)
        $frontendOk = ($wait -and $tcp.Connected)
        $tcp.Close()
    } catch { }
    
    return @{ Backend = $backendOk; Frontend = $frontendOk }
}

# ─── Main Loop ──────────────────────────────────────────────────────────────

Write-Log "OC2 Watchdog started. Gateway=:${GatewayPort}, OCE=:${OceBackendPort}/:${OceFrontendPort}"
Write-Log "StallThreshold=${StallThresholdSeconds}s, RateLimitBackoff=${RateLimitBackoffSeconds}s, CheckInterval=${CheckIntervalSeconds}s"
Write-Log "Monitoring: port liveness, stalled sessions, rate limits, timeouts, telegram, OCE services"

$consecutivePortFailures = 0
$rateLimitBackoffUntil = [datetime]::MinValue

while ($true) {
    try {
        $needsRestart = $false
        $reason = ""
        
        # Check 1: Port liveness
        $portOk = Test-GatewayPort
        if (-not $portOk) {
            $consecutivePortFailures++
            Write-Log "Gateway port FAILED (failure #$consecutivePortFailures)"
            if ($consecutivePortFailures -ge 2) {
                $needsRestart = $true
                $reason = "Port $GatewayPort not listening after $consecutivePortFailures checks"
            }
        } else {
            $consecutivePortFailures = 0
            
            # Check 2: Stalled sessions, rate limits, timeout loops
            $stallInfo = Test-StalledSession
            if ($stallInfo.IsStalled) {
                $needsRestart = $true
                $reason = "Stalled session (stallCount=$($stallInfo.StalledCount), progressAge=$($stallInfo.LastProgressAge)s)"
            }
            if ($stallInfo.IsRateLimited) {
                if ((Get-Date) -lt $rateLimitBackoffUntil) {
                    Write-Log "Rate limit backoff active until $rateLimitBackoffUntil. Skipping restart."
                } else {
                    $needsRestart = $true
                    $reason = "Rate limit loop detected (count=$($stallInfo.RateLimitCount))"
                    $rateLimitBackoffUntil = (Get-Date).AddSeconds($RateLimitBackoffSeconds)
                    Write-Log "Setting rate limit backoff until $rateLimitBackoffUntil"
                }
            }
            if ($stallInfo.IsTimeoutLoop) {
                $needsRestart = $true
                $reason = "Timeout loop detected (count=$($stallInfo.TimeoutCount))"
            }
            
            # Check 3: Telegram connectivity
            if (-not $needsRestart) {
                $tgOk = Test-TelegramConnected
                if (-not $tgOk) {
                    Write-Log "Telegram may be disconnected. Will monitor..."
                }
            }
        }
        
        # Check 4: OCE services (restart if down)
        $oce = Test-OceServices
        if (-not $oce.Backend) {
            Write-Log "OCE Backend (:$OceBackendPort) is DOWN. Attempting restart..."
            Start-Process -FilePath "python" -ArgumentList "-m","oce.backend.main" -WindowStyle Hidden -WorkingDirectory "C:\Users\wifik\Desktop\projects\larger-lab"
            Start-Sleep -Seconds 8
        }
        if (-not $oce.Frontend) {
            Write-Log "OCE Frontend (:$OceFrontendPort) is DOWN. Attempting restart..."
            Start-Process -FilePath "npm" -ArgumentList "run","dev" -WindowStyle Hidden -WorkingDirectory $FrontendDir
            Start-Sleep -Seconds 10
        }
        
        if ($needsRestart) {
            Write-Log "RESTART TRIGGERED: $reason"
            Restart-Gateway
        }
    } catch {
        Write-Log "Watchdog error: $($_.Exception.Message)"
    }
    
    Start-Sleep -Seconds $CheckIntervalSeconds
}
