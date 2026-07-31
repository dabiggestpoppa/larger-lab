# CEREBUS System Startup - Idempotent, No Duplicates
# ====================================================
# Starts CEREBUS Unified Scanner (includes ST/P90 engines, DTB, Directional Bias).
# Safe to run multiple times - singleton enforcement prevents duplicates.
# Desktop alerts only — no Telegram.
#
# Usage:
#   .\scripts\start_system.ps1              # Start CEREBUS scanner
#   .\scripts\start_system.ps1 --status     # Check what is running
#   .\scripts\start_system.ps1 --stop       # Stop all services

param(
    [switch]$Status,
    [switch]$Stop
)

$ErrorActionPreference = "SilentlyContinue"
$RepoRoot = "C:\Users\wifik\Desktop\projects\larger-lab"
$VenvPython = "$RepoRoot\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"

function Get-CerebusProcesses {
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
        $cmd -match "run_cerebus_unified"
    }
}

function Show-Status {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "  CEREBUS System Status" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan

    $cerebus = Get-CerebusProcesses
    if ($cerebus) {
        $pids = ($cerebus | ForEach-Object { $_.Id }) -join ", "
        Write-Host "  CEREBUS Scanner:   " -NoNewline
        Write-Host "RUNNING (PID: $pids)" -ForegroundColor Green
    } else {
        Write-Host "  CEREBUS Scanner:   " -NoNewline
        Write-Host "STOPPED" -ForegroundColor Red
    }

    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Stop-AllServices {
    Write-Host "Stopping all CEREBUS services..." -ForegroundColor Yellow

    Get-CerebusProcesses | ForEach-Object {
        Write-Host "  Stopping CEREBUS (PID $($_.Id))..." -NoNewline
        Stop-Process -Id $_.Id -Force
        Write-Host " OK" -ForegroundColor Green
    }

    Write-Host "All services stopped." -ForegroundColor Green
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

# Start CEREBUS if not running
$cerebus = Get-CerebusProcesses
if ($cerebus) {
    Write-Host "  CEREBUS already running (PID: $($cerebus.Id)) - skipping" -ForegroundColor DarkGray
} else {
    Write-Host "  Starting CEREBUS Scanner..." -NoNewline
    try {
        Start-Process -FilePath $VenvPython -ArgumentList "$RepoRoot\quant-lab\ml\run_cerebus_unified.py","--interval","300" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        $cerebus = Get-CerebusProcesses
        if ($cerebus) {
            Write-Host " OK (PID: $($cerebus.Id))" -ForegroundColor Green
        } else {
            Write-Host " STARTED (outside active window 3AM-12PM EST)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host " FAILED: $_" -ForegroundColor Red
    }
}

Write-Host ""
Show-Status
