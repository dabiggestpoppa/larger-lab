# CEREBUS System Startup — Idempotent, No Duplicates
# ====================================================
# Starts OCE backend and CEREBUS scanner if not already running.
# Safe to run multiple times — singleton enforcement in each script prevents duplicates.
#
# Usage:
#   .\scripts\start_system.ps1              # Start all services
#   .\scripts\start_system.ps1 --status     # Check what's running
#   .\scripts\start_system.ps1 --stop       # Stop all services

param(
    [switch]$Status,
    [switch]$Stop
)

$ErrorActionPreference = "SilentlyContinue"
$RepoRoot = "C:\Users\wifik\Desktop\projects\larger-lab"
$VenvPython = "$RepoRoot\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"

# Service definitions
$Services = @{
    "oce" = @{
        Name = "OCE Backend"
        Cmd = "`"$VenvPython`" -m oce.backend.main"
        Port = 8000
    }
    "cerebus" = @{
        Name = "CEREBUS Scanner"
        Cmd = "`"$VenvPython`" `"$RepoRoot\quant-lab\ml\run_cerebus_unified.py`" --interval 300"
        Port = $null
    }
}

function Get-ServiceProcesses($serviceName) {
    $svc = $Services[$serviceName]
    $procName = if ($serviceName -eq "oce") { "oce.backend.main" } else { "run_cerebus_unified.py" }
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
        $cmd -match [regex]::Escape($procName)
    }
}

function Show-Status {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  CEREBUS System Status" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    foreach ($key in $Services.Keys) {
        $svc = $Services[$key]
        $procs = Get-ServiceProcesses $key
        if ($procs) {
            $pids = ($procs | ForEach-Object { $_.Id }) -join ", "
            Write-Host "  $($svc.Name): " -NoNewline
            Write-Host "RUNNING (PID: $pids)" -ForegroundColor Green
        } else {
            Write-Host "  $($svc.Name): " -NoNewline
            Write-Host "STOPPED" -ForegroundColor Red
        }
    }
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Stop-AllServices {
    Write-Host "Stopping all CEREBUS services..." -ForegroundColor Yellow
    foreach ($key in $Services.Keys) {
        $procs = Get-ServiceProcesses $key
        foreach ($proc in $procs) {
            Write-Host "  Stopping PID $($proc.Id)..." -NoNewline
            Stop-Process -Id $proc.Id -Force
            Write-Host " OK" -ForegroundColor Green
        }
    }
    # Clean up PID files
    @("$RepoRoot\.guarddog_pids.json", "$RepoRoot\.signal_bot.pid", "$RepoRoot\scripts\.telegram_gateway.pid") | ForEach-Object {
        if (Test-Path $_) { Remove-Item $_ -Force }
    }
    Write-Host "All services stopped." -ForegroundColor Green
}

function Start-Service($serviceName) {
    $svc = $Services[$serviceName]
    $existing = Get-ServiceProcesses $serviceName
    if ($existing) {
        Write-Host "  $($svc.Name) already running (PID: $($existing.Id)) — skipping" -ForegroundColor DarkGray
        return
    }
    Write-Host "  Starting $($svc.Name)..." -NoNewline
    try {
        $process = Start-Process -FilePath "powershell" -ArgumentList "-WindowStyle Hidden -Command `"cd '$RepoRoot'; $($svc.Cmd)`"" -PassThru
        Start-Sleep -Seconds 2
        # Verify it started
        $verify = Get-ServiceProcesses $serviceName
        if ($verify) {
            Write-Host " OK (PID: $($verify.Id))" -ForegroundColor Green
        } else {
            Write-Host " STARTED (PID: $($process.Id))" -ForegroundColor Green
        }
    } catch {
        Write-Host " FAILED: $_" -ForegroundColor Red
    }
}

# --- Main ---
if ($Status) {
    Show-Status
    exit 0
}

if ($Stop) {
    Stop-AllServices
    exit 0
}

Write-Host ""
Write-Host "Starting CEREBUS System..." -ForegroundColor Cyan
Write-Host ""

Start-Service "oce"
Start-Service "cerebus"

Write-Host ""
Show-Status
