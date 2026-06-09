# CEREBUS CLEAN BRIDGE — PowerShell Startup Script
# Explicitly uses venv Python, avoids UV interception
# Usage: .\scripts\start_clean_bridge.ps1

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$BaseDir = "C:\Users\wifik\Desktop\projects\larger-lab"
$VenvPython = "$BaseDir\.venv\Scripts\python.exe"
$BridgeScript = "$BaseDir\quant-lab\mt5\clean_bridge.py"

# Verify venv Python exists
if (-not (Test-Path $VenvPython)) {
    Write-Error "Venv Python not found at $VenvPython"
    exit 1
}

# Kill any existing bridge processes (clean start)
$Existing = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*clean_bridge*' }
foreach ($proc in $Existing) {
    Write-Host "Killing existing bridge PID $($proc.ProcessId)"
    Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
}

# Start bridge with explicit venv Python
Write-Host "Starting clean bridge..."
Start-Process -FilePath $VenvPython -ArgumentList "`"$BridgeScript`"" -WorkingDirectory $BaseDir -WindowStyle Hidden

Write-Host "Bridge started. Check logs at quant-lab/mt5/live_logs/clean_bridge.log"