# CEREBUS System Health Check — Restart If Dead
# ==============================================
# Checks if OCE and CEREBUS are running, restarts any that crashed.
# Designed to be called by Windows Task Scheduler every 5-10 minutes.
# Idempotent — safe to run as often as needed.
#
# Usage:
#   .\scripts\check_system.ps1          # Check and restart if needed
#   .\scripts\check_system.ps1 --quiet  # Only output if something restarted

param(
    [switch]$Quiet
)

$ErrorActionPreference = "SilentlyContinue"
$RepoRoot = "C:\Users\wifik\Desktop\projects\larger-lab"
$VenvPython = "$RepoRoot\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"
$LogFile = "$RepoRoot\.system_health.log"
$Restarted = $false

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    if (-not $Quiet) { Write-Host $line }
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
}

function Get-ServiceProcesses($pattern) {
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
        $cmd -match [regex]::Escape($pattern)
    }
}

function Start-ServiceSafe($serviceName, $cmd, $pattern) {
    $existing = Get-ServiceProcesses $pattern
    if ($existing) { return $false }

    Write-Log "RESTART: $serviceName was dead, starting..."
    try {
        Start-Process -FilePath "powershell" -ArgumentList "-WindowStyle Hidden -Command `"cd '$RepoRoot'; $cmd`"" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        $verify = Get-ServiceProcesses $pattern
        if ($verify) {
            Write-Log "RESTART OK: $serviceName (PID: $($verify.Id))"
            return $true
        } else {
            Write-Log "RESTART FAIL: $serviceName did not start"
            return $true  # Still return true to indicate we tried
        }
    } catch {
        Write-Log "RESTART ERROR: $serviceName — $_"
        return $true
    }
}

# --- Check OCE ---
$restarted = Start-ServiceSafe "OCE Backend" "`"$VenvPython`" -m oce.backend.main" "oce.backend.main"
$Restarted = $Restarted -or $restarted

# --- Check CEREBUS ---
$restarted = Start-ServiceSafe "CEREBUS Scanner" "`"$VenvPython`" `"$RepoRoot\quant-lab\ml\run_cerebus_unified.py`" --interval 300" "run_cerebus_unified.py"
$Restarted = $Restarted -or $restarted

# --- Clean up stale PID files ---
if (Test-Path "$RepoRoot\.guarddog_pids.json") {
    Remove-Item "$RepoRoot\.guarddog_pids.json" -Force
}

if (-not $Quiet -and -not $Restarted) {
    Write-Log "OK: All services running"
}

# Return exit code for Task Scheduler
if ($Restarted) { exit 1 } else { exit 0 }
