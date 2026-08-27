# TB-R6.6.1 - Install Windows persistent runtime for the TB forward test.
#
# Registers a Task Scheduler entry that launches the TB SUPERVISOR:
#   - On system startup (AtStartup) - survives reboot
#   - On user logon (AtLogOn) - catches manual session start
#
# The task runs as the CURRENT USER with InteractiveToken so the Python
# MT5 API can connect to the user's running MetaTrader 5 terminal.
#
# Battery/idle policies are set to NEVER stop the forward test.
# The task restarts up to 3 times on crash with 1-minute intervals.
#
# Run (PowerShell, as the target user):
#     powershell -ExecutionPolicy Bypass -File .\install_windows_runtime.ps1

$ErrorActionPreference = "Stop"

$TaskName = "TB-Runtime-Supervisor"
$Repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Supervisor = Join-Path $Repo "quant-lab\runtime\tb_supervisor.py"

if (-not (Test-Path $Supervisor)) {
    Write-Error "supervisor not found: $Supervisor"
    exit 1
}

$Py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Py) {
    $Py = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $Py) {
    Write-Error "python not found on PATH"
    exit 1
}

if ($Py -like "*py.exe") {
    $Py = "$Py -3"
}

$Action = New-ScheduledTaskAction -Execute "cmd" `
    -Argument "/c cd /d `"$Repo`" && `"$Py`" -u `"$Supervisor`"" `
    -WorkingDirectory $Repo

$TriggerStartup = New-ScheduledTaskTrigger -AtStartup
$TriggerLogon   = New-ScheduledTaskTrigger -AtLogOn

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Days 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action `
    -Trigger @($TriggerStartup, $TriggerLogon) `
    -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "TB runtime task installed: $TaskName"
Write-Host "  python:     $Py"
Write-Host "  supervisor: $Supervisor"
Write-Host "  triggers:   AtStartup + AtLogOn"
Write-Host "  identity:   $env:USERNAME (InteractiveToken)"
Write-Host "  battery:    unrestricted"
Write-Host "  restart:    3 retries, 1-min interval"
Write-Host ""
Write-Host "To start now: python quant-lab/runtime/tbctl.py start"
