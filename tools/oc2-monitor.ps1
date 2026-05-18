# OC2 Gateway Monitor & Self-Heal Script
# Checks OC2 health every 5 minutes, detects common issues, auto-restarts if needed
# Usage: powershell -File tools\oc2-monitor.ps1

param(
    [int]$CheckIntervalSeconds = 300,
    [string]$LogFile = "C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-05-17.log"
)

# Known error patterns and their fixes
$KnownIssues = @{
    "context overflow"        = @{ Desc = "Session context exceeded safe threshold"; Fix = "Restart gateway"; Severity = "HIGH" }
    "ECONNRESET"              = @{ Desc = "OpenRouter API connection reset"; Fix = "Auto-retries with fallback. If persistent, restart."; Severity = "MEDIUM" }
    "typing.*TTL exceeded"    = @{ Desc = "Typing indicator timed out (>60s response)"; Fix = "Self-resolves. If stuck >5min, restart."; Severity = "LOW" }
    "EADDRINUSE"              = @{ Desc = "Port 18790 in use by stale process"; Fix = "Kill stale PID, restart gateway"; Severity = "HIGH" }
    "gateway already running" = @{ Desc = "Another gateway instance detected"; Fix = "Run openclaw gateway stop, then restart"; Severity = "HIGH" }
    "model.*gpt-5.5"          = @{ Desc = "Wrong model loaded (gpt-5.5 not owl-alpha)"; Fix = "Check OPENCLAW_HOME=.openclaw-2. Restart."; Severity = "MEDIUM" }
}

function Get-OC2Status {
    $proc = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'openclaw' }
    $port = netstat -ano | Select-String "18790.*LISTENING"
    $health = try { (Invoke-WebRequest -Uri "http://127.0.0.1:18790/health" -TimeoutSec 5 -UseBasicParsing).Content } catch { "DOWN" }
    $model = "UNKNOWN"
    if (Test-Path $LogFile) {
        $m = Get-Content $LogFile -Tail 100 | Select-String "agent model:" | Select-Object -Last 1
        if ($m) { $model = ($m -split "agent model:")[-1].Trim() }
    }
    return @{ Process = $proc; Port = ($port -ne $null); Health = $health; Model = $model }
}

function Get-OC2Issues {
    $issues = @()
    if (-not (Test-Path $LogFile)) { return $issues }
    $log = Get-Content $LogFile -Tail 200
    foreach ($p in $KnownIssues.Keys) {
        $matches = $log | Select-String $p
        if ($matches) { $issues += @{ Pattern = $p; Info = $KnownIssues[$p]; Count = $matches.Count } }
    }
    return $issues
}

function Restart-OC2 {
    Write-Host "$(Get-Date 'HH:mm:ss') [RESTART] Stopping..." -ForegroundColor Yellow
    & openclaw gateway stop 2>&1 | Out-Null
    Start-Sleep -Seconds 3
    $stale = netstat -ano | Select-String "18790.*LISTENING"
    if ($stale) { $pid = ($stale -split '\s+')[-1]; Stop-Process -Id $pid -Force -EA SilentlyContinue }
    Start-Sleep -Seconds 2
    $env:OPENCLAW_HOME = "C:\Users\wifik\.openclaw-2"
    Start-Process powershell -ArgumentList "-NoProfile -EP Bypass -Command `"openclaw gateway run --port 18790 --allow-unconfigured`"" -WindowStyle Hidden -WD "C:\Users\wifik\.openclaw-2"
    Start-Sleep -Seconds 12
    $h = try { (Invoke-WebRequest -Uri "http://127.0.0.1:18790/health" -TimeoutSec 5 -UseBasicParsing).Content } catch { "DOWN" }
    if ($h -match "live") { Write-Host "$(Get-Date 'HH:mm:ss') [RESTART] OK - Gateway up" -ForegroundColor Green; return $true }
    else { Write-Host "$(Get-Date 'HH:mm:ss') [RESTART] FAIL - Still down" -ForegroundColor Red; return $false }
}

# === MAIN LOOP ===
Write-Host "=== OC2 Monitor Started ===" -ForegroundColor Cyan
Write-Host "Interval: ${CheckIntervalSeconds}s | Issues tracked: $($KnownIssues.Count)" -ForegroundColor Gray

while ($true) {
    $s = Get-OC2Status
    $issues = Get-OC2Issues

    $pc = if ($s.Process) { "Green" } else { "Red" }
    $hc = if ($s.Health -match "live") { "Green" } else { "Red" }
    Write-Host "$(Get-Date 'HH:mm:ss') | " -NoNewline
    Write-Host "PID:$($s.Process.Id) " -NoNewline -ForegroundColor $pc
    Write-Host "Health:" -NoNewline; Write-Host "$($s.Health) " -NoNewline -ForegroundColor $hc
    Write-Host "Model:$($s.Model)" -NoNewline
    if ($issues.Count -gt 0) { Write-Host " | Issues:$($issues.Count)" -ForegroundColor Yellow } else { Write-Host "" }

    foreach ($i in $issues) {
        $c = switch ($i.Info.Severity) { "HIGH" { "Red" } "MEDIUM" { "Yellow" } default { "Cyan" } }
        Write-Host "  [$($i.Info.Severity)] $($i.Info.Desc) (x$($i.Count))" -ForegroundColor $c
        Write-Host "    Fix: $($i.Info.Fix)" -ForegroundColor Gray
    }

    $restart = $false
    if ($s.Health -eq "DOWN" -and -not $s.Port) { Write-Host "  -> DOWN. Restart." -ForegroundColor Red; $restart = $true }
    elseif ($s.Port -and $s.Health -eq "DOWN") { Write-Host "  -> Stale. Restart." -ForegroundColor Red; $restart = $true }
    elseif ($issues | Where-Object { $_.Info.Severity -eq "HIGH" -and $_.Count -gt 2 }) { Write-Host "  -> High issue. Restart." -ForegroundColor Yellow; $restart = $true }

    if ($restart) { Restart-OC2 | Out-Null }

    Write-Host "  [Next: ${CheckIntervalSeconds}s]" -ForegroundColor DarkGray; Write-Host ""
    Start-Sleep -Seconds $CheckIntervalSeconds
}
